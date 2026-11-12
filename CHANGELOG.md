# Changelog

Last signed update: 11 November, 2026

## Unreleased

- Added the GitHub wiki and updated the README, command reference, source format,
  architecture guide, source directory, and manual.
- Clarified receipts, source health checks, and the discovery review queue.
- Added offline tests and pull request checks for Python 3.10–3.14.

## 2.1.0 — Spamalot name and presentation

- Renamed the executable module to `spamalot.py` and the Unix man page to `spamalot(1)`.
- Added an installable `spamalot` command with the bundled registry and man page.
- Added local SVG header artwork and a slow-flashing red warning GIF, with static text fallback in the README.
- Updated CLI examples, reference documentation, and bundled source metadata.
- Changed the default new-installation database name to `spamalot.sqlite3`. Existing databases remain compatible using `--db postal_mail.sqlite3`.
- No new merchant registrations, cancellations, health checks, or AI API calls were executed for this repackaging release.


## 2.0.0 — 2026-11-03

- Increased curated physical postal-mail sources to 45, including the earlier 33 (minus a non-postal print-at-home listing) and 13 additional official print-mail sources.
- Moved original five embedded sources into the authoritative `default-sources.json`; refreshed the full CSV mirror.
- Added source health checks for print signup, removal and evidence pages; conservative broken-page detection, safe HTTPS redirect repairs and manually reviewed link suggestions.
- Added audit tables for source checks, URL changes and AI research candidates. Existing v1/v1.1 databases are migrated without removing request history.
- Added source enabling/disabling, source export and explicit verified URL replacement commands.
- Added optional OpenAI, Gemini and Perplexity web-grounded research adapters, with review-only queue and explicit human promotion.
- Added the man-page and Markdown reference generator plus source directory and offline maintenance tests.
- Preserved separate interactive subscription, selective or blanket unsubscription, per-run receipts, and local privacy protections.

## 1.1.0 — 2026-11-02

- Expanded catalog/church/NGO/policy source list and added category filtering and default registry synchronization.

## 1.0.0 — 2026-11-02

- Initial consent-first interactive physical postal-mail subscription and cancellation tracker with SQLite and JSON receipts.
