"""
THE HARNESS CONSENTS ITS OWN AGENTS (Spec T21, 26 September 2026): the harness is its own customer,
born once with a software passkey, seated once by the operator, and consented by software for every
label the run file names — no browser, no link, no listener, no hand.

THE FINDING (not re-diagnosed). `corridor_harness.py --consent <label>` used to print an OAuth link and
wait for a person to open it, sign in, choose a package, name the agent, approve it with a passkey and
press Finish; the consent opened by hand on 26 September never reached the harness, and Series A stopped
at A2. Every step of the consent is JSON over HTTP — the calls `pages/consentpage.ts` makes — and the
estate harness already carries a software passkey `@simplewebauthn/server` accepts (`aer360_passkey.py`,
used here as it is). The one step that is not an HTTP call is the package: `POST /v1/consent/:id/checkout`
opens the payment desk, and the harness will not drive the desk's page. So the seat is granted once, on the
box, by the operator (`tools/harness_seat.sh <customer-id>`), and this module stops with one sentence and
one command until it is.

Read from the connector's code rather than from memory (aeredium/aer-connector, main at 9e20d6c):
  apps/server/src/routes/auth.ts        signup/options → {options, nonce, issuedAtMs, handle}; signup/verify
                                        {displayName, email, country, handle, nonce, issuedAtMs, response} → {customer, csrfToken}
                                        and the session cookie; signin/options → {options, nonce, issuedAtMs};
                                        signin/verify {nonce, issuedAtMs, response}; stepup/options (purpose approve)
  apps/server/src/services/session.ts   the cookie `aer_connector_session`; the header `x-aer-csrf`
  apps/server/src/routes/guards.ts      requireCaller(…, {mutating: true}): the cookie, then the CSRF header
  apps/server/src/services/webauthn.ts  rpID and origin from the connector's config; the counter must move forward
  apps/server/src/routes/oauth.ts       GET /authorize → 302, Location: /consent?request=<id>; POST /token
  apps/server/src/routes/consent.ts     GET /v1/consent/:id → a stage: sign_in, pay, connected, agent, closed;
                                        ?connect=1 → agent, with agents[] and roles[] (defaultRank, questionnaire);
                                        POST /agent {name, roleId, fundingAddress, rank, answers, nonce, issuedAtMs,
                                        response} → the receipt with connection.id; POST /finish {connectionId, rank}
                                        or {agentId} → {redirectTo}; AGENT_ALREADY_CONNECTED where a connection stands
  apps/server/src/services/billing.ts   standingOf: trialing or active, and the clock → paid; else none or lapsed
  apps/server/src/http.ts               a refusal is {error: {code, message, detail}}; 401 NOT_AUTHENTICATED and
                                        PASSKEY_*, 402 SUBSCRIPTION_*, 400 ANSWER_INVALID and REQUEST_MALFORMED,
                                        409 AGENT_ALREADY_CONNECTED, 502 AAP_REFUSED, 503 *_UNREACHABLE
  packages/shared/src/refusals.ts       the codes and their sentences
  packages/shared/src/packages.ts       Solo seats three agents

THE ANSWER BOOK (§4) is the harness's, per role, pinned here beside the figures Series C expects
(per trade 20, per day 100, ask me first 50). Only maxTxPerDay, assets and rank are the role's own, read
from the payload's roles[]; the four the page leaves for the person are the book's. The series do not
import the book — series.py is fenced — so the book reads the series' figures out of the restore pauses
series.py already carries ("set 'per trade' back to 20 dollars") and stops the run where the two disagree,
naming both. The book is not a second copy: it is held against the series.

THE TRADER'S LIST (Spec T22, 27 September 2026): the Trader's list is `T.TRADER_LIST_B3`, the eight lines B3 names,
so a Trader may trade from its first consent. The Payer's list is the run file's listed address, so B4 reads the
list and passes when the address stands.

Nothing here prints a secret: the passkey's PEM, the ceremony's bytes and signature, the cookie, the CSRF
token, the authorization code and the sign-up handle are redacted to their last four characters in the run
folder's record, and the line printed for a consent carries none of them.

Runs on the Mac's own Python 3.9.6 with the standard library, and /usr/bin/openssl through
aer360_passkey.py. Nothing to install; nothing binds a port.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aer360_passkey as PK  # noqa: E402
import series as S  # noqa: E402
import tables as T  # noqa: E402
import corridor_harness as H  # noqa: E402  (the two modules import each other; H is used at call time only)

# ---------------------------------------------------------------------------
# The harness's own customer (§1): who it is, and where its two files live.
# ---------------------------------------------------------------------------
TESTER_NAME = re.compile(r"^[a-z0-9-]+$")  # the tester's name is the local part of the address, so it is confined
HARNESS_EMAIL = "harness+%s@aeredium.io"
HARNESS_DISPLAY_NAME = "%s (harness)"
HARNESS_COUNTRY = "AU"
PASSKEY_FILE = "passkey.json"  # ~/.corridor-harness/<tester>/passkey.json, mode 600
CUSTOMER_FILE = "customer.json"  # ~/.corridor-harness/<tester>/customer.json, mode 600
SEAT_SCRIPT = "tools/harness_seat.sh"

# The funding wallet the estate harness writes down at S5 (Spec T21 §5): Harness Holdings' own, a key allocated on
# the platform and held in the enclave. The path is the estate harness's store, its estate's client id, and the one
# file S5 writes; tests hold these three names to aer360_harness's and aer360_answers's own.
AER360_STORE_DIR = "~/.aer360-harness"
HARNESS_HOLDINGS = "harness-holdings"
FUNDING_WALLET_FILE = "funding-wallet.json"
ADDRESS_FORM = re.compile(r"^0x[0-9a-fA-F]{40}$")


def funding_wallet_path() -> str:
    return os.path.join(os.path.expanduser(AER360_STORE_DIR), HARNESS_HOLDINGS, FUNDING_WALLET_FILE)


# ---------------------------------------------------------------------------
# The connector's roads and words, each read from the file named beside it.
# ---------------------------------------------------------------------------
CSRF_HEADER = "x-aer-csrf"  # services/session.ts CSRF_HEADER; the cookie itself is the jar's to carry
SIGNUP_OPTIONS = "/v1/auth/signup/options"
SIGNUP_VERIFY = "/v1/auth/signup/verify"
SIGNIN_OPTIONS = "/v1/auth/signin/options"
SIGNIN_VERIFY = "/v1/auth/signin/verify"
STEPUP_OPTIONS = "/v1/auth/stepup/options"
CONSENT_ROUTE = "/v1/consent/%s"
CONSENT_CONNECT_QUERY = "connect=1"  # routes/consent.ts: "Connect a different agent" asks the server for step three
AGENT_ROUTE = "/v1/consent/%s/agent"
FINISH_ROUTE = "/v1/consent/%s/finish"
CONSENT_PAGE_QUERY = "request"  # routes/oauth.ts: the redirect carries an opaque request id and nothing else
STAGES = ("sign_in", "pay", "connected", "agent", "closed")  # routes/consent.ts, the read road
STANDING_LAPSED = "lapsed"  # services/billing.ts standingOf
SEAT_CODES = ("SUBSCRIPTION_REQUIRED", "SUBSCRIPTION_LAPSED")  # http.ts: both 402
PASSKEY_REJECTED = "PASSKEY_REJECTED"
PASSKEY_NOT_ENROLLED = "PASSKEY_NOT_ENROLLED"
# A counter that does not advance is refused by @simplewebauthn/server first ("Response counter value N was lower than
# expected M", carried in detail.cause by services/webauthn.ts) and, past it, by the connector's own check ("this passkey
# reported a signature counter that has already been used, which is what a cloned authenticator looks like").
COUNTER_REFUSAL_WORDS = ("was lower than expected", "signature counter that has already been used")
SOLO_SEATS = 3  # packages/shared/src/packages.ts PACKAGES.solo.agents
ANSWERED_STATUS = re.compile(r"answered (\d{3})")  # the status inside an Oauth road's own error sentence

# ---------------------------------------------------------------------------
# The answer book (§4), beside the figures Series C expects.
# ---------------------------------------------------------------------------
BOOK_PER_TX_USD = "20"
BOOK_DAILY_USD = "100"
BOOK_HOLD_ABOVE_USD = "50"
BOOK_CHAINS = ("arbitrum", "base")  # arbitrum first: the first chain is the home chain the child wallet is minted on
TRADER_LIST_SCOPE = "agent"
ROLES = ("trader", "payer", "payer_nogas")
# The figures series.py's restore pauses carry, read as data: "set 'per trade' back to 20 dollars" (H3, the Payer),
# "set 'per day' back to 100 dollars" (H2, the Trader), "set 'ask me first' back to 50 dollars" (C5 the Payer, D13 the Trader).
SERIES_FIGURE = re.compile(r"set '(per trade|per day|ask me first)' back to (\d+) dollars")
FIELD_OF = {"per trade": "perTxUsd", "per day": "dailyUsd", "ask me first": "holdAboveUsd"}
SPOKEN_OF = {"perTxUsd": "per trade", "dailyUsd": "per day", "holdAboveUsd": "ask me first"}

# ---------------------------------------------------------------------------
# The sentences this road can stop with (Spec T21 §1, §2, §5; the Refusals clause).
# ---------------------------------------------------------------------------
SIGNED_UP_LINE = "signed up as the harness's own customer %s; seat it with %s %s"
CONSENTED_LINE = "consented %s as the harness's own customer with its stored passkey; agent %s, rank %s; funding wallet %s; tokens stored"
SEAT_SENTENCE = "the harness is not seated%s: run %s %s on the box, then rerun"
COUNTER_SENTENCE = ("the harness's passkey counter is behind the connector's: the passkey file was not saved after a sign-in; "
                    "a new tester name is a new customer")
NO_WALLET_SENTENCE = "no wallet address of the harness's own: run aer360_harness.py first (S5 births the funding wallet and writes it down)"
CHECKSUM_SENTENCE = "the funding-wallet file at %s carries %s, whose checksum is not its own (%s); refused before any call"
LISTED_DIFFERS_SENTENCE = ("the run file's listed_address %s is not the harness's own funding wallet %s (%s): the harness lists only its own "
                           "wallet; set listed_address to it, or leave it empty to be filled, and rerun")
TESTER_NAME_SENTENCE = "the tester name %r cannot name the harness's customer: it must match [a-z0-9-]+, because it is the local part of %s"
NOT_ENROLLED_SENTENCE = ("the connector has never registered the passkey stored at %s (%s): the sign-up that made it did not "
                         "complete. Set that folder aside, or run as a new tester name, which is a new customer")
PASSKEY_FILE_SENTENCE = ("the passkey file at %s cannot be read (%s): it was not written whole. Set that folder aside, or run as a new "
                         "tester name, which is a new customer")
BOOK_DISAGREES_SENTENCE = "the answer book and series.py disagree: %s; the run stops until the two say one figure"
NO_ROLE_SENTENCE = "the connector lists no role %s for the %s; it lists %s"
NO_COUNT_SENTENCE = ("the role %s states no maxTxPerDay and the book pins none; a blank is filed as zero, which is an agent that may make "
                     "no transaction at all, so nothing was filed")
LISTED_ADDRESS_SENTENCE = "the run file's listed_address is empty, so the Payer's list cannot be written at consent"


class ConsentStop(Exception):
    """
    The consent stopped, and the sentence says what happened. `outcome` is the word the record starts with —
    `refused`, `unreachable`, `malformed`, `fault` or `stopped` — and `code`, `status` and `said` carry the
    other party's own answer where there is one. A refusal says the answer will be the same on retry.
    """

    def __init__(self, sentence: str, outcome: str = "stopped", code: Optional[str] = None, status: Optional[int] = None,
                 said: Optional[str] = None, route: Optional[str] = None):
        super().__init__(sentence)
        self.sentence = sentence
        self.outcome = outcome
        self.code = code
        self.status = status
        self.said = said
        self.route = route


def last4(value: Any) -> str:
    """A secret to its last four characters (§6), as the estate harness's record prints one."""
    text = str(value)
    return "…" + (text[-4:] if len(text) > 4 else text)


