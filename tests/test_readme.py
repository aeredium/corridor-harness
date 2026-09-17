"""
The README says the things a tester has to be told (Spec T2 §7), in the words that
will be read aloud to them.
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

README = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")


def read():
    with open(README, "r", encoding="utf-8") as handle:
        return handle.read()


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = read()

    def test_the_consent_page_road_for_a_second_agent(self):
        self.assertIn("Connect a different agent", self.text)
        self.assertIn("You are already connected", self.text)

    def test_this_repository_is_the_harnesss_home_and_changes_arrive_by_pull_request(self):
        self.assertIn("This repository is the harness's home", self.text)
        self.assertIn("pull request", self.text)

    def test_it_says_which_tests_gate_money(self):
        self.assertIn("A1, A2, A3, A5 and A4's native-balance check", self.text)
        self.assertIn("A6 and A4's notes gate nothing", self.text)

    def test_it_says_a_check_that_could_not_be_made_holds_money_back(self):
        """Spec T2 §5 as amended 14 September 2026; the README's gate paragraph says the same."""
        self.assertIn("gates money only when it was made and passed", self.text)
        self.assertIn("holds money back **exactly as a failure does**", self.text)
        self.assertIn("never say money moved without the chain having been read", self.text)
        self.assertIn("A4's native-balance check was not made: the run file names no RPC for arbitrum", self.text)
        self.assertNotIn("that holds nothing back, and the report says it was not made", self.text)

    def test_it_says_what_a5_costs(self):
        self.assertIn("one metered `check_action` unit", self.text)

    def test_it_says_the_required_field_wins(self):
        """Spec T3 §1: the README names the decoy, the rule and what a dry run prints."""
        self.assertIn("Spec T3", self.text)
        self.assertIn("the required field wins", self.text)
        self.assertIn("NOT ACCEPTED", self.text)
        self.assertIn("A door that declares only `amount_usd`, one that speaks dollars, is still obeyed.", self.text)
        self.assertIn("which for the amount is `amount_usd_cents`", self.text)
        self.assertNotIn("A dry run, with no schema to read, prints the Guide's names.", self.text)

    def test_it_says_a4_reads_the_tokens_where_the_wallet_puts_them(self):
        """Spec T3 §2 and §3: the README says where A4 reads the tokens, what it prints, and what the rails line notes."""
        self.assertIn("A4 reads the tokens where the Wallet puts them", self.text)
        self.assertIn("`tokens.balances`", self.text)
        self.assertIn("`tokens.road`", self.text)
        self.assertIn("every verified stablecoin row this door holds for arbitrum", self.text)
        self.assertIn("where the Wallet states them and they agree with the chain, A4 is a plain pass", self.text)
        self.assertIn("`aeredium-testnet (2237)`", self.text)
        self.assertIn("printed as a note, not a failure", self.text)
        self.assertIn("on 15 September 2026 for A4 again (Spec T3)", self.text)

    def test_it_carries_the_chain_guards_sentence(self):
        self.assertIn("which the product does not offer; the series runs on ethereum, arbitrum and base. "
                      "Create the agent again on one of those and consent it.", self.text)

    def test_it_no_longer_sends_anyone_to_can_sign(self):
        self.assertNotIn("`police.can_sign`", self.text)
        self.assertIn("MCP Police carries no tool called `can_sign`", self.text)
        self.assertIn("pact.policy_hash", self.text)

    def test_the_commands_it_prints_are_this_repositorys(self):
        for command in re.findall(r"python3 [^\n`]+", self.text):
            self.assertNotIn("tools/harness", command, command)

    def test_the_gate_the_readme_names_is_the_gate_the_harness_keeps(self):
        """The README's sentence about what gates money is read against the gate itself."""
        said = [line for line in self.text.splitlines() if "have passed in the same run" in line]
        self.assertEqual(len(said), 1, "one sentence names the gate")
        for test_id in h.Runner.GATE_TESTS:
            self.assertIn(test_id, said[0], "the README names %s among the tests that gate money" % test_id)
            self.assertIn(test_id, S.BY_ID)
        for test_id in ("A4", "A6"):
            self.assertNotIn("%s," % test_id, said[0], "%s does not gate money" % test_id)
        self.assertIn("A4's native-balance check", said[0])

    def test_it_names_version_1_2_as_the_series_the_harness_runs(self):
        """Spec T6 §4: the README names version 1.2, sixty-three tests, and the fixture that carries it."""
        self.assertIn("version 1.2, 17 September 2026", self.text)
        self.assertIn("sixty-three tests", self.text)
        self.assertIn("`tests/fixtures/series-1.2.md`", self.text)
        self.assertNotIn("series-1.0", self.text)
        self.assertIn("on 15 September 2026 for A4 again (Spec T3)", self.text)
        self.assertIn("A hold the Series expected (C5, D13) is a pass.", self.text)
        self.assertNotIn("H3) is a pass", self.text, "version 1.2's H3 expects a refusal and an allow, not a hold")

    def test_the_three_lists_it_prints_are_series_pys(self):
        """The README's three lists are read against series.py's own, so they cannot drift (Spec T1 §4, Spec T6 §3)."""
        def ids_on(prefix):
            lines = [line for line in self.text.splitlines() if line.startswith(prefix)]
            self.assertEqual(len(lines), 1, prefix)
            return set(re.findall(r"\b([A-H]\d{1,2})\b", lines[0]))
        self.assertEqual(ids_on("Runs by itself: "), set(S.HARNESS_RUNS))
        self.assertEqual(ids_on("Left to a person, "), set(S.LEFT_TO_A_PERSON))
        # D7 is named in the same sentence for its one pause, though the spec lists it among those the harness runs.
        self.assertEqual(ids_on("Pauses for the owner's passkey") - {"D7"}, set(S.PAUSES))
        self.assertIn("H5", S.HARNESS_RUNS)
        for test_id in ("H6", "H7"):
            self.assertIn(test_id, S.LEFT_TO_A_PERSON)


if __name__ == "__main__":
    unittest.main()
