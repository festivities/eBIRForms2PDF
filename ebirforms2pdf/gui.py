"""Tkinter desktop UI for eBIRForms2PDF."""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .extract import extract_templates
from .finder import scan
from .locator import find_install_root, is_install_root
from .render import PAPER_SIZES_MM, export_many


class EbirApp(tk.Tk):
    """Pick drafts, paper size and output folder, then export PDFs."""

    def __init__(self, auto_load=True):
        super().__init__()
        self.title(f"eBIRForms2PDF {__version__}")
        self.minsize(660, 540)
        self.root_dir = find_install_root()
        self.entries = []
        self.visible = []
        self.named_dir = None
        self.queue = queue.Queue()
        self.busy = False
        self._poll_id = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        if auto_load:
            self.refresh_forms()
        self._poll_id = self.after(100, self._poll)

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(top, text="eBIRForms folder:").pack(side=tk.LEFT)
        self.root_var = tk.StringVar(value=str(self.root_dir) if self.root_dir else "")
        ttk.Entry(top, textvariable=self.root_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=6
        )
        self.change_btn = ttk.Button(top, text="Change...", command=self.change_root)
        self.change_btn.pack(side=tk.LEFT)
        self.rescan_btn = ttk.Button(top, text="Rescan", command=self.refresh_forms)
        self.rescan_btn.pack(side=tk.LEFT, padx=(6, 0))

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
        self.show_encrypted_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            side,
            text="Show encrypted",
            variable=self.show_encrypted_var,
            command=self._refresh_list,
        ).pack(fill=tk.X)

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

    def _set_busy(self, busy):
        self.busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for button in (self.change_btn, self.rescan_btn, self.export_btn):
            button.configure(state=state)

    def change_root(self):
        picked = filedialog.askdirectory(title="eBIRForms install folder")
        if picked:
            self.root_var.set(picked)
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
        if self.busy:
            return
        typed = self.root_var.get().strip().strip("\"'")
        folder = Path(typed) if typed else None
        if folder is None or not is_install_root(folder):
            self._clear_forms()
            messagebox.showwarning(
                "Not an install",
                "That folder has no BIRForms.exe + savefile. Type the eBIRForms folder"
                " above or use Change...",
            )
            return
        self._set_busy(True)
        self.status_var.set("Loading templates...")
        threading.Thread(target=self._load, args=(folder,), daemon=True).start()

    def _load(self, folder):
        result = ("load_failed", "Could not load forms: unknown error")
        try:
            result = ("loaded", extract_templates(folder / "BIRForms.exe"), scan(folder))
        except Exception as exc:
            result = ("load_failed", f"Could not load forms: {exc}")
        finally:
            self.queue.put(result)

    def _clear_forms(self):
        self.named_dir = None
        self.load_entries([])

    def load_entries(self, entries):
        self.entries = list(entries)
        self._refresh_list()

    def _refresh_list(self):
        show = self.show_encrypted_var.get()
        self.visible = [e for e in self.entries if show or not e.encrypted]
        self.listbox.delete(0, tk.END)
        for entry in self.visible:
            marker = "  [encrypted - not exportable]" if entry.encrypted else ""
            self.listbox.insert(
                tk.END, f"{entry.form_code}  {entry.period}  {entry.filename}{marker}"
            )
        hidden = len(self.entries) - len(self.visible)
        extra = f" ({hidden} encrypted hidden)" if hidden else ""
        self.status_var.set(f"{len(self.visible)} form(s) shown{extra}.")

    def start_export(self):
        if self.busy:
            return
        picked = [self.visible[i] for i in self.listbox.curselection()]
        if not picked:
            messagebox.showwarning("Nothing selected", "Select at least one form to export.")
            return
        out_dir = Path(self.out_var.get().strip().strip("\"'") or ".")
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Output folder", f"Cannot use that folder: {exc}")
            return
        self._set_busy(True)
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
        try:
            for status, line in export_many(picked, out_dir, named_dir, paper):
                if status == "OK":
                    done += 1
                self.queue.put(("row", line))
                self.queue.put(("step", None))
        finally:
            self.queue.put(("done", done, len(picked)))

    def _poll(self):
        self._poll_id = None
        try:
            while True:
                kind, *payload = self.queue.get_nowait()
                if kind == "row":
                    self._log(payload[0])
                elif kind == "step":
                    self.progress.step(1)
                elif kind == "done":
                    ok, total = payload
                    self._set_busy(False)
                    self.status_var.set(f"Done: {ok}/{total} exported.")
                elif kind == "loaded":
                    self.named_dir = payload[0]
                    self._set_busy(False)
                    self.load_entries(payload[1])
                elif kind == "load_failed":
                    self._set_busy(False)
                    self._clear_forms()
                    messagebox.showerror("Templates", payload[0])
        except queue.Empty:
            pass
        finally:
            self._poll_id = self.after(100, self._poll)

    def _on_close(self):
        if self.busy and not messagebox.askyesno(
            "Busy", "A load or export is still running. Close anyway?"
        ):
            return
        self.destroy()

    def destroy(self):
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        super().destroy()


def main():
    EbirApp().mainloop()


if __name__ == "__main__":
    main()
