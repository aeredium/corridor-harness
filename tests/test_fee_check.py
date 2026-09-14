"""The fee check finds the five-basis-point leg to the fee address and fails when it is off by one unit (Spec T1 §11)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import tables as T  # noqa: E402

WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
ROUTER = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
POOL = "0x2222222222222222222222222222222222222222"
WALLET = "0x1111111111111111111111111111111111111111"
FEE = T.address("FEE_ADDRESS")
GROSS = 1_987_654_321_012_345  # wei of WETH the pool paid the router
RIGHT_FEE = GROSS * 5 // 10000  # 993_827_160_506


def receipt(fee_amount, delivered=None):
    delivered = GROSS - fee_amount if delivered is None else delivered
    return {"status": "0x1", "logs": [
        {"address": USDC, "topics": [h.TRANSFER_TOPIC, h.pad_topic(WALLET), h.pad_topic(POOL)], "data": hex(5_000_000), "logIndex": "0x0"},
        {"address": WETH, "topics": [h.TRANSFER_TOPIC, h.pad_topic(POOL), h.pad_topic(ROUTER)], "data": hex(GROSS), "logIndex": "0x1"},
        {"address": WETH, "topics": [h.TRANSFER_TOPIC, h.pad_topic(ROUTER), h.pad_topic(FEE)], "data": hex(fee_amount), "logIndex": "0x2"},
        {"address": WETH, "topics": [h.TRANSFER_TOPIC, h.pad_topic(ROUTER), h.pad_topic(WALLET)], "data": hex(delivered), "logIndex": "0x3"},
    ]}


class FeeCheckTest(unittest.TestCase):
    def test_finds_the_five_basis_point_leg(self):
        check = h.fee_check(h.transfers_in(receipt(RIGHT_FEE)), FEE, WALLET, router=ROUTER)
        self.assertTrue(check["ok"], check)
        self.assertEqual(check["found"], RIGHT_FEE)
        self.assertEqual(check["expected"], RIGHT_FEE)
        self.assertEqual(check["token"], WETH)
        self.assertEqual(check["gross"], GROSS)
        self.assertEqual(check["delivered"], GROSS - RIGHT_FEE)
        self.assertEqual(check["bps"], 5)

    def test_one_unit_over_fails(self):
        check = h.fee_check(h.transfers_in(receipt(RIGHT_FEE + 1)), FEE, WALLET, router=ROUTER)
        self.assertFalse(check["ok"])
        self.assertEqual(check["found"], RIGHT_FEE + 1)
        self.assertEqual(check["expected"], RIGHT_FEE)
        self.assertIn("five basis points", check["reason"])

    def test_one_unit_short_fails(self):
        check = h.fee_check(h.transfers_in(receipt(RIGHT_FEE - 1)), FEE, WALLET, router=ROUTER)
        self.assertFalse(check["ok"])
        self.assertEqual(check["found"], RIGHT_FEE - 1)
        self.assertEqual(check["expected"], RIGHT_FEE)

    def test_without_the_router_the_gross_is_delivered_plus_fee(self):
        check = h.fee_check(h.transfers_in(receipt(RIGHT_FEE)), FEE, WALLET)
        self.assertTrue(check["ok"])
        self.assertEqual(check["gross_read_from"], "delivered plus fee")
        self.assertFalse(h.fee_check(h.transfers_in(receipt(RIGHT_FEE + 1)), FEE, WALLET)["ok"])

    def test_no_fee_leg_is_a_finding_not_a_crash(self):
        no_fee = {"status": "0x1", "logs": receipt(RIGHT_FEE)["logs"][:2]}
        check = h.fee_check(h.transfers_in(no_fee), FEE, WALLET, router=ROUTER)
        self.assertFalse(check["ok"])
        self.assertIsNone(check["found"])
        self.assertIn("no transfer to the fee address", check["reason"])

    def test_the_series_figure_read_aloud(self):
        self.assertEqual(h.format_units(RIGHT_FEE, 18), "0.000000993827160506")
        self.assertEqual(h.format_units(1_000_000, 6), "1")
        self.assertEqual(h.format_units(1_234_500, 6), "1.2345")


if __name__ == "__main__":
    unittest.main()
