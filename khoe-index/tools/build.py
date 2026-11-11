"""Builds the address -> sub-queue index for Kharkiv region from Kharkivoblenergo's "Адреси та черги" PDF.
Same index format as ../gpv-index (the apps share the lookup); the row text parser is gpv-index's gpv_parse,
fed with kh_text's marker-first rewrite of the cells.

Usage:
  build.py --pdf DOC.pdf --url URL --out DIR [--previous DIR/index.json] [--work TMP]
  build.py --work DIR --out DIR      (reuse lines/rules JSON already in DIR, e.g. in tests)

Exit code 1 means the result failed validation; the previous index must then be kept.
"""
import argparse, datetime, gzip, hashlib, json, os, re, subprocess, sys
from collections import Counter

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
sys.path.append(os.path.join(TOOLS, "..", "..", "gpv-index", "tools"))   # after ours: both have build.py, find_source.py
import kh_rows, kh_text, gpv_parse


def junk_name(s):
    """Fragments and objects that are not settlement or street names (kept out of the index)."""
    return (s is None or len(s) < 3 or not re.match(r"^[А-ЯІЇЄҐ0-9]", s) or '"' in s or
            re.search(r"споживач|котельн|гараж|гуртож|свердловин|станці|кіоск|ввод|ввід|школ|лікарн|рада\b|філія|"
                      r"підприєм|агрохолдинг|ферм|склад|магазин|банк|кафе|ТОВ|ПП\b|ФГ\b|район\b|р-н|промзона|база|"
                      r"адміністрац|водозаб|агрофі?и?рм|\bмрн\b|завод\b|з-д\b|комбінат\b|фабрик[аи]\b|елеватор\b|насосна\b|тубдиспансер|інститут\b|ТРЦ|\bСШ\b|\bУКК\b|в/ч", s, re.I))


MARKER_FIRST = re.compile(rf"(?<![А-ЯІЇЄҐа-яіїєґ])(?:м\.|с\.|смт\.|с-ще\.)", re.I)


def merge_continuations(rows):
    """An inner rule splits a cell into bands each with its own X ("смт Солоницівка: вул. Зоряна, … /
    пров. Чкалова, вул. Річна, …"): a band of the same sub-queue that names no settlement continues the one above."""
    out = []
    for r in rows:
        r = {**r, "norm": kh_text.normalize(r["text"])}
        if not r["norm"]:
            continue
        if out and out[-1]["q"] == r["q"] and not MARKER_FIRST.search(r["norm"]) and \
                (re.match(r"^(?:вул|пров|в'їзд|туп|пр|пл|[а-яіїєґ0-9])", r["norm"]) or re.search(r"(?:[,;\-]|\b(?:вул|пров)\.)\s*$", out[-1]["text"])):
            prev = out[-1]
            prev["text"] = f'{prev["text"]} {r["text"]}'; prev["norm"] = f'{prev["norm"]}, {r["norm"]}'
            continue
        out.append(r)
    return out


def settlement_name(s):
    """"Рогань ХАРКІВГАЗ", "Липчанівка ПТФ", "Ізюм —" → the name alone."""
    s = re.sub(r"\s+(?:[А-ЯІЇЄҐ]{2,}\b.*|[—–-]+)$", "", s).strip()
    s = re.sub(r"\s+\S+\s+с/р$|\s+с/р$", "", s).strip()
    return gpv_parse.norm(s) or None


def entries_from_rows(rows):
    out = []
    for i, r in enumerate(rows):
        seen = set()
        for e in gpv_parse.parse_row(r["norm"]):
            s = settlement_name(e["settlement"]) if e["settlement"] else None
            if not s or junk_name(s) or (e["street"] is not None and junk_name(e["street"])):
                continue
            if e["street"] is None:
                if s in seen:
                    continue
                seen.add(s)
            out.append({"row": i, "settlement": s, "street": e["street"], "kind": e["kind"], "houses": e["houses"],
                        "partial": e["partial"]})
        # A settlement listed with some of its streets is in this sub-queue only in part.
        streets_of = {e["settlement"] for e in out if e["row"] == i and e["street"] is not None}
        for e in out:
            if e["row"] == i and e["street"] is None and e["settlement"] in streets_of:
                e["partial"] = True
        # …and one named only through its streets gets a partial whole-settlement entry too.
        for s in sorted(streets_of - {e["settlement"] for e in out if e["row"] == i and e["street"] is None}):
            out.append({"row": i, "settlement": s, "street": None, "kind": "", "houses": None, "partial": True})
    return out


