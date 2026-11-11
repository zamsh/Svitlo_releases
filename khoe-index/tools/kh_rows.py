"""Table rows of Kharkivoblenergo's "Адреси та черги" document.

The table is [addresses | queue 1 (I, II) | … | queue 6 (I, II)]: an "X" in a column puts the row in
that sub-queue ("1 черга, ІІ" = 1.2). Input: text lines (pdflines.swift: {"p", "x", "y" from page top,
"w", "t"}) and horizontal rules (pdfrules.swift: {"p", "y", "x0", "x1"}). A row is the band between two
rules; a line belongs to the band holding its middle. PDFKit often glues a row's "X" to the end of its
last text line ("… Минківка с., X"); the X's x is then the line's right end.
A band without an X continues the row above (a cell split by a page break or an inner rule).
"""
import re

TEXT_RIGHT = 530     # the address column ends here; the sub-queue columns follow
LINE_MIDDLE = 4      # pdflines' y is the top of the line; the font is ~7–8 pt
X_WIDTH = 5


def columns(lines):
    """Centres of the 12 sub-queue columns from the header's "І ІІ" cells: [(x, "1.1"), (x, "1.2"), …]."""
    heads = sorted((l for l in lines if re.fullmatch(r"І\s*ІІ", l["t"])), key=lambda l: (l["p"], l["x"]))
    first = [l for l in heads if l["p"] == heads[0]["p"]][:6] if heads else []
    if len(first) != 6:
        raise ValueError(f"expected 6 queue headers, found {len(first)}")
    out = []
    for n, l in enumerate(first, 1):
        out += [(l["x"] + 3, f"{n}.1"), (l["x"] + l["w"] - 4, f"{n}.2")]
    return out


def bands(rules, page):
    ys = sorted(r["y"] for r in rules if r["p"] == page and r["x0"] < TEXT_RIGHT + 20 and r["x1"] > TEXT_RIGHT + 100)
    edges = []
    for y in ys:
        if not edges or y - edges[-1] > 2:
            edges.append(y)
    return list(zip(edges, edges[1:]))


def join(parts):
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def rows(lines, rules):
    cols = columns(lines)

    def queue(x):
        cx, q = min(cols, key=lambda c: abs(c[0] - x))
        return q if abs(cx - x) < 25 else None

    out = []
    for page in sorted({l["p"] for l in lines}):
        on_page = [l for l in lines if l["p"] == page]
        for top, bottom in bands(rules, page):
            inside = sorted((l for l in on_page if top <= l["y"] + LINE_MIDDLE < bottom), key=lambda l: (l["y"], l["x"]))
            queues, text = [], []
            for l in inside:
                t = l["t"]
                if t == "X":
                    queues.append(queue(l["x"] + X_WIDTH / 2)); continue
                if re.search(r"\sX$", t) and l["x"] + l["w"] > TEXT_RIGHT:
                    queues.append(queue(l["x"] + l["w"] - X_WIDTH / 2)); t = t[:-1]
                if l["x"] < TEXT_RIGHT:
                    text.append(t)
            queues = sorted({q for q in queues if q})
            body = join(text)
            if re.search(r"Графік погодинних|Назви населених пунктів|Величина відключаємого|^\s*\d черга", body) or \
               (not queues and not body):
                continue
            if not queues and out:
                out[-1]["text"] = join([out[-1]["text"], body]); continue
            out.append({"page": page, "q": queues, "text": body})
    return out
