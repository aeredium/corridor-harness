"""
THE DOUBLES THE REHEARSAL IS PROVED AGAINST (Spec P1d): the Police and the Wallet behind the connector's
relay as one MCP session, the access platform's gas ledger and gas roads over HTTP, and the chain's public
RPC. Each stands in for a real service and is at least as strict as it: it refuses what the service refuses,
in the service's own sentence and status, and answers in the service's own shape —

  the Police        check_action's ALLOW receipt with `gas_account` and `gas_low` (mcp-police 1.14.0, Spec 25);
  the Wallet        wallet_status with the key record (`account`, Spec 66 §1) and `gas_account` (§3); get_balances
                    with the tokens where Spec 49 puts them; the desk's 402 `gas_account_short` in U3's sentence,
                    relayed as the MCP door relays an HTTP refusal (the body as the text, isError); the ticket; the
                    submit answer's `execution.user_operation` with the userOpHash, the delegation where the key was
                    delegated first (Spec 154 §5) and the sponsor's handleOps (stablepro-agent-server, Spec 66 §2);
  the platform      the ledger in cents (internal/gas/ledger.go), the admin credit road under the admin key with
                    adminAuth's three 401 sentences and `deduped` (Spec 154 §1, gas_handlers.go), GET /v1/gas-account
                    with `account_id` and `recent_lines`, GET /v1/gas/operations/{hash} under the account's own key
                    and 404 for another account's, the quote's reservation as Spec 154c §2 computes it and U3's
                    refusal naming it, the settlement as 154c §3 debits it — gas from the receipt at the recorded
                    price, service rounded half up and at least a cent, one line whose words are 154c's — and the
                    read-back of 154c §4;
  the chain         eth_getTransactionReceipt for the transactions the platform sent, with gasUsed and effectiveGasPrice.

Every secret here is a sentinel issued at construction, and no string in this file begins with the platform's
prefixes: they are read from corridor_harness, where the platform's own words live.
"""
import json
import os
import re
import secrets
import sys
import urllib.parse
import uuid
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import tables as T  # noqa: E402

CHAIN = "arbitrum"
CHAIN_ID = 42161
WALLET = "0x2222222222222222222222222222222222222222"       # the sandbox wallet's address, as its key record states it
WALLET_ID = "w-sandbox"
KEY_ID = "key-sandbox-7cfb99c110c9"
ACCOUNT_ID = "acct-sandbox-1"                                # the harness's owner's platform account
OTHER_WALLET = "0x3333333333333333333333333333333333333333"  # another wallet of the same owner
USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
ENTRY_POINT = "0x0000000071727De22E5E9d8BAf0edAc6f37da032"
PAYMASTER = "0xF3655d4d8B1C7Ed0ae1C33A8b6F2A6f5A7C0800C"
SPONSOR = "0x4444444444444444444444444444444444444444"
IMPLEMENTATION = "0x0562346e1291fd9B922991A249FaaBD0bFEa325f"
POLICY_HASH = "0x5237c7e1b0c4f1a9d8e3b26a5f470c91d2846ebb73f5a0c1e94d6b28fa310577"
PLATFORM = "https://platform.test"
RPC_URL = T.REHEARSAL_RPC[CHAIN].url

# The platform's own sentences (internal/api/middleware.go adminAuth; gas_handlers.go; internal/gas/errors.go), word for word.
ADMIN_MISSING = "missing or malformed Authorization header"
ADMIN_FORMAT = "invalid admin key format"
ADMIN_INVALID = "invalid admin key"
CREDENTIAL_FORMAT = "invalid credential format"
UNAUTHENTICATED = "unauthenticated"
SERVICE_REFUSAL = ("this road answers an account's own credential or an agent's pact credential; a service identity reads "
                   "GET /v1/gas/operations/{userOpHash}, and the credit road admits a door key (AAP_GAS_DOOR_KEYS) alone")
REASON_REQUIRED = "reason is required on an admin credit: the road exists for the sandbox and for goodwill, and the row says which"
TOP_UP = "Top up US$10.00 or more."
BUY_GAS = "Ask your owner to buy gas on AER Connect."  # the Wallet's desk's tail (account_road.go buyGasOnAERConnect)


def sentinel(tag: str) -> str:
    return "%s-sentinel-%s" % (tag, secrets.token_hex(12))


def hex_hash() -> str:
    return "0x" + secrets.token_hex(32)


def round_half_up(numerator: int, denominator: int) -> int:
    return (2 * numerator + denominator) // (2 * denominator)


