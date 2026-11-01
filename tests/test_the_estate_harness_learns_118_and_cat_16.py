"""
Spec T31 (1 November 2026, from the three estate runs of 31 October and 1 November on production): the estate harness learns AER 360 Spec
AER360-118 and Spec AER360-CAT-16, and never strands its estate.

  §1.1  S3 reads Spec AER360-118's 202 — the charter change that waits for its quorum — and finishes it by the estate's road as the people it
        names, against a double that counts approvals as the estate does (services/charterchanges.ts at a80ac13: needed = approvalsRequired, less one
        for the confirmer where the confirmer counts, less the approvals recorded): written on the count met, CHARTER_CHANGE_NOT_LISTED after. The
        count is a reading: S3's line and S10's note say how many approvals wrote the change and whether the confirmer is counted among them, and
        only a change written on fewer than the spec's count is S10's finding against the estate.
  §1.2  A change an earlier run left pending is finished before S3 begins its interview; one that cannot be finished stops S3 as FAILED — prerequisite.
  §1.3  The read-back book carries Spec AER360-CAT-16's lines, held against the read-back of 1 November (tests/fixtures/aer360-readback-2026-11-01.json).
  §1.4  S7's expectations are derived from the charter the harness answered — with a US$10 hold and with a US$0 hold.
  §1.5  A passkey counter the estate refuses as low, saying the figure it expects, is adopted once and not twice.

The sentences held here are the estate's own, copied from aeredium/AERAccounts at a80ac13 and from the brief's quotation of the report of 1 November,
never borrowed from the harness's book, so the book is not tested against itself.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import tests.test_aer360_double as D  # noqa: E402
from tests.test_aer360_double import EstateDouble, Refusal, runner_on  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "aer360-readback-2026-11-01.json")
# The brief's quotation of the report of 1 November 2026 (Spec T31 §0, item 3), word for word
C2_WRITTEN_ON_1_NOVEMBER = ("Recorded as your production figure: US$100 per payment. While your estate is in the sandbox, every signing entry this estate draws "
                            "up on its own account carries US$100 per payment instead; your figure is written to them when your estate goes live, with nothing "
                            "further from you.")
DERIVED_ON_1_NOVEMBER = "US$1,000 per day, so US$7,000 per week and US$31,000 per month. To change the weekly or monthly figure, change the daily figure."
# What the book expected before Spec T31 (Spec T27, b523cbf's ceilingWrittenSentence)
WRITTEN_C2 = ("Written to the signing platform as the per-payment limit of every signing entry this estate draws up on its own account: US$100. "
              "No single payment above it is approved, on any network.")


def fixture_lines():
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def book_answers(interview_type="policy"):
    """The answers as the harness records them, with no prompt, so the fixture's shorthand prompts are compared with nothing."""
    return [(q.id, A.ANSWERS[interview_type][q.id], "", q.kind) for q in A.expected_walk(interview_type)]


def ids_of(lines):
    return [str(l.get("questionId")) for l in lines]


