"""Mock 1 tests. The tests are the spec: where README.md is ambiguous, believe these."""

import unittest

from solution import FileHost


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.fh = FileHost()

    def test_upload_then_get(self):
        self.fh.file_upload("file.txt", 100)
        self.assertEqual(self.fh.file_get("file.txt"), 100)

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.fh.file_get("nope.txt"))

    def test_upload_returns_none(self):
        self.assertIsNone(self.fh.file_upload("a.txt", 1))

    def test_duplicate_upload_raises(self):
        self.fh.file_upload("file.txt", 100)
        with self.assertRaises(RuntimeError):
            self.fh.file_upload("file.txt", 200)

    def test_copy(self):
        self.fh.file_upload("a.txt", 42)
        self.fh.file_copy("a.txt", "b.txt")
        self.assertEqual(self.fh.file_get("b.txt"), 42)
        self.assertEqual(self.fh.file_get("a.txt"), 42)

    def test_copy_missing_source_raises(self):
        with self.assertRaises(RuntimeError):
            self.fh.file_copy("ghost.txt", "b.txt")

    def test_copy_overwrites_dest(self):
        self.fh.file_upload("a.txt", 42)
        self.fh.file_upload("b.txt", 7)
        self.fh.file_copy("a.txt", "b.txt")
        self.assertEqual(self.fh.file_get("b.txt"), 42)

    def test_zero_size_file_is_a_real_file(self):
        self.fh.file_upload("empty.txt", 0)
        self.assertEqual(self.fh.file_get("empty.txt"), 0)


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.fh = FileHost()

    def test_search_orders_by_size_desc(self):
        self.fh.file_upload("f1.txt", 100)
        self.fh.file_upload("f2.txt", 300)
        self.fh.file_upload("f3.txt", 200)
        self.assertListEqual(self.fh.file_search("f"), ["f2.txt", "f3.txt", "f1.txt"])

    def test_search_breaks_ties_by_name_asc(self):
        self.fh.file_upload("beta.txt", 50)
        self.fh.file_upload("alpha.txt", 50)
        self.assertListEqual(self.fh.file_search("a"), ["alpha.txt"])
        self.assertListEqual(self.fh.file_search(""), ["alpha.txt", "beta.txt"])

    def test_search_respects_prefix(self):
        self.fh.file_upload("docs/a.txt", 10)
        self.fh.file_upload("img/b.png", 20)
        self.assertListEqual(self.fh.file_search("docs/"), ["docs/a.txt"])

    def test_search_no_match_returns_empty_list(self):
        self.fh.file_upload("a.txt", 10)
        self.assertListEqual(self.fh.file_search("zzz"), [])

    def test_search_caps_at_ten(self):
        for i in range(15):
            self.fh.file_upload(f"f{i:02d}.txt", i)
        result = self.fh.file_search("f")
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], "f14.txt")
        self.assertEqual(result[-1], "f05.txt")


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.fh = FileHost()

    def test_upload_at_and_get_at(self):
        self.fh.file_upload_at(10, "a.txt", 100)
        self.assertEqual(self.fh.file_get_at(10, "a.txt"), 100)
        self.assertEqual(self.fh.file_get_at(10**9, "a.txt"), 100)

    def test_ttl_expiry_is_exclusive(self):
        self.fh.file_upload_at(10, "a.txt", 100, 5)
        self.assertEqual(self.fh.file_get_at(14, "a.txt"), 100)
        self.assertIsNone(self.fh.file_get_at(15, "a.txt"))
        self.assertIsNone(self.fh.file_get_at(16, "a.txt"))

    def test_level_one_methods_still_work(self):
        self.fh.file_upload("legacy.txt", 5)
        self.assertEqual(self.fh.file_get("legacy.txt"), 5)
        self.assertEqual(self.fh.file_get_at(10**9, "legacy.txt"), 5)

    def test_upload_over_expired_name_succeeds(self):
        self.fh.file_upload_at(0, "a.txt", 10, 5)
        self.fh.file_upload_at(5, "a.txt", 99)
        self.assertEqual(self.fh.file_get_at(5, "a.txt"), 99)

    def test_upload_over_living_name_raises(self):
        self.fh.file_upload_at(0, "a.txt", 10, 5)
        with self.assertRaises(RuntimeError):
            self.fh.file_upload_at(4, "a.txt", 99)

    def test_copy_inherits_absolute_expiry(self):
        self.fh.file_upload_at(0, "a.txt", 10, 10)
        self.fh.file_copy_at(9, "a.txt", "b.txt")
        self.assertEqual(self.fh.file_get_at(9, "b.txt"), 10)
        self.assertIsNone(self.fh.file_get_at(10, "b.txt"))

    def test_copy_of_expired_source_raises(self):
        self.fh.file_upload_at(0, "a.txt", 10, 5)
        with self.assertRaises(RuntimeError):
            self.fh.file_copy_at(5, "a.txt", "b.txt")

    def test_search_at_excludes_expired(self):
        self.fh.file_upload_at(0, "big.txt", 900, 5)
        self.fh.file_upload_at(0, "big2.txt", 100)
        self.assertListEqual(self.fh.file_search_at(4, "big"), ["big.txt", "big2.txt"])
        self.assertListEqual(self.fh.file_search_at(5, "big"), ["big2.txt"])


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.fh = FileHost()

    def test_upload_by_returns_remaining_capacity(self):
        self.fh.add_user(0, "alice", 1000)
        self.assertEqual(self.fh.file_upload_at_by(0, "alice", "a.txt", 400), 600)
        self.assertEqual(self.fh.file_upload_at_by(0, "alice", "b.txt", 100), 500)

    def test_add_user_returns_none_and_rejects_duplicates(self):
        self.assertIsNone(self.fh.add_user(0, "alice", 10))
        with self.assertRaises(RuntimeError):
            self.fh.add_user(1, "alice", 20)

    def test_upload_by_unknown_user_raises(self):
        with self.assertRaises(RuntimeError):
            self.fh.file_upload_at_by(0, "nobody", "a.txt", 1)

    def test_over_capacity_returns_none_and_does_not_upload(self):
        self.fh.add_user(0, "alice", 100)
        self.assertIsNone(self.fh.file_upload_at_by(0, "alice", "big.txt", 101))
        self.assertIsNone(self.fh.file_get_at(0, "big.txt"))
        self.assertEqual(self.fh.file_upload_at_by(0, "alice", "ok.txt", 100), 0)

    def test_expired_file_releases_quota(self):
        self.fh.add_user(0, "alice", 100)
        self.fh.file_upload_at_by(0, "alice", "temp.txt", 100, 5)
        self.assertIsNone(self.fh.file_upload_at_by(4, "alice", "next.txt", 1))
        self.assertEqual(self.fh.file_upload_at_by(5, "alice", "next.txt", 60), 40)

    def test_unowned_uploads_do_not_consume_quota(self):
        self.fh.add_user(0, "alice", 100)
        self.fh.file_upload_at(0, "free.txt", 5000)
        self.assertEqual(self.fh.file_upload_at_by(0, "alice", "a.txt", 100), 0)

    def test_copies_are_unowned(self):
        self.fh.add_user(0, "alice", 100)
        self.fh.file_upload_at_by(0, "alice", "a.txt", 100)
        self.fh.file_copy_at(0, "a.txt", "b.txt")
        # the copy belongs to nobody, so alice is charged for a.txt only
        self.fh.add_user(0, "bob", 50)
        self.assertEqual(self.fh.merge_user(0, "bob", "alice"), 50)

    def test_merge_sums_capacity_and_transfers_files(self):
        self.fh.add_user(0, "alice", 500)
        self.fh.add_user(0, "bob", 300)
        self.fh.file_upload_at_by(0, "alice", "a.txt", 200)
        self.fh.file_upload_at_by(0, "bob", "b.txt", 100)
        # alice: 500 + 300 capacity, 200 + 100 used
        self.assertEqual(self.fh.merge_user(1, "alice", "bob"), 500)
        with self.assertRaises(RuntimeError):
            self.fh.file_upload_at_by(1, "bob", "c.txt", 1)
        self.assertEqual(self.fh.file_get_at(1, "b.txt"), 100)

    def test_merge_rejects_unknown_or_identical_users(self):
        self.fh.add_user(0, "alice", 10)
        with self.assertRaises(RuntimeError):
            self.fh.merge_user(0, "alice", "alice")
        with self.assertRaises(RuntimeError):
            self.fh.merge_user(0, "alice", "ghost")


