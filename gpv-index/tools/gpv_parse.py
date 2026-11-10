"""Turns GPV row text into structured address entries.

A row is free text such as
  "м.Горішні плавні: вул.Миру 9, 11, 15А; Молодіжна 18, 20, 21/6; пров.Молодіжний 2-12"
  "с.Чечужино, Новоселівка, Друга Олександрівка"
  "с.Сагайдак частково вул.: Генерала Пащенка (буд.37-130), Дружби (буд.3-28)"
The text is scanned left to right. A settlement marker (м./с./с-ще/смт) starts a settlement list:
comma-separated bare names after it are more settlements, until a street marker or a house number
appears. From then on bare names are streets of the last settlement.
"""
import re

LET = "А-ЯІЇЄҐа-яіїєґ'’`ʼ"
SETTLEMENT_MARK = re.compile(r"(?<![А-ЯІЇЄҐа-яіїєґ])(?:м\.|м\s|с\.м\.т\.?|смт\.?|с-ще|сел\.|селище|с\.|c\.|с\s|село\s)\s*", re.I)
STREET_MARK = re.compile(r"(?<![А-ЯІЇЄҐа-яіїєґ'])((?:вулиця|провулок|проспект|бульвар|площа|тупик|тупік|узвіз|проїзд|в'їзд|шосе|мікрорайон|квартал|майдан|сквер)(?![А-ЯІЇЄҐа-яіїєґ'])|"
                         r"(?:вул|пров|просп|пр-т|пр-к|п-к|пр|бульв|бул|б-р|пл|туп|мкр|м-н|кварт)(?:\.|(?![А-ЯІЇЄҐа-яіїєґ'])))\s*:?\s*", re.I)
HOUSE_TOKEN = re.compile(r"(?:№\s*|буд\.?\s*|б\.\s*)?(\d{1,4})\s*([а-яіїєґ])?(?:\s*/\s*(\d{1,4}[а-яіїєґ]?))?(?:\s*[-–]\s*(\d{1,4})\s*([а-яіїєґ])?(?:/\d+)?)?", re.I)
PARITY = re.compile(r"\(?\s*(не)?парн[іиа]\w*\s*\)?", re.I)
NOISE = re.compile(r"[«\"“„][^»\"”]*[»\"”]|\bТОВ\b|\bПАТ\b|\bПрАТ\b|\bФОП\b|\bКП\b|\bАТ\b|юридичн\w* споживач\w*|побутов\w* споживач\w*|Абонентські ТП.*$|ТП-\d+\w*", re.I)
SKIP_NAME = re.compile(r"^(та|і|й|частково|буд|корп|к|кв|вул|пров|№|ввід|школа|д/с|дитсадок|гуртожиток)$", re.I)

