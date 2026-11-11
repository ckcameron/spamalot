"""Exercise consent and auditing through the CLI using temporary local state."""

import json
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import spamalot as pm


class CliTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.db = Path(workspace.name) / 'test.sqlite3'
        self.profile = Path(workspace.name) / 'profile.json'
        self.receipts = Path(workspace.name) / 'receipts'
        self.source = {
            'slug': 'test-catalog',
            'name': 'Test Print Catalog',
            'subscribe_url': 'https://publisher.example/request',
            'unsubscribe_url': 'https://publisher.example/stop',
            'optout_instructions': 'Ask the publisher to stop sending the printed catalog.',
            'evidence_url': 'https://publisher.example/preferences',
        }
        browser = patch.object(pm.webbrowser, 'open', side_effect=AssertionError('Unexpected browser launch'))
        browser.start()
        self.addCleanup(browser.stop)

    def run_cli(self, *command, answers=(pm.AGREEMENT,), interactive=True):
        args = [
            'spamalot', '--db', str(self.db), '--profile', str(self.profile),
            '--receipts', str(self.receipts), *command,
        ]
        stderr = StringIO()
        with (
            patch.object(sys, 'argv', args),
            patch.object(sys.stdin, 'isatty', return_value=interactive),
            patch('builtins.input', side_effect=answers),
            redirect_stdout(StringIO()),
            redirect_stderr(stderr),
        ):
            status = pm.main()
        return status, stderr.getvalue()

    def seed_source(self):
        with closing(pm.connect(self.db)) as db:
            pm.import_sources(db, [self.source], origin='bundled')

    def read_receipt(self, operation):
        receipts = [
            json.loads(path.read_text(encoding='utf-8'))
            for path in self.receipts.glob('*.json')
        ]
        matches = [receipt for receipt in receipts if receipt['operation'] == operation]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_init_rejects_noninteractive_consent(self):
        status, error = self.run_cli('init', interactive=False)
        self.assertEqual(status, 2)
        self.assertIn('Interactive acknowledgment is required', error)
        self.assertFalse(self.db.exists())
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.receipts.exists())

    def test_init_rejects_incorrect_acknowledgment(self):
        status, error = self.run_cli('init', answers=('yes',))
        self.assertEqual(status, 2)
        self.assertIn('Acknowledgment rejected', error)
        self.assertFalse(self.db.exists())
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.receipts.exists())

    def test_dry_runs_record_the_correct_urls_without_a_profile(self):
        self.seed_source()
        for action in ('subscribe', 'unsubscribe'):
            with self.subTest(action=action):
                status, error = self.run_cli(action, '--source', 'test-catalog', '--dry-run')
                self.assertEqual(status, 0, error)
                receipt = self.read_receipt(action)
                self.assertEqual(receipt['agreement'], pm.AGREEMENT)
                self.assertEqual(receipt['summary'], {
                    'events': 1, 'reported_requests': 0,
                    'unverified_requests': 0, 'not_submitted': 1,
                })
                event, = receipt['events']
                self.assertEqual(event['action'], action)
                self.assertEqual(event['status'], 'dry_run')
                self.assertEqual(event['url'], self.source[f'{action}_url'])
                with closing(pm.connect(self.db)) as db:
                    row = db.execute(
                        'SELECT status, url FROM events WHERE event_id = ?', (event['event_id'],)
                    ).fetchone()
                    self.assertEqual(tuple(row), ('dry_run', self.source[f'{action}_url']))
                    self.assertEqual(pm.latest_state(db, 'test-catalog'), 'not_subscribed')
        self.assertFalse(self.profile.exists())

    def test_address_confirmation_precedes_assisted_subscription(self):
        self.seed_source()
        self.profile.write_text(json.dumps({
            'first_name': 'Example', 'last_name': 'Recipient',
            'address1': '123 Test Street', 'city': 'Example City', 'state': 'CA', 'zip': '90000',
        }), encoding='utf-8')
        status, error = self.run_cli(
            'subscribe', '--source', 'test-catalog', answers=(pm.AGREEMENT, 'no'),
        )
        self.assertEqual(status, 1)
        self.assertIn('Address ownership not confirmed', error)
        receipt = self.read_receipt('subscribe')
        self.assertEqual(receipt['events'], [])
        self.assertEqual(receipt['summary']['reported_requests'], 0)
        self.assertNotIn('123 Test Street', json.dumps(receipt))

    def test_discovery_decline_does_not_call_provider(self):
        with patch.object(pm, 'request_candidates') as request:
            status, error = self.run_cli(
                'discover', '--provider', 'openai', answers=(pm.AGREEMENT, 'no'),
            )
        self.assertEqual(status, 1)
        self.assertIn('AI request not authorized', error)
        request.assert_not_called()
        self.assertEqual(self.read_receipt('discover')['events'], [])
