"""
Spec T22 (27 September 2026): the Trader's list is B3's list at consent, and B3 reads what stands before it waits.
From the corridor harness's Series A of 26 September as tester `bear` (run `2026-09-26-215325-bear`): A5 was refused by
MCP Police — "This agent's destination list is empty: its owner has listed nobody yet, so it may pay nobody." — because
the answer book filed `counterparties: []` for every Trader it consented. Each test here was red on main: the book filed
an empty list, the record carried none, and B3 waited ninety seconds for a hash that had no reason to move.

The doubles are the existing injection points: `answer_book` is pure; the consent walks against the connector double
(tests/consent_double.py) through `corridor_harness.http_request`; `step_pause` runs against the fake MCP session
(tests/fakes.py) through `session_factory`, with a token store of its own carrying the Trader's consent record.
"""
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_consent as C  # noqa: E402
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402
import tables as T  # noqa: E402

try:
    from .fakes import FakeClock, FakeSession, OWNER, POLICY_HASH, run_file, runner_for
    from .test_the_harness_consents_its_own_agents import ConsentBase, FUNDING
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeClock, FakeSession, OWNER, POLICY_HASH, run_file, runner_for
    from test_the_harness_consents_its_own_agents import ConsentBase, FUNDING

B3_LIST = [T.address(key) for key in T.TRADER_LIST_B3]
OTHER_HASH = "0x9f41ad0c6e2b58147ac3d9f0b6512e8837d4ca7091fe2b6d5308cc41ab97e260"
FILED_AT = "2026-09-27T01:00:00Z"
TRADER_ROW = {"id": "trader.v1", "name": "Trader", "defaultRank": "agent",
              "questionnaire": {"holdAboveUsd": "10", "maxTxPerDay": "50", "chains": ["arbitrum", "base", "ethereum"],
                                "assets": ["USDC", "USDT", "WETH"], "venues": ["uniswap_v3", "pancakeswap_v3", "curve", "best_direct", "cctp", "usdt0"]}}
PAYER_ROW = {"id": "payer.v1", "name": "Payer", "defaultRank": "agent",
             "questionnaire": {"holdAboveUsd": "10", "maxTxPerDay": "20", "chains": ["arbitrum", "base", "ethereum"], "assets": ["USDC", "USDT"]}}


class TheBookFilesB3sList(unittest.TestCase):
    def test_the_traders_list_is_the_eight_addresses_of_trader_list_b3_in_b3s_order_under_the_scope_agent(self):
        answers = C.answer_book("trader", TRADER_ROW, {})
        self.assertEqual(answers["counterparties"], B3_LIST)
        self.assertEqual(len(answers["counterparties"]), 8)
        self.assertEqual(answers["counterpartiesScope"], "agent")
        # the eight are the lines B3 writes, in the order the Series' own paragraph names them, and the lines the pause reads aloud
        self.assertEqual(re.findall(r"0x[0-9a-fA-F]{40}", S.BY_ID["B3"].text), B3_LIST)
        self.assertEqual([key for _, key in S.B3_LINES], T.TRADER_LIST_B3)
        self.assertNotIn("", answers["counterparties"])
        for address in answers["counterparties"]:
            self.assertRegex(address, r"^0x[0-9a-fA-F]{40}$", "an address on every declared chain, never a venue word")

    def test_the_traders_book_whole(self):
        """The dict the PR body carries verbatim: the book's four, the role's own count and assets, the chains, the scope and the list."""
        self.assertEqual(C.answer_book("trader", TRADER_ROW, {}), {
            "perTxUsd": "20", "dailyUsd": "100", "holdAboveUsd": "50", "maxTxPerDay": "50", "chains": ["arbitrum", "base"],
            "assets": ["USDC", "USDT", "WETH"], "counterpartiesScope": "agent", "counterparties": B3_LIST,
        })

    def test_the_payers_book_is_unchanged(self):
        """A guard: the Payer's list is still the run file's listed address under the run file's scope, and payer_nogas the same."""
        payer = C.answer_book("payer", PAYER_ROW, {"listed_address": OWNER, "payer_list_scope": "shared"})
        self.assertEqual((payer["counterpartiesScope"], payer["counterparties"], payer["maxTxPerDay"]), ("shared", [OWNER], "20"))
        nogas = C.answer_book("payer_nogas", PAYER_ROW, {"listed_address": OWNER})
        self.assertEqual((nogas["counterpartiesScope"], nogas["counterparties"]), ("agent", [OWNER]))
        with self.assertRaises(C.ConsentStop) as stopped:
            C.answer_book("payer", PAYER_ROW, {"listed_address": ""})
        self.assertEqual(stopped.exception.sentence, C.LISTED_ADDRESS_SENTENCE)

    def test_the_module_says_the_list_is_b3s_in_one_sentence_and_no_longer_says_it_opens_empty(self):
        sentence = "the Trader's list is `T.TRADER_LIST_B3`, the eight lines B3 names, so a Trader may trade from its first consent"
        module, docstring = " ".join(C.__doc__.split()), " ".join((C.answer_book.__doc__ or "").split())
        self.assertIn(sentence, module)
        self.assertIn(sentence, docstring)
        for gone in ("opens empty", "filed EMPTY", "pay nobody", "the Trader's empty", "questionnaire.venues"):
            self.assertNotIn(gone, module + docstring, gone)


