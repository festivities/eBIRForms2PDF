import tempfile
import unittest
from pathlib import Path

from ebirforms2pdf.finder import parse_filename, scan, shannon_entropy

DRAFT_BODY = (
    "<?xml version='1.0'?>"
    "<div>frm1701q:txtYear=2026 frm1701q:txtYear=</div>"
    "<div>txtFinalFlag=false txtFinalFlag=</div>"
)


class TestParseFilename(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_filename("123456789-0605-2026.xml"), ("123456789", "0605", "2026"))

    def test_long_form_code(self):
        self.assertEqual(
            parse_filename("123456789001-1701Qv2018-2026Q3.xml"),
            ("123456789001", "1701Qv2018", "2026Q3"),
        )

    def test_monthly_period(self):
        self.assertEqual(
            parse_filename("123456789-0619E-122025.xml"), ("123456789", "0619E", "122025")
        )

    def test_amended_suffix(self):
        self.assertEqual(
            parse_filename("123456789-1702MXv2018C-2026V1.xml"),
            ("123456789", "1702MXv2018C", "2026V1"),
        )

    def test_encrypted_name_stops_at_hash(self):
        self.assertEqual(
            parse_filename("123456789-1701Qv2018-2026Q3#mail@example.com#.xml"),
            ("123456789", "1701Qv2018", "2026Q3"),
        )

    def test_invalid(self):
        self.assertIsNone(parse_filename("readme.txt"))
        self.assertIsNone(parse_filename("short-1-2.xml"))
        self.assertIsNone(parse_filename("12345678-0605-2026.xml"))


class TestScan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        savefile = self.root / "savefile"
        savefile.mkdir()
        (savefile / "123456789-0605-2026.xml").write_text(DRAFT_BODY, encoding="utf-8")
        (savefile / "123456789001-1701Qv2018-2026Q3.xml").write_text(
            DRAFT_BODY, encoding="utf-8"
        )
        (savefile / "readme.txt").write_text("notes", encoding="utf-8")
        (savefile / "123456789-0619E-122025.xml").write_text(
            "<?xml version='1.0'?><p>not a draft</p>", encoding="utf-8"
        )
        iaf = self.root / "IAF_RDO_Copy"
        iaf.mkdir()
        blob = bytes(range(256)) * 8
        (iaf / "123456789-1701Qv2018-2026Q3#user@example.com#.xml").write_bytes(blob)
        empty_dir = self.root / "IAF_RDO_Archive"
        empty_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_classifies_drafts(self):
        entries = scan(self.root)
        plain = [e for e in entries if not e.encrypted]
        self.assertEqual(len(plain), 2)
        codes = {e.form_code for e in plain}
        self.assertEqual(codes, {"0605", "1701Qv2018"})

    def test_scan_skips_non_drafts(self):
        entries = scan(self.root)
        names = [e.filename for e in entries if not e.encrypted]
        self.assertNotIn("readme.txt", names)
        self.assertNotIn("123456789-0619E-122025.xml", names)

    def test_scan_detects_encrypted(self):
        entries = scan(self.root)
        encrypted = [e for e in entries if e.encrypted]
        self.assertEqual(len(encrypted), 1)
        self.assertEqual(encrypted[0].form_code, "1701Qv2018")
        self.assertEqual(encrypted[0].period, "2026Q3")

    def test_high_entropy_blob_detected(self):
        blob = bytes((i * 37 + 11) % 256 for i in range(512))
        self.assertGreater(shannon_entropy(blob), 6.0)

    def test_plain_xml_low_entropy(self):
        self.assertLess(shannon_entropy(DRAFT_BODY.encode("utf-8")[:512]), 6.0)

    def test_empty_encrypted_dir_no_crash(self):
        entries = scan(self.root)
        self.assertTrue(all(e.path.exists() for e in entries))


if __name__ == "__main__":
    unittest.main()
