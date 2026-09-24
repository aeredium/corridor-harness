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
    # --- the one tester's listed destination the Series itself names, by role (Spec T5) ---
    "TESTER_LISTED": Pinned(
        "0xfec697fc2D4323aE7618BFF2347C01E29653FB57",
        "one tester's listed destination, the owner's own wallet (B4)",
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


# ---------------------------------------------------------------------------
# THE REHEARSAL (Spec P1d, 24 September 2026): the corridor's first sponsored
# operation, walked by the harness's own agent on the tester's own road — Police,
# Wallet, platform, gateway, chain — and judged in dollars against the chain's
# receipt (`corridor_harness.py rehearse`). Nothing pinned here is a secret. The
# agent's bearer, the sandbox account's credential and the admin credential are
# read from files outside the repository, named below by file and key and never
# by value; no file of this repository holds a bearer, a credential or a key.
# ---------------------------------------------------------------------------
class PublicRpc(NamedTuple):
    """One keyless public JSON-RPC endpoint the rehearsal may READ a receipt from, and where it was read."""

    url: str
    what: str
    source: str


# The chain the rehearsal may walk, and the public RPC it reads `eth_getTransactionReceipt`
# from (standard library, reads only). A chain not named here is refused by name: the
# corridor's first sponsored operation is on Arbitrum One (P1c deploys the paymaster there).
REHEARSAL_RPC: Dict[str, PublicRpc] = {
    "arbitrum": PublicRpc(
        "https://arb1.arbitrum.io/rpc",
        "Arbitrum One's own public JSON-RPC endpoint (chain 42161), keyless; the harness only reads from it",
        "Arbitrum docs, 'RPC endpoints and providers', Arbitrum One row; the same endpoint the run-file skeleton "
        "has named since Spec T1 §3 (corridor_harness.default_run_file)",
    ),
}

# The harness's own agent on AER Connect: the sandbox the rehearsal walks as. Its wallet is a
# key allocated on the platform and held in the enclave, born with the agent on the owner's
# account page (the Wallet's mint road, Spec 66 §1); the harness holds no key for it and only
# ever speaks to it through the Police and the Wallet under the agent's own OAuth consent.
SANDBOX: Dict[str, str] = {
    # The consent label. The bearer lives in ~/.corridor-harness/<label>.json (mode 600), written by
    # the consent and never by hand — exactly where the series stores every agent's tokens.
    "label": "harness-payer",
    # The platform account the harness's owner pays with: the `account_id` GET /v1/gas-account names
    # for the sandbox's credential, and the `{id}` of the admin credit road. Pinned by Bear from the
    # first run's own reading; while it is empty the rehearsal names the id the platform states and stops.
    "account_id": "",
    # The wallet's address as the Wallet's live key record states it (`wallet_status` → `account.address`,
    # Spec 66 §1 as amended: the address the key signs from). Pinned by Bear from the first consent; the
    # rehearsal reads the live record every run and refuses to go on where the two differ. It is the one
    # destination the rehearsal sends to: the wallet's own address (Spec T1 §5 — a destination comes from
    # the pinned tables or the run file, and from nowhere else).
    "wallet_address": "",
}

# The sandbox account's platform credential (the account's own key), read from
# ~/.corridor-harness/sandbox.env, never printed. The platform admits it on GET /v1/gas-account and
# GET /v1/gas/operations/{userOpHash} (aegiskey-access-platform internal/api/gas_handlers.go,
# gasCredentialAuth: an account key or an agent's pact credential; a service identity on the read alone).
SANDBOX_ENV_FILE = "sandbox.env"
SANDBOX_ENV_KEY_KEY = "AAP_ACCOUNT_KEY"

# The admin credential, exactly as Spec T14 names it (aer360_tables.py; AERAccounts .env.example): the
# file Bear keeps under ~/.aer360-harness/, the platform's base URL and the admin key — never in the
# repository, never printed. tests/test_rehearsal.py proves these agree with aer360_tables.py.
ADMIN_ENV_DIR = "~/.aer360-harness"
ADMIN_ENV_FILE = "admin.env"
ADMIN_ENV_URL_KEY = "AAP_ADMIN_BASE_URL"
ADMIN_ENV_KEY_KEY = "AAP_ADMIN_KEY"

# The platform's roads the rehearsal asks (aegiskey-access-platform internal/api/router.go, Spec 154, 154c).
ADMIN_CREDIT_ROUTE = "/v1/admin/accounts/%s/gas-account/credits"  # the admin credit road: the account's id (Spec 154 §1)
GAS_ACCOUNT_ROUTE = "/v1/gas-account"                              # the balance, with the ledger's recent lines (Spec 154 §2)
GAS_OPERATION_ROUTE = "/v1/gas/operations/%s"                      # one operation by its userOpHash, or a delegation by its transaction hash (Spec 154 §6, 154c §4)

# The rehearsal's figures (SPEC.md §2, §3): the send, the credit, the balance the credit is made below,
# the poll, the deadline. The reason and the idempotency key carry the run id, the UTC start time.
REHEARSAL_SEND_USD = 0.01
REHEARSAL_SEND_ASSET = "USDC"
REHEARSAL_CREDIT_USD_CENTS = 500
REHEARSAL_CREDIT_BELOW_USD_CENTS = 100
REHEARSAL_INTERVAL_SECONDS = 5.0
REHEARSAL_DEADLINE_SECONDS = 180.0
REHEARSAL_REASON = "rehearsal %s"
REHEARSAL_IDEMPOTENCY_KEY = "rehearsal-%s"
RUN_ID_FORMAT = "%Y%m%d-%H%M%S"


def format_usd_cents(cents: Any) -> str:
    """The platform's own spelling of money (internal/gas/dollars.go FormatUSD): US$12.34, no grouping, a leading minus."""
    n = int(cents)
    negative = n < 0
    n = -n if negative else n
    return "%sUS$%d.%02d" % ("-" if negative else "", n // 100, n % 100)


def parse_env_file(text: str) -> Dict[str, str]:
    """A shell-style environment file, as Spec T14 reads admin.env: KEY=value lines, an optional `export`, quotes stripped, comments and blanks ignored."""
    out: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        out[key.strip()] = value
    return out
