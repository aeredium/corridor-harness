"""
THE SCREENS, AS THE BROWSER LEG READS THEM (Spec HRW-1 §2, the Optimiser: "one new module and one new table file for selectors").

Every route the browser leg opens, every heading it reads, every control it presses — by the accessible name a person's screen
reader announces and Playwright's get_by_role computes — every label it types into, and every sentence it expects to read, pinned
here byte for byte from the AER 360 web application at aeredium/AERAccounts main, commit b523cbf (Spec AER360-115, 8 October 2026,
after Spec AER360-RUN-ROAD of 7 October and Spec AER360-SEAT-CASE of 6 October), with the file and line each was read from. Paths:
`web/` is apps/web/src/, `shared/` is packages/shared/src/ (the @aeraccounts/shared package the screens import), `server/` is
apps/server/src/. Nothing here is composed by the harness: a sentence the estate composes is pinned with the function that composes
it, and the browser leg reads the rest off the page.

THE ACCESSIBLE NAME. Where a control carries an aria-label, that is its name; where it carries a visually-hidden span, the span's
words are part of its name ("Send again" + " — the same invitation, to Ben Signatory"); a radio or a box is named by its label (a
standing's radio by its aria-labelledby, the standing's name alone). A label that wraps hidden text (the interview's money field) is
matched on its opening words, never exactly; a control whose hidden words the estate composes from a record the harness does not
hold (a seat's `{seat.name || seat.email}`) is matched on its visible word, within its own row.

THE MANUAL'S WORDS (MANUAL_WORDS) are the Client Manual's, for R8's Customer Support comparison: first as the product's own library
carries the manual (apps/server/src/library/articles/manual/, kept in step with the screens by pull request — chapter 7 since
Spec AER360-RUN-ROAD, chapters 4 and 15 since Spec AER360-115), then the owner's edition, v8 of 20 September 2026 (the Filing
Cabinet, Client Manual drawer), where the two differ. The manual names few controls by label; where it names one, the page must offer
it, and where it says a sentence the founder will read, the page must say it.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

SOURCE = "aeredium/AERAccounts main at b523cbf (Spec AER360-115, 8 October 2026)"

# ---------------------------------------------------------------------------
# The people the browser leg seats, and the estate's own words for its seats and entries.
# ---------------------------------------------------------------------------
APPROVERS = ("ada", "ben")                         # R4 and R6: the two approvers, each in a browser context of their own (Spec HRW-1 R6)
ESTATE_ENTRY = "aer-accounts"                      # server/services/charterceilings.ts, isEstateOwnSigningEntry: the entry provisioning births
AUTHOR_ENTRY_SUFFIX = " (author)"                  # the founder's entry, f"{first} (author)", drawn up by the birth script (group100_invite.sh)
PRODUCTION_GROUP = "group-100"                     # the one signing group a client account stands on (Spec 113; the Group 100 brief)
# invite.mjs's one line where the birth gave no --email (server/invite.ts:98, Spec AER360-SEAT-CASE §3.2), read from the birth printout
NO_EMAIL_LINE = "no --email given: this founder's presses will carry no name until one is recorded"

# ---------------------------------------------------------------------------
# The estate's roads the browser leg reads the store through (as the API leg reads it), and the platform's one read road.
# ---------------------------------------------------------------------------
SESSION_ROUTE = "/v1/auth/session"                 # server/routes/auth.ts:1106 — the session the passkey opened: credentialId, workspace, roles
INVITES_ROUTE = "/v1/invites"                      # server/routes/invites.ts:416 — the register: email (invitee_email), state, redeemedAt, credentialId
INTERVIEWS_ROUTE = "/v1/onboarding/interviews"     # server/routes/onboarding.ts:289 — begin: {interview, page}
CHARTER_ROUTE = "/v1/onboarding/charter"           # server/routes/onboarding.ts:335 — {standsWritten, inForceSince}
APPROVER_SEATS_ROUTE = "/v1/approver-seats"        # server/routes/approverseats.ts:63 — {charterStands, seats: [{name, email, state, onRoster, …}], summary}
WALLETS_REGISTER_ROUTE = "/v1/aer360/wallets"      # server/routes/aer360.ts:308 — {register: {wallets: [{walletId, walletNumber, address, keyed, chains, level, …}]}}
PLAN_ROUTE = "/v1/aer360/plan"                     # server/routes/aer360.ts:243 — {signingGroup: {accountId, assigned, standing, sentence}}, read live from the platform
PAYEES_ROUTE_API = "/v1/payees"                    # server/routes/payees.ts:89 — {payees: [{displayName, addresses: [{id, chain, address, whitelistStatus}]}]}
SET_ROUTE = "/v1/sets/%s"                          # server/routes/sets.ts:295 — {set: {status, approval, instructions: [{status, txHash, failureReason, …}], trail}}
ADMIN_POLICIES_ROUTE = "/v1/admin/accounts/%s/policies"  # the platform's admin read of an account's entries (server/services/aapclient.ts:1087, listPolicyEntriesAsAdmin)

# ---------------------------------------------------------------------------
# The shell (web/App.tsx).
# ---------------------------------------------------------------------------
SIDEBAR_NAME = "Sections"                          # web/App.tsx:351 — nav[aria-label="Sections"]
CSS_ESTATE_NAME = "nav[aria-label='Sections'] .brand"  # web/App.tsx:356-359 — div.brand: visually-hidden "Estate: " then the workspace's name
ESTATE_PREFIX = "Estate: "
JOURNEY_NAME = "Your journey"                      # shared/journey.ts:288 JOURNEY_BAR_LABEL — the bar under the banner, "Step n of 7 — …" and Continue
CSS_CARD = "section.card"                          # web/components/ui.tsx:51-54 — Card: section.card, its title an h2 in div.card-head
CSS_REFUSAL = ".refusal"                           # web/components/Refusals.tsx:59-61 — RefusalNotice: role alert, or status where acknowledgeable
CSS_LEGEND = "legend"                              # web/screens/Onboarding.tsx:1553-1558 — the question's prompt
CSS_READ_BACK_LINE = "dl > div"                    # web/screens/Onboarding.tsx:1410-1411 — each line: dt prompt, dd spoken

# ---------------------------------------------------------------------------
# R1 — the invitation page (web/screens/Invite.tsx), outside the shell.
# ---------------------------------------------------------------------------
ENROLMENT_CREATE_ACTION = "Create my key now"      # shared/enrolment.ts:63 — the one button, where the page's own request for a key did not finish
INVITE_DEAD_HEADING = "This invitation could not be opened"  # web/screens/Invite.tsx:305 — then the estate's refusal (INVITE_INVALID, its cause in the detail)
ENROLMENT_KEY_EXISTS = "Your key exists, and you are signed in."  # shared/enrolment.ts:109-110
ENROLMENT_KEY_AND_SEAT_GRANTED = "Your key exists and your seat is granted — you can approve now."  # shared/enrolment.ts:105-106
ENROLMENT_KEY_EXISTS_SEAT_PENDING = ("Your key exists, and you are signed in. Your charter names you an approver and your seat could not be recorded yet — "
                                     "your estate’s key holder can grant it in the People room with one press.")  # shared/enrolment.ts:121-124
# enrolmentCompletedSentence (shared/enrolment.ts:222-227): the completing heading is one of the three, from what the estate confirmed of the seat
ENROLMENT_DONE_HEADINGS = (ENROLMENT_KEY_EXISTS, ENROLMENT_KEY_AND_SEAT_GRANTED, ENROLMENT_KEY_EXISTS_SEAT_PENDING)


def continue_label(estate: str) -> str:
    """web/screens/Invite.tsx:338 — "Continue to {session.workspace.name}", the page's one next step once the key exists."""
    return "Continue to %s" % estate


