"""Mock 6 — File System.  Implement FileSystem here."""

import math
import copy

# You are implementing an in-memory file system. Paths are absolute, `/`-separated
# strings with no trailing slash: `/`, `/docs`, `/docs/report.txt`. The root
# directory `/` always exists. Sizes are non-negative integers.

class FileSystem:
    def __init__(self):
        self.paths = {} # path: "size"
        self.paths['/'] = {'dir': True, 'user': 'root'}
        self.quotas = {} # user_id: int
        self.quotas['root'] = math.inf
    
    def _parent_dir(self, path):
        par_path_split = path.split("/")[:-1]
        if par_path_split == ['']:
            return "/"
        return "/".join(par_path_split)
    
    def _is_dir(self, path):
        return self.paths[path]['dir'] == True
       
    def _root_helper(self, path):
        if path == '/':
            return path
        return path + '/'
    
    def mkdir_by(self, path, user):
        if path in self.paths or self._parent_dir(path) not in self.paths:
            return False
        self.paths[path] = {'dir': True, 'user': user}
        return True

    def mkdir(self, path):
        return self.mkdir_by(path, 'root')
    
    def get_usage(self, user):
        return sum([v['size'] for k, v in self.paths.items() if v['user'] == user and not v['dir']])
        
    def write_file_by(self, user, path, size):
        return self.write_file_with_hash(user, path, size, None)
    
    def write_file_with_hash(self, user, path, size, content_hash):
        if self._parent_dir(path) not in self.paths or (path in self.paths and self.paths[path]['dir']):
            return False
        if user in self.quotas and (self.get_usage(user) + size > self.quotas[user]):
            return False
        self.paths[path] = {'dir': False, 'size': size, 'user': user, 'hash': content_hash}
        return True
    
    def write_file(self, path, size):
        return self.write_file_by('root', path, size)
    
    def _dir_size(self, path):
        # sum all file sizes with path as prefix, assumes path is a directory
        path = self._root_helper(path)
        prefix_files = [(k,v) for k, v in self.paths.items() if k.startswith(path) and 'size' in self.paths[k]]
        prefix_files = [x[1]['size'] for x in prefix_files]
        return sum(prefix_files)
    
    def get_size(self, path):
        if path not in self.paths:
            return None
        if self.paths[path]['dir']:
            return self._dir_size(path)
        return self.paths[path]['size']
        
    def ls(self, path):
        if path not in self.paths or not self._is_dir(path):
            return None
        path = self._root_helper(path)
        in_dir = [k for k, v in self.paths.items() if k.startswith(path)]
        in_dir_no_pref = [k[len(path):] for k in in_dir]
        res = sorted(list(set([x.split("/")[0] for x in in_dir_no_pref])))
        res = [x for x in res if len(x) > 0]
        return res
    
    def set_quota(self, user, limit):
        if (user not in self.quotas or self.quotas[user] < limit) and self.get_usage(user) < limit:
            self.quotas[user] = limit
            return True
        return False
    
    def largest_files(self, path, n):
        if path not in self.paths or not self.paths[path]['dir']:
            return []
        pairs = [(v['size'], k) for k, v in self.paths.items() if (k.startswith(path) and not v['dir'])]
        sorted_pairs = sorted(pairs, key=lambda x: (-x[0], x[1]))
        form_strs = [f'{x[1]}({x[0]})' for x in sorted_pairs][:n]
        return form_strs
        
    
    def delete(self, path):
        if path not in self.paths or path == "/":
            return None
        paths_to_remove = [(k,v) for k,v in self.paths.items() if k.startswith(path)]
        files_removed = len([(k,v) for k,v in self.paths.items() if k.startswith(path) if not v['dir']])
        for p in paths_to_remove:
            del self.paths[p[0]]
        return files_removed
        
    def move(self, src, dst):
        if src not in self.paths or src == '/' or dst in self.paths or not self._parent_dir(dst) in self.paths or dst.startswith(src):
            return False
        paths_to_move = [k for k in self.paths if k.startswith(src)]
        for p in paths_to_move:
            new_path = p.replace(src, dst)
            obj_to_move = copy.deepcopy(self.paths[p])
            del self.paths[p]
            self.paths[new_path] = obj_to_move
        return True
    
    
    def disk_usage(self):
        # simple disk usage - calculate size of all paths that are files
        tot_usage = 0
        seen_hash = set()
        for p, v in self.paths.items():
            if not v['dir'] and not v['hash'] in seen_hash:
                tot_usage += v['size']
                if v['hash'] == None:
                    continue
                seen_hash.add(v['hash'])
        return tot_usage

