# Mock 4 — Build System

> **Read one level at a time.** Implement `BuildSystem` in `solution.py`.
> `./run.sh 1` … `./run.sh 5`. Where this document and the tests disagree,
> **the tests win**.

You are implementing the scheduler for a build system. Tasks have a duration and
may depend on other tasks. All state is in memory. Durations and times are
non-negative integers; the build starts at time `0`.

---

## Level 1 — Initial design & basic functions

- `add_task(task_id, duration)`
  - Returns `True`, or `False` if a task with that id already exists.
- `add_dependency(task_id, depends_on)`
  - Declares that `task_id` cannot start until `depends_on` has finished.
  - Returns `True` on success, and `False` if any of the following hold: either
    task does not exist, the two ids are equal, the dependency has already been
    declared, or adding it would create a cycle.
- `get_duration(task_id)`
  - Returns the task's duration, or `None` if the task does not exist.

---

## Level 2 — Data structures & data processing

- `list_tasks(prefix)`
  - Returns at most **10** task ids beginning with `prefix`, ordered by duration
    descending, ties by task id ascending. `[]` if nothing matches.

---

## Level 3 — Scheduling

- `run_order()`
  - Returns every task id in an order in which they could be executed one at a
    time: no task appears before any task it depends on.
  - Ties are broken deterministically: whenever more than one task is eligible to
    run next, the one with the smallest id goes first.
  - Returns `[]` when there are no tasks.
- `earliest_finish(task_id)`
  - The earliest time this task can be finished, assuming the build starts at
    time `0` and unlimited tasks may run at once. Returns `None` if the task does
    not exist.

---

## Level 4 — Caching

A cached task's output is already on disk, so it takes **zero** time to "run". It
still appears in `run_order` and still gates its dependents.

- `mark_cached(task_id)`
  - Marks the task cached. Returns `True`, or `False` if the task does not exist
    or was already cached.
- `invalidate(task_id)`
  - Clears the cache on `task_id` and on every task that transitively depends on
    it — editing a source file invalidates everything downstream of it.
  - Returns the ids that were actually cached and are now not, sorted ascending.
    Returns `[]` if the task does not exist or nothing was cached.

`earliest_finish` must account for caching.

---

## Level 5 — Parallel execution

- `run_parallel(workers)`
  - Returns the time at which the whole build finishes when run on `workers`
    identical machines, under this exact scheduling rule:
    - The build starts at time `0`.
    - A task is *ready* once every task it depends on has finished.
    - Whenever a worker is free and at least one ready task is unstarted, the
      ready task with the smallest id is started immediately on that worker.
    - A task started at time `t` occupies its worker until `t + duration`
      (`t + 0` for a cached task, which frees the worker in the same instant).
  - Returns `0` when there are no tasks. `workers` is at least 1.
