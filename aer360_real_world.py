#!/usr/bin/env python3
"""
HARNESS REAL WORLD (Spec HRW-1, written 7 October 2026 in Singapore on the owner's naming and ruling of the same day, revised
9 October 2026 in Melbourne): the BROWSER LEG of the estate harness.

The owner, 7 October 2026: "I want to call it Harness Real World. So when I refer to Harness Real World, it will actually take the
root of the browser, and it will do a proper test like if it was a human being."

The estate harness (aer360_harness.py, Specs T7 to T28) stays as it is and is, by name, the API LEG: the proof of the server's roads.
This module is the browser leg: a real browser (Chromium, through Playwright), the real pages at accounts.aeredium.io, a passkey
behind the real WebAuthn prompt (a Chrome DevTools Protocol virtual authenticator whose credential is kept on the operator's Mac), the
presses a founder makes and the sentences a founder reads, and the chain read afterwards. A road is proved only when both legs agree,
and R8 says whether they do. The rule it exists for (Spec HRW-1 §1): a harness proves the road a customer travels, in the customer's
shoes, or it proves a different road. On 6 October 2026 the API leg had been at one hundred per cent for two days while a founder
could not send a payment: the harness had called /v1/sets/:id/submit and /execute itself, and the screen a founder uses made neither
call (Spec AER360-RUN-ROAD §1).

THE LAWS IT KEEPS, the API leg's own:

  THE HARNESS IS THE FOUNDER, NOT A JUDGE. It presses only what a founder presses and reads only what a founder reads; the store is
  read afterwards the way the API leg reads it, through the estate's own routes, under the person's own session (the browser
  context's own request road, which carries the context's cookies and nothing else).

  A FAILURE IS EVIDENCE, NOT A VERDICT. Every station records the page's heading and every sentence shown after a press, verbatim; the
  request the browser made, with its status and body (Playwright's network log; the invitation token, every passkey field, the CSRF
  token and the session cookie redacted to their last four characters — the cookie and the headers are never recorded at all); the
  store row read afterwards; and a screenshot. A refusal shown to the founder is quoted exactly and classified in the API leg's
  vocabulary — REFUSED, UNREACHABLE, MALFORMED QUESTION, ANSWERED WITH ERROR — with the store's reading beside it, and where the
  screen's words and the store disagree that is a finding of its own. The harness's own failures (a control not found in time, a
  timeout, Playwright not installed) are named as the harness's, never as the estate's, with the screenshot (Spec HRW-1 §6).

  REFUSALS TELL THE TRUTH; NO "MAY" WITHOUT ITS BOUND. The one cure this leg ever makes on money is Spec T26's — a gas credit through
  the platform's admin road, only where the estate's review on the screen refused GAS_SHORTFALL, once per refusal, sized by that
  refusal's ceiling. A wallet short of the one-dollar book is never funded by the harness: the station stops naming the address, the
  chain and the figure, as Spec T14's birth run does, because funding a wallet is the owner's act. Nothing repeats on a clock.

THE OWNER'S THREE CHANGES (9 October 2026). The guard: a page inside an estate's shell that names no estate stops the run, and only the
sign-in and invitation pages, which have no shell, pass without a name. The inbox: a run waiting for an approval is approved only on a card
that names a run this process created — carrying its id, or the card the run's own page links to — and a card that names no run is never
pressed (at AERAccounts b523cbf none does: a finding, and R9 cancels the run). The literal bound: before every Submit this run, the rows the
page will submit are held to the owner's wallet and to RUN_CEILING_CENTS — 100 cents, written here, for the whole run — beside the book's own
ONE_DOLLAR_MINOR; and no route is recorded with its query string (redact_query).

THE CUSTOMER SUPPORT HAT (Bear, 9 October 2026: "put yourself in the shoes of the customer"). Every station records the page's own
"what to do next" — the notice, the control's label, the refusal — and R8 holds it against the Client Manual's words for each step this
run walked, at every station that passed (aer360_screens.MANUAL_WORDS). A page that leaves a founder without a next step is a finding even
when the server did its job.

THE PAGE IS READ WHEN IT SPEAKS. A page renders an answer after the browser has received it, and Playwright's networkidle is a page load's
state that no press re-arms: so every press that makes a request waits for that request's answer, and what the page says after it is read
once the page says it (Visitor.poll), never before.

THE STATIONS carry the API leg's numbers so the two legs line up: R1 Enrol (S1), R2 Sign in (S2), R3 Policy Interview (S3), R4 People
(S4), R5 Wallet (S5), R6 Payees (S6), R7 Payment and R7b The second press (S7), R8 The two legs agree, R9 Teardown. `--from S5` (or
R5) resumes at a station, every person signed in with the credential stored for them, so a station can be re-run without rebirth.

THE UNTIDY FIXTURES (Spec HRW-1 §4) are listed in aer360_tables.py beside the ruling or spec that made each a rule (UNTIDY_FIXTURES):
the estate born by the operator's CLI road (group100_invite.sh), with --email and, in one run, deliberately without it; the charter's
addresses with capitals and surrounding spaces; one approver whose display name is not their address; the founder pressing Submit
this run twice; one payee address typed with a trailing space; the run's reference left at its default; and the estate's signing
entries never set by hand — they stand at zero until the Policy Interview's write puts the charter's ceilings on them (Spec
AER360-115), which R3 reads before and after, and which R7's first landed payment proves.

WHERE THE SPEC AND THE CODE PART COMPANY, said rather than resolved silently (the module keeps the code's road and names it):
  1. The duplicate screen's "press Confirm it is intentional" is the refusal's own sentence (refusals.ts DUPLICATE_UNACKNOWLEDGED:
     "… Confirm it is intentional to continue."). The screen's control is a box — "I have checked the possible repeat(s) above and want
     to continue" — then Check again, then Submit this run (PaymentEntry.tsx), which is what T28 found and what this leg presses, within
     T28's bound and nowhere else.
  2. R5's "Create a new wallet, answer its questions, every limit above zero": the press asks one question, Whose wallet is this?, and
     no limit (Wallets.tsx); a wallet the estate presses for signs under the estate's own entries, whose limits R3's write sets. And a
     fresh estate offers the press only once its funding wallet stands, so R5 presses Give this estate its funding wallet first where the
     page offers it, as the page asks a founder to.
  3. R7 and R7b pay the one-dollar book between them: R7 enters HH-0001 and HH-0002, R7b — the founder's second Submit this run, a
     different run under the same default reference, the same day — HH-0003. Spec T24's law ("No more than $1.") forbids a second run
     that moves money beyond the book, and a second run that repeated R7's rows would meet the duplicate screen naming a payment of THIS
     run, which T28's bound refuses to acknowledge.
  4. The store rows R1 names (enrollment_invites.redeemed_at and invitee_email, webauthn_credentials) live on the estate's database,
     which only the estate box reaches. They are read as the API leg reads the store: the invitation register (GET /v1/invites: state,
     redeemedAt, email, credentialId) and the session the passkey opened (GET /v1/auth/session, and R2's sign-in from a fresh context,
     which the estate admits only against the stored credential row).
  5. The signing entries R3 reads are the platform's, which no estate route lists. Before the interview they are read on the platform's
     own read road (GET /v1/admin/accounts/{id}/policies) with the admin credential the API leg already files (admin.env), read-only,
     for this estate's own account and no other; where it is not filed or not reachable, that is said, and the write's own receipt —
     the compile's answer as the browser received it, `receipt.ceilings`, naming each entry the write found at zero and filled — is the
     estate's record of before and after.
  6. R2's "read the estate's name in the heading": a page's heading is its room's (Onboarding, Consolidation); the shell names the estate
     in its sidebar (App.tsx, the brand: "Estate: <name>"), and that is what the guard reads before every press, R2's included.
  7. R4's "read Seated": the Approver seats panel lists the approvers C11 names — Ada, who is seated. Ben approves changes (A8's census,
     the roster that whitelists a payee, R6) and is no payment approver, so he has no seat: the founder invites him from the form, typed,
     and his row on the register reads Redeemed. And the charter names Ada's seat by the address C11 was answered with (the compiler's
     roster is C11's addresses; parseRoster gives no name), so the seat's Invite fills the address and leaves the name for the founder.
  8. §2 Implementer's "resumes from the API leg's stored state": the browser leg's people enrol in the browser, their passkeys the virtual
     authenticator's, so it resumes from its own state beside the API leg's in the same store (~/.aer360-harness/real-world/), with the
     same --from flag (S<n> or R<n>), reading the API leg's admin.env and payee.env; the API leg's software passkeys are not presented.
  9. R9's "cancel any draft the run left": a run this run submitted that still waits for an approval is cancelled too, from the same Cancel
     on its page, since it would move money the moment someone approved it after the run; a run that executed is left as it stands.

The browser leg needs Playwright for Python and its Chromium; it is the one thing the repository's harnesses install (Spec HRW-1 §2:
Playwright and Chromium are on the operator's Mac). It is imported only when a live run starts, so --dry, the tests and every other
harness here stay on the standard library.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aer360_answers as A  # noqa: E402  the book: the people, the answers, the payments
import aer360_harness as E  # noqa: E402  the API leg: its vocabulary, its redaction, its report reader, its gas-credit words — imported, never refactored
import aer360_passkey as PK  # noqa: E402  write_private: a file only its owner can read
import aer360_screens as S  # noqa: E402  the screens as the browser reads them, pinned from aeredium/AERAccounts
import aer360_tables as T  # noqa: E402  the tables both legs read, the untidy fixtures among them
from corridor_harness import RUNS_DIR, RunFolder  # noqa: E402  the run folder: report.md and evidence.jsonl, as every run folder here

# ---------------------------------------------------------------------------
# Where things are.
# ---------------------------------------------------------------------------
DEFAULT_BASE = E.DEFAULT_BASE                 # https://accounts.aeredium.io — production, the harness's own estates only
STORE_ROOT = E.STORE_DIR                      # ~/.aer360-harness: admin.env and payee.env, as the API leg files them
STORE_FOLDER = "real-world"                   # ~/.aer360-harness/real-world/<person>.json (0600): each person's credential (Spec HRW-1 §3)
STATE_FILE = "state.json"                     # ~/.aer360-harness/real-world/state.json (0600): what this leg made, so --from resumes without rebirth
TESTER = "real-world"                         # the run folder: ~/Downloads/harness-runs/<date-time>-real-world/
API_REPORTS_DIR = "."                         # where the API leg writes aer360-harness-<date>.md (its --out default): R8 reads the newest there
USER_AGENT_NOTE = "Harness Real World (Spec HRW-1)"

# ---------------------------------------------------------------------------
# The stations, with the API leg's numbers (Spec HRW-1 §3).
# ---------------------------------------------------------------------------
STATIONS: List[Tuple[str, str]] = [
    ("R1", "Enrol"), ("R2", "Sign in"), ("R3", "Policy Interview"), ("R4", "People"), ("R5", "Wallet"), ("R6", "Payees"),
    ("R7", "Payment"), ("R7b", "The second press"), ("R8", "The two legs agree"), ("R9", "Teardown"),
]
STATION_IDS = [s for s, _ in STATIONS]
TITLES = dict(STATIONS)
# R8 holds each browser station against the API leg's station of the same number (R7b's press is S7's road too).
API_LEG_STATION = {"R1": "S1", "R2": "S2", "R3": "S3", "R4": "S4", "R5": "S5", "R6": "S6", "R7": "S7", "R7b": "S7"}

PASS, FAIL, FAILED_PREREQUISITE, SKIPPED, NOT_RUN = E.PASS, E.FAIL, E.FAILED_PREREQUISITE, E.SKIPPED, E.NOT_RUN
FAILURES = E.FAILURES

# The API leg's vocabulary for what came back (the charter law, "Refusals tell the truth", 4 September 2026), and the harness's own word.
REFUSED = "REFUSED"                            # 401, 403, 404, 409, 422, 429, or a 502 carrying the other party's no: a judgment, the same on retry
UNREACHABLE = "UNREACHABLE"                    # no answer, a timeout, a 5xx: a fault, not a judgment
MALFORMED_QUESTION = "MALFORMED QUESTION"      # 400: the question as asked (here, as typed) was refused as malformed
ANSWERED_WITH_ERROR = "ANSWERED WITH ERROR"    # a 2xx that carries a failure in the other party's words (a payment's failureReason)
SCREEN = "SCREEN"                              # the page itself: a control missing, a sentence that disagrees with the store, no next step
HARNESS = "HARNESS"                            # the harness's own failure: a control not found in time, a timeout, Playwright not installed

# The bounds of the waits (no-op under the test clock).
ACTION_TIMEOUT_SECONDS = 30.0                  # a control to appear, a press's answer to arrive
NAVIGATION_TIMEOUT_SECONDS = 60.0              # a page to load
SETTLE_TIMEOUT_SECONDS = 10.0                  # the network to fall quiet after a load (Playwright's networkidle is a page load's state, never re-armed by a press)
ENABLED_WAIT_SECONDS = 10.0                    # a control the page is about to enable (Submit this run once the review is acceptable) waited for before it is called disabled
POLL_SECONDS = 0.25                            # between two readings of the page while it catches up with an answer it has received
GUARD_WAIT_SECONDS = 10.0                      # a page still rendering, waited for before the guard calls it a page it cannot place
RUN_READS_AT_MOST = 40                         # the run's page read again up to this many times while a payment is not terminal
RUN_READ_WAIT_SECONDS = 5.0                    # between those reads — the page itself re-reads every 2 s while moving, every 10 s while waiting
INTERVIEW_PAGES_AT_MOST = 80                   # the Policy Interview walked at most this many pages before the harness calls it a loop
APPROVALS_AT_MOST = 2                          # the seated approvers asked to approve a waiting run, in the book's order, each once

# The virtual authenticator every person's context carries (Spec HRW-1 §3): CTAP2, resident keys, user verification, the user verified —
# the estate asks for a discoverable credential and user verification on every ceremony (services/webauthn.ts: residentKey required,
# userVerification required), and a platform authenticator answers without a human hand.
VIRTUAL_AUTHENTICATOR = {"protocol": "ctap2", "transport": "internal", "hasResidentKey": True, "hasUserVerification": True,
                         "isUserVerified": True, "automaticPresenceSimulation": True}
CREDENTIAL_KIND = "aer360-real-world credential (Chrome DevTools Protocol virtual authenticator, P-256)"

PLAYWRIGHT_MISSING = ("Playwright for Python is not importable by %s, and the browser leg drives Chromium through it (Spec HRW-1 §3). "
                      "Install it once: %s -m pip install --user playwright, then %s -m playwright install chromium. Nothing was opened and nothing was sent")
CHROMIUM_MISSING = ("Chromium would not launch through Playwright (%s); install it once: %s -m playwright install chromium. Nothing was opened and nothing "
                    "was sent")
I_MEAN_IT = ("Harness Real World presses controls on %s with real passkeys and moves up to one dollar of real USDC to the owner's wallet. "
             "Nothing was opened. Run it again with --i-mean-it; the plan it would walk is printed below.")
FOUNDER_NOT_ENROLLED = "the founder not enrolled here"
NO_FOUNDER_SESSION = "no founder session"
WRONG_ESTATE = "a page names another estate"
OWNER_PAYEE_NOT_FILED = E.OWNER_PAYEE_NOT_FILED
WALLET_NOT_FUNDED = "the wallet holds less than the book"
NO_WALLET = "no wallet of this leg's"
NO_APPROVER_SESSION = "an approver without a session"
NO_API_LEG_REPORT = "no API leg report for this estate"
NOTHING_COMPARED = "no station both legs ran to a judgment"
EMAIL_NOT_RECORDED = "the founder's email not recorded"
NOT_PINNED_ESTATE = ("the page names the estate %r, which is not one of the harness's own (%s); the harness presses nothing on anyone's estate "
                     "but its own, so the run stops here (Spec HRW-1 §2, the Attacker)")
NO_ESTATE_IN_THE_SHELL = ("the page at %s stands inside an estate's shell and names no estate (the sidebar's brand is empty, or cannot be read), so the guard "
                          "cannot tell whose estate it is; the harness presses nothing on a page it cannot place, so the run stops here (Spec HRW-1 §2, the Attacker)")
NOT_A_PAGE_WITHOUT_THE_SHELL = ("the page at %s (its heading %r) shows no estate's shell and is neither the sign-in page nor the invitation page — the only "
                                "pages that stand outside the shell, and so the only ones that may name no estate — so the guard cannot tell whose estate it is; "
                                "the run stops here (Spec HRW-1 §2, the Attacker)")
NOT_THIS_ESTATE = ("the page names the estate %r, and this run's estate is %r; the harness presses nothing on an estate it did not set out to walk, "
                   "so the run stops here (Spec HRW-1 §2, the Attacker)")
# THE LITERAL BOUND (Spec HRW-1 §5: "It does not move more than one dollar in a run, and only to the owner's wallet"; the one-dollar law of 3 October
# 2026), written here as a figure and never read from the book: before every Submit this run, the rows the page will submit — with what this run has
# already submitted — come to at most this many cents of USDC, and every one is to the owner's wallet. The book's own bound, aer360_tables.ONE_DOLLAR_MINOR,
# is held beside it; a book changed past a dollar meets this one first.
RUN_CEILING_CENTS = 100
LITERAL_BOUND_ADDRESS = ("the review the page received names %s, not the owner's wallet %s; this leg pays the owner's wallet alone (Spec HRW-1 §5, Spec T24), so "
                         "%r was not pressed and the run stops here")
LITERAL_BOUND_UNREADABLE = ("the review the page received carries a row this leg cannot bound (%s): it submits USDC alone, in whole minor units, so %r was not "
                            "pressed and the run stops here")
LITERAL_BOUND_TOTAL = ("the rows the page would submit come to %d cents and this run has already submitted %d: together above the %d cents this leg submits in a "
                       "run at most (Spec HRW-1 §5, the one-dollar law), so %r was not pressed and the run stops here")
FUND_THE_WALLET = ("fund wallet %s (%s) with %s of %s on %s — this run's book needs %s from here and the chain reads %s there — then rerun with --from %s; "
                   "the harness funds no wallet, because funding a wallet is the owner's act")


class HarnessFault(E.HarnessError):
    """The harness's own failure — a control not found in time, a timeout, Playwright missing: never the estate's (Spec HRW-1 §6)."""


class RunStop(Exception):
    """
    A stop of the whole run: a page naming an estate not the harness's own (§2); a founder born without --email whose address is not yet
    recorded (§4 — the record script, then --from S1); or R8 finding a report fault in one of the legs (§3). `kind` classifies it: SCREEN for
    what a page or the store showed, HARNESS for the legs' own reports disagreeing.
    """

    def __init__(self, sentence: str, station: str = "", prerequisite: Optional[str] = None, kind: str = SCREEN):
        super().__init__(sentence)
        self.sentence = sentence
        self.station = station
        self.prerequisite = prerequisite
        self.kind = kind


StationStop = E.StationStop


# ---------------------------------------------------------------------------
# Small pure helpers.
# ---------------------------------------------------------------------------
def fold(email: Any) -> str:
    """The estate's own fold (apps/server/src/services/emailfold.ts, foldEmail): trimmed, lower-cased — the one form a seat carries."""
    return str(email or "").strip().lower()


def now_iso() -> str:
    return E.now_iso()


def last4(value: Any) -> str:
    return E.last4(value)


def kind_of(status: int, body: Any) -> str:
    """
    What came back, in the API leg's vocabulary (the charter law: every catch classifies). REFUSED — 401, 403, 404, 409, 422, 429, or a 502
    carrying the other party's no in a refusal body: a judgment, the same on retry. MALFORMED QUESTION — 400: the question as the page
    sent it was refused as malformed (a zero typed where the estate takes none is one). UNREACHABLE — no answer (0) or any other 5xx: a
    fault. ANSWERED WITH ERROR — anything else that carries an error in the other party's words.
    """
    refusal = body.get("error") if isinstance(body, dict) and isinstance(body.get("error"), dict) else None
    if status in (401, 403, 404, 409, 422, 429) or (status == 502 and refusal):
        return REFUSED
    if status == 400:
        return MALFORMED_QUESTION
    if status == 0 or 500 <= status < 600:
        return UNREACHABLE
    return ANSWERED_WITH_ERROR


def refusal_words(body: Any) -> str:
    """The estate's refusal in its own words: code, message, and the other party's sentence where it travels (platformSaid, gatewaySaid, cause)."""
    refusal = body.get("error") if isinstance(body, dict) and isinstance(body.get("error"), dict) else None
    if refusal is None:
        return ""
    detail = refusal.get("detail") if isinstance(refusal.get("detail"), dict) else {}
    beside = [str(detail[k]) for k in ("platformSaid", "gatewaySaid", "cause") if detail.get(k)]
    return "%s: %s%s" % (refusal.get("code"), refusal.get("message"), "".join(" (%s)" % b for b in beside))


QUERY_REDACTED = "?<redacted>"


def redact_query(route: Any) -> str:
    """
    A route or an address as the evidence records it, its query string redacted (the owner's third change, 9 October 2026): a query can carry an
    id, an address or a token, and the path alone names the road. Applied to route fields only, never to free text, where a question mark is a
    question mark.
    """
    return re.sub(r"\?[^\s#]+", QUERY_REDACTED, str(route))


def shown(name: Any) -> str:
    """A control's name as the record says it: its words, or — for a control matched on its visible word (a seat's Invite) — that word and an ellipsis."""
    pattern = getattr(name, "pattern", None)
    if pattern is None:
        return str(name)
    return re.sub(r"\(\?:[^)]*\)|[\^$\\]", "", pattern).strip() + " …"


