"""
Spec T14 (22 September 2026, amended 22:35; built 24 September 2026): the harness pays in cents, funds Harness Holdings from Harness Treasury — a
second sandbox workspace whose key lives only in the enclave — credits the gas account through the platform's admin credit road as the sandbox may,
proves the gas refusal (S7a), and S7 passes with money that moved; S10 counts the money to the cent. Each test here was red on main.

The double is the estate at AER 360 Spec 104 beside the platform at Spec 154 (tests/test_aer360_double.py): two workspaces on one estate, sharing
the platform's gas ledger (PlatformDouble, whose one road on the wire is the admin credit road) and the payment chain's USDC (UsdcChainDouble, whose
public RPC answers balanceOf). Harness Holdings holds no USDC and no gas; Harness Treasury holds the US$100.00 Bear funded it with and no gas.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests.test_aer360_double import (  # noqa: E402
    AAP_ACCOUNT_ID, EstateDouble, PLATFORM_ADMIN_INVALID, PLATFORM_BASE, PlatformDouble, TREASURY_ACCOUNT_ID, UsdcChainDouble, runner_on,
)

SHORTFALL_MINOR = 18240000  # the three payments together, in USDC minor units: 1.25 + 4.99 + 12.00
U3_SENTENCE = "Your gas account holds US$0.00. This set needs at most US$1.20 of gas. Nothing was sent. Buy gas below."


def run_against(tmp=None, admin_env=True, **double_kwargs):
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tmp or tempfile.mkdtemp(), invite=double.mint_founder_link(), admin_env=admin_env)
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheTreasuryPaysAndTheThreePaymentsLand(unittest.TestCase):
    """Holdings at US$0.00 and the Treasury at US$100.00: the one payment of US$18.24, S7a, the two credits, the three payments, and S10's count."""

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
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$18.24: submitted: status pending_approval, approvalsRequired 1; Harriet Founder signed (1 of 1): approved; landed (+US$18.24): instruction confirmed, run settled, userOpHash 0x" % self.holdings_wallet, o.line)
        self.assertIn("payee US$0.00 → US$18.24, gas US$0.31", o.line)
        # the road, as the estate's own: review, create, submit, challenge, approve, execute, the register until terminal, the trail
        # the Treasury founder's calls are labelled with her workspace in Every call, so the two founders named Harriet Founder are told apart
        routes = [c.route for c in self.runner.calls if c.station == "S7" and c.who == "Harriet Founder (Harness Treasury)" and c.path.startswith(("/v1/sets", "/v1/approvals", "/v1/export"))]
        set_id = record["set_id"]
        self.assertEqual(routes, ["POST /v1/sets/review", "POST /v1/sets", "POST /v1/sets/%s/submit" % set_id, "POST /v1/approvals/%s/challenge" % set_id,
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
        self.assertIn("S7a proved: the review refused GAS_SHORTFALL — \"%s\" — naming the US$0.00 the harness read and the gate's ceiling US$1.20; nothing left (no new run in the register; Holdings' USDC unchanged at US$18.24)" % U3_SENTENCE, self.outcomes["S7"].line)
        review = next(s for s in self.runner.evidence["S7"] if s["route"] == "POST /v1/sets/review" and str(s["expected"]).startswith("S7a:"))
        self.assertEqual(len(review["sent"]["pays"]), 3, "the set of three")
        self.assertEqual(review["result"], "refused as U3 says: %s" % U3_SENTENCE)
        self.assertEqual(T.gas_set_shortfall_sentence(0, 120), U3_SENTENCE)
        # S7a was proved before Holdings' gas was credited, on the account the harness read at US$0.00
        credits = [c for c in self.runner.calls if c.station == "S7" and "gas-account/credits" in c.path]
        review_at = [i for i, c in enumerate(self.runner.calls) if c.station == "S7" and c.route == "POST /v1/sets/review"][1]
        holdings_credit_at = next(i for i, c in enumerate(self.runner.calls) if AAP_ACCOUNT_ID in c.path and "gas-account/credits" in c.path)
        self.assertLess(review_at, holdings_credit_at, "S7a before Holdings' credit (Spec T14 §3)")
        self.assertEqual(len(credits), 2)

    def test_the_admin_credit_road_received_one_credit_per_workspace_with_the_reason_and_the_credential_was_never_printed(self):
        posts = self.double.platform.requests
        self.assertEqual([(r["method"], r["path"]) for r in posts], [("POST", T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID), ("POST", T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID)],
                         "the Treasury first (its payment needs gas), then Holdings after S7a")
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
        self.assertIn("Harness Holdings credited US$10.00 (line %s): balance US$10.00, available US$10.00" % records[1]["balance_after"] and self.double.platform.lines[-4]["id"] and "", "")
        report = self.runner.report()
        self.assertNotIn(self.double.platform.admin_key, report, "the admin key travels in no record")
        self.assertNotIn(self.double.platform.admin_key, self.outcomes["S7"].line)
        self.assertNotIn("authorization", json.dumps([c.sent for c in self.runner.calls]).lower(), "the bearer rides in a header, which is never recorded")
        self.assertEqual(self.money["holdings"]["credited"], 1000)
        self.assertEqual(self.money["treasury"]["credited"], 1000)

    def test_the_three_payments_land_with_the_gas_lines_and_the_signers_press_in_the_specs_order(self):
        o = self.outcomes["S7"]
        sets = self.runner.facts["sets"]
        for key, amount in (("P1", 1250000), ("P2", 4990000), ("P3", 12000000)):
            record = sets[key]
            self.assertTrue(record["landed"], record["said"])
            self.assertEqual((record["status"], record["set_status"], record["amount_minor"]), ("confirmed", "settled", amount))
            self.assertEqual(record["balance_after"] - record["balance_before"], amount, key)
            self.assertEqual((record["gas_debit_cents"], record["gas_debit"]), (31, "US$0.31"))
            self.assertTrue(str(record["user_op_hash"]).startswith("0x") and str(record["tx_hash"]).startswith("0x"))
        self.assertEqual([a["who"] for a in sets["P1"]["approvals"]], [], "the estate asked no signature within the hold for a listed payee")
        self.assertEqual([(a["who"], a["refusal_code"], a["status_after"]) for a in sets["P2"]["approvals"]],
                         [("Ben Signatory", "ROLE_NOT_GRANTED", None), ("Cora Clerk", "ROLE_NOT_GRANTED", None), ("Ada Approver", None, "approved")],
                         "the spec's order: the holder, the clerk, then the approver; the estate admits the approver standing alone and says so")
        self.assertEqual([(a["who"], a["status_after"]) for a in sets["P3"]["approvals"]][-1], ("Ada Approver", "approved"))
        self.assertEqual(o.line.count("gas US$0.31"), 4, "the Treasury's payment and the three, each with its gas debit beside it")
        self.assertEqual(len(self.double.chain.transfers), 4)
        self.assertEqual(self.double.chain.balance_of(self.holdings_wallet), 0, "Holdings paid out exactly what it received")
        self.assertEqual(self.double.chain.balance_of(T.address("NORTHWIND_ETHEREUM")), 1250000)
        self.assertEqual(self.double.chain.balance_of(T.address("CONTOSO_ETHEREUM")), 12000000)
        # the payees' balances were read from the chain's public RPC, before and after, against the contract the estate names
        rpc_calls = [c for c in self.runner.calls if c.station == "S7" and c.path == T.public_rpc_url(T.PAYEE_CHAIN)]
        self.assertEqual(len(rpc_calls), 6)
        self.assertTrue(all(c.sent["params"][0]["to"] == self.double.chain.token for c in rpc_calls))
        self.assertEqual(self.runner.facts["usdc_token"], self.double.chain.token)
        self.assertEqual(self.double.chain.calls[0]["body"]["params"][0]["data"], T.balance_of_call_data(T.address("NORTHWIND_ETHEREUM")))
        self.assertEqual(self.outcomes["S11"].line, "the attacker: 17 probe(s), 0 not made, 1 finding(s)", "the settled runs answer S11's probes as refusals")

    def test_s10_counts_the_money_to_the_cent(self):
        notes = [n for n in self.runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)")]
        self.assertEqual(notes, ["money moved (Spec T14 §5): Harness Treasury's USDC US$100.00 → US$81.76 (paid US$18.24); Harness Holdings' USDC US$0.00 → US$0.00 (received US$18.24; the three payments US$18.24, of which US$18.24 landed); "
                                 "Harness Holdings' gas account US$0.00 → US$9.07 (credited US$10.00; gas debits US$0.93 over 3 of 3 payments that landed): every pair reconciles to the cent"])
        self.assertEqual([f.probe for f in self.runner.findings if f.probe.startswith("money moved")], [])
        self.assertEqual(self.money["treasury"]["usdc_after"], 81760000)
        self.assertEqual(self.money["holdings"]["gas_after"], 907)
        self.assertEqual(self.double.platform.balance(AAP_ACCOUNT_ID), {"balance_usd_cents": 907, "reserved_usd_cents": 0, "available_usd_cents": 907})
        self.assertEqual(self.double.platform.balance(TREASURY_ACCOUNT_ID), {"balance_usd_cents": 969, "reserved_usd_cents": 0, "available_usd_cents": 969})
        # the findings are the two the estate's own code makes, as before
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings], [("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")])

    def test_the_report_names_the_treasury_and_the_money_and_reads_back(self):
        report = self.runner.report()
        self.assertIn("Harness Treasury: funding wallet %s — the float Bear funds with USDC on arbitrum, once; it pays Harness Holdings' shortfall through the estate's own road, and the harness holds no key for it (Spec T14)." % self.treasury.source_account, report)
        self.assertIn("The asset: the three payments together need US$18.24 of USDC; Harness Treasury pays Harness Holdings the shortfall through the estate's own road (Spec T14); the harness never mints the asset and holds no key.", report)
        self.assertIn("| POST %s%s |" % (PLATFORM_BASE, T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID), report, "the admin credit is in Every call")
        self.assertIn("| POST %s |" % T.public_rpc_url(T.PAYEE_CHAIN), report)
        path = self.runner.write_report()
        read = H.read_report(path)
        self.assertEqual(read["outcomes"]["S7"], "pass")
        self.assertEqual(len(read["outcomes"]), len(H.STATIONS))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheTreasuryIsShort(unittest.TestCase):
    def test_s7_fails_with_the_sentence_and_nothing_is_sent(self):
        double, runner, outcomes = run_against(treasury_usdc_cents=1000)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)  # Spec T19 §3: the stop is a missing prerequisite, named in the line
        sentence = T.TREASURY_SHORT_SENTENCE % ("US$10.00", "US$18.24", double.treasury.source_account, "arbitrum")
        self.assertEqual(sentence, "Harness Treasury holds US$10.00; the run needs US$18.24; fund %s on arbitrum" % double.treasury.source_account)
        self.assertTrue(o.line.endswith("%s (the three payments need US$18.24 and Harness Holdings holds US$0.00); nothing was sent" % sentence), o.line)
        self.assertIn("payments: %s — " % H.TREASURY_SHORT, o.line, "the summary line names the scenario and the missing prerequisite")
        self.assertFalse(any(sentence in n for n in runner.notes["S7"]), "Spec T19 §3: the note beside the stop is gone; its figures travel in the line")
        self.assertEqual([c.route for c in runner.calls if c.station == "S7" and c.method == "POST" and c.path.startswith("/v1/sets")], [], "nothing was submitted")
        self.assertEqual(double.platform.requests, [], "no gas was credited either")
        self.assertEqual(double.chain.transfers, [])
        self.assertEqual(double.chain.balance_of(double.treasury.source_account), 10000000)
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
        self.assertEqual(s7a["left"][1], "Harness Holdings' USDC moved from US$18.24 to US$0.00")
        self.assertIn("S7a failed: a payment left — the review created run(s) set-", o.line)
        self.assertIn("; Harness Holdings' USDC moved from US$18.24 to US$0.00", o.line)

    def test_a_balance_that_already_covers_the_ceiling_is_reported_not_failed(self):
        double = EstateDouble()
        double.platform.credit(AAP_ACCOUNT_ID, 1000, "an earlier run's credit", "an earlier sandbox run", "admin", "admin:bearer")
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertEqual(runner.facts["s7a"]["verdict"], "not proved")
        self.assertIn("S7a not proved: Harness Holdings' gas account (US$10.00 available) covers the set's ceiling, so the review admits the set and the refusal cannot be met this run (the gate's evidence: gas account: US$10.00 available; this set needs at most US$1.20 of gas over 3 payments", o.line)
        self.assertEqual(runner.facts["money"]["holdings"]["gas_before"], 1000)
        self.assertEqual(runner.facts["money"]["holdings"]["credited"], 1000, "credited all the same: the unspent balance stays (Bear, 22 September 2026)")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheAdminCreditRoad(unittest.TestCase):
    def test_the_file_absent_fails_s7_with_its_sentence_and_nothing_is_credited_or_sent(self):
        double, runner, outcomes = run_against(admin_env=False)
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)  # Spec T19 §3: a stop is a missing prerequisite, named
        self.assertIn("payments: %s — " % H.NO_ADMIN_CREDENTIAL, o.line)
        self.assertTrue(o.line.endswith(T.NO_GAS_CREDIT_ROAD_SENTENCE), o.line)
        self.assertEqual(T.NO_GAS_CREDIT_ROAD_SENTENCE, "no gas credit road: the sandbox credits gas through the platform's admin road; file the credential in ~/.aer360-harness/admin.env")
        self.assertTrue(any(n.endswith("is not filed: the gas credits below will fail with %r" % T.NO_GAS_CREDIT_ROAD_SENTENCE) for n in runner.notes["S7"]), runner.notes["S7"])
        self.assertEqual(double.platform.requests, [])
        self.assertEqual(double.chain.transfers, [], "the Treasury's payment needs gas first, so nothing left")
        self.assertIn("Harness Treasury holds US$100.00 of USDC on arbitrum", o.line, "the Treasury was brought in and the balances read before the credit step stopped S7")

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
        self.assertEqual(len(double.platform.requests), 1)
        self.assertEqual(runner.facts["gas_credits"][0]["outcome"], "refused")
        self.assertNotIn("not-the-key", runner.report(), "the key, right or wrong, is redacted")
        self.assertEqual(T.parse_env_file("export A='x'\n# a comment\nB=\"y\"\n\nC=z=1\n"), {"A": "x", "B": "y", "C": "z=1"})

    def test_a_platform_that_cannot_be_reached_is_a_fault_named_as_one(self):
        double, runner, outcomes = run_against(platform=PlatformDouble(down=True))
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)  # Spec T19 §3: a fault of the platform's road is not a missing prerequisite
        self.assertIn("the gas credit for Harness Treasury was not made: the platform could not be reached: POST %s%s could not be reached: [Errno 61] Connection refused" % (PLATFORM_BASE, T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID), o.line)
        self.assertNotIn("the estate could not be reached", o.line, "the platform is not the estate")

    def test_the_credit_is_sized_by_the_ceiling_as_the_sandbox_may_and_a_shortfall_at_the_review_credits_once_more(self):
        double, runner, outcomes = run_against(quote_ceiling_usd_cents=1200)
        self.assertEqual(outcomes["S7"].outcome, H.PASS, outcomes["S7"].line)
        posts = [(json.loads(r["body"])["amount_usd_cents"], r["path"]) for r in double.platform.requests]
        self.assertEqual(posts, [(1000, T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID), (3000, T.ADMIN_CREDIT_ROUTE % TREASURY_ACCOUNT_ID), (8000, T.ADMIN_CREDIT_ROUTE % AAP_ACCOUNT_ID)],
                         "U3's ten dollars; the Treasury's review refused for want of gas, so the next ten dollars above twice its ceiling; Holdings the next ten dollars above twice S7a's ceiling of US$36.00")
        self.assertEqual(H.Runner.gas_credit_for(None), 1000)
        self.assertEqual(H.Runner.gas_credit_for(120), 1000)
        self.assertEqual(H.Runner.gas_credit_for(1200), 3000)
        self.assertEqual(H.Runner.gas_credit_for(3600), 8000)
        self.assertEqual(runner.facts["money"]["treasury"]["credited"], 4000)
        self.assertEqual(runner.facts["money"]["holdings"]["credited"], 8000)
        self.assertIn("the review refused GAS_SHORTFALL (Your gas account holds US$10.00. This set needs at most US$12.00 of gas. Nothing was sent. Buy gas below.); gas credited and the review asked again", outcomes["S7"].line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class APaymentWhosePayeeBalanceDoesNotRise(unittest.TestCase):
    def test_each_payment_fails_naming_the_two_figures(self):
        # Holdings already holds the three payments (no Treasury payment to fail first); the chain debits the sender and credits nobody
        double, runner, outcomes = run_against(holdings_usdc_cents=1824, chain=UsdcChainDouble(lose_transfers=True))
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("Harness Holdings holds US$18.24, at or above the three payments' US$18.24, so the Treasury was not asked to pay", o.line)
        for key, amount in (("P1", "US$1.25"), ("P2", "US$4.99"), ("P3", "US$12.00")):
            record = runner.facts["sets"][key]
            self.assertFalse(record["landed"])
            self.assertEqual(record["failure"], "the payee's USDC balance did not rise by %s: US$0.00 → US$0.00" % amount)
            self.assertIn("%s (%s USDC, expected to" % (key, amount[3:]), o.line)
            self.assertEqual((record["status"], record["set_status"]), ("confirmed", "settled"), "the estate says landed; the chain says otherwise, and the chain decides")
        self.assertIn("not landed — the payee's USDC balance did not rise by US$1.25: US$0.00 → US$0.00 (instruction confirmed, run settled, userOpHash 0x", o.line)
        self.assertTrue(any(f.probe.startswith("money moved: Harness Holdings' USDC does not reconcile") for f in runner.findings), "S10: nothing landed, and Holdings' USDC still fell")

    def test_a_balance_the_rpc_could_not_read_is_not_a_pass(self):
        double, runner, outcomes = run_against(holdings_usdc_cents=1824, chain=UsdcChainDouble(fault="down"))
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
        self.assertEqual([(f.station, f.probe, f.expected, f.said) for f in findings],
                         [("S10", "money moved: Harness Holdings' gas account does not reconcile to the cent", "US$0.00 before, plus US$10.00 credited, less US$0.93 of gas debits: US$9.07", "the estate reads US$9.04 after")])
        self.assertEqual(outcomes["S10"].outcome, H.FAIL)
        note = next(n for n in runner.notes["S10"] if n.startswith("money moved (Spec T14 §5)"))
        self.assertTrue(note.endswith("Harness Holdings' gas account US$0.00 → US$9.04 (credited US$10.00; gas debits US$0.93 over 3 of 3 payments that landed): 1 pair(s) do not reconcile to the cent — findings above"), note)

    def test_the_count_is_pure_arithmetic_on_the_figures_read(self):
        runner = H.Runner("https://estate.test", tempfile.mkdtemp(), None, False, None, tempfile.mkdtemp(), say=lambda s: None, sleep=lambda s: None)
        runner.facts["money"] = {"treasury": {"usdc_before": 100000000, "usdc_after": 81760000, "paid_minor": 18240000, "credited": 1000, "gas_before": 0, "gas_after": 969},
                                 "holdings": {"usdc_before": 0, "usdc_after": 0, "received_minor": 18240000, "credited": 1000, "gas_before": 0, "gas_after": 907},
                                 "payments": [{"key": "P1", "amount_minor": 1250000, "landed": True, "gas_debit_cents": 31}, {"key": "P2", "amount_minor": 4990000, "landed": True, "gas_debit_cents": 31},
                                              {"key": "P3", "amount_minor": 12000000, "landed": True, "gas_debit_cents": 31}]}
        runner.audit_the_money_moved("S10")
        self.assertEqual(runner.findings, [])
        self.assertTrue(runner.notes["S10"][0].endswith("every pair reconciles to the cent"))
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
        self.assertTrue(o.line.endswith("%s (the three payments need US$18.24 and Harness Holdings holds US$0.00; the Treasury holds US$0.00); nothing was sent" % sentence), o.line)
        self.assertIn("payments: %s — " % H.TREASURY_NOT_FUNDED, o.line, "the summary line names the scenario and the missing prerequisite")
        self.assertIn("the interviews walked from the book with the Treasury's own name, approver and account approvers (23 and 18 questions)", o.line)
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
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$18.24" % double.source_account, o2.line)
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
