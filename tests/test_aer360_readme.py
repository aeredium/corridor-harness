"""The README section and the CHANGELOG say the things a founder running the estate harness has to be told (Spec T7)."""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_harness as H  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), "r", encoding="utf-8") as handle:
        return handle.read()


class EstateHarnessReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = read("README.md")
        self.section = self.text.split("## The estate harness", 1)[1]

    def test_the_readme_has_the_estate_harness_section_after_the_corridors(self):
        self.assertIn("## The estate harness", self.text)
        self.assertLess(self.text.index("## The tests of the harness itself"), self.text.index("## The estate harness"))

    def test_it_states_the_two_laws_and_what_it_needs(self):
        self.assertIn("The harness is the founder, not a judge.", self.section)
        self.assertIn("A failure is evidence, not a verdict.", self.section)
        self.assertIn("/usr/bin/openssl", self.section)
        self.assertIn("http.cookiejar", self.section)
        self.assertIn("`none`", self.section)

    def test_it_names_the_estate_the_people_and_the_money(self):
        for words in ("Harness Holdings Pty Ltd", "Harriet Founder", "Ada Approver", "Ben Signatory", "Cora Clerk", "Operating account",
                      "10,000", "50,000", "250,000", "Northwind Supplies", "Contoso Legal", "1,250", "4,999.99", "12,000"):
            self.assertIn(words, self.section, words)
        self.assertIn("harness+<first>@aeredium.io", self.section)

    def test_it_names_the_twelve_stations_and_the_three_hats(self):
        for station, title in H.STATIONS:
            self.assertIn(station, self.section)
        for hat in ("auditor", "attacker", "optimizer"):
            self.assertIn(hat, self.section)

    def test_it_says_where_the_keys_live_and_that_the_link_is_a_secret(self):
        self.assertIn("~/.aer360-harness/<estate>/<person>.json", self.section)
        self.assertIn("0600", self.section)
        self.assertIn("never pasted into a chat", self.section)

    def test_it_lists_the_options_and_the_commands_are_this_repositorys(self):
        for option in ("--base", "--invite", "--from S5", "--dry", "--out", "--fresh"):
            self.assertIn(option, self.section, option)
        self.assertIn("python3 aer360_harness.py --dry", self.section)
        self.assertIn("python3 -m unittest discover tests", self.section)

    def test_it_names_the_report_and_says_it_names_no_real_person(self):
        self.assertIn("aer360-harness-<date>.md", self.section)
        self.assertIn("names no real person and no real company", self.section)

    def test_it_records_what_the_code_and_the_spec_disagree_on(self):
        self.assertIn("version 12", self.section)
        self.assertIn("C16", self.section)
        self.assertIn("standsWritten", self.section)
        self.assertIn("one role-bearing credential", self.section)
        self.assertIn("funding account", self.section)

    def test_it_does_not_disturb_the_corridors_guarded_sentences(self):
        self.assertEqual(len([l for l in self.section.splitlines() if "have passed in the same run" in l]), 0)
        for prefix in ("Runs by itself: ", "Left to a person, ", "Pauses for the owner's passkey"):
            self.assertFalse(any(l.startswith(prefix) for l in self.section.splitlines()), prefix)


    def test_it_says_what_the_law_says_and_what_the_harness_expects_since_spec_t8(self):
        self.assertIn("Spec T8, 20 September 2026", self.section)
        self.assertIn("Unless it is stipulated explicitly in the questionnaire, it must be accepted", self.section)
        self.assertIn("accepted, as the law says (Bear, 20 September 2026: unless the questionnaire stipulates otherwise, an address is accepted)", self.section)
        self.assertIn("a finding only if refused", self.section)
        self.assertIn("compared by content", self.section)
        self.assertIn("`name — role — email`", self.section)
        self.assertIn("`jsonb`", self.section)
        self.assertIn("not compared: no rendering for kind <k>", self.section)
        self.assertIn("the invitation road sends the email before it answers, which is where its four seconds go", self.section)
        self.assertIn("reported and not judged", self.section)
        self.assertIn("*last run* column", self.section)
        self.assertIn("closed, still open or new", self.section)
        self.assertIn("The Python confirms what was fixed.", self.section)
        self.assertIn("`tests/fixtures/aer360-dry-calls.txt`", self.section)
        self.assertNotIn("the read-back word for word against the answers given", self.section, "the comparison is by content now")

    def test_it_says_a_payee_is_whitelisted_at_its_quorum_since_spec_t9(self):
        self.assertIn("Spec T9, 20 September 2026", self.section)
        self.assertIn("S6 presses until the quorum is met", self.section)
        self.assertIn("governanceSignersFor", self.section)
        self.assertIn("may_still_approve", self.section)
        self.assertIn("1 of 2 approvals recorded for this address. One more is needed, from", self.section)
        self.assertIn("a quorum that exceeds its roster", self.section)
        self.assertIn("read from the row whose `id` is this run's `payee_id`, never by address", self.section)
        self.assertIn("WHITELIST_ROSTER", self.section)
        self.assertIn("WHITELIST_QUORUM", self.section)

    def test_it_says_every_person_is_brought_in_on_their_own_credential_since_spec_t10(self):
        self.assertIn("Spec T10, 20 September 2026", self.section)
        self.assertIn("compares the session's `credentialId` with the founder's", self.section)
        self.assertIn("brings them in again", self.section)
        self.assertIn("`~/.aer360-harness/<estate>/<person>-2-<date>.json`", self.section)
        self.assertIn("never over it", self.section)
        self.assertIn("a credential of <name>'s own, not the founder's", self.section)
        self.assertIn("already on their own credential", self.section)
        self.assertIn("`enrolled_not_seated` or names a credential other than her session's", self.section)
        self.assertIn("a grant the estate refuses is a finding in the estate's words", self.section)
        self.assertIn("`sharesCredentialWith`", self.section)
        self.assertIn("shares a credential with …; invite them again to give them their own", self.section)
        self.assertIn("the frozen fixture is 134 lines", self.section)
        self.assertIn("S6 is Spec T9's, unchanged", self.section)
        self.assertIn("requires the `approver` standing", self.section)
        self.assertIn("`SIGNATURE_NOT_COUNTED`", self.section)
        self.assertIn("`validateMultisigSigner`", self.section)
        self.assertIn("`before_spec_91=True`", self.section)
        self.assertIn("until Spec 91; see Spec T10 below", self.section)


    def test_it_says_the_book_learned_catalog_version_14_and_what_the_auditor_reads_back_since_spec_t11(self):
        self.assertIn("Spec T11, 21 September 2026", self.section)
        self.assertIn("aer360-harness-2026-09-21.md", self.section)
        self.assertIn("commit cf3be4a, `CATALOG_VERSION 14`", self.section)
        for words in ("*The people who may change these rules, at the number you set for a change*", "*No — only wallets held by people or companies*",
                      "*One person, named here*", "`{choice, person: {name, email}}`", "Harriet Founder, CEO", "2,000.00 (the holder alone)", "10,000.00 (two signatures enough)",
                      "WA1 gains Ben beside Ada", "WQ stays at one", "`CATALOG_VERSION_ANSWERED = 14`", "the estate states no catalog version on the roads a browser walks",
                      "`tests/fixtures/aer360-served-2026-09-21.json`", "`payeeApproval` is the change-approvers answer", "`payeeVenueContracts` is `refused`",
                      "`{held: by_person, name: Ben Signatory, email, title: Officer}`", "`signingTiers.holderAloneUpToCents` is `200000`", "`twoSignaturesUpToCents` `1000000`",
                      "never as the written *US$1 and 00 cents.*", "*You answered No: such an address will be refused when entered.*",
                      "no `payeeApproval`, no `holder`", "`PAYEE_IS_VENUE_CONTRACT`, 422",
                      "*This address is the contract of Uniswap v3 on ethereum. Your charter says a payee must be a wallet held by a person or a company (question C19). Nothing was saved.*",
                      "keeps the expectation of 20 September", "*within the holder's own figure (US$2,000.00), one signature — the holder's*",
                      "*two signatures (above US$2,000.00, up to US$10,000.00)*", "*three signatures (above US$10,000.00)*", "invents no source account",
                      "the frozen fixture is 141 lines", "`refuses_venue_contract=None` follows the charter", "`catalog_version=12` leaves the seven out"):
            self.assertIn(words, self.section, words)
        self.assertIn("the catalog is version 14 since AER 360 Spec 92; see Spec T11 below", self.section)
        self.assertIn("since Spec T11 the probe reads the charter's answer to C19 at run time", self.section)
        self.assertIn("a finding only if refused", self.section, "Spec T8's sentence stands, for an estate whose C19 is Yes")

    def test_it_says_the_harness_follows_a_walk_back_since_spec_t12(self):
        self.assertIn("Spec T12, 21 September 2026", self.section)
        self.assertIn("aer360-harness-2026-09-21-223148.md", self.section)
        self.assertIn("AER 360 Spec 95", self.section)
        for words in ("A walk-back is followed, once per question", "`CHARTER_INCOMPLETE` with `walkBackTo`",
                      "walked back to WA1: <the estate's sentence>; answered from the book and returned to the read-back",
                      "walked back to twice is a failure with both sentences", "applies to S3 and S5 alike",
                      "take their expectation from the answer book for every question the read-back carries",
                      "how many lines came from this run's answers and how many from the book",
                      "the whitelist door admits any active roster signer", "the roster is the census of four at two",
                      "in order with the founder last", "pressing on past a `SIGNATURE_NOT_COUNTED` refusal",
                      "Ada refused, Ben and Cora counted, two of four", "bound to her retired credential",
                      "the census signs it at Spec 99", "a note, not a finding, because the estate is telling the truth",
                      "S7 is unchanged and still waits on Spec 98's funding wallet"):
            self.assertIn(words, self.section, words)


    def test_it_says_the_harness_births_and_funds_the_wallet_since_spec_t13(self):
        self.assertIn("Spec T13, 22 September 2026", self.section)
        self.assertIn("aer360-harness-2026-09-21-234438.md", self.section)
        self.assertIn("AER 360 Spec 98", self.section)
        for words in ("S5 ends by giving the estate its funding wallet", "`POST /v1/workspace/funding-wallet`", "`funding-wallet:<workspace id>:<issuedAtMs>`",
                      "`workspace.funding_wallet`", "funding wallet: <address> on <home stack>, key <id>", "`WALLET_BIRTH_REFUSED` carries the gateway's sentence",
                      "`GATEWAY_UNAVAILABLE` is a fault", "`FUNDING_WALLET_ALREADY_BORN` is never met", "S5 funds the wallet from the faucet, once, as the founder would",
                      "`https://testnet.rpc.aeredium.io`", "`https://aeredium.io/faucet-api/request`", '`{"address": "<address>"}`',
                      "four payments per wallet and eight per IP in a day, and 200 SEAR across everyone", "never asks twice in one run and never invents a balance",
                      "never judged as the estate's", "S6 judges the register, not the press",
                      "the platform counted 2 of 2 and the register reads proposed; the estate's mirror disagrees with the platform",
                      "S7 says what the payments would need", "US$18,249.99 of USDC", "never mints or moves the asset", "The report names the wallet",
                      "`transactable True`", "no address of the faucet's or the treasury's", "143 → 150"):
            self.assertIn(words, self.section, words)


    def test_it_says_the_approvers_sign_adas_seat_home_and_s6_counts_ada_since_spec_t15(self):
        self.assertIn("Spec T15, 22 September 2026", self.section)
        self.assertIn("aer360-harness-2026-09-22-135010.md", self.section)
        self.assertIn("AER 360 Spec 99 (aeredium/AERAccounts, commit 33e039c)", self.section)
        for words in ("S4 signs the pending roster changes", "`GET /v1/roster/changes`", "`roster-change:<workspace id>:<pendingTxId>:<issuedAtMs>`", "`roster.change`",
                      "`POST /v1/roster/changes/{pendingTxId}/sign`", "reading `signaturesCollected` after each, until the estate reports it applied",
                      "asserts the change applied with its seat naming the owner's current credential in the estate's short form",
                      "Ben Signatory counted (1 of 2); Cora Clerk counted (2 of 2); applied: the seat now names",
                      "judged for Rule 13 the way S10 judges every refusal and reported in the estate's words", "`CHANGE_SIGNER_NOT_ON_ROSTER`", "`APPROVER_ALREADY_SIGNED`",
                      "`SIGNATURE_NOT_COUNTED` (the platform's *not authorized*)", "`PLATFORM_REFUSED`", "*conflict: pending transaction expired*",
                      "the move is proposed afresh once; a second expiry fails S4 naming the ceremony", "S4 does nothing new and says so in one line",
                      "S6 expects Ada to count", "Ada's press counted (1 of 2) and Ben's (2 of 2), stops at the count so Cora is not asked", "*entry is already active*",
                      "a `SIGNATURE_NOT_COUNTED` for a person whose seat S4 just moved is a finding, not a note", "S10 reads the trail", "`GET /v1/export/audit`",
                      "`roster.seat_rebound`", "SPEC.md spells it `roster.seat.rebound`", "naming the ceremony and every signer", "drops Spec T12's note",
                      "Two disagreements carried to Bear, not silently resolved", "not at a sign-in", "never from login/verify",
                      "Granting <who>'s seat again in this room, or <who> redeeming a fresh invitation, proposes the move afresh", "`POST /v1/approver-seats/grant`",
                      "a roster change this estate did not propose", "does not guess whose seat it moves", "the platform's ceremony is content-bound",
                      "`sign_the_roster_changes`", "150 → 156", "`change_roster`", "`before_spec_99`", "`ceremony_lapses`", "`lapse_after_first_signature`", "`account_email`"):
            self.assertIn(words, self.section, words)
        self.assertLess(self.section.index("Spec T13, 22 September 2026"), self.section.index("Spec T15, 22 September 2026"))

    def test_it_says_the_harness_grants_a_stale_seat_again_since_spec_t17(self):
        self.assertIn("Spec T17, 23 September 2026", self.section)
        self.assertIn("aer360-harness-2026-09-22-214017.md", self.section)
        self.assertIn("it does not recognise your key as one of this wallet's signatories", self.section)
        for words in ("the seat view has no onRoster; skipping", "`GET /v1/approver-seats`", "`GET /v1/roster/changes`",
                      "`harness+<name>@aeredium.io`, never by display name", "a change already awaits; not granted",
                      "`propose_the_move_afresh`", "`REPROPOSALS_AT_MOST`", "*moved at once*", "two passkeys enrolled; not granted",
                      "not of the harness; not granted", "unverified: <rosterSaid>", "A `true` seat prints nothing",
                      "change <id> moves <who>'s seat to a credential the harness does not hold; not signed",
                      "never the stale seat's owner, and — where they have a seat row in the seats view — reading `onRoster: true`", "is able on the list's word alone",
                      "<n> required, <m> able", "grants no further seat", "up to three times over a bounded wait",
                      "*<k> of <n> signatures*", "for a person whose seat read `null` the finding cites the unverified seat",
                      "One note per seat granted", "*Spec 95 opened a governed ceremony to move it* is deleted", "it was never a fact",
                      "`onRoster`, `rosterSaid`", "156 → 159", "`seat_on_roster`", "`seats_override`",
                      "rerun once 105 is live", "count Ada 1 of 2", "Each of the spec's tests was red on main"):
            self.assertIn(words, self.section, words)
        self.assertLess(self.section.index("Spec T15, 22 September 2026"), self.section.index("Spec T17, 23 September 2026"))

