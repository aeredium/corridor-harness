"""
Harness Real World (Spec HRW-1, revised 9 October 2026): the browser leg of the estate harness, walked on the screens' double.

The screens' double (tests/real_world_double.py and tests/real_world_screens.py) stands in for Playwright and renders the pages the browser leg
walks as their TSX renders them at aeredium/AERAccounts b523cbf, making the calls each press makes into the estate's own double
(tests/test_aer360_double.py), extended for the roads the screens use. Every test below walks the leg as it runs on the operator's Mac — the
one-time link, the passkey behind the prompt, the presses, the sentences — and asserts what a founder would have read and what the store holds.
"""
from __future__ import annotations

import builtins
import contextlib
import io
import json
import os
import re
import stat
import sys
import tempfile
import unittest
from typing import Any, Callable, Dict, List, Optional, Tuple
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as E  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_real_world as R  # noqa: E402
import aer360_screens as S  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests import real_world_double as W  # noqa: E402
from tests import real_world_screens as SC  # noqa: E402
from tests import test_aer360_double as D  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL_PASS = {"S%d" % n: E.PASS for n in range(1, 8)}
REPLAY_SENTENCE = "A different payment run already carries this reference. Open it, or change the reference."


def write_api_report(folder: str, outcomes: Dict[str, str], company: str = A.ESTATE["company"], name: str = "aer360-harness-2026-10-09.md") -> str:
    """The API leg's report as aer360_harness.py writes it: its title naming the estate, and the closing table R8 reads."""
    path = os.path.join(folder, name)
    rows = "".join("| %s Station | %s | a line |\n" % (station, E.outcome_cell(outcome)) for station, outcome in sorted(outcomes.items()))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("%s%s — 2026-10-09T10:00:00+11:00\n\n## The closing table\n\n| Station | Outcome | Line |\n|---|---|---|\n%s" % (E.REPORT_TITLE, company, rows))
    return path


class Setting:
    """One estate on the screens' double, born by the CLI road, with the operator's store beside it: payee.env, admin.env, the API leg's report."""

    def __init__(self, estate: Optional[W.ScreensEstate] = None, birth_email: Optional[str] = T.REAL_WORLD_BIRTH_EMAIL, admin_env: bool = True,
                 payee_env: bool = True, api_outcomes: Optional[Dict[str, str]] = ALL_PASS, printout: Optional[Callable[[str], str]] = None, **estate_kw: Any):
        self.tmp = tempfile.mkdtemp(prefix="hrw-")
        self.estate = estate if estate is not None else W.ScreensEstate(**estate_kw)
        self.world = W.World(self.estate)
        self.link = self.estate.mint_founder_link("Harriet Founder", email=birth_email)
        text = self.estate.birth_printout(self.link, email=birth_email)
        self.birth = os.path.join(self.tmp, "birth.txt")
        with open(self.birth, "w", encoding="utf-8") as handle:
            handle.write(printout(text) if printout else text)
        self.store = os.path.join(self.tmp, "store")
        os.makedirs(self.store)
        if payee_env:
            D.file_the_owner_payee(self.store)
        if admin_env:
            with open(os.path.join(self.store, T.ADMIN_ENV_FILE), "w", encoding="utf-8") as handle:
                handle.write("%s=%s\n%s=%s\n" % (T.ADMIN_ENV_URL_KEY, D.PLATFORM_BASE, T.ADMIN_ENV_KEY_KEY, self.estate.platform.admin_key))
        if api_outcomes is not None:
            write_api_report(self.tmp, api_outcomes)
        self.legs = 0

    def leg(self, start_at: Optional[str] = None, birth: bool = True) -> R.RealWorld:
        self.legs += 1
        said: List[str] = []
        leg = R.RealWorld(base=D.BASE, store_root=self.store, birth=self.birth if birth else None, start_at=start_at,
                          runs_root=os.path.join(self.tmp, "runs-%d" % self.legs), api_reports=self.tmp, driver=self.world.driver(),
                          transport=self.estate, say=said.append, sleep=lambda seconds: None, time_scale=0.001)
        leg.said = said  # type: ignore[attr-defined]
        return leg

    def walk(self, **kw: Any) -> R.RealWorld:
        leg = self.leg(**kw)
        leg.run()
        leg.report_path = leg.write_report()  # type: ignore[attr-defined]
        return leg


def outcomes(leg: R.RealWorld) -> Dict[str, str]:
    return {o.station: o.outcome for o in leg.outcomes}


def line_of(leg: R.RealWorld, station: str) -> str:
    return next(o.line for o in leg.outcomes if o.station == station)


def probes(leg: R.RealWorld, station: Optional[str] = None) -> List[str]:
    return [f.probe for f in leg.findings if station is None or f.station == station]