class TheBookLearnsCat16(unittest.TestCase):
    """§1.3: the book's lines beside C2, C3 and O1, and the read-back of 1 November held to them."""

    def test_the_book_speaks_the_lines_of_1_november_in_their_order(self):
        c2 = A.lines_beside("policy", "C2", A.POLICY_ANSWERS["C2"], A.POLICY_ANSWERS["C3"], sandbox=True, amending=True)
        self.assertEqual(c2, [{"questionId": "C2_WRITTEN", "prompt": "What the company ceiling becomes", "spoken": C2_WRITTEN_ON_1_NOVEMBER}])
        c3 = A.lines_beside("policy", "C3", A.POLICY_ANSWERS["C3"], A.POLICY_ANSWERS["C2"], sandbox=True, amending=True)
        self.assertEqual([l["questionId"] for l in c3], ["SANDBOX_FIGURE", "DERIVED_WEEK_MONTH", "C3_WRITTEN"], "C3_WRITTEN three lines after C3")
        self.assertEqual(c3[0], {"questionId": "SANDBOX_FIGURE", "prompt": "What this figure does while your estate is in the sandbox",
                                 "spoken": "Recorded as your production figure. In the sandbox this is replaced by US$100."})
        self.assertEqual(c3[1]["spoken"], DERIVED_ON_1_NOVEMBER)
        self.assertTrue(c3[2]["spoken"].startswith("Recorded as your production figure: US$1,000 per day. While your estate is in the sandbox,"), c3[2]["spoken"])
        # C2's figure is the allowance itself, not above it, so no sandbox figure's line stands beside it (sandboxFigureRecorded: cents > allowance)
        self.assertNotIn("SANDBOX_FIGURE", [l["questionId"] for l in c2])
        # the wallet account's daily figure (O1, US$50) derives its week and month, and is within the allowance
        self.assertEqual(A.lines_beside("wallet_account", "O1", A.ACCOUNT_ANSWERS["O1"], sandbox=True), [
            {"questionId": "DERIVED_WEEK_MONTH", "prompt": "The weekly and monthly figures, derived from this one",
             "spoken": "US$50 per day, so US$350 per week and US$1,550 per month. To change the weekly or monthly figure, change the daily figure."}])
        self.assertEqual(A.lines_beside("wallet_account", "O2", A.ACCOUNT_ANSWERS["O2"], sandbox=True), [], "the per-payment hold, US$10, is within the allowance")
        self.assertEqual(A.lines_beside("wallet_account", "O1", {"cents": None}, sandbox=True)[0]["spoken"],
                         "No daily figure is written, so no weekly or monthly figure is derived from it. Write a daily figure and the weekly and monthly figures follow, "
                         "seven and thirty-one times it.")
        # on the live realm: no sandbox figure's line, and the ceiling's written form
        live = A.lines_beside("policy", "C3", A.POLICY_ANSWERS["C3"], A.POLICY_ANSWERS["C2"], sandbox=False)
        self.assertEqual([l["questionId"] for l in live], ["DERIVED_WEEK_MONTH", "C3_WRITTEN"])
        self.assertTrue(live[1]["spoken"].startswith("Written to the signing platform as the daily limit of the same entries: US$1,000."))

    def test_the_read_back_of_1_november_raises_none_of_the_three_findings(self):
        read = fixture_lines()
        lines = read["lines"]
        ids = ids_of(lines)
        self.assertEqual(ids[ids.index("C2"):ids.index("C3") + 4], ["C2", "C2_WRITTEN", "C3", "SANDBOX_FIGURE", "DERIVED_WEEK_MONTH", "C3_WRITTEN"])
        for amending in (True, False, None):  # in the sandbox the form does not depend on what stood before
            self.assertEqual(H.audit_readback("policy", book_answers(), lines, amending, realm=read["realm"]), [], amending)
        self.assertEqual(H.audit_readback("policy", book_answers(), lines, True), [], "the realm read off the read-back's own first line where none was recorded")

    def test_the_book_of_before_is_gone_and_a_line_the_estate_speaks_otherwise_is_still_a_finding(self):
        read = fixture_lines()
        old = [dict(l, spoken=WRITTEN_C2) if l["questionId"] == "C2_WRITTEN" else l for l in read["lines"]]
        found = H.audit_readback("policy", book_answers(), old, True, realm="sandbox")
        self.assertEqual([(f["probe"], f["said"]) for f in found], [("read-back (policy) of C2: what the company ceiling becomes", "the read-back's C2_WRITTEN line says %r" % WRITTEN_C2)])
        # the two lines CAT-16 put between C3 and C3_WRITTEN are the book's now: without them, each is missing and C3_WRITTEN stands in the wrong place
        without = [l for l in read["lines"] if l["questionId"] not in ("SANDBOX_FIGURE", "DERIVED_WEEK_MONTH")]
        probes = [f["probe"] for f in H.audit_readback("policy", book_answers(), without, True, realm="sandbox")]
        self.assertEqual(probes, ["read-back (policy) of C3: what this figure does while your estate is in the sandbox",
                                  "read-back (policy) of C3: the weekly and monthly figures, derived from this one",
                                  "read-back (policy) of C3: what the daily total becomes (where it stands)"])
        # a synthetic line the book carries, moved, is found where it stands
        moved = [l for l in read["lines"] if l["questionId"] != "DERIVED_WEEK_MONTH"] + [next(l for l in read["lines"] if l["questionId"] == "DERIVED_WEEK_MONTH")]
        probes = [f["probe"] for f in H.audit_readback("policy", book_answers(), moved, True, realm="sandbox")]
        self.assertIn("read-back (policy) of C3: the weekly and monthly figures, derived from this one (where it stands)", probes)
        # an answer's line the book does not know remains a finding, as before
        extra = read["lines"] + [{"questionId": "C4W", "prompt": "…", "spoken": "US$7,000 and 00 cents."}]
        self.assertEqual([f["probe"] for f in H.audit_readback("policy", book_answers(), extra, True, realm="sandbox")], ["read-back (policy) of C4W"])

    def test_the_sentences_are_the_estates(self):
        self.assertEqual(A.SANDBOX_ALLOWANCE_USD_CENTS, 10000, "realm.ts SANDBOX_PAYMENT_CEILING_USD_CENTS: ruling four, US$100")
        self.assertEqual((A.usd_cents_said(10000), A.usd_cents_said(3100000), A.usd_cents_said(155), A.usd_cents_said(0)), ("US$100", "US$31,000", "US$1.55", "US$0"))
        self.assertEqual(A.dollars_ceiling_of("10001"), 101, "rounded up, never below the figure")
        self.assertEqual(A.STANDING_CEILING_KEPT, "Where such a limit already stands above zero, this write leaves it as it stands: changing a limit that stands is a change "
                                                  "of the company’s rules, which your change quorum (C12) must agree to, and this write carries no such agreement.")
        self.assertEqual(H.CEILING_READBACK_LINES, A.CEILING_READBACK_LINES, "the harness reads the book's names")