class TheConsentRecordCarriesWhatWasFiled(ConsentBase):
    def test_the_traders_press_carries_the_eight_and_the_record_reads_them_back(self):
        stored = self.consent("trader")
        press = self.double.presses[0]["body"]
        self.assertEqual(press["answers"]["counterparties"], B3_LIST, "the eight lines, checksummed as tables.py pins them")
        self.assertEqual(press["answers"]["counterpartiesScope"], "agent")
        # the double is the platform's form check (an address on every declared chain): the eight pass it, and the Trader is born
        self.assertEqual(len(self.double.agents), 1)
        self.assertEqual(self.double.agents[0]["document"]["scope"]["counterparties_allowed"], [a.lower() for a in B3_LIST])
        # the record: the addresses filed, beside when they were filed, where the harness always stored the tokens
        self.assertEqual(stored["counterparties"], B3_LIST)
        self.assertTrue(stored["consented_at"])
        record = h.read_json(os.path.join(self.store, "alpha-trader.json"))
        self.assertEqual(record["counterparties"], B3_LIST)
        self.assertIn("created with the book's answers", record["consented_by"])
        self.assertEqual(record["funding_address"], FUNDING)

    def test_the_payers_record_carries_the_one_address_it_filed(self):
        stored = self.consent("payer")
        self.assertEqual(stored["counterparties"], [OWNER])

    def test_a_hand_over_files_nothing_and_the_record_says_none_unless_this_harness_created_the_agent(self):
        customer = self.born()
        self.double.plant_agent(customer["id"], "alpha-payer", "payer.v1", connected=True, counterparties=[OWNER.lower()])
        stored = self.consent("payer")
        self.assertNotIn("counterparties", stored, "an agent born elsewhere: the harness filed no list, so the record claims none")
        self.assertIn("handed over the connection it already holds", stored["consented_by"])
        # a Trader this harness created, consented again by hand-over (the token refused, the same connection): the list it filed stands
        self.consent("trader")
        self.double.calls.clear()
        again = self.consent("trader")
        self.assertIn("handed over the connection it already holds", again["consented_by"])
        self.assertEqual(again["counterparties"], B3_LIST, "the record keeps what this harness filed at creation")


class B3Base(unittest.TestCase):
    """B3's pause against the fake corridor, with a token store of the runner's own carrying the Trader's consent record."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.said = []
        self.asked = []
        self.clock = FakeClock()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def runner_with(self, session, extra=None, answer=""):
        """A runner whose store holds t-trader's tokens with `extra` on the record (None: no record at all)."""
        oauth = h.Oauth("https://mcppro.aeredium.io", os.path.join(self.tmp, "store"), say=self.said.append)
        if extra is not None:
            oauth.store_tokens("t-trader", {"access_token": "at-" + "x" * 24, "refresh_token": "rt-" + "x" * 24}, "mcp-x", extra=extra)

        def ask(question):
            self.asked.append(question)
            return answer
        return h.Runner("t", run_file(), oauth, h.RunFolder(self.tmp, "t"), say=self.said.append, ask=ask, sleep=self.clock.sleep,
                        clock=self.clock, session_factory=lambda label: session)

    def b3(self, runner):
        test = S.BY_ID["B3"]
        return runner.step_pause(test, test.steps[0], None)

    def status_reads(self, session):
        return [c for c in session.calls if c[1] == "wallet.wallet_status"]