# ---------------------------------------------------------------------------
# The series' figures, and the book held against them (§4).
# ---------------------------------------------------------------------------
def series_figures() -> Dict[str, Dict[str, str]]:
    """The figures series.py restores to, per role and per field, read from its pauses as data."""
    out: Dict[str, Dict[str, str]] = {}
    for test in S.TESTS:
        for step in test.steps:
            if not isinstance(step, S.Pause):
                continue
            for what, figure in SERIES_FIGURE.findall(step.text):
                out.setdefault(step.agent, {})[FIELD_OF[what]] = figure
    return out


def book_figures(role: str) -> Dict[str, str]:
    """The three figures the book files for a role — the same three for the Trader and the Payer."""
    return {"perTxUsd": BOOK_PER_TX_USD, "dailyUsd": BOOK_DAILY_USD, "holdAboveUsd": BOOK_HOLD_ABOVE_USD}


def book_disagreements() -> List[str]:
    """Where a figure in series.py and the book disagree, one line naming both; empty where they agree."""
    out: List[str] = []
    for agent, fields in sorted(series_figures().items()):
        book = book_figures(agent)
        for field, figure in sorted(fields.items()):
            if book.get(field) != figure:
                out.append("series.py restores the %s's %s to %s dollars and the book files %s" % (
                    agent, SPOKEN_OF[field], figure, book.get(field)))
    return out