class TheChangeThatWaitsIsParsed(unittest.TestCase):
    """§1.1: the 202 of Spec AER360-118 read as what it is, and the 202 of Spec 109 as what it is."""

    def answer(self, status, body):
        return H.Answer("POST", "/v1/onboarding/interviews/iv-1/compile", status, {}, json.dumps(body), 5)

    def test_the_two_shapes_of_a_202(self):
        change = {"id": "4f1c2e9a-0000-4000-8000-000000000001", "state": "pending", "confirmedBy": "Harriet Founder", "confirmedAt": "2026-11-01T02:13:00.000Z",
                  "approvalsRequired": 2, "approvedBy": [], "title": "Charter change, confirmed by Harriet Founder", "now": [], "carried": 0, "carriedLines": [],
                  "confirmerCounts": True}
        body = {"state": "awaiting_change_approvals", "interviewId": "iv-1", "change": change}
        self.assertEqual(H.Runner.charter_change_that_waits(self.answer(202, body)), body)
        self.assertIsNone(H.Runner.write_that_waits(self.answer(202, body)), "not Spec 109's write that waits")
        self.assertIsNone(H.Runner.charter_change_that_waits(self.answer(200, body)), "the status is asserted, not only the body")
        self.assertIsNone(H.Runner.charter_change_that_waits(self.answer(202, dict(body, change=None))), "a change, or nothing")
        spec_109 = {"state": "awaiting_approvals", "interviewId": "iv-1", "ceremonies": []}
        self.assertIsNone(H.Runner.charter_change_that_waits(self.answer(202, spec_109)))
        self.assertEqual(H.Runner.write_that_waits(self.answer(202, spec_109)), spec_109)
        self.assertEqual(H.Runner.charter_change_words(change), "the charter change 4f1c2e9a… pending, approvalsRequired 2, approvedBy [], confirmed by Harriet Founder at "
                                                               "2026-11-01T02:13:00.000Z; the confirmer counts")

    def test_the_count_is_a_reading_beside_what_the_spec_intends(self):
        record = {"written": True, "approvalsRequired": 2, "approvals_that_wrote": 1, "confirmerCounts": True, "approvedBy_final": ["Ada Approver"], "confirmedBy": "Harriet Founder"}
        H.Runner.read_the_count(record)
        self.assertEqual((record["spec_count"], record["confirmer_counted"], record["fewer_than_the_spec"]), (1, True, False), "1 November: one approval wrote it, as the spec intends")
        self.assertIn("approvalsRequired 2; the change was written on 1 approval(s) (Ada Approver); the confirmer (Harriet Founder) is counted among them", record["count_words"])
        self.assertIn(H.SPEC_118_COUNTS_THE_CONFIRMER, record["count_words"])
        self.assertTrue(record["count_words"].endswith("the estate wrote it on that count, as the spec intends"), record["count_words"])
        fewer = dict(record, confirmerCounts=False)
        H.Runner.read_the_count(fewer)
        self.assertEqual((fewer["spec_count"], fewer["fewer_than_the_spec"]), (2, True), "where the confirmer does not count, one approval is fewer than the spec's two")
        unsaid = dict(record, confirmerCounts=None)
        H.Runner.read_the_count(unsaid)
        self.assertIn("by the book's C15 (the change does not say)", unsaid["count_words"])
        self.assertFalse(unsaid["fewer_than_the_spec"], "the book answers C15 Yes, so the confirmer counts")


