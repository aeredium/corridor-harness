"""
The rehearsal (Spec P1d): one sponsored operation on the tester's own road, judged in dollars against the chain's
receipt — proved against doubles of the Police, the Wallet, the platform and the chain's RPC that issue sentinel
secrets. Each test here was red on main, where `corridor_harness.py rehearse` did not exist.
"""
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import tables as T  # noqa: E402
import aer360_tables as AT  # noqa: E402

try:
    from . import rehearsal_doubles as D
except ImportError:  # run as a top-level module by `unittest discover tests`
    import rehearsal_doubles as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARTED = _dt.datetime(2026, 9, 24, 5, 20, 0, tzinfo=_dt.timezone.utc)
RUN_ID = "20260924-052000"


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def sleep(self, seconds):
        self.now += seconds

    def __call__(self):
        return self.now


class RehearsalBase(unittest.TestCase):
    """A store with the consent and the two credential files, the pins set to the double's, and the roads routed to the doubles."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = os.path.join(self.tmp, "corridor-harness")
        os.makedirs(self.store)
        self.admin_env = os.path.join(self.tmp, "aer360-harness", T.ADMIN_ENV_FILE)
        os.makedirs(os.path.dirname(self.admin_env))
        self.sandbox_env = os.path.join(self.store, T.SANDBOX_ENV_FILE)
        self.saved_sandbox = dict(T.SANDBOX)
        T.SANDBOX["account_id"] = D.ACCOUNT_ID
        T.SANDBOX["wallet_address"] = D.WALLET
        self.access_token = D.sentinel("access")
        self.refresh_token = D.sentinel("refresh")
        with open(os.path.join(self.store, "%s.json" % T.SANDBOX["label"]), "w", encoding="utf-8") as handle:
            json.dump({"label": T.SANDBOX["label"], "access_token": self.access_token, "refresh_token": self.refresh_token,
                       "client_id": "mcp-double", "expires_at": time.time() + 3600}, handle)

    def tearDown(self):
        T.SANDBOX.clear()
        T.SANDBOX.update(self.saved_sandbox)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def file_credentials(self, platform, admin_key=None, account_key=None):
        with open(self.admin_env, "w", encoding="utf-8") as handle:
            handle.write("%s=%s\n%s=%s\n" % (T.ADMIN_ENV_URL_KEY, D.PLATFORM, T.ADMIN_ENV_KEY_KEY, admin_key or platform.admin_key))
        with open(self.sandbox_env, "w", encoding="utf-8") as handle:
            handle.write("%s=%s\n" % (T.SANDBOX_ENV_KEY_KEY, account_key or platform.account_key))

    def doubles(self, platform_kw=None, session_kw=None):
        platform = D.PlatformDouble(**(platform_kw or {}))
        session = D.CorridorDouble(platform, **(session_kw or {}))
        rpc = D.RpcDouble(platform)
        self.file_credentials(platform)
        return platform, session, rpc

    def rehearse(self, platform, session, rpc, argv=(), real_time=False, oauth=None, **overrides):
        said = []
        clock = FakeClock()
        inject = dict(say=said.append, sleep=clock.sleep, clock=clock, session_factory=lambda label: session,
                      http=D.router(platform, rpc), store_dir=self.store, admin_env=self.admin_env, sandbox_env=self.sandbox_env, started_at=STARTED)
        if real_time:
            inject.pop("sleep")
            inject.pop("clock")
        if oauth is not None:
            inject["oauth"] = oauth
        inject.update(overrides)
        code = h.rehearse_main(["--chain", "arbitrum"] + list(argv), **inject)
        return code, said

    def assertSaid(self, said, *fragments):
        text = "\n".join(said)
        for fragment in fragments:
            self.assertIn(fragment, text, "the output does not say %r:\n%s" % (fragment, text))
        return text

    def assertFailed(self, code, said, *fragments):
        text = self.assertSaid(said, "rehearsal %s FAILED: " % RUN_ID, *fragments)
        self.assertEqual(code, h.REHEARSAL_FAILED, text)
        return text


class TheWholeWalkTest(RehearsalBase):
    """A fresh wallet at US$0.00: the refusal proved, the credit, the send, the poll, the receipt, the debit judged (SPEC.md tests, first bullet)."""

    def test_the_walk_passes_from_a_fresh_wallet(self):
        platform, session, rpc = self.doubles()
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(
            said,
            "the gas account before, through the Wallet: balance US$0.00, reserved US$0.00, available US$0.00",
            "Your gas account holds US$0.00. This payment needs at most US$0.33 of gas. Nothing was sent.",
            "the first figure, US$0.00, is the balance read; the second, US$0.33, is the reservation",
            "credited US$5.00 (line ",
            "rehearsal %s)" % RUN_ID,
            "the gas account after the credit, through the Wallet: balance US$5.00, reserved US$0.00, available US$5.00",
            "the balance rose by exactly US$5.00",
            "the Police allowed: receipt ", 'gas_account "US$5.00"',
            "the Wallet built ticket t-",
            "the Wallet's answer: userOpHash 0x",
            "the send is submitted",
            "the send landed: operation 0x",
            'the platform\'s debit: “gas and service, US$0.22: gas US$0.20, service US$0.02 (10%), paid in advance from your gas account” — reservation US$0.33, gas US$0.20, service US$0.02, total US$0.22, margin 1000 bps, at US$2000.00 per ether',
            "the chain's receipt: gasUsed 100000 × effectiveGasPrice 1000000000 wei = 100000000000000 wei, at the recorded price US$2000.00 per ether = US$0.20",
            "the send judged: gas US$0.20 is within a cent of the receipt's US$0.20; service US$0.02 is within a cent of gas × 1000/10000 and at least a cent; total US$0.22 = gas + service; total ≤ reservation US$0.33",
            "the gas account fell by exactly US$0.22, the sum of the walk's totals: US$5.00 → US$4.78",
            "reserved is US$0.00: every reservation released",
            "USDC unchanged to the cent: 1000000 minor units before and after",
            "rehearsal %s PASSED: 1 operation(s) landed on arbitrum" % RUN_ID,
        )
        self.assertEqual(code, h.REHEARSAL_PASSED, text)
        # The refusal walk asked the Police and the Wallet once each and submitted nothing; the send asked each once more.
        self.assertEqual(len(session.calls_to("police.check_action")), 2)
        self.assertEqual(len(session.calls_to("wallet.build_transaction")), 2)
        self.assertEqual(len(session.calls_to("wallet.submit_transaction")), 1)
        # The send, in the doors' own vocabulary: one cent to the wallet's own pinned address, the receipt passed on.
        check = session.calls_to("police.check_action")[-1]
        self.assertEqual(check["action_kind"], "transfer_stable")
        self.assertEqual(check["amount_usd_cents"], 1)
        self.assertEqual(check["to_address"], D.WALLET)
        self.assertEqual(check["chain"], "arbitrum")
        self.assertEqual(check["asset_symbol"], "USDC")
        self.assertEqual(check["child_wallet_id"], D.WALLET_ID)
        self.assertNotIn("amount_usd", check)
        build = session.calls_to("wallet.build_transaction")[-1]
        self.assertEqual(build["action"], "transfer_stable")
        self.assertEqual(build["amount_usd"], 0.01)
        self.assertEqual(build["to_address"], D.WALLET)
        self.assertIn("police_receipt", build)
        self.assertIn(build["police_receipt"], session.receipts)
        submit = session.calls_to("wallet.submit_transaction")[0]
        self.assertEqual(set(submit), {"wallet_id", "ticket_id"})
        # The credit: the admin road, the run id in the key and the reason, the admin bearer.
        credits = [r for r in platform.requests if r["path"] == T.ADMIN_CREDIT_ROUTE % D.ACCOUNT_ID]
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0]["method"], "POST")
        self.assertEqual(credits[0]["headers"]["authorization"], "Bearer " + platform.admin_key)
        self.assertEqual(json.loads(credits[0]["body"]), {"amount_usd_cents": 500, "reason": "rehearsal " + RUN_ID, "idempotency_key": "rehearsal-" + RUN_ID})
        # The polls and the account read were made under the account's own credential, never the admin's.
        reads = [r for r in platform.requests if r["path"].startswith("/v1/gas/operations/") or r["path"] == T.GAS_ACCOUNT_ROUTE]
        self.assertTrue(reads)
        for read in reads:
            self.assertEqual(read["headers"]["authorization"], "Bearer " + platform.account_key)
        # The receipt was read from the pinned public RPC, and the ledger settled as the words say.
        self.assertEqual([r["method"] for r in rpc.requests], ["eth_getTransactionReceipt"])
        self.assertEqual(platform.balance(D.ACCOUNT_ID), {"balance_usd_cents": 478, "reserved_usd_cents": 0, "available_usd_cents": 478})

    def test_service_at_three_cents_on_gas_of_twenty_passes(self):
        platform, session, rpc = self.doubles(platform_kw={"service_off_cents": 1})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, "service US$0.03 is within a cent of gas × 1000/10000", "total US$0.23 = gas + service", "US$5.00 → US$4.77")
        self.assertEqual(code, h.REHEARSAL_PASSED, text)

    def test_a_wallet_delegated_first_makes_two_operations_both_judged(self):
        """Spec 154 §5: the Wallet's answer says the wallet was delegated first; the delegation is polled and judged like the send."""
        platform, session, rpc = self.doubles(session_kw={"delegate_first": True})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(
            said,
            "the wallet was delegated first (Spec 154 §5): the delegation 0x",
            "the delegation landed: delegation 0x",
            "the delegation judged: gas US$0.10 is within a cent of the receipt's US$0.10; service US$0.01",
            "the send judged: gas US$0.20",
            "the gas account fell by exactly US$0.33, the sum of the walk's totals: US$5.00 → US$4.67",
            "rehearsal %s PASSED: 2 operation(s) landed" % RUN_ID,
        )
        self.assertEqual(code, h.REHEARSAL_PASSED, text)
        self.assertEqual(len(rpc.requests), 2, "one receipt per operation")


