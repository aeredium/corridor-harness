"""
Spec T14 (22 September 2026, amended 22:35; built 24 September 2026): the harness pays in cents, funds Harness Holdings from Harness Treasury — a
second sandbox workspace whose key lives only in the enclave — credits a gas account through the platform's admin credit road only on the review's
GAS_SHORTFALL (as Spec T26 reads T14's "as the sandbox may"),
proves the gas refusal (S7a), and S7 passes with money that moved; S10 counts the money to the cent. Each test here was red on main.

The double is the estate at AER 360 Spec 104 beside the platform at Spec 154 (tests/test_aer360_double.py): two workspaces on one estate, sharing
the platform's gas ledger (PlatformDouble, whose one road on the wire is the admin credit road) and the payment chain's USDC (UsdcChainDouble, whose
public RPC answers balanceOf). Harness Holdings holds no USDC and no gas; Harness Treasury holds the US$100.00 Bear funded it with and no gas.

Spec T24 (3 October 2026): on a real chain — and the double's chain is `arbitrum` — the book is one dollar (0.50, 0.01 and 0.49) and every payment goes
to the owner's own wallet, which the tests file in the store's payee.env as OWNER_WALLET_FOR_TESTS; the Treasury's shortfall is US$1.00, and under the
book's US$10.00 hold no payment of the three is held, so the signers are not asked.

Spec T26 (4 October 2026, the owner's ruling: "That is stupid. Why is that happening? It's certainly not my rule. So, undo that now."): gas is
credited only when the review says the account is short, never on a standing order. The double's two gas accounts start at zero unless a test says
otherwise (`holdings_gas_cents`, `treasury_gas_cents`), so T14's scenarios are the ones where a review refuses GAS_SHORTFALL and one credit cures it;
the scenarios of T26 §4 are below — the sandbox's two balances of 4 October (US$99.71 and US$119.95), under which nothing is credited, no admin call
is made and admin.env is never opened.
"""
import json
import os
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import (  # noqa: E402
    AAP_ACCOUNT_ID, EstateDouble, OWNER_WALLET_FOR_TESTS, PLATFORM_ADMIN_INVALID, PLATFORM_BASE, PlatformDouble, TREASURY_ACCOUNT_ID, UsdcChainDouble, runner_on,
)

SHORTFALL_MINOR = 1000000  # the three payments together, in USDC minor units: 0.50 + 0.01 + 0.49 — the one-dollar book of Spec T24 on a real chain
U3_SENTENCE = "Your gas account holds US$0.00. This set needs at most US$1.20 of gas. Nothing was sent. Buy gas below."
# Spec T26 §2: what a payment's line says where its review refused GAS_SHORTFALL and one credit cured it — the gate's sentence for one payment of this double
CURE_CLAUSE = "the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.); gas credited and the review asked again"


