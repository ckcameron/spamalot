# Development and maintenance

## Test and sanity-check

```sh
python3 -m unittest discover -v
python3 -m compileall -q spamalot.py source_health.py source_discovery.py manuals.py
python3 spamalot.py build-docs --output .
```

Tests use temporary or in-memory SQLite databases, stubbed HTTP replies, and stubbed provider payloads. They **do not** verify live merchant forms, actual mail delivery, or production API integration. Do not represent them otherwise.

## Coding conventions

- Keep public I/O boundaries explicit and validate before writing to the registry.
- Prefer descriptive function names, short comments explaining decisions, and standard Python types.
- Put changeable publisher URLs in the source registry rather than hardcoding them in code.
- Avoid hidden submissions, CAPTCHA bypasses, suppression of user consent, or fabricated success states.
- Add regression coverage for database migrations, source-health status transitions, and cancellation of disabled sources.
- Keep project output, profiles, receipts, secrets, and SQLite databases out of Git.

## Updating documentation

Edit the templates in `manuals.py` before regenerating `docs/COMMANDS.md`, `docs/ARCHITECTURE.md`, `docs/SOURCE_FORMAT.md`, or `man/man1/spamalot.1`. The `wiki/` pages are complementary, edited directly for GitHub Wiki.

## Publishing this wiki

GitHub Wiki uses its own Git repository: `https://github.com/ckcameron/spamalot.wiki.git`. GitHub may require enabling Wikis under **Settings → Features** and creating the first wiki page in the UI before the wiki remote exists.

After the wiki has been initialized, run the repo's **Sync wiki** GitHub Actions workflow manually. It copies the tracked `wiki/*.md` pages to the wiki's Git repository using an authorized token. It does not remove unrelated wiki pages.

If GitHub Actions does not have permission to push to the Wiki remote, configure the workflow's `WIKI_PUSH_TOKEN` secret with the required repository permissions or push the files through an authenticated local Git client. Never add a PAT to source control.