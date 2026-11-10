"""Parser and lookup tests against the GPV document valid 01.10.2026-01.04.2027.

Every expected queue below was checked by hand against the text of HPV_26_27-sajt-8.10.2026.pdf.
Run: python3 -m unittest discover -s gpv-index/tests
"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import gpv_rows, gpv_parse, gpv_lookup, build

FIXTURE = os.path.join(HERE, "fixtures", "lines-HPV_26_27-2026-10-08.json")


def load_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


class ParseRowTests(unittest.TestCase):
    def entries(self, text):
        return [(e["settlement"], e["street"], e["houses"], e["partial"]) for e in gpv_parse.parse_row(text)]

    def test_streets_with_houses_after_settlement(self):
        e = self.entries("КП ВУВКГ (ФКНС № 9 ввід1); м.Горішні плавні: вул.Миру 9, 15А; Молодіжна 18, 21/6")
        self.assertIn(("Горішні плавні", "Миру", [{"n": "9"}, {"n": "15а"}], False), e)
        self.assertIn(("Горішні плавні", "Молодіжна", [{"n": "18"}, {"n": "21/6"}], False), e)

    def test_settlement_list(self):
        e = self.entries("с.Чечужино, Новоселівка, Друга Олександрівка")
        self.assertEqual([x[0] for x in e], ["Чечужино", "Новоселівка", "Друга Олександрівка"])
        self.assertTrue(all(x[1] is None for x in e))

    def test_abbreviated_settlement_and_odd_range(self):
        e = self.entries("с.В.Рублівка вул.Молодіжна №24,34-44,75-85(непарні);вул.Центральна №38")
        self.assertEqual(e[0][0], "В.Рублівка")
        self.assertEqual(e[0][2], [{"n": "24"}, {"from": 34, "to": 44}, {"from": 75, "to": 85, "parity": "odd"}])

    def test_partial_settlement(self):
        e = self.entries("с. Голуби, с.Сагайдак частково вул.: Генерала Пащенка (буд.37-130)")
        self.assertIn(("Голуби", None, None, False), e)
        self.assertIn(("Сагайдак", "Генерала Пащенка", [{"from": 37, "to": 130}], True), e)

    def test_unbalanced_quotes_do_not_swallow_the_settlement(self):
        e = self.entries('КВП "ТЕ" м. Горішні Плавні" (АБК); Міський парк; пров.Молодіжний 2, 20')
        self.assertIn(("Горішні Плавні", "Молодіжний", [{"n": "2"}, {"n": "20"}], False), e)

    def test_marker_inside_word_is_not_a_street_kind(self):
        e = self.entries("м. Хорол вул. Короленка з провулками, Квартальна, тупік Південний")
        streets = [x[1] for x in e]
        self.assertIn("Квартальна", streets)
        self.assertIn("Короленка", streets)
        self.assertIn("Південний", streets)


class DocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = gpv_rows.rows(load_fixture())
        cls.entries = build.entries_from_rows(cls.rows)

    def find(self, *address):
        r = gpv_lookup.lookup(self.entries, *address)
        return r["queues"], r["level"]

    def test_document_structure(self):
        problems, stats = build.validate(self.rows, self.entries, None)
        self.assertEqual(problems, [])
        self.assertEqual(len(stats["rows_per_queue"]), 12)

    def test_period_from_title(self):
        self.assertEqual(build.title_period(load_fixture()), ("2026-10-01", "2027-04-01"))

    def test_golden_addresses(self):
        cases = {
            ("Горішні Плавні", "вулиця Молодіжна", "18"): (["5.1"], "house"),
            ("Горішні Плавні", "Молодіжна", "4"): (["1.2"], "house"),
            ("Горішні Плавні", "провулок Молодіжний", "20"): (["1.2", "5.1"], "house"),     # listed in both
            ("Велика Рублівка", "Молодіжна", "77"): (["4.2"], "range"),                    # 75-85 odd
            ("Чечужино", None, None): (["5.1"], "settlement"),
            ("Сагайдак", "Генерала Пащенка", "50"): (["6.2"], "range"),
            ("Полтава", "Решетилівська", "47а"): (["1.1"], "house"),                        # document typo: Решитилівська
            ("Нова Галещина", "Шкільна", "3"): (["5.1"], "street"),
        }
        for address, expected in cases.items():
            with self.subTest(address=address):
                self.assertEqual(self.find(*address), expected)

    def test_unknown_address(self):
        self.assertEqual(self.find("Неіснуюче", "Вигадана", "1"), ([], None))


if __name__ == "__main__":
    unittest.main()
