"""
Spec T34 (28 November 2026): the Pathfinder reads a ticket made of two operations.

The agents' Wallet now sends every call as its own UserOperation (stablepro-agent-server Spec W-OPS): for the Pathfinder's ticket the
approval, where the quote carries one, and then the swap. The answers of wallet.submit_transaction and wallet.ticket_status keep every
field they had, describing the VALUE operation, and gain `operations`: every operation in the order sent. What the spec asks the tests to
prove, on the double (tests/pathfinder_double.py, which answers as the Wallet now does and can still answer the old single shape):

  two operations walked whole: S11, S12 and S12a pass, the gas account's fall is the sum, each receipt is read;
  an answer with no `operations`: the walk as it always was, in the sentences it always had (the guard);
  a tool call is waited for as long as the relay may wait (§7): a submit answered after 70 seconds is heard, the wait stated on tools/call
    alone, with a short wait stated in the test and a double just inside and just outside it — no test sleeps;
  a door that was asked and did not answer is not "no swap" (§8): the relay's sentence with the swap landing afterwards passes S11 with its
    finding, and S12 and S12a run; the relay's older sentence likewise; and the agent is not halted before S11's reading ends.

The failure paths — the approval's operation reverted, the approval landed with the swap refused, the unanswered submit with the approval
landed and no swap, the gas account fallen by one operation's debit where two were sent — are walked where every station's failure paths
are, each a fault of the product (tests/test_a_fail_means_a_fault.py). Section 5's finding, on a first run and on a later one, and section
6's row are held in tests/test_aerconnect_harness.py, beside what Spec T33 pinned there.

Standard library only, and no network: every road answers through corridor_harness.http_request, patched to the double.
"""
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerconnect_harness as P  # noqa: E402
import corridor_harness as H  # noqa: E402

try:
    from .pathfinder_double import ISSUER, RELAY_ASKED_UNANSWERED_SAID, RELAY_NOT_REACHED_SAID
    from .test_aerconnect_harness import PathfinderBase
except ImportError:  # run as a top-level module by `unittest discover tests`
    from pathfinder_double import ISSUER, RELAY_ASKED_UNANSWERED_SAID, RELAY_NOT_REACHED_SAID
    from test_aerconnect_harness import PathfinderBase

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A, AH, S, SH = "0x" + "a1" * 32, "0x" + "a2" * 32, "0x" + "b1" * 32, "0x" + "b2" * 32  # an approval's and a swap's hashes, nobody's


def approval(**fields):
    return dict({"kind": "approve", "user_op_hash": A, "handle_ops_tx_hash": AH, "reserved_usd": "0.06", "debited_usd": "0.01", "status": "landed", "success": True}, **fields)


def swap(**fields):
    return dict({"kind": "swap", "user_op_hash": S, "handle_ops_tx_hash": SH, "reserved_usd": "0.07", "debited_usd": "0.02", "status": "landed", "success": True}, **fields)