# ---------------------------------------------------------------------------
# R2 — the sign-in page (web/screens/SignIn.tsx), and where a founder lands.
# ---------------------------------------------------------------------------
SIGN_IN_HEADING = "Sign in"                        # web/screens/SignIn.tsx:104
SIGN_IN_BUTTON = "Sign in with passkey"            # web/screens/SignIn.tsx:121 (busy: "Waiting for your passkey…")
LANDING_HEADING = "Consolidation"                  # web/screens/Aer360.tsx:138-141 — `/`; the landing law sends a new estate to its journey's route instead

# ---------------------------------------------------------------------------
# R3 — the Policy Interview (web/screens/Onboarding.tsx), and the catalog's ceilings (server/services/questioncatalog.ts, version 15).
# ---------------------------------------------------------------------------
ONBOARDING_ROUTE = "/onboarding"
ONBOARDING_HEADING = "Onboarding"                  # web/screens/Onboarding.tsx:1153-1156
POLICY_CARD = "The Policy Interview"               # web/screens/Onboarding.tsx:1194
BEGIN_POLICY_INTERVIEW = "Begin the Policy Interview"  # web/screens/Onboarding.tsx:1210
AMEND_THE_CHARTER_CONTROL = "Amend the charter with a new interview"  # shared/refusals.ts:2085 — where a charter stands written
NEXT_BUTTON = "Next — commit this answer and continue"  # web/screens/Onboarding.tsx:1799-1800 — aria-label of "Next →"
ADD_ENTRY = "Add another entry"                    # web/screens/Onboarding.tsx:1783-1785
TEXT_ANSWER_LABEL = "Your answer"                  # web/screens/Onboarding.tsx:1597-1600
CURRENCY_LABEL = "Currency"                        # web/screens/Onboarding.tsx:1642-1648
MONEY_LABEL = "Amount in US dollars"               # web/screens/Onboarding.tsx:1604-1630 — " (required)" follows, and hidden text inside the label: matched on these words
PERCENT_LABEL = "Percentage"                       # web/screens/Onboarding.tsx:1664-1666
ROSTER_SINGLE_LABEL = "One email address, from the people you named"  # web/screens/Onboarding.tsx:1700
ROSTER_MULTI_LABEL = "Email addresses, comma separated, from the people you named"  # web/screens/Onboarding.tsx:1700
DEFAULT_LIST_FIELDS: List[Dict[str, Any]] = [{"key": "label", "label": "Name"}, {"key": "address", "label": "Email or address"}]  # web/screens/Onboarding.tsx:253-257
READ_BACK_HEADING = "The read-back"                # web/screens/Onboarding.tsx:1384-1387
CONFIRM_CHARTER = "Confirm with my passkey — author this charter"  # web/screens/Onboarding.tsx:1452-1454
CHARTER_WRITTEN_HEADING = "The charter is written"  # web/screens/Onboarding.tsx:1107 — an h2 inside the receipt's card
INTERVIEW_AWAITING_APPROVALS = "awaiting_approvals"  # shared/wire.ts:1866 — a write that waits (the book's Policy Interview never does)
# The catalog's note beside C2 and C3 (server/services/questioncatalog.ts:875-878, CEILING_NOTE) carries CHARTER_CEILINGS_REQUIRED and
# NOTHING_ALONE_IS_APPROVAL_NOT_ZERO (shared/explain.ts:433-438); it never says "a zero is refused" in those words — these are its words that do.
CHARTER_CEILINGS_REQUIRED = ("The company ceiling (C2) and the daily total (C3) must each be a figure above zero: the signing platform refuses every "
                             "payment on an account whose ceilings are not set.")
