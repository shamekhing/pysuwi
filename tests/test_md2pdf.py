import tempfile
import unittest
from pathlib import Path

from commands.md2pdf import _safe_url_fetcher


class SafeUrlFetcherTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name).resolve()
        self.fetched = []

    def tearDown(self):
        self.temp_dir.cleanup()

    def default_fetcher(self, url):
        self.fetched.append(url)
        return {"url": url}

    def test_allows_local_file_inside_input_directory(self):
        resource = self.base_dir / "image.png"
        resource.touch()

        result = _safe_url_fetcher(
            resource.as_uri(), self.base_dir, self.default_fetcher
        )

        self.assertEqual(result, {"url": resource.as_uri()})
        self.assertEqual(self.fetched, [resource.as_uri()])

    def test_allows_embedded_data_resource(self):
        result = _safe_url_fetcher(
            "data:image/png;base64,AAAA", self.base_dir, self.default_fetcher
        )

        self.assertEqual(result["url"], "data:image/png;base64,AAAA")

    def test_rejects_network_resource(self):
        with self.assertRaises(ValueError):
            _safe_url_fetcher(
                "https://example.com/image.png", self.base_dir, self.default_fetcher
            )

        self.assertEqual(self.fetched, [])

    def test_rejects_local_file_outside_input_directory(self):
        outside = self.base_dir.parent / "outside.png"

        with self.assertRaises(ValueError):
            _safe_url_fetcher(
                outside.as_uri(), self.base_dir, self.default_fetcher
            )

        self.assertEqual(self.fetched, [])

    def test_rejects_symlink_to_file_outside_input_directory(self):
        outside = self.base_dir.parent / "outside.png"
        outside.touch()
        link = self.base_dir / "outside-link.png"
        link.symlink_to(outside)

        with self.assertRaises(ValueError):
            _safe_url_fetcher(link.as_uri(), self.base_dir, self.default_fetcher)

        self.assertEqual(self.fetched, [])


if __name__ == "__main__":
    unittest.main()
