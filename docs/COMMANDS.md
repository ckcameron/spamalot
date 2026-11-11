# Command reference

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
