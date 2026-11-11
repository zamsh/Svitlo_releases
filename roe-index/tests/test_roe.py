"""Row and index tests against Rivneoblenergo's GPV documents published 2026-10
(GPV_cherga_misto_Rivne-1.pdf: whole; GPV_cherga_Rivnenska_oblast-1.pdf: pages 1, 2 and 32).

Every expected queue below was checked by hand against the PDF text.
Run: python3 -m unittest discover -s roe-index/tests
"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpv-index", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))      # before gpv-index: both have a build.py
import roe_rows, build, gpv_lookup, find_source

with open(os.path.join(HERE, "fixtures", "roe-2026-10.json"), encoding="utf-8") as f:
    FIXTURE = json.load(f)


def all_rows():
    city = [r for r in roe_rows.rows(FIXTURE["city"]["lines"], FIXTURE["city"]["rules"], "city") if r["q"]]
    region = [r for r in roe_rows.rows(FIXTURE["region"]["lines"], FIXTURE["region"]["rules"], "region") if r["q"]]
    return city, region


def lookup(settlement, street=None, house=None):
    city, region = all_rows()
    rows = city + region
    entries = build.entries_from_rows(rows)
    for e in entries:
        e["q"] = rows[e["row"]]["q"][0]
    return gpv_lookup.lookup(entries, settlement, street, house)


class RowTests(unittest.TestCase):
    def test_city_rows(self):
        city, _ = all_rows()
        self.assertEqual(len(city), 82)
        self.assertTrue(all(len(r["q"]) == 1 for r in city))
        self.assertTrue(city[0]["text"].startswith("вул. Героїв УПА"))      # no row number
        self.assertEqual(city[0]["q"], ["1.1"])
        # A row split in two by an inner rule: the second part has its own queue.
        self.assertTrue(city[3]["text"].startswith("вул.Кулика і Гудачека, 38"))

    def test_region_rows(self):
        _, region = all_rows()
        self.assertTrue(all(len(r["q"]) == 1 for r in region))
        first = region[0]
        self.assertEqual((first["hromada"], first["q"]), ("Березнівська", ["1.2"]))
        self.assertIn("с.Яцковичі (повністю)", first["settlements"])
        self.assertIn("пров.Б.Хмельницького,В.Стуса", first["text"])           # word broken at the line end

    def test_queue_inside_text_cell(self):
        _, region = all_rows()
        r = next(r for r in region if "сокооцтовий" in r["text"])
        self.assertEqual(r["q"], ["5.2"])
        self.assertFalse(r["text"].endswith("5.2"))

    def test_join(self):
        self.assertEqual(roe_rows.join(["с.Крупець, Біла Криниця", "м. Радивилів"]), "с.Крупець, Біла Криниця м. Радивилів")
        self.assertEqual(roe_rows.join(["вул.Кулика і", "Гудачека"]), "вул.Кулика і Гудачека")


class LookupTests(unittest.TestCase):
    def check(self, expected, level, *address):
        r = lookup(*address)
        self.assertEqual((r["queues"], r["level"]), (expected, level), address)

    def test_city_houses(self):
        self.check(["1.1"], "house", "Рівне", "Соборна", "348")
        self.check(["1.1"], "house", "Рівне", "вул. Млинівська", "30")
        self.check(["1.1"], "house", "Рівне", "Корольова", "27")
        # Listed twice in the document, in two sub-queues.
        self.check(["3.1", "6.1"], "house", "Рівне", "Київська", "40а")

    def test_region(self):
        self.check(["4.1"], "range", "Колодязне", "Андріївська", "100")
        self.check(["5.2"], "settlement", "Озірці")
        self.check(["1.2"], "street", "Балашівка", "Вигон")

    def test_dash_lists_streets(self):
        # "С.Злазне- Цитень, Колгоспна": streets, not settlements.
        city, region = all_rows()
        entries = build.entries_from_rows(city + region)
        names = {e["settlement"] for e in entries}
        self.assertNotIn("Колгоспна", names)
        self.assertNotIn("Хороброго", names)


class SourceTests(unittest.TestCase):
    def test_find_links(self):
        html = ('<a href="https://www.roe.vsei.ua/wp-content/uploads/2026/03/GPV_cherga_misto_Rivne.pdf">x</a>'
                '<a href="https://www.roe.vsei.ua/wp-content/uploads/2026/10/GPV_cherga_misto_Rivne-1.pdf">x</a>'
                '<a href="https://www.roe.vsei.ua/wp-content/uploads/2026/10/GPV_cherga_Rivnenska_oblast-1.pdf">x</a>'
                '<a href="https://www.roe.vsei.ua/wp-content/uploads/gpv/Avaria_Rivne.pdf">x</a>')
        self.assertEqual(find_source.find(html), {
            "city": "https://www.roe.vsei.ua/wp-content/uploads/2026/10/GPV_cherga_misto_Rivne-1.pdf",
            "region": "https://www.roe.vsei.ua/wp-content/uploads/2026/10/GPV_cherga_Rivnenska_oblast-1.pdf"})


if __name__ == "__main__":
    unittest.main()
