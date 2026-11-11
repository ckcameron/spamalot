#!/usr/bin/env python3
"""
Spamalot - U.S. physical-mail catalog, circular, and print-periodical tracker.

Copyright (c) 2026 CK Cameron.
License: CC BY-NC-SA 4.0 (see LICENSE.txt).

FOR THE NAMED RECIPIENT ONLY.  USE AT AN ADDRESS WHERE YOU LAWFULLY
RECEIVE POSTAL MAIL.  NEVER ENTER A THIRD PARTY'S NAME OR ADDRESS.

UNTESTED for legal ramifications and for continued compatibility with
any third-party website.  Check ALL applicable local/state/federal laws,
site policies and postal regulations before use. The author expressly
DISCOURAGES deploying the script in its unmodified/raw form. Review its
code, targets, data handling, and each organization's current rules.

By continuing, you affirm you are the named recipient, have checked local
law, are genuinely interested in each selected source's products/services,
and consent to receive PHYSICAL POSTAL MARKETING from those sources.
You alone accept all responsibility and legal liability for your use;
to the extent permitted by law, the author provides no warranty and
accepts no liability for your use, including direct/indirect damages.
A disclaimer or license may not waive non-waivable legal rights or duties.

The program only opens PHYSICAL-postal-mail request pages; however, SOME
organizations couple print subscriptions with electronic messaging. Review
published notes, each site's actual terms and opt-in boxes before submitting.
The program does not separately opt you in to email/SMS, and does not bypass
CAPTCHAs or website anti-automation measures.

A receipt records YOUR report or a visible website signal about a request.
It is NOT proof of the organization's acceptance or postal delivery.
A blanket opt-out means all TRACKED sources, not every mailer in the USA.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import uuid
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from source_discovery import ProviderError, parse_candidates, request_candidates
from source_health import check_url, replacement_suggestions, same_organization_host

VERSION = '2.1.0'
AGREEMENT = 'I AM THE RECIPIENT; I CHECKED LOCAL LAW; I ACCEPT RESPONSIBILITY'
STATES = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split())
FIELDS = ('first_name', 'last_name', 'address1', 'address2', 'city', 'state', 'zip', 'email', 'phone')
SOURCE_COLUMNS = ('slug', 'name', 'subscribe_url', 'unsubscribe_url', 'optout_instructions', 'evidence_url', 'category', 'notes', 'automation')

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def private_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(data)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def secure_existing(path: Path) -> None:
    if os.name == 'posix':
        os.chmod(path, 0o600)


def is_https(url: str) -> bool:
    try:
        p = urlsplit(url)
        return p.scheme == 'https' and bool(p.netloc) and not p.username and not p.password
    except ValueError:
        return False


def normalize_slug(value: str) -> str:
    value = str(value).strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{1,63}', value):
        raise ValueError(f'Invalid source slug: {value!r}; use 2-64 letters/digits/_/-')
    return value


# Source files are editable input, not trusted configuration. Validate every
# address and opt-out field before a record can reach the local registry.
def validated_source(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError('Each source must be a JSON object / CSV row.')
    row = {k: (record.get(k) or '') for k in SOURCE_COLUMNS}
    row['slug'] = normalize_slug(row['slug'])
    for key in ('name', 'subscribe_url', 'unsubscribe_url', 'optout_instructions', 'evidence_url'):
        if not str(row[key]).strip():
            raise ValueError(f'{row["slug"]}: missing required {key}')
    for key in ('subscribe_url', 'unsubscribe_url', 'evidence_url'):
        if not is_https(str(row[key])):
            raise ValueError(f'{row["slug"]}: {key} must be an HTTPS URL (published official proof required)')
    # Require a specific published exit route before any source can be added.
    if len(str(row['optout_instructions']).strip()) < 20:
        raise ValueError(f'{row["slug"]}: supply a real, published postal opt-out procedure')
    auto = row.get('automation') or {}
    if isinstance(auto, str):
        auto = json.loads(auto) if auto.strip() else {}
    if not isinstance(auto, dict):
        raise ValueError(f'{row["slug"]}: automation must be JSON object')
    for action in ('subscribe', 'unsubscribe'):
        if action in auto:
            spec = auto[action]
            if not isinstance(spec, dict) or not isinstance(spec.get('fields'), dict):
                raise ValueError(f'{row["slug"]}: automation.{action}.fields must map selectors to profile fields')
            if not isinstance(spec.get('submit'), str) or not isinstance(spec.get('confirmation'), str):
                raise ValueError(f'{row["slug"]}: automation.{action} requires submit and confirmation CSS/text selectors')
            if any(f not in FIELDS for f in spec['fields'].values()):
                raise ValueError(f'{row["slug"]}: unrecognized profile field in automation.{action}')
    row['automation'] = json.dumps(auto, sort_keys=True)
    return {k: str(row[k]).strip() for k in SOURCE_COLUMNS}


# Keep schema creation and forward-only migrations together. The database is a
# durable audit log; upgrading it must never silently reset request history.
def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS sources (
            slug TEXT PRIMARY KEY, name TEXT NOT NULL, subscribe_url TEXT NOT NULL,
            unsubscribe_url TEXT NOT NULL, optout_instructions TEXT NOT NULL,
            evidence_url TEXT NOT NULL, category TEXT NOT NULL,
            notes TEXT NOT NULL, automation TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL,
            operation TEXT NOT NULL, agreement TEXT NOT NULL,
            receipt_path TEXT, completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
            source_slug TEXT NOT NULL REFERENCES sources(slug),
            action TEXT NOT NULL CHECK (action IN ('subscribe', 'unsubscribe')),
            status TEXT NOT NULL, timestamp TEXT NOT NULL,
            url TEXT NOT NULL, details TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS events_source_time ON events(source_slug, timestamp);
    ''')
    # Upgrade existing v1 databases without discarding subscriptions or receipts.
    existing = {r[1] for r in conn.execute('PRAGMA table_info(sources)')}
    columns = {
        'health': "TEXT NOT NULL DEFAULT 'unchecked'",
        'checked_at': "TEXT NOT NULL DEFAULT ''",
        'check_details': "TEXT NOT NULL DEFAULT ''",
        'failures': 'INTEGER NOT NULL DEFAULT 0',
        'default_enabled': 'INTEGER NOT NULL DEFAULT 1',
        'origin': "TEXT NOT NULL DEFAULT 'legacy'",
    }
    for column, definition in columns.items():
        if column not in existing:
            conn.execute(f'ALTER TABLE sources ADD COLUMN {column} {definition}')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS checks (
            id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
            source_slug TEXT NOT NULL REFERENCES sources(slug),
            checked_at TEXT NOT NULL, role TEXT NOT NULL,
            state TEXT NOT NULL, status_code INTEGER,
            request_url TEXT NOT NULL, final_url TEXT NOT NULL,
            suggested_url TEXT NOT NULL, details TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
            discovered_at TEXT NOT NULL, slug TEXT NOT NULL,
            state TEXT NOT NULL, payload TEXT NOT NULL,
            citations TEXT NOT NULL, review_notes TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_changes (
            id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
            source_slug TEXT NOT NULL REFERENCES sources(slug),
            changed_at TEXT NOT NULL, field_name TEXT NOT NULL,
            old_value TEXT NOT NULL, new_value TEXT NOT NULL, reason TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS checks_by_source ON checks(source_slug, checked_at);
    ''')
    conn.commit()
    secure_existing(db_path)
    return conn


# Import is deliberately conservative: existing entries survive unless the
# operator explicitly requests metadata replacement.
def import_sources(conn: sqlite3.Connection, items: list[dict], update: bool = False,
                   origin: str = 'imported') -> tuple[int, int]:
    validated = [validated_source(i) for i in items]
    enabled = {normalize_slug(i['slug']): int(bool(i.get('default_enabled', origin == 'bundled')))
               for i in items}
    if len({i['slug'] for i in validated}) != len(validated):
        raise ValueError('Duplicate slugs in input file')
    new, changed = 0, 0
    for row in validated:
        exists = conn.execute('SELECT 1 FROM sources WHERE slug=?', (row['slug'],)).fetchone()
        if exists and not update:
            continue
        now = utc_now()
        if exists:
            conn.execute('''UPDATE sources SET name=:name,subscribe_url=:subscribe_url,
                unsubscribe_url=:unsubscribe_url,optout_instructions=:optout_instructions,
                evidence_url=:evidence_url,category=:category,notes=:notes,
                automation=:automation,updated_at=:now WHERE slug=:slug''', dict(row, now=now))
            changed += 1
        else:
            conn.execute('''INSERT INTO sources
                (slug,name,subscribe_url,unsubscribe_url,optout_instructions,evidence_url,
                 category,notes,automation,created_at,updated_at)
                VALUES (:slug,:name,:subscribe_url,:unsubscribe_url,:optout_instructions,
                        :evidence_url,:category,:notes,:automation,:now,:now)''', dict(row, now=now))
            conn.execute('UPDATE sources SET default_enabled=?,origin=? WHERE slug=?',
                         (enabled[row['slug']], origin, row['slug']))
            new += 1
    conn.commit()
    return new, changed


def read_sources_file(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        if path.suffix.lower() == '.json':
            obj = json.load(f)
            if isinstance(obj, dict):
                obj = obj.get('sources', [])
            if not isinstance(obj, list):
                raise ValueError('JSON source file must contain a list or {"sources": [...]}')
            return obj
        if path.suffix.lower() == '.csv':
            return list(csv.DictReader(f))
    raise ValueError('Source imports must be .json or .csv')


def load_default_sources() -> list[dict]:
    """Read bundled, evidence-backed postal sources; fail closed if missing."""
    external = Path(__file__).resolve().with_name('spamalot_data') / 'default-sources.json'
    if not external.is_file():
        raise ValueError(f'Missing bundled source database: {external}; reinstall Spamalot or restore the file from the source archive')
    return read_sources_file(external)


def category_matches(category: str, filters: list[str] | None) -> bool:
    """Case-insensitive category substring filter, OR across repeated values."""
    return not filters or any(x.casefold() in category.casefold() for x in filters)


def load_profile(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f'Profile missing: {path}. Run `init` and edit your profile.')
    with path.open(encoding='utf-8') as f:
        p = json.load(f)
    for k in ('first_name', 'last_name', 'address1', 'city', 'state', 'zip'):
        if not isinstance(p.get(k), str) or not p[k].strip() or p[k].startswith('YOUR_'):
            raise ValueError(f'Enter your own {k} in {path}')
    p = {key: str(p.get(key) or '').strip() for key in FIELDS}
    p['state'] = p['state'].upper()
    if p['state'] not in STATES:
        raise ValueError('Profile state must be a U.S. state or DC abbreviation')
    if not re.fullmatch(r'\d{5}(?:-\d{4})?', p['zip']):
        raise ValueError('ZIP must be 5 or 5+4 digits')
    if '@' in p['address1'] or '@' in p['city']:
        raise ValueError('Profile address is not a recognizable U.S. postal address')
    return p


def disclaimer() -> None:
    print('''
SPAMALOT - UNTESTED RESEARCH / PERSONAL-USE SOFTWARE
================================================================
ONLY the named recipient may use this for mail delivered to an address
at which they lawfully receive U.S. postal mail. Never target anyone else.

You affirm genuine interest in products/services for EVERY selected source
and freely consent to that source sending you PHYSICAL POSTAL MAIL.
Your request is NOT consent to electronic marketing; review each site's
checkboxes and any bundled communications before completing a form.

Check local/state/federal law and each site's terms BEFORE use. The author
DISCOURAGES using this program in its raw, unreviewed form. It is
UNTESTED for legal ramifications or third-party website compatibility.
YOU ASSUME ALL RESPONSIBILITY AND LEGAL LIABILITY FOR YOUR USE.
To the fullest extent allowed by law, the author DISCLAIMS ALL WARRANTIES
AND LIABILITY, express/implied, including fitness or merchantability.
No license/disclaimer can nullify mandatory legal obligations.

Licensed CC BY-NC-SA 4.0: attribution + noncommercial + share-alike.
No automated CAPTCHA/anti-bot bypass, no bulk repeated requests, no
third-party addresses. Opt-out-all covers ONLY organizations recorded here.
Results are user-reported requests, not verified merchant acceptances.
''')


# Acknowledgment is intentionally interactive. This is not an unattended
# bulk-subscription tool and there is no --yes shortcut.
def acknowledge() -> str:
    disclaimer()
    if not sys.stdin.isatty():
        raise ValueError('Interactive acknowledgment is required for every run; no unattended execution.')
    print('Type this EXACT sentence to proceed:')
    print(AGREEMENT)
    answer = input('Acknowledgment: ').strip()
    if answer != AGREEMENT:
        raise ValueError('Acknowledgment rejected: no work performed')
    return AGREEMENT


# A run groups all per-source decisions under one audit identifier. It tracks
# what the operator attempted, not what a publisher ultimately accepted.
def new_run(conn: sqlite3.Connection, operation: str, agreement: str) -> dict:
    run = {'run_id': str(uuid.uuid4()), 'operation': operation, 'started_at': utc_now(),
           'agreement': agreement, 'events': [], 'notices': [], 'version': VERSION}
    conn.execute('INSERT INTO runs (run_id,started_at,operation,agreement) VALUES (?,?,?,?)',
                 (run['run_id'], run['started_at'], operation, agreement))
    conn.commit()
    return run


def record(conn: sqlite3.Connection, run: dict, row: sqlite3.Row, action: str,
           status: str, details: str) -> None:
    event = {'event_id': str(uuid.uuid4()), 'run_id': run['run_id'],
             'source': row['slug'], 'organization': row['name'], 'action': action,
             'status': status, 'timestamp': utc_now(),
             'url': row['subscribe_url' if action == 'subscribe' else 'unsubscribe_url'],
             'details': details}
    conn.execute('''INSERT INTO events
      (event_id,run_id,source_slug,action,status,timestamp,url,details)
      VALUES (:event_id,:run_id,:source,:action,:status,:timestamp,:url,:details)''', event)
    conn.commit()
    run['events'].append(event)


# Write the local receipt before marking the database run complete. The
# restrictive file mode avoids publishing the user's audit trail by accident.
def finalize(conn: sqlite3.Connection, run: dict, receipts_dir: Path) -> Path:
    run['completed_at'] = utc_now()
    run['summary'] = {'events': len(run['events']),
                      'reported_requests': sum(e['status'] in ('user_reported_submitted', 'site_confirmation_observed') for e in run['events']),
                      'unverified_requests': sum(e['status'] == 'request_unverified' for e in run['events']),
                      'not_submitted': sum(e['status'] in ('not_submitted', 'dry_run') for e in run['events'])}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    receipt = receipts_dir / f'{stamp}-{run["run_id"][:8]}.json'
    private_write(receipt, json.dumps(run, indent=2, ensure_ascii=False) + '\n')
    conn.execute('UPDATE runs SET receipt_path=?,completed_at=? WHERE run_id=?',
                 (str(receipt), run['completed_at'], run['run_id']))
    conn.commit()
    return receipt


# State is derived from recorded events rather than a writable "subscribed"
# flag. An attempt is not proof that a publisher changed its mailing list.
def latest_state(conn: sqlite3.Connection, slug: str) -> str:
    events = conn.execute('''SELECT action,status FROM events
      WHERE source_slug=? ORDER BY timestamp DESC,rowid DESC''', (slug,)).fetchall()
    # Unsuccessful operations are not state transitions.
    for e in events:
        if e['status'] in ('user_reported_submitted', 'site_confirmation_observed', 'request_unverified'):
            if e['action'] == 'subscribe':
                return 'subscribed_or_requested'
            return 'optout_requested'
    return 'not_subscribed'


def ever_subscribed(conn: sqlite3.Connection, slug: str) -> bool:
    return conn.execute('''SELECT 1 FROM events WHERE source_slug=? AND action='subscribe'
      AND status IN ('user_reported_submitted','site_confirmation_observed','request_unverified') LIMIT 1''', (slug,)).fetchone() is not None


# Resolve explicit slugs, selection files, and --all in one place. Opt-out
# selection intentionally includes broken and manually disabled sources.
def pick_sources(conn: sqlite3.Connection, args: argparse.Namespace, action: str) -> list[sqlite3.Row]:
    rows = {r['slug']: r for r in conn.execute('SELECT * FROM sources ORDER BY name COLLATE NOCASE')}
    names: list[str] = []
    if args.source:
        names.extend(args.source)
    if args.file:
        path = Path(args.file)
        with path.open(encoding='utf-8-sig', newline='') as f:
            if path.suffix.lower() == '.json':
                value = json.load(f)
                names.extend(value['sources'] if isinstance(value, dict) else value)
            elif path.suffix.lower() == '.csv':
                reader = csv.DictReader(f)
                if 'slug' not in (reader.fieldnames or []):
                    raise ValueError('Selection CSV requires slug column')
                names.extend(row['slug'] for row in reader)
            else:
                names.extend(line.strip() for line in f if line.strip() and not line.lstrip().startswith('#'))
    if args.all or (action == 'subscribe' and not names):
        if action == 'subscribe':
            names.extend(r['slug'] for r in rows.values()
                         if r['default_enabled'] and r['health'] != 'broken'
                         and latest_state(conn, r['slug']) != 'subscribed_or_requested')
        else:
            # Blanket: EVERY previously recorded opt-in, including where opt-out was attempted.
            names.extend(r['slug'] for r in rows.values() if ever_subscribed(conn, r['slug']))
    if action == 'unsubscribe' and not names and not args.all:
        raise ValueError('Specify --source, --file, or --all for unsubscribe')
    selected, seen = [], set()
    for item in names:
        slug = normalize_slug(item)
        if slug not in rows:
            raise ValueError(f'Unknown slug {slug!r}. Import its full verified postal opt-out details first.')
        if slug not in seen:
            if action == 'subscribe' and rows[slug]['health'] == 'broken':
                raise ValueError(f'{slug}: flagged as broken. Repair and recheck the source first.')
            selected.append(rows[slug])
            seen.add(slug)
    return [r for r in selected if category_matches(r['category'], args.category)]


# Browser automation is opt-in and form-specific. No guessed controls, hidden
# browsing, or CAPTCHA handling: the operator reviews each visible form.
def automation_interactive(row: sqlite3.Row, action: str, profile: dict) -> tuple[str, str]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout  # type: ignore
    except ImportError:
        return ('not_submitted', 'Playwright not installed; use assisted browser mode or pip install playwright && playwright install chromium')
    automation = json.loads(row['automation'] or '{}').get(action)
    if not automation:
        return ('not_submitted', f'No reviewed automation adapter configured for {action}; use assisted mode')
    dest = row['subscribe_url' if action == 'subscribe' else 'unsubscribe_url']
    # Explicit, reviewed selectors only: never guess a submit button or defeat CAPTCHAs.
    try:
        clicked = False
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(dest, wait_until='domcontentloaded', timeout=30000)
            for selector, profile_key in automation['fields'].items():
                value = profile.get(profile_key, '')
                if not value:
                    raise ValueError(f'Profile missing field {profile_key} needed by {row["slug"]}')
                locator = page.locator(selector)
                # Support both text inputs and ordinary state/country <select>s.
                if locator.evaluate('(el) => el.tagName.toLowerCase()') == 'select':
                    locator.select_option(value, timeout=10000)
                else:
                    locator.fill(value, timeout=10000)
            print('Review form IN BROWSER for accuracy, terms, unwanted email/SMS checkboxes,')
            print('payment requests and any human verification. Do NOT proceed if uncertain.')
            if input('Submit this single postal-mail request? Type SUBMIT: ').strip() != 'SUBMIT':
                browser.close()
                return ('not_submitted', 'User declined submission after auto-fill')
            clicked = True  # outcome may be uncertain after the click starts
            page.locator(automation['submit']).click(timeout=10000)
            try:
                page.locator(automation['confirmation']).wait_for(state='visible', timeout=12000)
                result = ('site_confirmation_observed',
                          f'Configured success selector appeared after click: {automation["confirmation"]}')
            except PWTimeout:
                result = ('request_unverified', 'Submit clicked; no configured confirmation observed. Verify directly with merchant.')
            print('Submission attempt finished; inspect the browser, then press Enter to close.')
            input()
            browser.close()
            return result
    except (Exception, KeyboardInterrupt) as exc:
        status = 'request_unverified' if locals().get('clicked', False) else 'not_submitted'
        return (status, f'Browser automation interrupted or failed; check source manually: {type(exc).__name__}: {exc}')


def assisted_interactive(row: sqlite3.Row, action: str, no_browser: bool) -> tuple[str, str]:
    url = row['subscribe_url' if action == 'subscribe' else 'unsubscribe_url']
    if action == 'unsubscribe':
        print('Published POSTAL opt-out procedure:', row['optout_instructions'])
        print('Published proof:', row['evidence_url'])
    if row['notes']:
        print('Caution:', row['notes'])
    print('Official page:', url)
    if not no_browser:
        opened = webbrowser.open(url)
        if not opened:
            print('Browser did not open automatically; visit the URL manually.')
    print('Complete the request yourself. Disable optional EMAIL/SMS subscriptions.')
    print('Do not report submission unless you actually completed the postal-mail request.')
    choice = input('Was the POSTAL request actually submitted? [y]es / [n]o / [u]nverified: ').strip().lower()
    if choice == 'y':
        return ('user_reported_submitted', 'User stated that an actual postal-mail request was submitted; merchant acceptance not independently verified')
    if choice == 'u':
        return ('request_unverified', 'User could not verify whether merchant received postal-mail request')
    return ('not_submitted', 'User did not complete postal-mail request')


def print_sources(conn: sqlite3.Connection, history: bool = False, category: list[str] | None = None) -> None:
    if history:
        for r in conn.execute('''SELECT timestamp, source_slug, action, status, details
                                 FROM events ORDER BY timestamp DESC,rowid DESC LIMIT 100'''):
            print(f'{r["timestamp"]} {r["source_slug"]:17} {r["action"]:11} {r["status"]} | {r["details"]}')
        return
    for r in conn.execute('SELECT * FROM sources ORDER BY name COLLATE NOCASE'):
        if not category_matches(r['category'], category):
            continue
        state = latest_state(conn, r['slug'])
        print(f'{r["slug"]:22} {state:24} {r["name"]}  [{r["category"]}]')
        print(f'  HEALTH: {r["health"]}, default={bool(r["default_enabled"])}; checked={r["checked_at"] or "never"}')
        print(f'  SUB: {r["subscribe_url"]}')
        print(f'  OUT: {r["unsubscribe_url"]}')


def save_change(conn: sqlite3.Connection, run: dict, slug: str, field: str,
                old: str, new: str, reason: str) -> None:
    conn.execute('''INSERT INTO source_changes
      (id,run_id,source_slug,changed_at,field_name,old_value,new_value,reason)
      VALUES (?,?,?,?,?,?,?,?)''',
      (str(uuid.uuid4()), run['run_id'], slug, utc_now(), field, old, new, reason))


def apply_url_change(conn: sqlite3.Connection, run: dict, row: sqlite3.Row,
                     field: str, new_url: str, reason: str) -> None:
    if field not in ('subscribe_url', 'unsubscribe_url', 'evidence_url') or not is_https(new_url):
        raise ValueError('Invalid URL field or replacement')
    old = row[field]
    if old == new_url:
        return
    save_change(conn, run, row['slug'], field, old, new_url, reason)
    run.setdefault('changes', []).append({'source': row['slug'], 'field': field, 'old_url': old, 'new_url': new_url, 'reason': reason})
    conn.execute(f'UPDATE sources SET {field}=?, updated_at=?, health=? WHERE slug=?',
                 (new_url, utc_now(), 'review', row['slug']))
    conn.commit()


# A health check examines publicly visible URLs only. A reachable page is
# not evidence of a functional signup, and ambiguous errors warrant review.
def check_sources(conn: sqlite3.Connection, run: dict, rows: list[sqlite3.Row],
                  timeout: int, delay: float, repair: bool, suggest: bool,
                  failure_threshold: int) -> dict:
    summary = {'checked': 0, 'healthy': 0, 'review': 0, 'broken': 0, 'redirect_repairs': 0}
    run['checks'] = []
    field_roles = (('subscribe_url', 'subscribe'), ('unsubscribe_url', 'unsubscribe'),
                   ('evidence_url', 'evidence'))
    for pos, row in enumerate(rows):
        print(f'[{pos + 1}/{len(rows)}] {row["slug"]}')
        observations = []
        for field, role in field_roles:
            result = check_url(row[field], role, timeout=timeout)
            print(f'  {role:12} {result.result:7} HTTP {result.http_status or "-"}: {result.reason}')
            if result.suggested_url and repair:
                apply_url_change(conn, run, row, field, result.suggested_url,
                                 'Same-organization HTTPS redirect; page content passed heuristic check')
                summary['redirect_repairs'] += 1
                print(f'    REPAIRED: {row[field]} -> {result.suggested_url}')
            elif result.final_url != row[field]:
                print(f'    REDIRECT (review): {result.final_url}')
            if result.result != 'ok' and suggest:
                proposals = replacement_suggestions(row[field], role, timeout=timeout)
                for proposal in proposals[:3]:
                    print(f'    POSSIBLE REPLACEMENT (not applied): {proposal}')
            conn.execute('''INSERT INTO checks
                (id,run_id,source_slug,checked_at,role,state,status_code,
                 request_url,final_url,suggested_url,details)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (str(uuid.uuid4()), run['run_id'], row['slug'], utc_now(), role,
                 result.result, result.http_status, result.url, result.final_url,
                 result.suggested_url, result.reason))
            observations.append(result)
            if delay:
                time.sleep(delay)
        failed = any(o.result == 'broken' for o in observations)
        uncertain = any(o.result == 'review' for o in observations)
        failures = row['failures'] + 1 if failed else 0
        status = ('broken' if failed and failures >= failure_threshold else
                  'review' if failed or uncertain else 'healthy')
        # Only a confirmed repeatable 404/410/soft404 is grounds to disable by default.
        enabled = 0 if status == 'broken' else row['default_enabled']
        details = ' | '.join(f'{field_roles[i][1]}: {o.reason}' for i, o in enumerate(observations))
        conn.execute('''UPDATE sources SET checked_at=?,health=?,check_details=?,
                    failures=?,default_enabled=? WHERE slug=?''',
                     (utc_now(), status, details[:3000], failures, enabled, row['slug']))
        conn.commit()
        summary['checked'] += 1
        summary['broken' if status == 'broken' else 'review' if status == 'review' else 'healthy'] += 1
        run['checks'].append({
            'source': row['slug'], 'status': status,
            'default_enabled': bool(enabled), 'consecutive_missing_page_checks': failures,
            'observations': [
                {'role': field_roles[i][1], 'url': o.url, 'final_url': o.final_url,
                 'state': o.result, 'http_status': o.http_status,
                 'suggested_url': o.suggested_url, 'details': o.reason}
                for i, o in enumerate(observations)
            ],
        })
        print(f'  OVERALL: {status}; consecutive missing-page checks: {failures}; default enabled: {bool(enabled)}')
    return summary


# AI search output goes into a quarantine table. Promotion requires independent
# inspection of both the print signup and the physical-mail removal procedure.
def discover_candidates(conn: sqlite3.Connection, provider: str, model: str,
                        category: str, max_candidates: int, check: bool) -> list[dict]:
    answer, citations = request_candidates(provider, model, category)
    items = parse_candidates(answer)
    stored = []
    known = {r[0] for r in conn.execute('SELECT slug FROM sources')}
    for data in items[:max_candidates]:
        try:
            parsed = validated_source(data)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f'  Skipped malformed AI result: {str(exc)[:160]}')
            continue
        if parsed['slug'] in known:
            print(f'  Skipped existing source: {parsed["slug"]}')
            continue
        # No network data from an AI provider is sufficient to establish validity.
        checks = {}
        if check:
            for key, role in (('subscribe_url', 'subscribe'), ('unsubscribe_url', 'unsubscribe'),
                              ('evidence_url', 'evidence')):
                observed = check_url(parsed[key], role)
                checks[role] = {'result': observed.result, 'status': observed.http_status,
                                'reason': observed.reason}
        candidate_id = str(uuid.uuid4())
        conn.execute('''INSERT INTO candidates
            (id,provider,model,discovered_at,slug,state,payload,citations,review_notes)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (candidate_id, provider, model or '', utc_now(), parsed['slug'], 'pending',
             json.dumps(data, ensure_ascii=False), json.dumps(citations[:30]),
             json.dumps(checks, ensure_ascii=False)))
        stored.append({'id': candidate_id, 'name': parsed['name'], 'slug': parsed['slug'],
                       'urls': [parsed['subscribe_url'], parsed['unsubscribe_url'], parsed['evidence_url']],
                       'checks': checks})
    conn.commit()
    return stored


# Export is a snapshot of locally eligible records, not a claim that every
# destination currently accepts postal requests.
def export_sources(conn: sqlite3.Connection, target: Path, include_review: bool) -> int:
    rows = conn.execute('''SELECT * FROM sources
            WHERE default_enabled=1 AND health != 'broken' AND
            (? = 1 OR health IN ('healthy','unchecked')) ORDER BY name COLLATE NOCASE''',
            (int(include_review),)).fetchall()
    payload = {'source_set': 'spamalot-curated', 'researched_date': utc_now()[:10],
               'description': 'Review the public postal subscription and opt-out pages before use',
               'sources': [{**{k: r[k] for k in SOURCE_COLUMNS if k != 'automation'},
                            'automation': json.loads(r['automation']),
                            'default_enabled': bool(r['default_enabled'])} for r in rows]}
    private_write(target, json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    return len(rows)


# CLI parsing is kept at the boundary so database and provider functions can
# be exercised without launching a browser or issuing external requests.
def run_main() -> int:
    parser = argparse.ArgumentParser(
        prog='spamalot',
        description='Consent-first U.S. printed catalog, magazine, newsletter and policy-mail tracker',
    )
    parser.add_argument('--db', type=Path, default=Path('spamalot.sqlite3'))
    parser.add_argument('--profile', type=Path, default=Path('profile.json'))
    parser.add_argument('--receipts', type=Path, default=Path('receipts'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init', help='Seed bundled sources and write example private address profile')
    sync = sub.add_parser('sync-defaults', help='Add newly researched sources to existing DB without changing past events or user profile')
    sync.add_argument('--update', action='store_true', help='Refresh existing bundled source records with newer published details')
    imp = sub.add_parser('import-sources', help='Import additional verified sources from CSV or JSON')
    imp.add_argument('--file', required=True)
    imp.add_argument('--update', action='store_true', help='Update existing source details after review')
    ls = sub.add_parser('sources', help='List mailers and last recorded state')
    ls.add_argument('--category', action='append', help='Filter categories (e.g. Catalog, Church, NGO, Political); repeatable')
    sub.add_parser('history', help='Show recent request audit trail')
    check = sub.add_parser('check-sources', help='Read-only HTTP check, record failures and repair safe redirects')
    check.add_argument('--source', action='append', help='One or more specific slugs; default: all')
    check.add_argument('--timeout', type=int, default=12, help='Timeout per request in seconds')
    check.add_argument('--delay', type=float, default=0.5, help='Seconds to wait between requests')
    check.add_argument('--failure-threshold', type=int, default=2, help='Missing-page checks before disabling a default (min 2)')
    check.add_argument('--no-repair', action='store_true', help='Do not apply safe same-host redirects')
    check.add_argument('--suggest', action='store_true', help='Also inspect official homepages for replacement links')
    repair = sub.add_parser('adopt-url', help='Apply a manually verified URL replacement')
    repair.add_argument('--source', required=True)
    repair.add_argument('--field', choices=('subscribe_url','unsubscribe_url','evidence_url'), required=True)
    repair.add_argument('--url', required=True)
    disc = sub.add_parser('discover', help='Query a public web-grounded AI API for REVIEW-ONLY postal sources')
    disc.add_argument('--provider', required=True, choices=('openai','gemini','perplexity'))
    disc.add_argument('--model', default='', help='Provider model override')
    disc.add_argument('--category', default='', help='Focus research on catalogs, churches, NGOs, political print, etc.')
    disc.add_argument('--max-candidates', type=int, default=12)
    disc.add_argument('--check', action='store_true', help='Read-only HTTP check of every suggested URL')
    sub.add_parser('candidates', help='List AI-discovered sources awaiting verification')
    promote = sub.add_parser('promote-candidate', help='Import an individually reviewed candidate (disabled by default)')
    promote.add_argument('--id', required=True)
    enable = sub.add_parser('enable-source', help='Enable a manually verified source for --all')
    enable.add_argument('--source', required=True)
    disable = sub.add_parser('disable-source', help='Exclude a source from --all (keeps opt-out history)')
    disable.add_argument('--source', required=True)
    exp = sub.add_parser('export-defaults', help='Export enabled, nonbroken sources to a new curated JSON file')
    exp.add_argument('--file', type=Path, required=True)
    exp.add_argument('--include-review', action='store_true')
    doc = sub.add_parser('build-docs', help='Generate manual page and Markdown references')
    doc.add_argument('--output', type=Path, default=Path('generated-docs'))
    for command in ('subscribe', 'unsubscribe'):
        p = sub.add_parser(command, help=('Request paper mail' if command == 'subscribe' else 'Request per-source or blanket cancellation'))
        choices = p.add_mutually_exclusive_group()
        choices.add_argument('--all', action='store_true', help='All source catalog entries (subscribe), or all ever-subscribed sources (unsubscribe)')
        choices.add_argument('--file', help='A .txt, .json or slug-column CSV target list')
        choices.add_argument('--source', action='append', help='Repeatable source slug')
        p.add_argument('--category', action='append', help='Filter by one or more category substrings; e.g. --all --category Church')
        p.add_argument('--automate', action='store_true', help='Playwright auto-fill + explicit one-by-one approval; requires reviewed source adapters')
        p.add_argument('--no-browser', action='store_true', help='Print manual URLs rather than opening a local browser')
        p.add_argument('--dry-run', action='store_true', help='Create receipt listing proposed actions but make no submissions')
    args = parser.parse_args()
    agreement = acknowledge()
    conn = connect(args.db)
    run = new_run(conn, args.command, agreement)
    code = 0
    try:
        if args.command == 'init':
            count = import_sources(conn, load_default_sources(), origin='bundled')[0]
            if args.profile.exists():
                print(f'Existing profile preserved: {args.profile}')
            else:
                sample = dict(first_name='YOUR_FIRST_NAME', last_name='YOUR_LAST_NAME',
                              address1='YOUR_STREET_ADDRESS', address2='', city='YOUR_CITY',
                              state='CA', zip='00000', email='', phone='')
                private_write(args.profile, json.dumps(sample, indent=2) + '\n')
                print(f'Created private profile template: {args.profile}. EDIT IT before subscription.')
            print(f'Added {count} bundled research sources. Verify official forms and local law before requests.')
        elif args.command == 'sync-defaults':
            fresh, changed = import_sources(conn, load_default_sources(), update=args.update, origin='bundled')
            print(f'Sources synchronized: {fresh} new, {changed} updated; existing event/receipt history preserved.')
        elif args.command == 'import-sources':
            fresh, changed = import_sources(conn, read_sources_file(Path(args.file)), args.update)
            print(f'Sources imported: {fresh} new, {changed} updated. All other duplicates were left intact.')
            print('Evidence URLs are imported as CLAIMS; YOU must verify their current content.')
        elif args.command == 'sources':
            print_sources(conn, category=args.category)
        elif args.command == 'history':
            print_sources(conn, history=True)
        elif args.command == 'check-sources':
            if not 2 <= args.failure_threshold <= 20 or not 1 <= args.timeout <= 120 or not 0 <= args.delay <= 30:
                raise ValueError('Invalid health check parameters')
            rows = conn.execute('SELECT * FROM sources ORDER BY slug').fetchall()
            if args.source:
                requested = {normalize_slug(v) for v in args.source}
                rows = [r for r in rows if r['slug'] in requested]
                if len(rows) != len(requested):
                    raise ValueError(f'Source not found: {requested - {r["slug"] for r in rows}}')
            stats = check_sources(conn, run, rows, args.timeout, args.delay,
                                  not args.no_repair, args.suggest, args.failure_threshold)
            run['notices'].append(f'Health check summary: {stats}')
            print('Health check:', stats)
        elif args.command == 'adopt-url':
            row = conn.execute('SELECT * FROM sources WHERE slug=?', (normalize_slug(args.source),)).fetchone()
            if row is None:
                raise ValueError('Unknown source slug')
            if not same_organization_host(row[args.field], args.url):
                raise ValueError('New URL must be on the same official hostname or subdomain; no blind domain swaps')
            if input('Have you personally verified the new official page? Type VERIFIED: ').strip() != 'VERIFIED':
                raise ValueError('No modification made')
            apply_url_change(conn, run, row, args.field, args.url, 'Manual source URL review')
            print(f'Updated {row["slug"]}.{args.field}; re-run check-sources')
        elif args.command == 'discover':
            if not 1 <= args.max_candidates <= 30:
                raise ValueError('--max-candidates must be between 1 and 30')
            print('AI providers may charge API/search fees. Your address profile is NOT sent.')
            if input('Authorize one paid/external AI request? Type SEARCH: ').strip() != 'SEARCH':
                raise ValueError('AI request not authorized')
            found = discover_candidates(conn, args.provider, args.model,
                                        args.category, args.max_candidates, args.check)
            run['candidate_ids'] = [item['id'] for item in found]
            for item in found:
                print(f'  {item["id"]} | {item["name"]} ({item["slug"]})')
                for url in item['urls']:
                    print(f'      {url}')
                if item['checks']:
                    print('      transport:', item['checks'])
            print(f'Stored {len(found)} untrusted candidates; verify postal signup AND opt-out before promotion.')
        elif args.command == 'candidates':
            for r in conn.execute('SELECT * FROM candidates ORDER BY discovered_at DESC LIMIT 150'):
                print(f'{r["id"]} {r["state"]:10} {r["provider"]:10} {r["slug"]}')
                print('  ' + r['payload'][:500])
                if r['citations'] != '[]':
                    print('  Citations:', r['citations'][:600])
        elif args.command == 'promote-candidate':
            row = conn.execute('SELECT * FROM candidates WHERE id=?', (args.id,)).fetchone()
            if row is None or row['state'] != 'pending':
                raise ValueError('Candidate ID not found or already handled')
            candidate = json.loads(row['payload'])
            print(json.dumps(candidate, indent=2))
            print('Check that the official site currently accepts free POSTAL subscriptions')
            print('and publishes a method to stop PHYSICAL mail. AI text is not proof.')
            if input('Type VERIFIED POSTAL SIGNUP AND OPTOUT: ').strip() != 'VERIFIED POSTAL SIGNUP AND OPTOUT':
                raise ValueError('Review not confirmed')
            fresh, _ = import_sources(conn, [{**candidate, 'default_enabled': False}], origin='ai-reviewed')
            if not fresh:
                raise ValueError('Source slug already exists; review duplicate manually')
            conn.execute("UPDATE candidates SET state='promoted' WHERE id=?", (args.id,))
            conn.commit()
            print('Imported for review, excluded from --all until enable-source is used.')
        elif args.command in ('enable-source','disable-source'):
            slug = normalize_slug(args.source)
            row = conn.execute('SELECT * FROM sources WHERE slug=?', (slug,)).fetchone()
            if not row:
                raise ValueError('Unknown source slug')
            if args.command == 'enable-source':
                if row['health'] == 'broken':
                    raise ValueError('Broken source must be repaired and rechecked before enabling')
                if input('Verified POSTAL subscription AND published opt-out? Type VERIFIED: ').strip() != 'VERIFIED':
                    raise ValueError('Manual verification required')
            conn.execute('UPDATE sources SET default_enabled=? WHERE slug=?',
                         (int(args.command == 'enable-source'), slug))
            conn.commit()
            print('Updated source default eligibility; audit records retained.')
        elif args.command == 'export-defaults':
            print(f'Exported {export_sources(conn, args.file, args.include_review)} reviewed defaults to {args.file}')
        elif args.command == 'build-docs':
            from manuals import write_manuals
            for generated in write_manuals(args.output):
                print('Generated:', generated)
        else:
            selected = pick_sources(conn, args, args.command)
            print(f'{len(selected)} organization(s) selected for {args.command}.')
            profile = load_profile(args.profile) if selected and not args.dry_run else {}
            if selected and not args.dry_run:
                print(f'ADDRESS: {profile["first_name"]} {profile["last_name"]}, {profile["address1"]}, {profile["city"]}, {profile["state"]} {profile["zip"]}')
                print('You must ACTUALLY be interested in EVERY selected company and its offerings.')
                if input('Is this YOUR legitimate postal address? Type MY ADDRESS: ').strip() != 'MY ADDRESS':
                    raise ValueError('Address ownership not confirmed; no submissions')
            for idx, row in enumerate(selected, start=1):
                print(f'\n[{idx}/{len(selected)}] {row["name"]} ({row["slug"]})')
                if args.dry_run:
                    record(conn, run, row, args.command, 'dry_run', 'No website opened and no request made')
                    print('DRY RUN:', row['subscribe_url' if args.command == 'subscribe' else 'unsubscribe_url'])
                    continue
                try:
                    spec = json.loads(row['automation'] or '{}').get(args.command)
                    if args.automate and spec:
                        status, details = automation_interactive(row, args.command, profile)
                    else:
                        if args.automate:
                            print('No reviewed browser adapter; using interactive assisted submission instead.')
                        status, details = assisted_interactive(row, args.command, args.no_browser)
                    record(conn, run, row, args.command, status, details)
                    print('Recorded:', status)
                except (KeyboardInterrupt, EOFError):
                    record(conn, run, row, args.command, 'not_submitted', 'Stopped by user before confirming submission')
                    print('\nStopped by user; remaining sources were not processed.')
                    break
                if idx < len(selected):
                    time.sleep(2.0)  # modest pacing; never rapid-fire repeated requests
    except (ValueError, OSError, json.JSONDecodeError, sqlite3.Error, ProviderError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        run['notices'].append(f'ERROR: {exc}')
        code = 1
    finally:
        receipt = finalize(conn, run, args.receipts)
        print(f'RECEIPT: {receipt.resolve()}')
        print(f'Request outcomes: {run["summary"]}')
        conn.close()
    return code


def main() -> int:
    try:
        return run_main()
    except (ValueError, KeyboardInterrupt) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
