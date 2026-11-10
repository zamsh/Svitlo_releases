"""Address -> sub-queue lookup over the GPV index (reference implementation for the apps)."""
import re

KIND_WORDS = r"(вулиця|вул|провулок|пров|проспект|просп|пр-т|пр-к|п-к|пр|бульвар|бульв|бул|б-р|площа|пл|тупик|тупік|туп|узвіз|проїзд|шосе|мікрорайон|мкр|м-н|квартал|кварт|майдан|сквер)\.?"
SETTL_WORDS = r"(місто|м|село|с|селище|с-ще|смт|с\.м\.т)\.?"

def base(s):
    s = (s or "").lower().replace("’", "'").replace("`", "'").replace("ʼ", "'").replace("ё", "е")
    s = re.sub(r"[\"«»()]", " ", s)
    return re.sub(r"\s+", " ", s).strip(" .,-")

def norm_settlement(s):
    s = base(s)
    s = re.sub(rf"^{SETTL_WORDS}\s*", "", s)
    return re.sub(r"\.\s*", ". ", s).strip()

def norm_street(s):
    s = base(s)
    s = re.sub(rf"^{KIND_WORDS}\s*", "", s)
    s = re.sub(r"\bімені\b|\bім\.\s*", "", s)
    return re.sub(r"\.\s*", ". ", s).strip()

def lev(a, b):
    if abs(len(a) - len(b)) > 2: return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def name_matches(doc, query):
    """'в. рублівка' ~ 'велика рублівка'; 'решитилівська' ~ 'решетилівська'; word order must match."""
    if doc == query: return True
    dt, qt = doc.split(), query.split()
    if len(dt) == len(qt) and all(d == q or (d.endswith(".") and q.startswith(d[:-1])) or
                                  (len(d) > 6 and d[-2:] == q[-2:] and lev(d, q) <= (1 if len(d) < 10 else 2)) for d, q in zip(dt, qt)):
        return True
    # the document often drops first names: 'тютюнника' ~ 'василя тютюнника'
    if len(dt) < len(qt) and dt == qt[-len(dt):] and len(dt[-1]) > 5: return True
    return False

def parse_house(h):
    m = re.match(r"^\s*(\d+)\s*([а-яіїєґ]?)\s*(?:/\s*(\S+))?", base(h))
    return (int(m.group(1)), m.group(2), m.group(3)) if m else None

def house_matches(item, house):
    num, letter, frac = house
    if "n" in item:
        hn = parse_house(item["n"])
        return hn is not None and hn[0] == num and hn[1] == letter and (hn[2] is None or hn[2] == frac)
    if not (item["from"] <= num <= item["to"]): return False
    p = item.get("parity")
    return p is None or (p == "odd") == (num % 2 == 1)

LEVELS = ["house", "range", "street", "settlement"]

KIND_GROUP = {"вулиця": "вул", "вул": "вул", "провулок": "пров", "пров": "пров", "п-к": "пров", "пр-к": "пров",
              "проспект": "просп", "просп": "просп", "пр-т": "просп", "бульвар": "бул", "бульв": "бул", "бул": "бул", "б-р": "бул",
              "площа": "пл", "пл": "пл", "тупик": "туп", "тупік": "туп", "туп": "туп", "узвіз": "узвіз"}

def kind_of(s):
    m = re.match(rf"^{KIND_WORDS}", base(s or ""))
    return KIND_GROUP.get(m.group(1)) if m else None

def lookup(index, settlement, street=None, house=None):
    """Returns {"queues": [...], "level": ..., "matches": [...]} for the most specific level found."""
    q_kind = kind_of(street)
    s_q, st_q, h_q = norm_settlement(settlement), norm_street(street) if street else None, parse_house(house) if house else None
    found = {lvl: [] for lvl in LEVELS}
    for e in index:
        if not name_matches(norm_settlement(e["settlement"]), s_q): continue
        if e["street"] is None:
            found["settlement"].append(e); continue
        if not st_q or not name_matches(norm_street(e["street"]), st_q): continue
        d_kind = KIND_GROUP.get(e["kind"])
        if q_kind and d_kind and q_kind != d_kind: continue
        if not e["houses"]:
            found["street"].append(e); continue
        if h_q:
            for item in e["houses"]:
                if house_matches(item, h_q):
                    found["house" if "n" in item else "range"].append(e); break
    for lvl in LEVELS:
        if found[lvl]:
            return {"queues": sorted({e["q"] for e in found[lvl]}), "level": lvl, "matches": found[lvl]}
    return {"queues": [], "level": None, "matches": []}
