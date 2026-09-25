"""
Spec T19 (25 September 2026): the harness reaches the wait with a quorum of two, signs as two people, and a scenario that stops at its
first line says so in red — from the record of a customer estate on 24 September (eleven presses of Finish the write, each answered the
platform's 409 on the creation of the account's approved-destinations list) and from AER 360 Spec 109 as built (aeredium/AERAccounts,
commit e2dcc6e). Each test here was red on main.

The fixture (tests/fixtures/aer360-write-waits-for-approvals.json) is Spec 109's own recorded payloads — the 202, the ceremonies read for
A, B and a viewer, the sign bodies, the finish, the audit rows of a two-person finish, the card's sentences and the refusals — with the
harness's people in place of the suite's; S14's judgments are driven by it with no double and no network, and the double's answers are
held to its fields and its sentences. The double is the estate at Spec 109 (tests/test_aer360_double.py): a wallet-account write opens a
platform account with its own whitelist_mutation roster at WQ's count, the list's creation is governed on it, the compile answers 202,
GET /v1/onboarding/ceremonies says who has not signed, and the approvers sign it where they stand under their own passkeys.
"""
import codecs
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import EstateDouble, MUTATION_CEREMONY_REQUIRED, interview_ceremony_sentence, runner_on  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "aer360-write-waits-for-approvals.json")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The two identifiers of the customer estate the spec was written from — its workspace and its ceremony — rot13 so this file does not carry
# them either (the way tests/test_the_harness_names_no_real_tester.py carries its two names). No tracked file may carry them.
CUSTOMER_IDENTIFIERS = tuple(codecs.decode(word, "rot13") for word in ("0nnqrpn0", "ns1o4oro"))
NAME = A.APPROVALS_ACCOUNT_NAME
APPROVERS = [A.PEOPLE[k].name for k in A.APPROVALS_APPROVERS]
RED_CELL = '<span style="color:red">%s</span>' % H.FAILED_PREREQUISITE


def load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def tracked_files():
    """Every file the repository carries, as git lists them; a checkout without git is walked instead."""
    try:
        listed = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], check=True, capture_output=True).stdout
        return sorted(part.decode("utf-8") for part in listed.split(b"\0") if part)
    except (OSError, subprocess.CalledProcessError):
        paths = []
        for folder, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            paths.extend(os.path.relpath(os.path.join(folder, name), ROOT) for name in files)
        return sorted(paths)


def run_against(tmp=None, said=None, **double_kwargs):
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tmp or tempfile.mkdtemp(), invite=double.mint_founder_link(), said=said)
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes


def seed_a_write_that_waits(double=None, tmp=None):
    """
    An estate where the approvals account stands awaiting: S1 to S5 walked (the people brought in on their own credentials, the Operating
    account written, the funding wallet born), then S14's own walk to its 202 — and nothing signed. Returns the double, the store, the
    seeding runner and the interview's id.
    """
    double = double or EstateDouble()
    tmp = tmp or tempfile.mkdtemp()
    runner = runner_on(double, tmp, invite=double.mint_founder_link())
    for station, title in H.STATIONS[:5]:
        outcome = runner.run_station(station, title)
        assert outcome.outcome == H.PASS, outcome.line
    record = {}
    interview_id, view, _ = runner.walk_the_approvals_account("S14", runner.founder(), record)
    assert view.get("state") == "awaiting", view
    return double, tmp, runner, interview_id


def list_ceremony_of(double, interview_id):
    receipt = double.interviews[interview_id].get("writeReceipt") or {}
    pending = (receipt.get("whitelistCeremony") or {}).get("pendingTxId")
    return next(c for c in double.ceremonies if c["id"] == pending)


def approvals_accounts_of(double):
    return [iv for iv in double.interviews.values() if iv["interviewType"] == "wallet_account" and (iv.get("compiledCharter") or {}).get("name") == NAME]


