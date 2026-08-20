# Anthropic AFP — Technical Assessment #1

Prep workspace for the 90-minute CodeSignal assessment (invited 2026-08-08, due
2026-08-15).

```
cheatsheet/
  icf_patterns.py            the 8 primitives every one of these problems is made of
  python_speed.md            stdlib recall sheet -- read out loud on Day 5 mocks/
  m1_file_hosting/           canonical CodeSignal example, extended to 5 levels
  m2_banking/                ledger, top-spenders, deferred cashback, merge, history
  m3_memory_db/              key/field store, TTL, backup/restore, transactions
  m4_warehouse/              stock batches, perishable units, orders, historical qty
  m5_filesystem/             hierarchical paths, subtree rollups, quotas, move, dedup
reference/                   worked solutions -- open only after your attempt
```

Each mock:

```bash
cd mocks/m1_file_hosting
./run.sh          # every level
./run.sh 3        # level 3 only
./run.sh 3 --ref  # level 3 against the reference solution (post-mortem only)
```

Rules that make the practice worth anything:

1. Read `README.md` **one level at a time**. Do not scroll ahead.
2. 90 minutes on a visible timer, hard stop.
3. No AI assistance of any kind during a run — that includes this tool. Only
   <https://docs.python.org/3/>, same as the real assessment.

182 reference tests across the five mocks, all passing. Python 3.10+, stdlib only.
