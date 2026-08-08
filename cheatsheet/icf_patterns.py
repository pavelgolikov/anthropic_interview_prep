"""
The eight primitives that compose essentially every Industry-Coding-Framework problem.

Read this once, then close it and re-implement each one from a blank file. That
recall drill is worth more than reading it five times.

Run:  python3 cheatsheet/icf_patterns.py
"""

import copy
from bisect import bisect_right
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# 1. RECORD-AS-DICT  --  the single decision that decides whether L3 hurts
# ---------------------------------------------------------------------------
# BAD: the value is a bare scalar. When L3 says "files now have an owner and a
#      TTL", every read site in your code has to change.
#
#   self.files[name] = size
#
# GOOD: the value is a record. L3 becomes `rec["ttl"] = ttl`.
#
#   self.files[name] = {"size": size}
#
# Cost at L1: 8 characters. Payoff at L3: you keep your job.


class Store:
    """Minimal shape to start EVERY one of these problems with."""

    def __init__(self):
        self.items = {}  # id -> {"field": value, ...}

    def put(self, key, size):
        if key in self.items:
            return False
        self.items[key] = {"size": size}  # <- record, not scalar
        return True


# ---------------------------------------------------------------------------
# 2. THE _at() DELEGATION TRICK  --  makes L3 a 3-line change
# ---------------------------------------------------------------------------
# L1 hands you `set(key, value)`. L3 hands you `set_at(timestamp, key, value)`
# and says the old one must keep working.
#
# Do NOT write the logic twice. Write it ONCE in the timestamped version, and
# make the plain version a delegate. If you did this at L1 (with timestamp=0),
# L3 costs you nothing at all.


class Timed:
    def __init__(self):
        self.data = {}

    # the real implementation lives here
    def set_at(self, timestamp, key, value):
        self.data[key] = {"value": value, "at": timestamp}
        return True

    # the L1 signature survives untouched, forever
    def set(self, key, value):
        return self.set_at(0, key, value)


# ---------------------------------------------------------------------------
# 3. TTL / EXPIRY  --  store the ABSOLUTE expiry, never the relative ttl
# ---------------------------------------------------------------------------
# Storing `ttl` forces you to remember the creation time at every read.
# Storing `expires_at = timestamp + ttl` makes every read a single comparison.
# Use None for "lives forever" and let the alive check short-circuit.


class TTLStore:
    def __init__(self):
        self.data = {}  # key -> {"value": v, "expires_at": int | None}

    def set_at(self, timestamp, key, value, ttl=None):
        self.data[key] = {
            "value": value,
            "expires_at": None if ttl is None else timestamp + ttl,
        }

    def _alive(self, rec, timestamp):
        # convention: expires_at is EXCLUSIVE (dead exactly at expires_at).
        # Whichever convention the tests use, pick it once and use this ONE
        # helper everywhere -- then flipping it is a one-character fix.
        return rec["expires_at"] is None or timestamp < rec["expires_at"]

    def get_at(self, timestamp, key):
        rec = self.data.get(key)
        if rec is None or not self._alive(rec, timestamp):
            return None
        return rec["value"]

    def alive_items(self, timestamp):
        """Lazy expiry: never delete on a timer, just filter on read."""
        return {k: r for k, r in self.data.items() if self._alive(r, timestamp)}


# ---------------------------------------------------------------------------
# 4. TOP-K WITH TIE-BREAK  --  the L2 mechanic, near-universally present
# ---------------------------------------------------------------------------
# You almost never need heapq here. n is small and "sort by X desc, ties by
# name asc" is one composite key. Negate numerics to flip only that field.


def top_k(records, k=10):
    """records: iterable of (name, size). Size desc, then name asc."""
    return [name for name, _ in sorted(records, key=lambda p: (-p[1], p[0]))[:k]]


# Formatting the result is where points quietly leak. Read the expected string
# in the test character by character:  "alice(120)"  vs  "alice: 120".
def fmt(pairs):
    return [f"{name}({value})" for name, value in pairs]


# ---------------------------------------------------------------------------
# 5. PREFIX SEARCH  --  do not build a trie
# ---------------------------------------------------------------------------
# str.startswith over the whole dict is O(n) and completely fine. A trie costs
# you 20 minutes and buys performance that is explicitly not graded.


def search_prefix(items, prefix):
    return [k for k in items if k.startswith(prefix)]


# ---------------------------------------------------------------------------
# 6. SNAPSHOT / ROLLBACK / BACKUP-RESTORE  --  the classic L4
# ---------------------------------------------------------------------------
# Two viable strategies. Pick by whether rollback targets an ARBITRARY time
# (strategy A) or an EXPLICITLY saved point (strategy B).
#
# A) Snapshot after every mutation. Rollback = binary-search the log.
#    Costs memory, costs nothing in thinking time. Efficiency is not graded.
# B) backup(t) saves on demand; restore(t) reloads the latest backup <= t.
#
# The prerequisite for both: every mutation must funnel through one place.


