"""Mock 6 tests. The tests are the spec."""

import unittest

from solution import FileSystem


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_mkdir_creates_and_rejects_duplicates(self):
        self.assertTrue(self.fs.mkdir("/docs"))
        self.assertFalse(self.fs.mkdir("/docs"))

    def test_mkdir_requires_an_existing_parent(self):
        self.assertFalse(self.fs.mkdir("/a/b"))
        self.assertTrue(self.fs.mkdir("/a"))
        self.assertTrue(self.fs.mkdir("/a/b"))

    def test_write_file_and_get_size(self):
        self.assertTrue(self.fs.write_file("/report.txt", 10))
        self.assertEqual(self.fs.get_size("/report.txt"), 10)

    def test_write_file_overwrites(self):
        self.fs.write_file("/report.txt", 10)
        self.assertTrue(self.fs.write_file("/report.txt", 3))
        self.assertEqual(self.fs.get_size("/report.txt"), 3)

    def test_write_file_rejects_bad_paths(self):
        self.assertFalse(self.fs.write_file("/a/f.txt", 1))
        self.fs.mkdir("/a")
        self.assertFalse(self.fs.write_file("/a", 5))

    def test_get_size_of_a_directory_sums_the_subtree(self):
        self.fs.mkdir("/a")
        self.fs.mkdir("/a/b")
        self.fs.write_file("/a/f.txt", 3)
        self.fs.write_file("/a/b/g.txt", 4)
        self.assertEqual(self.fs.get_size("/a"), 7)
        self.assertEqual(self.fs.get_size("/a/b"), 4)
        self.assertEqual(self.fs.get_size("/"), 7)

    def test_missing_paths_and_the_root(self):
        self.assertIsNone(self.fs.get_size("/nope"))
        self.assertFalse(self.fs.mkdir("/"))
        self.assertEqual(self.fs.get_size("/"), 0)


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_ls_returns_sorted_child_names(self):
        self.fs.mkdir("/a")
        self.fs.write_file("/a/c.txt", 1)
        self.fs.write_file("/a/b.txt", 1)
        self.fs.mkdir("/a/d")
        self.assertListEqual(self.fs.ls("/a"), ["b.txt", "c.txt", "d"])

    def test_ls_of_an_empty_directory(self):
        self.fs.mkdir("/a")
        self.assertListEqual(self.fs.ls("/a"), [])

    def test_ls_of_a_file_or_a_missing_path(self):
        self.fs.write_file("/f.txt", 1)
        self.assertIsNone(self.fs.ls("/f.txt"))
        self.assertIsNone(self.fs.ls("/nope"))

    def test_ls_is_not_recursive(self):
        self.fs.mkdir("/a")
        self.fs.mkdir("/a/b")
        self.fs.write_file("/a/b/deep.txt", 1)
        self.assertListEqual(self.fs.ls("/a"), ["b"])

    def test_ls_of_the_root(self):
        self.fs.mkdir("/a")
        self.fs.write_file("/f.txt", 1)
        self.assertListEqual(self.fs.ls("/"), ["a", "f.txt"])

    def test_largest_files_orders_by_size_descending(self):
        self.fs.write_file("/a.txt", 5)
        self.fs.write_file("/b.txt", 9)
        self.fs.write_file("/c.txt", 1)
        self.assertListEqual(
            self.fs.largest_files("/", 10), ["/b.txt(9)", "/a.txt(5)", "/c.txt(1)"]
        )

    def test_largest_files_ties_limit_and_scope(self):
        self.fs.mkdir("/d")
        self.fs.write_file("/d/y.txt", 5)
        self.fs.write_file("/d/x.txt", 5)
        self.fs.write_file("/d/z.txt", 9)
        self.fs.write_file("/outside.txt", 100)
        self.assertListEqual(
            self.fs.largest_files("/d", 2), ["/d/z.txt(9)", "/d/x.txt(5)"]
        )
        self.assertListEqual(self.fs.largest_files("/d/z.txt", 5), [])


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_write_file_by_sets_the_owner(self):
        self.assertTrue(self.fs.write_file_by("alice", "/f.txt", 10))
        self.assertEqual(self.fs.get_usage("alice"), 10)

    def test_get_usage_for_an_unknown_user(self):
        self.assertEqual(self.fs.get_usage("nobody"), 0)

    def test_quota_blocks_an_oversized_write(self):
        self.assertTrue(self.fs.set_quota("alice", 10))
        self.assertFalse(self.fs.write_file_by("alice", "/f.txt", 11))
        self.assertIsNone(self.fs.get_size("/f.txt"))

    def test_a_write_that_exactly_fills_the_quota(self):
        self.fs.set_quota("alice", 10)
        self.assertTrue(self.fs.write_file_by("alice", "/f.txt", 10))
        self.assertFalse(self.fs.write_file_by("alice", "/g.txt", 1))

    def test_set_quota_below_current_usage_fails(self):
        self.fs.write_file_by("alice", "/f.txt", 10)
        self.assertFalse(self.fs.set_quota("alice", 5))
        self.assertTrue(self.fs.write_file_by("alice", "/g.txt", 1))

    def test_overwriting_transfers_ownership(self):
        self.fs.write_file_by("alice", "/f.txt", 10)
        self.assertTrue(self.fs.write_file_by("bob", "/f.txt", 4))
        self.assertEqual(self.fs.get_usage("alice"), 0)
        self.assertEqual(self.fs.get_usage("bob"), 4)

    def test_root_is_never_limited(self):
        self.assertTrue(self.fs.write_file("/big.bin", 10**9))
        self.assertEqual(self.fs.get_usage("root"), 10**9)

    def test_a_quota_counts_only_its_own_users_files(self):
        self.fs.set_quota("alice", 10)
        self.assertTrue(self.fs.write_file_by("bob", "/b.txt", 100))
        self.assertTrue(self.fs.write_file_by("alice", "/a.txt", 10))


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_delete_a_file(self):
        self.fs.write_file("/f.txt", 5)
        self.assertEqual(self.fs.delete("/f.txt"), 1)
        self.assertIsNone(self.fs.get_size("/f.txt"))

    def test_delete_a_directory_removes_the_subtree(self):
        self.fs.mkdir("/a")
        self.fs.mkdir("/a/b")
        self.fs.write_file("/a/f.txt", 1)
        self.fs.write_file("/a/b/g.txt", 1)
        self.assertEqual(self.fs.delete("/a"), 2)
        self.assertIsNone(self.fs.get_size("/a"))
        self.assertListEqual(self.fs.ls("/"), [])

    def test_delete_a_missing_path_or_the_root(self):
        self.assertIsNone(self.fs.delete("/nope"))
        self.assertIsNone(self.fs.delete("/"))

    def test_delete_frees_quota_usage(self):
        self.fs.set_quota("alice", 10)
        self.fs.write_file_by("alice", "/f.txt", 10)
        self.assertEqual(self.fs.delete("/f.txt"), 1)
        self.assertEqual(self.fs.get_usage("alice"), 0)
        self.assertTrue(self.fs.write_file_by("alice", "/g.txt", 10))

    def test_move_a_file(self):
        self.fs.write_file("/f.txt", 5)
        self.fs.mkdir("/d")
        self.assertTrue(self.fs.move("/f.txt", "/d/f.txt"))
        self.assertEqual(self.fs.get_size("/d/f.txt"), 5)
        self.assertIsNone(self.fs.get_size("/f.txt"))

    def test_move_a_directory_takes_the_subtree(self):
        self.fs.mkdir("/a")
        self.fs.mkdir("/a/b")
        self.fs.write_file("/a/b/g.txt", 7)
        self.fs.mkdir("/dst")
        self.assertTrue(self.fs.move("/a", "/dst/a"))
        self.assertEqual(self.fs.get_size("/dst/a"), 7)
        self.assertEqual(self.fs.get_size("/dst/a/b/g.txt"), 7)
        self.assertListEqual(self.fs.ls("/"), ["dst"])

    def test_move_rejects_bad_arguments(self):
        self.fs.write_file("/f.txt", 1)
        self.fs.write_file("/g.txt", 1)
        self.assertFalse(self.fs.move("/nope", "/x.txt"))
        self.assertFalse(self.fs.move("/f.txt", "/g.txt"))
        self.assertFalse(self.fs.move("/f.txt", "/missing/x.txt"))
        self.assertFalse(self.fs.move("/", "/x"))

    def test_move_a_directory_into_itself(self):
        self.fs.mkdir("/a")
        self.fs.mkdir("/a/b")
        self.assertFalse(self.fs.move("/a", "/a/b/c"))


