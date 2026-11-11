"""Row and index tests against Kharkivoblenergo's "Адреси та черги 26-27.pdf" (published 2026-10-07;
fixture = pages 1, 2, 5 and 9). Every expected sub-queue below was checked by hand against the PDF.
Run: python3 -m unittest discover -s khoe-index/tests
"""
import json, os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpv-index", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))      # before gpv-index: both have a build.py
import kh_rows, kh_text, build, gpv_lookup, gpv_parse, find_source

with open(os.path.join(HERE, "fixtures", "khoe-2026-10.json"), encoding="utf-8") as f:
    FIXTURE = json.load(f)


def all_rows():
    return build.merge_continuations([r for r in kh_rows.rows(FIXTURE["lines"], FIXTURE["rules"]) if r["q"]])


def lookup(settlement, street=None, house=None):
    rows = all_rows()
    entries = build.entries_from_rows(rows)
    for e in entries:
        e["q"] = rows[e["row"]]["q"][0]
    return gpv_lookup.lookup(entries, settlement, street, house)


def parsed(cell):
    return [(e["settlement"], e["street"]) for e in gpv_parse.parse_row(kh_text.normalize(cell))]


class RowTests(unittest.TestCase):
    def test_columns(self):
        cols = kh_rows.columns(FIXTURE["lines"])
        self.assertEqual([q for _, q in cols], [f"{n}.{s}" for n in range(1, 7) for s in (1, 2)])

    def test_rows(self):
        rows = all_rows()
        self.assertTrue(all(len(r["q"]) == 1 for r in rows))
        valky = next(r for r in rows if r["text"].startswith("Валківський р-н, Валки м., Харківська вул.; Богодухівська"))
        self.assertEqual(valky["q"], ["1.2"])                      # X glued to the line ("… с., X") or alone
        self.assertNotIn(" X", valky["text"])
        # Bands split by inner rules, each with its own X, stay one row.
        self.assertTrue(any("Солоницівка: вул. Зоряна" in r["text"] and "Новопроложна" in r["text"] for r in rows))


class TextTests(unittest.TestCase):
    def test_marker_last(self):
        self.assertEqual(parsed("Валківський р-н, Валки м., Харківська вул.; Богодухівська вул.., Гузівка с., Ков'яги смт., Центральна вул."),
                         [("Валки", "Харківська"), ("Валки", "Богодухівська"), ("Гузівка", None), ("Ков'яги", "Центральна")])
        self.assertEqual(parsed("Валківський р-н, Велика Кадигробівка с., Водяна Балка с., Манили с. Мельникове с., Просівка с."),
                         [("Велика Кадигробівка", None), ("Водяна Балка", None), ("Манили", None), ("Мельникове", None), ("Просівка", None)])

    def test_marker_first(self):
        self.assertEqual(parsed("Богодухівськйи р-н, м. Валки вул. Курячівська, с. Литвинівка"),
                         [("Валки", "Курячівська"), ("Литвинівка", None)])

    def test_slips(self):
        self.assertEqual(parsed("Чугуївський р-н,с.Коропове,с.Лиман:Садова,Станционна"),
                         [("Коропове", None), ("Лиман", "Садова"), ("Лиман", "Станционна")])
        self.assertEqual(parsed("м.ЗміївАдминистративна,Донецка"), [("Зміїв", "Административна"), ("Зміїв", "Донецка")])
        self.assertEqual(parsed("с.Слобожанське-вул.: Дружби,Шевченко,С.Закори.Енергетикі"),
                         [("Слобожанське", "Дружби"), ("Слобожанське", "Шевченко"), ("Слобожанське", "Закори"), ("Слобожанське", "Енергетикі")])
        self.assertEqual(parsed("с.СкрипаЇ,х.Лесной,с.ШелудькІвка-вул.:Горького"),
                         [("Скрипаї", None), ("Лесной", None), ("Шелудьківка", "Горького")])
        self.assertEqual(parsed("м. Люботин, Низовая, Ревчанская"), [("Люботин", "Низовая"), ("Люботин", "Ревчанская")])
        self.assertEqual(parsed("вул. П.Мирного, с.Петровка, п.Беляевка"), [(None, "П.Мирного"), ("Петровка", None), ("Беляевка", None)])


class LookupTests(unittest.TestCase):
    def test_golden_addresses(self):
        self.assertEqual(lookup("Валки", "Харківська вул.")["queues"], ["1.2"])
        self.assertEqual(lookup("Солоницівка", "Заводська")["queues"], ["3.1"])
        self.assertEqual(lookup("Солоницівка", "Сумський шлях", "10")["level"], "house")
        self.assertEqual(lookup("Зміїв", "Фабрична")["queues"], ["6.2"])
        self.assertEqual(lookup("Гайдари")["queues"], ["4.1"])
        self.assertEqual(lookup("Люботин", "Абдулова")["queues"], ["2.2"])
        self.assertEqual(lookup("Високий", "Велозаводська")["queues"], ["2.1"])
        self.assertEqual(lookup("Ізюм", "Покровська")["queues"], ["3.2", "4.2"])

    def test_enterprises_left_out(self):
        names = {e["settlement"] for e in build.entries_from_rows(all_rows())}
        self.assertFalse(any(re.search(r"ТОВ|ПАТ|\"|завод\b", n) for n in names))


class SourceTests(unittest.TestCase):
    def test_find(self):
        listing = {"data": [
            {"attributes": {"filename": "Адреси та черги 26-27.docx", "filemime": "application/msword", "uri": {"url": "/a.docx"}}},
            {"attributes": {"filename": "Адреси та черги 26-27.pdf", "filemime": "application/pdf", "uri": {"url": "/sites/default/files/pdf/x.pdf"}}},
        ]}
        self.assertEqual(find_source.find(listing), "https://oblenergo.kharkiv.ua/sites/default/files/pdf/x.pdf")
        self.assertIsNone(find_source.find({"data": []}))


if __name__ == "__main__":
    unittest.main()
