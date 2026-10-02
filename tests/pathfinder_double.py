"""
A double of the connector as Pathfinder walks it (Spec H-PATHFINDER): the T21 double of the auth, authorize, consent, token
and MCP roads (tests/consent_double.py, its passkey ceremonies verified for real), with the owner's account roads added
from aeredium/aer-connector at 9e20d6c (apps/server/src/routes/account.ts), the MCP door's fourteen tools with the inputSchemas
their own sources declare (MCP Police src/server.ts at c2af71c; the MCP Wallet internal/mcp/catalog.go at 125f788), and
Arbitrum One's JSON-RPC for the reader (the handleOps receipt with its UserOperationEvent and Transfer logs; Chainlink's
ETH/USD feed answering latestRoundData).

At least as strict as the services it stands in for: each road refuses what the connector refuses, with the connector's own
code, status and sentence (packages/shared/src/refusals.ts, http.ts) — a mutating press without the CSRF header, an answer
that is not a figure, a gas press below the floor, a delete while the wallet holds funds, a revoke of a connection already
ended — and the doors refuse what they refuse: Police an amount in dollars, the Wallet a build without the Police's receipt
for that action and a submit missing a required field. The platform debits gas by its own arithmetic (internal/gas/dollars.go
GasAndServiceCents, ten percent, at least a cent) at the double's price.

It answers through corridor_harness.http_request's own signature; a test patches that one function and no port is bound.
"""
import hashlib
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerconnect_harness as P  # noqa: E402
import corridor_harness as H  # noqa: E402
import tables as T  # noqa: E402

try:
    from .consent_double import ConnectorDouble, ISSUER, Refused, b64url
except ImportError:  # run as a top-level module by `unittest discover tests`
    from consent_double import ConnectorDouble, ISSUER, Refused, b64url

RPC_URL = T.REHEARSAL_RPC["arbitrum"].url
RPC_HOST = urllib.parse.urlparse(RPC_URL).netloc
ENTRY_POINT = "0x0000000071727De22E5E9d8BAf0edAc6f37da032"  # ERC-4337 EntryPoint v0.7
USDC_ARBITRUM = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
WETH_ARBITRUM = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
POOL = "0xC6962004f452bE9203591991D15f6b388e09E8D0"  # the USDC/WETH pool the router swaps through
PRICE_USD = 2500  # the double's price of ETH, for the feed and for the platform's debit alike
GAS_USED = 400000
GAS_PRICE_WEI = 10_000_000  # 0.01 gwei, an Arbitrum figure
DELEGATION_GAS_USED = 60000

# packages/shared/src/refusals.ts and apps/server/src/http.ts, verbatim, for the account roads' codes.
MESSAGES = {
    "NOT_AUTHENTICATED": "You are not signed in. Sign in with your passkey and try again.",
    "PASSKEY_REJECTED": "That passkey could not be verified, so nothing was done. Try again, and if it keeps failing enrol a new one.",
    "ANSWER_INVALID": "That answer cannot be accepted. The reason is named beside it.",
    "REQUEST_MALFORMED": "That request could not be read. Nothing was changed.",
    "SUBSCRIPTION_REQUIRED": "This needs a paid subscription and none has been paid yet. Choose a plan on your account page; nothing else on this connector works until it clears.",
    "SUBSCRIPTION_LAPSED": "Your subscription has lapsed, so reading still works and acting does not. Pay it on your account page and acting returns at once.",
    "AAP_UNREACHABLE": "The access platform could not be reached, so no credential was minted and nothing was created.",
    "AAP_REFUSED": "The access platform refused this. Its own words are beside this.",
    "WALLET_UNREACHABLE": "The MCP Wallet could not be reached, so no wallet was minted and no agent was registered.",
    "AGENT_NOT_FOUND": "There is no such agent here.",
    "AGENT_NOT_CONNECTABLE": "That agent cannot carry a connection: it holds no live credential, or it has been halted.",
    "ROLE_UNKNOWN": "There is no such role. The roles are MCP Police’s twelve, read from it live.",
    "CUSTOMER_NOT_PROVISIONED": "This customer has no sealed account key, so nothing can be minted on their behalf. Nothing was changed.",
    "CONNECTION_NOT_FOUND": "There is no such connection here.",
    "CONNECTION_NOT_REVOCABLE": "This connection has already ended. There is nothing left to revoke.",
}
STATUS = {
    "NOT_AUTHENTICATED": 401, "PASSKEY_REJECTED": 401, "ANSWER_INVALID": 400, "REQUEST_MALFORMED": 400, "SUBSCRIPTION_REQUIRED": 402,
    "SUBSCRIPTION_LAPSED": 402, "AAP_UNREACHABLE": 503, "AAP_REFUSED": 502, "WALLET_UNREACHABLE": 503, "AGENT_NOT_FOUND": 404,
    "AGENT_NOT_CONNECTABLE": 409, "ROLE_UNKNOWN": 400, "CUSTOMER_NOT_PROVISIONED": 409, "CONNECTION_NOT_FOUND": 404,
    "CONNECTION_NOT_REVOCABLE": 409,
}
NO_PLATFORM_ACCOUNT_YET_SAID = ("You have no account at the access platform yet: one is opened when your first agent is created, and your "
                                "gas account is kept on it. Create an agent first.")
GAS_NOT_OPEN_SAID = "Buying gas is not open on this door yet."
GAS_NOT_OPEN_WHY = ("This deployment holds no AAP_GAS_DOOR_KEY, the bearer the access platform’s credit road admits, so a payment taken now "
                    "could not be credited to your gas account. Nothing was opened and nothing was charged.")
NOT_PAID_CAUSE = "nothing was created and nothing was charged: an agent is created only for a paid subscription, and this one is not paid."
NO_LIVE_CONNECTION = ("This agent holds no live connection, and the Wallet answers about an agent only to that agent’s own credential — so "
                      "there is nothing this service may read on its behalf just now.")
HALT_FINALITY = ("Halting an agent is final. There is no un-halt: its credential is revoked at the access platform and both doors refuse it "
                 "on the very next knock. Granting authority again means creating a new agent, which is cheap and is meant to be.")
DELETE_FINALITY = ("Deleting an agent is final. Its seat in your package is free again and it no longer appears on this page; the register "
                   "keeps every agent that ever existed. Granting authority again means creating a new agent, which is cheap and is meant to be.")
