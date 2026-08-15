"""Mock 6 reference solution — File System.

Read this only AFTER your own attempt. What to look for:

  * There is no tree here. Two flat containers -- a set of directory paths and
    a dict of file paths -- plus string prefix matching give you subtree sizes,
    `ls`, and `largest_files` for free. A nested `{"children": {...}}` tree also
    works, but every one of those three then needs a traversal.
  * `_under` is the one place "beneath this directory" is defined. Level 1's
    `get_size`, Level 2's two methods and Level 4's `delete` all call it, so the
    trailing-slash edge case around root is handled once instead of four times.
  * The flat model's weak spot is Level 4 `move`, which has to re-key every
    affected path. That is the trade: a tree would move one pointer. It is still
    ~8 lines, and nothing here is graded on speed.
  * `write_file` is `write_file_by("root", ...)`. Writing the owner-aware form
    as the real implementation at Level 3 means Level 1 keeps working with a
    one-line delegate, and Level 5 slots a hash in beside the owner.

~130 lines.
"""


class FileSystem:
    ROOT = "/"

    def __init__(self):
        self.dirs = {self.ROOT}
        self.files = {}  # path -> {"size": int, "owner": str, "hash": str|None}
        self.quotas = {}  # user -> limit

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _parent(path):
        head = path.rsplit("/", 1)[0]
        return head or "/"

    def _exists(self, path):
        return path in self.dirs or path in self.files

    def _prefix(self, directory):
        return directory if directory == self.ROOT else directory + "/"

    def _under(self, directory):
        """Every file path strictly beneath `directory`."""
        prefix = self._prefix(directory)
        return [p for p in self.files if p.startswith(prefix)]

    # ------------------------------------------------------------------ level 1
    def mkdir(self, path):
        if self._exists(path) or self._parent(path) not in self.dirs:
            return False
        self.dirs.add(path)
        return True

    def write_file(self, path, size):
        return self.write_file_by("root", path, size)

    def get_size(self, path):
        if path in self.files:
            return self.files[path]["size"]
        if path in self.dirs:
            return sum(self.files[p]["size"] for p in self._under(path))
        return None

    # ------------------------------------------------------------------ level 2
    def ls(self, path):
        if path not in self.dirs:
            return None
        prefix = self._prefix(path)
        names = set()
        for candidate in list(self.files) + list(self.dirs):
            if candidate == path or not candidate.startswith(prefix):
                continue
            names.add(candidate[len(prefix):].split("/")[0])
        return sorted(names)

    def largest_files(self, path, n):
        if path not in self.dirs:
            return []
        hits = [(p, self.files[p]["size"]) for p in self._under(path)]
        hits.sort(key=lambda pair: (-pair[1], pair[0]))
        return [f"{p}({size})" for p, size in hits[:n]]

    # ------------------------------------------------------------------ level 3
    def write_file_by(self, user, path, size, content_hash=None):
        if path in self.dirs or self._parent(path) not in self.dirs:
            return False
        existing = self.files.get(path)
        credit = existing["size"] if existing and existing["owner"] == user else 0
        limit = self.quotas.get(user)
        if limit is not None and self.get_usage(user) - credit + size > limit:
            return False
        self.files[path] = {"size": size, "owner": user, "hash": content_hash}
        return True

    def set_quota(self, user, limit):
        if limit < self.get_usage(user):
            return False
        self.quotas[user] = limit
        return True

    def get_usage(self, user):
        return sum(f["size"] for f in self.files.values() if f["owner"] == user)

    # ------------------------------------------------------------------ level 4
    def delete(self, path):
        if path == self.ROOT:
            return None
        if path in self.files:
            del self.files[path]
            return 1
        if path in self.dirs:
            doomed = self._under(path)
            for p in doomed:
                del self.files[p]
            prefix = self._prefix(path)
            self.dirs = {d for d in self.dirs if d != path and not d.startswith(prefix)}
            return len(doomed)
        return None

    def move(self, src, dst):
        if src == self.ROOT or not self._exists(src) or self._exists(dst):
            return False
        if self._parent(dst) not in self.dirs:
            return False
        if dst.startswith(src + "/"):  # would move a directory inside itself
            return False
        moved = [p for p in self.files if p == src or p.startswith(src + "/")]
        for p in moved:
            self.files[dst + p[len(src):]] = self.files.pop(p)
        for d in [d for d in self.dirs if d == src or d.startswith(src + "/")]:
            self.dirs.discard(d)
            self.dirs.add(dst + d[len(src):])
        return True

    # ------------------------------------------------------------------ level 5
    def write_file_with_hash(self, user, path, size, content_hash):
        return self.write_file_by(user, path, size, content_hash)

    def disk_usage(self):
        seen = {}
        total = 0
        for path, meta in self.files.items():
            if meta["hash"] is None:
                total += meta["size"]  # no hash -> never shared
            else:
                seen[meta["hash"]] = meta["size"]
        return total + sum(seen.values())
