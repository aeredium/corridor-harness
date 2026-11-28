"""
The security reading of pull request 35 (Spec T34), read at b432aaa: what its findings found, held here on the double, one class for each
finding answered by a change.

  Finding 2: where S11 could not read the chain, or on a run resumed past S11, S12 reads the receipt of the approval's operation again —
    and held neither the sender nor the paymaster its UserOperationEvent names, which S11 holds on its own reading. S12 holds both now.
  Finding 3: the approval's operation was judged landed and paid for, and what it approved was never read. S12 reads the ERC-20 Approval
    log in its receipt and holds the owner to the wallet, the spender to the venue contract the trade names and the amount to what the
    swap took — what the Series' D2 says of every trade: "approve(SwapRouter02, exactly the USDC amount of the trade)".
  Finding 4: the pin's row cited a second source nobody on the harness's side had verified, and only a comment said so. The row's own
    string, which `tables.describe` prints, says it now. The source itself is confirmed by nothing here: that check is still owed.

The file is named so that the repository's one command for the suite, `python3 -m unittest discover tests`, reaches it among the first
modules it runs.

Standard library only, and no network: every road answers through corridor_harness.http_request, patched to the double.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerconnect_harness as P  # noqa: E402
import corridor_harness as H  # noqa: E402
import tables as T  # noqa: E402

try:
    from .pathfinder_double import APPROVAL_TOPIC, USDC_ARBITRUM, WETH_ARBITRUM, topic_of, word
    from .test_aerconnect_harness import PathfinderBase
except ImportError:  # run as a top-level module by `unittest discover tests`
    from pathfinder_double import APPROVAL_TOPIC, USDC_ARBITRUM, WETH_ARBITRUM, topic_of, word
    from test_aerconnect_harness import PathfinderBase

ANOTHER = H.checksum_address("0x" + "5e" * 20)  # nobody's address: neither the agent's wallet nor the group-100 paymaster, nor the venue contract
PAYMASTER = H.checksum_address(P.PAYMASTER["arbitrum"])
VENUE = H.checksum_address(P.TRADE["contract_address"])  # the venue contract the trade names: Uniswap v3's SwapRouter02 on Arbitrum, tables.py's
UNLIMITED = 2 ** 256 - 1


class S12HoldsTheSenderAndThePaymasterOfTheApprovalItReadsAgain(PathfinderBase):
    """
    Finding 2. S11 judges every operation's UserOperationEvent: success, the sender the wallet, the paymaster the group-100 paymaster. Where
    S11 never read the chain (the RPC refused it), or the run is resumed at S12, S12 reads the approval's receipt again by the hash the
    Wallet named, and that second reading is the only one the run has: it holds what S11's would have.
    """

    def s11_refused_by_the_rpc(self):
        """A walk whose S11 the RPC refuses once, on the first receipt it asks for: S11 judged no event, and S12 reads both receipts again."""
        self.double.rpc_error_on, self.double.rpc_error_times = "eth_getTransactionReceipt", 1
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.FAIL, s11.line)
        self.assertIn("refused: the arbitrum RPC at https://arb1.arbitrum.io refused eth_getTransactionReceipt", s11.line)
        self.assertNotIn("paymaster", s11.line, "S11 read no receipt, so it judged no event")
        self.assertNotIn("sender", s11.line)
        return runner

    def test_another_paymaster_on_the_approvals_event_fails_s12_where_s11_could_not_read_the_chain(self):
        self.double.approval_paymaster = ANOTHER
        runner = self.s11_refused_by_the_rpc()
        s12 = runner.outcome_of("S12")
        self.assertEqual((s12.outcome, s12.cause), (P.FAIL, P.FAULT), s12.line)
        self.assertIn("the approval's operation: the paymaster is %s, and the group-100 paymaster is %s" % (ANOTHER, PAYMASTER), s12.line)
        self.assertNotIn("the operation's sender is", s12.line, "the sender is the wallet, and nothing is said of it")

    def test_another_sender_on_the_approvals_event_fails_s12_where_s11_could_not_read_the_chain(self):
        self.double.approval_sender = ANOTHER
        runner = self.s11_refused_by_the_rpc()
        s12 = runner.outcome_of("S12")
        self.assertEqual((s12.outcome, s12.cause), (P.FAIL, P.FAULT), s12.line)
        self.assertIn("the approval's operation: the operation's sender is %s, and the wallet is %s" % (ANOTHER, self.agent_of(runner)["walletAddress"]), s12.line)
        self.assertNotIn("the paymaster is", s12.line, "the paymaster is the group-100 paymaster, and nothing is said of it")

    def test_a_run_resumed_at_s12_holds_them_by_the_hashes_run_json_keeps(self):
        """S11 read the chain, said so and failed; a run resumed past it with --from S12 reads the approval's receipt again and says the same."""
        self.double.approval_paymaster = ANOTHER
        first = self.runner()
        for station, title in P.STATIONS[:10]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        s11 = first.run_station(*P.STATIONS[10])
        said = "the approval's operation: the paymaster is %s, and the group-100 paymaster is %s" % (ANOTHER, PAYMASTER)
        self.assertEqual((s11.station, s11.outcome), ("S11", P.FAIL), first.line(s11))
        self.assertIn(said, s11.line)
        runner = self.walk(start_at="S12")
        s12 = runner.outcome_of("S12")
        self.assertEqual((s12.outcome, s12.cause), (P.FAIL, P.FAULT), s12.line)
        self.assertIn(said, s12.line, "S12's own reading holds what S11's held")

    def test_the_wallet_and_the_paymaster_on_the_approvals_event_pass_s12_as_before(self):
        """The guard: an approval sent by the wallet and paid by the group-100 paymaster is read again and nothing is said of either."""
        runner = self.s11_refused_by_the_rpc()
        s12 = runner.outcome_of("S12")
        self.assertEqual(s12.outcome, P.PASS, s12.line)
        self.assertNotIn("the paymaster is", s12.line)
        self.assertNotIn("the operation's sender is", s12.line)


