import unittest

from refresh_sell_through import build_dataset, classify, percentile, weighted_sell_through


def row(allocated, sold):
    sell_through = sold / allocated
    return {
        "allocated_units": allocated,
        "sold_units": sold,
        "is_sellout": sold == allocated,
        "is_near_sellout": sell_through >= 0.9,
    }


class SellThroughRulesTest(unittest.TestCase):
    def test_percentile_interpolates(self):
        self.assertEqual(percentile([10, 20, 30, 40], 0.75), 32.5)

    def test_chronic_sellout_requires_consistent_weighted_demand(self):
        rows = [row(100, 100), row(100, 100), row(100, 100), row(100, 95)]
        signal, adjustment, *_ = classify(rows, 4, 100, 3, 4)
        self.assertEqual(signal, "Chronic sellout")
        self.assertEqual(adjustment, 30)

    def test_large_overallocation_blocks_volume_increase(self):
        rows = [row(100, 100), row(100, 100), row(100, 100), row(1000, 100)]
        signal, adjustment, *_ = classify(rows, 4, 100, 3, 3)
        self.assertEqual(signal, "Volatile allocation")
        self.assertEqual(adjustment, 0)

    def test_recent_slow_mover_reduces_volume(self):
        rows = [row(100, 20), row(100, 30), row(100, 40), row(100, 40)]
        signal, adjustment, price_signal, _ = classify(rows, 4, 100, 0, 0)
        self.assertEqual(signal, "Slow mover")
        self.assertEqual(adjustment, -10)
        self.assertEqual(price_signal, "Do not raise")

    def test_mixed_recent_allocations_do_not_create_emerging_shortage(self):
        rows = [row(100, 100), row(100, 95), row(1000, 100), row(1000, 100)]
        signal, adjustment, *_ = classify(rows, 4, 100, 1, 2)
        self.assertNotEqual(signal, "Emerging shortage")
        self.assertEqual(adjustment, -10)

    def test_weighted_sell_through_uses_units(self):
        self.assertAlmostEqual(weighted_sell_through([row(100, 100), row(900, 0)]), 0.1)

    def test_short_history_flower_stays_in_dataset(self):
        api = {"allocations": [{
            "inventory_allocation_id": "week-a", "period_from": "2026-10-11",
            "period_to": "2026-10-17", "timezone": "America/Los_Angeles",
            "products": [{"product_id": "flower-a", "product_name": "Sungrown Flower 3.5g",
                          "brand_name": "Snickle Fritz", "category_name": "Snickle Fritz Flower",
                          "allocated_units": 100, "sold_units": 100, "unsold_units": 0,
                          "sell_through": 1, "sold_revenue": 500}]}]}
        result = build_dataset(api)
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["category_name"], "Snickle Fritz Flower")
        self.assertEqual(result["products"][0]["signal"], "Limited history")
        self.assertEqual(result["products"][0]["soldout_weeks"], 1)


if __name__ == "__main__":
    unittest.main()