def run_against(tmp=None, admin_env=True, said=None, **double_kwargs):
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tmp or tempfile.mkdtemp(), invite=double.mint_founder_link(), admin_env=admin_env, said=said)
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheTreasuryPaysAndTheThreePaymentsLand(unittest.TestCase):
    """
    Holdings at US$0.00 and the Treasury at US$100.00, both gas accounts at zero (T14's double): the Treasury's review refuses GAS_SHORTFALL and one
    credit cures it, its one payment of US$1.00 lands, S7a is proved, P1's review refuses and one credit cures it, the three payments land, and S10
    counts — two cures, one per refusal, and no standing credit (Spec T26).
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.double, cls.runner, cls.outcomes = run_against(tmp=cls.tmp)
        cls.treasury = cls.double.treasury
        cls.holdings_wallet = cls.double.source_account
        cls.money = cls.runner.facts["money"]

    def test_the_treasury_pays_one_payment_of_one_set_to_holdings_address_approved_with_its_founders_passkey_and_landed(self):
        o = self.outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        record = self.money["treasury"]["payment"]
        self.assertEqual((record["key"], record["amount_minor"], record["payee"]), ("HT", SHORTFALL_MINOR, self.holdings_wallet))
        self.assertTrue(record["landed"], record["said"])
        self.assertEqual((record["status"], record["set_status"], record["approvals_required"]), ("confirmed", "settled", 1))
        self.assertEqual([(a["who"], a["status_after"], a["given"]) for a in record["approvals"]], [("Harriet Founder", "approved", 1)])
        founder = self.runner.treasury.people["harriet"]
        self.assertEqual(record["approvals"][0]["credential"], founder.credential_id, "the Treasury founder's own passkey approved it")
        self.assertIn(founder.credential_id, self.treasury.second_approvers, "seated at her charter's compile: C11 names the address her estate is opened under")
        self.assertNotEqual(founder.credential_id, self.runner.people["harriet"].credential_id, "a credential of the Treasury's own, not Holdings' founder's")
        # one set of one instruction, from the Treasury's wallet to Holdings' address, settled
        sets = list(self.treasury.sets.values())
        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0]["status"], "settled")
        self.assertEqual([(i["address"], i["amountMinor"], i["status"], i["isOneOff"]) for i in sets[0]["instructions"]], [(self.holdings_wallet.lower(), str(SHORTFALL_MINOR), "confirmed", True)])
        self.assertEqual(self.double.chain.transfers[0], {"from": self.treasury.source_account.lower(), "to": self.holdings_wallet.lower(), "minor": SHORTFALL_MINOR})
        # judged on the run's status, the userOpHash, the handleOps transaction hash and Holdings' balance before and after (§4)
        self.assertTrue(str(record["user_op_hash"]).startswith("0x") and str(record["tx_hash"]).startswith("0x"))
        self.assertEqual((record["balance_before"], record["balance_after"]), (0, SHORTFALL_MINOR))
        self.assertEqual(record["gas_debit_cents"], 31)
        # Spec T26 §2: the Treasury's gas account held nothing, so its review refused GAS_SHORTFALL; one credit cured it and the review was asked
        # again — said in the payment's own line, with the platform's figures, before the submit
        cure = self.runner.facts["gas_credits"][0]
        line = next(l for l in self.double.platform.lines if l["kind"] == "credit" and l["account_id"] == TREASURY_ACCOUNT_ID)
        self.assertEqual((cure["who"], cure["said"]), ("Harness Treasury", "Harness Treasury credited US$10.00 (line %s): balance US$10.00, available US$10.00" % line["id"]))
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$1.00: %s; %s; submitted: status pending_approval, approvalsRequired 1; Harriet Founder signed (1 of 1): approved; "
                      "landed (+US$1.00): instruction confirmed, run settled, userOpHash 0x" % (self.holdings_wallet, CURE_CLAUSE, cure["said"]), o.line)
        self.assertIn("payee US$0.00 → US$1.00, gas US$0.31", o.line)
        # the road, as the estate's own: the review (refused for want of gas), the review again after the cure, create, submit, challenge, approve, execute,
        # the register until terminal, the trail; the Treasury founder's calls are labelled with her workspace in Every call, so the two founders named
        # Harriet Founder are told apart
        routes = [c.route for c in self.runner.calls if c.station == "S7" and c.who == "Harriet Founder (Harness Treasury)" and c.path.startswith(("/v1/sets", "/v1/approvals", "/v1/export"))]
        set_id = record["set_id"]
        self.assertEqual(routes, ["POST /v1/sets/review", "POST /v1/sets/review", "POST /v1/sets", "POST /v1/sets/%s/submit" % set_id, "POST /v1/approvals/%s/challenge" % set_id,
                                  "POST /v1/approvals/%s/approve" % set_id, "POST /v1/sets/%s/execute" % set_id, "GET /v1/sets/%s" % set_id, "GET /v1/export/audit?limit=5000"])

    def test_the_treasury_founders_passkey_lives_under_its_own_folder_and_the_harness_holds_no_key_for_the_wallet(self):
        store = self.runner.store_dir
        self.assertEqual(sorted(os.listdir(os.path.join(store, T.TREASURY["client_id"]))), ["harriet.json"], "one founder passkey, nothing else")
        self.assertEqual(oct(os.stat(os.path.join(store, T.TREASURY["client_id"], "harriet.json")).st_mode & 0o777), "0o600")
        with open(os.path.join(store, T.TREASURY["client_id"], "harriet.json"), "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        self.assertEqual(stored["aap_credential_id"], self.runner.treasury.people["harriet"].credential_id)
        self.assertNotIn(self.treasury.source_account.lower(), json.dumps(stored).lower(), "the wallet's address is the estate's to answer; no key of the wallet is anywhere in the store")
        self.assertEqual(self.money["treasury"]["address"], self.treasury.source_account)
        self.assertIn("Harness Treasury: the Treasury founder enrolled by invitation; funding wallet: %s on double-stack-1" % self.treasury.source_account, self.outcomes["S7"].line)

    def test_s7a_proves_the_refusal_in_u3s_sentence_with_the_figures_the_harness_read_and_nothing_left(self):
        s7a = self.runner.facts["s7a"]
        self.assertEqual((s7a["verdict"], s7a["available"], s7a["ceiling"], s7a["sentence"], s7a["left"]), ("proved", 0, 120, U3_SENTENCE, []))
        self.assertEqual(s7a["detail"]["availableUsdCents"], "0")
        self.assertEqual(s7a["detail"]["payments"], "3")
        self.assertIn("S7a proved: the review refused GAS_SHORTFALL — \"%s\" — naming the US$0.00 the harness read and the gate's ceiling US$1.20; nothing left (no new run in the register; Holdings' USDC unchanged at US$1.00)" % U3_SENTENCE, self.outcomes["S7"].line)
        review = next(s for s in self.runner.evidence["S7"] if s["route"] == "POST /v1/sets/review" and str(s["expected"]).startswith("S7a:"))
        self.assertEqual(len(review["sent"]["pays"]), 3, "the set of three")
        self.assertEqual(review["result"], "refused as U3 says: %s" % U3_SENTENCE)
        self.assertEqual(T.gas_set_shortfall_sentence(0, 120), U3_SENTENCE)
        # S7a was proved on an account nothing of this run had credited (US$0.00): Holdings' one credit comes after it, at P1's review (Spec T26 §2)
        credits = [c for c in self.runner.calls if c.station == "S7" and "gas-account/credits" in c.path]
        reviews = [i for i, c in enumerate(self.runner.calls) if c.station == "S7" and c.route == "POST /v1/sets/review"]
        review_at = reviews[2]  # the Treasury's review, refused and asked again after its cure, then S7a's
        holdings_credit_at = next(i for i, c in enumerate(self.runner.calls) if AAP_ACCOUNT_ID in c.path and "gas-account/credits" in c.path)
        self.assertLess(review_at, holdings_credit_at, "S7a before Holdings' credit (Spec T14 §3; Spec T26: the credit is P1's cure)")
        self.assertEqual(len(credits), 2, "one cure per refusal: the Treasury's and Holdings'")

    def test_the_admin_credit_road_received_one_credit_per_workspace_with_the_reason_and_the_credential_was_never_printed(self):
        posts = self.double.platform.requests
        self.assertEqual([(r["method"], r["path"]) for r in posts], [("POST", T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID), ("POST", T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID)],
                         "the Treasury's cure first (its review refused), then Holdings' at P1's review, after S7a (Spec T26 §2)")
        # Spec T26 §2: each credit sits between the review that refused and the review asked again, and nothing else credits
        reviews = [i for i, c in enumerate(self.runner.calls) if c.station == "S7" and c.route == "POST /v1/sets/review"]
        self.assertEqual(len(reviews), 7, "the Treasury's twice, S7a's, P1's twice, P2's, P3's")
        treasury_credit_at = next(i for i, c in enumerate(self.runner.calls) if TREASURY_ACCOUNT_ID in c.path and "gas-account/credits" in c.path)
        holdings_credit_at = next(i for i, c in enumerate(self.runner.calls) if AAP_ACCOUNT_ID in c.path and "gas-account/credits" in c.path)
        self.assertTrue(reviews[0] < treasury_credit_at < reviews[1], "the Treasury's cure between its two reviews")
        self.assertTrue(reviews[3] < holdings_credit_at < reviews[4], "Holdings' cure between P1's two reviews")
        for post in posts:
            body = json.loads(post["body"])
            self.assertEqual(body["amount_usd_cents"], T.GAS_CREDIT_USD_CENTS)
            self.assertEqual(body["reason"], "sandbox run %s" % self.runner.run_stamp)
            self.assertEqual(post["headers"]["authorization"], "Bearer %s" % self.double.platform.admin_key)
        self.assertEqual([json.loads(p["body"])["idempotency_key"] for p in posts],
                         ["aer360-harness-%s-harness-treasury-gas-1" % self.runner.run_stamp, "aer360-harness-%s-harness-holdings-gas-1" % self.runner.run_stamp],
                         "one key per credit of the run for a workspace: a second credit carries its own ordinal, so the platform dedupes neither")
        self.assertEqual([(a["type"], a["outcome"], a["account_id"], a["amount_usd_cents"]) for a in self.double.platform.audit],
                         [("gas.credited_by_admin", "credited", TREASURY_ACCOUNT_ID, 1000), ("gas.credited_by_admin", "credited", AAP_ACCOUNT_ID, 1000)])
        records = self.runner.facts["gas_credits"]
        self.assertEqual([(r["who"], r["outcome"], r["status"], r["balance_after"]["available_usd_cents"]) for r in records],
                         [("Harness Treasury", "credited", 201, 1000), ("Harness Holdings", "credited", 201, 1000)])
        holdings_line = next(l for l in self.double.platform.lines if l["kind"] == "credit" and l["account_id"] == AAP_ACCOUNT_ID)
        self.assertEqual(records[1]["said"], "Harness Holdings credited US$10.00 (line %s): balance US$10.00, available US$10.00" % holdings_line["id"])
        self.assertIn("P1 (0.50 USDC to %s, the owner's wallet, expected to proceeds to approval): %s; %s; submitted: status approved" % (OWNER_WALLET_FOR_TESTS, CURE_CLAUSE, records[1]["said"]),
                      self.outcomes["S7"].line, "the cure is said in P1's own line")
        report = self.runner.report()
        self.assertNotIn(self.double.platform.admin_key, report, "the admin key travels in no record")
        self.assertNotIn(self.double.platform.admin_key, self.outcomes["S7"].line)
        self.assertNotIn("authorization", json.dumps([c.sent for c in self.runner.calls]).lower(), "the bearer rides in a header, which is never recorded")
        self.assertEqual(self.money["holdings"]["credited"], 1000)
        self.assertEqual(self.money["treasury"]["credited"], 1000)

    def test_the_three_payments_land_with_the_gas_lines_and_the_signers_press_in_the_specs_order(self):
        o = self.outcomes["S7"]
        sets = self.runner.facts["sets"]
        for key, amount in (("P1", 500000), ("P2", 10000), ("P3", 490000)):
            record = sets[key]
            self.assertTrue(record["landed"], record["said"])
            self.assertEqual((record["status"], record["set_status"], record["amount_minor"]), ("confirmed", "settled", amount))
            self.assertEqual(record["balance_after"] - record["balance_before"], amount, key)
            self.assertEqual((record["gas_debit_cents"], record["gas_debit"]), (31, "US$0.31"))
            self.assertTrue(str(record["user_op_hash"]).startswith("0x") and str(record["tx_hash"]).startswith("0x"))
            self.assertEqual(record["payee"], OWNER_WALLET_FOR_TESTS, "Spec T24: every payment on a real chain goes to the owner's wallet")
        self.assertEqual([a["who"] for a in sets["P1"]["approvals"]], [], "the estate asked no signature within the hold for a listed payee")
        # Spec T24: the one-dollar book is under the US$10.00 hold throughout, and HH-0001 paid the owner's wallet moments before HH-0002, so Spec 69
        # holds nothing — the estate asks no signature for any of the three, and the signers are never pressed
        self.assertEqual([(a["who"], a["refusal_code"], a["status_after"]) for a in sets["P2"]["approvals"]], [],
                         "the one-off destination is already paid by this estate (HH-0001), so Spec 69's hold is not provable and the estate asked no signature")
        self.assertEqual(sets["P2"]["approvals_required"], 0)
        self.assertEqual(sets["P3"]["approvals"], [], "US$0.49 is under the hold")
        self.assertEqual(o.line.count("gas US$0.31"), 4, "the Treasury's payment and the three, each with its gas debit beside it")
        self.assertEqual(len(self.double.chain.transfers), 4)
        self.assertEqual(self.double.chain.balance_of(self.holdings_wallet), 0, "Holdings paid out exactly what it received")
        self.assertEqual(self.double.chain.balance_of(OWNER_WALLET_FOR_TESTS), 1000000, "the owner's wallet received the whole dollar")
        self.assertEqual(self.double.chain.balance_of(T.address("NORTHWIND_ETHEREUM")), 0, "no derived address was paid on a real chain (Spec T24)")
        self.assertEqual(self.double.chain.balance_of(T.address("CONTOSO_ETHEREUM")), 0)
        # the payees' balances were read from the chain's public RPC, before and after, against the contract the estate names
        rpc_calls = [c for c in self.runner.calls if c.station == "S7" and c.path == T.public_rpc_url(T.PAYEE_CHAIN)]
        self.assertEqual(len(rpc_calls), 6)
        self.assertTrue(all(c.sent["params"][0]["to"] == self.double.chain.token for c in rpc_calls))
        self.assertEqual(self.runner.facts["usdc_token"], self.double.chain.token)
        self.assertEqual(self.double.chain.calls[0]["body"]["params"][0]["data"], T.balance_of_call_data(OWNER_WALLET_FOR_TESTS))
        self.assertEqual(self.outcomes["S11"].line, "the attacker: 17 probe(s), 1 not made, 1 finding(s)",
                         "the settled runs answer S11's probes as refusals; the hold probe is not made on the one-dollar book, where P3 is under the hold (Spec T24)")

    def test_s10_counts_the_money_to_the_cent(self):
        notes = [n for n in self.runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)")]
        # Spec T26 §3.4: each workspace's gas account is reconciled — the credits made in this run less its debits equals the movement, to the cent
        self.assertEqual(notes, ["money moved (Spec T14 §5): Harness Treasury's USDC US$100.00 → US$99.00 (paid US$1.00); Harness Treasury's gas account US$0.00 → US$9.69 (credited US$10.00; gas debit US$0.31 on its payment); "
                                 "Harness Holdings' USDC US$0.00 → US$0.00 (received US$1.00; the three payments US$1.00, of which US$1.00 landed); "
                                 "Harness Holdings' gas account US$0.00 → US$9.07 (credited US$10.00; gas debits US$0.93 over 3 of 3 payments that landed); "
                                 "Harness Holdings' USDC fell by US$1.00 and its gas account by US$0.93, US$1.93 in all — exactly the payments that landed (US$1.00) plus their gas (US$0.93): every pair reconciles to the cent"])
        self.assertEqual([f.probe for f in self.runner.findings if f.probe.startswith("money moved")], [])
        self.assertEqual(self.money["treasury"]["usdc_after"], 99000000)
        self.assertEqual(self.money["holdings"]["gas_after"], 907)
        self.assertEqual(self.double.platform.balance(AAP_ACCOUNT_ID), {"balance_usd_cents": 907, "reserved_usd_cents": 0, "available_usd_cents": 907})
        self.assertEqual(self.double.platform.balance(TREASURY_ACCOUNT_ID), {"balance_usd_cents": 969, "reserved_usd_cents": 0, "available_usd_cents": 969})
        # the findings are the two the estate's own code makes, as before
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings], [("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")])

    def test_the_report_names_the_treasury_and_the_money_and_reads_back(self):
        report = self.runner.report()
        self.assertIn("Harness Treasury: funding wallet %s — the float Bear funds with USDC on arbitrum, once; it pays Harness Holdings' shortfall through the estate's own road, and the harness holds no key for it (Spec T14)." % self.treasury.source_account, report)
        self.assertIn("The asset: the three payments together need US$1.00 of USDC; Harness Treasury pays Harness Holdings the shortfall through the estate's own road (Spec T14); the harness never mints the asset and holds no key. "
                      "On arbitrum every payment goes to the owner's wallet, %s, read from ~/.aer360-harness/payee.env and never from the repository; the book there is one dollar in all (Spec T24)." % OWNER_WALLET_FOR_TESTS, report)
        self.assertIn("| POST %s%s |" % (PLATFORM_BASE, T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID), report, "the admin credit is in Every call")
        self.assertIn("| POST %s |" % T.public_rpc_url(T.PAYEE_CHAIN), report)
        path = self.runner.write_report()
        read = H.read_report(path)
        self.assertEqual(read["outcomes"]["S7"], "pass")
        self.assertEqual(len(read["outcomes"]), len(H.STATIONS))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheTreasuryIsShort(unittest.TestCase):
    def test_s7_fails_with_the_sentence_and_nothing_is_sent(self):
        double, runner, outcomes = run_against(treasury_usdc_cents=50)  # fifty cents: short of the one-dollar book (Spec T24)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)  # Spec T19 §3: the stop is a missing prerequisite, named in the line
        sentence = T.TREASURY_SHORT_SENTENCE % ("US$0.50", "US$1.00", double.treasury.source_account, "arbitrum")
        self.assertEqual(sentence, "Harness Treasury holds US$0.50; the run needs US$1.00; fund %s on arbitrum" % double.treasury.source_account)
        self.assertTrue(o.line.endswith("%s (the three payments need US$1.00 and Harness Holdings holds US$0.00); nothing was sent" % sentence), o.line)
        self.assertIn("payments: %s — " % H.TREASURY_SHORT, o.line, "the summary line names the scenario and the missing prerequisite")
        self.assertFalse(any(sentence in n for n in runner.notes["S7"]), "Spec T19 §3: the note beside the stop is gone; its figures travel in the line")
        self.assertEqual([c.route for c in runner.calls if c.station == "S7" and c.method == "POST" and c.path.startswith("/v1/sets")], [], "nothing was submitted")
        self.assertEqual(double.platform.requests, [], "no gas was credited either")
        self.assertEqual(double.chain.transfers, [])
        self.assertEqual(double.chain.balance_of(double.treasury.source_account), 500000)
        self.assertTrue(any(n.startswith("the money was not counted: S7 did not read the balances before and after") for n in runner.notes["S10"]))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S7aAgainstDoublesThatAnswerDifferently(unittest.TestCase):
    def test_a_refusal_naming_other_figures_fails_s7_naming_it(self):
        double, runner, outcomes = run_against(gas_refusal_names_other_figures=True)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        s7a = runner.facts["s7a"]
        self.assertEqual(s7a["verdict"], "failed")
        self.assertIn("S7a failed: the refusal names other figures — it says 'Your gas account holds US$0.01. This set needs at most US$2.20 of gas. Nothing was sent. Buy gas below.'; the harness read US$0.00 available, and the gate's detail says available 1, ceiling 220", o.line)
        # the payments still ran and landed: S7a's failure is one failure among the proofs, and the report carries it beside them
        self.assertTrue(all(runner.facts["sets"][k]["landed"] for k in ("P1", "P2", "P3")))

    def test_a_payment_that_left_behind_the_refusal_fails_s7_naming_it(self):
        double, runner, outcomes = run_against(review_refuses_but_pays=True)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        s7a = runner.facts["s7a"]
        self.assertEqual(s7a["verdict"], "failed")
        self.assertEqual(len(s7a["left"]), 2, s7a["left"])
        self.assertTrue(s7a["left"][0].startswith("the review created run(s) set-"), s7a["left"])
        self.assertEqual(s7a["left"][1], "Harness Holdings' USDC moved from US$1.00 to US$0.00")
        self.assertIn("S7a failed: a payment left — the review created run(s) set-", o.line)
        self.assertIn("; Harness Holdings' USDC moved from US$1.00 to US$0.00", o.line)



S7A_FINDING = "Harness Holdings' gas account holds US$99.71, and this set needs at most US$1.20; the gate admitted the set, which is right"


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class GasIsCreditedOnlyWhenShort(unittest.TestCase):
    """
    Spec T26 §4: the double starts with the two balances the sandbox held on 4 October 2026 — Holdings' gas at US$99.71, the Treasury's at
    US$119.95 — and no admin credential is filed (`admin_env=False`): S7 pays all three, makes no admin call, never opens admin.env, S7a reads the
    finding, S10 reconciles. The run that fell on this (`aer360-harness-2026-10-04-135413.md`) failed S7 on a credit nobody needed.
    """

    @classmethod
    def setUpClass(cls):
        cls.said = []
        cls.double, cls.runner, cls.outcomes = run_against(admin_env=False, holdings_gas_cents=9971, treasury_gas_cents=11995, said=cls.said)

    def test_s7_pays_all_three_makes_no_admin_call_and_never_opens_admin_env(self):
        o = self.outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(self.double.platform.requests, [], "no admin call: the accounts cover the sets")
        self.assertEqual(self.runner.facts["gas_credits"], [])
        self.assertEqual((self.runner.facts["money"]["holdings"]["credited"], self.runner.facts["money"]["treasury"]["credited"]), (0, 0))
        self.assertFalse(os.path.exists(self.runner.admin_env_path), "admin_env=False: nothing is filed, and nothing missed it")
        self.assertIsNone(self.runner.admin_env, "the credential was never read")
        self.assertEqual([n for n in self.runner.notes["S7"] if T.ADMIN_ENV_FILE in n or "credit" in n], [], "the file is not read and nothing is said of it (Spec T26 §3.3)")
        self.assertNotIn(T.NO_GAS_CREDIT_ROAD_SENTENCE, o.line)
        self.assertNotIn("gas credited", o.line)
        sets = self.runner.facts["sets"]
        self.assertTrue(all(sets[k]["landed"] for k in ("P1", "P2", "P3")), o.line)
        self.assertTrue(self.runner.facts["money"]["treasury"]["payment"]["landed"])
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$1.00: submitted: status pending_approval, approvalsRequired 1;" % self.double.source_account, o.line, "no cure clause: nothing was refused")
        # Spec T26 §3.4: S7's line carries both workspaces' gas balances before and after
        self.assertIn("before: Harness Holdings holds US$0.00 of USDC on arbitrum; Harness Treasury holds US$100.00 of USDC on arbitrum; Harness Holdings's Gas account: US$99.71 (balance US$99.71, reserved US$0.00); "
                      "Harness Treasury's Gas account: US$119.95 (balance US$119.95, reserved US$0.00)", o.line)
        self.assertIn("after: Harness Holdings holds US$0.00 of USDC on arbitrum; Harness Treasury holds US$99.00 of USDC on arbitrum; Harness Holdings's Gas account: US$98.78 (balance US$98.78, reserved US$0.00); "
                      "Harness Treasury's Gas account: US$119.64 (balance US$119.64, reserved US$0.00)", o.line)
        self.assertEqual(self.double.platform.balance(AAP_ACCOUNT_ID)["balance_usd_cents"], 9878, "US$99.71 less three debits of US$0.31: the balance is spent at cents a run, never moved")
        self.assertEqual(self.double.platform.balance(TREASURY_ACCOUNT_ID)["balance_usd_cents"], 11964)
        self.assertEqual(len([c for c in self.runner.calls if c.station == "S7" and c.route == "POST /v1/sets/review"]), 5, "the Treasury's, S7a's and the three payments', each asked once")

    def test_s7a_is_a_finding_under_s7_never_a_fail_and_names_both_figures(self):
        s7a = self.runner.facts["s7a"]
        self.assertEqual((s7a["verdict"], s7a["available"], s7a["ceiling"]), ("not provable", 9971, 120))
        self.assertEqual(s7a["said"], "%s: %s" % (T.S7A_NOT_PROVABLE_PROBE, S7A_FINDING))
        self.assertEqual(s7a["said"], "S7a not provable this run: " + S7A_FINDING)
        self.assertIn("; S7a not provable this run: %s; " % S7A_FINDING, self.outcomes["S7"].line)
        self.assertEqual([(f.station, f.probe, f.said, f.route) for f in self.runner.findings if f.station == "S7"],
                         [("S7", "S7a not provable this run", S7A_FINDING, "POST /v1/sets/review")])
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings],
                         [("S7", "S7a not provable this run"), ("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")])
        self.assertIn("  S7 finding: S7a not provable this run: %s" % S7A_FINDING, self.said, "said on the terminal as a finding, not as a fail")
        self.assertFalse(any(l.startswith("S7 — fail") for l in self.said), [l for l in self.said if l.startswith("S7 —")])
        report = self.runner.report()
        s7 = report.split("## S7 — Payments", 1)[1].split("## S8 — ", 1)[0]
        self.assertIn("### Findings\n\n- **S7a not provable this run** — %s\n  - Route: POST /v1/sets/review" % S7A_FINDING, s7)
        self.assertIn("Findings in this run: 3 (S7 1, S10 1, S11 1).", report)
        self.assertNotIn("Findings under S10 and S11", report)
        read = H.read_report(self.runner.write_report())
        self.assertEqual(read["outcomes"]["S7"], "pass")
        self.assertIn({"station": "S7", "probe": "S7a not provable this run", "said": S7A_FINDING}, read["findings"], "the finding reads back for the next run's last-run column")

    def test_s10_reconciles_each_gas_account_with_nothing_credited(self):
        notes = [n for n in self.runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)")]
        self.assertEqual(notes, ["money moved (Spec T14 §5): Harness Treasury's USDC US$100.00 → US$99.00 (paid US$1.00); Harness Treasury's gas account US$119.95 → US$119.64 (credited US$0.00; gas debit US$0.31 on its payment); "
                                 "Harness Holdings' USDC US$0.00 → US$0.00 (received US$1.00; the three payments US$1.00, of which US$1.00 landed); "
                                 "Harness Holdings' gas account US$99.71 → US$98.78 (credited US$0.00; gas debits US$0.93 over 3 of 3 payments that landed); "
                                 "Harness Holdings' USDC fell by US$1.00 and its gas account by US$0.93, US$1.93 in all — exactly the payments that landed (US$1.00) plus their gas (US$0.93): every pair reconciles to the cent"])
        self.assertEqual([f.probe for f in self.runner.findings if f.probe.startswith("money moved")], [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class HoldingsIsShortAndTheTreasuryIsNot(unittest.TestCase):
    """Spec T26 §4: Holdings' gas at zero, the Treasury's covering — S7a proved, P1's review refuses GAS_SHORTFALL, exactly one credit sized by the ceiling, the review passes, the payments land."""

    def test_exactly_one_credit_is_made_at_the_first_payments_review_and_sized_by_its_ceiling(self):
        double, runner, outcomes = run_against(treasury_gas_cents=11995)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual((runner.facts["s7a"]["verdict"], runner.facts["s7a"]["available"], runner.facts["s7a"]["ceiling"]), ("proved", 0, 120))
        posts = [(json.loads(r["body"])["amount_usd_cents"], r["path"], json.loads(r["body"])["idempotency_key"]) for r in double.platform.requests]
        self.assertEqual(posts, [(1000, T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID, "aer360-harness-%s-harness-holdings-gas-1" % runner.run_stamp)], "one cure, n counting the credits actually made")
        self.assertEqual((runner.facts["money"]["holdings"]["credited"], runner.facts["money"]["treasury"]["credited"]), (1000, 0))
        self.assertEqual([(c["who"], c["amount_usd_cents"], c["outcome"]) for c in runner.facts["gas_credits"]], [("Harness Holdings", 1000, "credited")])
        self.assertEqual(H.Runner.gas_credit_for(40), 1000, "the refusal's ceiling of US$0.40 asks for U3's ten dollars")
        # the cure sits between P1's refused review and the review asked again, before P1 is created; the Treasury's review was not refused
        routes = [("ADMIN " + c.path) if "gas-account/credits" in c.path else c.route for c in runner.calls if c.station == "S7"]
        reviews = [i for i, r in enumerate(routes) if r == "POST /v1/sets/review"]
        self.assertEqual(len(reviews), 6, "the Treasury's once, S7a's, P1's twice, P2's, P3's")
        credit_at = next(i for i, r in enumerate(routes) if r.startswith("ADMIN ") and r.endswith(T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID))
        self.assertTrue(reviews[2] < credit_at < reviews[3], routes)
        self.assertLess(credit_at, routes.index("POST /v1/sets", reviews[2]), "credited before P1's run is created")
        cure = runner.facts["gas_credits"][0]
        self.assertIn("P1 (0.50 USDC to %s, the owner's wallet, expected to proceeds to approval): %s; %s; submitted: status approved, approvalsRequired 0; landed (+US$0.50)" % (
            OWNER_WALLET_FOR_TESTS, CURE_CLAUSE, cure["said"]), o.line)
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$1.00: submitted: status pending_approval" % double.source_account, o.line, "the Treasury's account covered its review: no cure")
        self.assertTrue(all(runner.facts["sets"][k]["landed"] for k in ("P1", "P2", "P3")))
        self.assertIsNotNone(runner.admin_env, "the credential was read when the credit was about to be made, and kept")
        self.assertEqual([n for n in runner.notes["S7"] if T.ADMIN_ENV_FILE in n], [], "a credential that is filed is read without a word")
        note = next(n for n in runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)"))
        self.assertIn("Harness Treasury's gas account US$119.95 → US$119.64 (credited US$0.00; gas debit US$0.31 on its payment); ", note)
        self.assertIn("Harness Holdings' gas account US$0.00 → US$9.07 (credited US$10.00; gas debits US$0.93 over 3 of 3 payments that landed)", note)
        self.assertTrue(note.endswith("every pair reconciles to the cent"), note)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class ThePlatformDidNotCreditWhatItSaid(unittest.TestCase):
    """Spec T26 §3.1: a second GAS_SHORTFALL after the credit fails S7 naming both figures — the platform's and the gate's."""

    def test_a_second_gas_shortfall_after_the_credit_fails_s7_naming_both_figures(self):
        double, runner, outcomes = run_against(platform=PlatformDouble(credit_is_hollow=True), treasury_gas_cents=11995)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)  # the platform's road failing, not a missing prerequisite
        sentence = ("the review refused GAS_SHORTFALL again after the credit: the platform said Harness Holdings was credited US$10.00 and its gas account held US$10.00 available, "
                    "and the review says the account holds US$0.00 — 'Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.' — "
                    "so the platform did not credit what it said it did")
        self.assertEqual(T.GAS_CREDIT_HOLLOW_SENTENCE % ("GAS_SHORTFALL", "Harness Holdings", "US$10.00", "US$10.00", "US$0.00",
                                                          "Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below."), sentence)
        self.assertTrue(o.line.endswith("; " + sentence), o.line)
        self.assertIn("S7a proved: the review refused GAS_SHORTFALL", o.line, "what S7 said before the stop travels with it")
        self.assertEqual(len(double.platform.requests), 1, "one credit, which the platform said it made")
        self.assertEqual([(c["who"], c["outcome"], c["balance_after"]["available_usd_cents"]) for c in runner.facts["gas_credits"]], [("Harness Holdings", "credited", 1000)])
        self.assertEqual(double.platform.balance(AAP_ACCOUNT_ID)["available_usd_cents"], 0, "the ledger holds nothing of it")
        self.assertEqual(double.sets, {}, "P1 was never created: the review refused twice")
        self.assertEqual(len(double.treasury.sets), 1, "the Treasury's payment landed before it")
        routes = [c.route for c in runner.calls if c.station == "S7" and c.route == "POST /v1/sets/review"]
        self.assertEqual(len(routes), 4, "the Treasury's, S7a's, P1's and P1's again — then the stop")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheAdminCreditRoad(unittest.TestCase):
    def test_the_file_absent_with_gas_at_zero_fails_s7_with_t14s_sentence_naming_the_refusal_that_needed_it(self):
        double, runner, outcomes = run_against(admin_env=False)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)  # Spec T19 §3: a stop is a missing prerequisite, named
        self.assertIn("payments: %s — " % H.NO_ADMIN_CREDENTIAL, o.line)
        self.assertTrue(o.line.endswith(T.NO_GAS_CREDIT_ROAD_SENTENCE), o.line)
        self.assertEqual(T.NO_GAS_CREDIT_ROAD_SENTENCE, "no gas credit road: the sandbox credits gas through the platform's admin road; file the credential in ~/.aer360-harness/admin.env")
        # Spec T26 §3.3: the sentence names the refusal that needed the credit, then T14's sentence
        self.assertTrue(o.line.endswith("; the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.), which a gas credit cures; %s" % T.NO_GAS_CREDIT_ROAD_SENTENCE), o.line)
        self.assertEqual(T.GAS_CURE_NEEDED_CLAUSE % ("GAS_SHORTFALL", "<U3's sentence>"), "the review refused GAS_SHORTFALL (<U3's sentence>), which a gas credit cures")
        self.assertTrue(any(n.endswith("is not filed: the gas credits below will fail with %r" % T.NO_GAS_CREDIT_ROAD_SENTENCE) for n in runner.notes["S7"]), runner.notes["S7"])
        self.assertEqual(double.platform.requests, [])
        self.assertEqual(double.chain.transfers, [], "the Treasury's payment needs gas first, so nothing left")
        self.assertEqual((double.treasury.sets, double.sets), ({}, {}), "the Treasury's run was reviewed, refused and never created; S7a was not reached")
        self.assertEqual(len([c for c in runner.calls if c.station == "S7" and c.route == "POST /v1/sets/review"]), 1, "the one review whose refusal needed the credit")
        self.assertIn("Harness Treasury holds US$100.00 of USDC on arbitrum", o.line, "the Treasury was brought in and the balances read before the cure stopped S7")

    def test_the_file_absent_with_gas_covering_passes_s7_and_the_file_is_never_opened(self):
        with unittest.mock.patch.object(H.Runner, "read_admin_env", side_effect=AssertionError("admin.env was opened on a run that needed no credit")):
            double, runner, outcomes = run_against(admin_env=False, holdings_gas_cents=9971, treasury_gas_cents=11995)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(double.platform.requests, [])
        self.assertTrue(all(runner.facts["sets"][k]["landed"] for k in ("P1", "P2", "P3")))
        self.assertEqual(runner.notes["S7"], [])

    def test_a_wrong_key_is_the_platforms_refusal_in_its_words_and_the_same_on_retry(self):
        double = EstateDouble()
        tmp = tempfile.mkdtemp()
        store = os.path.join(tmp, "store")
        os.makedirs(store)
        with open(os.path.join(store, T.ADMIN_ENV_FILE), "w", encoding="utf-8") as handle:
            handle.write("export %s='%s'\n%s=%snot-the-key\n" % (T.ADMIN_ENV_URL_KEY, PLATFORM_BASE, T.ADMIN_ENV_KEY_KEY, T.ADMIN_KEY_PREFIX))
        runner = runner_on(double, tmp, invite=double.mint_founder_link(), admin_env=False)
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)  # Spec T19 §3: the platform's refusal is the estate's road failing, not a missing prerequisite
        self.assertTrue(o.line.endswith("the gas credit for Harness Treasury was not made: refused: the platform refused the admin credential (HTTP 401): %s — the answer will be the same until the credential in admin.env is replaced" % PLATFORM_ADMIN_INVALID), o.line)
        self.assertIn("; the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.), which a gas credit cures; the gas credit for Harness Treasury was not made: refused:", o.line,
                      "Spec T26 §3.3: the refusal that needed the credit is named first")
        self.assertEqual(len(double.platform.requests), 1)
        self.assertEqual(runner.facts["gas_credits"][0]["outcome"], "refused")
        self.assertNotIn("not-the-key", runner.report(), "the key, right or wrong, is redacted")
        self.assertEqual(T.parse_env_file("export A='x'\n# a comment\nB=\"y\"\n\nC=z=1\n"), {"A": "x", "B": "y", "C": "z=1"})

    def test_a_platform_that_cannot_be_reached_is_a_fault_named_as_one(self):
        double, runner, outcomes = run_against(platform=PlatformDouble(down=True))
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)  # Spec T19 §3: a fault of the platform's road is not a missing prerequisite
        # Spec T26 §3.3: an unreachable admin road fails S7 only because a refusal needed the credit, and the sentence names that refusal first
        self.assertTrue(o.line.endswith("; the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.), which a gas credit cures; "
                                        "the gas credit for Harness Treasury was not made: the platform could not be reached: POST %s%s could not be reached: [Errno 61] Connection refused" % (
                                            PLATFORM_BASE, T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID)), o.line)
        self.assertNotIn("the estate could not be reached", o.line, "the platform is not the estate")
        self.assertEqual(runner.facts["gas_credits"][0]["outcome"], "unreachable")
        # and the same platform, unreachable, on a run whose accounts cover their sets: never asked (Spec T26 §3.3)
        double2, runner2, outcomes2 = run_against(platform=PlatformDouble(down=True), holdings_gas_cents=9971, treasury_gas_cents=11995)
        self.assertEqual(outcomes2["S7"].outcome, H.PASS, outcomes2["S7"].line)
        self.assertEqual(double2.platform.requests, [], "the road that could not be reached on 4 October is not needed, so it is not asked")

    def test_each_cure_is_sized_by_its_own_refusals_ceiling_and_made_once(self):
        double, runner, outcomes = run_against(quote_ceiling_usd_cents=1200)
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)
        posts = [(json.loads(r["body"])["amount_usd_cents"], r["path"]) for r in double.platform.requests]
        self.assertEqual(posts, [(3000, T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID), (3000, T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID)],
                         "Spec T26 §2: one cure per refusal, each the next ten dollars above twice its own refusal's ceiling of US$12.00 — not S7a's ceiling of US$36.00, which T14 sized Holdings' standing credit by")
        self.assertEqual(H.Runner.gas_credit_for(None), 1000)
        self.assertEqual(H.Runner.gas_credit_for(120), 1000)
        self.assertEqual(H.Runner.gas_credit_for(1200), 3000)
        self.assertEqual(H.Runner.gas_credit_for(3600), 8000)
        self.assertEqual(runner.facts["s7a"]["ceiling"], 3600, "read at S7a, and no credit is sized by it")
        self.assertEqual(runner.facts["money"]["treasury"]["credited"], 3000)
        self.assertEqual(runner.facts["money"]["holdings"]["credited"], 3000)
        self.assertEqual(outcomes["S7"].line.count("the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$12.00 of gas. Nothing was sent. Buy gas below.); gas credited and the review asked again"), 2,
                         "the Treasury's cure and P1's")
        self.assertIn("Harness Treasury credited US$30.00 (line ", outcomes["S7"].line)
        self.assertIn("Harness Holdings credited US$30.00 (line ", outcomes["S7"].line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class APaymentWhosePayeeBalanceDoesNotRise(unittest.TestCase):
    def test_each_payment_fails_naming_the_two_figures(self):
        # Holdings already holds the three payments (no Treasury payment to fail first); the chain debits the sender and credits nobody
        double, runner, outcomes = run_against(holdings_usdc_cents=100, chain=UsdcChainDouble(lose_transfers=True))
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("Harness Holdings holds US$1.00, at or above the three payments' US$1.00, so the Treasury was not asked to pay", o.line)
        for key, amount in (("P1", "US$0.50"), ("P2", "US$0.01"), ("P3", "US$0.49")):
            record = runner.facts["sets"][key]
            self.assertFalse(record["landed"])
            self.assertEqual(record["failure"], "the payee's USDC balance did not rise by %s: US$0.00 → US$0.00" % amount)
            self.assertIn("%s (%s USDC to %s, the owner's wallet, expected to" % (key, amount[3:], OWNER_WALLET_FOR_TESTS), o.line)
            self.assertEqual((record["status"], record["set_status"]), ("confirmed", "settled"), "the estate says landed; the chain says otherwise, and the chain decides")
        self.assertIn("not landed — the payee's USDC balance did not rise by US$0.50: US$0.00 → US$0.00 (instruction confirmed, run settled, userOpHash 0x", o.line)
        self.assertTrue(any(f.probe.startswith("money moved: Harness Holdings' USDC does not reconcile") for f in runner.findings), "S10: nothing landed, and Holdings' USDC still fell")

    def test_a_balance_the_rpc_could_not_read_is_not_a_pass(self):
        double, runner, outcomes = run_against(holdings_usdc_cents=100, chain=UsdcChainDouble(fault="down"))
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        record = runner.facts["sets"]["P1"]
        self.assertTrue(record["failure"].startswith("the payee's balance could not be read (the RPC at %s could not be reached:" % T.public_rpc_url(T.PAYEE_CHAIN)), record["failure"])
        self.assertEqual((record["status"], record["set_status"]), ("confirmed", "settled"))
        self.assertFalse(any(f.probe.startswith("Rule 13") for f in runner.findings), "the RPC is not the estate")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheAuditorCountsTheMoney(unittest.TestCase):
    def test_a_one_cent_gap_is_a_finding(self):
        double, runner, outcomes = run_against(platform=PlatformDouble(debit_gap_cents=1))
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)
        findings = [f for f in runner.findings if f.probe.startswith("money moved")]
        # Spec T26 §3.4: each workspace's gas account is reconciled, so the ledger's extra cent is found on both — the Treasury's one payment and Holdings' three
        self.assertEqual([(f.station, f.probe, f.expected, f.said) for f in findings],
                         [("S10", "money moved: Harness Treasury's gas account does not reconcile to the cent", "US$0.00 before, plus US$10.00 credited, less US$0.31 of gas debit on its payment: US$9.69", "the estate reads US$9.68 after"),
                          ("S10", "money moved: Harness Holdings' gas account does not reconcile to the cent", "US$0.00 before, plus US$10.00 credited, less US$0.93 of gas debits: US$9.07", "the estate reads US$9.04 after")])
        self.assertEqual(outcomes["S10"].outcome, H.FAIL)
        note = next(n for n in runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)"))
        self.assertIn("Harness Treasury's gas account US$0.00 → US$9.68 (credited US$10.00; gas debit US$0.31 on its payment); ", note)
        self.assertTrue(note.endswith("Harness Holdings' gas account US$0.00 → US$9.04 (credited US$10.00; gas debits US$0.93 over 3 of 3 payments that landed); "
                                      "Harness Holdings' USDC fell by US$1.00 and its gas account by US$0.96, US$1.96 in all — which is not the payments that landed (US$1.00) plus their gas (US$0.93): "
                                      "2 pair(s) do not reconcile to the cent — findings above"), note)

    def test_the_count_is_pure_arithmetic_on_the_figures_read(self):
        runner = H.Runner("https://estate.test", tempfile.mkdtemp(), None, False, None, tempfile.mkdtemp(), say=lambda s: None, sleep=lambda s: None)
        runner.facts["money"] = {"treasury": {"usdc_before": 100000000, "usdc_after": 81760000, "paid_minor": 18240000, "credited": 1000, "gas_before": 0, "gas_after": 969,
                                              "payment": {"landed": True, "gas_debit_cents": 31}},
                                 "holdings": {"usdc_before": 0, "usdc_after": 0, "received_minor": 18240000, "credited": 1000, "gas_before": 0, "gas_after": 907},
                                 "payments": [{"key": "P1", "amount_minor": 1250000, "landed": True, "gas_debit_cents": 31}, {"key": "P2", "amount_minor": 4990000, "landed": True, "gas_debit_cents": 31},
                                              {"key": "P3", "amount_minor": 12000000, "landed": True, "gas_debit_cents": 31}]}
        runner.audit_the_money_moved("S10")
        self.assertEqual(runner.findings, [])
        self.assertTrue(runner.notes["S10"][0].endswith("every pair reconciles to the cent"))
        self.assertIn("Harness Treasury's gas account US$0.00 → US$9.69 (credited US$10.00; gas debit US$0.31 on its payment); ", runner.notes["S10"][0], "Spec T26 §3.4: the Treasury's gas account is reconciled too")
        # a Treasury that made no payment has no gas debit, and its account is still reconciled
        runner.notes["S10"] = []
        runner.facts["money"]["treasury"].update({"usdc_after": 100000000, "paid_minor": 0, "credited": 0, "gas_after": 0, "payment": None})
        runner.facts["money"]["holdings"]["received_minor"] = 0
        runner.facts["money"]["holdings"]["usdc_before"] = 18240000
        runner.audit_the_money_moved("S10")
        self.assertEqual(runner.findings, [])
        self.assertIn("Harness Treasury's gas account US$0.00 → US$0.00 (credited US$0.00; no payment, so no gas debit); ", runner.notes["S10"][0])
        runner.facts["money"]["treasury"].update({"usdc_after": 81760000, "paid_minor": 18240000, "credited": 1000, "gas_after": 969, "payment": {"landed": True, "gas_debit_cents": 31}})
        runner.facts["money"]["holdings"]["received_minor"] = 18240000
        runner.facts["money"]["holdings"]["usdc_before"] = 0
        runner.notes["S10"] = []
        runner.facts["money"]["holdings"]["usdc_after"] = 10000  # one cent of USDC left behind
        runner.notes["S10"] = []
        runner.audit_the_money_moved("S10")
        self.assertEqual([(f.probe, f.expected, f.said) for f in runner.findings],
                         [("money moved: Harness Holdings' USDC does not reconcile to the cent", "US$0.00 before, plus US$18.24 received from the Treasury, less US$18.24 of payments that landed: US$0.00", "the estate reads US$0.01 after")])
        runner.findings = []
        runner.facts["money"]["payments"][2]["gas_debit_cents"] = None  # a debit the trail did not carry
        runner.facts["money"]["holdings"]["usdc_after"] = 0
        runner.audit_the_money_moved("S10")
        self.assertEqual([f.probe for f in runner.findings], ["money moved: a gas debit is not on the trail"])
        self.assertEqual(runner.findings[0].said, "2 of 3 landed payment(s) carry a gas debit; the gas account moved US$0.00 → US$9.07")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheBirthRunStopsWithTheFundSentence(unittest.TestCase):
    def test_the_first_run_births_the_treasury_prints_the_address_and_stops_and_the_rerun_pays(self):
        double = EstateDouble(treasury_funding_wallet="press")
        tmp = tempfile.mkdtemp()
        runner = runner_on(double, tmp, invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)  # Spec T19 §3: the birth run stops at a missing prerequisite — the Treasury is not funded
        address = double.treasury.source_account
        sentence = T.FUND_TREASURY_SENTENCE % (address, "arbitrum")
        self.assertEqual(sentence, "fund Harness Treasury: %s on arbitrum, then rerun" % address)
        self.assertTrue(o.line.endswith("%s (the three payments need US$1.00 and Harness Holdings holds US$0.00; the Treasury holds US$0.00); nothing was sent" % sentence), o.line)
        self.assertIn("payments: %s — " % H.TREASURY_NOT_FUNDED, o.line, "the summary line names the scenario and the missing prerequisite")
        # Spec T27: the Treasury's Policy Interview is asked C2 and C3 at catalog version 15 and the book answers them, so 25 where it was 23
        self.assertIn("the interviews walked from the book with the Treasury's own name, approver and account approvers (25 and 18 questions)", o.line)
        self.assertIn("funding wallet: %s on double-stack-1, key %s (born by this run's press)" % (address, double.treasury.custody_key_id), o.line)
        self.assertTrue(any(n.startswith("%s — the estate's own words: Fund this account with USDC on arbitrum. Gas is bought separately, below." % sentence) for n in runner.notes["S7"]), runner.notes["S7"])
        self.assertEqual(double.platform.requests, [], "nothing credited")
        self.assertEqual(double.chain.transfers, [], "nothing sent")
        presses = [c for c in runner.calls if c.station == "S7" and c.route == "POST /v1/workspace/funding-wallet"]
        self.assertEqual(len(presses), 1, "the key allocated on the platform, once")
        self.assertEqual(double.treasury.funding_presses[-1]["binding"]["purpose"], "workspace.funding_wallet")
        self.assertTrue(runner.facts["treasury"]["born_now"] and runner.facts["treasury"]["wallet_born_now"] and runner.facts["treasury"]["interviews_walked"])
        # the Treasury's charter: the book's, with its own name and approver
        policy = double.treasury.newest_written_policy_charter()
        self.assertEqual(policy["name"], "Harness Treasury Pty Ltd")
        self.assertEqual(policy["signers"], [T.TREASURY["email"]], "C11 names the address the Treasury's estate is opened under")
        account = double.treasury.newest_written_charter()
        self.assertEqual(account["signers"][0], "Harness Treasury <%s>" % T.TREASURY["email"])
        self.assertEqual(account["amountsUsdCents"]["holdOverPerTx"], A.MONEY["per_payment_cents"], "the book's operations account, unchanged")
        # Bear funds the address, once, and the rerun pays: the founder signs in, the charter stands, nothing is walked again
        double.chain.credit(address, T.usdc_minor_of_cents(5000))
        runner2 = runner_on(double, tmp, invite=None)
        outcomes2 = {o.station: o for o in runner2.run()}
        o2 = outcomes2["S7"]
        self.assertEqual(o2.outcome, H.PASS, o2.line)
        self.assertIn("Harness Treasury: the Treasury founder signed in with the stored passkey; funding wallet: %s on double-stack-1, key %s (already born; not pressed for again); before:" % (address, double.treasury.custody_key_id), o2.line)
        self.assertEqual([c.route for c in runner2.calls if c.station == "S7" and "/onboarding/" in c.path], ["GET /v1/onboarding/charter"])
        self.assertIn("Harness Treasury holds US$50.00 of USDC on arbitrum", o2.line)
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$1.00" % double.source_account, o2.line)
        self.assertEqual(sorted(os.listdir(os.path.join(runner2.store_dir, T.TREASURY["client_id"]))), ["harriet.json"], "one passkey, kept across the runs")


