"""Builds the address -> sub-queue index from the Poltavaoblenergo GPV PDF.

Usage:
  build.py --pdf HPV.pdf --source-url URL --out DIR [--previous DIR/index.json] [--work TMP]
  build.py --lines lines.json --out DIR          (skip PDF extraction, e.g. in tests)

PDF text is extracted by tools/pdflines.swift (PDFKit, macOS): other extractors return the text in
the wrong reading order for this document. Exit code 1 means the result failed validation; the
previous index must then be kept.
"""
import argparse, datetime, gzip, hashlib, json, os, re, subprocess, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import gpv_rows, gpv_parse

TOOLS = os.path.dirname(os.path.abspath(__file__))

# Main town of each branch: rows without an explicit settlement list streets of this town.
BRANCH_TOWN = {
    "Полтавська об'єднана": "Полтава", "Кременчуцька об'єднана": "Кременчук", "Лубенська об'єднана": "Лубни",
    "Миргородська об'єднана": "Миргород", "Горішньоплавнівська": "Горішні Плавні", "Великокохнівська": "Кременчук",
    "Гадяцька": "Гадяч", "Глобинська": "Глобине", "Гребінківська": "Гребінка", "Диканьканська": "Диканька",
    "Диканська": "Диканька", "Зіньківська": "Зіньків", "Карлівська": "Карлівка", "Кобеляцька": "Кобеляки",
    "Козельщинська": "Козельщина", "Котелевська": "Котельва", "Красногорівська": None, "Лохвицька": "Лохвиця",
    "Машівська": "Машівка", "Новосанжарська": "Нові Санжари", "Оржицька": "Оржиця", "Пирятинська": "Пирятин",
    "Полтавська дільниця РЕМ": None, "Решетилівська": "Решетилівка", "Семенівська": "Семенівка",
    "Хорольська": "Хорол", "Чорнухинська": "Чорнухи", "Чутівська": "Чутове", "Шишацька": "Шишаки",
}

def branch_town(branch):
    b = (branch or "").replace("’", "'")
    return next((v for k, v in BRANCH_TOWN.items() if b.startswith(k)), None)

def short_branch(branch):
    return re.sub(r"\s+(АТ|Кременчуцької|Полтавської|Лубенської|Миргородської).*$", "", (branch or "").replace("’", "'"))

def junk_name(s):
    """Fragments and objects that are not street names (kept out of the index)."""
    return (s is None or len(s) < 3 or not re.match(r"^[А-ЯІЇЄҐ0-9]", s) or '"' in s or
            re.search(r"споживач|котельн|гараж|гуртож|свердловин|станці|кіоск|ввод|ввід|школ|лікарн|рада\b|філія", s, re.I))

def entries_from_rows(rows):
    out = []
    for i, r in enumerate(rows):
        for e in gpv_parse.parse_row(r["text"]):
            if e["settlement"] is None:
                e["settlement"] = branch_town(r["branch"])
                if not e["settlement"]: continue
            if junk_name(e["settlement"]) or (e["street"] is not None and junk_name(e["street"])): continue
            out.append({"q": r["queue"], "branch": short_branch(r["branch"]), "settlement": e["settlement"],
                        "street": e["street"], "kind": e["kind"], "houses": e["houses"], "partial": e["partial"], "row": i})
    return out

def compact(rows, entries, meta):
    """App format: rows keep the source text (shown as evidence); entries reference rows by index."""
    used = sorted({e["row"] for e in entries}); remap = {r: i for i, r in enumerate(used)}
    def houses(items):
        if not items: return None
        return [x["n"] if "n" in x else [x["from"], x["to"]] + ([x["parity"]] if x.get("parity") else []) for x in items]
    return {
        "version": 1, "source": meta,
        "rows": [{"q": rows[r]["queue"], "branch": short_branch(rows[r]["branch"]), "text": rows[r]["text"]} for r in used],
        # [settlement, street|null, kind, houses|null, partial 0/1, row]
        "entries": [[e["settlement"], e["street"], e["kind"], houses(e["houses"]), int(e["partial"]), remap[e["row"]]] for e in entries],
    }

def validate(rows, entries, previous):
    problems, stats = [], {}
    queues = Counter(r["queue"] for r in rows)
    stats["rows"] = len(rows); stats["entries"] = len(entries); stats["rows_per_queue"] = dict(sorted(queues.items()))
    missing = [f"{q}.{s}" for q in range(1, 7) for s in (1, 2) if f"{q}.{s}" not in queues]
    if missing: problems.append(f"sections not found: {missing}")
    blocks = {}
    for r in rows: blocks.setdefault((r["queue"], r["branch"]), []).append(r["n"])
    broken = [k for k, ns in blocks.items() if ns[0] != 1 or any(b <= a for a, b in zip(ns, ns[1:]))]
    stats["blocks"] = len(blocks); stats["blocks_out_of_order"] = len(broken)
    if len(broken) > max(3, len(blocks) // 10): problems.append(f"{len(broken)} branch blocks have out-of-order numbering")
    if previous:
        p_rows, p_entries = len(previous["rows"]), len(previous["entries"])
        stats["previous_entries"] = p_entries
        if len(entries) < 0.8 * p_entries: problems.append(f"entries dropped from {p_entries} to {len(entries)}")
    if len(entries) < 2000: problems.append(f"only {len(entries)} entries")
    return problems, stats

def title_period(lines):
    head = " ".join(l["t"] for l in lines if l["p"] == 1 and l["y"] < 90)
    m = re.search(r"з\s*(\d\d\.\d\d\.\d{4})\D+по\s*(\d\d\.\d\d\.\d{4})", head)
    iso = lambda d: datetime.datetime.strptime(d, "%d.%m.%Y").date().isoformat()
    return (iso(m.group(1)), iso(m.group(2))) if m else (None, None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf"); ap.add_argument("--lines"); ap.add_argument("--source-url", default="")
    ap.add_argument("--out", required=True); ap.add_argument("--previous")
    ap.add_argument("--work", help="folder for intermediate files (default: --out)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sha = None
    if a.pdf:
        sha = hashlib.sha256(open(a.pdf, "rb").read()).hexdigest()
        os.makedirs(a.work or a.out, exist_ok=True)
        a.lines = os.path.join(a.work or a.out, "lines.json")
        subprocess.run(["swift", os.path.join(TOOLS, "pdflines.swift"), a.pdf, a.lines], check=True)
    lines = json.load(open(a.lines))
    rows = gpv_rows.rows(lines)
    entries = entries_from_rows(rows)
    previous = json.load(open(a.previous)) if a.previous and os.path.exists(a.previous) else None
    problems, stats = validate(rows, entries, previous)
    valid_from, valid_to = title_period(lines)
    meta = {"url": a.source_url, "sha256": sha, "valid_from": valid_from, "valid_to": valid_to,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()}
    report = {"meta": meta, "stats": stats, "problems": problems}
    json.dump(report, open(os.path.join(a.out, "report.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if problems:
        return 1
    idx = compact(rows, entries, meta)
    data = json.dumps(idx, ensure_ascii=False, separators=(",", ":")).encode()
    open(os.path.join(a.out, "index.json"), "wb").write(data)
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"index.json: {len(data) // 1024} KB ({len(gzip.compress(data)) // 1024} KB gzipped)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
