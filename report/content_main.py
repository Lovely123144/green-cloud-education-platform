# -*- coding: utf-8 -*-
import re
import docx_lib as L
from docx_lib import p_figure, p_fig_caption, p_table_caption, table, spacer
from content_refs import REFS
from content_a import part_a
from content_b import part_b
from content_c import part_c
from content_d import part_d

L.REFS.update(REFS)


def build(img_info):
    B = []; add = B.append
    fig_no = {}; tab_no = {}

    def fig(key, caption):
        n = len(fig_no) + 1; fig_no[key] = n; rid, idx, cx, cy = img_info[key]
        add(p_figure(rid, idx, cx, cy, key)); add(p_fig_caption(f"Fig.{n}.", caption))

    def tab(key, caption, headers, rows, widths, align=None, sz=18, bold_first_col=False):
        n = len(tab_no) + 1; tab_no[key] = n
        add(p_table_caption(f"Table {n}.", caption)); add(table(headers, rows, widths, align, sz, bold_first_col)); add(spacer(80))

    for part in (part_a, part_b, part_c):
        part(add, fig, tab)
    ref_slot = len(B); head_slot = len(L.HEADINGS); part_d(add, fig, tab)   # appendices built last, placed after the references
    appendix = B[ref_slot:]; del B[ref_slot:]; app_heads = L.HEADINGS[head_slot:]; del L.HEADINGS[head_slot:]
    B.append(L.p_h1("References", numbered=False)); L.HEADINGS.extend(app_heads)
    L.HEADINGS[:] = [h for h in L.HEADINGS if h[1] != "References"]
    L.HEADINGS.insert(head_slot, (1, "References"))
    B.extend(L.p_ref(L.REFS[k]) for k, _ in sorted(L.CITES.items(), key=lambda kv: kv[1]))
    B.extend(appendix)

    def resolve(m):
        kind, key = m.group(1), m.group(2)
        if kind == "T": return f"Table {tab_no[key]}"
        return f"Fig. {fig_no[key]}"
    out = [re.sub(r"@@([TF]):(\w+)@@", resolve, x) for x in B]
    left = [x for x in out if "@@" in x]
    assert not left, left[0][:200]
    return out