def money_text(minor: int, decimals: int = 6) -> str:
    """Minor units as a person types them into an Amount field: 500000 of USDC → "0.50"."""
    whole, fraction = divmod(int(minor), 10 ** decimals)
    return "%d.%02d" % (whole, fraction // (10 ** (decimals - 2))) if decimals >= 2 else str(whole)


def cents_text(cents: Any) -> str:
    """Cents as a person types them, grouped as en-US groups them: "10000" → "100.00", "100000" → "1,000.00"."""
    n = int(str(cents))
    return "{:,}.{:02d}".format(n // 100, n % 100)


def parse_birth(text: str) -> Dict[str, Any]:
    """
    The birth script's printout, read (Spec HRW-1 §4, R1): group100_invite.sh prints "account id: <id>", "founder credential: <id>" and
    invite.mjs's lines — "Invite for <account> (<name>)", "Email:    <address>" where --email was given, and the link on a line of its own —
    and, where --email was not given, invite.mjs's one line: "no --email given: this founder's presses will carry no name until one is
    recorded". Answers the facts; the link is the caller's to keep secret.
    """
    facts: Dict[str, Any] = {"link": None, "account_id": None, "founder_credential": None, "company": None, "display_name": None,
                             "email": None, "no_email_warning": None}
    for raw in text.splitlines():
        line = raw.strip()
        found = re.search(r"(https?://\S+/invite#\S+)", line)
        if found and not facts["link"]:
            facts["link"] = found.group(1)
        found = re.match(r"^account id:\s*(\S+)$", line)
        if found:
            facts["account_id"] = found.group(1)
        found = re.match(r"^founder credential:\s*(\S+)$", line)
        if found:
            facts["founder_credential"] = found.group(1)
        found = re.match(r"^Invite for (.+) \((.+)\)$", line)
        if found:
            facts["company"], facts["display_name"] = found.group(1), found.group(2)
        found = re.match(r"^Email:\s+(\S+)$", line)
        if found:
            facts["email"] = found.group(1)
        if line == S.NO_EMAIL_LINE:
            facts["no_email_warning"] = line
    return facts


# ---------------------------------------------------------------------------
# What a station records.
# ---------------------------------------------------------------------------
class Outcome:
    def __init__(self, station: str, outcome: str, line: str):
        self.station = station
        self.outcome = outcome
        self.line = line


class Finding:
    """A finding: the probe, the page's words, the store's reading, the expectation, the classification and the one-line sentence."""

    def __init__(self, station: str, probe: str, said: str, kind: str, page: str = "", store: str = "", expected: str = "", route: str = ""):
        self.station = station
        self.probe = probe
        self.said = said
        self.kind = kind
        self.page = page
        self.store = store
        self.expected = expected
        self.route = route


class Exchange:
    """One request the browser made and the estate's answer, as Playwright's network log saw it — redacted when it was recorded."""

    def __init__(self, station: str, who: str, method: str, path: str, status: int, sent: Any, text: str, at: str):
        self.station = station
        self.who = who
        self.method = method
        self.path = path
        self.status = status
        self.sent = sent
        self.text = text
        self.at = at
        self._json: Any = None
        self._parsed = False

    @property
    def json(self) -> Any:
        if not self._parsed:
            self._parsed = True
            try:
                self._json = json.loads(self.text) if self.text and self.text.strip() else None
            except ValueError:
                self._json = None
        return self._json

    @property
    def route(self) -> str:
        return "%s %s" % (self.method, self.path)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def sentence(self) -> str:
        words = refusal_words(self.json)
        return words or ("HTTP %d" % self.status)


class StoreRead:
    """A store row read the way the API leg reads it: a GET on the estate's own route, under the person's own session."""

    def __init__(self, path: str, status: int, text: str):
        self.path = path
        self.status = status
        self.text = text
        try:
            self.json = json.loads(text) if text and text.strip() else None
        except ValueError:
            self.json = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def sentence(self) -> str:
        return refusal_words(self.json) or "HTTP %d" % self.status


# ---------------------------------------------------------------------------
# The browser: Playwright for Python, imported when a live run starts.
# ---------------------------------------------------------------------------
class Driver:
    """What the leg needs of Playwright: a way to start it, and its two error kinds (a timeout, and everything else it raises)."""

    def __init__(self, start: Callable[[], Any], timeout_error: type, error: type):
        self.start = start
        self.timeout_error = timeout_error
        self.error = error


def live_driver() -> Driver:
    """Playwright for Python's sync API, or the harness's own sentence for its absence (§6: named as the harness's, never the estate's)."""
    try:
        from playwright.sync_api import Error as PlaywrightError  # type: ignore[import-not-found]
        from playwright.sync_api import TimeoutError as PlaywrightTimeout  # type: ignore[import-not-found]
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        raise HarnessFault(PLAYWRIGHT_MISSING % (sys.executable, sys.executable, sys.executable))
    return Driver(lambda: sync_playwright().start(), PlaywrightTimeout, PlaywrightError)


def urllib_transport(request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
    """The roads that are not the estate's (the chain's public RPC; the platform's admin road): the API leg's own transport."""
    return E.urllib_transport(request)


# ---------------------------------------------------------------------------
# One person in their own browser context.
# ---------------------------------------------------------------------------
class Visitor:
    """
    One person of the estate in a browser context of their own: a page, a CDP session, and a virtual authenticator holding their passkey
    (Spec HRW-1 §3: one browser context per person, each with its own authenticator). Every press reads the estate's name first (the
    guard, §2); every request the page makes is recorded as it is answered.
    """

    def __init__(self, leg: "RealWorld", key: str, name: str, context: Any, page: Any, cdp: Any, authenticator_id: str):
        self.leg = leg
        self.key = key
        self.name = name
        self.context = context
        self.page = page
        self.cdp = cdp
        self.authenticator_id = authenticator_id
        self.session: Optional[Dict[str, Any]] = None
        self.closed = False
        page.on("response", self.on_response)

    # -- the network log -----------------------------------------------------------------------------------------------
    def on_response(self, response: Any) -> None:
        """Every answer to a request this page made on the estate's own roads (/v1/…), recorded the moment it arrives."""
        try:
            url = str(response.url)
            parsed = urllib.parse.urlparse(url)
            if "%s://%s" % (parsed.scheme, parsed.netloc) != self.leg.origin or not parsed.path.startswith("/v1/"):
                return
            request = response.request
            method = str(request.method)
            try:
                sent = request.post_data
            except Exception:  # noqa: BLE001 — a request without a body, or one Playwright cannot replay
                sent = None
            try:
                text = response.text()
            except Exception as err:  # noqa: BLE001 — a redirect or a body Chromium did not keep: said, never invented
                text = "<the body was not available to the browser's log: %s>" % err
            self.leg.exchange(self, method, parsed.path + (("?" + parsed.query) if parsed.query else ""), int(response.status), sent, text)
        except Exception as err:  # noqa: BLE001 — a log entry that could not be made must never stop a press
            self.leg.say("  (the browser's log could not record an answer: %s)" % err)

    # -- the passkey -----------------------------------------------------------------------------------------------------
    def credentials(self) -> List[Dict[str, Any]]:
        answer = self.cdp.send("WebAuthn.getCredentials", {"authenticatorId": self.authenticator_id})
        return [c for c in ((answer or {}).get("credentials") or []) if isinstance(c, dict)]

    def add_credential(self, credential: Dict[str, Any]) -> None:
        self.cdp.send("WebAuthn.addCredential", {"authenticatorId": self.authenticator_id, "credential": credential})

    # -- waiting --------------------------------------------------------------------------------------------------------
    def settle(self) -> None:
        """The network fallen quiet after a load or a press, bounded; a page that keeps reading (the run's page) is not waited on past the bound."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=int(SETTLE_TIMEOUT_SECONDS * 1000 * self.leg.time_scale))
        except self.leg.driver.timeout_error:
            pass

    def poll(self, check: Callable[[], bool], seconds: float = ACTION_TIMEOUT_SECONDS) -> bool:
        """
        Whether the page comes to show something within the bound, read again every POLL_SECONDS: a page renders an answer after the browser
        has received it (React sets its state, then renders), so what the page says after a press is read once it says it, never before.
        """
        deadline = time.monotonic() + seconds * self.leg.time_scale
        while True:
            try:
                if check():
                    return True
            except self.leg.driver.error:
                pass
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(int(POLL_SECONDS * 1000))

    def appears(self, locator: Any, seconds: float = ACTION_TIMEOUT_SECONDS) -> bool:
        """Whether the first element a locator names is visible within the bound — a fact of the page, not a fault."""
        try:
            locator.first.wait_for(state="visible", timeout=int(seconds * 1000 * self.leg.time_scale))
            return True
        except self.leg.driver.timeout_error:
            return False

    def must_appear(self, locator: Any, what: str, seconds: float = ACTION_TIMEOUT_SECONDS) -> Any:
        """The first element a locator names, visible within the bound — or the harness's own failure, named as the harness's (§6)."""
        if not self.appears(locator, seconds):
            shot = self.screenshot("missing")
            raise HarnessFault("the harness found no %s on %s within %d s (as %s; screenshot %s)" % (
                what, self.where(), int(seconds), self.name, shot or "not taken"))
        return locator.first

    # -- where the page stands --------------------------------------------------------------------------------------------
    def where(self) -> str:
        try:
            parsed = urllib.parse.urlparse(str(self.page.url))
            return parsed.path or "/"
        except Exception:  # noqa: BLE001
            return "the page"

    def goto(self, path: str) -> None:
        """Open a page of the estate as a person types its address: the base and the path, the one-time link's fragment included."""
        self.page.goto(self.leg.base + path, wait_until="domcontentloaded", timeout=int(NAVIGATION_TIMEOUT_SECONDS * 1000 * self.leg.time_scale))
        self.settle()

    def heading(self) -> str:
        """The page's own heading (its first h1), as a person reads it; empty where the page has none yet."""
        locator = self.page.get_by_role("heading", level=1)
        try:
            return " ".join(locator.first.inner_text().split()) if locator.count() else ""
        except self.leg.driver.error:
            return ""

    def estate_name(self) -> Optional[str]:
        """
        The estate the shell names in its sidebar (App.tsx: `<span class="visually-hidden">Estate: </span>{workspace.name}`): the name, or None
        where the page has no such brand, where it cannot be read, or where it names nothing.
        """
        locator = self.page.locator(S.CSS_ESTATE_NAME)
        try:
            if not locator.count():
                return None
            text = " ".join(locator.first.inner_text().split())
        except self.leg.driver.error:
            return None
        prefix = S.ESTATE_PREFIX.strip()
        name = text[len(prefix):].strip() if text.startswith(prefix) else text
        return name or None

    def in_the_shell(self) -> bool:
        """Whether the page stands inside an estate's shell: the sidebar, nav[aria-label="Sections"] (App.tsx), is on it."""
        try:
            return self.page.get_by_role("navigation", name=S.SIDEBAR_NAME, exact=True).count() > 0
        except self.leg.driver.error:
            return False

    def outside_the_shell_by_right(self) -> bool:
        """The two pages that stand outside the shell, and so name no estate: the invitation page (its own route) and the sign-in page."""
        return self.where() == S.INVITE_ROUTE or self.heading() == S.SIGN_IN_HEADING

    def guard(self, named: Optional[str] = None) -> None:
        """
        THE WRONG-ESTATE GUARD (Spec HRW-1 §2, the Attacker), before every press, fill and choice: the estate the page names must be one of the
        harness's own (aer360_tables.HARNESS_ESTATE_NAMES) and the one this run set out to walk; otherwise the run stops, nothing pressed. A page
        inside an estate's shell that names no estate stops the run too; only the two pages that stand outside the shell — the sign-in page and
        the invitation page — may pass without a name, and any other page that names none stops it. `named` is an estate a control itself names
        (the invitation page's Continue to <estate>).
        """
        if named is not None:
            self.hold_to_the_estate(named)
            return
        # a page still rendering is waited for, bounded: placed once it names an estate, or once it is one of the two pages outside the shell
        self.poll(lambda: bool(self.estate_name()) or (not self.in_the_shell() and self.outside_the_shell_by_right()), GUARD_WAIT_SECONDS)
        name = self.estate_name()
        if name:
            self.hold_to_the_estate(name)
            return
        if self.in_the_shell():
            raise RunStop(NO_ESTATE_IN_THE_SHELL % self.where(), prerequisite=WRONG_ESTATE)
        if self.outside_the_shell_by_right():
            return
        raise RunStop(NOT_A_PAGE_WITHOUT_THE_SHELL % (self.where(), self.heading()), prerequisite=WRONG_ESTATE)

    def hold_to_the_estate(self, name: str) -> None:
        """The estate a page or a control names, held to the harness's own and to the one this run set out to walk."""
        if not T.is_harness_estate(name):
            raise RunStop(NOT_PINNED_ESTATE % (name, ", ".join(T.HARNESS_ESTATE_NAMES)), prerequisite=WRONG_ESTATE)
        if self.leg.estate_name and name != self.leg.estate_name:
            raise RunStop(NOT_THIS_ESTATE % (name, self.leg.estate_name), prerequisite=WRONG_ESTATE)

    # -- the controls -----------------------------------------------------------------------------------------------------
    def control(self, name: str, role: str = "button", within: Any = None) -> Any:
        return (within if within is not None else self.page).get_by_role(role, name=name, exact=True)

    def has(self, name: str, role: str = "button", within: Any = None, seconds: float = 0.0) -> bool:
        locator = self.control(name, role, within)
        if seconds <= 0:
            try:
                return locator.count() > 0
            except self.leg.driver.error:
                return False
        return self.appears(locator, seconds)

    def press(self, name: Any, within: Any = None, role: str = "button", answer: Optional[Tuple[str, str]] = None,
              why: str = "", named: Optional[str] = None, seconds: float = ACTION_TIMEOUT_SECONDS, answer_optional: bool = False) -> Optional[Exchange]:
        """
        Press a control as a person does: the guard first; the control by its accessible name, exactly; enabled — waited for while the page
        catches up — or the page's own fact that it is not (a StationStop in the page's words); and where `answer` names the request the press
        makes (method, path pattern), that request's answer, waited for and returned. `answer_optional`: a press the page may refuse itself,
        sending nothing (Add payee's own check of an address) — no answer within the bound is then None, not the harness's fault.
        """
        self.guard(named)
        target = self.must_appear(self.control(name, role, within), "%s %r" % (role, shown(name)), seconds)
        if not self.poll(lambda: bool(target.is_enabled()), ENABLED_WAIT_SECONDS):
            raise StationStop("the page offers %r but will not let it be pressed (it is disabled) on %s, as %s" % (shown(name), self.where(), self.name))
        before = len(self.leg.exchanges)
        waited: Any = None
        if answer is not None:
            method, pattern = answer
            regex = re.compile(pattern)
            try:
                with self.page.expect_response(lambda r: r.request.method == method and bool(regex.search(urllib.parse.urlparse(r.url).path)),
                                               timeout=int(seconds * 1000 * self.leg.time_scale)) as waiting:
                    target.click()
                waited = waiting.value
            except self.leg.driver.timeout_error:
                if answer_optional:
                    self.settle()
                    self.leg.step("press", self.name, "pressed %r on %s%s — and the page sent nothing" % (shown(name), self.where(), (" — %s" % why) if why else ""))
                    return None
                shot = self.screenshot("no-answer")
                raise HarnessFault("the harness pressed %r on %s and no %s %s answered within %d s (as %s; screenshot %s)" % (
                    shown(name), self.where(), method, pattern, int(seconds), self.name, shot or "not taken"))
        else:
            target.click()
        self.settle()
        self.leg.step("press", self.name, "pressed %r on %s%s" % (shown(name), self.where(), (" — %s" % why) if why else ""))
        if answer is None:
            return None
        method, pattern = answer
        regex = re.compile(pattern)
        found = [x for x in self.leg.exchanges[before:] if x.method == method and regex.search(x.path.split("?", 1)[0]) and x.who == self.name]
        if not found and waited is not None:
            # the log's handler could not keep this answer (a body the browser let go): the answer the wait returned is read instead, and recorded
            self.on_response(waited)
            found = [x for x in self.leg.exchanges[before:] if x.method == method and regex.search(x.path.split("?", 1)[0]) and x.who == self.name]
        return found[-1] if found else None

    def fill(self, label: str, value: str, within: Any = None, exact: bool = True) -> None:
        self.guard()
        field = self.must_appear((within if within is not None else self.page).get_by_label(label, exact=exact), "field %r" % label)
        field.fill(value)
        self.leg.step("type", self.name, "typed %s into %r on %s" % (json.dumps(value, ensure_ascii=False), label, self.where()))

    def choose(self, label: str, within: Any = None) -> None:
        """A radio, chosen by its label as a person reads it."""
        self.guard()
        radio = self.must_appear(self.control(label, "radio", within), "choice %r" % label)
        radio.check()
        self.leg.step("choose", self.name, "chose %r on %s" % (label, self.where()))

    def tick(self, label: str, on: bool = True, within: Any = None, exact: bool = True) -> None:
        """A box, ticked (or cleared) by its label."""
        self.guard()
        box = self.must_appear((within if within is not None else self.page).get_by_role("checkbox", name=label, exact=exact), "box %r" % label)
        if box.is_checked() != on:
            box.check() if on else box.uncheck()
        self.leg.step("tick", self.name, "%s the box %r on %s" % ("ticked" if on else "cleared", label, self.where()))

    def select(self, label: str, option: str, within: Any = None) -> None:
        """A drop-down, set to the option a person reads in it."""
        self.guard()
        field = self.must_appear((within if within is not None else self.page).get_by_label(label, exact=True), "list %r" % label)
        field.select_option(label=option)
        self.leg.step("select", self.name, "chose %r from %r on %s" % (option, label, self.where()))

    def options_of(self, label: str, within: Any = None) -> List[str]:
        field = self.must_appear((within if within is not None else self.page).get_by_label(label, exact=True), "list %r" % label)
        return [" ".join(t.split()) for t in field.locator("option").all_inner_texts()]

    def value_of(self, label: str, within: Any = None) -> str:
        field = self.must_appear((within if within is not None else self.page).get_by_label(label, exact=True), "field %r" % label)
        return str(field.input_value())

    def card(self, title: str) -> Any:
        """A card of the page by its title (ui.tsx Card: a section.card whose head is an h2 of that title)."""
        return self.page.locator(S.CSS_CARD).filter(has=self.page.get_by_role("heading", name=title, exact=True))

    def text_of(self, locator: Any) -> str:
        try:
            return " ".join(locator.first.inner_text().split()) if locator.count() else ""
        except self.leg.driver.error:
            return ""

    def texts(self, role: str, within: Any = None, name: Optional[str] = None) -> List[str]:
        """Every region of a role on the page (status, alert, note), each read whole as a person hears it."""
        scope = within if within is not None else self.page
        locator = scope.get_by_role(role, name=name, exact=True) if name else scope.get_by_role(role)
        out: List[str] = []
        try:
            for item in locator.all():
                text = " ".join(item.inner_text().split())
                if text:
                    out.append(text)
        except self.leg.driver.error:
            pass
        return out

    def refusals(self, within: Any = None) -> List[str]:
        """Every refusal or warning the page shows (Refusals.tsx RefusalNotice: role alert, or status where acknowledgeable), word for word."""
        scope = within if within is not None else self.page
        out: List[str] = []
        try:
            for item in scope.locator(S.CSS_REFUSAL).all():
                text = " ".join(item.inner_text().split())
                if text:
                    out.append(text)
        except self.leg.driver.error:
            pass
        return out

    def main_text(self) -> str:
        return self.text_of(self.page.locator("main"))

    def screenshot(self, label: str) -> Optional[str]:
        """The page as a person sees it, written to the run folder; None where the folder is a dry one or the browser refused."""
        return self.leg.screenshot(self, label)

    # -- the store, read as the API leg reads it ----------------------------------------------------------------------------
    def read(self, path: str, expected: str) -> StoreRead:
        """A GET on the estate's own route under this person's session — the context's own request road, its cookies and nothing else."""
        try:
            answer = self.context.request.get(self.leg.base + path, timeout=int(NAVIGATION_TIMEOUT_SECONDS * 1000 * self.leg.time_scale))
            status, text = int(answer.status), str(answer.text())
        except self.leg.driver.error as err:
            status, text = 0, "the estate could not be reached for %s: %s" % (path, err)
        read = StoreRead(path, status, self.leg.secrets.redact_text(text))
        self.leg.store_step(self.name, read, expected)
        return read

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            self.context.close()
        except Exception:  # noqa: BLE001 — a context that will not close is the browser's, and the run has its evidence already
            pass


# ---------------------------------------------------------------------------
# The runner.
# ---------------------------------------------------------------------------
class RealWorld:
    """The browser leg: the stations R1 to R9, in a founder's shoes, on the harness's own estate."""

    def __init__(self, base: str = DEFAULT_BASE, store_root: str = STORE_ROOT, birth: Optional[str] = None,
                 start_at: Optional[str] = None, headed: bool = False, runs_root: str = RUNS_DIR, api_reports: str = API_REPORTS_DIR,
                 driver: Optional[Driver] = None, transport: Optional[Callable[[urllib.request.Request], Tuple[int, List[Tuple[str, str]], str]]] = None,
                 say: Callable[[str], None] = print, sleep: Callable[[float], None] = time.sleep, time_scale: float = 1.0,
                 in_colour: Optional[bool] = None, dry_folder: bool = False):
        self.base = base.rstrip("/")
        parsed = urllib.parse.urlparse(self.base)
        self.origin = "%s://%s" % (parsed.scheme, parsed.netloc)
        self.store_root = store_root
        # production's credentials and state at real-world/ (Spec HRW-1 §3); any other base's in a folder of its own beneath, so a run on one never
        # overwrites another's
        self.store_dir = os.path.join(store_root, STORE_FOLDER) if self.base == DEFAULT_BASE.rstrip("/") else os.path.join(
            store_root, STORE_FOLDER, re.sub(r"[^A-Za-z0-9.-]+", "-", parsed.netloc) or "estate")
        self.admin_env_path = os.path.join(store_root, T.ADMIN_ENV_FILE)
        self.payee_env_path = os.path.join(store_root, T.PAYEE_ENV_FILE)
        self.birth_path = birth
        self.start_at = normalise_station(start_at) if start_at else None
        self.headed = headed
        self.api_reports = api_reports
        self.driver = driver
        self.transport = transport or urllib_transport
        self.say = lambda text: say(self.secrets.redact_text(str(text)))  # nothing printed carries a secret whole: every line passes the redaction
        self.sleep = sleep
        self.time_scale = time_scale
        self.in_colour = in_colour if in_colour is not None else (say is print and hasattr(sys.stdout, "isatty") and sys.stdout.isatty())
        self.folder = RunFolder(runs_root, TESTER, dry=dry_folder)
        self.secrets = E.Secrets()
        self.started_at = now_iso()
        self.run_stamp = "%s-%s" % (_dt.datetime.now().strftime("%Y%m%d-%H%M%S"), os.urandom(2).hex())
        self.current = "start"
        self.outcomes: List[Outcome] = []
        self.findings: List[Finding] = []
        self.exchanges: List[Exchange] = []
        self.evidence: Dict[str, List[Dict[str, Any]]] = {s: [] for s in ["start", "resume"] + STATION_IDS}
        self.notes: Dict[str, List[str]] = {s: [] for s in ["start", "resume"] + STATION_IDS}
        self.next_steps: Dict[str, List[Tuple[str, str]]] = {s: [] for s in STATION_IDS}  # the page's own "what to do next", by station (the Customer Support hat)
        self.visitors: Dict[str, Visitor] = {}
        self.playwright: Any = None
        self.browser: Any = None
        self.stopped: Optional[str] = None
        self.shots = 0
        self.state: Dict[str, Any] = {}
        self.birth: Dict[str, Any] = {}
        self.estate_name: Optional[str] = None
        self.admin: Optional[Dict[str, str]] = None
        self.admin_read = False
        self.not_used: set = set()  # the people whose stored credential is another estate's, said once
        self.refused_birth: Optional[str] = None  # a printout naming an estate not the harness's own: R1 stops the run on it, before any link is opened
        # what this run made and read, station by station — the report's summary and R8's comparison read these
        self.facts: Dict[str, Any] = {"runs": [], "instructions_created": {}, "gas_credits": [], "owner_payee": None, "entries_before": None, "submitted_cents": 0,
                                      "entries_after": None, "receipt_ceilings": None, "wallet": None, "payees": [], "chain": {}}

    # -- the records ------------------------------------------------------------------------------------------------------
    def step(self, kind: str, who: str, what: str, expected: str = "", result: str = "", page: str = "", shot: Optional[str] = None) -> None:
        """One step of the station as it happened: who did what, what was expected, what came of it, and the page's own words."""
        entry = {"station": self.current, "kind": kind, "who": who, "what": self.secrets.redact_text(what), "expected": expected,
                 "result": self.secrets.redact_text(result), "page": self.secrets.redact_text(page), "screenshot": shot}
        self.evidence.setdefault(self.current, []).append(entry)
        self.folder.record(**entry)

    def store_step(self, who: str, read: StoreRead, expected: str) -> None:
        entry = {"station": self.current, "kind": "store", "who": who, "what": "GET %s" % redact_query(read.path), "expected": expected,
                 "result": "answered" if read.ok else "%s (%s)" % (read.sentence(), kind_of(read.status, read.json)), "status": read.status,
                 "came_back": read.text if read.json is None else json.dumps(self.secrets.redact(read.json), ensure_ascii=False), "page": "", "screenshot": None}
        self.evidence.setdefault(self.current, []).append(entry)
        self.folder.record(**entry)

    def note(self, text: str) -> None:
        text = self.secrets.redact_text(text)
        self.notes.setdefault(self.current, []).append(text)
        self.say("  %s note: %s" % (self.current, text))

    def next_step(self, where: str, sentence: str) -> None:
        """What the page told the founder to do next, in its own words (the Customer Support hat): R8 holds it against the manual."""
        sentence = " ".join(str(sentence or "").split())
        if sentence:
            self.next_steps.setdefault(self.current, []).append((where, self.secrets.redact_text(sentence)))

    def finding(self, probe: str, said: str, kind: str, page: str = "", store: str = "", expected: str = "", route: str = "", fails: bool = True) -> Finding:
        found = Finding(self.current, probe, self.secrets.redact_text(said), kind, self.secrets.redact_text(page), self.secrets.redact_text(store),
                        expected, redact_query(route) if route else "")
        self.findings.append(found)
        self.folder.record(station=self.current, kind="finding", probe=probe, said=found.said, classified=kind, page=found.page, store=found.store,
                           expected=expected, route=found.route)
        self.say(("%s — %s — %s: %s" % (self.current, FAIL, probe, found.said)) if fails else ("  %s finding: %s: %s" % (self.current, probe, found.said)))
        return found

    def exchange(self, v: Visitor, method: str, path: str, status: int, sent: Optional[str], text: str) -> None:
        """One request the browser made and its answer, the secrets in it learnt first and then redacted to their last four characters."""
        parsed_sent: Any = None
        if sent:
            try:
                parsed_sent = json.loads(sent)
            except ValueError:
                parsed_sent = None
        parsed_answer: Any = None
        try:
            parsed_answer = json.loads(text) if text and text.strip() else None
        except ValueError:
            parsed_answer = None
        for body in (parsed_sent, parsed_answer):
            if isinstance(body, dict):
                for key in ("token", "csrfToken"):
                    if isinstance(body.get(key), str):
                        self.secrets.add(body[key])
                if isinstance(body.get("url"), str) and "#" in body["url"]:
                    self.secrets.add(body["url"].split("#", 1)[1])
        red_sent = self.secrets.redact(parsed_sent) if parsed_sent is not None else (self.secrets.redact_text(sent) if sent else None)
        red_text = json.dumps(self.secrets.redact(parsed_answer), ensure_ascii=False) if parsed_answer is not None else self.secrets.redact_text(text)
        x = Exchange(self.current, v.name, method, path, status, red_sent, red_text, now_iso())
        x._json, x._parsed = (self.secrets.redact(parsed_answer) if parsed_answer is not None else None), True
        self.exchanges.append(x)
        self.folder.record(station=self.current, kind="request", who=v.name, route=redact_query(x.route), status=status, sent=red_sent, came_back=red_text)

    def answered(self, method: str, pattern: str, who: Optional[str] = None, since: int = 0) -> Optional[Exchange]:
        """The newest answer the browser received on a route since a point in the log, as the page received it."""
        regex = re.compile(pattern)
        for x in reversed(self.exchanges[since:]):
            if x.method == method and regex.search(x.path.split("?", 1)[0]) and (who is None or x.who == who):
                return x
        return None

    def screenshot(self, v: Visitor, label: str) -> Optional[str]:
        """
        The page as a person sees it, to the run folder — never while a one-time link stands on the page (§2: screenshots scrubbed of
        tokens and one-time links: a picture cannot be scrubbed, so the harness does not take it while the link is shown).
        """
        if self.folder.dry or v.closed:
            return None
        try:
            if v.page.get_by_label(S.INVITE_LINK_LABEL, exact=True).count():
                return None
        except Exception:  # noqa: BLE001
            return None
        self.shots += 1
        name = "%s-%02d-%s-%s.png" % (self.current, self.shots, v.key, re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "page")
        path = os.path.join(self.folder.path, name)
        try:
            v.page.screenshot(path=path, full_page=True)
        except Exception as err:  # noqa: BLE001 — a picture the browser would not take is said, never invented
            self.note("the screenshot %s was not taken: %s" % (name, err))
            return None
        text_path = path[:-4] + ".txt"
        try:
            with open(text_path, "w", encoding="utf-8") as handle:
                handle.write(self.secrets.redact_text(v.main_text()) + "\n")
        except OSError:
            pass
        return name

    # -- the store: credentials, state, the files the API leg files ------------------------------------------------------
    def credential_path(self, key: str) -> str:
        return os.path.join(self.store_dir, "%s.json" % key)

    def load_credential(self, key: str) -> Optional[Dict[str, Any]]:
        path = self.credential_path(key)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                record = json.load(handle)
        except (OSError, ValueError) as err:
            raise HarnessFault("the credential stored at %s could not be read: %s" % (path, err))
        if not isinstance(record, dict) or not isinstance(record.get("credential"), dict):
            raise HarnessFault("the credential stored at %s is not one this harness wrote (no `credential`)" % path)
        if record.get("base") and record.get("base") != self.base:
            self.note("the credential stored for %s at %s was created at %s, not %s; it is left alone and not used" % (key, path, record.get("base"), self.base))
            return None
        private = record["credential"].get("privateKey")
        if isinstance(private, str):
            self.secrets.add(private)
        return record

    def this_account(self) -> Optional[str]:
        """The platform account of the estate this run walks: the one the session named in R1 (kept in state.json), else the birth printout's."""
        return (self.state.get("estate") or {}).get("accountId") or (self.state.get("birth") or {}).get("account_id") or self.birth.get("account_id")

    def stored_for_this_estate(self, key: str) -> Optional[Dict[str, Any]]:
        """
        The person's stored credential where it is this estate's: a credential saved under another platform account (an earlier birth's estate,
        which carries the same name) is not used — it would sign into that estate, and the guard would stop the run — and is set aside, never
        deleted, when the new one is saved.
        """
        record = self.load_credential(key)
        if record is None:
            return None
        held = (record.get("workspace") or {}).get("accountId")
        account = self.this_account()
        if held and account and held != account:
            if key not in self.not_used:
                self.not_used.add(key)
                self.note("the credential stored for %s at %s was made on account %s, and this run's estate is account %s; it is not used" % (
                    A.PEOPLE[key].name, self.credential_path(key), held, account))
            return None
        return record

    def set_aside_credential(self, key: str) -> Optional[str]:
        """A credential of an earlier estate is set aside, never deleted, before a new one is saved in its place (as the API leg's --fresh does)."""
        path = self.credential_path(key)
        if not os.path.isfile(path):
            return None
        aside = "%s.%s.json" % (path[:-5], _dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.move(path, aside)
        return aside

    def save_credential(self, v: Visitor) -> Optional[Dict[str, Any]]:
        """
        The person's credential as the virtual authenticator holds it — once the estate has accepted it (a session in hand: an enrolment it
        verified, a sign-in it counted) and after every ceremony, so the signature counter the estate checks moves forward with it (Spec HRW-1
        §3: the passkey persists like a human's) — written 0600, never printed. A stored credential it replaces (another credential: an earlier
        estate's, or one the estate no longer knows) is set aside first, never deleted.
        """
        if self.folder.dry or v.session is None:
            return None
        held = v.credentials()
        rp_id = urllib.parse.urlparse(self.base).hostname
        credential = next((c for c in held if c.get("rpId") == rp_id), held[0] if held else None)
        if credential is None:
            self.note("%s's authenticator holds no credential to save" % v.name)
            return None
        if isinstance(credential.get("privateKey"), str):
            self.secrets.add(credential["privateKey"])
        previous = self.load_credential_quietly(v.key)
        if previous is not None and (previous.get("credential") or {}).get("credentialId") != credential.get("credentialId"):
            aside = self.set_aside_credential(v.key)
            if aside:
                self.note("the credential stored for %s (account %s) was set aside at %s, never deleted, before the new one was saved" % (
                    v.name, (previous.get("workspace") or {}).get("accountId"), aside))
            previous = None
        session = v.session
        workspace = session.get("workspace") if isinstance(session.get("workspace"), dict) else {}
        record = {"kind": CREDENTIAL_KIND, "person": v.key, "name": v.name, "base": self.base, "rpId": credential.get("rpId"),
                  "workspace": {"id": workspace.get("id") or (previous or {}).get("workspace", {}).get("id"),
                                "name": workspace.get("name") or (previous or {}).get("workspace", {}).get("name"),
                                "accountId": workspace.get("aapAccountId") or (previous or {}).get("workspace", {}).get("accountId")},
                  "estateCredentialId": session.get("credentialId") or (previous or {}).get("estateCredentialId"),
                  "credential": credential, "createdAt": (previous or {}).get("createdAt") or now_iso(), "savedAt": now_iso()}
        PK.write_private(self.credential_path(v.key), record)
        return record

    def save_everyone(self) -> None:
        """Every person with a session in this run, their credential saved as it stands — at the end of each station, whatever ended it."""
        for v in list(self.visitors.values()):
            if v.closed or v.session is None:
                continue
            try:
                self.save_credential(v)
            except (HarnessFault, OSError) as err:
                self.note("%s's credential could not be saved: %s" % (v.name, err))
            except Exception as err:  # noqa: BLE001 — the browser's own error, said and never fatal to the report
                if self.driver is not None and isinstance(err, (self.driver.timeout_error, self.driver.error)):
                    self.note("%s's credential could not be read from the browser: %s" % (v.name, err))
                else:
                    raise

    def load_credential_quietly(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            with open(self.credential_path(key), "r", encoding="utf-8") as handle:
                record = json.load(handle)
            return record if isinstance(record, dict) else None
        except (OSError, ValueError):
            return None

    def load_state(self) -> None:
        path = os.path.join(self.store_dir, STATE_FILE)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                self.state = loaded if isinstance(loaded, dict) and loaded.get("base") in (None, self.base) else {}
            except (OSError, ValueError) as err:
                raise HarnessFault("the browser leg's state at %s could not be read: %s" % (path, err))
        self.state.setdefault("base", self.base)

    def set_aside_state(self) -> Optional[str]:
        """An earlier estate's state, set aside beside the new one and never deleted (as a credential of an earlier estate is)."""
        path = os.path.join(self.store_dir, STATE_FILE)
        if self.folder.dry or not os.path.isfile(path):
            return None
        aside = "%s.%s.json" % (path[:-5], _dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.move(path, aside)
        return aside

    def save_state(self) -> None:
        if self.folder.dry:
            return
        self.state["savedAt"] = now_iso()
        PK.write_private(os.path.join(self.store_dir, STATE_FILE), self.state)

    def read_birth(self) -> None:
        """
        The run's input (Spec HRW-1 R1): the birth script's printout — the one-time link, the account, the founder's credential, the estate it
        names — never typed into the report. A printout naming an estate not the harness's own touches nothing of the store, and R1 stops the run
        on it before the link is opened (the invitation page asks for a key the moment it opens, so the guard is held before, never after).
        """
        if self.birth_path:
            path = os.path.expanduser(self.birth_path)
            try:
                with (sys.stdin if path == "-" else open(path, "r", encoding="utf-8")) as handle:
                    text = handle.read()
            except OSError as err:
                raise HarnessFault("the birth printout at %s could not be read: %s" % (path, err))
            self.birth = parse_birth(text)
            if self.birth.get("link"):
                self.secrets.add(E.token_of_link(self.birth["link"]))
            if not self.birth.get("link"):
                raise HarnessFault("the birth printout at %s carries no one-time link (a line ending /invite#<token>)" % path)
            company = self.birth.get("company")
            if company and not T.is_harness_estate(company):
                self.refused_birth = NOT_PINNED_ESTATE % (company, ", ".join(T.HARNESS_ESTATE_NAMES))
                return
            earlier = (self.state.get("estate") or {}).get("accountId")
            if self.birth.get("account_id") and earlier and earlier != self.birth["account_id"]:
                # a rebirth: what state.json holds (the wallet, the runs) is the earlier estate's, so this run starts afresh beside it
                aside = self.set_aside_state()
                self.state = {"base": self.base}
                self.note("the browser leg's state was of account %s and this birth's estate is account %s, so this run starts afresh (the earlier state %s)" % (
                    earlier, self.birth["account_id"], ("kept at %s" % aside) if aside else "left as it was"))
        if self.birth.get("company"):
            self.estate_name = str(self.birth["company"])
        elif isinstance(self.state.get("estate"), dict) and self.state["estate"].get("company"):
            self.estate_name = str(self.state["estate"]["company"])
        if self.birth.get("account_id") or self.birth.get("no_email_warning") or self.birth.get("email"):
            self.state["birth"] = {k: self.birth.get(k) for k in ("account_id", "founder_credential", "company", "display_name", "email", "no_email_warning")}
            self.state["birth"]["readAt"] = now_iso()

    def read_admin_env(self) -> Optional[Dict[str, str]]:
        """The platform's admin credential as the API leg files it (Spec T14: AAP_ADMIN_BASE_URL, AAP_ADMIN_KEY), read once, never printed."""
        if self.admin_read:
            return self.admin
        self.admin_read = True
        if not os.path.isfile(self.admin_env_path):
            return None
        try:
            with open(self.admin_env_path, "r", encoding="utf-8") as handle:
                values = T.parse_env_file(handle.read())
        except OSError:
            return None
        base = values.get(T.ADMIN_ENV_URL_KEY, "").strip().rstrip("/")
        key = values.get(T.ADMIN_ENV_KEY_KEY, "").strip()
        if not base or not key:
            return None
        self.secrets.add(key)
        self.admin = {"base": base, "key": key, "path": self.admin_env_path}
        return self.admin

    def owner_payee(self) -> Tuple[Optional[str], Optional[str]]:
        """Spec T24: the owner's own wallet, from payee.env — the one address this leg ever pays — or what is wrong with the file."""
        if not os.path.isfile(self.payee_env_path):
            return None, "is not filed"
        with open(self.payee_env_path, "r", encoding="utf-8") as handle:
            return T.owner_payee_of(handle.read())

    # -- the roads that are not the estate's: the chain, the platform's admin road --------------------------------------------
    def outside(self, who: str, method: str, url: str, body: Any, headers: Optional[Dict[str, str]] = None) -> Tuple[int, Any, str]:
        """One call outside the estate, recorded redacted, never retried; a road that cannot be reached is status 0 and its words."""
        sent_headers = {"Accept": "application/json", "User-Agent": "%s (python-stdlib)" % USER_AGENT_NOTE}
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            sent_headers["Content-Type"] = "application/json"
        sent_headers.update(headers or {})
        request = urllib.request.Request(url, data=data, method=method, headers=sent_headers)
        try:
            status, _, text = self.transport(request)
        except E.Unreachable as err:
            status, text = 0, str(err)
        try:
            parsed = json.loads(text) if text and text.strip() else None
        except ValueError:
            parsed = None
        red = json.dumps(self.secrets.redact(parsed), ensure_ascii=False) if parsed is not None else self.secrets.redact_text(text)
        self.folder.record(station=self.current, kind="outside", who=who, route=redact_query("%s %s" % (method, url)), status=status,
                           sent=self.secrets.redact(body), came_back=red)
        self.evidence.setdefault(self.current, []).append({"station": self.current, "kind": "outside", "who": who, "what": redact_query("%s %s" % (method, url)),
                                                           "expected": "", "result": "HTTP %d" % status if status else "unreachable", "page": "",
                                                           "came_back": red, "screenshot": None})
        return status, parsed, text

    def chain_balance(self, holder: str, token: Optional[str], who: str) -> Tuple[Optional[int], str]:
        """A balance read from the chain as the API leg reads a payee's (eth_call balanceOf on the token the estate names), or the RPC's words."""
        url = T.public_rpc_url(T.PAYEE_CHAIN)
        if not url:
            return None, "no public RPC is known for %s (aer360_tables.py, public_rpc_url)" % T.PAYEE_CHAIN
        if not token:
            return None, "the estate names no %s contract on %s, so there is nothing to read the balance against" % (T.PAYMENT_ASSET, T.PAYEE_CHAIN)
        body = {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": token, "data": T.balance_of_call_data(holder)}, "latest"]}
        status, parsed, text = self.outside(who, "POST", url, body)
        if status == 0:
            return None, "the RPC at %s could not be reached: %s" % (url, text)
        if not isinstance(parsed, dict) or parsed.get("error") is not None:
            return None, "the RPC at %s answered %s" % (url, json.dumps(parsed.get("error"), ensure_ascii=False) if isinstance(parsed, dict) else (text[:200] or "nothing"))
        result = parsed.get("result")
        try:
            minor = int(result, 16) if isinstance(result, str) and result not in ("0x", "") else 0
        except ValueError:
            return None, "the RPC at %s answered %r for balanceOf, which is not a number" % (url, str(result)[:80])
        return minor, "%s of %s read from the chain (%s)" % (T.usdc_dollars(minor), T.PAYMENT_ASSET, url)

    # -- the browser ----------------------------------------------------------------------------------------------------
    def open_browser(self) -> None:
        if self.driver is None:
            self.driver = live_driver()
        try:
            self.playwright = self.driver.start()
            self.browser = self.playwright.chromium.launch(headless=not self.headed)
        except Exception as err:  # noqa: BLE001 — Playwright's own error, named as the harness's with its cure
            if isinstance(err, (self.driver.timeout_error, self.driver.error)):
                self.close_browser()
                raise HarnessFault(CHROMIUM_MISSING % (" ".join(str(err).split())[:400], sys.executable))
            raise

    def close_browser(self) -> None:
        for v in list(self.visitors.values()):
            v.close()
        for thing, how in ((self.browser, "close"), (self.playwright, "stop")):
            if thing is not None:
                try:
                    getattr(thing, how)()
                except Exception:  # noqa: BLE001 — the run's evidence is written whatever the browser does on its way out
                    pass

    def visitor(self, key: str, fresh: bool = False, bare: bool = False) -> Visitor:
        """
        The person's own context: one per person, opened when first needed (or afresh: R2 signs in from a fresh context), with a CDP
        virtual authenticator (WebAuthn.enable, addVirtualAuthenticator) and the person's stored credential re-added (addCredential) where it
        is this estate's. `bare`: a context for an enrolment, its authenticator empty, so the one credential it holds afterwards is the new one.
        """
        if key in self.visitors and not fresh and not bare and not self.visitors[key].closed:
            return self.visitors[key]
        if key in self.visitors:
            self.visitors[key].close()
        context = self.browser.new_context(viewport={"width": 1280, "height": 960}, locale="en-AU")
        page = context.new_page()
        page.set_default_timeout(int(ACTION_TIMEOUT_SECONDS * 1000 * self.time_scale))
        cdp = context.new_cdp_session(page)
        cdp.send("WebAuthn.enable", {"enableUI": False})
        added = cdp.send("WebAuthn.addVirtualAuthenticator", {"options": dict(VIRTUAL_AUTHENTICATOR)})
        v = Visitor(self, key, A.PEOPLE[key].name, context, page, cdp, str((added or {}).get("authenticatorId")))
        stored = None if bare else self.stored_for_this_estate(key)
        if stored is not None:
            v.add_credential(stored["credential"])
        self.visitors[key] = v
        return v

    def founder(self) -> Visitor:
        v = self.visitors.get(A.FOUNDER)
        if v is None or v.closed or v.session is None:
            raise StationStop("the founder has no session in this run (R1 and R2 did not end in one)", prerequisite=NO_FOUNDER_SESSION)
        return v

    def adopt_estate(self, name: Any, where: str) -> None:
        """The estate this run walks, from the first page or record that names it: one of the harness's own, or the run stops (§2)."""
        text = str(name or "").strip()
        if not text:
            return
        if not T.is_harness_estate(text):
            raise RunStop(NOT_PINNED_ESTATE % (text, ", ".join(T.HARNESS_ESTATE_NAMES)), prerequisite=WRONG_ESTATE)
        if self.estate_name and text != self.estate_name:
            raise RunStop(NOT_THIS_ESTATE % (text, self.estate_name), prerequisite=WRONG_ESTATE)
        if not self.estate_name:
            self.note("this run walks %s (named by %s)" % (text, where))
        self.estate_name = text
        self.state.setdefault("estate", {})["company"] = text

    # -- running ----------------------------------------------------------------------------------------------------------
    def run(self) -> List[Outcome]:
        self.load_state()
        self.read_birth()
        self.open_browser()
        try:
            start_index = STATION_IDS.index(self.start_at) if self.start_at else 0
            if start_index:
                self.resume()
            for index, (station, title) in enumerate(STATIONS):
                if index < start_index:
                    outcome = Outcome(station, SKIPPED, "%s: resumed at %s" % (title, self.start_at))
                elif self.stopped:
                    outcome = Outcome(station, NOT_RUN, "%s: not run — the run stopped: %s" % (title.lower(), self.stopped))
                else:
                    outcome = self.run_station(station, title)
                outcome.line = self.secrets.redact_text(outcome.line)
                self.outcomes.append(outcome)
                self.say(self.line(outcome))
        finally:
            self.close_browser()
            self.save_state()
        return self.outcomes

    def line(self, outcome: Outcome) -> str:
        kind = outcome.outcome
        if kind == FAILED_PREREQUISITE and self.in_colour:
            kind = E.RED + kind + E.RESET
        return "%s — %s — %s" % (outcome.station, kind, outcome.line)

    def run_station(self, station: str, title: str) -> Outcome:
        self.current = station
        method = getattr(self, "station_%s" % station.lower())
        try:
            outcome = method()
        except RunStop as stop:
            self.stopped = stop.sentence
            self.finding(stop.prerequisite or "the run stopped", stop.sentence, stop.kind)
            outcome = Outcome(station, FAILED_PREREQUISITE if stop.prerequisite and stop.prerequisite != WRONG_ESTATE else FAIL,
                              "%s: %s%s" % (title.lower(), ("%s — " % stop.prerequisite) if stop.prerequisite else "", stop.sentence))
        except StationStop as err:
            if not err.prerequisite:
                # every stop classified (the charter law): the vocabulary word its sentence ends on, where it carries the estate's answer; else what a
                # page or the store showed
                found = re.search(r"\((%s)\)\W*$" % "|".join(re.escape(k) for k in (REFUSED, UNREACHABLE, MALFORMED_QUESTION, ANSWERED_WITH_ERROR)), str(err))
                self.finding("%s stopped" % station, str(err), found.group(1) if found else SCREEN)
            outcome = Outcome(station, FAILED_PREREQUISITE if err.prerequisite else FAIL, "%s: %s" % (title.lower(), err))
        except HarnessFault as err:
            self.finding("the harness's own failure", str(err), HARNESS)
            outcome = Outcome(station, FAIL, "%s: the harness could not complete this station — its own failure, not the estate's: %s" % (title.lower(), err))
        except (A.UnknownQuestion, A.AnswerDoesNotFit) as err:
            self.finding("the book does not answer the question the estate serves", str(err), HARNESS, expected="the answer book's answer for every question served")
            outcome = Outcome(station, FAIL, "%s: %s" % (title.lower(), err))
        except Exception as err:  # noqa: BLE001 — Playwright's own errors are the harness's road failing, never the estate's
            if self.driver is not None and isinstance(err, (self.driver.timeout_error, self.driver.error)):
                self.finding("the harness's own failure", "the browser answered %s: %s" % (type(err).__name__, err), HARNESS)
                outcome = Outcome(station, FAIL, "%s: the harness could not complete this station — the browser answered %s: %s" % (
                    title.lower(), type(err).__name__, " ".join(str(err).split())[:400]))
            else:
                raise
        founder = self.visitors.get(A.FOUNDER)
        if founder is not None and not founder.closed and station not in ("R8",):
            self.step("page", founder.name, "the page at the end of %s" % station, page=founder.heading(), shot=founder.screenshot("end"))
        self.save_everyone()
        self.save_state()
        outcome.line = self.secrets.redact_text(outcome.line)
        return outcome

    def resume(self) -> None:
        """--from: every person with a stored credential signs in from their own context, so the later stations have their sessions."""
        self.current = "resume"
        for key in (A.FOUNDER,) + S.APPROVERS:
            if self.stored_for_this_estate(key) is None:
                self.say("resume — %s has no stored credential for this estate; the stations needing %s say so" % (A.PEOPLE[key].name, A.PEOPLE[key].name))
                continue
            try:
                v = self.visitor(key)
                self.sign_in(v)
            except RunStop as stop:
                self.stopped = stop.sentence
                self.finding(stop.prerequisite or "the run stopped", stop.sentence, stop.kind)
                return
            except (StationStop, HarnessFault) as err:
                self.say("resume — %s could not sign in: %s" % (A.PEOPLE[key].name, err))
                continue
            except Exception as err:  # noqa: BLE001 — the browser's own error, named as the harness's
                if self.driver is not None and isinstance(err, (self.driver.timeout_error, self.driver.error)):
                    self.finding("the harness's own failure", "%s could not be signed in: the browser answered %s: %s" % (A.PEOPLE[key].name, type(err).__name__, err), HARNESS)
                    continue
                raise
            self.say("resume — %s signed in with the stored credential" % A.PEOPLE[key].name)

    # -- the sign-in a founder makes (R2, and every resumed person) ---------------------------------------------------------
    def sign_in(self, v: Visitor) -> Dict[str, Any]:
        """
        The sign-in page as a person meets it (SignIn.tsx): the heading, one control, and the passkey prompt the virtual authenticator answers
        with the stored credential; the session the estate answered; the shell, and the estate its sidebar names (the guard).
        """
        v.goto("/")
        if v.estate_name() is None:
            heading = v.heading()
            if heading != S.SIGN_IN_HEADING:
                raise StationStop("the sign-in page did not appear: the page's heading reads %r, not %r (%s)" % (heading, S.SIGN_IN_HEADING, v.where()))
            self.next_step("the sign-in page", "%s [%s]" % (heading, S.SIGN_IN_BUTTON))
            verified = v.press(S.SIGN_IN_BUTTON, answer=("POST", r"^/v1/auth/login/verify$"))
            if verified is None or not verified.ok:
                said = " | ".join(v.refusals()) or (verified.sentence() if verified else "no answer")
                raise StationStop("%s could not sign in: the page says %s; the estate answered %s (%s)" % (
                    v.name, json.dumps(said, ensure_ascii=False), verified.sentence() if verified else "nothing",
                    kind_of(verified.status, verified.json) if verified else UNREACHABLE))
            v.session = verified.json if isinstance(verified.json, dict) else None
            self.save_credential(v)  # the estate counted the signature: the counter kept now, or the next run's sign-in is refused as a replay
        if not v.appears(v.page.get_by_role("navigation", name=S.SIDEBAR_NAME)):
            raise StationStop("%s signed in and the estate's shell did not appear on %s" % (v.name, v.where()))
        name = v.estate_name()
        self.adopt_estate(name, "the sidebar after %s signed in" % v.name)
        v.guard()
        if v.session is None:
            read = v.read(S.SESSION_ROUTE, "the session this context holds")
            v.session = read.json if read.ok and isinstance(read.json, dict) else None
        self.save_credential(v)
        return v.session or {}

    # ======================================================================================================================
    # The people's addresses, as the founder types them (Spec HRW-1 §4: capitals and surrounding spaces; one approver whose
    # display name is not their address) and as the estate folds them.
    # ======================================================================================================================
    @staticmethod
    def typed_address(key: str) -> str:
        return T.REAL_WORLD_TYPED_ADDRESSES.get(key, A.PEOPLE[key].email)

    @classmethod
    def address_of(cls, key: str) -> str:
        return fold(cls.typed_address(key))

    @classmethod
    def person_by_address(cls, email: Any) -> Optional[str]:
        wanted = fold(email)
        return next((k for k in A.PEOPLE if cls.address_of(k) == wanted or fold(A.PEOPLE[k].email) == wanted), None)

    # ======================================================================================================================
    # R1 — Enrol.
    # ======================================================================================================================
    def enrol(self, v: Visitor, link: str) -> str:
        """
        The one-time link opened as a person opens it (Invite.tsx): the page asks for the key by itself the moment it opens — the virtual
        authenticator confirms — or offers its one button where it could not; the welcome read; Continue to the estate the session names.
        Answers the welcome, in the page's words.
        """
        token = E.token_of_link(link)
        self.secrets.add(token)
        parsed = urllib.parse.urlparse(link.strip())
        if "%s://%s" % (parsed.scheme, parsed.netloc) != self.origin:
            raise StationStop("the one-time link is for %s://%s, and this run walks %s; nothing was opened" % (parsed.scheme, parsed.netloc, self.origin))
        before = len(self.exchanges)
        v.goto("%s#%s" % (parsed.path or "/invite", token))
        done = v.page.get_by_role("heading", level=1).filter(has_text=re.compile("|".join(re.escape(s) for s in S.ENROLMENT_DONE_HEADINGS)))
        if not v.appears(done, ACTION_TIMEOUT_SECONDS):
            heading = v.heading()
            if heading == S.INVITE_DEAD_HEADING:
                options = self.answered("POST", r"^/v1/auth/invite/options$", v.name, before)
                said = " | ".join(v.refusals()) or "no sentence"
                raise StationStop("the invitation page says %r: %s; the estate answered %s (%s)" % (
                    heading, json.dumps(said, ensure_ascii=False), options.sentence() if options else "nothing", kind_of(options.status, options.json) if options else UNREACHABLE))
            if v.has(S.ENROLMENT_CREATE_ACTION, seconds=2.0):
                self.step("page", v.name, "the invitation page did not finish by itself; it offers its one button", page=" | ".join(
                    [heading] + v.texts("status") + v.refusals()))
                v.press(S.ENROLMENT_CREATE_ACTION, answer=("POST", r"^/v1/auth/invite/verify$"), why="the page's one button")
            v.must_appear(done, "the invitation page's completing heading (one of %s)" % "; ".join(S.ENROLMENT_DONE_HEADINGS))
        verify = self.answered("POST", r"^/v1/auth/invite/verify$", v.name, before)
        if verify is None or not verify.ok or not isinstance(verify.json, dict):
            said = " | ".join(v.refusals())
            raise StationStop("the invitation page shows %r and the estate's answer to the key is %s; the page says %s" % (
                v.heading(), verify.sentence() if verify else "absent from the browser's log", json.dumps(said or "nothing more", ensure_ascii=False)))
        v.session = verify.json
        self.save_credential(v)  # the key exists at the estate and the link is spent: kept now, whatever stops the station after
        heading = v.heading()
        welcome = v.text_of(v.page.locator(S.CSS_CARD))
        workspace = verify.json.get("workspace") if isinstance(verify.json.get("workspace"), dict) else {}
        estate = str(workspace.get("name") or "")
        self.adopt_estate(estate, "the session the one-time link opened")
        cont = S.continue_label(estate)
        self.step("page", v.name, "the invitation page after the key", page="%s — %s" % (heading, welcome))
        self.next_step("the invitation page", "%s %s [%s]" % (heading, welcome, cont))
        v.press(cont, named=estate, why="the page's next step")
        if not v.appears(v.page.get_by_role("navigation", name=S.SIDEBAR_NAME)):
            raise StationStop("%s pressed %r and the estate's shell did not appear on %s" % (v.name, cont, v.where()))
        v.guard()
        self.save_credential(v)
        return "%s — %s" % (heading, welcome)

    def station_r1(self) -> Outcome:
        key = A.FOUNDER
        if self.refused_birth:
            raise RunStop(self.refused_birth, prerequisite=WRONG_ESTATE)
        stored = self.stored_for_this_estate(key)
        link = self.birth.get("link")
        said: List[str] = []
        # a link given is a link to use, unless the credential stored for the founder is this very estate's (the printout's account): a rerun
        confirmed = stored is not None and bool(self.this_account()) and (stored.get("workspace") or {}).get("accountId") == self.this_account()
        if stored is not None and (confirmed or not link):
            v = self.visitor(key)
            self.sign_in(v)
            said.append("signed in with the credential stored at %s (created %s), so the one-time link%s was not needed" % (
                self.credential_path(key), stored.get("createdAt"), " given" if link else ""))
        elif link:
            if not self.birth.get("company") or not T.is_harness_estate(self.birth.get("company")):
                raise StationStop("the printout names no estate (its \"Invite for <estate> (<founder>)\" line), so the guard cannot be held before the link is "
                                  "used — the invitation page asks for a key the moment it opens; nothing was opened", prerequisite=FOUNDER_NOT_ENROLLED)
            v = self.visitor(key, fresh=True, bare=True)
            welcome = self.enrol(v, link)
            said.append("enrolled by the one-time link: the page said %s" % json.dumps(welcome, ensure_ascii=False))
        else:
            raise StationStop("no credential is stored for %s at %s and no --birth <the birth script's printout> was given; the first run needs the "
                              "printout, whose one-time link enrols the founder" % (A.PEOPLE[key].name, self.credential_path(key)), prerequisite=FOUNDER_NOT_ENROLLED)
        session = v.session or {}
        workspace = session.get("workspace") if isinstance(session.get("workspace"), dict) else {}
        self.state.setdefault("estate", {}).update({"company": self.estate_name, "workspaceId": workspace.get("id"), "accountId": workspace.get("aapAccountId")})
        # THE STORE, as the API leg reads it: the invitation register (redeemedAt, email, credentialId) and the session the passkey opened.
        register = v.read(S.INVITES_ROUTE, "the invitation register: the founder's row redeemed (redeemedAt), the invitee's email recorded (Spec AER360-SEAT-CASE) and the credential it enrolled")
        mine = session.get("credentialId")
        rows = [r for r in ((register.json or {}).get("invites") or []) if isinstance(r, dict)] if register.ok else []
        row = next((r for r in rows if mine and r.get("credentialId") == mine and r.get("state") == "redeemed"), None) or next(
            (r for r in rows if r.get("state") == "redeemed" and fold(r.get("displayName")) == fold(v.name)), None)
        failures = 0
        typed = self.typed_address(key)
        if not register.ok:
            failures += 1
            self.finding("the invitation register could not be read", "GET %s answered %s" % (S.INVITES_ROUTE, register.sentence()), kind_of(register.status, register.json),
                         store=register.text[:400], expected="the founder's row, redeemed")
        elif row is None:
            failures += 1
            self.finding("no redeemed invitation for the founder's credential", "the register lists %d invitation(s) and none is redeemed under credential %s" % (
                len(rows), last4(mine)), SCREEN, store=json.dumps(rows, ensure_ascii=False)[:600], expected="enrollment_invites.redeemed_at set for the founder's row")
        else:
            said.append("the register: %s's invitation %s at %s, credential %s" % (row.get("displayName"), row.get("state"), row.get("redeemedAt"), last4(row.get("credentialId"))))
            email = row.get("email")
            warning = (self.state.get("birth") or {}).get("no_email_warning") or self.birth.get("no_email_warning")
            if not email:
                # the whole run stops, warned or not: a founder whose presses carry no name would walk the interview and the payees as nobody
                # (Spec AER360-SEAT-CASE §3.2). invite.mjs prints its warning to standard error (invite.ts:159), so a printout saved without 2>&1 lacks it.
                why = ("the birth printed %r and the register reads no email for %s, as the warning said it would" % (warning, v.name) if warning else
                       "the register reads no email for %s, and the printout this run read carries no warning that --email was left out (invite.mjs prints "
                       "it to standard error, so a printout saved without 2>&1 leaves it out)" % v.name)
                raise RunStop("%s: run the record script on the estate box (dist-deploy/record-founder-emails.mjs, --dry first, then without; Spec "
                              "AER360-SEAT-CASE §3.3, the Onboarding Road 1.5 §8a), then rerun with --from S1 — %s" % (why, "; ".join(said)), prerequisite=EMAIL_NOT_RECORDED)
            elif fold(email) != fold(typed):
                failures += 1
                self.finding("the founder was born with another address", "the register records %s for %s, and the charter will name %s (%s folded): the seat the charter "
                             "compiles for her is not hers, so her presses will not count" % (email, v.name, json.dumps(typed), fold(typed)), SCREEN,
                             store=json.dumps(row, ensure_ascii=False), expected="the birth's --email folds to the charter's founder address")
            else:
                proved = (" — recorded by the record script after a birth without --email, whose one-line warning this run's printout carried: %r" % warning) if warning else ""
                said.append("invitee_email %s%s" % (email, proved))
        read = v.read(S.SESSION_ROUTE, "the session the passkey opened: its credential (the webauthn_credentials row the estate verified it against), the workspace and the roles")
        if read.ok and isinstance(read.json, dict):
            said.append("the passkey's row stands: the estate opened a session for credential %s, roles %s" % (
                last4(read.json.get("credentialId")), ", ".join(read.json.get("roles") or []) or "none"))
        else:
            failures += 1
            self.finding("the session could not be read", "GET %s answered %s" % (S.SESSION_ROUTE, read.sentence()), kind_of(read.status, read.json), expected="the session the passkey opened")
        return Outcome("R1", FAIL if failures else PASS, "%s as %s, in %s: %s" % ("enrol", v.name, self.estate_name, "; ".join(said)))

    # ======================================================================================================================
    # R2 — Sign in, from a fresh context with the saved credential.
    # ======================================================================================================================
    def station_r2(self) -> Outcome:
        key = A.FOUNDER
        stored = self.load_credential(key)
        if stored is None:
            raise StationStop("no credential is stored for %s at %s, so there is nothing to sign in with" % (A.PEOPLE[key].name, self.credential_path(key)),
                              prerequisite=FOUNDER_NOT_ENROLLED)
        v = self.visitor(key, fresh=True)
        session = self.sign_in(v)
        name = v.estate_name()
        landing = v.heading()
        arrival = [t for t in v.texts("status") if t]
        journey = v.texts("navigation", name=S.JOURNEY_NAME)
        self.next_step("the landing page", " | ".join([landing] + arrival + journey))
        self.step("page", v.name, "the page a founder lands on", page=" | ".join([landing] + arrival + journey))
        read = v.read(S.SESSION_ROUTE, "the session a fresh context opened with the stored credential: the same estate credential as enrolment")
        failures = 0
        same = read.ok and isinstance(read.json, dict) and stored.get("estateCredentialId") in (None, read.json.get("credentialId"))
        if not same:
            failures += 1
            self.finding("a fresh context opened another credential's session", "the stored credential was enrolled as %s and the session reads %s" % (
                last4(stored.get("estateCredentialId")), last4((read.json or {}).get("credentialId") if isinstance(read.json, dict) else None)), SCREEN,
                store=read.text[:400], expected="the same credential")
        roles = list((read.json or {}).get("roles") or []) if isinstance(read.json, dict) else []
        return Outcome("R2", FAIL if failures else PASS, "signed in from a fresh context with the stored credential; the sidebar names %s; the page lands on %s; roles %s%s" % (
            name, json.dumps(landing, ensure_ascii=False), ", ".join(roles) or "none", ("; the page says %s" % json.dumps(" | ".join(arrival), ensure_ascii=False)) if arrival else ""))

    # ======================================================================================================================
    # R3 — The Policy Interview, through the screens, with the untidy spellings, under catalog version 15.
    # ======================================================================================================================
    def read_entries(self, when: str) -> Optional[List[Dict[str, Any]]]:
        """
        The account's signing entries on the platform's own read road (GET /v1/admin/accounts/{id}/policies), read-only, for this estate's own
        account and no other — the account the session names — with the admin credential the API leg files. None, and the reason said, where it
        is not filed, not reachable, or refuses: the write's receipt then speaks for the entries (the module's header, note 5).
        """
        account = (self.state.get("estate") or {}).get("accountId") or (self.state.get("birth") or {}).get("account_id")
        admin = self.read_admin_env()
        if not account:
            self.note("the signing entries were not read %s: no platform account is named by the session or the birth printout" % when)
            return None
        if admin is None:
            self.note("the signing entries were not read %s: %s is not filed (AAP_ADMIN_BASE_URL, AAP_ADMIN_KEY), so the write's own receipt speaks for them" % (
                when, self.admin_env_path))
            return None
        status, body, text = self.outside("the harness, on the platform's read road", "GET", admin["base"] + S.ADMIN_POLICIES_ROUTE % account, None,
                                          headers={"Authorization": "Bearer %s" % admin["key"]})
        if not (200 <= status < 300) or not isinstance(body, dict):
            self.note("the signing entries were not read %s: the platform's read road answered %s — %s (%s)" % (
                when, status or "nothing", (body or {}).get("error") if isinstance(body, dict) else text[:200], kind_of(status, body)))
            return None
        entries = [e for e in (body.get("policy_entries") or body.get("policies") or []) if isinstance(e, dict)]
        return [{"name": e.get("name"), "access": e.get("access_type"), "active": e.get("active", True), "supersededBy": str(e.get("superseded_by") or ""),
                 "perPaymentUsd": e.get("max_amount_per_tx_usd"), "perDayUsd": e.get("max_amount_per_day_usd")} for e in entries]

    @staticmethod
    def entries_words(entries: Optional[List[Dict[str, Any]]]) -> str:
        """The signing entries in force, each with its two limits in dollars (per payment/per day), and how many more stand superseded or inactive."""
        if entries is None:
            return "not read"
        signing = [e for e in entries if "sign" in str(e.get("access") or "")]
        live = [e for e in signing if e.get("active", True) is not False and not str(e.get("supersededBy") or "")]
        words = ", ".join("%s %s/%s" % (e.get("name"), e.get("perPaymentUsd"), e.get("perDayUsd")) for e in live) or "no signing entry in force"
        return words + ((" (and %d not in force)" % (len(signing) - len(live))) if len(signing) > len(live) else "")

    def current_page(self, since: int) -> Optional[Dict[str, Any]]:
        """The wizard page the browser last received (the begin's page, an answer's, a question's, or the interview's), as the page received it."""
        for x in reversed(self.exchanges[since:]):
            path = x.path.split("?", 1)[0]
            if not x.ok or not isinstance(x.json, dict):
                continue
            if x.method == "POST" and path == S.INTERVIEWS_ROUTE and isinstance(x.json.get("page"), dict):
                return x.json["page"]
            if re.match(r"^/v1/onboarding/interviews/[^/]+(/answers|/questions/[^/]+|/reopen)?$", path) and "progress" in x.json:
                return x.json
        return None

    def book_value(self, served: Dict[str, Any]) -> Dict[str, Any]:
        """The book's answer for the served question (aer360_answers.answer_for, which refuses an unknown question), with the founder's own spellings typed in."""
        value = json.loads(json.dumps(A.answer_for("policy", served)))
        qid = str(served.get("questionId"))
        if qid == "A8":
            value["entries"] = [dict(e, email=self.typed_address(self.person_by_address(e.get("email")) or "")) if self.person_by_address(e.get("email")) else e
                                for e in value.get("entries") or []]
        elif qid == "C18":
            value["entries"] = [dict(e, email=self.typed_address(self.person_by_address(e.get("email")) or "")) if self.person_by_address(e.get("email")) else e
                                for e in value.get("entries") or []]
        elif qid == "C11":
            value["people"] = [self.typed_address(self.person_by_address(p) or "") if self.person_by_address(p) else p for p in value.get("people") or []]
        return value

    def answer_on_the_page(self, v: Visitor, q: Dict[str, Any], value: Dict[str, Any]) -> None:
        """One answer, through the page's own controls (Onboarding.tsx, per kind), as a person gives it."""
        kind = str(q.get("kind"))
        if kind == "statement":
            return
        if kind == "single_choice":
            v.choose(str(value["choice"]))
        elif kind == "multi_choice":
            for option in q.get("options") or []:
                v.tick(str(option), on=option in (value.get("choices") or []))
        elif kind == "text":
            v.fill(S.TEXT_ANSWER_LABEL, str(value.get("text") or ""))
        elif kind == "currency":
            v.select(S.CURRENCY_LABEL, str(value.get("text")))
        elif kind == "money":
            cents = value.get("cents")
            v.fill(S.MONEY_LABEL, "" if cents in (None, "") else cents_text(cents), exact=False)
        elif kind == "percent":
            percent = value.get("percent")
            v.fill(S.PERCENT_LABEL, "" if percent is None else str(percent), exact=False)
        elif kind in ("roster_single", "roster_multi"):
            v.fill(S.ROSTER_SINGLE_LABEL if kind == "roster_single" else S.ROSTER_MULTI_LABEL, ", ".join(value.get("people") or []))
        elif kind == "list":
            fields = q.get("listFields") or S.DEFAULT_LIST_FIELDS
            entries = list(value.get("entries") or [])
            first = fields[0]["label"] if fields else "Name"
            for index in range(len(entries)):
                if not v.has(S.list_field_label(first, index), role="textbox") and not v.page.get_by_label(S.list_field_label(first, index), exact=True).count():
                    v.press(S.ADD_ENTRY, why="a row for entry %d" % (index + 1))
            for index, entry in enumerate(entries):
                for field in fields:
                    label = S.list_field_label(str(field["label"]), index)
                    text = str(entry.get(field["key"], "") or "")
                    if field.get("kind") == "choice" and field.get("options"):
                        v.select(label, text)
                    else:
                        v.fill(label, text)
        elif kind == "person_or_none":
            v.choose(str(value["choice"]))
            options = q.get("options") or []
            if options and value["choice"] == options[0]:
                person = value.get("person") or {}
                for field in q.get("listFields") or S.DEFAULT_LIST_FIELDS:
                    v.fill(str(field["label"]), str(person.get(field["key"], "") or ""))
        elif kind == "count":
            count = value.get("count")
            v.fill(str(q.get("prompt")), "" if count is None else str(count))
        else:
            raise StationStop("the page serves question %s as %r, a kind this harness has no hand for" % (q.get("questionId"), kind))

    def press_next(self, v: Visitor) -> Optional[Exchange]:
        return v.press(S.NEXT_BUTTON, answer=("POST", r"^/v1/onboarding/interviews/[^/]+/answers$"), why="commit the answer")

    def station_r3(self) -> Outcome:
        v = self.founder()
        said: List[str] = []
        failures = 0
        # the entries BEFORE the write: the fixture of 9 October — born by the CLI road, never set by hand, so every signing entry stands at zero
        before_entries = self.read_entries("before the interview")
        self.facts["entries_before"] = before_entries
        v.goto(S.ONBOARDING_ROUTE)
        heading = v.heading()
        if heading != S.ONBOARDING_HEADING:
            raise StationStop("the Onboarding room did not open: its heading reads %r, not %r" % (heading, S.ONBOARDING_HEADING))
        if v.has(S.AMEND_THE_CHARTER_CONTROL, seconds=3.0):
            # a rerun on a charter an earlier run wrote: the entries carry what that write put on them, which read_the_charter_as_compiled reads
            standing_words = v.text_of(v.card(S.POLICY_CARD))
            self.next_step("the Onboarding room", standing_words)
            said.append("this estate's charter stands written (%s); the harness amends nothing a founder wrote, and reads what it compiled" % standing_words)
            return self.read_the_charter_as_compiled(v, said, failures, receipt=None)
        if before_entries is not None:
            ours = [e for e in before_entries if self.is_estate_own_entry(e)]
            standing = [e for e in ours if (e.get("perPaymentUsd") or 0) > 0 or (e.get("perDayUsd") or 0) > 0]
            said.append("the signing entries before the interview: %s" % self.entries_words(before_entries))
            if standing:
                failures += 1
                self.finding("a signing entry stood above zero before the interview", "%s stood at %s before the Policy Interview's write: set by a hand, not by the "
                             "compile (the fixture of 9 October is an estate whose entries were never set by hand)" % (
                                 ", ".join(str(e.get("name")) for e in standing), self.entries_words(standing)), SCREEN,
                             store=self.entries_words(before_entries), expected="aer-accounts and the author entry at zero until the write")
        since = len(self.exchanges)
        started = v.press(S.BEGIN_POLICY_INTERVIEW, answer=("POST", r"^/v1/onboarding/interviews$"), why="the Policy Interview")
        if started is None or not started.ok:
            raise StationStop("Begin the Policy Interview answered %s; the page says %s (%s)" % (
                started.sentence() if started else "nothing", json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False),
                kind_of(started.status, started.json) if started else UNREACHABLE))
        zero_tried = False
        answered: List[str] = []
        page: Optional[Dict[str, Any]] = None
        for _ in range(INTERVIEW_PAGES_AT_MOST):
            page = self.current_page(since)
            q = (page or {}).get("question")
            if not isinstance(q, dict):
                break
            qid = str(q.get("questionId"))
            prompt = " ".join(str(q.get("prompt") or "").split())
            v.poll(lambda: v.text_of(v.page.locator(S.CSS_LEGEND)) == prompt)  # the page renders the question after the browser has its answer
            legend = v.text_of(v.page.locator(S.CSS_LEGEND))
            if legend != prompt:
                failures += 1
                self.finding("the page's question is not the served question", "question %s: the page reads %r and the answer the browser received serves %r" % (
                    qid, legend, q.get("prompt")), SCREEN, page=legend, store=str(q.get("prompt")), expected="the same words")
            if qid in A.ADDED_IN_V15["policy"]:
                note = " ".join(str(q.get("note") or "").split())
                if note and note not in v.main_text():
                    failures += 1
                    self.finding("%s's note is not on the page" % qid, "the served note %r is not among the page's sentences" % note, SCREEN, expected="the note beside the question")
                elif not note or S.ZERO_REFUSED_WORDS not in note:
                    failures += 1
                    self.finding("%s's note does not say a zero is refused" % qid, "the note beside %s reads %r" % (qid, note), SCREEN,
                                 expected="the note says a zero is refused (Spec AER360-115 §3.4: %r)" % S.CHARTER_CEILINGS_REQUIRED)
                else:
                    said.append("%s's note: %r" % (qid, note))
            if qid == "C2" and not zero_tried:
                zero_tried = True
                v.fill(S.MONEY_LABEL, "0", exact=False)
                refused = self.press_next(v)
                v.poll(lambda: bool(v.refusals()))
                words = " | ".join(v.refusals())
                if refused is not None and refused.ok:
                    failures += 1
                    self.finding("a zero at C2 was accepted", "the page took a company ceiling of zero and moved on; the estate answered HTTP %d" % refused.status, SCREEN,
                                 page=words, expected="the page's refusal: %r" % S.CEILING_ZERO_REFUSED)
                    raise StationStop("a zero at C2 was accepted, so the interview stands on a zero ceiling; nothing more was answered")
                kind = kind_of(refused.status, refused.json) if refused else UNREACHABLE
                if S.CEILING_ZERO_REFUSED not in words:
                    failures += 1
                    self.finding("the zero's refusal is not the estate's sentence", "the page says %s" % json.dumps(words, ensure_ascii=False), SCREEN, page=words,
                                 store=refused.sentence() if refused else "", expected=S.CEILING_ZERO_REFUSED)
                said.append("a zero at C2 was refused at the page (%s, %s): %s" % (refused.sentence() if refused else "no answer", kind, json.dumps(words, ensure_ascii=False)))
                self.next_step("C2's refusal", words)
                page = self.current_page(since) or page
            value = self.book_value(q)
            self.answer_on_the_page(v, q, value)
            moved = self.press_next(v)
            if moved is None or not moved.ok:
                v.poll(lambda: bool(v.refusals()))
                words = " | ".join(v.refusals())
                raise StationStop("question %s (%s) was refused: the page says %s; the estate answered %s (%s)" % (
                    qid, q.get("kind"), json.dumps(words, ensure_ascii=False), moved.sentence() if moved else "nothing",
                    kind_of(moved.status, moved.json) if moved else UNREACHABLE))
            answered.append(qid)
        else:
            raise StationStop("the interview served more than %d pages; the harness stops rather than walk a loop (the last question: %s)" % (
                INTERVIEW_PAGES_AT_MOST, ((page or {}).get("question") or {}).get("questionId")))
        said.append("%d question(s) answered through the page (%s), the addresses typed as a client types them" % (len(answered), ", ".join(answered)))
        if A.ADDED_IN_V15["policy"][0] not in answered:
            failures += 1
            self.finding("the interview did not ask C2 and C3", "the walk served %s and neither of version 15's two ceilings" % ", ".join(answered), SCREEN,
                         expected="catalog version 15: C2 and C3 after C9 and before C10")
        # THE READ-BACK, as the page reads it, held against the read-back the browser received
        if not v.appears(v.page.get_by_role("heading", name=S.READ_BACK_HEADING, exact=True)):
            raise StationStop("the read-back did not appear after the last question; the page reads %r" % v.heading())
        v.appears(v.page.locator(S.CSS_READ_BACK_LINE))  # the lines arrive on the read-back's own request, after its heading
        lines = self.read_back_lines(v)
        received = self.answered("GET", r"^/v1/onboarding/interviews/[^/]+/readback$", v.name, since)
        served = [l for l in (((received.json or {}).get("lines") or []) if received and isinstance(received.json, dict) else []) if isinstance(l, dict)]
        for line in served:
            shown = next((l for l in lines if l[0] == " ".join(str(line.get("prompt") or "").split())), None)
            if shown is None or shown[1] != " ".join(str(line.get("spoken") or "").split()):
                failures += 1
                self.finding("a read-back line on the page is not the served line", "%s: the page reads %r; the browser received %r" % (
                    line.get("questionId"), shown[1] if shown else None, line.get("spoken")), SCREEN, page=json.dumps(shown, ensure_ascii=False) if shown else "",
                    store=json.dumps(line, ensure_ascii=False), expected="the same sentence")
        amending = False
        for which, (line_id, prompt) in E.CEILING_READBACK_LINES.items():
            cents = A.MONEY["company_ceiling_cents"] if which == "perPayment" else A.MONEY["daily_total_cents"]
            partner = A.MONEY["daily_total_cents"] if which == "perPayment" else A.MONEY["company_ceiling_cents"]
            expected = E.ceiling_read_back_sentence(which, cents, partner, amending)
            shown = next((l for l in lines if l[0] == prompt), None)
            if shown is None or shown[1] != expected:
                failures += 1
                self.finding("the read-back's %s line" % line_id, "the page reads %r beside %r" % (shown[1] if shown else None, prompt), SCREEN,
                             page=json.dumps(shown, ensure_ascii=False) if shown else "", expected=expected)
            else:
                said.append("the read-back says %r: %r" % (prompt, shown[1]))
        self.next_step("the read-back", S.CONFIRM_CHARTER)
        compiled = v.press(S.CONFIRM_CHARTER, answer=("POST", r"^/v1/onboarding/interviews/[^/]+/compile$"), why="author the charter under the passkey", seconds=180.0)
        self.save_credential(v)
        if compiled is None:
            raise StationStop("the confirm was pressed and no compile answered; the page says %s" % json.dumps(" | ".join(v.refusals()) or v.heading(), ensure_ascii=False))
        if not compiled.ok or not isinstance(compiled.json, dict):
            raise StationStop("the charter was not written: the page says %s; the compile answered %s (%s)" % (
                json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False), compiled.sentence(), kind_of(compiled.status, compiled.json)))
        if compiled.json.get("state") == S.INTERVIEW_AWAITING_APPROVALS:
            raise StationStop("the Policy Interview's write waits for approvals (%s); the book's charter finishes on the founder's press" % json.dumps(
                compiled.json.get("ceremonies"), ensure_ascii=False)[:300])
        v.appears(v.page.get_by_role("heading", name=S.CHARTER_WRITTEN_HEADING, exact=True), 60.0)
        result = v.text_of(v.card(S.CHARTER_WRITTEN_HEADING)) or v.main_text()
        self.step("page", v.name, "the written charter", page=result)
        self.next_step("the written charter", result)
        said.append("written: %s" % json.dumps(result[:300], ensure_ascii=False))
        receipt = compiled.json.get("receipt") if isinstance(compiled.json.get("receipt"), dict) else {}
        return self.read_the_charter_as_compiled(v, said, failures, receipt=receipt)

    @staticmethod
    def is_estate_own_entry(entry: Dict[str, Any]) -> bool:
        """
        The estate's own signing entries, by its own rule (services/charterceilings.ts:97-108, isSigningEntryInForce and isEstateOwnSigningEntry):
        in force — active and superseded by nothing (the platform lists a superseded version beside its successor) — signing, and named
        `aer-accounts` or "<name> (author)".
        """
        name = str(entry.get("name") or "")
        in_force = entry.get("active", True) is not False and not str(entry.get("supersededBy") or "")
        return in_force and "sign" in str(entry.get("access") or "sign") and (name == S.ESTATE_ENTRY or name.endswith(S.AUTHOR_ENTRY_SUFFIX))

    def read_back_lines(self, v: Visitor) -> List[Tuple[str, str]]:
        """The read-back's lines as the page shows them: each prompt (dt) with the sentence beneath it (the first dd)."""
        out: List[Tuple[str, str]] = []
        for item in v.page.locator(S.CSS_READ_BACK_LINE).all():
            prompt = " ".join(item.locator("dt").first.inner_text().split())
            spoken = " ".join(item.locator("dd").first.inner_text().split())
            out.append((prompt, spoken))
        return out

    def read_the_charter_as_compiled(self, v: Visitor, said: List[str], failures: int, receipt: Optional[Dict[str, Any]]) -> Outcome:
        """
        After the write: the receipt's ceilings (the entries the write found at zero and filled, in whole dollars), the entries read again on
        the platform's read road, the roster the People page shows, and the seat view (GET /v1/approver-seats) — every address folded, every
        name as typed (Spec AER360-SEAT-CASE).
        """
        ceilings = (receipt or {}).get("ceilings") if isinstance((receipt or {}).get("ceilings"), dict) else None
        self.facts["receipt_ceilings"] = ceilings
        want_tx = int(A.MONEY["company_ceiling_cents"]) // 100
        want_day = int(A.MONEY["daily_total_cents"]) // 100
        if receipt is not None:
            if ceilings is None:
                failures += 1
                self.finding("the write's receipt names no ceilings", "the compile's receipt carries no `ceilings` (Spec AER360-115)", SCREEN,
                             store=json.dumps(receipt, ensure_ascii=False)[:400], expected="perPaymentUsd %d, perDayUsd %d, the entries written" % (want_tx, want_day))
            else:
                names = [str(e.get("name")) for e in (ceilings.get("entries") or []) if isinstance(e, dict)]
                ok = ceilings.get("perPaymentUsd") == want_tx and ceilings.get("perDayUsd") == want_day and S.ESTATE_ENTRY in names and any(
                    n.endswith(S.AUTHOR_ENTRY_SUFFIX) for n in names)
                words = "the write's receipt: US$%s per payment and US$%s per day written onto %s%s" % (
                    ceilings.get("perPaymentUsd"), ceilings.get("perDayUsd"), ", ".join(names) or "no entry",
                    ("; unwritten: %s" % "; ".join(ceilings.get("unwritten") or [])) if ceilings.get("unwritten") else "")
                said.append(words)
                if not ok:
                    failures += 1
                    self.finding("the write did not put the charter's ceilings on the estate's own entries", words, SCREEN, store=json.dumps(ceilings, ensure_ascii=False),
                                 expected="US$%d and US$%d onto %s and the founder's (author) entry, each found at zero (written by the compile and by no hand)" % (
                                     want_tx, want_day, S.ESTATE_ENTRY))
        after = self.read_entries("after the write")
        self.facts["entries_after"] = after
        if after is not None:
            ours = [e for e in after if self.is_estate_own_entry(e)]
            said.append("the signing entries after the write: %s" % self.entries_words(after))
            wrong = [e for e in ours if e.get("perPaymentUsd") != want_tx or e.get("perDayUsd") != want_day]
            if wrong:
                failures += 1
                self.finding("an estate entry does not carry the charter's two figures", self.entries_words(wrong), SCREEN, store=self.entries_words(after),
                             expected="%s and the (author) entries at %d per payment and %d per day, in dollars" % (S.ESTATE_ENTRY, want_tx, want_day))
        # the compiled roster, as the People page shows it, and the seat view the platform's roster is read through
        v.goto(S.PEOPLE_ROUTE)
        seats_card = v.card(S.APPROVER_SEATS_CARD)
        shown = v.text_of(seats_card)
        self.step("page", v.name, "the compiled roster on the People page", page=shown)
        seats = v.read(S.APPROVER_SEATS_ROUTE, "the approver seats the charter compiled: each seat's address in the folded form, each name as the founder typed it")
        rows = [s for s in (((seats.json or {}).get("seats") or []) if seats.ok and isinstance(seats.json, dict) else []) if isinstance(s, dict)]
        named = 0
        for key in A.CENSUS_ORDER:
            typed = self.typed_address(key)
            seat = next((s for s in rows if fold(s.get("email")) == fold(typed)), None)
            if seat is None:
                continue
            named += 1
            if fold(seat.get("email")) != fold(typed) or (seat.get("name") and seat.get("name") != A.PEOPLE[key].name):
                failures += 1
                self.finding("a seat is not the person the founder typed", "the seat for %s reads %r, %r; the founder typed %s and %r" % (
                    A.PEOPLE[key].name, seat.get("name"), seat.get("email"), json.dumps(typed), A.PEOPLE[key].name), SCREEN,
                    store=json.dumps(seat, ensure_ascii=False), expected="an address folding to %s, and the name %r as typed" % (fold(typed), A.PEOPLE[key].name))
            if fold(typed) not in shown.lower():
                failures += 1
                self.finding("the People page does not show a compiled seat", "%s's seat (%s) is in the seat view and not on the page" % (A.PEOPLE[key].name, fold(typed)),
                             SCREEN, page=shown[:400], expected="every seat on the page")
        said.append("the compiled roster on the People page: %d seat(s) — the approvers C11 names — each the person the founder typed, named as typed%s; the platform's "
                    "roster carries each address folded (the compile's user_id, Spec AER360-SEAT-CASE) and is listed on no road this harness reads — R6's counted "
                    "presses are where the platform is seen to find each seat" % (named, "" if seats.ok else " (the seat view answered %s)" % seats.sentence()))
        if not seats.ok:
            failures += 1
        charter = v.read(S.CHARTER_ROUTE, "the charter stands written")
        if not (charter.ok and isinstance(charter.json, dict) and charter.json.get("standsWritten") is True):
            failures += 1
            self.finding("the charter does not stand written", "GET %s answered %s" % (S.CHARTER_ROUTE, charter.text[:300]), SCREEN, expected="standsWritten true")
        return Outcome("R3", FAIL if failures else PASS, "; ".join(said))

    # ======================================================================================================================
    # R4 — People: the approvers invited from the screen, each redeeming in their own context.
    # ======================================================================================================================
    @staticmethod
    def payment_approvers() -> List[str]:
        """The people the book names at C11 (the approvers of payments): the charter seats them, each with a row on the Approver seats panel."""
        return [k for k in (RealWorld.person_by_address(p) for p in (A.POLICY_ANSWERS["C11"].get("people") or [])) if k]

    def seat_row(self, v: Visitor, key: str) -> Any:
        return v.card(S.APPROVER_SEATS_CARD).get_by_role("row").filter(has_text=self.address_of(key))

    def seat_state(self, v: Visitor, key: str) -> str:
        return v.text_of(self.seat_row(v, key))

    def register_rows(self, v: Visitor, key: str, state: Optional[str] = None) -> Any:
        """The person's rows on the Invitations register, by the name the founder typed — those in one state, where it is named."""
        rows = v.card(S.INVITATIONS_CARD).get_by_role("row").filter(has_text=A.PEOPLE[key].name)
        return rows.filter(has_text=S.REGISTER_WORDS[state]) if state else rows

    def invite_from_the_seat(self, v: Visitor, key: str) -> Optional[str]:
        """
        The founder's road for an approver the charter seats (People.tsx's Approver seats panel): an invitation an earlier run minted, whose link
        this run never held, withdrawn first; then the seat's own Invite, which fills the form. None where the panel shows no row for them.
        """
        name = A.PEOPLE[key].name
        row = self.seat_row(v, key)
        state = self.seat_state(v, key)
        if not state:
            return None
        if S.SEAT_WORDS["invited"] in state:
            v.press(S.SEAT_WITHDRAW, within=row, answer=("POST", r"^/v1/invites/[^/]+/revoke$"),
                    why="an earlier run's invitation to %s, whose link this run does not hold" % name)
            self.next_step("the Approver seats panel", " | ".join(v.texts("status", within=v.card(S.APPROVER_SEATS_CARD))))
        v.press(S.SEAT_INVITE, within=self.seat_row(v, key), why="the seat's own road to an invitation for %s" % name)
        form = v.card(S.INVITE_CARD)
        if not v.value_of(S.INVITE_NAME_LABEL, within=form).strip():
            # the seat names the person by the address C11 was answered with (the compiler's roster is C11's addresses; parseRoster gives no name),
            # so its Invite fills the address alone and the form will not submit without a name: the founder types it, as the page leaves her to
            self.note("the seat's Invite filled the address and left %r empty (the charter's C11 seat carries no name), so the founder typed %r" % (
                S.INVITE_NAME_LABEL, name))
            v.fill(S.INVITE_NAME_LABEL, name, within=form)
        return self.mint_from_the_form(v, key, "the seat's Invite")

    def invite_from_the_form(self, v: Visitor, key: str) -> str:
        """
        The founder's road for a person the charter names at A8 and not at C11 (Ben Signatory approves changes, not payments): no seat row, so the
        form, typed — an earlier run's pending invitation withdrawn first on the register, as its row asks.
        """
        name = A.PEOPLE[key].name
        pending = self.register_rows(v, key, "pending")
        if pending.count():
            row = pending.first
            v.press(S.withdraw_from_register_label(name), within=row, why="an earlier run's invitation to %s, whose link this run does not hold" % name)
            v.press(S.confirm_withdraw_label(name), within=self.register_rows(v, key, "pending").first, answer=("POST", r"^/v1/invites/[^/]+/revoke$"),
                    why="the register's second question, answered")
        form = v.card(S.INVITE_CARD)
        v.fill(S.INVITE_NAME_LABEL, name, within=form)
        v.fill(S.INVITE_EMAIL_LABEL, self.typed_address(key), within=form)
        return self.mint_from_the_form(v, key, "the form, typed")

    def mint_from_the_form(self, v: Visitor, key: str, road: str) -> str:
        """The form completed as the page asks (People.tsx): the Executive standing, the pen accepted, Invite, the link shown once and hidden."""
        name = A.PEOPLE[key].name
        form = v.card(S.INVITE_CARD)
        v.choose(S.EXECUTIVE_STANDING, within=form) if v.has(S.EXECUTIVE_STANDING, role="radio", within=form) else v.choose(S.LEVEL_ONE_EXECUTIVE, within=form)
        v.tick(S.PEN_LABEL_WORDS, within=form, exact=False)
        typed_name = v.value_of(S.INVITE_NAME_LABEL, within=form)
        typed_email = v.value_of(S.INVITE_EMAIL_LABEL, within=form)
        minted = v.press(S.INVITE_SUBMIT, within=form, answer=("POST", r"^/v1/invites$"), why="the invitation, and its link shown once")
        if minted is None or not minted.ok:
            raise StationStop("the invitation for %s was refused: the page says %s; the estate answered %s (%s)" % (
                name, json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False), minted.sentence() if minted else "nothing",
                kind_of(minted.status, minted.json) if minted else UNREACHABLE))
        link = v.value_of(S.INVITE_LINK_LABEL)  # waited for: the receipt renders once the page has the minted answer
        if not link:
            raise StationStop("the invitation for %s was minted and the page shows no link in %r" % (name, S.INVITE_LINK_LABEL))
        receipt_heading = v.text_of(v.page.get_by_role("heading", name=re.compile(re.escape(S.INVITED_HEADING_WORDS))))
        self.secrets.add(E.token_of_link(link))
        receipt = v.page.locator(S.CSS_CARD).filter(has=v.page.get_by_role("heading", name=receipt_heading, exact=True))
        self.step("page", v.name, "the invitation receipt, by %s" % road, page=self.secrets.redact_text(v.text_of(receipt)))
        self.next_step("the invitation receipt", "%s — %s" % (receipt_heading, S.HIDE_THE_LINK))
        v.press(S.HIDE_THE_LINK, why="the link handed over (to %s's own browser)" % name)
        if typed_name != name or fold(typed_email) != self.address_of(key):
            self.note("%s filled %r and %r for %s, and the book's are %r and %s" % (road, typed_name, typed_email, name, name, self.address_of(key)))
        return link

    def station_r4(self) -> Outcome:
        v = self.founder()
        said: List[str] = []
        failures = 0
        seated_by_charter = self.payment_approvers()
        for key in S.APPROVERS:
            name = A.PEOPLE[key].name
            a = self.visitors.get(key)
            if a is not None and not a.closed and a.session is not None:
                said.append("%s is enrolled and signed in (the credential stored at %s)" % (name, self.credential_path(key)))
                continue
            if self.stored_for_this_estate(key) is not None:
                try:
                    self.sign_in(self.visitor(key))
                    said.append("%s signed in with the credential stored at %s" % (name, self.credential_path(key)))
                    continue
                except StationStop as err:
                    self.note("%s's stored credential did not sign in (%s), so the founder invites them again" % (name, err))
            v.goto(S.PEOPLE_ROUTE)
            link = None
            if key in seated_by_charter:
                link = self.invite_from_the_seat(v, key)
                if link is None:
                    failures += 1
                    self.finding("no approver seat for %s" % name, "the People page's Approver seats list no row for %s (%s), whom the charter names at C11" % (
                        name, self.address_of(key)), SCREEN, page=v.text_of(v.card(S.APPROVER_SEATS_CARD))[:400], expected="a seat for every approver C11 names")
            if link is None:
                link = self.invite_from_the_form(v, key)
            welcome = self.enrol(self.visitor(key, fresh=True, bare=True), link)
            said.append("%s invited from %s and enrolled in a context of their own: %s" % (
                name, "the seat" if key in seated_by_charter else "the form", json.dumps(welcome, ensure_ascii=False)))
        v.goto(S.PEOPLE_ROUTE)
        seats = v.read(S.APPROVER_SEATS_ROUTE, "the seat of each approver the charter names at C11: seated, on the platform's roster")
        register = v.read(S.INVITES_ROUTE, "each approver's invitation: redeemed, at the address the founder typed")
        seat_rows = [s for s in (((seats.json or {}).get("seats") or []) if seats.ok and isinstance(seats.json, dict) else []) if isinstance(s, dict)]
        invites = [r for r in (((register.json or {}).get("invites") or []) if register.ok and isinstance(register.json, dict) else []) if isinstance(r, dict)]
        for key in S.APPROVERS:
            name = A.PEOPLE[key].name
            if key in seated_by_charter:
                shown = self.seat_state(v, key)
                seat = next((s for s in seat_rows if fold(s.get("email")) == self.address_of(key)), None)
                if S.SEAT_WORDS["seated"] not in shown:
                    failures += 1
                    self.finding("%s is not seated on the page" % name, "the seat row reads %r" % shown, SCREEN, page=shown,
                                 store=json.dumps(seat, ensure_ascii=False) if seat else "no seat", expected=S.SEAT_WORDS["seated"])
                elif seat is None or seat.get("state") != "seated" or seat.get("onRoster") is False:
                    failures += 1
                    self.finding("%s's seat on the page and in the store disagree" % name, "the page reads %r and the seat view %s" % (shown, json.dumps(seat, ensure_ascii=False)),
                                 SCREEN, page=shown, store=json.dumps(seat, ensure_ascii=False), expected="seated, on the roster")
                else:
                    said.append("%s: %r on the page; the seat view reads %s%s" % (name, S.SEAT_WORDS["seated"], seat.get("state"),
                                                                                "" if seat.get("onRoster") is None else ", on the roster" if seat.get("onRoster") else ""))
                continue
            # an approver of changes: no seat; the register's redeemed row, at the address typed, and an author's standing to press Approve in R6
            shown = v.text_of(self.register_rows(v, key, "redeemed"))
            row = next((r for r in invites if r.get("state") == "redeemed" and fold(r.get("email")) == self.address_of(key)), None)
            person = self.visitors.get(key)
            roles = list(((person.session or {}) if person is not None else {}).get("roles") or [])
            if not shown or row is None:
                failures += 1
                self.finding("%s's invitation is not redeemed" % name, "the register's row on the page reads %r; the store's %s" % (
                    shown or "nothing", json.dumps(row, ensure_ascii=False) if row else "has no redeemed row at %s" % self.address_of(key)), SCREEN,
                    page=shown, store=json.dumps(row, ensure_ascii=False) if row else "", expected="%s, at %s" % (S.REGISTER_WORDS["redeemed"], self.address_of(key)))
            elif "author" not in roles:
                failures += 1
                self.finding("%s holds no author standing" % name, "%s's session reads roles %s, so the Approve on a payee row will not take their press" % (
                    name, ", ".join(roles) or "none"), SCREEN, store=json.dumps(row, ensure_ascii=False), expected="author (an Executive)")
            else:
                said.append("%s: %r on the register at %s (an approver of changes, so no seat), standing %s" % (
                    name, S.REGISTER_WORDS["redeemed"], row.get("email"), ", ".join(roles)))
        self.next_step("the People page", " | ".join(self.seat_state(v, k) for k in S.APPROVERS if k in seated_by_charter))
        ben = A.PEOPLE[T.REAL_WORLD_NAME_NOT_ADDRESS]
        said.append("%s's display name is not his address (%s), and he is found by the address" % (ben.name, self.address_of(ben.key)))
        return Outcome("R4", FAIL if failures else PASS, "; ".join(said))

    # ======================================================================================================================
    # R5 — The wallet: Create a new wallet, as the Wallets room offers it.
    # ======================================================================================================================
    def station_r5(self) -> Outcome:
        v = self.founder()
        said: List[str] = []
        failures = 0
        v.goto(S.WALLETS_ROUTE)
        if v.heading() != S.WALLETS_HEADING:
            raise StationStop("the Wallets room did not open: its heading reads %r" % v.heading())
        if v.has(S.GIVE_FUNDING_WALLET, seconds=3.0):
            # a fresh estate: the page offers its funding wallet first, and the new-wallet press only once one stands (Wallets.tsx)
            absence = v.text_of(v.card(S.FUNDING_WALLET_CARD))
            given = v.press(S.GIVE_FUNDING_WALLET, answer=("POST", r"^/v1/workspace/funding-wallet$"), why="the page offers it before any new wallet", seconds=180.0)
            self.save_credential(v)
            if given is None or not given.ok:
                raise StationStop("Give this estate its funding wallet was refused: the page says %s; the estate answered %s (%s)" % (
                    json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False), given.sentence() if given else "nothing",
                    kind_of(given.status, given.json) if given else UNREACHABLE))
            said.append("the page first offered %r (%s) and it was pressed" % (S.GIVE_FUNDING_WALLET, json.dumps(absence, ensure_ascii=False)))
            v.goto(S.WALLETS_ROUTE)
        funding = " | ".join(v.texts("note", name=S.FUNDING_WALLET_NOTE) + v.texts("note", name=S.FUND_THIS_ACCOUNT_NOTE))
        if funding:
            said.append("the funding wallet: %s" % json.dumps(funding, ensure_ascii=False))
        known = self.state.get("wallet") if isinstance(self.state.get("wallet"), dict) else None
        register = v.read(S.WALLETS_REGISTER_ROUTE, "the wallet register: the wallet this leg made, keyed, with its address")
        rows = self.register_wallets(register)
        mine = next((w for w in rows if known and w.get("walletId") == known.get("walletId")), None)
        if mine is not None:
            said.append("the wallet this leg made on %s stands: wallet %s at %s" % (known.get("bornAt"), mine.get("walletNumber"), mine.get("address")))
        else:
            card = v.card(S.NEW_WALLET_CARD)
            if not v.has(S.CREATE_NEW_WALLET, within=card, seconds=10.0):
                raise StationStop("the Wallets room offers no %r; the page says %s" % (S.CREATE_NEW_WALLET, json.dumps(v.main_text()[:400], ensure_ascii=False)))
            v.press(S.CREATE_NEW_WALLET, within=card, why="the room's own press for a wallet")
            v.must_appear(card.locator(S.CSS_LEGEND), "the press's question")
            questions = [" ".join(t.split()) for t in card.locator(S.CSS_LEGEND).all_inner_texts()]
            self.next_step("the A new wallet card", " | ".join(questions))
            v.choose(S.THIS_ESTATE, within=card)
            before_born = " | ".join(v.texts("note", within=card, name=S.BEFORE_WALLET_BORN_NOTE))
            since = len(self.exchanges)
            v.press(S.CREATE_IT, within=card, answer=("POST", r"^/v1/workspace/wallets(/options)?$"), why="the wallet, under the passkey", seconds=180.0)
            self.save_credential(v)  # the ceremony moved the counter: saved before anything that could stop the station
            born_words = v.page.get_by_role("status").filter(has_text=re.compile(r"^Wallet \S+ is born"))
            if not v.appears(born_words, 180.0):
                x = self.answered("POST", r"^/v1/workspace/wallets$", v.name, since) or self.answered("POST", r"^/v1/workspace/wallets/options$", v.name, since)
                raise StationStop("the wallet was not born: the page says %s; the estate answered %s (%s)" % (
                    json.dumps(" | ".join(v.refusals(within=card)) or "nothing", ensure_ascii=False), x.sentence() if x else "nothing",
                    kind_of(x.status, x.json) if x else UNREACHABLE))
            self.save_credential(v)
            status = v.text_of(born_words)
            found = re.match(r"^Wallet (\S+) is born(?:: (0x[0-9a-fA-F]{40}))?\.", status)
            answer = self.answered("POST", r"^/v1/workspace/wallets$", v.name, since) or self.answered("POST", r"^/v1/workspace/wallets/options$", v.name, since)
            wallet = (answer.json or {}).get("wallet") if answer and isinstance(answer.json, dict) else None
            self.state["wallet"] = {"walletId": (wallet or {}).get("walletId"), "walletNumber": found.group(1) if found else (wallet or {}).get("walletNumber"),
                                    "address": (found.group(2) if found and found.group(2) else (wallet or {}).get("address")), "bornAt": now_iso()}
            known = self.state["wallet"]
            said.append("the press asked %s and no limit; %s; the page says %s" % (
                " and ".join(json.dumps(q, ensure_ascii=False) for q in questions) or "nothing", json.dumps(before_born, ensure_ascii=False), json.dumps(status, ensure_ascii=False)))
            self.next_step("the Wallets room", status)
            register = v.read(S.WALLETS_REGISTER_ROUTE, "the wallet register: the wallet just born, keyed, with its address")
            rows = self.register_wallets(register)
            mine = next((w for w in rows if w.get("walletId") == known.get("walletId") or (known.get("address") and fold(w.get("address")) == fold(known.get("address")))), None)
        self.facts["wallet"] = known
        if mine is None:
            failures += 1
            self.finding("the register does not list the new wallet", "the page said it was born and the wallet register lists no such row", SCREEN,
                         store=register.text[:400], expected="the wallet row, keyed, with its address")
        else:
            if known is not None:
                known.update({k: mine.get(k) for k in ("walletId", "walletNumber", "address", "name") if mine.get(k)})
                self.state["wallet"] = known
            if mine.get("keyed") is not True:
                failures += 1
                self.finding("the new wallet is not keyed", "the register's row reads keyed %r, so no payment may leave it (Spec 110 item 4)" % mine.get("keyed"), SCREEN,
                             store=json.dumps(mine, ensure_ascii=False))
            fund = " | ".join(v.texts("note", name=S.fund_wallet_note(str(mine.get("walletNumber")))))
            if fund:
                self.next_step("the new wallet's card", fund)
            card = v.page.locator(S.CSS_CARD).filter(has_text=str(mine.get("walletNumber")))
            if v.has(S.PAY_FROM_THIS_WALLET, role="link", within=card.filter(has=v.page.get_by_role("link", name=S.PAY_FROM_THIS_WALLET))):
                self.next_step("the new wallet's card", S.PAY_FROM_THIS_WALLET)
            said.append("the register: wallet %s, %s, keyed %s, on %s" % (mine.get("walletNumber"), mine.get("address"), mine.get("keyed"), ", ".join(mine.get("chains") or []) or "no chain yet"))
        plan = v.read(S.PLAN_ROUTE, "the signing group the platform holds for this estate's account: group-100 and nothing else")
        group = (plan.json or {}).get("signingGroup") if plan.ok and isinstance(plan.json, dict) else None
        assigned = list((group or {}).get("assigned") or [])
        if assigned != [S.PRODUCTION_GROUP]:
            failures += 1
            self.finding("the estate's account is not on Group 100 alone", "the platform answers %s (%s)" % (
                json.dumps(assigned), (group or {}).get("sentence") or plan.sentence()), SCREEN, store=plan.text[:400], expected='["%s"]' % S.PRODUCTION_GROUP)
        else:
            said.append("the account stands on %s: %s" % (S.PRODUCTION_GROUP, (group or {}).get("sentence")))
        return Outcome("R5", FAIL if failures else PASS, "; ".join(said))

    @staticmethod
    def register_wallets(read: StoreRead) -> List[Dict[str, Any]]:
        body = read.json if read.ok and isinstance(read.json, dict) else {}
        register = body.get("register") if isinstance(body.get("register"), dict) else {}
        return [w for w in (register.get("wallets") or []) if isinstance(w, dict)]

    # ======================================================================================================================
    # R6 — Payees: the owner's wallet added from the screen, approved by two approvers in their own contexts.
    # ======================================================================================================================
    def require_owner_payee(self) -> str:
        owner, problem = self.owner_payee()
        if owner is None:
            raise StationStop("%s — the file %s" % (T.NO_OWNER_PAYEE_SENTENCE % T.PAYEE_CHAIN, problem), prerequisite=OWNER_PAYEE_NOT_FILED)
        self.facts["owner_payee"] = owner
        return owner

    def approvers(self) -> List[Visitor]:
        out: List[Visitor] = []
        for key in S.APPROVERS:
            v = self.visitors.get(key)
            if v is None or v.closed or v.session is None:
                raise StationStop("%s has no session in this run: R4 seats the approvers, and a resumed run signs them in with their stored credentials" % A.PEOPLE[key].name,
                                  prerequisite=NO_APPROVER_SESSION)
            out.append(v)
        return out

    def payee_row(self, v: Visitor, name: str, status_word: Optional[str] = None) -> Any:
        rows = v.card(S.PAYEES_CARD).get_by_role("row").filter(has_text=name).filter(has_text=T.PAYEE_CHAIN)
        return rows.filter(has_text=status_word) if status_word else rows

    def add_the_payee(self, v: Visitor, index: int, name: str, owner: str, said: List[str]) -> int:
        """
        Add a payee as the founder does (PayeeRegistry.tsx): the name, the chain, the owner's wallet — the second typed with a trailing space.
        Answers the failures it found (an address stored as typed).
        """
        typed = owner + (" " if index == T.REAL_WORLD_TRAILING_SPACE_PAYEE else "")
        card = v.card(S.ADD_PAYEE_CARD)
        v.fill(S.PAYEE_NAME_LABEL, name, within=card)
        v.fill(S.PAYEE_CHAIN_LABEL, T.PAYEE_CHAIN, within=card)
        v.fill(S.PAYEE_ADDRESS_LABEL, typed, within=card)
        # Add payee sends POST /v1/payees once the page's own check of the address passes, and nothing where it refuses: the answer is waited
        # for, and only a refusal the page shows — nothing sent, for certain — is answered by typing the address again; never a second press blind
        created = v.press(S.ADD_PAYEE, within=card, answer=("POST", r"^/v1/payees$"), answer_optional=True, why="the payee, at the owner's wallet")
        if created is None:
            words = " | ".join(v.refusals(within=card))
            if typed != owner and words:
                said.append("the page refused the address typed with a trailing space before anything was sent: %s — retyped as the page asks" % json.dumps(words, ensure_ascii=False))
                self.next_step("the Add payee card", words)
                v.fill(S.PAYEE_ADDRESS_LABEL, owner, within=card)
                created = v.press(S.ADD_PAYEE, within=card, answer=("POST", r"^/v1/payees$"), answer_optional=True, why="the payee, the address retyped")
            if created is None:
                raise StationStop("Add payee sent nothing for %s within %d s: the page says %s" % (name, int(ACTION_TIMEOUT_SECONDS), json.dumps(
                    " | ".join(v.refusals(within=card)) or "nothing", ensure_ascii=False)))
        if not created.ok or not isinstance(created.json, dict):
            raise StationStop("%s was not added: the page says %s; the estate answered %s (%s)" % (
                name, json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False), created.sentence(), kind_of(created.status, created.json)))
        row_json = created.json.get("payee") if isinstance(created.json.get("payee"), dict) else {}
        addresses = [a for a in (row_json.get("addresses") or []) if isinstance(a, dict)]
        stored = str(addresses[0].get("address")) if addresses else ""
        if typed == owner:
            return 0
        if fold(stored) == fold(owner):
            said.append("%s's address was typed with a trailing space and the estate stored %s" % (name, stored))
            return 0
        self.finding("an address typed with a trailing space was stored as typed", "%s's address was stored as %r" % (name, stored), SCREEN,
                     store=json.dumps(addresses, ensure_ascii=False), expected="the address without the space (%s)" % owner)
        return 1

    def send_for_approval(self, v: Visitor, name: str) -> None:
        """The payee's own Send for approval, and its row read once it says Pending promotion."""
        row = self.payee_row(v, name, S.STATUS_WORDS["proposed"])
        sent = v.press(S.SEND_FOR_APPROVAL, within=row, answer=("POST", r"^/v1/payees/addresses/[^/]+/promote$"), why="the address to its approvers")
        if sent is None or not sent.ok:
            v.poll(lambda: bool(v.refusals()))
            raise StationStop("%s was not sent for approval: the page says %s; the estate answered %s (%s)" % (
                name, json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False), sent.sentence() if sent else "nothing",
                kind_of(sent.status, sent.json) if sent else UNREACHABLE))
        v.poll(lambda: S.STATUS_WORDS["pending_promotion"] in v.text_of(self.payee_row(v, name)))

    def station_r6(self) -> Outcome:
        v = self.founder()
        owner = self.require_owner_payee()
        approvers = self.approvers()
        said: List[str] = ["the owner's wallet %s (read from %s; Spec T24)" % (owner, self.payee_env_path)]
        failures = 0
        for index, payee in enumerate(T.PAYEES):
            name = payee["name"]
            register = v.read(S.PAYEES_ROUTE_API, "the payee register before %s is added" % name)
            standing = self.payee_record(register, name, owner)
            if standing and standing.get("whitelistStatus") == "whitelisted":
                v.goto(S.PAYEES_ROUTE)
                shown = v.text_of(self.payee_row(v, name, S.STATUS_WORDS["whitelisted"]))
                self.next_step("the Payees room", shown)
                said.append("%s stands whitelisted at the owner's wallet on %s (an earlier run's); its row reads %s" % (name, T.PAYEE_CHAIN, json.dumps(shown, ensure_ascii=False)))
                self.facts["payees"].append({"name": name, "addressId": standing.get("id"), "status": "whitelisted"})
                if not shown:
                    failures += 1
                    self.finding("%s is whitelisted in the store and not on the page" % name, "the Payees room shows no %s row for %s on %s" % (
                        S.STATUS_WORDS["whitelisted"], name, T.PAYEE_CHAIN), SCREEN, store=json.dumps(standing, ensure_ascii=False), expected="the row, Whitelisted")
                continue
            v.goto(S.PAYEES_ROUTE)
            status = (standing or {}).get("whitelistStatus")
            if status in ("proposed", "pending_promotion"):
                # an earlier attempt's payee at the owner's wallet: taken on from where it stands, as a founder would, and never added a second time
                said.append("%s stands %s at the owner's wallet (an earlier attempt's), taken on from there and not added again" % (name, status))
                self.next_step("the Payees room", v.text_of(self.payee_row(v, name)))
            else:
                failures += self.add_the_payee(v, index, name, owner, said)
            if status != "pending_promotion":
                self.send_for_approval(v, name)
            words = [" | ".join(v.texts("status", within=self.payee_row(v, name)))]
            for a in approvers:
                a.goto(S.PAYEES_ROUTE)
                arow = self.payee_row(a, name, S.STATUS_WORDS["pending_promotion"])
                if not arow.count():
                    break
                pressed = a.press(S.APPROVE, within=arow, answer=("POST", r"^/v1/payees/addresses/[^/]+/approve$"), why="their own signature on the address")
                self.save_credential(a)
                # the row as the approver now reads it — its status, and the sentence the press left in it (one of two; then Whitelisted) — and any
                # refusal: read once the page shows what the answer said
                if pressed is not None and pressed.ok and isinstance(pressed.json, dict):
                    shows = (S.STATUS_WORDS["whitelisted"] if pressed.json.get("whitelistStatus") == "whitelisted"
                             else " ".join(str(pressed.json.get("sentence") or S.STATUS_WORDS["pending_promotion"]).split()))
                    a.poll(lambda: shows in a.text_of(self.payee_row(a, name)))
                else:
                    a.poll(lambda: bool(a.refusals()))
                page_words = " | ".join(t for t in [a.text_of(self.payee_row(a, name))] + a.refusals() if t)
                if pressed is None or not pressed.ok or not isinstance(pressed.json, dict):
                    failures += 1
                    detail = ((pressed.json or {}).get("error") or {}).get("detail") if pressed and isinstance(pressed.json, dict) else None
                    self.finding("%s's approval of %s was refused" % (a.name, name), "the page says %s; the platform said %s" % (
                        json.dumps(page_words, ensure_ascii=False), json.dumps((detail or {}).get("platformSaid") if isinstance(detail, dict) else None)),
                        kind_of(pressed.status, pressed.json) if pressed else UNREACHABLE, page=page_words, store=pressed.sentence() if pressed else "",
                        route="POST /v1/payees/addresses/…/approve", expected="counted: one of two, then approved")
                    continue
                body = pressed.json
                counts = body.get("approvals") if isinstance(body.get("approvals"), dict) else {}
                words.append("%s: %s%s — the page: %s" % (a.name, body.get("whitelistStatus"), (" (%s of %s)" % (counts.get("collected"), counts.get("required"))) if counts else "",
                                                         json.dumps(page_words, ensure_ascii=False)))
                self.next_step("the Payees room, after %s's press" % a.name, page_words or str(body.get("sentence") or body.get("whitelistStatus")))
                if body.get("whitelistStatus") == "whitelisted":
                    break
            after = v.read(S.PAYEES_ROUTE_API, "the payee register after the approvals: %s whitelisted at the owner's wallet" % name)
            record = self.payee_record(after, name, owner)
            status = (record or {}).get("whitelistStatus")
            self.facts["payees"].append({"name": name, "addressId": (record or {}).get("id"), "status": status})
            if status != "whitelisted":
                failures += 1
                self.finding("%s is not whitelisted" % name, "the register reads %r after the approvers' presses" % status, SCREEN, store=json.dumps(record, ensure_ascii=False),
                             expected="whitelisted once two of the roster approve")
            said.append("%s at the owner's wallet: %s; the register reads %s" % (name, "; ".join(w for w in words if w), status))
        return Outcome("R6", FAIL if failures else PASS, "; ".join(said))

    @staticmethod
    def payee_record(read: StoreRead, name: str, owner: str) -> Optional[Dict[str, Any]]:
        """The address of the payee called `name` on the payments' chain at the owner's wallet, as the register holds it (the newest such row)."""
        payees = (read.json or {}).get("payees") if read.ok and isinstance(read.json, dict) else None
        found = None
        for p in payees or []:
            if not isinstance(p, dict) or p.get("displayName") != name:
                continue
            for a in p.get("addresses") or []:
                if isinstance(a, dict) and str(a.get("chain")) == T.PAYEE_CHAIN and fold(a.get("address")) == fold(owner):
                    found = a
        return found

    # ======================================================================================================================
    # R7 and R7b — Enter payments, Submit this run, the run's page, the chain. The book's dollar between the founder's two presses.
    # ======================================================================================================================
    def book_rows(self, station: str) -> List[A.Payment]:
        keys = T.REAL_WORLD_FIRST_PRESS if station == "R7" else T.REAL_WORLD_SECOND_PRESS
        return [p for p in A.payments() if p.key in keys]

    def token_of_usdc(self, v: Visitor) -> Optional[str]:
        read = v.read(T.FUNDING_BALANCES_ROUTE, "the %s contract the estate names on %s (the balances road's row), which a balance is read against on the chain" % (T.PAYMENT_ASSET, T.PAYEE_CHAIN))
        rows = ((read.json or {}).get("balances") or []) if read.ok and isinstance(read.json, dict) else []
        row = next((r for r in rows if isinstance(r, dict) and str(r.get("asset") or "").upper() == T.PAYMENT_ASSET and str(r.get("chain") or "").lower() == T.PAYEE_CHAIN), None)
        return str(row.get("token")) if row and row.get("token") else None

    def enter_the_run(self, v: Visitor, rows: Sequence[A.Payment], owner: str, wallet: Dict[str, Any]) -> None:
        """The run typed as a founder types it (PaymentEntry.tsx): the reference left at its default, the wallet it leaves from, each payment's card."""
        v.goto(S.ENTRY_ROUTE)
        if v.heading() != S.ENTRY_HEADING:
            raise StationStop("Enter payments did not open: its heading reads %r" % v.heading())
        placeholder = v.page.get_by_label(S.REFERENCE_LABEL, exact=True).first.get_attribute("placeholder") if v.page.get_by_label(S.REFERENCE_LABEL, exact=True).count() else None
        self.step("page", v.name, "the run's reference left at its default (the field's placeholder reads %r; an empty reference is sent as %r)" % (placeholder, S.DEFAULT_REFERENCE))
        if v.page.get_by_label(S.PAY_FROM_LABEL, exact=True).count():
            options = v.options_of(S.PAY_FROM_LABEL)
            choice = next((o for o in options if o.startswith("%s · " % wallet.get("walletNumber"))), None)
            if choice is None:
                raise StationStop("Pay from offers no option for wallet %s (it offers %s)" % (wallet.get("walletNumber"), json.dumps(options, ensure_ascii=False)))
            v.select(S.PAY_FROM_LABEL, choice)
        else:
            raise StationStop("Enter payments offers no %r, so the run would leave from the funding wallet and not the wallet R5 made" % S.PAY_FROM_LABEL)
        for index, payment in enumerate(rows):
            if index:
                v.press(S.ADD_PAYMENT, why="a card for %s" % payment.invoice)
            card = v.card(S.payment_card(index + 1))
            if payment.payee_key is None:
                v.tick(S.ONE_OFF_LABEL, within=card, exact=False)
                v.fill(S.ONE_OFF_NAME_LABEL, payment.payee_name, within=card)
                v.fill(S.ONE_OFF_ADDRESS_LABEL, owner, within=card)
            else:
                options = v.options_of(S.PAYEE_LABEL, within=card)
                wanted = S.payee_option(payment.payee_name, T.PAYEE_CHAIN)
                if wanted not in options:
                    raise StationStop("the Payee list of %s offers no %r (it offers %s)" % (S.payment_card(index + 1), wanted, json.dumps(options, ensure_ascii=False)))
                if options.count(wanted) > 1:
                    # two payees that read alike: a founder cannot tell which is the owner's wallet, and neither can the harness, so it chooses neither
                    self.finding("%s: two payees read alike" % self.current, "the Payee list of %s offers %d entries reading %r" % (
                        S.payment_card(index + 1), options.count(wanted), wanted), SCREEN, page=json.dumps(options, ensure_ascii=False),
                        expected="one entry for the owner's wallet")
                    raise StationStop("the Payee list offers %d entries reading %r, so nothing was chosen and nothing submitted" % (options.count(wanted), wanted))
                v.select(S.PAYEE_LABEL, wanted, within=card)
            v.fill(S.CHAIN_LABEL, T.PAYEE_CHAIN, within=card)
            v.fill(S.ASSET_LABEL, T.PAYMENT_ASSET, within=card)
            v.fill(S.AMOUNT_LABEL, money_text(int(payment.amount_minor), T.ASSET_DECIMALS[T.PAYMENT_ASSET]), within=card)
            v.fill(S.INVOICE_LABEL, payment.invoice, within=card)

    def review_on_the_page(self, v: Visitor, press: str) -> Tuple[Optional[Exchange], Dict[str, Any]]:
        """Check this run (or Check again) pressed, and the review read both ways: the page's table of checks, and the answer the page received."""
        review = v.press(press, answer=("POST", r"^/v1/sets/review$"), why="the checks before the run exists")
        card = v.card(S.REVIEW_CARD)
        # the page renders the review once it has the answer: read when Submit this run stands as the answer says — enabled only where acceptable
        if review is not None and review.ok and isinstance(review.json, dict):
            acceptable = review.json.get("acceptable") is True
            v.poll(lambda: card.count() > 0 and v.control(S.SUBMIT_RUN).count() > 0 and bool(v.control(S.SUBMIT_RUN).first.is_enabled()) == acceptable)
        else:
            v.poll(lambda: bool(v.refusals()))
        gates = []
        for row in card.get_by_role("row").all()[1:]:
            gates.append(" ".join(row.inner_text().split()))
        words = {"gates": gates, "approval": v.text_of(card.locator("p").filter(has_text=S.RUN_TOTAL_WORDS)), "leaves": " | ".join(v.texts("note", name=S.LEAVES_FROM_NOTE)),
                 "refusals": v.refusals(), "submit_enabled": v.control(S.SUBMIT_RUN).first.is_enabled() if v.control(S.SUBMIT_RUN).count() else False}
        self.step("page", v.name, "the review on the page", page=json.dumps(words, ensure_ascii=False))
        return review, words

    def gas_shortfall(self, review: Optional[Exchange]) -> Optional[Dict[str, Any]]:
        gate = E.gate_of(review.json if review is not None else None, T.GAS_GATE)
        if not gate or gate.get("passed") is True:
            return None
        return next((r for r in (gate.get("refusals") or []) if isinstance(r, dict) and r.get("code") == T.GAS_SHORTFALL), None)

    def cure_gas(self, refusal: Dict[str, Any]) -> str:
        """
        Spec T26's cure, the one this leg makes on money: the estate's review refused GAS_SHORTFALL on the screen, so the estate's gas account is
        credited once through the platform's admin road, sized by that refusal's ceiling — never on a standing order, and never twice for one refusal.
        """
        detail = refusal.get("detail") if isinstance(refusal.get("detail"), dict) else {}
        ceiling = str(detail.get("ceilingUsdCents", ""))
        cents = E.Runner.gas_credit_for(int(ceiling) if ceiling.isdigit() else None)
        admin = self.read_admin_env()
        if admin is None:
            raise StationStop("%s; %s" % (T.GAS_CURE_NEEDED_CLAUSE % (T.GAS_SHORTFALL, refusal.get("message")), T.NO_GAS_CREDIT_ROAD_SENTENCE), prerequisite=E.NO_ADMIN_CREDENTIAL)
        account = (self.state.get("estate") or {}).get("accountId")
        if not account:
            raise StationStop("the gas credit was not made: the session names no platform account (workspace.aapAccountId)")
        ordinal = 1 + len(self.facts["gas_credits"])
        body = {"amount_usd_cents": int(cents), "reason": T.ADMIN_CREDIT_REASON % self.run_stamp, "idempotency_key": "aer360-real-world-%s-gas-%d" % (self.run_stamp, ordinal)}
        status, parsed, text = self.outside("the harness, at the platform's admin road", "POST", admin["base"] + T.ADMIN_CREDIT_ROUTE % account, body,
                                            headers={"Authorization": "Bearer %s" % admin["key"]})
        outcome, words = E.Runner.credit_words(E.Answer("POST", T.ADMIN_CREDIT_ROUTE % account, status, {}, text, 0), self.estate_name or "the estate")
        self.facts["gas_credits"].append({"amount_usd_cents": cents, "outcome": outcome, "said": words, "status": status})
        if outcome not in ("credited", "deduped"):
            raise StationStop("%s; the gas credit was not made: %s (%s)" % (T.GAS_CURE_NEEDED_CLAUSE % (T.GAS_SHORTFALL, refusal.get("message")), words,
                                                                          kind_of(status, parsed) if not (200 <= status < 300) else ANSWERED_WITH_ERROR))
        return "the review refused %s (%s), so the gas account was credited once: %s" % (T.GAS_SHORTFALL, refusal.get("message"), words)

    def answer_the_duplicate_screen(self, v: Visitor, review: Optional[Exchange], entered: Sequence[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Spec T28's bound, on the screen (Spec HRW-1 R7): each warning read word for word from the page and judged against the answer the page
        received — the box ticked, and Check again pressed, only where every warning names a payment of an EARLIER run; otherwise a finding,
        and nothing pressed. Answers the verdict ("none", "confirmed", "outside") and the sentences said.
        """
        payload = review.json if review is not None else None
        gate = E.duplicate_gate_of(payload)
        warnings = E.repeat_warnings(payload)
        if gate is None or gate.get("passed") is True or not warnings:
            return "none", []
        shown = v.refusals()
        warned = " | ".join(t for t in shown if E.DUPLICATE_UNACKNOWLEDGED_SENTENCE in t) or " | ".join(shown)
        self.next_step("the review's duplicate warning", warned)
        spoken: List[str] = ["the page warns, word for word: %s" % json.dumps(warned, ensure_ascii=False)]
        verdicts = []
        for w in warnings:
            row_index = w.get("rowIndex")
            row = entered[row_index] if isinstance(row_index, int) and 0 <= row_index < len(entered) else None
            kind, why = E.repeat_within_bound(w, self.started_at, self.facts["instructions_created"], row)
            verdicts.append((w, kind, why))
        outside = [(w, k, why) for w, k, why in verdicts if k != E.REPEAT_EARLIER]
        if outside:
            for w, k, why in outside:
                probe = (E.REPEAT_WITHIN_RUN_PROBE if k == E.REPEAT_WITHIN_RUN else E.REPEAT_UNBOUNDED_PROBE) % self.current
                self.finding(probe, "%s — %s" % (E.repeat_words(w, T.PAYMENT_ASSET), why), REFUSED, page=" | ".join(shown), store=json.dumps(w, ensure_ascii=False),
                             expected=E.REPEAT_BOUND_WORDS)
            return "outside", spoken + ["nothing was acknowledged and nothing created (Spec T28's bound)"]
        v.tick(S.ACKNOWLEDGE_REPEATS_WORDS, exact=False)
        again, _ = self.review_on_the_page(v, S.CHECK_AGAIN)
        gate = E.duplicate_gate_of(again.json if again is not None else None)
        if not gate or gate.get("passed") is not True or not str(gate.get("evidence") or "").endswith(E.DUPLICATE_ACKNOWLEDGED_EVIDENCE):
            self.finding("%s: the acknowledged review did not pass the duplicate screen" % self.current, E.duplicate_gate_words(again.json if again else None, T.PAYMENT_ASSET),
                         REFUSED, expected="the gate passed, its evidence ending %r" % E.DUPLICATE_ACKNOWLEDGED_EVIDENCE)
            return "outside", spoken
        for w, _, _ in verdicts:
            payee, amount, reference, sent_at, previous = E.repeat_facts(w, T.PAYMENT_ASSET)
            self.note(E.REPEAT_CONFIRMED_NOTE % (payee, amount, reference, sent_at, previous))
        return "confirmed", spoken + ["the box ticked and Check again pressed — the founder's confirmation, as T28 bounds it: %s" % gate.get("evidence")]

    def payment_approver_visitors(self) -> List[Visitor]:
        """The approvers of payments the charter names at C11, each with a session in this run, in the book's order."""
        return [v for v in (self.visitors.get(k) for k in self.payment_approvers()) if v is not None and not v.closed and v.session is not None]

    @staticmethod
    def runs_named_by(card: Any) -> Set[str]:
        """The runs an inbox card names: its own id or data attribute (data-run-id, data-set-id), and every link of its to a run's page (/runs/<id>)."""
        names: Set[str] = set()
        for attribute in ("id", "data-run-id", "data-set-id"):
            value = card.get_attribute(attribute)
            if value:
                names.add(str(value))
        for link in card.get_by_role("link").all():
            found = re.search(r"/runs/([^/?#]+)", str(link.get_attribute("href") or ""))
            if found:
                names.add(urllib.parse.unquote(found.group(1)))
        return names

    def marks_the_run_page_links_to(self, a: Visitor, run_id: str) -> Set[str]:
        """
        The inbox cards the run's own page links to (Runs.tsx says "in the Approver inbox"; a link of it to /inbox carrying a fragment, or a
        run=, set= or card= query, names the card): the run's page read in the approver's own context.
        """
        a.goto(S.RUN_ROUTE % run_id)
        a.appears(a.page.get_by_role("status", name=S.RUN_STATUS_NAME, exact=True))
        marks: Set[str] = set()
        for link in a.page.get_by_role("link").all():
            parsed = urllib.parse.urlparse(str(link.get_attribute("href") or ""))
            if parsed.path.rstrip("/") != S.INBOX_ROUTE:
                continue
            if parsed.fragment:
                marks.add(urllib.parse.unquote(parsed.fragment))
            query = urllib.parse.parse_qs(parsed.query)
            for key in ("run", "set", "card"):
                marks.update(query.get(key, []))
        return marks

    def approve_in_the_inbox(self, run_id: str, invoices: Sequence[str]) -> List[str]:
        """
        The run waits: each approver of payments the charter names at C11, in the book's order, opens their Approver inbox and presses Approve
        with passkey once, until the run is approved — and only on a card that belongs to a run this process created: a card that carries the
        run's id (its own id or data attribute, or a link of its to /runs/<id>), or the card the run's own page links to. A card that names no
        run is never pressed: a finding, and the run left waiting, which R9 cancels. (At AERAccounts b523cbf neither the card nor the run's page
        names a run, so a run that waits is not approved by this leg there.)
        """
        said: List[str] = []
        ours = {str(r.get("id")) for r in self.facts["runs"]}
        for a in self.payment_approver_visitors()[:APPROVALS_AT_MOST]:
            state = self.founder().read(S.SET_ROUTE % run_id, "the run before %s's press" % a.name)
            status = str(((state.json or {}).get("set") or {}).get("status")) if state.ok and isinstance(state.json, dict) else ""
            if status != "pending_approval" or run_id not in ours:
                break
            marks = self.marks_the_run_page_links_to(a, run_id)
            a.goto(S.INBOX_ROUTE)
            waiting = a.page.locator(S.CSS_CARD).filter(has=a.control(S.APPROVE_WITH_PASSKEY))
            a.appears(waiting, SETTLE_TIMEOUT_SECONDS)
            card = None
            unnamed = 0
            elsewhere = 0
            for candidate in waiting.all():
                names = self.runs_named_by(candidate)
                if names & marks:
                    names.add(run_id)  # the card the run's own page links to
                if not names:
                    unnamed += 1
                elif run_id in names:
                    card = candidate
                    break
                else:
                    elsewhere += 1
            if card is None:
                self.finding("%s: no card in the Approver inbox names this run" % self.current, "%s's inbox lists %d run(s) waiting — %d naming no run, %d naming "
                             "another — and none names run %s (%s), by its id or by a link from the run's own page; a card that names no run is never pressed, so "
                             "nothing was approved" % (a.name, unnamed + elsewhere, unnamed, elsewhere, run_id, ", ".join(invoices)), SCREEN,
                             page=" | ".join(waiting.all_inner_texts())[:600], expected="a card carrying this run's id, or the card the run's page links to")
                said.append("%s's inbox names no card for run %s, so nothing was pressed" % (a.name, run_id))
                break
            button = a.control(S.APPROVE_WITH_PASSKEY, within=card)
            if not button.count() or not button.first.is_enabled():
                said.append("%s may not approve it: %s" % (a.name, json.dumps(" | ".join(a.texts("status", within=card)) or a.text_of(card), ensure_ascii=False)))
                continue
            pressed = a.press(S.APPROVE_WITH_PASSKEY, within=card, answer=("POST", r"^/v1/approvals/[^/]+/approve$"), why="one passkey confirmation approves the whole run")
            self.save_credential(a)
            if pressed is not None and "/%s/" % run_id not in pressed.path:
                self.finding("%s: the press approved another run" % self.current, "%s's press in the Approver inbox approved %s, not this run's %s" % (
                    a.name, pressed.path, run_id), SCREEN, expected="this run approved, and no other")
            if pressed is None or not pressed.ok:
                self.finding("%s's approval was refused" % a.name, "the page says %s; the estate answered %s" % (
                    json.dumps(" | ".join(a.refusals()) or "nothing", ensure_ascii=False), pressed.sentence() if pressed else "nothing"),
                    kind_of(pressed.status, pressed.json) if pressed else UNREACHABLE, expected="counted")
                continue
            said.append("%s approved it in the Approver inbox (%s)" % (a.name, json.dumps(pressed.json, ensure_ascii=False)[:200]))
        return said

    def follow_the_run(self, v: Visitor, run_id: str) -> Tuple[Dict[str, Any], List[str]]:
        """The run's page read until every payment is terminal — its own words each time — beside the run as the store holds it."""
        last: Dict[str, Any] = {}
        words: List[str] = []
        for read_number in range(RUN_READS_AT_MOST):
            v.goto(S.RUN_ROUTE % run_id)
            v.appears(v.page.get_by_role("status", name=S.RUN_STATUS_NAME, exact=True))  # the run is read by the page's own request, after the load
            words = [v.text_of(v.page.get_by_role("status", name=S.RUN_STATUS_NAME, exact=True))] + [
                " ".join(r.inner_text().split()) for r in v.card(S.PAYMENTS_CARD).get_by_role("row").all()[1:]]
            read = v.read(S.SET_ROUTE % run_id, "the run as the store holds it: each instruction's status, its txHash or its failureReason")
            last = ((read.json or {}).get("set") or {}) if read.ok and isinstance(read.json, dict) else {}
            instructions = [i for i in (last.get("instructions") or []) if isinstance(i, dict)]
            if instructions and all(str(i.get("status")) in T.INSTRUCTION_TERMINAL_STATES for i in instructions):
                break
            if str(last.get("status")) in ("draft", "cancelled"):
                break
            self.sleep(RUN_READ_WAIT_SECONDS)
        self.step("page", v.name, "the run's page", page=" | ".join(words))
        self.next_step("the run's page", " | ".join(w for w in words if w))
        return last, words

    def hold_to_the_literal_bound(self, reviewed: List[Dict[str, Any]], owner: str, book: Sequence[A.Payment]) -> int:
        """
        THE LITERAL BOUND (RUN_CEILING_CENTS), held before every Submit this run on the rows the page will submit — the review it received: each to
        the owner's wallet, in USDC, and together with what this run has already submitted at most RUN_CEILING_CENTS, and the book's
        ONE_DOLLAR_MINOR beside it. Otherwise the whole run stops, nothing pressed: classified HARNESS where the book itself asks for more, SCREEN
        where the page would submit other than the book. Answers the cents these rows come to.
        """
        if not reviewed:
            raise RunStop(LITERAL_BOUND_UNREADABLE % ("the review carries no row", S.SUBMIT_RUN), kind=SCREEN)
        cents = 0
        for row in reviewed:
            address, asset, minor = str(row.get("address") or ""), str(row.get("asset") or ""), str(row.get("amountMinor") or "")
            if fold(address) != fold(owner):
                raise RunStop(LITERAL_BOUND_ADDRESS % (address or "no address", owner, S.SUBMIT_RUN), kind=SCREEN)
            if asset != T.PAYMENT_ASSET or not minor.isdigit():
                raise RunStop(LITERAL_BOUND_UNREADABLE % (json.dumps({k: row.get(k) for k in ("asset", "amountMinor", "address")}, ensure_ascii=False),
                                                          S.SUBMIT_RUN), kind=SCREEN)
            cents += -(-int(minor) // 10 ** (T.ASSET_DECIMALS[asset] - 2))  # rounded up: a part of a cent counts as a cent
        already = int(self.facts.get("submitted_cents") or 0)
        minor_per_cent = 10 ** (T.ASSET_DECIMALS[T.PAYMENT_ASSET] - 2)
        if already + cents > RUN_CEILING_CENTS or (already + cents) * minor_per_cent > T.ONE_DOLLAR_MINOR:
            asked = sum(-(-int(p.amount_minor) // minor_per_cent) for p in book)
            raise RunStop(LITERAL_BOUND_TOTAL % (cents, already, RUN_CEILING_CENTS, S.SUBMIT_RUN), kind=HARNESS if already + asked > RUN_CEILING_CENTS else SCREEN)
        return cents

    def pay_from_the_screen(self, station: str) -> Outcome:
        v = self.founder()
        owner = self.require_owner_payee()
        wallet = self.facts.get("wallet") or (self.state.get("wallet") if isinstance(self.state.get("wallet"), dict) else None)
        if not wallet or not wallet.get("address"):
            raise StationStop("no wallet of this leg's stands to pay from: R5 makes it", prerequisite=NO_WALLET)
        rows = self.book_rows(station)
        total = sum(int(p.amount_minor) for p in rows)
        # where the wallet is short, the owner is asked once for what this run still has to pay — at R7, R7b's row too — never press by press
        needed = total + (sum(int(p.amount_minor) for p in self.book_rows("R7b")) if station == "R7" else 0)
        said: List[str] = []
        failures = 0
        token = self.token_of_usdc(v)
        held, held_words = self.chain_balance(str(wallet["address"]), token, "%s's wallet %s" % (self.estate_name, wallet.get("walletNumber")))
        if held is not None and held < total:
            raise StationStop(FUND_THE_WALLET % (wallet.get("walletNumber"), wallet["address"], T.usdc_dollars(needed - held), T.PAYMENT_ASSET, T.C9_NETWORK_CHOICE,
                                                 T.usdc_dollars(needed), T.usdc_dollars(held), station.replace("R", "S")), prerequisite=WALLET_NOT_FUNDED)
        before, before_words = self.chain_balance(owner, token, "the owner's wallet")
        said.append("before: the wallet holds %s; the owner's wallet %s" % (held_words, before_words))
        self.enter_the_run(v, rows, owner, wallet)
        entered = [{"chain": T.PAYEE_CHAIN, "asset": T.PAYMENT_ASSET, "amountMinor": p.amount_minor, "invoiceRef": p.invoice} for p in rows]
        review, words = self.review_on_the_page(v, S.CHECK_RUN)
        shortfall = self.gas_shortfall(review)
        if shortfall is not None:
            said.append(self.cure_gas(shortfall))
            review, words = self.review_on_the_page(v, S.CHECK_AGAIN)
            if self.gas_shortfall(review) is not None:
                raise StationStop("the review refused %s again after the credit: %s (%s)" % (T.GAS_SHORTFALL, (self.gas_shortfall(review) or {}).get("message"), REFUSED))
        verdict, spoken = self.answer_the_duplicate_screen(v, review, entered)
        said.extend(spoken)
        if verdict == "outside":
            return Outcome(station, FAIL, "; ".join(said))
        if verdict == "confirmed":
            review = self.answered("POST", r"^/v1/sets/review$", v.name) or review
            words = {"submit_enabled": v.control(S.SUBMIT_RUN).first.is_enabled() if v.control(S.SUBMIT_RUN).count() else False}
        if not (review is not None and review.ok and isinstance(review.json, dict) and review.json.get("acceptable") is True) or not words.get("submit_enabled"):
            page_words = " | ".join(v.refusals())
            raise StationStop("the run cannot be submitted: the page says %s; the review %s (%s)" % (
                json.dumps(page_words or v.text_of(v.card(S.REVIEW_CARD))[:300], ensure_ascii=False), review.sentence() if review and not review.ok else "is not acceptable",
                kind_of(review.status, review.json) if review is not None and not review.ok else (ANSWERED_WITH_ERROR if review is not None else UNREACHABLE)))
        # THE OWNER'S WALLET AND THE BOOK, held at the screen before the one press that moves money (Spec T24; Spec HRW-1 §5): the literal bound
        # first — every row the page will submit is to the owner's wallet, and with what this run has submitted they come to at most RUN_CEILING_CENTS —
        # then the book's: every row in this press's own amounts from the book, or Submit this run is not pressed
        reviewed = [r for r in (review.json.get("rows") or []) if isinstance(r, dict)]
        cents = self.hold_to_the_literal_bound(reviewed, owner, rows)
        strangers = sorted({str(r.get("address")) for r in reviewed if fold(r.get("address")) != fold(owner)})
        amounts = sorted(int(str(r.get("amountMinor") or "0")) if str(r.get("amountMinor") or "0").isdigit() else -1 for r in reviewed)
        if strangers or amounts != sorted(int(p.amount_minor) for p in rows):
            raise StationStop("the review the page received names %s in amounts %s, and this press pays only %s to the owner's wallet %s (Spec T24, "
                              "the one-dollar law), so %r was not pressed and nothing moved" % (
                                  ", ".join(strangers) or "the owner's wallet", ", ".join(T.usdc_dollars(a) for a in amounts) or "none",
                                  ", ".join("%s %s" % (p.invoice, T.usdc_dollars(int(p.amount_minor))) for p in rows), owner, S.SUBMIT_RUN))
        # A RUN THAT WILL WAIT is submitted only where an approver of payments the charter names (C11) is here to approve it: otherwise it would stand
        # submitted, waiting on nobody in this run
        approval = review.json.get("approval") if isinstance(review.json.get("approval"), dict) else {}
        required = int(approval.get("approvalsRequired") or 0) if str(approval.get("approvalsRequired") or "0").isdigit() else 0
        if required and not self.payment_approver_visitors():
            raise StationStop("this run would wait for %d approval(s), and no approver the charter names at C11 (%s) has a session in this run, so nobody here could "
                              "approve it; %r was not pressed" % (required, ", ".join(A.PEOPLE[k].name for k in self.payment_approvers()), S.SUBMIT_RUN),
                              prerequisite=NO_APPROVER_SESSION)
        approval_words = v.text_of(v.card(S.REVIEW_CARD).locator("p").filter(has_text=S.RUN_TOTAL_WORDS))
        self.next_step("the review", "%s [%s]" % (approval_words, S.SUBMIT_RUN))
        since = len(self.exchanges)
        v.press(S.SUBMIT_RUN, answer=("POST", r"^/v1/sets$"), why="the run created and submitted in one press (Spec AER360-RUN-ROAD)", seconds=120.0)
        created = self.answered("POST", r"^/v1/sets$", v.name, since)
        if created is None or not created.ok or not isinstance(created.json, dict):
            page_words = " | ".join(v.refusals())
            code = ((created.json or {}).get("error") or {}).get("code") if created is not None and isinstance(created.json, dict) else None
            if code == S.IDEMPOTENCY_KEY_REUSED:
                self.finding("%s: the second run was refused as a replay" % station, "the page says %s" % json.dumps(page_words, ensure_ascii=False), REFUSED,
                             page=page_words, store=created.sentence(), expected="a second, different run of the day under the same reference is created (Spec AER360-RUN-ROAD §3.2)")
            raise StationStop("Submit this run created no run: the page says %s; the estate answered %s (%s)" % (
                json.dumps(page_words or "nothing", ensure_ascii=False), created.sentence() if created else "nothing", kind_of(created.status, created.json) if created else UNREACHABLE))
        run = created.json.get("set") if isinstance(created.json.get("set"), dict) else {}
        run_id = str(run.get("id"))
        for i in run.get("instructions") or []:
            if isinstance(i, dict) and i.get("id"):
                self.facts["instructions_created"][str(i["id"])] = {"key": i.get("invoiceRef"), "set_id": run_id, **{k: i.get(k) for k in (
                    "address", "chain", "asset", "amountMinor", "invoiceRef")}}
        record = {"station": station, "id": run_id, "reference": run.get("reference"), "createdAt": run.get("createdAt"), "invoices": [p.invoice for p in rows],
                  "total_minor": total, "cents": cents}
        self.facts["runs"].append(record)
        self.facts["submitted_cents"] = int(self.facts.get("submitted_cents") or 0) + cents  # counted once the run exists, whether or not it is sent
        self.state.setdefault("runs", []).append({k: record[k] for k in ("station", "id", "reference", "createdAt")})
        if not v.appears(v.page.get_by_role("status", name=S.RUN_STATUS_NAME, exact=True), 60.0):
            raise StationStop("the press created run %s and the run's page did not open; the page reads %r at %s" % (run_id, v.heading(), v.where()))
        submitted = self.answered("POST", r"^/v1/sets/[^/]+/submit$", v.name, since)
        banner = " | ".join(v.texts("status", name=S.SUBMISSION_NAME))
        said.append("run %s (reference %r) created and %s: the page says %s" % (
            run_id, run.get("reference"), "submitted (%s)" % json.dumps(submitted.json, ensure_ascii=False) if submitted is not None and submitted.ok else
            "not submitted (%s)" % (submitted.sentence() if submitted else "no submit in the browser's log"), json.dumps(banner or " | ".join(v.refusals()), ensure_ascii=False)))
        self.next_step("the run's page", banner)
        said.extend(self.approve_in_the_inbox(run_id, record["invoices"]))
        final, page_words = self.follow_the_run(v, run_id)
        instructions = [i for i in (final.get("instructions") or []) if isinstance(i, dict)]
        landed = [i for i in instructions if i.get("status") == T.INSTRUCTION_CONFIRMED_STATE]
        record.update(status=final.get("status"), landed=len(landed), hashes=[i.get("txHash") for i in landed])
        if str(final.get("status")) == "draft":
            failures += 1
            self.finding("%s: the run stays a draft" % station, "the run's page says %s" % json.dumps(" | ".join(page_words), ensure_ascii=False), SCREEN,
                         page=" | ".join(page_words), store=json.dumps(final, ensure_ascii=False)[:500], expected="submitted by the press that created it (Spec AER360-RUN-ROAD)")
        for i in instructions:
            if i.get("status") == T.INSTRUCTION_CONFIRMED_STATE:
                continue
            failures += 1
            reason = str(i.get("failureReason") or "")
            shown = next((w for w in page_words if (i.get("invoiceRef") or "") in w or (reason and reason[:40] in w)), "")
            plain = next((s for s in S.ESTATE_PLAIN_SENTENCES if s in " | ".join(page_words)), None)
            self.finding("%s: %s %s was not landed" % (station, i.get("invoiceRef"), i.get("status")), "the run's page says %s%s; the store holds %s" % (
                json.dumps(shown or " | ".join(page_words), ensure_ascii=False), (" and, beside it, the estate's plain sentence %r" % plain) if plain else "",
                json.dumps({k: i.get(k) for k in ("status", "failureReason", "txHash")}, ensure_ascii=False)),
                ANSWERED_WITH_ERROR if reason else SCREEN, page=shown, store=reason, expected="landed, with its transaction hash")
        after, after_words = self.chain_balance(owner, token, "the owner's wallet")
        moved = sum(int(i.get("amountMinor") or 0) for i in landed)
        if before is None or after is None:
            failures += 1
            self.finding("%s: the chain could not be read" % station, "before: %s; after: %s" % (before_words, after_words), UNREACHABLE,
                         expected="the owner's wallet read before and after on %s" % T.PAYEE_CHAIN)
        elif after - before != moved:
            failures += 1
            self.finding("%s: the owner's wallet moved by another figure" % station, "it read %s before and %s after; the landed payments total %s" % (
                T.usdc_dollars(before), T.usdc_dollars(after), T.usdc_dollars(moved)), SCREEN, expected="moved by the run's landed total")
        said.append("%d of %d payment(s) landed (%s); the owner's wallet %s → %s" % (
            len(landed), len(instructions), ", ".join(str(h) for h in record["hashes"]) or "no hash", T.usdc_dollars(before) if before is not None else "unread",
            T.usdc_dollars(after) if after is not None else "unread"))
        return Outcome(station, FAIL if failures else PASS, "; ".join(said))

    def station_r7(self) -> Outcome:
        return self.pay_from_the_screen("R7")

    def station_r7b(self) -> Outcome:
        """
        The founder presses Submit this run a second time the same day, under the same default reference, for a different run — the rest of the
        one-dollar book (Spec HRW-1 R7b; the module's header, note 3). The screen must create it: IDEMPOTENCY_KEY_REUSED is a finding.
        """
        first = next((r for r in self.facts["runs"] if r.get("station") == "R7"), None)
        outcome = self.pay_from_the_screen("R7b")
        second = next((r for r in self.facts["runs"] if r.get("station") == "R7b"), None)
        if second is None:
            return outcome
        extra: List[str] = []
        failures = 0 if outcome.outcome == PASS else 1
        if first is not None:
            if second["id"] == first["id"]:
                failures += 1
                self.finding("R7b: the second press answered the first run", "both presses name run %s" % first["id"], SCREEN, expected="a second, different run")
            if second.get("reference") != first.get("reference"):
                extra.append("the two runs carry references %r and %r" % (first.get("reference"), second.get("reference")))
            else:
                extra.append("a second, different run (%s) under the same reference %r as R7's (%s), the same day" % (second["id"], second.get("reference"), first["id"]))
        else:
            extra.append("R7 created no run this run, so the second press is the day's first")
        return Outcome("R7b", FAIL if failures else PASS, "%s; %s" % (outcome.line, "; ".join(extra)))

    # ======================================================================================================================
    # R8 — The two legs agree; and the founder's next step, page by page, held against the Client Manual's words.
    # ======================================================================================================================
    def api_leg_report(self) -> Optional[Dict[str, Any]]:
        """The API leg's newest report for the same estate (aer360-harness-<date>[-HHMMSS].md in its folder, the estate named in its title)."""
        try:
            names = os.listdir(self.api_reports)
        except OSError:
            return None
        dated = []
        for name in names:
            found = E.REPORT_NAME.match(name)
            if found:
                dated.append(((found.group(1), found.group(2) or "000000"), name))
        for _, name in sorted(dated, reverse=True):
            path = os.path.join(self.api_reports, name)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    title = handle.readline().strip()
                report = E.read_report(path)
            except (OSError, UnicodeDecodeError):
                continue
            company = title[len(E.REPORT_TITLE):].rsplit(" — ", 1)[0] if title.startswith(E.REPORT_TITLE) else None
            if company and self.estate_name and company == self.estate_name:
                report["company"] = company
                return report
        return None

    def outcome_of(self, station: str) -> Optional[Outcome]:
        return next((o for o in self.outcomes if o.station == station), None)

    def station_r8(self) -> Outcome:
        report = self.api_leg_report()
        said: List[str] = []
        failures = 0
        if report is None:
            raise StationStop("no report of the API leg names %s in %s (aer360-harness-<date>.md, its --out folder): run python3 aer360_harness.py for the same estate, "
                              "then this leg again — R8 compares the stations a run walks" % (self.estate_name or "this estate", os.path.abspath(self.api_reports)),
                              prerequisite=NO_API_LEG_REPORT)
        said.append("the API leg's report %s (started %s)" % (report["name"], report.get("started_at")))
        report_faults: List[str] = []
        agreed: List[str] = []
        not_compared: List[str] = []
        for station, api_station in API_LEG_STATION.items():
            mine = self.outcome_of(station)
            theirs = report["outcomes"].get(api_station)
            # a station that did not run to its judgment on either side — skipped, not run, or stopped on a prerequisite (a file not filed, a session
            # not held) — proved nothing about the road, so there is nothing to compare
            if mine is None or mine.outcome in (SKIPPED, NOT_RUN, FAILED_PREREQUISITE) or theirs in (None, SKIPPED, NOT_RUN, FAILED_PREREQUISITE, E.OUT_OF_SCOPE):
                not_compared.append("%s/%s (%s, %s)" % (station, api_station, mine.outcome if mine else "not run", theirs or "absent"))
                continue
            if theirs == PASS and mine.outcome != PASS:
                failures += 1
                self.finding("a SCREEN fault at %s" % station, "the server can; the screen cannot: the API leg passed %s and the browser leg %s %s — %s" % (
                    api_station, mine.outcome, station, mine.line[:300]), SCREEN, expected="both legs pass")
            elif mine.outcome == PASS and theirs != PASS:
                report_faults.append("the browser leg passed %s and the API leg %s %s" % (station, theirs, api_station))
            else:
                agreed.append("%s/%s %s" % (station, api_station, mine.outcome if mine.outcome == theirs else "%s and %s" % (mine.outcome, theirs)))
        if report_faults:
            raise RunStop(kind=HARNESS, sentence="a report fault in one of the legs: %s — a road cannot pass at the screen and fail at the server, so one of the two reports is wrong "
                          "(Spec HRW-1 R8); the run stops here" % "; ".join(report_faults))
        if not agreed and not failures:
            raise StationStop("no station of this run ran to a judgment the API leg's report %s also holds (not compared: %s), so the two legs were not compared" % (
                report["name"], ", ".join(not_compared)), prerequisite=NOTHING_COMPARED)
        said.append("the legs agree on %s" % (", ".join(agreed) or "nothing"))
        if not_compared:
            said.append("not compared: %s" % ", ".join(not_compared))
        failures += self.hold_the_pages_against_the_manual(said)
        return Outcome("R8", FAIL if failures else PASS, "; ".join(said))

    def hold_the_pages_against_the_manual(self, said: List[str]) -> int:
        """
        The Customer Support hat: every station that passed must have left the founder a next step, in the page's own words; and where the Client
        Manual names a control or says a sentence for a step this run walked, the page must offer that control or say that sentence
        (aer360_screens.MANUAL_WORDS: the manual as the product's library carries it, beside the owner's edition v8 where the two differ). A
        failed station is not held — its own findings say what its page said — and a step a rerun did not walk (a charter, a wallet, payees that
        already stand) is not held either. The manual's words for a step that names no control are set beside the page's for the reader.
        """
        failures = 0
        held = 0
        pressed = self.pressed_names()
        for station in STATION_IDS:
            mine = self.outcome_of(station)
            if station in ("R8", "R9") or mine is None or mine.outcome != PASS:
                continue
            steps = self.next_steps.get(station) or []
            if not steps:
                failures += 1
                self.finding("%s left the founder no next step" % station, "the station passed and recorded no sentence, notice or control telling the founder what comes next",
                             SCREEN, expected="the page's own next step (the Customer Support hat)")
            words = " | ".join(s for _, s in steps)
            for item in S.MANUAL_WORDS.get(station, []):
                check = item.get("check")
                if check == "duplicate":
                    if self.met_the_duplicate_screen(station):
                        self.note("%s, beside the manual: the manual's word for the founder's confirmation of a repeat is the refusal's own imperative, %r (%s); "
                                  "the page's control is the box %r, then %r, then %r — the founder confirmed it by the page's controls" % (
                                      station, item["quote"], item["source"], S.ACKNOWLEDGE_REPEATS_WORDS, S.CHECK_AGAIN, S.SUBMIT_RUN))
                    continue
                if not self.walked(station, item):
                    continue
                held += 1
                if check == "none":
                    self.note("%s, beside the manual: the manual says %r (%s); the page said %s" % (station, item["quote"], item["source"], json.dumps(words, ensure_ascii=False)))
                elif check == "pressed" and not any(n == item["control"] or n.startswith(item["control"]) for n in pressed.get(station, [])):
                    failures += 1
                    self.finding("the manual and the page disagree at %s" % station, "the manual says %r (%s) and names %r; the founder pressed %s" % (
                        item["quote"], item["source"], item["control"], json.dumps(pressed.get(station, []), ensure_ascii=False)), SCREEN, page=words,
                        expected="a control the manual names")
                elif check == "said" and item["words"] not in words:
                    failures += 1
                    self.finding("the manual and the page disagree at %s" % station, "the manual says %r (%s); the page said %s" % (
                        item["quote"], item["source"], json.dumps(words, ensure_ascii=False)), SCREEN, page=words, expected=item["words"])
        said.append("the pages' next steps held against %d of the Client Manual's words, for the steps this run walked" % held)
        return failures

    def walked(self, station: str, item: Dict[str, Any]) -> bool:
        """Whether this run walked the step a manual item describes: the request the step makes, answered, at the station (and a field of its answer set)."""
        road = item.get("walked")
        if not road:
            return True
        method, pattern = road[0], re.compile(road[1])
        field = road[2] if len(road) > 2 else None
        for x in self.exchanges:
            if x.station != station or x.method != method or not x.ok or not pattern.search(x.path.split("?", 1)[0]):
                continue
            value: Any = x.json
            for part in (field.split(".") if field else []):
                value = value.get(part) if isinstance(value, dict) else None
            if field is None or value:
                return True
        return False

    def pressed_names(self) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for station, entries in self.evidence.items():
            for e in entries:
                found = re.match(r"^pressed '(.*)' on ", e.get("what") or "") or re.match(r'^pressed "(.*)" on ', e.get("what") or "")
                if e.get("kind") == "press" and found:
                    out.setdefault(station, []).append(found.group(1))
        return out

    def met_the_duplicate_screen(self, station: str) -> bool:
        return any(f.station == station for f in self.findings if "duplicate" in f.probe) or any(
            E.DUPLICATE_UNACKNOWLEDGED_SENTENCE in s for _, s in self.next_steps.get(station, [])) or any(
            "Spec T28" in n for n in self.notes.get(station, []))

    # ======================================================================================================================
    # R9 — Teardown: any draft this run left is cancelled from its own page; nothing else is touched.
    # ======================================================================================================================
    def station_r9(self) -> Outcome:
        """
        Teardown: every run this run made that has not been sent — a draft, or one still waiting for an approval, which would move money the moment
        someone approved it after the run — cancelled from its own page (the run page's Cancel), and read again to see that it was; nothing else
        is touched, and a run that executed is left as it stands.
        """
        v = self.founder()
        cancelled: List[str] = []
        stands: List[str] = []
        failures = 0
        for record in self.facts["runs"]:
            read = v.read(S.SET_ROUTE % record["id"], "the run this run made: a run not sent is cancelled, anything else is left as it stands")
            status = str(((read.json or {}).get("set") or {}).get("status")) if read.ok and isinstance(read.json, dict) else "unread (%s)" % read.sentence()
            if status not in ("draft", "pending_approval"):
                stands.append("%s %s" % (record["id"], status))
                continue
            v.goto(S.RUN_ROUTE % record["id"])
            pressed = v.press(S.CANCEL_RUN, answer=("POST", r"^/v1/sets/[^/]+/cancel$"), why="a run this run made and did not send (%s)" % status)
            after = v.read(S.SET_ROUTE % record["id"], "the run, cancelled")
            now = str(((after.json or {}).get("set") or {}).get("status")) if after.ok and isinstance(after.json, dict) else "unread (%s)" % after.sentence()
            if pressed is None or not pressed.ok or now != "cancelled":
                failures += 1
                v.poll(lambda: bool(v.refusals()))
                self.finding("R9: a run this run made was not cancelled", "%s stood %s and stands %s after the page's Cancel; the page says %s; the estate answered %s" % (
                    record["id"], status, now, json.dumps(" | ".join(v.refusals()) or "nothing", ensure_ascii=False), pressed.sentence() if pressed else "nothing"),
                    kind_of(pressed.status, pressed.json) if pressed is not None and not pressed.ok else (UNREACHABLE if pressed is None else SCREEN),
                    store=after.text[:400], expected="cancelled")
            cancelled.append("%s %s → %s (%s)" % (record["id"], status, now, "the page's Cancel" if pressed is not None and pressed.ok else
                                                  (pressed.sentence() if pressed is not None else "no answer")))
        if not self.facts["runs"]:
            return Outcome("R9", PASS, "this run made no run, so nothing was left to cancel; nothing else is touched")
        return Outcome("R9", FAIL if failures else PASS, "cancelled: %s; left as they stand: %s; nothing else is touched" % (
            ", ".join(cancelled) or "none", ", ".join(stands) or "none"))

    # ======================================================================================================================
    # The report: the API leg's shape, with the page's own words beside what the store and the chain say.
    # ======================================================================================================================
    def report(self) -> str:
        lines: List[str] = []
        lines.append("# AER 360 browser leg run — Harness Real World — %s — %s" % (self.estate_name or "the estate was not reached", self.started_at))
        lines.append("")
        lines.append("Spec HRW-1, written 7 October 2026, revised 9 October 2026. Base URL %s. The browser leg walks the road a founder walks — a real browser, "
                     "the real pages, a passkey behind the real prompt — and reads the store afterwards as the API leg reads it. A failure below is evidence, "
                     "not a verdict: what the page said, word for word; the request the browser made and what came back (secrets and passkey material redacted "
                     "to their last four characters; no header, no cookie); the store's reading; and the screenshot. This report names no real person and no real "
                     "company: the estate and its people are the harness's own." % self.base)
        lines.append("")
        lines.append("## The closing table")
        lines.append("")
        lines.append("| Station | Outcome | Line |")
        lines.append("|---|---|---|")
        for o in self.outcomes:
            cells = ["%s %s" % (o.station, TITLES.get(o.station, "")), E.outcome_cell(o.outcome), o.line]
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
        lines.append("")
        where = ", ".join("%s %d" % (s, n) for s, n in ((s, sum(1 for f in self.findings if f.station == s)) for s in ["start", "resume"] + STATION_IDS) if n)
        lines.append("Findings in this run: %d%s." % (len(self.findings), (" (%s)" % where) if where else ""))
        lines.append("")
        lines.extend(self.summary_lines())
        for station in ["resume"] + STATION_IDS:
            outcome = self.outcome_of(station)
            if station == "resume":
                if not self.evidence.get("resume"):
                    continue
                lines.append("")
                lines.append("## Resume")
                lines.extend(self.render_steps(self.evidence["resume"]))
                continue
            lines.append("")
            lines.append("## %s — %s" % (station, TITLES[station]))
            lines.append("")
            lines.append("Outcome: **%s**. %s" % (outcome.outcome if outcome else NOT_RUN, outcome.line if outcome else ""))
            for where_said, sentence in self.next_steps.get(station, []):
                lines.append("")
                lines.append("What to do next, in the page's words (%s): \"%s\"" % (where_said, sentence))
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
                    lines.append("  - Kind: %s" % f.kind)
                    if f.page:
                        lines.append("  - The page said: \"%s\"" % f.page)
                    if f.store:
                        lines.append("  - The store says: `%s`" % f.store)
                    if f.route:
                        lines.append("  - Route: %s" % f.route)
                    if f.expected:
                        lines.append("  - Expected: %s" % f.expected)
            steps = self.evidence.get(station, [])
            if steps:
                lines.append("")
                lines.append("### Evidence, step by step")
                lines.extend(self.render_steps(steps))
        lines.append("")
        lines.append("## Every request the browser made")
        lines.append("")
        lines.append("| At | Station | Who | Route | Status |")
        lines.append("|---|---|---|---|---|")
        for x in self.exchanges:
            lines.append("| %s | %s | %s | %s | %d |" % (x.at, x.station, x.who, redact_query(x.route).replace("|", "\\|"), x.status))
        return self.secrets.redact_text("\n".join(lines) + "\n")

    def summary_lines(self) -> List[str]:
        out: List[str] = []
        wallet = self.facts.get("wallet") or {}
        if wallet:
            out.append("- The wallet this leg pays from: %s, %s." % (wallet.get("walletNumber"), wallet.get("address")))
        if self.facts.get("owner_payee"):
            out.append("- The payee of every payment: %s, %s (Spec T24)." % (self.facts["owner_payee"], T.OWNER_WALLET_WORDS))
        for run in self.facts["runs"]:
            out.append("- %s: run %s, reference %r, %s, %s landed, hashes %s." % (run["station"], run["id"], run.get("reference"), run.get("status"),
                                                                                 run.get("landed"), ", ".join(str(h) for h in run.get("hashes") or []) or "none"))
        if self.facts["gas_credits"]:
            out.append("- Gas credited, each on the review's %s and once: %s." % (T.GAS_SHORTFALL, "; ".join(c["said"] for c in self.facts["gas_credits"])))
        if self.facts.get("receipt_ceilings"):
            out.append("- The write's ceilings: %s." % json.dumps(self.facts["receipt_ceilings"], ensure_ascii=False))
        if out:
            out.insert(0, "Summary:")
            out.insert(1, "")
        return out

    @staticmethod
    def render_steps(steps: List[Dict[str, Any]]) -> List[str]:
        out: List[str] = []
        for index, s in enumerate(steps, 1):
            out.append("")
            out.append("%d. [%s] %s — %s" % (index, s.get("kind"), s.get("who"), s.get("what")))
            if s.get("expected"):
                out.append("   - Expected: %s" % s["expected"])
            if s.get("result"):
                out.append("   - Result: %s" % s["result"])
            if s.get("page"):
                out.append("   - The page said: \"%s\"" % s["page"])
            if s.get("came_back"):
                out.append("   - Came back, verbatim: `%s`" % str(s["came_back"])[:2000])
            if s.get("screenshot"):
                out.append("   - Screenshot: %s" % s["screenshot"])
        return out

    def write_report(self) -> str:
        return self.folder.write_report(self.report())


# ---------------------------------------------------------------------------
# The plan, printed without --i-mean-it: every station, what it presses and what it reads, with nothing opened and nothing sent.
# ---------------------------------------------------------------------------
def normalise_station(text: str) -> str:
    """--from S5, R5, s7b, R7b: the API leg's numbers name the browser leg's stations (Spec HRW-1 §3: the same --from flag)."""
    raw = str(text or "").strip()
    found = re.match(r"^[RrSs](\d+)([bB]?)$", raw)
    wanted = "R%s%s" % (found.group(1), found.group(2).lower()) if found else raw
    if wanted not in STATION_IDS:
        raise HarnessFault("no station called %s; the stations are %s (S<n> names the same station as R<n>)" % (raw, ", ".join(STATION_IDS)))
    return wanted


def plan_lines(base: str = DEFAULT_BASE, start_at: Optional[str] = None) -> List[str]:
    start = STATION_IDS.index(normalise_station(start_at)) if start_at else 0
    first = [p for p in A.payments() if p.key in T.REAL_WORLD_FIRST_PRESS]
    second = [p for p in A.payments() if p.key in T.REAL_WORLD_SECOND_PRESS]
    book = lambda rows: ", ".join("%s %s %s to %s" % (p.invoice, p.amount, T.PAYMENT_ASSET, p.payee_name) for p in rows)  # noqa: E731
    walk = {
        "R1": "open the one-time link the birth script printed (from --birth, never printed; the estate it names held to the harness's own first), the virtual authenticator answering the page's own "
              "request for a key — or %r where the page offers it; read the welcome; %r; then GET %s and GET %s" % (S.ENROLMENT_CREATE_ACTION, S.continue_label("<estate>"),
                                                                                                                  S.INVITES_ROUTE, S.SESSION_ROUTE),
        "R2": "a fresh context, the stored credential re-added: %s → %r; the estate the sidebar names (one of %s, else the run stops)" % (base, S.SIGN_IN_BUTTON,
                                                                                                                                       ", ".join(T.HARNESS_ESTATE_NAMES)),
        "R3": "the signing entries read on the platform's read road (zero); %s → %r; every page answered through its controls from the book, the addresses typed "
              "%s; a zero at C2 once, its refusal read; C2 %s and C3 %s; the read-back's two ceiling lines; %r; the receipt's ceilings; the entries again; the "
              "People page's roster and GET %s" % (S.ONBOARDING_ROUTE, S.BEGIN_POLICY_INTERVIEW, ", ".join(json.dumps(t) for t in T.REAL_WORLD_TYPED_ADDRESSES.values()),
                                                    cents_text(A.MONEY["company_ceiling_cents"]), cents_text(A.MONEY["daily_total_cents"]), S.CONFIRM_CHARTER,
                                                    S.APPROVER_SEATS_ROUTE),
        "R4": "%s: %s from the seat the charter gives them (its Invite), %s from the form (%r and %r typed: an approver of changes has no seat); the "
              "Executive standing and the pen, %r, the link read once and hidden; each redeems it in a context of their own; %r on the seat, %r on the register" % (
            S.PEOPLE_ROUTE, " and ".join(A.PEOPLE[k].name for k in S.APPROVERS if k in RealWorld.payment_approvers()),
            " and ".join(A.PEOPLE[k].name for k in S.APPROVERS if k not in RealWorld.payment_approvers()), S.INVITE_NAME_LABEL, S.INVITE_EMAIL_LABEL,
            S.INVITE_SUBMIT, S.SEAT_WORDS["seated"], S.REGISTER_WORDS["redeemed"]),
        "R5": "%s: %r where the page offers it first; %r → %r → %r; the address read; GET %s and GET %s (group-100)" % (
            S.WALLETS_ROUTE, S.GIVE_FUNDING_WALLET, S.CREATE_NEW_WALLET, S.THIS_ESTATE, S.CREATE_IT, S.WALLETS_REGISTER_ROUTE, S.PLAN_ROUTE),
        "R6": "%s: %s added at the owner's wallet (%s; one typed with a trailing space), %r; %s press %r in their own contexts; GET %s" % (
            S.PAYEES_ROUTE, " and ".join(p["name"] for p in T.PAYEES), T.OWNER_PAYEE_PLACEHOLDER, S.SEND_FOR_APPROVAL, " then ".join(A.PEOPLE[k].name for k in S.APPROVERS),
            S.APPROVE, S.PAYEES_ROUTE_API),
        "R7": "%s: %s; the reference left at its default; %r; the duplicate screen answered within Spec T28's bound; a gas credit only on the review's %s; %r; the "
              "Approver inbox; the run's page until landed; the owner's wallet read on the chain before and after" % (S.ENTRY_ROUTE, book(first), S.CHECK_RUN,
                                                                                                                       T.GAS_SHORTFALL, S.SUBMIT_RUN),
        "R7b": "the second %r of the day under the same default reference: %s — the screen must create it" % (S.SUBMIT_RUN, book(second)),
        "R8": "the API leg's newest report for the same estate (aer360-harness-<date>.md), station by station; each page's next step held against the Client Manual",
        "R9": "every run this run made and did not send — a draft, or one waiting for an approval — cancelled from its own page (%r) and read again; "
              "nothing else touched" % S.CANCEL_RUN,
    }
    out = []
    for index, (station, title) in enumerate(STATIONS):
        out.append("%s %s — %s" % (station, title, ("skipped: resumed at %s" % STATION_IDS[start]) if index < start else walk[station]))
    out.append("The book on %s: %s in all, every payment to the owner's wallet (Spec T24)." % (
        T.PAYEE_CHAIN, T.usdc_dollars(sum(int(p.amount_minor) for p in first + second))))
    return out


# ---------------------------------------------------------------------------
# The command line.
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Harness Real World (Spec HRW-1): the browser leg of the estate harness — a real browser, the real pages, "
                                                 "a passkey behind the real prompt, the presses a founder makes and the sentences a founder reads.")
    parser.add_argument("--i-mean-it", dest="i_mean_it", action="store_true",
                        help="press controls on the estate with real passkeys and move up to one dollar of real USDC to the owner's wallet; without it the plan is printed")
    parser.add_argument("--from", dest="start_at", help="resume at a station — S5 or R5, the API leg's numbers — every person signed in with their stored credential")
    parser.add_argument("--headed", action="store_true", help="show the browser (by default it runs headless and writes a screenshot per station)")
    parser.add_argument("--birth", help="the birth script's printout, a file or - for standard input: the one-time link, the account id, and whether --email was given")
    parser.add_argument("--base", default=DEFAULT_BASE, help="the estate's base URL (default %s)" % DEFAULT_BASE)
    parser.add_argument("--store", default=STORE_ROOT, help="the harness's store (default ~/.aer360-harness): admin.env, payee.env, and real-world/ for the credentials")
    parser.add_argument("--out", default=RUNS_DIR, help="where the run folder is written (default ~/Downloads/harness-runs)")
    parser.add_argument("--api-reports", dest="api_reports", default=API_REPORTS_DIR, help="the API leg's report folder, which R8 reads (default the working folder)")
    args = parser.parse_args(argv)
    try:
        start_at = normalise_station(args.start_at) if args.start_at else None
    except HarnessFault as err:
        print(str(err))
        return 2
    if not args.i_mean_it:
        print(I_MEAN_IT % args.base)
        for line in plan_lines(args.base, start_at):
            print(line)
        return 2
    leg = RealWorld(args.base, os.path.expanduser(args.store), args.birth, start_at, args.headed, os.path.expanduser(args.out), args.api_reports)
    try:
        leg.run()
    except KeyboardInterrupt:
        print("Interrupted; the report is written with what ran.")
    except HarnessFault as err:
        print("The harness could not start — its own failure, not the estate's: %s" % err)
        if not leg.outcomes:
            return 2
    finally:
        if leg.outcomes:
            print("Report: %s" % leg.write_report())
    return 1 if any(o.outcome in FAILURES for o in leg.outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
