"""
Series A as Spec T2 leaves it: the hash read from the Wallet, A5 comparing hashes and
not verdicts, A4 stated as the product stands, A2 reading the agent's own role, and the
gate that says exactly which of Series A holds money back.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402
import tables as T  # noqa: E402

try:
    from .fakes import FakeSession, OWNER, POLICY_HASH, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeSession, OWNER, POLICY_HASH, runner_for

OTHER_HASH = "0x9f41ad0c6e2b58147ac3d9f0b6512e8837d4ca7091fe2b6d5308cc41ab97e260"
NATIVE_WEI = 1000000000000000
USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
CHAINS = {"arbitrum": {"rpc": "https://rpc.test/arbitrum", "tokens": {"USDC": USDC}, "explorer": ""}}

PAGES = {
    "/.well-known/oauth-authorization-server": (200, "{}"),
    "/healthz": (200, "ok"),
    "/mcp": (401, "unauthorized"),
    "/guide": (200, "The Owner's Guide."),
    "/account": (200, "Your agents."),
    "/terms": (200, "A trading fee applies."),
}


def chain_answer(body):
    """The chain's own RPC: a native balance, and balanceOf/decimals for one token."""
    payload = json.loads(body.decode("utf-8"))
    method, params = payload["method"], payload["params"]
    if method == "eth_getBalance":
        return hex(NATIVE_WEI)
    if method == "eth_call":
        data = params[0]["data"]
        if data.startswith(h.selector("decimals()")):
            return hex(6)
        if data.startswith(h.selector("balanceOf(address)")):
            return hex(30_000_000)  # 30 USDC
    if method == "eth_blockNumber":
        return hex(100)
    if method in ("eth_getTransactionByHash", "eth_getTransactionReceipt"):
        return None  # this fake chain mines nothing; the harness reports the hash unconfirmed
    if method == "eth_getLogs":
        return []
    raise AssertionError("the test reached for %s" % method)


class SeriesABase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._http = h.http_request
        h.http_request = self.canned_http

    def tearDown(self):
        h.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def canned_http(self, method, url, headers=None, body=None, timeout=None):
        if url.startswith("https://rpc.test/"):
            return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": chain_answer(body)}), 1)
        for path, (status, text) in PAGES.items():
            if url.endswith(path):
                return h.HttpAnswer(status, {}, text, 1)
        raise AssertionError("the test reached for %s" % url)

    def outcome_for(self, test_id, session, chains=None):
        runner = runner_for(session, self.tmp, chains=chains)
        outcomes = {o.test.id: o for o in runner.run(["A"])}
        return runner, outcomes[test_id]


