From an installed copy, run `man spamalot`. See the [roff source](https://github.com/ckcameron/spamalot/blob/main/man/man1/spamalot.1).

```text
SPAMALOT(1)                          User Commands                          SPAMALOT(1)

NAME
     spamalot - manage consenting U.S. physical-postal catalog and print subscriptions

SYNOPSIS
     spamalot [--db DATABASE] [--profile FILE] [--receipts DIRECTORY] COMMAND [OPTIONS]

DESCRIPTION
     Track  requests for physical magazines, catalogs, church publications, NGO materi‐
     als, and policy circulars sent to the named recipient's  lawful  U.S.  postal  ad‐
     dress.   Spamalot opens official publisher pages so the named recipient can review
     and complete each request. Use an interactive terminal to acknowledge the  consent
     and  liability  notice  before  running  a  command. Dry runs preview the selected
     sources and write a local receipt without opening a  publisher  page.   A  receipt
     records  a  user report or browser observation. Confirm acceptance or cancellation
     with the publisher when needed.

COMMANDS
     init   Create a private example profile and import bundled sources into SQLite.

     sync-defaults [--update]
            Import new bundled sources without changing the local subscription history.
            --update refreshes known URLs/descriptions but  cannot  re-enable  disabled
            sources.

     sources [--category TEXT]
            List  sources,  their  postal  request  and  removal URLs, and their health
            state.

     subscribe [--all | --source SLUG | --file FILE] [--category TEXT] [--dry-run]
            Interactively request physical mail. Only eligible  nonbroken  sources  are
            selected by --all. Options --automate and --no-browser are supported.

     unsubscribe [--all | --source SLUG | --file FILE] [--dry-run]
            Show  the  publisher's  removal  procedure and open its page. --all selects
            sources with a recorded signup attempt, including disabled and  broken  en‐
            tries.

     check-sources [--source SLUG] [--no-repair] [--suggest]
            Run  read-only HTTPS checks of subscription, unsubscribe and evidence URLs.
            Check for HTTP failures and plausible page content. Apply same-organization
            HTTPS redirects only when the result passes basic content  inspection.  Two
            separate  missing-page checks disable a source by default; transient errors
            only flag review.

     adopt-url --source SLUG --field FIELD --url HTTPS_URL
            Manually accept an official replacement URL after reviewing the form.

     discover --provider {openai,gemini,perplexity} [--model MODEL] [--category TEXT]
     [--check]
            Call one public web-grounded AI API using a  locally  configured  API  key.
            This  may  incur  charges.  A  candidate is untrusted, requires a published
            postal unsubscribe method and does not enter the default list  without  re‐
            view.

     candidates
            Show unreviewed AI suggestions and the underlying URLs/citations.

     promote-candidate --id UUID
            Require  personal verification of postal signup and opt-out pages, then im‐
            port a candidate into SQLite. The source is initially disabled for --all.

     enable-source --source SLUG
            Enable a manually checked source for --all.

     disable-source --source SLUG
            Keep the source and history but exclude it from automatic --all selection.

     export-defaults --file FILE [--include-review]
            Write enabled sources with healthy or unchecked status to a new JSON  file.
            --include-review  adds  enabled  sources flagged for review. Existing files
            are protected from overwrite.

     import-sources --file FILE [--update]
            Import user-curated CSV/JSON sources with  official  physical-mail  opt-out
            details.   New  imports  are disabled by default. Review each source before
            enabling it.

     history
            Show recent subscription and cancellation audit records.

     build-docs [--output DIR]
            Create this manual page and operational Markdown reference files.

FILES
     profile.json
            Your legitimate U.S. street address, private to your machine; never sent to
            AI APIs.

     spamalot.sqlite3
            Source records, health checks, URL changes, request events  and  AI  candi‐
            dates.

     receipts/
            Timestamped, permission-restricted JSON receipts of acknowledged runs.

     default-sources.json
            Bundled  source catalog with source-specific printed-mail cancellation evi‐
            dence.

ENVIRONMENT
     OPENAI_API_KEY
            API key for OpenAI Responses API with web search.

     GEMINI_API_KEY
            API key for Gemini Grounding with Google Search.

     PERPLEXITY_API_KEY
            API key for the Perplexity Sonar API.

WARNINGS
     This program has not been tested for all legal ramifications. Review local,  state
     and  federal  law  and  every  merchant's  terms before making requests. It is re‐
     stricted to the actual named recipient at their own lawful  U.S.  postal  address.
     The  recipient must genuinely want each selected source's goods, services, or pub‐
     lications and accepts responsibility for their use. Author liability is disclaimed
     to the extent permitted by law.  Published site contact information  may  be  out‐
     dated. A successful HTTP status is not proof that a postal subscription or cancel‐
     lation  is  operational.  Neither the author nor the software offers any warranty,
     to the fullest extent allowed by law. License: CC BY-NC-SA 4.0; see LICENSE.txt.

SEE ALSO
     README.md, SOURCES.md,  docs/COMMANDS.md,  docs/ARCHITECTURE.md,  docs/SOURCE_FOR‐
     MAT.md.  Project wiki

spamalot 2.1.0                         2026-11-11                           SPAMALOT(1)
```
