# Python stdlib recall sheet

Only what actually comes up in ICF problems. If you have to look one of these up
mid-assessment, that is 60 seconds you do not have. Read it out loud once on Day 5.

## collections

```python
from collections import defaultdict, Counter, deque, OrderedDict

d = defaultdict(int)          # d[k] += 1 with no guard
d = defaultdict(list)         # d[k].append(x)
d = defaultdict(dict)         # nested: d[key][field] = value   <- the ICF workhorse
d = defaultdict(lambda: defaultdict(int))

Counter(words).most_common(3)     # [(item, count), ...] -- but ties are by
                                  # insertion order, NOT alphabetical. Almost
                                  # every test wants alphabetical ties, so:
sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:3]

q = deque(); q.append(x); q.popleft()       # BFS
od = OrderedDict(); od.move_to_end(k)       # LRU
```

## Sorting — the composite key

```python
sorted(xs, key=lambda x: (-x["size"], x["name"]))      # size desc, name asc
sorted(xs, key=lambda x: (x[1], -x[0]))                # mixed directions
sorted(d.items(), key=lambda kv: kv[1], reverse=True)  # only when ALL desc

# Negation only works on numbers. To reverse a string field, sort twice
# (Python's sort is stable) -- least significant key first:
xs.sort(key=lambda x: x.name)                 # 2nd priority
xs.sort(key=lambda x: -x.size)                # 1st priority wins
```

## Dict idioms

```python
d.get(k)                    # None if missing -- tests love None returns
d.get(k, default)
d.setdefault(k, {})["f"] = v
d.pop(k, None)              # delete without KeyError
k in d
{k: v for k, v in d.items() if pred(v)}
dict(sorted(d.items()))
for k in list(d):           # iterate while deleting -- MUST wrap in list()
    if dead(d[k]): del d[k]
```

## bisect — sorted event logs

```python
from bisect import bisect_left, bisect_right, insort

i = bisect_right(times, t) - 1     # index of the latest entry <= t
                                   # (the "state as of time T" lookup)
insort(times, t)                   # keep a list sorted on insert
```

## heapq — only when you genuinely need a running top-K

```python
import heapq
heapq.heappush(h, (-priority, tiebreak, item))   # max-heap = negate
heapq.heappop(h)
heapq.nlargest(3, xs, key=lambda x: x.size)      # usually just use sorted()
```

## Copying — snapshots

```python
import copy
copy.deepcopy(self.data)     # nested dicts. THE snapshot tool. Slow, don't care.
dict(d)                      # shallow -- silently shares nested dicts. Bug source.
d.copy()                     # same shallow trap
```

## Dataclasses — worth it if records have 3+ fields

```python
from dataclasses import dataclass, field, replace

@dataclass
class File:
    size: int
    owner: str = "admin"
    expires_at: int | None = None
    tags: list = field(default_factory=list)   # never `= []`

f2 = replace(f, owner="bob")     # copy with one field changed
```
A plain dict is faster to type and easier to `deepcopy`. Use a dataclass only when
you are typing `rec["..."]` so often it is slowing you down.

## Strings & formatting

```python
f"{name}({value})"
name.startswith(prefix)
"/".join(parts)
path.strip("/").split("/")        # path problems: strip FIRST or you get ''
"".join(sorted(s))
s.rjust(3, "0")  /  f"{n:03d}"
```

## Numbers

```python
a // b        # floor -- goes toward -inf. -7 // 2 == -4
int(a / b)    # truncates toward 0.  int(-7/2) == -3   <- LC150's gotcha
round(x)      # banker's rounding! round(0.5) == 0. Use int(x + 0.5) if unsure.
amount * 2 // 100        # 2% cashback, floored -- do integer math, never float
```

## Control flow that saves lines

```python
val = d[k] if k in d else None
x = a or b                       # careful: 0 and "" are falsy
if not (rec := self.data.get(k)):    # walrus: fetch + test in one
    return None
return None if bad else result
```

## unittest — reading the tests, which is the real skill

```python
self.assertEqual(actual, expected)
self.assertIsNone(x)          # expects None specifically, not False
self.assertFalse(x)           # False, 0, "", [] all pass -- ambiguous, look around
self.assertRaises(RuntimeError)
self.assertCountEqual(a, b)   # same elements, ORDER IRRELEVANT
self.assertListEqual(a, b)    # order matters
```
`assertCountEqual` vs `assertListEqual` is the single most common place people
over- or under-implement sorting. Check which one the test uses before you write a
`sorted()`.

## Run tests fast

```bash
python3 -m unittest test_solution.TestLevel1 -v      # one level
python3 -m unittest test_solution -v                 # everything
python3 -m unittest test_solution -k prefix          # by name substring
```

## Things you cannot use

No `sortedcontainers`, no `numpy`, no `pandas`. Python stdlib only. If you find
yourself wanting `SortedList`, you want a plain list plus `sorted()` on read.
