"""
Every address in aer360_tables.py is a valid checksummed EVM address and none appears in the
corridor's tables.py; the one venue address S11 sends on purpose is read from the corridor's table
at run time and is never in the harness's own (Spec T7).
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_tables as T  # noqa: E402
import tables as corridor  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TheTables(unittest.TestCase):
    def test_every_pinned_address_is_a_checksummed_evm_address(self):
        for key, row in T.PINNED.items():
            self.assertRegex(row.address, r"^0x[0-9a-fA-F]{40}$", key)
            self.assertTrue(T.is_checksummed(row.address), "%s does not spell its EIP-55 checksum" % key)
            self.assertTrue(row.what)
            self.assertTrue(row.label)

    def test_no_pinned_address_is_the_corridors(self):
        ours = {row.address.lower() for row in T.PINNED.values()}
        theirs = set(T.corridor_addresses())
        self.assertEqual(ours & theirs, set())
        for row in corridor.PINNED.values():
            self.assertFalse(T.is_pinned(row.address), row.what)

    def test_the_addresses_are_derived_from_the_seed_and_change_with_it(self):
        for key, row in T.PINNED.items():
            self.assertEqual(T.derive_address(row.label), row.address, key)
        self.assertNotEqual(T.derive_address("Northwind Supplies/ethereum", seed="another seed"), T.address("NORTHWIND_ETHEREUM"))
        self.assertEqual(len({row.address for row in T.PINNED.values()}), len(T.PINNED), "every label derives a different address")

    def test_the_source_file_holds_no_literal_address(self):
        """Nothing here was typed: no forty-hex literal lives in the file, so none can be a real address mistyped."""
        with open(os.path.join(ROOT, "aer360_tables.py"), "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertEqual(re.findall(r"0x[0-9a-fA-F]{40}", text), [])

    def test_the_venue_probe_reads_the_corridors_table_at_run_time_and_is_never_ours(self):
        venue = T.venue_address_for_probe()
        self.assertEqual(venue["address"], corridor.address("UNISWAP_V3_ETHEREUM"))
        self.assertEqual(venue["what"], "Uniswap v3 SwapRouter02 on Ethereum")
        self.assertFalse(T.is_pinned(venue["address"]))
        with open(os.path.join(ROOT, "aer360_tables.py"), "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn(venue["address"].lower(), text.lower())

    def test_a_wrong_checksum_names_the_same_bytes_and_fails_the_check(self):
        good = T.address("CHECKSUM_PROBE_ETHEREUM")
        broken = T.wrong_checksum(good)
        self.assertNotEqual(good, broken)
        self.assertEqual(good.lower(), broken.lower())
        self.assertFalse(T.is_checksummed(broken))
        self.assertTrue(T.is_checksummed(good))

    def test_six_unlisted_destinations_are_pinned_for_the_wait_and_the_first_is_the_named_one(self):
        self.assertEqual(len(T.UNLISTED_KEYS), 6)
        self.assertEqual(T.UNLISTED_KEYS[0], "UNLISTED_ETHEREUM")
        for key in T.UNLISTED_KEYS:
            self.assertIn(key, T.PINNED)
            self.assertTrue(T.is_checksummed(T.address(key)))
        self.assertEqual(len({T.address(k) for k in T.UNLISTED_KEYS}), 6)

    def test_the_payee_chain_and_the_payees(self):
        self.assertEqual(T.PAYEE_CHAIN, "ethereum")
        self.assertEqual(T.C9_NETWORK_CHOICE, "Ethereum")
        self.assertEqual([p["name"] for p in T.PAYEES], ["Northwind Supplies", "Contoso Legal"])
        for p in T.PAYEES:
            self.assertIn(p["key"], T.PINNED)
            self.assertEqual(p["chain"], T.PAYEE_CHAIN)
        with self.assertRaises(KeyError):
            T.address("NOT_PINNED")

    def test_minor_units_are_string_arithmetic(self):
        self.assertEqual(T.minor_units("1250.00", 6), "1250000000")
        self.assertEqual(T.minor_units("4999.99", 6), "4999990000")
        self.assertEqual(T.minor_units("0.07", 2), "7")
        self.assertEqual(T.minor_units("12000", 6), "12000000000")
        with self.assertRaises(ValueError):
            T.minor_units("1.2345678", 6)
        with self.assertRaises(ValueError):
            T.minor_units("-1", 6)
        with self.assertRaises(ValueError):
            T.minor_units("1e3", 6)


if __name__ == "__main__":
    unittest.main()
