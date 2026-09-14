"""
The hash is read from the Wallet, where it lives (Spec T2 §1, §2), and a figure the
Wallet sends as a JSON number is read as the number it is (Spec T2 §4).

MCP Police answered the harness, in its own words: "MCP Police carries no tool called
“can_sign”." Every hash therefore comes from the MCP Wallet's `wallet_status`, as
`pact.policy_hash`, with `get_balances`' `pact_budget.policy_hash` as a second source.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402

try:
    from .fakes import FakeSession, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeSession, runner_for

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
EITAN = "0x5237c7e1b0c4f1a9d8e3b26a5f470c91d2846ebb73f5a0c1e94d6b28fa310577"


def answer_from(name):
    """One recorded answer, read back exactly as the door sent it."""
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as handle:
        raw = handle.read()
    return h.McpAnswer(200, json.loads(raw), raw, 1)


class HashReaderTest(unittest.TestCase):
    def test_the_recorded_wallet_status_answer_states_the_hash(self):
        answer = answer_from("wallet-status-eitan.json")
        self.assertEqual(h.wallet_policy_hash(answer.data), EITAN)
        self.assertTrue(EITAN.startswith("0x5237c7e1"))

    def test_the_pact_is_read_whole(self):
        pact = h.wallet_pact(answer_from("wallet-status-eitan.json").data)
        self.assertEqual(pact["policy_hash"], EITAN)
        self.assertEqual(pact["state"], "active")
        self.assertEqual(pact["policy_generation"], 4)

    def test_a_change_between_two_answers_is_seen(self):
        before = h.wallet_policy_hash(answer_from("wallet-status-eitan.json").data)
        after = h.wallet_policy_hash(answer_from("wallet-status-eitan-after-save.json").data)
        self.assertNotEqual(before, after)
        self.assertTrue(h.hash_moved(before, after), "a save moves the hash")
        self.assertFalse(h.hash_moved(before, before), "an unchanged pact does not")
        self.assertFalse(h.hash_moved(EITAN, EITAN.upper().replace("0X", "0x")),
                         "the same hash in another case is the same hash")

    def test_get_balances_is_the_second_source(self):
        balances = {"wallet_id": "w-1", "pact_budget": {"id": "p-1", "policy_hash": EITAN, "spent_usd": 0}}
        self.assertEqual(h.wallet_policy_hash(balances), EITAN)

    def test_a_wallet_that_states_no_hash_reads_as_none(self):
        self.assertIsNone(h.wallet_policy_hash({"wallet_id": "w-1", "chain": "arbitrum"}))
        self.assertIsNone(h.wallet_policy_hash(None))
        self.assertTrue(h.hash_moved(None, EITAN))


class PactInTheReportTest(unittest.TestCase):
    """Spec T2 §1: pact.id, pact.state and pact.policy_generation are read, and a reader can see them."""

    def test_the_summary_carries_the_pact_the_wallet_states(self):
        tmp = tempfile.mkdtemp()
        try:
            runner = runner_for(FakeSession(role_id="trader.v1"), tmp)
            runner.session("trader", "A5")
            runner.read_policy_hash("trader", "A5")
            report = runner.report()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("Pact p-1, state active, policy generation 3.", report)
        self.assertIn("Policy hash at the start %s" % EITAN, report)


class JudgedBlockTest(unittest.TestCase):
    """Police carries the pact it judged under on allow, deny and hold alike (Spec T2 §2)."""

    def test_every_verdict_carries_the_hash(self):
        for verdict in ("allow", "deny", "hold"):
            data = {"verdict": verdict, "judged": {"pact_id": "p-1", "policy_hash": EITAN}}
            self.assertEqual(h.judged_policy_hash(data), EITAN, verdict)
            self.assertIsNotNone(h.judged_in(data), verdict)

    def test_an_answer_without_a_judged_block_reads_as_none(self):
        data = {"verdict": "deny", "sentence": "The destination is not on this agent's list"}
        self.assertIsNone(h.judged_in(data))
        self.assertIsNone(h.judged_policy_hash(data))


class SecondSourceTest(unittest.TestCase):
    """get_balances is only reached when wallet_status states no hash (Spec T2 §1)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_get_balances_is_not_called_when_wallet_status_states_the_hash(self):
        session = FakeSession(role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        runner.session("trader", "A5")
        self.assertEqual(runner.read_policy_hash("trader", "A5"), EITAN)
        self.assertEqual([c for c in session.calls if c[1] == "wallet.get_balances"], [],
                         "the second source is only reached when the first states none")

    def test_get_balances_is_called_when_wallet_status_states_none(self):
        session = FakeSession(role_id="trader.v1", pact_in_status=False)
        runner = runner_for(session, self.tmp)
        runner.session("trader", "A5")
        self.assertEqual(runner.read_policy_hash("trader", "A5"), EITAN)
        self.assertEqual(len([c for c in session.calls if c[1] == "wallet.get_balances"]), 1)
        self.assertEqual((runner.pacts.get("trader") or {}).get("pact_id"), "p-1")

    def test_a_door_that_refuses_both_leaves_the_hash_unread(self):
        session = FakeSession(role_id="trader.v1", pact_in_status=False, policy_hash=None)
        runner = runner_for(session, self.tmp)
        runner.session("trader", "A5")
        self.assertIsNone(runner.read_policy_hash("trader", "A5"))


class OneHashEverywhereTest(unittest.TestCase):
    """F4 compares Police's receipt and the Wallet's ticket with the Wallet's own pact (Spec T2 §1)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def f4_over(self, receipt_hash, ticket_hash):
        import series as S
        runner = runner_for(FakeSession(role_id="trader.v1"), self.tmp)
        runner.session("trader", "F4")
        runner.walks["D2"] = [{"kind": S.ALLOWED, "police": {"policy_hash": receipt_hash},
                               "build": {"policy_hash": ticket_hash}}]
        return runner.check_one_hash_everywhere(S.BY_ID["F4"], S.Check("one_hash_everywhere", {"test": "D2"}), None)

    def test_three_that_agree_pass(self):
        outcome = self.f4_over(EITAN, EITAN)
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)
        self.assertIn("the receipt, the ticket and the Wallet's pact carry one policy hash", outcome.sentence)
        self.assertIn("wallet_status %s" % EITAN, outcome.line)

    def test_one_that_differs_fails_with_all_three_quoted(self):
        outcome = self.f4_over("0xdead", EITAN)
        self.assertEqual(outcome.outcome, h.FAIL)
        self.assertIn("0xdead", outcome.line)
        self.assertIn(EITAN, outcome.line)


class NumericBalanceTest(unittest.TestCase):
    """The Wallet sends the native balance as a JSON number; asking for a string printed None (Spec T2 §4)."""

    def test_find_key_returns_a_number_as_the_number_it_is(self):
        answer = {"wallet_id": "w-1", "native": {"symbol": "ETH", "wei": 1000000000000000}}
        self.assertEqual(h.find_key(answer, ["wei"]), 1000000000000000)
        self.assertIsNone(h.find_key(answer, ["wei"], str), "asking for a string is what printed None wei")

    def test_a_string_is_still_read(self):
        self.assertEqual(h.find_key({"native": {"wei": "1000000000000000"}}, ["wei"]), "1000000000000000")

    # The report line that prints this figure is proved end to end, through the harness's own
    # A4 check, by test_series_a.A4Test.test_the_native_balance_is_read_as_the_number_the_wallet_sends.


if __name__ == "__main__":
    unittest.main()