class TheExpectationIsTheCharters(unittest.TestCase):
    """§1.4: S7's expectations derived from the charter the harness answered — a US$10 hold, then a US$0 hold — and the sandbox allowance."""

    def expect(self, amounts, hold, daily=5000, one_off_at=None, paid_before=True, allowance=10000):
        out, day = [], 0
        for index, cents in enumerate(amounts):
            out.append(H.expectation_of_the_charter(cents, day, hold, daily, index == one_off_at, paid_before, H.HOLDS_NEW_DESTINATIONS, allowance))
            day += cents
        return out

    def test_a_us_10_hold_lets_the_one_dollar_book_proceed(self):
        found = self.expect([50, 1, 49], 1000, one_off_at=1, paid_before=True)
        self.assertEqual([e["waits"] for e in found], [False, False, False], "P1 and P3 proceeded and landed on 1 November, as this charter expects")
        self.assertEqual(found[0]["word"], "proceed: under the per-payment hold of US$10.00 and within the day's US$50.00")
        self.assertEqual(found[1]["word"], "proceed: under the per-payment hold of US$10.00 and within the day's US$50.00; a declared one-off to a destination this estate "
                                           "has paid before, which Spec 69 does not hold")
        new = self.expect([50, 1, 49], 1000, one_off_at=1, paid_before=False)
        self.assertEqual((new[1]["waits"], new[1]["word"]), (True, "wait for the approver: a declared one-off to a destination this estate has never paid (Spec 69)"))
        self.assertEqual(self.expect([50, 1, 49], 1000, one_off_at=1, paid_before=None)[1]["word"], "wait for the approver where the destination is new to this estate (Spec 69)")
        above = self.expect([1000, 1200], 1000, daily=None)
        self.assertEqual([e["word"] for e in above], ["wait for the approver: at or above the per-payment hold of US$10.00"] * 2, "at the hold or above it waits")
        day = self.expect([900, 900, 900, 900, 900, 900], 1000)
        self.assertEqual([e["waits"] for e in day], [False, False, False, False, False, True])
        self.assertEqual(day[-1]["word"], "wait for the approver: it takes the day past its US$50.00")

    def test_a_us_0_hold_holds_every_payment(self):
        found = self.expect([50, 1, 49], 0, one_off_at=1, paid_before=True)
        self.assertEqual([e["waits"] for e in found], [True, True, True])
        self.assertEqual({e["word"] for e in found}, {"wait for the approver: at or above the per-payment hold of US$0.00"})

    def test_the_sandbox_allowance_refuses_at_the_review_first(self):
        self.assertEqual(H.expectation_of_the_charter(10001, 0, 1000, 5000, False, None, H.HOLDS_NEW_DESTINATIONS, 10000, "the sandbox allows for one payment"),
                         {"word": "be refused at its review: it is worth more than the US$100.00 the sandbox allows for one payment", "waits": None})

    def test_the_terms_are_read_from_the_charter_s5_compiled_else_from_the_book(self):
        runner = H.Runner("https://estate.test", tempfile.mkdtemp(), None, False, None, tempfile.mkdtemp(), transport=lambda r: (500, [], ""), say=lambda s: None)
        runner.facts["workspace"] = {"realm": "sandbox"}
        book = runner.charter_terms()
        self.assertEqual((book["hold"], book["daily"], book["mode"], book["allowance"]), (1000, 5000, H.HOLDS_NEW_DESTINATIONS, 10000))
        self.assertIn("no account charter compiled in this run", book["from"])
        runner.facts["charter"]["wallet_account"] = {"amountsUsdCents": {"holdOverPerTx": "0", "dailyTotal": "5000"}, "whitelistMode": "hold_non_listed"}
        runner.facts["solana"]["allowance"] = {"leftUsdCents": "9900"}
        zero = runner.charter_terms()
        self.assertEqual((zero["hold"], zero["daily"], zero["allowance"], zero["from"]), (0, 5000, 9900, "the charter the harness answered in S5"))


