"""Mock 2 reference solution — Banking System.

Read this only AFTER your own attempt. What to look for:

  * `_advance(timestamp)` is the first line of every public method. That single
    convention is the entire answer to "there is no clock, cashback lands later".
  * Every balance mutation goes through `_set_balance`, which also appends to the
    history log. Level 5 is then a five-line lookup instead of a redesign.
  * Payment status is DERIVED from `timestamp >= due` rather than stored as a
    flag. Derived state cannot go stale, so the merge in Level 4 cannot corrupt it.
  * The merge is a checklist: balance, outgoing, pending events, payment
    ownership, history. Write the checklist as comments first, then fill it in.
"""

MILLISECONDS_IN_1_DAY = 86_400_000
CASHBACK_PERCENT = 2


class Bank:
    def __init__(self):
        # account_id -> {"balance", "outgoing", "created_at", "history"}
        self.accounts = {}
        # account_id -> {"created_at", "history", "merged_at"} for merged-away ids
        self.absorbed = {}
        self.pending = []  # [{"due", "seq", "account", "amount"}]
        self.payments = {}  # payment_id -> {"account", "due"}
        self._seq = 0

    # ------------------------------------------------------------------ helpers
    def _advance(self, timestamp):
        """Credit every cashback that has come due at or before `timestamp`."""
        due = [e for e in self.pending if e["due"] <= timestamp]
        if not due:
            return
        self.pending = [e for e in self.pending if e["due"] > timestamp]
        for event in sorted(due, key=lambda e: (e["due"], e["seq"])):
            account = self.accounts.get(event["account"])
            if account is not None:
                self._set_balance(
                    event["due"], event["account"], account["balance"] + event["amount"]
                )

    def _set_balance(self, timestamp, account_id, balance):
        account = self.accounts[account_id]
        account["balance"] = balance
        account["history"].append((timestamp, balance))

    # ------------------------------------------------------------------ level 1
    def create_account(self, timestamp, account_id):
        self._advance(timestamp)
        if account_id in self.accounts:
            return False
        self.accounts[account_id] = {
            "balance": 0,
            "outgoing": 0,
            "created_at": timestamp,
            "history": [(timestamp, 0)],
        }
        return True

    def deposit(self, timestamp, account_id, amount):
        self._advance(timestamp)
        account = self.accounts.get(account_id)
        if account is None:
            return None
        self._set_balance(timestamp, account_id, account["balance"] + amount)
        return account["balance"]

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
        self._advance(timestamp)
        source = self.accounts.get(source_account_id)
        target = self.accounts.get(target_account_id)
        if source is None or target is None or source_account_id == target_account_id:
            return None
        if source["balance"] < amount:
            return None
        self._set_balance(timestamp, source_account_id, source["balance"] - amount)
        self._set_balance(timestamp, target_account_id, target["balance"] + amount)
        source["outgoing"] += amount
        return source["balance"]

    # ------------------------------------------------------------------ level 2
    def top_spenders(self, timestamp, n):
        self._advance(timestamp)
        ranked = sorted(
            self.accounts.items(), key=lambda kv: (-kv[1]["outgoing"], kv[0])
        )
        return [f"{aid}({rec['outgoing']})" for aid, rec in ranked[:n]]

    # ------------------------------------------------------------------ level 3
    def pay(self, timestamp, account_id, amount):
        self._advance(timestamp)
        account = self.accounts.get(account_id)
        if account is None or account["balance"] < amount:
            return None
        self._set_balance(timestamp, account_id, account["balance"] - amount)
        account["outgoing"] += amount

        self._seq += 1
        payment_id = f"payment{self._seq}"
        due = timestamp + MILLISECONDS_IN_1_DAY
        self.payments[payment_id] = {"account": account_id, "due": due}
        self.pending.append(
            {
                "due": due,
                "seq": self._seq,
                "account": account_id,
                "amount": amount * CASHBACK_PERCENT // 100,
            }
        )
        return payment_id

    def get_payment_status(self, timestamp, account_id, payment):
        self._advance(timestamp)
        if account_id not in self.accounts:
            return None
        record = self.payments.get(payment)
        if record is None or record["account"] != account_id:
            return None
        return "CASHBACK_RECEIVED" if timestamp >= record["due"] else "IN_PROGRESS"

    # ------------------------------------------------------------------ level 4
    def merge_accounts(self, timestamp, account_id_1, account_id_2):
        self._advance(timestamp)
        if account_id_1 == account_id_2:
            return False
        keep = self.accounts.get(account_id_1)
        gone = self.accounts.get(account_id_2)
        if keep is None or gone is None:
            return False

        keep["outgoing"] += gone["outgoing"]
        self._set_balance(timestamp, account_id_1, keep["balance"] + gone["balance"])
        for event in self.pending:
            if event["account"] == account_id_2:
                event["account"] = account_id_1
        for record in self.payments.values():
            if record["account"] == account_id_2:
                record["account"] = account_id_1

        self.absorbed[account_id_2] = {
            "created_at": gone["created_at"],
            "history": gone["history"],
            "merged_at": timestamp,
        }
        del self.accounts[account_id_2]
        return True

    # ------------------------------------------------------------------ level 5
    def get_balance(self, timestamp, account_id, time_at):
        self._advance(timestamp)
        if account_id in self.accounts:
            record = self.accounts[account_id]
        elif account_id in self.absorbed:
            record = self.absorbed[account_id]
            if time_at >= record["merged_at"]:
                return None
        else:
            return None

        if time_at < record["created_at"]:
            return None
        for at, balance in reversed(record["history"]):
            if at <= time_at:
                return balance
        return None