def answer_book(role: str, role_row: Dict[str, Any], run_file_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    The answers `POST /v1/consent/:id/agent` carries for a role (routes/consent.ts answersBody): the book's four,
    the role's own maxTxPerDay and assets, the book's chains, and the list — the Payer's the run file's listed
    address under the run file's scope; the Trader's list is `T.TRADER_LIST_B3`, the eight lines B3 names, so a
    Trader may trade from its first consent.
    """
    questionnaire = role_row.get("questionnaire") if isinstance(role_row.get("questionnaire"), dict) else {}
    count = questionnaire.get("maxTxPerDay")
    if count in (None, ""):
        raise ConsentStop(NO_COUNT_SENTENCE % role_row.get("id"))
    answers: Dict[str, Any] = {
        "perTxUsd": BOOK_PER_TX_USD,
        "dailyUsd": BOOK_DAILY_USD,
        "holdAboveUsd": BOOK_HOLD_ABOVE_USD,
        "maxTxPerDay": str(count),
        "chains": list(BOOK_CHAINS),
    }
    assets = questionnaire.get("assets")
    if isinstance(assets, list):  # a role that names no asset list is not asked the question (routes/consent.ts)
        answers["assets"] = [str(a) for a in assets]
    if role == "trader":
        answers["counterpartiesScope"] = TRADER_LIST_SCOPE
        answers["counterparties"] = [T.address(key) for key in T.TRADER_LIST_B3]
    else:
        listed = str(run_file_row.get("listed_address") or "").strip()
        if not listed:
            raise ConsentStop(LISTED_ADDRESS_SENTENCE)
        answers["counterpartiesScope"] = str(run_file_row.get("payer_list_scope") or "agent")
        answers["counterparties"] = [listed]
    return answers


# ---------------------------------------------------------------------------
# The funding wallet the estate harness wrote down (§5).
# ---------------------------------------------------------------------------
def funding_wallet_address(path: Optional[str] = None) -> str:
    """
    The harness's own funding wallet, checksummed, or the S5 sentence. An address written without a checksum (all one
    case, EIP-55) is checksummed and used; a mixed-case address whose checksum is not its own refuses before any call.
    """
    path = path or funding_wallet_path()
    record = H.read_json(path) if os.path.exists(path) else None
    address = str((record or {}).get("address") or "").strip() if isinstance(record, dict) else ""
    if not address:
        raise ConsentStop(NO_WALLET_SENTENCE)
    if not ADDRESS_FORM.match(address):
        raise ConsentStop(CHECKSUM_SENTENCE % (path, address, "not an address of forty hex digits"))
    checksummed = H.checksum_address(address)
    digits = address[2:]
    if digits == digits.lower() or digits == digits.upper():
        return checksummed
    if checksummed != address:
        raise ConsentStop(CHECKSUM_SENTENCE % (path, address, checksummed))
    return address


def reconcile_listed_address(run_file_row: Dict[str, Any], path: Optional[str] = None) -> Tuple[str, bool]:
    """
    Spec T21 §5: the run file's listed_address is the harness's own funding wallet. Empty, it is filled (the caller
    prints, then writes back); the same wallet in any spelling stands as it is; another address stops the run naming both.
    Returns the wallet's checksummed address and whether the row was filled.
    """
    path = path or funding_wallet_path()
    address = funding_wallet_address(path)
    listed = str(run_file_row.get("listed_address") or "").strip()
    if not listed:
        run_file_row["listed_address"] = address
        return address, True
    if listed.lower() != address.lower():
        raise ConsentStop(LISTED_DIFFERS_SENTENCE % (listed, address, path))
    return address, False


# ---------------------------------------------------------------------------
# The wire: JSON over HTTP as the page speaks it, with a cookie jar and the CSRF header, every call recorded.
# ---------------------------------------------------------------------------
class _CookieInfo:
    def __init__(self, headers: Sequence[Tuple[str, str]]):
        self._headers = list(headers)

    def get_all(self, name: str, default: Any = None) -> Any:
        found = [v for k, v in self._headers if k.lower() == name.lower()]
        return found if found else default


class _CookieResponse:
    """What http.cookiejar asks of a response: `info().get_all('Set-Cookie', [])`."""

    def __init__(self, headers: Sequence[Tuple[str, str]]):
        self._info = _CookieInfo(headers)

    def info(self) -> _CookieInfo:
        return self._info


def refusal_of(parsed: Any) -> Optional[Dict[str, Any]]:
    """The connector's refusal, {code, message, detail}, where the body carries one (http.ts ApiErrorBody)."""
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict) and parsed["error"].get("code"):
        return parsed["error"]
    return None


