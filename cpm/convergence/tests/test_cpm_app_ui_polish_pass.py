# -*- coding: utf-8 -*-
"""Pre-K CPM UI polish pass -- focused presentation checks.

Record: cpm/qualification/PRE_K_UI_POLISH_PASS.md.

The candidate must be exactly the item-8-qualified app (an explicit,
hash-validated reference path; never the candidate) plus the declared
presentation edits below: reconstruction applies those edits to the reference
and must reproduce the candidate byte for byte. The only free text is the
embedded icon (pinned by the SHA-256 of the decoded PNG) and the inserted
semantic-button helper (pinned by its parsed palette and checked at runtime).

Runtime gates build a real ProdWindow through the R15 harness environment
(real PySide/Qt 4.8 when importable, plus the behavioural Qt model) from both
the candidate and the reference, and compare them.

Usage:
  python test_cpm_app_ui_polish_pass.py --reference=<pinned item-8 app>
  internal: --child=window --qt=<real|model> --root=<dir> --reference=<...> --target=<candidate|reference>
"""
from __future__ import print_function

import ast
import base64
import gc
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
APP_PATH = os.environ.get("CPM_TEST_APP_PATH") or os.path.join(_REPO_ROOT, "cpm", "app", "SFM_Character_Preset_Manager.py")
REFERENCE_SHA256 = "bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5"  # item 8 COMPLETE / PASS
CANDIDATE_SHA256 = "4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7"
# Superseded: 7e4686d7 (live-verified U2; previous Getting started wording), kept for the record.
SUPERSEDED_REFINED_SHA256 = "7e4686d7c6fe699743a1f611e50d7adce030037f147c5d6c7654c589f30bdb36"
# Superseded first visual candidate (solid role fills, "Choose a character" heading); kept for the record.
SUPERSEDED_CANDIDATE_SHA256 = "5c6e27895920f27100f0692ef3a5565888463d5da453f3c9303ebb67c766b58e"
ICON_PNG_SHA256 = "65cd4fb31059652537b7e4146c4a5c02e82d00104bb3d0d41d70034e80b21185"  # 64x64 RGBA
HELPER_TEXT_SHA256 = "6df2c300a11f444f4f6b63901ff946ce3f7a18dc1cdb8f04598a8d1cf6e64623"  # palette + helper, as inserted
ICON_SOURCE_SHA256 ="c466919c137128d081e652d5c6b3e4404a8f463f14cc23b100cc35d380014c0d"  # owner-supplied 1254x1254
PY2 = sys.version_info[0] == 2
_TEXT = unicode if PY2 else str  # noqa: F821
RESULTS = []

# --- Approved presentation ------------------------------------------------------
HELP_HEADING = u"Getting started"
HELP_CHARACTER = (u"Choose the character you want to edit. Use Body Presets for body shape and Expressions for "
                  u"facial expressions. In Clothing Fit, choose clothing or accessories to fit to that character.")
HELP_PLAYHEAD = (u"The model list shows models in the shot under the playhead. To use a character from another shot, "
                 u"move the playhead into that shot, click Refresh Model List, then choose the character.")
HELP_BOLD = [u"Body Presets", u"Expressions", u"Clothing Fit", u"Refresh Model List"]  # UI names, Help convention


def _help_html(text):
    for term in HELP_BOLD:
        text = re.sub(u"(?<= )%s(?=[ ,.])" % re.escape(term), u"<b>%s</b>" % term, text, count=1)
    return text
UPDATE_COPY = u"The preset's current values will be overwritten."
CLEAR_STATUS_TAIL = u"Click Clear Classification, then choose a new classification under Needs review."
# Restrained accents: neutral fill and text; the role is carried by the border.
PALETTES = {
    u"primary": {"background": "#494949", "border": "#4f7594", "color": "#d8d8d8",
                 "hover": "#515151", "hover_border": "#5b88ad", "pressed": "#3e4247"},
    u"favorite": {"background": "#494949", "border": "#806d43", "color": "#d8d8d8",
                  "hover": "#515151", "hover_border": "#947d4b", "pressed": "#45423c"},
    u"destructive": {"background": "#494949", "border": "#7a4d4d", "color": "#d8d8d8",
                     "hover": "#515151", "hover_border": "#8d5959", "pressed": "#463e3e"},
}
NEUTRAL_FILL, NEUTRAL_BORDER, NEUTRAL_PRESSED = "#494949", "#5b5b5b", "#414141"
DISABLED = ("#393939", "#858585", "#484848")  # neutral disabled background / text / border
ROLES = sorted([("apply_body", u"primary"), ("apply_expr", u"primary"), ("fit_button", u"primary"),
                ("favorite_body", u"favorite"), ("favorite_expr", u"favorite"),
                ("delete_body", u"destructive"), ("delete_expr", u"destructive")])
