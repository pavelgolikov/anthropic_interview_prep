"""Mock 4 tests. The tests are the spec."""

import unittest

from solution import BuildSystem


def chain(bs, *pairs):
    """Helper: add tasks given as (id, duration) pairs."""
    for task_id, duration in pairs:
        bs.add_task(task_id, duration)


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.bs = BuildSystem()

    def test_add_task(self):
        self.assertTrue(self.bs.add_task("compile", 5))
        self.assertFalse(self.bs.add_task("compile", 9))
        self.assertEqual(self.bs.get_duration("compile"), 5)

    def test_get_duration_missing(self):
        self.assertIsNone(self.bs.get_duration("nope"))

    def test_zero_duration_task(self):
        self.bs.add_task("noop", 0)
        self.assertEqual(self.bs.get_duration("noop"), 0)

    def test_add_dependency(self):
        chain(self.bs, ("a", 1), ("b", 1))
        self.assertTrue(self.bs.add_dependency("b", "a"))

    def test_dependency_requires_both_tasks(self):
        self.bs.add_task("a", 1)
        self.assertFalse(self.bs.add_dependency("b", "a"))
        self.assertFalse(self.bs.add_dependency("a", "b"))

    def test_self_dependency_rejected(self):
        self.bs.add_task("a", 1)
        self.assertFalse(self.bs.add_dependency("a", "a"))

    def test_duplicate_dependency_rejected(self):
        chain(self.bs, ("a", 1), ("b", 1))
        self.assertTrue(self.bs.add_dependency("b", "a"))
        self.assertFalse(self.bs.add_dependency("b", "a"))

    def test_direct_cycle_rejected(self):
        chain(self.bs, ("a", 1), ("b", 1))
        self.bs.add_dependency("b", "a")
        self.assertFalse(self.bs.add_dependency("a", "b"))

    def test_transitive_cycle_rejected(self):
        chain(self.bs, ("a", 1), ("b", 1), ("c", 1))
        self.bs.add_dependency("b", "a")
        self.bs.add_dependency("c", "b")
        self.assertFalse(self.bs.add_dependency("a", "c"))
        self.assertTrue(self.bs.add_dependency("c", "a"))


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.bs = BuildSystem()

    def test_orders_by_duration_desc(self):
        chain(self.bs, ("build_a", 3), ("build_b", 9), ("build_c", 5))
        self.assertListEqual(
            self.bs.list_tasks("build_"), ["build_b", "build_c", "build_a"]
        )

    def test_ties_by_id_asc(self):
        chain(self.bs, ("z", 5), ("a", 5))
        self.assertListEqual(self.bs.list_tasks(""), ["a", "z"])

    def test_prefix_filters(self):
        chain(self.bs, ("test_x", 1), ("build_y", 2))
        self.assertListEqual(self.bs.list_tasks("test_"), ["test_x"])
        self.assertListEqual(self.bs.list_tasks("zzz"), [])

    def test_caps_at_ten(self):
        chain(self.bs, *[(f"t{i:02d}", i) for i in range(20)])
        result = self.bs.list_tasks("t")
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], "t19")
        self.assertEqual(result[-1], "t10")


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.bs = BuildSystem()

    def test_run_order_empty(self):
        self.assertListEqual(self.bs.run_order(), [])

    def test_run_order_no_dependencies_is_sorted(self):
        chain(self.bs, ("c", 1), ("a", 1), ("b", 1))
        self.assertListEqual(self.bs.run_order(), ["a", "b", "c"])

    def test_run_order_respects_dependencies(self):
        chain(self.bs, ("link", 1), ("compile", 1), ("fetch", 1))
        self.bs.add_dependency("compile", "fetch")
        self.bs.add_dependency("link", "compile")
        self.assertListEqual(self.bs.run_order(), ["fetch", "compile", "link"])

    def test_run_order_tie_break_is_smallest_id(self):
        chain(self.bs, ("a", 1), ("b", 1), ("c", 1), ("d", 1))
        self.bs.add_dependency("b", "a")
        # after `a`, both `b` and `c` are eligible -> `b` first
        self.assertListEqual(self.bs.run_order(), ["a", "b", "c", "d"])

    def test_earliest_finish_chain(self):
        chain(self.bs, ("a", 3), ("b", 2), ("c", 4))
        self.bs.add_dependency("b", "a")
        self.assertEqual(self.bs.earliest_finish("a"), 3)
        self.assertEqual(self.bs.earliest_finish("b"), 5)
        self.assertEqual(self.bs.earliest_finish("c"), 4)

    def test_earliest_finish_takes_the_slowest_dependency(self):
        chain(self.bs, ("fast", 1), ("slow", 10), ("join", 2))
        self.bs.add_dependency("join", "fast")
        self.bs.add_dependency("join", "slow")
        self.assertEqual(self.bs.earliest_finish("join"), 12)

    def test_earliest_finish_missing_task(self):
        self.assertIsNone(self.bs.earliest_finish("nope"))


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.bs = BuildSystem()
        chain(self.bs, ("a", 3), ("b", 2), ("c", 4))
        self.bs.add_dependency("b", "a")
        self.bs.add_dependency("c", "b")

    def test_mark_cached(self):
        self.assertTrue(self.bs.mark_cached("a"))
        self.assertFalse(self.bs.mark_cached("a"))
        self.assertFalse(self.bs.mark_cached("nope"))

    def test_cached_task_costs_nothing(self):
        self.bs.mark_cached("a")
        self.assertEqual(self.bs.earliest_finish("a"), 0)
        self.assertEqual(self.bs.earliest_finish("b"), 2)
        self.assertEqual(self.bs.earliest_finish("c"), 6)

    def test_cached_tasks_still_appear_in_run_order(self):
        self.bs.mark_cached("a")
        self.assertListEqual(self.bs.run_order(), ["a", "b", "c"])

    def test_invalidate_cascades_downstream(self):
        for task in ("a", "b", "c"):
            self.bs.mark_cached(task)
        self.assertListEqual(self.bs.invalidate("b"), ["b", "c"])
        self.assertEqual(self.bs.earliest_finish("a"), 0)
        self.assertEqual(self.bs.earliest_finish("c"), 6)

    def test_invalidate_does_not_touch_upstream(self):
        self.bs.mark_cached("a")
        self.bs.mark_cached("c")
        self.assertListEqual(self.bs.invalidate("c"), ["c"])
        self.assertEqual(self.bs.earliest_finish("a"), 0)

    def test_invalidate_reports_only_what_was_cached(self):
        self.bs.mark_cached("c")
        self.assertListEqual(self.bs.invalidate("a"), ["c"])
        self.assertListEqual(self.bs.invalidate("a"), [])

    def test_invalidate_missing_task(self):
        self.assertListEqual(self.bs.invalidate("nope"), [])

    def test_mark_cached_again_after_invalidate(self):
        self.bs.mark_cached("a")
        self.bs.invalidate("a")
        self.assertTrue(self.bs.mark_cached("a"))