def cause_of(refusal: Dict[str, Any]) -> str:
    detail = refusal.get("detail")
    if isinstance(detail, dict):
        for key in ("cause", "said", "issues", "validation"):
            if detail.get(key):
                return str(detail[key])
    return ""


def connector_said(answer: "H.HttpAnswer", parsed: Any, secrets_: Sequence[str] = ()) -> str:
    """
    The connector's own words for what came back: the refusal's code, sentence and cause; an OAuth road's error and
    description; or the status and the body — every text passed through the redaction, so a sentence carries no secret.
    """
    refusal = refusal_of(parsed)
    if refusal:
        cause = cause_of(refusal)
        return "%s (%d): %s%s" % (refusal.get("code"), answer.status, H.redact(str(refusal.get("message")), secrets_, mask=last4),
                                  (" — " + H.redact(cause, secrets_, mask=last4)) if cause else "")
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), str):  # routes/oauth.ts: {error, error_description}
        return "%s (%d): %s" % (parsed["error"], answer.status, H.redact(str(parsed.get("error_description") or ""), secrets_, mask=last4))
    return "HTTP %d%s" % (answer.status, (": " + H.redact(answer.text[:300], secrets_, mask=last4)) if answer.text else "")


def query_codes_in(value: Any) -> List[str]:
    """An authorization code riding in a URL's query — the finish's `redirectTo`, a Location — so it is scrubbed by value."""
    found: List[str] = []
    if isinstance(value, dict):
        for inner in value.values():
            found.extend(query_codes_in(inner))
    elif isinstance(value, list):
        for item in value:
            found.extend(query_codes_in(item))
    elif isinstance(value, str) and "code=" in value:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(value).query)
        found.extend(c for c in query.get("code", []) if len(c) >= 8)
    return found


def classify(status: int, parsed: Any) -> str:
    """The outcome word a record starts with (the Refusals law): refused, malformed, or a fault."""
    if status in (401, 402, 403, 404, 409) or (status == 502 and refusal_of(parsed)):
        return "refused"
    if status == 400:
        return "malformed"
    return "fault"


class Wire:
    """One customer's leg of the wire: the cookie jar, the CSRF token, the secrets seen, every exchange recorded."""

    def __init__(self, issuer: str, record: Callable[..., None], secrets_: List[str], label: str = "",
                 clock: Callable[[], float] = time.monotonic):
        self.issuer = issuer.rstrip("/")
        parsed = urllib.parse.urlparse(self.issuer)
        self.origin = "%s://%s" % (parsed.scheme, parsed.netloc)  # the issuer from the run file, never pinned
        self.record = record
        self.secrets = secrets_
        self.label = label
        self.clock = clock
        self.jar = http.cookiejar.CookieJar()
        self.csrf: Optional[str] = None

    def note_secret(self, value: Any) -> None:
        if isinstance(value, str) and len(value) >= 8 and value not in self.secrets:
            self.secrets.append(value)

    def call(self, method: str, path: str, body: Any = None, follow_redirects: bool = True,
             form: Optional[Dict[str, str]] = None) -> Tuple["H.HttpAnswer", Any]:
        """
        One call as the page would make it: the jar's cookie, JSON in and out (or a form, at the token endpoint),
        `x-aer-csrf` once a session stands. Every exchange is recorded, redacted to the last four characters. A
        connector that cannot be reached stops the road as unreachable, in the transport's own words.
        """
        url = path if path.startswith("http") else self.issuer + path
        headers: Dict[str, str] = {"Accept": "application/json"}
        data: Optional[bytes] = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode("ascii")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        probe = urllib.request.Request(url, method=method)
        self.jar.add_cookie_header(probe)
        cookie = probe.get_header("Cookie")
        if cookie:
            headers["Cookie"] = cookie
        if self.csrf:
            headers[CSRF_HEADER] = self.csrf
        route = "%s %s" % (method, urllib.parse.urlparse(url).path)  # the road, never the whole link
        sent = form if form is not None else body
        started = self.clock()
        try:
            answer = H.http_request(method, url, headers, data, follow_redirects=follow_redirects)
        except H.Unreachable as err:
            self.record(test_id="consent", kind="consent", tool=route, agent=self.label, outcome="unreachable",
                        arguments=H.redact({"headers": headers, "body": sent}, self.secrets, mask=last4),
                        answer=str(err), http_status=0, round_trip_ms=int((self.clock() - started) * 1000))
            raise ConsentStop("unreachable: the connector could not be reached at %s: %s; nothing was changed, and a retry may reach it"
                              % (route, err), outcome="unreachable", route=route)
        for name, value in answer.headers.items():
            if name.lower() == "set-cookie":
                self.jar.extract_cookies(_CookieResponse([("Set-Cookie", value)]), probe)
                self.note_secret(value.split(";", 1)[0].split("=", 1)[-1])
        parsed: Any
        try:
            parsed = json.loads(answer.text) if answer.text.strip() else None
        except ValueError:
            parsed = None
        for secret in H.secret_values(parsed) + query_codes_in(parsed) + query_codes_in(dict(answer.headers)):
            self.note_secret(secret)
        outcome = "answered" if 200 <= answer.status < 300 else (
            "redirected" if 300 <= answer.status < 400 else classify(answer.status, parsed))
        self.record(test_id="consent", kind="consent", tool=route, agent=self.label, outcome=outcome,
                    arguments=H.redact({"headers": headers, "body": sent}, self.secrets, mask=last4),
                    answer=H.redact(parsed if parsed is not None else answer.text, self.secrets, mask=last4),
                    answer_headers=H.redact({k: v for k, v in answer.headers.items() if k.lower() in ("location", "set-cookie", "content-type")},
                                            self.secrets, mask=last4),
                    http_status=answer.status, round_trip_ms=answer.elapsed_ms)
        return answer, parsed


