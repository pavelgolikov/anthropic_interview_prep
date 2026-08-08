"""Mock 2 tests. The tests are the spec."""

import unittest

from solution import Bank

DAY = 86_400_000


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()

    def test_create_account(self):
        self.assertTrue(self.bank.create_account(1, "alice"))
        self.assertFalse(self.bank.create_account(2, "alice"))

    def test_new_account_starts_empty(self):
        self.bank.create_account(1, "alice")
        self.assertEqual(self.bank.deposit(2, "alice", 0), 0)

    def test_deposit_returns_new_balance(self):
        self.bank.create_account(1, "alice")
        self.assertEqual(self.bank.deposit(2, "alice", 100), 100)
        self.assertEqual(self.bank.deposit(3, "alice", 50), 150)

    def test_deposit_to_missing_account(self):
        self.assertIsNone(self.bank.deposit(1, "ghost", 100))

    def test_transfer_returns_source_balance(self):
        self.bank.create_account(1, "alice")
        self.bank.create_account(1, "bob")
        self.bank.deposit(2, "alice", 100)
        self.assertEqual(self.bank.transfer(3, "alice", "bob", 30), 70)
        self.assertEqual(self.bank.deposit(4, "bob", 0), 30)

    def test_transfer_insufficient_funds_is_a_noop(self):
        self.bank.create_account(1, "alice")
        self.bank.create_account(1, "bob")
        self.bank.deposit(2, "alice", 100)
        self.assertIsNone(self.bank.transfer(3, "alice", "bob", 101))
        self.assertEqual(self.bank.deposit(4, "alice", 0), 100)
        self.assertEqual(self.bank.deposit(4, "bob", 0), 0)

    def test_transfer_missing_accounts(self):
        self.bank.create_account(1, "alice")
        self.bank.deposit(2, "alice", 100)
        self.assertIsNone(self.bank.transfer(3, "alice", "ghost", 10))
        self.assertIsNone(self.bank.transfer(3, "ghost", "alice", 10))

    def test_transfer_to_self_is_rejected(self):
        self.bank.create_account(1, "alice")
        self.bank.deposit(2, "alice", 100)
        self.assertIsNone(self.bank.transfer(3, "alice", "alice", 10))
        self.assertEqual(self.bank.deposit(4, "alice", 0), 100)


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        for name in ("alice", "bob", "carol"):
            self.bank.create_account(1, name)
            self.bank.deposit(1, name, 1000)

    def test_ranks_by_outgoing_desc(self):
        self.bank.transfer(2, "alice", "bob", 100)
        self.bank.transfer(3, "bob", "carol", 300)
        self.assertListEqual(
            self.bank.top_spenders(4, 3), ["bob(300)", "alice(100)", "carol(0)"]
        )

    def test_ties_broken_by_account_id_asc(self):
        self.bank.transfer(2, "carol", "alice", 50)
        self.bank.transfer(3, "bob", "alice", 50)
        self.assertListEqual(
            self.bank.top_spenders(4, 3), ["bob(50)", "carol(50)", "alice(0)"]
        )

    def test_limit_is_respected(self):
        self.bank.transfer(2, "alice", "bob", 100)
        self.assertListEqual(self.bank.top_spenders(3, 1), ["alice(100)"])

    def test_n_larger_than_account_count(self):
        self.assertEqual(len(self.bank.top_spenders(2, 99)), 3)

    def test_incoming_does_not_reduce_outgoing(self):
        self.bank.transfer(2, "alice", "bob", 400)
        self.bank.transfer(3, "bob", "alice", 100)
        self.assertListEqual(self.bank.top_spenders(4, 2), ["alice(400)", "bob(100)"])


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.bank.create_account(1, "alice")
        self.bank.deposit(1, "alice", 10_000)

    def test_pay_returns_sequential_ids(self):
        self.assertEqual(self.bank.pay(2, "alice", 100), "payment1")
        self.assertEqual(self.bank.pay(3, "alice", 100), "payment2")

    def test_pay_withdraws_immediately(self):
        self.bank.pay(2, "alice", 100)
        self.assertEqual(self.bank.deposit(3, "alice", 0), 9_900)

    def test_pay_rejects_missing_account_and_overdraft(self):
        self.assertIsNone(self.bank.pay(2, "ghost", 1))
        self.assertIsNone(self.bank.pay(2, "alice", 10_001))
        self.assertEqual(self.bank.deposit(3, "alice", 0), 10_000)

    def test_cashback_lands_after_exactly_one_day(self):
        self.bank.pay(2, "alice", 1_000)  # 2% of 1000 = 20
        self.assertEqual(self.bank.deposit(2 + DAY - 1, "alice", 0), 9_000)
        self.assertEqual(self.bank.deposit(2 + DAY, "alice", 0), 9_020)

    def test_cashback_is_floored(self):
        self.bank.pay(2, "alice", 149)  # 2% of 149 = 2.98 -> 2
        self.assertEqual(self.bank.deposit(2 + DAY, "alice", 0), 10_000 - 149 + 2)

    def test_payment_status(self):
        pid = self.bank.pay(2, "alice", 1_000)
        self.assertEqual(self.bank.get_payment_status(3, "alice", pid), "IN_PROGRESS")
        self.assertEqual(
            self.bank.get_payment_status(2 + DAY, "alice", pid), "CASHBACK_RECEIVED"
        )

    def test_payment_status_rejects_wrong_owner_or_unknown_ids(self):
        self.bank.create_account(1, "bob")
        pid = self.bank.pay(2, "alice", 100)
        self.assertIsNone(self.bank.get_payment_status(3, "bob", pid))
        self.assertIsNone(self.bank.get_payment_status(3, "alice", "payment99"))
        self.assertIsNone(self.bank.get_payment_status(3, "ghost", pid))

    def test_payments_count_as_outgoing(self):
        self.bank.create_account(1, "bob")
        self.bank.deposit(1, "bob", 10_000)
        self.bank.pay(2, "alice", 500)
        self.bank.transfer(2, "bob", "alice", 200)
        self.assertListEqual(
            self.bank.top_spenders(3, 2), ["alice(500)", "bob(200)"]
        )

    def test_cashback_does_not_earn_cashback(self):
        self.bank.pay(2, "alice", 10_000)  # cashback 200
        self.assertEqual(self.bank.deposit(2 + 3 * DAY, "alice", 0), 200)


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.bank.create_account(1, "alice")
        self.bank.create_account(1, "bob")
        self.bank.deposit(1, "alice", 1_000)
        self.bank.deposit(1, "bob", 500)

    def test_merge_sums_balances(self):
        self.assertTrue(self.bank.merge_accounts(2, "alice", "bob"))
        self.assertEqual(self.bank.deposit(3, "alice", 0), 1_500)

    def test_merged_account_disappears(self):
        self.bank.merge_accounts(2, "alice", "bob")
        self.assertIsNone(self.bank.deposit(3, "bob", 10))
        self.assertIsNone(self.bank.transfer(3, "alice", "bob", 10))
        self.assertListEqual(self.bank.top_spenders(3, 5), ["alice(0)"])

    def test_merge_rejects_bad_arguments(self):
        self.assertFalse(self.bank.merge_accounts(2, "alice", "alice"))
        self.assertFalse(self.bank.merge_accounts(2, "alice", "ghost"))
        self.assertFalse(self.bank.merge_accounts(2, "ghost", "alice"))

    def test_merge_sums_outgoing(self):
        self.bank.create_account(1, "carol")
        self.bank.transfer(2, "alice", "carol", 100)
        self.bank.transfer(2, "bob", "carol", 200)
        self.bank.merge_accounts(3, "alice", "bob")
        self.assertListEqual(
            self.bank.top_spenders(4, 5), ["alice(300)", "carol(0)"]
        )

    def test_pending_cashback_follows_the_merge(self):
        self.bank.pay(2, "bob", 500)  # cashback 10, due at 2 + DAY
        self.bank.merge_accounts(3, "alice", "bob")
        self.assertEqual(self.bank.deposit(4, "alice", 0), 1_000)
        self.assertEqual(self.bank.deposit(2 + DAY, "alice", 0), 1_010)

    def test_payment_status_moves_to_the_surviving_account(self):
        pid = self.bank.pay(2, "bob", 500)
        self.bank.merge_accounts(3, "alice", "bob")
        self.assertEqual(self.bank.get_payment_status(4, "alice", pid), "IN_PROGRESS")
        self.assertIsNone(self.bank.get_payment_status(4, "bob", pid))
        self.assertEqual(
            self.bank.get_payment_status(2 + DAY, "alice", pid), "CASHBACK_RECEIVED"
        )


