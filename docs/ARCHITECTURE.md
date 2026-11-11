# Architecture and verification limits

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