class EachFailureIsNamedTest(RehearsalBase):
    """SPEC.md tests, second bullet: each fails naming it."""

    def test_wrong_words(self):
        platform, session, rpc = self.doubles(platform_kw={"words": "gas, US$0.22, paid in advance from your gas account"})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the send: the words “gas, US$0.22, paid in advance from your gas account” do not begin “gas and service, US$” and end “paid in advance from your gas account”")

    def test_gas_two_cents_off_the_receipt(self):
        platform, session, rpc = self.doubles(platform_kw={"gas_off_cents": 2})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "gas_usd_cents US$0.22 is 2 cent(s) from the receipt's US$0.20")

    def test_service_two_cents_off(self):
        platform, session, rpc = self.doubles(platform_kw={"service_off_cents": 2})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "service_usd_cents US$0.04 is more than a cent from gas × 1000/10000 = 2.0000 cents")

    def test_total_is_not_gas_plus_service(self):
        platform, session, rpc = self.doubles(platform_kw={"total_off_cents": 1})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "total_usd_cents US$0.23 is not gas + service = US$0.22")

    def test_total_above_the_reservation(self):
        platform, session, rpc = self.doubles(platform_kw={"reservation_report_cents": 21})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "total_usd_cents US$0.22 is above the reservation US$0.21")

    def test_the_account_fell_by_another_figure(self):
        platform, session, rpc = self.doubles(platform_kw={"debit_gap_cents": 1})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the gas account fell by US$0.23, not by the walk's totals US$0.22 (US$5.00 before the walk, US$4.77 after)")

    def test_reserved_not_zero(self):
        platform, session, rpc = self.doubles(platform_kw={"hold_reservation": True})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the gas account still reserves US$0.33 after the walk; every reservation should have been released")

    def test_reverted(self):
        platform, session, rpc = self.doubles(platform_kw={"revert": True})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the send reverted — the platform says: the operation transaction 0x", "reverted on chain; the gas it burned, US$0.22, was debited all the same")

    def test_a_receipt_that_reverted_where_the_platform_says_landed(self):
        platform, session, rpc = self.doubles(platform_kw={"receipt_status_reverted": True})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the receipt says the transaction reverted (status 0x0) where the platform says landed")

    def test_deduped_true_on_the_credit(self):
        platform, session, rpc = self.doubles(platform_kw={"deduped_credit": True})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertFailed(code, said, "the platform deduped the credit rehearsal-%s (HTTP 200): a credit under this run id already stands and nothing was credited now; the platform answered: " % RUN_ID,
                                 '"deduped": true')
        self.assertNotIn("wallet.submit_transaction", text.split("deduped the credit", 1)[1], "nothing was sent after the deduped credit")
        self.assertEqual(len(session.calls_to("wallet.submit_transaction")), 0)

    def test_a_mismatched_live_address(self):
        platform, session, rpc = self.doubles(session_kw={"live_address": D.OTHER_WALLET})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertFailed(code, said, "the Wallet's live key record names %s and tables.py pins %s for the harness wallet; nothing was sent" % (D.OTHER_WALLET, D.WALLET),
                                 "the key signed from %s, not %s, the address this wallet was told" % (D.OTHER_WALLET, D.WALLET))
        self.assertEqual(len(session.calls_to("police.check_action")), 0)
        self.assertEqual([r for r in platform.requests if r["method"] == "POST"], [], "nothing was credited")

    def test_an_operation_still_submitted_at_the_start(self):
        platform, session, rpc = self.doubles(platform_kw={"open_operation": True, "initial_balance_cents": 500})
        code, said = self.rehearse(platform, session, rpc)
        open_hash = next(k for k, v in platform.operations.items() if v["status"] == "submitted")
        self.assertFailed(code, said, "an operation of this account is still submitted: %s (this wallet); two rehearsals never cross" % open_hash)
        self.assertEqual(len(session.calls_to("police.check_action")), 0)

    def test_an_open_operation_of_another_wallet_of_the_owner_is_named_too(self):
        platform, session, rpc = self.doubles(platform_kw={"open_operation": True, "open_sender": D.OTHER_WALLET, "initial_balance_cents": 500})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "(another wallet of the owner, %s); two rehearsals never cross" % D.OTHER_WALLET)

    def test_a_chain_not_in_tables(self):
        platform, session, rpc = self.doubles()
        said = []
        code = h.rehearse_main(["--chain", "base"], say=said.append, session_factory=lambda label: session, http=D.router(platform, rpc),
                               store_dir=self.store, admin_env=self.admin_env, sandbox_env=self.sandbox_env, started_at=STARTED)
        self.assertFailed(code, said, "tables.py names no public RPC for 'base'; the rehearsal runs on arbitrum and nowhere else")
        self.assertEqual(session.calls, [], "nothing was asked")

    def test_the_police_refusing_the_send_fails_in_its_own_words(self):
        platform, session, rpc = self.doubles(session_kw={"police": "deny"})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the Police did not allow the send, where it refuses nothing for gas — MCP Police: “The destination %s is not on this agent’s list”" % D.WALLET)
        self.assertEqual(len(session.calls_to("wallet.build_transaction")), 0)

    def test_a_ticket_minted_at_zero_fails_and_is_never_submitted(self):
        platform, session, rpc = self.doubles(session_kw={"mint_at_zero": True})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the Wallet minted ticket t-", "for the send where U3's refusal was expected at US$0.00; the harness submitted nothing")
        self.assertEqual(len(session.calls_to("wallet.submit_transaction")), 0)

    def test_a_refusal_naming_another_first_figure_fails(self):
        platform, session, rpc = self.doubles(session_kw={"desk_says_holds": "US$0.10"})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "U3's sentence says the account holds US$0.10 where the gas account read US$0.00")

    def test_a_credential_the_operations_read_refuses_is_said_in_the_platforms_words(self):
        """SPEC.md §3: the operations read answers the account's credential; a refusal is the platform's judgment, told as one."""
        platform, session, rpc = self.doubles(platform_kw={"refuse_account_credential": True, "initial_balance_cents": 200})
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "refused: the platform refused the credential at GET /v1/gas/operations/0x", "(HTTP 401): invalid credential format — the answer will be the same until the credential in %s is replaced" % self.sandbox_env)

    def test_a_platform_that_answers_154_without_154c_fails_naming_the_missing_figures(self):
        platform, session, rpc = self.doubles(platform_kw={"words": "gas, US$0.22, paid in advance from your gas account"})
        original_view = platform.view

        def view_without_154c(row):
            out = original_view(row)
            for name in ("gas_usd_cents", "service_usd_cents", "total_usd_cents", "margin_bps", "native_usd_cents_per_ether"):
                out.pop(name, None)
            return out
        platform.view = view_without_154c
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the send: the platform's operation carries no gas_usd_cents, service_usd_cents, total_usd_cents, margin_bps, native_usd_cents_per_ether (Spec 154c §4)")

    def test_a_mismatched_account_id(self):
        platform, session, rpc = self.doubles()
        T.SANDBOX["account_id"] = "acct-somebody-else"
        code, said = self.rehearse(platform, session, rpc)
        self.assertFailed(code, said, "the credential in %s belongs to account %s and tables.py pins acct-somebody-else" % (self.sandbox_env, D.ACCOUNT_ID))
        self.assertEqual([r for r in platform.requests if r["method"] == "POST"], [])