class TheReaderOfWhatAnOperationApproved(unittest.TestCase):
    """Finding 3, the small reader: the ERC-20 Approval logs of a receipt — the token, the owner, the spender and the amount."""

    def test_the_topic_is_erc_20s_approval_as_every_explorer_prints_it(self):
        self.assertEqual(APPROVAL_TOPIC, "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925")
        self.assertEqual(P.APPROVAL_TOPIC, APPROVAL_TOPIC, "the harness derives it from the event's signature, and the double states it")

    def test_an_approval_is_read_and_nothing_else_is_read_as_one(self):
        owner, spender = H.checksum_address("0x" + "a7" * 20), VENUE
        receipt = {"logs": [
            {"address": USDC_ARBITRUM, "topics": [H.TRANSFER_TOPIC, topic_of(owner), topic_of(spender)], "data": "0x" + word(7)},  # a Transfer
            {"address": USDC_ARBITRUM, "topics": [APPROVAL_TOPIC.upper().replace("0X", "0x"), topic_of(owner), topic_of(spender)], "data": "0x" + word(100000)},
            {"address": WETH_ARBITRUM, "topics": [APPROVAL_TOPIC, topic_of(owner), topic_of(ANOTHER)], "data": "0x" + word(UNLIMITED)},
            {"address": WETH_ARBITRUM, "topics": [APPROVAL_TOPIC, topic_of(owner), topic_of(spender), "0x" + word(9)], "data": "0x"},  # ERC-721's, four topics
            {"address": USDC_ARBITRUM, "topics": [APPROVAL_TOPIC, topic_of(owner), topic_of(spender)], "data": "0x"},  # an amount of nothing
        ]}
        self.assertEqual(P.approvals_in(receipt), [
            {"token": H.checksum_address(USDC_ARBITRUM), "owner": owner, "spender": spender, "amount": 100000},
            {"token": H.checksum_address(WETH_ARBITRUM), "owner": owner, "spender": ANOTHER, "amount": UNLIMITED},
            {"token": H.checksum_address(USDC_ARBITRUM), "owner": owner, "spender": spender, "amount": 0},
        ])
        for empty in ({}, {"logs": None}, {"logs": []}):
            self.assertEqual(P.approvals_in(empty), [])


