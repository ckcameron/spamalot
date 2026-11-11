# Source format

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
