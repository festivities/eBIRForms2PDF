import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ebirforms2pdf import locator


class TestFindInstallRoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "eBIRForms"
        (self.root / "savefile").mkdir(parents=True)
        (self.root / "BIRForms.exe").write_bytes(b"")

    def tearDown(self):
        self.tmp.cleanup()

    def test_override_accepted(self):
        self.assertEqual(locator.find_install_root(self.root), self.root)

    def test_override_without_savefile_rejected(self):
        bare = Path(self.tmp.name) / "bare"
        bare.mkdir()
        (bare / "BIRForms.exe").write_bytes(b"")
        self.assertIsNone(locator.find_install_root(bare))

    def test_override_missing_folder_rejected(self):
        self.assertIsNone(locator.find_install_root(Path(self.tmp.name) / "missing"))


class TestRegistryCandidates(unittest.TestCase):
    def _candidates(self, value):
        with mock.patch.object(locator.winreg, "OpenKey"), mock.patch.object(
            locator.winreg, "QueryValueEx", return_value=(value, 1)
        ):
            return list(locator._registry_candidates())

    def test_quotes_stripped(self):
        self.assertEqual(
            set(self._candidates('"C:\\Apps\\eBIRForms"')), {Path(r"C:\Apps\eBIRForms")}
        )

    def test_non_string_ignored(self):
        self.assertEqual(self._candidates(5), [])


if __name__ == "__main__":
    unittest.main()
