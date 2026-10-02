#!/usr/bin/env python3
"""
PATHFINDER, THE AER CONNECT OWNER HARNESS (Spec H-PATHFINDER, 2 October 2026): the script becomes the owner and walks
AER Connect A to Z, all the way to a trade.

The ruling of 2 October 2026: "create a harness that checks the entire MCP A to Z for bugs; the Python script becomes
the owner; go all the way to trade." The corridor harness assumes a person did the owner's half first — signed up,
created the agent, set its limits, bought gas, connected Claude. Pathfinder does that half itself, as the owner and as
its agent (a Trader, role trader.v1), and then trades.

Two laws, as the other harnesses keep them:

  THE HARNESS IS THE OWNER, NOT A JUDGE. It speaks to the connector exactly as the account page and the consent page do
  — JSON over HTTP under the owner's own session and software passkey — and to the MCP exactly as Claude does, under the
  per-connection credential the consent hands over. It holds no key, no rail and no rule of its own.

  A FAILURE IS EVIDENCE, NOT A VERDICT. Every step records what was sent, what came back word for word, the route, the
  expectation and the result, secrets redacted to their last four characters, and never a paraphrase or a guessed cause.
  Where a door or the platform refuses, the line quotes the server's own sentence first, then the lexicon's one-line
  description; a cause the lexicon does not know is quoted verbatim and marked unclassified.

THE STATIONS, A TO Z
  S1  Sign up            POST /v1/auth/signup/options, /verify — born once; a stored passkey is signed in with
  S2  The account        GET /v1/account — the owner born once, the seat's standing, the assigned group group-100
  S3  Create agent       GET /v1/account/agents/new, the step-up, POST /v1/account/agents — trader.v1, this run's own agent
  S4  Recall the policy  POST /v1/account/agents/:id/policy — the policy S3 was born with, recalled and re-filed as an edit;
                         the pact keeps its id, the agent and its token are not touched (the law of 2 October 2026)
  S5  The child wallet   GET /v1/account/agents/:id/wallet-record — provisioned, not a mock, the owner's
  S6  Buy gas            POST /v1/account/gas (the floor, then ten dollars), GET /v1/account/gas-account — read live
  S7  Connect Claude     /authorize, the consent's step three, /finish, /token — the per-connection credential
  S8  The catalogue      MCP initialize, tools/list — the fourteen tools
  S9  The agent          aerconnect_my_agent — the wallet UUID, the pact, the gas balance
  S10 The judgment       police.check_action — the trade within the mandate, a receipt
  S11 The trade          the agent's wallet funded by Harness Holdings through the estate's own road where it is short (Spec T23),
                         then wallet.build_transaction, wallet.submit_transaction — a real swap, landed, sponsored by the paymaster
  S12 The reader         the chain and the gas trail — the swap on chain, the debit with its 10% charge, the balances reconciled
  S12a The commission check  the trading fee on chain: five basis points of the trade's output, in the ERC-20 Transfer logs, to
                         the agents' fee address — FEE_BPS and FEE_ADDRESS read from tables.py, judged by fee_check
  S13 Teardown           revoke, halt, delete — the agent this run created; the owner is never touched

REUSED, NOT REIMPLEMENTED (AAOI OP1). `corridor_consent.py` is the owner: `HarnessCustomer` signs up once, signs in with
the stored passkey, saves the sign count BEFORE every assertion and never resends one, and steps up per press; its wire
carries the cookie and the CSRF header and records every exchange redacted to the last four characters. S7 walks the
consent with that module's pieces (the authorize link, the stage words, the code and state readers, the seat sentence) but
not with `Consent` itself, whose create branch would make a second agent wherever this run's is not listed (below).
`corridor_harness.py` is the OAuth road (`Oauth`, `pkce_pair`, the token store), the MCP session (`Mcp`, whose
`rpc` alone is restated here so its record is redacted to the last four characters as the law asks), the readers of a
door's answer (`classify_police`, `classify_wallet`, `who_answered`, `arguments_for`, `gas_account_in`), the chain
(`ChainRpc`, `transfers_in`, `event_topic`, `checksum_address`) and the run folder. `aer360_passkey.py` is the passkey,
through the consent module, unchanged. What is new here: the owner's stations (create agent, set limits, read the
wallet, buy gas), the trade stations, the teardown, the guard and the lexicon.

THE OWNER IS BORN ONCE (AAOI AT1, OP2). One owner per name, under the corridor harness's own convention:
`harness+<name>@aeredium.io`, display name `<name> (harness)`, its passkey and customer id at
`~/.connect-harness/<name>/passkey.json` and `customer.json`, mode 600. There is no owner-delete route, so a fresh owner
per run would litter the connector with owners nobody can remove: the owner is born once and reused, and only the
per-run agent is created and torn down. A customer.json without its passkey is an owner whose key is lost, and the run
stops rather than bear a second owner.

THE GUARD (AAOI AT1). Every state-creating station — the sign-up, the agent's creation, its limits, the gas press, the
connection, the trade — refuses a base URL that is not a declared test ring unless `--i-mean-it` is passed, in one
sentence. A test ring is declared with `--test-ring`, the sandbox among them: no source the harness reads names the
sandbox's host, and the default base is the customer connector the Owner's Guide sends owners to, so a run with no flag
creates nothing anywhere. The reads are never refused, and neither is the teardown, which removes only what runs of this
harness created.

THE TEARDOWN (AAOI AT2). After the run — or after an early stop, or an interrupt — S13 revokes the connection this run
made, halts the agent this run created and deletes it, and the report names what was removed. It never attempts to
delete an owner. Every run writes its state to `~/.connect-harness/<name>/run.json` (mode 600) the moment it is about to
create anything — S3's press is written down before it is sent, so an agent whose answer was lost is found by its label —
and nothing a run created is ever recorded nowhere: a run that starts at or before S3 sets an earlier run's standing agent
aside in `earlier` and removes it beside its own; a run resumed past S3 (`--from`) takes the standing agent up as its own
and tears it down at its end; what cannot be removed (a delete refused while the wallet holds funds) stays on record, in
the connector's words, for the next run. An owner, its stored credentials and its agents belong to one connector: a run
on another base signs nothing in, sends no credential and removes nothing there.

THE LEXICON (AAOI OP2, AT3) is the connector's error dictionary, mirrored: `LEXICON` below, one entry per named cause,
each with its one-line description and the source it was read from. The dictionary is the connector's
`packages/shared/src/errors.ts`; until that file is merged the mirror is pending with the recorded reason
(`LEXICON_PENDING_REASON`) and every entry is read from its owning service's own source; the moment the file exists,
`tests/test_aerconnect_lexicon.py` fails on any drift and never skips.

READ FROM THE CODE RATHER THAN FROM MEMORY, in fresh clones (as T21 read the connector):
  aeredium/aer-connector at 9e20d6c (Spec 59):
    apps/server/src/routes/account.ts   GET /v1/account; GET /v1/account/agents/new (roles with their questionnaire, the
                                        chain offer; it provisions the account, so it is guarded with the press);
                                        POST /v1/account/agents {name, roleId, fundingAddress, answers, nonce, issuedAtMs,
                                        response}; POST /v1/account/agents/:id/policy {answers}; GET
                                        /v1/account/agents/:id/wallet-record (read through the agent's own connection,
                                        so before S7 it says why it cannot); POST /v1/account/gas {amountUsd} (US$10.00
                                        floor, refused below it by name; a Stripe Checkout, credited only by the desk's
                                        signed event); GET /v1/account/gas-account; POST /v1/account/agents/:id/halt and
                                        /delete {reason} (a delete refuses while the wallet holds funds); POST
                                        /v1/account/connections/:id/revoke {reason}
    apps/server/src/routes/consent.ts   answersBody {perTxUsd, dailyUsd, holdAboveUsd, maxTxPerDay, chains, assets?,
                                        counterpartiesScope, counterparties}; readAnswers; questionnaireFor (the two
                                        budgets open empty and are the owner's own figures); finishBody {agentId} for
                                        an agent born on the dashboard (Spec 35)
    apps/server/src/services/mcprelay.ts tools/list is the connector's two tools first, then the doors' own, prefixed;
                                        aerconnect_my_agent answers wallet {id, address, chain}, limits {pactId, state,
                                        documentHash, policyHash, document}, gas_account and gasAccount
    packages/shared/src/refusals.ts, apps/server/src/http.ts   the codes, their sentences, their statuses
  aeredium/mcp-police at c2af71c: check_action's inputSchema (role_id, action_kind, asset_symbol, amount_usd_cents in
    cents, child_wallet_id, contract_address, to_asset, venue) and its verdict and receipt
  aeredium/stablepro-agent-server at 125f788: internal/mcp/catalog.go (build_transaction, submit_transaction,
    ticket_status, get_balances and their required fields); the UserOperationOutcome a submit answers with; the
    Chainlink ETH/USD feed on Arbitrum the Wallet reads (internal/execution/onchain/oracle/feeds.go)
  aeredium/aegiskey-access-platform at ef57388: internal/gas/dollars.go GasAndServiceCents (the debit is gas plus a
    service charge of AAP_GAS_MARGIN_BPS, ten percent, at least one cent); the lexicon's platform words
  aeredium/api_bis3 at 345be29: cmd/api-gateway/refusal_prefix.go and docs/enclave-envelope-source.md (Spec GP1)

WHERE THE SPEC AND THE CODE PART COMPANY, each cited here and in the README (the charter: say so, cite both):
  1. S10. The spec names `police.can_sign`. MCP Police registers no tool by that name on main or on any branch (`git log
     -S can_sign` finds nothing); its judgment, with a receipt, is `check_action`, and S10 calls it. `can_sign` is a
     field (the Wallet's pact block), not a tool.
  2. S7. The spec names `POST /v1/consent/:id/agent` with the step-up. That press CREATES an agent (routes/consent.ts), so
     after S3 it would make a second one and spend a second seat. An agent born on the dashboard is connected by `/finish
     {agentId}` (Spec 35), and S7 presses only that, for this run's agent as the stage lists it, stopping where the stage
     lists no such agent; the step-up the spec asks for is made once, at S3's press, where the ruling of 8 September 2026
     puts it.
  3. S8. The fourteen are the two connector tools, the eight Wallet tools the architecture of 2 October 2026 names, and
     the four Police tools its own source registers beside the assignment tools the architecture says are hidden from a
     paying agent. The Wallet's source also registers `get_crossing` (Spec 46), and the relay at 9e20d6c lists the
     assignment tools under their not-the-road description; where the live catalogue carries them, S8 names each.
  4. S2. GET /v1/account at 9e20d6c states the account's signing group on no field (the group is
     CONNECTOR_SIGNING_GROUP, named at the account's birth); S2 reads every field that could carry it and says so.

THE HARNESS FUNDS ITS OWN AGENT (Spec T23, 2 October 2026; Bear: "I am not intervening in the harnessed dealings. It has to be done
automatically. We already financed the gas. That's all there is."). The run of that evening stopped at S11 waiting for a person to send
ten cents to the child wallet. The harness IS the owner; the owner's money is Harness Holdings'; and the estate harness already moves
Holdings' USDC with no key in anyone's hands, through AER 360's own payment road (`aer360_harness.py`). So where S11 finds the wallet
short of TRADE_RAW it makes the wallet a payee of Harness Holdings exactly as the estate harness's S6 makes Northwind one
(`aer360_estate_road.propose_payee`, one writing shared by both), has Holdings pay it TRADE_RAW and no more through T14's machinery
by import (`Runner.pay`: review, create, submit, the signers' presses, execute, the landing reads; `treasury_pays_the_shortfall` where
Holdings is short; `credit_gas` through the admin road where the review refuses for want of gas), and waits for its own money: the set
settled, the instruction confirmed, the wallet's USDC read through wallet.get_balances. The estate's people come from where they are
(`~/.aer360-harness/`); the one sentence on this road that names a thing a person must do is T14's treasury top-up. And S3 sends, S5
and S9 expect, the funding wallet the connector's own register holds for an owner that already exists (`GET /v1/account`): a funding
root is registered once (connector Spec 8), and the file is read only when the owner's root is about to be registered.

THE LIVE TIGHTENING (AAOI IM3) is a marked second pass: every body below is derived from the source, and only the bodies
the source leaves genuinely ambiguous carry a LIVE-TODO comment. `--dry` is the walk, green now; the live run is proven
once the production connector is deployed.

Runs on the Mac's own Python 3.9 with the standard library, and /usr/bin/openssl through aer360_passkey.py.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corridor_harness as H  # noqa: E402  (the OAuth road, the MCP session, the chain, the redaction, the run folder)
import corridor_consent as C  # noqa: E402  (the harness's own customer and the consent road)
import series as S  # noqa: E402
import tables as T  # noqa: E402
import aer360_answers as A  # noqa: E402  (Harness Holdings' people, by name: the founder, the roster, the clerk)
import aer360_estate_road as R  # noqa: E402  (the estate's payee road, one writing shared with the estate harness's S6)
import aer360_harness as E  # noqa: E402  (the estate harness: its Runner is the road Harness Holdings pays on — review, create, submit, sign, execute, land)
import aer360_tables as ET  # noqa: E402  (the estate's own words for money, the Treasury, the admin credential)

# ---------------------------------------------------------------------------
# Where it runs, who it is, where it keeps things.
# ---------------------------------------------------------------------------
DEFAULT_BASE = H.DEFAULT_ISSUER  # the customer connector the Owner's Guide sends owners to — not a test ring
# The declared test rings: none is built in. The sandbox connector's host is named in no source the harness can read (the
# connector's README: it "travels in the email with the keys"), so the sandbox, like any test ring, is named with --test-ring,
# and every other base — the customer connector the harness defaults to among them — refuses every state-creating station
# without --i-mean-it.
TEST_RINGS: Tuple[str, ...] = ()
STORE_DIR = "~/.connect-harness"  # ~/.connect-harness/<owner>/: passkey.json, customer.json, client.json, run.json, tokens
# The estate the owner's money is in (Spec T23): Harness Holdings and Harness Treasury as the estate harness left them — the people's
# passkeys under ~/.aer360-harness/harness-holdings/ and harness-treasury/, the platform's admin credential in admin.env, the funding wallet
# file beside them. The base is the estate harness's own default (aer360_tables.py names no base URL; aer360_harness.py does).
ESTATE_BASE = E.DEFAULT_BASE
ESTATE_STORE_DIR = C.AER360_STORE_DIR
RUNS_DIR = H.RUNS_DIR  # the report and the evidence go to a folder of their own here, never into the checkout
DEFAULT_OWNER = "pathfinder"  # harness+pathfinder@aeredium.io
EXPECTED_GROUP = "group-100"  # S2: the production signing group (the Group 100 brief of 27 September 2026)
ROLE = "trader"
ROLE_ID = S.ROLE_IDS[ROLE]  # trader.v1
AGENT_NAME = "%s-trader-%s"  # <owner>-trader-<run id>: the per-run agent, and its consent label
RUN_FILE = "run.json"
RUN_ID_FORMAT = "%Y%m%d-%H%M%S"
REASON = "Pathfinder run %s: the harness tears down the agent it created"  # the {reason} revoke, halt and delete carry

# The connector's own roads (apps/server/src/routes/account.ts at 9e20d6c).
ACCOUNT_ROUTE = "/v1/account"
AGENTS_NEW_ROUTE = "/v1/account/agents/new"
AGENTS_ROUTE = "/v1/account/agents"
POLICY_ROUTE = "/v1/account/agents/%s/policy"  # the edit road; the old /limits road was removed by Spec C-BIRTH-100
WALLET_RECORD_ROUTE = "/v1/account/agents/%s/wallet-record"
GAS_ROUTE = "/v1/account/gas"
GAS_ACCOUNT_ROUTE = "/v1/account/gas-account"
HALT_ROUTE = "/v1/account/agents/%s/halt"
DELETE_ROUTE = "/v1/account/agents/%s/delete"
REVOKE_ROUTE = "/v1/account/connections/%s/revoke"
DISCOVERY_ROUTE = "/.well-known/oauth-authorization-server"
RESOURCE_ROUTE = "/.well-known/oauth-protected-resource" + H.MCP_PATH
CLIENT_NAME = "aerconnect-harness"

# The gas press (services/billing.ts GAS_MINIMUM_TOP_UP_USD_CENTS; routes/account.ts gasBelowMinimumSaid).
GAS_MINIMUM_USD_CENTS = 1000
GAS_BELOW_FLOOR_USD = "9.99"  # pressed first: refused by name, naming the floor, and nothing is opened
GAS_FLOOR_SAID = "below the least gas that can be bought at once, which is US$10.00"

# ---------------------------------------------------------------------------
# The stations, and which of them create state (the guard).
# ---------------------------------------------------------------------------
STATIONS: List[Tuple[str, str]] = [
    ("S1", "Sign up"), ("S2", "The account"), ("S3", "Create agent"), ("S4", "Set the policy"), ("S5", "The child wallet"),
    ("S6", "Buy gas"), ("S7", "Connect Claude"), ("S8", "The catalogue"), ("S9", "The agent"), ("S10", "The judgment"),
    ("S11", "The trade"), ("S12", "The reader"), ("S12a", "The commission check"), ("S13", "Teardown"),
]
STATION_IDS = [station for station, _ in STATIONS]
TITLES = dict(STATIONS)
# What each state-creating station would do, as the guard's sentence says it.
GUARDED = {"S1": "sign up an owner", "S3": "create an agent", "S4": "recall and re-file an agent's policy", "S6": "buy gas",
           "S7": "connect Claude", "S11": "trade"}

PASS = "pass"
FAIL = "fail"
STOPPED = "stopped"  # the station met something it could not get past by itself: a seat, the wallet's funds, a key
GUARDED_OUT = "refused by the guard"
NOT_RUN = "not run"  # a station before it did not deliver what it needs; the sentence names which
SKIPPED = "skipped"  # passed over by --from

GUARD_SENTENCE = ("%s is not a declared test ring (a test ring, the sandbox among them, is named with --test-ring), so the harness "
                  "refuses to %s there without --i-mean-it.")
# What this run holds, and the station whose own line says why: never a cause in the world the harness does not know (a press
# whose answer was lost may have created the agent, and a Police that did not answer may have issued a receipt).
NO_SESSION = "the owner holds no session: its sign-in did not complete (S1's line says why, or the resume's where S1 was passed over)"
NO_AGENT = "this run holds no agent: S3 named none (its own line says why)"
NO_CONNECTION = "this run holds no credential for the agent: S7 did not connect Claude (its own line says why)"
NO_MCP = "there is no MCP session: S8 did not open one"
NO_WALLET_ID = "the agent's wallet UUID is not known: neither S3 nor S9 named it"
NO_RECEIPT = "this run holds no Police receipt for the trade: S10 obtained none (its own line says why)"
NO_LANDING = "S11 did not confirm a landed swap on chain (its own line says why), so there is no landed operation to read"
# S12a. The rate and the fee wallet are tables.py's (T.FEE_BPS, T.address("FEE_ADDRESS")) and the arithmetic is
# corridor_harness.fee_check: read, never declared here, so the owner harness and the corridor harness check one figure against
# one wallet. A Solana fee address would be pinned in tables.py under this key; tables.py pins none (the corridor's knowledge base:
# "Solana and native Bitcoin, deferred"; the MCP Wallet's fee recipient is an EVM address), and the harness never invents one.
SOLANA_FEE_KEY = "FEE_ADDRESS_SOLANA"
NO_SOLANA_FEE_SENTENCE = ("tables.py pins no Solana fee address (no %s entry), so the SPL transfer the commission rides in on %s was not "
                          "judged; the harness never invents a destination or a fee address")
KEY_LOST_SENTENCE = ("the owner %s was born (%s) but its passkey is not at %s: a sign-up now would be a second owner nobody can "
                     "remove; restore the passkey file, or set the folder aside to be born again")
OTHER_BASE_SENTENCE = ("the owner %s (customer %s) was born at %s, and this run's base is %s: an owner is born once per connector "
                       "and its passkey is that connector's; run as another --owner for this base")
NO_RESUME_SENTENCE = ("no agent of an earlier run stands to resume with (%s names none that was not torn down): run from S1, "
                      "which creates this run's own")

# ---------------------------------------------------------------------------
# The fourteen tools (S8): the connector's two, the Wallet's eight, the Police's four.
# ---------------------------------------------------------------------------
CATALOGUE: Tuple[str, ...] = (
    # the connector's own, first in the list (services/mcprelay.ts myAgentListing and guideListing)
    "aerconnect_my_agent", "aerconnect_guide",
    # the Wallet door, the hands: the eight the architecture of 2 October 2026 names, each in internal/mcp/catalog.go
    "wallet.wallet_status", "wallet.mint_wallet", "wallet.get_address", "wallet.get_balances",
    "wallet.build_transaction", "wallet.submit_transaction", "wallet.ticket_status", "wallet.my_usage",
    # the Police door, the judge and its reads: the four src/server.ts registers beside the two assignment tools, which
    # the architecture hides from a paying agent; no commit of MCP Police has ever registered a tool called can_sign
    "police.list_roles", "police.describe_role", "police.check_action", "police.my_usage",
)
CATALOGUE_SIZE = 14

# ---------------------------------------------------------------------------
# The trade (S10 to S12): one real swap on Arbitrum One, where the group-100 paymaster lives.
# ---------------------------------------------------------------------------
# Ten cents of USDC for WETH through Uniswap v3's SwapRouter02 on Arbitrum (pinned in tables.py, the first line of B3's
# list). Small on purpose, and the size is the teardown's: a delete refuses while the wallet holds funds — a cent of a
# stablecoin, 0.0001 WETH (Spec 45 §5, routes/account.ts) — and ten cents of WETH is below that, so the swap leaves dust
# the delete names and abandons rather than funds it refuses over.
TRADE: Dict[str, Any] = {
    "action": "trade", "chain": "arbitrum", "asset": "USDC", "to_asset": "WETH", "venue": "uniswap_v3",
    "contract_address": T.address("UNISWAP_V3_ARBITRUM"), "amount_usd": 0.10,
}
TRADE_USD_CENTS = 10
TRADE_RAW = TRADE_USD_CENTS * 10 ** (T.DECIMALS["USDC"] - 2)  # 100000: ten cents of USDC at six decimals
# S11 FUNDS THE AGENT ITSELF (Spec T23; Bear, 2 October 2026: "I am not intervening in the harnessed dealings. It has to be done
# automatically. We already financed the gas. That's all there is."). The harness IS the owner; the owner's money is Harness Holdings';
# and the estate harness already moves Holdings' USDC with no key in anyone's hands, through AER 360's own payment road. So where the
# child wallet is short of TRADE_RAW, S11 makes the wallet a payee of Harness Holdings (exactly as the estate harness's S6 makes Northwind
# one) and has Holdings pay it TRADE_RAW and no more — reviewed, created, submitted, approved by the signers and executed by its author
# through the estate's own machinery (aer360_harness.Runner.pay), with Harness Treasury paying Holdings the shortfall first where Holdings
# is short (T14) and gas credited through the platform's admin road where the review refuses for want of it (T14). The only sentence on
# this road that names a thing a person must do names a treasury top-up (T14's), never a per-run act. No key is anywhere.
PAYEE_NAME = "%s (agent wallet)"  # <owner>-trader-<run id> (agent wallet): the payee that is this run's agent
FUNDING_SENTENCE = "funding %s on %s with US$0.10 of USDC from Harness Holdings through the estate's own road: set %s, run %s"
FUNDED_SENTENCE = "the wallet holds %d minor units of USDC now (handleOps %s); the trade goes on"
SHORT_SENTENCE = "the wallet %s on %s holds %s, and the swap needs %d minor units of USDC: Harness Holdings funds it through the estate's own road"
HELD_ALREADY_SENTENCE = "the wallet %s on %s holds %d minor units of USDC already, at or above the swap's %d, so nothing is funded this run"
NOT_LANDED_SENTENCE = ("the wallet %s on %s holds %s, and the swap needs %d minor units of USDC: the payment Harness Holdings made for it (set %s) "
                       "had not landed within %d s — %s; no swap was made")
PAYEE_REFUSED_SENTENCE = "the estate refused the agent's wallet %s as a payee — %s; nothing was sent"
NOT_WHITELISTED_SENTENCE = "the estate's register reads %s for the payee %s, not whitelisted (%s); nothing was sent"
FUNDING_FAILED_SENTENCE = "the funding payment from Harness Holdings did not land — %s; no swap was made"
TREASURY_PAYMENT_FAILED_SENTENCE = "Harness Treasury's payment of the shortfall to Harness Holdings did not land — %s; nothing was sent to the agent's wallet"
# The estate harness's own sentence for a founder it holds no passkey for (aer360_harness.py, station_s1), with what to run first.
ESTATE_FOUNDER_ABSENT = "no passkey is stored for %s at %s and no --invite <link> was given; the first run needs the invitation link"
RUN_THE_ESTATE_FIRST = "run aer360_harness.py first"
NO_ESTATE_FOUNDER_SENTENCE = "%s — " + ESTATE_FOUNDER_ABSENT + "; " + RUN_THE_ESTATE_FIRST + " (S1 enrols Harness Holdings' founder); nothing was sent"
NO_ESTATE_WALLET_SENTENCE = "Harness Holdings has no funding wallet to pay from — %s; " + RUN_THE_ESTATE_FIRST + " (S5 births the funding wallet); nothing was sent"
ESTATE_NOT_HOLDINGS_SENTENCE = "the founder's session at %s names the workspace %r, not %r; nothing was sent"
# The ERC-4337 paymaster deployed for group-100 on Arbitrum, as the architecture of 2 October 2026 names it ("the ERC-4337
# paymaster at 0x2275…70ec on Arbitrum"); the platform's gas road points at it on P0. Read off the chain, never sent to.
PAYMASTER = {"arbitrum": "0x2275c477acef13886c0cb3eb7ab55ea1e07370ec"}
# Chainlink's ETH/USD feed on Arbitrum One, as the MCP Wallet reads it (stablepro-agent-server
# internal/execution/onchain/oracle/feeds.go, chain 42161, "ETH"). Read off the chain, never sent to.
ETH_USD_FEED = {"arbitrum": "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612"}
LATEST_ROUND_DATA = H.selector("latestRoundData()")
FEED_DECIMALS = H.selector("decimals()")
# The EntryPoint's own event (ERC-4337 v0.6 and v0.7 alike): userOpHash, sender and paymaster indexed.
USER_OPERATION_EVENT = H.event_topic("UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)")
MARGIN_BPS = 1000  # AAP_GAS_MARGIN_BPS, ten percent by the ruling of 24 September 2026 (internal/gas/dollars.go)
# The platform values the gas at its own price of the moment it quoted (internal/gas/price.go: a spot price cached up to
# five minutes); the reader values it at Chainlink's at the landing block, so the debit is judged within a band of two
# percent either way of that price, and to the cent at each end of it.
PRICE_BAND_BPS = 200
# The doors' inputSchemas as their own sources declare them, for the DRY WALK ONLY, so a dry print names the fields each door
# takes (MCP Police at c2af71c src/server.ts check_action; the MCP Wallet at 125f788 internal/mcp/catalog.go). A live call is
# shaped to the schema tools/list hands over, never to these.
DRY_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "police.check_action": {"type": "object", "required": ["role_id", "amount_usd_cents"], "properties": {name: {} for name in (
        "role_id", "action_kind", "chain", "to_chain", "asset_symbol", "venue", "to_asset", "route_chosen_by", "route_detail", "function",
        "amount_usd_cents", "child_wallet_id", "to_address", "counterparty_address", "contract_address", "method_selector",
        "spent_today_usd_cents", "transactions_today", "slippage_bps", "price_deviation_bps", "simulation_passed", "oracle_check_passed")}},
    "wallet.build_transaction": {"type": "object", "required": ["wallet_id", "action"], "properties": {name: {} for name in (
        "pact_id", "wallet_id", "action", "amount_usd", "to_address", "chain", "asset", "venue", "function", "counterparty_address",
        "contract_address", "to_asset", "to_chain", "method_selector", "approval_id", "client_request_id", "police_receipt")}},
    "wallet.submit_transaction": {"type": "object", "required": ["agent_id", "wallet_id", "pact_id", "ticket_id", "action"], "properties": {name: {} for name in (
        "agent_id", "wallet_id", "pact_id", "ticket_id", "action", "amount_usd", "to_address", "chain", "asset", "venue", "function",
        "counterparty_address", "contract_address", "method_selector", "to_asset", "to_chain")}},
}
TRADE_POLL_SECONDS = T.REHEARSAL_INTERVAL_SECONDS
TRADE_DEADLINE_SECONDS = T.REHEARSAL_DEADLINE_SECONDS
WEI_PER_ETHER = 10 ** 18

# ---------------------------------------------------------------------------
# THE LEXICON: the connector's error dictionary, mirrored (AAOI OP2, AT3).
# ---------------------------------------------------------------------------
LEXICON_SOURCE = "packages/shared/src/errors.ts"
LEXICON_PENDING_REASON = (
    "pending: aeredium/aer-connector at 9e20d6c (Spec 59, 24 September 2026) carries no packages/shared/src/errors.ts, "
    "and the connector's dictionary (Spec C-GAS-ERR-100) is not merged; until it is, the harness's copy is read entry by "
    "entry from each owning service's own source, named beside it, and from the day the file exists the mirror test fails "
    "on any drift and never skips"
)
# Set to the connector commit the copy was taken from once errors.ts is merged and mirrored; from then on the mirror test
# fails where it cannot read a clone at all.
LEXICON_MIRRORED_AT: Optional[str] = None

GP1_SOURCE = "api_bis3 cmd/api-gateway/refusal_prefix.go and docs/enclave-envelope-source.md, \"The prefixes a caller may receive\" (Spec GP1, 345be29)"


def _entry(description: str, owner: str, source: str) -> Dict[str, str]:
    return {"description": description, "owner": owner, "source": source}


LEXICON: Dict[str, Dict[str, str]] = {
    "invalid_credential": _entry(
        "the credential presented is not a credential this platform knows: no active credential matched it, so nothing was "
        "judged; the answer is the same on retry",
        "the access platform", "aegiskey-access-platform internal/access/auth_constants.go AuthReasonInvalidCredential; the "
        "sentence is authenticateDenialSentence (internal/access/authorize.go) — the platform's own word, not unknown_credential"),
    "group_not_assigned": _entry(
        "signing group \"<group>\" is not assigned to this account: account <id> is assigned <its groups, or \"no group\">; an operator "
        "assigns the group on the account (assigned_groups), and the answer is the same on retry until then",
        "the access platform", "aegiskey-access-platform internal/access/authorize.go groupNotAssignedSentence, as its README tables it (Spec AAP-AUTHZ-CAUSE)"),
    "legacy_limit_zero": _entry(
        "<policy>'s <limit> limit has not been set to more than zero. Set it to a figure above zero for the payment to be approved.",
        "the gateway", "api_bis3 internal/gateway/layer3.go Layer3CauseLegacyLimitZero and legacyLimitZeroSentence (Spec G5, G14)"),
    "agent_pact_not_composed": _entry(
        "the platform granted credential <credential> but composed no pact document into the policy chain for agent <agent> under pact "
        "<pact> (agent_pact.composed absent or false): a platform below AAP Spec 141 does not read agent_context on authorize, and an "
        "agent's action is never judged against a document that is not the agent's; ship AAP Spec 141 and list this credential in "
        "AAP_AGENT_CONTEXT_CREDENTIAL_IDS",
        "the gateway", "api_bis3 internal/gateway/authorize.go ReasonAgentPactNotComposed and AgentPactNotComposedDetail (Spec G2)"),
    "DUPLICATE_UNACKNOWLEDGED": _entry(
        "This looks like a payment that has already been made recently. Confirm it is intentional to continue.",
        "AER 360", "AERAccounts packages/shared/src/refusals.ts, 422 in apps/server/src/http.ts"),
    "insufficient_gas": _entry(
        "Your gas account holds <available>. This <payment or trade> needs at most <ceiling> of gas. Nothing was sent. Top up US$10.00 or more.",
        "the access platform", "aegiskey-access-platform internal/gas/errors.go OutcomeInsufficientGas and InsufficientGasSentence (U3, Spec 154)"),
    "ROLE_NOT_GRANTED": _entry(
        "Your credential does not carry this permission. Permissions come from your organisation’s policy, not from this "
        "application.",
        "AER 360", "AERAccounts packages/shared/src/refusals.ts, 403 in apps/server/src/http.ts"),
    "NOT_AUTHENTICATED": _entry(
        "You are not signed in. Sign in with your passkey and try again.",
        "AER Connect", "aer-connector packages/shared/src/refusals.ts, 401 in apps/server/src/http.ts"),
    # The GP1 prefixes: every refusal the gateway returns begins with one of them (refusal_prefix.go, refusalPrefixes).
    "PolicyDenied": _entry(
        "A refusal of policy, the same on retry: the gateway's own reason (the engine's word, a digest that does not match, "
        "a gas rule, a key's binding, a group that is not this road's) or, on a cluster reject, the orchestrator's sentence "
        "verbatim.", "the gateway", GP1_SOURCE),
    "PolicyHeld": _entry(
        "The request is held for a second approver and the platform could not record the hold; the hold reason follows.",
        "the gateway", GP1_SOURCE),
    "Held": _entry(
        "The request is held for a second approver; the hold reason, the held request id and the expiry follow.",
        "the gateway", GP1_SOURCE),
    "SigningFailed": _entry(
        "A failure, not a refusal: the orchestrator could not be reached or fell silent, or its reply could not be read.",
        "the gateway", GP1_SOURCE),
    "PolicyEnvelopeRefused": _entry(
        "This gateway withheld the cluster's signature on a check of the returned envelope; the check and the verifier's "
        "words follow.", "the gateway", GP1_SOURCE),
    "PolicyEvaluationFailed": _entry(
        "A fault at Layer 3: the engine could not be asked, the facts could not be built, or the day's amount could not be "
        "read from the platform (Spec VF1).", "the gateway", GP1_SOURCE),
    "PermissionDenied": _entry(
        "Layer 2 refused: the platform's authorization, in its words; or the caller is not the ceremony's.",
        "the gateway", GP1_SOURCE),
    "Unauthenticated": _entry("No credential, a revoked or unknown one, or one of the wrong mode.", "the gateway", GP1_SOURCE),
    "Replayed": _entry("A request identifier seen before within the window.", "the gateway", GP1_SOURCE),
    "RateLimitExceeded": _entry("The credential's rate limit.", "the gateway", GP1_SOURCE),
    "KeyNotHomed": _entry("The key named is homed to another stack.", "the gateway", GP1_SOURCE),
    "KeyTypeRefused": _entry(
        "The key's type is not known to this gateway, or the caller named another than the record's (module GW-R).",
        "the gateway", GP1_SOURCE),
    "PolicyAuthorizationFailed": _entry("The host road's bind of the policy envelope failed.", "the gateway", GP1_SOURCE),
    "PolicyDeniedOnResume": _entry(
        "On the held resume: the re-evaluation, or the cluster, refused the resumed request; on a cluster reject the "
        "orchestrator's sentence follows this word alone.", "the gateway", GP1_SOURCE),
    "HeldConsumeFailed": _entry("On the held resume: the platform did not consume the approval.", "the gateway", GP1_SOURCE),
    "MultisigRequired": _entry(
        "A multisig ceremony was opened and more signatures are needed; the count and the ceremony id follow.",
        "the gateway", GP1_SOURCE),
    "PolicyMisconfigured": _entry("The policy requires several signatures but names no multisig.", "the gateway", GP1_SOURCE),
    "RESOURCE_EXHAUSTED": _entry("On the stream road: the orchestrator pipeline is saturated.", "the gateway", GP1_SOURCE),
}
GP1_PREFIXES: Tuple[str, ...] = (
    "PolicyDenied", "PolicyHeld", "Held", "SigningFailed", "PolicyEnvelopeRefused", "PolicyEvaluationFailed",
    "PermissionDenied", "Unauthenticated", "Replayed", "RateLimitExceeded", "KeyNotHomed", "PolicyDeniedOnResume",
    "HeldConsumeFailed", "KeyTypeRefused", "PolicyAuthorizationFailed", "MultisigRequired", "PolicyMisconfigured",
    "RESOURCE_EXHAUSTED",
)
UNCLASSIFIED = "unclassified"


def lexicon_names_in(sentence: str, code: Optional[str] = None) -> List[str]:
    """
    The lexicon's names a refusal carries, in the order they appear: its code where it is one, a GP1 prefix wherever a
    sentence opens with one ("PolicyDenied: …", also inside a relayed quotation), and a cause word anywhere in it.
    """
    text = sentence or ""
    found: List[Tuple[int, str]] = []
    if code and code in LEXICON:
        found.append((-1, code))
    for name in LEXICON:
        if name in GP1_PREFIXES:
            match = re.search(r"(?<![A-Za-z_])%s: " % re.escape(name), text)
        else:
            match = re.search(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(name), text)
        if match and all(name != seen for _, seen in found):
            found.append((match.start(), name))
    return [name for _, name in sorted(found)]


def named(sentence: str, code: Optional[str] = None) -> str:
    """
    The server's own sentence first, then the dictionary's one-line description of every name it carries; a cause the
    dictionary does not know is the sentence verbatim, marked unclassified. Never a paraphrase.
    """
    names = lexicon_names_in(sentence, code)
    if not names:
        return "%s [%s]" % (sentence, UNCLASSIFIED)
    return "%s [%s]" % (sentence, "; ".join("%s: %s" % (name, LEXICON[name]["description"]) for name in names))


def lexicon_copy() -> Dict[str, str]:
    """The harness's copy as the mirror compares it: each name and its one-line description."""
    return {name: entry["description"] for name, entry in LEXICON.items()}


