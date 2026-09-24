#!/usr/bin/env python3
"""
THE ESTATE HARNESS: a Python script that walks AER 360 end to end as a founder (Spec T7).

Bear, 19 September 2026: "A Python script that will test AER 360 end to end: building the
policy, creating wallets, creating names for the signatures, creating a whitelist. You decide
the parameters, the money. I want to find out if there are still any bugs, because now we have
very serious people asking to be onboarded, and we need to know where we stand."

Two laws, carried from Spec T1:

  THE HARNESS IS THE FOUNDER, NOT A JUDGE. It speaks to AER 360 exactly as a founder's browser
  does: the same HTTPS routes under /v1, the same passkey, the same interview answered one
  question at a time, the same read-back and confirmation. It holds no admin key, no platform
  key and no rule of its own.

  A FAILURE IS EVIDENCE, NOT A VERDICT. When a station does not come out as expected, the report
  carries what was sent, what came back word for word, which route answered, and where the truth
  can be read. The harness never paraphrases an answer and never guesses at a cause.

Read from the AER 360 code (aeredium/AERAccounts, main after PR #106, commit e651616) rather than
from memory:
  apps/server/src/routes/auth.ts           invite/options, invite/verify, login/options, login/verify, session
  apps/server/src/routes/guards.ts         the session cookie, the x-csrf-token header on mutating routes, the roles
  apps/server/src/routes/onboarding.ts     interviews, answers, readback, confirm/options, confirm, compile, charter
  apps/server/src/routes/invites.ts        POST /v1/invites (viewer, author; principal refused by name), the register
  apps/server/src/routes/approverseats.ts  the seats, grant, take
  apps/server/src/routes/payees.ts         payees, addresses, promote, approve
  apps/server/src/routes/sets.ts           review, sets, submit; routes/approvals.ts: challenge, approve
  apps/server/src/routes/journey.ts        GET /v1/journey; routes/workspace.ts: workspace, readiness
  apps/server/src/services/webauthn.ts     attestation none, user verification required
  apps/server/src/services/session.ts      the cookie aer_accounts_session, assertCsrf
  apps/server/src/services/stepup.ts       the digest-bound challenge, a 120-second freshness window
  apps/server/src/http.ts                  the error body {error: {code, message, detail…}} and the status per code
  packages/shared/src/refusals.ts, money.ts, payeeaddress.ts, journey.ts

Spec T8 (20 September 2026, from the first live run and Bear's rulings of that morning) taught the
harness to expect what the law says. The venue-contract probe expects acceptance: "Unless it is
stipulated explicitly in the questionnaire, it must be accepted" — the questionnaire decides policy,
and a contract is an address. The read-back is compared by content, rendered in the estate's own
spoken forms (services/onboarding.ts, readback(), the `spoken` switch, read at main after PR #108,
commit dff4c9a, where that file is e651616's byte for byte): a list entry's values in the order the
estate stores them, which is jsonb's (db/onboardingschema.ts, `value: jsonb('value')`) — for the
census, name — role — email. A slow call is a fact to report, never a finding. And when a previous
report stands in the working folder, the closing table says what closed since it, what is still
open and what is new.

Spec T10 (20 September 2026, after AER 360 Spec 91, PR #112, deployed to the estate, and the fourth live run,
aer360-harness-2026-09-20-135419.md, where Ben's press after Ada's was counted as Ada's because the two shared
one credential): every person is brought in on their own credential. Spec 91 made an `author` invitation mint
a credential of the person's own; a passkey enrolled before it keeps speaking for the shared credential until
that credential is revoked at the platform, and a seat bound to the shared credential stays bound until it is
re-granted. So after each person signs in with their stored passkey, S4 compares the session's credentialId
with the founder's; where they are equal S4 says so and brings the person in again — the founder mints a new
author invitation for the same name and email, the person redeems it with a NEW software passkey stored beside
the old one (<person>-2-<date>.json, never overwriting it), and their session is the new one. Ada's seat is
granted again where it is enrolled_not_seated or names a credential other than her session's. S10 asserts that
the sessions carry distinct credential ids, none the founder's, and reads the People register's Spec 91 marker
("shares a credential with …") for each person. S6 is Spec T9's, unchanged, and reports what the estate answers.

Spec T11 (21 September 2026, from the run of the same night, aer360-harness-2026-09-21.md, and the estate's catalog at
AER 360 Spec 92, commit cf3be4a, CATALOG_VERSION 14): the answer book learns catalog version 14 and the auditor reads the
new law back. The run stopped at S3 and S5 on the seven questions Spec 92 added (C11A, C11C, C19, WO1, WO2, WO3, WO4); the
book answers them (aer360_answers.py) and states the version it answers, which S3 reports beside what the estate served — the
estate states no catalog version on the roads a browser walks, so an unknown question is reported with the book's version and
the inference that the estate's is later. S10 reads the new law back against the compiled charter: `payeeApproval` (C11A: the
change approvers, the census of four at a quorum of two), `payeeVenueContracts` refused (C19 No), `holder` (WO1: Ben Signatory,
by_person, Officer), `signingTiers.holderAloneUpToCents` 200000 and `twoSignaturesUpToCents` 1000000, and the third party WO2
names as a signer beside WA1's people; against the read-back, the two figures as the book wrote them and never as the written
US$1.00, and C19's door line. S11's venue probe follows the charter: where the compiled policy charter says `refused`, the probe
expects the payee door's own refusal — PAYEE_IS_VENUE_CONTRACT, 422, in the sentence `payeeIsVenueContractSentence` composes —
and reports an acceptance as the finding; an estate whose C19 is Yes, or was never asked, keeps the expectation of 20 September.
S7 keeps its three amounts and says in its expectation column what the tiers would do with each (P1 within the holder's own
figure, P2 two signatures, P3 three); it still cannot run until the workspace has a funding account, and says so.

Spec T13 (22 September 2026, from the run of 23:44 the night before, aer360-harness-2026-09-21-234438.md, against the estate at
AER 360 Spec 98, and from the faucet's mechanism as Bear recorded it the same night): the harness presses for the funding wallet,
funds it from the faucet as the founder would, and reads the payee register back after the count. S5 ends by reading GET
/v1/workspace; where `fundingWalletAbsence` stands it presses for the wallet as Harriet — the options road first, whose challenge the
estate derives from `funding-wallet:<workspace id>:<issuedAtMs>` under the purpose `workspace.funding_wallet` (routes/workspace.ts,
FUNDING_WALLET_PURPOSE; services/stepup.ts, deriveChallenge), then POST /v1/workspace/funding-wallet with issuedAtMs and the passkey's
assertion — reads the workspace again and reports "funding wallet: <address> on <home stack>, key <id>". A refusal is reported in the
estate's words (WALLET_BIRTH_REFUSED carries the gateway's sentence; GATEWAY_UNAVAILABLE is a fault) and S5 fails naming it; a wallet
already born is reported and never pressed for again. Where the wallet's native balance on the AEREDIUM testnet reads below 0.1 SEAR —
eth_getBalance through the chain's public RPC named in the faucet record (aer360_tables.py), because the estate offers a browser no live
balance of its funding wallet — the harness POSTs the address to the faucet once, exactly as the faucet page does, and reports the answer
verbatim; it never asks twice in one run and never invents a balance. S6 judges the register, not the press: GET /v1/payees decides, and
a register that reads `proposed` after the platform counted 2 of 2 fails S6 with the mirror sentence, the truth until AER 360 Spec 100.
S7, with a wallet present, names each refusal verbatim and adds one line saying what the three payments need together — US$18,249.99
of USDC — so Bear can fund the wallet by hand; the harness never mints or moves the asset. S8 reads `transactable True` once the wallet
exists, and the report's summary carries the wallet's address.

Spec T15 (22 September 2026, from the run of 13:50 the same day, aer360-harness-2026-09-22-135010.md, against the estate before AER 360
Spec 99 (and before Spec 100: the register still read proposed), and from Spec 99 as it was built, aeredium/AERAccounts commit 33e039c): the harness has the approvers sign a change of who the
approvers are, and S6 counts Ada. Since T12 the harness presses the roster until the count is met and walks a refusal back once; Ada's
seat on Harness Holdings' whitelist roster is bound to a passkey the harness retired, Spec 95 proposed the move when she redeemed a fresh
invitation, the charter asks two approvers to agree to a change of the approvers (C12), so the platform holds the move as a pending
ceremony and nobody signed it. With Spec 99 the door exists — GET /v1/roster/changes, POST /v1/roster/changes/{pendingTxId}/sign under a
step-up of purpose `roster.change` — and S4 walks through it as the census would: after every person has signed in on their own
credential it reads the roster changes as the founder and, for each change the estate lists as awaiting, signs in turn as each person the
list names as able to sign, with their stored passkey, reading signaturesCollected after each, until the estate reports it applied; then
it re-reads the roster changes and asserts the seat now names the owner's current credential. Each signature is judged: a counted one
reports the numbers; a refusal is judged for Rule 13 the way S10 judges every refusal and reported in the estate's words, never retried.
A change the estate lists as expired is reported and the move is proposed afresh, once; a second expiry fails S4 naming the ceremony.
S6 expects Ada's press counted (1 of 2) and Ben's (2 of 2), stops at the count so Cora is not asked, and a SIGNATURE_NOT_COUNTED for a
person whose seat S4 just moved is a finding, not a note. S10 asserts `roster.seat_rebound` in the audit trail (the accountant's export,
GET /v1/export/audit) for each seat S4 moved, naming every signer, and drops T12's note where there is nothing left to note. A fresh
estate, whose register lists no change, leaves S4 unchanged but for one line.

TWO DISAGREEMENTS CARRIED TO BEAR, NOT SILENTLY RESOLVED. (1) SPEC.md §1 says that for a change listed expired "the harness signs the
seat's owner in once more so Spec 95 proposes it afresh". The estate proposes a move at a re-invitation's redemption, at a seat grant
and at the self-seat, and not at a sign-in: `rebindRosterSeats` is called from routes/auth.ts (invite/verify) and from the two seat roads
in services/approverseats.ts, never from login/verify, and enrolment.ts says in its own words that a sentence telling the person to
"sign in again" would send them to a door that proposes nothing; the estate's own expired sentence names the two roads that do —
"Granting <who>'s seat again in this room, or <who> redeeming a fresh invitation, proposes the move afresh." So the harness takes the
lighter of the two, the founder granting the seat again (POST /v1/approver-seats/grant, which Spec 95 answers by presenting the move),
and says so in the step. (2) The ceremony the live estate holds for Ada's seat was opened on 21 September at Spec 95, before Spec 99
wrote the seat's row (`roster.change_proposed` is written where the awaiting outcome is composed), so the list will show it as "a roster
change this estate did not propose", which the estate offers no press for and the harness does not guess whose seat it moves. It takes
the same road once: the founder grants again each seat the charter names for a person of the harness, so Spec 95 proposes any such move
afresh and records it — the platform's ceremony is content-bound, so a live ceremony is reached again, now recorded, and a lapsed one is
born afresh — then re-reads the list and signs. If Bear would rather the harness only report such a change, the one branch to remove is
named in `sign_the_roster_changes`.

Spec T14 (22 September 2026, amended 22:35 — replacing a text that kept a float wallet's key in a file, which the corridor's law forbids:
Bear, "we are only using threshold signatures. There is no key anywhere to be found" — built 24 September 2026, after AER 360 Spec 104 and
platform Spec 154 went live): the harness pays in cents. Every money answer and expectation of Harness Holdings is scaled by one thousand
(aer360_answers.py: the tiers US$2.00 and US$10.00, the hold US$10.00, the daily US$50.00, the payments US$1.25, US$4.99 and US$12.00),
because the sandbox estate pays on real chains with real USDC. The float is a WORKSPACE, not a file: Harness Treasury, born once by the
harness exactly as Harness Holdings is (its founder's passkey under ~/.aer360-harness/harness-treasury/, its funding wallet a key allocated
on the platform and held in the enclave), whose address Bear funds with USDC once; before the three payments, where Holdings' USDC is below
their sum, the Treasury pays the shortfall to Holdings' address as one payment of one set, approved with the Treasury founder's passkey,
through the estate's own road, and the harness waits for the run to land. Gas is a balance in dollars on the platform's ledger (U3): S7
reads both workspaces' gas accounts from the estate, proves the review's refusal for want of gas in U3's sentence with the figures it read
(S7a), then credits each gas account through the platform's ADMIN credit road with the credential Bear files in ~/.aer360-harness/admin.env
(never in the repository, never printed). S7 is judged on money that moved — the run's status, the userOpHash, the handleOps transaction
hash and the payee's USDC balance before and after, the gas debited beside — and S10 counts the money to the cent. The card road is not
walked by the harness. The order S7 walks, and the signatures the estate asks against those the tiers would, are two disagreements carried
to Bear in S7's own comment.

Runs on the Mac's own Python 3.9.6 with the standard library only: urllib.request, http.cookiejar,
json, hashlib, secrets, base64, struct, subprocess. The one binary it calls is /usr/bin/openssl,
through aer360_passkey.py. Nothing to install; nothing is shipped to any box.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import http.cookiejar
import json
import os
import re
import secrets
import shutil
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aer360_answers as A  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402

# ---------------------------------------------------------------------------
# Constants read from the AER 360 code.
# ---------------------------------------------------------------------------
DEFAULT_BASE = "https://accounts.aeredium.io"
DEMO_BASE = "https://demo.accounts.aeredium.io"
SESSION_COOKIE = "aer_accounts_session"  # services/session.ts SESSION_COOKIE
CSRF_HEADER = "x-csrf-token"  # routes/guards.ts requireMutatingSession
STEPUP_MAX_AGE_SECONDS = 120  # services/stepup.ts STEPUP_MAX_AGE_MS
JOURNEY_STAGE_IDS = [  # packages/shared/src/journey.ts JOURNEY_STAGES, in order
    "policy_interview", "first_wallet_account", "working_the_sandbox", "acceptance_rehearsal",
    "identity_verification", "transit_ceremony", "live",
]
JOURNEY_STAGE_COUNT = len(JOURNEY_STAGE_IDS)
STORE_DIR = os.path.expanduser("~/.aer360-harness")
USER_AGENT = "aer360-harness/1.0 (python-stdlib)"
SLOW_CALL_SECONDS = 2.0  # S12: every call over two seconds is listed
RETRY_AFTER_5XX_SECONDS = 2.0  # S12: a 5xx is retried once after two seconds, both answers kept
HTTP_TIMEOUT_SECONDS = 60.0
# Bear's ruling of 20 September 2026 on S11's venue probe (Spec T8). The questionnaire decides policy and a
# contract is an address; the day the questionnaire gains a stipulation against venue contracts, the
# probe's expectation flips to a refusal. Until then a refusal is the finding, with this ruling quoted.
VENUE_RULING = "Bear, 20 September 2026: unless the questionnaire stipulates otherwise, an address is accepted"
# Spec T11 (21 September 2026): the questionnaire gained the stipulation the same day (AER 360 Spec 92, catalog version 14, C19), and
# Harness Holdings answers it No. The probe reads the compiled policy charter's `payeeVenueContracts` at run time: `refused` expects the
# payee door's own refusal — PAYEE_IS_VENUE_CONTRACT, 422 (packages/shared/src/refusals.ts; http.ts), in the sentence
# `payeeIsVenueContractSentence` composes, naming the venue as it publishes itself and the chain sent (services/payees.ts,
# assertPayeeIsNotVenueContract) — and reports an acceptance as the finding; `accepted`, or a charter that was never asked (null,
# which every reader takes as the founder's default), keeps the expectation of 20 September.
PAYEE_IS_VENUE_CONTRACT = "PAYEE_IS_VENUE_CONTRACT"
PAYEE_IS_VENUE_CONTRACT_STATUS = 422
VENUE_CONTRACT_QUESTION_ID = "C19"  # services/payees.ts VENUE_CONTRACT_QUESTION_ID
# The estate's own names for the venues its closed table knows (packages/shared/src/venues.ts, VENUE_NAMES), and which of them the
# corridor's pinned probe address is. The sentence the door says names the venue by its published name, never its id.
ESTATE_VENUE_NAMES = {"uniswap_v3": "Uniswap v3", "pancakeswap_v3": "PancakeSwap v3"}
CORRIDOR_VENUE_IDS = {"UNISWAP_V3_ETHEREUM": "uniswap_v3"}
# What the estate tells a browser about its catalog version: nothing. routes/onboarding.ts answers an interview's id and state, and
# the page carries none; the interview row's catalogVersion never leaves the server. So S3 reports the book's version beside this.
ESTATE_STATES_NO_CATALOG_VERSION = ("the estate states no catalog version on the roads a browser walks (routes/onboarding.ts answers an "
                                    "interview's id and state, and the page carries none)")
# The two figures WO3 and WO4 arrive written with, as the read-back speaks them (services/onboarding.ts, spokenAnswer, money).
WRITTEN_DOLLAR_SPOKEN = "US$1 and 00 cents."
# C19 answered No: the read-back's own line about the payee door (services/onboarding.ts, VENUE_DOOR_READBACK_QUESTION_ID).
VENUE_DOOR_READBACK_QUESTION_ID = "C19_DOOR"
VENUE_DOOR_READBACK_SENTENCE = "You answered No: such an address will be refused when entered."
# Where an invitation's seconds go (Spec T8): routes/invites.ts mints the invitation, awaits the email's
# dispatch (attemptDispatch), stamps the row, and only then answers 201. A fact to report, not a finding.
INVITATION_SENDS_FIRST = "the invitation road sends the email before it answers, which is where its four seconds go"
# Spec T10: the People register's Spec 91 marker, as the People screen speaks it (packages/shared/src/enrolment.ts,
# sharesCredentialSentence: "shares a credential with <names>; invite them again to give them their own").
SHARES_CREDENTIAL_MARKER = "shares a credential with"
# The report's name in the working folder: aer360-harness-<date>.md, and -<HHMMSS> for a later one the same day.
REPORT_NAME = re.compile(r"^aer360-harness-(\d{4}-\d{2}-\d{2})(?:-(\d{6}))?\.md$")
# Spec T13 (22 September 2026): the funding wallet, as AER 360 Spec 98 built it (aeredium/AERAccounts, commit 56582b8;
# routes/workspace.ts, services/fundingwallet.ts, services/stepup.ts), and the faucet (aer360_tables.py, from the cabinet's faucet
# record). The press is a step-up like the interviews' confirm: the options road answers a challenge the estate derives —
# HMAC(secret, setDigest|credentialId|purpose) with setDigest `funding-wallet:<workspace id>:<issuedAtMs>` — and the press carries
# issuedAtMs and the passkey's assertion over it. The harness reads the workspace before it presses, so a wallet already born is
# reported and FUNDING_WALLET_ALREADY_BORN is never met.
FUNDING_WALLET_OPTIONS_ROUTE = "/v1/workspace/funding-wallet/options"
FUNDING_WALLET_ROUTE = "/v1/workspace/funding-wallet"
FUNDING_WALLET_PURPOSE = "workspace.funding_wallet"  # routes/workspace.ts FUNDING_WALLET_PURPOSE
FUNDING_WALLET_BINDING = "funding-wallet:%s:%s"  # the setDigest half of the binding: the workspace id, then issuedAtMs
NO_FUNDING_WALLET_REASON = "no funding wallet"  # services/fundingwallet.ts NO_FUNDING_WALLET_REASON: the readiness answer's reason
WALLET_BIRTH_REFUSED = "WALLET_BIRTH_REFUSED"  # 502: the gateway answered, and the answer was no — its words travel in detail.gatewaySaid
GATEWAY_UNAVAILABLE = "GATEWAY_UNAVAILABLE"  # 503: not configured, not reached, or reached and not now — a fault, not a judgment
FUNDING_WALLET_ALREADY_BORN = "FUNDING_WALLET_ALREADY_BORN"  # 409: never met by this harness, which reads before it presses
# S6's mirror sentence (Spec T13 §3): the platform counted the quorum and the estate's register still reads proposed — the truth
# until AER 360 Spec 100 fixes the mirror; S6 passes after it, when the register reads whitelisted on the next GET /v1/payees.
MIRROR_DISAGREES = "the platform counted %s of %s and the register reads %s; the estate's mirror disagrees with the platform"
# Spec T15 (22 September 2026): the roster ceremony's door, as AER 360 Spec 99 built it (aeredium/AERAccounts, commit 33e039c). The roads and
# the step-up purpose are pinned in aer360_tables.py; these are the codes the signing pass meets and judges (packages/shared/src/refusals.ts;
# apps/server/src/http.ts for each status). Every sentence travels in the estate's words; none is composed here.
CHANGE_SIGNER_NOT_ON_ROSTER = "CHANGE_SIGNER_NOT_ON_ROSTER"  # 403: the roster's no, naming who may sign, judged before the platform is asked
ROSTER_CHANGE_UNKNOWN = "ROSTER_CHANGE_UNKNOWN"  # 404: the id names nothing signable here — the platform lists none, or this estate did not propose it
APPROVER_ALREADY_SIGNED = "APPROVER_ALREADY_SIGNED"  # 409: the platform's record carries this signer already; refused from the record, never asked twice
SIGNATURE_NOT_COUNTED = "SIGNATURE_NOT_COUNTED"  # 403: the platform did not count the signer; its words travel in detail.platformSaid
PLATFORM_REFUSED = "PLATFORM_REFUSED"  # 502: the platform's own no — a ceremony expired, approved or consumed — in its words (Spec 97)
REPROPOSALS_AT_MOST = 1  # Spec T15 §1: a move whose change is listed expired is proposed afresh once; a second expiry fails S4 naming the ceremony
PROPOSED_AFRESH = "proposed afresh"  # the pass's word for a change it could not sign as listed, whose move the founder's grant proposed again
SEAT_REREAD_ATTEMPTS = 3  # Spec T17 §2: after the count is met S4 re-reads the seat up to three times over a bounded wait, and says "moved" only on a true read
SEAT_REREAD_WAIT_SECONDS = 1.0  # the bounded wait between those re-reads (no-op under the test clock)
# Spec T14 (22 September 2026, amended 22:35; built 24 September 2026): the harness pays in cents, funds Harness Holdings from Harness Treasury —
# a second sandbox workspace whose key lives only in the enclave — credits the gas account through the platform's admin road as the sandbox may,
# proves the gas refusal (S7a) and judges S7 on money that moved. The rows, roads, codes and sentences are pinned in aer360_tables.py, read from
# AER 360 Spec 104 and platform Spec 154; these are the harness's own bounds and the spec's order of signers.
LANDING_READS = 30  # after POST /v1/sets/{id}/execute answers, GET /v1/sets/{id} is read up to this many times while an instruction is not terminal
LANDING_WAIT_SECONDS = 3.0  # the bounded wait between those reads (no-op under the test clock)
TRAIL_PAGES_AT_MOST = 40  # GET /v1/export/audit is followed by its nextCursor up to this many pages of AUDIT_EXPORT_LIMIT rows
SIGNERS_IN_ORDER = ("ben", "cora", "ada", "harriet")  # SPEC.md §4's order for a run that waits: the holder, the clerk, then the approver and the third party

STATIONS: List[Tuple[str, str]] = [
    ("S1", "Enrol"), ("S2", "Journey"), ("S3", "Policy Interview"), ("S4", "People"),
    ("S5", "Wallet account"), ("S6", "Payees"), ("S7", "Payments"), ("S8", "Journey and readiness"),
    ("S9", "The tour"), ("S10", "The auditor"), ("S11", "The attacker"), ("S12", "The optimizer"),
]
STATION_IDS = [s for s, _ in STATIONS]

PASS = "pass"
FAIL = "fail"
SKIPPED = "skipped"
NOT_RUN = "not run"
OUT_OF_SCOPE = "out of scope"

# The sentences a refusal must never be (Rule 13: a refusal is never told as an outage, and a
# bare status code or a generic sentence names nothing). Compared case-insensitively.
GENERIC_REFUSAL_PHRASES = (
    "something went wrong", "try again later", "could not be reached", "internal server error",
    "unauthorized", "forbidden", "bad request", "an error occurred", "unknown error",
)
# The fields whose values are passkey material or secrets, redacted to their last four characters.
REDACTED_FIELDS = {
    "pem", "clientDataJSON", "attestationObject", "authenticatorData", "signature", "userHandle",
    "csrfToken", "token", "sealedToken", "accountKey", "cookie", "set-cookie", "Cookie", "Set-Cookie",
}


class HarnessError(Exception):
    """A fault of the harness or its surroundings, never a judgment about the estate."""


class Unreachable(HarnessError):
    """The network did not answer: connect error, timeout. A fault, not a refusal."""


class StationStop(Exception):
    """A station stops here, with its own sentence; the run continues where the next does not depend on it."""


# ---------------------------------------------------------------------------
# Redaction: secrets and passkey material to their last four characters.
# ---------------------------------------------------------------------------
def last4(value: Any) -> str:
    text = str(value)
    if len(text) <= 4:
        return "…" + text
    return "…" + text[-4:]


class Secrets:
    """Every secret the run has seen, so no evidence line can carry one whole."""

    def __init__(self) -> None:
        self.values: List[str] = []

    def add(self, value: Optional[str]) -> None:
        if isinstance(value, str) and len(value) >= 8 and value not in self.values:
            self.values.append(value)

    def redact_text(self, text: str) -> str:
        out = text
        for value in sorted(self.values, key=len, reverse=True):
            if value in out:
                out = out.replace(value, last4(value))
        return out

    def redact(self, value: Any, key: Optional[str] = None) -> Any:
        if isinstance(value, dict):
            return {k: self.redact(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [self.redact(v, key) for v in value]
        if isinstance(value, str):
            if key in REDACTED_FIELDS:
                return last4(value)
            if key == "url" and "#" in value:
                head, _, token = value.partition("#")
                return "%s#%s" % (head, last4(token))
            return self.redact_text(value)
        return value


def token_of_link(link: str) -> str:
    """The invitation's token is the fragment of the link: <origin>/invite#<token> (routes/invites.ts, invite.ts)."""
    fragment = urllib.parse.urlparse(link.strip()).fragment
    if not fragment:
        raise HarnessError("the invitation link carries no #<token> fragment; the token rides in the fragment of the link")
    return fragment


def names_in_words(names: Sequence[Any]) -> str:
    """`namesInWords` (packages/shared/src/enrolment.ts): "Harriet Founder, Ben Signatory and Cora Clerk"."""
    spoken = [str(n) for n in names]
    if len(spoken) <= 1:
        return spoken[0] if spoken else ""
    return "%s and %s" % (", ".join(spoken[:-1]), spoken[-1])


def shares_credential_sentence(shared_with: Sequence[Any]) -> str:
    """The People screen's one marker sentence (Spec 91, item 4), word for word as `sharesCredentialSentence` composes it."""
    return "%s %s; invite them again to give them their own" % (SHARES_CREDENTIAL_MARKER, names_in_words(shared_with))


def now_ms() -> int:
    return int(time.time() * 1000)


def now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def payee_is_venue_contract_sentence(venue_name: str, chain: str, question_id: str = VENUE_CONTRACT_QUESTION_ID) -> str:
    """`payeeIsVenueContractSentence` (packages/shared/src/refusals.ts, Spec 92), word for word."""
    return ("This address is the contract of %s on %s. Your charter says a payee must be a wallet held by a person or a company "
            "(question %s). Nothing was saved." % (venue_name, chain, question_id))


def venue_law_of(charter: Optional[Dict[str, Any]]) -> str:
    """
    What the compiled policy charter says the payee door does with a venue's contract: 'refused' where `payeeVenueContracts` is
    refused (C19 No), else 'accepted' — a charter that was never asked compiles null, which every reader takes as the founder's
    default (onboardingcompiler.ts, venueContractsOf; Bear, 20 September 2026).
    """
    return "refused" if isinstance(charter, dict) and charter.get("payeeVenueContracts") == "refused" else "accepted"


def venue_law_of_the_book() -> str:
    """The same reading off the answer book's C19, for a dry run and for a run that compiled no policy charter."""
    return "refused" if (A.POLICY_ANSWERS.get("C19") or {}).get("choice") == A.VENUE_NO else "accepted"


def usd(cents: Any) -> str:
    """A figure in cents as Spec T11 writes one: US$2,000.00."""
    whole, frac = divmod(int(cents), 100)
    return "US$%s.%02d" % ("{:,}".format(whole), frac)


def under_the_tiers(amount: str, holder_alone_cents: Optional[str], two_signatures_cents: Optional[str]) -> str:
    """
    What the signing tiers (Spec 92, WO3 and WO4) would do with a payment of `amount` — a plain decimal of USDC, read as dollars,
    because the tiers' figures are US cents and USDC is the dollar-pegged asset the payments are made in (Spec T11 §4): within the
    holder's own figure, two signatures, or three. A wallet held by no one has no first figure; up to its two-signature figure a
    payment is one approver's passkey (onboardingcompiler.ts, the tier rules).
    """
    if two_signatures_cents is None:
        return "under the tiers: no figures compiled for this account"
    cents = int(T.minor_units(amount, 2))
    two = int(two_signatures_cents)
    if holder_alone_cents is not None and cents <= int(holder_alone_cents):
        return "under the tiers: within the holder's own figure (%s), one signature — the holder's" % usd(holder_alone_cents)
    if cents <= two:
        if holder_alone_cents is None:
            return "under the tiers: up to the two-signature figure (%s) of a wallet held by no one, one approver's passkey" % usd(two)
        return "under the tiers: two signatures (above %s, up to %s)" % (usd(holder_alone_cents), usd(two))
    return "under the tiers: three signatures (above %s)" % usd(two)


# ---------------------------------------------------------------------------
# HTTP through urllib, with a cookie jar per person, every call recorded.
# ---------------------------------------------------------------------------
class Answer:
    def __init__(self, method: str, path: str, status: int, headers: Dict[str, str], text: str, elapsed_ms: int):
        self.method = method
        self.path = path
        self.status = status
        self.headers = headers
        self.text = text
        self.elapsed_ms = elapsed_ms
        self._json: Any = None
        self._parsed = False

    @property
    def json(self) -> Any:
        if not self._parsed:
            self._parsed = True
            try:
                self._json = json.loads(self.text) if self.text.strip() else None
            except ValueError:
                self._json = None
        return self._json

    @property
    def refusal(self) -> Optional[Dict[str, Any]]:
        body = self.json
        if isinstance(body, dict) and isinstance(body.get("error"), dict):
            return body["error"]
        return None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def sentence(self) -> str:
        """The estate's own words for what came back: the refusal's code and message, or the status."""
        refusal = self.refusal
        if refusal:
            detail = refusal.get("detail") or {}
            cause = detail.get("cause") if isinstance(detail, dict) else None
            return "%s: %s%s" % (refusal.get("code"), refusal.get("message"), (" (%s)" % cause) if cause else "")
        return "HTTP %d%s" % (self.status, (": " + self.text[:200]) if not self.ok and self.text else "")


class Call:
    """One call, as recorded: who sent what where, what came back, how long it took."""

    def __init__(self, station: str, who: str, method: str, path: str, sent: Any, answer: Answer, at: str,
                 retry_of: Optional["Call"] = None, outside: bool = False):
        self.station = station
        self.who = who
        self.method = method
        self.path = path
        self.sent = sent  # already redacted
        self.status = answer.status
        self.text = answer.text  # redacted at record time
        self.elapsed_ms = answer.elapsed_ms
        self.at = at
        self.retry_of = retry_of
        self.size = len(answer.text.encode("utf-8"))
        # Spec T13: a call to the chain's public RPC or the faucet — not the estate's, so its answer is recorded and measured and
        # never judged as the estate's (the minor-unit law and Rule 13 are the estate's; `path` is the whole URL)
        self.outside = outside

    @property
    def route(self) -> str:
        return "%s %s" % (self.method, self.path)


class _CookieInfo:
    """What http.cookiejar asks of a response: `info().get_all('Set-Cookie', [])`."""

    def __init__(self, headers: Sequence[Tuple[str, str]]):
        self._headers = list(headers)

    def get_all(self, name: str, default: Any = None) -> Any:
        found = [v for k, v in self._headers if k.lower() == name.lower()]
        return found if found else default


class _CookieResponse:
    def __init__(self, headers: Sequence[Tuple[str, str]]):
        self._info = _CookieInfo(headers)

    def info(self) -> _CookieInfo:
        return self._info


Transport = Callable[[urllib.request.Request], Tuple[int, List[Tuple[str, str]], str]]


def urllib_transport(request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return response.status, list(response.headers.items()), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        text = err.read().decode("utf-8", "replace") if err.fp else ""
        return err.code, list((err.headers or {}).items()), text
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as err:
        raise Unreachable("%s %s could not be reached: %s" % (request.get_method(), request.full_url, getattr(err, "reason", err)))


class Person:
    """One person at the estate: a cookie jar of their own, their passkey, their session."""

    def __init__(self, spec: A.Person):
        self.spec = spec
        self.key = spec.key
        self.name = spec.name
        self.email = spec.email
        self.jar = http.cookiejar.CookieJar()
        self.csrf: Optional[str] = None
        self.session: Optional[Dict[str, Any]] = None
        self.passkey: Optional[PK.SoftwarePasskey] = None
        self.key_file: Optional[str] = None  # the file the passkey was loaded from or saved to; a later passkey has a suffixed name (Spec T10)
        self.enrolled_now = False

    @property
    def signed_in(self) -> bool:
        return self.session is not None

    @property
    def credential_id(self) -> Optional[str]:
        return self.session.get("credentialId") if self.session else None

    @property
    def roles(self) -> List[str]:
        return list(self.session.get("roles") or []) if self.session else []

    def adopt(self, session: Dict[str, Any]) -> None:
        self.session = session
        self.csrf = session.get("csrfToken")


# ---------------------------------------------------------------------------
# The runner.
# ---------------------------------------------------------------------------
class Outcome:
    def __init__(self, station: str, outcome: str, line: str):
        self.station = station
        self.outcome = outcome
        self.line = line


class Finding:
    """A finding under S10 or S11: the probe, what was sent, what came back, the expectation, the result."""

    def __init__(self, station: str, probe: str, sent: Any, came_back: str, expected: str, said: str, route: str = ""):
        self.station = station
        self.probe = probe
        self.sent = sent
        self.came_back = came_back
        self.expected = expected
        self.said = said
        self.route = route


class Runner:
    def __init__(self, base: str = DEFAULT_BASE, store_dir: str = STORE_DIR, invite: Optional[str] = None,
                 fresh: bool = False, start_at: Optional[str] = None, out_dir: str = ".", dry: bool = False,
                 transport: Optional[Transport] = None, say: Callable[[str], None] = print,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 openssl: str = PK.OPENSSL, treasury_invite: Optional[str] = None, estate: Optional[Dict[str, str]] = None,
                 admin_env: Optional[str] = None):
        self.base = base.rstrip("/")
        parsed = urllib.parse.urlparse(self.base)
        self.origin = "%s://%s" % (parsed.scheme, parsed.netloc)
        self.store_dir = store_dir
        # Spec T14: the workspace this runner is the founder of — Harness Holdings, or Harness Treasury for the float's own runner (for_treasury)
        self.estate: Dict[str, str] = dict(estate or A.ESTATE)
        self.estate_dir = os.path.join(store_dir, self.estate["client_id"])
        self.treasury_invite = treasury_invite
        self.admin_env_path = admin_env or os.path.join(store_dir, T.ADMIN_ENV_FILE)
        self.treasury: Optional["Runner"] = None
        self.answer_overrides: Dict[str, Dict[str, Dict[str, Any]]] = {}  # this workspace's own answers over the book's (the Treasury's A1, C11, WA1)
        self.who_suffix = ""  # " (Harness Treasury)" on the Treasury's runner, so Every call tells the two workspaces' founders apart
        self.invite = invite
        self.fresh = fresh
        self.start_at = start_at
        self.out_dir = out_dir
        self.dry = dry
        self.transport = transport or urllib_transport
        self.say = say
        self.sleep = sleep
        self.clock = clock
        self.openssl = openssl
        self.secrets = Secrets()
        for link in (invite, treasury_invite):
            if link:
                try:
                    self.secrets.add(token_of_link(link))
                except HarnessError:
                    pass
        self.people: Dict[str, Person] = {key: Person(spec) for key, spec in A.PEOPLE.items()}
        self.calls: List[Call] = []
        self.outcomes: List[Outcome] = []
        self.findings: List[Finding] = []
        self.evidence: Dict[str, List[Dict[str, Any]]] = {s: [] for s in STATION_IDS}
        self.evidence["resume"] = []
        self.notes: Dict[str, List[str]] = {s: [] for s in STATION_IDS}
        self.facts: Dict[str, Any] = {
            "answers": {"policy": [], "wallet_account": []},  # (questionId, value, prompt, kind) as given
            "readback": {}, "charter": {}, "compile": {}, "interview": {}, "interview_state": {},
            "invites_minted": [], "invites_register": None, "seats": None,
            "brought_in_again": [], "seat_regrant": None,  # Spec T10: who was brought in again, and Ada's seat before and after
            "payees": [], "payees_register": None, "sets": {}, "sets_register": None,
            "journey": {}, "readiness": None, "workspace": None, "wallets": None, "charter_standing": None,
            "served_twice": {"policy": [], "wallet_account": []},
            # Spec T13: the funding wallet as GET /v1/workspace answers it, the press, the gas balance read from the chain, and the
            # faucet's one answer per run
            "funding_wallet": None, "funding_wallet_absence": None, "funding_press": None, "gas_balance": None, "faucet": None,
            # Spec T15: the roster changes as GET /v1/roster/changes last answered them, the signing pass's record per change, and each seat S4 moved
            "roster_changes": None, "roster_signing": [], "seats_moved": [],
            # Spec T14: the Treasury as S7 brought it in, the money before and after, S7a, the gas credits, and the USDC contract the estate names
            "treasury": None, "money": {}, "s7a": None, "gas_credits": [], "usdc_token": None,
        }
        self.started_at = now_iso()
        self.last_run_report: Optional[Dict[str, Any]] = None
        self._last_run_looked_for = False
        # The run's own mark, in every idempotency key it sends: the clock to the second and four
        # random hex digits, so two runs a second apart never share a key.
        self.run_stamp = "%s-%s" % (_dt.datetime.now().strftime("%Y%m%d-%H%M%S"), secrets.token_hex(2))

    # -- the store ----------------------------------------------------------------
    def key_path(self, person: Person) -> str:
        """The person's first passkey's file; a passkey they are brought in again with is stored beside it, suffixed (Spec T10)."""
        return os.path.join(self.estate_dir, "%s.json" % person.key)

    def stored_key_paths(self, person: Person) -> List[str]:
        """Every passkey stored for the person at this estate, oldest first: <key>.json, then <key>-2-<date>.json, and so on."""
        return PK.stored_key_paths(self.key_path(person))

    def next_key_path(self, person: Person) -> str:
        """Where a passkey the person is brought in again with is stored: beside the old one, suffixed with its ordinal and the date, never over it."""
        return PK.next_key_path(self.key_path(person), _dt.datetime.now().strftime("%Y-%m-%d"))

    def load_passkeys(self) -> None:
        """Each person signs in with the newest passkey stored for them at this base; an older one is kept and never used to sign (Spec T10)."""
        for person in self.people.values():
            for path in reversed(self.stored_key_paths(person)):
                stored = PK.SoftwarePasskey.load(path, self.openssl)
                if stored is None:
                    continue
                if stored.base and stored.base != self.base:
                    self.say("Note: the passkey stored for %s at %s was enrolled at %s, not %s; it is left alone and not used." % (
                        person.name, path, stored.base, self.base))
                    continue
                person.passkey = stored
                person.key_file = path
                break

    def archive_store(self) -> Optional[str]:
        """--fresh: the estate's key folder is set aside, never deleted, so a second estate is a deliberate act."""
        if not os.path.isdir(self.estate_dir):
            return None
        archived = "%s.%s" % (self.estate_dir, _dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.move(self.estate_dir, archived)
        return archived

    def save_passkey(self, person: Person) -> None:
        if person.passkey is None or self.dry:
            return
        person.passkey.base = self.base
        person.passkey.display_name = person.passkey.display_name or person.name
        person.passkey.created_at = person.passkey.created_at or now_iso()
        path = person.key_file or self.key_path(person)  # the file this passkey came from, or its own suffixed name (Spec T10); never another key's
        person.passkey.save(path)
        person.key_file = path

    # -- the wire -----------------------------------------------------------------
    def request(self, person: Optional[Person], method: str, path: str, body: Any = None, station: str = "",
                csrf: bool = True, headers: Optional[Dict[str, str]] = None, who: Optional[str] = None, retry: bool = True) -> Answer:
        """
        One call as the browser would make it: the person's cookie jar, JSON in and out, the session's
        x-csrf-token on every state-changing request (guards.ts). A 5xx is retried once after two seconds
        and both answers are kept (S12) — except where `retry` is False: a press carrying a passkey assertion
        (Spec T13, the funding wallet) cannot be sent twice, so its 5xx is reported as the estate said it.
        Everything is recorded, redacted.
        """
        url = self.base + path
        sent_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        data: Optional[bytes] = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            sent_headers["Content-Type"] = "application/json"
        if person is not None and csrf and method != "GET" and person.csrf:
            sent_headers[CSRF_HEADER] = person.csrf
        sent_headers.update(headers or {})
        answer = self._send(person, method, url, data, sent_headers, path)
        who_said = who or ((person.name + self.who_suffix) if person else "nobody (no session)")
        call = self.record(station, who_said, method, path, body, answer)
        if retry and 500 <= answer.status < 600:
            self.say("  (%s %s answered %d; retrying once after %d seconds, both answers kept)" % (method, path, answer.status, int(RETRY_AFTER_5XX_SECONDS)))
            self.sleep(RETRY_AFTER_5XX_SECONDS)
            second = self._send(person, method, url, data, sent_headers, path)
            self.record(station, who_said, method, path, body, second, retry_of=call)
            return second
        return answer

    def _send(self, person: Optional[Person], method: str, url: str, data: Optional[bytes],
              headers: Dict[str, str], path: str) -> Answer:
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        if person is not None:
            person.jar.add_cookie_header(request)
        started = self.clock()
        status, answer_headers, text = self.transport(request)
        elapsed = int((self.clock() - started) * 1000)
        if person is not None:
            person.jar.extract_cookies(_CookieResponse(answer_headers), request)
            for name, value in answer_headers:
                if name.lower() == "set-cookie":
                    self.secrets.add(value.split(";", 1)[0].split("=", 1)[-1])
        return Answer(method, path, status, {k: v for k, v in answer_headers}, text, elapsed)

    def request_outside(self, who: str, method: str, url: str, body: Any, station: str, headers: Optional[Dict[str, str]] = None) -> Answer:
        """
        Spec T13: one call to a road that is not the estate's — the chain's public RPC, the faucet — made as the faucet page
        makes it: JSON in and out, no cookie, no CSRF token, and never retried (the faucet is asked once per run). A road that
        cannot be reached is recorded as a fault, status 0 and the fault's words, and never raised: the estate is not the one
        that failed, so no station is judged on it. Spec T14: the platform's admin credit road takes its bearer in `headers`, which
        are never recorded.
        """
        sent_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        data: Optional[bytes] = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            sent_headers["Content-Type"] = "application/json"
        sent_headers.update(headers or {})
        request = urllib.request.Request(url, data=data, method=method, headers=sent_headers)
        started = self.clock()
        try:
            status, answer_headers, text = self.transport(request)
        except Unreachable as err:
            status, answer_headers, text = 0, [], str(err)
        answer = Answer(method, url, status, {k: v for k, v in answer_headers}, text, int((self.clock() - started) * 1000))
        self.record(station, who, method, url, body, answer, outside=True)
        return answer

    def record(self, station: str, who: str, method: str, path: str, body: Any, answer: Answer,
               retry_of: Optional[Call] = None, outside: bool = False) -> Call:
        parsed = answer.json
        if isinstance(parsed, dict):
            for key in ("csrfToken", "token"):
                if isinstance(parsed.get(key), str):
                    self.secrets.add(parsed[key])
            if isinstance(parsed.get("url"), str) and "#" in parsed["url"]:
                self.secrets.add(parsed["url"].split("#", 1)[1])
        redacted_text = self.secrets.redact_text(answer.text) if parsed is None else json.dumps(self.secrets.redact(parsed), ensure_ascii=False)
        redacted_answer = Answer(method, path, answer.status, answer.headers, redacted_text, answer.elapsed_ms)
        call = Call(station, who, method, path, self.secrets.redact(body), redacted_answer, now_iso(), retry_of, outside)
        self.calls.append(call)
        return call

    def step(self, station: str, call_answer: Answer, expected: str, result: str, sent: Any = None, who: str = "") -> None:
        """One evidence entry for the report: the route, what was sent, what came back verbatim, the expectation, the result."""
        self.evidence.setdefault(station, []).append({
            "route": "%s %s" % (call_answer.method, call_answer.path),
            "who": who,
            "sent": self.secrets.redact(sent) if sent is not None else None,
            "status": call_answer.status,
            "came_back": self.secrets.redact_text(call_answer.text) if call_answer.json is None else json.dumps(self.secrets.redact(call_answer.json), ensure_ascii=False, indent=2),
            "expected": expected,
            "result": result,
            "elapsed_ms": call_answer.elapsed_ms,
        })

    def note(self, station: str, text: str) -> None:
        self.notes.setdefault(station, []).append(text)
        self.say("  %s note: %s" % (station, text))

    def finding(self, station: str, probe: str, sent: Any, answer: Optional[Answer], expected: str, said: str) -> Finding:
        came_back = ""
        route = ""
        if answer is not None:
            route = "%s %s" % (answer.method, answer.path)
            came_back = "HTTP %d — %s" % (answer.status, self.secrets.redact_text(answer.text) if answer.json is None
                                            else json.dumps(self.secrets.redact(answer.json), ensure_ascii=False))
        finding = Finding(station, probe, self.secrets.redact(sent), came_back, expected, said, route)
        self.findings.append(finding)
        self.say("%s — %s — %s: %s" % (station, FAIL, probe, said))
        return finding

    # -- the ceremonies -------------------------------------------------------------
    def enrol_by_invite(self, person: Person, link: str, station: str) -> Answer:
        """The invitation road: options, a new software passkey, verify. Ends in a session (auth.ts)."""
        token = token_of_link(link)
        self.secrets.add(token)
        opened = self.request(person, "POST", "/v1/auth/invite/options", {"token": token, "issuedAtMs": now_ms(), "response": {}}, station, csrf=False)
        self.step(station, opened, "200 with options (rp.id, challenge, user.id) and the invitee's displayName",
                  "answered" if opened.ok else opened.sentence(), {"token": token, "issuedAtMs": "<now>", "response": {}}, person.name)
        if not opened.ok or not isinstance(opened.json, dict) or "options" not in opened.json:
            raise StationStop("POST /v1/auth/invite/options answered %s" % opened.sentence())
        options = opened.json["options"]
        issued_at = opened.json.get("issuedAtMs")
        passkey = PK.SoftwarePasskey.create_for(options, self.origin, self.openssl)
        registration = passkey.registration(options, self.origin)
        try:
            PK.verify_registration(registration, str(options.get("challenge")), self.origin, passkey.rp_id)
        except PK.PasskeyRefused as err:
            raise HarnessError("the harness's own registration failed its own check before it was sent: %s" % err)
        body = {"token": token, "issuedAtMs": issued_at, "response": registration}
        verified = self.request(person, "POST", "/v1/auth/invite/verify", body, station, csrf=False)
        self.step(station, verified, "200 with a session (workspace, credentialId, roles, csrfToken) and the cookie %s" % SESSION_COOKIE,
                  "enrolled and signed in" if verified.ok else verified.sentence(), body, person.name)
        if verified.ok and isinstance(verified.json, dict):
            person.adopt(verified.json)
            passkey.aap_credential_id = verified.json.get("credentialId")
            passkey.display_name = verified.json.get("displayName") or person.name
            person.passkey = passkey
            person.enrolled_now = True
            self.save_passkey(person)
        return verified

    def sign_in(self, person: Person, station: str, replay_of: Optional[Dict[str, Any]] = None,
                rp_id: Optional[str] = None) -> Tuple[Answer, Dict[str, Any]]:
        """
        Sign in with the stored passkey (auth.ts login/options, login/verify). `replay_of` reuses an
        earlier options bundle to prove the replay refusal; `rp_id` signs for another relying party on purpose.
        Returns the verify answer and the options bundle used.
        """
        if person.passkey is None:
            raise StationStop("no passkey is stored for %s at %s" % (person.name, self.key_path(person)))
        if replay_of is None:
            opened = self.request(person, "POST", "/v1/auth/login/options", {}, station, csrf=False)
            self.step(station, opened, "200 with options (challenge, rpId), issuedAtMs and a nonce",
                      "answered" if opened.ok else opened.sentence(), {}, person.name)
            if not opened.ok or not isinstance(opened.json, dict) or "options" not in opened.json:
                raise StationStop("POST /v1/auth/login/options answered %s" % opened.sentence())
            bundle = opened.json
        else:
            bundle = replay_of
        options = bundle["options"]
        assertion = person.passkey.assertion(str(options.get("challenge")), rp_id=rp_id or options.get("rpId") or person.passkey.rp_id,
                                             origin=self.origin)
        self.save_passkey(person)
        body = {"nonce": bundle.get("nonce"), "issuedAtMs": bundle.get("issuedAtMs"), "response": assertion}
        verified = self.request(person, "POST", "/v1/auth/login/verify", body, station, csrf=False)
        if verified.ok and isinstance(verified.json, dict) and replay_of is None and rp_id is None:
            person.adopt(verified.json)
        return verified, bundle

    def assertion_for(self, person: Person, challenge: str, station: str) -> Dict[str, Any]:
        if person.passkey is None:
            raise StationStop("%s holds no passkey to sign with" % person.name)
        assertion = person.passkey.assertion(challenge, origin=self.origin)
        self.save_passkey(person)
        return assertion

    # -- running -----------------------------------------------------------------
    def run(self) -> List[Outcome]:
        self.load_passkeys()
        if self.fresh:
            if not self.invite:
                raise HarnessError("--fresh refuses to run without a new --invite <link>: a second estate is a deliberate act")
            archived = self.archive_store()
            if archived:
                self.say("--fresh: the stored passkeys were set aside at %s" % archived)
            for person in self.people.values():
                person.passkey = None
                person.key_file = None
        start_index = 0
        if self.start_at:
            if self.start_at not in STATION_IDS:
                raise HarnessError("no station called %s; the stations are %s" % (self.start_at, ", ".join(STATION_IDS)))
            start_index = STATION_IDS.index(self.start_at)
            self.resume()
        for index, (station, title) in enumerate(STATIONS):
            if index < start_index:
                outcome = Outcome(station, SKIPPED, "%s: resumed at %s" % (title, self.start_at))
            else:
                outcome = self.run_station(station, title)
            self.outcomes.append(outcome)
            self.say(self.line(outcome))
        return self.outcomes

    def line(self, outcome: Outcome) -> str:
        return "%s — %s — %s" % (outcome.station, outcome.outcome, outcome.line)

    def resume(self) -> None:
        """--from: sign in everybody who has a stored passkey, so the later stations have their sessions."""
        for key in (A.FOUNDER,) + A.AUTHORS_INVITED + (A.VIEWER_INVITED,):
            person = self.people[key]
            if person.passkey is None:
                self.say("resume — %s has no stored passkey; stations needing %s say so" % (person.name, person.name))
                continue
            try:
                verified, _ = self.sign_in(person, "resume")
            except (StationStop, HarnessError) as err:
                self.say("resume — %s could not sign in: %s" % (person.name, err))
                continue
            self.step("resume", verified, "a session for %s" % person.name, "signed in" if verified.ok else verified.sentence(), None, person.name)
            self.say("resume — %s %s" % (person.name, "signed in with the stored passkey" if verified.ok else "refused: %s" % verified.sentence()))

    def run_station(self, station: str, title: str) -> Outcome:
        method = getattr(self, "station_%s" % station.lower())
        try:
            return method()
        except StationStop as err:
            return Outcome(station, FAIL, "%s: %s" % (title.lower(), err))
        except Unreachable as err:
            return Outcome(station, FAIL, "%s: the estate could not be reached, so nothing was judged: %s" % (title.lower(), err))
        except HarnessError as err:
            return Outcome(station, FAIL, "%s: the harness could not complete this station: %s" % (title.lower(), err))
        except (A.UnknownQuestion, A.AnswerDoesNotFit) as err:
            return Outcome(station, FAIL, "%s: %s" % (title.lower(), err))

    def founder(self) -> Person:
        person = self.people[A.FOUNDER]
        if not person.signed_in:
            raise StationStop("the founder has no session (S1 did not end in one)")
        return person

    def outcome_of(self, station: str) -> Optional[Outcome]:
        return next((o for o in self.outcomes if o.station == station), None)

    # -- S1 Enrol ---------------------------------------------------------------------
    def station_s1(self) -> Outcome:
        person = self.people[A.FOUNDER]
        how = ""
        if person.passkey is not None:
            verified, _ = self.sign_in(person, "S1")
            self.step("S1", verified, "200 with a session in the workspace %s" % self.estate["company"],
                      "signed in" if verified.ok else verified.sentence(), {"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<assertion>"}, person.name)
            if not verified.ok:
                if self.invite:
                    self.say("  S1: the stored passkey was refused (%s); enrolling with --invite instead" % verified.sentence())
                    person.passkey = None
                    verified = self.enrol_by_invite(person, self.invite, "S1")
                    how = "enrolled by invitation after the stored passkey was refused"
                else:
                    raise StationStop("POST /v1/auth/login/verify answered %s" % verified.sentence())
            else:
                how = "signed in with the stored passkey"
                if self.invite:
                    self.note("S1", "a passkey was already stored for %s, so the --invite link was not spent" % person.name)
        elif self.invite:
            verified = self.enrol_by_invite(person, self.invite, "S1")
            how = "enrolled by invitation"
        else:
            raise StationStop("no passkey is stored for %s at %s and no --invite <link> was given; the first run needs the invitation link" % (
                person.name, self.key_path(person)))
        if not verified.ok or person.session is None:
            raise StationStop("POST /v1/auth/invite/verify answered %s" % verified.sentence())
        workspace = person.session.get("workspace") or {}
        name = str(workspace.get("name") or "")
        self.facts["workspace"] = workspace
        if name.strip().lower() != self.estate["company"].lower():
            raise StationStop("%s; the session names the workspace %r, not %r" % (how, name, self.estate["company"]))
        return Outcome("S1", PASS, "%s as %s; session in %s (%s), roles %s, credential %s" % (
            how, person.name, name, workspace.get("realm"), ", ".join(person.roles) or "none", last4(person.credential_id)))

    # -- S2 Journey ------------------------------------------------------------------
    def read_journey(self, station: str, who: Person) -> Dict[str, Any]:
        answer = self.request(who, "GET", "/v1/journey", None, station)
        view = answer.json if isinstance(answer.json, dict) else {}
        current = view.get("currentStage")
        current_id = next((s.get("id") for s in view.get("stages") or [] if s.get("current")), None)
        self.step(station, answer, "the road: currentStage, stageCount %d, the current stage's id" % JOURNEY_STAGE_COUNT,
                  ("stage %s of %s, %s" % (current, view.get("stageCount"), current_id)) if answer.ok else answer.sentence(), None, who.name)
        if not answer.ok:
            raise StationStop("GET /v1/journey answered %s" % answer.sentence())
        self.facts["journey"][station] = view
        return view

    def station_s2(self) -> Outcome:
        founder = self.founder()
        view = self.read_journey("S2", founder)
        current = view.get("currentStage")
        current_id = next((s.get("id") for s in view.get("stages") or [] if s.get("current")), None)
        if view.get("stageCount") != JOURNEY_STAGE_COUNT:
            return Outcome("S2", FAIL, "journey: stageCount %r, not %d as journey.ts numbers the road" % (view.get("stageCount"), JOURNEY_STAGE_COUNT))
        if current == 1 and current_id == "policy_interview":
            return Outcome("S2", PASS, "journey: stage 1 of %d, policy_interview; road %s, landing %s" % (JOURNEY_STAGE_COUNT, view.get("road"), view.get("landingRoute")))
        return Outcome("S2", PASS, "journey: stage %s of %s, %s — this estate has walked before; the interviews that follow amend its charter (road %s)" % (
            current, view.get("stageCount"), current_id, view.get("road")))

    # -- the interview walk (S3 and S5) --------------------------------------------------
    def walk_interview(self, station: str, interview_type: str, who: Person) -> Tuple[str, Dict[str, Any], int]:
        """Start (or resume) the interview and answer every question the estate serves, from the book."""
        started = self.request(who, "POST", "/v1/onboarding/interviews", {"interviewType": interview_type}, station)
        self.step(station, started, "200 with the interview id and its first page",
                  "answered" if started.ok else started.sentence(), {"interviewType": interview_type}, who.name)
        if not started.ok or not isinstance(started.json, dict):
            raise StationStop("POST /v1/onboarding/interviews answered %s" % started.sentence())
        interview_id = str((started.json.get("interview") or {}).get("id") or (started.json.get("page") or {}).get("interviewId"))
        self.facts["interview"][interview_type] = interview_id
        page = started.json.get("page") or {}
        answered = 0
        served: List[str] = []
        for _ in range(200):
            state = page.get("state")
            if page.get("contradiction"):
                contradiction = page["contradiction"]
                raise StationStop("the estate served a contradiction page on %s: %s" % (
                    (page.get("question") or {}).get("questionId"), contradiction.get("message")))
            question = page.get("question")
            if question is None or state not in ("in_progress", "at_read_back"):
                break
            qid = str(question.get("questionId"))
            if qid in served:
                self.facts["served_twice"][interview_type].append(qid)
            served.append(qid)
            try:
                value = A.answer_for(interview_type, question)
            except A.UnknownQuestion as err:
                # Spec T11: reported as before, with the version pair in the sentence — the book's, and what can be said of the estate's.
                raise StationStop("%s — %s; %s, and it served a question the book does not know, so its catalog is later than %d or is "
                                  "not the one the book read (%s)" % (err, self.book_version_words(), ESTATE_STATES_NO_CATALOG_VERSION,
                                                                        A.CATALOG_VERSION_ANSWERED, A.CATALOG_SOURCE))
            value = self.override_answer(interview_type, qid, value)
            body = {"questionId": qid, "value": value}
            answer = self.request(who, "POST", "/v1/onboarding/interviews/%s/answers" % interview_id, body, station)
            self.step(station, answer, "200 with the next page (%s: %s)" % (qid, question.get("kind")),
                      "answered" if answer.ok else answer.sentence(), body, who.name)
            if not answer.ok or not isinstance(answer.json, dict):
                raise StationStop("POST /v1/onboarding/interviews/%s/answers for %s answered %s" % (interview_id, qid, answer.sentence()))
            self.facts["answers"][interview_type].append((qid, value, str(question.get("prompt", "")), str(question.get("kind", ""))))
            answered += 1
            page = answer.json
        self.facts["interview_state"][interview_type] = page.get("state")
        return interview_id, page, answered

    @staticmethod
    def book_version_words() -> str:
        return "the answer book answers catalog version %d" % A.CATALOG_VERSION_ANSWERED

    def override_answer(self, interview_type: str, qid: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """The book's answer, or this workspace's own where it has one (Spec T14: the Treasury's name, its payment approver and its account approvers)."""
        own = (self.answer_overrides.get(interview_type) or {}).get(qid)
        return own if own is not None else value

    def confirm_and_compile(self, station: str, interview_type: str, interview_id: str, who: Person, page: Dict[str, Any]) -> Dict[str, Any]:
        walked_back: Dict[str, str] = {}  # Spec T12 §1: a question walked back to once, so a second is a failure and never a loop
        state = page.get("state")
        while True:
            if state == "at_read_back":
                readback = self.request(who, "GET", "/v1/onboarding/interviews/%s/readback" % interview_id, None, station)
                walk = self.walk_back_of(readback)
                if walk is not None:
                    state = self.follow_walk_back(station, interview_type, interview_id, who, readback, walk, walked_back).get("state")
                    continue
                self.step(station, readback, "the charter read back in plain sentences, the realm first",
                          ("%d lines" % len((readback.json or {}).get("lines") or [])) if readback.ok else readback.sentence(), None, who.name)
                if not readback.ok or not isinstance(readback.json, dict):
                    raise StationStop("GET readback answered %s" % readback.sentence())
                self.facts["readback"][interview_type] = readback.json
                options = self.request(who, "POST", "/v1/onboarding/interviews/%s/confirm/options" % interview_id, {}, station)
                self.step(station, options, "200 with the digest-bound challenge, issuedAtMs and the digest",
                          "answered" if options.ok else options.sentence(), {}, who.name)
                if not options.ok or not isinstance(options.json, dict):
                    raise StationStop("POST confirm/options answered %s" % options.sentence())
                challenge = str((options.json.get("options") or {}).get("challenge"))
                body = {"issuedAtMs": options.json.get("issuedAtMs"), "response": self.assertion_for(who, challenge, station)}
                confirmed = self.request(who, "POST", "/v1/onboarding/interviews/%s/confirm" % interview_id, body, station)
                walk = self.walk_back_of(confirmed)
                if walk is not None:
                    state = self.follow_walk_back(station, interview_type, interview_id, who, confirmed, walk, walked_back).get("state")
                    continue
                self.step(station, confirmed, "200 with the interview confirmed", "confirmed" if confirmed.ok else confirmed.sentence(), body, who.name)
                if not confirmed.ok:
                    raise StationStop("POST confirm answered %s" % confirmed.sentence())
                state = "confirmed"
            if state in ("confirmed", "compiled"):
                compiled = self.request(who, "POST", "/v1/onboarding/interviews/%s/compile" % interview_id, {}, station)
                walk = self.walk_back_of(compiled)
                if walk is not None:
                    state = self.follow_walk_back(station, interview_type, interview_id, who, compiled, walk, walked_back).get("state")
                    continue
                self.step(station, compiled, "200 with the compiled charter, the write receipt and the seat",
                          "compiled and written" if compiled.ok else compiled.sentence(), {}, who.name)
                if not compiled.ok or not isinstance(compiled.json, dict):
                    raise StationStop("POST compile answered %s" % compiled.sentence())
                self.facts["compile"][interview_type] = compiled.json
                self.facts["charter"][interview_type] = compiled.json.get("charter") or {}
                return compiled.json
            raise StationStop("the interview stands in state %r after its questions; the read-back was not reached" % state)

    @staticmethod
    def walk_back_of(answer: Answer) -> Optional[str]:
        """The questionId a CHARTER_INCOMPLETE refusal asks the browser to walk back to, or None (Spec T12 §1)."""
        refusal = answer.refusal
        if refusal and refusal.get("code") == "CHARTER_INCOMPLETE":
            target = refusal.get("walkBackTo")
            if isinstance(target, dict) and target.get("questionId"):
                return str(target["questionId"])
        return None

    def follow_walk_back(self, station: str, interview_type: str, interview_id: str, who: Person,
                         refusal_answer: Answer, qid: str, walked_back: Dict[str, str]) -> Dict[str, Any]:
        """
        Spec T12 §1: a founder's browser taken back to a question answers it and returns to the read-back. Where the
        read-back or a confirm answers CHARTER_INCOMPLETE with walkBackTo, the harness answers the named question from
        the book, resumes to the read-back, and reports the walk-back as a note. The same question walked back to twice
        is a failure carrying both sentences — a book that cannot satisfy the belt is reported, never looped.
        """
        refusal = refusal_answer.refusal or {}
        sentence = str(refusal.get("message") or refusal_answer.sentence())
        self.step(station, refusal_answer, "a walk-back to %s the harness follows, or the read-back" % qid,
                  "walk-back to %s: %s" % (qid, sentence), None, who.name)
        if qid in walked_back:
            raise StationStop("walked back to %s a second time and the belt still refuses: first %r, then %r; the book's answer "
                              "does not satisfy the estate's belt, so it is reported and never looped" % (qid, walked_back[qid], sentence))
        walked_back[qid] = sentence
        book = A.ANSWERS.get(interview_type, {})
        if qid not in book:
            raise StationStop("the estate walked back to %s (%s), which the answer book has no answer for" % (qid, sentence))
        value = self.override_answer(interview_type, qid, book[qid])
        body = {"questionId": qid, "value": value}
        answered = self.request(who, "POST", "/v1/onboarding/interviews/%s/answers" % interview_id, body, station)
        self.step(station, answered, "200 with the next page (%s answered from the book on the walk-back)" % qid,
                  "answered from the book" if answered.ok else answered.sentence(), body, who.name)
        if not answered.ok or not isinstance(answered.json, dict):
            raise StationStop("answering %s on the walk-back answered %s" % (qid, answered.sentence()))
        self.facts["answers"][interview_type].append((qid, value, "", A.kind_of(interview_type, qid) or ""))
        page = self.drive_to_read_back(station, interview_type, interview_id, who, answered.json)
        self.note(station, "walked back to %s: %s; answered from the book and returned to the read-back" % (qid, sentence))
        return page

    def drive_to_read_back(self, station: str, interview_type: str, interview_id: str, who: Person, page: Dict[str, Any]) -> Dict[str, Any]:
        """Answer from the book any further questions the estate serves after a walk-back's answer, until the read-back."""
        for _ in range(200):
            if page.get("contradiction"):
                raise StationStop("the estate served a contradiction on the walk-back: %s" % (page.get("contradiction") or {}).get("message"))
            question = page.get("question")
            if question is None or page.get("state") not in ("in_progress", "at_read_back"):
                return page
            qid = str(question.get("questionId"))
            value = self.override_answer(interview_type, qid, A.answer_for(interview_type, question))
            body = {"questionId": qid, "value": value}
            answer = self.request(who, "POST", "/v1/onboarding/interviews/%s/answers" % interview_id, body, station)
            self.step(station, answer, "200 with the next page (%s: %s, resumed toward the read-back)" % (qid, question.get("kind")),
                      "answered" if answer.ok else answer.sentence(), body, who.name)
            if not answer.ok or not isinstance(answer.json, dict):
                raise StationStop("resuming after the walk-back, %s answered %s" % (qid, answer.sentence()))
            self.facts["answers"][interview_type].append((qid, value, str(question.get("prompt", "")), str(question.get("kind", ""))))
            page = answer.json
        return page

    def station_s3(self) -> Outcome:
        founder = self.founder()
        interview_id, page, answered = self.walk_interview("S3", "policy", founder)
        compiled = self.confirm_and_compile("S3", "policy", interview_id, founder, page)
        standing = self.request(founder, "GET", "/v1/onboarding/charter", None, "S3")
        self.step("S3", standing, "standsWritten true with inForceSince", json.dumps(standing.json) if standing.ok else standing.sentence(), None, founder.name)
        self.facts["charter_standing"] = standing.json if isinstance(standing.json, dict) else None
        view = self.read_journey("S3", founder)
        current = view.get("currentStage")
        charter = compiled.get("charter") or {}
        detail = "policy interview: %d questions answered, read-back %d lines, charter compiled (%s; quorum %s; networks recorded %s, allowed %s), journey stage %s of %s" % (
            answered, len((self.facts["readback"].get("policy") or {}).get("lines") or []), charter.get("name"), charter.get("quorum"),
            charter.get("recordedChains"), charter.get("allowedChains"), current, view.get("stageCount"))
        # Spec T11: the book's catalog version beside the estate's — which the estate does not state, so what it served stands for it.
        detail += "; %s, and the estate served %d question(s), every one known to the book (%s)" % (self.book_version_words(), answered, ESTATE_STATES_NO_CATALOG_VERSION)
        problems: List[str] = []
        if not (isinstance(standing.json, dict) and standing.json.get("standsWritten") is True):
            problems.append("GET /v1/onboarding/charter says %s" % (json.dumps(standing.json) if standing.json is not None else standing.sentence()))
        if not isinstance(current, int) or current < 2:
            problems.append("the journey stands at stage %s, not 2" % current)
        elif current > 2:
            detail += " (beyond stage 2: this estate had walked further before this run)"
        if problems:
            return Outcome("S3", FAIL, detail + "; " + "; ".join(problems))
        return Outcome("S3", PASS, detail)

    # -- S4 People --------------------------------------------------------------------
    # Spec T10 (20 September 2026): every person is brought in on their own credential. AER 360 Spec 91 (aeredium/AERAccounts,
    # commit 9964205, PR #112) made an `author` invitation mint a credential of the person's own on the account's role-bearing
    # policy entry (services/invites.ts, mintAuthorCredential), bound to their passkey on redemption. Two things Spec 91 did not
    # do, and said so: a passkey enrolled before it keeps speaking for the shared credential until that credential is revoked
    # at the platform, and a roster seat bound to the shared credential stays bound until the seat is re-granted. The harness's
    # three people were enrolled before Spec 91 and Ada's seat was granted before it; the fourth live run
    # (aer360-harness-2026-09-20-135419.md) counted Ben's press after Ada's as Ada's, because the two shared one credential.
    # So S4 reads Ada's seat as it finds it, compares each session's credentialId with the founder's, brings the person in
    # again where they are equal, and grants Ada's seat again where it does not name her own credential.
    OWN_CREDENTIAL_EXPECTED = "a credential of %s's own, not the founder's"

    def mint_invite(self, station: str, person: Person, role: str) -> Answer:
        founder = self.founder()
        body = {"displayName": person.name, "email": person.email, "role": role}
        minted = self.request(founder, "POST", "/v1/invites", body, station)
        self.step(station, minted, "201 with the one-time link %s/invite#<token>, said once" % self.origin,
                  ("minted (credential %s)" % last4((minted.json or {}).get("credentialId"))) if minted.ok else minted.sentence(), body, founder.name)
        if minted.ok and isinstance(minted.json, dict):
            invite = dict(minted.json.get("invite") or {})
            invite["credentialId"] = minted.json.get("credentialId") or invite.get("credentialId")
            self.facts["invites_minted"].append({"person": person.key, "role": role, "invite": invite})
        return minted

    def bring_in(self, station: str, person: Person, role: str) -> str:
        """Enrol a person by a freshly minted invitation, or sign them in with the stored passkey."""
        if person.signed_in:
            return "already signed in"
        if person.passkey is not None:
            verified, _ = self.sign_in(person, station)
            self.step(station, verified, "a session for %s" % person.name, "signed in" if verified.ok else verified.sentence(), None, person.name)
            if verified.ok:
                return "signed in with the stored passkey"
            return "the stored passkey was refused: %s" % verified.sentence()
        minted = self.mint_invite(station, person, role)
        if not minted.ok or not isinstance(minted.json, dict) or not minted.json.get("url"):
            return "no invitation: %s" % minted.sentence()
        verified = self.enrol_by_invite(person, str(minted.json["url"]), station)
        if not verified.ok:
            return "the enrolment was refused: %s" % verified.sentence()
        seat = (verified.json or {}).get("approverSeat")
        return "enrolled as %s%s" % (role, (", seat on redemption: %s" % json.dumps(seat)) if seat else "")

    def bring_in_on_own_credential(self, station: str, person: Person, founder: Person) -> str:
        """
        Spec T10 §1. Sign the person in with their stored passkey (or enrol them by a fresh invitation where none is stored),
        then compare the session's credentialId with the founder's. Equal is the shared credential of S10's finding: S4 says
        so and brings the person in again (`bring_in_again`). Different is "already on their own credential", and nothing is
        minted. The step's expectation is the one line `a credential of <name>'s own, not the founder's`; its result names the
        last four characters of both credentials.
        """
        expected = self.OWN_CREDENTIAL_EXPECTED % person.name
        answer: Optional[Answer] = None
        fresh = False
        if person.signed_in:
            how = "already signed in"
        elif person.passkey is not None:
            verified, _ = self.sign_in(person, station)
            if not verified.ok:
                self.step(station, verified, "a session for %s" % person.name, verified.sentence(), None, person.name)
                return "the stored passkey was refused: %s" % verified.sentence()
            how = "signed in with the stored passkey"
            answer = verified
        else:
            minted = self.mint_invite(station, person, "author")
            if not minted.ok or not isinstance(minted.json, dict) or not minted.json.get("url"):
                return "no invitation: %s" % minted.sentence()
            verified = self.enrol_by_invite(person, str(minted.json["url"]), station)
            if not verified.ok:
                return "the enrolment was refused: %s" % verified.sentence()
            seat = (verified.json or {}).get("approverSeat")
            how = "enrolled as author%s" % ((", seat on redemption: %s" % json.dumps(seat)) if seat else "")
            answer = verified
            fresh = True
        if not person.credential_id or not founder.credential_id:
            said = "%s; not compared with the founder's credential: %s names no credentialId" % (
                how, "the session" if not person.credential_id else "the founder's session")
            if answer is not None:
                self.step(station, answer, expected, said, None, person.name)
            return said
        if person.credential_id != founder.credential_id:
            result = "already on their own credential: %s, not the founder's %s" % (last4(person.credential_id), last4(founder.credential_id))
            if answer is not None:
                self.step(station, answer, expected, result, None, person.name)
            return "%s; %s" % (how, result)
        result = "on the shared credential %s, the founder's" % last4(founder.credential_id)
        if answer is not None:
            self.step(station, answer, expected, result + ("" if fresh else "; brought in again below"), None, person.name)
        if fresh:
            # A fresh invitation on this estate enrolled the founder's credential just now (the estate before Spec 91), so a
            # second one would too; S10 reports the one credential worn by several people.
            return "%s; %s — a fresh invitation on this estate enrolled the founder's credential, so no second one was minted" % (how, result)
        self.say("  %s: %s's session carries the founder's credential %s (a passkey enrolled before Spec 91 keeps speaking for it); bringing %s in again on a credential of their own" % (
            station, person.name, last4(founder.credential_id), person.name))
        return "%s; %s; %s" % (how, result, self.bring_in_again(station, person, founder))

    def bring_in_again(self, station: str, person: Person, founder: Person) -> str:
        """
        Spec T10 §1: the founder mints a new `author` invitation for the same name and email (`mint_invite`); the person
        redeems it with a NEW software passkey (`enrol_by_invite`), stored beside the old one under a suffixed name
        (`<person>-2-<date>.json`, `next_key_path`) and never over it; the person's session is the new one. The old passkey
        is kept, because the estate's audit trail names it and a later station may need to prove it no longer signs. A
        refusal anywhere on the road is told in the estate's words, and the person keeps the session and the passkey they had.
        """
        expected = self.OWN_CREDENTIAL_EXPECTED % person.name
        old_passkey = person.passkey
        old_file = person.key_file or self.key_path(person)
        record: Dict[str, Any] = {"person": person.key, "old_credential": person.credential_id, "old_key_file": old_file,
                                  "new_credential": None, "new_key_file": None, "seat": None, "ok": False, "said": None}
        self.facts["brought_in_again"].append(record)
        minted = self.mint_invite(station, person, "author")
        if not minted.ok or not isinstance(minted.json, dict) or not minted.json.get("url"):
            record["said"] = "not brought in again: the invitation answered %s" % minted.sentence()
            return record["said"]
        person.key_file = self.next_key_path(person)
        verified: Optional[Answer] = None
        stopped = ""
        try:
            verified = self.enrol_by_invite(person, str(minted.json["url"]), station)
        except StationStop as err:
            stopped = str(err)
        finally:
            if person.passkey is old_passkey:  # no new passkey was adopted, so the old one keeps its own file
                person.key_file = old_file
        if verified is None or not verified.ok:
            record["said"] = "not brought in again: %s" % (stopped if verified is None else "the enrolment answered %s" % verified.sentence())
            return record["said"]
        record["new_credential"] = person.credential_id
        record["new_key_file"] = person.key_file
        record["seat"] = (verified.json or {}).get("approverSeat")
        if person.credential_id == founder.credential_id:
            result = "still the founder's %s after the re-invitation" % last4(person.credential_id)
        else:
            record["ok"] = True
            result = "brought in again on %s, not the founder's %s" % (last4(person.credential_id), last4(founder.credential_id))
        self.step(station, verified, expected, result, None, person.name)
        seat_said = (", seat on redemption: %s" % json.dumps(record["seat"])) if record["seat"] else ""
        record["said"] = "%s (the new passkey stored at %s, the old one kept at %s%s)" % (result, person.key_file, old_file, seat_said)
        return record["said"]

    def read_seats(self, station: str, founder: Person, expected: str) -> Optional[Dict[str, Any]]:
        seats = self.request(founder, "GET", "/v1/approver-seats", None, station)
        self.step(station, seats, expected, "answered" if seats.ok else seats.sentence(), None, founder.name)
        view = seats.json if isinstance(seats.json, dict) else None
        if view is not None:
            self.facts["seats"] = view
        return view

    @staticmethod
    def seat_of(view: Optional[Dict[str, Any]], email: str) -> Optional[Dict[str, Any]]:
        if not isinstance(view, dict):
            return None
        return next((s for s in view.get("seats") or [] if str(s.get("email", "")).lower() == email.lower()), None)

    @staticmethod
    def seat_words(row: Optional[Dict[str, Any]], view: Optional[Dict[str, Any]]) -> str:
        """A seat as the line speaks it: its state and the credential it names, or that it is not in the seats at all."""
        if view is None:
            return "no seats view"
        if row is None:
            return "not in the charter's seats"
        named = last4(row["credentialId"]) if row.get("credentialId") else ("no credential (ambiguous: several answer to the address)" if row.get("ambiguous") else "no credential")
        return "%s, naming %s" % (row.get("state"), named)

    def seat_on_own_credential(self, station: str, founder: Person, ada: Person, found_words: str) -> str:
        """
        Spec T10 §2. After Ada is brought in again, read the seats; where Ada's seat is enrolled_not_seated or names a credential
        other than her session's, grant it again (POST /v1/approver-seats/grant) and expect the seat to name her own credential.
        The step says which credential the seat named before and after; a grant the estate refuses is a finding in the estate's
        words. `found_words` is Ada's seat as this run found it, before anybody was brought in again.
        """
        own = ada.credential_id if ada.signed_in else None
        view = self.read_seats(station, founder, "the charter's approver seats after the people were brought in; %s's seat naming %s" % (
            ada.name, ("%s's own credential %s" % (ada.name, last4(own))) if own else "a credential of %s's own" % ada.name))
        row = self.seat_of(view, ada.email)
        stood_words = self.seat_words(row, view)
        record: Dict[str, Any] = {"found": found_words, "stood": row, "granted": None, "after": None, "refusal": None}
        self.facts["seat_regrant"] = record
        said = ["%s's seat: found %s" % (ada.name, found_words)]
        if stood_words != found_words:
            said.append("after the people were brought in %s" % stood_words)
        if row is None:
            return "; ".join(said)
        before = row.get("credentialId")
        names_own = own is not None and before is not None and str(before) == str(own)
        if row.get("state") != "enrolled_not_seated" and (own is None or names_own):
            if names_own:
                said.append("%s's own credential, so no grant was needed" % ada.name)
            return "; ".join(said)
        body = {"email": ada.email}
        expected = "the seat seated, naming %s (before the grant: %s)" % (
            ("%s's own credential %s" % (ada.name, last4(own))) if own else "%s's credential" % ada.name, stood_words)
        granted = self.request(founder, "POST", "/v1/approver-seats/grant", body, station)
        if granted.ok and isinstance(granted.json, dict):
            self.facts["seats"] = granted.json
            after = self.seat_of(granted.json, ada.email)
            after_words = self.seat_words(after, granted.json)
            record.update(granted=True, after=after)
            self.step(station, granted, expected, "granted: %s" % after_words, body, founder.name)
            said.append("granted again by the founder: %s" % after_words)
            if own is not None and (after is None or str(after.get("credentialId")) != str(own)):
                self.finding(station, "approver seat: %s's seat after the grant" % ada.name, body, granted, expected,
                             "the seat is %s, not %s's own %s" % (after_words, ada.name, last4(own)))
            return "; ".join(said)
        record.update(granted=False, refusal=granted.sentence())
        self.step(station, granted, expected, granted.sentence(), body, founder.name)
        self.finding(station, "approver seat: the grant of %s's seat" % ada.name, body, granted, expected, "refused: %s" % granted.sentence())
        said.append("the grant answered %s" % granted.sentence())
        return "; ".join(said)

    def retired_passkeys(self) -> List[Dict[str, Any]]:
        """
        Every passkey stored for the estate's people other than the one each now signs with (Spec T10 §1): kept, never used to
        sign, and still bound at the estate to the credential it enrolled — which is why the People register's Spec 91 marker on
        the founder's row names them (S10). Read from the store, so a run after the re-invitation knows them too.
        """
        out: List[Dict[str, Any]] = []
        for person in self.people.values():
            for path in self.stored_key_paths(person):
                if person.key_file and os.path.realpath(path) == os.path.realpath(person.key_file):
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        data = json.load(handle)
                except (OSError, ValueError):
                    continue
                if not isinstance(data, dict) or (data.get("base") and data["base"] != self.base):
                    continue
                out.append({"person": person.key, "label": data.get("display_name") or person.name,
                            "aap_credential_id": data.get("aap_credential_id"), "path": path})
        return out

    def station_s4(self) -> Outcome:
        founder = self.founder()
        ada = self.people[A.PAYMENT_APPROVER]
        findings_before = len(self.findings)
        found_view = self.read_seats("S4", founder, "the charter's approver seats as this run finds them: which credential %s's seat names before anybody is brought in again" % ada.name)
        found_words = self.seat_words(self.seat_of(found_view, ada.email), found_view)
        said: List[str] = []
        for key in A.AUTHORS_INVITED:
            person = self.people[key]
            said.append("%s %s" % (person.name, self.bring_in_on_own_credential("S4", person, founder)))
        seat_said = self.seat_on_own_credential("S4", founder, ada, found_words)
        grant_said, changes_said, changes_ok = self.sign_the_roster_changes("S4", founder)  # Spec T17 §1: S4 grants a stale seat again, then T15's pass signs it
        register = self.request(founder, "GET", "/v1/invites", None, "S4")
        self.step("S4", register, "the invitation register: who was invited, as what, and how it went; each row's sharesCredentialWith (Spec 91's marker) is read by S10",
                  "answered" if register.ok else register.sentence(), None, founder.name)
        self.facts["invites_register"] = register.json if isinstance(register.json, dict) else None
        rows = (register.json or {}).get("invites") if isinstance(register.json, dict) else None
        grant_segment = ("%s; " % grant_said) if grant_said else ""  # Spec T17: the grant step's words, before the signing narrative; empty where the door was not open
        detail = "people: %s; %s; %sroster changes: %s; %s invitation(s) in the register" % ("; ".join(said), seat_said, grant_segment, changes_said, len(rows) if isinstance(rows, list) else "?")
        signed_in = all(self.people[k].signed_in for k in A.AUTHORS_INVITED)
        brought_in = all(r["ok"] for r in self.facts["brought_in_again"])
        if signed_in and brought_in and changes_ok and len(self.findings) == findings_before:
            return Outcome("S4", PASS, detail)
        return Outcome("S4", FAIL, detail)

    # -- S4's tail: the approvers sign a change of who the approvers are (Spec T15) -------------------------------
    def read_roster_changes(self, station: str, founder: Person, expected: str) -> Tuple[Answer, Optional[Dict[str, Any]]]:
        """GET /v1/roster/changes as the founder (Spec 99): every roster change the platform holds for the estate, recorded as read."""
        answer = self.request(founder, "GET", T.ROSTER_CHANGES_ROUTE, None, station)
        view = answer.json if answer.ok and isinstance(answer.json, dict) else None
        listed = view.get("changes") if view is not None else None
        if isinstance(listed, list):
            result = "%d change(s) listed%s" % (len(listed), (": " + "; ".join(self.change_words(c) for c in listed if isinstance(c, dict))) if listed else "")
        else:
            result = answer.sentence()
        self.step(station, answer, expected, result, None, founder.name)
        if view is not None:
            self.facts["roster_changes"] = view
        return answer, view

    @staticmethod
    def change_words(change: Dict[str, Any]) -> str:
        """One roster change as the line speaks it: the ceremony in short form, its state, whose seat it moves, the count."""
        seat = change.get("seat") if isinstance(change.get("seat"), dict) else None
        whose = ("%s's seat" % (seat.get("name") or seat.get("email"))) if seat else "a roster change this estate did not propose"
        return "%s… %s (%s, %s of %s signed)" % (T.credential_short_form(change.get("pendingTxId")), change.get("state"), whose,
                                                 change.get("signaturesCollected"), change.get("requiredSignatures"))

    @staticmethod
    def route_not_found(answer: Answer) -> bool:
        """
        An estate before Spec 99 has no roster roads: fastify answers its own 404 (`Route GET:/v1/roster/changes not found`, no refusal body of
        the house's), and the double a REQUEST_MALFORMED naming the route. Either is the door's absence, not a refusal of the founder.
        """
        if answer.status == 404 and answer.refusal is None:
            return True
        refusal = answer.refusal or {}
        detail = refusal.get("detail") if isinstance(refusal.get("detail"), dict) else {}
        return refusal.get("code") == "REQUEST_MALFORMED" and "not found" in str(detail.get("validation") or "").lower()

    def person_named(self, name: Any) -> Optional[Person]:
        """The harness's person the estate names by display name — the roster's seats and the register carry the census names."""
        wanted = str(name or "").strip().lower()
        return next((p for p in self.people.values() if p.name.lower() == wanted), None) if wanted else None

    def person_by_email(self, email: Any) -> Optional[Person]:
        wanted = str(email or "").strip().lower()
        return next((p for p in self.people.values() if p.email.lower() == wanted), None) if wanted else None

    def sign_the_roster_changes(self, station: str, founder: Person) -> Tuple[str, str, bool]:
        """
        Spec T17 §1 and §2, in substance T15 §1 with a grant step. After every person has signed in on their own credential, S4 reads
        GET /v1/roster/changes and GET /v1/approver-seats. Where the seat view carries `onRoster` (AER 360 Spec 105), S4 grants each
        stale seat of a person of the harness — one whose seat reads `onRoster: false` — one at a time, and only where no change for it
        already awaits, then T15's pass signs it as the persons who can (`_sign_pass_t17`). Where the seat view has no `onRoster` (an
        estate before Spec 105), S4 prints one line and behaves exactly as T15 (`_sign_pass_t15`).

        Returns three words for the station's line: the grant step's (empty where the door was not open), T15's/T17's signing words,
        and whether every change the pass could sign ended with the seat reading on the roster.
        """
        answer, view = self.read_roster_changes(station, founder, (
            "every roster change the platform holds for the estate (Spec 99): the ceremony, its state (awaiting, approved, applied, expired, closed), "
            "whose seat it moves, requiredSignatures and signaturesCollected, who has signed and who may; a fresh estate lists none"))
        if view is None:
            if self.route_not_found(answer):
                self.note(station, "the estate has no door onto the roster ceremony (%s answered %s): an estate before AER 360 Spec 99, so the signing pass was not made" % (
                    T.ROSTER_CHANGES_ROUTE, answer.sentence()))
                return "", "the door is not open (an estate before Spec 99): %s answered %s" % (T.ROSTER_CHANGES_ROUTE, answer.sentence()), True
            return "", "the roster changes could not be read: %s" % answer.sentence(), False
        # Spec T17 §1: the grant step reads the approver seats, with onRoster (AER 360 Spec 105). An estate without the field is behaved
        # as T15 (§0), with one line saying so; the two signing rules of §2 apply only where onRoster is present.
        seats_view = self.read_seats(station, founder, (
            "the approver seats with onRoster (AER 360 Spec 105): which seat of a person of the harness reads on the roster and which is stale"))
        seats = seats_view.get("seats") if isinstance(seats_view, dict) else None
        has_onroster = isinstance(seats, list) and any(isinstance(s, dict) and T.SEAT_ON_ROSTER in s for s in seats)
        if not has_onroster:
            words, ok = self._sign_pass_t15(station, founder, view)
            return "the seat view has no onRoster; skipping", words, ok
        return self._sign_pass_t17(station, founder, view, [s for s in seats if isinstance(s, dict)])

    def _sign_pass_t15(self, station: str, founder: Person, view: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Spec T15's signing pass, run unchanged where the seat view has no onRoster (an estate before AER 360 Spec 105). For each change
        the estate lists as awaiting it signs in turn as each person the list names as able to sign; a change listed expired or one this
        estate did not propose is proposed afresh once (`propose_the_move_afresh`, `REPROPOSALS_AT_MOST`) and signed. Returns the words and
        whether every change the pass could sign ended applied.
        """
        changes = [c for c in (view.get("changes") or []) if isinstance(c, dict)]
        if not changes:
            return "none awaits a signature: the register lists no roster change, so S4 did nothing new (Spec T15 §4)", True
        said: List[str] = []
        ok = True
        finished: Dict[str, str] = {}  # the ceremony's id → the outcome the pass reached for it
        reproposed: Dict[str, int] = {}  # the seat's address (or "*" for a change naming none) → how many times the move was proposed afresh

        def signable(c: Dict[str, Any]) -> bool:
            return str(c.get("state")) == "awaiting" and isinstance(c.get("seat"), dict) and bool(c.get("proposedHere"))

        queue = list(changes)
        while queue:
            change = queue.pop(0)
            pending_tx_id = str(change.get("pendingTxId"))
            if pending_tx_id in finished and not (finished[pending_tx_id] == PROPOSED_AFRESH and signable(change)):
                continue  # judged already — unless the platform's content-bound ceremony came back as the same id, now proposed here and awaiting
            state = str(change.get("state"))
            seat = change.get("seat") if isinstance(change.get("seat"), dict) else None
            record: Dict[str, Any] = {"pendingTxId": pending_tx_id, "state_found": state, "proposed_here": bool(change.get("proposedHere")), "seat": seat,
                                      "sentence": change.get("sentence"), "signatures": [], "outcome": None, "rebound": None, "reproposed": False}
            self.facts["roster_signing"].append(record)
            if state in ("applied", "closed"):
                finished[pending_tx_id] = record["outcome"] = state
                said.append("%s: %s" % (self.change_words(change), change.get("sentence")))
                continue
            if signable(change):
                outcome, words = self.sign_as_the_list_names(station, founder, change, record)
                finished[pending_tx_id] = record["outcome"] = outcome
                said.append("%s: %s" % (self.change_words(change), words))
                if outcome != "applied":
                    ok = False
                continue
            # Expired, approved and unapplied, or a change this estate did not propose: the estate offers no press for it as it stands, and says so.
            key = str(seat.get("email") or "").lower() if seat else "*"
            record["outcome"] = state if seat else "not proposed here"
            self.note(station, "roster change %s…: %s" % (T.credential_short_form(pending_tx_id), change.get("sentence")))
            if seat is None and state not in ("awaiting", "approved"):
                # a foreign ceremony the platform no longer holds live: nothing to propose afresh for, and nothing to sign
                finished[pending_tx_id] = record["outcome"]
                said.append("%s: reported; not signed, the estate offers no press for it" % self.change_words(change))
                continue
            if reproposed.get(key, 0) >= REPROPOSALS_AT_MOST:
                finished[pending_tx_id] = record["outcome"]
                if seat is None:
                    said.append("%s: still a roster change this estate did not propose after the seats were granted again; not signed, the estate offers no press for it" % self.change_words(change))
                else:
                    said.append("%s: %s again after the move was proposed afresh — S4 fails naming the ceremony %s" % (self.change_words(change), state, pending_tx_id))
                    ok = False
                continue
            reproposed[key] = reproposed.get(key, 0) + 1
            record["reproposed"] = True
            finished[pending_tx_id] = PROPOSED_AFRESH
            record["outcome"] = "%s; %s" % (record["outcome"], PROPOSED_AFRESH)
            afresh = self.propose_the_move_afresh(station, founder, seat)
            said.append("%s: %s; %s" % (self.change_words(change), change.get("sentence"), afresh))
            again, view_again = self.read_roster_changes(station, founder, "the roster changes after the seat was granted again: the move proposed afresh and listed awaiting%s" % (
                (", naming %s's seat" % (seat.get("name") or seat.get("email"))) if seat else ""))
            if view_again is None:
                said.append("the roster changes could not be read again: %s" % again.sentence())
                ok = False
                break
            # the same ceremony may be listed again — now proposed here and awaiting, where the platform's content-bound ceremony was reached again —
            # or a fresh one; a change judged already is not judged twice
            queue = [c for c in (view_again.get("changes") or []) if isinstance(c, dict)
                     and (str(c.get("pendingTxId")) not in finished or (finished[str(c.get("pendingTxId"))] == PROPOSED_AFRESH and signable(c)))]
        return "; ".join(said), ok

    # -- S4's tail under AER 360 Spec 105: the seat view reads the roster, so S4 grants a stale seat again and signs it (Spec T17) ---
    def _sign_pass_t17(self, station: str, founder: Person, view: Dict[str, Any], seats: List[Dict[str, Any]]) -> Tuple[str, str, bool]:
        """
        Spec T17. The seat view carries onRoster (AER 360 Spec 105). S4 grants each stale seat of a person of the harness — matched by
        email `harness+<name>@aeredium.io`, never by display name — one at a time, and only where no change for it already awaits; then
        T15's pass signs it as the persons whose own seat reads `onRoster: true`, and after the count S4 re-reads the seat and says
        `moved` only on a `true` read. A seat reading `true` prints nothing; a seat with a null credential or `ambiguous`, a seat of a
        person not of the harness, and a seat reading null each print their line and are not granted (§1). Returns the grant step's
        words, the signing words, and whether every seat S4 set out to move ended reading on the roster.
        """
        seats_by_email = {str(s.get("email", "")).lower(): s for s in seats}
        changes = [c for c in (view.get("changes") or []) if isinstance(c, dict)]

        def awaiting_for(email: str) -> Optional[Dict[str, Any]]:
            wanted = str(email).lower()
            return next((c for c in changes if str(c.get("state")) == "awaiting" and isinstance(c.get("seat"), dict)
                         and str(c["seat"].get("email") or "").lower() == wanted), None)

        grant_lines: List[str] = []
        sign_lines: List[str] = []
        ok = True
        stopped = False  # once a count fell short, S4 grants no further seat (§2)
        for seat in seats:
            onr = seat.get(T.SEAT_ON_ROSTER)
            who = seat.get("name") or seat.get("email")
            email = str(seat.get("email") or "").lower()
            person = self.person_by_email(email)
            if onr is True:
                continue  # a true seat prints nothing
            # A stale seat, or one the estate could not verify. The lines, in the order §1 gives them: a null credential or two passkeys
            # enrolled (which reads null too, so it is judged first); a seat of a person not of the harness; then a seat reading null.
            if seat.get("credentialId") is None or seat.get("ambiguous"):
                grant_lines.append("%s's seat: two passkeys enrolled; not granted" % who)
                continue
            if person is None:
                grant_lines.append("%s's seat: not of the harness; not granted" % who)
                continue
            if onr is None:
                grant_lines.append("%s's seat: unverified: %s" % (who, seat.get(T.SEAT_ROSTER_SAID)))
                continue
            # onr is False, the seat names a credential, and the person is of the harness: a seat the grant road will move
            if stopped:
                continue  # a count already fell short: this seat is not granted (§2)
            change = awaiting_for(email)
            if change is not None:
                grant_lines.append("%s's seat: a change already awaits; not granted" % person.name)
            else:
                afresh = self.propose_the_move_afresh(station, founder, {"email": person.email, "name": person.name})
                grant_lines.append("%s's seat: granted again; %s" % (person.name, afresh))
                again, view_again = self.read_roster_changes(station, founder,
                    "the roster changes after %s's seat was granted again: the move proposed afresh and listed awaiting, or moved at once where the grant carries no pendingTxId" % person.name)
                if view_again is None:
                    sign_lines.append("the roster changes could not be read again: %s" % again.sentence())
                    ok = False
                    break
                changes = [c for c in (view_again.get("changes") or []) if isinstance(c, dict)]
                change = awaiting_for(email)
                if change is None:
                    # the grant's answer carried no pendingTxId: Spec 95 applied the move at once (§1)
                    grant_lines.append("moved at once")
                    moved, words = self._confirm_seat_onroster(station, founder, person, None, None, None)
                    sign_lines.append(words)
                    if not moved:
                        ok = False
                    continue
            outcome, words = self._sign_change_t17(station, founder, change, person, seats_by_email)
            sign_lines.append("%s: %s" % (self.change_words(change), words))
            if outcome == "count_short":
                ok = False
                stopped = True
                continue  # grant no further seat
            if outcome != "moved":
                ok = False
        grant_said = "; ".join(grant_lines) if grant_lines else "every seat of the harness reads on the roster; nothing to grant"
        changes_said = "; ".join(sign_lines) if sign_lines else "none awaits a signature: no stale seat of the harness needed a move (Spec T17)"
        return grant_said, changes_said, ok

    def _sign_change_t17(self, station: str, founder: Person, change: Dict[str, Any], owner: Person,
                         seats_by_email: Dict[str, Dict[str, Any]]) -> Tuple[str, str]:
        """
        Spec T17 §2. Sign one change with two rules added to T15's pass: sign only where the seat's person is of the harness and the
        target credential is that person's stored passkey (else a finding, not signed); and sign only as persons whose own seat reads
        the list names as able (`maySign`), never the stale seat's owner, and — where they have a seat row in the seats view — reading
        `onRoster: true` there; a signer the list names with no seat row is able on the list's word alone (§2, amended). Where such
        persons are fewer than requiredSignatures, S4 fails naming the count. Returns the outcome and the words for the line.
        """
        pending_tx_id = str(change.get("pendingTxId"))
        seat = change.get("seat") if isinstance(change.get("seat"), dict) else {}
        required = change.get("requiredSignatures")
        own_short = T.credential_short_form(owner.credential_id) if owner.credential_id else None
        target = seat.get("newCredentialId")
        # §2 rule 1: the change must move the seat of a harness person to that person's stored passkey, or it is not signed.
        if self.person_by_email(seat.get("email")) is None or target != own_short:
            said = "change %s moves %s's seat to a credential the harness does not hold; not signed" % (pending_tx_id, seat.get("name") or seat.get("email") or owner.name)
            self.finding(station, "roster change %s…: the target credential the harness holds" % T.credential_short_form(pending_tx_id), None, None,
                         "the change moves %s's seat to their stored passkey %s (short form)" % (owner.name, own_short), said)
            return "not_signed", said

        def able(name: Any) -> Optional[Person]:
            signer = self.person_named(name)
            if signer is None or not signer.signed_in or signer.email.lower() == owner.email.lower():
                return None  # the stale seat's owner never signs her own move (§2)
            row = seats_by_email.get(signer.email.lower())
            # A signer WITH a seat row must read onRoster true there; a signer the list names with NO seat row is able on the list's word
            # alone — Ben and Cora on Harness Holdings, whose charter seats only Ada under C11 while the whitelist roster carries all
            # three (§2, amended 23 September 2026; the earlier rule required a seat row of every signer, which here leaves nobody able).
            if isinstance(row, dict) and row.get(T.SEAT_ON_ROSTER) is not True:
                return None
            return signer

        may = list(change.get("maySign") or [])
        able_names = [name for name in may if able(name) is not None]
        if isinstance(required, int) and len(able_names) < required:
            # a person whose current key is not on the roster cannot sign (§2): fewer able than the count asks
            return "count_short", "%d required, %d able" % (required, len(able_names))
        spoken = ["found awaiting at %s of %s, %s able to sign" % (change.get("signaturesCollected"), required, names_in_words(able_names) or "nobody")]
        collected = change.get("signaturesCollected")
        for name in may:
            signer = able(name)
            if signer is None:
                continue  # named as able by the list, but their own seat does not read on the roster (§2)
            answer, body = self.sign_roster_change_as(station, signer, pending_tx_id, owner.name, required)
            if body is None:
                spoken.append("%s refused (%s)" % (signer.name, answer.sentence()))  # the estate's words, verbatim; never retried
                continue
            required = body.get("requiredSignatures") or required
            collected = body.get("signaturesCollected")
            spoken.append("%s counted (%s of %s)" % (signer.name, collected, required))
            if body.get("state") == "applied":
                moved, words = self._confirm_seat_onroster(station, founder, owner, collected, required, body)
                spoken.append(words)
                return ("moved" if moved else "not_moved"), "; ".join(spoken)
        spoken.append("nobody left to sign, and the estate did not report the change applied")
        return "awaiting", "; ".join(spoken)

    def _confirm_seat_onroster(self, station: str, founder: Person, owner: Person, collected: Any, required: Any,
                               body: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Spec T17 §2. After the count is met, re-read GET /v1/approver-seats up to three times over a bounded wait, and say `moved` only
        on a read where the owner's seat reads `onRoster: true`; otherwise fail naming the seat and `<k> of <n> signatures`. A moved
        seat is recorded in `facts["seats_moved"]` for S6 and S10. Returns whether the seat read on the roster, and the words.
        """
        for attempt in range(SEAT_REREAD_ATTEMPTS):
            seats_view = self.read_seats(station, founder,
                "%s's seat reading onRoster true after the count (AER 360 Spec 105)" % owner.name)
            row = self.seat_of(seats_view, owner.email)
            if isinstance(row, dict) and row.get(T.SEAT_ON_ROSTER) is True:
                if body is not None:  # a signed move; a "moved at once" grant has no ceremony and no signers to record for S10
                    self._record_seat_moved(owner, body)
                return True, "moved: %s's seat now reads on the roster%s" % (
                    owner.name, (", signed by %s" % (names_in_words([str(s.get("name")) for s in (body or {}).get("signedBy") or [] if isinstance(s, dict)]) or "nobody the estate names")) if body else "")
            if attempt < SEAT_REREAD_ATTEMPTS - 1:
                self.sleep(SEAT_REREAD_WAIT_SECONDS)
        count = "%s of %s signatures" % (0 if collected is None else collected, 0 if required is None else required)
        self.finding(station, "roster change: %s's seat after the count" % owner.name, None, None,
                     "%s's seat reading onRoster true (AER 360 Spec 105)" % owner.name,
                     "%s's seat did not read on the roster after the count: %s" % (owner.name, count))
        return False, "%s's seat did not read on the roster: %s" % (owner.name, count)

    def _record_seat_moved(self, owner: Person, body: Optional[Dict[str, Any]]) -> None:
        """Record a seat S4 moved this run, for S6 (a not-counted press of theirs is a finding) and S10 (the trail's `roster.seat_rebound`)."""
        body = body or {}
        signers = [str(s.get("name")) for s in body.get("signedBy") or [] if isinstance(s, dict)]
        pending_tx_id = body.get("pendingTxId")
        if any(m.get("key") == owner.key for m in self.facts["seats_moved"]):
            return
        self.facts["seats_moved"].append({
            "email": owner.email.lower(), "key": owner.key, "name": owner.name,
            "pendingTxId": str(pending_tx_id) if pending_tx_id else None,
            "signers": signers, "signer_credentials": [s.get("credentialId") for s in body.get("signedBy") or [] if isinstance(s, dict)],
            "new_credential": owner.credential_id, "rebound": body.get("rebound"), "roster": (body.get("rebound") or {}).get("rosterName")})

    def propose_the_move_afresh(self, station: str, founder: Person, seat: Optional[Dict[str, Any]]) -> str:
        """
        The road the estate names for a move that must be proposed afresh (packages/shared/src/enrolment.ts, the expired sentence: "Granting
        <who>'s seat again in this room, or <who> redeeming a fresh invitation, proposes the move afresh"): the founder grants the seat again,
        POST /v1/approver-seats/grant, and Spec 95's rebind presents the move to the platform, which holds it as a ceremony the estate now
        records against the seat. Where the change names a seat, its owner's; where it names none, each seat the charter names for a person
        of the harness (`facts["seats"]`, the seats view S4 read), so that nothing is matched to a seat by guesswork.
        """
        if seat is not None:
            people = [self.person_by_email(seat.get("email"))]
            if people[0] is None:
                return "the seat's owner, %s, is not one of the harness's people, so nothing was proposed afresh" % seat.get("email")
        else:
            view = self.facts.get("seats") if isinstance(self.facts.get("seats"), dict) else {}
            people = [self.person_by_email(s.get("email")) for s in view.get("seats") or [] if isinstance(s, dict) and s.get("state") == "seated"]
            people = [p for p in people if p is not None]
            if not people:
                return "the charter's seats name no person of the harness, so nothing was proposed afresh"
        words: List[str] = []
        for person in people:
            body = {"email": person.email}
            expected = ("the seats view, and Spec 95 proposing %s's move afresh at the seat grant — the estate proposes a move at a seat grant or a redemption, "
                        "not at a sign-in — so the roster changes list it awaiting" % person.name)
            granted = self.request(founder, "POST", "/v1/approver-seats/grant", body, station)
            self.step(station, granted, expected, "granted again" if granted.ok else granted.sentence(), body, founder.name)
            if granted.ok and isinstance(granted.json, dict):
                self.facts["seats"] = granted.json
                words.append("the founder granted %s's seat again so Spec 95 proposes the move afresh" % person.name)
            else:
                words.append("the grant of %s's seat answered %s" % (person.name, granted.sentence()))
        return "; ".join(words)

    def sign_as_the_list_names(self, station: str, founder: Person, change: Dict[str, Any], record: Dict[str, Any]) -> Tuple[str, str]:
        """
        One awaiting change: sign in turn as each person the list names as able to sign, reading signaturesCollected after each, until the
        estate reports it applied. A person the harness holds no session for is reported and passed over; a refusal is reported in the
        estate's words and the next person signs. Returns the outcome (applied, approved, awaiting) and the words for the line.
        """
        pending_tx_id = record["pendingTxId"]
        seat = record["seat"] or {}
        owner = self.person_by_email(seat.get("email"))
        who = seat.get("name") or seat.get("email")
        required = change.get("requiredSignatures")
        spoken = ["found awaiting at %s of %s, %s able to sign" % (change.get("signaturesCollected"), required, names_in_words(change.get("maySign") or []) or "nobody")]
        for name in change.get("maySign") or []:
            signer = self.person_named(name)
            if signer is None or not signer.signed_in:
                spoken.append("%s named as able to sign, but the harness holds no session for them" % name)
                continue
            answer, body = self.sign_roster_change_as(station, signer, pending_tx_id, who, required)
            entry = {"who": signer.name, "key": signer.key, "credential": signer.credential_id, "status": answer.status,
                     "answer": body if body is not None else answer.sentence(), "refusal_code": (answer.refusal or {}).get("code") if answer.refusal else None}
            record["signatures"].append(entry)
            if body is None:
                spoken.append("%s refused (%s)" % (signer.name, answer.sentence()))  # the estate's words, verbatim; never retried
                continue
            required = body.get("requiredSignatures") or required
            spoken.append("%s counted (%s of %s)" % (signer.name, body.get("signaturesCollected"), required))
            state = body.get("state")
            if state == "applied":
                record["rebound"] = body.get("rebound")
                spoken.append("applied: %s" % self.assert_the_seat_moved(station, founder, pending_tx_id, body, owner, who))
                return "applied", "; ".join(spoken)
            if state == "approved":
                # the count is met and the platform holds the change approved and unapplied — reopened, or held — in the estate's sentence
                spoken.append(str(body.get("sentence")))
                return "approved", "; ".join(spoken)
        return "awaiting", "; ".join(spoken + ["nobody left to sign, and the estate did not report the change applied"])

    def sign_roster_change_as(self, station: str, signer: Person, pending_tx_id: str, who: Any, required: Any) -> Tuple[Answer, Optional[Dict[str, Any]]]:
        """
        One signature, as the signer (Spec 99, item 2): the options road first, whose challenge the estate derives from the binding
        `roster-change:<workspace id>:<pendingTxId>:<issuedAtMs>` | the signer's credential | `roster.change`, then the press with issuedAtMs
        and the passkey's assertion, once and never retried (an assertion cannot be sent twice). Returns the answer and its body where it counted.
        """
        opened = self.request(signer, "POST", T.ROSTER_CHANGE_SIGN_OPTIONS_ROUTE % pending_tx_id, {}, station)
        self.step(station, opened, "200 with options (the challenge the estate derives from %s under the purpose %s) and issuedAtMs" % (
            T.ROSTER_CHANGE_BINDING % ("<workspace id>", pending_tx_id, "<issuedAtMs>"), T.ROSTER_CHANGE_PURPOSE), "answered" if opened.ok else opened.sentence(), {}, signer.name)
        if not opened.ok or not isinstance(opened.json, dict) or not isinstance(opened.json.get("options"), dict):
            return opened, None
        assertion = self.assertion_for(signer, str(opened.json["options"].get("challenge")), station)
        body = {"issuedAtMs": opened.json.get("issuedAtMs"), "response": assertion}
        expected = ("%s's signature counted: signaturesCollected of %s, state awaiting until the count is met, then applied with rebound naming %s's current credential; "
                    "a refusal is judged for Rule 13 and reported in the estate's words, never retried" % (signer.name, required, who))
        signed = self.request(signer, "POST", T.ROSTER_CHANGE_SIGN_ROUTE % pending_tx_id, body, station, retry=False)
        counted = signed.ok and isinstance(signed.json, dict)
        result = ("counted: %s of %s, %s" % (signed.json.get("signaturesCollected"), signed.json.get("requiredSignatures"), signed.json.get("state"))) if counted else self.refusal_judged(signed)
        self.step(station, signed, expected, result, body, signer.name)
        return signed, (signed.json if counted else None)

    @staticmethod
    def refusal_judged(answer: Answer) -> str:
        """A refusal judged for Rule 13 as S10 judges every refusal (`refusal_without_why`): it names what happened and who refused, or it does not; S10 raises the finding."""
        why = refusal_without_why(answer.status, answer.text)
        if why:
            return "refused without saying why (Rule 13, raised by S10): %s — %s" % (why, answer.sentence())
        return "refused, and the refusal says why (Rule 13): %s" % answer.sentence()

    def assert_the_seat_moved(self, station: str, founder: Person, pending_tx_id: str, body: Dict[str, Any], owner: Optional[Person], who: Any) -> str:
        """
        Spec T15 §1, the assertion after the count: the roster changes are read again and the change must read applied, its seat naming the
        owner's current credential in the estate's short form (its first eight characters, `credentialIdShortForm`), as must the signature's
        own `rebound`. A seat that names another credential is a finding in the estate's words; a move asserted is recorded for S6 and S10.
        """
        own = owner.credential_id if owner is not None and owner.signed_in else None
        short_own = T.credential_short_form(own) if own else None
        expected = "the change %s… applied, its seat naming %s's current credential %s (short form %s)" % (
            T.credential_short_form(pending_tx_id), who, last4(own) if own else "(no session to compare with)", short_own)
        answer, view = self.read_roster_changes(station, founder, expected)
        listed = next((c for c in (view.get("changes") or []) if isinstance(c, dict) and str(c.get("pendingTxId")) == pending_tx_id), None) if view else None
        listed_names = ((listed or {}).get("seat") or {}).get("newCredentialId") if listed else None
        rebound_names = (body.get("rebound") or {}).get("newCredentialId") if isinstance(body.get("rebound"), dict) else None
        signers = [str(s.get("name")) for s in body.get("signedBy") or [] if isinstance(s, dict)]
        moved = {"email": str((body.get("rebound") or {}).get("email") or (owner.email if owner else "")).lower(), "key": owner.key if owner else None, "name": who,
                 "pendingTxId": pending_tx_id, "signers": signers, "signer_credentials": [s.get("credentialId") for s in body.get("signedBy") or [] if isinstance(s, dict)],
                 "new_credential": own, "rebound": body.get("rebound"), "roster": (body.get("rebound") or {}).get("rosterName")}
        if own is None:
            self.facts["seats_moved"].append(moved)
            return "the estate reports the seat moved (%s); %s has no session, so the credential was not compared" % (rebound_names, who)
        if listed is not None and listed.get("state") == "applied" and listed_names == short_own and rebound_names == short_own:
            self.facts["seats_moved"].append(moved)
            return "the seat now names %s, %s's current credential (%s), signed by %s" % (short_own, who, last4(own), names_in_words(signers) or "nobody the estate names")
        self.finding(station, "roster change %s…: the seat after the count" % T.credential_short_form(pending_tx_id), None, answer, expected,
                     "the register lists the change %s, its seat naming %s; the signature's answer named %s" % (
                         listed.get("state") if listed else "not at all", listed_names, rebound_names))
        return "the seat did not read as moved: listed %s, naming %s" % (listed.get("state") if listed else "not at all", listed_names)

    def seat_moved_for(self, person: Person) -> Optional[Dict[str, Any]]:
        """The seat S4 moved for this person in this run, or None (Spec T15 §2, §3)."""
        return next((m for m in self.facts.get("seats_moved") or [] if m.get("key") == person.key), None)

    # -- S5 Wallet account ---------------------------------------------------------------
    def station_s5(self) -> Outcome:
        founder = self.founder()
        interview_id, page, answered = self.walk_interview("S5", "wallet_account", founder)
        compiled = self.confirm_and_compile("S5", "wallet_account", interview_id, founder, page)
        wallets = self.request(founder, "GET", "/v1/aer360/wallets", None, "S5")
        self.step("S5", wallets, "the Wallets register with the operating account, or the register's own absence sentence",
                  "answered" if wallets.ok else wallets.sentence(), None, founder.name)
        self.facts["wallets"] = wallets.json if isinstance(wallets.json, dict) else None
        view = self.read_journey("S5", founder)
        current = view.get("currentStage")
        current_id = next((s.get("id") for s in view.get("stages") or [] if s.get("current")), None)
        charter = compiled.get("charter") or {}
        register_said = "not read"
        if isinstance(wallets.json, dict):
            answer = wallets.json.get("answer")
            if answer is None:
                register_said = "the Wallets register answered no rows: %s" % wallets.json.get("absence")
            else:
                names = [m.get("walletName") for m in (answer.get("matches") or [])]
                register_said = "the Wallets register lists %s" % (names or "no wallets")
        detail = "wallet account: %d questions answered, charter compiled (%s, purpose %s, per payment hold %s cents, daily %s cents, destinations %s); %s; journey stage %s of %s (%s)" % (
            answered, charter.get("name"), charter.get("purpose"), (charter.get("amountsUsdCents") or {}).get("holdOverPerTx"),
            (charter.get("amountsUsdCents") or {}).get("dailyTotal"), charter.get("whitelistMode"), register_said, current, view.get("stageCount"), current_id)
        # Spec T13 §1 and §2: S5 ends by giving the estate its funding wallet, and funding it from the faucet as the founder would
        funding_said, wallet_failed = self.give_the_estate_its_funding_wallet("S5", founder)
        detail += "; %s; %s" % (funding_said, self.fund_the_wallet_from_the_faucet("S5", founder))
        if not isinstance(current, int) or current < 3:
            return Outcome("S5", FAIL, detail + "; expected stage 3 of %d, working_the_sandbox" % JOURNEY_STAGE_COUNT)
        if current > 3:
            detail += " (beyond stage 3: this estate had walked further before this run)"
        if wallet_failed:
            return Outcome("S5", FAIL, detail)
        return Outcome("S5", PASS, detail)

    # -- S5's tail: the funding wallet and the faucet (Spec T13) -----------------------------------
    def give_the_estate_its_funding_wallet(self, station: str, founder: Person) -> Tuple[str, bool]:
        """
        Spec T13 §1. GET /v1/workspace first: a wallet already born is reported and never pressed for again, so
        FUNDING_WALLET_ALREADY_BORN is never met. Where `fundingWalletAbsence` stands, the founder presses: the options road
        answers the challenge the estate derives from `funding-wallet:<workspace id>:<issuedAtMs>` under the purpose
        `workspace.funding_wallet`, the passkey signs it, and POST /v1/workspace/funding-wallet carries issuedAtMs and the
        assertion — once, never retried, because an assertion cannot be sent twice. The workspace is read again and the line says
        "funding wallet: <address> on <home stack>, key <id>". A refusal is told in the estate's words — WALLET_BIRTH_REFUSED
        carries the gateway's sentence; GATEWAY_UNAVAILABLE is a fault — and S5 fails naming it. An estate before Spec 98, whose
        workspace answers neither field, has no press to make; that is reported and S5 is not failed for it.
        Returns the line and whether S5 fails.
        """
        workspace = self.request(founder, "GET", "/v1/workspace", None, station)
        self.step(station, workspace, "the workspace with fundingWallet (address, keyId, homeStack, bornAt, sentence) or fundingWalletAbsence (Spec 98)",
                  "answered" if workspace.ok else workspace.sentence(), None, founder.name)
        self.facts["workspace"] = workspace.json if isinstance(workspace.json, dict) else None
        if not workspace.ok or not isinstance(workspace.json, dict):
            return "funding wallet: not read — GET /v1/workspace answered %s" % workspace.sentence(), True
        wallet = workspace.json.get("fundingWallet")
        absence = workspace.json.get("fundingWalletAbsence")
        if isinstance(wallet, dict) and wallet.get("address"):
            self.facts["funding_wallet"] = wallet
            return "%s (already born; not pressed for again)" % self.funding_wallet_words(wallet), False
        if "fundingWallet" not in workspace.json and "fundingWalletAbsence" not in workspace.json:
            said = ("funding wallet: the workspace answers neither fundingWallet nor fundingWalletAbsence — an estate before AER 360 Spec 98, "
                    "with no press for a funding wallet; sourceAccount %s" % json.dumps(workspace.json.get("sourceAccount")))
            self.note(station, said)
            return said, False
        self.facts["funding_wallet_absence"] = absence
        options = self.request(founder, "POST", FUNDING_WALLET_OPTIONS_ROUTE, {}, station)
        self.step(station, options, "200 with options (the challenge the estate derives from %s under the purpose %s) and issuedAtMs" % (
            FUNDING_WALLET_BINDING % ("<workspace id>", "<issuedAtMs>"), FUNDING_WALLET_PURPOSE), "answered" if options.ok else options.sentence(), {}, founder.name)
        if not options.ok or not isinstance(options.json, dict) or not isinstance(options.json.get("options"), dict):
            self.facts["funding_press"] = {"route": FUNDING_WALLET_OPTIONS_ROUTE, "status": options.status, "answer": options.sentence(),
                                           "refusal_code": (options.refusal or {}).get("code") if options.refusal else None}
            return "funding wallet: not born — the options road answered %s" % options.sentence(), True
        challenge = str(options.json["options"].get("challenge"))
        body = {"issuedAtMs": options.json.get("issuedAtMs"), "response": self.assertion_for(founder, challenge, station)}
        pressed = self.request(founder, "POST", FUNDING_WALLET_ROUTE, body, station, retry=False)
        self.step(station, pressed, "200: born true, fundingWallet {address, keyId, homeStack, bornAt, sentence}; a refusal in the estate's words "
                  "(%s carries the gateway's sentence; %s is a fault)" % (WALLET_BIRTH_REFUSED, GATEWAY_UNAVAILABLE),
                  "born" if pressed.ok else pressed.sentence(), body, founder.name)
        refusal = pressed.refusal or {}
        code = refusal.get("code") if pressed.refusal else None
        detail_of_refusal = refusal.get("detail") if isinstance(refusal.get("detail"), dict) else {}
        self.facts["funding_press"] = {"route": FUNDING_WALLET_ROUTE, "status": pressed.status, "issuedAtMs": body["issuedAtMs"],
                                       "answer": pressed.json if pressed.ok and isinstance(pressed.json, dict) else pressed.sentence(),
                                       "refusal_code": code, "gateway_said": detail_of_refusal.get("gatewaySaid")}
        if not pressed.ok:
            kind = "a fault" if code == GATEWAY_UNAVAILABLE else "refused"
            return "funding wallet: not born — %s: %s" % (kind, pressed.sentence()), True
        pressed_wallet = pressed.json.get("fundingWallet") if isinstance(pressed.json, dict) and isinstance(pressed.json.get("fundingWallet"), dict) else {}
        again = self.request(founder, "GET", "/v1/workspace", None, station)
        self.step(station, again, "the workspace with the funding wallet just born: %s" % self.funding_wallet_words(pressed_wallet),
                  "answered" if again.ok else again.sentence(), None, founder.name)
        self.facts["workspace"] = again.json if isinstance(again.json, dict) else self.facts["workspace"]
        read_back = again.json.get("fundingWallet") if again.ok and isinstance(again.json, dict) else None
        if not isinstance(read_back, dict) or not read_back.get("address"):
            self.finding(station, "the funding wallet read back after the press", {"issuedAtMs": body["issuedAtMs"], "response": "<assertion>"}, again,
                         "fundingWallet carrying the address the press answered (%s)" % pressed_wallet.get("address"),
                         "GET /v1/workspace after the press answers %s" % (again.sentence() if not again.ok else json.dumps(
                             {k: again.json.get(k) for k in ("fundingWallet", "fundingWalletAbsence")}, ensure_ascii=False)))
            self.facts["funding_wallet"] = pressed_wallet or None
            return "%s — the press answered born and the workspace read back does not carry it" % self.funding_wallet_words(pressed_wallet), True
        if pressed_wallet.get("address") and str(pressed_wallet["address"]).lower() != str(read_back["address"]).lower():
            self.finding(station, "the funding wallet read back after the press", None, again, "the address the press answered, %s" % pressed_wallet["address"],
                         "the workspace reads back %s" % read_back["address"])
        self.facts["funding_wallet"] = read_back
        return "%s (born by this run's press)" % self.funding_wallet_words(read_back), False

    @staticmethod
    def funding_wallet_words(wallet: Dict[str, Any]) -> str:
        """The spec's line, funding wallet: <address> on <home stack>, key <id>; a record naming no stack says so, as the estate's own sentence does."""
        stack = wallet.get("homeStack")
        return "funding wallet: %s on %s, key %s" % (wallet.get("address"), stack if stack else "a stack the record does not name", wallet.get("keyId"))

    @staticmethod
    def outside_sentence(answer: Answer) -> str:
        """What a road that is not the estate's answered: a fault's words at status 0, else the status and the body verbatim."""
        if answer.status == 0:
            return "could not be reached: %s" % answer.text
        return "HTTP %d: %s" % (answer.status, answer.text[:300] or "<empty>")

    def read_native_balance(self, station: str, founder: Person, address: str) -> Tuple[Optional[int], str]:
        """
        Spec T13 §2: the funding wallet's native balance on the AEREDIUM testnet, in wei. The estate offers a browser no live
        balance of its funding wallet (routes/*.ts carry no such road; GET /v1/aer360/wallets is the daily close's record, in the
        base currency), so the chain's public RPC named in the faucet record is read — eth_getBalance, as the corridor reads a
        chain. A fault is reported in the RPC's own words and answers None: the harness never invents a balance.
        """
        body = {"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [address, "latest"]}
        answer = self.request_outside(founder.name, "POST", T.TESTNET_RPC_URL, body, station)
        self.step(station, answer, "a hex quantity: the funding wallet's native balance in wei on %s (chain %d, %s); a fault is reported and the faucet is not asked" % (
            T.TESTNET_NAME, T.TESTNET_CHAIN_ID, T.NATIVE_COIN), "answered" if answer.ok else self.outside_sentence(answer), body, founder.name)
        if answer.status == 0:
            return None, "the RPC at %s could not be reached: %s" % (T.TESTNET_RPC_URL, answer.text)
        parsed = answer.json
        if not isinstance(parsed, dict):
            return None, "the RPC at %s answered HTTP %d without JSON: %s" % (T.TESTNET_RPC_URL, answer.status, answer.text[:200] or "<empty>")
        if parsed.get("error") is not None:
            return None, "the RPC at %s refused eth_getBalance: %s" % (T.TESTNET_RPC_URL, json.dumps(parsed["error"], ensure_ascii=False))
        result = parsed.get("result")
        if not isinstance(result, str) or not result.startswith("0x"):
            return None, "the RPC at %s answered %r for eth_getBalance, which is not a hex quantity" % (T.TESTNET_RPC_URL, result)
        try:
            wei = int(result, 16)
        except ValueError:
            return None, "the RPC at %s answered %r for eth_getBalance, which is not a number" % (T.TESTNET_RPC_URL, result[:80])
        return wei, "%s %s (%d wei) read from %s" % (T.coin_amount(wei), T.NATIVE_COIN, wei, T.TESTNET_RPC_URL)

    def fund_the_wallet_from_the_faucet(self, station: str, founder: Person) -> str:
        """
        Spec T13 §2: with the wallet present and its native balance below GAS_FLOOR_SEAR, the wallet's address is POSTed to the
        faucet as JSON {"address": …}, exactly as the faucet page does, once per run, and the answer is reported verbatim — paid
        and tx_hash, or the faucet's own refusal sentence. Never twice in one run; never on a balance the harness did not read.
        This is gas only: what the payments move is S7's question.
        """
        wallet = self.facts.get("funding_wallet")
        if not isinstance(wallet, dict) or not wallet.get("address"):
            return "faucet: not asked — the estate has no funding wallet to fund"
        if self.facts.get("faucet") is not None:
            return "faucet: asked once already in this run — %s" % self.facts["faucet"]["said"]
        address = str(wallet["address"])
        wei, balance_said = self.read_native_balance(station, founder, address)
        self.facts["gas_balance"] = {"wei": wei, "said": balance_said, "address": address}
        if wei is None:
            self.note(station, "gas: %s; the faucet was not asked, because the harness never invents a balance" % balance_said)
            return "gas: %s; the faucet was not asked (the harness never invents a balance)" % balance_said
        if wei >= T.GAS_FLOOR_WEI:
            return "gas: %s, at or above %s %s; the faucet was not asked" % (balance_said, T.GAS_FLOOR_SEAR, T.NATIVE_COIN)
        body = {"address": address}
        answer = self.request_outside("%s (at the faucet page)" % founder.name, "POST", T.FAUCET_REQUEST_URL, body, station)
        said = self.faucet_words(answer)
        self.step(station, answer, "paid true and tx_hash (%s %s), or the faucet's own refusal sentence — verbatim, once per run (its limits: %s)" % (
            T.FAUCET_PAYS_SEAR, T.NATIVE_COIN, T.FAUCET_LIMITS), said, body, "%s (at the faucet page)" % founder.name)
        self.facts["faucet"] = {"status": answer.status, "answer": answer.json if isinstance(answer.json, dict) else answer.text, "said": said, "address": address, "at": now_iso()}
        return "gas: %s, below %s %s; %s" % (balance_said, T.GAS_FLOOR_SEAR, T.NATIVE_COIN, said)

    @staticmethod
    def faucet_words(answer: Answer) -> str:
        """
        The faucet's answer in its own words, read as its page reads them (aeredium/faucet, internal/faucet/server_manual.go:
        handleRequest and autoPayRequest): ok and paid with tx_hash; ok and queued where a send failed and the row waits for the
        admin queue; ok alone in manual mode; else `error`, the faucet's plain-language reason, at its status.
        """
        if answer.status == 0:
            return "the faucet could not be reached: %s" % answer.text
        body = answer.json if isinstance(answer.json, dict) else None
        if body is not None and answer.ok and body.get("ok") is True:
            if body.get("paid") is True and body.get("tx_hash"):
                return "the faucet paid: paid true, tx_hash %s%s" % (body["tx_hash"], (", times_paid %s" % body["times_paid"]) if "times_paid" in body else "")
            return "the faucet saved the request without paying (%s): %s" % ("queued for its admin queue" if body.get("queued") else "manual mode", json.dumps(body, ensure_ascii=False))
        if body is not None and body.get("error"):
            return "the faucet refused (HTTP %d): %s" % (answer.status, body["error"])
        return "the faucet answered HTTP %d: %s" % (answer.status, answer.text[:300] or "<empty>")

    def funding_summary_lines(self) -> List[str]:
        """Spec T13 §5: the report's summary names the funding wallet, so the faucet and the asset can be checked by eye."""
        wallet = self.facts.get("funding_wallet")
        press = self.facts.get("funding_press")
        lines: List[str] = []
        if isinstance(wallet, dict) and wallet.get("address"):
            lines.append("%s (GET /v1/workspace; %s/address/%s)." % (self.funding_wallet_words(wallet).replace("funding wallet:", "Funding wallet:", 1), T.TESTNET_EXPLORER_URL, wallet["address"]))
        elif self.facts.get("funding_wallet_absence"):
            lines.append("Funding wallet: none — %s%s" % (self.facts["funding_wallet_absence"],
                                                        (" The press answered %s." % press["answer"]) if isinstance(press, dict) and not isinstance(press.get("answer"), dict) else ""))
        else:
            lines.append("Funding wallet: not read in this run.")
        gas = self.facts.get("gas_balance")
        faucet = self.facts.get("faucet")
        if isinstance(gas, dict):
            lines.append("Gas: %s%s" % (gas["said"], ("; %s." % faucet["said"]) if isinstance(faucet, dict) else "; the faucet was not asked."))
        treasury = self.facts.get("treasury")
        if isinstance(treasury, dict) and treasury.get("address"):
            lines.append("Harness Treasury: funding wallet %s — the float Bear funds with %s on %s, once; it pays Harness Holdings' shortfall through the estate's own road, and the harness holds no key for it (Spec T14)." % (
                treasury["address"], T.PAYMENT_ASSET, T.PAYEE_CHAIN))
        lines.append("The asset: the three payments together need %s of %s; Harness Treasury pays Harness Holdings the shortfall through the estate's own road (Spec T14); the harness never mints the asset and holds no key." % (
            self.payments_need()[1], T.PAYMENT_ASSET))
        return lines

    @staticmethod
    def payments_need() -> Tuple[str, str]:
        """What the three payments need together: the plain total of the asset, and the same figure as US dollars (USDC is the dollar-pegged asset, Spec T11 §4)."""
        total = T.payments_total([p.amount for p in A.PAYMENTS], T.ASSET_DECIMALS[T.PAYMENT_ASSET])
        return total, usd(int(T.minor_units(total, 2)))

    # -- S6 Payees ----------------------------------------------------------------------
    # Spec T9 (20 September 2026): who presses after Ada, and how a count is spoken. Ben Signatory, who signs
    # changes to the rules, is the presser the harness falls back to when the estate's answer names nobody for
    # whom it holds a session; the count words are the ones the estate's own sentence uses ("One more is needed").
    FALLBACK_PRESSER = "ben"
    COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}

    def station_s6(self) -> Outcome:
        """
        Two payees, each created and promoted by the founder, then approved until the whitelist roster's quorum
        is met (Spec T9, 20 September 2026, from the second live run, report aer360-harness-2026-09-20-103245.md).

        The charter Harness Holdings confirmed answered C12 = 2 and C12A = No, so the `whitelist_mutation`
        roster's threshold is two and its members are the census of A8 (`governanceSignersFor`,
        onboardingcompiler.ts): Harriet Founder, Ada Approver, Ben Signatory, Cora Clerk — the answer book's
        WHITELIST_ROSTER at WHITELIST_QUORUM. The second live run pressed once, as Ada, and called the estate's
        honest `pending_promotion` a failure; the audit row said why: requiredSignatures 2, signaturesCollected 1.
        Under Spec 89 (aeredium/AERAccounts, commit 7d809e1, routes/payees.ts and services/payees.ts) the first
        approval's answer says so itself — `approvals {required, collected, remaining}`, `may_still_approve` with
        the roster's unsigned names, and the sentence "1 of 2 approvals recorded for this address. One more is
        needed, from …" — and the harness presses on (§1): after Ada, the first name in may_still_approve for whom
        it holds a signed-in session, else Ben Signatory, else the founder, until whitelisted, a refusal, or
        approvals.required presses, whichever is first, and never more times than the roster has names (§3). An
        estate before Spec 89 answers without approvals; one further press is made as Ben, on the charter's quorum
        of two, and the report says so.

        The first approval's answer is audited (§2): a pending answer that does not say why is a finding of S10's
        kind raised here, and so is a quorum that exceeds its roster, or a sentence that does not begin with its
        count. Each step says what it expects (§3), and the register's status is read from the row whose id is
        this run's payee id, never by address: every run creates its payees afresh, the register is ordered by
        display name (routes/payees.ts), and earlier runs leave rows with the same addresses still pending.
        """
        founder = self.founder()
        said: List[str] = []
        all_whitelisted = True
        for payee in T.PAYEES:
            address = T.address(payee["key"])
            body = {"displayName": payee["name"], "defaultAsset": T.PAYMENT_ASSET, "defaultChain": payee["chain"],
                    "addresses": [{"chain": payee["chain"], "address": address}]}
            created = self.request(founder, "POST", "/v1/payees", body, "S6")
            self.step("S6", created, "201 with the payee and its proposed address", "created" if created.ok else created.sentence(), body, founder.name)
            if not created.ok or not isinstance(created.json, dict):
                said.append("%s: %s" % (payee["name"], created.sentence()))
                all_whitelisted = False
                continue
            row = created.json.get("payee") or {}
            addresses = row.get("addresses") or []
            address_id = str(addresses[0].get("id")) if addresses else None
            record = {"key": payee["key"], "name": payee["name"], "payee_id": row.get("id"), "address_id": address_id, "address": address, "chain": payee["chain"],
                      "promoted": None, "approved": None, "presses": []}
            self.facts["payees"].append(record)
            if not address_id:
                said.append("%s: created with no address id" % payee["name"])
                all_whitelisted = False
                continue
            promoted = self.request(founder, "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, "S6")
            self.step("S6", promoted, "a ceremony: status pending_promotion, platformMembershipId, ceremony", "answered" if promoted.ok else promoted.sentence(), {}, founder.name)
            record["promoted"] = promoted.json if promoted.ok else promoted.sentence()
            promote_said = "promoted" if promoted.ok else "promote answered %s" % promoted.sentence()
            said.append("%s: created; %s; %s" % (payee["name"], promote_said, self.approve_to_quorum(record)))
        # Spec T13 §3: the register is the judge, not the press. After the presses, GET /v1/payees decides each payee on its
        # whitelistStatus; a register that reads proposed after the platform counted the quorum fails with the mirror sentence.
        register = self.request(founder, "GET", "/v1/payees", None, "S6")
        self.step("S6", register, "the payees register with both addresses whitelisted, read by this run's payee ids — the judgement is the register's, not the press's (Spec T13 §3)",
                  "answered" if register.ok else register.sentence(), None, founder.name)
        self.facts["payees_register"] = register.json if isinstance(register.json, dict) else None
        for record in self.facts["payees"]:
            status = self.register_status_of(register.json, record)
            record["register_status"] = status
            record["mirror"] = self.mirror_sentence(record, status)
            if status != "whitelisted":
                all_whitelisted = False
        detail = "payees: %s; register: %s" % ("; ".join(said), ", ".join(
            "%s %s%s" % (r["name"], r.get("register_status"), (" (%s)" % r["mirror"]) if r.get("mirror") else "") for r in self.facts["payees"]) or "none")
        return Outcome("S6", PASS if all_whitelisted and self.facts["payees"] else FAIL, detail)

    @staticmethod
    def mirror_sentence(record: Dict[str, Any], register_status: str) -> Optional[str]:
        """
        Spec T13 §3: the register reads proposed after the platform counted the quorum — the estate's mirror disagrees with the
        platform, which is the truth until AER 360 Spec 100 ships and the register reads whitelisted on the next GET /v1/payees.
        """
        count = record.get("count")
        if register_status != "proposed" or not isinstance(count, dict):
            return None
        collected, required = count.get("collected"), count.get("required")
        if isinstance(collected, int) and isinstance(required, int) and required > 0 and collected >= required:
            return MIRROR_DISAGREES % (collected, required, register_status)
        return None

    def approve_to_quorum(self, record: Dict[str, Any]) -> str:
        """
        Spec T12 §2: press the roster people the harness holds a passkey for, in order (the founder last), on their
        current credential, until the estate answers whitelisted or nobody is left. Each press is recorded with the
        estate's answer verbatim; a press refused SIGNATURE_NOT_COUNTED — its seat bound to a retired credential the
        census cannot yet move (Spec 95 opened the ceremony, Spec 99 signs it) — is recorded and the next person
        presses. The line names who counted and who did not, and the outcome the estate last gave.
        """
        pressers = self.whitelist_pressers()
        if not pressers:
            return "no roster member has a session, so the whitelist was not pressed"
        quorum = A.WHITELIST_QUORUM
        required: Optional[int] = None  # the estate's own figure, read from the first answer that counted
        counted: List[str] = []
        spoken: List[str] = []
        outcome = "not answered"
        audited = False
        for presser in pressers:
            moved = self.seat_moved_for(presser)  # Spec T15 §2: S4 moved this person's roster seat to their current credential
            expected = self.press_expectation(len(counted) + 1, required if required is not None else quorum)
            if moved is not None:
                expected += " — S4 moved %s's roster seat to their current credential %s (ceremony %s…), so SIGNATURE_NOT_COUNTED is a finding (Spec T15 §2)" % (
                    presser.name, last4(presser.credential_id), T.credential_short_form(moved["pendingTxId"]))
            answer = self.request(presser, "POST", "/v1/payees/addresses/%s/approve" % record["address_id"], {}, "S6")
            self.step("S6", answer, expected, "answered" if answer.ok else answer.sentence(), {}, presser.name)
            body = answer.json if answer.ok and isinstance(answer.json, dict) else None
            code = (answer.refusal or {}).get("code") if answer.refusal else None
            record["presses"].append({
                "who": presser.name, "key": presser.key, "credential": presser.credential_id, "status": answer.status,
                "answer": body if body is not None else answer.sentence(),
                "refusal_code": code,
            })
            if body is None:
                spoken.append("%s not counted (%s)" % (presser.name, answer.sentence()))
                if code == SIGNATURE_NOT_COUNTED and moved is not None:
                    self.finding("S6", "a press not counted after S4 moved the seat: %s for %s" % (presser.name, record["name"]), {}, answer, expected,
                                 "not counted: %s — S4 had %s sign the move of %s's roster seat to %s (ceremony %s), and the estate reported it applied" % (
                                     answer.sentence(), names_in_words(moved.get("signers") or []) or "the census", presser.name, last4(presser.credential_id), moved["pendingTxId"]))
                if outcome == "not answered":
                    outcome = "pending_promotion"
                continue
            record["approved"] = body
            status = body.get("whitelistStatus")
            approvals = body.get("approvals") if isinstance(body.get("approvals"), dict) else None
            if not audited and status == "pending_promotion":
                self.audit_first_approval(record, answer, body)  # Spec T9 §2, on the first pending answer that counted
                audited = True
            if approvals is not None and isinstance(approvals.get("required"), int) and approvals["required"] > 0:
                required = approvals["required"]
            counted.append(presser.name)
            collected = approvals["collected"] if approvals is not None and isinstance(approvals.get("collected"), int) else len(counted)
            record["count"] = {"collected": collected, "required": required if required is not None else quorum}  # Spec T13 §3: what the platform counted
            spoken.append("%s counted (%s of %s)" % (presser.name, collected, required if required is not None else quorum))
            if status != "pending_promotion":
                outcome = str(status)
                break
            outcome = "pending_promotion"
        return "%s: %s" % ("; ".join(spoken) or "nobody pressed", outcome)

    def whitelist_pressers(self) -> List[Person]:
        """The roster people the harness holds a signed-in session for, in the charter's roster order, the founder last (Spec T12 §2)."""
        order = [k for k in A.CENSUS_ORDER if k != A.FOUNDER] + [A.FOUNDER]
        return [self.people[k] for k in order if k in self.people and self.people[k].signed_in]

    def press_expectation(self, press: int, required: int) -> str:
        """What the n-th press that counts should answer (Spec T9 §3): pending with the count and the sentence until the quorum's press, then whitelisted."""
        if press >= required:
            return "whitelistStatus whitelisted"
        remaining = required - press
        return ("whitelistStatus pending_promotion with %s more needed (%d of %d approvals recorded): approvals {required, collected, remaining}, "
                "may_still_approve naming the unsigned, and the sentence (Spec 89)" % (self.COUNT_WORDS.get(remaining, str(remaining)), press, required))

    def audit_first_approval(self, record: Dict[str, Any], answer: Answer, body: Dict[str, Any]) -> None:
        """
        Spec T9 §2: a pending first approval must say why (Spec 89) — approvals, may_still_approve and sentence beside its status —
        name a roster that can meet its quorum, and begin its sentence with its count. Each failing is a finding of S10's kind, raised
        here, carrying the answer verbatim. A null may_still_approve is the estate's honest answer where the platform's roster could
        not be read, and is not a missing field.
        """
        missing = [key for key in ("approvals", "may_still_approve", "sentence") if key not in body]
        if missing:
            self.finding("S6", "a pending approval that did not say why (Spec 89): %s" % record["name"], {}, answer,
                         "approvals {required, collected, remaining}, may_still_approve and sentence beside whitelistStatus pending_promotion (Spec 89)",
                         "the answer carried no %s" % " and no ".join(missing))
            return
        approvals = body.get("approvals")
        names = body.get("may_still_approve")
        sentence = body.get("sentence")
        required = approvals.get("required") if isinstance(approvals, dict) else None
        collected = approvals.get("collected") if isinstance(approvals, dict) else None
        if isinstance(required, int) and isinstance(collected, int) and isinstance(names, list) and required > len(names) + collected:
            self.finding("S6", "a quorum that exceeds its roster: %s" % record["name"], {}, answer,
                         "approvals.required no greater than the names in may_still_approve plus approvals.collected",
                         "approvals.required is %d, may_still_approve names %d and approvals.collected is %d, so the count can never be met" % (required, len(names), collected))
        if isinstance(required, int) and isinstance(collected, int) and isinstance(sentence, str):
            opening = "%d of %d %s recorded for this address." % (collected, required, "approval" if required == 1 else "approvals")
            if not sentence.startswith(opening):
                self.finding("S6", "a sentence that does not begin with its count (Spec 89): %s" % record["name"], {}, answer,
                             'a sentence beginning "%s"' % opening, 'the sentence is "%s"' % sentence)

    @staticmethod
    def register_status_of(register: Any, record: Dict[str, Any]) -> str:
        """The status of this run's own row — the payee whose id is this run's payee_id — never a lookup by address (Spec T9 §3)."""
        if not isinstance(register, dict):
            return "no register was read"
        for row in register.get("payees") or []:
            if str(row.get("id")) != str(record.get("payee_id")):
                continue
            addresses = row.get("addresses") or []
            for addr in addresses:
                if str(addr.get("id")) == str(record.get("address_id")):
                    return str(addr.get("whitelistStatus"))
            for addr in addresses:
                if str(addr.get("address", "")).lower() == str(record.get("address", "")).lower():
                    return str(addr.get("whitelistStatus"))
            return "in the register without its address"
        return "absent from the register"

    # -- S7 Payments (Spec T14, 22 September 2026, amended 22:35; built 24 September 2026) -------------------------------------------
    # The harness pays in cents, funds Harness Holdings from a treasury workspace whose key lives only in the enclave, credits the gas
    # account as the sandbox may, proves the gas refusal (S7a), and judges S7 on money that moved. Read from AER 360 Spec 104 and
    # platform Spec 154 (aer360_tables.py names the files and commits); every sentence the estate or the platform speaks travels verbatim.
    #
    # THE ORDER S7 WALKS, AND WHY — A DISAGREEMENT CARRIED TO BEAR, NOT SILENTLY RESOLVED. SPEC.md §3 says the two gas accounts are
    # credited AFTER S7a's refusal is proved; §2 says the Treasury pays Holdings' shortfall BEFORE S7. The Treasury's own payment is
    # quoted, sponsored and sent by the platform's gas roads, so it cannot leave until the Treasury's gas account holds gas; and the
    # review's dry quote of a payment simulates the transfer (Spec 154: the call gas from the chain's dry run of the callData), so an
    # estate holding no USDC is refused for an unpriceable transfer, not for want of gas. So S7 credits the Treasury's gas first (§3's
    # road, U3's US$10.00), has the Treasury pay the shortfall (§2), proves S7a on Holdings — whose gas nobody has credited yet (§3) —
    # then credits Holdings' gas (§3) and makes the three payments (§4). Every other word of §2 to §4 is kept.
    #
    # THE SIGNATURES — A SECOND DISAGREEMENT CARRIED TO BEAR. SPEC.md §4 says P1 lands with one signature (the holder's), P2 waits for two
    # and lands when Ben and Cora sign, P3 waits for three. Those are the signing tiers of Spec 92 (WO3, WO4), which the estate RECORDS
    # in the compiled charter and enforces nowhere on the payments road: at 8812c64 `signingTiers` is written by onboardingcompiler.ts
    # and read by no route; the approvals road asks `approvalsRequired` from the band (the per-payment hold) and the destination rule
    # (Spec 69), and admits the `approver` standing alone (routes/approvals.ts, requireCaller 'approver'), which the charter seats Ada
    # in. So the harness walks the spec's road — the signers press in the spec's order, Ben, Cora, then Ada and Harriet, while the run
    # waits — reports each answer in the estate's words, never retries a refusal, and judges each payment on the four proofs §4 names:
    # the run's status, the userOpHash, the handleOps transaction hash and the payee's USDC balance before and after. The count the
    # estate asked and the count the tiers would ask stand side by side in the line, for Bear to rule on.
    TIER_ROAD_WORDS = {
        "P1": "the spec: lands with one signature, the holder's (Ben Signatory)",
        "P2": "the spec: waits for two and lands when Ben Signatory and Cora Clerk sign",
        "P3": "the spec: waits for three and lands when the third signs",
    }

    def clerk(self) -> Person:
        cora = self.people[A.PAYMENT_CLERK]
        return cora if cora.signed_in else self.founder()

    def payee_address_id(self, key: str) -> Optional[str]:
        for record in self.facts["payees"]:
            if record["key"] == key and record.get("address_id"):
                return record["address_id"]
        register = self.facts.get("payees_register") or {}
        wanted = T.address(key).lower()
        for row in register.get("payees") or []:
            for addr in row.get("addresses") or []:
                if str(addr.get("address", "")).lower() == wanted:
                    return str(addr.get("id"))
        return None

    def fresh_unlisted_key(self, clerk: Person) -> str:
        """
        The first pinned unlisted destination the estate's runs register has never seen. Spec 69 pauses
        a NEW destination, and a destination paid in an earlier run — in any state but rejected — is old
        to the estate (setgates.ts, isDestinationNew); a run that found none fresh says so and reuses the first.
        """
        register = self.request(clerk, "GET", "/v1/sets", None, "S7")
        self.step("S7", register, "the runs register, read for the destinations this estate has paid before", "answered" if register.ok else register.sentence(), None, clerk.name)
        paid: set = set()
        if isinstance(register.json, dict):
            for row in register.json.get("sets") or []:
                for instruction in row.get("instructions") or []:
                    paid.add(str(instruction.get("address", "")).lower())
        for key in T.UNLISTED_KEYS:
            if T.address(key).lower() not in paid:
                self.facts["unlisted_key"] = key
                return key
        self.note("S7", "every pinned unlisted destination has been paid in an earlier run of this estate; %s is paid again and the estate will not find it new" % T.UNLISTED_KEYS[0])
        self.facts["unlisted_key"] = T.UNLISTED_KEYS[0]
        return T.UNLISTED_KEYS[0]

    def pay_row(self, payment: A.Payment) -> Optional[Dict[str, Any]]:
        if payment.payee_key is None:
            key = self.facts.get("unlisted_key") or self.fresh_unlisted_key(self.clerk())
            return {"oneOff": {"chain": T.PAYEE_CHAIN, "address": T.address(key), "declared": True, "payeeName": payment.payee_name},
                    "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": payment.amount_minor, "invoiceRef": payment.invoice}
        address_id = self.payee_address_id(payment.payee_key)
        if address_id is None:
            return None
        return {"payeeAddressId": address_id, "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": payment.amount_minor, "invoiceRef": payment.invoice}

    def tiers(self) -> Tuple[Optional[str], Optional[str], str]:
        """
        The signing tiers' two figures (Spec 92, WO3 and WO4): this run's compiled account charter where it carries them, else the
        book's answers, and a word for where they were read (Spec T11 §4).
        """
        charter = self.facts["charter"].get("wallet_account") or {}
        tiers = charter.get("signingTiers")
        if isinstance(tiers, dict) and tiers.get("twoSignaturesUpToCents") is not None:
            return tiers.get("holderAloneUpToCents"), tiers.get("twoSignaturesUpToCents"), "this run's compiled account charter"
        holder_named = (A.ACCOUNT_ANSWERS.get("WO1") or {}).get("choice") == A.HOLDER_PERSON
        return ((A.ACCOUNT_ANSWERS.get("WO3") or {}).get("cents") if holder_named else None), (A.ACCOUNT_ANSWERS.get("WO4") or {}).get("cents"), "the answer book"

    # -- the admin credential and the Treasury (Spec T14 §2, §3) ------------------------------------------------------------------
    def read_admin_env(self, station: str) -> Optional[Dict[str, str]]:
        """
        Spec T14 §3: the platform's admin credential Bear keeps in ~/.aer360-harness/admin.env, in the estate's own setting names
        (AERAccounts .env.example): AAP_ADMIN_BASE_URL and AAP_ADMIN_KEY. Read once per run and never printed — the key joins the
        secrets and is redacted from every record. A file absent or incomplete is noted here and fails S7 at the credit step with the
        spec's sentence, so the Treasury's birth and the balances are still read and reported first.
        """
        path = self.admin_env_path
        if not os.path.isfile(path):
            self.note(station, "%s is not filed: the gas credits below will fail with %r" % (path, T.NO_GAS_CREDIT_ROAD_SENTENCE))
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                values = T.parse_env_file(handle.read())
        except OSError as err:
            self.note(station, "%s could not be read (%s): the gas credits below will fail" % (path, err))
            return None
        base = values.get(T.ADMIN_ENV_URL_KEY, "").strip().rstrip("/")
        key = values.get(T.ADMIN_ENV_KEY_KEY, "").strip()
        if not base or not key:
            missing = " and no ".join(name for name, value in ((T.ADMIN_ENV_URL_KEY, base), (T.ADMIN_ENV_KEY_KEY, key)) if not value)
            self.note(station, "%s names no %s: the gas credits below will fail" % (path, missing))
            return None
        self.secrets.add(key)
        if not key.startswith(T.ADMIN_KEY_PREFIX):
            self.note(station, "%s's %s does not begin %s, which the platform's admin road requires (internal/api/middleware.go says \"invalid admin key format\"); the credit will be refused" % (
                path, T.ADMIN_ENV_KEY_KEY, T.ADMIN_KEY_PREFIX))
        return {"base": base, "key": key, "path": path}

    @staticmethod
    def treasury_overrides() -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        The Treasury's interviews are the book's, with three answers of its own (aer360_tables.py, TREASURY): its name (A1); its one
        payment approver (C11) — the address the Treasury's estate is opened under, which the estate attributes to the founder's own
        key (services/approverseats.ts, addressesOfCaller) so that the founder's compile seats her (completeSeatOnCharterWrite) and
        her passkey can approve the float's payment; and that address first among the account's approvers (WA1), beside the book's.
        Nothing else in the book changes.
        """
        return {"policy": {"A1": {"text": T.TREASURY["company"]}, "C11": {"people": [T.TREASURY["email"]]}},
                "wallet_account": {"WA1": {"entries": [{"name": T.TREASURY["short"], "email": T.TREASURY["email"]}] + list(A.ACCOUNT_ANSWERS["WA1"]["entries"])}}}

    def for_treasury(self) -> "Runner":
        """The Treasury's own runner — its founder, cookie jar, passkey folder (~/.aer360-harness/harness-treasury/) and facts — sharing this run's records, secrets and stamp."""
        if self.treasury is None:
            t = Runner(self.base, self.store_dir, self.treasury_invite, False, None, self.out_dir, self.dry, self.transport, self.say, self.sleep, self.clock,
                       self.openssl, estate=T.TREASURY, admin_env=self.admin_env_path)
            for value in t.secrets.values:
                self.secrets.add(value)
            t.secrets, t.calls, t.evidence, t.notes, t.findings = self.secrets, self.calls, self.evidence, self.notes, self.findings
            t.run_stamp = self.run_stamp
            t.who_suffix = " (%s)" % T.TREASURY["short"]
            t.answer_overrides = self.treasury_overrides()
            t.load_passkeys()
            self.treasury = t
        return self.treasury

    def treasury_passkey_stored(self) -> bool:
        """Whether a passkey is stored for the Treasury's founder under ~/.aer360-harness/harness-treasury/: a Treasury born by an earlier run."""
        return self.for_treasury().people[A.FOUNDER].passkey is not None

    def bring_in_the_treasury(self, station: str) -> Dict[str, Any]:
        """
        Spec T14 §2: Harness Treasury, a second sandbox workspace born once by the harness exactly as Harness Holdings is (Spec T13).
        Its founder signs in with the passkey stored under ~/.aer360-harness/harness-treasury/, or is enrolled by --treasury-invite; on
        the birth run the policy and wallet-account interviews are walked from the book with the Treasury's three answers, and the
        funding wallet is pressed for — a key allocated on the platform and held in the enclave (Spec 98, Spec 104 §1). The harness
        then prints the address and stops S7 with "fund Harness Treasury: <address> on <chain>, then rerun"; a later run signs in and
        reads the wallet the workspace answers. The harness holds no key for it, ever.
        """
        t = self.for_treasury()
        founder = t.people[A.FOUNDER]
        record: Dict[str, Any] = {"born_now": False, "interviews_walked": False, "wallet_born_now": False, "address": None, "said": "", "workspace": None, "wallet": None}
        self.facts["treasury"] = record
        if founder.passkey is not None:
            verified, _ = t.sign_in(founder, station)
            t.step(station, verified, "a session for %s at %s, with the Treasury founder's stored passkey" % (founder.name, T.TREASURY["short"]),
                   "signed in" if verified.ok else verified.sentence(), {"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<assertion>"}, founder.name)
            if verified.ok:
                how = "the Treasury founder signed in with the stored passkey"
            elif self.treasury_invite:
                self.say("  %s: the Treasury founder's stored passkey was refused (%s); enrolling with --treasury-invite instead" % (station, verified.sentence()))
                founder.passkey = None
                founder.key_file = None
                verified = t.enrol_by_invite(founder, self.treasury_invite, station)
                how = "the Treasury founder enrolled by invitation after the stored passkey was refused"
                record["born_now"] = True
            else:
                raise StationStop("no Harness Treasury session: POST /v1/auth/login/verify answered %s" % verified.sentence())
        elif self.treasury_invite:
            verified = t.enrol_by_invite(founder, self.treasury_invite, station)
            how = "the Treasury founder enrolled by invitation"
            record["born_now"] = True
        else:
            raise StationStop("no Harness Treasury: no passkey is stored for its founder at %s and no --treasury-invite <link> was given; the first run births the "
                              "Treasury from the birth script's invitation, exactly as Harness Holdings was born" % t.key_path(founder))
        if not verified.ok or founder.session is None:
            raise StationStop("no Harness Treasury session: the invitation road answered %s" % verified.sentence())
        workspace = founder.session.get("workspace") or {}
        name = str(workspace.get("name") or "")
        t.facts["workspace"] = workspace
        record["workspace"] = workspace
        if not name.strip().lower().startswith(T.TREASURY["short"].lower()):
            raise StationStop("%s; the session names the workspace %r, not %s" % (how, name, T.TREASURY["short"]))
        before = t.request(founder, "GET", "/v1/workspace", None, station)
        t.step(station, before, "the Treasury's workspace before anything is walked: fundingWallet where the Treasury stood before this run, fundingWalletAbsence on the birth run",
               "answered" if before.ok else before.sentence(), None, founder.name)
        stood = before.ok and isinstance(before.json, dict) and isinstance(before.json.get("fundingWallet"), dict) and bool(before.json["fundingWallet"].get("address"))
        record["wallet_stood_before"] = stood
        standing = t.request(founder, "GET", "/v1/onboarding/charter", None, station)
        t.step(station, standing, "the Treasury's policy charter: standsWritten true on a rerun; false on the birth run, which walks the interviews from the book",
               json.dumps(standing.json) if standing.ok else standing.sentence(), None, founder.name)
        stands = isinstance(standing.json, dict) and standing.json.get("standsWritten") is True
        walked = ""
        if not stands:
            interview_id, page, answered = t.walk_interview(station, "policy", founder)
            t.confirm_and_compile(station, "policy", interview_id, founder, page)
            interview_id, page, answered_account = t.walk_interview(station, "wallet_account", founder)
            t.confirm_and_compile(station, "wallet_account", interview_id, founder, page)
            record["interviews_walked"] = True
            walked = "; the interviews walked from the book with the Treasury's own name, approver and account approvers (%d and %d questions)" % (answered, answered_account)
        wallet_said, wallet_failed = t.give_the_estate_its_funding_wallet(station, founder)
        wallet = t.facts.get("funding_wallet")
        if wallet_failed or not isinstance(wallet, dict) or not wallet.get("address"):
            raise StationStop("Harness Treasury has no funding wallet: %s" % wallet_said)
        press = t.facts.get("funding_press")
        record.update(address=wallet["address"], wallet=wallet, wallet_born_now=bool(isinstance(press, dict) and press.get("status") == 200))
        record["said"] = "%s: %s; %s%s" % (T.TREASURY["short"], how, wallet_said, walked)
        # THE BIRTH RUN (Spec T14 §2, the ship note): the Treasury's funding wallet did not stand before this run — it was born by the wallet
        # account's write (Spec 98) or by the press above — so Bear has never seen its address. S7 prints it and, once it has read the Treasury's
        # USDC and found it short of the shortfall, stops with the spec's sentence; a wallet that stood before and is short is told the other.
        record["born_this_run"] = not stood
        if record["born_this_run"]:
            sentence = T.FUND_TREASURY_SENTENCE % (wallet["address"], T.PAYEE_CHAIN)
            self.say("  %s: %s" % (station, sentence))
            self.note(station, "%s — the estate's own words: %s" % (sentence, (wallet.get("fundSentence") or "").strip() or "the workspace answered no fund sentence"))
        return record

    # -- the money reads: USDC through the estate's own road, gas from the platform, a payee from the chain ------------------------
    def read_usdc_balance(self, runner: "Runner", person: Person, station: str, who: str) -> Tuple[Optional[int], str, Optional[str]]:
        """
        Spec 104 §1: the stablecoin the funding wallet holds on each chain this deployment pays on, read live through the estate's own
        road (GET /v1/workspace/funding-account/balances) and said in dollars. The USDC row on the payments' chain is the figure — its
        balanceMinor, exact — and its `token` is the contract the estate names, which a payee's balance is read against on the chain.
        A road that cannot say (no wallet, no row, no RPC) is reported in the estate's words and answers None: no balance is invented.
        """
        answer = runner.request(person, "GET", T.FUNDING_BALANCES_ROUTE, None, station)
        body = answer.json if answer.ok and isinstance(answer.json, dict) else None
        rows = [r for r in ((body or {}).get("balances") or []) if isinstance(r, dict)]
        row = next((r for r in rows if str(r.get("asset") or "").upper() == T.PAYMENT_ASSET and str(r.get("chain") or "").lower() == T.PAYEE_CHAIN), None)
        expected = "%s's %s balance on %s in dollars (Spec 104 §1: balances[{chain, asset, token, balanceMinor, usdMinor, sentence}])" % (who, T.PAYMENT_ASSET, T.PAYEE_CHAIN)
        if body is None:
            runner.step(station, answer, expected, answer.sentence(), None, person.name)
            return None, "%s's %s balance could not be read: %s" % (who, T.PAYMENT_ASSET, answer.sentence()), None
        if row is None:
            named = ", ".join("%s on %s" % (r.get("asset"), r.get("chain")) for r in rows)
            said = "%s's %s balance on %s: the estate names no %s row on %s (%s)" % (
                who, T.PAYMENT_ASSET, T.PAYEE_CHAIN, T.PAYMENT_ASSET, T.PAYEE_CHAIN, body.get("absence") or ("the rows name %s" % named if named else "no rows"))
            runner.step(station, answer, expected, said, None, person.name)
            return None, said, None
        token = row.get("token")
        minor = row.get("balanceMinor")
        if not isinstance(minor, str) or not INTEGER_TEXT.match(minor):
            said = "%s's %s balance on %s could not be read: %s" % (who, T.PAYMENT_ASSET, T.PAYEE_CHAIN, row.get("sentence") or json.dumps(row, ensure_ascii=False))
            runner.step(station, answer, expected, said, None, person.name)
            return None, said, token
        said = "%s holds %s of %s on %s" % (who, T.usdc_dollars(int(minor)), T.PAYMENT_ASSET, T.PAYEE_CHAIN)
        runner.step(station, answer, expected, "%s (%s)" % (said, row.get("sentence")), None, person.name)
        return int(minor), said, token

    def read_gas_account(self, runner: "Runner", person: Person, station: str, who: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Spec 104 §3: the gas account read live from the platform through the estate's own road (GET /v1/gas/account): `account` with
        the figures in cents (availableUsdCents, balanceUsdCents, reservedUsdCents), the platform's `low`, and the Wallets screen's own
        sentence, "Gas account: US$<available>"; or `unreadable`, the estate's sentence for a platform it could not ask.
        """
        answer = runner.request(person, "GET", T.GAS_ACCOUNT_ROUTE, None, station)
        body = answer.json if answer.ok and isinstance(answer.json, dict) else None
        account = body.get("account") if body is not None and isinstance(body.get("account"), dict) else None
        expected = "%s's gas account: \"%s: US$…\" with availableUsdCents, balanceUsdCents, reservedUsdCents and low, read live from the platform (Spec 104 §3)" % (who, T.GAS_ACCOUNT_LABEL)
        if account is None:
            said = "%s's gas account could not be read: %s" % (who, (body or {}).get("unreadable") or answer.sentence())
            runner.step(station, answer, expected, said, None, person.name)
            return None, said
        said = "%s's %s (balance %s, reserved %s%s)" % (who, account.get("sentence"), account.get("balance"), account.get("reserved"), "; low" if account.get("low") else "")
        runner.step(station, answer, expected, said, None, person.name)
        return account, said

    def read_token_balance(self, station: str, who: str, chain: str, token: Optional[str], holder: str) -> Tuple[Optional[int], str]:
        """
        Spec T14 §4: a payee's USDC balance, read from the chain as the corridor reads one — eth_call balanceOf(address) on the token the
        estate names (the USDC row of the balances road) through the chain's public RPC, pinned from the corridor harness's own skeleton
        — because the estate offers a browser no road to a payee's balance. A fault is the RPC's, reported in its words, and answers None:
        the harness never invents a balance, and a proof it could not read is not a pass (Bear, 14 September 2026: "a missing RPC should
        make anybody worry").
        """
        url = T.public_rpc_url(chain)
        if not url:
            return None, "no public RPC is known for %s: neither the AEREDIUM testnet's nor the corridor harness's skeleton names one (aer360_tables.py, public_rpc_url)" % chain
        if not token:
            return None, "the estate names no %s contract on %s (the balances road's token), so there is nothing to read the balance against" % (T.PAYMENT_ASSET, chain)
        data = T.balance_of_call_data(holder)
        body = {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": token, "data": data}, "latest"]}
        answer = self.request_outside(who, "POST", url, body, station)
        self.step(station, answer, "a 32-byte hex word: %s's %s balance in minor units on %s (balanceOf on %s through the chain's public RPC)" % (holder, T.PAYMENT_ASSET, chain, token),
                  "answered" if answer.ok else self.outside_sentence(answer), body, who)
        if answer.status == 0:
            return None, "the RPC at %s could not be reached: %s" % (url, answer.text)
        parsed = answer.json
        if not isinstance(parsed, dict):
            return None, "the RPC at %s answered HTTP %d without JSON: %s" % (url, answer.status, answer.text[:200] or "<empty>")
        if parsed.get("error") is not None:
            return None, "the RPC at %s refused eth_call: %s" % (url, json.dumps(parsed["error"], ensure_ascii=False))
        result = parsed.get("result")
        if not isinstance(result, str) or not result.startswith("0x"):
            return None, "the RPC at %s answered %r for balanceOf, which is not a hex word" % (url, result)
        try:
            minor = int(result, 16) if result not in ("0x", "") else 0
        except ValueError:
            return None, "the RPC at %s answered %r for balanceOf, which is not a number" % (url, result[:80])
        return minor, "%s of %s (%d minor units) read from %s" % (T.usdc_dollars(minor), T.PAYMENT_ASSET, minor, url)

    # -- the gas credits (Spec T14 §3): the platform's admin credit road, never the card road ----------------------------------------
    def credit_gas(self, runner: "Runner", station: str, admin: Optional[Dict[str, str]], who: str, cents: int) -> Dict[str, Any]:
        """
        One credit to a workspace's gas account through the platform's admin credit road (Spec 154 §1: POST
        /v1/admin/accounts/{id}/gas-account/credits under the admin key; reason required; audited gas.credited_by_admin), the reason
        "sandbox run <run id>" and an idempotency key of this run's, so a post repeated credits once. The answer is classified as Rule
        13 asks (`credit_words`): credited or deduped with the platform's balance; the platform's refusal of the credential in its own
        words, the same on retry; the harness's or the deployment's mistake; a fault. Anything but a credit fails S7 naming it, and no
        credential fails S7 with the spec's sentence.
        """
        if admin is None:
            raise StationStop(T.NO_GAS_CREDIT_ROAD_SENTENCE)
        workspace = runner.facts.get("workspace")
        account_id = None
        if isinstance(workspace, dict):  # the session's workspace (S1), or GET /v1/workspace's whole answer (S5, S7): either names the platform account
            inner = workspace.get("workspace") if isinstance(workspace.get("workspace"), dict) else {}
            account_id = workspace.get("aapAccountId") or inner.get("aapAccountId")
        if not account_id:
            raise StationStop("the gas credit for %s was not made: the estate's session names no platform account (workspace.aapAccountId), so the admin road has no account to credit" % who)
        founder = runner.people[A.FOUNDER]
        # one key per credit of this run for this workspace — the platform dedupes a repeated key, so a second credit (the review's shortfall
        # cured with more gas) carries its own ordinal
        ordinal = 1 + sum(1 for r in self.facts["gas_credits"] if r.get("who") == who)
        body = {"amount_usd_cents": int(cents), "reason": T.ADMIN_CREDIT_REASON % self.run_stamp,
                "idempotency_key": "aer360-harness-%s-%s-gas-%d" % (self.run_stamp, runner.estate["client_id"], ordinal)}
        url = admin["base"] + T.ADMIN_CREDIT_ROUTE % account_id
        who_said = "%s (at the platform's admin road)" % founder.name
        answer = self.request_outside(who_said, "POST", url, body, station, headers={"Authorization": "Bearer %s" % admin["key"]})
        outcome, words = self.credit_words(answer, who)
        self.step(station, answer, "201 with the line and the balance (the platform's own figures: balance_usd_cents, reserved_usd_cents, available_usd_cents), or 200 deduped "
                  "for a key already credited; a refusal in the platform's words (Spec 154 §1; the reason \"%s\")" % body["reason"], words, body, who_said)
        balance = answer.json.get("balance") if isinstance(answer.json, dict) and isinstance(answer.json.get("balance"), dict) else None
        record = {"who": who, "account_id": account_id, "amount_usd_cents": int(cents), "reason": body["reason"], "idempotency_key": body["idempotency_key"],
                  "status": answer.status, "outcome": outcome, "said": words, "balance_after": balance}
        self.facts["gas_credits"].append(record)
        if outcome not in ("credited", "deduped"):
            raise StationStop("the gas credit for %s was not made: %s" % (who, words))
        return record

    @staticmethod
    def credit_words(answer: Answer, who: str) -> Tuple[str, str]:
        """The platform's answer to a credit, classified — what happened, in the platform's own words (internal/api/middleware.go, gas_handlers.go, internal/gas/credit.go)."""
        body = answer.json if isinstance(answer.json, dict) else None
        said = body.get("error") if body is not None and isinstance(body.get("error"), str) else None
        if answer.status == 0:
            return "unreachable", "the platform could not be reached: %s" % answer.text
        if answer.ok and body is not None and isinstance(body.get("balance"), dict):
            balance = body["balance"]
            line = body.get("line") if isinstance(body.get("line"), dict) else {}
            outcome = "deduped" if body.get("deduped") else "credited"
            return outcome, "%s %s %s (line %s): balance %s, available %s%s" % (
                who, outcome, T.format_usd_cents(line.get("amount_usd_cents") or 0), line.get("id"), T.format_usd_cents(balance.get("balance_usd_cents") or 0),
                T.format_usd_cents(balance.get("available_usd_cents") or 0), (" — %s" % body["note"]) if body.get("note") else "")
        if answer.ok:
            return "unreadable", "the platform answered HTTP %d in a shape the harness will not read: %s" % (answer.status, answer.text[:300])
        if answer.status in (401, 403):
            return "refused", "refused: the platform refused the admin credential (HTTP %d): %s — the answer will be the same until the credential in %s is replaced" % (
                answer.status, said or answer.text[:300], T.ADMIN_ENV_FILE)
        if 400 <= answer.status < 500:
            return "malformed", "the platform refused the harness's question (HTTP %d): %s — a mistake of the harness or of the deployment, not the estate's" % (answer.status, said or answer.text[:300])
        return "fault", "the platform answered a fault (HTTP %d): %s" % (answer.status, said or answer.text[:300])

    @staticmethod
    def gas_credit_for(ceiling_cents: Optional[int]) -> int:
        """
        What a workspace is credited (Spec T14 §3, "as the sandbox may"): U3's ten dollars — or, where a set's ceiling read at S7a says
        the run's reservations (the creations' quotes and the executions') would exceed them, the next ten dollars above twice that
        ceiling (U3: "if they estimate that their transactions are large, they will need to put more"). Pure arithmetic on the platform's
        own figure; nothing marked up.
        """
        if not isinstance(ceiling_cents, int) or ceiling_cents <= 0:
            return T.GAS_CREDIT_USD_CENTS
        need = 2 * ceiling_cents
        return max(T.GAS_CREDIT_USD_CENTS, -(-need // T.GAS_CREDIT_USD_CENTS) * T.GAS_CREDIT_USD_CENTS)

    # -- S7a: the gas refusal, proved before any gas is credited (Spec T14 §3) ----------------------------------------------------
    def prove_the_gas_refusal(self, clerk: Person, rows: List[Dict[str, Any]], gas: Optional[Dict[str, Any]], usdc_before: Optional[int]) -> Dict[str, Any]:
        """
        With Harness Holdings' gas account below the review's ceiling, the set of three is submitted to the review (POST /v1/sets/review,
        which creates nothing) and the gas gate must refuse GAS_SHORTFALL in U3's sentence with both figures — "Your gas account holds
        US$… This set needs at most US$… of gas. Nothing was sent. Buy gas below." — the first the figure the harness read from GET
        /v1/gas/account, the second the gate's own ceilingUsdCents; and no payment may have left: the runs register carries no new run
        and Holdings' USDC is unchanged. Proved, S7a passes. A gate that admits the set because the balance already covers the ceiling is
        reported and not failed (the estate did right; the refusal cannot be met this run). A refusal naming other figures, a refusal
        for another cause, or a payment that left fails S7 naming it.
        """
        record: Dict[str, Any] = {"verdict": "not proved", "available": None, "ceiling": None, "sentence": None, "said": None, "left": None, "detail": None}
        self.facts["s7a"] = record
        available = gas.get("availableUsdCents") if isinstance(gas, dict) else None
        if not isinstance(available, int) or isinstance(available, bool):
            record.update(verdict="failed", said="S7a failed: Harness Holdings' gas account could not be read, so there is no figure to hold the sentence against")
            return record
        record["available"] = available
        register = self.request(clerk, "GET", "/v1/sets", None, "S7")
        self.step("S7", register, "the runs register before S7a's review, so a run the review created would be seen", "answered" if register.ok else register.sentence(), None, clerk.name)
        before_ids = {str(s.get("id")) for s in ((register.json or {}).get("sets") or [])} if isinstance(register.json, dict) else set()
        body = {"pays": rows, "duplicatesAcknowledged": False}
        review = self.request(clerk, "POST", "/v1/sets/review", body, "S7")
        expected = ("S7a: the gas gate (%s) refusing %s in U3's sentence with the figures the harness read — \"Your gas account holds %s. This set needs at most US$<the gate's ceilingUsdCents> "
                    "of gas. Nothing was sent. Buy gas below.\" — and nothing created (Spec 104 §4)" % (T.GAS_GATE, T.GAS_SHORTFALL, T.format_usd_cents(available)))
        payload = review.json if review.ok and isinstance(review.json, dict) else None
        if payload is None:
            self.step("S7", review, expected, review.sentence(), body, clerk.name)
            record.update(verdict="failed", said="S7a failed: the review answered %s, not the gas gate's refusal" % review.sentence())
            return record
        gates = [g for g in (payload.get("gates") or []) if isinstance(g, dict)]
        gate = next((g for g in gates if g.get("gate") == T.GAS_GATE), None)
        refusals = [r for r in ((gate or {}).get("refusals") or []) if isinstance(r, dict)]
        shortfall = next((r for r in refusals if r.get("code") == T.GAS_SHORTFALL), None)
        others = [r for g in gates for r in (g.get("refusals") or []) if isinstance(r, dict) and r.get("code") != T.GAS_SHORTFALL]
        if gate is None:
            result = "the review carries no %s gate (gates: %s)" % (T.GAS_GATE, ", ".join(str(g.get("gate")) for g in gates) or "none")
            record.update(verdict="failed", said="S7a failed: " + result)
        elif shortfall is None and gate.get("passed") is True:
            result = "the gate admits the set: %s" % gate.get("evidence")
            record["said"] = ("S7a not proved: Harness Holdings' gas account (%s available) covers the set's ceiling, so the review admits the set and the refusal cannot be met this run "
                              "(the gate's evidence: %s)" % (T.format_usd_cents(available), gate.get("evidence")))
        elif shortfall is None:
            result = "the gate refused, but not for want of gas: %s" % ("; ".join("%s: %s" % (r.get("code"), r.get("message")) for r in refusals) or gate.get("evidence"))
            record.update(verdict="failed", said="S7a failed: " + result)
        else:
            detail = shortfall.get("detail") if isinstance(shortfall.get("detail"), dict) else {}
            ceiling_text = str(detail.get("ceilingUsdCents", ""))
            ceiling = int(ceiling_text) if INTEGER_TEXT.match(ceiling_text) else None
            record.update(ceiling=ceiling, sentence=shortfall.get("message"), detail=detail)
            wanted = T.gas_set_shortfall_sentence(available, ceiling) if ceiling is not None else None
            if wanted is not None and shortfall.get("message") == wanted and str(detail.get("availableUsdCents")) == str(available):
                result = "refused as U3 says: %s" % shortfall.get("message")
                record.update(verdict="proved", said="S7a proved: the review refused %s — \"%s\" — naming the %s the harness read and the gate's ceiling %s" % (
                    T.GAS_SHORTFALL, shortfall.get("message"), T.format_usd_cents(available), T.format_usd_cents(ceiling)))
            else:
                result = "refused, but naming other figures: %r (the harness read %s available; the gate's detail says available %s, ceiling %s)" % (
                    shortfall.get("message"), T.format_usd_cents(available), detail.get("availableUsdCents"), detail.get("ceilingUsdCents"))
                record.update(verdict="failed", said="S7a failed: the refusal names other figures — it says %r; the harness read %s available, and the gate's detail says available %s, ceiling %s" % (
                    shortfall.get("message"), T.format_usd_cents(available), detail.get("availableUsdCents"), detail.get("ceilingUsdCents")))
        if others and record["verdict"] != "failed":
            self.note("S7", "S7a: the review carried refusals beside the gas gate's: %s" % "; ".join("%s: %s" % (r.get("code"), r.get("message")) for r in others))
        self.step("S7", review, expected, result, body, clerk.name)
        register_after = self.request(clerk, "GET", "/v1/sets", None, "S7")
        self.step("S7", register_after, "the runs register after S7a's review: no new run (nothing was sent)", "answered" if register_after.ok else register_after.sentence(), None, clerk.name)
        after_ids = {str(s.get("id")) for s in ((register_after.json or {}).get("sets") or [])} if isinstance(register_after.json, dict) else set()
        new_ids = sorted(after_ids - before_ids)
        usdc_after, usdc_words, _ = self.read_usdc_balance(self, clerk, "S7", "Harness Holdings")
        left: List[str] = []
        if new_ids:
            left.append("the review created run(s) %s" % ", ".join(new_ids))
        if usdc_before is not None and usdc_after is not None and usdc_after != usdc_before:
            left.append("Harness Holdings' %s moved from %s to %s" % (T.PAYMENT_ASSET, T.usdc_dollars(usdc_before), T.usdc_dollars(usdc_after)))
        record["left"] = left
        if left:
            record.update(verdict="failed", said="S7a failed: a payment left — %s" % "; ".join(left))
        elif record["verdict"] == "proved":
            record["said"] += "; nothing left (no new run in the register; Holdings' %s unchanged at %s)" % (
                T.PAYMENT_ASSET, T.usdc_dollars(usdc_after) if usdc_after is not None else "a figure the estate could not say")
        return record

    # -- one payment through the estate's own road, judged on money that moved (Spec 104 §2; Spec T14 §4) --------------------------
    def pay(self, runner: "Runner", author: Person, key: str, row: Dict[str, Any], amount_minor: int, payee_address: str, signers: Sequence[Person],
            expect_words: str, read_payee_balance: Callable[[], Tuple[Optional[int], str]], station: str = "S7",
            cure: Optional[Callable[[Dict[str, Any]], bool]] = None, more_gas: Optional[Callable[[Optional[int]], bool]] = None) -> Dict[str, Any]:
        """
        The review; the run created and submitted; the signers pressing in the spec's order while the run waits, until the estate reports
        it approved (each refusal in the estate's words, never retried; `cure` may mend one refusal once and ask for the same press again —
        the Treasury founder's seat); the run executed by its author (POST /v1/sets/{id}/execute: the estate quotes, signs, sponsors and
        sends through the platform's gas roads and waits for the platform to report the operation landed); the run read until its
        instruction is terminal; the payee's USDC before and after. `more_gas` may credit the workspace once where the review's gas gate
        refuses GAS_SHORTFALL, and the review is asked again. The trail's row is read afterwards by `judge_landing`.
        """
        record: Dict[str, Any] = {"key": key, "amount_minor": amount_minor, "payee": payee_address, "set_id": None, "instruction_id": None, "review": None, "created": None,
                                  "refusal": None, "submitted": None, "approvals_required": None, "approvals": [], "executed": None, "view": None, "status": None,
                                  "set_status": None, "tx_hash": None, "failure_reason": None, "gas_value": None, "user_op_hash": None, "gas_debit_cents": None,
                                  "gas_debit": None, "balance_before": None, "balance_after": None, "before_words": None, "after_words": None, "landed": False,
                                  "said": None, "failure": None, "spoken": []}
        before, before_words = read_payee_balance()
        record.update(balance_before=before, before_words=before_words)
        review_body = {"pays": [row], "duplicatesAcknowledged": False}
        for attempt in range(2):
            review = runner.request(author, "POST", "/v1/sets/review", review_body, station)
            runner.step(station, review, "the gates' review of the run before anything is created — the gas gate reading the gas account and one dry quote (Spec 104 §4); %s" % expect_words,
                        "answered" if review.ok else review.sentence(), review_body, author.name)
            record["review"] = review.json if review.ok else review.sentence()
            shortfall = self.gas_shortfall_of(review)
            if shortfall is None or more_gas is None or attempt:
                break
            detail = shortfall.get("detail") if isinstance(shortfall.get("detail"), dict) else {}
            ceiling_text = str(detail.get("ceilingUsdCents", ""))
            if not more_gas(int(ceiling_text) if INTEGER_TEXT.match(ceiling_text) else None):
                break
            record["spoken"].append("the review refused %s (%s); gas credited and the review asked again" % (T.GAS_SHORTFALL, shortfall.get("message")))
        create_body = dict(review_body)
        create_body.update({"idempotencyKey": "aer360-harness-%s-%s" % (self.run_stamp, key), "reference": "Harness payment %s" % key})
        created = runner.request(author, "POST", "/v1/sets", create_body, station)
        runner.step(station, created, "201 with the run in draft and its review", "created" if created.ok else created.sentence(), create_body, author.name)
        if not created.ok or not isinstance(created.json, dict):
            record.update(refusal=created.sentence(), failure="refused at creation", said="refused at creation — %s" % created.sentence())
            return record
        record["created"] = created.json
        set_view = created.json.get("set") if isinstance(created.json.get("set"), dict) else {}
        set_id = str(set_view.get("id"))
        record["set_id"] = set_id
        instructions = [i for i in (set_view.get("instructions") or []) if isinstance(i, dict)]
        record["instruction_id"] = str(instructions[0].get("id")) if instructions else None
        submitted = runner.request(author, "POST", "/v1/sets/%s/submit" % set_id, {}, station)
        runner.step(station, submitted, "status pending_approval with approvalsRequired, or approved where the estate asks no second hand; %s" % expect_words,
                    "answered" if submitted.ok else submitted.sentence(), {}, author.name)
        record["submitted"] = submitted.json if submitted.ok else submitted.sentence()
        if not submitted.ok or not isinstance(submitted.json, dict):
            record.update(failure="not submitted", said="created; the submit answered %s" % submitted.sentence())
            return record
        status = str(submitted.json.get("status"))
        required = submitted.json.get("approvalsRequired")
        record["approvals_required"] = required
        spoken: List[str] = record["spoken"] + ["submitted: status %s, approvalsRequired %s" % (status, required)]
        cured = False
        for signer in signers:
            if status != "pending_approval":
                break
            if not signer.signed_in:
                spoken.append("%s has no session to sign with" % signer.name)
                continue
            outcome = self.sign_the_run(runner, signer, set_id, station)
            record["approvals"].append(outcome)
            spoken.append(outcome["said"])
            if outcome.get("status_after") is None and cure is not None and not cured and outcome.get("refusal_code") == "ROLE_NOT_GRANTED":
                cured = True
                if cure(outcome):
                    outcome = self.sign_the_run(runner, signer, set_id, station)
                    record["approvals"].append(outcome)
                    spoken.append(outcome["said"])
            if outcome.get("status_after") is not None:
                status = str(outcome["status_after"])
        record["status_after_signing"] = status
        if status == "pending_approval":
            record.update(status=status, set_status=status, failure="waits with nobody left to sign", said="; ".join(spoken) + "; nobody left to sign, so the run waits and nothing was sent")
            return record
        if status != "approved":
            record.update(status=status, set_status=status, failure="not approved: %s" % status, said="; ".join(spoken))
            return record
        executed = runner.request(author, "POST", T.SET_EXECUTE_ROUTE % set_id, {}, station, retry=False)
        runner.step(station, executed, "the run executed through the platform's gas roads (Spec 104 §2): the estate quotes, signs, sponsors and sends, waits for the platform to report the "
                    "operation landed, and answers setStatus and each instruction's status and txHash; a refusal in the estate's words, never retried", "answered" if executed.ok else executed.sentence(), {}, author.name)
        record["executed"] = executed.json if executed.ok else executed.sentence()
        if not executed.ok:
            spoken.append("execute answered %s" % executed.sentence())
        view = self.read_until_terminal(runner, author, set_id, station, executed.ok)
        record["view"] = view
        set_row = view.get("set") if isinstance(view, dict) and isinstance(view.get("set"), dict) else {}
        instruction = next((i for i in (set_row.get("instructions") or []) if isinstance(i, dict)), None) or {}
        record.update(set_status=set_row.get("status"), status=instruction.get("status"), tx_hash=instruction.get("txHash"), failure_reason=instruction.get("failureReason"),
                      gas_value=instruction.get("gasValue"))
        if instruction.get("id") and not record["instruction_id"]:
            record["instruction_id"] = str(instruction.get("id"))
        after, after_words = read_payee_balance()
        record.update(balance_after=after, after_words=after_words, spoken=spoken)
        return record

    def sign_the_run(self, runner: "Runner", signer: Person, set_id: str, station: str) -> Dict[str, Any]:
        """One signer's press on a waiting run: the digest-bound challenge, then the approval with the passkey's assertion — once, never retried; a refusal in the estate's words."""
        challenge = runner.request(signer, "POST", "/v1/approvals/%s/challenge" % set_id, {}, station)
        expected = ("the digest-bound challenge %s's passkey signs; or a refusal in the estate's words — ROLE_NOT_GRANTED where the estate admits the approver standing alone, "
                    "SUBMITTER_MAY_NOT_APPROVE where the charter says so — never retried" % signer.name)
        record: Dict[str, Any] = {"who": signer.name, "key": signer.key, "credential": signer.credential_id, "status": challenge.status, "refusal_code": None, "status_after": None, "given": None, "said": None}
        if not challenge.ok or not isinstance(challenge.json, dict):
            runner.step(station, challenge, expected, challenge.sentence(), {}, signer.name)
            record.update(refusal_code=(challenge.refusal or {}).get("code") if challenge.refusal else None, said="%s refused (%s)" % (signer.name, challenge.sentence()))
            return record
        runner.step(station, challenge, expected, "answered", {}, signer.name)
        body = {"response": runner.assertion_for(signer, str(challenge.json.get("challenge")), station)}
        approved = runner.request(signer, "POST", "/v1/approvals/%s/approve" % set_id, body, station, retry=False)
        runner.step(station, approved, "status approved where %s's signature meets approvalsRequired, else pending_approval with approvalsGiven" % signer.name,
                    "answered" if approved.ok else approved.sentence(), body, signer.name)
        record["status"] = approved.status
        if not approved.ok or not isinstance(approved.json, dict):
            record.update(refusal_code=(approved.refusal or {}).get("code") if approved.refusal else None, said="%s refused at the press (%s)" % (signer.name, approved.sentence()))
            return record
        record.update(status_after=approved.json.get("status"), given=approved.json.get("approvalsGiven"),
                      said="%s signed (%s of %s): %s" % (signer.name, approved.json.get("approvalsGiven"), approved.json.get("approvalsRequired"), approved.json.get("status")))
        return record

    def read_until_terminal(self, runner: "Runner", person: Person, set_id: str, station: str, executed: bool) -> Optional[Dict[str, Any]]:
        """GET /v1/sets/{id} until every instruction is terminal (confirmed, failed, rejected) and the run is settled — a bounded number of reads over a bounded wait; once where nothing was executed."""
        view: Optional[Dict[str, Any]] = None
        reads = LANDING_READS if executed else 1
        for attempt in range(reads):
            answer = runner.request(person, "GET", "/v1/sets/%s" % set_id, None, station)
            runner.step(station, answer, "the run as the register shows it: the instruction confirmed (the platform reported the operation landed) or failed, with its txHash; the run settled",
                        "answered" if answer.ok else answer.sentence(), None, person.name)
            if not answer.ok or not isinstance(answer.json, dict):
                return view
            view = answer.json
            set_row = view.get("set") if isinstance(view.get("set"), dict) else {}
            instructions = [i for i in (set_row.get("instructions") or []) if isinstance(i, dict)]
            if all(str(i.get("status")) in T.INSTRUCTION_TERMINAL_STATES for i in instructions) and str(set_row.get("status")) in T.SET_TERMINAL_STATES:
                return view
            if attempt < reads - 1:
                self.sleep(LANDING_WAIT_SECONDS)
        return view

    @staticmethod
    def gas_shortfall_of(review: Answer) -> Optional[Dict[str, Any]]:
        """The gas gate's GAS_SHORTFALL refusal in a review's payload, or None."""
        payload = review.json if review.ok and isinstance(review.json, dict) else None
        if payload is None:
            return None
        for gate in payload.get("gates") or []:
            if isinstance(gate, dict) and gate.get("gate") == T.GAS_GATE:
                return next((r for r in (gate.get("refusals") or []) if isinstance(r, dict) and r.get("code") == T.GAS_SHORTFALL), None)
        return None

    def read_trail(self, runner: "Runner", person: Person, station: str, expected: str) -> Optional[List[Dict[str, Any]]]:
        """The accountant's audit export (GET /v1/export/audit, oldest first), every page followed by its nextCursor as `since`, up to a bound; None where it could not be read."""
        rows: List[Dict[str, Any]] = []
        since: Optional[str] = None
        for page in range(TRAIL_PAGES_AT_MOST):
            path = "%s?limit=%d%s" % (T.AUDIT_EXPORT_ROUTE, T.AUDIT_EXPORT_LIMIT, ("&since=%s" % urllib.parse.quote(since, safe="")) if since else "")
            answer = runner.request(person, "GET", path, None, station)
            body = answer.json if answer.ok and isinstance(answer.json, dict) else None
            items = [r for r in (body.get("items") or []) if isinstance(r, dict)] if body is not None else None
            runner.step(station, answer, expected, ("%d trail row(s)%s" % (len(items), (" on page %d" % (page + 1)) if page else "")) if items is not None else answer.sentence(), None, person.name)
            if items is None:
                return rows if rows else None
            rows.extend(items)
            since = body.get("nextCursor") if isinstance(body.get("nextCursor"), str) else None
            if not since or not items:
                break
        return rows

    def judge_landing(self, record: Dict[str, Any], trail: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Spec T14 §4: the four proofs — the run's status (the instruction confirmed, the run settled: the estate's words for an operation
        the platform reported landed), the userOpHash and the handleOps transaction hash from the trail's instruction.confirmed row, and the
        payee's USDC balance risen by the amount — with the gas debited read from the same row in dollars and reported beside. One proof
        missing fails the payment naming it; a balance that could not be read is not a pass.
        """
        if record.get("executed") is None:
            # THE RUN NEVER REACHED EXECUTION: refused at the review or the creation, not submitted, or waiting with nobody left to sign —
            # told in the words it stopped with (the estate's, where the estate refused), and never judged on proofs it could not have.
            record["landed"] = False
            if record.get("refusal"):
                record["said"] = "refused at creation — %s" % record["refusal"]
                record["failure"] = record.get("failure") or "refused at creation"
            elif not record.get("said"):
                record["said"] = record.get("failure") or "not executed"
            return record
        hits = [r for r in (trail or []) if r.get("action") == T.INSTRUCTION_CONFIRMED and record.get("instruction_id") and str(r.get("subject_id")) == str(record["instruction_id"])]
        detail = hits[-1].get("detail") if hits and isinstance(hits[-1].get("detail"), dict) else {}
        record["user_op_hash"] = detail.get("userOpHash")
        record["gas_debit"] = detail.get("gasDebit")
        debit = str(detail.get("gasDebitUsdCents", ""))
        record["gas_debit_cents"] = int(debit) if INTEGER_TEXT.match(debit) else None
        if not record.get("tx_hash") and detail.get("txHash"):
            record["tx_hash"] = detail.get("txHash")
        before, after, amount = record.get("balance_before"), record.get("balance_after"), int(record["amount_minor"])
        missing: List[str] = []
        if record.get("failure"):
            missing.append(record["failure"])
        if record.get("status") != "confirmed":
            missing.append("the instruction is %s%s" % (record.get("status"), (" (%s)" % record["failure_reason"]) if record.get("failure_reason") else ""))
        if record.get("set_status") != "settled":
            missing.append("the run is %s" % record.get("set_status"))
        if not record.get("tx_hash"):
            missing.append("no handleOps transaction hash")
        if not record.get("user_op_hash"):
            missing.append("no userOpHash on the trail's %s row%s" % (T.INSTRUCTION_CONFIRMED, "" if trail is not None else " (the trail could not be read)"))
        if before is None or after is None:
            missing.append("the payee's balance could not be read (%s)" % (record.get("before_words") if before is None else record.get("after_words")))
        elif after - before != amount:
            missing.append("the payee's %s balance did not rise by %s: %s → %s" % (T.PAYMENT_ASSET, T.usdc_dollars(amount), T.usdc_dollars(before), T.usdc_dollars(after)))
        record["landed"] = not missing
        proofs = "instruction %s, run %s, userOpHash %s, tx %s, payee %s → %s, gas %s" % (
            record.get("status"), record.get("set_status"), record.get("user_op_hash"), record.get("tx_hash"),
            T.usdc_dollars(before) if before is not None else "unread", T.usdc_dollars(after) if after is not None else "unread",
            record.get("gas_debit") or "not on the trail")
        spoken = list(record.get("spoken") or [])
        if record["landed"]:
            spoken.append("landed (+%s): %s" % (T.usdc_dollars(amount), proofs))
            record["failure"] = None
        else:
            spoken.append("not landed — %s (%s)" % ("; ".join(missing), proofs))
            record["failure"] = "; ".join(missing)
        record["said"] = "; ".join(spoken) if spoken else (record.get("said") or "")
        return record

    def treasury_pays_the_shortfall(self, t: "Runner", founder: Person, clerk: Person, shortfall: int, holdings_address: str, admin: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """
        Spec T14 §2: one payment of one set from Harness Treasury to Harness Holdings' address — a declared one-off of the shortfall —
        approved with the Treasury founder's passkey (the charter names her the payment approver; where the estate refuses her at the
        guard, her seat is granted once and she presses again), executed by her, and waited for until the estate reports it landed.
        Holdings' balance is read before and after through the estate's own road, as the Treasury's payee.
        """
        row = {"oneOff": {"chain": T.PAYEE_CHAIN, "address": holdings_address, "declared": True, "payeeName": A.ESTATE["company"]},
               "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": str(shortfall), "invoiceRef": "HT-%s" % self.run_stamp}

        def cure(outcome: Dict[str, Any]) -> bool:
            body = {"email": T.TREASURY["email"]}
            granted = t.request(founder, "POST", "/v1/approver-seats/grant", body, "S7")
            t.step("S7", granted, "the Treasury founder's own seat, granted once after the guard refused her (%s), so her passkey can approve the float's payment" % outcome.get("said"),
                   "granted" if granted.ok else granted.sentence(), body, founder.name)
            return granted.ok

        def more_gas(ceiling: Optional[int]) -> bool:
            credit = self.credit_gas(t, "S7", admin, T.TREASURY["short"], self.gas_credit_for(ceiling))
            self.facts["money"]["treasury"]["credited"] = self.facts["money"]["treasury"].get("credited", 0) + credit["amount_usd_cents"]
            return True

        record = self.pay(t, founder, "HT", row, shortfall, holdings_address, [founder], "the Treasury's founder approves with her passkey; the run lands and Harness Holdings' %s rises by %s" % (
            T.PAYMENT_ASSET, T.usdc_dollars(shortfall)), lambda: self.read_usdc_balance(self, clerk, "S7", "Harness Holdings")[:2], cure=cure, more_gas=more_gas)
        trail = self.read_trail(t, founder, "S7", "the Treasury's trail: the %s row for its payment — userOpHash, the handleOps txHash, gasDebitUsdCents and gasDebit (Spec 104 §2, §5)" % T.INSTRUCTION_CONFIRMED)
        return self.judge_landing(record, trail)

    def station_s7(self) -> Outcome:
        said: List[str] = []
        try:
            return self.walk_s7(said)
        except StationStop as err:
            # a stop carries what S7 had said before it — the Treasury brought in, the money before — so the line tells the whole road
            raise StationStop("; ".join(said + [str(err)]))

    def walk_s7(self, said: List[str]) -> Outcome:
        clerk = self.clerk()
        holder_alone, two_signatures, tiers_read_from = self.tiers()
        failures = 0
        money: Dict[str, Any] = {"treasury": {}, "holdings": {}, "payments": []}
        self.facts["money"] = money
        workspace = self.request(clerk, "GET", "/v1/workspace", None, "S7")
        self.step("S7", workspace, "the workspace: its funding wallet (fundingWallet, with the fund sentence and the chains this deployment pays on, Spec 104 §1) and the platform account it stands on (workspace.aapAccountId)",
                  "answered" if workspace.ok else workspace.sentence(), None, clerk.name)
        view = workspace.json if isinstance(workspace.json, dict) else {}
        funding = view.get("fundingWallet") if isinstance(view.get("fundingWallet"), dict) and view["fundingWallet"].get("address") else None
        if funding and not self.facts.get("funding_wallet"):
            self.facts["funding_wallet"] = funding  # a run resumed past S5 still names the wallet in S8 and the summary
        if isinstance(view.get("workspace"), dict):
            self.facts["workspace"] = view  # the workspace's whole answer, as S5 keeps it; the platform account rides in workspace.aapAccountId
        if funding is None:
            self.note("S7", "Harness Holdings has no funding wallet (%s): the Treasury has no address to fund, and the estate refuses a run without one (routes/sets.ts, requireSourceAccount); see S5" % (
                view.get("fundingWalletAbsence") or workspace.sentence()))
        admin = self.read_admin_env("S7")
        # 1. Harness Holdings' money before: its USDC through the estate's own balances road, its gas account from the platform through the estate (§3, §5)
        if funding is not None:
            h_usdc, h_words, token = self.read_usdc_balance(self, clerk, "S7", "Harness Holdings")
            h_gas, h_gas_words = self.read_gas_account(self, clerk, "S7", "Harness Holdings")
        else:
            h_usdc, h_words, token = None, "Harness Holdings has no funding wallet, so its %s was not read" % T.PAYMENT_ASSET, None
            h_gas, h_gas_words = None, "Harness Holdings' gas account was not read: no funding wallet, so nothing of this run can leave"
        self.facts["usdc_token"] = token
        money["holdings"].update({"usdc_before": h_usdc, "gas_before": (h_gas or {}).get("balanceUsdCents"), "gas_available_before": (h_gas or {}).get("availableUsdCents"), "credited": 0, "received_minor": 0})
        need = sum(int(p.amount_minor) for p in A.PAYMENTS)
        shortfall = max(0, need - h_usdc) if (funding is not None and h_usdc is not None) else 0
        # 2. the Treasury (§2): brought in where Holdings is short of the three payments, or where it stands already (a passkey stored by an
        # earlier run, or --treasury-invite for the birth run, which prints the address and stops S7); an estate with no funding wallet has no
        # address to fund, so the Treasury is not asked, and the three payments below record the estate's own refusal
        treasury: Optional[Dict[str, Any]] = None
        t: Optional["Runner"] = None
        t_founder: Optional[Person] = None
        t_usdc: Optional[int] = None
        t_gas: Optional[Dict[str, Any]] = None
        if funding is not None and (shortfall > 0 or self.treasury_invite or self.treasury_passkey_stored()):
            treasury = self.bring_in_the_treasury("S7")
            t = self.treasury
            t_founder = t.founder()
            said.append(treasury["said"])
            t_usdc, t_words, _ = self.read_usdc_balance(t, t_founder, "S7", T.TREASURY["short"])
            t_gas, t_gas_words = self.read_gas_account(t, t_founder, "S7", T.TREASURY["short"])
        elif funding is None:
            t_words = "%s was not brought in: Harness Holdings has no funding wallet, so there is no address to fund" % T.TREASURY["short"]
            t_gas_words = "%s's gas account was not read" % T.TREASURY["short"]
            self.note("S7", t_words)
        else:
            t_words = "%s was not brought in: Harness Holdings holds %s, at or above the three payments' %s, and no Treasury passkey is stored" % (
                T.TREASURY["short"], T.usdc_dollars(h_usdc), T.usdc_dollars(need))
            t_gas_words = "%s's gas account was not read" % T.TREASURY["short"]
        money["treasury"].update({"usdc_before": t_usdc, "gas_before": (t_gas or {}).get("balanceUsdCents"), "address": (treasury or {}).get("address"), "credited": 0, "paid_minor": 0, "payment": None})
        said.append("before: %s; %s; %s; %s" % (h_words, t_words, h_gas_words, t_gas_words))
        # 3. the shortfall, paid by the Treasury through the estate's own road (§2), its gas credited first (§3; see the order above)
        if funding is not None and h_usdc is not None:
            if shortfall == 0:
                said.append("Harness Holdings holds %s, at or above the three payments' %s, so the Treasury was not asked to pay" % (T.usdc_dollars(h_usdc), T.usdc_dollars(need)))
            else:
                assert t is not None and t_founder is not None and treasury is not None
                if t_usdc is None or t_usdc < shortfall:
                    if treasury.get("born_this_run"):
                        # the birth run: the address is printed, and the run stops with the ship note's sentence — Bear funds it once, then reruns
                        sentence = T.FUND_TREASURY_SENTENCE % (treasury.get("address"), T.PAYEE_CHAIN)
                        self.note("S7", "%s (the three payments need %s and Harness Holdings holds %s; the Treasury holds %s); nothing was sent" % (
                            sentence, T.usdc_dollars(need), T.usdc_dollars(h_usdc), T.usdc_dollars(t_usdc) if t_usdc is not None else "a balance the estate could not say"))
                        raise StationStop(sentence)
                    sentence = T.TREASURY_SHORT_SENTENCE % (T.usdc_dollars(t_usdc) if t_usdc is not None else "a balance the estate could not say", T.usdc_dollars(shortfall),
                                                            treasury.get("address"), T.PAYEE_CHAIN)
                    self.note("S7", "%s (the three payments need %s and Harness Holdings holds %s); nothing was sent" % (sentence, T.usdc_dollars(need), T.usdc_dollars(h_usdc)))
                    raise StationStop("%s; nothing was sent" % sentence)
                credit = self.credit_gas(t, "S7", admin, T.TREASURY["short"], T.GAS_CREDIT_USD_CENTS)
                money["treasury"]["credited"] += credit["amount_usd_cents"]
                said.append(credit["said"])
                record = self.treasury_pays_the_shortfall(t, t_founder, clerk, shortfall, funding["address"], admin)
                money["treasury"]["payment"] = record
                said.append("Harness Treasury pays Harness Holdings (%s) the shortfall of %s: %s" % (funding["address"], T.usdc_dollars(shortfall), record["said"]))
                if record["landed"]:
                    money["treasury"]["paid_minor"] = shortfall
                    money["holdings"]["received_minor"] = shortfall
                    h_usdc = record["balance_after"] if record["balance_after"] is not None else h_usdc
                else:
                    failures += 1
        else:
            said.append("the Treasury was not asked to pay: %s" % ("Harness Holdings has no funding wallet" if funding is None else "Harness Holdings' %s could not be read" % T.PAYMENT_ASSET))
        # 4. S7a: the gas refusal proved on Holdings, whose gas account nobody has credited yet (§3)
        rows: List[Dict[str, Any]] = []
        for payment in A.PAYMENTS:
            row = self.pay_row(payment)
            if row is not None:
                rows.append(row)
        if funding is None:
            s7a = {"verdict": "not made", "said": "S7a not made: Harness Holdings has no funding wallet, so the estate refuses the set before its gas gate is reached", "ceiling": None}
            self.facts["s7a"] = s7a
            self.note("S7", s7a["said"])
        elif len(rows) == len(A.PAYMENTS):
            s7a = self.prove_the_gas_refusal(clerk, rows, h_gas, h_usdc)
        else:
            s7a = {"verdict": "failed", "said": "S7a not made: no address id for %s, so the set of three could not be reviewed" % ", ".join(
                p.payee_name for p in A.PAYMENTS if self.pay_row(p) is None), "ceiling": None}
            self.facts["s7a"] = s7a
        said.append(s7a["said"])
        if s7a["verdict"] == "failed":
            failures += 1
        # 5. the gas credits (§3): Holdings now, sized by S7a's ceiling as the sandbox may; the Treasury's where it stands and was not credited above
        if funding is not None:
            credit = self.credit_gas(self, "S7", admin, "Harness Holdings", self.gas_credit_for(s7a.get("ceiling")))
            money["holdings"]["credited"] += credit["amount_usd_cents"]
            said.append(credit["said"])
            if t is not None and not money["treasury"]["credited"]:
                credit = self.credit_gas(t, "S7", admin, T.TREASURY["short"], T.GAS_CREDIT_USD_CENTS)
                money["treasury"]["credited"] += credit["amount_usd_cents"]
                said.append(credit["said"])
        else:
            self.note("S7", "no gas was credited: Harness Holdings has no funding wallet, so no payment of this run could leave whatever its gas account holds")
        # 6. the three payments (§4), the signers pressing in the spec's order while a run waits
        signers = [self.people[k] for k in SIGNERS_IN_ORDER]

        def more_gas_for_holdings(ceiling: Optional[int]) -> bool:
            extra = self.credit_gas(self, "S7", admin, "Harness Holdings", self.gas_credit_for(ceiling))
            money["holdings"]["credited"] += extra["amount_usd_cents"]
            return True

        records: List[Dict[str, Any]] = []
        for payment in A.PAYMENTS:
            row = self.pay_row(payment)
            tier_words = under_the_tiers(payment.amount, holder_alone, two_signatures)
            if row is None:
                said.append("%s (%s %s, expected to %s): no address id for %s, so nothing was sent; %s" % (payment.key, payment.amount, T.PAYMENT_ASSET, payment.expect, payment.payee_name, tier_words))
                failures += 1
                continue
            address = row["oneOff"]["address"] if "oneOff" in row else T.address(payment.payee_key)
            expect_words = "%s; %s; expected to %s (figures from %s)" % (tier_words, self.TIER_ROAD_WORDS.get(payment.key, ""), payment.expect, tiers_read_from)
            record = self.pay(self, clerk, payment.key, row, int(payment.amount_minor), address, signers, expect_words,
                              lambda address=address: self.read_token_balance("S7", clerk.name, T.PAYEE_CHAIN, token, address), more_gas=more_gas_for_holdings)
            record.update(expect=payment.expect, tier_words=tier_words, amount=payment.amount)
            self.facts["sets"][payment.key] = record
            records.append(record)
        trail = self.read_trail(self, self.founder() if self.people[A.FOUNDER].signed_in else clerk, "S7",
                                "the trail: one %s row per payment that landed — userOpHash, the handleOps txHash, gasDebitUsdCents and gasDebit in the platform's own figures (Spec 104 §2, §5)" % T.INSTRUCTION_CONFIRMED) if records else None
        for record in records:
            self.judge_landing(record, trail)
            asked = record.get("approvals_required")
            said.append("%s (%s %s, expected to %s): %s; the estate asked %s signature(s) and %s; %s" % (
                record["key"], record["amount"], T.PAYMENT_ASSET, record["expect"], record["said"], asked if asked is not None else "?",
                self.TIER_ROAD_WORDS.get(record["key"], ""), record["tier_words"]))
            money["payments"].append({"key": record["key"], "amount_minor": record["amount_minor"], "landed": record["landed"], "gas_debit_cents": record.get("gas_debit_cents"),
                                      "user_op_hash": record.get("user_op_hash"), "tx_hash": record.get("tx_hash")})
            if not record["landed"]:
                failures += 1
        # 7. the money after (§5)
        h_usdc_after, h_words_after, _ = self.read_usdc_balance(self, clerk, "S7", "Harness Holdings") if funding is not None else (None, h_words, None)
        h_gas_after, h_gas_words_after = self.read_gas_account(self, clerk, "S7", "Harness Holdings") if funding is not None else (None, h_gas_words)
        if t is not None and t_founder is not None:
            t_usdc_after, t_words_after, _ = self.read_usdc_balance(t, t_founder, "S7", T.TREASURY["short"])
            t_gas_after, t_gas_words_after = self.read_gas_account(t, t_founder, "S7", T.TREASURY["short"])
        else:
            t_usdc_after, t_words_after, t_gas_after, t_gas_words_after = None, t_words, None, t_gas_words
        money["holdings"].update({"usdc_after": h_usdc_after, "gas_after": (h_gas_after or {}).get("balanceUsdCents"), "gas_available_after": (h_gas_after or {}).get("availableUsdCents")})
        money["treasury"].update({"usdc_after": t_usdc_after, "gas_after": (t_gas_after or {}).get("balanceUsdCents")})
        said.append("after: %s; %s; %s; %s" % (h_words_after, t_words_after, h_gas_words_after, t_gas_words_after))
        return Outcome("S7", FAIL if failures else PASS, "payments as %s: %s" % (clerk.name, "; ".join(said)))

    # -- S8 Journey and readiness --------------------------------------------------------
    def station_s8(self) -> Outcome:
        founder = self.founder()
        view = self.read_journey("S8", founder)
        current = view.get("currentStage")
        current_id = next((s.get("id") for s in view.get("stages") or [] if s.get("current")), None)
        readiness = self.request(founder, "GET", "/v1/workspace/readiness", None, "S8")
        self.step("S8", readiness, "transactable, reason, the workspace", "answered" if readiness.ok else readiness.sentence(), None, founder.name)
        self.facts["readiness"] = readiness.json if isinstance(readiness.json, dict) else None
        if not readiness.ok:
            raise StationStop("GET /v1/workspace/readiness answered %s" % readiness.sentence())
        done = [s.get("id") for s in view.get("stages") or [] if s.get("done")]
        # Spec T13 §5: the line names the funding wallet as the workspace last answered it, beside the readiness it decides
        wallet = self.facts.get("funding_wallet")
        if isinstance(wallet, dict) and wallet.get("address"):
            wallet_words = self.funding_wallet_words(wallet)
        elif self.facts.get("funding_wallet_absence"):
            wallet_words = "funding wallet: none — %s" % self.facts["funding_wallet_absence"]
        else:
            wallet_words = "funding wallet: not read in this run"
        return Outcome("S8", PASS, "journey stage %s of %s (%s); done: %s; readiness: transactable %s, reason %s; %s" % (
            current, view.get("stageCount"), current_id, ", ".join(done) or "none", readiness.json.get("transactable"), readiness.json.get("reason"), wallet_words))

    # -- S9 The tour -----------------------------------------------------------------------
    def station_s9(self) -> Outcome:
        return Outcome("S9", OUT_OF_SCOPE, "the tour's answers as Claude would see them are out of scope: the harness is the founder, not Claude")

    # -- S10 The auditor ----------------------------------------------------------------
    def station_s10(self) -> Outcome:
        before = len(self.findings)
        founder = self.people[A.FOUNDER]
        for interview_type in A.INTERVIEW_TYPES:
            readback = self.facts["readback"].get(interview_type)
            answers = self.facts["answers"].get(interview_type) or []
            book = A.ANSWERS.get(interview_type, {})
            lines = (readback or {}).get("lines") or []
            line_ids = [str(l.get("questionId")) for l in lines if not l.get("synthetic")]
            if readback:
                for f in audit_readback(interview_type, answers, lines):
                    if f.get("not_compared"):
                        self.note("S10", "%s: %s" % (f["probe"], f["said"]))
                    else:
                        self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
                # Spec T12 §0: the note says how many lines came from this run's answers and how many from the book
                self.note("S10", readback_provenance_note(interview_type, answers, lines))
            else:
                self.note("S10", "no read-back recorded for the %s interview in this run; the read-back comparison was not made" % interview_type)
            charter = self.facts["charter"].get(interview_type)
            if charter:
                # Spec T12 §0: the charter's expectation comes from the book for every question the read-back carries
                covered = {qid: book[qid] for qid in line_ids if qid in book}
                covered.update({q: v for q, v, _, _ in answers})
                for f in audit_charter(interview_type, charter, covered):
                    self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            else:
                self.note("S10", "no compiled charter recorded for the %s interview; the charter comparison was not made" % interview_type)
        if founder.signed_in:
            journey = self.read_journey("S10", founder)
            standing = self.request(founder, "GET", "/v1/onboarding/charter", None, "S10")
            self.step("S10", standing, "standsWritten", "answered" if standing.ok else standing.sentence(), None, founder.name)
            payees = self.request(founder, "GET", "/v1/payees", None, "S10")
            self.step("S10", payees, "the payees register", "answered" if payees.ok else payees.sentence(), None, founder.name)
            sets = self.request(founder, "GET", "/v1/sets", None, "S10")
            self.step("S10", sets, "the runs register", "answered" if sets.ok else sets.sentence(), None, founder.name)
            invites = self.request(founder, "GET", "/v1/invites", None, "S10")
            self.step("S10", invites, "the invitation register", "answered" if invites.ok else invites.sentence(), None, founder.name)
            self.facts["payees_register"] = payees.json if isinstance(payees.json, dict) else self.facts.get("payees_register")
            self.facts["sets_register"] = sets.json if isinstance(sets.json, dict) else None
            self.facts["invites_register"] = invites.json if isinstance(invites.json, dict) else self.facts.get("invites_register")
            registers = {
                "charter_stands_written": bool((standing.json or {}).get("standsWritten")) if isinstance(standing.json, dict) else None,
                "account_compiled": bool(self.facts["charter"].get("wallet_account")) or None,
                "payees": len((payees.json or {}).get("payees") or []) if isinstance(payees.json, dict) else None,
                "sets": len((sets.json or {}).get("sets") or []) if isinstance(sets.json, dict) else None,
                "wallets_absent": (self.facts.get("wallets") or {}).get("absence") if isinstance(self.facts.get("wallets"), dict) else None,
            }
            for f in audit_journey(journey, registers):
                self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            for f in audit_people(self.facts.get("invites_register"), self.facts["invites_minted"], {k: p.credential_id for k, p in self.people.items() if p.signed_in},
                                  retired=self.retired_passkeys()):
                if f.get("note"):
                    self.note("S10", f["said"])
                else:
                    self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            for f in audit_payees(self.facts.get("payees_register"), self.facts["payees"], self.facts["charter"].get("wallet_account")):
                self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            for note in self.seat_binding_notes():
                self.note("S10", note)
            self.audit_the_trail_for_moved_seats("S10", founder)  # Spec T15 §3
        else:
            self.note("S10", "the founder has no session; the registers were not read again")
        self.audit_the_money_moved("S10")  # Spec T14 §5: the auditor counts the money
        for f in audit_money(self.calls):
            self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
        for f in audit_refusals(self.calls):
            self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
        found = len(self.findings) - before
        refusals_met = len([c for c in self.calls if c.status >= 400 and c.station not in ("S10", "S11") and not c.outside])
        return Outcome("S10", PASS if found == 0 else FAIL, "the auditor: %d finding(s); %d refusal(s) met in S1 to S9 checked for Rule 13; %d call(s) checked for the minor-unit law" % (
            found, refusals_met, len(self.calls)))

    def audit_the_trail_for_moved_seats(self, station: str, founder: Person) -> None:
        """
        Spec T15 §3: for each seat S4 moved, the audit trail carries `roster.seat_rebound` (services/audit.ts; SPEC.md spells it
        `roster.seat.rebound`) naming the ceremony and every signer — read through the accountant's audit export, GET /v1/export/audit,
        the one road a browser reads the trail on (routes/exports.ts: `items`, oldest first, each with action, credential_id and detail).
        A row missing, or one naming another seat, another road or not every signer, is a finding; a row found is a note.
        """
        moved = self.facts.get("seats_moved") or []
        if not moved:
            return
        expected = "the trail: a %s row for each seat S4 moved (%s), naming the ceremony and every signer" % (
            T.ROSTER_SEAT_REBOUND, ", ".join("%s's" % m.get("name") for m in moved))
        answer = self.request(founder, "GET", "%s?limit=%d" % (T.AUDIT_EXPORT_ROUTE, T.AUDIT_EXPORT_LIMIT), None, station)
        rows = [r for r in ((answer.json or {}).get("items") or []) if isinstance(r, dict)] if answer.ok and isinstance(answer.json, dict) else None
        self.step(station, answer, expected, ("%d trail row(s)" % len(rows)) if rows is not None else answer.sentence(), None, founder.name)
        if rows is None:
            self.finding(station, "the audit trail", None, answer, expected, "the trail could not be read: %s" % answer.sentence())
            return
        for m in moved:
            probe = "the trail's %s row for %s's seat (ceremony %s…)" % (T.ROSTER_SEAT_REBOUND, m.get("name"), T.credential_short_form(m["pendingTxId"]))
            wanted = "one %s row with pendingTxId %s, seatEmail %s, via %s, and signerNames naming %s" % (
                T.ROSTER_SEAT_REBOUND, m["pendingTxId"], m.get("email"), T.VIA_ROSTER_CHANGE, names_in_words(m.get("signers") or []) or "every signer")
            hits = [r for r in rows if r.get("action") == T.ROSTER_SEAT_REBOUND and isinstance(r.get("detail"), dict) and str(r["detail"].get("pendingTxId")) == str(m["pendingTxId"])]
            if not hits:
                self.finding(station, probe, None, answer, wanted, "no %s row names the ceremony among %d trail row(s)" % (T.ROSTER_SEAT_REBOUND, len(rows)))
                continue
            detail = hits[-1]["detail"]
            names = [n.strip() for n in str(detail.get("signerNames") or "").split(",") if n.strip()]
            wrong: List[str] = []
            if str(detail.get("seatEmail") or "").lower() != str(m.get("email") or "").lower():
                wrong.append("seatEmail %r" % detail.get("seatEmail"))
            if detail.get("via") != T.VIA_ROSTER_CHANGE:
                wrong.append("via %r" % detail.get("via"))
            missing = [s for s in m.get("signers") or [] if s not in names]
            if missing:
                wrong.append("signerNames %r does not name %s" % (detail.get("signerNames"), names_in_words(missing)))
            if wrong:
                self.finding(station, probe, None, answer, wanted, "the row reads %s: %s" % (", ".join(wrong), json.dumps(detail, ensure_ascii=False)))
                continue
            self.note(station, "the trail carries %s for %s's seat: ceremony %s, signed by %s, moved from %s to %s on %s (via %s), at %s" % (
                T.ROSTER_SEAT_REBOUND, m.get("name"), m["pendingTxId"], detail.get("signerNames"), last4(detail.get("oldCredentialId")), last4(detail.get("newCredentialId")),
                detail.get("rosterName"), detail.get("via"), hits[-1].get("at")))

    def audit_the_money_moved(self, station: str) -> None:
        """
        Spec T14 §5: one note counting the money — Harness Treasury's USDC before and after, Harness Holdings' USDC before and after, the
        sum of the three payments, Holdings' gas account before and after against the sum of the three gas debits — and a finding where
        any pair does not reconcile to the cent. USDC is reckoned in its own minor units (six decimals, exact); the gas account in the
        platform's cents on `balanceUsdCents`, credits less debits: a reservation the platform has not yet released is not money moved.
        """
        money = self.facts.get("money") or {}
        treasury, holdings, payments = money.get("treasury") or {}, money.get("holdings") or {}, money.get("payments") or []
        if not money or "usdc_before" not in holdings or "usdc_after" not in holdings:
            outcome = self.outcome_of("S7")
            self.note(station, "the money was not counted: S7 did not read the balances before and after in this run (%s)" % ((outcome.line if outcome else "S7 did not run")[:240]))
            return

        def dollars(minor: Any) -> str:
            return T.usdc_dollars(minor) if isinstance(minor, int) else "unread"

        def cents(value: Any) -> str:
            return T.format_usd_cents(value) if isinstance(value, int) else "unread"

        landed = [p for p in payments if p.get("landed")]
        landed_sum = sum(int(p["amount_minor"]) for p in landed)
        payments_sum = sum(int(p.amount_minor) for p in A.PAYMENTS)
        debits = [p.get("gas_debit_cents") for p in landed]
        known_debits = [d for d in debits if isinstance(d, int)]
        paid = int(treasury.get("paid_minor") or 0)
        received = int(holdings.get("received_minor") or 0)
        pairs: List[Tuple[str, str, str, bool]] = []
        unread: List[str] = []
        tb, ta = treasury.get("usdc_before"), treasury.get("usdc_after")
        if isinstance(tb, int) and isinstance(ta, int):
            pairs.append(("Harness Treasury's %s" % T.PAYMENT_ASSET, "%s before, less %s paid to Harness Holdings: %s" % (dollars(tb), dollars(paid), dollars(tb - paid)), dollars(ta), tb - paid == ta))
        else:
            unread.append("Harness Treasury's %s (%s before, %s after)" % (T.PAYMENT_ASSET, dollars(tb), dollars(ta)))
        hb, ha = holdings.get("usdc_before"), holdings.get("usdc_after")
        if isinstance(hb, int) and isinstance(ha, int):
            pairs.append(("Harness Holdings' %s" % T.PAYMENT_ASSET, "%s before, plus %s received from the Treasury, less %s of payments that landed: %s" % (
                dollars(hb), dollars(received), dollars(landed_sum), dollars(hb + received - landed_sum)), dollars(ha), hb + received - landed_sum == ha))
        else:
            unread.append("Harness Holdings' %s (%s before, %s after)" % (T.PAYMENT_ASSET, dollars(hb), dollars(ha)))
        gb, ga = holdings.get("gas_before"), holdings.get("gas_after")
        credited = int(holdings.get("credited") or 0)
        if isinstance(gb, int) and isinstance(ga, int) and len(known_debits) == len(debits):
            pairs.append(("Harness Holdings' gas account", "%s before, plus %s credited, less %s of gas debits: %s" % (
                cents(gb), cents(credited), cents(sum(known_debits)), cents(gb + credited - sum(known_debits))), cents(ga), gb + credited - sum(known_debits) == ga))
        elif isinstance(gb, int) and isinstance(ga, int):
            self.finding(station, "money moved: a gas debit is not on the trail", None, None, "a gasDebitUsdCents on the %s row of each payment that landed" % T.INSTRUCTION_CONFIRMED,
                         "%d of %d landed payment(s) carry a gas debit; the gas account moved %s → %s" % (len(known_debits), len(debits), cents(gb), cents(ga)))
        else:
            unread.append("Harness Holdings' gas account (%s before, %s after)" % (cents(gb), cents(ga)))
        for probe, expected, got, ok in pairs:
            if not ok:
                self.finding(station, "money moved: %s does not reconcile to the cent" % probe, None, None, expected, "the estate reads %s after" % got)
        if pairs:
            gaps = sum(1 for _, _, _, ok in pairs if not ok)
            verdict = "every pair reconciles to the cent" if gaps == 0 else "%d pair(s) do not reconcile to the cent — findings above" % gaps
        else:
            verdict = "no pair could be counted"
        if unread:
            verdict += "; not counted: %s" % ", ".join(unread)
        self.note(station, "money moved (Spec T14 §5): Harness Treasury's %s %s → %s (paid %s); Harness Holdings' %s %s → %s (received %s; the three payments %s, of which %s landed); "
                  "Harness Holdings' gas account %s → %s (credited %s; gas debits %s over %d of %d payments that landed): %s" % (
                      T.PAYMENT_ASSET, dollars(tb), dollars(ta), dollars(paid), T.PAYMENT_ASSET, dollars(hb), dollars(ha), dollars(received), dollars(payments_sum), dollars(landed_sum),
                      cents(gb), cents(ga), cents(credited), cents(sum(known_debits)), len(known_debits), len(landed), verdict))

    def seat_binding_notes(self) -> List[str]:
        """
        Spec T12 §3: for each roster person whose S6 whitelist press was refused SIGNATURE_NOT_COUNTED, a note naming
        the credential the harness pressed with and the one the People register says they hold — so the report shows the
        platform's roster seat still bound to a retired passkey. It is a note, not a finding: the estate is telling the truth.
        One per person. Spec T15 §3: a person whose seat S4 moved in this run is not noted here — their refused press is S6's
        finding — so the note is dropped when there is nothing left to note.
        """
        register = self.facts.get("invites_register") or {}
        rows_by_email: Dict[str, List[Dict[str, Any]]] = {}
        for row in register.get("invites") or []:
            email = str(row.get("email") or "").strip().lower()
            if email and row.get("state") == "redeemed" and row.get("credentialId"):
                rows_by_email.setdefault(email, []).append(row)
        notes: List[str] = []
        seen: set = set()
        moved_keys = {m.get("key") for m in self.facts.get("seats_moved") or []}
        for record in self.facts["payees"]:
            for press in record.get("presses") or []:
                key = press.get("key")
                if press.get("refusal_code") != "SIGNATURE_NOT_COUNTED" or key in seen or key in moved_keys:
                    continue
                seen.add(key)
                pressed = press.get("credential")
                rows = rows_by_email.get(str(A.PEOPLE[key].email).lower(), []) if key in A.PEOPLE else []
                # the credential the People register says they hold: the one the harness pressed with where the register
                # carries a redeemed row for it (the person's own current credential), else the newest such row it names
                held = pressed if any(str(r.get("credentialId")) == str(pressed) for r in rows) else (rows[0].get("credentialId") if rows else None)
                held_words = last4(held) if held else "no credential the register names"
                notes.append(
                    "S6: %s's whitelist press was not counted (SIGNATURE_NOT_COUNTED); the harness pressed with %s, the credential of their own the People register says they hold (%s), "
                    "so the platform's roster seat is still bound to a retired passkey, and S4 found no roster change of theirs it could sign "
                    "(Spec 99's door; see S4's line). The estate is telling the truth: a note, not a finding." % (press.get("who"), last4(press.get("credential")), held_words))
        return notes

    # -- S11 The attacker ---------------------------------------------------------------
    def refused_or_finding(self, probe: str, sent: Any, answer: Answer, expected: str) -> bool:
        """A probe passes on a refusal that says why; any acceptance, or a refusal without its why, is a finding."""
        if answer.ok:
            self.finding("S11", probe, sent, answer, expected, "ACCEPTED: %s" % answer.sentence())
            return False
        why = refusal_without_why(answer.status, answer.text)
        if why:
            self.finding("S11", probe, sent, answer, expected, "refused without saying why: %s" % why)
            return False
        self.say("  S11 — refused as expected — %s: %s" % (probe, answer.sentence()))
        return True

    def probe_step(self, probe: str, answer: Answer, sent: Any, expected: str, who: str, result: Optional[str] = None) -> None:
        said = result if result is not None else (("accepted (%s)" if answer.ok else "refused: %s") % answer.sentence())
        self.step("S11", answer, expected, said, sent, who)
        self.evidence["S11"][-1]["probe"] = probe

    def accepted_or_finding(self, probe: str, sent: Any, answer: Answer, expected: str, law: str) -> bool:
        """The mirror of refused_or_finding, for a probe the law expects accepted: a refusal is the finding, with the ruling quoted."""
        if answer.ok:
            self.say("  S11 — accepted, as the law says — %s: HTTP %d" % (probe, answer.status))
            return True
        self.finding("S11", probe, sent, answer, expected, "REFUSED: %s — %s" % (answer.sentence(), law))
        return False

    def venue_law(self) -> Tuple[str, str]:
        """
        What the charter says the payee door does with a venue's contract, read at run time (Spec T11 §3): this run's compiled
        policy charter's `payeeVenueContracts` where S3 compiled one; where this run compiled none (a run resumed past S3), the
        answer book's C19 stands in and a note says so. 'refused' or 'accepted', and the words for where it was read.
        """
        charter = self.facts["charter"].get("policy")
        if charter:
            return venue_law_of(charter), "this run's compiled policy charter says payeeVenueContracts %s" % json.dumps(charter.get("payeeVenueContracts"), ensure_ascii=False)
        law = venue_law_of_the_book()
        book_c19 = json.dumps(A.POLICY_ANSWERS["C19"]["choice"], ensure_ascii=False)
        self.note("S11", "this run compiled no policy charter (S3 did not run), so the venue probe's expectation is read off the answer book's C19, %s" % book_c19)
        return law, "the answer book's C19 is %s" % book_c19

    def probe_venue_contract(self, founder: Person) -> None:
        """
        S11's venue probe: a payee whose address is a real venue contract, read from the corridor's tables.py at
        run time and never from a table of the harness's own.

        THE EXPECTATION FOLLOWS THE CHARTER (Spec T11, 21 September 2026). The first live run, 20 September 2026,
        called the estate's HTTP 201 a failure; Bear ruled the same morning: "Unless it is stipulated explicitly in
        the questionnaire, it must be accepted." The questionnaire decides policy, and a contract is an address —
        and the same day AER 360 Spec 92 gave the questionnaire the stipulation: C19, "May a payee address be the
        contract of a trading venue or exchange…", whose No compiles `payeeVenueContracts: 'refused'` and makes the
        payee door refuse a known venue's contract by name, PAYEE_IS_VENUE_CONTRACT, 422, in one sentence
        (services/payees.ts, assertPayeeIsNotVenueContract; packages/shared/src/refusals.ts). Harness Holdings
        answers No. So the probe reads the compiled charter's answer at run time: where it says refused, the door's
        own refusal in the charter's words is what the law says and an acceptance is the finding; where it says
        accepted, or was never asked, HTTP 201 is reported as accepted, as the law says, and a refusal is the
        finding, with the ruling quoted beside the estate's own sentence — the expectation of 20 September.
        """
        venue = T.venue_address_for_probe()
        probe = "a payee address that is a real venue contract (%s, read from the corridor's tables.py at run time)" % venue["what"]
        body = {"displayName": "Venue probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": venue["address"]}]}
        law, read_from = self.venue_law()
        self.facts["venue_law"] = law
        answer = self.request(founder, "POST", "/v1/payees", body, "S11")
        if law == "accepted":
            expected = "HTTP 201: accepted, as the law says (%s; %s)" % (VENUE_RULING, read_from)
            result = ("accepted, as the law says (%s)" % VENUE_RULING) if answer.ok else "refused: %s" % answer.sentence()
            self.probe_step(probe, answer, body, expected, founder.name, result=result)
            self.accepted_or_finding(probe, body, answer, expected, "the law says otherwise (%s; a contract is an address; %s)" % (VENUE_RULING, read_from))
            return
        venue_name = ESTATE_VENUE_NAMES.get(CORRIDOR_VENUE_IDS.get(venue["key"], ""), venue["what"])
        sentence = payee_is_venue_contract_sentence(venue_name, T.PAYEE_CHAIN)
        expected = "HTTP %d %s: %s (%s)" % (PAYEE_IS_VENUE_CONTRACT_STATUS, PAYEE_IS_VENUE_CONTRACT, sentence, read_from)
        refusal = answer.refusal or {}
        as_the_door_says = (answer.status == PAYEE_IS_VENUE_CONTRACT_STATUS and refusal.get("code") == PAYEE_IS_VENUE_CONTRACT
                            and str(refusal.get("message") or "") == sentence)
        if answer.ok:
            result = "accepted (HTTP %d) — the charter says otherwise" % answer.status
        elif as_the_door_says:
            result = "refused as the charter says (%s No): %s" % (VENUE_CONTRACT_QUESTION_ID, answer.sentence())
        else:
            result = "refused, but not as the charter's door refuses: %s" % answer.sentence()
        self.probe_step(probe, answer, body, expected, founder.name, result=result)
        if answer.ok:
            self.finding("S11", probe, body, answer, expected,
                         "ACCEPTED: HTTP %d — the charter answered No at %s (payeeVenueContracts refused), so the payee door must refuse %s, %d; it saved a venue's contract" % (
                             answer.status, VENUE_CONTRACT_QUESTION_ID, PAYEE_IS_VENUE_CONTRACT, PAYEE_IS_VENUE_CONTRACT_STATUS))
            return
        why = refusal_without_why(answer.status, answer.text)
        if why:
            self.finding("S11", probe, body, answer, expected, "refused without saying why: %s" % why)
            return
        if not as_the_door_says:
            self.finding("S11", probe, body, answer, expected,
                         "REFUSED, but not as the charter's door refuses: %s — expected %s, %d, %r" % (answer.sentence(), PAYEE_IS_VENUE_CONTRACT, PAYEE_IS_VENUE_CONTRACT_STATUS, sentence))
            return
        self.say("  S11 — refused as the charter says — %s: %s" % (probe, answer.sentence()))

    def station_s11(self) -> Outcome:
        before = len(self.findings)
        founder = self.founder()
        probes = 0
        # 1. A mutating call without the x-csrf-token header (guards.ts requireMutatingSession → assertCsrf).
        probes += 1
        probe = "a mutating call without the x-csrf-token header (POST /v1/workspace/display-currency)"
        body = {"displayCurrency": A.ESTATE["display_currency"]}
        answer = self.request(founder, "POST", "/v1/workspace/display-currency", body, "S11", csrf=False)
        self.probe_step(probe, answer, body, "401 NOT_AUTHENTICATED, missing or incorrect CSRF token", founder.name)
        self.refused_or_finding(probe, body, answer, "refused: the session's own token is required on every state-changing request")
        # 2. A second person's session against the founder's interview: Ben confirms it with Harriet's passkey.
        probes += 1
        probe = "a second person's session against the founder's interview (Ben confirms the policy interview with the founder's passkey)"
        ben = self.people["ben"]
        interview_id = self.facts["interview"].get("policy")
        if ben.signed_in and interview_id:
            options = self.request(ben, "POST", "/v1/onboarding/interviews/%s/confirm/options" % interview_id, {}, "S11")
            self.probe_step(probe + " — the challenge", options, {}, "a challenge, or a refusal", ben.name)
            if options.ok and isinstance(options.json, dict):
                challenge = str((options.json.get("options") or {}).get("challenge"))
                confirm_body = {"issuedAtMs": options.json.get("issuedAtMs"), "response": self.assertion_for(founder, challenge, "S11")}
                confirmed = self.request(ben, "POST", "/v1/onboarding/interviews/%s/confirm" % interview_id, confirm_body, "S11")
                self.probe_step(probe, confirmed, confirm_body, "a refusal by name (INTERVIEW_NOT_OPEN or STEP_UP_INVALID)", ben.name)
                self.refused_or_finding(probe, confirm_body, confirmed, "refused: the founder's passkey does not confirm under Ben's session, and a written interview is not confirmed again")
            else:
                self.refused_or_finding(probe, {}, options, "refused")
        else:
            self.note("S11", "probe not made: %s" % ("Ben has no session" if not ben.signed_in else "no policy interview id in this run"))
        # 3. A viewer's session against each author route.
        olive = self.people[A.VIEWER_INVITED]
        viewer_said = self.bring_in("S11", olive, "viewer")
        self.say("  S11: %s %s" % (olive.name, viewer_said))
        viewer_probes = [
            ("POST", "/v1/payees", {"displayName": "Viewer probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]}),
            ("POST", "/v1/sets", {"pays": [{"oneOff": {"chain": T.PAYEE_CHAIN, "address": T.address("UNLISTED_ETHEREUM"), "declared": True}, "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": "1000000"}],
                                  "duplicatesAcknowledged": False, "idempotencyKey": "aer360-harness-%s-viewer" % self.run_stamp, "reference": "Viewer probe"}),
            ("POST", "/v1/invites", {"displayName": "Viewer probe", "email": "harness+probe@aeredium.io", "role": "author"}),
            ("POST", "/v1/onboarding/interviews/%s/answers" % (interview_id or "<policy interview>"), {"questionId": "A1", "value": {"text": "Viewer probe"}}),
        ]
        for method, path, body in viewer_probes:
            probes += 1
            probe = "a viewer's session at an author route: %s %s" % (method, path)
            if not olive.signed_in:
                self.note("S11", "probe not made (%s): the viewer has no session — %s" % (probe, viewer_said))
                continue
            answer = self.request(olive, method, path, body, "S11")
            self.probe_step(probe, answer, body, "403 ROLE_NOT_GRANTED naming the room, the standing held and the standing needed", olive.name)
            self.refused_or_finding(probe, body, answer, "refused by the guard, by name")
        # 4. An invitation for the principal role.
        probes += 1
        probe = "an invitation for the principal role"
        body = {"displayName": "Principal probe", "email": "harness+principal@aeredium.io", "role": "principal"}
        answer = self.request(founder, "POST", "/v1/invites", body, "S11")
        self.probe_step(probe, answer, body, "422 INVITE_ROLE_NOT_AVAILABLE, refused by name", founder.name)
        self.refused_or_finding(probe, body, answer, "refused by name: the principal road is not built")
        # 5, 6 and 14. Probe drafts: a question not served, an answer of the wrong kind, a compile before confirm.
        drafts: List[Tuple[str, str]] = []
        started = self.request(founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"}, "S11")
        self.probe_step("a probe draft of the policy interview", started, {"interviewType": "policy"}, "a fresh draft, deleted at the end of S11", founder.name)
        if started.ok and isinstance(started.json, dict):
            draft_id = str((started.json.get("interview") or {}).get("id"))
            draft_state = (started.json.get("interview") or {}).get("state")
            if draft_state in ("in_progress",) and (started.json.get("page") or {}).get("question", {}).get("questionId") == "A1":
                drafts.append(("policy", draft_id))
                probes += 1
                probe = "an answer for a question the interview did not serve (B4 while A9 is unanswered)"
                body = {"questionId": "B4", "value": {"choices": []}}
                answer = self.request(founder, "POST", "/v1/onboarding/interviews/%s/answers" % draft_id, body, "S11")
                self.probe_step(probe, answer, body, "400 ANSWER_INVALID: this question is not asked given the answers so far", founder.name)
                self.refused_or_finding(probe, body, answer, "refused: a question the interview did not serve takes no answer")
                probes += 1
                probe = "a compile before confirm"
                answer = self.request(founder, "POST", "/v1/onboarding/interviews/%s/compile" % draft_id, {}, "S11")
                self.probe_step(probe, answer, {}, "409 INTERVIEW_NOT_OPEN: the compiler reads only confirmed interviews", founder.name)
                self.refused_or_finding(probe, {}, answer, "refused: nothing compiles before the read-back is confirmed under a passkey")
            else:
                self.note("S11", "the policy draft came back in state %r at %s, not a fresh draft; the draft probes were not made on it" % (
                    draft_state, (started.json.get("page") or {}).get("question", {}).get("questionId")))
        account = self.request(founder, "POST", "/v1/onboarding/interviews", {"interviewType": "wallet_account"}, "S11")
        self.probe_step("a probe draft of the wallet account interview", account, {"interviewType": "wallet_account"}, "a fresh draft, deleted at the end of S11", founder.name)
        if account.ok and isinstance(account.json, dict):
            draft_id = str((account.json.get("interview") or {}).get("id"))
            page = account.json.get("page") or {}
            if (account.json.get("interview") or {}).get("state") == "in_progress" and (page.get("question") or {}).get("questionId") == "W0":
                drafts.append(("wallet_account", draft_id))
                for qid in ("W0", "WN", "W1"):
                    value = A.ACCOUNT_ANSWERS[qid]
                    page_answer = self.request(founder, "POST", "/v1/onboarding/interviews/%s/answers" % draft_id, {"questionId": qid, "value": value}, "S11")
                    self.probe_step("the probe draft walked to its first money question", page_answer, {"questionId": qid, "value": value}, "the next page", founder.name)
                    if not page_answer.ok:
                        break
                probes += 1
                probe = "an answer of the wrong kind (a string where money is asked, O1)"
                body = {"questionId": "O1", "value": {"cents": "fifty thousand dollars"}}
                answer = self.request(founder, "POST", "/v1/onboarding/interviews/%s/answers" % draft_id, body, "S11")
                self.probe_step(probe, answer, body, "400 ANSWER_INVALID: an amount is a whole number of cents", founder.name)
                self.refused_or_finding(probe, body, answer, "refused: money is a whole number of cents, never a string of words")
            else:
                self.note("S11", "the wallet account draft did not open at W0 in_progress; the wrong-kind probe was not made")
        # 7 and 8. A passkey assertion replayed with a challenge already used; an assertion signed for the wrong rpId.
        probes += 1
        probe = "a passkey assertion replayed with a challenge already used"
        if founder.passkey is not None:
            first, bundle = self.sign_in(founder, "S11")
            self.probe_step(probe + " — the first sign-in", first, {"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<assertion>"}, "200: a fresh session", founder.name)
            if first.ok:
                replay, _ = self.sign_in(founder, "S11", replay_of=bundle)
                self.probe_step(probe, replay, {"nonce": "<the same nonce>", "issuedAtMs": "<the same issuedAtMs>", "response": "<a new assertion over the same challenge>"},
                                "403 STEP_UP_STALE: challenge already used", founder.name)
                self.refused_or_finding(probe, {"nonce": bundle.get("nonce"), "issuedAtMs": bundle.get("issuedAtMs")}, replay, "refused: a challenge is used once")
            else:
                self.note("S11", "the replay probe was not made: the first sign-in answered %s" % first.sentence())
            probes += 1
            probe = "an assertion signed for the wrong rpId"
            wrong, bundle = self.sign_in(founder, "S11", rp_id="not-the-estate.invalid")
            self.probe_step(probe, wrong, {"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<assertion whose rpIdHash is not the estate's>"},
                            "403 STEP_UP_INVALID: the relying party id hash does not match", founder.name)
            self.refused_or_finding(probe, {"rpId": "not-the-estate.invalid"}, wrong, "refused: an assertion for another relying party is not this estate's")
        else:
            self.note("S11", "the passkey probes were not made: the founder holds no passkey in this run")
        # 9 and 10. A payee address with a wrong checksum (a refusal expected); a payee address that is a real
        # venue contract (the charter decides: refused by name where C19 is No, else accepted — a contract is an address).
        probes += 1
        probe = "a payee address with a wrong checksum"
        broken = T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))
        body = {"displayName": "Checksum probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": broken}]}
        answer = self.request(founder, "POST", "/v1/payees", body, "S11")
        self.probe_step(probe, answer, body, "a refusal (ADDRESS_MALFORMED), or the estate's acceptance recorded as it is", founder.name)
        self.refused_or_finding(probe, body, answer, "refused: an address whose checksum is wrong is not an address")
        probes += 1
        self.probe_venue_contract(founder)  # expects what the compiled charter says (Spec T11): refused by name under C19 No, else accepted as the law says
        # 11. A payment above the per-payment limit from the clerk (S7's P3), not released without approval.
        probes += 1
        probe = "the clerk's payment above the per-payment limit (S7's P3) released without approval?"
        p3 = self.facts["sets"].get("P3")
        if p3 and isinstance(p3.get("view"), dict):
            set_view = (p3["view"].get("set") or {})
            status = set_view.get("status")
            required = (set_view.get("approval") or {}).get("approvalsRequired")
            if status == "approved" and (required or 0) == 0:
                self.finding("S11", probe, p3.get("created"), None, "the run waits for an approval", "ACCEPTED: the sandbox approved a %s payment at submission with %s approvals required" % (A.PAYMENTS[2].amount, required))
            else:
                self.say("  S11 — as expected — %s: status %s, approvalsRequired %s" % (probe, status, required))
        else:
            self.note("S11", "probe not made (%s): S7 created no run for P3 (%s)" % (probe, (p3 or {}).get("refusal")))
        # 12. The clerk approving her own payment.
        probes += 1
        probe = "the clerk approving her own payment (S7's P3)"
        cora = self.people[A.PAYMENT_CLERK]
        if p3 and p3.get("set_id") and cora.signed_in and p3.get("submitted") and isinstance(p3.get("submitted"), dict):
            challenge = self.request(cora, "POST", "/v1/approvals/%s/challenge" % p3["set_id"], {}, "S11")
            self.probe_step(probe + " — the challenge", challenge, {}, "403 ROLE_NOT_GRANTED or SUBMITTER_MAY_NOT_APPROVE, in the charter's words", cora.name)
            if challenge.ok and isinstance(challenge.json, dict):
                approve_body = {"response": self.assertion_for(cora, str(challenge.json.get("challenge")), "S11")}
                approved = self.request(cora, "POST", "/v1/approvals/%s/approve" % p3["set_id"], approve_body, "S11")
                self.probe_step(probe, approved, approve_body, "a refusal", cora.name)
                self.refused_or_finding(probe, approve_body, approved, "refused: the person who entered a payment does not release it alone")
            else:
                self.refused_or_finding(probe, {}, challenge, "refused: the person who entered a payment does not release it alone")
        else:
            self.note("S11", "probe not made (%s): %s" % (probe, "Cora has no session" if not cora.signed_in else "S7 left no submitted run for P3"))
        # 13. A second confirm of an already confirmed interview.
        probes += 1
        probe = "a second confirm of an already confirmed interview (the policy interview)"
        if interview_id:
            options = self.request(founder, "POST", "/v1/onboarding/interviews/%s/confirm/options" % interview_id, {}, "S11")
            self.probe_step(probe + " — the challenge", options, {}, "a challenge, or a refusal", founder.name)
            if options.ok and isinstance(options.json, dict):
                body = {"issuedAtMs": options.json.get("issuedAtMs"), "response": self.assertion_for(founder, str((options.json.get("options") or {}).get("challenge")), "S11")}
                confirmed = self.request(founder, "POST", "/v1/onboarding/interviews/%s/confirm" % interview_id, body, "S11")
                self.probe_step(probe, confirmed, body, "409 INTERVIEW_NOT_OPEN: confirm happens at the read-back", founder.name)
                self.refused_or_finding(probe, body, confirmed, "refused: a confirmed interview is not confirmed again")
            else:
                self.refused_or_finding(probe, {}, options, "refused")
        else:
            self.note("S11", "probe not made (%s): no policy interview id in this run" % probe)
        # The probe drafts are deleted: what a founder does with a draft they started by mistake.
        for interview_type, draft_id in drafts:
            deleted = self.request(founder, "DELETE", "/v1/onboarding/interviews/%s" % draft_id, None, "S11")
            self.probe_step("the %s probe draft deleted" % interview_type, deleted, None, "{deleted: true}", founder.name)
        found = len(self.findings) - before
        return Outcome("S11", PASS if found == 0 else FAIL, "the attacker: %d probe(s), %d finding(s)" % (probes, found))

    # -- S12 The optimizer --------------------------------------------------------------
    def station_s12(self) -> Outcome:
        """
        The optimizer measures and never judges (Spec T8): every call over two seconds is listed with its route,
        and the station passes with its numbers. A slow invitation is explained where it is listed — the
        invitation road sends the email before it answers — rather than counted against anybody.
        """
        measure = optimizer_measures(self.calls, self.facts["served_twice"])
        self.facts["optimizer"] = measure
        for line in measure["lines"]:
            self.say("  S12: %s" % line)
        return Outcome("S12", PASS, "the optimizer: %d call(s), %d over %.0f seconds, largest answer %d bytes, %d retried after a 5xx; the interviews took %d call(s), %d of them reads a browser would not make" % (
            measure["calls"], len(measure["slow"]), SLOW_CALL_SECONDS, measure["largest"]["size"] if measure["largest"] else 0,
            len(measure["retried"]), measure["interview_calls"], measure["wasted_reads"]))

    # -- the report ------------------------------------------------------------------------
    def report(self) -> str:
        lines: List[str] = []
        lines.append("# AER 360 estate harness run — %s — %s" % (A.ESTATE["company"], self.started_at))
        lines.append("")
        lines.append("Specs T7 and T8, 19 and 20 September 2026. Base URL %s. The harness is the founder, not a judge; a failure below is evidence, not a verdict: "
                     "what was sent (secrets and passkey material redacted to their last four characters), what came back word for word, the route, the expectation and the result. "
                     "This report names no real person and no real company: the estate and its people are the harness's own." % self.base)
        lines.append("")
        last = self.last_run()
        fates = compare_findings(last["findings"], self.findings) if last else None
        lines.append("## The closing table")
        lines.append("")
        if last:
            lines.append("| Station | Outcome | Last run | Line |")
            lines.append("|---|---|---|---|")
        else:
            lines.append("| Station | Outcome | Line |")
            lines.append("|---|---|---|")
        for o in self.outcomes:
            cells = ["%s %s" % (o.station, dict(STATIONS).get(o.station, "")), o.outcome]
            if last and fates is not None:
                cells.append(self.last_run_cell(last, fates, o.station))
            cells.append(o.line)
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
        lines.append("")
        lines.append("Findings under S10 and S11: %d." % len(self.findings))
        lines.append("")
        lines.extend(self.funding_summary_lines())  # Spec T13 §5: the funding wallet, the gas and the asset, by eye
        if last and fates is not None:
            lines.append("")
            lines.append("Since the last run (%s, started %s): %d closed, %d still open, %d new. A finding is closed when the last run raised it and this run did not, "
                         "still open when both did, new when only this run did; findings are matched by station and probe, with the ids a run mints set aside." % (
                             last["name"], last.get("started_at") or "time unknown", len(fates["closed"]), len(fates["still_open"]), len(fates["new"])))
            for word, key in (("closed", "closed"), ("still open", "still_open"), ("new", "new")):
                for f in fates[key]:
                    lines.append("- %s — %s — %s" % (word, f["station"], f["probe"]))
        if self.evidence.get("resume"):
            lines.append("")
            lines.append("## Resume")
            lines.extend(self.render_steps(self.evidence["resume"]))
        for station, title in STATIONS:
            outcome = self.outcome_of(station)
            lines.append("")
            lines.append("## %s — %s" % (station, title))
            lines.append("")
            lines.append("Outcome: **%s**. %s" % (outcome.outcome if outcome else NOT_RUN, outcome.line if outcome else ""))
            for note in self.notes.get(station, []):
                lines.append("")
                lines.append("Note: %s" % note)
            findings = [f for f in self.findings if f.station == station]
            if findings:
                lines.append("")
                lines.append("### Findings")
                for f in findings:
                    lines.append("")
                    lines.append("- **%s** — %s" % (f.probe, f.said))
                    if f.route:
                        lines.append("  - Route: %s" % f.route)
                    if f.sent is not None:
                        lines.append("  - Sent: `%s`" % json.dumps(f.sent, ensure_ascii=False))
                    if f.came_back:
                        lines.append("  - Came back, verbatim: `%s`" % f.came_back)
                    lines.append("  - Expected: %s" % f.expected)
            steps = self.evidence.get(station, [])
            if steps:
                lines.append("")
                lines.append("### Evidence, call by call")
                lines.extend(self.render_steps(steps))
            if station == "S12" and self.facts.get("optimizer"):
                lines.append("")
                for line in self.facts["optimizer"]["lines"]:
                    lines.append("- %s" % line)
        lines.append("")
        lines.append("## Every call")
        lines.append("")
        lines.append("| At | Station | Who | Route | Status | ms | Bytes |")
        lines.append("|---|---|---|---|---|---|---|")
        for c in self.calls:
            lines.append("| %s | %s | %s | %s | %d | %d | %d |" % (c.at, c.station, c.who, c.route, c.status, c.elapsed_ms, c.size))
        return "\n".join(lines) + "\n"

    def last_run(self) -> Optional[Dict[str, Any]]:
        """The previous report in the working folder, looked for once per run, so a rerun after a fix can say what closed (Spec T8)."""
        if not self._last_run_looked_for:
            self._last_run_looked_for = True
            self.last_run_report = find_last_report(self.out_dir, self.started_at)
        return self.last_run_report

    @staticmethod
    def last_run_cell(last: Dict[str, Any], fates: Dict[str, List[Dict[str, Any]]], station: str) -> str:
        """The closing table's last-run cell: the station's previous outcome, then its findings' fates by probe."""
        previous = last["outcomes"].get(station)
        parts = ["last run %s" % previous if previous else "not in the last run"]
        for word, key in (("closed", "closed"), ("still open", "still_open"), ("new", "new")):
            probes = [f["probe"] for f in fates[key] if f["station"] == station]
            if probes:
                parts.append("%d %s: %s" % (len(probes), word, "; ".join(probes)))
        return " · ".join(parts)

    def render_steps(self, steps: List[Dict[str, Any]]) -> List[str]:
        out: List[str] = []
        for index, s in enumerate(steps, 1):
            out.append("")
            out.append("%d. %s%s — %s" % (index, ("[%s] " % s["probe"]) if s.get("probe") else "", s["route"], s.get("who", "")))
            out.append("   - Expected: %s" % s["expected"])
            out.append("   - Result: %s (HTTP %s, %s ms)" % (s["result"], s["status"], s.get("elapsed_ms")))
            if s.get("sent") is not None:
                out.append("   - Sent: `%s`" % json.dumps(s["sent"], ensure_ascii=False))
            out.append("   - Came back, verbatim:")
            out.append("")
            out.append("     ```")
            for text_line in str(s["came_back"]).splitlines() or [""]:
                out.append("     " + text_line)
            out.append("     ```")
        return out

    def write_report(self) -> str:
        os.makedirs(self.out_dir, exist_ok=True)
        date = _dt.datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(self.out_dir, "aer360-harness-%s.md" % date)
        if os.path.exists(path):
            path = os.path.join(self.out_dir, "aer360-harness-%s-%s.md" % (date, _dt.datetime.now().strftime("%H%M%S")))
        text = self.report()  # rendered before the file exists, so the previous report is found and this one is never its own last run
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path


# ---------------------------------------------------------------------------
# The auditor's comparisons (S10), as functions over recorded facts so a fixture can prove them.
# ---------------------------------------------------------------------------
def spoken_entry(entry: Dict[str, Any]) -> str:
    """One list entry as the read-back speaks it: its values in the order the estate stores them, joined by ' — '."""
    stored = A.as_the_estate_stores(entry) if isinstance(entry, dict) else {}
    return " — ".join("" if v is None else str(v) for v in stored.values())


def spoken_for(kind: str, question_id: str, value: Dict[str, Any]) -> Optional[str]:
    """
    The sentence the read-back speaks for an answer, in the estate's own forms (Spec T8) — services/onboarding.ts,
    readback(), the `spoken` switch, read from the code at main after PR #108 (commit dff4c9a, where that file is
    e651616's byte for byte), not guessed:

      statement      'Stated and acknowledged.'
      single_choice  the choice
      multi_choice   the choices joined by ', '; none chosen: B4's fail-closed sentence, otherwise 'None chosen.'
      text           the text, trimmed, or 'Left blank.'
      currency       its code — the text, trimmed (Spec 88's `spokenAnswer` arm, commit 35cdc6f). On main the kind
                     has no arm and falls to the switch's default, JSON.stringify, which the live run of 20 September
                     2026 heard as '{"text":"AUD"}'; that stays a finding of the estate's until Spec 88 lands
      list           each entry's values in the order the estate stores them — jsonb's: shortest key first, then byte
                     order (A.as_the_estate_stores) — joined by ' — ', the entries joined by '; '; none: 'No entries.'
                     For the census that reads name — role — email
      money          'US$<whole, grouped> and <cents, two digits> cents.'; left empty: the no-limit sentence
      percent        '<figure> per cent.'; left empty: T4's own sentence, otherwise 'Left empty — no share is set.'
      count          '<figure, grouped> payment(s) in a day.'; left empty: 'Left empty — no limit on how many.'
      roster_*       the people joined by ', ', or 'No one chosen.'
      person_or_none '<name> — <email>.' where a person is named (the email alone where the name is blank); otherwise
                     the option's own sentence with a full stop, or 'No one chosen.' (Spec 92, WO1; read at cf3be4a)
      money, a zero  '<figure> — nothing is paid under this rule until you write a figure.' (Spec 90: a zero is a wall)

    A kind not listed has no rendering here, and None is returned: the comparison then says 'not compared: no
    rendering for kind <k>' rather than calling a difference it cannot judge a finding.
    """
    if kind == "statement":
        return "Stated and acknowledged."
    if kind == "single_choice":
        return str(value.get("choice") or "")
    if kind == "multi_choice":
        choices = value.get("choices") or []
        if choices:
            return ", ".join(str(c) for c in choices)
        if question_id == "B4":
            return ("No grants made — each level below you sees only its own level, and you see every level. "
                    "The safest answer, and the one that stands until you change it.")
        return "None chosen."
    if kind in ("text", "currency"):
        text = str(value.get("text") or "").strip()
        return text or "Left blank."
    if kind == "list":
        entries = value.get("entries") or []
        return "; ".join(spoken_entry(e) for e in entries) or "No entries."
    if kind == "money":
        cents = value.get("cents")
        if cents is None:
            return "Left empty — no limit; the loosest possible answer."
        whole, frac = divmod(int(cents), 100)
        figure = "US$%s and %02d cents" % ("{:,}".format(whole), frac)
        if int(cents) == 0:
            return "%s — nothing is paid under this rule until you write a figure." % figure
        return figure + "."
    if kind == "person_or_none":
        person = value.get("person")
        if isinstance(person, dict) and str(person.get("email") or "").strip():
            name = str(person.get("name") or "").strip()
            email = str(person.get("email")).strip()
            return "%s — %s." % (name, email) if name else "%s." % email
        choice_text = str(value.get("choice") or "").strip()
        return "%s." % choice_text if choice_text else "No one chosen."
    if kind == "percent":
        percent = value.get("percent")
        if percent is None:
            return "Left empty — never halts on pace." if question_id == "T4" else "Left empty — no share is set."
        figure = str(int(percent)) if isinstance(percent, float) and percent.is_integer() else str(percent)
        return "%s per cent." % figure
    if kind == "count":
        count = value.get("count")
        if count is None:
            return "Left empty — no limit on how many."
        return "%s %s in a day." % ("{:,}".format(count), "payment" if count == 1 else "payments")
    if kind in ("roster_single", "roster_multi"):
        return ", ".join(str(p) for p in value.get("people") or []) or "No one chosen."
    return None


def readback_disagreements(probe: str, kind: str, value: Dict[str, Any], expected: str, said: str) -> List[Dict[str, Any]]:
    """
    What differs between the line the estate spoke and the answer given, by content. A list is compared entry by
    entry, and each finding names the entry that differs — its place and its first value, the name — so a moved
    word in one census row is one finding about that row. Anything else, or a list whose entry count differs, is
    one finding carrying both lines whole.
    """
    if kind == "list":
        entries = [e for e in (value.get("entries") or []) if isinstance(e, dict)]
        given = [spoken_entry(e) for e in entries]
        heard = said.split("; ") if said and said != "No entries." else []
        if given and len(given) == len(heard):
            out: List[Dict[str, Any]] = []
            for index, (g, h) in enumerate(zip(given, heard), 1):
                if g != h:
                    named = g.split(" — ", 1)[0] or ("entry %d" % index)
                    out.append({"probe": "%s, entry %d (%s)" % (probe, index, named), "sent": entries[index - 1], "expected": g,
                                "said": "the read-back says %r for this entry" % h})
            if out:
                return out
    if kind == "money" and said == WRITTEN_DOLLAR_SPOKEN and expected != WRITTEN_DOLLAR_SPOKEN:
        # Spec T11: WO3 and WO4 arrive written at one dollar; a read-back still speaking it did not take the figure the book wrote
        return [{"probe": probe, "sent": value, "expected": expected,
                 "said": "the read-back says %r — the figure the field arrived written with, not the %r the book wrote" % (said, expected)}]
    return [{"probe": probe, "sent": value, "expected": expected, "said": "the read-back says %r" % said}]


def audit_readback(interview_type: str, answers: Sequence[Tuple[str, Dict[str, Any], str, str]], lines: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    The read-back compared by content, line by line (Spec T8), with the expectation for every line the estate
    speaks taken from the book (A.ANSWERS) for every question the read-back carries, whether or not this run
    answered it (Spec T12 §0). A resumed interview's read-back carries the answers earlier runs gave to the rest,
    and the book is what those answers were; comparing only against this run's answers made every earlier answer a
    finding. So a line this run answered is rendered from what it sent (and its prompt is checked); a line only the
    book knows is rendered from the book; a line the book does not know is a finding as before. An answer of a kind
    with no rendering is not compared (not_compared=True), which S10 records as a note. The provenance count — how
    many lines came from this run and how many from the book — is written by S10, which holds the counts.
    """
    findings: List[Dict[str, Any]] = []
    book = A.ANSWERS.get(interview_type, {})
    run_answered = {str(qid): (value, prompt, kind) for qid, value, prompt, kind in answers}
    spoken = {str(l.get("questionId")): l for l in lines if not l.get("synthetic")}
    # a question this run answered that the read-back carries no line for is a finding (a dropped answer)
    for qid, (value, prompt, kind) in run_answered.items():
        if qid not in spoken:
            expected = spoken_for(kind, qid, value)
            findings.append({"probe": "read-back (%s) of %s" % (interview_type, qid), "sent": value,
                             "expected": expected if expected is not None else json.dumps(value, ensure_ascii=False),
                             "said": "the read-back has no line for %s, which was answered" % qid})
    for qid, line in spoken.items():
        probe = "read-back (%s) of %s" % (interview_type, qid)
        said = str(line.get("spoken"))
        if qid in run_answered:
            value, prompt, kind = run_answered[qid]
        elif qid in book:
            value, prompt, kind = book[qid], None, A.kind_of(interview_type, qid)
        else:
            findings.append({"probe": probe, "sent": None, "expected": "no line for a question the book does not know",
                             "said": "the read-back carries a line for %s, which the harness did not answer and the book does not know: %r" % (qid, said)})
            continue
        expected = spoken_for(kind, qid, value) if kind else None
        if expected is None:
            findings.append({"probe": probe, "sent": value, "expected": None, "not_compared": True,
                             "said": "not compared: no rendering for kind %s (the read-back says %r)" % (kind, said)})
        elif said != expected:
            findings.extend(readback_disagreements(probe, kind, value, expected, said))
        if prompt and str(line.get("prompt")) != prompt:
            findings.append({"probe": probe + " (the prompt)", "sent": prompt, "expected": prompt, "said": "the read-back's prompt is %r" % line.get("prompt")})
    # Spec T11: C19 answered No — the read-back says what the payee door will do, in its own line (VENUE_DOOR_READBACK_QUESTION_ID).
    # Spec T12 §0: the C19 answer is read from this run's answers or, failing that, the book, like every other line.
    c19 = run_answered["C19"][0] if "C19" in run_answered else book.get("C19")
    if "C19" in spoken and isinstance(c19, dict) and c19.get("choice") == A.VENUE_NO:
        door = next((l for l in lines if str(l.get("questionId")) == VENUE_DOOR_READBACK_QUESTION_ID), None)
        probe = "read-back (%s) of C19: the door's sentence" % interview_type
        if door is None:
            findings.append({"probe": probe, "sent": c19, "expected": VENUE_DOOR_READBACK_SENTENCE,
                             "said": "the read-back carries no line (%s) saying what the payee door will do with a venue's contract" % VENUE_DOOR_READBACK_QUESTION_ID})
        elif str(door.get("spoken")) != VENUE_DOOR_READBACK_SENTENCE:
            findings.append({"probe": probe, "sent": c19, "expected": VENUE_DOOR_READBACK_SENTENCE, "said": "the read-back's door line says %r" % door.get("spoken")})
    return findings


def readback_provenance_note(interview_type: str, answers: Sequence[Tuple[str, Dict[str, Any], str, str]], lines: Sequence[Dict[str, Any]]) -> str:
    """
    Spec T12 §0: how many read-back lines this run answered and how many the book supplied, counted over the lines the
    estate speaks (the synthetic lines set aside). On a resumed interview the read-back carries the answers earlier runs
    gave, so the two counts show how much of the law being read back this run wrote and how much stood before it.
    """
    book = A.ANSWERS.get(interview_type, {})
    run_ids = {q for q, _, _, _ in answers}
    line_ids = [str(l.get("questionId")) for l in lines if not l.get("synthetic")]
    from_run = sum(1 for qid in line_ids if qid in run_ids)
    from_book = sum(1 for qid in line_ids if qid not in run_ids and qid in book)
    return "the %s read-back was checked against the book: %d line(s), %d this run answered and %d from the book" % (
        interview_type, from_run + from_book, from_run, from_book)


def audit_charter(interview_type: str, charter: Dict[str, Any], answers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The compiled charter compared with the answers the read-back reflects: the figures, the rosters, the networks."""
    findings: List[Dict[str, Any]] = []

    def expect(probe: str, expected: Any, got: Any, sent: Any = None) -> None:
        if expected != got:
            findings.append({"probe": "charter (%s): %s" % (interview_type, probe), "sent": sent, "expected": json.dumps(expected, ensure_ascii=False),
                             "said": "the charter carries %s" % json.dumps(got, ensure_ascii=False)})

    choice = lambda qid: (answers.get(qid) or {}).get("choice")  # noqa: E731
    choices = lambda qid: list((answers.get(qid) or {}).get("choices") or [])  # noqa: E731
    text = lambda qid: str((answers.get(qid) or {}).get("text") or "").strip()  # noqa: E731
    entries = lambda qid: list((answers.get(qid) or {}).get("entries") or [])  # noqa: E731
    people = lambda qid: list((answers.get(qid) or {}).get("people") or [])  # noqa: E731
    cents = lambda qid: (answers.get(qid) or {}).get("cents") if qid in answers else None  # noqa: E731
    amounts = charter.get("amountsUsdCents") or {}
    if interview_type == "policy":
        expect("the name (A1)", text("A1"), charter.get("name"), text("A1"))
        expect("the release quorum (C10)", int(choice("C10")) if choice("C10") else None, charter.get("quorum"), choice("C10"))
        expect("the signers (C11)", people("C11"), charter.get("signers"), people("C11"))
        census = ["%s <%s>" % (e.get("name", "").strip(), e.get("email", "").strip()) if e.get("name", "").strip() else e.get("email", "").strip()
                  for e in entries("A8") if e.get("email", "").strip()]
        expect("the change approvers (A8's census)", census, charter.get("changeApprovers"), entries("A8"))
        recorded = sorted({"aeredium"} | {c.lower() for c in choices("C9")})
        expect("the networks recorded (C9 plus Aeredium)", recorded, sorted(charter.get("recordedChains") or []), choices("C9"))
        expect("the preparer may release (C15)", None if choice("C15") is None else choice("C15") == "Yes", charter.get("requesterCountsAsSigner"), choice("C15"))
        expect("the destination rule (version 12 asks none)", None, charter.get("whitelistMode"))
        contact = next(({"name": e.get("name", "").strip(), "email": e.get("email", "").strip()} for e in entries("C18") if e.get("email", "").strip()), None)
        if contact:
            said = json.dumps(charter.get("securityContact"), ensure_ascii=False)
            if contact["email"] not in said:
                findings.append({"probe": "charter (policy): the security contact (C18)", "sent": contact, "expected": contact["email"], "said": "the charter carries %s" % said})
        if choice("C12"):
            governance = json.dumps(charter.get("mutationGovernance") or charter.get("changeQuorum") or charter.get("governance"), ensure_ascii=False)
            if choice("C12") not in governance:
                findings.append({"probe": "charter (policy): the change quorum (C12)", "sent": choice("C12"), "expected": "a change quorum of %s" % choice("C12"),
                                 "said": "the charter's governance carries %s" % governance})
        # Spec T11 — who approves a new payee (C11A), as onboardingcompiler.ts payeeApprovalOf reads the answer: the first answer is
        # C11's people at C10's count; the second the census (else C11's people) at C12's, or C12D's behind a Yes on C12A; the third
        # C11C's one person at one. The charter's record carries answer, roster ("Name <email>") and quorum, and S10 compares the three.
        c11a = choice("C11A")
        if c11a is not None:
            if c11a == A.PAYEE_APPROVAL_PAYMENT_APPROVERS:
                want: Any = {"answer": "payment_approvers", "roster": people("C11"), "quorum": int(choice("C10")) if choice("C10") else None}
            elif c11a == A.PAYEE_APPROVAL_CHANGE_APPROVERS:
                c12d = choice("C12D") if choice("C12A") == "Yes" else None
                count = c12d or choice("C12")
                want = {"answer": "change_approvers", "roster": census if census else people("C11"), "quorum": int(count) if count else None}
            else:
                cfo = next((e for e in entries("C11C") if str(e.get("email", "")).strip()), None)
                label = ("%s <%s>" % (cfo.get("name", "").strip(), cfo.get("email", "").strip()) if cfo.get("name", "").strip() else cfo.get("email", "").strip()) if cfo else None
                want = {"answer": "cfo", "roster": [label] if label else [], "quorum": 1}
            got = charter.get("payeeApproval")
            expect("who approves a new payee (C11A: the answer, its roster and its quorum)", want,
                   {k: got.get(k) for k in ("answer", "roster", "quorum")} if isinstance(got, dict) else got, c11a)
        # Spec T11 — may a payee be a venue's contract (C19): No compiles 'refused', Yes 'accepted' (venueContractsOf)
        c19 = choice("C19")
        if c19 is not None:
            expect("may a payee be a venue's contract (C19)", "refused" if c19 == A.VENUE_NO else "accepted", charter.get("payeeVenueContracts"), c19)
    else:
        expect("the name (WN)", text("WN"), charter.get("name"), text("WN"))
        expect("the purpose (W1)", choice("W1"), charter.get("purpose"), choice("W1"))
        expect("the release quorum (WQ)", int(choice("WQ")) if choice("WQ") else None, charter.get("quorum"), choice("WQ"))
        signers = ["%s <%s>" % (e.get("name", "").strip(), e.get("email", "").strip()) if e.get("name", "").strip() else e.get("email", "").strip()
                   for e in entries("WA1") if e.get("email", "").strip()]
        # Spec T11 — WO2's third party is a signer beside WA1's people, once by email (onboardingcompiler.ts: "a person named at both
        # WA1 and WO2 holds one seat, not two"), spoken as full name and surname (personLabel)
        third = next((e for e in entries("WO2") if str(e.get("email", "")).strip()), None)
        if third is not None:
            third_email = str(third.get("email")).strip()
            if not any(str(e.get("email", "")).strip().lower() == third_email.lower() for e in entries("WA1")):
                label = " ".join(part for part in (str(third.get("name", "")).strip(), str(third.get("surname", "")).strip()) if part)
                signers.append("%s <%s>" % (label, third_email) if label else third_email)
        expect("the signers (WA1, and WO2's third party once)" if third is not None else "the signers (WA1)", signers, charter.get("signers"),
               {"WA1": entries("WA1"), "WO2": entries("WO2")} if third is not None else entries("WA1"))
        purpose = choice("W1") or ""
        # Spec T11 — the wallet's people and tiers (WO1, WO3, WO4), as the compiler records them (readWalletPeople): the holder by
        # person with the title W1 decides (holderTitleFor: the Principal of a customer's account, the Officer of every other
        # wallet), or by no one; and the two figures, WO3 null for a wallet held by no one because it is not asked
        wo1 = answers.get("WO1")
        if isinstance(wo1, dict):
            if wo1.get("choice") == A.HOLDER_PERSON:
                person = wo1.get("person") or {}
                holder: Any = {"held": "by_person", "name": str(person.get("name", "")).strip(), "email": str(person.get("email", "")).strip(),
                               "title": "Principal" if purpose == A.CUSTOMER else "Officer"}
            else:
                holder = {"held": "by_no_one"}
            expect("who holds this wallet (WO1)", holder, charter.get("holder"), wo1)
        if "WO4" in answers:
            tiers = charter.get("signingTiers") if isinstance(charter.get("signingTiers"), dict) else {}
            expect("the holder's own figure (WO3)", cents("WO3"), tiers.get("holderAloneUpToCents"), cents("WO3"))
            expect("the two-signature figure (WO4)", cents("WO4"), tiers.get("twoSignaturesUpToCents"), cents("WO4"))
        if purpose.startswith("Operations") or purpose.startswith("Something else"):
            expect("the per-payment hold (O2)", cents("O2"), amounts.get("holdOverPerTx"), cents("O2"))
            expect("the daily figure (O1)", cents("O1"), amounts.get("dailyTotal"), cents("O1"))
            modes = {"Yes": "hold_non_listed", "List only": "allow_only", "Anyone, freely": "none"}
            expect("the destination rule (O3)", modes.get(choice("O3") or "", None), charter.get("whitelistMode"), choice("O3"))
            expect("no deny ceiling in the operations dialect", None, amounts.get("denyCeiling"))
        if purpose.startswith("Treasury"):
            expect("the treasury ceiling (T1)", cents("T1"), amounts.get("denyCeiling"), cents("T1"))
        expect("the submitter may approve (WA2)", A.WA2_YES == choice("WA2") if choice("WA2") in (A.WA2_YES, A.WA2_NO) else None,
               charter.get("requesterCountsAsSigner"), choice("WA2"))
        recorded = sorted({"aeredium"} | {c.lower() for c in choices("X1")})
        if "X1" in answers:
            expect("the networks recorded (X1 plus Aeredium)", recorded, sorted(charter.get("recordedChains") or []), choices("X1"))
    if charter.get("realm") == "sandbox":
        allowed = [str(c).lower() for c in charter.get("allowedChains") or []]
        live = {c.lower() for c in choices("C9" if interview_type == "policy" else "X1")}
        crossed = sorted(live & set(allowed))
        if crossed:
            findings.append({"probe": "charter (%s): a sandbox charter naming a live network" % interview_type, "sent": sorted(live), "expected": "allowedChains without %s" % crossed,
                             "said": "allowedChains %s" % allowed})
    return findings


def audit_journey(journey: Dict[str, Any], registers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The journey's stage compared with what the registers hold."""
    findings: List[Dict[str, Any]] = []
    stages = {str(s.get("id")): s for s in journey.get("stages") or []}
    done = lambda sid: bool((stages.get(sid) or {}).get("done"))  # noqa: E731

    def mismatch(probe: str, expected: str, said: str) -> None:
        findings.append({"probe": "journey: %s" % probe, "sent": None, "expected": expected, "said": said})

    stands = registers.get("charter_stands_written")
    if stands is not None and stands != done("policy_interview"):
        mismatch("stage 1 against the charter's standing", "stage 1 done exactly when GET /v1/onboarding/charter stands written (%s)" % stands,
                 "stage 1 done %s" % done("policy_interview"))
    if registers.get("account_compiled") and not done("first_wallet_account"):
        mismatch("stage 2 against the wallet account interview", "stage 2 done: the wallet account's charter compiled in this run", "stage 2 done False")
    payees, sets = registers.get("payees"), registers.get("sets")
    if payees is not None and sets is not None:
        worked = payees > 0 and sets > 0
        if worked != done("working_the_sandbox"):
            mismatch("stage 3 against the payees and runs registers", "stage 3 done exactly when a payee and a run exist (%d payee(s), %d run(s))" % (payees, sets),
                     "stage 3 done %s" % done("working_the_sandbox"))
    flags = [done(sid) for sid in JOURNEY_STAGE_IDS]
    last = max([i + 1 for i, f in enumerate(flags) if f] or [0])
    expected_current = min(JOURNEY_STAGE_COUNT, last + 1)
    current = journey.get("currentStage")
    if current is not None and current != expected_current:
        mismatch("the current stage against the stages done", "currentStage %d (one past the last stage done)" % expected_current, "currentStage %s with done %s" % (current, flags))
    if journey.get("stageCount") != JOURNEY_STAGE_COUNT:
        mismatch("the stage count", "stageCount %d" % JOURNEY_STAGE_COUNT, "stageCount %s" % journey.get("stageCount"))
    return findings


MONEY_KEY = re.compile(r"(Minor|Cents|cents|amountMinor|Bps)$")
INTEGER_TEXT = re.compile(r"^-?\d+$")


def audit_money(calls: Sequence[Call]) -> List[Dict[str, Any]]:
    """
    Every money figure the server returned, checked against the minor-unit law (money.ts): an integer of minor units, never a float. A string
    of digits, as every road of the estate spoke it until Spec 104; or a JSON integer, as Spec 104's gas roads speak cents (routes/gas.ts,
    availableUsdCents) — exact either way, so neither is a finding (Spec T14). A float, or a string that is not an integer, is.
    """
    findings: List[Dict[str, Any]] = []
    seen: set = set()

    def walk(value: Any, path: str, call: Call) -> None:
        if isinstance(value, dict):
            for key, inner in value.items():
                here = "%s.%s" % (path, key) if path else str(key)
                scalar = not isinstance(inner, (dict, list))
                if scalar and MONEY_KEY.search(str(key)) and str(key) not in ("baseDecimals", "assetDecimals", "currencyDecimals"):
                    if inner is not None and not ((isinstance(inner, str) and INTEGER_TEXT.match(inner)) or (isinstance(inner, int) and not isinstance(inner, bool))):
                        mark = ("law", call.route, here)
                        if mark not in seen:
                            seen.add(mark)
                            findings.append({"probe": "minor-unit law at %s (%s)" % (here, call.route), "sent": None,
                                             "expected": "an integer of minor units, as a string or a JSON integer", "said": "the server returned %r (%s)" % (inner, type(inner).__name__)})
                if isinstance(inner, float):
                    mark = ("float", call.route, here)
                    if mark not in seen:
                        seen.add(mark)
                        findings.append({"probe": "a float at %s (%s)" % (here, call.route), "sent": None, "expected": "no float anywhere downstream of money.ts",
                                         "said": "the server returned the float %r" % inner})
                walk(inner, here, call)
        elif isinstance(value, list):
            for index, inner in enumerate(value):
                walk(inner, "%s[%d]" % (path, index), call)

    for call in calls:
        if call.outside:
            continue  # Spec T13: the chain's RPC and the faucet answer in their own shapes; the minor-unit law is the estate's
        try:
            body = json.loads(call.text) if call.text.strip() else None
        except ValueError:
            continue
        walk(body, "", call)
    return findings


def refusal_without_why(status: int, text: str) -> Optional[str]:
    """Rule 13: a refusal names what happened and who refused. Returns the fault, or None for a refusal that says why."""
    if status < 400:
        return None
    try:
        body = json.loads(text) if text.strip() else None
    except ValueError:
        body = None
    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return "no refusal body: HTTP %d with %r" % (status, text[:120])
    code = error.get("code")
    message = str(error.get("message") or "").strip()
    if not code or not message:
        return "a refusal with no code or no sentence: %s" % json.dumps(error)[:200]
    if code == "INTERNAL_ERROR":
        return "INTERNAL_ERROR: the sentence this house says when it has no words"
    lowered = message.lower()
    for phrase in GENERIC_REFUSAL_PHRASES:
        if phrase in lowered:
            return "a generic sentence (%r) on a %d" % (phrase, status)
    return None


def audit_refusals(calls: Sequence[Call]) -> List[Dict[str, Any]]:
    """Every refusal met in S1 to S9, checked for Rule 13. S10 and S11 judge their own refusals."""
    findings: List[Dict[str, Any]] = []
    for call in calls:
        if call.station in ("S10", "S11") or call.status < 400 or call.outside:
            continue  # an outside call (Spec T13: the RPC, the faucet) is reported verbatim where it was made, never judged as the estate's
        why = refusal_without_why(call.status, call.text)
        if why:
            findings.append({"probe": "Rule 13 at %s (%s)" % (call.route, call.station), "sent": call.sent, "expected": "a refusal that names what happened and who refused",
                             "said": "%s — %s" % (why, call.text[:300])})
    return findings


def audit_people(register: Optional[Dict[str, Any]], minted: Sequence[Dict[str, Any]], credentials: Dict[str, Optional[str]],
                 founder_key: str = A.FOUNDER, retired: Sequence[Dict[str, Any]] = ()) -> List[Dict[str, Any]]:
    """
    The People register compared with the invitations sent, and the credentials the sessions carry.

    Spec T10 §3: the audit also asserts, after S4, that the sessions carry distinct credential ids and none but the founder's
    is the founder's, and says so when they do — an entry with `note` is a fact for S10 to report, not a finding, so the
    closing table can say the finding closed. And it reads the register's Spec 91 marker, `sharesCredentialWith` (spoken on
    the People screen as "shares a credential with …; invite them again to give them their own"), for each of the harness's
    people: expected absent after the re-invitation, and a finding where it stands. The founder's row is the one marker the
    harness expects: the passkeys it retired (`retired`, each with its label and the credential it enrolled) still speak for
    the founder's credential at the estate, which does nothing to them by itself (Spec 91, item 4), so a marker naming exactly
    those labels is reported and not a finding — any other name on it is.
    """
    findings: List[Dict[str, Any]] = []
    if register is None:
        return findings
    all_rows = [r for r in register.get("invites") or [] if isinstance(r, dict)]
    rows = {str(r.get("id")): r for r in all_rows}
    for m in minted:
        invite = m["invite"]
        row = rows.get(str(invite.get("id")))
        probe = "people register: the invitation of %s" % A.PEOPLE[m["person"]].name
        if row is None:
            findings.append({"probe": probe, "sent": invite, "expected": "a row in the register", "said": "the register has no row for invitation %s" % invite.get("id")})
            continue
        for field in ("displayName", "email", "role"):
            if str(row.get(field)) != str(invite.get(field)):
                findings.append({"probe": probe + " (%s)" % field, "sent": invite.get(field), "expected": str(invite.get(field)), "said": "the register says %r" % row.get(field)})
        if credentials.get(m["person"]) and row.get("state") != "redeemed":
            findings.append({"probe": probe + " (state)", "sent": invite, "expected": "redeemed: the person signed in with the passkey this invitation enrolled",
                             "said": "the register says %r" % row.get("state")})
    held = {k: v for k, v in credentials.items() if v}
    distinct = set(held.values())
    founder_credential = held.get(founder_key)
    if len(held) > 1 and len(distinct) < len(held):
        by_credential: Dict[str, List[str]] = {}
        for k, v in held.items():
            by_credential.setdefault(str(v), []).append(A.PEOPLE[k].name)
        shared = {last4(c): names for c, names in by_credential.items() if len(names) > 1}
        said = "the sessions carry %d distinct credential id(s) for %d people: %s" % (len(distinct), len(held), json.dumps(shared, ensure_ascii=False))
        if founder_credential and len(by_credential.get(str(founder_credential), [])) > 1:
            said += "; %s is the founder's credential" % last4(founder_credential)
        findings.append({"probe": "people register: one credential for several people", "sent": None,
                         "expected": "one credential id per person, so the register and every approval can tell them apart",
                         "said": said})
    elif held:
        each = ", ".join("%s %s" % (A.PEOPLE[k].name, last4(v)) for k, v in held.items())
        if founder_credential is None:
            said = "the %d session(s) carry %d distinct credential id(s) (%s); the founder has no session, so whether any is the founder's was not checked" % (len(held), len(distinct), each)
        else:
            said = "the %d session(s) carry %d distinct credential id(s), and only the founder's own is the founder's %s: %s" % (len(held), len(distinct), last4(founder_credential), each)
        findings.append({"note": True, "probe": "people register: one credential per person", "said": said})
    # The register's Spec 91 marker, for each of the harness's people.
    with_field = [r for r in all_rows if "sharesCredentialWith" in r]
    if all_rows and not with_field:
        findings.append({"note": True, "probe": "people register: the Spec 91 marker",
                         "said": "the register's rows carry no sharesCredentialWith (Spec 91's marker), so it was not read: an estate before Spec 91"})
        return findings
    by_email = {A.PEOPLE[k].email.lower(): k for k in A.PEOPLE}

    def person_of(row: Dict[str, Any]) -> Optional[str]:
        email = str(row.get("email") or "").strip().lower()
        if email:
            return by_email.get(email)
        if founder_credential and str(row.get("credentialId")) == str(founder_credential):
            return founder_key
        return None

    retired_on_founders = sorted({str(r.get("label")) for r in retired if founder_credential and str(r.get("aap_credential_id")) == str(founder_credential)})
    marked: List[str] = []
    read: List[str] = []
    for row in with_field:
        who = person_of(row)
        if who is not None and row.get("state") == "redeemed" and who not in read:
            read.append(who)
        names = row.get("sharesCredentialWith")
        if not isinstance(names, list) or not names:
            continue
        spoken = shares_credential_sentence(names)
        register_says = 'the register says sharesCredentialWith %s; on the People screen: "%s"' % (json.dumps(names, ensure_ascii=False), spoken)
        if who == founder_key:
            if retired_on_founders and sorted(str(n) for n in names) == retired_on_founders:
                marked.append(who)
                findings.append({"note": True, "probe": "people register: the Spec 91 marker on the founder's row",
                                 "said": "the founder's row (%s) carries the marker for the %d passkey(s) the harness retired, which still speak for the founder's credential %s at the estate: %s" % (
                                     row.get("displayName"), len(names), last4(founder_credential), register_says)})
            else:
                marked.append(who)
                findings.append({"probe": "people register: the Spec 91 marker on the founder's row", "sent": None,
                                 "expected": "no marker, or one naming only the passkeys the harness retired (%s)" % (", ".join(retired_on_founders) or "none"),
                                 "said": register_says})
        elif who is not None:
            marked.append(who)
            findings.append({"probe": "people register: the Spec 91 marker on %s's row" % A.PEOPLE[who].name, "sent": None,
                             "expected": "no marker after the re-invitation: a credential of %s's own" % A.PEOPLE[who].name, "said": register_says})
        else:
            findings.append({"note": True, "probe": "people register: the Spec 91 marker on a row that is not the harness's",
                             "said": "the register marks %s (%s): %s" % (row.get("displayName"), row.get("email"), register_says)})
    unmarked = [A.PEOPLE[k].name for k in A.PEOPLE if k in read and k not in marked]
    if unmarked:
        findings.append({"note": True, "probe": "people register: the Spec 91 marker absent",
                         "said": "the People register marks none of %s as sharing a credential (Spec 91's marker absent on their rows)" % ", ".join(unmarked)})
    return findings


def audit_payees(register: Optional[Dict[str, Any]], created: Sequence[Dict[str, Any]], account_charter: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The payees register compared with the whitelist the charter enforces and with what the harness had approved."""
    findings: List[Dict[str, Any]] = []
    if register is None:
        return findings
    statuses: Dict[str, Tuple[str, str]] = {}
    for row in register.get("payees") or []:
        for addr in row.get("addresses") or []:
            statuses[str(addr.get("address", "")).lower()] = (str(addr.get("whitelistStatus")), str(row.get("displayName")))
    for record in created:
        approved = record.get("approved")
        if isinstance(approved, dict) and approved.get("whitelistStatus") == "whitelisted":
            status = statuses.get(record["address"].lower())
            if status is None or status[0] != "whitelisted":
                findings.append({"probe": "payees register: %s" % record["name"], "sent": record["address"], "expected": "whitelisted, as Ada's approval answered",
                                 "said": "the register says %s" % (status[0] if status else "the address is absent")})
    if account_charter:
        for entry in account_charter.get("whitelistEntries") or []:
            address = str(entry.get("address", "")).lower()
            if address and address not in statuses:
                findings.append({"probe": "payees register against the charter's list", "sent": entry, "expected": "the charter's entry in the register",
                                 "said": "the charter lists %s (%s) and the register does not carry it" % (entry.get("address"), entry.get("label"))})
    return findings


def optimizer_measures(calls: Sequence[Call], served_twice: Dict[str, List[str]]) -> Dict[str, Any]:
    """S12: wall times, the slow, the ten slowest, the interviews' call counts, the largest answer, the 5xx retried."""
    slow = [c for c in calls if c.elapsed_ms > SLOW_CALL_SECONDS * 1000]
    slowest = sorted(calls, key=lambda c: c.elapsed_ms, reverse=True)[:10]
    largest = max(calls, key=lambda c: c.size) if calls else None
    retried = [c for c in calls if c.retry_of is not None]
    interview_calls = [c for c in calls if c.station in ("S3", "S5") and "/v1/onboarding/" in c.path]
    reads: Dict[str, int] = {}
    for c in interview_calls:
        if c.method == "GET":
            reads[c.route] = reads.get(c.route, 0) + 1
    duplicate_reads = sum(n - 1 for n in reads.values() if n > 1)
    twice = sum(len(v) for v in served_twice.values())
    wasted = duplicate_reads + twice
    lines = [
        "%d call(s) in all; %d over %.0f seconds" % (len(calls), len(slow), SLOW_CALL_SECONDS),
        "the ten slowest: " + (", ".join("%s %d ms (%s)" % (c.route, c.elapsed_ms, c.station) for c in slowest) or "none"),
        "the interviews (S3 and S5) took %d call(s); %d read(s) a browser would not make (%d read-back or page fetched twice, %d question(s) served twice: %s)" % (
            len(interview_calls), wasted, duplicate_reads, twice, json.dumps(served_twice)),
        "the largest answer: %s" % ("%s, %d bytes (%s)" % (largest.route, largest.size, largest.station) if largest else "none"),
        "5xx answers retried once after %.0f seconds: %s" % (RETRY_AFTER_5XX_SECONDS, ", ".join("%s (%d then %d)" % (c.route, c.retry_of.status, c.status) for c in retried) or "none"),
    ]
    slow_invitations = [c for c in slow if c.route == "POST /v1/invites"]
    if slow:
        lines.append("every call over %.0f seconds, reported and not judged: %s" % (
            SLOW_CALL_SECONDS, ", ".join("%s %d ms (%s)" % (c.route, c.elapsed_ms, c.station) for c in slow)))
    if slow_invitations:
        # Spec T8: a fact to report, not a finding. routes/invites.ts mints the invitation, awaits the email's
        # dispatch, stamps the row, and only then answers 201; a future estate spec may move the send off the road.
        lines.append("%s — %s (routes/invites.ts: the invitation is minted, the email's dispatch is awaited, the row is stamped, and only then does the route answer 201)" % (
            INVITATION_SENDS_FIRST, ", ".join("%d ms (%s)" % (c.elapsed_ms, c.station) for c in slow_invitations)))
    return {"calls": len(calls), "slow": slow, "slowest": slowest, "largest": {"route": largest.route, "size": largest.size} if largest else None,
            "retried": retried, "interview_calls": len(interview_calls), "wasted_reads": wasted, "slow_invitations": slow_invitations, "lines": lines}


# ---------------------------------------------------------------------------
# The last run (Spec T8): the previous report in the working folder, read back, so a rerun after a fix
# says each finding's fate — closed, still open, new. The Python confirms what was fixed.
# ---------------------------------------------------------------------------
UUID_TEXT = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
PATH_ID_TEXT = re.compile(r"/[a-z]+-[0-9a-f]{6,}(?=/|\b)")
REPORT_TITLE = "# AER 360 estate harness run — "
FINDING_LINE = re.compile(r"^- \*\*(.+?)\*\* — (.*)$")
STATION_HEADING = re.compile(r"^## (S\d+) — ")


def finding_key(probe: str) -> str:
    """A finding's identity across runs: its probe with the ids a run mints (uuids; the double's `addr-…`) set aside."""
    return PATH_ID_TEXT.sub("/<id>", UUID_TEXT.sub("<id>", probe))


def _table_cells(line: str) -> List[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", inner)]


def read_report(path: str) -> Dict[str, Any]:
    """
    A report this harness wrote, read back: when the run started, each station's outcome from the closing table
    (three columns, Spec T7, or four with the last-run column), and every finding under its station heading.
    """
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    started_at: Optional[str] = None
    outcomes: Dict[str, str] = {}
    findings: List[Dict[str, Any]] = []
    header: Optional[List[str]] = None
    in_table = False
    station: Optional[str] = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if started_at is None and line.startswith(REPORT_TITLE):
            started_at = line.rsplit(" — ", 1)[-1].strip()
        if line.startswith("| Station |"):
            header = _table_cells(line)
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
            elif not line.startswith("|---"):
                cells = _table_cells(line)
                outcome_at = header.index("Outcome") if header and "Outcome" in header else 1
                if len(cells) > outcome_at:
                    outcomes[cells[0].split(" ", 1)[0]] = cells[outcome_at]
            continue
        heading = STATION_HEADING.match(line)
        if heading:
            station = heading.group(1)
            continue
        if line.startswith("## "):
            station = None
            continue
        found = FINDING_LINE.match(line)
        if found and station:
            findings.append({"station": station, "probe": found.group(1), "said": found.group(2)})
    return {"path": path, "name": os.path.basename(path), "started_at": started_at, "outcomes": outcomes, "findings": findings}


def find_last_report(out_dir: str, own_started_at: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    The newest report in the working folder, read; None when there is none. The bare-dated name is the first
    report of its day and the -HHMMSS names come after it; a report of this very run is never its own last run.
    """
    try:
        names = os.listdir(out_dir)
    except OSError:
        return None
    dated: List[Tuple[Tuple[str, str], str]] = []
    for name in names:
        match = REPORT_NAME.match(name)
        if match:
            dated.append(((match.group(1), match.group(2) or "000000"), name))
    for _, name in sorted(dated, reverse=True):
        try:
            report = read_report(os.path.join(out_dir, name))
        except (OSError, UnicodeDecodeError):
            continue
        if own_started_at and report["started_at"] == own_started_at:
            continue
        return report
    return None


def compare_findings(previous: Sequence[Dict[str, Any]], current: Sequence[Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Each finding's fate between two runs, matched by station and probe (finding_key): closed — the last run
    raised it and this one did not; still open — both did; new — only this run did. In order of appearance.
    """
    def keyed(items: Sequence[Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
        out: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for f in items:
            station = f.station if isinstance(f, Finding) else str(f["station"])
            probe = f.probe if isinstance(f, Finding) else str(f["probe"])
            out.setdefault((station, finding_key(probe)), {"station": station, "probe": probe})
        return out
    before, now = keyed(previous), keyed(current)
    return {"closed": [before[k] for k in before if k not in now],
            "still_open": [now[k] for k in now if k in before],
            "new": [now[k] for k in now if k not in before]}


# ---------------------------------------------------------------------------
# The dry run (Spec T7, Options): every call of the twelve stations, in order, with no network.
# ---------------------------------------------------------------------------
def _j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def dry_lines(base: str = DEFAULT_BASE, start_at: Optional[str] = None, with_invite: bool = True) -> List[str]:
    origin = base.rstrip("/")
    lines: List[str] = []

    def line(station: str, text: str) -> None:
        lines.append("%s — %s" % (station, text))

    founder = A.PEOPLE[A.FOUNDER]
    # S1
    if with_invite:
        line("S1", "POST /v1/auth/invite/options %s → expect 200: options (rp.id, challenge, user.id, pubKeyCredParams with ES256), issuedAtMs, displayName" % _j({"token": "<token from --invite>", "issuedAtMs": "<now>", "response": {}}))
        line("S1", "[passkey] a new P-256 key for %s (openssl ecparam -genkey -name prime256v1), attestation none, flags UP|UV|AT, COSE ES256" % founder.name)
        line("S1", "POST /v1/auth/invite/verify %s → expect 200: a session in %s (Set-Cookie %s, csrfToken, roles author and viewer); the key stored at ~/.aer360-harness/%s/%s.json mode 0600" % (
            _j({"token": "<token>", "issuedAtMs": "<issuedAtMs from options>", "response": "<RegistrationResponseJSON>"}), A.ESTATE["company"], SESSION_COOKIE, A.ESTATE["client_id"], founder.key))
    else:
        line("S1", "POST /v1/auth/login/options {} → expect 200: options (challenge, rpId), issuedAtMs, nonce")
        line("S1", "POST /v1/auth/login/verify %s → expect 200: a session in %s" % (_j({"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<AuthenticationResponseJSON over authenticatorData ‖ SHA-256(clientDataJSON)>"}), A.ESTATE["company"]))
    # S2
    line("S2", "GET /v1/journey → expect currentStage 1 of %d, the current stage policy_interview" % JOURNEY_STAGE_COUNT)
    # S3
    line("S3", "POST /v1/onboarding/interviews %s → expect 200: the interview id and its first page; the answer book answers catalog version %d, and %s" % (
        _j({"interviewType": "policy"}), A.CATALOG_VERSION_ANSWERED, ESTATE_STATES_NO_CATALOG_VERSION))
    for q in A.expected_walk("policy"):
        line("S3", "POST /v1/onboarding/interviews/<policy interview>/answers %s → expect 200: the next page (%s)" % (_j({"questionId": q.id, "value": A.POLICY_ANSWERS[q.id]}), q.kind))
    line("S3", "GET /v1/onboarding/interviews/<policy interview>/readback → expect the charter in plain sentences, the sandbox realm first")
    line("S3", "POST /v1/onboarding/interviews/<policy interview>/confirm/options {} → expect the digest-bound challenge, issuedAtMs, digest")
    line("S3", "POST /v1/onboarding/interviews/<policy interview>/confirm %s → expect 200: state confirmed" % _j({"issuedAtMs": "<issuedAtMs>", "response": "<assertion by the founder's passkey over the challenge>"}))
    line("S3", "POST /v1/onboarding/interviews/<policy interview>/compile {} → expect 200: charter (name, quorum 1, signers, recordedChains, allowedChains aeredium-testnet), receipt, seat")
    line("S3", "GET /v1/onboarding/charter → expect standsWritten true")
    line("S3", "GET /v1/journey → expect currentStage 2 of %d" % JOURNEY_STAGE_COUNT)
    # S4 — Spec T10: every person is brought in on their own credential
    approver = A.PEOPLE[A.PAYMENT_APPROVER]
    line("S4", "GET /v1/approver-seats (as %s) → expect the charter's seats as this run finds them: which credential %s's seat names before anybody is brought in again" % (founder.name, approver.name))
    for key in A.AUTHORS_INVITED:
        person = A.PEOPLE[key]
        line("S4", "POST /v1/invites %s (as %s, x-csrf-token) → expect 201: url %s/invite#<token>, said once" % (_j({"displayName": person.name, "email": person.email, "role": "author"}), founder.name, origin))
        line("S4", "POST /v1/auth/invite/options %s → expect 200: options for %s" % (_j({"token": "<token from the url>", "issuedAtMs": "<now>", "response": {}}), person.name))
        line("S4", "POST /v1/auth/invite/verify %s → expect 200: a session for %s, roles author and viewer%s" % (
            _j({"token": "<token>", "issuedAtMs": "<issuedAtMs>", "response": "<RegistrationResponseJSON with a new passkey>"}), person.name,
            "; approverSeat on redemption where the charter names them" if key == A.PAYMENT_APPROVER else ""))
        line("S4", "[compare] %s's session credentialId with the founder's (where a passkey is stored for %s: POST /v1/auth/login/options {} and /verify first) → expect a credential of %s's own, not the founder's; equal is the shared credential of S10's finding, and %s is brought in again" % (
            person.name, person.name, person.name, person.name))
        line("S4", "POST /v1/invites %s (as %s, x-csrf-token) — only if %s's session carries the founder's credential → expect 201: a fresh invitation for the same name and email, minting a credential of %s's own (Spec 91)" % (
            _j({"displayName": person.name, "email": person.email, "role": "author"}), founder.name, person.name, person.name))
        line("S4", "POST /v1/auth/invite/options %s — only if %s is brought in again → expect 200: options for %s" % (
            _j({"token": "<token from the fresh url>", "issuedAtMs": "<now>", "response": {}}), person.name, person.name))
        line("S4", "POST /v1/auth/invite/verify %s — only if %s is brought in again → expect 200: a session for %s on a credential of %s's own, not the founder's; the new key stored beside the old at ~/.aer360-harness/%s/%s-2-<date>.json mode 0600, the old one untouched" % (
            _j({"token": "<token>", "issuedAtMs": "<issuedAtMs>", "response": "<RegistrationResponseJSON with a NEW passkey>"}), person.name, person.name, person.name, A.ESTATE["client_id"], person.key))
    line("S4", "GET /v1/approver-seats (as %s) → expect the charter's seats after the people were brought in; %s seated or enrolled_not_seated, and which credential the seat names" % (founder.name, approver.name))
    line("S4", "POST /v1/approver-seats/grant %s (as %s) — only if the seat is enrolled_not_seated or names a credential other than %s's session's → expect the seat seated, naming %s's own credential (Spec 91); a refusal is a finding in the estate's words" % (
        _j({"email": approver.email}), founder.name, approver.name, approver.name))
    # Spec T17 §1 and §2 (in substance T15 §1 with a grant step): S4 reads the roster changes and the seats with onRoster (AER 360
    # Specs 99 and 105), grants each stale seat of a harness person one at a time where nothing awaits, and T15's pass signs it.
    line("S4", "GET %s (as %s) → expect every roster change the platform holds for the estate (Spec 99): pendingTxId, state awaiting, approved, applied, expired or closed, whose seat it moves, requiredSignatures, signaturesCollected, signedBy, maySign; a fresh estate lists none, and S4 says so in one line" % (
        T.ROSTER_CHANGES_ROUTE, founder.name))
    line("S4", "GET /v1/approver-seats (as %s) — the grant step's read, with %s (AER 360 Spec 105) → expect each seat's onRoster true, false or null; for a seat of a harness person (matched by email harness+<name>@aeredium.io) reading false with no awaiting change the founder grants it again (below); a seat reading true prints nothing; a null credential or ambiguous seat, a seat of a person not of the harness, and a null seat print their line and are not granted; an estate without %s prints \"the seat view has no onRoster; skipping\" and S4 behaves as T15" % (
        founder.name, T.SEAT_ON_ROSTER, T.SEAT_ON_ROSTER))
    line("S4", "POST /v1/approver-seats/grant %s (as %s) — only for a seat of a harness person reading %s false with no awaiting change → expect Spec 95 to propose the move afresh at the seat grant, one call, listed awaiting and signed below; where the grant's answer carries no pendingTxId the line says \"moved at once\" and the signing is skipped" % (
        _j({"email": approver.email}), founder.name, T.SEAT_ON_ROSTER))
    line("S4", "POST %s {} (as each person the change's list names as able — not the stale seat's owner, and where they have a seat row reading %s true; a person the list names with no seat row is able on the list's word) — only for a change listed awaiting whose target credential is that person's stored passkey → expect 200: options with the challenge the estate derives from %s under the purpose %s, and issuedAtMs; where the able persons are fewer than requiredSignatures S4 fails \"<n> required, <m> able\" and grants no further seat" % (
        T.ROSTER_CHANGE_SIGN_OPTIONS_ROUTE % "<pendingTxId>", T.SEAT_ON_ROSTER, T.ROSTER_CHANGE_BINDING % ("<workspace id>", "<pendingTxId>", "<issuedAtMs>"), T.ROSTER_CHANGE_PURPOSE))
    line("S4", "POST %s %s → expect 200: signaturesCollected of requiredSignatures, state awaiting until the count is met, then applied with rebound naming %s's current credential; a change moving a harness seat to a credential the harness does not hold is the finding \"change <id> moves <who>'s seat to a credential the harness does not hold; not signed\"; a refusal (%s, %s, %s, %s) is judged for Rule 13 and reported in the estate's words, never retried" % (
        T.ROSTER_CHANGE_SIGN_ROUTE % "<pendingTxId>", _j({"issuedAtMs": "<issuedAtMs>", "response": "<assertion by the signer's passkey over the challenge>"}), approver.name,
        CHANGE_SIGNER_NOT_ON_ROSTER, APPROVER_ALREADY_SIGNED, SIGNATURE_NOT_COUNTED, PLATFORM_REFUSED))
    line("S4", "POST /v1/approver-seats/grant %s (as %s) — only for a change listed expired, or one this estate did not propose → expect Spec 95 to propose the move afresh at the seat grant (the estate proposes a move at a seat grant or a redemption, not at a sign-in), the change re-listed awaiting and signed; a second expiry fails S4 naming the ceremony" % (
        _j({"email": approver.email}), founder.name))
    line("S4", "GET %s (as %s) — after the count is met → expect the change applied, its seat naming %s's current credential in short form, as the signature's rebound named it" % (
        T.ROSTER_CHANGES_ROUTE, founder.name, approver.name))
    line("S4", "GET /v1/approver-seats (as %s) — after the count is met, up to three times over a bounded wait → expect %s's seat reading %s true (moved); otherwise S4 fails naming the seat and \"<k> of <n> signatures\"" % (
        founder.name, approver.name, T.SEAT_ON_ROSTER))
    line("S4", "GET /v1/invites (as %s) → expect the register: three authors, redeemed; each row's sharesCredentialWith (Spec 91's marker) read for S10, expected absent after the re-invitation" % founder.name)
    # S5
    line("S5", "POST /v1/onboarding/interviews %s → expect 200: the interview id and its first page" % _j({"interviewType": "wallet_account"}))
    for q in A.expected_walk("wallet_account"):
        line("S5", "POST /v1/onboarding/interviews/<account interview>/answers %s → expect 200: the next page (%s)" % (_j({"questionId": q.id, "value": A.ACCOUNT_ANSWERS[q.id]}), q.kind))
    line("S5", "GET /v1/onboarding/interviews/<account interview>/readback → expect the account's charter in plain sentences")
    line("S5", "POST /v1/onboarding/interviews/<account interview>/confirm/options {} → expect the digest-bound challenge")
    line("S5", "POST /v1/onboarding/interviews/<account interview>/confirm %s → expect 200: state confirmed" % _j({"issuedAtMs": "<issuedAtMs>", "response": "<assertion>"}))
    line("S5", "POST /v1/onboarding/interviews/<account interview>/compile {} → expect 200: charter (%s, holdOverPerTx %s, dailyTotal %s, whitelistMode hold_non_listed), receipt: the account opened on the platform" % (
        A.WALLET_ACCOUNT_NAME, A.MONEY["per_payment_cents"], A.MONEY["per_day_cents"]))
    line("S5", "GET /v1/aer360/wallets → expect the Wallets register with %s, or its absence sentence before the first close" % A.WALLET_ACCOUNT_NAME)
    line("S5", "GET /v1/journey → expect currentStage 3 of %d, working_the_sandbox" % JOURNEY_STAGE_COUNT)
    # S5's tail — Spec T13: the funding wallet (AER 360 Spec 98) and the faucet, as the founder at the Wallets screen and the faucet page
    line("S5", "GET /v1/workspace → expect fundingWallet (address, keyId, homeStack, bornAt, sentence) or fundingWalletAbsence (Spec 98); a wallet already born is reported and not pressed for again")
    line("S5", "POST %s {} — only where fundingWalletAbsence stands → expect 200: options with the challenge the estate derives from %s under the purpose %s, and issuedAtMs" % (
        FUNDING_WALLET_OPTIONS_ROUTE, FUNDING_WALLET_BINDING % ("<workspace id>", "<issuedAtMs>"), FUNDING_WALLET_PURPOSE))
    line("S5", "POST %s %s → expect 200: born true, fundingWallet {address, keyId, homeStack}; %s (the gateway's sentence) or %s (a fault) is reported in the estate's words and S5 fails naming it" % (
        FUNDING_WALLET_ROUTE, _j({"issuedAtMs": "<issuedAtMs>", "response": "<assertion by %s's passkey over the challenge>" % founder.name}), WALLET_BIRTH_REFUSED, GATEWAY_UNAVAILABLE))
    line("S5", "GET /v1/workspace → expect the funding wallet just born, reported as \"funding wallet: <address> on <home stack>, key <id>\"")
    line("S5", "POST %s %s → expect a hex quantity, the wallet's native balance in wei on %s (chain %d, %s); the estate offers a browser no live balance of its funding wallet, so the chain's public RPC named in the faucet record is read; a fault is reported and the faucet is not asked" % (
        T.TESTNET_RPC_URL, _j({"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": ["<funding wallet>", "latest"]}), T.TESTNET_NAME, T.TESTNET_CHAIN_ID, T.NATIVE_COIN))
    line("S5", "POST %s %s — once per run, only where the balance reads below %s %s → expect paid true and tx_hash (%s %s), or the faucet's own refusal sentence, verbatim (its limits: %s)" % (
        T.FAUCET_REQUEST_URL, _j({"address": "<funding wallet>"}), T.GAS_FLOOR_SEAR, T.NATIVE_COIN, T.FAUCET_PAYS_SEAR, T.NATIVE_COIN, T.FAUCET_LIMITS))
    # S6 — Spec T12: since AER 360 Spec 95 the whitelist door admits any active roster signer; the harness presses the roster
    # people it holds a passkey for, in order (the founder last), until the estate answers whitelisted or nobody is left. A press
    # refused SIGNATURE_NOT_COUNTED (its seat bound to a retired credential, Spec 95/99) is recorded and the next person presses.
    quorum = A.WHITELIST_QUORUM
    roster_pressers = [k for k in A.CENSUS_ORDER if k != A.FOUNDER]  # ada, ben, cora; the founder is the last resort
    for payee in T.PAYEES:
        line("S6", "POST /v1/payees %s (as %s) → expect 201: the payee with its address proposed" % (
            _j({"displayName": payee["name"], "defaultAsset": T.PAYMENT_ASSET, "defaultChain": payee["chain"], "addresses": [{"chain": payee["chain"], "address": T.address(payee["key"])}]}), founder.name))
        line("S6", "POST /v1/payees/addresses/<address of %s>/promote {} (as %s) → expect a ceremony: status pending_promotion, platformMembershipId, ceremony" % (payee["name"], founder.name))
        for key in roster_pressers:
            line("S6", "POST /v1/payees/addresses/<address of %s>/approve {} (as %s, the roster in order, the founder last) → expect the estate to count it toward the quorum of %s (approvals, may_still_approve, sentence; Spec 89) — with every seat on its holder's current credential, %s counted (1 of 2) and %s counted (2 of 2), the count met, so %s is not asked (Spec T15 §2); a SIGNATURE_NOT_COUNTED for a person whose seat S4 just moved is a finding, one for a seat S4 could not move is recorded and the next person presses, until whitelisted or nobody is left" % (
                payee["name"], A.PEOPLE[key].name, Runner.COUNT_WORDS.get(quorum, str(quorum)), A.PEOPLE[roster_pressers[0]].name, A.PEOPLE[roster_pressers[1]].name, A.PEOPLE[roster_pressers[2]].name))
    line("S6", "GET /v1/payees → expect both addresses whitelisted, read by this run's payee ids; the judgement is the register's, not the press's — a register reading proposed after the platform counted %s of %s fails with the mirror sentence (Spec T13 §3)" % (quorum, quorum))
    # S7 — Spec T14: the Treasury, the money before, the shortfall paid, S7a, the gas credits, the three payments judged on money that moved, the money after
    clerk = A.PEOPLE[A.PAYMENT_CLERK]
    treasurer = "%s at %s" % (founder.name, T.TREASURY["short"])
    holder_named = (A.ACCOUNT_ANSWERS.get("WO1") or {}).get("choice") == A.HOLDER_PERSON
    tier_alone = (A.ACCOUNT_ANSWERS.get("WO3") or {}).get("cents") if holder_named else None
    tier_two = (A.ACCOUNT_ANSWERS.get("WO4") or {}).get("cents")
    need_dollars = Runner.payments_need()[1]
    line("S7", "GET /v1/workspace (as %s) → expect the funding wallet S5 gave the estate (fundingWallet, with the fund sentence and the chains this deployment pays on, Spec 104 §1) and the platform account it stands on (workspace.aapAccountId)" % clerk.name)
    line("S7", "[file] ~/.aer360-harness/%s → %s and %s, the platform's admin credential Bear files, read once and never printed; absent, S7 fails at the credit step with \"%s\"" % (
        T.ADMIN_ENV_FILE, T.ADMIN_ENV_URL_KEY, T.ADMIN_ENV_KEY_KEY, T.NO_GAS_CREDIT_ROAD_SENTENCE))
    line("S7", "POST /v1/auth/login/options {} and POST /v1/auth/login/verify %s (as %s, with the passkey stored at ~/.aer360-harness/%s/%s.json) → expect a session in %s; with no stored passkey, --treasury-invite: POST /v1/auth/invite/options {\"token\": \"<token from --treasury-invite>\", …} and /verify with a new passkey stored there — the birth run" % (
        _j({"nonce": "<nonce>", "issuedAtMs": "<issuedAtMs>", "response": "<assertion>"}), treasurer, T.TREASURY["client_id"], founder.key, T.TREASURY["company"]))
    line("S7", "GET /v1/onboarding/charter (as %s) → expect standsWritten true on a rerun; on the birth run the policy interview (%d questions, A1 %r and C11 %s the Treasury's own) and the wallet account interview (%d questions, WA1 with %s first) are walked from the book, confirmed under the founder's passkey and compiled" % (
        treasurer, len(A.expected_walk("policy")), T.TREASURY["company"], _j([T.TREASURY["email"]]), len(A.expected_walk("wallet_account")), T.TREASURY["email"]))
    line("S7", "GET /v1/workspace (as %s) → expect the Treasury's funding wallet, or fundingWalletAbsence; absent: POST %s {} and POST %s (a key allocated on the platform and held in the enclave), then S7 stops: \"%s\"" % (
        treasurer, FUNDING_WALLET_OPTIONS_ROUTE, FUNDING_WALLET_ROUTE, T.FUND_TREASURY_SENTENCE % ("<address>", T.PAYEE_CHAIN)))
    line("S7", "GET %s (as %s) → expect Harness Holdings' %s on %s in dollars (balanceMinor, exact) and the %s contract the estate names (token), Spec 104 §1" % (
        T.FUNDING_BALANCES_ROUTE, clerk.name, T.PAYMENT_ASSET, T.PAYEE_CHAIN, T.PAYMENT_ASSET))
    line("S7", "GET %s (as %s) → expect Harness Treasury's %s on %s in dollars" % (T.FUNDING_BALANCES_ROUTE, treasurer, T.PAYMENT_ASSET, T.PAYEE_CHAIN))
    line("S7", "GET %s (as %s) → expect Harness Holdings' gas account, \"%s: US$…\" with availableUsdCents, balanceUsdCents, reservedUsdCents and low, read live from the platform (Spec 104 §3)" % (
        T.GAS_ACCOUNT_ROUTE, clerk.name, T.GAS_ACCOUNT_LABEL))
    line("S7", "GET %s (as %s) → expect Harness Treasury's gas account" % (T.GAS_ACCOUNT_ROUTE, treasurer))
    credit_body = _j({"amount_usd_cents": T.GAS_CREDIT_USD_CENTS, "reason": T.ADMIN_CREDIT_REASON % "<run>", "idempotency_key": "aer360-harness-<run>-%s-gas-<n>" % T.TREASURY["client_id"]})
    line("S7", "POST <%s>%s %s (Authorization: Bearer <%s>, at the platform's admin road) — only where Harness Holdings' %s is below the three payments' %s → expect 201: the line and the balance (Spec 154 §1, audited gas.credited_by_admin); where the Treasury holds less than the shortfall S7 stops instead: \"%s\" and nothing is sent; a refusal in the platform's words fails S7" % (
        T.ADMIN_ENV_URL_KEY, T.ADMIN_CREDIT_ROUTE % "<the Treasury's aapAccountId>", credit_body, T.ADMIN_ENV_KEY_KEY, T.PAYMENT_ASSET, need_dollars,
        T.TREASURY_SHORT_SENTENCE % ("US$<x>", "US$<y>", "<address>", T.PAYEE_CHAIN)))
    treasury_row = {"oneOff": {"chain": T.PAYEE_CHAIN, "address": "<Harness Holdings' funding wallet>", "declared": True, "payeeName": A.ESTATE["company"]},
                    "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": "<the shortfall in minor units>", "invoiceRef": "HT-<run>"}
    line("S7", "POST /v1/sets/review %s (as %s) — only where Holdings is short → expect the gates' review; a %s refusal credits the Treasury more gas once and asks again" % (
        _j({"pays": [treasury_row], "duplicatesAcknowledged": False}), treasurer, T.GAS_SHORTFALL))
    line("S7", "POST /v1/sets %s (as %s) → expect 201: the run in draft" % (
        _j({"pays": [treasury_row], "duplicatesAcknowledged": False, "idempotencyKey": "aer360-harness-<run>-HT", "reference": "Harness payment HT"}), treasurer))
    line("S7", "POST /v1/sets/<run HT>/submit {} → expect status pending_approval, approvalsRequired 1: the shortfall is above the Treasury's %s hold and Holdings' address is new to it" % usd(A.MONEY["per_payment_cents"]))
    line("S7", "POST /v1/approvals/<run HT>/challenge {} then /approve %s (as %s, the charter's one payment approver, with her passkey) → expect status approved, approvalsGiven 1 of 1; refused at the guard once, POST /v1/approver-seats/grant %s and the press again; a second refusal in the estate's words fails S7" % (
        _j({"response": "<assertion over the challenge>"}), treasurer, _j({"email": T.TREASURY["email"]})))
    line("S7", "POST %s {} (as %s) → expect setStatus settled and the instruction confirmed with its txHash: the estate quoted, signed, sponsored and sent through the platform's gas roads and waited for the platform to report the operation %s (Spec 104 §2); a refusal in the estate's words, never retried" % (
        T.SET_EXECUTE_ROUTE % "<run HT>", treasurer, T.PLATFORM_LANDED))
    line("S7", "GET /v1/sets/<run HT> → expect the run as the register shows it, read until its instruction is terminal (up to %d reads over a bounded wait)" % LANDING_READS)
    line("S7", "GET %s?limit=%d (as %s; every page by its nextCursor) → expect the %s row for the run: userOpHash, the handleOps txHash, gasDebitUsdCents and gasDebit" % (
        T.AUDIT_EXPORT_ROUTE, T.AUDIT_EXPORT_LIMIT, treasurer, T.INSTRUCTION_CONFIRMED))
    line("S7", "GET %s (as %s) → expect Harness Holdings' %s risen by the shortfall: the Treasury's payment landed" % (T.FUNDING_BALANCES_ROUTE, clerk.name, T.PAYMENT_ASSET))
    three = []
    for payment in A.PAYMENTS:
        if payment.payee_key is None:
            three.append({"oneOff": {"chain": T.PAYEE_CHAIN, "address": T.address("UNLISTED_ETHEREUM"), "declared": True, "payeeName": payment.payee_name},
                          "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": payment.amount_minor, "invoiceRef": payment.invoice})
        else:
            three.append({"payeeAddressId": "<address of %s>" % payment.payee_name, "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": payment.amount_minor, "invoiceRef": payment.invoice})
    line("S7", "GET /v1/sets (as %s) → the runs register before S7a's review, so a run the review created would be seen" % clerk.name)
    line("S7", "POST /v1/sets/review %s (as %s) — S7a, with Harness Holdings' gas account below the set's ceiling → expect the gas gate (%s) refusing %s in U3's sentence with the figures the harness read: \"Your gas account holds US$<available>. This set needs at most US$<ceiling> of gas. Nothing was sent. Buy gas below.\" (Spec 104 §4); a gate that admits the set because the balance covers the ceiling is reported, not failed; a refusal naming other figures, or a payment that left, fails S7" % (
        _j({"pays": three, "duplicatesAcknowledged": False}), clerk.name, T.GAS_GATE, T.GAS_SHORTFALL))
    line("S7", "GET /v1/sets (as %s) → expect no new run since S7a's review; then GET %s → expect Harness Holdings' %s unchanged: nothing left" % (clerk.name, T.FUNDING_BALANCES_ROUTE, T.PAYMENT_ASSET))
    holdings_credit = _j({"amount_usd_cents": "<%d, or the next ten dollars above twice S7a's ceiling>" % T.GAS_CREDIT_USD_CENTS, "reason": T.ADMIN_CREDIT_REASON % "<run>", "idempotency_key": "aer360-harness-<run>-%s-gas-<n>" % A.ESTATE["client_id"]})
    line("S7", "POST <%s>%s %s (Authorization: Bearer <%s>) → expect 201: Harness Holdings' gas account credited, the balance in the platform's own figures; a refusal in the platform's words fails S7" % (
        T.ADMIN_ENV_URL_KEY, T.ADMIN_CREDIT_ROUTE % "<Harness Holdings' aapAccountId>", holdings_credit, T.ADMIN_ENV_KEY_KEY))
    line("S7", "POST <%s>%s %s — only where the Treasury was not credited above → expect 201" % (T.ADMIN_ENV_URL_KEY, T.ADMIN_CREDIT_ROUTE % "<the Treasury's aapAccountId>", credit_body))
    signers = names_in_words([A.PEOPLE[k].name for k in SIGNERS_IN_ORDER])
    for payment, row in zip(A.PAYMENTS, three):
        tier_words = under_the_tiers(payment.amount, tier_alone, tier_two)
        payee = row["oneOff"]["address"] if "oneOff" in row else "<address of %s>" % payment.payee_name
        call = _j({"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": "<the %s contract the estate names>" % T.PAYMENT_ASSET, "data": "<balanceOf(%s)>" % payee}, "latest"]})
        line("S7", "POST %s %s → expect a 32-byte hex word: %s's %s balance in minor units before the payment (the chain's public RPC, read from the corridor harness's own skeleton at run time; a fault is the RPC's, and a proof it could not read is not a pass)" % (
            T.public_rpc_url(T.PAYEE_CHAIN), call, payment.payee_name, T.PAYMENT_ASSET))
        line("S7", "POST /v1/sets/review %s (as %s) → expect the gates' review; %s; a %s refusal credits Holdings more gas once and asks again" % (_j({"pays": [row], "duplicatesAcknowledged": False}), clerk.name, tier_words, T.GAS_SHORTFALL))
        line("S7", "POST /v1/sets %s (as %s) → expect 201: the run in draft" % (_j({"pays": [row], "duplicatesAcknowledged": False, "idempotencyKey": "aer360-harness-<run>-%s" % payment.key, "reference": "Harness payment %s" % payment.key}), clerk.name))
        line("S7", "POST /v1/sets/<run %s>/submit {} → expect status and approvalsRequired as the estate's band and destination rule decide; %s (%s): expected to %s; %s; %s" % (
            payment.key, payment.amount, T.PAYMENT_ASSET, payment.expect, Runner.TIER_ROAD_WORDS[payment.key], tier_words))
        line("S7", "POST /v1/approvals/<run %s>/challenge {} then /approve %s (as %s in turn while the run waits: the holder, the clerk, then the approver and the third party) → expect the estate's answer to each in its words — ROLE_NOT_GRANTED where it admits the approver standing alone — until status approved; a refusal is never retried" % (
            payment.key, _j({"response": "<assertion over the challenge>"}), signers))
        line("S7", "POST %s {} (as %s) → expect setStatus settled and the instruction confirmed with its txHash: the platform reported the operation %s (Spec 104 §2)" % (
            T.SET_EXECUTE_ROUTE % ("<run %s>" % payment.key), clerk.name, T.PLATFORM_LANDED))
        line("S7", "GET /v1/sets/<run %s> → expect the run as the register shows it, read until its instruction is terminal" % payment.key)
        line("S7", "POST %s %s → expect %s's %s balance after, risen by exactly %s; otherwise the payment fails naming the two figures" % (
            T.public_rpc_url(T.PAYEE_CHAIN), call, payment.payee_name, T.PAYMENT_ASSET, payment.amount))
    line("S7", "GET %s?limit=%d (as %s; every page by its nextCursor) → expect one %s row per payment that landed: userOpHash, the handleOps txHash, gasDebitUsdCents and gasDebit in the platform's own figures; each payment is judged on the run's status, the userOpHash, the txHash and the payee's balance risen by its amount, the gas debited reported beside it (Spec T14 §4)" % (
        T.AUDIT_EXPORT_ROUTE, T.AUDIT_EXPORT_LIMIT, founder.name, T.INSTRUCTION_CONFIRMED))
    line("S7", "GET %s (as %s), GET %s (as %s), GET %s (as %s), GET %s (as %s) → the money after: both workspaces' %s and gas accounts, for S10's count" % (
        T.FUNDING_BALANCES_ROUTE, clerk.name, T.FUNDING_BALANCES_ROUTE, treasurer, T.GAS_ACCOUNT_ROUTE, clerk.name, T.GAS_ACCOUNT_ROUTE, treasurer, T.PAYMENT_ASSET))
    # S8
    line("S8", "GET /v1/journey → printed: the stage, the stages done")
    line("S8", "GET /v1/workspace/readiness → printed: transactable True once the wallet exists (False, reason \"%s\", before it), and the funding wallet's address" % NO_FUNDING_WALLET_REASON)
    # S9
    line("S9", "[out of scope] the tour's answers as Claude would see them: the harness is the founder, not Claude")
    # S10
    line("S10", "[compare] the read-back of each interview word for word with the answers given, as readback() spells them")
    line("S10", "[compare] the compiled charter (the compile answer) with the read-back: the figures, the rosters, the networks; GET /v1/onboarding/charter for its standing")
    line("S10", "[compare] the compiled charter's Spec 92 fields with the answers given: payeeApproval (C11A — the change approvers, the census of %d at a quorum of %d), payeeVenueContracts (C19 — %s), holder (WO1 — %s, by_person, %s), signingTiers.holderAloneUpToCents (WO3 — %s) and twoSignaturesUpToCents (WO4 — %s), and WO2's third party among the signers; the read-back's WO3 and WO4 as the book wrote them and never as the written US$1.00, and C19's door line" % (
        len(A.WHITELIST_ROSTER), A.WHITELIST_QUORUM, venue_law_of_the_book(), A.PEOPLE[A.WALLET_HOLDER].name, A.WALLET_HOLDER_TITLE,
        A.MONEY["holder_alone_cents"], A.MONEY["two_signatures_cents"]))
    line("S10", "GET /v1/journey, GET /v1/onboarding/charter, GET /v1/payees, GET /v1/sets, GET /v1/invites → [compare] the journey stage with what the registers hold")
    line("S10", "[check] every money figure the server returned against the minor-unit law (money.ts): an integer string of minor units, never a float")
    line("S10", "[check] every refusal met in S1 to S9 for Rule 13: it names what happened and who refused; a bare status or a generic sentence is a finding")
    line("S10", "[compare] the People register with the invitations sent, and the credential id each session carries")
    line("S10", "[compare] the payees register with the whitelist the charter enforces and with what Ada approved")
    line("S10", "GET %s?limit=%d → [compare] the trail's %s row for each seat S4 moved: the ceremony's id, seatEmail, via %s, and signerNames naming every signer (Spec T15 §3); the note about a seat still bound to a retired passkey is dropped where S4 moved it" % (
        T.AUDIT_EXPORT_ROUTE, T.AUDIT_EXPORT_LIMIT, T.ROSTER_SEAT_REBOUND, T.VIA_ROSTER_CHANGE))
    line("S10", "[compare] the money moved (Spec T14 §5): Harness Treasury's %s before and after, Harness Holdings' %s before and after, the sum of the three payments (%s), and Holdings' gas account before and after against the sum of the three gas debits — one note, and a finding where any pair does not reconcile to the cent" % (
        T.PAYMENT_ASSET, T.PAYMENT_ASSET, Runner.payments_need()[1]))
    # S11
    line("S11", "POST /v1/workspace/display-currency %s without x-csrf-token → expect 401 NOT_AUTHENTICATED" % _j({"displayCurrency": A.ESTATE["display_currency"]}))
    line("S11", "POST /v1/onboarding/interviews/<policy interview>/confirm/options {} then /confirm as Ben with the founder's passkey → expect a refusal by name")
    line("S11", "POST /v1/invites %s (as %s) → expect 201; then invite/options and invite/verify → a viewer's session" % (_j({"displayName": A.PEOPLE[A.VIEWER_INVITED].name, "email": A.PEOPLE[A.VIEWER_INVITED].email, "role": "viewer"}), founder.name))
    for route in ("POST /v1/payees", "POST /v1/sets", "POST /v1/invites", "POST /v1/onboarding/interviews/<policy interview>/answers"):
        line("S11", "%s (as %s, a viewer) → expect 403 ROLE_NOT_GRANTED naming the room" % (route, A.PEOPLE[A.VIEWER_INVITED].name))
    line("S11", "POST /v1/invites %s → expect 422 INVITE_ROLE_NOT_AVAILABLE, refused by name" % _j({"displayName": "Principal probe", "email": "harness+principal@aeredium.io", "role": "principal"}))
    line("S11", "POST /v1/onboarding/interviews %s → a probe draft; POST .../answers %s → expect 400 ANSWER_INVALID (not asked given the answers so far)" % (_j({"interviewType": "policy"}), _j({"questionId": "B4", "value": {"choices": []}})))
    line("S11", "POST /v1/onboarding/interviews/<policy draft>/compile {} → expect 409 INTERVIEW_NOT_OPEN: the compiler reads only confirmed interviews")
    line("S11", "POST /v1/onboarding/interviews %s → a probe draft walked to O1; POST .../answers %s → expect 400 ANSWER_INVALID (an amount is a whole number of cents)" % (
        _j({"interviewType": "wallet_account"}), _j({"questionId": "O1", "value": {"cents": "fifty thousand dollars"}})))
    line("S11", "POST /v1/auth/login/options then /verify twice with the same nonce, issuedAtMs and challenge → expect the second refused 403 STEP_UP_STALE: challenge already used")
    line("S11", "POST /v1/auth/login/verify with an assertion whose rpIdHash is SHA-256('not-the-estate.invalid') → expect 403 STEP_UP_INVALID")
    line("S11", "POST /v1/payees %s → expect a refusal, or the estate's acceptance recorded" % _j({"displayName": "Checksum probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))}]}))
    venue_body = _j({"displayName": "Venue probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": "<the corridor's tables.py UNISWAP_V3_ETHEREUM, read at run time>"}]})
    if venue_law_of_the_book() == "refused":
        line("S11", "POST /v1/payees %s → expect %d %s: %s (the book answers %s %s; the live run reads the compiled policy charter's payeeVenueContracts); an acceptance is the finding" % (
            venue_body, PAYEE_IS_VENUE_CONTRACT_STATUS, PAYEE_IS_VENUE_CONTRACT, payee_is_venue_contract_sentence(ESTATE_VENUE_NAMES["uniswap_v3"], T.PAYEE_CHAIN),
            VENUE_CONTRACT_QUESTION_ID, _j(A.POLICY_ANSWERS["C19"]["choice"])))
    else:
        line("S11", "POST /v1/payees %s → expect 201, accepted, as the law says (%s; the book answers %s %s, and the live run reads the compiled policy charter's payeeVenueContracts); a refusal is the finding" % (
            venue_body, VENUE_RULING, VENUE_CONTRACT_QUESTION_ID, _j(A.POLICY_ANSWERS["C19"]["choice"])))
    line("S11", "[check] S7's P3 (%s %s, above the per-payment limit) was not released without approval" % (A.PAYMENTS[2].amount, T.PAYMENT_ASSET))
    line("S11", "POST /v1/approvals/<run P3>/challenge {} then /approve (as %s, who entered it) → expect a refusal in the charter's words" % clerk.name)
    line("S11", "POST /v1/onboarding/interviews/<policy interview>/confirm/options {} then /confirm (as %s) → expect 409 INTERVIEW_NOT_OPEN: confirm happens at the read-back" % founder.name)
    line("S11", "DELETE /v1/onboarding/interviews/<policy draft>, DELETE /v1/onboarding/interviews/<account draft> → the probe drafts deleted")
    # S12
    line("S12", "[measure] every call's wall time; every call over %.0f seconds; the ten slowest with their routes" % SLOW_CALL_SECONDS)
    line("S12", "[measure] the calls the interviews needed, and how many were reads a browser would not make (a question served twice, a read-back fetched twice)")
    line("S12", "[measure] the size of the largest answer; any 5xx retried once after %.0f seconds, both answers kept" % RETRY_AFTER_5XX_SECONDS)
    if start_at:
        if start_at not in STATION_IDS:
            raise HarnessError("no station called %s; the stations are %s" % (start_at, ", ".join(STATION_IDS)))
        cut = STATION_IDS.index(start_at)
        kept = [l for l in lines if STATION_IDS.index(l.split(" — ", 1)[0]) >= cut]
        return ["resume — POST /v1/auth/login/options {} and /verify for every stored passkey (%s)" % ", ".join(A.PEOPLE[k].name for k in (A.FOUNDER,) + A.AUTHORS_INVITED + (A.VIEWER_INVITED,))] + kept
    return lines


# ---------------------------------------------------------------------------
# The command line.
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="The Estate Harness: walks AER 360 end to end as a founder (Spec T7).")
    parser.add_argument("--base", default=DEFAULT_BASE, help="the estate's base URL (default %s; %s for the demo estate)" % (DEFAULT_BASE, DEMO_BASE))
    parser.add_argument("--invite", help="the founder's one-time invitation link, first run only; never paste it into a chat")
    parser.add_argument("--treasury-invite", dest="treasury_invite", help="Harness Treasury's founder invitation link, the birth run only (Spec T14); never paste it into a chat")
    parser.add_argument("--from", dest="start_at", help="resume at a station, for example S5, signing in with the stored passkeys")
    parser.add_argument("--dry", action="store_true", help="print every call the harness would make, without connecting")
    parser.add_argument("--fresh", action="store_true", help="set the stored passkeys aside and enrol a new estate; refuses without --invite")
    parser.add_argument("--out", default=".", help="the folder the report is written to (default the working folder)")
    parser.add_argument("--store", default=STORE_DIR, help="where the passkeys are kept (default ~/.aer360-harness)")
    args = parser.parse_args(argv)

    if args.dry:
        for line in dry_lines(args.base, args.start_at, with_invite=bool(args.invite) or not args.start_at):
            print(line)
        print("Dry run: nothing was sent.")
        return 0
    if args.fresh and not args.invite:
        print("--fresh refuses to run without a new --invite <link>: a second estate is a deliberate act.")
        return 2
    runner = Runner(args.base, args.store, args.invite, args.fresh, args.start_at, args.out, treasury_invite=args.treasury_invite)
    try:
        runner.run()
    except KeyboardInterrupt:
        print("Interrupted; the report is written with what ran.")
    except HarnessError as err:
        print(str(err))
        return 2
    finally:
        if runner.outcomes:
            path = runner.write_report()
            print("Report: %s" % path)
    return 1 if any(o.outcome == FAIL for o in runner.outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
