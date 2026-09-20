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
# Where an invitation's seconds go (Spec T8): routes/invites.ts mints the invitation, awaits the email's
# dispatch (attemptDispatch), stamps the row, and only then answers 201. A fact to report, not a finding.
INVITATION_SENDS_FIRST = "the invitation road sends the email before it answers, which is where its four seconds go"
# The report's name in the working folder: aer360-harness-<date>.md, and -<HHMMSS> for a later one the same day.
REPORT_NAME = re.compile(r"^aer360-harness-(\d{4}-\d{2}-\d{2})(?:-(\d{6}))?\.md$")

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


def now_ms() -> int:
    return int(time.time() * 1000)


def now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


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
                 retry_of: Optional["Call"] = None):
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
                 openssl: str = PK.OPENSSL):
        self.base = base.rstrip("/")
        parsed = urllib.parse.urlparse(self.base)
        self.origin = "%s://%s" % (parsed.scheme, parsed.netloc)
        self.store_dir = store_dir
        self.estate_dir = os.path.join(store_dir, A.ESTATE["client_id"])
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
        if invite:
            try:
                self.secrets.add(token_of_link(invite))
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
            "payees": [], "payees_register": None, "sets": {}, "sets_register": None,
            "journey": {}, "readiness": None, "workspace": None, "wallets": None, "charter_standing": None,
            "served_twice": {"policy": [], "wallet_account": []},
        }
        self.started_at = now_iso()
        self.last_run_report: Optional[Dict[str, Any]] = None
        self._last_run_looked_for = False
        # The run's own mark, in every idempotency key it sends: the clock to the second and four
        # random hex digits, so two runs a second apart never share a key.
        self.run_stamp = "%s-%s" % (_dt.datetime.now().strftime("%Y%m%d-%H%M%S"), secrets.token_hex(2))

    # -- the store ----------------------------------------------------------------
    def key_path(self, person: Person) -> str:
        return os.path.join(self.estate_dir, "%s.json" % person.key)

    def load_passkeys(self) -> None:
        for person in self.people.values():
            stored = PK.SoftwarePasskey.load(self.key_path(person), self.openssl)
            if stored is None:
                continue
            if stored.base and stored.base != self.base:
                self.say("Note: the passkey stored for %s at %s was enrolled at %s, not %s; it is left alone and not used." % (
                    person.name, self.key_path(person), stored.base, self.base))
                continue
            person.passkey = stored

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
        person.passkey.save(self.key_path(person))

    # -- the wire -----------------------------------------------------------------
    def request(self, person: Optional[Person], method: str, path: str, body: Any = None, station: str = "",
                csrf: bool = True, headers: Optional[Dict[str, str]] = None, who: Optional[str] = None) -> Answer:
        """
        One call as the browser would make it: the person's cookie jar, JSON in and out, the session's
        x-csrf-token on every state-changing request (guards.ts). A 5xx is retried once after two seconds
        and both answers are kept (S12). Everything is recorded, redacted.
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
        who_said = who or (person.name if person else "nobody (no session)")
        call = self.record(station, who_said, method, path, body, answer)
        if 500 <= answer.status < 600:
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

    def record(self, station: str, who: str, method: str, path: str, body: Any, answer: Answer,
               retry_of: Optional[Call] = None) -> Call:
        parsed = answer.json
        if isinstance(parsed, dict):
            for key in ("csrfToken", "token"):
                if isinstance(parsed.get(key), str):
                    self.secrets.add(parsed[key])
            if isinstance(parsed.get("url"), str) and "#" in parsed["url"]:
                self.secrets.add(parsed["url"].split("#", 1)[1])
        redacted_text = self.secrets.redact_text(answer.text) if parsed is None else json.dumps(self.secrets.redact(parsed), ensure_ascii=False)
        redacted_answer = Answer(method, path, answer.status, answer.headers, redacted_text, answer.elapsed_ms)
        call = Call(station, who, method, path, self.secrets.redact(body), redacted_answer, now_iso(), retry_of)
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
            self.step("S1", verified, "200 with a session in the workspace %s" % A.ESTATE["company"],
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
        if name.strip().lower() != A.ESTATE["company"].lower():
            raise StationStop("%s; the session names the workspace %r, not %r" % (how, name, A.ESTATE["company"]))
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
            value = A.answer_for(interview_type, question)
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

    def confirm_and_compile(self, station: str, interview_type: str, interview_id: str, who: Person, page: Dict[str, Any]) -> Dict[str, Any]:
        state = page.get("state")
        if state == "at_read_back":
            readback = self.request(who, "GET", "/v1/onboarding/interviews/%s/readback" % interview_id, None, station)
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
            self.step(station, confirmed, "200 with the interview confirmed", "confirmed" if confirmed.ok else confirmed.sentence(), body, who.name)
            if not confirmed.ok:
                raise StationStop("POST confirm answered %s" % confirmed.sentence())
            state = "confirmed"
        if state in ("confirmed", "compiled"):
            compiled = self.request(who, "POST", "/v1/onboarding/interviews/%s/compile" % interview_id, {}, station)
            self.step(station, compiled, "200 with the compiled charter, the write receipt and the seat",
                      "compiled and written" if compiled.ok else compiled.sentence(), {}, who.name)
            if not compiled.ok or not isinstance(compiled.json, dict):
                raise StationStop("POST compile answered %s" % compiled.sentence())
            self.facts["compile"][interview_type] = compiled.json
            self.facts["charter"][interview_type] = compiled.json.get("charter") or {}
            return compiled.json
        raise StationStop("the interview stands in state %r after its questions; the read-back was not reached" % state)

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

    def station_s4(self) -> Outcome:
        founder = self.founder()
        said: List[str] = []
        for key in A.AUTHORS_INVITED:
            person = self.people[key]
            said.append("%s %s" % (person.name, self.bring_in("S4", person, "author")))
        seats = self.request(founder, "GET", "/v1/approver-seats", None, "S4")
        self.step("S4", seats, "the charter's approver seats and where each stands", "answered" if seats.ok else seats.sentence(), None, founder.name)
        self.facts["seats"] = seats.json if isinstance(seats.json, dict) else None
        ada = self.people[A.PAYMENT_APPROVER]
        seat_said = "no seats view"
        if isinstance(seats.json, dict):
            row = next((s for s in seats.json.get("seats") or [] if str(s.get("email", "")).lower() == ada.email.lower()), None)
            seat_said = "Ada's seat %s" % (row.get("state") if row else "not in the charter's seats")
            if row and row.get("state") == "enrolled_not_seated":
                granted = self.request(founder, "POST", "/v1/approver-seats/grant", {"email": ada.email}, "S4")
                self.step("S4", granted, "the seats view with Ada seated", "answered" if granted.ok else granted.sentence(), {"email": ada.email}, founder.name)
                if granted.ok and isinstance(granted.json, dict):
                    self.facts["seats"] = granted.json
                    row = next((s for s in granted.json.get("seats") or [] if str(s.get("email", "")).lower() == ada.email.lower()), None)
                    seat_said = "Ada's seat granted by the founder: %s" % (row.get("state") if row else "not in the seats")
                else:
                    seat_said = "Ada's seat grant answered %s" % granted.sentence()
        register = self.request(founder, "GET", "/v1/invites", None, "S4")
        self.step("S4", register, "the invitation register: who was invited, as what, and how it went", "answered" if register.ok else register.sentence(), None, founder.name)
        self.facts["invites_register"] = register.json if isinstance(register.json, dict) else None
        rows = (register.json or {}).get("invites") if isinstance(register.json, dict) else None
        detail = "people: %s; %s; %s invitation(s) in the register" % ("; ".join(said), seat_said, len(rows) if isinstance(rows, list) else "?")
        if all(self.people[k].signed_in for k in A.AUTHORS_INVITED):
            return Outcome("S4", PASS, detail)
        return Outcome("S4", FAIL, detail)

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
        if not isinstance(current, int) or current < 3:
            return Outcome("S5", FAIL, detail + "; expected stage 3 of %d, working_the_sandbox" % JOURNEY_STAGE_COUNT)
        if current > 3:
            detail += " (beyond stage 3: this estate had walked further before this run)"
        return Outcome("S5", PASS, detail)

    # -- S6 Payees ----------------------------------------------------------------------
    def station_s6(self) -> Outcome:
        founder = self.founder()
        ada = self.people[A.PAYMENT_APPROVER]
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
            record = {"key": payee["key"], "name": payee["name"], "payee_id": row.get("id"), "address_id": address_id, "address": address, "chain": payee["chain"], "promoted": None, "approved": None}
            self.facts["payees"].append(record)
            if not address_id:
                said.append("%s: created with no address id" % payee["name"])
                all_whitelisted = False
                continue
            promoted = self.request(founder, "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, "S6")
            self.step("S6", promoted, "the platform's answer: status, membership id, ceremony", "answered" if promoted.ok else promoted.sentence(), {}, founder.name)
            record["promoted"] = promoted.json if promoted.ok else promoted.sentence()
            approve_said = "Ada has no session, so the approval was not asked"
            if ada.signed_in:
                approved = self.request(ada, "POST", "/v1/payees/addresses/%s/approve" % address_id, {}, "S6")
                self.step("S6", approved, "whitelistStatus whitelisted", "answered" if approved.ok else approved.sentence(), {}, ada.name)
                record["approved"] = approved.json if approved.ok else approved.sentence()
                approve_said = ("approved by Ada: %s" % (approved.json or {}).get("whitelistStatus")) if approved.ok else ("Ada's approval answered %s" % approved.sentence())
            said.append("%s: %s; promote %s; %s" % (payee["name"], "created", ("status %s" % (promoted.json or {}).get("status")) if promoted.ok else promoted.sentence(), approve_said))
        register = self.request(founder, "GET", "/v1/payees", None, "S6")
        self.step("S6", register, "the payees register with both addresses whitelisted", "answered" if register.ok else register.sentence(), None, founder.name)
        self.facts["payees_register"] = register.json if isinstance(register.json, dict) else None
        statuses: Dict[str, str] = {}
        if isinstance(register.json, dict):
            for row in register.json.get("payees") or []:
                for addr in row.get("addresses") or []:
                    statuses[str(addr.get("address", "")).lower()] = str(addr.get("whitelistStatus"))
        for record in self.facts["payees"]:
            status = statuses.get(record["address"].lower(), "absent from the register")
            record["register_status"] = status
            if status != "whitelisted":
                all_whitelisted = False
        detail = "payees: %s; register: %s" % ("; ".join(said), ", ".join("%s %s" % (r["name"], r.get("register_status")) for r in self.facts["payees"]) or "none")
        return Outcome("S6", PASS if all_whitelisted and self.facts["payees"] else FAIL, detail)

    # -- S7 Payments --------------------------------------------------------------------
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

    def station_s7(self) -> Outcome:
        clerk = self.clerk()
        ada = self.people[A.PAYMENT_APPROVER]
        workspace = self.request(clerk, "GET", "/v1/workspace", None, "S7")
        self.step("S7", workspace, "the workspace, its funding account (sourceAccount) and the offered currencies", "answered" if workspace.ok else workspace.sentence(), None, clerk.name)
        source_account = (workspace.json or {}).get("sourceAccount") if isinstance(workspace.json, dict) else None
        if not source_account:
            self.note("S7", "the workspace names no funding account (sourceAccount null); the founder's browser offers no control for one, and routes/sets.ts refuses a run without it — the payments below record the estate's own sentence")
        said: List[str] = []
        failures = 0
        for payment in A.PAYMENTS:
            row = self.pay_row(payment)
            if row is None:
                said.append("%s: no address id for %s, so nothing was sent" % (payment.key, payment.payee_name))
                failures += 1
                continue
            review_body = {"pays": [row], "duplicatesAcknowledged": False}
            review = self.request(clerk, "POST", "/v1/sets/review", review_body, "S7")
            self.step("S7", review, "the gates' review of the run before anything is created", "answered" if review.ok else review.sentence(), review_body, clerk.name)
            create_body = dict(review_body)
            create_body.update({"idempotencyKey": "aer360-harness-%s-%s" % (self.run_stamp, payment.key), "reference": "Harness payment %s" % payment.key})
            created = self.request(clerk, "POST", "/v1/sets", create_body, "S7")
            self.step("S7", created, "201 with the run in draft and its review", "created" if created.ok else created.sentence(), create_body, clerk.name)
            record: Dict[str, Any] = {"key": payment.key, "expect": payment.expect, "review": review.json if review.ok else review.sentence(),
                                      "created": created.json if created.ok else None, "refusal": None if created.ok else created.sentence(),
                                      "submitted": None, "view": None, "approval": None}
            self.facts["sets"][payment.key] = record
            if not created.ok or not isinstance(created.json, dict):
                said.append("%s (%s, expected to %s): refused at creation — %s" % (payment.key, payment.amount, payment.expect, created.sentence()))
                failures += 1
                continue
            set_id = str((created.json.get("set") or {}).get("id"))
            record["set_id"] = set_id
            submitted = self.request(clerk, "POST", "/v1/sets/%s/submit" % set_id, {}, "S7")
            self.step("S7", submitted, "status pending_approval (or approved where the policy asks no second hand), the digest, approvalsRequired",
                      "answered" if submitted.ok else submitted.sentence(), {}, clerk.name)
            record["submitted"] = submitted.json if submitted.ok else submitted.sentence()
            view = self.request(clerk, "GET", "/v1/sets/%s" % set_id, None, "S7")
            self.step("S7", view, "the run as the register shows it", "answered" if view.ok else view.sentence(), None, clerk.name)
            record["view"] = view.json if view.ok else view.sentence()
            set_view = (view.json or {}).get("set") if isinstance(view.json, dict) else None
            status = str((set_view or {}).get("status") or (submitted.json or {}).get("status") if submitted.ok else submitted.sentence())
            required = ((set_view or {}).get("approval") or {}).get("approvalsRequired")
            verdict, sentence = self.judge_payment(payment, status, required, submitted.ok)
            if verdict == FAIL:
                failures += 1
            said.append("%s (%s USDC, expected to %s): %s" % (payment.key, payment.amount, payment.expect, sentence))
            if payment.key == "P1":
                said.append(self.approve_first(record, set_id, status, ada))
        detail = "payments as %s: %s" % (clerk.name, "; ".join(said))
        return Outcome("S7", FAIL if failures else PASS, detail)

    @staticmethod
    def judge_payment(payment: A.Payment, status: str, required: Any, submitted_ok: bool) -> Tuple[str, str]:
        """The spec's expectation against the estate's own words for the run's state."""
        waits = status == "pending_approval" and isinstance(required, int) and required >= 1
        if payment.expect == "proceeds to approval":
            if status in ("pending_approval", "approved"):
                return PASS, "created and submitted; status %s, approvalsRequired %s" % (status, required)
            return FAIL, "status %s, approvalsRequired %s" % (status, required)
        if payment.expect in ("waits", "held"):
            if waits:
                return PASS, "the run waits for approval: status %s, approvalsRequired %s" % (status, required)
            if status == "approved":
                return FAIL, "the sandbox approved it at submission: status approved, approvalsRequired %s" % required
            return FAIL, "status %s, approvalsRequired %s" % (status, required)
        return FAIL, "status %s" % status

    def approve_first(self, record: Dict[str, Any], set_id: str, status: str, ada: Person) -> str:
        if status != "pending_approval":
            return "Ada's approval of P1 was not asked: the run stands %s" % status
        if not ada.signed_in:
            return "Ada's approval of P1: Ada has no session"
        challenge = self.request(ada, "POST", "/v1/approvals/%s/challenge" % set_id, {}, "S7")
        self.step("S7", challenge, "the digest-bound challenge Ada's passkey signs", "answered" if challenge.ok else challenge.sentence(), {}, ada.name)
        if not challenge.ok or not isinstance(challenge.json, dict):
            record["approval"] = challenge.sentence()
            return "Ada's approval of P1: the challenge answered %s" % challenge.sentence()
        body = {"response": self.assertion_for(ada, str(challenge.json.get("challenge")), "S7")}
        approved = self.request(ada, "POST", "/v1/approvals/%s/approve" % set_id, body, "S7")
        self.step("S7", approved, "status approved, approvalsGiven 1 of 1", "answered" if approved.ok else approved.sentence(), body, ada.name)
        record["approval"] = approved.json if approved.ok else approved.sentence()
        if approved.ok and isinstance(approved.json, dict):
            return "Ada approved P1: status %s, approvals %s of %s" % (approved.json.get("status"), approved.json.get("approvalsGiven"), approved.json.get("approvalsRequired"))
        return "Ada's approval of P1 answered %s" % approved.sentence()

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
        return Outcome("S8", PASS, "journey stage %s of %s (%s); done: %s; readiness: transactable %s, reason %s" % (
            current, view.get("stageCount"), current_id, ", ".join(done) or "none", readiness.json.get("transactable"), readiness.json.get("reason")))

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
            if readback and answers:
                for f in audit_readback(interview_type, answers, readback.get("lines") or []):
                    if f.get("not_compared"):
                        self.note("S10", "%s: %s" % (f["probe"], f["said"]))
                    else:
                        self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            else:
                self.note("S10", "no read-back and answers recorded for the %s interview in this run; the read-back comparison was not made" % interview_type)
            charter = self.facts["charter"].get(interview_type)
            if charter and answers:
                for f in audit_charter(interview_type, charter, {q: v for q, v, _, _ in answers}):
                    self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            elif answers:
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
            for f in audit_people(self.facts.get("invites_register"), self.facts["invites_minted"], {k: p.credential_id for k, p in self.people.items() if p.signed_in}):
                self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
            for f in audit_payees(self.facts.get("payees_register"), self.facts["payees"], self.facts["charter"].get("wallet_account")):
                self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
        else:
            self.note("S10", "the founder has no session; the registers were not read again")
        for f in audit_money(self.calls):
            self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
        for f in audit_refusals(self.calls):
            self.finding("S10", f["probe"], f["sent"], None, f["expected"], f["said"])
        found = len(self.findings) - before
        refusals_met = len([c for c in self.calls if c.status >= 400 and c.station not in ("S10", "S11")])
        return Outcome("S10", PASS if found == 0 else FAIL, "the auditor: %d finding(s); %d refusal(s) met in S1 to S9 checked for Rule 13; %d call(s) checked for the minor-unit law" % (
            found, refusals_met, len(self.calls)))

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

    def probe_venue_contract(self, founder: Person) -> None:
        """
        S11's venue probe: a payee whose address is a real venue contract, read from the corridor's tables.py at
        run time and never from a table of the harness's own.

        THE EXPECTATION IS ACCEPTANCE (Spec T8). The first live run, 20 September 2026, called the estate's
        HTTP 201 a failure; Bear ruled the same morning: "Unless it is stipulated explicitly in the questionnaire,
        it must be accepted." The questionnaire decides policy, and a contract is an address — no question of the
        charter asks whether a venue contract may be a payee, so the estate has nothing to refuse it under, and
        an estate that accepted it did what the law says. The probe stays, because the expectation FLIPS the day
        the questionnaire gains such a stipulation: then a refusal in the charter's words is what the law says,
        and an acceptance becomes the finding. Until that day HTTP 201 is reported as accepted, as the law says,
        and a refusal is the finding, with the ruling quoted beside the estate's own sentence.
        """
        venue = T.venue_address_for_probe()
        probe = "a payee address that is a real venue contract (%s, read from the corridor's tables.py at run time)" % venue["what"]
        body = {"displayName": "Venue probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": venue["address"]}]}
        answer = self.request(founder, "POST", "/v1/payees", body, "S11")
        expected = "HTTP 201: accepted, as the law says (%s)" % VENUE_RULING
        result = ("accepted, as the law says (%s)" % VENUE_RULING) if answer.ok else "refused: %s" % answer.sentence()
        self.probe_step(probe, answer, body, expected, founder.name, result=result)
        self.accepted_or_finding(probe, body, answer, expected, "the law says otherwise (%s; a contract is an address)" % VENUE_RULING)

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
        # venue contract (acceptance expected: the questionnaire decides policy, and a contract is an address).
        probes += 1
        probe = "a payee address with a wrong checksum"
        broken = T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))
        body = {"displayName": "Checksum probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": broken}]}
        answer = self.request(founder, "POST", "/v1/payees", body, "S11")
        self.probe_step(probe, answer, body, "a refusal (ADDRESS_MALFORMED), or the estate's acceptance recorded as it is", founder.name)
        self.refused_or_finding(probe, body, answer, "refused: an address whose checksum is wrong is not an address")
        probes += 1
        self.probe_venue_contract(founder)  # expects acceptance, as the law says (Spec T8); a refusal is the finding
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
        return "US$%s and %02d cents." % ("{:,}".format(whole), frac)
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
    return [{"probe": probe, "sent": value, "expected": expected, "said": "the read-back says %r" % said}]


