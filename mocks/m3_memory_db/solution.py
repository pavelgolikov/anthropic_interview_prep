"""Mock 3 — In-Memory Database.  Implement MemoryDB here."""

import copy
import bisect


class MemoryDB:
    def __init__(self):
        self.db = {} # key: {field: {"value": value, "expires": expiry timestamp}}
        self.timestamps = []
        self.backups = []
    
    def _alive(self, db, key, field, timestamp):
        if db[key][field]["expires"] is None:
            return True
        return db[key][field]["expires"] > timestamp
    
    def set_at_with_ttl(self, timestamp, key, field, value, ttl):
        if key not in self.db:
            self.db[key] = {}
        self.db[key][field] = {
            "value": value,
            "timestamp": timestamp,
            "expires": None if ttl is None else timestamp + ttl,
            }
        return None
    
    def set_at(self, timestamp, key, field, value):
        return self.set_at_with_ttl(timestamp, key, field, value, None)
    
    def set(self, key, field, value):
        return self.set_at(0, key, field, value)

    def get_at(self, timestamp, key, field):
        if key not in self.db or (key in self.db and field not in self.db[key]):
            return None
        if not self._alive(self.db, key, field, timestamp):
            return None
        return self.db[key][field]["value"]
    
    def get(self, key, field):
        return self.get_at(0, key, field)

    def delete_at(self, timestamp, key, field):
        if key not in self.db or (key in self.db and field not in self.db[key]) or not self._alive(self.db, key, field, timestamp):
            return False
        del self.db[key][field]
        if len(self.db[key].keys()) == 0:
            del self.db[key]
        return True
    
    def delete(self, key, field):
        return self.delete_at(0, key, field)
        
    def scan_by_prefix_at(self, timestamp, key, prefix):
        if key not in self.db:
            return []
        pairs = [(fld,v) for fld, v in self.db[key].items() if self._alive(self.db, key, fld, timestamp)]
        pairs_sorted = sorted(pairs)
        filtered_by_prefix = [x for x in pairs_sorted if x[0].startswith(prefix)]
        return [f"{x[0]}({x[1]["value"]})" for x in filtered_by_prefix]
    
    def scan_by_prefix(self, key, prefix):
        return self.scan_by_prefix_at(0, key, prefix)

    def scan_at(self, timestamp, key):
        return self.scan_by_prefix_at(timestamp, key, "")
    
    def scan(self, key):
        return self.scan_at(0, key)

    def backup(self, timestamp):
        self.timestamps.append(timestamp)
        snapshot = {}
        for key, fields in self.db.items():
            live = {f: dict(e) for f, e in fields.items() if self._alive(self.db, key, f, timestamp)}
            if live:
                snapshot[key] = live
        self.backups.append(snapshot)
        return len(snapshot.keys())
    
    def restore(self, timestamp, timestamp_to_restore):
        ts_ind = bisect.bisect_right(self.timestamps, timestamp_to_restore) - 1
        ts_filt = self.timestamps[ts_ind:]
        if ts_ind < 0:
            self.db = {}
            self.timestamps = []
            self.backups = []
            return None
        
        # rebase the ttls
        self.db = self.backups[ts_ind]
        for k, v in self.db.items():
            for f in v.values():
                if f['expires'] is not None:
                    remaining_life = f['expires'] - timestamp_to_restore
                    f["expires"] = timestamp + remaining_life
        return None
        


# ## Level 5 — Transactions

# Exactly one transaction may be open at a time.

# - `begin(timestamp)`
#   - Opens a transaction. Returns `True`, or `False` if one is already open.
# - `commit(timestamp)`
#   - Makes every change since `begin` permanent. Returns `True`, or `False` if no
#     transaction is open.
# - `abort(timestamp)`
#   - Discards every change since `begin`. Returns `True`, or `False` if no
#     transaction is open.

# While a transaction is open, reads (`get_at`, `scan_at`, `scan_by_prefix_at`) see
# the uncommitted changes. Return values of writes are unaffected by being inside a
# transaction. `backup` and `restore` are never called inside a transaction.
