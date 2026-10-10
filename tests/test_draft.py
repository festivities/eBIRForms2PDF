import tempfile
import unittest
from pathlib import Path

from ebirforms2pdf.draft import js_unescape, parse_draft

SYNTHETIC = (
    "<?xml version='1.0'?>"
    "<div>frm1701q:txtYear=2026 frm1701q:txtYear=</div>"
    "<div>frm1701q:txtName=%u00D1uca frm1701q:txtName=</div>"
    "<div>frm1701q:txtCode=%41%42 frm1701q:txtCode=</div>"
    "<div>frm1701q:chkFinal=false frm1701q:chkFinal=</div>"
    "<div>frm1701q:txtMaxPage=2 frm1701q:txtMaxPage=</div>"
    "<div>frm1701q:txtEmpty= frm1701q:txtEmpty=</div>"
    "<div>frm1701q:txtPlus=a+b frm1701q:txtPlus=</div>"
    "All Rights Reserved BIR 2012.0"
)


class TestJsUnescape(unittest.TestCase):
    def test_unicode_escape(self):
        self.assertEqual(js_unescape("%u00D1"), "\xd1")

    def test_byte_escape(self):
        self.assertEqual(js_unescape("%41%42"), "AB")

    def test_plus_is_literal(self):
        self.assertEqual(js_unescape("a+b"), "a+b")

    def test_plain_text_untouched(self):
        self.assertEqual(js_unescape("hello 100%25"), "hello 100%")

    def test_mixed(self):
        self.assertEqual(js_unescape("%u0041x%42"), "AxB")

    def test_single_pass_no_double_decode(self):
        self.assertEqual(js_unescape("%u002541"), "%41")

    def test_surrogate_pair_combined(self):
        self.assertEqual(js_unescape("%uD83D%uDE00"), "\U0001f600")

    def test_malformed_left_as_is(self):
        for text in ("%u12", "%ZZ", "100%"):
            with self.subTest(text=text):
                self.assertEqual(js_unescape(text), text)


class TestParseDraft(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "123456789001-1701Qv2018-2026Q3.xml"
        self.path.write_text(SYNTHETIC, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_values_parsed(self):
        meta, values = parse_draft(self.path)
        self.assertEqual(values["frm1701q:txtYear"], "2026")
        self.assertEqual(values["frm1701q:txtName"], "\xd1uca")
        self.assertEqual(values["frm1701q:txtCode"], "AB")
        self.assertEqual(values["frm1701q:txtPlus"], "a+b")
        self.assertEqual(values["frm1701q:txtEmpty"], "")

    def test_boolean_passthrough(self):
        _, values = parse_draft(self.path)
        self.assertEqual(values["frm1701q:chkFinal"], "false")

    def test_max_page_suffix_match(self):
        meta, _ = parse_draft(self.path)
        self.assertEqual(meta.max_page, 2)

    def test_trailer_ignored(self):
        _, values = parse_draft(self.path)
        self.assertNotIn("All Rights Reserved", values)


if __name__ == "__main__":
    unittest.main()
