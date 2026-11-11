# Troubleshooting

**A publisher page returns 403, 429, or CAPTCHA.** These are review conditions, not proof that a source is broken. Open the official page manually; do not bypass anti-bot controls.

**A source is marked broken.** Inspect the stored URL, look for official replacement pages, and use `adopt-url` after verification. Two consecutive missing-page checks can disable a default. Historic cancellation records are retained.

**The publisher redirects to another company/domain.** The checker will not automatically trust an unrelated domain. Confirm ownership and the new postal opt-out policy manually.

**A receipt says `request_unverified`.** It records uncertainty, not success. Confirm with the publisher directly before repeating requests.

**`unsubscribe --all` does not include every advertiser.** It operates only on sources previously recorded in the local registry. External postal suppression services are beyond the application's scope.

**An AI candidate has no usable postal opt-out.** Discard it. An email unsubscribe link alone is not enough.

**No AI key or model error.** Set the provider-specific environment variable and verify current model/API support and billing arrangements.

**Browser automation refuses to submit.** The site lacks a reviewed adapter, a selector may have changed, or the visible per-request confirmation was not given. Use ordinary assisted mode and inspect the actual form.

**I can't open the live GitHub Wiki.** Enable the Wiki feature and create its initial `Home` page in the GitHub UI. The pages are also browseable under [`wiki/`](https://github.com/ckcameron/spamalot/tree/main/wiki). Run the manual Sync wiki workflow once Wiki is initialized and an authorized token is configured. See [[Development]].