class TheTablesFacts(unittest.TestCase):
    def test_the_treasurys_rows_and_the_admin_credentials_file_name(self):
        self.assertEqual(T.TREASURY, {"company": "Harness Treasury Pty Ltd", "short": "Harness Treasury", "client_id": "harness-treasury", "email": "harness+treasury@aeredium.io"})
        self.assertEqual((T.ADMIN_ENV_FILE, T.ADMIN_ENV_URL_KEY, T.ADMIN_ENV_KEY_KEY, T.ADMIN_KEY_PREFIX), ("admin.env", "AAP_ADMIN_BASE_URL", "AAP_ADMIN_KEY", "".join(("aek", "-admin-"))))  # composed: no file under tests/ holds the platform's prefix (Spec P1d)
        self.assertEqual(T.ADMIN_CREDIT_ROUTE % "abc", "/v1/admin/accounts/abc/gas-account/credits")
        self.assertEqual(T.ADMIN_CREDIT_REASON % "20260924-000000-abcd", "sandbox run 20260924-000000-abcd")
        self.assertEqual(T.GAS_CREDIT_USD_CENTS, 1000)
        self.assertEqual((T.GAS_ACCOUNT_ROUTE, T.FUNDING_BALANCES_ROUTE, T.SET_EXECUTE_ROUTE % "x"), ("/v1/gas/account", "/v1/workspace/funding-account/balances", "/v1/sets/x/execute"))
        self.assertEqual((T.GAS_GATE, T.GAS_SHORTFALL, T.INSTRUCTION_CONFIRMED, T.PLATFORM_LANDED), ("gas_preflight", "GAS_SHORTFALL", "instruction.confirmed", "landed"))
        self.assertEqual(T.INSTRUCTION_TERMINAL_STATES, ("confirmed", "failed", "rejected"))
        self.assertEqual(T.SET_TERMINAL_STATES, ("settled", "partially_settled", "cancelled"))

    def test_the_estates_spelling_of_dollars_and_the_sentences(self):
        self.assertEqual(T.format_usd_cents(0), "US$0.00")
        self.assertEqual(T.format_usd_cents(120), "US$1.20")
        self.assertEqual(T.format_usd_cents(182499), "US$1824.99", "formatUsdCents groups nothing")
        self.assertEqual(T.format_usd_cents(-5), "-US$0.05")
        self.assertEqual(T.gas_set_shortfall_sentence(0, 120), U3_SENTENCE)
        self.assertEqual(T.gas_debit_words(31), "gas, US$0.31, paid in advance from your gas account")
        self.assertEqual(T.usdc_dollars(18240000), "US$18.24")
        self.assertEqual(T.usdc_dollars(0), "US$0.00")
        self.assertEqual(T.usdc_dollars(100000000), "US$100.00")
        self.assertEqual(T.usdc_dollars(18240001), "US$18.240001", "dust is shown whole, never rounded away")
        self.assertEqual(T.usdc_minor_of_cents(1824), 18240000)
        with self.assertRaises(ValueError):
            T.usdc_dollars(-1)
        self.assertEqual(T.TREASURY_SHORT_SENTENCE % ("US$10.00", "US$18.24", "0xabc", "arbitrum"), "Harness Treasury holds US$10.00; the run needs US$18.24; fund 0xabc on arbitrum")
        self.assertEqual(T.FUND_TREASURY_SENTENCE % ("0xabc", "arbitrum"), "fund Harness Treasury: 0xabc on arbitrum, then rerun")

    def test_the_public_rpc_is_read_from_the_corridors_skeleton_at_run_time_and_the_balance_call_is_the_erc20_selector(self):
        self.assertEqual(T.public_rpc_url("ethereum"), "https://ethereum-rpc.publicnode.com")
        self.assertEqual(T.public_rpc_url("arbitrum"), "https://arb1.arbitrum.io/rpc", "Spec T18: the payments' chain, from the corridor's skeleton")
        self.assertEqual(T.public_rpc_url(T.PAYEE_CHAIN), "https://arb1.arbitrum.io/rpc")
        self.assertEqual(T.public_rpc_url("aeredium-testnet"), T.TESTNET_RPC_URL)
        self.assertIsNone(T.public_rpc_url("solana"))
        self.assertEqual(T.ERC20_BALANCE_OF_SELECTOR, "0x70a08231")
        data = T.balance_of_call_data(T.address("NORTHWIND_ETHEREUM"))
        self.assertEqual(len(data), 2 + 8 + 64)
        self.assertTrue(data.startswith("0x70a08231000000000000000000000000"))
        self.assertTrue(data.endswith(T.address("NORTHWIND_ETHEREUM").lower()[2:]))
        with self.assertRaises(ValueError):
            T.balance_of_call_data("0x123")
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aer360_tables.py"), "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("publicnode", text, "the endpoint is the corridor's fact, read at run time and never copied")


if __name__ == "__main__":
    unittest.main()
