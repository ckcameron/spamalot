# Data model, receipts, and privacy

Spamalot stores its working state locally.

- **`profile.json`**: named recipient and their lawful U.S. mailing address; keep private.
- **`spamalot.sqlite3`**: source metadata, checks, candidates, URL changes, runs, and request events.
- **`receipts/`**: one locally written timestamped JSON receipt per acknowledged run, including no-ops and dry runs.
- **`default-sources.json`**: public bundled reference list, not personal data.

## Main database tables

| Table | Purpose |
| --- | --- |
| `sources` | URLs, postal opt-out instructions, category, enablement, and health |
| `runs` | Execution identifiers, acknowledgment and completion metadata |
| `events` | Per-source subscribe/unsubscribe request outcomes |
| `checks` | Per-URL health observations |
| `candidates` | Untrusted AI proposals and citations |
| `source_changes` | Audit trail of edited source URLs |

## Event semantics

- `user_reported_submitted`: recipient says a request was submitted.
- `site_confirmation_observed`: configured browser confirmation selector appeared.
- `request_unverified`: operation may have occurred; acceptance is uncertain.
- `not_submitted`: no completed request was reported.
- `dry_run`: preview only; no publisher submission.

**None proves postal delivery or vendor-side processing.** Database migrations retain existing records. A source marked broken remains available for cancellation lookup.

## Securing local data

Do not commit `profile.json`, SQLite files, receipts, keys, or other personal information. Store project and data on a trusted local filesystem and back up your database before upgrades. On POSIX, the application uses restrictive permissions for key generated files, but your OS backups/sync software remain your responsibility.

AI research does not send the profile or event history to the provider. Browser-assisted submissions necessarily disclose recipient data to the chosen publisher, as reviewed by the user.