"""
--dry prints the twelve stations' calls in order with no network, the probes of S10 to S12 included (Spec T7).
Spec T8 changed what the harness expects, not what it sends: the calls are frozen in tests/fixtures/aer360-dry-calls.txt
from the dry run at main after PR #5, and the venue probe's expectation is the law's. Spec T9 added S6's second press;
Spec T10 added, under S4, the seats as the run finds them, the conditional re-invitation for each author, and the seat
re-grant's condition (121 → 134 lines). Spec T11 added the six answers the book now gives that a version-14 estate serves
(C11A and C19 under S3; WO1 to WO4 under S5) and one S10 comparison line for Spec 92's charter fields (134 → 141 lines); the
venue probe's expectation follows the book's C19, and S7's submit lines say what the tiers would do. Spec T13 ended S5 with the
funding wallet and the faucet — the workspace read, the options road, the press, the read-back, the one balance read and the one
faucet call — and added S7's asset-line report (143 → 150 lines). Spec T15 added, under S4, the roster changes read, the signature's two
roads for each person the list names, the seat granted again for a change listed expired, and the read-back after the count, and under
S10 the trail's roster.seat_rebound row (150 → 156 lines). Spec T17 added S4's grant step (156 → 159). Spec T14 rewrote S7: the admin credential's
file, the Treasury's sign-in or birth, its charter and funding wallet, the four money reads before, the Treasury's gas credit and its payment of the
shortfall, S7a's review of the set of three, Holdings' gas credit, each payment's balance reads on the chain, its review, creation, submission,
approvals in the spec's order, execution and register reads, the trail, and the four money reads after; and under S10 the money moved (159 → 193 lines).
Spec T18 moved the chain word: every S6, S7 and S11 call that names a chain names `arbitrum`, C9 is answered `Arbitrum One`, the venue body names the
corridor's UNISWAP_V3_ARBITRUM row, and S7 gains one conditional call — the payees register read where S6 left no record (193 → 194 lines).
"""
import contextlib
import io
import os
import sys
import unittest
import unittest.mock
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
        self.assertFalse(any('"questionId": "C16"' in l for l in s3), "version 12 retired C16, and version 14 never serves it")
        # Spec T11: the two of the seven a version-14 policy interview serves this book, in the catalog's order; C11C stays behind the CFO's answer
        self.assertTrue(any('"questionId": "C11A", "value": {"choice": "The people who may change these rules, at the number you set for a change"}' in l for l in s3))
        self.assertTrue(any('"questionId": "C19", "value": {"choice": "No — only wallets held by people or companies"}' in l for l in s3))
        self.assertFalse(any('"questionId": "C11C"' in l for l in s3), "C11C is asked only behind C11A's third answer")
        ids = [l.split('"questionId": "', 1)[1].split('"', 1)[0] for l in s3]
        self.assertEqual(ids[ids.index("C11") + 1], "C11A")
        self.assertEqual(ids[ids.index("C15") + 1], "C19")
        self.assertIn("the answer book answers catalog version 14", [l for l in lines if l.startswith("S3 — POST /v1/onboarding/interviews {")][0])
        self.assertIn(H.ESTATE_STATES_NO_CATALOG_VERSION, [l for l in lines if l.startswith("S3 — POST /v1/onboarding/interviews {")][0])
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
        self.assertEqual(len([l for l in s4 if "GET /v1/approver-seats" in l]), 4, "as the run finds them, after the people were brought in, the grant step's read with onRoster, and the read-back after the count (Spec T17)")
        s5 = [l for l in lines if l.startswith("S5 — POST /v1/onboarding/interviews/<account interview>/answers")]
        self.assertEqual(len(s5), len(A.expected_walk("wallet_account")))
        self.assertTrue(any('"questionId": "O2"' in l and A.MONEY["per_payment_cents"] in l for l in s5))
        # Spec T11: the wallet's people and tiers, after WA2 and before WCW, as the book sends them
        self.assertTrue(any('"questionId": "WO1", "value": {"choice": "One person, named here", "person": {"name": "Ben Signatory", "email": "harness+ben@aeredium.io"}}' in l for l in s5))
        self.assertTrue(any('"questionId": "WO2", "value": {"entries": [{"name": "Harriet", "surname": "Founder", "email": "harness+harriet@aeredium.io", "title": "CEO"}]}' in l for l in s5))
        self.assertTrue(any('"questionId": "WO3", "value": {"cents": "200"}' in l for l in s5), "Spec T14: US$2.00")
        self.assertTrue(any('"questionId": "WO4", "value": {"cents": "1000"}' in l for l in s5), "Spec T14: US$10.00")
        self.assertTrue(any('"questionId": "WA1", "value": {"entries": [{"name": "Ada Approver", "email": "harness+ada@aeredium.io"}, {"name": "Ben Signatory", "email": "harness+ben@aeredium.io"}]}' in l for l in s5))
        account_ids = [l.split('"questionId": "', 1)[1].split('"', 1)[0] for l in s5]
        self.assertEqual(account_ids[account_ids.index("WA2") + 1:account_ids.index("WCW")], ["WO1", "WO2", "WO3", "WO4"])
        self.assertTrue(any("GET /v1/aer360/wallets" in l for l in lines if l.startswith("S5")))
        s6 = [l for l in lines if l.startswith("S6 — ")]
        self.assertEqual(len([l for l in s6 if "POST /v1/payees {" in l]), 2)
        self.assertTrue(any(T.address("NORTHWIND_ETHEREUM") in l for l in s6))
        self.assertTrue(any(T.address("CONTOSO_ETHEREUM") in l for l in s6))
        self.assertEqual(len([l for l in s6 if "/promote" in l]), 2)
        self.assertEqual(len([l for l in s6 if "/approve" in l]), 6, "three roster pressers per payee: Ada, Ben, Cora (Spec T12)")
        s7 = [l for l in lines if l.startswith("S7 — ")]
        # Spec T14: the Treasury's review and creation, S7a's review of the set of three, and the three payments' reviews and creations
        self.assertEqual(len([l for l in s7 if "POST /v1/sets/review" in l]), 5)
        self.assertEqual(len([l for l in s7 if "POST /v1/sets {" in l]), 4)
        self.assertTrue(any(T.address("UNLISTED_ETHEREUM") in l and '"declared": true' in l for l in s7))
        for payment in A.PAYMENTS:
            self.assertTrue(any(payment.amount_minor in l for l in s7), payment.key)
        self.assertTrue(any("POST /v1/approvals/<run P1>/challenge {} then /approve" in l for l in s7))
        self.assertTrue(any("POST /v1/approvals/<run HT>/challenge {} then /approve" in l and "the Treasury founder" not in l and "Harriet Founder at Harness Treasury" in l for l in s7))
        # Spec T14 §4: the submit lines say what the spec asks and what the tiers would do, in cents
        submits = [l for l in s7 if "/submit {}" in l]
        self.assertEqual(len(submits), 4, "the Treasury's payment and the three")
        self.assertIn("1.25 (USDC): expected to proceeds to approval; the spec: lands with one signature, the holder's (Ben Signatory); under the tiers: within the holder's own figure (US$2.00), one signature — the holder's", submits[1])
        self.assertIn("4.99 (USDC): expected to waits; the spec: waits for two and lands when Ben Signatory and Cora Clerk sign; under the tiers: two signatures (above US$2.00, up to US$10.00)", submits[2])
        self.assertIn("12.00 (USDC): expected to held; the spec: waits for three and lands when the third signs; under the tiers: three signatures (above US$10.00)", submits[3])
        self.assertEqual(len([l for l in s7 if "/execute {}" in l]), 4, "every approved run is executed by its author")
        self.assertEqual(len([l for l in s7 if "gas-account/credits" in l]), 3, "the Treasury's credit, Holdings' credit, and the Treasury's where it was not credited before")
        self.assertEqual(len([l for l in s7 if T.public_rpc_url(T.PAYEE_CHAIN) in l]), 6, "each payee's balance before and after, on the chain")
        self.assertEqual(len([l for l in s7 if T.GAS_ACCOUNT_ROUTE in l]), 3, "both gas accounts before, and the money-after line")
        self.assertTrue(any(T.NO_GAS_CREDIT_ROAD_SENTENCE in l for l in s7))
        self.assertTrue(any(T.FUND_TREASURY_SENTENCE % ("<address>", T.PAYEE_CHAIN) in l for l in s7))
        self.assertTrue(any("Your gas account holds US$<available>. This set needs at most US$<ceiling> of gas. Nothing was sent. Buy gas below." in l for l in s7))
        s8 = [l for l in lines if l.startswith("S8 — ")]
        self.assertTrue(any("GET /v1/workspace/readiness" in l for l in s8))

    def test_the_three_hats_are_printed_with_their_probes(self):
        lines = H.dry_lines()
        s10 = [l for l in lines if l.startswith("S10 — ")]
        self.assertTrue(any("read-back" in l and "word for word" in l for l in s10))
        self.assertTrue(any("minor-unit law" in l for l in s10))
        self.assertTrue(any("Rule 13" in l for l in s10))
        spec92 = [l for l in s10 if "Spec 92 fields" in l]
        self.assertEqual(len(spec92), 1)
        for words in ("payeeApproval (C11A — the change approvers, the census of 4 at a quorum of 2)", "payeeVenueContracts (C19 — refused)",
                      "holder (WO1 — Ben Signatory, by_person, Officer)", "signingTiers.holderAloneUpToCents (WO3 — 200) and twoSignaturesUpToCents (WO4 — 1000)",
                      "WO2's third party among the signers", "never as the written US$1.00", "C19's door line"):
            self.assertIn(words, spec92[0], words)
        money = [l for l in s10 if "the money moved (Spec T14 §5)" in l]
        self.assertEqual(len(money), 1)
        self.assertIn("the sum of the three payments (US$18.24)", money[0])
        self.assertIn("a finding where any pair does not reconcile to the cent", money[0])
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
        self.assertEqual(len(frozen), 194, "Spec T14 rewrote S7 (159 → 193); Spec T18 adds S7's conditional register read for a run resumed at S7 (193 → 194)")
        self.assertEqual(calls_of(H.dry_lines()), frozen)
        self.assertEqual(len([l for l in frozen if l.startswith("S4 — ") and "/v1/roster/changes" in l]), 4, "the list, the options, the press, the read-back after the count")
        self.assertEqual(len([l for l in frozen if l.startswith("S4 — ") and "/v1/approver-seats/grant" in l]), 3, "Spec T10's grant, Spec T17's grant of a stale seat, and Spec T15's seat granted again for an expired change")
        self.assertEqual(len([l for l in frozen if l.startswith("S10 — ") and "/v1/export/audit" in l]), 1, "the trail is read once")
        self.assertEqual(len([l for l in frozen if l.startswith("S5 — ") and "/v1/workspace/funding-wallet" in l]), 2, "the options road and the press")
        self.assertEqual(len([l for l in frozen if "https://aeredium.io/faucet-api/request" in l]), 1, "the faucet is asked once")
        self.assertEqual(len([l for l in frozen if "https://testnet.rpc.aeredium.io" in l]), 1, "the balance is read once")
        added = [l for l in frozen if any('"questionId": "%s"' % qid in l for qid in ("C11A", "C19", "WO1", "WO2", "WO3", "WO4"))]
        self.assertEqual(len(added), 6)
        self.assertEqual(len([l for l in frozen if l.startswith("S10 — ") and "Spec 92 fields" in l]), 1)
        self.assertEqual(len([l for l in frozen if l.startswith("S6 — ") and "/approve" in l]), 6, "three roster pressers per payee")
        # Spec T14: S7's new calls, cut at the arrow
        self.assertEqual(len([l for l in frozen if l.startswith("S7 — ") and "gas-account/credits" in l]), 3)
        self.assertEqual(len([l for l in frozen if l.startswith("S7 — ") and "/execute {}" in l]), 4)
        self.assertEqual(len([l for l in frozen if l.startswith("S7 — ") and "/v1/export/audit" in l]), 2, "the Treasury's trail and Holdings'")
        self.assertEqual(len([l for l in frozen if l.startswith("S7 — ") and T.public_rpc_url(T.PAYEE_CHAIN) in l]), 6)
        self.assertEqual(len([l for l in frozen if l.startswith("S10 — ") and "the money moved" in l]), 1)

    def test_s4_carries_the_conditional_re_invitation_for_each_author_and_the_seat_re_grant(self):
        """Spec T10 §5: for each author the comparison and the conditional fresh invitation, options and verify with a NEW passkey stored beside the old; for Ada the seat re-grant."""
        s4 = [l for l in H.dry_lines() if l.startswith("S4 — ")]
        self.assertEqual(len(s4), 33, "Spec T10's 25, Spec T15's five, and Spec T17's three (the grant-step read, the grant, the read-back after the count)")
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
        self.assertEqual(len(grant), 3, "Spec T10's grant, Spec T17's grant of a stale seat, and Spec T15's seat granted again for a change listed expired")
        self.assertIn("— only if the seat is enrolled_not_seated or names a credential other than Ada Approver's session's → expect the seat seated, naming Ada Approver's own credential (Spec 91); a refusal is a finding in the estate's words", grant[0])
        self.assertIn("GET /v1/invites (as Harriet Founder) → expect the register: three authors, redeemed; each row's sharesCredentialWith (Spec 91's marker) read for S10, expected absent after the re-invitation", s4[-1])

    def test_s4_grants_the_stale_seat_then_signs_the_roster_change_as_the_list_names_and_s10_reads_the_trail(self):
        """Spec T17 §1 and §2: after the seat re-grant, S4 reads the changes and the seats with onRoster, grants a stale seat, signs it as the able persons, re-reads the seat, and S10 reads the trail."""
        lines = H.dry_lines()
        s4 = [l for l in lines if l.startswith("S4 — ")]
        grant = next(i for i, l in enumerate(s4) if "POST /v1/approver-seats/grant" in l)  # Spec T10's grant of Ada's own credential
        tail = s4[grant + 1:]
        self.assertEqual(len(tail), 9, "the list, the grant-step read, the grant of a stale seat, the options, the press, the grant for an expired change, the read-back, the seat read again, then the register")
        self.assertTrue(tail[0].startswith("S4 — GET /v1/roster/changes (as Harriet Founder) → expect every roster change the platform holds for the estate (Spec 99): pendingTxId, state awaiting, approved, applied, expired or closed, whose seat it moves, requiredSignatures, signaturesCollected, signedBy, maySign; a fresh estate lists none, and S4 says so in one line"), tail[0])
        self.assertIn("GET /v1/approver-seats (as Harriet Founder) — the grant step's read, with onRoster (AER 360 Spec 105) → expect each seat's onRoster true, false or null; for a seat of a harness person (matched by email harness+<name>@aeredium.io) reading false with no awaiting change the founder grants it again (below); a seat reading true prints nothing; a null credential or ambiguous seat, a seat of a person not of the harness, and a null seat print their line and are not granted; an estate without onRoster prints \"the seat view has no onRoster; skipping\" and S4 behaves as T15", tail[1])
        self.assertIn('POST /v1/approver-seats/grant {"email": "harness+ada@aeredium.io"} (as Harriet Founder) — only for a seat of a harness person reading onRoster false with no awaiting change → expect Spec 95 to propose the move afresh at the seat grant, one call, listed awaiting and signed below; where the grant\'s answer carries no pendingTxId the line says "moved at once" and the signing is skipped', tail[2])
        self.assertIn("POST /v1/roster/changes/<pendingTxId>/sign/options {} (as each person the change's list names as able — not the stale seat's owner, and where they have a seat row reading onRoster true; a person the list names with no seat row is able on the list's word) — only for a change listed awaiting whose target credential is that person's stored passkey → expect 200: options with the challenge the estate derives from roster-change:<workspace id>:<pendingTxId>:<issuedAtMs> under the purpose roster.change, and issuedAtMs; where the able persons are fewer than requiredSignatures S4 fails \"<n> required, <m> able\" and grants no further seat", tail[3])
        self.assertIn('POST /v1/roster/changes/<pendingTxId>/sign {"issuedAtMs": "<issuedAtMs>", "response": "<assertion by the signer\'s passkey over the challenge>"} → expect 200: signaturesCollected of requiredSignatures, state awaiting until the count is met, then applied with rebound naming Ada Approver\'s current credential; a change moving a harness seat to a credential the harness does not hold is the finding "change <id> moves <who>\'s seat to a credential the harness does not hold; not signed"; a refusal (CHANGE_SIGNER_NOT_ON_ROSTER, APPROVER_ALREADY_SIGNED, SIGNATURE_NOT_COUNTED, PLATFORM_REFUSED) is judged for Rule 13 and reported in the estate\'s words, never retried', tail[4])
        self.assertIn('POST /v1/approver-seats/grant {"email": "harness+ada@aeredium.io"} (as Harriet Founder) — only for a change listed expired, or one this estate did not propose → expect Spec 95 to propose the move afresh at the seat grant (the estate proposes a move at a seat grant or a redemption, not at a sign-in), the change re-listed awaiting and signed; a second expiry fails S4 naming the ceremony', tail[5])
        self.assertIn("GET /v1/roster/changes (as Harriet Founder) — after the count is met → expect the change applied, its seat naming Ada Approver's current credential in short form, as the signature's rebound named it", tail[6])
        self.assertIn("GET /v1/approver-seats (as Harriet Founder) — after the count is met, up to three times over a bounded wait → expect Ada Approver's seat reading onRoster true (moved); otherwise S4 fails naming the seat and \"<k> of <n> signatures\"", tail[7])
        self.assertTrue(tail[8].startswith("S4 — GET /v1/invites"))
        s6 = [l for l in lines if l.startswith("S6 — ") and "/approve" in l]
        for l in s6:
            self.assertIn("with every seat on its holder's current credential, Ada Approver counted (1 of 2) and Ben Signatory counted (2 of 2), the count met, so Cora Clerk is not asked (Spec T15 §2)", l)
        s10 = [l for l in lines if l.startswith("S10 — GET /v1/export/audit")]
        self.assertEqual(len(s10), 1)
        self.assertIn("→ [compare] the trail's roster.seat_rebound row for each seat S4 moved: the ceremony's id, seatEmail, via roster_change, and signerNames naming every signer (Spec T15 §3); the note about a seat still bound to a retired passkey is dropped where S4 moved it", s10[0])
        # Spec T12: S6 presses the whole roster (Ada, Ben, Cora) per payee
        self.assertEqual(len([l for l in H.dry_lines() if l.startswith("S6 — ") and "/approve" in l]), 6)

    def test_the_venue_probes_expectation_is_the_charters(self):
        """Spec T11 §3: the book answers C19 No, so the dry line expects the payee door's own refusal by name, in the estate's sentence; an acceptance is the finding."""
        s11 = [l for l in H.dry_lines() if l.startswith("S11 — ") and "Venue probe" in l]
        self.assertEqual(len(s11), 1)
        self.assertIn("→ expect 422 PAYEE_IS_VENUE_CONTRACT: This address is the contract of Uniswap v3 on arbitrum. Your charter says a payee must be a wallet held by a person or a company (question C19). Nothing was saved."
                      " (the book answers C19 \"No — only wallets held by people or companies\"; the live run reads the compiled policy charter's payeeVenueContracts); an acceptance is the finding", s11[0])
        self.assertNotIn("expect 201", s11[0])
        checksum = [l for l in H.dry_lines() if l.startswith("S11 — ") and "Checksum probe" in l]
        self.assertIn("→ expect a refusal, or the estate's acceptance recorded", checksum[0], "the checksum probe still expects a refusal")

    def test_an_estate_whose_c19_is_yes_keeps_the_expectation_of_20_september(self):
        """Spec T11 §3: with C19 answered Yes the venue line expects acceptance, as the law says, and a refusal is the finding — the expectation of Spec T8."""
        with unittest.mock.patch.dict(A.POLICY_ANSWERS, {"C19": {"choice": A.VENUE_YES}}):
            s11 = [l for l in H.dry_lines() if l.startswith("S11 — ") and "Venue probe" in l]
            self.assertEqual(len(s11), 1)
            self.assertIn("→ expect 201, accepted, as the law says (%s; the book answers C19 \"Yes\", and the live run reads the compiled policy charter's payeeVenueContracts); a refusal is the finding" % H.VENUE_RULING, s11[0])
            self.assertNotIn("PAYEE_IS_VENUE_CONTRACT", s11[0])
            self.assertEqual(H.venue_law_of_the_book(), "accepted")
        self.assertEqual(H.venue_law_of_the_book(), "refused")

    def test_s6_presses_the_roster_in_order_the_founder_last(self):
        """Spec T12 §2: S6 presses the roster people the harness holds a passkey for — Ada, Ben, Cora, the founder last — until whitelisted; a press refused SIGNATURE_NOT_COUNTED is recorded and the next presses."""
        s6 = [l for l in H.dry_lines() if l.startswith("S6 — ")]
        approves = [l for l in s6 if "/approve" in l]
        self.assertEqual(len(approves), 6, "three roster pressers (Ada, Ben, Cora) per payee")
        for name in ("Ada Approver", "Ben Signatory", "Cora Clerk"):
            mine = [l for l in approves if "(as %s, the roster in order, the founder last)" % name in l]
            self.assertEqual(len(mine), 2, name)
            for l in mine:
                self.assertIn("count it toward the quorum of two", l)
                self.assertIn("a SIGNATURE_NOT_COUNTED for a person whose seat S4 just moved is a finding, one for a seat S4 could not move is recorded and the next person presses", l)
                self.assertIn("until whitelisted or nobody is left", l)
        self.assertFalse(any("(as Harriet Founder, the roster" in l for l in approves), "the founder is the last resort, not a listed press")
        self.assertEqual(len([l for l in s6 if "/promote" in l and "pending_promotion" in l]), 2)
        self.assertTrue(any("read by this run's payee ids" in l for l in s6))

    def test_s5_ends_with_the_funding_wallet_and_the_faucet_asked_once(self):
        """Spec T13 §1 and §2: after the journey read, S5 reads the workspace, presses for the wallet where it is absent, reads it back, reads the balance and asks the faucet once."""
        lines = H.dry_lines()
        s5 = [l for l in lines if l.startswith("S5 — ")]
        journey = next(i for i, l in enumerate(s5) if l.startswith("S5 — GET /v1/journey"))
        tail = s5[journey + 1:]
        self.assertEqual(len(tail), 6)
        self.assertTrue(tail[0].startswith("S5 — GET /v1/workspace → expect fundingWallet (address, keyId, homeStack, bornAt, sentence) or fundingWalletAbsence (Spec 98); a wallet already born is reported and not pressed for again"), tail[0])
        self.assertIn("POST /v1/workspace/funding-wallet/options {} — only where fundingWalletAbsence stands → expect 200: options with the challenge the estate derives from funding-wallet:<workspace id>:<issuedAtMs> under the purpose workspace.funding_wallet, and issuedAtMs", tail[1])
        self.assertIn('POST /v1/workspace/funding-wallet {"issuedAtMs": "<issuedAtMs>", "response": "<assertion by Harriet Founder\'s passkey over the challenge>"} → expect 200: born true, fundingWallet {address, keyId, homeStack}; WALLET_BIRTH_REFUSED (the gateway\'s sentence) or GATEWAY_UNAVAILABLE (a fault) is reported in the estate\'s words and S5 fails naming it', tail[2])
        self.assertIn('GET /v1/workspace → expect the funding wallet just born, reported as "funding wallet: <address> on <home stack>, key <id>"', tail[3])
        self.assertIn('POST https://testnet.rpc.aeredium.io {"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": ["<funding wallet>", "latest"]} → expect a hex quantity, the wallet\'s native balance in wei on AEREDIUM testnet2 (chain 2237, SEAR)', tail[4])
        self.assertIn("the estate offers a browser no live balance of its funding wallet, so the chain's public RPC named in the faucet record is read; a fault is reported and the faucet is not asked", tail[4])
        self.assertIn('POST https://aeredium.io/faucet-api/request {"address": "<funding wallet>"} — once per run, only where the balance reads below 0.1 SEAR → expect paid true and tx_hash (0.5 SEAR), or the faucet\'s own refusal sentence, verbatim (its limits: four payments per wallet and eight per IP in a day, and 200 SEAR across everyone)', tail[5])
        s6 = [l for l in lines if l.startswith("S6 — GET /v1/payees")]
        self.assertIn("the judgement is the register's, not the press's — a register reading proposed after the platform counted 2 of 2 fails with the mirror sentence (Spec T13 §3)", s6[0])
        s7 = [l for l in lines if l.startswith("S7 — ")]
        self.assertIn("expect the funding wallet S5 gave the estate (fundingWallet, with the fund sentence and the chains this deployment pays on, Spec 104 §1)", s7[0])
        self.assertTrue(s7[-1].startswith("S7 — GET /v1/workspace/funding-account/balances (as Cora Clerk), GET /v1/workspace/funding-account/balances (as Harriet Founder at Harness Treasury)"), s7[-1])
        self.assertIn("the money after: both workspaces' USDC and gas accounts, for S10's count", s7[-1])
        s8 = [l for l in lines if l.startswith("S8 — GET /v1/workspace/readiness")]
        self.assertIn('printed: transactable True once the wallet exists (False, reason "no funding wallet", before it), and the funding wallet\'s address', s8[0])

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