class A5Test(SeriesABase):
    """A5 reads the Wallet's hash and Police's judged hash, and compares the two (Spec T2 §2)."""

    def test_one_hash_passes_whatever_the_verdict(self):
        for verdict in ("allow", "deny"):
            session = FakeSession(police=verdict, role_id="trader.v1")
            _, a5 = self.outcome_for("A5", session)
            self.assertEqual(a5.outcome, h.PASS, "%s: %s" % (verdict, a5.sentence))
            self.assertIn(POLICY_HASH, a5.sentence)
            asked = [c for c in session.calls if c[0] == "A5" and c[1] == "police.check_action"]
            self.assertEqual(len(asked), 1, "A5 asks Police exactly once")

    def test_two_hashes_that_differ_fail_with_both_quoted(self):
        session = FakeSession(role_id="trader.v1", judged_hash=OTHER_HASH)
        _, a5 = self.outcome_for("A5", session)
        self.assertEqual(a5.outcome, h.FAIL)
        self.assertIn(POLICY_HASH, a5.sentence)
        self.assertIn(OTHER_HASH, a5.sentence)
        self.assertIn(POLICY_HASH, a5.evidence["came_back"])
        self.assertIn(OTHER_HASH, a5.evidence["came_back"])

    def test_a_wallet_that_states_no_hash_says_so_rather_than_differ(self):
        """A missing hash is not two hashes that differ, and the sentence says which it is."""
        session = FakeSession(role_id="trader.v1", policy_hash=None, judged_hash=OTHER_HASH)
        _, a5 = self.outcome_for("A5", session)
        self.assertEqual(a5.outcome, h.FAIL)
        self.assertIn("the Wallet stated no policy hash", a5.sentence)
        self.assertIn(OTHER_HASH, a5.sentence)

    def test_a_judged_block_without_a_hash_says_so_too(self):
        session = FakeSession(role_id="trader.v1", judged_hash="")
        _, a5 = self.outcome_for("A5", session)
        self.assertEqual(a5.outcome, h.FAIL)
        self.assertIn("Police's judged block carried no policy hash", a5.sentence)
        self.assertIn(POLICY_HASH, a5.sentence)

    def test_no_judged_block_fails_in_polices_own_words(self):
        session = FakeSession(police="deny", role_id="trader.v1", judged=False)
        _, a5 = self.outcome_for("A5", session)
        self.assertEqual(a5.outcome, h.FAIL)
        self.assertIn("no judged block", a5.sentence.lower())
        self.assertIn("is not on this agent", a5.evidence["came_back"])

    def test_a_trader_asks_d2s_question_on_its_own_chain(self):
        session = FakeSession(role_id="trader.v1", chain="base")
        _, a5 = self.outcome_for("A5", session)
        sent = [c[2] for c in session.calls if c[0] == "A5" and c[1] == "police.check_action"][0]
        self.assertEqual(sent["action_kind"], "trade")
        self.assertEqual(sent["chain"], "base")
        self.assertEqual(sent["to_asset"], "WETH")
        self.assertEqual(sent["venue"], "uniswap_v3")
        self.assertEqual(sent["contract_address"], T.address("UNISWAP_V3_BASE"))
        self.assertEqual(sent["amount_usd_cents"], 500)

    def test_a_payer_asks_c1s_question(self):
        """Eitan's run was consented as a Payer under the Trader's label; A5 asks what it can ask."""
        session = FakeSession(role_id="payer.v1", chain="arbitrum")
        _, a5 = self.outcome_for("A5", session)
        sent = [c[2] for c in session.calls if c[0] == "A5" and c[1] == "police.check_action"][0]
        self.assertEqual(sent["action_kind"], "transfer_stable")
        self.assertEqual(sent["amount_usd_cents"], 100)
        self.assertEqual(sent["to_address"], "0xfec697fc2D4323aE7618BFF2347C01E29653FB57")
        self.assertNotIn("venue", sent)
        self.assertEqual(a5.outcome, h.PASS, a5.sentence)

    def test_polices_receipt_never_reaches_a5s_evidence(self):
        """A5's one check_action is allowed, so Police issues a receipt; the report never carries it."""
        session = FakeSession(police="allow", role_id="trader.v1", judged=False)
        _, a5 = self.outcome_for("A5", session)
        self.assertEqual(a5.outcome, h.FAIL, "no judged block, so the whole answer is quoted")
        dumped = json.dumps(a5.evidence)
        self.assertIn("police-receipt-secret-1", json.dumps(session.check_action_answer({})),
                      "the fake corridor really does hand out a receipt")
        self.assertNotIn("police-receipt-secret-1", dumped, "the receipt secret does not reach the report")
        self.assertIn("<redacted>", dumped)

    def test_a_trader_on_a_chain_with_no_listed_router_names_none(self):
        """A5 still compares hashes on a chain the product does not offer; it invents no address."""
        session = FakeSession(role_id="trader.v1", chain="aeredium-testnet")
        _, a5 = self.outcome_for("A5", session)
        sent = [c[2] for c in session.calls if c[0] == "A5" and c[1] == "police.check_action"][0]
        self.assertEqual(sent["chain"], "aeredium-testnet")
        self.assertEqual(sent["contract_address"], "", "no router is listed for that chain, so none is named")
        self.assertIn("has no listed Uniswap router", a5.line)
        self.assertEqual(a5.outcome, h.PASS, a5.sentence)

    def test_a_payer_with_no_listed_address_asks_nothing_and_says_why(self):
        session = FakeSession(role_id="payer.v1")
        runner = h.Runner("t", {"issuer": "https://mcppro.aeredium.io", "chains": {},
                                "testers": {"t": {"agents": {"trader": "t-trader"}, "listed_address": ""}}},
                          None, h.RunFolder(self.tmp, "t"), say=lambda s: None, ask=lambda q: "",
                          session_factory=lambda label: session, require_series_a=False)
        outcome = runner.run_test(S.BY_ID["A5"])
        self.assertEqual(outcome.outcome, h.FAIL)
        self.assertIn("names no listed_address", outcome.sentence)
        self.assertEqual([c for c in session.calls if c[1] == "police.check_action"], [],
                         "the harness never invents a destination")

    def test_nothing_is_built_or_signed_by_a5(self):
        session = FakeSession(role_id="trader.v1")
        self.outcome_for("A5", session)
        tools = [tool for _, tool, _ in session.calls]
        self.assertNotIn("wallet.build_transaction", tools)
        self.assertNotIn("wallet.submit_transaction", tools)

    def test_the_hash_comes_from_get_balances_when_wallet_status_lacks_it(self):
        session = FakeSession(role_id="trader.v1", pact_in_status=False)
        _, a5 = self.outcome_for("A5", session)
        self.assertEqual(a5.outcome, h.PASS, a5.sentence)
        self.assertIn(POLICY_HASH, a5.sentence)