ZERO_REFUSED_WORDS = "must each be a figure above zero"
# A zero typed at C2: ANSWER_INVALID, HTTP 400 (server/services/onboarding.ts:571-576; server/http.ts:468), its message shared/explain.ts:450-451
CEILING_ZERO_REFUSED = "This estate does not accept a zero here. %s Write the figure itself." % CHARTER_CEILINGS_REQUIRED


def list_field_label(label: str, index: int) -> str:
    """web/screens/Onboarding.tsx:1750-1762 — a list entry's field: "{field.label} (entry {i + 1})"."""
    return "%s (entry %d)" % (label, index + 1)


# ---------------------------------------------------------------------------
# R3 and R4 — People (web/screens/People.tsx).
# ---------------------------------------------------------------------------
PEOPLE_ROUTE = "/people"
APPROVER_SEATS_CARD = "Approver seats"             # web/screens/People.tsx:1212
INVITE_CARD = "Invite someone to a standing"       # web/screens/People.tsx:564
INVITE_NAME_LABEL = "Full name"                    # web/screens/People.tsx:572
INVITE_EMAIL_LABEL = "Email address"               # web/screens/People.tsx:584
# The standings the form mints (shared/standings.ts:157-236): Executive (wire author) and Overseer (wire viewer, the default). An approver is
# invited as an Executive, as the API leg mints `author` for Ada and Ben; the radio is named "Level 1 Executive" once /v1/visibility says level 1
# (standingName, shared/standings.ts:317-322), and the form asks the pen to be accepted before it will submit (web/screens/People.tsx:671-685).
EXECUTIVE_STANDING = "Executive"
LEVEL_ONE_EXECUTIVE = "Level 1 Executive"
PEN_LABEL_WORDS = "should hold the pen"            # "Yes — {name} should hold the pen." (web/screens/People.tsx:671-685)
INVITE_SUBMIT = "Invite, and show me the link"     # web/screens/People.tsx:699-701
INVITED_HEADING_WORDS = " has been invited as "    # web/screens/People.tsx:498-501 — "{displayName} has been invited as {an Executive | a Level 1 Executive}"
INVITE_LINK_LABEL = "One-time invitation link"     # web/screens/People.tsx:518-527 — shown once; the harness never screenshots a page showing it
HIDE_THE_LINK = "I have sent the link — hide it"   # web/screens/People.tsx:556
SEAT_WORDS = {"seated": "Seated", "enrolled_not_seated": "Enrolled, not seated", "invited": "Invited — awaiting their key",
              "not_enrolled": "Not yet enrolled"}  # shared/enrolment.ts:235-240 SEAT_STATE_WORDS


