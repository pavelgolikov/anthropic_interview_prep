"""Mock 1 — File Hosting Service.  Implement FileHost here.

Only Level 1 signatures are given, exactly as CodeSignal would hand them to you.
Add the later levels' methods yourself as you unlock them.
"""
import copy


class FileHost:
    def __init__(self):
        # self.files has entries: {"filename": {"timestamp": int, "size": int, "expires_on": int}}
        self.files = {}
    
    def _alive(self, file_name, timestamp):
        # return rec["expires_at"] is None or timestamp < rec["expires_at"]
        return file_name in self.files.keys() and (self.files[file_name]['expires_on'] is None or timestamp < self.files[file_name]['expires_on'])
        
    def file_upload_at(self, timestamp, file_name, size, ttl=None):
        if file_name in self.files.keys() and self._alive(file_name, timestamp):
            raise RuntimeError
        self.files[file_name] = {"timestamp": timestamp, "size": size, "expires_on": None if ttl is None else timestamp + ttl}
        return None
    
    def file_upload(self, file_name, size):
        return self.file_upload_at(0, file_name, size)
    
    def file_get_at(self, timestamp, file_name):
        # how to handle dead files? we need a cleanup procedure any time we access?
        if not file_name in self.files.keys() or not self._alive(file_name, timestamp):
            return None
        return self.files.get(file_name).get("size")

    def file_get(self, file_name):
        return self.file_get_at(0, file_name)

    def file_copy_at(self, timestamp, source, dest):
        if source not in self.files.keys() or not self._alive(source, timestamp):
            raise RuntimeError
        self.files[dest] = copy.deepcopy(self.files[source])
        return None

    def file_copy(self, source, dest):
        return self.file_copy_at(0, source, dest)
    
    def file_search_at(self, timestamp, prefix):
        # need pairs (name, size) have 
        # valid_keys = [k for k in self.files.keys() if k.startswith(prefix)]
        pairs = [(v['size'], k) for k, v in self.files.items() if (k.startswith(prefix) and self._alive(k, timestamp))]
        # print(pairs)
        prefixes_ordered = [pair[1] for pair in sorted(pairs, key=lambda p: (-p[0], p[1]))][:10]
        return prefixes_ordered
    
    def file_search(self, prefix):
        return self.file_search_at(0, prefix)
    
    
        

# Files may now have a lifetime. Every Level 1/2 method gains a timestamped twin.
# **The Level 1 and Level 2 methods must keep working unchanged** — treat them as
# operating at timestamp `0` with an infinite lifetime.

# A file uploaded at `t` with `ttl = n` is alive for timestamps in `[t, t + n)`.
# It is dead at exactly `t + n`. A `ttl` of `None` means it lives forever.
# A dead file is indistinguishable from a file that never existed.

# - `file_upload_at(timestamp, file_name, size, ttl=None)`
#   - Raises `RuntimeError` only if a **living** file of that name exists. Uploading
#     over a name whose file has expired succeeds.
# - `file_get_at(timestamp, file_name)` — size, or `None` if missing or expired.
# - `file_copy_at(timestamp, source, dest)`
#   - Raises `RuntimeError` if `source` is missing or expired at `timestamp`.
#   - The copy inherits the source's **absolute** expiry time, not a fresh `ttl`.
# - `file_search_at(timestamp, prefix)` — as Level 2, but only living files.