class A4Test(SeriesABase):
    """A4 as the product stands (Spec T2 §4)."""

    def test_the_wallets_own_chain_passes_with_a_note_naming_spec_49(self):
        _, a4 = self.outcome_for("A4", FakeSession(role_id="trader.v1"), chains=CHAINS)
        self.assertEqual(a4.outcome, h.PASS_NOTE, a4.sentence)
        self.assertIn("Spec 49", json.dumps(a4.note))

    def test_rails_where_the_wallet_states_them(self):
        session = FakeSession(role_id="trader.v1", rails=["ethereum", "arbitrum", "base"])
        runner = runner_for(session, self.tmp, chains=CHAINS)
        outcome = runner.run_test(S.BY_ID["A4"])
        self.assertIn(outcome.outcome, (h.PASS, h.PASS_NOTE))
        self.assertIn("its rails", outcome.sentence)

    def test_a_chain_outside_the_three_fails_in_the_guards_words(self):
        session = FakeSession(role_id="trader.v1", chain="aeredium-testnet")
        runner = runner_for(session, self.tmp)
        outcome = runner.run_test(S.BY_ID["A4"])
        self.assertEqual(outcome.outcome, h.FAIL)
        self.assertIn("which the product does not offer", outcome.sentence)

    def test_the_native_balance_is_read_as_the_number_the_wallet_sends(self):
        _, a4 = self.outcome_for("A4", FakeSession(role_id="trader.v1"), chains=CHAINS)
        self.assertIn("the Wallet says %d wei" % NATIVE_WEI, a4.line)
        self.assertNotIn("None wei", a4.line)
        self.assertIn("they agree", a4.sentence)

    def test_the_token_balance_is_read_from_the_chain_alone_and_noted(self):
        runner, a4 = self.outcome_for("A4", FakeSession(role_id="trader.v1"), chains=CHAINS)
        self.assertIn("read from arbitrum's own RPC", a4.line)
        self.assertIn("30 USDC", a4.line)
        self.assertIn("Spec 49", a4.note["got"])
        self.assertIn("ERC-20 balances are not read here", a4.note["got"], "the Wallet's own sentence is quoted")
        self.assertTrue(runner.a4_native_balance, "the native comparison was made, and it gates money")

    def test_a_wallet_that_states_no_native_balance_fails_the_gating_check(self):
        session = FakeSession(role_id="trader.v1", native_wei=None)
        runner = runner_for(session, self.tmp, chains=CHAINS)
        outcome = runner.run_test(S.BY_ID["A4"])
        self.assertEqual(outcome.outcome, h.FAIL)
        self.assertIs(runner.a4_native_balance, False)


