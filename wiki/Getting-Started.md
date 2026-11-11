# Getting started

## Prerequisites

Python **3.10 or newer**; SQLite and other core dependencies are included in Python's standard library. The optional visible-browser automation uses Playwright and requires a site-specific adapter.

Clone or unpack the repository, then initialize:

```sh
python3 spamalot.py init
```

The program creates a local `spamalot.sqlite3`, a private `profile.json` template, and a `receipts/` directory. Enter **your own** U.S. recipient name and legitimate mailing address in `profile.json`. Never commit it.

Every operation requires the full interactive recipient/responsibility acknowledgment. Read the warning and verify that you satisfy it before entering the phrase.

## First checks

```sh
python3 spamalot.py sources
python3 spamalot.py subscribe --all --dry-run
python3 -m unittest discover -v
```

Dry-run shows the eligible selection; it does not prove that a publisher's form works.

## Requesting mail

```sh
python3 spamalot.py subscribe --source highcountrygardens
python3 spamalot.py subscribe --file selected-sources.txt
python3 spamalot.py subscribe --all --category Catalog
```

The normal mode opens the official request page and asks you to report whether **you actually submitted** a physical-mail request. Disable unwanted email/SMS marketing options.

## Migrating earlier releases

Retain a backup of your database and private profile. Copy updated code and registry files, then run:

```sh
python3 spamalot.py sync-defaults
```

If your previous database is `postal_mail.sqlite3`, use `--db postal_mail.sqlite3` or back it up and rename it. Existing source metadata is preserved unless `sync-defaults --update` is used. A sync does not restore disabled sources.

See [[Commands]], [[Receipts-and-Data]], and [[Safety-and-Licensing]].