class S12ReadsWhatTheApprovalApproved(PathfinderBase):
    """
    Finding 3. The approval is its own operation with its own receipt, and S11, S12 and S12a judged that receipt for its status, its
    UserOperationEvent and its debit alone: a Wallet that approved another spender than the venue contract, or more than the trade sells,
    passed all three so long as the swap's transfers reconciled. S12 reads the Approval log now, and each of those is a fault it names.
    """

    def failed_at_s12_alone(self, runner):
        """S11 passed — it judges the landing, not what was approved — and S12 failed, a fault; the commission on the swap is read all the same."""
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        s12 = runner.outcome_of("S12")
        self.assertEqual((s12.outcome, s12.cause), (P.FAIL, P.FAULT), s12.line)
        self.assertNotIn("the balances reconcile", s12.line.split("; ")[0], "the problem is said first")
        self.assertEqual(runner.outcome_of("S12a").outcome, P.PASS, self.line_of(runner, "S12a"))
        return s12.line

    def test_the_venue_contract_and_exactly_what_the_swap_took_pass_and_s12_says_what_was_approved(self):
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual(runner.findings, {})
        self.assertIn("; the approval's operation approved the venue contract %s to take 0.1 USDC from the wallet, exactly what the swap took; " % VENUE,
                      self.line_of(runner, "S12"))
        self.assertEqual(T.address("UNISWAP_V3_ARBITRUM"), VENUE, "the venue contract is the one tables.py pins for the trade's venue on its chain")

    def test_another_spender_than_the_venue_contract_fails_s12(self):
        self.double.approval_spender = ANOTHER
        line = self.failed_at_s12_alone(self.walk())
        self.assertIn("the approval's operation: the approval's spender %s is not the venue contract %s" % (ANOTHER, VENUE), line)
        self.assertNotIn("approved the venue contract", line)
        self.assertNotIn("the allowance of", line, "the amount is the trade's, and nothing is said of it")

    def test_an_unlimited_allowance_fails_s12(self):
        self.double.approval_amount = UNLIMITED
        line = self.failed_at_s12_alone(self.walk())
        self.assertIn("the approval's operation: the allowance of %d minor units of USDC (an unlimited allowance) is not the 100000 the swap took" % UNLIMITED, line)
        self.assertNotIn("the approval's spender", line, "the spender is the venue contract, and nothing is said of it")

    def test_an_allowance_of_one_unit_more_than_the_swap_took_fails_s12(self):
        """Series D3: "if the Wallet ever reports one leg on a fresh trade, an allowance was left standing, and that is a failure" — read here on chain."""
        self.double.approval_amount = P.TRADE_RAW + 1
        line = self.failed_at_s12_alone(self.walk())
        self.assertIn("the approval's operation: the allowance of 100001 minor units of USDC is not the 100000 the swap took", line)
        self.assertNotIn("unlimited", line)

    def test_an_approval_of_another_token_fails_s12(self):
        self.double.approval_token = WETH_ARBITRUM
        line = self.failed_at_s12_alone(self.walk())
        self.assertIn("the approval's operation: the Approval is logged by the token %s, and the USDC the trade sells is %s" % (
            H.checksum_address(WETH_ARBITRUM), H.checksum_address(USDC_ARBITRUM)), line)

    def test_a_receipt_that_carries_no_approval_by_the_wallet_fails_s12(self):
        self.double.approval_log = False
        runner = self.walk()
        line = self.failed_at_s12_alone(runner)
        self.assertIn("the approval's operation: its receipt carries no ERC-20 Approval by the wallet %s (0 Approval logs read in it), so what it approved "
                      "could not be read" % self.agent_of(runner)["walletAddress"], line)

    def test_a_run_resumed_at_s12_reads_what_was_approved_by_the_hash_run_json_keeps(self):
        self.double.approval_spender = ANOTHER
        first = self.runner()
        for station, title in P.STATIONS[:11]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        runner = self.walk(start_at="S12")
        s12 = runner.outcome_of("S12")
        self.assertEqual((s12.outcome, s12.cause), (P.FAIL, P.FAULT), s12.line)
        self.assertIn("the approval's operation: the approval's spender %s is not the venue contract %s" % (ANOTHER, VENUE), s12.line)

    def test_a_quote_that_carries_no_approval_is_read_as_before(self):
        """The guard: no approval's operation was sent, so there is no receipt of one to read, and S12 says nothing of one."""
        self.double.needs_approval = False
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertNotIn("approv", self.line_of(runner, "S12"))

    def test_a_wallet_before_w_ops_is_read_as_before(self):
        """The guard: the one operation of a Wallet that lists none is read exactly as it always was, in the sentences it always had."""
        self.double.operations = False
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertNotIn("approv", self.line_of(runner, "S12"))


