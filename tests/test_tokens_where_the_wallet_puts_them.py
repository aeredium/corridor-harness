"""
A4 reads the tokens where the Wallet puts them, and prints the rails as the door names
them (Spec T3 §2, §3).

Alice's run of 14 September 15:41: the Wallet (Spec 49) answered get_balances with
`tokens: {balances: [{asset, chain, contract, decimals, raw, amount, available, source},
…], chains, road, said}`, stating 2 USDC, 0 USDT and 0 WETH on Arbitrum — the same
figures the harness read from the chain — and the harness, looking for a LIST under
`tokens`, found an object, and wrote "get_balances states the ERC-20 balances … it does
not (Spec 49)" while quoting the Wallet's own sentence that states them. Its door also
names aeredium-testnet (2237) among its rails.

The fixtures carry the Wallet's shape as its code writes it (stablepro-agent-server,
doorway_wallets.go), with the figures Alice's run reported and the wallet's own id and
address removed; the token contracts are the public ones the run file names too.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

try:
    from .fakes import FakeSession, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeSession, runner_for

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
NATIVE_WEI = 1000000000000000
ARBITRUM_TOKENS = h.default_run_file()["chains"]["arbitrum"]["tokens"]
USDC, USDT, WETH = ARBITRUM_TOKENS["USDC"], ARBITRUM_TOKENS["USDT"], ARBITRUM_TOKENS["WETH"]
PYUSD = "0x46850aD61C2B7d64d08c9C754F45254596696984"  # a token the run file does not name
CHAINS = {"arbitrum": {"rpc": "https://rpc.test/arbitrum", "tokens": dict(ARBITRUM_TOKENS), "explorer": ""}}
THREE_RAILS = [{"chain": "arbitrum", "chain_id": 42161, "live": True},
               {"chain": "base", "chain_id": 8453, "live": True},
               {"chain": "ethereum", "chain_id": 1, "live": True}]
ROAD = ("every verified stablecoin row this door holds for arbitrum, because the pact's compiled document names no "
        "assets this door could read")
NOTE_NOT_STATED = "it does not"

PAGES = {
    "/.well-known/oauth-authorization-server": (200, "{}"),
    "/healthz": (200, "ok"),
    "/mcp": (401, "unauthorized"),
    "/guide": (200, "The Owner's Guide."),
    "/account": (200, "Your agents."),
    "/terms": (200, "A trading fee applies."),
}


def recorded(name):
    """One recorded answer's body, exactly as the door sent it inside the JSON-RPC envelope."""
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as handle:
        envelope = json.load(handle)
    return json.loads(envelope["result"]["content"][0]["text"])


ALICE_BALANCES = recorded("get-balances-alice.json")
ALICE_STATUS = recorded("wallet-status-alice-rails.json")


def row(asset, contract, raw, decimals):
    """One token row as Spec 49's Wallet writes it (doorway_wallets.go, tokenRow)."""
    digits = str(raw).rjust(decimals + 1, "0")
    return {"chain": "arbitrum", "asset": asset, "contract": contract, "available": True, "raw": str(raw),
            "source": "eth_call balanceOf on arbitrum via arb1.arbitrum.io", "decimals": decimals,
            "amount": digits[:-decimals] + "." + digits[-decimals:]}


def tokens_block(rows, road=ROAD):
    return {"road": road, "chains": ["arbitrum"], "balances": rows, "said": "this wallet holds what the rows say"}


class AliceDoor(FakeSession):
    """The fake corridor answering wallet_status and get_balances with Alice's recorded shapes."""

    def __init__(self, status=None, balances=None, **kwargs):
        FakeSession.__init__(self, **kwargs)
        self.recorded_status = status
        self.recorded_balances = balances

    def status_answer(self):
        return self.recorded_status if self.recorded_status is not None else FakeSession.status_answer(self)

    def balances_answer(self):
        return self.recorded_balances if self.recorded_balances is not None else FakeSession.balances_answer(self)