class TheDeadlineAndTheResumeTest(RehearsalBase):
    def test_the_deadline_prints_the_hash_and_the_resume_sentence(self):
        platform, session, rpc = self.doubles(platform_kw={"never_lands": True})
        code, said = self.rehearse(platform, session, rpc, argv=["--interval", "0.01", "--deadline", "0.1"], real_time=True)
        user_op_hash = session.calls_to("wallet.submit_transaction") and next(iter(platform.operations))
        text = self.assertSaid(said, "the send is submitted; asking again in 0.01 s", user_op_hash,
                               "had not landed at the deadline of 0.1 s: not judged; rerun with --resume %s" % user_op_hash)
        self.assertEqual(code, h.REHEARSAL_NOT_JUDGED, text)
        self.assertNotIn("FAILED", text)
        self.assertNotIn("PASSED", text)
        self.assertIn(user_op_hash, [line for line in said if line == user_op_hash], "the hash is printed on a line of its own")

    def test_resume_polls_and_judges_without_sending(self):
        platform, session, rpc = self.doubles(platform_kw={"initial_balance_cents": 500})
        row = platform.quote(D.WALLET, "transfer")
        platform.submit(row["user_op_hash"])
        code, said = self.rehearse(platform, session, rpc, argv=["--resume", row["user_op_hash"]])
        text = self.assertSaid(said, "--resume %s: polling and judging without sending" % row["user_op_hash"], "the send landed",
                               "the send judged: gas US$0.20", "the fall of the balance is not judged: this run made no reading after the credit (--resume)",
                               "reserved is US$0.00", "rehearsal %s PASSED" % RUN_ID)
        self.assertEqual(code, h.REHEARSAL_PASSED, text)
        for tool in ("police.check_action", "wallet.build_transaction", "wallet.submit_transaction", "wallet.get_balances"):
            self.assertEqual(session.calls_to(tool), [], "%s was not asked under --resume" % tool)
        self.assertEqual([r for r in platform.requests if r["method"] == "POST"], [], "nothing was credited under --resume")

    def test_resume_refuses_an_operation_of_another_wallet(self):
        platform, session, rpc = self.doubles(platform_kw={"initial_balance_cents": 500})
        row = platform.quote(D.OTHER_WALLET, "transfer")
        platform.submit(row["user_op_hash"])
        code, said = self.rehearse(platform, session, rpc, argv=["--resume", row["user_op_hash"]])
        self.assertFailed(code, said, "was sent by %s, not by the harness wallet %s; it is not this rehearsal's to judge" % (D.OTHER_WALLET, D.WALLET))

    def test_resume_takes_a_hash_and_nothing_else(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            h.rehearse_main(["--chain", "arbitrum", "--resume", "not-a-hash"], say=lambda s: None)
        self.assertIn("--resume takes a userOpHash: 0x and sixty-four hexadecimal characters", err.getvalue())


class TheBalanceDecidesTheRefusalAndTheCreditTest(RehearsalBase):
    def test_fifty_cents_skips_the_refusal_with_its_sentence_and_credits(self):
        platform, session, rpc = self.doubles(platform_kw={"initial_balance_cents": 50})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, h.REFUSAL_SKIPPED_SENTENCE % "US$0.50", "credited US$5.00", "the gas account after the credit, through the Wallet: balance US$5.50",
                               "US$5.50 → US$5.28", "rehearsal %s PASSED" % RUN_ID)
        self.assertEqual(code, h.REHEARSAL_PASSED, text)
        self.assertEqual(len(session.calls_to("wallet.build_transaction")), 1, "no refusal walk: the build is asked for the send alone")
        self.assertEqual(len([r for r in platform.requests if r["method"] == "POST"]), 1)

    def test_two_dollars_skips_the_refusal_and_the_credit(self):
        platform, session, rpc = self.doubles(platform_kw={"initial_balance_cents": 200})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, h.REFUSAL_SKIPPED_SENTENCE % "US$2.00", "no credit: the gas account holds US$2.00, not below US$1.00", "US$2.00 → US$1.78",
                               "rehearsal %s PASSED" % RUN_ID)
        self.assertEqual(code, h.REHEARSAL_PASSED, text)
        self.assertEqual(len(session.calls_to("wallet.build_transaction")), 1)
        self.assertEqual([r for r in platform.requests if r["method"] == "POST"], [], "the admin road was not asked")


