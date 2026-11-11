"""Build the installable man page and operational documentation."""

from __future__ import annotations

from pathlib import Path

MAN = r''' .TH SPAMALOT 1 "2026-11-03" "spamalot 2.1" "User Commands"
.SH NAME
spamalot \- manage consenting U.S. physical-postal catalog and print subscriptions
.SH SYNOPSIS
.B spamalot
.RI [ --db " DATABASE" ]
.RI [ --profile " FILE" ]
.RI [ --receipts " DIRECTORY" ]
.I COMMAND
.RI [ OPTIONS ]
.SH DESCRIPTION
Track requests for physical magazines, catalogs, church publications, NGO materials,
and policy circulars sent to the named recipient's lawful U.S. postal address.
No electronic-only subscriptions are included. The program opens official web pages,
asks the user to make and confirm each request, and creates a local JSON receipt.
It never submits an entire bulk batch unattended and never bypasses anti-bot controls.
No merchant acceptance or actual delivery is guaranteed.
.SH COMMANDS
.TP
.B init
Create a private example profile and import bundled sources into SQLite.
.TP
.B sync-defaults [--update]
Import new bundled sources without changing the local subscription history.
--update refreshes known URLs/descriptions but cannot re-enable disabled sources.
.TP
.B sources [--category TEXT]
List sources, their postal request and removal URLs, and their health state.
.TP
.B subscribe [--all | --source SLUG | --file FILE] [--category TEXT] [--dry-run]
Interactively request physical mail. Only eligible nonbroken sources are selected
by --all. Options --automate and --no-browser are supported.
.TP
.B unsubscribe [--all | --source SLUG | --file FILE] [--dry-run]
Interactively request postal-mail removal. --all covers recorded past subscriptions,
not all U.S. direct marketers. Opt-out remains possible for a disabled source.
.TP
.B check-sources [--source SLUG] [--no-repair] [--suggest]
Run read-only HTTPS checks of subscription, unsubscribe and evidence URLs.
Check for HTTP failures and plausible page content. Apply same-organization HTTPS
redirects only when the result passes basic content inspection. Two separate
missing-page checks disable a source by default; transient errors only flag review.
.TP
.B adopt-url --source SLUG --field FIELD --url HTTPS_URL
Manually accept an official replacement URL after reviewing the form.
.TP
.B discover --provider {openai,gemini,perplexity} [--model MODEL] [--category TEXT] [--check]
Call one public web-grounded AI API using a locally configured API key. This may
incur charges. A candidate is untrusted, requires a published postal unsubscribe
method and does not enter the default list without review.
.TP
.B candidates
Show unreviewed AI suggestions and the underlying URLs/citations.
.TP
.B promote-candidate --id UUID
Require personal verification of postal signup and opt-out pages, then import
a candidate into SQLite. The source is initially disabled for --all.
.TP
.B enable-source --source SLUG
Enable a manually checked source for --all.
.TP
.B disable-source --source SLUG
Keep the source and history but exclude it from automatic --all selection.
.TP
.B export-defaults --file FILE [--include-review]
Write enabled, nonbroken source entries to new JSON. Does not overwrite source
bundles unless the caller explicitly names their path. A new export will not
include disabled or broken sources.
.TP
.B import-sources --file FILE [--update]
Import user-curated CSV/JSON sources with official physical-mail opt-out details.
Imported sources are disabled until individually reviewed and enabled.
.TP
.B history
Show recent subscription and cancellation audit records.
.TP
.B build-docs [--output DIR]
Create this manual page and operational Markdown reference files.
.SH FILES
.TP
.I profile.json
Your legitimate U.S. street address, private to your machine; never sent to AI APIs.
.TP
.I spamalot.sqlite3
Source records, health checks, URL changes, request events and AI candidates.
.TP
.I receipts/
Timestamped, permission-restricted JSON receipts of acknowledged runs.
.TP
.I default-sources.json
Bundled source catalog with source-specific printed-mail cancellation evidence.
.SH ENVIRONMENT
.TP
.B OPENAI_API_KEY
API key for OpenAI Responses API with web search.
.TP
.B GEMINI_API_KEY
API key for Gemini Grounding with Google Search.
.TP
.B PERPLEXITY_API_KEY
API key for the Perplexity Sonar API.
.SH WARNINGS
This program has not been tested for all legal ramifications. Review local,
state and federal law and every merchant's terms before making requests. It is
restricted to the actual named recipient at their own lawful U.S. postal address.
The recipient must genuinely want each selected source's goods, services, or
publications and accepts responsibility for their use. Author liability is
disclaimed to the extent permitted by law.
Published site contact information may be outdated. A successful HTTP status
is not proof that a postal subscription or cancellation is operational.
Neither the author nor the software offers any warranty, to the fullest extent
allowed by law. License: CC BY-NC-SA 4.0; see LICENSE.txt.
.SH SEE ALSO
README.md, SOURCES.md, docs/ARCHITECTURE.md, docs/SOURCE_FORMAT.md
'''

