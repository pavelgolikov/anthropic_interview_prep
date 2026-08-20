"""Mock 5 tests. The tests are the spec."""

import unittest

from solution import Warehouse


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.wh = Warehouse()

    def test_add_stock_returns_the_total(self):
        self.assertEqual(self.wh.add_stock("widget", 5), 5)

    def test_add_stock_accumulates(self):
        self.wh.add_stock("widget", 5)
        self.assertEqual(self.wh.add_stock("widget", 3), 8)
        self.assertEqual(self.wh.get_quantity("widget"), 8)

    def test_get_quantity_missing_item(self):
        self.assertIsNone(self.wh.get_quantity("nothing"))

    def test_ship_returns_the_remainder(self):
        self.wh.add_stock("widget", 10)
        self.assertEqual(self.wh.ship("widget", 4), 6)
        self.assertEqual(self.wh.get_quantity("widget"), 6)

    def test_ship_beyond_stock_changes_nothing(self):
        self.wh.add_stock("widget", 5)
        self.assertIsNone(self.wh.ship("widget", 6))
        self.assertEqual(self.wh.get_quantity("widget"), 5)

    def test_ship_missing_item(self):
        self.assertIsNone(self.wh.ship("nothing", 1))

    def test_item_survives_being_emptied(self):
        self.wh.add_stock("widget", 5)
        self.assertEqual(self.wh.ship("widget", 5), 0)
        self.assertEqual(self.wh.get_quantity("widget"), 0)


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.wh = Warehouse()

    def test_search_orders_by_quantity_descending(self):
        self.wh.add_stock("bolt", 5)
        self.wh.add_stock("bracket", 9)
        self.wh.add_stock("brace", 1)
        self.assertListEqual(
            self.wh.search("b"), ["bracket(9)", "bolt(5)", "brace(1)"]
        )

    def test_search_breaks_ties_by_item_id(self):
        self.wh.add_stock("b3", 5)
        self.wh.add_stock("b1", 5)
        self.wh.add_stock("b2", 5)
        self.assertListEqual(self.wh.search("b"), ["b1(5)", "b2(5)", "b3(5)"])

    def test_search_skips_empty_items(self):
        self.wh.add_stock("nut", 3)
        self.wh.add_stock("nail", 2)
        self.wh.ship("nail", 2)
        self.assertListEqual(self.wh.search("n"), ["nut(3)"])
        self.assertListEqual(self.wh.search("na"), [])

    def test_search_no_match(self):
        self.wh.add_stock("bolt", 5)
        self.assertListEqual(self.wh.search("zzz"), [])

    def test_search_returns_at_most_ten(self):
        for i in range(12):
            self.wh.add_stock(f"item{i:02d}", i + 1)
        found = self.wh.search("item")
        self.assertEqual(len(found), 10)
        self.assertEqual(found[0], "item11(12)")
        self.assertEqual(found[-1], "item02(3)")

    def test_search_matches_a_prefix_not_a_substring(self):
        self.wh.add_stock("abc", 1)
        self.wh.add_stock("xabc", 2)
        self.assertListEqual(self.wh.search("abc"), ["abc(1)"])


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.wh = Warehouse()

    def test_add_stock_at_and_get_quantity_at(self):
        self.assertEqual(self.wh.add_stock_at(10, "milk", 5), 5)
        self.assertEqual(self.wh.get_quantity_at(10**9, "milk"), 5)

    def test_expiry_is_exclusive(self):
        self.wh.add_stock_at_with_expiry(10, "milk", 5, 5)
        self.assertEqual(self.wh.get_quantity_at(14, "milk"), 5)
        self.assertEqual(self.wh.get_quantity_at(15, "milk"), 0)

    def test_level_one_methods_still_work(self):
        self.assertEqual(self.wh.add_stock("milk", 5), 5)
        self.assertEqual(self.wh.get_quantity("milk"), 5)
        self.assertEqual(self.wh.get_quantity_at(10**9, "milk"), 5)

    def test_permanent_and_expiring_stock_coexist(self):
        self.wh.add_stock_at(0, "milk", 3)
        self.wh.add_stock_at_with_expiry(0, "milk", 2, 5)
        self.assertEqual(self.wh.get_quantity_at(4, "milk"), 5)
        self.assertEqual(self.wh.get_quantity_at(5, "milk"), 3)

    def test_ship_at_takes_the_soonest_expiring_first(self):
        self.wh.add_stock_at_with_expiry(0, "milk", 2, 100)
        self.wh.add_stock_at_with_expiry(0, "milk", 2, 5)
        self.assertEqual(self.wh.ship_at(0, "milk", 2), 2)
        self.assertEqual(self.wh.get_quantity_at(5, "milk"), 2)

    def test_never_expiring_units_ship_last(self):
        self.wh.add_stock_at(0, "milk", 2)
        self.wh.add_stock_at_with_expiry(0, "milk", 2, 10)
        self.assertEqual(self.wh.ship_at(0, "milk", 2), 2)
        self.assertEqual(self.wh.get_quantity_at(10**9, "milk"), 2)

    def test_ship_at_cannot_use_expired_units(self):
        self.wh.add_stock_at_with_expiry(0, "milk", 5, 10)
        self.assertIsNone(self.wh.ship_at(10, "milk", 1))
        self.assertEqual(self.wh.get_quantity_at(10, "milk"), 0)

    def test_search_at_hides_expired_stock(self):
        self.wh.add_stock_at(0, "aa", 1)
        self.wh.add_stock_at_with_expiry(0, "ab", 9, 5)
        self.assertListEqual(self.wh.search_at(4, "a"), ["ab(9)", "aa(1)"])
        self.assertListEqual(self.wh.search_at(5, "a"), ["aa(1)"])

    def test_item_emptied_by_expiry_still_exists(self):
        self.wh.add_stock_at_with_expiry(0, "milk", 5, 5)
        self.assertEqual(self.wh.get_quantity_at(5, "milk"), 0)


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.wh = Warehouse()

    def test_place_order_deducts_stock(self):
        self.wh.add_stock_at(0, "bolt", 10)
        self.assertTrue(self.wh.place_order(1, "order1", "bolt", 4))
        self.assertEqual(self.wh.get_quantity_at(1, "bolt"), 6)

    def test_duplicate_order_id_is_rejected(self):
        self.wh.add_stock_at(0, "bolt", 10)
        self.wh.place_order(1, "order1", "bolt", 4)
        self.assertFalse(self.wh.place_order(2, "order1", "bolt", 1))
        self.assertEqual(self.wh.get_quantity_at(2, "bolt"), 6)

    def test_order_for_an_unknown_item(self):
        self.assertFalse(self.wh.place_order(0, "order1", "nothing", 1))

    def test_order_beyond_stock_changes_nothing(self):
        self.wh.add_stock_at(0, "bolt", 5)
        self.assertFalse(self.wh.place_order(0, "order1", "bolt", 6))
        self.assertEqual(self.wh.get_quantity_at(0, "bolt"), 5)

    def test_cancel_returns_units_to_stock(self):
        self.wh.add_stock_at(0, "bolt", 10)
        self.wh.place_order(1, "order1", "bolt", 4)
        self.assertEqual(self.wh.cancel_order(2, "order1"), 4)
        self.assertEqual(self.wh.get_quantity_at(2, "bolt"), 10)

    def test_cancel_unknown_order(self):
        self.assertIsNone(self.wh.cancel_order(0, "nothing"))

    def test_an_order_cancels_only_once(self):
        self.wh.add_stock_at(0, "bolt", 10)
        self.wh.place_order(1, "order1", "bolt", 4)
        self.assertEqual(self.wh.cancel_order(2, "order1"), 4)
        self.assertIsNone(self.wh.cancel_order(3, "order1"))

    def test_units_that_expired_while_held_are_not_returned(self):
        self.wh.add_stock_at(0, "milk", 3)
        self.wh.add_stock_at_with_expiry(0, "milk", 2, 5)
        self.assertTrue(self.wh.place_order(0, "order1", "milk", 4))
        self.assertEqual(self.wh.get_quantity_at(0, "milk"), 1)
        self.assertEqual(self.wh.cancel_order(6, "order1"), 2)
        self.assertEqual(self.wh.get_quantity_at(6, "milk"), 3)