# ---------------------------------------------------------------------------
# Reading errors.ts when it lands: a TypeScript object literal, read as data.
# ---------------------------------------------------------------------------
DESCRIPTION_KEYS = ("description", "describe", "summary", "sentence", "said", "message", "text")


class _TsReader:
    """
    Just enough of TypeScript to read a dictionary as data: comments skipped; strings (single, double, and backticks, a
    template with an interpolation being no sentence) joined across `+`; object literals with bare or quoted keys, also
    inside Object.freeze( … ); every other value — a number, a list, a call, a name — walked over and left alone.
    """

    QUOTES = ("'", '"', "`")
    ESCAPES = {"n": "\n", "t": "\t", "'": "'", '"': '"', "`": "`", "\\": "\\"}

    def __init__(self, text: str):
        self.text = _strip_ts_comments(text)
        self.i = 0

    def ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1

    def peek(self) -> str:
        self.ws()
        return self.text[self.i] if self.i < len(self.text) else ""

    def skip_string(self) -> Optional[str]:
        """Over one string literal, from its opening quote: its value, or None for a template that interpolates."""
        quote = self.text[self.i]
        self.i += 1
        out: List[str] = []
        interpolated = False
        while self.i < len(self.text):
            ch = self.text[self.i]
            if ch == "\\" and self.i + 1 < len(self.text):
                out.append(self.ESCAPES.get(self.text[self.i + 1], self.text[self.i + 1]))
                self.i += 2
                continue
            if quote == "`" and ch == "$" and self.text[self.i + 1:self.i + 2] == "{":
                interpolated = True
                self.i += 2
                depth = 1
                while self.i < len(self.text) and depth:
                    inner = self.text[self.i]
                    if inner in self.QUOTES:
                        self.skip_string()
                        continue
                    depth += 1 if inner == "{" else -1 if inner == "}" else 0
                    self.i += 1
                continue
            self.i += 1
            if ch == quote:
                return None if interpolated else "".join(out)
            out.append(ch)
        return None

    def joined(self) -> Tuple[bool, Optional[str]]:
        """A string, or strings joined by +: (whether one stood here, its value — None where any part interpolates)."""
        if self.peek() not in self.QUOTES:
            return False, None
        parts: List[Optional[str]] = [self.skip_string()]
        while True:
            save = self.i
            if self.peek() != "+":
                break
            self.i += 1
            if self.peek() not in self.QUOTES:
                self.i = save
                break
            parts.append(self.skip_string())
        return True, (None if any(p is None for p in parts) else "".join(p for p in parts if p is not None))

    def key(self) -> Optional[str]:
        if self.peek() in self.QUOTES:
            return self.skip_string()
        match = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*").match(self.text, self.i)
        if not match:
            return None
        self.i = match.end()
        return match.group(0)

    def value(self) -> Any:
        ch = self.peek()
        if ch in self.QUOTES:
            return self.joined()[1]
        if ch == "{":
            return self.object()
        if self.text.startswith("Object.freeze(", self.i):
            self.i += len("Object.freeze(")
            inner = self.value()
            self.close(")")
            return inner
        self.skip_value()
        return None

    def close(self, bracket: str) -> None:
        """On to just past the bracket that closes the one already open, strings and nested brackets walked over."""
        depth = 1
        while self.i < len(self.text) and depth:
            ch = self.text[self.i]
            if ch in self.QUOTES:
                self.skip_string()
                continue
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            self.i += 1

    def object(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        self.ws()
        self.i += 1  # {
        while self.i < len(self.text):
            ch = self.peek()
            if ch == "}":
                self.i += 1
                return out
            if ch == "," or ch == ";":
                self.i += 1
                continue
            before = self.i
            if self.text.startswith("...", self.i):
                self.i += 3
                self.skip_value()
                continue
            name = self.key()
            if name is None or self.peek() != ":":
                self.skip_value()  # a shorthand property, a method, anything that is not `key: value`
                if self.i == before:
                    self.i += 1
                continue
            self.i += 1  # :
            out[name] = self.value()
        return out

    def skip_value(self) -> None:
        """Over one value that is neither a string nor an object: to the comma, semicolon or bracket that ends it."""
        depth = 0
        while self.i < len(self.text):
            ch = self.text[self.i]
            if ch in self.QUOTES:
                self.skip_string()
                continue
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                if depth == 0:
                    return
                depth -= 1
            elif ch in ",;" and depth == 0:
                return
            self.i += 1


def _strip_ts_comments(text: str) -> str:
    out: List[str] = []
    i = 0
    quote: Optional[str] = None
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i):
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end < 0 else end + 2
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def lexicon_of_typescript(text: str) -> Dict[str, str]:
    """
    Every name a TypeScript dictionary defines and its one-line description: from each `export const X = …{…}` object
    literal, a key whose value is a sentence, or an object carrying one under `description` (or summary, sentence, said,
    message, text). Values that are neither — a status number, a list — are not entries.
    """
    reader = _TsReader(text)
    out: Dict[str, str] = {}
    for match in re.finditer(r"export\s+const\s+[A-Za-z_$][A-Za-z0-9_$]*\s*(?::[^=]+)?=", reader.text):
        reader.i = match.end()
        found = reader.value()
        if not isinstance(found, dict):
            continue
        for name, value in found.items():
            if isinstance(value, str):
                out[name] = value
            elif isinstance(value, dict):
                for key in DESCRIPTION_KEYS:
                    if isinstance(value.get(key), str):
                        out[name] = value[key]
                        break
    return out


def lexicon_drift(theirs: Dict[str, str], ours: Optional[Dict[str, str]] = None) -> List[str]:
    """Every difference between the connector's dictionary and the harness's copy, one line each; empty where they agree."""
    ours = lexicon_copy() if ours is None else ours
    lines: List[str] = []
    for name in ours:
        if name not in theirs:
            lines.append("%s is in the harness's copy and not in %s" % (name, LEXICON_SOURCE))
        elif theirs[name] != ours[name]:
            lines.append("%s reads %r in %s and %r in the harness's copy" % (name, theirs[name], LEXICON_SOURCE, ours[name]))
    for name in theirs:
        if name not in ours:
            lines.append("%s is in %s and not in the harness's copy" % (name, LEXICON_SOURCE))
    return lines


# ---------------------------------------------------------------------------
# Small readers.
# ---------------------------------------------------------------------------
UUID_FORM = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
GROUP_KEYS = ("assignedGroups", "assigned_groups", "signingGroup", "signing_group", "signingGroups", "group")


def normal_base(base: str) -> str:
    """A base URL as the guard compares it: scheme and host lower-cased, no path, no trailing slash."""
    parsed = urllib.parse.urlparse(base.strip())
    netloc = (parsed.netloc or parsed.path).lower()
    return "%s://%s" % ((parsed.scheme or "https").lower(), netloc.rstrip("/"))


def is_test_ring(base: str, rings: Sequence[str]) -> bool:
    return normal_base(base) in {normal_base(ring) for ring in rings}


def guard_sentence(base: str, station: str) -> str:
    return GUARD_SENTENCE % (normal_base(base), GUARDED[station])


def groups_in(view: Any) -> List[str]:
    """Every signing group an answer states, under any of the names a group goes by; empty where it states none."""
    found: List[str] = []
    for key in GROUP_KEYS:
        value = H.find_key(view, [key])
        if isinstance(value, str) and value.strip():
            found.append(value.strip())
        elif isinstance(value, list):
            found.extend(str(v).strip() for v in value if isinstance(v, str) and v.strip())
    return list(dict.fromkeys(found))


def cents_of(value: Any) -> Optional[int]:
    """Cents from the Wallet's dollars ("0.03", "US$0.03"), or None."""
    return H.usd_cents(value)


def gas_and_service_cents(wei: int, cents_per_ether_x1e6: int, bps: int = MARGIN_BPS) -> Tuple[int, int]:
    """
    The platform's own arithmetic (internal/gas/dollars.go GasAndServiceCents): gas is the cost in cents, rounded half up;
    service is the unrounded gas figure × bps/10000, rounded half up, and at least one cent when gas is above zero. The
    price is carried in millionths of a cent per ether so a band's edge loses nothing to rounding.
    """
    # gas cents = wei × price / 1e18, the price being cents_per_ether_x1e6 / 1e6
    numerator = wei * cents_per_ether_x1e6
    denominator = WEI_PER_ETHER * 10 ** 6
    gas = (2 * numerator + denominator) // (2 * denominator)
    service_num = numerator * bps
    service_den = denominator * 10000
    service = (2 * service_num + service_den) // (2 * service_den)
    if service < 1 and numerator > 0:
        service = 1
    return gas, service