class TestLevel5(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.bank.create_account(10, "alice")
        self.bank.create_account(10, "bob")

    def test_balance_before_creation_is_none(self):
        self.assertIsNone(self.bank.get_balance(100, "alice", 9))
        self.assertEqual(self.bank.get_balance(100, "alice", 10), 0)

    def test_unknown_account(self):
        self.assertIsNone(self.bank.get_balance(100, "ghost", 50))

    def test_balance_walks_the_history(self):
        self.bank.deposit(20, "alice", 100)
        self.bank.deposit(30, "alice", 50)
        self.assertEqual(self.bank.get_balance(100, "alice", 19), 0)
        self.assertEqual(self.bank.get_balance(100, "alice", 20), 100)
        self.assertEqual(self.bank.get_balance(100, "alice", 29), 100)
        self.assertEqual(self.bank.get_balance(100, "alice", 30), 150)
        self.assertEqual(self.bank.get_balance(100, "alice", 999), 150)

    def test_transfers_appear_on_both_sides(self):
        self.bank.deposit(20, "alice", 100)
        self.bank.transfer(30, "alice", "bob", 40)
        self.assertEqual(self.bank.get_balance(100, "alice", 30), 60)
        self.assertEqual(self.bank.get_balance(100, "bob", 30), 40)
        self.assertEqual(self.bank.get_balance(100, "bob", 29), 0)

    def test_cashback_appears_at_its_landing_time(self):
        self.bank.deposit(20, "alice", 10_000)
        self.bank.pay(30, "alice", 1_000)  # cashback 20 at 30 + DAY
        later = 30 + DAY + 5
        self.assertEqual(self.bank.get_balance(later, "alice", 30 + DAY - 1), 9_000)
        self.assertEqual(self.bank.get_balance(later, "alice", 30 + DAY), 9_020)

    def test_merged_account_history_survives_until_the_merge(self):
        self.bank.deposit(20, "alice", 100)
        self.bank.deposit(20, "bob", 700)
        self.bank.merge_accounts(50, "alice", "bob")
        self.assertEqual(self.bank.get_balance(100, "bob", 49), 700)
        self.assertIsNone(self.bank.get_balance(100, "bob", 50))
        self.assertEqual(self.bank.get_balance(100, "alice", 50), 800)
        self.assertEqual(self.bank.get_balance(100, "alice", 49), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
