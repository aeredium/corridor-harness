"""
Spec T24 (3 October 2026, from the owner's two rulings of that night: "No more than $1." and "The money should always be paid to my MetaMask
address. Always."): on a real chain the estate harness pays the owner's own wallet, and the book's payments total no more than one dollar.

The finding, not re-diagnosed: every payee address `aer360_tables.py` derives from its seed has no key behind it — harmless on the AEREDIUM
testnet, lost money since Spec T18 moved PAYEE_CHAIN to `arbitrum`; the run of 28 September paid US$18.24 to addresses nobody can spend from.

The double is the estate at `arbitrum` (tests/test_aer360_double.py), a real chain, so the law of Spec T24 is in force against it: the tests
file the owner's wallet in the store's payee.env as OWNER_WALLET_FOR_TESTS — a made-up, checksummed address, nobody's; the owner's real address
is in no file of this repository — and `payee_env=False` is the owner who filed nothing. Each test here was red on main.
"""
import json
import os
import re
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import EstateDouble, OWNER_WALLET_FOR_TESTS, file_the_owner_payee, runner_on  # noqa: E402

OWNER = OWNER_WALLET_FOR_TESTS
STOP = T.NO_OWNER_PAYEE_SENTENCE % "arbitrum"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_against(tmp=None, payee_env=True, start_at=None, said=None, **double_kwargs):
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tmp or tempfile.mkdtemp(), invite=double.mint_founder_link() if start_at is None else None, payee_env=payee_env, start_at=start_at, said=said)
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes


