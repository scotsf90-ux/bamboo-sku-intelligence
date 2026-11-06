"""Guards index(): a malformed dimension row that no fact row uses must be skipped, not crash the daily run."""
import unittest

from refresh_closures import index


class UnusedBadRowsTest(unittest.TestCase):
    def test_unused_malformed_rows_do_not_crash(self):
        api = {"dimensions": {
            "clients": {"rows": [[1, "Good Store", 0, 0], [2, 404, 0, 0]]},
            "products": {"rows": [[1, "Gummiez 10pk", 0, 0], [2, 77, 0, 0], [3, "Odd Cat", 0, "x"]]},
            "retail_categories": {"rows": [[0, "Edibles Line"]]},
            "reps": {"rows": [[0, "Koen B"]]}},
            "facts": {"client_product_sales": {"row": [0], "col": [0], "revenue_cents": [100],
                                               "units": [1], "last_ordered_at_utc": ["2026-06-02"]}}}
        out = index(api, {})
        self.assertEqual(out, [("Good Store", "Gummiez 10pk", "Edibles Line", 100, 1, "2026-06-02")])


if __name__ == "__main__":
    unittest.main()
