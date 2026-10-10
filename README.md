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

Interactive:

```
.venv\Scripts\ebirforms2pdf
```

Non-interactive:

```
ebirforms2pdf --list
ebirforms2pdf --all --out C:\Users\me\Documents
ebirforms2pdf --all --paper legal --out C:\Users\me\Documents
ebirforms2pdf --all --root D:\eBIRForms --out .
ebirforms2pdf "C:\Apps\eBIRForms\savefile\123456789000-1701Qv2018-2026Q3.xml" --out .
```

Flags: `--list` (print saved drafts and exit), `--all` (export every draft), `--out DIR`,
`--root PATH` (eBIRForms install folder, if autodetection fails), `--cache DIR`
(template cache location), `--paper {a4,legal}` (output paper size, default `a4`;
legal files get a `-legal` filename suffix), `--version`.

Encrypted final copies (`IAF_*_Copy` / `IAF_*_Archive`) are listed but cannot be exported.

Desktop app (checkboxes instead of typed numbers, progress bar, result log):

```
.venv\Scripts\ebirforms2pdf-gui
```

Self-contained Windows executables — no Python needed on the target machine, but
Microsoft Edge or Google Chrome must be installed (rendering engine):

```
build_exe.bat
```

Double-click it (or run it from a terminal). It produces `dist\eBIRForms2PDF.exe`
(desktop app) and `dist\ebirforms2pdf-cli.exe` (the same command line). Windows
SmartScreen may flag the fresh binaries on first run ("More info" → "Run anyway").

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

Use `--paper legal` to export at the forms' original 8.5"×13" size instead of A4.

## Tested forms

Only **1701Q (1701Qv2018)** has been verified end-to-end with a real filled draft: correct
page count, correct page size, no clipping, and values checked against the official layout —
in both A4 and Philippine legal output. Every other template is supported by the same generic
fill-and-render path but has not been tested yet. If you try one, please report the result.

## Privacy

All processing is local; nothing leaves your machine. Form contents are never logged.
Draft values are only written to a short-lived temporary HTML file next to the extracted
template (deleted immediately after each export) and into the PDF you chose as output.
No personal data is stored in this repository.

## Troubleshooting

- **"eBIRForms installation not found"** — pass `--root` pointing at the folder that
  contains `BIRForms.exe` and a `savefile` subfolder.
- **"no Chromium-based browser found"** — install Edge or Chrome, or run
  `python -m playwright install chromium`.
- **"manifest resource 129 missing"** — your eBIRForms version stores templates
  differently; file an issue with the app version number.
- Landscape-oriented forms may render rotated content incorrectly (they rely on an
  IE-only CSS filter the renderer ignores).

## License

GPLv3 — see [LICENSE](LICENSE).
