"""
A corridor that answers as told: one fake session shared by the tests that need a door.

It carries no `police.can_sign`, because MCP Police carries none (Spec T2 §1): a test
that still reached for it would fail here with "unexpected tool", which is the point.
The hash lives in the Wallet's `wallet_status`, as `pact.policy_hash`, and MCP Police
states what it judged under in a `judged` block on allow, deny and hold alike.

Its `get_balances` answers as the Wallet did before Spec 49 — the native balance and a
sentence — unless a `tokens` block is given, in which case it is stated where Spec 49's
Wallet puts it (Spec T3 §2); its `wallet_status` states `rails` where given (Spec T3 §3).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402

WALLET = "0x1111111111111111111111111111111111111111"
OWNER = "0xfec697fc2D4323aE7618BFF2347C01E29653FB57"
HASH = "0x" + "11" * 32
POLICY_HASH = "0x5237c7e1b0c4f1a9d8e3b26a5f470c91d2846ebb73f5a0c1e94d6b28fa310577"
SAME = object()  # judged_hash left alone: Police judged under the hash the Wallet states


# One blob carrying every word A3's three questions look for, so a fake corridor can
# answer Series A without the Guide itself.
GUIDE_SAID = (
    "Owner's Guide v1.1 §5: list 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45 for Uniswap on Arbitrum. "
    "A Trader cannot send: there is no road by which money leaves. "
    "Owner's Guide v1.1 §12, not yet built: answer a hold, return an agent, Curve as a class, "
    "Exchanges beyond the three, Chains beyond the three, USDT crossings to or from Base."
)


def rpc_answer(payload, is_error=False):
    result = {"content": [{"type": "text", "text": json.dumps(payload) if not isinstance(payload, str) else payload}]}
    if is_error:
        result["isError"] = True
    body = {"jsonrpc": "2.0", "id": 1, "result": result}
    return h.McpAnswer(200, body, json.dumps(body), 1)


class FakeSession:
    """Police allows or denies, the Wallet builds or refuses, and both state the pact's hash."""

    POLICE_PROPS = {"action_kind": {}, "chain": {}, "asset_symbol": {}, "to_address": {}, "amount_usd_cents": {},
                    "child_wallet_id": {}, "to_asset": {}, "venue": {}, "contract_address": {}, "to_chain": {}}
    WALLET_PROPS = {"wallet_id": {}, "action": {}, "amount_usd": {}, "to_address": {}, "chain": {}, "asset": {},
                    "police_receipt": {}, "ticket_id": {}}

    def __init__(self, police="allow", wallet="ticket", chain="arbitrum", role_id="payer.v1",
                 policy_hash=POLICY_HASH, judged_hash=SAME, judged=True, native_wei=1000000000000000,
                 rails=None, pact_in_status=True, tokens=None, document=None):
        self.police = police
        # Spec T21: `my_agent` states the compiled document (mcprelay.ts `document`); B4 reads the Payer's list off it.
        self.document = document
        self.wallet = wallet
        self.chain = chain
        self.role_id = role_id
        self.policy_hash = policy_hash
        self.judged_hash = policy_hash if judged_hash is SAME else judged_hash
        self.judged = judged
        self.native_wei = native_wei
        self.rails = rails
        self.pact_in_status = pact_in_status  # False: the hash is only in get_balances' pact_budget
        self.tokens = tokens  # None: no tokens block, as before Spec 49; else Spec 49's object, or a bare list
        self.calls = []
        self.submits = []
        self.secrets_seen = []
        self.tools = {
            "aerconnect_my_agent": {"name": "aerconnect_my_agent", "inputSchema": {"properties": {}}},
            "aerconnect_guide": {"name": "aerconnect_guide", "inputSchema": {"properties": {"question": {}}}},
            "police.check_action": {"name": "police.check_action", "inputSchema": {"properties": self.POLICE_PROPS}},
            "wallet.wallet_status": {"name": "wallet.wallet_status", "inputSchema": {"properties": {"wallet_id": {}}}},
            "wallet.get_balances": {"name": "wallet.get_balances", "inputSchema": {"properties": {"wallet_id": {}}}},
            "wallet.build_transaction": {"name": "wallet.build_transaction", "inputSchema": {"properties": self.WALLET_PROPS}},
            "wallet.submit_transaction": {"name": "wallet.submit_transaction", "inputSchema": {"properties": {"wallet_id": {}, "ticket_id": {}}}},
            "police.assignment_status": {"name": "police.assignment_status", "description": "NOT THE ROAD FOR AN AER CONNECT AGENT. …", "inputSchema": {"properties": {}}},
        }

    # -- the session -------------------------------------------------------
    def initialize(self, test_id):
        return None

    def tools_list(self, test_id):
        return list(self.tools.values())

    def schema_of(self, tool):
        listed = self.tools.get(tool)
        return listed["inputSchema"] if listed else None

    def properties_of(self, tool):
        listed = self.tools.get(tool)
        return listed["inputSchema"]["properties"] if listed else None

    # -- what each door answers --------------------------------------------
    def status_answer(self):
        body = {"wallet_id": "w-1", "address": WALLET, "chain": self.chain,
                "native": {"symbol": "ETH", "wei": self.native_wei}}
        if self.rails is not None:
            body["rails"] = self.rails
        if self.pact_in_status:
            body["pact"] = {"id": "p-1", "policy_hash": self.policy_hash, "state": "active", "policy_generation": 3}
        return body

    def balances_answer(self):
        body = {"wallet_id": "w-1", "address": WALLET, "chain": self.chain,
                "native": {"symbol": "ETH", "wei": self.native_wei},
                "sentence": "This door states the native balance only; ERC-20 balances are not read here.",
                "pact_budget": {"id": "p-1", "policy_hash": self.policy_hash, "spent_usd": 0}}
        if self.tokens is not None:
            # Spec 49: the tokens are stated, and the sentence that said they were not is gone.
            body["tokens"] = self.tokens
            body.pop("sentence")
        return body

    def check_action_answer(self, args):
        # The judged block is there whatever the verdict; an empty judged_hash makes a
        # block that carries no hash, which is not the same as no block at all.
        judged = {}
        if self.judged:
            judged["judged"] = {"pact_id": "p-1"}
            if self.judged_hash:
                judged["judged"]["policy_hash"] = self.judged_hash
        if self.police == "allow":
            body = {"verdict": "allow", "policy_hash": self.policy_hash,
                    "receipt": {"issued": True, "token": "police-receipt-secret-1", "nonce": "n-1"}}
        else:
            body = {"verdict": "deny", "reason": "denied", "policy_hash": self.policy_hash,
                    "sentence": "The destination %s is not on this agent’s list" % args.get("to_address")}
        body.update(judged)
        return body

    def call(self, tool, args, test_id):
        bare = tool.split(".", 1)[-1]
        if bare in h.ROADS or str(self.tools.get(tool, {}).get("description", "")).startswith(h.NOT_THE_ROAD_SAID):
            raise h.HarnessError("refusing to call %s" % tool)
        self.calls.append((test_id, tool, dict(args)))
        if tool == "aerconnect_my_agent":
            facts = {"source": "aer-connect", "agent": {"name": "Payer One", "roleId": self.role_id},
                     "connection": {"rank": "agent", "standing": "paid"},
                     "wallet": {"id": "w-1", "address": WALLET, "chain": self.chain},
                     "fundingWallet": {"address": OWNER}, "caps": {"said": "no caps"}, "said": "…"}
            if self.document is not None:
                facts["document"] = self.document
            return rpc_answer(facts)
        if tool == "aerconnect_guide":
            return rpc_answer({"said": GUIDE_SAID, "cites": "Owner's Guide v1.1"})
        if tool == "wallet.wallet_status":
            return rpc_answer(self.status_answer())
        if tool == "wallet.get_balances":
            return rpc_answer(self.balances_answer())
        if tool == "police.check_action":
            return rpc_answer(self.check_action_answer(args))
        if tool == "wallet.build_transaction":
            if "police_receipt" not in args:
                return rpc_answer("receipt_missing: This action carries no pre-flight receipt. Nobody enters but through the Police.", is_error=True)
            if self.wallet == "ticket":
                return rpc_answer({"ticket_id": "t-1", "wallet_id": "w-1", "legs": [{"kind": "transfer"}], "policy_hash": self.policy_hash})
            return rpc_answer("agent_destination_not_whitelisted: the destination is not on the list", is_error=True)
        if tool == "wallet.submit_transaction":
            self.submits.append(dict(args))
            return rpc_answer({"ticket_id": args.get("ticket_id"), "legs": [{"tx_hash": HASH}]})
        raise AssertionError("unexpected tool %s" % tool)


class FakeClock:
    """Time that moves only when the runner sleeps, so a ninety-second wait costs nothing."""

    def __init__(self):
        self.now = 0.0

    def sleep(self, seconds):
        self.now += seconds

    def __call__(self):
        return self.now


def run_file(chains=None):
    return {"issuer": "https://mcppro.aeredium.io",
            "testers": {"t": {"agents": {"trader": "t-trader", "payer": "t-payer", "payer_nogas": None},
                              "listed_address": OWNER, "payer_list_scope": "agent"}},
            "chains": chains or {}}


def runner_for(session, tmp, require_series_a=False, chains=None):
    clock = FakeClock()
    return h.Runner("t", run_file(chains), None, h.RunFolder(tmp, "t"), say=lambda s: None, ask=lambda q: "",
                    sleep=clock.sleep, clock=clock, session_factory=lambda label: session,
                    require_series_a=require_series_a)