class TheBirthAndTheStopsTest(RehearsalBase):
    """SPEC.md §1: where the wallet does not exist it is born to the harness by the consent, and the run stops with the fund sentence."""

    def test_no_stored_consent_runs_the_consent_and_stops_with_the_fund_sentence(self):
        platform, session, rpc = self.doubles()
        oauth = D.FakeOauth(stored=None)
        code, said = self.rehearse(platform, session, rpc, oauth=oauth)
        text = self.assertSaid(said, "No consent is stored for harness-payer", "the consent runs now",
                               "rehearsal %s stopped before the walk: %s" % (RUN_ID, h.FUND_SENTENCE % (D.WALLET, "arbitrum")))
        self.assertEqual(code, h.REHEARSAL_STOPPED, text)
        self.assertEqual(oauth.consents, ["harness-payer"])
        self.assertEqual(session.calls_to("police.check_action"), [])
        self.assertNotIn(oauth.access_token, text)
        self.assertNotIn(oauth.refresh_token, text)

    def test_a_wallet_below_one_cent_of_usdc_stops_with_the_fund_sentence(self):
        platform, session, rpc = self.doubles(session_kw={"usdc_minor": 9999})
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, "USDC on arbitrum before, where the Wallet puts it (tokens.balances): 0.009999 USDC (9999 minor units",
                               "stopped before the walk: %s" % (h.FUND_SENTENCE % (D.WALLET, "arbitrum")))
        self.assertEqual(code, h.REHEARSAL_STOPPED, text)
        self.assertEqual(session.calls_to("police.check_action"), [])

    def test_an_unpinned_wallet_address_stops_naming_what_to_pin(self):
        platform, session, rpc = self.doubles()
        T.SANDBOX["wallet_address"] = ""
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, "tables.py pins no address for the harness wallet (SANDBOX['wallet_address']); the Wallet's key record names %s (key %s): pin it, then rerun" % (D.WALLET, D.KEY_ID))
        self.assertEqual(code, h.REHEARSAL_STOPPED, text)

    def test_an_unpinned_account_id_stops_naming_the_platforms_own_id(self):
        platform, session, rpc = self.doubles()
        T.SANDBOX["account_id"] = ""
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, "tables.py pins no account id for the harness's sandbox account (SANDBOX['account_id']); the platform names %s for the credential in %s: pin it, then rerun" % (D.ACCOUNT_ID, self.sandbox_env))
        self.assertEqual(code, h.REHEARSAL_STOPPED, text)

    def test_a_missing_credential_file_stops_naming_the_file(self):
        platform, session, rpc = self.doubles()
        os.remove(self.sandbox_env)
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, "%s is not filed: the rehearsal reads the sandbox account's platform credential (%s) from it; file it, then rerun" % (self.sandbox_env, T.SANDBOX_ENV_KEY_KEY))
        self.assertEqual(code, h.REHEARSAL_STOPPED, text)
        self.assertEqual(session.calls, [])

    def test_an_admin_key_of_the_wrong_shape_is_not_presented(self):
        platform, session, rpc = self.doubles()
        self.file_credentials(platform, admin_key="not-an-admin-key-sentinel")
        code, said = self.rehearse(platform, session, rpc)
        text = self.assertSaid(said, "does not begin %s, the platform's own prefix for an admin key" % h.ADMIN_KEY_PREFIX)
        self.assertEqual(code, h.REHEARSAL_STOPPED, text)
        self.assertEqual(platform.requests, [])


