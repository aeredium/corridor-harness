"""
The chain guard (Spec T2 §6): a wallet on a chain the product does not offer runs no
money series, and is told so in words.

Victor's Trader lived on `aeredium-testnet`. That is Victor's to recreate, not the
harness's — but the harness must refuse the money series for it plainly, and Series A
must still run and report, because Series A moves nothing.
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
    from .fakes import FakeSession, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeSession, runner_for

GUARD = ("t-trader's wallet is on aeredium-testnet, which the product does not offer; the series runs on "
         "ethereum, arbitrum and base. Create the agent again on one of those and consent it.")

PAGES = {
    "/.well-known/oauth-authorization-server": (200, '{"issuer": "https://mcppro.aeredium.io"}'),
    "/healthz": (200, "ok"),
    "/mcp": (401, "unauthorized"),
    "/guide": (200, "The Owner's Guide. Nothing here about what a trade costs."),
    "/account": (200, "Your agents."),
    "/terms": (200, "A trading fee applies to trades."),
}


def canned_http(method, url, headers=None, body=None, timeout=None):
    """The connector's public pages, so Series A can run with no network."""
    for path, (status, text) in PAGES.items():
        if url.endswith(path):
            return h.HttpAnswer(status, {}, text, 1)
    raise AssertionError("the test reached for %s" % url)


class ChainGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._http = h.http_request
        h.http_request = canned_http

    def tearDown(self):
        h.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_series(self, chain, series=("A", "C")):
        session = FakeSession(police="allow", wallet="ticket", chain=chain, role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        return runner, session, runner.run(list(series))

    def test_a_wallet_off_the_three_chains_runs_no_money_test(self):
        runner, session, outcomes = self.run_series("aeredium-testnet")
        money = [o for o in outcomes if o.test.moves_money]
        self.assertTrue(money, "Series C moves money")
        guarded = 0
        for outcome in money:
            self.assertEqual(outcome.outcome, h.SKIPPED, outcome.test.id)
            if outcome.test.agent == "payer_nogas":
                continue  # C8 has no agent in the run file at all, and says so first
            # The guard is the agent's, so it names the label that test runs as.
            self.assertEqual(outcome.sentence, GUARD.replace("t-trader", "t-%s" % outcome.test.agent), outcome.test.id)
            guarded += 1
        self.assertGreater(guarded, 3)
        tools = [tool for _, tool, _ in session.calls]
        self.assertNotIn("wallet.build_transaction", tools, "nothing was built")
        self.assertNotIn("wallet.submit_transaction", tools, "nothing was signed")
        self.assertEqual(session.submits, [])

    def test_series_a_still_runs_and_reports(self):
        runner, session, outcomes = self.run_series("aeredium-testnet")
        ran = [o.test.id for o in outcomes if o.test.series == "A"]
        self.assertEqual(ran, ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"])
        by_id = {o.test.id: o for o in outcomes}
        self.assertEqual(by_id["A1"].outcome, h.PASS, by_id["A1"].sentence)
        self.assertEqual(by_id["A5"].outcome, h.PASS, by_id["A5"].sentence)
        self.assertEqual(by_id["A6"].outcome, h.PASS, by_id["A6"].sentence)
        # A4 says the chain is not one the product offers, in the guard's own words.
        self.assertEqual(by_id["A4"].outcome, h.FAIL)
        self.assertIn("which the product does not offer", by_id["A4"].sentence)
        report = runner.report()
        # The money tests carry the sentence whole; inside A4 it is one clause of a longer one.
        self.assertIn(GUARD.replace("t-trader", "t-payer"), report)
        self.assertIn(GUARD.rstrip("."), report)

    def test_a_wallet_on_one_of_the_three_is_not_guarded(self):
        for chain in S.PRODUCT_CHAINS:
            runner, session, outcomes = self.run_series(chain, series=("C",))
            guarded = [o for o in outcomes if o.sentence.endswith("consent it.")]
            self.assertEqual(guarded, [], chain)

    def test_the_guard_reads_the_chain_from_wallet_status_not_from_my_agent(self):
        session = FakeSession(chain="aeredium-testnet", role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        runner.session("trader", "A2")
        # my_agent named the same chain, but the guard's reading is wallet_status's.
        self.assertEqual(runner.chain_of("trader", "A2"), "aeredium-testnet")
        self.assertEqual(runner.chain_guard("trader", "A2"), GUARD)
        self.assertIn("wallet.wallet_status", [tool for _, tool, _ in session.calls])

    def test_the_consent_says_the_agent_is_on_a_chain_the_product_does_not_offer(self):
        session = FakeSession(chain="aeredium-testnet", role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        runner.session("trader", "consent")
        notes = runner.consent_notes("trader")
        self.assertEqual(len(notes), 1, notes)
        self.assertEqual(notes[0], "Note: " + GUARD)

    def test_the_consent_says_when_the_wrong_agent_was_consented(self):
        """Eitan's first run: a Payer consented under the Trader's label, found at consent time."""
        session = FakeSession(chain="arbitrum", role_id="payer.v1")
        runner = runner_for(session, self.tmp)
        runner.session("trader", "consent")
        notes = runner.consent_notes("trader")
        self.assertEqual(len(notes), 1, notes)
        self.assertIn("t-trader reports role payer.v1, not trader.v1", notes[0])
        self.assertIn("Connect a different agent", notes[0])

    def test_the_consent_says_nothing_when_the_agent_is_the_right_one(self):
        session = FakeSession(chain="arbitrum", role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        runner.session("trader", "consent")
        self.assertEqual(runner.consent_notes("trader"), [])

    def test_a_wallet_that_names_no_chain_is_guarded_too(self):
        session = FakeSession(chain="", role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        runner.session("trader", "A2")
        said = runner.chain_guard("trader", "A2")
        self.assertIsNotNone(said)
        self.assertIn("no chain it would name", said)


if __name__ == "__main__":
    unittest.main()
