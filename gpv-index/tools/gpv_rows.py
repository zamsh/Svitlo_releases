"""Rebuilds GPV table rows (queue, branch, row number, text) from PDF text lines with coordinates.

Layout of the document: the row number sits in a narrow left column (x < 30), wrapped text in the
wide column (x ~ 35), queue and branch headers are centred (x > 100). Lines of one table cell are
closer than GAP points; long cells have their number vertically centred, so cells are clustered by gap.
"""
import re, sys, json
from collections import Counter

ORD = {"Перша": 1, "Друга": 2, "Третя": 3, "Четверта": 4, "П'ята": 5, "П’ята": 5, "Шоста": 6}
SECTION = re.compile(r"(Перша|Друга|Третя|Четверта|П['’]ята|Шоста) черга (ІІ|І|II|I) підчерга")
NUMBER = re.compile(r"^(\d{1,3})(?:\s+(.*))?$")
GAP = 13  # points: lines closer than this belong to one table cell

def rows(lines):
    by_page = {}
    for l in lines: by_page.setdefault(l["p"], []).append(l)
    queue = branch = None
    out, cur = [], None
    for p in sorted(by_page):
        ls = sorted(by_page[p], key=lambda l: (l["y"], l["x"]))
        cell, last_y = [], None
        def close_cell():
            nonlocal cur
            if not cell: return
            num_line = next((c for c in cell if c["x"] < 30 and NUMBER.match(c["t"])), None)
            texts = []
            for c in cell:
                if c is num_line:
                    rest = NUMBER.match(c["t"]).group(2)
                    if rest: texts.append(rest)
                else:
                    texts.append(c["t"])
            text = " ".join(texts).strip()
            if num_line:
                if cur: out.append(cur)
                cur = {"queue": queue, "branch": branch, "n": int(NUMBER.match(num_line["t"]).group(1)), "page": p, "text": text}
            elif cur and text:            # cell continued from the previous page
                cur["text"] += " " + text
            cell.clear()
        for l in ls:
            t = l["t"]
            if re.fullmatch(r"\d{1,3}", t) and int(t) == p and l["x"] > 300: continue   # page number
            if l["x"] > 100 and l["y"] > 0:                                              # centred header
                close_cell()
                m = SECTION.search(t)
                if m:
                    if cur: out.append(cur); cur = None
                    queue = f"{ORD[m.group(1)]}.{2 if m.group(2) in ('ІІ', 'II') else 1}"
                elif re.search(r"дільниця|філія", t):
                    if cur: out.append(cur); cur = None
                    branch = t
                last_y = None
                continue
            if t.startswith("Графік погодинного") or re.fullmatch(r"\S+ черга", t): continue
            m = NUMBER.match(t) if l["x"] < 30 else None
            cell_nums = [int(NUMBER.match(c["t"]).group(1)) for c in cell if c["x"] < 30 and NUMBER.match(c["t"])]
            starts_row = bool(m and cell_nums and int(m.group(1)) == cell_nums[-1] + 1)
            if starts_row or (last_y is not None and l["y"] - last_y > GAP): close_cell()
            cell.append(l); last_y = l["y"]
        close_cell()
    if cur: out.append(cur)
    return out

if __name__ == "__main__":
    rs = rows(json.load(open(sys.argv[1])))
    json.dump(rs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print(len(rs), sorted(Counter(r["queue"] for r in rs).items()))
    # sanity: numbering inside each (queue, branch) block should be 1..N
    blocks, bad = {}, []
    for r in rs: blocks.setdefault((r["queue"], r["branch"]), []).append(r["n"])
    for k, ns in blocks.items():
        if ns != list(range(1, len(ns) + 1)): bad.append((k, ns))
    print("blocks:", len(blocks), "with broken numbering:", len(bad))
    for k, ns in bad[:12]: print(" ", k, ns)