def stop_for(what: str, route: str, answer: "H.HttpAnswer", parsed: Any, secrets_: Sequence[str] = ()) -> ConsentStop:
    """
    Every catch classifies: a 401/402/403/409 (or a platform's 502 relayed) is a REFUSAL, told with the
    connector's own words and never as an outage; a 400 is a MALFORMED QUESTION of the harness's own; anything else
    is a FAULT. The other party's sentence travels unedited in `said`.
    """
    said = connector_said(answer, parsed, secrets_)
    refusal = refusal_of(parsed)
    code = refusal.get("code") if refusal else None
    kind = classify(answer.status, parsed)
    if kind == "refused":
        return ConsentStop("refused: the connector refused %s at %s — %s; the answer will be the same on retry" % (what, route, said),
                           outcome="refused", code=code, status=answer.status, said=said, route=route)
    if kind == "malformed":
        return ConsentStop("malformed: the connector could not read the harness's %s at %s — %s; the harness's question is wrong, not the connector"
                           % (what, route, said), outcome="malformed", code=code, status=answer.status, said=said, route=route)
    return ConsentStop("fault: the connector answered %s at %s with %s; nothing of the harness's was judged" % (what, route, said),
                       outcome="fault", code=code, status=answer.status, said=said, route=route)


def stop_for_road(what: str, err: Exception) -> ConsentStop:
    """An Oauth road's own error (`the token endpoint answered 400: …`, `registration answered 500: …`), classified by the status it names."""
    if isinstance(err, H.Unreachable):
        return ConsentStop("unreachable: the connector could not be reached for %s: %s; nothing was changed, and a retry may reach it" % (what, err),
                           outcome="unreachable")
    found = ANSWERED_STATUS.search(str(err))
    status = int(found.group(1)) if found else 0
    kind = classify(status, None) if status else "fault"
    if kind == "refused":
        return ConsentStop("refused: the connector refused %s — %s; the answer will be the same on retry" % (what, err), outcome="refused", status=status)
    if kind == "malformed":
        return ConsentStop("malformed: the connector could not read the harness's %s — %s; the harness's question is wrong, not the connector"
                           % (what, err), outcome="malformed", status=status)
    return ConsentStop("fault: the connector answered %s with %s; nothing of the harness's was judged" % (what, err), outcome="fault", status=status or None)


# ---------------------------------------------------------------------------
# The harness's own customer: born once, signed in with the stored passkey, stepped up per press.
# ---------------------------------------------------------------------------
def load_passkey(path: str, openssl: str = PK.OPENSSL) -> Optional[PK.SoftwarePasskey]:
    """The stored passkey, None where there is none, and a stop — never a traceback — where the file was not written whole."""
    if not os.path.exists(path):
        return None
    try:
        return PK.SoftwarePasskey.load(path, openssl)
    except (ValueError, KeyError, TypeError, PK.PasskeyError) as err:
        raise ConsentStop(PASSKEY_FILE_SENTENCE % (path, err))


def save_passkey(passkey: PK.SoftwarePasskey, path: str) -> None:
    """The one copy of the customer's key, written whole or not at all: to `<path>.tmp` (mode 600), then moved over the file."""
    partial = path + ".tmp"
    passkey.save(partial)
    os.replace(partial, path)


