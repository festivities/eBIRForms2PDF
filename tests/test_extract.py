import tempfile
import unittest
from pathlib import Path

from ebirforms2pdf.extract import extract_templates

REAL_EXE = Path(r"C:\Apps\eBIRForms\BIRForms.exe")


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


if __name__ == "__main__":
    unittest.main()