class MovingSession(FakeSession):
    """A Wallet whose hash moves after the first reads: the save changed something, as B3 always expected."""

    def __init__(self, moves_after=1, **kwargs):
        super().__init__(**kwargs)
        self.moves_after = moves_after
        self.reads = 0

    def status_answer(self):
        self.reads += 1
        if self.reads > self.moves_after:
            self.policy_hash = OTHER_HASH
        return super().status_answer()


class B3ReadsWhatStandsBeforeItWaits(B3Base):
    RECORD = {"counterparties": B3_LIST, "consented_at": FILED_AT}

    def test_b3_passes_with_the_stood_sentence_and_both_hashes_without_a_wait_where_the_list_stands_and_the_hash_does_not_move(self):
        session = FakeSession(role_id="trader.v1")
        runner = self.runner_with(session, self.RECORD)
        outcome = self.b3(runner)
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)
        self.assertEqual(outcome.sentence, "the list stood from consent (eight lines, filed %s); the save changed nothing and the hash did not move (before %s, after %s)."
                         % (FILED_AT, POLICY_HASH, POLICY_HASH))
        self.assertEqual(outcome.line, outcome.sentence)
        self.assertEqual(outcome.evidence["came_back"], "before: %s\nafter: %s" % (POLICY_HASH, POLICY_HASH), "both hashes are the evidence")
        self.assertEqual(outcome.evidence["policy_hash"], POLICY_HASH)
        self.assertEqual(outcome.evidence["expected"], h.B3_STOOD_EXPECTED)
        self.assertEqual(outcome.evidence["who"], "the MCP Wallet's wallet_status")
        # no ninety-second wait: the clock never moved, nobody was asked to wait or skip, and the hash was read once before and once after
        self.assertEqual(self.clock.now, 0.0)
        self.assertEqual(self.asked, ["Press Enter when done: "])
        self.assertEqual(len(self.status_reads(session)), 2)
        # the person was told the eight lines, and not that they must write them
        for what, key in S.B3_LINES:
            self.assertIn("  %s: %s" % (what, T.address(key)), self.said)
        self.assertNotIn("  " + h.B3_NOT_FROM_CONSENT_LINE, self.said)

    def test_b3_passes_with_todays_sentence_where_the_list_stands_and_the_hash_moved(self):
        session = MovingSession(moves_after=1, role_id="trader.v1")
        runner = self.runner_with(session, self.RECORD)
        outcome = self.b3(runner)
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)
        self.assertEqual(outcome.sentence, "the policy hash moved (before %s, after %s)." % (POLICY_HASH, OTHER_HASH))
        self.assertEqual(self.clock.now, 0.0)
        self.assertEqual(self.asked, ["Press Enter when done: "])

    def test_a_record_carrying_no_list_takes_todays_road_and_a_hash_that_does_not_move_is_never_a_pass(self):
        session = FakeSession(role_id="trader.v1")
        runner = self.runner_with(session, {"consented_at": FILED_AT})  # a Trader consented before Spec T22
        outcome = self.b3(runner)
        self.assertEqual(outcome.outcome, h.SKIPPED, outcome.sentence)
        self.assertEqual(outcome.sentence, "the policy hash had not moved within ninety seconds and the person chose to skip; skipped, not passed.")
        self.assertGreaterEqual(self.clock.now, h.HASH_WAIT_SECONDS, "the wait was the wait")
        self.assertEqual(self.asked, ["Press Enter when done: ", "Wait another ninety seconds, or skip this test? [w/s] "])
        self.assertIn("  " + h.B3_NOT_FROM_CONSENT_LINE, self.said, "the person is told the list does not stand from consent")

    def test_a_record_carrying_no_list_still_passes_where_the_hash_moves(self):
        session = MovingSession(moves_after=2, role_id="trader.v1")
        runner = self.runner_with(session, {"consented_at": FILED_AT})
        outcome = self.b3(runner)
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)
        self.assertEqual(outcome.sentence, "the policy hash moved (before %s, after %s)." % (POLICY_HASH, OTHER_HASH))

    def test_a_record_carrying_another_list_takes_todays_road(self):
        for other in (B3_LIST[:7], list(reversed(B3_LIST)), [OWNER], [], [a.lower() for a in B3_LIST]):
            self.setUp()
            session = FakeSession(role_id="trader.v1")
            runner = self.runner_with(session, {"counterparties": other, "consented_at": FILED_AT})
            self.assertIsNone(runner.trader_list_from_consent(), other)
            outcome = self.b3(runner)
            self.assertEqual(outcome.outcome, h.SKIPPED, (other, outcome.sentence))
            self.assertIn("  " + h.B3_NOT_FROM_CONSENT_LINE, self.said)
            self.tearDown()

    def test_no_record_and_no_token_store_take_todays_road(self):
        session = FakeSession(role_id="trader.v1")
        runner = self.runner_with(session, None)
        self.assertIsNone(runner.trader_list_from_consent())
        self.assertEqual(self.b3(runner).outcome, h.SKIPPED)
        self.setUp()
        runner = runner_for(FakeSession(role_id="trader.v1"), self.tmp)  # the unit tests' runner, with no store at all
        self.assertIsNone(runner.oauth)
        self.assertIsNone(runner.trader_list_from_consent())
        self.assertEqual(self.b3(runner).outcome, h.SKIPPED)

    def test_the_reading_names_the_eight_and_when_they_were_filed(self):
        runner = self.runner_with(FakeSession(role_id="trader.v1"), self.RECORD)
        self.assertEqual(runner.trader_list_from_consent(), {"counterparties": B3_LIST, "consented_at": FILED_AT})
        self.setUp()  # a store of its own: store_tokens merges over a record that stands
        runner = self.runner_with(FakeSession(role_id="trader.v1"), {"counterparties": B3_LIST})
        self.assertEqual(runner.trader_list_from_consent()["consented_at"], "a time the record does not state")

    def test_a_hash_the_wallet_never_stated_is_a_failure_to_read_even_where_the_list_stands(self):
        session = FakeSession(role_id="trader.v1", policy_hash=None)
        runner = self.runner_with(session, self.RECORD)
        outcome = self.b3(runner)
        self.assertEqual(outcome.outcome, h.FAIL, outcome.sentence)
        self.assertIn("the Wallet stated no policy hash before this step", outcome.sentence)

    def test_only_b3_reads_the_record_b8_still_waits_for_the_hash_to_move(self):
        session = FakeSession(role_id="trader.v1")
        runner = self.runner_with(session, self.RECORD)
        test = S.BY_ID["B8"]
        first = test.steps[0]
        self.assertIsInstance(first, S.Pause)
        self.assertTrue(first.hash_moves)
        outcome = runner.step_pause(test, first, None)
        self.assertEqual(outcome.outcome, h.SKIPPED, outcome.sentence)
        self.assertGreaterEqual(self.clock.now, h.HASH_WAIT_SECONDS, "B8 exercises the mirror's refresh (Rule 9): the hash must move")
        self.assertNotIn("  " + h.B3_NOT_FROM_CONSENT_LINE, self.said)

    def test_b3s_pause_tells_the_person_the_lines_stand_from_consent_and_to_change_nothing(self):
        step = S.BY_ID["B3"].steps[0]
        self.assertIsInstance(step, S.Pause)
        self.assertTrue(step.hash_moves)
        self.assertEqual(step.agent, "trader")
        for words in ("stand from consent", "Open Set limits for the Trader", "change nothing", "press Enter"):
            self.assertIn(words, step.text, words)
        self.assertNotIn("write exactly", step.text)
        self.assertEqual(S.BY_ID["B3"].text, S.BY_ID["B3"].text.strip(), "the Series' own paragraph is untouched")
        self.assertIn("write exactly these lines and save", S.BY_ID["B3"].text)


if __name__ == "__main__":
    unittest.main()
