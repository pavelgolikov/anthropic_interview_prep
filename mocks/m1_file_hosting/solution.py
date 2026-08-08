"""Mock 1 — File Hosting Service.  Implement FileHost here.

Only Level 1 signatures are given, exactly as CodeSignal would hand them to you.
Add the later levels' methods yourself as you unlock them.
"""


class FileHost:
    def __init__(self):
        raise NotImplementedError

    def file_upload(self, file_name, size):
        raise NotImplementedError

    def file_get(self, file_name):
        raise NotImplementedError

    def file_copy(self, source, dest):
        raise NotImplementedError
