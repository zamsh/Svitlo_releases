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
    """find_source against saved pages of t.me/s/kharkivenergy (2026-11-20: posts 2371–2390 and the page before)."""
    PDF = ("https://oblenergo.kharkiv.ua/sites/default/files/pdf/"
           "%D0%90%D0%B4%D1%80%D0%B5%D1%81%D0%B8%20%D1%82%D0%B0%20%D1%87%D0%B5%D1%80%D0%B3%D0%B8%2026-27.pdf")

    @staticmethod
    def page(name):
        with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as f:
            return f.read()

    def run_main(self, pages, meta_url=PDF):
        """main() with fetch() answering from `pages` (url -> html or exception); returns (code, stdout json)."""
        import io, tempfile, contextlib
        def fake(url):
            r = pages[url]
            if isinstance(r, Exception):
                raise r
            return r
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as m:
            json.dump({"url": meta_url}, m)
        out, err, orig = io.StringIO(), io.StringIO(), find_source.fetch
        find_source.fetch = fake
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = find_source.main(["--meta", m.name])
        finally:
            find_source.fetch = orig
            os.unlink(m.name)
        return code, (json.loads(out.getvalue()) if out.getvalue() else None)

    def test_link_from_channel(self):
        url, oldest = find_source.find(self.page("kharkiv-telegram-2026-11-20.html"))
        self.assertEqual(url, self.PDF)
        self.assertEqual(oldest, 2371)
        self.assertEqual(find_source.find(self.page("kharkiv-telegram-2026-11-20-before-2371.html"))[0], self.PDF)

    def test_newest_post_wins(self):
        page = ('<div data-post="kharkivenergy/10">Перелік адрес за чергами - <a href="https://x/old.pdf">тут</a></div>'
                '<div data-post="kharkivenergy/11">Перелік адрес за чергами - <a href="https://x/new%2027-28.pdf">тут</a></div>'
                '<div data-post="kharkivenergy/12">Перелік адрес — <a href="https://t.me/x">не PDF</a></div>'
                '<div data-post="kharkivenergy/13"><a href="https://x/other.pdf">без підпису</a></div>')
        self.assertEqual(find_source.find(page), ("https://x/new%2027-28.pdf", 10))
        self.assertEqual(find_source.find("<html>Loading...</html>"), (None, None))

    def test_same_document(self):
        self.assertTrue(find_source.same_document(self.PDF, find_source.urllib.parse.unquote(self.PDF)))
        self.assertFalse(find_source.same_document(self.PDF, self.PDF.replace("26-27", "27-28")))
        self.assertFalse(find_source.same_document(self.PDF, None))

    def test_main(self):
        first, before = self.page("kharkiv-telegram-2026-11-20.html"), self.page("kharkiv-telegram-2026-11-20-before-2371.html")
        ch = find_source.CHANNEL
        self.assertEqual(self.run_main({ch: first}), (0, {"url": self.PDF, "new": False}))
        self.assertEqual(self.run_main({ch: first}, meta_url="https://x/old.pdf"), (0, {"url": self.PDF, "new": True}))
        # No such post on the first page: one older page is read.
        no_link = find_source.MARKER.sub("Графік", first)
        self.assertEqual(self.run_main({ch: no_link, ch + "?before=2371": before}), (0, {"url": self.PDF, "new": False}))
        self.assertEqual(self.run_main({ch: no_link, ch + "?before=2371": no_link})[0], 2)
        self.assertEqual(self.run_main({ch: find_source.urllib.error.URLError("timed out")})[0], 3)


if __name__ == "__main__":
    unittest.main()