class TheReadersOfTheOperations(unittest.TestCase):
    """Spec T34 §1, the small readers: the operations an answer lists, the ticket's operations in the order sent, and how far each got."""

    def test_the_operations_are_found_wherever_an_answer_carries_the_list(self):
        rows = [approval(), swap()]
        self.assertEqual(P.operations_in({"ticket_id": "t", "execution": {"user_op_hash": S, "operations": rows}}), rows, "on the submit's outcome")
        self.assertEqual(P.operations_in({"ticket": {"id": "t", "operations": rows}}), rows, "on the ticket")
        self.assertEqual(P.operations_in({"ticket": {"id": "t"}, "operations": rows}), rows, "beside the ticket")
        for answer in (None, "", [], {}, {"execution": {"user_op_hash": S}}, {"operations": None}, {"operations": []}, {"operations": "two"}):
            self.assertEqual(P.operations_in(answer), [], answer)
        self.assertEqual(P.operations_in({"operations": [approval(), "swap", None]}), [approval()], "a row that is not a row is not read as one")

    def test_an_answer_with_no_list_is_the_one_operation_exactly_as_before(self):
        one = {"user_op_hash": S, "handle_ops_tx_hash": SH, "status": "landed", "success": True, "calls": ["approve", "swap"]}
        read = P.with_listed([dict(one)], [])
        self.assertEqual(read, [one], "a Wallet before W-OPS: nothing is added, and nothing is named")
        self.assertNotIn("kind", read[0])
        self.assertEqual(P.operation_said(read[0]), "the operation")

    def test_the_value_operation_is_last_and_carries_the_answers_own_fields(self):
        own = {"user_op_hash": S, "handle_ops_tx_hash": SH, "status": "landed", "success": True, "calls": ["approve", "swap"], "delegation_tx_hash": "0x" + "d1" * 32}
        read = P.with_listed([dict(own)], [approval(), swap()])
        self.assertEqual([op["kind"] for op in read], ["approve", "swap"])
        self.assertEqual(read[0], approval())
        self.assertEqual(read[1]["calls"], ["approve", "swap"], "what only the answer's own fields state is kept")
        self.assertEqual(read[1]["delegation_tx_hash"], own["delegation_tx_hash"])
        self.assertEqual((read[1]["debited_usd"], read[1]["reserved_usd"]), ("0.02", "0.07"), "what its own row states is read")
        self.assertEqual([P.operation_said(op) for op in read], ["the approval's operation", "the swap's operation"])
        alone = P.with_listed([dict(own)], [swap()])
        self.assertEqual([op["kind"] for op in alone], ["swap"], "a quote that carries no approval: the one operation, named")
        self.assertEqual(P.operation_said({"kind": "transfer"}), "the transfer's operation")

    def test_listed_operations_with_no_value_one_among_them_are_a_swap_not_sent(self):
        read = P.with_listed([{"calls": ["approve", "swap"], "success": False}], [approval()])
        self.assertEqual([op.get("kind") for op in read], ["approve", "swap"])
        self.assertFalse(P.operation_sent(read[1]))
        self.assertEqual(P.Pathfinder.fate_said(read[1]), "the swap's operation was not sent")
        self.assertEqual(P.Pathfinder.fate_said(read[0]), "the approval's operation %s landed in the handleOps transaction %s" % (A, AH))

    def test_a_newer_reading_is_laid_over_each_operation_in_its_place(self):
        known = P.with_listed([{"user_op_hash": S, "handle_ops_tx_hash": SH, "status": "submitted", "success": False, "calls": ["approve", "swap"]}],
                              [approval(), swap(status="submitted", success=False, debited_usd=None)])
        self.assertFalse(P.landed_word(known[1]))
        later = P.with_listed(known[:-1] + [P.newer_reading(known[-1], {"user_op_hash": S, "handle_ops_tx_hash": SH, "debited_usd": "0.02"}, P.TICKET_FIELDS)],
                              [approval(), swap()])
        self.assertEqual((later[1]["status"], later[1]["success"], later[1]["debited_usd"]), ("landed", True, "0.02"))
        self.assertEqual(later[1]["calls"], ["approve", "swap"], "what was known is kept")
        self.assertEqual(later[0], approval())
        shorter = P.with_listed(later, [swap()])
        self.assertEqual([op["kind"] for op in shorter], ["approve", "swap"], "an operation once read is never dropped by a shorter list")

    def test_how_far_an_operation_got_is_said_by_the_wallets_own_word_for_it(self):
        fate = P.Pathfinder.fate_said
        self.assertTrue(P.ended_badly(approval(status="reverted", success=False, reason="it reverted")))
        self.assertEqual(fate(approval(status="reverted", success=False, reason="it reverted")), "the approval's operation %s reverted — it reverted [unclassified]" % A)
        self.assertTrue(P.ended_badly(swap(success=False)), "a landing whose success is false did not go as asked")
        self.assertTrue(P.ended_badly({"kind": "swap", "status": "failed", "success": False, "reason": "refused"}))
        self.assertEqual(fate({"kind": "swap", "status": "failed", "success": False, "reason": "refused"}),
                         "the swap's operation was not sent (status failed) — refused [unclassified]")
        self.assertTrue(P.ended_badly({"kind": "swap", "reason": "refused"}), "a reason named for an operation never sent")
        waiting = swap(status="submitted", success=False, debited_usd=None)
        self.assertFalse(P.ended_badly(waiting), "sent and not yet landed: `success` is false until it lands")
        self.assertEqual(fate(waiting, 180), "the swap's operation %s had not landed at the deadline of 180 s (status submitted, handleOps %s)" % (S, SH))
        self.assertFalse(P.ended_badly({}), "nothing known of it yet")
        # the one operation of a Wallet before W-OPS, in the words S11 always had for it
        old = {"user_op_hash": S, "handle_ops_tx_hash": SH, "status": "submitted"}
        self.assertEqual(fate(old, 180), "the operation %s had not landed at the deadline of 180 s (status submitted, handleOps %s)" % (S, SH))
        self.assertEqual(fate(dict(old, status="reverted", reason="out of gas")), "the operation %s reverted — out of gas [unclassified]" % S)
        self.assertEqual(fate(dict(old, status="landed", debited_usd="0.02")), "the operation %s landed in the handleOps transaction %s" % (S, SH))

    def test_the_relays_two_sentences_for_a_door_that_did_not_answer_are_known_and_a_refusal_is_not_one(self):
        def answer(text):
            return H.McpAnswer(200, {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": text}], "isError": True}}, "", 1)

        for said in (RELAY_ASKED_UNANSWERED_SAID % 240, RELAY_NOT_REACHED_SAID):
            relayed = answer(said)
            self.assertTrue(P.door_did_not_answer(relayed, H.classify_wallet(relayed).get("who") or {}), said)
        self.assertIn("asked and did not answer within 240 seconds; it is not known whether anything was done", RELAY_ASKED_UNANSWERED_SAID % 240,
                      "aer-connector Spec C-WAIT-1's sentence, as Spec T34 quotes it")
        refused = answer("ticket_invalid: no unspent ticket by that id")
        self.assertFalse(P.door_did_not_answer(refused, H.classify_wallet(refused).get("who") or {}), "the Wallet's own refusal is the Wallet's answer")

    def test_the_waits_are_the_specs(self):
        self.assertEqual(P.TOOL_WAIT_SECONDS, 300.0)
        self.assertEqual(P.RELAY_DOOR_WAIT_SECONDS, 240)
        self.assertGreater(P.TOOL_WAIT_SECONDS, P.RELAY_DOOR_WAIT_SECONDS, "longer than the relay's, so the relay's answer is always heard")
        self.assertEqual(P.FATE_WAIT_SECONDS, 180.0)
        self.assertEqual(inspect.signature(H.http_request).parameters["timeout"].default, 60.0, "http_request's own default is as it was")
        with open(os.path.join(ROOT, "corridor_harness.py"), encoding="utf-8") as handle:
            corridor = handle.read()
        self.assertIn("http_answer = http_request(\"POST\", self.mcp_url, headers, body)", corridor, "the money Series' session states no wait, as before")
        self.assertNotIn("TOOL_WAIT", corridor)


class TwoOperationsAreWalkedWhole(PathfinderBase):
    """Spec T34 §1 to §4, through the double as the Wallet now answers: the approval's operation and the swap's."""

    def receipts_asked(self, runner, station):
        return [step["sent"]["params"][0] for step in runner.steps[station] if step["route"].startswith("eth_getTransactionReceipt")]

    def test_s11_s12_and_s12a_pass_the_fall_is_the_sum_and_each_receipt_is_read(self):
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual(runner.findings, {})
        operations = runner.facts["operations"]
        self.assertEqual([op["kind"] for op in operations], ["approve", "swap"], "in the order sent, the value operation last")
        self.assertEqual([(op["status"], op["success"]) for op in operations], [("landed", True), ("landed", True)])
        approve, value = operations
        self.assertIs(runner.facts["operation"], value)
        ticket = self.double.tickets[runner.facts["ticket_id"]]
        self.assertEqual((value["user_op_hash"], value["handle_ops_tx_hash"]), (ticket["user_op_hash"], ticket["handle_ops_tx_hash"]),
                         "the answer's own fields describe the swap")
        self.assertNotEqual(approve["handle_ops_tx_hash"], value["handle_ops_tx_hash"], "two sponsor's transactions")
        wallet = self.agent_of(runner)["walletAddress"]
        paymaster = H.checksum_address(P.PAYMASTER["arbitrum"])
        block = self.double.block
        # S11 names both, in order, and waited for the landing of each as it waits for the one
        self.assertIn("ticket %s submitted as 2 operations; the approval's operation %s landed in the handleOps transaction %s (block %d), reserved US$0.06, debited "
                      "US$0.01; the swap's operation %s landed in the handleOps transaction %s (block %d), reserved US$0.07, debited US$0.02; each from the wallet %s, "
                      "sponsored by the paymaster %s; the Wallet's calls approve, swap; " % (
                          runner.facts["ticket_id"], approve["user_op_hash"], approve["handle_ops_tx_hash"], block - 1, value["user_op_hash"],
                          value["handle_ops_tx_hash"], block, wallet, paymaster), self.line_of(runner, "S11"))
        self.assertEqual(self.receipts_asked(runner, "S11"), [approve["handle_ops_tx_hash"], value["handle_ops_tx_hash"]], "each receipt read, in the order sent")
        self.assertEqual(len(runner.facts["operations_read"]), 1)
        self.assertEqual(runner.facts["operations_read"][0][2]["user_op_hash"], approve["user_op_hash"], "the approval's own UserOperationEvent")
        self.assertEqual(runner.facts["event"]["user_op_hash"], value["user_op_hash"])
        # S12 says how many operations and names each, judges each debit within its own band, and holds the fall against the sum
        s12 = self.line_of(runner, "S12")
        self.assertIn("2 operations of the trade read, each by the receipt of its sponsor's transaction: the approval's operation %s in %s (block %d) and the swap's "
                      "operation %s in %s (block %d)" % (approve["user_op_hash"], approve["handle_ops_tx_hash"], block - 1, value["user_op_hash"],
                                                         value["handle_ops_tx_hash"], block), s12)
        self.assertIn("the approval's operation, the debit: US$0.01 for 1000000000000 wei of gas at US$2500.00 per ether (Chainlink at block %d), within US$0.01 to "
                      "US$0.01 for gas plus the 10%% charge" % block, s12)
        self.assertIn("the swap's operation, the debit: US$0.02 for 4000000000000 wei of gas at US$2500.00 per ether (Chainlink at block %d), within US$0.02 to "
                      "US$0.02 for gas plus the 10%% charge" % block, s12)
        self.assertIn("the gas account fell by US$0.04, US$10.00 to US$9.96, which is the sum of the debits of the 2 operations (the approval's operation US$0.01 and "
                      "the swap's operation US$0.02) and the delegation's", s12)
        self.assertIn("the balances reconcile: USDC 100000 → 0", s12)
        self.assertEqual(self.receipts_asked(runner, "S12"), [ticket["delegation_tx_hash"]], "the delegation's receipt; the operations' are S11's readings")
        # S12a reads the commission on the swap's operation, and says so
        s12a = self.line_of(runner, "S12a")
        self.assertTrue(s12a.startswith("commission 0.00000002 WETH to 0xabd0… (5 bps) — "), s12a)
        self.assertIn("read from the ERC-20 Transfer logs of %s" % value["handle_ops_tx_hash"], s12a)
        self.assertTrue(s12a.endswith("; read on the swap's operation, the trade's value operation: the approval's operation before it is not the swap, and no "
                                      "commission is looked for on it"), s12a)
        # run.json keeps what a resumed S12 needs: the swap's hashes where they always were, and the approval's beside them
        traded = H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))["traded"]
        self.assertEqual((traded["kind"], traded["user_op_hash"], traded["handle_ops_tx_hash"]), ("swap", value["user_op_hash"], value["handle_ops_tx_hash"]))
        self.assertEqual([(op["kind"], op["user_op_hash"], op["handle_ops_tx_hash"], op["debited_usd"]) for op in traded["operations_before"]],
                         [("approve", approve["user_op_hash"], approve["handle_ops_tx_hash"], "0.01")])

    def test_a_run_resumed_at_s12_reads_both_operations_again_by_the_hashes_run_json_keeps(self):
        first = self.runner()
        for station, title in P.STATIONS[:11]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        approve, value = first.facts["operations"]
        runner = self.walk(start_at="S12")
        for station in ("S12", "S12a", "S13"):
            self.assertEqual(runner.outcome_of(station).outcome, P.PASS, runner.line(runner.outcome_of(station)))
        asked = self.receipts_asked(runner, "S12")
        self.assertEqual(asked[:2], [value["handle_ops_tx_hash"], approve["handle_ops_tx_hash"]], "the swap's, as before, and then the approval's")
        self.assertIn("which is the sum of the debits of the 2 operations (the approval's operation US$0.01 and the swap's operation US$0.02) and the delegation's",
                      self.line_of(runner, "S12"))
        self.assertTrue(self.line_of(runner, "S12a").endswith("no commission is looked for on it"), self.line_of(runner, "S12a"))

    def test_a_quote_that_carries_no_approval_is_the_one_operation_named(self):
        self.double.needs_approval = False
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual([op["kind"] for op in runner.facts["operations"]], ["swap"])
        value = runner.facts["operation"]
        self.assertIn("submitted as 1 operation; the swap's operation %s landed in the handleOps transaction %s (block %d), reserved US$0.07, debited US$0.02; from the "
                      "wallet " % (value["user_op_hash"], value["handle_ops_tx_hash"], self.double.block), self.line_of(runner, "S11"))
        self.assertIn("1 operation of the trade read, each by the receipt of its sponsor's transaction: the swap's operation %s in %s" % (
            value["user_op_hash"], value["handle_ops_tx_hash"]), self.line_of(runner, "S12"))
        self.assertIn("the gas account fell by US$0.03, US$10.00 to US$9.97, which is the sum of the debits of the 1 operation (the swap's operation US$0.02) and the "
                      "delegation's", self.line_of(runner, "S12"))
        self.assertNotIn("value operation", self.line_of(runner, "S12a"), "no approval's operation came before it, so S12a's line is the one it always had")


