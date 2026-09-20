"""
--dry prints the twelve stations' calls in order with no network, the probes of S10 to S12 included (Spec T7).
Spec T8 changed what the harness expects, not what it sends: the calls are frozen in tests/fixtures/aer360-dry-calls.txt
from the dry run at main after PR #5, and the venue probe's expectation is the law's. Spec T9 added S6's second press;
Spec T10 added, under S4, the seats as the run finds them, the conditional re-invitation for each author, and the seat
re-grant's condition (121 → 134 lines).
"""
import contextlib
import io
import os
import sys
import unittest
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_tables as T  # noqa: E402


def no_network(*args, **kwargs):
    raise AssertionError("the dry run reached for the network: %r" % (args[:1],))


FROZEN_CALLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "aer360-dry-calls.txt")


def calls_of(lines):
    """Each dry line without its expectation: the station and the call, which is what --dry must keep unchanged."""
    out = []
    for line in lines:
        station, _, rest = line.partition(" — ")
        out.append("%s — %s" % (station, rest.split(" → ", 1)[0] if " → " in rest else rest))
    return out


class DryRunTest(unittest.TestCase):
    def setUp(self):
        self._urlopen = urllib.request.urlopen
        urllib.request.urlopen = no_network

    def tearDown(self):
        urllib.request.urlopen = self._urlopen

    def stations_in(self, lines):
        seen = []
        for line in lines:
            station = line.split(" — ", 1)[0]
            if station not in seen:
                seen.append(station)
        return seen

    def test_the_twelve_stations_in_order(self):
        lines = H.dry_lines()
        self.assertEqual(self.stations_in(lines), H.STATION_IDS)
        for line in lines:
            self.assertIn(" — ", line)

    def test_s1_enrols_by_invitation_and_s3_answers_every_question_the_book_expects(self):
        lines = H.dry_lines()
        s1 = [l for l in lines if l.startswith("S1 — ")]
        self.assertTrue(any("POST /v1/auth/invite/options" in l for l in s1))
        self.assertTrue(any("POST /v1/auth/invite/verify" in l for l in s1))
        self.assertTrue(any("attestation none" in l and "flags UP|UV|AT" in l for l in s1))
        s3 = [l for l in lines if l.startswith("S3 — POST /v1/onboarding/interviews/<policy interview>/answers")]
        self.assertEqual(len(s3), len(A.expected_walk("policy")))
        self.assertIn('"questionId": "A1"', s3[0])
        self.assertIn('"questionId": "G1"', s3[-1])
        self.assertFalse(any('"questionId": "B4"' in l for l in s3), "B4 is not served while A9 is No")
        self.assertFalse(any('"questionId": "C16"' in l for l in s3), "version 12 never serves C16")
        s3_all = [l for l in lines if l.startswith("S3 — ")]
        order = [l.split(" — ", 1)[1].split(" ", 1)[1].split(" ")[0] for l in s3_all if "→" in l]
        self.assertEqual(order[0], "/v1/onboarding/interviews")
        self.assertTrue(any("/readback" in l for l in s3_all))
        self.assertTrue(any("/confirm/options" in l for l in s3_all))
        self.assertTrue(any("/confirm " in l for l in s3_all))
        self.assertTrue(any("/compile" in l for l in s3_all))
        self.assertTrue(any("GET /v1/onboarding/charter" in l for l in s3_all))

    def test_s4_to_s8_walk_the_people_the_account_the_payees_and_the_payments(self):
        lines = H.dry_lines()
        s4 = [l for l in lines if l.startswith("S4 — ")]
        self.assertEqual(len([l for l in s4 if "POST /v1/invites {" in l]), 6, "a first invitation for each author, and the conditional re-invitation (Spec T10)")
        for key in A.AUTHORS_INVITED:
            self.assertTrue(any(A.PEOPLE[key].email in l for l in s4), key)
        self.assertEqual(len([l for l in s4 if "GET /v1/approver-seats" in l]), 2, "the seats as the run finds them, and after the people were brought in")
        s5 = [l for l in lines if l.startswith("S5 — POST /v1/onboarding/interviews/<account interview>/answers")]
        self.assertEqual(len(s5), len(A.expected_walk("wallet_account")))
        self.assertTrue(any('"questionId": "O2"' in l and A.MONEY["per_payment_cents"] in l for l in s5))
        self.assertTrue(any("GET /v1/aer360/wallets" in l for l in lines if l.startswith("S5")))
        s6 = [l for l in lines if l.startswith("S6 — ")]
        self.assertEqual(len([l for l in s6 if "POST /v1/payees {" in l]), 2)
        self.assertTrue(any(T.address("NORTHWIND_ETHEREUM") in l for l in s6))
        self.assertTrue(any(T.address("CONTOSO_ETHEREUM") in l for l in s6))
        self.assertEqual(len([l for l in s6 if "/promote" in l]), 2)
        self.assertEqual(len([l for l in s6 if "/approve" in l]), 4, "two presses per payee: Ada, then the next roster member (Spec T9)")
        s7 = [l for l in lines if l.startswith("S7 — ")]
        self.assertEqual(len([l for l in s7 if "POST /v1/sets/review" in l]), 3)
        self.assertEqual(len([l for l in s7 if "POST /v1/sets {" in l]), 3)
        self.assertTrue(any(T.address("UNLISTED_ETHEREUM") in l and '"declared": true' in l for l in s7))
        for payment in A.PAYMENTS:
            self.assertTrue(any(payment.amount_minor in l for l in s7), payment.key)
        self.assertTrue(any("POST /v1/approvals/<run P1>/approve" in l for l in s7))
        s8 = [l for l in lines if l.startswith("S8 — ")]
        self.assertTrue(any("GET /v1/workspace/readiness" in l for l in s8))

    def test_the_three_hats_are_printed_with_their_probes(self):
        lines = H.dry_lines()
        s10 = [l for l in lines if l.startswith("S10 — ")]
        self.assertTrue(any("read-back" in l and "word for word" in l for l in s10))
        self.assertTrue(any("minor-unit law" in l for l in s10))
        self.assertTrue(any("Rule 13" in l for l in s10))
        s11 = [l for l in lines if l.startswith("S11 — ")]
        for probe in ("without x-csrf-token", "Ben with the founder's passkey", "a viewer", '"role": "principal"', "not asked given the answers so far",
                      "the compiler reads only confirmed interviews", "an amount is a whole number of cents", "challenge already used", "rpIdHash",
                      "Checksum probe", "Venue probe", "above the per-payment limit", "who entered it", "confirm happens at the read-back", "DELETE"):
            self.assertTrue(any(probe in l for l in s11), probe)
        self.assertTrue(any(T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM")) in l for l in s11))
        self.assertFalse(any("0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45" in l for l in lines), "the venue address is read at run time, never printed from a table of ours")
        s12 = [l for l in lines if l.startswith("S12 — ")]
        self.assertTrue(any("two seconds" in l or "2 seconds" in l for l in s12))
        self.assertTrue(any("ten slowest" in l for l in s12))
        self.assertTrue(any("5xx" in l for l in s12))

    def test_the_calls_are_unchanged_since_spec_t7(self):
        """Spec T8: --dry unchanged in its calls. The fixture is the dry run at main after PR #5, its expectations cut off at the arrow."""
        with open(FROZEN_CALLS, "r", encoding="utf-8") as handle:
            frozen = handle.read().splitlines()
        self.assertEqual(len(frozen), 134, "Spec T9 added a second approve press per payee to S6; Spec T10 added thirteen lines under S4 and reworded the seat re-grant's condition, and nothing else")
        self.assertEqual(calls_of(H.dry_lines()), frozen)

    def test_s4_carries_the_conditional_re_invitation_for_each_author_and_the_seat_re_grant(self):
        """Spec T10 §5: for each author the comparison and the conditional fresh invitation, options and verify with a NEW passkey stored beside the old; for Ada the seat re-grant."""
        s4 = [l for l in H.dry_lines() if l.startswith("S4 — ")]
        self.assertEqual(len(s4), 25)
        self.assertIn("GET /v1/approver-seats (as Harriet Founder) → expect the charter's seats as this run finds them: which credential Ada Approver's seat names before anybody is brought in again", s4[0])
        for key in A.AUTHORS_INVITED:
            person = A.PEOPLE[key]
            mine = [l for l in s4 if person.name in l]
            compare = [l for l in mine if l.startswith("S4 — [compare] %s's session credentialId with the founder's" % person.name)]
            self.assertEqual(len(compare), 1, key)
            self.assertIn("→ expect a credential of %s's own, not the founder's; equal is the shared credential of S10's finding, and %s is brought in again" % (person.name, person.name), compare[0])
            again = [l for l in mine if "— only if %s's session carries the founder's credential" % person.name in l]
            self.assertEqual(len(again), 1, key)
            self.assertTrue(again[0].startswith("S4 — POST /v1/invites {\"displayName\": \"%s\", \"email\": \"%s\", \"role\": \"author\"} (as Harriet Founder, x-csrf-token) — only if" % (person.name, person.email)), again[0])
            self.assertIn("→ expect 201: a fresh invitation for the same name and email, minting a credential of %s's own (Spec 91)" % person.name, again[0])
            conditional = [l for l in mine if "— only if %s is brought in again" % person.name in l]
            self.assertEqual([l.split(" ", 4)[3] for l in conditional], ["/v1/auth/invite/options", "/v1/auth/invite/verify"], key)
            self.assertIn("<RegistrationResponseJSON with a NEW passkey>", conditional[1])
            self.assertIn("the new key stored beside the old at ~/.aer360-harness/harness-holdings/%s-2-<date>.json mode 0600, the old one untouched" % key, conditional[1])
            self.assertIn("→ expect 200: a session for %s on a credential of %s's own, not the founder's" % (person.name, person.name), conditional[1])
        grant = [l for l in s4 if "POST /v1/approver-seats/grant" in l]
        self.assertEqual(len(grant), 1)
        self.assertIn("— only if the seat is enrolled_not_seated or names a credential other than Ada Approver's session's → expect the seat seated, naming Ada Approver's own credential (Spec 91); a refusal is a finding in the estate's words", grant[0])
        self.assertIn("GET /v1/invites (as Harriet Founder) → expect the register: three authors, redeemed; each row's sharesCredentialWith (Spec 91's marker) read for S10, expected absent after the re-invitation", s4[-1])
        # the other stations are as Spec T9 left them
        self.assertEqual(len([l for l in H.dry_lines() if l.startswith("S6 — ") and "/approve" in l]), 4)

    def test_the_venue_probes_expectation_is_the_law(self):
        s11 = [l for l in H.dry_lines() if l.startswith("S11 — ") and "Venue probe" in l]
        self.assertEqual(len(s11), 1)
        self.assertIn("→ expect 201, accepted, as the law says (%s); a refusal is the finding" % H.VENUE_RULING, s11[0])
        self.assertNotIn("expect a refusal", s11[0])
        checksum = [l for l in H.dry_lines() if l.startswith("S11 — ") and "Checksum probe" in l]
        self.assertIn("→ expect a refusal, or the estate's acceptance recorded", checksum[0], "the checksum probe still expects a refusal")

    def test_the_second_press_is_carried_with_its_expectation(self):
        """Spec T9 §5: S6's second press names the next roster member (expected Ben Signatory) and expects whitelisted; the first press expects the quorum's pending answer."""
        s6 = [l for l in H.dry_lines() if l.startswith("S6 — ")]
        approves = [l for l in s6 if "/approve" in l]
        self.assertEqual(len(approves), 4)
        first = [l for l in approves if "(as Ada Approver)" in l]
        self.assertEqual(len(first), 2)
        for l in first:
            self.assertIn("expect whitelistStatus pending_promotion with one more needed", l)
            self.assertIn("approvals {required 2, collected 1, remaining 1}", l)
            self.assertIn("may_still_approve", l)
            self.assertIn("sentence (Spec 89)", l)
        second = [l for l in approves if "the next roster member the first answer names, expected Ben Signatory" in l]
        self.assertEqual(len(second), 2, "one second press per payee, expected Ben Signatory")
        for l in second:
            self.assertIn("→ expect whitelistStatus whitelisted", l)
        self.assertEqual(len([l for l in s6 if "/promote" in l and "pending_promotion" in l]), 2)
        self.assertTrue(any("read by this run's payee ids" in l for l in s6))

    def test_no_line_carries_a_secret_or_a_venue_address_of_our_own(self):
        lines = H.dry_lines()
        for line in lines:
            self.assertNotIn("BEGIN EC PRIVATE KEY", line)
        self.assertTrue(all("<token" in l for l in lines if "/invite/options" in l))

    def test_main_dry_prints_and_sends_nothing(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = H.main(["--dry"])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("Dry run: nothing was sent.", text)
        self.assertIn("S12 — [measure]", text)
        self.assertNotIn("Report:", text)

    def test_from_resumes_at_a_station_with_a_sign_in_for_the_stored_passkeys(self):
        lines = H.dry_lines(start_at="S5")
        self.assertTrue(lines[0].startswith("resume — POST /v1/auth/login/options"))
        self.assertEqual(self.stations_in(lines[1:]), ["S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12"])
        with self.assertRaises(H.HarnessError):
            H.dry_lines(start_at="S13")

    def test_fresh_without_an_invite_refuses(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = H.main(["--fresh", "--store", os.path.join(os.path.dirname(__file__), "no-such-store")])
        self.assertEqual(code, 2)
        self.assertIn("--fresh refuses to run without a new --invite", out.getvalue())


if __name__ == "__main__":
    unittest.main()
