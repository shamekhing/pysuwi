#!/usr/bin/env python3
"""pysuwi: plug-and-play command dispatcher.

Bundled plugins live in <checkout>/commands/. Your own plugins live in
~/.pysuwi/commands/ and override bundled ones with the same name.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import TextIO

VERSION = "1.1.0"
SRC_DIR = Path(__file__).resolve().parent
BUNDLED_DIR = SRC_DIR / "commands"
USER_DIR = Path.home() / ".pysuwi" / "commands"
BIN_LINK = Path.home() / ".local" / "bin" / "pysuwi"
COMPLETION_FILE = Path.home() / ".local/share/bash-completion/completions/pysuwi"
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
BUILTINS = {
    "doctor": "Check the installation and every plugin",
    "update": "Update pysuwi from its git checkout",
}

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_PLUGIN = 3
EXIT_INTERRUPT = 130


class PluginError(Exception):
    """A plugin file exists but cannot be used."""


def warn(msg: str) -> None:
    print(f"pysuwi: {msg}", file=sys.stderr)


def show_trace() -> None:
    if os.environ.get("PYSUWI_DEBUG"):
        traceback.print_exc()


def discover() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for folder in (BUNDLED_DIR, USER_DIR):  # user folder last, so it wins
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.py")):
            name = path.stem
            if NAME_RE.match(name) and name not in BUILTINS:
                found[name] = path
    return found


def summary(path: Path) -> str:
    """First docstring line, read without executing the plugin."""
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return "(unreadable)"
    lines = doc.strip().splitlines() if doc else []
    return lines[0] if lines else ""


def load_plugin(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"pysuwi_cmd_{path.stem.replace('-', '_')}", path
    )
    if spec is None or spec.loader is None:
        raise PluginError("cannot create an import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "run", None)):
        raise PluginError("no run(argv) entry point")
    return module


def print_usage(commands: dict[str, Path], stream: TextIO | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    rows = [(n, summary(p)) for n, p in commands.items()]
    width = max([len(n) for n, _ in rows] + [len(b) for b in BUILTINS] + [8])
    lines = [
        "usage: pysuwi <command> [options]",
        "       pysuwi --list-commands | --version | --help",
        "",
        "commands:",
    ]
    if not commands:
        lines.append(f"  (none yet; add plugins to {USER_DIR})")
    lines += [f"  {n:<{width}}  {d}" for n, d in rows]
    lines += ["", "built-in:"]
    lines += [f"  {n:<{width}}  {d}" for n, d in BUILTINS.items()]
    print("\n".join(lines), file=stream)


def update() -> int:
    if not (SRC_DIR / ".git").exists():
        warn("this install is not a git checkout; reinstall with install.sh")
        return EXIT_FAILURE
    try:
        result = subprocess.run(["git", "-C", str(SRC_DIR), "pull", "--ff-only"])
    except FileNotFoundError:
        warn("git is not installed")
        return EXIT_FAILURE
    if result.returncode != 0:
        warn("update failed (pinned to a tag, or local changes present?)")
        return EXIT_FAILURE
    return EXIT_OK


def doctor() -> int:
    ok = True

    def check(label: str, passed: bool, detail: str = "") -> None:
        nonlocal ok
        ok = ok and passed
        suffix = f": {detail}" if detail else ""
        print(f"[{'ok' if passed else 'FAIL'}] {label}{suffix}")

    check("python >= 3.9", sys.version_info >= (3, 9), sys.version.split()[0])
    check("source checkout", (SRC_DIR / "pysuwi.py").is_file(), str(SRC_DIR))
    on_path = shutil.which("pysuwi")
    check("launcher available",
          BIN_LINK.exists() or BIN_LINK.is_symlink() or on_path is not None,
          on_path or str(BIN_LINK))
    check("pysuwi on PATH", on_path is not None,
          on_path or "add ~/.local/bin to PATH and open a new login shell")
    if COMPLETION_FILE.is_file():
        check("bash completion", True, str(COMPLETION_FILE))
    else:
        print(f"[info] bash completion not installed (optional): {COMPLETION_FILE}")

    commands = discover()
    print(f"[info] {len(commands)} plugin(s) found")
    for name, path in commands.items():
        try:
            load_plugin(path)
            check(f"plugin '{name}'", True)
        except Exception as exc:  # noqa: BLE001 - report, never crash
            check(f"plugin '{name}'", False, f"{type(exc).__name__}: {exc}")
    return EXIT_OK if ok else EXIT_FAILURE


def _exit_code(exc: SystemExit) -> int:
    if exc.code is None:
        return EXIT_OK
    if isinstance(exc.code, int):
        return exc.code
    print(exc.code, file=sys.stderr)
    return EXIT_FAILURE


def main(argv: list[str]) -> int:
    commands = discover()
    if not argv:
        print_usage(commands, stream=sys.stderr)
        return EXIT_USAGE

    cmd, rest = argv[0], argv[1:]
    if cmd in ("-h", "--help", "help"):
        print_usage(commands)
        return EXIT_OK
    if cmd == "--version":
        print(f"pysuwi {VERSION}")
        return EXIT_OK
    if cmd == "--list-commands":
        print("\n".join(list(commands) + list(BUILTINS)))
        return EXIT_OK
    if cmd == "doctor":
        return doctor()
    if cmd == "update":
        return update()

    if cmd not in commands:
        warn(f"unknown command '{cmd}' (see 'pysuwi --help')")
        return EXIT_USAGE

    try:
        module = load_plugin(commands[cmd])
    except PluginError as exc:
        warn(f"plugin '{cmd}' is invalid: {exc}")
        return EXIT_PLUGIN
    except Exception as exc:  # noqa: BLE001
        warn(f"plugin '{cmd}' failed to load ({type(exc).__name__}: {exc})")
        show_trace()
        return EXIT_PLUGIN

    try:
        result = module.run(rest)
    except SystemExit as exc:  # argparse --help and usage errors land here
        return _exit_code(exc)
    except KeyboardInterrupt:
        warn(f"'{cmd}' interrupted")
        return EXIT_INTERRUPT
    except Exception as exc:  # noqa: BLE001
        warn(f"'{cmd}' failed: {type(exc).__name__}: {exc}")
        show_trace()
        return EXIT_FAILURE

    return result if isinstance(result, int) else EXIT_OK


def cli() -> int:
    return main(sys.argv[1:])


if __name__ == "__main__":
    try:
        sys.exit(cli())
    except KeyboardInterrupt:
        warn("interrupted")
        sys.exit(EXIT_INTERRUPT)
