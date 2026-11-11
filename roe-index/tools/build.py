"""Builds the address -> sub-queue index for Rivne region from Rivneoblenergo's two GPV documents
(city of Rivne and the rest of the region). Same index format as ../gpv-index (the apps share the
lookup); the row text parser is gpv-index's gpv_parse.

Usage:
  build.py --city-pdf CITY.pdf --region-pdf REGION.pdf --city-url URL --region-url URL --out DIR
           [--previous DIR/index.json] [--work TMP]
  build.py --work DIR --out DIR      (reuse lines/rules JSON already in DIR, e.g. in tests)

Exit code 1 means the result failed validation; the previous index must then be kept.
"""
import argparse, datetime, gzip, hashlib, json, os, re, subprocess, sys
from collections import Counter

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
sys.path.append(os.path.join(TOOLS, "..", "..", "gpv-index", "tools"))   # after ours: both have build.py, find_source.py
import roe_rows, gpv_parse

WHOLE = re.compile(r"[-–]?\s*\(?\s*повністю\s*\)?|\(?\s*всі\s+вулиці\s*\)?", re.I)
PARTIAL_WORD = re.compile(r"частково|частк\w*|чатково", re.I)


def junk_name(s):
    """Fragments and objects that are not settlement or street names (kept out of the index)."""
    return (s is None or len(s) < 3 or not re.match(r"^[А-ЯІЇЄҐ0-9]", s) or '"' in s or
            re.search(r"споживач|котельн|гараж|гуртож|свердловин|станці|кіоск|ввод|ввід|школ|лікарн|рада\b|філія|"
                      r"підприєм|агрохолдинг|ферм|склад|магазин|банк|кафе|ТОВ|ПП\b|ФГ\b|район\b|р-н|промзона|база", s, re.I))


# "с. Бабин -- Тиха, Заводська", "с.Горбаків - Шевченка", "С.Злазне: Цитень": the streets of that settlement.
SETTLEMENT_DASH = re.compile(r"((?:^|[\s,.;(])(?:[сС]|м|смт|с-ще)\.?\s*[А-ЯІЇЄҐ][А-ЯІЇЄҐа-яіїєґ'’ʼ]+(?:\s+[А-ЯІЇЄҐ][А-ЯІЇЄҐа-яіїєґ'’ʼ]+)?)"
                             r"\s*(?:-{1,2}\s+|–\s*|\s+[-–]\s*|:\s*)(?=[А-ЯІЇЄҐ])")
# "С.Хороброго" (Святослава Хороброго) is a street; a capital "С." starts a settlement only if one is named so.
CAPITAL_S = re.compile(r"(?<![А-ЯІЇЄҐа-яіїєґ])С\.\s*(?=[А-ЯІЇЄҐ])")


def clean(text, known=None):
    text = WHOLE.sub(" ", text)
    text = PARTIAL_WORD.sub(" частково ", text)
    if known is not None:
        def capital(m):
            word = re.match(r"[А-ЯІЇЄҐа-яіїєґ'’ʼ]+", text[m.end():])
            return m.group(0) if word and gpv_parse.norm(word.group(0)) in known else "С "
        text = CAPITAL_S.sub(capital, text)
    return SETTLEMENT_DASH.sub(r"\1 вул. ", text)


def settlement_list(cell):
    """Settlements column → [(name, partial)]: "с.Озірці (повністю), с.Рудня, частково с.Колодязне"."""
    out = []
    for e in gpv_parse.parse_row(clean(cell)):
        if e["street"] is None and e["settlement"] and not junk_name(e["settlement"]):
            out.append((e["settlement"], e["partial"]))
    return out


def entries_from_rows(rows):
    # Settlements the documents name in the settlements column (and the city): a "settlement" found only in a
    # street cell is a street the parser took for a settlement ("с.Бабин -- Тиха, Заводська").
    known = {"Рівне"} | {n for r in rows for n, _ in settlement_list(r["settlements"])}
    out = []
    for i, r in enumerate(rows):
        named = settlement_list(r["settlements"])
        whole = {n for n, partial in named if not partial}
        # Rows whose street cell names no settlement list streets of the row's only (or only partial) settlement.
        partial_ones = [n for n, p in named if p]
        default = named[0][0] if len(named) == 1 else (partial_ones[0] if len(partial_ones) == 1 else None)
        seen = set()
        for e in gpv_parse.parse_row(clean(r["text"], known)):
            s = e["settlement"] or default
            if s not in known:
                if e["street"] is None and default:
                    e = {**e, "street": s, "kind": ""}      # a street listed after the settlement
                s = default if e["street"] is not None else None
            if not s or junk_name(s) or (e["street"] is not None and junk_name(e["street"])):
                continue
            if e["street"] is None and s in seen:
                continue
            seen.add(s)
            out.append({"row": i, "settlement": s, "street": e["street"], "kind": e["kind"], "houses": e["houses"],
                        "partial": e["partial"] or (e["street"] is None and s not in whole)})
        # Every settlement of the settlements column is in this row's queue, whole or in part.
        for n, partial in named:
            if not any(x["row"] == i and x["settlement"] == n and x["street"] is None for x in out):
                has_streets = any(x["row"] == i and x["settlement"] == n for x in out)
                out.append({"row": i, "settlement": n, "street": None, "kind": "", "houses": None,
                            "partial": partial or has_streets})
    return out