COMMANDS = '''# Command reference

Run `spamalot --help` for argument-level help. Each acknowledged run produces
an audit receipt in `receipts/`, including failed operations and dry runs.
Operations require a local interactive acknowledgment. The address profile is
used only for the user-managed signup and cancellation actions.

| Command | Purpose |
| --- | --- |
| `init` | Initialize SQLite, bundled records, and a private profile template. |
| `sync-defaults` | Merge newly bundled sources into an existing installation. |
| `sources` / `history` | List current status and past request events. |
| `subscribe --all --dry-run` | Preview all eligible, nonbroken postal sources. |
| `subscribe --source slug` | Open an individual postal request form. |
| `unsubscribe --all` | Individually request opt-out for all historically requested sources. |
| `check-sources --suggest` | Read-only checks, safe redirect repair and official-site URL suggestions. |
| `adopt-url` | Apply one manually verified replacement on the same organization domain. |
| `discover --provider gemini --category NGO --check` | Get source candidates from public web-grounded AI. |
| `candidates` / `promote-candidate` | Examine and manually accept a discovery result. |
| `enable-source` / `disable-source` | Change default eligibility without deleting history. |
| `export-defaults --file new-defaults.json` | Export enabled sources with health status not marked broken. |
| `import-sources --file verified.csv` | Import custom candidates, disabled pending verification. |
| `build-docs` | Generate this guide, man page and architecture notes. |

`--all` never silently includes a candidate or source marked as broken.
Manual opt-out remains available for previously used broken/disabled sources.

## Checking a source

```console
spamalot check-sources --source territorial --suggest
spamalot check-sources --source territorial --no-repair
spamalot adopt-url --source territorial --field subscribe_url --url https://territorialseed.com/pages/catalogs
spamalot check-sources --source territorial
```

On the first confirmed missing-page check the source becomes `review`; a second
consecutive confirmed missing-page check marks it `broken` and disables it for
`subscribe --all`. A 403, bot challenge, timeout or 500 is inconclusive and stays
`review`. A 200 response alone cannot establish that a form works. In most cases
human validation is still necessary. The health checker uses HTTPS GET only.
Request outcomes are recorded separately during signup and cancellation.

## AI source discovery

```console
export GEMINI_API_KEY='your-key'
spamalot discover --provider gemini --category 'church print magazines' --check
spamalot candidates
spamalot promote-candidate --id <candidate-uuid>
spamalot check-sources --source <new-slug>
spamalot enable-source --source <new-slug>
```

Providers are OpenAI, Gemini and Perplexity. All require a provider-specific API
key and may charge for web-grounded requests. The AI call includes only the
research category, never the postal address, profile or receipt history. There
is no automation of CAPTCHA, checkout, mass form submissions or third-party
recipients. AI sources are untrusted until personally verified against the
publisher's own postal subscription and opt-out pages.
'''

SOURCE_FORMAT = '''# Source format

`spamalot_data/default-sources.json` contains an object with a `sources` list; imported CSV
rows use the same source keys. All links must use `https://`.

```json
{
  "slug": "sampleprint",
  "name": "Example Print Publisher",
  "category": "Catalog / Example",
  "subscribe_url": "https://publisher.example/catalog-request",
  "unsubscribe_url": "https://publisher.example/mail-preferences",
  "optout_instructions": "Contact subscriber services to stop physical mail at the listed postal address.",
  "evidence_url": "https://publisher.example/privacy",
  "notes": "Physical paper only; deselect any optional email offers.",
  "automation": {},
  "default_enabled": false
}
```

Do **not** import this illustrative example as a real source. Each actual
source must have an official published postal removal process; email-only
unsubscribe links do not qualify. `default_enabled=false` excludes a record
from `subscribe --all` but keeps its details for review and historical opt-out.
A manually curated imported record starts disabled regardless of its request
status; use `enable-source` once personally verified.

The source schema also supports manually reviewed Playwright adapters, but
none are required to run the normal assisted-browser workflow. Do not guess
form selectors or submit requests unattended; never bypass website protections.
'''

ARCHITECTURE = '''# Architecture and verification limits

- **Storage:** SQLite retains sources, request events, read-only HTTP checks,
  URL-change history, AI candidates and run metadata. Existing v1 databases
  are migrated in place; old events and opt-out records remain accessible.
- **Default dataset:** all bundled records come from a single curated JSON registry. CSV is regenerated from that
  registry, not edited independently.
- **Health checks:** `source_health.py` fetches public HTTPS pages with timeouts,
  bounded redirect handling and limited HTML inspection. It rejects known
  non-public IP destinations, but is not a hardened network proxy or crawler.
  A 200 page may be email-only or accept no requests, and an anti-bot 403
  need not mean the source is gone. Two consecutive HTTP 404/410 or soft-404
  observations disable a source; otherwise uncertain results remain for review.
- **URL repair:** a canonical redirect on the same organizational hostname,
  with suitable page content, may be adopted automatically. Different domains
  are never adopted automatically. Official-homepage link suggestions are
  review-only. Changes are stored in `source_changes`.
- **Discovery:** `source_discovery.py` makes a single authenticated call to a
  chosen public, search-enabled AI API. Its text is treated as untrusted and
  stored in `candidates`; a human must confirm it offers physical postal mail
  *and* a documented postal cancellation mechanism. The profile is never
  included in the research prompt.
- **Subscription workflow:** Browser assisted and confirmation-based. Receipts
  record user statements or configured confirmation selectors, not delivery.
  There are no unattended submissions to external websites.
- **Opt-outs:** The `unsubscribe --all` command covers every source with a
  recorded attempted/confirmed signup, even if its status later became broken.
  This is not a universal USPS or industry suppression service.

## Release verification

```console
python3 -m unittest discover -v
python3 -m compileall -q .
spamalot --help
```

No live merchant requests or cancellations are made by these tests. API
contracts may evolve; confirm current documentation and set a supported model.
The health checker and AI integrations must be tested against real services by
an authorized user; the packaged offline tests do not verify their uptime.
'''


def write_manuals(output: Path) -> list[Path]:
    files = {
        'man/man1/spamalot.1': MAN.lstrip(),
        'docs/COMMANDS.md': COMMANDS,
        'docs/SOURCE_FORMAT.md': SOURCE_FORMAT,
        'docs/ARCHITECTURE.md': ARCHITECTURE,
    }
    paths = []
    for relative, content in files.items():
        dest = output / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding='utf-8')
        paths.append(dest)
    return paths
