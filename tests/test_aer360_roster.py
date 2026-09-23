"""
Spec T15 (22 September 2026): the harness has the approvers sign a change of who the approvers are, and S6 counts Ada — from the run of
13:50 the same day (aer360-harness-2026-09-22-135010.md), where S6 read "Ada Approver not counted (SIGNATURE_NOT_COUNTED …)" and S10 noted
the platform's roster seat still bound to a retired passkey, and from AER 360 Spec 99 as it was built (aeredium/AERAccounts, commit 33e039c).
Each test here was red on main.

The double is the estate at Spec 99 (tests/test_aer360_double.py): a re-invitation's redemption proposes the seat's move (Spec 95) and the
platform holds it as a ceremony at the charter's count of two; GET /v1/roster/changes lists it, POST /v1/roster/changes/{id}/sign signs it
under the signer's step-up of purpose `roster.change`, and the count met, the change is presented again, the seat moves and the trail says
`roster.seat_rebound`. Harness Holdings is walked as the live runs left it: a first run before Spec 91 binds Ada's roster seat to the founder's
credential her press wore; the estate moves to Specs 91, 95 and 99; the second run re-invites Ada and meets the ceremony.
"""
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
from tests.test_aer360_double import (  # noqa: E402
    EstateDouble, MESSAGES, PLATFORM_EXPIRED, PLATFORM_NOT_AUTHORIZED_SENTENCE, FUNDING_WALLET_PURPOSE, WORKSPACE_ID, runner_on,
)

WHITELIST_ROSTER_NAME = "Harness Holdings Pty Ltd — whitelist_mutation approvers"
CHANGE_ROSTER_NAME = "Harness Holdings Pty Ltd — multisig_mutation approvers"
EXPIRED_OPENS = ("Moving Ada Approver’s seat to their current passkey expired at the access platform before the count was met: 0 of 2 approvers have signed. "
                 "The platform holds it as pending, expiring ")
EXPIRED_CLOSES = "and nothing can be signed on it now. Granting Ada Approver’s seat again in this room, or Ada Approver redeeming a fresh invitation, proposes the move afresh."
GRANTED_AGAIN = "the founder granted Ada Approver's seat again so Spec 95 proposes the move afresh"


def four_at_two(change_roster=("ben", "cora"), **second_run_dials):
    """
    Harness Holdings as the live runs left it. The first run is the estate before Spec 91: four people on one credential, and Ada's press in
    S6 binds her roster seat to it. Then Specs 91, 95 and 99 are live (`second_run_dials` set any other dial on the double), and the second
    run re-invites Ada on a credential of her own; her redemption proposes the move, and the platform holds it as a ceremony at two.
    """
    double = EstateDouble(before_spec_91=True, change_roster=change_roster)
    tmp = tempfile.mkdtemp()
    link = double.mint_founder_link()
    first = runner_on(double, tmp, invite=link)
    first.run()
    double.before_spec_91 = False
    for name, value in second_run_dials.items():
        setattr(double, name, value)
    said = []
    runner = runner_on(double, tmp, invite=link, said=said)
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes, said


def roster_changes_of(line):
    """S4's line between `roster changes: ` and the register's count."""
    return re.split(r"; \d+ invitation\(s\) in the register$", line.split("roster changes: ", 1)[1])[0]