class AStore:
    """A software passkey's counter and its save, as the runner touches them (Spec T31 §1.5) — nothing else of the passkey is read here."""

    def __init__(self, sign_count):
        self.sign_count = sign_count
        self.base = None
        self.display_name = None
        self.created_at = None
        self.saved = []

    def save(self, path):
        self.saved.append((path, self.sign_count))


class TheCounterIsTold(unittest.TestCase):
    """§1.5: adopted once and not twice, never lowered, a note in the station and a reading in S10."""

    def setUp(self):
        self.runner = H.Runner("https://estate.test", tempfile.mkdtemp(), None, False, None, tempfile.mkdtemp(), transport=lambda r: (500, [], ""), say=lambda s: None)
        self.person = self.runner.people["ada"]
        self.person.passkey = AStore(25)

    @staticmethod
    def refused(held, expected):
        body = {"error": {"code": "STEP_UP_INVALID", "message": "That passkey confirmation could not be verified.",
                          "detail": {"cause": "Response counter value %d was lower than expected %d" % (held, expected)}}}
        return H.Answer("POST", "/v1/charter-changes/c/approve", 403, {}, json.dumps(body), 3)

    @staticmethod
    def counted():
        return H.Answer("POST", "/v1/charter-changes/c/approve", 200, {}, json.dumps({"state": "written"}), 3)

    def test_the_counter_is_adopted_once_and_the_press_made_again(self):
        answers = [self.refused(25, 30), self.counted()]
        presses = []

        def press():
            presses.append(self.person.passkey.sign_count)
            return answers[len(presses) - 1]

        out = self.runner.press_once_more_on_the_counter("S3", self.person, press)
        self.assertEqual(out.status, 200)
        self.assertEqual(presses, [25, 30], "the second press made with the counter the estate expects")
        self.assertEqual(self.person.passkey.saved[-1][1], 30, "saved at once")
        self.assertIn("the estate expected counter 30 for Ada Approver and the store held 25; adopted 30", self.runner.notes["S3"])
        self.assertEqual(self.runner.facts["counters_adopted"], [{"station": "S3", "who": "Ada Approver", "held": 25, "expected": 30, "adopted": 30}])
        self.assertEqual(self.runner.findings, [], "a reading of the harness's own store, never a finding against the estate")

    def test_a_second_refusal_of_the_same_shape_is_not_pressed_a_third_time(self):
        presses = []

        def press():
            presses.append(1)
            return self.refused(30 + len(presses), 40 + len(presses))

        out = self.runner.press_once_more_on_the_counter("S5", self.person, press)
        self.assertEqual(len(presses), 2, "once more, once")
        self.assertEqual(out.refusal["code"], "STEP_UP_INVALID", "the second refusal is returned as the estate said it")
        self.assertEqual(len(self.runner.facts["counters_adopted"]), 1)
        self.assertTrue(any("the press is not made a third time" in n for n in self.runner.notes["S5"]))

    def test_the_counter_is_never_lowered_and_anything_else_is_left_alone(self):
        self.person.passkey = AStore(156)
        answers = [self.refused(149, 149), self.counted()]
        out = self.runner.press_once_more_on_the_counter("S5", self.person, lambda: answers.pop(0))
        self.assertEqual((out.status, self.person.passkey.sign_count), (200, 156), "1 November: the store at 156 stays at 156")
        other = H.Answer("POST", "/x", 403, {}, json.dumps({"error": {"code": "STEP_UP_INVALID", "message": "That passkey confirmation could not be verified.",
                                                                      "detail": {"cause": "the asserting passkey is not the approving credential"}}}), 3)
        calls = []
        self.assertIs(self.runner.press_once_more_on_the_counter("S5", self.person, lambda: calls.append(1) or other), other)
        self.assertEqual(len(calls), 1, "a refusal of another cause is not pressed again")


