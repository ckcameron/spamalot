# Command reference

Use `python3 spamalot.py --help` and `python3 spamalot.py <command> --help` for the locally installed version's exact option list.

| Command | Action |
| --- | --- |
| `init` | Create private profile template and seed bundled sources |
| `sync-defaults [--update]` | Merge bundled source records into an existing registry |
| `sources [--category X]` | Show source URLs, state, and category |
| `history` | Show recent local request events |
| `subscribe --source SLUG` | Interactive physical-mail request |
| `subscribe --file FILE` | Select sources from text, CSV, or JSON |
| `subscribe --all [--category X]` | Iterate eligible sources, still requiring user review |
| `unsubscribe --source SLUG` | Interactive postal opt-out |
| `unsubscribe --file FILE` | Opt out of an input-file selection |
| `unsubscribe --all` | Revisit all historically requested sources in the local database |
| `check-sources [--suggest]` | Read-only HTTP tests and optional replacement suggestions |
| `adopt-url --source SLUG --field FIELD --url URL` | Manually approve corrected official HTTPS URL |
| `discover --provider NAME [--category X] [--check]` | Search AI API for untrusted candidates |
| `candidates` | Inspect candidate queue |
| `promote-candidate --id UUID` | Add manually verified candidate (initially disabled) |
| `enable-source / disable-source --source SLUG` | Control eligibility |
| `import-sources --file FILE [--update]` | Import curated source data |
| `export-defaults --file FILE [--include-review]` | Export enabled, nonbroken records |
| `build-docs --output .` | Regenerate local Markdown command docs and man page |

Global options: `--db`, `--profile`, `--receipts`.

### Examples

```sh
python3 spamalot.py check-sources --suggest
python3 spamalot.py check-sources --source highcountrygardens --no-repair
python3 spamalot.py subscribe --all --dry-run
python3 spamalot.py unsubscribe --all
python3 spamalot.py build-docs --output .
man -l man/man1/spamalot.1
```

Input-file formats: plain text with one slug per line, CSV with a `slug` column, or JSON list (or JSON `{"sources":[...]}`). Subscription and cancellation are intentionally separate commands; there is no inferred opt-out from a signup.

Use the [complete generated command reference](https://github.com/ckcameron/spamalot/blob/main/docs/COMMANDS.md) for additional details.