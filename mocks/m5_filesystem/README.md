# Mock 5 — File System


You are implementing an in-memory file system. Paths are absolute, `/`-separated
strings with no trailing slash: `/`, `/docs`, `/docs/report.txt`. The root
directory `/` always exists. Sizes are non-negative integers.

---

## Level 1 — Initial design & basic functions

- `mkdir(path)`
  - Creates a directory at `path`.
  - Returns `True`, or `False` if something already exists at `path` or the
    parent directory does not exist.
- `write_file(path, size)`
  - Creates a file at `path`, or overwrites the file already there.
  - Returns `True`, or `False` if the parent directory does not exist or `path`
    names an existing directory.
- `get_size(path)`
  - For a file, its size. For a directory, the total size of every file anywhere
    beneath it. `None` if nothing exists at `path`.

---

## Level 2 — Data structures & data processing

- `ls(path)`
  - The **names** of the immediate children of the directory at `path`, sorted
    ascending — names only, not full paths.
  - `[]` for an empty directory. `None` if `path` does not exist or is a file.
- `largest_files(path, n)`
  - At most `n` strings of the form `"full_path(size)"` for files anywhere
    beneath the directory `path`, ordered by size descending, ties by full path
    ascending.
  - `[]` if nothing matches or `path` is not a directory.

---

## Level 3 — Users & quotas

Every file now has an owner. The Level 1/2 methods still work and act as the
user `"root"`, who is never subject to a quota.

- `write_file_by(user, path, size)`
  - As `write_file`, but the file is owned by `user`.
  - Overwriting a file transfers ownership to `user`: the previous owner stops
    being charged for it and `user` starts.
  - Returns `False` if the write would take `user`'s total owned bytes above
    their quota. Nothing is written in that case.
- `set_quota(user, limit)`
  - Sets `user`'s limit in bytes. Returns `True`, or `False` if `limit` is below
    what `user` already owns — in which case the quota is not set.
- `get_usage(user)`
  - The total size of every file owned by `user`. `0` if they own nothing.

---

## Level 4 — Moving & deleting

- `delete(path)`
  - Removes the file or directory at `path`, and everything beneath it.
  - Returns the number of **files** removed, or `None` if nothing exists at
    `path`. Deleting `/` is not allowed and returns `None`.
  - Deleted files stop counting toward their owner's usage.
- `move(src, dst)`
  - Moves the file or directory at `src` to `dst`, keeping sizes and owners.
    Moving a directory takes everything beneath it along.
  - Returns `True`, or `False` if `src` does not exist, `src` is `/`, something
    already exists at `dst`, `dst`'s parent directory does not exist, or `dst`
    is inside `src`.

---

## Level 5 — Deduplication

Files may be written with a content hash. Two files with the same hash hold
identical bytes, so the system stores those bytes only once.

- `write_file_with_hash(user, path, size, content_hash)`
  - As `write_file_by`, and records `content_hash` for the file.
- `disk_usage()`
  - The total bytes actually stored: each distinct content hash is counted once,
    at its size. Files written without a hash are always counted in full,
    individually.

Quotas are unaffected by deduplication — `get_usage` counts what a user wrote,
not what was stored.
