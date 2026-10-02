"""
Spec T23 (2 October 2026): the harness funds its own agent from its own estate, and no station stops to ask the operator for anything.

Bear, the same evening: "I am not intervening in the harnessed dealings. It has to be done automatically. We already financed the gas.
That's all there is. Now the harness has to prove that the trade can get all the way through. If not, there are bugs." The run of that
evening (2026-10-02-223735-pathfinder-pathfinder) stopped at S11 saying "this run's agent is born with an empty wallet, and no station
funds it"; and S5 and S9 failed because the connector's customer row carries the funding wallet registered at the owner's birth while
the estate harness's file had since been rewritten.

Each test here was red on main. They run against the Pathfinder double (tests/pathfinder_double.py) beside the estate double
(tests/test_aer360_double.py): Harness Holdings and Harness Treasury as one run of the estate harness leaves them, the child wallet's USDC
on the estate's chain, so what Holdings pays through the estate's own road is what the Wallet door reads and the swap sells. No network.
"""
import json
import os
import re
import sys
import unittest
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_harness as E  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as ET  # noqa: E402
import aerconnect_harness as P  # noqa: E402
import corridor_harness as H  # noqa: E402
from tests.test_aer360_double import VENUE_STIPULATION  # noqa: E402

try:
    from .test_aerconnect_harness import FUNDING, PathfinderBase
except ImportError:  # run as a top-level module by `unittest discover tests`
    from test_aerconnect_harness import FUNDING, PathfinderBase

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Sentences that told a person to act, none of which may be said on a run that funds its own agent.
A_PERSON_IS_ASKED = ("no station funds it", "nothing arrived within", "the harness reads the wallet for", "send ")