DOLLARS = re.compile(r"^\d+(\.\d{1,2})?$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
# Spec 45 §5: what counts as funds, below which a balance is dust and the delete proceeds naming it.
FUNDS_THRESHOLDS = {"USDC": 10000, "WETH": 10 ** 14, "ETH": 10 ** 15}
DECIMALS = {"USDC": 6, "WETH": 18, "ETH": 18}
OFFERED = [{"key": "arbitrum", "displayName": "Arbitrum One", "family": "evm", "chainId": 42161, "nativeSymbol": "ETH"},
           {"key": "base", "displayName": "Base", "family": "evm", "chainId": 8453, "nativeSymbol": "ETH"},
           {"key": "ethereum", "displayName": "Ethereum", "family": "evm", "chainId": 1, "nativeSymbol": "ETH"}]


class AccountRefused(Exception):
    def __init__(self, code, cause=None, message=None, provenance=None, **detail):
        super().__init__(code)
        self.code = code
        self.message = message
        self.provenance = provenance
        self.detail = dict(detail)
        if cause is not None:
            self.detail["cause"] = cause

    def answer(self):
        """refusals.ts: "Routes turn this into an HTTP body verbatim" — the code, the message, the detail and, where there is one, the provenance."""
        body = {"code": self.code, "message": self.message or MESSAGES[self.code], "detail": self.detail}
        if self.provenance:
            body["provenance"] = self.provenance
        return STATUS[self.code], {"error": body}


def dollars(cents):
    return "%d.%02d" % (cents // 100, cents % 100)


def cents_from_dollars(text):
    text = text.strip()
    if not DOLLARS.match(text):
        return None
    whole, _, frac = text.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])


def platform_debit(wei, price_usd=PRICE_USD, bps=P.MARGIN_BPS):
    """internal/gas/dollars.go GasAndServiceCents at the double's own price, exactly: gas rounded half up, service the unrounded gas × bps, at least a cent."""
    gas, service = P.gas_and_service_cents(wei, price_usd * 100 * 10 ** 6, bps)
    return gas + service


def word(value):
    return "%064x" % value


def topic_of(address):
    return "0x" + address.lower().replace("0x", "").rjust(64, "0")


def schema(required, *names):
    return {"type": "object", "required": list(required), "properties": {name: {"type": "string"} for name in names}}


# The fourteen tools, with the inputSchemas their sources declare (the double's own copy; the harness reads what tools/list hands it).
TOOL_SCHEMAS = {
    "aerconnect_my_agent": {"type": "object", "properties": {}},
    "aerconnect_guide": schema((), "question"),
    "wallet.wallet_status": schema(("wallet_id",), "wallet_id"),
    "wallet.mint_wallet": schema(("funding_address", "role"), "agent_id", "funding_address", "role", "chain", "custody_type", "custom_role_id", "client_request_id"),
    "wallet.get_address": schema(("wallet_id",), "wallet_id"),
    "wallet.get_balances": schema(("wallet_id",), "wallet_id"),
    "wallet.build_transaction": schema(("wallet_id", "action"), "pact_id", "wallet_id", "action", "amount_usd", "to_address", "chain", "asset", "venue",
                                       "function", "counterparty_address", "contract_address", "to_asset", "to_chain", "method_selector", "approval_id",
                                       "client_request_id", "police_receipt"),
    "wallet.submit_transaction": schema(("agent_id", "wallet_id", "pact_id", "ticket_id", "action"), "agent_id", "wallet_id", "pact_id", "ticket_id",
                                        "action", "amount_usd", "to_address", "chain", "asset", "venue", "function", "counterparty_address",
                                        "contract_address", "method_selector", "to_asset", "to_chain"),
    "wallet.ticket_status": schema(("ticket_id",), "ticket_id"),
    "wallet.my_usage": {"type": "object", "properties": {}},
    "police.list_roles": {"type": "object", "properties": {}},
    "police.describe_role": schema(("role_id",), "role_id"),
    "police.check_action": schema(("role_id", "amount_usd_cents"), "role_id", "action_kind", "chain", "to_chain", "asset_symbol", "venue", "to_asset",
                                  "route_chosen_by", "route_detail", "function", "amount_usd_cents", "child_wallet_id", "to_address",
                                  "counterparty_address", "contract_address", "method_selector", "spent_today_usd_cents", "transactions_today",
                                  "slippage_bps", "price_deviation_bps", "simulation_passed", "oracle_check_passed", "amount", "amount_usd", "amount_dollars"),
    "police.my_usage": {"type": "object", "properties": {}},
}
for _name in ("amount", "amount_usd", "amount_dollars"):
    TOOL_SCHEMAS["police.check_action"]["properties"][_name]["description"] = "NOT ACCEPTED. Present only so an amount sent in dollars is refused rather than silently ignored."


def tool_listing(name):
    return {"name": name, "title": name, "description": "%s (the double)" % name, "inputSchema": TOOL_SCHEMAS.get(name, {"type": "object", "properties": {}}),
            "annotations": {"title": name}}