class AnAnswerWithNoOperationsIsTodaysWalk(PathfinderBase):
    """Spec T34 §1, the guard: a Wallet before W-OPS lists no operations, and no expectation is held that the product has not promised."""
    options = dict(PathfinderBase.options, operations=False)

    def test_the_walk_is_unchanged_in_the_sentences_it_always_had(self):
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual(runner.findings, {})
        self.assertEqual(len(runner.facts["operations"]), 1)
        value = runner.facts["operation"]
        self.assertNotIn("kind", value)
        wallet = self.agent_of(runner)["walletAddress"]
        block = self.double.block
        s11 = self.line_of(runner, "S11")
        self.assertIn("ticket %s submitted; the operation %s landed in the handleOps transaction %s (block %d), from the wallet %s, sponsored by the paymaster %s; "
                      "the Wallet's calls approve, swap; reserved US$0.07, debited US$0.02; " % (
                          runner.facts["ticket_id"], value["user_op_hash"], value["handle_ops_tx_hash"], block, wallet, H.checksum_address(P.PAYMASTER["arbitrum"])), s11)
        self.assertNotIn("submitted as", s11)
        self.assertEqual([step["route"] for step in runner.steps["S11"] if step["route"].startswith("eth_getTransactionReceipt")],
                         ["eth_getTransactionReceipt https://arb1.arbitrum.io"], "the one receipt, read once")
        s12 = self.line_of(runner, "S12")
        self.assertIn("; the debit: US$0.02 for 4000000000000 wei of gas at US$2500.00 per ether (Chainlink at block %d), within US$0.02 to US$0.02 for gas plus the "
                      "10%% charge; the gas account fell by US$0.03, US$10.00 to US$9.97, which is the debit and the delegation's; the balances reconcile: USDC 100000 → 0"
                      % block, s12)
        self.assertNotIn("operation", s12)
        self.assertTrue(s12.startswith("the reader: on chain: "), s12)
        self.assertNotIn("value operation", self.line_of(runner, "S12a"))
        traded = H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))["traded"]
        self.assertEqual((traded["kind"], traded["operations_before"]), (None, []))

    def test_its_failures_are_said_as_they_always_were(self):
        self.double.lands_later = 10 ** 6
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        self.assertEqual((s11.outcome, s11.cause), (P.FAIL, P.FAULT), s11.line)
        ticket = self.double.tickets[runner.facts["ticket_id"]]
        self.assertEqual(s11.line, "the trade: the operation %s had not landed at the deadline of 180 s (status submitted, handleOps %s); the ticket is %s, and run.json "
                                   "keeps both hashes for --from S12" % (ticket["user_op_hash"], ticket["handle_ops_tx_hash"], ticket["id"]))
        self.assertIn("the Wallet answered the submit with an error after the operation was sent — confirmation_timeout: ", " ".join(runner.notes["S11"]))
        self.assertEqual(self.line_of(runner, "S12"), "the reader: %s" % P.NO_LANDING)

    def test_a_resumed_s12_reads_the_one_operation_run_json_keeps(self):
        first = self.runner()
        for station, title in P.STATIONS[:11]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        runner = self.walk(start_at="S12")
        for station in ("S12", "S12a", "S13"):
            self.assertEqual(runner.outcome_of(station).outcome, P.PASS, runner.line(runner.outcome_of(station)))
        self.assertIn("which is the debit and the delegation's", self.line_of(runner, "S12"))