class ChainReaderFaultTest(SeriesABase):
    """A door that answers something other than a hex quantity is a fault, never the end of a run."""

    def canned_http(self, method, url, headers=None, body=None, timeout=None):
        if url.startswith("https://rpc.test/"):
            payload = json.loads(body.decode("utf-8"))
            if payload["method"] == "eth_call":  # the token read answers null
                return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": None}), 1)
            return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": chain_answer(body)}), 1)
        for path, (status, text) in PAGES.items():
            if url.endswith(path):
                return h.HttpAnswer(status, {}, text, 1)
        raise AssertionError("the test reached for %s" % url)

    def test_a_null_token_read_is_a_note_and_the_run_goes_on(self):
        runner, a4 = self.outcome_for("A4", FakeSession(role_id="trader.v1"), chains=CHAINS)
        self.assertIn(a4.outcome, (h.PASS, h.PASS_NOTE), a4.sentence)
        self.assertIn("USDC not read", a4.line)
        self.assertTrue(runner.a4_native_balance, "the native comparison still stands")
        self.assertEqual([o.test.id for o in runner.outcomes][-1], "A8", "the run reached the end of Series A")


class SecretsInTheReportTest(SeriesABase):
    """A note quotes a door's own words, so it is scrubbed exactly as an evidence block is."""

    class Leaky(FakeSession):
        def balances_answer(self):
            row = FakeSession.balances_answer(self)
            row["receipt"] = {"token": "wallet-secret-token-xyz"}
            row.pop("sentence")
            return row

    def test_a_secret_in_a_note_never_reaches_the_report(self):
        runner, a4 = self.outcome_for("A4", self.Leaky(role_id="trader.v1"), chains=CHAINS)
        self.assertIn("wallet-secret-token-xyz", json.dumps(a4.note), "the note really did quote the answer")
        report = runner.report()
        self.assertNotIn("wallet-secret-token-xyz", report)
        self.assertIn("<redacted>", report)


class A2Test(SeriesABase):
    """A2 reads the role against the label the run file gives the agent (Spec T2 §9)."""

    def test_a_trader_under_the_trader_label_passes(self):
        _, a2 = self.outcome_for("A2", FakeSession(role_id="trader.v1"))
        self.assertEqual(a2.outcome, h.PASS, a2.sentence)
        self.assertIn("t-trader", a2.line)

    def test_a_payer_under_the_trader_label_fails_and_names_the_consent_button(self):
        _, a2 = self.outcome_for("A2", FakeSession(role_id="payer.v1"))
        self.assertEqual(a2.outcome, h.FAIL)
        self.assertIn("trader.v1", a2.sentence)
        self.assertIn("Connect a different agent", a2.sentence)

    def test_a_payer_under_the_payer_label_passes(self):
        session = FakeSession(role_id="payer.v1")
        runner = runner_for(session, self.tmp)
        step = S.Check("my_agent_facts", {"role": "payer"})
        outcome = runner.check_my_agent_facts(S.BY_ID["A2"], step, None)
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)
        self.assertIn("t-payer", outcome.line)

    def test_the_summary_says_which_label_series_a_ran_as(self):
        runner = runner_for(FakeSession(role_id="trader.v1"), self.tmp, chains=CHAINS)
        runner.run(["A"])
        report = runner.report()
        self.assertIn("Series A ran as t-trader, the run file's trader", report)
        self.assertIn("the agent itself reported role trader.v1", report)


