"""
The three hats (Spec T7): the S10 comparisons are tested on a fixture charter with one planted
disagreement; each S11 probe has a test against the local double that answers as routes/guards.ts
and the interview do; the S12 measures are read off a recorded call log.

Spec T8 (20 September 2026): the read-back is compared by content, in the estate's own spoken forms
(the live census line of 20 September against the book's JSON entries is no finding; one moved name
is one finding naming the entry; a kind with no rendering is not compared); the venue probe expects
acceptance, and a double that refuses reads as a finding with the ruling quoted; a run with
four-second invitations passes S12 and the report says where the seconds go; two reports in the
folder give the closing table its last-run column, with closed, still open and new.
"""
import copy
import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import Clock, EstateDouble, VENUE_STIPULATION, runner_on  # noqa: E402

# The estate's own A8 line from the first live run, 20 September 2026 (report aer360-harness-2026-09-20.md), word for word:
# the entries the book sends as name, email, role, spoken in the order jsonb stores them.
LIVE_CENSUS_LINE = ("Harriet Founder — Authorise payments — harness+harriet@aeredium.io; Ada Approver — Release payments — harness+ada@aeredium.io; "
                    "Ben Signatory — Authorise payments — harness+ben@aeredium.io; Cora Clerk — Enter payments — harness+cora@aeredium.io")


def fixture_answers(interview_type):
    """The answers as the harness records them: (id, value, prompt, kind) for the walk the book expects."""
    return [(q.id, A.ANSWERS[interview_type][q.id], "prompt of %s" % q.id, q.kind) for q in A.expected_walk(interview_type)]


def fixture_readback(interview_type):
    lines = [{"questionId": "REALM", "prompt": "Where this estate opens", "spoken": "This estate opens in the Sandbox…", "synthetic": True}]
    for qid, value, prompt, kind in fixture_answers(interview_type):
        lines.append({"questionId": qid, "prompt": prompt, "spoken": H.spoken_for(kind, qid, value)})
    return lines


def fixture_charter(interview_type):
    """A compiled charter that agrees with the book, in the shape onboardingcompiler.ts records."""
    if interview_type == "policy":
        return {"interviewType": "policy", "name": A.ESTATE["company"], "purpose": None, "allowedChains": ["aeredium-testnet"], "recordedChains": ["aeredium", "ethereum"],
                "realm": "sandbox", "whitelistMode": None, "whitelistEntries": [], "quorum": 1, "signers": [A.PEOPLE["ada"].email],
                "changeApprovers": ["%s <%s>" % (A.PEOPLE[k].name, A.PEOPLE[k].email) for k in A.CENSUS_ORDER], "isAgentsAccount": False, "principal": None,
                "amountsUsdCents": {"denyCeiling": None, "holdOverPerTx": None, "dailyTotal": None, "weeklyTotal": None, "monthlyTotal": None},
                "requesterCountsAsSigner": True, "securityContact": {"name": A.PEOPLE["harriet"].name, "email": A.PEOPLE["harriet"].email},
                "mutationGovernance": [{"scope": "all", "quorum": 2}]}
    return {"interviewType": "wallet_account", "name": A.WALLET_ACCOUNT_NAME, "purpose": A.WALLET_ACCOUNT_PURPOSE, "allowedChains": ["aeredium-testnet"], "recordedChains": ["aeredium"],
            "realm": "sandbox", "whitelistMode": "hold_non_listed", "whitelistEntries": [], "quorum": 1, "signers": ["%s <%s>" % (A.PEOPLE["ada"].name, A.PEOPLE["ada"].email)],
            "isAgentsAccount": False, "principal": A.PEOPLE["cora"].email,
            "amountsUsdCents": {"denyCeiling": None, "holdOverPerTx": A.MONEY["per_payment_cents"], "dailyTotal": A.MONEY["per_day_cents"], "weeklyTotal": None, "monthlyTotal": None},
            "requesterCountsAsSigner": True, "securityContact": None}