class AToolCallIsWaitedForAsLongAsTheRelayMayWait(PathfinderBase):
    """
    Spec T34 §7. Run 20261128-022511 on production gave the submit up at 60 seconds, http_request's own default, while a first swap takes
    about 85. The double's Wallet takes `submit_seconds` to answer, and a caller whose stated wait is shorter hears the transport's
    timeout; nothing sleeps: the double holds the two figures against each other.
    """

    def test_a_submit_answered_after_seventy_seconds_is_heard(self):
        self.double.submit_seconds = 70
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual(runner.findings, {}, "the answer arrived: nothing is said of a wait")
        self.assertNotIn("never arrived", self.line_of(runner, "S11"))
        self.assertEqual([step["route"] for step in runner.steps["S11"] if step["route"] == "MCP tools/call wallet.ticket_status"], [],
                         "the Wallet's own answer said both operations landed, so no ticket was followed")

    def test_the_wait_is_stated_on_a_tools_call_alone_and_no_other_callers_wait_is_changed(self):
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        plain = ("initialize", "notifications/initialized", "tools/list")
        tools = [(name, wait) for name, wait in self.double.waits if name not in plain]
        others = [(name, wait) for name, wait in self.double.waits if name in plain]
        self.assertIn("wallet.submit_transaction", [name for name, _ in tools])
        self.assertIn("wallet.ticket_status", [name for name, _ in tools])
        self.assertEqual({wait for _, wait in tools}, {300.0}, "every call of a tool waits 300 seconds, longer than the relay's 240")
        self.assertEqual({name for name, _ in others}, set(plain))
        self.assertEqual({wait for _, wait in others}, {None}, "no other MCP method states a wait: http_request's own default, as before")
        self.assertEqual(inspect.signature(self._http).parameters["timeout"].default, 60.0)

    def test_the_default_of_sixty_seconds_would_not_have_heard_it(self):
        """The run of 28 November, on the double: a caller waiting http_request's 60 seconds for a submit answered at 70 hears only the timeout."""
        self.double.submit_seconds = 70
        runner = self.walk(tool_wait=60)
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.PASS, s11.line)
        self.assertEqual(len(runner.findings["S11"]), 1)
        self.assertIn("the answer to wallet.submit_transaction never arrived — the harness waited up to 60.0 s for it, and the transport says: POST %s/mcp: The read "
                      "operation timed out" % ISSUER, runner.findings["S11"][0])

    def test_a_short_wait_and_a_double_just_inside_it_is_heard_and_just_outside_it_is_not(self):
        self.double.submit_seconds = 0.19
        inside = self.walk(tool_wait=0.2)
        self.assertEqual(inside.outcome_of("S11").outcome, P.PASS, self.line_of(inside, "S11"))
        self.assertEqual(inside.findings, {}, "answered inside the wait: heard")
        self.assertEqual({wait for name, wait in self.double.waits if name == "wallet.submit_transaction"}, {0.2}, "the wait the caller stated is the wait the transport is given")
        self.double.submit_seconds = 0.21
        outside = self.walk(tool_wait=0.2)
        s11 = outside.outcome_of("S11")
        self.assertEqual(s11.outcome, P.PASS, s11.line)
        self.assertIn("the harness waited up to 0.2 s for it", outside.findings["S11"][0], "answered outside the wait: not heard, and S11 reads the ticket's fate instead")
        self.assertEqual(self.clock.slept.count(0.2), 0, "the wait is a maximum and never a delay: nothing slept it")


