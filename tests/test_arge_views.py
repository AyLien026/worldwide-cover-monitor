"""Regression checks for the ARGE Polarphilatelie GitHub Pages views."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ArgeViewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.porto = (ROOT / "arge/portoliste/index.html").read_text(encoding="utf-8")
        cls.atlas = (ROOT / "arge/polar/index.html").read_text(encoding="utf-8")
        cls.rates = json.loads((ROOT / "postage/rates.json").read_text(encoding="utf-8"))

    def test_exact_existing_arge_country_scope(self):
        block = re.search(r"const countries=\[(.*?)\];", self.porto, flags=re.DOTALL)
        self.assertIsNotNone(block)
        selected = re.findall(r"\['[^']+','[^']+','([^']+)'\]", block.group(1))
        self.assertEqual(len(selected), 33)
        self.assertEqual(len(set(selected)), 33)
        known = {r["id"] for r in self.rates["rates"]}
        self.assertFalse(set(selected) - known, "Unmatched ARGE rate IDs")
        self.assertIn("south-georgia", selected)
        self.assertNotIn("switzerland", selected)
        self.assertNotIn("germany", selected)

    def test_shared_data_only(self):
        self.assertIn("fetch('../../postage/rates.json'", self.porto)
        self.assertIn("fetch('../../polar/stations.json'", self.atlas)
        self.assertIn("fetch('../../polar/land.json'", self.atlas)
        self.assertIn("cache:'no-store'", self.porto)

    def test_verified_and_unverified_not_conflated(self):
        self.assertIn("r.status==='verified'", self.porto)
        self.assertIn("Nicht abschließend verifiziert", self.porto)
        self.assertIn("nicht", self.porto.lower())
        self.assertIn("scheduled_from", self.porto)

    def test_staging_pages_deployed(self):
        workflow = (ROOT / ".github/workflows/monitor.yml").read_text(encoding="utf-8")
        self.assertIn("'arge/**'", workflow)
        self.assertIn("cp arge/portoliste/index.html site/arge/portoliste/index.html", workflow)
        self.assertIn("cp arge/polar/index.html site/arge/polar/index.html", workflow)


if __name__ == "__main__":
    unittest.main()
