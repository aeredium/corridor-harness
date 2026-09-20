"""
The answer book covers every question id of the live catalog (Spec T7): a test reads the ids from
a fixture copied from questioncatalog.v11.ts and fails on any id without an answer, and every
answer has the shape its kind takes and a choice the catalog offers.
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_tables as T  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "aer360-questioncatalog.v11.ts")


def fixture_questions():
    """(interview type, id, kind, prompt) for every question the frozen v11 catalog shipped."""
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        text = handle.read()
    policy_text = text.split("CATALOG_V11_POLICY", 1)[1].split("CATALOG_V11_ACCOUNT", 1)[0]
    account_text = text.split("CATALOG_V11_ACCOUNT", 1)[1].split("export const CATALOG_V11:", 1)[0]
    pattern = re.compile(r'questionId: "([A-Z0-9]+)",\s*part: "[^"]*",\s*kind: "([a-z_]+)",\s*prompt: "((?:[^"\\]|\\.)*)"')
    out = []
    for interview_type, body in (("policy", policy_text), ("wallet_account", account_text)):
        for match in pattern.finditer(body):
            out.append((interview_type, match.group(1), match.group(2), match.group(3)))
    return out


class TheBookCoversTheCatalog(unittest.TestCase):
    def setUp(self):
        self.questions = fixture_questions()

    def test_the_fixture_is_the_frozen_catalog_version_11_with_both_interviews(self):
        with open(FIXTURE, "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("THE FROZEN CATALOG VERSION 11", text)
        self.assertIn("Generated FROM the v11 catalog. Never edited by hand.", text)
        ids = [q[1] for q in self.questions]
        self.assertEqual(len(ids), 68)
        self.assertEqual(len(set(ids)), 68)
        self.assertIn(("policy", "C16"), [(q[0], q[1]) for q in self.questions], "version 11 still asked C16")
        self.assertIn(("wallet_account", "WA2"), [(q[0], q[1]) for q in self.questions])

    def test_every_id_of_the_fixture_has_an_answer_of_its_kind(self):
        for interview_type, qid, kind, prompt in self.questions:
            book = A.ANSWERS[interview_type]
            self.assertIn(qid, book, "no answer for %s %s (%s): %s" % (interview_type, qid, kind, prompt))
            self.assertEqual(A.kind_of(interview_type, qid), kind, "the book knows %s as another kind" % qid)
            field = A.SHAPE_OF_KIND[kind]
            self.assertIn(field, book[qid], "the answer to %s (%s) carries no %r" % (qid, kind, field))

    def test_the_book_answers_nothing_the_fixture_does_not_ask(self):
        asked = {(q[0], q[1]) for q in self.questions}
        for interview_type, book in A.ANSWERS.items():
            for qid in book:
                self.assertIn((interview_type, qid), asked, "the book answers %s %s, which version 11 never asked" % (interview_type, qid))

    def test_every_choice_is_one_the_live_catalog_offers(self):
        for interview_type, book in A.ANSWERS.items():
            for qid, value in book.items():
                q = A.question(interview_type, qid)
                if q.kind == "single_choice":
                    self.assertIn(value["choice"], q.options, "%s's answer is not among its options" % qid)
                if q.kind == "multi_choice":
                    for c in value["choices"]:
                        self.assertIn(c, q.options, "%s's choice %r is not among its options" % (qid, c))

    def test_the_option_strings_are_the_catalogs_own_words(self):
        # spelled with the catalog's typographic apostrophes and dashes, byte for byte
        self.assertEqual(A.question("policy", "D4").options[1], "Stop it cold — halt the agent’s account until a person restores it")
        self.assertEqual(A.question("wallet_account", "W1").options[1], "Treasury — holding and protecting the company’s digital assets")
        self.assertEqual(A.question("wallet_account", "WA2").options[0], "Yes — one person can both submit and release, where the quorum allows it")
        self.assertEqual(A.question("policy", "A9").options[0], "No — this company stands alone")
        self.assertEqual(A.question("policy", "C16").options, ["4 hours", "24 hours", "3 days", "Custom"])

    def test_money_is_a_whole_number_of_cents_never_a_float(self):
        for interview_type, book in A.ANSWERS.items():
            for qid, value in book.items():
                if "cents" in value and value["cents"] is not None:
                    self.assertIsInstance(value["cents"], str, qid)
                    self.assertRegex(value["cents"], r"^\d+$", qid)
                if "percent" in value and value["percent"] is not None:
                    self.assertTrue(0 < value["percent"] <= 100, qid)
        self.assertEqual(A.MONEY["per_payment_cents"], "1000000")
        self.assertEqual(A.MONEY["per_day_cents"], "5000000")
        self.assertEqual(A.MONEY["treasury_ceiling_cents"], "25000000")
        self.assertEqual(A.ACCOUNT_ANSWERS["O2"]["cents"], A.MONEY["per_payment_cents"])
        self.assertEqual(A.ACCOUNT_ANSWERS["O1"]["cents"], A.MONEY["per_day_cents"])
        self.assertEqual(A.ACCOUNT_ANSWERS["T1"]["cents"], A.MONEY["treasury_ceiling_cents"])


class TheBookIsTheSpecsEstate(unittest.TestCase):
    def test_the_estate_its_people_and_their_emails(self):
        self.assertEqual(A.ESTATE["company"], "Harness Holdings Pty Ltd")
        self.assertEqual(A.ESTATE["client_id"], "harness-holdings")
        self.assertEqual(A.ESTATE["country"], "Australia")
        self.assertEqual(A.ESTATE["display_currency"], "AUD")
        names = [A.PEOPLE[k].name for k in A.CENSUS_ORDER]
        self.assertEqual(names, ["Harriet Founder", "Ada Approver", "Ben Signatory", "Cora Clerk"])
        for person in A.PEOPLE.values():
            self.assertRegex(person.email, r"^harness\+[a-z]+@aeredium\.io$")
            self.assertEqual(person.email, "harness+%s@aeredium.io" % person.key)
        self.assertEqual(A.PEOPLE["ada"].role, "author")
        self.assertEqual(A.PEOPLE["ben"].role, "author")
        self.assertEqual(A.PEOPLE["cora"].role, "author")
        self.assertEqual(A.PEOPLE["olive"].role, "viewer")
        for key in A.CENSUS_ORDER:
            self.assertIn(A.PEOPLE[key].census, A.FINANCE_ROLES)

    def test_the_rules_the_spec_decided(self):
        self.assertEqual(A.POLICY_ANSWERS["C10"]["choice"], "1", "one approver for every payment")
        self.assertEqual(A.POLICY_ANSWERS["C11"]["people"], [A.PEOPLE["ada"].email], "C11 names Ada")
        self.assertEqual(A.POLICY_ANSWERS["C12"]["choice"], "2", "two for a change of rules")
        self.assertEqual(A.POLICY_ANSWERS["B4"]["choices"], [], "sight granted to no level beneath")
        self.assertEqual(A.POLICY_ANSWERS["A9"]["choice"], "No — this company stands alone", "no levels beneath")
        self.assertEqual(A.POLICY_ANSWERS["A11"]["choice"], "No", "no agents yet")
        self.assertEqual(A.POLICY_ANSWERS["R1"]["choice"], "No", "recovery: the least the catalog allows")
        self.assertEqual(A.POLICY_ANSWERS["C9"]["choices"], [T.C9_NETWORK_CHOICE])
        self.assertEqual(A.ACCOUNT_ANSWERS["WN"]["text"], "Operating account")
        self.assertEqual(A.ACCOUNT_ANSWERS["W1"]["choice"], "Operations — day-to-day business payments")
        self.assertEqual(A.ACCOUNT_ANSWERS["O3"]["choice"], "Yes", "pause the first payment to somewhere new (Spec 69)")

    def test_the_quorums_never_exceed_the_rosters_that_must_meet_them(self):
        """crosschecks.ts: a quorum may never exceed the roster; WA2's No beside one approver is refused at the page."""
        self.assertLessEqual(int(A.POLICY_ANSWERS["C10"]["choice"]), len(A.POLICY_ANSWERS["C11"]["people"]))
        self.assertLessEqual(int(A.POLICY_ANSWERS["C12"]["choice"]), len(A.POLICY_ANSWERS["A8"]["entries"]))
        self.assertLessEqual(int(A.ACCOUNT_ANSWERS["WQ"]["choice"]), len(A.ACCOUNT_ANSWERS["WA1"]["entries"]))
        if len(A.ACCOUNT_ANSWERS["WA1"]["entries"]) == 1:
            self.assertEqual(A.ACCOUNT_ANSWERS["WA2"]["choice"], A.WA2_YES)
        self.assertEqual(A.POLICY_ANSWERS["C15"]["choice"], "Yes", "C15 and WA2 are one fact, one field")
        # every roster email is a census email
        census = {e["email"] for e in A.POLICY_ANSWERS["A8"]["entries"]}
        for email in A.POLICY_ANSWERS["C11"]["people"]:
            self.assertIn(email, census)
        for entry in A.ACCOUNT_ANSWERS["WA1"]["entries"]:
            self.assertIn(entry["email"], census)

    def test_the_walk_the_book_expects_of_a_version_12_estate(self):
        self.assertEqual([q.id for q in A.expected_walk("policy")],
                         ["A1", "A4", "A5", "A8", "A9", "A11", "B1", "B2", "B3", "C9S", "C9", "C10", "C11", "C15", "C18", "C12", "C12A", "D0", "R0", "R1", "G1"])
        self.assertEqual([q.id for q in A.expected_walk("wallet_account")],
                         ["W0", "WN", "W1", "O1", "O2", "O3", "O4", "PN0", "PN1", "WQ", "WA1", "WA2", "WCW", "WG1"])
        self.assertNotIn("C16", [q.id for q in A.expected_walk("policy")], "version 12 never serves the retired pair")

    def test_the_whitelist_roster_is_the_a8_census_and_its_quorum_is_c12(self):
        """Spec T9 §4: WHITELIST_ROSTER is the A8 census names and WHITELIST_QUORUM is the C12 answer, so the harness's expectation is the charter's."""
        census_names = [e["name"] for e in A.POLICY_ANSWERS["A8"]["entries"]]
        self.assertEqual(list(A.WHITELIST_ROSTER), census_names)
        self.assertEqual(list(A.WHITELIST_ROSTER), [A.PEOPLE[k].name for k in A.CENSUS_ORDER])
        self.assertEqual(A.WHITELIST_QUORUM, int(A.POLICY_ANSWERS["C12"]["choice"]))
        self.assertEqual(A.WHITELIST_QUORUM, 2)
        # a roster of four at a quorum of two can meet its quorum: the finding of the second live run was the harness's, not the estate's
        self.assertGreaterEqual(len(A.WHITELIST_ROSTER), A.WHITELIST_QUORUM)
        # C12A is No, so C12's one number governs every change family (onboardingcompiler.ts, governanceRecordsFor)
        self.assertEqual(A.POLICY_ANSWERS["C12A"]["choice"], "No")

    def test_the_payments_the_spec_decided(self):
        self.assertEqual([(p.key, p.amount, p.expect) for p in A.PAYMENTS],
                         [("P1", "1250.00", "proceeds to approval"), ("P2", "4999.99", "waits"), ("P3", "12000.00", "held")])
        self.assertEqual(A.PAYMENTS[0].amount_minor, "1250000000")
        self.assertEqual(A.PAYMENTS[1].amount_minor, "4999990000")
        self.assertEqual(A.PAYMENTS[2].amount_minor, "12000000000")
        self.assertEqual(A.PAYMENTS[0].payee_key, "NORTHWIND_ETHEREUM")
        self.assertIsNone(A.PAYMENTS[1].payee_key, "the second payment goes to an address not on the list")
        self.assertEqual(A.PAYMENTS[2].payee_key, "CONTOSO_ETHEREUM")


