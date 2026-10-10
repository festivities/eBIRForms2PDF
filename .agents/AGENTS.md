# eBIRForms2PDF — Agent Context

Public, open-source Python tool: finds offline filled BIR (Philippines Bureau of Internal Revenue)
forms saved by the official **eBIRForms Offline Package**, lets the user choose forms, and exports
each as a **perfectly-fitted A4 PDF** ready for printing. Rationale: the app lays forms out for
8.5"×13" legal paper, so its built-in Windows print-to-PDF clips content when A4 is selected; BIR's
official document size is A4.

## Hard rules (all agents)
- Python: ONLY `D:\Dev\projects\eBIRForms2PDF\.venv\Scripts\python.exe`. pip installs into the venv
  are pre-authorized. NEVER use or install into global Python.
- Workflow: the main agent plans and delegates to `general` subagents, verifies every finding
  against ground truth, and reviews all code. `AGENTS.md` is maintained ONLY by the main agent.
- Git: no commits/pushes unless the user explicitly asks. The repo is PUBLIC: never place personal
  data (TINs, names, emails, amounts), credentials, or BIR endpoint secrets in any repo file.
  Real draft files may contain `ebirOnlineSecret` (submission credential) — never log or print
  draft contents. Tests use synthetic data only.
- `C:\Apps\eBIRForms` is the user's REAL installation with REAL taxpayer data: strictly read-only;
  never execute its binaries.
- Scratch space: `C:\Users\fes\AppData\Local\Temp\opencode`.
- Code style: no comments in source; small docstrings only.

## Verified ground truth (2026-10-10; app v7.9.6.2 — main-agent-verified)
- Install root: registry `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\eBIRForms_is1`
  → `InstallLocation`. Fallbacks: `C:\Apps\eBIRForms`, `C:\eBIRForms`, `%USERPROFILE%\eBIRForms`.
- Most files under the install dir are Hidden+System — scanners must enumerate hidden entries.
- Filled drafts: `<root>\savefile\*.xml`. Plain UTF-8 pseudo-XML: `<?xml version='1.0'?>` header;
  body = `<div>CONTROLID=VALUE CONTROLID=</div>` lines (serializer duplicates the id as a
  terminator); trailer `All Rights Reserved BIR 2012.0`. Values are JS `escape()`d (unescape must
  handle `%uXXXX` and `%XX`; do NOT translate `+`). Radio/checkbox stored as `true`/`false`.
  This machine's draft has a single `txtAddress` div (address-split claim was wrong for it —
  parse generically: join duplicate ids if ever encountered).
- Draft filename grammar: `TIN(9-14)-<formCode[+version][C][V*]>-<period>.xml`; period = `YYYY`,
  `YYYYQ1..Q4`, or `MMYYYY`; amended returns get `V`/`V1`… suffix.
- Control IDs = `frm<code>:<htmlInputId>` (e.g. `frm1701q:txtYear`) and match the HTML input ids in
  the form template exactly. App-level keys also present: `txtFinalFlag`, `txtEmail`,
  `ebirOnline*` (incl. `ebirOnlineSecret` — sensitive), `txtMaxPage`, `txtSheets`,
  `driveSelectTPExport`.
- Encrypted final copies: `<root>\IAF_*_Copy\` / `IAF_*_Archive\`, filename `…#<email>#.xml`,
  high entropy (Encrypt.exe, AES) → list but never parse/render.
