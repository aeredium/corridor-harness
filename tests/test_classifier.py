"""The outcome classifier maps answers to the five kinds of Spec T1 §7, and reads who answered (§6)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402


def answer(payload, is_error=False, status=200, structured=None):
    result = {"content": [{"type": "text", "text": payload if isinstance(payload, str) else json.dumps(payload)}]}
    if is_error:
        result["isError"] = True
    if structured is not None:
        result["structuredContent"] = structured
    body = {"jsonrpc": "2.0", "id": 1, "result": result}
    return h.McpAnswer(status, body, json.dumps(body), 3)


POLICE_DENY = answer({"verdict": "deny", "reason": "denied",
                      "sentence": "The destination 0x000000000000000000000000000000000000dEaD is not on this agent’s list"})
POLICE_HOLD = answer({"verdict": "hold_for_manual_approval", "reason": "manual_approval_required",
                      "sentence": "owner approval required before ticket can be minted"})
POLICE_ALLOW = answer({"verdict": "allow", "policy_hash": "0xabc", "receipt": {"issued": True, "token": "police-receipt-1", "nonce": "n-1", "expires_at": "x"}})
POLICE_CONTEXT = answer({"verdict": "deny", "reason": "context_incomplete:oracle", "sentence": "the oracle fact cannot be established"})
WALLET_ERROR = answer("receipt_missing: This action carries no pre-flight receipt. Nobody enters but through the Police.", is_error=True)
WALLET_ENGINE = answer("agent_destination_not_whitelisted: the destination is not on the list this agent's pact consulted", is_error=True)
WALLET_TICKET = answer({"ticket_id": "t-1", "wallet_id": "w-1", "legs": [{"kind": "approve"}, {"kind": "swap"}], "policy_hash": "0xabc"})
WALLET_SUBMIT = answer({"ticket_id": "t-1", "legs": [{"tx_hash": "0x" + "11" * 32}, {"tx_hash": "0x" + "22" * 32}]})
WALLET_HELD = answer("owner approval required before ticket can be minted: the amount meets the period total", is_error=True)
GUIDE = answer({"answers": [{"topic": "x", "answer": "Uniswap v3 on Arbitrum: 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45.", "source": "AER Connect Owner's Guide v1.1, 13 September 2026, §5", "date": "2026-09-13"}]})
RELAY_ROAD = answer({"refused": True, "by": "aer-connect", "reason": "The Police tools that propose or track an assignment are the operator road", "source": "Spec 127"}, is_error=True)
DEAD_BEARER = h.McpAnswer(401, {"error": "invalid_token", "error_description": "The bearer token is not valid for this server."},
                          '{"error":"invalid_token","error_description":"The bearer token is not valid for this server."}', 2)
POLICE_HTTP_CREDENTIAL = answer("MCP Police REFUSED this call. Nothing was done, no payment was made and no answer was invented. MCP Police said: “the access platform does not recognise the presented credential”. This is the door answering, not a fault: it will refuse again in exactly the same way until whatever it named is put right. Tell the person what it said rather than trying again.", is_error=True)
WALLET_HTTP_JUDGMENT = answer("The MCP Wallet door REFUSED this call. Nothing was done, no payment was made and no answer was invented. The MCP Wallet door said: “WETH is not a stablecoin this door transfers on arbitrum”. This is the door answering, not a fault: it will refuse again in exactly the same way until whatever it named is put right. Tell the person what it said rather than trying again.", is_error=True)


class ClassifierTest(unittest.TestCase):
    def test_a_police_deny_is_refused_at_pre_flight(self):
        police = h.classify_police(POLICE_DENY)
        self.assertEqual(police["kind"], "deny")
        self.assertEqual(police["who"]["party"], "MCP Police")
        self.assertEqual(police["who"]["reason"], "denied")
        self.assertEqual(h.outcome_kind({"police": police}), S.PRE_FLIGHT)
        self.assertEqual(h.outcome_kind({"police": h.classify_police(POLICE_CONTEXT)}), S.PRE_FLIGHT)
        self.assertEqual(h.classify_police(POLICE_CONTEXT)["who"]["reason"], "context_incomplete:oracle")

    def test_a_police_manual_approval_required_is_held(self):
        police = h.classify_police(POLICE_HOLD)
        self.assertEqual(police["kind"], "hold")
        self.assertEqual(police["who"]["reason"], "manual_approval_required")
        self.assertEqual(h.outcome_kind({"police": police}), S.HELD)

    def test_a_wallet_error_body_is_refused_at_the_wallet(self):
        allow = h.classify_police(POLICE_ALLOW)
        self.assertEqual(allow["kind"], "allow")
        self.assertEqual(allow["receipt"], "police-receipt-1")
        build = h.classify_wallet(WALLET_ERROR)
        self.assertEqual(build["kind"], "refused")
        self.assertEqual(build["who"]["party"], "the MCP Wallet")
        self.assertEqual(build["who"]["reason"], "receipt_missing")
        self.assertTrue(build["who"]["sentence"].startswith("This action carries no pre-flight receipt"))
        self.assertEqual(h.outcome_kind({"police": allow, "build": build}), S.AT_WALLET)

    def test_the_engines_code_is_named_as_the_wallet_relayed_it(self):
        build = h.classify_wallet(WALLET_ENGINE)
        self.assertEqual(build["kind"], "refused")
        self.assertEqual(build["who"]["party"], "the engine's reason code as the MCP Wallet relayed it")
        self.assertEqual(build["who"]["reason"], "agent_destination_not_whitelisted")

    def test_the_wallets_owner_approval_sentence_is_held(self):
        build = h.classify_wallet(WALLET_HELD)
        self.assertEqual(build["kind"], "held")
        self.assertEqual(h.outcome_kind({"police": h.classify_police(POLICE_ALLOW), "build": build}), S.HELD)

    def test_a_successful_submit_is_allowed_and_signed(self):
        allow = h.classify_police(POLICE_ALLOW)
        build = h.classify_wallet(WALLET_TICKET)
        self.assertEqual(build["kind"], "ticket")
        self.assertEqual(build["ticket_id"], "t-1")
        self.assertEqual(build["legs"], 2)
        submit = h.classify_wallet(WALLET_SUBMIT)
        self.assertEqual(submit["kind"], "ticket")
        walk = {"police": allow, "build": build, "submit": submit, "hashes": [{"hash": "0x" + "11" * 32, "status": "success"}]}
        self.assertEqual(h.outcome_kind(walk), S.ALLOWED)
        self.assertEqual(h.hex64_in(WALLET_SUBMIT.data), ["0x" + "11" * 32, "0x" + "22" * 32])

    def test_a_guide_answer_with_the_words_is_answered(self):
        self.assertTrue(h.answered(GUIDE, ["0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", "Owner's Guide v1.1", "§5"]))
        self.assertFalse(h.answered(GUIDE, ["PancakeSwap"]))
        self.assertIn(S.ANSWERED, S.KINDS)
        self.assertEqual(len(S.KINDS), 5)

    def test_the_relays_road_refusal_and_a_dead_bearer_are_no_judgment(self):
        road = h.classify_police(RELAY_ROAD)
        self.assertEqual(road["kind"], "no_judgment")
        self.assertIn("AER Connect's relay", road["who"]["party"])
        dead = h.classify_police(DEAD_BEARER)
        self.assertEqual(dead["kind"], "no_judgment")
        self.assertEqual(h.outcome_kind({"police": dead}), "no outcome")
        self.assertEqual(h.outcome_kind({"police": road}), "no outcome")
        credential = h.classify_police(POLICE_HTTP_CREDENTIAL)
        self.assertEqual(credential["kind"], "no_judgment", "a credential refused at the door is not a judgment of the action")

    def test_a_doors_http_refusal_in_its_own_words_is_a_judgment(self):
        build = h.classify_wallet(WALLET_HTTP_JUDGMENT)
        self.assertEqual(build["kind"], "refused")
        self.assertEqual(build["who"]["party"], "the MCP Wallet (an HTTP refusal, relayed whole by AER Connect)")
        self.assertEqual(build["who"]["sentence"], "WETH is not a stablecoin this door transfers on arbitrum")

    def test_kind_matching_and_the_series_unions(self):
        self.assertTrue(h.kind_matches(S.REFUSED, S.PRE_FLIGHT))
        self.assertTrue(h.kind_matches(S.REFUSED, S.AT_WALLET))
        self.assertFalse(h.kind_matches(S.REFUSED, S.HELD))
        self.assertTrue(h.kind_matches(S.ALLOWED_OR_REFUSED, S.ALLOWED))
        self.assertFalse(h.kind_matches(S.PRE_FLIGHT, S.AT_WALLET))

    def test_arguments_take_the_doors_own_names(self):
        police_props = {"role_id": {}, "action_kind": {}, "chain": {}, "asset_symbol": {}, "to_address": {}, "amount_usd_cents": {}, "child_wallet_id": {}}
        fields = h.action_fields(S.pay(1, to="DEAD_ADDRESS"), None)
        args, omitted = h.arguments_for(police_props, fields, {"wallet_id": "w-1", "role_id": "payer.v1"})
        self.assertEqual(args, {"action_kind": "transfer_stable", "chain": "arbitrum", "asset_symbol": "USDC", "amount_usd_cents": 100,
                                "to_address": "0x000000000000000000000000000000000000dEaD", "child_wallet_id": "w-1", "role_id": "payer.v1"})
        self.assertEqual(omitted, [])
        guide_args, _ = h.arguments_for(None, h.action_fields(S.UNISWAP_ARBITRUM_TRADE, None), {"wallet_id": "w-1"})
        self.assertEqual(guide_args["venue"], "uniswap_v3")
        self.assertEqual(guide_args["to_asset"], "WETH")
        self.assertEqual(guide_args["contract_address"], "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45")
        self.assertEqual(guide_args["amount_usd"], 5)
        wallet_args, omitted = h.arguments_for({"wallet_id": {}, "action": {}, "amount_usd": {}, "chain": {}, "asset": {}, "police_receipt": {}}, fields, {"wallet_id": "w-1", "police_receipt": "r"})
        self.assertEqual(wallet_args["police_receipt"], "r")
        self.assertEqual(omitted, ["to_address"], "what the schema did not declare is named, not guessed")

    def test_a_destination_comes_only_from_the_two_permitted_places(self):
        with self.assertRaises(h.HarnessError):
            h.resolve_address("0x1111111111111111111111111111111111111111", None)
        self.assertEqual(h.resolve_address(S.OWNER, "0xfec697fc2D4323aE7618BFF2347C01E29653FB57"), "0xfec697fc2D4323aE7618BFF2347C01E29653FB57")
        self.assertEqual(h.resolve_address("FEE_ADDRESS", None), "0xabd0235C036CBeCb911DC74958B3c8F114cec42a")


if __name__ == "__main__":
    unittest.main()
