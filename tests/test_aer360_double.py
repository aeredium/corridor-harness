"""
AN ESTATE THAT ANSWERS AS THE CODE DOES: a local double of the AER 360 routes the estate harness
speaks to, and the tests that hold the double to the service it stands in for.

The standing law (4 September 2026): every test double must be at least as strict as the real
service — it refuses what the service refuses, with the service's own sentence and status. So
this double is a re-statement, route by route, of aeredium/AERAccounts at e651616:

  routes/auth.ts, services/webauthn.ts     the invitation and sign-in ceremonies, verified by the
                                           pure-Python re-statement in aer360_passkey.py; a replayed
                                           challenge is STEP_UP_STALE, a wrong rpId STEP_UP_INVALID
  routes/guards.ts, services/session.ts    the cookie aer_accounts_session, x-csrf-token on every
                                           mutating route (and not on the onboarding routes, exactly
                                           as the code has it), the roles
  services/roles.ts, refusals.ts           ROLE_NOT_GRANTED in the room sentence
  routes/onboarding.ts, services/onboarding.ts, crosschecks.ts
                                           the interview: pages, validateValue, the quorum-roster
                                           checks, the read-back, confirm, compile
  routes/invites.ts, services/invites.ts   principal refused by name; an author invitation enrols
                                           the ONE role-bearing credential the account carries
  routes/approverseats.ts                  the seats, grant
  routes/payees.ts, payeeaddress.ts        the shape of an address, lower-cased; promote; approve
                                           under approvallaw.ts
  routes/sets.ts, setgates.ts, destinationlaw.ts, roles.ts resolveQuorumBand
                                           review and create, the band and the destination wait
  routes/approvals.ts, approvallaw.ts      challenge and approve
  routes/journey.ts, services/journey.ts   the stage facts; routes/workspace.ts; http.ts statuses

It is a transport for aer360_harness.Runner: a callable taking a urllib Request and answering
(status, headers, text), so the harness's own cookie jar, CSRF header and recording are exercised.

Spec T8 (20 September 2026) held the double to two more of the estate's ways, because a double that
speaks what the service does not is how a wrong comparison ships with a green suite:

  db/onboardingschema.ts `value: jsonb('value')`   an answer is stored as jsonb stores it — keys shortest
                                                   first, then in byte order — so the read-back speaks the
                                                   census as `name — role — email`, as the live estate did
  services/onboarding.ts, the `spoken` switch      on main (dff4c9a, e651616) the currency kind has no arm
                                                   and falls to `default: JSON.stringify(v)`: A5 is read back
                                                   as '{"text":"AUD"}', as the live run heard it. Spec 88's
                                                   `spokenAnswer` (35cdc6f, not yet merged) speaks the code;
                                                   `currency_spoken_as_code=True` is that estate

and gave it two dials the harness's tests need: `refuses_venue_contract=True` stands in for the day the
questionnaire gains a stipulation against venue contracts (the estate has no such road and so no word for
it; the double borrows ADDRESS_PROPOSAL_REFUSED, the code the estate uses for an address it will not
propose, and says in its detail what it stands in for), and `invite_seconds` makes POST /v1/invites take
that long on a clock the runner shares, the way the live road does while it awaits the email's dispatch.

Spec T9 (20 September 2026) held the double to the whitelist road as Spec 89 (aeredium/AERAccounts,
commit 7d809e1) left it, because the second live run pressed once and met an answer that said nothing:

  services/onboardingcompiler.ts, governanceSignersFor   the `whitelist_mutation` roster is the census (A8),
  and governanceRecordsFor                               one seat per person named by email with the credential
                                                         slot empty until a press binds it, at C12's number
                                                         (each family's own behind a Yes on C12A); seated here
                                                         when the policy charter compiles (`whitelist_seats`)
  routes/payees.ts, services/payees.ts                   a press that leaves the address pending answers
  (pendingApprovalStanding, pendingApprovalSentence)     approvals {required, collected, remaining},
                                                         may_still_approve (the unsigned, by display name) and
                                                         the sentence, composed word for word as the estate
                                                         composes it (`pending_approval_sentence`); the press
                                                         that meets the count answers whitelisted and nothing
                                                         about waiting; the same person pressing again is told
                                                         the same thing, because the platform counts a
                                                         signature once (routes/payees.test.ts, "the same
                                                         person pressing again is told the same thing")
  test/aapDouble.ts, the signatures road                 a press by somebody with no seat on the roster is the
  services/payees.ts, signAsPresser                      platform's bare "not authorized", relayed as
                                                         SIGNATURE_NOT_COUNTED with the platform's status and
                                                         words in the detail

and three dials: `pending_approval_says_why=False` is the estate of 20 September 2026 before Spec 89, whose
press answered `{"whitelistStatus": "pending_promotion"}` and nothing else; `whitelist_roster=("ada",)`
seats only the people named, so a roster smaller than its quorum can be met; `platform_never_activates=True`
is a platform that counts every signature and never activates the address, so the count is met and the
status never moves.

Spec T10 (20 September 2026) taught the double AER 360 Spec 91 (aeredium/AERAccounts, commit 9964205, PR #112),
and corrected one choice Spec T9 had made its own: T9 counted a press for the seat of the PERSON pressing,
found by email, so that Ben's press could count after Ada's on the one credential four people wore. The
fourth live run proved the platform counts otherwise, and Spec 91's builder established the rule from the
platform's source (aegiskey-access-platform, internal/access/pending_transaction_v2.go,
`validateMultisigSigner`; the estate's own double of it, apps/server/src/test/aapDouble.ts, the signatures
road): a signature counts for an ACTIVE seat of the roster matched by CREDENTIAL; a press that says whose seat
it is (`user_id`) binds the caller's credential to that person's EMPTY seat; a seat already bound to a
different key refuses, with the platform's bare "not authorized"; and a credential is counted once per
ceremony. So on the shared credential Ben's press matches Ada's bound seat and counts nothing, as the live
run met, and two distinct credentials make two of two. The estate's press says whose seat it is only where
the estate can attach the credential to ONE address that no other person's key shares
(services/payees.ts, signAsPresser → signerEmailOf → emailOfCredential; Spec 91's addressOfCredential).

  services/invites.ts, mintAuthorCredential          an `author` invitation mints a credential of the person's own on
                                                     the ONE in-force policy entry bearing `sign` that a credential holds
                                                     (several are INVITE_INVALID, listing entries and credentials);
                                                     redemption binds the passkey to it
  routes/auth.ts, services/invites.ts               a re-invitation's redemption retires the bindings an earlier redeemed
  (earlierBindingsOf, person.credential_replaced)    invitation of the same address enrolled
  services/approverseats.ts (enrolmentRecords,       a credential no passkey here speaks for is nobody's; a retired binding
  credentialHolders, othersHolding)                  is dropped from the address; a credential other people's passkeys also
                                                     speak for is refused a seat (APPROVER_SEAT_CREDENTIAL_SHARED, 409) and
                                                     never seated by the redemption road; several credentials on one address
                                                     are APPROVER_SEAT_AMBIGUOUS (409), never guessed between
  routes/invites.ts, services/invites.ts             GET /v1/invites marks each person's newest redeemed row with the other
  (markSharedCredentials)                            names whose passkeys speak for its credential: `sharesCredentialWith`
  services/onboardingcompiler.ts (establishGovernance) the change governance — the rosters — is established once; a later
  test/aapDouble.ts (/v1/mutation-governance/establish) compile leaves it (`governanceAlreadyStood`), so a seat once bound at
                                                     the platform stays bound

and the knobs: `before_spec_91=True` is the estate of the four live runs — an author invitation enrols the founder's
credential, nothing is retired, the register carries no marker, the seat road unions and refuses nothing for sharing;
`seat_completes_on_redemption=False` is an estate before Spec 58's count 3, whose redemption says nothing of a seat;
`second_authorship_entry=True` gives the account a second policy entry bearing authorship (a CFO's credential), so an
author invitation is refused, listing both, as Spec 91's own test has it; `platform_names_approver=("ben",)` is an
operator at the platform's own console naming a person's minted credential a second approver on the entry — outside
the estate's seat road, which refuses them (APPROVER_SEAT_NOT_IN_CHARTER), and read live by the estate (roles.ts).

Spec T11 (21 September 2026) taught the double AER 360 Spec 92 (aeredium/AERAccounts, commit cf3be4a, catalog version 14), read
from the code and not from memory, because the run of that night stopped on questions the double had never served:

  services/questioncatalog.ts                        the seven questions version 14 added (C11A, C11C, C19, WO1, WO2, WO3, WO4), the
                                                     option W1 gained, their parts, prompts, options, list fields and notes, served
                                                     from tests/fixtures/aer360-served-2026-09-21.json — the pages the estate served
                                                     that night, and the catalog's words for the five the run never reached; WO3 and
                                                     WO4 served with the written dollar as their value where no answer stands
  services/onboarding.ts, validateValue              `person_or_none`: the choice is one of the two options; behind the first the
                                                     person is named in full with a work email; behind "No one" no person travels
  services/onboarding.ts, spokenAnswer, readback     a person is spoken as `<name> — <email>.`; a written zero as a wall; and Spec 92's
                                                     synthetic lines — C19_DOOR after a No, WO1_TITLE after a named holder, HOLD_NOT_WRITTEN
                                                     and WQ_TIERS on a tiered account
  services/onboardingcompiler.ts                     `payeeApprovalOf` (the whitelist_mutation roster the answer to C11A draws up, which
                                                     the double seats), `venueContractsOf`, `readWalletPeople` (the holder with the title
                                                     `holderTitleFor` gives, the third party with a title of the three, the two figures),
                                                     `assertSigningTiersConsistent` (WO4 not above WO3; fewer than three people between
                                                     WA1 and WO2 — refused at the read-back, the confirm and the compile in the spec's own
                                                     sentences), the third party as a signer beside WA1's people once by email, and the
                                                     charter's `payeeApproval`, `payeeVenueContracts`, `holder` and `signingTiers`
  services/payees.ts, assertPayeeIsNotVenueContract  THE DOOR: where the written policy charter says `payeeVenueContracts: 'refused'` and
  packages/shared/src/venues.ts, refusals.ts         the address is on the engine's closed venue table (copied here row for row), the
                                                     payee is refused PAYEE_IS_VENUE_CONTRACT, 422, in `payeeIsVenueContractSentence`'s
                                                     words, naming the venue as it publishes itself and the chain sent

and the venue dial is redrawn: `refuses_venue_contract=None` (the default) is the door following the charter, as Spec 92 built it;
`True` is the stand-in of Spec T8 — a door that refuses the probe address regardless of its charter, under ADDRESS_PROPOSAL_REFUSED,
which now stands for an estate refusing against a charter that says accepted; `False` is a door that saves the address regardless,
an estate whose door never learned C19. `catalog_version` below 14 leaves the seven out, the estate of the runs before 21 September.

Spec T13 (22 September 2026) taught the double AER 360 Spec 98 (aeredium/AERAccounts, commit 56582b8), the faucet and the chain, read from
their own code, because the run of 23:44 met an estate with no funding wallet and a register that lagged the platform:

  routes/workspace.ts, services/fundingwallet.ts     GET /v1/workspace answers fundingWallet {address, keyId, homeStack, bornAt, sentence}
                                                     or fundingWalletAbsence (NO_FUNDING_WALLET_SENTENCE); the founder's press is two steps —
                                                     POST /v1/workspace/funding-wallet/options, whose challenge is derived from the binding
                                                     `funding-wallet:<workspace id>:<issuedAtMs>` | credential | `workspace.funding_wallet`
                                                     (services/stepup.ts, deriveChallenge), refusing FUNDING_WALLET_ALREADY_BORN (409) where a
                                                     key stands; and POST /v1/workspace/funding-wallet with issuedAtMs and the assertion, which
                                                     births the wallet (born true) or refuses WALLET_BIRTH_REFUSED (502, the gateway's words in
                                                     detail.gatewaySaid — tonight “PermissionDenied: not authorized”) or GATEWAY_UNAVAILABLE
                                                     (503, a deployment fault named with its setting); readiness reads transactable false with
                                                     the reason `no funding wallet` until both columns stand
  services/payees.ts, the mirror (`mirror_lags`)     the press that meets the count may answer the row's stale `proposed` while the platform
                                                     counted 2 of 2; `register_corrects` (Spec 100) is whether GET /v1/payees reads whitelisted
                                                     on the next read or still `proposed`
  services/setgates.ts gasPreflight, chains.ts       `asset_short`: the gas pre-flight's estimate of the USDC transfer reverts at the RPC, so
  wrapRpc                                            the run is refused GAS_PREFLIGHT_UNAVAILABLE with the RPC's words as the cause
  aeredium/faucet, server_manual.go (FaucetDouble)   POST /faucet-api/request {"address"} → ok, paid and tx_hash; ok and queued; or the
                                                     handler's own refusal sentence under `error` at its status (400, 409, 429)
  the chain's public RPC (TestnetRpcDouble)          eth_getBalance answers the balance this double is told, as a hex quantity; eth_chainId 0x8bd

and the knobs: `funding_wallet="press"` (the default) is an estate whose wallet the press births; `"born"` already holds it; `"refused"` is
the estate of 23:44, whose gateway refuses the credential; `"unavailable"` a deployment with no gateway configured.

Spec T15 (22 September 2026) taught the double AER 360 Spec 99 (aeredium/AERAccounts, commit 33e039c) and, beneath it, the platform's
pending-transaction roads as the estate's own double of the platform models them (apps/server/src/test/aapDouble.ts), read from the code,
because the run of 13:50 met a seat the census had no door to move:

  services/approverseats.ts, rebindRosterSeats     A SEAT FOLLOWS ITS PERSON (Spec 95): at a re-invitation's redemption (routes/auth.ts,
  (`rebind_roster_seats`)                            invite/verify) and at a seat grant — never at a sign-in — every active roster seat naming
                                                     the person's address and bound to a credential they no longer hold is presented to the
                                                     platform moved (`replace_multisig_signers`, the roster sent again with the one credential
                                                     changed); where the account's change governance holds multisig_update at a count above
                                                     one, the platform answers a CEREMONY and the estate records it against the seat
                                                     (`roster.change_proposed`, Spec 99) and answers `rosterSeats.awaiting` with Spec 95's
                                                     sentence; at a count of one the platform applies it and the trail says `roster.seat_rebound`
  test/aapDouble.ts, the pending transactions       the ceremony's lifecycle — pending → approved the moment the count is met → consumed when the
  (`born_ceremony`, `ceremony_is_live`)             governed write is presented again with the same content, which the platform binds it to by
                                                     digest; a lapse read off expires_at (24 hours), never swept to a word; a signature counts for
                                                     an active seat matched by credential, or binds an empty seat named by the address the press
                                                     carries; anybody else "not authorized"; a lapsed ceremony "conflict: pending transaction
                                                     expired"; one no longer pending "conflict: pending transaction is <status>"
  routes/rosterchanges.ts, services/approverseats.ts GET /v1/roster/changes (`list_roster_changes`, `roster_change_view`): every multisig_mutation
  (listRosterChanges, signRosterChange,             ceremony, newest first, joined to the seat the estate recorded, with who has signed, who may
  applyRosterChange)                                 and whether the caller may — a ceremony no seat row names is "a roster change this estate did
                                                     not propose" and is never matched by guesswork; POST …/sign/options and …/sign
                                                     (`roster_change_sign_options`, `sign_roster_change`): the step-up bound to
                                                     `roster-change:<workspace id>:<pendingTxId>:<issuedAtMs>` | credential | `roster.change`, then
                                                     in the fail-closed order ROSTER_CHANGE_UNKNOWN (404: not proposed here, or not listed),
                                                     CHANGE_SIGNER_NOT_ON_ROSTER (403, the roster's own words naming who may, before the platform
                                                     is asked), APPROVER_ALREADY_SIGNED (409, from the platform's record, never asked twice), the
                                                     platform's own no relayed as PLATFORM_REFUSED (502, Spec 97's sentence) or SIGNATURE_NOT_COUNTED
                                                     (403, "not authorized" in detail.platformSaid); the count met, the change presented again and
                                                     the seat marked rebound from the roster the platform returns (`apply_roster_change`), the trail
                                                     row naming the ceremony and every signer
  packages/shared/src/enrolment.ts, refusals.ts     every sentence, word for word (`roster_change_sentence`, `roster_change_signed_sentence`,
                                                     `not_on_change_roster_sentence`, `platform_refused_sentence`, `roster_seat_awaiting_sentence`)
  routes/exports.ts, auditRegister                  GET /v1/export/audit (`audit_export`): the trail a browser reads, oldest first — `items` of
                                                     audit_id, at, action, credential_id, subject_id, detail
  services/payees.ts, approvalPlatformRefusal       a whitelist press on an entry the platform no longer holds pending — the count met and the
                                                     address active — is the platform's 409 "entry is already active" relayed as
                                                     ADDRESS_PROPOSAL_REFUSED in the approve road's own sentence: a third press is refused as
                                                     unneeded, in the platform's words

and the knobs: `change_roster=("ben", "cora")` seats only the census keys named on the multisig_mutation roster (None, the default, seats the
census the compiler writes, `governanceSignersFor`: the four at C12's count); `before_spec_99=True` is the estate at Spec 95 — the move is
proposed and the platform holds the ceremony, but no seat row is recorded and the roster roads do not exist; `ceremony_lapses=1` makes the next
ceremony born lapse at birth (the platform's clock past its expires_at), `2` the next two; `lapse_after_first_signature=True` lets the clock pass
a ceremony's expiry once its first signature is counted, so the second meets the platform's "conflict: pending transaction expired";
`account_email` is the AAP account's own address, which the estate attributes to the founder's key (`addressesOfCaller`) — None, the default,
is an account whose address the double does not know, so the founder's key is attributed no census seat.

Spec T14 (22 September 2026, amended 22:35; built 24 September 2026) taught the double AER 360 Spec 104 (aeredium/AERAccounts, commit 8812c64)
and platform Spec 154 and 154b (aeredium/aegiskey-access-platform, commits e7dc195 and 451b998), read from their code, because the harness now
pays real USDC through the estate's own road and buys its gas from the platform's ledger:

  routes/workspace.ts, services/fundingwallet.ts     the funding wallet view carries the fund sentence and the chains this deployment pays on (Spec 104
                                                     §1); GET /v1/workspace/funding-account/balances answers the stablecoin the key holds per chain in
                                                     dollars — chain, asset, the token contract, balanceMinor, usdMinor, the sentence — read from the
                                                     chain double (UsdcChainDouble)
  routes/gas.ts, services/accountabstraction.ts      GET /v1/gas/account: the balance read live from the platform double's ledger, "Gas account: US$…",
                                                     the platform's low flag (twice the median of the last ten debits, or US$1.00), the press not open
  routes/sets.ts requireSourceAccount                a run asked of an estate with no funding wallet is WORKSPACE_NOT_PROVISIONED (503) in the
                                                     funding wallet's own sentence — GAS_PREFLIGHT_UNAVAILABLE is gone with the pre-flight
  services/execution.ts gasAccountPreflight          THE FOURTH GATE (`gas_account_preflight`): the balance read before the quotes, one dry quote
                                                     per payment — the chain's dry run of the transfer refuses where the key holds less than the
                                                     amount (PAYMENT_UNPRICED, "This payment could not be priced: <their sentence>"), the platform
                                                     refuses each quote the balance cannot cover (insufficient_gas) and its ceiling still counts —
                                                     and U3's sentence with the set's figures under GAS_SHORTFALL where the balance is below the sum;
                                                     the review's reservations are released by the platform's poller at valid_until, which in this
                                                     double is the review's end
  routes/sets.ts, services/execution.ts executeSet   POST /v1/sets/{id}/execute (`execute_set`, `drive_payment`): an approved run executed by its
                                                     author — the ceiling reserved, U3's per-payment refusal where the balance cannot cover it, the
                                                     transfer on the chain double, the debit at actual cost, the instruction confirmed with its txHash
                                                     and gasValue, the run settled or partially settled (states.ts resolveSetOutcome), and the trail's
                                                     instruction.confirmed row with userOpHash, txHash, gasDebitUsdCents and gasDebit
  services/approverseats.ts completeSeatOnCharterWrite the confirming credential is seated where the charter names an address the estate attributes
                                                     to it (addressesOfCaller) — the account's own address for the founder's key (`account_email`)
  internal/api/gas_handlers.go, middleware.go        THE PLATFORM (PlatformDouble): the gas ledger per account and the ADMIN credit road, POST
  internal/gas/credit.go, ledger.go                  /v1/admin/accounts/{id}/gas-account/credits under the admin key — 401 in adminAuth's three
                                                     sentences, reason required, an unknown account 404, a repeated key deduped, 201 with the line and
                                                     the balance; the door road and the card road are not walked by the harness
  the payment chain (UsdcChainDouble)                the token contract the estate names, every holder's USDC in minor units, the transfers the
                                                     payments make, and the chain's public RPC answering eth_call balanceOf as a node does

and the sandbox is TWO WORKSPACES ON ONE ESTATE: every EstateDouble births a Treasury double beside it (Harness Treasury, `T.TREASURY`), sharing the
platform, the chain and the step-up secret, and answers a request the Treasury owns — its session's cookie, its invitation's token, its passkey at the
sign-in road — by handing it over (`owns`). Knobs: `treasury_usdc_cents` (US$100.00: what Bear funded the float with), `holdings_usdc_cents` (US$0.00),
`treasury_funding_wallet` ("born": Bear birthed and funded it before this run; "press": this run births it and stops), `gas_refusal_names_other_figures`
(a review whose sentence names other figures), `review_refuses_but_pays` (a review that says nothing was sent while money moved), `UsdcChainDouble(
lose_transfers=True)` (a payee whose balance does not rise), `PlatformDouble(debit_gap_cents=1)` (a ledger one cent apart from the trail), and
`runner_on(..., admin_env=False)` (no credential filed). `asset_short` is gone: the chain's balances decide.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import tempfile
import time
import unittest
import unittest.mock
import urllib.parse
import urllib.request
import uuid
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "aer360-questioncatalog.v11.ts")
BASE = "https://estate.test"
RP_ID = "estate.test"
WORKSPACE_ID = "ws-harness"
AAP_ACCOUNT_ID = "aap-account-harness"

# --- the refusal vocabulary, as refusals.ts and http.ts spell it -----------------------------
STATUS = {
    "NOT_AUTHENTICATED": 401, "PASSKEY_NOT_ENROLLED": 401, "INVITE_INVALID": 401, "ROLE_NOT_GRANTED": 403,
    "SUBMITTER_MAY_NOT_APPROVE": 403, "STEP_UP_INVALID": 403, "STEP_UP_STALE": 403, "INTERVIEW_NOT_FOUND": 404,
    "INTERVIEW_NOT_OPEN": 409, "ANSWER_INVALID": 400, "CHARTER_INCOMPLETE": 409, "INVITE_ROLE_NOT_AVAILABLE": 422,
    "INVITE_ALREADY_STANDING": 409, "ADDRESS_MALFORMED": 422, "ADDRESS_NOT_WHITELISTED": 422,
    "ADDRESS_PROMOTION_PENDING": 422, "CHAIN_NOT_SUPPORTED": 422, "SET_NOT_APPROVABLE": 409,
    "APPROVER_ALREADY_SIGNED": 409, "GAS_PREFLIGHT_UNAVAILABLE": 503, "REQUEST_MALFORMED": 400,
    "INTERNAL_ERROR": 500, "APPROVER_SEAT_NOT_ENROLLED": 422, "APPROVER_SEAT_NOT_IN_CHARTER": 422,
    "ONE_OFF_NOT_DECLARED": 422, "AMOUNT_MALFORMED": 400, "ASSET_UNKNOWN": 422, "WORKSPACE_NOT_PROVISIONED": 503,
    "SET_NOT_EDITABLE": 409, "BASE_CURRENCY_UNSET": 422, "ADDRESS_PROPOSAL_REFUSED": 422, "SIGNATURE_NOT_COUNTED": 403,
    "APPROVER_SEAT_AMBIGUOUS": 409, "APPROVER_SEAT_CREDENTIAL_SHARED": 409, "PAYEE_IS_VENUE_CONTRACT": 422,
    "WALLET_BIRTH_REFUSED": 502, "GATEWAY_UNAVAILABLE": 503, "FUNDING_WALLET_ALREADY_BORN": 409, "GAS_SHORTFALL": 422,
    "CHANGE_SIGNER_NOT_ON_ROSTER": 403, "ROSTER_CHANGE_UNKNOWN": 404, "PLATFORM_REFUSED": 502, "CHANGE_GOVERNANCE_UNREADABLE": 503,
    "ROSTER_SEAT_NOT_REBOUND": 502,
    # Spec 104 (accountabstraction.ts paymentUnpricedRefusal): the platform answered and refused a quote, 502; did not answer, or answered a fault, 503
    "PAYMENT_UNPRICED": 502, "PAYMENT_PRICING_UNAVAILABLE": 503,
}
MESSAGES = {
    "NOT_AUTHENTICATED": "You are not signed in.",
    "PASSKEY_NOT_ENROLLED": "That key belonged to no estate — it was stale, and it can never sign you in.",
    "INVITE_INVALID": "This invite link is expired or has already been used.",
    "ROLE_NOT_GRANTED": "Your credential does not carry this permission. Permissions come from your organisation’s policy, not from this application.",
    "SUBMITTER_MAY_NOT_APPROVE": "This cannot be approved by the same person who submitted it. Whether one person may do both is your organisation’s charter’s decision, and it says not here.",
    "STEP_UP_INVALID": "That passkey confirmation could not be verified.",
    "STEP_UP_STALE": "That passkey confirmation has expired. Please confirm again.",
    "INTERVIEW_NOT_FOUND": "No such interview.",
    "INTERVIEW_NOT_OPEN": "This interview is not at a stage where that action is possible.",
    "ANSWER_INVALID": "That answer does not fit the question as asked.",
    "CHARTER_INCOMPLETE": "The interview cannot compile: a mandatory answer is missing.",
    "INVITE_ROLE_NOT_AVAILABLE": "That role cannot be invited yet. Choose one of the roles this centre offers today.",
    "INVITE_ALREADY_STANDING": "An invitation to this person already stands, so a second one was not created. Resend the one that stands, or withdraw it first — two live invitations to one address is how an estate ends up with two keys for one person and no way to tell which to seat.",
    "ADDRESS_MALFORMED": "That is not an address the chain it names can pay, so nothing was saved. Check the address and the chain, then try again.",
    "ADDRESS_NOT_WHITELISTED": "This address is not on your approved payee list. Add it to the list, or mark this payment as a one-off.",
    "ADDRESS_PROMOTION_PENDING": "This address is still waiting to be approved onto your payee list, so it cannot be paid yet.",
    "CHAIN_NOT_SUPPORTED": "This service does not pay out on that chain.",
    "SET_NOT_APPROVABLE": "This run is not waiting for approval.",
    "APPROVER_ALREADY_SIGNED": "This approver has already signed this run.",
    "GAS_PREFLIGHT_UNAVAILABLE": "Network fees for this run could not be estimated, so it was not submitted.",
    "REQUEST_MALFORMED": "That request could not be read.",
    "INTERNAL_ERROR": "Something went wrong at our end. Nothing was changed.",
    "APPROVER_SEAT_NOT_ENROLLED": "This person holds no credential in this estate yet, so there is nothing to seat. Invite them; their seat completes itself when they bind their passkey.",
    "APPROVER_SEAT_NOT_IN_CHARTER": "Only the people your charter names as approvers can be given an approver’s seat. Naming somebody new is done in an interview, which is where policy is authored — not here.",
    "ONE_OFF_NOT_DECLARED": "This address is not on your approved payee list. To pay it anyway, mark the payment as a one-off.",
    "AMOUNT_MALFORMED": "That amount could not be read as a number.",
    "ASSET_UNKNOWN": "This service does not recognise that asset.",
    "WORKSPACE_NOT_PROVISIONED": "This workspace has not finished being set up from your AEGISKey account yet. Nothing can be paid until it has.",
    "SET_NOT_EDITABLE": "This run can no longer be edited.",
    "BASE_CURRENCY_UNSET": "Choose the currency your books reconcile to before entering payments. Every figure is valued in it.",
    "ADDRESS_PROPOSAL_REFUSED": "The access platform would not accept this address for approval, so it was not sent. Nothing was changed. The platform’s own words are below.",
    "SIGNATURE_NOT_COUNTED": "The access platform did not count your approval: it does not recognise your key as one of this wallet’s signatories. The address stays exactly as it was — nothing was approved, and nothing was changed.",
    "APPROVER_SEAT_AMBIGUOUS": "This email address matches more than one enrolled credential, so which one to seat cannot be told from the record. Nothing was changed. Withdraw or revoke the credentials that are no longer this person’s, and grant the seat again.",
    "APPROVER_SEAT_CREDENTIAL_SHARED": "This person’s passkey speaks for a credential that other people in this estate also hold, so there is no credential of their own to seat, and seating the one they hold would seat everyone who holds it. Nothing was changed. Invite this person again to give them their own; their seat completes itself when they bind their passkey.",
    # the default sentence only (Spec 92); every raise composes its own through payee_is_venue_contract_sentence, naming the venue and the chain
    "PAYEE_IS_VENUE_CONTRACT": "This address is the contract of a known trading venue. Your charter says a payee must be a wallet held by a person or a company. Nothing was saved.",
    # Spec 98 (refusals.ts): the base sentence; the road that meets the refusal appends the gateway's own words to it
    "WALLET_BIRTH_REFUSED": "The signing gateway would not allocate a key for this estate’s funding wallet, so the estate still has none. Nothing was written.",
    "FUNDING_WALLET_ALREADY_BORN": "This estate already holds its funding wallet. A key is allocated once for an estate; nothing was changed.",
    "GATEWAY_UNAVAILABLE": "The signing service could not be reached. Nothing was signed.",
    "GAS_SHORTFALL": "The funding account does not hold enough of the chain’s native asset to cover the network fees for this run.",
    # Spec 99 (refusals.ts): the default sentences; every raise of the first composes its own through not_on_change_roster_sentence
    "CHANGE_SIGNER_NOT_ON_ROSTER": "Changing these rules is signed by the people your charter names for it, and that list is not the same list as the one that releases a payment. Your signature was not recorded.",
    "ROSTER_CHANGE_UNKNOWN": "No roster change with this id is held for this estate: the access platform lists none, or this estate did not propose it and cannot say what it changes. Nothing was signed.",
    "CHANGE_GOVERNANCE_UNREADABLE": "How many must agree to this change, and who may sign it, could not be read from your estate’s change governance — so it was not guessed at. Nothing was opened, signed or applied.",
    # Spec 97 (refusals.ts): the default sentence; every raise composes its own through platform_refused_sentence
    "PLATFORM_REFUSED": "The access platform did not carry out this request, so nothing was changed. Its own status and words are below.",
    "ROSTER_SEAT_NOT_REBOUND": "The access platform would not move this person’s roster seat to their new credential, so the seat stays bound to the credential it held. Nothing was marked rebound. The platform’s own words are below.",
    # Spec 104: every raise composes its own — "This payment could not be priced: <the platform's sentence>." — these stand where none was composed
    "PAYMENT_UNPRICED": "This payment could not be priced: the access platform refused the quote. The answer will be the same until what it named is resolved.",
    "PAYMENT_PRICING_UNAVAILABLE": "This payment could not be priced: the access platform could not be asked. Nothing was sent.",
}
ESTATE_KEY_CURE = ("If you meant a different estate, sign out and choose that estate’s key when your device offers the picker — "
                   "each key is labelled with its estate’s name.")
SANDBOX_SENTENCE = ('This estate opens in the Sandbox: your transactions execute on the AEREDIUM test network, where the value carried is valueless, '
                    'and every one of them is marked with a leading "S-" on its reference. Going live is a later ceremony, performed with an AEREDIUM officer '
                    'once you and we agree the estate works.')
HELD_PAYMENT_WAITS = ("A held payment waits until an approver answers it. Only that answer ends the hold — nothing else does, and no amount of time passing will — "
                      "and whoever submitted the payment can cancel it instead.")
WALLETS_ABSENCE = "No daily close has completed yet. The Wallets view reads the record; the record begins with the first close."
NO_FUNDING_ACCOUNT = "No funding account has been set for this workspace, so network fees cannot be checked."
# Spec T13 — the funding wallet (services/fundingwallet.ts, routes/workspace.ts at 56582b8), word for word
NO_FUNDING_WALLET_SENTENCE = "This estate has no funding wallet yet; its payments cannot leave until it has one."
NO_FUNDING_WALLET_REASON = "no funding wallet"
FUNDING_WALLET_PURPOSE = "workspace.funding_wallet"
GATEWAY_SAID_ON_21_SEPTEMBER = "PermissionDenied: not authorized"  # the gateway's words in the 23:44 run's receipt
WALLET_BIRTH_REFUSED_ON_21_SEPTEMBER = (MESSAGES["WALLET_BIRTH_REFUSED"] + " It refused this estate’s credential. The gateway said: “%s”. "
                                        "The answer will be the same until what it named is resolved." % GATEWAY_SAID_ON_21_SEPTEMBER)
GATEWAY_NOT_CONFIGURED = ("This deployment has no signing gateway configured, so no key can be allocated and the estate’s funding wallet cannot be born. "
                          "Nothing was written.")
ALREADY_BORN_CAUSE = "this estate already carries a custody key; a key is allocated once"
# The gas pre-flight (setgates.ts gasPreflight → chains.ts estimateTransfer → wrapRpc): the RPC's own words for an ERC-20 transfer the wallet
# cannot cover travel as the cause, err.message[:200]; the reason string is the token contract's, and this is the common one.
ESTIMATE_REVERTED = 'execution reverted: "ERC20: transfer amount exceeds balance"'
FAUCET_HOST = urllib.parse.urlparse(T.FAUCET_REQUEST_URL).netloc
RPC_HOST = urllib.parse.urlparse(T.TESTNET_RPC_URL).netloc
# Spec T15 — the platform's pending-transaction roads as the estate's own double models them (apps/server/src/test/aapDouble.ts), and the
# whitelist road's answer to a press the platform no longer needs (services/payees.ts, approvalPlatformRefusal), word for word
PLATFORM_NOT_AUTHORIZED_SENTENCE = "not authorized"  # `validateMultisigSigner` returns ErrNotAuthorized unwrapped: the body a live client saw on 31 August 2026
PLATFORM_EXPIRED = "conflict: pending transaction expired"  # read off expires_at; the platform sweeps nothing to the word `expired`
PLATFORM_NOT_PENDING = "conflict: pending transaction is %s"  # a signature on a ceremony already approved or consumed
PLATFORM_ENTRY_ALREADY = "entry is already %s"  # the whitelist approve on an entry no longer pending
PENDING_TX_TTL_SECONDS = 24 * 60 * 60  # the platform's default ceremony lifetime (defaultPendingTxTTL)
CHANGE_ROSTER_ID = "ms-multisig-mutation-harness"  # the census the compiler writes for C12C's family (governanceSignersFor), at C12's count
WHITELIST_ROSTER_ID = "ms-whitelist-mutation-harness"
SIGNATURES_ROAD = "POST /v1/pending-transactions-v2/{id}/signatures"  # the platform road a roster change is signed on (aapclient.ts)
NOT_ON_ROSTER_CAUSE = ("a change of who the approvers are is signed by the active signers of the roster the access platform collects this ceremony on — "
                       "the census your charter wrote (A8), at C12C’s count — and this credential is not one of them, by credential or by any address this "
                       "estate attributes to it. Nothing was signed.")
STEPUP_MAX_AGE_MS = 120 * 1000
KNOWN_CHAINS = ("ethereum", "polygon", "arbitrum", "optimism", "base", "avalanche", "bsc", "solana", "anvil")
KNOWN_ASSETS = ("AERX", "AVAX", "BNB", "DAI", "ETH", "MATIC", "POL", "SOL", "USDC", "USDT", "WBTC", "WETH")
STANDING_WORDS = {"author": "an author", "approver": "an approver", "viewer": "a viewer"}


def spoken_standings(held: Sequence[str]) -> str:
    spoken = [STANDING_WORDS.get(h, h) for h in held]
    if not spoken:
        return "somebody with no standing at all"
    if len(spoken) == 1:
        return spoken[0]
    return "%s and %s" % (", ".join(spoken[:-1]), spoken[-1])


def role_not_granted_sentence(workspace: str, held: Sequence[str], required: Optional[str], because: Optional[str] = None) -> str:
    parts = ["You are signed into %s as %s." % (workspace, spoken_standings(held))]
    if required is not None:
        parts.append("This action needs %s — permissions come from your organisation’s policy, not from this application." % STANDING_WORDS.get(required, required))
    if because:
        parts.append(because)
    parts.append(ESTATE_KEY_CURE)
    return " ".join(parts)


class Refusal(Exception):
    def __init__(self, code: str, message: Optional[str] = None, detail: Optional[Dict[str, Any]] = None, **extra: Any):
        super().__init__(code)
        self.code = code
        self.message = message or MESSAGES[code]
        self.detail = detail
        self.extra = extra

    def body(self) -> Dict[str, Any]:
        error: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.detail:
            error["detail"] = self.detail
        error.update(self.extra)
        return {"error": error}


class Malformed(Exception):
    """A zod rejection: a malformed request, relayed as REQUEST_MALFORMED with the issues."""

    def __init__(self, issue: str):
        super().__init__(issue)
        self.issue = issue


def load_v11_prompts() -> Dict[str, Dict[str, str]]:
    """id → {part, kind, prompt} from the frozen v11 catalog, so the double serves the shipped prompts."""
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        text = handle.read()
    out: Dict[str, Dict[str, str]] = {}
    for match in re.finditer(r'questionId: "([A-Z0-9]+)",\s*part: "([^"]*)",\s*kind: "([^"]*)",\s*prompt: "((?:[^"\\]|\\.)*)"', text):
        out[match.group(1)] = {"part": match.group(2), "kind": match.group(3), "prompt": match.group(4).replace('\\"', '"')}
    return out


V11 = load_v11_prompts()
SERVED_FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "aer360-served-2026-09-21.json")


def load_v14_added() -> Dict[str, Dict[str, Any]]:
    """
    id → {part, kind, prompt, options, listFields, note, written} for the seven questions catalog version 14 added (Spec 92), from the
    fixture of the pages the estate served on 21 September 2026 and the catalog's own words for the five the run never reached.
    """
    with open(SERVED_FIXTURE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    out: Dict[str, Dict[str, Any]] = {}
    for questions in data["added"].values():
        for q in questions:
            out[q["questionId"]] = q
    return out


V14_ADDED = load_v14_added()
PROMPTS: Dict[str, Dict[str, Any]] = dict(V11)
PROMPTS.update(V14_ADDED)
LEVELS_BENEATH = set(A.LEVELS_BENEATH)
# packages/shared/src/venues.ts (Spec 92): the engine's closed venue table, row for row and in its order, and the venues' published names.
VENUE_CONTRACTS = (
    ("uniswap_v3", "ethereum", "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"),
    ("uniswap_v3", "arbitrum", "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"),
    ("uniswap_v3", "base", "0x2626664c2603336E57B271c5C0b26F421741e481"),
    ("pancakeswap_v3", "ethereum", "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4"),
    ("pancakeswap_v3", "arbitrum", "0x32226588378236Fd0c7c4053999F88aC0e5cAc77"),
    ("pancakeswap_v3", "base", "0x678Aa4bF4E210cf2166753e054d5b7c31cc7fa86"),
)
VENUE_NAMES = {"uniswap_v3": "Uniswap v3", "pancakeswap_v3": "PancakeSwap v3"}
VENUE_CONTRACT_QUESTION_ID = "C19"  # services/payees.ts


def venue_of_destination(chain: str, destination: str) -> str:
    """`venueOfDestination`: the venue id when the destination is a known venue contract on its chain, else the empty string."""
    if not destination.strip():
        return ""
    for venue, row_chain, address in VENUE_CONTRACTS:
        if row_chain.strip().lower() == chain.strip().lower() and address.lower() == destination.strip().lower():
            return venue
    return ""


def payee_is_venue_contract_sentence(venue_name: str, chain: str, question_id: str = VENUE_CONTRACT_QUESTION_ID) -> str:
    """`payeeIsVenueContractSentence` (packages/shared/src/refusals.ts), word for word."""
    return ("This address is the contract of %s on %s. Your charter says a payee must be a wallet held by a person or a company "
            "(question %s). Nothing was saved." % (venue_name, chain, question_id))


# The signing tiers' sentences (packages/shared/src/refusals.ts; services/onboardingcompiler.ts), word for word.
TIER_TWO_NOT_ABOVE_ONE = "The figure for two signatures must be above the figure for one; as written, two signatures would never be asked."
TIER_HOLD_NOT_WRITTEN = ("Under this wallet’s signing tiers this figure is RECORDED and NOT written as a hold: a payment above the figure the holder "
                         "may pay alone waits for its second or third signature instead, and those signatures are the approval.")
TIER_QUORUM_STANDS_ASIDE = ("Under this wallet’s signing tiers, how many signatures a payment needs is decided by the two figures below — one up to the "
                            "first, two up to the second, three above it. This number sizes the roster that approves a new payee for this account, and "
                            "AER 360’s own approval inbox for a payment a clerk enters.")
TIERS_FROM_CATALOG_VERSION = 14  # questioncatalog.ts TIERS_FROM_CATALOG_VERSION


def tiers_need_three_people(figure: str, named: int) -> str:
    """`tiersNeedThreePeople`: the figure WO4 names and how many distinct people WA1 and WO2 name between them."""
    return "Three signatures are asked above %s but only %d %s named; name more or lower the tiers." % (figure, named, "person is" if named == 1 else "people are")


def usd_figure(cents: Any) -> str:
    """`usdFigure`: a figure in cents spoken the way the read-back speaks one — US$50,000 and 00 cents."""
    whole, frac = divmod(int(cents), 100)
    return "US$%s and %02d cents" % ("{:,}".format(whole), frac)


def holder_title_for(purpose: Optional[str]) -> str:
    """`holderTitleFor`: the Principal of a customer's account, the Officer of every other wallet."""
    return "Principal" if purpose == A.CUSTOMER else "Officer"
