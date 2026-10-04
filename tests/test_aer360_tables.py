"""
Every address in aer360_tables.py is a valid checksummed EVM address and none appears in the
corridor's tables.py; the one venue address S11 sends on purpose is read from the corridor's table
at run time and is never in the harness's own (Spec T7). Since Spec T18 the chain is one word in one
place, `arbitrum`, the venue probe sends the corridor's Arbitrum row, and the pinned keys keep the
names they were first minted under, so no address moved.

Spec T24 (3 October 2026; the owner: "No more than $1." and "The money should always be paid to my MetaMask address. Always."): the law of a
real chain — on a chain not in TESTNET_CHAIN_NAMES no payment may go to a derived address, every one goes to the owner's own wallet read from
payee.env, the book's total may not exceed 1000000 minor units of USDC, and payee.env absent stops S6 and S7 with the spec's sentence. Each
test of the law was red on main.
"""
import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
import tables as corridor  # noqa: E402
from tests.test_aer360_double import EstateDouble, OWNER_WALLET_FOR_TESTS, file_the_owner_payee, runner_on  # noqa: E402

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
        self.assertEqual(venue["key"], T.UNISWAP_V3_ARBITRUM, "Spec T18 §3: the probe moves with the payees")
        self.assertEqual(venue["address"], corridor.address("UNISWAP_V3_ARBITRUM"))
        self.assertEqual(venue["what"], "Uniswap v3 SwapRouter02 on Arbitrum")
        self.assertEqual(T.venue_address_for_probe("UNISWAP_V3_ETHEREUM")["what"], "Uniswap v3 SwapRouter02 on Ethereum", "the Ethereum row is still readable by name")
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
        """Spec T18 §1: the chain is one word in one place; no row of the payees copies it, and the pinned keys keep their minted names."""
        self.assertEqual(T.PAYEE_CHAIN, "arbitrum")
        self.assertEqual(T.C9_NETWORK_CHOICE, "Arbitrum One")
        self.assertEqual([p["name"] for p in T.PAYEES], ["Northwind Supplies", "Contoso Legal"])
        self.assertEqual([p["key"] for p in T.PAYEES], ["NORTHWIND_ETHEREUM", "CONTOSO_ETHEREUM"], "the keys record where the labels were first minted")
        for p in T.PAYEES:
            self.assertIn(p["key"], T.PINNED)
            self.assertNotIn("chain", p, "the chain is read from PAYEE_CHAIN at run time, never copied into a row")
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


# The spec's sentences, word for word (SPEC.md §1 and §2), held here so no edit can move a word unnoticed.
THE_STOP_SENTENCE = ("the owner's payee address is not filed at ~/.aer360-harness/payee.env (OWNER_PAYEE_ADDRESS); "
                     "on arbitrum the harness pays only the owner's own wallet; nothing was sent")
THE_HOLD_SENTENCE = "the one-off destination is the owner's wallet, already paid by this estate, so Spec 69's hold is not provable this run"


def pays_to(runner, station="S7"):
    """
    Every (invoiceRef, destination) a POST /v1/sets or /v1/sets/review body of the station names — the one-off's address, or `<payee id>` for a
    payeeAddressId. Harness Holdings' payments carry HH- references; the Treasury's shortfall payment to Holdings' own wallet carries HT-.
    """
    out = []
    for call in runner.calls:
        if call.station != station or call.route not in ("POST /v1/sets", "POST /v1/sets/review") or not isinstance(call.sent, dict):
            continue
        for row in call.sent.get("pays") or []:
            out.append((str(row.get("invoiceRef") or ""), (row.get("oneOff") or {}).get("address") or ("<payee %s>" % row.get("payeeAddressId"))))
    return out


