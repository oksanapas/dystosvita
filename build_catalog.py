# Збирає catalog.json:
#  1) з усіх .html у репозиторії, де в <head> є <meta name="klas"> і <meta name="tema">
#  2) з файлу links.csv (зовнішні посилання: адреса,клас,тема,назва)
import csv, html, json, os, re

SKIP_DIRS = {".git", ".github", "node_modules"}

def meta(text, name):
    m = re.search(r'<meta\b[^>]*\bname=["\']%s["\'][^>]*>' % name, text, re.I)
    if not m:
        return None
    c = re.search(r'\bcontent=["\']([^"\']*)["\']', m.group(0), re.I)
    return html.unescape(c.group(1)).strip() if c else None

def parse_grades(s):
    """'6' -> [6]; '5,6' -> [5, 6]; '5-7' -> [5, 6, 7]"""
    out = set()
    for part in re.split(r"[,;\s]+", s or ""):
        r = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", part)
        if r:
            out.update(range(int(r.group(1)), int(r.group(2)) + 1))
        elif part.isdigit():
            out.add(int(part))
    return sorted(out)

items = []

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.lower().endswith(".html"):
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, ".").replace(os.sep, "/")
        if rel == "index.html":
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        klas, tema = meta(text, "klas"), meta(text, "tema")
        if not klas:
            continue  # без позначки класу — не потрапляє в каталог
        t = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        nazva = html.unescape(t.group(1)).strip() if t else f[:-5]
        items.append({"url": rel, "klas": parse_grades(klas), "tema": tema or "", "nazva": nazva})

if os.path.exists("links.csv"):
    with open("links.csv", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            url = (row.get("адреса") or "").strip()
            if not url:
                continue
            tema = (row.get("тема") or "").strip()
            items.append({
                "url": url,
                "klas": parse_grades(row.get("клас")),
                "tema": tema,
                "nazva": (row.get("назва") or "").strip() or tema or url,
            })

items = [i for i in items if i["klas"]]
items.sort(key=lambda i: (i["klas"][0], i["tema"].lower(), i["nazva"].lower()))

with open("catalog.json", "w", encoding="utf-8") as fh:
    json.dump(items, fh, ensure_ascii=False, indent=1)

print(f"У каталозі: {len(items)}")
