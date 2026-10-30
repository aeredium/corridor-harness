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

ON A REAL CHAIN THE PAYEE IS THE OWNER'S OWN WALLET (Spec T24, 3 October 2026). The derived addresses
have no key behind them: harmless on the AEREDIUM testnet, lost money anywhere else — since Spec T18
moved PAYEE_CHAIN to `arbitrum` the payments are real USDC, and the run of 28 September 2026 paid
US$18.24 to addresses nobody can spend from. So where PAYEE_CHAIN is not one of TESTNET_CHAIN_NAMES
the harness pays only the owner's own wallet, read at run time from ~/.aer360-harness/payee.env
(OWNER_PAYEE_ADDRESS, EIP-55 checksummed; OWNER_PAYEE_CHAIN equal to PAYEE_CHAIN) and never written
here or anywhere in the repository; the derived table serves the testnet and the probes S11 expects
refused. The book's three payments on a real chain total one dollar (`aer360_answers.py`).
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

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
ASSET_DECIMALS = {"USDC": 6, "USDT": 6, "ETH": 18, "WETH": 18, "DAI": 18, "SOL": 9}  # SOL: nine decimals, money.ts ASSET_DECIMALS (Spec T29)

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
# Gas is a balance in dollars on the platform's gas ledger (U3), credited for the sandbox through the platform's ADMIN credit road — with
# the admin credential Bear files in ~/.aer360-harness/admin.env, never in the repository, never printed — only where the estate's review
# refuses GAS_SHORTFALL for the workspace (Spec T26, 4 October 2026: a credit is a cure for a refusal, never a standing order). The card
# road is Bear's.
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
GAS_CREDIT_USD_CENTS = 1000                  # U3 (Bear, 22 September 2026): "put $10 on our account every time"; accountabstraction.ts GAS_DEFAULT_TOP_UP_USD_CENTS — the size of one cure, made only on the review's GAS_SHORTFALL (Spec T26); Runner.gas_credit_for sizes a larger ceiling
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
# Spec T26 (4 October 2026): gas is credited only when the review says the account is short; never on a standing order. The owner's ruling on
# the estate run of 13:40 that day, which failed S7 on a credit nobody needed: "That is stupid. Why is that happening? It's certainly not my
# rule. So, undo that now." The sentences this spec adds, word for word (SPEC.md §3.1 to §3.3).
S7A_NOT_PROVABLE_PROBE = "S7a not provable this run"   # the finding's name under S7 and in the report's Findings (§3.2): never a fail, never a cause for a credit
S7A_NOT_PROVABLE_SENTENCE = "Harness Holdings' gas account holds %s, and this set needs at most %s; the gate admitted the set, which is right"
GAS_CURE_NEEDED_CLAUSE = "the review refused %s (%s), which a gas credit cures"   # §3.3: the refusal that needed the credit, said in S7's line before what stopped the cure (T14's sentence where no credential is filed)
GAS_CREDIT_HOLLOW_SENTENCE = ("the review refused %s again after the credit: the platform said %s was credited %s and its gas account held %s available, and the review says "
                              "the account holds %s — %r — so the platform did not credit what it said it did")   # §3.1: both figures, the platform's and the gate's


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


# ---------------------------------------------------------------------------
# THE OWNER'S OWN WALLET IS THE PAYEE ON A REAL CHAIN (Spec T24, 3 October 2026). The owner's two rulings of that night: "No more than
# $1." and "The money should always be paid to my MetaMask address. Always." Every address this file derives has no key behind it —
# harmless on the AEREDIUM testnet (SEAR), lost money on a real chain: since Spec T18 moved PAYEE_CHAIN to `arbitrum` the payments are
# real USDC, and the run of 28 September 2026 paid US$18.24 (HH-0001, HH-0002, HH-0003; Harness Holdings fell from US$50.00 to
# US$31.76) to addresses nobody can spend from, recorded as lost. So where PAYEE_CHAIN is not one of TESTNET_CHAIN_NAMES the harness
# reads ~/.aer360-harness/payee.env — a 0600 file beside the passkeys, filed by the owner with set_owner_payee.sh, never in the
# repository — and the address it names is Northwind Supplies', Contoso Legal's and the one-off destination's. The file missing or
# malformed stops S6 before any payee is made and S7 before any payment with NO_OWNER_PAYEE_SENTENCE, never a derived address on a
# real chain; a checksum that does not spell itself is malformed. On the testnet the derived table is used as before.
# ---------------------------------------------------------------------------
PAYEE_ENV_FILE = "payee.env"                     # under ~/.aer360-harness/, beside admin.env and the passkeys, mode 0600
OWNER_PAYEE_ADDRESS_KEY = "OWNER_PAYEE_ADDRESS"  # the owner's own wallet, spelled with its EIP-55 checksum
OWNER_PAYEE_CHAIN_KEY = "OWNER_PAYEE_CHAIN"      # the chain the file was filed for; it must equal PAYEE_CHAIN
OWNER_WALLET_WORDS = "the owner's wallet"        # the words every S7 payment line carries beside the payee's address on a real chain (Spec T24 §4)
DERIVED_WORDS = "a test address derived from the seed"  # the testnet's words in the same place
OWNER_PAYEE_PLACEHOLDER = "<%s from ~/.aer360-harness/%s>" % (OWNER_PAYEE_ADDRESS_KEY, PAYEE_ENV_FILE)  # what --dry prints: the printer never reads the file
ONE_DOLLAR_MINOR = 1000000                       # US$1.00 of USDC in minor units: the most the book's payments may total on a real chain (Spec T24 §3, §5)
# The sentences this spec adds, word for word (SPEC.md §1 and §2). The stop names ~/.aer360-harness whatever --store says, as admin.env's does.
NO_OWNER_PAYEE_SENTENCE = ("the owner's payee address is not filed at ~/.aer360-harness/payee.env (OWNER_PAYEE_ADDRESS); "
                           "on %s the harness pays only the owner's own wallet; nothing was sent")
