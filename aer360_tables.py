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
from typing import Any, Dict, List, NamedTuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corridor_harness import checksum_address, keccak256  # noqa: E402  the corridor's own keccak and EIP-55

# The seed every test address is derived from. Changing it changes every address at once,
# which is the point: no address here was ever typed, so none can be a real one mistyped.
SEED = "aer360-harness test addresses — Spec T7, 19 September 2026"

# THE CHAIN IS ONE WORD IN ONE PLACE (Spec T18, 24 September 2026; Bear: "Let's move to Arbitrum."). The chain a payee's
# address lives on, the chain every payment is made on, and where that word comes from. The harness answers C9 (the networks
# beside Aeredium) with the display name below; since AER 360 Spec 106 the compiler writes the choice by the registry's id
# (`packages/shared/src/chains.ts`, chainIdForName; `onboardingcompiler.ts`, chainAllowlist — until 106 it lower-cased the
# display name, which is the id for "Ethereum" and a chain nothing knows for "Arbitrum One"), and the registry names the
# chain `arbitrum`: display name "Arbitrum One", family evm, chain id 42161, payouts true. Everything the harness sends or
# expects about a chain reads PAYEE_CHAIN at run time — S3's expected recorded networks, the payees' chain, the payee
# resolution, S7's notes and the Treasury sentence, the register and asset reads, the venue probe — so moving the chain is
# moving these two lines and nothing else. The sandbox's own network, `aeredium-testnet`, is not in that registry, so the
# payee road (`isKnownChain`) would refuse a payee address declared on it; the harness records which networks the compiled
# charter names.
PAYEE_CHAIN = "arbitrum"
C9_NETWORK_CHOICE = "Arbitrum One"

# Spec 106's rule, mirrored for the auditor's read-back of the networks (packages/shared/src/chains.ts, chainIdForName;
# onboardingcompiler.ts, chainAllowlist): after a trim, a case-insensitive exact match on a served display name or on the id of
# a chain the platform serves answers the id; anything else the compiler lower-cases exactly as it always did (Bitcoin → bitcoin),
# so every standing charter reads back unchanged. The rows are the registry's for the names C9 serves, read on 24 September 2026.
REGISTRY_IDS_BY_NAME = {"ethereum": "ethereum", "arbitrum one": "arbitrum", "arbitrum": "arbitrum", "solana": "solana"}


def chain_id_for_name(name: Any) -> str:
    """The id the compiler writes for a network a person chose (Spec 106), else the choice lower-cased, as the compiler falls back."""
    wanted = str(name).strip().lower()
    return REGISTRY_IDS_BY_NAME.get(wanted, wanted)


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