NEUTRAL = ["save_body", "update_body", "info_body", "save_expr", "update_expr", "info_expr", "refresh", "details",
           "help_button", "mark_expr", "mark_body", "mark_out", "reclassify_flex"]
GRID = {"mark_expr": [0, 0], "mark_body": [0, 1], "mark_out": [1, 0], "reclassify_flex": [1, 1]}
MIN_SIZE, DEFAULT_SIZE = [540, 650], [580, 800]
# Tokens whose counts must not change: no new scope/watch/polling mechanism.
MECHANISM_TOKENS = ["QTimer", "singleShot", "startTimer", "setInterval", "QFileSystemWatcher", "installEventFilter",
                    "GetShotAtCurrentTime", "GetSelected", "SelectedShots", "prod_scope(", "prod_cpm_authorize_operation(",
                    "modal_watch_timer", "QSettings", "setProperty"]

# --- Declared edits (scope, old, new, count) ---------------------------------------
# Scope None = module; "ProdWindow.<method>" = that ProdWindow method only.
EDITS = [
    (None, u'PROD_WINDOW_ICON_NAME = u"SFMCPMGearIcon.png"', u'PROD_WINDOW_ICON_NAME = u"SFMCPMIconWoman.png"', 1),
    ("ProdWindow.__init__", u'                "<b>Model:</b>"', u'                "<b>Character Model:</b>"', 1),
    ("ProdWindow.__init__", u"        self.setMinimumSize(\n            500,\n            650,\n        )\n"
     u"        self.resize(\n            520,\n            800,\n        )",
     u"        self.setMinimumSize(\n            540,\n            650,\n        )\n"
     u"        self.resize(\n            580,\n            800,\n        )", 1),
]
for _k in ("body", "expr"):
    EDITS += [
        ("ProdWindow.__init__", u"tool_apply_main_action_button(self.apply_%s)" % _k,
         u'tool_apply_semantic_action_button(self.apply_%s, u"primary")' % _k, 1),
        ("ProdWindow.__init__", u"tool_apply_secondary_action_button(self.favorite_%s)" % _k,
         u'tool_apply_semantic_action_button(self.favorite_%s, u"favorite")' % _k, 1),
        ("ProdWindow.__init__", u"tool_apply_secondary_action_button(self.delete_%s)" % _k,
         u'tool_apply_semantic_action_button(self.delete_%s, u"destructive")' % _k, 1),
    ]
EDITS += [
    ("ProdWindow.__init__", u'        self.fit_button = QtGui.QPushButton("Fit Selected to Model")\n',
     u'        self.fit_button = QtGui.QPushButton("Fit Selected to Model")\n'
     u'        tool_apply_semantic_action_button(self.fit_button, u"primary")\n', 1),
    ("ProdWindow.__init__", u"        review_actions = QtGui.QHBoxLayout()\n",
     u"        # Two rows: the existing order, carried into a 2x2 grid.\n"
     u"        review_actions = QtGui.QGridLayout()\n", 1),
]
for _w, (_r, _c) in sorted(GRID.items()):
    EDITS.append(("ProdWindow.__init__", u"        review_actions.addWidget(\n            self.%s\n        )" % _w,
                  u"        review_actions.addWidget(\n            self.%s,\n            %d, %d,\n        )" % (_w, _r, _c), 1))
