"""
The founder's road, S1 to S9, walked against the estate double (Spec T7): the enrolment, the
journey, the Policy Interview answered from the book to its compile, the people, the wallet
account, the payees, the payments and Ada's approval, the journey and readiness; then the three
hats on what the double said, the report, and a run resumed with the stored passkeys.

Spec T10 (20 September 2026): the double is the estate after AER 360 Spec 91, so a fresh run enrols
each person on a credential of their own — and meets what that unmasks under this charter (only Ada is
a named approver, so Ben's press is refused at the approve route's guard). The estate of the four live
runs stands behind `before_spec_91=True`, and the three scenarios Spec T10 lists — the people brought in
again on their own credentials, the people already on their own, a seat grant refused — are here too.

Spec T11 (21 September 2026): the double is the estate at AER 360 Spec 92, catalog version 14, so S3 walks
23 questions and S5 18, the book answering the seven Spec 92 added; S3 reports the book's version beside
what the estate served; S10 reads the new law back and raises nothing new; S11's venue probe meets the payee
door's refusal by name, PAYEE_IS_VENUE_CONTRACT, and raises no finding; S7 says what the tiers would do.
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
from tests.test_aer360_double import (EstateDouble, NO_FUNDING_WALLET_SENTENCE, Refusal, WALLET_BIRTH_REFUSED_ON_21_SEPTEMBER,  # noqa: E402
                                      approver_seat_shared_sentence, runner_on, tiers_need_three_people, usd_figure)

# The approve route's guard (aeredium/AERAccounts, routes/payees.ts:221 at 9964205: requireCaller 'approver'), in the room sentence.
NEEDS_AN_APPROVER = ("ROLE_NOT_GRANTED: You are signed into Harness Holdings Pty Ltd as an author and a viewer. This action needs an approver — "
                     "permissions come from your organisation’s policy, not from this application.")
PENDING_FIRST_ANSWER = {
    "whitelistStatus": "pending_promotion",
    "approvals": {"required": 2, "collected": 1, "remaining": 1},
    "may_still_approve": ["Harriet Founder", "Ben Signatory", "Cora Clerk"],
    "sentence": "1 of 2 approvals recorded for this address. One more is needed, from Harriet Founder, Ben Signatory or Cora Clerk. The address is not payable until then.",
}


def store_of(runner):
    return os.path.join(runner.store_dir, A.ESTATE["client_id"])


def read_key_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheFoundersRoad(unittest.TestCase):
    """A fresh estate under Spec 91: every person enrolled on a credential of their own, and what that unmasks under this charter."""

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
        self.assertIn("policy interview: 23 questions answered", o.line, "Spec T11: C11A and C19 among them")
        self.assertIn("charter compiled (Harness Holdings Pty Ltd; quorum 1", o.line)
        self.assertIn("journey stage 2 of 7", o.line)
        # Spec T11 §5: the book's version beside the estate's, which the estate does not state
        self.assertIn("; the answer book answers catalog version 14, and the estate served 23 question(s), every one known to the book (%s)" % H.ESTATE_STATES_NO_CATALOG_VERSION, o.line)
        given = [q for q, _, _, _ in self.runner.facts["answers"]["policy"]]
        self.assertEqual(given, [q.id for q in A.expected_walk("policy")], "the estate served the questions the book expected, in order")
        self.assertIn("C11A", given)
        self.assertIn("C19", given)
        self.assertNotIn("C11C", given, "asked only behind C11A's third answer")
        charter = self.runner.facts["charter"]["policy"]
        self.assertEqual(charter["payeeApproval"], {"answer": "change_approvers", "roster": ["%s <%s>" % (A.PEOPLE[k].name, A.PEOPLE[k].email) for k in A.CENSUS_ORDER],
                                                    "quorum": 2, "rosterQuestionId": "A8", "quorumQuestionId": "C12"})
        self.assertEqual(charter["payeeVenueContracts"], "refused")
        self.assertEqual(self.runner.facts["charter"]["policy"]["allowedChains"], ["aeredium-testnet"])
        self.assertEqual(self.runner.facts["charter"]["policy"]["recordedChains"], ["aeredium", "ethereum"])
        self.assertEqual(self.runner.facts["charter_standing"], {"standsWritten": True, "inForceSince": self.runner.facts["compile"]["policy"]["receipt"]["completedAt"]})
        self.assertIs(self.runner.facts["compile"]["policy"]["receipt"]["governanceAlreadyStood"], False, "the first compile establishes the change governance")

    def test_s4_brings_in_the_three_authors_each_on_their_own_credential_and_ada_is_seated_on_hers(self):
        """Spec 91: three invitations, three credentials, none the founder's; the redemption seats Ada on her own (Spec T10 §1, §2)."""
        o = self.outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        founder = self.runner.people["harriet"]
        credentials = set()
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            self.assertTrue(person.signed_in, key)
            self.assertIn("author", person.roles)
            self.assertIn("%s enrolled as author" % person.name, o.line)
            self.assertIn("already on their own credential: %s, not the founder's %s" % (H.last4(person.credential_id), H.last4(founder.credential_id)), o.line)
            self.assertNotEqual(person.credential_id, founder.credential_id)
            credentials.add(person.credential_id)
        self.assertEqual(len(credentials), 3, "three distinct credentials")
        self.assertEqual(self.runner.facts["brought_in_again"], [], "nobody was on the shared credential, so nothing was minted twice")
        ada = self.runner.people["ada"]
        self.assertIn("Ada Approver's seat: found not_enrolled, naming no credential; after the people were brought in seated, naming %s; Ada Approver's own credential, so no grant was needed" % H.last4(ada.credential_id), o.line)
        seats = self.runner.facts["seats"]
        ada_seat = next(s for s in seats["seats"] if s["email"] == A.PEOPLE["ada"].email)
        self.assertEqual(ada_seat["state"], "seated", "the invitation completed the seat the charter named")
        self.assertEqual(ada_seat["credentialId"], ada.credential_id, "on Ada's own credential, never the founder's (Spec 91, item 2)")
        self.assertIn("approver", ada.roles)
        self.assertNotIn("approver", self.runner.people["ben"].roles, "Ben holds his own credential, and the charter seats only Ada")
        self.assertEqual(len(self.runner.facts["invites_register"]["invites"]), 4, "the founder's birth invitation and three authors")
        # the comparison step, once per person, with the one expected line (Spec T10 §1)
        compared = [s for s in self.runner.evidence["S4"] if s["expected"].startswith("a credential of ")]
        self.assertEqual([s["expected"] for s in compared], ["a credential of %s's own, not the founder's" % A.PEOPLE[k].name for k in A.AUTHORS_INVITED])
        for s in compared:
            self.assertTrue(s["result"].startswith("already on their own credential: …"), s["result"])
            self.assertIn(", not the founder's …", s["result"])

    def test_s5_opens_the_operating_account_and_moves_the_journey_to_stage_three(self):
        o = self.outcomes["S5"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("wallet account: 18 questions answered", o.line, "Spec T11: WO1 to WO4 among them, WO3 behind the named holder")
        self.assertIn("charter compiled (Operating account, purpose Operations — day-to-day business payments, per payment hold 1000000 cents, daily 5000000 cents, destinations hold_non_listed)", o.line)
        self.assertIn("journey stage 3 of 7 (working_the_sandbox)", o.line)
        self.assertIn("No daily close has completed yet", o.line)
        given = [q for q, _, _, _ in self.runner.facts["answers"]["wallet_account"]]
        self.assertEqual(given, [q.id for q in A.expected_walk("wallet_account")])
        self.assertEqual(given[given.index("WA2") + 1:given.index("WCW")], ["WO1", "WO2", "WO3", "WO4"])
        # the compiled account charter carries Spec 92's fields as the compiler records them
        charter = self.runner.facts["charter"]["wallet_account"]
        self.assertEqual(charter["holder"], {"held": "by_person", "name": "Ben Signatory", "email": A.PEOPLE["ben"].email, "title": "Officer"})
        self.assertEqual(charter["signingTiers"]["holderAloneUpToCents"], "200000")
        self.assertEqual(charter["signingTiers"]["twoSignaturesUpToCents"], "1000000")
        self.assertEqual(charter["signingTiers"]["thirdParty"], {"name": "Harriet", "surname": "Founder", "email": A.PEOPLE["harriet"].email, "title": "CEO"})
        self.assertEqual(charter["signers"], ["Ada Approver <%s>" % A.PEOPLE["ada"].email, "Ben Signatory <%s>" % A.PEOPLE["ben"].email, "Harriet Founder <%s>" % A.PEOPLE["harriet"].email],
                         "WA1's people, and WO2's third party once")
        self.assertIsNone(charter["payeeApproval"])
        self.assertIsNone(charter["payeeVenueContracts"])
        # the read-back spoke the figures the book wrote, never the written dollar, and the person by name and email
        lines = {l["questionId"]: l["spoken"] for l in self.runner.facts["readback"]["wallet_account"]["lines"]}
        self.assertEqual(lines["WO3"], "US$2,000 and 00 cents.")
        self.assertEqual(lines["WO4"], "US$10,000 and 00 cents.")
        self.assertEqual(lines["WO1"], "Ben Signatory — %s." % A.PEOPLE["ben"].email)
        self.assertEqual(lines["WO2"], "Harriet — %s — CEO — Founder" % A.PEOPLE["harriet"].email, "a list entry's values in the order jsonb stores them")
        self.assertIn("WO1_TITLE", lines)
        self.assertIn("HOLD_NOT_WRITTEN", lines)
        self.assertIn("WQ_TIERS", lines)

    def test_s6_presses_the_roster_until_the_quorum_is_met_on_a_fresh_estate(self):
        """
        Spec T12 §2: since AER 360 Spec 95 the whitelist door admits any active roster signer, not only a seated approver.
        On a fresh estate every roster seat is empty, so Ada's press binds her own seat and counts (1 of 2), Ben's binds
        his and meets the quorum of two, and the payee is whitelisted. The harness presses the roster in order and stops
        when the count is met, so Cora is not reached.
        """
        o = self.outcomes["S6"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("Northwind Supplies: created; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", o.line)
        self.assertIn("Contoso Legal: created; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", o.line)
        self.assertIn("register: Northwind Supplies whitelisted, Contoso Legal whitelisted", o.line)
        for record in self.runner.facts["payees"]:
            self.assertEqual([(p["who"], p["status"]) for p in record["presses"]], [("Ada Approver", 200), ("Ben Signatory", 200)], "the quorum is met at Ben; Cora is not reached")
            self.assertEqual(record["presses"][0]["answer"], PENDING_FIRST_ANSWER, "the first approval's answer says why (Spec 89)")
            self.assertEqual(record["register_status"], "whitelisted")
        self.assertEqual([f for f in self.runner.findings if f.station == "S6"], [], "the estate said why at each pending press, at a quorum its roster can meet")

    def test_s7_makes_the_three_payments_as_the_clerk_and_reads_each_state_against_its_expectation(self):
        o = self.outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertTrue(o.line.startswith("payments as Cora Clerk:"))
        # Spec T12: S6 whitelisted Northwind, so the first payment to it is within limits and clears at submission (no approval asked)
        self.assertIn("P1 (1250.00 USDC, expected to proceeds to approval): created and submitted; status approved, approvalsRequired 0", o.line)
        self.assertIn("Ada's approval of P1 was not asked: the run stands approved", o.line)
        self.assertIn("P2 (4999.99 USDC, expected to waits): the run waits for approval: status pending_approval, approvalsRequired 1", o.line)
        self.assertIn("P3 (12000.00 USDC, expected to held): the run waits for approval: status pending_approval, approvalsRequired 1", o.line)
        # Spec T11 §4: the amounts are unchanged, and the line and the expectation column say what the tiers would do with each
        self.assertIn("approvalsRequired 0; under the tiers: within the holder's own figure (US$2,000.00), one signature — the holder's", o.line)
        self.assertIn("approvalsRequired 1; under the tiers: two signatures (above US$2,000.00, up to US$10,000.00)", o.line)
        self.assertIn("approvalsRequired 1; under the tiers: three signatures (above US$10,000.00)", o.line)
        submits = [s for s in self.runner.evidence["S7"] if s["route"].endswith("/submit")]
        self.assertEqual([s["expected"].split("; ", 1)[1] for s in submits],
                         ["under the tiers: within the holder's own figure (US$2,000.00), one signature — the holder's",
                          "under the tiers: two signatures (above US$2,000.00, up to US$10,000.00)",
                          "under the tiers: three signatures (above US$10,000.00)"])
        reviews = [s for s in self.runner.evidence["S7"] if s["route"].endswith("/sets/review")]
        self.assertTrue(all("(figures from this run's compiled account charter)" in s["expected"] for s in reviews), [s["expected"] for s in reviews])
        self.assertEqual([p.amount for p in A.PAYMENTS], ["1250.00", "4999.99", "12000.00"])
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

    def test_s10_finds_mains_json_currency_and_nothing_else_and_counts_four_distinct_credentials(self):
        """Spec T10 §3: four sessions, four distinct credential ids, none the founder's — said as a note; the marker absent on every row."""
        o = self.outcomes["S10"]
        findings = [f for f in self.runner.findings if f.station == "S10"]
        self.assertEqual([f.probe for f in findings], ["read-back (policy) of A5"], o.line)
        self.assertEqual(findings[0].expected, "AUD", "a currency is read back as its code (Spec 88); main's default arm speaks JSON, which is the estate's finding")
        self.assertEqual(findings[0].said, "the read-back says '{\"text\":\"AUD\"}'")
        self.assertEqual(o.outcome, H.FAIL)
        self.assertIn("1 finding(s)", o.line)
        founder = self.runner.people["harriet"]
        self.assertIn("the 4 session(s) carry 4 distinct credential id(s), and only the founder's own is the founder's %s: Harriet Founder %s, Ada Approver %s, Ben Signatory %s, Cora Clerk %s" % (
            H.last4(founder.credential_id), H.last4(founder.credential_id), H.last4(self.runner.people["ada"].credential_id),
            H.last4(self.runner.people["ben"].credential_id), H.last4(self.runner.people["cora"].credential_id)), self.runner.notes["S10"])
        self.assertIn("the People register marks none of Harriet Founder, Ada Approver, Ben Signatory, Cora Clerk as sharing a credential (Spec 91's marker absent on their rows)", self.runner.notes["S10"])
        self.assertTrue(all(row["sharesCredentialWith"] == [] for row in self.runner.facts["invites_register"]["invites"]))
        # the census the double speaks as jsonb stores it — name — role — email — against the book's name, email, role: no finding (Spec T8)
        a8 = next(l for l in self.runner.facts["readback"]["policy"]["lines"] if l["questionId"] == "A8")
        self.assertTrue(a8["spoken"].startswith("Harriet Founder — Authorise payments — harness+harriet@aeredium.io; "), a8["spoken"])
        self.assertFalse(any("not compared" in n for n in self.runner.notes["S10"]), "every kind the catalog serves has a rendering")

    def test_s11_finds_the_acceptances_the_code_makes_and_nothing_else(self):
        o = self.outcomes["S11"]
        findings = [f for f in self.runner.findings if f.station == "S11"]
        probes = [f.probe for f in findings]
        # the clerk's own approval is refused at the guard now that Cora holds a credential of her own: no longer a finding (Spec 91)
        self.assertEqual(probes, ["a payee address with a wrong checksum"], o.line)
        for f in findings:
            self.assertTrue(f.said.startswith("ACCEPTED:"), f.said)
            self.assertTrue(f.came_back.startswith("HTTP 20"), f.came_back)
        self.assertIn("17 probe(s), 1 finding(s)", o.line)
        # Spec T11 §3: the charter answered No at C19, so the probe expects the payee door's refusal by name, in the estate's sentence
        venue = [s for s in self.runner.evidence["S11"] if "a real venue contract" in str(s.get("probe", ""))]
        self.assertEqual(len(venue), 1)
        self.assertEqual(venue[0]["status"], 422)
        sentence = "This address is the contract of Uniswap v3 on ethereum. Your charter says a payee must be a wallet held by a person or a company (question C19). Nothing was saved."
        self.assertEqual(venue[0]["expected"], "HTTP 422 PAYEE_IS_VENUE_CONTRACT: %s (this run's compiled policy charter says payeeVenueContracts \"refused\")" % sentence)
        self.assertEqual(venue[0]["result"], "refused as the charter says (C19 No): PAYEE_IS_VENUE_CONTRACT: %s" % sentence)
        self.assertIn('"code": "PAYEE_IS_VENUE_CONTRACT"', venue[0]["came_back"])
        self.assertEqual(self.runner.facts["venue_law"], "refused")
        self.assertTrue(any(l.startswith("  S11 — refused as the charter says — a payee address that is a real venue contract") and l.endswith(": PAYEE_IS_VENUE_CONTRACT: %s" % sentence) for l in self.said))
        self.assertFalse(any("venue contract" in f.probe for f in findings), "refused as the charter says is no finding")
        refused = [l for l in self.said if l.startswith("  S11 — refused as expected — ")]
        for expected in ("without the x-csrf-token header", "Ben confirms", "a viewer's session at an author route: POST /v1/payees", "POST /v1/sets", "POST /v1/invites",
                         "/answers", "principal", "did not serve", "compile before confirm", "wrong kind", "replayed", "wrong rpId", "second confirm",
                         "the clerk approving her own payment"):
            self.assertTrue(any(expected in l for l in refused), expected)
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
        self.assertEqual(len(self.runner.findings), 2, "A5 as JSON, the wrong checksum accepted")
        self.assertIn("Findings under S10 and S11: 2.", self.report)
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
        self.assertEqual(sorted(os.listdir(store_of(self.runner))), ["ada.json", "ben.json", "cora.json", "harriet.json", "olive.json"], "one passkey per person")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheEstateBeforeSpec91(unittest.TestCase):
    """The estate of the four live runs (`before_spec_91=True`): an author invitation enrols the founder's credential, and S10 says so."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(before_spec_91=True)
        cls.tmp = tempfile.mkdtemp()
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        cls.outcomes = {o.station: o for o in cls.runner.run()}

    def test_s4_enrols_everybody_onto_the_founders_credential_and_says_so(self):
        o = self.outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        founder = self.runner.people["harriet"]
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            self.assertEqual(person.credential_id, founder.credential_id)
            self.assertIn("%s enrolled as author" % person.name, o.line)
        self.assertIn("on the shared credential %s, the founder's — a fresh invitation on this estate enrolled the founder's credential, so no second one was minted" % H.last4(founder.credential_id), o.line)
        self.assertEqual(self.runner.facts["brought_in_again"], [], "a fresh enrolment that lands on the shared credential is not re-invited in the same run")
        self.assertIn("Ada Approver's seat: found not_enrolled, naming no credential; after the people were brought in seated, naming %s" % H.last4(founder.credential_id), o.line)

    def test_s6_counts_the_shared_credentials_presses_once_as_the_fourth_live_run_did(self):
        """The platform matches a press to a seat by credential (Spec T10, from Spec 91's builder): one shared credential, one signature, however many roster members press it."""
        o = self.outcomes["S6"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("Northwind Supplies: created; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (1 of 2); Cora Clerk counted (1 of 2); Harriet Founder counted (1 of 2): pending_promotion", o.line)
        for record in self.runner.facts["payees"]:
            self.assertEqual([p["who"] for p in record["presses"]], ["Ada Approver", "Ben Signatory", "Cora Clerk", "Harriet Founder"])
            self.assertEqual(record["presses"][1]["answer"], PENDING_FIRST_ANSWER, "Ben's press is told what Ada's was told: the platform counted the one credential once")

    def test_s10_raises_the_one_credential_for_four_people_and_names_it_the_founders(self):
        findings = [f for f in self.runner.findings if f.station == "S10"]
        self.assertEqual([f.probe for f in findings], ["read-back (policy) of A5", "people register: one credential for several people"])
        self.assertIn("1 distinct credential id(s) for 4 people", findings[1].said)
        self.assertTrue(findings[1].said.endswith("; %s is the founder's credential" % H.last4(self.runner.people["harriet"].credential_id)), findings[1].said)
        self.assertIn("the register's rows carry no sharesCredentialWith (Spec 91's marker), so it was not read: an estate before Spec 91", self.runner.notes["S10"])

    def test_s11_finds_the_clerks_own_approval_accepted_on_the_shared_credential(self):
        probes = [f.probe for f in self.runner.findings if f.station == "S11"]
        self.assertEqual(probes, ["a payee address with a wrong checksum", "the clerk approving her own payment (S7's P3)"])
        self.assertIn("17 probe(s), 2 finding(s)", self.outcomes["S11"].line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S6AgainstDoublesThatAnswerDifferently(unittest.TestCase):
    """
    Spec T9: the knobs on the whitelist road — the estate before Spec 89, a roster below its quorum, a platform that never activates.
    Since Spec T10 Ben holds a credential of his own and the charter seats Ada alone, so an operator at the platform's console names
    Ben's credential a second approver (`platform_names_approver`) for his press to pass the guard and reach the platform.
    """

    def run_s6(self, **double_kwargs):
        double = EstateDouble(platform_names_approver=("ben",), **double_kwargs)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        return double, runner, outcomes

    def test_an_estate_before_spec_89_still_whitelists_and_each_pending_press_saying_nothing_is_a_finding(self):
        """Spec T12 §2: the roster is pressed in order; a press that counts but says nothing of why (before Spec 89) is a finding, and the quorum is still met."""
        double, runner, outcomes = self.run_s6(pending_approval_says_why=False)
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)
        for record in runner.facts["payees"]:
            self.assertEqual([p["who"] for p in record["presses"]], ["Ada Approver", "Ben Signatory"])
            self.assertEqual(record["register_status"], "whitelisted")
        findings = [f for f in runner.findings if f.station == "S6" and "did not say why" in f.probe]
        self.assertEqual(len(findings), 2, "one per payee: the first pending press carried no approvals count")
        self.assertIn("the answer carried no approvals and no may_still_approve and no sentence", findings[0].said)
        self.assertIn("pending_promotion", findings[0].came_back)

    def test_a_roster_smaller_than_its_quorum_is_the_finding_a_quorum_that_exceeds_its_roster(self):
        """Spec T9 §2: an answer whose approvals.required exceeds the names in may_still_approve plus collected is a finding; Ben's press, on no seat, is the platform's refusal relayed."""
        double, runner, outcomes = self.run_s6(whitelist_roster=("ada",))
        findings = [f for f in runner.findings if f.station == "S6" and "a quorum that exceeds its roster" in f.probe]
        self.assertEqual(len(findings), 2, "one per payee: two required, only Ada on the roster")
        self.assertIn("approvals.required is 2, may_still_approve names 0 and approvals.collected is 1", findings[0].said)
        self.assertEqual(outcomes["S6"].outcome, H.FAIL, "the register never reaches whitelisted")
        self.assertIn("Ben Signatory not counted (SIGNATURE_NOT_COUNTED: The access platform did not count your approval", outcomes["S6"].line)

    def test_a_platform_that_never_activates_fails_s6_with_the_register_statuses(self):
        """Spec T12 §2: the count is met but the platform never activates, so the harness presses the whole roster (until nobody is left) and S6 fails with the register's pending statuses."""
        double, runner, outcomes = self.run_s6(platform_never_activates=True)
        self.assertEqual(outcomes["S6"].outcome, H.FAIL, outcomes["S6"].line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2)", outcomes["S6"].line)
        self.assertIn(": pending_promotion", outcomes["S6"].line)
        self.assertIn("register: Northwind Supplies pending_promotion, Contoso Legal pending_promotion", outcomes["S6"].line)
        for record in runner.facts["payees"]:
            self.assertEqual([p["who"] for p in record["presses"]], ["Ada Approver", "Ben Signatory", "Cora Clerk", "Harriet Founder"], "the roster is pressed to exhaustion: the count is met but the address never activates")
            self.assertEqual(record["register_status"], "pending_promotion")

    def test_every_press_refused_fails_s6_naming_each_refusal(self):
        """Spec T12 §2: a roster with no seat the harness can bind — every press SIGNATURE_NOT_COUNTED — fails S6, its line naming each refusal."""
        double, runner, outcomes = self.run_s6(whitelist_roster=())
        self.assertEqual(outcomes["S6"].outcome, H.FAIL, outcomes["S6"].line)
        for name in ("Ada Approver", "Ben Signatory", "Cora Clerk", "Harriet Founder"):
            self.assertIn("%s not counted (SIGNATURE_NOT_COUNTED: The access platform did not count your approval" % name, outcomes["S6"].line)
        for record in runner.facts["payees"]:
            self.assertEqual([p["status"] for p in record["presses"]], [403, 403, 403, 403])
            self.assertNotEqual(record["register_status"], "whitelisted")
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
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", outcomes["S6"].line)
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)
        self.assertEqual(runner.facts["unlisted_key"], "UNLISTED_ETHEREUM_2", "the first run paid the first unlisted destination, so the estate no longer finds it new")
        self.assertIn("P2 (4999.99 USDC, expected to waits): the run waits for approval", outcomes["S7"].line)
        self.assertTrue(any("no read-back recorded for the policy interview" in n for n in runner.notes["S10"]))
        # Spec T11: a run that compiled no policy charter reads the book's C19 for the venue probe and says so; the door still refuses by name
        self.assertTrue(any(n.startswith("this run compiled no policy charter (S3 did not run), so the venue probe's expectation is read off the answer book's C19") for n in runner.notes["S11"]), runner.notes["S11"])
        self.assertEqual(runner.facts["venue_law"], "refused")
        self.assertFalse(any("venue contract" in f.probe for f in runner.findings if f.station == "S11"))
        venue = [s for s in runner.evidence["S11"] if "a real venue contract" in str(s.get("probe", ""))][-1]
        self.assertEqual(venue["status"], 422)
        self.assertIn("(the answer book's C19 is \"No — only wallets held by people or companies\")", venue["expected"])
        # and S7's tiers are read from the book, no account charter having been compiled in this run
        reviews = [s for s in runner.evidence["S7"] if s["route"].endswith("/sets/review")]
        self.assertTrue(all("(figures from the answer book)" in s["expected"] for s in reviews), [s["expected"] for s in reviews])

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
        self.assertIs(runner.facts["compile"]["policy"]["receipt"]["governanceAlreadyStood"], True, "the change governance was established by the first run and stands")
        self.assertEqual(outcomes["S4"].outcome, H.PASS, outcomes["S4"].line)
        self.assertEqual(outcomes["S4"].line.count("signed in with the stored passkey; already on their own credential"), 3)
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
        self.assertEqual(sorted(os.listdir(store_of(runner))), ["ada.json", "ben.json", "cora.json", "harriet.json", "olive.json"], "the fresh keys under their first names")

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
    def test_an_estate_whose_gateway_refuses_the_birth_fails_s5_and_s7_in_the_estates_words_and_the_hats_still_run(self):
        """
        Spec T13: the estate of 23:44 on 21 September — the founder presses for the funding wallet and the gateway refuses the
        credential, so none is born. S5 fails naming WALLET_BIRTH_REFUSED with the gateway's sentence; the faucet is not asked
        (nothing to fund); S7 meets routes/sets.ts's refusal of a run without a funding account and adds no asset line (there is no
        wallet to fund by hand); S8 reads transactable False, reason no funding wallet; the hats still run.
        """
        double = EstateDouble(funding_wallet="refused")
        tmp = tempfile.mkdtemp()
        link = double.mint_founder_link()
        runner = runner_on(double, tmp, invite=link)
        outcomes = {o.station: o for o in runner.run()}
        for station in ("S1", "S2", "S3", "S4"):
            self.assertEqual(outcomes[station].outcome, H.PASS, outcomes[station].line)
        s5 = outcomes["S5"]
        self.assertEqual(s5.outcome, H.FAIL, s5.line)
        self.assertIn("funding wallet: not born — refused: WALLET_BIRTH_REFUSED: %s" % WALLET_BIRTH_REFUSED_ON_21_SEPTEMBER, s5.line)
        self.assertIn("faucet: not asked — the estate has no funding wallet to fund", s5.line)
        self.assertEqual(double.faucet.requests, [])
        self.assertEqual(double.rpc.calls, [], "no wallet, so no balance to read")
        presses = [c for c in runner.calls if c.route == "POST /v1/workspace/funding-wallet"]
        self.assertEqual([(c.status, c.retry_of) for c in presses], [(502, None)], "the press is made once with its assertion and never retried")
        self.assertEqual(outcomes["S6"].outcome, H.PASS, "Spec 95: the roster whitelists the payees; the funding wallet gates S7, not S6")
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL)
        self.assertIn("refused at creation — GAS_PREFLIGHT_UNAVAILABLE: No funding account has been set for this workspace, so network fees cannot be checked.", o.line)
        self.assertTrue(any("names no funding account" in n and NO_FUNDING_WALLET_SENTENCE in n for n in runner.notes["S7"]), runner.notes["S7"])
        self.assertNotIn("US$18,249.99", o.line, "no wallet, so no asset line: nothing can be funded by hand yet")
        self.assertEqual(outcomes["S8"].outcome, H.PASS)
        self.assertIn("journey stage 3 of 7", outcomes["S8"].line)
        self.assertIn("readiness: transactable False, reason no funding wallet; funding wallet: none — %s" % NO_FUNDING_WALLET_SENTENCE, outcomes["S8"].line)
        self.assertEqual(outcomes["S12"].outcome, H.PASS)
        # Rule 13 held: the 502 and the 503 named what happened, so S10 raised no finding about them
        self.assertFalse(any(f.probe.startswith("Rule 13") for f in runner.findings))
        self.assertTrue(any("S7 created no run for P3" in n for n in runner.notes["S11"]))
        summary = runner.report().split("Findings under S10 and S11", 1)[1].split("## S1 — Enrol", 1)[0]
        self.assertIn("Funding wallet: none — %s The press answered WALLET_BIRTH_REFUSED: " % NO_FUNDING_WALLET_SENTENCE, summary)

    def test_an_unreachable_estate_is_a_fault_not_a_judgment(self):
        def dead(request):
            raise H.Unreachable("%s %s could not be reached: connection refused" % (request.get_method(), request.full_url))
        tmp = tempfile.mkdtemp()
        runner = H.Runner("https://estate.test", os.path.join(tmp, "store"), "https://estate.test/invite#token-0000", False, None, tmp, transport=dead, say=lambda s: None, sleep=lambda s: None)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S1"].outcome, H.FAIL)
        self.assertIn("the estate could not be reached, so nothing was judged", outcomes["S1"].line)
        self.assertIn("connection refused", outcomes["S1"].line)


# ---------------------------------------------------------------------------
# Spec T10 — every person is brought in on their own credential.
# ---------------------------------------------------------------------------
@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class EveryPersonOnTheirOwnCredential(unittest.TestCase):
    """
    Spec T10 against the double in the pre-91 shape with four people on one credential, then Spec 91 deployed: the first run
    is the estate of the four live runs; the second is the rerun the ship note asks for. S4 re-invites three, stores three new
    passkeys with the suffix, and the sessions carry four distinct credentials; S10 raises no credential finding and the closing
    table says the old one closed; S6 reports what the platform answers.
    """

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(before_spec_91=True)
        cls.tmp = tempfile.mkdtemp()
        cls.link = cls.double.mint_founder_link()
        cls.first = runner_on(cls.double, cls.tmp, invite=cls.link)
        cls.first_outcomes = {o.station: o for o in cls.first.run()}
        cls.first_report = cls.first.write_report()
        cls.store = store_of(cls.first)
        cls.before = {key: open(os.path.join(cls.store, "%s.json" % key), "rb").read() for key in A.AUTHORS_INVITED}
        cls.double.before_spec_91 = False  # Spec 91 deploys (PR #112)
        cls.said = []
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.link, said=cls.said)
        cls.outcomes = {o.station: o for o in cls.runner.run()}
        cls.report_path = cls.runner.write_report()
        with open(cls.report_path, "r", encoding="utf-8") as handle:
            cls.report = handle.read()
        cls.after = {key: open(os.path.join(cls.store, "%s.json" % key), "rb").read() for key in A.AUTHORS_INVITED}
        cls.date = os.path.basename(cls.runner.people["ada"].key_file)[len("ada-2-"):-len(".json")]

    def test_the_first_run_is_the_estate_of_the_four_live_runs(self):
        founder = self.first.people["harriet"]
        self.assertTrue(all(self.first.people[k].credential_id == founder.credential_id for k in A.AUTHORS_INVITED))
        self.assertIn("people register: one credential for several people", [f.probe for f in self.first.findings])
        self.assertEqual(self.first_outcomes["S6"].outcome, H.FAIL)
        self.assertIn("Ben Signatory counted (1 of 2)", self.first_outcomes["S6"].line, "on one shared credential the platform counts the roster's presses once")

    def test_s4_sees_the_shared_credential_and_brings_the_three_in_again_on_their_own(self):
        o = self.outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        founder = self.runner.people["harriet"]
        shared = H.last4(founder.credential_id)
        credentials = {founder.credential_id}
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            self.assertIn("%s signed in with the stored passkey; on the shared credential %s, the founder's; brought in again on %s, not the founder's %s (the new passkey stored at %s, the old one kept at %s" % (
                person.name, shared, H.last4(person.credential_id), shared, person.key_file, os.path.join(self.store, "%s.json" % key)), o.line)
            self.assertNotEqual(person.credential_id, founder.credential_id)
            credentials.add(person.credential_id)
        self.assertEqual(len(credentials), 4, "four sessions, four distinct credentials")
        records = self.runner.facts["brought_in_again"]
        self.assertEqual([r["person"] for r in records], list(A.AUTHORS_INVITED))
        for r in records:
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["old_credential"], founder.credential_id)
            self.assertEqual(r["new_credential"], self.runner.people[r["person"]].credential_id)
        self.assertEqual(records[0]["seat"], {"charterNamedThem": True, "granted": True, "note": None}, "the redemption of Ada's fresh invitation seated her own credential")
        self.assertTrue(any("bringing Ada Approver in again on a credential of their own" in l for l in self.said))
        # the minted invitations: three in the first run, three more now
        self.assertEqual([m["person"] for m in self.runner.facts["invites_minted"]], list(A.AUTHORS_INVITED))
        self.assertEqual(len(self.runner.facts["invites_register"]["invites"]), 8, "the birth invitation, three authors, the viewer, and three re-invitations")

    def test_the_steps_expect_a_credential_of_the_persons_own_and_name_both(self):
        founder = self.runner.people["harriet"]
        compared = [s for s in self.runner.evidence["S4"] if s["expected"].startswith("a credential of ")]
        self.assertEqual(len(compared), 6, "the sign-in and the re-enrolment, for each of three people")
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            mine = [s for s in compared if s["who"] == person.name]
            self.assertEqual([s["expected"] for s in mine], ["a credential of %s's own, not the founder's" % person.name] * 2)
            self.assertEqual(mine[0]["route"], "POST /v1/auth/login/verify")
            self.assertEqual(mine[0]["result"], "on the shared credential %s, the founder's; brought in again below" % H.last4(founder.credential_id))
            self.assertEqual(mine[1]["route"], "POST /v1/auth/invite/verify")
            self.assertEqual(mine[1]["result"], "brought in again on %s, not the founder's %s" % (H.last4(person.credential_id), H.last4(founder.credential_id)))

    def test_three_new_passkeys_are_stored_beside_the_old_with_the_suffix_and_the_date(self):
        founder = self.runner.people["harriet"]
        expected = ["ada-2-%s.json" % self.date, "ada.json", "ben-2-%s.json" % self.date, "ben.json", "cora-2-%s.json" % self.date, "cora.json", "harriet.json", "olive.json"]
        self.assertEqual(sorted(os.listdir(self.store)), expected)
        self.assertRegex(self.date, r"^\d{4}-\d{2}-\d{2}$")
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            new_path = os.path.join(self.store, "%s-2-%s.json" % (key, self.date))
            self.assertEqual(person.key_file, new_path)
            self.assertEqual(oct(os.stat(new_path).st_mode & 0o777), "0o600")
            new = read_key_file(new_path)
            old = read_key_file(os.path.join(self.store, "%s.json" % key))
            self.assertEqual(new["aap_credential_id"], person.credential_id, "the new passkey speaks for the credential of the person's own")
            self.assertEqual(old["aap_credential_id"], founder.credential_id, "the old passkey still speaks for the founder's credential")
            self.assertNotEqual(new["credential_id"], old["credential_id"], "two passkeys, not one written over the other")
            self.assertEqual(new["display_name"], person.name)
            self.assertEqual(self.runner.stored_key_paths(person), [os.path.join(self.store, "%s.json" % key), new_path], "oldest first")

    def test_the_old_passkey_files_are_untouched_by_a_run(self):
        """The old key is kept: after the re-invitation only its counter moved, with the one sign-in that found it shared; a run after that never writes it."""
        for key in A.AUTHORS_INVITED:
            before = json.loads(self.before[key])
            after = json.loads(self.after[key])
            self.assertEqual(after["sign_count"], before["sign_count"] + 1, "the sign-in that found the shared credential moved the counter once")
            before.pop("sign_count")
            after.pop("sign_count")
            self.assertEqual(before, after, "nothing else of the old passkey changed: its key, its credential id and the credential it spoke for stand")
        third = runner_on(self.double, self.tmp, invite=self.link)
        outcomes = {o.station: o for o in third.run()}
        self.assertEqual(outcomes["S4"].outcome, H.PASS, outcomes["S4"].line)
        self.assertEqual(outcomes["S4"].line.count("signed in with the stored passkey; already on their own credential"), 3)
        for key in A.AUTHORS_INVITED:
            with open(os.path.join(self.store, "%s.json" % key), "rb") as handle:
                self.assertEqual(handle.read(), self.after[key], "the old passkey file is byte for byte as the re-invitation run left it")
            self.assertEqual(third.people[key].key_file, os.path.join(self.store, "%s-2-%s.json" % (key, self.date)), "the newest passkey signs")
        self.assertEqual(len([n for n in os.listdir(self.store) if n.startswith("ada-")]), 1, "no third passkey was stored: nothing was minted")
        self.assertEqual(third.facts["brought_in_again"], [])

    def test_adas_seat_names_her_new_credential_and_the_line_says_what_it_named_before(self):
        o = self.outcomes["S4"]
        founder = self.runner.people["harriet"]
        ada = self.runner.people["ada"]
        self.assertIn("Ada Approver's seat: found seated, naming %s; after the people were brought in seated, naming %s; Ada Approver's own credential, so no grant was needed" % (
            H.last4(founder.credential_id), H.last4(ada.credential_id)), o.line)
        regrant = self.runner.facts["seat_regrant"]
        self.assertEqual(regrant["found"], "seated, naming %s" % H.last4(founder.credential_id))
        self.assertEqual(regrant["stood"]["credentialId"], ada.credential_id)
        self.assertIsNone(regrant["granted"], "the redemption seated her, so no grant was made")
        self.assertEqual([c.route for c in self.runner.calls if c.station == "S4" and c.route == "POST /v1/approver-seats/grant"], [])
        seat = next(s for s in self.runner.facts["seats"]["seats"] if s["email"] == ada.email)
        self.assertEqual((seat["state"], seat["credentialId"], seat["ambiguous"]), ("seated", ada.credential_id, False))
        self.assertIn("approver", ada.roles)

    def test_s10_raises_no_credential_finding_and_the_closing_table_says_it_closed(self):
        founder = self.runner.people["harriet"]
        probes = [f.probe for f in self.runner.findings if f.station == "S10"]
        self.assertEqual(probes, ["read-back (policy) of A5"], probes)
        self.assertNotIn("people register: one credential for several people", probes)
        self.assertFalse(any("the Spec 91 marker on" in p for p in probes), "no marker finding: the three were re-invited, and the founder's row names only the passkeys the harness retired")
        notes = self.runner.notes["S10"]
        self.assertIn("the 4 session(s) carry 4 distinct credential id(s), and only the founder's own is the founder's %s: Harriet Founder %s, Ada Approver %s, Ben Signatory %s, Cora Clerk %s" % (
            H.last4(founder.credential_id), H.last4(founder.credential_id), H.last4(self.runner.people["ada"].credential_id),
            H.last4(self.runner.people["ben"].credential_id), H.last4(self.runner.people["cora"].credential_id)), notes)
        self.assertIn("the People register marks none of Ada Approver, Ben Signatory, Cora Clerk, Olive Overseer as sharing a credential (Spec 91's marker absent on their rows)", notes)
        self.assertIn("the founder's row (Harriet) carries the marker for the 3 passkey(s) the harness retired, which still speak for the founder's credential %s at the estate: "
                      'the register says sharesCredentialWith ["Ada Approver", "Ben Signatory", "Cora Clerk"]; on the People screen: "shares a credential with Ada Approver, Ben Signatory and Cora Clerk; invite them again to give them their own"' % H.last4(founder.credential_id), notes)
        self.assertEqual([(r["person"], r["label"], r["aap_credential_id"]) for r in self.runner.retired_passkeys()],
                         [(k, A.PEOPLE[k].name, founder.credential_id) for k in A.AUTHORS_INVITED])
        # the register: each re-invited person's newest row carries no marker; the founder's names the three retired passkeys
        rows = self.runner.facts["invites_register"]["invites"]
        for key in A.AUTHORS_INVITED:
            person = self.runner.people[key]
            own = [r for r in rows if r["email"] == person.email and r["credentialId"] == person.credential_id]
            self.assertEqual(len(own), 1)
            self.assertEqual((own[0]["state"], own[0]["sharesCredentialWith"]), ("redeemed", []))
        founder_row = next(r for r in rows if r["email"] is None)
        self.assertEqual(founder_row["sharesCredentialWith"], ["Ada Approver", "Ben Signatory", "Cora Clerk"])
        # the closing table: the finding of the last run closed
        self.assertIn("| S10 The auditor | fail | last run fail · 1 closed: people register: one credential for several people · 1 still open: read-back (policy) of A5 |", self.report)
        self.assertIn("- closed — S10 — people register: one credential for several people", self.report)
        self.assertEqual(self.runner.last_run()["name"], os.path.basename(self.first_report))

    def test_s4_has_the_census_sign_adas_seat_home_and_s6_counts_ada(self):
        """
        Spec T15, THE FOUR-AT-TWO AFTER SPEC 99. The change governance was established on the first run, so the roster's seat
        for Ada was still bound to the credential her first press wore — the founder's, now retired. Her re-invitation's
        redemption proposes the move (Spec 95) and the platform holds it as a ceremony at the charter's count of two. S4 lists it
        and has the census sign it as the list names them: the founder is refused in the roster's own words (this double
        attributes the founder's key no address), Ada counts (1 of 2), Ben counts (2 of 2), the platform applies it, and the
        seat now names Ada's current credential. S6 then presses Ada (1 of 2) and Ben (2 of 2), stops at the count so Cora is
        not asked, and the payee is whitelisted; S10 reads the trail's roster.seat_rebound row and drops Spec T12's note.
        """
        o = self.outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        ada = self.runner.people["ada"]
        signing = self.runner.facts["roster_signing"]
        self.assertEqual(len(signing), 1, signing)
        record = signing[0]
        self.assertEqual((record["state_found"], record["proposed_here"], record["outcome"], record["reproposed"]), ("awaiting", True, "applied", False))
        self.assertEqual(record["seat"]["email"], ada.email)
        self.assertEqual([(s["who"], s["status"]) for s in record["signatures"]], [("Harriet Founder", 403), ("Ada Approver", 200), ("Ben Signatory", 200)],
                         "each person the list names as able to sign, in turn, until the estate reports it applied; Cora is not reached")
        self.assertEqual(record["signatures"][0]["refusal_code"], "CHANGE_SIGNER_NOT_ON_ROSTER")
        self.assertEqual(record["signatures"][1]["answer"]["signaturesCollected"], 1)
        self.assertEqual(record["signatures"][2]["answer"]["state"], "applied")
        short = ada.credential_id[:8]
        self.assertIn("roster changes: %s… awaiting (Ada Approver's seat, 0 of 2 signed): found awaiting at 0 of 2, Harriet Founder, Ada Approver, Ben Signatory and Cora Clerk able to sign; "
                      "Harriet Founder refused (CHANGE_SIGNER_NOT_ON_ROSTER: A change of who the approvers are is signed by Harriet Founder, Ada Approver, Ben Signatory and Cora Clerk; you are not among them. Nothing was signed." % record["pendingTxId"][:8], o.line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2); applied: the seat now names %s, Ada Approver's current credential (%s), signed by Ada Approver and Ben Signatory" % (
            short, H.last4(ada.credential_id)), o.line)
        moved = self.runner.facts["seats_moved"]
        self.assertEqual([(m["key"], m["signers"], m["new_credential"]) for m in moved], [("ada", ["Ada Approver", "Ben Signatory"], ada.credential_id)])
        ada_seat = next(s for s in self.double.whitelist_seats if s["user_id"] == A.PEOPLE["ada"].email)
        self.assertEqual(ada_seat["credential_id"], ada.credential_id, "the platform moved the roster's seat to Ada's current credential")
        # S6: Ada 1 of 2, Ben 2 of 2, Cora not asked
        o6 = self.outcomes["S6"]
        self.assertEqual(o6.outcome, H.PASS, o6.line)
        sig = "Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted"
        self.assertIn("Northwind Supplies: created; promoted; %s" % sig, o6.line)
        self.assertIn("Contoso Legal: created; promoted; %s" % sig, o6.line)
        for payee in self.runner.facts["payees"]:
            self.assertEqual([(p["who"], p["status"]) for p in payee["presses"]], [("Ada Approver", 200), ("Ben Signatory", 200)], "the count is met at Ben; Cora is not asked")
            self.assertEqual(payee["register_status"], "whitelisted")
        self.assertEqual([f for f in self.runner.findings if f.station in ("S4", "S6")], [])
        # every refusal S4 met says who refused and why (Rule 13)
        for call in self.runner.calls:
            if call.station == "S4" and call.status >= 400:
                self.assertIsNone(H.refusal_without_why(call.status, call.text), call.text)
        # S10: the trail row, and no note about a seat still bound to a retired passkey
        notes = self.runner.notes["S10"]
        self.assertFalse(any("whitelist press was not counted" in n for n in notes), notes)
        trail = [n for n in notes if n.startswith("the trail carries roster.seat_rebound for Ada Approver's seat: ceremony %s, signed by Ada Approver, Ben Signatory, moved from %s to %s on Harness Holdings Pty Ltd — whitelist_mutation approvers (via roster_change), at " % (
            record["pendingTxId"], H.last4(self.runner.people["harriet"].credential_id), H.last4(ada.credential_id)))]
        self.assertEqual(len(trail), 1, notes)

    def test_the_seat_is_granted_again_where_the_redemption_did_not_seat_it(self):
        """Spec T10 §2, the grant road: an estate whose redemption says nothing of a seat leaves Ada enrolled_not_seated on her new credential, and the founder grants it."""
        double = EstateDouble(before_spec_91=True, seat_completes_on_redemption=False)
        tmp = tempfile.mkdtemp()
        link = double.mint_founder_link()
        first = runner_on(double, tmp, invite=link)
        first_outcomes = {o.station: o for o in first.run()}
        founder = first.people["harriet"]
        self.assertIn("Ada Approver's seat: found not_enrolled, naming no credential; after the people were brought in enrolled_not_seated, naming %s; granted again by the founder: seated, naming %s" % (
            H.last4(founder.credential_id), H.last4(founder.credential_id)), first_outcomes["S4"].line, "the estate before Spec 91 seats the shared credential")
        double.before_spec_91 = False
        second = runner_on(double, tmp, invite=link)
        outcomes = {o.station: o for o in second.run()}
        ada = second.people["ada"]
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("Ada Approver's seat: found seated, naming %s; after the people were brought in enrolled_not_seated, naming %s; granted again by the founder: seated, naming %s" % (
            H.last4(founder.credential_id), H.last4(ada.credential_id), H.last4(ada.credential_id)), o.line)
        regrant = second.facts["seat_regrant"]
        self.assertTrue(regrant["granted"])
        self.assertEqual(regrant["after"]["credentialId"], ada.credential_id)
        grant = [s for s in second.evidence["S4"] if s["route"] == "POST /v1/approver-seats/grant"]
        self.assertEqual(len(grant), 1)
        self.assertEqual(grant[0]["expected"], "the seat seated, naming Ada Approver's own credential %s (before the grant: enrolled_not_seated, naming %s)" % (H.last4(ada.credential_id), H.last4(ada.credential_id)))
        self.assertEqual(grant[0]["result"], "granted: seated, naming %s" % H.last4(ada.credential_id))
        self.assertEqual([f for f in second.findings if f.station == "S4"], [])
        self.assertIn(ada.credential_id, double.second_approvers, "the policy names Ada's own credential a second approver")
        self.assertNotIn(founder.credential_id, [c for c in double.second_approvers if c != founder.credential_id], "and the grant added nothing else")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AlreadyOnTheirOwnCredential(unittest.TestCase):
    """Spec T10 against the double where the credentials already differ: nothing minted, "already on their own credential", one passkey per person."""

    def test_nothing_is_minted_and_each_person_keeps_their_one_passkey(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        link = double.mint_founder_link()
        first = runner_on(double, tmp, invite=link)
        first.run()
        second = runner_on(double, tmp, invite=link)
        outcomes = {o.station: o for o in second.run()}
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        founder = second.people["harriet"]
        for key in A.AUTHORS_INVITED:
            person = second.people[key]
            self.assertIn("%s signed in with the stored passkey; already on their own credential: %s, not the founder's %s" % (
                person.name, H.last4(person.credential_id), H.last4(founder.credential_id)), o.line)
        self.assertNotIn("brought in again", o.line)
        posted = [c.route for c in second.calls if c.station == "S4" and c.method == "POST"]
        self.assertEqual(posted, ["POST /v1/auth/login/options", "POST /v1/auth/login/verify"] * 3, "S4 only signed the three in: nothing minted, nobody enrolled, no grant")
        self.assertEqual(second.facts["brought_in_again"], [])
        self.assertEqual(second.facts["invites_minted"], [])
        self.assertEqual(sorted(os.listdir(store_of(second))), ["ada.json", "ben.json", "cora.json", "harriet.json", "olive.json"], "one passkey per person")
        self.assertIn("Ada Approver's seat: found seated, naming %s; Ada Approver's own credential, so no grant was needed" % H.last4(second.people["ada"].credential_id), o.line)
        self.assertNotIn("people register: one credential for several people", [f.probe for f in second.findings])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ASeatGrantRefusedIsAFindingInTheEstatesWords(unittest.TestCase):
    """
    Spec T10 §2: a grant the estate refuses is a finding in the estate's words. The estate: people enrolled before Spec 91 onto the
    founder's credential with nobody seated (a redemption before Spec 58's count 3 said nothing of a seat); then Spec 91 deploys on
    an account that has gained a second policy entry bearing authorship, so the re-invitation is refused (INVITE_INVALID, listing
    both, as Spec 91's own test has it) and Ada stays on the shared credential — which the seat road refuses to seat, by name
    (APPROVER_SEAT_CREDENTIAL_SHARED, 409).
    """

    def test_the_grant_refused_by_name_is_a_finding_and_s4_fails(self):
        double = EstateDouble(before_spec_91=True, seat_completes_on_redemption=False)
        tmp = tempfile.mkdtemp()
        link = double.mint_founder_link()
        first = runner_on(double, tmp, invite=link)
        for station in ("station_s1", "station_s2", "station_s3"):
            self.assertEqual(getattr(first, station)().outcome, H.PASS)
        for key in A.AUTHORS_INVITED:
            self.assertEqual(first.bring_in("S4", first.people[key], "author"), "enrolled as author")
        double.before_spec_91 = False
        double.second_authorship_entry = True
        second = runner_on(double, tmp, invite=link)
        outcomes = {o.station: o for o in second.run()}
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        founder = second.people["harriet"]
        refused_mint = ("not brought in again: the invitation answered INVITE_INVALID: This invite link is expired or has already been used. "
                        "(the account carries several policy entries bearing authorship; this invite must name which credential it enrols)")
        for key in A.AUTHORS_INVITED:
            self.assertIn("%s signed in with the stored passkey; on the shared credential %s, the founder's; %s" % (A.PEOPLE[key].name, H.last4(founder.credential_id), refused_mint), o.line)
            self.assertEqual(second.people[key].credential_id, founder.credential_id, "still on the shared credential")
        sentence = approver_seat_shared_sentence("", ["Harriet", "Ben Signatory", "Cora Clerk"])
        self.assertIn("Ada Approver's seat: found enrolled_not_seated, naming %s; the grant answered APPROVER_SEAT_CREDENTIAL_SHARED: %s" % (H.last4(founder.credential_id), sentence), o.line)
        findings = [f for f in second.findings if f.station == "S4"]
        self.assertEqual([f.probe for f in findings], ["approver seat: the grant of Ada Approver's seat"])
        finding = findings[0]
        self.assertEqual(finding.route, "POST /v1/approver-seats/grant")
        self.assertEqual(finding.sent, {"email": A.PEOPLE["ada"].email})
        self.assertEqual(finding.said, "refused: APPROVER_SEAT_CREDENTIAL_SHARED: %s" % sentence)
        self.assertTrue(finding.came_back.startswith("HTTP 409 — "), finding.came_back)
        self.assertIn('"sharedWith": "Harriet, Ben Signatory, Cora Clerk"', finding.came_back)
        self.assertEqual(finding.expected, "the seat seated, naming Ada Approver's own credential %s (before the grant: enrolled_not_seated, naming %s)" % (H.last4(founder.credential_id), H.last4(founder.credential_id)))
        self.assertIsNone(H.refusal_without_why(409, finding.came_back.split(" — ", 1)[1]), "the refusal says who refused and why")
        self.assertEqual(second.facts["seat_regrant"]["granted"], False)
        self.assertTrue(second.facts["seat_regrant"]["refusal"].startswith("APPROVER_SEAT_CREDENTIAL_SHARED: "))
        self.assertEqual([r["ok"] for r in second.facts["brought_in_again"]], [False, False, False])
        # S10 still says who shares what
        self.assertIn("people register: one credential for several people", [f.probe for f in second.findings if f.station == "S10"])
        report = second.report()
        self.assertIn("- **approver seat: the grant of Ada Approver's seat** — refused: APPROVER_SEAT_CREDENTIAL_SHARED: ", report)
        self.assertIn("  - Route: POST /v1/approver-seats/grant", report)


class WalkBackDouble(EstateDouble):
    """An estate whose wallet-account read-back walks the browser back to WA1 a set number of times before it passes (Spec T12 §1)."""

    def __init__(self, walk_backs=1, **kwargs):
        super().__init__(**kwargs)
        self._walk_backs_left = walk_backs

    def readback(self, iv, check_standing=True):
        if check_standing and iv["interviewType"] == "wallet_account" and self._walk_backs_left > 0:
            self._walk_backs_left -= 1
            sentence = tiers_need_three_people(usd_figure(A.MONEY["two_signatures_cents"]), 2)
            raise Refusal("CHARTER_INCOMPLETE", sentence, {"cause": sentence, "named": "2"}, walkBackTo={"questionId": "WA1"})
        return super().readback(iv, check_standing)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheHarnessFollowsAWalkBack(unittest.TestCase):
    """
    Spec T12 §1: where the read-back answers CHARTER_INCOMPLETE with walkBackTo, the harness answers the named question from
    the book, resumes to the read-back and reads it again, reporting the walk-back as a note. The same question walked back
    to twice is a failure carrying both sentences — a book that cannot satisfy the belt is reported and never looped.
    """

    SENTENCE = tiers_need_three_people(usd_figure(A.MONEY["two_signatures_cents"]), 2)

    def s5(self, walk_backs):
        double = WalkBackDouble(walk_backs=walk_backs)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        for station in ("station_s1", "station_s2", "station_s3", "station_s4"):
            getattr(runner, station)()
        return runner, runner.run_station("S5", "Wallet account")  # run_station catches a StationStop as an Outcome, as a run does

    def test_a_walk_back_is_followed_once_and_the_note_is_written(self):
        runner, o = self.s5(1)
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("walked back to WA1: %s; answered from the book and returned to the read-back" % self.SENTENCE, runner.notes["S5"])
        self.assertIn("wallet_account", runner.facts["readback"], "the read-back was reached and recorded after the walk-back")
        self.assertIn("WA1", [q for q, _, _, _ in runner.facts["answers"]["wallet_account"]], "WA1 was answered from the book on the walk-back")

    def test_the_same_walk_back_twice_is_a_failure_with_both_sentences(self):
        runner, o = self.s5(2)
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("walked back to WA1 a second time", o.line)
        self.assertEqual(o.line.count(self.SENTENCE), 2, "the failure carries both of the estate's sentences")
        self.assertNotIn("wallet_account", runner.facts["readback"], "the read-back was never reached, so none was recorded")


if __name__ == "__main__":
    unittest.main()