class AnswerForAServedPage(unittest.TestCase):
    def test_a_known_question_answers_from_the_book_and_checks_the_options_the_page_offers(self):
        page = {"questionId": "A9", "kind": "single_choice", "prompt": "Will anyone stand at a level beneath you…", "options": A.question("policy", "A9").options}
        self.assertEqual(A.answer_for("policy", page), A.POLICY_ANSWERS["A9"])
        currency = {"questionId": "A5", "kind": "currency", "prompt": "What currency…", "options": ["AUD", "EUR", "USD"]}
        self.assertEqual(A.answer_for("policy", currency), {"text": "AUD"})

    def test_an_unknown_question_stops_with_its_id_prompt_and_kind(self):
        with self.assertRaises(A.UnknownQuestion) as caught:
            A.answer_for("policy", {"questionId": "Z9", "kind": "money", "prompt": "How much may the moon cost?", "options": None})
        self.assertEqual((caught.exception.question_id, caught.exception.kind, caught.exception.prompt), ("Z9", "money", "How much may the moon cost?"))
        self.assertIn("Z9", str(caught.exception))
        self.assertIn("How much may the moon cost?", str(caught.exception))

    def test_a_choice_the_page_does_not_offer_stops_with_the_options_offered(self):
        with self.assertRaises(A.AnswerDoesNotFit) as caught:
            A.answer_for("policy", {"questionId": "A9", "kind": "single_choice", "prompt": "…", "options": ["Yes", "No"]})
        self.assertEqual(caught.exception.offered, ["Yes", "No"])
        with self.assertRaises(A.AnswerDoesNotFit):
            A.answer_for("policy", {"questionId": "A5", "kind": "currency", "prompt": "…", "options": ["USD", "EUR"]})

    def test_a_kind_that_moved_stops_the_run(self):
        with self.assertRaises(A.AnswerDoesNotFit) as caught:
            A.answer_for("policy", {"questionId": "C10", "kind": "money", "prompt": "…", "options": None})
        self.assertIn("the estate serves it as money", caught.exception.cause)


if __name__ == "__main__":
    unittest.main()