# A seat's own controls carry, hidden, `{seat.name || seat.email}` — the charter's name for the person where it gives one, else the address as
# the charter wrote it — so the harness finds each within the seat's own row by the words a person sees, and never composes the hidden half.
SEAT_INVITE = re.compile(r"^Invite(?: |$)")        # web/screens/People.tsx:1353-1360 — a seat not yet enrolled: it fills the form and mints nothing
SEAT_WITHDRAW = re.compile(r"^Withdraw it(?: |$)")  # web/screens/People.tsx:1371-1381 — a seat whose invitation stands: withdrawn at once, no confirmation
SEAT_STATE_MEANING_SEATED = "your policy names their credential; they may approve"  # shared/enrolment.ts:283-284, hidden beside the pill

# The register (web/screens/People.tsx:726-899): every invitation the estate has issued, a pending one with its own Send again and Withdraw; the
# Withdraw asks once more in the row ("Withdraw the invitation to {name}? …") before it sends anything. A person the charter names at A8 and not at
# C11 (an approver of changes, not of payments) has no seat row, so the register is where the founder meets their invitation.
INVITATIONS_CARD = "Invitations"                   # web/screens/People.tsx:726
REGISTER_WORDS = {"pending": "Pending", "redeemed": "Redeemed", "revoked": "Revoked", "expired": "Expired"}  # web/lib/format.ts:168-213 statusPill, titleCase


def withdraw_from_register_label(name: str) -> str:
    """web/screens/People.tsx:884-892 — a pending invitation's "Withdraw" and, hidden, " the invitation to {displayName}"."""
    return "Withdraw the invitation to %s" % name


