import contextlib
import io
import tempfile
import unittest
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

import pysuwi


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.bundled_dir = self.root / "bundled"
        self.user_dir = self.root / "user"
        self.bundled_dir.mkdir()
        self.user_dir.mkdir()
        self.patchers = [
            patch.object(pysuwi, "BUNDLED_DIR", self.bundled_dir),
            patch.object(pysuwi, "USER_DIR", self.user_dir),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_plugin(self, directory, name, source):
        path = directory / f"{name}.py"
        path.write_text(source, encoding="utf-8")
        return path

    def test_discover_sorts_and_user_plugin_overrides_bundled(self):
        self.write_plugin(self.bundled_dir, "zebra", '"""Bundled."""\n')
        self.write_plugin(self.bundled_dir, "alpha", '"""Alpha."""\n')
        self.write_plugin(self.bundled_dir, "doctor", '"""Reserved."""\n')
        self.write_plugin(self.user_dir, "zebra", '"""User version."""\n')
        self.write_plugin(self.user_dir, "BadName", '"""Invalid name."""\n')

        found = pysuwi.discover()

        self.assertEqual(list(found), ["alpha", "zebra"])
        self.assertEqual(found["zebra"], self.user_dir / "zebra.py")

    def test_summary_reads_first_docstring_line_and_handles_invalid_file(self):
        valid = self.write_plugin(self.bundled_dir, "valid", '"""One line.\nMore."""\n')
        invalid = self.write_plugin(self.bundled_dir, "invalid", "def (")

        self.assertEqual(pysuwi.summary(valid), "One line.")
        self.assertEqual(pysuwi.summary(invalid), "(unreadable)")

    def test_load_plugin_requires_run_entry_point(self):
        invalid = self.write_plugin(self.bundled_dir, "invalid", "VALUE = 1\n")

        with self.assertRaises(pysuwi.PluginError):
            pysuwi.load_plugin(invalid)

    def test_main_help_version_and_command_list(self):
        self.write_plugin(
            self.bundled_dir,
            "hello",
            '"""Say hello."""\ndef run(argv): return 0\n',
        )

        for argv, expected in (
            (["--version"], f"pysuwi {pysuwi.VERSION}"),
            (["--list-commands"], "hello"),
        ):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = pysuwi.main(argv)
            self.assertEqual(result, pysuwi.EXIT_OK)
            self.assertIn(expected, output.getvalue())

        help_output = io.StringIO()
        with contextlib.redirect_stdout(help_output):
            self.assertEqual(pysuwi.main(["--help"]), pysuwi.EXIT_OK)
        self.assertIn("Say hello.", help_output.getvalue())

    def test_main_returns_usage_error_for_unknown_command(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            result = pysuwi.main(["missing"])

        self.assertEqual(result, pysuwi.EXIT_USAGE)
        self.assertIn("unknown command 'missing'", output.getvalue())

    def test_main_runs_plugin_and_returns_its_exit_code(self):
        self.write_plugin(
            self.bundled_dir,
            "hello",
            "def run(argv):\n    return len(argv) + 2\n",
        )

        self.assertEqual(pysuwi.main(["hello", "one", "two"]), 4)

    def test_package_version_matches_cli_version(self):
        self.assertEqual(version("pysuwi"), pysuwi.VERSION)


if __name__ == "__main__":
    unittest.main()
