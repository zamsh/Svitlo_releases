"""Table rows of the two Rivneoblenergo GPV documents.

Input: text lines (pdflines.swift: {"p", "x", "y" from page top, "w", "t"}) and horizontal table rules
(pdfrules.swift: {"p", "y", "x0", "x1"}). A row is the band between two rules that cross the queue
column; a line belongs to the band holding its middle. Columns are told apart by x:
  city   (GPV_cherga_misto_Rivne):      [№ + streets and houses | sub-queue "1,1"]
  region (GPV_cherga_Rivnenska_oblast): [hromada | settlements | streets and houses | queue "1.1"]
A band without a queue continues the row above it (a cell split by a page break or an inner rule).
"""
import re

QUEUE = re.compile(r"^([1-6])[.,]([12])$")
TRAILING_QUEUE = re.compile(r"\s+([1-6])[.,]([12])\s*$")
LAYOUT = {"city": {"queue_x": 487}, "region": {"queue_x": 788, "hromada_x": 140, "streets_x": 345}}
LINE_MIDDLE = 4      # pdflines' y is the top of the line; the font is ~8–9 pt


def bands(rules, page, qx):
    ys = sorted(r["y"] for r in rules if r["p"] == page and r["x0"] < qx - 2 and r["x1"] > qx + 8)
    edges = []
    for y in ys:
        if not edges or y - edges[-1] > 3:
            edges.append(y)
    return list(zip(edges, edges[1:]))


def join(parts):
    """Lines of one cell → one string. A word broken at the line end ("Хмельницьког" + "о") keeps no space."""
    s = ""
    for p in parts:
        # A short lowercase start that isn't an abbreviation ("м.", "с.") is the end of the previous word.
        tail = re.match(r"[а-яіїєґ'’]+(?!\.)(?=[\s,;.)]|$)", p)
        glued = s.endswith(("-", "(", "/")) or (s[-1:].isalpha() and tail is not None and len(tail.group(0)) <= 2)
        s = s + p if glued else (s + " " + p if s else p)
    return re.sub(r"\s+", " ", s).strip()


def is_header(r):
    t = " ".join(r.get(k, "") for k in ("hromada", "settlements", "text"))
    return bool(re.search(r"^ст\.\d+ з \d+$|Графік погодинного|Назва територіальної|Назви вулиць|№ п/п", t.strip()))


def rows(lines, rules, kind):
    lay = LAYOUT[kind]
    qx = lay["queue_x"]
    out = []
    for page in sorted({l["p"] for l in lines}):
        on_page = [l for l in lines if l["p"] == page]
        for top, bottom in bands(rules, page, qx):
            inside = sorted((l for l in on_page if top <= l["y"] + LINE_MIDDLE < bottom), key=lambda l: (l["y"], l["x"]))
            queues = [QUEUE.sub(r"\1.\2", l["t"]) for l in inside if l["x"] >= qx - 15 and QUEUE.match(l["t"])]
            text = [l for l in inside if not (l["x"] >= qx - 15 and QUEUE.match(l["t"]))]
            if kind == "city":
                r = {"hromada": "Рівненська", "settlements": "м.Рівне", "text": join(l["t"] for l in text)}
                r["text"] = re.sub(r"^\d{1,3}\s+", "", r["text"])            # the row number
            else:
                r = {"hromada": join(l["t"] for l in text if l["x"] < lay["hromada_x"]),
                     "settlements": join(l["t"] for l in text if lay["hromada_x"] <= l["x"] < lay["streets_x"]),
                     "text": join(l["t"] for l in text if lay["streets_x"] <= l["x"] < qx - 15)}
            if not queues:
                # "…сокооцтовий з-д. 5.2": the queue ran into the text cell.
                m = TRAILING_QUEUE.search(r["text"])
                if m:
                    queues = [f"{m.group(1)}.{m.group(2)}"]
                    r["text"] = r["text"][:m.start()].strip()
            r = {"page": page, "q": queues, **r}
            if is_header(r) or not (queues or r["text"] or r["settlements"]):
                continue
            if not queues and out:
                prev = out[-1]
                for k in ("settlements", "text"):
                    prev[k] = join([prev[k], r[k]]) if r[k] else prev[k]
                continue
            out.append(r)
    return out