def debit_band(wei: int, price_x1e6: int, bps: int = MARGIN_BPS, band_bps: int = PRICE_BAND_BPS) -> Tuple[int, int]:
    """The least and the most the platform could debit for this cost: gas plus service at the price ± the band, in cents."""
    low_price = price_x1e6 * (10000 - band_bps) // 10000
    high_price = -(-price_x1e6 * (10000 + band_bps) // 10000)
    low = sum(gas_and_service_cents(wei, low_price, bps))
    high = sum(gas_and_service_cents(wei, high_price, bps))
    return low, high


def word_at(data: bytes, index: int) -> int:
    return int.from_bytes(data[32 * index:32 * (index + 1)], "big")


def user_operation_events(receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every UserOperationEvent a receipt logged: the userOpHash, the sender, the paymaster, success and the actual cost."""
    out: List[Dict[str, Any]] = []
    for log in receipt.get("logs") or []:
        topics = [str(t) for t in (log.get("topics") or [])]
        if len(topics) == 4 and topics[0].lower() == USER_OPERATION_EVENT:
            raw = bytes.fromhex(str(log.get("data") or "0x")[2:] or "")
            out.append({
                "entry_point": H.checksum_address(str(log.get("address") or "0x" + "0" * 40)),
                "user_op_hash": topics[1].lower(),
                "sender": H.checksum_address("0x" + topics[2][-40:]),
                "paymaster": H.checksum_address("0x" + topics[3][-40:]),
                "nonce": word_at(raw, 0) if len(raw) >= 32 else None,
                "success": bool(word_at(raw, 1)) if len(raw) >= 64 else None,
                "actual_gas_cost": word_at(raw, 2) if len(raw) >= 96 else None,
                "actual_gas_used": word_at(raw, 3) if len(raw) >= 128 else None,
            })
    return out


def balance_row(data: Any, chain: str, asset: str) -> Optional[Dict[str, Any]]:
    """The asset's row on the chain, where the Wallet puts it: get_balances' tokens.balances (Spec 49, Spec T3 §2)."""
    return H.usdc_row_in(data, chain, asset)


def raw_of(row: Optional[Dict[str, Any]]) -> Optional[int]:
    if not isinstance(row, dict):
        return None
    try:
        return int(str(row.get("raw")).strip())
    except (TypeError, ValueError):
        return None


def contract_of(row: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(row, dict):
        return None
    for key in ("contract", "contract_address", "address", "token"):
        value = row.get(key)
        if isinstance(value, str) and H.HEX40.fullmatch(value.strip()):
            return value.strip()
    return None


def short_json(value: Any, limit: int = 600) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit] + "…"


SETTING_NAME = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")


def kind_of(status: int, parsed: Any) -> str:
    """
    The law's classes (Refusals tell the truth, 4 September 2026), for a non-2xx answer: REFUSED — 401, 402, 403, 404, 409,
    429, or a 502 carrying the connector's relayed refusal (a door or the platform said no); MALFORMED — 400 or 422, the
    harness's own question; MISCONFIGURED — a refusal whose provenance names the deployment setting that mends it (the
    connector's AAP_GAS_DOOR_KEY); UNREACHABLE — every other 5xx, the other party unable to answer; and ANSWERED WITH AN
    ERROR for whatever else came back.
    """
    refusal = C.refusal_of(parsed) or {}
    provenance = refusal.get("provenance") if isinstance(refusal.get("provenance"), dict) else {}
    if SETTING_NAME.match(str(provenance.get("reference") or "")):
        return "misconfigured"
    if status in (401, 402, 403, 404, 409, 429) or (status == 502 and refusal):
        return "refused"
    if status in (400, 422):
        return "malformed"
    if 500 <= status < 600:
        return "unreachable"
    return "answered with an error"


class ChainRefused(H.HarnessError):
    """The chain's JSON-RPC endpoint answered the harness's question with an error of its own: its words travel, and it is no fault of the harness."""


# corridor_consent's unreachable sentence ends so, which is true of a read; of a press it is told as what is known (press_unreachable).
WIRE_UNREACHABLE_TAIL = "; nothing was changed, and a retry may reach it"
PRESS_UNREACHABLE_TAIL = "; its answer never arrived, so whether the connector carried it out is not known"
_SENT_METHOD = re.compile(r"\b(GET|HEAD|POST|PUT|PATCH|DELETE) (?:https?://|/)")


def press_unreachable(sentence: str, route: Optional[str] = None) -> str:
    """
    The transport cannot tell a request that never left from an answer lost on its way back (a timeout), so "nothing was
    changed" is the harness's to say of a read only. Of a press — any method but GET — it says what it knows: the answer never
    arrived, and whether the connector carried the press out is not known. The method is the route's, else the one the
    transport's own error names.
    """
    if not sentence.endswith(WIRE_UNREACHABLE_TAIL):
        return sentence
    found = _SENT_METHOD.search(route or "") or _SENT_METHOD.search(sentence)
    if found is None or found.group(1) in ("GET", "HEAD"):
        return sentence
    return sentence[: -len(WIRE_UNREACHABLE_TAIL)] + PRESS_UNREACHABLE_TAIL


def landed_word(operation: Dict[str, Any]) -> bool:
    """Whether the Wallet's own word says the operation landed: the status landed, or the debit it states once it has."""
    return str(operation.get("status") or "") == "landed" or bool(operation.get("debited_usd"))


def chain_family(chain: str) -> str:
    """The family a chain's commission rides in: an SPL transfer on Solana, an ERC-20 Transfer log on every EVM chain."""
    return "solana" if str(chain).strip().lower().startswith("solana") else "evm"


def bought_token_of(transfers: Sequence[Dict[str, Any]], wallet: str, sold_token: Optional[str] = None) -> Optional[str]:
    """The token the trade bought: the one that arrived at the wallet, other than the coin it sold."""
    for transfer in transfers:
        if transfer["to"].lower() == wallet.lower() and (not sold_token or transfer["token"].lower() != sold_token.lower()):
            return transfer["token"]
    return None


def judge_commission(transfers: Sequence[Dict[str, Any]], wallet: str, router: Optional[str], fee_address: str
                     ) -> Dict[str, Any]:
    """
    The commission, judged by corridor_harness.fee_check at tables.py's rate: the router pays fee = gross × FEE_BPS / 10000,
    rounded down, to the fee address and the rest to the wallet, the gross read from the pool's transfer to the router where
    the router is known. Adds what fee_check leaves to its reason, so a failure names the figure found and the figure expected:
    the gross and the expected fee where no leg reached the fee address, and the address a leg went to instead.
    """
    check = dict(H.fee_check(transfers, fee_address, wallet, bps=T.FEE_BPS, router=router))
    token = check.get("token") or bought_token_of(transfers, wallet)
    check["token"] = token
    if token and check.get("expected") is None:
        to_router = [t["amount"] for t in transfers if router and t["token"].lower() == token.lower() and t["to"].lower() == router.lower()]
        delivered = sum(t["amount"] for t in transfers if t["token"].lower() == token.lower() and t["to"].lower() == wallet.lower())
        gross = sum(to_router) if to_router else None
        elsewhere = [t for t in transfers if t["token"].lower() == token.lower() and router and t["from"].lower() == router.lower()
                     and t["to"].lower() not in (wallet.lower(), fee_address.lower())]
        if gross is None:
            gross = delivered + sum(t["amount"] for t in elsewhere)
        check.update(gross=gross, delivered=delivered, expected=gross * T.FEE_BPS // 10000, found=0, legs_to_fee_address=0,
                     elsewhere=[{"to": t["to"], "amount": t["amount"]} for t in elsewhere])
    return check


def spl_transfers_in(transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    A Solana transaction's SPL token movements, in the shape fee_check reads: for every owner whose balance of a mint rose, a
    transfer of the rise to that owner. A transfer on Solana moves between token accounts, and the transaction's own meta —
    getTransaction's preTokenBalances and postTokenBalances — names the wallet that owns each, so the fee wallet is read as an
    owner and never as a token account the harness would have to derive.
    """
    meta = transaction.get("meta") if isinstance(transaction.get("meta"), dict) else {}

    def balances(key: str) -> Dict[Tuple[str, str], int]:
        out: Dict[Tuple[str, str], int] = {}
        for row in meta.get(key) or []:
            if not isinstance(row, dict):
                continue
            owner, mint = str(row.get("owner") or ""), str(row.get("mint") or "")
            amount = int(str((row.get("uiTokenAmount") or {}).get("amount") or "0"))
            out[(owner, mint)] = out.get((owner, mint), 0) + amount
        return out

    before, after = balances("preTokenBalances"), balances("postTokenBalances")
    moves = []
    for (owner, mint), held in after.items():
        rise = held - before.get((owner, mint), 0)
        if owner and mint and rise > 0:
            moves.append({"token": mint, "from": "", "to": owner, "amount": rise, "log_index": None})
    return moves


class StationStop(Exception):
    """A station stops here, with its own sentence and its own outcome word; the run goes on to what does not need it."""

    def __init__(self, sentence: str, outcome: str = STOPPED):
        super().__init__(sentence)
        self.sentence = sentence
        self.outcome = outcome


class Outcome:
    def __init__(self, station: str, outcome: str, line: str):
        self.station = station
        self.outcome = outcome
        self.line = line


# ---------------------------------------------------------------------------
# The MCP session and the chain reader, recorded to the last four characters.
# ---------------------------------------------------------------------------
class OwnerMcp(H.Mcp):
    """
    corridor_harness.Mcp as it is — initialize, tools/list, the schema readers, the guard against a road that is not an
    AER Connect agent's — with `rpc` restated for the one thing the law asks of this harness and the corridor's session
    does not do: its record redacts every secret to its last four characters, and a door that cannot be reached is
    recorded in the transport's own words before the fault travels on.
    """

    def __init__(self, oauth: H.Oauth, label: str, record: Callable[..., None], mcp_url: str, secrets_: List[str]):
        super().__init__(oauth, label, record, mcp_url)
        self.secrets = secrets_

    def bearer(self) -> str:
        """
        The stored per-connection credential, refreshed where it is spent; a refresh the connector refuses is told as a refusal.
        A credential is sent only to the connector that issued it, and a credential never stored is said as that.
        """
        record = self.oauth.tokens(self.label)
        if not record:
            raise StationStop("the harness holds no stored credential for %s at %s: S7 has not connected this run's agent"
                              % (self.label, self.oauth.token_path(self.label)), outcome=NOT_RUN)
        if record.get("issuer") and normal_base(str(record["issuer"])) != normal_base(self.oauth.issuer):
            raise StationStop("the credential stored for %s was issued by %s, and this run's base is %s: a credential is never sent to "
                              "another connector" % (self.label, normal_base(str(record["issuer"])), normal_base(self.oauth.issuer)))
        try:
            return super().bearer()
        except H.Unreachable:
            raise
        except H.HarnessError as err:
            raise refresh_stop(err)

    def note(self, values: Sequence[str]) -> None:
        for value in values:
            if isinstance(value, str) and len(value) >= 8 and value not in self.secrets:
                self.secrets.append(value)
            if isinstance(value, str) and value not in self.secrets_seen:
                self.secrets_seen.append(value)

    def rpc(self, method: str, params: Optional[Dict[str, Any]], test_id: str, notification: bool = False,
            allow_refresh: bool = True) -> H.McpAnswer:
        bearer = self.bearer()
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notification:
            payload["id"] = self._next_id
            self._next_id += 1
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "Authorization": "Bearer " + bearer, "MCP-Protocol-Version": H.PROTOCOL_VERSION}
        self.note([bearer] + H.secret_values(params or {}))
        tool = (params or {}).get("name", method) if method == "tools/call" else method
        sent = H.redact(params or {}, self.secrets, mask=C.last4)
        try:
            http_answer = H.http_request("POST", self.mcp_url, headers, json.dumps(payload).encode("utf-8"))
        except H.Unreachable as err:
            self.record(test_id=test_id, kind=method, tool=tool, arguments=sent, answer=str(err), http_status=0,
                        round_trip_ms=0, agent=self.label, outcome="unreachable")
            raise
        parsed = H.parse_rpc_body(http_answer.text)
        answer = H.McpAnswer(http_answer.status, parsed, http_answer.text, http_answer.elapsed_ms)
        self.note(H.secret_values(parsed))
        self.record(test_id=test_id, kind=method, tool=tool, arguments=sent, answer=H.redact(parsed, self.secrets, mask=C.last4),
                    http_status=http_answer.status, round_trip_ms=http_answer.elapsed_ms, agent=self.label)
        if http_answer.status == 401 and allow_refresh:
            try:
                self.oauth.refresh(self.label)  # the door said the bearer is spent; the corridor's own road, once
            except H.Unreachable:
                raise
            except H.HarnessError as err:
                raise refresh_stop(err)
            return self.rpc(method, params, test_id, notification, allow_refresh=False)
        return answer

    def listed(self, test_id: str) -> List[Dict[str, Any]]:
        """tools/list, and where it answers no list, the answer quoted and named rather than a fault of the harness's."""
        try:
            return self.tools_list(test_id)
        except H.Unreachable:
            raise
        except H.HarnessError as err:
            raise StationStop("tools/list answered no list — %s" % named(str(err).replace("tools/list did not answer with a tool list: ", "")), outcome=FAIL)


def refresh_stop(err: Exception) -> "StationStop":
    """
    The Oauth road's refresh, classified (the Refusals law): the token endpoint answering invalid_grant has refused the grant —
    the connection was revoked or the token already rotated — and says so again on retry; another 4xx is the harness's question
    malformed; anything else a fault. The endpoint's own words travel.
    """
    words = str(err)
    if "is stored for" in words:  # the Oauth road's own: nothing was asked of the token endpoint
        return StationStop("the harness holds no refresh token to renew the per-connection credential with (%s); nothing was asked of "
                           "the token endpoint" % words, outcome=STOPPED)
    found = C.ANSWERED_STATUS.search(words)
    status = int(found.group(1)) if found else 0
    if "invalid_grant" in words or status in (401, 403):
        return StationStop("refused: the connector's token endpoint refused to refresh the per-connection credential — %s; the answer will "
                           "be the same on retry" % named(words), outcome=FAIL)
    if 400 <= status < 500:
        return StationStop("malformed: the connector's token endpoint could not read the harness's refresh — %s; the harness's question is "
                           "wrong, not the connector" % named(words), outcome=FAIL)
    return StationStop("fault: the connector's token endpoint answered the refresh with %s; nothing was judged" % named(words), outcome=FAIL)


class RecordedChain(H.ChainRpc):
    """
    corridor_harness.ChainRpc, every JSON-RPC call recorded: the reader reads only, and says what it read. The route names
    the endpoint by its scheme and host alone, and a path or query long enough to carry a provider's key is a secret,
    redacted to its last four characters wherever a sentence would print it.
    """

    def __init__(self, name: str, url: str, record: Callable[..., None], secrets_: Optional[List[str]] = None):
        super().__init__(name, url)
        self.record_line = record
        parsed = urllib.parse.urlparse(url)
        self.host = "%s://%s" % (parsed.scheme, parsed.netloc)
        keyed = (parsed.path + (("?" + parsed.query) if parsed.query else "")).strip()
        if secrets_ is not None and len(keyed) >= 8 and keyed not in secrets_:
            secrets_.append(keyed)

    def call(self, method: str, params: Sequence[Any]) -> Any:
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": list(params)}
        self._id += 1
        route = "%s %s" % (method, self.host)
        try:
            answer = H.http_request("POST", self.url, {"Content-Type": "application/json"}, json.dumps(body).encode("utf-8"), timeout=60)
        except H.Unreachable as err:
            self.record_line(tool=route, arguments=body, answer=str(err), http_status=0, round_trip_ms=0, outcome="unreachable")
            raise
        parsed = H.json_in(answer.text)
        self.record_line(tool=route, arguments=body, answer=parsed if parsed is not None else answer.text,
                         http_status=answer.status, round_trip_ms=answer.elapsed_ms)
        if not isinstance(parsed, dict):
            raise H.Unreachable("%s answered %d without JSON: %s" % (self.url, answer.status, answer.text[:200]))
        if parsed.get("error"):
            raise ChainRefused("the %s RPC at %s refused %s: %s" % (self.name, self.host, method, json.dumps(parsed["error"], ensure_ascii=False)))
        return parsed.get("result")


# ---------------------------------------------------------------------------
# The owner's answers to the questionnaire (S3, S4).
# ---------------------------------------------------------------------------
def answers_from(questionnaire: Dict[str, Any], offered: Sequence[str], role_id: str = ROLE_ID) -> Dict[str, Any]:
    """
    The answers `POST /v1/account/agents` and `POST /v1/account/agents/:id/policy` carry (routes/consent.ts answersBody):
    the questionnaire the server returned, as it returned it, where it gave a starting answer — the hold, the count of
    transactions a day, the assets — and the owner's own figures where the form opens empty and the owner must write one:
    the two budgets (Spec 41: "we do not have an opinion on the figure"; the harness writes the corridor's book, per trade
    20 and per day 100). The chains are the questionnaire's, with the trade's chain first, because the first chain ticked
    is where the wallet is minted. The list is the Trader's (T.TRADER_LIST_B3, the eight venue contracts B3 names, under
    the scope `agent`), so the agent may trade from its first pact.
    """
    # LIVE-TODO: the shape is answersBody's; whether the platform accepts this filing is a live fact — the questionnaire's
    # starting answers are Police's describe_role template read live, the platform validates every address of the list
    # against every chain the agent is scoped to (requireAgentWhitelistPayableDestinations), and the hold must stay above
    # the trade's ten cents or S10 is held. Confirm against the production connector's questionnaire for trader.v1.
    count = questionnaire.get("maxTxPerDay")
    if count in (None, ""):
        raise StationStop(C.NO_COUNT_SENTENCE % role_id)
    hold = questionnaire.get("holdAboveUsd")
    if hold in (None, ""):
        hold = C.BOOK_PER_TX_USD  # QUESTIONNAIRE_SAID.hold: "write the per-trade figure to never be asked"
    ticked = [str(c) for c in (questionnaire.get("chains") or []) if str(c) in offered]
    if TRADE["chain"] not in offered:
        raise StationStop("the connector offers no %s for %s (the chains on offer are %s), and the trade is made there, where "
                          "the group-100 paymaster lives" % (TRADE["chain"], role_id, ", ".join(offered) or "none"))
    chains = [TRADE["chain"]] + [c for c in ticked if c != TRADE["chain"]]
    answers: Dict[str, Any] = {
        "perTxUsd": C.BOOK_PER_TX_USD,
        "dailyUsd": C.BOOK_DAILY_USD,
        "holdAboveUsd": str(hold),
        "maxTxPerDay": str(count),
        "chains": chains,
        "counterpartiesScope": C.TRADER_LIST_SCOPE,
        "counterparties": [T.address(key) for key in T.TRADER_LIST_B3],
    }
    assets = questionnaire.get("assets")
    if isinstance(assets, list):  # absent means the question was not asked (routes/consent.ts), and then nothing is sent
        answers["assets"] = [str(a) for a in assets]
    return answers


def document_disagreements(document: Any, answers: Dict[str, Any]) -> List[str]:
    """
    Where the pact document the connector filed (services/ceremony.ts agentPolicyDocument: scope.chains with the home chain
    first, scope.assets_allowed, scope.counterparties_whitelist_scope and counterparties_allowed, budgets in dollars,
    velocity.max_tx_per_day, approvals.human_approval_threshold_usd) does not say what the owner sent; empty where it does.
    """
    if not isinstance(document, dict):
        return ["the pact carries no document (%s)" % short_json(document, 200)]
    scope = document.get("scope") if isinstance(document.get("scope"), dict) else {}
    budgets = document.get("budgets") if isinstance(document.get("budgets"), dict) else {}
    velocity = document.get("velocity") if isinstance(document.get("velocity"), dict) else {}
    approvals = document.get("approvals") if isinstance(document.get("approvals"), dict) else {}
    wanted: List[Tuple[str, Any, Any]] = [
        ("scope.chains", scope.get("chains"), list(answers["chains"])),
        ("scope.counterparties_whitelist_scope", scope.get("counterparties_whitelist_scope"), str(answers["counterpartiesScope"]).strip().lower()),
        ("budgets.per_tx_cap_usd", budgets.get("per_tx_cap_usd"), float(answers["perTxUsd"])),
        ("budgets.daily_cap_usd", budgets.get("daily_cap_usd"), float(answers["dailyUsd"])),
        ("velocity.max_tx_per_day", velocity.get("max_tx_per_day"), int(answers["maxTxPerDay"])),
        ("approvals.human_approval_threshold_usd", approvals.get("human_approval_threshold_usd"), float(answers["holdAboveUsd"])),
    ]
    if "assets" in answers:
        wanted.append(("scope.assets_allowed", scope.get("assets_allowed"), list(dict.fromkeys(a.strip().upper() for a in answers["assets"] if a.strip()))))
    out: List[str] = []
    for key, got, want in wanted:
        same = got == want
        if isinstance(want, float):
            same = isinstance(got, (int, float)) and not isinstance(got, bool) and abs(float(got) - want) < 0.005
        if not same:
            out.append("the document's %s is %s, and %s was sent" % (key, json.dumps(got), json.dumps(want)))
    filed = scope.get("counterparties_allowed")
    sent = [str(a).strip() for a in answers["counterparties"]]
    if not isinstance(filed, list) or [str(a).lower() for a in filed] != [a.lower() for a in sent]:
        out.append("the document's scope.counterparties_allowed is %s, and the %d contracts of the Trader's list were sent" % (json.dumps(filed), len(sent)))
    return out


# ---------------------------------------------------------------------------
# The run.
# ---------------------------------------------------------------------------
class Pathfinder:
    """
    One run, S1 to S13. Every collaborator can be handed in for the tests: `say` for the terminal, `sleep` and `clock` for
    the polls, `openssl` for the passkey, `started_at` for the run id, `rpc_url` for the chain. The wire is
    corridor_harness.http_request, read at call time, so a test that patches that one function answers every road.
    """

    def __init__(self, base: str = DEFAULT_BASE, owner: str = DEFAULT_OWNER, store_dir: str = STORE_DIR,
                 out_dir: str = RUNS_DIR, start_at: Optional[str] = None, i_mean_it: bool = False,
                 test_rings: Sequence[str] = (), funding_wallet: Optional[str] = None, rpc_url: Optional[str] = None,
                 say: Callable[[str], None] = print, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, openssl: str = C.PK.OPENSSL,
                 started_at: Optional[_dt.datetime] = None, interval: float = TRADE_POLL_SECONDS,
                 deadline: float = TRADE_DEADLINE_SECONDS, dry: bool = False, estate_base: str = ESTATE_BASE,
                 estate_store: str = ESTATE_STORE_DIR, estate_transport: Optional[E.Transport] = None, estate_admin_env: Optional[str] = None):
        self.base = base.rstrip("/")
        self.owner = owner
        self.store_dir = os.path.expanduser(store_dir)
        self.folder_dir = os.path.join(self.store_dir, owner)
        self.start_at = start_at
        self.i_mean_it = i_mean_it
        self.rings = tuple(TEST_RINGS) + tuple(test_rings)
        # Spec T23: the estate the owner's money is in, read from where the estate harness keeps it — its base, its store (the people's passkeys
        # under harness-holdings/ and harness-treasury/), the admin credential in admin.env, and the funding wallet file beside them
        self.estate_base = estate_base.rstrip("/")
        self.estate_store = os.path.expanduser(estate_store)
        self.estate_transport: E.Transport = estate_transport or E.urllib_transport
        self.estate_admin_env = estate_admin_env or os.path.join(self.estate_store, ET.ADMIN_ENV_FILE)
        self.funding_wallet = funding_wallet or os.path.join(self.estate_store, C.HARNESS_HOLDINGS, C.FUNDING_WALLET_FILE)
        self.estate: Optional[E.Runner] = None
        self.rpc_url = rpc_url or T.REHEARSAL_RPC[TRADE["chain"]].url
        self._say = say
        self.sleep = sleep
        self.clock = clock
        self.interval = float(interval)
        self.deadline = float(deadline)
        self.started_at = started_at or _dt.datetime.now(_dt.timezone.utc)
        self.run_id = self.started_at.strftime(RUN_ID_FORMAT)
        self.label = AGENT_NAME % (owner, self.run_id)
        self.secrets: List[str] = []
        self.steps: Dict[str, List[Dict[str, Any]]] = {}
        self.notes: Dict[str, List[str]] = {}
        self.outcomes: List[Outcome] = []
        self.current = "S1"
        self.expectations: Dict[str, str] = {}
        self.expect_default = ""
        self.facts: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}
        self.signed_in = False
        self.mcp: Optional[OwnerMcp] = None
        self.removed: List[str] = []
        self.folder = H.RunFolder(os.path.expanduser(out_dir), "pathfinder-%s" % owner, dry=dry)
        # The owner: born once, under the corridor harness's convention; a name outside [a-z0-9-]+ is refused here.
        self.customer = C.HarnessCustomer(owner, self.base, self.store_dir, self.record, self.say, secrets_=self.secrets,
                                          openssl=openssl, clock=clock)
        self.oauth = H.Oauth(self.base, self.folder_dir, say=self.say)
        self.chain = RecordedChain(TRADE["chain"], self.rpc_url, self.record, self.secrets)

    # -- the terminal and the record ---------------------------------------------------------------------
    def say(self, text: str) -> None:
        self._say(H.redact(text, self.secrets, mask=C.last4))

    def note(self, text: str) -> None:
        self.notes.setdefault(self.current, []).append(text)
        self.say("  %s note: %s" % (self.current, text))

    def expect(self, default: str, **by_route: str) -> None:
        """What the next calls are expected to answer: by route where the station knows each, else the default."""
        self.expect_default = default
        self.expectations = dict(by_route)

    def expected_for(self, route: str) -> str:
        """The expectation for a route: its own where the station named it (a key ending in / names every road under it), else the default."""
        for key, sentence in self.expectations.items():
            if route == key or (key.endswith("/") and route.startswith(key)):
                return sentence
        return self.expect_default

    @staticmethod
    def result_word(status: Any, answer: Any, outcome: Optional[str]) -> str:
        if outcome:
            return outcome
        if not isinstance(status, int) or status == 0:
            return "unreachable"
        if isinstance(answer, dict) and (isinstance(answer.get("error"), dict) or
                                         (isinstance(answer.get("result"), dict) and answer["result"].get("isError") is True)):
            return "answered with an error" if status < 400 else "refused"
        if 200 <= status < 300:
            return "answered"
        if 300 <= status < 400:
            return "redirected"
        return kind_of(status, answer)

    def record(self, **line: Any) -> None:
        """
        Every exchange on every road — the owner's wire, the consent, the MCP session, the chain — under the station that
        made it: the route, what was sent, what came back, the expectation and the result, every secret to its last four
        characters (the wire and the session redact before they hand a line over; this redacts once more, by value).
        """
        tool = str(line.get("tool") or line.get("kind") or "")
        kind = line.get("kind")
        if kind == "tools/call":
            route = "MCP tools/call %s" % tool
        elif kind and kind != "consent":
            route = "MCP %s" % kind  # initialize, notifications/initialized, tools/list
        else:
            route = tool  # the wire's "POST /v1/…", the chain's "eth_call <url>"
        status = line.get("http_status")
        entry = {
            "at": H.now_iso(),
            "station": self.current,
            "route": route,
            "who": line.get("agent") or "",
            "sent": H.redact(line.get("arguments"), self.secrets, mask=C.last4),
            "status": status,
            "came_back": H.redact(line.get("answer"), self.secrets, mask=C.last4),
            "headers": H.redact(line.get("answer_headers"), self.secrets, mask=C.last4) if line.get("answer_headers") else None,
            "elapsed_ms": line.get("round_trip_ms"),
            "expected": self.expected_for(route),
            "result": self.result_word(status, line.get("answer"), line.get("outcome")),
        }
        self.steps.setdefault(self.current, []).append(entry)
        self.folder.record(**entry)

    # -- the owner's wire -----------------------------------------------------------------------------------
    def call(self, method: str, path: str, body: Any = None, lost: str = "") -> Tuple[H.HttpAnswer, Any]:
        """
        One call as the account page makes it, on the owner's own session; a connector that cannot be reached fails the station
        in the wire's words, and a press whose answer never arrived is told as not known to have been carried out, with `lost`,
        what the run does about it, after.
        """
        try:
            return self.customer.wire.call(method, path, body)
        except C.ConsentStop as stop:
            sentence = press_unreachable(stop.sentence, stop.route) if stop.outcome == "unreachable" else stop.sentence
            if lost and sentence.endswith(PRESS_UNREACHABLE_TAIL):
                sentence = "%s; %s" % (sentence, lost)
            raise StationStop("%s; nothing was judged" % sentence, outcome=FAIL)

    def refused(self, what: str, route: str, answer: H.HttpAnswer, parsed: Any) -> StationStop:
        """Every catch classifies (kind_of), and each class says what happened in the connector's own words, then the lexicon's."""
        said = C.connector_said(answer, parsed, self.secrets)
        refusal = C.refusal_of(parsed) or {}
        words = named(said, refusal.get("code"))
        kind = kind_of(answer.status, parsed)
        if kind == "refused":
            sentence = "refused: the connector refused %s at %s — %s; the answer will be the same on retry" % (what, route, words)
        elif kind == "malformed":
            sentence = ("malformed: the connector could not read the harness's %s at %s — %s; the harness's question is wrong, not the "
                        "connector" % (what, route, words))
        elif kind == "misconfigured":
            sentence = ("misconfigured: the connector's deployment lacks %s, so it could not answer %s at %s — %s; the setting is the "
                        "operator's to make, and nothing was changed" % ((refusal.get("provenance") or {}).get("reference"), what, route, words))
        elif kind == "unreachable":
            sentence = ("unreachable: the connector could not answer %s at %s (HTTP %d) — %s; nothing was judged, and a retry may reach it"
                        % (what, route, answer.status, words))
        else:
            sentence = "answered with an error: the connector answered %s at %s with HTTP %d — %s" % (what, route, answer.status, words)
        return StationStop(sentence, outcome=FAIL)

    def consent_stop(self, stop: C.ConsentStop) -> StationStop:
        """
        The consent road's own stop, kept in its words: a seat or a missing file stops the station; a refusal or a fault fails it.
        corridor_consent calls a 5xx a fault; the law's word for a party that could not answer is unreachable, so that one is
        told again as unreachable, the connector's own words unchanged inside it.
        """
        if stop.outcome == "fault" and stop.status and 500 <= int(stop.status) < 600:
            return StationStop("unreachable: the connector could not answer at %s (HTTP %d) — %s; nothing was judged, and a retry may reach it" % (
                stop.route or "the sign-in road", int(stop.status), named(stop.said or stop.sentence, stop.code)), outcome=FAIL)
        told = press_unreachable(stop.sentence, stop.route) if stop.outcome == "unreachable" else stop.sentence
        sentence = told if stop.code is None else "%s [%s]" % (told, "; ".join(
            "%s: %s" % (n, LEXICON[n]["description"]) for n in lexicon_names_in(stop.sentence, stop.code)) or UNCLASSIFIED)
        if stop.outcome == "stopped" or stop.code in C.SEAT_CODES:
            return StationStop(sentence, outcome=STOPPED)
        return StationStop(sentence, outcome=FAIL)

    def guard(self, station: str) -> None:
        if station in GUARDED and not self.i_mean_it and not is_test_ring(self.base, self.rings):
            raise StationStop(guard_sentence(self.base, station), outcome=GUARDED_OUT)

    def need(self, present: Any, sentence: str) -> None:
        if not present:
            # A resumed run that found no standing agent says that, rather than blaming a station it skipped.
            raise StationStop(self.facts.get("resume_refused") or sentence, outcome=NOT_RUN)

    def session(self) -> OwnerMcp:
        """The MCP session S8 opened; a run resumed past S8 opens it here, from the stored credential, exactly as S8 does."""
        if self.mcp is None:
            s8 = self.outcome_of("S8")
            if s8 is not None and s8.outcome != SKIPPED:
                raise StationStop(NO_MCP, outcome=NOT_RUN)  # S8 ran this run and opened none: its line says why
            self.need(self.facts.get("connected"), NO_CONNECTION)
            self.expect("", **{"MCP initialize": "200 with the server's name, version and instructions",
                               "MCP notifications/initialized": "202, a notification", "MCP tools/list": "200 with the tools"})
            session = OwnerMcp(self.oauth, self.label, self.record, self.base + H.MCP_PATH, self.secrets)
            answer = session.initialize(self.current)
            if answer.is_error or not answer.result:
                who = H.who_answered(answer, "connector")
                raise StationStop("initialize was refused — %s: %s" % (who["party"], named(str(who.get("sentence") or answer.quoted()[:400]))), outcome=FAIL)
            session.listed(self.current)
            self.mcp = session
        return self.mcp

    def owner_elsewhere(self) -> Optional[str]:
        """The sentence for an owner born at another connector than this run's base, or None."""
        stored = H.read_json(self.customer.customer_path) if os.path.exists(self.customer.customer_path) else None
        issuer = str((stored or {}).get("issuer") or "").rstrip("/") if isinstance(stored, dict) else ""
        if issuer and normal_base(issuer) != normal_base(self.base):
            return OTHER_BASE_SENTENCE % (self.owner, self.customer.customer_id, issuer, normal_base(self.base))
        return None

    # -- the run's own state, written the moment anything is created ---------------------------------------
    def run_path(self) -> str:
        return os.path.join(self.folder_dir, RUN_FILE)

    def save_state(self) -> None:
        state = dict(self.state)
        state.update({"run_id": self.run_id, "base": self.base, "owner": self.owner, "label": self.label, "saved_at": H.now_iso()})
        self.state = state
        H.write_private(self.run_path(), state)

    def load_state(self) -> Optional[Dict[str, Any]]:
        try:
            stored = H.read_json(self.run_path())
        except (OSError, ValueError):
            return None
        return stored if isinstance(stored, dict) else None

    # -- running ---------------------------------------------------------------------------------------------
    def run(self) -> List[Outcome]:
        self.say("Pathfinder %s at %s as the owner %s (%s) and its agent %s (%s); the record is %s" % (
            self.run_id, self.base, self.owner, C.HARNESS_EMAIL % self.owner, self.label, ROLE_ID, self.folder.path))
        if not is_test_ring(self.base, self.rings):
            self.say("%s is not a declared test ring; %s" % (normal_base(self.base), "--i-mean-it was passed, so the state-creating stations run"
                     if self.i_mean_it else "every state-creating station will refuse it, and the reads run"))
        start_index = 0
        if self.start_at:
            if self.start_at not in STATION_IDS:
                raise H.HarnessError("no station called %s; the stations are %s" % (self.start_at, ", ".join(STATION_IDS)))
            start_index = STATION_IDS.index(self.start_at)
        self.running: Optional[str] = None
        try:
            self.take_up(start_index)
            if start_index:
                self.resume(start_index)
            for index, (station, title) in enumerate(STATIONS[:-1]):
                if index < start_index:
                    outcome = Outcome(station, SKIPPED, "%s: resumed at %s" % (title.lower(), self.start_at))
                else:
                    self.running = station
                    outcome = self.run_station(station, title)
                    self.running = None
                self.outcomes.append(outcome)
                self.say(self.line(outcome))
        except KeyboardInterrupt:
            self.say("Interrupted: the stations not reached are not run, and the teardown runs now.")
            for index, (station, title) in enumerate(STATIONS[:-1]):
                if index < len(self.outcomes):
                    continue
                if index < start_index:
                    outcome = Outcome(station, SKIPPED, "%s: resumed at %s" % (title.lower(), self.start_at))
                else:
                    outcome = Outcome(station, NOT_RUN, "%s: the run was interrupted %s it" % (title.lower(), "during" if station == self.running else "before"))
                self.outcomes.append(outcome)
        finally:
            if len(self.outcomes) < len(STATIONS):
                outcome = self.run_station("S13", TITLES["S13"])
                self.outcomes.append(outcome)
                self.say(self.line(outcome))
        return self.outcomes

    @staticmethod
    def line(outcome: Outcome) -> str:
        return "%s — %s — %s" % (outcome.station, outcome.outcome, outcome.line)

    def run_station(self, station: str, title: str) -> Outcome:
        self.current = station
        self.expect("")
        method = getattr(self, "station_%s" % station.lower())
        try:
            return method()
        except StationStop as stop:
            return Outcome(station, stop.outcome, "%s: %s" % (title.lower(), stop.sentence))
        except C.ConsentStop as stop:
            mapped = self.consent_stop(stop)
            return Outcome(station, mapped.outcome, "%s: %s" % (title.lower(), mapped.sentence))
        except H.Unreachable as err:
            return Outcome(station, FAIL, "%s: unreachable: %s; nothing was judged, and a retry may reach it" % (title.lower(), err))
        except ChainRefused as err:
            return Outcome(station, FAIL, "%s: refused: %s; the chain's own word, and no judgment of the trade" % (title.lower(), err))
        except H.HarnessError as err:
            return Outcome(station, FAIL, "%s: the harness could not complete this station (a fault, not a judgment): %s" % (title.lower(), err))

    def outcome_of(self, station: str) -> Optional[Outcome]:
        return next((o for o in self.outcomes if o.station == station), None)

    def take_up(self, start_index: int) -> None:
        """
        What run.json holds, taken up before any station so nothing a run created is ever recorded nowhere. A run that starts
        at or before S3 creates its own agent: an agent an earlier run left standing — not torn down, or a press whose answer
        was lost — moves to `earlier`, and S13 removes it beside this run's. A run resumed past S3 takes the standing agent up
        as its own (resume). Agents on another connector are kept as they are and never touched from here.
        """
        stored = self.load_state() or {}
        earlier = [e for e in (stored.get("earlier") or []) if isinstance(e, dict)]
        standing = not stored.get("torn_down") and (isinstance(stored.get("agent"), dict) and stored["agent"].get("id") or stored.get("pressed"))
        if start_index > STATION_IDS.index("S3") and standing:
            self.state = dict(stored, earlier=earlier)
            return
        if standing:
            earlier.append({"run_id": stored.get("run_id"), "label": stored.get("label"), "base": stored.get("base"),
                            "agent": stored.get("agent"), "pressed": stored.get("pressed"),
                            "why": "not torn down by run %s" % stored.get("run_id")})
            self.say("an agent of run %s (%s) was not torn down: this run removes it at S13, beside its own" % (stored.get("run_id"), stored.get("label")))
        self.state = {"earlier": earlier}
        if earlier:
            self.save_state()

    def resume(self, start_index: int) -> None:
        """--from: the owner signs in with its stored passkey, on its own connector; past S3, the standing agent is taken up as this run's."""
        self.current = "resume"
        self.expect("a session for the owner, with the stored passkey (no second owner is born)")
        elsewhere = self.owner_elsewhere()
        if elsewhere:
            self.facts["resume_refused"] = elsewhere
            self.say("resume — %s" % elsewhere)
            return
        if self.customer.passkey is None:
            self.say("resume — no owner passkey is stored at %s; the stations that need the owner say so" % self.customer.passkey_path)
        else:
            try:
                self.customer.sign_in()
                self.signed_in = True
                self.say("resume — the owner %s signed in with its stored passkey" % self.customer.customer_id)
            except C.ConsentStop as stop:
                self.say("resume — the owner could not sign in: %s" % stop.sentence)
        if start_index <= STATION_IDS.index("S3"):
            return  # this run creates its own agent; take_up has moved any standing one to `earlier`
        stored = self.state
        if stored.get("base") and normal_base(str(stored["base"])) != normal_base(self.base):
            self.facts["resume_refused"] = ("the standing agent of run %s is on %s, and this run's base is %s: it is resumed and torn down "
                                            "only on its own connector" % (stored.get("run_id"), normal_base(str(stored["base"])), normal_base(self.base)))
            self.state = {"earlier": stored.get("earlier") or []}
        elif isinstance(stored.get("agent"), dict) and stored["agent"].get("id") and not stored.get("torn_down"):
            self.label = str(stored.get("label") or self.label)
            self.run_id = str(stored.get("run_id") or self.run_id)
            agent = stored["agent"]
            self.facts.update({"agent_id": agent.get("id"), "agent_name": agent.get("name"), "wallet": agent.get("wallet") or {},
                               "pact_id": stored.get("pact_id"), "connection_id": stored.get("connection_id")})
            if stored.get("connected"):
                self.facts["connected"] = True
            self.say("resume — the run %s's agent %s stands (%s), and this run takes it up and tears it down at its end"
                     % (self.run_id, agent.get("name"), agent.get("id")))
            return
        if "resume_refused" not in self.facts:
            self.facts["resume_refused"] = NO_RESUME_SENTENCE % self.run_path()
        self.say("resume — %s" % self.facts["resume_refused"])

    # -- S1 Sign up -----------------------------------------------------------------------------------------
    def station_s1(self) -> Outcome:
        born = self.customer.passkey is None
        stored_id = self.customer.customer_id
        if born and stored_id:
            raise StationStop(KEY_LOST_SENTENCE % (stored_id, self.customer.customer_path, self.customer.passkey_path))
        elsewhere = self.owner_elsewhere()
        if elsewhere:
            raise StationStop(elsewhere)
        if born:
            self.guard("S1")
        self.expect("",
                    **{"POST " + C.SIGNUP_OPTIONS: "200 with options (rp.id, challenge, user.id), the nonce, issuedAtMs and the sign-up handle",
                       "POST " + C.SIGNUP_VERIFY: "200 with the customer and a csrfToken, and the session cookie: the owner born, once",
                       "POST " + C.SIGNIN_OPTIONS: "200 with options (challenge, rpId), the nonce and issuedAtMs",
                       "POST " + C.SIGNIN_VERIFY: "200 with the customer customer.json names and a csrfToken: the owner signed in, no second one born"})
        self.customer.sign_up_or_in()
        self.signed_in = True
        customer_id = self.customer.customer_id
        if born:
            return Outcome("S1", PASS, "sign up: the owner was born now — %s, %s, customer %s; its passkey and customer id are at %s, mode 600, "
                           "and every later run signs in with them" % (C.HARNESS_DISPLAY_NAME % self.owner, C.HARNESS_EMAIL % self.owner,
                                                                       customer_id, self.folder_dir))
        if stored_id and (self.customer.customer or {}).get("id") != stored_id:
            raise StationStop("the stored passkey signed in as customer %s, and customer.json names %s: the owner is not the one born"
                              % ((self.customer.customer or {}).get("id"), stored_id), outcome=FAIL)
        return Outcome("S1", PASS, "sign up: the owner %s (%s) signed in with its stored passkey; it was born once and no second owner was created"
                       % (customer_id, C.HARNESS_EMAIL % self.owner))

    # -- S2 The account -------------------------------------------------------------------------------------
    def station_s2(self) -> Outcome:
        self.need(self.signed_in, NO_SESSION)
        self.expect("200 with the customer (the id customer.json names), the subscription's standing, the agents, the connections, "
                    "and the account's assigned signing group %s" % EXPECTED_GROUP)
        answer, view = self.call("GET", ACCOUNT_ROUTE)
        if answer.status != 200 or not isinstance(view, dict):
            raise self.refused("the account", "GET " + ACCOUNT_ROUTE, answer, view)
        customer = view.get("customer") if isinstance(view.get("customer"), dict) else {}
        stored_id = self.customer.customer_id
        if stored_id and customer.get("id") != stored_id:
            raise StationStop("GET %s names customer %s, and the owner born once is %s" % (ACCOUNT_ROUTE, customer.get("id"), stored_id), outcome=FAIL)
        subscription = view.get("subscription") if isinstance(view.get("subscription"), dict) else {}
        standing = subscription.get("standing")
        self.facts["standing"] = standing
        agents = [a for a in (view.get("agents") or []) if isinstance(a, dict)]
        words = "the owner %s, the seat %s (%s, %s), %d agent(s) on the page" % (
            customer.get("id"), standing or "not stated", subscription.get("plan") or "no plan", subscription.get("state") or "no row", len(agents))
        if standing != "paid":
            self.note(C.seat_sentence(stored_id, standing))
        groups = groups_in({k: v for k, v in view.items() if k != "agents"})
        if not groups:
            raise StationStop("%s; GET %s states no assigned signing group on any field, so %s could not be read on this road (the "
                              "connector names the group at the account's birth, from CONNECTOR_SIGNING_GROUP)" % (words, ACCOUNT_ROUTE, EXPECTED_GROUP),
                              outcome=FAIL)
        if EXPECTED_GROUP not in groups or len(groups) != 1:
            raise StationStop("%s; the account is assigned %s, and %s was expected" % (words, ", ".join(groups), EXPECTED_GROUP), outcome=FAIL)
        return Outcome("S2", PASS, "the account: %s; assigned group %s" % (words, EXPECTED_GROUP))

    # -- S3 Create agent ------------------------------------------------------------------------------------
    def station_s3(self) -> Outcome:
        self.guard("S3")
        self.need(self.signed_in, NO_SESSION)
        self.expect("", **{
            "GET " + ACCOUNT_ROUTE: "200 with the owner's account: customer.fundingWallet.address, the funding root the connector registered at the "
                                    "owner's first agent and keeps since (connector Spec 8: registered once), or null for an owner it holds none for yet",
            "GET " + AGENTS_NEW_ROUTE: "200 with the roles, each with its questionnaire (trader.v1 among them), and the chain offer",
            "POST " + C.STEPUP_OPTIONS: "200 with options (challenge, rpId) under the purpose approve, the nonce and issuedAtMs",
            "POST " + AGENTS_ROUTE: "200 with the agent (its id, its child wallet, its pact read back from the platform) and how Claude reaches it",
        })
        funding, funding_words = self.funding_wallet_for_the_press()  # the connector's, else the file's — refused before any press where both are missing
        answer, offer = self.call("GET", AGENTS_NEW_ROUTE)
        if answer.status != 200 or not isinstance(offer, dict):
            refusal = C.refusal_of(offer) or {}
            if refusal.get("code") in C.SEAT_CODES:
                raise StationStop("%s (the connector said: %s)" % (C.seat_sentence(self.customer.customer_id, "lapsed" if refusal.get("code") == "SUBSCRIPTION_LAPSED" else None),
                                                                   C.connector_said(answer, offer, self.secrets)))
            raise self.refused("the questionnaire", "GET " + AGENTS_NEW_ROUTE, answer, offer)
        roles = [r for r in (offer.get("roles") or []) if isinstance(r, dict)]
        role = next((r for r in roles if r.get("id") == ROLE_ID), None)
        if role is None:
            raise StationStop(C.NO_ROLE_SENTENCE % (ROLE_ID, "owner's agent", ", ".join(str(r.get("id")) for r in roles) or "none"), outcome=FAIL)
        chain_offer = offer.get("chainOffer") if isinstance(offer.get("chainOffer"), dict) else {}
        offered = [str(c.get("key")) for c in (chain_offer.get("chains") or []) if isinstance(c, dict) and c.get("key")]
        if not offered and chain_offer.get("unreadable"):
            raise StationStop("the chain offer could not be read — %s" % named(str(chain_offer.get("unreadable"))), outcome=FAIL)
        questionnaire = role.get("questionnaire") if isinstance(role.get("questionnaire"), dict) else {}
        answers = answers_from(questionnaire, offered)
        self.facts["answers"] = answers
        stepped = self.customer.step_up()  # the press that makes authority demands a fresh passkey (the ruling of 8 September 2026)
        body = {"name": self.label, "roleId": ROLE_ID, "fundingAddress": funding, "answers": answers}
        body.update(stepped)
        # Written before the press is sent: an answer lost on the way back may still have created the agent, and the teardown
        # then finds it by this label (S13), so nothing this run made is ever recorded nowhere.
        self.state["pressed"] = {"label": self.label, "at": H.now_iso()}
        self.facts["funding"] = funding
        self.save_state()
        pressed, created = self.call("POST", AGENTS_ROUTE, body, lost="S13 looks for an agent named %s on the account and removes it" % self.label)
        if pressed.status != 200 or not isinstance(created, dict) or not isinstance(created.get("agent"), dict):
            raise self.refused("the agent's creation", "POST " + AGENTS_ROUTE, pressed, created)
        agent = created["agent"]
        wallet = agent.get("wallet") if isinstance(agent.get("wallet"), dict) else {}
        pact = agent.get("pact") if isinstance(agent.get("pact"), dict) else {}
        if not agent.get("id"):
            raise StationStop("the press answered 200 with an agent carrying no id, so nothing the harness could tear down: %s" % short_json(created), outcome=FAIL)
        if pact.get("id"):
            self.facts["born_pact_id"] = pact.get("id")  # born with the agent (the law): S4 must find the same pact
        self.facts.update({"agent_id": agent.get("id"), "agent_name": agent.get("name"), "wallet": {
            "id": wallet.get("id"), "address": wallet.get("address"), "chain": wallet.get("chain"), "isMock": wallet.get("isMock")}})
        self.facts.pop("resume_refused", None)  # this run has its own agent now
        # Written the moment the agent exists, so a run that dies after this is resumed and torn down (S13, --from).
        self.state.update({"agent": {"id": agent.get("id"), "name": agent.get("name"), "roleId": agent.get("roleId"),
                                     "wallet": self.facts["wallet"]}, "created_at": H.now_iso(), "torn_down": False})
        self.save_state()
        if agent.get("name") != self.label or agent.get("roleId") != ROLE_ID:
            raise StationStop("the press created %s (%s), and the harness asked for %s (%s)" % (agent.get("name"), agent.get("roleId"), self.label, ROLE_ID), outcome=FAIL)
        return Outcome("S3", PASS, "create agent: %s (%s) created with a fresh passkey; agent %s, child wallet %s at %s on %s, funding wallet %s — %s; "
                       "the chains %s, per trade US$%s, per day US$%s, ask me first above US$%s, %s transactions a day"
                       % (self.label, ROLE_ID, agent.get("id"), wallet.get("id"), wallet.get("address"), wallet.get("chain"), funding, funding_words,
                          ", ".join(answers["chains"]), answers["perTxUsd"], answers["dailyUsd"], answers["holdAboveUsd"], answers["maxTxPerDay"])
                       + ("; the pact %s %s" % (pact.get("id"), pact.get("state")) if pact else ""))

    # -- S4 Set the policy ----------------------------------------------------------------------------------
    def station_s4(self) -> Outcome:
        self.guard("S4")
        self.need(self.signed_in, NO_SESSION)
        self.need(self.facts.get("agent_id"), NO_AGENT)
        answers = self.facts.get("answers")
        if not answers:  # a resumed run: the questionnaire is read again, exactly as S3 read it
            self.expect("200 with the roles, each with its questionnaire, and the chain offer")
            answer, offer = self.call("GET", AGENTS_NEW_ROUTE)
            if answer.status != 200 or not isinstance(offer, dict):
                raise self.refused("the questionnaire", "GET " + AGENTS_NEW_ROUTE, answer, offer)
            role = next((r for r in (offer.get("roles") or []) if isinstance(r, dict) and r.get("id") == ROLE_ID), None) or {}
            chain_offer = offer.get("chainOffer") if isinstance(offer.get("chainOffer"), dict) else {}
            offered = [str(c.get("key")) for c in (chain_offer.get("chains") or []) if isinstance(c, dict) and c.get("key")]
            answers = answers_from(role.get("questionnaire") if isinstance(role.get("questionnaire"), dict) else {}, offered)
        route = POLICY_ROUTE % self.facts["agent_id"]
        self.expect("200 with the pact S3 was born with: the same id, state active, and the document carrying the answers sent — the edit re-files the policy only, and touches neither the agent nor its token")
        answer, filed = self.call("POST", route, {"answers": answers})
        if answer.status != 200 or not isinstance(filed, dict) or not isinstance(filed.get("pact"), dict):
            raise self.refused("the agent's policy edit", "POST " + POLICY_ROUTE % ":id", answer, filed)
        pact = filed["pact"]
        document = pact.get("document") if isinstance(pact.get("document"), dict) else {}
        self.facts["pact_id"] = pact.get("id")
        self.state["pact_id"] = pact.get("id")
        self.save_state()
        problems: List[str] = []
        if not pact.get("id"):
            problems.append("the pact carries no id")
        if str(pact.get("state") or "") != "active":
            problems.append("the pact's state is %r, not active" % pact.get("state"))
        born = self.facts.get("born_pact_id")
        if born and pact.get("id") != born:
            problems.append("the edit changed the pact: born %s, now %s — the agent and its token must not be touched" % (born, pact.get("id")))
        problems.extend(document_disagreements(document, answers))
        if problems:
            raise StationStop("the connector filed pact %s, and %s" % (pact.get("id"), "; ".join(problems)), outcome=FAIL)
        return Outcome("S4", PASS, "recall the policy: pact %s %s unchanged by the edit; the document carries the questionnaire's answers as sent — per trade US$%s, per "
                       "day US$%s, ask me first above US$%s, %s transactions a day, the chains %s (the wallet's first), the %d contracts of the "
                       "Trader's list under the scope %r" % (pact.get("id"), pact.get("state"), answers["perTxUsd"], answers["dailyUsd"],
                                                             answers["holdAboveUsd"], answers["maxTxPerDay"], ", ".join(answers["chains"]),
                                                             len(answers["counterparties"]), answers["counterpartiesScope"])
                       + ("; %s" % filed.get("entrySaid") if filed.get("entrySaid") else ""))

    # -- S5 The child wallet --------------------------------------------------------------------------------
    def registered_funding_wallet(self) -> Optional[str]:
        """
        The funding wallet the connector's register of record holds for this owner — GET /v1/account, customer.fundingWallet.address: the
        funding root registered at the owner's first agent and kept since (connector Spec 8, services/ceremony.ts provisionCustomer: "a customer
        who already has a funding root keeps it") — in the connector's own spelling, or None where the connector holds none for the owner yet.
        """
        answer, owner = self.call("GET", ACCOUNT_ROUTE)
        if answer.status != 200 or not isinstance(owner, dict):
            raise self.refused("the account", "GET " + ACCOUNT_ROUTE, answer, owner)
        customer = owner.get("customer") if isinstance(owner.get("customer"), dict) else {}
        top = customer.get("fundingWallet") if isinstance(customer.get("fundingWallet"), dict) else {}
        address = str(top.get("address") or "").strip()
        return address if C.ADDRESS_FORM.match(address) else None

    def funding_wallet_for_the_press(self) -> Tuple[str, str]:
        """
        Spec T23: the connector is right about an owner's funding wallet — the root is registered once, at the owner's first agent — so for an
        owner that already exists S3 sends, and S5 and S9 expect, the address GET /v1/account reports; the file (the estate harness's
        funding-wallet.json, rewritten by every estate run that births a wallet) is read only for an owner the connector lists no funding wallet
        for, the one this press is about to register. Answers the address and the S3 line's words saying which was used and why.
        """
        registered = self.registered_funding_wallet()
        if registered:
            return registered, ("the connector's, registered at the owner's first agent and kept since (GET %s customer.fundingWallet; a funding root is "
                                "registered once, connector Spec 8), so the file at %s was not read" % (ACCOUNT_ROUTE, self.funding_wallet))
        funding = C.funding_wallet_address(self.funding_wallet)  # refuses before any press, in the consent's own sentence
        return funding, "the file's (%s): the connector lists no funding wallet for this owner yet, and this press registers it" % self.funding_wallet

    def funding_address(self) -> str:
        """The funding wallet S3 sent, or — on a run resumed past S3 — the connector's registered one read again, else the file's."""
        if not self.facts.get("funding"):
            self.facts["funding"] = self.funding_wallet_for_the_press()[0]
        return str(self.facts["funding"])

    def station_s5(self) -> Outcome:
        self.need(self.signed_in, NO_SESSION)
        self.need(self.facts.get("agent_id"), NO_AGENT)
        self.expect("200 with the walletRecord naming the child wallet S3 created; its status read through the agent's own connection, "
                    "or the connector's sentence for why it cannot be read yet")
        answer, view = self.call("GET", WALLET_RECORD_ROUTE % self.facts["agent_id"])
        if answer.status != 200 or not isinstance(view, dict) or not isinstance(view.get("walletRecord"), dict):
            raise self.refused("the wallet's record", "GET " + WALLET_RECORD_ROUTE % ":id", answer, view)
        record = view["walletRecord"]
        wallet = self.facts.get("wallet") or {}
        if not record.get("walletId"):
            raise StationStop("the agent has no child wallet: %s" % (record.get("absent") or short_json(record)), outcome=FAIL)
        if wallet.get("id") and record.get("walletId") != wallet.get("id"):
            raise StationStop("the wallet record names wallet %s, and S3's agent carries %s" % (record.get("walletId"), wallet.get("id")), outcome=FAIL)
        if wallet.get("isMock") is True:
            raise StationStop("the Wallet minted a mock wallet (isMock true): its address holds no key and nothing can be signed for it", outcome=FAIL)
        # Bound to the owner: the child wallet is minted against the owner's own top-level wallet, the funding wallet S3 sent,
        # and the account the owner's session reads lists the agent as the owner's.
        self.expect("200 with the owner's account: its funding wallet the one S3 sent, and this run's agent among its agents")
        funding = self.funding_address()
        account, owner = self.call("GET", ACCOUNT_ROUTE)
        if account.status != 200 or not isinstance(owner, dict):
            raise self.refused("the account", "GET " + ACCOUNT_ROUTE, account, owner)
        customer = owner.get("customer") if isinstance(owner.get("customer"), dict) else {}
        top = customer.get("fundingWallet") if isinstance(customer.get("fundingWallet"), dict) else {}
        problems: List[str] = []
        if str(top.get("address") or "").lower() != funding.lower():
            problems.append("the owner's funding wallet is %s, and S3 minted the agent against %s" % (top.get("address") or "not stated", funding))
        if not any(isinstance(a, dict) and str(a.get("id")) == str(self.facts["agent_id"]) for a in owner.get("agents") or []):
            problems.append("the owner's account does not list the agent %s" % self.facts["agent_id"])
        if problems:
            raise StationStop("the child wallet %s is not shown bound to the owner: %s" % (record.get("walletId"), "; ".join(problems)), outcome=FAIL)
        self.facts["wallet"] = dict(wallet, id=record.get("walletId"))
        status = record.get("status")
        read = ("its status read through the agent's connection: %s" % short_json(status, 300)) if status else (
            "its status not read yet, in the connector's words: %s" % (record.get("unreachable") or record.get("statusUnreadable") or "no reason given"))
        return Outcome("S5", PASS, "the child wallet: %s at %s on %s, provisioned (not a mock), bound to the owner — minted against the owner's "
                       "funding wallet %s, and the agent listed on the owner's own account; %s" % (
                           record.get("walletId"), wallet.get("address"), wallet.get("chain"), funding, read))

    # -- S6 Buy gas -----------------------------------------------------------------------------------------
    def station_s6(self) -> Outcome:
        self.guard("S6")
        self.need(self.signed_in, NO_SESSION)
        self.expect("400 ANSWER_INVALID naming the floor, US$10.00, and nothing opened")
        floor, refused = self.call("POST", GAS_ROUTE, {"amountUsd": GAS_BELOW_FLOOR_USD})
        floor_refusal = C.refusal_of(refused) or {}
        if floor.status != 400 or floor_refusal.get("code") != "ANSWER_INVALID":
            if 200 <= floor.status < 300:
                raise StationStop("US$%s was not refused: the connector opened a gas press below the floor of US$10.00 — %s" % (
                    GAS_BELOW_FLOOR_USD, short_json(refused, 300)), outcome=FAIL)
            raise self.refused("the gas press below the floor", "POST " + GAS_ROUTE, floor, refused)
        if GAS_FLOOR_SAID not in C.cause_of(floor_refusal):
            raise StationStop("US$%s was refused, and not naming the floor of US$10.00 — %s" % (GAS_BELOW_FLOOR_USD, named(
                C.connector_said(floor, refused, self.secrets), floor_refusal.get("code"))), outcome=FAIL)
        # LIVE-TODO: the gas press opens a Stripe Checkout and the credit lands only by the desk's signed event
        # (handleGasPurchaseEvent, then the held-credit worker); the source offers no test-credit road, so how the test ring
        # credits ten dollars without a card is confirmed live. Until then the station judges the press and the live read.
        self.expect("200 with a checkout (url, id) for US$10.00, amountCents 1000")
        pressed, checkout = self.call("POST", GAS_ROUTE, {"amountUsd": "10"})
        if pressed.status != 200 or not isinstance(checkout, dict) or not isinstance(checkout.get("checkout"), dict):
            raise self.refused("the gas press", "POST " + GAS_ROUTE, pressed, checkout)
        if checkout.get("amountCents") != GAS_MINIMUM_USD_CENTS:
            raise StationStop("the gas press opened a checkout for %s cents, and ten dollars (1000) was pressed" % checkout.get("amountCents"), outcome=FAIL)
        self.expect("200: the gas account read live from the platform (read platform), the available figure, the minimum US$10.00")
        read_answer, gas = self.call("GET", GAS_ACCOUNT_ROUTE)
        if read_answer.status != 200 or not isinstance(gas, dict):
            raise self.refused("the gas account", "GET " + GAS_ACCOUNT_ROUTE, read_answer, gas)
        if gas.get("read") != "platform":
            raise StationStop("the checkout %s opened for US$10.00, and the gas account was not read live — %s"
                              % (checkout["checkout"].get("id"), named(str(gas.get("unreadable") or gas.get("said")))), outcome=FAIL)
        if gas.get("minimumTopUpCents") != GAS_MINIMUM_USD_CENTS:
            raise StationStop("the gas account states a minimum of %s cents, and ten dollars was expected" % gas.get("minimumTopUpCents"), outcome=FAIL)
        available = (gas.get("available") or {}).get("cents") if isinstance(gas.get("available"), dict) else None
        self.facts["gas_after_s6"] = available
        held = [h for h in (gas.get("held") or []) if isinstance(h, dict)]
        return Outcome("S6", PASS, "buy gas: US$%s refused naming the floor; the checkout %s opened for US$10.00; the gas account read live: %s%s%s"
                       % (GAS_BELOW_FLOOR_USD, checkout["checkout"].get("id"), gas.get("said"), " (low)" if gas.get("low") else "",
                          ("; %d payment(s) not yet credited: %s" % (len(held), "; ".join(str(h.get("said")) for h in held))) if held else ""))

    # -- S7 Connect Claude ----------------------------------------------------------------------------------
    def station_s7(self) -> Outcome:
        self.guard("S7")
        self.need(self.signed_in, NO_SESSION)
        self.need(self.facts.get("agent_id"), NO_AGENT)
        self.expect("", **{
            "GET " + DISCOVERY_ROUTE: "200 with the authorization server's metadata (authorize, token, registration)",
            "GET " + RESOURCE_ROUTE: "200 naming the MCP resource",
            "POST /register": "201 with the client id, PKCE and no secret",
            "POST " + C.SIGNIN_OPTIONS: "200 with options (challenge, rpId), the nonce and issuedAtMs",
            "POST " + C.SIGNIN_VERIFY: "200 with the owner's session",
            "GET /authorize": "302 to the consent page, ?request=<id>, read without following (PKCE S256)",
            "GET /v1/consent/": "200 at stage agent, listing this run's agent with no connection yet",
            "POST /v1/consent/": "200 with redirectTo carrying the code and the state sent: {agentId}, the first connection of an agent born on the dashboard",
            "POST /token": "200 with the per-connection access and refresh tokens",
        })
        # A connection is this run's only once S7 makes it: a flag carried from run.json does not outlive a failed S7.
        self.facts.pop("connected", None)
        self.state["connected"] = False
        self.save_state()
        self.prepare_oauth()
        _, how = self.connect()
        self.facts["connected"] = True
        self.state["connected"] = True
        self.save_state()
        connection = self.connection_of_agent()
        if connection:
            self.facts["connection_id"] = connection.get("id")
            self.state["connection_id"] = connection.get("id")
            self.save_state()
        return Outcome("S7", PASS, "connect Claude: %s — %s; the connection %s%s; the per-connection credential is stored at %s, mode 600"
                       % (self.label, how, (connection or {}).get("id") or "(not listed)",
                          (" in the rank %s" % (connection.get("rank") or {}).get("id")) if isinstance((connection or {}).get("rank"), dict) else "",
                          self.oauth.token_path(self.label)))

    def connect(self) -> Tuple[Dict[str, Any], str]:
        """
        The consent, walked for the agent S3 created and for no other. corridor_consent's pieces — the owner's sign-in, the wire,
        the authorize link, the stage words, the code and state readers, the seat sentence — without Consent's create branch: at
        step three a press naming no standing agent creates one (routes/consent.ts, POST /v1/consent/:id/agent), so this road
        presses only /finish, for this run's agent as the stage lists it, and stops where the stage does not list it.
        """
        customer, wire = self.customer, self.customer.wire
        customer.sign_in()
        client = self.oauth.client()
        verifier, challenge = H.pkce_pair()
        state = secrets.token_urlsafe(24)
        wire.note_secret(verifier)
        redirect_uri = str(client["redirect_uri"])  # the registered loopback; any loopback port matches, and none is bound
        link = self.oauth.authorization_link(client["client_id"], redirect_uri, challenge, state)
        opened, parsed = wire.call("GET", link, follow_redirects=False)
        location = next((v for k, v in opened.headers.items() if k.lower() == "location"), None)
        request_id = C.request_id_of(location) if opened.status in (302, 303, 307) and location else None
        if not request_id:
            if opened.status in (302, 303, 307) and location:
                raise StationStop("refused: the authorize road sent the harness to %s instead of the consent page — %s" % (
                    H.redact(location, self.secrets, mask=C.last4), named(C.Consent.oauth_error_of(location))), outcome=FAIL)
            raise self.refused("the authorize request", "GET /authorize", opened, parsed)
        read, stage = wire.call("GET", C.CONSENT_ROUTE % request_id + "?" + C.CONSENT_CONNECT_QUERY)
        if read.status != 200 or not isinstance(stage, dict) or stage.get("stage") not in C.STAGES:
            raise self.refused("the consent's stage", "GET " + C.CONSENT_ROUTE % ":id", read, stage)
        word = str(stage["stage"])
        if word == "pay":
            subscription = stage.get("subscription") if isinstance(stage.get("subscription"), dict) else {}
            raise StationStop(C.seat_sentence(customer.customer_id, subscription.get("standing")))
        if word == "closed":
            closed = stage.get("closed") if isinstance(stage.get("closed"), dict) else {}
            raise StationStop("refused: the connection request is %s — %s" % (closed.get("state"), named(str(closed.get("said")))), outcome=FAIL)
        if word != "agent":
            raise StationStop("answered with an error: the connector answered stage %s to the owner's signed-in read asking for step three (?%s)"
                              % (word, C.CONSENT_CONNECT_QUERY), outcome=FAIL)
        agents = [a for a in (stage.get("agents") or []) if isinstance(a, dict)]
        mine = next((a for a in agents if str(a.get("id")) == str(self.facts["agent_id"])), None)
        if mine is None:
            raise StationStop("this run's agent %s (%s) is not listed at the consent's step three, which lists %s: the connector lists the "
                              "owner's active agents only, so it is halted, deleted or not this owner's; nothing was pressed, since a press "
                              "naming no standing agent would create another" % (
                                  self.facts["agent_id"], self.label, ", ".join("%s (%s)" % (a.get("name"), a.get("id")) for a in agents) or "none"))
        role = next((r for r in (stage.get("roles") or []) if isinstance(r, dict) and r.get("id") == ROLE_ID), {})
        rank = str(role.get("defaultRank") or "agent")
        if mine.get("connectionId"):
            body: Dict[str, Any] = {"connectionId": mine["connectionId"], "rank": rank}
            how = "the connection it already held, handed over"
        else:
            body = {"agentId": mine["id"]}
            how = "connected for the first time (Spec 35: the first connection of an agent born on the dashboard)"
        finished, done = wire.call("POST", C.FINISH_ROUTE % request_id, body)
        if finished.status != 200 or not isinstance(done, dict) or not done.get("redirectTo"):
            refusal = C.refusal_of(done) or {}
            if refusal.get("code") in C.SEAT_CODES:
                raise StationStop("%s (the connector said: %s)" % (C.seat_sentence(customer.customer_id, "lapsed" if refusal.get("code") == "SUBSCRIPTION_LAPSED"
                                                                                   else None), C.connector_said(finished, done, self.secrets)))
            raise self.refused("the finish", "POST " + C.FINISH_ROUTE % ":id", finished, done)
        code, came_state = C.code_and_state_of(str(done["redirectTo"]))
        wire.note_secret(code)
        if came_state != state:
            raise StationStop("answered with an error: the finish came back with a state the harness did not send; nothing was exchanged", outcome=FAIL)
        if not code:
            raise StationStop("answered with an error: the finish came back without a code in redirectTo", outcome=FAIL)
        exchanged, tokens = wire.call("POST", str(self.oauth.metadata()["token_endpoint"]), form={
            "grant_type": "authorization_code", "client_id": str(client["client_id"]), "code": code,
            "code_verifier": verifier, "redirect_uri": redirect_uri,
        })
        if exchanged.status != 200 or not isinstance(tokens, dict) or not tokens.get("access_token"):
            said = C.connector_said(exchanged, tokens, self.secrets)
            if isinstance(tokens, dict) and tokens.get("error") in ("invalid_grant", "invalid_client", "unauthorized_client"):
                raise StationStop("refused: the token endpoint refused the code for %s — %s; the answer will be the same on retry" % (self.label, named(said)),
                                  outcome=FAIL)
            raise self.refused("the code's exchange", "POST /token", exchanged, tokens)
        for value in (tokens.get("access_token"), tokens.get("refresh_token")):
            wire.note_secret(value)
        stored = self.oauth.store_tokens(self.label, tokens, str(client["client_id"]), extra={
            "customer_id": customer.customer_id, "agent_id": mine["id"], "agent_name": self.label, "rank": body.get("rank") or rank,
            "consented_at": H.now_iso(), "consented_by": "Pathfinder's own passkey, %s" % how})
        return stored, how

    def prepare_oauth(self) -> None:
        """The discovery and the client registration, made on the recorded wire so the record carries them, then handed to the Oauth road's own cache."""
        wire = self.customer.wire
        if self.oauth._metadata is None:
            answer, meta = wire.call("GET", DISCOVERY_ROUTE)
            if answer.status != 200 or not isinstance(meta, dict):
                raise self.refused("the authorization server's metadata", "GET " + DISCOVERY_ROUTE, answer, meta)
            self.oauth._metadata = meta
        if self.oauth._resource is None:
            answer, resource = wire.call("GET", RESOURCE_ROUTE)
            self.oauth._resource = resource if answer.status == 200 and isinstance(resource, dict) else {}
        stored = H.read_json(self.oauth.client_path())
        if not (stored and stored.get("issuer") == self.oauth.issuer and stored.get("client_id")):
            redirect = "http://127.0.0.1:%d/callback" % H.REGISTERED_REDIRECT_PORT
            body = {"redirect_uris": [redirect], "client_name": CLIENT_NAME, "token_endpoint_auth_method": "none",
                    "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"]}
            answer, registered = wire.call("POST", str(self.oauth._metadata["registration_endpoint"]), body)
            if answer.status != 201 or not isinstance(registered, dict) or not registered.get("client_id"):
                raise self.refused("the client registration", "POST /register", answer, registered)
            H.write_private(self.oauth.client_path(), {"issuer": self.oauth.issuer, "client_id": registered["client_id"], "redirect_uri": redirect,
                                                       "registered_at": H.now_iso(), "registration": registered})

    def connection_of_agent(self) -> Optional[Dict[str, Any]]:
        """This run's agent's live connection, as GET /v1/account lists it."""
        self.expect("200 with the connections: this run's agent's live connection among them")
        answer, view = self.call("GET", ACCOUNT_ROUTE)
        if answer.status != 200 or not isinstance(view, dict):
            return None
        for row in view.get("connections") or []:
            if isinstance(row, dict) and str(row.get("agentId")) == str(self.facts.get("agent_id")) and row.get("state") == "active":
                return row
        return None

    # -- S8 The catalogue -----------------------------------------------------------------------------------
    def station_s8(self) -> Outcome:
        if self.facts.get("resume_refused") and not self.facts.get("agent_id"):
            raise StationStop(self.facts["resume_refused"], outcome=NOT_RUN)
        self.need(self.facts.get("connected"), NO_CONNECTION)
        self.expect("", **{"MCP initialize": "200 with the server's name, version and instructions",
                           "MCP notifications/initialized": "202, a notification",
                           "MCP tools/list": "200 with the fourteen tools: %s" % ", ".join(CATALOGUE)})
        session = OwnerMcp(self.oauth, self.label, self.record, self.base + H.MCP_PATH, self.secrets)
        answer = session.initialize("S8")
        if answer.is_error or not answer.result:
            who = H.who_answered(answer, "connector")
            raise StationStop("initialize was refused — %s: %s" % (who["party"], named(str(who.get("sentence") or answer.quoted()[:400]))), outcome=FAIL)
        self.mcp = session
        tools = session.listed("S8")
        names = [str(t.get("name")) for t in tools if isinstance(t, dict)]
        missing = [n for n in CATALOGUE if n not in names]
        extra = [n for n in names if n not in CATALOGUE]
        info = session.server_info or {}
        head = "%s %s" % (info.get("name") or "the connector", info.get("version") or "")
        if missing or extra or len(names) != CATALOGUE_SIZE:
            raise StationStop("%s lists %d tool(s), and the fourteen were expected%s%s" % (
                head.strip(), len(names), ("; missing: %s" % ", ".join(missing)) if missing else "", ("; not expected: %s" % ", ".join(extra)) if extra else ""),
                outcome=FAIL)
        return Outcome("S8", PASS, "the catalogue: %s lists the fourteen tools — %s" % (head.strip(), ", ".join(names)))

    # -- S9 The agent ---------------------------------------------------------------------------------------
    def station_s9(self) -> Outcome:
        self.session()
        self.expect("the agent this connection holds: its wallet UUID, its pact (id, state, hashes), and the owner's gas balance read live")
        answer = self.mcp.call(H.MY_AGENT_TOOL, {}, "S9")
        data = answer.data if isinstance(answer.data, dict) else {}
        if answer.is_error or not data:
            who = H.who_answered(answer, "connector")
            raise StationStop("aerconnect_my_agent was refused — %s: %s" % (who["party"], named(str(who.get("sentence") or answer.quoted()[:400]))), outcome=FAIL)
        wallet = data.get("wallet") if isinstance(data.get("wallet"), dict) else {}
        limits = data.get("limits") if isinstance(data.get("limits"), dict) else {}
        gas = H.gas_account_in(data)
        agent = data.get("agent") if isinstance(data.get("agent"), dict) else {}
        problems: List[str] = []
        if not UUID_FORM.match(str(wallet.get("id") or "")):
            problems.append("the wallet id %r is not a UUID" % wallet.get("id"))
        known = (self.facts.get("wallet") or {}).get("id")
        if known and wallet.get("id") and wallet.get("id") != known:
            problems.append("the wallet is %s, and S3's agent carries %s" % (wallet.get("id"), known))
        if agent.get("name") and agent.get("name") != self.label:
            problems.append("the agent is %s, and this run's is %s" % (agent.get("name"), self.label))
        if not limits.get("pactId"):
            problems.append("no pact: %s" % (limits.get("absent") or limits.get("said") or "the limits carry no pactId"))
        elif self.facts.get("pact_id") and limits.get("pactId") != self.facts.get("pact_id"):
            problems.append("the pact is %s, and S4 filed %s" % (limits.get("pactId"), self.facts.get("pact_id")))
        if limits.get("state") not in (None, "active"):
            problems.append("the pact's state is %r" % limits.get("state"))
        if not gas.get("read"):
            problems.append("the gas balance was not read: %s" % ((data.get("gasAccount") or {}).get("unreadable") if isinstance(data.get("gasAccount"), dict) else "no gas_account"))
        funding = (data.get("fundingWallet") or {}).get("address") if isinstance(data.get("fundingWallet"), dict) else None
        if self.facts.get("funding") and str(funding or "").lower() != str(self.facts["funding"]).lower():
            problems.append("the agent's funding wallet is %s, and S3 minted it against %s" % (funding or "not stated", self.facts["funding"]))
        if problems:
            raise StationStop("; ".join(problems), outcome=FAIL)  # a wallet S9 rejected is never adopted
        self.facts["wallet"] = dict(self.facts.get("wallet") or {}, id=wallet.get("id") or known, address=wallet.get("address") or (self.facts.get("wallet") or {}).get("address"),
                                    chain=wallet.get("chain") or (self.facts.get("wallet") or {}).get("chain"))
        self.facts["gas_s9"] = gas.get("available")
        return Outcome("S9", PASS, "the agent: %s (%s), wallet %s at %s on %s; pact %s %s, document hash %s, policy hash %s; the owner's gas account %s"
                       % (agent.get("name"), agent.get("roleId"), wallet.get("id"), wallet.get("address"), wallet.get("chain"), limits.get("pactId"),
                          limits.get("state") or "", limits.get("documentHash") or "not stated", limits.get("policyHash") or "not stated",
                          data.get("gas_account")))

    # -- S10 The judgment -----------------------------------------------------------------------------------
    def station_s10(self) -> Outcome:
        self.session()
        wallet_id = (self.facts.get("wallet") or {}).get("id")
        self.need(wallet_id, NO_WALLET_ID)
        self.expect("allow, with a receipt for this exact action (the trade within the mandate)")
        # LIVE-TODO: the trade's arguments are shaped to the inputSchema police.check_action declares live (arguments_for: the
        # required name wins), from MCP Police at c2af71c — role_id, action_kind, asset_symbol, amount_usd_cents, to_asset,
        # venue, contract_address, child_wallet_id; the relay fills function and slippage_bps. Confirm on the production door.
        args, omitted = H.arguments_for(self.mcp.schema_of("police.check_action"), TRADE, {"wallet_id": wallet_id, "role_id": ROLE_ID})
        if omitted:
            self.note("the Police's schema declares no field for: %s" % ", ".join(sorted(set(omitted))))
        answer = self.mcp.call("police.check_action", args, "S10")
        police = H.classify_police(answer)
        self.facts["police"] = police
        who = police.get("who") or {}
        if police["kind"] != "allow":
            raise StationStop("%s answered %s — %s" % (who.get("party", "MCP Police"), police["kind"], named(str(police.get("sentence") or ""),
                                                                                                                         who.get("reason") or None)), outcome=FAIL)
        if not police.get("receipt"):
            raise StationStop("MCP Police allowed the trade and issued no receipt — %s" % short_json(answer.data, 500), outcome=FAIL)
        self.facts["receipt"] = police["receipt"]
        return Outcome("S10", PASS, "the judgment: MCP Police allowed the trade (%s US$%.2f of %s for %s on %s through %s, %s) and issued receipt %s; "
                       "the policy hash it judged under %s" % (TRADE["action"], TRADE["amount_usd"], TRADE["asset"], TRADE["to_asset"], TRADE["chain"],
                                                              TRADE["venue"], TRADE["contract_address"], police.get("receipt_id") or "issued",
                                                              police.get("policy_hash") or "not stated"))

    # -- S11 The trade --------------------------------------------------------------------------------------
    def station_s11(self) -> Outcome:
        self.guard("S11")
        self.session()
        wallet = self.facts.get("wallet") or {}
        self.need(wallet.get("id"), NO_WALLET_ID)
        if not self.facts.get("receipt") and (self.outcome_of("S10") or Outcome("S10", "", "")).outcome == SKIPPED:
            raise StationStop("S10 was passed over by --from %s, and its receipt — single-use, and never written down — is not kept: resume "
                              "at S10" % self.start_at, outcome=NOT_RUN)
        self.need(self.facts.get("receipt"), NO_RECEIPT)
        facts = {"wallet_id": wallet["id"]}
        # the wallet's own balances first: the harness trades only what the wallet holds — and where the wallet is short, the harness funds it
        # itself, from Harness Holdings through the estate's own road (Spec T23); no station asks a person for anything
        self.expect("the wallet's balances on its own chain: USDC at least %d minor units (US$0.10); short of it, Harness Holdings funds the "
                    "wallet through the estate's own road" % TRADE_RAW)
        balances, usdc, weth, held = self.read_agent_balances(facts)
        funded: Optional[str] = None
        if held is None or held < TRADE_RAW:
            usdc, weth, held, funded = self.fund_the_wallet(wallet, facts, held, balances)
        else:
            self.note(HELD_ALREADY_SENTENCE % (wallet.get("address"), TRADE["chain"], held, TRADE_RAW))
        self.facts["before"] = {"usdc": held, "weth": raw_of(weth), "usdc_contract": contract_of(usdc), "weth_contract": contract_of(weth)}
        self.expect("200: the gas account read live, before the trade")
        gas_answer, gas = self.call("GET", GAS_ACCOUNT_ROUTE)
        self.facts["gas_before"] = ((gas or {}).get("available") or {}).get("cents") if isinstance(gas, dict) and isinstance(gas.get("available"), dict) else None
        # LIVE-TODO: build_transaction's trade arguments, shaped to its live inputSchema, from stablepro-agent-server
        # internal/mcp/catalog.go at 125f788 — wallet_id, action trade, amount_usd in dollars, chain, asset (the coin sold),
        # to_asset (the coin bought), venue, contract_address (the venue's router), police_receipt, client_request_id.
        self.expect("a single-use ticket for the trade, with the pact it was built under")
        build_args, omitted = H.arguments_for(self.mcp.schema_of("wallet.build_transaction"), TRADE, dict(facts, police_receipt=self.facts["receipt"]))
        properties, _, _ = H.schema_parts(self.mcp.schema_of("wallet.build_transaction"))
        if properties and "client_request_id" in properties:
            build_args["client_request_id"] = "pathfinder-%s" % self.run_id  # the build's idempotency key: a retry is the same ticket
        built = self.mcp.call("wallet.build_transaction", build_args, "S11")
        build = H.classify_wallet(built)
        if build["kind"] != "ticket" or not build.get("ticket_id"):
            who = build.get("who") or {}
            raise StationStop("the Wallet did not build it — %s (%s): %s" % (who.get("party", "the MCP Wallet"), build["kind"],
                                                                                        named(str(build.get("sentence") or built.text[:400]), who.get("reason") or None)), outcome=FAIL)
        pact_id = H.find_key(built.data, ["pact_id", "pactId"], str) if isinstance(built.data, (dict, list)) else None
        # LIVE-TODO: submit_transaction's required fields (catalog.go: agent_id, wallet_id, pact_id, ticket_id, action) and the
        # trade's fields identical to the build's; the agent id is the connector's (the platform's subject), the pact the build's.
        self.expect("the operation signed and sent: the userOpHash, the sponsor's handleOps transaction, the platform's status, the debit")
        submit_args, _ = H.arguments_for(self.mcp.schema_of("wallet.submit_transaction"), TRADE,
                                         dict(facts, ticket_id=build["ticket_id"], pact_id=pact_id or self.facts.get("pact_id")))
        properties, _, _ = H.schema_parts(self.mcp.schema_of("wallet.submit_transaction"))
        if properties and "agent_id" in properties:
            submit_args["agent_id"] = self.facts.get("agent_id")
        submitted = self.mcp.call("wallet.submit_transaction", submit_args, "S11")
        submit = H.classify_wallet(submitted)
        data = submitted.data if isinstance(submitted.data, dict) else {}
        operation = H.find_key(data, ["execution", "user_operation"], dict) or {}
        sent = bool(operation.get("user_op_hash") or operation.get("handle_ops_tx_hash"))
        if not sent and (submitted.is_error or submit["kind"] in ("refused", "held", "no_judgment")):
            who = submit.get("who") or {}
            raise StationStop("the Wallet refused the submit — %s (%s): %s" % (who.get("party", "the MCP Wallet"), submit["kind"],
                                                                                named(str(submit.get("sentence") or submitted.text[:400]), who.get("reason") or None)), outcome=FAIL)
        if sent and submitted.is_error:
            # The operation left: a confirmation that timed out is the Wallet's word that it "was sent and may still land"
            # (useroperation.go, confirmation_timeout), never a refusal. Its words travel, and its ticket is followed.
            reason = H.find_key(data, ["reason", "reason_code", "code"], str)
            words = H.find_key(data, ["message"], str) or submitted.text[:400]
            self.note("the Wallet answered the submit with an error after the operation was sent — %s; the harness follows its ticket"
                      % named("%s: %s" % (reason, words) if reason and not str(words).startswith(reason) else str(words), reason))
        self.facts["ticket_id"] = build["ticket_id"]
        self.remember_trade(operation, build["ticket_id"])
        operation = self.until_landed(operation, build["ticket_id"])
        self.remember_trade(operation, build["ticket_id"])  # written before the chain is read: an RPC that fails loses no hash
        user_op_hash = str(operation.get("user_op_hash") or "").lower()
        handle_ops = str(operation.get("handle_ops_tx_hash") or "").lower()
        self.facts["operation"] = operation
        status = str(operation.get("status") or "")
        # The Wallet's `success` is the UserOperationEvent's flag once landed and false before (UserOperationOutcome), so it is
        # read only on an answer that says landed; the chain's own event, read below, is the judge of a landing either way.
        if status in ("reverted", "expired", "failed") or (status == "landed" and operation.get("success") is False):
            raise StationStop("the operation %s %s — %s" % (user_op_hash or "(no hash)", operation.get("status") or "did not succeed",
                                                             named(str(operation.get("reason") or "the Wallet named no reason"))), outcome=FAIL)
        if not landed_word(operation) or not H.HEX64.fullmatch(handle_ops or ""):
            raise StationStop("the operation %s had not landed at the deadline of %s s (status %s, handleOps %s); the ticket is %s, and run.json "
                              "keeps both hashes for --from S12" % (user_op_hash or "(no hash)", int(self.deadline), operation.get("status") or "not stated",
                                                                   handle_ops or "not named", build["ticket_id"]), outcome=FAIL)
        self.expect("the handleOps receipt: status 0x1, and the UserOperationEvent for this userOpHash: success, from the wallet, paid by the group-100 paymaster")
        # The Wallet's word that it landed travels with any answer the chain could not give: the hashes are in run.json, and S12 reads again.
        kept = ("the Wallet says the operation %s landed in the handleOps transaction %s; run.json keeps both hashes, and S12 reads the "
                "receipt again" % (user_op_hash or "(no hash)", handle_ops))
        try:
            receipt = self.receipt_of(handle_ops, wait=True)
        except ChainRefused as err:
            raise StationStop("refused: %s; the chain's own word, and no judgment of the trade — %s" % (err, kept), outcome=FAIL)
        except H.Unreachable as err:
            raise StationStop("unreachable: %s; nothing was judged, and a retry may reach it — %s" % (err, kept), outcome=FAIL)
        if not isinstance(receipt, dict):
            raise StationStop("%s names no receipt for the handleOps transaction %s within %d s — %s" % (self.chain.host, handle_ops, int(self.deadline), kept),
                              outcome=FAIL)
        self.facts["receipt_tx"] = receipt
        event = next((e for e in user_operation_events(receipt) if e["user_op_hash"] == user_op_hash), None)
        problems: List[str] = []
        if H.hex_quantity(receipt.get("status")) != 1:
            problems.append("the handleOps receipt's status is %s" % receipt.get("status"))
        if event is None:
            # The platform's own sentence for the same absence (internal/gas/settle.go): no other operation's event stands in.
            problems.append("the EntryPoint emitted no UserOperationEvent for this hash in the transaction (%s in %s)" % (user_op_hash, handle_ops))
        else:
            if event["success"] is not True:
                problems.append("the UserOperationEvent says the operation did not succeed")
            if wallet.get("address") and event["sender"].lower() != str(wallet["address"]).lower():
                problems.append("the operation's sender is %s, and the wallet is %s" % (event["sender"], wallet["address"]))
            if event["paymaster"].lower() != PAYMASTER[TRADE["chain"]].lower():
                problems.append("the paymaster is %s, and the group-100 paymaster is %s" % (event["paymaster"], H.checksum_address(PAYMASTER[TRADE["chain"]])))
        if problems:
            raise StationStop("; ".join(problems), outcome=FAIL)
        self.facts["event"] = event
        return Outcome("S11", PASS, "the trade: %sticket %s submitted; the operation %s landed in the handleOps transaction %s (block %s), from the wallet "
                       "%s, sponsored by the paymaster %s; the Wallet's calls %s; reserved US$%s, debited US$%s" % (
                           ("funded by Harness Holdings through the estate's own road — %s; " % funded) if funded
                           else "the wallet held %d minor units of USDC already, so nothing was funded; " % held,
                           build["ticket_id"], user_op_hash, handle_ops, H.hex_quantity(receipt.get("blockNumber")), event["sender"], event["paymaster"],
                           ", ".join(operation.get("calls") or []) or "not stated", operation.get("reserved_usd") or "not stated",
                           operation.get("debited_usd") or "not stated"))

    def remember_trade(self, operation: Dict[str, Any], ticket_id: str) -> None:
        """What a resumed S12 and S12a need, in run.json — the hashes, the ticket, the readings taken before — and never a secret."""
        self.state["traded"] = {
            "user_op_hash": str(operation.get("user_op_hash") or "").lower() or None,
            "handle_ops_tx_hash": str(operation.get("handle_ops_tx_hash") or "").lower() or None,
            "delegation_tx_hash": str(operation.get("delegation_tx_hash") or "").lower() or None,
            "ticket_id": ticket_id, "status": operation.get("status"), "debited_usd": operation.get("debited_usd"),
            "reserved_usd": operation.get("reserved_usd"), "before": self.facts.get("before"), "gas_before": self.facts.get("gas_before"),
            "saved_at": H.now_iso(),
        }
        self.save_state()

    # -- S11 funds the agent itself (Spec T23) ----------------------------------------------------------------
    def read_agent_balances(self, facts: Dict[str, Any]) -> Tuple[H.McpAnswer, Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[int]]:
        """The child wallet's balances through wallet.get_balances: the answer, its USDC and WETH rows on the trade's chain, and the USDC held in minor units."""
        args, _ = H.arguments_for(self.mcp.schema_of("wallet.get_balances"), {}, facts)
        balances = self.mcp.call("wallet.get_balances", args, "S11")
        usdc = balance_row(balances.data, TRADE["chain"], TRADE["asset"])
        return balances, usdc, balance_row(balances.data, TRADE["chain"], TRADE["to_asset"]), raw_of(usdc)

    @staticmethod
    def holds_words(held: Optional[int], balances: H.McpAnswer) -> str:
        return ("%d minor units of USDC" % held) if held is not None else "no USDC row the harness could read (%s)" % short_json(balances.data, 300)

    def agent_wallet_usdc(self, facts: Dict[str, Any]) -> Tuple[Optional[int], str]:
        """The payee's balance as the estate's payment road reads one (Runner.pay, before and after): the child wallet's USDC through wallet.get_balances."""
        balances, _, _, held = self.read_agent_balances(facts)
        return held, self.holds_words(held, balances)

    def fund_the_wallet(self, wallet: Dict[str, Any], facts: Dict[str, Any], held: Optional[int], balances: H.McpAnswer
                        ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], int, str]:
        """
        Spec T23: this run's agent is born with an empty wallet, and the harness — the owner — funds it from Harness Holdings through the
        estate's own road, exactly as the estate harness moves Holdings' money (S6, S7, T14): the wallet made a payee at the roster's quorum,
        one one-off set of one payment of TRADE_RAW, reviewed, created, submitted, approved and executed through the estate's machinery, the
        Treasury paying Holdings the shortfall first where Holdings is short, gas credited through the admin road where the review refuses
        for want of it; then the harness waits for its own money (until_funded). The estate harness's own stops travel in its words: a
        missing prerequisite — the Treasury not born, no admin credential — is a stop this run cannot get past by itself; the estate's
        refusal is the estate failing; a transport fault is unreachable. Answers the wallet's USDC and WETH rows, the USDC held, and the words.
        """
        address = str(wallet.get("address") or "")
        self.note(SHORT_SENTENCE % (address, TRADE["chain"], self.holds_words(held, balances), TRADE_RAW))
        self.facts["estate_sent"] = []
        try:
            return self.holdings_pays_the_wallet(address, facts)
        except E.StationStop as stop:
            raise StationStop("%s; %s" % (stop, self.sent_words()) if stop.prerequisite else "%s; %s" % (stop.sentence, self.sent_words()),
                              outcome=STOPPED if stop.prerequisite else FAIL)
        except E.Unreachable as err:
            raise StationStop("unreachable: the estate could not be reached, so nothing was judged: %s; %s" % (err, self.sent_words()), outcome=FAIL)
        except E.HarnessError as err:
            raise StationStop("the estate harness could not complete the funding (a fault, not a judgment): %s; %s" % (err, self.sent_words()), outcome=FAIL)

    def sent_words(self) -> str:
        """What this run's funding road had sent when it stopped — nothing, or each payment that left, named — so no stop says 'nothing was sent' untruthfully."""
        sent = self.facts.get("estate_sent") or []
        return "nothing was sent" if not sent else "sent before the stop: %s" % "; ".join(sent)

    def estate_runner(self) -> E.Runner:
        """
        The estate harness's own Runner for Harness Holdings — its wire, its people, its payee and payment roads — on the estate's base and
        store, with this run's clock, sleep and terminal, and its evidence written into this run's record as it happens (the Treasury's own
        runner beside it the same). Built once per run; nothing is sent until a station asks it to.
        """
        if self.estate is None:
            estate = E.Runner(self.estate_base, self.estate_store, transport=self.estate_transport, say=self.say, sleep=self.sleep, clock=self.clock,
                              openssl=self.customer.openssl, admin_env=self.estate_admin_env, in_colour=False)
            estate.load_passkeys()
            self.adopt_estate_records(estate, A.ESTATE["company"])
            self.adopt_estate_records(estate.for_treasury(), ET.TREASURY["company"])
            self.estate = estate
        return self.estate

    def adopt_estate_records(self, runner: E.Runner, where: str) -> None:
        """
        Every evidence entry, note and finding the estate runner writes is written into this run's record the moment it is written — the
        route, who, what was sent, what came back (redacted by the estate runner to the last four characters, and once more here with every
        secret it has seen), the expectation and the result — so the report's S11 carries the estate's road call by call beside the
        connector's and the doors'. The runner's own records are kept as they are.
        """
        original_step, original_note, original_finding = runner.step, runner.note, runner.finding

        def step(station: str, call_answer: Any, expected: str, result: str, sent: Any = None, who: str = "") -> None:
            original_step(station, call_answer, expected, result, sent, who)
            entry = runner.evidence[station][-1]
            for value in runner.secrets.values:
                if value not in self.secrets:
                    self.secrets.append(value)
            line = {"at": H.now_iso(), "station": self.current, "route": entry["route"], "who": "%s (%s)" % (entry["who"] or "nobody", where),
                    "sent": H.redact(entry["sent"], self.secrets, mask=C.last4), "status": entry["status"],
                    "came_back": H.redact(entry["came_back"], self.secrets, mask=C.last4), "headers": None, "elapsed_ms": entry["elapsed_ms"],
                    "expected": entry["expected"], "result": entry["result"]}
            self.steps.setdefault(self.current, []).append(line)
            self.folder.record(**line)

        def note(station: str, text: str) -> None:
            original_note(station, text)
            self.notes.setdefault(self.current, []).append("%s: %s" % (where, text))

        def finding(station: str, probe: str, sent: Any, answer: Any, expected: str, said: str) -> Any:
            found = original_finding(station, probe, sent, answer, expected, said)
            self.notes.setdefault(self.current, []).append("a finding of the estate's at %s — %s: %s" % (where, probe, said))
            return found

        runner.step, runner.note, runner.finding = step, note, finding  # type: ignore[assignment]

    def estate_people(self) -> Tuple[E.Runner, E.Person, E.Person]:
        """
        Harness Holdings' people, from where they already are (Spec T23 §5): each of the census — the founder who creates the payee, the roster
        who press it to its quorum, the clerk who authors the payment, the signers — signed in with the passkey the estate harness stored under
        ~/.aer360-harness/harness-holdings/ (the newest file per person), on the estate's own base. A founder with no passkey stops S11 with the
        estate harness's own sentence for that absence; a person without one is noted and does not press. Answers the runner, the founder and the clerk.
        """
        estate = self.estate_runner()
        founder = estate.people[A.FOUNDER]
        if founder.passkey is None:
            raise StationStop(NO_ESTATE_FOUNDER_SENTENCE % (E.FOUNDER_NOT_ENROLLED, founder.name, estate.key_path(founder)), outcome=STOPPED)
        for key in A.CENSUS_ORDER:
            person = estate.people[key]
            if person.passkey is None:
                self.note("%s has no passkey stored at %s, so %s does not press for %s this run" % (person.name, estate.key_path(person), person.name, A.ESTATE["company"]))
                continue
            verified, _ = estate.sign_in(person, "S11")
            estate.step("S11", verified, "a session for %s at %s, with the stored passkey" % (person.name, A.ESTATE["company"]),
                        "signed in" if verified.ok else verified.sentence(), {"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<assertion>"}, person.name)
            if not verified.ok:
                if key == A.FOUNDER:
                    raise StationStop("%s's founder could not sign in — POST /v1/auth/login/verify answered %s; nothing was sent" % (A.ESTATE["company"], verified.sentence()), outcome=FAIL)
                self.note("%s could not sign in at %s (%s), so %s does not press this run" % (person.name, A.ESTATE["company"], verified.sentence(), person.name))
        workspace = (founder.session or {}).get("workspace") or {}
        name = str(workspace.get("name") or "")
        if name.strip().lower() != A.ESTATE["company"].lower():
            raise StationStop(ESTATE_NOT_HOLDINGS_SENTENCE % (self.estate_base, name, A.ESTATE["company"]), outcome=FAIL)
        estate.facts["workspace"] = workspace
        return estate, founder, estate.clerk()

    def holdings_pays_the_wallet(self, address: str, facts: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], int, str]:
        """
        The road, in order (Spec T23 §1 to §3). The reads first, which create nothing: Holdings' workspace (its funding wallet, the operating
        account the agent is paid from, and the platform account its gas stands on), the admin credential, Holdings' USDC — and where Holdings is
        short of TRADE_RAW, the Treasury brought in and its USDC read, so a Treasury that cannot cover the shortfall stops the run with T14's
        sentence before anything is made. Then the payee: this run's agent's wallet, named `<label> (agent wallet)`, created, promoted and
        pressed to the roster's quorum exactly as S6 does Northwind, the register the judge; a refusal is the estate's, in its sentence. Then
        the money: the Treasury pays Holdings the shortfall first, where there is one (T14 §2); then Holdings pays the wallet TRADE_RAW and no
        more, through T14's `pay` — the review (gas credited through the admin road where the gas gate refuses, and the review asked again),
        the creation, the submit, the signers' presses in the spec's order while the run waits, the execute by its author, the register read
        until the instruction is terminal, the wallet's USDC before and after — judged on the trail as T14 judges a landing. Then the wait.
        """
        chain = ET.PAYEE_CHAIN
        estate, founder, clerk = self.estate_people()
        workspace = estate.request(clerk, "GET", "/v1/workspace", None, "S11")
        estate.step("S11", workspace, "%s's workspace: its funding wallet — the operating account the agent's wallet is paid from — and the platform account its gas "
                    "stands on (workspace.aapAccountId, Spec 104 §1)" % A.ESTATE["company"], "answered" if workspace.ok else workspace.sentence(), None, clerk.name)
        view = workspace.json if isinstance(workspace.json, dict) else {}
        funding = view.get("fundingWallet") if isinstance(view.get("fundingWallet"), dict) and view["fundingWallet"].get("address") else None
        if funding is None:
            raise StationStop(NO_ESTATE_WALLET_SENTENCE % (view.get("fundingWalletAbsence") or workspace.sentence()), outcome=STOPPED)
        if isinstance(view.get("workspace"), dict):
            estate.facts["workspace"] = view  # the whole answer, as the estate's S5 and S7 keep it: the platform account rides in workspace.aapAccountId
        estate.facts["funding_wallet"] = funding
        admin = estate.read_admin_env("S11")
        estate.facts["money"] = {"treasury": {"credited": 0, "payment": None}, "holdings": {"credited": 0}, "payments": []}
        # 1. the money before: Holdings' USDC; and where Holdings is short, the Treasury's (T14 §2) — reads, which create nothing
        h_usdc, h_words, _ = estate.read_usdc_balance(estate, clerk, "S11", "Harness Holdings")
        if h_usdc is None:
            raise StationStop("%s; nothing was sent" % h_words, outcome=FAIL)
        shortfall = max(0, TRADE_RAW - h_usdc)
        treasury: Optional[Dict[str, Any]] = None
        t: Optional[E.Runner] = None
        t_founder: Optional[E.Person] = None
        if shortfall:
            treasury = estate.bring_in_the_treasury("S11")
            t = estate.treasury
            assert t is not None
            t_founder = t.founder()
            t_usdc, _, _ = estate.read_usdc_balance(t, t_founder, "S11", ET.TREASURY["short"])
            needs = "the trade needs %s and Harness Holdings holds %s" % (ET.usdc_dollars(TRADE_RAW), ET.usdc_dollars(h_usdc))
            if t_usdc is None or t_usdc < shortfall:
                # T14's sentences, word for word: the one place on this road that names a thing only a person can do — a treasury top-up, never a per-run act
                holds = ET.usdc_dollars(t_usdc) if t_usdc is not None else "a balance the estate could not say"
                if treasury.get("born_this_run"):
                    raise StationStop("%s — %s (%s; the Treasury holds %s); nothing was sent" % (
                        E.TREASURY_NOT_FUNDED, ET.FUND_TREASURY_SENTENCE % (treasury.get("address"), chain), needs, holds), outcome=STOPPED)
                raise StationStop("%s — %s (%s); nothing was sent" % (
                    E.TREASURY_SHORT, ET.TREASURY_SHORT_SENTENCE % (holds, ET.usdc_dollars(shortfall), treasury.get("address"), chain), needs), outcome=STOPPED)
            money_words = "Harness Holdings holds %s, short of the trade's %s by %s, and %s holds %s" % (
                ET.usdc_dollars(h_usdc), ET.usdc_dollars(TRADE_RAW), ET.usdc_dollars(shortfall), ET.TREASURY["short"], ET.usdc_dollars(t_usdc))
        else:
            money_words = "Harness Holdings holds %s, at or above the trade's %s, so the Treasury was not asked" % (ET.usdc_dollars(h_usdc), ET.usdc_dollars(TRADE_RAW))
        # 2. the payee is the child wallet (§1): exactly as the estate harness's S6 makes Northwind one, and the register is the judge
        name = PAYEE_NAME % self.label
        record, payee_words, whole = R.propose_payee(estate, founder, name, self.label, address, chain, "S11")
        if record is None or not whole:
            raise StationStop(PAYEE_REFUSED_SENTENCE % (address, payee_words), outcome=FAIL)
        R.judge_payee_register(estate, founder, "S11", [record],
                               "the payees register reading whitelisted for %s, by this run's payee id — the judgement is the register's, not the press's (Spec T13 §3)" % name)
        self.state["estate"] = {"payee": name, "payee_id": record.get("payee_id"), "address_id": record.get("address_id"), "chain": chain}
        self.save_state()  # what this run made at the estate is on record the moment it exists
        if record.get("register_status") != "whitelisted":
            raise StationStop(NOT_WHITELISTED_SENTENCE % (record.get("register_status"), name, "; ".join(w for w in (payee_words, record.get("mirror")) if w)), outcome=FAIL)
        payee_said = "the payee %s; the register reads %s" % (payee_words, record.get("register_status"))
        # 3. the shortfall, paid by the Treasury first, through the same road (T14 §2)
        treasury_said = ""
        if shortfall:
            assert t is not None and t_founder is not None and treasury is not None
            paid_t = estate.treasury_pays_the_shortfall(t, t_founder, clerk, shortfall, funding["address"], admin)
            estate.facts["money"]["treasury"]["payment"] = paid_t
            self.facts["estate_sent"].append("%s's payment of %s to Harness Holdings (set %s)" % (ET.TREASURY["short"], ET.usdc_dollars(shortfall), paid_t.get("set_id")))
            if not paid_t["landed"]:
                raise StationStop(TREASURY_PAYMENT_FAILED_SENTENCE % paid_t["said"], outcome=FAIL)
            treasury_said = "; %s paid Harness Holdings (%s) the shortfall of %s first: %s" % (ET.TREASURY["short"], funding["address"], ET.usdc_dollars(shortfall), paid_t["said"])
        # 4. Holdings pays the trade's amount, and no more (§2)

        def more_gas(ceiling: Optional[int]) -> bool:
            credit = estate.credit_gas(estate, "S11", admin, "Harness Holdings", E.Runner.gas_credit_for(ceiling))
            estate.facts["money"]["holdings"]["credited"] += credit["amount_usd_cents"]
            return True

        row = {"payeeAddressId": record["address_id"], "asset": ET.PAYMENT_ASSET, "chain": chain, "amountMinor": str(TRADE_RAW), "invoiceRef": "PF-%s" % self.run_id}
        signers = [estate.people[k] for k in E.SIGNERS_IN_ORDER]
        expect_words = "Harness Holdings pays %s of %s to %s, the agent's wallet, and no more — the trade's amount (Spec T23 §2)" % (ET.usdc_dollars(TRADE_RAW), ET.PAYMENT_ASSET, address)
        paid = estate.pay(estate, clerk, self.label, row, TRADE_RAW, address, signers, expect_words, lambda: self.agent_wallet_usdc(facts), station="S11", more_gas=more_gas)
        self.state["estate"].update(set_id=paid.get("set_id"), instruction_id=paid.get("instruction_id"))
        self.save_state()
        if not paid.get("set_id"):
            raise StationStop(FUNDING_FAILED_SENTENCE % paid["said"], outcome=FAIL)
        self.facts["estate_sent"].append("Harness Holdings' payment of %s to the agent's wallet (set %s)" % (ET.usdc_dollars(TRADE_RAW), paid["set_id"]))
        self.note(FUNDING_SENTENCE % (address, chain, paid["set_id"], self.run_id))
        trail = estate.read_trail(estate, founder, "S11", "the trail: the %s row for the funding payment — userOpHash, the handleOps txHash, gasDebitUsdCents and gasDebit (Spec 104 §2, §5)" % ET.INSTRUCTION_CONFIRMED)
        estate.judge_landing(paid, trail)
        if paid.get("executed") is None or isinstance(paid.get("executed"), str):
            raise StationStop(FUNDING_FAILED_SENTENCE % paid["said"], outcome=FAIL)  # refused at the review or the creation, not submitted, waiting with nobody left to sign, or the execute refused: in the words it stopped with
        usdc, weth, held = self.until_funded(estate, founder, clerk, paid, address, facts)
        self.facts["funded"] = {k: paid.get(k) for k in ("set_id", "instruction_id", "status", "set_status", "tx_hash", "user_op_hash", "gas_debit", "gas_debit_cents", "landed",
                                                           "balance_before", "balance_after")}
        self.facts["funded"].update(payee_id=record.get("payee_id"), address_id=record.get("address_id"), holdings_before=h_usdc, shortfall=shortfall,
                                    treasury_payment=(estate.facts["money"]["treasury"].get("payment") or {}).get("set_id"), gas_credited=estate.facts["money"]["holdings"]["credited"])
        return usdc, weth, held, "%s; %s%s; Harness Holdings paid the agent's wallet %s: %s" % (payee_said, money_words, treasury_said, ET.usdc_dollars(TRADE_RAW), paid["said"])

    @staticmethod
    def landing_words(paid: Dict[str, Any]) -> str:
        """The payment's state in the estate's words: the instruction, its failure reason where it has one, the run, the handleOps hash where it is named."""
        return "the instruction %s%s, the run %s%s" % (paid.get("status") or "not read", (" (%s)" % paid["failure_reason"]) if paid.get("failure_reason") else "",
                                                       paid.get("set_status") or "not read", (", handleOps %s" % paid["tx_hash"]) if paid.get("tx_hash") else "")

    def read_the_set_again(self, estate: E.Runner, clerk: E.Person, paid: Dict[str, Any]) -> None:
        """One read of the run as the register shows it (GET /v1/sets/{id}), the payment's record updated from it: the run's status, the instruction's, its txHash, its failure reason."""
        answer = estate.request(clerk, "GET", "/v1/sets/%s" % paid["set_id"], None, "S11")
        estate.step("S11", answer, "the run as the register shows it: the instruction confirmed (the platform reported the operation landed) and the run settled, or not yet",
                    "answered" if answer.ok else answer.sentence(), None, clerk.name)
        if not answer.ok or not isinstance(answer.json, dict):
            return
        set_row = answer.json.get("set") if isinstance(answer.json.get("set"), dict) else {}
        instruction = next((i for i in (set_row.get("instructions") or []) if isinstance(i, dict)), None) or {}
        paid.update(view=answer.json, set_status=set_row.get("status"), status=instruction.get("status"), tx_hash=instruction.get("txHash") or paid.get("tx_hash"),
                    failure_reason=instruction.get("failureReason"), gas_value=instruction.get("gasValue"))

    def until_funded(self, estate: E.Runner, founder: E.Person, clerk: E.Person, paid: Dict[str, Any], address: str, facts: Dict[str, Any]
                     ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], int]:
        """
        The loop that once waited for a person waits for the harness's own money (Spec T23 §3): the set settled and the instruction confirmed —
        read again from the estate's register, every interval, while they are not — and the child wallet's USDC, read through wallet.get_balances,
        at or above TRADE_RAW; --funds-wait bounds the wait. Landed, the trade goes on; a payment the estate reports failed or rejected stops S11 in
        the estate's words; one not landed within the wait stops S11 naming the set and the state the register last gave it.
        """
        set_id = str(paid.get("set_id"))
        deadline_at = self.clock() + self.deadline
        while True:
            status, set_status = str(paid.get("status") or ""), str(paid.get("set_status") or "")
            terminal = set_status in ET.SET_TERMINAL_STATES and status in ET.INSTRUCTION_TERMINAL_STATES
            if status in ("failed", "rejected") or (terminal and status != ET.INSTRUCTION_CONFIRMED_STATE):
                raise StationStop(FUNDING_FAILED_SENTENCE % self.landing_words(paid), outcome=FAIL)
            balances, usdc, weth, held = self.read_agent_balances(facts)
            if set_status == ET.SET_SETTLED and status == ET.INSTRUCTION_CONFIRMED_STATE and held is not None and held >= TRADE_RAW:
                if not paid.get("landed"):
                    # the register says it landed after the payment road's own bounded reads had given up: judged again, on the trail, as T14 judges a
                    # landing — the earlier verdict's words set aside first, since judge_landing carries a record's standing failure into its count
                    paid.update(balance_after=held, failure=None, spoken=[w for w in (paid.get("spoken") or []) if not str(w).startswith("not landed — ")])
                    trail = estate.read_trail(estate, founder, "S11", "the trail, read again now the register says the run settled: the %s row for the funding payment" % ET.INSTRUCTION_CONFIRMED)
                    estate.judge_landing(paid, trail)
                self.note(FUNDED_SENTENCE % (held, paid.get("tx_hash") or "not named"))
                return usdc, weth, held
            if self.clock() >= deadline_at:
                break
            self.sleep(self.interval)
            if not terminal:
                self.read_the_set_again(estate, clerk, paid)
        raise StationStop(NOT_LANDED_SENTENCE % (address, TRADE["chain"], self.holds_words(held, balances), TRADE_RAW, set_id, int(self.deadline), self.landing_words(paid)), outcome=FAIL)

    def until_landed(self, operation: Dict[str, Any], ticket_id: str) -> Dict[str, Any]:
        """
        The Wallet's own ticket_status, every interval until the operation has landed or ended badly, to the deadline. The Wallet
        names the handleOps transaction the moment it is sent, with the status submitted (useroperation.go), so a hash is not a
        landing: landed is the status landed, or the debit the ticket states once the operation landed.
        """
        deadline_at = self.clock() + self.deadline
        while not landed_word(operation) and str(operation.get("status") or "") not in ("reverted", "expired", "failed"):
            if self.clock() >= deadline_at:
                break
            self.sleep(self.interval)
            self.expect("the ticket's state: the operation's userOpHash, its handleOps transaction once it landed, the debit")
            args, _ = H.arguments_for(self.mcp.schema_of("wallet.ticket_status"), {}, {"ticket_id": ticket_id})
            answer = self.mcp.call("wallet.ticket_status", args, self.current)
            data = answer.data if isinstance(answer.data, dict) else {}
            ticket = H.find_key(data, ["ticket"], dict) or data
            merged = dict(operation)
            merged.pop("success", None)  # the submit's flag predates the landing; only a newer reading may say it
            for key in ("user_op_hash", "handle_ops_tx_hash", "reserved_usd", "debited_usd", "delegation_tx_hash", "status", "fate", "success"):
                if ticket.get(key) not in (None, ""):
                    merged[key] = ticket[key]
            operation = merged
        return operation

    # -- S12 The reader -------------------------------------------------------------------------------------
    def landing(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        The landed swap's receipt and its UserOperationEvent: S11's; or, where the Wallet told this run's S11 that the operation
        landed and the chain did not answer S11's read (an RPC that refused, or lagged past the deadline), read again by the hash
        the Wallet named; or — on a run resumed past S11 — read again by the hashes run.json keeps, with the readings S11 took
        before the trade. Only this run's own facts are read for the first two: a trade of an earlier run never stands in.
        """
        if self.facts.get("receipt_tx") and self.facts.get("event"):
            return self.facts["receipt_tx"], self.facts["event"]
        s11 = self.outcome_of("S11")
        if s11 is not None and s11.outcome != SKIPPED:
            operation = self.facts.get("operation") or {}
            handle_ops = str(operation.get("handle_ops_tx_hash") or "").lower()
            user_op_hash = str(operation.get("user_op_hash") or "").lower()
            if self.facts.get("receipt_tx") or not landed_word(operation) or not H.HEX64.fullmatch(handle_ops) or not user_op_hash:
                raise StationStop(NO_LANDING, outcome=NOT_RUN)  # S11 read the receipt and judged it, or no landing was ever said
            self.expect("the handleOps receipt S11 could not read, read again by the hash the Wallet named")
            receipt = self.receipt_of(handle_ops)
            event = next((e for e in user_operation_events(receipt) if e["user_op_hash"] == user_op_hash), None) if isinstance(receipt, dict) else None
            if event is None:
                raise StationStop("the Wallet says the operation %s landed in the handleOps transaction %s, and %s %s" % (
                    user_op_hash, handle_ops, self.chain.host, "names no receipt for it" if not isinstance(receipt, dict)
                    else "names a receipt carrying no UserOperationEvent for it"), outcome=FAIL)
            self.note("S11 could not read the handleOps receipt; it is read here, by the hash the Wallet named")
            self.facts.update(receipt_tx=receipt, event=event)
            return receipt, event
        if s11 is None:
            raise StationStop(NO_LANDING, outcome=NOT_RUN)
        traded = self.state.get("traded") if isinstance(self.state.get("traded"), dict) else {}
        handle_ops, user_op_hash = traded.get("handle_ops_tx_hash"), traded.get("user_op_hash")
        if not handle_ops or not user_op_hash:
            raise StationStop("S11 was passed over by --from %s, and run.json records no landed trade to read" % self.start_at, outcome=NOT_RUN)
        self.expect("the landed trade's handleOps receipt, read again by the hash run.json keeps")
        receipt = self.receipt_of(handle_ops)
        event = next((e for e in user_operation_events(receipt) if e["user_op_hash"] == user_op_hash), None) if isinstance(receipt, dict) else None
        if event is None:
            raise StationStop("S11 was passed over by --from %s, and the trade run.json records (handleOps %s) has no receipt carrying its "
                              "UserOperationEvent on %s" % (self.start_at, handle_ops, self.chain.host), outcome=NOT_RUN)
        self.facts.update(receipt_tx=receipt, event=event, ticket_id=traded.get("ticket_id"), before=traded.get("before") or {},
                          gas_before=traded.get("gas_before"),
                          operation={k: traded.get(k) for k in ("user_op_hash", "handle_ops_tx_hash", "delegation_tx_hash", "status", "debited_usd", "reserved_usd")})
        return receipt, event

    def station_s12(self) -> Outcome:
        receipt, event = self.landing()
        self.session()  # the Wallet's reads below; a run resumed past S8 opens the session here
        wallet = self.facts.get("wallet") or {}
        before = self.facts.get("before") or {}
        operation = self.facts.get("operation") or {}
        address = str(wallet.get("address") or "").lower()
        problems: List[str] = []
        lines: List[str] = []
        # 1. the swap on chain: the coin sold left the wallet, the coin bought arrived
        transfers = H.transfers_in(receipt)
        usdc_token = str(before.get("usdc_contract") or "").lower()
        weth_token = str(before.get("weth_contract") or "").lower()
        sold = sum(t["amount"] for t in transfers if t["from"].lower() == address and (not usdc_token or t["token"].lower() == usdc_token))
        bought = sum(t["amount"] for t in transfers if t["to"].lower() == address and (not weth_token or t["token"].lower() == weth_token))
        if sold <= 0:
            problems.append("the receipt carries no transfer of %s out of the wallet" % TRADE["asset"])
        if bought <= 0:
            problems.append("the receipt carries no transfer of %s into the wallet" % TRADE["to_asset"])
        lines.append("on chain: %s %s left the wallet and %s %s arrived (%d transfer(s) in the receipt)" % (
            H.format_units(sold, T.DECIMALS[TRADE["asset"]]), TRADE["asset"], H.format_units(bought, T.DECIMALS[TRADE["to_asset"]]), TRADE["to_asset"], len(transfers)))
        if sold and sold != TRADE_RAW:
            self.note("the chain says %d minor units of %s left the wallet; the trade was for %d" % (sold, TRADE["asset"], TRADE_RAW))
        # 2. the gas trail: the debit, judged in dollars against the chain at the platform's ten percent
        self.expect("the ticket's debit, read once more: debited_usd")
        ticket = self.read_ticket()
        debited = cents_of(ticket.get("debited_usd") or operation.get("debited_usd"))
        self.expect("200: the gas account read live, after the trade")
        gas_answer, gas = self.call("GET", GAS_ACCOUNT_ROUTE)
        after_gas = ((gas or {}).get("available") or {}).get("cents") if isinstance(gas, dict) and isinstance(gas.get("available"), dict) else None
        before_gas = self.facts.get("gas_before")
        operations = [("the swap", receipt)]
        delegation = str(ticket.get("delegation_tx_hash") or operation.get("delegation_tx_hash") or "").lower()
        if H.HEX64.fullmatch(delegation or ""):
            self.expect("the delegation's receipt: status 0x1 (the key delegated by the first operation, an operation of this walk too)")
            delegated = self.receipt_of(delegation)
            if isinstance(delegated, dict):
                operations.append(("the delegation", delegated))
            else:
                problems.append("the delegation %s has no receipt on %s" % (delegation, self.rpc_url))
        self.expect("Chainlink's ETH/USD on %s at the landing block: latestRoundData and decimals" % TRADE["chain"])
        block = H.hex_quantity(receipt.get("blockNumber"))
        price = self.eth_price(block)
        bands: List[Tuple[str, int, int, int]] = []
        for label, row in operations:
            wei = (H.hex_quantity(row.get("gasUsed")) or 0) * (H.hex_quantity(row.get("effectiveGasPrice")) or 0)
            if label == "the swap" and isinstance(event.get("actual_gas_cost"), int):
                # The platform's own rule (internal/gas/settle.go): where the EntryPoint's event states what the operation cost
                # the deposit, the greater of that and the receipt's gasUsed × effectiveGasPrice is the gas.
                wei = max(wei, event["actual_gas_cost"])
            low, high = debit_band(wei, price) if price else (0, 0)
            bands.append((label, wei, low, high))
        if price is None:
            problems.append("the price of ETH could not be read from %s, so the debit's ten percent could not be judged — %s"
                            % (ETH_USD_FEED[TRADE["chain"]], self.facts.get("price_unread") or "the feed answered no price"))
        elif debited is None:
            problems.append("the Wallet states no debited_usd for the operation (%s)" % short_json(ticket, 300))
        else:
            label, wei, low, high = bands[0]
            if not low <= debited <= high:
                problems.append("the debit of %s is outside %s to %s: gas of %d wei plus the platform's ten percent (at least a cent), at US$%s per ether ± %d bps"
                                % (T.format_usd_cents(debited), T.format_usd_cents(low), T.format_usd_cents(high), wei, H.price_words(price // 10 ** 6), PRICE_BAND_BPS))
            lines.append("the debit: %s for %d wei of gas at US$%s per ether (Chainlink at block %s), within %s to %s for gas plus the 10%% charge"
                         % (T.format_usd_cents(debited), wei, H.price_words(price // 10 ** 6), block, T.format_usd_cents(low), T.format_usd_cents(high)))
        # 3. the balances reconcile: the gas account fell by the debits; the coins moved by what the chain says moved
        if before_gas is None or after_gas is None:
            problems.append("the gas account was not read both before and after (before %s, after %s)" % (before_gas, after_gas))
        elif debited is not None:
            fall = before_gas - after_gas
            others_low = sum(b[2] for b in bands[1:])
            others_high = sum(b[3] for b in bands[1:])
            if not debited + others_low <= fall <= debited + others_high:
                problems.append("the gas account fell by %s (%s to %s), and the debits come to %s%s" % (
                    T.format_usd_cents(fall), T.format_usd_cents(before_gas), T.format_usd_cents(after_gas), T.format_usd_cents(debited),
                    (" and %s to %s for the delegation" % (T.format_usd_cents(others_low), T.format_usd_cents(others_high))) if bands[1:] else ""))
            else:
                lines.append("the gas account fell by %s, %s to %s, which is the debit%s" % (
                    T.format_usd_cents(fall), T.format_usd_cents(before_gas), T.format_usd_cents(after_gas), " and the delegation's" if bands[1:] else ""))
        self.expect("the wallet's balances after the trade: USDC fallen and WETH risen by exactly what the chain moved")
        args, _ = H.arguments_for(self.mcp.schema_of("wallet.get_balances"), {}, {"wallet_id": wallet.get("id")})
        balances = self.mcp.call("wallet.get_balances", args, "S12")
        usdc_after = raw_of(balance_row(balances.data, TRADE["chain"], TRADE["asset"]))
        weth_after = raw_of(balance_row(balances.data, TRADE["chain"], TRADE["to_asset"]))
        if usdc_after is None or before.get("usdc") is None or before["usdc"] - usdc_after != sold:
            problems.append("USDC went from %s to %s minor units, and the chain moved %d out" % (before.get("usdc"), usdc_after, sold))
        if weth_after is None or (before.get("weth") or 0) + bought != weth_after:
            problems.append("WETH went from %s to %s, and the chain moved %d in" % (before.get("weth"), weth_after, bought))
        if not problems:
            lines.append("the balances reconcile: USDC %s → %s, WETH %s → %s minor units" % (before.get("usdc"), usdc_after, before.get("weth") or 0, weth_after))
        if problems:
            raise StationStop("; ".join(problems + lines), outcome=FAIL)
        return Outcome("S12", PASS, "the reader: %s" % "; ".join(lines))

    def receipt_of(self, tx_hash: str, wait: bool = False) -> Optional[Dict[str, Any]]:
        """
        The chain's receipt. A public RPC may lag the Wallet's word by a block or more: asked up to three times an interval
        apart, or — `wait`, where the Wallet has said the operation landed — every interval to the deadline.
        """
        deadline_at = self.clock() + self.deadline
        attempt = 0
        while True:
            receipt = self.chain.receipt(tx_hash)
            if isinstance(receipt, dict):
                return receipt
            attempt += 1
            if (not wait and attempt >= 3) or (wait and self.clock() >= deadline_at):
                return None
            self.sleep(self.interval)

    # -- S12a The commission check ------------------------------------------------------------------------
    def station_s12a(self) -> Outcome:
        """
        The trading fee, confirmed on chain: the swap's ERC-20 Transfer logs carry a leg of FEE_BPS of the trade's output to the
        fee address, and the fee address's own incoming Transfer logs at the landing block carry the same leg, in the same
        transaction — the chain's word, never the calldata alone. The rate and the address are tables.py's, read here and not
        declared, and only this harness's terminal and report show them, the address shortened as the corridor prints it.
        """
        if chain_family(TRADE["chain"]) == "solana":
            return self.commission_on_solana()
        receipt, _ = self.landing()
        wallet = str((self.facts.get("wallet") or {}).get("address") or "")
        fee_address = T.address("FEE_ADDRESS")
        transfers = H.transfers_in(receipt)
        check = judge_commission(transfers, wallet, TRADE["contract_address"], fee_address)
        self.facts["commission"] = check
        token = check.get("token")
        symbol, decimals = self.token_words(token)
        figure = lambda units: "%s %s" % (H.format_units(int(units or 0), decimals), symbol)  # noqa: E731
        of_what = "the %s the pool paid the router" if check.get("gross_read_from") == "the pool's transfer to the router" else "the %s delivered plus the fee"
        if not check.get("ok"):
            legs = int(check.get("legs_to_fee_address") or 0)
            if legs > 1:
                raise StationStop("found %d transfers to %s in the swap's Transfer logs, the first of %s, where one of %s (%d bps of %s) was expected"
                                  % (legs, H.short(fee_address), figure(check.get("found")), figure(check.get("expected")), T.FEE_BPS,
                                     of_what % figure(check.get("gross"))), outcome=FAIL)
            if legs and check.get("found") == check.get("expected"):
                raise StationStop("found %s to %s, the %d bps expected, but the router paid out %s of the %s it received (%s to the wallet)" % (
                    figure(check.get("found")), H.short(fee_address), T.FEE_BPS, figure(int(check.get("delivered") or 0) + int(check.get("found") or 0)),
                    figure(check.get("gross")), figure(check.get("delivered"))), outcome=FAIL)
            if legs:
                raise StationStop("found %s to %s, and %d bps of %s is %s expected" % (
                    figure(check.get("found")), H.short(fee_address), T.FEE_BPS, of_what % figure(check.get("gross")), figure(check.get("expected"))),
                    outcome=FAIL)
            if check.get("elsewhere"):
                leg = check["elsewhere"][0]
                raise StationStop("found %s to %s, not to the fee address %s, where %s (%d bps of %s) was expected" % (
                    figure(leg["amount"]), leg["to"], H.short(fee_address), figure(check.get("expected")), T.FEE_BPS, figure(check.get("gross"))),
                    outcome=FAIL)
            raise StationStop("found no transfer to the fee address %s in the swap's Transfer logs, where %s (%d bps of %s) was expected" % (
                H.short(fee_address), figure(check.get("expected")), T.FEE_BPS, figure(check.get("gross"))), outcome=FAIL)
        # The fee address's own incoming Transfer logs at the landing block: the same leg, in the same transaction.
        self.expect("the fee address's incoming ERC-20 Transfer logs at the landing block: the commission's leg among them, in the swap's transaction")
        block = H.hex_quantity(receipt.get("blockNumber"))
        handle_ops = str(receipt.get("transactionHash") or (self.state.get("traded") or {}).get("handle_ops_tx_hash") or "").lower()
        confirmed = ""
        try:
            logs = self.chain.logs(block, [H.TRANSFER_TOPIC, None, H.pad_topic(fee_address)], to_block=hex(block)) if block is not None else []
        except (H.HarnessError, H.Unreachable) as err:
            self.note("the fee address's incoming Transfer logs could not be read (%s); the swap's own receipt carries the leg" % err)
        else:
            mine = [log for log in logs if str(log.get("transactionHash") or "").lower() == handle_ops
                    and str(log.get("address") or "").lower() == str(token).lower() and int(str(log.get("data") or "0x0"), 16) == check["found"]]
            if not mine:
                raise StationStop("the swap's receipt carries %s to %s, and the fee address's own incoming Transfer logs at block %s carry no such "
                                  "leg in that transaction (%d incoming log(s) read)" % (figure(check["found"]), H.short(fee_address), block, len(logs)),
                                  outcome=FAIL)
            confirmed = "; the fee address's own incoming Transfer logs at block %s carry it in the swap's transaction" % block
        return Outcome("S12a", PASS, "commission %s to %s (%d bps) — %d bps of %s, read from the ERC-20 Transfer logs of %s%s" % (
            figure(check["found"]), H.short(fee_address), T.FEE_BPS, T.FEE_BPS, of_what % figure(check["gross"]),
            handle_ops or "the swap's transaction", confirmed))

    def commission_on_solana(self) -> Outcome:
        """
        On Solana the commission rides in an SPL transfer, read from the transaction's own token balances (spl_transfers_in) and
        judged by the same fee_check, against the Solana fee address tables.py pins. It pins none today, and nothing is invented.
        """
        pinned = T.PINNED.get(SOLANA_FEE_KEY)
        if pinned is None:
            raise StationStop(NO_SOLANA_FEE_SENTENCE % (SOLANA_FEE_KEY, TRADE["chain"]))
        transaction = self.facts.get("solana_transaction")
        self.need(transaction, NO_LANDING)
        wallet = str((self.facts.get("wallet") or {}).get("address") or "")
        check = H.fee_check(spl_transfers_in(transaction), pinned.address, wallet, bps=T.FEE_BPS)
        if not check.get("ok"):
            raise StationStop("found %s units to %s, and %s units (%d bps) were expected — %s" % (
                check.get("found") or 0, H.short(pinned.address), check.get("expected"), T.FEE_BPS, check.get("reason")), outcome=FAIL)
        return Outcome("S12a", PASS, "commission %s units of %s to %s (%d bps), read from the SPL token balances of the trade's transaction"
                       % (check["found"], check["token"], H.short(pinned.address), T.FEE_BPS))

    def token_words(self, token: Optional[str]) -> Tuple[str, Optional[int]]:
        """A token's symbol and decimals: the trade's own coins by the contracts the Wallet stated, else asked of the chain."""
        before = self.facts.get("before") or {}
        for asset, contract in ((TRADE["to_asset"], before.get("weth_contract")), (TRADE["asset"], before.get("usdc_contract"))):
            if token and contract and str(contract).lower() == str(token).lower():
                return asset, T.DECIMALS.get(asset)
        if not token:
            return "units", None
        return self.chain.token_symbol(token), self.chain.token_decimals(token)

    def read_ticket(self) -> Dict[str, Any]:
        ticket_id = self.facts.get("ticket_id")
        if not ticket_id or self.mcp is None:
            return {}
        args, _ = H.arguments_for(self.mcp.schema_of("wallet.ticket_status"), {}, {"ticket_id": ticket_id})
        answer = self.mcp.call("wallet.ticket_status", args, self.current)
        data = answer.data if isinstance(answer.data, dict) else {}
        return H.find_key(data, ["ticket"], dict) or data

    def eth_price(self, block: Optional[int]) -> Optional[int]:
        """Chainlink's ETH/USD at the block, in millionths of a cent per ether, or None where the feed could not be read."""
        feed = ETH_USD_FEED[TRADE["chain"]]
        tag = hex(block) if block is not None else "latest"
        try:
            raw = self.chain.call("eth_call", [{"to": feed, "data": LATEST_ROUND_DATA}, tag])
            decimals_raw = self.chain.call("eth_call", [{"to": feed, "data": FEED_DECIMALS}, tag])
            answer = int(str(raw)[2 + 64:2 + 128], 16)  # latestRoundData's second word: the answer
            decimals = int(str(decimals_raw), 16)
        except (H.HarnessError, ValueError, TypeError) as err:
            self.facts["price_unread"] = str(err)  # the RPC's own words, or what could not be read of its answer
            return None
        if answer <= 0:
            return None
        return answer * 100 * 10 ** 6 // 10 ** decimals

    # -- S13 Teardown ---------------------------------------------------------------------------------------
    def station_s13(self) -> Outcome:
        """
        What runs of this harness created, and nothing else: this run's agent — by its id, and by its label where a press's answer
        was lost — and every agent an earlier run left standing on this connector, each with its live connections revoked, halted
        and deleted. The owner is never touched: there is no owner-delete road, and the owner is born once to be reused. What
        could not be removed stays in run.json, said in the connector's words, for the next run's S13.
        """
        targets: List[Dict[str, Any]] = []
        pressed = self.state.get("pressed") if isinstance(self.state.get("pressed"), dict) else {}
        mine = self.facts.get("agent_id") or (self.state.get("agent") or {}).get("id")
        if mine or pressed:
            targets.append({"whose": "this run's", "label": pressed.get("label") or self.label, "id": mine, "earlier": None})
        for entry in self.state.get("earlier") or []:
            if normal_base(str(entry.get("base") or self.base)) != normal_base(self.base):
                continue  # another connector's agent is torn down on its own connector
            targets.append({"whose": "run %s's" % entry.get("run_id"), "label": entry.get("label") or (entry.get("pressed") or {}).get("label"),
                            "id": (entry.get("agent") or {}).get("id"), "earlier": entry})
        if not targets:
            return Outcome("S13", PASS, "teardown: this run created no agent and made no connection, and no earlier run left one standing, so "
                           "nothing was removed; the owner %s stands, as it always does" % (self.customer.customer_id or "(not born)"))
        elsewhere = self.owner_elsewhere()
        if elsewhere:
            return Outcome("S13", FAIL, "teardown: %s; nothing was asked of %s" % (elsewhere, normal_base(self.base)))
        if not self.signed_in:
            if self.customer.passkey is None:
                return Outcome("S13", FAIL, "teardown: %s stands, and the owner holds no passkey at %s to sign in with, so nothing was removed"
                               % ("; ".join("%s agent %s" % (t["whose"], t["id"] or t["label"]) for t in targets), self.customer.passkey_path))
            self.expect("a session for the owner, to remove what this harness created")
            try:
                self.customer.sign_in()
                self.signed_in = True
            except C.ConsentStop as stop:
                return Outcome("S13", FAIL, "teardown: the owner could not sign in to remove what stands — %s; it still stands" % stop.sentence)
        reason = REASON % self.run_id
        self.expect("200 with the owner's account: its agents and its connections, to find what this harness created")
        answer, view = self.call("GET", ACCOUNT_ROUTE)
        read = answer.status == 200 and isinstance(view, dict)
        listed = {str(a.get("id")): a for a in ((view or {}).get("agents") or [])} if read else {}
        problems: List[str] = []
        unresolved: List[Dict[str, Any]] = []
        if not read:
            problems.append("the account could not be read to find this harness's agents — %s" % self.refused("the account", "GET " + ACCOUNT_ROUTE, answer, view).sentence)
        for target in targets:
            ids = [target["id"]] if target["id"] else []
            ids += [aid for aid, a in listed.items() if target["label"] and a.get("name") == target["label"] and aid not in ids]
            if not ids:
                if read:
                    self.removed.append("nothing for %s press of %s: no agent of that name stands on the account" % (target["whose"], target["label"]))
                else:
                    unresolved.append(target)
                continue
            before = len(problems)
            for agent_id in ids:
                self.remove_agent(agent_id, target["whose"], listed if read else None, view if read else None, reason, problems)
            if len(problems) > before:
                unresolved.append(target)
        this_run_done = not any(t["earlier"] is None for t in unresolved) and read
        self.state["torn_down"] = this_run_done
        self.state["removed"] = list(self.removed)
        self.state["torn_down_at"] = H.now_iso()
        self.state["earlier"] = [dict(t["earlier"], why="not removed by run %s: %s" % (self.run_id, "; ".join(problems))) for t in unresolved if t["earlier"]]
        self.save_state()
        if problems:
            return Outcome("S13", FAIL, "teardown: removed %s; NOT removed: %s; the owner %s was not touched" % (
                "; ".join(self.removed) or "nothing", "; ".join(problems), self.customer.customer_id))
        return Outcome("S13", PASS, "teardown: removed %s; the owner %s was not touched and stands for the next run" % (
            "; ".join(self.removed), self.customer.customer_id))

    def remove_agent(self, agent_id: str, whose: str, listed: Optional[Dict[str, Any]], view: Optional[Dict[str, Any]], reason: str,
                     problems: List[str]) -> None:
        """One agent: its live connections revoked (Claude's door), then halted (its pact and credential), then deleted (its seat)."""
        if listed is not None and agent_id not in listed:
            self.removed.append("nothing more for %s agent %s: it is not on the page (deleted already)" % (whose, agent_id))
            return
        live = [row for row in ((view or {}).get("connections") or []) if isinstance(row, dict)
                and str(row.get("agentId")) == str(agent_id) and row.get("state") == "active"]
        for row in live:
            self.expect("200: the connection revoked at the platform, every bearer of it dead")
            revoked, said = self.call("POST", REVOKE_ROUTE % row["id"], {"reason": reason})
            if revoked.status == 200:
                self.removed.append("%s connection %s (revoked)" % (whose, row["id"]))
            else:
                problems.append("%s connection %s was not revoked — %s" % (whose, row["id"], self.refused("the revoke", "POST " + REVOKE_ROUTE % ":id", revoked, said).sentence))
        agent = (listed or {}).get(agent_id) or {}
        if listed is None or agent.get("state") == "active":
            self.expect("200: the agent halted (its pact and its credential revoked, its seat given back)")
            halted, said = self.call("POST", HALT_ROUTE % agent_id, {"reason": reason})
            if halted.status == 200:
                self.removed.append("%s agent %s halted (%s)" % (whose, agent_id, ((said or {}).get("finality") if isinstance(said, dict) else "") or "halted"))
            elif not (listed is None and (C.refusal_of(said) or {}).get("code") == "AGENT_NOT_CONNECTABLE"):
                problems.append("%s agent %s was not halted — %s" % (whose, agent_id, self.refused("the halt", "POST " + HALT_ROUTE % ":id", halted, said).sentence))
        self.expect("200: the agent deleted — off the page and out of the count, its seat free; any dust named")
        deleted, said = self.call("POST", DELETE_ROUTE % agent_id, {"reason": reason})
        if deleted.status == 200:
            self.removed.append("%s agent %s deleted (%s)" % (whose, agent_id, ((said or {}).get("said") if isinstance(said, dict) else "") or "deleted"))
        else:
            problems.append("%s agent %s was not deleted — %s" % (whose, agent_id, self.refused("the delete", "POST " + DELETE_ROUTE % ":id", deleted, said).sentence))

    # -- the report -------------------------------------------------------------------------------------------
    def report(self) -> str:
        lines: List[str] = []
        lines.append("# Pathfinder, the AER Connect owner harness — run %s" % self.run_id)
        lines.append("")
        lines.append("Spec H-PATHFINDER, 2 October 2026. Base URL %s (%s). The owner %s (%s) and its agent %s (%s). The harness is the owner, "
                     "not a judge; a failure below is evidence, not a verdict: what was sent (secrets and passkey material redacted to their last "
                     "four characters), what came back word for word, the route, the expectation and the result. Where a door or the platform "
                     "refused, the server's own sentence comes first, then the lexicon's description in brackets." % (
                         self.base, "a declared test ring" if is_test_ring(self.base, self.rings) else
                         ("not a declared test ring; --i-mean-it was passed" if self.i_mean_it else "not a declared test ring"),
                         self.owner, C.HARNESS_EMAIL % self.owner, self.label, ROLE_ID))
        lines.append("")
        lines.append("## The closing table")
        lines.append("")
        lines.append("| Station | Outcome | Line |")
        lines.append("|---|---|---|")
        for outcome in self.outcomes:
            cells = ["%s %s" % (outcome.station, TITLES.get(outcome.station, "")), outcome.outcome, outcome.line]
            lines.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
        lines.append("")
        lines.append("## What the teardown removed")
        lines.append("")
        if self.removed:
            for item in self.removed:
                lines.append("- %s" % item)
        else:
            lines.append("- nothing: this run created nothing to remove" if not self.state.get("agent") else "- nothing was removed")
        lines.append("- the owner %s was not touched: it is born once and reused, and there is no owner-delete road" % (self.customer.customer_id or "(not born)"))
        for station, title in STATIONS:
            outcome = self.outcome_of(station)
            lines.append("")
            lines.append("## %s — %s" % (station, title))
            lines.append("")
            lines.append("Outcome: **%s**. %s" % (outcome.outcome if outcome else NOT_RUN, outcome.line if outcome else ""))
            for note in self.notes.get(station, []):
                lines.append("")
                lines.append("Note: %s" % note)
            steps = self.steps.get(station, [])
            if steps:
                lines.append("")
                lines.append("### Evidence, call by call")
                lines.extend(self.render_steps(steps))
        if self.steps.get("resume"):
            lines.append("")
            lines.append("## Resume")
            lines.extend(self.render_steps(self.steps["resume"]))
        lines.append("")
        lines.append("## Every call")
        lines.append("")
        lines.append("| At | Station | Route | Status | ms |")
        lines.append("|---|---|---|---|---|")
        for station in ["resume"] + STATION_IDS:
            for step in self.steps.get(station, []):
                lines.append("| %s | %s | %s | %s | %s |" % (step["at"], station, str(step["route"]).replace("|", "\\|"), step["status"], step.get("elapsed_ms")))
        text = "\n".join(lines) + "\n"
        return H.redact(text, self.secrets, mask=C.last4)

    @staticmethod
    def render_steps(steps: List[Dict[str, Any]]) -> List[str]:
        out: List[str] = []
        for index, step in enumerate(steps, 1):
            out.append("")
            out.append("%d. %s%s" % (index, step["route"], (" — %s" % step["who"]) if step.get("who") else ""))
            out.append("   - Expected: %s" % (step.get("expected") or "an answer"))
            out.append("   - Result: %s (HTTP %s, %s ms)" % (step.get("result"), step.get("status"), step.get("elapsed_ms")))
            if step.get("sent") is not None:
                out.append("   - Sent: `%s`" % json.dumps(step["sent"], ensure_ascii=False))
            out.append("   - Came back, verbatim:")
            out.append("")
            out.append("     ```")
            came_back = step.get("came_back")
            text = came_back if isinstance(came_back, str) else json.dumps(came_back, ensure_ascii=False, indent=2)
            for text_line in str(text).splitlines() or [""]:
                out.append("     " + text_line)
            out.append("     ```")
        return out

    def write_report(self) -> str:
        return self.folder.write_report(self.report())


def exit_code_of(outcomes: Sequence[Outcome]) -> int:
    """0 where every station passed (or was passed over by --from); 1 where any failed; 2 where any stopped, was refused or did not run."""
    words = [o.outcome for o in outcomes]
    if FAIL in words:
        return 1
    if any(w in (STOPPED, GUARDED_OUT, NOT_RUN) for w in words):
        return 2
    return 0


# ---------------------------------------------------------------------------
# The dry walk: every station and every call, in order, with no network.
# ---------------------------------------------------------------------------
def _j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def dry_lines(base: str = DEFAULT_BASE, owner: str = DEFAULT_OWNER, store_dir: str = STORE_DIR, start_at: Optional[str] = None,
              i_mean_it: bool = False, test_rings: Sequence[str] = (), funding_wallet: Optional[str] = None, estate_base: str = ESTATE_BASE,
              estate_store: str = ESTATE_STORE_DIR) -> List[str]:
    """Every station and every call the harness would make, in order. Nothing is sent and nothing is written."""
    if not C.TESTER_NAME.match(owner):
        raise C.ConsentStop(C.TESTER_NAME_SENTENCE % (owner, C.HARNESS_EMAIL % "<owner>"))
    base = base.rstrip("/")
    rings = tuple(TEST_RINGS) + tuple(test_rings)
    ring = is_test_ring(base, rings)
    folder = os.path.join(store_dir, owner)  # printed as given; read expanded
    born = os.path.exists(os.path.join(os.path.expanduser(folder), C.PASSKEY_FILE))
    label = AGENT_NAME % (owner, "<run id>")
    lines: List[str] = []
    started = STATION_IDS.index(start_at) if start_at in STATION_IDS else 0

    def station(sid: str, what: str) -> None:
        skipped = STATION_IDS.index(sid) < started
        guard = ""
        if sid in GUARDED:
            guard = (" [guard: %s is a declared test ring; it runs]" % normal_base(base) if ring else
                     " [guard: --i-mean-it; it runs]" if i_mean_it else " [guard: refused — %s]" % guard_sentence(base, sid))
        lines.append("%s %s — %s%s%s" % (sid, TITLES[sid], what, guard, " [skipped: resumed at %s]" % start_at if skipped else ""))

    def call(sid: str, text: str) -> None:
        lines.append("%s — %s" % (sid, text))

    trade_check, _ = H.arguments_for(DRY_SCHEMAS["police.check_action"], TRADE, {"wallet_id": "<wallet UUID>", "role_id": ROLE_ID})
    trade_build, _ = H.arguments_for(DRY_SCHEMAS["wallet.build_transaction"], TRADE, {"wallet_id": "<wallet UUID>", "police_receipt": "<receipt>"})
    trade_build["client_request_id"] = "pathfinder-<run id>"
    trade_submit, _ = H.arguments_for(DRY_SCHEMAS["wallet.submit_transaction"], TRADE, {"wallet_id": "<wallet UUID>", "ticket_id": "<ticket>", "pact_id": "<pact>"})
    trade_submit["agent_id"] = "<agent id>"
    answers = {"perTxUsd": C.BOOK_PER_TX_USD, "dailyUsd": C.BOOK_DAILY_USD, "holdAboveUsd": "<the questionnaire's, else %s>" % C.BOOK_PER_TX_USD,
               "maxTxPerDay": "<the questionnaire's>", "chains": [TRADE["chain"], "<the questionnaire's other chains>"],
               "assets": "<the questionnaire's>", "counterpartiesScope": C.TRADER_LIST_SCOPE,
               "counterparties": ["%s (%s)" % (T.address(k), k) for k in T.TRADER_LIST_B3]}
    if start_at and started:
        lines.append("resume — POST %s {} then POST %s {nonce, issuedAtMs, response} → the owner signed in with the stored passkey; the standing "
                     "agent taken up from %s, or each station that needs it says none stands" % (C.SIGNIN_OPTIONS, C.SIGNIN_VERIFY, os.path.join(folder, RUN_FILE)))
    station("S1", "the owner's software passkey: born once as %s (%s), signed in with ever after" % (C.HARNESS_DISPLAY_NAME % owner, C.HARNESS_EMAIL % owner))
    if born:
        call("S1", "POST %s {} → expect 200: options (challenge, rpId), nonce, issuedAtMs" % C.SIGNIN_OPTIONS)
        call("S1", "POST %s %s → expect 200: the customer %s names and a csrfToken; the sign count saved before the assertion, never resent" % (
            C.SIGNIN_VERIFY, _j({"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<AuthenticationResponseJSON>"}), os.path.join(folder, C.CUSTOMER_FILE)))
    else:
        call("S1", "POST %s %s → expect 200: options (rp.id, challenge, user.id), nonce, issuedAtMs, handle" % (
            C.SIGNUP_OPTIONS, _j({"displayName": C.HARNESS_DISPLAY_NAME % owner, "email": C.HARNESS_EMAIL % owner, "country": C.HARNESS_COUNTRY})))
        call("S1", "[passkey] a new P-256 key (openssl ecparam -genkey -name prime256v1), attestation none, saved to %s mode 600 before the ceremony is sent"
             % os.path.join(folder, C.PASSKEY_FILE))
        call("S1", "POST %s %s → expect 200: the customer and a csrfToken, the session cookie; customer.json written mode 600" % (
            C.SIGNUP_VERIFY, _j({"displayName": C.HARNESS_DISPLAY_NAME % owner, "email": C.HARNESS_EMAIL % owner, "country": C.HARNESS_COUNTRY,
                                 "handle": "<handle>", "nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<RegistrationResponseJSON>"})))
    station("S2", "the account: the owner born once, the seat's standing, the assigned group %s" % EXPECTED_GROUP)
    call("S2", "GET %s → expect 200: customer.id = customer.json's, subscription.standing paid, the assigned signing group %s" % (ACCOUNT_ROUTE, EXPECTED_GROUP))
    station("S3", "this run's own agent, %s (%s), with a fresh passkey" % (label, ROLE_ID))
    call("S3", "GET %s → expect 200: customer.fundingWallet.address, the funding root the connector registered at the owner's first agent and keeps since "
         "(connector Spec 8: registered once) — sent as fundingAddress for an owner that already has one; for an owner the connector lists none for, [file] "
         "the funding wallet from %s (checksummed; refused before any press where it is missing)" % (
             ACCOUNT_ROUTE, funding_wallet or os.path.join(estate_store, C.HARNESS_HOLDINGS, C.FUNDING_WALLET_FILE)))
    call("S3", "GET %s → expect 200: roles (%s with its questionnaire: holdAboveUsd, maxTxPerDay, chains, assets), chainOffer.chains (%s among them)" % (
        AGENTS_NEW_ROUTE, ROLE_ID, TRADE["chain"]))
    call("S3", "POST %s {} → expect 200: options (challenge, rpId) under the purpose approve, nonce, issuedAtMs" % C.STEPUP_OPTIONS)
    call("S3", "POST %s %s → expect 200: agent {id, name, roleId, wallet {id, address, chain, isMock false}, pact}; run.json written mode 600" % (
        AGENTS_ROUTE, _j({"name": label, "roleId": ROLE_ID, "fundingAddress": "<the funding wallet>", "answers": answers,
                          "nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<AuthenticationResponseJSON>"})))
    station("S4", "the questionnaire the server returned, filed as the pact")
    call("S4", "POST %s %s → expect 200: pact {id = S3's, unchanged, state active, document = the answers sent}; the agent and its token untouched" % (POLICY_ROUTE % "<agent id>", _j({"answers": "<the answers S3 sent>"})))
    station("S5", "the child wallet: provisioned, not a mock, the owner's")
    call("S5", "GET %s → expect 200: walletRecord.walletId = S3's wallet; its status, or the connector's sentence for why it cannot be read before S7" % (
        WALLET_RECORD_ROUTE % "<agent id>"))
    station("S6", "gas: the ten-dollar floor, the press, the balance read live")
    call("S6", "POST %s %s → expect 400 ANSWER_INVALID: \"…%s. Nothing was charged.\"" % (GAS_ROUTE, _j({"amountUsd": GAS_BELOW_FLOOR_USD}), GAS_FLOOR_SAID))
    call("S6", "POST %s %s → expect 200: checkout {url, id}, amountCents 1000" % (GAS_ROUTE, _j({"amountUsd": "10"})))
    call("S6", "GET %s → expect 200: read platform, available {cents, said}, minimumTopUpCents 1000" % GAS_ACCOUNT_ROUTE)
    station("S7", "Claude connected to this run's agent: the per-connection credential")
    call("S7", "GET %s, GET %s, POST /register (once; client.json) → expect the metadata, the resource, a client id with PKCE and no secret" % (DISCOVERY_ROUTE, RESOURCE_ROUTE))
    call("S7", "POST %s, POST %s → expect the owner's session" % (C.SIGNIN_OPTIONS, C.SIGNIN_VERIFY))
    call("S7", "GET /authorize?response_type=code&client_id=<client>&redirect_uri=http://127.0.0.1:%d/callback&code_challenge=<S256>&code_challenge_method=S256&state=<state>&scope=%s&resource=%s%s "
         "→ expect 302 to /consent?request=<id>, read without following; no port is bound" % (H.REGISTERED_REDIRECT_PORT, H.ACTING_SCOPE, base, H.MCP_PATH))
    call("S7", "GET /v1/consent/<id>?%s → expect 200 at stage agent, listing %s with no connection" % (C.CONSENT_CONNECT_QUERY, label))
    call("S7", "POST /v1/consent/<id>/finish %s → expect 200: redirectTo with the code and the state sent (Spec 35: the first connection of an agent born on the dashboard)"
         % _j({"agentId": "<agent id>"}))
    call("S7", "POST /token grant_type=authorization_code&code=<code>&code_verifier=<verifier>&redirect_uri=… → expect 200: access and refresh tokens, stored at %s mode 600"
         % os.path.join(folder, "%s.json" % label))
    station("S8", "the catalogue: the fourteen tools")
    call("S8", "MCP initialize %s → expect 200: serverInfo and instructions" % _j({"protocolVersion": H.PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": H.CLIENT_NAME, "version": "1.0.0"}}))
    call("S8", "MCP tools/list {} → expect exactly: %s" % ", ".join(CATALOGUE))
    station("S9", "the agent: the wallet UUID, the pact, the gas balance")
    call("S9", "MCP tools/call %s {} → expect wallet.id (a UUID, S3's), limits.pactId (S4's) and state active, gas_account US$<available>" % H.MY_AGENT_TOOL)
    station("S10", "the judgment: the trade within the mandate, a receipt")
    call("S10", "MCP tools/call police.check_action %s → expect allow with a receipt" % _j(trade_check))
    station("S11", "the agent's wallet funded by Harness Holdings through the estate's own road where it is short, then a real swap, landed, sponsored by the paymaster")
    call("S11", "MCP tools/call wallet.get_balances %s → expect USDC on %s of at least %d minor units; short of it: \"%s\"" % (
        _j({"wallet_id": "<wallet UUID>"}), TRADE["chain"], TRADE_RAW, SHORT_SENTENCE % ("<wallet address>", TRADE["chain"], "<what it holds>", TRADE_RAW)))
    estate_people = os.path.join(estate_store, A.ESTATE["client_id"])
    call("S11", "[estate %s] POST /v1/auth/login/options {}, POST /v1/auth/login/verify {nonce, issuedAtMs, response} as each of %s with the passkey stored under %s "
         "→ expect a session in the workspace %s; the founder's absence: \"%s\"" % (
             estate_base, ", ".join(A.PEOPLE[k].name for k in A.CENSUS_ORDER), estate_people, A.ESTATE["company"],
             NO_ESTATE_FOUNDER_SENTENCE % (E.FOUNDER_NOT_ENROLLED, A.PEOPLE[A.FOUNDER].name, os.path.join(estate_people, "%s.json" % A.FOUNDER))))
    call("S11", "[estate] GET /v1/workspace → expect fundingWallet.address, Harness Holdings' operating account, and workspace.aapAccountId; [file] %s read for the platform's "
         "admin credential (%s, %s), never printed" % (os.path.join(estate_store, ET.ADMIN_ENV_FILE), ET.ADMIN_ENV_URL_KEY, ET.ADMIN_ENV_KEY_KEY))
    call("S11", "[estate] GET %s → expect Harness Holdings' %s on %s; where it is short of %d minor units, Harness Treasury signed in from %s, its %s read, and short: "
         "\"%s\" (T14's sentence; nothing is sent)" % (
             ET.FUNDING_BALANCES_ROUTE, ET.PAYMENT_ASSET, ET.PAYEE_CHAIN, TRADE_RAW, os.path.join(estate_store, ET.TREASURY["client_id"]), ET.PAYMENT_ASSET,
             ET.TREASURY_SHORT_SENTENCE % ("<what it holds>", "US$0.10", "<the Treasury's address>", ET.PAYEE_CHAIN)))
    call("S11", "[estate] POST /v1/payees %s → expect 201 with the payee and its proposed address; POST /v1/payees/addresses/<id>/promote {} → pending_promotion; "
         "POST /v1/payees/addresses/<id>/approve {} as each roster member in T12's order until whitelisted; GET /v1/payees → the register reads whitelisted, by this run's payee id" % (
             _j({"displayName": PAYEE_NAME % label, "defaultAsset": ET.PAYMENT_ASSET, "defaultChain": ET.PAYEE_CHAIN,
                 "addresses": [{"chain": ET.PAYEE_CHAIN, "address": "<wallet address>"}]})))
    call("S11", "[estate] where Harness Holdings is short: Harness Treasury pays Harness Holdings the shortfall first, one one-off set of one payment, approved with the Treasury "
         "founder's passkey, executed, read until settled (T14 §2)")
    call("S11", "[estate] POST /v1/sets/review %s → expect the gates passed; %s at the gas gate → POST %s on the platform's admin road (%s), then the review again" % (
        _j({"pays": [{"payeeAddressId": "<address id>", "asset": ET.PAYMENT_ASSET, "chain": ET.PAYEE_CHAIN, "amountMinor": str(TRADE_RAW), "invoiceRef": "PF-<run id>"}],
            "duplicatesAcknowledged": False}), ET.GAS_SHORTFALL, ET.ADMIN_CREDIT_ROUTE % "<workspace.aapAccountId>", ET.ADMIN_CREDIT_REASON % "<stamp>"))
    call("S11", "[estate] POST /v1/sets {pays, idempotencyKey, reference}, POST /v1/sets/<id>/submit {} → approved, or pending_approval and each of %s presses "
         "POST /v1/approvals/<id>/challenge and /approve while it waits; POST /v1/sets/<id>/execute {} by its author; GET /v1/sets/<id> until the instruction is terminal; "
         "GET %s?limit=%d → the %s row" % (", ".join(A.PEOPLE[k].name for k in E.SIGNERS_IN_ORDER), ET.AUDIT_EXPORT_ROUTE, ET.AUDIT_EXPORT_LIMIT, ET.INSTRUCTION_CONFIRMED))
    call("S11", "note: \"%s\"" % (FUNDING_SENTENCE % ("<wallet address>", ET.PAYEE_CHAIN, "<set id>", "<run id>")))
    call("S11", "MCP tools/call wallet.get_balances %s every %s s, with GET /v1/sets/<id> while the run is not settled, until the set is settled, the instruction confirmed and "
         "USDC on %s is at least %d minor units, deadline %s s (--funds-wait) → note: \"%s\"" % (
             _j({"wallet_id": "<wallet UUID>"}), TRADE_POLL_SECONDS, TRADE["chain"], TRADE_RAW, TRADE_DEADLINE_SECONDS, FUNDED_SENTENCE % (TRADE_RAW, "<hash>")))
    call("S11", "GET %s → expect 200: the gas account before the trade" % GAS_ACCOUNT_ROUTE)
    call("S11", "MCP tools/call wallet.build_transaction %s → expect a ticket and the pact it was built under" % _j(trade_build))
    call("S11", "MCP tools/call wallet.submit_transaction %s → expect the execution: user_op_hash, handle_ops_tx_hash, status, reserved_usd, debited_usd" % _j(trade_submit))
    call("S11", "MCP tools/call wallet.ticket_status %s every %s s until the handleOps transaction is named, deadline %s s" % (
        _j({"ticket_id": "<ticket>"}), TRADE_POLL_SECONDS, TRADE_DEADLINE_SECONDS))
    call("S11", "[read] eth_getTransactionReceipt <handleOps> at %s → expect status 0x1 and the UserOperationEvent: success, sender the wallet, paymaster %s"
         % (T.REHEARSAL_RPC[TRADE["chain"]].url, H.checksum_address(PAYMASTER[TRADE["chain"]])))
    station("S12", "the reader: the swap on chain, the debit with its 10% charge, the balances reconciled")
    call("S12", "[read] the receipt's Transfer logs → expect USDC out of the wallet and WETH into it")
    call("S12", "MCP tools/call wallet.ticket_status %s → expect debited_usd" % _j({"ticket_id": "<ticket>"}))
    call("S12", "GET %s → expect the gas account after: fallen by the debit (and the delegation's, where the operation delegated the key first)" % GAS_ACCOUNT_ROUTE)
    call("S12", "[read] eth_call latestRoundData() and decimals() on %s at the landing block → the debit within gas plus %d bps (at least a cent), at that price ± %d bps"
         % (ETH_USD_FEED[TRADE["chain"]], MARGIN_BPS, PRICE_BAND_BPS))
    call("S12", "MCP tools/call wallet.get_balances %s → expect USDC fallen and WETH risen by exactly what the chain moved" % _j({"wallet_id": "<wallet UUID>"}))
    station("S12a", "the commission: %d bps of the trade's output to the fee address %s, on chain" % (T.FEE_BPS, H.short(T.address("FEE_ADDRESS"))))
    call("S12a", "[read] the handleOps receipt's ERC-20 Transfer logs → expect the pool's %s to the router, %d bps of it to %s, the rest to the wallet "
         "(corridor_harness.fee_check)" % (TRADE["to_asset"], T.FEE_BPS, H.short(T.address("FEE_ADDRESS"))))
    call("S12a", "[read] eth_getLogs Transfer to %s at the landing block → expect the same leg in the swap's transaction; the line: "
         "\"commission <amount> %s to %s (%d bps)\"" % (H.short(T.address("FEE_ADDRESS")), TRADE["to_asset"], H.short(T.address("FEE_ADDRESS")), T.FEE_BPS))
    station("S13", "this run's agent removed; the owner never touched")
    call("S13", "GET %s → the connections and the agents" % ACCOUNT_ROUTE)
    call("S13", "POST %s %s → expect 200: the connection revoked" % (REVOKE_ROUTE % "<connection id>", _j({"reason": REASON % "<run id>"})))
    call("S13", "POST %s %s → expect 200: halted, its pact and credential revoked, its seat back" % (HALT_ROUTE % "<agent id>", _j({"reason": REASON % "<run id>"})))
    call("S13", "POST %s %s → expect 200: deleted, any dust named; run.json marked torn down" % (DELETE_ROUTE % "<agent id>", _j({"reason": REASON % "<run id>"})))
    return lines


# ---------------------------------------------------------------------------
# The command line.
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None, **inject: Any) -> int:
    parser = argparse.ArgumentParser(description="Pathfinder, the AER Connect owner harness: the script is the owner and walks A to Z to a trade (Spec H-PATHFINDER).")
    parser.add_argument("--base", default=DEFAULT_BASE, help="the connector's base URL (default %s, the sandbox)" % DEFAULT_BASE)
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="the owner's name, born once as harness+<name>@aeredium.io (default %s)" % DEFAULT_OWNER)
    parser.add_argument("--dry", action="store_true", help="print every station and every call, without connecting")
    parser.add_argument("--from", dest="start_at", help="resume at a station, for example S8, with the owner's stored passkey and the standing run's agent")
    parser.add_argument("--i-mean-it", dest="i_mean_it", action="store_true", help="let the state-creating stations run on a base that is not a declared test ring")
    parser.add_argument("--test-ring", dest="test_rings", action="append", default=[], metavar="BASE", help="declare a base a test ring (repeatable)")
    parser.add_argument("--store", default=STORE_DIR, help="where the owner's passkey, customer id, tokens and run state are kept (default %s)" % STORE_DIR)
    parser.add_argument("--out", default=RUNS_DIR, help="where the run's folder (report.md, evidence.jsonl) is written (default %s)" % RUNS_DIR)
    parser.add_argument("--funding-wallet", dest="funding_wallet", default=None,
                        help="the owner's funding-wallet file, read only for an owner the connector lists no funding wallet for (default <estate store>/%s/%s)"
                             % (C.HARNESS_HOLDINGS, C.FUNDING_WALLET_FILE))
    parser.add_argument("--estate-base", dest="estate_base", default=ESTATE_BASE,
                        help="the AER 360 estate Harness Holdings lives at, which S11 pays the agent's wallet from (default %s, the estate harness's --base)" % ESTATE_BASE)
    parser.add_argument("--estate-store", dest="estate_store", default=ESTATE_STORE_DIR,
                        help="where the estate harness keeps Harness Holdings' and Harness Treasury's passkeys and admin.env (default %s, its --store)" % ESTATE_STORE_DIR)
    parser.add_argument("--rpc", default=None, help="the %s JSON-RPC endpoint the reader reads (default %s)" % (TRADE["chain"], T.REHEARSAL_RPC[TRADE["chain"]].url))
    parser.add_argument("--funds-wait", dest="funds_wait", type=float, default=TRADE_DEADLINE_SECONDS, metavar="SECONDS",
                        help="how long S11 waits for the payment it made from Harness Holdings to land in the agent's wallet before it stops (default %d s); "
                             "the same deadline bounds the ticket's landing" % int(TRADE_DEADLINE_SECONDS))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.start_at and args.start_at not in STATION_IDS:
        parser.error("--from takes a station: %s" % ", ".join(STATION_IDS))
    if args.dry:
        try:
            lines = dry_lines(args.base, args.owner, args.store, args.start_at, args.i_mean_it, args.test_rings, args.funding_wallet, args.estate_base, args.estate_store)
        except C.ConsentStop as stop:
            print(stop.sentence)
            return 2
        for line in lines:
            print(line)
        print("Dry walk: nothing was sent.")
        return 0
    try:
        if args.funds_wait <= 0:
            print("--funds-wait must be a positive number of seconds")
            return 2
        inject.setdefault("deadline", args.funds_wait)
        inject.setdefault("estate_base", args.estate_base)
        inject.setdefault("estate_store", args.estate_store)
        runner = Pathfinder(args.base, args.owner, args.store, args.out, args.start_at, args.i_mean_it, args.test_rings,
                            args.funding_wallet, args.rpc, **inject)
    except C.ConsentStop as stop:
        print(stop.sentence)
        return 2
    try:
        runner.run()
    except H.HarnessError as err:
        print(str(err))
        return 2
    finally:
        if runner.outcomes:
            path = runner.write_report()
            runner.say("Report: %s" % path)
    return exit_code_of(runner.outcomes)


if __name__ == "__main__":
    sys.exit(main())