class NothingSecretIsPrintedTest(RehearsalBase):
    """SPEC.md §5 and the tests' fifth bullet: no sentinel secret and no Authorization value appears; the guarded files hold no platform prefix."""

    def secrets_of(self, platform, session):
        return [platform.admin_key, platform.account_key, session.bearer, self.access_token, self.refresh_token] + list(session.receipts)

    def test_no_sentinel_secret_and_no_authorization_value_appears_in_the_output(self):
        for platform_kw, session_kw in (({}, {}), ({"deduped_credit": True}, {}), ({}, {"live_address": D.OTHER_WALLET}), ({"never_lands": True}, {})):
            platform, session, rpc = self.doubles(platform_kw=platform_kw, session_kw=session_kw)
            argv = ["--interval", "0.01", "--deadline", "0.05"] if platform_kw.get("never_lands") else []
            code, said = self.rehearse(platform, session, rpc, argv=argv, real_time=bool(argv))
            text = "\n".join(said)
            for secret in self.secrets_of(platform, session):
                self.assertNotIn(secret, text, "a secret reached the output")
            self.assertNotIn("Bearer " + platform.admin_key, text)
            self.assertNotIn("Bearer " + platform.account_key, text)
            for line in said:
                if "Authorization" in line:
                    self.assertIn("Authorization: Bearer <redacted>", line, line)
            if platform.requests:
                self.assertIn("(Authorization: Bearer <redacted>)", text, "every platform call prints its header, redacted")
            if not session_kw and not platform_kw:
                self.assertIn('"police_receipt": "<redacted>"', text, "the receipt is redacted in the build's arguments")
                self.assertIn('"token": "<redacted>"', text, "the receipt is redacted in the Police's answer")
                self.assertEqual(code, h.REHEARSAL_PASSED)

    def test_the_tables_and_the_tests_hold_no_string_beginning_with_the_platforms_prefix(self):
        forbidden = "".join(("aek", "-"))
        carriers = []
        for folder, dirs, files in os.walk(os.path.join(ROOT, "tests")):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in files:
                path = os.path.join(folder, name)
                with open(path, "rb") as handle:
                    if forbidden.encode("utf-8") in handle.read():
                        carriers.append(os.path.relpath(path, ROOT))
        with open(os.path.join(ROOT, "tables.py"), "rb") as handle:
            if forbidden.encode("utf-8") in handle.read():
                carriers.append("tables.py")
        self.assertEqual(carriers, [])

    def test_the_repository_holds_no_credential_file_and_ignores_the_token_file(self):
        listed = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], check=True, capture_output=True).stdout
        tracked = [part.decode("utf-8") for part in listed.split(b"\0") if part]
        for name in tracked:
            self.assertNotIn(os.path.basename(name), (T.ADMIN_ENV_FILE, T.SANDBOX_ENV_FILE), "%s is tracked" % name)
        ignored = subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", "%s.json" % T.SANDBOX["label"]], capture_output=True).returncode == 0
        self.assertTrue(ignored, "the sandbox's token file could be committed")


