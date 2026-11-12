# Architecture and testing

## Local data

`spamalot.py` handles the CLI and stores the registry, request events, source
checks, URL changes, and discovery queue in SQLite. It migrates older databases
in place. The bundled JSON supplies the default registry. The CSV is a readable
copy of the same records.

Operational commands require the interactive consent notice before a run
starts. Dry runs use the registry and write an audit receipt. They skip the
address profile and browser. For a live request, the named recipient confirms
their address and reviews each publisher's form. Keep the profile, database,
and receipts in a private working directory.

## Source checks and discovery

`source_health.py` reads public HTTPS pages with timeouts, a redirect limit,
and a bounded response body. A 200 response can come from an email-only form
or an obsolete page. Repeated missing pages disable the source for
`subscribe --all`. An access challenge, timeout, or other uncertain response
gets flagged for review. Signup history remains available for
`unsubscribe --all`, even for disabled or broken sources.

A redirect on the same organizational host can replace a URL if the target
passes the page checks. Run with `--no-repair` to check without applying
redirect changes. Homepage link suggestions are for manual review. The
`source_changes` table records applied URL changes.

`source_discovery.py` sends a research prompt and optional category to the
selected AI provider. The prompt excludes the local profile and audit history.
Results go to the candidate queue. Before promoting one, confirm the
publisher offers physical mail and documents how to stop it. Promoted
candidates start disabled.

## Tests and documentation

```sh
python3 -m unittest discover -v
python3 -m compileall -q spamalot.py source_health.py source_discovery.py manuals.py
spamalot --help
```

GitHub Actions runs the offline suite and checks the installed command,
bundled registry, and manual on Ubuntu with Python 3.10 through 3.14. The tests
use temporary databases and simulated browser, HTTP, or provider behavior.
They do not validate live signup and removal forms, delivery, or paid AI APIs.

Edit the reference text in `manuals.py`, then run
`spamalot build-docs --output .` from the repository root to regenerate
the Markdown references and `man/man1/spamalot.1`.