def confirm_withdraw_label(name: str) -> str:
    """web/screens/People.tsx:857-862 — the row's second question answered: "Yes — withdraw {displayName}’s invitation" (POST /v1/invites/{id}/revoke)."""
    return "Yes — withdraw %s’s invitation" % name


# ---------------------------------------------------------------------------
# R5 — Wallets (web/screens/Wallets.tsx).
# ---------------------------------------------------------------------------
WALLETS_ROUTE = "/wallets"
WALLETS_HEADING = "Wallets"                        # web/screens/Wallets.tsx:644-648
FUNDING_WALLET_CARD = "Funding wallet"             # web/screens/Wallets.tsx:934 — a fresh estate's card, the absence and the press
GIVE_FUNDING_WALLET = "Give this estate its funding wallet"  # web/screens/Wallets.tsx:936-938
FUNDING_WALLET_NOTE = "Funding wallet"             # web/screens/Wallets.tsx:657-659 — role note: "Funding wallet: <address>, on <stack>."
FUND_THIS_ACCOUNT_NOTE = "Fund this account"       # web/screens/Wallets.tsx:664-666 — "Fund this account with USDC on … Gas is bought separately, below."
NEW_WALLET_CARD = "A new wallet"                   # web/screens/Wallets.tsx:778-779 — an author of root standing, once a funding wallet stands
CREATE_NEW_WALLET = "Create a new wallet"          # web/screens/Wallets.tsx:781-783
WHOSE_WALLET_LEGEND = "Whose wallet is this?"      # web/screens/Wallets.tsx:788 — the press's one question for this estate's own wallet
THIS_ESTATE = "This estate"                        # web/screens/Wallets.tsx:788-808
BEFORE_WALLET_BORN_NOTE = "Before this wallet is born"  # web/screens/Wallets.tsx:858-860 — "Level 1 — head office: …"
CREATE_IT = "Create it"                            # web/screens/Wallets.tsx:874-886
PAY_FROM_THIS_WALLET = "Pay from this wallet"      # web/screens/Wallets.tsx:1006-1009 — a link on every keyed wallet's card


def fund_wallet_note(number: str) -> str:
    """web/screens/Wallets.tsx:961-963 — the born wallet's card: role note named "Fund wallet {n}", the estate's fund sentence."""
    return "Fund wallet %s" % number


# ---------------------------------------------------------------------------
# R6 — Payees (web/screens/PayeeRegistry.tsx).
# ---------------------------------------------------------------------------
PAYEES_ROUTE = "/payees"
ADD_PAYEE_CARD = "Add a payee"                     # web/screens/PayeeRegistry.tsx:174
PAYEE_NAME_LABEL = "Name"                          # web/screens/PayeeRegistry.tsx:177
PAYEE_CHAIN_LABEL = "Chain"                        # web/screens/PayeeRegistry.tsx:181-182 — free text, "ethereum" until typed over; `isKnownChain` matches it exactly
PAYEE_ADDRESS_LABEL = "Address"                    # web/screens/PayeeRegistry.tsx:185-191 — a trailing space is trimmed by the judgment, never refused (shared/payeeaddress.ts:146-147)
ADD_PAYEE = "Add payee"                            # web/screens/PayeeRegistry.tsx:223
PAYEES_CARD = "Payees — who you pay"               # web/screens/PayeeRegistry.tsx:245
SEND_FOR_APPROVAL = "Send for approval"            # web/screens/PayeeRegistry.tsx:304 — the same name on every row: scoped by the row
APPROVE = "Approve"                                # web/screens/PayeeRegistry.tsx:315 — likewise
STATUS_WORDS = {"proposed": "Proposed", "pending_promotion": "Pending promotion", "whitelisted": "Whitelisted",
                "rejected": "Rejected"}            # web/lib/format.ts:168-237 statusPill, titleCase of the register's word

