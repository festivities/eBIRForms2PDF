import contextlib
import io
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ebirforms2pdf import __main__ as cli
from ebirforms2pdf.finder import FormEntry
from ebirforms2pdf.render import export_many

DRAFT = (
    "<?xml version='1.0'?>"
    "<div>frm0605:txtYear=2026 frm0605:txtYear=</div>"
    "<div>txtFinalFlag=false txtFinalFlag=</div>"
)
SECOND_DRAFT = DRAFT.replace("frm0605", "frm1701q")
BLOB = bytes(range(256)) * 8
DRAFT_NAME = "123456789-0605-2026.xml"
SECOND_NAME = "123456789-1701Qv2018-2026Q3.xml"


def _result(warnings=()):
    return SimpleNamespace(paper="a4", pages=2, scale=0.912, warnings=list(warnings))


def _entry(path, encrypted=False):
    return FormEntry(Path(path), "0605", "2026", encrypted, 10, 0.0, Path(path).name)


class ParseSelectionTest(unittest.TestCase):
    def test_numbers_and_ranges(self):
        self.assertEqual(cli._parse_selection("1,3-4", 5), ([0, 2, 3], []))

    def test_all_keyword(self):
        self.assertEqual(cli._parse_selection(" ALL ", 3), ([0, 1, 2], []))
        self.assertEqual(cli._parse_selection("a", 2), ([0, 1], []))

    def test_reversed_range_is_sorted(self):
        self.assertEqual(cli._parse_selection("5-3", 5), ([2, 3, 4], []))

    def test_empty_tokens_ignored(self):
        self.assertEqual(cli._parse_selection("1,,2", 5), ([0, 1], []))

    def test_invalid_and_out_of_range_tokens_reported(self):
        chosen, invalid = cli._parse_selection("1,9,x,0,2-,1-3-5", 5)
        self.assertEqual(chosen, [0])
        self.assertEqual(invalid, ["9", "x", "0", "2-", "1-3-5"])

    def test_non_ascii_digit_reported_not_crashing(self):
        self.assertEqual(cli._parse_selection("²", 5), ([], ["²"]))

    def test_huge_range_rejected_quickly(self):
        started = time.perf_counter()
        chosen, invalid = cli._parse_selection("1-99999999999", 5)
        self.assertLess(time.perf_counter() - started, 1.0)
        self.assertEqual(chosen, [])
        self.assertEqual(invalid, ["1-99999999999"])


class ExportManyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch("ebirforms2pdf.render.export_pdf", return_value=_result())
        self.export = patcher.start()
        self.addCleanup(patcher.stop)
        self.out = Path(self.tmp.name)

    def _targets(self):
        return [call.args[3].name for call in self.export.call_args_list]

    def test_same_name_from_two_folders_gets_suffix(self):
        entries = [_entry(f"savefile/{DRAFT_NAME}"), _entry(f"temp/{DRAFT_NAME}")]
        results = list(export_many(entries, self.out, self.tmp.name, "a4"))
        self.assertEqual(
            self._targets(), ["123456789-0605-2026.pdf", "123456789-0605-2026-2.pdf"]
        )
        self.assertEqual([status for status, _ in results], ["OK", "OK"])

    def test_suffix_is_before_legal_marker(self):
        entries = [_entry(DRAFT_NAME), _entry(DRAFT_NAME)]
        list(export_many(entries, self.out, self.tmp.name, "legal"))
        self.assertEqual(
            self._targets(), ["123456789-0605-2026-legal.pdf", "123456789-0605-2026-legal-2.pdf"]
        )

    def test_suffix_skips_names_already_taken_in_run(self):
        entries = [_entry(DRAFT_NAME), _entry(DRAFT_NAME), _entry("123456789-0605-2026-2.xml")]
        list(export_many(entries, self.out, self.tmp.name, "a4"))
        self.assertEqual(
            self._targets(),
            ["123456789-0605-2026.pdf", "123456789-0605-2026-2.pdf", "123456789-0605-2026-2-2.pdf"],
        )

    def test_skip_error_and_ok_lines(self):
        self.export.side_effect = [
            RuntimeError(),
            _result(["fill script failed (ReferenceError); output may be incomplete"]),
        ]
        entries = [_entry("enc.xml", encrypted=True), _entry("bad.xml"), _entry("good.xml")]
        results = list(export_many(entries, self.out, self.tmp.name, "a4"))
        statuses = [status for status, _ in results]
        self.assertEqual(statuses, ["SKIP", "ERROR", "OK"])
        self.assertEqual(
            results[0][1], "SKIP enc.xml: not exportable (encrypted final copy)"
        )
        self.assertEqual(results[1][1], "ERROR bad.xml: RuntimeError: ")
        self.assertIn("(a4, 2 pages, scale 0.912)", results[2][1])
        self.assertIn("\n  WARNING: fill script failed (ReferenceError)", results[2][1])
        self.assertEqual(self.export.call_count, 2)

    def test_error_is_one_line_with_type_name(self):
        self.export.side_effect = ValueError("first\nsecond")
        results = list(export_many([_entry("bad.xml")], self.out, self.tmp.name, "a4"))
        self.assertEqual(results, [("ERROR", "ERROR bad.xml: ValueError: first second")])


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / "eBIRForms"
        (self.root / "savefile").mkdir(parents=True)
        (self.root / "BIRForms.exe").write_bytes(b"")
        self.draft = self._write(f"savefile/{DRAFT_NAME}", DRAFT)
        self.second = self._write(f"savefile/{SECOND_NAME}", SECOND_DRAFT)
        self.out = base / "out"
        extract = mock.patch.object(cli, "extract_templates", return_value=base / "named")
        self.extract = extract.start()
        self.addCleanup(extract.stop)
        export = mock.patch("ebirforms2pdf.render.export_pdf", return_value=_result())
        self.export = export.start()
        self.addCleanup(export.stop)

    def _write(self, rel, text=None, data=None):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            path.write_text(text, encoding="utf-8")
        else:
            path.write_bytes(data)
        return path

    def _run(self, *argv, input_side_effect=None):
        out = io.StringIO()
        base = ["--root", str(self.root), "--out", str(self.out)]
        with contextlib.redirect_stdout(out):
            if input_side_effect is None:
                code = cli.main([*base, *argv])
            else:
                with mock.patch("builtins.input", side_effect=input_side_effect):
                    code = cli.main([*base, *argv])
        return code, out.getvalue()

    def test_all_ok_exits_0(self):
        code, text = self._run(str(self.draft), str(self.second), "--paper", "a4")
        self.assertEqual(code, 0)
        self.assertEqual(text.count("OK "), 2)

    def test_partial_failure_exits_2(self):
        self.export.side_effect = [_result(), RuntimeError("boom")]
        code, text = self._run(str(self.draft), str(self.second))
        self.assertEqual(code, 2)
        self.assertIn("ERROR", text)
        self.assertIn("1 failed, 1 exported", text)

    def test_all_failed_exits_1(self):
        self.export.side_effect = RuntimeError("boom")
        code, _ = self._run(str(self.draft), str(self.second))
        self.assertEqual(code, 1)

    def test_encrypted_copy_is_skipped_not_failed(self):
        encrypted = self._write("IAF_RDO_Copy/123456789-0605-2026#user@example.com#.xml", data=BLOB)
        code, text = self._run(str(self.draft), str(encrypted))
        self.assertEqual(code, 0)
        self.assertIn("SKIP", text)

    def test_only_encrypted_copy_exits_1(self):
        encrypted = self._write("IAF_RDO_Copy/123456789-0605-2026#user@example.com#.xml", data=BLOB)
        code, _ = self._run(str(encrypted))
        self.assertEqual(code, 1)
        self.export.assert_not_called()

    def test_missing_path_reported_and_counted(self):
        code, text = self._run(str(self.draft), str(self.root / "missing.xml"))
        self.assertEqual(code, 2)
        self.assertIn("file not found", text)
        self.assertEqual(self.export.call_count, 1)

    def test_non_draft_path_rejected(self):
        plain = self._write("notes.xml", "<?xml version='1.0'?><p>not a draft</p>")
        code, text = self._run(str(plain))
        self.assertEqual(code, 1)
        self.assertIn("not an eBIRForms draft", text)

    def test_all_flag_ignored_with_paths(self):
        code, text = self._run(str(self.draft), "--all", "--paper", "a4")
        self.assertEqual(code, 0)
        self.assertIn("--all is ignored", text)

    def test_unwritable_out_folder_exits_1(self):
        blocker = self._write("blocker", "x")
        code, text = self._run(str(self.draft), "--out", str(blocker / "sub"), "--paper", "a4")
        self.assertEqual(code, 1)
        self.assertIn("cannot create output folder", text)
        self.export.assert_not_called()

    def test_eof_at_selection_cancels(self):
        code, text = self._run("--paper", "a4", input_side_effect=EOFError)
        self.assertEqual(code, 1)
        self.assertIn("cancelled", text)
        self.export.assert_not_called()

    def test_invalid_selection_reprompts(self):
        code, text = self._run("--paper", "a4", input_side_effect=["9", "1"])
        self.assertEqual(code, 0)
        self.assertIn("invalid selection: 9", text)
        self.assertEqual(self.export.call_count, 1)

    def test_three_invalid_selections_exit_1(self):
        code, _ = self._run("--paper", "a4", input_side_effect=["9", "x", "0"])
        self.assertEqual(code, 1)
        self.export.assert_not_called()

    def test_eof_at_paper_prompt_uses_default(self):
        code, _ = self._run(input_side_effect=["1", EOFError])
        self.assertEqual(code, 0)
        self.assertEqual(self.export.call_args.args[4], "a4")

    def test_ctrl_c_exits_130_without_traceback(self):
        code, text = self._run("--paper", "a4", input_side_effect=KeyboardInterrupt)
        self.assertEqual(code, 130)
        self.assertIn("cancelled", text)
        self.export.assert_not_called()


if __name__ == "__main__":
    unittest.main()
