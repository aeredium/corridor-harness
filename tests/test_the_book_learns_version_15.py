"""
Spec T27 (8 October 2026, from the owner's ruling of that day: "This needs to be done now. You want the estate to know the answer to those
questions."): the answer book learns catalog version 15 — the company ceiling (C2) and the daily total (C3).

AER 360 Spec AER360-115 (aeredium/AERAccounts PR #137, merge commit b523cbf) asked the two again, after C9 and before C10, both money, both
required, refused at the page when blank or zero, and the charter does not compile without both. The book answers them US$100.00 and
US$1,000.00, the figures every signing entry of the harness estates already carries. The double is the estate at version 15
(tests/test_aer360_double.py), speaking a currency as its code as the estate has since Spec 88 (`currency_spoken_as_code=True`), so S10's verdict
is the ceilings' alone; `catalog_version=14` is the estate before it. Each test here was red on main, where the book answered version 14 and its
S3 stopped at C2.

The sentences below are the estate's own, copied from its code at b523cbf and held here as literals, so neither the harness's re-statement
(aer360_harness.ceiling_read_back_sentence) nor the double's (tests/test_aer360_double.ceiling_read_back_sentence) is tested against itself:
services/charterceilings.ts (ceilingWrittenSentence, STANDING_CEILING_KEPT, ceilingReadBackSentence) and packages/shared/src/explain.ts
(CHARTER_CEILINGS_REQUIRED, CEILING_ZERO_REFUSED, CHARTER_CEILINGS_REFUSED_AT_COMPILE).
"""
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
import tests.test_aer360_double as D  # noqa: E402
from tests.test_aer360_double import EstateDouble, Refusal, runner_on  # noqa: E402

WRITTEN_C2 = ("Written to the signing platform as the per-payment limit of every signing entry this estate draws up on its own account: US$100. "
              "No single payment above it is approved, on any network.")
WRITTEN_C3 = "Written to the signing platform as the daily limit of the same entries: US$1,000. No payment that takes a day’s total above it is approved."
KEPT = ("Where such a limit already stands above zero, this write leaves it as it stands: changing a limit that stands is a change of the company’s "
        "rules, which your change quorum (C12) must agree to, and this estate has no road for that change yet.")
ROUNDED = " That is your figure rounded up to the next whole dollar, because the platform holds whole dollars, so the ceiling is never smaller than yours."
NOT_WRITTEN_BESIDE_C3 = ("Not written to the signing platform while the daily total (C3) is not answered above zero: the platform refuses every payment "
                         "while either limit of a signing entry stands at zero, so this estate writes the two together or not at all.")
NOT_WRITTEN_BESIDE_C2 = NOT_WRITTEN_BESIDE_C3.replace("the daily total (C3)", "the company ceiling (C2)")
REQUIRED = ("The company ceiling (C2) and the daily total (C3) must each be a figure above zero: the signing platform refuses every payment on an "
            "account whose ceilings are not set.")
ZERO_REFUSED = "This estate does not accept a zero here. %s Write the figure itself." % REQUIRED
REFUSED_AT_COMPILE = ("This estate refused to compile the charter before the signing platform could refuse its payments. %s Answer both, each with a "
                      "figure above zero." % REQUIRED)
VERSION_14_CLAUSE = "; this Policy Interview asks neither C2 nor C3, which catalog version 15 added, so it stands at catalog version 14 and the book answered it as before"


def run(double, tmp, start_at=None, said=None):
    runner = runner_on(double, tmp, invite=double.mint_founder_link() if start_at is None else None, start_at=start_at, said=said)
    return runner, {o.station: o for o in runner.run()}


def lines_of(runner):
    return list((runner.facts["readback"].get("policy") or {}).get("lines") or [])


def line(lines, qid):
    return next((l for l in lines if l.get("questionId") == qid), None)


def ceiling_findings(runner):
    return [f for f in runner.findings if f.station == "S10" and ("C2" in f.probe or "C3" in f.probe or "ceiling" in f.probe)]