class ChangelogTest(unittest.TestCase):
    def test_the_changelog_records_spec_t17_before_t15_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T17 — S4 grants a stale seat again before signing, one seat at a time, and S6 counts Ada (23 September 2026)", text)
        self.assertLess(text.index("## Spec T17"), text.index("## Spec T15"))
        t17 = text.split("## Spec T17", 1)[1].split("## Spec T15", 1)[0]
        for words in ("aer360-harness-2026-09-22-214017.md", "AER 360 Spec 105", "fix/a-seat-tells-the-platforms-truth",
                      "it does not recognise your key as one of this wallet's signatories", "`sign_the_roster_changes`",
                      "`_sign_pass_t15`", "`_sign_pass_t17`", "`_sign_change_t17`", "`_confirm_seat_onroster`", "`_record_seat_moved`",
                      "the seat view has no onRoster; skipping", "`GET /v1/roster/changes`", "`GET /v1/approver-seats`",
                      "`harness+<name>@aeredium.io`, never by display name", "a change already awaits; not granted",
                      "`propose_the_move_afresh`", "`REPROPOSALS_AT_MOST`", "*moved at once*", "two passkeys enrolled; not granted",
                      "not of the harness; not granted", "unverified: <rosterSaid>",
                      "change <id> moves <who>'s seat to a credential the harness does not hold; not signed",
                      "where they have a seat row — reading `onRoster: true`", "is able on the list's word alone", "*<n> required, <m> able*",
                      "grants no further seat", "`SEAT_REREAD_ATTEMPTS`", "*<k> of <n> signatures*",
                      "for a person whose seat read `null` the finding cites the unverified seat", "`seat_binding_notes`",
                      "*Spec 95 opened a governed ceremony to move it* is deleted", "it was never a fact",
                      "`SEAT_ON_ROSTER`", "`SEAT_ROSTER_SAID`", "`onRoster`", "`rosterSaid`", "156 → 159 lines",
                      "`seat_on_roster`", "`seats_override`", "`rebindRosterSeats`", "`moving`",
                      "`tests/test_aer360_roster.py`", "2 required, 1 able", "moved at once", "the passkey files, the estate and the platform"):
            self.assertIn(words, t17, words)

    def test_the_changelog_records_spec_t15_before_t13_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T15 — The harness has the approvers sign a change of who the approvers are, and S6 counts Ada (22 September 2026)", text)
        self.assertLess(text.index("## Spec T15"), text.index("## Spec T13"))
        t15 = text.split("## Spec T15", 1)[1].split("## Spec T13", 1)[0]
        for words in ("aer360-harness-2026-09-22-135010.md", "AER 360 Spec 99", "commit 33e039c", "`sign_the_roster_changes`", "`read_roster_changes`", "`sign_as_the_list_names`",
                      "`sign_roster_change_as`", "`assert_the_seat_moved`", "`refusal_judged`", "`propose_the_move_afresh`", "`REPROPOSALS_AT_MOST`", "`route_not_found`",
                      "`GET /v1/roster/changes`", "`POST /v1/roster/changes/{pendingTxId}/sign/options`", "`POST /v1/roster/changes/{pendingTxId}/sign`",
                      "`roster-change:<workspace id>:<pendingTxId>:<issuedAtMs>`", "`roster.change`", "`request(..., retry=False)`", "`credentialIdShortForm`",
                      "`facts[\"seats_moved\"]`", "`refusal_without_why`", "a second expiry fails S4 naming the ceremony",
                      "none awaits a signature: the register lists no roster change, so S4 did nothing new (Spec T15 §4)", "`approve_to_quorum`", "`seat_moved_for`",
                      "`audit_the_trail_for_moved_seats`", "`seat_binding_notes`", "`GET /v1/export/audit?limit=5000`", "`roster.seat_rebound`", "`roster.seat.rebound`",
                      "`signerNames`", "A DISAGREEMENT CARRIED TO BEAR, NOT SILENTLY RESOLVED", "not at a sign-in", "`rebindRosterSeats`", "never from login/verify",
                      "Granting <who>'s seat again in this room, or <who> redeeming a fresh invitation, proposes the move afresh.", "`POST /v1/approver-seats/grant`",
                      "a roster change this estate did not propose", "`roster.change_proposed`", "content-bound", "drop the `seat is None` road", "150 → 156 lines",
                      "`ROSTER_CHANGES_ROUTE`", "`ROSTER_CHANGE_SIGN_ROUTE`", "`ROSTER_CHANGE_SIGN_OPTIONS_ROUTE`", "`ROSTER_CHANGE_PURPOSE`", "`ROSTER_CHANGE_BINDING`",
                      "`ROSTER_SEAT_REBOUND`", "`AUDIT_EXPORT_ROUTE`", "`credential_short_form`", "`CHANGE_SIGNER_NOT_ON_ROSTER` (403)", "`ROSTER_CHANGE_UNKNOWN` (404)",
                      "`APPROVER_ALREADY_SIGNED` (409)", "`PLATFORM_REFUSED` (502)", "`rebind_roster_seats`", "`replace_multisig_signers`", "`seat_change_roster`",
                      "`born_ceremony`", "`ceremony_is_live`", "`list_roster_changes`", "`roster_change_view`", "`sign_roster_change`", "`apply_roster_change`",
                      "`roster_change_sentence`", "`roster_change_signed_sentence`", "`platform_refused_sentence`", "`audit_export`", "`approvalPlatformRefusal`",
                      "`change_roster=(\"ben\", \"cora\")`", "`before_spec_99`", "`ceremony_lapses`", "`lapse_after_first_signature`", "`account_email`",
                      "`tests/test_aer360_roster.py`", "`aer360_answers.py`, the passkey files, the estate"):
            self.assertIn(words, t15, words)

    def test_the_changelog_records_spec_t13_before_t12_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T13 — The harness presses for the funding wallet, funds it from the faucet as the founder would, and reads the payee register back after the count (22 September 2026)", text)
        self.assertLess(text.index("## Spec T13"), text.index("## Spec T12"))
        t13 = text.split("## Spec T13", 1)[1].split("## Spec T12", 1)[0]
        for words in ("aer360-harness-2026-09-21-234438.md", "AER 360 Spec 98", "`give_the_estate_its_funding_wallet`", "`funding_wallet_words`", "`read_native_balance`",
                      "`fund_the_wallet_from_the_faucet`", "`faucet_words`", "`request_outside`", "`request(..., retry=False)`", "`FUNDING_WALLET_PURPOSE`",
                      "`funding-wallet:<workspace id>:<issuedAtMs>`", "`WALLET_BIRTH_REFUSED`", "`GATEWAY_UNAVAILABLE`", "`FUNDING_WALLET_ALREADY_BORN` is never met",
                      "`Call.outside`", "`audit_money`", "`audit_refusals`", "`mirror_sentence`", "`MIRROR_DISAGREES`",
                      "the platform counted 2 of 2 and the register reads proposed; the estate's mirror disagrees with the platform", "`payments_need`", "`payments_need_line`",
                      "US$18,249.99 of USDC", "`funding_summary_lines`", "143 → 150 lines", "`TESTNET_RPC_URL`", "`FAUCET_REQUEST_URL`", "`GAS_FLOOR_SEAR`", "`coin_amount`",
                      "`FaucetDouble`", "`TestnetRpcDouble`", '`funding_wallet="press"|"born"|"refused"|"unavailable"`', "`mirror_lags`", "`register_corrects`", "`asset_short`",
                      "`tests/test_aer360_funding.py`", "`aer360_answers.py`, the passkey files, the estate, the faucet"):
            self.assertIn(words, t13, words)

    def test_the_changelog_records_spec_t12_before_t11_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T12 — The harness follows a walk-back as a browser would, and S6 presses the roster people whose presses count (21 September 2026)", text)
        self.assertLess(text.index("## Spec T12"), text.index("## Spec T11"))
        t12 = text.split("## Spec T12", 1)[1].split("## Spec T11", 1)[0]
        for words in ("aer360-harness-2026-09-21-223148.md", "AER 360 Spec 95", '`walkBackTo {questionId: "WA1"}`',
                      "`audit_readback`", "`audit_charter`", "`readback_provenance_note`", "`walk_back_of`", "`follow_walk_back`",
                      "`drive_to_read_back`", "walked back to WA1: <the estate's sentence>; answered from the book and returned to the read-back",
                      "The same question walked back to twice is a failure carrying both sentences", "`approve_to_quorum`", "`whitelist_pressers`",
                      "the founder last", "`SIGNATURE_NOT_COUNTED`", "names who counted and who did not", '`next_presser` and the pre-89 "one further press"',
                      "Ada refused, Ben and Cora counted, two of four", "`seat_binding_notes`", "the seat still bound to a retired passkey until Spec 99 lands",
                      "141 → 143 lines", "the whitelist door learns AER 360 Spec 95 — `address_action`'s approve and reject admit any authenticated author",
                      "`WalkBackDouble`", "`TheHarnessFollowsAWalkBack`", "twenty-eight lines of which the run answered ten",
                      "S7's P1 clears at submission now that Northwind is whitelisted",
                      "`aer360_answers.py` (T11's book stands)",
                      "`corridor_harness.py`, `series.py`, `tables.py`, `aer360_passkey.py`, `aer360_tables.py` and the corridor's tests"):
            self.assertIn(words, t12, words)

    def test_the_changelog_records_spec_t11_before_t10_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T11 — The answer book learns catalog version 14, and the auditor reads the new law back (21 September 2026)", text)
        self.assertLess(text.index("## Spec T11"), text.index("## Spec T10"))
        t11 = text.split("## Spec T11", 1)[1].split("## Spec T10", 1)[0]
        for words in ("aer360-harness-2026-09-21.md", "commit cf3be4a", "`CATALOG_VERSION 14`", "`person_or_none`",
                      '`C11A` `{"choice": "The people who may change these rules, at the number you set for a change"}`',
                      '`C11C` `{"entries": []}`', '`C19` `{"choice": "No — only wallets held by people or companies"}`',
                      '`WO1` `{"choice": "One person, named here", "person": {"name": "Ben Signatory", "email": <Ben\'s>}}`',
                      '`WO2` `{"entries": [{"name": "Harriet", "surname": "Founder", "email": <Harriet\'s>, "title": "CEO"}]}`',
                      '`WO3` `{"cents": "200000"}`', '`WO4` `{"cents": "1000000"}`', "`holder_alone_cents`", "`two_signatures_cents`", "`WA1` gains Ben beside Ada",
                      "`CATALOG_VERSION_ANSWERED = 14`", "`ADDED_IN_V14`", "every one known to the book", "with the version pair in the sentence",
                      "who approves a new payee (C11A: the answer, its roster and its quorum)", "may a payee be a venue's contract (C19)", "who holds this wallet (WO1)",
                      "the holder's own figure (WO3)", "the two-signature figure (WO4)", "the signers (WA1, and WO2's third party once)", "`C19_DOOR`",
                      "`PAYEE_IS_VENUE_CONTRACT`, 422", "`payee_is_venue_contract_sentence`", "it saved a venue's contract", "the expectation of 20 September stands",
                      "`under_the_tiers`", "within the holder's own figure (US$2,000.00)", "does not invent a source account", "134 → 141 lines",
                      "`tests/fixtures/aer360-served-2026-09-21.json`", "`TIER_TWO_NOT_ABOVE_ONE`", "`tiers_need_three_people`", "`read_wallet_people`",
                      "`VENUE_CONTRACTS`", "`refuses_venue_contract=None`", "`catalog_version=12` leaves the seven out",
                      "corridor_harness.py, series.py, tables.py, aer360_passkey.py, aer360_tables.py and the corridor's tests are not touched"):
            self.assertIn(words, t11, words)


    def test_the_changelog_records_spec_t7_and_its_files(self):
        text = read("CHANGELOG.md")
        self.assertIn("Spec T7", text)
        for name in ("aer360_harness.py", "aer360_answers.py", "aer360_tables.py", "aer360_passkey.py", "tests/fixtures/aer360-questioncatalog.v11.ts"):
            self.assertIn(name, text, name)
        self.assertIn("corridor_harness.py, series.py, tables.py and the corridor's tests are not touched", text)

    def test_the_changelog_records_spec_t10_before_t9_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T10 — Every person is brought in on their own credential, and the harness proves the quorum (20 September 2026)", text)
        self.assertLess(text.index("## Spec T10"), text.index("## Spec T9"))
        t10 = text.split("## Spec T10", 1)[1].split("## Spec T9", 1)[0]
        for words in ("aer360-harness-2026-09-20-135419.md", "commit 9964205, PR #112", "compares the session's `credentialId` with the founder's",
                      "`<person>-2-<date>.json`", "`next_key_path`", "a credential of <name>'s own, not the founder's", "already on their own credential",
                      "`POST /v1/approver-seats/grant`", "`Person.key_file`", "`stored_key_paths`", "`retired_passkeys`", "`audit_people`",
                      "`sharesCredentialWith`", "`shares_credential_sentence`", "121 → 134 lines", "`APPROVER_SEAT_CREDENTIAL_SHARED`", "`APPROVER_SEAT_AMBIGUOUS`",
                      "`person.credential_replaced`", "`governanceAlreadyStood`", "`validateMultisigSigner`", "`before_spec_91`", "`seat_completes_on_redemption=False`",
                      "`second_authorship_entry`", "`platform_names_approver`", "A DISAGREEMENT CARRIED TO BEAR, NOT SILENTLY RESOLVED", "`routes/payees.ts:221`",
                      "This action needs an approver", "not authorized", "`SIGNATURE_NOT_COUNTED`",
                      "S6's press loop, the founder's enrolment, the answers to every interview and every figure",
                      "corridor_harness.py, series.py, tables.py, aer360_tables.py and the corridor's tests are not touched"):
            self.assertIn(words, t10, words)

    def test_the_changelog_records_spec_t9_before_t8_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T9 — A payee is whitelisted when its quorum is met, and the harness presses for the quorum (20 September 2026)", text)
        self.assertLess(text.index("## Spec T9"), text.index("## Spec T8"))
        t9 = text.split("## Spec T9", 1)[1].split("## Spec T8", 1)[0]
        for words in ("presses until the quorum is met", "governanceSignersFor", "WHITELIST_ROSTER", "WHITELIST_QUORUM",
                      "may_still_approve", "a quorum that exceeds its roster", "this run's `payee_id`",
                      "aer360-dry-calls.txt", "119 → 121 lines", "SIGNATURE_NOT_COUNTED",
                      "a second press by the same person is refused", "answers as the estate does after Spec 89",
                      "corridor_harness.py, series.py, tables.py, aer360_passkey.py, aer360_tables.py and the corridor's tests are not touched"):
            self.assertIn(words, t9, words)

    def test_the_changelog_records_spec_t8_before_t7_and_names_every_change(self):
        text = read("CHANGELOG.md")
        self.assertIn("## Spec T8 — The harness expects what the law says (20 September 2026)", text)
        self.assertLess(text.index("## Spec T8"), text.index("## Spec T7"))
        t8 = text.split("## Spec T8", 1)[1].split("## Spec T7", 1)[0]
        for words in ("the venue probe expects acceptance", "compared by content", "as_the_estate_stores", "`jsonb`", "name — role — email",
                      "the invitation road sends the email before it answers", "*last run* column", "closed, still open or new",
                      "tests/fixtures/aer360-dry-calls.txt", "currency_spoken_as_code", "refuses_venue_contract", "ADDRESS_PROPOSAL_REFUSED",
                      "corridor_harness.py, series.py, tables.py, aer360_passkey.py, aer360_tables.py and the corridor's tests are not touched"):
            self.assertIn(words, t8, words)


class GitignoreTest(unittest.TestCase):
    def test_the_report_is_never_committed_by_accident(self):
        lines = [l.strip() for l in read(".gitignore").splitlines() if l.strip()]
        self.assertIn("aer360-harness-*.md", lines)
        try:
            ignored = subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", "aer360-harness-2026-09-20.md"], capture_output=True).returncode == 0
        except OSError:
            self.skipTest("git is not on this machine")
        self.assertTrue(ignored)


if __name__ == "__main__":
    unittest.main()