class ADoorThatWasAskedAndDidNotAnswerIsNotNoSwap(PathfinderBase):
    """
    Spec T34 §8. The relay waits 240 seconds for the Wallet's door and then answers in its place; the double's Wallet takes longer, and
    the swap goes on at the Wallet all the same. S11 concludes nothing from the relay's sentence alone: it reads the ticket and the chain.
    """

    def unanswered(self, **dials):
        self.double.submit_seconds = 300  # longer than the relay's 240: the relay answers in the door's place, and the harness, waiting 300, hears it
        for name, value in dials.items():
            setattr(self.double, name, value)

    def test_the_relays_sentence_with_the_swap_landing_afterwards_passes_s11_with_its_finding_and_s12_and_s12a_run(self):
        self.unanswered(swap_sent_after=2)  # the Wallet stands between the approval's operation and the swap's when the relay gives up
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        relayed = RELAY_ASKED_UNANSWERED_SAID % 240
        submit = next(step for step in runner.steps["S11"] if step["route"] == "MCP tools/call wallet.submit_transaction")
        self.assertIn(relayed, str(submit["came_back"]), "what the harness heard was the relay's sentence, not the Wallet's answer")
        approve, value = runner.facts["operations"]
        self.assertEqual(runner.findings, {"S11": [
            "the answer to wallet.submit_transaction never arrived — AER Connect's relay said: %s [unclassified]; the trade's fate was read where the product keeps it, "
            "wallet.ticket_status for the ticket %s and the chain, and the trade landed: the approval's operation %s landed in the handleOps transaction %s and the "
            "swap's operation %s landed in the handleOps transaction %s" % (relayed, runner.facts["ticket_id"], approve["user_op_hash"], approve["handle_ops_tx_hash"],
                                                                           value["user_op_hash"], value["handle_ops_tx_hash"])]})
        s11 = self.line_of(runner, "S11")
        self.assertIn("submitted as 2 operations — its answer never arrived, and the trade's fate was read from wallet.ticket_status and the chain (a finding); the "
                      "approval's operation %s landed in the handleOps transaction %s" % (approve["user_op_hash"], approve["handle_ops_tx_hash"]), s11)
        names = [name for name, _ in self.double.tool_calls]
        after = names[names.index("wallet.submit_transaction") + 1:]
        self.assertEqual(after[:2], ["wallet.ticket_status", "wallet.ticket_status"], "the ticket, read until the swap landed")
        self.assertEqual(self.double.tickets[runner.facts["ticket_id"]]["user_op_hash"], value["user_op_hash"])
        self.assertIn("which is the sum of the debits of the 2 operations (the approval's operation US$0.01 and the swap's operation US$0.02) and the delegation's",
                      self.line_of(runner, "S12"))
        self.assertTrue(self.line_of(runner, "S12a").startswith("commission 0.00000002 WETH to 0xabd0… (5 bps) — "), self.line_of(runner, "S12a"))
        self.assertEqual(P.exit_code_of(runner.outcomes), 0, "a finding is not a fail")

    def test_the_relays_older_sentence_is_read_the_same_way(self):
        self.unanswered(relay_said=RELAY_NOT_REACHED_SAID)
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual(len(runner.findings["S11"]), 1)
        self.assertIn("never arrived — AER Connect's relay said: The MCP Wallet door could not be reached, so nothing was done. [unclassified]; the trade's fate was read",
                      runner.findings["S11"][0])
        self.assertNotIn("refused the submit", self.line_of(runner, "S11"))

    def test_a_swap_the_ticket_names_and_never_says_landed_is_read_on_the_chain(self):
        """The fate is read where the product keeps it: the ticket, and the chain as S12 reads it — the receipt and the operation's own UserOperationEvent."""
        self.unanswered(lands_later=10 ** 6)  # the ticket names the swap's handleOps transaction and never states its landing or its debit
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        self.assertEqual(s11.outcome, P.PASS, s11.line)
        approve, value = runner.facts["operations"]
        self.assertEqual((value["status"], value["success"]), ("landed", True), "read from the chain's UserOperationEvent for the swap's own hash")
        self.assertEqual(len(runner.findings["S11"]), 1)
        self.assertEqual([name for name, _ in self.double.tool_calls].count("wallet.ticket_status"), 2, "one reading in S11 was enough; S12 reads the ticket once more")
        # the Wallet's ticket never stated the swap's debit, and S12 says so: a fault of the product's, in S12's own words
        s12 = runner.outcome_of("S12")
        self.assertEqual((s12.outcome, s12.cause), (P.FAIL, P.FAULT), s12.line)
        self.assertIn("the Wallet states no debited_usd for the swap's operation", s12.line)
        self.assertEqual(runner.outcome_of("S12a").outcome, P.PASS, self.line_of(runner, "S12a"))

    def test_a_read_of_the_ticket_that_does_not_arrive_either_does_not_end_the_reading(self):
        """A reading cut short would hand the agent to the teardown with the swap still on its way: the read is noted, and the reading goes on."""
        self.unanswered(swap_sent_after=2)
        status = self.double.tool_wallet_ticket_status
        lost = []

        def losing(rpc_id, agent, connection, args):
            if not lost:
                lost.append(args.get("ticket_id"))
                raise H.Unreachable("POST %s/mcp: The read operation timed out" % ISSUER)
            return status(rpc_id, agent, connection, args)

        self.double.tool_wallet_ticket_status = losing
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        self.assertEqual(lost, [runner.facts["ticket_id"]])
        self.assertIn("wallet.ticket_status did not answer (POST %s/mcp: The read operation timed out); the reading of the trade's fate goes on to its end" % ISSUER,
                      runner.notes["S11"])
        self.assertEqual(runner.outcome_of("S12").outcome, P.PASS, self.line_of(runner, "S12"))

    def test_the_agent_is_not_halted_before_s11s_reading_ends(self):
        self.unanswered(swap_never_sent=True)  # the approval's operation landed and no swap follows: S11 reads for the whole 180 seconds
        seen = {}
        submit = self.double.tool_wallet_submit_transaction
        account = self.double.account

        def submitting(rpc_id, agent, connection, args):
            seen["submitted_at"] = self.clock.t
            return submit(rpc_id, agent, connection, args)

        def watching(method, path, headers, payload):
            if path.endswith("/halt"):
                seen.setdefault("halted_at", self.clock.t)
                seen.setdefault("reads_at_the_halt", [name for name, _ in self.double.tool_calls].count("wallet.ticket_status"))
            return account(method, path, headers, payload)

        self.double.tool_wallet_submit_transaction = submitting
        self.double.account = watching
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.FAIL, self.line_of(runner, "S11"))
        self.assertEqual(self.double.halted, [runner.facts["agent_id"]], "the teardown still runs")
        reads = [name for name, _ in self.double.tool_calls].count("wallet.ticket_status")
        self.assertEqual(reads, int(P.FATE_WAIT_SECONDS / P.TRADE_POLL_SECONDS), "the ticket read every interval for the whole 180 seconds")
        self.assertEqual(seen["reads_at_the_halt"], reads, "every reading of the ticket's fate was made before the agent was halted")
        self.assertGreaterEqual(seen["halted_at"] - seen["submitted_at"], P.FATE_WAIT_SECONDS, "and the halt came no sooner than the reading's end")


if __name__ == "__main__":
    unittest.main()