# THE KEYS AND THEIR LABELS KEEP THE NAMES THEY WERE FIRST MINTED UNDER (Spec T7, on ethereum; Spec T18 moved the chain without
# moving an address): `_pin` derives the bytes from the label, so renaming a key or a label would move its address. The `_ETHEREUM`
# suffix records where a label was first minted, not where the payee pays — that is PAYEE_CHAIN, above, and an EVM address is the
# same twenty bytes on every EVM chain.
PINNED: Dict[str, Derived] = {
    "NORTHWIND_ETHEREUM": _pin("Northwind Supplies/ethereum", "the test payee Northwind Supplies"),
    "CONTOSO_ETHEREUM": _pin("Contoso Legal/ethereum", "the test payee Contoso Legal"),
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

# The two payees of the whitelist (Spec T7, "The estate, its people and its money"), created on PAYEE_CHAIN and resolved by
# (name, chain) before any payment (Spec T18 §2). No row copies the chain: the harness reads PAYEE_CHAIN where it creates or resolves one.
PAYEES: List[Dict[str, str]] = [
    {"key": "NORTHWIND_ETHEREUM", "name": "Northwind Supplies"},
    {"key": "CONTOSO_ETHEREUM", "name": "Contoso Legal"},
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


# THE VENUE PROBE'S ROW (Spec T18 §3): Uniswap v3 SwapRouter02 on Arbitrum One, chain 42161 — the KEY of the corridor's tables.py row
# whose bytes S11 reads at run time (`venue_address_for_probe`) and which are never written here. Read once, on 24 September 2026, from
# Uniswap's published deployments (UNISWAP_V3_ARBITRUM_SOURCE, the row "SwapRouter02") and found to be the corridor's row: SwapRouter02 is
# one address on Ethereum and on Arbitrum One. The estate's own closed venue table (packages/shared/src/venues.ts, copied row for row
# from the engine's) holds the same row on `arbitrum`, so a payee registered on PAYEE_CHAIN with this address is refused
# PAYEE_IS_VENUE_CONTRACT where the charter says so (C19 No); tests/test_aer360_tables.py holds the corridor's row to the published bytes.
UNISWAP_V3_ARBITRUM = "UNISWAP_V3_ARBITRUM"
UNISWAP_V3_ARBITRUM_SOURCE = "https://developers.uniswap.org/docs/protocols/v3/deployments/v3-arbitrum-deployments"


def venue_address_for_probe(key: str = UNISWAP_V3_ARBITRUM) -> Dict[str, str]:
    """
    THE ONE VENUE ADDRESS S11 SENDS ON PURPOSE, read from the corridor's own table at run time
    and never from this file — Uniswap v3 SwapRouter02 on PAYEE_CHAIN since Spec T18. Refuses if
    the corridor's row is somehow one of ours.
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


# ---------------------------------------------------------------------------
# THE AEREDIUM TESTNET AND ITS FAUCET (Spec T13, 22 September 2026): facts, never inventions. Read from the
# cabinet's faucet record — Deployments drawer, "AEREDIUM testnet faucet, the auto-pay mechanism end to end,
# 21 September 2026", written from Bear's own account — and from the faucet page that record describes,
# https://aeredium.io/faucet.html, whose network helper names the RPC and the explorer beside the chain id.
# The RPC was read back on 22 September 2026: eth_chainId answered 0x8bd, which is 2237.
#
# The harness funds the estate's funding wallet exactly as a founder at that page would: one POST of the
# address as JSON to the faucet's request road, once per run, only where the wallet's native balance reads
# below GAS_FLOOR_SEAR — and it never invents a balance. The faucet pays exactly 0.5 SEAR per request and
# refuses, in its own sentence, past four payments to a wallet or eight to an IP in a trailing day, or 200
# SEAR across everyone. This is gas only; what the payments move (USDC) is a different question, and the
# harness never mints or moves it. No address of the faucet's or the treasury's is written here.
# ---------------------------------------------------------------------------
TESTNET_CHAIN_ID = 2237                      # testnet 2, hex 0x8bd
TESTNET_NAME = "AEREDIUM testnet2"
NATIVE_COIN = "SEAR"
NATIVE_DECIMALS = 18
TESTNET_RPC_URL = "https://testnet.rpc.aeredium.io"
TESTNET_EXPLORER_URL = "https://testnet.explorer.aeredium.io"
FAUCET_PAGE_URL = "https://aeredium.io/faucet.html"
FAUCET_REQUEST_URL = "https://aeredium.io/faucet-api/request"
FAUCET_PAYS_SEAR = "0.5"                     # exactly, per auto-paid request
FAUCET_LIMITS = "four payments per wallet and eight per IP in a day, and 200 SEAR across everyone"
GAS_FLOOR_SEAR = "0.1"                       # below it the harness asks the faucet, once per run (Spec T13 §2)


def to_wei(amount: str) -> int:
    """A plain decimal of the native coin to wei, by the same string arithmetic as minor_units."""
    return int(minor_units(amount, NATIVE_DECIMALS))


GAS_FLOOR_WEI = to_wei(GAS_FLOOR_SEAR)


def coin_amount(wei: int) -> str:
    """
    Wei as a plain decimal of the native coin, by string arithmetic — no float anywhere: 0 → "0",
    500000000000000000 → "0.5", 10**18 → "1", 1234500000000000000 → "1.2345".
    """
    if not isinstance(wei, int) or wei < 0:
        raise ValueError("a balance is a non-negative integer of wei: %r" % (wei,))
    text = str(wei).rjust(NATIVE_DECIMALS + 1, "0")
    whole, fraction = text[:-NATIVE_DECIMALS], text[-NATIVE_DECIMALS:].rstrip("0")
    return whole + ("." + fraction if fraction else "")


def payments_total(amounts: List[str], decimals: int = 6) -> str:
    """The sum of plain-decimal amounts of the payment asset, as a plain decimal, by string arithmetic."""
    total = sum(int(minor_units(a, decimals)) for a in amounts)
    text = str(total).rjust(decimals + 1, "0")
    fraction = text[-decimals:].rstrip("0").ljust(2, "0")
    return text[:-decimals] + "." + fraction


# ---------------------------------------------------------------------------
# THE ROSTER CEREMONY'S DOOR (Spec T15, 22 September 2026): the two roads and the step-up purpose, read from AER 360 Spec 99
# (aeredium/AERAccounts, commit 33e039c — apps/server/src/routes/rosterchanges.ts, services/approverseats.ts, services/changequorum.ts,
# services/audit.ts; packages/shared/src/wire.ts, enrolment.ts, refusals.ts) and never invented.
#
# Spec 95 moves a roster seat to a person's current credential at a re-invitation's redemption, at a seat grant and at the self-seat —
# not at a sign-in (enrolment.ts says so in its own words) — and where the charter asks more than one person to agree to a change of
# who the approvers are (C12C), the access platform holds the move as a ceremony, a pending `multisig_update` needing the charter's
# count of signatures. Spec 99 is the door the client's people sign it through: the list, and one signature under the signer's own
# session with a passkey step-up of purpose `roster.change`, whose challenge the estate derives from the binding
# `roster-change:<workspace id>:<pendingTxId>:<issuedAtMs>` | the signer's credential | the purpose. The count met, the estate presents
# the change to the platform again, the seat moves, and the trail says so: `roster.seat_rebound` naming the ceremony and every signer
# (SPEC.md spells the verb `roster.seat.rebound`; the estate's closed list of verbs, services/audit.ts, spells it with an underscore,
# and the harness uses the estate's word). The trail a browser reads is the accountant's audit export.
# ---------------------------------------------------------------------------
ROSTER_CHANGES_ROUTE = "/v1/roster/changes"                                # GET: every roster change the platform holds for the estate
ROSTER_CHANGE_SIGN_OPTIONS_ROUTE = "/v1/roster/changes/%s/sign/options"    # POST: the step-up's first half, the digest-bound challenge
ROSTER_CHANGE_SIGN_ROUTE = "/v1/roster/changes/%s/sign"                    # POST: one signature, as the signer
ROSTER_CHANGE_PURPOSE = "roster.change"                                    # routes/rosterchanges.ts ROSTER_CHANGE_PURPOSE, on CHANGE_CEREMONIES (C12C's family)
ROSTER_CHANGE_BINDING = "roster-change:%s:%s:%s"                           # the setDigest half of the binding: the workspace id, the ceremony's id, then issuedAtMs
ROSTER_CHANGE_OPERATION = "multisig_update"                                # services/approverseats.ts ROSTER_CHANGE_OPERATION: Spec 95's rebind, in the platform's word
ROSTER_CHANGE_STATES = ("awaiting", "approved", "applied", "expired", "closed")  # packages/shared/src/wire.ts RosterChangeState
SEAT_ON_ROSTER = "onRoster"                                              # Spec 105 (packages/shared/src/wire.ts ApproverSeatView): whether the platform's roster still names the seat's current credential — true, false, or null
SEAT_ROSTER_SAID = "rosterSaid"                                           # Spec 105: the platform's own sentence beside a null onRoster (the roster could not be read, or names the person under no credential the estate can verify)
ROSTER_SEAT_REBOUND = "roster.seat_rebound"                                # services/audit.ts: the trail's verb for a seat the platform moved
ROSTER_CHANGE_PROPOSED = "roster.change_proposed"                          # services/audit.ts: the seat's row for a move the client's governance holds
VIA_ROSTER_CHANGE = "roster_change"                                        # the road a met count re-presented the change on, as the trail writes it
AUDIT_EXPORT_ROUTE = "/v1/export/audit"                                    # routes/exports.ts: the trail, oldest first, `items` with at, action, credential_id, detail
AUDIT_EXPORT_LIMIT = 5000                                                  # routes/exports.ts MAX_LIMIT


def credential_short_form(credential_id: Any) -> str:
    """`credentialIdShortForm` (packages/shared/src/enrolment.ts): a credential id's first eight characters, for a line a person reads."""
    return str(credential_id or "")[:8]


# ---------------------------------------------------------------------------
# THE WRITE THAT WAITS FOR APPROVALS (Spec T19, 25 September 2026), as AER 360 Spec 109 built it (aeredium/AERAccounts, commit e2dcc6e:
# routes/onboarding.ts, routes/passkeysign.ts, services/onboardingcompiler.ts step 5, packages/shared/src/wire.ts and refusals.ts, read in
# its run folder rather than from memory). The creation of a wallet account's approved-destinations list is `whitelist_modify` on the NEW
# account, which the account's own charter governs at WQ's count on WA1's roster (WO2's third party seated beside them); where WQ is two
# or more the platform holds the creation as a ceremony until that many sign, and the estate answers the compile 202 — the write waits.
# The approvers sign it where they stand, each under their own passkey, through the same two-step road as the roster ceremony's, and
# the signature that meets the count finishes the write as the presser. Every road, state, verb and code here is the estate's own word.
# ---------------------------------------------------------------------------
INTERVIEW_AWAITING_APPROVALS = "awaiting_approvals"                        # wire.ts INTERVIEW_AWAITING_APPROVALS: the state beside compiled and written
ONBOARDING_CEREMONIES_ROUTE = "/v1/onboarding/ceremonies"                  # GET (viewer): every write of the estate that waits, as the caller may read and sign it
INTERVIEW_CEREMONY_SIGN_OPTIONS_ROUTE = "/v1/onboarding/interviews/%s/ceremonies/%s/sign/options"  # POST: the step-up's first half — the interview, the ceremony
INTERVIEW_CEREMONY_SIGN_ROUTE = "/v1/onboarding/interviews/%s/ceremonies/%s/sign"                  # POST: one signature, as the signer
INTERVIEW_CEREMONY_PURPOSE = "onboarding.ceremony"                         # routes/onboarding.ts: the step-up purpose the challenge is bound to
INTERVIEW_CEREMONY_BINDING = "onboarding-ceremony:%s:%s:%s:%s"             # the setDigest half of the binding: the workspace id, the interview id, the ceremony's id, then issuedAtMs
INTERVIEW_CEREMONY_STATES = ("awaiting", "approved", "applied", "expired", "closed")  # read off the platform's record exactly as a roster change's is (rosterChangeState)
APPROVED_DESTINATIONS_SUFFIX = " — approved destinations"                  # onboardingcompiler.ts approvedDestinationsListName: "<account name> — approved destinations"
WRITE_AWAITING_APPROVALS = "onboarding.write_awaiting_approvals"          # services/audit.ts: the trail's row for a wait, once per ceremony opened (pendingTxId, requiredMultisigId, replaces?)
CEREMONY_SIGNED = "onboarding.ceremony_signed"                             # services/audit.ts: one row per signature counted — credentialId the presser, subjectId the interview
INTERVIEW_WRITTEN = "onboarding.interview_written"                         # services/audit.ts: the write's row; on the sign road credentialId and detail.pressedBy are the presser's
INTERVIEW_WRITE_FAILED = "onboarding.interview_write_failed"              # services/audit.ts: a write that did not finish, with its cause
WALLET_BORN = "wallet.born"                                                # services/audit.ts: the funding wallet's birth — once per estate, never a second
WRITE_IN_PROGRESS = "WRITE_IN_PROGRESS"                                    # 409: another press holds this interview's write; nothing was signed or written
CEREMONY_NOT_LISTED = "CEREMONY_NOT_LISTED"                                # 404: not on this interview, the platform no longer lists it, or the interview is <state> — detail.cause says which
CEREMONY_CLOSED = "CEREMONY_CLOSED"                                        # 409: the ceremony no longer collects signatures (detail.platformStatus); Finish the write opens a new one
CHARTER_WRITE_UNFINISHED = "CHARTER_WRITE_UNFINISHED"                      # 409: the write did not finish, the cause in detail.cause — the estate's words for a refusal met at the write


def account_name_of_list(list_name: Any) -> str:
    """The account a list was created for, read off the list's name as the estate composes it (the suffix removed); an unnamed list is spoken as such."""
    text = str(list_name or "").strip()
    if text.endswith(APPROVED_DESTINATIONS_SUFFIX):
        return text[:-len(APPROVED_DESTINATIONS_SUFFIX)]
    return text or "an unnamed list"


# ---------------------------------------------------------------------------
# THE TREASURY, THE GAS ACCOUNT AND THE ADMIN CREDIT ROAD (Spec T14, 22 September 2026, amended 22:35; built 24 September 2026).
# Facts, never inventions, read from AER 360 Spec 104 (aeredium/AERAccounts, commit 8812c64 — routes/gas.ts, routes/workspace.ts,
# routes/sets.ts, services/execution.ts, services/accountabstraction.ts, services/fundingwallet.ts, packages/shared/src/states.ts)
# and from platform Spec 154 and 154b (aeredium/aegiskey-access-platform, commits e7dc195 and 451b998 — internal/api/router.go,
# gas_handlers.go, middleware.go, internal/gas/credit.go, ledger.go).
#
# The float is a WORKSPACE, not a file (Bear, 22 September: "we are only using threshold signatures. There is no key anywhere to be
# found"): Harness Treasury is a second sandbox workspace the harness births exactly as Harness Holdings was born — its own founder
# passkey under ~/.aer360-harness/harness-treasury/, its funding wallet a key allocated on the platform and held in the enclave. Bear
# funds that wallet's address with USDC once; the harness holds no key for it and pays from it only through the estate's own road.
# Gas is a balance in dollars on the platform's gas ledger (U3), credited for the sandbox through the platform's ADMIN credit road with
# the admin credential Bear files in ~/.aer360-harness/admin.env — never in the repository, never printed. The card road is Bear's.
# ---------------------------------------------------------------------------
TREASURY = {
    "company": "Harness Treasury Pty Ltd",   # the workspace's name, as the birth script names it; the session's workspace must begin with the short name
    "short": "Harness Treasury",
    "client_id": "harness-treasury",         # the folder under ~/.aer360-harness/ the Treasury founder's passkey lives in
    # The address the Treasury's estate is opened under, which the estate attributes to the founder's own key (services/approverseats.ts,
    # addressesOfCaller: the account's own address, for a key the register attaches to nobody) — so the Treasury's charter names it as the
    # payment approver (C11) and the founder's compile seats her (completeSeatOnCharterWrite): the one approver the float needs.
    "email": "harness+treasury@aeredium.io",
}
ADMIN_ENV_FILE = "admin.env"                 # under ~/.aer360-harness/: the platform's admin credential, in the estate's own setting names
ADMIN_ENV_URL_KEY = "AAP_ADMIN_BASE_URL"     # AERAccounts .env.example: the access platform's base URL
ADMIN_ENV_KEY_KEY = "AAP_ADMIN_KEY"          # AERAccounts .env.example: the admin key, `aek-admin-…` (internal/api/middleware.go)
ADMIN_KEY_PREFIX = "aek-admin-"
ADMIN_CREDIT_ROUTE = "/v1/admin/accounts/%s/gas-account/credits"   # router.go: the admin credit road of the gas account (Spec 154 §1): the account's id
ADMIN_CREDIT_REASON = "sandbox run %s"                             # gas_handlers.go PostAdminGasAccountCredit: reason required; the harness names the run
GAS_CREDIT_USD_CENTS = 1000                  # U3 (Bear, 22 September 2026): "put $10 on our account every time"; accountabstraction.ts GAS_DEFAULT_TOP_UP_USD_CENTS
GAS_ACCOUNT_ROUTE = "/v1/gas/account"        # routes/gas.ts: the balance, read live from the platform; `account.sentence` is "Gas account: US$<available>"
GAS_ACCOUNT_LABEL = "Gas account"            # accountabstraction.ts GAS_ACCOUNT_LABEL
FUNDING_BALANCES_ROUTE = "/v1/workspace/funding-account/balances"  # routes/workspace.ts: the stablecoin the funding wallet holds, per chain, in dollars
SET_EXECUTE_ROUTE = "/v1/sets/%s/execute"    # routes/sets.ts: execute an approved run (author-gated); the estate waits for the platform to report it landed
GAS_GATE = "gas_preflight"                   # setgates.ts: the fourth gate's name in the review payload, the gas account preflight (Spec 104 §4)
GAS_SHORTFALL = "GAS_SHORTFALL"              # refusals.ts; execution.ts gasAccountPreflight: U3's sentence with the set's figures
PAYMENT_UNPRICED = "PAYMENT_UNPRICED"        # 502: the platform answered and refused the quote — "This payment could not be priced: <their sentence>"
PAYMENT_PRICING_UNAVAILABLE = "PAYMENT_PRICING_UNAVAILABLE"  # 503: the platform did not answer, or answered a fault
WORKSPACE_NOT_PROVISIONED = "WORKSPACE_NOT_PROVISIONED"      # 503: routes/sets.ts requireSourceAccount — a run asked of an estate with no funding wallet
INSTRUCTION_CONFIRMED = "instruction.confirmed"   # services/audit.ts: the trail's row for a landed payment — txHash, userOpHash, gasDebitUsdCents, gasDebit
INSTRUCTION_TERMINAL_STATES = ("confirmed", "failed", "rejected")          # packages/shared/src/states.ts TERMINAL_INSTRUCTION_STATES
SET_TERMINAL_STATES = ("settled", "partially_settled", "cancelled")        # states.ts TERMINAL_SET_STATES
PLATFORM_LANDED = "landed"                   # the platform's word for an operation whose receipt the sponsor read (GET /v1/gas/operations/{hash}); the estate's is `confirmed`
SET_SETTLED = "settled"                      # states.ts resolveSetOutcome: every instruction confirmed
INSTRUCTION_CONFIRMED_STATE = "confirmed"    # states.ts: the instruction landed and its receipt was read
# The sandbox chain's names as the estate speaks them: the compiled charter's `allowedChains` word (onboardingcompiler.ts) and the
# registry's short name (packages/shared/src/chains.ts). Either names the AEREDIUM testnet whose RPC Spec T13 pinned above.
TESTNET_CHAIN_NAMES = ("aeredium-testnet", "aeredium")
ERC20_BALANCE_OF = "balanceOf(address)"
ERC20_BALANCE_OF_SELECTOR = "0x" + keccak256(ERC20_BALANCE_OF.encode("ascii"))[:4].hex()   # 0x70a08231, the ERC-20 selector
# The sentences this spec adds, word for word (SPEC.md §2 and §3, the ship note).
NO_GAS_CREDIT_ROAD_SENTENCE = ("no gas credit road: the sandbox credits gas through the platform's admin road; file the credential in "
                               "~/.aer360-harness/admin.env")
TREASURY_SHORT_SENTENCE = "Harness Treasury holds %s; the run needs %s; fund %s on %s"
FUND_TREASURY_SENTENCE = "fund Harness Treasury: %s on %s, then rerun"


def public_rpc_url(chain: str) -> Optional[str]:
    """
    THE PUBLIC RPC THE HARNESS MAY READ A PAYEE'S BALANCE FROM, and nothing else: the AEREDIUM testnet's (Spec T13, from the faucet
    record) for the sandbox chain under either of the estate's names for it, else the endpoint the corridor harness's own run-file
    skeleton names for the chain (`corridor_harness.default_run_file`, read at run time and never copied here). None for a chain
    neither names: the harness never invents an endpoint, and says so.
    """
    if chain in TESTNET_CHAIN_NAMES:
        return TESTNET_RPC_URL
    from corridor_harness import default_run_file  # the corridor harness's skeleton, beside this file

    row = (default_run_file().get("chains") or {}).get(chain)
    return str(row["rpc"]) if isinstance(row, dict) and row.get("rpc") else None


def balance_of_call_data(address: str) -> str:
    """The ERC-20 `balanceOf(address)` call: the selector and the address left-padded to thirty-two bytes, as eth_call takes it."""
    body = address.lower()[2:] if address.lower().startswith("0x") else address.lower()
    if len(body) != 40 or any(c not in "0123456789abcdef" for c in body):
        raise ValueError("an EVM address is 0x and forty hexadecimal characters: %r" % address)
    return ERC20_BALANCE_OF_SELECTOR + body.rjust(64, "0")


def format_usd_cents(cents: Any) -> str:
    """`formatUsdCents` (services/accountabstraction.ts), the estate's own spelling on the gas roads: US$12.34, no grouping, a leading minus."""
    n = int(cents)
    negative = n < 0
    n = -n if negative else n
    return "%sUS$%d.%02d" % ("-" if negative else "", n // 100, n % 100)


def gas_set_shortfall_sentence(available_cents: Any, ceiling_cents: Any) -> str:
    """`gasSetShortfallSentence` (Spec 104 §4), U3's sentence for a set, word for word."""
    return "Your gas account holds %s. This set needs at most %s of gas. Nothing was sent. Buy gas below." % (
        format_usd_cents(available_cents), format_usd_cents(ceiling_cents))


def gas_debit_words(actual_cents: Any) -> str:
    """`gasDebitWords` (Spec 104 §5; Spec 154 §4): the debit's words on the trail and the export."""
    return "gas, %s, paid in advance from your gas account" % format_usd_cents(actual_cents)


def usdc_dollars(minor: Any) -> str:
    """
    USDC minor units (six decimals) as dollars, by integer arithmetic — the asset is the dollar-pegged one the payments are made in
    (Spec T11 §4): 18240000 → "US$18.24"; dust below a cent is shown whole rather than rounded away: 18240001 → "US$18.240001".
    """
    n = int(minor)
    if n < 0:
        raise ValueError("a balance is a non-negative integer of minor units: %r" % (minor,))
    whole, fraction = divmod(n, 10 ** ASSET_DECIMALS[PAYMENT_ASSET])
    if fraction % 10 ** (ASSET_DECIMALS[PAYMENT_ASSET] - 2) == 0:
        return "US$%d.%02d" % (whole, fraction // 10 ** (ASSET_DECIMALS[PAYMENT_ASSET] - 2))
    return "US$%d.%0*d" % (whole, ASSET_DECIMALS[PAYMENT_ASSET], fraction)


def usdc_minor_of_cents(cents: Any) -> int:
    """Cents to USDC minor units: the payments' figures are dollars, and USDC carries six decimals."""
    return int(cents) * 10 ** (ASSET_DECIMALS[PAYMENT_ASSET] - 2)


def parse_env_file(text: str) -> Dict[str, str]:
    """A shell-style environment file: KEY=value lines, an optional `export`, quotes stripped, comments and blanks ignored."""
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