def audit_readback(interview_type: str, answers: Sequence[Tuple[str, Dict[str, Any], str, str]], lines: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    The read-back compared with the answers the harness gave, by content (Spec T8): each answer rendered in the
    estate's own spoken form (spoken_for) and compared with the line the estate spoke, a list entry by entry so a
    finding names the entry. An answer of a kind the harness has no rendering for is not compared: its entry
    carries not_compared=True and says so, and S10 records it as a note, never a finding. A line for a question
    the harness did not answer, a missing line, and a moved prompt are findings as before.
    """
    findings: List[Dict[str, Any]] = []
    spoken = {str(l.get("questionId")): l for l in lines if not l.get("synthetic")}
    for qid, value, prompt, kind in answers:
        expected = spoken_for(kind, qid, value)
        line = spoken.get(qid)
        probe = "read-back (%s) of %s" % (interview_type, qid)
        if line is None:
            findings.append({"probe": probe, "sent": value, "expected": expected if expected is not None else json.dumps(value, ensure_ascii=False),
                             "said": "the read-back has no line for %s, which was answered" % qid})
            continue
        said = str(line.get("spoken"))
        if expected is None:
            findings.append({"probe": probe, "sent": value, "expected": None, "not_compared": True,
                             "said": "not compared: no rendering for kind %s (the read-back says %r)" % (kind, said)})
        elif said != expected:
            findings.extend(readback_disagreements(probe, kind, value, expected, said))
        if prompt and str(line.get("prompt")) != prompt:
            findings.append({"probe": probe + " (the prompt)", "sent": prompt, "expected": prompt, "said": "the read-back's prompt is %r" % line.get("prompt")})
    answered = {qid for qid, _, _, _ in answers}
    for qid in spoken:
        if qid not in answered:
            findings.append({"probe": "read-back (%s) of %s" % (interview_type, qid), "sent": None, "expected": "no line for a question the harness did not answer",
                             "said": "the read-back carries a line for %s, which the harness did not answer: %r" % (qid, spoken[qid].get("spoken"))})
    return findings


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
    else:
        expect("the name (WN)", text("WN"), charter.get("name"), text("WN"))
        expect("the purpose (W1)", choice("W1"), charter.get("purpose"), choice("W1"))
        expect("the release quorum (WQ)", int(choice("WQ")) if choice("WQ") else None, charter.get("quorum"), choice("WQ"))
        signers = ["%s <%s>" % (e.get("name", "").strip(), e.get("email", "").strip()) if e.get("name", "").strip() else e.get("email", "").strip()
                   for e in entries("WA1") if e.get("email", "").strip()]
        expect("the signers (WA1)", signers, charter.get("signers"), entries("WA1"))
        purpose = choice("W1") or ""
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
    """Every money figure the server returned, checked against the minor-unit law (money.ts): an integer string of minor units, never a float."""
    findings: List[Dict[str, Any]] = []
    seen: set = set()

    def walk(value: Any, path: str, call: Call) -> None:
        if isinstance(value, dict):
            for key, inner in value.items():
                here = "%s.%s" % (path, key) if path else str(key)
                scalar = not isinstance(inner, (dict, list))
                if scalar and MONEY_KEY.search(str(key)) and str(key) not in ("baseDecimals", "assetDecimals", "currencyDecimals"):
                    if inner is not None and not (isinstance(inner, str) and INTEGER_TEXT.match(inner)):
                        mark = ("law", call.route, here)
                        if mark not in seen:
                            seen.add(mark)
                            findings.append({"probe": "minor-unit law at %s (%s)" % (here, call.route), "sent": None,
                                             "expected": "an integer string of minor units", "said": "the server returned %r (%s)" % (inner, type(inner).__name__)})
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
        if call.station in ("S10", "S11") or call.status < 400:
            continue
        why = refusal_without_why(call.status, call.text)
        if why:
            findings.append({"probe": "Rule 13 at %s (%s)" % (call.route, call.station), "sent": call.sent, "expected": "a refusal that names what happened and who refused",
                             "said": "%s — %s" % (why, call.text[:300])})
    return findings


def audit_people(register: Optional[Dict[str, Any]], minted: Sequence[Dict[str, Any]], credentials: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    """The People register compared with the invitations sent, and the credentials the sessions carry."""
    findings: List[Dict[str, Any]] = []
    if register is None:
        return findings
    rows = {str(r.get("id")): r for r in register.get("invites") or []}
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
    if len(held) > 1 and len(distinct) < len(held):
        by_credential: Dict[str, List[str]] = {}
        for k, v in held.items():
            by_credential.setdefault(str(v), []).append(A.PEOPLE[k].name)
        shared = {last4(c): names for c, names in by_credential.items() if len(names) > 1}
        findings.append({"probe": "people register: one credential for several people", "sent": None,
                         "expected": "one credential id per person, so the register and every approval can tell them apart",
                         "said": "the sessions carry %d distinct credential id(s) for %d people: %s" % (len(distinct), len(held), json.dumps(shared, ensure_ascii=False))})
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
    line("S3", "POST /v1/onboarding/interviews %s → expect 200: the interview id and its first page" % _j({"interviewType": "policy"}))
    for q in A.expected_walk("policy"):
        line("S3", "POST /v1/onboarding/interviews/<policy interview>/answers %s → expect 200: the next page (%s)" % (_j({"questionId": q.id, "value": A.POLICY_ANSWERS[q.id]}), q.kind))
    line("S3", "GET /v1/onboarding/interviews/<policy interview>/readback → expect the charter in plain sentences, the sandbox realm first")
    line("S3", "POST /v1/onboarding/interviews/<policy interview>/confirm/options {} → expect the digest-bound challenge, issuedAtMs, digest")
    line("S3", "POST /v1/onboarding/interviews/<policy interview>/confirm %s → expect 200: state confirmed" % _j({"issuedAtMs": "<issuedAtMs>", "response": "<assertion by the founder's passkey over the challenge>"}))
    line("S3", "POST /v1/onboarding/interviews/<policy interview>/compile {} → expect 200: charter (name, quorum 1, signers, recordedChains, allowedChains aeredium-testnet), receipt, seat")
    line("S3", "GET /v1/onboarding/charter → expect standsWritten true")
    line("S3", "GET /v1/journey → expect currentStage 2 of %d" % JOURNEY_STAGE_COUNT)
    # S4
    for key in A.AUTHORS_INVITED:
        person = A.PEOPLE[key]
        line("S4", "POST /v1/invites %s (as %s, x-csrf-token) → expect 201: url %s/invite#<token>, said once" % (_j({"displayName": person.name, "email": person.email, "role": "author"}), founder.name, origin))
        line("S4", "POST /v1/auth/invite/options %s → expect 200: options for %s" % (_j({"token": "<token from the url>", "issuedAtMs": "<now>", "response": {}}), person.name))
        line("S4", "POST /v1/auth/invite/verify %s → expect 200: a session for %s, roles author and viewer%s" % (
            _j({"token": "<token>", "issuedAtMs": "<issuedAtMs>", "response": "<RegistrationResponseJSON with a new passkey>"}), person.name,
            "; approverSeat on redemption where the charter names them" if key == A.PAYMENT_APPROVER else ""))
    line("S4", "GET /v1/approver-seats (as %s) → expect the charter's seats; %s seated or enrolled_not_seated" % (founder.name, A.PEOPLE[A.PAYMENT_APPROVER].name))
    line("S4", "POST /v1/approver-seats/grant %s (as %s) — only if the seat is enrolled_not_seated → expect the seat seated" % (_j({"email": A.PEOPLE[A.PAYMENT_APPROVER].email}), founder.name))
    line("S4", "GET /v1/invites (as %s) → expect the register: three authors, redeemed" % founder.name)
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
    # S6
    for payee in T.PAYEES:
        line("S6", "POST /v1/payees %s (as %s) → expect 201: the payee with its address proposed" % (
            _j({"displayName": payee["name"], "defaultAsset": T.PAYMENT_ASSET, "defaultChain": payee["chain"], "addresses": [{"chain": payee["chain"], "address": T.address(payee["key"])}]}), founder.name))
        line("S6", "POST /v1/payees/addresses/<address of %s>/promote {} (as %s) → expect the platform's answer: status, platformMembershipId, ceremony" % (payee["name"], founder.name))
        line("S6", "POST /v1/payees/addresses/<address of %s>/approve {} (as %s) → expect whitelistStatus whitelisted" % (payee["name"], A.PEOPLE[A.PAYMENT_APPROVER].name))
    line("S6", "GET /v1/payees → expect both addresses whitelisted")
    # S7
    clerk = A.PEOPLE[A.PAYMENT_CLERK]
    line("S7", "GET /v1/workspace (as %s) → expect the funding account (sourceAccount) the runs leave from; the founder's browser offers no control for one" % clerk.name)
    for payment in A.PAYMENTS:
        if payment.payee_key is None:
            row: Dict[str, Any] = {"oneOff": {"chain": T.PAYEE_CHAIN, "address": T.address("UNLISTED_ETHEREUM"), "declared": True, "payeeName": payment.payee_name},
                                   "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": payment.amount_minor, "invoiceRef": payment.invoice}
        else:
            row = {"payeeAddressId": "<address of %s>" % payment.payee_name, "asset": T.PAYMENT_ASSET, "chain": T.PAYEE_CHAIN, "amountMinor": payment.amount_minor, "invoiceRef": payment.invoice}
        line("S7", "POST /v1/sets/review %s (as %s) → expect the five gates' review" % (_j({"pays": [row], "duplicatesAcknowledged": False}), clerk.name))
        line("S7", "POST /v1/sets %s (as %s) → expect 201: the run in draft" % (_j({"pays": [row], "duplicatesAcknowledged": False, "idempotencyKey": "aer360-harness-<run>-%s" % payment.key, "reference": "Harness payment %s" % payment.key}), clerk.name))
        line("S7", "POST /v1/sets/<run %s>/submit {} → expect status, setDigest, approvalsRequired; %s (%s): expected to %s" % (payment.key, payment.amount, T.PAYMENT_ASSET, payment.expect))
        line("S7", "GET /v1/sets/<run %s> → expect the run's state as the register shows it" % payment.key)
    line("S7", "POST /v1/approvals/<run P1>/challenge {} (as %s) → expect the digest-bound challenge" % A.PEOPLE[A.PAYMENT_APPROVER].name)
    line("S7", "POST /v1/approvals/<run P1>/approve %s (as %s) → expect status approved, approvalsGiven 1 of 1" % (_j({"response": "<assertion over the challenge>"}), A.PEOPLE[A.PAYMENT_APPROVER].name))
    # S8
    line("S8", "GET /v1/journey → printed: the stage, the stages done")
    line("S8", "GET /v1/workspace/readiness → printed: transactable, reason")
    # S9
    line("S9", "[out of scope] the tour's answers as Claude would see them: the harness is the founder, not Claude")
    # S10
    line("S10", "[compare] the read-back of each interview word for word with the answers given, as readback() spells them")
    line("S10", "[compare] the compiled charter (the compile answer) with the read-back: the figures, the rosters, the networks; GET /v1/onboarding/charter for its standing")
    line("S10", "GET /v1/journey, GET /v1/onboarding/charter, GET /v1/payees, GET /v1/sets, GET /v1/invites → [compare] the journey stage with what the registers hold")
    line("S10", "[check] every money figure the server returned against the minor-unit law (money.ts): an integer string of minor units, never a float")
    line("S10", "[check] every refusal met in S1 to S9 for Rule 13: it names what happened and who refused; a bare status or a generic sentence is a finding")
    line("S10", "[compare] the People register with the invitations sent, and the credential id each session carries")
    line("S10", "[compare] the payees register with the whitelist the charter enforces and with what Ada approved")
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
    line("S11", "POST /v1/payees %s → expect 201, accepted, as the law says (%s); a refusal is the finding" % (
        _j({"displayName": "Venue probe", "addresses": [{"chain": T.PAYEE_CHAIN, "address": "<the corridor's tables.py UNISWAP_V3_ETHEREUM, read at run time>"}]}), VENUE_RULING))
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
    runner = Runner(args.base, args.store, args.invite, args.fresh, args.start_at, args.out)
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
