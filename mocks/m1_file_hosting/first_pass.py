"""Mock 1 — File Hosting Service.  Implement FileHost here.

Only Level 1 signatures are given, exactly as CodeSignal would hand them to you.
Add the later levels' methods yourself as you unlock them.
"""

import copy
from bisect import bisect_right

class FileHost:
    def __init__(self):
        self.files = {} # {"filename": {"size": int, "owner": user_id, "expires_on": int}}
        self.users = {} # {"user_id": {"capacity": int}}
    
        self._times = []  # sorted timestamps
        self._snaps = []  # parallel list of deep copies
    

    def _alive(self, file_name, timestamp):
        # return rec["expires_at"] is None or timestamp < rec["expires_at"]
        return file_name in self.files.keys() and (self.files[file_name]['expires_on'] is None or timestamp < self.files[file_name]['expires_on'])


    def _living(self, timestamp):
        return {k: v for k, v in self.files.items() if self._alive(k, timestamp)}
    

    def _remaining(self, user_id, timestamp):
        # compute how much capacity user_id has remaining at timestamp
        used = sum( [v['size'] for k, v in self._living(timestamp).items() if v['owner'] == user_id])
        return self.users[user_id]['capacity'] - used
    

    def _write(self, timestamp, file_name, size, ttl, user_id):
        if self._alive(file_name, timestamp):
            raise RuntimeError("there is already a file by that name")
        self.files[file_name] = {"size": size, "expires_on": None if ttl is None else timestamp + ttl, "owner": user_id}
        
    
    ### L5
    def _commit(self, timestamp):
        """Call at the END of every mutating public method. That's the whole trick."""
        state = copy.deepcopy([self.files, self.users])
        if self._times and self._times[-1] == timestamp:
            self._snaps[-1] = state
        else:
            self._times.append(timestamp)
            self._snaps.append(state)


    def file_upload_at_by(self, timestamp, user_id, file_name, size, ttl=None):
        if user_id not in self.users.keys():
            raise RuntimeError("user_id does not exist")
        if self._remaining(user_id, timestamp) < size:
            return None
        self._write(timestamp, file_name, size, ttl, user_id)
        self._commit(timestamp)
        return self._remaining(user_id, timestamp)


    def file_upload_at(self, timestamp, file_name, size, ttl=None):
        self._write(timestamp, file_name, size, ttl, None)
        self._commit(timestamp)
        return None
    

    def file_upload(self, file_name, size):
        return self.file_upload_at(0, file_name, size)
    

    def file_get_at(self, timestamp, file_name):
        if not self._alive(file_name, timestamp):
            return None
        return self.files.get(file_name).get("size")


    def file_get(self, file_name):
        return self.file_get_at(0, file_name)


    def file_copy_at(self, timestamp, source, dest):
        if not self._alive(source, timestamp):
            raise RuntimeError
        self.files[dest] = {**self.files[source], 'owner': None}
        self._commit(timestamp)


    def file_copy(self, source, dest):
        return self.file_copy_at(0, source, dest)
    

    def file_search_at(self, timestamp, prefix):
        # need pairs (name, size) have 
        pairs = [(v['size'], k) for k, v in self.files.items() if (k.startswith(prefix) and self._alive(k, timestamp))]
        prefixes_ordered = [pair[1] for pair in sorted(pairs, key=lambda p: (-p[0], p[1]))][:10]
        return prefixes_ordered
    

    def file_search(self, prefix):
        return self.file_search_at(0, prefix)
    

    def add_user(self, timestamp, user_id, capacity):
        if user_id in self.users.keys():
            raise RuntimeError("user already exists")
        self.users[user_id] = {"capacity": capacity}
        self._commit(timestamp)
    

    def merge_user(self, timestamp, user_id_1, user_id_2):
        if user_id_1 == user_id_2:
            raise RuntimeError("same user")
        if user_id_1 not in self.users.keys() or user_id_2 not in self.users.keys():
            raise RuntimeError("unregistered user")
        self.users[user_id_1]['capacity'] += self.users[user_id_2]['capacity']
        for k, v in self.files.items():
            if v['owner'] == user_id_2:
                v['owner'] = user_id_1
        del self.users[user_id_2]
        self._commit(timestamp)
        return self._remaining(user_id_1, timestamp)
            

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

    def rollback(self, timestamp):
        """Restore the state as of `timestamp` (latest snapshot at or before it)."""
        i = bisect_right(self._times, timestamp) - 1
        if i < 0:
            self.files, self.users = {}, {}
        else:
            self.files, self.users = copy.deepcopy(self._snaps[i][0]), copy.deepcopy(self._snaps[i][1])
        del self._snaps[i + 1:]
        del self._times[i + 1:]
