"""
Spec T28 (8 October 2026, on the owner's ruling of that day — "What do you think if we fix the harness to answer yes when the question is asked,
and let's see whether that fixes the problem, because that would be the easiest fix of them all?" — agreed with one bound, so the yes is never
blind): the founder confirms a repeat. S7 acknowledges the estate's duplicate screen as a founder would, and only then.

The finding, not re-diagnosed: the first run after Spec T27 refused all three payments at creation — DUPLICATE_UNACKNOWLEDGED, "This looks like a
payment that has already been made recently. Confirm it is intentional to continue." — because the one-dollar book pays the same three invoices
to the owner's wallet on every run, and the run of 4 October lay four days back, inside the estate's seven-day window (setgates.ts
duplicateScreen; config.ts DUPLICATE_WINDOW_DAYS). The double never raised the screen ("no matching payment in the last 7 days", whatever the
register held), which is how the harness reached a live run with no hand for it; it raises it now as the estate does, and `age_runs(days)` is
time passing between two runs.

The spec's tests: (a) a warning naming a payment of an earlier run, four days back → the second review with duplicatesAcknowledged true, the
creation with it, and one note per warning; (b) a warning naming an instruction this run created, or a previouslySentAt after the run began →
no second review, no creation, a finding in the estate's words, S7 fails; (c) no warning → one review and a creation with the field false, as
today; (d) the dry run's new lines and count; (e) the question-mark sentence is gone. Each was red on main.
"""
import datetime as _dt
import os
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import MESSAGES, OWNER_WALLET_FOR_TESTS, EstateDouble, runner_on  # noqa: E402

OWNER = OWNER_WALLET_FOR_TESTS
SENTENCE = "This looks like a payment that has already been made recently. Confirm it is intentional to continue."
PROBE_WORDS = "a duplicate within this run, never acknowledged (Spec T28)"


def by_reference(double):
    """The workspace's runs by the invoice reference of their one instruction (the set of three is never created: S7a creates nothing)."""
    return {s["instructions"][0]["invoiceRef"]: s for s in double.sets.values() if len(s["instructions"]) == 1}


def reviews_and_creations(runner, reference):
    """S7's reviews and creations of the one payment under `reference`, in order: (route, duplicatesAcknowledged)."""
    out = []
    for c in runner.calls:
        if c.station != "S7" or c.route not in ("POST /v1/sets/review", "POST /v1/sets") or not isinstance(c.sent, dict):
            continue
        pays = c.sent.get("pays") or []
        if len(pays) == 1 and pays[0].get("invoiceRef") == reference:
            out.append((c.route, c.sent.get("duplicatesAcknowledged")))
    return out


def set_of_three_reviews(runner):
    return [c.sent.get("duplicatesAcknowledged") for c in runner.calls
            if c.station == "S7" and c.route == "POST /v1/sets/review" and isinstance(c.sent, dict) and len(c.sent.get("pays") or []) == 3]


def note_for(payee, amount, reference, run):
    return H.REPEAT_CONFIRMED_NOTE % (payee, amount, reference, run["createdAt"], run["id"])


def confirmed_words(payee, amount, reference, run):
    return ("the duplicate screen named %s %s under %s, paid on %s (run %s); the founder confirmed it, as a founder would, and the review asked again passed it: "
            "1 possible duplicate(s), acknowledged by the author (Spec T28)" % (payee, amount, reference, run["createdAt"], run["id"]))


