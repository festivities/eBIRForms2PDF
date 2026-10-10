import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ebirforms2pdf.finder import FormEntry
from ebirforms2pdf.render import output_pdf_name


def _display_available():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


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
    def test_export_flow(self):
        from ebirforms2pdf import gui

        app = gui.EbirApp(auto_load=False)
        try:
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            out = Path(tmp.name)
            app.named_dir = out
            app.out_var.set(str(out))
            app.load_entries(
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
            self.assertEqual(app.listbox.size(), 2)
            app.select_all()

            def _fake(entry, draft, named, target, paper="a4"):
                Path(target).write_bytes(b"%PDF-1.4 fake")
                return SimpleNamespace(paper=paper, pages=2, scale=0.85)

            with mock.patch.object(gui, "export_pdf") as fake:
                fake.side_effect = _fake
                app.start_export()
                deadline = time.time() + 30
                while app.busy and time.time() < deadline:
                    app.update()
                    time.sleep(0.05)
                app.update()
            self.assertFalse(app.busy)
            self.assertEqual(fake.call_count, 2)
            self.assertTrue((out / "111111111-1701Qv2018-2026Q3.pdf").is_file())
            self.assertTrue((out / "111111111-0605-2026.pdf").is_file())
            self.assertIn("Done: 2/2 exported.", app.status_var.get())
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
