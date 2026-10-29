"""
Spec T29 and HRW-2 (24 October 2026, amended 30 October 2026): the two legs of the estate harness learn the Solana road. This file is the API
leg's: the curve and the alphabet held to the estate's own vectors, and the five stations — S5s Solana wallets, S6s Solana payee, S7s-1 SOL
payment, S7s-2 the curve belt, S7s-3 Solana holdings — walked on the estate double with the road open and closed, and every stop proved by name.

THE VECTORS (§5): the base58 known-answer table and the curve's deterministic probes are copied as data from aeredium/AERAccounts main at
d369926, packages/solana/src/address.test.ts (Spec AER360-SOL-114 §3.10) — the public base58 vectors, sha256 probes `solana-curve-probe-<i>`,
`thirty-one`, and the Ed25519 secrets `solana-test-secret-<i>`, whose public keys are derived here in pure Python (RFC 8032 §5.1.5, the base
point's scalar multiple in affine coordinates) since the test has no independent library to hand. No address of the owner's, and nobody's key.

THE BOOK (§0a.3): the SOL amount is the owner's figure and the brief writes none, so the walks that pay patch `aer360_answers.SOLANA_PAYMENT_SOL`
with a test figure (0.002 SOL, twenty cents at the double's US$100.00 a SOL) and lower the USDC book to 0.40, 0.01 and 0.39 — eighty cents, so the
dollar has room for the twenty. The unpatched book stops S7s-1 by name (the figure not written; and, with a figure, no room under the dollar).
"""
import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import (MESSAGES, OWNER_WALLET_FOR_TESTS, SOLANA_BASE_FEE_LAMPORTS, EstateDouble, file_the_owner_payee,  # noqa: E402
                                      runner_on, solana_address_for_tests)

SOL_FIGURE = "0.002"                 # the test's stand-in for the owner's figure: 2,000,000 lamports, twenty cents at the double's rate
SOL_LAMPORTS = 2_000_000
SOLANA_BOOK = [A.PAYMENTS_ON_A_REAL_CHAIN[0]._replace(amount="0.40"), A.PAYMENTS_ON_A_REAL_CHAIN[1], A.PAYMENTS_ON_A_REAL_CHAIN[2]._replace(amount="0.39")]
SOLANA_STATIONS = ("S5s", "S6s", "S7s-1", "S7s-2", "S7s-3")

# packages/solana/src/address.test.ts, BASE58_VECTORS — "the public base58 test vectors", copied as data
BASE58_VECTORS = [
    ("", ""),
    ("61", "2g"),
    ("626262", "a3gV"),
    ("636363", "aPEr"),
    ("73696d706c792061206c6f6e6720737472696e67", "2cFupjhnEsSn59qHXstmK2ffpLv2"),
    ("00eb15231dfceb60925886b67d065299925915aeb172c06647", "1NS17iag9jJgTHD1VXjvLCEnZuQ3rJDE9L"),
    ("516b6fcd0f", "ABnLTmg"),
    ("bf4f89001e670274dd", "3SEo3LWLoPntC"),
    ("572e4794", "3EFU7m"),
    ("ecac89cad93923c02321", "EJDM8drfXA6uyA"),
    ("10c8511e", "Rt5zm"),
    ("00000000000000000000", "1111111111"),
]


def probe(label):
    """address.test.ts `probe`: a deterministic 32-byte candidate, sha256 of the label."""
    return hashlib.sha256(label.encode("utf-8")).digest()


# -- Ed25519 in pure Python, for the keys address.test.ts derives with @noble/curves (RFC 8032 §5.1.5) ---------------------------------------
P = 2 ** 255 - 19
D = (-121665 * pow(121666, P - 2, P)) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)
BASE_Y = (4 * pow(5, P - 2, P)) % P


def recover_x(y, sign):
    x2 = ((y * y - 1) * pow(D * y * y + 1, P - 2, P)) % P
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = (x * SQRT_M1) % P
    if (x * x - x2) % P:
        raise ValueError("not a point")
    return P - x if (x & 1) != sign else x


BASE = (recover_x(BASE_Y, 0), BASE_Y)


def edwards_add(a, b):
    x1, y1 = a
    x2, y2 = b
    product = D * x1 * x2 * y1 * y2
    x3 = ((x1 * y2 + x2 * y1) * pow(1 + product, P - 2, P)) % P
    y3 = ((y1 * y2 + x1 * x2) * pow(1 - product, P - 2, P)) % P
    return x3, y3


def scalar_mult(k, point):
    result = (0, 1)
    while k:
        if k & 1:
            result = edwards_add(result, point)
        point = edwards_add(point, point)
        k >>= 1
    return result