class TheBoundIsReadOffTheEstatesOwnWords(unittest.TestCase):
    """The pure functions over a review's payload: the instants, the bound, the amount, the gate's words — and the sentence, the estate's own."""

    STARTED = "2026-10-08T14:37:00.123+08:00"  # now_iso's spelling: the run began at 06:37:00.123 UTC

    def warning(self, sent_at="2026-10-04T06:12:13.456Z", previous="ins-4-october", **detail):
        values = {"payee": "Northwind Supplies", "address": OWNER.lower(), "amountMinor": "500000", "invoiceRef": "HH-0001",
                  "previousInstructionId": previous, "previouslySentAt": sent_at, "windowDays": "7"}
        values.update(detail)
        return {"code": "DUPLICATE_UNACKNOWLEDGED", "message": SENTENCE, "rowIndex": 0, "acknowledgeable": True, "detail": values,
                "provenance": {"source": "payout_instructions", "reference": previous}}

    def test_the_harness_and_the_double_restate_one_sentence_and_one_gate(self):
        self.assertEqual(H.DUPLICATE_UNACKNOWLEDGED_SENTENCE, SENTENCE, "refusals.ts REFUSAL_MESSAGES, word for word")
        self.assertEqual(MESSAGES["DUPLICATE_UNACKNOWLEDGED"], SENTENCE)
        self.assertEqual((H.DUPLICATE_GATE, H.DUPLICATE_UNACKNOWLEDGED, H.DUPLICATE_ACKNOWLEDGED_EVIDENCE),
                         ("duplicate_screen", "DUPLICATE_UNACKNOWLEDGED", "acknowledged by the author"))
        self.assertEqual(H.REPEAT_BOUND_WORDS, "only where the review's duplicate screen names a payment of an earlier run (previouslySentAt before this run began); "
                                               "a duplicate within this run is a finding, never acknowledged", "SPEC.md §3.3, word for word")

    def test_instants_are_read_in_the_estates_spelling_and_the_harnesss_and_nothing_else(self):
        utc = _dt.timezone.utc
        self.assertEqual(H.instant_of("2026-10-04T06:12:13.456Z"), _dt.datetime(2026, 10, 4, 6, 12, 13, 456000, tzinfo=utc))
        self.assertEqual(H.instant_of(self.STARTED), _dt.datetime(2026, 10, 8, 6, 37, 0, 123000, tzinfo=utc))
        self.assertEqual(H.instant_of("2026-10-08T01:07:00-0530"), _dt.datetime(2026, 10, 8, 6, 37, 0, tzinfo=utc))
        self.assertEqual(H.instant_of(H.now_iso()).tzinfo is not None, True, "the harness's own stamp reads back")
        for garbage in (None, "", "4 October", "2026-10-04", "2026-10-04T06:12:13", "2026-13-40T06:12:13Z", 1696400000):
            self.assertIsNone(H.instant_of(garbage), garbage)

    def test_a_payment_of_an_earlier_run_is_within_the_bound(self):
        within, why = H.repeat_within_bound(self.warning(), self.STARTED, {})
        self.assertTrue(within)
        self.assertEqual(why, "a payment of an earlier run: previouslySentAt 2026-10-04T06:12:13.456Z, before this run began (%s); instruction ins-4-october is not one this run created" % self.STARTED)

    def test_a_payment_made_after_the_run_began_is_outside_whatever_its_id(self):
        within, why = H.repeat_within_bound(self.warning(sent_at="2026-10-08T06:37:00.124Z"), self.STARTED, {})
        self.assertFalse(within)
        self.assertEqual(why, "previouslySentAt 2026-10-08T06:37:00.124Z is not before this run began (%s): the payment it names was made within this run" % self.STARTED)
        self.assertFalse(H.repeat_within_bound(self.warning(sent_at="2026-10-08T06:37:00.123Z"), self.STARTED, {})[0], "the very instant the run began is not before it")

    def test_an_instruction_this_run_created_is_outside_whatever_its_clock_says(self):
        """The estate's clock behind the Mac's would put this run's own payment before the run began; the ids catch it."""
        within, why = H.repeat_within_bound(self.warning(previous="ins-mine"), self.STARTED, {"ins-mine": {"key": "P1", "set_id": "set-mine"}})
        self.assertFalse(within)
        self.assertEqual(why, "instruction ins-mine is P1's, which this run created (run set-mine)")

    def test_what_cannot_be_read_cannot_be_bounded(self):
        self.assertEqual(H.repeat_within_bound(self.warning(sent_at="yesterday"), self.STARTED, {}),
                         (False, "previouslySentAt 'yesterday' is not a time the harness can read, so the repeat cannot be bounded"))
        self.assertEqual(H.repeat_within_bound(self.warning(previous=""), self.STARTED, {}),
                         (False, "the warning names no previousInstructionId, so the repeat cannot be bounded"))
        bare = {"code": "DUPLICATE_UNACKNOWLEDGED", "message": SENTENCE}
        self.assertEqual(H.repeat_within_bound(bare, self.STARTED, {})[0], False)
        self.assertEqual(H.repeat_within_bound(self.warning(), "not a time", {}),
                         (False, "this run's start 'not a time' is not a time the harness can read, so the repeat cannot be bounded"))

    def test_the_amount_is_said_in_the_assets_own_decimals(self):
        self.assertEqual(H.asset_amount("500000", "USDC"), "0.50 USDC")
        self.assertEqual(H.asset_amount("10000", "USDC"), "0.01 USDC")
        self.assertEqual(H.asset_amount("490000", "USDC"), "0.49 USDC")
        self.assertEqual(H.asset_amount("1000000", "USDC"), "1.00 USDC")
        self.assertEqual(H.asset_amount("1234567", "USDC"), "1.234567 USDC")
        self.assertEqual(H.asset_amount("1.5", "USDC"), "1.5 (minor units) of USDC", "a figure that is not an integer is said as it came")
        self.assertEqual(H.asset_amount(None, "USDC"), "an amount the estate did not state (minor units) of USDC")

    def test_the_gate_is_reported_with_the_acknowledgeable_list_beside_it_and_the_warning_word_for_word(self):
        payload = {"gates": [{"gate": "duplicate_screen", "passed": False, "refusals": [self.warning()], "evidence": "1 possible duplicate(s) need acknowledgement"}],
                   "acknowledgeable": [self.warning()]}
        self.assertEqual(H.duplicate_gate_words(payload, "USDC"),
                         'duplicate_screen not passed — 1 possible duplicate(s) need acknowledgement; DUPLICATE_UNACKNOWLEDGED: "%s" — Northwind Supplies 0.50 USDC under HH-0001, '
                         'previouslySentAt 2026-10-04T06:12:13.456Z, previousInstructionId ins-4-october; acknowledgeable: 1 (DUPLICATE_UNACKNOWLEDGED)' % SENTENCE)
        self.assertEqual(H.duplicate_gate_words({"gates": []}, "USDC"), "the review carries no duplicate_screen gate")
        self.assertEqual(H.repeat_warnings({"gates": [{"gate": "gas_preflight", "refusals": [self.warning()]}]}), [], "only the duplicate screen's warnings are judged")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheDoubleScreensAsTheEstateDoes(unittest.TestCase):
    """setgates.ts duplicateScreen and payoutsets.ts createSet, as the double restates them: the warning, its detail, the 422, the acknowledgement, the window."""

    @classmethod
    def setUpClass(cls):
        # Holdings keeps four dollars after the run, so the gas gate's dry quotes pass and the duplicate screen is the creation's first blocking
        # refusal (payoutsets.ts createSet throws the first; with no USDC the gas gate's PAYMENT_UNPRICED, 502, would come first)
        cls.double = EstateDouble(holdings_usdc_cents=500)
        cls.tmp = tempfile.mkdtemp()
        cls.first = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        cls.outcomes = {o.station: o for o in cls.first.run()}
        cls.runner = runner_on(cls.double, cls.tmp, start_at="S7")
        cls.runner.load_passkeys()
        cls.runner.resume()
        cls.clerk = cls.runner.clerk()
        cls.row = {"oneOff": {"chain": T.PAYEE_CHAIN, "address": OWNER, "declared": True, "payeeName": "Unlisted destination"}, "asset": "USDC", "chain": T.PAYEE_CHAIN,
                   "amountMinor": "10000", "invoiceRef": "HH-0002"}

    def review(self, row, acknowledged=False):
        return self.runner.request(self.clerk, "POST", "/v1/sets/review", {"pays": [row], "duplicatesAcknowledged": acknowledged}, "test")

    def test_a_repeat_within_seven_days_is_warned_of_in_the_estates_words_with_its_detail(self):
        self.assertEqual(self.outcomes["S7"].outcome, H.PASS, self.outcomes["S7"].line)
        earlier = by_reference(self.double)["HH-0002"]
        answer = self.review(self.row)
        gate = H.duplicate_gate_of(answer.json)
        self.assertEqual((gate["passed"], gate["evidence"]), (False, "1 possible duplicate(s) need acknowledgement"))
        warning = gate["refusals"][0]
        self.assertEqual((warning["code"], warning["message"], warning["rowIndex"], warning["acknowledgeable"]), ("DUPLICATE_UNACKNOWLEDGED", SENTENCE, 0, True))
        self.assertEqual(warning["detail"], {"payee": "Unlisted destination", "address": OWNER.lower(), "amountMinor": "10000", "invoiceRef": "HH-0002",
                                             "previousInstructionId": earlier["instructions"][0]["id"], "previouslySentAt": earlier["createdAt"], "windowDays": "7"})
        self.assertEqual(warning["provenance"], {"source": "payout_instructions", "reference": earlier["instructions"][0]["id"]})
        self.assertEqual(answer.json["acknowledgeable"], [warning], "the review's acknowledgeable list: the duplicate screen, and nothing else today")
        self.assertFalse(answer.json["acceptable"], "an acknowledgeable warning is a gate that has not passed until it is acknowledged")
        self.assertEqual(answer.json["rows"][0]["refusals"][-1], warning, "the warning rides on its row too")

    def test_acknowledged_the_gate_passes_and_the_warning_stays(self):
        answer = self.review(self.row, acknowledged=True)
        gate = H.duplicate_gate_of(answer.json)
        self.assertEqual((gate["passed"], gate["evidence"], len(gate["refusals"])), (True, "1 possible duplicate(s), acknowledged by the author", 1))
        self.assertEqual(len(answer.json["acknowledgeable"]), 1, "still listed: the accountant said yes to it")

    def test_a_creation_not_acknowledged_is_refused_422_in_the_warnings_own_words(self):
        body = {"pays": [self.row], "duplicatesAcknowledged": False, "idempotencyKey": "t28-refused", "reference": "T28 probe"}
        answer = self.runner.request(self.clerk, "POST", "/v1/sets", body, "test")
        self.assertEqual(answer.status, 422)
        self.assertEqual((answer.refusal["code"], answer.refusal["message"], answer.refusal["acknowledgeable"]), ("DUPLICATE_UNACKNOWLEDGED", SENTENCE, True))
        self.assertEqual(answer.sentence(), "DUPLICATE_UNACKNOWLEDGED: %s" % SENTENCE, "the 8 October line, word for word")
        self.assertFalse(any(s["idempotencyKey"] == "t28-refused" for s in self.double.sets.values()), "an unacknowledged refusal creates no run")

    def test_another_reference_another_amount_or_another_chain_is_no_repeat(self):
        for change in ({"invoiceRef": "HH-0002b"}, {"amountMinor": "10001"}, {"chain": "ethereum"}):
            row = dict(self.row, **change)
            if "chain" in change:
                row["oneOff"] = dict(self.row["oneOff"], chain=change["chain"])
            gate = H.duplicate_gate_of(self.review(row).json)
            self.assertEqual((gate["passed"], gate["refusals"], gate["evidence"]), (True, [], "no matching payment in the last 7 days"), change)

    def test_past_the_window_the_screen_remembers_nothing(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        runner_on(double, tmp, invite=double.mint_founder_link()).run()
        double.age_runs(8)
        runner = runner_on(double, tmp, start_at="S7")
        runner.load_passkeys()
        runner.resume()
        answer = runner.request(runner.clerk(), "POST", "/v1/sets/review", {"pays": [self.row], "duplicatesAcknowledged": False}, "test")
        gate = H.duplicate_gate_of(answer.json)
        self.assertEqual((gate["passed"], gate["evidence"]), (True, "no matching payment in the last 7 days"))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ARepeatOfAnEarlierRunIsConfirmedAsAFounderWould(unittest.TestCase):
    """(a) The 8 October run, replayed: a full run, four days, a full run again. Each warning names a payment of the earlier run, so the founder confirms it."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble()
        cls.tmp = tempfile.mkdtemp()
        link = cls.double.mint_founder_link()
        cls.first = runner_on(cls.double, cls.tmp, invite=link)
        cls.first_outcomes = {o.station: o for o in cls.first.run()}
        cls.double.age_runs(4)  # 4 October to 8 October
        cls.earlier = by_reference(cls.double)
        cls.said = []
        cls.runner = runner_on(cls.double, cls.tmp, invite=link, said=cls.said)
        cls.outcomes = {o.station: o for o in cls.runner.run()}
        cls.line = cls.outcomes["S7"].line

    def test_the_first_run_paid_the_book_and_the_second_pays_it_again_one_dollar_each(self):
        self.assertEqual(self.first_outcomes["S7"].outcome, H.PASS, self.first_outcomes["S7"].line)
        self.assertEqual(self.outcomes["S7"].outcome, H.PASS, self.line)
        sets = self.runner.facts["sets"]
        self.assertEqual([(k, sets[k]["landed"]) for k in ("P1", "P2", "P3")], [("P1", True), ("P2", True), ("P3", True)])
        self.assertEqual(self.double.chain.balance_of(OWNER), 2000000, "a dollar a run, every cent to the owner's wallet: the book is unchanged")
        self.assertEqual([p.invoice for p in A.payments()], ["HH-0001", "HH-0002", "HH-0003"], "the harness never changes the book to dodge the screen (§4)")

    def test_each_payment_is_reviewed_reviewed_again_with_the_acknowledgement_and_created_with_it(self):
        for reference in ("HH-0001", "HH-0002", "HH-0003"):
            self.assertEqual(reviews_and_creations(self.runner, reference),
                             [("POST /v1/sets/review", False), ("POST /v1/sets/review", True), ("POST /v1/sets", True)], reference)
        # the estate kept the warning on each run it created, the gate passed by the author's yes
        for key, reference in (("P1", "HH-0001"), ("P2", "HH-0002"), ("P3", "HH-0003")):
            gate = H.duplicate_gate_of(self.double.sets[self.runner.facts["sets"][key]["set_id"]]["review"])
            self.assertEqual((gate["passed"], gate["evidence"]), (True, "1 possible duplicate(s), acknowledged by the author"), key)
            self.assertEqual(gate["refusals"][0]["detail"]["previousInstructionId"], self.earlier[reference]["instructions"][0]["id"], key)
            step = [s for s in self.runner.evidence["S7"] if s["route"] == "POST /v1/sets/review" and s["sent"]["duplicatesAcknowledged"] is True
                    and len(s["sent"]["pays"]) == 1 and s["sent"]["pays"][0]["invoiceRef"] == reference]
            self.assertEqual(len(step), 1, reference)
            self.assertIn("the review asked again with duplicatesAcknowledged true, as the founder's screen sends it (PaymentEntry.tsx)", step[0]["expected"])
            self.assertTrue(step[0]["result"].startswith("answered; duplicate_screen passed — 1 possible duplicate(s), acknowledged by the author; DUPLICATE_UNACKNOWLEDGED: \"%s\"" % SENTENCE),
                            step[0]["result"])
            self.assertTrue(step[0]["result"].endswith("acknowledgeable: 1 (DUPLICATE_UNACKNOWLEDGED)"), step[0]["result"])

    def test_one_note_per_warning_names_the_earlier_run_the_estate_remembered(self):
        notes = [n for n in self.runner.notes["S7"] if n.endswith("(Spec T28)")]
        self.assertEqual(notes, [note_for("Northwind Supplies", "0.50 USDC", "HH-0001", self.earlier["HH-0001"]),
                                 note_for("Unlisted destination", "0.01 USDC", "HH-0002", self.earlier["HH-0002"]),
                                 note_for("Contoso Legal", "0.49 USDC", "HH-0003", self.earlier["HH-0003"])], "three warnings, three notes: S7a's and each payment's name the same three")
        self.assertEqual(notes[0], "the estate's duplicate screen named Northwind Supplies 0.50 USDC under HH-0001 as paid on %s (run %s); this run's founder confirmed it, "
                                   "as a founder would (Spec T28)" % (self.earlier["HH-0001"]["createdAt"], self.earlier["HH-0001"]["id"]), "SPEC.md §2 Implementer, word for word")
        self.assertIn(self.first.facts["sets"]["P1"]["set_id"], notes[0], "the run of the earlier day, read off the runs register S7 already reads")
        report = self.runner.report()
        for note in notes:
            self.assertIn("Note: %s" % note, report)
        self.assertIn('DUPLICATE_UNACKNOWLEDGED: "%s"' % SENTENCE, report, "the warning, quoted word for word in the report (§4)")

    def test_s7_says_what_the_screen_named_and_that_the_founder_confirmed_it(self):
        for key, payee, amount, reference in (("P1", "Northwind Supplies", "0.50 USDC", "HH-0001"), ("P2", "Unlisted destination", "0.01 USDC", "HH-0002"),
                                              ("P3", "Contoso Legal", "0.49 USDC", "HH-0003")):
            self.assertIn("%s; submitted: status approved, approvalsRequired 0" % confirmed_words(payee, amount, reference, self.earlier[reference]), self.line, key)
        self.assertEqual(self.line.count("the estate asked 0 signature(s)"), 3)
        self.assertNotIn("?", self.line.replace("?limit", ""), "never a question mark for a number")

    def test_s7a_reviews_the_set_again_with_the_acknowledgement_and_creates_nothing(self):
        self.assertEqual(set_of_three_reviews(self.runner), [False, True])
        s7a = self.runner.facts["s7a"]
        self.assertEqual(s7a["repeats"]["verdict"], "confirmed")
        self.assertIsNone(s7a["repeat_failure"])
        self.assertIn("the duplicate screen named Northwind Supplies 0.50 USDC under HH-0001, paid on %s (run %s); Unlisted destination 0.01 USDC under HH-0002, paid on %s (run %s); "
                      "Contoso Legal 0.49 USDC under HH-0003, paid on %s (run %s); the founder confirmed them, as a founder would, and the review asked again passed them: "
                      "3 possible duplicate(s), acknowledged by the author (Spec T28)" % (
                          self.earlier["HH-0001"]["createdAt"], self.earlier["HH-0001"]["id"], self.earlier["HH-0002"]["createdAt"], self.earlier["HH-0002"]["id"],
                          self.earlier["HH-0003"]["createdAt"], self.earlier["HH-0003"]["id"]), s7a["said"])
        self.assertEqual(s7a["left"], [], "neither review created a run")
        self.assertFalse(any(n.startswith("S7a: the review carried refusals beside the gas gate's") for n in self.runner.notes["S7"]),
                         "the duplicate screen's warnings are judged, not noted as refusals of another kind")

    def test_no_finding_is_raised_and_the_money_reconciles(self):
        self.assertEqual([f.probe for f in self.runner.findings if PROBE_WORDS in f.probe], [])
        self.assertFalse(any(f.probe.startswith("money moved") for f in self.runner.findings), [f.probe for f in self.runner.findings])
        self.assertTrue(any(n.startswith("money moved (Spec T14 §5)") and "every pair reconciles to the cent" in n for n in self.runner.notes["S10"]), self.runner.notes["S10"])

    def test_the_treasurys_review_names_nothing_so_it_is_reviewed_once_and_created_without_the_field(self):
        treasury = [(c.route, c.sent.get("duplicatesAcknowledged")) for c in self.runner.calls
                    if c.station == "S7" and c.route in ("POST /v1/sets/review", "POST /v1/sets") and isinstance(c.sent, dict)
                    and str((c.sent.get("pays") or [{}])[0].get("invoiceRef", "")).startswith("HT-")]
        self.assertEqual(treasury, [("POST /v1/sets/review", False), ("POST /v1/sets", False)], "HT-<run> is this run's own reference: the screen names nothing")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ARepeatWithinThisRunIsAFindingNeverAcknowledged(unittest.TestCase):
    """(b) The bound: a warning naming a payment made after this run began, or one this run created, is a finding in the estate's words; nothing is acknowledged or created."""

    def test_a_previously_sent_at_after_the_run_began_is_a_finding_and_nothing_is_created(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        first = runner_on(double, tmp, invite=double.mint_founder_link())
        self.assertEqual({o.station: o for o in first.run()}["S7"].outcome, H.PASS)
        double.age_runs(-1 / 96)  # the earlier payments stamped a quarter of an hour on: made, as the estate tells it, after the next run began
        earlier = by_reference(double)
        runner = runner_on(double, tmp, start_at="S7")
        o = {x.station: x for x in runner.run()}["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        for reference in ("HH-0001", "HH-0002", "HH-0003"):
            self.assertEqual(reviews_and_creations(runner, reference), [("POST /v1/sets/review", False)], "no second review, no creation: %s" % reference)
        self.assertEqual(set_of_three_reviews(runner), [False], "S7a's set is not reviewed again either")
        self.assertEqual(double.chain.balance_of(OWNER), 1000000, "nothing of the second run reached the owner's wallet")
        findings = [f for f in runner.findings if PROBE_WORDS in f.probe]
        self.assertEqual([f.probe for f in findings], ["S7a: " + PROBE_WORDS] * 3 + ["P1: " + PROBE_WORDS, "P2: " + PROBE_WORDS, "P3: " + PROBE_WORDS])
        p1 = findings[3]
        previous = earlier["HH-0001"]["instructions"][0]["id"]
        self.assertEqual(p1.said, 'DUPLICATE_UNACKNOWLEDGED: "%s" — Northwind Supplies 0.50 USDC under HH-0001, previouslySentAt %s, previousInstructionId %s; '
                                  "previouslySentAt %s is not before this run began (%s): the payment it names was made within this run; not acknowledged, and nothing was created" % (
                                      SENTENCE, earlier["HH-0001"]["createdAt"], previous, earlier["HH-0001"]["createdAt"], runner.started_at))
        self.assertEqual(p1.route, "POST /v1/sets/review")
        self.assertIn(SENTENCE, p1.came_back, "what came back, verbatim")
        self.assertIn("previousInstructionId not an instruction this run created", p1.expected)
        self.assertIn("P1 (0.50 USDC to %s, the owner's wallet, expected to proceeds to approval): paid to the register's Northwind Supplies on arbitrum, whitelisted; "
                      "the duplicate screen named a payment this run cannot bound — DUPLICATE_UNACKNOWLEDGED: \"%s\"" % (OWNER, SENTENCE), o.line)
        self.assertIn("a finding, not acknowledged, and nothing was created (Spec T28); %s and the one-dollar book" % H.NO_RUN_CREATED, o.line)
        self.assertEqual([n for n in runner.notes["S7"] if n.endswith("(Spec T28)")], [], "nothing confirmed, nothing noted as confirmed")
        report = runner.report()
        self.assertIn("**P1: %s** — DUPLICATE_UNACKNOWLEDGED: \"%s\"" % (PROBE_WORDS, SENTENCE), report)

    def test_a_warning_naming_an_instruction_this_run_created_is_a_finding_and_nothing_is_created(self):
        """Two payments of one book repeat each other — the owner's wallet is every payee's address on a real chain — so P3's review names P1's own instruction."""
        book = [A.Payment("P1", "NORTHWIND_ETHEREUM", "Northwind Supplies", "0.49", "HH-0001", "proceeds to approval", "a test book"),
                A.PAYMENTS_ON_A_REAL_CHAIN[1],
                A.Payment("P3", "CONTOSO_ETHEREUM", "Contoso Legal", "0.49", "HH-0001", "proceeds to approval", "a test book: P1 again, under P1's reference")]
        self.assertLessEqual(A.payments_total_minor(book), T.ONE_DOLLAR_MINOR, "the one-dollar law holds for the test book too")
        with unittest.mock.patch.object(A, "PAYMENTS_ON_A_REAL_CHAIN", book):
            double = EstateDouble(holdings_gas_cents=9971, treasury_gas_cents=11995)  # gas that covers: each review asked once
            runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
            o = {x.station: x for x in runner.run()}["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        p1 = runner.facts["sets"]["P1"]
        self.assertTrue(p1["landed"])
        self.assertEqual(reviews_and_creations(runner, "HH-0001"), [("POST /v1/sets/review", False), ("POST /v1/sets", False), ("POST /v1/sets/review", False)],
                         "P1 reviewed and created; P3 reviewed once — no second review, no creation")
        p3 = runner.facts["sets"]["P3"]
        self.assertEqual((p3["set_id"], p3["landed"], p3["failure"]), (None, False, "a duplicate within this run, not acknowledged"))
        findings = [f for f in runner.findings if PROBE_WORDS in f.probe]
        self.assertEqual([f.probe for f in findings], ["P3: " + PROBE_WORDS])
        self.assertEqual(findings[0].said, 'DUPLICATE_UNACKNOWLEDGED: "%s" — Contoso Legal 0.49 USDC under HH-0001, previouslySentAt %s, previousInstructionId %s; '
                                           "instruction %s is P1's, which this run created (run %s); not acknowledged, and nothing was created" % (
                                               SENTENCE, double.sets[p1["set_id"]]["createdAt"], p1["instruction_id"], p1["instruction_id"], p1["set_id"]))
        self.assertIn("P3 (0.49 USDC to %s, the owner's wallet, expected to proceeds to approval): the duplicate screen named a payment this run cannot bound" % OWNER, o.line)
        self.assertIn("nothing was created (Spec T28); %s and" % H.NO_RUN_CREATED, o.line)
        self.assertEqual(double.chain.balance_of(OWNER), 500000, "P1's forty-nine cents and P2's cent; P3 never left")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheAcknowledgementNotTakenCreatesNothing(unittest.TestCase):
    """§4: a refusal of the second review, or a second review whose gate does not pass, is reported in the estate's words; nothing is created, and S7 fails."""

    def second_run(self, **dial):
        double = EstateDouble(**dial)
        tmp = tempfile.mkdtemp()
        runner_on(double, tmp, invite=double.mint_founder_link()).run()
        double.age_runs(4)
        earlier = by_reference(double)
        runner = runner_on(double, tmp, start_at="S7")
        return double, earlier, runner, {x.station: x for x in runner.run()}["S7"]

    def test_a_screen_that_does_not_take_the_acknowledgement_leaves_the_payment_uncreated_in_the_gates_own_words(self):
        double, earlier, runner, o = self.second_run(acknowledgement_ignored=True)
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertEqual(reviews_and_creations(runner, "HH-0001"), [("POST /v1/sets/review", False), ("POST /v1/sets/review", True)], "reviewed again, never created")
        p1 = runner.facts["sets"]["P1"]
        self.assertEqual((p1["set_id"], p1["failure"]), (None, "the duplicate screen did not pass the acknowledgement"))
        previous = earlier["HH-0001"]["instructions"][0]["id"]
        self.assertIn("the review asked again with the founder's acknowledgement did not pass the duplicate screen as the acknowledgement asks — duplicate_screen not passed — "
                      "1 possible duplicate(s) need acknowledgement; DUPLICATE_UNACKNOWLEDGED: \"%s\" — Northwind Supplies 0.50 USDC under HH-0001, previouslySentAt %s, "
                      "previousInstructionId %s; acknowledgeable: 1 (DUPLICATE_UNACKNOWLEDGED); nothing was created (Spec T28); %s and" % (
                          SENTENCE, earlier["HH-0001"]["createdAt"], previous, H.NO_RUN_CREATED), o.line)
        self.assertEqual(runner.facts["s7a"]["repeats"]["verdict"], "not passed")
        self.assertEqual([n for n in runner.notes["S7"] if n.endswith("(Spec T28)")], [], "nothing confirmed")
        self.assertEqual(double.chain.balance_of(OWNER), 1000000, "the second run moved nothing to the owner's wallet")

    def test_a_refused_second_review_is_told_in_the_estates_words_and_nothing_is_created(self):
        double, earlier, runner, o = self.second_run(acknowledged_review_refused=True)
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertEqual(reviews_and_creations(runner, "HH-0003"), [("POST /v1/sets/review", False), ("POST /v1/sets/review", True)])
        second = [c for c in runner.calls if c.station == "S7" and c.route == "POST /v1/sets/review" and c.sent.get("duplicatesAcknowledged") is True]
        self.assertTrue(second and all(c.status == 401 for c in second), [c.status for c in second])
        self.assertIn("P3 (0.49 USDC to %s, the owner's wallet, expected to proceeds to approval): paid to the register's Contoso Legal on arbitrum, whitelisted; "
                      "the review asked again with the founder's acknowledgement answered NOT_AUTHENTICATED: You are not signed in.; nothing was created (Spec T28); %s and" % (
                          OWNER, H.NO_RUN_CREATED), o.line)
        self.assertEqual(runner.facts["sets"]["P3"]["failure"], "the second review was refused")
        self.assertEqual(runner.facts["s7a"]["repeats"]["verdict"], "refused")
        self.assertIn("the review asked again with the founder's acknowledgement answered NOT_AUTHENTICATED: You are not signed in.; nothing was created (Spec T28)", runner.facts["s7a"]["said"])
        self.assertFalse(any(c.route == "POST /v1/sets" and len(c.sent.get("pays") or []) == 1 and c.sent["pays"][0].get("invoiceRef", "").startswith("HH-")
                             for c in runner.calls if c.station == "S7"), "no payment of the book was created")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class NoWarningNoSecondReview(unittest.TestCase):
    """(c) A review the screen is silent on: one review, a creation with duplicatesAcknowledged false — as today."""

    def test_a_fresh_estate_whose_gas_covers_its_sets_reviews_each_payment_once(self):
        double = EstateDouble(holdings_gas_cents=9971, treasury_gas_cents=11995)  # 4 October's balances: no review is short of gas, so nothing asks it twice
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        o = {x.station: x for x in runner.run()}["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        for reference in ("HH-0001", "HH-0002", "HH-0003"):
            self.assertEqual(reviews_and_creations(runner, reference), [("POST /v1/sets/review", False), ("POST /v1/sets", False)], reference)
        self.assertEqual(set_of_three_reviews(runner), [False])
        self.assertEqual([s["result"] for s in runner.evidence["S7"] if s["route"] == "POST /v1/sets/review" and len(s["sent"]["pays"]) == 1], ["answered"] * 4,
                         "the Treasury's and the three payments' reviews read as they read before")
        self.assertEqual(runner.facts["repeats"], [])
        self.assertEqual([n for n in runner.notes["S7"] if n.endswith("(Spec T28)")], [])
        self.assertNotIn("duplicate screen", o.line)
        self.assertEqual(runner.facts["s7a"]["repeats"]["verdict"], "none")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheTreasuryIsReviewedTheSameWay(unittest.TestCase):
    """The Treasury's shortfall payment (Spec T14) is read for the screen as the three are: a repeat of its earlier run is confirmed and noted."""

    def test_a_repeat_of_the_treasurys_earlier_payment_is_confirmed_before_it_is_created(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        runner_on(double, tmp, invite=double.mint_founder_link()).run()
        double.age_runs(4)
        runner = runner_on(double, tmp, start_at="S7")
        # the Treasury's earlier payment under the reference this run will send: same wallet, chain, asset and amount (the shortfall is a dollar again)
        earlier = next(s for s in double.treasury.sets.values() if s["instructions"][0]["invoiceRef"].startswith("HT-"))
        earlier["instructions"][0]["invoiceRef"] = "HT-%s" % runner.run_stamp
        o = {x.station: x for x in runner.run()}["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        treasury = [(c.route, c.sent.get("duplicatesAcknowledged")) for c in runner.calls
                    if c.station == "S7" and c.route in ("POST /v1/sets/review", "POST /v1/sets") and isinstance(c.sent, dict)
                    and (c.sent.get("pays") or [{}])[0].get("invoiceRef") == "HT-%s" % runner.run_stamp]
        self.assertEqual(treasury, [("POST /v1/sets/review", False), ("POST /v1/sets/review", True), ("POST /v1/sets", True)])
        previous = earlier["instructions"][0]["id"]
        self.assertIn(H.REPEAT_CONFIRMED_NOTE % ("Harness Holdings Pty Ltd", "1.00 USDC", "HT-%s" % runner.run_stamp, earlier["createdAt"],
                                                 "not named: instruction %s is in no runs register this run read" % previous), runner.notes["S7"],
                      "the Treasury's register is not read by S7, and the note says so rather than guess a run")
        self.assertTrue(runner.facts["money"]["treasury"]["payment"]["landed"])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class PathfindersRoadIsUnchanged(unittest.TestCase):
    """`pay` without `confirm_repeats` — Pathfinder's S11 funding payment — reads no screen: one review, and the creation's refusal in the estate's words, as today."""

    def test_the_payment_road_without_the_confirmation_is_todays(self):
        double = EstateDouble(holdings_usdc_cents=500)  # funded, so the creation's first blocking refusal is the duplicate screen's, not the gas gate's
        tmp = tempfile.mkdtemp()
        runner_on(double, tmp, invite=double.mint_founder_link()).run()
        double.age_runs(4)
        runner = runner_on(double, tmp, start_at="S7")
        runner.load_passkeys()
        runner.resume()
        clerk = runner.clerk()
        row = {"oneOff": {"chain": T.PAYEE_CHAIN, "address": OWNER, "declared": True, "payeeName": "Unlisted destination"}, "asset": "USDC", "chain": T.PAYEE_CHAIN,
               "amountMinor": "10000", "invoiceRef": "HH-0002"}
        record = runner.pay(runner, clerk, "PX", row, 10000, OWNER, [], "a payment of the earlier run, without the confirmation", lambda: (None, "not read"), station="S11")
        self.assertEqual([(c.route, c.sent.get("duplicatesAcknowledged")) for c in runner.calls if c.station == "S11"],
                         [("POST /v1/sets/review", False), ("POST /v1/sets", False)])
        self.assertEqual(record["said"], "refused at creation — DUPLICATE_UNACKNOWLEDGED: %s" % SENTENCE)
        self.assertIsNone(record["repeats"])
        self.assertEqual(runner.findings, [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheQuestionMarkIsGone(unittest.TestCase):
    """(e) Where the estate created no run, S7's line says so — never "the estate asked ? signature(s)"."""

    def test_a_payment_refused_before_any_run_was_created_says_no_run_was_created(self):
        double = EstateDouble(funding_wallet="unavailable")  # no funding wallet: every review and creation is refused (routes/sets.ts requireSourceAccount)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        o = {x.station: x for x in runner.run()}["S7"]
        self.assertEqual(o.outcome, H.FAIL)
        self.assertNotIn("asked ? signature", o.line)
        self.assertNotIn("?", o.line)
        for key in ("P1", "P2", "P3"):
            self.assertIn("%s (" % key, o.line)
        self.assertEqual(o.line.count("refused at creation — WORKSPACE_NOT_PROVISIONED: "), 3)
        self.assertEqual(o.line.count("(no funding wallet); %s and " % H.NO_RUN_CREATED), 3, o.line)


class TheDryRunSaysTheBound(unittest.TestCase):
    """(d) Each review line of S7 gains its conditional second review, saying the bound; the creations say the acknowledgement is true only then."""

    def test_each_review_has_its_second_review_and_each_creation_its_condition(self):
        lines = [l for l in H.dry_lines() if l.startswith("S7 — ")]
        firsts = [i for i, l in enumerate(lines) if l.startswith("S7 — POST /v1/sets/review ") and '"duplicatesAcknowledged": false' in l]
        seconds = [i for i, l in enumerate(lines) if l.startswith("S7 — POST /v1/sets/review ") and '"duplicatesAcknowledged": true' in l]
        creations = [i for i, l in enumerate(lines) if l.startswith("S7 — POST /v1/sets {")]
        self.assertEqual((len(firsts), len(seconds), len(creations)), (5, 5, 4), "the Treasury's, S7a's and each payment's review, each with its second review; four creations")
        for i in seconds:
            self.assertIn("— %s →" % H.REPEAT_BOUND_WORDS, lines[i], "the bound, in the call part of the line, before the arrow")
            self.assertIn('passed, its evidence ending "acknowledged by the author"', lines[i])
            self.assertIn("(Spec T28)", lines[i])
        for i in creations:
            self.assertIn('"duplicatesAcknowledged": "<true only where the second review above was made, else false>"', lines[i])
            self.assertIn("duplicatesAcknowledged is true only where the duplicate screen named a payment of an earlier run and the second review saw its gate pass (Spec T28)", lines[i])
        for i in firsts:
            self.assertIn("the duplicate screen (duplicate_screen) read and each DUPLICATE_UNACKNOWLEDGED judged", lines[i])
        # each second review follows its first, before its creation (the Treasury's after its cure line; S7a's before the register read after it)
        pairs = list(zip(firsts, seconds))
        self.assertTrue(all(first < second for first, second in pairs), pairs)
        self.assertTrue(all(c > s for s, c in zip([seconds[0]] + seconds[2:], creations)), (seconds, creations))
        self.assertIn("S7a creates nothing", lines[seconds[1]])
        self.assertTrue(lines[seconds[1] + 1].startswith("S7 — GET /v1/sets (as Cora Clerk) → expect no new run since S7a's review"), lines[seconds[1] + 1])
        self.assertEqual(len(H.dry_lines()), 240, "Spec T27's 235 and the five second reviews")


if __name__ == "__main__":
    unittest.main()
