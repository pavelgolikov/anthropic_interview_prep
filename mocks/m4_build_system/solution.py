"""Mock 4 — Build System.  Implement BuildSystem here."""

from collections import deque
import heapq

class BuildSystem:
    def __init__(self):
        self.tasks = {} # task_id: {"duration": duration, "dependencies": [task_ids]}
        self.rev_deps = {}  # task_id: [list of tasks that depend on us]

    def _can_reach(self, src, dst):
        stack = []
        seen = set()
        stack.append(src)
        while stack:
            el = stack.pop()
            if el in seen:
                continue
            if el == dst:
                return True
            stack += self.tasks[el]['dependencies']
            seen.add(el)
        return False
    
    def top_sort(self):
        res = []
        in_degress = {k: len(v['dependencies']) for k, v in self.tasks.items()}
        heap = [k for k, d in in_degress.items() if d == 0]
        heapq.heapify(heap)
        while heap:
            el = heapq.heappop(heap)
            for dep in self.rev_deps[el]:
                in_degress[dep] -= 1
                if in_degress[dep] == 0:
                    heapq.heappush(heap, dep)
            res.append(el)
        return res

    def add_task(self, task_id, duration):
        if task_id in self.tasks:
            return False
        self.tasks[task_id] = {"duration": duration, "dependencies": []}
        self.rev_deps[task_id] = []
        return True

    def add_dependency(self, task_id, depends_on):
        if task_id not in self.tasks or \
        depends_on not in self.tasks or \
        (task_id == depends_on) or \
        depends_on in self.tasks[task_id]['dependencies'] or \
        self._can_reach(depends_on, task_id):
            return False
        self.tasks[task_id]['dependencies'].append(depends_on)
        self.rev_deps[depends_on].append(task_id)
        return True

    def get_duration(self, task_id):
        if task_id not in self.tasks:
            return None
        return self.tasks[task_id]['duration']

    def list_tasks(self, prefix):
        pairs = [(-v['duration'], k) for k, v in self.tasks.items() if k.startswith(prefix)]
        sorted_pairs = sorted(pairs)
        sorted_pairs = [x[1] for x in sorted_pairs]
        return sorted_pairs[:10]
    
    def run_order(self):
        return self.top_sort()
    
    def earliest_finish(self, task_id):

        
        

# ## Level 3 — Scheduling

# - `run_order()`
#   - Returns every task id in an order in which they could be executed one at a
#     time: no task appears before any task it depends on.
#   - Ties are broken deterministically: whenever more than one task is eligible to
#     run next, the one with the smallest id goes first.
#   - Returns `[]` when there are no tasks.

# - `earliest_finish(task_id)`
#   - The earliest time this task can be finished, assuming the build starts at
#     time `0` and unlimited tasks may run at once. Returns `None` if the task does
#     not exist.
