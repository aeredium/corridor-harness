"""
THE SERIES AS DATA: every test the Acceptance Series names, and nothing it does not.

Spec T1 section 10: `series.py` holds the tests as data — id, rule, words, tool
arguments, expected kind, expected sentence, pause text. The text of each test is
the Series' own, verbatim, so the report can print it for the person who runs the
tests the harness leaves to a person (Spec T1 §4), and the unit tests prove that
every id here is in the Series document and every id in the document is here.

The document: "AER Connect Corridor Acceptance Test Series before Sale, version
1.0, 13 September 2026" (the Series). The sentences a refusal is matched against
come from the AER Connect Owner's Guide v1.1 §10, transcribed below with the
Guide's own ellipses and angle brackets, which the matcher treats as wildcards.

Nothing here decides a cause. A test carries the party and the rule under which
its answer can be checked — the "where-to-read" line of a failure — and no more.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
# The five kinds of expected outcome (Spec T1 §7), plus the two unions a test
# in the Series states without naming the judge.
# ---------------------------------------------------------------------------
ALLOWED = "allowed and signed"
PRE_FLIGHT = "refused at pre-flight"
AT_WALLET = "refused at the Wallet"
HELD = "held"
ANSWERED = "answered"
KINDS = (ALLOWED, PRE_FLIGHT, AT_WALLET, HELD, ANSWERED)

# Unions the Series itself leaves open: "Refused" without naming the judge, and
# E5's "either ignores the address ... or refuses".
REFUSED = "refused (by either judge)"
ALLOWED_OR_REFUSED = "allowed to the agent's own address, or refused"

# Who runs a test (Spec T1 §4): the harness by itself, the harness with a pause
# for the owner's passkey, or a person.
HARNESS = "harness"
PAUSE = "pause"
PERSON = "person"

# Placeholders resolved at run time. They are the ONLY way a destination reaches
# an argument: a table key from tables.py, or the owner's address from the run
# file (Spec T1 §5).
OWNER = "<owner's listed address>"


@dataclass
class Action:
    """One corridor action in the Guide's own vocabulary (Guide §7, §8, §9)."""

    action: str  # transfer_stable | trade | bridge_stable
    chain: str
    asset: str
    amount_usd: float
    to_address: Optional[str] = None  # OWNER, or a tables.py key
    to_asset: Optional[str] = None
    venue: Optional[str] = None
    contract_address: Optional[str] = None  # a tables.py key, or "" for empty
    to_chain: Optional[str] = None


@dataclass
class Walk:
    """One walk of the corridor: police.check_action, wallet.build_transaction, wallet.submit_transaction."""

    action: Action
    expect: str
    sentence: Optional[str] = None  # the expected sentence, with … and <…> as wildcards
    sentence_source: str = ""  # where the sentence is written
    legs: Optional[int] = None  # the number of legs the ticket must carry
    fee: Optional[str] = None  # "expected" (five basis points to the fee address) | "none"
    build_only: bool = False  # C3: build without a receipt, no check_action first
    no_receipt: bool = False  # C3: send no police_receipt at all
    label: str = ""  # a short label for the report line


@dataclass
class Pause:
    """A pause for the owner's passkey (Spec T1 §4): one sentence saying exactly what to do."""

    text: str
    agent: str  # whose policy hash is read afterwards: trader | payer
    hash_moves: Optional[bool] = True  # True: must change; False: must not; None: not read
    ask: Optional[str] = None  # a question whose typed answer is recorded verbatim
    expect_words: Sequence[str] = ()  # words expected in the typed answer, if any


@dataclass
class Call:
    """One tool call with an 'answered' expectation: the text contains the given words."""

    tool: str
    args: Dict[str, Any]
    words: Sequence[str]
    label: str = ""
    any_of: bool = False  # True: any one word suffices; False: every word must appear


@dataclass
class Http:
    """A plain HTTP probe (A1)."""

    method: str
    path: str
    expect_status: int
    bearer: bool = False


@dataclass
class Grep:
    """A word count over public pages and the tool list (A6)."""

    pages: Sequence[str]
    absent: Sequence[str]
    present_on: Dict[str, Sequence[str]]  # page -> words that must appear


@dataclass
class Check:
    """A check the harness makes from what it already holds (D4, D16, E2, F2, F3, F4, A2, A4, A5)."""

    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Test:
    id: str
    title: str
    rule: str  # the clause the test proves, from the Series
    text: str  # the Series' own paragraph, verbatim
    who: str  # HARNESS | PAUSE | PERSON
    series: str
    steps: List[Any] = field(default_factory=list)
    says: str = ""  # the words said to Claude, from the Series
    agent: str = ""  # trader | payer | payer_nogas | "" (no agent needed)
    where: str = ""  # the part and the rule a failure is read under
    moves_money: bool = False
    stage2: bool = False
    figure_usd: Optional[float] = None  # the Series' own figure for this test


# ---------------------------------------------------------------------------
# The Owner's Guide §10, transcribed. Each sentence in the Guide's own words,
# with the Guide's ellipses and angle brackets, and the remedy the Guide gives.
# ---------------------------------------------------------------------------
GUIDE_SECTION_10: List[Dict[str, str]] = [
    {
        "kind": "destination",
        "sentence": "This action names no destination…",
        "remedy": "add the address under Set limits.",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "destination",
        "sentence": "The destination … is not on this agent's list",
        "remedy": "add the address under Set limits.",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "venue",
        "sentence": "The venue contract … is not on this agent's list",
        "remedy": "add the exchange's address from section 5 for that chain.",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "best_direct",
        "sentence": "best_direct may choose <exchange>, whose contract … is not on this agent's list; list it, or remove <exchange>…",
        "remedy": "do one or the other.",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "hold",
        "sentence": "owner approval required before ticket can be minted",
        "remedy": "the amount met your \"ask me first\" figure; raise it, or test smaller (section 4).",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "allowance",
        "sentence": "the dry-run failed on <chain>: … insufficient allowance / TRANSFER_FROM_FAILED",
        "remedy": "the one-time approval has not yet been signed; re-save your limits form once (section 4), then run again.",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "gas",
        "sentence": "signing address … has … wei native balance; need at least …",
        "remedy": "the agent's wallet needs gas on that chain (section 6).",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "to_asset",
        "sentence": "a trade must name the asset it buys in to_asset",
        "remedy": "tell the agent what to buy.",
        "source": "Owner's Guide v1.1 §10",
    },
    {
        "kind": "curve",
        "sentence": "curve … has no pool …",
        "remedy": "list the pool (section 5), or choose another exchange.",
        "source": "Owner's Guide v1.1 §10",
    },
]

# Sentences the Series and the Guide quote outside §10, matched the same way.
OTHER_SENTENCES: List[Dict[str, str]] = [
    {
        "kind": "not_wired",
        "sentence": "this door trades directly on uniswap_v3, pancakeswap_v3, curve, best_direct; <name> is not yet wired to it.",
        "source": "Owner's Guide v1.1 §7; Series §6 D11",
    },
    {
        "kind": "not_stablecoin",
        "sentence": "… is not a stablecoin this door transfers on <chain>…",
        "source": "Series §5 C7",
    },
    {
        "kind": "no_pool",
        "sentence": "curve on arbitrum has no pool holding both USDC and USDT that this door could quote",
        "source": "Series §6 D7",
    },
    {
        "kind": "no_rail",
        "sentence": "no rail is configured for <chain> on this door… so this…",
        "source": "Series §9 G2",
    },
    {
        "kind": "form_choice",
        "sentence": "Say whether this list is for this agent only or for all your agents. Nothing was sent.",
        "source": "Series §4 B1; Owner's Guide v1.1 §4",
    },
]

# A6 pins the fee, not the word (Spec T2 §3). The phrase "basis points" is NOT here:
# MCP Police's check_action schema uses it for `slippage_bps` ("Declared maximum
# slippage, in basis points") and `price_deviation_bps`, and neither is the fee, so
# counting it made A6 fail on the corridor's own tool list. Each of these is the fee
# itself, and "fee" is counted as a whole word: `sweepTokenWithFee`, `fee_recipient`
# and `feeRecipient` carry it with a word character on one side, so each is pinned
# in its own right.
FEE_WORDS: Sequence[str] = ("fee", "0.05%", "five basis points", "5 bps", "sweepTokenWithFee",
                            "fee_recipient", "feeRecipient")

