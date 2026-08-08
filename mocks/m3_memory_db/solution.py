"""Mock 3 — In-Memory Database.  Implement MemoryDB here."""


class MemoryDB:
    def __init__(self):
        raise NotImplementedError

    def set(self, key, field, value):
        raise NotImplementedError

    def get(self, key, field):
        raise NotImplementedError

    def delete(self, key, field):
        raise NotImplementedError
