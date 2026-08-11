"""Mock 2 — Banking System.  Implement Bank here."""

class Bank:
    def __init__(self):
        self.accounts = {} # account_id : {"timestamp": int, "balance": int, "total_spending" int}
        self.payment_ind = 0
        self.payments = {}  # payment_id : {"timestamp": int, "account_id": str, "amount": int, "cb_due" due time, "status": "IN_PROGRESS" or "CASHBACK_RECEIVED"}

    def create_account(self, timestamp, account_id):
        if account_id in self.accounts.keys():
            return False
        # create the account with 0 balance
        self.accounts[account_id] = {"timestamp": timestamp, "balance": 0, "total_spending": 0}
        return True
    

    # HELPERS -------------------------------------------------------------------
    def _set_balance(self, timestamp, account_id, new_balance, reason):
        if reason == 'transfer_out' or reason == 'payment':
            old_balance = self.accounts[account_id]['balance']
            self.accounts[account_id]['total_spending'] += (old_balance - new_balance)
        self.accounts[account_id]['balance'] = new_balance
        return None

    def _fast_forward(self, timestamp):
        # look through payments and see which ones have due cashbacks
        due_cb = [x for x in self.payments.values() if (x['status'] == "IN_PROGRESS" and x['cb_due'] <= timestamp)]
        # pay all cashbacks that are due
        for cb in due_cb:
            cb_amount = cb['amount'] * 2 // 100
            new_balance = self.accounts[cb['account_id']]['balance'] + cb_amount
            self._set_balance(timestamp, cb['account_id'], new_balance, 'cashback')
            cb['status'] = "CASHBACK_RECEIVED"


    # L1 -----------------------------------------------------------------------
    def deposit(self, timestamp, account_id, amount):
        self._fast_forward(timestamp)
        if account_id not in self.accounts.keys():
            return None
        new_balance = self.accounts[account_id]['balance'] + amount
        self._set_balance(timestamp, account_id, new_balance, 'deposit')
        return new_balance

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
        self._fast_forward(timestamp)
        if target_account_id not in self.accounts or source_account_id not in self.accounts:
            return None
        new_balance_source = self.accounts[source_account_id]['balance'] - amount
        new_balance_target = self.accounts[target_account_id]['balance'] + amount
        if source_account_id == target_account_id:
            return None
        if new_balance_source < 0:
            return None

        # set balance
        self._set_balance(timestamp, source_account_id, new_balance_source, 'transfer_out')
        self._set_balance(timestamp, target_account_id, new_balance_target, 'transfer_in')
        return new_balance_source
        

    # L2 -----------------------------------------------------------------------
    def top_spenders(self, timestamp, n):
        self._fast_forward(timestamp)
        # want pairs (total_spent, account_id)
        pairs = [(v['total_spending'], k) for k, v in self.accounts.items()]
        pairs_sorted = sorted(pairs, key=lambda p: (-p[0], p[1]))[:n]
        top_spender_list_strings = [f"{x[1]}({x[0]})" for x in pairs_sorted]
        return top_spender_list_strings


    # L3 -----------------------------------------------------------------------
    def pay(self, timestamp, account_id, amount):
        self._fast_forward(timestamp)
        if account_id not in self.accounts or self.accounts[account_id]['balance'] < amount:
            return None
        self.payment_ind += 1
        new_balance = self.accounts[account_id]['balance'] - amount
        self._set_balance(timestamp, account_id, new_balance, 'payment')
        
        self.payments[f"payment{self.payment_ind}"] = {
            "timestamp": timestamp,
            "cb_due": timestamp + 86400000,
            "account_id": account_id,
            "amount": amount,
            "status": "IN_PROGRESS",
            }
        return f"payment{self.payment_ind}"
        
    def get_payment_status(self, timestamp, account_id, payment):
        self._fast_forward(timestamp)
        if (account_id not in self.accounts) or (payment not in self.payments):
            return None
        if payment in self.payments and account_id != self.payments[payment]['account_id']:
            return None
        return self.payments[payment]['status']
