"""Small helpers to generate WordprocessingML paragraphs/tables that match the course template."""
import re
from xml.sax.saxutils import escape

TEXT_W = 9014   # text width in dxa (A4, template margins)
CITES = {}      # key -> number (assigned by first appearance)
HEADINGS = []   # (level, display text) in document order, used for the table of contents
H1_COUNT = [0]
REFS = {}       # key -> formatted reference string (filled by caller)


def cite_numbers(keys):
    nums = []
    for k in keys:
        if k not in REFS:
            raise KeyError(f"unknown reference key {k}")
        if k not in CITES:
            CITES[k] = len(CITES) + 1
        nums.append(CITES[k])
    return ",".join(str(n) for n in sorted(set(nums)))


def _expand_cites(text):
    return re.sub(r"\[\[([a-z0-9_,]+)\]\]", lambda m: "[" + cite_numbers(m.group(1).split(",")) + "]", text)


def _run(text, b=False, i=False, sub=False, sup=False, sz=None, extra=""):
    rpr = ""
    if b: rpr += "<w:b/><w:bCs/>"
    if i: rpr += "<w:i/><w:iCs/>"
    if sz: rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if sub: rpr += '<w:vertAlign w:val="subscript"/>'
    if sup: rpr += '<w:vertAlign w:val="superscript"/>'
    rpr += extra
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


TOK = re.compile(r"(\*\*.+?\*\*|\*.+?\*|_\{.+?\}|\^\{.+?\})")


def runs(text, sz=None, base_b=False):
    text = _expand_cites(text)
    out = []
    for part in TOK.split(text):
        if not part:
            continue
        if part.startswith("**"): out.append(_run(part[2:-2], b=True, sz=sz))
        elif part.startswith("*"): out.append(_run(part[1:-1], i=True, b=base_b, sz=sz))
        elif part.startswith("_{"): out.append(_run(part[2:-1], sub=True, b=base_b, sz=sz))
        elif part.startswith("^{"): out.append(_run(part[2:-1], sup=True, b=base_b, sz=sz))
        else: out.append(_run(part, b=base_b, sz=sz))
    return "".join(out)


def p_body(text, cont=False):
    ind = 0 if cont else 480
    return f'<w:p><w:pPr><w:spacing w:after="80"/><w:ind w:firstLine="{ind}"/></w:pPr>{runs(text)}</w:p>'


def p_h1(text, numbered=True, page_break=False):
    num = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="10"/></w:numPr>' if numbered else ""
    if numbered:
        H1_COUNT[0] += 1; HEADINGS.append((1, f"{H1_COUNT[0]}. {text}"))
    else:
        HEADINGS.append((1, text))
    pb = "<w:pageBreakBefore/>" if page_break else ""
    return f'<w:p><w:pPr><w:pStyle w:val="af2"/><w:keepNext/>{pb}{num}</w:pPr><w:r><w:t>{escape(text)}</w:t></w:r></w:p>'


def p_h2(text):
    HEADINGS.append((2, text))
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:before="140" w:after="60"/><w:ind w:firstLine="0"/><w:jc w:val="left"/>'
            '<w:outlineLvl w:val="2"/></w:pPr>' + runs(text, sz=26, base_b=True).replace("<w:r><w:t", "<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val=\"26\"/></w:rPr><w:t") + '</w:p>')


def p_equation(expr, number):
    return ('<w:p><w:pPr><w:tabs><w:tab w:val="center" w:pos="4507"/><w:tab w:val="right" w:pos="9014"/></w:tabs>'
            '<w:spacing w:before="60" w:after="100"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr>'
            '<w:r><w:tab/></w:r>' + runs(expr) + f'<w:r><w:tab/><w:t>({number})</w:t></w:r></w:p>')


def p_figure(rid, idx, cx, cy, name):
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:before="100" w:after="40"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr><w:r>'
            f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{idx}" name="{name}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="{idx}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def p_fig_caption(label, text):
    return ('<w:p><w:pPr><w:pStyle w:val="a3"/><w:keepLines/><w:spacing w:after="120"/><w:ind w:firstLine="0"/></w:pPr>'
            + runs(f"{label} {text}") + '</w:p>')


def p_table_caption(label, text):
    return ('<w:p><w:pPr><w:pStyle w:val="Els-table-text"/><w:keepNext/><w:spacing w:before="100" w:after="60" w:line="240" w:lineRule="auto"/>'
            '<w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr>'
            + runs(f"**{label}** {text}", sz=20) + '</w:p>')