def norm(s):
    s = re.sub(r"\s+(буд|б|№|корп|кв)\.?$", "", s.strip(), flags=re.I)
    s = re.sub(r"\s+з\s+пров\w*$", "", s, flags=re.I)                     # 'Короленка з провулками' -> 'Короленка'

    s = s.replace("’", "'").replace("`", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", s).strip(" .,-–:;()")

def parse_houses(text):
    """'1, 3, 5-9(непарні), 21/6, 15А' -> list of {"n":..} or {"from":..,"to":..,"parity":..}."""
    items = []
    parity_all = None
    pm = PARITY.search(text)
    if pm: parity_all = "odd" if pm.group(1) else "even"
    text = re.sub(r"\s*(корпус|корп\.?|к\.)\s*\d+[а-яіїєґ]?", "", text, flags=re.I)
    for m in HOUSE_TOKEN.finditer(PARITY.sub(" ", text)):
        a, a_letter, frac, b, b_letter = m.groups()
        if b and not frac:
            lo, hi = int(a), int(b)
            if hi < lo: continue
            items.append({"from": int(a), "to": int(b), **({"parity": parity_all} if parity_all else {})})
        else:
            items.append({"n": f"{a}{(a_letter or '').lower()}" + (f"/{frac.lower()}" if frac else "")})
    return items

def split_name_houses(seg):
    """'Молодіжна 18, 20' -> ('Молодіжна', '18, 20'); 'Генерала Пащенка (буд.37-130)' -> ('Генерала Пащенка', 'буд.37-130')."""
    seg = seg.strip()
    m = re.match(rf"^([{LET}][{LET}\.\- ]*?[{LET}\.])\s*[-–,]?\s*\(?((?:№|буд|б\.)?\s*\d.*)$", seg)
    if m: return norm(m.group(1)), m.group(2)
    if re.match(rf"^[{LET}]", seg) and not re.search(r"\d", seg): return norm(seg), None
    if re.match(r"^(№|буд)?\s*\d", seg): return None, seg
    return norm(re.sub(r"\d.*$", "", seg)) or None, (re.search(r"\d.*$", seg) or [None])[0]

def parse_row(text):
    """Returns entries {settlement, street, kind, houses, partial}. settlement may be None (branch default)."""
    text = NOISE.sub(" ", text)
    entries = []
    settlement = None
    mode = "streets"              # what bare names mean right now (rows start with streets of the branch town)
    pending_settlements = []      # settlements in the current list that got no streets
    street_kind = ""
    partial = False
    last_street = None

    def flush_settlements():
        for s in pending_settlements:
            entries.append({"settlement": s, "street": None, "kind": "", "houses": None, "partial": partial})
        pending_settlements.clear()

    # Tokenise by settlement / street markers and separators, keeping the markers.
    pos = 0
    text = re.sub(r"\(\s*((?:не)?парн[іиа]\w*)\s*\)", r" \1", text, flags=re.I)        # keep parity with its list
    text = re.sub(r"(?<=\d)\s*,\s*(?=(?:не)?парн)", " ", text, flags=re.I)
    tokens = re.split(rf"({SETTLEMENT_MARK.pattern}|{STREET_MARK.pattern}|[;:,](?!\d{{3}})|\.(?=\s|$)|\s+та\s+)", text, flags=re.I)
    for tok in tokens:
        if tok is None: continue
        t = tok.strip()
        if not t: continue
        if SETTLEMENT_MARK.fullmatch(tok) or SETTLEMENT_MARK.fullmatch(t + " "):
            flush_settlements(); mode = "settlements"; last_street = None; partial = False; continue
        if STREET_MARK.fullmatch(tok) or STREET_MARK.fullmatch(t + " ") or STREET_MARK.fullmatch(t):
            if pending_settlements:
                settlement = pending_settlements.pop()   # streets belong to the last named settlement
                flush_settlements()
            street_kind = re.sub(r"[.:\s]", "", t).lower(); mode = "streets"; continue
        if t == ";" and mode == "settlements":
            if pending_settlements: settlement = pending_settlements[-1]
            mode = "streets"; continue
        if t in ";:,.()" or re.fullmatch(r"(та|і)", t): continue
        if re.fullmatch(r"частково", t, re.I): partial = True; continue
        t = re.sub(r"[()]", " ", t).strip()
        t = re.sub(r"^(?:[А-ЯІЇЄҐ]{2,}\b\s*)+", "", t).strip()                         # abbreviations: ПНС, ФКНС, ВУВКГ
        if not t: continue
        name, houses = split_name_houses(t)
        if name and SKIP_NAME.match(name): name = None
        if name and re.search(r"частково", name, re.I):
            partial = True; name = norm(re.sub(r"частково", "", name, flags=re.I)) or None
        if mode == "settlements" and name:
            name = norm(re.split(r"[\"«»“”(]", name)[0]) or None      # 'Горішні Плавні" АБК' -> 'Горішні Плавні'
            if not name: continue
        if mode == "settlements" and name and not houses:
            pending_settlements.append(name); settlement = name; continue
        if mode == "settlements" and name and houses:
            # "с.Розпашне вул.Сонячна" handled by STREET_MARK; here "Молодіжна 18" right after a settlement
            if pending_settlements:
                settlement = pending_settlements.pop(); flush_settlements()
            mode = "streets"
        if name:
            last_street = name
            entries.append({"settlement": settlement, "street": name, "kind": street_kind, "houses": parse_houses(houses) if houses else None, "partial": partial})
        elif houses and last_street:
            # continuation of the previous street's house list (split by a comma)
            prev = entries[-1]
            if prev["street"] == last_street:
                prev["houses"] = (prev["houses"] or []) + parse_houses(houses)
    flush_settlements()
    for e in entries:
        if e["settlement"]: e["settlement"] = norm(e["settlement"])
    return entries
