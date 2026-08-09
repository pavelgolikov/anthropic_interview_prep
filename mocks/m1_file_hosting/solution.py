"""Mock 1 — File Hosting Service.  Implement FileHost here.

Only Level 1 signatures are given, exactly as CodeSignal would hand them to you.
Add the later levels' methods yourself as you unlock them.
"""
import copy


class FileHost:
    def __init__(self):
        # self.files has entries: {"filename": {"timestamp": int, "size": int}}
        self.files = {}

    def file_upload(self, file_name, size):
        if file_name in self.files.keys():
            raise RuntimeError
        self.files[file_name] = {"timestamp": 0, "size": size}
        return None

    def file_get(self, file_name):
        if file_name in self.files.keys():
            return self.files.get(file_name).get("size")
        return None

    def file_copy(self, source, dest):
        if source not in self.files.keys():
            raise RuntimeError
        self.files[dest] = copy.deepcopy(self.files[source])
        return None
    
    def file_search(self, prefix):
        # need pairs (name, size) have 
        # valid_keys = [k for k in self.files.keys() if k.startswith(prefix)]
        pairs = [(v['size'], k) for k, v in self.files.items() if k.startswith(prefix)]
        # print(pairs)
        prefixes_ordered = [pair[1] for pair in sorted(pairs, key=lambda p: (-p[0], p[1]))][:10]
        return prefixes_ordered
        

# - `file_search(prefix)`
#   - Returns the names of **at most 10** files whose name starts with `prefix`.
#   - Ordered by size descending; ties broken by file name ascending.
#   - Returns `[]` when nothing matches.