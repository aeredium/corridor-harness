"""The unexpected-allow guard stops the run (Spec T1 §5, §11), and the ordinary refusals do not."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

WALLET = "0x1111111111111111111111111111111111111111"
OWNER = "0xfec697fc2D4323aE7618BFF2347C01E29653FB57"
HASH = "0x" + "11" * 32


def rpc_answer(payload, is_error=False):
    result = {"content": [{"type": "text", "text": json.dumps(payload) if not isinstance(payload, str) else payload}]}
    if is_error:
        result["isError"] = True
    body = {"jsonrpc": "2.0", "id": 1, "result": result}
    return h.McpAnswer(200, body, json.dumps(body), 1)


class FakeSession:
    """A corridor that answers as told: Police allows or denies, the Wallet builds or refuses."""

    POLICE_PROPS = {"action_kind": {}, "chain": {}, "asset_symbol": {}, "to_address": {}, "amount_usd_cents": {}, "child_wallet_id": {}}
    WALLET_PROPS = {"wallet_id": {}, "action": {}, "amount_usd": {}, "to_address": {}, "chain": {}, "asset": {}, "police_receipt": {}, "ticket_id": {}}

    def __init__(self, police="allow", wallet="ticket"):
        self.police = police
        self.wallet = wallet
        self.calls = []
        self.submits = []
        self.secrets_seen = []
        self.tools = {
            "aerconnect_my_agent": {"name": "aerconnect_my_agent", "inputSchema": {"properties": {}}},
            "police.check_action": {"name": "police.check_action", "inputSchema": {"properties": self.POLICE_PROPS}},
            "police.can_sign": {"name": "police.can_sign", "inputSchema": {"properties": {}}},
            "wallet.build_transaction": {"name": "wallet.build_transaction", "inputSchema": {"properties": self.WALLET_PROPS}},
            "wallet.submit_transaction": {"name": "wallet.submit_transaction", "inputSchema": {"properties": {"wallet_id": {}, "ticket_id": {}}}},
            "police.assignment_status": {"name": "police.assignment_status", "description": "NOT THE ROAD FOR AN AER CONNECT AGENT. …", "inputSchema": {"properties": {}}},
        }

    def initialize(self, test_id):
        return None

    def tools_list(self, test_id):
        return list(self.tools.values())

    def properties_of(self, tool):
        listed = self.tools.get(tool)
        return listed["inputSchema"]["properties"] if listed else None

    def call(self, tool, args, test_id):
        bare = tool.split(".", 1)[-1]
        if bare in h.ROADS or str(self.tools.get(tool, {}).get("description", "")).startswith(h.NOT_THE_ROAD_SAID):
            raise h.HarnessError("refusing to call %s" % tool)
        self.calls.append((test_id, tool, dict(args)))
        if tool == "aerconnect_my_agent":
            return rpc_answer({"source": "aer-connect", "agent": {"name": "Payer One", "roleId": "payer.v1"},
                               "connection": {"rank": "agent", "standing": "paid"},
                               "wallet": {"id": "w-1", "address": WALLET, "chain": "arbitrum"},
                               "fundingWallet": {"address": OWNER}, "caps": {"said": "no caps"}, "said": "…"})
        if tool == "police.can_sign":
            return rpc_answer({"can_sign": True, "pact_id": "p-1", "policy_hash": "0xhash1"})
        if tool == "police.check_action":
            if self.police == "allow":
                return rpc_answer({"verdict": "allow", "policy_hash": "0xhash1",
                                   "receipt": {"issued": True, "token": "police-receipt-secret-1", "nonce": "n-1"}})
            return rpc_answer({"verdict": "deny", "reason": "denied", "policy_hash": "0xhash1",
                               "sentence": "The destination %s is not on this agent’s list" % args.get("to_address")})
        if tool == "wallet.build_transaction":
            if "police_receipt" not in args:
                return rpc_answer("receipt_missing: This action carries no pre-flight receipt. Nobody enters but through the Police.", is_error=True)
            if self.wallet == "ticket":
                return rpc_answer({"ticket_id": "t-1", "wallet_id": "w-1", "legs": [{"kind": "transfer"}], "policy_hash": "0xhash1"})
            return rpc_answer("agent_destination_not_whitelisted: the destination is not on the list", is_error=True)
        if tool == "wallet.submit_transaction":
            self.submits.append(dict(args))
            return rpc_answer({"ticket_id": args.get("ticket_id"), "legs": [{"tx_hash": HASH}]})
        raise AssertionError("unexpected tool %s" % tool)


class FakeClock:
    """Time that moves only when the runner sleeps, so a ninety-second wait costs nothing."""

    def __init__(self):
        self.now = 0.0

    def sleep(self, seconds):
        self.now += seconds

    def __call__(self):
        return self.now


def runner_for(session, tmp):
    run_file = {"issuer": "https://mcppro.aeredium.io",
                "testers": {"t": {"agents": {"trader": "t-trader", "payer": "t-payer", "payer_nogas": None}, "listed_address": OWNER, "payer_list_scope": "agent"}},
                "chains": {}}
    folder = h.RunFolder(tmp, "t")
    clock = FakeClock()
    return h.Runner("t", run_file, None, folder, say=lambda s: None, ask=lambda q: "", sleep=clock.sleep, clock=clock,
                    session_factory=lambda label: session, require_series_a=False)


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_an_unexpected_allow_stops_the_run_before_anything_is_signed(self):
        session = FakeSession(police="allow", wallet="ticket")
        runner = runner_for(session, self.tmp)
        outcomes = runner.run(["C"], start_at="C2")  # C2 expects Police to refuse the dead address
        self.assertEqual(runner.stopped, "C2")
        self.assertEqual(session.submits, [], "nothing is signed after an unexpected allow")
        c2 = outcomes[0]
        self.assertEqual(c2.test.id, "C2")
        self.assertEqual(c2.outcome, h.FAIL)
        self.assertIn("unexpected allow", c2.sentence)
        self.assertIn("UNEXPECTED ALLOW", c2.evidence["where"] + c2.evidence["expected"] + str(c2.evidence.get("came_back")) + c2.line)
        self.assertNotIn("police-receipt-secret-1", json.dumps(c2.evidence), "the receipt secret does not reach the report")
        for later in outcomes[1:]:
            self.assertEqual(later.outcome, h.NOT_RUN, later.test.id)
        tools_called = [tool for _, tool, _ in session.calls]
        self.assertNotIn("wallet.submit_transaction", tools_called)
        self.assertEqual(tools_called.count("police.check_action"), 1)
        report = runner.report()
        self.assertIn("The series stopped at C2", report)

    def test_an_expected_refusal_passes_and_does_not_stop(self):
        session = FakeSession(police="deny")
        runner = runner_for(session, self.tmp)
        outcomes = runner.run(["C"], start_at="C2")
        self.assertIsNone(runner.stopped)
        c2 = outcomes[0]
        self.assertEqual(c2.outcome, h.PASS, c2.sentence)
        self.assertIn("refused at pre-flight", c2.sentence)
        c3 = outcomes[1]
        self.assertEqual(c3.test.id, "C3")
        self.assertEqual(c3.outcome, h.PASS, c3.sentence)
        self.assertEqual([tool for tid, tool, _ in session.calls if tid == "C3"], ["wallet.build_transaction"])
        # C5 and C6 are skipped (nobody at the terminal moved the hash), so the refusals collected for F3 are
        # C2, C3, C4 and C7 — this fake corridor denies everything.
        self.assertEqual([r["test"] for r in runner.refusals], ["C2", "C3", "C4", "C7"])
        self.assertEqual(runner.refusals[0]["guide_match"], S.DESTINATION_SENTENCE)
        skipped = [o for o in outcomes if o.test.id in ("C5", "C6")]
        self.assertTrue(all(o.outcome == h.SKIPPED for o in skipped), "a hash that never moves is a skip, never a pass")

    def test_a_wallet_refusal_where_pre_flight_was_expected_is_the_wrong_kind(self):
        session = FakeSession(police="allow", wallet="refused")
        runner = runner_for(session, self.tmp)
        outcomes = runner.run(["C"], start_at="C2")
        self.assertIsNone(runner.stopped, "a refusal never stops the run")
        c2 = outcomes[0]
        self.assertEqual(c2.outcome, h.FAIL)
        self.assertIn("wrong kind", c2.evidence["where"])
        self.assertEqual(c2.evidence["who"], "the engine's reason code as the MCP Wallet relayed it")

    def test_the_road_tools_are_never_called(self):
        session = FakeSession()
        oauth_free = h.Mcp.__new__(h.Mcp)
        oauth_free.tools = session.tools
        with self.assertRaises(h.HarnessError):
            h.Mcp.call(oauth_free, "police.assignment_status", {}, "A5")
        with self.assertRaises(h.HarnessError):
            h.Mcp.call(oauth_free, "police.request_assignment", {}, "A5")

    def test_the_series_a_gate_holds_money_back(self):
        session = FakeSession(police="deny")
        run_file = {"issuer": "x", "testers": {"t": {"agents": {"trader": "a", "payer": "b"}, "listed_address": OWNER}}, "chains": {}}
        clock = FakeClock()
        runner = h.Runner("t", run_file, None, h.RunFolder(self.tmp, "t"), say=lambda s: None, ask=lambda q: "", sleep=clock.sleep, clock=clock,
                          session_factory=lambda label: session)
        outcome = runner.run_test(S.BY_ID["C2"])
        self.assertEqual(outcome.outcome, h.SKIPPED)
        self.assertIn("Series A has not passed", outcome.sentence)
        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()
