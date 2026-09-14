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

    def test_it_says_what_a5_costs(self):
        self.assertIn("one metered `check_action` unit", self.text)

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


if __name__ == "__main__":
    unittest.main()
