"""
The three hats (Spec T7): the S10 comparisons are tested on a fixture charter with one planted
disagreement; each S11 probe has a test against the local double that answers as routes/guards.ts
and the interview do; the S12 measures are read off a recorded call log.
"""
import copy
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import EstateDouble, runner_on  # noqa: E402


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
        self.assertEqual(H.spoken_for("percent", "T4", {"percent": None}), "Left empty — never halts on pace.")
        self.assertEqual(H.spoken_for("percent", "X5", {"percent": 2.5}), "2.5 per cent.")
        self.assertEqual(H.spoken_for("roster_multi", "C11", {"people": []}), "No one chosen.")
        self.assertEqual(H.spoken_for("text", "A4", {"text": "  "}), "Left blank.")
        self.assertEqual(H.spoken_for("count", "C14N", {"count": 1}), "1 payment in a day.")

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

    def test_the_address_probes_record_the_estates_acceptance_as_findings(self):
        checksum = self.step("a payee address with a wrong checksum")
        self.assertEqual(checksum["status"], 201)
        self.assertEqual(checksum["sent"]["addresses"][0]["address"], T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM")))
        venue = self.step("a real venue contract")
        self.assertEqual(venue["status"], 201)
        self.assertEqual(venue["sent"]["addresses"][0]["address"], T.venue_address_for_probe()["address"])
        findings = {f.probe: f for f in self.runner.findings if f.station == "S11"}
        self.assertIn("a payee address with a wrong checksum", findings)
        self.assertTrue(findings["a payee address with a wrong checksum"].said.startswith("ACCEPTED: HTTP 201"))

    def test_the_clerks_own_approval_is_recorded_as_the_estate_answered_it(self):
        step = self.step("the clerk approving her own payment")
        self.assertEqual(step["who"], "Cora Clerk")
        self.assertEqual(step["status"], 200, "one credential worn by four people: the charter's Yes lets the clerk release her own run")
        finding = next(f for f in self.runner.findings if f.probe == "the clerk approving her own payment (S7's P3)")
        self.assertIn("ACCEPTED", finding.said)
        self.assertTrue(finding.route.startswith("POST /v1/approvals/"))

    def test_findings_are_printed_in_the_failure_form_with_the_probe(self):
        lines = [l for l in self.said if l.startswith("S11 — fail — ") and ": ACCEPTED: " in l]
        self.assertEqual(len(lines), 3)
        self.assertIn("S11 — fail — the attacker: 17 probe(s), 3 finding(s)", self.said)


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


if __name__ == "__main__":
    unittest.main()
