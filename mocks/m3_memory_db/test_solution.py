"""Mock 3 tests. The tests are the spec."""

import unittest

from solution import MemoryDB


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()

    def test_set_then_get(self):
        self.assertIsNone(self.db.set("user1", "name", "alice"))
        self.assertEqual(self.db.get("user1", "name"), "alice")

    def test_get_missing_key_or_field(self):
        self.assertIsNone(self.db.get("nokey", "name"))
        self.db.set("user1", "name", "alice")
        self.assertIsNone(self.db.get("user1", "age"))

    def test_set_overwrites(self):
        self.db.set("user1", "name", "alice")
        self.db.set("user1", "name", "bob")
        self.assertEqual(self.db.get("user1", "name"), "bob")

    def test_keys_are_independent(self):
        self.db.set("user1", "name", "alice")
        self.db.set("user2", "name", "bob")
        self.assertEqual(self.db.get("user1", "name"), "alice")
        self.assertEqual(self.db.get("user2", "name"), "bob")

    def test_delete(self):
        self.db.set("user1", "name", "alice")
        self.assertTrue(self.db.delete("user1", "name"))
        self.assertIsNone(self.db.get("user1", "name"))
        self.assertFalse(self.db.delete("user1", "name"))
        self.assertFalse(self.db.delete("nokey", "name"))

    def test_deleting_last_field_removes_the_key(self):
        self.db.set("user1", "name", "alice")
        self.db.delete("user1", "name")
        self.assertFalse(self.db.delete("user1", "anything"))


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()

    def test_scan_is_sorted_by_field_name(self):
        self.db.set("user1", "name", "alice")
        self.db.set("user1", "age", "30")
        self.db.set("user1", "city", "toronto")
        self.assertListEqual(
            self.db.scan("user1"), ["age(30)", "city(toronto)", "name(alice)"]
        )

    def test_scan_missing_key(self):
        self.assertListEqual(self.db.scan("nokey"), [])

    def test_scan_by_prefix(self):
        self.db.set("user1", "addr_city", "toronto")
        self.db.set("user1", "addr_street", "queen")
        self.db.set("user1", "name", "alice")
        self.assertListEqual(
            self.db.scan_by_prefix("user1", "addr_"),
            ["addr_city(toronto)", "addr_street(queen)"],
        )

    def test_scan_by_prefix_no_match(self):
        self.db.set("user1", "name", "alice")
        self.assertListEqual(self.db.scan_by_prefix("user1", "zzz"), [])

    def test_scan_reflects_deletes(self):
        self.db.set("user1", "a", "1")
        self.db.set("user1", "b", "2")
        self.db.delete("user1", "a")
        self.assertListEqual(self.db.scan("user1"), ["b(2)"])


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()

    def test_set_at_and_get_at(self):
        self.db.set_at(10, "user1", "name", "alice")
        self.assertEqual(self.db.get_at(10, "user1", "name"), "alice")
        self.assertEqual(self.db.get_at(10**9, "user1", "name"), "alice")

    def test_ttl_expiry_is_exclusive(self):
        self.db.set_at_with_ttl(10, "user1", "name", "alice", 5)
        self.assertEqual(self.db.get_at(14, "user1", "name"), "alice")
        self.assertIsNone(self.db.get_at(15, "user1", "name"))

    def test_level_one_methods_still_work(self):
        self.db.set("user1", "name", "alice")
        self.assertEqual(self.db.get("user1", "name"), "alice")
        self.assertEqual(self.db.get_at(10**9, "user1", "name"), "alice")

    def test_plain_set_clears_an_existing_ttl(self):
        self.db.set_at_with_ttl(0, "user1", "name", "alice", 5)
        self.db.set_at(1, "user1", "name", "bob")
        self.assertEqual(self.db.get_at(100, "user1", "name"), "bob")

    def test_new_ttl_replaces_the_old_one(self):
        self.db.set_at_with_ttl(0, "user1", "name", "alice", 100)
        self.db.set_at_with_ttl(1, "user1", "name", "bob", 5)
        self.assertIsNone(self.db.get_at(6, "user1", "name"))

    def test_delete_at_respects_expiry(self):
        self.db.set_at_with_ttl(0, "user1", "name", "alice", 5)
        self.assertFalse(self.db.delete_at(5, "user1", "name"))
        self.db.set_at_with_ttl(6, "user1", "name", "alice", 5)
        self.assertTrue(self.db.delete_at(7, "user1", "name"))

    def test_scan_at_hides_expired_fields(self):
        self.db.set_at(0, "user1", "a", "1")
        self.db.set_at_with_ttl(0, "user1", "b", "2", 5)
        self.assertListEqual(self.db.scan_at(4, "user1"), ["a(1)", "b(2)"])
        self.assertListEqual(self.db.scan_at(5, "user1"), ["a(1)"])

    def test_key_disappears_when_all_fields_expire(self):
        self.db.set_at_with_ttl(0, "user1", "a", "1", 5)
        self.assertListEqual(self.db.scan_at(5, "user1"), [])
        self.assertListEqual(self.db.scan_by_prefix_at(5, "user1", "a"), [])

    def test_scan_by_prefix_at(self):
        self.db.set_at(0, "user1", "addr_city", "toronto")
        self.db.set_at_with_ttl(0, "user1", "addr_street", "queen", 5)
        self.assertListEqual(
            self.db.scan_by_prefix_at(5, "user1", "addr_"), ["addr_city(toronto)"]
        )


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()

    def test_backup_counts_non_empty_keys(self):
        self.db.set_at(0, "user1", "a", "1")
        self.db.set_at(0, "user2", "a", "1")
        self.assertEqual(self.db.backup(1), 2)

    def test_backup_ignores_expired_fields(self):
        self.db.set_at_with_ttl(0, "user1", "a", "1", 5)
        self.db.set_at(0, "user2", "a", "1")
        self.assertEqual(self.db.backup(5), 1)

    def test_restore_brings_back_deleted_data(self):
        self.db.set_at(0, "user1", "name", "alice")
        self.db.backup(1)
        self.db.delete_at(2, "user1", "name")
        self.assertIsNone(self.db.restore(3, 1))
        self.assertEqual(self.db.get_at(3, "user1", "name"), "alice")

    def test_restore_drops_data_added_after_the_backup(self):
        self.db.set_at(0, "user1", "a", "1")
        self.db.backup(1)
        self.db.set_at(2, "user1", "b", "2")
        self.db.restore(3, 1)
        self.assertListEqual(self.db.scan_at(3, "user1"), ["a(1)"])

    def test_restore_picks_the_latest_backup_at_or_before(self):
        self.db.set_at(0, "user1", "a", "1")
        self.db.backup(10)
        self.db.set_at(11, "user1", "b", "2")
        self.db.backup(20)
        self.db.restore(30, 19)
        self.assertListEqual(self.db.scan_at(30, "user1"), ["a(1)"])

    def test_restore_with_no_backup_empties_the_database(self):
        self.db.set_at(0, "user1", "a", "1")
        self.db.backup(10)
        self.db.restore(30, 5)
        self.assertListEqual(self.db.scan_at(30, "user1"), [])

    def test_ttl_is_rebased_on_the_restore_time(self):
        self.db.set_at_with_ttl(0, "user1", "a", "1", 100)  # dies at 100
        self.db.backup(10)  # 90 left to live
        self.db.restore(1000, 10)  # so it should now die at 1090
        self.assertEqual(self.db.get_at(1089, "user1", "a"), "1")
        self.assertIsNone(self.db.get_at(1090, "user1", "a"))

    def test_permanent_fields_stay_permanent_across_restore(self):
        self.db.set_at(0, "user1", "a", "1")
        self.db.backup(10)
        self.db.restore(1000, 10)
        self.assertEqual(self.db.get_at(10**9, "user1", "a"), "1")


