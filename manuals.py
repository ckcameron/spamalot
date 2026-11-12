"""Build the installable man page and operational documentation."""

from __future__ import annotations

from pathlib import Path

# Edit the templates here, then regenerate the checked-in docs with build-docs.
MAN = r''' .TH SPAMALOT 1 "2026-11-11" "spamalot 2.1.0" "User Commands"
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
Spamalot opens official publisher pages so the named recipient can review and
complete each request. Use an interactive terminal to acknowledge the consent
and liability notice before running a command. Dry runs preview the selected
sources and write a local receipt without opening a publisher page.
A receipt records a user report or browser observation. Confirm acceptance
or cancellation with the publisher when needed.
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
Show the publisher's removal procedure and open its page. --all selects
sources with a recorded signup attempt, including disabled and broken entries.
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
Write enabled sources with healthy or unchecked status to a new JSON file.
--include-review adds enabled sources flagged for review. Existing files are
protected from overwrite.
.TP
.B import-sources --file FILE [--update]
Import user-curated CSV/JSON sources with official physical-mail opt-out details.
New imports are disabled by default. Review each source before enabling it.
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
README.md, SOURCES.md, docs/COMMANDS.md, docs/ARCHITECTURE.md, docs/SOURCE_FORMAT.md.
.UR https://github.com/ckcameron/spamalot/wiki
Project wiki
.UE
'''

COMMANDS = '''# Command reference

Run `spamalot --help` for options. Operational commands require an
acknowledgment in an interactive terminal. Once a run starts, Spamalot saves
its receipt in `receipts/`, including dry runs and failed operations. Pass
`--db`, `--profile`, or `--receipts` before the subcommand to use another path.

| Command | Purpose |
| --- | --- |
| `init` | Initialize SQLite, bundled records, and a private profile template. |
| `sync-defaults` | Merge newly bundled sources into an existing installation. |
| `sources` / `history` | List current status and past request events. |
| `subscribe --all --dry-run` | Preview all eligible, nonbroken postal sources. |
| `subscribe --source slug` | Open an individual postal request form. |
| `unsubscribe --source SLUG` | Show the publisher's removal instructions and open its page. |
| `unsubscribe --all` | Go through all sources with a recorded signup attempt. |
| `check-sources --suggest` | Read-only checks, safe redirect repair and official-site URL suggestions. |
| `adopt-url` | Apply one manually verified replacement on the same organization domain. |
| `discover --provider gemini --category NGO --check` | Get source candidates from public web-grounded AI. |
| `candidates` / `promote-candidate` | Examine and manually accept a discovery result. |
| `enable-source` / `disable-source` | Change default eligibility without deleting history. |
| `export-defaults --file new-defaults.json` | Export enabled sources with healthy or unchecked status. Add `--include-review` to include enabled sources under review. |
| `import-sources --file my-sources.csv` | Import a CSV or JSON registry. New imports are disabled by default. |
| `build-docs` | Generate this guide, man page and architecture notes. |

## Select and record requests

Use `--source SLUG` for a single publisher or repeat it for several. A
`--file` list accepts slugs as one-per-line text, a JSON array, or CSV with a
`slug` column. `subscribe --all` selects enabled sources that are eligible for
a new request. `unsubscribe --all` uses signup history and includes sources
that later broke or were disabled.

`--dry-run` previews the selection and records it locally without using the
address profile or opening a browser. `--no-browser` prints the URLs for you
to open yourself. For a live request, confirm your address and complete the
publisher's own procedure. The receipt records your report or a browser
confirmation signal. Contact the publisher to confirm its decision.

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
New custom imports are disabled by default. Omit `default_enabled` in
CSV and use a JSON Boolean if you include the field in JSON. After you
check the signup and removal routes, run `enable-source --source SLUG`.
Use `import-sources --update` to refresh details for existing slugs while
keeping their local health, eligibility, and request history.

The source schema also supports manually reviewed Playwright adapters, but
none are required to run the normal assisted-browser workflow. Do not guess
form selectors or submit requests unattended; never bypass website protections.
'''

ARCHITECTURE = '''# Architecture and testing

## Local data

`spamalot.py` handles the CLI and stores the registry, request events, source
checks, URL changes, and discovery queue in SQLite. It migrates older databases
in place. The bundled JSON supplies the default registry. The CSV is a readable
copy of the same records.

Operational commands require the interactive consent notice before a run
starts. Dry runs use the registry and write an audit receipt. They skip the
address profile and browser. For a live request, the named recipient confirms
their address and reviews each publisher's form. Keep the profile, database,
and receipts in a private working directory.

## Source checks and discovery

`source_health.py` reads public HTTPS pages with timeouts, a redirect limit,
and a bounded response body. A 200 response can come from an email-only form
or an obsolete page. Repeated missing pages disable the source for
`subscribe --all`. An access challenge, timeout, or other uncertain response
gets flagged for review. Signup history remains available for
`unsubscribe --all`, even for disabled or broken sources.

A redirect on the same organizational host can replace a URL if the target
passes the page checks. Run with `--no-repair` to check without applying
redirect changes. Homepage link suggestions are for manual review. The
`source_changes` table records applied URL changes.

`source_discovery.py` sends a research prompt and optional category to the
selected AI provider. The prompt excludes the local profile and audit history.
Results go to the candidate queue. Before promoting one, confirm the
publisher offers physical mail and documents how to stop it. Promoted
candidates start disabled.

## Tests and documentation

```sh
python3 -m unittest discover -v
python3 -m compileall -q spamalot.py source_health.py source_discovery.py manuals.py
spamalot --help
```

GitHub Actions runs the offline suite and checks the installed command,
bundled registry, and manual on Ubuntu with Python 3.10 through 3.14. The tests
use temporary databases and simulated browser, HTTP, or provider behavior.
They do not validate live signup and removal forms, delivery, or paid AI APIs.

Edit the reference text in `manuals.py`, then run
`spamalot build-docs --output .` from the repository root to regenerate
the Markdown references and `man/man1/spamalot.1`.
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
