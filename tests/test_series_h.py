"""
Series H as version 1.2 of the Series reads it (Spec T6 §3): H5 is run by the harness as the Payer on C1's
own road, with no form step, because the form has no period hold to set; H6 and H7 are left to a person, as
H1 and H4 are; H2 and H3 pause for the owner's passkey and walk what 1.2 says; and no pause asks for a period
total, because the 1.2 form has none.
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

try:
    from .fakes import FakeSession, OWNER, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeSession, OWNER, runner_for


def no_network(*args, **kwargs):
    raise AssertionError("the test reached for the network: %r" % (args[:2],))


class SeriesHTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._http = h.http_request
        h.http_request = no_network

    def tearDown(self):
        h.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_series(self, series):
        session = FakeSession(police="allow", wallet="ticket", role_id="payer.v1")
        runner = runner_for(session, self.tmp)
        return runner, session, {o.test.id: o for o in runner.run(series)}

    def test_h5_runs_by_itself_as_the_payer_on_c1s_road(self):
        runner, session, outcomes = self.run_series(["H"])
        h5 = outcomes["H5"]
        calls = [(tool, args) for tid, tool, args in session.calls if tid == "H5"]
        self.assertEqual([tool for tool, _ in calls], ["police.check_action", "wallet.build_transaction", "wallet.submit_transaction"],
                         "check, build, submit: the corridor's order, with no pause before it")
        check, build, submit = (args for _, args in calls)
        self.assertEqual((check["action_kind"], check["chain"], check["amount_usd_cents"], check["to_address"]),
                         ("transfer_stable", "arbitrum", 100, OWNER))
        self.assertEqual(check.get("asset_symbol", check.get("asset")), "USDC")
        self.assertEqual(build["police_receipt"], "police-receipt-secret-1", "the build carries Police's receipt")
        self.assertEqual(submit["ticket_id"], "t-1", "the submit carries this run's ticket")
        self.assertEqual(session.submits, [{"wallet_id": "w-1", "ticket_id": "t-1"}])
        self.assertNotIn(h5.outcome, (h.SKIPPED, h.PERSON_OUT, h.NOT_RUN), h5.sentence)
        self.assertIsNone(runner.stopped)
        # The same fake corridor answers C1 the same way: H5 is C1's payment, read under Rule 7 as amended.
        _, c1_session, c1_outcomes = self.run_series(["C"])
        c1 = c1_outcomes["C1"]
        self.assertEqual(h5.outcome, c1.outcome)
        self.assertEqual([tool for tid, tool, _ in c1_session.calls if tid == "C1"][-3:], [tool for tool, _ in calls])
        self.assertEqual(h5.evidence["sent"], c1.evidence["sent"], "the same words, under the same names, to the same doors")

    def test_h1_h4_h6_and_h7_are_a_persons_and_h2_and_h3_pause(self):
        runner, session, outcomes = self.run_series(["H"])
        for tid in ("H1", "H4", "H6", "H7"):
            self.assertEqual(outcomes[tid].outcome, h.PERSON_OUT, tid)
        self.assertEqual([tool for tid, tool, _ in session.calls if tid in ("H1", "H4", "H6", "H7")], [], "a person's test calls no door")
        for tid in ("H2", "H3"):
            # Nobody at this terminal moved the hash, so the pause is skipped, and a skip is never a pass.
            self.assertEqual(outcomes[tid].outcome, h.SKIPPED, tid)
            self.assertIn("skipped, not passed", outcomes[tid].sentence)
        report = runner.report()
        for tid in ("H6", "H7"):
            self.assertIn(S.BY_ID[tid].text, report, "%s's text is printed for the person who runs it" % tid)
        self.assertIn("### H5 — Ask me first alone is a complete discretion", report)

    def test_the_dry_run_of_series_h_is_version_1_2s(self):
        by_id = {}
        for line in h.dry_lines(["H"]):
            by_id.setdefault(line.split(" — ", 1)[0], []).append(line)

        def expectations(lines):
            return [line.split("expect: ", 1)[1] for line in lines if line.split(" — ", 1)[1].startswith("expect:")]

        h5 = by_id["H5"]
        self.assertEqual([line.split()[3] for line in h5 if "tools/call" in line],
                         ["police.check_action", "wallet.build_transaction", "wallet.submit_transaction"])
        self.assertFalse(any("[pause]" in line for line in h5), "H5 pauses for nothing: there is no period hold to set")
        self.assertIn('"amount_usd_cents": 100', h5[0])
        self.assertEqual(expectations(h5), [S.ALLOWED])
        h2 = by_id["H2"]
        self.assertEqual(len([line for line in h2 if "[pause]" in line]), 3, "12 dollars, exactly 15 dollars, back to 100")
        # The build line names police.check_action too, in its receipt placeholder, so count the calls by their opening.
        self.assertEqual(len([line for line in h2 if line.startswith("H2 — tools/call police.check_action")]), 4)
        self.assertEqual(expectations(h2), [S.ALLOWED, S.ALLOWED, S.REFUSED, S.ALLOWED])
        self.assertTrue(any("set 'per day' to exactly 15 dollars" in line for line in h2))
        h3 = by_id["H3"]
        self.assertEqual(len([line for line in h3 if "[pause]" in line]), 3, "4 dollars, 5 dollars, back to 20")
        self.assertEqual(expectations(h3), [S.REFUSED, S.ALLOWED])
        self.assertFalse(any("expect: held" in line for line in h3), "1.2's H3 expects no hold")
        for tid in ("H1", "H4", "H6", "H7"):
            self.assertEqual(len(by_id[tid]), 1, tid)
            self.assertIn("left to a person", by_id[tid][0])
        for line in sum(by_id.values(), []):
            self.assertNotIn("period total", line, "the 1.2 form has no period total, so no line asks for one")


if __name__ == "__main__":
    unittest.main()
