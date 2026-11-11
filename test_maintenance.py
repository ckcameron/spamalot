#!/usr/bin/env python3
"""Offline regression tests; no merchant form is opened or submitted."""

import argparse
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import spamalot as pm
import source_discovery as ai
import source_health as health


class HealthTests(unittest.TestCase):
    def test_http_missing_and_challenge(self):
        self.assertEqual(health.page_assessment(404, 'text/html', b'', 'subscribe')[0], 'broken')
        self.assertEqual(health.page_assessment(429, 'text/html', b'', 'evidence')[0], 'review')
        self.assertEqual(health.page_assessment(503, 'text/html', b'', 'unsubscribe')[0], 'review')
        self.assertEqual(health.page_assessment(200, 'text/html', b'<h1>Page Not Found</h1>', 'subscribe')[0], 'broken')

    def test_redirect_resolution_restricts_org(self):
        self.assertTrue(health.same_organization_host('https://www.example.com/old', 'https://example.com/new'))
        self.assertTrue(health.same_organization_host('https://example.com/old', 'https://forms.example.com/new'))
        self.assertFalse(health.same_organization_host('https://example.com/old', 'https://example.org/new'))
        self.assertRaises(ValueError, health.public_https_url, 'http://example.com', resolve=False)
        self.assertRaises(ValueError, health.public_https_url, 'https://localhost/x', resolve=False)
        self.assertRaises(ValueError, health.public_https_url, 'https://127.0.0.1/x', resolve=False)

    def test_suggests_only_same_organization_https_redirect(self):
        def same_domain(url, timeout):
            return (200, 'text/html', b'<h1>Request Printed Catalog</h1><p>By postal mail only. Use your own actual mailing address to receive this printed catalog.</p>',
                    'https://www.example.com/catalog', [url, 'https://www.example.com/catalog'])
        result = health.check_url('https://example.com/old', 'subscribe', fetcher=same_domain)
        self.assertEqual(result.result, 'ok')
        self.assertEqual(result.suggested_url, 'https://www.example.com/catalog')

        def other_org(url, timeout):
            return (200, 'text/html', b'<h1>Request Printed Catalog</h1>',
                    'https://other.example.net/catalog', [url, 'https://other.example.net/catalog'])
        result = health.check_url('https://example.com/old', 'subscribe', fetcher=other_org)
        self.assertEqual(result.result, 'review')
        self.assertEqual(result.suggested_url, '')

    def test_two_missing_page_checks_disable_source_without_deleting_history(self):
        with tempfile.TemporaryDirectory() as temp:
            conn = pm.connect(Path(temp) / 'mail.db')
            pm.import_sources(conn, pm.load_default_sources(), origin='bundled')
            row = conn.execute("SELECT * FROM sources WHERE slug='territorial'").fetchone()
            run = pm.new_run(conn, 'subscribe', pm.AGREEMENT)
            pm.record(conn, run, row, 'subscribe', 'user_reported_submitted', 'test record, no real request')
            pm.finalize(conn, run, Path(temp) / 'receipts')
            missing = lambda url, role, timeout: health.Observation(url, url, 'broken', 404, 'HTTP 404', [url])
            with patch.object(pm, 'check_url', side_effect=missing):
                for index in range(2):
                    run = pm.new_run(conn, 'check-sources', pm.AGREEMENT)
                    row = conn.execute("SELECT * FROM sources WHERE slug='territorial'").fetchone()
                    pm.check_sources(conn, run, [row], 1, 0, False, False, 2)
                    pm.finalize(conn, run, Path(temp) / 'receipts')
                    self.assertEqual(conn.execute("SELECT health FROM sources WHERE slug='territorial'").fetchone()[0],
                                     'review' if index == 0 else 'broken')
            self.assertEqual(conn.execute("SELECT default_enabled FROM sources WHERE slug='territorial'").fetchone()[0], 0)
            self.assertTrue(pm.ever_subscribed(conn, 'territorial'))
            args = argparse.Namespace(source=None, file=None, all=True, category=None)
            selected = pm.pick_sources(conn, args, 'unsubscribe')
            self.assertIn('territorial', [r['slug'] for r in selected])
            exported = Path(temp) / 'clean.json'
            self.assertGreater(pm.export_sources(conn, exported, include_review=False), 1)
            self.assertNotIn('territorial', {r['slug'] for r in json.loads(exported.read_text())['sources']})

    def test_old_database_schema_migrates(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / 'legacy.db'
            conn = sqlite3.connect(db)
            conn.executescript('''CREATE TABLE sources (
              slug TEXT PRIMARY KEY, name TEXT NOT NULL, subscribe_url TEXT NOT NULL,
              unsubscribe_url TEXT NOT NULL, optout_instructions TEXT NOT NULL,
              evidence_url TEXT NOT NULL, category TEXT NOT NULL, notes TEXT NOT NULL,
              automation TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
              CREATE TABLE runs (run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL,
              operation TEXT NOT NULL, agreement TEXT NOT NULL,
              receipt_path TEXT, completed_at TEXT);
              CREATE TABLE events (event_id TEXT PRIMARY KEY, run_id TEXT, source_slug TEXT,
              action TEXT, status TEXT, timestamp TEXT, url TEXT, details TEXT);''')
            conn.commit()
            conn.close()
            migrated = pm.connect(db)
            self.assertIn('default_enabled', [x[1] for x in migrated.execute('PRAGMA table_info(sources)')])
            self.assertEqual(migrated.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 0)
            migrated.close()


class DiscoveryTests(unittest.TestCase):
    def test_candidate_json_parsing(self):
        self.assertEqual(ai.parse_candidates('```json\n[{"slug":"foo"}]\n```')[0]['slug'], 'foo')
        with self.assertRaises(ai.ProviderError):
            ai.parse_candidates('not valid JSON')

    def test_openai_api_payload_and_citation_extraction(self):
        calls = []
        def response(url, headers, payload, timeout):
            calls.append((url, payload))
            return {'output': [{'type': 'message', 'content': [{'text': '[{"slug":"test"}]',
                    'annotations': [{'url': 'https://example.com/evidence'}]}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'private-test-key'}):
            result, citations = ai.request_candidates('openai', '', 'Church', requester=response)
        self.assertIn('test', result)
        self.assertEqual(citations, ['https://example.com/evidence'])
        self.assertEqual(calls[0][1]['tools'], [{'type': 'web_search'}])
        self.assertNotIn('private-test-key', str(calls[0][1]))

    def test_invalid_ai_suggestions_never_become_default(self):
        with tempfile.TemporaryDirectory() as temp:
            conn = pm.connect(Path(temp) / 'mail.db')
            invalid = [{'slug': 'postermail', 'name': 'Email only newsletter',
                        'subscribe_url': 'http://example.com/signup',
                        'unsubscribe_url': 'https://example.com/unsubscribe',
                        'optout_instructions': 'Unsubscribe from email by clicking a link.',
                        'evidence_url': 'https://example.com/privacy', 'category': 'NGO'}]
            with patch.object(pm, 'request_candidates', return_value=(json.dumps(invalid), [])):
                candidates = pm.discover_candidates(conn, 'openai', '', '', 10, check=False)
            self.assertEqual(candidates, [])
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM sources').fetchone()[0], 0)
            conn.close()


if __name__ == '__main__':
    unittest.main()