class ChainMustBeReadBeforeMoneyMoves(SeriesABase):
    """
    Spec T2 §5 as amended 14 September 2026. The founder's ruling: "a missing RPC should make
    anybody worry." A native-balance check that could not be made holds money back exactly as a
    failure does, and every money test says which chain could not be read.
    """

    RPC_FAULT = None  # set by a test: the JSON-RPC error body the chain answers

    def canned_http(self, method, url, headers=None, body=None, timeout=None):
        if url.startswith("https://rpc.test/"):
            if self.RPC_FAULT is not None:
                return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "error": self.RPC_FAULT}), 1)
            return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": chain_answer(body)}), 1)
        for path, (status, text) in PAGES.items():
            if url.endswith(path):
                return h.HttpAnswer(status, {}, text, 1)
        raise AssertionError("the test reached for %s" % url)

    def run_a_and_c(self, chains):
        session = FakeSession(police="allow", wallet="ticket", role_id="trader.v1")
        runner = h.Runner("t", {"issuer": "https://mcppro.aeredium.io", "chains": chains,
                                "testers": {"t": {"agents": {"trader": "t-trader", "payer": "t-payer"},
                                                  "listed_address": OWNER}}},
                          None, h.RunFolder(self.tmp, "t"), say=lambda s: None, ask=lambda q: "",
                          session_factory=lambda label: session)
        return runner, session, runner.run(["A", "C"])

    def money_tests_in(self, outcomes):
        return [o for o in outcomes if o.test.moves_money and o.test.agent != "payer_nogas"]

    def test_no_rpc_for_the_agents_chain_skips_every_money_test_naming_it(self):
        runner, session, outcomes = self.run_a_and_c(chains={})
        money = self.money_tests_in(outcomes)
        self.assertTrue(money, "Series C moves money")
        for outcome in money:
            self.assertEqual(outcome.outcome, h.SKIPPED, outcome.test.id)
            self.assertIn("A4's native-balance check was not made: the run file names no RPC for arbitrum",
                          outcome.sentence, outcome.test.id)
        tools = [tool for _, tool, _ in session.calls]
        self.assertNotIn("wallet.build_transaction", tools, "nothing was built")
        self.assertNotIn("wallet.submit_transaction", tools, "nothing was signed")
        self.assertEqual(session.submits, [])
        self.assertIn("Total moved by allowed actions: 0 dollars", runner.report())

    def test_a_chain_that_answers_a_fault_skips_every_money_test_quoting_it(self):
        self.RPC_FAULT = {"code": -32000, "message": "archive node unavailable"}
        try:
            runner, session, outcomes = self.run_a_and_c(chains=CHAINS)
        finally:
            self.RPC_FAULT = None
        money = self.money_tests_in(outcomes)
        self.assertTrue(money)
        for outcome in money:
            self.assertEqual(outcome.outcome, h.SKIPPED, outcome.test.id)
            self.assertIn("A4's native-balance check was not made: arbitrum could not be read", outcome.sentence)
            self.assertIn("archive node unavailable", outcome.sentence, "the chain's own fault is quoted")
        self.assertEqual(session.submits, [])
        self.assertIsNone(runner.a4_native_balance)

    def test_a_chain_that_answers_lets_money_through(self):
        """The same run with a chain that answers: the gate opens, so the two above mean something."""
        runner, session, outcomes = self.run_a_and_c(chains=CHAINS)
        self.assertTrue(runner.series_a_passed, runner.series_a_gate_said)
        self.assertIn("A4's native-balance check passed", runner.series_a_gate_said)
        first = [o for o in outcomes if o.test.id == "C1"][0]
        self.assertNotEqual(first.outcome, h.SKIPPED, first.sentence)
        self.assertIn("wallet.build_transaction", [tool for _, tool, _ in session.calls])


