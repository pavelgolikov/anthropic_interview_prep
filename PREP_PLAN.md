# Anthropic AFP — Technical Assessment #1 Prep Plan

**Assessment window:** invite received 2026-08-08, due 11:59pm 2026-08-15.
**Target sit date:** morning of 2026-08-14 (leaves a full buffer day for tech problems).

---

## 1. What this assessment actually is

It is **not** a LeetCode round. Your email describes CodeSignal's **Industry Coding
Skills Evaluation Framework** (ICF / "Industry Coding Assessment"), which Anthropic
uses with a 5-level variant. Every phrase in your email maps onto that framework:

| Your email says | Framework meaning |
|---|---|
| "a simple coding project from a spec, broken into five levels" | ONE system, built progressively. Level N+1 extends the code you wrote for Level N. |
| "You can read the tests, and run them early and often" | Tests are visible. They are the executable spec. |
| "the provided test suite is the final word on requirements" | Ambiguity in prose → go read the assert. |
| "Don't worry about edge cases no test checks" | Do not gold-plate. Implement to the tests. |
| "no libraries are needed; unittest" | Python stdlib only. |
| "not evaluated on code quality, readability, or maintainability" | See §2 — this differs from the public blogs, and **your email wins**. |
| "execution speed matters only where explicitly mentioned" | Do not optimize. O(n) scans over dicts are fine. |
| "You do not need to complete all levels to advance" | Partial credit is real. Every passing test is points. |

