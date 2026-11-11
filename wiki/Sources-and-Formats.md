# Source registry and import formats

The bundled `default-sources.json` is authoritative. `default-sources.csv` is its human-editable/exportable counterpart. `SOURCES.md` is the publisher-by-publisher index of physical subscription and postal opt-out instructions.

## Required source fields

| Field | Meaning |
| --- | --- |
| `slug` | Unique lowercase identifier (2–64 characters; letters, digits, `_`, `-`) |
| `name` | Organization or publication name |
| `category` | Catalog, Church, NGO, Political, etc. |
| `subscribe_url` | Official HTTPS URL for the **physical-mail** request |
| `unsubscribe_url` | Published physical-mail removal/contact URL |
| `optout_instructions` | Human-readable, specific printed-mail cancellation procedure |
| `evidence_url` | Official HTTPS evidence supporting the request and opt-out route |
| `notes` | Eligibility, optional email/SMS, or restrictions |
| `automation` | Optional explicit Playwright selector configuration; normally empty |

An import must document a **postal** opt-out, not only an email unsubscribe link. URLs must use HTTPS. CSV and JSON are accepted:

```sh
python3 spamalot.py import-sources --file more-sources.csv
python3 spamalot.py import-sources --file more-sources.json --update
python3 spamalot.py sources --category NGO
```

Newly imported sources start disabled pending inspection. Do not infer that every page currently works merely because an HTTP request returns 200.

The catalog contains 45 curated entries, but some may change or disappear. Run source checks, inspect the relevant publisher policy, and exclude any that require unwanted electronic subscriptions or donations.

See [`docs/SOURCE_FORMAT.md`](https://github.com/ckcameron/spamalot/blob/main/docs/SOURCE_FORMAT.md) and [`SOURCES.md`](https://github.com/ckcameron/spamalot/blob/main/SOURCES.md).