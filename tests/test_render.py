import os
import tempfile
import unittest
from pathlib import Path

from ebirforms2pdf.extract import extract_templates
from ebirforms2pdf.finder import FormEntry
from ebirforms2pdf.render import export_pdf

REAL_EXE = Path(r"C:\Apps\eBIRForms\BIRForms.exe")
SYNTHETIC = (
    "<?xml version='1.0'?>"
    "<div>frm1701q:txtYear=2099 frm1701q:txtYear=</div>"
    "<div>txtFinalFlag=false txtFinalFlag=</div>"
    "<div>frm1701q:txtMaxPage=2 frm1701q:txtMaxPage=</div>"
)

FAST = os.environ.get("EBIR_FAST_TESTS") == "1"


def _browser_available():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as context:
            for channel in ("msedge", "chrome"):
                try:
                    browser = context.chromium.launch(channel=channel)
                    browser.close()
                    return True
                except Exception:
                    continue
            browser = context.chromium.launch()
            browser.close()
            return True
    except Exception:
        return False


@unittest.skipIf(FAST, "EBIR_FAST_TESTS=1")
@unittest.skipUnless(REAL_EXE.is_file(), "real eBIRForms install not available")
@unittest.skipUnless(_browser_available(), "no Chromium-based browser available")
class TestRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.named = extract_templates(REAL_EXE)
        cls.draft = Path(cls.tmp.name) / "000000000-1701Qv2018-2099Q3.xml"
        cls.draft.write_text(SYNTHETIC, encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _entry(self):
        return FormEntry(
            path=self.draft,
            form_code="1701Qv2018",
            period="2099Q3",
            encrypted=False,
            size=self.draft.stat().st_size,
            mtime=self.draft.stat().st_mtime,
            filename=self.draft.name,
        )

    def test_renders_a4_pdf(self):
        out = Path(self.tmp.name) / "out.pdf"
        result = export_pdf(self._entry(), self.draft, self.named, out)
        self.assertTrue(out.is_file())
        self.assertEqual(result.paper, "a4")
        self.assertGreater(result.pages, 0)
        from pypdf import PdfReader

        reader = PdfReader(str(out))
        box = reader.pages[0].mediabox
        self.assertAlmostEqual(float(box.width), 595.5, delta=2.0)
        self.assertAlmostEqual(float(box.height), 842.25, delta=2.0)
        first = reader.pages[0].extract_text() or ""
        self.assertNotIn("Page 2", first)

    def test_renders_legal_pdf(self):
        out = Path(self.tmp.name) / "out-legal.pdf"
        result = export_pdf(self._entry(), self.draft, self.named, out, paper="legal")
        self.assertTrue(out.is_file())
        self.assertEqual(result.paper, "legal")
        self.assertGreater(result.pages, 0)
        from pypdf import PdfReader

        reader = PdfReader(str(out))
        box = reader.pages[0].mediabox
        self.assertAlmostEqual(float(box.width), 612.28, delta=2.0)
        self.assertAlmostEqual(float(box.height), 935.43, delta=2.0)
        first = reader.pages[0].extract_text() or ""
        last = reader.pages[-1].extract_text() or ""
        self.assertNotIn("Page 2", first)
        self.assertIn("Page 2", last)

    def test_no_temp_html_left_behind(self):
        out = Path(self.tmp.name) / "out2.pdf"
        export_pdf(self._entry(), self.draft, self.named, out)
        leftovers = list((self.named / "forms").glob("_ebir2pdf_render_*.html"))
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