class TestLevel5(unittest.TestCase):
    def setUp(self):
        self.bs = BuildSystem()

    def test_no_tasks(self):
        self.assertEqual(self.bs.run_parallel(4), 0)

    def test_single_worker_is_the_total_duration(self):
        chain(self.bs, ("a", 3), ("b", 2), ("c", 4))
        self.assertEqual(self.bs.run_parallel(1), 9)

    def test_independent_tasks_share_workers(self):
        chain(self.bs, ("a", 3), ("b", 2), ("c", 4))
        # t=0 start a(->3) and b(->2); t=2 b frees, start c(->6)
        self.assertEqual(self.bs.run_parallel(2), 6)

    def test_more_workers_than_tasks(self):
        chain(self.bs, ("a", 3), ("b", 2), ("c", 4))
        self.assertEqual(self.bs.run_parallel(10), 4)

    def test_dependencies_serialise_the_build(self):
        chain(self.bs, ("a", 3), ("b", 2), ("c", 4))
        self.bs.add_dependency("b", "a")
        # t=0: a(->3) and c(->4); t=3: b starts (->5)
        self.assertEqual(self.bs.run_parallel(2), 5)

    def test_smallest_ready_id_wins_a_free_worker(self):
        chain(self.bs, ("a", 1), ("b", 100), ("c", 1))
        self.assertEqual(self.bs.run_parallel(1), 102)
        self.assertEqual(self.bs.run_parallel(2), 100)

    def test_cached_tasks_take_no_time_and_free_the_worker(self):
        chain(self.bs, ("a", 5), ("b", 5), ("c", 5))
        self.bs.mark_cached("a")
        self.bs.mark_cached("b")
        self.assertEqual(self.bs.run_parallel(1), 5)

    def test_cached_dependency_unblocks_immediately(self):
        chain(self.bs, ("a", 100), ("b", 7))
        self.bs.add_dependency("b", "a")
        self.bs.mark_cached("a")
        self.assertEqual(self.bs.run_parallel(1), 7)

    def test_diamond(self):
        chain(self.bs, ("a", 2), ("b", 5), ("c", 3), ("d", 1))
        self.bs.add_dependency("b", "a")
        self.bs.add_dependency("c", "a")
        self.bs.add_dependency("d", "b")
        self.bs.add_dependency("d", "c")
        # a finishes at 2; b(->7) and c(->5) run in parallel; d needs both -> 8
        self.assertEqual(self.bs.run_parallel(2), 8)
        # one worker: a(2), b(7), c(10), d(11)
        self.assertEqual(self.bs.run_parallel(1), 11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