class TestLevel5(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_disk_usage_without_hashes(self):
        self.fs.write_file("/a.txt", 5)
        self.fs.write_file("/b.txt", 3)
        self.assertEqual(self.fs.disk_usage(), 8)

    def test_identical_hashes_are_stored_once(self):
        self.fs.write_file_with_hash("u", "/a.txt", 5, "h1")
        self.fs.write_file_with_hash("u", "/b.txt", 5, "h1")
        self.assertEqual(self.fs.disk_usage(), 5)

    def test_different_hashes_are_stored_separately(self):
        self.fs.write_file_with_hash("u", "/a.txt", 5, "h1")
        self.fs.write_file_with_hash("u", "/b.txt", 3, "h2")
        self.assertEqual(self.fs.disk_usage(), 8)

    def test_deleting_one_copy_keeps_the_bytes(self):
        self.fs.write_file_with_hash("u", "/a.txt", 5, "h1")
        self.fs.write_file_with_hash("u", "/b.txt", 5, "h1")
        self.fs.delete("/a.txt")
        self.assertEqual(self.fs.disk_usage(), 5)

    def test_deleting_every_copy_frees_the_bytes(self):
        self.fs.write_file_with_hash("u", "/a.txt", 5, "h1")
        self.fs.write_file_with_hash("u", "/b.txt", 5, "h1")
        self.fs.delete("/a.txt")
        self.fs.delete("/b.txt")
        self.assertEqual(self.fs.disk_usage(), 0)

    def test_quotas_count_logical_bytes_not_stored_bytes(self):
        self.fs.set_quota("u", 9)
        self.assertTrue(self.fs.write_file_with_hash("u", "/a.txt", 5, "h1"))
        self.assertFalse(self.fs.write_file_with_hash("u", "/b.txt", 5, "h1"))
        self.assertEqual(self.fs.disk_usage(), 5)

    def test_hashed_and_unhashed_files_mix(self):
        self.fs.write_file("/plain.txt", 4)
        self.fs.write_file_with_hash("u", "/a.txt", 5, "h1")
        self.fs.write_file_with_hash("u", "/b.txt", 5, "h1")
        self.assertEqual(self.fs.disk_usage(), 9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
