"""Mock 4 — Build System.  Implement BuildSystem here."""


class BuildSystem:
    def __init__(self):
        raise NotImplementedError

    def add_task(self, task_id, duration):
        raise NotImplementedError

    def add_dependency(self, task_id, depends_on):
        raise NotImplementedError

    def get_duration(self, task_id):
        raise NotImplementedError