ONE_OFF_ALREADY_PAID_SENTENCE = "the one-off destination is the owner's wallet, already paid by this estate, so Spec 69's hold is not provable this run"
ONE_OFF_NEW_SENTENCE = "the one-off destination is the owner's wallet, which this estate has never paid, so Spec 69's hold is provable this run"


def is_testnet(chain: Any) -> bool:
    """Whether a chain word names the AEREDIUM testnet under either of the estate's names for it (TESTNET_CHAIN_NAMES)."""
    return str(chain or "").strip().lower() in TESTNET_CHAIN_NAMES


def pays_a_real_chain(chain: Optional[str] = None) -> bool:
    """Spec T24: whether the payments' chain — PAYEE_CHAIN, read at call time — is a real chain, where the harness pays only the owner's wallet."""
    return not is_testnet(PAYEE_CHAIN if chain is None else chain)


def payee_words(chain: Optional[str] = None) -> str:
    """The words beside a payee's address in S7's line: the owner's wallet on a real chain, a derived test address on the testnet."""
    return OWNER_WALLET_WORDS if pays_a_real_chain(chain) else DERIVED_WORDS


def owner_payee_of(text: str, chain: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    The owner's wallet from payee.env's text, checked as Spec T24 §1 asks: (address, None) where OWNER_PAYEE_ADDRESS is 0x and forty hexadecimal
    characters spelling its own EIP-55 checksum, is none of the harness's derived addresses, and OWNER_PAYEE_CHAIN equals the payments' chain;
    else (None, what is wrong, in words naming the key), so the stop can say what it found rather than only that it stopped.
    """
    wanted_chain = str(PAYEE_CHAIN if chain is None else chain)
    values = parse_env_file(text)
    address = values.get(OWNER_PAYEE_ADDRESS_KEY, "").strip()
    filed_chain = values.get(OWNER_PAYEE_CHAIN_KEY, "").strip()
    if not address:
        return None, "names no %s" % OWNER_PAYEE_ADDRESS_KEY
    if len(address) != 42 or not address.startswith("0x") or any(c not in "0123456789abcdefABCDEF" for c in address[2:]):
        return None, "%s is not 0x and forty hexadecimal characters" % OWNER_PAYEE_ADDRESS_KEY
    if not is_checksummed(address):
        return None, "%s does not spell its own EIP-55 checksum (copy the address from the wallet again)" % OWNER_PAYEE_ADDRESS_KEY
    if is_pinned(address):
        return None, "%s is one of the harness's own derived test addresses, which no key stands behind" % OWNER_PAYEE_ADDRESS_KEY
    if not filed_chain:
        return None, "names no %s (the payments are made on %s)" % (OWNER_PAYEE_CHAIN_KEY, wanted_chain)
    if filed_chain.lower() != wanted_chain.lower():
        return None, "%s is %r, not %s, the chain the payments are made on" % (OWNER_PAYEE_CHAIN_KEY, filed_chain, wanted_chain)
    return address, None


# ---------------------------------------------------------------------------
# HARNESS REAL WORLD — THE BROWSER LEG'S ESTATE AND ITS UNTIDY FIXTURES (Spec HRW-1, written 7 October 2026, revised 9 October 2026). The
# browser leg (aer360_real_world.py) reads this file and the answer book as the API leg does, so the two legs cannot drift apart, and walks
# them as a real client comes (§4): each fixture below is a real founder's habit or fault met in the first fortnight of Group 100, listed
# beside the ruling or spec that made it a rule. Nothing here is an address of anyone's but the harness's own people and the owner's file.
# ---------------------------------------------------------------------------
# §2, the Attacker: the only estates the browser leg presses a control on. A page whose sidebar names another stops the run, nothing pressed.
HARNESS_ESTATE_NAMES = ("Harness Holdings Pty Ltd", "Harness Treasury")


def is_harness_estate(name: Any) -> bool:
    """One of the harness's own estates by the name its page shows: Harness Holdings Pty Ltd, or the Treasury — whose workspace the birth script names
    "Harness Treasury Pty Ltd", and which the API leg admits by its short name (TREASURY["short"])."""
    text = str(name or "").strip()
    return text in HARNESS_ESTATE_NAMES or text.startswith(HARNESS_ESTATE_NAMES[1] + " ")


# §4: the charter's addresses as a client types them — capitals and surrounding spaces — for the two people whose addresses the spec writes out.
# The estate folds what it compares and what it writes to the platform's roster (foldEmail: trimmed, lower-cased), so each is the same person as
# its folded form. Every other person keeps the book's own address (aer360_answers.PEOPLE).
REAL_WORLD_TYPED_ADDRESSES = {
    "harriet": "Harriet.Founder@aeredium.io ",
    "ada": " ADA.Approver@aeredium.io",
}
REAL_WORLD_BIRTH_EMAIL = "harriet.founder@aeredium.io"   # the birth's --email: the founder's address as the charter will fold it, so her seat is hers
REAL_WORLD_NAME_NOT_ADDRESS = "ben"                       # §4: the approver whose display name is not his address — Ben Signatory, harness+ben@aeredium.io
REAL_WORLD_TRAILING_SPACE_PAYEE = 1                       # §4: the second payee's address (PAYEES[1], Contoso Legal's) typed with a trailing space
# Spec T24's one-dollar book between the founder's two presses of Submit this run (§4: "The founder presses Submit this run twice"): R7 enters
# HH-0001 and HH-0002, R7b — a second, different run the same day under the same default reference — HH-0003. The two together are the book's
# dollar and no more ("No more than $1."), every payment to the owner's wallet; a second run that repeated the first's rows would meet the
# duplicate screen naming a payment of this very run, which Spec T28's bound never acknowledges.
REAL_WORLD_FIRST_PRESS = ("P1", "P2")
REAL_WORLD_SECOND_PRESS = ("P3",)

UNTIDY_FIXTURES: List[Tuple[str, str]] = [
    ("the estate is born by the CLI road the operator uses for clients, group100_invite.sh, never by a tidy fixture",
     "Spec 113 (29 September 2026), the birth script; the AER 360 Onboarding Road 1.5, §2"),
    ("the birth gives --email, and in one run deliberately does not: invite.mjs prints its one line, and the record script records the email",
     "Spec AER360-SEAT-CASE §3.2 and §3.3 (live 7 October 2026); the Onboarding Road 1.5, §8a"),
    ("the charter's addresses carry capitals and surrounding spaces (`Harriet.Founder@aeredium.io `, ` ADA.Approver@aeredium.io`)",
     "the owner's ruling of 6 October 2026, \"It should make no difference either way\"; Specs AAP-SEAT-CASE and AER360-SEAT-CASE §3.1"),
    ("one approver's display name is not their address (Ben Signatory, harness+ben@aeredium.io)",
     "Spec AER360-SEAT-CASE §3.1: the seat is found by the folded address, and display_name keeps the charter's name as typed"),
    ("the founder presses Submit this run twice in a day, under the same reference",
     "Spec AER360-RUN-ROAD §3.1 and §3.2 (live 7 October 2026): the press submits, and the idempotency key is per attempt"),
    ("one payee address is typed with a trailing space",
     "the Client Manual, ch. 7 Step 1: \"AER 360 checks the address as you type\"; shared/payeeaddress.ts trims before it judges"),
    ("the run's reference is left at its default",
     "Spec AER360-RUN-ROAD §1: the key was `${reference || 'run'}-${today}`, and a founder's second run of the day was refused as a replay"),
    ("the estate's signing entries are never set by hand: they stand at zero until the Policy Interview's write puts the charter's ceilings on them",
     "the owner, 7 October 2026 (the fixture of 9 October); Spec AER360-115: the compile writes C2 and C3 onto aer-accounts and every (author) entry"),
    # Spec T29 and HRW-2 (§4): the Solana road's two untidy fixtures, each a slip a founder makes with a base58 address
    ("a Solana payee's address is pasted with a trailing space (the estate trims it; the register shows it trimmed)",
     "Spec T29 and HRW-2 §4; shared/payeeaddress.ts judges the trimmed string (payeeAddressRefusal: address.trim()) and stores it verbatim"),
    ("a Solana address is pasted in the EVM field of an EVM payee (refused in the estate's sentence: not an address Arbitrum One can pay)",
     "Spec T29 and HRW-2 §4; shared/payeeaddress.ts ADDRESS_SHAPES.evm: an address is 0x followed by exactly 40 hexadecimal characters"),
]


# ---------------------------------------------------------------------------
# THE SOLANA ROAD (Spec T29 and HRW-2, written 24 October 2026, amended 30 October 2026): the two legs learn a second curve. Every route,
# shape and sentence below is read from aeredium/AERAccounts main at d369926 (Spec AER360-SOL-114, PR #143, 24 October 2026), never from
# memory, and the file each came from is named beside it:
#   apps/web/src/screens/Wallets.tsx and services/fundingwallet.ts — Create a new wallet asks the network first ("Which network does the
#     wallet stand on?": the Ethereum-family networks, or Solana), then whose wallet it is; both steps of the press carry `chain: 'evm' |
#     'solana'`; a Solana wallet is an Ed25519 pool key allocated through the gateway on Group 100 with `key_type ed25519`, its base58 address
#     recorded VERBATIM (the case is the key), its register row standing on `solana` alone with `addressForm: 'solana'` and `curve: 'ed25519'`
#     on the key's row; no recovery line is shown for it (the owner's ruling of 23 October 2026). The birth is not gated by the Solana road:
#     the allocation goes through the gateway, and nothing of SOLANA_RPC_URLS is read at a birth.
#   routes/payees.ts and packages/shared/src/payeeaddress.ts — a Solana address is judged at entry: the base58 shape (32 to 44 characters of
#     Bitcoin's alphabet), then exactly 32 bytes, then the Ed25519 curve, each fault in its own sentence under ADDRESS_MALFORMED (422), with
#     the fault named in the detail; the platform judges again at the whitelist write; beside a Solana address the register says
#     `solanaUsdcAccount` true, false ("has not received USDC yet", PayeeRegistry.tsx) or null (the road closed: the room says nothing).
#   packages/solana/src/address.ts — the judgment's three faults, `shape`, `length`, `off_curve`, and the curve's own arithmetic over
#     p = 2^255 − 19, which the harness carries below in pure Python, as the passkey's CBOR is carried, so the fault stations can build a
#     32-byte string no key produces without any library.
#   services/payoutsets.ts, services/execution.ts, services/solana/payroad.ts — the curve belt (assertCurveForChain) refuses a Solana payment
#     from an EVM wallet and an EVM payment from a Solana wallet, WALLET_CURVE_MISMATCH (422), at the review and again at execution; a payee
#     with no USDC account is refused SOLANA_TOKEN_ACCOUNT_ABSENT before anything is signed; the fee is the wallet's own lamports, topped up
#     by the platform's sponsor where they fall short of the reserve of 0.01 SOL (packages/solana/src/fees.ts FEE_RESERVE_LAMPORTS), the
#     top-up on the trail (operationId, reserveLamports, debit, sentReported); the message is signed through BIS 100 and broadcast by the
#     estate; the trail's `instruction.signing` row carries `road: 'solana'`, and the row lands with its signature as its hash and the slot on
#     `instruction.confirmed`.
#   services/solana/road.ts — a closed road is SOLANA_ROAD_CLOSED naming SOLANA_RPC_URLS; a stop between the two endpoints is
#     SOLANA_SOURCES_DISAGREE; the top-up's two ends are SOLANA_TOPUP_FAILED and SOLANA_TOPUP_EXPIRED; the review's Solana leg
#     (execution.ts solanaChainPreflight) refuses every Solana row with the closed road's own refusal, so a closed road refuses at the review.
#   packages/shared/src/refusals.ts and explain.ts — the sentences, and the founder's sentence beside each; apps/server/src/http.ts — the statuses.
#   routes/workspace.ts — GET /v1/workspace/sandbox-allowance (Spec AER360-117): the sandbox's allowance, what its payments have taken, what is
#     left, and the line the pages say; routes/aer360.ts — the register (GET /v1/aer360/wallets), the plan's signing group (GET /v1/aer360/plan),
#     the refresh that reads every wallet's holdings live (POST /v1/aer360/refresh: SOL always, USDC summed across every token account of the
#     configured mint, through the two-source reader — services/holdings.ts) and the overview that lists them per asset (GET /v1/aer360/overview).
# ---------------------------------------------------------------------------
SOLANA_CHAIN = "solana"                      # packages/shared/src/chains.ts: id `solana`, display name Solana, family solana, native asset SOL, payouts true
SOLANA_DISPLAY_NAME = "Solana"
SOL = "SOL"                                  # the native coin; nine decimals (money.ts ASSET_DECIMALS)
SOL_DECIMALS = 9
LAMPORTS_PER_SOL = 10 ** SOL_DECIMALS
FEE_RESERVE_LAMPORTS = 10_000_000            # packages/solana/src/fees.ts FEE_RESERVE_LAMPORTS: 0.01 SOL a wallet keeps back so its next payment can pay its own fee
SOLANA_CURVE = "ed25519"                     # wallet_keys.curve for a Solana birth (fundingwallet.ts); every EVM key is secp256k1
EVM_CURVE = "secp256k1"
SOLANA_RPC_SETTING = "SOLANA_RPC_URLS"       # config.ts: two endpoints open the road; fewer close it by name
SOLANA_MINT_SETTING = "SOLANA_USDC_MINT"
SOLANA_EXPLORER_TX_URL = "https://solscan.io/tx/"  # chains.ts explorerTxUrl for solana
PRODUCTION_SIGNING_GROUP = "group-100"       # the one signing group a client account stands on (Spec 113; the Group 100 brief of 27 September 2026)
# The roads (routes/workspace.ts, routes/aer360.ts).
WALLET_PRESS_OPTIONS_ROUTE = "/v1/workspace/wallets/options"   # step one of the press: whose, chain → options, issuedAtMs, walletId
WALLET_PRESS_ROUTE = "/v1/workspace/wallets"                   # step two: the same answers, the assertion, issuedAtMs, walletId → born, wallet, signingGroup
WALLETS_REGISTER_ROUTE = "/v1/aer360/wallets"                  # the register: wallets [{walletId, walletNumber, name, address, chains, keyed, level, …}]
PLAN_ROUTE = "/v1/aer360/plan"                                 # the plan, and signingGroup {accountId, assigned, standing, sentence}, read live from the platform
SANDBOX_ALLOWANCE_ROUTE = "/v1/workspace/sandbox-allowance"    # {realm, allowance: {allowanceUsdCents, spentUsdCents, leftUsdCents, said} | null}
REFRESH_ROUTE = "/v1/aer360/refresh"                           # POST (author): every wallet's holdings read live; {holdings: {taken, skipped: [{holder, wallet, asset, reason}], source}, …}
OVERVIEW_ROUTE = "/v1/aer360/overview"                         # {holders: [{name, wallets: [{id, walletNumber, name, holdingBaseMinor, absence, holdings: [{asset, chain, amountMinor, …}]}]}]}
READINESS_ROUTE = "/v1/workspace/readiness"                    # {transactable, reason, workspace}
ADMIN_POLICIES_ROUTE = "/v1/admin/accounts/%s/policies"        # the platform's read road of an account's entries (aapclient.ts listPolicyEntriesAsAdmin), as the browser leg's R3 reads it
# The refusals (refusals.ts REFUSAL_CODES and REFUSAL_MESSAGES; http.ts REFUSAL_STATUS), word for word.
SOLANA_ROAD_CLOSED = "SOLANA_ROAD_CLOSED"
SOLANA_TOKEN_ACCOUNT_ABSENT = "SOLANA_TOKEN_ACCOUNT_ABSENT"
WALLET_CURVE_MISMATCH = "WALLET_CURVE_MISMATCH"
SOLANA_SOURCES_DISAGREE = "SOLANA_SOURCES_DISAGREE"
SOLANA_TOPUP_FAILED = "SOLANA_TOPUP_FAILED"
SOLANA_TOPUP_EXPIRED = "SOLANA_TOPUP_EXPIRED"
SOLANA_REFUSAL_STATUSES = {SOLANA_ROAD_CLOSED: 503, SOLANA_SOURCES_DISAGREE: 503, SOLANA_TOKEN_ACCOUNT_ABSENT: 422, SOLANA_TOPUP_FAILED: 422,
                           SOLANA_TOPUP_EXPIRED: 422, WALLET_CURVE_MISMATCH: 422}
SOLANA_REFUSAL_SENTENCES = {
    SOLANA_ROAD_CLOSED: "The Solana road is closed on this deployment: it names fewer than two Solana endpoints (SOLANA_RPC_URLS). Nothing was read and nothing was sent.",
    SOLANA_TOKEN_ACCOUNT_ABSENT: "This payee has not received USDC yet, so there is no USDC account on Solana to pay into. Nothing was sent. The payee must receive USDC once before it can be paid here.",
    WALLET_CURVE_MISMATCH: "This wallet’s key is not of the curve this payment’s network runs on — a wallet pays only on the network its key’s curve belongs to. Nothing was sent.",
    SOLANA_SOURCES_DISAGREE: "The estate’s two Solana endpoints did not answer alike, so the Solana road is stopped. Nothing was read and nothing was sent.",
    SOLANA_TOPUP_FAILED: "The Solana network did not carry the sponsor’s fee top-up. Nothing left the wallet; the platform’s signed top-up stands unbroadcast, and a new run asks it again.",
    SOLANA_TOPUP_EXPIRED: "The sponsor’s fee top-up passed its last valid block height without landing on the Solana network, so this attempt is over. Nothing left the wallet; the retry broadcasts the platform’s same signed bytes again.",
}
# The founder's sentence beside each (explain.ts FOUNDER_SENTENCES, the Solana road's block; SEND_US is explain.ts's own closing line).
SEND_US = "Send the words above to us and we will tell you what to do."
SOLANA_FOUNDER_SENTENCES = {
    WALLET_CURVE_MISMATCH: "This wallet’s key is not of the curve this payment’s network runs on — a wallet pays only on the network its key’s curve belongs to, and nothing was sent. Make the payment again from a wallet of that network.",
    SOLANA_TOKEN_ACCOUNT_ABSENT: "This payee has not received USDC yet, so there is no USDC account on Solana to pay into. Nothing was sent. The payee must receive USDC once before it can be paid here.",
    SOLANA_SOURCES_DISAGREE: "The estate’s two Solana endpoints did not answer alike, so the Solana road is stopped. Nothing was read and nothing was sent, and the operations desk has been told.",
    SOLANA_ROAD_CLOSED: "The Solana road is closed on this deployment, so nothing was read and nothing was sent. " + SEND_US,
    SOLANA_TOPUP_FAILED: "The Solana network did not carry the sponsor’s fee top-up; its own final word is above. Nothing left the wallet, and the top-up is never paid for twice — make the run again and the platform answers the same signed top-up.",
    SOLANA_TOPUP_EXPIRED: "The sponsor’s fee top-up outlived its moment on the network without landing, so nothing left the wallet. Make the run again: the platform answers the same signed top-up under the payment’s own id, and the estate sends it again.",
}
# The curve belt's cause (payoutsets.ts assertCurveForChain), carried in the refusal's detail beside chain, curve and required.
CURVE_MISMATCH_CAUSE_SOLANA = "a Solana payment leaves only from a wallet whose key’s curve is recorded as ed25519"
CURVE_MISMATCH_CAUSE_EVM = "an EVM payment leaves only from a wallet whose key’s curve is secp256k1"
# The press refused a network that is neither (fundingwallet.ts judgePressAnswers): REQUEST_MALFORMED, 400.
WALLET_NETWORK_REFUSED_SENTENCE = "A wallet is born on the EVM networks or on Solana; answer the network question one way or the other."
# The payee door's words for a Solana address (payeeaddress.ts ADDRESS_SHAPES.solana, addressMalformedRefusal, solanaKeyRefusal): one code,
# ADDRESS_MALFORMED, three sentences — the fault travels in the detail (`fault`: shape, length, off_curve).
ADDRESS_MALFORMED = "ADDRESS_MALFORMED"
SOLANA_SHAPE_EXPECTED = "an address is 32 to 44 base58 characters, and base58 leaves out the digit zero, capital O, capital I and lower-case L"
EVM_SHAPE_EXPECTED = "an address is 0x followed by exactly 40 hexadecimal characters"
SOLANA_LENGTH_WORDS = "A Solana address is exactly 32 bytes in base58, and this string decodes to a different length."
SOLANA_OFF_CURVE_WORDS = "A Solana address is a key on Solana’s own curve, and this string — well-formed base58 though it is — is not one: no secret key produces it."
SOLANA_FAULTS = ("shape", "length", "off_curve")  # packages/solana/src/address.ts SolanaAddressFault, judged in this order
HAS_NOT_RECEIVED_USDC = "has not received USDC yet"  # PayeeRegistry.tsx, beside a Solana address whose solanaUsdcAccount reads false
# The trail's verbs on a Solana payment (services/audit.ts; execution.ts driveSolanaPayment), beside INSTRUCTION_CONFIRMED above.
INSTRUCTION_BUILDING = "instruction.building"
INSTRUCTION_SIGNING = "instruction.signing"
INSTRUCTION_BROADCASTING = "instruction.broadcasting"
INSTRUCTION_FAILED = "instruction.failed"
INSTRUCTION_REJECTED = "instruction.rejected"
SOLANA_ROAD_WORD = "solana"                  # `road` on every trail row of a Solana payment; `gas_roads` on an EVM one
SIGNATURE_BYTES = 64                         # packages/solana/src/sign.ts SIGNATURE_BYTES: an Ed25519 signature, and so the hash a Solana row lands with
# The cluster's refusal that names no rule (Spec T29 §0a.5): the exact words BIS 100's party 0 answers, filed under the Group 100 findings.
PARTY_0_DENIED = "policy evaluation on party 0 rejected the request: denied"
GROUP_100_FINDING_WORDS = "Group 100"        # the probe's opening words for a finding that is the cluster's, not the estate's
# THE BASE58 ALPHABET AND THE CURVE'S CONSTANTS (packages/solana/src/address.ts, byte for byte): no 0, no O, no I, no l; p = 2^255 − 19; the
# curve's d (−121665/121666 in the field, the published constant of RFC 8032); √−1 in the field (2^((p−1)/4) mod p).
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {ch: index for index, ch in enumerate(BASE58_ALPHABET)}
SOLANA_SHAPE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")  # address.ts judgeSolanaAddress's first fact; payeeaddress.ts ADDRESS_SHAPES.solana.fits
_P = (1 << 255) - 19
_EDWARDS_D = 37095705934669439343138083508754565189542113879843219016388785533085940283555
_SQRT_M1 = 19681161376707505956807079304988542015446066515923890162744021073123829784752


def base58_decode(text: Any) -> Optional[bytes]:
    """address.ts base58Decode: the text as one big-endian number, each leading '1' a leading zero byte; None where a character is not base58."""
    if not isinstance(text, str):
        return None
    if text == "":
        return b""
    value = 0
    for ch in text:
        digit = _BASE58_INDEX.get(ch)
        if digit is None:
            return None
        value = value * 58 + digit
    body = value.to_bytes((value.bit_length() + 7) // 8, "big") if value else b""
    leading = len(text) - len(text.lstrip("1"))
    return b"\x00" * leading + body


def base58_encode(raw: bytes) -> str:
    """address.ts base58Encode: each leading zero byte a '1', then the number in the alphabet."""
    leading = len(raw) - len(raw.lstrip(b"\x00"))
    value = int.from_bytes(raw, "big") if raw else 0
    out = ""
    while value > 0:
        value, digit = divmod(value, 58)
        out = BASE58_ALPHABET[digit] + out
    return "1" * leading + out


def is_on_curve(raw: bytes) -> bool:
    """
    address.ts isOnCurve, the curve's own arithmetic: the low 255 bits of the thirty-two bytes (little-endian) are y, which must be below p; the top
    bit is the sign of x and plays no part; x² = (y² − 1) / (d·y² + 1) must be a square in the field — found by the (p+3)/8 exponent, with the √−1
    correction the standard prescribes. A string of thirty-two bytes that is not a point is nobody's key.
    """
    if len(raw) != 32:
        return False
    y = int.from_bytes(raw, "little") & ((1 << 255) - 1)
    if y >= _P:
        return False
    y2 = (y * y) % _P
    u = (y2 - 1) % _P
    v = (_EDWARDS_D * y2 + 1) % _P
    x2 = (u * pow(v, _P - 2, _P)) % _P
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = (x * _SQRT_M1) % _P
        if (x * x - x2) % _P != 0:
            return False
    return True


def judge_solana_address(text: Any) -> Tuple[Optional[str], Optional[bytes]]:
    """
    address.ts judgeSolanaAddress, in its order: the shape, then exactly thirty-two bytes, then the curve. Answers (None, the bytes) for an address,
    else (the fault, the bytes where the shape fit): 'shape', 'length' or 'off_curve'.
    """
    if not isinstance(text, str) or not SOLANA_SHAPE.match(text):
        return "shape", None
    raw = base58_decode(text)
    if raw is None:
        return "shape", None
    if len(raw) != 32:
        return "length", raw
    if not is_on_curve(raw):
        return "off_curve", raw
    return None, raw


def is_solana_address(text: Any) -> bool:
    """True where the string is a Solana address in full: shape, bytes and curve (address.ts isSolanaAddress)."""
    return judge_solana_address(text)[0] is None


def solana_address_malformed_sentence(fault: str, named: str = SOLANA_DISPLAY_NAME) -> str:
    """payeeaddress.ts addressMalformedRefusal (shape) and solanaKeyRefusal (length, off_curve): the one code's three sentences, word for word."""
    base = "That is not an address %s can pay, so nothing was saved." % named
    if fault == "shape":
        return "%s On %s, %s." % (base, named, SOLANA_SHAPE_EXPECTED)
    if fault == "length":
        return "%s %s" % (base, SOLANA_LENGTH_WORDS)
    if fault == "off_curve":
        return "%s %s" % (base, SOLANA_OFF_CURVE_WORDS)
    raise ValueError("a Solana address has three faults, shape, length and off_curve, not %r" % fault)


def evm_address_malformed_sentence(named: str) -> str:
    """payeeaddress.ts addressMalformedRefusal for an EVM chain: what the door says to a Solana address pasted in an EVM payee's field (HRW-2 §4)."""
    return "That is not an address %s can pay, so nothing was saved. On %s, %s." % (named, named, EVM_SHAPE_EXPECTED)


def off_curve_variant(address: str) -> str:
    """
    Spec T29 §3.2's third slip: the real address decoded, a byte flipped until the harness's own on-curve check fails, re-encoded — a base58 string
    of thirty-two bytes that is well formed and is nobody's key. The low bytes are tried first (they are y's low bits); about half of all
    thirty-two-byte strings are off the curve, so the first flip or the second finds one.
    """
    fault, raw = judge_solana_address(address)
    if fault is not None or raw is None:
        raise ValueError("%r is not a Solana address (%s), so no off-curve variant of it can be built" % (address, fault))
    for index in range(0, 32):
        for flip in range(1, 256):
            candidate = bytearray(raw)
            candidate[index] ^= flip
            if not is_on_curve(bytes(candidate)):
                return base58_encode(bytes(candidate))
    raise ValueError("no byte of %s can be flipped off the curve" % address)


def short_variant(address: str) -> str:
    """Spec T29 §3.2's second slip: a base58 string of thirty-one bytes — the real address's first thirty-one bytes, re-encoded."""
    fault, raw = judge_solana_address(address)
    if fault is not None or raw is None:
        raise ValueError("%r is not a Solana address (%s), so no thirty-one-byte variant of it can be built" % (address, fault))
    return base58_encode(raw[:31])


def lamports_of(amount: str) -> int:
    """A plain decimal of SOL to lamports, by the same string arithmetic as minor_units (nine decimals)."""
    return int(minor_units(amount, SOL_DECIMALS))


def sol_words(lamports: Any) -> str:
    """Lamports as a plain decimal of SOL with the coin's name, by string arithmetic: 10000000 → "0.01 SOL", 2500000 → "0.0025 SOL", 0 → "0 SOL"."""
    n = int(lamports)
    if n < 0:
        raise ValueError("a balance is a non-negative integer of lamports: %r" % (lamports,))
    text = str(n).rjust(SOL_DECIMALS + 1, "0")
    whole, fraction = text[:-SOL_DECIMALS], text[-SOL_DECIMALS:].rstrip("0")
    return "%s%s SOL" % (whole, ("." + fraction) if fraction else "")


def curve_for_chain(chain: Any) -> str:
    """payoutsets.ts assertCurveForChain: `ed25519` for a payment on solana, `secp256k1` for every other chain."""
    return SOLANA_CURVE if str(chain or "").lower() == SOLANA_CHAIN else EVM_CURVE


def chain_family(chain: Any) -> str:
    """packages/shared/src/chains.ts: the family a chain's addresses belong to — solana for `solana`, evm for every other chain the registry pays."""
    return "solana" if str(chain or "").lower() == SOLANA_CHAIN else "evm"


def usdc_signal_words(signal: Any) -> str:
    """The register's `solanaUsdcAccount` beside a Solana address, in the words the room shows (PayeeRegistry.tsx): false is the room's sentence, null is silence."""
    if signal is True:
        return "a USDC account stands (solanaUsdcAccount true)"
    if signal is False:
        return "%s (solanaUsdcAccount false)" % HAS_NOT_RECEIVED_USDC
    return "the room says nothing (solanaUsdcAccount null: the road is closed, or the signal was never read)"


# The sentences the Solana stations say (Spec T29 §0a, §3), word for word, so a test holds each.
SOLANA_PAYEE_KEY = "SOLANA_PAYEE"            # the payee.env key §3.2 drafted and §0a.2 retired: present, it is ignored and the report says so
SOLANA_WALLETS_FILE = "solana-wallets.json"  # under ~/.aer360-harness/<estate>/: the two Solana wallets S5s pressed for (no key in it), reused by later runs
SOLANA_PAYEE_IGNORED_SENTENCE = ("%s in ~/.aer360-harness/%s is ignored: the Solana payment's destination is the harness's own second Solana wallet, born on the "
                                 "threshold cluster at S5s, never an address outside the estate (the owner's ruling of 29 October 2026, Spec T29 §0a.2)" % (
                                     SOLANA_PAYEE_KEY, PAYEE_ENV_FILE))
SOLANA_AMOUNT_NOT_WRITTEN_SENTENCE = ("the book names no SOL amount for the Solana payment (aer360_answers.SOLANA_PAYMENT_SOL is None): the figure is the owner's, "
                                      "written in the book by him, and the brief writes none (Spec T29 §0a.3); nothing was sent")
SOLANA_FUNDS_LINE = "the Solana wallet's address: %s — the owner sends the SOL once, at his amount, from his own wallet; the payment needs %s plus the %s fee reserve (Spec T29 §0a.3)"
WAITING_FOR_SOL_SENTENCE = ("waiting for the owner's SOL: the Solana wallet %s holds %s and the payment needs %s plus the %s fee reserve (%s in all), read from the estate's "
                            "holdings road; the owner sends it once, at his amount, from his own wallet; the wait of %d s under --funds-wait ran out and nothing was sent")
NO_ROOM_UNDER_THE_DOLLAR_SENTENCE = ("no room under the one-dollar total (Spec T24): the book's payments on %s come to %s and the Solana payment is worth %s at the estate's "
                                     "own valuation, %s in all; the harness refuses to exceed one dollar in a run, and nothing was sent")
ALLOWANCE_SHORT_SENTENCE = "the sandbox allowance is short: the estate says \"%s\", and the Solana payment is worth %s at the estate's valuation; nothing was sent (Spec T29 §0a.6)"
SOLANA_SKIPPED_SENTENCE = "the Solana stations after S5s are skipped by name: %s"
SOLANA_NOT_ALLOWED_SENTENCE = ("the account's allowed chains lack solana: the platform's entries in force name %s, so the cluster's party 0 would refuse every Solana "
                               "payment with no rule named; the owner adds solana by the admin road before the Solana stations walk (Spec T29 §0a.4); nothing was pressed")
WRONG_SIGNING_GROUP_SENTENCE = ("the workspace %s (account %s) stands on %s, not %s: the harness refuses to run at all on a workspace off the production signing group "
                                "(Spec T29 §0a.4; the journal of 29 October 2026 shows a Harness Holdings row standing on group-3); nothing was pressed")
CLOSED_ROAD_TRUTH_TOLD = "the road is closed, and the estate said so by name: %s — truth told, zero moved"

