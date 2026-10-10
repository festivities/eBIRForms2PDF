"""Render a filled form template to a fitted A4 or Philippine legal PDF via Chromium."""

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import sync_playwright

from .draft import parse_draft

MARGIN_MM = 4
PAPER_SIZES_MM = {"a4": (210, 297), "legal": (215.9, 330.2)}
SCALE_CAP = 0.90
MAX_CALIBRATION_ATTEMPTS = 3
_VIEWPORT_MAX = 2400

_FILL_SCRIPT_TEMPLATE = r"""
window.alert = function () {};
window.confirm = function () { return false; };
window.sleeptime = function () {};
window.checkFinalCopyBtn = function () {};
for (var bi = 0; bi < document.body.children.length; bi++) {
  var bk = document.body.children[bi];
  if (bk.tagName && bk.tagName.indexOf(':') > -1
      && getComputedStyle(bk).display !== 'none') {
    bk.style.display = 'contents';
  }
}
window.__ebir2pdf_unfilled = [];
window.__ebir2pdf_err = null;
try {
  var loader = document.getElementById('loader');
  if (loader) { loader.style.display = 'none'; }
  document.querySelectorAll('[id^="Page"][id$="Content"]').forEach(function (el) {
    el.style.display = 'block';
  });
  var rdoXml = __RDO_XML__;
  if (rdoXml) {
    var responseRdo = document.getElementById('responseRdo');
    if (responseRdo && typeof loadRdo === 'function' && typeof rdoList !== 'undefined'
        && rdoList.length === 0) {
      responseRdo.innerHTML = rdoXml;
      try { loadRdo(); } catch (e) {}
      if (typeof getRdo === 'function') { try { getRdo(); } catch (e) {} }
    }
  }
  var values = __VALUES__;
  Object.keys(values).forEach(function (key) {
    if (!key) { return; }
    var val = String(values[key]);
    var el = document.getElementById(key);
    if (!el) {
      var byName = document.getElementsByName(key);
      if (byName.length > 0) { el = byName[0]; }
    }
    if (!el) { window.__ebir2pdf_unfilled.push(key); return; }
    var t = (el.type || '').toLowerCase();
    if (t === 'checkbox') { el.checked = (val === 'true'); return; }
    if (t === 'radio') { if (val === 'true') { el.checked = true; } return; }
    if (t === 'select-one' || t === 'select-multiple') {
      for (var i = 0; i < el.options.length; i++) {
        if (el.options[i].value === val || el.options[i].text === val) {
          el.selectedIndex = i;
          break;
        }
      }
      return;
    }
    el.value = val;
  });
  document.querySelectorAll('select').forEach(function (s) {
    if (s.options.length === 0) { return; }
    if ((s.id || '').indexOf('driveSelect') === 0) { return; }
    var opt = s.selectedIndex >= 0 ? s.options[s.selectedIndex] : null;
    var label = document.createElement('div');
    label.className = 'labels';
    label.textContent = opt ? (opt.text || '') : '';
    s.style.display = 'none';
    s.insertAdjacentElement('afterend', label);
  });
} catch (e) { window.__ebir2pdf_err = String(e); }
"""

_ROOT_WIDTH_SCRIPT = r"""
(function () {
  var root = document.getElementById('formPaper') || document.getElementById('wrapper')
    || document.getElementById('container') || document.body;
  return root.scrollWidth;
})()
"""

_MEASURE_SCRIPT = r"""
(function () {
  var root = document.getElementById('formPaper') || document.getElementById('wrapper')
    || document.getElementById('container') || document.body;
  var anc = root.parentElement;
  while (anc && anc !== document.body) {
    var ar = anc.getBoundingClientRect();
    if (ar.width > 0) {
      anc.style.boxSizing = 'border-box';
      anc.style.width = Math.ceil(ar.width) + 'px';
    }
    anc.style.marginLeft = '0px';
    anc.style.marginRight = '0px';
    anc = anc.parentElement;
  }
  var r0 = root.getBoundingClientRect();
  if (Math.abs(r0.left) >= 1) {
    root.style.marginLeft = (parseFloat(root.style.marginLeft) || 0) - r0.left + 'px';
  }
  var r1 = root.getBoundingClientRect();
  var pages = document.querySelectorAll('[id^="Page"][id$="Content"]');
  var maxPageH = 0;
  pages.forEach(function (el) { maxPageH = Math.max(maxPageH, el.scrollHeight); });
  if (!maxPageH) { maxPageH = root.scrollHeight; }
  return { w: Math.ceil(r1.right - r1.left) + 2, ph: maxPageH };
})()
"""


@dataclass
class RenderResult:
    pdf_path: Path
    pages: int
    expected_pages: int | None
    scale: float
    unfilled_count: int
    paper: str


class RenderError(Exception):
    pass


def _locate_template(named_dir, form_code):
    forms_dir = Path(named_dir) / "forms"
    if not forms_dir.is_dir():
        raise RenderError(f"forms directory not found: {forms_dir}")
    candidates = [form_code, re.sub(r"V\d*$", "", form_code)]
    for code in candidates:
        direct = forms_dir / f"BIR-Form{code}.hta"
        if direct.is_file():
            return direct
        wanted = f"bir-form{code.lower()}.hta"
        try:
            children = list(forms_dir.iterdir())
        except OSError as exc:
            raise RenderError(f"cannot list {forms_dir}: {exc}") from exc
        for child in children:
            if child.name.lower() == wanted:
                return child
    raise RenderError(
        f"no template for form code '{form_code}' (searched {forms_dir} for"
        f" 'BIR-Form{form_code}.hta' and amended-return variants)"
    )