def ed25519_public_key(secret):
    digest = hashlib.sha512(secret).digest()
    a = int.from_bytes(digest[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    x, y = scalar_mult(a, BASE)
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def the_solana_book(figure=SOL_FIGURE, book=None):
    """The owner's figure written and the USDC book lowered to leave room under the dollar — the harness reads both at call time."""
    return unittest.mock.patch.multiple(A, SOLANA_PAYMENT_SOL=figure, PAYMENTS_ON_A_REAL_CHAIN=list(SOLANA_BOOK if book is None else book))


def calls_at(runner, station, route=None):
    return [c for c in runner.calls if c.station == station and (route is None or c.route == route)]


def sets_carrying(double, invoice):
    return [s for s in double.sets.values() if any(i.get("invoiceRef") == invoice for i in s["instructions"])]


def solana_wallets_of(double):
    """The double's pressed Solana wallets in wallet-number order: the first pays, the second is the payee."""
    return sorted([w for w in double.pressed_wallets.values() if w["chain"] == T.SOLANA_CHAIN], key=lambda w: int(w["walletNumber"]))


class TheCurveAndTheAlphabet(unittest.TestCase):
    """aer360_tables.py carries packages/solana/src/address.ts in pure Python; the estate's own vectors hold it."""

    def test_the_alphabet_is_solanas(self):
        self.assertEqual(T.BASE58_ALPHABET, "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        for forbidden in "0OIl":
            self.assertNotIn(forbidden, T.BASE58_ALPHABET)

    def test_every_known_answer_vector_encodes_and_decodes(self):
        for hex_bytes, base58 in BASE58_VECTORS:
            raw = bytes.fromhex(hex_bytes)
            self.assertEqual(T.base58_encode(raw), base58, "encode %s" % hex_bytes)
            self.assertEqual(T.base58_decode(base58), raw, "decode %s" % base58)
        self.assertIsNone(T.base58_decode("0OIl"), "a character outside the alphabet is no base58")
        self.assertIsNone(T.base58_decode(None))

    def test_round_trips_keep_leading_zeros_as_leading_ones(self):
        for i in range(16):
            raw = b"\x00\x00" + probe("round-trip-%d" % i)[2:]
            text = T.base58_encode(raw)
            self.assertTrue(text.startswith("11"))
            self.assertEqual(T.base58_decode(text), raw)

    def test_the_three_facts_are_judged_in_their_order(self):
        for text in ("not base58 at all!!", "", "0OIl", "a", "1" * 45, None, 42):
            self.assertEqual(T.judge_solana_address(text)[0], "shape", repr(text))
        thirty_one = T.base58_encode(probe("thirty-one")[:31])
        self.assertGreaterEqual(len(thirty_one), 32)
        self.assertEqual(T.judge_solana_address(thirty_one)[0], "length")
        self.assertEqual(T.judge_solana_address("1" * 44)[0], "length", "44 ones decode to 44 zero bytes — wrong length, not wrong shape")

    def test_the_256_deterministic_probes_exercise_both_doors_and_agree_with_the_judgment(self):
        on_curve = off_curve = non_canonical = 0
        for i in range(256):
            candidate = probe("solana-curve-probe-%d" % i)
            y = int.from_bytes(candidate, "little") & ((1 << 255) - 1)
            text = T.base58_encode(candidate)
            if y >= P:
                self.assertFalse(T.is_on_curve(candidate), "a non-canonical y is refused outright (candidate %d)" % i)
                non_canonical += 1
                continue
            if T.is_on_curve(candidate):
                on_curve += 1
                self.assertEqual(T.judge_solana_address(text), (None, candidate))
                self.assertTrue(T.is_solana_address(text))
            else:
                off_curve += 1
                self.assertEqual(T.judge_solana_address(text), ("off_curve", candidate))
                self.assertFalse(T.is_solana_address(text))
        self.assertGreater(on_curve, 0)
        self.assertGreater(off_curve, 0)
        self.assertGreaterEqual(non_canonical, 0)

    def test_every_key_derived_from_the_estates_test_secrets_is_on_the_curve(self):
        for i in range(16):
            public_key = ed25519_public_key(probe("solana-test-secret-%d" % i))
            self.assertTrue(T.is_on_curve(public_key), "solana-test-secret-%d" % i)
            self.assertTrue(T.is_solana_address(T.base58_encode(public_key)))
        door = ed25519_public_key(probe("solana-door-secret"))
        self.assertEqual(T.judge_solana_address(T.base58_encode(door)), (None, door))

    def test_the_base_point_is_the_standards(self):
        self.assertEqual(BASE_Y, 46316835694926478169428394003475163141307993866256225615783033603165251855960)
        self.assertEqual(BASE[0], 15112221349535400772501151409588531511454012693041857206046113283949847762202)

    def test_the_slips_are_built_from_a_real_address_and_name_their_faults(self):
        address = solana_address_for_tests("the slips' address")
        self.assertIsNone(T.judge_solana_address(address)[0])
        short = T.short_variant(address)
        self.assertEqual(T.judge_solana_address(short)[0], "length")
        self.assertEqual(len(T.base58_decode(short)), 31)
        off = T.off_curve_variant(address)
        self.assertEqual(T.judge_solana_address(off)[0], "off_curve")
        self.assertEqual(len(T.base58_decode(off)), 32)
        self.assertNotEqual(off, address)
        with self.assertRaises(ValueError):
            T.short_variant("0x" + "ab" * 20)

    def test_the_payee_doors_three_sentences_are_the_estates(self):
        base = "That is not an address Solana can pay, so nothing was saved."
        self.assertEqual(T.solana_address_malformed_sentence("shape"), "%s On Solana, %s." % (base, T.SOLANA_SHAPE_EXPECTED))
        self.assertEqual(T.solana_address_malformed_sentence("length"), "%s %s" % (base, T.SOLANA_LENGTH_WORDS))
        self.assertEqual(T.solana_address_malformed_sentence("off_curve"), "%s %s" % (base, T.SOLANA_OFF_CURVE_WORDS))
        self.assertEqual(T.evm_address_malformed_sentence("Arbitrum One"),
                         "That is not an address Arbitrum One can pay, so nothing was saved. On Arbitrum One, an address is 0x followed by exactly 40 hexadecimal characters.")
        with self.assertRaises(ValueError):
            T.solana_address_malformed_sentence("curve")
        self.assertEqual(MESSAGES[T.WALLET_CURVE_MISMATCH], T.SOLANA_REFUSAL_SENTENCES[T.WALLET_CURVE_MISMATCH], "the double restates refusals.ts, word for word")
        self.assertEqual(MESSAGES[T.SOLANA_ROAD_CLOSED], T.SOLANA_REFUSAL_SENTENCES[T.SOLANA_ROAD_CLOSED])
        self.assertEqual(MESSAGES[T.SOLANA_TOKEN_ACCOUNT_ABSENT], T.SOLANA_REFUSAL_SENTENCES[T.SOLANA_TOKEN_ACCOUNT_ABSENT])

    def test_lamports_and_sol_are_said_by_string_arithmetic(self):
        self.assertEqual(T.lamports_of("0.002"), 2_000_000)
        self.assertEqual(T.lamports_of("1"), T.LAMPORTS_PER_SOL)
        self.assertEqual(T.sol_words(T.FEE_RESERVE_LAMPORTS), "0.01 SOL")
        self.assertEqual(T.sol_words(2_500_000), "0.0025 SOL")
        self.assertEqual(T.sol_words(0), "0 SOL")
        self.assertEqual(T.sol_words(47_995_000), "0.047995 SOL")
        self.assertEqual(T.FEE_RESERVE_LAMPORTS, 10_000_000, "packages/solana/src/fees.ts FEE_RESERVE_LAMPORTS")
        self.assertEqual(T.ASSET_DECIMALS["SOL"], 9)
        self.assertEqual((T.curve_for_chain("solana"), T.curve_for_chain("arbitrum"), T.chain_family("solana"), T.chain_family("ethereum")), ("ed25519", "secp256k1", "solana", "evm"))
        self.assertEqual(T.usdc_signal_words(False), "has not received USDC yet (solanaUsdcAccount false)")
        with self.assertRaises(ValueError):
            T.sol_words(-1)

    def test_the_book_names_no_figure_until_the_owner_writes_one(self):
        self.assertIsNone(A.SOLANA_PAYMENT_SOL, "Spec T29 §0a.3: the brief writes none")
        self.assertIsNone(A.solana_payment())
        payment = A.solana_payment(SOL_FIGURE)
        self.assertEqual((payment.key, payment.payee_key, payment.payee_name, payment.invoice, payment.lamports), ("PS1", "SOLANA_WALLET_2", A.SOLANA_PAYEE_NAME, "HH-S001", SOL_LAMPORTS))
        self.assertEqual([w["chain"] for w in A.SOLANA_WALLETS], ["solana", "solana"])
        self.assertEqual(A.payments_total_minor(), T.ONE_DOLLAR_MINOR, "the USDC book stands as Spec T24 left it")
        self.assertEqual(A.payments_total_minor(SOLANA_BOOK), 800000)
        self.assertEqual([s for s, _ in H.STATIONS], ["S1", "S2", "S3", "S4", "S5", "S5s", "S6", "S6s", "S7", "S7s-1", "S7s-2", "S7s-3", "S8", "S9", "S10", "S11", "S12", "S14"])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheRoadIsOpen(unittest.TestCase):
    """The five stations on an estate whose Solana road is open, with the owner's figure written: two wallets, one payee, one SOL payment that lands."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble()
        cls.tmp = tempfile.mkdtemp()
        cls.said = []
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link(), said=cls.said)
        with the_solana_book():
            cls.outcomes = {o.station: o for o in cls.runner.run()}
            cls.report_path = cls.runner.write_report()
        with open(cls.report_path, "r", encoding="utf-8") as handle:
            cls.report = handle.read()
        cls.wallets = solana_wallets_of(cls.double)

    def test_the_five_pass_and_the_findings_are_the_two_the_double_always_gives(self):
        for station in SOLANA_STATIONS:
            self.assertEqual(self.outcomes[station].outcome, H.PASS, self.outcomes[station].line)
        self.assertEqual(self.outcomes["S7"].outcome, H.PASS, self.outcomes["S7"].line)
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings], [("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")])

    def test_s5s_presses_two_solana_wallets_with_the_network_on_both_steps_and_reads_each_back(self):
        self.assertEqual(len(self.wallets), 2)
        for w in self.wallets:
            self.assertTrue(T.is_solana_address(w["address"]))
            self.assertEqual((w["chains"], w["curve"], w["keyed"]), (["solana"], "ed25519", True))
        for route in ("POST %s" % T.WALLET_PRESS_OPTIONS_ROUTE, "POST %s" % T.WALLET_PRESS_ROUTE):
            presses = calls_at(self.runner, "S5s", route)
            self.assertEqual(len(presses), 2, route)
            self.assertTrue(all(c.sent["chain"] == "solana" and c.sent["whose"] == "estate" for c in presses))
        line = self.outcomes["S5s"].line
        self.assertIn("Solana wallet: born by this run's press — wallet 2 at %s (level 1, signing group [\"group-100\"])" % self.wallets[0]["address"], line)
        self.assertIn("Solana wallet 2: born by this run's press — wallet 3 at %s" % self.wallets[1]["address"], line)
        self.assertIn("the register: wallet 3 on solana, keyed True, address %s" % self.wallets[1]["address"], line)
        self.assertIn("the view carries no addressForm or curve field (RegisterWalletView at d369926)", line)
        self.assertEqual([w["address"] for w in self.runner.facts["solana"]["wallets"]], [w["address"] for w in self.wallets])

    def test_s5s_writes_the_two_down_without_a_key_and_prints_the_first_address_for_the_owner(self):
        path = self.runner.solana_wallets_file()
        self.assertTrue(path.endswith(os.path.join(A.ESTATE["client_id"], T.SOLANA_WALLETS_FILE)))
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        with open(path, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        self.assertEqual([w["address"] for w in stored["wallets"]], [w["address"] for w in self.wallets])
        self.assertEqual(stored["payee"]["address"], self.wallets[1]["address"])
        self.assertEqual(stored["payment"]["invoice"], "HH-S001")
        self.assertTrue(stored["payment"]["landed"])
        text = json.dumps(stored).lower()
        for secret_word in ("private", "secret", "seed", "keyid", "begin"):
            self.assertNotIn(secret_word, text, secret_word)
        self.assertIn(T.SOLANA_FUNDS_LINE % (self.wallets[0]["address"], "0.002 SOL", "0.01 SOL"), self.runner.notes["S5s"])

    def test_s6s_makes_the_second_wallet_the_payee_on_solana_verbatim_and_reads_its_usdc_signal(self):
        line = self.outcomes["S6s"].line
        payee = self.runner.facts["solana"]["payee"]
        self.assertEqual((payee["name"], payee["address"], payee["chain"], payee["register_status"]), (A.SOLANA_PAYEE_NAME, self.wallets[1]["address"], "solana", "whitelisted"))
        rows = [a for a in self.double.addresses.values() if a["chain"] == "solana"]
        self.assertEqual([(a["address"], a["whitelistStatus"]) for a in rows], [(self.wallets[1]["address"], "whitelisted")], "the payee alone on solana; none of the slips written")
        self.assertIn("the payee is the harness's second Solana wallet %s (wallet 3), never an address outside the estate (the owner's ruling of 29 October 2026)" % self.wallets[1]["address"], line)
        self.assertIn("the address stands verbatim; solanaUsdcAccount false — has not received USDC yet (solanaUsdcAccount false)", line)
        self.assertIs(self.runner.facts["solana"]["usdc_signal"], False)
        self.assertNotIn(T.SOLANA_PAYEE_KEY, line, "payee.env carries no SOLANA_PAYEE, so nothing is said of it")

    def test_s6s_types_the_three_slips_and_each_is_refused_in_the_estates_sentence_and_none_is_written(self):
        slips = [c for c in calls_at(self.runner, "S6s", "POST /v1/payees") if str(c.sent.get("displayName", "")).startswith("Solana slip: ")]
        self.assertEqual(len(slips), 3)
        self.assertTrue(all(c.status == 422 for c in slips))
        faults = [json.loads(c.text)["error"] for c in slips]
        self.assertEqual([f["code"] for f in faults], [T.ADDRESS_MALFORMED] * 3)
        self.assertEqual([f["message"] for f in faults], [T.solana_address_malformed_sentence(fault) for fault in ("shape", "length", "off_curve")])
        self.assertEqual(faults[0]["detail"]["expected"], T.SOLANA_SHAPE_EXPECTED)
        self.assertEqual([f["detail"].get("fault") for f in faults[1:]], ["length", "off_curve"])
        line = self.outcomes["S6s"].line
        for words in ("the wrong shape (a 0x address) (shape): refused — \"%s\"" % T.solana_address_malformed_sentence("shape"),
                      "base58 of thirty-one bytes (length): refused", "thirty-two bytes off the curve (off_curve): refused", "none of the three written"):
            self.assertIn(words, line, words)

    def test_s7s_1_pays_the_sol_from_the_first_wallet_to_the_second_under_the_dollar_and_the_allowance(self):
        line = self.outcomes["S7s-1"].line
        payer, payee = self.wallets
        self.assertEqual([(t["from"], t["to"], t["lamports"]) for t in self.double.solana.transfers], [(payer["address"], payee["address"], SOL_LAMPORTS)])
        self.assertEqual(self.double.solana.balance_of(payee["address"]), SOL_LAMPORTS)
        self.assertEqual(self.double.solana.balance_of(payer["address"]), 50_000_000 - SOL_LAMPORTS - SOLANA_BASE_FEE_LAMPORTS)
        self.assertIn("the sandbox allowance: Sandbox allowance: US$9.20 of US$10.00 left", line)
        self.assertIn("the book's SOL amount: 0.002 SOL (HH-S001, the owner's figure)", line)
        self.assertIn("the payee: this run's %s on solana at %s (wallet 3)" % (A.SOLANA_PAYEE_NAME, payee["address"]), line)
        self.assertIn("before: wallet 2 holds 0.05 SOL", line)
        self.assertIn("the estate values the payment at US$0.20; with the book's US$0.80 on arbitrum that is US$1.00 of the one-dollar total (Spec T24); the allowance has US$9.20 left", line)
        self.assertIn("landed (+0.002 SOL)", line)
        self.assertIn("payee wallet 0 SOL → 0.002 SOL", line)
        created = calls_at(self.runner, "S7s-1", "POST /v1/sets")
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].sent["walletId"], payer["walletId"])
        self.assertEqual(created[0].sent["pays"][0]["asset"], "SOL")
        self.assertEqual(created[0].sent["pays"][0]["amountMinor"], str(SOL_LAMPORTS))
        money = self.runner.facts["money"]["solana"]
        self.assertEqual((money["lamports"], money["usd_cents"], money["landed"], money["gas_debit_cents"]), (SOL_LAMPORTS, 20, True, 0))

    def test_s7s_1_proves_the_landing_on_the_signature_the_trail_and_the_payees_sol(self):
        run = sets_carrying(self.double, "HH-S001")[0]
        instruction = run["instructions"][0]
        self.assertEqual((run["status"], instruction["status"], run["sourceAccount"]), ("settled", "confirmed", self.wallets[0]["address"]))
        self.assertEqual(len(T.base58_decode(instruction["txHash"])), T.SIGNATURE_BYTES)
        mine = [r for r in self.double.trail if r.get("subject_id") == instruction["id"]]
        actions = [r["action"] for r in mine]
        for action in (T.INSTRUCTION_BUILDING, T.INSTRUCTION_SIGNING, T.INSTRUCTION_BROADCASTING, T.INSTRUCTION_CONFIRMED):
            self.assertIn(action, actions)
        signing = next(r for r in mine if r["action"] == T.INSTRUCTION_SIGNING)["detail"]
        self.assertEqual((signing["road"], signing["carries"], signing["fee"]), ("solana", {"kind": "native", "lamports": str(SOL_LAMPORTS)}, "met from the wallet’s standing lamports"))
        confirmed = next(r for r in mine if r["action"] == T.INSTRUCTION_CONFIRMED)["detail"]
        self.assertEqual(confirmed["txHash"], instruction["txHash"])
        self.assertTrue(confirmed["slot"].isdigit())
        self.assertTrue(confirmed["explorer"].startswith(T.SOLANA_EXPLORER_TX_URL))
        record = self.runner.facts["solana"]["payment"]
        self.assertEqual((record["tx_hash"], record["slot"], record["landed"], record["top_up"]), (instruction["txHash"], confirmed["slot"], True, None))
        self.assertIn("the Solana payment (S7s-1, Spec T29): 0.002 SOL landed, worth US$0.20 at the estate's valuation, counted with the book's US$0.80 under the one-dollar total (US$1.00 in all)",
                      " ".join(self.runner.notes["S10"]))

    def test_s7s_2_is_refused_at_the_curve_belt_and_dials_nothing(self):
        line = self.outcomes["S7s-2"].line
        review = calls_at(self.runner, "S7s-2", "POST /v1/sets/review")
        self.assertEqual(len(review), 1)
        self.assertEqual(review[0].status, 422)
        self.assertNotIn("walletId", review[0].sent, "the funding wallet: no walletId, an EVM key")
        error = json.loads(review[0].text)["error"]
        self.assertEqual((error["code"], error["message"]), (T.WALLET_CURVE_MISMATCH, T.SOLANA_REFUSAL_SENTENCES[T.WALLET_CURVE_MISMATCH]))
        self.assertEqual((error["detail"]["curve"], error["detail"]["required"], error["detail"]["cause"]), ("secp256k1", "ed25519", T.CURVE_MISMATCH_CAUSE_SOLANA))
        self.assertEqual(sets_carrying(self.double, "HH-S002"), [])
        self.assertIn("refused WALLET_CURVE_MISMATCH, 422 — \"%s\" (curve secp256k1, required ed25519" % T.SOLANA_REFUSAL_SENTENCES[T.WALLET_CURVE_MISMATCH], line)
        self.assertIn("nothing dialled", line)

    def test_s7s_3_reads_each_wallets_holdings_through_the_estates_road_and_the_signal_unchanged(self):
        line = self.outcomes["S7s-3"].line
        self.assertIn("wallet 2 holds 0.047995 SOL and US$0.00 of USDC", line)
        self.assertIn("wallet 3 holds 0.002 SOL and US$0.00 of USDC", line)
        self.assertIn("the Solana payee's USDC signal unchanged: solanaUsdcAccount false (has not received USDC yet (solanaUsdcAccount false))", line)
        self.assertEqual([(h["wallet"], h["lamports"]) for h in self.runner.facts["solana"]["holdings"]], [("2", 50_000_000 - SOL_LAMPORTS - SOLANA_BASE_FEE_LAMPORTS), ("3", SOL_LAMPORTS)])
        refreshes = calls_at(self.runner, "S7s-3", "POST %s" % T.REFRESH_ROUTE)
        self.assertEqual(len(refreshes), 1, "one reading for the station, never a node of the harness's own")
        self.assertEqual([c.route for c in self.runner.calls if "rpc" in c.route.lower() and "solana" in c.route.lower()], [], "no Solana node of the harness's own is ever called")

    def test_the_report_carries_the_five_and_reads_back(self):
        for station, title in (("S5s", "Solana wallets"), ("S6s", "Solana payee"), ("S7s-1", "SOL payment"), ("S7s-2", "The curve belt"), ("S7s-3", "Solana holdings")):
            self.assertIn("| %s %s | pass |" % (station, title), self.report)
            self.assertIn("## %s — %s" % (station, title), self.report)
        read = H.read_report(self.report_path)
        self.assertEqual([read["outcomes"][s] for s in SOLANA_STATIONS], ["pass"] * 5)
        self.assertEqual(len(read["outcomes"]), len(H.STATIONS))
        self.assertIn(self.wallets[0]["address"], self.report)
        self.assertNotIn("BEGIN EC PRIVATE KEY", self.report)

    def test_a_run_resumed_at_s5s_takes_the_wallets_and_the_payee_on_and_pays_again_confirming_the_repeat(self):
        said = []
        runner = runner_on(self.double, self.tmp, start_at="S5s", said=said)
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        for station in SOLANA_STATIONS:
            self.assertEqual(outcomes[station].outcome, H.PASS, outcomes[station].line)
        self.assertEqual(len(solana_wallets_of(self.double)), 2, "nothing pressed for again")
        self.assertIn("taken on, not pressed for again", outcomes["S5s"].line)
        self.assertEqual(calls_at(runner, "S5s", "POST %s" % T.WALLET_PRESS_ROUTE), [])
        self.assertIn("%s stands whitelisted on solana at %s (an earlier run's); taken on, not made again" % (A.SOLANA_PAYEE_NAME, self.wallets[1]["address"]), outcomes["S6s"].line)
        self.assertEqual(len(self.double.solana.transfers), 2, "the second run pays the owner's figure again, as the book says")
        self.assertTrue(any("confirmed it, as a founder would (Spec T28)" in n for n in runner.notes["S7s-1"]), runner.notes["S7s-1"])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheRoadIsClosed(unittest.TestCase):
    """SOLANA_RPC_URLS names fewer than two endpoints: the wallets are born all the same, the payee is made, and every reading or payment says the road is closed by name."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(solana_road="closed")
        cls.tmp = tempfile.mkdtemp()
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        with the_solana_book():
            cls.outcomes = {o.station: o for o in cls.runner.run()}
        cls.wallets = solana_wallets_of(cls.double)

    def test_every_solana_station_passes_as_truth_told_and_nothing_moves(self):
        for station in SOLANA_STATIONS:
            self.assertEqual(self.outcomes[station].outcome, H.PASS, self.outcomes[station].line)
        self.assertEqual(self.double.solana.transfers, [])
        self.assertEqual(sets_carrying(self.double, "HH-S001"), [], "the review refused the closed road, so no run was created")
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings], [("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")])

    def test_s5s_births_the_wallets_because_the_allocation_goes_through_the_gateway_not_the_road(self):
        self.assertEqual(len(self.wallets), 2)
        self.assertIn("born by this run's press", self.outcomes["S5s"].line)

    def test_s6s_reads_the_signal_as_null_and_the_room_silent(self):
        self.assertIn("solanaUsdcAccount null — the room says nothing (solanaUsdcAccount null: the road is closed, or the signal was never read)", self.outcomes["S6s"].line)
        self.assertIsNone(self.runner.facts["solana"]["usdc_signal"])

    def test_s7s_1_meets_the_closed_road_at_the_review_and_says_so_by_name(self):
        line = self.outcomes["S7s-1"].line
        self.assertIn(T.CLOSED_ROAD_TRUTH_TOLD % ("%s: %s" % (T.SOLANA_ROAD_CLOSED, T.SOLANA_REFUSAL_SENTENCES[T.SOLANA_ROAD_CLOSED])), line)
        self.assertIn("the refresh skipped it, SOLANA_ROAD_CLOSED", line)
        self.assertTrue(self.runner.facts["solana"]["closed"])
        reviews = calls_at(self.runner, "S7s-1", "POST /v1/sets/review")
        self.assertEqual(len(reviews), 1)
        gate = next(g for g in json.loads(reviews[0].text)["gates"] if g["gate"] == T.GAS_GATE)
        self.assertEqual([r["code"] for r in gate["refusals"]], [T.SOLANA_ROAD_CLOSED])
        self.assertEqual(calls_at(self.runner, "S7s-1", "POST /v1/sets"), [])

    def test_s7s_2_is_judged_at_the_door_whatever_the_road(self):
        self.assertIn("refused WALLET_CURVE_MISMATCH, 422", self.outcomes["S7s-2"].line)

    def test_s7s_3_reads_the_skipped_wallets_and_their_absence(self):
        line = self.outcomes["S7s-3"].line
        self.assertIn("wallet 2: the refresh skipped it, SOLANA_ROAD_CLOSED — \"%s\" — and the overview shows its row with no figure" % T.SOLANA_REFUSAL_SENTENCES[T.SOLANA_ROAD_CLOSED], line)
        self.assertIn(T.CLOSED_ROAD_TRUTH_TOLD % ("%s: %s" % (T.SOLANA_ROAD_CLOSED, T.SOLANA_REFUSAL_SENTENCES[T.SOLANA_ROAD_CLOSED])), line)
        self.assertTrue(all(h["closed"] and h["lamports"] is None for h in self.runner.facts["solana"]["holdings"]))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ThePreflight(unittest.TestCase):
    """Spec T29 §0a.4: the plan's signing group and the account's allowed chains, read before anything is pressed."""

    def test_a_workspace_off_group_100_stops_the_whole_run_at_s1(self):
        double = EstateDouble(assigned_groups=("group-3",))
        tmp = tempfile.mkdtemp()
        said = []
        runner = runner_on(double, tmp, invite=double.mint_founder_link(), said=said)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S1"].outcome, H.FAILED_PREREQUISITE, outcomes["S1"].line)
        sentence = T.WRONG_SIGNING_GROUP_SENTENCE % (A.ESTATE["company"], double.aap_account_id, "group-3", "group-100")
        self.assertIn(sentence, outcomes["S1"].line)
        self.assertEqual(runner.halted, sentence)
        for station in [s for s, _ in H.STATIONS if s != "S1"]:
            self.assertEqual(outcomes[station].outcome, H.NOT_RUN, outcomes[station].line)
            self.assertIn("not run — the run stopped at S1: ", outcomes[station].line)
        self.assertEqual(double.pressed_wallets, {})
        self.assertEqual(double.sets, {})
        self.assertEqual([c.route for c in runner.calls if c.route.startswith("POST") and c.station != "S1"], [], "nothing pressed after the stop")

    def test_an_account_whose_chains_lack_solana_stops_the_solana_stations_by_name_at_s5s(self):
        double = EstateDouble(solana_allowed=False)
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        self.assertIn("the account's allowed chains: arbitrum on", outcomes["S1"].line)
        self.assertIn("solana is not among them, so the Solana stations stop by name at S5s (Spec T29 §0a.4)", outcomes["S1"].line)
        self.assertEqual(outcomes["S5s"].outcome, H.FAILED_PREREQUISITE, outcomes["S5s"].line)
        self.assertIn(T.SOLANA_NOT_ALLOWED_SENTENCE % "arbitrum", outcomes["S5s"].line)
        for station in ("S6s", "S7s-1", "S7s-3"):
            self.assertEqual(outcomes[station].outcome, H.FAILED_PREREQUISITE, outcomes[station].line)
            self.assertIn("the Solana stations after S5s are skipped by name", outcomes[station].line)
        self.assertEqual(outcomes["S7s-2"].outcome, H.FAILED_PREREQUISITE, outcomes["S7s-2"].line)
        self.assertEqual(solana_wallets_of(double), [], "nothing pressed")
        self.assertEqual(double.solana.transfers, [])
        for station in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"):
            self.assertEqual(outcomes[station].outcome, H.PASS, outcomes[station].line)

    def test_without_admin_env_the_chains_are_said_unread_and_the_road_is_walked(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link(), admin_env=False)
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        self.assertIn("the account's allowed chains: not read — the estate's readiness reports none", outcomes["S1"].line)
        self.assertIn("is not filed, so the platform's read road was not asked", outcomes["S1"].line)
        self.assertIn("the account %s stands on group-100" % double.aap_account_id, outcomes["S1"].line)
        self.assertEqual([outcomes[s].outcome for s in SOLANA_STATIONS], [H.PASS] * 5, [outcomes[s].line for s in SOLANA_STATIONS])
        self.assertEqual([r for r in double.platform.requests if r["path"].endswith("/policies")], [], "the platform's read road is not asked without the credential")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheOwnersFigureAndTheDollar(unittest.TestCase):
    """Spec T29 §0a.3, §0a.6 and Spec T24: the figure is the owner's; the dollar and the allowance are read, never assumed."""

    def test_no_figure_written_prints_the_address_and_stops_s7s_1_before_any_review(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}  # the book as the brief leaves it: SOLANA_PAYMENT_SOL is None
        wallets = solana_wallets_of(double)
        self.assertEqual(outcomes["S7s-1"].outcome, H.FAILED_PREREQUISITE, outcomes["S7s-1"].line)
        self.assertEqual(outcomes["S7s-1"].line, "sol payment: %s" % T.SOLANA_AMOUNT_NOT_WRITTEN_SENTENCE)
        self.assertIn(T.SOLANA_FUNDS_LINE % (wallets[0]["address"], A.SOLANA_AMOUNT_PLACEHOLDER, "0.01 SOL"), runner.notes["S7s-1"])
        self.assertEqual(calls_at(runner, "S7s-1", "POST /v1/sets/review"), [])
        self.assertEqual(calls_at(runner, "S7s-1", "GET %s" % T.SANDBOX_ALLOWANCE_ROUTE)[0].status, 200, "the allowance is read first, never a constant")
        self.assertEqual(double.solana.transfers, [])
        for station in ("S5s", "S6s", "S7s-2", "S7s-3"):
            self.assertEqual(outcomes[station].outcome, H.PASS, outcomes[station].line)
        self.assertIn("one lamport (the book names no SOL amount; the belt is judged at the door before any figure matters)", outcomes["S7s-2"].line)
        self.assertEqual([(f.station, f.probe) for f in runner.findings], [("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")])

    def test_on_the_one_dollar_book_as_t24_left_it_there_is_no_room_for_any_figure(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with unittest.mock.patch.object(A, "SOLANA_PAYMENT_SOL", SOL_FIGURE):
            outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S7s-1"].outcome, H.FAILED_PREREQUISITE, outcomes["S7s-1"].line)
        self.assertIn(T.NO_ROOM_UNDER_THE_DOLLAR_SENTENCE % ("arbitrum", "US$1.00", "US$0.20", "US$1.20"), outcomes["S7s-1"].line)
        self.assertEqual(len(calls_at(runner, "S7s-1", "POST /v1/sets/review")), 1, "the review priced it; the judgment stopped before any creation")
        self.assertEqual(calls_at(runner, "S7s-1", "POST /v1/sets"), [])
        self.assertEqual(double.solana.transfers, [])

    def test_an_allowance_short_of_the_payment_stops_s7s_1_in_the_estates_words(self):
        double = EstateDouble(sandbox_allowance_usd_cents=90)  # the USDC book takes eighty cents; ten are left, and the SOL payment is worth twenty
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S7s-1"].outcome, H.FAILED_PREREQUISITE, outcomes["S7s-1"].line)
        self.assertIn(T.ALLOWANCE_SHORT_SENTENCE % ("Sandbox allowance: US$0.10 of US$0.90 left", "US$0.20"), outcomes["S7s-1"].line)
        self.assertEqual(calls_at(runner, "S7s-1", "POST /v1/sets"), [])
        self.assertEqual(double.solana.transfers, [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheWaitForTheOwnersSol(unittest.TestCase):
    """Spec T29 §0a.3: the first wallet must hold the payment plus the reserve; the harness reads the estate's road and waits under --funds-wait, then records itself waiting."""

    def test_a_wallet_the_owner_has_not_funded_is_waited_for_and_nothing_is_sent(self):
        double = EstateDouble(solana_wallet_lamports=0)
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        wallets = solana_wallets_of(double)
        self.assertEqual(outcomes["S7s-1"].outcome, H.FAILED_PREREQUISITE, outcomes["S7s-1"].line)
        self.assertIn(T.WAITING_FOR_SOL_SENTENCE % (wallets[0]["address"], "0 SOL", "0.002 SOL", "0.01 SOL", "0.012 SOL", 180), outcomes["S7s-1"].line)
        self.assertEqual(len(calls_at(runner, "S7s-1", "POST %s" % T.REFRESH_ROUTE)), 13, "one reading, then twelve more under the default --funds-wait of 180 s every 15 s")
        self.assertEqual(calls_at(runner, "S7s-1", "POST /v1/sets/review"), [])
        self.assertEqual(double.solana.transfers, [])
        self.assertEqual(outcomes["S7s-3"].outcome, H.PASS, outcomes["S7s-3"].line)
        self.assertIn("wallet 2 holds 0 SOL", outcomes["S7s-3"].line)

    def test_funds_wait_bounds_the_readings(self):
        double = EstateDouble(solana_wallet_lamports=0)
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link(), funds_wait=30)
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S7s-1"].outcome, H.FAILED_PREREQUISITE)
        self.assertEqual(len(calls_at(runner, "S7s-1", "POST %s" % T.REFRESH_ROUTE)), 3)
        self.assertIn("the wait of 30 s under --funds-wait ran out and nothing was sent", outcomes["S7s-1"].line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheClusterRefusesWithNoRuleNamed(unittest.TestCase):
    """Spec T29 §0a.5: BIS 100's party 0 answers "denied" and names no rule — recorded word for word, filed under the Group 100 findings."""

    def test_the_refusal_is_a_group_100_finding_not_the_estates(self):
        double = EstateDouble(solana_fault="denied")
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S7s-1"].outcome, H.FAIL, outcomes["S7s-1"].line)
        run = sets_carrying(double, "HH-S001")[0]
        self.assertEqual((run["instructions"][0]["status"], run["instructions"][0]["failureReason"]), ("rejected", T.PARTY_0_DENIED))
        group_100 = [f for f in runner.findings if f.station == "S7s-1" and f.probe.startswith(T.GROUP_100_FINDING_WORDS)]
        self.assertEqual(len(group_100), 1, [(f.station, f.probe) for f in runner.findings])
        self.assertEqual(group_100[0].probe, "Group 100: the cluster refused the Solana payment and named no rule")
        self.assertIn("BIS 100's party 0 answered \"%s\" — the rule is unnamed; filed under the Group 100 findings, not the estate's (Spec T29 §0a.5)" % T.PARTY_0_DENIED, group_100[0].said)
        self.assertIn("the instruction is rejected (%s)" % T.PARTY_0_DENIED, outcomes["S7s-1"].line)
        self.assertEqual(double.solana.transfers, [], "nothing left the wallet")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheSolanaPayeeKeyIsIgnored(unittest.TestCase):
    """Spec T29 §0a.2: SOLANA_PAYEE in payee.env, where present, is ignored, and the report says so; the payee is the harness's own second wallet."""

    def test_the_key_is_ignored_and_said(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        store = os.path.join(tmp, "store")
        elsewhere = solana_address_for_tests("an address outside the estate")
        file_the_owner_payee(store, text="%s=%s\n%s=%s\n%s=%s\n" % (T.OWNER_PAYEE_ADDRESS_KEY, OWNER_WALLET_FOR_TESTS, T.OWNER_PAYEE_CHAIN_KEY, T.PAYEE_CHAIN, T.SOLANA_PAYEE_KEY, elsewhere))
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        wallets = solana_wallets_of(double)
        self.assertEqual(outcomes["S6s"].outcome, H.PASS, outcomes["S6s"].line)
        self.assertIn(T.SOLANA_PAYEE_IGNORED_SENTENCE, runner.notes["S6s"])
        self.assertIn("SOLANA_PAYEE in payee.env is present and ignored (Spec T29 §0a.2)", outcomes["S6s"].line)
        self.assertEqual(runner.facts["solana"]["payee"]["address"], wallets[1]["address"])
        self.assertEqual([t["to"] for t in double.solana.transfers], [wallets[1]["address"]])
        self.assertNotIn(elsewhere, json.dumps([c.sent for c in runner.calls], default=str), "the address outside the estate is never sent anywhere")
        self.assertNotIn(elsewhere, " ".join(o.line for o in outcomes.values()) + " ".join(n for notes in runner.notes.values() for n in notes), "nor printed")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheSponsorTopsUpInTheDouble(unittest.TestCase):
    """
    The double's own top-up arm (Spec AER360-SOL-114 §3.6), which the harness never reaches because it waits for the payment plus the reserve
    first (Spec T29 §0a.3): a wallet short of the reserve at the moment of execution has the sponsor's transfer confirmed first, charged to the gas
    account in dollars, and the trail's signing row carries the top-up's record.
    """

    def test_a_wallet_short_of_the_reserve_is_topped_up_first_and_the_debit_is_recorded(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        with the_solana_book():
            outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(outcomes["S7s-1"].outcome, H.PASS, outcomes["S7s-1"].line)
        payer, payee = solana_wallets_of(double)
        double.solana.lamports[payer["address"]] = 11_000_000  # 0.011 SOL: the payment and the reserve need 0.012
        clerk = runner.clerk()
        before = double.platform.balance(double.aap_account_id)["available_usd_cents"]
        row = {"payeeAddressId": runner.facts["solana"]["payee"]["address_id"], "asset": "SOL", "chain": "solana", "amountMinor": str(SOL_LAMPORTS), "invoiceRef": "HH-S003"}
        created = runner.request(clerk, "POST", "/v1/sets", {"pays": [row], "duplicatesAcknowledged": False, "walletId": payer["walletId"], "idempotencyKey": "test-top-up", "reference": "top-up"}, "test")
        self.assertEqual(created.status, 201, created.text)
        set_id = created.json["set"]["id"]
        self.assertEqual(runner.request(clerk, "POST", "/v1/sets/%s/submit" % set_id, {}, "test").json["status"], "approved")
        executed = runner.request(clerk, "POST", "/v1/sets/%s/execute" % set_id, {}, "test")
        self.assertTrue(executed.ok, executed.text)
        run = double.sets[set_id]
        self.assertEqual(run["instructions"][0]["status"], "confirmed")
        signing = next(r for r in double.trail if r.get("subject_id") == run["instructions"][0]["id"] and r["action"] == T.INSTRUCTION_SIGNING)["detail"]
        top_up = signing["topUp"]
        self.assertEqual((top_up["reserveLamports"], top_up["debitUsdCents"], top_up["debit"], top_up["deduped"], top_up["sentReported"]), (str(T.FEE_RESERVE_LAMPORTS), 10, "US$0.10", False, True))
        self.assertEqual(len(T.base58_decode(top_up["signature"])), T.SIGNATURE_BYTES)
        self.assertEqual(before - double.platform.balance(double.aap_account_id)["available_usd_cents"], 10, "the sponsor's 0.001 SOL at US$100.00 a SOL, charged to the gas account")
        self.assertEqual(double.solana.balance_of(payee["address"]), 2 * SOL_LAMPORTS)


class TheDryRun(unittest.TestCase):
    def test_the_five_stations_print_their_calls_in_their_places(self):
        lines = H.dry_lines()
        stations = []
        for line in lines:
            station = line.split(" — ", 1)[0]
            if station not in stations:
                stations.append(station)
        self.assertEqual(stations, [s for s, _ in H.STATIONS], "every station prints, the Solana five in their places")
        s5s = [l for l in lines if l.startswith("S5s — ")]
        self.assertEqual(len(s5s), 8)
        self.assertIn('S5s — POST /v1/workspace/wallets/options {"whose": "estate", "chain": "solana"} (as Harriet Founder) — only where no Solana wallet stands → expect 200', s5s[1])
        s7s1 = [l for l in lines if l.startswith("S7s-1 — ")]
        self.assertEqual(len(s7s1), 16)
        self.assertIn("[book] aer360_answers.SOLANA_PAYMENT_SOL → the owner's figure in SOL, written in the book by him (the brief writes none, Spec T29 §0a.3)", s7s1[1])
        self.assertIn('"amountMinor": "<lamports of the book\'s SOL amount, aer360_answers.SOLANA_PAYMENT_SOL: the owner\'s figure>"', s7s1[5])
        self.assertTrue(any("never a node of the harness's own" in l for l in s7s1))
        self.assertTrue(any(T.PARTY_0_DENIED in l for l in s7s1), "the dry run names the cluster's unnamed rule")
        s7s2 = [l for l in lines if l.startswith("S7s-2 — ")]
        self.assertEqual(len(s7s2), 3)
        self.assertIn("422 WALLET_CURVE_MISMATCH", s7s2[1])
        self.assertEqual(len([l for l in lines if l.startswith("S7s-3 — ")]), 2)
        s6s = [l for l in lines if l.startswith("S6s — ")]
        self.assertEqual(len(s6s), 12)
        self.assertIn("SOLANA_PAYEE, where present, is ignored", s6s[0])
        for line in lines:
            self.assertNotIn(OWNER_WALLET_FOR_TESTS, line)

    def test_the_dry_run_prints_the_placeholder_and_never_a_figure(self):
        """The printer reads no book figure and no file: the SOL amount is the placeholder, whatever the book holds, so the fixture carries no figure of anyone's."""
        with unittest.mock.patch.object(A, "SOLANA_PAYMENT_SOL", "0.003"):
            lines = H.dry_lines()
        self.assertFalse(any("0.003" in l or "3000000" in l for l in lines))
        self.assertTrue(all("<lamports of the book's SOL amount, aer360_answers.SOLANA_PAYMENT_SOL: the owner's figure>" in l for l in lines if "/v1/sets" in l and '"asset": "SOL"' in l))


if __name__ == "__main__":
    unittest.main()
