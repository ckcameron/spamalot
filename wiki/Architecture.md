# Architecture

Spamalot is a small Python command-line program with intentionally explicit boundaries.

| Module | Responsibilities |
| --- | --- |
| `spamalot.py` | CLI, recipient acknowledgment, SQLite schema and migrations, source import, request selection, events and receipts |
| `source_health.py` | Read-only HTTPS inspection, redirect evaluation and candidate replacement URLs |
| `source_discovery.py` | Optional API-keyed research adapters (OpenAI, Gemini, Perplexity), response normalization |
| `manuals.py` | Canonical local man-page and Markdown-reference templates |
| `default-sources.json` | Bundled source metadata |
| `test_spamalot.py`, `test_maintenance.py` | Offline regression tests |

## Boundaries worth keeping

1. **User consent:** an explicit interactive acknowledgment; no unattended --yes mode.
2. **Recipient data:** local profile used for opted-in forms, never for AI research prompts.
3. **Public source checks:** no form submissions and no assertion that reachable pages are operational.
4. **Candidate quarantine:** generated suggestions remain pending until manual verification and enabling.
5. **Durable history:** source updates and broken links do not erase request events or past opt-out instructions.
6. **Accurate receipts:** the app records what was attempted or observed, not imagined publisher acceptance.

A publisher may change an HTML form without changing its URL. This is why a health-check result and a working browser adapter are distinct concepts. Treat saved CSS selectors as brittle and inspect them before use.

The current code favors ordinary Python standard-library data access and per-source operations over introducing a background crawler or distributed service. Read [the architecture reference](https://github.com/ckcameron/spamalot/blob/main/docs/ARCHITECTURE.md) for the operational limitations.