def write_back(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def every_sentence_of(runner, said):
    return [o.line for o in runner.outcomes] + [n for notes in runner.notes.values() for n in notes] + list(said) + [runner.report()]


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheHarnessFundsItsOwnAgent(PathfinderBase):
    def drain_holdings_gas(self):
        """Harness Holdings' gas account to nothing for one test — the platform's ledger debited — and the drained amount credited back after it."""
        platform, account = self.estate_double.platform, self.estate_double.aap_account_id
        available = platform.balance(account)["available_usd_cents"]
        platform.debit(account, available, "drained-for-the-test-%s" % uuid.uuid4(), "arbitrum", "0x" + "00" * 32, "0x" + "00" * 32)
        self.addCleanup(platform.credit, account, available, "put-back-after-the-test-%s" % uuid.uuid4(), "the test puts the gas back", "test", "test")
        return available

    def estate_routes(self, runner, station="S11"):
        """The estate's road as this run's own evidence carries it: the routes the estate runner walked, in order."""
        return [s["route"] for s in runner.steps[station] if "(%s)" % E.A.ESTATE["company"] in s["who"] or "(%s)" % ET.TREASURY["company"] in s["who"]]

    def test_s11_funds_the_wallet_from_holdings_through_the_estates_own_road_and_the_trade_goes_on(self):
        estate = self.estate_double
        transfers_before = len(estate.chain.transfers)
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        address = runner.facts["wallet"]["address"]
        # §1 the payee is the child wallet: created, promoted and pressed to the roster's quorum exactly as S6 does Northwind; the register the judge
        name = P.PAYEE_NAME % runner.label
        payee = estate.payees[runner.state["estate"]["payee_id"]]  # this run's own, by id: every walk in this class names its agent alike
        self.assertEqual(payee["displayName"], name)
        rows = [a for a in estate.addresses.values() if a["payeeId"] == payee["id"]]
        self.assertEqual([(a["chain"], a["address"], a["whitelistStatus"]) for a in rows], [("arbitrum", address.lower(), "whitelisted")])
        self.assertEqual((payee["defaultAsset"], payee["defaultChain"]), ("USDC", "arbitrum"))
        # §2 one set of one payment of exactly TRADE_RAW, from Holdings' operating account to the wallet, settled and confirmed; the Treasury not asked
        funded = runner.facts["funded"]
        set_row = estate.sets[funded["set_id"]]
        self.assertEqual(set_row["status"], "settled")
        self.assertEqual(set_row["sourceAccount"], estate.source_account)
        self.assertEqual([(i["address"], i["amountMinor"], i["asset"], i["status"], i["isOneOff"]) for i in set_row["instructions"]],
                         [(address.lower(), str(P.TRADE_RAW), "USDC", "confirmed", False)])
        self.assertEqual(estate.chain.transfers[transfers_before:], [{"from": estate.source_account.lower(), "to": address.lower(), "minor": P.TRADE_RAW}])
        self.assertEqual((funded["shortfall"], funded["treasury_payment"], funded["gas_credited"]), (0, None, 0))
        self.assertEqual((funded["balance_before"], funded["balance_after"], funded["landed"]), (0, P.TRADE_RAW, True))
        # §3 the harness waited for its own money, and the trade spent the whole ten cents the moment it landed
        self.assertIn(P.FUNDING_SENTENCE % (address, "arbitrum", funded["set_id"], runner.run_id), runner.notes["S11"])
        self.assertIn(P.FUNDED_SENTENCE % (P.TRADE_RAW, funded["tx_hash"]), runner.notes["S11"])
        self.assertTrue(str(funded["tx_hash"]).startswith("0x") and str(funded["user_op_hash"]).startswith("0x"))
        self.assertIn("the balances reconcile: USDC 100000 → 0", self.line_of(runner, "S12"))
        self.assertEqual(estate.chain.balance_of(address), 0, "the swap sold exactly the ten cents Holdings paid")
        # the line tells the whole road
        line = self.line_of(runner, "S11")
        self.assertIn("the trade: funded by Harness Holdings through the estate's own road — the payee %s: created on arbitrum; promoted; " % name, line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted; the register reads whitelisted; Harness Holdings holds US$", line)
        self.assertIn(", at or above the trade's US$0.10, so the Treasury was not asked; Harness Holdings paid the agent's wallet US$0.10: submitted: status approved, "
                      "approvalsRequired 0; landed (+US$0.10): instruction confirmed, run settled, userOpHash 0x", line)
        self.assertIn("payee US$0.00 → US$0.10, gas US$0.31; ticket ", line)
        self.assertIn("sponsored by the paymaster", line)
        # the operator is asked nothing: no sentence of the run tells a person to send money
        for text in every_sentence_of(runner, self.said):
            for words in A_PERSON_IS_ASKED:
                self.assertNotIn(words, text, words)
            self.assertNotRegex(text, r"(?<![\w$])fund 0x", "a sentence asks a person to fund an address")

    def test_the_estates_road_is_walked_in_order_and_recorded_call_by_call_in_this_runs_s11(self):
        runner = self.walk()
        set_id = runner.facts["funded"]["set_id"]
        address_id = runner.state["estate"]["address_id"]
        routes = self.estate_routes(runner)
        expected_order = ["POST /v1/auth/login/options", "POST /v1/auth/login/verify", "GET /v1/workspace", "GET %s" % ET.FUNDING_BALANCES_ROUTE,
                          "POST /v1/payees", "POST /v1/payees/addresses/%s/promote" % address_id, "POST /v1/payees/addresses/%s/approve" % address_id,
                          "GET /v1/payees", "POST /v1/sets/review", "POST /v1/sets", "POST /v1/sets/%s/submit" % set_id, "POST /v1/sets/%s/execute" % set_id,
                          "GET /v1/sets/%s" % set_id, "GET %s?limit=%d" % (ET.AUDIT_EXPORT_ROUTE, ET.AUDIT_EXPORT_LIMIT)]
        positions = [routes.index(route) for route in expected_order]
        self.assertEqual(positions, sorted(positions), routes)
        self.assertEqual(routes.count("POST /v1/payees/addresses/%s/approve" % address_id), 2, "the roster presses to its quorum of two, and no further")
        self.assertEqual(routes.count("POST /v1/sets"), 1, "one set")
        self.assertNotIn("POST /v1/approvals/%s/challenge" % set_id, routes, "a payment of ten cents under the hold asks no second hand")
        self.assertEqual([r for r in routes if r.startswith("POST /v1/sets/review")], ["POST /v1/sets/review"], "the review once: the gas gate passed")
        # every estate step is a step of this run: the route, who at which estate, what was sent, what came back, the expectation and the result
        for step in runner.steps["S11"]:
            if "(%s)" % E.A.ESTATE["company"] in step["who"]:
                for key in ("route", "sent", "came_back", "expected", "result", "status", "elapsed_ms"):
                    self.assertIn(key, step, step["route"])
                self.assertTrue(step["expected"], step["route"])
        who = {s["who"] for s in runner.steps["S11"] if "(%s)" % E.A.ESTATE["company"] in s["who"]}
        self.assertIn("Harriet Founder (%s)" % E.A.ESTATE["company"], who)
        self.assertIn("Cora Clerk (%s)" % E.A.ESTATE["company"], who, "the clerk authors and executes the payment, as T14 has it")
        with open(os.path.join(runner.folder.path, "evidence.jsonl"), encoding="utf-8") as handle:
            evidence = [json.loads(line) for line in handle]
        self.assertEqual(len(evidence), sum(len(v) for v in runner.steps.values()))
        report = runner.report()
        self.assertIn("POST /v1/sets/%s/execute — Cora Clerk (%s)" % (set_id, E.A.ESTATE["company"]), report)
        self.assertIn("Note: " + P.FUNDING_SENTENCE % (runner.facts["wallet"]["address"], "arbitrum", set_id, runner.run_id), report)

    def test_holdings_short_the_treasury_pays_the_shortfall_first_then_holdings_pays(self):
        estate = self.estate_double
        holdings, treasury = estate.source_account.lower(), estate.treasury.source_account.lower()
        self.holdings_and_treasury_hold(0, 10 ** 8)
        transfers_before = len(estate.chain.transfers)
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        address = runner.facts["wallet"]["address"].lower()
        funded = runner.facts["funded"]
        self.assertEqual((funded["holdings_before"], funded["shortfall"]), (0, P.TRADE_RAW))
        self.assertEqual(estate.chain.transfers[transfers_before:], [{"from": treasury, "to": holdings, "minor": P.TRADE_RAW},
                                                                      {"from": holdings, "to": address, "minor": P.TRADE_RAW}],
                         "the Treasury pays Holdings the shortfall first, then Holdings pays the wallet — exactly the trade's amount each")
        paid_t = estate.treasury.sets[funded["treasury_payment"]]
        self.assertEqual((paid_t["status"], paid_t["sourceAccount"].lower()), ("settled", treasury))
        self.assertEqual([(i["address"], i["amountMinor"], i["isOneOff"]) for i in paid_t["instructions"]], [(holdings, str(P.TRADE_RAW), True)])
        line = self.line_of(runner, "S11")
        self.assertIn("Harness Holdings holds US$0.00, short of the trade's US$0.10 by US$0.10, and Harness Treasury holds US$100.00; Harness Treasury paid Harness Holdings "
                      "(%s) the shortfall of US$0.10 first: " % estate.source_account, line)
        self.assertIn("Harriet Founder signed (1 of 1): approved; landed (+US$0.10): instruction confirmed, run settled, userOpHash 0x", line)
        self.assertIn("; Harness Holdings paid the agent's wallet US$0.10: submitted: status approved, approvalsRequired 0; landed (+US$0.10)", line)
        routes = self.estate_routes(runner)
        self.assertLess(routes.index("POST /v1/sets/%s/execute" % funded["treasury_payment"]), routes.index("POST /v1/sets/%s/execute" % funded["set_id"]))
        self.assertLess(routes.index("POST /v1/payees"), routes.index("POST /v1/sets/%s/execute" % funded["treasury_payment"]), "the payee is made before any money moves")

    def test_treasury_short_s11_stops_with_t14s_sentence_and_nothing_is_sent(self):
        estate = self.estate_double
        self.holdings_and_treasury_hold(0, 0)
        calls_before, transfers_before, credits_before, payees_before = len(estate.calls), len(estate.chain.transfers), len(estate.platform.requests), len(estate.payees)
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.STOPPED, s11.line)
        sentence = ET.TREASURY_SHORT_SENTENCE % ("US$0.00", "US$0.10", estate.treasury.source_account, "arbitrum")
        self.assertEqual(sentence, "Harness Treasury holds US$0.00; the run needs US$0.10; fund %s on arbitrum" % estate.treasury.source_account)
        self.assertEqual(s11.line, "the trade: %s — %s (the trade needs US$0.10 and Harness Holdings holds US$0.00); nothing was sent" % (E.TREASURY_SHORT, sentence))
        self.assertEqual([c["path"] for c in estate.calls[calls_before:] if c["method"] == "POST" and c["path"].startswith(("/v1/sets", "/v1/payees"))], [], "nothing was sent, and no payee was made")
        self.assertEqual((len(estate.chain.transfers), len(estate.platform.requests), len(estate.payees)), (transfers_before, credits_before, payees_before))
        self.assertEqual(self.words(runner)["S13"], P.PASS, "the agent whose wallet holds nothing is torn down")
        self.assertEqual(P.exit_code_of(runner.outcomes), 2)

    def test_the_estate_refuses_the_child_wallet_as_a_payee_and_s11_fails_in_the_estates_sentence(self):
        estate = self.estate_double
        address = H.checksum_address("0x" + "ab" * 20)
        self.double.wallet_address = address
        estate.refuses_payee_addresses = (address.lower(),)
        self.addCleanup(setattr, estate, "refuses_payee_addresses", ())
        calls_before, transfers_before = len(estate.calls), len(estate.chain.transfers)
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.FAIL, s11.line)
        self.assertEqual(s11.line, "the trade: " + P.PAYEE_REFUSED_SENTENCE % (
            address, "%s: ADDRESS_PROPOSAL_REFUSED: %s (a stipulation this door applies whatever the charter says; this double stands in for an estate that does)"
            % (P.PAYEE_NAME % runner.label, VENUE_STIPULATION)))
        self.assertEqual([c["path"] for c in estate.calls[calls_before:] if c["method"] == "POST" and c["path"].startswith("/v1/sets")], [], "nothing was sent")
        self.assertEqual(len(estate.chain.transfers), transfers_before)
        self.assertNotIn(address.lower(), [a["address"] for a in estate.addresses.values()], "no payee row carries the refused address")
        self.assertNotIn("estate", runner.state, "nothing of this run's stands at the estate")
        self.assertEqual(self.words(runner)["S13"], P.PASS)

    def test_holdings_gas_below_the_ceiling_is_credited_through_the_admin_road_before_the_set_is_submitted(self):
        estate = self.estate_double
        platform, account = estate.platform, estate.aap_account_id
        available = self.drain_holdings_gas()
        self.assertEqual(platform.balance(account)["available_usd_cents"], 0)
        requests_before = len(platform.requests)
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        posts = [(json.loads(r["body"])["amount_usd_cents"], r["path"], json.loads(r["body"])["reason"]) for r in platform.requests[requests_before:]]
        self.assertEqual(posts, [(1000, ET.ADMIN_CREDIT_ROUTE % account, ET.ADMIN_CREDIT_REASON % runner.estate.run_stamp)],
                         "U3's ten dollars, once, for Holdings' account, with the run named as the reason")
        self.assertEqual(runner.facts["funded"]["gas_credited"], 1000)
        routes = self.estate_routes(runner)
        credit = next(i for i, r in enumerate(routes) if r.endswith(ET.ADMIN_CREDIT_ROUTE % account))
        self.assertLess(routes.index("POST /v1/sets/review"), credit, "the review's gas gate refused first")
        self.assertLess(credit, routes.index("POST /v1/sets"), "credited before the set is created")
        self.assertLess(credit, routes.index("POST /v1/sets/%s/submit" % runner.facts["funded"]["set_id"]), "and before it is submitted")
        self.assertEqual(routes.count("POST /v1/sets/review"), 2, "the review asked again after the credit")
        self.assertIn("the review refused GAS_SHORTFALL (Your gas account holds US$0.00. This set needs at most US$0.40 of gas. Nothing was sent. Buy gas below.); "
                      "gas credited and the review asked again", self.line_of(runner, "S11"))
        self.assertNotIn(platform.admin_key, runner.report() + "\n".join(self.said), "the admin credential is never printed")

    def test_no_admin_credential_and_gas_below_the_ceiling_stops_s11_with_the_estates_sentence_and_nothing_is_sent(self):
        estate = self.estate_double
        platform, account = estate.platform, estate.aap_account_id
        self.drain_holdings_gas()
        calls_before, transfers_before = len(estate.calls), len(estate.chain.transfers)
        runner = self.walk(estate_admin_env=os.path.join(self.tmp, "no-such-admin.env"))
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.STOPPED, s11.line)
        self.assertTrue(s11.line.endswith("%s — %s; nothing was sent" % (E.NO_ADMIN_CREDENTIAL, ET.NO_GAS_CREDIT_ROAD_SENTENCE)), s11.line)
        self.assertEqual([c["path"] for c in estate.calls[calls_before:] if c["method"] == "POST" and c["path"].startswith("/v1/sets") and not c["path"].endswith("/review")], [])
        self.assertEqual(len(estate.chain.transfers), transfers_before)
        self.assertTrue(any(n.endswith("is not filed: the gas credits below will fail with %r" % ET.NO_GAS_CREDIT_ROAD_SENTENCE) for n in runner.notes["S11"]), runner.notes["S11"])

    def test_a_wallet_that_already_holds_the_trades_amount_is_not_funded_again(self):
        estate = self.estate_double
        self.double.wallet_usdc = P.TRADE_RAW
        calls_before, transfers_before, payees_before = len(estate.calls), len(estate.chain.transfers), len(estate.payees)
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        address = runner.facts["wallet"]["address"]
        self.assertIn(P.HELD_ALREADY_SENTENCE % (address, "arbitrum", P.TRADE_RAW, P.TRADE_RAW), runner.notes["S11"])
        self.assertIn("the trade: the wallet held 100000 minor units of USDC already, so nothing was funded; ticket ", self.line_of(runner, "S11"))
        self.assertEqual((len(estate.calls), len(estate.chain.transfers), len(estate.payees)), (calls_before, transfers_before, payees_before), "the estate was not asked")
        self.assertNotIn("funded", runner.facts)

    def test_the_estates_people_absent_stops_s11_with_the_estate_harnesss_own_sentence_before_anything_is_sent(self):
        estate = self.estate_double
        empty_store = os.path.join(self.tmp, "no-estate-store")
        os.makedirs(empty_store)
        calls_before = len(estate.calls)
        runner = self.walk(estate_store=empty_store)
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.STOPPED, s11.line)
        self.assertEqual(s11.line, "the trade: " + P.NO_ESTATE_FOUNDER_SENTENCE % (E.FOUNDER_NOT_ENROLLED, "Harriet Founder", os.path.join(empty_store, "harness-holdings", "harriet.json")))
        self.assertIn("run aer360_harness.py first", s11.line)
        self.assertEqual(len(estate.calls), calls_before, "nothing was asked of the estate")
        self.assertEqual(self.words(runner)["S13"], P.PASS)

    def test_the_treasury_not_born_stops_s11_with_the_estate_harnesss_own_sentence(self):
        """Holdings short and no Treasury passkey stored: the estate harness's own stop, in its words, a prerequisite this run cannot get past."""
        estate = self.estate_double
        self.holdings_and_treasury_hold(0, 10 ** 8)
        treasury_key = os.path.join(self.estate_store, ET.TREASURY["client_id"], "harriet.json")
        with open(treasury_key, encoding="utf-8") as handle:
            kept = handle.read()
        os.remove(treasury_key)
        self.addCleanup(write_back, treasury_key, kept)
        transfers_before = len(estate.chain.transfers)
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.STOPPED, s11.line)
        self.assertTrue(s11.line.startswith("the trade: %s — no passkey is stored for its founder at %s and no --treasury-invite <link> was given" % (E.TREASURY_NOT_BORN, treasury_key)), s11.line)
        self.assertTrue(s11.line.endswith("; nothing was sent"))
        self.assertEqual(len(estate.chain.transfers), transfers_before)

    def test_the_estates_secrets_never_appear_whole_in_the_report_the_evidence_or_the_terminal(self):
        estate = self.estate_double
        runner = self.walk()
        report = runner.report()
        with open(os.path.join(runner.folder.path, "evidence.jsonl"), encoding="utf-8") as handle:
            evidence = handle.read()
        said = "\n".join(self.said)
        with open(os.path.join(self.estate_store, "harness-holdings", "harriet.json"), encoding="utf-8") as handle:
            stored = json.load(handle)
        secrets = {"the platform's admin key": [estate.platform.admin_key], "an estate session cookie": list(estate.sessions),
                   "an estate CSRF token": [s["csrfToken"] for s in estate.sessions.values()],
                   "the founder's private key": [line for line in str(stored.get("pem") or stored.get("key") or "").splitlines() if len(line) >= 16 and "-----" not in line]}
        for what, values in secrets.items():
            self.assertTrue(values, "the walk carried %s" % what)
            for value in values:
                for text, where in ((report, "the report"), (evidence, "the evidence"), (said, "the terminal")):
                    self.assertNotIn(value, text, "%s appears whole in %s" % (what, where))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheFundingWalletIsTheConnectors(PathfinderBase):
    def test_an_existing_owner_sends_the_connectors_registered_funding_wallet_and_s5_and_s9_pass_against_it(self):
        first = self.walk()
        self.assertEqual(self.words(first), {s: P.PASS for s in P.STATION_IDS}, [first.line(o) for o in first.outcomes])
        self.assertIn("funding wallet %s — the file's (%s): the connector lists no funding wallet for this owner yet, and this press registers it" % (FUNDING, self.funding),
                      self.line_of(first, "S3"))
        press = next(step for step in first.steps["S3"] if step["route"] == "POST " + P.AGENTS_ROUTE)
        self.assertEqual(press["sent"]["body"]["fundingAddress"], FUNDING)
        # the connector registered the root once; a later estate run rewrites the file — and then loses it altogether
        other = H.checksum_address("0x" + "d1" * 20)
        with open(self.funding, "w", encoding="utf-8") as handle:
            json.dump({"address": other, "chain": "arbitrum", "keyId": "key-2"}, handle)
        second = self.walk()
        self.assertEqual(self.words(second), {s: P.PASS for s in P.STATION_IDS}, [second.line(o) for o in second.outcomes])
        self.assertIn("funding wallet %s — the connector's, registered at the owner's first agent and kept since (GET /v1/account customer.fundingWallet; a funding root is "
                      "registered once, connector Spec 8), so the file at %s was not read" % (FUNDING, self.funding), self.line_of(second, "S3"))
        press = next(step for step in second.steps["S3"] if step["route"] == "POST " + P.AGENTS_ROUTE)
        self.assertEqual(press["sent"]["body"]["fundingAddress"], FUNDING, "the connector's, not the file's")
        self.assertIn("minted against the owner's funding wallet %s" % FUNDING, self.line_of(second, "S5"))
        self.assertNotIn(other, self.line_of(second, "S3") + self.line_of(second, "S5") + self.line_of(second, "S9"))
        os.remove(self.funding)
        third = self.walk()
        self.assertEqual(self.words(third), {s: P.PASS for s in P.STATION_IDS}, "the file is used only when the owner is born")

    def test_a_new_owner_sends_the_files_and_without_it_s3_refuses_before_any_press_in_the_consents_sentence(self):
        os.remove(self.funding)
        runner = self.walk()
        s3 = runner.outcome_of("S3")
        self.assertEqual(s3.outcome, P.STOPPED, s3.line)
        self.assertIn("run aer360_harness.py first", s3.line)
        self.assertFalse(self.reached("POST", P.AGENTS_ROUTE), "no press")
        self.assertEqual([m for m, p, _ in self.double.calls if p == P.ACCOUNT_ROUTE], ["GET", "GET"], "S2's read and S3's: the connector is asked first, and holds none")

    def test_a_resumed_run_reads_the_connectors_funding_wallet_for_s5(self):
        first = self.walk()
        with open(self.funding, "w", encoding="utf-8") as handle:
            json.dump({"address": H.checksum_address("0x" + "d1" * 20), "chain": "arbitrum", "keyId": "key-2"}, handle)
        # a run that died after S7: its agent stands, and the resumed run's S5 must expect the connector's wallet, not the file's
        second = self.runner()
        for station, title in P.STATIONS[:7]:
            self.assertEqual(second.run_station(station, title).outcome, P.PASS)
        resumed = self.walk(start_at="S5")
        self.assertEqual(resumed.outcome_of("S5").outcome, P.PASS, self.line_of(resumed, "S5"))
        self.assertIn("minted against the owner's funding wallet %s" % FUNDING, self.line_of(resumed, "S5"))