def ceil_div(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


def insufficient_gas_sentence(available_cents: int, reservation_cents: int, kind: str) -> str:
    """U3's refusal as the platform writes it (errors.go InsufficientGasSentence), the figure the reservation (Spec 154c §2)."""
    return "Your gas account holds %s. This %s needs at most %s of gas. Nothing was sent. %s" % (
        T.format_usd_cents(available_cents), kind, T.format_usd_cents(reservation_cents), TOP_UP)


def debit_words(total: int, gas: int, service: int, bps: int) -> str:
    """Spec 154c §3's one line: "gas and service, US$<sum>: gas US$<gas>, service US$<service> (10%), paid in advance from your gas account"."""
    percent = ("%g" % (bps / 100.0)).rstrip("0").rstrip(".") if bps % 100 else str(bps // 100)
    return "gas and service, %s: gas %s, service %s (%s%%), paid in advance from your gas account" % (
        T.format_usd_cents(total), T.format_usd_cents(gas), T.format_usd_cents(service), percent)


class PlatformRefusal(Exception):
    def __init__(self, status: int, code: str, sentence: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(sentence)
        self.status, self.code, self.sentence, self.detail = status, code, sentence, detail or {}


class PlatformDouble:
    """The access platform's gas ledger and gas roads (Specs 154, 154b, 154c), in process for the Wallet double and over HTTP for the harness."""

    def __init__(self, account_id: str = ACCOUNT_ID, wallet: str = WALLET, chain: str = CHAIN, ceiling_cents: int = 30,
                 margin_bps: int = 1000, price_cents_per_ether: int = 200000, gas_used: int = 100000, effective_gas_price: int = 10 ** 9,
                 delegation_gas_used: int = 50000, delegation_ceiling_cents: int = 15, lands_after: int = 2, initial_balance_cents: int = 0,
                 **knobs: Any):
        self.admin_key = h.ADMIN_KEY_PREFIX + sentinel("admin")
        self.account_key = h.ACCOUNT_KEY_PREFIX + sentinel("account")
        self.account_id = account_id
        self.wallet = wallet
        self.chain = chain
        self.ceiling_cents = ceiling_cents
        self.margin_bps = margin_bps
        self.price_cents_per_ether = price_cents_per_ether
        self.gas_used = gas_used
        self.effective_gas_price = effective_gas_price
        self.delegation_gas_used = delegation_gas_used
        self.delegation_ceiling_cents = delegation_ceiling_cents
        self.lands_after = lands_after
        self.knobs = knobs
        self.accounts = {account_id}
        self.lines: List[Dict[str, Any]] = []
        self.operations: Dict[str, Dict[str, Any]] = {}
        self.polls: Dict[str, int] = {}
        self.requests: List[Dict[str, Any]] = []
        self.last_reservation: Dict[str, int] = {}
        if initial_balance_cents:
            self.credit(account_id, initial_balance_cents, "seed:" + uuid.uuid4().hex, "the balance before this run", "admin")
        if knobs.get("open_operation"):
            row = self.new_operation(self.knobs.get("open_sender") or wallet, "operation", "payment", self.ceiling_cents)
            self.reserve(row)
            row["status"] = "submitted"
            row["transaction_hash"] = hex_hash()
            self.operations[row["user_op_hash"]] = row

    # -- the ledger (internal/gas/ledger.go) -------------------------------------------------------
    def balance(self, account_id: str) -> Dict[str, int]:
        mine = [line for line in self.lines if line["account_id"] == account_id]
        credits = sum(line["amount_usd_cents"] for line in mine if line["kind"] == "credit")
        debits = sum(line["amount_usd_cents"] for line in mine if line["kind"] == "debit")
        reserved = sum(line["amount_usd_cents"] for line in mine if line["kind"] == "reservation" and line.get("released_at") is None)
        return {"balance_usd_cents": credits - debits, "reserved_usd_cents": reserved, "available_usd_cents": credits - debits - reserved}

    def describe_balance(self, account_id: str) -> Dict[str, Any]:
        figures = self.balance(account_id)
        out: Dict[str, Any] = dict(figures)
        out.update({"balance": T.format_usd_cents(figures["balance_usd_cents"]), "reserved": T.format_usd_cents(figures["reserved_usd_cents"]),
                    "available": T.format_usd_cents(figures["available_usd_cents"])})
        return out

    def _line(self, account_id: str, kind: str, cents: int, key: str, **extra: Any) -> Dict[str, Any]:
        line = {"id": str(uuid.uuid4()), "account_id": account_id, "kind": kind, "amount_usd_cents": cents, "amount": T.format_usd_cents(cents),
                "idempotency_key": key, "created_at": "2026-09-24T05:20:00Z"}
        line.update(extra)
        self.lines.append(line)
        return line

    def credit(self, account_id: str, cents: int, key: str, reason: str, source: str) -> Tuple[Dict[str, Any], bool]:
        existing = next((line for line in self.lines if line["idempotency_key"] == key), None)
        if existing is not None:
            return existing, False
        return self._line(account_id, "credit", cents, key, source=source, reason=reason, actor="admin:bearer",
                          words="credit, %s, %s" % (T.format_usd_cents(cents), reason)), True

    # -- the operations (quote.go, submit.go, delegate.go, settle.go, operations.go) --------------------
    def new_operation(self, sender: str, kind: str, purpose: str, ceiling_cents: int) -> Dict[str, Any]:
        reservation = ceiling_cents + max(1, ceil_div(ceiling_cents * self.margin_bps, 10000)) if self.margin_bps and ceiling_cents > 0 else ceiling_cents
        row: Dict[str, Any] = {
            "id": str(uuid.uuid4()), "account_id": self.account_id, "chain": self.chain, "chain_id": CHAIN_ID, "kind": kind, "status": "quoted",
            "user_op_hash": hex_hash() if kind == "operation" else "", "sender": sender, "purpose": purpose, "entry_point": ENTRY_POINT,
            "paymaster": PAYMASTER, "sponsor": SPONSOR, "implementation": IMPLEMENTATION,
            "reservation_usd_cents": reservation, "ceiling_wei": str(ceiling_cents * 10 ** 18 // self.price_cents_per_ether),
            "price_usd": "%d.%02d" % (self.price_cents_per_ether // 100, self.price_cents_per_ether % 100),
            "quoted_at": "2026-09-24T05:20:01Z", "valid_after": 0, "valid_until": 1790000000, "polls": 0,
            "_ceiling_cents": ceiling_cents, "_bps": self.margin_bps,
        }
        return row

    def reserve(self, row: Dict[str, Any]) -> None:
        line = self._line(row["account_id"], "reservation", row["reservation_usd_cents"], "reserve:" + row["id"], chain=row["chain"], operation_id=row["id"],
                          user_op_hash=row["user_op_hash"], transaction_hash=row.get("transaction_hash", ""), released_at=None,
                          words="gas reserved, at most %s, for this %s" % (T.format_usd_cents(row["reservation_usd_cents"]), row["purpose"]))
        row["reservation_line_id"] = line["id"]
        self.last_reservation[row["chain"]] = row["reservation_usd_cents"]

    def quote(self, sender: str, kind: str) -> Dict[str, Any]:
        """POST /v1/gas/quote as the Wallet asks it: the reservation checked against what is available, U3's refusal naming the reservation."""
        purpose = "payment" if kind in ("payment", "transfer") else "trade"
        row = self.new_operation(sender, "operation", purpose, self.ceiling_cents)
        available = self.balance(self.account_id)["available_usd_cents"]
        if available < row["reservation_usd_cents"]:
            raise PlatformRefusal(402, "insufficient_gas", insufficient_gas_sentence(available, row["reservation_usd_cents"], purpose),
                                  {"available_usd_cents": available, "ceiling_usd_cents": row["reservation_usd_cents"]})
        self.reserve(row)
        self.operations[row["user_op_hash"]] = row
        return row

    def delegate(self, sender: str) -> Dict[str, Any]:
        """The delegation the platform sends first where the key is undelegated (Spec 154 §5): its own operation row, keyed by its transaction hash."""
        row = self.new_operation(sender, "delegation", "delegation", self.delegation_ceiling_cents)
        row["transaction_hash"] = hex_hash()
        self.reserve(row)
        row["status"] = "submitted"
        row["submitted_at"] = "2026-09-24T05:20:02Z"
        self.operations[row["transaction_hash"]] = row
        return row

    def submit(self, user_op_hash: str) -> Dict[str, Any]:
        row = self.operations[user_op_hash]
        if row["status"] != "quoted":
            raise PlatformRefusal(409, "conflict", "the operation %s is %s and admits no submit" % (user_op_hash, row["status"]))
        row["status"] = "submitted"
        row["transaction_hash"] = hex_hash()
        row["submitted_at"] = "2026-09-24T05:20:03Z"
        return row

    def settle(self, row: Dict[str, Any]) -> None:
        """Spec 154c §3: gas from the receipt at the recorded price, service rounded half up and at least a cent, one line of gas + service."""
        gas_used = self.delegation_gas_used if row["kind"] == "delegation" else self.gas_used
        cost_wei = gas_used * self.effective_gas_price
        gas_exact_num, gas_exact_den = cost_wei * self.price_cents_per_ether, 10 ** 18
        gas = round_half_up(gas_exact_num, gas_exact_den)
        service = round_half_up(gas_exact_num * row["_bps"], gas_exact_den * 10000) if row["_bps"] else 0
        if row["_bps"] and gas_exact_num > 0:
            service = max(1, service)
        reported_gas = gas + int(self.knobs.get("gas_off_cents", 0))
        reported_service = service + int(self.knobs.get("service_off_cents", 0))
        total = reported_gas + reported_service + int(self.knobs.get("total_off_cents", 0))
        words = self.knobs.get("words") or debit_words(total, reported_gas, reported_service, row["_bps"])
        row.update({"gas_used": str(gas_used), "effective_gas_price": str(self.effective_gas_price), "actual_cost_wei": str(cost_wei),
                    "settle_price_usd": row["price_usd"], "block_number": "384000001", "settled_at": "2026-09-24T05:20:09Z",
                    "debit_usd_cents": total, "gas_usd_cents": reported_gas, "service_usd_cents": reported_service, "total_usd_cents": total,
                    "margin_bps": row["_bps"], "native_usd_cents_per_ether": self.price_cents_per_ether, "words": words})
        if "reservation_report_cents" in self.knobs:
            row["reservation_usd_cents"] = int(self.knobs["reservation_report_cents"])
        debited = total + int(self.knobs.get("debit_gap_cents", 0))
        self._line(row["account_id"], "debit", debited, "debit:" + row["id"], chain=row["chain"], operation_id=row["id"], user_op_hash=row["user_op_hash"],
                   transaction_hash=row["transaction_hash"], words=words)
        if not self.knobs.get("hold_reservation"):
            for line in self.lines:
                if line["id"] == row.get("reservation_line_id"):
                    line["released_at"] = row["settled_at"]
        if self.knobs.get("revert"):
            row["status"] = "reverted"
            row["success"] = False
            row["revert_reason"] = "execution reverted"
            row["refusal"] = "the %s transaction %s reverted on chain; the gas it burned, %s, was debited all the same" % (
                row["kind"], row["transaction_hash"], T.format_usd_cents(total))
        else:
            row["status"] = "landed"
            row["success"] = True

    def read(self, op_hash: str) -> Optional[Dict[str, Any]]:
        row = self.operations.get(op_hash.lower())
        if row is None:
            return None
        if row["status"] == "submitted" and not self.knobs.get("never_lands"):
            self.polls[op_hash] = self.polls.get(op_hash, 0) + 1
            if self.polls[op_hash] >= self.lands_after:
                self.settle(row)
        return row

    def view(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """OperationView (operations.go): the row with every dollar figure beside its cents; the 154c fields once settled."""
        out = {k: v for k, v in row.items() if not k.startswith("_") and k != "polls" and v not in ("", None)}
        out["reservation"] = T.format_usd_cents(row["reservation_usd_cents"])
        if row.get("debit_usd_cents") is not None:
            out["debit"] = T.format_usd_cents(row["debit_usd_cents"])
        out["price"] = "US$%s per coin" % row["price_usd"]
        return out

    def account_view(self, account_id: str) -> Dict[str, Any]:
        figures = self.describe_balance(account_id)
        mine = [line for line in self.lines if line["account_id"] == account_id][-25:]
        view = dict(figures)
        view.update({"account_id": account_id, "low": figures["available_usd_cents"] < 100, "low_balance_usd_cents": 100,
                     "minimum_top_up_usd_cents": 1000, "top_up": "Top up US$10.00 or more, by card, on the account you pay with.",
                     "low_pots": False, "low_pot_chains": [], "operations_settled": len([l for l in mine if l["kind"] == "debit"]),
                     "recent_lines": list(reversed(mine))})
        return view

    def receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """What the chain says about a transaction the platform sent: the receipt the settle worker read."""
        row = next((r for r in self.operations.values() if str(r.get("transaction_hash", "")).lower() == tx_hash.lower()), None)
        if row is None or row["status"] not in ("landed", "reverted"):
            return None
        status = "0x0" if (row["status"] == "reverted" or self.knobs.get("receipt_status_reverted")) else "0x1"
        return {"transactionHash": row["transaction_hash"], "blockNumber": hex(int(row["block_number"])), "status": status,
                "gasUsed": hex(int(row["gas_used"])), "effectiveGasPrice": hex(int(row["effective_gas_price"])), "from": SPONSOR,
                "to": ENTRY_POINT if row["kind"] == "operation" else row["sender"], "logs": []}

    # -- the roads over HTTP (router.go, gas_handlers.go, middleware.go) ------------------------------
    def __call__(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, body: Optional[bytes] = None, timeout: Any = None) -> h.HttpAnswer:
        parsed = urllib.parse.urlparse(url)
        headers = {k.lower(): v for k, v in (headers or {}).items()}
        raw_body = body.decode("utf-8") if body else ""
        self.requests.append({"method": method, "path": parsed.path, "headers": headers, "body": raw_body})
        if self.knobs.get("down"):
            raise h.Unreachable("%s %s: [Errno 61] Connection refused" % (method, url))
        bearer = headers.get("authorization", "")
        bearer = bearer[len("Bearer "):].strip() if bearer.startswith("Bearer ") else ""
        m = re.match(r"^/v1/admin/accounts/([^/]+)/gas-account/credits$", parsed.path)
        if m and method == "POST":
            return self.admin_credit(m.group(1), headers.get("authorization", ""), raw_body)
        if parsed.path == T.GAS_ACCOUNT_ROUTE and method == "GET":
            caller = self.gas_caller(bearer, admit_service=False)
            if isinstance(caller, h.HttpAnswer):
                return caller
            return self.json(200, self.account_view(caller))
        m = re.match(r"^/v1/gas/operations/([^/]+)$", parsed.path)
        if m and method == "GET":
            if self.knobs.get("refuse_account_credential") and bearer.startswith(h.ACCOUNT_KEY_PREFIX):
                return self.json(401, {"error": CREDENTIAL_FORMAT})
            caller = self.gas_caller(bearer, admit_service=True)
            if isinstance(caller, h.HttpAnswer):
                return caller
            op_hash = m.group(1).lower()
            if not (op_hash.startswith("0x") and len(op_hash) == 66):
                return self.json(400, {"error": "%r is not a 32-byte hash" % m.group(1), "code": "validation"})
            row = self.read(op_hash)
            if row is None or (caller != "" and row["account_id"] != caller):
                return self.json(404, {"error": "not found: no operation with hash %s" % op_hash})
            return self.json(200, self.view(row))
        return self.json(404, {"error": "not found"})

    def gas_caller(self, bearer: str, admit_service: bool) -> Any:
        """gasCredentialAuth: an account key is the account's own; a service identity reads operations alone; anything else is refused by shape."""
        if not bearer:
            return self.json(401, {"error": UNAUTHENTICATED})
        if bearer.startswith(h.ACCOUNT_KEY_PREFIX):
            if bearer != self.account_key:
                return self.json(401, {"error": "invalid account key"})
            return self.account_id
        if bearer.startswith(h.ADMIN_KEY_PREFIX):
            if not admit_service:
                return self.json(403, {"error": SERVICE_REFUSAL})
            return "" if bearer == self.admin_key else self.json(401, {"error": ADMIN_INVALID})
        return self.json(401, {"error": CREDENTIAL_FORMAT})

    def admin_credit(self, account_id: str, authorization: str, raw_body: str) -> h.HttpAnswer:
        if not authorization.startswith("Bearer ") or not authorization[len("Bearer "):].strip():
            return self.json(401, {"error": ADMIN_MISSING})
        bearer = authorization[len("Bearer "):].strip()
        if not bearer.startswith(h.ADMIN_KEY_PREFIX):
            return self.json(401, {"error": ADMIN_FORMAT})
        if bearer != self.admin_key:
            return self.json(401, {"error": ADMIN_INVALID})
        if account_id not in self.accounts:
            return self.json(404, {"error": "not found: no account %s" % account_id})
        try:
            body = json.loads(raw_body) if raw_body else {}
        except ValueError as err:
            return self.json(400, {"error": str(err)})
        unknown = [k for k in body if k not in ("account_id", "amount_usd_cents", "stripe_event_id", "idempotency_key", "reason", "reference")]
        if unknown:
            return self.json(400, {"error": 'json: unknown field "%s"' % unknown[0]})
        reason = str(body.get("reason") or "").strip()
        if not reason:
            return self.json(400, {"error": REASON_REQUIRED})
        amount = body.get("amount_usd_cents")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            return self.json(400, {"error": "amount_usd_cents must be a positive integer of cents", "code": "validation"})
        key = str(body.get("idempotency_key") or "").strip() or ("admin:" + str(uuid.uuid4()))
        line, created = self.credit(account_id, amount, key, reason, "admin")
        if self.knobs.get("deduped_credit"):
            created = False
        answer: Dict[str, Any] = {"line": line, "deduped": not created, "below_minimum": amount < 1000, "minimum_top_up_usd_cents": 1000,
                                  "balance": self.describe_balance(account_id)}
        if answer["below_minimum"]:
            answer["note"] = "%s was credited; the minimum top-up is US$10.00, and a top-up below it is accepted and recorded as it came" % T.format_usd_cents(amount)
        return self.json(201 if created else 200, answer)

    @staticmethod
    def json(status: int, body: Any) -> h.HttpAnswer:
        return h.HttpAnswer(status, {"Content-Type": "application/json"}, json.dumps(body, ensure_ascii=False), 3)


class RpcDouble:
    """The chain's public RPC: eth_getTransactionReceipt for what the platform's sponsor sent, and nothing else."""

    def __init__(self, platform: PlatformDouble):
        self.platform = platform
        self.requests: List[Dict[str, Any]] = []

    def __call__(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, body: Optional[bytes] = None, timeout: Any = None) -> h.HttpAnswer:
        payload = json.loads(body.decode("utf-8")) if body else {}
        self.requests.append(payload)
        if payload.get("method") == "eth_getTransactionReceipt":
            result = self.platform.receipt(str(payload["params"][0]))
            return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}), 2)
        return h.HttpAnswer(200, {}, json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32601, "message": "the method %s does not exist/is not available" % payload.get("method")}}), 2)


