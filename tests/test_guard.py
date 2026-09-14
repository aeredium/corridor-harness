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

try:
    from .fakes import FakeClock, FakeSession, OWNER, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeClock, FakeSession, OWNER, runner_for


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
