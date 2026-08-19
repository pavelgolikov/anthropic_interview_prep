"""Mock 2 — Banking System.  Implement Bank here."""

import bisect
import copy

class Bank:
    def __init__(self):
        self.accounts = {}  # account_id :{"balance": int, "timestamp": timestamp}
        self.payments = {}  # payment_id: {"amount": int, "timestamp": timestamp, "account_id": account_id, "due": int, "paid": False}
        self.pay_id = 0
        self._ts = [0]
        self._snaps = [{}]
    
    def create_account(self, timestamp, account_id):
        self._advance(timestamp)
        if account_id in self.accounts:
            return False
        self.accounts[account_id] = {"timestamp": timestamp, "balance": 0, "outgoing": 0}
        self._commit(timestamp)
        return True
    
    def _commit(self, timestamp):
        if len(self._ts) > 0 and self._ts[-1] == timestamp:
            self._snaps[-1] = copy.deepcopy(self.accounts)
        else:
            self._ts.append(timestamp)
            self._snaps.append(copy.deepcopy(self.accounts))
    
    def _set_balance(self, timestamp, account_id, new_balance):
        old_balance = self.accounts[account_id]['balance']
        if old_balance > new_balance:
            self.accounts[account_id]['outgoing'] += old_balance - new_balance
        self.accounts[account_id]['balance'] = new_balance

    def deposit(self, timestamp, account_id, amount):
        self._advance(timestamp)
        if account_id not in self.accounts:
            return None
        new_balance = self.accounts[account_id]['balance'] + amount
        self._set_balance(timestamp, account_id, new_balance)
        self._commit(timestamp)
        return self.accounts[account_id]['balance']

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
        self._advance(timestamp)
        if source_account_id not in self.accounts or target_account_id not in self.accounts:
            return None
        if source_account_id == target_account_id or self.accounts[source_account_id]['balance'] < amount:
            return None
        new_source = self.accounts[source_account_id]['balance'] - amount
        new_target = self.accounts[target_account_id]['balance'] + amount
        self._set_balance(timestamp, source_account_id, new_source)
        self._set_balance(timestamp, target_account_id, new_target)
        self._commit(timestamp)
        return new_source
        
    def top_spenders(self, timestamp, n):
        self._advance(timestamp)
        pairs = [(k,v['outgoing']) for k, v in self.accounts.items()]
        pairs_sorted = sorted(pairs, key=lambda x: (-x[1], x[0]))
        pairs_sorted_cut = pairs_sorted[:n]
        ret_strings = [f"{x[0]}({x[1]})" for x in pairs_sorted_cut]
        return ret_strings
        
        
    def _advance(self, timestamp):
        # advances time - called as first line of every method
        # loop through all payments and pay the ones due
        for p_id, p_data in self.payments.items():
            if p_data['due'] <= timestamp and not p_data['paid']:
                new_bal = self.accounts[p_data['account_id']]['balance'] + p_data['amount']
                self._set_balance(p_data['due'], p_data['account_id'], new_bal)
                p_data['paid'] = True
                self._commit(p_data['due'])
                
    
    def pay(self, timestamp, account_id, amount):
        self._advance(timestamp)
        if account_id not in self.accounts or self.accounts[account_id]['balance'] < amount:
            return None
        new_balance = self.accounts[account_id]['balance'] - amount
        self._set_balance(timestamp, account_id, new_balance)
        self.pay_id += 1
        pay_id = "payment" + str(self.pay_id)
        # create cashback payment
        self.payments[pay_id] = {"account_id": account_id,
                                 "amount": int(amount * 0.02),
                                 "due": timestamp + 86400000,
                                 "paid": False
                                 }
        self._commit(timestamp)
        return pay_id
        

    def get_payment_status(self, timestamp, account_id, payment):
        self._advance(timestamp)
        if account_id not in self.accounts or payment not in self.payments or self.payments[payment]['account_id'] != account_id:
            return None
        if self.payments[payment]['due'] <= timestamp:
            return "CASHBACK_RECEIVED"
        return "IN_PROGRESS"
        
    
    def merge_accounts(self, timestamp, account_id_1, account_id_2):
        self._advance(timestamp)
        if account_id_1 == account_id_2 or account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False
        
        # change all payments for account_id_2 to account_id_1
        for p_id, p_data in self.payments.items():
            if p_data['account_id'] == account_id_2:
                p_data['account_id'] = account_id_1
        
        # sum balance and total outgoing from 2 to 1
        new_1_bal = self.accounts[account_id_1]['balance'] + self.accounts[account_id_2]['balance']
        self._set_balance(timestamp, account_id_1, new_1_bal)
        new_1_out = self.accounts[account_id_1]['outgoing'] + self.accounts[account_id_2]['outgoing']
        self.accounts[account_id_1]['outgoing'] = new_1_out
        del self.accounts[account_id_2]
        self._commit(timestamp)
        return True
        
    
    def get_balance(self, timestamp, account_id, time_at):
        # if time_at == timestamp:
        self._advance(timestamp)
        # search timestamps
        i = bisect.bisect_right(self._ts, time_at) - 1
        # temporarily sub old accounts for new one
        old_accounts = self._snaps[i]
        if time_at == timestamp:
            old_accounts = self.accounts
        # look up name in new account
        if account_id not in old_accounts:
            return None
        return old_accounts[account_id]['balance']
        

# ## Level 5 — Historical balances

# - `get_balance(timestamp, account_id, time_at)`

#   - Returns the account's balance as it was at `time_at`. `time_at <= timestamp`.

#   - Returns `None` if the account did not exist at `time_at`.

#   - Cashback that had landed by `time_at` is included; cashback that lands later
#     is not.

#   - An account that was merged away is still queryable for any `time_at`
#     **strictly before** the merge, and returns `None` from the merge timestamp
#     onward.