def router(platform: PlatformDouble, rpc: RpcDouble):
    """http_request as the tests hand it to the harness: the platform at its base URL, the chain at the pinned RPC, and nothing else."""
    def route(method: str, url: str, headers: Optional[Dict[str, str]] = None, body: Optional[bytes] = None, timeout: Any = None) -> h.HttpAnswer:
        if url.startswith(PLATFORM):
            return platform(method, url, headers, body, timeout)
        if url == RPC_URL:
            return rpc(method, url, headers, body, timeout)
        raise AssertionError("the rehearsal reached for %s %s" % (method, url))
    return route


def mcp_answer(payload: Any, is_error: bool = False, structured: Any = None) -> h.McpAnswer:
    """One JSON-RPC answer as the connector relays a door's: the body as the text, isError where the door's HTTP status was not 2xx."""
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    result: Dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if structured is not None:
        result["structuredContent"] = structured
    if is_error:
        result["isError"] = True
    body = {"jsonrpc": "2.0", "id": 1, "result": result}
    return h.McpAnswer(200, body, json.dumps(body, ensure_ascii=False), 7)


class CorridorDouble:
    """The Police and the Wallet behind AER Connect's relay, as the one MCP session the rehearsal speaks to."""

    POLICE_PROPS = {"action_kind": {}, "chain": {}, "asset_symbol": {}, "to_address": {},
                    "amount_usd_cents": {"description": "The amount in US cents."},
                    "amount_usd": {"description": "NOT ACCEPTED. Present only so an amount sent in dollars is refused rather than silently ignored."},
                    "child_wallet_id": {}, "to_asset": {}, "venue": {}, "contract_address": {}, "to_chain": {}}
    WALLET_PROPS = {"wallet_id": {}, "action": {}, "amount_usd": {}, "to_address": {}, "chain": {}, "asset": {}, "police_receipt": {}, "ticket_id": {}}

    def __init__(self, platform: PlatformDouble, wallet: str = WALLET, live_address: Optional[str] = None, police: str = "allow",
                 usdc_minor: int = 1000000, delegate_first: bool = False, chain: str = CHAIN, **knobs: Any):
        self.platform = platform
        self.wallet = wallet
        self.live_address = live_address or wallet
        self.police = police
        self.usdc_minor = usdc_minor
        self.delegate_first = delegate_first
        self.chain = chain
        self.knobs = knobs
        self.bearer = sentinel("bearer")                 # the agent's bearer, as the session presents it on every call
        self.secrets_seen: List[str] = [self.bearer]
        self.calls: List[Tuple[str, str, Dict[str, Any]]] = []
        self.tickets: Dict[str, Dict[str, Any]] = {}
        self.receipts: Dict[str, str] = {}
        self.delegated = False
        self.tools = {
            h.MY_AGENT_TOOL: {"name": h.MY_AGENT_TOOL, "inputSchema": {"properties": {}}},
            h.GUIDE_TOOL: {"name": h.GUIDE_TOOL, "inputSchema": {"properties": {"question": {}}}},
            "police.check_action": {"name": "police.check_action", "inputSchema": {"properties": self.POLICE_PROPS, "required": ["action_kind", "amount_usd_cents"]}},
            "wallet.wallet_status": {"name": "wallet.wallet_status", "inputSchema": {"properties": {"wallet_id": {}}, "required": ["wallet_id"]}},
            "wallet.get_address": {"name": "wallet.get_address", "inputSchema": {"properties": {"wallet_id": {}}}},
            "wallet.get_balances": {"name": "wallet.get_balances", "inputSchema": {"properties": {"wallet_id": {}}, "required": ["wallet_id"]}},
            "wallet.build_transaction": {"name": "wallet.build_transaction", "inputSchema": {"properties": self.WALLET_PROPS, "required": ["wallet_id", "action"]}},
            "wallet.submit_transaction": {"name": "wallet.submit_transaction", "inputSchema": {"properties": {"wallet_id": {}, "ticket_id": {}}, "required": ["wallet_id", "ticket_id"]}},
            "wallet.ticket_status": {"name": "wallet.ticket_status", "inputSchema": {"properties": {"wallet_id": {}, "ticket_id": {}}}},
        }

    # -- the session -------------------------------------------------------------------------------
    def initialize(self, test_id: str) -> h.McpAnswer:
        return h.McpAnswer(200, {"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {"name": "aer-connect", "version": "double"}}}, "{}", 5)

    def tools_list(self, test_id: str) -> List[Dict[str, Any]]:
        return list(self.tools.values())

    def schema_of(self, tool: str) -> Optional[Dict[str, Any]]:
        listed = self.tools.get(tool)
        return listed["inputSchema"] if listed else None

    def properties_of(self, tool: str) -> Optional[Dict[str, Any]]:
        listed = self.tools.get(tool)
        return listed["inputSchema"]["properties"] if listed else None

    # -- what the Wallet says (Spec 66) --------------------------------------------------------------
    def gas_line(self) -> Dict[str, Any]:
        figures = self.platform.balance(self.platform.account_id)
        if self.knobs.get("gas_unreadable"):
            return {"read": False, "source": "GET /v1/gas-account", "said": "the access platform did not answer GET /v1/gas-account: HTTP 503: not now"}
        return {"read": True, "source": "GET /v1/gas-account", "available": T.format_usd_cents(figures["available_usd_cents"]),
                "balance": T.format_usd_cents(figures["balance_usd_cents"]), "reserved": T.format_usd_cents(figures["reserved_usd_cents"]),
                "low": figures["available_usd_cents"] < 100, "minimum_top_up": "US$10.00"}

    def account_view(self) -> Dict[str, Any]:
        delegated_on = [self.chain] if self.delegated else []
        out: Dict[str, Any] = {"road": "key_delegated", "address": self.live_address, "chain": self.chain, "key_id": KEY_ID,
                               "delegation": [{"chain": self.chain, "read": True, "delegated": self.delegated, "implementation": IMPLEMENTATION.lower()}],
                               "delegated_on": delegated_on,
                               "said": ("this wallet is delegated on %s" % self.chain) if self.delegated else
                                       "this wallet is delegated on no chain yet; its first operation on %s will delegate it" % self.chain}
        if self.live_address.lower() != self.wallet.lower():
            out["retired_addresses"] = [self.wallet]
            out["correction"] = {"from": self.wallet, "to": self.live_address, "at": "2026-09-23T14:15:00Z",
                                 "said": "the key signed from %s, not %s, the address this wallet was told; nothing was sent; the wallet's address is corrected to %s"
                                         % (self.live_address, self.wallet, self.live_address)}
        return out

    def status_answer(self) -> Dict[str, Any]:
        return {"wallet_id": WALLET_ID, "address": self.live_address, "chain": self.chain, "role_id": "payer.v1",
                "rails": [{"chain": self.chain, "chain_id": CHAIN_ID, "live": True}],
                "pact": {"id": "p-sandbox", "policy_hash": POLICY_HASH, "state": "active", "policy_generation": 3},
                "account": self.account_view(), "gas_account": self.gas_line()}

    def balances_answer(self) -> Dict[str, Any]:
        raw = str(self.usdc_minor)
        amount = h.format_units(self.usdc_minor, 6)
        usd = "%d.%02d" % (self.usdc_minor // 10 ** 6, (self.usdc_minor % 10 ** 6) // 10 ** 4)
        return {"wallet_id": WALLET_ID, "address": self.live_address, "chain": self.chain,
                "tokens": {"balances": [{"asset": "USDC", "chain": self.chain, "contract": USDC, "decimals": 6, "raw": raw, "amount": amount,
                                         "available": True, "source": "chain", "usd": usd}],
                           "chains": [self.chain], "road": "every verified stablecoin row this door holds for %s" % self.chain,
                           "said": "this wallet holds US$%s of USDC on %s" % (usd, self.chain)},
                "pact_budget": {"id": "p-sandbox", "policy_hash": POLICY_HASH, "spent_usd": 0},
                "account": self.account_view(), "gas_account": self.gas_line(),
                "holds": [{"asset": "USDC", "chain": self.chain, "usd": usd}], "said": "this wallet holds US$%s of USDC on %s" % (usd, self.chain)}

    def my_agent_answer(self) -> Dict[str, Any]:
        figures = self.platform.balance(self.platform.account_id)
        return {"source": "aer-connect", "agent": {"name": "Harness Payer", "roleId": "payer.v1"}, "connection": {"rank": "agent", "standing": "paid"},
                "wallet": {"id": WALLET_ID, "address": self.wallet, "chain": self.chain}, "fundingWallet": {"address": self.wallet},
                "caps": {"maxPerTxUsdCents": 2000, "maxPerDayUsdCents": 10000, "said": "per trade US$20.00, per day US$100.00"},
                "gas_account": T.format_usd_cents(figures["available_usd_cents"]),
                "gasAccount": {"availableUsdCents": figures["available_usd_cents"], "low": figures["available_usd_cents"] < 100, "unreadable": None},
                "said": "You are connected as Harness Payer, a Payer."}

    # -- the Police (mcp-police 1.14.0, Spec 25) -----------------------------------------------------
    def check_action_answer(self, args: Dict[str, Any]) -> h.McpAnswer:
        figures = self.platform.balance(self.platform.account_id)
        gas_fields = {"gas_account": T.format_usd_cents(figures["available_usd_cents"]), "gas_low": figures["available_usd_cents"] < 100}
        judged = {"source": "pact", "pact_id": "p-sandbox", "policy_hash": POLICY_HASH, "policy_active": True}
        if self.police != "allow":
            structured = {"verdict": "deny", "decision": "deny", "reason": "denied", "context_incomplete": False, "judged": judged,
                          "sentence": "The destination %s is not on this agent’s list" % args.get("to_address"), "receipt": {"issued": False, "token": None,
                          "not_issued_because": "denied"}}
            structured.update(gas_fields)
            text = "DENY. The destination %s is not on this agent’s list.\n\nPRE-FLIGHT RECEIPT: none issued — denied\n\ngas_account: %s\ngas_low: %s\n\nMetering: counted." % (
                args.get("to_address"), gas_fields["gas_account"], str(gas_fields["gas_low"]).lower())
            return mcp_answer(text, structured=structured)
        token = "police-receipt-" + secrets.token_hex(16)
        self.receipts[token] = args.get("child_wallet_id", "")
        structured = {"verdict": "allow", "decision": "allow", "reason": "allowed", "context_incomplete": False, "judged": judged, "policy_hash": POLICY_HASH,
                      "receipt": {"issued": True, "token": token, "nonce": "n-" + secrets.token_hex(4), "expires_at": "2026-09-24T05:25:00Z", "not_issued_because": None}}
        structured.update(gas_fields)
        text = ("ALLOW. The action is within the pact.\n\nPRE-FLIGHT RECEIPT: issued, valid until 2026-09-24T05:25:00Z. Its value is: %s — pass it exactly as the "
                "`police_receipt` argument of the MCP Wallet's build_transaction.\n\ngas_account: %s\ngas_low: %s\n\nMetering: counted.") % (
            token, gas_fields["gas_account"], str(gas_fields["gas_low"]).lower())
        return mcp_answer(text, structured=structured)

    # -- the Wallet's desk, build and submit (Spec 66 §2, §3) ----------------------------------------
    def build_answer(self, args: Dict[str, Any]) -> h.McpAnswer:
        if "police_receipt" not in args:
            return mcp_answer("receipt_missing: This action carries no pre-flight receipt. Nobody enters but through the Police.", is_error=True)
        if args.get("police_receipt") not in self.receipts:
            return mcp_answer({"error": "receipt_invalid", "reason_code": "receipt_invalid", "message": "the pre-flight receipt is not one MCP Police issued for this wallet"}, is_error=True)
        if args.get("action") != "transfer_stable":
            return mcp_answer({"error": "not_wired", "message": "this door trades directly on uniswap_v3, pancakeswap_v3, curve, best_direct"}, is_error=True)
        kind = "transfer"
        if self.knobs.get("desk_says_holds") is not None:
            # A desk whose first figure is not the balance the harness read: the sentence's arithmetic is judged, not trusted.
            sentence = "Your gas account holds %s. This %s needs at most US$1.00 of gas. Nothing was sent. %s" % (self.knobs["desk_says_holds"], kind, BUY_GAS)
            return self.desk_refusal(sentence)
        if self.delegate_first and not self.delegated:
            # Spec 154 §5: the sender is undelegated at its first quote, so the platform delegates it first, and the operation follows.
            available = self.platform.balance(self.platform.account_id)["available_usd_cents"]
            if available < self.platform.delegation_ceiling_cents and not self.knobs.get("mint_at_zero"):
                return self.desk_refusal(insufficient_gas_sentence(available, self.platform.delegation_ceiling_cents, "payment"))
        try:
            row = self.platform.quote(self.live_address, kind)
        except PlatformRefusal as refusal:
            if self.knobs.get("mint_at_zero"):
                row = self.platform.new_operation(self.live_address, "operation", "payment", self.platform.ceiling_cents)
                self.platform.operations[row["user_op_hash"]] = row
            else:
                # The platform's own U3 refusal at the quote, relayed verbatim under the desk's code (spec 66 §3).
                return self.desk_refusal(refusal.sentence)
        delegation = None
        if self.delegate_first and not self.delegated:
            delegation = self.platform.delegate(self.live_address)
            self.delegated = True
        ticket_id = "t-" + secrets.token_hex(6)
        self.tickets[ticket_id] = {"row": row, "delegation": delegation}
        ticket = {"id": ticket_id, "pact_id": "p-sandbox", "request_digest": "0x" + secrets.token_hex(32), "policy_hash": POLICY_HASH,
                  "expires_at": "2026-09-24T05:30:00Z", "created_at": "2026-09-24T05:20:02Z", "leg_count": 1, "function": "transfer",
                  "simulation_passed": True, "oracle_check_passed": True}
        return mcp_answer({"ticket": ticket, "policy": {"outcome": "allow", "policy_hash": POLICY_HASH}, "pact_id": "p-sandbox", "gas_account": self.gas_line()})

    def desk_refusal(self, sentence: str) -> h.McpAnswer:
        body = {"error": "gas_account_short", "reason_code": "gas_account_short", "message": sentence, "chain": self.chain, "kind": "transfer",
                "gas_account": self.gas_line(), "ticket": None}
        return mcp_answer(body, is_error=True)

    def submit_answer(self, args: Dict[str, Any]) -> h.McpAnswer:
        ticket = self.tickets.get(str(args.get("ticket_id")))
        if ticket is None:
            return mcp_answer({"error": "ticket_not_found", "reason_code": "ticket_not_found", "message": "no ticket %s is minted for this wallet" % args.get("ticket_id")}, is_error=True)
        row = ticket["row"]
        try:
            self.platform.submit(row["user_op_hash"])
        except PlatformRefusal as refusal:
            return mcp_answer({"error": "platform_refused", "reason_code": "platform_refused", "message": refusal.sentence, "gas_account": self.gas_line()}, is_error=True)
        delegation = ticket["delegation"]
        operation = {"sender": self.live_address, "chain": self.chain, "user_op_hash": row["user_op_hash"], "entry_point": ENTRY_POINT,
                     "reserved_usd": "%d.%02d" % (row["reservation_usd_cents"] // 100, row["reservation_usd_cents"] % 100),
                     "calls": ["transfer"], "status": row["status"], "success": False, "delegated": bool(delegation is None and self.delegate_first)}
        message = "submitted on %s: leg 1 user_operation tx %s; signed as UserOperation %s" % (self.chain, row["transaction_hash"], row["user_op_hash"])
        if delegation is not None:
            operation["delegation_tx_hash"] = delegation["transaction_hash"]
            message += "; the key was delegated first (tx %s)" % delegation["transaction_hash"]
        message += "; sent by the access platform's sponsor as tx %s; the ticket is spent" % row["transaction_hash"]
        execution = {"tx_hash": row["transaction_hash"], "status": "submitted", "backend": "account_road", "legs": [{"kind": "user_operation", "tx_hash": row["transaction_hash"]}],
                     "user_operation": operation}
        return mcp_answer({"status": "submitted", "ticket_id": args.get("ticket_id"), "policy_hash": POLICY_HASH, "execution": execution,
                           "signed": True, "gateway_reached": True, "message": message, "gas_account": self.gas_line(),
                           "ticket": {"id": args.get("ticket_id"), "used_at": "2026-09-24T05:20:04Z"}})

    def call(self, tool: str, args: Dict[str, Any], test_id: str) -> h.McpAnswer:
        bare = tool.split(".", 1)[-1]
        if bare in h.ROADS:
            raise h.HarnessError("refusing to call %s" % tool)
        self.calls.append((test_id, tool, dict(args)))
        if tool == h.MY_AGENT_TOOL:
            return mcp_answer(self.my_agent_answer())
        if tool == "wallet.wallet_status":
            return mcp_answer(self.status_answer())
        if tool == "wallet.get_balances":
            return mcp_answer(self.balances_answer())
        if tool == "police.check_action":
            return self.check_action_answer(args)
        if tool == "wallet.build_transaction":
            return self.build_answer(args)
        if tool == "wallet.submit_transaction":
            return self.submit_answer(args)
        raise AssertionError("the rehearsal reached for %s" % tool)

    def calls_to(self, tool: str) -> List[Dict[str, Any]]:
        return [args for _, name, args in self.calls if name == tool]


class FakeOauth:
    """The token store as the tests need it: a stored consent, or none — in which case the consent runs and is counted."""

    def __init__(self, stored: Optional[Dict[str, Any]] = None):
        self.stored = stored
        self.consents: List[str] = []
        self.access_token = sentinel("access")
        self.refresh_token = sentinel("refresh")

    def tokens(self, label: str) -> Optional[Dict[str, Any]]:
        return self.stored

    def consent(self, label: str) -> Dict[str, Any]:
        self.consents.append(label)
        self.stored = {"label": label, "access_token": self.access_token, "refresh_token": self.refresh_token}
        return self.stored
