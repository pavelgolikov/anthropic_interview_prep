"""Mock 3 — In-Memory Database.  Implement MemoryDB here."""

import copy
import bisect


class MemoryDB:
    def __init__(self):
        self.kv = {}    # key: {field: {"value": val, "ex": int}}
        self._tss = []
        self._snaps = []
        self.stash = None
    
    def _live(self, ts, key, field):
        if self.kv[key][field]['ex'] == None:
            return True
        return self.kv[key][field]['ex'] > ts
    
    def set_at_with_ttl(self, ts, key, field, value, ttl):
        if key not in self.kv:
            self.kv[key] = {}
        self.kv[key][field] = {"val": value,
                               "ex": None if ttl is None else ttl + ts,
                               }
        return None
    
    def set_at(self, ts, key, field, value):
        return self.set_at_with_ttl(ts, key, field, value, None)
    
    def set(self, key, field, value):
        return self.set_at(0, key, field, value)
    
    def get_at(self, ts, key, field):
        if key not in self.kv or field not in self.kv[key] or not self._live(ts, key, field):
            return None
        return self.kv[key][field]['val']
    
    def get(self, key, field):
        return self.get_at(0, key, field)
    
    def delete_at(self, ts, key, field):
        if key not in self.kv or field not in self.kv[key] or not self._live(ts, key, field):
            return False
        del self.kv[key][field]
        if len(self.kv[key].keys()) == 0:
            del self.kv[key]
        return True
    
    def delete(self, key, field):
        return self.delete_at(0, key, field)
    
    def scan_by_prefix_at(self, ts, key, prefix):
        if key not in self.kv:
            return []
        pairs = [(fn,v['val']) for fn, v in self.kv[key].items() if fn.startswith(prefix) and self._live(ts, key, fn)]
        pairs = sorted(pairs)
        pair_str = [f"{x[0]}({x[1]})" for x in pairs]
        return pair_str
    
    def scan_by_prefix(self, key, prefix):
        return self.scan_by_prefix_at(0, key, prefix)

    def scan_at(self, ts, key):
        return self.scan_by_prefix_at(ts, key, "")

    def scan(self, key):
        return self.scan_by_prefix(key, "")
        
    def backup(self, ts):
        db_to_save = {}
        for k in self.kv:
            for f in self.kv[k]:
                if self._live(ts, k, f):
                    db_to_save[k] = {}
                    db_to_save[k][f] = copy.deepcopy(self.kv[k][f])
        if len(self._tss) > 0 and self._tss[-1] == ts:
            self._snaps[-1] = copy.deepcopy((db_to_save, self._tss, self._snaps))
        else:
            self._tss.append(ts)
            self._snaps.append(copy.deepcopy((db_to_save, self._tss, self._snaps)))
        num_keys_live = len(db_to_save.keys())
        return num_keys_live
    
    def restore(self, ts, targ_ts):
        i = bisect.bisect_right(self._tss, targ_ts) - 1
        if i < 0 or self._tss == []:
            self.kv = {}
            self._tss = []
            self._snaps = []
        else:
            self.kv = copy.deepcopy(self._snaps[i][0])
            self._tss = copy.deepcopy(self._snaps[i][1])
            self._snaps = copy.deepcopy(self._snaps[i][2])
        # adjust ex fields
        for k in self.kv:
            for f in self.kv[k]:
                if self.kv[k][f]['ex'] != None:
                    self.kv[k][f]['ex'] = ts + (self.kv[k][f]['ex'] - targ_ts)
        return None 


    def begin(self, ts):
        if self.stash != None:
            return False
        self.stash = copy.deepcopy(self.kv)
        return True
        
    def commit(self, ts):
        if self.stash == None:
            return False
        self.stash = None
        return True

    def abort(self, ts):
        if self.stash == None:
            return False
        self.kv = self.stash
        self.stash = None
        return True
