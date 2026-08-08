"""Mock 3 reference solution — In-Memory Database.

Read this only AFTER your own attempt. What to look for:

  * `{key: {field: {"value": ..., "expires_at": ...}}}`. Three levels of dict from
    the start. The Level 1 temptation is `{key: {field: value}}`, and it costs a
    rewrite at Level 3.
  * `_alive`, `_living_fields` and `_render` are the only places that know about
    expiry and formatting. Levels 3-5 all reuse them.
  * Level 5 is nine lines because a transaction here is just "keep a copy, and
    put it back on abort". Writes go straight into `self.data`, so reads see
    uncommitted state for free. Resist the urge to build a staging buffer.

~95 lines.
"""

import copy
from bisect import bisect_right


class MemoryDB:
    def __init__(self):
        self.data = {}  # key -> {field: {"value": str, "expires_at": int|None}}
        self._backup_times = []
        self._backups = []  # parallel: (taken_at, deep-copied living state)
        self._txn_snapshot = None

    # ------------------------------------------------------------------ helpers
    def _alive(self, record, timestamp):
        return record["expires_at"] is None or timestamp < record["expires_at"]

    def _living_fields(self, timestamp, key):
        return {
            field: record
            for field, record in self.data.get(key, {}).items()
            if self._alive(record, timestamp)
        }

    def _render(self, fields):
        return [f"{field}({fields[field]['value']})" for field in sorted(fields)]

    def _write(self, timestamp, key, field, value, ttl):
        self.data.setdefault(key, {})[field] = {
            "value": value,
            "expires_at": None if ttl is None else timestamp + ttl,
        }

    # ------------------------------------------------------- levels 1 & 2 (thin)
    def set(self, key, field, value):
        return self.set_at(0, key, field, value)

    def get(self, key, field):
        return self.get_at(0, key, field)

    def delete(self, key, field):
        return self.delete_at(0, key, field)

    def scan(self, key):
        return self.scan_at(0, key)

    def scan_by_prefix(self, key, prefix):
        return self.scan_by_prefix_at(0, key, prefix)

    # ------------------------------------------------------------------ level 3
    def set_at(self, timestamp, key, field, value):
        self._write(timestamp, key, field, value, None)

    def set_at_with_ttl(self, timestamp, key, field, value, ttl):
        self._write(timestamp, key, field, value, ttl)

    def get_at(self, timestamp, key, field):
        record = self.data.get(key, {}).get(field)
        if record is None or not self._alive(record, timestamp):
            return None
        return record["value"]

    def delete_at(self, timestamp, key, field):
        record = self.data.get(key, {}).get(field)
        if record is None or not self._alive(record, timestamp):
            return False
        del self.data[key][field]
        if not self.data[key]:
            del self.data[key]
        return True

    def scan_at(self, timestamp, key):
        return self._render(self._living_fields(timestamp, key))

    def scan_by_prefix_at(self, timestamp, key, prefix):
        living = self._living_fields(timestamp, key)
        return self._render({f: r for f, r in living.items() if f.startswith(prefix)})

    # ------------------------------------------------------------------ level 4
    def backup(self, timestamp):
        snapshot = {}
        for key in self.data:
            living = self._living_fields(timestamp, key)
            if living:
                snapshot[key] = copy.deepcopy(living)
        self._backup_times.append(timestamp)
        self._backups.append((timestamp, snapshot))
        return len(snapshot)

    def restore(self, timestamp, timestamp_to_restore):
        i = bisect_right(self._backup_times, timestamp_to_restore) - 1
        if i < 0:
            self.data = {}
            return None
        taken_at, snapshot = self._backups[i]
        self.data = {
            key: {
                field: {
                    "value": record["value"],
                    # remaining lifetime at backup time, re-based on `timestamp`
                    "expires_at": None
                    if record["expires_at"] is None
                    else timestamp + (record["expires_at"] - taken_at),
                }
                for field, record in fields.items()
            }
            for key, fields in snapshot.items()
        }
        return None

    # ------------------------------------------------------------------ level 5
    def begin(self, timestamp):
        if self._txn_snapshot is not None:
            return False
        self._txn_snapshot = copy.deepcopy(self.data)
        return True

    def commit(self, timestamp):
        if self._txn_snapshot is None:
            return False
        self._txn_snapshot = None
        return True

    def abort(self, timestamp):
        if self._txn_snapshot is None:
            return False
        self.data = self._txn_snapshot
        self._txn_snapshot = None
        return True
