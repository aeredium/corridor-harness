"""--dry produces every call for Series A to E, in order, with no network (Spec T1 §8, §11)."""
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402
import tables as T  # noqa: E402


def no_network(*args, **kwargs):
    raise AssertionError("the dry run reached for the network: %r" % (args[:2],))


class DryRunTest(unittest.TestCase):
    def setUp(self):
        self._http = h.http_request
        h.http_request = no_network

    def tearDown(self):
        h.http_request = self._http

    def test_every_call_for_series_a_to_e_in_order(self):
        lines = h.dry_lines(["A", "B", "C", "D", "E"])
        ids_seen = []
        for line in lines:
            test_id = line.split(" — ", 1)[0]
            if test_id not in ids_seen:
                ids_seen.append(test_id)
        expected = [t.id for t in S.tests_in(["A", "B", "C", "D", "E"])]
        self.assertEqual(ids_seen, expected, "every test of A to E appears once, in Series order")
        # C1 walks the corridor in the corridor's order
        c1 = [l for l in lines if l.startswith("C1 — tools/call")]
        self.assertEqual([l.split()[3] for l in c1], ["police.check_action", "wallet.build_transaction", "wallet.submit_transaction"])
        self.assertIn('"police_receipt": "<receipt from police.check_action>"', c1[1])
        self.assertIn('"ticket_id": "<ticket from wallet.build_transaction>"', c1[2])
        # C2 is refused at pre-flight, so the build is not reached
        c2 = [l for l in lines if l.startswith("C2 — ")]
        self.assertTrue(any("police.check_action" in l and T.address("DEAD_ADDRESS") in l for l in c2))
        self.assertFalse(any("wallet.build_transaction" in l for l in c2))
        # C3 builds without a receipt and never asks Police first
        c3 = [l for l in lines if l.startswith("C3 — tools/call")]
        self.assertEqual(len(c3), 1)
        self.assertIn("wallet.build_transaction", c3[0])
        self.assertNotIn("police_receipt", c3[0])
        # D2 names the venue, the asset bought and the pinned contract
        d2 = [l for l in lines if l.startswith("D2 — tools/call police.check_action")][0]
        self.assertIn('"venue": "uniswap_v3"', d2)
        self.assertIn('"to_asset": "WETH"', d2)
        self.assertIn(T.address("UNISWAP_V3_ARBITRUM"), d2)
        self.assertIn('"amount_usd": 5', d2)
        # D8 leaves contract_address empty for best_direct
        d8 = [l for l in lines if l.startswith("D8 — tools/call police.check_action")][0]
        self.assertIn('"venue": "best_direct"', d8)
        self.assertIn('"contract_address": ""', d8)
        # E1 crosses by bridge_stable to base
        e1 = [l for l in lines if l.startswith("E1 — tools/call police.check_action")][0]
        self.assertIn('"action": "bridge_stable"', e1)
        self.assertIn('"to_chain": "base"', e1)
        # every pause is printed, with the wallet_status that follows it
        self.assertTrue(any(l.startswith("C5 — [pause]") for l in lines))
        self.assertTrue(any(l.startswith("C5 — tools/call wallet.wallet_status") for l in lines))
        self.assertTrue(any(l.startswith("B3 — [pause]") for l in lines))
        # A1 is plain HTTP
        self.assertTrue(any(l.startswith("A1 — POST https://mcppro.aeredium.io/mcp (no bearer) → expect 401") for l in lines))
        # C8 and E3 are printed in a dry run even though a live run may skip them
        self.assertTrue(any(l.startswith("C8 — tools/call") for l in lines))
        self.assertTrue(any(l.startswith("E3 — tools/call") for l in lines))
        self.assertFalse(any("STOP" in l for l in lines))

    def test_the_hash_is_read_from_the_wallet_and_never_from_can_sign(self):
        """Spec T2 §1: MCP Police carries no tool called can_sign, so no dry line names one."""
        lines = h.dry_lines(["A", "B", "C", "D", "E"])
        self.assertEqual([l for l in lines if "can_sign" in l], [])
        series_a = [l for l in lines if l[:2] in ("A1", "A2", "A3", "A4", "A5", "A6")]
        self.assertTrue(any("wallet.wallet_status" in l for l in series_a),
                        "Series A reads the hash from the Wallet")
        # every pause that reads a hash reads it from the Wallet
        pauses = [l for l in lines if "confirm pact.policy_hash" in l]
        self.assertTrue(pauses)
        for line in pauses:
            self.assertIn("tools/call wallet.wallet_status", line)

    def test_a5_asks_police_exactly_once(self):
        """Spec T2 §2: A5 reads the Wallet's hash, then makes ONE check_action, and compares hashes."""
        a5 = [l for l in h.dry_lines(["A"]) if l.startswith("A5 — ")]
        self.assertEqual(len([l for l in a5 if "police.check_action" in l]), 1, a5)
        self.assertEqual(len([l for l in a5 if "wallet.wallet_status" in l]), 1, a5)
        self.assertTrue(any("pact.policy_hash" in l for l in a5), a5)
        self.assertTrue(any("judged.policy_hash" in l and "whatever the verdict" in l for l in a5), a5)

    def test_a4_reads_the_chain_and_the_tokens_as_the_product_stands(self):
        """Spec T2 §4: wallet_status names the wallet's own chain; the tokens come from the RPC."""
        a4 = [l for l in h.dry_lines(["A"]) if l.startswith("A4 — ")]
        self.assertTrue(any("wallet.wallet_status" in l and "ethereum, arbitrum, base" in l for l in a4), a4)
        self.assertTrue(any("Spec 49" in l for l in a4), a4)
        self.assertFalse(any('expect words ["ethereum", "arbitrum", "base"]' in l for l in a4),
                         "A4 no longer demands three rails from a Wallet that names one chain")

    def test_a6_counts_the_fee_and_not_the_phrase_basis_points(self):
        """Spec T2 §3: the pin is the fee's own words."""
        a6 = [l for l in h.dry_lines(["A"]) if l.startswith("A6 — ")]
        self.assertEqual(len([l for l in a6 if "(expect 0)" in l]), 3, a6)
        for line in a6:
            if "(expect 0)" in line:
                self.assertIn("sweepTokenWithFee", line)
                self.assertIn("feeRecipient", line)
                self.assertNotIn('"basis points"', line)

    def test_no_amount_above_the_series_figures(self):
        for test in S.TESTS:
            for step in test.steps:
                if isinstance(step, S.Walk):
                    self.assertIsNotNone(test.figure_usd, "%s moves money but names no figure" % test.id)
                    self.assertLessEqual(step.action.amount_usd, test.figure_usd, test.id)

    def test_main_dry_prints_and_sends_nothing(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = h.main(["--dry", "--series", "A", "C"])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("Dry run: nothing was sent.", text)
        self.assertIn("C7 — tools/call police.check_action", text)
        self.assertNotIn("D1 —", text)

    def test_from_resumes_at_a_test_and_keeps_series_a(self):
        lines = h.dry_lines(["A", "C", "D"], start_at="D7")
        ids_seen = []
        for line in lines:
            test_id = line.split(" — ", 1)[0]
            if test_id not in ids_seen:
                ids_seen.append(test_id)
        self.assertEqual(ids_seen[:6], ["A1", "A2", "A3", "A4", "A5", "A6"])
        self.assertNotIn("C1", ids_seen)
        self.assertNotIn("D6", ids_seen)
        self.assertIn("D7", ids_seen)
        self.assertIn("D16", ids_seen)


if __name__ == "__main__":
    unittest.main()
