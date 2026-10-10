import json
import os
import tempfile
import types
import unittest
from pathlib import Path

from ebirforms2pdf.extract import extract_templates
from ebirforms2pdf.finder import FormEntry
from ebirforms2pdf.render import RenderError, _build_html, _launch, export_pdf, output_pdf_name

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


def _injected(init, name):
    marker = f"window.{name} = "
    return json.JSONDecoder().raw_decode(init, init.index(marker) + len(marker))[0]


class TestOutputName(unittest.TestCase):
    def test_a4_name_ignores_case(self):
        self.assertEqual(
            output_pdf_name("000000000-1701Qv2018-2099Q3.xml", "A4"),
            "000000000-1701Qv2018-2099Q3.pdf",
        )

    def test_legal_suffix_ignores_case(self):
        self.assertEqual(
            output_pdf_name("000000000-1701Qv2018-2099Q3.XML", "Legal"),
            "000000000-1701Qv2018-2099Q3-legal.pdf",
        )


class _FailingChromium:
    def launch(self, channel=None):
        raise RuntimeError(f"{channel or 'bundled'} broke\nsecond line")


class TestLaunch(unittest.TestCase):
    def test_error_names_each_channel_first_line_only(self):
        context = types.SimpleNamespace(chromium=_FailingChromium())
        with self.assertRaises(RenderError) as caught:
            _launch(context)
        message = str(caught.exception)
        self.assertIn("msedge: msedge broke", message)
        self.assertIn("chrome: chrome broke", message)
        self.assertNotIn("second line", message)


class TestBuildHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls.tmp.name) / "BIR-Form1701Qv2018.hta"
        cls.template.write_bytes(b"<html><body>synthetic</body></html>")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_draft_values_stay_out_of_html(self):
        values = {"ebirOnlineSecret": "SYNTH-SECRET-7f3a", "frm1701q:txtTin": "SYNTH-VALUE-9c1e"}
        html, init = _build_html(self.template, values, "")
        self.assertNotIn(b"SYNTH-SECRET-7f3a", html)
        self.assertNotIn(b"SYNTH-VALUE-9c1e", html)
        self.assertIn("SYNTH-VALUE-9c1e", init)
        self.assertNotIn("SYNTH-SECRET-7f3a", init)

    def test_placeholder_text_in_value_is_preserved(self):
        values = {"frm1701q:txtNote": "__RDO_XML__ __VALUES__"}
        html, init = _build_html(self.template, values, "<option>x</option>")
        self.assertEqual(_injected(init, "__ebir2pdf_values"), values)
        self.assertEqual(_injected(init, "__ebir2pdf_rdo"), "<option>x</option>")
        self.assertNotIn(b"__RDO_XML__", html)


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
        self.assertEqual(result.pages, 2)
        self.assertEqual(result.warnings, [])
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
        self.assertEqual(result.pages, 2)
        self.assertEqual(result.warnings, [])
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

    def test_page_mismatch_warns_and_keeps_scale(self):
        draft = Path(self.tmp.name) / "000000000-1701Qv2018-2099Q4.xml"
        draft.write_text(SYNTHETIC.replace("txtMaxPage=2", "txtMaxPage=1"), encoding="utf-8")
        out = Path(self.tmp.name) / "out-mismatch.pdf"
        result = export_pdf(self._entry(), draft, self.named, out)
        self.assertEqual(result.pages, 2)
        self.assertEqual(result.expected_pages, 1)
        self.assertGreater(result.scale, 0.6)
        self.assertTrue(any("draft expects 1" in warning for warning in result.warnings))

    def test_unknown_frm_control_warns_without_values(self):
        draft = Path(self.tmp.name) / "000000000-1701Qv2018-2099Q5.xml"
        draft.write_text(
            SYNTHETIC
            + "<div>frm1701q:txtNoSuchControl=SYNTH-VALUE-41 frm1701q:txtNoSuchControl=</div>"
            + "<div>txtEmail=SYNTH-EMAIL txtEmail=</div>",
            encoding="utf-8",
        )
        out = Path(self.tmp.name) / "out-unfilled.pdf"
        result = export_pdf(self._entry(), draft, self.named, out)
        self.assertEqual(result.unfilled_count, 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("frm1701q:txtNoSuchControl", result.warnings[0])
        self.assertNotIn("SYNTH-VALUE-41", result.warnings[0])


if __name__ == "__main__":
    unittest.main()
