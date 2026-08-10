# Mock 1 — File Hosting Service

> **Read one level at a time.** Do not scroll ahead. The skill being trained is
> designing Level 1 without knowing what Level 4 wants.
>
> Implement `FileHost` in `solution.py`. Run `./run.sh 1` … `./run.sh 5`.
> Partial credit is real: a level with 4/6 tests passing is worth more than a level
> you skipped. Where this document and the tests disagree, **the tests win**.

You are implementing a simplified file hosting service. All state is in memory.
Timestamps are integers (seconds). There is no wall clock — time only advances when
a method is called with a timestamp.

Files have **no contents**. A file is nothing but a name and a size; you are
implementing the service's bookkeeping, not moving any bytes. "Upload" means
"record that this name now exists with this size".

---

## Level 1 — Initial design & basic functions

- `file_upload(file_name, size)`
  - Uploads a file of `size` bytes. Returns `None`.
  - Raises `RuntimeError` if a file with that name already exists.
- `file_get(file_name)`
  - Returns the file's size, or `None` if it does not exist.
- `file_copy(source, dest)`
  - Copies `source` to `dest`. Returns `None`.
  - Raises `RuntimeError` if `source` does not exist.
  - If `dest` already exists it is overwritten.

---

## Level 2 — Data structures & data processing

- `file_search(prefix)`
  - Returns the names of **at most 10** files whose name starts with `prefix`.
  - Ordered by size descending; ties broken by file name ascending.
  - Returns `[]` when nothing matches.

---

## Level 3 — Refactoring & encapsulation

Files may now have a lifetime. Every Level 1/2 method gains a timestamped twin.
**The Level 1 and Level 2 methods must keep working unchanged** — treat them as
operating at timestamp `0` with an infinite lifetime.

A file uploaded at `t` with `ttl = n` is alive for timestamps in `[t, t + n)`.
It is dead at exactly `t + n`. A `ttl` of `None` means it lives forever.
A dead file is indistinguishable from a file that never existed.

- `file_upload_at(timestamp, file_name, size, ttl=None)`
  - Raises `RuntimeError` only if a **living** file of that name exists. Uploading
    over a name whose file has expired succeeds.
- `file_get_at(timestamp, file_name)` — size, or `None` if missing or expired.
- `file_copy_at(timestamp, source, dest)`
  - Raises `RuntimeError` if `source` is missing or expired at `timestamp`.
  - The copy inherits the source's **absolute** expiry time, not a fresh `ttl`.
- `file_search_at(timestamp, prefix)` — as Level 2, but only living files.

---

## Level 4 — Extending design & functionality

Files may now belong to a user with a storage quota.

- `add_user(timestamp, user_id, capacity)`
  - Registers a user with `capacity` bytes of quota. Returns `None`.
  - Raises `RuntimeError` if `user_id` already exists.
- `file_upload_at_by(timestamp, user_id, file_name, size, ttl=None)`
  - Uploads a file owned by `user_id`.
  - Returns the user's **remaining** capacity after the upload.
  - Returns `None` and does not upload if the user's remaining capacity is less
    than `size`.
  - Raises `RuntimeError` if `user_id` is not registered, or if a living file of
    that name already exists.
- `merge_user(timestamp, user_id_1, user_id_2)`
  - Transfers every file owned by `user_id_2` to `user_id_1`, sums their
    capacities into `user_id_1`, and removes `user_id_2`.
  - Returns `user_id_1`'s remaining capacity.
  - Raises `RuntimeError` if either user is unregistered or the two ids are equal.

Rules:
- A user's used capacity is the total size of their **living** files. An expired
  file releases its quota.
- Files uploaded via `file_upload` / `file_upload_at` are **unowned** and count
  against nobody's quota.
- Files created by `file_copy` / `file_copy_at` are also unowned, whoever owned
  the source.

---
































## Level 5 — Historical state

- `rollback(timestamp)`
  - Restores all state — files and users — to what it was immediately after the
    last operation that occurred at or before `timestamp`. Returns `None`.
  - Operations after `timestamp` are discarded: files uploaded after it disappear,
    users added after it are unregistered, merges are undone.
  - Level 1 and Level 2 operations count as having occurred at timestamp `0`.
  - Expiry times are **absolute and preserved**: a file restored by a rollback
    still expires at the same timestamp it was originally going to.
  - Rolling back to a time before any operation leaves the service empty.
  - History after the rollback point is discarded — a later `rollback` to a
    timestamp after this one restores this same state.