def evidence_of(leg: R.RealWorld) -> List[Dict[str, Any]]:
    with open(os.path.join(leg.folder.path, "evidence.jsonl"), "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def everything_written(leg: R.RealWorld) -> str:
    """Every word the run folder holds: the report, the evidence, and the text beside each screenshot."""
    texts = []
    for name in sorted(os.listdir(leg.folder.path)):
        if name.endswith((".md", ".jsonl", ".txt")):
            texts.append(read(os.path.join(leg.folder.path, name)))
    return "\n".join(texts)


class ReplayRefusingEstate(W.ScreensEstate):
    """The estate before Spec AER360-RUN-ROAD §3.2: a second run of the day under a reference already carried is refused as a replay."""

    def review_or_create(self, headers, body, create):  # type: ignore[no-untyped-def]
        reference = "S-" + str((body or {}).get("reference"))
        if create and any(row["reference"] == reference for row in self.sets.values()):
            return 409, {"error": {"code": S.IDEMPOTENCY_KEY_REUSED, "message": REPLAY_SENTENCE, "detail": {"reference": reference}}}
        return super().review_or_create(headers, body, create)


class WaitingEstate(W.ScreensEstate):
    """An estate whose runs each wait for one approval: the run stands pending in the Approver inbox until a seated approver presses."""

    def review(self, caller, charter, rows, acknowledged):  # type: ignore[no-untyped-def]
        out = super().review(caller, charter, rows, acknowledged)
        out["approvalsRequired"] = max(1, out["approvalsRequired"])
        out["payload"]["approval"]["approvalsRequired"] = out["approvalsRequired"]
        return out


class DraftLeavingEstate(W.ScreensEstate):
    """An estate that refuses the submission, so the run the press created stands a draft — the founder's 6 October, met at the screen."""

    def submit_set(self, headers, set_id):  # type: ignore[no-untyped-def]
        raise D.Refusal("SET_NOT_EDITABLE", detail={"cause": "this double refuses every submission"})


class SigningRefusingEstate(W.ScreensEstate):
    """A platform that refuses every payment at the signing: the run executes and each payment fails, the platform's sentence its reason."""

    SAID = "SIGNING_REFUSED: The signing platform refused this payment: the policy denied it (legacy_limit_zero)."

    def drive_payment(self, caller, instruction):  # type: ignore[no-untyped-def]
        self.fail_instruction(caller, instruction, self.SAID, {"said": self.SAID})


class RefusingCancelEstate(DraftLeavingEstate):
    """An estate that leaves the run a draft and refuses its cancellation too: R9's Cancel is refused, and R9 must say so."""

    def cancel_set(self, headers, set_id):  # type: ignore[no-untyped-def]
        raise D.Refusal("SET_NOT_EDITABLE", detail={"cause": "this double refuses every cancellation"})


class RefusingApprovalEstate(WaitingEstate):
    """A run that waits, whose approval the estate refuses: the run stands waiting for an approval at the end of the run."""

    def approval(self, headers, set_id, action, body):  # type: ignore[no-untyped-def]
        if action == "approve":
            raise D.Refusal("SET_NOT_APPROVABLE", detail={"cause": "this double refuses every approval"})
        return super().approval(headers, set_id, action, body)


class DoubledInboxEstate(WaitingEstate):
    """An Approver inbox listing each waiting run twice, the second under another id — two cards that read alike, as a run an earlier attempt left would."""

    def inbox(self, headers):  # type: ignore[no-untyped-def]
        status, answer = super().inbox(headers)
        answer["sets"] = [card for row in answer["sets"] for card in (row, dict(row, id=row["id"] + "-twin"))]
        return status, answer


# ======================================================================================================================
# The whole walk, R1 to R9, on an estate born by the CLI road with --email.
# ======================================================================================================================
class TheWalk(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s = Setting()
        cls.estate = cls.s.estate
        cls.minted: List[str] = []  # every one-time link the People page was answered with, kept here to prove none reaches the run folder
        mint = cls.estate.mint_invite

        def recording(headers, body):  # type: ignore[no-untyped-def]
            status, answer = mint(headers, body)
            cls.minted.append(answer["url"])
            return status, answer

        cls.estate.mint_invite = recording  # type: ignore[assignment]
        cls.leg = cls.s.walk()
        cls.written = everything_written(cls.leg)

    def test_every_station_passes_in_order(self) -> None:
        self.assertEqual([o.station for o in self.leg.outcomes], R.STATION_IDS)
        self.assertEqual(outcomes(self.leg), {s: E.PASS for s in R.STATION_IDS}, "\n".join(self.leg.said))
        self.assertEqual(self.leg.findings, [])

    def test_r1_enrols_by_the_one_time_link_and_reads_the_register_and_the_session(self) -> None:
        line = line_of(self.leg, "R1")
        self.assertIn("enrolled by the one-time link: the page said \"%s" % S.ENROLMENT_KEY_EXISTS, line)
        self.assertIn("invitee_email %s" % T.REAL_WORLD_BIRTH_EMAIL, line)
        self.assertIn("the passkey's row stands", line)
        row = next(r for r in self.estate.invites.values() if r["credentialId"] == self.estate.founder_credential)
        self.assertIsNotNone(row["redeemedAt"])
        self.assertTrue(any(p["credentialId"] == self.estate.founder_credential for p in self.estate.passkeys.values()))

    def test_the_authenticator_is_a_ctap2_platform_key_that_verifies_the_user(self) -> None:
        cdp = [c for b in self.s.world.browsers for c in b.contexts]
        self.assertGreaterEqual(len(cdp), 4)  # the founder (R1, then a fresh context at R2), Ada and Ben, each in a context of their own
        for page in self.s.world.pages():
            self.assertEqual(len(page.authenticators), 1)
            options = page.authenticators[0].options
            self.assertEqual((options["protocol"], options["hasResidentKey"], options["hasUserVerification"], options["isUserVerified"]),
                             ("ctap2", True, True, True))

    def test_r2_signs_in_from_a_fresh_context_and_reads_the_estate_named_in_the_sidebar(self) -> None:
        line = line_of(self.leg, "R2")
        self.assertIn("signed in from a fresh context with the stored credential; the sidebar names %s" % A.ESTATE["company"], line)
        self.assertIn("the page lands on \"Onboarding\"", line)  # the landing law: a new estate is sent to its journey's first stage

    def test_r3_reads_the_entries_at_zero_before_and_at_the_charter_figures_after(self) -> None:
        self.assertEqual([(e["name"], e["perPaymentUsd"], e["perDayUsd"]) for e in self.leg.facts["entries_before"]],
                         [("aer-accounts", 0, 0), ("Harriet Founder (author)", 0, 0)])
        self.assertEqual([(e["name"], e["perPaymentUsd"], e["perDayUsd"]) for e in self.leg.facts["entries_after"]],
                         [("aer-accounts", 100, 1000), ("Harriet Founder (author)", 100, 1000)])
        ceilings = self.leg.facts["receipt_ceilings"]
        self.assertEqual((ceilings["perPaymentUsd"], ceilings["perDayUsd"]), (100, 1000))
        self.assertEqual(sorted(e["name"] for e in ceilings["entries"]), ["Harriet Founder (author)", "aer-accounts"])
        self.assertIn("the signing entries before the interview: aer-accounts 0/0, Harriet Founder (author) 0/0", line_of(self.leg, "R3"))
        self.assertIn("the signing entries after the write: aer-accounts 100/1000, Harriet Founder (author) 100/1000", line_of(self.leg, "R3"))
        # the platform's read road, read-only, under the admin credential, for this estate's own account and no other
        reads = [r for r in self.estate.platform.requests if r["path"].endswith("/policies")]
        self.assertEqual(len(reads), 2)
        self.assertTrue(all(r["method"] == "GET" and r["path"] == S.ADMIN_POLICIES_ROUTE % self.estate.aap_account_id for r in reads))

    def test_r3_tries_a_zero_at_c2_once_and_reads_the_refusal_in_the_estates_words(self) -> None:
        zeros = [x for x in self.leg.exchanges if x.route.endswith("/answers") and '"cents": "0"' in json.dumps(x.sent)]
        self.assertEqual(len(zeros), 1)
        self.assertEqual(zeros[0].status, 400)
        self.assertEqual(R.kind_of(zeros[0].status, zeros[0].json), R.MALFORMED_QUESTION)
        self.assertIn("a zero at C2 was refused at the page", line_of(self.leg, "R3"))
        self.assertIn(S.CEILING_ZERO_REFUSED, line_of(self.leg, "R3"))
        self.assertIn(("C2's refusal", next(s for w, s in self.leg.next_steps["R3"] if w == "C2's refusal")), self.leg.next_steps["R3"])

    def test_r3_reads_the_two_ceiling_lines_of_the_read_back_and_the_notes_beside_c2_and_c3(self) -> None:
        line = line_of(self.leg, "R3")
        for which, (_, prompt) in E.CEILING_READBACK_LINES.items():
            cents = A.MONEY["company_ceiling_cents"] if which == "perPayment" else A.MONEY["daily_total_cents"]
            partner = A.MONEY["daily_total_cents"] if which == "perPayment" else A.MONEY["company_ceiling_cents"]
            self.assertIn("the read-back says %r: %r" % (prompt, E.ceiling_read_back_sentence(which, cents, partner, False)), line)
        self.assertIn("C2's note: ", line)
        self.assertIn("C3's note: ", line)

    def test_r3_types_the_untidy_spellings_and_the_estate_folds_the_roster(self) -> None:
        interview = next(iv for iv in self.estate.interviews.values() if iv["interviewType"] == "policy")
        latest = {qid: row["value"] for qid, row in self.estate.latest(interview["id"]).items()}
        census = [e["email"] for e in latest["A8"]["entries"]]
        self.assertIn("Harriet.Founder@aeredium.io ", census)
        self.assertIn(" ADA.Approver@aeredium.io", census)
        self.assertEqual(latest["C2"], {"cents": A.MONEY["company_ceiling_cents"]})
        self.assertEqual(latest["C3"], {"cents": A.MONEY["daily_total_cents"]})
        self.assertIn("harriet.founder@aeredium.io", [s["user_id"] for s in self.estate.whitelist_seats])
        self.assertIn("ada.approver@aeredium.io", [s["user_id"] for s in self.estate.whitelist_seats])
        self.assertTrue(all(s["user_id"] == s["user_id"].strip().lower() for s in self.estate.whitelist_seats))

    def test_r4_invites_ada_from_her_seat_and_ben_from_the_form_each_redeeming_in_a_context_of_their_own(self) -> None:
        line = line_of(self.leg, "R4")
        self.assertIn("Ada Approver invited from the seat and enrolled in a context of their own: \"%s" % S.ENROLMENT_KEY_AND_SEAT_GRANTED, line)
        self.assertIn("Ben Signatory invited from the form and enrolled in a context of their own: \"%s" % S.ENROLMENT_KEY_EXISTS, line)
        self.assertIn("Ada Approver: 'Seated' on the page; the seat view reads seated", line)
        self.assertIn("Ben Signatory: 'Redeemed' on the register at harness+ben@aeredium.io (an approver of changes, so no seat), standing author", line)
        minted = {r["displayName"]: r for r in self.estate.invites.values() if r.get("role") == "author"}
        self.assertEqual(minted["Ada Approver"]["email"], "ADA.Approver@aeredium.io")  # the seat's address; the email field's value is sanitised by the browser
        self.assertEqual(minted["Ben Signatory"]["email"], A.PEOPLE["ben"].email)
        self.assertTrue(all(r["state"] == "redeemed" for r in minted.values()))
        self.assertIn("the seat's Invite filled the address and left 'Full name' empty", " ".join(self.leg.notes["R4"]))

    def test_r5_gives_the_funding_wallet_then_presses_a_new_wallet_on_group_100(self) -> None:
        line = line_of(self.leg, "R5")
        self.assertIn("the page first offered %r" % S.GIVE_FUNDING_WALLET, line)
        self.assertIn("the press asked \"%s\" and no limit" % S.WHOSE_WALLET_LEGEND, line)
        wallet = self.leg.facts["wallet"]
        self.assertEqual(wallet["walletNumber"], "2")
        self.assertIn("the page says \"Wallet 2 is born: %s. It is counted below.\"" % wallet["address"], line)
        self.assertIn("keyed True", line)
        self.assertIn("the account stands on group-100", line)

    def test_r6_adds_the_owners_wallet_twice_and_two_approvers_whitelist_each_in_their_own_contexts(self) -> None:
        line = line_of(self.leg, "R6")
        self.assertIn("Contoso Legal's address was typed with a trailing space and the estate stored %s" % D.OWNER_WALLET_FOR_TESTS.lower(), line)
        self.assertEqual(line.count("Ada Approver: pending_promotion (1 of 2)"), 2)
        self.assertEqual(line.count("Ben Signatory: whitelisted"), 2)
        self.assertIn("1 of 2 approvals recorded for this address.", line)
        self.assertEqual([p["status"] for p in self.leg.facts["payees"]], ["whitelisted", "whitelisted"])
        typed = [x for x in self.leg.exchanges if x.route == "POST /v1/payees"]
        self.assertEqual(len(typed), 2)
        self.assertEqual(typed[1].sent["addresses"][0]["address"], D.OWNER_WALLET_FOR_TESTS + " ")  # sent as typed; the estate trims it
        approvals = [x for x in self.leg.exchanges if x.route.endswith("/approve") and "/payees/" in x.route]
        self.assertEqual([x.who for x in approvals], ["Ada Approver", "Ben Signatory"] * 2)

    def test_r7_and_r7b_pay_the_one_dollar_book_between_them_to_the_owners_wallet_and_nothing_else(self) -> None:
        runs = self.leg.facts["runs"]
        self.assertEqual([(r["station"], r["invoices"]) for r in runs], [("R7", ["HH-0001", "HH-0002"]), ("R7b", ["HH-0003"])])
        self.assertEqual(runs[0]["reference"], runs[1]["reference"])
        self.assertEqual(runs[0]["reference"], "S-" + S.DEFAULT_REFERENCE)
        self.assertNotEqual(runs[0]["id"], runs[1]["id"])
        self.assertEqual(self.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), sum(int(p.amount_minor) for p in A.payments()))
        self.assertEqual(self.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 1000000)  # one dollar of USDC, six decimals
        self.assertIn("the owner's wallet US$0.00 → US$0.51", line_of(self.leg, "R7"))
        self.assertIn("the owner's wallet US$0.51 → US$1.00", line_of(self.leg, "R7b"))
        self.assertIn("a second, different run (%s) under the same reference 'S-Payment run' as R7's (%s), the same day" % (runs[1]["id"], runs[0]["id"]),
                      line_of(self.leg, "R7b"))

    def test_the_screen_creates_and_submits_and_nobody_calls_execute(self) -> None:
        routes = [(x.station, x.who, x.method, re.sub(r"set-[0-9a-f]+", "<id>", x.path)) for x in self.leg.exchanges]
        for station in ("R7", "R7b"):
            self.assertIn((station, "Harriet Founder", "POST", "/v1/sets"), routes)
            self.assertIn((station, "Harriet Founder", "POST", "/v1/sets/<id>/submit"), routes)
        self.assertFalse(any(path.endswith("/execute") for _, _, _, path in routes))
        self.assertFalse(any(c["path"].endswith("/execute") for c in self.estate.calls))
        created = [x for x in self.leg.exchanges if x.route == "POST /v1/sets"]
        self.assertTrue(all(x.sent["reference"] == S.DEFAULT_REFERENCE and x.sent["walletId"] == self.leg.facts["wallet"]["walletId"] for x in created))

    def test_the_gas_account_is_credited_once_on_the_reviews_shortfall_sized_as_t26_sizes_it(self) -> None:
        credits = [r for r in self.estate.platform.requests if r["path"].endswith("/gas-account/credits")]
        self.assertEqual(len(credits), 1)
        self.assertEqual(json.loads(credits[0]["body"])["amount_usd_cents"], E.Runner.gas_credit_for(80))
        self.assertEqual(len(self.leg.facts["gas_credits"]), 1)
        self.assertIn("the review refused GAS_SHORTFALL", line_of(self.leg, "R7"))
        self.assertNotIn("GAS_SHORTFALL", line_of(self.leg, "R7b"))  # R7's credit covers R7b: no second cure without a second refusal

    def test_r8_finds_the_two_legs_agree_and_holds_each_walked_step_against_the_manual(self) -> None:
        line = line_of(self.leg, "R8")
        self.assertIn("the legs agree on R1/S1 pass, R2/S2 pass, R3/S3 pass, R4/S4 pass, R5/S5 pass, R6/S6 pass, R7/S7 pass, R7b/S7 pass", line)
        self.assertIn("the pages' next steps held against 15 of the Client Manual's words, for the steps this run walked", line)
        self.assertTrue(any(n.startswith("R1, beside the manual: the manual says 'Open the invitation link.") for n in self.leg.notes["R8"]))

    def test_r9_cancels_nothing_where_every_run_landed(self) -> None:
        self.assertIn("cancelled: none; left as they stand: %s settled, %s settled" % tuple(r["id"] for r in self.leg.facts["runs"]), line_of(self.leg, "R9"))
        self.assertFalse(any(c["path"].endswith("/cancel") for c in self.estate.calls))

    def test_every_station_records_the_pages_own_next_step(self) -> None:
        for station in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R7b"):
            self.assertTrue(self.leg.next_steps[station], station)
        self.assertIn("What to do next, in the page's words", read(self.leg.report_path))

    def test_each_station_ends_with_a_screenshot_and_its_text(self) -> None:
        names = os.listdir(self.leg.folder.path)
        for station in R.STATION_IDS:
            if station == "R8":
                continue
            self.assertTrue(any(n.startswith("%s-" % station) and n.endswith("-end.png") for n in names), station)
            self.assertTrue(any(n.startswith("%s-" % station) and n.endswith("-end.txt") for n in names), station)

    def test_no_secret_reaches_the_run_folder(self) -> None:
        self.assertEqual(len(self.minted), 2)
        secrets = [self.s.link.split("#", 1)[1]] + [u.split("#", 1)[1] for u in self.minted]
        secrets += [row["csrfToken"] for row in self.estate.sessions.values()] + list(self.estate.sessions) + [self.estate.platform.admin_key]
        for name in ("harriet", "ada", "ben"):
            secrets.append(json.loads(read(os.path.join(self.leg.store_dir, "%s.json" % name)))["credential"]["privateKey"])
        for secret in secrets:
            self.assertNotIn(secret, self.written)
            self.assertNotIn(secret, "\n".join(self.leg.said))
        logged = [x.json["url"] for x in self.leg.exchanges if x.route == "POST /v1/invites"]
        self.assertEqual(logged, ["%s#%s" % (u.split("#", 1)[0], R.last4(u.split("#", 1)[1])) for u in self.minted])  # the token kept to its last four
        assertions = [x for x in self.leg.exchanges if x.route == "POST /v1/auth/login/verify"]
        self.assertTrue(assertions and all(len(x.sent["response"]["response"]["signature"]) <= 5 for x in assertions))

    def test_each_persons_credential_is_kept_0600_and_moves_with_its_signature_counter(self) -> None:
        for name in ("harriet", "ada", "ben"):
            path = os.path.join(self.leg.store_dir, "%s.json" % name)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600, name)
            record = json.loads(read(path))
            self.assertEqual((record["kind"], record["person"], record["rpId"]), (R.CREDENTIAL_KIND, name, self.estate.rp_id))
            self.assertEqual(record["workspace"]["accountId"], self.estate.aap_account_id)
            raw = W.unb64(record["credential"]["credentialId"])
            row = next(r for k, r in self.estate.passkeys.items() if PK.b64url_decode(k) == raw)
            self.assertEqual(record["credential"]["signCount"], row["signCount"], name)  # saved after every ceremony, so the estate's counter and the file agree
        path = os.path.join(self.leg.store_dir, R.STATE_FILE)
        state = json.loads(read(path))
        self.assertEqual(state["estate"]["accountId"], self.estate.aap_account_id)
        self.assertEqual(state["wallet"]["walletNumber"], "2")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_the_report_is_the_api_legs_shape_with_the_pages_words_beside_the_store(self) -> None:
        text = read(self.leg.report_path)
        self.assertTrue(text.startswith("# AER 360 browser leg run — Harness Real World — %s — " % A.ESTATE["company"]))
        self.assertIn("| Station | Outcome | Line |", text)
        self.assertIn("| R7b The second press | pass |", text)
        self.assertIn("## Every request the browser made", text)
        self.assertIn("Came back, verbatim:", text)
        self.assertIn("The page said:", text)
        self.assertIn("Findings in this run: 0.", text)


