import tempfile
import unittest
from pathlib import Path

from scripts.repair_sec_urls import repair_csv_file, repair_json_file, repair_url


BROKEN_URL = "https://www.sec.gov/Archives/edgar/data/1213900/0001213900-25-117587/example.htm"
FIXED_URL = "https://www.sec.gov/Archives/edgar/data/1213900/000121390025117587/0001213900-25-117587-index.htm"


class TestRepairSecUrls(unittest.TestCase):
    def test_repairs_only_sec_accession_directories(self) -> None:
        self.assertEqual(repair_url(BROKEN_URL), FIXED_URL)
        self.assertEqual(repair_url("https://example.com/0001213900-25-117587"), "https://example.com/0001213900-25-117587")

    def test_repairs_json_with_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "evidence.json"
            path.write_text('{"url": "' + BROKEN_URL + '"}', encoding="utf-8")
            self.assertEqual(repair_json_file(path, apply=True, backup_root=root / "backups"), 1)
            self.assertIn(FIXED_URL, path.read_text(encoding="utf-8"))
            self.assertTrue((root / "backups" / "evidence.json").exists())

    def test_repairs_csv_source_links_with_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "companies.csv"
            path.write_text('Company Name + Ticker,Source Links\nExample,"' + BROKEN_URL + '"\n', encoding="utf-8")
            self.assertEqual(repair_csv_file(path, apply=True, backup_root=root / "backups"), 1)
            self.assertIn(FIXED_URL, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