class TheWordsAreGone(unittest.TestCase):
    def test_no_station_funds_it_is_said_nowhere_in_the_harness_and_the_dry_walk_carries_the_new_s11_lines(self):
        with open(os.path.join(ROOT, "aerconnect_harness.py"), encoding="utf-8") as handle:
            harness = handle.read()
        self.assertNotIn("no station funds it", harness)
        self.assertFalse(hasattr(P, "FUND_SENTENCE") or hasattr(P, "UNFUNDED_SENTENCE"), "the sentences that asked a person are gone")
        with open(os.path.join(ROOT, "tests", "fixtures", "aerconnect-dry-walk.txt"), encoding="utf-8") as handle:
            walk = handle.read()
        self.assertNotIn("no station funds it", walk)
        self.assertIn(P.FUNDING_SENTENCE % ("<wallet address>", "arbitrum", "<set id>", "<run id>"), walk)
        self.assertIn(P.FUNDED_SENTENCE % (P.TRADE_RAW, "<hash>"), walk)
        self.assertIn("POST /v1/payees", walk)
        self.assertIn("POST /v1/sets/review", walk)
        self.assertIn(ET.TREASURY_SHORT_SENTENCE % ("<what it holds>", "US$0.10", "<the Treasury's address>", "arbitrum"), walk)
        self.assertIn(ET.ADMIN_CREDIT_ROUTE % "<workspace.aapAccountId>", walk)

    def test_the_estate_is_named_from_the_command_line_as_the_estate_harness_names_it(self):
        lines = P.dry_lines(store_dir="/s", estate_base="https://estate.example", estate_store="/e")
        s3 = next(line for line in lines if line.startswith("S3 — GET /v1/account"))
        self.assertIn("[file] the funding wallet from /e/harness-holdings/funding-wallet.json", s3)
        s11 = [line for line in lines if line.startswith("S11 — [estate")]
        self.assertTrue(s11[0].startswith("S11 — [estate https://estate.example] POST /v1/auth/login/options"), s11[0])
        self.assertIn("/e/harness-holdings", s11[0])
        self.assertIn("/e/admin.env", s11[1])
        self.assertIn("/e/harness-treasury", s11[2])
        default = P.dry_lines(store_dir="/s")
        self.assertIn("[estate %s]" % E.DEFAULT_BASE, next(line for line in default if line.startswith("S11 — [estate")))
        self.assertEqual(P.ESTATE_STORE_DIR, "~/.aer360-harness")
        self.assertEqual(P.ESTATE_BASE, "https://accounts.aeredium.io")

    def test_the_payee_road_is_one_writing_shared_by_the_two_harnesses(self):
        import aer360_estate_road as R
        with open(os.path.join(ROOT, "aer360_harness.py"), encoding="utf-8") as handle:
            estate = handle.read()
        self.assertIn("R.propose_payee(self, founder, payee[\"name\"], payee[\"key\"], address, T.PAYEE_CHAIN, \"S6\")", estate)
        self.assertIn("R.judge_payee_register(self, founder, \"S6\", self.facts[\"payees\"]", estate)
        self.assertNotIn('created = self.request(founder, "POST", "/v1/payees", body, "S6")', estate, "S6 no longer carries its own writing of the presses")
        self.assertIn('R.propose_payee(estate, founder, name, self.label, address, chain, "S11")', harness_text())
        self.assertEqual(sorted(R.__all__), ["judge_payee_register", "propose_payee", "register_words"])


def harness_text():
    with open(os.path.join(ROOT, "aerconnect_harness.py"), encoding="utf-8") as handle:
        return handle.read()


if __name__ == "__main__":
    unittest.main()