# ======================================================================================================================
# Untidy births: without --email, and a page naming another estate.
# ======================================================================================================================
class TheBirthWithoutEmail(unittest.TestCase):
    def test_the_warning_stops_r1_naming_the_record_script_and_the_rerun_after_it_passes(self) -> None:
        s = Setting(birth_email=None)
        self.assertIn(S.NO_EMAIL_LINE, read(s.birth))
        first = s.walk()
        self.assertEqual(outcomes(first)["R1"], E.FAILED_PREREQUISITE)
        self.assertIn(R.EMAIL_NOT_RECORDED, line_of(first, "R1"))
        self.assertIn("dist-deploy/record-founder-emails.mjs", line_of(first, "R1"))
        self.assertIn("rerun with --from S1", line_of(first, "R1"))
        # the whole run stops there: a founder whose presses carry no name walks nothing more, and nothing is paid
        self.assertTrue(all(outcomes(first)[st] == E.NOT_RUN for st in R.STATION_IDS[1:]))
        self.assertEqual([(f.probe, f.kind) for f in first.findings], [(R.EMAIL_NOT_RECORDED, R.SCREEN)])
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 0)
        # the founder enrolled before the register was read, so the rerun signs in; the record script fills the blank row
        s.estate.record_founder_emails()
        second = s.walk(start_at="S1")
        self.assertEqual(outcomes(second)["R1"], E.PASS, line_of(second, "R1"))
        self.assertIn("signed in with the credential stored at", line_of(second, "R1"))
        self.assertIn("invitee_email %s — recorded by the record script after a birth without --email, whose one-line warning this run's printout carried: %r" % (
            T.REAL_WORLD_BIRTH_EMAIL, S.NO_EMAIL_LINE), line_of(second, "R1"))
        self.assertEqual(outcomes(second), {s_: E.PASS for s_ in R.STATION_IDS}, "\n".join(second.said))

    def test_a_blank_email_stops_the_run_even_where_the_printout_lost_the_warning(self) -> None:
        # invite.mjs prints its warning to standard error (invite.ts:159), so a printout saved with > alone lacks it: the stop does not depend on it
        s = Setting(birth_email=None, printout=lambda text: text.replace(S.NO_EMAIL_LINE + "\n", ""))
        leg = s.leg()
        leg.run()
        self.assertEqual(outcomes(leg)["R1"], E.FAILED_PREREQUISITE)
        self.assertIn("the printout this run read carries no warning that --email was left out (invite.mjs prints it to standard error, so a printout "
                      "saved without 2>&1 leaves it out): run the record script", line_of(leg, "R1"))
        self.assertTrue(all(outcomes(leg)[st] == E.NOT_RUN for st in R.STATION_IDS[1:]))

    def test_a_birth_under_another_address_is_a_finding(self) -> None:
        s = Setting(birth_email="someone.else@aeredium.io")
        leg = s.leg()
        leg.run()
        self.assertIn("the founder was born with another address", probes(leg, "R1"))


