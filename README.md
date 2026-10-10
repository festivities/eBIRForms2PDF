# eBIRForms2PDF

Export forms saved by the Philippine BIR's **eBIRForms Offline Package** as print-ready
PDFs — **A4** by default, or Philippine **legal** (8.5"×13") with `--paper legal` —
no clipping, no manual scale fiddling, entirely offline.

## Why

The eBIRForms offline app lays its forms out for 8.5"×13" Philippine legal paper. When you
use the app's built-in print-to-PDF with A4 selected (A4 is BIR's official document size),
content near the right edge and bottom of each page gets **clipped**. This tool renders the
form's own embedded template, fills it with your saved draft values, and scales the result
to fit A4 exactly.

## Install

Requires Python 3.10+ on Windows and an existing eBIRForms offline installation
(templates are read from your install; nothing is modified there).

```
python -m venv .venv
.venv\Scripts\pip install .
```

A Chromium-based browser is needed for rendering: **Microsoft Edge** (preinstalled on
Windows 10/11) or Google Chrome. If neither is available, run
`.venv\Scripts\python -m playwright install chromium` once.

## Usage

Interactive (type numbers like `1,3-5`, `all`, or `a`; an invalid selection is shown and you
get up to three tries):

```
.venv\Scripts\ebirforms2pdf
```

Non-interactive:

```
ebirforms2pdf --list
ebirforms2pdf --all --out "%USERPROFILE%\Documents\BIR"
ebirforms2pdf --all --paper legal --out "%USERPROFILE%\Documents\BIR"
ebirforms2pdf --all --root D:\eBIRForms --out "%USERPROFILE%\Documents\BIR"
ebirforms2pdf "C:\Apps\eBIRForms\savefile\123456789000-1701Qv2018-2026Q3.xml" --out "%USERPROFILE%\Documents\BIR"
```

Flags: `--list` (print saved drafts and exit), `--all` (export every draft; ignored when draft
paths are given), `--out DIR` (output folder, created if missing), `--root PATH` (eBIRForms
install folder, if autodetection fails), `--cache DIR` (template cache location), `--paper {a4,legal}`
(output paper size, default `a4`; legal files get a `-legal` filename suffix), `--version`.

Draft paths that are missing or are not eBIRForms drafts are reported as `ERROR` and skipped.
If one run would write two outputs with the same name (the same draft in `savefile\` and
`temp\`), the later one gets a `-2` suffix instead of overwriting the first. Existing files in
the output folder from earlier runs are overwritten.

Exit codes:

| Code | Meaning |
|------|---------|
| `0` | Every selected draft was exported (skipped encrypted copies do not count as failures). |
| `1` | Nothing was exported, or setup failed (no install found, templates could not be read, output folder could not be created, selection cancelled). |
| `2` | Partial failure: some drafts exported and some failed. |
| `130` | Cancelled with Ctrl+C. |

Encrypted final copies (`IAF_*_Copy` / `IAF_*_Archive`) are listed but cannot be exported;
selecting one, or passing one as a path, reports `SKIP`.

Desktop app (multi-select list instead of typed numbers, progress bar, result log):

```
.venv\Scripts\ebirforms2pdf-gui
```

Self-contained Windows executables — no Python needed on the target machine, but
Microsoft Edge or Google Chrome must be installed (rendering engine). Build them from the
repository folder after the Install steps above:

```
build_exe.bat
```

It produces `dist\eBIRForms2PDF.exe` (desktop app) and `dist\ebirforms2pdf-cli.exe` (the same
command line, same exit codes). Windows SmartScreen may flag the fresh binaries on first run
("More info" → "Run anyway").

## Designed paper sizes

BIR's templates target different papers, which is exactly why the app's print-to-PDF clips on
A4: most forms are laid out for 8.5"×13" Philippine legal paper (one for 8.5"×14"), a handful
target A4, and 45 of 84 declare no paper size at all — in the original app, IE/printer defaults
decided. eBIRForms2PDF measures each form's actual print layout and scales it to fit A4
exactly: A4-native forms come out at ~1:1, legal-sized ones at ~0.83.

The full per-form survey (v7.9.6.2 templates) is in [docs/paper-sizes.md](docs/paper-sizes.md).
Notable: 2200Pv2020 is 8.5"×14"; 2550Qv2024 is clean A4; the old-generation
1700/1701/1702EX/MX/RT declare A4 while being laid out for legal — the clipping bug in its
purest form.

Use `--paper legal` (Philippine legal 8.5x13in, the GUI's "Legal" option) instead of A4. Forms
designed for a taller page are scaled down to fit it; 2200Pv2020 (8.5x14in) is one of these.

## Tested forms

Only **1701Q (1701Qv2018)** has been verified end-to-end with a real filled draft: correct
page count, correct page size, no clipping, and values checked against the official layout —
in both A4 and Philippine legal output. Every other template is supported by the same generic
fill-and-render path but has not been tested yet. If you try one, please report the result.

## Known limitations

- **2550DS**: drafts made with the old template version (BIR-Form2550DS-old) are saved under the
  same `-2550DS-` filename as current drafts, so they are rendered with the current 2550DS
  template.
- Landscape-oriented forms may render rotated content incorrectly (they rely on an IE-only CSS
  filter the renderer ignores).

## Privacy

All processing is local; nothing leaves your machine. Form contents are never logged.
Draft values are only written to a short-lived temporary HTML file next to the extracted
template (deleted immediately after each export) and into the PDF you chose as output.
No personal data is stored in this repository. The `.gitignore` excludes draft XML at the
repository root, `savefile/`, `temp/`, `profile/` and `IAF_*/` folders, and PDFs, so exports
written into a clone are not committed by accident.

## Troubleshooting

- **"eBIRForms installation not found (checked registry and default paths)"** — pass `--root`
  pointing at the folder that contains `BIRForms.exe` and a `savefile` subfolder.
- **"no Chromium-based browser found; install Microsoft Edge or Google Chrome, ..."** — install
  Edge or Chrome. Source installs can instead run
  `.venv\Scripts\python -m playwright install chromium` once.
- **"ERROR: template extraction failed: manifest resource 129 is missing; the app layout
  changed"** — your eBIRForms version stores templates differently; file an issue with the app
  version number. Other extraction failures start with "could not extract templates:".

## License

GPLv3 — see [LICENSE](LICENSE).
