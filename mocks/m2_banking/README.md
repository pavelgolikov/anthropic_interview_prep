# Mock 2 — Banking System


You are implementing a simplified banking backend. All state is in memory.
Timestamps are integers in **milliseconds** and are non-decreasing across calls.
There is no wall clock — time advances only when a method is called.

All amounts are integers. Balances can never go negative.

---

## Level 1 — Initial design & basic functions

- `create_account(timestamp, account_id)`
  - Returns `True` if the account was created, `False` if it already exists.
  - New accounts start with a balance of 0.
- `deposit(timestamp, account_id, amount)`
  - Returns the balance after the deposit, or `None` if the account does not exist.
- `transfer(timestamp, source_account_id, target_account_id, amount)`
  - Moves `amount` from source to target. Returns the **source's** balance
    afterwards.
  - Returns `None` if either account does not exist, if the two ids are equal, or
    if the source has insufficient funds. Nothing is moved in those cases.

---

## Level 2 — Data structures & data processing

- `top_spenders(timestamp, n)`
  - Returns at most `n` strings of the form `"account_id(total_outgoing)"`.
  - `total_outgoing` is the total ever transferred **out** of the account. It is
    not reduced by incoming transfers or deposits.
  - Ordered by `total_outgoing` descending, ties by `account_id` ascending.
  - Accounts that have never sent anything are included, with `0`.

---

## Level 3 — Refactoring & encapsulation

Accounts can now make payments that earn cashback.

- `pay(timestamp, account_id, amount)`
  - Withdraws `amount` immediately and returns a payment id of the form
    `"payment1"`, `"payment2"`, … numbered globally in order of creation across
    all accounts, starting at 1.
  - Returns `None` if the account does not exist or has insufficient funds.
  - A payment counts toward `total_outgoing`, exactly like a transfer.
  - Cashback of `2%` of `amount`, **rounded down**, is credited back to the
    account `86400000` ms (24 hours) later. Cashback is not outgoing, and it does
    not itself earn cashback.
- `get_payment_status(timestamp, account_id, payment)`
  - Returns `"IN_PROGRESS"` if the cashback has not been credited yet, or
    `"CASHBACK_RECEIVED"` once it has.
  - Returns `None` if the account does not exist, the payment does not exist, or
    the payment was not made by that account.

Cashback lands exactly at `payment_timestamp + 86400000`; an operation at that
timestamp sees it as already credited.

---

## Level 4 — Extending design & functionality

- `merge_accounts(timestamp, account_id_1, account_id_2)`
  - Merges `account_id_2` into `account_id_1`. Returns `True` on success, `False`
    if either account does not exist or the two ids are equal.
  - Balances are summed into `account_id_1`; `total_outgoing` is summed too.
  - `account_id_2` ceases to exist. Operations on it afterwards behave as if it
    never existed.
  - Cashback still pending for `account_id_2` is credited to `account_id_1` when
    it lands.
  - Payments made by `account_id_2` remain queryable, but now under
    `account_id_1`.

---

## Level 5 — Historical balances

- `get_balance(timestamp, account_id, time_at)`
  - Returns the account's balance as it was at `time_at`. `time_at <= timestamp`.
  - Returns `None` if the account did not exist at `time_at`.
  - Cashback that had landed by `time_at` is included; cashback that lands later
    is not.
  - An account that was merged away is still queryable for any `time_at`
    **strictly before** the merge, and returns `None` from the merge timestamp
    onward.