class TheStoredCredentials(unittest.TestCase):
    def test_a_printout_naming_no_estate_opens_no_link(self) -> None:
        s = Setting(printout=lambda text: "\n".join(l for l in text.splitlines() if not l.startswith("Invite for ")))
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R1"], E.FAILED_PREREQUISITE)
        self.assertIn("the printout names no estate", line_of(leg, "R1"))
        self.assertEqual(s.estate.calls, [])
        self.assertNotIn(s.link.split("#", 1)[1], everything_written(leg))

    def test_a_store_folder_of_its_own_for_every_base_but_production(self) -> None:
        tmp = tempfile.mkdtemp(prefix="hrw-store-")
        live = R.RealWorld(base=R.DEFAULT_BASE, store_root=tmp, runs_root=tmp, dry_folder=True, say=lambda t: None)
        other = R.RealWorld(base="https://estate.test:8443", store_root=tmp, runs_root=tmp, dry_folder=True, say=lambda t: None)
        self.assertEqual(live.store_dir, os.path.join(tmp, R.STORE_FOLDER))
        self.assertEqual(other.store_dir, os.path.join(tmp, R.STORE_FOLDER, "estate.test-8443"))

    def test_a_resume_with_nothing_stored_says_so_and_each_station_names_its_prerequisite(self) -> None:
        s = Setting()
        leg = s.walk(start_at="S5")
        self.assertIn("resume — Harriet Founder has no stored credential for this estate; the stations needing Harriet Founder say so", leg.said)
        self.assertEqual(outcomes(leg)["R5"], E.FAILED_PREREQUISITE)
        self.assertIn(R.NO_FOUNDER_SESSION, line_of(leg, "R5"))
        self.assertEqual(s.estate.calls, [])

    def test_a_credential_of_an_earlier_estate_is_set_aside_never_used_and_never_deleted(self) -> None:
        first = Setting()
        self.assertEqual(outcomes(first.walk())["R1"], E.PASS)
        reborn = W.ScreensEstate(aap_account_id="aap-account-reborn", platform=first.estate.platform, chain=first.estate.chain)
        later = Setting(estate=reborn)
        later.store = first.store  # the operator's one store, across a rebirth of the estate on the same platform
        leg = later.walk()
        self.assertEqual(outcomes(leg), {st: E.PASS for st in R.STATION_IDS}, "\n".join(leg.said))
        self.assertTrue(any(n.startswith("the browser leg's state was of account %s and this birth's estate is account aap-account-reborn, so this run starts "
                                         "afresh (the earlier state kept at " % first.estate.aap_account_id) for n in leg.notes["start"]))
        self.assertIn("enrolled by the one-time link", line_of(leg, "R1"))
        self.assertTrue(any("was made on account %s, and this run's estate is account aap-account-reborn; it is not used" % first.estate.aap_account_id in n
                            for n in leg.notes["R1"]))
        folder = leg.store_dir
        for name in ("harriet", "ada", "ben", "state"):
            self.assertEqual(len([n for n in os.listdir(folder) if n.startswith(name + ".") and n != name + ".json"]), 1, name)
        aside = [n for n in os.listdir(folder) if n.startswith("harriet.") and n != "harriet.json"]
        self.assertEqual(json.loads(read(os.path.join(folder, aside[0])))["workspace"]["accountId"], first.estate.aap_account_id)
        self.assertEqual(json.loads(read(os.path.join(folder, "harriet.json")))["workspace"]["accountId"], "aap-account-reborn")


class TheWrongEstate(unittest.TestCase):
    def test_a_page_naming_an_estate_not_the_harnesss_own_stops_the_run_before_any_press(self) -> None:
        s = Setting(company="Someone Else Pty Ltd")
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R1"], E.FAIL)
        self.assertIn(R.WRONG_ESTATE, probes(leg, "R1"))
        self.assertIn("'Someone Else Pty Ltd', which is not one of the harness's own", line_of(leg, "R1"))
        self.assertTrue(all(outcomes(leg)[st] == E.NOT_RUN for st in R.STATION_IDS[1:]))
        self.assertFalse(any(e["kind"] == "press" for e in evidence_of(leg)))
        self.assertFalse(os.path.exists(os.path.join(leg.store_dir, "harriet.json")))
        self.assertEqual(s.estate.calls, [])  # the printout named another estate: the link was never opened

    def test_a_page_naming_the_other_harness_estate_than_the_printout_stops_the_run(self) -> None:
        s = Setting(printout=lambda text: text.replace("Invite for %s" % A.ESTATE["company"], "Invite for Harness Treasury Pty Ltd"))
        leg = s.walk()
        self.assertIn("the page names the estate %r, and this run's estate is 'Harness Treasury Pty Ltd'" % A.ESTATE["company"], line_of(leg, "R1"))
        self.assertTrue(all(outcomes(leg)[st] == E.NOT_RUN for st in R.STATION_IDS[1:]))

    def test_the_guard_admits_the_harnesss_own_estates_only(self) -> None:
        for name in ("Harness Holdings Pty Ltd", "Harness Treasury", "Harness Treasury Pty Ltd"):
            self.assertTrue(T.is_harness_estate(name), name)
        for name in ("Harness Holdings", "Someone Else Pty Ltd", "", None, "Harness Treasury-like Pty Ltd"):
            self.assertFalse(T.is_harness_estate(name), name)


# ======================================================================================================================
# The second leg on the same estate: --from, the duplicate screen, the replay, the wait.
# ======================================================================================================================
class TheResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s = Setting()
        cls.first = cls.s.walk()
        cls.s.estate.age_runs(1)  # a day passes; the first run's payments stand within the screen's seven days
        cls.second = cls.s.walk(start_at="S7")

    def test_the_first_walk_passed(self) -> None:
        self.assertEqual(outcomes(self.first), {s: E.PASS for s in R.STATION_IDS})

    def test_from_s7_skips_r1_to_r6_and_signs_every_person_in_with_their_stored_credential(self) -> None:
        got = outcomes(self.second)
        self.assertEqual([got[s] for s in R.STATION_IDS[:6]], [E.SKIPPED] * 6)
        self.assertIn("resume — Harriet Founder signed in with the stored credential", self.second.said)
        self.assertIn("resume — Ada Approver signed in with the stored credential", self.second.said)
        self.assertIn("resume — Ben Signatory signed in with the stored credential", self.second.said)

    def test_the_duplicate_screen_is_confirmed_as_a_founder_confirms_it_naming_the_earlier_runs_payments(self) -> None:
        self.assertEqual((outcomes(self.second)["R7"], outcomes(self.second)["R7b"]), (E.PASS, E.PASS), "\n".join(self.second.said))
        ticks = [e for e in evidence_of(self.second) if e["kind"] == "tick" and S.ACKNOWLEDGE_REPEATS_WORDS in e["what"]]
        self.assertEqual([e["station"] for e in ticks], ["R7", "R7b"])
        again = [x for x in self.second.exchanges if x.route == "POST /v1/sets/review" and x.sent.get("duplicatesAcknowledged") is True]
        self.assertEqual(len(again), 2)
        created = [x for x in self.second.exchanges if x.route == "POST /v1/sets"]
        self.assertTrue(all(x.sent["duplicatesAcknowledged"] is True for x in created))
        self.assertIn("the page warns, word for word: \"", line_of(self.second, "R7"))
        self.assertIn(E.DUPLICATE_UNACKNOWLEDGED_SENTENCE, line_of(self.second, "R7"))
        notes = " ".join(self.second.notes["R7"])
        first_run = self.first.facts["runs"][0]["id"]
        self.assertIn("(Spec T28)", notes)
        self.assertIn(first_run, json.dumps([f for f in self.s.estate.sets.values()]))
        self.assertTrue(any(n.startswith("R7, beside the manual: the manual's word for the founder's confirmation of a repeat") for n in self.second.notes["R8"]))
        self.assertEqual(outcomes(self.second)["R8"], E.PASS, line_of(self.second, "R8"))

    def test_the_second_dollar_goes_to_the_owners_wallet_and_nowhere_else(self) -> None:
        self.assertEqual(self.s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 2 * 1000000)

    def test_a_step_the_rerun_did_not_walk_is_not_held_against_the_manual(self) -> None:
        # R7's Submit and landed, R7b's Submit and its replay sentence set beside the page: the charter's, the wallet's and the payees' steps not walked
        self.assertIn("held against 4 of the Client Manual's words, for the steps this run walked", line_of(self.second, "R8"))


class TheSecondPress(unittest.TestCase):
    def test_a_replay_refusal_of_the_second_run_is_a_finding_in_the_estates_words(self) -> None:
        s = Setting(estate=ReplayRefusingEstate())
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.PASS)
        self.assertEqual(outcomes(leg)["R7b"], E.FAIL)
        self.assertIn("R7b: the second run was refused as a replay", probes(leg, "R7b"))
        finding = next(f for f in leg.findings if f.probe == "R7b: the second run was refused as a replay")
        self.assertIn(REPLAY_SENTENCE, finding.page)
        self.assertEqual(finding.kind, R.REFUSED)
        self.assertIn("Submit this run created no run", line_of(leg, "R7b"))
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 510000)  # R7's half dollar and a cent, nothing more
        self.assertIn("a SCREEN fault at R7b", probes(leg, "R8"))

    def test_a_duplicate_naming_a_payment_of_this_run_is_a_finding_and_nothing_is_pressed(self) -> None:
        with mock.patch.object(T, "REAL_WORLD_SECOND_PRESS", ("P1",)):
            s = Setting()
            leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.PASS)
        self.assertEqual(outcomes(leg)["R7b"], E.FAIL)
        self.assertIn(E.REPEAT_WITHIN_RUN_PROBE % "R7b", probes(leg, "R7b"))
        self.assertIn("nothing was acknowledged and nothing created (Spec T28's bound)", line_of(leg, "R7b"))
        self.assertFalse(any(e["kind"] == "tick" and e["station"] == "R7b" for e in evidence_of(leg)))
        self.assertEqual(len([x for x in leg.exchanges if x.route == "POST /v1/sets"]), 1)
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 510000)