# -- against the double -----------------------------------------------------------------------------------------------------------------------
def run(double, tmp, invite=True):
    runner = runner_on(double, tmp, invite=double.mint_founder_link() if invite else None)
    return runner, {o.station: o for o in runner.run()}


def leave_a_change_pending(double, tmp):
    """An earlier run that compiled an amendment and stopped before anyone approved it: the founder signs in, walks, confirms and compiles."""
    runner = runner_on(double, tmp)
    runner.load_passkeys()
    runner.station_s1()
    founder = runner.people[A.FOUNDER]
    interview_id, page, _ = runner.walk_interview("S3", "policy", founder)
    waiting = runner.confirm_and_compile("S3", "policy", interview_id, founder, page)
    assert waiting.get("state") == H.INTERVIEW_AWAITING_CHANGE_APPROVALS, waiting
    return waiting


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AChangeWaitsForItsQuorum(unittest.TestCase):
    """§1.1: the second run amends the written charter; C12 asks two, the confirmer counts (C15 Yes), so the first approval recorded writes it."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(currency_spoken_as_code=True, change_quorum=True)
        cls.tmp = tempfile.mkdtemp()
        cls.first, cls.first_outcomes = run(cls.double, cls.tmp)
        cls.runner, cls.outcomes = run(cls.double, cls.tmp, invite=False)

    def test_the_first_run_writes_its_charter_at_the_compile(self):
        self.assertEqual(self.first_outcomes["S3"].outcome, H.PASS, self.first_outcomes["S3"].line)
        self.assertNotIn("charter change", self.first_outcomes["S3"].line, "no charter stood written, so nothing waits")

    def test_s3_finishes_the_change_as_the_people_it_names(self):
        o = self.outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("the compile answered 202 — the charter change waits for its quorum (Spec AER360-118)", o.line)
        self.assertIn("Ben Signatory approved and the change was written on that approval", o.line)
        self.assertIn("the count read: approvalsRequired 2; the change was written on 1 approval(s) (Ben Signatory); the confirmer (Harriet Founder) is counted among them, "
                      "by the change's confirmerCounts", o.line)
        change = self.double.charter_changes[-1]
        self.assertEqual((change["state"], [a["email"] for a in change["approvals"]]), ("written", [A.PEOPLE["ben"].email]))
        self.assertEqual(self.double.interviews[change["interviewId"]]["state"], "written")
        presses = [c.route for c in self.runner.calls if c.station == "S3" and "/approve" in c.route]
        self.assertEqual(presses, ["POST /v1/charter-changes/%s/approve/options" % change["id"], "POST /v1/charter-changes/%s/approve" % change["id"]], "once, never retried")
        record = self.runner.facts["charter_changes"][-1]
        self.assertEqual((record["written"], record["written_by"], record["approvals_that_wrote"], record["confirmer_counted"]), (True, "Ben Signatory", 1, True))

    def test_s10_reads_the_count_and_finds_nothing_against_the_estate(self):
        self.assertFalse(any("the count that wrote it" in f.probe for f in self.runner.findings))
        self.assertTrue(any(n.startswith("charter change ") and "as the spec intends" in n for n in self.runner.notes["S10"]), self.runner.notes["S10"])

    def test_an_approval_after_the_write_is_refused_charter_change_not_listed(self):
        change = self.double.charter_changes[-1]
        cora = self.runner.people["cora"]
        self.assertTrue(self.runner.session_for(cora, "test"))
        answer, body = self.runner.approve_charter_change_as("test", cora, change["id"], {"approvalsRequired": 2, "approvedBy": ["Ben Signatory"]})
        self.assertIsNone(body)
        self.assertEqual((answer.status, answer.refusal["code"], answer.refusal["detail"]["state"]), (404, "CHARTER_CHANGE_NOT_LISTED", "written"))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AChangeWhoseConfirmerDoesNotCount(unittest.TestCase):
    """§1.1: where the confirmer's agreement does not count, two approvals write the change, and the first leaves it pending one longer."""

    def test_two_approvals_write_it_and_the_count_says_the_confirmer_is_not_counted(self):
        double = EstateDouble(currency_spoken_as_code=True, change_quorum=True, confirmer_counts=False)
        tmp = tempfile.mkdtemp()
        run(double, tmp)
        runner, outcomes = run(double, tmp, invite=False)
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("Ben Signatory approved (approvedBy 1 of approvalsRequired 2)", o.line)
        self.assertIn("Cora Clerk approved and the change was written on that approval", o.line)
        self.assertIn("written on 2 approval(s) (Ben Signatory, Cora Clerk); the confirmer (Harriet Founder) is not counted among them", o.line)
        self.assertEqual(runner.facts["charter_changes"][-1]["problems"], [])


