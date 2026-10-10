import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ebirforms2pdf.extract import ExtractError
from ebirforms2pdf.finder import FormEntry
from ebirforms2pdf.render import output_pdf_name

DRAFT = (
    "<?xml version='1.0'?>"
    "<div>frm0605:txtYear=2026 frm0605:txtYear=</div>"
    "<div>txtFinalFlag=false txtFinalFlag=</div>"
)


def _display_available():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


def _pump(app, timeout=30):
    deadline = time.time() + timeout
    while app.busy and time.time() < deadline:
        app.update()
        time.sleep(0.02)
    app.update()


def _install(base):
    root = Path(base) / "eBIRForms"
    (root / "savefile").mkdir(parents=True)
    (root / "BIRForms.exe").write_bytes(b"")
    (root / "savefile" / "123456789-0605-2026.xml").write_text(DRAFT, encoding="utf-8")
    return root


class TestOutputName(unittest.TestCase):
    def test_a4(self):
        self.assertEqual(
            output_pdf_name("123456789-1701Qv2018-2026Q3.xml", "a4"),
            "123456789-1701Qv2018-2026Q3.pdf",
        )

    def test_legal(self):
        self.assertEqual(
            output_pdf_name("123456789-1701Qv2018-2026Q3.xml", "legal"),
            "123456789-1701Qv2018-2026Q3-legal.pdf",
        )