class TheRunThatDidNotLand(unittest.TestCase):
    def test_a_run_left_a_draft_is_a_finding_in_the_pages_words_and_r9_cancels_it_from_its_own_page(self) -> None:
        s = Setting(estate=DraftLeavingEstate())
        leg = s.walk()
        self.assertEqual((outcomes(leg)["R7"], outcomes(leg)["R7b"]), (E.FAIL, E.FAIL))
        self.assertIn("R7: the run stays a draft", probes(leg, "R7"))
        self.assertIn("not submitted (SET_NOT_EDITABLE", line_of(leg, "R7"))
        drafts = [r["id"] for r in leg.facts["runs"]]
        self.assertEqual(len(drafts), 2)
        self.assertEqual(outcomes(leg)["R9"], E.PASS)
        self.assertIn("cancelled: %s draft → cancelled (the page's Cancel), %s draft → cancelled (the page's Cancel)" % tuple(drafts), line_of(leg, "R9"))
        self.assertEqual([s.estate.sets[i]["status"] for i in drafts], ["cancelled", "cancelled"])
        presses = [e for e in evidence_of(leg) if e["station"] == "R9" and e["kind"] == "press"]
        self.assertEqual([e["what"].split(" on ")[0] for e in presses], ["pressed %r" % S.CANCEL_RUN] * 2)
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 0)

    def test_a_payment_refused_at_the_signing_is_read_on_the_runs_page_in_the_platforms_words(self) -> None:
        s = Setting(estate=SigningRefusingEstate())
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.FAIL)
        finding = next(f for f in leg.findings if f.probe == "R7: HH-0001 failed was not landed")
        self.assertEqual(finding.kind, R.ANSWERED_WITH_ERROR)
        self.assertIn(SigningRefusingEstate.SAID, finding.page)
        self.assertEqual(finding.store, SigningRefusingEstate.SAID)
        self.assertIn("0 of 2 payment(s) landed (no hash); the owner's wallet US$0.00 → US$0.00", line_of(leg, "R7"))
        self.assertNotIn("the owner's wallet moved by another figure", " ".join(probes(leg)))


class StrangerReviewingEstate(W.ScreensEstate):
    """An estate whose review names another address for the first row than the payee the page chose: the harness must press nothing."""

    STRANGER = T.checksum_address("0x" + "1234" * 10)

    def review(self, caller, charter, rows, acknowledged):  # type: ignore[no-untyped-def]
        out = super().review(caller, charter, rows, acknowledged)
        if out["payload"]["rows"]:
            out["payload"]["rows"][0]["address"] = self.STRANGER
        return out


class TheOwnersWallet(unittest.TestCase):
    def test_a_review_naming_another_address_stops_before_submit_and_nothing_moves(self) -> None:
        s = Setting(estate=StrangerReviewingEstate())
        leg = s.walk()
        self.assertEqual((outcomes(leg)["R7"], outcomes(leg)["R7b"]), (E.FAIL, E.FAIL))
        self.assertIn("the review the page received names %s" % StrangerReviewingEstate.STRANGER, line_of(leg, "R7"))
        self.assertIn("so 'Submit this run' was not pressed and nothing moved", line_of(leg, "R7"))
        self.assertFalse(any(x.route == "POST /v1/sets" for x in leg.exchanges))
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 0)
        self.assertEqual(s.estate.chain.balance_of(StrangerReviewingEstate.STRANGER), 0)

    def test_two_payees_that_read_alike_are_a_finding_and_neither_is_chosen(self) -> None:
        estate = W.ScreensEstate()
        estate.hold_payee("Northwind Supplies", T.PAYEE_CHAIN, T.checksum_address("0x" + "4321" * 10))  # an earlier payee of the same name elsewhere
        s = Setting(estate=estate)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R6"], E.PASS, line_of(leg, "R6"))
        self.assertEqual(outcomes(leg)["R7"], E.FAIL)
        self.assertIn("R7: two payees read alike", probes(leg, "R7"))
        self.assertFalse(any(x.route == "POST /v1/sets" and x.station == "R7" for x in leg.exchanges))


class TheWaitingRun(unittest.TestCase):
    def test_a_run_that_waits_is_approved_in_the_seated_approvers_inbox_and_executes_on_that_press(self) -> None:
        s = Setting(estate=WaitingEstate())
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.PASS, "\n".join(leg.said))
        self.assertIn("the page says \"Submitted: waiting for 1 approval.\"", line_of(leg, "R7"))
        self.assertIn("Ada Approver approved it in the Approver inbox", line_of(leg, "R7"))
        approvals = [x for x in leg.exchanges if x.route.startswith("POST /v1/approvals/") and x.route.endswith("/approve")]
        self.assertEqual([(x.station, x.who) for x in approvals], [("R7", "Ada Approver"), ("R7b", "Ada Approver")])
        self.assertFalse(any(c["path"].endswith("/execute") for c in s.estate.calls))
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 1000000)


# ======================================================================================================================
# Money: the wallet the owner funds, the gas the review asks for.
# ======================================================================================================================
class TheMoney(unittest.TestCase):
    def test_a_wallet_short_of_the_book_stops_r7_naming_the_address_and_the_figure_and_the_harness_funds_nothing(self) -> None:
        s = Setting(new_wallet_usdc_cents=0)
        leg = s.walk()
        self.assertEqual((outcomes(leg)["R7"], outcomes(leg)["R7b"]), (E.FAILED_PREREQUISITE, E.FAILED_PREREQUISITE))
        wallet = leg.facts["wallet"]
        self.assertIn(R.WALLET_NOT_FUNDED, line_of(leg, "R7"))
        # asked once, for the whole of this run's book: R7's rows and R7b's
        self.assertIn("fund wallet 2 (%s) with US$1.00 of USDC on %s — this run's book needs US$1.00 from here and the chain reads US$0.00 there — then "
                      "rerun with --from S7" % (wallet["address"], T.C9_NETWORK_CHOICE), line_of(leg, "R7"))
        self.assertIn("with US$0.49 of USDC", line_of(leg, "R7b"))
        self.assertIn("then rerun with --from S7b", line_of(leg, "R7b"))
        self.assertIn("the harness funds no wallet, because funding a wallet is the owner's act", line_of(leg, "R7"))
        self.assertFalse(any(x.route == "POST /v1/sets" for x in leg.exchanges))
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 0)
        rpc = [e for e in evidence_of(leg) if e["kind"] == "outside" and "rpc" in e["route"]]
        self.assertTrue(rpc and all('"eth_call"' in json.dumps(e["sent"]) for e in rpc))

    def test_where_the_gas_covers_the_run_no_credit_is_made(self) -> None:
        s = Setting(initial_gas_cents=1000)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.PASS, line_of(leg, "R7"))
        self.assertEqual(leg.facts["gas_credits"], [])
        self.assertFalse(any(r["path"].endswith("/gas-account/credits") for r in s.estate.platform.requests))

    def test_without_admin_env_the_entries_are_said_unread_and_the_receipt_speaks_for_them(self) -> None:
        s = Setting(admin_env=False, initial_gas_cents=1000)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R3"], E.PASS, line_of(leg, "R3"))
        self.assertIn("the signing entries were not read before the interview: %s is not filed" % os.path.join(s.store, T.ADMIN_ENV_FILE), " ".join(leg.notes["R3"]))
        self.assertIn("the write's receipt: US$100 per payment and US$1000 per day written onto aer-accounts, Harriet Founder (author)", line_of(leg, "R3"))
        self.assertEqual(s.estate.platform.requests, [])

    def test_a_shortfall_without_admin_env_stops_r7_naming_the_missing_credential(self) -> None:
        s = Setting(admin_env=False)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.FAILED_PREREQUISITE)
        self.assertIn(E.NO_ADMIN_CREDENTIAL, line_of(leg, "R7"))
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 0)

    def test_without_payee_env_r6_stops_and_nothing_is_paid(self) -> None:
        s = Setting(payee_env=False)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R6"], E.FAILED_PREREQUISITE)
        self.assertIn(R.OWNER_PAYEE_NOT_FILED, line_of(leg, "R6"))
        self.assertEqual(outcomes(leg)["R7"], E.FAILED_PREREQUISITE)
        self.assertFalse(any(x.route == "POST /v1/payees" for x in leg.exchanges))


# ======================================================================================================================
# The entries never set by hand (Spec HRW-1 §4, the fixture of 9 October).
# ======================================================================================================================
class TheEntries(unittest.TestCase):
    def test_an_entry_set_by_hand_before_the_interview_is_a_finding(self) -> None:
        estate = W.ScreensEstate()
        estate.platform.entries[estate.aap_account_id][0]["max_amount_per_tx_usd"] = 250
        s = Setting(estate=estate)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R3"], E.FAIL)
        self.assertIn("a signing entry stood above zero before the interview", probes(leg, "R3"))

    def test_an_estate_before_version_15_asks_no_ceiling_and_writes_none(self) -> None:
        s = Setting(catalog_version=14)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R3"], E.FAIL)
        self.assertIn("the interview did not ask C2 and C3", probes(leg, "R3"))
        self.assertIn("the write's receipt names no ceilings", probes(leg, "R3"))
        self.assertIn("an estate entry does not carry the charter's two figures", probes(leg, "R3"))