class TheReadBackSentenceIsTheEstates(unittest.TestCase):
    """ceilingReadBackSentence, word for word, in the harness's re-statement and in the double's, held to the estate's literals."""

    def test_both_restatements_speak_the_estates_sentence_in_both_forms_and_beside_a_partner_not_answered(self):
        for say in (H.ceiling_read_back_sentence, D.ceiling_read_back_sentence):
            self.assertEqual(say("perPayment", "10000", "100000", False), WRITTEN_C2, say.__module__)
            self.assertEqual(say("perDay", "100000", "10000", False), WRITTEN_C3, say.__module__)
            self.assertEqual(say("perPayment", "10000", "100000", True), WRITTEN_C2 + " " + KEPT, say.__module__)
            self.assertEqual(say("perDay", "100000", "10000", True), WRITTEN_C3 + " " + KEPT, say.__module__)
            # whole dollars, rounded UP from the cents, grouped as en-US groups them, and the rounding said
            self.assertEqual(say("perPayment", "10001", "100000", False), WRITTEN_C2.replace("US$100.", "US$101." + ROUNDED), say.__module__)
            self.assertEqual(say("perDay", "123456789", "1", False), WRITTEN_C3.replace("US$1,000.", "US$1,234,568." + ROUNDED), say.__module__)
            # BOTH OR NEITHER: beside a partner not answered above zero, nothing is written, and the read-back says why — kept or not
            self.assertEqual(say("perPayment", "10000", None, False), NOT_WRITTEN_BESIDE_C3, say.__module__)
            self.assertEqual(say("perDay", "100000", "0", True), NOT_WRITTEN_BESIDE_C2, say.__module__)
        self.assertEqual(H.STANDING_CEILING_KEPT, KEPT)
        self.assertEqual((H.CEILING_READBACK_LINES["perPayment"], H.CEILING_READBACK_LINES["perDay"]),
                         (("C2_WRITTEN", "What the company ceiling becomes"), ("C3_WRITTEN", "What the daily total becomes")))
        self.assertEqual((D.CHARTER_CEILINGS_REQUIRED, D.CEILING_ZERO_REFUSED, D.CHARTER_CEILINGS_REFUSED_AT_COMPILE), (REQUIRED, ZERO_REFUSED, REFUSED_AT_COMPILE))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AFreshEstateAtVersion15(unittest.TestCase):
    """A fresh estate at catalog version 15: S3 walks 25 pages, the read-back says the two ceilings are written, S10 finds nothing."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(currency_spoken_as_code=True)
        cls.runner, cls.outcomes = run(cls.double, tempfile.mkdtemp())

    def test_the_double_is_the_estate_at_version_15(self):
        self.assertEqual(self.double.catalog_version, 15)
        policy = [iv for iv in self.double.interviews.values() if iv["interviewType"] == "policy"]
        self.assertEqual({iv["catalogVersion"] for iv in policy}, {15}, "S3's interview and S11's probe draft alike")
        self.assertEqual(self.double.interviews[self.runner.facts["interview"]["policy"]]["catalogVersion"], 15)

    def test_s3_answers_c2_and_c3_from_the_book_and_states_version_15(self):
        o = self.outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("policy interview: 25 questions answered", o.line)
        self.assertIn("; the answer book answers catalog version 15, and the estate served 25 question(s), every one known to the book (%s)" % H.ESTATE_STATES_NO_CATALOG_VERSION, o.line)
        self.assertNotIn("asks neither", o.line, "the book's version and the interview's agree, so the sentence names one")
        given = {q: (value, prompt, kind) for q, value, prompt, kind in self.runner.facts["answers"]["policy"]}
        self.assertEqual(given["C2"], ({"cents": "10000"}, "Is there an amount so large that no one in this company should ever make a payment of it — no approval, no exception?", "money"))
        self.assertEqual(given["C3"], ({"cents": "100000"}, "How much is the maximum total of payments that can be made daily?", "money"))
        order = [q for q, _, _, _ in self.runner.facts["answers"]["policy"]]
        self.assertEqual(order[order.index("C9"):order.index("C10") + 1], ["C9", "C2", "C3", "C10"])
        self.assertEqual(self.runner.facts["interview_began"]["policy"], "in_progress")

    def test_the_read_back_says_each_ceiling_is_written_directly_after_it(self):
        lines = lines_of(self.runner)
        ids = [l["questionId"] for l in lines]
        self.assertEqual(ids[ids.index("C2"):ids.index("C3") + 2], ["C2", "C2_WRITTEN", "C3", "C3_WRITTEN"])
        self.assertEqual(line(lines, "C2")["spoken"], "US$100 and 00 cents.")
        self.assertEqual(line(lines, "C3")["spoken"], "US$1,000 and 00 cents.")
        self.assertEqual(line(lines, "C2_WRITTEN"), {"questionId": "C2_WRITTEN", "prompt": "What the company ceiling becomes", "spoken": WRITTEN_C2, "synthetic": True})
        self.assertEqual(line(lines, "C3_WRITTEN"), {"questionId": "C3_WRITTEN", "prompt": "What the daily total becomes", "spoken": WRITTEN_C3, "synthetic": True})

    def test_s10_reads_the_two_lines_back_on_a_fresh_estate_and_finds_nothing(self):
        self.assertIs(self.runner.earlier_policy_stood_written(), False, "S2 read the journey at stage 1, policy_interview not done")
        o = self.outcomes["S10"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(ceiling_findings(self.runner), [])
        self.assertFalse(any("form was not judged" in n for n in self.runner.notes["S10"]))
        self.assertEqual(H.audit_readback("policy", self.runner.facts["answers"]["policy"], lines_of(self.runner), False), [])

    def test_the_charter_carries_the_two_figures_and_s10_compares_them(self):
        charter = self.runner.facts["charter"]["policy"]
        self.assertEqual({k: charter["amountsUsdCents"][k] for k in ("denyCeiling", "dailyTotal")}, {"denyCeiling": "10000", "dailyTotal": "100000"})
        answers = {q: v for q, v, _, _ in self.runner.facts["answers"]["policy"]}
        self.assertEqual(H.audit_charter("policy", charter, answers), [])
        drifted = dict(charter, amountsUsdCents=dict(charter["amountsUsdCents"], dailyTotal="5000"))
        found = H.audit_charter("policy", drifted, answers)
        self.assertEqual([(f["probe"], f["expected"], f["said"]) for f in found], [
            ("charter (policy): the company ceiling (C2) and the daily total (C3), in cents", '{"denyCeiling": "10000", "dailyTotal": "100000"}',
             'the charter carries {"denyCeiling": "10000", "dailyTotal": "5000"}')])

    def test_nothing_else_moves_the_payments_are_the_one_dollar_book(self):
        self.assertEqual(self.outcomes["S7"].outcome, H.PASS, self.outcomes["S7"].line)
        self.assertEqual(sum(s["amount_minor"] for s in self.runner.facts["sets"].values()), T.ONE_DOLLAR_MINOR)


class AnEstateThatForgetsItsWrittenCharter(EstateDouble):
    """An estate whose read-back says the ceilings are written even where an earlier Policy Interview stands written — the kept clause dropped."""

    def __init__(self, **kwargs):
        super().__init__(currency_spoken_as_code=True, **kwargs)

    def readback(self, iv, check_standing=True):
        return [dict(l, spoken=l["spoken"].replace(" " + D.STANDING_CEILING_KEPT, "")) if l["questionId"] in ("C2_WRITTEN", "C3_WRITTEN") else l
                for l in super().readback(iv, check_standing)]


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AnEstateWhoseCharterStandsWritten(unittest.TestCase):
    """A second run: the Policy Interview is answered again over a written charter, so the read-back says the standing limits are kept."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(currency_spoken_as_code=True)
        cls.tmp = tempfile.mkdtemp()
        cls.first, cls.first_outcomes = run(cls.double, cls.tmp)
        cls.runner = runner_on(cls.double, cls.tmp)  # the second full run signs in with the stored passkeys
        cls.outcomes = {o.station: o for o in cls.runner.run()}

    def test_the_first_run_was_written_and_the_second_reads_back_kept(self):
        self.assertEqual(line(lines_of(self.first), "C2_WRITTEN")["spoken"], WRITTEN_C2)
        self.assertIn("this estate has walked before", self.outcomes["S2"].line)
        self.assertEqual(self.outcomes["S3"].outcome, H.PASS, self.outcomes["S3"].line)
        self.assertNotEqual(self.runner.facts["interview"]["policy"], self.first.facts["interview"]["policy"], "a written charter is amended by a new interview")
        lines = lines_of(self.runner)
        self.assertEqual(line(lines, "C2_WRITTEN")["spoken"], WRITTEN_C2 + " " + KEPT)
        self.assertEqual(line(lines, "C3_WRITTEN")["spoken"], WRITTEN_C3 + " " + KEPT)
        self.assertIs(self.runner.earlier_policy_stood_written(), True, "S2 read the journey at stage 1 done, and S3 began an interview in progress")
        self.assertEqual(self.outcomes["S10"].outcome, H.PASS, self.outcomes["S10"].line)
        self.assertEqual(ceiling_findings(self.runner), [])

    def test_an_estate_that_says_written_over_a_written_charter_is_a_finding_in_its_words(self):
        double = AnEstateThatForgetsItsWrittenCharter()
        tmp = tempfile.mkdtemp()
        run(double, tmp)
        runner = runner_on(double, tmp)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S10"].outcome, H.FAIL, outcomes["S10"].line)
        found = ceiling_findings(runner)
        self.assertEqual([f.probe for f in found], ["read-back (policy) of C2: what the company ceiling becomes", "read-back (policy) of C3: what the daily total becomes"])
        self.assertEqual(found[0].expected, WRITTEN_C2 + " " + KEPT)
        self.assertEqual(found[0].said, "the read-back's C2_WRITTEN line says %r — the written form, though S2 found an earlier Policy Interview standing written "
                                        "(the journey's stage 1 done before S3)" % WRITTEN_C2)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AVersion14Estate(unittest.TestCase):
    """An estate before Spec AER360-115 serves neither question: the book answers it as before, and S3's sentence names both versions."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(catalog_version=14, currency_spoken_as_code=True)
        cls.runner, cls.outcomes = run(cls.double, tempfile.mkdtemp())

    def test_s3_answers_the_23_and_names_both_versions(self):
        o = self.outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("policy interview: 23 questions answered", o.line)
        self.assertIn("; the answer book answers catalog version 15, and the estate served 23 question(s), every one known to the book%s (%s)" % (
            VERSION_14_CLAUSE, H.ESTATE_STATES_NO_CATALOG_VERSION), o.line)
        given = [q for q, _, _, _ in self.runner.facts["answers"]["policy"]]
        self.assertEqual(given, [q.id for q in A.expected_walk("policy") if q.id not in A.ADDED_IN_V15["policy"]])

    def test_the_read_back_carries_no_ceiling_line_and_s10_expects_none(self):
        self.assertFalse(any(l["questionId"] in ("C2", "C3", "C2_WRITTEN", "C3_WRITTEN") for l in lines_of(self.runner)))
        self.assertEqual(self.outcomes["S10"].outcome, H.PASS, self.outcomes["S10"].line)
        self.assertEqual(ceiling_findings(self.runner), [])
        charter = self.runner.facts["charter"]["policy"]
        self.assertEqual((charter["amountsUsdCents"]["denyCeiling"], charter["amountsUsdCents"]["dailyTotal"]), (None, None), "never asked, never compiled")

    def test_the_sentence_names_the_version_the_questions_show(self):
        walk = [q.id for q in A.expected_walk("policy")]
        self.assertEqual(H.version_15_words(walk), "")
        self.assertEqual(H.version_15_words([q for q in walk if q not in ("C2", "C3")]), VERSION_14_CLAUSE)
        before_14 = [q for q in walk if q not in ("C2", "C3", "C11A", "C11C", "C19")]
        self.assertEqual(H.version_15_words(before_14), VERSION_14_CLAUSE.replace("catalog version 14", "a catalog version before 14"))
        self.assertEqual(H.version_15_words([q for q in walk if q != "C3"]), "; this Policy Interview asks C2 and not C3, though catalog version 15 added both")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheReadBackHeldToTheTwoLines(unittest.TestCase):
    """A read-back without the two lines, with another figure, elsewhere or under another heading is a finding in the estate's words."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(currency_spoken_as_code=True)
        cls.runner, cls.outcomes = run(cls.double, tempfile.mkdtemp())
        cls.answers = cls.runner.facts["answers"]["policy"]
        cls.lines = lines_of(cls.runner)

    def audit(self, lines, amending=False):
        return [f for f in H.audit_readback("policy", self.answers, lines, amending) if "C2" in f["probe"] or "C3" in f["probe"]]

    def test_a_read_back_without_the_two_lines_is_two_findings(self):
        found = self.audit([l for l in self.lines if l["questionId"] not in ("C2_WRITTEN", "C3_WRITTEN")])
        self.assertEqual([(f["probe"], f["expected"], f["said"]) for f in found], [
            ("read-back (policy) of C2: what the company ceiling becomes", WRITTEN_C2, "the read-back carries no line (C2_WRITTEN) saying what the company ceiling becomes"),
            ("read-back (policy) of C3: what the daily total becomes", WRITTEN_C3, "the read-back carries no line (C3_WRITTEN) saying what the daily total becomes")])

    def test_a_figure_other_than_the_books_is_a_finding_carrying_the_estates_words(self):
        other = WRITTEN_C2.replace("US$100.", "US$1,000.")
        found = self.audit([dict(l, spoken=other) if l["questionId"] == "C2_WRITTEN" else l for l in self.lines])
        self.assertEqual([(f["probe"], f["sent"], f["expected"], f["said"]) for f in found], [
            ("read-back (policy) of C2: what the company ceiling becomes", {"cents": "10000"}, WRITTEN_C2, "the read-back's C2_WRITTEN line says %r" % other)])
        kept_on_a_fresh_estate = self.audit([dict(l, spoken=WRITTEN_C3 + " " + KEPT) if l["questionId"] == "C3_WRITTEN" else l for l in self.lines])
        self.assertEqual([f["said"] for f in kept_on_a_fresh_estate], [
            "the read-back's C3_WRITTEN line says %r — the kept form, though S2 found no earlier Policy Interview standing written (the journey's stage 1 not done before S3)" % (WRITTEN_C3 + " " + KEPT)])

    def test_a_line_standing_elsewhere_or_under_another_heading_is_a_finding(self):
        moved = [l for l in self.lines if l["questionId"] != "C2_WRITTEN"] + [line(self.lines, "C2_WRITTEN")]
        found = self.audit(moved)
        self.assertEqual([f["probe"] for f in found], ["read-back (policy) of C2: what the company ceiling becomes (where it stands)"])
        self.assertEqual(found[0]["expected"], "the line directly after C2's")
        headed = self.audit([dict(l, prompt="What the ceiling is") if l["questionId"] == "C3_WRITTEN" else l for l in self.lines])
        self.assertEqual([(f["probe"], f["said"]) for f in headed], [("read-back (policy) of C3: what the daily total becomes (the prompt)", "the read-back's C3_WRITTEN line is headed 'What the ceiling is'")])

    def test_where_the_harness_did_not_see_how_the_estate_stood_either_form_is_admitted_and_noted(self):
        for spoken_c2, form in ((WRITTEN_C2, "written"), (WRITTEN_C2 + " " + KEPT, "kept")):
            lines = [dict(l, spoken=spoken_c2) if l["questionId"] == "C2_WRITTEN" else l for l in self.lines]
            found = [f for f in self.audit(lines, amending=None) if "C2" in f["probe"]]
            self.assertEqual(len(found), 1, found)
            self.assertTrue(found[0]["not_compared"])
            self.assertEqual(found[0]["said"], "the estate spoke the %s form (C2_WRITTEN); this run did not read the journey before S3 began the interview, so whether an earlier "
                                               "Policy Interview stood written is not known here and the form was not judged" % form)
        wrong = self.audit([dict(l, spoken="Nothing is written.") if l["questionId"] == "C2_WRITTEN" else l for l in self.lines], amending=None)
        self.assertEqual([f.get("not_compared") for f in wrong if "C2" in f["probe"]], [None], "a sentence of neither form is still a finding")
        self.assertEqual(wrong[0]["expected"], "%s — or, where an earlier Policy Interview stands written, %s" % (WRITTEN_C2, WRITTEN_C2 + " " + KEPT))

    def test_a_run_resumed_at_s3_admits_the_kept_form_and_says_why_it_was_not_judged(self):
        tmp = tempfile.mkdtemp()
        double = EstateDouble(currency_spoken_as_code=True)
        run(double, tmp)
        runner, outcomes = run(double, tmp, start_at="S3")
        self.assertEqual(outcomes["S2"].outcome, H.SKIPPED)
        self.assertIsNone(runner.earlier_policy_stood_written())
        self.assertEqual(line(lines_of(runner), "C2_WRITTEN")["spoken"], WRITTEN_C2 + " " + KEPT, "the estate knows its charter stands written")
        self.assertEqual(outcomes["S10"].outcome, H.PASS, outcomes["S10"].line)
        self.assertIn("read-back (policy) of C2: what the company ceiling becomes: the estate spoke the kept form (C2_WRITTEN); this run did not read the journey before S3 "
                      "began the interview, so whether an earlier Policy Interview stood written is not known here and the form was not judged", runner.notes["S10"])


