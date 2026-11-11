# Spamalot

> A mailbox is a terrible thing to waste. Use your **own** mailbox.

Spamalot tracks requests for free, physical U.S. postal mail: printed catalogs, religious publications, NGO newsletters, and policy circulars. It keeps an SQLite source registry, lets the recipient make or cancel requests interactively, checks published source pages, and writes local JSON audit receipts.

**Important:** Spamalot is only for the actual consenting recipient at an address where they lawfully receive mail. It is untested for legal ramifications. Check applicable law and publisher terms. No warranty or author liability is offered beyond what applicable law permits. Do not run unfamiliar code or use third-party names or addresses.

## Contents

- [[Getting-Started]] — installation, initialization, consent, upgrades
- [[Commands]] — CLI reference and working examples
- [[Sources-and-Formats]] — curated registry, CSV/JSON imports, eligible sources
- [[Source-Health]] — HTTP status checks, redirects, broken sources
- [[AI-Discovery]] — optional external research and candidate review
- [[Browser-Operations]] — interactive subscriptions, cancellations, and automation
- [[Receipts-and-Data]] — SQLite, receipts, private profiles, event semantics
- [[Architecture]] — modules, trust boundaries, and design decisions
- [[Development]] — tests, maintenance, documentation generation
- [[Safety-and-Licensing]] — legal scope, recipient consent, licensing
- [[Troubleshooting]] — common failures and what they mean

The bundled registry contains 45 organizations. **That is not a count of verified successful subscriptions.** Live publisher forms and AI services are not covered by offline tests.

Source: [GitHub repository](https://github.com/ckcameron/spamalot). The editable canonical wiki pages are also kept in [`wiki/`](https://github.com/ckcameron/spamalot/tree/main/wiki).