#!/usr/bin/env python3
"""
THE CORRIDOR HARNESS: a Python script that runs the acceptance series as the agent.

Spec T1, 13 September 2026. Two laws (Spec T1 §1):

  THE HARNESS IS THE AGENT, NOT A JUDGE. It speaks to the corridor exactly as
  Claude does — MCP over HTTPS at https://mcppro.aeredium.io/mcp, under an agent's
  own OAuth consent — and says the words the Owner's Guide gives. It holds no key,
  no rail and no rule of its own.

  A FAILURE IS EVIDENCE, NOT A VERDICT. When a test does not come out as the
  Series expects, the report carries what was sent, what came back word for word,
  who answered, and where the truth can be read. The harness never paraphrases an
  answer and never guesses at a cause.

Read from the connector's code rather than from memory (Spec T1 §10):
  apps/server/src/routes/oauth.ts        the five OAuth routes, PKCE S256 only, no client secret
  apps/server/src/services/connector.ts  loopback redirects match on any port (RFC 8252 §7.3),
                                         a five-minute code, rotating refresh tokens
  apps/server/src/routes/mcp.ts          stateless streamable HTTP, JSON answers, the 401 shape
  apps/server/src/services/mcprelay.ts   tools are `<door>.<name>`; the connector's own are
                                         `aerconnect_my_agent` and `aerconnect_guide`
  packages/shared/src/knowledge.ts       ROADS — the tools that are not an AER Connect agent's
  packages/shared/src/words.ts           the scope `aeredium:act`, the relay's refusal sentences

Runs on the Mac's own Python 3.9.6 with the standard library only (Spec T1 §2 as
amended): urllib.request, json, hashlib, secrets, http.server. Nothing else.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import hashlib
import http.server
import json
import os
import re
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import series as S  # noqa: E402
import tables as T  # noqa: E402

# ---------------------------------------------------------------------------
# Constants read from the connector's code.
# ---------------------------------------------------------------------------
DEFAULT_ISSUER = "https://mcppro.aeredium.io"
MCP_PATH = "/mcp"  # config.ts: CONNECTOR_MCP_PATH default
PROTOCOL_VERSION = "2025-06-18"  # test/mcpclient.ts: the version the SDK's client offers
ACTING_SCOPE = "aeredium:act"  # words.ts: ACTING_SCOPE
MY_AGENT_TOOL = "aerconnect_my_agent"  # mcprelay.ts: MY_AGENT_TOOL
GUIDE_TOOL = "aerconnect_guide"  # mcprelay.ts: GUIDE_TOOL
NOT_THE_ROAD_SAID = "NOT THE ROAD FOR AN AER CONNECT AGENT."  # words.ts
# knowledge.ts ROADS: refused by the relay before any door is dialled. Never called.
ROADS = ("request_assignment", "police_assignment_status", "assignment_status")
CLIENT_NAME = "corridor-harness"
REGISTERED_REDIRECT_PORT = 8765  # any loopback port matches at authorize (connector.ts, redirectUriMatches)
CONSENT_WINDOW_SECONDS = 4 * 60 * 60  # connector.ts: CONSENT_WINDOW_MS
HASH_WAIT_SECONDS = 90  # Spec T1 §4
RECEIPT_WAIT_SECONDS = 240
CROSSING_WAIT_SECONDS = 20 * 60
STORE_DIR = os.path.expanduser("~/.corridor-harness")
RUNS_DIR = os.path.expanduser("~/Downloads/harness-runs")
USER_AGENT = "corridor-harness/1.0 (python-stdlib)"

# The outcomes a test can have in the report (Spec T1 §6).
PASS = "pass"
PASS_NOTE = "pass with a note"
FAIL = "fail"
HELD_OUT = "held"
SKIPPED = "skipped"
PERSON_OUT = "left to a person"
NOT_RUN = "not run"

# Relay sentences, from words.ts, used to read who answered.
RELAY_POLICE_REFUSED = "MCP Police REFUSED this call."
RELAY_WALLET_REFUSED = "The MCP Wallet door REFUSED this call."
RELAY_UNREACHABLE = "could not be reached, so nothing was done."
RELAY_NO_SUCH_TOOL = "There is no tool called"
RELAY_DOOR_LACKS_TOOL = "carries no tool called"
RELAY_READER = "It was granted in the reading rank"
RELAY_LAPSED = "Tell the person to pay the subscription"


# The sentence the harness refuses a money series in, when an agent's wallet is on a
# chain the product does not offer (Spec T2 §6). Victor's Trader was on aeredium-testnet.
def chain_guard_sentence(label: str, chain: Optional[str]) -> str:
    return ("%s's wallet is on %s, which the product does not offer; the series runs on ethereum, "
            "arbitrum and base. Create the agent again on one of those and consent it." % (label, chain))


class HarnessError(Exception):
    """A fault of the harness or its surroundings, never a judgment about the corridor."""


class Unreachable(HarnessError):
    """The network did not answer."""


# ---------------------------------------------------------------------------
# Keccak-256, in pure Python, because Ethereum's hash is not hashlib's sha3.
# ---------------------------------------------------------------------------
_M64 = (1 << 64) - 1
_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_KECCAK_ROT = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def _rol(value: int, shift: int) -> int:
    shift %= 64
    if shift == 0:
        return value & _M64
    return ((value << shift) | (value >> (64 - shift))) & _M64


def _keccak_f(a: List[int]) -> List[int]:
    for rc in _KECCAK_RC:
        c = [a[x] ^ a[x + 5] ^ a[x + 10] ^ a[x + 15] ^ a[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        a = [a[i] ^ d[i % 5] for i in range(25)]
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(a[x + 5 * y], _KECCAK_ROT[x][y])
        a = [
            b[i] ^ ((b[(i % 5 + 1) % 5 + 5 * (i // 5)] ^ _M64) & b[(i % 5 + 2) % 5 + 5 * (i // 5)])
            for i in range(25)
        ]
        a[0] ^= rc
    return a


def keccak256(data: bytes) -> bytes:
    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != 0:
        padded.append(0x00)
    padded[-1] |= 0x80
    state = [0] * 25
    for offset in range(0, len(padded), rate):
        block = padded[offset:offset + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[8 * i:8 * i + 8], "little")
        state = _keccak_f(state)
    return b"".join(state[i].to_bytes(8, "little") for i in range(4))


def selector(signature: str) -> str:
    return "0x" + keccak256(signature.encode("ascii"))[:4].hex()


def event_topic(signature: str) -> str:
    return "0x" + keccak256(signature.encode("ascii")).hex()


def checksum_address(addr: str) -> str:
    """EIP-55, so an address is read aloud the way the explorer prints it."""
    low = addr.lower().replace("0x", "")
    digest = keccak256(low.encode("ascii")).hex()
    out = []
    for ch, nibble in zip(low, digest):
        out.append(ch.upper() if ch in "abcdef" and int(nibble, 16) >= 8 else ch)
    return "0x" + "".join(out)


TRANSFER_TOPIC = event_topic("Transfer(address,address,uint256)")

# ---------------------------------------------------------------------------
# ABI decoding for the calls the harness knows (Spec T1 §6, chain.jsonl).
# ---------------------------------------------------------------------------
SIGNATURES: Dict[str, str] = {
    "approve(address,uint256)": "approve",
    "transfer(address,uint256)": "transfer",
    "transferFrom(address,address,uint256)": "transferFrom",
    "exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))": "exactInputSingle",
    "exactInputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))": "exactInputSingle(deadline)",
    "exactInput((bytes,address,uint256,uint256))": "exactInput",
    "exactInput((bytes,address,uint256,uint256,uint256))": "exactInput(deadline)",
    "exactOutputSingle((address,address,uint24,address,uint256,uint256,uint160))": "exactOutputSingle",
    "multicall(bytes[])": "multicall",
    "multicall(uint256,bytes[])": "multicall(deadline)",
    "multicall(bytes32,bytes[])": "multicall(previousBlockhash)",
    "sweepTokenWithFee(address,uint256,uint256,address)": "sweepTokenWithFee",
    "sweepTokenWithFee(address,uint256,address,uint256,address)": "sweepTokenWithFee(recipient)",
    "sweepToken(address,uint256)": "sweepToken",
    "sweepToken(address,uint256,address)": "sweepToken(recipient)",
    "unwrapWETH9(uint256)": "unwrapWETH9",
    "unwrapWETH9(uint256,address)": "unwrapWETH9(recipient)",
    "unwrapWETH9WithFee(uint256,uint256,address)": "unwrapWETH9WithFee",
    "unwrapWETH9WithFee(uint256,address,uint256,address)": "unwrapWETH9WithFee(recipient)",
    "refundETH()": "refundETH",
    "depositForBurn(uint256,uint32,bytes32,address)": "depositForBurn",
    "depositForBurn(uint256,uint32,bytes32,address,bytes32,uint256,uint32)": "depositForBurn(v2)",
    "receiveMessage(bytes,bytes)": "receiveMessage",
    "send((uint32,bytes32,uint256,uint256,bytes,bytes,bytes),(uint256,uint256),address)": "send",
    "exchange(int128,int128,uint256,uint256)": "exchange",
    "exchange(uint256,uint256,uint256,uint256)": "exchange",
    "exchange_underlying(int128,int128,uint256,uint256)": "exchange_underlying",
}
SELECTORS: Dict[str, Tuple[str, str]] = {selector(sig): (name, sig) for sig, name in SIGNATURES.items()}


def _hexbytes(data: str) -> bytes:
    return bytes.fromhex(data[2:] if data.startswith("0x") else data)


def _int_at(args: bytes, offset: int) -> int:
    return int.from_bytes(args[offset:offset + 32], "big")


def _addr_at(args: bytes, offset: int) -> str:
    return checksum_address("0x" + args[offset + 12:offset + 32].hex())


def _bytes32_at(args: bytes, offset: int) -> str:
    return "0x" + args[offset:offset + 32].hex()


def _bytes32_as_address(word: str) -> str:
    raw = word[2:]
    if raw[:24] == "0" * 24:
        return checksum_address("0x" + raw[24:])
    return word


def _dyn_bytes_at(args: bytes, offset: int) -> bytes:
    length = _int_at(args, offset)
    return args[offset + 32:offset + 32 + length]


def _dyn_bytes_array_at(args: bytes, base: int) -> List[bytes]:
    count = _int_at(args, base)
    items = []
    for k in range(count):
        rel = _int_at(args, base + 32 + 32 * k)
        items.append(_dyn_bytes_at(args, base + 32 + rel))
    return items


def decode_call(data: str) -> Dict[str, Any]:
    """The call a transaction's input encodes, where the harness knows the selector."""
    raw = _hexbytes(data) if data and data != "0x" else b""
    if len(raw) < 4:
        return {"function": "none", "selector": None}
    sel = "0x" + raw[:4].hex()
    args = raw[4:]
    known = SELECTORS.get(sel)
    if known is None:
        return {"function": "unknown", "selector": sel}
    name, sig = known
    out: Dict[str, Any] = {"function": name, "selector": sel, "signature": sig}
    try:
        if name in ("approve", "transfer"):
            out["args"] = {"to" if name == "transfer" else "spender": _addr_at(args, 0), "amount": _int_at(args, 32)}
        elif name == "transferFrom":
            out["args"] = {"from": _addr_at(args, 0), "to": _addr_at(args, 32), "amount": _int_at(args, 64)}
        elif name == "exactInputSingle":
            out["args"] = {
                "tokenIn": _addr_at(args, 0), "tokenOut": _addr_at(args, 32), "fee": _int_at(args, 64),
                "recipient": _addr_at(args, 96), "amountIn": _int_at(args, 128),
                "amountOutMinimum": _int_at(args, 160), "sqrtPriceLimitX96": _int_at(args, 192),
            }
        elif name == "exactInputSingle(deadline)":
            out["args"] = {
                "tokenIn": _addr_at(args, 0), "tokenOut": _addr_at(args, 32), "fee": _int_at(args, 64),
                "recipient": _addr_at(args, 96), "deadline": _int_at(args, 128), "amountIn": _int_at(args, 160),
                "amountOutMinimum": _int_at(args, 192), "sqrtPriceLimitX96": _int_at(args, 224),
            }
        elif name == "exactOutputSingle":
            out["args"] = {
                "tokenIn": _addr_at(args, 0), "tokenOut": _addr_at(args, 32), "fee": _int_at(args, 64),
                "recipient": _addr_at(args, 96), "amountOut": _int_at(args, 128),
                "amountInMaximum": _int_at(args, 160), "sqrtPriceLimitX96": _int_at(args, 192),
            }
        elif name.startswith("exactInput"):
            tuple_at = _int_at(args, 0)
            path = _dyn_bytes_at(args, tuple_at + _int_at(args, tuple_at))
            fields = {"path": "0x" + path.hex(), "recipient": _addr_at(args, tuple_at + 32)}
            if name == "exactInput":
                fields.update({"amountIn": _int_at(args, tuple_at + 64), "amountOutMinimum": _int_at(args, tuple_at + 96)})
            else:
                fields.update({"deadline": _int_at(args, tuple_at + 64), "amountIn": _int_at(args, tuple_at + 96),
                               "amountOutMinimum": _int_at(args, tuple_at + 128)})
            out["args"] = fields
        elif name.startswith("multicall"):
            if name == "multicall":
                base = _int_at(args, 0)
            else:
                out["args"] = {"deadline" if "deadline" in name else "previousBlockhash":
                               _int_at(args, 0) if "deadline" in name else _bytes32_at(args, 0)}
                base = _int_at(args, 32)
            out["inner"] = [decode_call("0x" + item.hex()) for item in _dyn_bytes_array_at(args, base)]
        elif name == "sweepTokenWithFee":
            out["args"] = {"token": _addr_at(args, 0), "amountMinimum": _int_at(args, 32),
                           "feeBips": _int_at(args, 64), "feeRecipient": _addr_at(args, 96)}
        elif name == "sweepTokenWithFee(recipient)":
            out["args"] = {"token": _addr_at(args, 0), "amountMinimum": _int_at(args, 32), "recipient": _addr_at(args, 64),
                           "feeBips": _int_at(args, 96), "feeRecipient": _addr_at(args, 128)}
        elif name == "sweepToken":
            out["args"] = {"token": _addr_at(args, 0), "amountMinimum": _int_at(args, 32)}
        elif name == "sweepToken(recipient)":
            out["args"] = {"token": _addr_at(args, 0), "amountMinimum": _int_at(args, 32), "recipient": _addr_at(args, 64)}
        elif name == "unwrapWETH9":
            out["args"] = {"amountMinimum": _int_at(args, 0)}
        elif name == "unwrapWETH9(recipient)":
            out["args"] = {"amountMinimum": _int_at(args, 0), "recipient": _addr_at(args, 32)}
        elif name == "unwrapWETH9WithFee":
            out["args"] = {"amountMinimum": _int_at(args, 0), "feeBips": _int_at(args, 32), "feeRecipient": _addr_at(args, 64)}
        elif name == "unwrapWETH9WithFee(recipient)":
            out["args"] = {"amountMinimum": _int_at(args, 0), "recipient": _addr_at(args, 32),
                           "feeBips": _int_at(args, 64), "feeRecipient": _addr_at(args, 96)}
        elif name == "refundETH":
            out["args"] = {}
        elif name == "depositForBurn":
            out["args"] = {"amount": _int_at(args, 0), "destinationDomain": _int_at(args, 32),
                           "mintRecipient": _bytes32_as_address(_bytes32_at(args, 64)), "burnToken": _addr_at(args, 96)}
        elif name == "depositForBurn(v2)":
            out["args"] = {"amount": _int_at(args, 0), "destinationDomain": _int_at(args, 32),
                           "mintRecipient": _bytes32_as_address(_bytes32_at(args, 64)), "burnToken": _addr_at(args, 96),
                           "destinationCaller": _bytes32_as_address(_bytes32_at(args, 128)), "maxFee": _int_at(args, 160),
                           "minFinalityThreshold": _int_at(args, 192)}
        elif name == "receiveMessage":
            message = _dyn_bytes_at(args, _int_at(args, 0))
            attestation = _dyn_bytes_at(args, _int_at(args, 32))
            out["args"] = {"message": "0x" + message.hex(), "message_bytes": len(message),
                           "attestation_bytes": len(attestation)}
        elif name == "send":
            p = _int_at(args, 0)
            out["args"] = {
                "dstEid": _int_at(args, p), "to": _bytes32_as_address(_bytes32_at(args, p + 32)),
                "amountLD": _int_at(args, p + 64), "minAmountLD": _int_at(args, p + 96),
                "nativeFee": _int_at(args, 32), "lzTokenFee": _int_at(args, 64), "refundAddress": _addr_at(args, 96),
            }
        elif name in ("exchange", "exchange_underlying"):
            def signed(v: int) -> int:
                return v - (1 << 256) if v >= (1 << 255) else v
            out["args"] = {"i": signed(_int_at(args, 0)), "j": signed(_int_at(args, 32)),
                           "dx": _int_at(args, 64), "min_dy": _int_at(args, 96)}
    except (IndexError, ValueError) as err:
        out["decode_error"] = str(err)
    return out