class TestLevel5(unittest.TestCase):
    def setUp(self):
        self.wh = Warehouse()

    def test_quantity_at_before_the_item_existed(self):
        self.wh.add_stock_at(10, "bolt", 5)
        self.assertIsNone(self.wh.quantity_at(100, "bolt", 9))

    def test_quantity_at_sees_operations_at_or_before(self):
        self.wh.add_stock_at(10, "bolt", 5)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 10), 5)

    def test_quantity_at_ignores_later_operations(self):
        self.wh.add_stock_at(10, "bolt", 5)
        self.wh.add_stock_at(20, "bolt", 7)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 19), 5)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 20), 12)

    def test_quantity_at_reflects_shipments(self):
        self.wh.add_stock_at(0, "bolt", 10)
        self.wh.ship_at(5, "bolt", 3)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 4), 10)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 5), 7)

    def test_quantity_at_accounts_for_expiry(self):
        self.wh.add_stock_at_with_expiry(0, "milk", 5, 10)
        self.assertEqual(self.wh.quantity_at(100, "milk", 9), 5)
        self.assertEqual(self.wh.quantity_at(100, "milk", 10), 0)

    def test_quantity_at_reflects_orders_and_cancellations(self):
        self.wh.add_stock_at(0, "bolt", 10)
        self.wh.place_order(2, "order1", "bolt", 4)
        self.wh.cancel_order(8, "order1")
        self.assertEqual(self.wh.quantity_at(100, "bolt", 1), 10)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 2), 6)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 7), 6)
        self.assertEqual(self.wh.quantity_at(100, "bolt", 8), 10)

    def test_quantity_at_the_present_matches_get_quantity_at(self):
        self.wh.add_stock_at(0, "milk", 4)
        self.wh.add_stock_at_with_expiry(1, "milk", 6, 20)
        self.wh.ship_at(2, "milk", 3)
        self.wh.place_order(3, "order1", "milk", 2)
        self.assertEqual(
            self.wh.quantity_at(30, "milk", 30), self.wh.get_quantity_at(30, "milk")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
