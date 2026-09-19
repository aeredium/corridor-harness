"""
THE ESTATE HARNESS'S PINNED TABLES (Spec T7): every address the estate harness may ever send,
and the one figure that decides where a payee's address lives.

Nothing here is a real counterparty's. Every address is DERIVED by the harness from a fixed
seed — keccak-256 of the seed and a label, the last twenty bytes, spelled with the EIP-55
checksum the payee road accepts (`packages/shared/src/payeeaddress.ts`: 0x followed by exactly
forty hexadecimal characters; the estate stores the lower-case form and treats mixed case as a
checksum, not an identity) — and every one of them is labelled a test address. A test proves
that none of them is any of the corridor's pinned addresses (`tables.py`, the venue contracts,
the fee address, the testers' destinations).

The ONE venue address S11 sends on purpose — to prove the estate's answer to a payee whose
address is a real exchange contract — is read from the corridor's `tables.py` AT RUN TIME
(`venue_address_for_probe`) and is never written here: the harness must never be able to
whitelist one by accident, and a table that does not hold it cannot be misread into doing so.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, NamedTuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corridor_harness import checksum_address, keccak256  # noqa: E402  the corridor's own keccak and EIP-55

# The seed every test address is derived from. Changing it changes every address at once,
# which is the point: no address here was ever typed, so none can be a real one mistyped.
SEED = "aer360-harness test addresses — Spec T7, 19 September 2026"

# The chain a payee's address lives on, and where that word comes from. The harness answers
# C9 (the networks beside Aeredium) with 'Ethereum'; the compiler lower-cases the choice into
# the chain allowlist (`onboardingcompiler.ts`, chainAllowlist), and `packages/shared/src/chains.ts`
# names the chain `ethereum` (family evm, chain id 1). The sandbox's own network,
# `aeredium-testnet`, is not in that registry, so the payee road (`isKnownChain`) would refuse
# a payee address declared on it; the harness records which networks the compiled charter names.
PAYEE_CHAIN = "ethereum"
C9_NETWORK_CHOICE = "Ethereum"


class Derived(NamedTuple):
    """One test address: the bytes, what it stands for, and the label it was derived from."""

    address: str
    what: str
    label: str


def derive_address(label: str, seed: str = SEED) -> str:
    """A checksummed EVM address from the seed and a label: keccak-256, last twenty bytes, EIP-55."""
    digest = keccak256(("%s|%s" % (seed, label)).encode("utf-8"))
    return checksum_address("0x" + digest[-20:].hex())


def _pin(label: str, what: str) -> Derived:
    return Derived(derive_address(label), what, label)


PINNED: Dict[str, Derived] = {
    "NORTHWIND_ETHEREUM": _pin("Northwind Supplies/ethereum", "the test payee Northwind Supplies, on ethereum"),
    "CONTOSO_ETHEREUM": _pin("Contoso Legal/ethereum", "the test payee Contoso Legal, on ethereum"),
    # The address S11 spells with a wrong checksum: derived here, mis-cased on purpose in `wrong_checksum`.
    "CHECKSUM_PROBE_ETHEREUM": _pin("Checksum probe/ethereum", "a test address S11 sends with its checksum broken"),
}

# The addresses S7's second payment may go to: on nobody's list, declared a one-off, expected to
# wait (Spec 69). Spec 69 pauses a NEW destination, and the estate counts a destination it has ever
# paid — in any run not rejected — as old (`setgates.ts`, isDestinationNew). So six are pinned, and
# a run pays the first one the estate's runs register has never seen; a seventh run says so and
# reuses the first.
UNLISTED_KEYS: List[str] = ["UNLISTED_ETHEREUM"] + ["UNLISTED_ETHEREUM_%d" % n for n in range(2, 7)]
for _n, _key in enumerate(UNLISTED_KEYS, 1):
    PINNED[_key] = _pin("Unlisted destination %d/ethereum" % _n, "test address %d on nobody's list, paid once to prove the wait" % _n)

# The two payees of the whitelist (Spec T7, "The estate, its people and its money").
PAYEES: List[Dict[str, str]] = [
    {"key": "NORTHWIND_ETHEREUM", "name": "Northwind Supplies", "chain": PAYEE_CHAIN},
    {"key": "CONTOSO_ETHEREUM", "name": "Contoso Legal", "chain": PAYEE_CHAIN},
]

# The asset the payments are made in, and its decimals as `packages/shared/src/money.ts` knows them.
PAYMENT_ASSET = "USDC"
ASSET_DECIMALS = {"USDC": 6, "USDT": 6, "ETH": 18, "WETH": 18, "DAI": 18}


def address(key: str) -> str:
    """The pinned bytes for a table key. A key that is not pinned is a bug, and it throws."""
    if key not in PINNED:
        raise KeyError("no test address called %s" % key)
    return PINNED[key].address


def describe(key: str) -> str:
    row = PINNED[key]
    return "%s — %s (derived from the seed and the label %r)" % (row.address, row.what, row.label)


def is_pinned(addr: Optional[str]) -> bool:
    if not addr:
        return False
    low = addr.lower()
    return any(row.address.lower() == low for row in PINNED.values())


def wrong_checksum(addr: str) -> str:
    """
    The same address with its EIP-55 checksum broken: the first letter's case is flipped, so the
    string still names the same bytes but no longer spells the checksum. Refused by a door that
    checks EIP-55; accepted by one that lower-cases (the estate's, by its own account).
    """
    body = addr[2:]
    for index, ch in enumerate(body):
        if ch.isalpha():
            flipped = ch.lower() if ch.isupper() else ch.upper()
            return "0x" + body[:index] + flipped + body[index + 1:]
    raise ValueError("an address with no letters has no checksum to break: %s" % addr)


def is_checksummed(addr: str) -> bool:
    """Whether a mixed-case address spells its own EIP-55 checksum."""
    if not isinstance(addr, str) or len(addr) != 42 or not addr.startswith("0x"):
        return False
    try:
        int(addr[2:], 16)
    except ValueError:
        return False
    return checksum_address(addr) == addr


def venue_address_for_probe(key: str = "UNISWAP_V3_ETHEREUM") -> Dict[str, str]:
    """
    THE ONE VENUE ADDRESS S11 SENDS ON PURPOSE, read from the corridor's own table at run time
    and never from this file. Refuses if the corridor's row is somehow one of ours.
    """
    import tables as corridor  # the corridor harness's pinned table, beside this file

    venue = corridor.address(key)
    if is_pinned(venue):
        raise RuntimeError("the corridor's %s is one of the estate harness's own test addresses; refusing" % key)
    return {"address": venue, "what": corridor.PINNED[key].what, "source": corridor.PINNED[key].source, "key": key}


def corridor_addresses() -> List[str]:
    """Every address the corridor's table pins, lower-cased, so a test can prove none is ours."""
    import tables as corridor

    return [row.address.lower() for row in corridor.PINNED.values()]


def minor_units(amount: str, decimals: int) -> str:
    """A decimal amount to a string of minor units, by string arithmetic — no float anywhere."""
    text = amount.strip()
    if not text or text.startswith("-"):
        raise ValueError("an amount is a positive plain decimal: %r" % amount)
    whole, _, fraction = text.partition(".")
    if not whole.isdigit() or (fraction and not fraction.isdigit()):
        raise ValueError("an amount is a plain decimal: %r" % amount)
    if len(fraction) > decimals:
        raise ValueError("%r has %d decimal places but %s carries %d" % (amount, len(fraction), PAYMENT_ASSET, decimals))
    return str(int(whole + fraction.ljust(decimals, "0")))