class TheAuditorOnAFixture(unittest.TestCase):
    def test_a_charter_that_agrees_with_the_answers_raises_no_finding(self):
        for interview_type in A.INTERVIEW_TYPES:
            answers = {q: v for q, v, _, _ in fixture_answers(interview_type)}
            self.assertEqual(H.audit_charter(interview_type, fixture_charter(interview_type), answers), [], interview_type)

    def test_one_planted_disagreement_in_the_charter_is_the_one_finding(self):
        answers = {q: v for q, v, _, _ in fixture_answers("policy")}
        charter = fixture_charter("policy")
        charter["quorum"] = 2
        findings = H.audit_charter("policy", charter, answers)
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0]["probe"], "charter (policy): the release quorum (C10)")
        self.assertEqual(findings[0]["expected"], "1")
        self.assertEqual(findings[0]["said"], "the charter carries 2")
        account = fixture_charter("wallet_account")
        account["amountsUsdCents"]["holdOverPerTx"] = "999999"
        found = H.audit_charter("wallet_account", account, {q: v for q, v, _, _ in fixture_answers("wallet_account")})
        self.assertEqual([f["probe"] for f in found], ["charter (wallet_account): the per-payment hold (O2)"])
        self.assertEqual(found[0]["expected"], json.dumps(A.MONEY["per_payment_cents"]))

    def test_a_sandbox_charter_naming_a_live_network_is_a_finding(self):
        answers = {q: v for q, v, _, _ in fixture_answers("policy")}
        charter = fixture_charter("policy")
        charter["allowedChains"] = ["aeredium-testnet", "ethereum"]
        findings = H.audit_charter("policy", charter, answers)
        self.assertEqual([f["probe"] for f in findings], ["charter (policy): a sandbox charter naming a live network"])

    def test_the_read_back_that_agrees_raises_no_finding_and_one_moved_word_is_one_finding(self):
        for interview_type in A.INTERVIEW_TYPES:
            self.assertEqual(H.audit_readback(interview_type, fixture_answers(interview_type), fixture_readback(interview_type)), [], interview_type)
        lines = fixture_readback("policy")
        c10 = next(l for l in lines if l["questionId"] == "C10")
        c10["spoken"] = "2"
        findings = H.audit_readback("policy", fixture_answers("policy"), lines)
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0]["probe"], "read-back (policy) of C10")
        self.assertEqual(findings[0]["expected"], "1")
        self.assertEqual(findings[0]["said"], "the read-back says '2'")
        missing = [l for l in fixture_readback("policy") if l["questionId"] != "C18"]
        self.assertEqual([f["said"] for f in H.audit_readback("policy", fixture_answers("policy"), missing)],
                         ["the read-back has no line for C18, which was answered"])
        extra = fixture_readback("policy") + [{"questionId": "C16", "prompt": "…", "spoken": "24 hours"}]
        self.assertEqual(len(H.audit_readback("policy", fixture_answers("policy"), extra)), 1)

    def test_the_read_back_is_spoken_as_readback_spells_it(self):
        self.assertEqual(H.spoken_for("statement", "B1", {"acknowledged": True}), "Stated and acknowledged.")
        self.assertEqual(H.spoken_for("money", "O2", {"cents": "1000000"}), "US$10,000 and 00 cents.")
        self.assertEqual(H.spoken_for("money", "O2", {"cents": "499999"}), "US$4,999 and 99 cents.")
        self.assertEqual(H.spoken_for("money", "T1", {"cents": None}), "Left empty — no limit; the loosest possible answer.")
        self.assertEqual(H.spoken_for("multi_choice", "B4", {"choices": []}),
                         "No grants made — each level below you sees only its own level, and you see every level. The safest answer, and the one that stands until you change it.")
        self.assertEqual(H.spoken_for("multi_choice", "C9", {"choices": []}), "None chosen.")
        self.assertEqual(H.spoken_for("list", "C18", {"entries": [{"name": "Harriet Founder", "email": "harness+harriet@aeredium.io"}]}), "Harriet Founder — harness+harriet@aeredium.io")
        # a list entry's values in the order the estate stores them (jsonb: shortest key first, then byte order), never the order sent
        self.assertEqual(H.spoken_for("list", "A8", {"entries": [{"name": "Harriet Founder", "email": "harness+harriet@aeredium.io", "role": "Authorise payments"}]}),
                         "Harriet Founder — Authorise payments — harness+harriet@aeredium.io")
        self.assertEqual(H.spoken_for("list", "A8", {"entries": A.POLICY_ANSWERS["A8"]["entries"]}), LIVE_CENSUS_LINE)
        self.assertEqual(H.spoken_for("list", "P1", {"entries": [{"label": "Northwind", "address": "0xabc"}]}), "Northwind — 0xabc")
        self.assertEqual(H.spoken_for("list", "A8", {"entries": []}), "No entries.")
        self.assertEqual(H.spoken_for("currency", "A5", {"text": "AUD"}), "AUD", "a currency is its code")
        self.assertEqual(H.spoken_for("currency", "A5", {"text": ""}), "Left blank.")
        self.assertEqual(H.spoken_for("percent", "T4", {"percent": None}), "Left empty — never halts on pace.")
        self.assertEqual(H.spoken_for("percent", "X5", {"percent": 2.5}), "2.5 per cent.")
        self.assertEqual(H.spoken_for("percent", "X5", {"percent": 10.0}), "10 per cent.", "as JavaScript prints the number")
        self.assertEqual(H.spoken_for("percent", "X5", {"percent": 0.1234567}), "0.1234567 per cent.")
        self.assertEqual(H.spoken_for("roster_multi", "C11", {"people": []}), "No one chosen.")
        self.assertEqual(H.spoken_for("roster_multi", "C11", {"people": ["a@x.io", "b@x.io"]}), "a@x.io, b@x.io")
        self.assertEqual(H.spoken_for("text", "A4", {"text": "  "}), "Left blank.")
        self.assertEqual(H.spoken_for("count", "C14N", {"count": 1}), "1 payment in a day.")
        self.assertEqual(H.spoken_for("count", "C14N", {"count": 1234}), "1,234 payments in a day.")
        self.assertIsNone(H.spoken_for("duration", "Z1", {"seconds": 5}), "a kind the estate's switch does not name has no rendering here")

    def test_the_census_in_the_estates_spoken_form_against_the_books_json_answers_is_no_finding(self):
        """The live estate's A8 line of 20 September 2026 against the entries the book sends as name, email, role: no finding."""
        self.assertEqual([list(e.keys()) for e in A.POLICY_ANSWERS["A8"]["entries"]], [["name", "email", "role"]] * 4, "the book sends the entry as the wizard does")
        answers = [("A8", A.POLICY_ANSWERS["A8"], "Name them.", "list")]
        lines = [{"questionId": "A8", "prompt": "Name them.", "spoken": LIVE_CENSUS_LINE}]
        self.assertEqual(H.audit_readback("policy", answers, lines), [])

    def test_one_name_that_differs_in_the_census_is_one_finding_naming_the_entry(self):
        answers = [("A8", A.POLICY_ANSWERS["A8"], "Name them.", "list")]
        moved = LIVE_CENSUS_LINE.replace("Ada Approver — Release payments", "Ada Aprover — Release payments")
        findings = H.audit_readback("policy", answers, [{"questionId": "A8", "prompt": "Name them.", "spoken": moved}])
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0]["probe"], "read-back (policy) of A8, entry 2 (Ada Approver)")
        self.assertEqual(findings[0]["expected"], "Ada Approver — Release payments — harness+ada@aeredium.io")
        self.assertEqual(findings[0]["said"], "the read-back says 'Ada Aprover — Release payments — harness+ada@aeredium.io' for this entry")
        self.assertEqual(findings[0]["sent"], A.POLICY_ANSWERS["A8"]["entries"][1])
        self.assertNotIn("not_compared", findings[0])
        # two rows moved: two findings, each naming its row
        two = moved.replace("Cora Clerk — Enter payments", "Cora Clerk — Review payments")
        self.assertEqual([f["probe"] for f in H.audit_readback("policy", answers, [{"questionId": "A8", "prompt": "Name them.", "spoken": two}])],
                         ["read-back (policy) of A8, entry 2 (Ada Approver)", "read-back (policy) of A8, entry 4 (Cora Clerk)"])
        # a row missing altogether: one finding carrying both lines whole
        short = "; ".join(LIVE_CENSUS_LINE.split("; ")[:3])
        whole = H.audit_readback("policy", answers, [{"questionId": "A8", "prompt": "Name them.", "spoken": short}])
        self.assertEqual([f["probe"] for f in whole], ["read-back (policy) of A8"])
        self.assertEqual(whole[0]["expected"], LIVE_CENSUS_LINE)
        self.assertEqual(whole[0]["said"], "the read-back says %r" % short)

    def test_the_currency_is_expected_as_its_code_so_mains_json_is_the_estates_finding(self):
        answers = [("A5", {"text": "AUD"}, "What currency…", "currency")]
        self.assertEqual(H.audit_readback("policy", answers, [{"questionId": "A5", "prompt": "What currency…", "spoken": "AUD"}]), [])
        findings = H.audit_readback("policy", answers, [{"questionId": "A5", "prompt": "What currency…", "spoken": '{"text":"AUD"}'}])
        self.assertEqual([(f["probe"], f["expected"], f["said"]) for f in findings],
                         [("read-back (policy) of A5", "AUD", "the read-back says '{\"text\":\"AUD\"}'")])

    def test_a_kind_the_harness_has_no_rendering_for_is_not_compared_and_is_a_note_not_a_finding(self):
        answers = [("Z1", {"seconds": 5}, "How long?", "duration")]
        lines = [{"questionId": "Z1", "prompt": "How long?", "spoken": "Five seconds."}]
        out = H.audit_readback("policy", answers, lines)
        self.assertEqual(len(out), 1, out)
        self.assertTrue(out[0]["not_compared"])
        self.assertEqual(out[0]["probe"], "read-back (policy) of Z1")
        self.assertEqual(out[0]["said"], "not compared: no rendering for kind duration (the read-back says 'Five seconds.')")
        # S10 records it as a note and raises no finding
        runner = H.Runner("https://estate.test", tempfile.mkdtemp(), None, False, None, tempfile.mkdtemp(),
                          transport=lambda request: (500, [], ""), say=lambda s: None, sleep=lambda s: None)
        runner.facts["answers"]["policy"] = answers
        runner.facts["readback"]["policy"] = {"lines": lines}
        outcome = runner.station_s10()
        self.assertEqual(runner.findings, [])
        self.assertIn("read-back (policy) of Z1: not compared: no rendering for kind duration (the read-back says 'Five seconds.')", runner.notes["S10"])
        self.assertEqual(outcome.outcome, H.PASS)

    def test_the_journey_against_the_registers(self):
        journey = {"currentStage": 4, "stageCount": 7, "stages": [{"id": sid, "done": i < 3} for i, sid in enumerate(H.JOURNEY_STAGE_IDS)]}
        registers = {"charter_stands_written": True, "account_compiled": True, "payees": 2, "sets": 3}
        self.assertEqual(H.audit_journey(journey, registers), [])
        empty = dict(registers, payees=0)
        self.assertEqual([f["probe"] for f in H.audit_journey(journey, empty)], ["journey: stage 3 against the payees and runs registers"])
        stuck = copy.deepcopy(journey)
        stuck["currentStage"] = 1
        self.assertEqual([f["probe"] for f in H.audit_journey(stuck, registers)], ["journey: the current stage against the stages done"])
        no_charter = copy.deepcopy(journey)
        no_charter["stages"][0]["done"] = False
        self.assertIn("journey: stage 1 against the charter's standing", [f["probe"] for f in H.audit_journey(no_charter, registers)])

    def test_the_minor_unit_law(self):
        good = H.Call("S7", "Cora", "GET", "/v1/sets/1", None, H.Answer("GET", "/v1/sets/1", 200, {}, json.dumps({"set": {"aggregate": {"amountBaseMinor": "125000", "baseDecimals": 2}, "approval": {"bandThresholdBaseMinor": "0"}}}), 5), "now")
        self.assertEqual(H.audit_money([good]), [])
        bad = H.Call("S7", "Cora", "GET", "/v1/sets/2", None, H.Answer("GET", "/v1/sets/2", 200, {}, json.dumps({"set": {"aggregate": {"amountBaseMinor": 1250.5}, "rows": [{"amountMinor": 12}]}}), 5), "now")
        findings = H.audit_money([bad])
        self.assertEqual(sorted(f["probe"] for f in findings),
                         sorted(["minor-unit law at set.aggregate.amountBaseMinor (GET /v1/sets/2)", "a float at set.aggregate.amountBaseMinor (GET /v1/sets/2)", "minor-unit law at set.rows[0].amountMinor (GET /v1/sets/2)"]))

    def test_rule_13_on_the_refusals_met(self):
        named = H.Call("S6", "Ada", "POST", "/v1/payees/x/approve", {}, H.Answer("POST", "/v1/payees/x/approve", 403, {}, json.dumps({"error": {"code": "ROLE_NOT_GRANTED", "message": "You are signed into X as a viewer. …"}}), 5), "now")
        bare = H.Call("S7", "Cora", "POST", "/v1/sets", {}, H.Answer("POST", "/v1/sets", 500, {}, "Internal Server Error", 5), "now")
        generic = H.Call("S7", "Cora", "POST", "/v1/sets", {}, H.Answer("POST", "/v1/sets", 500, {}, json.dumps({"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong at our end. Nothing was changed."}}), 5), "now")
        outage = H.Call("S4", "Harriet", "POST", "/v1/invites", {}, H.Answer("POST", "/v1/invites", 403, {}, json.dumps({"error": {"code": "X", "message": "The door could not be reached, try again later."}}), 5), "now")
        own = H.Call("S11", "Olive", "POST", "/v1/payees", {}, H.Answer("POST", "/v1/payees", 500, {}, "boom", 5), "now")
        findings = H.audit_refusals([named, bare, generic, outage, own])
        self.assertEqual([f["probe"] for f in findings], ["Rule 13 at POST /v1/sets (S7)", "Rule 13 at POST /v1/sets (S7)", "Rule 13 at POST /v1/invites (S4)"])
        self.assertIn("no refusal body", findings[0]["said"])
        self.assertIn("INTERNAL_ERROR", findings[1]["said"])
        self.assertIn("could not be reached", findings[2]["said"])
        self.assertIsNone(H.refusal_without_why(403, json.dumps({"error": {"code": "NOT_AUTHENTICATED", "message": "You are not signed in.", "detail": {"cause": "missing or incorrect CSRF token"}}})))

    def test_the_people_register_against_the_invitations(self):
        minted = [{"person": "ada", "role": "author", "invite": {"id": "inv-1", "displayName": "Ada Approver", "email": A.PEOPLE["ada"].email, "role": "author"}}]
        register = {"invites": [{"id": "inv-1", "displayName": "Ada Approver", "email": A.PEOPLE["ada"].email, "role": "author", "state": "redeemed"}]}
        self.assertEqual(H.audit_people(register, minted, {"harriet": "cred-a", "ada": "cred-b"}), [])
        shared = H.audit_people(register, minted, {"harriet": "cred-a", "ada": "cred-a", "ben": "cred-a"})
        self.assertEqual([f["probe"] for f in shared], ["people register: one credential for several people"])
        self.assertIn("1 distinct credential id(s) for 3 people", shared[0]["said"])
        pending = {"invites": [dict(register["invites"][0], state="pending")]}
        self.assertEqual([f["probe"] for f in H.audit_people(pending, minted, {"ada": "cred-b"})], ["people register: the invitation of Ada Approver (state)"])
        absent = {"invites": []}
        self.assertEqual([f["probe"] for f in H.audit_people(absent, minted, {})], ["people register: the invitation of Ada Approver"])

    def test_the_payees_register_against_what_ada_approved(self):
        created = [{"key": "NORTHWIND_ETHEREUM", "name": "Northwind Supplies", "address": T.address("NORTHWIND_ETHEREUM"), "approved": {"whitelistStatus": "whitelisted"}}]
        register = {"payees": [{"displayName": "Northwind Supplies", "addresses": [{"address": T.address("NORTHWIND_ETHEREUM").lower(), "whitelistStatus": "whitelisted"}]}]}
        self.assertEqual(H.audit_payees(register, created, fixture_charter("wallet_account")), [])
        stale = {"payees": [{"displayName": "Northwind Supplies", "addresses": [{"address": T.address("NORTHWIND_ETHEREUM").lower(), "whitelistStatus": "pending_promotion"}]}]}
        findings = H.audit_payees(stale, created, None)
        self.assertEqual([f["said"] for f in findings], ["the register says pending_promotion"])
        listed = dict(fixture_charter("wallet_account"), whitelistEntries=[{"chain": "ethereum", "address": T.address("CONTOSO_ETHEREUM"), "label": "Contoso Legal"}])
        self.assertEqual([f["probe"] for f in H.audit_payees(register, created, listed)], ["payees register against the charter's list"])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheAttackerAgainstTheDouble(unittest.TestCase):
    """Each S11 probe against the double that answers as guards.ts and the interview do."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble()
        cls.tmp = tempfile.mkdtemp()
        cls.link = cls.double.mint_founder_link()
        cls.said = []
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.link, said=cls.said)
        cls.outcomes = {o.station: o for o in cls.runner.run()}
        cls.steps = cls.runner.evidence["S11"]

    def step(self, probe_fragment):
        found = [s for s in self.steps if probe_fragment in str(s.get("probe", ""))]
        self.assertTrue(found, probe_fragment)
        return found[-1]

    def test_the_csrf_probe_is_refused_in_the_guards_words(self):
        step = self.step("without the x-csrf-token header")
        self.assertEqual(step["status"], 401)
        self.assertIn("missing or incorrect CSRF token", step["came_back"])
        self.assertNotIn(H.CSRF_HEADER, json.dumps(step["sent"]))

    def test_the_second_session_probe_is_refused_by_name(self):
        step = self.step("Ben confirms the policy interview with the founder's passkey")
        self.assertEqual(step["status"], 409)
        self.assertIn("INTERVIEW_NOT_OPEN", step["came_back"])
        self.assertEqual(step["who"], "Ben Signatory")

    def test_the_viewer_is_refused_at_every_author_route_in_the_room_sentence(self):
        for route in ("POST /v1/payees", "POST /v1/sets", "POST /v1/invites", "/answers"):
            step = self.step("a viewer's session at an author route: %s" % route if not route.startswith("/") else route)
            self.assertEqual(step["status"], 403, route)
            self.assertIn("You are signed into Harness Holdings Pty Ltd as a viewer. This action needs an author", step["came_back"])
            self.assertEqual(step["who"], "Olive Overseer")

    def test_the_principal_invitation_is_refused_by_name(self):
        step = self.step("an invitation for the principal role")
        self.assertEqual(step["status"], 422)
        self.assertIn("INVITE_ROLE_NOT_AVAILABLE", step["came_back"])
        self.assertIn("the principal road", step["came_back"])

    def test_the_interview_probes(self):
        unserved = self.step("did not serve")
        self.assertEqual(unserved["status"], 400)
        self.assertIn("this question is not asked given the answers so far", unserved["came_back"])
        compile_first = self.step("a compile before confirm")
        self.assertEqual(compile_first["status"], 409)
        self.assertIn("the compiler reads only confirmed interviews", compile_first["came_back"])
        wrong_kind = self.step("an answer of the wrong kind")
        self.assertEqual(wrong_kind["status"], 400)
        self.assertIn("an amount is a whole number of cents", wrong_kind["came_back"])
        self.assertEqual(wrong_kind["sent"], {"questionId": "O1", "value": {"cents": "fifty thousand dollars"}})
        second = [s for s in self.steps if str(s.get("probe", "")) == "a second confirm of an already confirmed interview (the policy interview)"][-1]
        self.assertEqual(second["status"], 409)
        self.assertIn("confirm happens at the read-back", second["came_back"])

    def test_the_passkey_probes(self):
        replay = [s for s in self.steps if str(s.get("probe", "")) == "a passkey assertion replayed with a challenge already used"][-1]
        self.assertEqual(replay["status"], 403)
        self.assertIn("challenge already used", replay["came_back"])
        wrong = self.step("an assertion signed for the wrong rpId")
        self.assertEqual(wrong["status"], 403)
        self.assertIn("Unexpected RP ID hash", wrong["came_back"])

    def test_the_checksum_probe_is_a_finding_and_the_venue_probe_is_accepted_as_the_law_says(self):
        checksum = self.step("a payee address with a wrong checksum")
        self.assertEqual(checksum["status"], 201)
        self.assertEqual(checksum["sent"]["addresses"][0]["address"], T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM")))
        venue = self.step("a real venue contract")
        self.assertEqual(venue["status"], 201)
        self.assertEqual(venue["sent"]["addresses"][0]["address"], T.venue_address_for_probe()["address"])
        self.assertEqual(venue["expected"], "HTTP 201: accepted, as the law says (%s)" % H.VENUE_RULING)
        self.assertEqual(venue["result"], "accepted, as the law says (Bear, 20 September 2026: unless the questionnaire stipulates otherwise, an address is accepted)")
        findings = {f.probe: f for f in self.runner.findings if f.station == "S11"}
        self.assertIn("a payee address with a wrong checksum", findings)
        self.assertTrue(findings["a payee address with a wrong checksum"].said.startswith("ACCEPTED: HTTP 201"))
        self.assertFalse(any("venue contract" in probe for probe in findings), "accepted is what the law says; the venue is a finding only if refused")
        self.assertTrue(any(l.startswith("  S11 — accepted, as the law says — a payee address that is a real venue contract") and l.endswith(": HTTP 201") for l in self.said))

    def test_the_clerks_own_approval_is_recorded_as_the_estate_answered_it(self):
        step = self.step("the clerk approving her own payment")
        self.assertEqual(step["who"], "Cora Clerk")
        self.assertEqual(step["status"], 200, "one credential worn by four people: the charter's Yes lets the clerk release her own run")
        finding = next(f for f in self.runner.findings if f.probe == "the clerk approving her own payment (S7's P3)")
        self.assertIn("ACCEPTED", finding.said)
        self.assertTrue(finding.route.startswith("POST /v1/approvals/"))

    def test_findings_are_printed_in_the_failure_form_with_the_probe(self):
        lines = [l for l in self.said if l.startswith("S11 — fail — ") and ": ACCEPTED: " in l]
        self.assertEqual(len(lines), 2, "the wrong checksum and the clerk's own approval; the venue is accepted, as the law says")
        self.assertIn("S11 — fail — the attacker: 17 probe(s), 2 finding(s)", self.said)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheAttackerAgainstADoubleThatRefusesTheVenue(unittest.TestCase):
    """The day the questionnaire stipulates against venue contracts the estate refuses; until the harness is told the law changed, that refusal is the finding, with the ruling quoted."""

    def test_a_refusal_of_the_venue_probe_is_a_finding_with_the_ruling_quoted(self):
        double = EstateDouble(refuses_venue_contract=True)
        said = []
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link(), said=said)
        outcomes = {o.station: o for o in runner.run()}
        finding = next(f for f in runner.findings if f.station == "S11" and "a real venue contract" in f.probe)
        self.assertTrue(finding.said.startswith("REFUSED: ADDRESS_PROPOSAL_REFUSED: %s" % VENUE_STIPULATION), finding.said)
        self.assertIn("the law says otherwise (%s; a contract is an address)" % H.VENUE_RULING, finding.said)
        self.assertEqual(finding.expected, "HTTP 201: accepted, as the law says (%s)" % H.VENUE_RULING)
        self.assertEqual(finding.route, "POST /v1/payees")
        self.assertTrue(finding.came_back.startswith("HTTP 422 — "), finding.came_back)
        self.assertIn("this double stands in for the day it does", finding.came_back, "the estate's own words travel with the finding")
        self.assertIn("17 probe(s), 3 finding(s)", outcomes["S11"].line)
        step = [s for s in runner.evidence["S11"] if "a real venue contract" in str(s.get("probe", ""))][-1]
        self.assertEqual(step["status"], 422)
        self.assertTrue(step["result"].startswith("refused: ADDRESS_PROPOSAL_REFUSED: "), step["result"])
        self.assertTrue(any(l.startswith("S11 — fail — a payee address that is a real venue contract") and "REFUSED: ADDRESS_PROPOSAL_REFUSED" in l for l in said))
        report = runner.report()
        self.assertIn("- **a payee address that is a real venue contract (Uniswap v3 SwapRouter02 on Ethereum, read from the corridor's tables.py at run time)** — REFUSED: ADDRESS_PROPOSAL_REFUSED", report)
        self.assertIn("Bear, 20 September 2026", report)


class TheOptimizerOnARecordedLog(unittest.TestCase):
    def call(self, station, method, path, ms, size=10, status=200, retry_of=None):
        return H.Call(station, "x", method, path, None, H.Answer(method, path, status, {}, "x" * size, ms), "now", retry_of)

    def test_the_measures(self):
        calls = [self.call("S3", "POST", "/v1/onboarding/interviews", 50), self.call("S3", "GET", "/v1/onboarding/interviews/i/readback", 2500),
                 self.call("S3", "GET", "/v1/onboarding/interviews/i/readback", 30), self.call("S7", "POST", "/v1/sets", 3100, size=4000)]
        first = self.call("S6", "POST", "/v1/payees", 90, status=502)
        calls.append(first)
        calls.append(self.call("S6", "POST", "/v1/payees", 95, status=201, retry_of=first))
        measure = H.optimizer_measures(calls, {"policy": ["A1"], "wallet_account": []})
        self.assertEqual(measure["calls"], 6)
        self.assertEqual([c.route for c in measure["slow"]], ["GET /v1/onboarding/interviews/i/readback", "POST /v1/sets"])
        self.assertEqual(measure["slowest"][0].route, "POST /v1/sets")
        self.assertEqual(measure["largest"], {"route": "POST /v1/sets", "size": 4000})
        self.assertEqual(len(measure["retried"]), 1)
        self.assertEqual(measure["interview_calls"], 3)
        self.assertEqual(measure["wasted_reads"], 2, "one read-back fetched twice, one question served twice")
        text = "\n".join(measure["lines"])
        self.assertIn("2 over 2 seconds", text)
        self.assertIn("POST /v1/payees (502 then 201)", text)
        self.assertIn("the ten slowest:", text)

    def test_a_slow_invitation_is_reported_with_where_its_seconds_go_and_never_judged(self):
        calls = [self.call("S4", "POST", "/v1/invites", 4097, status=201), self.call("S4", "POST", "/v1/invites", 3686, status=201),
                 self.call("S11", "POST", "/v1/invites", 4140, status=201), self.call("S2", "GET", "/v1/journey", 1007)]
        measure = H.optimizer_measures(calls, {"policy": [], "wallet_account": []})
        self.assertEqual([c.elapsed_ms for c in measure["slow_invitations"]], [4097, 3686, 4140])
        text = "\n".join(measure["lines"])
        self.assertIn("3 over 2 seconds", text)
        self.assertIn("every call over 2 seconds, reported and not judged: POST /v1/invites 4097 ms (S4), POST /v1/invites 3686 ms (S4), POST /v1/invites 4140 ms (S11)", text)
        self.assertIn("%s — 4097 ms (S4), 3686 ms (S4), 4140 ms (S11) (routes/invites.ts:" % H.INVITATION_SENDS_FIRST, text)
        self.assertEqual(H.INVITATION_SENDS_FIRST, "the invitation road sends the email before it answers, which is where its four seconds go")
        quiet = H.optimizer_measures([self.call("S2", "GET", "/v1/journey", 1007)], {"policy": [], "wallet_account": []})
        self.assertNotIn(H.INVITATION_SENDS_FIRST, "\n".join(quiet["lines"]))
        self.assertEqual(quiet["slow_invitations"], [])
        other = H.optimizer_measures([self.call("S7", "POST", "/v1/sets", 2500)], {"policy": [], "wallet_account": []})
        self.assertNotIn(H.INVITATION_SENDS_FIRST, "\n".join(other["lines"]), "the sentence is the invitation road's, not every slow call's")
        self.assertIn("every call over 2 seconds, reported and not judged: POST /v1/sets 2500 ms (S7)", "\n".join(other["lines"]))

    @unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
    def test_a_run_with_four_second_invitations_passes_s12_and_the_report_carries_the_sentence(self):
        clock = Clock()
        double = EstateDouble(invite_seconds=4.0, clock=clock)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link(), clock=clock)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S12"].outcome, H.PASS, outcomes["S12"].line)
        self.assertIn("4 over 2 seconds", outcomes["S12"].line, "three authors in S4 and the viewer in S11, as in the live run; the principal probe is refused before the email")
        self.assertEqual([c.route for c in runner.facts["optimizer"]["slow"]], ["POST /v1/invites"] * 4)
        self.assertEqual([f for f in runner.findings if f.station == "S12"], [])
        report = runner.report()
        s12 = report.split("## S12 — The optimizer", 1)[1].split("## Every call", 1)[0]
        self.assertIn("Outcome: **pass**.", s12)
        self.assertIn("- every call over 2 seconds, reported and not judged: POST /v1/invites 4000 ms (S4), POST /v1/invites 4000 ms (S4), POST /v1/invites 4000 ms (S4), POST /v1/invites 4000 ms (S11)", s12)
        self.assertIn("- %s — 4000 ms (S4), 4000 ms (S4), 4000 ms (S4), 4000 ms (S11) (routes/invites.ts: the invitation is minted, the email's dispatch is awaited, the row is stamped, and only then does the route answer 201)" % H.INVITATION_SENDS_FIRST, s12)
        self.assertNotIn(H.INVITATION_SENDS_FIRST, report.split("## S12 — The optimizer", 1)[0].split("## S1 — Enrol", 1)[1], "the sentence sits beside the timings, in S12")

    def test_a_5xx_is_retried_once_after_two_seconds_and_both_answers_are_kept(self):
        answers = iter([(503, [("Content-Type", "application/json")], json.dumps({"error": {"code": "AAP_UNREACHABLE", "message": "The access platform could not be reached…"}})),
                        (200, [("Content-Type", "application/json")], json.dumps({"ok": True}))])
        slept = []

        def transport(request):
            return next(answers)
        runner = H.Runner("https://estate.test", tempfile.mkdtemp(), None, False, None, ".", transport=transport, say=lambda s: None, sleep=slept.append)
        answer = runner.request(None, "GET", "/v1/journey", None, "S2")
        self.assertEqual(answer.status, 200)
        self.assertEqual(slept, [H.RETRY_AFTER_5XX_SECONDS])
        self.assertEqual([c.status for c in runner.calls], [503, 200])
        self.assertIs(runner.calls[1].retry_of, runner.calls[0])
        with self.assertRaises(StopIteration):
            next(answers)


# A report in Spec T7's shape — three columns, no last-run column — cut down to what the reader of a previous
# report needs: the title line, the closing table, the findings under their stations, the calls.
T7_REPORT = """# AER 360 estate harness run — Harness Holdings Pty Ltd — 2026-09-20T09:23:37.995+10:00