BRANCH = "Харківська область"


def compact(rows, entries, meta):
    """App format: rows keep the source text (shown as evidence); entries reference rows by index."""
    used = sorted({e["row"] for e in entries}); remap = {r: i for i, r in enumerate(used)}

    def houses(items):
        if not items: return None
        return [x["n"] if "n" in x else [x["from"], x["to"]] + ([x["parity"]] if x.get("parity") else []) for x in items]

    return {
        "version": 1, "source": meta,
        # The districts in the cells are the pre-2020 ones and can't be tied to each settlement: one branch for all
        # (the apps group the settlement picker by branch); the row text keeps the district as evidence.
        "rows": [{"q": rows[r]["q"][0], "branch": BRANCH, "text": rows[r]["text"]} for r in used],
        # [settlement, street|null, kind, houses|null, partial 0/1, row]
        "entries": [[e["settlement"], e["street"], e["kind"], houses(e["houses"]), int(e["partial"]), remap[e["row"]]] for e in entries],
    }


def validate(rows, entries, previous):
    problems, stats = [], {}
    stats["rows"] = len(rows); stats["entries"] = len(entries)
    stats["rows_per_queue"] = dict(sorted(Counter(r["q"][0] for r in rows if r["q"]).items()))
    stats["rows_without_one_queue"] = sum(1 for r in rows if len(r["q"]) != 1)
    stats["settlements"] = len({e["settlement"] for e in entries})
    missing = [f"{q}.{s}" for q in range(1, 7) for s in (1, 2) if f"{q}.{s}" not in stats["rows_per_queue"]]
    if missing: problems.append(f"queues not found: {missing}")
    if stats["rows_without_one_queue"] > len(rows) // 50: problems.append(f'{stats["rows_without_one_queue"]} rows without exactly one queue')
    if len(rows) < 250: problems.append(f"only {len(rows)} rows")
    if stats["settlements"] < 300: problems.append(f'only {stats["settlements"]} settlements')
    if previous and len(entries) < 0.8 * len(previous["entries"]):
        problems.append(f'entries dropped from {len(previous["entries"])} to {len(entries)}')
    return problems, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf"); ap.add_argument("--url", default="")
    ap.add_argument("--out", required=True); ap.add_argument("--previous"); ap.add_argument("--work")
    a = ap.parse_args()
    work = a.work or a.out
    os.makedirs(a.out, exist_ok=True); os.makedirs(work, exist_ok=True)
    lines, rules = os.path.join(work, "lines.json"), os.path.join(work, "rules.json")
    sha = None
    if a.pdf:
        sha = hashlib.sha256(open(a.pdf, "rb").read()).hexdigest()
        subprocess.run(["swift", os.path.join(TOOLS, "pdflines.swift"), a.pdf, lines], check=True)
        subprocess.run(["swift", os.path.join(TOOLS, "pdfrules.swift"), a.pdf, rules], check=True)
    raw = [r for r in kh_rows.rows(json.load(open(lines)), json.load(open(rules))) if r["q"]]
    rows = merge_continuations(raw)
    entries = entries_from_rows(rows)
    previous = json.load(open(a.previous)) if a.previous and os.path.exists(a.previous) else None
    problems, stats = validate(rows, entries, previous)
    meta = {"url": a.url, "sha256": sha, "valid_from": None, "valid_to": None,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()}
    m = re.search(r"з (\d\d)\.(\d\d)\.(\d{4}) року по (\d\d)\.(\d\d)\.(\d{4})", " ".join(l["t"] for l in json.load(open(lines))[:5]))
    if m:
        meta["valid_from"] = f"{m[3]}-{m[2]}-{m[1]}"; meta["valid_to"] = f"{m[6]}-{m[5]}-{m[4]}"
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