# ---------------------------------------------------------------------------
# R7 and R7b — Enter payments (web/screens/PaymentEntry.tsx), the run's page (web/screens/Runs.tsx), the Approver inbox (web/screens/ApproverInbox.tsx).
# ---------------------------------------------------------------------------
ENTRY_ROUTE = "/entry"
ENTRY_HEADING = "Enter payments"                   # web/screens/PaymentEntry.tsx:364-367
REFERENCE_LABEL = "Reference for this run"         # web/screens/PaymentEntry.tsx:391-405 — left empty, the run is created as "Payment run"
DEFAULT_REFERENCE = "Payment run"                  # web/screens/PaymentEntry.tsx:320 — `reference || 'Payment run'` (a sandbox estate stores it marked "S-")
PAY_FROM_LABEL = "Pay from"                        # web/screens/PaymentEntry.tsx:410-427 — options "This estate’s funding wallet" and sourceWalletLabel(w)
ADD_PAYMENT = "Add another payment"                # web/screens/PaymentEntry.tsx:592-597
ONE_OFF_LABEL = "This is a one-off payment to an address that is not on our approved list"  # web/screens/PaymentEntry.tsx:436-445
ONE_OFF_NAME_LABEL = "Who is being paid"           # web/screens/PaymentEntry.tsx:462-477
ONE_OFF_ADDRESS_LABEL = "Address"                  # web/screens/PaymentEntry.tsx:462-477
PAYEE_LABEL = "Payee"                              # web/screens/PaymentEntry.tsx:483-500
CHAIN_LABEL = "Chain"                              # web/screens/PaymentEntry.tsx:506-528 — "anvil" until typed over
ASSET_LABEL = "Asset"                              # likewise "ETH"
AMOUNT_LABEL = "Amount"
INVOICE_LABEL = "Reference (inv #, description)"   # web/screens/PaymentEntry.tsx:540
CHECK_RUN = "Check this run"                       # web/screens/PaymentEntry.tsx:592-597
REVIEW_CARD = "What the checks found"              # web/screens/PaymentEntry.tsx:601
LEAVES_FROM_NOTE = "Leaves from"                   # web/screens/PaymentEntry.tsx:637-641
RUN_TOTAL_WORDS = "Run total:"                     # web/screens/PaymentEntry.tsx:644-652 — "· needs N approval(s), and never yours", or "· … executes when you submit it"
# The founder's confirmation of a repeat (web/screens/PaymentEntry.tsx:660-673): "I have checked the possible repeat{s} above and want to continue"
ACKNOWLEDGE_REPEATS_WORDS = "I have checked the possible repeat"
CHECK_AGAIN = "Check again"                        # web/screens/PaymentEntry.tsx:678-688
SUBMIT_RUN = "Submit this run"                     # web/screens/PaymentEntry.tsx:678-688 — POST /v1/sets then /v1/sets/{id}/submit, then /runs/{id}
IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"  # shared/refusals.ts:943-944; server/services/payoutsets.ts:544-579; HTTP 409
RUN_ROUTE = "/runs/%s"
SUBMISSION_NAME = "Your submission"                # web/screens/Runs.tsx:318-320 — role status: submittedWords (shared/runs.ts:1916-1920)
RUN_STATUS_NAME = "Status of this run"             # web/screens/Runs.tsx:344-346 — role status: runStatusWords (shared/runs.ts:1800-1824)
PAYMENTS_CARD = "Payments"                         # web/screens/Runs.tsx:400-411 — each payment: payee, amount, asset, chain, status, transaction, reason
CANCEL_RUN = "Cancel"                              # web/screens/Runs.tsx:389-393 — the author's own draft, waiting or approved run, not while it executes
INBOX_ROUTE = "/inbox"
APPROVE_WITH_PASSKEY = "Approve with passkey"      # web/screens/ApproverInbox.tsx:340-347 — the same name on every run's card: scoped by the card
# AER 360 Spec AER360-116 (drafted 9 October 2026, not yet built): beside the platform's legacy_limit_zero sentence on a refused run's page,
# the estate's own plain sentence (§3 item 8). The browser leg reads it where the page carries it and quotes it beside the platform's.
ESTATE_PLAIN_SENTENCES = ("Your charter does not yet state the company ceiling and the daily total. Answer the two questions in the Onboarding room, "
                          "then make the payment again.",)


