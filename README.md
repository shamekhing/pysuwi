# pysuwi

A plug-and-play command suite. Each `.py` file in a commands folder becomes a
subcommand, with no central router to edit.

## Install

Download the installer from a reviewed commit, inspect it, and install that
same commit from the `main` branch. Replace `REVIEWED_COMMIT_SHA` with its
full 40-character Git commit SHA:

    curl -fsSL https://raw.githubusercontent.com/shamekhing/pysuwi/REVIEWED_COMMIT_SHA/install.sh -o install.sh
    less install.sh
    PYSUWI_REF=REVIEWED_COMMIT_SHA bash install.sh

The installer requires a full commit SHA and checks out exactly that revision;
it does not run the installed application. Re-running the installer does not
replace an existing checkout; use `pysuwi update` to update it. To reinstall
from scratch, uninstall first.

## Use

    pysuwi --help
    pysuwi md2pdf -i notes.md -o notes.pdf
    pysuwi doctor
    pysuwi update

## Add a command

Create `~/.pysuwi/commands/<name>.py`. Command names must be lowercase and
start with a letter; they may contain lowercase letters, digits, and hyphens:

    """One-line summary shown in --help."""

    def run(argv: list[str]) -> int:
        ...
        return 0

Your plugins in `~/.pysuwi/commands/` survive updates. A file there with the
same name as a bundled plugin overrides it.

Plugins are Python code and are trusted with your user permissions. The
`pysuwi doctor` command imports each plugin to check it, so module-level plugin
code runs during diagnostics too.

When converting Markdown, `md2pdf` permits embedded `data:` resources and local
file resources under the input file's directory. Network URLs and local files
outside that directory are blocked to prevent unexpected resource access.

## Contributing a bundled command

Add `commands/<name>.py` to this repo and open a pull request.

## Uninstall

    bash install.sh --uninstall           # keeps your plugins
    bash install.sh --uninstall --purge   # removes everything

## Dependencies

On Debian/Ubuntu, `md2pdf` needs `python3-markdown` and `python3-weasyprint`:

    sudo apt install python3-markdown python3-weasyprint

On other platforms, install `markdown` and `weasyprint` in the same Python
environment that runs pysuwi (for example, in a virtual environment with
`python3 -m pip install markdown weasyprint`). Run `pysuwi doctor` to check the
installation.

## Development

Install the project and development tools in editable mode, then run tests and
lint:

    python3 -m pip install -e '.[dev]'
    python3 -m pytest
    python3 -m ruff check .

The CLI version is the single source of truth for package metadata and release
tags. The CI workflow checks that version tags use the matching `v` prefix.
