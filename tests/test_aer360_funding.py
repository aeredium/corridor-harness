"""
Spec T13 (22 September 2026): the harness presses for the funding wallet, funds it from the faucet as the founder would,
and reads the payee register back after the count — from the run of 23:44 on 21 September (aer360-harness-2026-09-21-234438.md)
against the estate at AER 360 Spec 98, and from the faucet's mechanism as Bear recorded it. Each test here was red on main.

The double is the estate after Spec 98 (tests/test_aer360_double.py): GET /v1/workspace answers fundingWallet or
fundingWalletAbsence; the founder's press is the two-step step-up whose challenge is derived from
`funding-wallet:<workspace id>:<issuedAtMs>` under the purpose `workspace.funding_wallet`; the gateway births, refuses or is
away by a dial. Beside it stand a faucet that answers as aeredium/faucet's own handler does (FaucetDouble) and the chain's
public RPC (TestnetRpcDouble).
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
    EstateDouble, FaucetDouble, GATEWAY_NOT_CONFIGURED, NO_FUNDING_WALLET_SENTENCE, TestnetRpcDouble,
    WALLET_BIRTH_REFUSED_ON_21_SEPTEMBER, WORKSPACE_ID, runner_on,
)

RPC = "https://testnet.rpc.aeredium.io"
FAUCET = "https://aeredium.io/faucet-api/request"


def run_against(**double_kwargs):
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes


def summary_of(runner):
    """The report's summary under the closing table: the funding wallet, the gas and the asset (Spec T13 §5)."""
    return runner.report().split("Findings under S10 and S11", 1)[1].split("## S1 — Enrol", 1)[0]


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheHarnessPressesForTheFundingWallet(unittest.TestCase):
    """A double whose GET /v1/workspace answers fundingWalletAbsence: the harness presses, reads the wallet back, and funds it once."""

    @classmethod
    def setUpClass(cls):
        cls.double, cls.runner, cls.outcomes = run_against()
        cls.wallet = cls.double.funding_wallet_view()

    def test_s5_reads_the_absence_presses_with_the_step_up_and_reads_the_wallet_back(self):
        o = self.outcomes["S5"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("funding wallet: %s on double-stack-1, key %s (born by this run's press)" % (self.wallet["address"], self.wallet["keyId"]), o.line)
        routes = [c.route for c in self.runner.calls if c.station == "S5" and c.path.startswith("/v1/workspace")]
        self.assertEqual(routes, ["GET /v1/workspace", "POST /v1/workspace/funding-wallet/options", "POST /v1/workspace/funding-wallet", "GET /v1/workspace"])
        # the step-up: the challenge the estate derived from funding-wallet:<id>:<ms> under the purpose, and the assertion verified against it
        options, press = self.double.funding_presses
        self.assertEqual((options["step"], press["step"]), ("options", "press"))
        self.assertTrue(press["verified"])
        self.assertEqual(press["binding"]["setDigest"], "funding-wallet:%s:%d" % (WORKSPACE_ID, press["issuedAtMs"]))
        self.assertEqual(press["binding"]["purpose"], "workspace.funding_wallet")
        self.assertEqual(H.FUNDING_WALLET_PURPOSE, "workspace.funding_wallet")
        self.assertEqual(press["binding"]["credentialId"], self.runner.people["harriet"].credential_id)
        self.assertEqual(press["issuedAtMs"], options["issuedAtMs"], "the press carries the issuedAtMs the options answered")
        sent = [c for c in self.runner.calls if c.route == "POST /v1/workspace/funding-wallet"]
        self.assertEqual(len(sent), 1, "pressed once, never retried")
        self.assertEqual(sent[0].sent["issuedAtMs"], options["issuedAtMs"])
        self.assertTrue(str(sent[0].sent["response"]["response"]["signature"]).startswith("…"), "the assertion's signature is redacted in the record")
        self.assertEqual(self.runner.facts["funding_wallet"]["address"], self.wallet["address"])
        self.assertEqual(self.runner.facts["funding_press"]["status"], 200)
        self.assertIsNone(self.runner.facts["funding_press"]["refusal_code"])
        steps = {s["route"]: s for s in self.runner.evidence["S5"] if "/funding-wallet" in s["route"]}
        self.assertIn("the challenge the estate derives from funding-wallet:<workspace id>:<issuedAtMs> under the purpose workspace.funding_wallet", steps["POST /v1/workspace/funding-wallet/options"]["expected"])
        self.assertEqual(steps["POST /v1/workspace/funding-wallet"]["result"], "born")
        self.assertIn('"born": true', steps["POST /v1/workspace/funding-wallet"]["came_back"])
        self.assertEqual([f for f in self.runner.findings if f.station == "S5"], [])

    def test_the_faucet_is_asked_once_with_the_address_as_the_page_sends_it_and_the_line_carries_paid_and_the_tx_hash(self):
        self.assertEqual([r["body"] for r in self.double.faucet.requests], [{"address": self.wallet["address"]}])
        self.assertEqual(self.double.faucet.requests[0]["headers"].get("Content-type") or self.double.faucet.requests[0]["headers"].get("content-type"), "application/json")
        self.assertNotIn("cookie", self.double.faucet.requests[0]["headers"], "no session travels to the faucet")
        line = self.outcomes["S5"].line
        self.assertIn("gas: 0 SEAR (0 wei) read from %s, below 0.1 SEAR; the faucet paid: paid true, tx_hash %s, times_paid 1" % (RPC, self.double.faucet.tx_hash), line)
        self.assertEqual(self.runner.facts["faucet"]["answer"]["tx_hash"], self.double.faucet.tx_hash)
        self.assertEqual(self.runner.facts["faucet"]["address"], self.wallet["address"])
        # the balance was read from the chain's public RPC as the corridor reads a chain: eth_getBalance for the wallet, latest
        self.assertEqual(self.double.rpc.calls[0]["body"], {"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [self.wallet["address"], "latest"]})
        self.assertEqual(self.runner.facts["gas_balance"], {"wei": 0, "said": "0 SEAR (0 wei) read from %s" % RPC, "address": self.wallet["address"]})
        outside = [c for c in self.runner.calls if c.outside and c.station == "S5"]
        self.assertEqual([(c.station, c.route, c.status) for c in outside], [("S5", "POST %s" % RPC, 200), ("S5", "POST %s" % FAUCET, 200)])
        self.assertEqual(outside[1].who, "Harriet Founder (at the faucet page)")
        # asking again in the same run asks nothing: once per run
        said = self.runner.fund_the_wallet_from_the_faucet("S5", self.runner.people["harriet"])
        self.assertTrue(said.startswith("faucet: asked once already in this run — the faucet paid: paid true, tx_hash "), said)
        self.assertEqual(len(self.double.faucet.requests), 1)
        self.assertEqual(len(self.double.rpc.calls), 1, "and no second balance read either")

    def test_s7_pays_and_s8_reads_transactable_true_and_names_the_wallet(self):
        self.assertEqual(self.outcomes["S7"].outcome, H.PASS, self.outcomes["S7"].line)
        # Spec T14: the Treasury paid the shortfall through the estate's own road, S7a was proved, and the three payments landed
        self.assertIn("Harness Treasury pays Harness Holdings (%s) the shortfall of US$18.24" % self.wallet["address"], self.outcomes["S7"].line)
        self.assertIn("S7a proved", self.outcomes["S7"].line)
        s8 = self.outcomes["S8"]
        self.assertEqual(s8.outcome, H.PASS, s8.line)
        self.assertIn("readiness: transactable True, reason None; funding wallet: %s on double-stack-1, key %s" % (self.wallet["address"], self.wallet["keyId"]), s8.line)

    def test_the_report_summary_carries_the_wallet_the_gas_and_the_asset_and_still_reads_back(self):
        summary = summary_of(self.runner)
        self.assertIn("Funding wallet: %s on double-stack-1, key %s (GET /v1/workspace; https://testnet.explorer.aeredium.io/address/%s)." % (
            self.wallet["address"], self.wallet["keyId"], self.wallet["address"]), summary)
        self.assertIn("Gas: 0 SEAR (0 wei) read from %s; the faucet paid: paid true, tx_hash %s, times_paid 1." % (RPC, self.double.faucet.tx_hash), summary)
        self.assertIn("The asset: the three payments together need US$18.24 of USDC; Harness Treasury pays Harness Holdings the shortfall through the estate's own road (Spec T14); the harness never mints the asset and holds no key.", summary)
        self.assertIn("Harness Treasury: funding wallet %s — the float Bear funds with USDC on arbitrum, once" % self.double.treasury.source_account, summary)
        path = self.runner.write_report()
        read = H.read_report(path)
        self.assertEqual(read["outcomes"]["S5"], "pass")
        self.assertEqual(len(read["outcomes"]), len(H.STATIONS), "the summary under the table does not disturb the table's reading")
        report = self.runner.report()
        self.assertIn("| POST %s |" % FAUCET, report, "the faucet call is in Every call")
        self.assertIn("| POST %s |" % RPC, report)
        self.assertIn('"paid": true', report, "the faucet's answer travels verbatim in the evidence")

    def test_the_outside_calls_are_measured_and_never_judged_as_the_estates(self):
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings], [("S10", "read-back (policy) of A5"), ("S11", "a payee address with a wrong checksum")],
                         "the RPC's and the faucet's answers raise nothing under the minor-unit law or Rule 13")
        measure = self.runner.facts["optimizer"]
        self.assertEqual(measure["calls"], len([c for c in self.runner.calls if c.station != "S14"]), "the optimizer counts them — every call up to S12; S14 walks after the hats (Spec T19)")
        self.assertIn("checked for Rule 13", self.outcomes["S10"].line)

    def test_a_faucet_refusal_is_not_a_rule_13_finding_because_it_is_not_the_estates(self):
        calls = [H.Call("S5", "Harriet Founder (at the faucet page)", "POST", FAUCET, {"address": "0x00"}, H.Answer("POST", FAUCET, 429, {}, json.dumps({"ok": False, "error": "too many payments from this network today — try again tomorrow"}), 5), "now", outside=True),
                 H.Call("S5", "Harriet Founder", "POST", RPC, {}, H.Answer("POST", RPC, 200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": "0x0", "amountMinor": 1.5}), 5), "now", outside=True)]
        self.assertEqual(H.audit_refusals(calls), [])
        self.assertEqual(H.audit_money(calls), [])
        estate = H.Call("S7", "Cora", "POST", "/v1/sets", {}, H.Answer("POST", "/v1/sets", 429, {}, json.dumps({"ok": False, "error": "x"}), 5), "now")
        self.assertEqual(len(H.audit_refusals([estate])), 1, "the same shape from the estate is the finding it always was")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AWalletAlreadyBorn(unittest.TestCase):
    def test_no_press_is_made_and_the_line_says_so(self):
        double, runner, outcomes = run_against(funding_wallet="born")
        wallet = double.funding_wallet_view()
        o = outcomes["S5"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("funding wallet: %s on double-stack-1, key %s (already born; not pressed for again)" % (wallet["address"], wallet["keyId"]), o.line)
        self.assertEqual([c.route for c in runner.calls if "/funding-wallet" in c.path], [], "FUNDING_WALLET_ALREADY_BORN is never met: the harness reads before it presses")
        self.assertEqual(double.funding_presses, [])
        self.assertIsNone(runner.facts["funding_press"])
        self.assertEqual(len(double.faucet.requests), 1, "a wallet born earlier is still funded where its balance is low")
        self.assertIn("readiness: transactable True", outcomes["S8"].line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheGatewayRefusesOrIsAway(unittest.TestCase):
    def test_a_refusal_is_told_in_the_estates_words_with_the_gateways_sentence_and_s5_fails(self):
        double, runner, outcomes = run_against(funding_wallet="refused")
        o = outcomes["S5"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("funding wallet: not born — refused: WALLET_BIRTH_REFUSED: %s" % WALLET_BIRTH_REFUSED_ON_21_SEPTEMBER, o.line)
        self.assertIn("The gateway said: “PermissionDenied: not authorized”.", o.line)
        press = runner.facts["funding_press"]
        self.assertEqual((press["status"], press["refusal_code"], press["gateway_said"]), (502, "WALLET_BIRTH_REFUSED", "PermissionDenied: not authorized"))
        presses = [c for c in runner.calls if c.route == "POST /v1/workspace/funding-wallet"]
        self.assertEqual([(c.status, c.retry_of) for c in presses], [(502, None)], "a 502 on the press is reported as the estate said it, never retried with the same assertion")
        self.assertEqual(double.funding_presses[-1]["verified"], True, "the estate verified the assertion before the gateway refused")
        self.assertFalse(double.has_funding_wallet())
        self.assertIn("faucet: not asked — the estate has no funding wallet to fund", o.line)
        self.assertEqual(double.faucet.requests, [])
        self.assertIn("readiness: transactable False, reason no funding wallet", outcomes["S8"].line)
        self.assertIn("Funding wallet: none — %s The press answered WALLET_BIRTH_REFUSED: " % NO_FUNDING_WALLET_SENTENCE, summary_of(runner))
        self.assertFalse(any(f.probe.startswith("Rule 13") for f in runner.findings), "the 502 says who refused and quotes them")
        step = next(s for s in runner.evidence["S5"] if s["route"] == "POST /v1/workspace/funding-wallet")
        self.assertIn('"gatewaySaid": "PermissionDenied: not authorized"', step["came_back"], "the gateway's words travel verbatim")
        self.assertIn("WALLET_BIRTH_REFUSED carries the gateway's sentence; GATEWAY_UNAVAILABLE is a fault", step["expected"])

    def test_a_gateway_not_configured_is_a_fault_named_with_its_setting(self):
        double, runner, outcomes = run_against(funding_wallet="unavailable")
        o = outcomes["S5"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("funding wallet: not born — a fault: GATEWAY_UNAVAILABLE: %s (no signing gateway is configured for this deployment)" % GATEWAY_NOT_CONFIGURED, o.line)
        presses = [c for c in runner.calls if c.route == "POST /v1/workspace/funding-wallet"]
        self.assertEqual([(c.status, c.retry_of) for c in presses], [(503, None)])
        self.assertIn('"setting": "GATEWAY_ADDRESS"', presses[0].text)
        self.assertEqual(outcomes["S7"].outcome, H.FAIL)
        self.assertIn("refused at creation — WORKSPACE_NOT_PROVISIONED: %s (no funding wallet)" % NO_FUNDING_WALLET_SENTENCE, outcomes["S7"].line, "Spec 104: requireSourceAccount, in the wallet's own sentence")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheFaucetAnswers(unittest.TestCase):
    def test_a_refusal_is_carried_in_the_faucets_own_sentence_and_s5_still_passes(self):
        double, runner, outcomes = run_against(faucet=FaucetDouble(FaucetDouble.WALLET_LIMIT))
        o = outcomes["S5"]
        self.assertEqual(o.outcome, H.PASS, "the faucet's refusal is the faucet's, not the estate's")
        self.assertIn("below 0.1 SEAR; the faucet refused (HTTP 429): this wallet has already received 4 payments in the last 24 hours — try again tomorrow", o.line)
        self.assertEqual(len(double.faucet.requests), 1)
        self.assertEqual(runner.facts["faucet"]["answer"], {"ok": False, "error": "this wallet has already received 4 payments in the last 24 hours — try again tomorrow"})
        step = next(s for s in runner.evidence["S5"] if s["route"] == "POST %s" % FAUCET)
        self.assertEqual(step["status"], 429)
        self.assertIn("try again tomorrow", step["came_back"])
        self.assertEqual([f for f in runner.findings if f.station in ("S5", "S10") and "faucet" in f.probe.lower()], [])
        self.assertIn("; the faucet refused (HTTP 429): this wallet has already received 4 payments in the last 24 hours — try again tomorrow.", summary_of(runner))

    def test_the_other_refusals_and_a_saved_but_unpaid_request_are_reported_in_the_faucets_words(self):
        for answer, words in ((FaucetDouble.IP_LIMIT, "the faucet refused (HTTP 429): too many payments from this network today — try again tomorrow"),
                              (FaucetDouble.BUDGET, "the faucet refused (HTTP 429): the faucet has reached its daily budget — try again tomorrow"),
                              (FaucetDouble.WAITING, "the faucet refused (HTTP 409): this address already has a request waiting — it will be reviewed shortly")):
            double, runner, outcomes = run_against(faucet=FaucetDouble(answer))
            self.assertIn(words, outcomes["S5"].line, answer)
            self.assertEqual(outcomes["S5"].outcome, H.PASS)
        double, runner, outcomes = run_against(faucet=FaucetDouble(FaucetDouble.QUEUED, times_paid=2))
        self.assertIn('the faucet saved the request without paying (queued for its admin queue): {"ok": true, "queued": true, "times_requested": 1, "times_paid": 2}', outcomes["S5"].line)

    def test_a_faucet_that_cannot_be_reached_or_answers_html_is_reported_verbatim_and_the_estate_is_not_blamed(self):
        double, runner, outcomes = run_against(faucet=FaucetDouble(FaucetDouble.DOWN))
        self.assertEqual(outcomes["S5"].outcome, H.PASS)
        self.assertIn("the faucet could not be reached: POST %s could not be reached: [Errno 61] Connection refused" % FAUCET, outcomes["S5"].line)
        self.assertNotIn("the estate could not be reached", outcomes["S5"].line)
        call = [c for c in runner.calls if c.path == FAUCET][0]
        self.assertEqual(call.status, 0)
        double, runner, outcomes = run_against(faucet=FaucetDouble(FaucetDouble.MALFORMED_ANSWER))
        self.assertIn("the faucet answered HTTP 502: <html><head><title>502 Bad Gateway</title></head><body>nginx</body></html>", outcomes["S5"].line)

    def test_a_balance_at_or_above_the_floor_asks_nothing(self):
        double, runner, outcomes = run_against(rpc=TestnetRpcDouble(balance_wei=T.GAS_FLOOR_WEI))
        self.assertIn("gas: 0.1 SEAR (100000000000000000 wei) read from %s, at or above 0.1 SEAR; the faucet was not asked" % RPC, outcomes["S5"].line)
        self.assertEqual(double.faucet.requests, [])
        self.assertIsNone(runner.facts["faucet"])
        double, runner, outcomes = run_against(rpc=TestnetRpcDouble(balance_wei=T.to_wei("0.5")))
        self.assertIn("gas: 0.5 SEAR (500000000000000000 wei) read from %s, at or above 0.1 SEAR; the faucet was not asked" % RPC, outcomes["S5"].line)
        self.assertEqual(double.faucet.requests, [])
        double, runner, outcomes = run_against(rpc=TestnetRpcDouble(balance_wei=T.GAS_FLOOR_WEI - 1))
        self.assertIn("gas: 0.099999999999999999 SEAR (99999999999999999 wei) read from %s, below 0.1 SEAR; the faucet paid" % RPC, outcomes["S5"].line)
        self.assertEqual(len(double.faucet.requests), 1)

    def test_a_balance_that_could_not_be_read_asks_nothing_because_the_harness_never_invents_a_balance(self):
        double, runner, outcomes = run_against(rpc=TestnetRpcDouble(fault="down"))
        self.assertEqual(outcomes["S5"].outcome, H.PASS, "the RPC is not the estate")
        self.assertIn("gas: the RPC at %s could not be reached: POST %s could not be reached: [Errno 8] nodename nor servname provided, or not known; the faucet was not asked (the harness never invents a balance)" % (RPC, RPC), outcomes["S5"].line)
        self.assertEqual(double.faucet.requests, [])
        self.assertTrue(any(n.startswith("gas: the RPC at %s could not be reached" % RPC) for n in runner.notes["S5"]))
        self.assertIsNone(runner.facts["gas_balance"]["wei"])
        double, runner, outcomes = run_against(rpc=TestnetRpcDouble(fault="error"))
        self.assertIn('gas: the RPC at %s refused eth_getBalance: {"code": -32000, "message": "header not found"}; the faucet was not asked' % RPC, outcomes["S5"].line)
        self.assertEqual(double.faucet.requests, [])
        double, runner, outcomes = run_against(rpc=TestnetRpcDouble(fault="not_json"))
        self.assertIn("gas: the RPC at %s answered HTTP 502 without JSON: <html><body>502 Bad Gateway</body></html>; the faucet was not asked" % RPC, outcomes["S5"].line)
        self.assertEqual(double.faucet.requests, [])
        self.assertIn("Gas: the RPC at %s answered HTTP 502 without JSON" % RPC, summary_of(runner))
        self.assertIn("; the faucet was not asked.", summary_of(runner))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheRegisterIsTheJudge(unittest.TestCase):
    """Spec T13 §3: S6 judges each payee on the register's whitelistStatus, not on the press's answer."""

    def test_a_register_that_reads_whitelisted_after_the_count_passes_s6_though_the_press_answered_proposed(self):
        double, runner, outcomes = run_against(mirror_lags=True)
        o = outcomes["S6"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("Northwind Supplies: created on arbitrum; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): proposed", o.line, "the press's answer, recorded and not judged")
        self.assertIn("register: Northwind Supplies whitelisted, Contoso Legal whitelisted", o.line)
        self.assertNotIn("mirror disagrees", o.line)
        for record in runner.facts["payees"]:
            self.assertEqual(record["count"], {"collected": 2, "required": 2})
            self.assertEqual(record["register_status"], "whitelisted")
            self.assertIsNone(record["mirror"])
            self.assertEqual(record["approved"], {"whitelistStatus": "proposed"})
        step = next(s for s in runner.evidence["S6"] if s["route"] == "GET /v1/payees")
        self.assertIn("the judgement is the register's, not the press's (Spec T13 §3)", step["expected"])

    def test_a_register_that_reads_proposed_after_two_of_two_fails_s6_with_the_mirror_sentence(self):
        double, runner, outcomes = run_against(mirror_lags=True, register_corrects=False)
        o = outcomes["S6"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        sentence = "the platform counted 2 of 2 and the register reads proposed; the estate's mirror disagrees with the platform"
        self.assertIn("register: Northwind Supplies proposed (%s), Contoso Legal proposed (%s)" % (sentence, sentence), o.line)
        for record in runner.facts["payees"]:
            self.assertEqual(record["mirror"], sentence)
            self.assertEqual(record["mirror"], H.MIRROR_DISAGREES % (2, 2, "proposed"))
            self.assertEqual(record["register_status"], "proposed")
        self.assertEqual([f for f in runner.findings if f.station == "S6"], [], "the estate said why at each press; the disagreement is S6's line, in one sentence")

    def test_the_mirror_sentence_is_only_for_proposed_after_a_met_count(self):
        self.assertIsNone(H.Runner.mirror_sentence({"count": {"collected": 1, "required": 2}}, "proposed"), "the count was not met: the register is simply not there yet")
        self.assertIsNone(H.Runner.mirror_sentence({"count": {"collected": 2, "required": 2}}, "pending_promotion"), "pending after a met count is the platform not activating, another truth")
        self.assertIsNone(H.Runner.mirror_sentence({}, "proposed"), "nobody's press counted")
        self.assertEqual(H.Runner.mirror_sentence({"count": {"collected": 2, "required": 2}}, "proposed"), H.MIRROR_DISAGREES % (2, 2, "proposed"))


class TheTablesFacts(unittest.TestCase):
    def test_the_testnet_and_the_faucet_as_the_record_and_the_page_name_them(self):
        self.assertEqual(T.TESTNET_CHAIN_ID, 2237)
        self.assertEqual(hex(T.TESTNET_CHAIN_ID), "0x8bd")
        self.assertEqual(T.TESTNET_NAME, "AEREDIUM testnet2")
        self.assertEqual(T.NATIVE_COIN, "SEAR")
        self.assertEqual(T.TESTNET_RPC_URL, RPC)
        self.assertEqual(T.TESTNET_EXPLORER_URL, "https://testnet.explorer.aeredium.io")
        self.assertEqual(T.FAUCET_PAGE_URL, "https://aeredium.io/faucet.html")
        self.assertEqual(T.FAUCET_REQUEST_URL, FAUCET)
        self.assertEqual(T.FAUCET_PAYS_SEAR, "0.5")
        self.assertEqual(T.FAUCET_LIMITS, "four payments per wallet and eight per IP in a day, and 200 SEAR across everyone")
        self.assertEqual(T.GAS_FLOOR_SEAR, "0.1")
        self.assertEqual(T.GAS_FLOOR_WEI, 10 ** 17)
        for url in (T.TESTNET_RPC_URL, T.TESTNET_EXPLORER_URL, T.FAUCET_PAGE_URL, T.FAUCET_REQUEST_URL):
            self.assertTrue(url.startswith("https://") and ".aeredium.io" in url or url.startswith("https://aeredium.io/"), url)

    def test_the_coin_arithmetic_is_strings_and_integers(self):
        self.assertEqual(T.to_wei("0.5"), 500000000000000000)
        self.assertEqual(T.to_wei("0.1"), T.GAS_FLOOR_WEI)
        self.assertEqual(T.coin_amount(0), "0")
        self.assertEqual(T.coin_amount(500000000000000000), "0.5")
        self.assertEqual(T.coin_amount(10 ** 18), "1")
        self.assertEqual(T.coin_amount(1234500000000000000), "1.2345")
        self.assertEqual(T.coin_amount(99), "0.000000000000000099")
        with self.assertRaises(ValueError):
            T.coin_amount(-1)
        with self.assertRaises(ValueError):
            T.coin_amount(0.5)  # type: ignore[arg-type]
        self.assertEqual(T.payments_total(["1250.00", "4999.99", "12000.00"]), "18249.99")
        self.assertEqual(T.payments_total(["0.075", "1"]), "1.075")
        self.assertEqual(T.payments_total(["1", "2"]), "3.00")

    def test_no_faucet_or_treasury_address_is_written_in_the_tables(self):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aer360_tables.py"), "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("0xb0EC", text)
        self.assertNotIn("0xD65C", text)


if __name__ == "__main__":
    unittest.main()
