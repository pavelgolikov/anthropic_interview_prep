# Mock 3 — In-Memory Database

> **Read one level at a time.** Implement `MemoryDB` in `solution.py`.
> `./run.sh 1` … `./run.sh 5`. Where this document and the tests disagree,
> **the tests win**.

You are implementing an in-memory key–value database. A **key** holds any number of
named **fields**, each with a string value — think of a key as a row and its fields
as columns. Timestamps are integers and are non-decreasing across calls.

---

## Level 1 — Initial design & basic functions

- `set(key, field, value)`
  - Creates or overwrites `field` on `key`. Creates `key` if needed. Returns `None`.
- `get(key, field)`
  - Returns the value, or `None` if the key or field does not exist.
- `delete(key, field)`
  - Removes `field` from `key`. Returns `True` if it was removed, `False` if the
    key or field did not exist.
  - A key with no remaining fields is treated as not existing.

---

## Level 2 — Data structures & data processing

- `scan(key)`
  - Returns every field on `key` as a list of `"field(value)"` strings, ordered by
    field name ascending. Returns `[]` if the key does not exist.
- `scan_by_prefix(key, prefix)`
  - As `scan`, restricted to fields whose name starts with `prefix`.

---

## Level 3 — Refactoring & encapsulation

Fields may now expire. Every Level 1/2 method gains a timestamped twin, and the
originals must keep working — treat them as operating at timestamp `0` with no
expiry.

A field set at `t` with `ttl = n` is alive for timestamps in `[t, t + n)` and is
dead at exactly `t + n`. A dead field is indistinguishable from one that was never
set. Overwriting a field replaces its lifetime entirely: a plain `set_at` over a
field that had a TTL makes it permanent again.

- `set_at(timestamp, key, field, value)`
- `set_at_with_ttl(timestamp, key, field, value, ttl)`
- `get_at(timestamp, key, field)`
- `delete_at(timestamp, key, field)`
- `scan_at(timestamp, key)`
- `scan_by_prefix_at(timestamp, key, prefix)`

---

## Level 4 — Backup & restore

- `backup(timestamp)`
  - Saves the state of the database at `timestamp`. Returns the number of keys
    that have at least one living field.
  - Only living fields are saved.
- `restore(timestamp, timestamp_to_restore)`
  - Replaces the current state with the most recent backup taken at or before
    `timestamp_to_restore`. Returns `None`.
  - **TTLs are re-based on the restore time.** A field that had `r` time left to
    live at the moment of the backup has exactly `r` time left to live as of
    `timestamp`. Fields with no expiry stay permanent.
  - If no backup exists at or before `timestamp_to_restore`, the database becomes
    empty.

---

## Level 5 — Transactions

Exactly one transaction may be open at a time.

- `begin(timestamp)`
  - Opens a transaction. Returns `True`, or `False` if one is already open.
- `commit(timestamp)`
  - Makes every change since `begin` permanent. Returns `True`, or `False` if no
    transaction is open.
- `abort(timestamp)`
  - Discards every change since `begin`. Returns `True`, or `False` if no
    transaction is open.

While a transaction is open, reads (`get_at`, `scan_at`, `scan_by_prefix_at`) see
the uncommitted changes. Return values of writes are unaffected by being inside a
transaction. `backup` and `restore` are never called inside a transaction.