class TestLevel5(unittest.TestCase):
    def setUp(self):
        self.fh = FileHost()

    def test_rollback_removes_later_uploads(self):
        self.fh.file_upload_at(10, "a.txt", 1)
        self.fh.file_upload_at(20, "b.txt", 2)
        self.assertIsNone(self.fh.rollback(15))
        self.assertEqual(self.fh.file_get_at(30, "a.txt"), 1)
        self.assertIsNone(self.fh.file_get_at(30, "b.txt"))

    def test_rollback_lands_on_an_exact_operation_timestamp(self):
        self.fh.file_upload_at(10, "a.txt", 1)
        self.fh.file_upload_at(20, "b.txt", 2)
        self.fh.rollback(20)
        self.assertEqual(self.fh.file_get_at(30, "b.txt"), 2)

    def test_rollback_before_any_operation_empties_everything(self):
        self.fh.file_upload_at(10, "a.txt", 1)
        self.fh.rollback(0)
        self.assertIsNone(self.fh.file_get_at(30, "a.txt"))
        self.assertListEqual(self.fh.file_search_at(30, ""), [])

    def test_rollback_preserves_absolute_expiry(self):
        self.fh.file_upload_at(0, "a.txt", 1, 100)
        self.fh.file_upload_at(50, "b.txt", 2)
        self.fh.rollback(60)
        self.assertEqual(self.fh.file_get_at(99, "a.txt"), 1)
        self.assertIsNone(self.fh.file_get_at(100, "a.txt"))

    def test_rollback_covers_level_one_operations(self):
        self.fh.file_upload("legacy.txt", 5)
        self.fh.file_upload_at(10, "new.txt", 5)
        self.fh.rollback(5)
        self.assertEqual(self.fh.file_get("legacy.txt"), 5)
        self.assertIsNone(self.fh.file_get_at(10, "new.txt"))

    def test_rollback_undoes_users_and_merges(self):
        self.fh.add_user(0, "alice", 100)
        self.fh.add_user(0, "bob", 100)
        self.fh.file_upload_at_by(1, "bob", "b.txt", 40)
        self.fh.merge_user(5, "alice", "bob")
        self.fh.rollback(4)
        self.assertEqual(self.fh.file_upload_at_by(6, "bob", "b2.txt", 60), 0)
        self.assertEqual(self.fh.file_upload_at_by(6, "alice", "a.txt", 100), 0)

    def test_rollback_truncates_history(self):
        self.fh.file_upload_at(10, "a.txt", 1)
        self.fh.file_upload_at(20, "b.txt", 2)
        self.fh.rollback(15)
        self.fh.rollback(100)
        self.assertIsNone(self.fh.file_get_at(200, "b.txt"))
        self.assertEqual(self.fh.file_get_at(200, "a.txt"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