def s7_calls(runner, route):
    return [c for c in runner.calls if c.station == "S7" and c.route == route]


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheOwnersWalletIsThePayee(unittest.TestCase):
    """One run against the estate at arbitrum: S6 makes both payees at the owner's wallet, S7 pays the one-dollar book to it and says so, S10 counts, S11 tells the truth."""

    @classmethod
    def setUpClass(cls):
        cls.said = []
        cls.double, cls.runner, cls.outcomes = run_against(said=cls.said)

    def test_s6_creates_both_payees_at_the_owners_wallet_through_the_two_signature_ceremony_and_says_so(self):
        o = self.outcomes["S6"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        creates = [s for s in self.runner.evidence["S6"] if s["route"] == "POST /v1/payees"]
        self.assertEqual([(s["sent"]["displayName"], s["sent"]["addresses"]) for s in creates],
                         [("Northwind Supplies", [{"chain": "arbitrum", "address": OWNER}]), ("Contoso Legal", [{"chain": "arbitrum", "address": OWNER}])])
        self.assertEqual([r["address"] for r in self.runner.facts["payees"]], [OWNER, OWNER])
        self.assertEqual([r["register_status"] for r in self.runner.facts["payees"]], ["whitelisted", "whitelisted"], "promoted and whitelisted at the roster's quorum of two (Spec T18 §2 resolves by name and chain)")
        self.assertIn("Northwind Supplies: created on arbitrum; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", o.line)
        self.assertTrue(o.line.endswith("; both at %s, the owner's wallet (read from ~/.aer360-harness/payee.env; never a derived address on arbitrum, Spec T24)" % OWNER), o.line)
        self.assertEqual(self.runner.facts["owner_payee"], OWNER)
        self.assertEqual([n for n in self.runner.notes["S6"] if n.startswith("the owner's wallet: %s on arbitrum, read from " % OWNER)],
                         ["the owner's wallet: %s on arbitrum, read from %s (Spec T24) — the address of every payee and of the one-off destination; nothing of this run is paid anywhere else" % (OWNER, self.runner.payee_env_path)])
        self.assertEqual(self.runner.payee_env_path, os.path.join(self.runner.store_dir, "payee.env"), "beside the passkeys and admin.env")
        self.assertEqual(oct(os.stat(self.runner.payee_env_path).st_mode & 0o777), "0o600")
        self.assertFalse(any(T.is_pinned(a["address"]) for a in self.double.addresses.values() if a["payeeId"] in {p["id"] for p in self.double.payees.values() if p["displayName"] in ("Northwind Supplies", "Contoso Legal")}),
                         "no derived address was whitelisted on a real chain")

    def test_s7_pays_the_one_dollar_book_to_the_owners_wallet_and_names_where_every_cent_went(self):
        o = self.outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        sets = self.runner.facts["sets"]
        self.assertEqual([(k, sets[k]["amount_minor"], sets[k]["payee"], sets[k]["landed"]) for k in ("P1", "P2", "P3")],
                         [("P1", 500000, OWNER, True), ("P2", 10000, OWNER, True), ("P3", 490000, OWNER, True)])
        self.assertEqual(sum(sets[k]["amount_minor"] for k in sets), T.ONE_DOLLAR_MINOR, "one dollar in all")
        self.assertEqual(self.double.chain.balance_of(OWNER), 1000000, "the owner's wallet received the whole dollar")
        self.assertEqual(self.double.chain.balance_of(T.address("NORTHWIND_ETHEREUM")) + self.double.chain.balance_of(T.address("CONTOSO_ETHEREUM")), 0)
        # Spec T24 §4: the line names where every cent went — the payee's address and the words "the owner's wallet" — on each payment
        self.assertIn("the payee on arbitrum: %s, the owner's wallet (read from ~/.aer360-harness/payee.env; Spec T24)" % OWNER, o.line)
        # Spec T26 §2: Holdings' gas account held nothing, so P1's review refused GAS_SHORTFALL and one credit cured it — said in P1's own line
        cure = self.runner.facts["gas_credits"][-1]
        self.assertEqual(cure["who"], "Harness Holdings")
        self.assertIn("P1 (0.50 USDC to %s, the owner's wallet, expected to proceeds to approval): the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.); "
                      "gas credited and the review asked again; %s; submitted: status approved, approvalsRequired 0; landed (+US$0.50)" % (OWNER, cure["said"]), o.line)
        self.assertIn("P2 (0.01 USDC to %s, the owner's wallet, expected to wait where the destination is new (Spec 69)): " % OWNER, o.line)
        self.assertIn("P3 (0.49 USDC to %s, the owner's wallet, expected to proceeds to approval): submitted: status approved, approvalsRequired 0; landed (+US$0.49)" % OWNER, o.line)
        self.assertEqual(o.line.count("to %s, the owner's wallet" % OWNER), 3)
        self.assertIn("payee US$0.00 → US$0.50, gas US$0.31", o.line)
        self.assertIn("payee US$0.50 → US$0.51, gas US$0.31", o.line)
        self.assertIn("payee US$0.51 → US$1.00, gas US$0.31", o.line)
        # Spec T24 §3: the Treasury's shortfall payment is computed from the one-dollar book; Spec T26: gas is credited only to cure a review's GAS_SHORTFALL —
        # the Treasury's and P1's, both accounts holding nothing in this double — one credit each, U3's ten dollars
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$1.00:" % self.double.source_account, o.line)
        self.assertEqual(self.runner.facts["money"]["treasury"]["paid_minor"], 1000000)
        self.assertEqual([json.loads(r["body"])["amount_usd_cents"] for r in self.double.platform.requests], [1000, 1000], "one cure each (Spec T26): the Treasury's review and P1's refused GAS_SHORTFALL")
        # the payee's balance was read from the chain against the owner's wallet, before and after each payment
        rpc = [c for c in self.runner.calls if c.station == "S7" and c.path == T.public_rpc_url(T.PAYEE_CHAIN)]
        self.assertEqual(len(rpc), 6)
        self.assertTrue(all(c.sent["params"][0]["data"] == T.balance_of_call_data(OWNER) for c in rpc))

    def test_the_one_offs_spec_69_words_are_honest_and_said_before_it_is_paid(self):
        """Spec T24 §2: HH-0001 paid the owner's wallet moments before, so the estate (setgates.ts, isDestinationNew) finds the destination old; the line says so, and it is a pass with the words."""
        record = self.runner.facts["one_off"]
        self.assertEqual((record["address"], record["paid_before"], record["said"]), (OWNER, True, T.ONE_OFF_ALREADY_PAID_SENTENCE))
        self.assertEqual(len(record["runs"]), 1)
        self.assertIn("(HH-0001, confirmed)", record["runs"][0], "the run that paid the wallet before: P1's")
        p2 = self.runner.facts["sets"]["P2"]
        self.assertEqual((p2["one_off_words"], p2["approvals_required"], p2["approvals"], p2["landed"]), (T.ONE_OFF_ALREADY_PAID_SENTENCE, 0, [], True))
        self.assertIn("expected to wait where the destination is new (Spec 69)): %s; submitted: status approved, approvalsRequired 0; landed (+US$0.01)" % T.ONE_OFF_ALREADY_PAID_SENTENCE, self.outcomes["S7"].line)
        # the runs register was read as the clerk between P1's landing and P2's review, and the step says what it was read for
        routes = [(c.route, (c.sent or {}).get("pays", [{}])[0].get("invoiceRef") if isinstance(c.sent, dict) else None) for c in self.runner.calls if c.station == "S7"]
        p1_execute = next(i for i, (r, _) in enumerate(routes) if r == "POST /v1/sets/%s/execute" % self.runner.facts["sets"]["P1"]["set_id"])
        p2_review = next(i for i, (r, ref) in enumerate(routes) if r == "POST /v1/sets/review" and ref == "HH-0002")
        register_reads = [i for i, (r, _) in enumerate(routes) if r == "GET /v1/sets"]
        between = [i for i in register_reads if p1_execute < i < p2_review]
        self.assertEqual(len(between), 1, "read once, after P1 landed and before P2 was reviewed")
        step = next(s for s in self.runner.evidence["S7"] if s["route"] == "GET /v1/sets" and "isDestinationNew" in s["expected"])
        self.assertEqual(step["who"], "Cora Clerk")
        self.assertIn("read for whether this estate has ever paid the owner's wallet %s on arbitrum — any instruction not rejected, to any payee (setgates.ts, isDestinationNew)" % OWNER, step["expected"])
        self.assertEqual(self.outcomes["S7"].outcome, H.PASS, "a pass with the words, not a failure")
        self.assertIsNone(self.runner.facts.get("unlisted_key"), "no derived unlisted destination is chosen on a real chain")

    def test_s10s_money_note_shows_the_difference_equals_the_payments_plus_gas(self):
        notes = [n for n in self.runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)")]
        self.assertEqual(len(notes), 1)
        self.assertIn("Harness Holdings' USDC US$0.00 → US$0.00 (received US$1.00; the three payments US$1.00, of which US$1.00 landed)", notes[0])
        self.assertIn("; Harness Holdings' USDC fell by US$1.00 and its gas account by US$0.93, US$1.93 in all — exactly the payments that landed (US$1.00) plus their gas (US$0.93): every pair reconciles to the cent", notes[0])
        self.assertEqual([f.probe for f in self.runner.findings if f.probe.startswith("money moved")], [])

    def test_s11s_hold_probe_is_counted_not_made_on_the_one_dollar_book_and_says_why(self):
        o = self.outcomes["S11"]
        self.assertEqual(o.line, "the attacker: 17 probe(s), 1 not made, 1 finding(s)")
        self.assertIn("probe not made (the clerk's payment above the per-payment limit (S7's P3) released without approval?): P3 is 0.49 USDC, under the US$10.00 hold (O2) on the one-dollar book (Spec T24), "
                      "so no payment of this run is above the per-payment limit and the estate rightly asks no approval for it", self.runner.notes["S11"])
        self.assertEqual([f.probe for f in self.runner.findings if f.station == "S11"], ["a payee address with a wrong checksum"], "no finding that lies about a payment the estate rightly approved")

    def test_the_report_carries_the_owners_wallet_and_reads_back(self):
        report = self.runner.report()
        summary = report.split("Findings in this run", 1)[1].split("## S1 — Enrol", 1)[0]
        self.assertIn("The asset: the three payments together need US$1.00 of USDC; Harness Treasury pays Harness Holdings the shortfall through the estate's own road (Spec T14); the harness never mints the asset and holds no key. "
                      "On arbitrum every payment goes to the owner's wallet, %s, read from ~/.aer360-harness/payee.env and never from the repository; the book there is one dollar in all (Spec T24)." % OWNER, summary)
        read = H.read_report(self.runner.write_report())
        self.assertEqual((read["outcomes"]["S6"], read["outcomes"]["S7"]), ("pass", "pass"))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheFirstPaymentToTheOwnersWalletProvesTheHold(unittest.TestCase):
    """Where the one-off is the first payment this estate ever makes to the owner's wallet — here, because the payee door refused the listed payees — Spec 69's hold is provable, and the line says so."""

    def test_a_wallet_the_estate_never_paid_waits_for_an_approval_and_the_line_says_the_hold_is_provable(self):
        double, runner, outcomes = run_against(refuses_payee_addresses=(OWNER,))
        self.assertEqual(outcomes["S6"].outcome, H.FAIL, "the payee door refused the owner's wallet, so Northwind and Contoso were not made")
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)  # P1 and P3 could not be resolved and were not sent; the one-off is the first payment to the wallet
        record = runner.facts["one_off"]
        self.assertEqual((record["address"], record["paid_before"], record["runs"], record["said"]), (OWNER, False, [], T.ONE_OFF_NEW_SENTENCE))
        p2 = runner.facts["sets"]["P2"]
        self.assertEqual(p2["approvals_required"], 1, "Spec 69 holds the first payment to a destination new to the estate")
        self.assertEqual([(a["who"], a["refusal_code"], a["status_after"]) for a in p2["approvals"]],
                         [("Ben Signatory", "ROLE_NOT_GRANTED", None), ("Cora Clerk", "ROLE_NOT_GRANTED", None), ("Ada Approver", None, "approved")],
                         "the signers press in the spec's order while the run waits, and the approver's signature releases it")
        self.assertTrue(p2["landed"], p2["said"])
        # Spec T26 §2: P2 is the first payment of Holdings reviewed here, its gas account holding nothing, so its review refused GAS_SHORTFALL and one credit cured it
        cure = runner.facts["gas_credits"][-1]
        self.assertEqual(cure["who"], "Harness Holdings")
        self.assertIn("P2 (0.01 USDC to %s, the owner's wallet, expected to wait where the destination is new (Spec 69)): %s; the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.); "
                      "gas credited and the review asked again; %s; submitted: status pending_approval, approvalsRequired 1;" % (OWNER, T.ONE_OFF_NEW_SENTENCE, cure["said"]), o.line)
        self.assertIn("P1 (0.50 USDC, expected to proceeds to approval): no payee Northwind Supplies on arbitrum in the register; nothing was sent;", o.line)
        self.assertEqual(double.chain.balance_of(OWNER), 10000, "one cent moved, to the owner's wallet, and nothing else")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheFileAbsentOrMalformed(unittest.TestCase):
    """Spec T24 §1: the file missing or malformed stops S6 before any payee and S7 before any payment, with the sentence — never a derived address on a real chain."""

    def test_the_file_absent_stops_s6_and_s7_with_the_sentence_as_a_missing_prerequisite_and_nothing_is_made_or_sent(self):
        said = []
        double, runner, outcomes = run_against(payee_env=False, said=said)
        o6, o7 = outcomes["S6"], outcomes["S7"]
        self.assertEqual((o6.outcome, o7.outcome), (H.FAILED_PREREQUISITE, H.FAILED_PREREQUISITE))
        self.assertEqual(o6.line, "payees: %s — %s" % (H.OWNER_PAYEE_NOT_FILED, STOP))
        self.assertTrue(o7.line.startswith("payments: %s — Harness Treasury: " % H.OWNER_PAYEE_NOT_FILED), o7.line)
        self.assertTrue(o7.line.endswith("; " + STOP), o7.line)
        self.assertIn("before: Harness Holdings holds US$0.00 of USDC on arbitrum; Harness Treasury holds US$100.00 of USDC on arbitrum", o7.line, "the money before is read and reported first")
        self.assertIn("S6 — %s — payees: %s — %s" % (H.FAILED_PREREQUISITE, H.OWNER_PAYEE_NOT_FILED, STOP), said)
        self.assertEqual(STOP, "the owner's payee address is not filed at ~/.aer360-harness/payee.env (OWNER_PAYEE_ADDRESS); on arbitrum the harness pays only the owner's own wallet; nothing was sent")
        self.assertEqual([p["displayName"] for p in double.payees.values() if p["displayName"] in ("Northwind Supplies", "Contoso Legal")], [], "no payee made")
        self.assertEqual(s7_calls(runner, "POST /v1/sets") + s7_calls(runner, "POST /v1/sets/review"), [], "nothing reviewed or created")
        self.assertEqual((double.sets, double.treasury.sets, double.chain.transfers, double.platform.requests), ({}, {}, [], []), "nothing sent, not even the Treasury's shortfall, and no gas credited")
        self.assertEqual([n for n in runner.notes["S7"] if STOP in n], [], "Spec T19 §3: the sentence travels in the line, not in a note beside it")
        self.assertEqual(runner.facts["owner_payee_problem"], "%s is not filed" % runner.payee_env_path)
        self.assertFalse(any(T.is_pinned(a["address"]) for a in double.addresses.values() if a["whitelistStatus"] != "proposed"), "S11's probe row aside, the estate holds no derived address")
        self.assertEqual(outcomes["S8"].outcome, H.PASS, "the run continues past the stop")

    def test_a_malformed_file_stops_with_what_it_found_before_the_sentence(self):
        cases = [
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=ethereum\n" % OWNER, "OWNER_PAYEE_CHAIN is 'ethereum', not arbitrum, the chain the payments are made on"),
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % OWNER.lower(), "OWNER_PAYEE_ADDRESS does not spell its own EIP-55 checksum (copy the address from the wallet again)"),
            ("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % T.address("NORTHWIND_ETHEREUM"), "OWNER_PAYEE_ADDRESS is one of the harness's own derived test addresses, which no key stands behind"),
        ]
        for text, wrong in cases:
            double = EstateDouble()
            tmp = tempfile.mkdtemp()
            path = file_the_owner_payee(os.path.join(tmp, "store"), text=text)
            runner = runner_on(double, tmp, invite=double.mint_founder_link())
            outcomes = {o.station: o for o in runner.run()}
            o6 = outcomes["S6"]
            self.assertEqual(o6.outcome, H.FAILED_PREREQUISITE, o6.line)
            self.assertEqual(o6.line, "payees: %s — %s %s; %s" % (H.OWNER_PAYEE_NOT_FILED, path, wrong, STOP), text)
            self.assertEqual(outcomes["S7"].outcome, H.FAILED_PREREQUISITE)
            self.assertTrue(outcomes["S7"].line.endswith("; %s %s; %s" % (path, wrong, STOP)), outcomes["S7"].line)
            self.assertEqual((double.sets, double.chain.transfers), ({}, []), text)
            self.assertEqual([p["displayName"] for p in double.payees.values() if p["displayName"] in ("Northwind Supplies", "Contoso Legal")], [], text)
        self.assertEqual(T.owner_payee_of("OWNER_PAYEE_ADDRESS=%s\nOWNER_PAYEE_CHAIN=arbitrum\n" % OWNER), (OWNER, None))

    def test_a_run_resumed_at_s7_reads_the_file_itself_and_resolves_the_payees_at_the_owners_wallet(self):
        tmp = tempfile.mkdtemp()
        double, first, first_outcomes = run_against(tmp=tmp)
        self.assertEqual(first_outcomes["S7"].outcome, H.PASS, first_outcomes["S7"].line)
        second = runner_on(double, tmp, start_at="S7")
        outcomes = {o.station: o for o in second.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(second.facts["owner_payee"], OWNER)
        self.assertEqual(len([n for n in second.notes["S7"] if n.startswith("the owner's wallet: %s on arbitrum, read from " % OWNER)]), 1, "S6 did not run, so S7 read the file")
        self.assertEqual(len([c for c in second.calls if c.station == "S7" and c.route == "GET /v1/payees"]), 1, "the register, read once (Spec T18 §2)")
        self.assertEqual(second.facts["payee_resolution"], {"P1": "the register's Northwind Supplies on arbitrum, whitelisted", "P3": "the register's Contoso Legal on arbitrum, whitelisted"})
        self.assertIn("P1 (0.50 USDC to %s, the owner's wallet, expected to proceeds to approval): paid to the register's Northwind Supplies on arbitrum, whitelisted; submitted:" % OWNER, o.line)
        self.assertEqual(second.facts["one_off"]["paid_before"], True, "the first run paid the wallet")
        self.assertEqual(double.chain.balance_of(OWNER), 2000000, "two dollars over two runs, every cent to the owner's wallet")
        # the file is read once per run, whatever the number of payees and payments
        reads = [n for n in second.notes["S7"] if "read from" in n and "payee.env" in n]
        self.assertEqual(len(reads), 1)


class TheTestnetKeepsTheDerivedTable(unittest.TestCase):
    """Spec T24: on the AEREDIUM testnet the derived table is used as today, T14's figures stand, and no file is required."""

    def test_with_payee_chain_set_to_the_testnet_the_derived_table_and_t14s_book_are_in_force_and_no_file_is_required(self):
        tmp = tempfile.mkdtemp()
        runner = H.Runner("https://estate.test", os.path.join(tmp, "store"), None, False, None, os.path.join(tmp, "out"),
                          transport=lambda r: (_ for _ in ()).throw(AssertionError("no call was expected")), say=lambda s: None, sleep=lambda s: None)
        with unittest.mock.patch.object(T, "PAYEE_CHAIN", "aeredium-testnet"):
            self.assertFalse(T.pays_a_real_chain())
            self.assertEqual(T.payee_words(), "a test address derived from the seed")
            self.assertEqual([p.amount for p in A.payments()], ["1.25", "4.99", "12.00"])
            self.assertIsNone(runner.require_owner_payee("S6"), "nothing to require: no payee.env stands in this store, and S6 does not stop")
            self.assertEqual(runner.payee_address("NORTHWIND_ETHEREUM"), T.address("NORTHWIND_ETHEREUM"))
            self.assertEqual(runner.payee_address("CONTOSO_ETHEREUM"), T.address("CONTOSO_ETHEREUM"))
            runner.facts["unlisted_key"] = "UNLISTED_ETHEREUM_3"
            self.assertEqual(runner.one_off_address(runner.people["cora"]), T.address("UNLISTED_ETHEREUM_3"))
            self.assertEqual(runner.one_off_words(runner.people["cora"], T.address("UNLISTED_ETHEREUM_3")), "", "the testnet's one-off says nothing of the owner's wallet")
            self.assertEqual(runner.read_owner_payee("S7"), (None, None))
            self.assertEqual(H.Runner.road_words("P2"), H.Runner.TIER_ROAD_WORDS["P2"], "T14's words on the testnet book")
            lines = H.dry_lines()
            s6 = [l for l in lines if l.startswith("S6 — ")]
            self.assertFalse(any("[file]" in l for l in s6), "no payee.env line on the testnet")
            self.assertTrue(any(T.address("NORTHWIND_ETHEREUM") in l for l in s6))
            self.assertTrue(any(T.address("UNLISTED_ETHEREUM") in l and '"declared": true' in l for l in lines if l.startswith("S7 — ")))
            self.assertFalse(any(T.OWNER_PAYEE_PLACEHOLDER in l for l in lines))
            self.assertTrue(any("12.00 (USDC): expected to held; the spec: waits for three and lands when the third signs" in l for l in lines))
        self.assertTrue(T.pays_a_real_chain(), "and arbitrum is a real chain again")

    def test_the_dry_run_never_reads_the_file_and_prints_no_address_but_the_derived_probe(self):
        lines = H.dry_lines()
        self.assertFalse(any(OWNER in l for l in lines), "the tests' owner wallet is not the printer's business either")
        addresses = set(re.findall(r"0x[0-9a-fA-F]{40}", "\n".join(lines)))
        self.assertEqual(addresses, {T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))}, "the one address a dry line prints is S11's checksum probe, derived and refused on purpose")
        self.assertEqual(len([l for l in lines if T.OWNER_PAYEE_PLACEHOLDER in l]), 7)
        with unittest.mock.patch("builtins.open", side_effect=AssertionError("the printer opened a file")):
            H.dry_lines()

    def test_no_address_of_the_owners_and_no_derived_payee_address_is_in_a_tracked_file_the_harness_reads(self):
        """The repository holds no owner address: the only forty-hex literals among the estate harness's sources and fixtures are the corridor's own and the probe's."""
        for name in ("aer360_tables.py", "aer360_answers.py", "aer360_harness.py", "aer360_estate_road.py"):
            with open(os.path.join(ROOT, name), "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertEqual(re.findall(r"0x[0-9a-fA-F]{40}", text), [], "%s holds a literal address" % name)
        with open(os.path.join(ROOT, "tests", "fixtures", "aer360-dry-calls.txt"), "r", encoding="utf-8") as handle:
            fixture = handle.read()
        self.assertEqual(set(re.findall(r"0x[0-9a-fA-F]{40}", fixture)), {T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))})
        self.assertNotIn(OWNER, fixture)


if __name__ == "__main__":
    unittest.main()