def sign_calls(runner, station="S4"):
    return [(c.who, c.status) for c in runner.calls if c.station == station and c.route.endswith("/sign")]


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheApproversSignAdasSeatHome(unittest.TestCase):
    """Spec T15, the spec's own scenario: one awaiting change for Ada needing 2, Ben and Cora able to sign."""

    @classmethod
    def setUpClass(cls):
        cls.double, cls.runner, cls.outcomes, cls.said = four_at_two()
        cls.ada = cls.runner.people["ada"]
        cls.record = cls.runner.facts["roster_signing"][0]
        cls.pending_tx_id = cls.record["pendingTxId"]
        cls.report = cls.runner.report()

    def test_s4_signs_as_ben_then_as_cora_asserts_the_seat_and_reports_both(self):
        o = self.outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(len(self.runner.facts["roster_signing"]), 1, "one change: the redemption's, for Ada's seat")
        record = self.record
        self.assertEqual((record["state_found"], record["proposed_here"], record["outcome"], record["reproposed"]), ("awaiting", True, "applied", False))
        self.assertEqual((record["seat"]["email"], record["seat"]["name"], record["seat"]["newCredentialId"]), (self.ada.email, "Ada Approver", self.ada.credential_id[:8]))
        self.assertEqual([(s["who"], s["status"], s["answer"]["signaturesCollected"], s["answer"]["state"]) for s in record["signatures"]],
                         [("Ben Signatory", 200, 1, "awaiting"), ("Cora Clerk", 200, 2, "applied")], "in turn as the list names them, reading signaturesCollected after each, until applied")
        self.assertEqual(roster_changes_of(o.line),
                         "%s… awaiting (Ada Approver's seat, 0 of 2 signed): found awaiting at 0 of 2, Ben Signatory and Cora Clerk able to sign; Ben Signatory counted (1 of 2); "
                         "Cora Clerk counted (2 of 2); applied: the seat now names %s, Ada Approver's current credential (%s), signed by Ben Signatory and Cora Clerk" % (
                             self.pending_tx_id[:8], self.ada.credential_id[:8], H.last4(self.ada.credential_id)))
        # the seat, asserted where the People screen reads it: the change applied, its seat naming Ada's current credential in the estate's short form
        self.assertEqual(self.record["rebound"]["newCredentialId"], self.ada.credential_id[:8])
        self.assertEqual(next(s for s in self.double.whitelist_seats if s["user_id"] == self.ada.email)["credential_id"], self.ada.credential_id, "the platform moved the seat")
        self.assertEqual([(m["key"], m["signers"], m["new_credential"], m["roster"]) for m in self.runner.facts["seats_moved"]],
                         [("ada", ["Ben Signatory", "Cora Clerk"], self.ada.credential_id, WHITELIST_ROSTER_NAME)])
        # the steps: the list, then for each signer the options road and the press, then the read-back after the count
        steps = [s for s in self.runner.evidence["S4"] if "/v1/roster/changes" in s["route"]]
        self.assertEqual([(s["route"].split(" ")[0], s["who"]) for s in steps],
                         [("GET", "Harriet Founder"), ("POST", "Ben Signatory"), ("POST", "Ben Signatory"), ("POST", "Cora Clerk"), ("POST", "Cora Clerk"), ("GET", "Harriet Founder")])
        self.assertTrue(steps[0]["expected"].startswith("every roster change the platform holds for the estate (Spec 99)"), steps[0]["expected"])
        self.assertEqual(steps[0]["result"], "1 change(s) listed: %s… awaiting (Ada Approver's seat, 0 of 2 signed)" % self.pending_tx_id[:8])
        self.assertEqual(steps[1]["expected"], "200 with options (the challenge the estate derives from roster-change:<workspace id>:%s:<issuedAtMs> under the purpose roster.change) and issuedAtMs" % self.pending_tx_id)
        self.assertEqual(steps[2]["expected"], "Ben Signatory's signature counted: signaturesCollected of 2, state awaiting until the count is met, then applied with rebound naming Ada Approver's current credential; "
                                               "a refusal is judged for Rule 13 and reported in the estate's words, never retried")
        self.assertEqual((steps[2]["result"], steps[4]["result"]), ("counted: 1 of 2, awaiting", "counted: 2 of 2, applied"))
        self.assertEqual(steps[2]["sent"]["issuedAtMs"], json.loads(steps[1]["came_back"])["issuedAtMs"], "the press carries the options' issuedAtMs")
        self.assertEqual(steps[5]["expected"], "the change %s… applied, its seat naming Ada Approver's current credential %s (short form %s)" % (
            self.pending_tx_id[:8], H.last4(self.ada.credential_id), self.ada.credential_id[:8]))
        self.assertEqual(steps[5]["result"], "1 change(s) listed: %s… applied (Ada Approver's seat, 2 of 2 signed)" % self.pending_tx_id[:8])
        # the passkey step-up: the double verified each assertion against the binding roster-change:<workspace id>:<pendingTxId>:<issuedAtMs> | credential | roster.change
        presses = [c for c in self.double.calls if c["path"].endswith("/sign") and c["method"] == "POST"]
        self.assertEqual(len(presses), 2)
        self.assertEqual(sign_calls(self.runner), [("Ben Signatory", 200), ("Cora Clerk", 200)], "each signer pressed once; nothing retried")
        self.assertEqual([f for f in self.runner.findings if f.station == "S4"], [])

    def test_the_list_and_the_answers_are_the_estates_own_words(self):
        steps = [s for s in self.runner.evidence["S4"] if "/v1/roster/changes" in s["route"]]
        listed = json.loads(steps[0]["came_back"])["changes"][0]
        self.assertEqual((listed["maySign"], listed["callerMaySign"], listed["callerHasSigned"], listed["signedBy"], listed["via"], listed["operation"]),
                         (["Ben Signatory", "Cora Clerk"], False, False, [], "invite_redemption", "multisig_update"))
        self.assertEqual(listed["sentence"], "Moving Ada Approver’s seat to their current passkey: 0 of 2 approvers have signed. Ben Signatory and Cora Clerk may sign.")
        self.assertEqual((listed["rosterName"], listed["signingRosterName"]), (WHITELIST_ROSTER_NAME, CHANGE_ROSTER_NAME))
        ben = json.loads(steps[2]["came_back"])
        self.assertEqual(ben["sentence"], "Your signature is counted: 1 of 2 approvers have signed (Ben Signatory). Cora Clerk may still sign.")
        self.assertEqual((ben["state"], ben["maySign"], ben["rebound"], ben["signedBy"][0]["name"], ben["signedBy"][0]["credentialId"]),
                         ("awaiting", ["Cora Clerk"], None, "Ben Signatory", self.runner.people["ben"].credential_id[:8]))
        cora = json.loads(steps[4]["came_back"])
        self.assertEqual(cora["sentence"], "Your signature completed the count: 2 of 2 approvers have signed (Ben Signatory and Cora Clerk). The access platform applied the change, "
                                           "and Ada Approver’s seat on “%s” now counts their current passkey." % WHITELIST_ROSTER_NAME)
        self.assertEqual(cora["rebound"], {"email": self.ada.email, "name": "Ada Approver", "oldCredentialId": self.runner.people["harriet"].credential_id[:8],
                                           "newCredentialId": self.ada.credential_id[:8], "rosterId": "ms-whitelist-mutation-harness", "rosterName": WHITELIST_ROSTER_NAME})
        after = json.loads(steps[5]["came_back"])["changes"][0]
        self.assertEqual((after["state"], after["platformStatus"], after["callerMaySign"]), ("applied", "consumed", False))
        self.assertEqual(after["sentence"], "Ada Approver’s seat was moved to their current passkey: 2 of 2 approvers signed (Ben Signatory and Cora Clerk). "
                                            "The access platform applied the change, and their presses now count.")

    def test_s6_counts_ada_then_ben_stops_at_the_count_and_the_platform_would_refuse_cora_as_unneeded(self):
        o = self.outcomes["S6"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(o.line, "payees: Northwind Supplies: created; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted; "
                                 "Contoso Legal: created; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted; "
                                 "register: Northwind Supplies whitelisted, Contoso Legal whitelisted")
        for record in self.runner.facts["payees"]:
            self.assertEqual([(p["who"], p["status"]) for p in record["presses"]], [("Ada Approver", 200), ("Ben Signatory", 200)], "Cora is not asked")
            self.assertEqual(record["presses"][0]["answer"]["approvals"], {"required": 2, "collected": 1, "remaining": 1})
            self.assertEqual(record["register_status"], "whitelisted")
        ada_press = next(s for s in self.runner.evidence["S6"] if s["who"] == "Ada Approver" and s["route"].endswith("/approve"))
        self.assertIn("S4 moved Ada Approver's roster seat to their current credential %s (ceremony %s…), so SIGNATURE_NOT_COUNTED is a finding (Spec T15 §2)" % (
            H.last4(self.ada.credential_id), self.pending_tx_id[:8]), ada_press["expected"])
        self.assertEqual([f for f in self.runner.findings if f.station == "S6"], [])
        # had Cora been asked, the platform would have refused her as unneeded, in its own words — the count was met and the entry is active
        cora = self.runner.people["cora"]
        refused = self.runner.request(cora, "POST", "/v1/payees/addresses/%s/approve" % self.runner.facts["payees"][0]["address_id"], {}, "test")
        self.assertEqual(refused.status, 422)
        self.assertEqual(refused.refusal["code"], "ADDRESS_PROPOSAL_REFUSED")
        self.assertEqual(refused.refusal["detail"]["platformSaid"], "entry is already active")
        self.assertEqual(refused.refusal["detail"]["platformStatus"], "409")
        self.assertTrue(refused.refusal["message"].startswith("The access platform would not approve this address, so nothing was changed: the platform answered HTTP 409: entry is already active for entry "), refused.refusal["message"])
        self.assertIsNone(H.refusal_without_why(refused.status, refused.text))

    def test_s10_reads_the_trail_row_naming_every_signer_and_drops_the_note(self):
        notes = self.runner.notes["S10"]
        self.assertFalse(any("whitelist press was not counted" in n for n in notes), "nothing left to note: S4 moved the seat")
        harriet = self.runner.people["harriet"]
        self.assertTrue(any(n.startswith("the trail carries roster.seat_rebound for Ada Approver's seat: ceremony %s, signed by Ben Signatory, Cora Clerk, moved from %s to %s on %s (via roster_change), at " % (
            self.pending_tx_id, H.last4(harriet.credential_id), H.last4(self.ada.credential_id), WHITELIST_ROSTER_NAME)) for n in notes), notes)
        rows = [r for r in self.double.trail if r["action"] == T.ROSTER_SEAT_REBOUND]
        self.assertEqual(len(rows), 1)
        detail = rows[0]["detail"]
        self.assertEqual((detail["pendingTxId"], detail["seatEmail"], detail["seatName"], detail["via"], detail["requiredSignatures"], detail["signerNames"]),
                         (self.pending_tx_id, self.ada.email, "Ada Approver", "roster_change", "2", "Ben Signatory, Cora Clerk"))
        self.assertEqual(detail["signerCredentialIds"], "%s,%s" % (self.runner.people["ben"].credential_id, self.runner.people["cora"].credential_id))
        self.assertEqual((detail["oldCredentialId"], detail["newCredentialId"]), (harriet.credential_id, self.ada.credential_id))
        self.assertEqual(rows[0]["credential_id"], self.runner.people["cora"].credential_id, "written by the hand whose signature met the count")
        step = next(s for s in self.runner.evidence["S10"] if s["route"].startswith("GET /v1/export/audit"))
        self.assertEqual(step["expected"], "the trail: a roster.seat_rebound row for each seat S4 moved (Ada Approver's), naming the ceremony and every signer")
        self.assertEqual([f.probe for f in self.runner.findings if f.station == "S10"], ["read-back (policy) of A5"], "main's known finding, and no other")

    def test_every_refusal_s4_met_says_why_and_the_report_carries_the_signing_pass(self):
        for call in self.runner.calls:
            if call.station == "S4" and call.status >= 400:
                self.assertIsNone(H.refusal_without_why(call.status, call.text), call.text)
        self.assertIn("## S4 — People", self.report)
        self.assertIn("POST /v1/roster/changes/%s/sign — Ben Signatory" % self.pending_tx_id, self.report)
        self.assertIn("POST /v1/roster/changes/%s/sign — Cora Clerk" % self.pending_tx_id, self.report)
        self.assertIn("Result: counted: 2 of 2, applied", self.report)
        self.assertIn("Note: the trail carries roster.seat_rebound for Ada Approver's seat", self.report)
        self.assertEqual(self.report.count("BEGIN EC PRIVATE KEY"), 0)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AdaNotCountedAfterS4MovedHerSeatIsAFinding(unittest.TestCase):
    def test_a_signature_not_counted_for_a_person_whose_seat_s4_moved_is_a_finding_not_a_note(self):
        """Spec T15 §2: S4 moved the seat and the estate reported it applied; a platform that then answers Ada's press "not authorized" is contradicting itself, and the harness says so."""
        double, runner, outcomes, _ = four_at_two()
        ada = runner.people["ada"]
        moved = runner.facts["seats_moved"][0]
        self.assertEqual(moved["key"], "ada")
        # the platform's roster seat for Ada, bound again to a key she does not hold — the fact S6 must be able to report
        seat = next(s for s in double.whitelist_seats if s["user_id"] == ada.email)
        seat["credential_id"] = "a-key-the-platform-still-holds"
        before = len(runner.findings)
        again = runner.station_s6()
        found = [f for f in runner.findings[before:] if f.station == "S6"]
        self.assertEqual([f.probe for f in found], ["a press not counted after S4 moved the seat: Ada Approver for Northwind Supplies", "a press not counted after S4 moved the seat: Ada Approver for Contoso Legal"])
        finding = found[0]
        self.assertTrue(finding.said.startswith("not counted: SIGNATURE_NOT_COUNTED: The access platform did not count your approval: it does not recognise your key as one of this wallet’s signatories."), finding.said)
        self.assertIn("— S4 had Ben Signatory and Cora Clerk sign the move of Ada Approver's roster seat to %s (ceremony %s), and the estate reported it applied" % (H.last4(ada.credential_id), moved["pendingTxId"]), finding.said)
        self.assertIn("S4 moved Ada Approver's roster seat to their current credential %s (ceremony %s…), so SIGNATURE_NOT_COUNTED is a finding (Spec T15 §2)" % (H.last4(ada.credential_id), moved["pendingTxId"][:8]), finding.expected)
        self.assertIn('"platformSaid": "not authorized"', finding.came_back)
        self.assertIn("Ada Approver not counted (SIGNATURE_NOT_COUNTED", again.line)
        self.assertIn("Ben Signatory counted (1 of 2); Cora Clerk counted (2 of 2): whitelisted", again.line, "the roster is still pressed past the refusal, as Spec T12 has it")
        self.assertEqual(runner.seat_binding_notes(), [], "the note about a seat still bound to a retired passkey is not written for a seat S4 moved: the refusal is the finding")
        # and a refusal for a person whose seat S4 did not move stays Spec T12's note
        cora_seat = next(s for s in double.whitelist_seats if s["user_id"] == A.PEOPLE["cora"].email)
        cora_seat["credential_id"] = "another-key"
        before = len(runner.findings)
        runner.facts["payees"] = []
        runner.station_s6()
        self.assertEqual([f.probe for f in runner.findings[before:] if f.station == "S6" and "Cora" in f.probe], [], "Cora's seat S4 did not move: a note, not a finding")
        self.assertTrue(any(n.startswith("S6: Cora Clerk's whitelist press was not counted (SIGNATURE_NOT_COUNTED)") for n in runner.seat_binding_notes()), runner.seat_binding_notes())


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ATrailWithoutTheRowIsAFinding(unittest.TestCase):
    def test_s10_raises_the_finding_when_the_trail_carries_no_row_for_the_moved_seat(self):
        double, runner, outcomes, _ = four_at_two()
        pending_tx_id = runner.facts["seats_moved"][0]["pendingTxId"]
        double.trail[:] = [r for r in double.trail if r["action"] != T.ROSTER_SEAT_REBOUND]
        before = len(runner.findings)
        runner.station_s10()
        new = [f for f in runner.findings[before:] if f.probe.startswith("the trail's roster.seat_rebound row for Ada Approver's seat (ceremony %s…)" % pending_tx_id[:8])]
        self.assertEqual(len(new), 1, [f.probe for f in runner.findings[before:]])
        self.assertTrue(new[0].said.startswith("no roster.seat_rebound row names the ceremony among "), new[0].said)
        self.assertEqual(new[0].expected, "one roster.seat_rebound row with pendingTxId %s, seatEmail %s, via roster_change, and signerNames naming Ben Signatory and Cora Clerk" % (pending_tx_id, A.PEOPLE["ada"].email))
        # and a row naming another road, or not every signer, is the finding too
        double.trail.append({"audit_id": "aud-test", "at": "2026-09-22T00:00:00.000Z", "action": T.ROSTER_SEAT_REBOUND, "credential_id": "", "subject_id": WORKSPACE_ID,
                             "detail": {"pendingTxId": pending_tx_id, "seatEmail": A.PEOPLE["ada"].email, "via": "seat_grant", "signerNames": "Ben Signatory"}})
        before = len(runner.findings)
        runner.station_s10()
        wrong = [f for f in runner.findings[before:] if f.probe.startswith("the trail's roster.seat_rebound row")]
        self.assertEqual(len(wrong), 1)
        self.assertIn("via 'seat_grant'", wrong[0].said)
        self.assertIn("signerNames 'Ben Signatory' does not name Cora Clerk", wrong[0].said)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ARefusalIsReportedInThePlatformsWordsAndNotRetried(unittest.TestCase):
    def test_the_platform_refuses_coras_signature_the_second_of_the_ceremony_in_its_own_words(self):
        """The clock passes the ceremony's expiry after Ben's signature: Cora's meets the platform's "conflict: pending transaction expired", relayed as PLATFORM_REFUSED (Spec 97)."""
        double, runner, outcomes, _ = four_at_two(lapse_after_first_signature=True)
        o = self.outcomes = outcomes["S4"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        record = runner.facts["roster_signing"][0]
        sentence = ("PLATFORM_REFUSED: The access platform refused this request (HTTP 409): “conflict: pending transaction expired”. Nothing was changed, and asking again will "
                    "meet the same answer until what the platform names has changed.")
        self.assertEqual(roster_changes_of(o.line), "%s… awaiting (Ada Approver's seat, 0 of 2 signed): found awaiting at 0 of 2, Ben Signatory and Cora Clerk able to sign; "
                                                    "Ben Signatory counted (1 of 2); Cora Clerk refused (%s); nobody left to sign, and the estate did not report the change applied" % (record["pendingTxId"][:8], sentence))
        self.assertEqual([(s["who"], s["status"], s["refusal_code"]) for s in record["signatures"]], [("Ben Signatory", 200, None), ("Cora Clerk", 502, "PLATFORM_REFUSED")])
        self.assertEqual(record["outcome"], "awaiting")
        self.assertEqual(sign_calls(runner), [("Ben Signatory", 200), ("Cora Clerk", 502)], "Cora's refused signature is not retried")
        step = next(s for s in runner.evidence["S4"] if s["who"] == "Cora Clerk" and s["route"].endswith("/sign"))
        self.assertEqual(step["result"], "refused, and the refusal says why (Rule 13): %s" % sentence)
        body = json.loads(step["came_back"])
        self.assertEqual(body["error"]["detail"], {"outcome": "refused", "platformStatus": "409", "platformSaid": PLATFORM_EXPIRED, "route": "POST /v1/pending-transactions-v2/{id}/signatures"})
        self.assertEqual(runner.facts["seats_moved"], [], "nothing moved")
        # S6 then meets Ada not counted, which is a note (S4 did not move the seat), and S10 raises no Rule 13 finding for a refusal that said why
        self.assertIn("Ada Approver not counted (SIGNATURE_NOT_COUNTED", outcomes["S6"].line)
        self.assertEqual([f for f in runner.findings if f.station in ("S4", "S6")], [])
        self.assertFalse(any(f.probe.startswith("Rule 13") for f in runner.findings), [f.probe for f in runner.findings])
        self.assertTrue(any(n.startswith("S6: Ada Approver's whitelist press was not counted (SIGNATURE_NOT_COUNTED)") and "S4 found no roster change of theirs it could sign (Spec 99's door; see S4's line)" in n
                            for n in runner.notes["S10"]), runner.notes["S10"])

    def test_a_second_signature_by_the_same_person_is_refused_from_the_platforms_record_and_the_harness_never_makes_one(self):
        double, runner, outcomes, _ = four_at_two()
        pending_tx_id = runner.facts["seats_moved"][0]["pendingTxId"]
        self.assertEqual(sign_calls(runner), [("Ben Signatory", 200), ("Cora Clerk", 200)], "one signature per person")
        ben = runner.people["ben"]
        again, body = runner.sign_roster_change_as("test", ben, pending_tx_id, "Ada Approver", 2)
        self.assertIsNone(body)
        self.assertEqual(again.status, 409)
        self.assertEqual(again.refusal["code"], "APPROVER_ALREADY_SIGNED")
        collected = next(c for c in double.ceremonies if c["id"] == pending_tx_id)["collected"][0]["collected_at"]
        self.assertEqual(again.refusal["message"], "You have already signed this change: the access platform’s record of ceremony %s… carries your signature (collected %s), and it counts each "
                                                   "signatory once. 2 of 2 stand; nothing was signed again." % (pending_tx_id[:8], collected))
        self.assertEqual(again.refusal["detail"], {"pendingTxId": pending_tx_id, "credentialId": ben.credential_id, "signaturesCollected": "2", "requiredSignatures": "2", "signedAt": collected, "platformStatus": "consumed"})
        self.assertEqual(len(next(c for c in double.ceremonies if c["id"] == pending_tx_id)["collected"]), 2, "the platform was not asked to count what it has counted")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheDoubleAnswersExpired(unittest.TestCase):
    def test_expired_once_the_seat_is_granted_again_the_change_re_listed_and_signed(self):
        """Spec T15 §1: a change listed expired is reported; the move is proposed afresh — by the seat grant, the road the estate names — re-listed and signed."""
        double, runner, outcomes, _ = four_at_two(ceremony_lapses=1)
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        records = runner.facts["roster_signing"]
        self.assertEqual([(r["state_found"], r["outcome"], r["reproposed"]) for r in records], [("expired", "expired; proposed afresh", True), ("awaiting", "applied", False)])
        self.assertNotEqual(records[0]["pendingTxId"], records[1]["pendingTxId"], "the lapsed ceremony stays as the platform holds it; the grant born a fresh one")
        words = roster_changes_of(o.line)
        self.assertTrue(words.startswith("%s… expired (Ada Approver's seat, 0 of 2 signed): %s" % (records[0]["pendingTxId"][:8], EXPIRED_OPENS)), words)
        self.assertIn(EXPIRED_CLOSES + "; " + GRANTED_AGAIN + "; %s… awaiting (Ada Approver's seat, 0 of 2 signed): found awaiting at 0 of 2, Ben Signatory and Cora Clerk able to sign; "
                      "Ben Signatory counted (1 of 2); Cora Clerk counted (2 of 2); applied: the seat now names" % records[1]["pendingTxId"][:8], words)
        self.assertEqual([n for n in runner.notes["S4"] if n.startswith("roster change %s…: %s" % (records[0]["pendingTxId"][:8], EXPIRED_OPENS))].__len__(), 1, runner.notes["S4"])
        grants = [s for s in runner.evidence["S4"] if s["route"] == "POST /v1/approver-seats/grant"]
        self.assertEqual(len(grants), 1, "granted again once")
        self.assertEqual(grants[0]["sent"], {"email": A.PEOPLE["ada"].email})
        self.assertEqual(grants[0]["expected"], "the seats view, and Spec 95 proposing Ada Approver's move afresh at the seat grant — the estate proposes a move at a seat grant or a redemption, "
                                                "not at a sign-in — so the roster changes list it awaiting")
        self.assertEqual(grants[0]["result"], "granted again")
        lists = [s for s in runner.evidence["S4"] if s["route"] == "GET /v1/roster/changes"]
        self.assertEqual(len(lists), 3, "as found, after the grant, and after the count")
        self.assertEqual(lists[1]["expected"], "the roster changes after the seat was granted again: the move proposed afresh and listed awaiting, naming Ada Approver's seat")
        self.assertEqual(sign_calls(runner), [("Ben Signatory", 200), ("Cora Clerk", 200)])
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", outcomes["S6"].line)
        self.assertEqual([f for f in runner.findings if f.station in ("S4", "S6")], [])
        # the platform's record of the lapsed ceremony: pending, nothing collected, its expiry past — the state the estate read as expired
        lapsed = next(c for c in double.ceremonies if c["id"] == records[0]["pendingTxId"])
        self.assertEqual((lapsed["status"], lapsed["collected"]), ("pending", []))

    def test_a_second_expiry_fails_s4_naming_the_ceremony(self):
        double, runner, outcomes, _ = four_at_two(ceremony_lapses=2)
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        records = runner.facts["roster_signing"]
        self.assertEqual([(r["state_found"], r["outcome"]) for r in records], [("expired", "expired; proposed afresh"), ("expired", "expired")])
        self.assertTrue(roster_changes_of(o.line).endswith("%s… expired (Ada Approver's seat, 0 of 2 signed): expired again after the move was proposed afresh — S4 fails naming the ceremony %s" % (
            records[1]["pendingTxId"][:8], records[1]["pendingTxId"])), o.line)
        self.assertEqual(len([s for s in runner.evidence["S4"] if s["route"] == "POST /v1/approver-seats/grant"]), 1, "proposed afresh once, and not again")
        self.assertEqual(sign_calls(runner), [], "nothing to sign")
        self.assertEqual(runner.facts["seats_moved"], [])
        self.assertIn("Ada Approver not counted (SIGNATURE_NOT_COUNTED", outcomes["S6"].line)
        self.assertTrue(any(n.startswith("S6: Ada Approver's whitelist press was not counted (SIGNATURE_NOT_COUNTED)") for n in runner.notes["S10"]))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheEstateBeforeSpec99AndTheDayAfter(unittest.TestCase):
    """The live estate's road: the run of 13:50 met Spec 95 without Spec 99; the ceremony it holds predates the seat's row."""

    @classmethod
    def setUpClass(cls):
        cls.double, cls.second, cls.before_99, _ = four_at_two(change_roster=None, before_spec_99=True)
        cls.trail_before_99 = [r["action"] for r in cls.double.trail]
        cls.double.before_spec_99 = False
        cls.said = []
        cls.third = runner_on(cls.double, os.path.dirname(cls.second.store_dir), invite=cls.second.invite, said=cls.said)
        cls.after_99 = {o.station: o for o in cls.third.run()}

    def test_before_spec_99_the_door_is_not_open_and_s4_says_so_in_one_line(self):
        o = self.before_99["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(roster_changes_of(o.line), "the door is not open (an estate before Spec 99): /v1/roster/changes answered REQUEST_MALFORMED: That request could not be read.")
        self.assertEqual(self.second.notes["S4"], ["the estate has no door onto the roster ceremony (/v1/roster/changes answered REQUEST_MALFORMED: That request could not be read.): "
                                                    "an estate before AER 360 Spec 99, so the signing pass was not made"])
        self.assertEqual(sign_calls(self.second), [])
        self.assertIn("Ada Approver not counted (SIGNATURE_NOT_COUNTED", self.before_99["S6"].line)
        self.assertEqual(self.before_99["S6"].outcome, H.PASS, "Ben and Cora carried the count, as on 22 September")
        self.assertTrue(any(n.startswith("S6: Ada Approver's whitelist press was not counted (SIGNATURE_NOT_COUNTED)") for n in self.second.notes["S10"]))
        self.assertEqual([r for r in self.trail_before_99 if not str(r).startswith(("set.", "instruction.", "export."))], [],
                         "Spec 95 alone recorded no seat row for the ceremony it opened (S7's execution rows and its reads of the trail aside, Spec T14)")

    def test_the_ceremony_of_spec_95_is_listed_as_one_this_estate_did_not_propose_and_the_grant_proposes_the_move_afresh(self):
        o = self.after_99["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        records = self.third.facts["roster_signing"]
        old = records[0]
        self.assertEqual((old["state_found"], old["proposed_here"], old["seat"], old["outcome"]), ("awaiting", False, None, "not proposed here; proposed afresh"))
        self.assertEqual(old["sentence"], "A roster change this estate did not propose: the access platform holds ceremony %s… on “%s” as pending, 0 of 2 approvers have signed. "
                                          "This estate cannot say what it changes, so it offers no press for it here." % (old["pendingTxId"][:8], CHANGE_ROSTER_NAME))
        fresh = records[1]
        self.assertEqual((fresh["state_found"], fresh["proposed_here"], fresh["outcome"]), ("awaiting", True, "applied"))
        self.assertNotEqual(fresh["pendingTxId"], old["pendingTxId"], "Ben's and Cora's presses bound their seats since the move was proposed, so the content differs and the platform born a fresh ceremony")
        ada = self.third.people["ada"]
        words = roster_changes_of(o.line)
        self.assertIn("%s… awaiting (a roster change this estate did not propose, 0 of 2 signed): %s; %s; " % (old["pendingTxId"][:8], old["sentence"], GRANTED_AGAIN), words)
        self.assertIn("%s… awaiting (Ada Approver's seat, 0 of 2 signed): found awaiting at 0 of 2, Harriet Founder, Ada Approver, Ben Signatory and Cora Clerk able to sign; "
                      "Harriet Founder refused (CHANGE_SIGNER_NOT_ON_ROSTER: A change of who the approvers are is signed by Harriet Founder, Ada Approver, Ben Signatory and Cora Clerk; "
                      "you are not among them. Nothing was signed." % fresh["pendingTxId"][:8], words)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2); applied: the seat now names %s, Ada Approver's current credential (%s), signed by Ada Approver and Ben Signatory" % (
            ada.credential_id[:8], H.last4(ada.credential_id)), words)
        self.assertEqual(sign_calls(self.third), [("Harriet Founder", 403), ("Ada Approver", 200), ("Ben Signatory", 200)])
        self.assertEqual(len([s for s in self.third.evidence["S4"] if s["route"] == "POST /v1/approver-seats/grant"]), 1)
        self.assertEqual(self.after_99["S6"].outcome, H.PASS, self.after_99["S6"].line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", self.after_99["S6"].line)
        self.assertEqual([f for f in self.third.findings if f.station in ("S4", "S6")], [])
        self.assertTrue(any(n.startswith("the trail carries roster.seat_rebound for Ada Approver's seat: ceremony %s, signed by Ada Approver, Ben Signatory" % fresh["pendingTxId"]) for n in self.third.notes["S10"]))
        # the founder's refusal is the roster's own no, before the platform was asked: a refusal that says why, naming who may
        refused = next(s for s in self.third.evidence["S4"] if s["who"] == "Harriet Founder" and s["route"].endswith("/sign"))
        body = json.loads(refused["came_back"])["error"]
        self.assertEqual((body["detail"]["question"], body["detail"]["ceremony"], body["detail"]["members"]), ("C12C", "roster.change", "Harriet Founder, Ada Approver, Ben Signatory, Cora Clerk"))
        self.assertIsNone(H.refusal_without_why(403, refused["came_back"]))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AFreshEstateIsUnchanged(unittest.TestCase):
    def test_s4_reads_the_register_once_finds_no_change_and_says_so_in_one_line(self):
        double = EstateDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(roster_changes_of(o.line), "none awaits a signature: the register lists no roster change, so S4 did nothing new (Spec T15 §4)")
        self.assertEqual([c.route for c in runner.calls if c.station == "S4" and "/v1/roster/changes" in c.route], ["GET /v1/roster/changes"])
        self.assertEqual(runner.facts["roster_signing"], [])
        self.assertEqual(runner.facts["seats_moved"], [])
        self.assertEqual([c.route for c in runner.calls if "/v1/export/audit" in c.route and c.station in ("S4", "S10")], [], "nothing moved, so S10 does not read the trail for a seat (S7 reads it for its payments, Spec T14)")
        self.assertEqual(double.ceremonies, [])
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheDoubleTellsTheTruthAboutTheCeremony(unittest.TestCase):
    """The double against Spec 99's own tests (rosterchanges.test.ts): the refusals before the platform is asked, and the platform's own no."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(before_spec_91=True, change_roster=("ben", "cora"))
        cls.tmp = tempfile.mkdtemp()
        cls.link = cls.double.mint_founder_link()
        runner_on(cls.double, cls.tmp, invite=cls.link).run()
        cls.double.before_spec_91 = False
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.link)
        cls.runner.load_passkeys()
        for station in ("station_s1", "station_s2", "station_s3"):
            getattr(cls.runner, station)()
        cls.founder = cls.runner.people["harriet"]
        cls.ada, cls.ben, cls.olive = cls.runner.people["ada"], cls.runner.people["ben"], cls.runner.people["olive"]
        cls.runner.bring_in_on_own_credential("test", cls.ada, cls.founder)  # signed in on the shared credential, then brought in again: the redemption proposes the move
        cls.runner.bring_in_on_own_credential("test", cls.ben, cls.founder)
        cls.runner.bring_in("test", cls.olive, "viewer")
        cls.pending_tx_id = cls.double.ceremonies[0]["id"]

    def test_the_redemption_answered_the_seat_held_by_the_clients_governance_in_spec_95s_words(self):
        verified = [c for c in self.runner.calls if c.route == "POST /v1/auth/invite/verify" and c.who == "Ada Approver"][-1]
        seats = json.loads(verified.text)["rosterSeats"]
        self.assertEqual((seats["rebound"], seats["refused"], len(seats["awaiting"])), ([], None, 1))
        held = seats["awaiting"][0]
        self.assertEqual((held["pendingTxId"], held["operation"], held["requiredSignatures"], held["signaturesCollected"], held["seatEmail"]), (self.pending_tx_id, "multisig_update", 2, 0, self.ada.email))
        self.assertEqual(held["sentence"], "Ada Approver’s seat on the roster “%s” was not moved yet: your charter asks 2 people to agree to a change of who the approvers are (C12C), and the access "
                                           "platform holds that change as ceremony %s at 0 of 2. The seat stays bound to the credential it held until they agree." % (WHITELIST_ROSTER_NAME, self.pending_tx_id))
        proposed = [r for r in self.double.trail if r["action"] == T.ROSTER_CHANGE_PROPOSED]
        self.assertEqual(len(proposed), 1)
        self.assertEqual((proposed[0]["detail"]["pendingTxId"], proposed[0]["detail"]["via"], proposed[0]["detail"]["requiredSignatures"], proposed[0]["detail"]["seatEmail"]),
                         (self.pending_tx_id, "invite_redemption", "2", self.ada.email))

    def test_a_viewer_nobody_the_census_names_is_refused_in_the_rosters_words_before_the_platform_is_asked(self):
        refused, body = self.runner.sign_roster_change_as("test", self.olive, self.pending_tx_id, "Ada Approver", 2)
        self.assertIsNone(body)
        self.assertEqual(refused.status, 403)
        self.assertEqual(refused.refusal["code"], "CHANGE_SIGNER_NOT_ON_ROSTER")
        self.assertEqual(refused.refusal["message"], "A change of who the approvers are is signed by Ben Signatory and Cora Clerk; you are not among them. Nothing was signed.")
        detail = refused.refusal["detail"]
        self.assertEqual((detail["roster"], detail["purpose"], detail["question"], detail["members"], detail["credentialId"], detail["addresses"]),
                         (CHANGE_ROSTER_NAME, "multisig_mutation", "C12C", "Ben Signatory, Cora Clerk", self.olive.credential_id, self.olive.email))
        self.assertEqual(self.double.ceremonies[0]["collected"], [], "the platform was not asked")
        # Ada may not sign her own move: the census does not seat her here
        listed = self.runner.request(self.ada, "GET", "/v1/roster/changes", None, "test").json["changes"][0]
        self.assertEqual((listed["callerMaySign"], listed["maySign"]), (False, ["Ben Signatory", "Cora Clerk"]))
        own, body = self.runner.sign_roster_change_as("test", self.ada, self.pending_tx_id, "Ada Approver", 2)
        self.assertEqual((own.status, own.refusal["code"]), (403, "CHANGE_SIGNER_NOT_ON_ROSTER"))

    def test_a_ceremony_no_seat_row_names_is_a_roster_change_this_estate_did_not_propose_and_cannot_be_signed_here(self):
        foreign = dict(self.double.born_ceremony(self.double.rosters()[1], "no-such-content"), operation="multisig_delete")
        self.double.ceremonies.append(foreign)
        try:
            listed = next(c for c in self.runner.request(self.ben, "GET", "/v1/roster/changes", None, "test").json["changes"] if c["pendingTxId"] == foreign["id"])
            self.assertEqual((listed["operation"], listed["proposedHere"], listed["seat"], listed["rosterId"], listed["state"], listed["callerMaySign"], listed["maySign"]),
                             (None, False, None, None, "awaiting", False, ["Ben Signatory", "Cora Clerk"]))
            self.assertEqual(listed["sentence"], "A roster change this estate did not propose: the access platform holds ceremony %s… on “%s” as pending, 0 of 2 approvers have signed. "
                                                 "This estate cannot say what it changes, so it offers no press for it here." % (foreign["id"][:8], CHANGE_ROSTER_NAME))
            refused, body = self.runner.sign_roster_change_as("test", self.ben, foreign["id"], "somebody", 2)
            self.assertEqual((refused.status, refused.refusal["code"]), (404, "ROSTER_CHANGE_UNKNOWN"))
            self.assertEqual(refused.refusal["message"], MESSAGES["ROSTER_CHANGE_UNKNOWN"])
            self.assertEqual(refused.refusal["detail"], {"pendingTxId": foreign["id"], "cause": "not_proposed_here"})
            self.assertEqual(foreign["collected"], [])
        finally:
            self.double.ceremonies.remove(foreign)

    def test_a_step_up_of_another_purpose_is_refused_as_a_step_up(self):
        opened = self.runner.request(self.ben, "POST", T.ROSTER_CHANGE_SIGN_OPTIONS_ROUTE % self.pending_tx_id, {}, "test")
        self.assertEqual(opened.status, 200)
        issued = opened.json["issuedAtMs"]
        wrong_purpose = self.double.challenge(FUNDING_WALLET_PURPOSE, "%s|%s" % (T.ROSTER_CHANGE_BINDING % (WORKSPACE_ID, self.pending_tx_id, issued), self.ben.credential_id), 0)
        assertion = self.runner.assertion_for(self.ben, wrong_purpose, "test")
        refused = self.runner.request(self.ben, "POST", T.ROSTER_CHANGE_SIGN_ROUTE % self.pending_tx_id, {"issuedAtMs": issued, "response": assertion}, "test", retry=False)
        self.assertEqual((refused.status, refused.refusal["code"]), (403, "STEP_UP_INVALID"))
        self.assertEqual(self.double.ceremonies[0]["collected"], [])

    def test_the_platforms_own_no_travels_in_its_words_where_the_ceremony_lapsed(self):
        record = self.double.ceremonies[0]
        kept = (record["expiresAtEpoch"], record["expiresAt"])
        record["expiresAtEpoch"] = kept[0] - 2 * 24 * 3600
        record["expiresAt"] = self.double._iso(record["expiresAtEpoch"])
        try:
            listed = self.runner.request(self.ben, "GET", "/v1/roster/changes", None, "test").json["changes"][0]
            self.assertEqual((listed["state"], listed["platformStatus"], listed["callerMaySign"]), ("expired", "pending", False))
            self.assertTrue(listed["sentence"].startswith(EXPIRED_OPENS) and listed["sentence"].endswith(EXPIRED_CLOSES), listed["sentence"])
            refused, body = self.runner.sign_roster_change_as("test", self.ben, self.pending_tx_id, "Ada Approver", 2)
            self.assertEqual((refused.status, refused.refusal["code"]), (502, "PLATFORM_REFUSED"))
            self.assertEqual(refused.refusal["message"], "The access platform refused this request (HTTP 409): “%s”. Nothing was changed, and asking again will meet the same answer until what the "
                                                         "platform names has changed." % PLATFORM_EXPIRED)
            self.assertNotIn("could not be reached", refused.refusal["message"])
            self.assertEqual(record["collected"], [])
        finally:
            record["expiresAtEpoch"], record["expiresAt"] = kept

    def test_a_signer_the_platform_does_not_count_is_signature_not_counted_with_the_platforms_words(self):
        seat = next(s for s in self.double.change_seats if s["user_id"] == self.ben.email)
        seat["credential_id"] = "a-key-ben-no-longer-holds"
        try:
            refused, body = self.runner.sign_roster_change_as("test", self.ben, self.pending_tx_id, "Ada Approver", 2)
            self.assertEqual((refused.status, refused.refusal["code"]), (403, "SIGNATURE_NOT_COUNTED"))
            self.assertEqual(refused.refusal["message"], MESSAGES["SIGNATURE_NOT_COUNTED"])
            self.assertEqual((refused.refusal["detail"]["platformSaid"], refused.refusal["detail"]["platformStatus"], refused.refusal["detail"]["roster"]), (PLATFORM_NOT_AUTHORIZED_SENTENCE, "403", CHANGE_ROSTER_NAME))
            self.assertEqual(self.double.ceremonies[0]["collected"], [])
        finally:
            seat["credential_id"] = ""


class TheTablesNameTheRoadsAsTheEstateSpellsThem(unittest.TestCase):
    def test_the_two_roads_the_step_up_purpose_and_the_trails_verb(self):
        self.assertEqual(T.ROSTER_CHANGES_ROUTE, "/v1/roster/changes")
        self.assertEqual(T.ROSTER_CHANGE_SIGN_ROUTE % "abc", "/v1/roster/changes/abc/sign")
        self.assertEqual(T.ROSTER_CHANGE_SIGN_OPTIONS_ROUTE % "abc", "/v1/roster/changes/abc/sign/options")
        self.assertEqual(T.ROSTER_CHANGE_PURPOSE, "roster.change")
        self.assertEqual(T.ROSTER_CHANGE_BINDING % ("ws", "ptx", "1"), "roster-change:ws:ptx:1")
        self.assertEqual(T.ROSTER_SEAT_REBOUND, "roster.seat_rebound", "the estate's verb, with an underscore; SPEC.md writes roster.seat.rebound")
        self.assertEqual(T.ROSTER_CHANGE_PROPOSED, "roster.change_proposed")
        self.assertEqual(T.VIA_ROSTER_CHANGE, "roster_change")
        self.assertEqual(T.ROSTER_CHANGE_STATES, ("awaiting", "approved", "applied", "expired", "closed"))
        self.assertEqual((T.AUDIT_EXPORT_ROUTE, T.AUDIT_EXPORT_LIMIT), ("/v1/export/audit", 5000))
        self.assertEqual(T.credential_short_form("6287746f-ecbe-414c-8965-3a6d6212fcb6"), "6287746f")
        self.assertEqual(T.credential_short_form(None), "")




# ---------------------------------------------------------------------------
# Spec T17 (23 September 2026): S4 grants a stale seat again before signing, one at a time, and S6 counts Ada.
# The estate at AER 360 Spec 105: the seat view reads the roster, so GET /v1/approver-seats carries onRoster. In substance T15 §1
# gains a grant step — a stale seat (onRoster false) is granted again to propose the move, then T15's pass signs it as the persons
# whose own seat reads onRoster true.
# ---------------------------------------------------------------------------
def stale_seat_estate(change_roster=("ben", "cora"), clear_changes=False, **dials):
    """
    Harness Holdings on the day Spec 105 is live. The first run binds Ada's whitelist seat to the shared credential (before Spec 91);
    Specs 91, 95, 99 and 105 deploy; a second runner signs everyone in on their own credential and re-grants Ada's seat (Spec T10).
    Returns the double and that second runner with S1–S3 and the bring-in done, ready for S4's grant step. With clear_changes the
    ceremony Ada's re-invitation proposed is swept, modelling the live finding: her seat is stale but no ceremony is on record.
    """
    double = EstateDouble(before_spec_91=True, change_roster=change_roster)
    tmp = tempfile.mkdtemp()
    link = double.mint_founder_link()
    runner_on(double, tmp, invite=link).run()
    double.before_spec_91 = False
    for name, value in dials.items():
        setattr(double, name, value)
    runner = runner_on(double, tmp, invite=link)
    runner.load_passkeys()
    for station in ("station_s1", "station_s2", "station_s3"):
        getattr(runner, station)()
    founder = runner.people["harriet"]
    for key in A.AUTHORS_INVITED:
        runner.bring_in_on_own_credential("S4", runner.people[key], founder)
    runner.seat_on_own_credential("S4", founder, runner.people["ada"], "found")
    if clear_changes:
        double.ceremonies = []  # the day Spec 105 is live: the seat is stale, and no ceremony for the move is on record (the finding)
    return double, runner, founder


def onroster_seats(runner, ada="compute", ben=True, cora=True):
    """The seats view Spec 105 answers: Ada's onRoster computed from the live roster (so it flips the moment the move applies), Ben's and Cora's as given."""
    def spec(key, onr):
        person = runner.people[key]
        return {"email": person.email, "name": person.name, "state": "seated", "credentialId": person.credential_id, "onRoster": onr}
    return [spec("ada", ada), spec("ben", ben), spec("cora", cora)]


def _grants_after(runner, before):
    return [c for c in runner.calls[before:] if c.route == "POST /v1/approver-seats/grant"]


def _signs_after(runner, before):
    return [c for c in runner.calls[before:] if c.route.endswith("/sign")]


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S4GrantsAStaleSeatAgainThenSignsIt(unittest.TestCase):
    """Spec T17 §1 and §2: Ada onRoster false, Ben and Cora true, and the changes list empty — S4 grants Ada's seat, Ben and Cora sign, the seat reads true."""

    def test_one_seat_ada_false_ben_and_cora_able_on_the_lists_word_the_grant_then_the_signatures_the_seat_reads_true(self):
        """
        Spec T17 §2, on Harness Holdings' own shape (amended 23 September 2026): the seats view carries ONE seat — Ada's, onRoster false,
        because the charter seats only Ada under C11 — while the whitelist roster carries Ada, Ben and Cora, so the change's maySign names
        Ben and Cora after the grant. Ben and Cora have no seat row, so they are able on the list's word alone; S4 grants Ada's seat,
        they sign, and Ada's seat reads on the roster.
        """
        double, runner, founder = stale_seat_estate(clear_changes=True)  # change_roster ("ben","cora"): maySign is Ben and Cora
        ada = runner.people["ada"]
        # ONE seat in the view, Ada's — as GET /v1/approver-seats answers charterApprovers (C11) on Harness Holdings; Ben and Cora are on
        # the roster but not on the seats view, so the harness reads no onRoster for them and takes the list's word that they may sign.
        double.seats_override = [{"email": ada.email, "name": ada.name, "state": "seated", "credentialId": ada.credential_id, "onRoster": "compute"}]
        self.assertEqual(double.ceremonies, [], "no ceremony is on record for the move")
        f_before, before = len(runner.findings), len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertTrue(ok, (grant_said, changes_said))
        grants, signs = _grants_after(runner, before), _signs_after(runner, before)
        self.assertEqual(len(grants), 1, "one grant, for Ada's seat")
        self.assertEqual(grants[0].sent, {"email": ada.email})
        first_grant = next(i for i, c in enumerate(runner.calls[before:]) if c.route == "POST /v1/approver-seats/grant")
        first_sign = next(i for i, c in enumerate(runner.calls[before:]) if c.route.endswith("/sign"))
        self.assertLess(first_grant, first_sign, "the double records the grant before any sign call")
        self.assertEqual([(c.who, c.status) for c in signs], [("Ben Signatory", 200), ("Cora Clerk", 200)], "sign calls as Ben and Cora, able on the list's word (no seat row of their own)")
        self.assertIn("Ada Approver's seat: granted again", grant_said)
        self.assertIn("found awaiting at 0 of 2, Ben Signatory and Cora Clerk able to sign", changes_said)
        self.assertIn("moved: Ada Approver's seat now reads on the roster, signed by Ben Signatory and Cora Clerk", changes_said)
        self.assertEqual([m["key"] for m in runner.facts["seats_moved"]], ["ada"])
        self.assertEqual(next(s for s in double.whitelist_seats if s["user_id"] == ada.email)["credential_id"], ada.credential_id, "the platform moved the seat")
        self.assertEqual([f for f in runner.findings[f_before:] if f.station == "S4"], [])

    def test_a_second_view_still_false_fails_s4_naming_ada_with_the_count(self):
        double, runner, founder = stale_seat_estate(clear_changes=True)
        double.seats_override = onroster_seats(runner, ada=False)  # the estate's seat view still reads false after the count
        f_before, before = len(runner.findings), len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertFalse(ok, (grant_said, changes_said))
        self.assertEqual(len(_grants_after(runner, before)), 1, "Ada's seat was granted")
        self.assertEqual([(c.who, c.status) for c in _signs_after(runner, before)], [("Ben Signatory", 200), ("Cora Clerk", 200)], "the count was met")
        self.assertIn("Ada Approver's seat did not read on the roster: 2 of 2 signatures", changes_said)
        found = [f for f in runner.findings[f_before:] if f.station == "S4"]
        self.assertEqual([f.probe for f in found], ["roster change: Ada Approver's seat after the count"])
        self.assertIn("did not read on the roster after the count: 2 of 2 signatures", found[0].said)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AChangeAlreadyAwaitsSoS4DoesNotGrant(unittest.TestCase):
    def test_zero_grants_the_line_and_the_signing_as_today(self):
        """Spec T17 §1: the changes list already carries an awaiting change for Ada — zero grants, the line, and T15's signing as today."""
        double, runner, founder = stale_seat_estate()  # Ada's re-invitation left an awaiting change; not cleared
        ada = runner.people["ada"]
        self.assertTrue(any(c["purpose"] == "multisig_mutation" for c in double.ceremonies), "a change awaits for Ada")
        double.seats_override = onroster_seats(runner)  # Ada compute (false), Ben and Cora true
        f_before, before = len(runner.findings), len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertTrue(ok, (grant_said, changes_said))
        self.assertEqual(_grants_after(runner, before), [], "zero grants: a change already awaits")
        self.assertIn("Ada Approver's seat: a change already awaits; not granted", grant_said)
        self.assertEqual([(c.who, c.status) for c in _signs_after(runner, before)], [("Ben Signatory", 200), ("Cora Clerk", 200)])
        self.assertIn("moved: Ada Approver's seat now reads on the roster", changes_said)
        self.assertEqual([m["key"] for m in runner.facts["seats_moved"]], ["ada"])
        self.assertEqual([f for f in runner.findings[f_before:] if f.station == "S4"], [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class FewerAbleThanTheCountFailsAfterOneGrant(unittest.TestCase):
    def test_ada_and_ben_both_false_two_required_one_able_no_second_grant(self):
        """Spec T17 §2: Ada and Ben both false on a roster requiring two — S4 fails "2 required, 1 able" after one grant, and grants no further seat."""
        double, runner, founder = stale_seat_estate(clear_changes=True)
        double.seats_override = onroster_seats(runner, ada="compute", ben=False, cora=True)  # only Cora can sign
        before = len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertFalse(ok, (grant_said, changes_said))
        self.assertEqual(len(_grants_after(runner, before)), 1, "one grant, for Ada's seat; the count fell short, so Ben's seat is not granted")
        self.assertEqual(_grants_after(runner, before)[0].sent, {"email": runner.people["ada"].email})
        self.assertEqual(_signs_after(runner, before), [], "no signature: the count could never be met")
        self.assertIn("2 required, 1 able", changes_said)
        self.assertEqual(runner.facts["seats_moved"], [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheSeatsThatArePrintedButNotGranted(unittest.TestCase):
    def test_a_stranger_an_ambiguous_and_a_null_seat_zero_grants_each_line(self):
        """Spec T17 §1: a stranger's stale seat, an ambiguous seat, and a null seat — zero grants, each with its own line."""
        double, runner, founder = stale_seat_estate(clear_changes=True)
        double.seats_override = [
            {"email": "outsider@example.com", "name": "An Outsider", "state": "seated", "credentialId": "cred-outsider", "onRoster": False},
            {"email": runner.people["ben"].email, "name": "Ben Signatory", "state": "seated", "credentialId": None, "ambiguous": True, "onRoster": None},
            {"email": runner.people["cora"].email, "name": "Cora Clerk", "state": "seated", "credentialId": "cred-cora", "onRoster": None, "rosterSaid": "no roster names this person"},
        ]
        before = len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertEqual(_grants_after(runner, before), [], "zero grants")
        self.assertEqual(_signs_after(runner, before), [], "nothing signed")
        self.assertIn("An Outsider's seat: not of the harness; not granted", grant_said)
        self.assertIn("Ben Signatory's seat: two passkeys enrolled; not granted", grant_said)
        self.assertIn("Cora Clerk's seat: unverified: no roster names this person", grant_said)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AChangeToACredentialTheHarnessDoesNotHoldIsNotSigned(unittest.TestCase):
    def test_the_target_is_not_a_stored_passkey_a_finding_not_signed(self):
        """Spec T17 §2: a change whose target credential is not the seat person's stored passkey is not signed, and it is the finding."""
        double, runner, founder = stale_seat_estate()  # a change awaits for Ada
        ada = runner.people["ada"]
        for row in double.trail:  # bend the recorded proposal so the change moves Ada's seat to a credential the harness never held
            if row["action"] == T.ROSTER_CHANGE_PROPOSED and str(row["detail"].get("seatEmail") or "").lower() == ada.email.lower():
                row["detail"]["newCredentialId"] = "a-credential-the-harness-never-held"
        double.seats_override = onroster_seats(runner)  # Ada compute (false), Ben and Cora true
        f_before, before = len(runner.findings), len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertFalse(ok, (grant_said, changes_said))
        self.assertEqual(_signs_after(runner, before), [], "not signed")
        self.assertEqual(runner.facts["seats_moved"], [])
        found = [f for f in runner.findings[f_before:] if f.station == "S4"]
        self.assertEqual(len(found), 1, [f.probe for f in found])
        self.assertIn("moves Ada Approver's seat to a credential the harness does not hold; not signed", found[0].said)
        self.assertIn("moves Ada Approver's seat to a credential the harness does not hold; not signed", changes_said)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AGrantThatMovesTheSeatAtOnce(unittest.TestCase):
    def test_no_pendingtxid_is_moved_at_once_no_sign_call_and_the_seat_is_re_read(self):
        """Spec T17 §1: a grant whose answer carries no pendingTxId — the move applied at once — prints "moved at once", skips the signing, and re-reads the seat."""
        double, runner, founder = stale_seat_estate(clear_changes=True)
        double.change_threshold = 1  # a change of one signature applies at once at the platform: no ceremony, no pendingTxId
        double.seats_override = onroster_seats(runner)  # Ada compute
        before = len(runner.calls)
        grant_said, changes_said, ok = runner.sign_the_roster_changes("S4", founder)
        self.assertTrue(ok, (grant_said, changes_said))
        self.assertEqual(len(_grants_after(runner, before)), 1, "one grant")
        self.assertEqual(_signs_after(runner, before), [], "no sign call: the move was applied at once")
        self.assertIn("moved at once", grant_said)
        self.assertIn("moved: Ada Approver's seat now reads on the roster", changes_said)
        self.assertTrue(any(c.route == "GET /v1/approver-seats" for c in runner.calls[before:]), "the seat was re-read")
        self.assertEqual(next(s for s in double.whitelist_seats if s["user_id"] == runner.people["ada"].email)["credential_id"], runner.people["ada"].credential_id)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AnEstateWithoutOnRosterBehavesAsT15(unittest.TestCase):
    def test_s4_prints_the_skipping_line_and_behaves_as_t15(self):
        """Spec T17 §0: against an estate whose seat view has no onRoster, S4 prints one line and behaves as T15 (the four-at-two, its awaiting change signed by Ben and Cora)."""
        double, runner, outcomes, _ = four_at_two()  # no seats_override: the seat view carries no onRoster
        o = outcomes["S4"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("the seat view has no onRoster; skipping", o.line)
        self.assertEqual(sign_calls(runner), [("Ben Signatory", 200), ("Cora Clerk", 200)], "T15's pass, unchanged")
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", outcomes["S6"].line)


if __name__ == "__main__":
    unittest.main()