class TheFixtureIsSpec109sOwnRecord(unittest.TestCase):
    """S14's judgments, driven by the payloads Spec 109's suite recorded — no double, no network."""

    def setUp(self):
        self.f = load_fixture()
        self.iv = self.f["the_202"]["body"]["interviewId"]
        self.tx = self.f["the_202"]["body"]["ceremonies"][0]["pendingTxId"]

    def test_the_fixture_names_no_customer_and_only_the_harnesss_people(self):
        text = json.dumps(self.f, ensure_ascii=False).lower()
        for own in ("harriet founder", "ada approver", "ben signatory", "olive overseer", "harness+ada@aeredium.io", NAME.lower()):
            self.assertIn(own, text, own)
        self.assertNotIn("example", text.replace("olive", ""), "no address of the suite's travels here")
        # the customer estate's workspace and ceremony identifiers are absent from the fixture, from this file, and from every tracked file
        for identifier in CUSTOMER_IDENTIFIERS:
            self.assertNotIn(identifier, text, "the fixture carries an identifier of the customer estate")
        with open(os.path.abspath(__file__), "r", encoding="utf-8") as handle:
            own_source = handle.read().lower()
        for identifier in CUSTOMER_IDENTIFIERS:
            self.assertNotIn(identifier, own_source, "this test carries the identifier it guards against")
        for path in tracked_files():
            with open(os.path.join(ROOT, path), "rb") as handle:
                content = handle.read().decode("utf-8", "replace").lower()
            for identifier in CUSTOMER_IDENTIFIERS:
                self.assertNotIn(identifier, content, "%s carries an identifier of the customer estate" % path)

    def test_the_202_is_a_wait_at_0_of_2_with_both_approvers_among_those_who_may_sign(self):
        body = self.f["the_202"]["body"]
        self.assertEqual(self.f["the_202"]["status"], 202)
        self.assertEqual(body["state"], T.INTERVIEW_AWAITING_APPROVALS)
        self.assertNotIn("charter", body)
        self.assertNotIn("receipt", body)
        view = body["ceremonies"][0]
        self.assertEqual(H.audit_the_wait(view, 2, APPROVERS, 0), [])
        self.assertEqual(view["listName"], NAME + T.APPROVED_DESTINATIONS_SUFFIX)
        self.assertEqual(T.account_name_of_list(view["listName"]), NAME)
        # the judgment sees a write that did not wait, a count that is not WQ's, an approver missing from maySign, a count already moved, a sentence not the table's
        for broken, probes in ((dict(view, state="approved"), ["the ceremony's state"]), (dict(view, maySign=["Harriet Founder"]), ["who may sign", "who may sign"]),  # one per approver missing
                               (dict(view, sentence="Waiting."), ["the card's sentence"]),
                               # a count the estate's own sentence no longer agrees with is two findings: the count, and the sentence beside it
                               (dict(view, requiredSignatures=1), ["the ceremony's count", "the card's sentence"]),
                               (dict(view, signaturesCollected=1), ["the signatures collected", "the card's sentence"])):
            self.assertEqual([p["probe"] for p in H.audit_the_wait(broken, 2, APPROVERS, 0)], probes, probes)
        # a count an earlier run left is accepted as found
        self.assertEqual(H.audit_the_wait(dict(view, signaturesCollected=1, sentence=view["sentence"].replace("0 of 2", "1 of 2")), 2, APPROVERS, None), [])

    def test_the_reads_for_a_b_and_a_viewer(self):
        reads = self.f["the_reads"]
        self.assertEqual(H.audit_the_reader(reads["ada"], "Ada Approver", True, False), [])
        self.assertEqual(H.audit_the_reader(reads["ben"], "Ben Signatory", True, False), [])
        self.assertEqual(H.audit_the_reader(reads["olive"], "Olive Overseer", False, False), [])
        self.assertEqual(reads["another_workspace"], {"ceremonies": []}, "another workspace's interview is absent by construction")
        self.assertEqual([p["probe"] for p in H.audit_the_reader(reads["olive"], "Olive Overseer", True, False)],
                         ["Olive Overseer's read: callerMaySign", "Olive Overseer's read: callerName"], "a viewer read as able")
        self.assertEqual([p["probe"] for p in H.audit_the_reader(reads["ada"], "Ada Approver", False, False)], ["Ada Approver's read: callerMaySign", "Ada Approver's read: callerName"], "an approver read as unable")
        self.assertEqual([p["probe"] for p in H.audit_the_reader(dict(reads["ada"], callerName="Ada"), "Ada Approver", True, False)], ["Ada Approver's read: callerName"], "a name the roster does not show")
        for who, view in (("ada", reads["ada"]), ("ben", reads["ben"])):
            self.assertEqual(view["sentence"], self.f["the_sentences_as_rendered"]["awaiting_may_sign"], who)
        self.assertEqual(reads["olive"]["sentence"], self.f["the_sentences_as_rendered"]["awaiting_not_on_roster"])

    def test_a_signed_reads_1_of_2_and_has_signed_and_her_second_press_is_refused_from_the_record(self):
        after = self.f["ada_signed"]["body"]["ceremonies"][0]
        self.assertEqual(self.f["ada_signed"]["body"]["state"], T.INTERVIEW_AWAITING_APPROVALS)
        self.assertEqual(H.audit_the_wait(after, 2, APPROVERS, 1), [])
        self.assertEqual(H.audit_the_reader(after, "Ada Approver", False, True), [])
        self.assertEqual(after["sentence"], self.f["the_sentences_as_rendered"]["awaiting_has_signed"])
        again = self.f["ada_again"]
        self.assertEqual((again["status"], again["body"]["error"]["code"]), (409, H.APPROVER_ALREADY_SIGNED))
        self.assertIn("1 of 2 stand; nothing was signed again.", again["body"]["error"]["message"])
        # every refusal Spec 109 records says why (Rule 13, as S10 judges them)
        for key, code, status in (("ada_again", H.APPROVER_ALREADY_SIGNED, 409), ("olive_signs", H.SIGNATURE_NOT_COUNTED, 403),
                                  ("a_wrong_id", T.CEREMONY_NOT_LISTED, 404), ("a_reopened_interview", T.CEREMONY_NOT_LISTED, 404)):
            refusal = self.f[key]
            self.assertEqual((refusal["status"], refusal["body"]["error"]["code"]), (status, code), key)
            self.assertIsNone(H.refusal_without_why(refusal["status"], json.dumps(refusal["body"])), key)
        self.assertEqual(self.f["olive_signs"]["body"]["error"]["message"], "This list is created by Ada Approver, Ben Signatory and Harriet Founder; you are not among them. Nothing was signed.")
        self.assertEqual(self.f["a_wrong_id"]["body"]["error"]["detail"]["cause"], "not on this interview")
        self.assertEqual(self.f["a_reopened_interview"]["body"]["error"]["detail"]["cause"], "the author is changing this interview; signing waits until it is confirmed and compiled again")

    def test_the_finish_is_one_written_row_pressed_by_b_two_signatures_and_no_second_wallet(self):
        rows = self.f["the_audit_rows"]
        trail = rows["awaiting"] + rows["signed"] + rows["written"] + rows["wallet_born"] + rows["failed"]
        creds = self.f["the_credentials"]
        self.assertEqual(self.f["ben_signed"]["body"], {"state": "written", "interviewId": self.iv, "ceremonies": []})
        self.assertEqual(H.audit_the_finish(trail, self.iv, self.tx, [creds["ada"], creds["ben"]], creds["ben"]), [])
        written = rows["written"][0]
        broken = [
            (trail + [written], "the trail's %s rows for the interview" % T.INTERVIEW_WRITTEN),
            (rows["awaiting"] + rows["signed"] + [dict(written, credential_id=creds["author"], detail=dict(written["detail"], pressedBy=creds["author"]))],
             "the %s row's credentialId" % T.INTERVIEW_WRITTEN),
            (rows["awaiting"] + rows["signed"][:1] + rows["written"], "the trail's %s rows for the ceremony" % T.CEREMONY_SIGNED),
            (rows["signed"] + rows["written"], "the trail's %s rows for the interview" % T.WRITE_AWAITING_APPROVALS),
            (trail + [{"credential_id": creds["author"], "action": T.INTERVIEW_WRITE_FAILED, "detail": {"interviewId": self.iv, "cause": "AAP POST /v1/whitelists-v2 failed (HTTP 409): …"}}],
             "the trail's %s rows for the interview" % T.INTERVIEW_WRITE_FAILED),
            (trail + rows["wallet_born"], "the trail's %s rows" % T.WALLET_BORN),
        ]
        for rows_broken, probe in broken:
            probes = [p["probe"] for p in H.audit_the_finish(rows_broken, self.iv, self.tx, [creds["ada"], creds["ben"]], creds["ben"])]
            self.assertIn(probe, probes, probe)

    def test_the_doubles_sentences_are_the_estates_and_its_answers_carry_the_estates_fields(self):
        reads = self.f["the_reads"]
        for key in ("the_author", "ada", "ben", "olive"):
            self.assertEqual(interview_ceremony_sentence(reads[key]), reads[key]["sentence"], key)
        after = self.f["ada_signed"]["body"]["ceremonies"][0]
        self.assertEqual(interview_ceremony_sentence(after), after["sentence"])
        for key in ("expired", "closed"):
            self.assertEqual(interview_ceremony_sentence(self.f["the_lapse"][key]), self.f["the_lapse"][key]["sentence"], key)
        sentences = self.f["the_sentences_as_rendered"]
        approved = dict(after, state="approved")
        self.assertEqual(interview_ceremony_sentence(dict(approved, callerIsAuthor=True)), sentences["approved_author"])
        self.assertEqual(interview_ceremony_sentence(dict(approved, callerIsAuthor=False)), sentences["approved_other"])
        self.assertEqual(interview_ceremony_sentence(dict(self.f["the_lapse"]["expired"], callerIsAuthor=True)), sentences["expired_author"])
        self.assertEqual(MUTATION_CEREMONY_REQUIRED % (0, 2, "4e1d9c07"), "mutation requires multisig approval: whitelist_modify requires 0/2 approvals (pending_tx_id=4e1d9c07)")
        # a live run's 202 carries exactly the fields Spec 109 recorded
        double, runner, outcomes = run_against()
        view = runner.facts["awaiting"]["wait"]["ceremonies"][0]
        self.assertEqual(set(view), set(self.f["the_202"]["body"]["ceremonies"][0]))
        self.assertEqual(set(runner.facts["awaiting"]["wait"]), set(self.f["the_202"]["body"]))
        signed = [c for c in runner.calls if c.station == "S14" and c.route.endswith("/sign") and c.status == 200]
        self.assertEqual(set(json.loads(signed[0].text)["ceremonies"][0]), set(after))
        self.assertEqual(json.loads(signed[-1].text), {"state": "written", "interviewId": runner.facts["awaiting"]["interviewId"], "ceremonies": []})


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheWriteWaitsAndTwoPeopleSign(unittest.TestCase):
    """Spec T19 §1: S14 against the double, the estate at Spec 109."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.said = []
        cls.double, cls.runner, cls.outcomes = run_against(tmp=cls.tmp, said=cls.said)
        cls.record = cls.runner.facts["awaiting"]
        cls.report = cls.runner.report()

    def test_s14_passes_with_the_wait_the_reads_the_two_signatures_and_the_estates_record(self):
        o = self.outcomes["S14"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        record = self.record
        self.assertFalse(record["resumed"])
        self.assertEqual(record["answered"], 18)
        given = {q: v for q, v, _, _ in record["answers"]}
        self.assertEqual(given["WN"], {"text": NAME})
        self.assertEqual(given["WQ"], {"choice": "2"})
        self.assertEqual(given["WA1"], A.approvals_account_overrides()["wallet_account"]["WA1"])
        self.assertEqual(given["O2"], A.ACCOUNT_ANSWERS["O2"], "the rest is the book's for the Operating account")
        self.assertEqual(record["wait"]["state"], T.INTERVIEW_AWAITING_APPROVALS)
        view = record["wait"]["ceremonies"][0]
        self.assertEqual((view["requiredSignatures"], view["signaturesCollected"], view["state"]), (2, 0, "awaiting"))
        self.assertEqual(view["maySign"], ["Ada Approver", "Ben Signatory", "Harriet Founder"], "WA1's two and WO2's third party, seated by the compiler")
        self.assertEqual(list(record["reads"]), ["harriet", "ada", "ben", "olive"])
        self.assertEqual((record["reads"]["ada"]["callerMaySign"], record["reads"]["ada"]["callerName"]), (True, "Ada Approver"))
        self.assertEqual((record["reads"]["ben"]["callerMaySign"], record["reads"]["ben"]["callerName"]), (True, "Ben Signatory"))
        self.assertEqual((record["reads"]["olive"]["callerMaySign"], record["reads"]["olive"]["callerName"]), (False, None))
        finish = record["finish"]
        self.assertEqual(finish["signed"], ["Ada Approver", "Ben Signatory"])
        self.assertTrue(finish["written"])
        self.assertEqual(finish["finished_by"], "Ben Signatory")
        self.assertEqual(finish["second_press"], {"who": "Ada Approver", "status": 409, "counted": False, "refusal_code": H.APPROVER_ALREADY_SIGNED})
        self.assertEqual([(p["who"], p["status"], p.get("second", False)) for p in finish["presses"]], [("Ada Approver", 200, False), ("Ada Approver", 409, True), ("Ben Signatory", 200, False)])
        self.assertEqual(record["after"], [], "no write waits once the count is met")
        self.assertEqual(record["page_state"], "written")
        self.assertEqual(record["funding_wallet"]["address"], self.runner.facts["funding_wallet"]["address"], "no second funding wallet")
        for words in ("%s: 18 questions answered (WN, WQ 2 and WA1 this account's own, the rest the Operating account's)" % NAME,
                      "compiled and the write waits (202): %s%s: ceremony " % (NAME, T.APPROVED_DESTINATIONS_SUFFIX), "awaiting, 0 of 2 signed; may sign: Ada Approver, Ben Signatory and Harriet Founder",
                      "read as Harriet Founder, Ada Approver, Ben Signatory and Olive Overseer", "finish: Ada Approver counted (1 of 2); Ada Approver's second press: refused, and the refusal says why (Rule 13): APPROVER_ALREADY_SIGNED: You have already signed this change",
                      "1 of 2 stand; nothing was signed again.; Ben Signatory counted and the write finished on their signature",
                      "the trail: 1 onboarding.interview_written row(s) for the interview, 2 onboarding.ceremony_signed, 1 onboarding.write_awaiting_approvals, 0 onboarding.interview_write_failed; 1 wallet.born in all",
                      "funding wallet unchanged: %s" % self.runner.facts["funding_wallet"]["address"],
                      "the list: the estate offers a browser no road onto the platform's list, so it is judged by the estate's own record of the write, above"):
            self.assertIn(words, o.line, words)
        self.assertEqual([f for f in self.runner.findings if f.station == "S14"], [])
        self.assertIn("S14 — pass — the write that waits: ", self.said[-1])

    def test_the_trail_carries_the_finish_as_spec_109_records_it(self):
        interview_id = self.record["interviewId"]
        pending = self.record["finish"]["pendingTxId"]
        trail = self.record["trail"]
        ada, ben = self.runner.people["ada"], self.runner.people["ben"]
        written = H.rows_of(trail, T.INTERVIEW_WRITTEN, interview_id)
        self.assertEqual(len(written), 1)
        self.assertEqual((written[0]["credential_id"], written[0]["detail"]["pressedBy"], written[0]["detail"]["pendingTxId"]), (ben.credential_id, ben.credential_id, pending))
        signed = [r for r in trail if r["action"] == T.CEREMONY_SIGNED and r["detail"]["pendingTxId"] == pending]
        self.assertEqual([(r["credential_id"], r["subject_id"], r["detail"]["signaturesCollected"], r["detail"]["status"]) for r in signed],
                         [(ada.credential_id, interview_id, "1", "pending"), (ben.credential_id, interview_id, "2", "approved")])
        awaiting = H.rows_of(trail, T.WRITE_AWAITING_APPROVALS, interview_id)
        self.assertEqual([(r["detail"]["pendingTxId"], r["detail"]["road"], r["detail"]["requiredSignatures"], r["detail"]["signaturesCollected"]) for r in awaiting], [(pending, "compile", "2", "0")])
        self.assertEqual(H.rows_of(trail, T.INTERVIEW_WRITE_FAILED, interview_id), [])
        self.assertEqual(len([r for r in trail if r["action"] == T.WALLET_BORN]), 1, "S5's press; the finish answered alreadyHeld")
        self.assertEqual(H.audit_the_finish(trail, interview_id, pending, [ada.credential_id, ben.credential_id], ben.credential_id), [])

    def test_the_calls_are_the_two_step_road_as_each_person_under_their_own_credential_and_never_retried(self):
        calls = [c for c in self.runner.calls if c.station == "S14"]
        interview_id = self.record["interviewId"]
        pending = self.record["finish"]["pendingTxId"]
        road = "/v1/onboarding/interviews/%s/ceremonies/%s/sign" % (interview_id, pending)
        signing = [(c.who, c.path.endswith("/options"), c.status) for c in calls if c.path.startswith(road)]
        self.assertEqual(signing, [("Ada Approver", True, 200), ("Ada Approver", False, 200), ("Ada Approver", True, 200), ("Ada Approver", False, 409),
                                   ("Ben Signatory", True, 200), ("Ben Signatory", False, 200)])
        self.assertTrue(all(c.retry_of is None for c in calls), "no press carrying an assertion is sent twice")
        compiles = [c for c in calls if c.path.endswith("/compile")]
        self.assertEqual([c.status for c in compiles], [202], "Finish the write was pressed once, by the compile road, and answered the wait")
        reads = [c.who for c in calls if c.route == "GET %s" % T.ONBOARDING_CEREMONIES_ROUTE]
        self.assertEqual(reads, ["Harriet Founder", "Harriet Founder", "Ada Approver", "Ben Signatory", "Olive Overseer", "Harriet Founder"], "the read first, the four reads, the read after")
        self.assertEqual([c.who for c in calls if c.route.startswith("GET %s" % T.AUDIT_EXPORT_ROUTE)], ["Harriet Founder"])
        self.assertEqual([c.route for c in calls][-2:], ["GET /v1/onboarding/interviews/%s" % interview_id, "GET /v1/workspace"])
        # the binding the double derived the challenge from
        options = [c for c in self.double.calls if c["path"] == road + "/options"]
        self.assertEqual(len(options), 3)
        # every refusal S14 met says why (Rule 13, as S10 judges them): the one refusal is the second press
        refused = [c for c in calls if c.status >= 400]
        self.assertEqual([(c.who, c.status) for c in refused], [("Ada Approver", 409)])
        self.assertIsNone(H.refusal_without_why(refused[0].status, refused[0].text))
        # nothing was started twice, and S14's answers were the book's with its own three
        self.assertEqual(len([c for c in calls if c.route == "POST /v1/onboarding/interviews"]), 1)

    def test_s5s_own_record_is_untouched_by_s14s_walk(self):
        self.assertEqual(self.runner.facts["charter"]["wallet_account"]["name"], A.WALLET_ACCOUNT_NAME)
        self.assertEqual(self.runner.facts["charter"]["wallet_account"]["quorum"], 1)
        given = {q: v for q, v, _, _ in self.runner.facts["answers"]["wallet_account"]}
        self.assertEqual((given["WN"], given["WQ"]), ({"text": A.WALLET_ACCOUNT_NAME}, {"choice": "1"}))
        self.assertNotEqual(self.runner.facts["interview"]["wallet_account"], self.record["interviewId"])
        self.assertEqual(self.runner.facts["interview_state"]["wallet_account"], "at_read_back", "as S5's walk recorded it, restored")
        lines = {l["questionId"]: l["spoken"] for l in self.runner.facts["readback"]["wallet_account"]["lines"]}
        self.assertEqual(lines["WN"], A.WALLET_ACCOUNT_NAME, "the Operating account's read-back, not the approvals account's")
        self.assertIsNotNone(self.record["readback"], "S14's own read-back is kept on its record")
        self.assertEqual({l["questionId"]: l["spoken"] for l in self.record["readback"]["lines"]}["WN"], NAME)

    def test_the_platform_holds_one_list_on_the_new_account_with_the_ceremony_consumed_and_the_seats_bound(self):
        iv = self.double.interviews[self.record["interviewId"]]
        self.assertEqual(iv["state"], "written")
        receipt = iv["writeReceipt"]
        account = self.double.accounts[receipt["aapAccountId"]]
        self.assertNotEqual(receipt["aapAccountId"], self.double.aap_account_id, "a platform account of its own")
        self.assertEqual([(w["name"], w["mode"], w["active"]) for w in account["whitelists"]], [(NAME + T.APPROVED_DESTINATIONS_SUFFIX, "hold_non_listed", True)])
        self.assertEqual(receipt["whitelistId"], account["whitelists"][0]["id"])
        self.assertNotIn("whitelistCeremony", receipt)
        self.assertEqual(receipt["fundingWallet"], {"born": False, "alreadyHeld": {"address": self.double.source_account}})
        self.assertNotIn("_accountKeySealed", receipt)
        ceremony = next(c for c in self.double.ceremonies if c["id"] == self.record["finish"]["pendingTxId"])
        self.assertEqual((ceremony["status"], len(ceremony["collected"]), ceremony["requiredSignatures"], ceremony["requiredMultisigId"]), ("consumed", 2, 2, account["roster"]["id"]))
        seats = {s["user_id"]: s["credential_id"] for s in account["roster"]["signers"]}
        self.assertEqual(seats[A.PEOPLE["ada"].email], self.runner.people["ada"].credential_id)
        self.assertEqual(seats[A.PEOPLE["ben"].email], self.runner.people["ben"].credential_id)
        self.assertEqual(seats[A.PEOPLE["harriet"].email], "", "the third party's seat stays empty: nobody pressed as her")
        self.assertEqual(account["roster"]["minSignatures"], 2)
        # the finish seated the presser, whom the charter names (completeSeatOnCharterWrite)
        self.assertIn(self.runner.people["ben"].credential_id, self.double.second_approvers)

    def test_the_report_and_the_dry_run_carry_s14(self):
        self.assertIn("## S14 — The write that waits", self.report)
        self.assertIn("| S14 The write that waits | pass | the write that waits: ", self.report)
        self.assertIn("Outcome: **pass**. the write that waits: %s: 18 questions answered" % NAME, self.report)
        self.assertEqual(len(H.read_report(self.runner.write_report())["outcomes"]), len(H.STATIONS))
        s14 = [l for l in H.dry_lines() if l.startswith("S14 — ")]
        self.assertEqual(len(s14), 34)
        self.assertTrue(s14[0].startswith("S14 — GET %s (as Harriet Founder) → expect every write of the estate that waits for approvals (Spec 109); a wallet-account interview named %s standing awaiting_approvals is resumed here and never started twice" % (T.ONBOARDING_CEREMONIES_ROUTE, NAME)), s14[0])
        self.assertTrue(any('"questionId": "WQ", "value": {"choice": "2"}' in l and "this account's own answer" in l for l in s14))
        self.assertTrue(any('"questionId": "WN", "value": {"text": "%s"}' % NAME in l for l in s14))
        self.assertTrue(any("/compile {} → expect 202: state awaiting_approvals, interviewId and ceremonies" in l for l in s14))
        self.assertEqual(len([l for l in s14 if "/ceremonies/<pendingTxId>/sign" in l]), 5, "Ada's options and press, her second press, Ben's options and press")
        self.assertTrue(any("→ expect 409 APPROVER_ALREADY_SIGNED" in l for l in s14))
        self.assertTrue(any("(as Ben Signatory) → expect 200: state written and no ceremony" in l for l in s14))
        self.assertTrue(any("GET /v1/export/audit?limit=5000" in l and "pressedBy Ben Signatory's" in l for l in s14))
        self.assertTrue(s14[-1].startswith("S14 — GET /v1/workspace (as Harriet Founder) → expect the funding wallet S5 gave the estate, unchanged"))
        resumed = H.dry_lines(start_at="S14")
        self.assertTrue(resumed[0].startswith("resume — "))
        self.assertEqual(resumed[1:], s14)
        s5 = [l for l in H.dry_lines() if l.startswith("S5 — ")]
        self.assertTrue(s5[0].startswith("S5 — GET %s (as Harriet Founder) → expect every write of the estate that waits for approvals (Spec 109)" % T.ONBOARDING_CEREMONIES_ROUTE), s5[0])
        self.assertIn('S5 stops: "FAILED — prerequisite: <name> stands awaiting approvals and could not be finished"', s5[0])
        self.assertTrue(s5[1].startswith("S5 — POST /v1/onboarding/interviews/<waiting interview>/compile {} (as Harriet Founder) — only for a ceremony listed expired, closed or approved"))
        self.assertTrue(s5[2].startswith("S5 — POST /v1/onboarding/interviews/<waiting interview>/ceremonies/<pendingTxId>/sign/options {} then …/sign"))
        self.assertTrue(any('a 202 (state awaiting_approvals — the write that waits for the client\'s approvers, Spec 109) is not a write that finishes: S5 stops with "the write is waiting for approvals; S5 expects a write that finishes"' in l for l in s5))

    def test_a_rerun_resumes_nothing_and_opens_another_account_and_the_next_payments_read_the_newest_charter(self):
        runner = runner_on(self.double, self.tmp)
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S14"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertFalse(runner.facts["awaiting"]["resumed"])
        self.assertNotEqual(runner.facts["awaiting"]["interviewId"], self.record["interviewId"])
        self.assertEqual(len(approvals_accounts_of(self.double)), 2, "a rerun opens another account")
        self.assertEqual(outcomes["S5"].outcome, H.PASS, outcomes["S5"].line)
        self.assertNotIn("before it,", outcomes["S5"].line, "nothing waited: the first run's finish left no write awaiting")
        # the finish seated Ben (the charter names him), so on the payments road his press now counts; this run's S5 wrote a newer Operating
        # account at WQ 1, the newest written charter the payments road reads, so P3 still asks one approval
        s7 = outcomes["S7"]
        self.assertEqual(s7.outcome, H.PASS, s7.line)
        p3 = s7.line.split("P3 (12.00 USDC", 1)[1]
        self.assertIn("approvalsRequired 1; Ben Signatory signed (1 of 1): approved", p3)
        # a run resumed past S5 meets the approvals account as the newest written charter — two approvals of an above-band payment, Ben and Ada
        resumed = runner_on(self.double, self.tmp, start_at="S7")
        outcomes3 = {o.station: o for o in resumed.run()}
        s7r = outcomes3["S7"]
        self.assertEqual(s7r.outcome, H.PASS, s7r.line)
        p3r = s7r.line.split("P3 (12.00 USDC", 1)[1]
        self.assertIn("approvalsRequired 2; Ben Signatory signed (1 of 2)", p3r)
        self.assertIn("Ada Approver signed (2 of 2): approved", p3r)
        self.assertEqual(len(approvals_accounts_of(self.double)), 3, "the resumed run's S14 opened one more")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheHarnessNeverStrandsItsEstate(unittest.TestCase):
    """Spec T19 §2: a write an earlier run left waiting is finished before S5, or resumed at S14's read; never started twice."""

    def test_an_awaiting_interview_of_that_name_is_finished_before_s5_and_s14_then_starts_its_own(self):
        double, tmp, first, interview_id = seed_a_write_that_waits()
        self.assertEqual(double.interviews[interview_id]["state"], T.INTERVIEW_AWAITING_APPROVALS)
        runner = runner_on(double, tmp)
        outcomes = {o.station: o for o in runner.run()}
        s5 = outcomes["S5"]
        self.assertEqual(s5.outcome, H.PASS, s5.line)
        self.assertTrue(s5.line.startswith("before it, %s stood awaiting approvals from an earlier run and was finished first: Ada Approver counted (1 of 2); Ben Signatory counted and the write finished on their signature; wallet account: 18 questions answered" % NAME), s5.line)
        finished = runner.facts["finished_before_s5"]
        self.assertEqual([(f["interviewId"], f["signed"], f["written"], f["finished_by"], f["second_press"]) for f in finished], [(interview_id, ["Ada Approver", "Ben Signatory"], True, "Ben Signatory", None)])
        self.assertEqual(double.interviews[interview_id]["state"], "written")
        s5_calls = [c for c in runner.calls if c.station == "S5"]
        first_start = next(i for i, c in enumerate(s5_calls) if c.route == "POST /v1/onboarding/interviews")
        self.assertEqual(s5_calls[0].route, "GET %s" % T.ONBOARDING_CEREMONIES_ROUTE, "the read comes first")
        self.assertEqual([(c.who, c.status) for c in s5_calls[:first_start] if c.path.endswith("/sign")], [("Ada Approver", 200), ("Ben Signatory", 200)], "the signatures before S5 starts its own")
        self.assertEqual(runner.facts["charter"]["wallet_account"]["name"], A.WALLET_ACCOUNT_NAME, "S5 then walked its own Operating account")
        self.assertNotEqual(runner.facts["interview"]["wallet_account"], interview_id, "never started twice: the finished one is not S5's")
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.PASS, s14.line)
        self.assertFalse(runner.facts["awaiting"]["resumed"])
        self.assertEqual(len(approvals_accounts_of(double)), 2)

    def test_an_awaiting_interview_of_that_name_is_resumed_at_s14s_read_never_started_twice(self):
        double, tmp, first, interview_id = seed_a_write_that_waits()
        runner = runner_on(double, tmp, start_at="S14")
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S14"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(outcomes["S5"].outcome, H.SKIPPED)
        self.assertTrue(runner.facts["awaiting"]["resumed"])
        self.assertEqual(runner.facts["awaiting"]["interviewId"], interview_id)
        self.assertIn("%s stood awaiting approvals from an earlier run and is resumed at the read, not started again: " % NAME, o.line)
        self.assertEqual([c for c in runner.calls if c.station == "S14" and c.route == "POST /v1/onboarding/interviews"], [], "never started twice")
        self.assertEqual(len(approvals_accounts_of(double)), 1)
        self.assertEqual(double.interviews[interview_id]["state"], "written")
        self.assertEqual(runner.facts["awaiting"]["finish"]["signed"], ["Ada Approver", "Ben Signatory"])

    def test_a_lapsed_ceremony_has_the_founder_press_finish_the_write_first_and_the_trail_names_what_it_replaces(self):
        double, tmp, first, interview_id = seed_a_write_that_waits()
        lapsed = list_ceremony_of(double, interview_id)
        lapsed["expiresAtEpoch"] = time.time() - 60
        lapsed["expiresAt"] = double._iso(lapsed["expiresAtEpoch"])
        runner = runner_on(double, tmp, start_at="S14")
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S14"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        record = runner.facts["awaiting"]
        self.assertTrue(record["resumed"])
        self.assertEqual(record["wait"]["state"], "expired")
        self.assertEqual(record["pressed_first"]["state"], "expired")
        self.assertEqual(record["pressed_first"]["status"], 202)
        fresh = record["finish"]["pendingTxId"]
        self.assertNotEqual(fresh, lapsed["id"])
        self.assertIn("the ceremony read expired; the founder pressed Finish the write and the estate opened %s%s: ceremony %s… awaiting, 0 of 2 signed" % (NAME, T.APPROVED_DESTINATIONS_SUFFIX, T.credential_short_form(fresh)), o.line)
        awaiting = H.rows_of(record["trail"], T.WRITE_AWAITING_APPROVALS, interview_id)
        self.assertEqual([(r["detail"]["pendingTxId"], r["detail"].get("replaces")) for r in awaiting], [(lapsed["id"], None), (fresh, lapsed["id"])])
        self.assertEqual(lapsed["status"], "pending", "the platform sweeps nothing: the lapsed one keeps its word and collects for a request nobody presents again")
        self.assertEqual(next(c for c in double.ceremonies if c["id"] == fresh)["status"], "consumed")
        # the same lapse met before S5 is finished the same way
        double2, tmp2, _, interview2 = seed_a_write_that_waits()
        lapsed2 = list_ceremony_of(double2, interview2)
        lapsed2["expiresAtEpoch"] = time.time() - 60
        runner2 = runner_on(double2, tmp2)
        outcomes2 = {o.station: o for o in runner2.run()}
        self.assertEqual(outcomes2["S5"].outcome, H.PASS, outcomes2["S5"].line)
        self.assertIn("was finished first: the ceremony read expired; the founder pressed Finish the write and the estate opened", outcomes2["S5"].line)
        self.assertEqual(double2.interviews[interview2]["state"], "written")

    def test_where_nobody_the_list_names_can_sign_s5_stops_at_the_missing_prerequisite_in_red(self):
        double, tmp, first, interview_id = seed_a_write_that_waits()
        for key in ("ada", "ben"):
            os.remove(first.key_path(first.people[key]))
        said = []
        runner = runner_on(double, tmp, start_at="S5", said=said)
        outcomes = {o.station: o for o in runner.run()}
        s5 = outcomes["S5"]
        self.assertEqual(s5.outcome, H.FAILED_PREREQUISITE, s5.line)
        self.assertTrue(s5.line.startswith("wallet account: %s stands awaiting approvals and could not be finished — " % NAME), s5.line)
        for words in ("Ada Approver is named as able and has no session to sign with", "Ben Signatory is named as able and has no session to sign with",
                      "Harriet Founder: refused, and the refusal says why (Rule 13): SIGNATURE_NOT_COUNTED: This list is created by Ada Approver, Ben Signatory and Harriet Founder; you are not among them. Nothing was signed.",
                      "the count stands at 0 of 2 and nobody else the list names can sign here"):
            self.assertIn(words, s5.line, words)
        self.assertEqual(runner.line(s5), "S5 — %s — %s" % (H.FAILED_PREREQUISITE, s5.line))
        self.assertIn(runner.line(s5), said)
        self.assertEqual(H.exit_code_of(list(outcomes.values())), 1)
        self.assertEqual(double.interviews[interview_id]["state"], T.INTERVIEW_AWAITING_APPROVALS, "left as it stood: the founder's press signs nothing")
        self.assertEqual([c.route for c in runner.calls if c.station == "S5" and c.route == "POST /v1/onboarding/interviews"], [], "S5 started nothing on top of it")
        # the table says so in red, and the report reader reads the kind back through the markup
        report_path = runner.write_report()
        with open(report_path, "r", encoding="utf-8") as handle:
            report = handle.read()
        self.assertIn("| S5 Wallet account | %s | wallet account: %s stands awaiting approvals and could not be finished — " % (RED_CELL, NAME), report)
        self.assertIn("Outcome: **%s**. wallet account: " % H.FAILED_PREREQUISITE, report)
        self.assertEqual(H.read_report(report_path)["outcomes"]["S5"], H.FAILED_PREREQUISITE)
        # S14, resuming the same write, cannot finish it either and fails rather than starting another
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.FAIL, s14.line)
        self.assertTrue(runner.facts["awaiting"]["resumed"])
        self.assertEqual(len(approvals_accounts_of(double)), 1)

    def test_s5_stops_where_its_own_write_waits_and_s14_will_not_start_over_a_write_of_another_name(self):
        with unittest.mock.patch.dict(A.ACCOUNT_ANSWERS, {"WQ": {"choice": "2"}}):
            double, runner, outcomes = run_against()
        s5 = outcomes["S5"]
        self.assertEqual(s5.outcome, H.FAIL, s5.line)  # the stop names no missing prerequisite: the estate answered the wait S5 does not accept
        self.assertEqual(s5.line, "wallet account: the write is waiting for approvals; S5 expects a write that finishes")
        compile_call = [c for c in runner.calls if c.station == "S5" and c.path.endswith("/compile")]
        self.assertEqual([c.status for c in compile_call], [202])
        operating = runner.facts["interview"]["wallet_account"]
        self.assertEqual(double.interviews[operating]["state"], T.INTERVIEW_AWAITING_APPROVALS)
        self.assertEqual(runner.facts["interview_state"]["wallet_account"], T.INTERVIEW_AWAITING_APPROVALS)
        self.assertNotIn("wallet_account", runner.facts["charter"], "no charter recorded: the 202 carries none")
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.FAILED_PREREQUISITE, s14.line)
        self.assertIn("a wallet-account interview of another name stands awaiting approvals — the estate handed back the wallet-account interview %s standing awaiting_approvals, which is not %s" % (operating, NAME), s14.line)
        self.assertEqual(len(approvals_accounts_of(double)), 0, "nothing started over it")

    def test_an_estate_before_spec_109_is_noted_at_s5_and_stops_s14_at_its_first_line(self):
        double, runner, outcomes = run_against(before_spec_109=True)
        self.assertEqual(outcomes["S5"].outcome, H.PASS, outcomes["S5"].line)
        self.assertEqual(runner.notes["S5"], ["the estate has no door onto the writes that wait (%s answered REQUEST_MALFORMED: That request could not be read.): an estate before AER 360 Spec 109, so nothing was finished" % T.ONBOARDING_CEREMONIES_ROUTE])
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.FAILED_PREREQUISITE, s14.line)
        self.assertEqual(s14.line, "the write that waits: %s — the estate has no door onto the writes that wait (%s answered REQUEST_MALFORMED: That request could not be read.): an estate before AER 360 Spec 109" % (H.SPEC_109_NOT_LIVE_PREREQUISITE, T.ONBOARDING_CEREMONIES_ROUTE))
        self.assertEqual([c.route for c in runner.calls if c.station == "S14"], ["GET %s" % T.ONBOARDING_CEREMONIES_ROUTE], "nothing started, nothing stranded")
        self.assertEqual(len(approvals_accounts_of(double)), 0)
        # and the old failure itself, met where a write is pressed on such an estate: the platform's 409 as a failed write, in its words
        with unittest.mock.patch.dict(A.ACCOUNT_ANSWERS, {"WQ": {"choice": "2"}}):
            double2, runner2, outcomes2 = run_against(before_spec_109=True)
        s5 = outcomes2["S5"]
        self.assertEqual(s5.outcome, H.FAIL, s5.line)  # the estate's refusal, as it was before Spec 109: the estate failing
        self.assertIn("POST compile answered CHARTER_WRITE_UNFINISHED: Your charter is compiled, and writing it to the platform did not finish.", s5.line)
        self.assertIn("(AAP POST /v1/whitelists-v2 failed (HTTP 409): mutation requires multisig approval: whitelist_modify requires 0/2 approvals (pending_tx_id=", s5.line)

    def test_the_plans_capacity_refusing_a_second_account_is_reported_in_the_estates_words_and_s14_stops(self):
        # the sentence is the test's stand-in for the platform's: the double carries whatever the platform says as the write's cause
        said = "AAP POST /v1/accounts failed (HTTP 402): this plan holds one wallet account; raise the plan to open another"
        double, runner, outcomes = run_against(second_account_refused=said)
        self.assertEqual(outcomes["S5"].outcome, H.PASS, outcomes["S5"].line)
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.FAIL, s14.line)  # an estate's refusal stays fail, in the estate's words
        self.assertEqual(s14.line, "the write that waits: POST compile answered CHARTER_WRITE_UNFINISHED: Your charter is compiled, and writing it to the platform did not finish. "
                                   "Nothing you answered is lost: reopen the interview and confirm again. (%s)" % said)
        interview_id = runner.facts["awaiting"]["interviewId"]
        self.assertEqual((double.interviews[interview_id]["state"], double.interviews[interview_id]["writeError"]), ("compiled", said))
        self.assertEqual(len([r for r in double.trail if r["action"] == T.INTERVIEW_WRITE_FAILED]), 1)
        self.assertEqual([c.status for c in runner.calls if c.station == "S14" and c.path.endswith("/compile")], [409])

    def test_a_signature_answered_wrongly_is_a_finding_and_fails_the_finish(self):
        """Spec T19 §1, the answers judged: one more signature than before, the presser's read saying they signed, and a second press refused as APPROVER_ALREADY_SIGNED."""
        class MiscountingDouble(EstateDouble):
            def interview_ceremony_view(self, iv, caller):
                view = super().interview_ceremony_view(iv, caller)
                if view.get("signaturesCollected"):
                    view = dict(view, signaturesCollected=0, callerHasSigned=False)  # a platform whose record says nothing moved
                return view
        double = MiscountingDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.FAIL, s14.line)
        probes = [f.probe for f in runner.findings if f.station == "S14"]
        self.assertIn("Ada Approver's signature: the count", probes)
        self.assertIn("Ada Approver's signature: callerHasSigned", probes)
        finding = next(f for f in runner.findings if f.probe == "Ada Approver's signature: the count")
        self.assertEqual((finding.expected, finding.said), ("signaturesCollected 1, one more than the 0 before the press", "signaturesCollected 0"))
        self.assertEqual([p["probe"] for p in runner.facts["awaiting"]["finish"]["problems"]], ["Ada Approver's signature: the count", "Ada Approver's signature: callerHasSigned"])
        self.assertTrue(runner.facts["awaiting"]["finish"]["written"], "the write still finished; the answers were judged wanting")

        class CountingTwiceDouble(EstateDouble):
            def already_signed_refusal(self, record, credential_id, seat):
                raise AssertionError("never asked: this platform counts a signatory twice")

            def sign_interview_ceremony(self, press, body):
                record = next((c for c in self.ceremonies if c["id"] == press["pendingTxId"]), None)
                if record is not None:
                    record["collected"] = [c for c in record["collected"] if c["credential_id"] != press["caller"]["credentialId"]]  # forgets the signature, so it counts again
                return super().sign_interview_ceremony(press, body)
        double = CountingTwiceDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S14"].outcome, H.FAIL, outcomes["S14"].line)
        second = runner.facts["awaiting"]["finish"]["second_press"]
        self.assertTrue(second["counted"])
        self.assertIn("Ada Approver's second press counted again — a second press must count nothing (finding)", outcomes["S14"].line)
        self.assertTrue(any(f.probe.startswith("a second press by Ada Approver on the ceremony") and f.said.startswith("the second press was counted") for f in runner.findings))

        class OtherRefusalDouble(EstateDouble):
            def already_signed_refusal(self, record, credential_id, seat):
                from tests.test_aer360_double import Refusal
                return Refusal("SIGNATURE_NOT_COUNTED", detail={"pendingTxId": record["id"], "platformStatus": "403", "platformSaid": "not authorized"})
        double = OtherRefusalDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S14"].outcome, H.FAIL, outcomes["S14"].line)
        second = runner.facts["awaiting"]["finish"]["second_press"]
        self.assertEqual((second["counted"], second["refusal_code"]), (False, H.SIGNATURE_NOT_COUNTED))
        self.assertIn("refused, but not as APPROVER_ALREADY_SIGNED (finding)", outcomes["S14"].line)
        finding = next(f for f in runner.findings if f.probe.startswith("a second press by Ada Approver"))
        self.assertTrue(finding.said.startswith("refused as SIGNATURE_NOT_COUNTED, not APPROVER_ALREADY_SIGNED: "), finding.said)
        # the same judgment before S5: a finish answered wrongly fails S5, though the write finished
        double2, tmp2, _, interview2 = seed_a_write_that_waits(double=MiscountingDouble())
        runner2 = runner_on(double2, tmp2)
        outcomes2 = {o.station: o for o in runner2.run()}
        self.assertEqual(outcomes2["S5"].outcome, H.FAIL, outcomes2["S5"].line)
        self.assertIn("; the finish answered wrongly: signaturesCollected 0; callerHasSigned false", outcomes2["S5"].line)
        self.assertEqual(double2.interviews[interview2]["state"], "written")

    def test_the_compiles_status_is_asserted_not_only_its_body(self):
        """Spec T19 §2, as T19 words it: HTTP 200 for a write that finishes, HTTP 202 with the wait's body for S14."""
        class Odd202Double(EstateDouble):
            def compile(self, caller, interview_id):
                status, body = super().compile(caller, interview_id)
                return (202, body) if status == 200 and self.interviews[interview_id]["interviewType"] == "wallet_account" else (status, body)
        double = Odd202Double()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        s5 = outcomes["S5"]
        self.assertEqual(s5.outcome, H.FAIL, s5.line)
        self.assertEqual(s5.line, "wallet account: POST compile answered HTTP 202 without the write that waits' body (state awaiting_approvals, interviewId, ceremonies)")

        class Odd201Double(EstateDouble):
            def compile(self, caller, interview_id):
                status, body = super().compile(caller, interview_id)
                return (201, body) if status == 200 and self.interviews[interview_id]["interviewType"] == "wallet_account" else (status, body)
        double = Odd201Double()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        s5 = outcomes["S5"]
        self.assertEqual(s5.outcome, H.FAIL, s5.line)
        self.assertEqual(s5.line, "wallet account: POST compile answered HTTP 201, not HTTP 200 with the compiled charter, the write receipt and the seat")
        step = [s for s in runner.evidence["S5"] if s["route"].endswith("/compile")][-1]
        self.assertTrue(step["expected"].startswith("HTTP 200 with the compiled charter, the write receipt and the seat; a 202"), step["expected"])
        self.assertEqual(step["result"], "HTTP 201, compiled and written")
        # and the 202 S14 accepts is asserted by status and body both
        double, runner, outcomes = run_against()
        step = [s for s in runner.evidence["S14"] if s["route"].endswith("/compile")][0]
        self.assertEqual(step["status"], 202)
        self.assertTrue(step["expected"].startswith("HTTP 202 with state awaiting_approvals, interviewId and ceremonies"), step["expected"])
        self.assertTrue(step["result"].startswith("HTTP 202, the write waits: "), step["result"])

    def test_the_report_reader_strips_the_outcome_cell_alone(self):
        """Spec T19 §3: the red span is the Outcome cell's; a line's own angle brackets — `--treasury-invite <link>`, `<pendingTxId>` — survive the read-back."""
        self.assertEqual(H._table_cells("| S7 Payments | %s | payments: --treasury-invite <link> and <pendingTxId> |" % RED_CELL),
                         ["S7 Payments", RED_CELL, "payments: --treasury-invite <link> and <pendingTxId>"])
        self.assertEqual(H.outcome_of_cell(RED_CELL), H.FAILED_PREREQUISITE)
        self.assertEqual(H.outcome_of_cell("pass"), "pass")
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "aer360-harness-2026-09-25.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# AER 360 estate harness run — Harness Holdings Pty Ltd — 2026-09-25T10:00:00+10:00\n\n## The closing table\n\n| Station | Outcome | Line |\n|---|---|---|\n"
                         "| S7 Payments | %s | payments: Harness Treasury not born — no --treasury-invite <link> was given |\n| S14 The write that waits | pass | the write that waits: <pendingTxId> |\n" % RED_CELL)
        read = H.read_report(path)
        self.assertEqual(read["outcomes"], {"S7": H.FAILED_PREREQUISITE, "S14": "pass"})

    def test_a_write_that_finished_at_once_at_wq_2_fails_s14(self):
        class UngovernedDouble(EstateDouble):
            def create_whitelist(self, account, name, mode):
                wl = {"id": "wl-ungoverned", "name": name, "mode": mode, "active": True, "entries": []}
                account["whitelists"].append(wl)
                return {"ceremony": None, "whitelist": wl}
        double = UngovernedDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        s14 = outcomes["S14"]
        self.assertEqual(s14.outcome, H.FAIL, s14.line)
        self.assertIn("compiled and the write finished at once (200), where WQ 2 asks the platform to hold the list's creation for the approvers — nothing waited", s14.line)
        finding = [f for f in runner.findings if f.station == "S14"]
        self.assertEqual(len(finding), 1)
        self.assertEqual(finding[0].probe, "the compile of %s at WQ 2" % NAME)
        self.assertIn("202 with state awaiting_approvals: the platform holds the list's creation for Ada Approver and Ben Signatory at WQ 2 (Spec 109)", finding[0].expected)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class APrerequisiteIsAFailureWithItsOwnName(unittest.TestCase):
    """Spec T19 §3: a StationStop is the outcome kind FAILED — prerequisite — red in the table, counted for the exit code, naming what was missing."""

    def test_s7_with_no_treasury_stops_at_harness_treasury_not_born_in_red(self):
        double = EstateDouble(treasury=False)
        tmp = tempfile.mkdtemp()
        said = []
        runner = runner_on(double, tmp, invite=double.mint_founder_link(), said=said)
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)
        self.assertTrue(o.line.startswith("payments: %s — no passkey is stored for its founder at " % H.TREASURY_NOT_BORN), o.line)
        self.assertIn("and no --treasury-invite <link> was given; the first run births the Treasury from the birth script's invitation, exactly as Harness Holdings was born", o.line)
        self.assertEqual(runner.line(o), "S7 — %s — %s" % (H.FAILED_PREREQUISITE, o.line), "the summary line names the scenario and the missing prerequisite")
        self.assertIn(runner.line(o), said)
        self.assertFalse(runner.in_colour, "a test's captured lines carry no colour")
        self.assertEqual(H.exit_code_of(list(outcomes.values())), 1, "counted as failure for the exit code")
        self.assertEqual(H.exit_code_of([H.Outcome("S7", H.PASS, "")]), 0)
        self.assertEqual(H.exit_code_of([H.Outcome("S7", H.FAIL, "")]), 1)
        self.assertEqual(runner.notes["S7"], [], "no note beside the stop")
        path = runner.write_report()
        with open(path, "r", encoding="utf-8") as handle:
            report = handle.read()
        self.assertIn("| S7 Payments | %s | payments: %s — no passkey is stored for its founder at " % (RED_CELL, H.TREASURY_NOT_BORN), report, "red in the table")
        self.assertIn("Outcome: **%s**. payments: %s — " % (H.FAILED_PREREQUISITE, H.TREASURY_NOT_BORN), report)
        self.assertEqual(report.count("<span"), 1, "the one markup the report carries")
        read = H.read_report(path)
        self.assertEqual(read["outcomes"]["S7"], H.FAILED_PREREQUISITE, "the report reader strips the markup")
        self.assertEqual(read["outcomes"]["S1"], H.PASS)
        # the hats still ran, and the stations after S7 are judged on what they are
        self.assertEqual(outcomes["S8"].outcome, H.PASS)
        self.assertEqual(outcomes["S12"].outcome, H.PASS)
        # a second run in the same folder reads the kind back in the last-run column
        runner2 = runner_on(double, tmp)
        outcomes2 = {o.station: o for o in runner2.run()}
        self.assertEqual(outcomes2["S7"].outcome, H.FAILED_PREREQUISITE)
        with open(runner2.write_report(), "r", encoding="utf-8") as handle:
            report2 = handle.read()
        self.assertIn("| S7 Payments | %s | last run %s | " % (RED_CELL, H.FAILED_PREREQUISITE), report2)

    def test_the_birth_run_stops_at_harness_treasury_not_funded_and_the_note_beside_the_stop_is_gone(self):
        double, runner, outcomes = run_against(treasury_funding_wallet="press")
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)
        address = double.treasury.source_account
        sentence = T.FUND_TREASURY_SENTENCE % (address, T.PAYEE_CHAIN)
        self.assertTrue(o.line.startswith("payments: %s — Harness Treasury: the Treasury founder enrolled by invitation; " % H.TREASURY_NOT_FUNDED), o.line)
        self.assertTrue(o.line.endswith("%s (the three payments need US$18.24 and Harness Holdings holds US$0.00; the Treasury holds US$0.00); nothing was sent" % sentence), o.line)
        self.assertEqual([n for n in runner.notes["S7"] if "nothing was sent" in n], [], "the note beside the stop is gone; its figures are in the line")
        self.assertTrue(any(n.startswith("%s — the estate's own words: " % sentence) for n in runner.notes["S7"]), "the estate's own fund sentence is still noted where the wallet is born")

    def test_a_short_treasury_stops_at_harness_treasury_short_of_the_run(self):
        double, runner, outcomes = run_against(treasury_usdc_cents=1000)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)
        self.assertIn("payments: %s — " % H.TREASURY_SHORT, o.line)
        self.assertEqual([n for n in runner.notes["S7"] if "nothing was sent" in n], [])

    def test_the_stop_names_its_prerequisite_and_str_carries_both(self):
        stop = H.StationStop("no passkey is stored", prerequisite=H.TREASURY_NOT_BORN)
        self.assertEqual(str(stop), "%s — no passkey is stored" % H.TREASURY_NOT_BORN)
        self.assertEqual((stop.sentence, stop.prerequisite), ("no passkey is stored", H.TREASURY_NOT_BORN))
        self.assertEqual(str(H.StationStop("the founder has no session")), "the founder has no session")
        self.assertIsNone(H.StationStop("the founder has no session").prerequisite)
        self.assertEqual(H.outcome_cell(H.FAILED_PREREQUISITE), RED_CELL)
        self.assertEqual(H.outcome_cell(H.FAIL), H.FAIL)
        self.assertEqual(H.FAILURES, (H.FAIL, H.FAILED_PREREQUISITE))

    def test_the_terminal_says_it_in_red_and_a_captured_run_does_not(self):
        outcome = H.Outcome("S7", H.FAILED_PREREQUISITE, "payments: %s — no passkey is stored" % H.TREASURY_NOT_BORN)
        tmp = tempfile.mkdtemp()
        coloured = H.Runner("https://estate.test", tmp, None, False, None, tmp, transport=lambda r: (200, [], "{}"), say=lambda s: None, sleep=lambda s: None, in_colour=True)
        self.assertEqual(coloured.line(outcome), "S7 — %s%s%s — payments: %s — no passkey is stored" % (H.RED, H.FAILED_PREREQUISITE, H.RESET, H.TREASURY_NOT_BORN))
        self.assertEqual(coloured.line(H.Outcome("S1", H.PASS, "enrolled")), "S1 — pass — enrolled", "only the one kind is coloured")
        plain = H.Runner("https://estate.test", tmp, None, False, None, tmp, transport=lambda r: (200, [], "{}"), say=lambda s: None, sleep=lambda s: None)
        self.assertFalse(plain.in_colour)
        self.assertNotIn(H.RED, plain.line(outcome))
        with contextlib.redirect_stdout(io.StringIO()):
            printing = H.Runner("https://estate.test", tmp, None, False, None, tmp, transport=lambda r: (200, [], "{}"), say=print, sleep=lambda s: None)
        self.assertFalse(printing.in_colour, "print to something that is not a terminal is not coloured either")


