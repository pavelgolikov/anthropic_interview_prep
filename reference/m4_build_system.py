"""Mock 4 reference solution — Build System.

Read this only AFTER your own attempt. What to look for:

  * Two adjacency maps, `deps` and `dependents`, maintained together on every
    edge insert. Keeping both costs one line at Level 1 and saves you from
    writing a reverse traversal at Levels 3, 4 and 5.
  * `_effective_duration` is the single place caching touches the schedule, so
    Level 4 does not reach into Level 3's code at all.
  * `run_order` and `run_parallel` share the same skeleton: maintain a sorted
    `ready` list, always take the smallest id. Sorting the ready set is what
    makes ties deterministic — a plain `set` here fails intermittently.
  * `earliest_finish` recomputes from scratch every call. Memoising across calls
    would be wrong the moment `mark_cached` runs, and nothing here is graded on
    speed.

~110 lines.
"""

from bisect import insort
from heapq import heappop, heappush


class BuildSystem:
    def __init__(self):
        self.tasks = {}  # task_id -> {"duration": int, "cached": bool}
        self.deps = {}  # task_id -> set of prerequisites
        self.dependents = {}  # task_id -> set of tasks that require it

    # ------------------------------------------------------------------ helpers
    def _effective_duration(self, task_id):
        task = self.tasks[task_id]
        return 0 if task["cached"] else task["duration"]

    def _depends_on(self, task_id, target):
        """Does `task_id` transitively depend on `target`?"""
        stack, seen = [task_id], set()
        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.deps[current])
        return False

    # ------------------------------------------------------------------ level 1
    def add_task(self, task_id, duration):
        if task_id in self.tasks:
            return False
        self.tasks[task_id] = {"duration": duration, "cached": False}
        self.deps[task_id] = set()
        self.dependents[task_id] = set()
        return True

    def add_dependency(self, task_id, depends_on):
        if task_id == depends_on:
            return False
        if task_id not in self.tasks or depends_on not in self.tasks:
            return False
        if depends_on in self.deps[task_id]:
            return False
        if self._depends_on(depends_on, task_id):  # would close a cycle
            return False
        self.deps[task_id].add(depends_on)
        self.dependents[depends_on].add(task_id)
        return True

    def get_duration(self, task_id):
        task = self.tasks.get(task_id)
        return None if task is None else task["duration"]

    # ------------------------------------------------------------------ level 2
    def list_tasks(self, prefix):
        hits = [
            (task_id, task["duration"])
            for task_id, task in self.tasks.items()
            if task_id.startswith(prefix)
        ]
        hits.sort(key=lambda pair: (-pair[1], pair[0]))
        return [task_id for task_id, _ in hits[:10]]

    # ------------------------------------------------------------------ level 3
    def run_order(self):
        pending = {t: len(self.deps[t]) for t in self.tasks}
        ready = sorted(t for t, n in pending.items() if n == 0)
        order = []
        while ready:
            task_id = ready.pop(0)  # smallest id -> deterministic ties
            order.append(task_id)
            for child in self.dependents[task_id]:
                pending[child] -= 1
                if pending[child] == 0:
                    insort(ready, child)
        return order

    def earliest_finish(self, task_id):
        if task_id not in self.tasks:
            return None
        finished = {}

        def resolve(current):
            if current not in finished:
                start = max((resolve(p) for p in self.deps[current]), default=0)
                finished[current] = start + self._effective_duration(current)
            return finished[current]

        return resolve(task_id)

    # ------------------------------------------------------------------ level 4
    def mark_cached(self, task_id):
        task = self.tasks.get(task_id)
        if task is None or task["cached"]:
            return False
        task["cached"] = True
        return True

    def invalidate(self, task_id):
        if task_id not in self.tasks:
            return []
        cleared, stack, seen = [], [task_id], set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            if self.tasks[current]["cached"]:
                self.tasks[current]["cached"] = False
                cleared.append(current)
            stack.extend(self.dependents[current])
        return sorted(cleared)

    # ------------------------------------------------------------------ level 5
    def run_parallel(self, workers):
        pending = {t: len(self.deps[t]) for t in self.tasks}
        ready = sorted(t for t, n in pending.items() if n == 0)
        running = []  # min-heap of (finish_time, task_id)
        free = workers
        now = 0
        remaining = len(self.tasks)

        while remaining:
            while free and ready:
                task_id = ready.pop(0)
                heappush(running, (now + self._effective_duration(task_id), task_id))
                free -= 1
            if not running:
                break  # unreachable for a DAG
            now = running[0][0]
            while running and running[0][0] == now:
                _, task_id = heappop(running)
                free += 1
                remaining -= 1
                for child in self.dependents[task_id]:
                    pending[child] -= 1
                    if pending[child] == 0:
                        insort(ready, child)
        return now