class Snapshotting:
    def __init__(self):
        self.data = {}
        self._times = []  # sorted timestamps
        self._snaps = []  # parallel list of deep copies

    def _commit(self, timestamp):
        """Call at the END of every mutating public method. That's the whole trick."""
        if self._times and self._times[-1] == timestamp:
            self._snaps[-1] = copy.deepcopy(self.data)
        else:
            self._times.append(timestamp)
            self._snaps.append(copy.deepcopy(self.data))

    def set_at(self, timestamp, key, value):
        self.data[key] = {"value": value}
        self._commit(timestamp)

    def rollback(self, timestamp):
        """Restore the state as of `timestamp` (latest snapshot at or before it)."""
        i = bisect_right(self._times, timestamp) - 1
        self.data = copy.deepcopy(self._snaps[i]) if i >= 0 else {}
        # Careful: after restoring, decide whether the history log itself is
        # truncated. Tests will tell you. Truncating is the usual reading:
        del self._times[i + 1:]
        del self._snaps[i + 1:]

    # TTL + rollback interact. If the tests say "ttls are recalculated", they
    # normally mean: a restored record keeps the REMAINING lifetime it had at
    # the snapshot instant, re-based on the restore instant:
    #     new_expiry = restore_time + (old_expiry - snapshot_time)
    # Read the test. State your assumption in a comment and move on.


# ---------------------------------------------------------------------------
# 7. DEFERRED / SCHEDULED EVENTS  --  "cashback lands 24h later"
# ---------------------------------------------------------------------------
# There is no clock. Time only advances when a public method is called with a
# timestamp. So: every public method starts by draining everything that became
# due at or before `timestamp`, in scheduled order.
#
# Keep pending events in a plain list and sort on drain. n is tiny.


class Deferred:
    def __init__(self):
        self.balances = defaultdict(int)
        self.pending = []  # [{"due": ts, "seq": n, "account": a, "amount": v}]
        self._seq = 0

    def _advance(self, timestamp):
        """FIRST LINE of every public method. Idempotent, cheap, saves you."""
        due = [e for e in self.pending if e["due"] <= timestamp]
        self.pending = [e for e in self.pending if e["due"] > timestamp]
        for e in sorted(due, key=lambda e: (e["due"], e["seq"])):
            self.balances[e["account"]] += e["amount"]

    def schedule(self, timestamp, account, amount, delay):
        self._advance(timestamp)
        self._seq += 1
        self.pending.append(
            {"due": timestamp + delay, "seq": self._seq, "account": account, "amount": amount}
        )

    def balance(self, timestamp, account):
        self._advance(timestamp)
        return self.balances[account]


# ---------------------------------------------------------------------------
# 8. MERGE TWO ENTITIES  --  the other classic L4
# ---------------------------------------------------------------------------
# "merge b into a, then b ceases to exist." The bug everyone ships is forgetting
# one of the derived aggregates. Before writing it, LIST every field that lives
# on the entity, then handle each one explicitly:
#
#   balance          -> sum
#   total_outgoing   -> sum          (aggregates you keep for top-K!)
#   owned_items      -> reassign owner on each item, then union
#   pending events   -> retarget every queued event pointing at b
#   history/log      -> concatenate, keep sorted by time
#   the id itself    -> often must stay queryable under BOTH ids
#
# Write that list as comments first, then fill each in. It is a checklist
# problem, not a thinking problem, and checklists are where speed comes from.


# ---------------------------------------------------------------------------
# 9. BONUS: DETERMINISTIC TOPOLOGICAL ORDER  --  for build/package variants
# ---------------------------------------------------------------------------
# Ties must break deterministically or the test fails intermittently. Sort the
# ready set, or use a sorted queue. Cycle detection = "did I emit every node?"


def topo_order(nodes, deps):
    """nodes: iterable of ids. deps: id -> set of prerequisite ids.
    Returns a list in dependency order, ties by id asc, or None if cyclic."""
    indeg = {n: len(deps.get(n, ())) for n in nodes}
    dependents = defaultdict(set)
    for n in nodes:
        for p in deps.get(n, ()):
            dependents[p].add(n)

    ready = sorted(n for n, d in indeg.items() if d == 0)
    out = []
    while ready:
        n = ready.pop(0)  # smallest id first -> deterministic
        out.append(n)
        for m in sorted(dependents[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
        ready.sort()
    return out if len(out) == len(indeg) else None


# ---------------------------------------------------------------------------
# Smoke test -- confirms every snippet above actually runs.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    s = Store()
    assert s.put("a", 10) and not s.put("a", 20)

    t = Timed()
    t.set("k", 1)
    assert t.data["k"] == {"value": 1, "at": 0}

    ttl = TTLStore()
    ttl.set_at(10, "k", "v", ttl=5)
    assert ttl.get_at(14, "k") == "v"
    assert ttl.get_at(15, "k") is None
    ttl.set_at(10, "forever", "v")
    assert ttl.get_at(10**9, "forever") == "v"

    assert top_k([("b", 5), ("a", 5), ("c", 9)], 2) == ["c", "a"]
    assert fmt([("alice", 120)]) == ["alice(120)"]
    assert search_prefix({"foo": 1, "fob": 1, "bar": 1}, "fo") == ["foo", "fob"]

    snap = Snapshotting()
    snap.set_at(1, "a", 1)
    snap.set_at(2, "b", 2)
    snap.rollback(1)
    assert set(snap.data) == {"a"}

    d = Deferred()
    d.schedule(0, "acc", 100, delay=10)
    assert d.balance(9, "acc") == 0
    assert d.balance(10, "acc") == 100

    assert topo_order(["a", "b", "c"], {"b": {"a"}, "c": {"a"}}) == ["a", "b", "c"]
    assert topo_order(["a", "b"], {"a": {"b"}, "b": {"a"}}) is None

    print("all patterns OK")
