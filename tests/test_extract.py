import tempfile
import unittest
from pathlib import Path

from ebirforms2pdf.extract import COMPLETE_MARKER, ExtractError, _safe_dest, extract_templates

REAL_EXE = Path(r"C:\Apps\eBIRForms\BIRForms.exe")


class TestSafeDest(unittest.TestCase):
    def test_rejects_escapes_and_accepts_relative(self):
        named = Path("named")
        for bad in (r"\Windows\x", "/abs/x", "C:x", r"..\x", r"forms\..\..\x"):
            with self.subTest(bad=bad):
                self.assertIsNone(_safe_dest(named, bad))
        self.assertEqual(_safe_dest(named, r"forms\a.hta"), named / "forms" / "a.hta")


class TestCacheAndErrors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name) / "cache"
        self.exe = Path(self.tmp.name) / "BIRForms.exe"
        self.exe.write_bytes(b"not a portable executable")
        stat = self.exe.stat()
        self.named = self.base / f"{stat.st_size}-{int(stat.st_mtime)}" / "named"
        self.named.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_bad_exe_becomes_extract_error(self):
        with self.assertRaises(ExtractError):
            extract_templates(self.exe, Path(self.tmp.name) / "fresh")

    def test_cache_without_marker_is_not_trusted(self):
        (self.named / "BIRForms.hta").write_text("partial", encoding="utf-8")
        with self.assertRaises(ExtractError):
            extract_templates(self.exe, self.base)

    def test_cache_with_marker_is_reused(self):
        (self.named / "BIRForms.hta").write_text("ok", encoding="utf-8")
        (self.named / COMPLETE_MARKER).touch()
        self.assertEqual(extract_templates(self.exe, self.base), self.named)


@unittest.skipUnless(REAL_EXE.is_file(), "real eBIRForms install not available")
class TestExtractTemplates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = tempfile.TemporaryDirectory()
        cls.named = extract_templates(REAL_EXE, Path(cls.cache.name))

    @classmethod
    def tearDownClass(cls):
        cls.cache.cleanup()

    def test_main_hta_extracted(self):
        self.assertTrue((self.named / "BIRForms.hta").is_file())

    def test_form_1701q_extracted(self):
        form = self.named / "forms" / "BIR-Form1701Qv2018.hta"
        self.assertTrue(form.is_file(), f"missing {form}")

    def test_form_count(self):
        forms = list((self.named / "forms").glob("*.hta"))
        self.assertEqual(len(forms), 84)

    def test_print_css_has_legal_width(self):
        css = (self.named / "css" / "print.css").read_text(encoding="utf-8", errors="replace")
        self.assertIn("8.3in", css)

    def test_cache_reuse(self):
        again = extract_templates(REAL_EXE, Path(self.cache.name))
        self.assertEqual(again, self.named)

    def test_missing_marker_reextracts(self):
        (self.named / COMPLETE_MARKER).unlink()
        form = self.named / "forms" / "BIR-Form1701Qv2018.hta"
        form.unlink()
        extract_templates(REAL_EXE, Path(self.cache.name))
        self.assertTrue(form.is_file())
        self.assertTrue((self.named / COMPLETE_MARKER).is_file())


if __name__ == "__main__":
    unittest.main()