class ChainBase(unittest.TestCase):
    """A chain double that answers balanceOf per contract, so the Wallet's rows are compared one by one."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.balances = {USDC.lower(): 2_000_000, USDT.lower(): 0, WETH.lower(): 0, PYUSD.lower(): 7_000_000}
        self.decimals = {USDC.lower(): 6, USDT.lower(): 6, WETH.lower(): 18, PYUSD.lower(): 6}
        self.eth_calls = []
        self._http = h.http_request
        h.http_request = self.canned_http

    def tearDown(self):
        h.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def chain_answer(self, body):
        payload = json.loads(body.decode("utf-8"))
        method, params = payload["method"], payload["params"]
        if method == "eth_getBalance":
            return hex(NATIVE_WEI)
        if method == "eth_call":
            to, data = params[0]["to"].lower(), params[0]["data"]
            self.eth_calls.append(to)
            if data.startswith(h.selector("decimals()")):
                return hex(self.decimals[to])
            if data.startswith(h.selector("balanceOf(address)")):
                return hex(self.balances[to])
        if method == "eth_blockNumber":
            return hex(100)
        raise AssertionError("the test reached for %s" % method)

    def canned_http(self, method, url, headers=None, body=None, timeout=None):
        if url.startswith("https://rpc.test/"):
            return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": self.chain_answer(body)}), 1)
        for path, (status, text) in PAGES.items():
            if url.endswith(path):
                return h.HttpAnswer(status, {}, text, 1)
        raise AssertionError("the test reached for %s" % url)

    def a4(self, session, chains=None):
        runner = runner_for(session, self.tmp, chains=CHAINS if chains is None else chains)
        return runner, runner.run_test(S.BY_ID["A4"])


class TokensWhereTheWalletPutsThemTest(ChainBase):
    def test_alices_get_balances_is_a_plain_pass_with_the_three_tokens_compared(self):
        """Spec 49's shape, the three figures agreeing with the chain: no note, and the road in the line."""
        session = AliceDoor(balances=ALICE_BALANCES, role_id="trader.v1", rails=THREE_RAILS)
        runner, a4 = self.a4(session)
        self.assertEqual(a4.outcome, h.PASS, a4.sentence)
        self.assertIsNone(a4.note)
        self.assertNotIn(NOTE_NOT_STATED, a4.sentence)
        for words in ("2 USDC (the chain agrees)", "0 USDT (the chain agrees)", "0 WETH (the chain agrees)"):
            self.assertIn(words, a4.line)
        self.assertIn("the Wallet states the token balances on arbitrum", a4.line)
        self.assertIn(ROAD, a4.line, "the road is printed after the balances")
        self.assertLess(a4.line.index("0 WETH"), a4.line.index(ROAD))
        self.assertIn(ROAD, a4.sentence)
        self.assertNotIn("read from arbitrum's own RPC", a4.line, "the tokens were not read from the chain alone")
        self.assertTrue(runner.a4_native_balance, "the native comparison was made, and it gates money")
        # every contract compared is one the run file names, read once each
        self.assertEqual(sorted(set(self.eth_calls)), sorted({USDC.lower(), USDT.lower(), WETH.lower()}))

    def test_alices_whole_a4_as_the_harness_now_reads_it(self):
        """Both of Alice's recorded answers: the tokens agree, the rails name a chain outside the three, and the only note is that."""
        session = AliceDoor(status=ALICE_STATUS, balances=ALICE_BALANCES, role_id="trader.v1")
        runner, a4 = self.a4(session)
        self.assertEqual(a4.outcome, h.PASS_NOTE, a4.sentence)
        self.assertNotIn(NOTE_NOT_STATED, json.dumps(a4.note))
        self.assertIn("aeredium-testnet (2237)", a4.note["got"])
        self.assertIn("aeredium-testnet (2237)", a4.line)
        self.assertIn("outside the three the product offers", a4.line)
        self.assertIn(ROAD, a4.line)
        self.assertIn("2 USDC (the chain agrees)", a4.line)

    def test_a_get_balances_with_no_tokens_block_is_noted_as_today(self):
        """Before Spec 49 the Wallet stated no tokens; the note is written then, and only then."""
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS))
        self.assertEqual(a4.outcome, h.PASS_NOTE)
        self.assertIn(NOTE_NOT_STATED, a4.note["got"])
        self.assertIn("Spec 49", a4.note["got"])
        self.assertIn("ERC-20 balances are not read here", a4.note["got"], "the Wallet's own sentence is quoted")
        self.assertIn("read from arbitrum's own RPC", a4.line)
        self.assertIn("2 USDC", a4.line)
        self.assertNotIn("road", a4.line)

    def test_a_bare_list_of_rows_is_read_too(self):
        rows = [row("USDC", USDC, 2_000_000, 6), row("USDT", USDT, 0, 6), row("WETH", WETH, 0, 18)]
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=rows))
        self.assertEqual(a4.outcome, h.PASS, a4.sentence)
        self.assertIn("2 USDC (the chain agrees)", a4.line)
        self.assertNotIn("road", a4.line, "a bare list carries no road sentence, and none is invented")

    def test_a_figure_that_differs_is_a_note_carrying_both_figures(self):
        self.balances[USDC.lower()] = 3_000_000
        session = FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block([row("USDC", USDC, 2_000_000, 6)]))
        runner, a4 = self.a4(session)
        self.assertEqual(a4.outcome, h.PASS_NOTE, a4.sentence)
        self.assertIn("USDC: the Wallet says 2 (2000000 raw), the chain says 3 (3000000 raw)", a4.line)
        self.assertIn("3 USDC (3000000 raw)", a4.note["expected"])
        self.assertIn("2 USDC (2000000 raw)", a4.note["got"])
        self.assertNotIn(NOTE_NOT_STATED, a4.note["got"])
        self.assertTrue(runner.a4_native_balance, "a token that differs is a note; the native check still passed")

    def test_a_token_the_run_file_does_not_name_is_printed_and_not_compared(self):
        """The harness reads no contract the run file did not name: the Wallet's figure is printed as stated."""
        rows = [row("USDC", USDC, 2_000_000, 6), row("PYUSD", PYUSD, 7_000_000, 6)]
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block(rows)))
        self.assertEqual(a4.outcome, h.PASS, a4.sentence)
        self.assertIn("7 PYUSD (not compared: the run file names no PYUSD on arbitrum)", a4.line)
        self.assertNotIn(PYUSD.lower(), self.eth_calls, "the unnamed contract was never asked anything")

    def test_a_token_the_run_file_names_at_another_contract_is_said_so(self):
        other = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"  # bridged USDC.e, not the run file's USDC
        rows = [row("USDC", other, 2_000_000, 6)]
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block(rows)))
        self.assertIn("not compared: the run file names USDC at %s on arbitrum, the Wallet at %s" % (USDC, other), a4.line)
        self.assertNotIn(other.lower(), self.eth_calls)

    def test_a_token_the_wallet_did_not_state_is_read_from_the_chain_alone(self):
        rows = [row("USDC", USDC, 2_000_000, 6)]
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block(rows)))
        self.assertEqual(a4.outcome, h.PASS, a4.sentence)
        self.assertIn("2 USDC (the chain agrees)", a4.line)
        self.assertIn("0 USDT read from the chain alone (the Wallet stated no balance for this contract)", a4.line)
        self.assertIn("0 WETH read from the chain alone (the Wallet stated no balance for this contract)", a4.line)
        self.assertIsNone(a4.note, "a token the Wallet did not state is said in the line, not noted")

    def test_a_row_the_wallet_could_not_read_is_said_in_its_words(self):
        rows = [row("USDC", USDC, 2_000_000, 6),
                {"chain": "arbitrum", "asset": "PYUSD", "available": False,
                 "reason": "PYUSD: no verified contract on arbitrum; not read"}]
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block(rows)))
        self.assertIn("PYUSD not read by the Wallet: PYUSD: no verified contract on arbitrum; not read", a4.line)
        self.assertEqual(a4.outcome, h.PASS, a4.sentence)

    def test_a_row_on_another_chain_names_the_chain(self):
        rows = [row("USDC", USDC, 2_000_000, 6), dict(row("USDC", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 8_000_000, 6), chain="base")]
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block(rows)))
        self.assertIn("8 USDC on base (not compared: the run file names no RPC for base)", a4.line)

    def test_the_road_reaches_the_report(self):
        session = AliceDoor(balances=ALICE_BALANCES, role_id="trader.v1", rails=THREE_RAILS)
        runner = runner_for(session, self.tmp, chains=CHAINS)
        runner.run(["A"])
        self.assertIn(ROAD, runner.report())
        self.assertTrue(runner.series_a_passed, runner.series_a_gate_said)

    def test_no_rpc_still_prints_what_the_wallet_states(self):
        session = AliceDoor(balances=ALICE_BALANCES, role_id="trader.v1", rails=THREE_RAILS)
        runner, a4 = self.a4(session, chains={})
        self.assertEqual(a4.outcome, h.PASS_NOTE)
        self.assertIsNone(runner.a4_native_balance, "no RPC, so the check could not be made")
        self.assertIn("no RPC for arbitrum", a4.line)
        self.assertIn("the Wallet states 2 USDC, 0 USDT, 0 WETH", a4.sentence)
        self.assertIn(ROAD, a4.line)

    def test_a_wallet_that_states_tokens_but_no_native_balance_still_fails_the_gating_check(self):
        session = FakeSession(role_id="trader.v1", rails=THREE_RAILS, native_wei=None,
                              tokens=tokens_block([row("USDC", USDC, 2_000_000, 6)]))
        runner, a4 = self.a4(session)
        self.assertEqual(a4.outcome, h.FAIL)
        self.assertIs(runner.a4_native_balance, False)
        self.assertIn("2 USDC (the chain agrees)", a4.line)
        self.assertIn(ROAD, a4.line)

    def test_wallet_tokens_reads_both_shapes_and_nothing_else(self):
        rows = [row("USDC", USDC, 1, 6)]
        self.assertEqual(h.wallet_tokens({"tokens": tokens_block(rows)}), (rows, ROAD, "this wallet holds what the rows say"))
        self.assertEqual(h.wallet_tokens({"tokens": rows}), (rows, None, None))
        self.assertEqual(h.wallet_tokens({"erc20": rows}), (rows, None, None))
        self.assertEqual(h.wallet_tokens({"tokens": {"road": ROAD}}), (None, None, None), "an object without a balances list is neither shape")
        self.assertEqual(h.wallet_tokens({"native": {"wei": 1}}), (None, None, None))
        self.assertEqual(h.wallet_tokens("not json"), (None, None, None))

    def test_the_dry_run_says_where_the_tokens_are_read(self):
        a4 = [l for l in h.dry_lines(["A"]) if l.startswith("A4 — ")]
        self.assertTrue(any("tokens.balances" in l and "tokens.road" in l for l in a4), a4)
        self.assertFalse(any("cannot state" in l for l in a4), "the dry run no longer says get_balances cannot state the tokens")