VENUE_STIPULATION = "This estate’s questionnaire stipulates that a venue contract is not a payee, so this address was not saved. Nothing was changed."
# What the platform says to a signature it will not count (apps/server/src/test/aapDouble.ts: "`validateMultisigSigner`
# returns `ErrNotAuthorized` unwrapped, and 'not authorized' is exactly the body a live client saw on 31 August 2026").
PLATFORM_NOT_AUTHORIZED = "not authorized"
A_PAYEE_ADDRESS = "a payee address onto the approved list"  # services/payees.ts: what the approve road is deciding about


def approver_seat_shared_sentence(name: str, shared_with: Sequence[str]) -> str:
    """`approverSeatSharedSentence` (packages/shared/src/enrolment.ts, Spec 91, item 2), word for word: the seat law with the names in it."""
    return ("%s shares a credential with %s, so there is no credential of their own to seat, and seating the one they hold would seat everyone who "
            "holds it. Nothing was changed. Invite %s again to give them their own; their seat completes itself when they bind their passkey." % (
                name, H.names_in_words(shared_with), name))


def spelled(n: int) -> str:
    """Small counts as words, the way the estate's sentence speaks them (services/payees.ts, `spelled`)."""
    return ["No", "One", "Two", "Three", "Four", "Five"][n] if 0 <= n <= 5 else str(n)


def names_joined(names: Sequence[str], last_joiner: str = "and") -> str:
    """`namesJoined` (services/onboardingcompiler.ts): "A, B or C"."""
    if len(names) <= 1:
        return names[0] if names else ""
    return "%s %s %s" % (", ".join(names[:-1]), last_joiner, names[-1])


def pending_approval_sentence(required: int, collected: int, may_still_approve: Sequence[str], members: Sequence[str]) -> str:
    """
    `pendingApprovalSentence` (services/payees.ts, Spec 89, count 1), word for word, for a roster the platform did read and
    whose every signature was pressed here (so nothing is "not pressed here"): the count, who is still needed, and that the
    address is not payable until then; where the count is met, that the platform has not yet activated the address; where
    nobody is left to sign, that the count can never be met as the roster stands.
    """
    remaining = max(required - collected, 0)
    recorded = "%d of %d %s recorded for this address." % (collected, required, "approval" if required == 1 else "approvals")
    if remaining == 0:
        return recorded + " The count is met and the access platform has not yet activated the address. It is not payable until it does."
    needed = "%s more %s needed" % (spelled(remaining), "is" if remaining == 1 else "are")
    if not may_still_approve:
        who = ("the roster that approves it has nobody on it" if not members
               else "everyone on the roster that approves it (%s) has already approved" % names_joined(list(members)))
        return "%s %s, but %s: as the roster stands, the count can never be met. The address is not payable as the roster stands." % (recorded, needed, who)
    return "%s %s, from %s. The address is not payable until then." % (recorded, needed, names_joined(list(may_still_approve), "or"))


def people_in_words(names: Sequence[str]) -> str:
    """`peopleInWords` (refusals.ts) and `namesInWords` (enrolment.ts): "A", "A and B", "A, B and C"."""
    spoken = [str(n) for n in names]
    if len(spoken) <= 1:
        return spoken[0] if spoken else ""
    return "%s and %s" % (", ".join(spoken[:-1]), spoken[-1])


def not_on_change_roster_sentence(names: Sequence[str]) -> str:
    """`notOnChangeRosterSentence` (refusals.ts, Spec 99), word for word."""
    who = people_in_words(names) if names else "nobody the roster currently names"
    return "A change of who the approvers are is signed by %s; you are not among them. Nothing was signed." % who


def platform_outcome(status: int) -> str:
    """`platformOutcome` (refusals.ts, Spec 97)."""
    if status >= 500:
        return "failed"
    if status in (400, 422):
        return "malformed"
    if status >= 400:
        return "refused"
    return "answered"


def platform_refused_sentence(status: int, said: str) -> str:
    """`platformRefusedSentence` (refusals.ts, Spec 97), word for word: what the platform did, and its own words in quotation marks."""
    quoted = (": “%s”" % said) if said else ""
    http = "HTTP %d" % status
    outcome = platform_outcome(status)
    if outcome == "refused":
        return ("The access platform refused this request (%s)%s. Nothing was changed, and asking again will meet the same answer until what the "
                "platform names has changed." % (http, quoted))
    if outcome == "malformed":
        return "The access platform would not accept the request this estate sent it (%s)%s. That is a fault in this estate’s request, not in yours; nothing was changed." % (http, quoted)
    if outcome == "failed":
        return "The access platform was reached and could not carry out this request (%s)%s. Nothing was changed; it may answer differently in a moment." % (http, quoted)
    return "The access platform answered this request (%s) in a shape this estate will not act on%s. Nothing was changed." % (http, quoted)


def roster_seat_awaiting_sentence(person: str, roster: str, pending_tx_id: str, required: int, collected: int) -> str:
    """`rosterSeatAwaitingSentence` (refusals.ts, Spec 95), word for word."""
    return ("%s’s seat on the roster “%s” was not moved yet: your charter asks %d %s to agree to a change of who the approvers are (C12C), and the "
            "access platform holds that change as ceremony %s at %d of %d. The seat stays bound to the credential it held until they agree." % (
                person, roster, required, "person" if required == 1 else "people", pending_tx_id, collected, required))


def time_of_day(epoch: float) -> str:
    """`timeOfDay` (packages/shared/src/when.ts): "5:47pm", in local time."""
    local = time.localtime(epoch)
    twelve = 12 if local.tm_hour % 12 == 0 else local.tm_hour % 12
    return "%d:%02d%s" % (twelve, local.tm_min, "am" if local.tm_hour < 12 else "pm")


