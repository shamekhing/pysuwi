# pysuwi

A plug-and-play command suite. Each `.py` file in a commands folder becomes a
subcommand, with no central router to edit.

## Install

Quick install:

    curl -fsSL https://raw.githubusercontent.com/shamekhing/pysuwi/main/install.sh | bash

Safer, and recommended: download, read, then run.

    curl -fsSL https://raw.githubusercontent.com/shamekhing/pysuwi/main/install.sh -o install.sh
    less install.sh
    bash install.sh

Pin a release with `PYSUWI_REF=v1.1.0` before `bash`. Re-running the installer
does not replace an existing checkout; use `pysuwi update` to update it. To
reinstall from scratch, uninstall first.

## Use

    pysuwi --help
    pysuwi md2pdf -i notes.md -o notes.pdf
    pysuwi doctor
    pysuwi update

## Add a command

Create `~/.pysuwi/commands/<name>.py`:

    """One-line summary shown in --help."""

    def run(argv: list[str]) -> int:
        ...
        return 0

Your plugins in `~/.pysuwi/commands/` survive updates. A file there with the
same name as a bundled plugin overrides it.

Plugins are Python code and are trusted with your user permissions. The
`pysuwi doctor` command imports each plugin to check it, so module-level plugin
code runs during diagnostics too.

## Contributing a bundled command

Add `commands/<name>.py` to this repo and open a pull request.

## Uninstall

    bash install.sh --uninstall           # keeps your plugins
    bash install.sh --uninstall --purge   # removes everything

## Dependencies

md2pdf needs `python3-markdown` and `python3-weasyprint` (apt). Run
`pysuwi doctor` to see what is missing.
