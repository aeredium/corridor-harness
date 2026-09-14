"""
THE PINNED TABLES: every address the harness may ever send, and where each was read.

Spec T1 section 5: the harness never sends a destination address, venue contract
or fee address from anywhere but two places — the owner's listed address in the
run file, and the tables pinned here, carried verbatim from the Series and the
Owner's Guide with the page each was read from. Nothing in this file is composed
at run time and nothing here is remembered: each line names its source so a
reader can open the document and check the bytes.

Documents:
  Series  — "AER Connect Corridor Acceptance Test Series before Sale, version 1.0,
            13 September 2026" (a verbatim copy rides in tests/fixtures/series-1.0.md).
  Guide   — "AER Connect Owner's Guide, version 1.1, 13 September 2026".
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional


class Pinned(NamedTuple):
    """One pinned address: the bytes, what it is, and the page it was read from."""

    address: str
    what: str
    source: str


PINNED: Dict[str, Pinned] = {
    # --- the exchange contracts a Trader lists (Series §4 B3; Guide §5 table) ---
    "UNISWAP_V3_ETHEREUM": Pinned(
        "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "Uniswap v3 SwapRouter02 on Ethereum",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'Uniswap v3 (SwapRouter02) | Ethereum'",
    ),
    "UNISWAP_V3_ARBITRUM": Pinned(
        "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "Uniswap v3 SwapRouter02 on Arbitrum",
        "Series §4 B3 and §3 A3; Owner's Guide v1.1 §5, table row 'Uniswap v3 (SwapRouter02) | Arbitrum'",
    ),
    "UNISWAP_V3_BASE": Pinned(
        "0x2626664c2603336E57B271c5C0b26F421741e481",
        "Uniswap v3 SwapRouter02 on Base",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'Uniswap v3 (SwapRouter02) | Base'",
    ),
    "PANCAKESWAP_V3_ETHEREUM": Pinned(
        "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "PancakeSwap v3 SmartRouter on Ethereum",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'PancakeSwap v3 (SmartRouter) | Ethereum'",
    ),
    "PANCAKESWAP_V3_ARBITRUM": Pinned(
        "0x32226588378236Fd0c7c4053999F88aC0e5cAc77",
        "PancakeSwap v3 SmartRouter on Arbitrum",
        "Series §4 B3 and §6 D5; Owner's Guide v1.1 §5, table row 'PancakeSwap v3 (SmartRouter) | Arbitrum'",
    ),
    "PANCAKESWAP_V3_BASE": Pinned(
        "0x678Aa4bF4E210cf2166753e054d5b7c31cc7fa86",
        "PancakeSwap v3 SmartRouter on Base",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'PancakeSwap v3 (SmartRouter) | Base'",
    ),
    # --- the crossing contracts (Series §4 B3; Guide §5 second table) ---
    "CCTP_TOKEN_MESSENGER_V2": Pinned(
        "0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d",
        "Circle CCTP TokenMessengerV2, the same address on Ethereum, Arbitrum and Base",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'USDC — Circle CCTP (TokenMessengerV2)'",
    ),
    "USDT0_ETHEREUM": Pinned(
        "0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee",
        "Tether USDT0 (OFT) on Ethereum",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'USDT — Tether USDT0 (OFT) | Ethereum'",
    ),
    "USDT0_ARBITRUM": Pinned(
        "0x14E4A1B13bf7F943c8ff7C51fb60FA964A298D92",
        "Tether USDT0 (OFT) on Arbitrum",
        "Series §4 B3; Owner's Guide v1.1 §5, table row 'USDT — Tether USDT0 (OFT) | Arbitrum'",
    ),
    # --- the addresses the Series sends on purpose to be refused ---
    "OLD_UNISWAP_ROUTER": Pinned(
        "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "the older Uniswap router, which the Wallet does not use (D14)",
        "Series §6 D14; Owner's Guide v1.1 §5, 'Do not list the older Uniswap router'",
    ),
    "DEAD_ADDRESS": Pinned(
        "0x000000000000000000000000000000000000dEaD",
        "an address on nobody's list, paid to prove the refusal (C2)",
        "Series §5 C2",
    ),
    # --- the fee address Series F reads back ---
    "FEE_ADDRESS": Pinned(
        "0xabd0235C036CBeCb911DC74958B3c8F114cec42a",
        "the agents' trading-fee address on Arbitrum and Base",
        "Series §8 F2",
    ),
    # --- a tester's listed destination the Series itself names ---
    "VICTOR_LISTED": Pinned(
        "0xfec697fc2D4323aE7618BFF2347C01E29653FB57",
        "Victor's listed destination, his own wallet (B4)",
        "Series §4 B4",
    ),
}

# The eight lines of the Trader's list, in the order B3 writes them (Series §4 B3).
TRADER_LIST_B3: List[str] = [
    "UNISWAP_V3_ARBITRUM",  # SwapRouter02 on Ethereum and Arbitrum is one address
    "UNISWAP_V3_BASE",
    "PANCAKESWAP_V3_ETHEREUM",
    "PANCAKESWAP_V3_ARBITRUM",
    "PANCAKESWAP_V3_BASE",
    "CCTP_TOKEN_MESSENGER_V2",
    "USDT0_ETHEREUM",
    "USDT0_ARBITRUM",
]

# The Series' figures (Series §2 and the tests that name another figure). The
# harness refuses to send any amount that is not the figure the Series wrote for
# that test; see `series.py` where each test carries its own.
TRADE_USD = 5
PAYMENT_USD = 1
FEE_BPS = 5  # five basis points on the output of a trade (Series §2, §8 F2)

# The chains the Series runs on, as the corridor spells them (Guide §7–§9).
CHAINS = ("arbitrum", "base", "ethereum")

# Token decimals by symbol, for reading a figure aloud. A token the harness has
# not heard of is read in raw units and its symbol and decimals are asked of the
# chain itself (`symbol()`/`decimals()`), never guessed.
DECIMALS = {"USDC": 6, "USDT": 6, "PYUSD": 6, "EURC": 6, "WETH": 18, "ETH": 18}


def address(key: str) -> str:
    """The pinned bytes for a table key. A key that is not pinned is a bug, and it throws."""
    if key not in PINNED:
        raise KeyError("no pinned address called %s" % key)
    return PINNED[key].address


def source(key: str) -> str:
    return PINNED[key].source


def describe(key: str) -> str:
    """One line for a report: the address, what it is, and where it was read."""
    row = PINNED[key]
    return "%s — %s (read from %s)" % (row.address, row.what, row.source)


def is_pinned(addr: Optional[str]) -> bool:
    """Whether an address is one of the pinned bytes, compared case-insensitively."""
    if not addr:
        return False
    low = addr.lower()
    return any(row.address.lower() == low for row in PINNED.values())
