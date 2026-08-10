"""Mock 1 — File Hosting Service.  Implement FileHost here.

Only Level 1 signatures are given, exactly as CodeSignal would hand them to you.
Add the later levels' methods yourself as you unlock them.
"""


class FileHost:
    def __init__(self):
        self.files = {} # {"filename": {"size": int, "owner": user_id, "expires_on": int}}
        self.users = {} # {"user_id": {"capacity": int}}
    
    
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
        
    def file_upload_at_by(self, timestamp, user_id, file_name, size, ttl=None):
        if user_id not in self.users.keys():
            raise RuntimeError("user_id does not exist")
        if self._remaining(user_id, timestamp) < size:
            return None
        self._write(timestamp, file_name, size, ttl, user_id)
        return self._remaining(user_id, timestamp)

    def file_upload_at(self, timestamp, file_name, size, ttl=None):
        self._write(timestamp, file_name, size, ttl, None)
        return None
    
    def file_upload(self, file_name, size):
        return self.file_upload_at(0, file_name, size)
    
    def file_get_at(self, timestamp, file_name):
        # how to handle dead files? we need a cleanup procedure any time we access?
        if not self._alive(file_name, timestamp):
            return None
        return self.files.get(file_name).get("size")

    def file_get(self, file_name):
        return self.file_get_at(0, file_name)

    def file_copy_at(self, timestamp, source, dest):
        if not self._alive(source, timestamp):
            raise RuntimeError
        self.files[dest] = {**self.files[source], 'owner': None}
        return None

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
        return self._remaining(user_id_1, timestamp)
            

# Rules:
# - Files uploaded via `file_upload` / `file_upload_at` are **unowned** and count
#   against nobody's quota.
# - Files created by `file_copy` / `file_copy_at` are also unowned, whoever owned
#   the source.