def payment_card(number: int) -> str:
    """web/screens/PaymentEntry.tsx:434 — each payment's card: "Payment {index + 1}"."""
    return "Payment %d" % number


def payee_option(name: str, chain: str) -> str:
    """web/screens/PaymentEntry.tsx:483-500 — a listed payee in the Payee list: "{displayName} — {chain} — approved" once whitelisted."""
    return "%s — %s — approved" % (name, chain)


# ---------------------------------------------------------------------------
# THE MANUAL'S WORDS, station by station (R8, the Customer Support hat). `check`: "pressed" — the founder pressed a control beginning with
# `control`; "said" — the page said `words`; "duplicate" — met only where the duplicate screen spoke: the manual's word for the founder's
# confirmation is the refusal's own imperative, and the page's control is a box, which R8 says beside it as a note; "none" — the manual names
# no control here, and R8 sets its words beside the page's for the reader. `walked`: the request the step makes (method, path, and a field of
# its answer that must be set) — an item is held only where this run walked that step (a rerun on a charter, a wallet and payees that already
# stand walks none of them) and only at a station that passed (a failed station's own findings say what its page said).
# ---------------------------------------------------------------------------
LIBRARY = "the manual as the product's library carries it, apps/server/src/library/articles/manual/"
MANUAL_WORDS: Dict[str, List[Dict[str, Any]]] = {
    "R1": [{"source": LIBRARY + "03-getting-started.md:20-26; the same in v8, ch. 3 Getting started › The one step",
            "quote": "Open the invitation link. The page does exactly one thing: it creates your key. One confirmation on your device and you are enrolled — "
                     "the page tells you in plain words the moment it is done",
            "control": None, "check": "none", "walked": ("POST", r"^/v1/auth/invite/verify$")}],
    "R2": [{"source": LIBRARY + "11-claude-at-your-side.md:13-14; the same in v8, ch. 11 Claude at your side",
            "quote": "(The \"Sign in\" page is only for someone who already has a passkey; it cannot make one.)",
            "control": None, "words": SIGN_IN_HEADING, "check": "said", "walked": ("POST", r"^/v1/auth/login/verify$")}],
    "R3": [{"source": LIBRARY + "04-setting-your-companys-rules-the-policy-interview.md:14; the same in v8, ch. 4 (a screenshot's caption)",
            "quote": "One question per page. Next commits; leaving resumes here.", "control": "Next", "check": "pressed",
            "walked": ("POST", r"^/v1/onboarding/interviews/[^/]+/answers$")},
           {"source": LIBRARY + "15-references.md:459-462 (Spec AER360-115; not in v8, which has no C2 and calls a written zero a wall)",
            "quote": "Where a zero is written at C2 or C3: " + CEILING_ZERO_REFUSED, "control": None, "words": CEILING_ZERO_REFUSED, "check": "said",
            "walked": ("POST", r"^/v1/onboarding/interviews$")},
           {"source": LIBRARY + "04-setting-your-companys-rules-the-policy-interview.md:313-314; the same in v8, ch. 4 Part G",
            "quote": "The read-back: your whole charter is read back to you and nothing binds until you confirm it under your passkey.",
            "control": None, "check": "none", "walked": ("GET", r"^/v1/onboarding/interviews/[^/]+/readback$")}],
    "R4": [{"source": LIBRARY + "06-the-rooms-of-aer-360.md:80-82; v8, ch. 6 People, adds that every person holds a key of their own",
            "quote": "Invitations are sent, resent, and withdrawn here, and every person's true state is shown — including \"invited, awaiting their key.\"",
            "control": None, "check": "none", "walked": ("POST", r"^/v1/invites$")},
           {"source": LIBRARY + "03-getting-started.md:22-24; the same in v8, ch. 3",
            "quote": "if your role includes approving, your approver seat is granted at that same moment and the page says so.",
            "control": None, "words": "your seat is granted", "check": "said", "walked": ("POST", r"^/v1/auth/invite/verify$", "approverSeat.charterNamedThem")}],
    "R5": [{"source": LIBRARY + "06-the-rooms-of-aer-360.md:102-105 (Spec 110a; not in v8)",
            "quote": "Creating a new wallet asks two things before your passkey: whose wallet it is, this estate's or a client's by name, and, for a "
                     "client's, whether the client signs.",
            "control": None, "words": WHOSE_WALLET_LEGEND, "check": "said", "walked": ("POST", r"^/v1/workspace/wallets/options$")},
           {"source": LIBRARY + "06-the-rooms-of-aer-360.md:105-106 (Spec 110a; not in v8)",
            "quote": "A payment leaves the wallet it names: Pay from this wallet stands on every wallet the estate holds a key for.",
            "control": None, "words": PAY_FROM_THIS_WALLET, "check": "said", "walked": ("GET", r"^/v1/aer360/wallets$")}],
    "R6": [{"source": LIBRARY + "07-making-a-payment-end-to-end.md:16-18; the same in v8, ch. 7 Step 1",
            "quote": "Open the Payees room from the sidebar. Choose Add payee, enter their name, and paste their payment address. Pick the network the "
                     "address belongs to.", "control": ADD_PAYEE, "check": "pressed", "walked": ("POST", r"^/v1/payees$")},
           {"source": LIBRARY + "07-making-a-payment-end-to-end.md:33-41; the same in v8, ch. 7 Step 2",
            "quote": "If your rules require two or more, the address stays pending after the first press, and its row says so: how many approvals are "
                     "recorded, how many are still needed, and who may still approve.",
            "control": None, "words": "approvals recorded for this address", "check": "said",
            "walked": ("POST", r"^/v1/payees/addresses/[^/]+/approve$", "approvals")}],
    "R7": [{"source": LIBRARY + "07-making-a-payment-end-to-end.md:60-62; the same in v8, ch. 7 Step 3",
            "quote": "When the run is complete, submit it.", "control": "Submit", "check": "pressed", "walked": ("POST", r"^/v1/sets$")},
           {"source": LIBRARY + "15-references.md:547-548; the same in v8, ch. 15 Reference B › Duplicate (p. 53)",
            "quote": "DUPLICATE_UNACKNOWLEDGED: This looks like a payment that has already been made recently. Confirm it is intentional to continue.",
            "control": "Confirm it is intentional", "check": "duplicate", "when": "duplicate"},
           {"source": LIBRARY + "07-making-a-payment-end-to-end.md:86-88; the same in v8, ch. 7 Step 5",
            "quote": "Once the last required approval lands, the run executes. Each payment is signed and sent to its network. You do not need to do "
                     "anything; the run page shows each payment settle in turn.", "control": None, "words": "landed", "check": "said",
            "walked": ("POST", r"^/v1/sets$")}],
    "R7b": [{"source": LIBRARY + "07-making-a-payment-end-to-end.md:60-62; the same in v8, ch. 7 Step 3",
             "quote": "When the run is complete, submit it.", "control": "Submit", "check": "pressed", "walked": ("POST", r"^/v1/sets$")},
            {"source": LIBRARY + "15-references.md:547-548; the same in v8, ch. 15 Reference B › Duplicate (p. 53)",
             "quote": "DUPLICATE_UNACKNOWLEDGED: This looks like a payment that has already been made recently. Confirm it is intentional to continue.",
             "control": "Confirm it is intentional", "check": "duplicate", "when": "duplicate"},
            {"source": LIBRARY + "15-references.md:581-583 (Spec AER360-RUN-ROAD); v8, ch. 15: \"A different payment run has already been submitted "
                       "under this reference.\", with no next step",
             "quote": "IDEMPOTENCY_KEY_REUSED: A different payment run already carries this reference. Open it, or change the reference.",
             "control": None, "check": "none", "walked": ("POST", r"^/v1/sets$")}],
}