Spec T7, 19 September 2026. Base URL https://accounts.aeredium.io.

## The closing table

| Station | Outcome | Line |
|---|---|---|
| S1 Enrol | pass | enrolled by invitation as Harriet Founder; session in Harness Holdings Pty Ltd (sandbox), roles author, viewer, credential …ddb1 |
| S2 Journey | pass | journey: stage 1 of 7, policy_interview; road wizard, landing /onboarding |
| S3 Policy Interview | pass | policy interview: 21 questions answered |
| S4 People | pass | people: Ada Approver enrolled as author, seat on redemption: {"charterNamedThem": true, "granted": true, "note": null} |
| S5 Wallet account | pass | wallet account: 14 questions answered |
| S6 Payees | fail | payees: Northwind Supplies: created; promote status proposed; Ada's approval answered INTERNAL_ERROR: Something went wrong at our end. Nothing was changed. |
| S7 Payments | fail | payments as Cora Clerk: P1 (1250.00, expected to proceeds to approval): refused at creation — GAS_PREFLIGHT_UNAVAILABLE \\| a pipe in a line |
| S8 Journey and readiness | pass | journey stage 3 of 7 (working_the_sandbox) |
| S9 The tour | out of scope | the tour's answers as Claude would see them are out of scope: the harness is the founder, not Claude |
| S10 The auditor | fail | the auditor: 7 finding(s); 16 refusal(s) met in S1 to S9 checked for Rule 13; 93 call(s) checked for the minor-unit law |
| S11 The attacker | fail | the attacker: 17 probe(s), 2 finding(s) |
| S12 The optimizer | pass | the optimizer: 123 call(s), 4 over 2 seconds, largest answer 6853 bytes, 8 retried after a 5xx |

