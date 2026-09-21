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


class ChangelogTest(unittest.TestCase):
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
