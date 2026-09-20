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
status never moves. One choice is the double's own and is said here: a press is counted for the seat of the
PERSON pressing, found by the email their invitation was written with — the estate's press says whose seat
it is (`user_id`, read from the invitation the credential redeemed) — because on this estate one credential
is worn by four people, and a double that matched by credential first, as the platform's own double does,
could never let Ben's press count after Ada's. The live estate may count differently; the harness reports
what it meets.
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
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

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
LEVELS_BENEATH = set(A.LEVELS_BENEATH)
VENUE_STIPULATION = "This estate’s questionnaire stipulates that a venue contract is not a payee, so this address was not saved. Nothing was changed."
# What the platform says to a signature it will not count (apps/server/src/test/aapDouble.ts: "`validateMultisigSigner`
# returns `ErrNotAuthorized` unwrapped, and 'not authorized' is exactly the body a live client saw on 31 August 2026").
PLATFORM_NOT_AUTHORIZED = "not authorized"
A_PAYEE_ADDRESS = "a payee address onto the approved list"  # services/payees.ts: what the approve road is deciding about


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


class Clock:
    """Time that moves only when somebody sleeps on it, so a four-second invitation costs the suite nothing."""

    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


class EstateDouble:
    """The estate, in memory. Strict as the code; every answer is the code's own shape."""

    def __init__(self, base: str = BASE, source_account: Optional[str] = "0x0000000000000000000000000000000000000abc",
                 company: str = A.ESTATE["company"], catalog_version: int = 12, currency_spoken_as_code: bool = False,
                 refuses_venue_contract: bool = False, invite_seconds: float = 0.0, clock: Optional[Clock] = None,
                 pending_approval_says_why: bool = True, whitelist_roster: Optional[Sequence[str]] = None, platform_never_activates: bool = False):
        self.currency_spoken_as_code = currency_spoken_as_code  # False: main's default arm (JSON); True: Spec 88's code
        self.refuses_venue_contract = refuses_venue_contract  # the day the questionnaire stipulates against venue contracts
        self.invite_seconds = invite_seconds  # how long POST /v1/invites takes on the shared clock, the email awaited
        self.clock = clock
        # Spec T9's dials. False: the estate of 20 September 2026 before Spec 89, whose press answered only the status.
        self.pending_approval_says_why = pending_approval_says_why
        # The census keys seated on the whitelist_mutation roster; None seats the census the charter compiles (A8).
        self.whitelist_roster = tuple(whitelist_roster) if whitelist_roster is not None else None
        # True: a platform that counts every signature and never activates the address, so the count is met and nothing moves.
        self.platform_never_activates = platform_never_activates
        # The whitelist_mutation roster as the compiler writes it, seated when the policy charter compiles (governanceSignersFor).
        self.whitelist_seats: List[Dict[str, Any]] = []
        self.whitelist_threshold: Optional[int] = None
        self.base = base.rstrip("/")
        parsed = urllib.parse.urlparse(self.base)
        self.origin = "%s://%s" % (parsed.scheme, parsed.netloc)
        self.rp_id = parsed.hostname or RP_ID
        self.secret = b"double-secret"
        self.catalog_version = catalog_version
        self.workspace = {"id": WORKSPACE_ID, "name": company, "aapAccountId": AAP_ACCOUNT_ID, "realm": "sandbox", "sandboxMarkLetter": "S",
                          "baseCurrency": "USD", "displayCurrency": "AUD", "status": "active", "provisioning": "provisioned",
                          "rateSource": "double", "createdAt": "2026-09-19T00:00:00.000Z"}
        self.source_account = source_account
        # The account's ONE role-bearing credential (the founder's author token drawn up by the birth script).
        self.founder_credential = "cred-founder-" + secrets.token_hex(4)
        self.credentials: Dict[str, Dict[str, Any]] = {self.founder_credential: {"access": "sign+audit", "name": "Founder (author)"}}
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
        headers = {k.lower(): v for k, v in request.header_items()}
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
        m = re.match(r"^/v1/sets/([^/]+)(/submit)?$", path)
        if m:
            if method == "GET" and not m.group(2):
                caller = self.require_caller(headers, "viewer")
                row = self.sets.get(m.group(1))
                if not row:
                    raise Refusal("SET_NOT_EDITABLE", detail={"cause": "no such run"})
                return 200, {"set": self.set_view(row, caller)}
            if method == "POST" and m.group(2) == "/submit":
                return self.submit_set(headers, m.group(1))
        m = re.match(r"^/v1/approvals/([^/]+)/(challenge|approve)$", path)
        if m and method == "POST":
            return self.approval(headers, m.group(1), m.group(2), body)
        if route == "GET /v1/workspace":
            self.require_session(headers)
            return 200, {"workspace": dict(self.workspace), "sourceAccount": self.source_account, "supportedCurrencies": ["AUD", "EUR", "GBP", "USD"]}
        if route == "POST /v1/workspace/display-currency":
            self.require_caller(headers, "author", mutating=True)
            currency = str((body or {}).get("displayCurrency", "")).upper()
            self.workspace["displayCurrency"] = currency
            return 200, {"displayCurrency": currency}
        if route == "GET /v1/workspace/readiness":
            self.require_session(headers)
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
        self.passkeys[body["response"]["id"]] = {"credentialId": credential_id, "publicKey": stored["public_key"], "signCount": stored["sign_count"],
                                                 "label": row["displayName"], "lastAuthAtMs": body["issuedAtMs"], "email": row.get("email")}
        self.audit.append("passkey.registered %s via invite" % credential_id)
        seat = self.complete_seat_on_redemption(credential_id, row.get("email"))
        roles = self.roles_of(credential_id)
        if not roles:
            raise Refusal("ROLE_NOT_GRANTED", detail={"required": "any", "held": "none"}, provenance={"source": "aap_policy"})
        session = self.open_session(credential_id, row["displayName"], set_cookie, row.get("email"))
        return 200, self.session_view(session, {"approverSeat": seat} if seat else None)

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
        return list(A.CATALOGS[interview_type])

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
        part = V11.get(q.id, {}).get("part", "") if q else (V11.get(visible[-1].id, {}).get("part", "") if visible else "")
        in_part = [v for v in visible if V11.get(v.id, {}).get("part", "") == part]
        question = None
        if q:
            question = {"questionId": q.id, "part": part, "kind": q.kind, "prompt": V11.get(q.id, {}).get("prompt", q.id), "options": list(q.options) if q.options else None,
                        "listFields": None, "recommended": None, "note": None, "required": q.required,
                        "priorValue": latest[q.id]["value"] if q.id in latest else None}
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
                                           "promptAsAsked": V11.get(qid, {}).get("prompt", qid), "credentialId": caller["credentialId"]})
        page = self.page(iv, serve_truth=False)
        if page["question"] is None:
            violation = self.standing_violation(iv["interviewType"], self.latest(interview_id))
            if violation:
                raise Refusal("ANSWER_INVALID", violation["sentence"], {"questionId": violation["quorumQuestionId"]}, walkBackTo={"questionId": violation["quorumQuestionId"]})
            if iv["state"] == "in_progress":
                iv["state"] = "at_read_back"
            page["state"] = "at_read_back"
        return 200, page

    def readback_lines_for_test(self, interview_id: str) -> List[Dict[str, Any]]:
        """The renderer alone, for a test: the lines as readback() would speak them, the standing checks set aside."""
        return self.readback(self.load_interview(interview_id), check_standing=False)

    def readback(self, iv: Dict[str, Any], check_standing: bool = True) -> List[Dict[str, Any]]:
        latest = self.latest(iv["id"])
        violation = self.standing_violation(iv["interviewType"], latest) if check_standing else None
        if violation:
            raise Refusal("ANSWER_INVALID", violation["sentence"], {"questionId": violation["quorumQuestionId"]}, walkBackTo={"questionId": violation["quorumQuestionId"]})
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
                spoken = "Left empty — no limit; the loosest possible answer." if cents is None else "US$%s and %02d cents." % ("{:,}".format(int(cents) // 100), int(cents) % 100)
            elif kind == "percent":
                p = v.get("percent")
                spoken = ("Left empty — never halts on pace." if q.id == "T4" else "Left empty — no share is set.") if p is None else "%s per cent." % p
            elif kind == "count":
                c = v.get("count")
                spoken = "Left empty — no limit on how many." if c is None else "%s %s in a day." % ("{:,}".format(c), "payment" if c == 1 else "payments")
            else:
                spoken = ", ".join(v.get("people") or []) or "No one chosen."
            lines.append({"questionId": q.id, "prompt": V11.get(q.id, {}).get("prompt", q.id), "spoken": spoken})
            if q.id in ("C10", "WQ"):
                lines.append({"questionId": "HELD_WAIT", "prompt": "What happens while a payment waits for them", "spoken": HELD_PAYMENT_WAITS, "synthetic": True})
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
        latest = {qid: row["value"] for qid, row in self.latest(interview_id).items()}
        charter = self.compile_charter(iv["interviewType"], latest)
        if iv["interviewType"] == "policy":
            self.seat_whitelist_roster(charter, latest)
        iv["compiledCharter"] = charter
        iv["state"] = "written"
        iv["writeReceipt"] = {"aapAccountId": AAP_ACCOUNT_ID, "policyEntryId": "pe-" + secrets.token_hex(4), "completedAt": self._now_iso()}
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
        people = self.parse_roster(charter.get("changeApprovers") or charter.get("signers") or [])
        if self.whitelist_roster is not None:
            wanted = {A.PEOPLE[k].email.lower() for k in self.whitelist_roster}
            people = [p for p in people if p["email"].lower() in wanted]
        choice = lambda qid: (latest.get(qid) or {}).get("choice")  # noqa: E731
        threshold = choice("C12D") if choice("C12A") == "Yes" and choice("C12D") else choice("C12")
        self.whitelist_seats = [{"user_id": p["email"], "display_name": p["name"], "credential_id": "", "status": "active"} for p in people]
        self.whitelist_threshold = int(threshold) if threshold else 1

    def compile_charter(self, interview_type: str, latest: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
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
        }
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

    def enrolled_by_email(self) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for row in self.invites.values():
            if row["redeemedAt"] and row.get("email"):
                out.setdefault(row["email"].strip().lower(), [])
                if row["credentialId"] not in out[row["email"].strip().lower()]:
                    out[row["email"].strip().lower()].append(row["credentialId"])
        return out

    def complete_seat_on_redemption(self, credential_id: str, email: Optional[str]) -> Optional[Dict[str, Any]]:
        if not email:
            return {"charterNamedThem": False, "granted": False, "note": None}
        charter = self.newest_written_charter()
        if not charter:
            return {"charterNamedThem": False, "granted": False, "note": None}
        wanted = email.strip().lower()
        if not any(p["email"].lower() == wanted for p in self.parse_roster(charter["signers"])):
            return {"charterNamedThem": False, "granted": False, "note": None}
        if credential_id not in self.second_approvers:
            self.second_approvers.append(credential_id)
            self.audit.append("approver_seat.granted %s via invite_redemption" % credential_id)
        return {"charterNamedThem": True, "granted": True, "note": None}

    def complete_seat_on_charter_write(self, credential_id: str) -> Dict[str, Any]:
        return {"charterNamedThem": False, "granted": False, "note": None}

    def seats(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author")
        return 200, self.seats_view(caller)

    def seats_view(self, caller: Dict[str, Any]) -> Dict[str, Any]:
        charter = self.newest_written_charter()
        if not charter:
            return {"charterStands": False, "seats": [], "summary": "", "policyEntryId": None}
        by_email = self.enrolled_by_email()
        seats = []
        for person in self.parse_roster(charter["signers"]):
            candidates = by_email.get(person["email"].lower(), [])
            seated = any(c in self.second_approvers for c in candidates)
            state = "seated" if seated else ("enrolled_not_seated" if candidates else "not_enrolled")
            seats.append({"name": person["name"], "email": person["email"], "state": state, "credentialId": candidates[0] if len(candidates) == 1 else None,
                          "ambiguous": len(candidates) > 1, "invitation": None, "selfSeatable": False})
        return {"charterStands": True, "seats": seats, "summary": "%d seated" % sum(1 for s in seats if s["state"] == "seated"), "policyEntryId": "pe-estate"}

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
        if candidates[0] not in self.second_approvers:
            self.second_approvers.append(candidates[0])
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
            self.credentials[credential_id] = {"access": "audit", "name": "Viewer — read only — %s" % display_name}
        else:
            # An author invitation enrols the ONE role-bearing credential the account carries (services/invites.ts).
            role_bearing = [c for c, e in self.credentials.items() if "sign" in e["access"] or "audit" in e["access"]]
            role_bearing = [c for c in role_bearing if c not in (cv for cv in self.credentials if self.credentials[cv]["access"] == "audit")]
            if len(role_bearing) != 1:
                raise Refusal("INVITE_INVALID", detail={"cause": "the account carries several role-bearing credentials; this invite must name which one it enrols", "candidates": ", ".join(role_bearing)})
            credential_id = role_bearing[0]
        token = secrets.token_urlsafe(32)
        row = {"id": "inv-" + secrets.token_hex(6), "displayName": display_name, "email": email, "phone": body.get("phone"), "role": role, "note": body.get("note"),
               "state": "pending", "credentialId": credential_id, "createdAt": self._now_iso(), "expiresAt": self._iso(time.time() + 72 * 3600),
               "redeemedAt": None, "revokedAt": None, "revokedByCredentialId": None, "dispatchedAt": None,
               "dispatchDetail": "This deployment has no mail lane, so nothing was sent. Copy the link and send it to this person yourself."}
        self.invites[hashlib.sha256(token.encode()).hexdigest()] = row
        self.audit.append("invite.minted %s %s by %s" % (role, email, caller["credentialId"]))
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
        return 200, {"invites": [dict(r) for r in sorted(self.invites.values(), key=lambda r: r["createdAt"], reverse=True)]}

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
            if self.refuses_venue_contract and address.lower() == T.venue_address_for_probe()["address"].lower():
                raise Refusal("ADDRESS_PROPOSAL_REFUSED", VENUE_STIPULATION,
                              {"chain": a["chain"], "address": address,
                               "cause": "a stipulation the live questionnaire does not carry today; this double stands in for the day it does"},
                              provenance={"source": "charter"})
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
        role = "author" if action == "promote" else "approver"
        caller = self.require_caller(headers, role, mutating=True)
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
        if row["whitelistStatus"] != "pending_promotion" or not row.get("ceremony"):
            raise Refusal("ADDRESS_PROMOTION_PENDING", detail={"cause": "this address has not been proposed to the platform whitelist yet"})
        facts = self.charter_facts(caller)
        may, cause = self.may_approve(facts, row["proposedBy"], caller["credentialId"])
        if not may:
            raise self.approval_refusal(cause or "charter_silent", facts, A_PAYEE_ADDRESS, caller["roles"])
        if action == "reject":
            row["whitelistStatus"] = "rejected"
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
        The seat is found by the presser's email first (see the module docstring for why, and what the live estate may do).
        """
        ceremony = row["ceremony"]
        active = [s for s in self.whitelist_seats if s["status"] == "active"]
        email = (caller.get("email") or "").lower()
        if email:
            seat = next((s for s in active if s["user_id"].lower() == email), None)
        else:
            seat = next((s for s in active if s["credential_id"] and s["credential_id"] == caller["credentialId"]), None)
        if seat is None:
            raise Refusal("SIGNATURE_NOT_COUNTED", detail={"payeeAddressId": row["id"], "credentialId": caller["credentialId"],
                                                           "platformStatus": "403", "platformSaid": PLATFORM_NOT_AUTHORIZED},
                          provenance={"source": "aap_whitelist", "reference": ceremony["pendingTxId"]})
        if not seat["credential_id"]:
            seat["credential_id"] = caller["credentialId"]  # the enrolment bind (spec 76)
        if seat["user_id"] not in ceremony["signatures"]:
            ceremony["signatures"].append(seat["user_id"])  # only once either way
        required, collected = ceremony["requiredSignatures"], len(ceremony["signatures"])
        if collected >= required and not self.platform_never_activates:
            row["whitelistStatus"] = "whitelisted"
            row["promotedAt"] = self._now_iso()
            self.audit.append("payee.address.whitelisted %s by %s" % (row["id"], seat["user_id"]))
            return {"whitelistStatus": "whitelisted"}
        may_still = [s["display_name"] for s in active if s["user_id"] not in ceremony["signatures"]]
        self.audit.append("payee.address.promotion_pending_quorum %s requiredSignatures %d, signaturesCollected %d, mayStillApprove %s" % (
            row["id"], required, collected, ", ".join(may_still) or "nobody"))
        if not self.pending_approval_says_why:
            return {"whitelistStatus": "pending_promotion"}  # the live estate's whole answer on 20 September 2026, before Spec 89
        return {"whitelistStatus": "pending_promotion",
                "approvals": {"required": required, "collected": collected, "remaining": max(required - collected, 0)},
                "may_still_approve": may_still,
                "sentence": pending_approval_sentence(required, collected, may_still, [s["display_name"] for s in active])}

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
        if not self.source_account:
            raise Refusal("GAS_PREFLIGHT_UNAVAILABLE", NO_FUNDING_ACCOUNT, {"cause": "workspace has no source account"})
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
            out = {"index": r["index"], "payeeId": None, "payeeName": (p.get("oneOff") or {}).get("payeeName") or "One-off payee", "address": (p.get("oneOff") or {}).get("address", ""),
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
            {"gate": "gas_preflight", "passed": True, "refusals": [], "evidence": "ethereum: needs 0, holds 1"},
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
def runner_on(double: EstateDouble, tmp: str, invite: Optional[str] = None, start_at: Optional[str] = None, said: Optional[List[str]] = None, **kwargs: Any) -> H.Runner:
    return H.Runner(double.base, os.path.join(tmp, "store"), invite, False, start_at, os.path.join(tmp, "out"), transport=double,
                    say=(said.append if said is not None else (lambda s: None)), sleep=lambda s: None, **kwargs)


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

    def test_an_author_invitation_enrols_the_one_role_bearing_credential(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        ada = self.runner.people["ada"]
        minted = self.request(self.founder, "POST", "/v1/invites", {"displayName": ada.name, "email": ada.email, "role": "author"})
        self.assertEqual(minted.status, 201)
        self.assertEqual(minted.json["credentialId"], self.founder.credential_id, "the invite enrols the founder's own credential, as services/invites.ts resolves it")
        self.runner.enrol_by_invite(ada, minted.json["url"], "test")
        self.assertEqual(ada.credential_id, self.founder.credential_id)

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

    def test_a_double_told_the_questionnaire_stipulates_against_venue_contracts_refuses_them_by_name(self):
        self.runner.enrol_by_invite(self.founder, self.link, "test")
        venue = T.venue_address_for_probe()["address"]
        body = {"displayName": "Venue probe", "addresses": [{"chain": "ethereum", "address": venue}]}
        accepted = self.request(self.founder, "POST", "/v1/payees", body)
        self.assertEqual(accepted.status, 201, "today's estate: an address is accepted unless the questionnaire stipulates otherwise")
        strict = EstateDouble(refuses_venue_contract=True)
        link = strict.mint_founder_link()
        runner = runner_on(strict, self.tmp, invite=link)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        refused = runner.request(founder, "POST", "/v1/payees", body, "test")
        self.assertEqual(refused.status, 422)
        self.assertEqual(refused.refusal["code"], "ADDRESS_PROPOSAL_REFUSED")
        self.assertEqual(refused.refusal["message"], VENUE_STIPULATION)
        self.assertIn("this double stands in for the day it does", refused.refusal["detail"]["cause"])
        self.assertIsNone(H.refusal_without_why(refused.status, refused.text), "a refusal that says why")
        other = runner.request(founder, "POST", "/v1/payees", {"displayName": "x", "addresses": [{"chain": "ethereum", "address": T.address("CHECKSUM_PROBE_ETHEREUM")}]}, "test")
        self.assertEqual(other.status, 201, "only the venue contract is stipulated against")

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
        double = EstateDouble(source_account=None)
        link = double.mint_founder_link()
        runner = runner_on(double, self.tmp, invite=link)
        founder = runner.people[A.FOUNDER]
        runner.enrol_by_invite(founder, link, "test")
        answer = runner.request(founder, "POST", "/v1/sets/review", {"pays": [{"oneOff": {"chain": "ethereum", "address": T.address("UNLISTED_ETHEREUM"), "declared": True}, "asset": "USDC", "chain": "ethereum", "amountMinor": "1000000"}], "duplicatesAcknowledged": False}, "test")
        self.assertEqual(answer.status, 503)
        self.assertEqual(answer.refusal["code"], "GAS_PREFLIGHT_UNAVAILABLE")
        self.assertEqual(answer.refusal["message"], NO_FUNDING_ACCOUNT)


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
        cls.double = EstateDouble()
        cls.tmp = tempfile.mkdtemp()
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        cls.runner.run()  # S1–S6 compile the policy (seating the whitelist roster) and seat Ada
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
        # A roster of one (Ada). Ben is an approver on this estate (the shared credential Ada's seat carries), but his
        # key is on no seat of this roster, so the platform declines his signature and the estate relays it (Rule 13).
        double = EstateDouble(whitelist_roster=("ada",))
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


if __name__ == "__main__":
    unittest.main()