class TheTablesFacts(unittest.TestCase):
    def test_the_pins_are_the_estates_words(self):
        self.assertEqual(T.INTERVIEW_AWAITING_APPROVALS, "awaiting_approvals")
        self.assertEqual(T.ONBOARDING_CEREMONIES_ROUTE, "/v1/onboarding/ceremonies")
        self.assertEqual(T.INTERVIEW_CEREMONY_SIGN_ROUTE % ("iv", "tx"), "/v1/onboarding/interviews/iv/ceremonies/tx/sign")
        self.assertEqual(T.INTERVIEW_CEREMONY_SIGN_OPTIONS_ROUTE % ("iv", "tx"), "/v1/onboarding/interviews/iv/ceremonies/tx/sign/options")
        self.assertEqual(T.INTERVIEW_CEREMONY_PURPOSE, "onboarding.ceremony")
        self.assertEqual(T.INTERVIEW_CEREMONY_BINDING % ("ws", "iv", "tx", 1), "onboarding-ceremony:ws:iv:tx:1")
        self.assertEqual(T.INTERVIEW_CEREMONY_STATES, T.ROSTER_CHANGE_STATES)
        self.assertEqual(T.account_name_of_list("Harness Holdings — approvals — approved destinations"), "Harness Holdings — approvals")
        self.assertEqual(T.account_name_of_list(None), "an unnamed list")
        self.assertEqual(T.account_name_of_list("Operating account"), "Operating account")
        self.assertEqual((T.WRITE_AWAITING_APPROVALS, T.CEREMONY_SIGNED, T.INTERVIEW_WRITTEN, T.INTERVIEW_WRITE_FAILED, T.WALLET_BORN),
                         ("onboarding.write_awaiting_approvals", "onboarding.ceremony_signed", "onboarding.interview_written", "onboarding.interview_write_failed", "wallet.born"))
        self.assertEqual((T.WRITE_IN_PROGRESS, T.CEREMONY_NOT_LISTED, T.CEREMONY_CLOSED, T.CHARTER_WRITE_UNFINISHED), ("WRITE_IN_PROGRESS", "CEREMONY_NOT_LISTED", "CEREMONY_CLOSED", "CHARTER_WRITE_UNFINISHED"))

    def test_the_book_answers_the_second_account_as_the_first_but_for_three(self):
        overrides = A.approvals_account_overrides()["wallet_account"]
        self.assertEqual(sorted(overrides), ["WA1", "WN", "WQ"])
        self.assertEqual(overrides["WN"], {"text": "Harness Holdings — approvals"})
        self.assertEqual(overrides["WQ"], {"choice": "2"})
        self.assertEqual(overrides["WA1"], {"entries": [{"name": "Ada Approver", "email": "harness+ada@aeredium.io"}, {"name": "Ben Signatory", "email": "harness+ben@aeredium.io"}]})
        self.assertEqual(A.APPROVALS_APPROVERS, ("ada", "ben"))
        answers = A.approvals_account_answers()
        self.assertEqual({q: answers[q] for q in overrides}, overrides)
        self.assertEqual({q: v for q, v in answers.items() if q not in overrides}, {q: v for q, v in A.ACCOUNT_ANSWERS.items() if q not in overrides})
        self.assertEqual(A.ACCOUNT_ANSWERS["WQ"], {"choice": "1"}, "the Operating account keeps WQ at one")
        self.assertIn("S14", H.STATION_IDS)
        self.assertEqual(H.STATIONS[-1], ("S14", "The write that waits"))


if __name__ == "__main__":
    unittest.main()
