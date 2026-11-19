import json, os, re, subprocess, sys
ROOT = os.path.abspath(os.path.dirname(__file__)); W = "/home/claude/render_tmp"
os.makedirs(W, exist_ok=True)
subprocess.run(["cp", os.path.join(ROOT, "Final_Report_Green_Cloud.docx"), os.path.join(W, "r.docx")], check=True)
subprocess.run(["python3", "/mnt/skills/public/docx/scripts/office/soffice.py", "--headless", "--convert-to", "pdf", "--outdir", W, os.path.join(W, "r.docx")], capture_output=True)
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", os.path.join(W, "r.pdf")], capture_output=True, text=True).stdout).group(1))
pages = []
for p in range(1, n + 1):
    t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", os.path.join(W, "r.pdf"), "-"], capture_output=True, text=True).stdout
    pages.append(re.sub(r"\s+", " ", t))
intro = next(i for i, t in enumerate(pages) if "Data centres have become" in t)       # 0-based pdf page of the Introduction
heads = json.load(open(os.path.join(ROOT, "headings.json")))
res, cur = {}, intro
for lvl, txt in heads:
    key = txt
    found = None
    for i in range(cur, n):
        if (" " + txt + " ") in (" " + pages[i] + " "):
            found = i; break
    if found is None:
        print("NOT FOUND:", txt); continue
    cur = found; res[txt] = str(found - intro + 1)
json.dump(res, open(os.path.join(ROOT, "toc_pages.json"), "w"), indent=1)
print("pdf pages:", n, "| intro on pdf page", intro + 1, "| last body page number", n - intro, "| headings found", len(res), "of", len(heads))
