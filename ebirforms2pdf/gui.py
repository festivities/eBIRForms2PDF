"""Tkinter desktop UI for eBIRForms2PDF."""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .extract import ExtractError, extract_templates
from .finder import scan
from .locator import find_install_root, is_install_root
from .render import PAPER_SIZES_MM, export_pdf, output_pdf_name


class EbirApp(tk.Tk):
    """Pick drafts, paper size and output folder, then export PDFs."""

    def __init__(self, auto_load=True):
        super().__init__()
        self.title(f"eBIRForms2PDF {__version__}")
        self.minsize(660, 540)
        self.root_dir = find_install_root()
        self.entries = []
        self.named_dir = None
        self.queue = queue.Queue()
        self.busy = False
        self._build()
        if auto_load:
            self.refresh_forms()
        self.after(100, self._poll)

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(top, text="eBIRForms folder:").pack(side=tk.LEFT)
        self.root_var = tk.StringVar(value=str(self.root_dir) if self.root_dir else "")
        ttk.Entry(top, textvariable=self.root_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=6
        )
        ttk.Button(top, text="Change...", command=self.change_root).pack(side=tk.LEFT)
        ttk.Button(top, text="Rescan", command=self.refresh_forms).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        mid = ttk.Frame(self, padding=(8, 0))
        mid.pack(fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(mid, selectmode=tk.EXTENDED)
        scroll = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.LEFT, fill=tk.Y)
        side = ttk.Frame(mid)
        side.pack(side=tk.LEFT, fill=tk.Y, padx=(6, 0))
        ttk.Button(side, text="Select all", command=self.select_all).pack(fill=tk.X)
        ttk.Button(side, text="Clear", command=self.select_none).pack(fill=tk.X, pady=4)

        opts = ttk.Frame(self, padding=8)
        opts.pack(fill=tk.X)
        ttk.Label(opts, text="Paper:").pack(side=tk.LEFT)
        self.paper_var = tk.StringVar(value="a4")
        for code in PAPER_SIZES_MM:
            label = "A4" if code == "a4" else "Legal (8.5x13in)"
            ttk.Radiobutton(opts, text=label, value=code, variable=self.paper_var).pack(
                side=tk.LEFT, padx=4
            )
        ttk.Label(opts, text="Output folder:").pack(side=tk.LEFT, padx=(12, 0))
        self.out_var = tk.StringVar(value=str(Path.cwd()))
        ttk.Entry(opts, textvariable=self.out_var, width=30).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=6
        )
        ttk.Button(opts, text="Browse...", command=self.browse_out).pack(side=tk.LEFT)

        go = ttk.Frame(self, padding=(8, 0))
        go.pack(fill=tk.X)
        self.export_btn = ttk.Button(go, text="Export selected", command=self.start_export)
        self.export_btn.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(go, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, padding=(8, 2)).pack(fill=tk.X)

        self.log = tk.Text(self, height=9, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _log(self, text):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def change_root(self):
        picked = filedialog.askdirectory(title="eBIRForms install folder")
        if not picked:
            return
        if not is_install_root(picked):
            messagebox.showwarning(
                "Not an install", "That folder has no BIRForms.exe + savefile."
            )
            return
        self.root_dir = Path(picked)
        self.root_var.set(str(self.root_dir))
        self.refresh_forms()

    def browse_out(self):
        picked = filedialog.askdirectory(title="Output folder")
        if picked:
            self.out_var.set(picked)

    def select_all(self):
        self.listbox.selection_set(0, tk.END)

    def select_none(self):
        self.listbox.selection_clear(0, tk.END)

    def refresh_forms(self):
        if not self.root_dir:
            messagebox.showwarning(
                "Not found", "eBIRForms installation not found. Use Change... to point at it."
            )
            return
        self.status_var.set("Loading templates...")
        self.update_idletasks()
        try:
            self.named_dir = extract_templates(self.root_dir / "BIRForms.exe")
        except ExtractError as exc:
            messagebox.showerror("Templates", f"Template extraction failed: {exc}")
            return
        self.load_entries(scan(self.root_dir))
        self.status_var.set(f"{len(self.entries)} form(s) found.")

    def load_entries(self, entries):
        self.entries = list(entries)
        self.listbox.delete(0, tk.END)
        for entry in self.entries:
            marker = "  [encrypted - not exportable]" if entry.encrypted else ""
            self.listbox.insert(
                tk.END, f"{entry.form_code}  {entry.period}  {entry.filename}{marker}"
            )

    def start_export(self):
        if self.busy:
            return
        picked = [self.entries[i] for i in self.listbox.curselection()]
        if not picked:
            messagebox.showwarning("Nothing selected", "Select at least one form to export.")
            return
        out_dir = Path(self.out_var.get().strip().strip("\"'") or ".")
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Output folder", f"Cannot use that folder: {exc}")
            return
        self.busy = True
        self.export_btn.configure(state=tk.DISABLED)
        self.progress.configure(maximum=len(picked), value=0)
        self.status_var.set(f"Exporting {len(picked)} form(s)...")
        thread = threading.Thread(
            target=self._run_exports,
            args=(picked, out_dir, self.named_dir, self.paper_var.get()),
            daemon=True,
        )
        thread.start()

    def _run_exports(self, picked, out_dir, named_dir, paper):
        done = 0
        for entry in picked:
            if entry.encrypted:
                self.queue.put(
                    ("row", f"SKIP {entry.filename}: not exportable (encrypted final copy)")
                )
            else:
                try:
                    target = out_dir / output_pdf_name(entry.filename, paper)
                    result = export_pdf(entry, entry.path, named_dir, target, paper)
                    pages = result.pages if result.pages > 0 else "?"
                    self.queue.put(
                        (
                            "row",
                            f"OK {entry.filename} -> {target} "
                            f"({pages} pages, scale {result.scale:.3f})",
                        )
                    )
                    done += 1
                except Exception as exc:
                    self.queue.put(("row", f"ERROR {entry.filename}: {exc}"))
            self.queue.put(("step", None))
        self.queue.put(("done", done, len(picked)))

    def _poll(self):
        try:
            while True:
                kind, *payload = self.queue.get_nowait()
                if kind == "row":
                    self._log(payload[0])
                elif kind == "step":
                    self.progress.step(1)
                elif kind == "done":
                    ok, total = payload
                    self.busy = False
                    self.export_btn.configure(state=tk.NORMAL)
                    self.status_var.set(f"Done: {ok}/{total} exported.")
        except queue.Empty:
            pass
        self.after(100, self._poll)


def main():
    EbirApp().mainloop()


if __name__ == "__main__":
    main()
