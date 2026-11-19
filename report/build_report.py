import os, re, shutil, sys, zipfile
from lxml import etree
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import json, subprocess, docx_lib as L, content_main as CM
import content_refs as C

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE = "/mnt/user-data/uploads/Final_Report_Template.docx"
WORK = "/home/claude/build_docx"; OUT = os.path.join(ROOT, "report", "Final_Report_Green_Cloud.docx")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{%s}" % NS["w"]
NSDECL = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK)
with zipfile.ZipFile(TEMPLATE) as z: z.extractall(WORK)

# ---------------- images
fig_dir = os.path.join(ROOT, "figures"); img_info = {}; rels_add = []
for i, name in enumerate(["fig_architecture", "fig_pipeline", "fig_memory", "fig_hourly", "fig_designs", "fig_scheduler", "fig_breakeven", "fig_designs", "fig_grid", "fig_sensitivity", "fig_flash", "fig_sched_example"]):
    src = os.path.join(fig_dir, name + ".png"); shutil.copy(src, os.path.join(WORK, "word", "media", name + ".png"))
    w, h = Image.open(src).size; cx = int(5.5 * 914400); cy = int(cx * h / w)
    rid = f"rIdFig{i+1}"; img_info[name] = (rid, 900 + i, cx, cy)
    rels_add.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}.png"/>')
rp = os.path.join(WORK, "word", "_rels", "document.xml.rels"); s = open(rp, encoding="utf-8").read()
open(rp, "w", encoding="utf-8").write(s.replace("</Relationships>", "".join(rels_add) + "</Relationships>"))
cp = os.path.join(WORK, "[Content_Types].xml"); s = open(cp, encoding="utf-8").read()
if 'Extension="png"' not in s:
    s = s.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)
open(cp, "w", encoding="utf-8").write(s)

# ---------------- document.xml
dp = os.path.join(WORK, "word", "document.xml"); tree = etree.parse(dp); body = tree.getroot().find("w:body", NS)
kids = list(body)

def set_underlined_run(p, text, sz):
    for r in p.findall("w:r", NS):
        rpr = r.find("w:rPr", NS)
        if rpr is not None and rpr.find("w:u", NS) is not None and r.find("w:t", NS) is not None:
            r.find("w:t", NS).text = text
            for tag in ("sz", "szCs"):
                e = rpr.find(f"w:{tag}", NS)
                if e is not None: e.set(W + "val", str(sz))
            return r
    raise RuntimeError("underlined run not found")

def drop_other_underlined(p, keep):
    for r in list(p.findall("w:r", NS)):
        rpr = r.find("w:rPr", NS)
        if r is not keep and rpr is not None and rpr.find("w:u", NS) is not None and r.find("w:t", NS) is not None:
            p.remove(r)

for idx, text in zip((4, 5, 6), C.TITLE):
    keep = set_underlined_run(kids[idx], text, 34); drop_other_underlined(kids[idx], keep)
for t in kids[11].iter(W + "t"):
    if t.text == "2023": t.text = "2026"
ts = list(kids[17].iter(W + "t")); ts[0].text = "2026  11"; ts[1].text = "  17"

# abstract
ab = kids[19]
for r in ab.findall("w:r", NS): ab.remove(r)
for r in ab.findall("w:proofErr", NS): ab.remove(r)
ab.append(etree.fromstring(f'<w:r {NSDECL}><w:t xml:space="preserve"></w:t></w:r>')); ab[-1].find("w:t", NS).text = C.ABSTRACT
for i in range(20, 30): body.remove(kids[i])
kw = kids[30]
kw.append(etree.fromstring(f'<w:r {NSDECL}><w:t xml:space="preserve"></w:t></w:r>')); kw[-1].find("w:t", NS).text = C.KEYWORDS
sect_final = kids[61]
for i in range(32, 61): body.remove(kids[i])

# new body (content_main builds everything incl. references and appendices)
parts = CM.build(img_info)
pages = json.load(open(os.path.join(ROOT, "report", "toc_pages.json"))) if os.path.exists(os.path.join(ROOT, "report", "toc_pages.json")) else {}
toc_head = ('<w:p><w:pPr><w:pageBreakBefore/><w:spacing w:before="120" w:after="160"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr>'
            '<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr><w:t>Contents</w:t></w:r></w:p>')
toc_xml = toc_head + L.toc_block(L.HEADINGS, pages)
tocfrag = etree.fromstring(f"<root {NSDECL}>" + toc_xml + "</root>")
for el in list(tocfrag): kids[31].addprevious(el)
frag = etree.fromstring(f"<root {NSDECL}>" + "".join(parts) + "</root>")
for el in list(frag): sect_final.addprevious(el)
json.dump(L.HEADINGS, open(os.path.join(ROOT, "report", "headings.json"), "w"))
tree.write(dp, xml_declaration=True, encoding="UTF-8", standalone=True)

# ---------------- zip
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(WORK, "[Content_Types].xml"), "[Content_Types].xml")
    for base, _, files in os.walk(WORK):
        for f in files:
            full = os.path.join(base, f); arc = os.path.relpath(full, WORK)
            if arc != "[Content_Types].xml": z.write(full, arc)
print("built", OUT, "| references:", len(L.CITES))