# ======================================================================================================================
# R8 on its own: the comparison with the API leg, the report fault, the manual.
# ======================================================================================================================
class TheTwoLegs(unittest.TestCase):
    def leg_with(self, mine: Dict[str, str], theirs: Optional[Dict[str, str]], company: str = A.ESTATE["company"]) -> R.RealWorld:
        tmp = tempfile.mkdtemp(prefix="hrw-r8-")
        if theirs is not None:
            write_api_report(tmp, theirs, company=company)
        leg = R.RealWorld(base=D.BASE, store_root=tmp, runs_root=os.path.join(tmp, "runs"), api_reports=tmp, say=lambda s: None, dry_folder=True)
        leg.estate_name = A.ESTATE["company"]
        leg.outcomes = [R.Outcome(st, mine.get(st, E.PASS), "a line") for st in R.STATION_IDS[:8]]
        for st in R.STATION_IDS[:8]:
            leg.next_steps[st].append(("a page", "a sentence"))
        leg.current = "R8"
        return leg

    def test_the_server_can_and_the_screen_cannot_is_a_screen_fault(self) -> None:
        leg = self.leg_with({"R4": E.FAIL}, ALL_PASS)
        outcome = leg.station_r8()
        self.assertEqual(outcome.outcome, E.FAIL)
        finding = next(f for f in leg.findings if f.probe == "a SCREEN fault at R4")
        self.assertIn("the server can; the screen cannot: the API leg passed S4 and the browser leg fail R4", finding.said)
        self.assertEqual(finding.kind, R.SCREEN)

    def test_the_reverse_is_a_report_fault_and_stops_the_run(self) -> None:
        leg = self.leg_with({}, dict(ALL_PASS, S6=E.FAIL))
        with self.assertRaises(R.RunStop) as stop:
            leg.station_r8()
        self.assertIn("a report fault in one of the legs: the browser leg passed R6 and the API leg fail S6", stop.exception.sentence)
        self.assertEqual(stop.exception.kind, R.HARNESS)
        leg.outcomes = [o for o in leg.outcomes if o.station != "R8"]
        outcome = leg.run_station("R8", "The two legs agree")
        self.assertEqual(outcome.outcome, E.FAIL)
        self.assertTrue(leg.stopped)

    def test_no_report_for_this_estate_is_a_prerequisite(self) -> None:
        leg = self.leg_with({}, ALL_PASS, company="Harness Treasury Pty Ltd")
        outcome = leg.run_station("R8", "The two legs agree")
        self.assertEqual(outcome.outcome, E.FAILED_PREREQUISITE)
        self.assertIn(R.NO_API_LEG_REPORT, outcome.line)

    def test_a_station_stopped_on_a_prerequisite_on_either_side_is_not_compared(self) -> None:
        leg = self.leg_with({"R6": E.FAILED_PREREQUISITE}, dict(ALL_PASS, S7=E.FAILED_PREREQUISITE))
        outcome = leg.station_r8()
        self.assertEqual(outcome.outcome, E.PASS, outcome.line)
        self.assertIn("not compared: R6/S6 (FAILED — prerequisite, pass), R7/S7 (pass, FAILED — prerequisite), R7b/S7 (pass, FAILED — prerequisite)", outcome.line)
        self.assertFalse(leg.findings)

    def test_nothing_compared_is_a_prerequisite_not_a_pass(self) -> None:
        leg = self.leg_with({}, ALL_PASS)
        leg.outcomes = [R.Outcome(st, E.SKIPPED, "resumed at R8") for st in R.STATION_IDS[:8]]
        outcome = leg.run_station("R8", "The two legs agree")
        self.assertEqual(outcome.outcome, E.FAILED_PREREQUISITE)
        self.assertIn(R.NOTHING_COMPARED, outcome.line)

    def test_a_station_the_api_leg_did_not_run_is_not_compared(self) -> None:
        leg = self.leg_with({}, {"S1": E.PASS, "S2": E.PASS})
        outcome = leg.station_r8()
        self.assertIn("not compared: R3/S3 (pass, absent)", outcome.line)
        self.assertEqual(outcome.outcome, E.PASS)

    def test_a_passing_station_that_left_no_next_step_is_a_finding(self) -> None:
        leg = self.leg_with({}, ALL_PASS)
        leg.next_steps["R5"] = []
        outcome = leg.station_r8()
        self.assertEqual(outcome.outcome, E.FAIL)
        self.assertIn("R5 left the founder no next step", probes(leg))

    def test_a_walked_step_whose_page_did_not_say_the_manuals_words_is_a_finding(self) -> None:
        leg = self.leg_with({}, ALL_PASS)
        leg.exchanges.append(R.Exchange("R5", "Harriet Founder", "POST", "/v1/workspace/wallets/options", 200, None, "{}", R.now_iso()))
        outcome = leg.station_r8()
        self.assertEqual(outcome.outcome, E.FAIL)
        finding = next(f for f in leg.findings if f.probe == "the manual and the page disagree at R5")
        self.assertEqual(finding.expected, S.WHOSE_WALLET_LEGEND)

    def test_a_walked_step_whose_control_is_named_otherwise_is_a_finding(self) -> None:
        leg = self.leg_with({}, ALL_PASS)
        leg.current = "R6"
        leg.exchanges.append(R.Exchange("R6", "Harriet Founder", "POST", "/v1/payees", 201, None, "{}", R.now_iso()))
        leg.step("press", "Harriet Founder", "pressed 'Add a payee' on /payees")
        leg.current = "R8"
        leg.station_r8()
        finding = next(f for f in leg.findings if f.probe == "the manual and the page disagree at R6")
        self.assertIn("and names 'Add payee'; the founder pressed [\"Add a payee\"]", finding.said)