class AnEstateThatWritesOnOne(EstateDouble):
    """An estate that writes a change on its first approval although the confirmer does not count — fewer than the spec's count."""

    def change_facts(self, change):
        facts = super().change_facts(change)
        if facts["approvedBy"]:
            facts["needed"] = 0
        return facts


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AChangeWrittenOnFewer(unittest.TestCase):
    """§1.1: a change written on fewer approvals than the spec's count is S10's finding against the estate, in the spec's words."""

    def test_the_finding_names_the_count(self):
        double = AnEstateThatWritesOnOne(currency_spoken_as_code=True, change_quorum=True, confirmer_counts=False)
        tmp = tempfile.mkdtemp()
        run(double, tmp)
        runner, outcomes = run(double, tmp, invite=False)
        found = [f for f in runner.findings if f.station == "S10" and "the count that wrote it" in f.probe]
        self.assertEqual(len(found), 1, [f.probe for f in runner.findings])
        self.assertEqual(found[0].said, "the estate wrote the change on 1 approval(s) (Ben Signatory), fewer than the spec's count")
        self.assertIn(H.SPEC_118_COUNTS_THE_CONFIRMER, found[0].expected)
        self.assertEqual(outcomes["S10"].outcome, H.FAIL)


class AnInboxThatRefusesEveryone(EstateDouble):
    """An estate whose inbox refuses every approval in the roster's words — a change that cannot be finished here."""

    refusing = False

    def approve_charter_change(self, headers, change_id, body):
        if self.refusing:
            self.admit_change_press(headers, change_id)
            raise Refusal("ROLE_NOT_GRANTED", D.change_approved_by_sentence(["Somebody Else"]), {"changeId": change_id, "required": "approver"})
        return super().approve_charter_change(headers, change_id, body)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AChangeLeftByAnEarlierRun(unittest.TestCase):
    """§1.2: a change an earlier run left pending is finished before S3 begins its interview — or S3 stops at the missing prerequisite, naming it."""

    def test_the_change_in_flight_is_finished_first_and_s3_walks_on(self):
        double = EstateDouble(currency_spoken_as_code=True, change_quorum=True)
        tmp = tempfile.mkdtemp()
        run(double, tmp)
        left = leave_a_change_pending(double, tmp)
        self.assertEqual(double.pending_change()["id"], left["change"]["id"])
        runner, outcomes = run(double, tmp, invite=False)
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertTrue(o.line.startswith("policy interview: a charter change from an earlier run stood pending and was finished first: "), o.line)
        self.assertEqual([c["state"] for c in double.charter_changes], ["written", "written"], "the earlier run's change, then this run's own")
        self.assertFalse(any("/withdraw" in c.route for c in runner.calls), "finished, never withdrawn")
        self.assertFalse(any('"CHARTER_CHANGE_WAITING"' in c.text for c in runner.calls if c.station == "S3"), "the interview was begun after the change was written")
        self.assertEqual(runner.facts["charter_changes"][0]["opened_this_run"], False)
        self.assertEqual(runner.facts["charter_changes"][0]["written_by"], "Ben Signatory")

    def test_a_change_that_cannot_be_finished_stops_s3_naming_it(self):
        double = AnInboxThatRefusesEveryone(currency_spoken_as_code=True, change_quorum=True)
        tmp = tempfile.mkdtemp()
        run(double, tmp)
        left = leave_a_change_pending(double, tmp)
        double.refusing = True
        runner, outcomes = run(double, tmp, invite=False)
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)
        self.assertTrue(o.line.startswith("policy interview: %s — the charter change %s…" % (H.CHARTER_CHANGE_PREREQUISITE, left["change"]["id"][:8])), o.line)
        self.assertIn("refused, and the refusal says why (Rule 13): ROLE_NOT_GRANTED", o.line)
        self.assertEqual(double.pending_change()["id"], left["change"]["id"], "the change stands as it was: nothing withdrawn")
        self.assertFalse(any(c.route == "POST /v1/onboarding/interviews" for c in runner.calls if c.station == "S3"), "no interview begun while a change stands pending")