def transfers_in(receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The ERC-20 Transfer events a receipt logged: token, from, to, amount."""
    out = []
    for log in receipt.get("logs") or []:
        topics = log.get("topics") or []
        if len(topics) == 3 and str(topics[0]).lower() == TRANSFER_TOPIC:
            data = log.get("data") or "0x0"
            amount = int(data, 16) if data not in ("0x", "") else 0
            out.append({
                "token": checksum_address(log.get("address", "")),
                "from": checksum_address("0x" + str(topics[1])[-40:]),
                "to": checksum_address("0x" + str(topics[2])[-40:]),
                "amount": amount,
                "log_index": int(str(log.get("logIndex", "0x0")), 16) if isinstance(log.get("logIndex"), str) else log.get("logIndex"),
            })
    return out


def fee_check(transfers: Sequence[Dict[str, Any]], fee_address: str, wallet_address: str,
              bps: int = T.FEE_BPS, router: Optional[str] = None) -> Dict[str, Any]:
    """
    THE FIVE-BASIS-POINT LEG (Series §2, D2, F2). The fee is taken inside the swap
    transaction: the pool pays the bought token to the router (the gross output),
    the router pays fee = gross * bps / 10000, rounded down, to the fee address,
    and the rest to the wallet. The gross is read from the pool's own transfer to
    the router where the router is known, so that a fee one unit short or one
    unit over fails either way; without the router it is delivered plus fee.
    """
    fee_low = fee_address.lower()
    wallet_low = wallet_address.lower()
    legs = [t for t in transfers if t["to"].lower() == fee_low]
    if not legs:
        return {"ok": False, "found": None, "expected": None, "reason": "no transfer to the fee address in this receipt"}
    leg = legs[0]
    token = leg["token"].lower()
    delivered = sum(t["amount"] for t in transfers if t["token"].lower() == token and t["to"].lower() == wallet_low)
    gross_from_pool = None
    if router:
        to_router = [t["amount"] for t in transfers if t["token"].lower() == token and t["to"].lower() == router.lower()]
        gross_from_pool = sum(to_router) if to_router else None
    gross = gross_from_pool if gross_from_pool is not None else delivered + leg["amount"]
    expected = gross * bps // 10000
    ok = leg["amount"] == expected and len(legs) == 1 and (gross_from_pool is None or delivered + leg["amount"] == gross)
    return {
        "ok": ok, "token": leg["token"], "found": leg["amount"], "expected": expected,
        "delivered": delivered, "gross": gross, "gross_read_from": "the pool's transfer to the router" if gross_from_pool is not None else "delivered plus fee",
        "bps": bps, "legs_to_fee_address": len(legs),
        "reason": None if ok else "the fee leg is %d units and five basis points of %d is %d" % (leg["amount"], gross, expected),
    }


# ---------------------------------------------------------------------------
# The sentence matcher (Spec T1 §7): the Guide's ellipses and <placeholders>
# are wildcards; the fixed words must all be there, in order.
# ---------------------------------------------------------------------------
_QUOTES = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"}


def normalise(text: str) -> str:
    out = text or ""
    # A sentence inside a JSON text blob may arrive with \uXXXX, \n or \/ escapes; read it as the words it is.
    out = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), out)
    out = out.replace("\\n", " ").replace("\\t", " ").replace("\\/", "/")
    for odd, plain in _QUOTES.items():
        out = out.replace(odd, plain)
    out = out.replace("...", "…")
    return re.sub(r"\s+", " ", out).strip().lower()


def sentence_regex(sentence: str) -> "re.Pattern[str]":
    text = normalise(sentence)
    parts: List[str] = []
    for token in re.split(r"(…|<[^<>]*>)", text):
        if not token:
            continue
        if token == "…" or (token.startswith("<") and token.endswith(">")):
            parts.append(".*?")
            continue
        alternatives = [a.strip() for a in token.split(" / ")] if " / " in token else [token.strip()]
        alternatives = [a for a in alternatives if a]
        if not alternatives:
            continue
        escaped = [r"\s+".join(re.escape(word) for word in alt.split()) for alt in alternatives]
        parts.append("(?:%s)" % "|".join(escaped) if len(escaped) > 1 else escaped[0])
    return re.compile("".join(parts), re.S)


def matches_sentence(expected: str, actual: str) -> bool:
    if not expected:
        return False
    return sentence_regex(expected).search(normalise(actual)) is not None


def guide_sentence_for(actual: str) -> Optional[Dict[str, str]]:
    """The Guide §10 row (or the Series' other quoted sentence) this text carries, or None."""
    for row in list(S.GUIDE_SECTION_10) + list(S.OTHER_SENTENCES):
        if matches_sentence(row["sentence"], actual):
            return row
    return None


# ---------------------------------------------------------------------------
# Redaction (Spec T1 §6, §10): the bearer and any receipt or ticket secret.
# ---------------------------------------------------------------------------
SECRET_KEYS = {
    "authorization", "access_token", "refresh_token", "police_receipt", "code_verifier", "client_secret",
    "private_key", "secret", "ticket_secret", "ticket_token", "signed_tx", "signed_transaction",
    "raw_transaction", "raw_tx", "receipt_token",
}
REDACTED = "<redacted>"


def secret_values(value: Any, parent_key: Optional[str] = None) -> List[str]:
    """The values under secret keys, so the same bytes are scrubbed wherever else they appear (inside a text blob, say)."""
    found: List[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            low = str(key).lower()
            secret_key = low in SECRET_KEYS or low.endswith("_secret") or (low == "token" and parent_key in ("receipt", "ticket"))
            if secret_key and isinstance(inner, str) and len(inner) >= 8:
                found.append(inner)
            else:
                found.extend(secret_values(inner, low))
    elif isinstance(value, list):
        for item in value:
            found.extend(secret_values(item, parent_key))
    elif isinstance(value, str) and value.lstrip().startswith("{"):
        inner = json_in(value)
        if isinstance(inner, (dict, list)):
            found.extend(secret_values(inner, parent_key))
    return found


def answered(answer: "McpAnswer", words: Sequence[str], any_of: bool = False) -> bool:
    """The fifth kind (Spec T1 §7): a text containing the given words."""
    if answer.is_error:
        return False
    haystack = normalise(answer.quoted())
    hits = [w for w in words if normalise(w) in haystack]
    return bool(hits) if any_of else len(hits) == len(list(words))


def redact(value: Any, secrets_: Sequence[str] = (), parent_key: Optional[str] = None) -> Any:
    """Every secret replaced by <redacted>; everything else returned byte for byte."""
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, inner in value.items():
            low = str(key).lower()
            secret_key = low in SECRET_KEYS or low.endswith("_secret") or (low == "token" and parent_key in ("receipt", "ticket"))
            if secret_key and inner not in (None, "", False):
                out[key] = REDACTED
            else:
                out[key] = redact(inner, secrets_, low)
        return out
    if isinstance(value, list):
        return [redact(item, secrets_, parent_key) for item in value]
    if isinstance(value, str):
        out_s = value
        for secret in secrets_:
            if secret and secret in out_s:
                out_s = out_s.replace(secret, REDACTED)
        return out_s
    return value


# ---------------------------------------------------------------------------
# Reading an answer: the text a model reads, the JSON in it, a key anywhere.
# ---------------------------------------------------------------------------
HEX64 = re.compile(r"\b0x[0-9a-fA-F]{64}\b")
HEX40 = re.compile(r"\b0x[0-9a-fA-F]{40}\b")


def text_of(result: Optional[Dict[str, Any]]) -> str:
    if not isinstance(result, dict):
        return ""
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    return "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))


def json_in(text: str) -> Optional[Any]:
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    start = text.find("{")
    if start >= 0:
        try:
            return json.loads(text[start:])
        except ValueError:
            return None
    return None


def find_key(obj: Any, names: Sequence[str], want: Optional[type] = None) -> Any:
    """The first value under any of these keys, searched depth-first."""
    wanted = {n.lower() for n in names}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in wanted and (want is None or isinstance(value, want)):
                return value
        for value in obj.values():
            found = find_key(value, names, want)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_key(item, names, want)
            if found is not None:
                return found
    return None


def find_policy_hash(obj: Any) -> Optional[str]:
    for names in (["policy_hash", "policyHash", "policy_document_hash", "pact_hash", "document_hash"],
                  ["content_hash", "hash"]):
        found = find_key(obj, names, str)
        if isinstance(found, str) and found:
            return found
    return None


# ---------------------------------------------------------------------------
# THE HASH IS READ FROM THE WALLET (Spec T2 §1). MCP Police carries no tool
# called can_sign — it answered, in its own words, "MCP Police carries no tool
# called “can_sign”" — so every hash the harness reads comes from the Wallet's
# wallet_status, as `pact.policy_hash`, and from get_balances' `pact_budget`
# where wallet_status states none.
# ---------------------------------------------------------------------------
PACT_BLOCKS = ("pact", "pact_budget", "pactBudget")


def pact_in(obj: Any) -> Dict[str, Any]:
    """The Wallet's pact block: `pact` in wallet_status, `pact_budget` in get_balances."""
    if isinstance(obj, (dict, list)):
        for name in PACT_BLOCKS:
            block = find_key(obj, [name], dict)
            if isinstance(block, dict):
                return block
    return {}


def wallet_pact(obj: Any) -> Dict[str, Any]:
    """
    The pact as the Wallet states it: its hash, its id, its state and its generation.
    A Wallet that states the hash outside a pact block is still read, so that the
    harness reports what the door said rather than nothing at all.
    """
    block = pact_in(obj)
    found = find_key(block, ["policy_hash", "policyHash"], str) if block else None
    if not (isinstance(found, str) and found):
        found = find_policy_hash(obj)
    return {
        "policy_hash": found if isinstance(found, str) and found else None,
        "pact_id": find_key(block, ["id", "pact_id", "pactId"], str) if block else None,
        "state": find_key(block, ["state", "status"], str) if block else None,
        "policy_generation": find_key(block, ["policy_generation", "policyGeneration"]) if block else None,
    }


def wallet_policy_hash(obj: Any) -> Optional[str]:
    """The policy hash the Wallet states, and None where it states none."""
    return wallet_pact(obj).get("policy_hash")


def hash_moved(before: Optional[str], after: Optional[str]) -> bool:
    """Whether the hash has moved between two Wallet answers, compared as the doors print it."""
    return (before or "").lower() != (after or "").lower()


def judged_in(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Police's `judged` block, which allow, deny and hold all carry (Spec T2 §2): the
    pact the door judged under. A5 reads its hash whatever the verdict, because it
    compares hashes and not verdicts.
    """
    if isinstance(obj, (dict, list)):
        block = find_key(obj, ["judged"], dict)
        if isinstance(block, dict):
            return block
    return None


def judged_policy_hash(obj: Any) -> Optional[str]:
    """The hash Police says it judged under, read from the `judged` block and nowhere else."""
    block = judged_in(obj)
    found = find_key(block, ["policy_hash", "policyHash"], str) if block else None
    return found if isinstance(found, str) and found else None


def hex64_in(obj: Any) -> List[str]:
    text = obj if isinstance(obj, str) else json.dumps(obj)
    seen: List[str] = []
    for match in HEX64.findall(text or ""):
        if match.lower() not in [s.lower() for s in seen]:
            seen.append(match)
    return seen


def numeric_leaves(obj: Any, prefix: str = "") -> Dict[str, float]:
    out: Dict[str, float] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.update(numeric_leaves(value, "%s.%s" % (prefix, key) if prefix else str(key)))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            out.update(numeric_leaves(value, "%s[%d]" % (prefix, index)))
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out[prefix] = obj
    return out


# ---------------------------------------------------------------------------
# The classifier (Spec T1 §7): who answered, and which of the five kinds.
# ---------------------------------------------------------------------------
class McpAnswer:
    """One JSON-RPC answer, exactly as received, with the readings the harness makes of it."""

    def __init__(self, status: int, body: Any, raw: str, elapsed_ms: int):
        self.status = status
        self.body = body if isinstance(body, dict) else {}
        self.raw = raw
        self.elapsed_ms = elapsed_ms
        self.result = self.body.get("result") if isinstance(self.body.get("result"), dict) else None
        self.rpc_error = self.body.get("error") if isinstance(self.body.get("error"), dict) else None

    @property
    def text(self) -> str:
        return text_of(self.result)

    @property
    def is_error(self) -> bool:
        return bool(self.result and self.result.get("isError") is True) or self.rpc_error is not None or self.status >= 400

    @property
    def structured(self) -> Any:
        return self.result.get("structuredContent") if self.result else None

    @property
    def data(self) -> Any:
        """The JSON a model would read: structured content where given, else the text parsed."""
        if self.structured is not None:
            return self.structured
        return json_in(self.text)

    def quoted(self) -> str:
        return self.raw if self.raw else json.dumps(self.body)


def who_answered(answer: McpAnswer, door: str) -> Dict[str, Any]:
    """
    WHO ANSWERED, read from the answer itself and never inferred (Spec T1 §6):
    MCP Police with its reason field, the MCP Wallet with its own sentence, the
    engine's reason code as the Wallet relayed it, or AER Connect's relay.
    """
    text = answer.text
    if answer.rpc_error is not None:
        return {"party": "the connector's MCP route (a JSON-RPC error)", "reason": str(answer.rpc_error.get("code")),
                "sentence": str(answer.rpc_error.get("message", ""))}
    if answer.status == 401:
        return {"party": "the connector's MCP route (401, the bearer was not accepted)", "reason": "invalid_token",
                "sentence": answer.raw}
    data = answer.data
    if isinstance(data, dict) and data.get("refused") is True and data.get("by"):
        return {"party": "AER Connect's relay (%s), before any door was dialled" % data.get("by"),
                "reason": str(data.get("reason", "")), "sentence": str(data.get("reason", "")),
                "source": str(data.get("source", ""))}
    if text.startswith(RELAY_POLICE_REFUSED) or text.startswith(RELAY_WALLET_REFUSED):
        party = "MCP Police" if text.startswith(RELAY_POLICE_REFUSED) else "the MCP Wallet"
        quoted = re.search(r"said: “(.*)”", text, re.S)
        return {"party": "%s (an HTTP refusal, relayed whole by AER Connect)" % party, "reason": "door_refused",
                "sentence": quoted.group(1) if quoted else text}
    if RELAY_UNREACHABLE in text:
        return {"party": "AER Connect's relay: %s did not answer" % ("MCP Police" if "Police" in text else "the MCP Wallet door"),
                "reason": "door_unreachable", "sentence": text}
    if text.startswith(RELAY_NO_SUCH_TOOL) or RELAY_DOOR_LACKS_TOOL in text:
        return {"party": "AER Connect's relay (no such tool)", "reason": "unknown_tool", "sentence": text}
    if RELAY_READER in text:
        return {"party": "AER Connect's relay (the reading rank may not act)", "reason": "reader", "sentence": text}
    if RELAY_LAPSED in text:
        return {"party": "AER Connect's relay (the subscription is not paid)", "reason": "lapsed", "sentence": text}
    if door == "police":
        reason = find_key(data, ["reason", "reason_code", "code"], str) if isinstance(data, (dict, list)) else None
        verdict = find_key(data, ["verdict", "decision", "outcome"], str) if isinstance(data, (dict, list)) else None
        sentence = _sentence_in(data) or text
        return {"party": "MCP Police", "reason": reason or verdict or "", "verdict": verdict, "sentence": sentence}
    if door == "wallet":
        code, sentence = _code_and_sentence(text)
        if code and code.startswith(("agent_", "policy_", "engine_", "rule_", "hold_", "aap_", "pact_")):
            return {"party": "the engine's reason code as the MCP Wallet relayed it", "reason": code, "sentence": sentence}
        return {"party": "the MCP Wallet", "reason": code or "", "sentence": sentence or text}
    return {"party": "AER Connect (the connector's own tool)", "reason": "", "sentence": text}


def _sentence_in(data: Any) -> Optional[str]:
    if not isinstance(data, (dict, list)):
        return None
    for names in (["sentence"], ["message"], ["said"], ["not_issued_because"], ["detail"], ["explanation"], ["description"]):
        found = find_key(data, names, str)
        if isinstance(found, str) and found.strip():
            return found
    return None


def _code_and_sentence(text: str) -> Tuple[Optional[str], str]:
    match = re.match(r"^\s*([a-z][a-z0-9_]{2,60})\s*:\s*(.*)$", text or "", re.S)
    if match:
        return match.group(1), match.group(2).strip()
    data = json_in(text or "")
    if isinstance(data, dict):
        code = find_key(data, ["code", "reason", "reason_code"], str)
        return (code, _sentence_in(data) or text)
    return None, text or ""


# Words in a door's HTTP refusal that mean the CREDENTIAL or the ROAD was refused,
# not the action: such an answer is no judgment of the action and never a pass.
NOT_A_JUDGMENT = ("credential", "unauthorized", "unauthorised", "unauthenticated", "not authoriz", "rate_limited",
                  "rate limit", "bearer", "token")
# Relay-level answers that are not a door's judgment either.
RELAY_REASONS = ("door_unreachable", "unknown_tool", "reader", "lapsed", "invalid_token")


def not_a_judgment(who: Dict[str, Any], answer: McpAnswer) -> bool:
    if answer.rpc_error is not None or answer.status >= 400:
        return True
    if who.get("reason") in RELAY_REASONS:
        return True
    if isinstance(answer.data, dict) and answer.data.get("refused") is True and answer.data.get("by"):
        return True  # the relay refused a road before any door was dialled
    if who.get("reason") == "door_refused":
        low = normalise(str(who.get("sentence", "")))
        return any(marker in low for marker in NOT_A_JUDGMENT)
    return False


def classify_police(answer: McpAnswer) -> Dict[str, Any]:
    """allow | deny | hold | no_judgment | unreadable, with the receipt where there is one."""
    who = who_answered(answer, "police")
    if not_a_judgment(who, answer):
        return {"kind": "no_judgment", "who": who, "sentence": who.get("sentence", "")}
    if who["reason"] == "door_refused":
        # Police refused over HTTP in its own words (mcpdoor.ts, classify): a judgment, delivered whole.
        return {"kind": "deny", "who": who, "sentence": who["sentence"]}
    data = answer.data
    verdict = (find_key(data, ["verdict", "decision", "outcome"], str) or "").lower() if isinstance(data, (dict, list)) else ""
    reason = (find_key(data, ["reason", "reason_code"], str) or "").lower() if isinstance(data, (dict, list)) else ""
    allowed = find_key(data, ["allowed", "allow", "ok", "can_sign"], bool) if isinstance(data, (dict, list)) else None
    receipt = find_key(data, ["receipt"]) if isinstance(data, (dict, list)) else None
    token = None
    if isinstance(receipt, dict):
        token = receipt.get("token") if receipt.get("issued") is not False else None
    elif isinstance(receipt, str):
        token = receipt
    if reason == "manual_approval_required" or verdict.startswith("hold") or "manual_approval" in verdict:
        return {"kind": "hold", "who": who, "sentence": who["sentence"], "policy_hash": find_policy_hash(data)}
    if verdict == "allow" or verdict == "allowed" or allowed is True or reason == "allowed":
        return {"kind": "allow", "who": who, "receipt": token, "receipt_id": find_key(receipt, ["id", "receipt_id", "nonce"], str) if isinstance(receipt, dict) else None,
                "policy_hash": find_policy_hash(data), "sentence": who["sentence"]}
    if verdict in ("deny", "denied", "refuse", "refused") or reason == "denied" or reason.startswith("context_incomplete") or allowed is False or answer.is_error:
        return {"kind": "deny", "who": who, "sentence": who["sentence"], "policy_hash": find_policy_hash(data)}
    return {"kind": "unreadable", "who": who, "sentence": answer.text}


def classify_wallet(answer: McpAnswer) -> Dict[str, Any]:
    """ticket | refused | held | no_judgment | unreadable, with the ticket where there is one."""
    who = who_answered(answer, "wallet")
    text = answer.text
    if not_a_judgment(who, answer):
        return {"kind": "no_judgment", "who": who, "sentence": who.get("sentence", "")}
    if matches_sentence(S.HOLD_SENTENCE, text):
        return {"kind": "held", "who": who, "sentence": who.get("sentence") or text}
    if answer.is_error:
        return {"kind": "refused", "who": who, "sentence": who.get("sentence") or text}
    data = answer.data
    ticket_id = None
    if isinstance(data, (dict, list)):
        ticket_id = find_key(data, ["ticket_id", "ticketId"], str)
        if ticket_id is None:
            ticket = find_key(data, ["ticket"])
            if isinstance(ticket, dict):
                ticket_id = find_key(ticket, ["id", "ticket_id"], str)
    if ticket_id:
        legs = find_key(data, ["legs"], list)
        return {"kind": "ticket", "who": who, "ticket_id": ticket_id, "legs": len(legs) if isinstance(legs, list) else None,
                "policy_hash": find_policy_hash(data), "sentence": who.get("sentence") or ""}
    hashes = hex64_in(data if data is not None else text)
    if hashes:
        return {"kind": "ticket", "who": who, "ticket_id": None, "legs": None, "hashes": hashes, "policy_hash": find_policy_hash(data)}
    return {"kind": "unreadable", "who": who, "sentence": text}


def outcome_kind(walk: Dict[str, Any]) -> str:
    """One of Spec T1 §7's five kinds (or 'no outcome') for a recorded walk."""
    police = walk.get("police")
    if police is not None:
        if police["kind"] == "deny":
            return S.PRE_FLIGHT
        if police["kind"] == "hold":
            return S.HELD
        if police["kind"] in ("no_judgment", "unreadable"):
            return "no outcome"
    build = walk.get("build")
    if build is not None:
        if build["kind"] == "held":
            return S.HELD
        if build["kind"] == "refused":
            return S.AT_WALLET
        if build["kind"] in ("no_judgment", "unreadable"):
            return "no outcome"
    submit = walk.get("submit")
    if submit is not None:
        if submit["kind"] == "refused":
            return S.AT_WALLET
        if submit["kind"] == "held":
            return S.HELD
        if submit["kind"] == "ticket" and walk.get("hashes"):
            return S.ALLOWED
        return "no outcome"
    if build is not None and build["kind"] == "ticket":
        return S.ALLOWED  # built (a ticket issued) and not submitted: the allow that matters for the guard
    return "no outcome"


def kind_matches(expect: str, kind: str) -> bool:
    if expect == S.REFUSED:
        return kind in (S.PRE_FLIGHT, S.AT_WALLET)
    if expect == S.ALLOWED_OR_REFUSED:
        return kind in (S.ALLOWED, S.PRE_FLIGHT, S.AT_WALLET)
    return expect == kind


def is_unexpected_allow(expect: str, walk: Dict[str, Any]) -> bool:
    """An action the Series expected to be refused or held that was built or signed (Spec T1 §5)."""
    if expect not in (S.PRE_FLIGHT, S.AT_WALLET, S.REFUSED, S.HELD):
        return False
    build = walk.get("build")
    submit = walk.get("submit")
    built = build is not None and build["kind"] == "ticket"
    signed = submit is not None and submit["kind"] == "ticket"
    return built or signed


# ---------------------------------------------------------------------------
# Argument building: the Guide's vocabulary, shaped to the door's own schema.
# ---------------------------------------------------------------------------
CANON_ALIASES: List[Tuple[str, List[str]]] = [
    ("action", ["action", "action_kind"]),
    ("chain", ["chain"]),
    ("asset", ["asset", "asset_symbol"]),
    ("amount_usd", ["amount_usd", "amount_usd_cents"]),
    ("to_address", ["to_address"]),
    ("to_asset", ["to_asset"]),
    ("venue", ["venue"]),
    ("contract_address", ["contract_address"]),
    ("to_chain", ["to_chain"]),
]
FACT_ALIASES: List[Tuple[str, List[str]]] = [
    ("wallet_id", ["wallet_id", "child_wallet_id"]),
    ("pact_id", ["pact_id"]),
    ("role_id", ["role_id"]),
    ("police_receipt", ["police_receipt"]),
    ("ticket_id", ["ticket_id"]),
]


def arguments_for(properties: Optional[Dict[str, Any]], action_fields: Dict[str, Any],
                  facts: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    The arguments for one call. With the door's schema in hand, only the fields it
    declares are sent, under the names it declares (the double in
    apps/server/src/test/mcpDoorDouble.ts spells Police's as action_kind,
    asset_symbol, amount_usd_cents and child_wallet_id, and the Wallet's as the
    Guide spells them). Without a schema — a dry run — the Guide's own names are
    printed. What could not be placed is returned so the evidence can say so.
    """
    args: Dict[str, Any] = {}
    omitted: List[str] = []
    for canon, aliases in CANON_ALIASES + FACT_ALIASES:
        value = action_fields.get(canon) if canon in action_fields else facts.get(canon)
        if value is None:
            continue
        if properties is None:
            name = aliases[0]
        else:
            name = next((alias for alias in aliases if alias in properties), None)
            if name is None:
                omitted.append(canon)
                continue
        if name == "amount_usd_cents":
            value = int(round(float(value) * 100))
        args[name] = value
    return args, omitted


def action_fields(action: S.Action, owner_address: Optional[str]) -> Dict[str, Any]:
    """The Guide's vocabulary for one action, with every destination resolved from the two permitted places."""
    fields: Dict[str, Any] = {"action": action.action, "chain": action.chain, "asset": action.asset,
                              "amount_usd": action.amount_usd}
    if action.to_asset is not None:
        fields["to_asset"] = action.to_asset
    if action.venue is not None:
        fields["venue"] = action.venue
    if action.to_chain is not None:
        fields["to_chain"] = action.to_chain
    if action.to_address is not None:
        fields["to_address"] = resolve_address(action.to_address, owner_address)
    if action.contract_address is not None:
        fields["contract_address"] = "" if action.contract_address == "" else resolve_address(action.contract_address, owner_address)
    return fields


def resolve_address(key: str, owner_address: Optional[str]) -> str:
    """A destination comes from the run file or the pinned tables, and from nowhere else (Spec T1 §5)."""
    if key == S.OWNER:
        return owner_address if owner_address else S.OWNER
    if key in T.PINNED:
        return T.address(key)
    raise HarnessError("refusing to send an address that is neither the owner's listed address nor a pinned table entry: %r" % key)


# ---------------------------------------------------------------------------
# HTTP through urllib, and nothing else.
# ---------------------------------------------------------------------------
class HttpAnswer:
    def __init__(self, status: int, headers: Dict[str, str], text: str, elapsed_ms: int):
        self.status = status
        self.headers = headers
        self.text = text
        self.elapsed_ms = elapsed_ms


def http_request(method: str, url: str, headers: Optional[Dict[str, str]] = None, body: Optional[bytes] = None,
                 timeout: float = 60.0) -> HttpAnswer:
    sent = {"User-Agent": USER_AGENT}
    sent.update(headers or {})
    request = urllib.request.Request(url, data=body, method=method, headers=sent)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", "replace")
            return HttpAnswer(response.status, dict(response.headers), text, int((time.monotonic() - started) * 1000))
    except urllib.error.HTTPError as err:
        text = err.read().decode("utf-8", "replace") if err.fp else ""
        return HttpAnswer(err.code, dict(err.headers or {}), text, int((time.monotonic() - started) * 1000))
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as err:
        raise Unreachable("%s %s: %s" % (method, url, getattr(err, "reason", err)))


def parse_rpc_body(text: str) -> Any:
    """A JSON body, or the last `data:` line of an event stream (the SDK's other shape)."""
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except ValueError:
        pass
    last = None
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                last = json.loads(line[5:].strip())
            except ValueError:
                continue
    return last if last is not None else {"raw": text}


# ---------------------------------------------------------------------------
# Files the harness keeps: the token store (mode 600) and the run file.
# ---------------------------------------------------------------------------
def write_private(path: str, data: Any) -> None:
    folder = os.path.dirname(path)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    try:
        os.chmod(folder, 0o700)
    except OSError:
        pass
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, json.dumps(data, indent=2, sort_keys=True).encode("utf-8"))
    finally:
        os.close(fd)


def read_json(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def default_run_file() -> Dict[str, Any]:
    """The skeleton the harness writes on first use for the owner to complete (Spec T1 §3). No secrets."""
    return {
        "_read_me": [
            "Complete this file once. It carries no secrets: labels, the owner's listed address per tester,",
            "and the chain RPC endpoints the harness may READ from (public endpoints suffice; it only reads).",
            "The 'tokens' map names the token contracts whose balances are read for the report; they are",
            "read targets, never destinations, and can be checked against the block explorer.",
        ],
        "issuer": DEFAULT_ISSUER,
        "testers": {
            "eitan": {
                "agents": {"trader": "eitan-trader", "payer": "eitan-payer", "payer_nogas": None},
                "listed_address": "",
                "payer_list_scope": "agent",
            },
            "victor": {
                "agents": {"trader": "victor-trader", "payer": "victor-payer", "payer_nogas": None},
                "listed_address": T.address("VICTOR_LISTED"),
                "payer_list_scope": "shared",
            },
        },
        "chains": {
            "arbitrum": {"chain_id": 42161, "rpc": "https://arb1.arbitrum.io/rpc", "explorer": "https://arbiscan.io/tx/",
                         "tokens": {"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                                    "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                                    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"}},
            "base": {"chain_id": 8453, "rpc": "https://mainnet.base.org", "explorer": "https://basescan.org/tx/",
                     "tokens": {"USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                                "WETH": "0x4200000000000000000000000000000000000006"}},
            "ethereum": {"chain_id": 1, "rpc": "https://ethereum-rpc.publicnode.com", "explorer": "https://etherscan.io/tx/",
                         "tokens": {"USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                                    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                                    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}},
        },
    }


# ---------------------------------------------------------------------------
# The OAuth road (Spec T1 §2): register once, consent per agent, PKCE S256,
# a loopback listener, the token store, and the refresh when told to.
# ---------------------------------------------------------------------------
class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    result: Dict[str, Any] = {}
    done = threading.Event()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        query = urllib.parse.parse_qs(parsed.query)
        _CallbackHandler.result = {key: values[0] for key, values in query.items()}
        body = ("<!doctype html><meta charset='utf-8'><title>corridor harness</title>"
                "<p>The harness has the answer. You can close this tab and return to the terminal.</p>").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        _CallbackHandler.done.set()

    def log_message(self, fmt: str, *args: Any) -> None:  # silence: nothing of the callback is printed
        return


class Oauth:
    def __init__(self, issuer: str, store_dir: str = STORE_DIR, say: Callable[[str], None] = print):
        self.issuer = issuer.rstrip("/")
        self.store_dir = store_dir
        self.say = say
        self._metadata: Optional[Dict[str, Any]] = None
        self._resource: Optional[Dict[str, Any]] = None

    # -- discovery ----------------------------------------------------------
    def metadata(self) -> Dict[str, Any]:
        if self._metadata is None:
            answer = http_request("GET", self.issuer + "/.well-known/oauth-authorization-server")
            if answer.status != 200:
                raise HarnessError("the authorization-server metadata answered %d: %s" % (answer.status, answer.text[:300]))
            self._metadata = json.loads(answer.text)
        return self._metadata

    def resource(self) -> str:
        if self._resource is None:
            answer = http_request("GET", self.issuer + "/.well-known/oauth-protected-resource" + MCP_PATH)
            self._resource = json.loads(answer.text) if answer.status == 200 else {}
        return str(self._resource.get("resource") or (self.issuer + MCP_PATH))

    # -- the client, registered once ---------------------------------------
    def client_path(self) -> str:
        return os.path.join(self.store_dir, "client.json")

    def client(self) -> Dict[str, Any]:
        stored = read_json(self.client_path())
        if stored and stored.get("issuer") == self.issuer and stored.get("client_id"):
            return stored
        redirect = "http://127.0.0.1:%d/callback" % REGISTERED_REDIRECT_PORT
        body = json.dumps({
            "redirect_uris": [redirect],
            "client_name": CLIENT_NAME,
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
        }).encode("utf-8")
        answer = http_request("POST", self.metadata()["registration_endpoint"],
                              {"Content-Type": "application/json", "Accept": "application/json"}, body)
        if answer.status != 201:
            raise HarnessError("registration answered %d: %s" % (answer.status, answer.text[:500]))
        registered = json.loads(answer.text)
        record = {"issuer": self.issuer, "client_id": registered["client_id"], "redirect_uri": redirect,
                  "registered_at": now_iso(), "registration": registered}
        write_private(self.client_path(), record)
        return record

    # -- the token store ----------------------------------------------------
    def token_path(self, label: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
        return os.path.join(self.store_dir, "%s.json" % safe)

    def tokens(self, label: str) -> Optional[Dict[str, Any]]:
        return read_json(self.token_path(label))

    def store_tokens(self, label: str, tokens: Dict[str, Any], client_id: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        record = dict(self.tokens(label) or {})
        record.update({
            "label": label,
            "issuer": self.issuer,
            "client_id": client_id,
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "scope": tokens.get("scope"),
            "token_type": tokens.get("token_type"),
            "expires_at": time.time() + float(tokens.get("expires_in", 3600)),
            "stored_at": now_iso(),
        })
        if extra:
            record.update(extra)
        write_private(self.token_path(label), record)
        return record

    # -- the consent ---------------------------------------------------------
    def consent(self, label: str, wait_seconds: float = CONSENT_WINDOW_SECONDS) -> Dict[str, Any]:
        meta = self.metadata()
        client = self.client()
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(24)
        server, port = self._listen()
        redirect_uri = "http://127.0.0.1:%d/callback" % port
        query = urllib.parse.urlencode({
            "response_type": "code",
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": ACTING_SCOPE,
            "resource": self.resource(),
        })
        link = "%s?%s" % (meta["authorization_endpoint"], query)
        self.say("Consent link for %s: %s" % (label, link))
        self.say("Open the link, choose the %s on the consent page, consent with your passkey, and press Finish; the harness is listening on 127.0.0.1:%d." % (label, port))
        try:
            got = _CallbackHandler.done.wait(wait_seconds)
        finally:
            server.shutdown()
            server.server_close()
        if not got:
            raise HarnessError("no consent arrived within %d seconds for %s" % (int(wait_seconds), label))
        result = dict(_CallbackHandler.result)
        _CallbackHandler.result = {}
        _CallbackHandler.done.clear()
        if result.get("error"):
            raise HarnessError("the consent came back refused: %s — %s" % (result.get("error"), result.get("error_description", "")))
        if result.get("state") != state:
            raise HarnessError("the consent came back with a state the harness did not send; nothing was exchanged")
        code = result.get("code", "")
        if not code:
            raise HarnessError("the consent came back without a code")
        tokens = self._exchange(meta["token_endpoint"], {
            "grant_type": "authorization_code",
            "client_id": client["client_id"],
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": redirect_uri,
        })
        return self.store_tokens(label, tokens, client["client_id"])

    def refresh(self, label: str) -> Dict[str, Any]:
        record = self.tokens(label)
        if not record or not record.get("refresh_token"):
            raise HarnessError("no refresh token is stored for %s; run --consent %s" % (label, label))
        tokens = self._exchange(self.metadata()["token_endpoint"], {
            "grant_type": "refresh_token",
            "client_id": record["client_id"],
            "refresh_token": record["refresh_token"],
        })
        return self.store_tokens(label, tokens, record["client_id"])

    def _exchange(self, token_endpoint: str, form: Dict[str, str]) -> Dict[str, Any]:
        body = urllib.parse.urlencode(form).encode("ascii")
        answer = http_request("POST", token_endpoint,
                              {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}, body)
        if answer.status != 200:
            raise HarnessError("the token endpoint answered %d: %s" % (answer.status, answer.text[:500]))
        tokens = json.loads(answer.text)
        if not tokens.get("access_token"):
            raise HarnessError("the token endpoint answered without an access token")
        return tokens

    @staticmethod
    def _listen() -> Tuple[http.server.HTTPServer, int]:
        _CallbackHandler.result = {}
        _CallbackHandler.done.clear()
        last_error: Optional[Exception] = None
        for port in (REGISTERED_REDIRECT_PORT, 0):
            try:
                server = http.server.HTTPServer(("127.0.0.1", port), _CallbackHandler)
                break
            except OSError as err:
                last_error = err
        else:
            raise HarnessError("could not listen on the loopback interface: %s" % last_error)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, server.server_address[1]


# ---------------------------------------------------------------------------
# The MCP session (Spec T1 §2): initialize, tools/list, tools/call, JSON over
# stateless streamable HTTP as routes/mcp.ts serves it.
# ---------------------------------------------------------------------------
class Mcp:
    def __init__(self, oauth: Oauth, label: str, record: Callable[..., None], mcp_url: Optional[str] = None):
        self.oauth = oauth
        self.label = label
        self.record = record
        self.mcp_url = mcp_url or (oauth.issuer + MCP_PATH)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.instructions = ""
        self.server_info: Dict[str, Any] = {}
        self.secrets_seen: List[str] = []  # so the report can scrub what the evidence scrubbed
        self._next_id = 1

    def bearer(self) -> str:
        record = self.oauth.tokens(self.label)
        if not record:
            raise HarnessError("no token is stored for %s; run --consent %s" % (self.label, self.label.split("-")[-1]))
        if record.get("expires_at", 0) <= time.time() + 30:
            record = self.oauth.refresh(self.label)
        return str(record["access_token"])

    def rpc(self, method: str, params: Optional[Dict[str, Any]], test_id: str, notification: bool = False,
            allow_refresh: bool = True) -> McpAnswer:
        bearer = self.bearer()
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notification:
            payload["id"] = self._next_id
            self._next_id += 1
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": "Bearer " + bearer,
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        http_answer = http_request("POST", self.mcp_url, headers, body)
        parsed = parse_rpc_body(http_answer.text)
        answer = McpAnswer(http_answer.status, parsed, http_answer.text, http_answer.elapsed_ms)
        # The bearer, and every receipt or ticket secret the call carried or the answer marked, wherever it appears.
        secrets_ = [bearer] + secret_values(params or {}) + secret_values(parsed)
        self.secrets_seen.extend(s for s in secrets_ if s not in self.secrets_seen)
        self.record(test_id=test_id, kind=method, tool=(params or {}).get("name", method) if method == "tools/call" else method,
                    arguments=redact((params or {}), secrets_), answer=redact(parsed, secrets_),
                    http_status=http_answer.status, round_trip_ms=http_answer.elapsed_ms, agent=self.label)
        if http_answer.status == 401 and allow_refresh:
            # "It refreshes when told to" (Spec T1 §2): the 401 is the door saying the bearer is spent.
            self.oauth.refresh(self.label)
            return self.rpc(method, params, test_id, notification, allow_refresh=False)
        return answer

    def initialize(self, test_id: str = "connect") -> McpAnswer:
        answer = self.rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": "1.0.0"},
        }, test_id)
        if answer.result:
            self.instructions = str(answer.result.get("instructions", ""))
            self.server_info = answer.result.get("serverInfo") or {}
        self.rpc("notifications/initialized", {}, test_id, notification=True)
        return answer

    def tools_list(self, test_id: str = "connect") -> List[Dict[str, Any]]:
        answer = self.rpc("tools/list", {}, test_id)
        tools = answer.result.get("tools") if answer.result else None
        if not isinstance(tools, list):
            raise HarnessError("tools/list did not answer with a tool list: %s" % answer.quoted()[:500])
        self.tools = {str(tool.get("name")): tool for tool in tools if isinstance(tool, dict)}
        return tools

    def properties_of(self, tool: str) -> Optional[Dict[str, Any]]:
        listed = self.tools.get(tool)
        if not listed:
            return None
        schema = listed.get("inputSchema") or {}
        props = schema.get("properties") if isinstance(schema, dict) else None
        return props if isinstance(props, dict) else {}

    def call(self, tool: str, arguments: Dict[str, Any], test_id: str) -> McpAnswer:
        bare = tool.split(".", 1)[1] if "." in tool else tool
        listed = self.tools.get(tool)
        marked = bool(listed and str(listed.get("description", "")).startswith(NOT_THE_ROAD_SAID))
        if bare in ROADS or marked:
            # Spec T1 §2: never a tool marked not the road for an AER Connect agent.
            raise HarnessError("refusing to call %s: it is marked not the road for an AER Connect agent" % tool)
        return self.rpc("tools/call", {"name": tool, "arguments": arguments}, test_id)


# ---------------------------------------------------------------------------
# The chain reader: JSON-RPC over the run file's public endpoints, reads only.
# ---------------------------------------------------------------------------
class ChainRpc:
    def __init__(self, name: str, url: str, tokens: Optional[Dict[str, str]] = None, explorer: str = ""):
        self.name = name
        self.url = url
        self.tokens = tokens or {}
        self.explorer = explorer
        self._id = 1

    def call(self, method: str, params: Sequence[Any]) -> Any:
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": list(params)}).encode("utf-8")
        self._id += 1
        answer = http_request("POST", self.url, {"Content-Type": "application/json"}, body, timeout=60)
        parsed = json_in(answer.text)
        if not isinstance(parsed, dict):
            raise Unreachable("%s answered %d without JSON: %s" % (self.url, answer.status, answer.text[:200]))
        if parsed.get("error"):
            raise HarnessError("%s %s refused: %s" % (self.name, method, json.dumps(parsed["error"])))
        return parsed.get("result")

    def block_number(self) -> int:
        return int(self.call("eth_blockNumber", []), 16)

    def transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.call("eth_getTransactionByHash", [tx_hash])

    def receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.call("eth_getTransactionReceipt", [tx_hash])

    def wait_receipt(self, tx_hash: str, timeout: float = RECEIPT_WAIT_SECONDS, sleep: Callable[[float], None] = time.sleep) -> Optional[Dict[str, Any]]:
        deadline = time.monotonic() + timeout
        while True:
            receipt = self.receipt(tx_hash)
            if receipt:
                return receipt
            if time.monotonic() >= deadline:
                return None
            sleep(3)

    def native_balance(self, address: str) -> int:
        return int(self.call("eth_getBalance", [address, "latest"]), 16)

    def eth_call(self, to: str, data: str) -> str:
        return str(self.call("eth_call", [{"to": to, "data": data}, "latest"]))

    def token_balance(self, token: str, holder: str) -> int:
        data = selector("balanceOf(address)") + holder.lower().replace("0x", "").rjust(64, "0")
        result = self.eth_call(token, data)
        return int(result, 16) if result not in ("0x", "") else 0

    def token_symbol(self, token: str) -> str:
        try:
            result = self.eth_call(token, selector("symbol()"))
            raw = _hexbytes(result)
            if len(raw) >= 64:
                offset = _int_at(raw, 0)
                if offset < len(raw):
                    return _dyn_bytes_at(raw, offset).decode("utf-8", "replace").strip("\x00") or token
            if len(raw) == 32:
                return raw.rstrip(b"\x00").decode("utf-8", "replace") or token
        except (HarnessError, Unreachable, ValueError):
            pass
        return token

    def token_decimals(self, token: str) -> Optional[int]:
        try:
            result = self.eth_call(token, selector("decimals()"))
            return int(result, 16) if result not in ("0x", "") else None
        except (HarnessError, Unreachable, ValueError):
            return None

    def logs(self, from_block: int, topics: Sequence[Optional[str]], to_block: str = "latest") -> List[Dict[str, Any]]:
        result = self.call("eth_getLogs", [{"fromBlock": hex(from_block), "toBlock": to_block, "topics": list(topics)}])
        return result if isinstance(result, list) else []

    def link(self, tx_hash: str) -> str:
        return (self.explorer + tx_hash) if self.explorer else tx_hash


def pad_topic(address: str) -> str:
    return "0x" + address.lower().replace("0x", "").rjust(64, "0")


def format_units(amount: int, decimals: Optional[int]) -> str:
    if decimals is None:
        return str(amount)
    if decimals == 0:
        return str(amount)
    whole, frac = divmod(amount, 10 ** decimals)
    text = ("%d.%0*d" % (whole, decimals, frac)).rstrip("0").rstrip(".")
    return text if text else "0"


def now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def short(addr: Optional[str]) -> str:
    if not addr or len(addr) < 10:
        return str(addr)
    return addr[:6] + "…"


# ---------------------------------------------------------------------------
# The three files of a run (Spec T1 §6).
# ---------------------------------------------------------------------------
class RunFolder:
    def __init__(self, root: str, tester: str, dry: bool = False):
        self.dry = dry
        stamp = _dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        self.path = os.path.join(root, "%s-%s" % (stamp, tester))
        if not dry:
            os.makedirs(self.path, exist_ok=True)
        self.evidence: List[Dict[str, Any]] = []
        self.chain: List[Dict[str, Any]] = []

    def record(self, **line: Any) -> None:
        entry = {"at": now_iso()}
        entry.update(line)
        self.evidence.append(entry)
        if not self.dry:
            with open(os.path.join(self.path, "evidence.jsonl"), "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def chain_line(self, line: Dict[str, Any]) -> None:
        self.chain.append(line)
        if not self.dry:
            with open(os.path.join(self.path, "chain.jsonl"), "a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")

    def write_report(self, text: str) -> str:
        path = os.path.join(self.path, "report.md")
        if not self.dry:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        return path


# ---------------------------------------------------------------------------
# The runner.
# ---------------------------------------------------------------------------
class Outcome:
    def __init__(self, test: S.Test, outcome: str, sentence: str, evidence: Optional[Dict[str, Any]] = None,
                 note: Optional[Dict[str, str]] = None, line: str = ""):
        self.test = test
        self.outcome = outcome
        self.sentence = sentence
        self.evidence = evidence
        self.note = note  # {"expected": ..., "got": ...} for a pass with a note
        self.line = line


class Runner:
    def __init__(self, tester: str, run_file: Dict[str, Any], oauth: Optional[Oauth], folder: RunFolder,
                 say: Callable[[str], None] = print, ask: Callable[[str], str] = input,
                 sleep: Callable[[float], None] = time.sleep, dry: bool = False, stage2: bool = False,
                 crossing_wait: float = CROSSING_WAIT_SECONDS, session_factory: Optional[Callable[[str], Any]] = None,
                 require_series_a: bool = True, clock: Callable[[], float] = time.monotonic):
        self.tester = tester
        self.clock = clock  # the unit tests advance a fake clock; the command line reads the real one
        # Spec T1 §5: nothing that moves money runs until Series A has passed in the same run.
        # The flag exists for the unit tests, which stand up no door for Series A; the command line never clears it.
        self.require_series_a = require_series_a
        self.run_file = run_file
        self.oauth = oauth
        self.folder = folder
        self.say = say
        self.ask = ask
        self.sleep = sleep
        self.dry = dry
        self.stage2 = stage2
        self.crossing_wait = crossing_wait
        self.session_factory = session_factory
        tester_row = (run_file.get("testers") or {}).get(tester) or {}
        self.labels: Dict[str, Optional[str]] = dict(tester_row.get("agents") or {})
        self.owner_address: Optional[str] = tester_row.get("listed_address") or None
        self.payer_list_scope: str = tester_row.get("payer_list_scope") or "agent"
        self.sessions: Dict[str, Any] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}  # role -> facts from aerconnect_my_agent
        self.policy_hash: Dict[str, Optional[str]] = {}
        self.policy_hash_begin: Dict[str, Optional[str]] = {}
        self.answers: Dict[str, McpAnswer] = {}  # "<test id>|<tool>" -> the answer as received
        self.chain_said: Dict[str, Optional[str]] = {}  # role -> the chain wallet_status names
        self.pacts: Dict[str, Dict[str, Any]] = {}  # role -> the pact the Wallet states
        # A4's native-balance check, which gates money (Spec T2 §5): True it was made,
        # False the Wallet stated no balance the harness could read, None it could not be made.
        self.a4_native_balance: Optional[bool] = None
        self.series_a_gate_said: str = "Series A has not run in this run"
        self.outcomes: List[Outcome] = []
        self.walks: Dict[str, List[Dict[str, Any]]] = {}  # test id -> walk records
        self.tickets: Dict[str, List[str]] = {}
        self.hashes: List[Dict[str, Any]] = []
        self.fee_legs: List[Dict[str, Any]] = []
        self.refusals: List[Dict[str, Any]] = []
        self.usage_readings: Dict[str, Any] = {}
        self.balances_before: Dict[str, Any] = {}
        self.balances_after: Dict[str, Any] = {}
        self.stopped: Optional[str] = None
        self.stopped_reason: str = ""
        self.first_block: Dict[str, int] = {}
        self.chains: Dict[str, ChainRpc] = {}
        for name, row in (run_file.get("chains") or {}).items():
            if isinstance(row, dict) and row.get("rpc"):
                self.chains[name] = ChainRpc(name, row["rpc"], row.get("tokens") or {}, row.get("explorer", ""))
        self.series_a_passed = False
        self.started_at = now_iso()

    # -- sessions -----------------------------------------------------------
    def label_for(self, role: str) -> Optional[str]:
        label = self.labels.get(role)
        if label:
            return str(label)
        if role in ("trader", "payer"):
            return "%s-%s" % (self.tester, role)
        return None

    def session(self, role: str, test_id: str = "connect") -> Any:
        if role in self.sessions:
            return self.sessions[role]
        label = self.label_for(role)
        if label is None:
            raise HarnessError("the run file names no %s for %s" % (role, self.tester))
        if self.session_factory is not None:
            session = self.session_factory(label)
        else:
            assert self.oauth is not None
            if self.oauth.tokens(label) is None:
                self.say("No token is stored for %s; the consent runs now." % label)
                self.oauth.consent(label)
            session = Mcp(self.oauth, label, self.folder.record)
        session.initialize(test_id)
        session.tools_list(test_id)
        answer = session.call(MY_AGENT_TOOL, {}, test_id)
        facts = answer.data if isinstance(answer.data, dict) else {}
        wallet = facts.get("wallet") or {}
        agent = facts.get("agent") or {}
        self.agents[role] = {
            "label": label, "name": agent.get("name"), "role_id": agent.get("roleId"),
            "wallet_id": wallet.get("id"), "address": wallet.get("address"), "chain": wallet.get("chain"),
            "rank": (facts.get("connection") or {}).get("rank"), "raw": facts,
        }
        if self.oauth is not None and self.session_factory is None:
            stored = self.oauth.tokens(label)
            if stored:
                stored["agent"] = redact({k: v for k, v in self.agents[role].items() if k != "raw"})
                write_private(self.oauth.token_path(label), stored)
        expected_word = "trader" if role == "trader" else "payer"
        if expected_word not in str(agent.get("roleId", "")).lower():
            self.say("Note: the agent behind %s reports roleId %r, not a %s role." % (label, agent.get("roleId"), expected_word))
        self.sessions[role] = session
        return session

    def facts(self, role: str) -> Dict[str, Any]:
        return self.agents.get(role) or {}

    # -- what the Wallet says about itself (Spec T2 §1, §4, §6) ----------------
    def wallet_status(self, role: str, test_id: str) -> McpAnswer:
        """wallet_status, called as the agent, and the chain it names remembered for the role."""
        session = self.session(role, test_id)
        props = session.properties_of("wallet.wallet_status")
        args, _ = arguments_for(props, {}, self.call_facts(role))
        answer = self.remember(test_id, "wallet.wallet_status", session.call("wallet.wallet_status", args, test_id))
        data = answer.data if answer.data is not None else answer.text
        found = find_key(data, ["chain", "network"], str) if isinstance(data, (dict, list)) else None
        if isinstance(found, str) and found.strip():
            self.chain_said[role] = found.strip().lower()
        elif role not in self.chain_said:
            said = self.facts(role).get("chain")
            self.chain_said[role] = str(said).strip().lower() if said else None
        return answer

    def chain_of(self, role: str, test_id: str) -> Optional[str]:
        """The chain the agent's wallet is on, as wallet_status names it."""
        if role not in self.chain_said:
            try:
                self.wallet_status(role, test_id)
            except (HarnessError, Unreachable):
                said = self.facts(role).get("chain")
                self.chain_said[role] = str(said).strip().lower() if said else None
        return self.chain_said.get(role)

    def role_said(self, role: str) -> str:
        """
        The role the agent itself reports, which is not always the role the run file
        filed its label under: Eitan's first run was consented as a Payer under the
        Trader's label. A5 asks the question this role can ask (Spec T2 §2).
        """
        role_id = str(self.facts(role).get("role_id") or "").lower()
        if "payer" in role_id:
            return "payer"
        if "trader" in role_id:
            return "trader"
        return "payer" if role.startswith("payer") else "trader"

    def consent_notes(self, role: str) -> List[str]:
        """
        What a tester needs to be told the moment a consent lands (Spec T2 §6, §7, §9):
        whether the agent that answered is the one this label is for, and whether its
        wallet is on a chain the product offers. Both were found the hard way on
        14 September: Eitan consented a Payer under the Trader's label, and Victor's
        Trader was on a chain the product no longer offers.
        """
        out: List[str] = []
        wanted = S.ROLE_IDS.get(role, "%s.v1" % role)
        said = str(self.facts(role).get("role_id") or "")
        if said.strip().lower().split(".")[0] != wanted.split(".")[0]:
            out.append("Note: %s reports role %s, not %s. If the consent page opened with \u201cYou are already "
                       "connected\u201d, press \u201cConnect a different agent\u201d and consent the agent you meant."
                       % (self.label_for(role) or role, said or "no role", wanted))
        guard = self.chain_guard(role, "consent")
        if guard:
            out.append("Note: " + guard)
        return out

    def chain_guard(self, role: str, test_id: str) -> Optional[str]:
        """
        The chain guard (Spec T2 §6): the sentence refusing a money series to an agent
        whose wallet is on a chain the product does not offer, or None where it is on one.
        """
        chain = self.chain_of(role, test_id)
        if chain and chain in S.PRODUCT_CHAINS:
            return None
        return chain_guard_sentence(self.label_for(role) or role, chain or "no chain it would name")

    def token_balances(self, rpc: "ChainRpc", address: str) -> Dict[str, str]:
        """The ERC-20 balances read from the chain's own RPC, which is where A4 reads them (Spec T2 §4)."""
        out: Dict[str, str] = {}
        for symbol, token in rpc.tokens.items():
            try:
                out[symbol] = format_units(rpc.token_balance(token, address),
                                           rpc.token_decimals(token) or T.DECIMALS.get(symbol, 6))
            except (HarnessError, Unreachable) as err:
                out[symbol] = "not read (%s)" % err
        return out

    def call_facts(self, role: str) -> Dict[str, Any]:
        facts = self.facts(role)
        out: Dict[str, Any] = {}
        if facts.get("wallet_id"):
            out["wallet_id"] = facts["wallet_id"]
        if facts.get("role_id"):
            out["role_id"] = facts["role_id"]
        if facts.get("pact_id"):
            out["pact_id"] = facts["pact_id"]
        return out

    # -- the plan -------------------------------------------------------------
    def plan(self, series: Sequence[str], start_at: Optional[str] = None) -> List[S.Test]:
        wanted = [s for s in S.SERIES_ORDER if s in series]
        tests = S.tests_in(wanted)
        if start_at:
            if start_at not in S.BY_ID:
                raise HarnessError("no test called %s in the Series" % start_at)
            cut = S.order_key(start_at)
            tests = [t for t in tests if S.order_key(t.id) >= cut or t.series == "A"]
        if self.require_series_a and any(t.moves_money for t in tests) and not any(t.series == "A" for t in tests):
            tests = S.tests_in(["A"]) + tests
        return tests

    # -- running --------------------------------------------------------------
    def run(self, series: Sequence[str], start_at: Optional[str] = None) -> List[Outcome]:
        tests = self.plan(series, start_at)
        for index, test in enumerate(tests):
            if self.stopped:
                self.outcomes.append(Outcome(test, NOT_RUN, "not run: the series stopped at %s on an unexpected allow." % self.stopped))
                continue
            try:
                outcome = self.run_test(test)
            except KeyboardInterrupt:
                raise
            except HarnessError as err:
                outcome = Outcome(test, FAIL, "the harness could not complete this test: %s" % err,
                                  self.evidence_block(test, expected=test.rule, came_back=str(err), who="the harness itself (a fault, not a judgment)"))
            self.outcomes.append(outcome)
            if outcome.outcome != "dry":
                self.say(self.report_line(outcome))
            if test.series == "A":
                self.series_a_passed, self.series_a_gate_said = self.money_gate()
        return self.outcomes

    # Which of Series A holds money back (Spec T2 §5). A6 and A4's notes prove wording,
    # not the corridor's judgement, so they gate nothing.
    GATE_TESTS = ("A1", "A2", "A3", "A5")

    def money_gate(self) -> Tuple[bool, str]:
        """Whether Series A has passed far enough for money to move, and which tests say so."""
        missing: List[str] = []
        for test_id in self.GATE_TESTS:
            outcome = next((o for o in self.outcomes if o.test.id == test_id), None)
            if outcome is None:
                missing.append("%s has not run" % test_id)
            elif outcome.outcome not in (PASS, PASS_NOTE):
                missing.append("%s %s" % (test_id, outcome.outcome))
        if self.a4_native_balance is False:
            missing.append("A4's native-balance check fail")
        if missing:
            return False, "; ".join(missing)
        return True, "A1, A2, A3, A5 and A4's native-balance check passed; A6 and A4's notes gate nothing"

    def report_line(self, outcome: Outcome) -> str:
        detail = outcome.line or outcome.sentence
        return "%s — %s — %s" % (outcome.test.id, outcome.outcome, detail)

    def run_test(self, test: S.Test) -> Outcome:
        if test.who == S.PERSON:
            return Outcome(test, PERSON_OUT, "left to a person; the Series' text is printed in the report with a line for the outcome.")
        if test.stage2 and not self.stage2:
            return Outcome(test, SKIPPED, "Stage 2 (Ethereum); run again with --stage2 to include it.")
        if self.dry:
            return self.dry_test(test)
        if test.agent == "payer_nogas" and not self.labels.get("payer_nogas"):
            return Outcome(test, SKIPPED, "needs a Payer funded with USDC and no ETH; name it in harness_run.json under agents.payer_nogas.")
        if test.moves_money and self.require_series_a and not self.series_a_passed:
            return Outcome(test, SKIPPED, "Series A has not passed in this run, so nothing that moves money is sent "
                                          "(Spec T1 §5): %s." % self.series_a_gate_said,
                           line="held back by Series A: %s" % self.series_a_gate_said)
        if test.agent:
            self.session(test.agent, test.id)
        if test.moves_money:
            guard = self.chain_guard(test.agent, test.id)
            if guard:
                return Outcome(test, SKIPPED, guard, line=guard)
            self.snapshot_balances(test.agent, before=True)
        previous = self.outcomes[-1] if self.outcomes else None
        outcome = self.run_steps(test, previous)
        return outcome

    # -- dry run (Spec T1 §8) --------------------------------------------------
    def dry_test(self, test: S.Test) -> Outcome:
        lines: List[str] = []
        for step in test.steps:
            lines.extend(self.dry_step(test, step))
        for line in lines:
            self.say("%s — %s" % (test.id, line))
        return Outcome(test, "dry", "%d call(s) printed" % len(lines), line="%d call(s) printed, nothing sent" % len(lines))

    # What each harness-side check calls, said in a dry run.
    DRY_CHECK_CALLS = {
        "my_agent_facts": ["tools/call aerconnect_my_agent {} → expect one agent: name, the role the run file files this label under (trader.v1 or payer.v1), wallet id, address, chain, caps"],
        "wallet_names_its_chain": ["tools/call wallet.wallet_status {\"wallet_id\": \"<wallet id>\"} → expect chain one of ethereum, arbitrum, base; rails where the Wallet states them (Spec 49)"],
        "pact_hash_agrees": [
            "tools/call wallet.wallet_status {\"wallet_id\": \"<wallet id>\"} → expect pact.policy_hash",
            "tools/call police.check_action {\"action\": \"trade\", \"chain\": \"<the agent's own chain>\", \"asset\": \"USDC\", \"amount_usd\": 5, \"to_asset\": \"WETH\", \"venue\": \"uniswap_v3\", \"contract_address\": \"<the listed router for that chain>\"} → expect judged.policy_hash, whatever the verdict (a Payer asks C1's question instead: transfer_stable, 1 USDC, to the listed address)",
        ],
        "balances_vs_chain": ["[read] eth_getBalance for the agent's address on its chain, compared with wallet.get_balances' native figure, and eth_call balanceOf for each token the run file names, which get_balances cannot state (Spec 49)"],
        "usage_delta": ["tools/call wallet.my_usage {} → compared with the reading taken before D2: up by two per trade with an approval"],
        "transcript_bytes": ["[read] evidence.jsonl for D2 to D15: no quote_tx_json, no calldata, no signed bytes"],
        "crossing_arrives": ["[read] eth_getLogs Transfer to the agent's address on the destination chain, and tools/call wallet.get_crossing {\"wallet_id\": \"<wallet id>\", \"ticket_id\": \"<ticket>\"} while waiting"],
        "complete_crossing": ["tools/call wallet.get_crossing {\"wallet_id\": \"<wallet id>\", \"ticket_id\": \"<ticket from E1>\"} — only if E1 said awaiting attestation"],
        "fee_accounting": ["[read] eth_getLogs Transfer to the fee address 0xabd0235C036CBeCb911DC74958B3c8F114cec42a on arbitrum and base over the run's blocks"],
        "sentences_vs_guide": ["[compare] every refusal collected in C, D and E against the table from Guide section 10"],
        "one_hash_everywhere": ["tools/call wallet.wallet_status {\"wallet_id\": \"<wallet id>\"} → its pact.policy_hash compared with the policy hash in D2's receipt and ticket"],
    }

    def dry_step(self, test: S.Test, step: Any) -> List[str]:
        issuer = self.run_file.get("issuer", DEFAULT_ISSUER)
        facts = {"wallet_id": "<wallet id>"}
        if isinstance(step, S.Http):
            who = "(no bearer)" if not step.bearer else "(bearer)"
            return ["%s %s%s %s → expect %d" % (step.method, issuer, step.path, who, step.expect_status)]
        if isinstance(step, S.Call):
            return ["tools/call %s %s → expect words %s" % (step.tool, json.dumps(step.args, ensure_ascii=False), json.dumps(list(step.words), ensure_ascii=False))]
        if isinstance(step, S.Grep):
            return ["GET %s%s — count %s (expect 0)" % (issuer, page, json.dumps(list(step.absent))) if page != "tools/list"
                    else "tools/list — count %s (expect 0)" % json.dumps(list(step.absent)) for page in step.pages] + \
                   ["GET %s%s — count %s (expect at least 1)" % (issuer, page, json.dumps(list(words))) for page, words in step.present_on.items()]
        if isinstance(step, S.Pause):
            out = ["[pause] %s" % step.text]
            if step.hash_moves is not None:
                out.append("tools/call wallet.wallet_status {\"wallet_id\": \"<wallet id>\"} — confirm pact.policy_hash %s" % ("moved" if step.hash_moves else "did not move"))
            return out
        if isinstance(step, S.Check):
            return list(self.DRY_CHECK_CALLS.get(step.name, ["[check] %s" % step.name]))
        if isinstance(step, S.Walk):
            fields = action_fields(step.action, self.owner_address)
            out = []
            if not step.build_only:
                check_args, _ = arguments_for(None, fields, facts)
                out.append("tools/call police.check_action %s" % json.dumps(check_args, ensure_ascii=False))
            reaches_wallet = step.build_only or step.expect not in (S.PRE_FLIGHT,)
            if reaches_wallet:
                build_facts = dict(facts)
                if not step.no_receipt:
                    build_facts["police_receipt"] = "<receipt from police.check_action>"
                build_args, _ = arguments_for(None, fields, build_facts)
                out.append("tools/call wallet.build_transaction %s" % json.dumps(build_args, ensure_ascii=False))
            if not step.build_only and step.expect in (S.ALLOWED, S.ALLOWED_OR_REFUSED):
                submit_args, _ = arguments_for(None, {}, {"wallet_id": facts["wallet_id"], "ticket_id": "<ticket from wallet.build_transaction>"})
                out.append("tools/call wallet.submit_transaction %s" % json.dumps(submit_args))
            out.append("expect: %s%s%s" % (step.expect, (" — “%s”" % step.sentence) if step.sentence else "",
                                          "" if reaches_wallet else " — the build is not reached"))
            return out
        return ["[unknown step]"]

    # -- live steps ------------------------------------------------------------
    def run_steps(self, test: S.Test, previous: Optional[Outcome]) -> Outcome:
        results: List[Outcome] = []
        pool_from_refusal: Optional[str] = None
        for step in test.steps:
            if self.stopped:
                break
            if isinstance(step, S.Http):
                results.append(self.step_http(test, step, previous))
            elif isinstance(step, S.Call):
                results.append(self.step_call(test, step, previous))
            elif isinstance(step, S.Grep):
                results.append(self.step_grep(test, step, previous))
            elif isinstance(step, S.Pause):
                extra = None
                if test.id == "D7" and pool_from_refusal:
                    extra = "The pool address the refusal named: %s" % pool_from_refusal
                outcome = self.step_pause(test, step, previous, extra)
                results.append(outcome)
                if outcome.outcome == SKIPPED:
                    break
            elif isinstance(step, S.Walk):
                outcome = self.step_walk(test, step, previous)
                results.append(outcome)
                if test.id == "D7" and outcome.evidence:
                    sentence = str(outcome.evidence.get("sentence") or outcome.evidence.get("came_back") or "")
                    found = HEX40.findall(sentence)
                    pool_from_refusal = found[0] if found else None
                    if outcome.outcome in (PASS, PASS_NOTE) and matches_sentence(S.CURVE_SENTENCE, sentence) and not found:
                        results.append(Outcome(test, PASS_NOTE, "no pool holds both USDC and USDT on Arbitrum, so the listed-pool half of D7 has nothing to run; the Series calls this a pass with a note."))
                        break
            elif isinstance(step, S.Check):
                results.append(self.step_check(test, step, previous))
        return self.combine(test, results)

    def combine(self, test: S.Test, results: List[Outcome]) -> Outcome:
        if not results:
            return Outcome(test, SKIPPED, "nothing ran.")
        if len(results) == 1:
            return results[0]
        order = {FAIL: 0, HELD_OUT: 1, SKIPPED: 2, NOT_RUN: 2, PASS_NOTE: 3, PERSON_OUT: 3, PASS: 4}
        worst = min(results, key=lambda o: order.get(o.outcome, 0))
        parts = [o.sentence.strip() for o in results if o.sentence]
        sentence = "; ".join(part[:-1] if part.endswith(".") else part for part in parts)
        if sentence and not sentence.endswith("."):
            sentence += "."
        line = ", ".join(o.line or o.sentence for o in results)
        # Every note a step made is kept, not only the worst step's: A4 makes two, one for the
        # rails the Wallet does not yet name and one for the token balances it cannot state.
        notes = [o.note for o in results if o.note]
        note = None
        if len(notes) == 1:
            note = notes[0]
        elif notes:
            note = {"expected": " | ".join(str(n.get("expected")) for n in notes),
                    "got": " | ".join(str(n.get("got")) for n in notes)}
        return Outcome(test, worst.outcome, sentence, worst.evidence, note, line)

    def step_http(self, test: S.Test, step: S.Http, previous: Optional[Outcome]) -> Outcome:
        issuer = self.run_file.get("issuer", DEFAULT_ISSUER)
        url = issuer + step.path
        headers = {"Accept": "application/json, text/event-stream"}
        body = None
        if step.method == "POST":
            headers["Content-Type"] = "application/json"
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode("utf-8")
        try:
            answer = http_request(step.method, url, headers, body)
        except Unreachable as err:
            self.folder.record(test_id=test.id, kind="http", tool="%s %s" % (step.method, step.path), arguments={}, answer=str(err), http_status=None, round_trip_ms=None)
            return Outcome(test, FAIL, "%s %s did not answer." % (step.method, step.path),
                           self.evidence_block(test, "%s %s answers %d" % (step.method, step.path, step.expect_status), str(err), "nobody: the door did not answer", previous=previous))
        self.folder.record(test_id=test.id, kind="http", tool="%s %s" % (step.method, step.path), arguments={"headers": headers},
                           answer={"status": answer.status, "headers": answer.headers, "body": answer.text[:4000]},
                           http_status=answer.status, round_trip_ms=answer.elapsed_ms)
        ok = answer.status == step.expect_status
        line = "%s %s → %d" % (step.method, step.path, answer.status)
        if ok:
            return Outcome(test, PASS, "%s answered %d." % (step.path, answer.status), line=line)
        return Outcome(test, FAIL, "%s answered %d where %d was expected." % (step.path, answer.status, step.expect_status),
                       self.evidence_block(test, "%s %s answers %d" % (step.method, step.path, step.expect_status),
                                           "HTTP %d\n%s" % (answer.status, answer.text[:4000]), "the connector's HTTP route", previous=previous), line=line)

    def step_call(self, test: S.Test, step: S.Call, previous: Optional[Outcome]) -> Outcome:
        session = self.session(test.agent or "trader", test.id)
        facts = self.facts(test.agent or "trader")
        args = {k: (facts.get("wallet_id") if v == "<wallet id>" else v) for k, v in step.args.items()}
        if step.tool in (MY_AGENT_TOOL, GUIDE_TOOL):
            sent = args
        else:
            sent, _ = arguments_for(session.properties_of(step.tool), {}, self.call_facts(test.agent or "trader"))
        answer = self.remember(test.id, step.tool, session.call(step.tool, sent, test.id))
        haystack = normalise(answer.quoted())
        present = [w for w in step.words if normalise(w) in haystack]
        missing = [w for w in step.words if normalise(w) not in haystack]
        who = who_answered(answer, step.tool.split(".")[0] if "." in step.tool else "connector")
        if answer.is_error:
            return Outcome(test, FAIL, "%s answered with a refusal instead of an answer." % step.tool,
                           self.evidence_block(test, "an answer containing %s" % json.dumps(list(step.words)), answer.quoted(), who["party"], reason=who.get("reason"), sentence=who.get("sentence"), previous=previous),
                           line="%s refused" % step.tool)
        ok = answered(answer, step.words, step.any_of)
        if ok:
            return Outcome(test, PASS, "%s answered with the expected words%s." % (step.tool, (" (" + step.label + ")") if step.label else ""), line="%s answered" % step.label or step.tool)
        return Outcome(test, PASS_NOTE if present else FAIL,
                       "%s answered, but without %s." % (step.tool, json.dumps(missing)),
                       self.evidence_block(test, "an answer containing %s" % json.dumps(list(step.words)), answer.quoted(), who["party"], reason=who.get("reason"), sentence=who.get("sentence"), previous=previous),
                       note={"expected": json.dumps(list(step.words)), "got": answer.text[:600]}, line="%s: missing %s" % (step.label or step.tool, json.dumps(missing)))

    def step_grep(self, test: S.Test, step: S.Grep, previous: Optional[Outcome]) -> Outcome:
        issuer = self.run_file.get("issuer", DEFAULT_ISSUER)
        counts: Dict[str, Dict[str, int]] = {}
        texts: Dict[str, str] = {}
        for page in list(step.pages) + list(step.present_on):
            if page == "tools/list":
                session = self.session(test.agent or "trader", test.id)
                texts[page] = json.dumps(session.tools_list(test.id), ensure_ascii=False)
            else:
                answer = http_request("GET", issuer + page, {"Accept": "text/html"})
                self.folder.record(test_id=test.id, kind="http", tool="GET %s" % page, arguments={}, answer={"status": answer.status, "body_bytes": len(answer.text)}, http_status=answer.status, round_trip_ms=answer.elapsed_ms)
                texts[page] = answer.text
        problems: List[str] = []
        for page in step.pages:
            counts[page] = counts_for(texts[page], step.absent)
            for word, n in counts[page].items():
                if n:
                    problems.append("%s carries %r %d time(s)" % (page, word, n))
        for page, words in step.present_on.items():
            counts.setdefault(page, {})
            for word in words:
                n = count_word(texts[page], word)
                counts[page][word] = n
                if not n:
                    problems.append("%s does not carry %r" % (page, word))
        line = "; ".join("%s: %s" % (page, ", ".join("%s=%d" % (w, n) for w, n in row.items())) for page, row in counts.items())
        self.folder.record(test_id=test.id, kind="grep", tool="A6 counts", arguments={"absent": list(step.absent), "present_on": {k: list(v) for k, v in step.present_on.items()}}, answer=counts, http_status=None, round_trip_ms=None)
        if not problems:
            return Outcome(test, PASS, "the public pages and the tool list carry no fee word, and /terms states the trading fee; the Wallet's environment on Virginia is Albert's half.", line=line)
        return Outcome(test, FAIL, "; ".join(problems) + ".",
                       self.evidence_block(test, "guide 0, account 0, tool list 0; terms at least 1", json.dumps(counts, indent=2), "the connector's pages and tools/list", previous=previous), line=line)

    def step_pause(self, test: S.Test, step: S.Pause, previous: Optional[Outcome], extra: Optional[str] = None) -> Outcome:
        role = step.agent
        self.session(role, test.id)
        before = self.read_policy_hash(role, test.id) if step.hash_moves is not None else None
        self.say("")
        self.say("PAUSE for %s: %s" % (test.id, step.text))
        if test.id == "B3":
            for what, key in S.B3_LINES:
                self.say("  %s: %s" % (what, T.address(key)))
        if test.id == "B4":
            self.say("  The owner's listed address: %s" % (self.owner_address or "(not in the run file)"))
            self.say("  List scope for this tester: %s" % ("one list for all my agents" if self.payer_list_scope == "shared" else "a list for this agent only"))
        if extra:
            self.say("  %s" % extra)
        if before is not None:
            self.say("  Policy hash before: %s" % before)
        try:
            self.ask("Press Enter when done: ")
        except EOFError:
            return Outcome(test, SKIPPED, "no one was at the terminal to do this step, so it was skipped, not passed.")
        typed = None
        if step.ask:
            try:
                typed = self.ask(step.ask + " ")
            except EOFError:
                typed = ""
            self.folder.record(test_id=test.id, kind="typed", tool="the person's answer", arguments={"question": step.ask}, answer=typed, http_status=None, round_trip_ms=None)
        outcome = PASS
        sentence = "the owner did: %s" % step.text
        evidence = None
        note = None
        if step.hash_moves is not None:
            after, moved = self.wait_for_hash(role, before, test.id, want_change=step.hash_moves)
            if moved is None:
                return Outcome(test, SKIPPED, "the policy hash had not moved within ninety seconds and the person chose to skip; skipped, not passed.")
            if step.hash_moves and not moved:
                outcome = FAIL
                sentence = "the policy hash did not move after the save (before %s, after %s)." % (before, after)
                evidence = self.evidence_block(test, "the hash moves and wallet_status prints the new hash", "before: %s\nafter: %s" % (before, after), "the MCP Wallet's wallet_status", previous=previous, policy_hash=after)
            elif step.hash_moves is False and moved:
                outcome = FAIL
                sentence = "the policy hash moved although the save was expected to be refused (before %s, after %s)." % (before, after)
                evidence = self.evidence_block(test, "the mandate table is unchanged", "before: %s\nafter: %s" % (before, after), "the MCP Wallet's wallet_status", previous=previous, policy_hash=after)
            else:
                sentence = "the policy hash %s (before %s, after %s)." % ("moved" if moved else "did not move", before, after)
        if step.ask and step.expect_words:
            missing = [w for w in step.expect_words if normalise(w) not in normalise(typed or "")]
            if missing and outcome == PASS:
                outcome = PASS_NOTE
                note = {"expected": " ".join(step.expect_words), "got": typed or ""}
                sentence += " The page's sentence was not the one the Series gives; both are quoted."
        return Outcome(test, outcome, sentence, evidence, note, line=sentence)

    def read_policy_hash(self, role: str, test_id: str) -> Optional[str]:
        """
        The policy hash, read where it lives (Spec T2 §1): the Wallet's wallet_status, as
        `pact.policy_hash`, and get_balances' `pact_budget.policy_hash` as a second source
        where wallet_status states none. MCP Police carries no tool called can_sign.
        """
        answer = self.wallet_status(role, test_id)
        pact = wallet_pact(answer.data if answer.data is not None else answer.text)
        if not pact.get("policy_hash"):
            second = self.pact_from_balances(role, test_id)
            if second and second.get("policy_hash"):
                pact = second
        found = pact.get("policy_hash")
        self.pacts[role] = pact
        self.policy_hash[role] = found
        if role not in self.policy_hash_begin:
            self.policy_hash_begin[role] = found
        if role in self.agents and pact.get("pact_id"):
            self.agents[role]["pact_id"] = pact["pact_id"]
        return found

    def pact_from_balances(self, role: str, test_id: str) -> Optional[Dict[str, Any]]:
        """get_balances' pact_budget, the second source for the hash (Spec T2 §1)."""
        try:
            session = self.session(role, test_id)
            props = session.properties_of("wallet.get_balances")
            args, _ = arguments_for(props, {}, self.call_facts(role))
            answer = self.remember(test_id, "wallet.get_balances", session.call("wallet.get_balances", args, test_id))
        except (HarnessError, Unreachable):
            return None
        return wallet_pact(answer.data if answer.data is not None else answer.text)

    def wait_for_hash(self, role: str, before: Optional[str], test_id: str, want_change: bool) -> Tuple[Optional[str], Optional[bool]]:
        deadline = self.clock() + HASH_WAIT_SECONDS
        after = before
        while True:
            after = self.read_policy_hash(role, test_id)
            moved = hash_moved(before, after)
            if moved == want_change:
                return after, moved
            if self.clock() >= deadline:
                if not want_change:
                    return after, moved
                self.say("The policy hash has not moved within ninety seconds (still %s)." % after)
                try:
                    choice = self.ask("Wait another ninety seconds, or skip this test? [w/s] ").strip().lower()
                except EOFError:
                    choice = "s"
                if choice.startswith("w"):
                    deadline = self.clock() + HASH_WAIT_SECONDS
                    continue
                return after, None
            self.sleep(10)

    # -- the walk ---------------------------------------------------------------
    def step_walk(self, test: S.Test, step: S.Walk, previous: Optional[Outcome]) -> Outcome:
        role = test.agent
        session = self.session(role, test.id)
        facts = self.facts(role)
        if test.figure_usd is not None and step.action.amount_usd > test.figure_usd:
            raise HarnessError("refusing to send %s dollars for %s: the Series' figure is %s" % (step.action.amount_usd, test.id, test.figure_usd))
        if step.action.action == "transfer_stable" and step.action.to_address == S.OWNER and not self.owner_address:
            raise HarnessError("the run file names no listed_address for %s; the harness never invents a destination" % self.tester)
        fields = action_fields(step.action, self.owner_address)
        if step.action.chain in self.chains and step.action.chain not in self.first_block:
            try:
                self.first_block[step.action.chain] = self.chains[step.action.chain].block_number()
            except (HarnessError, Unreachable):
                pass
        if test.id == "D2" and "before_D2" not in self.usage_readings:
            self.usage_readings["before_D2"] = self.read_usage(role, test.id)
        walk: Dict[str, Any] = {"test": test.id, "label": step.label, "expect": step.expect, "action": fields, "hashes": [], "answers": []}
        self.walks.setdefault(test.id, []).append(walk)
        # 1. police.check_action
        if not step.build_only:
            props = session.properties_of("police.check_action")
            check_args, omitted = arguments_for(props, fields, self.call_facts(role))
            answer = session.call("police.check_action", check_args, test.id)
            walk["answers"].append(("police.check_action", answer))
            police = classify_police(answer)
            walk["police"] = police
            walk["omitted_at_check"] = omitted
            if police["kind"] != "allow":
                return self.judge_walk(test, step, walk, previous)
        # 2. wallet.build_transaction
        build_facts = dict(self.call_facts(role))
        if not step.no_receipt and walk.get("police", {}).get("receipt"):
            build_facts["police_receipt"] = walk["police"]["receipt"]
        props = session.properties_of("wallet.build_transaction")
        build_args, omitted = arguments_for(props, fields, build_facts)
        answer = session.call("wallet.build_transaction", build_args, test.id)
        walk["answers"].append(("wallet.build_transaction", answer))
        build = classify_wallet(answer)
        walk["build"] = build
        walk["omitted_at_build"] = omitted
        if build["kind"] != "ticket":
            return self.judge_walk(test, step, walk, previous)
        if is_unexpected_allow(step.expect, walk):
            return self.stop_on_unexpected_allow(test, step, walk, previous)
        if step.build_only:
            return self.judge_walk(test, step, walk, previous)
        ticket_id = build.get("ticket_id")
        if ticket_id:
            self.tickets.setdefault(test.id, []).append(ticket_id)
        # 3. wallet.submit_transaction — only with a ticket this run's build issued (Spec T1 §5).
        props = session.properties_of("wallet.submit_transaction")
        submit_facts = dict(self.call_facts(role))
        if ticket_id:
            submit_facts["ticket_id"] = ticket_id
        submit_args, omitted = arguments_for(props, {}, submit_facts)
        if ticket_id is None and not build.get("hashes"):
            walk["submit"] = {"kind": "unreadable", "who": build["who"], "sentence": "the ticket carried no id the harness could read"}
            return self.judge_walk(test, step, walk, previous)
        answer = session.call("wallet.submit_transaction", submit_args, test.id)
        walk["answers"].append(("wallet.submit_transaction", answer))
        submit = classify_wallet(answer)
        if submit["kind"] == "unreadable" and hex64_in(answer.text):
            submit = {"kind": "ticket", "who": submit["who"], "hashes": hex64_in(answer.text)}
        walk["submit"] = submit
        walk["omitted_at_submit"] = omitted
        if submit["kind"] == "ticket":
            candidates = [h for h in hex64_in(answer.data if answer.data is not None else answer.text)
                          if h.lower() != str(build.get("policy_hash") or "").lower() and h.lower() != str(self.policy_hash.get(role) or "").lower()]
            walk["hashes"] = self.read_hashes(test, step, candidates, facts)
        return self.judge_walk(test, step, walk, previous)

    def read_hashes(self, test: S.Test, step: S.Walk, candidates: List[str], facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        chains = [step.action.chain] + ([step.action.to_chain] if step.action.to_chain else [])
        for tx_hash in candidates:
            for chain_name in chains:
                rpc = self.chains.get(chain_name)
                if rpc is None:
                    continue
                try:
                    tx = rpc.transaction(tx_hash)
                except (HarnessError, Unreachable) as err:
                    self.say("  (%s did not answer for %s: %s)" % (chain_name, short(tx_hash), err))
                    continue
                if not tx:
                    continue
                receipt = rpc.wait_receipt(tx_hash, sleep=self.sleep)
                line = self.chain_line(test, chain_name, tx, receipt, facts)
                out.append(line)
                break
        return out

    def chain_line(self, test: S.Test, chain_name: str, tx: Dict[str, Any], receipt: Optional[Dict[str, Any]], facts: Dict[str, Any]) -> Dict[str, Any]:
        rpc = self.chains[chain_name]
        decoded = decode_call(tx.get("input") or "0x")
        transfers = transfers_in(receipt) if receipt else []
        for t in transfers:
            t["symbol"] = rpc.token_symbol(t["token"])
            t["decimals"] = rpc.token_decimals(t["token"])
            t["amount_said"] = format_units(t["amount"], t["decimals"])
        status = None
        if receipt:
            status = int(str(receipt.get("status", "0x0")), 16)
        line = {
            "test": test.id, "chain": chain_name, "hash": tx.get("hash"),
            "block": int(str(receipt.get("blockNumber")), 16) if receipt and receipt.get("blockNumber") else None,
            "status": "success" if status == 1 else ("reverted" if status == 0 else "no receipt yet"),
            "from": checksum_address(tx.get("from")) if tx.get("from") else None,
            "to": checksum_address(tx.get("to")) if tx.get("to") else None,
            "decoded": decoded, "transfers": transfers,
            "gas_used": int(str(receipt.get("gasUsed")), 16) if receipt and receipt.get("gasUsed") else None,
            "explorer": rpc.link(str(tx.get("hash"))),
        }
        self.folder.chain_line(line)
        self.hashes.append(line)
        return line

    def stop_on_unexpected_allow(self, test: S.Test, step: S.Walk, walk: Dict[str, Any], previous: Optional[Outcome]) -> Outcome:
        self.stopped = test.id
        self.stopped_reason = "an action the Series expected to be %s was built%s" % (step.expect, " and signed" if walk.get("submit") else "")
        self.say("STOP: %s — %s. Nothing further is sent until a person restarts the harness." % (test.id, self.stopped_reason))
        evidence = self.walk_evidence(test, step, walk, previous, "UNEXPECTED ALLOW: %s" % self.stopped_reason)
        return Outcome(test, FAIL, "unexpected allow: %s; the series stopped here and nothing further was sent." % self.stopped_reason, evidence, line="UNEXPECTED ALLOW, series stopped")

    def judge_walk(self, test: S.Test, step: S.Walk, walk: Dict[str, Any], previous: Optional[Outcome]) -> Outcome:
        kind = outcome_kind(walk)
        walk["kind"] = kind
        sentence_said = self.walk_sentence(walk)
        self.collect_refusal(test, walk, kind, sentence_said)
        label = step.label or step.action.action
        if kind == "no outcome":
            who = ""
            for stage in ("submit", "build", "police"):
                part = walk.get(stage)
                if part and part.get("who"):
                    who = str(part["who"].get("party", ""))
                    break
            return Outcome(test, FAIL, "%s: no judgment of the action; %s answered and the answer is quoted." % (label, who or "nobody the harness could name"),
                           self.walk_evidence(test, step, walk, previous, "no judgment of the action was given: %s answered" % (who or "no readable party")),
                           line="%s: no judgment (%s)" % (label, who or "unreadable"))
        if not kind_matches(step.expect, kind):
            if kind == S.HELD:
                return Outcome(test, HELD_OUT, "%s was held, where the Series expected %s: “%s”." % (label, step.expect, sentence_said),
                               self.walk_evidence(test, step, walk, previous, "held where %s was expected" % step.expect), line="%s held" % label)
            return Outcome(test, FAIL, "%s came out %s where the Series expected %s." % (label, kind, step.expect),
                           self.walk_evidence(test, step, walk, previous, "the outcome is of the wrong kind: expected %s, got %s" % (step.expect, kind)),
                           line="%s: %s, expected %s" % (label, kind, step.expect))
        if kind == S.ALLOWED:
            return self.judge_allowed(test, step, walk, previous, label)
        # refused or held, as expected: the sentence decides pass or pass with a note
        if step.sentence:
            if matches_sentence(step.sentence, sentence_said):
                return Outcome(test, PASS, "%s, in the Guide's words: “%s”." % (kind, sentence_said), line="%s %s" % (label, kind))
            note = {"expected": step.sentence, "got": sentence_said, "source": step.sentence_source}
            return Outcome(test, PASS_NOTE, "%s, but in different words; both sentences are quoted." % kind,
                           self.walk_evidence(test, step, walk, previous, "the sentence is not the one %s gives" % (step.sentence_source or "the Series")),
                           note, line="%s %s (different sentence)" % (label, kind))
        return Outcome(test, PASS, "%s: “%s”." % (kind, sentence_said), line="%s %s" % (label, kind))

    def judge_allowed(self, test: S.Test, step: S.Walk, walk: Dict[str, Any], previous: Optional[Outcome], label: str) -> Outcome:
        hashes = walk.get("hashes") or []
        problems: List[str] = []
        notes: List[str] = []
        facts = self.facts(test.agent)
        wallet_address = str(facts.get("address") or "")
        if not hashes:
            problems.append("submit_transaction answered but no transaction hash could be found on the chain")
        reverted = [h for h in hashes if h["status"] == "reverted"]
        if reverted:
            problems.append("reverted on chain: %s" % ", ".join(str(h["hash"]) for h in reverted))
        pending = [h for h in hashes if h["status"] == "no receipt yet"]
        if pending:
            problems.append("no receipt within %d seconds for %s" % (RECEIPT_WAIT_SECONDS, ", ".join(str(h["hash"]) for h in pending)))
        legs = walk.get("build", {}).get("legs")
        if step.legs is not None:
            if legs is not None and legs != step.legs:
                problems.append("the ticket carries %d leg(s) where %d were expected" % (legs, step.legs))
            elif legs is None and len(hashes) != step.legs and hashes:
                problems.append("%d transaction(s) came back where %d legs were expected" % (len(hashes), step.legs))
        approval = next((h for h in hashes if h["decoded"].get("function") == "approve"), None)
        swap = next((h for h in hashes if h is not approval and h["decoded"].get("function") not in ("approve", "none", "unknown")), None)
        line_parts: List[str] = []
        if approval:
            line_parts.append("approval %s" % approval["hash"])
            spender = approval["decoded"].get("args", {}).get("spender", "")
            contract = walk["action"].get("contract_address")
            if contract and spender.lower() != contract.lower():
                problems.append("the approval's spender %s is not the venue contract %s" % (spender, contract))
            sold = [t for t in (swap or {}).get("transfers", []) if t["from"].lower() == wallet_address.lower()]
            if sold and approval["decoded"].get("args", {}).get("amount") != sold[0]["amount"]:
                problems.append("the allowance %s is not the amount the swap took, %s" % (approval["decoded"]["args"]["amount"], sold[0]["amount"]))
        if swap:
            line_parts.append("%s %s" % (swap["decoded"].get("function", "tx"), swap["hash"]))
        for h in hashes:
            if h is not approval and h is not swap:
                line_parts.append("%s %s" % (h["decoded"].get("function", "tx"), h["hash"]))
        if step.fee == "expected":
            target = swap or (hashes[0] if hashes else None)
            check = fee_check(target["transfers"], T.address("FEE_ADDRESS"), wallet_address, router=target.get("to")) if target else {"ok": False, "reason": "no swap transaction"}
            walk["fee_check"] = check
            if check.get("ok"):
                rpc = self.chains.get(step.action.chain)
                decimals = rpc.token_decimals(check["token"]) if rpc else None
                symbol = rpc.token_symbol(check["token"]) if rpc else check["token"]
                line_parts.append("fee %s %s to %s" % (format_units(check["found"], decimals), symbol, short(T.address("FEE_ADDRESS"))))
                self.fee_legs.append({"test": test.id, "chain": step.action.chain, "hash": target["hash"], "token": check["token"], "symbol": symbol, "amount": check["found"], "amount_said": format_units(check["found"], decimals), "expected": check["expected"]})
            else:
                problems.append("fee: %s" % check.get("reason"))
        if step.fee == "none":
            for h in hashes:
                legs_to_fee = [t for t in h["transfers"] if t["to"].lower() == T.address("FEE_ADDRESS").lower()]
                if legs_to_fee:
                    problems.append("a transfer went to the fee address on a %s where none was expected" % step.action.action)
        if step.action.action == "transfer_stable" and hashes and self.owner_address:
            arrived = [t for h in hashes for t in h["transfers"] if t["to"].lower() == self.owner_address.lower()]
            if arrived:
                line_parts.append("%s %s arrived at %s" % (arrived[0]["amount_said"], arrived[0]["symbol"], short(self.owner_address)))
            else:
                problems.append("no token transfer to the owner's listed address was logged")
        if step.action.action == "trade" and swap:
            bought = [t for t in swap["transfers"] if t["to"].lower() == wallet_address.lower()]
            if bought:
                line_parts.append("%s %s arrived" % (bought[0]["amount_said"], bought[0]["symbol"]))
            else:
                notes.append("no token transfer to the agent's wallet was logged in the swap")
        if step.action.action == "trade" and step.action.venue == "best_direct":
            text = " ".join(a.text for _, a in walk["answers"])
            chosen = [v for v in ("uniswap_v3", "pancakeswap_v3", "curve") if v in text.lower()]
            if chosen:
                line_parts.append("chose %s" % chosen[0])
            else:
                notes.append("the answer names no exchange the harness recognises as chosen")
        line = "%s — %s" % (label, ", ".join(line_parts)) if line_parts else label
        if problems:
            return Outcome(test, FAIL, "%s was allowed and signed, but %s." % (label, "; ".join(problems)),
                           self.walk_evidence(test, step, walk, previous, "; ".join(problems)), line=line + " — " + "; ".join(problems))
        if notes:
            return Outcome(test, PASS_NOTE, "%s was allowed and signed; %s." % (label, "; ".join(notes)), None, {"expected": step.expect, "got": "; ".join(notes)}, line=line)
        return Outcome(test, PASS, "%s was allowed and signed; the chain's receipt succeeded." % label, line=line)

    def walk_sentence(self, walk: Dict[str, Any]) -> str:
        for stage in ("submit", "build", "police"):
            part = walk.get(stage)
            if part and part.get("kind") in ("deny", "hold", "held", "refused", "unreadable", "unreachable"):
                return str(part.get("sentence") or part.get("who", {}).get("sentence") or "")
        return ""

    def collect_refusal(self, test: S.Test, walk: Dict[str, Any], kind: str, sentence: str) -> None:
        if kind in (S.PRE_FLIGHT, S.AT_WALLET, S.HELD) and sentence:
            who = None
            for stage in ("submit", "build", "police"):
                part = walk.get(stage)
                if part and part.get("kind") in ("deny", "hold", "held", "refused"):
                    who = part.get("who", {}).get("party")
                    break
            guide = guide_sentence_for(sentence)
            self.refusals.append({"test": test.id, "series": test.series, "kind": kind, "who": who, "sentence": sentence,
                                  "guide_match": guide["sentence"] if guide else None, "guide_source": guide["source"] if guide else None})

    # -- checks -----------------------------------------------------------------
    def step_check(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        name = step.name
        handler = getattr(self, "check_" + name, None)
        if handler is None:
            return Outcome(test, FAIL, "the harness has no check called %s." % name)
        return handler(test, step, previous)

    def check_my_agent_facts(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        """
        A2 (Spec T2 §9): the connector acts for exactly one agent, and that agent's role is
        the one the run file files its label under — payer.v1 for `payer`, trader.v1 for
        `trader` — not the word "Trader" the Series' own text happened to use.
        """
        role = str(step.args.get("role") or test.agent or "trader")
        session = self.session(role, test.id)
        answer = session.call(MY_AGENT_TOOL, {}, test.id)
        data = answer.data if isinstance(answer.data, dict) else {}
        agent = data.get("agent") or {}
        wallet = data.get("wallet") or {}
        problems = []
        if data.get("source") != "aer-connect":
            problems.append("the answer does not say it came from aer-connect")
        if not agent.get("name"):
            problems.append("no agent name")
        wanted = S.ROLE_IDS.get(role, "%s.v1" % role)
        family = str(agent.get("roleId", "")).strip().lower().split(".")[0]
        if family != wanted.split(".")[0]:
            problems.append("roleId %r is not %s, the role the run file files %s under; if the consent page "
                            "opened with \u201cYou are already connected\u201d, press \u201cConnect a different agent\u201d "
                            "and consent the agent you meant" % (agent.get("roleId"), wanted, self.label_for(role) or role))
        for field in ("id", "address", "chain"):
            if not wallet.get(field):
                problems.append("wallet.%s is %r" % (field, wallet.get(field)))
        if not (data.get("caps") or {}).get("said"):
            problems.append("no caps sentence")
        agents_named = [k for k in data if k in ("agents",)]
        if agents_named:
            problems.append("the answer names more than one agent")
        who = who_answered(answer, "connector")
        line = "%s (%s), %s, wallet %s on %s" % (self.label_for(role), agent.get("name"), agent.get("roleId"),
                                                  short(wallet.get("address")), wallet.get("chain"))
        if problems:
            return Outcome(test, FAIL, "; ".join(problems) + ".",
                           self.evidence_block(test, "name, role %s, wallet id, address, chain and caps; no other agent" % wanted,
                                               answer.quoted(), who["party"], previous=previous), line=line)
        return Outcome(test, PASS, "aerconnect_my_agent named one agent: %s." % line, line=line)

    def a5_question(self, role: str, chain: str) -> Tuple[Optional[S.Action], str]:
        """
        The one question A5 asks: the one this agent's own role can ask, on its own chain
        (Spec T2 §2). A Payer asks C1's, a Trader asks D2's. Nothing is built and nothing
        is submitted: A5 reads the hash Police judged under, whatever the verdict.
        """
        if self.role_said(role) == "payer":
            if not self.owner_address:
                return None, "the run file names no listed_address for %s, so a Payer has no question to ask" % self.tester
            return S.pay(T.PAYMENT_USD, chain=chain), "C1's question: a one-dollar transfer_stable to the listed address"
        key = "UNISWAP_V3_%s" % chain.upper()
        if key not in T.PINNED:
            return S.trade("uniswap_v3", "", chain=chain), \
                "D2's question on %s, which has no listed Uniswap router, so none is named" % chain
        return S.trade("uniswap_v3", key, chain=chain), \
            "D2's question: a five-dollar trade on uniswap_v3 for WETH with %s" % T.address(key)

    def check_pact_hash_agrees(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        """
        A5, the one-hash check (Spec T2 §2). The Wallet's pact.policy_hash, then one
        police.check_action as the agent the run is connected as, and Police's
        judged.policy_hash read from allow, deny and hold alike. A5 compares hashes,
        not verdicts.
        """
        role = test.agent or "trader"
        session = self.session(role, test.id)
        wallet_hash = self.read_policy_hash(role, test.id)
        chain = self.chain_of(role, test.id) or str(self.facts(role).get("chain") or "arbitrum")
        action, asked = self.a5_question(role, chain)
        if action is None:
            return Outcome(test, FAIL, asked + ".", self.evidence_block(
                test, "one check_action the agent's own role can ask", asked, "the harness itself (a fault, not a judgment)",
                previous=previous, policy_hash=wallet_hash), line="no question asked; the Wallet says %s" % wallet_hash)
        fields = action_fields(action, self.owner_address)
        props = session.properties_of("police.check_action")
        args, omitted = arguments_for(props, fields, self.call_facts(role))
        answer = self.remember(test.id, "police.check_action", session.call("police.check_action", args, test.id))
        data = answer.data if answer.data is not None else answer.text
        police = classify_police(answer)
        who = who_answered(answer, "police")

        def block(expected: str, came_back: str) -> Dict[str, Any]:
            out = self.evidence_block(test, expected, came_back, who["party"], reason=who.get("reason"),
                                      sentence=who.get("sentence"), previous=previous, policy_hash=wallet_hash)
            if omitted:
                out["omitted_arguments"] = "the door's schema declared no field for: %s" % ", ".join(sorted(set(omitted)))
            out["sent"] = fields
            return out

        if judged_in(data) is None:
            return Outcome(test, FAIL, "Police's answer carried no judged block, so there is no hash to compare; its own words are quoted.",
                           block("a judged block carrying the policy hash, whatever the verdict", answer.quoted()),
                           line="%s; no judged block; the Wallet says %s" % (asked, wallet_hash))
        police_hash = judged_policy_hash(data)
        line = "%s; the Wallet says %s, Police judged under %s (verdict: %s)" % (asked, wallet_hash, police_hash, police["kind"])
        if wallet_hash and police_hash and not hash_moved(wallet_hash, police_hash):
            return Outcome(test, PASS, "the Wallet and Police carry one policy hash, %s, and Police's verdict was %s, which A5 does "
                                       "not read; compare the hash with the account page's mandate table by hand." % (wallet_hash, police["kind"]),
                           line=line)
        if not wallet_hash:
            said = "the Wallet stated no policy hash, so there is none to compare; Police judged under %s." % police_hash
        elif not police_hash:
            said = "Police's judged block carried no policy hash, so there is none to compare; the Wallet says %s." % wallet_hash
        else:
            said = "the two hashes differ: the Wallet's pact.policy_hash is %s and Police's judged.policy_hash is %s." % (wallet_hash, police_hash)
        return Outcome(test, FAIL, said,
                       block("one hash: wallet_status's pact.policy_hash and Police's judged.policy_hash",
                             json.dumps({"wallet_status pact.policy_hash": wallet_hash,
                                         "police judged.policy_hash": police_hash,
                                         "verdict": police["kind"], "asked": asked}, indent=2)), line=line)

    def check_wallet_names_its_chain(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        """
        A4's first half as the product stands (Spec T2 §4): wallet_status names the wallet's
        own chain, which must be one of the three the product offers. It does not yet name
        all three as rails — that is the Wallet's, under Spec 49 — so the absence of a `rails`
        or `transfer_rails` field is a pass with a note naming Spec 49, and never a failure.
        """
        role = test.agent or "trader"
        answer = self.wallet_status(role, test.id)
        data = answer.data if answer.data is not None else answer.text
        chain = self.chain_of(role, test.id)
        rails = find_key(data, ["rails", "transfer_rails", "transferRails"]) if isinstance(data, (dict, list)) else None
        who = who_answered(answer, "wallet")
        line = "chain %s; rails %s" % (chain, json.dumps(rails) if rails is not None else "not stated")
        if not chain:
            return Outcome(test, FAIL, "wallet_status named no chain the harness could read.",
                           self.evidence_block(test, "wallet_status names the wallet's own chain", answer.quoted(),
                                               who["party"], sentence=who.get("sentence"), previous=previous), line=line)
        if chain not in S.PRODUCT_CHAINS:
            return Outcome(test, FAIL, chain_guard_sentence(self.label_for(role) or role, chain),
                           self.evidence_block(test, "a chain the product offers: %s" % ", ".join(S.PRODUCT_CHAINS),
                                               answer.quoted(), who["party"], sentence=who.get("sentence"), previous=previous), line=line)
        if rails is None:
            return Outcome(test, PASS_NOTE, "wallet_status names the wallet's own chain, %s; it states no rails, which is the "
                                            "Wallet's under Spec 49, not the corridor's judgement." % chain,
                           note={"expected": "a rails or transfer_rails field naming ethereum, arbitrum and base",
                                 "got": "wallet_status names only the wallet's own chain, %s (Spec 49)" % chain}, line=line)
        return Outcome(test, PASS, "wallet_status names the wallet's own chain, %s, and its rails: %s." % (chain, json.dumps(rails)), line=line)

    def check_balances_vs_chain(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        """
        A4's second half (Spec T2 §4). The native balance is read from the Wallet whatever
        its JSON type — the Wallet sends a number, and asking for a string printed "None wei"
        — and compared with the chain's own eth_getBalance. The ERC-20 balances are read from
        the chain's RPC alone, because get_balances cannot state them, and the Wallet's own
        sentence is quoted in a note pointing at Spec 49. This native comparison gates money
        (Spec T2 §5); the notes do not.
        """
        role = test.agent or "trader"
        facts = self.facts(role)
        answer = self.last_answer(test.id, "wallet.get_balances")
        data = answer.data if answer is not None else None
        wallet_wei = find_key(data, ["wei"]) if isinstance(data, (dict, list)) else None
        stated = find_key(data, ["tokens", "erc20", "token_balances", "tokenBalances"], list) if isinstance(data, (dict, list)) else None
        chain_name = self.chain_of(role, test.id) or str(facts.get("chain") or "arbitrum")
        rpc = self.chains.get(chain_name)
        if not rpc or not facts.get("address"):
            self.a4_native_balance = None
            return Outcome(test, PASS_NOTE, "the run file names no RPC for %s, so the Wallet's balances were not compared with the chain's." % chain_name,
                           note={"expected": "a comparison with the chain", "got": "the run file names no RPC for %s" % chain_name},
                           line="no RPC for %s" % chain_name)
        try:
            on_chain = rpc.native_balance(str(facts["address"]))
        except (HarnessError, Unreachable) as err:
            self.a4_native_balance = None
            return Outcome(test, PASS_NOTE, "the chain did not answer for the balance comparison: %s." % err,
                           note={"expected": "a comparison with the chain", "got": str(err)}, line="the chain did not answer")
        tokens = self.token_balances(rpc, str(facts["address"]))
        erc20 = "the token balances were read from %s's own RPC: %s" % (
            chain_name, ", ".join("%s %s" % (v, k) for k, v in sorted(tokens.items())) or "the run file names no token on this chain")
        note = None
        if not stated:
            sentence = _sentence_in(data) if isinstance(data, (dict, list)) else None
            note = {"expected": "get_balances states the ERC-20 balances",
                    "got": "it does not (Spec 49); the Wallet said: \u201c%s\u201d" % (sentence or (answer.text[:400] if answer else "(no answer)"))}
        if wallet_wei is None:
            self.a4_native_balance = False
            return Outcome(test, FAIL, "get_balances stated no native balance the harness could read; %s." % erc20,
                           self.evidence_block(test, "a native balance to compare with the chain's eth_getBalance",
                                               answer.quoted() if answer else "(no answer)", "the MCP Wallet",
                                               previous=previous), note=note, line=erc20)
        self.a4_native_balance = True
        said = "the Wallet says %s wei on %s; the chain says %d wei" % (wallet_wei, chain_name, on_chain)
        agree = str(wallet_wei).strip().isdigit() and int(str(wallet_wei).strip()) == on_chain
        sentence = said + ("; they agree. " if agree else "; they are read at different moments and are quoted for comparison. ") + erc20 + "."
        if agree and note is None:
            return Outcome(test, PASS, sentence, line=said + "; " + erc20)
        if note is None:
            note = {"expected": str(on_chain) + " wei", "got": str(wallet_wei) + " wei"}
        return Outcome(test, PASS_NOTE, sentence, note=note, line=said + "; " + erc20)

    def check_usage_delta(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        role = test.agent or "trader"
        before = self.usage_readings.get("before_D2")
        after = self.read_usage(role, test.id)
        self.usage_readings["after_D3"] = after
        approvals = 0
        for tid in step.args.get("trades_with_approval_in", []):
            for walk in self.walks.get(tid, []):
                if walk.get("kind") == S.ALLOWED and any(h["decoded"].get("function") == "approve" for h in walk.get("hashes", [])):
                    approvals += 1
        expected = 2 * approvals
        if before is None:
            return Outcome(test, SKIPPED, "no my_usage reading was taken before D2 in this run, so the delta cannot be read.")
        deltas = {k: after_v - before.get(k, 0) for k, after_v in numeric_leaves(after).items() if isinstance(after_v, (int, float))}
        matching = [k for k, v in deltas.items() if v == expected and expected > 0]
        line = "%d trade(s) with an approval; expected a count up by %d; deltas: %s" % (approvals, expected, json.dumps(deltas))
        if matching:
            return Outcome(test, PASS, "my_usage's %s rose by %d, two per trade with an approval." % (matching[0], expected), line=line)
        if approvals == 0:
            return Outcome(test, SKIPPED, "no trade with an approval passed in this run, so there is no count to read.", line=line)
        return Outcome(test, FAIL, "no count in my_usage rose by exactly %d; both readings are quoted." % expected,
                       self.evidence_block(test, "the count for the day has risen by two per trade with an approval", json.dumps({"before_D2": before, "after_D3": after}, indent=2), "the MCP Wallet's my_usage", previous=previous), line=line)

    def read_usage(self, role: str, test_id: str) -> Any:
        session = self.session(role, test_id)
        props = session.properties_of("wallet.my_usage")
        args, _ = arguments_for(props, {}, self.call_facts(role))
        answer = session.call("wallet.my_usage", args, test_id)
        return answer.data if answer.data is not None else answer.text

    def check_transcript_bytes(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        wanted = set(step.args.get("tests", []))
        offenders: List[str] = []
        for entry in self.folder.evidence:
            if entry.get("test_id") not in wanted or entry.get("kind") != "tools/call":
                continue
            dumped = json.dumps(entry.get("answer"))
            if "quote_tx_json" in dumped:
                offenders.append("%s: quote_tx_json" % entry["test_id"])
            if re.search(r'"0x[0-9a-fA-F]{200,}"', dumped):
                offenders.append("%s: a long hex string that looks like calldata" % entry["test_id"])
            if re.search(r'"(signed_tx|signed_transaction|raw_tx|raw_transaction|calldata)"', dumped):
                offenders.append("%s: a field named for transaction bytes" % entry["test_id"])
        if offenders:
            return Outcome(test, FAIL, "the agent-facing answers carry transaction bytes: %s." % "; ".join(offenders),
                           self.evidence_block(test, "no quote_tx_json, no calldata, no signed bytes", "\n".join(offenders), "the MCP Wallet's tickets", previous=previous))
        return Outcome(test, PASS, "no quote_tx_json, calldata or signed bytes appear in the answers of %s." % ", ".join(sorted(wanted, key=S.order_key)))

    def check_crossing_arrives(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        walks = self.walks.get(test.id, [])
        walk = walks[step.args.get("walk", 0)] if walks else None
        if not walk or walk.get("kind") != S.ALLOWED:
            if walk and walk.get("kind") in (S.PRE_FLIGHT, S.AT_WALLET) and test.id == "E5":
                return Outcome(test, PASS, "the crossing addressed to the owner was refused, which Rule 23 permits.")
            return Outcome(test, SKIPPED, "the crossing was not allowed and signed, so there is no arrival to read.")
        facts = self.facts(test.agent)
        to_chain = walk["action"].get("to_chain")
        rpc = self.chains.get(str(to_chain))
        if rpc is None:
            return Outcome(test, PASS_NOTE, "the run file names no RPC for %s, so the arrival was not read on chain." % to_chain, note={"expected": "an arrival", "got": "no RPC"})
        never_to = step.args.get("never_to")
        forbidden = resolve_address(never_to, self.owner_address).lower() if never_to else None
        start = rpc.block_number()
        deadline = self.clock() + self.crossing_wait
        arrivals: List[Dict[str, Any]] = []
        wallet_report: Optional[McpAnswer] = None
        session = self.session(test.agent, test.id)
        while self.clock() < deadline:
            logs = rpc.logs(max(0, start - 50), [TRANSFER_TOPIC, None, pad_topic(str(facts.get("address")))])
            fresh = [l for l in logs if str(l.get("transactionHash", "")).lower() not in {h["hash"].lower() for h in self.hashes if h.get("hash")}]
            if fresh:
                for log in fresh:
                    tx_hash = str(log["transactionHash"])
                    tx = rpc.transaction(tx_hash)
                    receipt = rpc.receipt(tx_hash)
                    if tx and receipt:
                        arrivals.append(self.chain_line(test, str(to_chain), tx, receipt, facts))
                break
            try:
                props = session.properties_of("wallet.get_crossing")
                ticket = (self.tickets.get(test.id) or [None])[-1]
                args, _ = arguments_for(props, {}, {**self.call_facts(test.agent), **({"ticket_id": ticket} if ticket else {})})
                if props is not None:
                    wallet_report = session.call("wallet.get_crossing", args, test.id)
                    walk.setdefault("crossing_reports", []).append(wallet_report.text[:2000])
            except HarnessError:
                pass
            self.sleep(20)
        if forbidden:
            to_owner = [t for a in arrivals for t in a["transfers"] if t["to"].lower() == forbidden]
            if to_owner:
                self.stopped = test.id
                self.stopped_reason = "a crossing delivered to the owner's address"
                return Outcome(test, FAIL, "the crossing delivered %s to the owner's address, which Rule 23 forbids; the series stopped." % to_owner[0]["amount_said"],
                               self.walk_evidence(test, S.Walk(S.CCTP_CROSSING, S.ALLOWED_OR_REFUSED), walk, previous, "delivered to the named address"))
        if not arrivals:
            return Outcome(test, FAIL, "no arrival at the agent's address on %s within %d seconds; the Wallet's last report is quoted." % (to_chain, int(self.crossing_wait)),
                           self.evidence_block(test, "the arrival on %s within minutes" % to_chain, wallet_report.quoted() if wallet_report else "(no report)", "the destination chain and the MCP Wallet's get_crossing", previous=previous))
        first = arrivals[0]
        got = [t for t in first["transfers"] if t["to"].lower() == str(facts.get("address", "")).lower()]
        said = "%s %s arrived on %s in %s (%s)" % (got[0]["amount_said"] if got else "?", got[0]["symbol"] if got else "", to_chain, first["hash"], first["decoded"].get("function"))
        return Outcome(test, PASS, said + ".", line=said)

    def check_complete_crossing(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        source = step.args.get("from", "E1")
        walks = self.walks.get(source, [])
        text = " ".join(a.text for w in walks for _, a in w.get("answers", []))
        text += " ".join(r for w in walks for r in w.get("crossing_reports", []))
        if "awaiting attestation" not in text.lower():
            return Outcome(test, PERSON_OUT, "E1 completed at once, so the awaiting-attestation road did not arise here; forcing it is Albert's on Virginia.")
        session = self.session(test.agent, test.id)
        props = session.properties_of("wallet.get_crossing")
        ticket = (self.tickets.get(source) or [None])[-1]
        args, _ = arguments_for(props, {}, {**self.call_facts(test.agent), **({"ticket_id": ticket} if ticket else {})})
        answer = session.call("wallet.get_crossing", args, test.id)
        hashes = hex64_in(answer.text)
        if hashes and not answer.is_error:
            return Outcome(test, PASS, "get_crossing completed the crossing and reported %s." % hashes[0], line="get_crossing %s" % hashes[0])
        who = who_answered(answer, "wallet")
        return Outcome(test, FAIL, "get_crossing did not report a completing hash.",
                       self.evidence_block(test, "get_crossing finishes the crossing", answer.quoted(), who["party"], reason=who.get("reason"), sentence=who.get("sentence"), previous=previous))

    def check_fee_accounting(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        expected_legs = [leg for leg in self.fee_legs if leg["test"] in set(step.args.get("tests", []))]
        found_all: List[Dict[str, Any]] = []
        problems: List[str] = []
        others: List[str] = []
        for chain_name in step.args.get("chains", []):
            rpc = self.chains.get(chain_name)
            if rpc is None or chain_name not in self.first_block:
                continue
            try:
                logs = rpc.logs(self.first_block[chain_name], [TRANSFER_TOPIC, None, pad_topic(T.address("FEE_ADDRESS"))])
            except (HarnessError, Unreachable) as err:
                problems.append("%s did not answer eth_getLogs: %s" % (chain_name, err))
                continue
            for log in logs:
                found_all.append({"chain": chain_name, "hash": str(log.get("transactionHash")), "token": checksum_address(str(log.get("address"))),
                                  "amount": int(str(log.get("data") or "0x0"), 16)})
        for leg in expected_legs:
            hit = [f for f in found_all if f["hash"].lower() == str(leg["hash"]).lower() and f["amount"] == leg["amount"]]
            if not hit:
                problems.append("the fee leg of %s (%s, %s units) was not found among the fee address's incoming transfers" % (leg["test"], leg["hash"], leg["amount"]))
        for f in found_all:
            if not any(f["hash"].lower() == str(leg["hash"]).lower() for leg in self.fee_legs):
                others.append("%s %s %d units" % (f["chain"], f["hash"], f["amount"]))
        line = "%d fee leg(s) of this run found among %d incoming transfer(s) in the run's block window" % (len(expected_legs) - len([p for p in problems if "was not found" in p]), len(found_all))
        if not expected_legs:
            return Outcome(test, SKIPPED, "no trade with a fee passed in this run, so there is no fee leg to account for.", line=line)
        if problems:
            return Outcome(test, FAIL, "; ".join(problems) + ".",
                           self.evidence_block(test, "the fee address's incoming transfers are exactly the fee legs of D2, D3, D5 and D15", json.dumps({"expected": expected_legs, "found": found_all}, indent=2), "the chains' own Transfer logs", previous=previous), line=line)
        if others:
            return Outcome(test, PASS_NOTE, "every fee leg of this run is on chain; %d other incoming transfer(s) sit in the same window (another tester's run, or not) and are listed." % len(others),
                           None, {"expected": "only this run's fee legs", "got": "; ".join(others)}, line=line)
        return Outcome(test, PASS, "every fee leg of this run is on chain at the fee address, each five basis points of its trade's output, and nothing else arrived in the window.", line=line)

    def check_sentences_vs_guide(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        wanted = set(step.args.get("series", []))
        collected = [r for r in self.refusals if r["series"] in wanted]
        matched = [r for r in collected if r["guide_match"]]
        unmatched = [r for r in collected if not r["guide_match"]]
        line = "%d refusal(s) collected, %d in Guide section 10's words, %d new" % (len(collected), len(matched), len(unmatched))
        if not collected:
            return Outcome(test, SKIPPED, "no refusal was collected in C, D or E in this run.", line=line)
        if unmatched:
            return Outcome(test, PASS_NOTE, "%s; the new sentences are listed for the guide's version 1.2." % line, None,
                           {"expected": "every refusal in Guide section 10's words", "got": " | ".join("%s: %s" % (r["test"], r["sentence"]) for r in unmatched)}, line=line)
        return Outcome(test, PASS, line + ".", line=line)

    def check_one_hash_everywhere(self, test: S.Test, step: S.Check, previous: Optional[Outcome]) -> Outcome:
        source = step.args.get("test", "D2")
        walks = [w for w in self.walks.get(source, []) if w.get("kind") == S.ALLOWED]
        if not walks:
            return Outcome(test, SKIPPED, "%s did not pass in this run, so there is no receipt and ticket to compare." % source)
        walk = walks[0]
        receipt_hash = (walk.get("police") or {}).get("policy_hash")
        ticket_hash = (walk.get("build") or {}).get("policy_hash")
        wallet_hash = self.read_policy_hash(test.agent or "trader", test.id)
        found = {"receipt": receipt_hash, "ticket": ticket_hash, "wallet_status": wallet_hash}
        present = {k: v for k, v in found.items() if v}
        line = ", ".join("%s %s" % (k, v) for k, v in found.items())
        if len(present) == 3 and len(set(present.values())) == 1:
            return Outcome(test, PASS, "the receipt, the ticket and the Wallet's pact carry one policy hash, %s; the engine's verdict on P0 and the account page are read by hand." % wallet_hash, line=line)
        if len(set(present.values())) > 1:
            return Outcome(test, FAIL, "the policy hashes differ: %s." % line, self.evidence_block(test, "one hash in the receipt, the ticket and the Wallet's pact", json.dumps(found, indent=2), "MCP Police's receipt and the MCP Wallet's ticket and wallet_status", previous=previous), line=line)
        return Outcome(test, PASS_NOTE, "not every answer carried a policy hash the harness could read: %s." % line, None, {"expected": "three hashes", "got": line}, line=line)

    # -- evidence ---------------------------------------------------------------
    def remember(self, test_id: str, tool: str, answer: McpAnswer) -> McpAnswer:
        """The last answer each tool gave in each test, kept as received, so a later check reads
        the door's own words rather than the redacted line written to the evidence file."""
        self.answers["%s|%s" % (test_id, tool)] = answer
        return answer

    def last_answer(self, test_id: str, tool: str) -> Optional[McpAnswer]:
        remembered = self.answers.get("%s|%s" % (test_id, tool))
        if remembered is not None:
            return remembered
        for entry in reversed(self.folder.evidence):
            if entry.get("test_id") == test_id and entry.get("tool") == tool:
                return McpAnswer(entry.get("http_status") or 0, entry.get("answer"), json.dumps(entry.get("answer"), ensure_ascii=False), entry.get("round_trip_ms") or 0)
        return None

    def evidence_block(self, test: S.Test, expected: str, came_back: str, who: str, reason: Optional[str] = None,
                       sentence: Optional[str] = None, previous: Optional[Outcome] = None, policy_hash: Optional[str] = None,
                       receipt_id: Optional[str] = None, ticket_id: Optional[str] = None, hashes: Optional[List[Dict[str, Any]]] = None,
                       comparison: str = "") -> Dict[str, Any]:
        facts = self.facts(test.agent) if test.agent else {}
        secrets_ = self.secrets()
        return {
            "expected": expected,
            "came_back": redact(came_back, secrets_),
            "who": who,
            "reason": reason,
            "sentence": redact(sentence, secrets_) if sentence else sentence,
            "receipt_id": receipt_id,
            "ticket_id": ticket_id,
            "policy_hash": policy_hash or self.policy_hash.get(test.agent or ""),
            "wallet_address": facts.get("address"),
            "chain": facts.get("chain"),
            "hashes": hashes or [],
            "previous": "%s — %s — %s" % (previous.test.id, previous.outcome, previous.sentence) if previous else "none (this was the first test of the run)",
            "where": "Answered by %s; %s%s." % (who, test.where, ("; " + comparison) if comparison else ""),
        }

    def secrets(self) -> List[str]:
        out: List[str] = []
        for session in self.sessions.values():
            out.extend(getattr(session, "secrets_seen", []) or [])
        # Every answer a check quoted, whether or not it was part of a walk: A5's one
        # check_action returns a receipt on an allow, and its evidence quotes the answer whole.
        for answer in self.answers.values():
            out.extend(secret_values(answer.body))
        for walks in self.walks.values():
            for walk in walks:
                token = (walk.get("police") or {}).get("receipt")
                if isinstance(token, str) and len(token) >= 8:
                    out.append(token)
        return out

    def walk_evidence(self, test: S.Test, step: S.Walk, walk: Dict[str, Any], previous: Optional[Outcome], comparison: str) -> Dict[str, Any]:
        came_back = "\n\n".join("%s answered:\n%s" % (tool, answer.quoted()) for tool, answer in walk.get("answers", []))
        who_part = None
        for stage in ("submit", "build", "police"):
            part = walk.get(stage)
            if part and part.get("who"):
                who_part = part
                break
        who = who_part.get("who", {}) if who_part else {}
        police = walk.get("police") or {}
        build = walk.get("build") or {}
        expected = "%s%s" % (step.expect, (" — “%s” (%s)" % (step.sentence, step.sentence_source)) if step.sentence else "")
        block = self.evidence_block(test, expected, came_back, who.get("party", "unknown"), who.get("reason"), who.get("sentence"), previous,
                                    police.get("policy_hash") or build.get("policy_hash"), police.get("receipt_id"), build.get("ticket_id"), walk.get("hashes"), comparison)
        omitted = (walk.get("omitted_at_check") or []) + (walk.get("omitted_at_build") or [])
        if omitted:
            block["omitted_arguments"] = "the door's schema declared no field for: %s" % ", ".join(sorted(set(omitted)))
        block["sent"] = walk.get("action")
        return block

    # -- balances ---------------------------------------------------------------
    def snapshot_balances(self, role: str, before: bool) -> None:
        facts = self.facts(role)
        address = facts.get("address")
        if not address:
            return
        target = self.balances_before if before else self.balances_after
        if before and role in target:
            return
        row: Dict[str, Any] = {"address": address}
        for name, rpc in self.chains.items():
            try:
                chain_row: Dict[str, str] = {"ETH": format_units(rpc.native_balance(str(address)), 18)}
                for symbol, token in rpc.tokens.items():
                    chain_row[symbol] = format_units(rpc.token_balance(token, str(address)), rpc.token_decimals(token) or T.DECIMALS.get(symbol, 6))
                row[name] = chain_row
            except (HarnessError, Unreachable) as err:
                row[name] = {"error": str(err)}
        target[role] = row

    def finish(self) -> str:
        for role in list(self.agents):
            if not self.dry:
                self.snapshot_balances(role, before=False)
        return self.folder.write_report(self.report())

    # -- the report (Spec T1 §6) ------------------------------------------------
    def report(self) -> str:
        counts: Dict[str, int] = {}
        for o in self.outcomes:
            counts[o.outcome] = counts.get(o.outcome, 0) + 1
        lines: List[str] = []
        lines.append("# Corridor harness run — %s — %s" % (self.tester, self.started_at))
        lines.append("")
        lines.append("Spec T1 as amended by Spec T2 (14 September 2026); Series version 1.0 (13 September 2026), A4, A5 and A6 "
                     "amended 14 September 2026. A failure below is evidence, not a verdict: the harness never guesses at a cause.")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append("Outcomes: " + ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())) + ".")
        if self.stopped:
            lines.append("")
            lines.append("**The series stopped at %s: %s. Nothing further was sent.**" % (self.stopped, self.stopped_reason))
        lines.append("")
        for role, facts in self.agents.items():
            pact = self.pacts.get(role) or {}
            lines.append("- %s (%s): %s, role %s, wallet %s on %s. Pact %s, state %s, policy generation %s. "
                         "Policy hash at the start %s, at the end %s (read from the MCP Wallet's wallet_status, pact.policy_hash)." % (
                             role, facts.get("label"), facts.get("name"), facts.get("role_id"), facts.get("address"),
                             self.chain_said.get(role) or facts.get("chain"),
                             pact.get("pact_id") or facts.get("pact_id") or "not stated",
                             pact.get("state") or "not stated",
                             pact.get("policy_generation") if pact.get("policy_generation") is not None else "not stated",
                             self.policy_hash_begin.get(role), self.policy_hash.get(role)))
        series_a = next((o for o in self.outcomes if o.test.series == "A" and o.test.agent), None)
        if series_a is not None:
            ran_as = series_a.test.agent
            lines.append("")
            lines.append("Series A ran as %s, the run file's %s; the agent itself reported role %s." % (
                self.label_for(ran_as), ran_as, self.facts(ran_as).get("role_id")))
        lines.append("")
        lines.append("What gates money (Spec T2 §5): A1, A2, A3, A5 and A4's native-balance check. A6 and A4's "
                     "notes prove wording, not the corridor's judgement, and hold nothing back. This run: %s." %
                     self.series_a_gate_said)
        moved = sum(w["action"].get("amount_usd", 0) for walks in self.walks.values() for w in walks if w.get("kind") == S.ALLOWED)
        lines.append("")
        lines.append("Total moved by allowed actions: %s dollars (the Series' figures, as sent)." % moved)
        if self.balances_before or self.balances_after:
            lines.append("")
            lines.append("Balances before and after, read on the chains' own RPC:")
            for role in sorted(set(self.balances_before) | set(self.balances_after)):
                lines.append("- %s before: %s" % (role, json.dumps(self.balances_before.get(role), sort_keys=True)))
                lines.append("- %s after: %s" % (role, json.dumps(self.balances_after.get(role), sort_keys=True)))
        lines.append("")
        lines.append("Fee legs found on chain: %s" % (", ".join("%s %s %s in %s" % (l["test"], l["amount_said"], l["symbol"], l["hash"]) for l in self.fee_legs) or "none"))
        lines.append("")
        lines.append("Every transaction hash in the run:")
        for h in self.hashes:
            lines.append("- %s %s %s %s (%s) %s" % (h["test"], h["chain"], h["hash"], h["status"], h["decoded"].get("function"), h.get("explorer", "")))
        if not self.hashes:
            lines.append("- none")
        lines.append("")
        lines.append("## Tests, in Series order")
        for o in self.outcomes:
            lines.append("")
            lines.append("### %s — %s" % (o.test.id, o.test.title))
            lines.append("")
            lines.append("Rule: %s" % o.test.rule)
            lines.append("")
            lines.append("Outcome: **%s**. %s" % (o.outcome, o.sentence))
            if o.test.who == S.PERSON:
                lines.append("")
                lines.append(o.test.text)
                lines.append("")
                lines.append("Outcome, written by the person: ____________________________________________")
            if o.note:
                lines.append("")
                lines.append("Note — expected: “%s”" % o.note.get("expected"))
                lines.append("Note — got: “%s”" % o.note.get("got"))
            if o.evidence:
                lines.extend(self.render_evidence(o.evidence))
        notes = [o for o in self.outcomes if o.outcome == PASS_NOTE and o.note]
        lines.append("")
        lines.append("## F3 — every pass with a note, collected")
        lines.append("")
        if not notes:
            lines.append("None.")
        for o in notes:
            lines.append("- %s: expected “%s”; got “%s”" % (o.test.id, o.note.get("expected"), o.note.get("got")))
        if self.refusals:
            lines.append("")
            lines.append("Refusals collected in C, D and E against Guide section 10:")
            for r in self.refusals:
                lines.append("- %s (%s, %s): “%s” — %s" % (r["test"], r["kind"], r["who"], r["sentence"], ("matches: " + r["guide_match"]) if r["guide_match"] else "not in section 10; note for version 1.2"))
        lines.append("")
        lines.append("## Left to a person")
        lines.append("")
        for t in S.TESTS:
            if t.who == S.PERSON and not any(o.test.id == t.id for o in self.outcomes):
                lines.append("### %s — %s" % (t.id, t.title))
                lines.append("")
                lines.append(t.text)
                lines.append("")
                lines.append("Outcome, written by the person: ____________________________________________")
                lines.append("")
        lines.append("")
        lines.append("Files: evidence.jsonl (every call, redacted), chain.jsonl (every hash decoded).")
        return "\n".join(lines) + "\n"

    @staticmethod
    def render_evidence(block: Dict[str, Any]) -> List[str]:
        out = ["", "Evidence:", ""]
        out.append("1. The Series expected: %s" % block.get("expected"))
        out.append("2. What came back, whole:")
        out.append("")
        out.append("```")
        out.append(str(block.get("came_back")))
        out.append("```")
        out.append("")
        who = block.get("who")
        reason = block.get("reason")
        sentence = block.get("sentence")
        out.append("3. Who answered: %s%s%s" % (who, (" — reason field: %s" % reason) if reason else "", (" — sentence: “%s”" % sentence) if sentence else ""))
        out.append("4. Receipt id %s, ticket id %s, policy hash %s." % (block.get("receipt_id"), block.get("ticket_id"), block.get("policy_hash")))
        out.append("5. Wallet address %s on %s." % (block.get("wallet_address"), block.get("chain")))
        hashes = block.get("hashes") or []
        out.append("6. Transaction hashes: %s" % (", ".join("%s (%s)" % (h.get("hash"), h.get("status")) for h in hashes) or "none"))
        out.append("7. The previous test: %s" % block.get("previous"))
        if block.get("omitted_arguments"):
            out.append("   Note: %s" % block["omitted_arguments"])
        if block.get("sent"):
            out.append("   Sent (the Guide's vocabulary, before the door's schema shaped it): %s" % json.dumps(block["sent"]))
        out.append("8. Where to read: %s" % block.get("where"))
        return out


def count_word(text: str, word: str) -> int:
    if re.fullmatch(r"[A-Za-z]+", word):
        return len(re.findall(r"\b%s\b" % re.escape(word), text, re.I))
    return len(re.findall(re.escape(word), text, re.I))


def counts_for(text: str, words: Sequence[str]) -> Dict[str, int]:
    """How many times each word appears on one page: A6's count, word by word."""
    return {word: count_word(text, word) for word in words}


def fee_word_counts(text: str) -> Dict[str, int]:
    """A6's pin (Spec T2 §3): the fee's own words, and never "basis points" on its own."""
    return counts_for(text, S.FEE_WORDS)


def fee_words_found(text: str) -> int:
    """How many pinned fee words a page carries in all. A6 expects 0 on /guide, /account and tools/list."""
    return sum(fee_word_counts(text).values())


# ---------------------------------------------------------------------------
# The command line (Spec T1 §8).
# ---------------------------------------------------------------------------
def load_run_file(path: str, say: Callable[[str], None]) -> Dict[str, Any]:
    existing = read_json(path)
    if existing:
        return existing
    skeleton = default_run_file()
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(skeleton, handle, indent=2)
    say("Wrote %s for you to complete: the owner's listed address per tester and the agent labels." % path)
    return skeleton


def dry_lines(series: Sequence[str], run_file: Optional[Dict[str, Any]] = None, tester: str = "dry", start_at: Optional[str] = None) -> List[str]:
    """Every call the harness would make, in order, with no network (Spec T1 §8, §11)."""
    lines: List[str] = []
    folder = RunFolder(RUNS_DIR, tester, dry=True)
    runner = Runner(tester, run_file or default_run_file(), None, folder, say=lines.append, ask=lambda _q: "", dry=True, stage2=True)
    runner.run(series, start_at)
    return [line for line in lines if not line.startswith("STOP")]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="The Corridor Harness: runs the acceptance series as the agent (Spec T1).")
    parser.add_argument("--tester", help="which tester's agents to run as (a key under testers in the run file)")
    parser.add_argument("--series", nargs="*", default=list(S.SELECTABLE_SERIES), choices=list(S.SELECTABLE_SERIES), help="which series to run (default all of A B C D E F H)")
    parser.add_argument("--from", dest="start_at", help="resume at a test id, for example D7")
    parser.add_argument("--dry", action="store_true", help="print every call the harness would make, without connecting")
    parser.add_argument("--consent", metavar="LABEL", help="run only the consent for one agent: trader, payer or payer_nogas")
    parser.add_argument("--run-file", default=os.path.join(STORE_DIR, "harness_run.json"), help="the run file (default ~/.corridor-harness/harness_run.json)")
    parser.add_argument("--issuer", default=None, help="the connector's issuer (default from the run file, else %s)" % DEFAULT_ISSUER)
    parser.add_argument("--stage2", action="store_true", help="include the Stage 2 test on Ethereum (E3)")
    parser.add_argument("--out", default=RUNS_DIR, help="where run folders are written (default ~/Downloads/harness-runs)")
    parser.add_argument("--crossing-wait", type=float, default=CROSSING_WAIT_SECONDS, help="seconds to wait for a crossing to arrive")
    args = parser.parse_args(argv)

    if args.dry:
        run_file = read_json(args.run_file) or default_run_file()
        if args.issuer:
            run_file["issuer"] = args.issuer
        for line in dry_lines(args.series, run_file, args.tester or "dry", args.start_at):
            print(line)
        print("Dry run: nothing was sent.")
        return 0

    if not args.tester:
        parser.error("--tester is required unless --dry")
    run_file = load_run_file(args.run_file, print)
    issuer = args.issuer or run_file.get("issuer") or DEFAULT_ISSUER
    run_file["issuer"] = issuer
    oauth = Oauth(issuer)
    testers = run_file.get("testers") or {}
    if args.tester not in testers:
        print("The run file names no tester called %s; the testers are %s." % (args.tester, ", ".join(testers) or "none"))
        return 2

    if args.consent:
        label = (testers[args.tester].get("agents") or {}).get(args.consent) or "%s-%s" % (args.tester, args.consent)
        folder = RunFolder(args.out, args.tester)
        runner = Runner(args.tester, run_file, oauth, folder, stage2=args.stage2)
        # --consent always runs the consent again: it is the road to a fresh connection for this label.
        oauth.consent(label)
        runner.session(args.consent, "consent")
        facts = runner.facts(args.consent)
        print("Connected as %s: %s (%s), wallet %s at %s on %s." % (label, facts.get("name"), facts.get("role_id"), facts.get("wallet_id"), facts.get("address"), facts.get("chain")))
        for line in runner.consent_notes(args.consent):
            print(line)
        hash_now = runner.read_policy_hash(args.consent, "consent")
        pact = runner.pacts.get(args.consent) or {}
        print("Policy hash now: %s (the Wallet's wallet_status, pact.policy_hash). Pact %s, state %s, policy generation %s." % (
            hash_now, pact.get("pact_id") or "not stated", pact.get("state") or "not stated",
            pact.get("policy_generation") if pact.get("policy_generation") is not None else "not stated"))
        print("Evidence: %s" % os.path.join(folder.path, "evidence.jsonl"))
        return 0

    folder = RunFolder(args.out, args.tester)
    runner = Runner(args.tester, run_file, oauth, folder, stage2=args.stage2, crossing_wait=args.crossing_wait)
    try:
        runner.run(args.series, args.start_at)
    except KeyboardInterrupt:
        print("Interrupted; the report is written with what ran.")
    finally:
        path = runner.finish()
        print("Report: %s" % path)
    return 1 if runner.stopped or any(o.outcome == FAIL for o in runner.outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
