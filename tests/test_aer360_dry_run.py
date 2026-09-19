"""--dry prints the twelve stations' calls in order with no network, the probes of S10 to S12 included (Spec T7)."""
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
        self.assertEqual(len([l for l in s4 if "POST /v1/invites {" in l]), 3)
        for key in A.AUTHORS_INVITED:
            self.assertTrue(any(A.PEOPLE[key].email in l for l in s4), key)
        self.assertTrue(any("GET /v1/approver-seats" in l for l in s4))
        s5 = [l for l in lines if l.startswith("S5 — POST /v1/onboarding/interviews/<account interview>/answers")]
        self.assertEqual(len(s5), len(A.expected_walk("wallet_account")))
        self.assertTrue(any('"questionId": "O2"' in l and A.MONEY["per_payment_cents"] in l for l in s5))
        self.assertTrue(any("GET /v1/aer360/wallets" in l for l in lines if l.startswith("S5")))
        s6 = [l for l in lines if l.startswith("S6 — ")]
        self.assertEqual(len([l for l in s6 if "POST /v1/payees {" in l]), 2)
        self.assertTrue(any(T.address("NORTHWIND_ETHEREUM") in l for l in s6))
        self.assertTrue(any(T.address("CONTOSO_ETHEREUM") in l for l in s6))
        self.assertEqual(len([l for l in s6 if "/promote" in l]), 2)
        self.assertEqual(len([l for l in s6 if "/approve" in l]), 2)
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
