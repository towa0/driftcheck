import unittest

from driftcheck.extract import extract_facts, Fact, extract


class TestExtract(unittest.TestCase):
    def test_units_across_languages(self):
        self.assertEqual(extract_facts("up to 8 kg"), [Fact("kg", "8")])
        self.assertEqual(extract_facts("högst 7,5 kg"), [Fact("kg", "7.5")])
        self.assertEqual(extract_facts("avautuu 24 tuntia ennen"), [Fact("hour", "24")])
        self.assertEqual(extract_facts("innerhalb von 14 Tagen"), [Fact("day", "14")])
        self.assertEqual(extract_facts("schließt 45 Minuten vor"), [Fact("minute", "45")])

    def test_money_prefix_and_suffix(self):
        self.assertEqual(extract_facts("a fee of €60."), [Fact("eur", "60")])
        self.assertEqual(extract_facts("Gebühr von 60 € aufgegeben"), [Fact("eur", "60")])

    def test_dimensions_not_double_counted(self):
        self.assertEqual(extract_facts("max 55 x 40 x 23 cm."), [Fact("cm", "55x40x23")])

    def test_ignores_bare_numbers(self):
        self.assertEqual(extract_facts("Gate 23 is open"), [])

    def test_links_normalised(self):
        ex = extract("# T\n## A\nSee [x](/fi/hotel-booking).", "fi")
        self.assertEqual(ex.links, ["/{loc}/hotel-booking"])


if __name__ == "__main__":
    unittest.main()