EDITS += [
    ("ProdWindow.__init__", u'            "Reclassify Flex"\n        )', u'            "Clear Classification"\n        )', 1),
    ("ProdWindow.populate", u'                "Choose a model"\n', u'                "Choose a character model"\n', 1),
    ("ProdWindow.populate", u'                "Choose a model."', u'                "Choose a character model."', 3),
    ("ProdWindow.populate", u'"%d model(s) found. Choose a model."', u'"%d model(s) found. Choose a character model."', 1),
    ("ProdWindow.clear_model_selection", u'                "Choose a model."', u'                "Choose a character model."', 3),
    ("ProdWindow.clear_model_selection", u'"Choose a model to begin."', u'"Choose a character model to begin."', 1),
    ("ProdWindow.review_changed",
     u'"Currently excluded from presets. Reclassify Flex moves it back to Needs review so you can classify it again."',
     u'"Excluded from presets. ' + CLEAR_STATUS_TAIL + u'"', 1),
    ("ProdWindow.review_changed",
     u'u"Currently classified as %s. Reclassify Flex moves it back to Needs review so you can classify it again."',
     u'u"Classified as %s. ' + CLEAR_STATUS_TAIL + u'"', 1),
    ("ProdWindow.operation_default_error_copy", u'"Can\'t reclassify flex",', u'"Can\'t clear classification",', 1),
    ("ProdWindow.update_kind", u"                box.setIcon(\n                    QtGui.QMessageBox.Question\n"
     u"                )\n", u"", 1),
    ("ProdWindow.update_kind", u'"This overwrites the values currently saved in this preset."', u'"' + UPDATE_COPY + u'"', 1),
    ("ProdWindow.open_help",
     u"                <h3>Choose a model</h3>\n"
     u"                <p>Select the model you want to work with from the <b>Model</b> menu. The Manager shows the "
     u"presets saved for that model.</p>\n",
     u"                <h3>" + HELP_HEADING + u"</h3>\n"
     u"                <p>" + _help_html(HELP_CHARACTER) + u"</p>\n"
     u"                <p>" + _help_html(HELP_PLAYHEAD) + u"</p>\n", 1),
    ("ProdWindow.open_help", u"click <b>Reclassify Flex</b>.</p>", u"click <b>Clear Classification</b>.</p>", 1),
]
HELPER_ANCHOR = u"\ndef tool_favorite_star_icon("
HELPER_AFTER = u"""def tool_apply_secondary_action_button(
    button,
):
    # Layout, rather than a second color family, carries hierarchy.
    tool_apply_main_action_button(
        button
    )
"""


def check(name, condition, value=None):
    RESULTS.append((name, bool(condition)))
    print("[%s] %s" % ("PASS" if condition else "FAIL", name))
    if not condition and value is not None:
        print("      value: %s" % (repr(value)[:1500],))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _read_reference(path):
    raw = _read(path)
    if _sha(raw) != REFERENCE_SHA256:
        raise SystemExit("REFUSED: --reference is not the item-8 app %s" % REFERENCE_SHA256)
    return raw


def _route():
    import test_cpm_app_canonical_route as route
    return route


def _source(raw):
    route = _route()
    path = os.path.join(tempfile.gettempdir(), "cpm_uipass_src_%s.py" % _sha(raw)[:12])
    with open(path, "wb") as f:
        f.write(raw)
    return route.AppSource(path)


# ---------------------------------------------------------------------------
# Static sections
# ---------------------------------------------------------------------------

def _scope_span(text, scope):
    """(start, end) character span of a ProdWindow method, or the module."""
    if scope is None:
        return 0, len(text)
    cls, meth = scope.split(".")
    c0 = text.index(u"\nclass %s(" % cls)
    c1 = text.index(u"\ndef ", c0 + 1)  # next module-level def ends the class
    marker = u"\n    def %s(" % meth
    assert text.count(marker, c0, c1) == 1, scope
    m0 = text.index(marker, c0)
    m1 = text.find(u"\n    def ", m0 + len(marker))
    m1 = c1 if (m1 < 0 or m1 > c1) else m1
    return m0, m1


def _icon_block(text):
    m = re.search(u'PROD_WINDOW_ICON_PNG_BASE64 = \\(\n(?:    "[A-Za-z0-9+/=]*"\n)+\\)\n', text)
    return m