The canonical published example (from CodeSignal's own technical brief) is a **file
hosting service**:

- **L1 — Initial design & basic functions.** 3–4 simple methods. `FILE_UPLOAD`, `FILE_GET`, `FILE_COPY`. ~15–20 LOC, 10–15 min.
- **L2 — Data structures & data processing.** `FILE_SEARCH(prefix)` → top 10 by size desc, tie by name. ~30–45 LOC cumulative, 20–30 min.
- **L3 — Refactoring & encapsulation.** Everything gets a `_AT(timestamp, ...)` twin, plus TTL/expiry. ~90–130 LOC cumulative, 30–60 min.
- **L4 — Extending design & functionality.** `ROLLBACK(timestamp)` — restore prior state, recalculate TTLs. ~110–160 LOC total.
- **L5 (Anthropic's extra level)** — not publicly documented. Expect either ownership/quota accounting, historical queries, merge semantics, or transactions.

Reported problem families (all the same shape): in-memory key-value DB with TTL,
banking / ledger with scheduled payments, file system or file host, worker
time-tracking, package manager, build system, text editor with undo, rate limiter.

**The single most important structural fact:** Level 3 always breaks naive Level 1
code. It is the level where a timestamp/expiry/ownership dimension gets bolted onto
data you stored as a bare scalar. Candidates who stored `files[name] = size` have to
rewrite; candidates who stored `files[name] = {"size": size}` just add a key.

## 2. One contradiction, resolved

Several SEO guides (Sundeep Teki, FinalRound, InterviewFox, Lodely) claim readability
is scored and that "LLMs detect test-gaming." Your email says the opposite in plain
language: *"You will not be evaluated on code quality, readability, or
maintainability."* Blind posts from actual candidates agree with your email.

**Trust your email.** But do not read it as "write garbage" — write plainly-structured
code because *you* need to refactor it three times in 90 minutes, not because a grader
is watching. Clean structure here is a speed tactic, not a scoring criterion.

(Those same guides are also the only source for "480/520/600 cutoffs." Treat all
specific score thresholds as unverified. The actionable version is just: get as far as
you can, as fast as you can.)

## 3. Answers to your three questions

**"Should I continue solving LeetCode?"**
Only as a warm-up, ~20–30 min/day, and only from the patterns that actually appear:
hash maps / `defaultdict` / `Counter` (your Pattern 1), sorting with composite keys and
intervals (Pattern 5), heaps and top-K (Pattern 8), and stacks (Pattern 6). These are
the ICF working set. Your fingers need to be warm; your algorithm knowledge does not
need to be deeper.

**"Should I look at LeetCode Hards?"**
**No.** This is the clearest call in the whole plan. CodeSignal's own framework
document explicitly lists as *out of scope* at every level: "complex or niche
algorithms (binary search, two pointers, dynamic programming)", "advanced data
structures", "concurrency/parallelism", and "data optimizations." Time spent on Hard
DP is time actively taken away from the thing being tested. Your Pattern 7 (binary
search) and Pattern 10 (DP) lists are the two *least* relevant sections of your tracker
for this specific assessment.

**"I've only been doing mediums."**
That is the correct difficulty band and you are already past it in the relevant
patterns. The gap in your tracker is not difficulty — it is **category**. You have zero
*design* problems logged. That is exactly the category this assessment is made of.

### The LeetCode swap

Replace algorithm grinding with **design problems**, which map ~1:1 onto ICF
primitives. Ranked by relevance:

| Problem | Why it matters here |
|---|---|
| **981. Time Based Key-Value Store** | Timestamped writes + "value as of time T". This is the L3 mechanic, exactly. |
| **588. Design In-Memory File System** | Nested paths, prefix listing, `ls` ordering. |
| **146. LRU Cache** | Dict + ordering discipline; `OrderedDict.move_to_end`. |
| **362. Design Hit Counter** | Sliding expiry window = TTL logic. |
| **359. Logger Rate Limiter** | Simplest possible TTL-per-key. |
| **1244. Design a Leaderboard** | Top-K with ties, add/reset — the L2 mechanic. |
| **355. Design Twitter** | Merge K sources, top-10 by recency. |
| **1166. Design File System** | Path validation + parent existence checks. |
| **635. Design Log Storage System** | Range query over granularity — good ambiguity practice. |
| **380. Insert Delete GetRandom** | You have this coded already; re-do it cold as a warm-up. |

Do these **untimed with no hints**, in a plain editor. Six of them beats sixty mediums.

## 4. Practice material in this repo

Four full mock assessments, each with 5 levels, a stub, and a `unittest` suite that
mirrors the real format (readable tests, grouped per level, partial credit visible):

```
mocks/m1_file_hosting/   # canonical CodeSignal example, extended to 5 levels
mocks/m2_banking/        # ledger, top-spenders, deferred cashback, merge, history
mocks/m3_memory_db/      # key/field store, TTL, backup/restore, transactions
mocks/m4_build_system/   # DAG, topo order, caching + invalidation, parallel makespan
```

Rules for using them, to keep the practice honest:

1. **Read `README.md` one level at a time.** Do not scroll ahead. The whole skill being
   trained is designing L1 without knowing L4.
2. Work in `solution.py`. Run `./run.sh 1` … `./run.sh 5`, or `./run.sh` for all.
3. **No Claude Code, no Copilot, no autocomplete, no web search** during a timed run.
   Only https://docs.python.org/3/ — same as the real thing. Practicing with AI
   assistance trains a reflex you are not allowed to use.
4. 90 minutes on a visible timer. Stop at 90 even if you are mid-level, then review.
5. `reference/` has a worked solution for each. Read it only *after* your attempt.

Free external practice, once you have burned through these:
[CodeSignal's official ICA practice test](https://codesignal.com/resource/industry-coding-framework/)
and the [community mock repo](https://github.com/PaulLockett/CodeSignal_Practice_Industry_Coding_Framework).

## 5. The 7-day schedule

Core track is ~2h/day; the extension is for days you have more room. Everything is
ordered so that if you lose a day, you drop from the bottom.

**Day 0 — Fri Aug 8 (today) · ~2h · Orientation**
- Read `cheatsheet/icf_patterns.py` end to end. It is the seven primitives that
  compose every one of these problems.
- Do **M1 untimed**, cheatsheet open, all five levels. Goal is not speed — it is to
  feel where L3 punishes an L1 shortcut.
- Diff your M1 against `reference/m1_file_hosting.py`. Write down, in one line each,
  every place you had to rewrite instead of extend.

**Day 1 — Sat Aug 9 · ~2.5h · First timed run**
- 20 min: LeetCode 981 + 359, cold.
- **90 min timed: M2 (banking).** Hard stop.
- 30 min review: which level did you lose time in, and was it thinking or typing?

**Day 2 — Sun Aug 10 · ~2h · Pattern drills**
- 30 min: LeetCode 146 + 1244.
- 60 min: from `cheatsheet/`, re-implement from memory, no reference: TTL-with-`_at`,
  snapshot/rollback, top-K with tie-break, deferred-event queue. Four blank files,
  20 min each. This is the highest-leverage hour of the week.
- 30 min: re-do the level of M2 you scored worst on.

**Day 3 — Mon Aug 11 · ~2.5h · Second timed run**
- **90 min timed: M3 (in-memory DB).** This is the most commonly reported family.
- 45 min review + read `reference/m3_memory_db.py`.

**Day 4 — Tue Aug 12 · ~2.5h · Third timed run, different shape**
- **90 min timed: M4 (build system).** Graph-flavoured, so it stresses a different
  muscle: adjacency dicts, topological order with deterministic tie-breaks.
- 30 min: LeetCode 588 + 362.

**Day 5 — Wed Aug 13 · ~2h · Consolidation**
- **90 min timed: re-do M1 cold.** You should now clear all five levels with time
  left. If you do not, that gap is your real signal — spend the remaining time there.
- 20 min: skim `cheatsheet/python_speed.md`, out loud, for the stdlib idioms you did
  not reach for.

**Day 6 — Thu Aug 14 · MORNING: SIT THE ASSESSMENT**
- Do not learn anything new today. 20-minute warm-up on a solved problem only.
- Logistics checklist below, then take it when you are freshest.

**Day 7 — Fri Aug 15 · Buffer**
- Reserved. If Day 6 hits a technical problem, you still have a full day and the
  deadline is 11:59pm. Do not plan to use this day.

## 6. In-assessment tactics

**First 5 minutes, before typing anything:**
1. Read the *whole* Level 1 prose and the *whole* Level 1 test file.
2. Ask: what is the entity, and what will get attached to it later? Give it a dict or a
   small class **now**, even if it holds one field.
3. Skim method names for a hint of what is coming (a `_at` suffix anywhere = timestamps
   are coming; a `user_id` anywhere = ownership is coming).

**Defaults that pay off on this specific format:**
- Store records as `dict` (or `@dataclass`), never as a bare scalar. `{"size": n}` not `n`.
- Write the timestamped form as the real implementation and make the plain form call it
  with `timestamp=0`. This makes L3 a 3-line change instead of a rewrite.
- Never mutate a method signature. Add a new method that delegates.
- Keep every mutation going through one small `_apply(...)` helper if any hint of
  rollback/undo appears — snapshotting then costs one line.
- `copy.deepcopy` for snapshots is fine. Efficiency is explicitly not graded.
- Sort with a composite key: `sorted(items, key=lambda x: (-x.size, x.name))[:10]`.
- Return types matter more than you expect. If a test expects `None`, do not return
  `False`. If it expects `[]`, do not return `None`. Read the assert.

**Time management (90 min, 5 levels):**

| Level | Budget | Cumulative |
|---|---|---|
| L1 | 10 min | 0:10 |
| L2 | 15 min | 0:25 |
| L3 | 25 min | 0:50 |
| L4 | 20 min | 1:10 |
| L5 | 20 min | 1:30 |

If you are over budget on a level, submit what passes and move on — later levels are
worth the same points and are sometimes easier than the level that stuck you.

**Failure modes to actively avoid:**
- Rewriting from scratch at L3 because the design broke. Refactor in place instead;
  you almost never have time for a rewrite.
- Handling edge cases no test mentions. Your email explicitly grants you permission to
  skip these.
- Optimizing. Nobody is timing your inner loop.
- Silent assumptions about ambiguous prose. Go read the test.

## 7. Logistics checklist (do this on Day 5, not Day 6)

- [ ] Run CodeSignal's system/connection check. There are no retakes for your-side issues.
- [ ] Wired ethernet if available; if not, sit next to the router.
- [ ] Close everything with an AI assistant in it — IDE plugins, browser extensions,
      Copilot, this tool. Proctoring is active and pasting external code is flagged.
- [ ] Have only https://docs.python.org/3/ open.
- [ ] 90 uninterrupted minutes blocked in the calendar; phone in another room.
- [ ] Water, and something to write on for sketching the data model.

## 8. Note on scope

This assessment is a floor-check on unassisted implementation fluency, not a ceiling
test — the email says as much ("Later stages of the selection process will evaluate how
effectively you use AI tools"). Your published work (ArbiGraph, the robust-reasoning
benchmark) is well past this bar conceptually; the only real risk is rustiness in
typing speed and stdlib recall after a month away. That is precisely what the timed
mocks are for.

Preparing with AI is fine and is what the email's "How to prepare" section invites.
Using it *during* the 90 minutes is not. Keep those cleanly separated — practice the
timed runs with everything closed.