Findings under S10 and S11: 9.

## S1 — Enrol

Outcome: **pass**. enrolled by invitation as Harriet Founder

### Evidence, call by call

1. POST /v1/auth/invite/options — Harriet Founder
   - Expected: 200 with options (rp.id, challenge, user.id) and the invitee's displayName
   - Result: answered (HTTP 200, 919 ms)

## S10 — The auditor

Outcome: **fail**. the auditor: 7 finding(s)

### Findings

- **read-back (policy) of A5** — the read-back says '{"text":"AUD"}'
  - Sent: `{"text": "AUD"}`
  - Expected: AUD

- **read-back (policy) of A8** — the read-back says 'Harriet Founder — Authorise payments — harness+harriet@aeredium.io'
  - Expected: Harriet Founder — harness+harriet@aeredium.io — Authorise payments

- **people register: one credential for several people** — the sessions carry 1 distinct credential id(s) for 4 people: {"…ddb1": ["Harriet Founder", "Ada Approver", "Ben Signatory", "Cora Clerk"]}
  - Expected: one credential id per person, so the register and every approval can tell them apart

- **Rule 13 at POST /v1/payees/addresses/3fe7e203-924c-45fe-9940-d136c63c5316/approve (S6)** — INTERNAL_ERROR: the sentence this house says when it has no words
  - Sent: `{}`