class PathfinderDouble(ConnectorDouble):
    def __init__(self, seated=True, catalogue=None, account_group=None, door_key=True, credit_on_checkout=0, gas_cents=1000,
                 wallet_usdc=0, funding_usdc=P.TRADE_RAW, funded_at_read=1, lands_later=0, delegate_first=True, police_verdict="allow", price_usd=PRICE_USD,
                 funds_left=False, margin_bps=P.MARGIN_BPS, gas_price_wei=GAS_PRICE_WEI, interrupt_on=None, receipt_lag=0,
                 fee_bps=T.FEE_BPS, fee_to=None, fee_leg=True, lose_press_answer=False, rpc_error_on=None, rpc_error_times=None, actual_gas_factor=1,
                 event_for_another_hash=False, account_funding=None, my_agent_wallet=None, rpc_host=RPC_HOST, **kwargs):
        """
        `catalogue` the names tools/list answers (default the fourteen); `account_group` a group GET /v1/account states under
        customer.signingGroup (None: it states none, as the connector at 9e20d6c does); `door_key` False is a deployment with
        no AAP_GAS_DOOR_KEY; `credit_on_checkout` cents the test ring credits when a checkout opens; `gas_cents` the gas
        account once the platform account exists; `wallet_usdc` what a new child wallet holds at birth (nothing, as a real one);
        `funding_usdc` what arrives in it by its `funded_at_read`-th balance read, standing in for the operator's transfer the
        harness asks for (0: nothing ever arrives); `lands_later` how many
        ticket_status reads pass before the operation names its handleOps transaction; `delegate_first` makes the first
        operation of a key delegate it (a second operation the platform debits); `funds_left` leaves funds behind the swap;
        `margin_bps` and `gas_price_wei` are the platform's margin and the chain's price of gas; `interrupt_on` an MCP method
        whose arrival raises KeyboardInterrupt, as a person pressing Ctrl-C there would; `receipt_lag` how many reads of a receipt
        the RPC answers null before it has caught up with the Wallet's word. The swap's commission, as the venue pays it
        (venues/uniswapv3 sweepTokenWithFee): the pool pays the router the gross, the router pays `fee_bps` of it to `fee_to`
        (default the agents' fee address, tables.py's) and the rest to the wallet; `fee_leg` False takes no commission at all.
        `lose_press_answer` creates the agent and then loses the answer on the way back, as a timeout would; `rpc_error_on` a
        JSON-RPC method the chain refuses with an error of its own, `rpc_error_times` times (None: always); `actual_gas_factor`
        makes the EntryPoint's actualGasCost that many times the receipt's cost (the platform debits the greater, settle.go);
        `event_for_another_hash` logs the UserOperationEvent of another operation; `account_funding` the funding wallet GET
        /v1/account states instead of the owner's; `my_agent_wallet` the wallet id aerconnect_my_agent states instead of the
        agent's; `rpc_host` the RPC's host.
        """
        super().__init__(seated=seated, **kwargs)
        self.catalogue = list(catalogue) if catalogue is not None else list(P.CATALOGUE)
        self.account_group = account_group
        self.door_key = door_key
        self.credit_on_checkout = credit_on_checkout
        self.gas_start = gas_cents
        self.gas = {}  # customer id → available cents
        self.wallet_usdc = wallet_usdc
        self.funding_usdc = funding_usdc
        self.funded_at_read = funded_at_read
        self.balance_reads = {}  # wallet address (lower) → how many times get_balances read it
        self.lands_later = lands_later
        self.delegate_first = delegate_first
        self.police_verdict = police_verdict
        self.price_usd = price_usd
        self.funds_left = funds_left
        self.margin_bps = margin_bps
        self.gas_price_wei = gas_price_wei
        self.interrupt_on = interrupt_on
        self.receipt_lag = receipt_lag
        self.fee_bps = fee_bps
        self.fee_to = fee_to or T.address("FEE_ADDRESS")
        self.fee_leg = fee_leg
        self.lose_press_answer = lose_press_answer
        self.rpc_error_on = rpc_error_on
        self.rpc_error_times = rpc_error_times
        self.rpc_errors_given = 0
        self.actual_gas_factor = actual_gas_factor
        self.event_for_another_hash = event_for_another_hash
        self.account_funding = account_funding
        self.my_agent_wallet = my_agent_wallet
        self.rpc_host = rpc_host
        self.receipt_reads = {}
        self.token_forms = []  # every form /token was handed, so a test can name the verifier and the code
        self.holdings = {}  # wallet address (lower) → {asset: raw}
        self.receipts = {}  # tx hash → receipt
        self.tickets = {}
        self.issued = {}  # police receipt token → the action it was issued for
        self.checkouts = []
        self.account_calls = []  # (method, path) of every account road reached
        self.tool_calls = []  # (name, arguments)
        self.deleted = []
        self.halted = []
        self.revoked = []
        self.block = 400_000_000
        self.delegated = set()

    # -- the transport: the chain's JSON-RPC at its own host, everything else as the connector -------------------
    def __call__(self, method, url, headers=None, body=None, timeout=None, follow_redirects=True):
        if urllib.parse.urlparse(url).netloc == self.rpc_host:
            payload = json.loads(body.decode("utf-8")) if body else {}
            self.calls.append((method, "rpc:" + str(payload.get("method")), 200))
            return H.HttpAnswer(200, {"Content-Type": "application/json"}, json.dumps(self.rpc(payload)), 1)
        return super().__call__(method, url, headers, body, timeout, follow_redirects)

    def route(self, method, path, query, headers, payload, follow_redirects):
        if path.startswith("/v1/account"):
            self.account_calls.append((method, path))
            try:
                return self.account(method, path, headers, payload)
            except AccountRefused as refused:
                status, answer = refused.answer()
                return status, answer, {}
        return super().route(method, path, query, headers, payload, follow_redirects)

    # -- the owner's account roads (routes/account.ts) ---------------------------------------------------------------
    def owner(self, headers, mutating=False):
        try:
            customer, _ = self.caller(headers, mutating=mutating)
        except Refused as refused:
            raise AccountRefused(refused.code, **refused.detail)
        return customer

    def mine(self, customer, agent_id):
        agent = next((a for a in self.agents if a["id"] == agent_id and a["customerId"] == customer["id"]), None)
        if agent is None:
            raise AccountRefused("AGENT_NOT_FOUND")
        return agent

    def assert_paid(self, customer):
        _, standing = self.standing_of(customer["id"])
        if standing != "paid":
            raise AccountRefused("SUBSCRIPTION_LAPSED" if standing == "lapsed" else "SUBSCRIPTION_REQUIRED", NOT_PAID_CAUSE)

    def provision(self, customer):
        if customer.get("aapAccountId") is None:
            customer["aapAccountId"] = "acct-" + secrets.token_hex(4)
            self.gas[customer["id"]] = self.gas_start

    @staticmethod
    def reason_of(payload):
        reason = (payload or {}).get("reason")
        if not isinstance(reason, str) or not 1 <= len(reason) <= 500:
            raise AccountRefused("REQUEST_MALFORMED", issues="reason: String must contain at least 1 character(s)")
        return reason.strip()

    def read_answers(self, answers):
        """routes/consent.ts readAnswers, the refusals it makes before any remote call."""
        if not isinstance(answers, dict):
            raise AccountRefused("REQUEST_MALFORMED", issues="answers: Expected object, received %s" % type(answers).__name__)
        for field in ("perTxUsd", "dailyUsd", "holdAboveUsd", "maxTxPerDay", "counterpartiesScope"):
            if not isinstance(answers.get(field), str):
                raise AccountRefused("REQUEST_MALFORMED", issues="answers.%s: Required" % field)
        if not isinstance(answers.get("chains"), list) or not answers["chains"]:
            raise AccountRefused("REQUEST_MALFORMED", issues="answers.chains: Array must contain at least 1 element(s)")
        if not isinstance(answers.get("counterparties"), list):
            raise AccountRefused("REQUEST_MALFORMED", issues="answers.counterparties: Required")
        for field, label in (("perTxUsd", "Per trade"), ("dailyUsd", "Per day")):
            if answers[field].strip() == "":
                raise AccountRefused("ANSWER_INVALID", "%s was left blank, and a blank is not a figure" % label)
        for field in ("perTxUsd", "dailyUsd", "holdAboveUsd"):
            if answers[field].strip() and cents_from_dollars(answers[field]) is None:
                raise AccountRefused("ANSWER_INVALID", "%s must be an amount in US dollars, written as digits with at most two decimal places — it was %s"
                                     % (field, json.dumps(answers[field])))
        if answers["maxTxPerDay"].strip() and not answers["maxTxPerDay"].strip().isdigit():
            raise AccountRefused("ANSWER_INVALID", "the number of transactions a day must be a whole number written as digits")
        chains = []
        for raw in answers["chains"]:
            if raw.strip() and raw.strip() not in chains:
                chains.append(raw.strip())
        offered = [c["key"] for c in OFFERED]
        strangers = [c for c in chains if c not in offered]
        if strangers:
            raise AccountRefused("ANSWER_INVALID", "%s is not a chain this connector offers: %s. Nothing was created." % (", ".join(strangers), ", ".join(offered)))
        assets = None
        if "assets" in answers:
            assets = []
            for raw in answers["assets"]:
                symbol = raw.strip().upper()
                if symbol and symbol not in assets:
                    assets.append(symbol)
        return {"perTxCents": cents_from_dollars(answers["perTxUsd"]), "dailyCents": cents_from_dollars(answers["dailyUsd"]),
                "holdAboveCents": cents_from_dollars(answers["holdAboveUsd"]) if answers["holdAboveUsd"].strip() else 0,
                "maxTxPerDay": int(answers["maxTxPerDay"]) if answers["maxTxPerDay"].strip() else 0,
                "counterpartiesScope": answers["counterpartiesScope"].strip().lower(),
                "counterparties": [a.strip() for a in answers["counterparties"] if a.strip()], "chains": chains, "homeChain": chains[0],
                **({} if assets is None else {"assets": assets})}

    @staticmethod
    def document_of(agent_id, role_id, read):
        """services/ceremony.ts agentPolicyDocument."""
        return {"role_id": role_id, "template_id": role_id, "version": "1", "nonce": agent_id,
                "scope": {"chains": [read["homeChain"]] + [c for c in read["chains"] if c != read["homeChain"]],
                          **({"assets_allowed": list(read["assets"])} if "assets" in read else {}),
                          "counterparties_whitelist_scope": read["counterpartiesScope"], "counterparties_allowed": list(read["counterparties"])},
                "budgets": {"per_tx_cap_usd": read["perTxCents"] / 100, "daily_cap_usd": read["dailyCents"] / 100},
                "velocity": {"max_tx_per_day": read["maxTxPerDay"]},
                "approvals": {"human_approval_threshold_usd": read["holdAboveCents"] / 100}}

    def agent_view(self, agent):
        return {"id": agent["id"], "name": agent["name"], "roleId": agent["roleId"], "state": agent["state"], "haltedAt": agent.get("haltedAt"),
                "haltedReason": agent.get("haltedReason"), "deletedAt": agent.get("deletedAt"), "deletedReason": agent.get("deletedReason"),
                "credentialPrefix": "cp-" + agent["id"][:4],
                "wallet": {"id": agent["walletId"], "address": agent["walletAddress"], "chain": agent["walletChain"], "isMock": False} if agent.get("walletId") else None,
                "pact": {"id": agent["pactId"], "state": agent.get("pactState", "active"), "document": agent["document"], "documentHash": "0x" + "ab" * 32},
                "haltable": agent["state"] == "active", "deletable": agent["state"] != "deleted"}

    def account(self, method, path, headers, payload):
        rest = path[len("/v1/account"):]
        if method == "GET" and rest == "":
            customer = self.owner(headers)
            subscription, standing = self.standing_of(customer["id"])
            funding = self.account_funding or customer.get("fundingAddress")
            view_customer = {"id": customer["id"], "displayName": customer["displayName"], "email": customer["email"], "country": customer["country"],
                             "fundingWallet": {"address": funding} if funding else None}
            if self.account_group:
                view_customer["signingGroup"] = self.account_group
            mine = [a for a in self.agents if a["customerId"] == customer["id"]]
            return 200, {"customer": view_customer,
                         "subscription": {"plan": subscription["plan"], "state": subscription["state"], "standing": standing, "priceCents": subscription["priceCents"]}
                         if subscription else {"plan": None, "state": None, "standing": standing},
                         "agents": [self.agent_view(a) for a in mine if a["state"] != "deleted"],
                         "allowance": {"activeAgents": len([a for a in mine if a["state"] == "active"])},
                         "connections": [{"id": c["id"], "agentId": c["agentId"], "clientId": c["clientId"], "rank": {"id": c["rank"]},
                                          "state": c["state"], "revocable": c["state"] == "active"}
                                         for c in self.connections.values() if c["customerId"] == customer["id"]],
                         "receipts": []}, {}
        if method == "GET" and rest == "/agents/new":
            customer = self.owner(headers)
            self.assert_paid(customer)
            self.provision(customer)  # GET /v1/account/agents/new provisions the account: it creates state
            return 200, {"roles": [dict(r) for r in self.roles],
                         "chainOffer": {"chains": [dict(c) for c in OFFERED], "unreadable": None, "said": {}, "signsOn": "…"},
                         "allowance": {"activeAgents": len([a for a in self.agents if a["customerId"] == customer["id"] and a["state"] == "active"])},
                         "said": "This creates a new agent on your account…"}, {}
        if method == "POST" and rest == "/agents":
            customer = self.owner(headers, mutating=True)
            body = payload or {}
            for field in ("name", "roleId", "fundingAddress", "answers", "nonce", "issuedAtMs", "response"):
                if field not in body:
                    raise AccountRefused("REQUEST_MALFORMED", issues="%s: Required" % field)
            if not isinstance(body["issuedAtMs"], int):
                raise AccountRefused("REQUEST_MALFORMED", issues="issuedAtMs: Expected number")
            read = self.read_answers(body["answers"])
            # verifyStepUp, before the money (the ruling of 8 September 2026)
            try:
                challenge = self.assert_challenge("approve", body["nonce"], body["issuedAtMs"])
                passkey = self.passkeys.get((body["response"] or {}).get("id"))
                if not passkey or passkey["customerId"] != customer["id"]:
                    raise Refused("PASSKEY_REJECTED", "that passkey does not belong to the person signed in here, so nothing was approved and no agent was created")
                self.verify_assertion(body["response"], challenge, passkey)
            except Refused as refused:
                raise AccountRefused(refused.code, **refused.detail)
            self.assert_paid(customer)
            self.provision(customer)
            role = next((r for r in self.roles if r["id"] == body["roleId"]), None)
            if role is None:
                raise AccountRefused("ROLE_UNKNOWN")
            active = [a for a in self.agents if a["customerId"] == customer["id"] and a["state"] == "active"]
            if len(active) >= self.seats:
                raise AccountRefused("AAP_REFUSED", "the access platform refused the agent's own credential (HTTP 409): plan connect-solo admits %d agent "
                                     "credentials and %d are active" % (self.seats, len(active)), status="409")
            for index, address in enumerate(read["counterparties"]):
                if not ADDRESS.match(address):
                    raise AccountRefused("AAP_REFUSED", "the access platform refused the agent's pact (HTTP 400): scope.counterparties_allowed[%d] is %s, "
                                         "which is not an address on %s" % (index, json.dumps(address), read["homeChain"]), status="400")
            if customer.get("fundingAddress") is None:
                customer["fundingAddress"] = body["fundingAddress"].strip()
            agent_id = str(uuid.uuid4())
            address = H.checksum_address("0x" + secrets.token_hex(20))
            agent = {"id": agent_id, "customerId": customer["id"], "name": body["name"].strip(), "roleId": body["roleId"], "state": "active",
                     "walletId": str(uuid.uuid4()), "walletAddress": address, "walletChain": read["homeChain"],
                     "document": self.document_of(agent_id, body["roleId"], read), "pactId": "aerconn:%s" % agent_id, "pactState": "active"}
            self.agents.append(agent)
            self.holdings[address.lower()] = {"USDC": self.wallet_usdc, "WETH": 0, "ETH": 0}
            if self.lose_press_answer:
                raise H.Unreachable("POST %s/v1/account/agents: timed out" % self.issuer)  # created, and the answer lost on the way back
            return 200, {"agent": self.agent_view(agent), "howClaudeReachesIt": "To let Claude act as this agent, connect AER Connect from Claude and choose it at step three.",
                         "said": "%s is created. It has its own child wallet, its own credential and a pact at the access platform carrying the limits you set." % agent["name"]}, {}
        match = re.match(r"^/agents/([^/]+)/(policy|wallet-record|halt|delete)$", rest)
        if match:
            agent_id, action = match.groups()
            if action == "wallet-record" and method == "GET":
                customer = self.owner(headers)
                agent = self.mine(customer, agent_id)
                live = self.connection_of(agent["id"])
                if live is None:
                    return 200, {"walletRecord": {"walletId": agent["walletId"], "status": None, "usage": None, "unreachable": NO_LIVE_CONNECTION,
                                                  "absent": None, "notServed": "…"}}, {}
                return 200, {"walletRecord": {"walletId": agent["walletId"], "status": self.wallet_status(agent), "statusUnreadable": None,
                                              "usage": {"gate_decisions": 0}, "usageUnreadable": None, "unreachable": None, "absent": None, "notServed": "…"}}, {}
            if method != "POST":
                raise AssertionError("the test reached for %s %s" % (method, path))
            customer = self.owner(headers, mutating=True)
            if action == "policy":  # the edit road (Spec C-BIRTH-100): re-files the policy only; the pact keeps its id, the agent and its token are untouched
                body = payload or {}
                if "answers" not in body:
                    raise AccountRefused("REQUEST_MALFORMED", issues="answers: Required")
                agent = self.mine(customer, agent_id)
                read = self.read_answers(body["answers"])
                agent["document"] = self.document_of(agent["id"], agent["roleId"], read)
                return 200, {"agent": {"id": agent["id"], "name": agent["name"], "roleId": agent["roleId"]},
                             "pact": {"id": agent["pactId"], "state": "active", "validUntil": None, "document": agent["document"]},
                             "entrySaid": None, "said": "%s’s policy is edited; the agent and its credential are untouched." % agent["name"]}, {}
            reason = self.reason_of(payload)
            agent = self.mine(customer, agent_id)
            if action == "halt":
                if agent["state"] != "active":
                    raise AccountRefused("AGENT_NOT_CONNECTABLE", "this agent has already been halted; halting is final and there is no un-halt")
                closed = self.close_connections(agent, "the agent was halted: %s" % reason)
                agent.update(state="halted", haltedAt=H.now_iso(), haltedReason=reason)
                self.halted.append(agent["id"])
                return 200, {"agent": {"id": agent["id"], "state": "halted", "haltedAt": agent["haltedAt"], "haltedReason": reason},
                             "connectionsClosed": closed, "pact": {"id": agent["pactId"], "revoked": True, "said": "Its pact was revoked…"},
                             "policyEntry": {"id": "pe-" + agent["id"][:6], "deactivated": True, "said": "…its seat in your package is free again."},
                             "finality": HALT_FINALITY}, {}
            if action == "delete":
                if agent["state"] == "deleted":
                    raise AccountRefused("AGENT_NOT_CONNECTABLE", message="%s was deleted at %s." % (agent["name"], agent.get("deletedAt")))
                held = self.holdings.get(agent["walletAddress"].lower(), {})
                funds = ["%s %s on %s" % (H.format_units(raw, DECIMALS[asset]), asset, agent["walletChain"]) for asset, raw in held.items()
                         if raw >= FUNDS_THRESHOLDS[asset]]
                if funds:
                    said = ", ".join(funds)
                    raise AccountRefused("AGENT_NOT_CONNECTABLE", message="This agent’s wallet still holds %s. Move the funds out before deleting the agent; a "
                                         "deleted agent cannot move anything, and its funds would be out of sight." % said, balances=said, agentState=agent["state"])
                dust = ["%s %s" % (H.format_units(raw, DECIMALS[asset]), asset) for asset, raw in held.items() if 0 < raw < FUNDS_THRESHOLDS[asset]]
                closed = self.close_connections(agent, "the agent was deleted: %s" % reason)
                agent.update(state="deleted", deletedAt=H.now_iso(), deletedReason=reason)
                self.deleted.append(agent["id"])
                said = "Deleted." if not dust else "Deleted. Its wallet on %s still holds %s of dust, which is abandoned." % (agent["walletChain"], " and ".join(dust))
                return 200, {"agent": {"id": agent["id"], "name": agent["name"], "state": "deleted", "deletedAt": agent["deletedAt"], "deletedReason": reason},
                             "connectionsClosed": closed, "pact": {"id": agent["pactId"], "revoked": "at the halt"},
                             "policyEntry": {"id": "pe-" + agent["id"][:6], "deactivated": True}, "said": said, "dust": [], "finality": DELETE_FINALITY}, {}
        match = re.match(r"^/connections/([^/]+)/revoke$", rest)
        if match and method == "POST":
            customer = self.owner(headers, mutating=True)
            reason = self.reason_of(payload)
            connection = self.connections.get(match.group(1))
            if connection is None or connection["customerId"] != customer["id"]:
                raise AccountRefused("CONNECTION_NOT_FOUND")
            if connection["state"] != "active":
                raise AccountRefused("CONNECTION_NOT_REVOCABLE", state=connection["state"])
            connection.update(state="revoked", revokedAt=H.now_iso(), revokedReason=reason)
            self.revoked.append(connection["id"])
            return 200, {"connection": {"id": connection["id"], "state": "revoked", "revokedAt": connection["revokedAt"], "revokedReason": reason},
                         "finality": "Revoking a connection is final…", "agentUntouched": "This closed Claude’s door only…"}, {}
        if method == "POST" and rest == "/gas":
            customer = self.owner(headers, mutating=True)
            if not self.door_key:
                raise AccountRefused("AAP_UNREACHABLE", GAS_NOT_OPEN_WHY, message=GAS_NOT_OPEN_SAID,
                                     provenance={"source": "aer-connector", "reference": "AAP_GAS_DOOR_KEY"})
            typed = str((payload or {}).get("amountUsd") or "").strip()
            amount = 1000 if typed == "" else cents_from_dollars(typed)
            if amount is None:
                raise AccountRefused("ANSWER_INVALID", "the amount must be in US dollars, like 10 or 12.50, and “%s” is not. Nothing was charged." % typed)
            if amount < 1000:
                raise AccountRefused("ANSWER_INVALID", "US$%s is below the least gas that can be bought at once, which is US$10.00. Nothing was charged." % dollars(amount))
            if customer.get("aapAccountId") is None:
                raise AccountRefused("CUSTOMER_NOT_PROVISIONED", "%s Nothing was charged." % NO_PLATFORM_ACCOUNT_YET_SAID)
            session_id = "cs_test_" + secrets.token_hex(12)
            self.checkouts.append({"customerId": customer["id"], "amountCents": amount, "id": session_id})
            if self.credit_on_checkout:
                self.gas[customer["id"]] = self.gas.get(customer["id"], 0) + self.credit_on_checkout
            return 200, {"checkout": {"url": "https://checkout.stripe.test/c/pay/%s" % session_id, "id": session_id}, "amountCents": amount,
                         "said": "Taking you to the payment desk to buy US$%s of gas." % dollars(amount)}, {}
        if method == "GET" and rest == "/gas-account":
            customer = self.owner(headers)
            if customer.get("aapAccountId") is None:
                return 200, {"read": "unreadable", "available": None, "said": NO_PLATFORM_ACCOUNT_YET_SAID, "low": None, "lowSaid": None,
                             "unreadable": NO_PLATFORM_ACCOUNT_YET_SAID, "minimumTopUpCents": 1000, "defaultTopUpCents": 1000, "held": []}, {}
            cents = self.gas.get(customer["id"], 0)
            return 200, {"read": "platform", "available": {"cents": cents, "said": "US$%s" % dollars(cents)}, "said": "Gas account: US$%s" % dollars(cents),
                         "low": cents < 50, "lowSaid": None, "unreadable": None, "minimumTopUpCents": 1000, "defaultTopUpCents": 1000, "held": []}, {}
        raise AssertionError("the test reached for %s %s" % (method, path))

    def close_connections(self, agent, why):
        closed = 0
        for connection in self.connections.values():
            if connection["agentId"] == agent["id"] and connection["state"] == "active":
                connection.update(state="closed", revokedReason=why)
                closed += 1
        return closed

    def wallet_status(self, agent):
        return {"wallet_id": agent["walletId"], "address": agent["walletAddress"], "chain": agent["walletChain"], "has_agent": True,
                "has_policy": True, "operational": True, "signing_group": "group-100"}

    # -- the MCP door: the connector's two tools, the Wallet's eight, the Police's four ---------------------------------
    def mcp(self, headers, payload):
        bearer = next((v for k, v in headers.items() if k.lower() == "authorization"), "").replace("Bearer ", "")
        held = self.access_tokens.get(bearer)
        connection = self.connections.get((held or {}).get("connectionId"))
        if not held or connection is None or connection["state"] != "active":
            return 401, {"jsonrpc": "2.0", "error": {"code": -32001, "message": "invalid_token: the bearer is not one this server issued, or its connection has ended"}}, \
                {"WWW-Authenticate": 'Bearer error="invalid_token"'}
        agent = next((a for a in self.agents if a["id"] == connection["agentId"]), None)
        method = payload.get("method")
        rpc_id = payload.get("id")
        if self.interrupt_on and method == self.interrupt_on:
            raise KeyboardInterrupt
        if method == "notifications/initialized":
            return 202, "", {}
        if method == "initialize":
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"protocolVersion": H.PROTOCOL_VERSION, "capabilities": {"tools": {}},
                                                                     "serverInfo": {"name": "aer-connect", "version": "double"}, "instructions": "AER Connect."}}, {}
        if method == "tools/list":
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": [tool_listing(n) for n in self.catalogue]}}, {}
        if method != "tools/call":
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "method not found"}}, {}
        name = (payload.get("params") or {}).get("name")
        args = (payload.get("params") or {}).get("arguments") or {}
        self.tool_calls.append((name, dict(args)))
        if name not in self.catalogue:
            return self.tool_text(rpc_id, "There is no tool called %s on this connector." % name, error=True)
        missing = [field for field in TOOL_SCHEMAS.get(name, {}).get("required", []) if args.get(field) in (None, "")]
        if missing:
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": "missing required argument(s): %s" % ", ".join(missing)}}, {}
        handler = getattr(self, "tool_" + name.replace(".", "_"), None)
        if handler is None:
            return self.tool_json(rpc_id, {"tool": name, "said": "answered by the double"})
        return handler(rpc_id, agent, connection, args)

    @staticmethod
    def tool_json(rpc_id, data, error=False):
        result = {"content": [{"type": "text", "text": json.dumps(data)}], "structuredContent": data}
        if error:
            result["isError"] = True
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": result}, {}

    @staticmethod
    def tool_text(rpc_id, text, error=False):
        result = {"content": [{"type": "text", "text": text}]}
        if error:
            result["isError"] = True
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": result}, {}

    def tool_aerconnect_my_agent(self, rpc_id, agent, connection, args):
        customer = self.customers[agent["customerId"]]
        cents = self.gas.get(customer["id"], 0)
        _, standing = self.standing_of(customer["id"])
        return self.tool_json(rpc_id, {
            "source": "aer-connect", "agent": {"name": agent["name"], "roleId": agent["roleId"]},
            "connection": {"rank": connection["rank"], "standing": standing},
            "wallet": {"id": self.my_agent_wallet or agent["walletId"], "address": agent["walletAddress"], "chain": agent["walletChain"]},
            "fundingWallet": {"address": customer.get("fundingAddress")},
            "limits": {"writtenBy": "…", "pactId": agent["pactId"], "state": agent.get("pactState", "active"), "documentHash": "0x" + "ab" * 32,
                       "policyHash": "0x" + "cd" * 32, "policyVersion": 1, "document": agent["document"], "said": "…"},
            "gas_account": "US$%s" % dollars(cents),
            "gasAccount": {"availableUsdCents": cents, "low": cents < 50, "lowSaid": None, "unreadable": None, "said": "…"}, "said": "…"})

    def tool_police_check_action(self, rpc_id, agent, connection, args):
        for decoy in ("amount", "amount_usd", "amount_dollars"):
            if decoy in args:
                return self.tool_text(rpc_id, "MCP Police REFUSED this call. It said: “%s is NOT ACCEPTED: amounts are integers of USD cents”" % decoy, error=True)
        if not isinstance(args.get("amount_usd_cents"), int):
            return self.tool_text(rpc_id, "MCP Police REFUSED this call. It said: “amount_usd_cents must be a whole number of USD cents”", error=True)
        document = agent["document"]
        allowed = [a.lower() for a in document["scope"]["counterparties_allowed"]]
        cents = self.gas.get(agent["customerId"], 0)
        base = {"advisory": "ADVISORY", "vessel": "…", "role": {"id": args.get("role_id"), "name": "Trader", "template_version": 9, "content_hash": "x"},
                "judged": {"source": "pact", "pact_id": agent["pactId"], "policy_id": "p1", "policy_version": 1, "policy_hash": "0x" + "cd" * 32},
                "gas_account": "US$%s" % dollars(cents), "gas_low": cents < 50}
        if str(args.get("contract_address") or "").lower() not in allowed:
            return self.tool_json(rpc_id, dict(base, verdict="deny", decision="reject", reason="agent_destination_not_whitelisted", context_incomplete=None,
                                               sentence="the destination is not on this agent's list"))
        if self.police_verdict == "deny":
            return self.tool_json(rpc_id, dict(base, verdict="deny", decision="reject", reason="PolicyDenied: denied (cause: legacy_limit_zero; the per-payment "
                                               "limit has not been set to more than zero. Set it to a figure above zero for the payment to be approved.)", context_incomplete=None))
        if args["amount_usd_cents"] > int(round(document["approvals"]["human_approval_threshold_usd"] * 100)):
            return self.tool_json(rpc_id, dict(base, verdict="hold_for_manual_approval", decision="hold", reason="manual_approval_required", context_incomplete=None))
        token = "rcpt_" + b64url(secrets.token_bytes(24))
        self.issued[token] = {"wallet_id": args.get("child_wallet_id"), "amount_usd_cents": args["amount_usd_cents"], "contract_address": args.get("contract_address")}
        receipt = {"issued": bool(args.get("child_wallet_id")), "id": "rid-" + secrets.token_hex(4)}
        if args.get("child_wallet_id"):
            receipt["token"] = token
        return self.tool_json(rpc_id, dict(base, verdict="allow", decision="commit", reason="allowed", context_incomplete=None, receipt=receipt))

    def balances_of(self, agent):
        held = self.holdings.get(agent["walletAddress"].lower(), {})
        rows = []
        for asset, contract in (("USDC", USDC_ARBITRUM), ("WETH", WETH_ARBITRUM)):
            raw = held.get(asset, 0)
            rows.append({"asset": asset, "chain": agent["walletChain"], "contract": contract, "decimals": DECIMALS[asset], "raw": str(raw),
                         "amount": H.format_units(raw, DECIMALS[asset]), "available": True, "source": "arbitrum via the double"})
        return {"wallet_id": agent["walletId"], "chain": agent["walletChain"], "native": {"symbol": "ETH", "wei": str(held.get("ETH", 0))},
                "tokens": {"balances": rows, "road": "the pact's document", "said": "…"}}

    def tool_wallet_get_balances(self, rpc_id, agent, connection, args):
        if args.get("wallet_id") != agent["walletId"]:
            return self.tool_text(rpc_id, "wallet_not_accessible: wallet not accessible to agent", error=True)
        key = agent["walletAddress"].lower()
        self.balance_reads[key] = self.balance_reads.get(key, 0) + 1
        if self.balance_reads[key] == self.funded_at_read and self.funding_usdc:
            held = self.holdings.setdefault(key, {})
            held["USDC"] = held.get("USDC", 0) + self.funding_usdc  # the operator's transfer, arrived
        return self.tool_json(rpc_id, self.balances_of(agent))

    def tool_wallet_build_transaction(self, rpc_id, agent, connection, args):
        if args.get("wallet_id") != agent["walletId"]:
            return self.tool_text(rpc_id, "wallet_not_accessible: wallet not accessible to agent", error=True)
        issued = self.issued.get(str(args.get("police_receipt") or ""))
        if issued is None or issued["wallet_id"] != args.get("wallet_id"):
            return self.tool_text(rpc_id, "receipt_missing: this door demands MCP Police's pre-flight receipt for this exact action", error=True)
        if "amount_usd_cents" in args or not isinstance(args.get("amount_usd"), (int, float)):
            return self.tool_text(rpc_id, "amount_invalid: amount_usd is required, in US dollars", error=True)
        held = self.holdings.get(agent["walletAddress"].lower(), {})
        raw = int(round(float(args["amount_usd"]) * 10 ** DECIMALS["USDC"]))
        if held.get("USDC", 0) < raw:
            return self.tool_text(rpc_id, "insufficient_balance: the wallet holds %d minor units of USDC and the trade sells %d" % (held.get("USDC", 0), raw), error=True)
        ticket_id = str(uuid.uuid4())
        self.tickets[ticket_id] = {"id": ticket_id, "agent": agent["id"], "args": dict(args), "raw": raw, "state": "minted", "reads": 0}
        return self.tool_json(rpc_id, {"ticket_id": ticket_id, "pact_id": agent["pactId"], "legs": [{"call": "approve"}, {"call": "swap"}],
                                       "expires_at": "…", "said": "ticket minted"})

    def tool_wallet_submit_transaction(self, rpc_id, agent, connection, args):
        ticket = self.tickets.get(str(args.get("ticket_id")))
        if ticket is None or ticket["state"] != "minted":
            return self.tool_text(rpc_id, "ticket_invalid: no unspent ticket by that id", error=True)
        if args.get("agent_id") != agent["id"]:
            return self.tool_text(rpc_id, "agent_mismatch: agent_id must match the calling agent", error=True)
        if args.get("pact_id") != agent["pactId"]:
            return self.tool_text(rpc_id, "pact_mismatch: the pact named is not the one the ticket was built under", error=True)
        ticket["state"] = "consumed"
        address = agent["walletAddress"]
        held = self.holdings.setdefault(address.lower(), {})
        gross = ticket["raw"] * 10 ** 12 // self.price_usd  # USDC (6 decimals) → WETH (18) at the price
        fee = gross * self.fee_bps // 10000 if self.fee_leg else 0
        bought = gross - fee
        router = ticket["args"].get("contract_address") or T.address("UNISWAP_V3_ARBITRUM")
        held["USDC"] = held.get("USDC", 0) - ticket["raw"]
        held["WETH"] = held.get("WETH", 0) + bought
        if self.funds_left:
            held["USDC"] += 50000
        user_op_hash = "0x" + secrets.token_hex(32)
        handle_ops = "0x" + secrets.token_hex(32)
        self.block += 7
        wei = GAS_USED * self.gas_price_wei
        logs = [
            {"address": USDC_ARBITRUM, "topics": [H.TRANSFER_TOPIC, topic_of(address), topic_of(POOL)], "data": "0x" + word(ticket["raw"])},
            {"address": WETH_ARBITRUM, "topics": [H.TRANSFER_TOPIC, topic_of(POOL), topic_of(router)], "data": "0x" + word(gross)},
        ]
        if self.fee_leg:
            logs.append({"address": WETH_ARBITRUM, "topics": [H.TRANSFER_TOPIC, topic_of(router), topic_of(self.fee_to)], "data": "0x" + word(fee)})
        logs.append({"address": WETH_ARBITRUM, "topics": [H.TRANSFER_TOPIC, topic_of(router), topic_of(address)], "data": "0x" + word(bought)})
        actual = wei * self.actual_gas_factor
        named_hash = ("0x" + secrets.token_hex(32)) if self.event_for_another_hash else user_op_hash
        logs.append({"address": ENTRY_POINT, "topics": [P.USER_OPERATION_EVENT, named_hash, topic_of(address), topic_of(P.PAYMASTER["arbitrum"])],
                     "data": "0x" + word(0) + word(1) + word(actual) + word(GAS_USED)})
        for index, log in enumerate(logs):
            log.update(logIndex=hex(index), transactionHash=handle_ops, blockNumber=hex(self.block))
        self.receipts[handle_ops] = {"transactionHash": handle_ops, "status": "0x1", "blockNumber": hex(self.block), "gasUsed": hex(GAS_USED),
                                     "effectiveGasPrice": hex(self.gas_price_wei), "logs": logs}
        debit = platform_debit(max(wei, actual), self.price_usd, self.margin_bps)  # settle.go: the greater is the gas
        delegation = None
        if self.delegate_first and address.lower() not in self.delegated:
            delegation = "0x" + secrets.token_hex(32)
            self.delegated.add(address.lower())
            self.receipts[delegation] = {"transactionHash": delegation, "status": "0x1", "blockNumber": hex(self.block - 1),
                                         "gasUsed": hex(DELEGATION_GAS_USED), "effectiveGasPrice": hex(self.gas_price_wei), "logs": []}
            self.gas[agent["customerId"]] = self.gas.get(agent["customerId"], 0) - platform_debit(DELEGATION_GAS_USED * self.gas_price_wei, self.price_usd,
                                                                                                    self.margin_bps)
        self.gas[agent["customerId"]] = self.gas.get(agent["customerId"], 0) - debit
        landed = self.lands_later == 0
        ticket.update(user_op_hash=user_op_hash, handle_ops_tx_hash=handle_ops, debited_usd=dollars(debit), reserved_usd=dollars(debit + 5),
                      delegation_tx_hash=delegation)
        execution = {"sender": address, "chain": agent["walletChain"], "user_op_hash": user_op_hash, "entry_point": ENTRY_POINT,
                     # the handleOps transaction is named the moment it is sent, with the status submitted (useroperation.go)
                     "handle_ops_tx_hash": handle_ops,
                     # `success` is a Go bool on UserOperationOutcome: the UserOperationEvent's flag once landed, false before it
                     "calls": ["approve", "swap"], "status": "landed" if landed else "submitted", "success": landed, "delegated": delegation is not None,
                     "reserved_usd": dollars(debit + 5)}
        if delegation:
            execution["delegation_tx_hash"] = delegation
        if landed:
            execution["debited_usd"] = dollars(debit)
            return self.tool_json(rpc_id, {"ticket_id": ticket["id"], "execution": execution, "message": "submitted through the platform's gas road"})
        # awaitOperation timed out: the Wallet answers with an error, and the operation it names was sent and may still land
        return self.tool_json(rpc_id, {"ticket_id": ticket["id"], "execution": execution, "reason": "confirmation_timeout",
                                       "message": "confirmation_timeout: the operation %s was sent and may still land; ask ticket_status" % user_op_hash},
                              error=True)

    def tool_wallet_ticket_status(self, rpc_id, agent, connection, args):
        ticket = self.tickets.get(str(args.get("ticket_id")))
        if ticket is None:
            return self.tool_text(rpc_id, "ticket_not_found", error=True)
        ticket["reads"] += 1
        # internal/ticket/manager.go: the operation's hashes from the moment it is sent; debited_usd once it landed; no status field
        view = {"id": ticket["id"], "state": ticket["state"], "user_op_hash": ticket.get("user_op_hash"), "reserved_usd": ticket.get("reserved_usd"),
                "handle_ops_tx_hash": ticket.get("handle_ops_tx_hash"), "fate": "consumed; what followed is in the audit journal"}
        if ticket.get("delegation_tx_hash"):
            view["delegation_tx_hash"] = ticket["delegation_tx_hash"]
        if ticket["reads"] >= self.lands_later and ticket.get("handle_ops_tx_hash"):
            view["debited_usd"] = ticket["debited_usd"]
        return self.tool_json(rpc_id, {"ticket": view})

    def token(self, form):
        self.token_forms.append(dict(form))
        return super().token(form)

    # -- Arbitrum One's JSON-RPC, read only ------------------------------------------------------------------------------
    def rpc(self, payload):
        method = payload.get("method")
        params = payload.get("params") or []
        rpc_id = payload.get("id")
        if self.rpc_error_on and method == self.rpc_error_on and (self.rpc_error_times is None or self.rpc_errors_given < self.rpc_error_times):
            self.rpc_errors_given += 1
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32005, "message": "limit exceeded: 25 requests per second"}}
        if method == "eth_getTransactionReceipt":
            key = str(params[0]).lower()
            self.receipt_reads[key] = self.receipt_reads.get(key, 0) + 1
            if self.receipt_reads[key] <= self.receipt_lag:
                return {"jsonrpc": "2.0", "id": rpc_id, "result": None}
            return {"jsonrpc": "2.0", "id": rpc_id, "result": self.receipts.get(key)}
        if method == "eth_blockNumber":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": hex(self.block)}
        if method == "eth_getLogs":
            query = params[0] if params else {}
            low = int(str(query.get("fromBlock") or "0x0"), 16)
            high = int(str(query.get("toBlock")), 16) if str(query.get("toBlock") or "latest") != "latest" else self.block
            wanted = query.get("topics") or []
            found = []
            for receipt in self.receipts.values():
                for log in receipt.get("logs") or []:
                    block = int(str(log.get("blockNumber") or receipt.get("blockNumber")), 16)
                    topics = [str(t).lower() for t in log.get("topics") or []]
                    if low <= block <= high and all(w is None or (i < len(topics) and topics[i] == str(w).lower()) for i, w in enumerate(wanted)):
                        found.append(dict(log))
            return {"jsonrpc": "2.0", "id": rpc_id, "result": found}
        if method == "eth_call":
            call = params[0] if params else {}
            if str(call.get("to") or "").lower() == P.ETH_USD_FEED["arbitrum"].lower():
                if call.get("data") == P.LATEST_ROUND_DATA:
                    answer = self.price_usd * 10 ** 8
                    return {"jsonrpc": "2.0", "id": rpc_id, "result": "0x" + word(1) + word(answer) + word(1) + word(1) + word(1)}
                if call.get("data") == P.FEED_DECIMALS:
                    return {"jsonrpc": "2.0", "id": rpc_id, "result": "0x" + word(8)}
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": "execution reverted"}}
        return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "the method %s does not exist" % method}}
