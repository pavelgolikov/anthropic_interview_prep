"""Mock 1 reference solution — File Hosting Service.

Read this only AFTER your own attempt. What to look for:

  * The whole implementation lives in the timestamped methods. The Level 1/2
    methods are three-line delegates written once and never touched again.
  * Records are dicts from line one, so Level 3 (`expires_at`) and Level 4
    (`owner`) are added fields, not rewrites.
  * `_alive` is the ONLY place the expiry convention is encoded. If the tests
    had wanted inclusive expiry, that is a one-character fix.
  * Every mutating method ends with `self._commit(timestamp)`. Level 5 then
    costs six lines.

~120 lines, which is squarely in the framework's 110-160 LOC target for a
complete project.
"""

import copy
from bisect import bisect_right


class FileHost:
    def __init__(self):
        self.files = {}  # name -> {"size": int, "owner": str|None, "expires_at": int|None}
        self.users = {}  # user_id -> {"capacity": int}
        self._times = []  # ascending operation timestamps
        self._snaps = []  # parallel snapshots of (files, users)

    # ------------------------------------------------------------------ helpers
    def _alive(self, rec, timestamp):
        return rec["expires_at"] is None or timestamp < rec["expires_at"]

    def _living(self, timestamp):
        return {n: r for n, r in self.files.items() if self._alive(r, timestamp)}

    def _commit(self, timestamp):
        state = (copy.deepcopy(self.files), copy.deepcopy(self.users))
        if self._times and self._times[-1] == timestamp:
            self._snaps[-1] = state
        else:
            self._times.append(timestamp)
            self._snaps.append(state)

    def _remaining(self, user_id, timestamp):
        used = sum(
            r["size"] for r in self._living(timestamp).values() if r["owner"] == user_id
        )
        return self.users[user_id]["capacity"] - used

    def _write(self, timestamp, file_name, size, ttl, owner):
        rec = self.files.get(file_name)
        if rec is not None and self._alive(rec, timestamp):
            raise RuntimeError(f"file already exists: {file_name}")
        self.files[file_name] = {
            "size": size,
            "owner": owner,
            "expires_at": None if ttl is None else timestamp + ttl,
        }

    # ------------------------------------------------------- levels 1 & 2 (thin)
    def file_upload(self, file_name, size):
        return self.file_upload_at(0, file_name, size)

    def file_get(self, file_name):
        return self.file_get_at(0, file_name)

    def file_copy(self, source, dest):
        return self.file_copy_at(0, source, dest)

    def file_search(self, prefix):
        return self.file_search_at(0, prefix)

    # ------------------------------------------------------------------ level 3
    def file_upload_at(self, timestamp, file_name, size, ttl=None):
        self._write(timestamp, file_name, size, ttl, owner=None)
        self._commit(timestamp)

    def file_get_at(self, timestamp, file_name):
        rec = self.files.get(file_name)
        if rec is None or not self._alive(rec, timestamp):
            return None
        return rec["size"]

    def file_copy_at(self, timestamp, source, dest):
        rec = self.files.get(source)
        if rec is None or not self._alive(rec, timestamp):
            raise RuntimeError(f"no such file: {source}")
        self.files[dest] = {**rec, "owner": None}  # copies are unowned
        self._commit(timestamp)

    def file_search_at(self, timestamp, prefix):
        hits = [
            (name, rec["size"])
            for name, rec in self._living(timestamp).items()
            if name.startswith(prefix)
        ]
        hits.sort(key=lambda pair: (-pair[1], pair[0]))
        return [name for name, _ in hits[:10]]

    # ------------------------------------------------------------------ level 4
    def add_user(self, timestamp, user_id, capacity):
        if user_id in self.users:
            raise RuntimeError(f"user already exists: {user_id}")
        self.users[user_id] = {"capacity": capacity}
        self._commit(timestamp)

    def file_upload_at_by(self, timestamp, user_id, file_name, size, ttl=None):
        if user_id not in self.users:
            raise RuntimeError(f"no such user: {user_id}")
        rec = self.files.get(file_name)
        if rec is not None and self._alive(rec, timestamp):
            raise RuntimeError(f"file already exists: {file_name}")
        if self._remaining(user_id, timestamp) < size:
            return None
        self._write(timestamp, file_name, size, ttl, owner=user_id)
        self._commit(timestamp)
        return self._remaining(user_id, timestamp)

    def merge_user(self, timestamp, user_id_1, user_id_2):
        if user_id_1 == user_id_2:
            raise RuntimeError("cannot merge a user into itself")
        for uid in (user_id_1, user_id_2):
            if uid not in self.users:
                raise RuntimeError(f"no such user: {uid}")
        self.users[user_id_1]["capacity"] += self.users[user_id_2]["capacity"]
        for rec in self.files.values():
            if rec["owner"] == user_id_2:
                rec["owner"] = user_id_1
        del self.users[user_id_2]
        self._commit(timestamp)
        return self._remaining(user_id_1, timestamp)

    # ------------------------------------------------------------------ level 5
    def rollback(self, timestamp):
        i = bisect_right(self._times, timestamp) - 1
        if i < 0:
            self.files, self.users = {}, {}
        else:
            files, users = self._snaps[i]
            self.files, self.users = copy.deepcopy(files), copy.deepcopy(users)
        del self._times[i + 1:]
        del self._snaps[i + 1:]