def when_in_words(iso: str, now: float) -> str:
    """`whenInWords` (packages/shared/src/when.ts): today or tomorrow at a time, a weekday within the week, else the date."""
    if not iso:
        return "—"
    try:
        when = time.mktime(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone if iso.endswith("Z") else time.mktime(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return iso
    a = time.localtime(now)
    b = time.localtime(when)
    days = round((time.mktime((b.tm_year, b.tm_mon, b.tm_mday, 0, 0, 0, 0, 0, -1)) - time.mktime((a.tm_year, a.tm_mon, a.tm_mday, 0, 0, 0, 0, 0, -1))) / 86400)
    clock = time_of_day(when)
    if days == 0:
        return "today at %s" % clock
    if days == 1:
        return "tomorrow at %s" % clock
    if 1 < days < 7:
        return "%s at %s" % (time.strftime("%A", b), clock)
    return "%s %d, %d at %s" % (time.strftime("%b", b), b.tm_mday, b.tm_year, clock)


def roster_change_sentence(facts: Dict[str, Any], now: float) -> str:
    """`rosterChangeSentence` (enrolment.ts, Spec 99), word for word: the line under the person's row, one per ceremony."""
    names = [s["name"] for s in facts.get("signedBy") or []]
    count = "%s of %s approvers have signed%s." % (facts.get("signaturesCollected"), facts.get("requiredSignatures"), (" (%s)" % people_in_words(names)) if names else "")
    seat = facts.get("seat")
    if not facts.get("proposedHere") or seat is None:
        return ("A roster change this estate did not propose: the access platform holds ceremony %s… on “%s” as %s, %s This estate cannot say what it "
                "changes, so it offers no press for it here." % (T.credential_short_form(facts.get("pendingTxId")), facts.get("signingRosterName") or "a roster it no longer lists",
                                                                  facts.get("platformStatus"), count))
    who = (seat.get("name") or "").strip() or seat.get("email")
    moving = "Moving %s’s seat to their current passkey" % who
    state = facts.get("state")
    may_sign = facts.get("maySign") or []
    afresh = "Granting %s’s seat again in this room, or %s redeeming a fresh invitation, proposes the move afresh." % (who, who)
    if state == "awaiting":
        return "%s: %s%s" % (moving, count, (" %s may sign." % people_in_words(may_sign)) if may_sign else "")
    if state == "approved":
        return ("%s: %s The access platform holds the change as %s and has not applied it: a governed change is applied only when it is presented to "
                "the platform again with the same content. Granting %s’s seat again in this room, or %s redeeming a fresh invitation, presents it, and the "
                "platform applies it with these signatures." % (moving, count, facts.get("platformStatus"), who, who))
    if state == "applied":
        return "%s’s seat was moved to their current passkey: %s The access platform applied the change, and their presses now count." % (who, count.replace("have signed", "signed"))
    if state == "expired":
        expires = facts.get("expiresAt")
        return ("%s expired at the access platform before the count was met: %s The platform holds it as %s%s, and nothing can be signed on it now. %s" % (
            moving, count, facts.get("platformStatus"), (", expiring %s" % when_in_words(expires, now)) if expires else "", afresh))
    return "%s: the access platform holds the change as %s, so nothing can be signed on it. %s" % (moving, facts.get("platformStatus"), afresh)


def roster_change_signed_sentence(view: Dict[str, Any], held_because: str = "") -> str:
    """`rosterChangeSignedSentence` (enrolment.ts, Spec 99), word for word: what the hand that signed is told."""
    names = [s["name"] for s in view.get("signedBy") or []]
    count = "%s of %s approvers have signed%s." % (view.get("signaturesCollected"), view.get("requiredSignatures"), (" (%s)" % people_in_words(names)) if names else "")
    state = view.get("state")
    if state == "awaiting":
        may_sign = view.get("maySign") or []
        return "Your signature is counted: %s%s" % (count, (" %s may still sign." % people_in_words(may_sign)) if may_sign else "")
    if state == "applied":
        rebound = view.get("rebound") or {}
        who = ((rebound.get("name") or "").strip() or rebound.get("email")) if rebound else "the person"
        roster = (" on “%s”" % rebound.get("rosterName")) if rebound else ""
        return "Your signature completed the count: %s The access platform applied the change, and %s’s seat%s now counts their current passkey." % (count, who, roster)
    reopened = view.get("reopened")
    if reopened:
        return ("Your signature completed the count: %s Presenting the change to the access platform again opened a fresh ceremony %s… at %s of %s: the roster has "
                "changed since the move was proposed, so the signatures given were for a change that no longer matches it. The move stands proposed afresh, and the "
                "seat stays where it was until it is signed again." % (count, T.credential_short_form(reopened.get("pendingTxId")), reopened.get("signaturesCollected"), reopened.get("requiredSignatures")))
    return "Your signature completed the count: %s The access platform holds the change approved and did not apply it%s. The seat stays where it was." % (
        count, (": %s" % held_because) if held_because else "")


class Clock:
    """Time that moves only when somebody sleeps on it, so a four-second invitation costs the suite nothing."""

    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


class FaucetDouble:
    """
    THE FAUCET AS ITS OWN CODE ANSWERS (aeredium/faucet, internal/faucet/server_manual.go — handleRequest and autoPayRequest, the
    auto-pay mode the cabinet's record names): POST {"address": "0x…"} → 200 {"ok": true, "paid": true, "tx_hash", "times_requested",
    "times_paid"}; a send that failed → 200 {"ok": true, "queued": true, …} and the row waits for the admin queue; over a window limit
    → 429 {"ok": false, "error": <the handler's sentence>}; a request already waiting → 409; a malformed body or address → 400. Every
    sentence below is the handler's own. `down` is a faucet that cannot be reached; `malformed_answer` a proxy answering HTML.
    """

    PAID, QUEUED, WALLET_LIMIT, IP_LIMIT, BUDGET, WAITING, DOWN, MALFORMED_ANSWER = "paid", "queued", "wallet_limit", "ip_limit", "budget", "waiting", "down", "malformed_answer"
    SENTENCES = {
        WALLET_LIMIT: (429, "this wallet has already received 4 payments in the last 24 hours — try again tomorrow"),
        IP_LIMIT: (429, "too many payments from this network today — try again tomorrow"),
        BUDGET: (429, "the faucet has reached its daily budget — try again tomorrow"),
        WAITING: (409, "this address already has a request waiting — it will be reviewed shortly"),
    }

    def __init__(self, answer: str = PAID, times_paid: int = 0):
        self.answer = answer
        self.times_paid = times_paid
        self.tx_hash = "0x" + secrets.token_hex(32)
        self.requests: List[Dict[str, Any]] = []

    def __call__(self, request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
        method = request.get_method()
        headers = {k.lower(): v for k, v in request.header_items()}
        body: Any = None
        malformed = False
        if request.data:
            try:
                body = json.loads(request.data.decode("utf-8"))
            except ValueError:
                malformed = True
        self.requests.append({"method": method, "path": urllib.parse.urlparse(request.full_url).path, "body": body, "headers": headers})
        if self.answer == self.DOWN:
            raise H.Unreachable("%s %s could not be reached: [Errno 61] Connection refused" % (method, request.full_url))
        if method != "POST":
            return self._json(405, {"ok": False, "error": "POST only"})
        if malformed or not isinstance(body, dict):
            return self._json(400, {"ok": False, "error": "invalid JSON body"})
        address = str(body.get("address", "")).strip()
        if not re.match(r"^0x[0-9a-fA-F]{40}$", address):
            return self._json(400, {"ok": False, "error": "that does not look like a valid address (0x + 40 hex characters)"})
        if self.answer == self.MALFORMED_ANSWER:
            return 502, [("Content-Type", "text/html")], "<html><head><title>502 Bad Gateway</title></head><body>nginx</body></html>"
        requested = len([r for r in self.requests if (r["body"] or {}).get("address") == body.get("address")])
        if self.answer == self.PAID:
            return self._json(200, {"ok": True, "paid": True, "tx_hash": self.tx_hash, "times_requested": requested, "times_paid": self.times_paid + 1})
        if self.answer == self.QUEUED:
            return self._json(200, {"ok": True, "queued": True, "times_requested": requested, "times_paid": self.times_paid})
        status, sentence = self.SENTENCES[self.answer]
        return self._json(status, {"ok": False, "error": sentence})

    @staticmethod
    def _json(status: int, payload: Any) -> Tuple[int, List[Tuple[str, str]], str]:
        return status, [("Content-Type", "application/json")], json.dumps(payload)


class TestnetRpcDouble:
    """
    THE CHAIN'S PUBLIC RPC, reads only: eth_getBalance answers the balance this double is told, as the hex quantity a node
    answers; eth_chainId answers 0x8bd (2237). `fault` is "down" (not reachable), "error" (a JSON-RPC error object), or
    "not_json" (a proxy's HTML) — each a road the harness must report and never read a balance from.
    """

    def __init__(self, balance_wei: int = 0, fault: Optional[str] = None):
        self.balance_wei = balance_wei
        self.fault = fault
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
        body = json.loads(request.data.decode("utf-8")) if request.data else {}
        self.calls.append({"method": request.get_method(), "body": body})
        if self.fault == "down":
            raise H.Unreachable("%s %s could not be reached: [Errno 8] nodename nor servname provided, or not known" % (request.get_method(), request.full_url))
        if self.fault == "not_json":
            return 502, [("Content-Type", "text/html")], "<html><body>502 Bad Gateway</body></html>"
        rpc_id = body.get("id")
        if self.fault == "error":
            return 200, [("Content-Type", "application/json")], json.dumps({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": "header not found"}})
        method = body.get("method")
        if method == "eth_getBalance":
            result = hex(self.balance_wei)
        elif method == "eth_chainId":
            result = hex(T.TESTNET_CHAIN_ID)
        else:
            return 200, [("Content-Type", "application/json")], json.dumps({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "the method %s does not exist/is not available" % method}})
        return 200, [("Content-Type", "application/json")], json.dumps({"jsonrpc": "2.0", "id": rpc_id, "result": result})


# ---------------------------------------------------------------------------
# THE ACCESS PLATFORM'S GAS LEDGER AND THE PAYMENT CHAIN'S USDC (Spec T14), each as its own code answers.
# ---------------------------------------------------------------------------
PLATFORM_BASE = "https://platform.test"  # the access platform's base URL the tests file in admin.env (AAP_ADMIN_BASE_URL)
PLATFORM_HOST = urllib.parse.urlparse(PLATFORM_BASE).netloc
PUBLIC_RPC_HOST = urllib.parse.urlparse(T.public_rpc_url(T.PAYEE_CHAIN) or "https://rpc.invalid").netloc
TREASURY_ACCOUNT_ID = "aap-account-treasury"
TREASURY_WORKSPACE_ID = "ws-treasury"
QUOTE_CEILING_USD_CENTS = 40  # the ceiling one dry quote reserves in this double, so a set of three needs at most US$1.20, as Spec 104's own test has it
ACTUAL_GAS_USD_CENTS = 31  # the debit the platform takes when an operation lands, at actual cost (Spec 154 §4)
# The platform's own sentences (internal/api/middleware.go adminAuth; gas_handlers.go PostAdminGasAccountCredit; internal/gas/credit.go; internal/identity/errors.go), word for word.
PLATFORM_ADMIN_MISSING = "missing or malformed Authorization header"
PLATFORM_ADMIN_FORMAT = "invalid admin key format"
PLATFORM_ADMIN_INVALID = "invalid admin key"
PLATFORM_REASON_REQUIRED = "reason is required on an admin credit: the road exists for the sandbox and for goodwill, and the row says which"
PLATFORM_AMOUNT_NOT_POSITIVE = "amount_usd_cents must be a positive whole number of cents, got %d"
PLATFORM_ACCOUNT_NOT_FOUND = "identity: not found"
PLATFORM_BELOW_MINIMUM = "%s was credited; the minimum top-up is %s, and a top-up below it is accepted and recorded as it came"
PLATFORM_INSUFFICIENT_GAS = "Your gas account holds %s. This %s needs at most %s of gas. Nothing was sent. Top up %s or more."  # test/gasRoadsDouble.ts insufficientGasSentence, the platform's per-operation sentence
# The chain's refusal of a transfer the key cannot cover, as the token contract words it and the platform relays it (the sentence the live run of 23 September met).
ESTIMATE_REVERTED_SAID = "the chain refused the dry run of the operation: %s" % ESTIMATE_REVERTED  # the platform's quote road, refusing in the chain's words
ESTIMATE_REVERTED_CLAUSE = "the access platform said: “%s”" % ESTIMATE_REVERTED_SAID  # GasRoadError.clause() for a refusal (services/accountabstraction.ts)
GAS_LOW_SENTENCE = ("Your gas account is low: the access platform says it holds less than the cost of two typical operations. Buy gas below; a payment the balance cannot "
                    "cover is refused before anything is sent.")  # services/accountabstraction.ts GAS_LOW_SENTENCE
BUYING_GAS_NOT_OPEN = "buying gas is not open on this estate yet"  # accountabstraction.ts BUYING_GAS_NOT_OPEN
AFTER_CHECKOUT_SENTENCES = {"bought": "Your card payment is with the payment desk. The gas account updates when the desk confirms it; this page reads the balance live.",
                            "cancelled": "The card payment was cancelled at the payment desk. Nothing was charged."}  # routes/gas.ts


def us_dollars(cents: int) -> str:
    """`usDollars` (services/fundingwallet.ts): US$1,234.56 from cents, grouped, by integer arithmetic."""
    negative = cents < 0
    n = -cents if negative else cents
    return "%sUS$%s.%02d" % ("-" if negative else "", "{:,}".format(n // 100), n % 100)


class PlatformDouble:
    """
    THE ACCESS PLATFORM'S GAS LEDGER AND ITS ADMIN CREDIT ROAD, as Spec 154 and 154b built them (aegiskey-access-platform: internal/gas/ledger.go —
    one line per credit, reservation or debit, in USD cents, with a unique idempotency key; internal/gas/credit.go — a repeated key answers the line
    that stands, `deduped`; internal/api/gas_handlers.go PostAdminGasAccountCredit — the admin key, `reason` required, 201 with the line and the
    balance, 200 deduped; internal/api/middleware.go adminAuth — a bearer missing, malformed or wrong is 401 in three sentences; response.go writeError
    — every refusal is {"error": <sentence>}). The estate doubles read and move this ledger in process, as the estate reads the platform's roads;
    the harness reaches only the admin credit road, over HTTP, with the credential admin.env names. `down` is a platform that cannot be reached;
    `debit_gap_cents` a ledger that debits more than the trail says, for S10's one-cent finding.
    """

    def __init__(self, admin_key: Optional[str] = None, down: bool = False, debit_gap_cents: int = 0):
        self.admin_key = admin_key or (T.ADMIN_KEY_PREFIX + secrets.token_hex(16))
        self.down = down
        self.debit_gap_cents = debit_gap_cents
        self.accounts: Set[str] = set()
        self.lines: List[Dict[str, Any]] = []
        self.requests: List[Dict[str, Any]] = []
        self.audit: List[Dict[str, Any]] = []

    # -- the ledger (ledger.go) ----------------------------------------------------------------------------------------
    def balance(self, account_id: str) -> Dict[str, int]:
        mine = [l for l in self.lines if l["account_id"] == account_id]
        credits = sum(l["amount_usd_cents"] for l in mine if l["kind"] == "credit")
        debits = sum(l["amount_usd_cents"] for l in mine if l["kind"] == "debit")
        reserved = sum(l["amount_usd_cents"] for l in mine if l["kind"] == "reservation" and l.get("released_at") is None)
        return {"balance_usd_cents": credits - debits, "reserved_usd_cents": reserved, "available_usd_cents": credits - debits - reserved}

    def debits_of(self, account_id: str) -> List[int]:
        return [l["amount_usd_cents"] for l in self.lines if l["account_id"] == account_id and l["kind"] == "debit"]

    def low(self, account_id: str) -> bool:
        """Spec 154 §2: below twice the median actual cost of the account's last ten operations, or US$1.00 where there are none."""
        recent = self.debits_of(account_id)[-10:]
        if not recent:
            figure = 100
        else:
            ordered = sorted(recent)
            middle = len(ordered) // 2
            median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) // 2
            figure = 2 * median
        return self.balance(account_id)["balance_usd_cents"] < figure

    def _line(self, account_id: str, kind: str, cents: int, key: str, **extra: Any) -> Dict[str, Any]:
        line = {"id": str(uuid.uuid4()), "account_id": account_id, "kind": kind, "amount_usd_cents": cents, "amount": T.format_usd_cents(cents),
                "idempotency_key": key, "created_at": EstateDouble._now_iso()}
        line.update(extra)
        self.lines.append(line)
        return line

    def credit(self, account_id: str, cents: int, key: str, reason: str, source: str, actor: str) -> Tuple[Dict[str, Any], bool]:
        existing = next((l for l in self.lines if l["idempotency_key"] == key), None)
        if existing is not None:
            return existing, False
        return self._line(account_id, "credit", cents, key, actor=actor, source=source, reason=reason, words="credit, %s, %s" % (T.format_usd_cents(cents), reason)), True

    def reserve(self, account_id: str, cents: int, key: str, chain: str, words: str) -> Dict[str, Any]:
        return self._line(account_id, "reservation", cents, key, chain=chain, words=words, released_at=None)

    def release(self, key: str) -> None:
        for line in self.lines:
            if line["kind"] == "reservation" and line["idempotency_key"] == key and line.get("released_at") is None:
                line["released_at"] = EstateDouble._now_iso()

    def debit(self, account_id: str, cents: int, key: str, chain: str, user_op_hash: str, tx_hash: str) -> Dict[str, Any]:
        return self._line(account_id, "debit", cents, key, chain=chain, user_op_hash=user_op_hash, transaction_hash=tx_hash, words=T.gas_debit_words(cents))

    # -- the admin credit road (gas_handlers.go, middleware.go) ------------------------------------------------------------
    def __call__(self, request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
        method = request.get_method()
        url = urllib.parse.urlparse(request.full_url)
        headers = {k.lower(): v for k, v in request.header_items()}
        raw_body = request.data.decode("utf-8") if request.data else ""
        self.requests.append({"method": method, "path": url.path, "headers": headers, "body": raw_body})
        if self.down:
            raise H.Unreachable("%s %s could not be reached: [Errno 61] Connection refused" % (method, request.full_url))
        m = re.match(r"^/v1/admin/accounts/([^/]+)/gas-account/credits$", url.path)
        if not m or method != "POST":
            return self._json(404, {"error": "not found"})
        authorization = headers.get("authorization", "")
        if not authorization.startswith("Bearer ") or not authorization[len("Bearer "):].strip():
            return self._json(401, {"error": PLATFORM_ADMIN_MISSING})
        bearer = authorization[len("Bearer "):].strip()
        if not bearer.startswith(T.ADMIN_KEY_PREFIX):
            return self._json(401, {"error": PLATFORM_ADMIN_FORMAT})
        if bearer != self.admin_key:
            return self._json(401, {"error": PLATFORM_ADMIN_INVALID})
        account_id = m.group(1)
        if account_id not in self.accounts:
            return self._json(404, {"error": PLATFORM_ACCOUNT_NOT_FOUND})
        try:
            body = json.loads(raw_body) if raw_body else {}
        except ValueError as err:
            return self._json(400, {"error": str(err)})
        if not isinstance(body, dict):
            return self._json(400, {"error": "json: cannot unmarshal into Go value of type api.gasCreditBody"})
        unknown = [k for k in body if k not in ("account_id", "amount_usd_cents", "stripe_event_id", "idempotency_key", "reason", "reference")]
        if unknown:
            return self._json(400, {"error": 'json: unknown field "%s"' % unknown[0]})
        reason = str(body.get("reason") or "").strip()
        if not reason:
            return self._json(400, {"error": PLATFORM_REASON_REQUIRED})
        amount = body.get("amount_usd_cents")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            return self._json(400, {"error": PLATFORM_AMOUNT_NOT_POSITIVE % (amount if isinstance(amount, int) else 0), "code": "validation"})
        key = str(body.get("idempotency_key") or "").strip() or ("admin:" + str(uuid.uuid4()))
        line, created = self.credit(account_id, amount, key, reason, "admin", "admin:bearer")
        answer: Dict[str, Any] = {"line": line, "deduped": not created, "below_minimum": line["amount_usd_cents"] < T.GAS_CREDIT_USD_CENTS,
                                  "minimum_top_up_usd_cents": T.GAS_CREDIT_USD_CENTS, "balance": self.balance(account_id)}
        if answer["below_minimum"]:
            answer["note"] = PLATFORM_BELOW_MINIMUM % (T.format_usd_cents(line["amount_usd_cents"]), T.format_usd_cents(T.GAS_CREDIT_USD_CENTS))
        self.audit.append({"type": "gas.credited_by_admin", "result": "success", "account_id": account_id, "outcome": "deduped" if not created else "credited",
                           "amount_usd_cents": line["amount_usd_cents"], "reason": reason, "idempotency_key": line["idempotency_key"]})
        return self._json(200 if not created else 201, answer)

    @staticmethod
    def _json(status: int, payload: Any) -> Tuple[int, List[Tuple[str, str]], str]:
        return status, [("Content-Type", "application/json")], json.dumps(payload)


class UsdcChainDouble:
    """
    THE PAYMENT CHAIN'S USDC, as the estate reads it and the harness reads it: the token contract the estate names on the chain (a derived test
    address, never a real one), every holder's balance in minor units, the transfers the estate's payments make, and the chain's public RPC
    answering `eth_call` balanceOf(address) as a node does — a 32-byte hex word — and `eth_chainId`. `lose_transfers` is a chain on which the
    sender is debited and the payee credited nothing: a payment whose payee's balance does not rise, which the harness must fail naming it.
    `fault` is "down" (the RPC cannot be reached) or "not_json" (a proxy answering HTML).
    """

    def __init__(self, lose_transfers: bool = False, fault: Optional[str] = None):
        self.token = T.derive_address("the estate double's %s contract/%s" % (T.PAYMENT_ASSET, T.PAYEE_CHAIN))
        self.balances: Dict[str, int] = {}
        self.transfers: List[Dict[str, Any]] = []
        self.lose_transfers = lose_transfers
        self.fault = fault
        self.calls: List[Dict[str, Any]] = []

    def balance_of(self, address: str) -> int:
        return self.balances.get(address.lower(), 0)

    def credit(self, address: str, minor: int) -> None:
        self.balances[address.lower()] = self.balance_of(address) + int(minor)

    def transfer(self, sender: str, payee: str, minor: int) -> None:
        if self.balance_of(sender) < minor:
            raise ValueError(ESTIMATE_REVERTED)
        self.balances[sender.lower()] = self.balance_of(sender) - minor
        if not self.lose_transfers:
            self.credit(payee, minor)
        self.transfers.append({"from": sender.lower(), "to": payee.lower(), "minor": minor})

    def __call__(self, request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
        body = json.loads(request.data.decode("utf-8")) if request.data else {}
        self.calls.append({"method": request.get_method(), "body": body})
        if self.fault == "down":
            raise H.Unreachable("%s %s could not be reached: [Errno 8] nodename nor servname provided, or not known" % (request.get_method(), request.full_url))
        if self.fault == "not_json":
            return 502, [("Content-Type", "text/html")], "<html><body>502 Bad Gateway</body></html>"
        rpc_id = body.get("id")
        method = body.get("method")
        if method == "eth_chainId":
            result: Any = hex(1)
        elif method == "eth_call":
            params = body.get("params") or [{}]
            call = params[0] if params and isinstance(params[0], dict) else {}
            data = str(call.get("data") or "")
            if str(call.get("to") or "").lower() != self.token.lower() or not data.lower().startswith(T.ERC20_BALANCE_OF_SELECTOR.lower()) or len(data) != 2 + 8 + 64:
                result = "0x"
            else:
                holder = "0x" + data[-40:]
                result = "0x" + ("%064x" % self.balance_of(holder))
        else:
            return 200, [("Content-Type", "application/json")], json.dumps({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "the method %s does not exist/is not available" % method}})
        return 200, [("Content-Type", "application/json")], json.dumps({"jsonrpc": "2.0", "id": rpc_id, "result": result})


class EstateDouble:
    """The estate, in memory. Strict as the code; every answer is the code's own shape."""

    def __init__(self, base: str = BASE, funding_wallet: str = "press",
                 company: str = A.ESTATE["company"], catalog_version: int = 14, currency_spoken_as_code: bool = False,
                 refuses_venue_contract: Optional[bool] = None, invite_seconds: float = 0.0, clock: Optional[Clock] = None,
                 pending_approval_says_why: bool = True, whitelist_roster: Optional[Sequence[str]] = None, platform_never_activates: bool = False,
                 before_spec_91: bool = False, seat_completes_on_redemption: bool = True, second_authorship_entry: bool = False,
                 platform_names_approver: Sequence[str] = (), mirror_lags: bool = False, register_corrects: bool = True,
                 faucet: Optional[FaucetDouble] = None, rpc: Optional[TestnetRpcDouble] = None,
                 change_roster: Optional[Sequence[str]] = None, before_spec_99: bool = False, ceremony_lapses: int = 0, account_email: Optional[str] = None,
                 lapse_after_first_signature: bool = False, seats_override: Optional[List[Dict[str, Any]]] = None,
                 platform: Optional[PlatformDouble] = None, chain: Optional[UsdcChainDouble] = None, treasury: bool = True, is_treasury: bool = False,
                 aap_account_id: Optional[str] = None, secret: Optional[bytes] = None, initial_usdc_cents: Optional[int] = None, holdings_usdc_cents: int = 0,
                 treasury_usdc_cents: int = 10000, treasury_funding_wallet: str = "born", quote_ceiling_usd_cents: int = QUOTE_CEILING_USD_CENTS,
                 actual_gas_usd_cents: int = ACTUAL_GAS_USD_CENTS, gas_refusal_names_other_figures: bool = False, review_refuses_but_pays: bool = False):
        self.currency_spoken_as_code = currency_spoken_as_code  # False: main's default arm (JSON); True: Spec 88's code
        # The payee door and a venue's contract (Spec T11). None: the door follows the written policy charter, as Spec 92 built it —
        # PAYEE_IS_VENUE_CONTRACT where the charter says refused and the address is on the venue table. True: Spec T8's stand-in, a door
        # that refuses the probe address regardless of its charter under ADDRESS_PROPOSAL_REFUSED. False: a door that saves it regardless.
        self.refuses_venue_contract = refuses_venue_contract
        self.invite_seconds = invite_seconds  # how long POST /v1/invites takes on the shared clock, the email awaited
        self.clock = clock
        # Spec T9's dials. False: the estate of 20 September 2026 before Spec 89, whose press answered only the status.
        self.pending_approval_says_why = pending_approval_says_why
        # The census keys seated on the whitelist_mutation roster; None seats the census the charter compiles (A8).
        self.whitelist_roster = tuple(whitelist_roster) if whitelist_roster is not None else None
        # True: a platform that counts every signature and never activates the address, so the count is met and nothing moves.
        self.platform_never_activates = platform_never_activates
        # Spec T10's dials. True: the estate of the four live runs, before Spec 91 — an author invitation enrols the founder's
        # credential, a redemption retires nothing, the register carries no marker, and the seat road refuses nothing for sharing.
        self.before_spec_91 = before_spec_91
        # False: an estate before Spec 58's count 3, whose redemption says nothing of a seat, so the founder must grant it.
        self.seat_completes_on_redemption = seat_completes_on_redemption
        # True: a second policy entry bearing authorship (a CFO's credential), so an author invitation is refused, listing both.
        self.second_authorship_entry = second_authorship_entry
        # The census keys whose minted credential an operator names a second approver at the platform's own console.
        self.platform_names_approver = tuple(platform_names_approver)
        # The whitelist_mutation roster as the compiler writes it, established when the policy charter first compiles
        # (governanceSignersFor, establishGovernance) and left standing by every compile after (governanceAlreadyStood).
        self.whitelist_seats: List[Dict[str, Any]] = []
        self.whitelist_threshold: Optional[int] = None
        self.governance_established = False
        # Spec T15 — the roster ceremony (AER 360 Spec 99). The multisig_mutation roster is the census the compiler writes for C12C's family
        # (governanceSignersFor), seated with the whitelist roster at the first policy compile, at C12's count; `change_roster` seats only the
        # census keys named. The platform's ceremonies, its record of who signed and when, and the estate's trail as the audit export reads it.
        self.change_roster = tuple(change_roster) if change_roster is not None else None
        self.change_seats: List[Dict[str, Any]] = []
        self.change_threshold: Optional[int] = None
        self.ceremonies: List[Dict[str, Any]] = []
        self.trail: List[Dict[str, Any]] = []
        self.before_spec_99 = before_spec_99  # the estate at Spec 95: the move proposed, the ceremony held, no seat row and no roster roads
        self.ceremony_lapses = ceremony_lapses  # the next ceremonies born lapse at birth: the platform's clock is past their expires_at
        self.lapse_after_first_signature = lapse_after_first_signature  # the platform's clock passes a ceremony's expires_at once its first signature is counted
        self.account_email = account_email  # the AAP account's own address, attributed to the founder's key (addressesOfCaller); None: not known here
        # Spec T17 / AER 360 Spec 105 — the seat view reads the roster. None (the default): the seat view has no onRoster, and the
        # harness behaves as T15. A list of seat specs {email, name?, state?, credentialId, ambiguous?, onRoster} makes GET
        # /v1/approver-seats answer those seats with onRoster (and rosterSaid where null); onRoster "compute" is read from the
        # live rosters by `seat_on_roster` (Spec 105 §1's shared predicate), so a seat flips true the moment a move applies.
        self.seats_override = [dict(spec) for spec in seats_override] if seats_override is not None else None
        self.whitelist_id = "wl-" + secrets.token_hex(4)
        self._query: Dict[str, List[str]] = {}
        # The bindings a re-invitation's redemption retired: (address, credential) pairs from person.credential_replaced.
        self.retired: set = set()
        self.base = base.rstrip("/")
        parsed = urllib.parse.urlparse(self.base)
        self.origin = "%s://%s" % (parsed.scheme, parsed.netloc)
        self.rp_id = parsed.hostname or RP_ID
        self.secret = secret if secret is not None else b"double-secret"  # shared with the Treasury double, so a sign-in's challenge verifies at either workspace
        self.catalog_version = catalog_version
        # Spec T14 — the sandbox's platform and chain, shared by the two workspaces; this workspace's platform account; the Treasury's knobs
        self.is_treasury = is_treasury
        self.platform = platform if platform is not None else PlatformDouble()
        self.chain = chain if chain is not None else UsdcChainDouble()
        self.aap_account_id = aap_account_id or AAP_ACCOUNT_ID
        self.platform.accounts.add(self.aap_account_id)
        self.workspace_id = TREASURY_WORKSPACE_ID if is_treasury else WORKSPACE_ID
        self.initial_usdc_cents = initial_usdc_cents if initial_usdc_cents is not None else holdings_usdc_cents  # what the wallet holds when born: Bear's funding
        self.quote_ceiling_usd_cents = quote_ceiling_usd_cents
        self.actual_gas_usd_cents = actual_gas_usd_cents
        self.gas_refusal_names_other_figures = gas_refusal_names_other_figures  # a review whose GAS_SHORTFALL names other figures than the account's
        self.review_refuses_but_pays = review_refuses_but_pays  # a review that says nothing was sent while money moved behind it
        self.delegated = False  # the key delegated on the payment chain at its first payment (Spec 104 §1)
        self.sponsor = T.derive_address("the platform double's sponsor account/%s" % T.PAYEE_CHAIN)
        self.paymaster = T.derive_address("the platform double's paymaster/%s" % T.PAYEE_CHAIN)
        self.implementation = T.derive_address("the platform double's Simple7702Account implementation/%s" % T.PAYEE_CHAIN)
        self.workspace = {"id": self.workspace_id, "name": company, "aapAccountId": self.aap_account_id, "realm": "sandbox", "sandboxMarkLetter": "S",
                          "baseCurrency": "USD", "displayCurrency": "AUD", "status": "active", "provisioning": "provisioned",
                          "rateSource": "double", "createdAt": "2026-09-19T00:00:00.000Z"}
        # Spec T13 — the funding wallet (Spec 98): BOTH columns, or none. "press": born by the founder's press; "born": already held;
        # "refused": the gateway refuses the credential, as it did on 21 September; "unavailable": no gateway configured. The typed-address
        # road (POST /v1/workspace/source-account) is closed, so nothing here sets a source account but the birth.
        if funding_wallet not in ("press", "born", "refused", "unavailable"):
            raise ValueError("funding_wallet is press, born, refused or unavailable, not %r" % funding_wallet)
        self.funding_wallet = funding_wallet
        self.source_account: Optional[str] = None
        self.custody_key_id: Optional[str] = None
        self.wallet_born_at: Optional[str] = None
        self.home_stack = "double-stack-1"
        self.funding_presses: List[Dict[str, Any]] = []  # each options call and press, with the binding the challenge was derived from
        # Spec T13 §3 — the mirror: the press that meets the count answers the row's stale `proposed` (as the live estate did at 23:44) while
        # the platform counted 2 of 2; `register_corrects` is Spec 100, the register reading whitelisted on the next GET /v1/payees
        self.mirror_lags = mirror_lags
        self.register_corrects = register_corrects
        self.faucet = faucet if faucet is not None else FaucetDouble()
        self.rpc = rpc if rpc is not None else TestnetRpcDouble()
        # The account's ONE role-bearing credential (the founder's author token drawn up by the birth script), on the account's
        # one policy entry bearing authorship — the entry an author invitation mints on since Spec 91.
        self.authorship_entry = {"id": "pe-author-" + secrets.token_hex(4), "name": "Founder (author)"}
        self.founder_credential = str(uuid.uuid4())  # the platform's credential ids are UUIDs, so their short form (Spec 99) tells them apart here too
        self.credentials: Dict[str, Dict[str, Any]] = {self.founder_credential: {"access": "sign+audit", "name": "Founder (author)", "entry": self.authorship_entry["id"]}}
        self.second_approvers: List[str] = []
        self.invites: Dict[str, Dict[str, Any]] = {}
        self.passkeys: Dict[str, Dict[str, Any]] = {}  # webauthnId → row
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.interviews: Dict[str, Dict[str, Any]] = {}
        self.answers: Dict[str, List[Dict[str, Any]]] = {}
        self.payees: Dict[str, Dict[str, Any]] = {}
        self.addresses: Dict[str, Dict[str, Any]] = {}
        self.sets: Dict[str, Dict[str, Any]] = {}
        self.approvals: Dict[str, List[Dict[str, Any]]] = {}
        self.instructions_seen: List[Tuple[str, str]] = []
        self.calls: List[Dict[str, Any]] = []
        self.audit: List[str] = []
        self.founder_invite_token: Optional[str] = None
        # Spec T14 — the second workspace of the sandbox: Harness Treasury, beside every Holdings double, on the same platform and chain
        self.treasury: Optional["EstateDouble"] = None
        if treasury and not is_treasury:
            self.treasury = EstateDouble(base=base, funding_wallet=treasury_funding_wallet, company=T.TREASURY["company"], catalog_version=catalog_version,
                                         currency_spoken_as_code=currency_spoken_as_code, faucet=self.faucet, rpc=self.rpc, platform=self.platform, chain=self.chain,
                                         treasury=False, is_treasury=True, aap_account_id=TREASURY_ACCOUNT_ID, secret=self.secret, account_email=T.TREASURY["email"],
                                         initial_usdc_cents=treasury_usdc_cents if treasury_funding_wallet == "born" else 0,  # Bear funds an address he has seen: a wallet that stood
                                         quote_ceiling_usd_cents=quote_ceiling_usd_cents, actual_gas_usd_cents=actual_gas_usd_cents)
        if funding_wallet == "born":
            self.birth_funding_wallet(None, "account_creation_interview")

    # -- the funding wallet (spec 98: services/fundingwallet.ts, routes/workspace.ts) ---------------------
    def has_funding_wallet(self) -> bool:
        """A funding wallet is BOTH columns. Either alone is not one (hasFundingWallet)."""
        return bool(self.source_account and self.custody_key_id)

    def funding_wallet_view(self) -> Optional[Dict[str, Any]]:
        if not self.has_funding_wallet():
            return None
        return {"address": self.source_account, "keyId": self.custody_key_id, "homeStack": self.home_stack, "bornAt": self.wallet_born_at,
                "sentence": "Funding wallet: %s, on %s." % (self.source_account, self.home_stack),
                # Spec 104 §1 (services/fundingwallet.ts FundingWalletView): the key's own address, the fund sentence and the chains this deployment pays on
                "keyAddress": self.source_account, "fundSentence": "Fund this account with %s on %s. Gas is bought separately, below." % (T.PAYMENT_ASSET, T.PAYEE_CHAIN),
                "chains": [T.PAYEE_CHAIN], "retiredAccount": None, "retiredSentence": None}

    def birth_funding_wallet(self, credential_id: Optional[str], via: str) -> Dict[str, Any]:
        """birthFundingWallet: refused before the gateway is asked where a key stands; else both columns in one write, and wallet.born."""
        if self.custody_key_id:
            raise Refusal("FUNDING_WALLET_ALREADY_BORN", detail={"address": self.source_account, "keyId": self.custody_key_id, "cause": ALREADY_BORN_CAUSE},
                          provenance={"source": "workspace"})
        if self.funding_wallet == "unavailable":
            raise Refusal("GATEWAY_UNAVAILABLE", GATEWAY_NOT_CONFIGURED, {"cause": "no signing gateway is configured for this deployment", "setting": "GATEWAY_ADDRESS"},
                          provenance={"source": "deployment"})
        if self.funding_wallet == "refused":
            raise Refusal("WALLET_BIRTH_REFUSED", WALLET_BIRTH_REFUSED_ON_21_SEPTEMBER, {"gatewaySaid": GATEWAY_SAID_ON_21_SEPTEMBER, "kind": "refused"},
                          provenance={"source": "gateway"})
        self.source_account = T.derive_address("the estate double's funding wallet/%s/%s" % (self.workspace["name"], T.TESTNET_NAME))
        self.custody_key_id = "key-" + secrets.token_hex(6)
        self.wallet_born_at = self._now_iso()
        if self.initial_usdc_cents:
            self.chain.credit(self.source_account, T.usdc_minor_of_cents(self.initial_usdc_cents))  # what Bear funded the wallet with (Spec T14: the Treasury's float)
        self.audit.append("wallet.born %s key %s on %s via %s by %s" % (self.source_account, self.custody_key_id, self.home_stack, via, credential_id))
        return {"address": self.source_account, "keyId": self.custody_key_id, "homeStack": self.home_stack, "bornAt": self.wallet_born_at}

    def funding_wallet_binding(self, issued_at: Any, credential_id: str) -> Dict[str, str]:
        """deriveChallenge's binding for the press: setDigest `funding-wallet:<workspace id>:<issuedAtMs>`, the credential, the purpose."""
        return {"setDigest": "funding-wallet:%s:%s" % (WORKSPACE_ID, issued_at), "credentialId": credential_id, "purpose": FUNDING_WALLET_PURPOSE}

    def funding_wallet_challenge(self, binding: Dict[str, str]) -> str:
        return self.challenge(binding["purpose"], "%s|%s" % (binding["setDigest"], binding["credentialId"]), 0)

    def funding_wallet_options(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author")
        if self.has_funding_wallet():
            raise Refusal("FUNDING_WALLET_ALREADY_BORN", detail={"address": self.source_account, "keyId": self.custody_key_id, "cause": ALREADY_BORN_CAUSE},
                          provenance={"source": "workspace"})
        issued_at = int(time.time() * 1000)
        binding = self.funding_wallet_binding(issued_at, caller["credentialId"])
        challenge = self.funding_wallet_challenge(binding)
        own = [w for w, row in self.passkeys.items() if row["credentialId"] == caller["credentialId"]]
        self.funding_presses.append({"step": "options", "binding": binding, "issuedAtMs": issued_at, "challenge": challenge})
        return 200, {"options": {"challenge": challenge, "rpId": self.rp_id, "timeout": 60000, "userVerification": "required",
                                 "allowCredentials": [{"id": w, "type": "public-key", "transports": ["internal"]} for w in own]}, "issuedAtMs": issued_at}

    def funding_wallet_press(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        body = body or {}
        for field in ("issuedAtMs", "response"):
            if field not in body:
                raise Malformed("%s: Required" % field)
        self.assert_fresh(body["issuedAtMs"])
        binding = self.funding_wallet_binding(body["issuedAtMs"], caller["credentialId"])
        expected = self.funding_wallet_challenge(binding)
        response = body["response"] or {}
        if not isinstance(response.get("id"), str) or not response["id"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "assertion carried no credential id"})
        stored = self.passkeys.get(response["id"])
        if not stored or stored["credentialId"] != caller["credentialId"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "the asserting passkey is not the pressing credential"})
        try:
            stored["signCount"] = PK.verify_assertion(response, expected, self.origin, self.rp_id, stored["publicKey"], stored["signCount"])
        except PK.PasskeyRefused as err:
            raise Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]})
        stored["lastAuthAtMs"] = body["issuedAtMs"]
        self.funding_presses.append({"step": "press", "binding": binding, "issuedAtMs": body["issuedAtMs"], "verified": True, "credentialId": caller["credentialId"]})
        birth = self.birth_funding_wallet(caller["credentialId"], "press")
        return 200, {"born": True, "fundingWallet": dict(birth, sentence="Funding wallet: %s, on %s." % (birth["address"], birth["homeStack"]))}

    # -- the birth script's road: the founder's one-time link -----------------------------
    def mint_founder_link(self, display_name: str = "Harriet") -> str:
        token = secrets.token_urlsafe(32)
        self.invites[hashlib.sha256(token.encode()).hexdigest()] = {
            "id": "inv-" + secrets.token_hex(6), "displayName": display_name, "email": None, "phone": None, "role": None, "note": "birth",
            "state": "pending", "credentialId": self.founder_credential, "createdAt": self._now_iso(), "expiresAt": self._iso(time.time() + 72 * 3600),
            "redeemedAt": None, "revokedAt": None, "revokedByCredentialId": None, "dispatchedAt": None, "dispatchDetail": None,
        }
        self.founder_invite_token = token
        return "%s/invite#%s" % (self.origin, token)

    # -- the transport ------------------------------------------------------------------
    def __call__(self, request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
        method = request.get_method()
        url = urllib.parse.urlparse(request.full_url)
        path = url.path
        # Spec T13: the faucet and the chain's RPC are other hosts; each answers for itself, in its own shape. Spec T14: so are the platform's admin road
        # and the payment chain's public RPC; and a request the Treasury workspace owns is answered by its own double
        if url.netloc == FAUCET_HOST and path.startswith("/faucet-api/"):
            return self.faucet(request)
        if url.netloc == RPC_HOST:
            return self.rpc(request)
        if url.netloc == PLATFORM_HOST:
            return self.platform(request)
        if url.netloc == PUBLIC_RPC_HOST:
            return self.chain(request)
        headers = {k.lower(): v for k, v in request.header_items()}
        if self.treasury is not None and self.treasury.owns(path, headers, request.data):
            return self.treasury(request)
        self._query = urllib.parse.parse_qs(url.query)
        body: Any = None
        if request.data:
            try:
                body = json.loads(request.data.decode("utf-8"))
            except ValueError:
                return self._answer(400, Refusal("REQUEST_MALFORMED", detail={"issues": "body: not JSON"}).body(), [])
        record = {"method": method, "path": path, "headers": headers, "body": body}
        self.calls.append(record)
        set_cookie: List[Tuple[str, str]] = []
        try:
            status, payload = self.dispatch(method, path, headers, body, set_cookie)
            return self._answer(status, payload, set_cookie)
        except Refusal as refusal:
            return self._answer(STATUS[refusal.code], refusal.body(), [])
        except Malformed as err:
            return self._answer(400, Refusal("REQUEST_MALFORMED", detail={"issues": err.issue}).body(), [])

    @staticmethod
    def _answer(status: int, payload: Any, set_cookie: List[Tuple[str, str]]) -> Tuple[int, List[Tuple[str, str]], str]:
        headers = [("Content-Type", "application/json; charset=utf-8")] + set_cookie
        return status, headers, json.dumps(payload, ensure_ascii=False)

    # -- helpers ------------------------------------------------------------------------------
    @staticmethod
    def _now_iso() -> str:
        return EstateDouble._iso(time.time())

    @staticmethod
    def _iso(epoch: float) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(epoch)) + ".000Z"

    def challenge(self, purpose: str, subject: str, issued_at: int) -> str:
        digest = hmac.new(self.secret, ("%s|%s|%s" % (purpose, subject, issued_at)).encode(), hashlib.sha256).digest()
        return PK.b64url_encode(digest)

    @staticmethod
    def assert_fresh(issued_at: Any) -> None:
        if not isinstance(issued_at, int) or issued_at <= 0:
            raise Malformed("issuedAtMs: Expected number, received %s" % type(issued_at).__name__)
        age = int(time.time() * 1000) - issued_at
        if age < 0 or age > STEPUP_MAX_AGE_MS:
            raise Refusal("STEP_UP_STALE", detail={"maxAgeSeconds": str(STEPUP_MAX_AGE_MS // 1000)})

    def roles_of(self, credential_id: str) -> List[str]:
        roles: List[str] = []
        entry = self.credentials.get(credential_id)
        if entry:
            if "sign" in entry["access"]:
                roles.append("author")
            if "audit" in entry["access"]:
                roles.append("viewer")
        if credential_id in self.second_approvers:
            roles.append("approver")
        if "author" in roles or "approver" in roles:
            if "viewer" not in roles:
                roles.append("viewer")
        return [r for r in ("author", "approver", "viewer") if r in roles]

    def session_view(self, session: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        view = {"workspace": dict(self.workspace), "credentialId": session["credentialId"], "displayName": session["displayName"],
                "roles": self.roles_of(session["credentialId"]), "rolesEvaluatedAt": self._now_iso(), "csrfToken": session["csrfToken"],
                "passkeySignals": {"rpId": self.rp_id, "userId": PK.b64url_encode(session["credentialId"].encode()), "name": "%s · AER 360" % self.workspace["name"],
                                   "displayName": session["displayName"], "allAcceptedCredentialIds": [w for w, row in self.passkeys.items() if row["credentialId"] == session["credentialId"]]}}
        view.update(extra or {})
        return view

    def open_session(self, credential_id: str, display_name: str, set_cookie: List[Tuple[str, str]], email: Optional[str] = None) -> Dict[str, Any]:
        # `email` is the address the person's invitation was written with (None for the founder's birth key): what the
        # estate's whitelist press says about whose seat it is (services/payees.ts, signerEmailOf → emailOfCredential).
        session = {"id": secrets.token_urlsafe(24), "credentialId": credential_id, "displayName": display_name, "csrfToken": secrets.token_urlsafe(24),
                   "workspaceId": WORKSPACE_ID, "email": email}
        self.sessions[session["id"]] = session
        set_cookie.append(("Set-Cookie", "%s=%s; HttpOnly; SameSite=Strict; Secure; Path=/; Max-Age=43200" % (H.SESSION_COOKIE, session["id"])))
        return session

    def require_session(self, headers: Dict[str, str]) -> Dict[str, Any]:
        cookie = headers.get("cookie", "")
        session_id = None
        for part in cookie.split(";"):
            name, _, value = part.strip().partition("=")
            if name == H.SESSION_COOKIE:
                session_id = value
        if not session_id:
            raise Refusal("NOT_AUTHENTICATED")
        session = self.sessions.get(session_id)
        if not session:
            raise Refusal("NOT_AUTHENTICATED", detail={"cause": "session expired"})
        return session

    def require_caller(self, headers: Dict[str, str], role: str, mutating: bool = False) -> Dict[str, Any]:
        session = self.require_session(headers)
        if mutating:
            token = headers.get(H.CSRF_HEADER)
            if not token or token != session["csrfToken"]:
                raise Refusal("NOT_AUTHENTICATED", detail={"cause": "missing or incorrect CSRF token"})
        held = self.roles_of(session["credentialId"])
        if role not in held:
            raise Refusal("ROLE_NOT_GRANTED", role_not_granted_sentence(self.workspace["name"], held, role),
                          {"workspace": self.workspace["name"], "held": ",".join(held) or "none", "required": role},
                          provenance={"source": "aap_policy"})
        return dict(session, roles=held)

    # -- dispatch ---------------------------------------------------------------------------------
    def dispatch(self, method: str, path: str, headers: Dict[str, str], body: Any, set_cookie: List[Tuple[str, str]]) -> Tuple[int, Any]:
        route = "%s %s" % (method, path)
        m = re.match(r"^/v1/onboarding/interviews/([^/]+)(/.*)?$", path)
        if m:
            return self.onboarding_interview(method, m.group(1), m.group(2) or "", headers, body)
        if route == "POST /v1/auth/invite/options":
            return self.invite_options(body)
        if route == "POST /v1/auth/invite/verify":
            return self.invite_verify(body, set_cookie)
        if route == "POST /v1/auth/login/options":
            return self.login_options()
        if route == "POST /v1/auth/login/verify":
            return self.login_verify(body, set_cookie)
        if route == "GET /v1/auth/session":
            return 200, self.session_view(self.require_session(headers))
        if route == "GET /v1/journey":
            return self.journey(headers)
        if route == "POST /v1/onboarding/interviews":
            return self.start_interview(headers, body)
        if route == "GET /v1/onboarding/charter":
            return self.charter_standing(headers)
        if route == "POST /v1/invites":
            return self.mint_invite(headers, body)
        if route == "GET /v1/invites":
            return self.list_invites(headers)
        if route == "GET /v1/approver-seats":
            return self.seats(headers)
        if route == "POST /v1/approver-seats/grant":
            return self.grant_seat(headers, body)
        # Spec 99's door (routes/rosterchanges.ts): absent before it, so an estate at Spec 95 answers the route unknown
        if not self.before_spec_99:
            if route == "GET /v1/roster/changes":
                return self.list_roster_changes(headers)
            m = re.match(r"^/v1/roster/changes/([^/]+)/sign(/options)?$", path)
            if m and method == "POST":
                if m.group(2):
                    return self.roster_change_sign_options(headers, m.group(1))
                return self.sign_roster_change(headers, m.group(1), body)
        if route == "GET /v1/export/audit":
            return self.audit_export(headers)
        if route == "POST /v1/payees":
            return self.create_payee(headers, body)
        if route == "GET /v1/payees":
            self.require_caller(headers, "viewer")
            return 200, {"payees": self.list_payees()}
        m = re.match(r"^/v1/payees/addresses/([^/]+)/(promote|approve|reject)$", path)
        if m and method == "POST":
            return self.address_action(headers, m.group(1), m.group(2))
        if route == "POST /v1/sets/review":
            return self.review_or_create(headers, body, create=False)
        if route == "POST /v1/sets":
            return self.review_or_create(headers, body, create=True)
        if route == "GET /v1/sets":
            caller = self.require_caller(headers, "viewer")
            return 200, {"sets": [self.set_view(s, caller) for s in sorted(self.sets.values(), key=lambda s: s["createdAt"], reverse=True)]}
        m = re.match(r"^/v1/sets/([^/]+)(/submit|/execute)?$", path)
        if m:
            if method == "GET" and not m.group(2):
                caller = self.require_caller(headers, "viewer")
                row = self.sets.get(m.group(1))
                if not row:
                    raise Refusal("SET_NOT_EDITABLE", detail={"cause": "no such run"})
                return 200, {"set": self.set_view(row, caller)}
            if method == "POST" and m.group(2) == "/submit":
                return self.submit_set(headers, m.group(1))
            if method == "POST" and m.group(2) == "/execute":
                return self.execute_set(headers, m.group(1))
        m = re.match(r"^/v1/approvals/([^/]+)/(challenge|approve)$", path)
        if m and method == "POST":
            return self.approval(headers, m.group(1), m.group(2), body)
        if route == "GET %s" % T.FUNDING_BALANCES_ROUTE:
            return self.funding_account_balances(headers)
        if route == "GET %s" % T.GAS_ACCOUNT_ROUTE:
            return self.gas_account(headers)
        if route == "GET /v1/workspace":
            self.require_session(headers)
            wallet = self.funding_wallet_view()
            return 200, {"workspace": dict(self.workspace), "sourceAccount": self.source_account, "fundingWallet": wallet,
                         "fundingWalletAbsence": None if wallet else NO_FUNDING_WALLET_SENTENCE, "supportedCurrencies": ["AUD", "EUR", "GBP", "USD"]}
        if route == "POST /v1/workspace/funding-wallet/options":
            return self.funding_wallet_options(headers)
        if route == "POST /v1/workspace/funding-wallet":
            return self.funding_wallet_press(headers, body)
        if route == "POST /v1/workspace/display-currency":
            self.require_caller(headers, "author", mutating=True)
            currency = str((body or {}).get("displayCurrency", "")).upper()
            self.workspace["displayCurrency"] = currency
            return 200, {"displayCurrency": currency}
        if route == "GET /v1/workspace/readiness":
            self.require_session(headers)
            # NO FUNDING WALLET, NO PAYMENT (spec 98, item 3): both columns, or transactable is false with the sentence's own reason
            if not self.has_funding_wallet():
                return 200, {"transactable": False, "reason": NO_FUNDING_WALLET_REASON, "workspace": dict(self.workspace)}
            return 200, {"transactable": True, "reason": None, "workspace": dict(self.workspace)}
        if route == "GET /v1/aer360/wallets":
            self.require_caller(headers, "viewer")
            return 200, {"answer": None, "absence": WALLETS_ABSENCE, "display": {"currency": "AUD", "rateE8": "150000000"}}
        raise Refusal("REQUEST_MALFORMED", detail={"validation": "Route %s not found" % route})

    # -- auth ----------------------------------------------------------------------------------------
    def _peek_invite(self, token: Any) -> Dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise Malformed("token: String must contain at least 1 character(s)")
        row = self.invites.get(hashlib.sha256(token.encode()).hexdigest())
        if not row or row["redeemedAt"] is not None or row["revokedAt"] is not None:
            raise Refusal("INVITE_INVALID")
        return row

    def registration_options(self, credential_id: str, display_name: str) -> Dict[str, Any]:
        return {"rp": {"name": "AER Accounts", "id": self.rp_id}, "user": {"id": PK.b64url_encode(credential_id.encode()), "name": "%s · AER 360" % self.workspace["name"], "displayName": display_name},
                "challenge": "", "pubKeyCredParams": [{"alg": -8, "type": "public-key"}, {"alg": -7, "type": "public-key"}, {"alg": -257, "type": "public-key"}],
                "timeout": 60000, "attestation": "none", "excludeCredentials": [], "authenticatorSelection": {"residentKey": "required", "userVerification": "required", "requireResidentKey": True}}

    def invite_options(self, body: Any) -> Tuple[int, Any]:
        body = body or {}
        for field in ("token", "issuedAtMs", "response"):
            if field not in body:
                raise Malformed("%s: Required" % field)
        row = self._peek_invite(body["token"])
        issued = int(time.time() * 1000)
        options = self.registration_options(row["credentialId"], row["displayName"])
        options["challenge"] = self.challenge("invite", body["token"], issued)
        return 200, {"options": options, "issuedAtMs": issued, "displayName": row["displayName"]}

    def invite_verify(self, body: Any, set_cookie: List[Tuple[str, str]]) -> Tuple[int, Any]:
        body = body or {}
        for field in ("token", "issuedAtMs", "response"):
            if field not in body:
                raise Malformed("%s: Required" % field)
        self.assert_fresh(body["issuedAtMs"])
        row = self._peek_invite(body["token"])
        try:
            stored = PK.verify_registration(body["response"], self.challenge("invite", body["token"], body["issuedAtMs"]), self.origin, self.rp_id)
        except (PK.PasskeyRefused, PK.PasskeyError, TypeError, KeyError, AttributeError) as err:
            raise Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]}, staleCredential={"rpId": self.rp_id, "credentialId": (body.get("response") or {}).get("id")})
        row["redeemedAt"] = self._now_iso()
        row["state"] = "redeemed"
        credential_id = row["credentialId"]
        row["_redeemedEpoch"] = time.time()
        self.passkeys[body["response"]["id"]] = {"credentialId": credential_id, "publicKey": stored["public_key"], "signCount": stored["sign_count"],
                                                 "label": row["displayName"], "lastAuthAtMs": body["issuedAtMs"], "email": row.get("email")}
        self.audit.append("passkey.registered %s via invite" % credential_id)
        if not self.before_spec_91 and row.get("email"):
            # THE OLD BINDING IS RETIRED (Spec 91, item 4; routes/auth.ts at the binding): every credential an earlier redeemed,
            # not withdrawn invitation of the same address enrolled, other than this one, on the trail with both ids.
            replaced = self.earlier_bindings_of(row)
            if replaced:
                for old in replaced:
                    self.retired.add((row["email"].strip().lower(), old))
                self.audit.append("person.credential_replaced %s: %s -> %s via invite_redemption" % (row["email"].strip().lower(), ",".join(replaced), credential_id))
        seat = self.complete_seat_on_redemption(credential_id, row.get("email"), row["displayName"])
        # A SEAT FOLLOWS ITS PERSON (Spec 95, count 2; routes/auth.ts): the credential this redemption bound is the one every roster seat naming
        # this address must count; the moved, held and refused seats travel on this answer alone, as `rosterSeats`
        roster_seats = self.rebind_roster_seats(row.get("email"), row["displayName"], credential_id, credential_id, "invite_redemption") if row.get("email") else None
        roles = self.roles_of(credential_id)
        if not roles:
            raise Refusal("ROLE_NOT_GRANTED", detail={"required": "any", "held": "none"}, provenance={"source": "aap_policy"})
        session = self.open_session(credential_id, row["displayName"], set_cookie, row.get("email"))
        extra: Dict[str, Any] = {}
        if seat:
            extra["approverSeat"] = seat
        if roster_seats is not None:
            extra["rosterSeats"] = roster_seats
        return 200, self.session_view(session, extra or None)

    def login_options(self) -> Tuple[int, Any]:
        issued = int(time.time() * 1000)
        nonce = PK.b64url_encode(secrets.token_bytes(16))
        return 200, {"options": {"rpId": self.rp_id, "challenge": self.challenge("login", nonce, issued), "allowCredentials": [], "timeout": 60000, "userVerification": "required"},
                     "issuedAtMs": issued, "nonce": nonce}

    def login_verify(self, body: Any, set_cookie: List[Tuple[str, str]]) -> Tuple[int, Any]:
        body = body or {}
        for field in ("nonce", "issuedAtMs", "response"):
            if field not in body:
                raise Malformed("%s: Required" % field)
        self.assert_fresh(body["issuedAtMs"])
        response = body["response"] or {}
        if not isinstance(response.get("id"), str) or not response["id"]:
            raise Refusal("NOT_AUTHENTICATED", detail={"cause": "assertion carried no credential id"})
        stored = self.passkeys.get(response["id"])
        if not stored:
            raise Refusal("PASSKEY_NOT_ENROLLED", detail={"presentedIdPrefix": response["id"][:12], "enrolledCredentials": str(len(self.passkeys))},
                          staleCredential={"rpId": self.rp_id, "credentialId": response["id"]})
        handle = (response.get("response") or {}).get("userHandle")
        if handle is not None:
            decoded = PK.b64url_decode(handle).decode("utf-8", "replace")
            if decoded != stored["credentialId"] and decoded != AAP_ACCOUNT_ID:
                raise Refusal("NOT_AUTHENTICATED", detail={"cause": "the passkey and its enrolment have come apart (user handle mismatch)",
                                                          "decodedHandlePrefix": decoded[:12], "expectedPrefix": stored["credentialId"][:12]})
        if body["issuedAtMs"] <= stored["lastAuthAtMs"]:
            raise Refusal("STEP_UP_STALE", detail={"cause": "challenge already used"})
        try:
            new_count = PK.verify_assertion(response, self.challenge("login", body["nonce"], body["issuedAtMs"]), self.origin, self.rp_id, stored["publicKey"], stored["signCount"])
        except PK.PasskeyRefused as err:
            raise Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]})
        stored["signCount"] = new_count
        stored["lastAuthAtMs"] = body["issuedAtMs"]
        roles = self.roles_of(stored["credentialId"])
        if not roles:
            raise Refusal("ROLE_NOT_GRANTED", detail={"required": "any", "held": "none"}, provenance={"source": "aap_policy"})
        session = self.open_session(stored["credentialId"], stored["label"], set_cookie, stored.get("email"))
        return 200, self.session_view(session)

    # -- the interviews --------------------------------------------------------------------------------
    def catalog(self, interview_type: str) -> List[A.Question]:
        """The book's catalog; an estate before version 14 (Spec T11) leaves out the seven Spec 92 added."""
        questions = list(A.CATALOGS[interview_type])
        if self.catalog_version < 14:
            added = set(A.ADDED_IN_V14[interview_type])
            questions = [q for q in questions if q.id not in added]
        return questions

    def latest(self, interview_id: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for row in self.answers.get(interview_id, []):
            out[row["questionId"]] = row
        return out

    @staticmethod
    def visible(q: A.Question, latest: Dict[str, Dict[str, Any]]) -> bool:
        if not q.depends_on:
            return True
        gate = latest.get(q.depends_on["questionId"])
        if not gate:
            return False
        value = gate["value"]
        chosen = value.get("choice")
        if isinstance(chosen, str):
            return chosen in q.depends_on["oneOf"]
        choices = value.get("choices")
        if isinstance(choices, list):
            return any(c in q.depends_on["oneOf"] for c in choices)
        return False

    def start_interview(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author")
        interview_type = (body or {}).get("interviewType")
        if interview_type not in ("policy", "wallet_account"):
            raise Malformed("interviewType: Invalid enum value. Expected 'policy' | 'wallet_account', received '%s'" % interview_type)
        in_flight = [iv for iv in self.interviews.values() if iv["interviewType"] == interview_type and iv["state"] not in ("written", "abandoned")]
        if in_flight:
            iv = sorted(in_flight, key=lambda i: i["createdAt"])[-1]
        else:
            iv = {"id": "iv-" + secrets.token_hex(6), "interviewType": interview_type, "state": "in_progress", "catalogVersion": self.catalog_version,
                  "createdAt": time.time(), "updatedAt": time.time(), "confirmedByCredentialId": None, "writeError": None, "compiledCharter": None, "writeReceipt": None,
                  "startedBy": caller["credentialId"]}
            self.interviews[iv["id"]] = iv
            self.answers[iv["id"]] = []
        page = self.page(iv, serve_truth=True)
        return 200, {"interview": {"id": iv["id"], "state": page["state"]}, "page": page}

    def page(self, iv: Dict[str, Any], serve_truth: bool) -> Dict[str, Any]:
        catalog = self.catalog(iv["interviewType"])
        latest = self.latest(iv["id"])
        visible = [q for q in catalog if self.visible(q, latest)]
        idx = next((i for i, q in enumerate(visible) if q.id not in latest), -1)
        state = iv["state"]
        contradiction = None
        if serve_truth and idx == -1 and state in ("in_progress", "at_read_back"):
            violation = self.standing_violation(iv["interviewType"], latest)
            if violation is None:
                if state == "in_progress":
                    iv["state"] = "at_read_back"
                state = "at_read_back"
            else:
                idx = next(i for i, q in enumerate(visible) if q.id == violation["quorumQuestionId"])
                contradiction = {"code": "ANSWER_INVALID", "message": violation["sentence"], "detail": {"questionId": violation["quorumQuestionId"]}}
        q = visible[idx] if idx != -1 else None
        at = idx if idx != -1 else len(visible)
        previous = None
        for i in range(at - 1, -1, -1):
            if visible[i].id in latest:
                previous = visible[i].id
                break
        part = PROMPTS.get(q.id, {}).get("part", "") if q else (PROMPTS.get(visible[-1].id, {}).get("part", "") if visible else "")
        in_part = [v for v in visible if PROMPTS.get(v.id, {}).get("part", "") == part]
        question = None
        if q:
            # THE FIGURE THAT ARRIVES WRITTEN (Spec 92): WO3 and WO4 carry the catalog's written dollar as the value on record where no
            # answer stands yet; every other page reads exactly as before
            written = PROMPTS.get(q.id, {}).get("written")
            question = {"questionId": q.id, "part": part, "kind": q.kind, "prompt": PROMPTS.get(q.id, {}).get("prompt", q.id), "options": list(q.options) if q.options else None,
                        "listFields": PROMPTS.get(q.id, {}).get("listFields"), "recommended": None, "note": PROMPTS.get(q.id, {}).get("note"), "required": q.required,
                        "priorValue": latest[q.id]["value"] if q.id in latest else (dict(written) if written else None)}
            if q.kind == "currency":
                question["options"] = ["AUD", "EUR", "GBP", "USD"]
        return {"interviewId": iv["id"], "state": state, "question": question,
                "progress": {"part": part, "positionInPart": (in_part.index(q) + 1) if q and q in in_part else len(in_part), "ofPart": len(in_part),
                             "position": min(at + 1, len(visible)), "of": len(visible)},
                "previousQuestionId": previous, "writeError": iv["writeError"], "confirmed": iv["confirmedByCredentialId"] is not None,
                "contradiction": contradiction, "display": {"currency": "AUD", "rateE8": "150000000"}, "baseDecimals": 2}

    # the cross-question checks (crosschecks.ts): a quorum may never exceed the roster that must meet it
    QUORUM_ROSTER_CHECKS = [
        ("policy", "C10", ("C11", "A8"), "releasing a held payment", None),
        ("policy", "C12", ("A8", "C11"), "changing the rules themselves", None),
        ("policy", "C12B", ("A8", "C11"), "changing the payment rules", ("C12A", ("Yes",))),
        ("policy", "C12C", ("A8", "C11"), "changing who the approvers are", ("C12A", ("Yes",))),
        ("policy", "C12D", ("A8", "C11"), "changing the approved lists", ("C12A", ("Yes",))),
        ("wallet_account", "WQ", ("WA1", "C11"), "releasing this account’s held payments", None),
    ]

    @staticmethod
    def people_named(value: Optional[Dict[str, Any]]) -> int:
        if not value:
            return 0
        if isinstance(value.get("people"), list):
            return len([p for p in value["people"] if isinstance(p, str) and p.strip()])
        if isinstance(value.get("entries"), list):
            count = 0
            for entry in value["entries"]:
                keys = list((entry or {}).keys())
                identifying = [k for k in keys if k in ("email", "address", "principalEmail")]
                fields = identifying or keys
                if any(isinstance(entry.get(k), str) and entry[k].strip() for k in fields):
                    count += 1
            return count
        return 0

    def standing_violation(self, interview_type: str, latest: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for itype, quorum_q, rosters, governs, asked_when in self.QUORUM_ROSTER_CHECKS:
            if itype != interview_type:
                continue
            if asked_when:
                gate = latest.get(asked_when[0])
                if not gate or gate["value"].get("choice") not in asked_when[1]:
                    continue
            quorum_value = latest.get(quorum_q)
            if not quorum_value:
                continue
            try:
                quorum = int(quorum_value["value"].get("choice"))
            except (TypeError, ValueError):
                continue
            roster = next(((r, self.people_named(latest[r]["value"])) for r in rosters if r in latest), None)
            if roster is None:
                continue
            if quorum > roster[1]:
                supplied = roster[1]
                sentence = ("You have named nobody; a quorum of %d can never be met. Name the people first, then set the quorum." % quorum) if supplied == 0 else (
                    "You have named %d %s; a quorum of %d can never be met. Name more people first, or choose %d." % (supplied, "person" if supplied == 1 else "people", quorum, supplied))
                return {"quorumQuestionId": quorum_q, "quorum": quorum, "rosterQuestionId": roster[0], "named": supplied, "sentence": sentence}
        if interview_type == "wallet_account":
            wa2 = latest.get("WA2")
            if wa2 and wa2["value"].get("choice") == A.WA2_NO:
                roster = next(((r, self.people_named(latest[r]["value"])) for r in ("WA1", "C11") if r in latest), None)
                if roster is not None and roster[1] <= 1:
                    return {"quorumQuestionId": "WA2", "quorum": 1, "rosterQuestionId": roster[0], "named": roster[1],
                            "sentence": "Answering “No” beside a single named approver is refused: nobody would be left who could release a payment. Name a second approver first, or answer Yes."}
        return None

    def validate_value(self, q: A.Question, value: Any) -> None:
        def refuse(cause: str) -> None:
            raise Refusal("ANSWER_INVALID", detail={"questionId": q.id, "cause": cause})
        if not isinstance(value, dict):
            raise Malformed("value: Expected object")
        kind = q.kind
        if kind == "statement":
            if value.get("acknowledged") is not True:
                refuse("a statement page is acknowledged by Next")
        elif kind == "single_choice":
            if not isinstance(value.get("choice"), str):
                refuse("choose one option")
            if not q.options or value["choice"] not in q.options:
                refuse("the choice must be one of the options offered")
        elif kind == "multi_choice":
            if not isinstance(value.get("choices"), list):
                refuse("choices must be a list")
            for c in value["choices"]:
                if not q.options or c not in q.options:
                    refuse("every choice must be one of the options offered")
        elif kind == "text":
            if q.required and not (isinstance(value.get("text"), str) and value["text"].strip()):
                refuse("an answer is required here")
        elif kind == "list":
            if not isinstance(value.get("entries"), list):
                refuse("entries must be a list")
            if q.required and len(value["entries"]) == 0:
                refuse("at least one entry is required here")
        elif kind == "money":
            cents = value.get("cents")
            if cents is None:
                if q.required:
                    refuse("this amount is mandatory and cannot be left empty")
            elif not isinstance(cents, str) or not re.match(r"^\d+$", cents):
                refuse("an amount is a whole number of cents")
        elif kind == "percent":
            percent = value.get("percent")
            if percent is None:
                if q.required:
                    refuse("this percentage is mandatory")
            elif not isinstance(percent, (int, float)) or isinstance(percent, bool) or percent <= 0 or percent > 100:
                refuse("a percentage is between 0 and 100")
        elif kind == "count":
            count = value.get("count")
            if count is None:
                if q.required:
                    refuse("this number is mandatory")
            elif not isinstance(count, int) or isinstance(count, bool) or count < 1:
                refuse("a count is a whole number of one or more")
        elif kind == "currency":
            if not isinstance(value.get("text"), str) or not re.match(r"^[A-Za-z]{3}$", value["text"].strip()):
                refuse("choose a currency from the list")
            elif value["text"].strip().upper() not in ("AUD", "EUR", "GBP", "USD"):
                refuse('"%s" is not one of the currencies AER 360 reports in. Choose one from the list: every figure is recorded in US dollars and translated live into your display currency, and a currency this platform cannot price is a lens that would show you nothing.' % value["text"].strip().upper())
        elif kind == "roster_single":
            if q.required and not (isinstance(value.get("people"), list) and len(value["people"]) == 1):
                refuse("choose one person from the roster")
        elif kind == "roster_multi":
            if not isinstance(value.get("people"), list):
                refuse("choose people from the roster")
            if len(value["people"]) > 5:
                refuse("the platform’s hard bound is five signatories")
            if q.required and len(value["people"]) == 0:
                refuse("choose at least one person")
        elif kind == "person_or_none":
            # ONE PERSON, OR NO ONE (Spec 92, WO1): services/onboarding.ts, validateValue, case 'person_or_none'
            if not isinstance(value.get("choice"), str):
                refuse("choose whether one person holds this, or no one")
            if not q.options or value["choice"] not in q.options:
                refuse("the choice must be one of the options offered")
            if value["choice"] == q.options[0]:
                person = value.get("person")
                if not isinstance(person, dict):
                    refuse("name the person: full name and work email")
                if not (isinstance(person.get("name"), str) and person["name"].strip()):
                    refuse("the person needs a full name")
                if not (isinstance(person.get("email"), str) and person["email"].strip()):
                    refuse("the person needs a work email")
            elif value.get("person") is not None:
                refuse("“No one” names nobody; remove the person or choose the first option")
        else:
            refuse("unknown question kind %s" % kind)

    def onboarding_interview(self, method: str, interview_id: str, rest: str, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        if rest == "" and method == "GET":
            self.require_caller(headers, "viewer")
            return 200, self.page(self.load_interview(interview_id), serve_truth=True)
        if rest == "" and method == "DELETE":
            self.require_caller(headers, "author")
            iv = self.load_interview(interview_id)
            if iv["state"] not in ("in_progress", "at_read_back"):
                raise Refusal("INTERVIEW_NOT_OPEN", detail={"state": iv["state"], "cause": "only an unconfirmed draft can be deleted"})
            if iv["confirmedByCredentialId"] is not None:
                raise Refusal("INTERVIEW_NOT_OPEN", detail={"state": iv["state"], "cause": "this interview was confirmed under a passkey; what a passkey authored, no button unwrites"})
            iv["state"] = "abandoned"
            return 200, {"deleted": True, "interviewId": interview_id}
        if rest == "/answers" and method == "POST":
            caller = self.require_caller(headers, "author")
            return self.record_answer(caller, interview_id, body)
        if rest == "/readback" and method == "GET":
            self.require_caller(headers, "viewer")
            return 200, {"realm": "sandbox", "lines": self.readback(self.load_interview(interview_id))}
        if rest == "/confirm/options" and method == "POST":
            caller = self.require_caller(headers, "author")
            iv = self.load_interview(interview_id)
            issued = int(time.time() * 1000)
            digest = self.interview_digest(iv)
            challenge = self.challenge("onboarding.confirm", "%s:%s|%s" % (digest, issued, caller["credentialId"]), issued)
            own = [w for w, row in self.passkeys.items() if row["credentialId"] == caller["credentialId"]]
            return 200, {"options": {"rpId": self.rp_id, "challenge": challenge, "allowCredentials": [{"id": w, "type": "public-key"} for w in own], "userVerification": "required", "timeout": 60000},
                         "issuedAtMs": issued, "digest": digest}
        if rest == "/confirm" and method == "POST":
            caller = self.require_caller(headers, "author")
            return self.confirm(caller, interview_id, body)
        if rest == "/compile" and method == "POST":
            caller = self.require_caller(headers, "author")
            return self.compile(caller, interview_id)
        raise Refusal("REQUEST_MALFORMED", detail={"validation": "Route %s /v1/onboarding/interviews/:id%s not found" % (method, rest)})

    def load_interview(self, interview_id: str) -> Dict[str, Any]:
        iv = self.interviews.get(interview_id)
        if not iv:
            raise Refusal("INTERVIEW_NOT_FOUND")
        return iv

    def record_answer(self, caller: Dict[str, Any], interview_id: str, body: Any) -> Tuple[int, Any]:
        body = body or {}
        qid = body.get("questionId")
        if not isinstance(qid, str) or not qid or len(qid) > 20:
            raise Malformed("questionId: Required")
        if not isinstance(body.get("value"), dict):
            raise Malformed("value: Expected object, received %s" % type(body.get("value")).__name__)
        iv = self.load_interview(interview_id)
        if iv["state"] not in ("in_progress", "at_read_back"):
            raise Refusal("INTERVIEW_NOT_OPEN", detail={"state": iv["state"]})
        q = next((c for c in self.catalog(iv["interviewType"]) if c.id == qid), None)
        if q is None:
            raise Refusal("ANSWER_INVALID", detail={"questionId": qid, "cause": "no such question in this interview"})
        latest = self.latest(interview_id)
        if not self.visible(q, latest):
            raise Refusal("ANSWER_INVALID", detail={"questionId": qid, "cause": "this question is not asked given the answers so far"})
        if qid == "A5":
            code = str(body["value"].get("text", "")).strip().upper()
            if code and code not in ("AUD", "EUR", "GBP", "USD"):
                raise Refusal("ANSWER_INVALID", detail={"questionId": "A5", "cause": '"%s" is not one of the currencies AER 360 reports in.' % code}, provenance={"source": "supported_currencies"})
        self.validate_value(q, body["value"])
        # stored as jsonb stores it (db/onboardingschema.ts `value: jsonb('value')`): keys shortest first, then in byte order
        stored = A.as_the_estate_stores(body["value"])
        # a quorum may never exceed the roster that must meet it, judged before the answer is committed
        trial = dict(latest)
        trial[qid] = {"questionId": qid, "value": stored}
        violation = self.standing_violation(iv["interviewType"], trial)
        if violation and violation["quorumQuestionId"] == qid:
            raise Refusal("ANSWER_INVALID", violation["sentence"], {"questionId": qid, "quorum": str(violation["quorum"]), "namedIn": violation["rosterQuestionId"], "named": str(violation["named"])},
                          walkBackTo={"questionId": violation["quorumQuestionId"]})
        prior = latest.get(qid)
        self.answers[interview_id].append({"questionId": qid, "value": stored, "revision": (prior["revision"] + 1) if prior else 1,
                                           "promptAsAsked": PROMPTS.get(qid, {}).get("prompt", qid), "credentialId": caller["credentialId"]})
        page = self.page(iv, serve_truth=False)
        if page["question"] is None:
            violation = self.standing_violation(iv["interviewType"], self.latest(interview_id))
            if violation:
                raise Refusal("ANSWER_INVALID", violation["sentence"], {"questionId": violation["quorumQuestionId"]}, walkBackTo={"questionId": violation["quorumQuestionId"]})
            if iv["state"] == "in_progress":
                iv["state"] = "at_read_back"
            page["state"] = "at_read_back"
        return 200, page

    def tiered(self, iv: Dict[str, Any], latest: Dict[str, Dict[str, Any]]) -> bool:
        """The compiler's own test (onboardingcompiler.ts): a wallet account begun under the tiers' version, for any purpose but the agents'."""
        if iv["interviewType"] != "wallet_account" or (iv.get("catalogVersion") or 0) < TIERS_FROM_CATALOG_VERSION:
            return False
        purpose = (latest.get("W1") or {}).get("value", {}).get("choice")
        return purpose is not None and not purpose.startswith("Agents — the wallet account")

    def tiers_violation(self, iv: Dict[str, Any], latest: Dict[str, Dict[str, Any]]) -> Optional[Refusal]:
        """
        `assertSigningTiersConsistent` (Spec 92): judged over the answers that exist, at the read-back, the confirm and the compile — WO4
        not above WO3, then fewer than three people between WA1 and WO2 once the third party is named, each in the spec's own sentence.
        """
        if not self.tiered(iv, latest):
            return None
        value = lambda qid: (latest.get(qid) or {}).get("value") or {}  # noqa: E731
        holder_named = value("WO1").get("choice") == A.HOLDER_PERSON
        alone = value("WO3").get("cents") if holder_named and "WO3" in latest else None
        two = value("WO4").get("cents") if "WO4" in latest else None
        if two is None:
            return None
        if alone is not None and int(two) <= int(alone):
            return Refusal("CHARTER_INCOMPLETE", TIER_TWO_NOT_ABOVE_ONE, {"cause": TIER_TWO_NOT_ABOVE_ONE, "holderAloneUpToCents": alone, "twoSignaturesUpToCents": two},
                           walkBackTo={"questionId": "WO4"})
        third = next((e for e in (value("WO2").get("entries") or []) if str(e.get("email", "")).strip()), None)
        if third is None:
            return None
        named = {str(e.get("email", "")).strip().lower() for e in (value("WA1").get("entries") or []) if str(e.get("email", "")).strip()}
        named.add(str(third["email"]).strip().lower())
        if len(named) < 3:
            sentence = tiers_need_three_people(usd_figure(two), len(named))
            return Refusal("CHARTER_INCOMPLETE", sentence, {"cause": sentence, "named": str(len(named)), "twoSignaturesUpToCents": two}, walkBackTo={"questionId": "WA1"})
        return None

    def readback_lines_for_test(self, interview_id: str) -> List[Dict[str, Any]]:
        """The renderer alone, for a test: the lines as readback() would speak them, the standing checks set aside."""
        return self.readback(self.load_interview(interview_id), check_standing=False)

    def readback(self, iv: Dict[str, Any], check_standing: bool = True) -> List[Dict[str, Any]]:
        latest = self.latest(iv["id"])
        violation = self.standing_violation(iv["interviewType"], latest) if check_standing else None
        if violation:
            raise Refusal("ANSWER_INVALID", violation["sentence"], {"questionId": violation["quorumQuestionId"]}, walkBackTo={"questionId": violation["quorumQuestionId"]})
        tiers_refusal = self.tiers_violation(iv, latest) if check_standing else None
        if tiers_refusal:
            raise tiers_refusal
        tiered = self.tiered(iv, latest)
        purpose = (latest.get("W1") or {}).get("value", {}).get("choice") if iv["interviewType"] == "wallet_account" else None
        lines = [{"questionId": "REALM", "prompt": "Where this estate opens", "spoken": SANDBOX_SENTENCE, "synthetic": True}]
        for q in self.catalog(iv["interviewType"]):
            if not self.visible(q, latest) or q.id not in latest:
                continue
            v = latest[q.id]["value"]
            kind = q.kind
            if kind == "statement":
                spoken = "Stated and acknowledged."
            elif kind == "single_choice":
                spoken = v.get("choice") or ""
            elif kind == "multi_choice":
                choices = v.get("choices") or []
                spoken = ", ".join(choices) if choices else (
                    "No grants made — each level below you sees only its own level, and you see every level. The safest answer, and the one that stands until you change it."
                    if q.id == "B4" else "None chosen.")
            elif kind == "text":
                spoken = (v.get("text") or "").strip() or "Left blank."
            elif kind == "currency":
                # main (dff4c9a, e651616): no arm for the kind, so `default: JSON.stringify(v)` — '{"text":"AUD"}', as the
                # live run of 20 September 2026 heard it. Spec 88's spokenAnswer speaks the code.
                spoken = ((v.get("text") or "").strip() or "Left blank.") if self.currency_spoken_as_code else json.dumps(v, separators=(",", ":"), ensure_ascii=False)
            elif kind == "list":
                spoken = "; ".join(" — ".join(str(x) for x in e.values()) for e in (v.get("entries") or [])) or "No entries."
            elif kind == "money":
                cents = v.get("cents")
                # a written zero is a wall (Spec 90), spoken as such; every other figure exactly as before
                spoken = ("Left empty — no limit; the loosest possible answer." if cents is None
                          else "%s — nothing is paid under this rule until you write a figure." % usd_figure(cents) if int(cents) == 0
                          else "%s." % usd_figure(cents))
            elif kind == "person_or_none":
                # ONE PERSON, OR NO ONE (Spec 92, WO1): spokenAnswer, case 'person_or_none'
                person = v.get("person")
                if isinstance(person, dict) and str(person.get("email") or "").strip():
                    name = str(person.get("name") or "").strip()
                    spoken = ("%s — %s." % (name, person["email"].strip())) if name else "%s." % person["email"].strip()
                else:
                    spoken = ("%s." % v["choice"].strip()) if str(v.get("choice") or "").strip() else "No one chosen."
            elif kind == "percent":
                p = v.get("percent")
                spoken = ("Left empty — never halts on pace." if q.id == "T4" else "Left empty — no share is set.") if p is None else "%s per cent." % p
            elif kind == "count":
                c = v.get("count")
                spoken = "Left empty — no limit on how many." if c is None else "%s %s in a day." % ("{:,}".format(c), "payment" if c == 1 else "payments")
            else:
                spoken = ", ".join(v.get("people") or []) or "No one chosen."
            lines.append({"questionId": q.id, "prompt": PROMPTS.get(q.id, {}).get("prompt", q.id), "spoken": spoken})
            if q.id in ("C10", "WQ"):
                lines.append({"questionId": "HELD_WAIT", "prompt": "What happens while a payment waits for them", "spoken": HELD_PAYMENT_WAITS, "synthetic": True})
            # Spec 92's lines — each a line in the read-back, never a question, where the answer it speaks about is
            if q.id == "C19" and v.get("choice") == A.VENUE_NO:
                lines.append({"questionId": "C19_DOOR", "prompt": "What happens to a venue’s contract entered as a payee",
                              "spoken": "You answered No: such an address will be refused when entered.", "synthetic": True})
            if q.id == "WO1" and v.get("choice") == A.HOLDER_PERSON and str((v.get("person") or {}).get("email") or "").strip():
                person = v["person"]
                name = str(person.get("name") or "").strip() or person["email"].strip()
                lines.append({"questionId": "WO1_TITLE", "prompt": "What this person is called",
                              "spoken": "%s is this wallet’s %s: the one person who receives it and opens it on their own device." % (name, holder_title_for(purpose)), "synthetic": True})
            if tiered and q.id in ("P3", "O2") and v.get("cents") is not None:
                lines.append({"questionId": "HOLD_NOT_WRITTEN", "prompt": "What this figure does under the signing tiers", "spoken": TIER_HOLD_NOT_WRITTEN, "synthetic": True})
            if tiered and q.id == "WQ":
                lines.append({"questionId": "WQ_TIERS", "prompt": "What this number does under the signing tiers", "spoken": TIER_QUORUM_STANDS_ASIDE, "synthetic": True})
        if iv["interviewType"] == "policy":
            lines.append({"questionId": "ESTATE_CAPACITY", "prompt": "What this estate can move — added up, never asked", "spoken": "Nothing yet: no wallet account has been opened.", "synthetic": True})
        return lines

    def interview_digest(self, iv: Dict[str, Any]) -> str:
        latest = self.latest(iv["id"])
        parts = ["%s#%s#%s" % (qid, row["revision"], json.dumps(row["value"], separators=(",", ":"), ensure_ascii=False)) for qid, row in sorted(latest.items())]
        return hashlib.sha256(("%s|%s" % (iv["id"], "|".join(parts))).encode("utf-8")).hexdigest()

    def confirm(self, caller: Dict[str, Any], interview_id: str, body: Any) -> Tuple[int, Any]:
        body = body or {}
        for field in ("issuedAtMs", "response"):
            if field not in body:
                raise Malformed("%s: Required" % field)
        self.assert_fresh(body["issuedAtMs"])
        iv = self.load_interview(interview_id)
        tiers_refusal = self.tiers_violation(iv, self.latest(interview_id))
        if tiers_refusal:
            raise tiers_refusal
        digest = self.interview_digest(iv)
        expected = self.challenge("onboarding.confirm", "%s:%s|%s" % (digest, body["issuedAtMs"], caller["credentialId"]), body["issuedAtMs"])
        response = body["response"] or {}
        if not isinstance(response.get("id"), str) or not response["id"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "assertion carried no credential id"})
        stored = self.passkeys.get(response["id"])
        if not stored or stored["credentialId"] != caller["credentialId"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "the asserting passkey is not the confirming credential"})
        try:
            stored["signCount"] = PK.verify_assertion(response, expected, self.origin, self.rp_id, stored["publicKey"], stored["signCount"])
        except PK.PasskeyRefused as err:
            raise Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]})
        stored["lastAuthAtMs"] = body["issuedAtMs"]
        if iv["state"] != "at_read_back":
            if iv["state"] == "in_progress":
                raise Refusal("INTERVIEW_NOT_OPEN", "This interview is no longer at its read-back, so there is nothing on this page left to confirm — it has returned to its questions since this page was read. Continue the interview to reach a fresh read-back.",
                              {"state": iv["state"], "cause": "confirm happens at the read-back"}, road={"kind": "continue_interview", "label": "Continue the interview", "interviewId": interview_id})
            if iv["state"] in ("confirmed", "compiled"):
                raise Refusal("INTERVIEW_NOT_OPEN", "This interview is already confirmed under your passkey, so there is nothing on this page left to confirm — what remains is writing its charter to the platform. Finish the write, or reopen the interview to change an answer and confirm again.",
                              {"state": iv["state"], "cause": "this interview is already confirmed; writing its charter is what remains"})
            raise Refusal("INTERVIEW_NOT_OPEN", detail={"state": iv["state"], "cause": "confirm happens at the read-back"})
        iv["state"] = "confirmed"
        iv["confirmedByCredentialId"] = caller["credentialId"]
        return 200, {"interview": {"id": iv["id"], "state": "confirmed"}}

    def compile(self, caller: Dict[str, Any], interview_id: str) -> Tuple[int, Any]:
        iv = self.load_interview(interview_id)
        if iv["state"] not in ("confirmed", "compiled"):
            raise Refusal("INTERVIEW_NOT_OPEN", detail={"state": iv["state"], "cause": "the compiler reads only confirmed interviews"})
        tiers_refusal = self.tiers_violation(iv, self.latest(interview_id))
        if tiers_refusal:
            raise tiers_refusal
        latest = {qid: row["value"] for qid, row in self.latest(interview_id).items()}
        charter = self.compile_charter(iv["interviewType"], latest, iv.get("catalogVersion"))
        already_stood = False
        if iv["interviewType"] == "policy":
            # THE CHANGE GOVERNANCE IS ESTABLISHED ONCE (services/onboardingcompiler.ts, establishGovernance; the platform's
            # /v1/mutation-governance/establish refuses an account that already holds a whitelist_mutation roster). A later
            # compile leaves the rosters as they stand — and a seat bound at the platform by a press stays bound.
            if self.governance_established:
                already_stood = True
            else:
                self.seat_whitelist_roster(charter, latest)
                self.seat_change_roster(charter, latest)
                self.governance_established = True
        iv["compiledCharter"] = charter
        iv["state"] = "written"
        iv["writeReceipt"] = {"aapAccountId": AAP_ACCOUNT_ID, "policyEntryId": "pe-" + secrets.token_hex(4), "completedAt": self._now_iso(),
                              "governanceAlreadyStood": already_stood}
        iv["updatedAt"] = time.time()
        seat = self.complete_seat_on_charter_write(caller["credentialId"])
        return 200, {"charter": charter, "receipt": iv["writeReceipt"], "seat": seat}

    @staticmethod
    def roster_of(value: Optional[Dict[str, Any]]) -> List[str]:
        return list((value or {}).get("people") or [])

    def seat_whitelist_roster(self, charter: Dict[str, Any], latest: Dict[str, Dict[str, Any]]) -> None:
        """
        The whitelist_mutation roster as the compiler writes it (services/onboardingcompiler.ts): the members are
        governanceSignersFor's — the census (A8, `changeApprovers`) where it names anyone with a work email, else C11's
        people (`signers`) — one seat per person, named by email, the credential slot empty until a press binds it; the
        threshold is governanceRecordsFor's — C12's number over every family, or C12D's own behind a Yes on C12A. The
        `whitelist_roster` dial seats only the census keys named, so a roster smaller than its quorum can be met.
        """
        approval = charter.get("payeeApproval")
        if isinstance(approval, dict):
            # Spec 92: the roster the answer to C11A draws up, at its own count (payeeApprovalOf); unanswered, the change roster as before
            people = self.parse_roster(approval.get("roster") or [])
            threshold: Any = approval.get("quorum")
        else:
            people = self.parse_roster(charter.get("changeApprovers") or charter.get("signers") or [])
            choice = lambda qid: (latest.get(qid) or {}).get("choice")  # noqa: E731
            threshold = choice("C12D") if choice("C12A") == "Yes" and choice("C12D") else choice("C12")
        if self.whitelist_roster is not None:
            wanted = {A.PEOPLE[k].email.lower() for k in self.whitelist_roster}
            people = [p for p in people if p["email"].lower() in wanted]
        self.whitelist_seats = [{"user_id": p["email"], "display_name": p["name"], "credential_id": "", "status": "active"} for p in people]
        self.whitelist_threshold = int(threshold) if threshold else 1

    def seat_change_roster(self, charter: Dict[str, Any], latest: Dict[str, Dict[str, Any]]) -> None:
        """
        The multisig_mutation roster — who signs a change of who the approvers are, C12C's family — as the compiler writes it
        (governanceSignersFor: the census, A8, else C11's people; one seat per person named by email, the credential slot empty until a
        signature binds it) at C12's count (C12C's own behind a Yes on C12A). The `change_roster` dial seats only the census keys named.
        """
        people = self.parse_roster(charter.get("changeApprovers") or charter.get("signers") or [])
        if self.change_roster is not None:
            wanted = {A.PEOPLE[k].email.lower() for k in self.change_roster}
            people = [p for p in people if p["email"].lower() in wanted]
        choice = lambda qid: (latest.get(qid) or {}).get("choice")  # noqa: E731
        threshold = choice("C12C") if choice("C12A") == "Yes" and choice("C12C") else choice("C12")
        self.change_seats = [{"user_id": p["email"], "display_name": p["name"], "credential_id": "", "status": "active"} for p in people]
        self.change_threshold = int(threshold) if threshold else 1

    @staticmethod
    def roster_entry(name: str, email: str) -> str:
        """`rosterEntry`: the one shape every roster on the charter carries, "Name <email>"."""
        return "%s <%s>" % (name.strip(), email.strip()) if name.strip() else email.strip()

    def payee_approval_of(self, latest: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """`payeeApprovalOf` (onboardingcompiler.ts, Spec 92): the one reading of C11A; null where never answered."""
        choice = lambda qid: (latest.get(qid) or {}).get("choice")  # noqa: E731
        answer = choice("C11A")
        if answer is None:
            return None
        payment_approvers = self.roster_of(latest.get("C11"))
        if answer == A.PAYEE_APPROVAL_PAYMENT_APPROVERS:
            return {"answer": "payment_approvers", "roster": payment_approvers, "quorum": int(choice("C10")) if choice("C10") else None,
                    "rosterQuestionId": "C11", "quorumQuestionId": "C10"}
        if answer == A.PAYEE_APPROVAL_CHANGE_APPROVERS:
            census = [self.roster_entry(str(e.get("name", "")), str(e.get("email", ""))) for e in ((latest.get("A8") or {}).get("entries") or []) if str(e.get("email", "")).strip()]
            c12d = choice("C12D") if choice("C12A") == "Yes" else None
            c12 = choice("C12")
            return {"answer": "change_approvers", "roster": census if census else payment_approvers,
                    "quorum": int(c12d) if c12d else (int(c12) if c12 else None),
                    "rosterQuestionId": "A8" if census else "C11", "quorumQuestionId": "C12D" if c12d else "C12"}
        if answer == A.PAYEE_APPROVAL_CFO:
            cfo = next(({"name": str(e.get("name", "")).strip(), "email": str(e.get("email", "")).strip()} for e in ((latest.get("C11C") or {}).get("entries") or [])
                        if str(e.get("email", "")).strip()), None)
            if cfo is None:
                raise Refusal("CHARTER_INCOMPLETE", detail={"cause": "C11A chose the CFO’s authority to approve a new payee, but C11C names nobody"}, walkBackTo={"questionId": "C11C"})
            return {"answer": "cfo", "roster": [self.roster_entry(cfo["name"], cfo["email"])], "quorum": 1, "rosterQuestionId": "C11C", "quorumQuestionId": "C11A", "cfo": cfo}
        raise Refusal("CHARTER_INCOMPLETE", detail={"cause": "C11A holds “%s”, which is not an answer this estate offers to who approves a new payee" % answer}, walkBackTo={"questionId": "C11A"})

    @staticmethod
    def venue_contracts_of(latest: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """`venueContractsOf`: null where never asked, which every reader takes as the founder's default, accepted."""
        answer = (latest.get("C19") or {}).get("choice")
        if answer is None:
            return None
        if answer == A.VENUE_YES:
            return "accepted"
        if answer == A.VENUE_NO:
            return "refused"
        raise Refusal("CHARTER_INCOMPLETE", detail={"cause": "C19 holds “%s”, which is not an answer this estate offers to whether a payee may be a venue’s contract" % answer}, walkBackTo={"questionId": "C19"})

    def read_wallet_people(self, latest: Dict[str, Dict[str, Any]], purpose: Optional[str]) -> Dict[str, Any]:
        """`readWalletPeople` (Spec 92): WO1 to WO4, refusing in words where an answer is missing, each refusal naming its page."""
        def refuse(question_id: str, cause: str) -> None:
            raise Refusal("CHARTER_INCOMPLETE", detail={"cause": cause}, walkBackTo={"questionId": question_id})
        wo1 = latest.get("WO1") or {}
        if not isinstance(wo1.get("choice"), str):
            refuse("WO1", "who holds this wallet was not answered; a wallet is held by one named person or by no one")
        if wo1["choice"] == A.HOLDER_NO_ONE:
            holder: Dict[str, Any] = {"held": "by_no_one"}
        elif wo1["choice"] == A.HOLDER_PERSON:
            person = wo1.get("person") or {}
            name = str(person.get("name") or "").strip()
            email = str(person.get("email") or "").strip()
            if not name or not email:
                refuse("WO1", "the holder must be named in full, with a work email, or the answer is No one")
            holder = {"held": "by_person", "name": name, "email": email, "title": holder_title_for(purpose)}
        else:
            refuse("WO1", "“%s” is not an answer this estate offers to who holds the wallet" % wo1["choice"])
        entry = next((e for e in ((latest.get("WO2") or {}).get("entries") or []) if str(e.get("email", "")).strip()), None)
        if entry is None:
            refuse("WO2", "the third party to this wallet’s activation and its largest payments was not named")
        third = {"name": str(entry.get("name") or "").strip(), "surname": str(entry.get("surname") or "").strip(),
                 "email": str(entry.get("email") or "").strip(), "title": str(entry.get("title") or "").strip()}
        if not third["name"]:
            refuse("WO2", "the third party needs a full name")
        if third["title"] not in A.THIRD_PARTY_TITLES:
            refuse("WO2", "the third party’s title must be one of %s; “%s” is not one of them" % (", ".join(A.THIRD_PARTY_TITLES), third["title"]))
        alone = (latest.get("WO3") or {}).get("cents") if holder["held"] == "by_person" else None
        if holder["held"] == "by_person" and alone is None:
            refuse("WO3", "up to what amount the holder may pay alone was not answered; the field arrives written and cannot be blank")
        two = (latest.get("WO4") or {}).get("cents")
        if two is None:
            refuse("WO4", "up to what amount two signatures are enough was not answered; the field arrives written and cannot be blank")
        return {"holder": holder, "thirdParty": third, "holderAloneUpToCents": alone, "twoSignaturesUpToCents": two}

    def compile_charter(self, interview_type: str, latest: Dict[str, Dict[str, Any]], catalog_version: Optional[int] = None) -> Dict[str, Any]:
        is_account = interview_type == "wallet_account"
        choice = lambda qid: (latest.get(qid) or {}).get("choice")  # noqa: E731
        cents = lambda qid: (latest.get(qid) or {}).get("cents")  # noqa: E731
        purpose = choice("W1") if is_account else None
        name = ((latest.get("WN") if is_account else latest.get("A1")) or {}).get("text", "").strip()
        if not name:
            raise Refusal("CHARTER_INCOMPLETE", detail={"cause": "the interview carries no name"}, walkBackTo={"questionId": "WN" if is_account else "A1"})
        approver_entries = [e for e in ((latest.get("WA1") or {}).get("entries") or []) if str(e.get("email", "")).strip()]
        signers = (["%s <%s>" % (e.get("name", "").strip(), e.get("email", "").strip()) if e.get("name", "").strip() else e.get("email", "").strip() for e in approver_entries]
                   if is_account and approver_entries else self.roster_of(latest.get("C11")))
        census = ["%s <%s>" % (e.get("name", "").strip(), e.get("email", "").strip()) if e.get("name", "").strip() else e.get("email", "").strip()
                  for e in ((latest.get("A8") or {}).get("entries") or []) if str(e.get("email", "")).strip()]
        quorum_text = choice("WQ") if is_account else choice("C10")
        quorum = int(quorum_text) if quorum_text else None
        if is_account and not signers:
            raise Refusal("CHARTER_INCOMPLETE", detail={"cause": "no approvers are named; no policy exists without named people"}, walkBackTo={"questionId": "WA1"})
        treasury = bool(purpose and purpose.startswith("Treasury"))
        agent = bool(purpose and purpose.startswith("Agents"))
        payroll = bool(purpose and purpose.startswith("Payroll"))
        trading = bool(purpose and purpose.startswith("Trading"))
        # Spec 92: the wallet's people and tiers, for a wallet account begun under version 14 or later, for any purpose but the agents'
        tiered = is_account and not agent and (catalog_version or 0) >= TIERS_FROM_CATALOG_VERSION
        wallet_people = self.read_wallet_people(latest, purpose) if tiered else None
        if wallet_people is not None:
            # THE THIRD PARTY IS A SIGNER beside WA1's people — once, by email
            third = wallet_people["thirdParty"]
            if not any(p["email"].lower() == third["email"].lower() for p in self.parse_roster(signers)):
                signers = list(signers) + [self.roster_entry(" ".join(part for part in (third["name"], third["surname"]) if part), third["email"])]
        deny = (cents("T1") if treasury else cents("AG2") if agent else None) if is_account else None
        hold = (cents("P3") if payroll else cents("O2")) if is_account else None
        daily = (cents("AG3") if agent else (cents("O1") if cents("O1") is not None else cents("X2"))) if is_account else None
        if treasury and deny is None:
            raise Refusal("CHARTER_INCOMPLETE", detail={"cause": "the treasury ceiling is mandatory and was left empty"}, walkBackTo={"questionId": "T1"})
        modes = {"Yes": "hold_non_listed", "List only": "allow_only", "Anyone, freely": "none", "No — the list only": "allow_only", "Pause anywhere new for approval": "hold_non_listed",
                 "Yes — always": "hold_non_listed", "Only above the usual approval band": "none"}
        destination = choice("X4") if trading else choice("T3") if treasury else choice("O3") if is_account else None
        mode = None if (not is_account or payroll or agent) else modes.get(destination or "", "hold_non_listed")
        if payroll:
            mode = "allow_only"
        if agent:
            mode = "allow_only"
        chosen = list(((latest.get("X1") if is_account else latest.get("C9")) or {}).get("choices") or [])
        recorded = sorted({"aeredium"} | {c.lower() for c in chosen})
        wa2 = choice("WA2")
        requester = ({A.WA2_YES: True, A.WA2_NO: False}.get(wa2) if is_account else (None if choice("C15") is None else choice("C15") == "Yes"))
        contact_entry = next(({"name": e.get("name", "").strip(), "email": e.get("email", "").strip()} for e in ((latest.get("C18") or {}).get("entries") or []) if str(e.get("email", "")).strip()), None)
        c12 = choice("C12")
        charter = {
            "interviewType": interview_type, "name": name, "purpose": purpose, "allowedChains": ["aeredium-testnet"], "recordedChains": recorded, "realm": "sandbox",
            "whitelistMode": mode, "whitelistEntries": [], "quorum": quorum, "signers": signers, "changeApprovers": census if not is_account else None,
            "isAgentsAccount": agent, "principal": (self.roster_of(latest.get("P4")) + self.roster_of(latest.get("O4")) + self.roster_of(latest.get("AG6")) + [None])[0] if is_account else None,
            "amountsUsdCents": {"denyCeiling": deny, "holdOverPerTx": hold, "dailyTotal": daily, "weeklyTotal": None, "monthlyTotal": None},
            "requesterCountsAsSigner": requester, "securityContact": contact_entry if not is_account else None,
            "mutationGovernance": ([{"scope": "all", "quorum": int(c12)}] if c12 else []) if not is_account else [],
            "visibility": {"grants": []}, "velocity": {"multiplier": None, "action": None}, "compilerVersion": "double",
            # Spec 92: null on a wallet-account interview for the two Part C answers; absent on every charter the tiers do not reach
            "payeeApproval": None if is_account else self.payee_approval_of(latest),
            "payeeVenueContracts": None if is_account else self.venue_contracts_of(latest),
        }
        if wallet_people is not None:
            charter["holder"] = wallet_people["holder"]
            charter["signingTiers"] = {"holderAloneUpToCents": wallet_people["holderAloneUpToCents"], "twoSignaturesUpToCents": wallet_people["twoSignaturesUpToCents"],
                                       "thirdParty": wallet_people["thirdParty"], "holdNotWritten": None if hold is None else TIER_HOLD_NOT_WRITTEN}
        return charter

    def charter_standing(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        self.require_caller(headers, "viewer")
        written = [iv for iv in self.interviews.values() if iv["interviewType"] == "policy" and iv["state"] == "written"]
        if not written:
            return 200, {"standsWritten": False, "inForceSince": None}
        newest = sorted(written, key=lambda i: i["updatedAt"])[-1]
        return 200, {"standsWritten": True, "inForceSince": newest["writeReceipt"]["completedAt"]}

    def newest_written_charter(self) -> Optional[Dict[str, Any]]:
        written = [iv for iv in self.interviews.values() if iv["state"] == "written" and iv["compiledCharter"]]
        if not written:
            return None
        return sorted(written, key=lambda i: i["updatedAt"])[-1]["compiledCharter"]

    def newest_written_policy_charter(self) -> Optional[Dict[str, Any]]:
        """The estate's written policy charter, which the payee door reads for C19's answer (services/payees.ts)."""
        written = [iv for iv in self.interviews.values() if iv["interviewType"] == "policy" and iv["state"] == "written" and iv["compiledCharter"]]
        if not written:
            return None
        return sorted(written, key=lambda i: i["updatedAt"])[-1]["compiledCharter"]

    # -- seats (approverseats.ts) ------------------------------------------------------------------------
    @staticmethod
    def parse_roster(roster: Sequence[str]) -> List[Dict[str, str]]:
        out = []
        for entry in roster or []:
            m = re.match(r"^(.*?)\s*<([^>]+)>$", entry.strip())
            name = m.group(1).strip() if m else ""
            email = (m.group(2) if m else entry).strip()
            if email:
                out.append({"name": name, "email": email})
        return out

    def credential_holders(self) -> Dict[str, List[str]]:
        """`credentialHolders` (services/approverseats.ts): every passkey bound here, by the credential it speaks for, as the distinct labels the keys were enrolled under, oldest first."""
        holders: Dict[str, List[str]] = {}
        for row in self.passkeys.values():
            names = holders.setdefault(row["credentialId"], [])
            if row["label"] not in names:
                names.append(row["label"])
        return holders

    def names_by_email(self) -> Dict[str, List[str]]:
        """The display names an address's redeemed invitations were minted in: the labels of this person's OWN keys, by construction."""
        out: Dict[str, List[str]] = {}
        for row in self.invites.values():
            if row["redeemedAt"] and row["revokedAt"] is None and row.get("email"):
                names = out.setdefault(row["email"].strip().lower(), [])
                if row["displayName"] not in names:
                    names.append(row["displayName"])
        return out

    def enrolled_by_email(self) -> Dict[str, List[str]]:
        """
        `enrolmentRecords(...).byEmail` (services/approverseats.ts): every credential this estate can honestly attach to an address —
        a redeemed, not withdrawn invitation's, that a passkey bound here speaks for (Spec 58), and not one the estate recorded as
        replaced (Spec 91, item 4, unless the estate is the one before Spec 91). One person invited twice onto one credential is one.
        """
        holders = self.credential_holders()
        out: Dict[str, List[str]] = {}
        for row in sorted(self.invites.values(), key=lambda r: r.get("_redeemedEpoch") or 0):
            if not row["redeemedAt"] or row["revokedAt"] is not None or not row.get("email"):
                continue
            email = row["email"].strip().lower()
            credential_id = row["credentialId"]
            if not credential_id or credential_id not in holders:
                continue
            if not self.before_spec_91 and (email, credential_id) in self.retired:
                continue
            held = out.setdefault(email, [])
            if credential_id not in held:
                held.append(credential_id)
        return out

    def others_holding(self, credential_id: str, email: str) -> List[str]:
        """`othersHolding` (services/approverseats.ts, Spec 91): the other people whose keys speak for a credential; empty means the person's own."""
        names = self.credential_holders().get(credential_id, [])
        own = self.names_by_email().get(email.strip().lower(), [])
        invited_onto_it = credential_id in self.enrolled_by_email().get(email.strip().lower(), [])
        if own and invited_onto_it:
            return [n for n in names if n not in own]
        return names[1:] if len(names) > 1 else []

    def signer_email_of(self, credential_id: str) -> Optional[str]:
        """
        Whose seat a press says it is (services/payees.ts, signAsPresser → signerEmailOf → emailOfCredential). Before Spec 91: the first
        address the register attached the credential to. Since Spec 91 (addressOfCredential): ONE address, and nobody else's key on the
        credential — else null, and the platform judges the credential alone.
        """
        by_email = self.enrolled_by_email()
        addresses = [email for email, held in by_email.items() if credential_id in held]
        if self.before_spec_91:
            return addresses[0] if addresses else None
        if len(addresses) != 1:
            return None
        return addresses[0] if not self.others_holding(credential_id, addresses[0]) else None

    def earlier_bindings_of(self, claimed: Dict[str, Any]) -> List[str]:
        """`earlierBindingsOf` (services/invites.ts, Spec 91): the credentials earlier redeemed, not withdrawn invitations of the same address enrolled, other than this one's."""
        wanted = (claimed.get("email") or "").strip().lower()
        if not wanted:
            return []
        replaced: List[str] = []
        for row in sorted(self.invites.values(), key=lambda r: r.get("_redeemedEpoch") or 0):
            if row["id"] == claimed["id"] or not row["redeemedAt"] or row["revokedAt"] is not None:
                continue
            if (row.get("email") or "").strip().lower() != wanted:
                continue
            credential_id = row["credentialId"]
            if not credential_id or credential_id == claimed["credentialId"] or credential_id in replaced:
                continue
            replaced.append(credential_id)
        return replaced

    def mark_shared_credentials(self, rows: Sequence[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        `markSharedCredentials` (services/invites.ts, Spec 91, item 4): one mark per person, on the newest redeemed invitation of each
        address (an invitation with no address is its own person), naming every other label on its credential; nothing on a row not
        redeemed or naming no credential.
        """
        holders = self.credential_holders()

        def person_of(row: Dict[str, Any]) -> str:
            address = (row.get("email") or "").strip().lower()
            return address or "#%s" % row["id"]

        redeemed = [r for r in rows if r["state"] == "redeemed" and r.get("credentialId")]
        own_names: Dict[str, List[str]] = {}
        for row in redeemed:
            names = own_names.setdefault(person_of(row), [])
            if row["displayName"] not in names:
                names.append(row["displayName"])
        marks: Dict[str, List[str]] = {}
        seen: set = set()
        for row in sorted(redeemed, key=lambda r: r.get("_redeemedEpoch") or 0, reverse=True):
            person = person_of(row)
            if person in seen:
                continue
            seen.add(person)
            others = [n for n in holders.get(row["credentialId"], []) if n not in own_names.get(person, [])]
            if others:
                marks[row["id"]] = others
        return marks

    def complete_seat_on_redemption(self, credential_id: str, email: Optional[str], display_name: str = "") -> Optional[Dict[str, Any]]:
        """
        `completeSeatOnRedemption` → `seatCompletesItself` (services/approverseats.ts): the charter names them or it does not; since
        Spec 91 a credential other people's keys speak for is not seated by a road nobody pressed, and the page says the road on. An
        estate before Spec 58's count 3 says nothing of a seat at all.
        """
        if not self.seat_completes_on_redemption:
            return None
        if not email:
            return {"charterNamedThem": False, "granted": False, "note": None}
        charter = self.newest_written_charter()
        if not charter:
            return {"charterNamedThem": False, "granted": False, "note": None}
        wanted = email.strip().lower()
        person = next((p for p in self.parse_roster(charter["signers"]) if p["email"].lower() == wanted), None)
        if person is None:
            return {"charterNamedThem": False, "granted": False, "note": None}
        if not self.before_spec_91:
            shared = self.others_holding(credential_id, wanted)
            if shared:
                self.audit.append("approver_seat.grant_refused %s APPROVER_SEAT_CREDENTIAL_SHARED via invite_redemption" % credential_id)
                return {"charterNamedThem": True, "granted": False, "note": approver_seat_shared_sentence(person["name"] or display_name, shared)}
        if credential_id not in self.second_approvers:
            self.second_approvers.append(credential_id)
            self.audit.append("approver_seat.granted %s via invite_redemption" % credential_id)
        return {"charterNamedThem": True, "granted": True, "note": None}

    def complete_seat_on_charter_write(self, credential_id: str) -> Dict[str, Any]:
        """
        `completeSeatOnCharterWrite` → `seatCompletesItself` (services/approverseats.ts, Spec 81 as Spec 91 left it): the CONFIRMING credential is
        seated where the newest written charter names an address the estate attributes to it — `addressesOfCaller`: the invitation it redeemed, else
        the account's own address for a key the register attaches to nobody and no second key speaks for (the founder's, where `account_email` is
        known) — never by name, never a guess between candidates; a credential other people's keys speak for is refused by name, audited, never
        thrown. This is how the Treasury's founder becomes its one payment approver (Spec T14 §2).
        """
        no_seat = {"charterNamedThem": False, "granted": False, "note": None}
        charter = self.newest_written_charter()
        if not charter:
            return no_seat
        mine = self.addresses_of_caller(credential_id)
        person = next((p for p in self.parse_roster(charter.get("signers") or []) if p["email"].lower() in mine), None)
        if person is None:
            return no_seat
        wanted = person["email"].lower()
        if not self.before_spec_91:
            shared = self.others_holding(credential_id, wanted)
            if shared:
                self.audit.append("approver_seat.grant_refused %s APPROVER_SEAT_CREDENTIAL_SHARED via charter_write" % credential_id)
                return {"charterNamedThem": True, "granted": False, "note": approver_seat_shared_sentence(person["name"] or wanted, shared)}
        if credential_id not in self.second_approvers:
            self.second_approvers.append(credential_id)
            self.audit.append("approver_seat.granted %s via charter_write" % credential_id)
        return {"charterNamedThem": True, "granted": True, "note": None}

    def seats(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author")
        return 200, self.seats_view(caller)

    def seats_view(self, caller: Dict[str, Any]) -> Dict[str, Any]:
        charter = self.newest_written_charter()
        if not charter:
            return {"charterStands": False, "seats": [], "summary": "", "policyEntryId": None}
        if self.seats_override is not None:
            # AER 360 Spec 105: the seat view carries onRoster (and rosterSaid where null). The listed people are the test's, in the
            # Spec-105 shape; onRoster is computed from the live rosters where the spec says "compute", so it is the estate's own truth.
            seats = [self._override_seat_view(spec) for spec in self.seats_override]
            return {"charterStands": True, "seats": seats, "summary": "%d seated" % sum(1 for s in seats if s["state"] == "seated"), "policyEntryId": "pe-estate"}
        by_email = self.enrolled_by_email()
        seats = []
        for person in self.parse_roster(charter["signers"]):
            candidates = by_email.get(person["email"].lower(), [])
            held = next((c for c in candidates if c in self.second_approvers), None)
            state = "seated" if held is not None else ("enrolled_not_seated" if candidates else "not_enrolled")
            seats.append({"name": person["name"], "email": person["email"], "state": state,
                          "credentialId": held if held is not None else (candidates[0] if len(candidates) == 1 else None),
                          "ambiguous": held is None and len(candidates) > 1, "invitation": None, "selfSeatable": False})
        return {"charterStands": True, "seats": seats, "summary": "%d seated" % sum(1 for s in seats if s["state"] == "seated"), "policyEntryId": "pe-estate"}

    def _override_seat_view(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """One seat of the override, in the Spec 105 shape: state, credentialId, ambiguous, and onRoster (computed from the rosters where the spec says so)."""
        email = spec.get("email")
        credential_id = spec.get("credentialId")
        onroster = spec.get("onRoster")
        roster_said = spec.get("rosterSaid")
        if onroster == "compute":
            onroster, roster_said = self.seat_on_roster(email, credential_id)
        seat = {"name": spec.get("name") or email, "email": email, "state": spec.get("state", "seated"),
                "credentialId": credential_id, "ambiguous": bool(spec.get("ambiguous")),
                "invitation": None, "selfSeatable": False, T.SEAT_ON_ROSTER: onroster}
        if onroster is None:
            seat[T.SEAT_ROSTER_SAID] = roster_said if roster_said is not None else "no roster names this person"
        return seat

    def seat_on_roster(self, email: Any, credential_id: Any) -> Tuple[Optional[bool], Optional[str]]:
        """
        AER 360 Spec 105 §1's shared predicate, in the double (services/approverseats.ts, `onRoster`): read the active rosters once and,
        for a seat whose credentialId is not null, answer true where on every active roster the active signer for this email names this
        credential (or another credential still enrolled for the person — "another of their passkeys"); false where some roster names the
        signer under a credential that is no longer enrolled for the person (exactly `rebindRosterSeats`' `moving` filter); null where the
        credential is null or no roster names the person at all, with the platform's sentence in rosterSaid.
        """
        if not credential_id:
            return None, "the seat names no credential"
        folded = str(email or "").strip().lower()
        enrolled = set(self.enrolled_by_email().get(folded, []))
        named = False
        stale = False
        for roster in self.rosters():
            if not roster.get("active"):
                continue
            for signer in roster["signers"]:
                if signer["status"] != "active" or signer["user_id"].strip().lower() != folded:
                    continue
                named = True
                other = signer["credential_id"]
                if other and other != credential_id and other not in enrolled:
                    stale = True  # a credential this person no longer holds — the moving filter's seat
        if not named:
            return None, "no roster names this person"
        return (False, None) if stale else (True, None)

    def grant_seat(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        email = str((body or {}).get("email", "")).strip()
        if not email:
            raise Malformed("email: String must contain at least 1 character(s)")
        charter = self.newest_written_charter()
        person = next((p for p in self.parse_roster((charter or {}).get("signers") or []) if p["email"].lower() == email.lower()), None)
        if person is None:
            raise Refusal("APPROVER_SEAT_NOT_IN_CHARTER", detail={"email": email.lower()})
        candidates = self.enrolled_by_email().get(email.lower(), [])
        if not candidates:
            raise Refusal("APPROVER_SEAT_NOT_ENROLLED", detail={"email": email.lower()})
        if len(candidates) > 1:
            raise Refusal("APPROVER_SEAT_AMBIGUOUS", detail={"email": email.lower(), "credentials": str(len(candidates))})
        credential_id = candidates[0]
        if not self.before_spec_91:
            # THEIR OWN, OR NOBODY'S (Spec 91, item 2): a credential other people's keys speak for is refused a seat, by name.
            shared = self.others_holding(credential_id, email)
            if shared:
                raise Refusal("APPROVER_SEAT_CREDENTIAL_SHARED", approver_seat_shared_sentence(person["name"], shared),
                              {"email": email.lower(), "sharedWith": ", ".join(shared)}, provenance={"source": "enrollment_invites"})
        if credential_id not in self.second_approvers:
            self.second_approvers.append(credential_id)
            self.audit.append("approver_seat.granted %s via people_room" % credential_id)
        # A SEAT FOLLOWS ITS PERSON (Spec 95, count 2; grantApproverSeat): the credential just seated is the one every roster seat naming this
        # address must count — a seat still bound to a credential they no longer hold is moved, or held by the client's own governance as a ceremony
        self.rebind_roster_seats(person["email"], person["name"], credential_id, caller["credentialId"], "seat_grant")
        return 200, self.seats_view(caller)

    # -- invites (routes/invites.ts) -----------------------------------------------------------------------
    def mint_invite(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        body = body or {}
        role = body.get("role")
        if role not in ("viewer", "author", "principal"):
            raise Malformed("role: Invalid enum value. Expected 'viewer' | 'author' | 'principal', received '%s'" % role)
        display_name = str(body.get("displayName", "")).strip()
        email = str(body.get("email", "")).strip()
        if not display_name:
            raise Malformed("displayName: String must contain at least 1 character(s)")
        if "@" not in email:
            raise Malformed("email: Invalid email")
        if role == "principal":
            raise Refusal("INVITE_ROLE_NOT_AVAILABLE", detail={"role": "principal", "cause": "a principal receives a wallet, and the wallet flow is not built yet (spec U1, unification). Invite this person as an author or a viewer today, or wait for the principal road."})
        standing = next((r for r in self.invites.values() if (r.get("email") or "").lower() == email.lower() and r["redeemedAt"] is None and r["revokedAt"] is None), None)
        if standing:
            raise Refusal("INVITE_ALREADY_STANDING", "An invitation to %s (%s) already stands, minted %s and expiring %s. Resend it, or withdraw it first." % (
                standing["displayName"], standing["email"], standing["createdAt"], standing["expiresAt"]),
                          {"inviteId": standing["id"], "invitedEmail": standing["email"], "invitedName": standing["displayName"], "expiresAt": standing["expiresAt"]})
        if role == "viewer":
            credential_id = "cred-viewer-" + secrets.token_hex(4)
            self.credentials[credential_id] = {"access": "audit", "name": "Viewer — read only — %s" % display_name, "entry": "pe-viewer"}
        elif self.before_spec_91:
            # Before Spec 91: an author invitation enrols the ONE role-bearing credential the account carries (services/invites.ts at e651616).
            role_bearing = [c for c, e in self.credentials.items() if "sign" in e["access"] or "audit" in e["access"]]
            role_bearing = [c for c in role_bearing if c not in (cv for cv in self.credentials if self.credentials[cv]["access"] == "audit")]
            if len(role_bearing) != 1:
                raise Refusal("INVITE_INVALID", detail={"cause": "the account carries several role-bearing credentials; this invite must name which one it enrols", "candidates": ", ".join(role_bearing)})
            credential_id = role_bearing[0]
        else:
            # Spec 91 (services/invites.ts, authorshipEntry, mintAuthorCredential): a credential of the person's own on the ONE in-force
            # policy entry bearing `sign` that an active credential holds; several are a refusal listing entries and credentials.
            entries = [(self.authorship_entry["id"], self.authorship_entry["name"], [c for c, e in self.credentials.items() if e.get("entry") == self.authorship_entry["id"] and "sign" in e["access"]])]
            if self.second_authorship_entry:
                entries.append(("pe-cfo", "Casey CFO (author)", ["cred-cfo"]))
            if len(entries) != 1:
                raise Refusal("INVITE_INVALID", detail={
                    "cause": "the account carries several policy entries bearing authorship; this invite must name which credential it enrols",
                    "candidates": ", ".join(c for _, _, held in entries for c in held), "entries": ", ".join("%s (%s)" % (eid, name) for eid, name, _ in entries)},
                    provenance={"source": "aap_policy"})
            entry_id, entry_name, _ = entries[0]
            credential_id = str(uuid.uuid4())
            self.credentials[credential_id] = {"access": "sign+audit", "name": "%s — %s" % (entry_name, display_name), "entry": entry_id}
            invited_key = next((k for k, p in A.PEOPLE.items() if p.email.lower() == email.lower()), None)
            if invited_key in self.platform_names_approver and credential_id not in self.second_approvers:
                self.second_approvers.append(credential_id)  # an operator at the platform's console, outside the estate's seat road
        token = secrets.token_urlsafe(32)
        row = {"id": "inv-" + secrets.token_hex(6), "displayName": display_name, "email": email, "phone": body.get("phone"), "role": role, "note": body.get("note"),
               "state": "pending", "credentialId": credential_id, "createdAt": self._now_iso(), "expiresAt": self._iso(time.time() + 72 * 3600),
               "redeemedAt": None, "revokedAt": None, "revokedByCredentialId": None, "dispatchedAt": None,
               "dispatchDetail": "This deployment has no mail lane, so nothing was sent. Copy the link and send it to this person yourself."}
        self.invites[hashlib.sha256(token.encode()).hexdigest()] = row
        self.audit.append("invite.minted %s %s by %s enrolsCredentialId %s mintedCredentialId %s" % (
            role, email, caller["credentialId"], credential_id, "null" if (role == "author" and self.before_spec_91) else credential_id))
        if self.clock is not None and self.invite_seconds:
            # routes/invites.ts: the invitation is minted first, then the email's dispatch is awaited, then the route answers
            self.clock.sleep(self.invite_seconds)
        return 201, {"invite": {k: row[k] for k in ("id", "displayName", "email", "phone", "role", "state", "credentialId", "expiresAt")},
                     "url": "%s/invite#%s" % (self.origin, token), "expiresAt": row["expiresAt"], "credentialId": credential_id, "accountName": self.workspace["name"],
                     "dispatch": {"sent": False, "at": None, "reason": row["dispatchDetail"]}}

    def list_invites(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "viewer")
        held = caller["roles"]
        if "author" not in held and "approver" not in held:
            raise Refusal("ROLE_NOT_GRANTED", role_not_granted_sentence(self.workspace["name"], held, "author or approver"),
                          {"workspace": self.workspace["name"], "held": ",".join(held), "required": "author or approver",
                           "cause": "the invitation register names the people your organisation has let in, and who let them in. An author or an approver may read it."})
        rows = sorted(self.invites.values(), key=lambda r: (r["createdAt"], r["id"]), reverse=True)
        wire = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
        if self.before_spec_91:
            return 200, {"invites": wire}
        marks = self.mark_shared_credentials(rows)
        return 200, {"invites": [dict(view, sharesCredentialWith=marks.get(view["id"], [])) for view in wire]}

    # -- payees (routes/payees.ts, payeeaddress.ts) -----------------------------------------------------------
    def create_payee(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        body = body or {}
        display_name = str(body.get("displayName", "")).strip()
        if not display_name:
            raise Malformed("displayName: String must contain at least 1 character(s)")
        if body.get("defaultAsset") and body["defaultAsset"] not in KNOWN_ASSETS:
            raise Refusal("ASSET_UNKNOWN", detail={"asset": body["defaultAsset"]})
        if body.get("defaultChain") and body["defaultChain"] not in KNOWN_CHAINS:
            raise Refusal("CHAIN_NOT_SUPPORTED", detail={"chain": body["defaultChain"]})
        stored = []
        for a in body.get("addresses") or []:
            if a.get("chain") not in KNOWN_CHAINS:
                raise Refusal("CHAIN_NOT_SUPPORTED", detail={"chain": a.get("chain")})
            address = str(a.get("address", "")).strip()
            if a["chain"] == "solana":
                fits = re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address) is not None
            else:
                fits = re.match(r"^0x[0-9a-fA-F]{40}$", address) is not None
            if not fits:
                named = {"ethereum": "Ethereum", "solana": "Solana"}.get(a["chain"], a["chain"])
                expected = ("an address is 0x followed by exactly 40 hexadecimal characters" if a["chain"] != "solana"
                            else "an address is 32 to 44 base58 characters, and base58 leaves out the digit zero, capital O, capital I and lower-case L")
                raise Refusal("ADDRESS_MALFORMED", "That is not an address %s can pay, so nothing was saved. On %s, %s." % (named, named, expected),
                              {"field": "address", "chain": a["chain"], "address": address, "expected": expected}, provenance={"source": "chain_registry", "reference": a["chain"]})
            if self.refuses_venue_contract is True and address.lower() == T.venue_address_for_probe()["address"].lower():
                # Spec T8's stand-in: a door that refuses the probe address whatever its charter says, under the code the estate used for
                # an address it would not propose — since Spec 92 an estate refusing against a charter that says accepted
                raise Refusal("ADDRESS_PROPOSAL_REFUSED", VENUE_STIPULATION,
                              {"chain": a["chain"], "address": address,
                               "cause": "a stipulation this door applies whatever the charter says; this double stands in for an estate that does"},
                              provenance={"source": "charter"})
            if self.refuses_venue_contract is None:
                # THE DOOR (Spec 92, services/payees.ts assertPayeeIsNotVenueContract): the written policy charter is read, and where it
                # answered No at C19 and the address is on the engine's venue table, the payee is refused in the spec's sentence
                policy = self.newest_written_policy_charter()
                venue = venue_of_destination(a["chain"], address) if (policy or {}).get("payeeVenueContracts") == "refused" else ""
                if venue:
                    raise Refusal("PAYEE_IS_VENUE_CONTRACT", payee_is_venue_contract_sentence(VENUE_NAMES.get(venue, venue), a["chain"]),
                                  {"venue": venue, "chain": a["chain"], "address": address, "charterQuestionId": VENUE_CONTRACT_QUESTION_ID},
                                  provenance={"source": "charter", "reference": VENUE_CONTRACT_QUESTION_ID})
            stored.append({"chain": a["chain"], "address": address if a["chain"] == "solana" else address.lower()})
        payee = {"id": "payee-" + secrets.token_hex(6), "displayName": display_name, "defaultAsset": body.get("defaultAsset"), "defaultChain": body.get("defaultChain"),
                 "references": body.get("references") or {}, "labels": body.get("labels") or [], "createdAt": self._now_iso()}
        self.payees[payee["id"]] = payee
        for a in stored:
            row = {"id": "addr-" + secrets.token_hex(6), "payeeId": payee["id"], "chain": a["chain"], "address": a["address"], "whitelistStatus": "proposed",
                   "promotedAt": None, "platformMembershipId": None, "proposedBy": caller["credentialId"]}
            self.addresses[row["id"]] = row
        return 201, {"payee": self.payee_view(payee)}

    def payee_view(self, payee: Dict[str, Any]) -> Dict[str, Any]:
        addresses = sorted([a for a in self.addresses.values() if a["payeeId"] == payee["id"]], key=lambda a: a["chain"])
        view = dict(payee)
        view["addresses"] = [{"id": a["id"], "chain": a["chain"], "address": a["address"], "whitelistStatus": a["whitelistStatus"], "promotedAt": a["promotedAt"], "platformMembershipId": a["platformMembershipId"]} for a in addresses]
        return view

    def list_payees(self) -> List[Dict[str, Any]]:
        return [self.payee_view(p) for p in sorted(self.payees.values(), key=lambda p: p["displayName"])]

    def charter_facts(self, caller: Dict[str, Any]) -> Dict[str, Any]:
        charter = self.newest_written_charter()
        quorum = charter.get("quorum") if charter else None
        return {"interviewType": charter["interviewType"] if charter else None, "namedApproverCredentialIds": list(self.second_approvers),
                "quorum": quorum if isinstance(quorum, int) and quorum >= 1 else None,
                "submitterMayApprove": charter.get("requesterCountsAsSigner") if charter and isinstance(charter.get("requesterCountsAsSigner"), bool) else None}

    def may_approve(self, facts: Dict[str, Any], submitter: Optional[str], approver: str) -> Tuple[bool, Optional[str]]:
        if approver not in facts["namedApproverCredentialIds"]:
            return False, "not_named"
        if submitter is None or submitter != approver:
            return True, None
        if facts["submitterMayApprove"] is False:
            return False, "charter_answered_no"
        if facts["quorum"] is None:
            return False, "charter_silent"
        if facts["submitterMayApprove"] is True:
            return True, None
        others = [c for c in facts["namedApproverCredentialIds"] if c != approver]
        if facts["quorum"] > 1 and not others:
            return False, "quorum_needs_another"
        return True, None

    def approval_refusal(self, cause: str, facts: Dict[str, Any], thing: str, held: Sequence[str]) -> Refusal:
        prompts = {"policy": "May the person who prepares a payment also count among those who release it?", "wallet_account": "May the person who submits a payment also be one of those who approve it?"}
        if cause == "not_named":
            because = "Your credential is not named as an approver in your organisation’s policy, so it cannot approve %s." % thing
            return Refusal("ROLE_NOT_GRANTED", role_not_granted_sentence(self.workspace["name"], held, None, because),
                           {"workspace": self.workspace["name"], "held": ",".join(held) or "none", "required": "approver"}, provenance={"source": "aap_policy"})
        if cause == "charter_answered_no":
            asked = prompts.get(facts["interviewType"] or "")
            message = "Your charter’s answer requires another approver: %sit answered No, so %s needs an approver who did not submit it." % (("asked “%s”, " % asked) if asked else "", thing)
        elif cause == "quorum_needs_another":
            message = ("Your charter requires an approver other than the submitter: it asks for %s people to agree before a release, and you are the only approver this estate has seated. "
                       "Seat another of the approvers your charter names, or lower the number who must agree." % facts["quorum"])
        else:
            message = ("Your estate has written no charter this deployment can read, so nothing has answered whether the person who submits may also approve. "
                       "Until it has, %s needs an approver who did not submit it." % thing)
        return Refusal("SUBMITTER_MAY_NOT_APPROVE", message, {"cause": cause}, provenance={"source": "charter"})

    def address_action(self, headers: Dict[str, str], address_id: str, action: str) -> Tuple[int, Any]:
        # AER 360 Spec 95 (Spec T12): the approve door admits any active roster signer, not only a seated approver — so the
        # gate is `author` (an authenticated author; a viewer is still refused), and the platform's ceremony
        # (sign_whitelist_ceremony) is the sole judge, binding and counting an active seat or refusing SIGNATURE_NOT_COUNTED.
        caller = self.require_caller(headers, "author", mutating=True)
        row = self.addresses.get(address_id)
        if not row:
            raise Refusal("ADDRESS_NOT_WHITELISTED", detail={"cause": "no such address"})
        if action == "promote":
            # routes/payees.ts, promote (spec 79): the platform holds the entry pending on the wallet's own whitelist_mutation
            # ceremony, and the honest answer is the ceremony's own numbers; a second send finds the ceremony that stands.
            ceremony = row.get("ceremony") or {"pendingTxId": "ptx-" + secrets.token_hex(4), "requiredSignatures": self.whitelist_threshold or 1, "signatures": []}
            row["ceremony"] = ceremony
            row["whitelistStatus"] = "pending_promotion"
            row["platformMembershipId"] = row.get("platformMembershipId") or ("mem-" + secrets.token_hex(4))
            self.audit.append("payee.address.promotion_pending_quorum %s requiredSignatures %d, signaturesCollected %d" % (
                address_id, ceremony["requiredSignatures"], len(ceremony["signatures"])))
            return 200, {"status": "pending_promotion", "platformMembershipId": row["platformMembershipId"],
                         "ceremony": {"pendingTxId": ceremony["pendingTxId"], "requiredSignatures": ceremony["requiredSignatures"], "signaturesCollected": len(ceremony["signatures"])}}
        if not row.get("ceremony"):
            raise Refusal("ADDRESS_PROMOTION_PENDING", detail={"cause": "this address has not been proposed to the platform whitelist yet"})
        entry_status = row.get("platformEntryStatus") or "pending"
        if entry_status != "pending":
            # THE PLATFORM NO LONGER NEEDS THIS PRESS (Spec T15 §2): the count was met and the entry is active, so the platform's approve answers
            # 409 "entry is already active" (test/aapDouble.ts), and the whitelist road relays it in its own sentence with the platform's words
            # beside it (services/payees.ts, approvalPlatformRefusal → platformRefusal: ADDRESS_PROPOSAL_REFUSED, 422)
            said = PLATFORM_ENTRY_ALREADY % entry_status
            raise Refusal("ADDRESS_PROPOSAL_REFUSED",
                          "The access platform would not approve this address, so nothing was changed: the platform answered HTTP 409: %s for entry %s of whitelist %s." % (
                              said, row["platformMembershipId"], self.whitelist_id),
                          {"payeeAddressId": row["id"], "chain": row["chain"], "address": row["address"], "credentialId": caller["credentialId"],
                           "entryId": row["platformMembershipId"], "whitelistId": self.whitelist_id, "platformStatus": "409", "platformSaid": said},
                          provenance={"source": "aap_whitelist"})
        if action == "reject":
            row["whitelistStatus"] = "rejected"
            row["platformEntryStatus"] = "rejected"
            row["promotedAt"] = self._now_iso()
            return 200, {"whitelistStatus": "rejected"}
        return 200, self.sign_whitelist_ceremony(row, caller)

    def sign_whitelist_ceremony(self, row: Dict[str, Any], caller: Dict[str, Any]) -> Dict[str, Any]:
        """
        The press performs the act (services/payees.ts, signAsPresser; Spec 89 says what it left standing). The platform's
        law, as the estate's own double of it states it (test/aapDouble.ts, the signatures road): a signature counts only
        for an active seat of the ceremony's roster; a press that says whose seat it is binds the caller's credential to that
        person's empty seat; a seat signs once, so a quorum of two is never met by one person pressing twice; anybody else is
        refused with the platform's bare "not authorized", which the estate relays as SIGNATURE_NOT_COUNTED with the
        platform's status and words. The press that meets the count answers whitelisted and nothing about waiting; a press
        that leaves it short answers the count, who may still approve, and the sentence — or, before Spec 89, the status alone.
        The seat is found by the platform's rule (Spec T10): by credential first, then an empty seat bound by the address the
        estate's press names; see the module docstring.
        """
        ceremony = row["ceremony"]
        active = [s for s in self.whitelist_seats if s["status"] == "active"]
        credential_id = caller["credentialId"]
        # THE PLATFORM'S RULE (Spec T10, from Spec 91's builder; test/aapDouble.ts, the signatures road): a signature counts for an
        # active seat matched by CREDENTIAL; a press that says whose seat it is binds the caller's credential to that person's
        # EMPTY seat; a seat already bound to a different key refuses; a credential is counted once. The estate's press says whose
        # seat it is only where it can attach the credential to one address nobody else's key shares (signAsPresser → signerEmailOf).
        user_id = self.signer_email_of(credential_id)
        seat = next((s for s in active if s["credential_id"] and s["credential_id"] == credential_id), None)
        if seat is None and user_id:
            named = next((s for s in active if s["user_id"].lower() == user_id.lower()), None)
            if named is not None and not named["credential_id"]:
                named["credential_id"] = credential_id  # the enrolment bind (spec 76)
                seat = named
        if seat is None:
            raise Refusal("SIGNATURE_NOT_COUNTED", detail={"payeeAddressId": row["id"], "credentialId": credential_id,
                                                           "platformStatus": "403", "platformSaid": PLATFORM_NOT_AUTHORIZED},
                          provenance={"source": "aap_whitelist", "reference": ceremony["pendingTxId"]})
        if credential_id not in ceremony["signatures"]:
            ceremony["signatures"].append(credential_id)  # only once either way
        required, collected = ceremony["requiredSignatures"], len(ceremony["signatures"])
        if collected >= required and not self.platform_never_activates:
            row["promotedAt"] = self._now_iso()
            row["platformEntryStatus"] = "active"  # the platform activated the entry: a further press meets its 409, relayed (Spec T15 §2)
            self.audit.append("payee.address.whitelisted %s by %s" % (row["id"], seat["user_id"]))
            if self.mirror_lags:
                # Spec T13 §3: the platform counted 2 of 2 and activated the entry; the estate's mirror answered the row's stale word,
                # `proposed`, as it did at 23:44 on 21 September. With Spec 100 the register corrects itself on the next GET /v1/payees;
                # before it the register reads `proposed` too.
                row["whitelistStatus"] = "whitelisted" if self.register_corrects else "proposed"
                return {"whitelistStatus": "proposed"}
            row["whitelistStatus"] = "whitelisted"
            return {"whitelistStatus": "whitelisted"}
        may_still = [s["display_name"] for s in active if not s["credential_id"] or s["credential_id"] not in ceremony["signatures"]]
        self.audit.append("payee.address.promotion_pending_quorum %s requiredSignatures %d, signaturesCollected %d, mayStillApprove %s" % (
            row["id"], required, collected, ", ".join(may_still) or "nobody"))
        if not self.pending_approval_says_why:
            return {"whitelistStatus": "pending_promotion"}  # the live estate's whole answer on 20 September 2026, before Spec 89
        return {"whitelistStatus": "pending_promotion",
                "approvals": {"required": required, "collected": collected, "remaining": max(required - collected, 0)},
                "may_still_approve": may_still,
                "sentence": pending_approval_sentence(required, collected, may_still, [s["display_name"] for s in active])}

    # -- the roster ceremony (Spec T15: AER 360 Spec 99, routes/rosterchanges.ts, services/approverseats.ts; the platform's roads, test/aapDouble.ts) --
    def rosters(self) -> List[Dict[str, Any]]:
        """The two governance rosters the compiler wrote, as the platform lists them (listMultisigs); their signer lists are the live ones."""
        return [
            {"id": WHITELIST_ROSTER_ID, "name": "%s — whitelist_mutation approvers" % self.workspace["name"], "purposes": ["whitelist_mutation"],
             "minSignatures": self.whitelist_threshold or 1, "signers": self.whitelist_seats, "active": True},
            {"id": CHANGE_ROSTER_ID, "name": "%s — multisig_mutation approvers" % self.workspace["name"], "purposes": ["multisig_mutation"],
             "minSignatures": self.change_threshold or 1, "signers": self.change_seats, "active": True},
        ]

    def roster_by_id(self, roster_id: Any) -> Optional[Dict[str, Any]]:
        return next((r for r in self.rosters() if r["id"] == roster_id), None)

    def append_trail(self, action: str, credential_id: Optional[str], detail: Dict[str, Any], subject_id: Optional[str] = None) -> Dict[str, Any]:
        """`appendAudit` (services/audit.ts), in the shape the audit export reads it back (routes/exports.ts, auditRegister): the row's subject is the thing acted on, else the workspace."""
        row = {"audit_id": "aud-" + secrets.token_hex(6), "at": self._now_iso(), "action": action, "credential_id": credential_id or "",
               "subject_id": subject_id or self.workspace["id"], "detail": detail}
        self.trail.append(row)
        return row

    def born_ceremony(self, roster: Dict[str, Any], payload_hash: str) -> Dict[str, Any]:
        """A ceremony at birth (test/aapDouble.ts, bornCeremony): pending, unconsumed, expiring a day out, nothing collected — or lapsed at birth by the dial."""
        now = time.time()
        lapsed = self.ceremony_lapses > 0
        if lapsed:
            self.ceremony_lapses -= 1
        expires = now - 60 if lapsed else now + PENDING_TX_TTL_SECONDS
        return {"id": str(uuid.uuid4()), "accountId": AAP_ACCOUNT_ID, "purpose": "multisig_mutation", "entryId": roster["id"], "payloadHash": payload_hash,
                "operation": T.ROSTER_CHANGE_OPERATION, "requiredMultisigId": CHANGE_ROSTER_ID, "requiredSignatures": self.change_threshold or 1,
                "status": "pending", "createdAt": self._iso(now), "expiresAt": self._iso(expires), "expiresAtEpoch": expires, "consumedAt": None, "collected": []}

    @staticmethod
    def ceremony_is_live(ceremony: Dict[str, Any], now: float) -> bool:
        """`ceremonyIsLive` (test/aapDouble.ts, findMutationCeremony's reading): pending or approved, unconsumed, and before its expiry."""
        return ceremony["status"] in ("pending", "approved") and ceremony.get("consumedAt") is None and ceremony["expiresAtEpoch"] > now

    def replace_multisig_signers(self, roster: Dict[str, Any], signers: List[Dict[str, Any]], actor: str) -> Dict[str, Any]:
        """
        The platform's PATCH /v1/multisigs-v2/{id} (test/aapDouble.ts): where the account's change governance holds multisig_update at a count
        above one, the change is a governed mutation — found again by the digest of its content (hashed without the actor), a fresh ceremony where
        none is live — answered 409 mutation_ceremony_required until the count is met, and APPLIED and CONSUMED in one act when the approved
        change is presented again. At a count of one, or with no governance established, the roster is written at once.
        """
        threshold = self.change_threshold or 1
        if self.governance_established and threshold > 1:
            content = {"name": roster["name"], "signers": [{k: s.get(k) for k in ("user_id", "credential_id", "status", "display_name")} for s in signers],
                       "min_signatures": roster["minSignatures"], "purposes": roster["purposes"]}
            payload_hash = hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()
            now = time.time()
            ceremony = next((c for c in self.ceremonies if c["entryId"] == roster["id"] and c["payloadHash"] == payload_hash and self.ceremony_is_live(c, now)), None)
            if ceremony is None:
                ceremony = self.born_ceremony(roster, payload_hash)
                self.ceremonies.append(ceremony)
            if ceremony["status"] != "approved":
                return {"ceremony": ceremony, "roster": None}
            ceremony["status"] = "consumed"
            ceremony["consumedAt"] = self._now_iso()
        roster["signers"][:] = signers  # the live list, replaced in place
        return {"ceremony": None, "roster": roster}

    def rebind_roster_seats(self, email: Any, person_name: str, credential_id: str, by_credential_id: str, via: str) -> Optional[Dict[str, Any]]:
        """
        `rebindRosterSeats` (services/approverseats.ts, Spec 95): every active seat naming this address and bound to a credential the person no
        longer holds is presented to the platform moved; a ceremony the client's own governance answers with is carried as `awaiting` with Spec 95's
        sentence and — since Spec 99 — remembered against the seat (`roster.change_proposed`); an applied move is written to the trail
        (`roster.seat_rebound`). An empty seat is left for its own person's press to fill. None before Spec 91, whose estate had no Spec 95.
        """
        if self.before_spec_91:
            return None
        wanted = str(email or "").strip().lower()
        outcome: Dict[str, Any] = {"rebound": [], "awaiting": [], "refused": None}
        if not wanted:
            return outcome
        person = (person_name or "").strip() or wanted
        for roster in self.rosters():
            moving = [s for s in roster["signers"] if s["status"] == "active" and s["user_id"].lower() == wanted and s["credential_id"] and s["credential_id"] != credential_id]
            if not moving:
                continue
            signers = [dict(s, credential_id=credential_id) if any(s is m for m in moving) else s for s in roster["signers"]]
            answered = self.replace_multisig_signers(roster, signers, by_credential_id)
            for seat in moving:
                moved = {"rosterId": roster["id"], "rosterName": roster["name"], "purposes": list(roster["purposes"]), "seatEmail": wanted,
                         "seatName": (seat.get("display_name") or "").strip() or (person_name or "").strip() or None,
                         "oldCredentialId": seat["credential_id"], "newCredentialId": credential_id}
                ceremony = answered["ceremony"]
                if ceremony is not None:
                    outcome["awaiting"].append(dict(moved, pendingTxId=ceremony["id"], operation=ceremony["operation"], requiredSignatures=ceremony["requiredSignatures"],
                                                    signaturesCollected=len(ceremony["collected"]),
                                                    sentence=roster_seat_awaiting_sentence(person, roster["name"], ceremony["id"], ceremony["requiredSignatures"], len(ceremony["collected"]))))
                    if not self.before_spec_99:
                        self.record_roster_change_proposed(by_credential_id, via, ceremony, moved)
                    continue
                self.append_trail(T.ROSTER_SEAT_REBOUND, by_credential_id, dict(
                    {"rosterId": moved["rosterId"], "rosterName": moved["rosterName"], "purposes": ",".join(moved["purposes"]), "seatEmail": wanted},
                    **({"seatName": moved["seatName"]} if moved["seatName"] else {}), oldCredentialId=moved["oldCredentialId"], newCredentialId=moved["newCredentialId"], via=via))
                outcome["rebound"].append(moved)
        return outcome

    def record_roster_change_proposed(self, by_credential_id: str, via: str, ceremony: Dict[str, Any], seat: Dict[str, Any]) -> None:
        """`recordRosterChangeProposed` (Spec 99): the ceremony the platform answered a move with, remembered against the seat it moves."""
        detail = {"pendingTxId": ceremony["id"], "operation": ceremony["operation"], "purpose": ceremony["purpose"], "requiredMultisigId": ceremony["requiredMultisigId"],
                  "requiredSignatures": str(ceremony["requiredSignatures"]), "signaturesCollected": str(len(ceremony["collected"])), "rosterId": seat["rosterId"],
                  "rosterName": seat["rosterName"], "purposes": ",".join(seat["purposes"]), "seatEmail": seat["seatEmail"]}
        if seat.get("seatName"):
            detail["seatName"] = seat["seatName"]
        detail.update({"oldCredentialId": seat["oldCredentialId"], "newCredentialId": seat["newCredentialId"], "via": via})
        self.append_trail(T.ROSTER_CHANGE_PROPOSED, by_credential_id, detail)

    def roster_change_proposals(self) -> Dict[str, Dict[str, Any]]:
        """`rosterChangeProposals`: every move this estate proposed, by the ceremony's id, read back off the trail; the newest row for an id wins."""
        proposals: Dict[str, Dict[str, Any]] = {}
        for row in self.trail:
            if row["action"] != T.ROSTER_CHANGE_PROPOSED:
                continue
            detail = row["detail"]
            if not all(detail.get(k) for k in ("pendingTxId", "rosterId", "seatEmail", "newCredentialId")):
                continue
            proposals[detail["pendingTxId"]] = dict(detail, byCredentialId=row["credential_id"], proposedAt=row["at"])
        return proposals

    def register_names(self) -> Dict[str, str]:
        """`registerNames`: the display name of the newest invitation to each address, any state."""
        names: Dict[str, str] = {}
        for row in sorted(self.invites.values(), key=lambda r: r["createdAt"], reverse=True):
            email = (row.get("email") or "").strip().lower()
            if email and email not in names:
                names[email] = row["displayName"]
        return names

    @staticmethod
    def seat_name(seat: Dict[str, Any], names: Dict[str, str]) -> str:
        """`seatName`: the seat's own display name, the register's, the address, else the credential in short form."""
        return (seat.get("display_name") or "").strip() or names.get(seat["user_id"].lower()) or seat["user_id"] or T.credential_short_form(seat.get("credential_id"))

    @staticmethod
    def seat_has_signed(seat: Dict[str, Any], collected: Sequence[Dict[str, Any]]) -> bool:
        return any((seat["credential_id"] and c["credential_id"] == seat["credential_id"]) or (c.get("user_id") and c["user_id"].lower() == seat["user_id"].lower()) for c in collected)

    def signer_view(self, signature: Dict[str, Any], active: Sequence[Dict[str, Any]], names: Dict[str, str]) -> Dict[str, Any]:
        seat = next((s for s in active if s["credential_id"] and s["credential_id"] == signature["credential_id"]), None)
        if seat is None and signature.get("user_id"):
            seat = next((s for s in active if s["user_id"].lower() == signature["user_id"].lower()), None)
        email = signature["user_id"].lower() if signature.get("user_id") else ((seat["user_id"].lower() or None) if seat else None)
        name = self.seat_name(seat, names) if seat else (names.get(email, email) if email else T.credential_short_form(signature["credential_id"]))
        return {"name": name, "email": email, "credentialId": T.credential_short_form(signature["credential_id"]), "signedAt": signature.get("collected_at")}

    def addresses_of_caller(self, credential_id: str) -> Set[str]:
        """
        `addressesOfCaller`: the one address the estate honestly attributes to the credential — the invitation it redeemed, nobody else's key on it
        (addressOfCredential) — else, for a key attached to no address and held by one passkey, the account's own address (getSelfAccount).
        """
        invited = self.signer_email_of(credential_id)
        if invited:
            return {invited.lower()}
        attached = any(credential_id in ids for ids in self.enrolled_by_email().values())
        held_by_one = len(self.credential_holders().get(credential_id, [])) <= 1
        if attached or not held_by_one:
            return set()
        return {self.account_email.strip().lower()} if self.account_email else set()

    @staticmethod
    def caller_seat(active: Sequence[Dict[str, Any]], credential_id: str, addresses: Set[str]) -> Optional[Dict[str, Any]]:
        """`callerSeat`: an active seat bound to the caller's credential, else one named by an address the estate attributes to them."""
        return next((s for s in active if s["credential_id"] and s["credential_id"] == credential_id), None) or \
            next((s for s in active if s["user_id"].lower() in addresses), None)

    @staticmethod
    def roster_change_state(record: Dict[str, Any], now: float) -> str:
        """`rosterChangeState`: the platform's status word beside its expiry — a lapsed pending or approved ceremony is expired."""
        lapsed = record["expiresAtEpoch"] <= now
        status = record["status"]
        if status == "consumed":
            return "applied"
        if status == "approved":
            return "expired" if lapsed else "approved"
        if status == "pending":
            return "expired" if lapsed else "awaiting"
        if status == "expired":
            return "expired"
        return "closed"

    def roster_change_view(self, record: Dict[str, Any], proposal: Optional[Dict[str, Any]], caller_credential: str, addresses: Set[str],
                           names: Dict[str, str], now: float) -> Dict[str, Any]:
        """`rosterChangeView`: one row of the list, composed from the platform's record and the estate's own."""
        signing = self.roster_by_id(record["requiredMultisigId"])
        active = [s for s in signing["signers"] if s["status"] == "active"] if signing else []
        collected = record["collected"]
        signed_by = [self.signer_view(c, active, names) for c in collected]
        may_sign = [self.seat_name(s, names) for s in active if not self.seat_has_signed(s, collected)]
        mine = self.caller_seat(active, caller_credential, addresses) if signing else None
        caller_has_signed = any(c["credential_id"] == caller_credential for c in collected) or (mine is not None and self.seat_has_signed(mine, collected))
        state = self.roster_change_state(record, now)
        seat = {"email": proposal["seatEmail"], "name": proposal.get("seatName") or None, "oldCredentialId": T.credential_short_form(proposal["oldCredentialId"]),
                "newCredentialId": T.credential_short_form(proposal["newCredentialId"])} if proposal else None
        facts = {"pendingTxId": record["id"], "state": state, "proposedHere": proposal is not None, "seat": seat, "signingRosterName": signing["name"] if signing else None,
                 "platformStatus": record["status"], "requiredSignatures": record["requiredSignatures"], "signaturesCollected": len(collected), "signedBy": signed_by,
                 "maySign": may_sign, "expiresAt": record["expiresAt"]}
        view = dict(facts)
        view.update({"operation": proposal["operation"] if proposal else None, "proposedAt": proposal["proposedAt"] if proposal else None,
                     "via": proposal["via"] if proposal else None, "rosterId": proposal["rosterId"] if proposal else None, "rosterName": proposal["rosterName"] if proposal else None,
                     "signingRosterId": record["requiredMultisigId"], "callerMaySign": state == "awaiting" and proposal is not None and mine is not None and not caller_has_signed,
                     "callerHasSigned": caller_has_signed, "createdAt": record["createdAt"], "sentence": roster_change_sentence(facts, now)})
        return view

    def list_roster_changes(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        """GET /v1/roster/changes (Spec 99, item 1): every multisig_mutation ceremony the platform holds for the estate, newest first, any status."""
        caller = self.require_caller(headers, "viewer")
        proposals = self.roster_change_proposals()
        names = self.register_names()
        addresses = self.addresses_of_caller(caller["credentialId"])
        now = time.time()
        listed = sorted((c for c in self.ceremonies if c["purpose"] == "multisig_mutation"), key=lambda c: (c["createdAt"], c["id"]), reverse=True)
        return 200, {"changes": [self.roster_change_view(c, proposals.get(c["id"]), caller["credentialId"], addresses, names, now) for c in listed]}

    def roster_change_binding(self, pending_tx_id: str, issued_at: Any, credential_id: str) -> Dict[str, str]:
        """deriveChallenge's binding for the signature: setDigest `roster-change:<workspace id>:<pendingTxId>:<issuedAtMs>`, the signer's credential, the purpose."""
        return {"setDigest": T.ROSTER_CHANGE_BINDING % (WORKSPACE_ID, pending_tx_id, issued_at), "credentialId": credential_id, "purpose": T.ROSTER_CHANGE_PURPOSE}

    def roster_change_challenge(self, binding: Dict[str, str]) -> str:
        return self.challenge(binding["purpose"], "%s|%s" % (binding["setDigest"], binding["credentialId"]), 0)

    def roster_change_sign_options(self, headers: Dict[str, str], pending_tx_id: str) -> Tuple[int, Any]:
        """Step one: the digest-bound challenge, for the signer's own passkeys — a person who may not sign at all still receives one; the roster judges at the press."""
        caller = self.require_caller(headers, "viewer", mutating=True)
        issued_at = int(time.time() * 1000)
        challenge = self.roster_change_challenge(self.roster_change_binding(pending_tx_id, issued_at, caller["credentialId"]))
        own = [w for w, row in self.passkeys.items() if row["credentialId"] == caller["credentialId"]]
        return 200, {"options": {"challenge": challenge, "rpId": self.rp_id, "timeout": 60000, "userVerification": "required",
                                 "allowCredentials": [{"id": w, "type": "public-key", "transports": ["internal"]} for w in own]}, "issuedAtMs": issued_at}

    def sign_roster_change(self, headers: Dict[str, str], pending_tx_id: str, body: Any) -> Tuple[int, Any]:
        """
        Step two (Spec 99, items 2 and 3; signRosterChange): the assertion verified against the same binding, then in the fail-closed order — is
        this a change the estate proposed; is the caller an active signer of the roster the platform collects it on; has the platform already counted
        them — then one signature as this person, and the platform's answer is the estate's; the count met, the change is presented again.
        """
        caller = self.require_caller(headers, "viewer", mutating=True)
        body = body or {}
        for field in ("issuedAtMs", "response"):
            if field not in body:
                raise Malformed("%s: Required" % field)
        self.assert_fresh(body["issuedAtMs"])
        expected = self.roster_change_challenge(self.roster_change_binding(pending_tx_id, body["issuedAtMs"], caller["credentialId"]))
        response = body["response"] or {}
        if not isinstance(response.get("id"), str) or not response["id"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "assertion carried no credential id"})
        stored = self.passkeys.get(response["id"])
        if not stored or stored["credentialId"] != caller["credentialId"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "the asserting passkey is not the signing credential"})
        try:
            stored["signCount"] = PK.verify_assertion(response, expected, self.origin, self.rp_id, stored["publicKey"], stored["signCount"])
        except PK.PasskeyRefused as err:
            raise Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]})
        stored["lastAuthAtMs"] = body["issuedAtMs"]
        proposal = self.roster_change_proposals().get(pending_tx_id)
        if proposal is None:
            raise Refusal("ROSTER_CHANGE_UNKNOWN", detail={"pendingTxId": pending_tx_id, "cause": "not_proposed_here"}, provenance={"source": "aap_policy", "reference": pending_tx_id})
        names = self.register_names()
        signing = self.roster_by_id(proposal["requiredMultisigId"])
        if signing is None:
            raise Refusal("CHANGE_GOVERNANCE_UNREADABLE", detail={"pendingTxId": pending_tx_id, "requiredMultisigId": proposal["requiredMultisigId"], "ceremony": T.ROSTER_CHANGE_PURPOSE, "question": "C12C"},
                          provenance={"source": "aap_policy"})
        active = [s for s in signing["signers"] if s["status"] == "active"]
        addresses = self.addresses_of_caller(caller["credentialId"])
        # THE ROSTER DECIDES WHO MAY SIGN — before the platform is asked to sign anything
        seat = self.caller_seat(active, caller["credentialId"], addresses)
        if seat is None:
            members = [self.seat_name(s, names) for s in active]
            detail = {"cause": NOT_ON_ROSTER_CAUSE, "roster": signing["name"], "rosterId": signing["id"], "purpose": "multisig_mutation", "question": "C12C",
                      "ceremony": T.ROSTER_CHANGE_PURPOSE, "members": ", ".join(members), "credentialId": caller["credentialId"]}
            if addresses:
                detail["addresses"] = ", ".join(sorted(addresses))
            raise Refusal("CHANGE_SIGNER_NOT_ON_ROSTER", not_on_change_roster_sentence(members), detail, provenance={"source": "aap_policy", "reference": signing["id"]})
        record = next((c for c in self.ceremonies if c["id"] == pending_tx_id and c["accountId"] == AAP_ACCOUNT_ID), None)
        if record is None:
            raise Refusal("ROSTER_CHANGE_UNKNOWN", detail={"pendingTxId": pending_tx_id, "cause": "not_listed", "platformSaid": "not found"}, provenance={"source": "aap_policy", "reference": pending_tx_id})
        collected = record["collected"]
        mine = next((c for c in collected if c["credential_id"] == caller["credentialId"]), None)
        if mine is None and self.seat_has_signed(seat, collected):
            mine = next((c for c in collected if (seat["credential_id"] and c["credential_id"] == seat["credential_id"]) or (c.get("user_id") and c["user_id"].lower() == seat["user_id"].lower())), None)
        if mine is not None:
            # ALREADY ON THE PLATFORM'S RECORD: refused from that record, and the platform is not asked to count what it has counted
            at = (" (collected %s)" % mine["collected_at"]) if mine.get("collected_at") else ""
            detail = {"pendingTxId": pending_tx_id, "credentialId": caller["credentialId"], "signaturesCollected": str(len(collected)), "requiredSignatures": str(record["requiredSignatures"]),
                      "platformStatus": record["status"]}
            if mine.get("collected_at"):
                detail["signedAt"] = mine["collected_at"]
            raise Refusal("APPROVER_ALREADY_SIGNED",
                          "You have already signed this change: the access platform’s record of ceremony %s… carries your signature%s, and it counts each signatory once. %d of %d stand; nothing was signed again." % (
                              T.credential_short_form(pending_tx_id), at, len(collected), record["requiredSignatures"]),
                          detail, provenance={"source": "aap_policy", "reference": pending_tx_id})
        # THE PLATFORM'S SIGNATURES ROAD (test/aapDouble.ts): the lapse read off expires_at; the status; the signer matched by credential, or bound by user_id
        now = time.time()
        if record["expiresAtEpoch"] <= now:
            raise Refusal("PLATFORM_REFUSED", platform_refused_sentence(409, PLATFORM_EXPIRED),
                          {"outcome": "refused", "platformStatus": "409", "platformSaid": PLATFORM_EXPIRED, "route": SIGNATURES_ROAD}, provenance={"source": "aap"})
        if record["status"] != "pending":
            said = PLATFORM_NOT_PENDING % record["status"]
            raise Refusal("PLATFORM_REFUSED", platform_refused_sentence(409, said), {"outcome": "refused", "platformStatus": "409", "platformSaid": said, "route": SIGNATURES_ROAD},
                          provenance={"source": "aap"})
        signer = next((s for s in active if s["credential_id"] and s["credential_id"] == caller["credentialId"]), None)
        if signer is None and seat["user_id"] and not seat["credential_id"]:
            seat["credential_id"] = caller["credentialId"]  # the enrolment bind (spec 76)
            signer = seat
        if signer is None:
            raise Refusal("SIGNATURE_NOT_COUNTED", detail={"pendingTxId": pending_tx_id, "credentialId": caller["credentialId"], "roster": signing["name"], "rosterId": signing["id"],
                                                           "platformStatus": "403", "platformSaid": PLATFORM_NOT_AUTHORIZED_SENTENCE},
                          provenance={"source": "aap_policy", "reference": pending_tx_id})
        collected.append({"credential_id": caller["credentialId"], "user_id": seat["user_id"], "collected_at": self._now_iso()})
        if len(collected) >= record["requiredSignatures"]:
            record["status"] = "approved"
        elif self.lapse_after_first_signature and len(collected) == 1:
            # THE CLOCK PASSES THE CEREMONY'S EXPIRY between the first signature and the next: the platform sweeps nothing, so the record keeps
            # `pending` and the next signature meets "conflict: pending transaction expired" in the platform's own words
            record["expiresAtEpoch"] = now - 60
            record["expiresAt"] = self._iso(record["expiresAtEpoch"])
        answer = {"pendingTxId": pending_tx_id, "requiredSignatures": record["requiredSignatures"], "signaturesCollected": len(collected),
                  "signedBy": [self.signer_view(c, active, names) for c in collected], "maySign": [self.seat_name(s, names) for s in active if not self.seat_has_signed(s, collected)]}
        if record["status"] != "approved":
            view = dict(answer, state="awaiting", rebound=None, reopened=None)
            return 200, dict(view, sentence=roster_change_signed_sentence(view))
        return 200, self.apply_roster_change(proposal, record, answer, caller["credentialId"])

    def apply_roster_change(self, proposal: Dict[str, Any], record: Dict[str, Any], answer: Dict[str, Any], actor: str) -> Dict[str, Any]:
        """
        `applyRosterChange` (Spec 99, item 3): the count met, Spec 95's change is presented to the platform again — the same roster read again, the
        same signer list derived the same way, so the digest reaches the approved ceremony and the platform applies and consumes it — and the seat is
        marked rebound only from the roster the platform returns, the trail row naming the ceremony and every signer.
        """
        roster = self.roster_by_id(proposal["rosterId"])
        who = (proposal.get("seatName") or "").strip() or proposal["seatEmail"]
        def held(because: str, reopened: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            view = dict(answer, state="approved", rebound=None, reopened=reopened)
            return dict(view, sentence=roster_change_signed_sentence(view, because))
        if roster is None:
            return held("the access platform’s list of rosters no longer carries “%s” active, so there is nothing to present the change against" % proposal["rosterName"])
        wanted = proposal["seatEmail"].lower()
        moving = [s for s in roster["signers"] if s["status"] == "active" and s["user_id"].lower() == wanted and s["credential_id"] and s["credential_id"] != proposal["newCredentialId"]]
        rebound = {"email": proposal["seatEmail"], "name": proposal.get("seatName") or None, "oldCredentialId": T.credential_short_form(proposal["oldCredentialId"]),
                   "newCredentialId": T.credential_short_form(proposal["newCredentialId"]), "rosterId": roster["id"], "rosterName": roster["name"]}
        def mark_rebound() -> Dict[str, Any]:
            detail = {"rosterId": roster["id"], "rosterName": roster["name"], "purposes": ",".join(roster["purposes"]), "seatEmail": proposal["seatEmail"]}
            if proposal.get("seatName"):
                detail["seatName"] = proposal["seatName"]
            detail.update({"oldCredentialId": proposal["oldCredentialId"], "newCredentialId": proposal["newCredentialId"], "via": T.VIA_ROSTER_CHANGE,
                           "pendingTxId": proposal["pendingTxId"], "requiredSignatures": str(answer["requiredSignatures"]),
                           "signerCredentialIds": ",".join(c["credential_id"] for c in record["collected"]), "signerNames": ", ".join(s["name"] for s in answer["signedBy"])})
            self.append_trail(T.ROSTER_SEAT_REBOUND, actor, detail)
            view = dict(answer, state="applied", rebound=rebound, reopened=None)
            return dict(view, sentence=roster_change_signed_sentence(view))
        if not moving:
            stands = any(s["status"] == "active" and s["user_id"].lower() == wanted and s["credential_id"] == proposal["newCredentialId"] for s in roster["signers"])
            if stands:
                return mark_rebound()
            return held("the roster “%s” no longer carries %s’s seat bound to the credential the change moves it from, so there is nothing to present" % (roster["name"], who))
        signers = [dict(s, credential_id=proposal["newCredentialId"]) if any(s is m for m in moving) else s for s in roster["signers"]]
        answered = self.replace_multisig_signers(roster, signers, actor)
        ceremony = answered["ceremony"]
        if ceremony is not None:
            if ceremony["id"] == proposal["pendingTxId"]:
                return held("the access platform answered the change with the same ceremony, at %d of %d, and did not apply it" % (len(ceremony["collected"]), ceremony["requiredSignatures"]))
            for s in moving:
                self.record_roster_change_proposed(actor, T.VIA_ROSTER_CHANGE, ceremony, {"rosterId": roster["id"], "rosterName": roster["name"], "purposes": list(roster["purposes"]),
                                                                                          "seatEmail": wanted, "seatName": (s.get("display_name") or "").strip() or proposal.get("seatName"),
                                                                                          "oldCredentialId": s["credential_id"], "newCredentialId": proposal["newCredentialId"]})
            return held("", {"pendingTxId": ceremony["id"], "requiredSignatures": ceremony["requiredSignatures"], "signaturesCollected": len(ceremony["collected"])})
        confirmed = any(s["status"] == "active" and s["user_id"].lower() == wanted and s["credential_id"] == proposal["newCredentialId"] for s in roster["signers"])
        if not confirmed:
            raise Refusal("ROSTER_SEAT_NOT_REBOUND", detail={"outcome": "answered", "pendingTxId": proposal["pendingTxId"], "seatEmail": wanted, "platformStatus": "200",
                                                             "platformSaid": "the roster returned does not carry the seat on the new credential", "route": "PATCH /v1/multisigs-v2/{id}", "via": T.VIA_ROSTER_CHANGE})
        return mark_rebound()

    def audit_export(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        """GET /v1/export/audit (routes/exports.ts): the trail, oldest first, `items` with audit_id, at, action, credential_id, subject_id, detail; the draw is itself a row."""
        caller = self.require_caller(headers, "viewer")
        limit = 500
        try:
            limit = max(1, min(5000, int((self._query.get("limit") or ["500"])[0])))
        except ValueError:
            raise Malformed("limit: Expected number")
        page = list(self.trail[:limit])
        self.append_trail("export.generated", caller["credentialId"], {"register": "audit", "format": "json", "rows": len(page)})
        return 200, {"items": page, "nextCursor": None, "rateSource": "double", "generatedAt": self._now_iso()}

    # -- sets (routes/sets.ts, setgates.ts, roles.ts, destinationlaw.ts) ------------------------------------------
    def review_or_create(self, headers: Dict[str, str], body: Any, create: bool) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        if not self.workspace.get("baseCurrency"):
            raise Refusal("BASE_CURRENCY_UNSET", provenance={"source": "workspace"})
        body = body or {}
        pays = body.get("pays")
        if not isinstance(pays, list) or not pays:
            raise Malformed("pays: Array must contain at least 1 element(s)")
        if create:
            for field in ("idempotencyKey", "reference"):
                if not isinstance(body.get(field), str) or not body[field]:
                    raise Malformed("%s: Required" % field)
        charter = self.newest_written_charter()
        if not self.has_funding_wallet():
            # routes/sets.ts requireSourceAccount (Spec 104): a run asked of an estate with no funding wallet, in the wallet's own sentence
            raise Refusal("WORKSPACE_NOT_PROVISIONED", NO_FUNDING_WALLET_SENTENCE, {"cause": NO_FUNDING_WALLET_REASON}, provenance={"source": "workspace"})
        rows = []
        for index, p in enumerate(pays):
            amount = p.get("amountMinor")
            if not isinstance(amount, str) or not re.match(r"^-?\d+$", amount.strip()):
                raise Refusal("AMOUNT_MALFORMED", detail={"amountMinor": str(amount)})
            rows.append({"index": index, "pay": p, "amountMinor": int(amount)})
        if create:
            existing = next((s for s in self.sets.values() if s["idempotencyKey"] == body["idempotencyKey"]), None)
            if existing:
                return 200, {"set": self.set_view(existing, caller), "alreadyExisted": True, "review": existing["review"]}
        review = self.review(caller, charter, rows, body.get("duplicatesAcknowledged") is True)
        if not create:
            if self.review_refuses_but_pays and not review["payload"]["acceptable"]:
                self.pay_behind_the_review(caller, review)  # a double that lies: "Nothing was sent", and money moved
            return 200, review["payload"]
        if not review["payload"]["acceptable"]:
            blocking = [r for g in review["payload"]["gates"] if not g["passed"] for r in g["refusals"]]
            first = blocking[0]
            raise Refusal(first["code"], first["message"], first.get("detail"), **{k: v for k, v in first.items() if k not in ("code", "message", "detail")})
        set_row = {"id": "set-" + secrets.token_hex(6), "reference": "S-" + body["reference"], "realm": "sandbox", "idempotencyKey": body["idempotencyKey"], "status": "draft",
                   "sourceAccount": self.source_account, "authorCredentialId": caller["credentialId"], "setDigest": "0x" + secrets.token_hex(32),
                   "aggregateBaseMinor": str(review["aggregateUsd"]), "aggregateUsdMinor": str(review["aggregateUsd"]), "approvalsRequired": review["approvalsRequired"],
                   "bandThresholdBaseMinor": str(review["threshold"]), "createdAt": self._now_iso(), "submittedAt": None, "approvedAt": None, "executedAt": None,
                   "instructions": [], "review": review["payload"]}
        for r in review["resolved"]:
            set_row["instructions"].append({"id": "ins-" + secrets.token_hex(6), "setId": set_row["id"], "sequence": r["index"], "payeeId": r["payeeId"], "payeeName": r["payeeName"],
                                            "chain": r["chain"], "address": r["address"], "isOneOff": r["isOneOff"], "asset": r["asset"], "amountMinor": str(r["amountMinor"]),
                                            "invoiceRef": r["invoiceRef"], "memo": None, "glCode": None, "status": "queued", "clientRequestId": "req-" + secrets.token_hex(4), "txHash": None,
                                            "failureReason": None, "holdId": None, "heldReason": None, "heldWaitSentence": None,
                                            "entryValue": {"asset": r["asset"], "assetDecimals": 6, "amountAssetMinor": str(r["amountMinor"]), "baseCurrency": "USD", "baseDecimals": 2,
                                                           "amountBaseMinor": str(r["usdMinor"]), "amountUsdMinor": str(r["usdMinor"]), "rate": {"source": "double", "observedAt": self._now_iso(), "rateE8": "100000000"},
                                                           "kind": "entry", "valuationId": "val-" + secrets.token_hex(4), "occurredAt": self._now_iso()},
                                            "executionValue": None, "gasValue": None, "feeAccrual": None, "lockedValue": None})
            self.instructions_seen.append((r["chain"], r["address"].lower()))
        self.sets[set_row["id"]] = set_row
        self.approvals[set_row["id"]] = []
        return 201, {"set": self.set_view(set_row, caller), "alreadyExisted": False, "review": review["payload"]}

    def review(self, caller: Dict[str, Any], charter: Optional[Dict[str, Any]], rows: List[Dict[str, Any]], acknowledged: bool) -> Dict[str, Any]:
        resolved = []
        whitelist_refusals = []
        waits = 0
        mode = charter.get("whitelistMode") if charter else None
        for r in rows:
            p = r["pay"]
            out = {"index": r["index"], "payeeId": None, "payeeName": (p.get("oneOff") or {}).get("payeeName") or "One-off payee", "address": str((p.get("oneOff") or {}).get("address", "")).lower(),
                   "isOneOff": bool(p.get("oneOff")), "standing": "declared_one_off" if p.get("oneOff") else "undeclared", "chain": p.get("chain"), "asset": str(p.get("asset", "")).upper(),
                   "amountMinor": r["amountMinor"], "invoiceRef": p.get("invoiceRef"), "refusals": [], "usdMinor": 0}
            if r["amountMinor"] <= 0:
                out["refusals"].append({"code": "AMOUNT_NOT_POSITIVE", "message": "A payment amount must be greater than zero.", "rowIndex": r["index"]})
            if out["asset"] not in KNOWN_ASSETS:
                out["refusals"].append({"code": "ASSET_UNKNOWN", "message": MESSAGES["ASSET_UNKNOWN"], "rowIndex": r["index"], "detail": {"asset": out["asset"]}})
            if p.get("chain") not in KNOWN_CHAINS:
                out["refusals"].append({"code": "CHAIN_NOT_SUPPORTED", "message": MESSAGES["CHAIN_NOT_SUPPORTED"], "rowIndex": r["index"], "detail": {"chain": p.get("chain")}, "provenance": {"source": "chain_registry"}})
            if p.get("payeeAddressId"):
                found = self.addresses.get(p["payeeAddressId"])
                if not found:
                    out["refusals"].append({"code": "ADDRESS_NOT_WHITELISTED", "message": MESSAGES["ADDRESS_NOT_WHITELISTED"], "rowIndex": r["index"], "detail": {"cause": "this payee address does not belong to this workspace"}})
                else:
                    out["payeeId"] = found["payeeId"]
                    out["payeeName"] = self.payees[found["payeeId"]]["displayName"]
                    out["address"] = found["address"]
                    out["isOneOff"] = False
                    out["standing"] = "whitelisted" if found["whitelistStatus"] == "whitelisted" else ("pending_promotion" if found["whitelistStatus"] == "pending_promotion" else "registered_unlisted")
            elif not p.get("oneOff"):
                out["refusals"].append({"code": "ONE_OFF_NOT_DECLARED", "message": MESSAGES["ONE_OFF_NOT_DECLARED"], "rowIndex": r["index"], "detail": {"cause": "no payee address was chosen and no one-off was declared"}})
            # USDC and USDT price 1:1 with the dollar in this double; the minor units are cents already (6 decimals → 2)
            out["usdMinor"] = r["amountMinor"] // 10000 if out["asset"] in ("USDC", "USDT") else r["amountMinor"]
            resolved.append(out)
        for out in resolved:
            if out["standing"] == "undeclared":
                continue
            if out["standing"] == "whitelisted":
                continue
            is_new = mode == "hold_non_listed" and (out["chain"], out["address"].lower()) not in self.instructions_seen
            if mode == "none":
                continue
            if mode == "hold_non_listed":
                if is_new:
                    waits += 1
                continue
            if mode == "allow_only":
                ref = ({"code": "ADDRESS_PROMOTION_PENDING", "message": MESSAGES["ADDRESS_PROMOTION_PENDING"], "rowIndex": out["index"], "detail": {"chain": out["chain"], "address": out["address"]}, "provenance": {"source": "aap_whitelist"}}
                       if out["standing"] == "pending_promotion" else
                       {"code": "ADDRESS_NOT_WHITELISTED", "message": "Your charter says this estate pays only the addresses on its approved list, so this payment cannot be made and marking it a one-off will not help. Put this address on the list and have it approved, then pay it.",
                        "rowIndex": out["index"], "detail": {"chain": out["chain"], "address": out["address"], "whitelistMode": "allow_only"}, "provenance": {"source": "charter"}})
                out["refusals"].append(ref)
                whitelist_refusals.append(ref)
                continue
            if out["standing"] == "pending_promotion":
                ref = {"code": "ADDRESS_PROMOTION_PENDING", "message": MESSAGES["ADDRESS_PROMOTION_PENDING"], "rowIndex": out["index"], "detail": {"chain": out["chain"], "address": out["address"]}, "provenance": {"source": "aap_whitelist"}}
            elif out["standing"] == "declared_one_off":
                continue
            else:
                ref = {"code": "ONE_OFF_NOT_DECLARED", "message": MESSAGES["ONE_OFF_NOT_DECLARED"], "rowIndex": out["index"], "detail": {"chain": out["chain"], "address": out["address"]}, "provenance": {"source": "aap_whitelist"}}
            out["refusals"].append(ref)
            whitelist_refusals.append(ref)
        for out in resolved:
            for ref in out["refusals"]:
                if ref["code"] in ("ADDRESS_NOT_WHITELISTED", "ADDRESS_PROMOTION_PENDING", "ONE_OFF_NOT_DECLARED") and ref not in whitelist_refusals:
                    whitelist_refusals.append(ref)
        pricing_refusals = [ref for out in resolved for ref in out["refusals"] if ref["code"] in ("ASSET_UNKNOWN",)]
        aggregate = sum(out["usdMinor"] for out in resolved if not out["refusals"])
        # the band: the charter's per-payment hold stands as the policy entry's second-approver threshold
        threshold = int((charter or {}).get("amountsUsdCents", {}).get("holdOverPerTx") or 0) if charter else 0
        quorum = (charter or {}).get("quorum") if charter else None
        band = (quorum if isinstance(quorum, int) else 1) if threshold > 0 and aggregate >= threshold else 0
        approvals_required = max(band, 1 if waits else 0)
        gates = [
            {"gate": "whitelist_or_one_off", "passed": not whitelist_refusals, "refusals": whitelist_refusals,
             "evidence": ("%d of %d payment(s) go somewhere new that is not on your approved list, so this run waits for one approval" % (waits, len(resolved))) if waits
             else "%d on the approved list, %d one-off" % (sum(1 for o in resolved if o["standing"] == "whitelisted"), sum(1 for o in resolved if o["isOneOff"]))},
            {"gate": "pricing", "passed": not pricing_refusals and bool(resolved), "refusals": pricing_refusals, "evidence": "priced from double"},
            {"gate": "quota", "passed": True, "refusals": [], "evidence": "this plan has no monthly signature ceiling"},
            self.gas_account_preflight(resolved),
            {"gate": "duplicate_screen", "passed": True, "refusals": [], "evidence": "no matching payment in the last 7 days"},
        ]
        payload = {"rows": [{"index": o["index"], "payeeName": o["payeeName"], "chain": o["chain"], "address": o["address"], "isOneOff": o["isOneOff"], "asset": o["asset"],
                             "amountMinor": str(o["amountMinor"]), "value": {"asset": o["asset"], "assetDecimals": 6, "amountAssetMinor": str(o["amountMinor"]), "baseCurrency": "USD", "baseDecimals": 2,
                                                                             "amountBaseMinor": str(o["usdMinor"]), "amountUsdMinor": str(o["usdMinor"]), "rate": {"source": "double", "observedAt": self._now_iso(), "rateE8": "100000000"},
                                                                             "kind": "entry", "valuationId": "", "occurredAt": self._now_iso()}, "refusals": o["refusals"]} for o in resolved],
                   "gates": gates,
                   "aggregate": {"asset": "USDC", "assetDecimals": 6, "amountAssetMinor": str(sum(o["amountMinor"] for o in resolved)), "baseCurrency": "USD", "baseDecimals": 2,
                                 "amountBaseMinor": str(aggregate), "amountUsdMinor": str(aggregate), "rate": {"source": "double", "observedAt": self._now_iso(), "rateE8": "100000000"}, "kind": "entry", "valuationId": "", "occurredAt": self._now_iso()},
                   "approval": {"approvalsRequired": approvals_required, "approvalsGiven": 0, "bandThresholdBaseMinor": str(threshold), "aggregateBaseMinor": str(aggregate),
                                "eligibleApproverCredentialIds": list(self.second_approvers), "approvedByCredentialIds": [], "submitterCredentialId": caller["credentialId"]},
                   "acceptable": bool(resolved) and all(g["passed"] for g in gates), "acknowledgeable": []}
        return {"payload": payload, "resolved": [o for o in resolved], "aggregateUsd": aggregate, "threshold": threshold, "approvalsRequired": approvals_required}

    def gas_account_preflight(self, resolved: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        THE FOURTH GATE (Spec 104 §4; services/execution.ts gasAccountPreflight): the gas balance read from the platform before the quotes,
        one dry quote per payment — the chain's dry run of the transfer refuses where the key holds less than the amount, relayed as
        PAYMENT_UNPRICED in the platform's words; the platform refuses a quote the balance cannot cover (insufficient_gas) and its ceiling
        still counts toward the set's; a quote admitted reserves its ceiling — and U3's sentence with the set's figures under GAS_SHORTFALL
        where the balance is below the sum. The review's reservations are released by the platform's poller at valid_until, which in this
        double is the review's end, so the next read of the account sees the balance whole.
        """
        payable = [o for o in resolved if not o["refusals"] and o["address"]]
        if not payable:
            return {"gate": "gas_preflight", "passed": True, "refusals": [], "evidence": "nothing to price"}
        account = self.aap_account_id
        available = self.platform.balance(account)["available_usd_cents"]
        review_id = secrets.token_hex(4)
        refusals: List[Dict[str, Any]] = []
        reserved: List[str] = []
        ceiling = quoted = shortfalls = 0
        for o in payable:
            if self.chain.balance_of(self.source_account) < o["amountMinor"]:
                refusals.append({"code": "PAYMENT_UNPRICED", "message": "This payment could not be priced: %s. The answer will be the same until what it named is resolved." % ESTIMATE_REVERTED_CLAUSE,
                                 "rowIndex": o["index"], "detail": {"party": "the access platform", "outcome": "refused", "route": "POST /v1/gas/quote", "said": ESTIMATE_REVERTED_SAID, "status": "400",
                                                                    "platformCode": "refused", "chain": o["chain"], "asset": o["asset"]},
                                 "provenance": {"source": "aap", "reference": "POST /v1/gas/quote"}})
                continue
            if self.platform.balance(account)["available_usd_cents"] < self.quote_ceiling_usd_cents:
                ceiling += self.quote_ceiling_usd_cents
                shortfalls += 1
                continue
            key = "review:%s:%s:%d" % (self.workspace["id"], review_id, o["index"])
            self.platform.reserve(account, self.quote_ceiling_usd_cents, key, o["chain"], "gas reserved, at most %s, for review:%s:%d on %s" % (
                T.format_usd_cents(self.quote_ceiling_usd_cents), review_id, o["index"], o["chain"]))
            reserved.append(key)
            ceiling += self.quote_ceiling_usd_cents
            quoted += 1
        if (quoted or shortfalls) and available < ceiling:
            said_available, said_ceiling = (available + 1, ceiling + 100) if self.gas_refusal_names_other_figures else (available, ceiling)
            refusals.append({"code": "GAS_SHORTFALL", "message": T.gas_set_shortfall_sentence(said_available, said_ceiling),
                             "detail": {"availableUsdCents": str(said_available), "ceilingUsdCents": str(said_ceiling), "payments": str(quoted + shortfalls), "account": self.source_account, "minimumTopUpUsdCents": "1000"},
                             "provenance": {"source": "aap", "reference": "GET /v1/gas-account"}})
        n = quoted + shortfalls
        evidence = "gas account: %s available; this set needs at most %s of gas over %d payment%s" % (T.format_usd_cents(available), T.format_usd_cents(ceiling), n, "" if n == 1 else "s")
        if quoted:
            evidence += "; the review’s %s (review:%s) %s on the gas account until the access platform releases %s at %s" % (
                "1 quote" if quoted == 1 else "%d quotes" % quoted, review_id, "holds its ceiling" if quoted == 1 else "hold their ceilings", "it" if quoted == 1 else "them", self._iso(time.time() + 300))
        for key in reserved:
            self.platform.release(key)  # valid_until, in this double, is the review's end
        return {"gate": "gas_preflight", "passed": not refusals, "refusals": refusals, "evidence": evidence}

    def pay_behind_the_review(self, caller: Dict[str, Any], review: Dict[str, Any]) -> None:
        """A double that lies (`review_refuses_but_pays`): the review said nothing was sent, and a run leaves anyway, so the harness must catch the money that moved."""
        rows = [o for o in review["resolved"] if o["address"]]
        set_row = {"id": "set-" + secrets.token_hex(6), "reference": "S-behind the review", "realm": "sandbox", "idempotencyKey": "behind-" + secrets.token_hex(4), "status": "settled",
                   "sourceAccount": self.source_account, "authorCredentialId": caller["credentialId"], "setDigest": "0x" + secrets.token_hex(32),
                   "aggregateBaseMinor": str(review["aggregateUsd"]), "aggregateUsdMinor": str(review["aggregateUsd"]), "approvalsRequired": 0, "bandThresholdBaseMinor": "0",
                   "createdAt": self._now_iso(), "submittedAt": self._now_iso(), "approvedAt": self._now_iso(), "executedAt": self._now_iso(), "instructions": [], "review": review["payload"]}
        for r in rows:
            try:
                self.chain.transfer(self.source_account, r["address"], r["amountMinor"])
            except ValueError:
                continue
            set_row["instructions"].append({"id": "ins-" + secrets.token_hex(6), "setId": set_row["id"], "sequence": r["index"], "payeeId": r["payeeId"], "payeeName": r["payeeName"],
                                            "chain": r["chain"], "address": r["address"], "isOneOff": r["isOneOff"], "asset": r["asset"], "amountMinor": str(r["amountMinor"]),
                                            "invoiceRef": r["invoiceRef"], "memo": None, "glCode": None, "status": "confirmed", "clientRequestId": "req-" + secrets.token_hex(4),
                                            "txHash": "0x" + secrets.token_hex(32), "failureReason": None, "holdId": None, "heldReason": None, "heldWaitSentence": None,
                                            "entryValue": None, "executionValue": None, "gasValue": None, "feeAccrual": None, "lockedValue": None})
        self.sets[set_row["id"]] = set_row
        self.approvals[set_row["id"]] = []

    # -- the funding account's balances and the gas account (Spec 104 §1, §3) ---------------------------------------------------------
    def funding_account_balances(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        """GET /v1/workspace/funding-account/balances (routes/workspace.ts, services/fundingwallet.ts readFundingAccountState): the stablecoin the key holds per chain, in dollars."""
        self.require_session(headers)
        if not self.has_funding_wallet():
            return 200, {"account": None, "balances": [], "delegations": [], "delegatedSentence": None, "retired": None, "absence": NO_FUNDING_WALLET_SENTENCE}
        minor = self.chain.balance_of(self.source_account)
        usd = minor // 10 ** (T.ASSET_DECIMALS[T.PAYMENT_ASSET] - 2)
        row = {"chain": T.PAYEE_CHAIN, "asset": T.PAYMENT_ASSET, "token": self.chain.token, "balanceMinor": str(minor), "usdMinor": str(usd),
               "sentence": "This account holds %s of %s on %s." % (us_dollars(usd), T.PAYMENT_ASSET, T.PAYEE_CHAIN)}
        return 200, {"account": self.source_account, "balances": [row],
                     "delegations": [{"chain": T.PAYEE_CHAIN, "delegated": self.delegated, "implementation": self.implementation, "sentence": None}],
                     "delegatedSentence": ("delegated on %s" % T.PAYEE_CHAIN) if self.delegated else None, "retired": None}

    def gas_account(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        """GET /v1/gas/account (routes/gas.ts): the balance read live from the platform, the Wallets screen's sentence, the platform's low flag, and the press that is not open."""
        self.require_session(headers)
        balance = self.platform.balance(self.aap_account_id)
        low = self.platform.low(self.aap_account_id)
        account = {"availableUsdCents": balance["available_usd_cents"], "balanceUsdCents": balance["balance_usd_cents"], "reservedUsdCents": balance["reserved_usd_cents"],
                   "available": T.format_usd_cents(balance["available_usd_cents"]), "balance": T.format_usd_cents(balance["balance_usd_cents"]), "reserved": T.format_usd_cents(balance["reserved_usd_cents"]),
                   "sentence": "%s: %s" % (T.GAS_ACCOUNT_LABEL, T.format_usd_cents(balance["available_usd_cents"])), "low": low, "lowSentence": GAS_LOW_SENTENCE if low else None,
                   "lowPots": False, "lowPotsSentence": None, "minimumTopUpUsdCents": T.GAS_CREDIT_USD_CENTS, "operationsSettled": len(self.platform.debits_of(self.aap_account_id))}
        return 200, {"account": account, "unreadable": None,
                     "buying": {"open": False, "sentence": BUYING_GAS_NOT_OPEN, "missing": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_GAS_PRICE_UNIT"]},
                     "purchases": [], "afterCheckout": dict(AFTER_CHECKOUT_SENTENCES)}

    # -- the run executed through the gas roads (Spec 104 §2; services/execution.ts executeSet, drivePayment) --------------------------
    def execute_set(self, headers: Dict[str, str], set_id: str) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        row = self.sets.get(set_id)
        if not row:
            raise Refusal("SET_NOT_APPROVABLE", detail={"cause": "no such run"})
        if row["status"] not in ("approved", "executing"):
            raise Refusal("SET_NOT_APPROVABLE", detail={"status": row["status"], "cause": "this run has not been approved for execution"})
        if not self.has_funding_wallet():
            raise Refusal("WORKSPACE_NOT_PROVISIONED", NO_FUNDING_WALLET_SENTENCE, {"cause": NO_FUNDING_WALLET_REASON}, provenance={"source": "workspace"})
        if row["status"] == "approved":
            row["status"] = "executing"
            row["executedAt"] = self._now_iso()
            self.append_trail("set.execution_started", caller["credentialId"], {"setDigest": row["setDigest"], "road": "gas_roads", "account": self.source_account}, subject_id=set_id)
        for instruction in row["instructions"]:
            if instruction["status"] in T.INSTRUCTION_TERMINAL_STATES or instruction["status"] == "held":
                continue
            self.drive_payment(caller, instruction)
        statuses = [i["status"] for i in row["instructions"]]
        if statuses and all(s in T.INSTRUCTION_TERMINAL_STATES for s in statuses) and row["status"] == "executing":
            row["status"] = "settled" if all(s == "confirmed" for s in statuses) else "partially_settled"  # states.ts resolveSetOutcome
            self.append_trail("set.settled", caller["credentialId"], {"outcome": row["status"], "confirmed": statuses.count("confirmed"), "failed": statuses.count("failed"),
                                                                       "rejected": statuses.count("rejected")}, subject_id=set_id)
        return 200, {"setId": set_id, "setStatus": row["status"],
                     "instructions": [{"instructionId": i["id"], "sequence": i["sequence"], "status": i["status"], "txHash": i["txHash"], "holdId": i["holdId"],
                                       "failureReason": i["failureReason"], "waiting": None} for i in row["instructions"]]}

    def drive_payment(self, caller: Dict[str, Any], instruction: Dict[str, Any]) -> None:
        """
        `drivePayment`: the quote reserves the platform's ceiling (U3's per-payment refusal where the balance cannot cover it — the instruction
        fails naming it), the chain's dry run refuses a transfer the key cannot cover, the key is delegated on its first payment, the operation
        is signed, sponsored and sent, and when the platform reports it landed the debit is taken at actual cost, the instruction is confirmed
        with its txHash and gasValue, and the trail's instruction.confirmed row carries the platform's own figures and words.
        """
        account = self.aap_account_id
        key = "op:%s" % instruction["id"]
        amount = int(instruction["amountMinor"])
        ceiling = self.quote_ceiling_usd_cents
        balance = self.platform.balance(account)
        if balance["available_usd_cents"] < ceiling:
            sentence = PLATFORM_INSUFFICIENT_GAS % (T.format_usd_cents(balance["available_usd_cents"]), "payment", T.format_usd_cents(ceiling), T.format_usd_cents(T.GAS_CREDIT_USD_CENTS))
            self.fail_instruction(caller, instruction, "GAS_SHORTFALL: %s" % sentence, {"platformCode": "insufficient_gas", "said": sentence})
            return
        if self.chain.balance_of(self.source_account) < amount:
            self.fail_instruction(caller, instruction, "PAYMENT_UNPRICED: This payment could not be priced: %s. The answer will be the same until what it named is resolved." % ESTIMATE_REVERTED_CLAUSE,
                                  {"said": ESTIMATE_REVERTED_SAID})
            return
        user_op_hash = "0x" + secrets.token_hex(32)
        tx_hash = "0x" + secrets.token_hex(32)
        self.platform.reserve(account, ceiling, key, instruction["chain"], "gas reserved, at most %s, for %s on %s" % (T.format_usd_cents(ceiling), user_op_hash, instruction["chain"]))
        self.delegated = True
        self.chain.transfer(self.source_account, instruction["address"], amount)
        actual = self.actual_gas_usd_cents
        self.platform.release(key)
        self.platform.debit(account, actual + self.platform.debit_gap_cents, key + ":debit", instruction["chain"], user_op_hash, tx_hash)
        now = self._now_iso()
        instruction["status"] = "confirmed"
        instruction["txHash"] = tx_hash
        instruction["executionValue"] = dict(instruction["entryValue"] or {}, kind="execution", occurredAt=now, valuationId="val-" + secrets.token_hex(4))
        gas_wei = actual * 10 ** 14  # the native coin at US$1,000.00 in this double: one cent is 10^14 wei
        instruction["gasValue"] = {"asset": "ETH", "assetDecimals": 18, "amountAssetMinor": str(gas_wei), "baseCurrency": "USD", "baseDecimals": 2, "amountBaseMinor": str(actual),
                                   "amountUsdMinor": str(actual), "rate": {"source": "double", "observedAt": now, "rateE8": "100000000000"}, "kind": "execution",
                                   "valuationId": "val-" + secrets.token_hex(4), "occurredAt": now}
        self.append_trail(T.INSTRUCTION_CONFIRMED, caller["credentialId"], {
            "txHash": tx_hash, "userOpHash": user_op_hash, "payloadKind": "user_operation", "road": "gas_roads", "sponsor": self.sponsor, "paymaster": self.paymaster,
            "gasDebitUsdCents": str(actual), "gasDebit": T.format_usd_cents(actual), "gasWords": T.gas_debit_words(actual), "reservationUsdCents": str(ceiling),
            "actualCostWei": str(gas_wei), "gasUsed": "150000", "effectiveGasPrice": str(gas_wei // 150000), "settlePriceUsd": "1000.00", "blockNumber": str(20000000 + len(self.trail)),
            "executionValuationId": instruction["executionValue"]["valuationId"], "gasValuationId": instruction["gasValue"]["valuationId"]}, subject_id=instruction["id"])

    def fail_instruction(self, caller: Dict[str, Any], instruction: Dict[str, Any], reason: str, detail: Dict[str, Any]) -> None:
        """`failInstruction`: one payee's failure is recorded on that payee and nothing else."""
        instruction["status"] = "failed"
        instruction["failureReason"] = reason
        self.append_trail("instruction.failed", caller["credentialId"], dict(detail, reason=reason, payloadKind="user_operation", road="gas_roads"), subject_id=instruction["id"])

    # -- two workspaces on one estate (Spec T14) ------------------------------------------------------------------------------------
    def owns(self, path: str, headers: Dict[str, str], data: Optional[bytes]) -> bool:
        """Whether this workspace's own records answer a request: its session's cookie, its invitation's token at the invitation road, or its passkey at the sign-in road."""
        for part in headers.get("cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == H.SESSION_COOKIE and value in self.sessions:
                return True
        if path not in ("/v1/auth/invite/options", "/v1/auth/invite/verify", "/v1/auth/login/verify"):
            return False
        try:
            body = json.loads(data.decode("utf-8")) if data else {}
        except ValueError:
            return False
        if not isinstance(body, dict):
            return False
        if path.startswith("/v1/auth/invite/"):
            token = body.get("token")
            return isinstance(token, str) and hashlib.sha256(token.encode()).hexdigest() in self.invites
        response = body.get("response") if isinstance(body.get("response"), dict) else {}
        return isinstance(response.get("id"), str) and response["id"] in self.passkeys

    def set_view(self, row: Dict[str, Any], caller: Dict[str, Any]) -> Dict[str, Any]:
        current = [a for a in self.approvals.get(row["id"], []) if a["setDigest"] == row["setDigest"]]
        view = {k: row[k] for k in ("id", "reference", "realm", "idempotencyKey", "status", "sourceAccount", "authorCredentialId", "setDigest", "createdAt", "submittedAt", "approvedAt", "executedAt")}
        view["aggregate"] = {"asset": "USDC", "assetDecimals": 6, "amountAssetMinor": "0", "baseCurrency": "USD", "baseDecimals": 2, "amountBaseMinor": row["aggregateBaseMinor"],
                             "amountUsdMinor": row["aggregateUsdMinor"], "rate": {"source": "double", "observedAt": row["createdAt"], "rateE8": "100000000"}, "kind": "entry", "valuationId": "", "occurredAt": row["createdAt"]}
        view["approval"] = {"approvalsRequired": row["approvalsRequired"], "approvalsGiven": len(current), "bandThresholdBaseMinor": row["bandThresholdBaseMinor"], "aggregateBaseMinor": row["aggregateBaseMinor"],
                            "eligibleApproverCredentialIds": list(self.second_approvers), "approvedByCredentialIds": [a["credentialId"] for a in current], "submitterCredentialId": row["authorCredentialId"]}
        view["instructions"] = [dict(i) for i in row["instructions"]]
        return view

    def submit_set(self, headers: Dict[str, str], set_id: str) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        row = self.sets.get(set_id)
        if not row:
            raise Refusal("SET_NOT_APPROVABLE", detail={"cause": "no such run"})
        if row["status"] != "draft":
            raise Refusal("SET_NOT_EDITABLE", detail={"status": row["status"]})
        row["status"] = "pending_approval"
        row["submittedAt"] = self._now_iso()
        if row["approvalsRequired"] == 0:
            row["status"] = "approved"
            row["approvedAt"] = self._now_iso()
            return 200, {"status": "approved", "setDigest": row["setDigest"], "approvalsRequired": 0}
        return 200, {"status": "pending_approval", "setDigest": row["setDigest"], "approvalsRequired": row["approvalsRequired"]}

    def approval(self, headers: Dict[str, str], set_id: str, action: str, body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "approver", mutating=True)
        row = self.sets.get(set_id)
        if not row:
            raise Refusal("SET_NOT_APPROVABLE", detail={"cause": "no such run"})
        if row["status"] != "pending_approval":
            raise Refusal("SET_NOT_APPROVABLE", detail={"status": row["status"]})
        facts = self.charter_facts(caller)
        may, cause = self.may_approve(facts, row["authorCredentialId"], caller["credentialId"])
        if not may:
            raise self.approval_refusal(cause or "charter_silent", facts, "a payment run", caller["roles"])
        challenge = self.challenge("set.approve", "%s|%s" % (row["setDigest"], caller["credentialId"]), 0)
        if action == "challenge":
            return 200, {"challenge": challenge, "setDigest": row["setDigest"]}
        response = (body or {}).get("response") or {}
        stored = self.passkeys.get(response.get("id", ""))
        if not stored or stored["credentialId"] != caller["credentialId"]:
            raise Refusal("STEP_UP_INVALID", detail={"cause": "that passkey is not enrolled for this credential"})
        try:
            stored["signCount"] = PK.verify_assertion(response, challenge, self.origin, self.rp_id, stored["publicKey"], stored["signCount"])
        except PK.PasskeyRefused as err:
            raise Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]})
        if any(a["credentialId"] == caller["credentialId"] for a in self.approvals[set_id]):
            raise Refusal("APPROVER_ALREADY_SIGNED", detail={"setId": set_id, "credentialId": caller["credentialId"]})
        self.approvals[set_id].append({"credentialId": caller["credentialId"], "setDigest": row["setDigest"]})
        count = len([a for a in self.approvals[set_id] if a["setDigest"] == row["setDigest"]])
        if count >= row["approvalsRequired"]:
            row["status"] = "approved"
            row["approvedAt"] = self._now_iso()
        return 200, {"status": row["status"], "approvalsGiven": count, "approvalsRequired": row["approvalsRequired"], "setDigest": row["setDigest"]}

    # -- the journey (services/journey.ts) ------------------------------------------------------------------------
    def journey(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "viewer")
        charter = any(iv["interviewType"] == "policy" and iv["state"] in ("compiled", "written") for iv in self.interviews.values())
        account = any(iv["interviewType"] == "wallet_account" and iv["state"] in ("compiled", "written") for iv in self.interviews.values())
        worked = bool(self.payees) and bool(self.sets)
        done = [charter, account, worked, False, False, False, False]
        last = max([i + 1 for i, d in enumerate(done) if d] or [0])
        current = min(7, last + 1)
        names = ["Run the Policy Interview", "Create the first wallet account", "Work the sandbox", "The acceptance rehearsal", "Verify the estate’s identity", "The transit ceremony", "Live"]
        routes = ["/onboarding", "/onboarding", "/payees", "/", "/identity", "/", "/"]
        hands = ["estate", "estate", "estate", "officer", "estate", "officer", "estate"]
        stages = [{"number": i + 1, "id": H.JOURNEY_STAGE_IDS[i], "name": names[i], "meaning": "", "done": done[i], "current": i + 1 == current, "route": routes[i], "hand": hands[i]} for i in range(7)]
        road = "wizard" if "author" in caller["roles"] else "registers"
        return 200, {"road": road, "realm": "sandbox", "live": False, "currentStage": current, "stageCount": 7, "landingRoute": routes[current - 1] if road == "wizard" else "/", "stages": stages}


# ---------------------------------------------------------------------------
# A runner wired to the double, for the tests that follow.
# ---------------------------------------------------------------------------
def runner_on(double: EstateDouble, tmp: str, invite: Optional[str] = None, start_at: Optional[str] = None, said: Optional[List[str]] = None,
              treasury_invite: Optional[str] = None, admin_env: bool = True, **kwargs: Any) -> H.Runner:
    """
    A runner wired to the double. Spec T14: unless told otherwise it is given the Treasury founder's invitation (the Treasury double mints one; a
    stored passkey makes it unspent) and the platform's admin credential is filed in the store's admin.env, as Bear files it — `admin_env=False`
    is the estate whose operator filed nothing.
    """
    store = os.path.join(tmp, "store")
    os.makedirs(store, exist_ok=True)
    platform = getattr(double, "platform", None)
    env_path = os.path.join(store, T.ADMIN_ENV_FILE)
    if admin_env and platform is not None and not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as handle:
            handle.write("%s=%s\n%s=%s\n" % (T.ADMIN_ENV_URL_KEY, PLATFORM_BASE, T.ADMIN_ENV_KEY_KEY, platform.admin_key))
        os.chmod(env_path, 0o600)
    treasury = getattr(double, "treasury", None)
    if treasury_invite is None and treasury is not None:
        treasury_invite = treasury.mint_founder_link()
    return H.Runner(double.base, store, invite, False, start_at, os.path.join(tmp, "out"), transport=double,
                    say=(said.append if said is not None else (lambda s: None)), sleep=lambda s: None, treasury_invite=treasury_invite, **kwargs)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheDoubleTellsTheTruth(unittest.TestCase):
    """The double refuses what the estate refuses, with the estate's own sentence and status."""

    def setUp(self):
        self.double = EstateDouble()
        self.tmp = tempfile.mkdtemp()
        self.link = self.double.mint_founder_link()
        self.runner = runner_on(self.double, self.tmp, invite=self.link)
        self.founder = self.runner.people[A.FOUNDER]

    def request(self, person, method, path, body=None, csrf=True, headers=None):
        return self.runner.request(person, method, path, body, "test", csrf=csrf, headers=headers)

    def test_a_call_with_no_session_is_not_authenticated(self):
        answer = self.request(None, "GET", "/v1/journey")
        self.assertEqual(answer.status, 401)
        self.assertEqual(answer.refusal["code"], "NOT_AUTHENTICATED")
        self.assertEqual(answer.refusal["message"], "You are not signed in.")

    def test_the_invitation_road_ends_in_a_session_and_a_stored_key(self):
        verified = self.runner.enrol_by_invite(self.founder, self.link, "test")
        self.assertEqual(verified.status, 200, verified.text)
        self.assertEqual(self.founder.session["workspace"]["name"], A.ESTATE["company"])
        self.assertIn("author", self.founder.roles)
        self.assertTrue(self.founder.csrf)
        path = self.runner.key_path(self.founder)
        self.assertTrue(os.path.exists(path))
        self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
        # the same link a second time is spent
        second = self.request(None, "POST", "/v1/auth/invite/options", {"token": H.token_of_link(self.link), "issuedAtMs": H.now_ms(), "response": {}}, csrf=False)
        self.assertEqual(second.status, 401)
        self.assertEqual(second.refusal["message"], "This invite link is expired or has already been used.")

    def test_a_mutating_call_without_the_csrf_header_is_refused_in_the_guards_words(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        answer = self.request(self.founder, "POST", "/v1/workspace/display-currency", {"displayCurrency": "AUD"}, csrf=False)
        self.assertEqual(answer.status, 401)
        self.assertEqual(answer.refusal["code"], "NOT_AUTHENTICATED")
        self.assertEqual(answer.refusal["detail"]["cause"], "missing or incorrect CSRF token")
        with_token = self.request(self.founder, "POST", "/v1/workspace/display-currency", {"displayCurrency": "AUD"})
        self.assertEqual(with_token.status, 200)

    def test_the_onboarding_routes_run_no_csrf_check_exactly_as_the_code_has_it(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        answer = self.request(self.founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"}, csrf=False)
        self.assertEqual(answer.status, 200, answer.text)

    def test_a_viewer_at_an_author_route_hears_the_room_sentence(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        olive = self.runner.people[A.VIEWER_INVITED]
        minted = self.request(self.founder, "POST", "/v1/invites", {"displayName": olive.name, "email": olive.email, "role": "viewer"})
        self.assertEqual(minted.status, 201, minted.text)
        self.runner.enrol_by_invite(olive, minted.json["url"], "test")
        self.assertEqual(olive.roles, ["viewer"])
        answer = self.request(olive, "POST", "/v1/payees", {"displayName": "x", "addresses": []})
        self.assertEqual(answer.status, 403)
        self.assertEqual(answer.refusal["code"], "ROLE_NOT_GRANTED")
        self.assertEqual(answer.refusal["message"],
                         "You are signed into %s as a viewer. This action needs an author — permissions come from your organisation’s policy, "
                         "not from this application. %s" % (A.ESTATE["company"], ESTATE_KEY_CURE))
        self.assertEqual(answer.refusal["detail"], {"workspace": A.ESTATE["company"], "held": "viewer", "required": "author"})

    def test_principal_is_refused_by_name(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        answer = self.request(self.founder, "POST", "/v1/invites", {"displayName": "P", "email": "harness+p@aeredium.io", "role": "principal"})
        self.assertEqual(answer.status, 422)
        self.assertEqual(answer.refusal["code"], "INVITE_ROLE_NOT_AVAILABLE")
        self.assertEqual(answer.refusal["message"], "That role cannot be invited yet. Choose one of the roles this centre offers today.")

    def test_an_author_invitation_mints_a_credential_of_the_persons_own_and_the_estate_before_spec_91_enrolled_the_founders(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        ada = self.runner.people["ada"]
        minted = self.request(self.founder, "POST", "/v1/invites", {"displayName": ada.name, "email": ada.email, "role": "author"})
        self.assertEqual(minted.status, 201)
        self.assertNotEqual(minted.json["credentialId"], self.founder.credential_id, "Spec 91: the invite mints a credential of the person's own (services/invites.ts, mintAuthorCredential)")
        self.assertEqual(minted.json["invite"]["credentialId"], minted.json["credentialId"])
        self.assertEqual(self.double.credentials[minted.json["credentialId"]], {"access": "sign+audit", "name": "Founder (author) — Ada Approver", "entry": self.double.authorship_entry["id"]},
                         "on the entry the founder's author credential is bound to, named for the entry and the person")
        self.runner.enrol_by_invite(ada, minted.json["url"], "test")
        self.assertEqual(ada.credential_id, minted.json["credentialId"], "redemption binds the passkey to that invitation's credential")
        self.assertEqual(ada.roles, ["author", "viewer"], "the entry's powers, and no seat: the redemption seats only whom a written charter names")
        # the estate of the four live runs, behind the knob
        before = EstateDouble(before_spec_91=True)
        link = before.mint_founder_link()
        runner = runner_on(before, self.tmp, invite=link)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        minted = runner.request(founder, "POST", "/v1/invites", {"displayName": ada.name, "email": ada.email, "role": "author"}, "test")
        self.assertEqual(minted.json["credentialId"], founder.credential_id, "before Spec 91 the invite enrolled the founder's own credential, as services/invites.ts at e651616 resolved it")

    def test_a_replayed_challenge_and_a_wrong_rp_id_are_refused_in_the_servers_words(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        first, bundle = self.runner.sign_in(self.founder, "test")
        self.assertEqual(first.status, 200, first.text)
        replay, _ = self.runner.sign_in(self.founder, "test", replay_of=bundle)
        self.assertEqual(replay.status, 403)
        self.assertEqual(replay.refusal["code"], "STEP_UP_STALE")
        self.assertEqual(replay.refusal["detail"]["cause"], "challenge already used")
        wrong, _ = self.runner.sign_in(self.founder, "test", rp_id="wrong.invalid")
        self.assertEqual(wrong.status, 403)
        self.assertEqual(wrong.refusal["code"], "STEP_UP_INVALID")
        self.assertEqual(wrong.refusal["detail"]["cause"], "Unexpected RP ID hash")

    def test_a_stale_issuance_is_refused(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        opened = self.request(self.founder, "POST", "/v1/auth/login/options", {}, csrf=False)
        assertion = self.founder.passkey.assertion(opened.json["options"]["challenge"], rp_id=opened.json["options"]["rpId"], origin=self.runner.origin)
        answer = self.request(self.founder, "POST", "/v1/auth/login/verify", {"nonce": opened.json["nonce"], "issuedAtMs": opened.json["issuedAtMs"] - STEPUP_MAX_AGE_MS - 1000, "response": assertion}, csrf=False)
        self.assertEqual(answer.status, 403)
        self.assertEqual(answer.refusal["code"], "STEP_UP_STALE")

    def test_the_interview_refuses_the_answers_validate_value_refuses(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        started = self.request(self.founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"})
        iv = started.json["interview"]["id"]
        unserved = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "B4", "value": {"choices": []}})
        self.assertEqual(unserved.status, 400)
        self.assertEqual(unserved.refusal["detail"]["cause"], "this question is not asked given the answers so far")
        wrong_option = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "A1", "value": {"text": ""}})
        self.assertEqual(wrong_option.refusal["detail"]["cause"], "an answer is required here")
        compiled = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/compile" % iv, {})
        self.assertEqual(compiled.status, 409)
        self.assertEqual(compiled.refusal["detail"]["cause"], "the compiler reads only confirmed interviews")

    def test_a_quorum_above_the_roster_is_refused_at_the_page(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        started = self.request(self.founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"})
        iv = started.json["interview"]["id"]
        for qid in ("A1", "A4", "A5", "A8", "A9", "A11", "B1", "B2", "B3", "C9S", "C9"):
            answer = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": qid, "value": A.POLICY_ANSWERS[qid]})
            self.assertEqual(answer.status, 200, answer.text)
        too_many = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "C10", "value": {"choice": "5"}})
        self.assertEqual(too_many.status, 400)
        self.assertEqual(too_many.refusal["message"], "You have named 4 people; a quorum of 5 can never be met. Name more people first, or choose 4.")

    def test_a_malformed_address_is_refused_in_the_doors_own_sentence_and_a_wrong_checksum_is_accepted_lower_cased(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        bad = self.request(self.founder, "POST", "/v1/payees", {"displayName": "x", "addresses": [{"chain": "ethereum", "address": "0xJohnDoe"}]})
        self.assertEqual(bad.status, 422)
        self.assertEqual(bad.refusal["code"], "ADDRESS_MALFORMED")
        self.assertEqual(bad.refusal["message"], "That is not an address Ethereum can pay, so nothing was saved. On Ethereum, an address is 0x followed by exactly 40 hexadecimal characters.")
        broken = T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))
        accepted = self.request(self.founder, "POST", "/v1/payees", {"displayName": "x", "addresses": [{"chain": "ethereum", "address": broken}]})
        self.assertEqual(accepted.status, 201, "payeeaddress.ts lower-cases; the mixed-case form is a checksum, not an identity")
        self.assertEqual(accepted.json["payee"]["addresses"][0]["address"], broken.lower())

    def test_the_read_back_speaks_a_list_entry_in_the_order_jsonb_stores_it(self):
        """The live estate, 20 September 2026: 'Harriet Founder — Authorise payments — harness+harriet@aeredium.io', for an entry sent as name, email, role."""
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        started = self.request(self.founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"})
        iv = started.json["interview"]["id"]
        for qid in ("A1", "A4", "A5", "A8"):
            answer = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": qid, "value": A.POLICY_ANSWERS[qid]})
            self.assertEqual(answer.status, 200, answer.text)
        self.assertEqual(list(A.POLICY_ANSWERS["A8"]["entries"][0].keys()), ["name", "email", "role"], "the book sends the entry as the wizard does")
        stored = self.double.latest(iv)["A8"]["value"]["entries"][0]
        self.assertEqual(list(stored.keys()), ["name", "role", "email"], "jsonb: shortest key first, then byte order")
        self.assertEqual(self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "A9", "value": A.POLICY_ANSWERS["A9"]}).status, 200)
        page = self.request(self.founder, "GET", "/v1/onboarding/interviews/%s" % iv)
        self.assertEqual(page.json["question"]["questionId"], "A11")
        # the read-back is refused before the questions are done, so the spoken form is read off the double's own renderer
        lines = self.double.readback_lines_for_test(iv)
        a8 = next(l for l in lines if l["questionId"] == "A8")
        self.assertEqual(a8["spoken"], "Harriet Founder — Authorise payments — harness+harriet@aeredium.io; Ada Approver — Release payments — harness+ada@aeredium.io; "
                                       "Ben Signatory — Authorise payments — harness+ben@aeredium.io; Cora Clerk — Enter payments — harness+cora@aeredium.io")

    def test_the_currency_is_read_back_as_main_speaks_it_and_as_spec_88_will(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        started = self.request(self.founder, "POST", "/v1/onboarding/interviews", {"interviewType": "policy"})
        iv = started.json["interview"]["id"]
        for qid in ("A1", "A4", "A5"):
            self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": qid, "value": A.POLICY_ANSWERS[qid]})
        a5 = next(l for l in self.double.readback_lines_for_test(iv) if l["questionId"] == "A5")
        self.assertEqual(a5["spoken"], '{"text":"AUD"}', "main: the currency kind falls to the switch's default arm, JSON.stringify")
        self.double.currency_spoken_as_code = True
        a5 = next(l for l in self.double.readback_lines_for_test(iv) if l["questionId"] == "A5")
        self.assertEqual(a5["spoken"], "AUD", "Spec 88: a currency is read back as its code")

    def walk(self, interview_type, overrides=None, stop_at=None):
        """Start an interview as the founder and answer every page from the book, `overrides` taking a question's place; the last page is returned."""
        started = self.request(self.founder, "POST", "/v1/onboarding/interviews", {"interviewType": interview_type})
        self.assertEqual(started.status, 200, started.text)
        iv = started.json["interview"]["id"]
        page = started.json["page"]
        for _ in range(60):
            question = page.get("question")
            if question is None or page.get("state") != "in_progress":
                break
            qid = question["questionId"]
            if qid == stop_at:
                break
            value = (overrides or {}).get(qid, A.ANSWERS[interview_type].get(qid))
            answer = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": qid, "value": value})
            self.assertEqual(answer.status, 200, answer.text)
            page = answer.json
        return iv, page

    def compile_policy(self):
        """The founder's road to a written policy charter: the walk, the read-back, the confirm under the passkey, the compile."""
        iv, page = self.walk("policy")
        self.assertEqual(page["state"], "at_read_back")
        compiled = self.runner.confirm_and_compile("test", "policy", iv, self.founder, page)
        return compiled["charter"]

    def test_the_payee_door_refuses_a_venues_contract_by_name_where_the_written_policy_charter_says_so(self):
        """Spec 92 (services/payees.ts, assertPayeeIsNotVenueContract): PAYEE_IS_VENUE_CONTRACT, 422, in payeeIsVenueContractSentence's words — and only then."""
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        venue = T.venue_address_for_probe()["address"]
        body = {"displayName": "Venue probe", "addresses": [{"chain": "ethereum", "address": venue}]}
        accepted = self.request(self.founder, "POST", "/v1/payees", body)
        self.assertEqual(accepted.status, 201, "no policy charter is written yet: the door reads no No and accepts, the founder's default")
        charter = self.compile_policy()
        self.assertEqual(charter["payeeVenueContracts"], "refused", "the book answers C19 No")
        refused = self.request(self.founder, "POST", "/v1/payees", body)
        self.assertEqual(refused.status, 422)
        self.assertEqual(refused.refusal["code"], "PAYEE_IS_VENUE_CONTRACT")
        self.assertEqual(refused.refusal["message"], "This address is the contract of Uniswap v3 on ethereum. Your charter says a payee must be a wallet held by a person or a company (question C19). Nothing was saved.")
        self.assertEqual(refused.refusal["detail"], {"venue": "uniswap_v3", "chain": "ethereum", "address": venue, "charterQuestionId": "C19"})
        self.assertEqual(refused.refusal["provenance"], {"source": "charter", "reference": "C19"})
        self.assertIsNone(H.refusal_without_why(refused.status, refused.text), "a refusal that says why")
        self.assertEqual(len(self.double.payees), 1, "nothing was saved")
        other = self.request(self.founder, "POST", "/v1/payees", {"displayName": "x", "addresses": [{"chain": "ethereum", "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]})
        self.assertEqual(other.status, 201, "only a known venue's contract is refused; a wallet is a wallet")
        # the table is the engine's, row for row: every row is refused on its chain and accepted on another
        for venue_id, chain, address in VENUE_CONTRACTS:
            row = self.request(self.founder, "POST", "/v1/payees", {"displayName": "row", "addresses": [{"chain": chain, "address": address}]})
            self.assertEqual(row.status, 422, (venue_id, chain))
            self.assertEqual(row.refusal["message"], payee_is_venue_contract_sentence(VENUE_NAMES[venue_id], chain))
        elsewhere = self.request(self.founder, "POST", "/v1/payees", {"displayName": "row", "addresses": [{"chain": "polygon", "address": venue}]})
        self.assertEqual(elsewhere.status, 201, "the same bytes on a chain the table knows no contract on are a wallet as far as this estate can tell")
        # the two dials: a door that refuses regardless, under Spec T8's stand-in; a door that saves regardless
        for dial, status, code in ((True, 422, "ADDRESS_PROPOSAL_REFUSED"), (False, 201, None)):
            self.double.refuses_venue_contract = dial
            answer = self.request(self.founder, "POST", "/v1/payees", body)
            self.assertEqual(answer.status, status, dial)
            if code:
                self.assertEqual(answer.refusal["code"], code)
                self.assertEqual(answer.refusal["message"], VENUE_STIPULATION)
        self.double.refuses_venue_contract = None

    def test_a_charter_whose_c19_is_yes_compiles_accepted_and_the_door_saves_the_venues_contract(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        with unittest.mock.patch.dict(A.POLICY_ANSWERS, {"C19": {"choice": A.VENUE_YES}}):
            charter = self.compile_policy()
        self.assertEqual(charter["payeeVenueContracts"], "accepted")
        body = {"displayName": "Venue probe", "addresses": [{"chain": "ethereum", "address": T.venue_address_for_probe()["address"]}]}
        self.assertEqual(self.request(self.founder, "POST", "/v1/payees", body).status, 201)

    def test_the_policy_charter_carries_c11a_as_payee_approval_of_reads_it_and_c19_and_the_read_back_says_what_the_door_will_do(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        charter = self.compile_policy()
        census = ["%s <%s>" % (A.PEOPLE[k].name, A.PEOPLE[k].email) for k in A.CENSUS_ORDER]
        self.assertEqual(charter["payeeApproval"], {"answer": "change_approvers", "roster": census, "quorum": 2, "rosterQuestionId": "A8", "quorumQuestionId": "C12"})
        self.assertEqual(charter["payeeVenueContracts"], "refused")
        # the whitelist_mutation roster the answer drew up: the census of four at two (as before this question, which is the point of the second answer)
        self.assertEqual([s["user_id"] for s in self.double.whitelist_seats], [A.PEOPLE[k].email for k in A.CENSUS_ORDER])
        self.assertEqual(self.double.whitelist_threshold, 2)
        lines = self.double.readback_lines_for_test(next(iv for iv in self.double.interviews))
        by_id = {l["questionId"]: l for l in lines}
        self.assertEqual(by_id["C11A"]["spoken"], A.PAYEE_APPROVAL_CHANGE_APPROVERS)
        self.assertEqual(by_id["C11A"]["prompt"], "When a new payee address is added, who must approve it before it can be paid?")
        self.assertEqual(by_id["C19"]["spoken"], A.VENUE_NO)
        self.assertEqual(by_id["C19_DOOR"], {"questionId": "C19_DOOR", "prompt": "What happens to a venue’s contract entered as a payee",
                                             "spoken": "You answered No: such an address will be refused when entered.", "synthetic": True})
        self.assertNotIn("C11C", by_id, "asked only behind the CFO's answer")

    def test_c11as_other_two_answers_draw_up_their_own_rosters_and_the_cfo_unnamed_is_refused_by_name(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        first = {"C11A": {"choice": A.PAYEE_APPROVAL_PAYMENT_APPROVERS}}
        iv, page = self.walk("policy", first)
        latest = {qid: row["value"] for qid, row in self.double.latest(iv).items()}
        approval = self.double.payee_approval_of(latest)
        self.assertEqual(approval, {"answer": "payment_approvers", "roster": [A.PEOPLE["ada"].email], "quorum": 1, "rosterQuestionId": "C11", "quorumQuestionId": "C10"})
        self.assertEqual(self.request(self.founder, "DELETE", "/v1/onboarding/interviews/%s" % iv).status, 200)
        third = {"C11A": {"choice": A.PAYEE_APPROVAL_CFO}, "C11C": {"entries": [{"name": "Cora Clerk", "email": A.PEOPLE["cora"].email}]}}
        iv, page = self.walk("policy", third)
        latest = {qid: row["value"] for qid, row in self.double.latest(iv).items()}
        self.assertIn("C11C", latest, "C11C is served behind the third answer")
        self.assertEqual(self.double.payee_approval_of(latest), {"answer": "cfo", "roster": ["Cora Clerk <%s>" % A.PEOPLE["cora"].email], "quorum": 1,
                                                                 "rosterQuestionId": "C11C", "quorumQuestionId": "C11A", "cfo": {"name": "Cora Clerk", "email": A.PEOPLE["cora"].email}})
        latest["C11C"] = {"entries": []}
        with self.assertRaises(Refusal) as caught:
            self.double.payee_approval_of(latest)
        self.assertEqual(caught.exception.code, "CHARTER_INCOMPLETE")
        self.assertEqual(caught.exception.detail["cause"], "C11A chose the CFO’s authority to approve a new payee, but C11C names nobody")

    def test_the_account_interview_serves_the_wallets_people_and_tiers_and_speaks_them_as_the_estate_does(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        iv, page = self.walk("wallet_account", stop_at="WO3")
        self.assertEqual(page["question"]["questionId"], "WO3", "WO3 opens behind the named holder")
        self.assertEqual(page["question"]["priorValue"], {"cents": "100"}, "the figure that arrives written: one dollar, as the value on record")
        self.assertEqual(page["question"]["note"], V14_ADDED["WO3"]["note"])
        self.assertEqual(page["question"]["part"], "The wallet’s people")
        self.assertEqual(page["progress"]["of"], 18)
        served = [row["questionId"] for row in self.double.answers[iv]]
        self.assertEqual(served[-2:], ["WO1", "WO2"])
        wo1 = self.double.latest(iv)["WO1"]["value"]
        self.assertEqual(list(wo1.keys()), ["choice", "person"])
        self.assertEqual(list(wo1["person"].keys()), ["name", "email"], "jsonb: shortest key first")
        iv, page = self.walk("wallet_account")
        self.assertEqual(page["state"], "at_read_back")
        lines = {l["questionId"]: l for l in self.double.readback_lines_for_test(iv)}
        self.assertEqual(lines["WO1"]["spoken"], "Ben Signatory — %s." % A.PEOPLE["ben"].email)
        self.assertEqual(lines["WO1_TITLE"]["spoken"], "Ben Signatory is this wallet’s Officer: the one person who receives it and opens it on their own device.")
        self.assertEqual(lines["WO2"]["spoken"], "Harriet — %s — CEO — Founder" % A.PEOPLE["harriet"].email)
        self.assertEqual(lines["WO3"]["spoken"], "US$2 and 00 cents.")
        self.assertEqual(lines["WO4"]["spoken"], "US$10 and 00 cents.")
        self.assertEqual(lines["HOLD_NOT_WRITTEN"]["spoken"], TIER_HOLD_NOT_WRITTEN)
        self.assertEqual(lines["WQ_TIERS"]["spoken"], TIER_QUORUM_STANDS_ASIDE)
        compiled = self.runner.confirm_and_compile("test", "wallet_account", iv, self.founder, page)["charter"]
        self.assertEqual(compiled["holder"], {"held": "by_person", "name": "Ben Signatory", "email": A.PEOPLE["ben"].email, "title": "Officer"})
        self.assertEqual(compiled["signingTiers"], {"holderAloneUpToCents": "200", "twoSignaturesUpToCents": "1000",
                                                    "thirdParty": {"name": "Harriet", "surname": "Founder", "email": A.PEOPLE["harriet"].email, "title": "CEO"},
                                                    "holdNotWritten": TIER_HOLD_NOT_WRITTEN})
        self.assertEqual(compiled["signers"], ["Ada Approver <%s>" % A.PEOPLE["ada"].email, "Ben Signatory <%s>" % A.PEOPLE["ben"].email, "Harriet Founder <%s>" % A.PEOPLE["harriet"].email])
        self.assertIsNone(compiled["payeeApproval"])
        self.assertIsNone(compiled["payeeVenueContracts"])

    def test_person_or_none_is_validated_as_the_estate_validates_it(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        iv, page = self.walk("wallet_account", stop_at="WO1")
        self.assertEqual(page["question"]["kind"], "person_or_none")
        self.assertEqual(page["question"]["options"], [A.HOLDER_PERSON, A.HOLDER_NO_ONE])
        self.assertEqual(page["question"]["listFields"], [{"key": "name", "label": "Full name"}, {"key": "email", "label": "Work email"}])
        def refused(value):
            answer = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "WO1", "value": value})
            self.assertEqual(answer.status, 400, answer.text)
            self.assertEqual(answer.refusal["code"], "ANSWER_INVALID")
            return answer.refusal["detail"]["cause"]
        self.assertEqual(refused({"person": {"name": "Ben", "email": "b@x.io"}}), "choose whether one person holds this, or no one")
        self.assertEqual(refused({"choice": "Ben holds it"}), "the choice must be one of the options offered")
        self.assertEqual(refused({"choice": A.HOLDER_PERSON}), "name the person: full name and work email")
        self.assertEqual(refused({"choice": A.HOLDER_PERSON, "person": {"name": "", "email": "b@x.io"}}), "the person needs a full name")
        self.assertEqual(refused({"choice": A.HOLDER_PERSON, "person": {"name": "Ben Signatory", "email": " "}}), "the person needs a work email")
        self.assertEqual(refused({"choice": A.HOLDER_NO_ONE, "person": {"name": "Ben Signatory", "email": "b@x.io"}}), "“No one” names nobody; remove the person or choose the first option")
        nobody = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/answers" % iv, {"questionId": "WO1", "value": {"choice": A.HOLDER_NO_ONE}})
        self.assertEqual(nobody.status, 200)
        self.assertEqual(nobody.json["question"]["questionId"], "WO2", "a wallet held by no one is not asked WO3")
        self.assertEqual(nobody.json["progress"]["of"], 17)

    def test_the_tiers_two_contradictions_are_refused_at_the_read_back_in_the_specs_sentences(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        # WO4 not above WO3
        iv, page = self.walk("wallet_account", {"WO4": {"cents": A.MONEY["holder_alone_cents"]}})  # WO4 equal to WO3: not above it
        self.assertEqual(page["state"], "at_read_back", "the page does not judge the tiers; the read-back does")
        readback = self.request(self.founder, "GET", "/v1/onboarding/interviews/%s/readback" % iv)
        self.assertEqual(readback.status, 409)
        self.assertEqual(readback.refusal["code"], "CHARTER_INCOMPLETE")
        self.assertEqual(readback.refusal["message"], TIER_TWO_NOT_ABOVE_ONE)
        self.assertEqual(readback.refusal["walkBackTo"], {"questionId": "WO4"})
        self.assertEqual(readback.refusal["detail"], {"cause": TIER_TWO_NOT_ABOVE_ONE, "holderAloneUpToCents": A.MONEY["holder_alone_cents"], "twoSignaturesUpToCents": A.MONEY["holder_alone_cents"]})
        compiled = self.request(self.founder, "POST", "/v1/onboarding/interviews/%s/compile" % iv, {})
        self.assertEqual(compiled.status, 409, "the compile reads only confirmed interviews, and the confirm judges the tiers too")
        self.assertEqual(self.request(self.founder, "DELETE", "/v1/onboarding/interviews/%s" % iv).status, 200)
        # fewer than three people between WA1 and WO2: Ada alone at WA1, Harriet at WO2
        iv, page = self.walk("wallet_account", {"WA1": {"entries": [{"name": A.PEOPLE["ada"].name, "email": A.PEOPLE["ada"].email}]}})
        readback = self.request(self.founder, "GET", "/v1/onboarding/interviews/%s/readback" % iv)
        self.assertEqual(readback.status, 409)
        self.assertEqual(readback.refusal["message"], "Three signatures are asked above US$10 and 00 cents but only 2 people are named; name more or lower the tiers.")
        self.assertEqual(readback.refusal["walkBackTo"], {"questionId": "WA1"})
        self.assertEqual(readback.refusal["detail"]["named"], "2")
        self.assertEqual(tiers_need_three_people(usd_figure("1000"), 1), "Three signatures are asked above US$10 and 00 cents but only 1 person is named; name more or lower the tiers.")
        self.assertEqual(self.request(self.founder, "DELETE", "/v1/onboarding/interviews/%s" % iv).status, 200)
        # a title not of the three is the compiler's refusal, at the compile
        iv, page = self.walk("wallet_account", {"WO2": {"entries": [{"name": "Harriet", "surname": "Founder", "email": A.PEOPLE["harriet"].email, "title": "Chair"}]}})
        latest = {qid: row["value"] for qid, row in self.double.latest(iv).items()}
        with self.assertRaises(Refusal) as caught:
            self.double.compile_charter("wallet_account", latest, 14)
        self.assertEqual(caught.exception.detail["cause"], "the third party’s title must be one of CEO, CFO, COO; “Chair” is not one of them")
        # an estate before version 14 never serves the seven, and compiles no holder and no tiers
        older = EstateDouble(catalog_version=12)
        self.assertFalse(any(q.id in A.ADDED_IN_V14["wallet_account"] for q in older.catalog("wallet_account")))
        self.assertFalse(any(q.id in A.ADDED_IN_V14["policy"] for q in older.catalog("policy")))
        self.assertEqual(len(older.catalog("wallet_account")), len(A.ACCOUNT_CATALOG) - 4)
        self.assertEqual(len(older.catalog("policy")), len(A.POLICY_CATALOG) - 3)
        charter = older.compile_charter("wallet_account", {qid: row["value"] for qid, row in self.double.latest(iv).items() if qid not in ("WO1", "WO2", "WO3", "WO4")}, 12)
        self.assertNotIn("holder", charter)
        self.assertNotIn("signingTiers", charter)
        self.assertEqual(charter["signers"], ["Ada Approver <%s>" % A.PEOPLE["ada"].email, "Ben Signatory <%s>" % A.PEOPLE["ben"].email])

    def test_an_invitation_takes_its_seconds_on_the_shared_clock(self):
        clock = Clock()
        slow = EstateDouble(invite_seconds=4.0, clock=clock)
        link = slow.mint_founder_link()
        runner = runner_on(slow, self.tmp, invite=link, clock=clock)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        ada = runner.people["ada"]
        minted = runner.request(founder, "POST", "/v1/invites", {"displayName": ada.name, "email": ada.email, "role": "author"}, "test")
        self.assertEqual(minted.status, 201)
        self.assertEqual(minted.elapsed_ms, 4000)
        self.assertEqual([c.elapsed_ms for c in runner.calls if c.route == "POST /v1/invites"], [4000])
        self.assertTrue(all(c.elapsed_ms == 0 for c in runner.calls if c.route != "POST /v1/invites"))

    def test_a_run_without_a_funding_account_is_refused_in_the_routes_words(self):
        double = EstateDouble(funding_wallet="refused")  # Spec T13: no typed address stands in for a wallet; this estate's press is refused, so none is born
        link = double.mint_founder_link()
        runner = runner_on(double, self.tmp, invite=link)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        answer = runner.request(founder, "POST", "/v1/sets/review", {"pays": [{"oneOff": {"chain": "ethereum", "address": T.address("UNLISTED_ETHEREUM"), "declared": True}, "asset": "USDC", "chain": "ethereum", "amountMinor": "1000000"}], "duplicatesAcknowledged": False}, "test")
        # Spec 104 (routes/sets.ts requireSourceAccount): the pre-flight is gone; a run asked of an estate with no funding wallet is refused in the wallet's own sentence
        self.assertEqual(answer.status, 503)
        self.assertEqual(answer.refusal["code"], "WORKSPACE_NOT_PROVISIONED")
        self.assertEqual(answer.refusal["message"], NO_FUNDING_WALLET_SENTENCE)
        self.assertEqual(answer.refusal["detail"], {"cause": NO_FUNDING_WALLET_REASON})


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheWhitelistRoadMeetsItsQuorum(unittest.TestCase):
    """
    Spec T9 §6: the double's approve answers as the estate does after Spec 89 (aeredium/AERAccounts, commit 7d809e1,
    routes/payees.ts, services/payees.ts): the first press is pending with the count, the unsigned by name, and the
    sentence; the press by a different roster member meets the count and whitelists; a press by an approver whose key
    is on no seat of the roster is the platform's refusal, relayed with its words.

    A NOTE ON SPEC.md §6 AND THE CODE. §6 also says "a second press by the same person is refused as the platform
    refuses a repeated signature." The shipped Spec 89 code does NOT refuse it: routes/payees.test.ts ("the same
    person pressing again is told the same thing: the platform counts a signature once") answers 200 with the SAME
    pending body, and test/aapDouble.ts records a repeated signature idempotently. §6's own governing clause is
    "answers as the estate does after Spec 89", and APPROVER_ALREADY_SIGNED (refusals.ts) is the payments road's
    refusal, never the whitelist road's. So the double answers as the code does — 200, counted once — and this test
    asserts that; the disagreement is carried to Bear in the PR, not silently resolved in the double.
    """

    @classmethod
    def setUpClass(cls):
        # Spec T10: every person holds a credential of their own, and the charter seats Ada alone — so for Ben's press to reach the
        # platform an operator at the platform's console names his credential a second approver (the estate's seat road refuses him:
        # APPROVER_SEAT_NOT_IN_CHARTER). Without it the approve route's guard refuses him (TheFoundersRoad in test_aer360_stations).
        cls.double = EstateDouble(platform_names_approver=("ben",))
        cls.tmp = tempfile.mkdtemp()
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        cls.runner.run()  # S1–S6 compile the policy (establishing the whitelist roster) and seat Ada
        cls.founder = cls.runner.people["harriet"]
        cls.ada = cls.runner.people["ada"]
        cls.ben = cls.runner.people["ben"]

    def fresh_address(self):
        """A payee the founder creates and promotes now, so a fresh ceremony stands waiting for its two signatures."""
        created = self.runner.request(self.founder, "POST", "/v1/payees",
                                      {"displayName": "Spec T9 payee", "defaultAsset": "USDC", "defaultChain": "ethereum",
                                       "addresses": [{"chain": "ethereum", "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]}, "test")
        self.assertEqual(created.status, 201, created.text)
        address_id = created.json["payee"]["addresses"][0]["id"]
        promoted = self.runner.request(self.founder, "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, "test")
        self.assertEqual(promoted.status, 200, promoted.text)
        self.assertEqual(promoted.json["status"], "pending_promotion")
        self.assertEqual(promoted.json["ceremony"]["requiredSignatures"], 2)
        return address_id

    def press(self, who, address_id):
        return self.runner.request(who, "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")

    def test_the_first_press_is_pending_with_the_count_the_unsigned_and_the_sentence(self):
        first = self.press(self.ada, self.fresh_address())
        self.assertEqual(first.status, 200, first.text)
        self.assertEqual(first.json, {
            "whitelistStatus": "pending_promotion",
            "approvals": {"required": 2, "collected": 1, "remaining": 1},
            "may_still_approve": ["Harriet Founder", "Ben Signatory", "Cora Clerk"],
            "sentence": "1 of 2 approvals recorded for this address. One more is needed, from Harriet Founder, Ben Signatory or Cora Clerk. "
                        "The address is not payable until then.",
        })

    def test_a_press_by_a_different_roster_member_meets_the_count_and_whitelists(self):
        address_id = self.fresh_address()
        self.press(self.ada, address_id)
        second = self.press(self.ben, address_id)
        self.assertEqual(second.status, 200, second.text)
        self.assertEqual(second.json, {"whitelistStatus": "whitelisted"}, "the second signature meets the quorum; nothing about waiting")
        # the platform's rule (Spec T10): each press bound the presser's own credential to the seat the estate named, and counted it once
        seats = {s["user_id"]: s["credential_id"] for s in self.double.whitelist_seats}
        self.assertEqual(seats[self.ada.email], self.ada.credential_id)
        self.assertEqual(seats[self.ben.email], self.ben.credential_id)
        self.assertNotEqual(self.ada.credential_id, self.ben.credential_id)

    def test_the_same_person_pressing_again_is_told_the_same_thing_the_platform_counts_a_signature_once(self):
        # Spec 89's code (routes/payees.test.ts): 200 with the same pending body, NOT a refusal. See the class docstring.
        address_id = self.fresh_address()
        first = self.press(self.ada, address_id)
        again = self.press(self.ada, address_id)
        self.assertEqual(again.status, 200, again.text)
        self.assertEqual(again.json, first.json, "the platform counts a signature once; the answer is unchanged")

    def test_the_pre_spec_89_knob_answers_the_status_alone(self):
        double = EstateDouble(pending_approval_says_why=False)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        runner.run()
        created = runner.request(runner.people["harriet"], "POST", "/v1/payees",
                                 {"displayName": "pre-89", "defaultAsset": "USDC", "defaultChain": "ethereum",
                                  "addresses": [{"chain": "ethereum", "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]}, "test")
        address_id = created.json["payee"]["addresses"][0]["id"]
        runner.request(runner.people["harriet"], "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, "test")
        first = runner.request(runner.people["ada"], "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        self.assertEqual(first.json, {"whitelistStatus": "pending_promotion"}, "the estate of 20 September 2026, before Spec 89: the status alone")

    def test_a_press_by_a_key_on_no_seat_is_the_platforms_refusal_relayed(self):
        # A roster of one (Ada). Ben is an approver on this estate (named at the platform's console), but his
        # key is on no seat of this roster, so the platform declines his signature and the estate relays it (Rule 13).
        double = EstateDouble(whitelist_roster=("ada",), platform_names_approver=("ben",))
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        runner.run()
        created = runner.request(runner.people["harriet"], "POST", "/v1/payees",
                                 {"displayName": "roster of one", "defaultAsset": "USDC", "defaultChain": "ethereum",
                                  "addresses": [{"chain": "ethereum", "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]}, "test")
        address_id = created.json["payee"]["addresses"][0]["id"]
        runner.request(runner.people["harriet"], "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, "test")
        runner.request(runner.people["ada"], "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        refused = runner.request(runner.people["ben"], "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        self.assertEqual(refused.status, 403)
        self.assertEqual(refused.refusal["code"], "SIGNATURE_NOT_COUNTED")
        self.assertEqual(refused.refusal["detail"]["platformSaid"], "not authorized")
        self.assertIsNone(H.refusal_without_why(refused.status, refused.text), "the refusal says who declined and why")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheDoubleLearnsSpec91(unittest.TestCase):
    """
    Spec T10 §6: the double mints a distinct credential per author invitation, binds the redeemed passkey to it, counts ceremony
    presses by credential_id (the platform's rule), carries the shared-credential marker on the People register for a person
    enrolled before Spec 91, refuses to seat a shared credential by name, retires the old binding on a re-invitation, and goes
    back to the pre-91 shape behind a knob.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def estate(self, **kwargs):
        double = EstateDouble(**kwargs)
        link = double.mint_founder_link()
        runner = runner_on(double, self.tmp, invite=link)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        return double, runner, founder

    def invite(self, runner, founder, person, role="author"):
        minted = runner.request(founder, "POST", "/v1/invites", {"displayName": person.name, "email": person.email, "role": role}, "test")
        self.assertEqual(minted.status, 201, minted.text)
        return minted

    def test_three_author_invitations_mint_three_distinct_credentials_on_the_authorship_entry_none_the_founders(self):
        double, runner, founder = self.estate()
        minted = [self.invite(runner, founder, runner.people[k]).json["credentialId"] for k in A.AUTHORS_INVITED]
        self.assertEqual(len(set(minted)), 3)
        self.assertNotIn(founder.credential_id, minted)
        for credential_id in minted:
            self.assertEqual(double.credentials[credential_id]["entry"], double.authorship_entry["id"], "the same entry: the same powers and not one more")
        self.assertEqual([a for a in double.audit if a.startswith("invite.minted author")][0].split(" enrolsCredentialId ")[1].split(" ")[0], minted[0])
        self.assertIn("mintedCredentialId %s" % minted[0], double.audit[-3])

    def test_redemption_binds_the_passkey_to_that_credential_and_the_register_shows_three_distinct_unmarked(self):
        double, runner, founder = self.estate()
        for key in A.AUTHORS_INVITED:
            person = runner.people[key]
            minted = self.invite(runner, founder, person)
            verified = runner.enrol_by_invite(person, minted.json["url"], "test")
            self.assertEqual(verified.json["credentialId"], minted.json["credentialId"])
            session = runner.request(person, "GET", "/v1/auth/session", None, "test")
            self.assertEqual(session.json["credentialId"], minted.json["credentialId"], "the session opened by the redemption carries the person's own credential")
        register = runner.request(founder, "GET", "/v1/invites", None, "test").json["invites"]
        authors = [r for r in register if r["role"] == "author"]
        self.assertEqual(len(authors), 3)
        self.assertEqual(len({r["credentialId"] for r in authors}), 3)
        for row in authors:
            self.assertEqual(row["state"], "redeemed")
            self.assertNotEqual(row["credentialId"], founder.credential_id)
            self.assertEqual(row["sharesCredentialWith"], [], "their own: nobody to share with")
        self.assertTrue(all(not k.startswith("_") for r in register for k in r), "the wire carries no private field")

    def test_two_policy_entries_bearing_authorship_are_refused_listing_both_and_nothing_is_minted(self):
        double, runner, founder = self.estate(second_authorship_entry=True)
        ada = runner.people["ada"]
        before = dict(double.credentials)
        refused = runner.request(founder, "POST", "/v1/invites", {"displayName": ada.name, "email": ada.email, "role": "author"}, "test")
        self.assertEqual(refused.status, 401)
        self.assertEqual(refused.refusal["code"], "INVITE_INVALID")
        self.assertEqual(refused.refusal["detail"]["cause"], "the account carries several policy entries bearing authorship; this invite must name which credential it enrols")
        self.assertIn(founder.credential_id, refused.refusal["detail"]["candidates"])
        self.assertIn("cred-cfo", refused.refusal["detail"]["candidates"])
        self.assertIn("%s (Founder (author))" % double.authorship_entry["id"], refused.refusal["detail"]["entries"])
        self.assertIn("pe-cfo (Casey CFO (author))", refused.refusal["detail"]["entries"])
        self.assertEqual(double.credentials, before, "nothing minted, the refusal came first")
        self.assertEqual([r for r in double.invites.values() if r.get("email") == ada.email], [], "no row")

    def test_a_press_is_counted_to_the_credential_that_made_it(self):
        """
        The platform's rule (Spec 91's builder, validateMultisigSigner; test/aapDouble.ts): on the shared credential, Ada's press binds
        her seat to it and Ben's press matches that seat by credential — one signature, as the fourth live run met. On credentials of
        their own, two presses are two of two.
        """
        # the estate of the four live runs: four people, one credential
        double = EstateDouble(before_spec_91=True)
        runner = runner_on(double, self.tmp, invite=double.mint_founder_link())
        runner.run()
        founder, ada, ben = runner.people["harriet"], runner.people["ada"], runner.people["ben"]
        self.assertEqual(ada.credential_id, founder.credential_id)
        address_id = self.fresh_address(runner, founder)
        first = runner.request(ada, "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        self.assertEqual(first.json["approvals"], {"required": 2, "collected": 1, "remaining": 1})
        self.assertEqual(first.json["may_still_approve"], ["Harriet Founder", "Ben Signatory", "Cora Clerk"])
        ada_seat = next(s for s in double.whitelist_seats if s["user_id"] == ada.email)
        self.assertEqual(ada_seat["credential_id"], founder.credential_id, "Ada's press bound her seat to the credential she wore: the founder's")
        second = runner.request(ben, "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        self.assertEqual(second.status, 200)
        self.assertEqual(second.json, first.json, "Ben's press matched Ada's seat by credential and counted nothing: the fourth live run's answer, word for word")
        self.assertEqual(next(s for s in double.whitelist_seats if s["user_id"] == ben.email)["credential_id"], "", "Ben's own seat stays empty")
        # credentials of their own, and Ben named an approver at the platform's console: two of two
        double = EstateDouble(platform_names_approver=("ben",))
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        runner.run()
        founder, ada, ben = runner.people["harriet"], runner.people["ada"], runner.people["ben"]
        address_id = self.fresh_address(runner, founder)
        runner.request(ada, "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        second = runner.request(ben, "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "test")
        self.assertEqual(second.json, {"whitelistStatus": "whitelisted"})
        ceremony = double.addresses[address_id]["ceremony"]
        self.assertEqual(ceremony["signatures"], [ada.credential_id, ben.credential_id])

    def test_a_seat_bound_to_the_shared_credential_is_moved_when_the_census_signs_the_change_and_the_persons_own_credential_then_counts(self):
        """
        Spec T12 met the seat bound to the founder's retired credential and Ada's own credential "not authorized" — SIGNATURE_NOT_COUNTED.
        Spec T15: the roster stands (governance established once), Ada's re-invitation proposes the move (Spec 95) and the platform holds it
        as a ceremony at the charter's count of two; S4 has the census sign it (Spec 99), the platform applies it, and Ada's own press counts.
        """
        double = EstateDouble(before_spec_91=True)
        runner = runner_on(double, self.tmp, invite=double.mint_founder_link())
        runner.run()  # Ada's press in S6 bound her seat to the shared credential
        founder = runner.people["harriet"]
        self.assertEqual(next(s for s in double.whitelist_seats if s["user_id"] == A.PEOPLE["ada"].email)["credential_id"], founder.credential_id)
        double.before_spec_91 = False
        again = runner_on(double, self.tmp, invite=runner.invite)
        outcomes = {o.station: o for o in again.run()}
        self.assertIs(again.facts["compile"]["policy"]["receipt"]["governanceAlreadyStood"], True, "a recompile leaves the rosters as they stand")
        ada = again.people["ada"]
        self.assertNotEqual(ada.credential_id, founder.credential_id, "brought in again on her own")
        self.assertIn("approver", ada.roles, "seated on redemption")
        # the redemption proposed the move, and the platform held it as a ceremony at two (Spec 95); S4 signed it (Spec 99)
        signing = again.facts["roster_signing"]
        self.assertEqual([r["outcome"] for r in signing], ["applied"], signing)
        self.assertEqual(signing[0]["seat"]["email"], ada.email)
        self.assertEqual(next(s for s in double.whitelist_seats if s["user_id"] == A.PEOPLE["ada"].email)["credential_id"], ada.credential_id, "the platform moved the seat to Ada's own credential")
        press = [c for c in again.calls if c.station == "S6" and c.route.endswith("/approve") and c.who == "Ada Approver"][0]
        self.assertEqual(press.status, 200, press.text)
        self.assertEqual(json.loads(press.text)["approvals"], {"required": 2, "collected": 1, "remaining": 1})
        self.assertEqual(outcomes["S6"].outcome, H.PASS, outcomes["S6"].line)
        self.assertIn("Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted", outcomes["S6"].line)
        for record in again.facts["payees"]:
            self.assertEqual(record["register_status"], "whitelisted")

    def test_people_already_on_a_shared_credential_are_marked_refused_a_seat_and_given_their_own_by_a_fresh_invitation(self):
        """Spec 91's own scenario (owncredential.test.ts, 'marks them on the register...'), against this double."""
        double, runner, founder = self.estate(before_spec_91=True, seat_completes_on_redemption=False)
        for station in ("station_s2", "station_s3"):
            getattr(runner, station)()
        ada, ben = runner.people["ada"], runner.people["ben"]
        for person in (ada, ben):
            runner.enrol_by_invite(person, self.invite(runner, founder, person).json["url"], "test")
            self.assertEqual(person.credential_id, founder.credential_id)
        double.before_spec_91 = False
        # THE REGISTER SAYS IT, naming the others from the estate's own passkey rows — the founder among them
        rows = {r["displayName"]: r for r in runner.request(founder, "GET", "/v1/invites", None, "test").json["invites"]}
        self.assertEqual(rows["Ada Approver"]["sharesCredentialWith"], ["Harriet", "Ben Signatory"])
        self.assertEqual(rows["Ben Signatory"]["sharesCredentialWith"], ["Harriet", "Ada Approver"])
        self.assertEqual(rows["Harriet"]["sharesCredentialWith"], ["Ada Approver", "Ben Signatory"], "the operator's invitation is its own person")
        self.assertEqual(H.shares_credential_sentence(rows["Ada Approver"]["sharesCredentialWith"]), "shares a credential with Harriet and Ben Signatory; invite them again to give them their own")
        # THE SEAT ROAD REFUSES BY NAME and writes nothing
        refused = runner.request(founder, "POST", "/v1/approver-seats/grant", {"email": ada.email}, "test")
        self.assertEqual(refused.status, 409)
        self.assertEqual(refused.refusal["code"], "APPROVER_SEAT_CREDENTIAL_SHARED")
        self.assertEqual(refused.refusal["message"], approver_seat_shared_sentence("", ["Harriet", "Ben Signatory"]))
        self.assertEqual(refused.refusal["detail"]["sharedWith"], "Harriet, Ben Signatory")
        self.assertEqual(double.second_approvers, [])
        seats = runner.request(founder, "GET", "/v1/approver-seats", None, "test").json
        seat = next(s for s in seats["seats"] if s["email"] == ada.email)
        self.assertEqual((seat["state"], seat["credentialId"]), ("enrolled_not_seated", founder.credential_id), "the panel still tells the truth")
        # A FRESH INVITATION mints her own; the redemption retires the old binding and seats her
        double.seat_completes_on_redemption = True
        again = self.invite(runner, founder, ada)
        own = again.json["credentialId"]
        self.assertNotEqual(own, founder.credential_id)
        verified = runner.enrol_by_invite(ada, again.json["url"], "test")
        self.assertEqual(verified.json["credentialId"], own)
        self.assertEqual(verified.json["approverSeat"], {"charterNamedThem": True, "granted": True, "note": None})
        self.assertEqual(double.second_approvers, [own])
        self.assertIn((ada.email.lower(), founder.credential_id), double.retired)
        self.assertTrue(any(a.startswith("person.credential_replaced %s: %s -> %s" % (ada.email.lower(), founder.credential_id, own)) for a in double.audit))
        rows = runner.request(founder, "GET", "/v1/invites", None, "test").json["invites"]
        adas = [r for r in rows if r["email"] == ada.email]
        self.assertEqual(len(adas), 2)
        self.assertEqual(next(r for r in adas if r["credentialId"] == own)["sharesCredentialWith"], [], "her newest invitation is her own and unmarked")
        self.assertEqual(next(r for r in adas if r["credentialId"] == founder.credential_id)["sharesCredentialWith"], [], "her earlier one is history")
        self.assertEqual(next(r for r in rows if r["email"] == ben.email)["sharesCredentialWith"], ["Harriet", "Ada Approver"], "Ben still shares, with the founder and the key Ada's earlier invitation bound")
        seat = next(s for s in runner.request(founder, "GET", "/v1/approver-seats", None, "test").json["seats"] if s["email"] == ada.email)
        self.assertEqual((seat["state"], seat["credentialId"], seat["ambiguous"]), ("seated", own, False))
        # a second seat road would be refused too: BEN IS STILL REFUSED (not in the charter's roster at all, here)
        ben_refused = runner.request(founder, "POST", "/v1/approver-seats/grant", {"email": ben.email}, "test")
        self.assertEqual(ben_refused.refusal["code"], "APPROVER_SEAT_NOT_IN_CHARTER")

    def test_the_pre_91_knob_puts_the_double_back_to_the_estates_old_shape(self):
        double, runner, founder = self.estate(before_spec_91=True)
        for station in ("station_s2", "station_s3"):
            getattr(runner, station)()
        ada = runner.people["ada"]
        runner.enrol_by_invite(ada, self.invite(runner, founder, ada).json["url"], "test")
        register = runner.request(founder, "GET", "/v1/invites", None, "test").json["invites"]
        self.assertTrue(all("sharesCredentialWith" not in r for r in register), "no marker before Spec 91")
        self.assertEqual(ada.credential_id, founder.credential_id)
        self.assertIn("approver", ada.roles, "the redemption seated the shared credential, as the first live run's did")
        self.assertIn("mintedCredentialId null", [a for a in double.audit if a.startswith("invite.minted author")][0])

    def fresh_address(self, runner, founder):
        created = runner.request(founder, "POST", "/v1/payees",
                                 {"displayName": "Spec T10 payee", "defaultAsset": "USDC", "defaultChain": "ethereum",
                                  "addresses": [{"chain": "ethereum", "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]}, "test")
        self.assertEqual(created.status, 201, created.text)
        address_id = created.json["payee"]["addresses"][0]["id"]
        promoted = runner.request(founder, "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, "test")
        self.assertEqual(promoted.status, 200, promoted.text)
        return address_id


if __name__ == "__main__":
    unittest.main()
