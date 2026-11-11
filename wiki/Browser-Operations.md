# Subscribing, cancelling, and browser adapters

## Assisted mode

`subscribe` opens a source's official printed-mail request page. You complete the form, verify any optional email/SMS selections, and answer whether you actually submitted a **physical-mail** request. The program records that report; it cannot independently establish acceptance.

```sh
python3 spamalot.py subscribe --source highcountrygardens
python3 spamalot.py subscribe --all --category Catalog
```

## Cancellation

`unsubscribe` is separate. For each source it displays the published postal opt-out instructions and opens the relevant page. If an organization requires a letter, phone call, or email request to stop **postal mail**, carry out that step yourself.

```sh
python3 spamalot.py unsubscribe --source highcountrygardens
python3 spamalot.py unsubscribe --file cancellations.txt
python3 spamalot.py unsubscribe --all
```

Blanket opt-out means **all sources with previously recorded subscription requests**, not all advertisers in the United States. Previously disabled/broken sources remain eligible for opt-out.

## Optional Playwright

Reviewed source definitions may include explicit `automation.subscribe` or `automation.unsubscribe` selectors mapping page fields to profile keys plus specific submit and confirmation selectors. Install Playwright separately and launch with `--automate`.

The browser remains **visible** and requires a per-form `SUBMIT` confirmation after you inspect the populated fields, privacy/marketing checkboxes, payment and consent terms. No default site-specific adapters are verified. Do not bypass CAPTCHA, rate limiting, access controls, or platform terms.

Receipts distinguish operator reports, observed confirmation selectors, and unverified requests. See [[Receipts-and-Data]].