class HarnessCustomer:
    def __init__(self, tester: str, issuer: str, store_dir: str, record: Callable[..., None], say: Callable[[str], None],
                 secrets_: Optional[List[str]] = None, openssl: str = PK.OPENSSL, clock: Callable[[], float] = time.monotonic):
        if not TESTER_NAME.match(tester):
            raise ConsentStop(TESTER_NAME_SENTENCE % (tester, HARNESS_EMAIL % "<tester>"))
        self.tester = tester
        self.email = HARNESS_EMAIL % tester
        self.display_name = HARNESS_DISPLAY_NAME % tester
        self.folder = os.path.join(store_dir, tester)
        self.passkey_path = os.path.join(self.folder, PASSKEY_FILE)
        self.customer_path = os.path.join(self.folder, CUSTOMER_FILE)
        self.say = say
        self.openssl = openssl
        self.wire = Wire(issuer, record, secrets_ if secrets_ is not None else [], label="%s (harness)" % tester, clock=clock)
        self.passkey: Optional[PK.SoftwarePasskey] = load_passkey(self.passkey_path, openssl)
        self.customer: Optional[Dict[str, Any]] = None

    @property
    def customer_id(self) -> Optional[str]:
        if self.customer:
            return str(self.customer.get("id"))
        stored = H.read_json(self.customer_path) if os.path.exists(self.customer_path) else None
        return str(stored.get("id")) if isinstance(stored, dict) and stored.get("id") else None

    # -- the session ----------------------------------------------------------
    def sign_up_or_in(self) -> Dict[str, Any]:
        """A stored passkey is signed in with; none means the harness is born now, once."""
        if self.passkey is not None:
            return self.sign_in()
        return self.sign_up()

    def sign_up(self) -> Dict[str, Any]:
        route = "POST " + SIGNUP_OPTIONS
        begun, parsed = self.wire.call("POST", SIGNUP_OPTIONS, {"displayName": self.display_name, "email": self.email, "country": HARNESS_COUNTRY})
        if begun.status != 200 or not isinstance(parsed, dict) or not isinstance(parsed.get("options"), dict):
            raise stop_for("the sign-up's options", route, begun, parsed, self.wire.secrets)
        options = parsed["options"]
        passkey = PK.SoftwarePasskey.create_for(options, self.wire.origin, self.openssl)  # rp.id from the server's options
        passkey.base = self.wire.issuer
        passkey.created_at = H.now_iso()
        # Saved before the ceremony is sent: the file is the harness's only memory of the key the connector is about to hold.
        save_passkey(passkey, self.passkey_path)
        self.wire.note_secret(passkey.key.pem)
        registration = passkey.registration(options, self.wire.origin)
        body = {"displayName": self.display_name, "email": self.email, "country": HARNESS_COUNTRY, "handle": parsed.get("handle"),
                "nonce": parsed.get("nonce"), "issuedAtMs": parsed.get("issuedAtMs"), "response": registration}
        route = "POST " + SIGNUP_VERIFY
        done, verified = self.wire.call("POST", SIGNUP_VERIFY, body)
        if done.status != 200 or not isinstance(verified, dict) or not isinstance(verified.get("customer"), dict):
            raise stop_for("the sign-up", route, done, verified, self.wire.secrets)
        self.passkey = passkey
        self.adopt(verified)
        H.write_private(self.customer_path, {
            "id": self.customer_id, "displayName": self.display_name, "email": self.email, "country": HARNESS_COUNTRY,
            "issuer": self.wire.issuer, "signedUpAt": H.now_iso(),
        })
        self.say(SIGNED_UP_LINE % (self.customer_id, SEAT_SCRIPT, self.customer_id))
        return verified

    def sign_in(self) -> Dict[str, Any]:
        assert self.passkey is not None
        route = "POST " + SIGNIN_OPTIONS
        begun, parsed = self.wire.call("POST", SIGNIN_OPTIONS, {})
        if begun.status != 200 or not isinstance(parsed, dict) or not isinstance(parsed.get("options"), dict):
            raise stop_for("the sign-in's options", route, begun, parsed, self.wire.secrets)
        options = parsed["options"]
        body = {"nonce": parsed.get("nonce"), "issuedAtMs": parsed.get("issuedAtMs"),
                "response": self.assertion_for(str(options.get("challenge")), options.get("rpId"))}
        route = "POST " + SIGNIN_VERIFY
        done, verified = self.wire.call("POST", SIGNIN_VERIFY, body)
        if done.status != 200 or not isinstance(verified, dict) or not isinstance(verified.get("customer"), dict):
            raise self.passkey_stop("the sign-in", route, done, verified)
        self.adopt(verified)
        return verified

    def adopt(self, session: Dict[str, Any]) -> None:
        self.customer = dict(session.get("customer") or {})
        self.wire.csrf = str(session.get("csrfToken") or "") or None
        self.wire.note_secret(self.wire.csrf)

    def passkey_stop(self, what: str, route: str, answer: "H.HttpAnswer", parsed: Any) -> ConsentStop:
        """A passkey refusal, told for what it is: a counter behind the connector's, a key never enrolled, or the connector's words."""
        refusal = refusal_of(parsed) or {}
        said = connector_said(answer, parsed, self.wire.secrets)
        if refusal.get("code") == PASSKEY_REJECTED and any(w in cause_of(refusal) for w in COUNTER_REFUSAL_WORDS):
            return ConsentStop("%s (the connector said: %s)" % (COUNTER_SENTENCE, said), outcome="refused",
                               code=PASSKEY_REJECTED, status=answer.status, said=said, route=route)
        if refusal.get("code") == PASSKEY_NOT_ENROLLED:
            return ConsentStop(NOT_ENROLLED_SENTENCE % (self.passkey_path, said), outcome="refused",
                               code=PASSKEY_NOT_ENROLLED, status=answer.status, said=said, route=route)
        return stop_for(what, route, answer, parsed, self.wire.secrets)

    # -- the assertion, with the counter saved BEFORE it is sent ---------------
    def assertion_for(self, challenge: str, rp_id: Optional[str] = None) -> Dict[str, Any]:
        """
        The counter is advanced and the passkey file saved BEFORE the assertion leaves, so a run that dies on the wire
        never resends a counter the connector has seen; an assertion is never sent twice, and each press gets a fresh one.
        """
        assert self.passkey is not None
        self.passkey.sign_count += 1
        save_passkey(self.passkey, self.passkey_path)
        response = self.passkey.assertion(challenge, rp_id=rp_id or self.passkey.rp_id, origin=self.wire.origin, count=False)
        self.wire.note_secret(response["response"].get("signature"))
        return response

    def step_up(self) -> Dict[str, Any]:
        """A fresh assertion under the purpose `approve` (auth.ts), for the one press that creates an agent."""
        route = "POST " + STEPUP_OPTIONS
        begun, parsed = self.wire.call("POST", STEPUP_OPTIONS, {})
        if begun.status != 200 or not isinstance(parsed, dict) or not isinstance(parsed.get("options"), dict):
            raise stop_for("the step-up's options", route, begun, parsed, self.wire.secrets)
        options = parsed["options"]
        return {"nonce": parsed.get("nonce"), "issuedAtMs": parsed.get("issuedAtMs"),
                "response": self.assertion_for(str(options.get("challenge")), options.get("rpId"))}


