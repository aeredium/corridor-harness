"""
The security reading of pull request 35 (Spec T34), read at b432aaa: what its findings found, held here on the double, one class for each
finding answered by a change.

  Finding 2: where S11 could not read the chain, or on a run resumed past S11, S12 reads the receipt of the approval's operation again —
    and held neither the sender nor the paymaster its UserOperationEvent names, which S11 holds on its own reading. S12 holds both now.

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

try:
    from .test_aerconnect_harness import PathfinderBase
except ImportError:  # run as a top-level module by `unittest discover tests`
    from test_aerconnect_harness import PathfinderBase

ANOTHER = H.checksum_address("0x" + "5e" * 20)  # nobody's address: neither the agent's wallet nor the group-100 paymaster
PAYMASTER = H.checksum_address(P.PAYMASTER["arbitrum"])


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


if __name__ == "__main__":
    unittest.main()
