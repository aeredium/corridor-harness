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


class ChangelogTest(unittest.TestCase):
    def test_the_changelog_records_spec_t7_and_its_files(self):
        text = read("CHANGELOG.md")
        self.assertIn("Spec T7", text)
        for name in ("aer360_harness.py", "aer360_answers.py", "aer360_tables.py", "aer360_passkey.py", "tests/fixtures/aer360-questioncatalog.v11.ts"):
            self.assertIn(name, text, name)
        self.assertIn("corridor_harness.py, series.py, tables.py and the corridor's tests are not touched", text)

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
