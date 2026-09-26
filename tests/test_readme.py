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

    def test_it_says_the_harness_consents_its_own_agents(self):
        """Spec T21: the README names the customer, the two files, the seat and its SQL, the wire, the book, the sentences and the record."""
        import corridor_consent as C
        section = self.text.split("## The consent", 1)[1].split("\n## ", 1)[0]
        for words in ("no browser, no link, no listener, no hand", "`<tester> (harness)`", "`harness+<tester>@aeredium.io`", "`[a-z0-9-]+`",
                      "`~/.corridor-harness/<tester>/passkey.json`", "`~/.corridor-harness/<tester>/customer.json`",
                      "*signed up as the harness's own customer <id>; seat it with tools/harness_seat.sh <id>*",
                      "BEFORE an assertion is sent and never resent", "There is no `--fresh`",
                      "by customer id, never by email, never by the harness, never by the desk's page", "bash tools/harness_seat.sh <customer-id>",
                      "`ec2-user@3.231.26.5`", "`/etc/aer-connector/aer-connector.env`", "`psql -v customer_id=<id>`", "`:'customer_id'`",
                      "^harness\\+[a-z0-9-]+@aeredium\\.io$", "ON CONFLICT (customer_id) WHERE state IN ('pending', 'trialing', 'active')",
                      "WHERE subscriptions.state <> 'active'", "'subscription_trial_started', 0,", "'harness:' || :'customer_id' || ':'",
                      "It never writes `state active`", "Solo seats three agents",
                      "`GET` it WITHOUT following redirects and read the consent id from `Location`", "`GET /v1/consent/:id?connect=1`",
                      "`POST /finish {connectionId, rank: the role's defaultRank}`", "`POST /finish {agentId}`", "`AGENT_ALREADY_CONNECTED` is never met",
                      "*consented <tester>-<label> as the harness's own customer with its stored passkey; agent <id>, rank <label>; tokens stored*",
                      "| `perTxUsd` | 20 | 20 |", "| `dailyUsd` | 100 | 100 |", "| `holdAboveUsd` | 50 | 50 |",
                      "**The Trader's list opens empty, not as the spec's words have it.**", "`requireAgentWhitelistPayableDestinations`",
                      "`~/.aer360-harness/harness-holdings/funding-wallet.json`", "`{address, chain, keyId, readAt}`",
                      "*the harness is not seated: run tools/harness_seat.sh <customer-id> on the box, then rerun*",
                      "*the harness's passkey counter is behind the connector's: the passkey file was not saved after a sign-in; a new tester name is a new customer*",
                      "*no wallet address of the harness's own: run aer360_harness.py first (S5 births the funding wallet and writes it down)*",
                      "A refusal is never told as an outage", "`pem`, `signature`, `cookie`, `set-cookie`, `csrfToken`, `code`, `handle` and `response`",
                      "redacted to their last four characters", "python3 corridor_harness.py --tester alice --series A"):
            self.assertIn(words, section, words)
        self.assertEqual(section.count("Consent link for alice-trader:"), 1, "the old link is named once, as history")
        self.assertIn(C.SEAT_SENTENCE % ("", "tools/harness_seat.sh", "<customer-id>"), section)
        self.assertIn(C.COUNTER_SENTENCE, section)
        self.assertIn(C.NO_WALLET_SENTENCE, section)
        self.assertIn("- `corridor_consent.py` — the harness's own customer and its consent, by software (Spec T21, 26 September 2026)", self.text)
        self.assertIn("- `tools/harness_seat.sh` — the operator's one command", self.text)
        estate = self.text.split("## The estate harness", 1)[1]
        self.assertIn("**S5 writes the funding wallet down for the corridor harness (Spec T21, 26 September 2026).**", estate)

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