class AnEstateWhoseCounterRan(EstateDouble):
    """An estate whose record of the founder's passkey counter runs ahead of the store — another device signed — before each confirm (`ahead_times` of them)."""

    ahead_times = 1

    def onboarding_interview(self, method, interview_id, rest, headers, body):
        if rest == "/confirm/options" and method == "POST" and self.ahead_times > 0:
            self.ahead_times -= 1
            session = self.require_session(headers)
            for row in self.passkeys.values():
                if row["credentialId"] == session["credentialId"]:
                    row["signCount"] += 5
        return super().onboarding_interview(method, interview_id, rest, headers, body)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheCounterIsToldByTheEstate(unittest.TestCase):
    """§1.5 against the double: the confirm refused for the counter, the figure adopted, the confirm made once more and S3 passes; twice, and S3 stops."""

    def test_adopted_once(self):
        double = AnEstateWhoseCounterRan(currency_spoken_as_code=True)
        runner, outcomes = run(double, tempfile.mkdtemp())
        self.assertEqual(outcomes["S3"].outcome, H.PASS, outcomes["S3"].line)
        self.assertEqual(len([c for c in runner.calls if c.station == "S3" and c.route.endswith("/confirm")]), 2)
        told = runner.facts["counters_adopted"]
        self.assertEqual([(t["station"], t["who"]) for t in told], [("S3", "Harriet Founder")])
        self.assertEqual(told[0]["adopted"], told[0]["expected"])
        self.assertIn("the estate expected counter %d for Harriet Founder and the store held %d; adopted %d" % (told[0]["expected"], told[0]["held"], told[0]["adopted"]),
                      runner.notes["S3"])
        self.assertTrue(any(n.startswith("a reading, not a finding: at S3 the estate expected counter") for n in runner.notes["S10"]))
        self.assertFalse(any("counter" in f.said for f in runner.findings))

    def test_not_twice(self):
        double = AnEstateWhoseCounterRan(currency_spoken_as_code=True)
        double.ahead_times = 2
        runner, outcomes = run(double, tempfile.mkdtemp())
        self.assertEqual(outcomes["S3"].outcome, H.FAIL, outcomes["S3"].line)
        self.assertIn("STEP_UP_INVALID", outcomes["S3"].line)
        self.assertEqual(len([c for c in runner.calls if c.station == "S3" and c.route.endswith("/confirm")]), 2, "the one press made again once, never a third time")
        # once for S3's press; a later station's own press (S5's confirm, the store still behind the estate's record) is a press of its own, told once in its turn
        self.assertEqual(len([t for t in runner.facts["counters_adopted"] if t["station"] == "S3"]), 1)
        self.assertTrue(any("the press is not made a third time" in n for n in runner.notes["S3"]))


if __name__ == "__main__":
    unittest.main()