# ======================================================================================================================
# The review of the code (9 October 2026): each defect it found, held here.
# ======================================================================================================================
class TheReviewOfTheCode(unittest.TestCase):
    def test_a_link_in_a_browser_error_is_never_printed_whole(self) -> None:
        s = Setting()
        token = s.link.split("#", 1)[1]
        real_goto = W.Page.goto

        def goto(page, url, **kw):  # type: ignore[no-untyped-def]
            if "/invite#" in url:
                raise W.FakeError("net::ERR_CONNECTION_RESET at %s" % url)
            return real_goto(page, url, **kw)

        with mock.patch.object(W.Page, "goto", goto):
            leg = s.walk()
        self.assertEqual(outcomes(leg)["R1"], E.FAIL)
        self.assertIn("ERR_CONNECTION_RESET", line_of(leg, "R1"))
        self.assertNotIn(token, line_of(leg, "R1"))
        self.assertNotIn(token, "\n".join(leg.said))
        self.assertNotIn(token, everything_written(leg))

    def test_a_run_that_would_wait_is_not_submitted_where_no_approver_of_payments_is_here(self) -> None:
        s = Setting(estate=WaitingEstate())
        first = s.walk()
        self.assertEqual(outcomes(first)["R7"], E.PASS, "\n".join(first.said))
        os.remove(os.path.join(first.store_dir, "ada.json"))
        s.estate.age_runs(1)
        second = s.walk(start_at="S7")
        self.assertEqual(outcomes(second)["R7"], E.FAILED_PREREQUISITE)
        self.assertIn("this run would wait for 1 approval(s), and no approver the charter names at C11 (Ada Approver) has a session in this run", line_of(second, "R7"))
        self.assertFalse(any(x.route == "POST /v1/sets" for x in second.exchanges))

    def test_two_runs_that_read_alike_in_the_inbox_are_a_finding_and_neither_is_approved_and_r9_cancels_the_waiting_runs(self) -> None:
        s = Setting(estate=DoubledInboxEstate())
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.FAIL)
        self.assertIn("R7: runs that read alike in the Approver inbox", probes(leg, "R7"))
        self.assertTrue(any(c["path"] == "/v1/approvals/inbox" for c in s.estate.calls))  # Ada's inbox was read
        self.assertFalse(any(c["method"] == "POST" and c["path"].startswith("/v1/approvals/") for c in s.estate.calls))  # and nothing in it pressed
        self.assertEqual(s.estate.chain.balance_of(D.OWNER_WALLET_FOR_TESTS), 0)
        runs = [r["id"] for r in leg.facts["runs"]]
        self.assertEqual(outcomes(leg)["R9"], E.PASS, line_of(leg, "R9"))
        self.assertIn("cancelled: %s pending_approval → cancelled (the page's Cancel), %s pending_approval → cancelled (the page's Cancel)" % tuple(runs),
                      line_of(leg, "R9"))

    def test_a_refused_approval_leaves_the_run_waiting_and_r9_cancels_it(self) -> None:
        s = Setting(estate=RefusingApprovalEstate())
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R7"], E.FAIL)
        self.assertIn("Ada Approver's approval was refused", probes(leg, "R7"))
        self.assertTrue(all(s.estate.sets[r["id"]]["status"] == "cancelled" for r in leg.facts["runs"]))

    def test_a_refused_cancellation_fails_r9_in_the_estates_words(self) -> None:
        s = Setting(estate=RefusingCancelEstate())
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R9"], E.FAIL)
        finding = next(f for f in leg.findings if f.probe == "R9: a run this run made was not cancelled")
        self.assertEqual(finding.kind, R.REFUSED)
        self.assertIn("SET_NOT_EDITABLE", finding.said)

    def test_a_stop_while_resuming_is_said_and_classified_never_a_traceback(self) -> None:
        s = Setting()
        first = s.walk()
        path = os.path.join(first.store_dir, R.STATE_FILE)
        state = json.loads(read(path))
        state["estate"]["company"] = "Harness Treasury Pty Ltd"  # the state of another of the harness's estates
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        second = s.walk(start_at="S5", birth=False)
        self.assertIn(R.WRONG_ESTATE, probes(second, "resume"))
        self.assertEqual([outcomes(second)[st] for st in R.STATION_IDS[4:]], [E.NOT_RUN] * 6)
        self.assertTrue(os.path.isfile(second.report_path))

    def test_chromium_that_will_not_launch_is_the_harnesss_own_failure_with_its_install_sentence(self) -> None:
        s = Setting()

        class NoChromium:
            def launch(self, headless: bool = True, **_: Any) -> Any:
                raise W.FakeError("Executable doesn't exist at ~/Library/Caches/ms-playwright/chromium-1228/chrome-mac/Chromium.app")

        class Started:
            chromium = NoChromium()

            def stop(self) -> None:
                pass

        leg = R.RealWorld(base=D.BASE, store_root=s.store, birth=s.birth, runs_root=os.path.join(s.tmp, "runs-x"), api_reports=s.tmp,
                          driver=R.Driver(Started, W.FakeTimeout, W.FakeError), transport=s.estate, say=lambda t: None, time_scale=0.001)
        with self.assertRaises(R.HarnessFault) as fault:
            leg.run()
        self.assertIn("Chromium would not launch through Playwright (Executable doesn't exist", str(fault.exception))
        self.assertIn("-m playwright install chromium. Nothing was opened and nothing was sent", str(fault.exception))
        self.assertEqual(s.estate.calls, [])

    def test_an_entry_superseded_at_zero_is_not_the_estates_own(self) -> None:
        estate = W.ScreensEstate()
        estate.platform.entries[estate.aap_account_id].append({"id": "pe-old", "name": "aer-accounts", "access_type": "sign+audit", "active": True,
                                                               "superseded_by": "pe-new", "max_amount_per_tx_usd": 0, "max_amount_per_day_usd": 0})
        s = Setting(estate=estate)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R3"], E.PASS, line_of(leg, "R3"))
        self.assertIn("the signing entries after the write: aer-accounts 100/1000, Harriet Founder (author) 100/1000 (and 1 not in force)", line_of(leg, "R3"))

    def test_a_page_that_refuses_the_typed_space_itself_sends_nothing_and_the_address_is_typed_again(self) -> None:
        refuses = SC.payee_address_refusal

        def strict(chain: str, address: str) -> Optional[Dict[str, Any]]:
            if address != address.strip():
                return {"code": "ADDRESS_MALFORMED", "message": "That is not an address Arbitrum One can pay, so nothing was saved."}
            return refuses(chain, address)

        with mock.patch.object(SC, "payee_address_refusal", strict):
            s = Setting()
            leg = s.walk()
        self.assertEqual(outcomes(leg)["R6"], E.PASS, line_of(leg, "R6"))
        self.assertIn("the page refused the address typed with a trailing space before anything was sent", line_of(leg, "R6"))
        self.assertEqual(len([x for x in leg.exchanges if x.route == "POST /v1/payees"]), 2)

    def test_a_payee_an_earlier_attempt_left_proposed_is_taken_on_never_added_again(self) -> None:
        estate = W.ScreensEstate()
        estate.hold_payee("Northwind Supplies", T.PAYEE_CHAIN, D.OWNER_WALLET_FOR_TESTS, whitelist_status="proposed")
        s = Setting(estate=estate)
        leg = s.walk()
        self.assertEqual(outcomes(leg)["R6"], E.PASS, line_of(leg, "R6"))
        self.assertIn("Northwind Supplies stands proposed at the owner's wallet (an earlier attempt's), taken on from there and not added again", line_of(leg, "R6"))
        self.assertEqual([x.sent["displayName"] for x in leg.exchanges if x.route == "POST /v1/payees"], ["Contoso Legal"])

    def test_every_stop_is_classified(self) -> None:
        s = Setting(estate=ReplayRefusingEstate())
        leg = s.walk()
        stop = next(f for f in leg.findings if f.probe == "R7b stopped")
        self.assertEqual(stop.kind, R.REFUSED)
        self.assertIn("Submit this run created no run", stop.said)