def spacer(after=60):
    return f'<w:p><w:pPr><w:spacing w:after="{after}"/><w:ind w:firstLine="0"/></w:pPr></w:p>'


def table(headers, rows, widths, align=None, sz=18, bold_first_col=False):
    assert sum(widths) == TEXT_W, sum(widths)
    n = len(widths); align = align or ["left"] + ["center"] * (n - 1)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    def cell(txt, w, al, top=False, bottom=False, hdr=False):
        b = ""
        if top: b += '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
        b += '<w:left w:val="nil"/>'
        if bottom: b += '<w:bottom w:val="single" w:sz="%d" w:space="0" w:color="auto"/>' % (4 if hdr else 8)
        b += '<w:right w:val="nil"/>'
        kn = "<w:keepNext/>" if hdr else "<w:keepNext w:val=\"0\"/>"
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:tcBorders>{b}</w:tcBorders><w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr><w:pStyle w:val="Els-table-text"/>{kn}<w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/>'
                f'<w:ind w:firstLine="0"/><w:jc w:val="{al}"/></w:pPr>{runs(txt, sz=sz, base_b=hdr)}</w:p></w:tc>')
    out = ['<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar></w:tblPr>' % TEXT_W
           + f"<w:tblGrid>{grid}</w:tblGrid>"]
    out.append("<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>" + "".join(
        cell(h, w, "left" if a == "left" else "center", top=True, bottom=True, hdr=True) for h, w, a in zip(headers, widths, align)) + "</w:tr>")
    for ri, r in enumerate(rows):
        last = ri == len(rows) - 1
        out.append("<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(
            cell(("**%s**" % c if (bold_first_col and ci == 0 and c) else c), w, a, bottom=last)
            for ci, (c, w, a) in enumerate(zip(r, widths, align))) + "</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def p_ref(text):
    return ('<w:p><w:pPr><w:pStyle w:val="Els-reference"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="11"/></w:numPr>'
            '<w:tabs><w:tab w:val="left" w:pos="480"/></w:tabs><w:spacing w:after="40"/><w:ind w:left="480" w:hanging="480"/>'
            '<w:rPr><w:sz w:val="20"/></w:rPr></w:pPr>' + runs(text, sz=20) + '</w:p>')


def p_code(lines):
    """Monospaced, shaded code block (one paragraph per line)."""
    out = []
    for i, ln in enumerate(lines):
        first, last = i == 0, i == len(lines) - 1
        out.append('<w:p><w:pPr>' + ('<w:keepNext/>' if not last else '') + '<w:keepLines/>' +
                   '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
                   f'<w:spacing w:before="{60 if first else 0}" w:after="{100 if last else 0}" w:line="240" w:lineRule="auto"/>'
                   '<w:ind w:left="240" w:right="240" w:firstLine="0"/><w:jc w:val="left"/></w:pPr>'
                   '<w:r><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
                   f'<w:t xml:space="preserve">{escape(ln) if ln else " "}</w:t></w:r></w:p>')
    return "".join(out)


def p_bullet(text):
    return ('<w:p><w:pPr><w:spacing w:after="50"/><w:ind w:left="720" w:hanging="300"/></w:pPr>'
            '<w:r><w:t xml:space="preserve">\u2022\u00a0\u00a0</w:t></w:r>' + runs(text) + '</w:p>')


def toc_block(entries, pages):
    """Table of contents as a real TOC field with cached result (right-click > Update field in Word)."""
    out = []
    n = len(entries)
    for i, (lvl, txt) in enumerate(entries):
        pg = pages.get(txt, "")
        ind = 0 if lvl == 1 else 360
        sz = 19 if lvl == 1 else 17
        bold = "<w:b/><w:bCs/>" if lvl == 1 else ""
        rpr = f'<w:rPr>{bold}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
        pre = ""
        if i == 0:
            pre = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o \"1-2\" \\u \\h </w:instrText></w:r>'
                   '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
        post = '<w:r><w:fldChar w:fldCharType="end"/></w:r>' if i == n - 1 else ""
        out.append('<w:p><w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9014"/></w:tabs><w:snapToGrid w:val="0"/>'
                   f'<w:spacing w:before="{40 if lvl == 1 else 0}" w:after="0" w:line="215" w:lineRule="exact"/><w:ind w:left="{ind}" w:firstLine="0"/><w:jc w:val="left"/></w:pPr>'
                   f'{pre}<w:r>{rpr}<w:t xml:space="preserve">{escape(txt)}</w:t></w:r><w:r>{rpr}<w:tab/></w:r><w:r>{rpr}<w:t>{pg}</w:t></w:r>{post}</w:p>')
    return "".join(out)