# The series that walk the corridor with money, which the chain guard refuses whole for
# an agent on a chain the product does not offer (Spec T2 §6). Series B is the owner's
# road: its form and list tests stand whatever chain the wallet is on, save B8, which
# walks the corridor and is caught by its own moves_money flag. Series A moves nothing
# and always runs. F reads back what the money series did; where they did not run, its
# checks say so in their own words.
MONEY_SERIES = ("C", "D", "E", "H")

# The chains the product offers (Spec T2 §6). An agent whose wallet is on any other
# chain is refused every money series, in the sentence the harness gives.
PRODUCT_CHAINS = ("ethereum", "arbitrum", "base")

# The role each label's agent must report, by the key the run file files it under
# (Spec T2 §9). A2 reads the role the agent itself states against this.
ROLE_IDS = {"trader": "trader.v1", "payer": "payer.v1", "payer_nogas": "payer.v1"}

# The B3 lines a pause reads aloud, keys into tables.py in the Series' order.
B3_LINES = [
    ("Uniswap SwapRouter02 on Ethereum and Arbitrum", "UNISWAP_V3_ARBITRUM"),
    ("Uniswap on Base", "UNISWAP_V3_BASE"),
    ("PancakeSwap SmartRouter on Ethereum", "PANCAKESWAP_V3_ETHEREUM"),
    ("PancakeSwap SmartRouter on Arbitrum", "PANCAKESWAP_V3_ARBITRUM"),
    ("PancakeSwap SmartRouter on Base", "PANCAKESWAP_V3_BASE"),
    ("Circle CCTP TokenMessengerV2", "CCTP_TOKEN_MESSENGER_V2"),
    ("Tether USDT0 on Ethereum", "USDT0_ETHEREUM"),
    ("Tether USDT0 on Arbitrum", "USDT0_ARBITRUM"),
]


# ---------------------------------------------------------------------------
# Reusable actions, in the Guide's vocabulary. Amounts are the Series' figures.
# ---------------------------------------------------------------------------
def pay(amount: float, to: str = OWNER, chain: str = "arbitrum", asset: str = "USDC") -> Action:
    return Action(action="transfer_stable", chain=chain, asset=asset, amount_usd=amount, to_address=to)


def trade(venue: str, contract: Optional[str], to_asset: Optional[str] = "WETH", amount: float = 5,
          chain: str = "arbitrum", asset: str = "USDC") -> Action:
    return Action(action="trade", chain=chain, asset=asset, amount_usd=amount, to_asset=to_asset,
                  venue=venue, contract_address=contract)


def bridge(asset: str, to_chain: str, amount: float = 5, chain: str = "arbitrum",
           to_address: Optional[str] = None) -> Action:
    return Action(action="bridge_stable", chain=chain, asset=asset, amount_usd=amount,
                  to_chain=to_chain, to_address=to_address)


UNISWAP_ARBITRUM_TRADE = trade("uniswap_v3", "UNISWAP_V3_ARBITRUM")
PANCAKE_ARBITRUM_TRADE = trade("pancakeswap_v3", "PANCAKESWAP_V3_ARBITRUM")
CURVE_ARBITRUM_TRADE = trade("curve", "", to_asset="USDT")
BEST_DIRECT_TRADE = trade("best_direct", "", to_asset="USDT")
CCTP_CROSSING = bridge("USDC", "base")

HOLD_SENTENCE = "owner approval required before ticket can be minted"
DESTINATION_SENTENCE = "The destination … is not on this agent's list"
VENUE_SENTENCE = "The venue contract … is not on this agent's list"
BEST_DIRECT_SENTENCE = "best_direct may choose <exchange>, whose contract … is not on this agent's list; list it, or remove <exchange>…"
GAS_SENTENCE = "signing address … has … wei native balance; need at least …"
TO_ASSET_SENTENCE = "a trade must name the asset it buys in to_asset"
NOT_WIRED_SENTENCE = "this door trades directly on uniswap_v3, pancakeswap_v3, curve, best_direct; <name> is not yet wired to it."
NOT_STABLECOIN_SENTENCE = "… is not a stablecoin this door transfers on <chain>…"
CURVE_SENTENCE = "curve … has no pool …"
NO_SERVE_SENTENCE = "… does not serve …"


def restore(agent: str, what: str) -> Pause:
    return Pause("Open Set limits for the %s, %s, and save with your passkey; then press Enter." % (agent, what),
                 agent=agent, hash_moves=True)


