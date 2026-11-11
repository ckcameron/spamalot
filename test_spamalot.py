#!/usr/bin/env python3
"""Offline regression tests: NO LIVE SUBSCRIPTIONS OR WEB REQUESTS."""
import json
import tempfile
import unittest
from pathlib import Path

import spamalot as pm


class SourceTests(unittest.TestCase):
    def test_bundled_are_valid_and_unique(self):
        items = pm.load_default_sources()
        self.assertGreaterEqual(len(items), 30)
        self.assertEqual(len(items), len({r['slug'] for r in items}))
        for item in items:
            parsed = pm.validated_source(item)
            self.assertTrue(pm.is_https(parsed['evidence_url']))
            self.assertGreaterEqual(len(parsed['optout_instructions']), 20)
            self.assertTrue(parsed['subscribe_url'].startswith('https://'))
            self.assertTrue(parsed['unsubscribe_url'].startswith('https://'))

    def test_idempotent_sync_and_history_preservation(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = pm.connect(Path(folder) / 'sources.db')
            seeds = pm.load_default_sources()
            added, updated = pm.import_sources(conn, seeds)
            self.assertEqual((added, updated), (len(seeds), 0))
            run = pm.new_run(conn, 'subscribe', pm.AGREEMENT)
            row = conn.execute('SELECT * FROM sources WHERE slug=?', ('llbean',)).fetchone()
            pm.record(conn, run, row, 'subscribe', 'user_reported_submitted', 'test fake local record')
            receipt = pm.finalize(conn, run, Path(folder) / 'receipts')
            self.assertTrue(receipt.is_file())
            self.assertEqual(json.loads(receipt.read_text())['summary']['reported_requests'],1)
            self.assertEqual(pm.import_sources(conn, seeds), (0, 0))
            self.assertEqual(pm.latest_state(conn,'llbean'),'subscribed_or_requested')
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)
            conn.close()

    def test_category_filters(self):
        self.assertTrue(pm.category_matches('Church / Printed Newsletter', ['church']))
        self.assertTrue(pm.category_matches('NGO / Civil Liberties', ['political','NGO']))
        self.assertFalse(pm.category_matches('Catalog / Home', ['church','policy']))
        self.assertTrue(pm.category_matches('Catalog / Home', []))

    def test_csv_json_import(self):
        items=pm.load_default_sources()
        self.assertGreaterEqual(len(items),25)


if __name__=='__main__':
    unittest.main()
