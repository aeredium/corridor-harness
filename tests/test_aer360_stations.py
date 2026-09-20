"""
The founder's road, S1 to S9, walked against the estate double (Spec T7): the enrolment, the
journey, the Policy Interview answered from the book to its compile, the people, the wallet
account, the payees, the payments and Ada's approval, the journey and readiness; then the three
hats on what the double said, the report, and a run resumed with the stored passkeys.
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
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import EstateDouble, runner_on  # noqa: E402


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheFoundersRoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble()
        cls.tmp = tempfile.mkdtemp()
        cls.link = cls.double.mint_founder_link()
        cls.said = []
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.link, said=cls.said)
        cls.outcomes = {o.station: o for o in cls.runner.run()}
        cls.report_path = cls.runner.write_report()
        with open(cls.report_path, "r", encoding="utf-8") as handle:
            cls.report = handle.read()

    def test_s1_enrols_the_founder_by_invitation_into_the_named_workspace(self):
        o = self.outcomes["S1"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("enrolled by invitation as Harriet Founder", o.line)
        self.assertIn("session in Harness Holdings Pty Ltd (sandbox)", o.line)
        self.assertTrue(os.path.exists(self.runner.key_path(self.runner.people["harriet"])))

    def test_s2_names_stage_one_of_seven(self):
        o = self.outcomes["S2"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("stage 1 of 7, policy_interview", o.line)

    def test_s3_answers_every_question_the_estate_serves_and_compiles_the_charter(self):
        o = self.outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("policy interview: 21 questions answered", o.line)
        self.assertIn("charter compiled (Harness Holdings Pty Ltd; quorum 1", o.line)
        self.assertIn("journey stage 2 of 7", o.line)
        given = [q for q, _, _, _ in self.runner.facts["answers"]["policy"]]
        self.assertEqual(given, [q.id for q in A.expected_walk("policy")], "the estate served the questions the book expected, in order")
        self.assertEqual(self.runner.facts["charter"]["policy"]["allowedChains"], ["aeredium-testnet"])
        self.assertEqual(self.runner.facts["charter"]["policy"]["recordedChains"], ["aeredium", "ethereum"])
        self.assertEqual(self.runner.facts["charter_standing"], {"standsWritten": True, "inForceSince": self.runner.facts["compile"]["policy"]["receipt"]["completedAt"]})

    def test_s4_brings_in_the_three_authors_and_seats_ada(self):
        o = self.outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            self.assertTrue(person.signed_in, key)
            self.assertIn("author", person.roles)
            self.assertIn("%s enrolled as author" % person.name, o.line)
        self.assertIn("Ada's seat", o.line)
        seats = self.runner.facts["seats"]
        ada_seat = next(s for s in seats["seats"] if s["email"] == A.PEOPLE["ada"].email)
        self.assertEqual(ada_seat["state"], "seated", "the invitation completed the seat the charter named")
        self.assertIn("approver", self.runner.people["ada"].roles)
        self.assertEqual(len(self.runner.facts["invites_register"]["invites"]), 4, "the founder's birth invitation and three authors")

    def test_s5_opens_the_operating_account_and_moves_the_journey_to_stage_three(self):
        o = self.outcomes["S5"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("wallet account: 14 questions answered", o.line)
        self.assertIn("charter compiled (Operating account, purpose Operations — day-to-day business payments, per payment hold 1000000 cents, daily 5000000 cents, destinations hold_non_listed)", o.line)
        self.assertIn("journey stage 3 of 7 (working_the_sandbox)", o.line)
        self.assertIn("No daily close has completed yet", o.line)

    def test_s6_presses_to_the_quorum_and_whitelists_both_payees(self):
        """Spec T9: two presses per payee — Ada, then the next roster member the answer names (Ben) — and the line of §3."""
        o = self.outcomes["S6"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        # the station's line names each payee's presses in order (Spec T9 §3), verbatim
        self.assertIn("Northwind Supplies: created; promoted; approved by Ada Approver (1 of 2), by Ben Signatory (2 of 2): whitelisted", o.line)
        self.assertIn("Contoso Legal: created; promoted; approved by Ada Approver (1 of 2), by Ben Signatory (2 of 2): whitelisted", o.line)
        self.assertIn("register: Northwind Supplies whitelisted, Contoso Legal whitelisted", o.line)
        for record in self.runner.facts["payees"]:
            self.assertEqual(record["approved"], {"whitelistStatus": "whitelisted"}, "the last press answered whitelisted")
            self.assertEqual([p["who"] for p in record["presses"]], ["Ada Approver", "Ben Signatory"])
            first = record["presses"][0]["answer"]
            # the first approval's answer says why it is still pending (Spec 89)
            self.assertEqual(first["whitelistStatus"], "pending_promotion")
            self.assertEqual(first["approvals"], {"required": 2, "collected": 1, "remaining": 1})
            self.assertEqual(first["may_still_approve"], ["Harriet Founder", "Ben Signatory", "Cora Clerk"])
            self.assertEqual(first["sentence"],
                             "1 of 2 approvals recorded for this address. One more is needed, from Harriet Founder, Ben Signatory or Cora Clerk. "
                             "The address is not payable until then.")
        # the run reads the register by this run's payee ids, not by address
        self.assertTrue(all(r.get("register_status") == "whitelisted" for r in self.runner.facts["payees"]))
        # no finding was raised in S6: the estate said why, at a quorum its roster can meet
        self.assertEqual([f for f in self.runner.findings if f.station == "S6"], [])

    def test_s7_makes_the_three_payments_as_the_clerk_and_reads_each_state_against_its_expectation(self):
        o = self.outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertTrue(o.line.startswith("payments as Cora Clerk:"))
        self.assertIn("P1 (1250.00 USDC, expected to proceeds to approval): created and submitted; status approved, approvalsRequired 0", o.line)
        self.assertIn("P2 (4999.99 USDC, expected to waits): the run waits for approval: status pending_approval, approvalsRequired 1", o.line)
        self.assertIn("P3 (12000.00 USDC, expected to held): the run waits for approval: status pending_approval, approvalsRequired 1", o.line)
        self.assertIn("Ada's approval of P1 was not asked: the run stands approved", o.line)
        sets = self.runner.facts["sets"]
        self.assertEqual(sets["P2"]["view"]["set"]["instructions"][0]["isOneOff"], True)
        self.assertEqual(sets["P3"]["view"]["set"]["approval"]["bandThresholdBaseMinor"], A.MONEY["per_payment_cents"])

    def test_s8_prints_the_journey_and_the_readiness(self):
        o = self.outcomes["S8"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("journey stage 4 of 7 (acceptance_rehearsal)", o.line)
        self.assertIn("done: policy_interview, first_wallet_account, working_the_sandbox", o.line)
        self.assertIn("readiness: transactable True", o.line)

    def test_s9_is_out_of_scope(self):
        self.assertEqual(self.outcomes["S9"].outcome, H.OUT_OF_SCOPE)

    def test_s10_finds_mains_json_currency_and_the_one_credential_four_people_share_and_nothing_else(self):
        o = self.outcomes["S10"]
        findings = [f for f in self.runner.findings if f.station == "S10"]
        self.assertEqual([f.probe for f in findings], ["read-back (policy) of A5", "people register: one credential for several people"], o.line)
        self.assertEqual(findings[0].expected, "AUD", "a currency is read back as its code (Spec 88); main's default arm speaks JSON, which is the estate's finding")
        self.assertEqual(findings[0].said, "the read-back says '{\"text\":\"AUD\"}'")
        self.assertIn("4 people", findings[1].said)
        self.assertEqual(o.outcome, H.FAIL)
        self.assertIn("2 finding(s)", o.line)
        # the census the double speaks as jsonb stores it — name — role — email — against the book's name, email, role: no finding (Spec T8)
        a8 = next(l for l in self.runner.facts["readback"]["policy"]["lines"] if l["questionId"] == "A8")
        self.assertTrue(a8["spoken"].startswith("Harriet Founder — Authorise payments — harness+harriet@aeredium.io; "), a8["spoken"])
        self.assertFalse(any(f.probe.startswith("read-back (policy) of A8") for f in findings))
        self.assertFalse(any("not compared" in n for n in self.runner.notes["S10"]), "every kind the catalog serves has a rendering")

    def test_s11_finds_the_acceptances_the_code_makes_and_nothing_else(self):
        o = self.outcomes["S11"]
        findings = [f for f in self.runner.findings if f.station == "S11"]
        probes = [f.probe for f in findings]
        self.assertEqual(probes, [
            "a payee address with a wrong checksum",
            "the clerk approving her own payment (S7's P3)",
        ], o.line)
        for f in findings:
            self.assertTrue(f.said.startswith("ACCEPTED:"), f.said)
            self.assertTrue(f.came_back.startswith("HTTP 20"), f.came_back)
        self.assertIn("17 probe(s), 2 finding(s)", o.line)
        # the venue contract is accepted, as the law says (Spec T8): the probe is made, HTTP 201 is the expectation, and it is no finding
        venue = [s for s in self.runner.evidence["S11"] if "a real venue contract" in str(s.get("probe", ""))]
        self.assertEqual(len(venue), 1)
        self.assertEqual(venue[0]["status"], 201)
        self.assertEqual(venue[0]["result"], "accepted, as the law says (%s)" % H.VENUE_RULING)
        self.assertTrue(any(l.startswith("  S11 — accepted, as the law says — a payee address that is a real venue contract") for l in self.said))
        refused = [l for l in self.said if l.startswith("  S11 — refused as expected — ")]
        for expected in ("without the x-csrf-token header", "Ben confirms", "a viewer's session at an author route: POST /v1/payees", "POST /v1/sets", "POST /v1/invites",
                         "/answers", "principal", "did not serve", "compile before confirm", "wrong kind", "replayed", "wrong rpId", "second confirm"):
            self.assertTrue(any(expected in l for l in refused), expected)
        # the viewer was brought in for the probes, and the probe drafts were deleted
        self.assertTrue(self.runner.people["olive"].signed_in)
        self.assertEqual(self.runner.people["olive"].roles, ["viewer"])
        deleted = [c for c in self.runner.calls if c.method == "DELETE" and c.station == "S11"]
        self.assertEqual(len(deleted), 2)
        self.assertTrue(all(c.status == 200 for c in deleted))

    def test_s12_measures_without_judging(self):
        o = self.outcomes["S12"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("the optimizer:", o.line)
        self.assertIn("0 over 2 seconds", o.line)
        self.assertIn("0 retried after a 5xx", o.line)
        self.assertIn("0 of them reads a browser would not make", o.line)
        self.assertNotIn(H.INVITATION_SENDS_FIRST, "\n".join(self.runner.facts["optimizer"]["lines"]), "no slow invitation, no sentence about one")

    def test_every_line_is_one_line_for_a_screen_reader(self):
        for station in H.STATION_IDS:
            line = self.runner.line(self.outcomes[station])
            self.assertTrue(line.startswith("%s — " % station), line)
            self.assertNotIn("\n", line)

    def test_the_report_carries_the_twelve_stations_the_evidence_and_no_secret(self):
        self.assertTrue(os.path.basename(self.report_path).startswith("aer360-harness-"))
        self.assertIn("## The closing table", self.report)
        for station, title in H.STATIONS:
            self.assertIn("| %s %s |" % (station, title), self.report)
            self.assertIn("## %s — %s" % (station, title), self.report)
        self.assertEqual(len(self.runner.findings), 4, "A5 as JSON, one credential for four people, the wrong checksum accepted, the clerk's own approval")
        self.assertIn("Findings under S10 and S11: 4.", self.report)
        self.assertIn("| Station | Outcome | Line |", self.report)
        self.assertNotIn("Last run", self.report, "no previous report in this run's folder, so no last-run column")
        self.assertIn("Specs T7 and T8, 19 and 20 September 2026.", self.report)
        self.assertIn("### Evidence, call by call", self.report)
        self.assertIn("Came back, verbatim:", self.report)
        token = H.token_of_link(self.link)
        self.assertNotIn(token, self.report, "the invitation token is redacted to its last four characters")
        self.assertIn("…" + token[-4:], self.report, "the token travels in the body, redacted to its last four characters")
        self.assertNotIn("BEGIN EC PRIVATE KEY", self.report)
        for call in self.runner.calls:
            if call.sent and isinstance(call.sent, dict) and isinstance(call.sent.get("response"), dict):
                for field in ("clientDataJSON", "attestationObject", "authenticatorData", "signature"):
                    if field in call.sent["response"]:
                        self.assertTrue(str(call.sent["response"][field]).startswith("…"), field)
        for person in self.runner.people.values():
            if person.csrf:
                self.assertNotIn(person.csrf, self.report)
        for cookie in self.double.sessions:
            self.assertNotIn(cookie, self.report)
        self.assertNotIn("csrfToken\": \"" + (self.runner.people["harriet"].csrf or "x"), self.report)

    def test_the_founders_key_file_carries_the_facts_a_later_run_needs(self):
        with open(self.runner.key_path(self.runner.people["harriet"]), "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        self.assertEqual(stored["base"], self.double.base)
        self.assertEqual(stored["rp_id"], self.double.rp_id)
        self.assertEqual(stored["aap_credential_id"], self.runner.people["harriet"].credential_id)
        self.assertGreaterEqual(stored["sign_count"], 3, "the counter moved with every assertion and was saved")
        self.assertEqual(oct(os.stat(self.runner.key_path(self.runner.people["harriet"])).st_mode & 0o777), "0o600")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S6AgainstDoublesThatAnswerDifferently(unittest.TestCase):
    """Spec T9: the knobs on the whitelist road — the estate before Spec 89, a roster below its quorum, a platform that never activates."""

    def run_s6(self, **double_kwargs):
        double = EstateDouble(**double_kwargs)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        return double, runner, outcomes

    def test_an_estate_before_spec_89_gets_one_further_press_by_ben_the_note_and_still_whitelists(self):
        """Spec T9 §1: where the answer carries no approvals count, one more press is made as Ben on the charter's quorum, and the note says so."""
        double, runner, outcomes = self.run_s6(pending_approval_says_why=False)
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)
        for record in runner.facts["payees"]:
            self.assertEqual([p["who"] for p in record["presses"]], ["Ada Approver", "Ben Signatory"])
            self.assertEqual(record["register_status"], "whitelisted")
        self.assertTrue(any("the answer carried no approvals count; one more press was made on the charter's quorum of two" in n
                            for n in runner.notes["S6"]))
        # §2: a pending first approval that did not say why is a finding of S10's kind, raised in S6, carrying the answer verbatim
        findings = [f for f in runner.findings if f.station == "S6" and "did not say why" in f.probe]
        self.assertEqual(len(findings), 2, "one per payee")
        self.assertIn("the answer carried no approvals and no may_still_approve and no sentence", findings[0].said)
        self.assertIn("pending_promotion", findings[0].came_back)

    def test_a_roster_smaller_than_its_quorum_is_the_finding_a_quorum_that_exceeds_its_roster(self):
        """Spec T9 §2: an answer whose approvals.required exceeds the names in may_still_approve plus collected is a finding."""
        double, runner, outcomes = self.run_s6(whitelist_roster=("ada",))
        findings = [f for f in runner.findings if f.station == "S6" and "a quorum that exceeds its roster" in f.probe]
        self.assertEqual(len(findings), 2, "one per payee: two required, only Ada on the roster")
        self.assertIn("approvals.required is 2, may_still_approve names 0 and approvals.collected is 1", findings[0].said)
        self.assertEqual(outcomes["S6"].outcome, H.FAIL, "the register never reaches whitelisted")

    def test_a_platform_that_never_activates_fails_s6_with_the_register_statuses(self):
        """Spec T9: the second press still answers pending_promotion after the required presses, so S6 fails as it did before."""
        double, runner, outcomes = self.run_s6(platform_never_activates=True)
        self.assertEqual(outcomes["S6"].outcome, H.FAIL, outcomes["S6"].line)
        self.assertIn("register: Northwind Supplies pending_promotion, Contoso Legal pending_promotion", outcomes["S6"].line)
        for record in runner.facts["payees"]:
            self.assertEqual(len(record["presses"]), 2, "the loop stops after approvals.required presses")
            self.assertEqual(record["register_status"], "pending_promotion")
        self.assertEqual([f for f in runner.findings if f.station == "S6"], [], "a platform that has not activated yet is not a finding; the estate said why")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ResumedAndSecondRuns(unittest.TestCase):
    def setUp(self):
        self.double = EstateDouble()
        self.tmp = tempfile.mkdtemp()
        self.link = self.double.mint_founder_link()
        first = runner_on(self.double, self.tmp, invite=self.link)
        self.first = {o.station: o for o in first.run()}

    def test_a_run_resumed_at_s6_signs_everybody_in_with_the_stored_passkeys(self):
        said = []
        runner = runner_on(self.double, self.tmp, start_at="S6", said=said)
        outcomes = {o.station: o for o in runner.run()}
        for station in ("S1", "S2", "S3", "S4", "S5"):
            self.assertEqual(outcomes[station].outcome, H.SKIPPED)
            self.assertIn("resumed at S6", outcomes[station].line)
        for key in ("harriet", "ada", "ben", "cora", "olive"):
            self.assertTrue(any(l == "resume — %s signed in with the stored passkey" % A.PEOPLE[key].name for l in said), key)
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)
        self.assertEqual(runner.facts["unlisted_key"], "UNLISTED_ETHEREUM_2", "the first run paid the first unlisted destination, so the estate no longer finds it new")
        self.assertIn("P2 (4999.99 USDC, expected to waits): the run waits for approval", outcomes["S7"].line)
        self.assertTrue(any("no read-back and answers recorded for the policy interview" in n for n in runner.notes["S10"]))

    def test_a_second_full_run_signs_in_rather_than_enrolling_and_amends_the_charter(self):
        said = []
        runner = runner_on(self.double, self.tmp, invite=self.link, said=said)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S1"].outcome, H.PASS, outcomes["S1"].line)
        self.assertIn("signed in with the stored passkey", outcomes["S1"].line)
        self.assertTrue(any("the --invite link was not spent" in n for n in runner.notes["S1"]))
        self.assertEqual(outcomes["S2"].outcome, H.PASS)
        self.assertIn("this estate has walked before", outcomes["S2"].line)
        self.assertEqual(outcomes["S3"].outcome, H.PASS, outcomes["S3"].line)
        self.assertIn("beyond stage 2: this estate had walked further before this run", outcomes["S3"].line)
        self.assertEqual(outcomes["S5"].outcome, H.PASS, outcomes["S5"].line)
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)

    def test_a_passkey_stored_for_another_base_is_left_alone(self):
        other = EstateDouble(base="https://demo.estate.test")
        link = other.mint_founder_link()
        said = []
        runner = runner_on(other, self.tmp, invite=link, said=said)
        runner.load_passkeys()
        self.assertIsNone(runner.people["harriet"].passkey)
        self.assertTrue(any("was enrolled at https://estate.test, not https://demo.estate.test" in l for l in said))

    def test_fresh_sets_the_stored_keys_aside_and_enrols_anew(self):
        double = EstateDouble()
        link = double.mint_founder_link()
        runner = H.Runner(double.base, os.path.join(self.tmp, "store"), link, True, None, os.path.join(self.tmp, "out"), transport=double, say=lambda s: None, sleep=lambda s: None)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S1"].outcome, H.PASS, outcomes["S1"].line)
        self.assertIn("enrolled by invitation", outcomes["S1"].line)
        archived = [d for d in os.listdir(os.path.join(self.tmp, "store")) if d.startswith("harness-holdings.")]
        self.assertEqual(len(archived), 1, "the old estate folder was set aside, never deleted")

    def test_without_a_stored_key_and_without_an_invite_s1_says_what_the_first_run_needs(self):
        double = EstateDouble()
        runner = runner_on(double, tempfile.mkdtemp())
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S1"].outcome, H.FAIL)
        self.assertIn("no passkey is stored for Harriet Founder", outcomes["S1"].line)
        self.assertIn("the first run needs the invitation link", outcomes["S1"].line)
        self.assertEqual(outcomes["S2"].outcome, H.FAIL)
        self.assertIn("the founder has no session", outcomes["S2"].line)
        self.assertEqual(outcomes["S9"].outcome, H.OUT_OF_SCOPE)
        self.assertEqual(outcomes["S12"].outcome, H.PASS)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheRunContinuesPastAFailedStation(unittest.TestCase):
    def test_a_workspace_with_no_funding_account_fails_s7_in_the_routes_words_and_the_hats_still_run(self):
        double = EstateDouble(source_account=None)
        tmp = tempfile.mkdtemp()
        link = double.mint_founder_link()
        runner = runner_on(double, tmp, invite=link)
        outcomes = {o.station: o for o in runner.run()}
        for station in ("S1", "S2", "S3", "S4", "S5", "S6"):
            self.assertEqual(outcomes[station].outcome, H.PASS, outcomes[station].line)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL)
        self.assertIn("refused at creation — GAS_PREFLIGHT_UNAVAILABLE: No funding account has been set for this workspace, so network fees cannot be checked.", o.line)
        self.assertTrue(any("names no funding account" in n for n in runner.notes["S7"]))
        self.assertEqual(outcomes["S8"].outcome, H.PASS)
        self.assertIn("journey stage 3 of 7", outcomes["S8"].line)
        self.assertEqual(outcomes["S12"].outcome, H.PASS)
        # Rule 13 held: the 503 named what happened, so S10 raised no finding about it
        self.assertFalse(any(f.probe.startswith("Rule 13") for f in runner.findings))
        self.assertTrue(any("S7 created no run for P3" in n for n in runner.notes["S11"]))

    def test_an_unreachable_estate_is_a_fault_not_a_judgment(self):
        def dead(request):
            raise H.Unreachable("%s %s could not be reached: connection refused" % (request.get_method(), request.full_url))
        tmp = tempfile.mkdtemp()
        runner = H.Runner("https://estate.test", os.path.join(tmp, "store"), "https://estate.test/invite#token-0000", False, None, tmp, transport=dead, say=lambda s: None, sleep=lambda s: None)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S1"].outcome, H.FAIL)
        self.assertIn("the estate could not be reached, so nothing was judged", outcomes["S1"].line)
        self.assertIn("connection refused", outcomes["S1"].line)


if __name__ == "__main__":
    unittest.main()