class ThePinsRowSaysWhoConfirmedItsSecondSource(unittest.TestCase):
    """
    Finding 4. The row of DELEGATION_IMPLEMENTATION_ARBITRUM cites a second source — the access platform's PIN.md and a read of the chain —
    that neither the builder of Spec T34 nor the security reading verified, and said so in a comment alone: `tables.describe` prints the
    row, and the row stopped at the citation. The row's own string now says what it is: recorded as the spec states it, confirmed by no
    one on the harness's side as of its date, with what is weak in it and what is still owed. Nothing here confirms the source itself.
    """
    KEY = "DELEGATION_IMPLEMENTATION_ARBITRUM"
    CITED = "eth_getCode at this address through arb1.arbitrum.io on 27 November 2026 answered 3,721 bytes"
    SAID = (" — the whole of that second source recorded as Spec T34 states it and, as of 28 November 2026, confirmed by no one who has worked on this "
            "repository: the builder who carried Spec T34 out, the security reading of pull request 35 and the repair that answered that reading each read "
            "neither PIN.md nor the chain; the reading of 27 November records a byte count and no hash of the code it was answered, and the match byte "
            "for byte is of prepared bytecode; still owed, by someone who can read PIN.md and the chain: the keccak256 of the code at this address held "
            "against the 0x1c26…6e02 above, and who checked and when recorded here")

    def test_the_rows_own_string_says_that_no_one_on_the_harnesss_side_confirmed_it(self):
        source = T.source(self.KEY)
        self.assertTrue(source.endswith(self.CITED + self.SAID), source)
        self.assertEqual(source.count("confirmed by no one who has worked on this repository"), 1)

    def test_what_describe_prints_carries_it_and_not_the_comment_alone(self):
        printed = T.describe(self.KEY)
        self.assertTrue(printed.endswith(self.SAID + ")"), printed)
        for words in ("recorded as Spec T34 states it", "as of 28 November 2026", "a byte count and no hash of the code", "is of prepared bytecode", "still owed"):
            self.assertIn(words, printed)

    def test_the_row_claims_no_check_that_nobody_made(self):
        source = T.source(self.KEY)
        cited, said = source.split(" — the whole of that second source ")
        for words in ("confirmed by", "checked by", "verified by"):
            self.assertNotIn(words, cited, "the citation names no one who checked it")
        self.assertNotIn("checked by", said)
        self.assertNotIn("verified by", said)
        self.assertEqual(said.count("confirmed by"), 1, "the one thing said of confirming it is that no one has")
        self.assertIn("keccak256 0x1c2695858cfcc5bfd49f48b8892f30c3a9e2e7f53357b47ed0cf7b6caee96e02", cited, "the hash the owed check is to be held against is the row's own")

    def test_the_pin_itself_is_as_it_was(self):
        self.assertEqual(T.address(self.KEY), "0x0562346e1291fd9B922991A249FaaBD0bFEa325f")
        self.assertEqual(list(T.PINNED_FROM_PRODUCTION), [self.KEY])
        self.assertEqual(T.PATHFINDER_LIST[-1], self.KEY)


if __name__ == "__main__":
    unittest.main()