def _icon_png(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == ["PROD_WINDOW_ICON_PNG_BASE64"]:
            return base64.b64decode(ast.literal_eval(node.value))
    return None


def _decode_png_rgba(png):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, hdr, chunks = 8, [], None, []
    while pos < len(png):
        ln, typ = struct.unpack(">I4s", png[pos:pos + 8])
        body = png[pos + 8:pos + 8 + ln]
        chunks.append(typ)
        if typ == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat.append(body)
        pos += 12 + ln
    w, h = hdr[0], hdr[1]
    raw = bytearray(zlib.decompress(b"".join(idat)))
    stride, rows, prev, i = w * 4, [], bytearray(w * 4), 0
    for _ in range(h):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if ft == 1:
                pr = a
            elif ft == 2:
                pr = b
            elif ft == 3:
                pr = (a + b) >> 1
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            else:
                pr = 0
            line[x] = (line[x] + pr) & 255
        rows.append(line)
        prev = line
    return hdr, chunks, rows


def section_pins(ref_raw, cand_raw):
    check("pins.reference_is_item8_app", _sha(ref_raw) == REFERENCE_SHA256)
    check("pins.candidate_exact", _sha(cand_raw) == CANDIDATE_SHA256, _sha(cand_raw))
    check("pins.candidate_is_new_identity", CANDIDATE_SHA256 != REFERENCE_SHA256)
    check("pins.candidate_utf8_lf", b"\r\n" not in cand_raw and cand_raw.decode("utf-8") is not None)
    check("pins.candidate_compiles", compile(cand_raw, APP_PATH, "exec") is not None)


def section_reconstruction(ref_raw, cand_raw):
    ref, cand = ref_raw.decode("utf-8"), cand_raw.decode("utf-8")
    text, problems = ref, []
    for scope, old, new, count in EDITS:
        a, b = _scope_span(text, scope)
        seg = text[a:b]
        if seg.count(old) != count:
            problems.append([scope, old[:60], seg.count(old), count])
            continue
        text = text[:a] + seg.replace(old, new) + text[b:]
    check("reconstruction.every_declared_edit_matches_exactly", not problems, problems)
    # Icon: the reference block is replaced by the candidate's own block (pinned below).
    m_ref, m_cand = _icon_block(text), _icon_block(cand)
    check("reconstruction.icon_blocks_found", m_ref is not None and m_cand is not None)
    text = text[:m_ref.start()] + m_cand.group(0) + text[m_ref.end():]
    # Helper: the candidate's inserted text between the secondary helper and the star icon.
    h0 = cand.index(HELPER_AFTER) + len(HELPER_AFTER)
    h1 = cand.index(HELPER_ANCHOR)
    inserted = cand[h0:h1]
    tree = ast.parse(inserted)
    kinds = [(type(n).__name__, getattr(n, "name", None) or [t.id for t in n.targets][0]) for n in tree.body]
    check("reconstruction.inserted_helper_text_pinned", _sha(inserted.encode("utf-8")) == HELPER_TEXT_SHA256,
          _sha(inserted.encode("utf-8")))
    check("reconstruction.inserted_text_is_palette_and_helper_only",
          kinds == [("Assign", "PROD_ACTION_BUTTON_PALETTES"), ("FunctionDef", "tool_apply_semantic_action_button")], kinds)
    r0 = text.index(HELPER_AFTER) + len(HELPER_AFTER)
    r1 = text.index(HELPER_ANCHOR)
    check("reconstruction.reference_gap_was_blank", text[r0:r1] == u"\n", text[r0:r1])
    text = text[:r0] + inserted + text[r1:]
    check("reconstruction.candidate_equals_reference_plus_declared_edits", text == cand,
          next((i for i, (x, y) in enumerate(zip(text, cand)) if x != y), min(len(text), len(cand))))
    # Name-level bounds (informative; implied by the byte reconstruction).
    rs, cs = _source(ref_raw), _source(cand_raw)
    changed = sorted(n for n in cs.top if n in rs.top and cs.top_text(n) != rs.top_text(n))
    check("bounds.changed_top_level", changed == ["PROD_WINDOW_ICON_NAME", "PROD_WINDOW_ICON_PNG_BASE64", "ProdWindow"], changed)
    check("bounds.added_top_level", sorted(set(cs.top) - set(rs.top))
          == ["PROD_ACTION_BUTTON_PALETTES", "tool_apply_semantic_action_button"], sorted(set(cs.top) - set(rs.top)))
    check("bounds.removed_top_level", not (set(rs.top) - set(cs.top)))
    rm, cm = rs.methods("ProdWindow"), cs.methods("ProdWindow")
    mchanged = sorted(n for n in cm if n in rm and cs.method_text("ProdWindow", n) != rs.method_text("ProdWindow", n))
    check("bounds.changed_prodwindow_methods", mchanged == sorted([
        "__init__", "clear_model_selection", "open_help", "operation_default_error_copy", "populate",
        "review_changed", "update_kind"]), mchanged)
    check("bounds.no_added_or_removed_methods", set(cm) == set(rm))
    for name in ("tool_apply_main_action_button", "tool_apply_secondary_action_button", "tool_apply_primary_button",
                 "tool_window_icon", "tool_apply_window_icon", "tool_apply_visual_theme", "tool_apply_tab_style",
                 "tool_set_status", "tool_favorite_star_icon"):
        check("bounds.unchanged.%s" % name, cs.top_text(name) == rs.top_text(name))
    return cs


def section_icon(cs, ref_raw):
    png = _icon_png(cs.tree)
    check("icon.embedded_png_pinned", png is not None and _sha(png) == ICON_PNG_SHA256, png and _sha(png))
    check("icon.name_is_owner_supplied", u'PROD_WINDOW_ICON_NAME = u"SFMCPMIconWoman.png"' in cs.top_text("PROD_WINDOW_ICON_NAME"))
    old_png = _icon_png(_source(ref_raw).tree)
    check("icon.previous_gear_icon_removed", old_png is not None and base64.b64encode(old_png).decode("ascii")[:200]
          not in cs.raw.decode("utf-8"))
    hdr, chunks, rows = _decode_png_rgba(png)
    check("icon.size_64_square_rgba8", hdr == (64, 64, 8, 6, 0, 0, 0), hdr)
    check("icon.no_ancillary_chunks", chunks == [b"IHDR", b"IDAT", b"IEND"], chunks)
    alphas = [row[x + 3] for row in rows for x in range(0, 256, 4)]
    corners = [rows[y][x * 4 + 3] for y in (0, 63) for x in (0, 63)]
    # The owner-supplied source's opaque area is alpha 254 (its 255 pixels are a thin minority).
    check("icon.transparency_preserved", corners == [0, 0, 0, 0] and min(alphas) == 0 and max(alphas) >= 254,
          [corners, min(alphas), max(alphas)])
    check("icon.compact_production_size", len(png) < 8192, len(png))
    check("icon.no_runtime_file_dependency", u"SFMCPMIconWoman.png" not in cs.top_text("tool_window_icon")
          and u"open(" not in cs.top_text("tool_window_icon"))


def section_wording(cs):
    init = cs.method_text("ProdWindow", "__init__")
    pop = cs.method_text("ProdWindow", "populate")
    clr = cs.method_text("ProdWindow", "clear_model_selection")
    check("wording.selector_label", u'"<b>Character Model:</b>"' in init and u'"<b>Model:</b>"' not in init)
    check("wording.placeholder", u'"Choose a character model"\n' in pop and u'"Choose a model"' not in pop)
    check("wording.empty_and_status_copy", u"Choose a model" not in pop and u"Choose a model" not in clr
          and clr.count(u'"Choose a character model."') == 3 and u'"Choose a character model to begin."' in clr)
    check("wording.refresh_model_list_unchanged", init.count(u'"Refresh Model List"') == 1)
    check("wording.clear_classification_button", u'"Clear Classification"' in init and u"Reclassify Flex" not in init)
    rc = cs.method_text("ProdWindow", "review_changed")
    check("wording.reviewed_status_copy", (u'u"Classified as %s. ' + CLEAR_STATUS_TAIL + u'"') in rc
          and (u'"Excluded from presets. ' + CLEAR_STATUS_TAIL + u'"') in rc and u"Reclassify Flex" not in rc)
    uk = cs.method_text("ProdWindow", "update_kind")
    check("wording.update_confirmation_copy", (u'"' + UPDATE_COPY + u'"') in uk
          and u"This overwrites the values currently saved" not in uk)
    check("wording.update_confirmation_no_question_icon", u"QMessageBox.Question" not in uk and u"setIcon(" not in uk)
    check("wording.update_confirmation_kept",
          re.search(u'"Update Preset",\\s+QtGui\\.QMessageBox\\.AcceptRole', uk) is not None
          and u"box.exec_()" in uk and re.search(u"box\\.setDefaultButton\\(\\s+cancel_button", uk) is not None)
    html = None
    for node in ast.walk(cs.methods("ProdWindow")["open_help"][2]):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "setHtml":
            html = ast.literal_eval(node.args[0])
    plain = re.sub(u"\\s+", u" ", re.sub(u"<[^>]+>", u" ", re.sub(u"<style>.*?</style>", u"", html or u"", flags=re.S)))
    plain = plain.replace(u" ,", u",")
    check("help.getting_started_heading_first", html is not None and HELP_HEADING == u"Getting started"
          and 0 <= html.find(u"<h3>") == html.find(u"<h3>Getting started</h3>")
          and u"<h3>Choose a character</h3>" not in html)
    check("help.character_paragraph", HELP_CHARACTER in plain, plain[:400])
    check("help.playhead_paragraph", re.sub(u"\\s+", u" ", HELP_PLAYHEAD) in plain, plain[:600])
    check("help.ui_names_bold", all((u"<b>%s</b>" % t) in (html or u"") for t in HELP_BOLD)
          and (html or u"").count(u"<b>Refresh Model List</b>") == 1)
    check("help.clear_classification", u"click <b>Clear Classification</b>" in (html or u"")
          and u"Reclassify Flex" not in (html or u""))
    check("help.not_added_to_main_window", HELP_CHARACTER not in init and u"playhead" not in init.lower())
    # Internal operation identities stay unchanged (logs, authorization names).
    check("wording.internal_operation_label_unchanged",
          cs.method_text("ProdWindow", "review_reclassify").count(u'"Reclassify Flex"') == 2)


def section_roles(cs, ref_raw):
    calls = []
    for node in ast.walk(cs.tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "tool_apply_semantic_action_button":
            target, role = node.args
            calls.append((target.attr, ast.literal_eval(role)))
    check("roles.semantic_call_census", sorted(calls) == ROLES, sorted(calls))
    init = cs.method_text("ProdWindow", "__init__")
    check("roles.neutral_controls_untouched", all(u"tool_apply_semantic_action_button(self.%s" % n not in init for n in NEUTRAL)
          and init.count(u"tool_apply_main_action_button(self.save_") == 2
          and init.count(u"tool_apply_main_action_button(self.update_") == 2
          and init.count(u"tool_apply_secondary_action_button(self.info_") == 2)
    palettes = None
    for node in cs.tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "PROD_ACTION_BUTTON_PALETTES":
            palettes = ast.literal_eval(node.value)
    check("roles.palette_values_pinned", palettes == PALETTES, palettes)
    main_btn = cs.top_text("tool_apply_main_action_button")

    def rgb(h):
        return [int(h[i:i + 2], 16) for i in (1, 3, 5)]

    def spread(h):
        return max(rgb(h)) - min(rgb(h))
    check("roles.normal_fill_is_neutral", all(p["background"] == NEUTRAL_FILL and p["color"] == "#d8d8d8"
                                              for p in palettes.values()) and NEUTRAL_FILL in main_btn)
    borders = [palettes[r]["border"] for r in (u"primary", u"favorite", u"destructive")]
    check("roles.border_accents_distinguish_roles", len(set(borders)) == 3 and NEUTRAL_BORDER not in borders
          and rgb(borders[0])[2] > rgb(borders[0])[0]            # blue cast
          and rgb(borders[1])[0] > rgb(borders[1])[2]            # warm cast
          and rgb(borders[2])[0] > max(rgb(borders[2])[1:]),     # red cast
          borders)
    check("roles.hover_restrained", all(p["hover"] == "#515151" and spread(p["hover"]) == 0
                                        and spread(p["hover_border"]) >= spread(p["border"]) for p in palettes.values()))
    check("roles.pressed_restrained", all(spread(p["pressed"]) <= 12
                                          and abs(sum(rgb(p["pressed"])) - sum(rgb(NEUTRAL_PRESSED))) <= 30
                                          for p in palettes.values()),
          [p["pressed"] for p in palettes.values()])
    check("roles.no_colored_text_or_solid_fill", all(spread(p["background"]) == 0 and spread(p["color"]) == 0
                                                     for p in palettes.values()))
    helper = cs.top_text("tool_apply_semantic_action_button")
    disabled_block = u"QPushButton:disabled {\n            background-color: #393939;\n            color: #858585;\n            border: 1px solid #484848;\n        }"
    check("roles.disabled_is_neutral_disabled", disabled_block in helper and disabled_block in main_btn)
    check("roles.every_state_defined", all(s in helper for s in (u"QPushButton {", u"QPushButton:hover {",
                                                                 u"QPushButton:pressed {", u"QPushButton:disabled {")))
    ref = ref_raw.decode("utf-8")
    cand = cs.raw.decode("utf-8")
    counts = dict((t, (ref.count(t), cand.count(t))) for t in MECHANISM_TOKENS)
    check("mechanism.no_new_scope_watch_or_polling", all(a == b for a, b in counts.values()),
          dict((t, v) for t, v in counts.items() if v[0] != v[1]))


# ---------------------------------------------------------------------------
# Runtime: real ProdWindow (R15 harness), candidate vs reference
# ---------------------------------------------------------------------------

def _r15():
    import test_cpm_app_r15_namespace_isolation as r15
    return r15


def scenario_window(env, real):
    ns = env.module().__dict__
    window = env.slot()
    QtCore, QtGui = ns["QtCore"], ns["QtGui"]
    out = {"window": window is not None, "attrs": sorted(vars(window).keys()),
           "module_names": sorted(k for k in ns if not k.startswith("__"))}
    gc.collect()
    out["timers"] = len([o for o in gc.get_objects() if isinstance(o, QtCore.QTimer)])
    if not real:
        return out
    env.settle()
    out["min_size"] = [window.minimumSize().width(), window.minimumSize().height()]
    out["size"] = [window.size().width(), window.size().height()]
    out["labels"] = sorted(_TEXT(lbl.text()) for lbl in window.findChildren(QtGui.QLabel) if u"Model" in _TEXT(lbl.text()))
    out["combo0"] = _TEXT(window.combo.itemText(0))
    out["refresh"] = _TEXT(window.refresh.text())
    out["reclassify_text"] = _TEXT(window.reclassify_flex.text())
    # QIcon.availableSizes() crashes PySide 1.2; actualSize() reports the largest real pixmap.
    icon = window.windowIcon()
    largest = icon.actualSize(QtCore.QSize(1024, 1024))
    out["icon"] = {"null": icon.isNull(), "sizes": [[largest.width(), largest.height()]],
                   "alpha": icon.pixmap(64, 64).hasAlpha(),
                   "same_as_cached": ns["tool_window_icon"]() is not None and not ns["tool_window_icon"]().isNull()}
    grid, positions = None, {}
    lay = window.review_page.layout()
    for i in range(lay.count()):
        sub = lay.itemAt(i).layout()
        if sub is not None and isinstance(sub, QtGui.QGridLayout):
            grid = sub
    if grid is not None:
        for name in GRID:
            pos = grid.getItemPosition(grid.indexOf(getattr(window, name)))
            positions[name] = [int(pos[0]), int(pos[1])]
    out["grid"] = {"is_grid": grid is not None, "positions": positions,
                   "rows": grid.rowCount() if grid else None, "cols": grid.columnCount() if grid else None}

    def sample(button):
        tab = button.parentWidget()
        while tab is not None and tab not in (window.body_page, window.expr_page, window.fit_page, window.review_page):
            tab = tab.parentWidget()
        if tab is not None and window.tabs.indexOf(tab) >= 0:
            window.tabs.setCurrentWidget(tab)
        env.settle()
        image = QtGui.QPixmap.grabWidget(button).toImage()
        y = image.height() // 2
        return [QtGui.QColor(image.pixel(3, y)).name(), QtGui.QColor(image.pixel(0, y)).name()]
    colors = {}
    for name in [r[0] for r in ROLES] + ["save_body", "update_body", "info_body", "refresh", "details"]:
        button = getattr(window, name)
        was = button.isEnabled()
        button.setEnabled(False)
        disabled = sample(button)
        button.setEnabled(True)
        enabled = sample(button)
        button.setEnabled(was)
        colors[name] = {"disabled": _TEXT(disabled[0]), "enabled": _TEXT(enabled[0]),
                        "disabled_border": _TEXT(disabled[1]), "enabled_border": _TEXT(enabled[1]),
                        "sheet": _TEXT(button.styleSheet())}
    out["colors"] = colors
    if window.tabs.indexOf(window.review_page) < 0:
        window.tabs.addTab(window.review_page, "Review")
    fits = {}
    for size in (DEFAULT_SIZE, MIN_SIZE, [520, 800]):
        window.resize(size[0], size[1])
        env.settle()
        bar = window.tabs.tabBar()
        fits["%dx%d" % tuple(size)] = {"window": [window.width(), window.height()], "tabs": bar.count(),
                                       "bar_width": bar.width(), "needed": bar.sizeHint().width(),
                                       "tab_widths": [bar.tabRect(i).width() for i in range(bar.count())]}
    out["tab_fit"] = fits
    return out


def child_main(qt_mode, root, reference, target):
    try:
        app_bytes = _read_reference(reference) if target == "reference" else _read(APP_PATH)
        r15 = _r15()
        env = r15.Env(qt_mode, root)
        env.deploy(impl_bytes=app_bytes)
        env.click()
        payload = {"ok": True, "result": scenario_window(env, qt_mode == "real")}
    except BaseException:  # noqa: BLE001
        import traceback
        payload = {"ok": False, "error": traceback.format_exc()[-2000:]}
    sys.stdout.write("UIPASS_CHILD_RESULT " + json.dumps(payload, default=repr, sort_keys=True) + "\n")
    sys.stdout.flush()


def run_child(mode, reference, target):
    root = os.path.join(tempfile.gettempdir(), "cpm_uipass_window", "%s_%s" % (mode, target))
    if os.path.isdir(root):
        shutil.rmtree(root)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child=window", "--qt=%s" % mode,
                             "--root=%s" % root, "--reference=%s" % reference, "--target=%s" % target],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = proc.communicate()[0].decode("utf-8", "replace")
    for line in output.splitlines():
        if line.startswith("UIPASS_CHILD_RESULT "):
            return json.loads(line[len("UIPASS_CHILD_RESULT "):])
    return {"ok": False, "error": output[-2000:]}


def section_window_runtime(reference):
    modes = (["real"] if _r15().qt_available() else []) + ["model"]
    print("Qt modes for window gates: %s" % ", ".join(modes))
    report = {}
    for mode in modes:
        cand, ref = run_child(mode, reference, "candidate"), run_child(mode, reference, "reference")
        check("%s.children_completed" % mode, cand["ok"] and ref["ok"], [cand.get("error"), ref.get("error")])
        c, r = cand.get("result") or {}, ref.get("result") or {}
        check("%s.window_created" % mode, c.get("window") is True and r.get("window") is True)
        check("%s.no_new_window_state" % mode, c.get("attrs") == r.get("attrs") and bool(c.get("attrs")),
              sorted(set(c.get("attrs") or []) ^ set(r.get("attrs") or [])))
        check("%s.no_new_timers" % mode, c.get("timers") == r.get("timers") and c.get("timers") is not None,
              [c.get("timers"), r.get("timers")])
        check("%s.module_names_only_helper_added" % mode,
              sorted(set(c.get("module_names") or []) - set(r.get("module_names") or []))
              == ["PROD_ACTION_BUTTON_PALETTES", "tool_apply_semantic_action_button"]
              and not set(r.get("module_names") or []) - set(c.get("module_names") or []))
        if mode != "real":
            continue
        check("real.window_dimensions", c.get("min_size") == MIN_SIZE and c.get("size") == DEFAULT_SIZE
              and r.get("min_size") == [500, 650] and r.get("size") == [520, 800],
              [c.get("min_size"), c.get("size"), r.get("min_size"), r.get("size")])
        check("real.selector_label", c.get("labels") == [u"<b>Character Model:</b>"], c.get("labels"))
        check("real.placeholder", c.get("combo0") == u"Choose a character model", c.get("combo0"))
        check("real.refresh_model_list_unchanged", c.get("refresh") == r.get("refresh") == u"Refresh Model List")
        check("real.clear_classification_text", c.get("reclassify_text") == u"Clear Classification")
        icon = c.get("icon") or {}
        check("real.window_icon_new_64px", icon.get("null") is False and icon.get("sizes") == [[64, 64]]
              and icon.get("alpha") is True
              and icon.get("same_as_cached") is True, icon)
        g = c.get("grid") or {}
        check("real.review_grid_2x2", g.get("is_grid") is True and g.get("positions") == GRID
              and g.get("rows") == 2 and g.get("cols") == 2, g)
        check("real.reference_review_was_single_row", (r.get("grid") or {}).get("is_grid") is False)
        colors = c.get("colors") or {}
        for name, role in ROLES:
            col = colors.get(name, {})
            check("real.role.%s.%s_enabled_neutral_fill_role_border" % (name, role),
                  col.get("enabled") == NEUTRAL_FILL and col.get("enabled_border") == PALETTES[role]["border"], col)
            check("real.role.%s.disabled_neutral" % name, col.get("disabled") == DISABLED[0]
                  and col.get("disabled_border") == DISABLED[2], col)
        for name in ("save_body", "update_body", "info_body"):
            col, rcol = colors.get(name, {}), (r.get("colors") or {}).get(name, {})
            check("real.neutral.%s_unchanged" % name, col and col == rcol and col.get("enabled") == "#494949", [col, rcol])
        for name in ("refresh", "details"):
            col, rcol = colors.get(name, {}), (r.get("colors") or {}).get(name, {})
            check("real.neutral.%s_unchanged" % name, col and col == rcol, [col, rcol])
        fit = c.get("tab_fit") or {}
        for size in ("%dx%d" % tuple(DEFAULT_SIZE), "%dx%d" % tuple(MIN_SIZE)):
            f = fit.get(size, {})
            check("real.tabs_fit_without_scrolling_%s" % size, f.get("tabs") == 4 and f.get("bar_width", 0) >= f.get("needed", 1), f)
        rf = (r.get("tab_fit") or {}).get("520x800", {})
        check("real.reference_520_scrolled", rf.get("tabs") == 4 and rf.get("bar_width", 0) < rf.get("needed", 0), rf)
        report = {"candidate_tab_fit": fit, "reference_520": rf}
    return report


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    reference = args.get("--reference") or os.environ.get("CPM_UIPASS_REFERENCE_APP")
    if "--child" in args:
        child_main(args["--qt"], args["--root"], reference, args["--target"])
        return
    if not reference:
        raise SystemExit("REFUSED: an explicit --reference=<pinned item-8 app> is required")
    print("Interpreter: %s" % sys.version.split()[0])
    ref_raw, cand_raw = _read_reference(reference), _read(APP_PATH)
    section_pins(ref_raw, cand_raw)
    cs = section_reconstruction(ref_raw, cand_raw)
    section_icon(cs, ref_raw)
    section_wording(cs)
    section_roles(cs, ref_raw)
    report = section_window_runtime(reference)
    if report:
        print("TAB FIT (real Qt): %s" % json.dumps(report, sort_keys=True))
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