class TheRailsLineTest(ChainBase):
    def test_alices_wallet_status_names_a_rail_outside_the_three_as_a_note(self):
        session = AliceDoor(status=ALICE_STATUS, role_id="trader.v1")
        runner = runner_for(session, self.tmp, chains=CHAINS)
        outcomes = {o.test.id: o for o in runner.run(["A"])}
        a4 = outcomes["A4"]
        self.assertIn(a4.outcome, (h.PASS, h.PASS_NOTE), a4.sentence)
        self.assertEqual(a4.outcome, h.PASS_NOTE)
        self.assertIn("chain arbitrum; rails aeredium-testnet (2237), arbitrum (42161), base (8453), ethereum (1)", a4.line)
        self.assertIn("outside the three the product offers: aeredium-testnet (2237)", a4.line)
        self.assertIn("aeredium-testnet (2237)", a4.note["got"])
        self.assertIn("telling the truth about itself", a4.sentence)
        self.assertNotIn("which the product does not offer", a4.sentence, "the wallet is on arbitrum; the guard does not fire")
        self.assertTrue(runner.series_a_passed, "A4's notes gate nothing: " + runner.series_a_gate_said)
        self.assertIn("aeredium-testnet (2237)", runner.report())

    def test_rails_within_the_three_are_a_plain_pass_printed_with_their_ids(self):
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=THREE_RAILS, tokens=tokens_block(
            [row("USDC", USDC, 2_000_000, 6), row("USDT", USDT, 0, 6), row("WETH", WETH, 0, 18)])))
        self.assertEqual(a4.outcome, h.PASS, a4.sentence)
        self.assertIn("chain arbitrum; rails arbitrum (42161), base (8453), ethereum (1)", a4.line)
        self.assertNotIn("outside the three", a4.line)
        self.assertIn("its rails: arbitrum (42161), base (8453), ethereum (1)", a4.sentence)

    def test_rails_stated_as_bare_names_still_pass(self):
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", rails=["ethereum", "arbitrum", "base"]))
        self.assertIn("rails ethereum, arbitrum, base", a4.line)
        self.assertNotIn("outside the three", a4.line)

    def test_no_rails_stated_is_the_spec_49_note_as_before(self):
        runner, a4 = self.a4(FakeSession(role_id="trader.v1"))
        self.assertEqual(a4.outcome, h.PASS_NOTE)
        self.assertIn("rails not stated", a4.line)
        self.assertIn("Spec 49", json.dumps(a4.note))

    def test_a_wallet_off_the_three_chains_still_fails_whatever_its_rails(self):
        """The judgement is unchanged: the rails line notes; the chain guard judges."""
        runner, a4 = self.a4(FakeSession(role_id="trader.v1", chain="aeredium-testnet", rails=ALICE_STATUS["rails"]))
        self.assertEqual(a4.outcome, h.FAIL)
        self.assertIn("which the product does not offer", a4.sentence)

    def test_rail_names_reads_the_shapes_a_door_may_send(self):
        self.assertEqual(h.rail_names(ALICE_STATUS["rails"]),
                         [("aeredium-testnet", "2237"), ("arbitrum", "42161"), ("base", "8453"), ("ethereum", "1")])
        self.assertEqual(h.rail_names(["ethereum", "arbitrum"]), [("ethereum", None), ("arbitrum", None)])
        self.assertEqual(h.rail_names({"ethereum": 1, "base": {"chain_id": 8453}, "arbitrum": True}),
                         [("ethereum", "1"), ("base", "8453"), ("arbitrum", None)])
        self.assertEqual(h.rail_names([{"live": True}, 42, ""]), [], "a shape that names nothing yields nothing")
        self.assertEqual(h.rail_names(None), [])
        self.assertEqual(h.rail_word("arbitrum", "42161"), "arbitrum (42161)")
        self.assertEqual(h.rail_word("arbitrum", None), "arbitrum")

    def test_the_dry_run_names_the_rails_note(self):
        a4 = [l for l in h.dry_lines(["A"]) if l.startswith("A4 — ") and "wallet.wallet_status" in l]
        self.assertTrue(any("any rail outside the three named as a note" in l for l in a4), a4)


if __name__ == "__main__":
    unittest.main()
