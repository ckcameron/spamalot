# Security policy

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/ckcameron/spamalot/security/advisories). Select **Report a vulnerability** and include the affected version or commit, the operating system and Python version, and what an attacker could realistically read, change, or trigger. Use dummy data and redact logs. Keep real addresses, receipts, API keys, and vulnerability details out of public issues and pull requests.

Start with Spamalot 2.1.0 or the current `main` branch. If you only observed the issue in an older copy, report the version you tested and describe what you know. Use [GitHub Issues](https://github.com/ckcameron/spamalot/issues) for ordinary bugs such as stale publisher links.

## Scope and trust boundaries

Spamalot is a local Python CLI for the named recipient to manage physical U.S. postal-mail requests. It stores a recipient profile, a SQLite registry and audit history, and JSON receipts on the operator's machine. Optional network activity includes public HTTPS source checks, requests to an AI discovery provider, and visits to publisher pages in a browser.

Publisher pages and redirects, imported source lists, browser adapter definitions, and AI responses are external input. Review the CLI, its data and network handling, and the repository's build, test, and publishing workflows where they handle credentials or untrusted contributions.

## Security expectations

- Require recipient acknowledgment before operational commands. Live signup and cancellation must stay under the recipient's control. Dry runs must avoid the browser and the recipient profile.
- Keep profiles and audit data private. Discovery prompts must exclude recipient details and audit history. Provider keys must stay out of receipts, logs, and generated documentation.
- Source health checks should read public HTTPS pages, validate redirect destinations, and bound the amount of data read. Automatic URL repair is limited to qualifying same-organization redirects. Homepage suggestions and AI candidates require manual review before use. A health result must never stand in for consent or publisher acceptance.
- Preserve the distinction between a dry run, a user-reported request, and an observed browser confirmation. A receipt must accurately reflect the local outcome.
- Untrusted pull request code must not receive repository secrets or publishing credentials.

## What makes a report actionable

Prioritize a realistic path to unauthorized submissions, private data or credential disclosure, unexpected access to non-public network resources, unauthorized changes to trusted sources or audit history, or compromise of a release or publishing workflow. Explain what input an attacker controls and what action the recipient or maintainer would need to take.

An outdated URL or a publisher rejecting a request is usually a maintenance issue. Report it privately if it creates a security impact, such as sending a recipient's data to an unintended destination. The source checker uses best-effort URL and address checks and is intended for personal use. Offline tests use simulated responses and do not establish how a live publisher or provider will behave.