def compact(rows, entries, meta):
    """App format: rows keep the source text (shown as evidence); entries reference rows by index."""
    used = sorted({e["row"] for e in entries}); remap = {r: i for i, r in enumerate(used)}

    def houses(items):
        if not items: return None
        return [x["n"] if "n" in x else [x["from"], x["to"]] + ([x["parity"]] if x.get("parity") else []) for x in items]

    def text(r):
        return r["text"] if r["settlements"] in ("", "м.Рівне") else f'{r["settlements"]}: {r["text"]}'

    return {
        "version": 1, "source": meta,
        "rows": [{"q": rows[r]["q"][0], "branch": rows[r]["hromada"] + " громада", "text": text(rows[r])} for r in used],
        # [settlement, street|null, kind, houses|null, partial 0/1, row]
        "entries": [[e["settlement"], e["street"], e["kind"], houses(e["houses"]), int(e["partial"]), remap[e["row"]]] for e in entries],
    }


def validate(city_rows, region_rows, entries, previous):
    problems, stats = [], {}
    rows = city_rows + region_rows
    stats["city_rows"] = len(city_rows); stats["region_rows"] = len(region_rows); stats["entries"] = len(entries)
    stats["rows_per_queue"] = dict(sorted(Counter(r["q"][0] for r in rows if r["q"]).items()))
    stats["rows_without_one_queue"] = sum(1 for r in rows if len(r["q"]) != 1)
    stats["settlements"] = len({e["settlement"] for e in entries})
    missing = [f"{q}.{s}" for q in range(1, 7) for s in (1, 2) if f"{q}.{s}" not in stats["rows_per_queue"]]
    if missing: problems.append(f"queues not found: {missing}")
    if stats["rows_without_one_queue"] > len(rows) // 50: problems.append(f'{stats["rows_without_one_queue"]} rows without exactly one queue')
    if len(city_rows) < 40: problems.append(f"only {len(city_rows)} rows in the city table")
    if len(region_rows) < 300: problems.append(f"only {len(region_rows)} rows in the region table")
    if not any(e["settlement"] == "Рівне" for e in entries): problems.append("no entries for Рівне")
    if previous and len(entries) < 0.8 * len(previous["entries"]):
        problems.append(f'entries dropped from {len(previous["entries"])} to {len(entries)}')
    return problems, stats


def extract(pdf, work, name):
    lines, rules = os.path.join(work, f"{name}-lines.json"), os.path.join(work, f"{name}-rules.json")
    subprocess.run(["swift", os.path.join(TOOLS, "pdflines.swift"), pdf, lines], check=True)
    subprocess.run(["swift", os.path.join(TOOLS, "pdfrules.swift"), pdf, rules], check=True)
    return lines, rules


def load_rows(work, name, kind):
    return [r for r in roe_rows.rows(json.load(open(os.path.join(work, f"{name}-lines.json"))),
                                     json.load(open(os.path.join(work, f"{name}-rules.json"))), kind) if r["q"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city-pdf"); ap.add_argument("--region-pdf")
    ap.add_argument("--city-url", default=""); ap.add_argument("--region-url", default="")
    ap.add_argument("--out", required=True); ap.add_argument("--previous"); ap.add_argument("--work")
    a = ap.parse_args()
    work = a.work or a.out
    os.makedirs(a.out, exist_ok=True); os.makedirs(work, exist_ok=True)
    sha = {}
    for name, pdf in (("city", a.city_pdf), ("region", a.region_pdf)):
        if pdf:
            sha[name] = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
            extract(pdf, work, name)
    city, region = load_rows(work, "city", "city"), load_rows(work, "region", "region")
    rows = city + region
    entries = entries_from_rows(rows)
    previous = json.load(open(a.previous)) if a.previous and os.path.exists(a.previous) else None
    problems, stats = validate(city, region, entries, previous)
    meta = {"url": a.region_url, "city_url": a.city_url, "sha256": sha.get("region"), "city_sha256": sha.get("city"),
            "valid_from": None, "valid_to": None,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()}
    report = {"meta": meta, "stats": stats, "problems": problems}
    json.dump(report, open(os.path.join(a.out, "report.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if problems:
        return 1
    data = json.dumps(compact(rows, entries, meta), ensure_ascii=False, separators=(",", ":")).encode()
    open(os.path.join(a.out, "index.json"), "wb").write(data)
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"index.json: {len(data) // 1024} KB ({len(gzip.compress(data)) // 1024} KB gzipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
