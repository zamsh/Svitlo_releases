"""Kharkivoblenergo's address cells → text gpv-index's gpv_parse reads.

Most cells name things marker-last: "Валківський р-н, Валки м., Харківська вул.; Гузівка с., Ков'яги смт.,
Центральна вул." Others are marker-first like the other operators: "м. Валки вул. Курячівська, с. Литвинівка".
Each marker is told apart by what follows it: a separator (or the end) makes it marker-last; a name makes it
marker-first, unless the cell is mostly marker-last ("Манили с. Мельникове с.," lists two villages).
Marker-last names are rewritten marker-first; districts ("Валківський р-н") are taken out and kept apart.
"""
import re

L = "А-ЯІЇЄҐа-яіїєґ'’ʼ`"
SETTLEMENT = r"смт|с-ще|сел|селище|с|м|(?-i:х|г|п)"   # "П.Мирного" is a street: х/г/п lowercase only
STREET = r"вул|ул|пров|пер|туп|в-д|в'їзд|в’їзд|пр-т|просп|пр|пл|м-н|мкр|бул|б-р|шосе|проїзд|узвіз|майдан"
MARK = re.compile(rf"(?<![{L}\-])({SETTLEMENT}|{STREET})(\.+|(?=[\s,;:]|$))", re.I)
SEP = re.compile(r"[,;:]")
DISTRICT = re.compile(rf"[А-ЯІЇЄҐ][{L}]+\s+(?:р-н|район)\b\.?\s*[,:]?", re.I)
NOISE = re.compile(r"[«\"“„][^»\"”]*[»\"”]?|\b(?:ТОВ|ПАТ|ПрАТ|ПраТ|ТДВ|ОДО|УОРА|ДП|КП|АТ|ФОП|ФГ|ПП)\b", re.I)


def districts(cell):
    return [re.sub(r"\s+", " ", re.sub(r"\s*(?:р-н|район)\b.*$", " р-н", m.group(0), flags=re.I)).strip()
            for m in DISTRICT.finditer(cell)]


# Spellings gpv_parse knows: "г." (Russian for town) → "м.", hamlets and "п." (settlement) → "с.".
CANON = {"г": "м", "п": "с", "х": "с", "сел": "с", "селище": "с", "ул": "вул", "пер": "пров", "в-д": "в'їзд", "в’їзд": "в'їзд"}


def is_settlement(mark):
    return re.fullmatch(SETTLEMENT, mark, re.I) is not None


def unglue(t):
    """Typing slips: "ШелудькІвка" (Latin-like capital І), "ЗміївАдминистративна", "Клейменівкас.Западня",
    "Закори.Енергетикі.Комунальна" (dots between names), Russian "частично"."""
    t = re.sub(r"(?<=[а-яіїєґ])([ІЇ])(?=[а-яіїєґ]|\b)", lambda m: m.group(1).lower(), t)
    t = re.sub(r"(?<=[а-яіїєґ]{3})с\.(?=\s*[А-ЯІЇЄҐ])", " с.", t)
    t = re.sub(r"(?<=[а-яіїєґ])(?=[А-ЯІЇЄҐ][а-яіїєґ]{3})", ": ", t)
    t = re.sub(rf"(?<![{L}])([А-ЯІЇЄҐ][{L}]{{3,}})\.(?=[А-ЯІЇЄҐ])", r"\1, ", t)
    t = re.sub(r"частично", "частково", t, flags=re.I)
    t = re.sub(r",\s*С\.\s*(?=[А-ЯІЇЄҐ])", ", ", t)            # "Шевченко,С.Закори": a street's initial
    t = re.sub(r"-(?=вул\.)", " - ", t)
    return re.sub(r"\bвулиці\b", "вул.", t, flags=re.I)


def normalize(cell):
    t = unglue(cell.replace("’", "'").replace("ʼ", "'").replace("`", "'"))
    t = DISTRICT.sub("; ", t)
    t = NOISE.sub(" ", t)
    t = re.sub(rf"(?<=[{L}.])(?=[А-ЯІЇЄҐ][{L}]+ськ\w*\s+р-н)", "; ", t)
    t = re.sub(r"\.{2,}", ".", t)
    t = re.sub(r":\s*\.", ":", t)
    marks = list(MARK.finditer(t))

    def after(m):
        rest = t[m.end():].lstrip()
        # "вул.: Дружби, …" introduces a list; "Введенка смт:" ends a settlement's name.
        if rest.startswith(":") and not is_settlement(m.group(1)):
            return "name"
        return "sep" if (not rest or SEP.match(rest) or rest[0] in ".)") else "name"

    kinds = [after(m) for m in marks]
    last_style = kinds.count("sep") >= max(1, kinds.count("name"))
    out, pos = [], 0
    for m, kind in zip(marks, kinds):
        mark = CANON.get(m.group(1).lower(), m.group(1).lower())
        chunk = t[pos:m.start()]
        cut = max(chunk.rfind(c) for c in ",;:")
        name = chunk[cut + 1:].strip(" .")
        if re.search(r"\s[-–]$|-$", name):
            name = ""
        # Marker-last: the name right before it, back to the last separator.
        if (kind == "sep" or last_style) and re.match(rf"^[А-ЯІЇЄҐ0-9][{L}0-9 .\-]*$", name) and not MARK.search(name):
            out.append(chunk[:cut + 1] + f" {mark}. {name}" + ("" if kind == "sep" else ","))
        else:
            out.append(chunk + f" {mark}. ")
        pos = m.end()
    out.append(t[pos:])
    s = "".join(out)
    # "с.Лиман:Садова,Станционна", "с.Лиман-вул.Андреївська", "с.Андріївка - вул. Центральна": that settlement's streets.
    s = re.sub(rf"((?:{SETTLEMENT})\.\s*[А-ЯІЇЄҐ][{L}.\-]*(?:\s+[А-ЯІЇЄҐ][{L}]+)?)\s*(?::|\s[-–]|-(?=вул))\s*(?!(?:{STREET})\.)(?=[А-ЯІЇЄҐ0-9])",
               r"\1 вул. ", s)
    s = re.sub(r"-\s*\.\s*(?=[А-ЯІЇЄҐ])", " - вул. ", s)                       # "с. Таранівка-.Харківська"
    s = re.sub(r"\s+", " ", s)
    # A town's bare names are its streets ("м. Люботин, Низовая, Ревчанская"); villages are listed bare too.
    s = re.sub(rf"(\bм\. [А-ЯІЇЄҐ][{L}\-]+)\s*,\s*(?=[А-ЯІЇЄҐ][{L}]+\s*[,;.])(?!(?:{SETTLEMENT}|{STREET})\.)", r"\1, вул. ", s)
    # "…, м. Шапошникова, О.Бринчука" in a street list: a square or a block named after a person, not a town.
    s = re.sub(rf"(?<=[,;] )м\. (?=[А-ЯІЇЄҐ][{L}]+(?:ого|ова|ева|єва|іна|ина)\b)", "пл. ", s)
    s = re.sub(r"\s*([,;:])\s*(?:[,;:]\s*)*", r"\1 ", s)      # ", ;" , ",," → one separator
    return s.strip(" ,;")