@unittest.skipUnless(_display_available(), "no display")
class TestGui(unittest.TestCase):
    def setUp(self):
        from ebirforms2pdf import gui

        self.gui = gui
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = gui.EbirApp(auto_load=False)
        self.addCleanup(self._destroy)
        for name in ("showwarning", "showerror", "askyesno"):
            patcher = mock.patch.object(gui.messagebox, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def _destroy(self):
        try:
            self.app.destroy()
        except tk.TclError:
            pass

    def _entries(self):
        return [
            FormEntry(
                Path("a.xml"), "1701Qv2018", "2026Q3", False, 10, 0.0,
                "111111111-1701Qv2018-2026Q3.xml",
            ),
            FormEntry(
                Path("b.xml"), "1701Qv2018", "2026Q3", True, 10, 0.0,
                "111111111-1701Qv2018-2026Q3#user@example.com#.xml",
            ),
        ]

    def test_encrypted_hidden_by_default(self):
        self.app.load_entries(self._entries())
        self.assertFalse(self.app.show_encrypted_var.get())
        self.assertEqual(self.app.listbox.size(), 1)
        self.assertIn("encrypted hidden", self.app.status_var.get())
        self.app.show_encrypted_var.set(True)
        self.app._refresh_list()
        self.assertEqual(self.app.listbox.size(), 2)

    def test_export_flow(self):
        out = Path(self.tmp.name)
        self.app.named_dir = out
        self.app.out_var.set(str(out))
        self.app.load_entries(
            [
                FormEntry(
                    Path("a.xml"), "1701Qv2018", "2026Q3", False, 10, 0.0,
                    "111111111-1701Qv2018-2026Q3.xml",
                ),
                FormEntry(
                    Path("b.xml"), "0605", "2026", False, 10, 0.0,
                    "111111111-0605-2026.xml",
                ),
            ]
        )
        self.assertEqual(self.app.listbox.size(), 2)
        self.app.select_all()

        def _fake(entry, draft, named, target, paper="a4"):
            Path(target).write_bytes(b"%PDF-1.4 fake")
            return SimpleNamespace(paper=paper, pages=2, scale=0.85, warnings=["synthetic note"])

        with mock.patch("ebirforms2pdf.render.export_pdf") as fake:
            fake.side_effect = _fake
            self.app.start_export()
            _pump(self.app)
        self.assertFalse(self.app.busy)
        self.assertEqual(fake.call_count, 2)
        self.assertTrue((out / "111111111-1701Qv2018-2026Q3.pdf").is_file())
        self.assertTrue((out / "111111111-0605-2026.pdf").is_file())
        self.assertIn("Done: 2/2 exported.", self.app.status_var.get())
        self.assertIn("  WARNING: synthetic note", self.app.log.get("1.0", tk.END))

    def test_rescan_uses_typed_folder(self):
        root = _install(self.tmp.name)
        named = Path(self.tmp.name) / "named"
        with mock.patch.object(self.gui, "extract_templates", return_value=named) as extract:
            self.app.root_var.set(f'"{root}"')
            self.app.refresh_forms()
            _pump(self.app)
        extract.assert_called_once_with(root / "BIRForms.exe")
        self.assertEqual(self.app.listbox.size(), 1)
        self.assertEqual(self.app.named_dir, named)
        self.showwarning.assert_not_called()

    def test_load_runs_off_ui_thread_and_disables_controls(self):
        root = _install(self.tmp.name)
        release = threading.Event()
        threads = []

        def slow_extract(exe, *args):
            threads.append(threading.current_thread())
            release.wait(10)
            return Path(self.tmp.name)

        with mock.patch.object(self.gui, "extract_templates", side_effect=slow_extract):
            self.app.root_var.set(str(root))
            self.app.refresh_forms()
            self.assertTrue(self.app.busy)
            self.assertTrue(self.app.rescan_btn.instate(["disabled"]))
            self.assertTrue(self.app.change_btn.instate(["disabled"]))
            self.assertTrue(self.app.export_btn.instate(["disabled"]))
            self.assertEqual(self.app.status_var.get(), "Loading templates...")
            release.set()
            _pump(self.app)
        self.assertNotEqual(threads[0], threading.main_thread())
        self.assertFalse(self.app.busy)
        self.assertFalse(self.app.rescan_btn.instate(["disabled"]))
        self.assertEqual(self.app.listbox.size(), 1)

    def test_invalid_folder_clears_forms_and_warns(self):
        root = _install(self.tmp.name)
        with mock.patch.object(self.gui, "extract_templates", return_value=Path(self.tmp.name)):
            self.app.root_var.set(str(root))
            self.app.refresh_forms()
            _pump(self.app)
        self.assertEqual(self.app.listbox.size(), 1)
        self.app.root_var.set(str(Path(self.tmp.name) / "missing"))
        self.app.refresh_forms()
        self.showwarning.assert_called_once()
        self.assertEqual(self.app.listbox.size(), 0)
        self.assertIsNone(self.app.named_dir)

    def test_extract_failure_clears_stale_forms(self):
        root = _install(self.tmp.name)
        side_effect = [Path(self.tmp.name), ExtractError("boom")]
        with mock.patch.object(self.gui, "extract_templates", side_effect=side_effect):
            self.app.root_var.set(str(root))
            self.app.refresh_forms()
            _pump(self.app)
            self.assertEqual(self.app.listbox.size(), 1)
            self.app.refresh_forms()
            _pump(self.app)
        self.showerror.assert_called_once()
        self.assertIn("boom", self.showerror.call_args.args[1])
        self.assertEqual(self.app.entries, [])
        self.assertEqual(self.app.listbox.size(), 0)
        self.assertIsNone(self.app.named_dir)
        self.assertFalse(self.app.busy)

    def test_close_asks_only_while_busy(self):
        self.app._set_busy(True)
        self.askyesno.return_value = False
        self.app._on_close()
        self.askyesno.assert_called_once()
        self.assertEqual(self.app.winfo_exists(), 1)
        self.app._set_busy(False)
        self.app._on_close()
        self.assertEqual(self.askyesno.call_count, 1)
        self.assertIsNone(self.app._poll_id)

    def test_poll_reschedules_after_handler_error(self):
        self.app.after_cancel(self.app._poll_id)
        self.app.queue.put(("row", "boom"))
        with mock.patch.object(self.app, "_log", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.app._poll()
        self.assertIsNotNone(self.app._poll_id)


if __name__ == "__main__":
    unittest.main()