# ======================================================================================================================
# The command line, the plan, and the harness's own failures.
# ======================================================================================================================
class TheCommandLine(unittest.TestCase):
    def run_main(self, argv: List[str]) -> Tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = R.main(argv)
        return code, out.getvalue()

    def test_without_i_mean_it_nothing_is_opened_and_the_plan_is_printed(self) -> None:
        with mock.patch.object(R, "live_driver", side_effect=AssertionError("no browser without --i-mean-it")):
            code, said = self.run_main([])
        self.assertEqual(code, 2)
        self.assertIn(R.I_MEAN_IT % R.DEFAULT_BASE, said)
        for station, title in R.STATIONS:
            self.assertIn("%s %s — " % (station, title), said)
        self.assertIn("The book on %s: US$1.00 in all, every payment to the owner's wallet (Spec T24)." % T.PAYEE_CHAIN, said)
        self.assertIn("Ada Approver from the seat the charter gives them (its Invite), Ben Signatory from the form", said)

    def test_from_names_the_api_legs_stations_too(self) -> None:
        self.assertEqual([R.normalise_station(x) for x in ("S5", "R5", "s7b", "R7b", "S7")], ["R5", "R5", "R7b", "R7b", "R7"])
        with self.assertRaises(R.HarnessFault) as fault:
            R.normalise_station("S12")
        self.assertIn("no station called S12", str(fault.exception))
        code, said = self.run_main(["--from", "S5"])
        self.assertEqual(code, 2)
        self.assertIn("R4 People — skipped: resumed at R5", said)
        code, said = self.run_main(["--from", "S12", "--i-mean-it"])
        self.assertEqual((code, said.strip()), (2, "no station called S12; the stations are %s (S<n> names the same station as R<n>)" % ", ".join(R.STATION_IDS)))

    def test_playwright_missing_is_the_harnesss_own_failure_with_the_install_sentence(self) -> None:
        real_import = builtins.__import__

        def no_playwright(name, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name.startswith("playwright"):
                raise ImportError("No module named 'playwright'")
            return real_import(name, *args, **kwargs)

        with mock.patch.object(builtins, "__import__", no_playwright):
            with self.assertRaises(R.HarnessFault) as fault:
                R.live_driver()
            self.assertIn("Playwright for Python is not importable", str(fault.exception))
            self.assertIn("-m pip install --user playwright, then", str(fault.exception))
            self.assertIn("-m playwright install chromium. Nothing was opened and nothing was sent", str(fault.exception))
            tmp = tempfile.mkdtemp(prefix="hrw-cli-")
            estate = W.ScreensEstate()
            link = estate.mint_founder_link()
            with open(os.path.join(tmp, "birth.txt"), "w", encoding="utf-8") as handle:
                handle.write(estate.birth_printout(link))
            code, said = self.run_main(["--i-mean-it", "--store", tmp, "--out", tmp, "--birth", os.path.join(tmp, "birth.txt")])
        self.assertEqual(code, 2)
        self.assertIn("The harness could not start — its own failure, not the estate's: Playwright for Python is not importable", said)
        self.assertNotIn(link.split("#", 1)[1], said)

    def test_a_control_not_found_is_named_as_the_harnesss_own_failure_with_its_screenshot(self) -> None:
        with mock.patch.object(S, "CREATE_IT", "Create it now"):
            s = Setting()
            leg = s.walk()
        self.assertEqual(outcomes(leg)["R5"], E.FAIL)
        finding = next(f for f in leg.findings if f.station == "R5")
        self.assertEqual((finding.probe, finding.kind), ("the harness's own failure", R.HARNESS))
        self.assertIn("the harness found no button 'Create it now' on /wallets within 180 s (as Harriet Founder; screenshot R5-", finding.said)
        self.assertIn("the harness could not complete this station — its own failure, not the estate's", line_of(leg, "R5"))


# ======================================================================================================================
# The pure helpers: the vocabulary, the figures, the birth printout.
# ======================================================================================================================
class TheHelpers(unittest.TestCase):
    def test_every_answer_is_classified_in_the_api_legs_vocabulary(self) -> None:
        refusal = {"error": {"code": "X", "message": "no"}}
        self.assertEqual([R.kind_of(st, refusal) for st in (401, 403, 404, 409, 422, 429)], [R.REFUSED] * 6)
        self.assertEqual(R.kind_of(502, refusal), R.REFUSED)
        self.assertEqual(R.kind_of(502, None), R.UNREACHABLE)
        self.assertEqual(R.kind_of(400, refusal), R.MALFORMED_QUESTION)
        self.assertEqual([R.kind_of(st, None) for st in (0, 500, 503)], [R.UNREACHABLE] * 3)
        self.assertEqual(R.kind_of(200, {"failureReason": "x"}), R.ANSWERED_WITH_ERROR)

    def test_a_refusal_is_told_in_the_other_partys_words(self) -> None:
        body = {"error": {"code": "SIGNATURE_NOT_COUNTED", "message": "The access platform did not count your approval.", "detail": {"platformSaid": "not authorized"}}}
        self.assertEqual(R.refusal_words(body), "SIGNATURE_NOT_COUNTED: The access platform did not count your approval. (not authorized)")
        self.assertEqual(R.refusal_words({"ok": True}), "")

    def test_figures_are_typed_as_a_person_types_them(self) -> None:
        self.assertEqual((R.cents_text("10000"), R.cents_text("100000"), R.cents_text("5")), ("100.00", "1,000.00", "0.05"))
        self.assertEqual((R.money_text(500000), R.money_text(10000), R.money_text(490000)), ("0.50", "0.01", "0.49"))
        self.assertEqual(R.fold(" ADA.Approver@aeredium.io"), "ada.approver@aeredium.io")

    def test_the_birth_printout_is_read_for_its_facts(self) -> None:
        estate = W.ScreensEstate()
        link = estate.mint_founder_link()
        facts = R.parse_birth(estate.birth_printout(link))
        self.assertEqual((facts["link"], facts["account_id"], facts["founder_credential"], facts["company"], facts["display_name"], facts["email"], facts["no_email_warning"]),
                         (link, estate.aap_account_id, estate.founder_credential, A.ESTATE["company"], "Harriet Founder", T.REAL_WORLD_BIRTH_EMAIL, None))
        bare = R.parse_birth(estate.birth_printout(link, email=None))
        self.assertEqual((bare["email"], bare["no_email_warning"]), (None, S.NO_EMAIL_LINE))

    def test_a_pattern_matched_control_is_said_by_its_visible_word(self) -> None:
        self.assertEqual((R.shown(S.SEAT_INVITE), R.shown(S.SEAT_WITHDRAW), R.shown(S.ADD_PAYEE)), ("Invite …", "Withdraw it …", "Add payee"))


# ======================================================================================================================
# The tables: the untidy fixtures beside their rulings, the split of the book, the manual's words.
# ======================================================================================================================
class TheTables(unittest.TestCase):
    def test_every_untidy_fixture_names_the_ruling_or_spec_that_made_it_a_rule(self) -> None:
        self.assertEqual(len(T.UNTIDY_FIXTURES), 8)
        for fixture, source in T.UNTIDY_FIXTURES:
            self.assertTrue(fixture and source, fixture)
            self.assertRegex(source, r"Spec|ruling|Manual|owner", fixture)
        words = " ".join(f for f, _ in T.UNTIDY_FIXTURES)
        for habit in ("--email", "capitals", "display name", "twice", "trailing space", "default", "never set by hand"):
            self.assertIn(habit, words)

    def test_the_typed_addresses_carry_capitals_and_surrounding_spaces_and_fold_to_the_book(self) -> None:
        self.assertEqual(T.REAL_WORLD_TYPED_ADDRESSES["harriet"], "Harriet.Founder@aeredium.io ")
        self.assertEqual(T.REAL_WORLD_TYPED_ADDRESSES["ada"], " ADA.Approver@aeredium.io")
        self.assertEqual(R.fold(T.REAL_WORLD_TYPED_ADDRESSES["harriet"]), T.REAL_WORLD_BIRTH_EMAIL)
        ben = A.PEOPLE[T.REAL_WORLD_NAME_NOT_ADDRESS]
        self.assertNotEqual(R.fold(ben.name), R.fold(ben.email).split("@")[0])

    def test_the_two_presses_pay_the_one_dollar_book_between_them_and_nothing_else(self) -> None:
        keys = [p.key for p in A.payments()]
        self.assertEqual(sorted(T.REAL_WORLD_FIRST_PRESS + T.REAL_WORLD_SECOND_PRESS), sorted(keys))
        self.assertFalse(set(T.REAL_WORLD_FIRST_PRESS) & set(T.REAL_WORLD_SECOND_PRESS))
        self.assertEqual(sum(int(p.amount_minor) for p in A.payments()), 1000000)

    def test_the_manual_words_are_held_by_station_each_with_its_source_and_its_step(self) -> None:
        self.assertEqual(sorted(S.MANUAL_WORDS), sorted(st for st in R.STATION_IDS if st not in ("R8", "R9")))
        for station, items in S.MANUAL_WORDS.items():
            for item in items:
                self.assertIn(item["check"], ("pressed", "said", "duplicate", "none"), station)
                self.assertTrue(item["source"].startswith(S.LIBRARY), station)
                if item["check"] == "said":
                    self.assertTrue(item["words"], station)
                if item["check"] == "pressed":
                    self.assertTrue(item["control"], station)
                if item["check"] != "duplicate":
                    self.assertIn(item["walked"][0], ("GET", "POST"), station)

    def test_the_screens_double_restates_the_words_the_harness_pins(self) -> None:
        # the words a founder reads on the seats, as the screens render them and as the harness reads them
        self.assertEqual(S.SEAT_WORDS, SC.SEAT_STATE_WORDS)
        self.assertEqual(S.SEAT_STATE_MEANING_SEATED, SC.SEAT_STATE_MEANING["seated"])
        self.assertEqual(S.ENROLMENT_KEY_EXISTS_SEAT_PENDING, SC.ENROLMENT_KEY_EXISTS_SEAT_PENDING)
        self.assertEqual(S.DEFAULT_LIST_FIELDS, SC.DEFAULT_LIST_FIELDS)


# ======================================================================================================================
# The one-time link is never photographed.
# ======================================================================================================================
class TheLinkOnTheScreen(unittest.TestCase):
    def test_no_screenshot_is_taken_while_a_one_time_link_stands_on_the_page(self) -> None:
        s = Setting()
        leg = s.walk()
        leg.open_browser()
        v = leg.visitor("harriet")
        leg.sign_in(v)
        v.goto(S.PEOPLE_ROUTE)
        form = v.card(S.INVITE_CARD)
        v.fill(S.INVITE_NAME_LABEL, A.PEOPLE["cora"].name, within=form)
        v.fill(S.INVITE_EMAIL_LABEL, A.PEOPLE["cora"].email, within=form)
        v.choose(S.LEVEL_ONE_EXECUTIVE, within=form)  # the estate stands at level 1, so the page names the standing so
        v.tick(S.PEN_LABEL_WORDS, within=form, exact=False)
        v.press(S.INVITE_SUBMIT, within=form, answer=("POST", r"^/v1/invites$"))
        self.assertTrue(v.value_of(S.INVITE_LINK_LABEL))
        before = set(os.listdir(leg.folder.path))
        self.assertIsNone(leg.screenshot(v, "the link"))
        self.assertEqual(set(os.listdir(leg.folder.path)), before)
        v.press(S.HIDE_THE_LINK)
        self.assertIsNotNone(leg.screenshot(v, "after"))
        leg.close_browser()


# ======================================================================================================================
# The documents: the CHANGELOG's line, word for word (Spec HRW-1 §8), and the README's section.
# ======================================================================================================================
SECTION_8 = ("Harness Real World (Spec HRW-1, revised 9 October): the browser leg of the estate harness — a real browser, the real pages, a passkey behind "
             "the real prompt, the presses a founder makes and the sentences a founder reads, the chain read afterwards, with untidy fixtures shaped like "
             "real clients (entries never set by hand among them), the duplicate screen confirmed as a founder confirms it, and a station that compares it "
             "with the API leg. Named by the owner on 7 October 2026 after a founder could not send a payment the API harness had been sending for days.")


class TheDocuments(unittest.TestCase):
    def test_the_changelog_carries_section_8s_line_word_for_word_above_t28(self) -> None:
        text = read(os.path.join(ROOT, "CHANGELOG.md"))
        self.assertIn("## Spec HRW-1 — Harness Real World: the browser leg of the estate harness (7 October 2026, revised 9 October 2026)\n\n%s\n" % SECTION_8, text)
        self.assertEqual(text.index("## "), text.index("## Spec HRW-1"), "the newest entry first")
        self.assertLess(text.index("## Spec HRW-1"), text.index("## Spec T28"))
        entry = text.split("## Spec HRW-1", 1)[1].split("## Spec T28", 1)[0]
        for words in ("`aer360_real_world.py` (new)", "`aer360_screens.py` (new)", "`aer360_tables.py`", "`tests/test_harness_real_world.py`",
                      "`tests/real_world_double.py`", "`tests/real_world_screens.py`", "**Auditor**", "**Attacker**", "**Optimiser**", "**Implementer**",
                      "**Customer Support**", "**Where the spec and the code part company**", "Not touched"):
            self.assertIn(words, entry, words)

    def test_the_readme_says_what_the_leg_needs_how_it_runs_and_what_it_will_not_do(self) -> None:
        text = read(os.path.join(ROOT, "README.md"))
        section = text.split("## Harness Real World, the browser leg of the estate harness", 1)[1].split("## Pathfinder", 1)[0]
        for words in ("python3 -m pip install --user playwright", "python3 -m playwright install chromium", "--i-mean-it", "--from S7", "--headed",
                      "~/.aer360-harness/", "real-world/", "0600", "**R1 Enrol**", "**R9 Teardown.**", "UNTIDY_FIXTURES", "**Safety.**",
                      "`Harness Holdings Pty Ltd` and `Harness Treasury`", "**Where the spec and the code part company**", "tests/real_world_screens.py"):
            self.assertIn(words, section, words)


if __name__ == "__main__":
    unittest.main()