class TheTablesTest(unittest.TestCase):
    def test_the_admin_credential_is_named_as_spec_t14_names_it(self):
        self.assertEqual(T.ADMIN_ENV_FILE, AT.ADMIN_ENV_FILE)
        self.assertEqual(T.ADMIN_ENV_URL_KEY, AT.ADMIN_ENV_URL_KEY)
        self.assertEqual(T.ADMIN_ENV_KEY_KEY, AT.ADMIN_ENV_KEY_KEY)
        self.assertEqual(T.ADMIN_CREDIT_ROUTE, AT.ADMIN_CREDIT_ROUTE)
        self.assertEqual(h.ADMIN_KEY_PREFIX, AT.ADMIN_KEY_PREFIX)
        self.assertEqual(T.ADMIN_ENV_DIR, "~/.aer360-harness")
        self.assertEqual(T.parse_env_file("A=1\nexport B='two'\n# c\nbad\n"), AT.parse_env_file("A=1\nexport B='two'\n# c\nbad\n"))
        self.assertEqual(T.format_usd_cents(478), AT.format_usd_cents(478))

    def test_the_rehearsal_rpc_is_the_skeletons_arbitrum_endpoint_and_the_sandbox_pins_no_address_yet(self):
        self.assertEqual(T.REHEARSAL_RPC["arbitrum"].url, h.default_run_file()["chains"]["arbitrum"]["rpc"])
        self.assertEqual(set(T.REHEARSAL_RPC), {"arbitrum"})
        self.assertEqual(T.SANDBOX["label"], "harness-payer")
        self.assertIn("payer", T.SANDBOX["label"], "the harness's agent is a Payer: a Trader cannot send")
        # Until Bear pins them from the first consent and the first run, both are empty, so the mode stops and says what to pin.
        self.assertEqual(T.SANDBOX["account_id"], "")
        self.assertEqual(T.SANDBOX["wallet_address"], "")
        self.assertEqual(T.REHEARSAL_SEND_USD, 0.01)
        self.assertEqual(T.REHEARSAL_CREDIT_USD_CENTS, 500)
        self.assertEqual(T.REHEARSAL_CREDIT_BELOW_USD_CENTS, 100)

    def test_the_money_helpers(self):
        self.assertEqual(h.usd_cents("US$4.78"), 478)
        self.assertEqual(h.usd_cents("0.33"), 33)
        self.assertEqual(h.usd_cents("-US$0.05"), -5)
        self.assertIsNone(h.usd_cents("four dollars"))
        self.assertEqual(h.cents_from_wei(10 ** 14, 200000), 20)
        self.assertEqual(h.cents_from_wei(25 * 10 ** 12, 200000), 5)
        self.assertEqual(h.cents_from_wei(2 * 10 ** 13, 200000), 4)   # 0.4 cents rounds down... to the nearest cent, halves up
        self.assertEqual(h.cents_from_wei(25 * 10 ** 11, 200000), 1)  # 0.5 cents rounds up
        reading = h.gas_account_in({"gas_account": {"read": True, "available": "US$4.78", "balance": "US$5.00", "reserved": "US$0.22", "low": False}})
        self.assertEqual((reading["available"], reading["balance"], reading["reserved"], reading["low"]), (478, 500, 22, False))
        self.assertEqual(h.gas_account_in({"verdict": "allow", "gas_account": "US$0.00"})["available"], 0)
        self.assertFalse(h.gas_account_in({"verdict": "allow"})["present"])
        self.assertTrue(h.U3_SENTENCE.search("Your gas account holds US$0.00. This transfer needs at most US$1.00 of gas. Nothing was sent. Ask your owner to buy gas on AER Connect."))


class TheCommandLineTest(unittest.TestCase):
    def test_rehearse_is_a_mode_of_its_own_and_refuses_an_unknown_chain_before_reading_any_file(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = h.main(["rehearse", "--chain", "nowhere"])
        self.assertEqual(code, h.REHEARSAL_FAILED)
        self.assertIn("tables.py names no public RPC for 'nowhere'; the rehearsal runs on arbitrum and nowhere else", out.getvalue())

    def test_the_series_command_line_is_unchanged(self):
        lines = h.dry_lines(["A"])
        self.assertTrue(lines)
        self.assertFalse(any("rehears" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