def _read_rdo_xml(named_dir):
    path = Path(named_dir) / "xml" / "rdo.xml"
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


def _json_safe(obj):
    return json.dumps(obj).replace("<", "\\u003c").replace(">", "\\u003e")


def _build_html(template_path, values, rdo_xml):
    """Append the fill script at the very end: templates define functions after </body>."""
    raw = template_path.read_bytes()
    script = _FILL_SCRIPT_TEMPLATE.replace("__VALUES__", _json_safe(values))
    script = script.replace("__RDO_XML__", _json_safe(rdo_xml or ""))
    return raw + b"<script>" + script.encode("utf-8") + b"</script>"


def _launch(context):
    for channel in ("msedge", "chrome"):
        try:
            return context.chromium.launch(channel=channel)
        except Exception:
            continue
    try:
        return context.chromium.launch()
    except Exception as exc:
        raise RenderError(
            "no Chromium-based browser found; install Microsoft Edge or Google Chrome,"
            " or run: python -m playwright install chromium"
        ) from exc


def _count_pdf_pages(pdf_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    return len(PdfReader(str(pdf_path)).pages)


def output_pdf_name(filename, paper="a4"):
    """Output filename for a draft: '<stem>.pdf', or '<stem>-legal.pdf' for legal."""
    stem = filename[:-4] if filename.lower().endswith(".xml") else filename
    return f"{stem}.pdf" if paper == "a4" else f"{stem}-legal.pdf"


def export_pdf(entry, draft_path, template_named_dir, out_pdf_path, paper="a4"):
    """Fill entry's form template with the draft and write a fitted PDF."""
    try:
        paper_w_mm, paper_h_mm = PAPER_SIZES_MM[paper.lower()]
    except (KeyError, AttributeError) as exc:
        raise RenderError(
            f"unknown paper size '{paper}' (choose from {sorted(PAPER_SIZES_MM)})"
        ) from exc
    template = _locate_template(template_named_dir, entry.form_code)
    meta, values = parse_draft(draft_path)
    rdo_xml = _read_rdo_xml(template_named_dir)
    template_dir = template.parent
    temp_html = template_dir / f"_ebir2pdf_render_{os.getpid()}.html"
    out_pdf_path = Path(out_pdf_path)
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    for stale in template_dir.glob("_ebir2pdf_render_*.html"):
        try:
            stale.unlink()
        except OSError:
            pass
    temp_html.write_bytes(_build_html(template, values, rdo_xml))
    try:
        with sync_playwright() as context:
            browser = _launch(context)
            try:
                page = browser.new_page()
                page.on("dialog", lambda dialog: dialog.dismiss())
                page.goto(temp_html.as_uri())
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(300)
                root_w = page.evaluate(_ROOT_WIDTH_SCRIPT)
                if isinstance(root_w, (int, float)) and 0 < root_w <= _VIEWPORT_MAX:
                    page.set_viewport_size({"width": math.ceil(root_w), "height": 900})
                page.emulate_media(media="print")
                unfilled = page.evaluate(
                    "window.__ebir2pdf_unfilled ? window.__ebir2pdf_unfilled.length : -1"
                )
                if not isinstance(unfilled, int):
                    unfilled = -1
                scale = 0.0
                width_mm = 0.0
                for _ in range(3):
                    dims = page.evaluate(_MEASURE_SCRIPT) or {}
                    width_mm = (dims.get("w") or 0) * 25.4 / 96
                    page_h_mm = (dims.get("ph") or 0) * 25.4 / 96
                    if page_h_mm > 0:
                        cap = min((paper_h_mm - 2 * MARGIN_MM) / page_h_mm, 1.0)
                    else:
                        cap = SCALE_CAP
                    if width_mm > 0:
                        new_scale = min((paper_w_mm - 2 * MARGIN_MM) / width_mm, cap)
                    else:
                        new_scale = cap
                    new_scale = max(0.1, min(new_scale, 2.0))
                    converged = scale > 0 and abs(new_scale - scale) < 0.01
                    scale = new_scale
                    if converged:
                        break
                    viewport_w = (paper_w_mm - 2 * MARGIN_MM) / scale * 96 / 25.4
                    if viewport_w <= 0 or viewport_w > _VIEWPORT_MAX:
                        break
                    page.set_viewport_size({"width": math.ceil(viewport_w), "height": 900})
                pages = None
                attempts = 0
                while True:
                    leftover = max(0.0, (paper_w_mm - 2 * MARGIN_MM) - width_mm * scale)
                    side = MARGIN_MM + leftover / 2
                    page.pdf(
                        path=str(out_pdf_path),
                        width=f"{paper_w_mm}mm",
                        height=f"{paper_h_mm}mm",
                        print_background=True,
                        scale=scale,
                        margin={
                            "top": f"{MARGIN_MM}mm",
                            "bottom": f"{MARGIN_MM}mm",
                            "left": f"{side:.2f}mm",
                            "right": f"{side:.2f}mm",
                        },
                        prefer_css_page_size=False,
                    )
                    pages = _count_pdf_pages(out_pdf_path)
                    if (
                        pages is None
                        or meta.max_page is None
                        or pages <= meta.max_page
                        or attempts >= MAX_CALIBRATION_ATTEMPTS
                    ):
                        break
                    scale = max(0.1, scale * meta.max_page / pages)
                    attempts += 1
                return RenderResult(
                    pdf_path=out_pdf_path,
                    pages=pages if pages is not None else -1,
                    expected_pages=meta.max_page,
                    scale=scale,
                    unfilled_count=unfilled,
                    paper=paper,
                )
            finally:
                browser.close()
    finally:
        try:
            temp_html.unlink()
        except OSError:
            pass