## S11 — The attacker

Outcome: **fail**. the attacker: 17 probe(s), 2 finding(s)

Note: probe not made (the clerk approving her own payment (S7's P3)): S7 left no submitted run for P3

### Findings

- **a payee address with a wrong checksum** — ACCEPTED: HTTP 201
  - Route: POST /v1/payees

- **a payee address that is a real venue contract (Uniswap v3 SwapRouter02 on Ethereum, read from the corridor's tables.py at run time)** — ACCEPTED: HTTP 201
  - Route: POST /v1/payees

## S12 — The optimizer

Outcome: **pass**. the optimizer: 123 call(s), 4 over 2 seconds

- 123 call(s) in all; 4 over 2 seconds
- the ten slowest: POST /v1/invites 4140 ms (S11), POST /v1/invites 4097 ms (S4)

## Every call

| At | Station | Who | Route | Status | ms | Bytes |
|---|---|---|---|---|---|---|
| 2026-09-20T09:23:38.915+10:00 | S1 | Harriet Founder | POST /v1/auth/invite/options | 200 | 919 | 677 |
"""


class TheLastRunColumn(unittest.TestCase):
    """When a previous report exists in the working folder, the closing table says each finding's fate: closed, still open, new (Spec T8)."""

    def test_a_spec_t7_report_is_read_back_and_the_ids_a_run_mints_are_set_aside(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "aer360-harness-2026-09-20.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(T7_REPORT)
        report = H.read_report(path)
        self.assertEqual(report["name"], "aer360-harness-2026-09-20.md")
        self.assertEqual(report["started_at"], "2026-09-20T09:23:37.995+10:00")
        self.assertEqual(len(report["outcomes"]), 12)
        self.assertEqual(report["outcomes"]["S6"], "fail")
        self.assertEqual(report["outcomes"]["S7"], "fail")
        self.assertEqual(report["outcomes"]["S9"], "out of scope")
        self.assertEqual(report["outcomes"]["S12"], "pass")
        self.assertEqual([(f["station"], f["probe"]) for f in report["findings"]], [
            ("S10", "read-back (policy) of A5"),
            ("S10", "read-back (policy) of A8"),
            ("S10", "people register: one credential for several people"),
            ("S10", "Rule 13 at POST /v1/payees/addresses/3fe7e203-924c-45fe-9940-d136c63c5316/approve (S6)"),
            ("S11", "a payee address with a wrong checksum"),
            ("S11", "a payee address that is a real venue contract (Uniswap v3 SwapRouter02 on Ethereum, read from the corridor's tables.py at run time)"),
        ])
        self.assertEqual(report["findings"][0]["said"], "the read-back says '{\"text\":\"AUD\"}'")
        self.assertEqual(H.finding_key("Rule 13 at POST /v1/payees/addresses/3fe7e203-924c-45fe-9940-d136c63c5316/approve (S6)"),
                         "Rule 13 at POST /v1/payees/addresses/<id>/approve (S6)")
        self.assertEqual(H.finding_key("Rule 13 at POST /v1/payees/addresses/addr-1a2b3c4d5e6f/approve (S6)"), "Rule 13 at POST /v1/payees/addresses/<id>/approve (S6)")
        self.assertEqual(H.finding_key("a viewer's session at an author route: POST /v1/onboarding/interviews/0be95dd1-4d22-45c7-b095-04102ce8e5c6/answers"),
                         "a viewer's session at an author route: POST /v1/onboarding/interviews/<id>/answers")
        self.assertEqual(H.finding_key("read-back (policy) of A8"), "read-back (policy) of A8")
        self.assertEqual(H.finding_key("a payee address with a wrong checksum"), "a payee address with a wrong checksum")
        # the fates: closed, still open, new — matched by station and probe, the ids set aside
        now = [H.Finding("S10", "people register: one credential for several people", None, "", "", ""),
               H.Finding("S10", "Rule 13 at POST /v1/payees/addresses/addr-9f9f9f9f9f9f/approve (S6)", None, "", "", ""),
               H.Finding("S11", "a payee address with a wrong checksum", None, "", "", ""),
               H.Finding("S11", "the clerk approving her own payment (S7's P3)", None, "", "", "")]
        fates = H.compare_findings(report["findings"], now)
        self.assertEqual([f["probe"] for f in fates["closed"]], ["read-back (policy) of A5", "read-back (policy) of A8",
                                                                 "a payee address that is a real venue contract (Uniswap v3 SwapRouter02 on Ethereum, read from the corridor's tables.py at run time)"])
        self.assertEqual([f["probe"] for f in fates["still_open"]], ["people register: one credential for several people",
                                                                     "Rule 13 at POST /v1/payees/addresses/addr-9f9f9f9f9f9f/approve (S6)", "a payee address with a wrong checksum"])
        self.assertEqual([f["probe"] for f in fates["new"]], ["the clerk approving her own payment (S7's P3)"])
        # the newest report is the last run; the bare date is the first of its day; a run is never its own last run
        later = os.path.join(tmp, "aer360-harness-2026-09-20-101010.md")
        with open(later, "w", encoding="utf-8") as handle:
            handle.write(T7_REPORT.replace("2026-09-20T09:23:37.995+10:00", "2026-09-20T10:10:10.000+10:00"))
        self.assertEqual(H.find_last_report(tmp)["name"], "aer360-harness-2026-09-20-101010.md")
        self.assertEqual(H.find_last_report(tmp, own_started_at="2026-09-20T10:10:10.000+10:00")["name"], "aer360-harness-2026-09-20.md")
        earlier_day = os.path.join(tmp, "aer360-harness-2026-09-19-235959.md")
        with open(earlier_day, "w", encoding="utf-8") as handle:
            handle.write(T7_REPORT)
        self.assertEqual(H.find_last_report(tmp)["name"], "aer360-harness-2026-09-20-101010.md")
        with open(os.path.join(tmp, "notes.md"), "w", encoding="utf-8") as handle:
            handle.write("# not a report\n")
        self.assertEqual(H.find_last_report(tmp)["name"], "aer360-harness-2026-09-20-101010.md")
        self.assertIsNone(H.find_last_report(os.path.join(tmp, "nowhere")))
        self.assertIsNone(H.find_last_report(tempfile.mkdtemp()))

    @unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
    def test_a_first_report_has_no_last_run_column(self):
        double = EstateDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        runner.run()
        path = runner.write_report()
        with open(path, "r", encoding="utf-8") as handle:
            report = handle.read()
        self.assertIn("| Station | Outcome | Line |", report)
        self.assertNotIn("Last run", report)
        self.assertNotIn("Since the last run", report)
        self.assertIsNone(runner.last_run())

    @unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
    def test_two_reports_in_the_folder_give_the_closing_table_its_last_run_column_with_closed_still_open_and_new(self):
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, "out")
        # the first run: the estate as main is today — the currency read back as JSON, the venue contract accepted
        first_double = EstateDouble()
        first = H.Runner(first_double.base, os.path.join(tmp, "store-1"), first_double.mint_founder_link(), False, None, out, transport=first_double, say=lambda s: None, sleep=lambda s: None)
        first.run()
        first_path = first.write_report()
        self.assertEqual([(f.station, f.probe) for f in first.findings], [
            ("S10", "read-back (policy) of A5"),
            ("S10", "people register: one credential for several people"),
            ("S11", "a payee address with a wrong checksum"),
            ("S11", "the clerk approving her own payment (S7's P3)"),
        ])
        # the rerun after a fix: Spec 88 has landed, so the currency is read back as its code; and the questionnaire
        # has gained a stipulation against venue contracts, which the harness has not yet been told is the law
        second_double = EstateDouble(currency_spoken_as_code=True, refuses_venue_contract=True)
        second = H.Runner(second_double.base, os.path.join(tmp, "store-2"), second_double.mint_founder_link(), False, None, out, transport=second_double, say=lambda s: None, sleep=lambda s: None)
        second.run()
        second_path = second.write_report()
        self.assertNotEqual(first_path, second_path)
        self.assertEqual(second.last_run()["name"], os.path.basename(first_path))
        with open(second_path, "r", encoding="utf-8") as handle:
            report = handle.read()
        self.assertIn("| Station | Outcome | Last run | Line |", report)
        self.assertIn("|---|---|---|---|", report)
        table = report.split("## The closing table", 1)[1].split("Findings under S10 and S11", 1)[0]
        rows = {line.split(" ", 2)[1]: line for line in table.splitlines() if re.match(r"^\| S\d+ ", line)}
        self.assertEqual(len(rows), 12)
        self.assertIn("| S1 Enrol | pass | last run pass | ", rows["S1"])
        self.assertIn("| S9 The tour | out of scope | last run out of scope | ", rows["S9"])
        self.assertIn("| S10 The auditor | fail | last run fail · 1 closed: read-back (policy) of A5 · 1 still open: people register: one credential for several people | ", rows["S10"])
        self.assertIn("| S11 The attacker | fail | last run fail · 2 still open: a payee address with a wrong checksum; the clerk approving her own payment (S7's P3) · "
                      "1 new: a payee address that is a real venue contract (Uniswap v3 SwapRouter02 on Ethereum, read from the corridor's tables.py at run time) | ", rows["S11"])
        self.assertIn("| S12 The optimizer | pass | last run pass | ", rows["S12"])
        since = report.split("Since the last run (", 1)[1]
        self.assertTrue(since.startswith("%s, started %s): 1 closed, 3 still open, 1 new." % (os.path.basename(first_path), first.started_at)), since[:240])
        self.assertIn("- closed — S10 — read-back (policy) of A5", report)
        self.assertIn("- still open — S10 — people register: one credential for several people", report)
        self.assertIn("- still open — S11 — a payee address with a wrong checksum", report)
        self.assertIn("- still open — S11 — the clerk approving her own payment (S7's P3)", report)
        self.assertIn("- new — S11 — a payee address that is a real venue contract", report)
        self.assertNotIn("- closed — S11", report)
        # a third run against today's estate again: the venue finding closes, the currency finding is new once more
        third_double = EstateDouble()
        third = H.Runner(third_double.base, os.path.join(tmp, "store-3"), third_double.mint_founder_link(), False, None, out, transport=third_double, say=lambda s: None, sleep=lambda s: None)
        third.run()
        third_report = third.report()
        self.assertEqual(third.last_run()["name"], os.path.basename(second_path))
        self.assertIn("- closed — S11 — a payee address that is a real venue contract", third_report)
        self.assertIn("- new — S10 — read-back (policy) of A5", third_report)


if __name__ == "__main__":
    unittest.main()