- Profiles: `<root>\profile\<TIN>.xml` (same pseudo-XML, short URL-encoded keys). `temp\` may hold
  staged imports; `success\`/`failed\` are import outcomes.
- Form templates live INSIDE `BIRForms.exe` (native 32-bit MFC, NOT .NET): 464 `RT_HTML` resources
  (~57.5 MB). Resource id 129 = UTF-16 (BOM) pipe-delimited manifest: `{GUID}|path|path|…`
  (~470 paths; 6 are `.gitkeep` placeholders with no resource). Resource id = 129 + manifest index
  (1-based); each payload = raw bytes XOR `0xFF`. Decoding yields the full web bundle:
  `BIRForms.hta`, `forms\BIR-Form<code>.hta` (84 forms), `css\` (`main.css`, `print.css`),
  `img\` (per-page barcode PNGs, jurat JPGs), `js\` (jQuery 1.x, `string-util.js`).
- Layout is legal-size: `.printBodyClass table{width:8.3in;height:12.5in}` at `css\print.css:63`
  is DEAD CSS (referenced by no template); the live legal geometry is per-form print-time JS
  clamps (`max-width:8.3in`), fixed `Print*Content` page divs (~1250–1300px ≈ 13in), and BIR
  `img\for_printing` reference scans (850×1300 = legal). Most forms declare no `@page` (IE or
  printer defaults decided) — this is the A4-clipping root cause. No native PDF export exists
  in the app (print pipeline only).
- Designed paper sizes per form (surveyed + verified 2026-10-10; full table in repo
  `docs/paper-sizes.md`): 27 legal 8.5×13 (high conf), 45 unknown/no declaration, 6 A4
  (2550Qv2024 `@page`; 1700v2018, 0619E/F, 1601EQ/FQ via alerts), 5 old-gen mixed
  (1700/1701/1702EX/MX/RT: `@page` A4 but legal geometry + legal reference scans), 1 legal
  8.5×14 (2200Pv2020). 20 v2018 forms carry dual alerts: Legal in `printme()` (main Print
  path) vs A4 in `printModal()` (secondary path). The renderer is measurement-driven, so it
  already adapts per form (A4-native ≈ 0.96, legal ≈ 0.83) — the survey required no code change.
- Reference decode of the full bundle (read-only): `C:\Users\fes\AppData\Local\Temp\opencode\ebir_extract\named\`.

## Architecture (v1)
`ebirforms2pdf/` package: `locator.py` (registry+fallbacks), `finder.py` (scan `savefile\`+`temp\`,
filename grammar + content signature, detect encrypted copies), `extract.py` (pefile → XOR-FF
decode → cache under `%LOCALAPPDATA%\eBIRForms2PDF` keyed by exe size+mtime; never write into the
install dir), `draft.py` (pseudo-XML → ordered values dict; JS-unescape; never log values),
`render.py` (copy `forms\BIR-Form<segment2>.hta` → injected `.html` (Chromium won't render `.hta`),
append script setting values by id + `checked` for true/false, print via Playwright Chromium —
prefer `channel="msedge"` then `"chrome"`, no browser download unless both missing — `page.pdf`
with explicit mm dimensions: **A4 210×297 default, Philippine legal 215.9×330.2 via `--paper
legal`** (`PAPER_SIZES_MM`; output gets a `-legal` filename suffix), `print_background=True`, computed scale-to-fit (per-page-height cap from `Page*Content`
divs, width fit, 0.90 fallback; auto-retry lower scale if PDF page count exceeds the draft's
`txtMaxPage`)), CLI (`__main__.py`: interactive picker `1,3-5`/`all`, `--list`,
`--all`, `--out`, `--root`, `--cache`, `--paper {a4,legal}`), desktop GUI (`gui.py`: tkinter
`EbirApp` — folder picker, multi-select list, paper radios, out-dir picker, threaded export
with progress/log; entry `ebirforms2pdf-gui`), frozen builds (`build_exe.bat` one-click:
PyInstaller `--onefile --collect-all playwright` → `dist\eBIRForms2PDF.exe` (windowed GUI)
+ `dist\ebirforms2pdf-cli.exe` via `launch_gui.py`/`launch_cli.py` shims — required because
direct-script builds break the package's relative imports; needs Edge/Chrome on target).
Deps: `pefile`, `playwright`, `pypdf` (all runtime).
Render specifics: injected fill script appended at end-of-document (templates define functions
after `</body>`); script un-hides `Page*Content` divs, hides `#loader`, pre-seeds RDO `<select>`s
from `xml/rdo.xml` via the form's own `loadRdo()`/`getRdo()` (dead ActiveX in Chromium),
converts `<select>`s to static labels for print, and neutralizes `<HTA:APPLICATION>` (IE gives it
no layout box; Chromium renders it as an inline wrapper that distorts layout) with
`display:contents`. Values are JSON-embedded with `<`/`>` escaped (`\u003c`) to prevent
`</script>` breakout. Fit/centering (learned the hard way — measure under print media, not
screen): `render.py` runs `emulate_media("print")`, freezes viewport-fluid ancestors of the root
(`#formPaper` box, which overflows its centered fluid `#wrapper`/`#container` by design), shifts
the root rect to x=0, fits its width, then re-measures at the computed print viewport
(fixed-point, ≤3 iterations); side margins are symmetric so the form centers when height-bound;
auto-calibration lowers scale if PDF pages exceed the draft's `txtMaxPage`. Verify geometry on
the OUTPUT PDF (text+images+vector extents vs page box) — screen-media DOM measurements lie.
Known non-bug: `txtLOB`/`txtTelno` live only in a
`display:none` `hiddenProfile` block — the official 1701Q print omits them by design.
Known risk: landscape forms use IE `DXImageTransform` rotation (ignored by Chromium) — parked as
limitation unless trivial.