class TheLawOfTheRealChain(unittest.TestCase):
    """Spec T24 §5: the guards. `arbitrum`, the payments' chain since Spec T18, is not one of TESTNET_CHAIN_NAMES, so the law is in force on the double."""

    def test_the_payments_chain_is_a_real_one_and_the_testnet_is_named(self):
        self.assertEqual(T.TESTNET_CHAIN_NAMES, ("aeredium-testnet", "aeredium"))
        self.assertNotIn(T.PAYEE_CHAIN, T.TESTNET_CHAIN_NAMES)
        self.assertTrue(T.pays_a_real_chain())
        self.assertTrue(T.pays_a_real_chain("arbitrum") and T.pays_a_real_chain("ethereum"))
        self.assertFalse(T.pays_a_real_chain("aeredium-testnet") or T.pays_a_real_chain("aeredium") or T.pays_a_real_chain("AEREDIUM"))
        self.assertEqual((T.is_testnet("aeredium"), T.is_testnet("arbitrum"), T.is_testnet(None)), (True, False, False))
        self.assertEqual((T.payee_words(), T.payee_words("aeredium-testnet")), ("the owner's wallet", "a test address derived from the seed"))

    def test_the_books_total_on_a_real_chain_may_not_exceed_one_dollar(self):
        self.assertEqual(T.ONE_DOLLAR_MINOR, 1000000)
        for chain in ("arbitrum", "ethereum", "base", "polygon", T.PAYEE_CHAIN):
            book = A.payments_for(chain)
            self.assertLessEqual(A.payments_total_minor(book), T.ONE_DOLLAR_MINOR, chain)
            self.assertLessEqual(sum(int(p.amount_minor) for p in book), 1000000, chain)
        self.assertLessEqual(A.payments_total_minor(), T.ONE_DOLLAR_MINOR, "the book in force")
        self.assertEqual(A.payments_total_minor(), 1000000, "the owner's dollar, to the cent: 0.50 + 0.01 + 0.49")
        self.assertGreater(A.payments_total_minor(A.PAYMENTS_ON_THE_TESTNET), T.ONE_DOLLAR_MINOR, "the testnet's figures are not under the law, and are never in force on a real chain")
        for chain in T.TESTNET_CHAIN_NAMES:
            self.assertIs(A.payments_for(chain), A.PAYMENTS_ON_THE_TESTNET)

    def test_the_owners_file_is_checked_and_a_checksum_that_does_not_spell_itself_is_refused(self):
        good = OWNER_WALLET_FOR_TESTS
        self.assertTrue(T.is_checksummed(good))
        self.assertEqual(T.owner_payee_of("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % good), (good, None))
        self.assertEqual(T.owner_payee_of("# a comment\nexport OWNER_PAYEE_ADDRESS='%s'\nOWNER_PAYEE_CHAIN=\"Arbitrum\"\n" % good), (good, None), "quotes and export, as a shell file")
        self.assertEqual(T.owner_payee_of("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=ethereum\n" % good, "ethereum"), (good, None), "the chain the test moves to")
        cases = [
            ("", "names no OWNER_PAYEE_ADDRESS"),
            ("OWNER_PAYEE_CHAIN=arbitrum\n", "names no OWNER_PAYEE_ADDRESS"),
            ("OWNER_PAYEE_ADDRESS=0x1234\nOWNER_PAYEE_CHAIN=arbitrum\n", "OWNER_PAYEE_ADDRESS is not 0x and forty hexadecimal characters"),
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % good.lower(), "OWNER_PAYEE_ADDRESS does not spell its own EIP-55 checksum (copy the address from the wallet again)"),
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % T.wrong_checksum(good), "OWNER_PAYEE_ADDRESS does not spell its own EIP-55 checksum (copy the address from the wallet again)"),
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % T.address("NORTHWIND_ETHEREUM"), "OWNER_PAYEE_ADDRESS is one of the harness's own derived test addresses, which no key stands behind"),
            ("OWNER_PAYEE_ADDRESS=%s\n" % good, "names no OWNER_PAYEE_CHAIN (the payments are made on arbitrum)"),
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=ethereum\n" % good, "OWNER_PAYEE_CHAIN is 'ethereum', not arbitrum, the chain the payments are made on"),
        ]
        for text, wrong in cases:
            self.assertEqual(T.owner_payee_of(text), (None, wrong), text)
        self.assertEqual(T.NO_OWNER_PAYEE_SENTENCE % T.PAYEE_CHAIN, THE_STOP_SENTENCE)
        self.assertEqual(T.ONE_OFF_ALREADY_PAID_SENTENCE, THE_HOLD_SENTENCE)
        self.assertEqual((T.PAYEE_ENV_FILE, T.OWNER_PAYEE_ADDRESS_KEY, T.OWNER_PAYEE_CHAIN_KEY), ("payee.env", "OWNER_PAYEE_ADDRESS", "OWNER_PAYEE_CHAIN"))
        self.assertEqual(T.OWNER_PAYEE_PLACEHOLDER, "<OWNER_PAYEE_ADDRESS from ~/.aer360-harness/payee.env>")

    @unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
    def test_on_a_real_chain_no_payment_goes_to_a_derived_address_and_the_run_moves_no_more_than_one_dollar(self):
        double = EstateDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)
        # every payment of Harness Holdings — S7's three, and S7a's review of the set of three — names the owner's wallet, never a derived address;
        # the Treasury's one payment (HT-) names Holdings' own wallet, as T14 §2 has it
        rows = pays_to(runner)
        holdings_rows = [(ref, d) for ref, d in rows if ref.startswith("HH-")]
        treasury_rows = [(ref, d) for ref, d in rows if ref.startswith("HT-")]
        self.assertEqual(len(holdings_rows), 10, "S7a's three; P1's review twice — refused for want of gas, cured, asked again (Spec T26) — and its creation; P2's and P3's review and creation")
        self.assertEqual(len(treasury_rows), 3, "the Treasury's review — refused for want of gas, cured, asked again (Spec T26) — and its creation")
        self.assertEqual(len(rows), len(holdings_rows) + len(treasury_rows))
        for ref, destination in holdings_rows:
            address = double.addresses[destination[len("<payee "):-1]]["address"] if destination.startswith("<payee ") else destination
            self.assertEqual(address.lower(), OWNER_WALLET_FOR_TESTS.lower(), (ref, destination))
            self.assertFalse(T.is_pinned(address), "a derived address was named on a real chain: %s" % destination)
        self.assertEqual({d.lower() for _, d in treasury_rows}, {double.source_account.lower()})
        instructions = [i for s in double.sets.values() for i in s["instructions"]]
        self.assertEqual({i["address"] for i in instructions}, {OWNER_WALLET_FOR_TESTS.lower()})
        self.assertFalse(any(T.is_pinned(i["address"]) for i in instructions))
        self.assertEqual(sum(int(i["amountMinor"]) for i in instructions), 1000000, "the run moved one dollar from Harness Holdings, and no more")
        self.assertLessEqual(sum(int(i["amountMinor"]) for i in instructions), T.ONE_DOLLAR_MINOR)
        treasury_instructions = [i for s in double.treasury.sets.values() for i in s["instructions"]]
        self.assertLessEqual(sum(int(i["amountMinor"]) for i in treasury_instructions), T.ONE_DOLLAR_MINOR, "the Treasury's shortfall payment is computed from the one-dollar book")
        self.assertEqual({i["address"] for i in treasury_instructions}, {double.source_account.lower()}, "the Treasury pays Holdings' own wallet (Spec T14 §2)")
        self.assertEqual(double.chain.balance_of(OWNER_WALLET_FOR_TESTS), 1000000)
        for key in T.PINNED:
            self.assertEqual(double.chain.balance_of(T.address(key)), 0, key)
        # the payees S6 whitelisted are at the owner's wallet too, so a later run resolving by (name, chain) finds nothing derived to pay
        self.assertEqual({a["address"] for a in double.addresses.values() if a["payeeId"] in {p["id"] for p in double.payees.values() if p["displayName"] in ("Northwind Supplies", "Contoso Legal")}},
                         {OWNER_WALLET_FOR_TESTS.lower()})

    @unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
    def test_payee_env_absent_s7_stops_with_the_sentence_and_nothing_was_sent(self):
        double = EstateDouble()
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link(), payee_env=False)
        outcomes = {o.station: o for o in runner.run()}
        o6, o7 = outcomes["S6"], outcomes["S7"]
        self.assertEqual(o7.outcome, H.FAILED_PREREQUISITE, o7.line)
        self.assertTrue(o7.line.endswith(THE_STOP_SENTENCE), o7.line)
        self.assertTrue(o7.line.startswith("payments: %s — " % H.OWNER_PAYEE_NOT_FILED), o7.line)
        self.assertIn("before: Harness Holdings holds US$0.00 of USDC on arbitrum", o7.line, "the money before is read and reported, as T14 reads it before the credit step")
        self.assertEqual(o6.outcome, H.FAILED_PREREQUISITE, o6.line)
        self.assertEqual(o6.line, "payees: %s — %s" % (H.OWNER_PAYEE_NOT_FILED, THE_STOP_SENTENCE))
        self.assertEqual(pays_to(runner), [], "nothing was reviewed, created or sent")
        self.assertEqual(double.sets, {}, "no run of Harness Holdings")
        self.assertEqual(double.treasury.sets, {}, "the stop comes before the Treasury pays")
        self.assertEqual(double.chain.transfers, [])
        self.assertEqual(double.platform.requests, [], "no gas was credited")
        self.assertEqual([p["displayName"] for p in double.payees.values() if p["displayName"] in ("Northwind Supplies", "Contoso Legal")], [], "no payee was made at a derived address")
        self.assertFalse(any(T.is_pinned(a["address"]) and a["whitelistStatus"] != "proposed" for a in double.addresses.values()), "S11's probe payee is the one row the estate holds, proposed and never paid")
        self.assertEqual([c.route for c in runner.calls if c.station == "S6"], [], "S6 asked the estate nothing")


if __name__ == "__main__":
    unittest.main()
