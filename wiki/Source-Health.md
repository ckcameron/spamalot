# Source health and URL maintenance

`check-sources` performs **read-only** requests to the subscription, cancellation, and evidence URLs recorded for each source. It does not fill out publisher forms, prove that printed mail will arrive, or confirm that an opt-out was accepted.

```sh
python3 spamalot.py check-sources --suggest
python3 spamalot.py check-sources --source highcountrygardens
python3 spamalot.py check-sources --source highcountrygardens --no-repair
```

The checker uses HTTPS, bounded redirects, response-size limits, transport status codes, and basic text heuristics. Redirects within the same organization's hostname/subdomain family may be adopted when the target passes basic inspection. Other domain moves require manual verification.

**States**

- **healthy:** pages were reachable with plausible content, not necessarily functional forms.
- **review:** access challenge, timeout, temporary server failure, ambiguous page, or first missing-page observation.
- **broken:** repeated missing-page responses (HTTP 404/410 or plausible soft 404) reach the configured failure threshold (default: two consecutive checks).

Broken sources are disabled for default `subscribe --all` selection, but their audit history and opt-out details remain available. A transient network error is not grounds for deletion.

`--suggest` searches official homepage links for possible replacements; suggestions are **not** silently adopted. Inspect the relevant page yourself and run:

```sh
python3 spamalot.py adopt-url --source highcountrygardens --field subscribe_url --url https://www.highcountrygardens.com/pages/mail-sign-up
```

The example URL must be verified before use. `adopt-url` changes local metadata and writes a URL-change event; it does not establish live publisher acceptance.

Security boundary: the checker rejects obvious local/private network destinations but is not a fully DNS-rebinding-resistant sandbox. Do not run it as a privileged system service on untrusted networks.

See [[Sources-and-Formats]] and [[Architecture]].