## Status log
- 2026-10-10: Investigation delegated to @general and VERIFIED by main agent (all core claims
  reproduced; two citation nits corrected above). Implementation delegated to @general.
- 2026-10-10: v1 implemented by @general, then reviewed + verified end-to-end by main agent:
  `--list` finds the real draft; export produces 2/2 expected pages, A4 mediabox (595.9×842.9pt),
  all text blocks inside page bounds (no clipping), name/TIN/address present in PDF text,
  ruff clean, 29/29 tests green. Main-agent review applied 3 fixes: `<`/`>` escaping of
  JSON-embedded values (script-tag breakout hardening), per-page-height scale cap (A4-native
  forms no longer shrunk to 0.90), `pypdf` promoted to runtime dep (auto-calibration). Verified
  only 1701Qv2018 against a real draft; other 83 forms structurally supported but untested.
  No git commits made (user has not requested any).
- 2026-10-10: User reported off-center + right-edge clipping. Root causes (verified via live
  print-media DOM inspection + PDF painted-extent analysis): (1) measurement ran at screen media
  while the PDF uses print media; (2) Chromium renders `<HTA:APPLICATION>` as an inline element
  (IE does not); (3) `#formPaper` overflows its centered viewport-fluid ancestors, so its
  position slides with viewport width. Fixed by print-media measurement with frozen ancestors,
  root-rect shift to x=0, fixed-point viewport iteration, and symmetric margins. Re-verified:
  painted left/right gaps ≈ 10–13pt on both pages (centered, ~0.7mm asymmetry), no negative
  gaps, 2/2 pages, fills present, 29/29 tests, ruff clean.
- 2026-10-10: `--paper {a4,legal}` implemented + verified by main agent (legal: 2pp, symmetric
  gaps, mediabox ≈ 612×935pt, scale 0.856; suite now 30 tests incl. legal mediabox test, ruff
  clean). README gained a Tested-forms table (only 1701Qv2018 user-verified). License switched
  MIT → GPLv3 (canonical text from SPDX mirror — gnu.org was unreachable from this network;
  pyproject `GPL-3.0-or-later`, deps are GPL-compatible). Privacy sweep clean (no TIN/email in
  repo; test fixtures synthetic). Remote set to `git@github.com:festivities/eBIRForms2PDF.git`,
  first commit `e46267d` force-pushed to master at user request.
- 2026-10-10: Paper-size survey delegated to @general and VERIFIED by main agent (12/84 `@page`
  file list, 2200Pv2020 = 8.5×14, 2550Qv2024 = clean A4, dual Legal/A4 alert pattern in v2018
  forms, old-gen 1701 = A4 `@page` + 13in page divs, `printBodyClass` = dead CSS — ground truth
  above corrected). Published   `docs/paper-sizes.md` (84 rows, generated from the scan JSON in
  scratch) + a README "Designed paper sizes" section. No renderer change needed.
- 2026-10-10: Legal-size page-2 header bled onto page 1 (verified in user's screenshots +
  painted-extent analysis). Root cause: templates declare zero page-break rules; A4 only worked
  because page-1 content exactly fills the shorter sheet. Fix: fill script now sets
  `break-before: page` on every `Page*Content` div after the first (no-op when already at a
  sheet top, so A4 is unaffected). Verified: legal page-1 bottom strip went 4389→0 dark pixels,
  header back on page 2, 2pp, symmetric gaps; A4 unchanged. Regression tests assert "Page 2"
  placement on both papers (proven to FAIL with the fix disabled). 34/34, ruff clean.
  Uncommitted (user did not ask for a commit).
- 2026-10-10: tkinter GUI + frozen exes, all as main agent per user request. `gui.py` (threaded
  export, queue-polled log/progress), `launch_gui.py`/`launch_cli.py` PyInstaller shims,
  `build_exe.bat` one-click (both exes, `--collect-all playwright`; `*.spec` gitignored).
  Verified: 33/33 tests (incl. headful GUI export-flow with mocked renderer + legal-mediabox
  test), ruff clean; frozen CLI exe lists + exports real draft end-to-end (2pp A4);
  `eBIRForms2PDF.exe` confirmed live with main window "eBIRForms2PDF 0.1.0" via tasklist +
  MainWindowTitle check. README gained Desktop-app/exe section; `ebirforms2pdf-gui` entry added.
  Privacy: new files contain no personal data (synthetic fixtures only).
- 2026-10-10: GUI hides encrypted final copies by default behind an opt-in "Show encrypted"
  checkbox (status line reports hidden count); encrypted rows selected with the box on still
  SKIP cleanly. 34/34 tests, ruff clean; committed `d4d782a`, pushed.