class TestLevel5(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()

    def test_begin_and_commit_return_values(self):
        self.assertTrue(self.db.begin(1))
        self.assertFalse(self.db.begin(2))
        self.assertTrue(self.db.commit(3))
        self.assertFalse(self.db.commit(4))

    def test_abort_return_values(self):
        self.assertFalse(self.db.abort(1))
        self.db.begin(2)
        self.assertTrue(self.db.abort(3))
        self.assertFalse(self.db.abort(4))

    def test_reads_see_uncommitted_writes(self):
        self.db.begin(1)
        self.db.set_at(2, "user1", "name", "alice")
        self.assertEqual(self.db.get_at(2, "user1", "name"), "alice")
        self.assertListEqual(self.db.scan_at(2, "user1"), ["name(alice)"])

    def test_commit_persists(self):
        self.db.begin(1)
        self.db.set_at(2, "user1", "name", "alice")
        self.db.commit(3)
        self.assertEqual(self.db.get_at(4, "user1", "name"), "alice")

    def test_abort_discards_writes(self):
        self.db.begin(1)
        self.db.set_at(2, "user1", "name", "alice")
        self.db.abort(3)
        self.assertIsNone(self.db.get_at(4, "user1", "name"))

    def test_abort_restores_overwritten_values(self):
        self.db.set_at(0, "user1", "name", "alice")
        self.db.begin(1)
        self.db.set_at(2, "user1", "name", "bob")
        self.db.abort(3)
        self.assertEqual(self.db.get_at(4, "user1", "name"), "alice")

    def test_abort_undoes_deletes(self):
        self.db.set_at(0, "user1", "name", "alice")
        self.db.begin(1)
        self.assertTrue(self.db.delete_at(2, "user1", "name"))
        self.assertIsNone(self.db.get_at(2, "user1", "name"))
        self.db.abort(3)
        self.assertEqual(self.db.get_at(4, "user1", "name"), "alice")

    def test_ttls_set_inside_a_transaction_survive_commit(self):
        self.db.begin(0)
        self.db.set_at_with_ttl(0, "user1", "name", "alice", 5)
        self.db.commit(1)
        self.assertEqual(self.db.get_at(4, "user1", "name"), "alice")
        self.assertIsNone(self.db.get_at(5, "user1", "name"))

    def test_transactions_can_be_reused(self):
        self.db.begin(1)
        self.db.set_at(1, "k", "a", "1")
        self.db.commit(2)
        self.db.begin(3)
        self.db.set_at(3, "k", "b", "2")
        self.db.abort(4)
        self.assertListEqual(self.db.scan_at(5, "k"), ["a(1)"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
