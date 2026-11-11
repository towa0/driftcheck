import json
import unittest
from pathlib import Path

from driftcheck.compare import check_corpus, baseline_check, evaluate

DATA = Path(__file__).resolve().parent.parent / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class TestShippedData(unittest.TestCase):
    def test_driftcheck_result(self):
        ev = evaluate(check_corpus(load("articles.json")), load("planted_issues.json"))
        self.assertEqual((ev["true_positives"], ev["planted"], ev["found"]), (10, 11, 11))

    def test_baseline_result(self):
        ev = evaluate(baseline_check(load("articles.json")), load("planted_issues.json"))
        self.assertEqual(ev["true_positives"], 2)


if __name__ == "__main__":
    unittest.main()