# ---------------------------------------------------------------------------
# THE TESTS, IN SERIES ORDER. `text` is the Series' own paragraph, verbatim.
# ---------------------------------------------------------------------------
TESTS: List[Test] = [
    # ---------------- Series A — readiness, no money moves ----------------
    Test(
        id="A1", series="A", who=HARNESS, title="The public door",
        rule="Proves the door is up and closed to strangers.",
        text="**A1. The public door.** From any computer: `https://mcppro.aeredium.io/.well-known/oauth-authorization-server` answers 200, `/healthz` answers 200, an unauthenticated POST to `/mcp` answers 401. Proves the door is up and closed to strangers. Evidence: the three status codes.",
        steps=[
            Http("GET", "/.well-known/oauth-authorization-server", 200),
            Http("GET", "/healthz", 200),
            Http("POST", "/mcp", 401),
        ],
        where="Answered by the connector's OAuth road and its MCP route (apps/server/src/routes/oauth.ts, routes/mcp.ts) under Series A1",
    ),
    Test(
        id="A2", series="A", who=HARNESS, agent="trader", title="Claude connects as one agent",
        rule="Proves the connector acts for exactly one agent (Rule 17, Rule 21).",
        text="**A2. Claude connects as one agent.** In Claude, with AER Connect connected as the Trader, ask: *\"Which agent are you?\"* Claude calls `my_agent` and answers with the agent's name, role Trader, wallet id, address and chain, and the caps written on its policy entry. It names no other agent. Proves the connector acts for exactly one agent (Rule 17, Rule 21). Evidence: the answer.",
        says="Which agent are you?",
        steps=[Check("my_agent_facts")],
        where="Answered by AER Connect's own tool aerconnect_my_agent (services/mcprelay.ts, myAgentAnswer) under Rule 17 and Rule 21; the role is read against the label the run file gives this agent (Spec T2 §9)",
    ),
    Test(
        id="A3", series="A", who=HARNESS, agent="trader", title="The guide is inside the MCP",
        rule="Proves Spec 39 and Rule 13.",
        text="**A3. The guide is inside the MCP.** Ask Claude: *\"Which address do I list for Uniswap on Arbitrum?\"* then *\"Can my trader send money back to me?\"* then *\"What is not yet built?\"* Each answer comes from `aerconnect_guide`, cites the AER Connect Owner's Guide v1.1 with its section, gives `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` for the first, says plainly that a Trader cannot send and that funds cannot yet leave for the second, and lists the hold page, the return road, Curve as a class, more exchanges, more chains and USDT to Base for the third. Proves Spec 39 and Rule 13. Evidence: the three answers.",
        says="Which address do I list for Uniswap on Arbitrum? / Can my trader send money back to me? / What is not yet built?",
        steps=[
            Call("aerconnect_guide", {"question": "Which address do I list for Uniswap on Arbitrum?"},
                 ["0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", "Owner's Guide v1.1", "§5"], label="Uniswap on Arbitrum"),
            Call("aerconnect_guide", {"question": "Can my trader send money back to me?"},
                 ["cannot send", "no road by which money leaves", "Owner's Guide v1.1"], label="a Trader cannot send"),
            Call("aerconnect_guide", {"question": "What is not yet built?"},
                 ["answer a hold", "return an agent", "Curve", "Exchanges beyond the three", "Chains beyond the three",
                  "USDT crossings to or from Base", "§12"], label="not yet built"),
        ],
        where="Answered by AER Connect's own tool aerconnect_guide from packages/shared/src/knowledge.ts under Spec 39 and Rule 13",
    ),
    Test(
        id="A4", series="A", who=HARNESS, agent="trader", title="The Wallet names its rails",
        rule="Proves Rule 18.",
        text="**A4. The Wallet names its rails.** Ask Claude: *\"What chains can your wallet reach, and what are my balances?\"* Claude calls `wallet_status` and `get_balances`. `wallet_status` names the wallet's own chain, which must be one of ethereum, arbitrum and base; it does not yet name all three as rails, so a missing `rails` or `transfer_rails` field is a pass with a note pointing at Spec 49, not a failure. The native balance the Wallet states is compared with the chain's own `eth_getBalance`, whether the Wallet sends it as a JSON number or as a string. The token balances are compared with the Wallet's statement where it makes one: for each token `get_balances` states in `tokens.balances` (Spec 49) that the run file names, the Wallet's `raw` figure is compared with the chain's own `balanceOf` for that contract, and the Wallet's `tokens.road` sentence is printed after the balances; where `get_balances` states no tokens, they are read from the chain's own RPC alone and the Wallet's own sentence is quoted in a note. Proves Rule 18. Evidence: the answer, compared with the chain's balances.",
        says="What chains can your wallet reach, and what are my balances?",
        steps=[
            Check("wallet_names_its_chain"),
            Call("wallet.get_balances", {"wallet_id": "<wallet id>"}, ["wallet"], label="balances"),
            Check("balances_vs_chain"),
        ],
        where="Answered by the MCP Wallet's wallet_status and get_balances under Rule 18 as Spec 49 leaves them; the native balance is compared with the chain's own eth_getBalance and the token balances with the Wallet's own statement in tokens.balances where it makes one, else read from the chain alone (Spec T3)",
    ),
    Test(
        id="A5", series="A", who=HARNESS, agent="trader", title="The Wallet and Police agree on the pact's hash",
        rule="Proves Rule 4, one pact one hash.",
        text="**A5. The Wallet and Police agree on the pact's hash.** Ask Claude: *\"Which policy are you signing under right now?\"* MCP Police carries no tool called `can_sign`, so the hash is read from the Wallet: `wallet_status` states it as `pact.policy_hash`. The harness then makes one `check_action` as the agent the run is connected as, with a question that fits its role and its own chain — a Payer asks C1's, a one-dollar `transfer_stable` to the listed address; a Trader asks D2's, a five-dollar `trade` on `uniswap_v3` for WETH with the listed router — and reads `judged.policy_hash` from Police's answer whatever the verdict: allow, deny and hold all carry it. The two hashes are the same string. A5 compares hashes, not verdicts, and fails in Police's own words where the answer carries no `judged` block. The same hash appears in the account page's mandate table for that agent. Proves Rule 4, one pact one hash. Evidence: the two hashes side by side. Cost: one metered `check_action` unit.",
        says="Which policy are you signing under right now?",
        steps=[Check("pact_hash_agrees")],
        where="Answered by the MCP Wallet's wallet_status (pact.policy_hash) and MCP Police's check_action (judged.policy_hash) under Rule 4; the account page's mandate table is compared by hand (the harness does not read the account page, Spec T1 §9)",
    ),
    Test(
        id="A6", series="A", who=HARNESS, agent="trader", title="The fee address is configured, and is not advertised",
        rule="Proves the ruling of 13 September on the fee.",
        text="**A6. The fee address is configured, and is not advertised.** Albert, on Virginia: the Wallet's environment carries `AGENT_TRADE_FEE_BPS=5` and the fee address. From any computer: `/guide`, `/account` and the tool list carry none of \"fee\" as a whole word, \"0.05%\", \"five basis points\", \"5 bps\", \"sweepTokenWithFee\", \"fee_recipient\" or \"feeRecipient\"; `/terms` states the trading fee. \"basis points\" on its own is not counted: MCP Police's `check_action` schema uses the phrase for `slippage_bps` and `price_deviation_bps`, and neither is the fee. Proves the ruling of 13 September on the fee. Evidence: grep counts (guide 0, account 0, tool list 0, terms at least 1).",
        steps=[Grep(pages=["/guide", "/account", "tools/list"], absent=FEE_WORDS,
                    present_on={"/terms": ["trading fee"]})],
        where="Answered by the connector's public pages and tools/list under the fee ruling of 13 September 2026 (Spec 38); the Wallet's environment on Virginia is Albert's half",
    ),
    Test(
        id="A7", series="A", who=PERSON, title="The oracle is fresh", rule="Proves the price-deviation and oracle facts can be established (Rule 12).",
        text="**A7. The oracle is fresh.** Albert, on Virginia: a dry quote on Arbitrum reports the Chainlink ETH/USD, USDC/USD and USDT/USD reads with timestamps inside each feed's heartbeat window. Proves the price-deviation and oracle facts can be established (Rule 12). Evidence: the log lines.",
    ),
    Test(
        id="A8", series="A", who=PERSON, title="Halting is final, on a spare agent", rule="Proves Rule 20.",
        text="**A8. Halting is final, on a spare agent.** Each owner creates a throwaway Payer, halts it, and asks Claude connected as that agent to do anything. Both doors refuse on the next call; the account page shows it halted; there is no un-halt control. Proves Rule 20. Evidence: the refusal and the page.",
    ),
    # ---------------- Series B — the owner's road: the form and the list ----------------
    Test(
        id="B1", series="B", who=PAUSE, agent="trader", title="A compulsory question left blank is refused before anything is sent",
        rule="Proves Rule 2.",
        text="**B1. A compulsory question left blank is refused before anything is sent.** Open Set limits, clear \"a list for this agent only / one list for all my agents\", press Save. The page says *\"Say whether this list is for this agent only or for all your agents. Nothing was sent.\"* and the mandate table is unchanged. Proves Rule 2. Evidence: the sentence and the unchanged hash.",
        steps=[Pause("Open Set limits for the Trader, clear the choice between 'a list for this agent only' and 'one list for all my agents', press Save, and read the page's sentence; then press Enter.",
                     agent="trader", hash_moves=False, ask="Type the sentence the page said, exactly:",
                     expect_words=["Say whether this list is for this agent only or for all your agents", "Nothing was sent"])],
        where="Answered by the limits form on the page (pages/agentform.ts) under Rule 2; the hash is read from the MCP Wallet's wallet_status",
    ),
    Test(
        id="B2", series="B", who=PAUSE, agent="trader", title="A wrong address is refused naming the line",
        rule="Proves Rule 5, Rule 13.",
        text="**B2. A wrong address is refused naming the line.** Add a line `0x1234` to the destination list and save. The platform refuses the whole save and names the line. Proves Rule 5, Rule 13. Evidence: the sentence.",
        steps=[Pause("Open Set limits for the Trader, add a line reading 0x1234 to the destination list, press Save with your passkey, and read the refusal; then press Enter.",
                     agent="trader", hash_moves=False, ask="Type the refusal's sentence, exactly:",
                     expect_words=["0x1234"])],
        where="Answered by the access platform through the limits form under Rule 5 and Rule 13; the hash is read from the MCP Wallet's wallet_status",
    ),
    Test(
        id="B3", series="B", who=PAUSE, agent="trader", title="The Trader's list",
        rule="Proves Rule 9 (the mirror refreshes) and Rule 4.",
        text="**B3. The Trader's list.** For the Trader, write exactly these lines and save: Uniswap SwapRouter02 on Ethereum and Arbitrum `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`, Uniswap on Base `0x2626664c2603336E57B271c5C0b26F421741e481`, PancakeSwap SmartRouter on Ethereum `0x13f4EA83D0bd40E75C8222255bc855a974568Dd4`, on Arbitrum `0x32226588378236Fd0c7c4053999F88aC0e5cAc77`, on Base `0x678Aa4bF4E210cf2166753e054d5b7c31cc7fa86`, Circle CCTP TokenMessengerV2 `0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d`, Tether USDT0 on Ethereum `0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee` and on Arbitrum `0x14E4A1B13bf7F943c8ff7C51fb60FA964A298D92`. Choose \"a list for this agent only\". The save succeeds, the hash moves, and within a minute Claude's `can_sign` prints the new hash. Proves Rule 9 (the mirror refreshes) and Rule 4. Evidence: old hash, new hash, the minute.",
        steps=[Pause("Open Set limits for the Trader, write exactly the eight lines the harness prints below into the destination list, choose 'a list for this agent only', and save with your passkey; then press Enter.",
                     agent="trader", hash_moves=True)],
        where="Answered by the MCP Wallet's wallet_status under Rule 9 and Rule 4",
    ),
    Test(
        id="B4", series="B", who=PAUSE, agent="payer", title="The Payer's list",
        rule="Proves Rule 5.",
        text="**B4. The Payer's list.** For the Payer, write one line: the owner's own wallet address (Victor's listed destination `0xfec697fc2D4323aE7618BFF2347C01E29653FB57`, and Eitan's equivalent). Choose \"one list for all my agents\" for one tester and \"a list for this agent only\" for the other, so both answers are exercised. Proves Rule 5. Evidence: the mandate table reading the list back (Rule 21).",
        steps=[Pause("Open Set limits for the Payer, write one line — the owner's listed address the harness prints below — choose the list scope the run file names for this tester, and save with your passkey; then press Enter.",
                     agent="payer", hash_moves=True)],
        where="Answered by the MCP Wallet's wallet_status under Rule 5; the mandate table is read by hand (Rule 21)",
    ),
    Test(
        id="B5", series="B", who=PAUSE, agent="payer", title="The template is a floor the owner narrows",
        rule="Proves Rule 3.",
        text="**B5. The template is a floor the owner narrows.** On the Payer's form, try to permit the action *trade*; on the Trader's, try to permit *transfer*. The form offers no such control, or refuses it. Proves Rule 3. Evidence: what the form shows.",
        steps=[Pause("On the Payer's Set limits form, look for a control that would permit the action 'trade'; on the Trader's, look for one that would permit 'transfer'; press Save on nothing; then press Enter.",
                     agent="payer", hash_moves=None, ask="Type what the form shows, in your own words:")],
        where="Answered by the limits form (pages/agentform.ts) under Rule 3",
    ),
    Test(
        id="B6", series="B", who=PERSON, title="The page reads the document back", rule="Proves Rule 21.",
        text="**B6. The page reads the document back.** After B3 and B4, read the mandate table aloud with the screen reader: chains, assets, each limit, ask me first, period total, count, and the list. Where a figure was left blank the page says *the document states none*. Proves Rule 21. Evidence: the table as read.",
    ),
    Test(
        id="B7", series="B", who=PERSON, title="Two agents, two lists", rule="Proves the shared-list answer.",
        text="**B7. Two agents, two lists.** With the shared list of B4 in force for the tester who chose \"one list for all my agents\", create a second Payer and confirm its mandate table shows the same list without writing it again. Proves the shared-list answer. Evidence: the second table.",
    ),
    Test(
        id="B8", series="B", who=PAUSE, agent="trader", title="The list is amended by saving again",
        rule="Proves Rule 9.", moves_money=True, figure_usd=5,
        text="**B8. The list is amended by saving again.** Remove one exchange line from the Trader's list, save, and see D6 below refuse the trade on that exchange; put the line back, save, and see it pass. Proves Rule 9. Evidence: the two hashes and the two outcomes.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3.",
        steps=[
            Pause("Open Set limits for the Trader, remove the PancakeSwap Arbitrum line 0x32226588378236Fd0c7c4053999F88aC0e5cAc77 from the destination list, and save with your passkey; then press Enter.",
                  agent="trader", hash_moves=True),
            Walk(PANCAKE_ARBITRUM_TRADE, PRE_FLIGHT, VENUE_SENTENCE, "Owner's Guide v1.1 §10", label="with the line removed"),
            Pause("Open Set limits for the Trader, put the PancakeSwap Arbitrum line 0x32226588378236Fd0c7c4053999F88aC0e5cAc77 back into the destination list, and save with your passkey; then press Enter.",
                  agent="trader", hash_moves=True),
            Walk(PANCAKE_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="with the line back"),
        ],
        where="Answered by MCP Police at pre-flight under Rule 9 and Police Spec 16, then by the MCP Wallet and the chain",
    ),
    # ---------------- Series C — the Payer ----------------
    Test(
        id="C1", series="C", who=HARNESS, agent="payer", title="A payment to a listed address passes",
        rule="Proves Rules 5, 6, 10, 11, 14.", moves_money=True, figure_usd=1,
        text="**C1. A payment to a listed address passes.** Say to Claude as the Payer: *\"Pay 1 USDC on Arbitrum to <the listed address>.\"* Claude calls `check_action` (allow, receipt), `build_transaction` (ticket, dry-run passed), `submit_transaction` (hash). The explorer shows 1 USDC arriving. Proves Rules 5, 6, 10, 11, 14. Evidence: the receipt, the ticket, the hash, the record row.",
        says="Pay 1 USDC on Arbitrum to <the listed address>.",
        steps=[Walk(pay(1), ALLOWED, legs=1, label="1 USDC to the listed address")],
        where="Answered by MCP Police, the MCP Wallet and the chain under Rules 5, 6, 10, 11 and 14",
    ),
    Test(
        id="C2", series="C", who=HARNESS, agent="payer", title="A payment to an unlisted address is refused at pre-flight",
        rule="Proves Rule 5, Rule 11.", moves_money=True, figure_usd=1,
        text="**C2. A payment to an unlisted address is refused at pre-flight.** *\"Pay 1 USDC on Arbitrum to 0x000000000000000000000000000000000000dEaD.\"* Police answers deny with the destination sentence; Claude does not build. Proves Rule 5, Rule 11. Evidence: the refusal.",
        says="Pay 1 USDC on Arbitrum to 0x000000000000000000000000000000000000dEaD.",
        steps=[Walk(pay(1, to="DEAD_ADDRESS"), PRE_FLIGHT, DESTINATION_SENTENCE, "Owner's Guide v1.1 §10", label="to the dead address")],
        where="Answered by MCP Police at pre-flight under Rule 5 and Rule 11; the sentence is Guide section 10's destination sentence",
    ),
    Test(
        id="C3", series="C", who=HARNESS, agent="payer", title="The receipt is required to build",
        rule="Proves Rule 11 (the order is enforced by the Wallet).", moves_money=True, figure_usd=1,
        text="**C3. The receipt is required to build.** Albert, from a shell with the agent's credential: call the Wallet's `build_transaction` for C1's payment without a Police receipt. The Wallet refuses in its own words. Proves Rule 11 (the order is enforced by the Wallet). Evidence: the refusal.",
        steps=[Walk(pay(1), AT_WALLET, build_only=True, no_receipt=True, label="build without a receipt, through the relay as the agent")],
        where="Answered by the MCP Wallet at build under Rule 11 (Wallet Spec 11, the receipt as a tool argument); made through the relay as the agent rather than from a shell",
    ),
    Test(
        id="C4", series="C", who=HARNESS, agent="payer", title="Above per transaction is refused",
        rule="Proves Rule 6.", moves_money=True, figure_usd=25,
        text="**C4. Above per transaction is refused.** *\"Pay 25 USDC on Arbitrum to <listed>.\"* (per transaction is 20). Refused, naming the limit. Proves Rule 6. Evidence: the refusal.",
        says="Pay 25 USDC on Arbitrum to <listed>.",
        steps=[Walk(pay(25), REFUSED, label="25 USDC, above per transaction")],
        where="Answered by MCP Police at pre-flight or by the MCP Wallet's judge under Rule 6",
    ),
    Test(
        id="C5", series="C", who=PAUSE, agent="payer", title="Ask me first holds",
        rule="Proves Rule 7 and the guide's warning that a hold cannot yet be answered.", moves_money=True, figure_usd=3,
        text="**C5. Ask me first holds.** Set \"ask me first\" to 2 dollars on the Payer, save, then *\"Pay 3 USDC on Arbitrum to <listed>.\"* The answer is a hold: *\"owner approval required before ticket can be minted\"*, and nothing is signed. Set it back to 50 and save. Proves Rule 7 and the guide's warning that a hold cannot yet be answered. Evidence: the hold sentence, the record row marked held.",
        says="Pay 3 USDC on Arbitrum to <listed>.",
        steps=[
            Pause("Open Set limits for the Payer, set 'ask me first' to 2 dollars, and save with your passkey; then press Enter.", agent="payer"),
            Walk(pay(3), HELD, HOLD_SENTENCE, "Owner's Guide v1.1 §10", label="3 USDC with ask-me-first at 2"),
            restore("Payer", "set 'ask me first' back to 50 dollars"),
        ],
        where="Answered by MCP Police (manual_approval_required) or the MCP Wallet's owner-approval sentence under Rule 7",
    ),
    Test(
        id="C6", series="C", who=PAUSE, agent="payer", title="A chain not ticked is refused",
        rule="Proves Rule 16.", moves_money=True, figure_usd=1,
        text="**C6. A chain not ticked is refused.** Untick Base on the Payer, save, then *\"Pay 1 USDC on Base to <listed>.\"* Refused, naming the chain. Re-tick and save. Proves Rule 16. Evidence: the refusal.",
        says="Pay 1 USDC on Base to <listed>.",
        steps=[
            Pause("Open Set limits for the Payer, untick Base, and save with your passkey; then press Enter.", agent="payer"),
            Walk(pay(1, chain="base"), REFUSED, label="1 USDC on Base with Base unticked"),
            restore("Payer", "tick Base again"),
        ],
        where="Answered by MCP Police at pre-flight or the MCP Wallet's judge under Rule 16",
    ),
    Test(
        id="C7", series="C", who=HARNESS, agent="payer", title="An asset the role does not move is refused in the Wallet's words",
        rule="Proves Rule 13.", moves_money=True, figure_usd=1,
        text="**C7. An asset the role does not move is refused in the Wallet's words.** *\"Pay 1 WETH on Arbitrum to <listed>.\"* The Wallet answers that WETH is not a stablecoin this door transfers on arbitrum and names the ones it does. Proves Rule 13. Evidence: the sentence.",
        says="Pay 1 WETH on Arbitrum to <listed>.",
        steps=[Walk(pay(1, asset="WETH"), AT_WALLET, NOT_STABLECOIN_SENTENCE, "Series §5 C7", label="1 WETH")],
        where="Answered by the MCP Wallet under Rule 13; the sentence is the one Series C7 gives",
    ),
    Test(
        id="C8", series="C", who=HARNESS, agent="payer_nogas", title="No gas is a named refusal",
        rule="Proves Rule 15, Rule 13.", moves_money=True, figure_usd=1,
        text="**C8. No gas is a named refusal.** On a Payer with USDC but no ETH on Arbitrum (drain the ETH first, or use a third throwaway Payer funded that way): *\"Pay 1 USDC on Arbitrum to <listed>.\"* The Wallet says the signing address has so many wei native balance and needs at least so many for gas. Proves Rule 15, Rule 13. Evidence: the sentence.",
        says="Pay 1 USDC on Arbitrum to <listed>.",
        steps=[Walk(pay(1), AT_WALLET, GAS_SENTENCE, "Owner's Guide v1.1 §10", label="1 USDC from a Payer with no gas")],
        where="Answered by the MCP Wallet under Rule 15 and Rule 13; the sentence is Guide section 10's gas sentence",
    ),
    # ---------------- Series D — the Trader ----------------
    Test(
        id="D1", series="D", who=HARNESS, agent="trader", title="A Trader cannot send, not even to its owner",
        rule="Proves Rule 8 as amended.", moves_money=True, figure_usd=1,
        text="**D1. A Trader cannot send, not even to its owner.** As the Trader: *\"Pay 1 USDC on Arbitrum to <the owner's address>.\"* Refused: the role permits trade and nothing else. Proves Rule 8 as amended. Evidence: the refusal, from Police or the Wallet, quoted.",
        says="Pay 1 USDC on Arbitrum to <the owner's address>.",
        steps=[Walk(pay(1), REFUSED, label="a Trader paying its owner")],
        where="Answered by MCP Police at pre-flight or the MCP Wallet under Rule 8 as amended",
    ),
    Test(
        id="D2", series="D", who=HARNESS, agent="trader", title="The first Uniswap trade: approval then swap, two hashes, exact allowance",
        rule="Proves Rule 8 amended (the one approval, exactly the amount), Spec 44, and the fee ruling.", moves_money=True, figure_usd=5,
        text="**D2. The first Uniswap trade: approval then swap, two hashes, exact allowance.** *\"Trade 5 dollars of USDC for WETH on Arbitrum on Uniswap v3.\"* Claude sends venue `uniswap_v3`, `to_asset WETH`. The ticket carries two legs; `submit_transaction` returns two hashes. On the explorer: the first transaction is `approve(SwapRouter02, exactly the USDC amount of the trade)`, the second is the swap, WETH arrives in the agent's wallet, and a WETH transfer of five basis points of the output goes to the fee address in the same swap transaction. Proves Rule 8 amended (the one approval, exactly the amount), Spec 44, and the fee ruling. Evidence: both hashes, the approval's amount, the fee transfer.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on Uniswap v3.",
        steps=[Walk(UNISWAP_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="Uniswap v3 on Arbitrum")],
        where="Answered by MCP Police, the MCP Wallet (Wallet Spec 44) and the chain under Rule 8 as amended and the fee ruling",
    ),
    Test(
        id="D3", series="D", who=HARNESS, agent="trader", title="The second Uniswap trade has one leg",
        rule="Proves that an approval is never unlimited: every trade needs its own.", moves_money=True, figure_usd=5,
        text="**D3. The second Uniswap trade has one leg.** Repeat D2. Because the allowance was exact and is spent, a fresh approval is needed again: the ticket again carries two legs. Then trade *\"5 dollars of USDC for WETH on Arbitrum on Uniswap v3\"* a third time and confirm the same. Proves that an approval is never unlimited: every trade needs its own. Evidence: the leg counts. Note: if the Wallet ever reports one leg on a fresh trade, an allowance was left standing, and that is a failure.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on Uniswap v3.",
        steps=[
            Walk(UNISWAP_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="second Uniswap trade"),
            Walk(UNISWAP_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="third Uniswap trade"),
        ],
        where="Answered by the MCP Wallet's ticket (its legs) and the chain under Rule 8 as amended",
    ),
    Test(
        id="D4", series="D", who=HARNESS, agent="trader", title="The approval counts as two transactions",
        rule="Proves the amendment's second sentence.",
        text="**D4. The approval counts as two transactions.** After D2 and D3, ask Claude for `my_usage`; the count for the day has risen by two per trade with an approval. Proves the amendment's second sentence. Evidence: the count before and after.",
        steps=[Check("usage_delta", {"trades_with_approval_in": ["D2", "D3"]})],
        where="Answered by the MCP Wallet's my_usage under Rule 8 as amended, second sentence; the reading before D2 and the reading after D3 are quoted whole",
    ),
    Test(
        id="D5", series="D", who=HARNESS, agent="trader", title="PancakeSwap on Arbitrum",
        rule="Proves Spec 45 part A.", moves_money=True, figure_usd=5,
        text="**D5. PancakeSwap on Arbitrum.** *\"Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3.\"* Same shape as D2, venue `pancakeswap_v3`, contract `0x32226588378236Fd0c7c4053999F88aC0e5cAc77`, fee peeled to the fee address. Proves Spec 45 part A. Evidence: hashes, fee transfer.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3.",
        steps=[Walk(PANCAKE_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="PancakeSwap v3 on Arbitrum")],
        where="Answered by MCP Police, the MCP Wallet (Wallet Spec 45 part A) and the chain",
    ),
    Test(
        id="D6", series="D", who=PAUSE, agent="trader", title="A venue whose contract is not listed is refused by Police, naming it",
        rule="Proves Police Spec 16 and Rule 5 applied to trades.", moves_money=True, figure_usd=5,
        text="**D6. A venue whose contract is not listed is refused by Police, naming it.** With B8's line removed: *\"Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3.\"* Police says the venue contract is not on this agent's list. Proves Police Spec 16 and Rule 5 applied to trades. Evidence: the sentence.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3.",
        steps=[
            Pause("Open Set limits for the Trader, remove the PancakeSwap Arbitrum line 0x32226588378236Fd0c7c4053999F88aC0e5cAc77 from the destination list, and save with your passkey; then press Enter.", agent="trader"),
            Walk(PANCAKE_ARBITRUM_TRADE, PRE_FLIGHT, VENUE_SENTENCE, "Owner's Guide v1.1 §10", label="PancakeSwap with its line removed"),
            restore("Trader", "put the PancakeSwap Arbitrum line 0x32226588378236Fd0c7c4053999F88aC0e5cAc77 back"),
        ],
        where="Answered by MCP Police at pre-flight under Rule 5 and Police Spec 16; the sentence is Guide section 10's venue sentence",
    ),
    Test(
        # Spec T1 §4 lists D7 among the tests the harness runs by itself; its one form step — adding the
        # pool the refusal named — is a passkey save, so the harness pauses for it as it does for D6.
        id="D7", series="D", who=HARNESS, agent="trader", title="Curve, refused first, then listed, then traded",
        rule="Proves Spec 45 part B and the Guide's Curve caveat.", moves_money=True, figure_usd=5,
        text="**D7. Curve, refused first, then listed, then traded.** *\"Trade 5 dollars of USDC for USDT on Arbitrum on Curve.\"* First outcome: a refusal naming the pool's address (or, if no pool holds both, the Wallet's sentence *\"curve on arbitrum has no pool holding both USDC and USDT that this door could quote\"*, which is also a pass with a note). Add the pool address to the list, save, repeat: the trade passes, USDT arrives, no fee is taken (Curve cannot peel one) and the record says so. Proves Spec 45 part B and the Guide's Curve caveat. Evidence: the refusal, the pool, the hash.",
        says="Trade 5 dollars of USDC for USDT on Arbitrum on Curve.",
        steps=[
            Walk(CURVE_ARBITRUM_TRADE, REFUSED, CURVE_SENTENCE, "Owner's Guide v1.1 §10", label="Curve, first time"),
            Pause("Open Set limits for the Trader, add the pool address the refusal named (the harness prints it above) to the destination list, and save with your passkey; then press Enter.", agent="trader"),
            Walk(CURVE_ARBITRUM_TRADE, ALLOWED, fee="none", label="Curve, with the pool listed"),
        ],
        where="Answered first by MCP Police or the MCP Wallet naming the pool (Wallet Spec 45 part B, Guide §5's Curve caveat), then by the Wallet and the chain",
    ),
    Test(
        id="D8", series="D", who=HARNESS, agent="trader", title="Best price, with every candidate recorded",
        rule="Proves Spec 45 part C and the chooser ordering.", moves_money=True, figure_usd=5,
        text="**D8. Best price, with every candidate recorded.** *\"Trade 5 dollars of USDC for USDT on Arbitrum at the best price.\"* Claude sends venue `best_direct` with an empty `contract_address`. The answer names the exchange chosen; the record row shows every exchange's quote, the one chosen and `route_chosen_by`. Proves Spec 45 part C and the chooser ordering. Evidence: the answer, the record row with all candidates.",
        says="Trade 5 dollars of USDC for USDT on Arbitrum at the best price.",
        steps=[Walk(BEST_DIRECT_TRADE, ALLOWED, label="best_direct on Arbitrum")],
        where="Answered by the MCP Wallet (Wallet Spec 45 part C) and the chain; the record row with every candidate is read on the account page by hand",
    ),
    Test(
        id="D9", series="D", who=PAUSE, agent="trader", title="Best price with one candidate unlisted is refused by Police, naming it",
        rule="Proves Spec 16's chooser clause.", moves_money=True, figure_usd=5,
        text="**D9. Best price with one candidate unlisted is refused by Police, naming it.** Remove the Uniswap Arbitrum line, save, repeat D8. Police: *\"best_direct may choose uniswap_v3, whose contract 0x68b3… on arbitrum is not on this agent's list; list it, or remove uniswap_v3…\"*. Put the line back and save. Proves Spec 16's chooser clause. Evidence: the sentence.",
        says="Trade 5 dollars of USDC for USDT on Arbitrum at the best price.",
        steps=[
            Pause("Open Set limits for the Trader, remove the Uniswap Arbitrum line 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45 from the destination list, and save with your passkey; then press Enter.", agent="trader"),
            Walk(BEST_DIRECT_TRADE, PRE_FLIGHT, BEST_DIRECT_SENTENCE, "Owner's Guide v1.1 §10", label="best_direct with Uniswap unlisted"),
            restore("Trader", "put the Uniswap Arbitrum line 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45 back"),
        ],
        where="Answered by MCP Police at pre-flight under Police Spec 16's chooser clause; the sentence is Guide section 10's best_direct sentence",
    ),
    Test(
        id="D10", series="D", who=HARNESS, agent="trader", title="A trade that names nothing to buy is refused",
        rule="Proves Rule 12, Rule 13.", moves_money=True, figure_usd=5,
        text="**D10. A trade that names nothing to buy is refused.** *\"Trade 5 dollars of USDC on Arbitrum on Uniswap v3.\"* The Wallet: *\"a trade must name the asset it buys in to_asset…\"*. Proves Rule 12, Rule 13. Evidence: the sentence.",
        says="Trade 5 dollars of USDC on Arbitrum on Uniswap v3.",
        steps=[Walk(trade("uniswap_v3", "UNISWAP_V3_ARBITRUM", to_asset=None), AT_WALLET, TO_ASSET_SENTENCE, "Owner's Guide v1.1 §10", label="no to_asset")],
        where="Answered by the MCP Wallet under Rule 12 and Rule 13; the sentence is Guide section 10's to_asset sentence",
    ),
    Test(
        id="D11", series="D", who=HARNESS, agent="trader", title="An exchange named but not wired is refused in words",
        rule="Proves Rule 13.", moves_money=True, figure_usd=5,
        text="**D11. An exchange named but not wired is refused in words.** *\"Trade 5 dollars of USDC for WETH on Arbitrum on Aerodrome.\"* The Wallet: *\"this door trades directly on uniswap_v3, pancakeswap_v3, curve, best_direct; aerodrome is not yet wired to it.\"* Proves Rule 13. Evidence: the sentence.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on Aerodrome.",
        steps=[Walk(trade("aerodrome", ""), AT_WALLET, NOT_WIRED_SENTENCE, "Owner's Guide v1.1 §7; Series D11", label="Aerodrome")],
        where="Answered by the MCP Wallet under Rule 13; the sentence is the one Guide section 7 and Series D11 give",
    ),
    Test(
        id="D12", series="D", who=HARNESS, agent="trader", title="Selling a non-stablecoin is refused",
        rule="Proves the Wallet's stated limit.", moves_money=True, figure_usd=5,
        text="**D12. Selling a non-stablecoin is refused.** *\"Trade 5 dollars of WETH for USDC on Arbitrum on Uniswap v3.\"* Refused: `asset` must be a stablecoin. Proves the Wallet's stated limit. Evidence: the sentence.",
        says="Trade 5 dollars of WETH for USDC on Arbitrum on Uniswap v3.",
        steps=[Walk(trade("uniswap_v3", "UNISWAP_V3_ARBITRUM", to_asset="USDC", asset="WETH"), REFUSED, label="selling WETH")],
        where="Answered by the MCP Wallet (its stated limit that asset must be a stablecoin, Guide §7) or MCP Police at pre-flight",
    ),
    Test(
        id="D13", series="D", who=PAUSE, agent="trader", title="The hold at the Trader's default",
        rule="Proves Rule 3 (the template's figure applies when the document states none) and Rule 7.", moves_money=True, figure_usd=12,
        text="**D13. The hold at the Trader's default.** Clear \"ask me first\" on the Trader (leave it blank), save, and *\"Trade 12 dollars of USDC for WETH on Arbitrum on Uniswap v3.\"* Held: *\"owner approval required before ticket can be minted\"* (the template's ten dollars applies). Set it back to 50 and save. Proves Rule 3 (the template's figure applies when the document states none) and Rule 7. Evidence: the hold.",
        says="Trade 12 dollars of USDC for WETH on Arbitrum on Uniswap v3.",
        steps=[
            Pause("Open Set limits for the Trader, clear 'ask me first' so it is blank, and save with your passkey; then press Enter.", agent="trader"),
            Walk(trade("uniswap_v3", "UNISWAP_V3_ARBITRUM", amount=12), HELD, HOLD_SENTENCE, "Owner's Guide v1.1 §10", label="12 dollars at the Trader's default"),
            restore("Trader", "set 'ask me first' back to 50 dollars"),
        ],
        where="Answered by MCP Police (manual_approval_required) or the MCP Wallet's owner-approval sentence under Rule 3 and Rule 7",
    ),
    Test(
        id="D14", series="D", who=PAUSE, agent="trader", title="The old Uniswap router is not a road",
        rule="Proves the guide's warning.", moves_money=True, figure_usd=5,
        text="**D14. The old Uniswap router is not a road.** Add `0xE592427A0AEce92De3Edee1F18E0157C05861564` to the list, save, and ask for a Uniswap trade with `contract_address` set to it. Refused: the Wallet does not use it. Remove the line. Proves the guide's warning. Evidence: the sentence.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on Uniswap v3, with contract_address 0xE592427A0AEce92De3Edee1F18E0157C05861564.",
        steps=[
            Pause("Open Set limits for the Trader, add the line 0xE592427A0AEce92De3Edee1F18E0157C05861564 to the destination list, and save with your passkey; then press Enter.", agent="trader"),
            Walk(trade("uniswap_v3", "OLD_UNISWAP_ROUTER"), AT_WALLET, label="the old router as contract_address"),
            restore("Trader", "remove the line 0xE592427A0AEce92De3Edee1F18E0157C05861564"),
        ],
        where="Answered by the MCP Wallet under the Guide §5 warning about the older Uniswap router",
    ),
    Test(
        id="D15", series="D", who=HARNESS, agent="trader", title="Uniswap and PancakeSwap on Base",
        rule="Proves the per-chain address tables.", moves_money=True, figure_usd=5,
        text="**D15. Uniswap and PancakeSwap on Base.** Repeat D2 and D5 on Base with the Base contracts. Proves the per-chain address tables. Evidence: hashes and fee transfers on Base.",
        says="Trade 5 dollars of USDC for WETH on Base on Uniswap v3. / Trade 5 dollars of USDC for WETH on Base on PancakeSwap v3.",
        steps=[
            Walk(trade("uniswap_v3", "UNISWAP_V3_BASE", chain="base"), ALLOWED, legs=2, fee="expected", label="Uniswap v3 on Base"),
            Walk(trade("pancakeswap_v3", "PANCAKESWAP_V3_BASE", chain="base"), ALLOWED, legs=2, fee="expected", label="PancakeSwap v3 on Base"),
        ],
        where="Answered by MCP Police, the MCP Wallet and the Base chain under the per-chain address tables of Guide §5",
    ),
    Test(
        id="D16", series="D", who=HARNESS, agent="trader", title="The agent never sees the transaction bytes",
        rule="Proves the agent-facing ticket rule.",
        text="**D16. The agent never sees the transaction bytes.** Read Claude's answers from D2 to D15: no `quote_tx_json`, no calldata, no signed bytes appear. The ticket the agent sees names facts, hashes and legs. Proves the agent-facing ticket rule. Evidence: the transcripts.",
        steps=[Check("transcript_bytes", {"tests": ["D2", "D3", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13", "D14", "D15"]})],
        where="Answered by the MCP Wallet's tickets as recorded in evidence.jsonl under the agent-facing ticket rule",
    ),
    # ---------------- Series E — the crossings ----------------
    Test(
        id="E1", series="E", who=HARNESS, agent="trader", title="USDC Arbitrum to Base by Circle's road",
        rule="Proves Rule 23 and Spec 46.", moves_money=True, figure_usd=5,
        text="**E1. USDC Arbitrum to Base by Circle's road.** *\"Move 5 USDC from Arbitrum to Base.\"* Claude sends `bridge_stable`, `to_chain base`. Police allows (the CCTP contract is listed, Spec 17); the ticket carries the approval and the burn; `submit_transaction` returns the hashes; within minutes the Wallet completes the arrival with `receiveMessage` on Base and reports that hash; 5 USDC appears on Base. The record names the venue `cctp` and *\"through the issuer's own road\"*, and *\"a crossing carries no service fee\"*. Proves Rule 23 and Spec 46. Evidence: burn hash, receive hash, the two balances.",
        says="Move 5 USDC from Arbitrum to Base.",
        steps=[Walk(CCTP_CROSSING, ALLOWED, fee="none", label="USDC Arbitrum to Base by CCTP"), Check("crossing_arrives", {"walk": 0})],
        where="Answered by MCP Police (Spec 17), the MCP Wallet (Wallet Spec 46) and the two chains under Rule 23",
    ),
    Test(
        id="E2", series="E", who=HARNESS, agent="trader", title="A slow attestation is not a loss",
        rule="Proves the awaiting-attestation road.",
        text="**E2. A slow attestation is not a loss.** If E1's attestation outlives the ticket, the answer says *\"awaiting attestation\"* with the burn hash; ask Claude *\"Complete my crossing\"* and `get_crossing` finishes it. If E1 completed at once, Albert forces the case on Virginia by shortening `AGENT_BRIDGE_ATTESTATION_TIMEOUT_SECONDS` for one run. Proves the awaiting-attestation road. Evidence: the two answers.",
        says="Complete my crossing",
        steps=[Check("complete_crossing", {"from": "E1"})],
        where="Answered by the MCP Wallet's get_crossing under the awaiting-attestation road (Guide §9); the forced case is Albert's on Virginia",
    ),
    Test(
        id="E3", series="E", who=HARNESS, agent="trader", title="USDT Arbitrum to Ethereum by Tether's road",
        rule="Proves Rule 23 for USDT.", moves_money=True, figure_usd=5, stage2=True,
        text="**E3. USDT Arbitrum to Ethereum by Tether's road.** Stage 2. *\"Move 5 USDT from Arbitrum to Ethereum.\"* Venue `usdt0`; one send transaction on Arbitrum paying LayerZero's fee in ETH; USDT arrives on Ethereum automatically; the Wallet confirms by the destination balance rising. Proves Rule 23 for USDT. Evidence: the send hash, the Ethereum balance.",
        says="Move 5 USDT from Arbitrum to Ethereum.",
        steps=[Walk(bridge("USDT", "ethereum"), ALLOWED, fee="none", label="USDT Arbitrum to Ethereum by USDT0"), Check("crossing_arrives", {"walk": 0})],
        where="Answered by MCP Police, the MCP Wallet and the two chains under Rule 23 for USDT",
    ),
    Test(
        id="E4", series="E", who=HARNESS, agent="trader", title="USDT to Base is refused in words",
        rule="Proves Rule 13 and the guide's note.", moves_money=True, figure_usd=5,
        text="**E4. USDT to Base is refused in words.** *\"Move 5 USDT from Arbitrum to Base.\"* The Wallet: this road does not serve these two chains (Tether does not publish its road on Base). Proves Rule 13 and the guide's note. Evidence: the sentence.",
        says="Move 5 USDT from Arbitrum to Base.",
        steps=[Walk(bridge("USDT", "base"), AT_WALLET, NO_SERVE_SENTENCE, "Series §7 E4", label="USDT to Base")],
        where="Answered by the MCP Wallet under Rule 13 and Guide §9's note that USDT cannot be crossed to or from Base",
    ),
    Test(
        id="E5", series="E", who=HARNESS, agent="trader", title="A crossing goes to the agent's own address only",
        rule="Proves Rule 23's \"to its own address only\" and Spec 17's recipient check.", moves_money=True, figure_usd=5,
        text="**E5. A crossing goes to the agent's own address only.** Ask *\"Move 5 USDC from Arbitrum to Base and deliver it to <the owner's address>.\"* The crossing either ignores the address and delivers to the agent's own wallet on Base, or refuses; it never delivers to the named address. Proves Rule 23's \"to its own address only\" and Spec 17's recipient check. Evidence: the destination of the minted USDC.",
        says="Move 5 USDC from Arbitrum to Base and deliver it to <the owner's address>.",
        steps=[Walk(bridge("USDC", "base", to_address=OWNER), ALLOWED_OR_REFUSED, fee="none", label="a crossing addressed to the owner"),
               Check("crossing_arrives", {"walk": 0, "never_to": OWNER})],
        where="Answered by MCP Police (Spec 17's recipient check), the MCP Wallet and the Base chain under Rule 23's 'to its own address only'",
    ),
    Test(
        id="E6", series="E", who=PAUSE, agent="trader", title="A bridge contract not listed is refused by Police",
        rule="Proves Spec 17.", moves_money=True, figure_usd=5,
        text="**E6. A bridge contract not listed is refused by Police.** Remove the CCTP line, save, repeat E1: Police says the destination is not on the list, naming the contract. Put the line back. Proves Spec 17. Evidence: the sentence.",
        says="Move 5 USDC from Arbitrum to Base.",
        steps=[
            Pause("Open Set limits for the Trader, remove the CCTP line 0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d from the destination list, and save with your passkey; then press Enter.", agent="trader"),
            Walk(CCTP_CROSSING, PRE_FLIGHT, DESTINATION_SENTENCE, "Owner's Guide v1.1 §10", label="CCTP with its line removed"),
            restore("Trader", "put the CCTP line 0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d back"),
        ],
        where="Answered by MCP Police at pre-flight under Police Spec 17; the sentence is Guide section 10's destination sentence naming the contract",
    ),
    # ---------------- Series F — the record, the accounts and the words ----------------
    Test(
        id="F1", series="F", who=PERSON, title="Every action is in the record", rule="Proves Rule 21 and the audit half of the fee ruling.",
        text="**F1. Every action is in the record.** On the account page, read the record for each agent: every test above, allowed, refused or held, is a row with action, amount, chain, venue, hashes per leg, and for D8 every candidate. Proves Rule 21 and the audit half of the fee ruling. Evidence: the rows, counted against the tests.",
    ),
    Test(
        id="F2", series="F", who=HARNESS, agent="trader", title="The fee is accounted",
        rule="Proves the fee lands where the accounts expect and only there.",
        text="**F2. The fee is accounted.** On the explorer, read the fee address `0xabd0235C036CBeCb911DC74958B3c8F114cec42a` on Arbitrum and Base: its incoming transfers are exactly the fee legs of D2, D3, D5 and D15, each five basis points of that trade's output, and nothing else. The record rows show the same amounts. Proves the fee lands where the accounts expect and only there. Evidence: the explorer's transfer list against the rows.",
        steps=[Check("fee_accounting", {"tests": ["D2", "D3", "D5", "D15"], "chains": ["arbitrum", "base"]})],
        where="Answered by the chains' own Transfer logs (eth_getLogs to the fee address) against the fee legs the harness decoded; the record rows are read on the account page by hand",
    ),
    Test(
        id="F3", series="F", who=HARNESS, title="Refusal sentences match the guide",
        rule="Proves Rule 13 and the guide's promise.",
        text="**F3. Refusal sentences match the guide.** Compare every refusal collected in C, D and E with Guide section 10. Each is either there verbatim or is noted for the guide's version 1.2. Proves Rule 13 and the guide's promise. Evidence: the list of matches and the list of new sentences.",
        steps=[Check("sentences_vs_guide", {"series": ["C", "D", "E"]})],
        where="Answered by the refusals recorded in evidence.jsonl against the table transcribed from Guide section 10",
    ),
    Test(
        id="F4", series="F", who=HARNESS, agent="trader", title="One hash everywhere",
        rule="Proves Rule 4.",
        text="**F4. One hash everywhere.** For one allowed trade (D2), the policy hash in Police's receipt, in the Wallet's ticket, in the engine's verdict (Albert reads it on P0) and on the account page are the same string. Proves Rule 4. Evidence: the four hashes.",
        steps=[Check("one_hash_everywhere", {"test": "D2"})],
        where="Answered by MCP Police's receipt, the MCP Wallet's ticket and the Wallet's wallet_status under Rule 4; the engine's verdict on P0 and the account page are read by hand",
    ),
    Test(
        id="F5", series="F", who=PERSON, title="The engine judged the bytes", rule="Proves Rule 14 and E2's parser.",
        text="**F5. The engine judged the bytes.** Albert, on P0: the engine's log for D2 shows the approval judged as destination = SwapRouter02, amount = the allowance, and the swap judged with the venue contract as destination; for C1, the amount read from the transfer's calldata, not from the request. Proves Rule 14 and E2's parser. Evidence: the log lines.",
    ),
    Test(
        id="F6", series="F", who=PERSON, title="Nothing on the public pages is untrue", rule="Proves Rule 13 for the website that will be written from them.",
        text="**F6. Nothing on the public pages is untrue.** Read `/guide`, `/terms`, `/privacy` and the account page aloud: every sentence describes what the tests just showed, and the not-yet-built list matches Guide section 12. Proves Rule 13 for the website that will be written from them. Evidence: any sentence that is not true, listed.",
    ),
    # ---------------- Series G — when a part fails, the corridor fails closed ----------------
    Test(
        id="G1", series="G", who=PERSON, title="Police down", rule="Proves Rule 11.",
        text="**G1. Police down.** Stop mcp-police on P0 for two minutes; the tester asks for C1's payment. Claude reports Police unreachable and builds nothing; the Wallet refuses a build without a receipt. Restart. Proves Rule 11. Evidence: the refusal.",
    ),
    Test(
        id="G2", series="G", who=PERSON, title="A rail removed", rule="Proves Rule 18.",
        text="**G2. A rail removed.** Remove Base from `AGENT_CHAIN_RPC_URLS` on Virginia and restart the Wallet; the tester asks for a payment on Base. The Wallet: *\"no rail is configured for base on this door… so this…\"*, and `wallet_status` no longer names Base. Restore. Proves Rule 18. Evidence: the sentence.",
    ),
    Test(
        id="G3", series="G", who=PERSON, title="The engine's mirror lags", rule="Proves Rule 9's \"within a minute\".",
        text="**G3. The engine's mirror lags.** Change a limit on the form and, within the same minute, ask for an action that the old document allows and the new one refuses. Either the new document is already in force (refused) or the old is (allowed, and the record shows the old hash). Both are the corridor telling the truth; what fails is a refusal with neither hash. Proves Rule 9's \"within a minute\". Evidence: the hashes on the row.",
    ),
    Test(
        id="G4", series="G", who=PERSON, title="A stale oracle", rule="Proves Rule 12.",
        text="**G4. A stale oracle.** Set `AGENT_ORACLE_MAX_AGE_SECONDS` to 1 on Virginia and restart; ask for D2. The Wallet refuses because the oracle fact cannot be established, and says so; nothing is signed. Restore. Proves Rule 12. Evidence: the sentence.",
    ),
    # ---------------- Series H — over a day and a week ----------------
    Test(
        id="H1", series="H", who=PERSON, title="The daily count resets", rule="Proves the day boundary.",
        text="**H1. The daily count resets.** After Series D, note `my_usage`; the next day, the count is zero and the day's ceiling is whole again. Proves the day boundary. Evidence: the two readings.",
    ),
    Test(
        id="H2", series="H", who=PAUSE, agent="trader", title="The per-day ceiling",
        rule="Proves Rule 6.", moves_money=True, figure_usd=5,
        text="**H2. The per-day ceiling.** Set per day to 12 dollars on the Trader, run three five-dollar trades; the third is refused, naming the daily figure. Set it back. Proves Rule 6. Evidence: the refusal.",
        says="Trade 5 dollars of USDC for WETH on Arbitrum on Uniswap v3.",
        steps=[
            Pause("Open Set limits for the Trader, set 'per day' to 12 dollars, and save with your passkey; then press Enter.", agent="trader"),
            Walk(UNISWAP_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="first of three"),
            Walk(UNISWAP_ARBITRUM_TRADE, ALLOWED, legs=2, fee="expected", label="second of three"),
            Walk(UNISWAP_ARBITRUM_TRADE, REFUSED, label="third of three, above the daily figure"),
            restore("Trader", "set 'per day' back to 100 dollars"),
        ],
        where="Answered by MCP Police at pre-flight or the MCP Wallet's judge under Rule 6",
    ),
    Test(
        id="H3", series="H", who=PAUSE, agent="payer", title="The period total holds",
        rule="Proves Rule 7's second line.", moves_money=True, figure_usd=5,
        text="**H3. The period total holds.** Set the period total to 12 dollars, run three five-dollar payments on the Payer; the third is held, not refused. Set it back. Proves Rule 7's second line. Evidence: the hold.",
        says="Pay 5 USDC on Arbitrum to <listed>.",
        steps=[
            Pause("Open Set limits for the Payer, set the period total to 12 dollars, and save with your passkey; then press Enter.", agent="payer"),
            Walk(pay(5), ALLOWED, legs=1, label="first of three"),
            Walk(pay(5), ALLOWED, legs=1, label="second of three"),
            Walk(pay(5), HELD, HOLD_SENTENCE, "Owner's Guide v1.1 §10", label="third of three, at the period total"),
            restore("Payer", "set the period total back to 200 dollars"),
        ],
        where="Answered by MCP Police (manual_approval_required) or the MCP Wallet's owner-approval sentence under Rule 7's second line",
    ),
    Test(
        id="H4", series="H", who=PERSON, title="Two owners do not see each other", rule="Proves Rule 17.",
        text="**H4. Two owners do not see each other.** Eitan's account page shows no agent of Victor's, and Claude connected as Eitan's Trader cannot name Victor's wallet. Proves Rule 17. Evidence: both pages.",
    ),
]

BY_ID: Dict[str, Test] = {t.id: t for t in TESTS}
SERIES_ORDER = ("A", "B", "C", "D", "E", "F", "G", "H")
SELECTABLE_SERIES = ("A", "B", "C", "D", "E", "F", "H")  # Spec T1 §8: G is a person's

# The three lists of Spec T1 §4, derived from the data so they cannot drift from it.
HARNESS_RUNS: List[str] = [t.id for t in TESTS if t.who == HARNESS]
PAUSES: List[str] = [t.id for t in TESTS if t.who == PAUSE]
LEFT_TO_A_PERSON: List[str] = [t.id for t in TESTS if t.who == PERSON]


def tests_in(series: Sequence[str]) -> List[Test]:
    wanted = set(series)
    return [t for t in TESTS if t.series in wanted]


def order_key(test_id: str) -> int:
    return list(BY_ID).index(test_id)
