"""Mock 1 — File Hosting Service.  Implement FileHost here.

Only Level 1 signatures are given, exactly as CodeSignal would hand them to you.
Add the later levels' methods yourself as you unlock them.
"""

import copy
from bisect import bisect_right
from math import inf

class FileHost:
    def __init__(self):
        self.files = {} # file_name: {"size": size, "expires": ttl + timestamp, "user_id": user id}
        self.users = {} # user_id: {"capacity": capacity}
        self.users['unowned'] = {'capacity': None}
        
        self._ts = []
        self._snaps = []
    
    def _live(self, file_name, timestamp):
        if self.files[file_name]['expires'] == None:
            return True
        return self.files[file_name]['expires'] > timestamp
    
    def _rem_cap(self, user_id, timestamp):
        if user_id == 'unowned':
            return inf
        # user's remaining capacity is capacity over live files
        live_files = [v['size'] for k, v in self.files.items() if self._live(k, timestamp) and v['user_id'] == user_id]
        total_usage = sum(live_files)
        return self.users[user_id]['capacity'] - total_usage
        
    
    def _commit(self, timestamp):
        if len(self._ts) > 0 and self._ts[-1] == timestamp:
            self._snaps[-1] = [(copy.deepcopy(self.files), copy.deepcopy(self.users))]
        else:
            self._ts.append(timestamp)
            self._snaps.append((copy.deepcopy(self.files), copy.deepcopy(self.users)))
        

    def merge_user(self, timestamp, user_id_1, user_id_2):
        if user_id_1 == user_id_2 or user_id_1 not in self.users or user_id_2 not in self.users:
            raise RuntimeError
        for fn in self.files.keys():
            if self.files[fn]['user_id'] == user_id_2:
                self.files[fn]['user_id'] = user_id_1
        self.users[user_id_1]['capacity'] += self.users[user_id_2]['capacity']
        del self.users[user_id_2]
        self._commit(timestamp)
        return self._rem_cap(user_id_1, timestamp)
        
    def add_user(self, timestamp, user_id, capacity):
        if user_id in self.users:
            raise RuntimeError
        self.users[user_id] = {'capacity': capacity}
        self._commit(timestamp)
        return None
        
    def file_copy_at(self, timestamp, source, dest):
        if source not in self.files or not self._live(source, timestamp):
            raise RuntimeError
        self.files[dest] = copy.deepcopy(self.files[source])
        self.files[dest]['user_id'] = 'unowned'
        self._commit(timestamp)
        return None
    
    def file_upload_at_by(self, timestamp, user_id, file_name, size, ttl=None):
        if (file_name in self.files and self._live(file_name, timestamp)) or (user_id not in self.users):
            raise RuntimeError
        if self._rem_cap(user_id, timestamp) < size:
            return None
        self.files[file_name] = {"size": size,
                                 "expires": None if ttl is None else timestamp + ttl,
                                 "user_id": user_id}
        user_rem_cap = self._rem_cap(user_id, timestamp)
        self._commit(timestamp)
        if user_rem_cap == inf:
            return None
        return user_rem_cap

    def file_copy(self, source, dest):
        return self.file_copy_at(0, source, dest)
    
    def file_upload_at(self, timestamp, file_name, size, ttl=None):
        return self.file_upload_at_by(timestamp, 'unowned', file_name, size, ttl)

    def file_upload(self, file_name, size):
        return self.file_upload_at(0, file_name, size, None)
        
    def file_get_at(self, timestamp, file_name):
        if file_name not in self.files or not self._live(file_name, timestamp):
            return None
        return self.files[file_name]['size']
    
    def file_get(self, file_name):
        return self.file_get_at(0, file_name)
    
    def file_search_at(self, timestamp, prefix):
        pairs = [(v['size'], k) for k, v in self.files.items() if (k.startswith(prefix) and self._live(k, timestamp))]
        sort_pairs = sorted(pairs, key=lambda x: (-x[0], x[1]))
        res = [x[1] for x in sort_pairs][:10]
        return res
    
    def file_search(self, prefix):
        return self.file_search_at(0, prefix)

    def rollback(self, timestamp):
        # search throught timestamps with bisect
        i = bisect_right(self._ts, timestamp) - 1
        if i < 0:
            self.files, self.users = {}, {}
        else:
            snap = self._snaps[i]
            self.files, self.users = copy.deepcopy(snap[0]), copy.deepcopy(snap[1])
            del self._ts[i+1:]
            del self._snaps[i+1:]

        
        

# - `rollback(timestamp)`
#   - Restores all state — files and users — to what it was immediately after the
#     last operation that occurred at or before `timestamp`. Returns `None`.

#   - Operations after `timestamp` are discarded: files uploaded after it disappear,
#     users added after it are unregistered, merges are undone.

#   - Level 1 and Level 2 operations count as having occurred at timestamp `0`.

#   - Expiry times are **absolute and preserved**: a file restored by a rollback
#     still expires at the same timestamp it was originally going to.

#   - Rolling back to a time before any operation leaves the service empty.

#   - History after the rollback point is discarded — a later `rollback` to a
#     timestamp after this one restores this same state.