class MoneyGateTest(SeriesABase):
    """Exactly which of Series A holds money back (Spec T2 §5)."""

    def gate_after(self, session, chains=None):
        runner = h.Runner("t", {"issuer": "https://mcppro.aeredium.io", "chains": CHAINS if chains is None else chains,
                                "testers": {"t": {"agents": {"trader": "t-trader", "payer": "t-payer"},
                                                  "listed_address": "0xfec697fc2D4323aE7618BFF2347C01E29653FB57"}}},
                          None, h.RunFolder(self.tmp, "t"), say=lambda s: None, ask=lambda q: "",
                          session_factory=lambda label: session)
        runner.run(["A"])
        return runner

    def test_a6_does_not_hold_money_back(self):
        PAGES["/guide"] = (200, "Our fee is 0.05%, five basis points.")
        try:
            runner = self.gate_after(FakeSession(role_id="trader.v1"))
        finally:
            PAGES["/guide"] = (200, "The Owner's Guide.")
        a6 = next(o for o in runner.outcomes if o.test.id == "A6")
        self.assertEqual(a6.outcome, h.FAIL, "the pin fired on a page that does advertise the fee")
        self.assertTrue(runner.series_a_passed, "A6 proves wording, not the corridor's judgement")
        self.assertIn("A6 and A4's notes gate nothing", runner.series_a_gate_said)

    def test_a4s_note_does_not_hold_money_back(self):
        runner = self.gate_after(FakeSession(role_id="trader.v1"))
        a4 = next(o for o in runner.outcomes if o.test.id == "A4")
        self.assertEqual(a4.outcome, h.PASS_NOTE)
        self.assertTrue(runner.series_a_passed)

    def test_a_check_that_could_not_be_made_holds_money_back(self):
        """
        Spec T2 §5 as amended 14 September 2026, on the founder's ruling that "a missing RPC
        should make anybody worry": the native-balance check gates money only when it was made
        and passed, and a check that could not be made holds money back exactly as a failure does.
        """
        runner = self.gate_after(FakeSession(role_id="trader.v1"), chains={})
        self.assertIsNone(runner.a4_native_balance, "no RPC, so the check could not be made")
        self.assertFalse(runner.series_a_passed, "a check that was not made holds money back")
        self.assertIn("A4's native-balance check was not made: the run file names no RPC for arbitrum",
                      runner.series_a_gate_said)
        self.assertNotIn("A4's native-balance check passed", runner.series_a_gate_said)
        self.assertNotIn("holds nothing back", runner.series_a_gate_said)

    def test_a5_holds_money_back(self):
        runner = self.gate_after(FakeSession(role_id="trader.v1", judged=False))
        self.assertFalse(runner.series_a_passed)
        self.assertIn("A5 fail", runner.series_a_gate_said)
        skipped = runner.run_test(S.BY_ID["C1"])
        self.assertEqual(skipped.outcome, h.SKIPPED)
        self.assertIn("A5 fail", skipped.sentence)

    def test_a2_holds_money_back(self):
        runner = self.gate_after(FakeSession(role_id="payer.v1"))
        self.assertFalse(runner.series_a_passed)
        self.assertIn("A2 fail", runner.series_a_gate_said)

    def test_a4s_native_balance_holds_money_back(self):
        runner = self.gate_after(FakeSession(role_id="trader.v1", native_wei=None))
        self.assertFalse(runner.series_a_passed)
        self.assertIn("A4's native-balance check fail", runner.series_a_gate_said)

    def test_the_gate_is_named_in_the_report(self):
        runner = self.gate_after(FakeSession(role_id="trader.v1"))
        report = runner.report()
        self.assertIn("A1, A2, A3, A5 and A4's native-balance check, which gates money only when it was made "
                      "and passed", report)
        self.assertIn("never says money moved without the chain having been read", report)

    def test_the_report_says_why_the_check_was_not_made(self):
        runner = self.gate_after(FakeSession(role_id="trader.v1"), chains={})
        self.assertIn("A4's native-balance check was not made: the run file names no RPC for arbitrum",
                      runner.report())


if __name__ == "__main__":
    unittest.main()