# ---------------------------------------------------------------------------
# The consent, walked by software for one label (§3).
# ---------------------------------------------------------------------------
def request_id_of(location: str) -> Optional[str]:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
    values = query.get(CONSENT_PAGE_QUERY) or []
    return values[0] if values else None


def code_and_state_of(redirect_to: str) -> Tuple[Optional[str], Optional[str]]:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_to).query)
    return (query.get("code") or [None])[0], (query.get("state") or [None])[0]


def seat_sentence(customer_id: Optional[str], standing: Optional[str]) -> str:
    """One sentence, one command, no link (§2). The pay stage states no date, so a lapsed seat is named and not dated."""
    why = " (its seat lapsed)" if standing == STANDING_LAPSED else ""
    return SEAT_SENTENCE % (why, SEAT_SCRIPT, customer_id or "<customer-id>")


class Consent:
    """
    The road, for one tester: sign in (or up), authorize, read the stage, press what the stage offers, finish,
    exchange the code, store the tokens where the harness stores them today.
    """

    def __init__(self, customer: HarnessCustomer, oauth: "H.Oauth", run_file_row: Dict[str, Any], say: Callable[[str], None],
                 funding_wallet: Optional[str] = None):
        self.customer = customer
        self.oauth = oauth
        self.row = run_file_row
        self.say = say
        self.funding_wallet = funding_wallet  # the path of the estate harness's file; None means the default

    def consent(self, role: str, label: str) -> Dict[str, Any]:
        if role not in ROLES:
            raise ConsentStop("no role called %s: the labels are %s" % (role, ", ".join(ROLES)))
        disagreements = book_disagreements()
        if disagreements:
            raise ConsentStop(BOOK_DISAGREES_SENTENCE % "; ".join(disagreements))
        funding_address = funding_wallet_address(self.funding_wallet)  # refuses before any call
        self.customer.sign_up_or_in()
        wire = self.customer.wire
        try:
            meta = self.oauth.metadata()
            client = self.oauth.client()
        except H.HarnessError as err:  # the discovery or the registration, the Oauth road's own calls
            raise stop_for_road("the discovery or the client registration", err)
        verifier, challenge = H.pkce_pair()
        state = secrets.token_urlsafe(24)
        wire.note_secret(verifier)
        redirect_uri = str(client["redirect_uri"])  # the registered loopback; any loopback port matches, and none is bound
        link = self.oauth.authorization_link(client["client_id"], redirect_uri, challenge, state)
        route = "GET /authorize"
        opened, parsed = wire.call("GET", link, follow_redirects=False)
        location = next((v for k, v in opened.headers.items() if k.lower() == "location"), None)
        request_id = request_id_of(location) if opened.status in (302, 303, 307) and location else None
        if not request_id:
            if opened.status in (302, 303, 307) and location:
                raise ConsentStop("refused: the authorize road sent the harness to %s instead of the consent page: %s" % (
                    H.redact(location, wire.secrets, mask=last4), self.oauth_error_of(location)), outcome="refused", route=route, status=opened.status)
            raise stop_for("the authorize request", route, opened, parsed, wire.secrets)
        stage_answer, stage = wire.call("GET", CONSENT_ROUTE % request_id + "?" + CONSENT_CONNECT_QUERY)
        if stage_answer.status != 200 or not isinstance(stage, dict) or stage.get("stage") not in STAGES:
            raise stop_for("the consent's stage", "GET " + CONSENT_ROUTE % ":id", stage_answer, stage, wire.secrets)
        word = str(stage["stage"])
        if word == "pay":
            subscription = stage.get("subscription") if isinstance(stage.get("subscription"), dict) else {}
            raise ConsentStop(seat_sentence(self.customer.customer_id, subscription.get("standing")),
                              outcome="refused", code="SUBSCRIPTION_REQUIRED" if subscription.get("standing") != STANDING_LAPSED else "SUBSCRIPTION_LAPSED",
                              status=stage_answer.status, route="GET " + CONSENT_ROUTE % ":id")
        if word == "sign_in":
            raise ConsentStop("fault: the connector answered stage sign_in to the harness's signed-in session at GET %s; the cookie did not carry"
                              % (CONSENT_ROUTE % request_id), outcome="fault", route="GET " + CONSENT_ROUTE % ":id")
        if word == "closed":
            closed = stage.get("closed") if isinstance(stage.get("closed"), dict) else {}
            raise ConsentStop("refused: the connection request is %s — %s" % (closed.get("state"), closed.get("said")),
                              outcome="refused", route="GET " + CONSENT_ROUTE % ":id")
        if word != "agent":
            raise ConsentStop("fault: the connector answered stage %s to a read asking for step three (?%s)" % (word, CONSENT_CONNECT_QUERY),
                              outcome="fault", route="GET " + CONSENT_ROUTE % ":id")
        role_id = S.ROLE_IDS[role]
        roles = [r for r in (stage.get("roles") or []) if isinstance(r, dict)]
        role_row = next((r for r in roles if r.get("id") == role_id), None)
        if role_row is None:
            raise ConsentStop(NO_ROLE_SENTENCE % (role_id, role, ", ".join(str(r.get("id")) for r in roles) or "none"))
        rank = str(role_row.get("defaultRank") or "agent")
        agents = [a for a in (stage.get("agents") or []) if isinstance(a, dict)]
        standing = next((a for a in agents if a.get("name") == label), None)
        finish_route = "POST " + FINISH_ROUTE % ":id"
        agent_id: Optional[str]
        answers: Optional[Dict[str, Any]] = None  # the book's answers where this consent creates the agent; a hand-over files none
        if standing is not None and standing.get("connectionId"):
            body: Dict[str, Any] = {"connectionId": standing["connectionId"], "rank": rank}
            agent_id = str(standing.get("id"))
            how = "handed over the connection it already holds"
        elif standing is not None:
            body = {"agentId": standing["id"]}  # Spec 35's first connection; never {agentId} where a connection stands
            agent_id = str(standing.get("id"))
            how = "connected for the first time"
        else:
            if len(agents) >= SOLO_SEATS:
                self.say("Note: %d agents stand on the harness's customer and Solo seats %d; the connector decides what happens to a %dth."
                         % (len(agents), SOLO_SEATS, len(agents) + 1))
            answers = answer_book(role, role_row, self.row)
            stepped = self.customer.step_up()
            press = {"name": label, "roleId": role_id, "fundingAddress": funding_address, "rank": rank, "answers": answers}
            press.update(stepped)
            pressed, receipt = wire.call("POST", AGENT_ROUTE % request_id, press)
            if pressed.status != 200 or not isinstance(receipt, dict) or not isinstance(receipt.get("receipt"), dict):
                refusal = refusal_of(receipt) or {}
                if refusal.get("code") in SEAT_CODES:
                    raise ConsentStop(seat_sentence(self.customer.customer_id, STANDING_LAPSED if refusal.get("code") == "SUBSCRIPTION_LAPSED" else None),
                                      outcome="refused", code=str(refusal.get("code")), status=pressed.status,
                                      said=connector_said(pressed, receipt, wire.secrets), route="POST " + AGENT_ROUTE % ":id")
                if refusal.get("code") == PASSKEY_REJECTED:
                    raise self.customer.passkey_stop("the agent press", "POST " + AGENT_ROUTE % ":id", pressed, receipt)
                raise stop_for("the agent press for %s" % label, "POST " + AGENT_ROUTE % ":id", pressed, receipt, wire.secrets)
            connection = (receipt["receipt"].get("connection") or {}) if isinstance(receipt["receipt"].get("connection"), dict) else {}
            created = receipt["receipt"].get("agent") if isinstance(receipt["receipt"].get("agent"), dict) else {}
            if not connection.get("id"):
                raise ConsentStop("fault: the agent press answered a receipt with no connection id for %s" % label, outcome="fault",
                                  route="POST " + AGENT_ROUTE % ":id")
            body = {"connectionId": connection["id"]}
            agent_id = str(created.get("id"))
            how = "created with the book's answers"
        finished, done = wire.call("POST", FINISH_ROUTE % request_id, body)
        if finished.status != 200 or not isinstance(done, dict) or not done.get("redirectTo"):
            refusal = refusal_of(done) or {}
            if refusal.get("code") in SEAT_CODES:
                raise ConsentStop(seat_sentence(self.customer.customer_id, STANDING_LAPSED if refusal.get("code") == "SUBSCRIPTION_LAPSED" else None),
                                  outcome="refused", code=str(refusal.get("code")), status=finished.status,
                                  said=connector_said(finished, done, wire.secrets), route=finish_route)
            raise stop_for("the finish for %s" % label, finish_route, finished, done, wire.secrets)
        code, came_state = code_and_state_of(str(done["redirectTo"]))
        wire.note_secret(code)
        if came_state != state:
            raise ConsentStop("fault: the finish came back with a state the harness did not send; nothing was exchanged", outcome="fault", route=finish_route)
        if not code:
            raise ConsentStop("fault: the finish came back without a code in redirectTo", outcome="fault", route=finish_route)
        # The exchange, through the same wire so the record carries it: the code and the verifier ride redacted.
        exchanged, tokens = wire.call("POST", str(meta["token_endpoint"]), form={
            "grant_type": "authorization_code", "client_id": str(client["client_id"]), "code": code,
            "code_verifier": verifier, "redirect_uri": redirect_uri,
        })
        if exchanged.status != 200 or not isinstance(tokens, dict) or not tokens.get("access_token"):
            said = connector_said(exchanged, tokens, wire.secrets)
            raise ConsentStop("refused: the token endpoint refused the code for %s — %s; the answer will be the same on retry" % (label, said),
                              outcome="refused", status=exchanged.status, said=said, route="POST /token")
        for value in (tokens.get("access_token"), tokens.get("refresh_token")):
            wire.note_secret(value)
        extra: Dict[str, Any] = {
            "customer_id": self.customer.customer_id, "agent_id": agent_id, "agent_name": label, "rank": body.get("rank") or rank,
            "funding_address": funding_address, "consented_at": H.now_iso(),
            "consented_by": "the harness's own passkey (Spec T21), %s" % how,
        }
        if answers is not None:
            # Spec T22 §1: the addresses the harness filed, so the harness can read what it filed (B3 reads them before it waits).
            extra["counterparties"] = list(answers["counterparties"])
        stored = self.oauth.store_tokens(label, tokens, str(client["client_id"]), extra=extra)
        self.say(CONSENTED_LINE % (label, agent_id, rank, funding_address))
        return stored

    @staticmethod
    def oauth_error_of(location: str) -> str:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
        return "%s — %s" % ((query.get("error") or ["no error named"])[0], (query.get("error_description") or [""])[0])


def consent(role: str, label: str, tester: str, issuer: str, store_dir: str, run_file_row: Dict[str, Any],
            record: Callable[..., None], say: Callable[[str], None], oauth: Optional["H.Oauth"] = None,
            secrets_: Optional[List[str]] = None, funding_wallet: Optional[str] = None, openssl: str = PK.OPENSSL) -> Dict[str, Any]:
    """The one call corridor_harness makes: consent this label as the harness's own customer, and store its tokens."""
    customer = HarnessCustomer(tester, issuer, store_dir, record, say, secrets_=secrets_, openssl=openssl)
    road = Consent(customer, oauth or H.Oauth(issuer, store_dir, say=say), run_file_row, say, funding_wallet=funding_wallet)
    return road.consent(role, label)
