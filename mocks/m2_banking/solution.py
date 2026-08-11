"""Mock 2 — Banking System.  Implement Bank here."""

REASONS = ['transfer_out', 'transfer_in', 'deposit']

class Bank:
    def __init__(self):
        self.accounts = {} # account_id : { "timestamp": int, "balance": int, "total_spending" int}

    def create_account(self, timestamp, account_id):
        if account_id in self.accounts.keys():
            return False
        # create the account with 0 balance
        self.accounts[account_id] = {"timestamp": timestamp, "balance": 0, "total_spending": 0}
        return True
    
    # HELPERS -------------------------------------------------------------------
    def _set_balance(self, timestamp, account_id, new_balance, reason):
        if reason == 'transfer_out':
            old_balance = self.accounts[account_id]['balance']
            self.accounts[account_id]['total_spending'] += (old_balance - new_balance)
        self.accounts[account_id]['balance'] = new_balance
        return None

    # L1 -----------------------------------------------------------------------
    def deposit(self, timestamp, account_id, amount):
        if account_id not in self.accounts.keys():
            return None
        new_balance = self.accounts[account_id]['balance'] + amount
        self._set_balance(timestamp, account_id, new_balance, 'deposit')
        return new_balance

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
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
        # want pairs (total_spent, account_id)
        pairs = [(v['total_spending'], k) for k, v in self.accounts.items()]
        pairs_sorted = sorted(pairs, key=lambda p: (-p[0], p[1]))[:n]
        top_spender_list_strings = [f"{x[1]}({x[0]})" for x in pairs_sorted]
        return top_spender_list_strings
    

# - `top_spenders(timestamp, n)`
#   - Returns at most `n` strings of the form `"account_id(total_outgoing)"`.
#   - `total_outgoing` is the total ever transferred **out** of the account. It is
#     not reduced by incoming transfers or deposits.
#   - Ordered by `total_outgoing` descending, ties by `account_id` ascending.