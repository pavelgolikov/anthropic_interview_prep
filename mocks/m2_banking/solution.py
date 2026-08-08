"""Mock 2 — Banking System.  Implement Bank here."""


class Bank:
    def __init__(self):
        raise NotImplementedError

    def create_account(self, timestamp, account_id):
        raise NotImplementedError

    def deposit(self, timestamp, account_id, amount):
        raise NotImplementedError

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
        raise NotImplementedError