class AnEstateAtALaterCatalog(EstateDouble):
    """An estate whose Policy Interview asks a question no catalog the book read asks — the next version's, say."""

    def __init__(self, **kwargs):
        super().__init__(currency_spoken_as_code=True, **kwargs)

    def catalog(self, interview_type, version=None):
        questions = super().catalog(interview_type, version)
        if interview_type == "policy":
            questions.insert([q.id for q in questions].index("C10"), A.Question("C4", "money", None, None, True))
        return questions


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheRefusalsTellTheTruth(unittest.TestCase):
    """§4: an unknown question still stops the run with its id, prompt and kind, the book's version 15 in the sentence; the estate refuses a wrong figure in its own words."""

    def test_a_question_the_book_does_not_know_stops_s3_naming_version_15(self):
        with unittest.mock.patch.dict(D.PROMPTS, {"C4": {"part": "Part C — The company’s rules", "prompt": "How much may this company pay in a week?"}}):
            runner, outcomes = run(AnEstateAtALaterCatalog(), tempfile.mkdtemp())
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("the answer book has no answer for policy question C4 (money): How much may this company pay in a week? — the answer book answers catalog version 15; "
                      "%s, and it served a question the book does not know, so its catalog is later than 15 or is not the one the book read (%s)" % (
                          H.ESTATE_STATES_NO_CATALOG_VERSION, A.CATALOG_SOURCE), o.line)
        self.assertIn("b523cbf", o.line)
        self.assertEqual([q for q, _, _, _ in runner.facts["answers"]["policy"]][-3:], ["C9", "C2", "C3"], "answered up to the question it does not know, and not past it")

    def test_a_zero_in_the_book_is_refused_at_the_page_in_the_estates_words(self):
        with unittest.mock.patch.dict(A.POLICY_ANSWERS, {"C2": {"cents": "0"}}):
            runner, outcomes = run(EstateDouble(currency_spoken_as_code=True), tempfile.mkdtemp())
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("for C2 answered", o.line)
        self.assertIn(ZERO_REFUSED, o.line)
        self.assertNotIn("C2", [q for q, _, _, _ in runner.facts["answers"]["policy"]], "nothing is committed past the refusal")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheDoubleIsTheEstateAtVersion15(unittest.TestCase):
    """The double refuses what the estate refuses at version 15, with its sentences, and serves each interview by its own catalog version."""

    def setUp(self):
        self.double = EstateDouble(currency_spoken_as_code=True)
        self.tmp = tempfile.mkdtemp()
        self.link = self.double.mint_founder_link()
        self.runner = runner_on(self.double, self.tmp, invite=self.link)
        self.founder = self.runner.people[A.FOUNDER]
        self.runner.enrol_by_invite(self.founder, self.link, "test")

    def request(self, method, path, body=None):
        return self.runner.request(self.founder, method, path, body, "test")

    def walk_to(self, stop_at):
        started = self.request("POST", "/v1/onboarding/interviews", {"interviewType": "policy"})
        iv, page = started.json["interview"]["id"], started.json["page"]
        while page.get("question") and page["question"]["questionId"] != stop_at and page.get("state") == "in_progress":
            qid = page["question"]["questionId"]
            page = self.request("POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": qid, "value": A.POLICY_ANSWERS[qid]}).json
        return iv, page

    def test_c2_is_served_after_c9_as_the_catalog_defines_it(self):
        iv, page = self.walk_to("C2")
        question = page["question"]
        self.assertEqual(page["previousQuestionId"], "C9")
        page_of = {p["questionId"]: p for p in D.V15_ADDED.values()}["C2"]
        self.assertEqual({k: question[k] for k in ("questionId", "part", "kind", "prompt", "note", "required")}, page_of)
        self.assertIsNone(question["options"])
        self.assertIsNone(question["priorValue"], "a blank field: no figure arrives written and none is suggested")

    def test_a_zero_or_a_blank_ceiling_is_refused_at_the_page(self):
        iv, page = self.walk_to("C2")
        zero = self.request("POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "C2", "value": {"cents": "0"}})
        self.assertEqual(zero.status, 400)
        self.assertEqual((zero.refusal["code"], zero.refusal["message"], zero.refusal["detail"]), ("ANSWER_INVALID", ZERO_REFUSED, {"questionId": "C2", "cause": REQUIRED}))
        blank = self.request("POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "C2", "value": {"cents": None}})
        self.assertEqual(blank.status, 400)
        self.assertEqual((blank.refusal["code"], blank.refusal["detail"]), ("ANSWER_INVALID", {"questionId": "C2", "cause": REQUIRED}))
        self.assertNotIn("C2", self.double.latest(iv), "nothing was committed")
        self.assertEqual(self.request("POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "C2", "value": {"cents": "10000"}}).status, 200)

    def test_the_compile_refuses_a_charter_without_both_and_names_the_page(self):
        iv, page = self.walk_to(None)
        latest = {qid: row["value"] for qid, row in self.double.latest(iv).items()}
        self.assertEqual(self.double.compile_charter("policy", latest, 15)["amountsUsdCents"]["denyCeiling"], "10000")
        for missing, zero, walked_to, detail in ((("C2",), (), "C2", {"cause": REQUIRED, "unanswered": "C2"}), ((), ("C3",), "C3", {"cause": REQUIRED, "answeredZero": "C3"})):
            answers = {q: ({"cents": "0"} if q in zero else v) for q, v in latest.items() if q not in missing}
            with self.assertRaises(Refusal) as caught:
                self.double.compile_charter("policy", answers, 15)
            self.assertEqual((caught.exception.code, caught.exception.message, caught.exception.detail, caught.exception.extra),
                             ("CHARTER_INCOMPLETE", REFUSED_AT_COMPILE, detail, {"walkBackTo": {"questionId": walked_to}}))
        before = {q: v for q, v in latest.items() if q not in ("C2", "C3")}
        self.assertEqual(self.double.compile_charter("policy", before, 14)["amountsUsdCents"]["denyCeiling"], None, "an interview of version 14 compiles exactly as before")

    def test_a_version_14_draft_in_flight_is_never_asked_the_two_and_the_next_interview_is(self):
        double = EstateDouble(catalog_version=14, currency_spoken_as_code=True)
        link = double.mint_founder_link()
        runner = runner_on(double, tempfile.mkdtemp(), invite=link)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        started = runner.request(founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"}, "test")
        iv, page = started.json["interview"]["id"], started.json["page"]
        double.catalog_version = 15  # AER 360 Spec AER360-115 goes live with the draft in flight
        served = []
        while page.get("question") and page.get("state") == "in_progress":
            qid = page["question"]["questionId"]
            served.append(qid)
            page = runner.request(founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": qid, "value": A.POLICY_ANSWERS[qid]}, "test").json
        self.assertEqual(served[served.index("C9") + 1], "C10", "the draft was begun under version 14, and seedCatalog never rewrites a version's rows")
        self.assertFalse(any(l["questionId"] in ("C2_WRITTEN", "C3_WRITTEN") for l in double.readback_lines_for_test(iv)))
        runner.confirm_and_compile("test", "policy", iv, founder, page)
        again = runner.request(founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"}, "test")
        self.assertNotEqual(again.json["interview"]["id"], iv)
        self.assertEqual(double.interviews[again.json["interview"]["id"]]["catalogVersion"], 15, "the charter is amended by a new interview, begun under version 15")


if __name__ == "__main__":
    unittest.main()
