"""
THE SCREENS THE BROWSER LEG WALKS, AS THE SCREENS' DOUBLE RENDERS THEM (Spec HRW-1's tests): App.tsx's shell and routes, Invite.tsx, SignIn.tsx,
Onboarding.tsx, People.tsx, Wallets.tsx, PayeeRegistry.tsx, PaymentEntry.tsx, Runs.tsx and ApproverInbox.tsx, at aeredium/AERAccounts b523cbf —
each rendered from its own state as an accessibility tree, each press making the calls its TSX makes, in the order it makes them. The words are
the screens' own, restated here (never read from aer360_screens.py): a control or a sentence the harness pinned wrongly is one it cannot find here.
Only what the browser leg meets is rendered; a room it never opens is the shell's Consolidation heading and nothing more.
"""
from __future__ import annotations

import re
import time
import urllib.parse
import uuid
from typing import Any, Dict, List, Optional

from tests.real_world_double import ApiError, El, NotAllowed, h, label_of

DEFAULT_LIST_FIELDS = [{"key": "label", "label": "Name"}, {"key": "address", "label": "Email or address"}]
ENROLMENT_KEY_EXISTS = "Your key exists, and you are signed in."
ENROLMENT_KEY_AND_SEAT_GRANTED = "Your key exists and your seat is granted — you can approve now."
ENROLMENT_KEY_EXISTS_SEAT_PENDING = ("Your key exists, and you are signed in. Your charter names you an approver and your seat could not be recorded yet — your estate’s "
                                     "key holder can grant it in the People room with one press.")
SEAT_STATE_WORDS = {"seated": "Seated", "enrolled_not_seated": "Enrolled, not seated", "invited": "Invited — awaiting their key", "not_enrolled": "Not yet enrolled"}
SEAT_STATE_MEANING = {  # shared/enrolment.ts seatStateMeaning, hidden beside each seat's pill (the invited arm's dates left out: the double keeps no clock)
    "seated": "your policy names their credential; they may approve",
    "invited": "an invitation to this person stands and their key does not exist yet, so there is nothing to seat. Resend it rather than creating a second — "
               "a second invitation is refused while this one stands",
    "not_enrolled": "no invitation stands for this person and this estate holds no credential for them — invite them, and their seat completes itself when they bind "
                    "their passkey",
    "enrolled_not_seated": "a credential exists and your policy does not name it yet"}
REGISTER_STATE_SENTENCE = {"pending": "not used yet", "redeemed": "used; this person is enrolled", "revoked": "withdrawn; the link no longer works",
                           "expired": "never used, and it lapsed"}  # web/screens/People.tsx stateSentence, without its dates
STATUS_WORDS = {"proposed": "Proposed", "pending_promotion": "Pending promotion", "whitelisted": "Whitelisted", "rejected": "Rejected", "redeemed": "Redeemed",
                "pending": "Pending", "revoked": "Revoked", "expired": "Expired", "pending_approval": "Pending approval"}
GATE_LABELS = {"whitelist_or_one_off": "Approved payee, or a capped one-off", "pricing": "Priced in your currency from fresh rates",
               "quota": "Monthly signature allowance", "gas_preflight": "Network fees covered", "duplicate_screen": "Not a repeat of a recent payment"}
LEVEL_ONE = ("Level 1 — head office", "This estate’s own wallets — everything internal to the company, its divisions included — approved by the estate’s people under the charter.")
ASSET_DECIMALS = {"ETH": 18, "WETH": 18, "DAI": 18, "POL": 18, "MATIC": 18, "AVAX": 18, "BNB": 18, "AERX": 18, "USDC": 6, "USDT": 6, "WBTC": 8, "SOL": 9}
KNOWN_CHAINS = ("ethereum", "polygon", "arbitrum", "optimism", "base", "avalanche", "bsc", "solana", "anvil")
CHAIN_NAMES = {"ethereum": "Ethereum", "arbitrum": "Arbitrum One", "base": "Base", "polygon": "Polygon", "optimism": "OP Mainnet"}


def now_ms() -> int:
    return int(time.time() * 1000)


def card(title: Any, *children: Any, action: Any = None, attrs: Optional[Dict[str, Any]] = None) -> El:
    """web/components/ui.tsx Card: section.card, its title an h2 in div.card-head."""
    return h("section", h("div", h("h2", title), action, cls="card-head"), *children, cls="card", attrs=attrs)


def plain_card(*children: Any) -> El:
    return h("section", *children, cls="card")


def hidden(text: str) -> El:
    return h("span", text, cls="visually-hidden")


def humanise(key: str) -> str:
    """web/components/Refusals.tsx humanise."""
    text = re.sub(r"([A-Z])", r" \1", key).replace("_", " ")
    text = text[:1].upper() + text[1:]
    return text.replace(" Usd", " USD").replace(" Minor", " (minor units)")


def refusal_notice(refusal: Dict[str, Any], road_link: bool = True) -> El:
    """web/components/Refusals.tsx RefusalNotice: role alert (status where acknowledgeable), the message, the detail, the provenance line."""
    warn = refusal.get("acknowledgeable") is True
    detail = refusal.get("detail") if isinstance(refusal.get("detail"), dict) else {}
    road = refusal.get("road") if isinstance(refusal.get("road"), dict) else None
    provenance = refusal.get("provenance") if isinstance(refusal.get("provenance"), dict) else None
    line = refusal.get("code") if provenance is None else "%s · from %s%s" % (refusal.get("code"), provenance.get("source"),
                                                                           (" (%s)" % provenance["reference"]) if provenance.get("reference") else "")
    return h("div",
             h("span", "!" if warn else "×", attrs={"aria-hidden": "true"}),
             h("div",
               h("p", hidden("Warning: " if warn else "Refused: "), refusal.get("message") or ""),
               h("p", h("a", road.get("label"), attrs={"href": "/runs/%s" % road.get("runId")}, click=lambda: None)) if (road and road.get("kind") == "open_run" and road_link) else None,
               h("dl", *[h("div", h("dt", humanise(k)), h("dd", str(v))) for k, v in detail.items()]) if detail else None,
               h("p", line)),
             cls="refusal", attrs={"role": "status" if warn else "alert"})


def pill(word: str) -> El:
    return h("span", word, cls="pill")


# ======================================================================================================================
# The shell (web/App.tsx).
# ======================================================================================================================
class App:
    # The shell's brand names the estate (App.tsx:356-359). False: a shell whose brand names nothing — the page the guard must not press on.
    BRAND_NAMES_ESTATE = True

    def __init__(self, page: Any, path: str, query: str, fragment: str):
        self.page = page
        self.path = path
        self.query = query
        self.fragment = fragment
        self.session: Optional[Dict[str, Any]] = None
        self.csrf: Optional[str] = None
        self.arrived = False
        self.screen: Any = None
        self.journey: Optional[Dict[str, Any]] = None

    def get(self, path: str) -> Any:
        return self.page.fetch("GET", path)

    def post(self, path: str, body: Any = None) -> Any:
        return self.page.fetch("POST", path, body)

    def mount(self) -> None:
        if self.path == "/invite":  # THE INVITATION LINK OWNS ITS ROUTE ABSOLUTELY (spec 64, count 1)
            self.screen = Invite(self, self.fragment)
            self.screen.mount()
            return
        try:
            self.hold(self.get("/v1/auth/session"))
        except ApiError:
            self.session = None
        if self.session is None:
            self.screen = SignIn(self)
            return
        self.open_route(self.path, self.query)

    def hold(self, session: Dict[str, Any]) -> None:
        self.session = session
        self.csrf = session.get("csrfToken")

    def arrive(self, session: Dict[str, Any]) -> None:
        self.hold(session)
        self.arrived = True
        parsed = urllib.parse.urlparse(self.page.url)
        self.open_route(parsed.path or "/", parsed.query, landing=True)

    def open_route(self, path: str, query: str, state: Optional[Dict[str, Any]] = None, landing: bool = False) -> None:
        try:
            self.journey = self.get("/v1/journey")
        except ApiError:
            self.journey = None
        if landing and path == "/" and self.journey and self.journey.get("landingRoute") not in (None, "/"):
            # THE LANDING LAW (components/Journey.tsx): a session entered on bare `/` is sent to the journey's landing route, once
            path = str(self.journey["landingRoute"])
            self.page.url = self.page.world.estate.origin + path
        self.path, self.query = path, query
        params = urllib.parse.parse_qs(query)
        m = re.match(r"^/runs/([^/]+)$", path)
        if path == "/onboarding":
            self.screen = Onboarding(self)
        elif path == "/people":
            self.screen = People(self)
        elif path == "/wallets":
            self.screen = Wallets(self)
        elif path == "/payees":
            self.screen = Payees(self)
        elif path == "/entry":
            self.screen = PaymentEntry(self, (params.get("wallet") or [""])[0])
        elif m:
            self.screen = RunPage(self, m.group(1), state)
        elif path == "/inbox":
            self.screen = Inbox(self)
        else:
            self.path = "/"
            self.screen = Consolidation(self)
        self.screen.mount()

    def navigate(self, path: str, state: Optional[Dict[str, Any]] = None) -> None:
        parsed = urllib.parse.urlparse(path)
        self.page.url = self.page.world.estate.origin + path
        self.open_route(parsed.path, parsed.query, state)

    def roles(self) -> List[str]:
        return list((self.session or {}).get("roles") or [])

    def render(self) -> El:
        banner = h("header", "AER 360", "by AEREDIUM", attrs={"role": "banner"})
        if isinstance(self.screen, (Invite, SignIn)) or self.session is None:
            return h("html", banner, self.screen.render() if self.screen else h("main", "Loading…"))
        workspace = self.session.get("workspace") or {}
        roles = self.roles()
        spoken = [("an %s" % r) if r in ("author", "approver") else ("a %s" % r) for r in roles]
        standing = spoken[0] if len(spoken) == 1 else ("%s and %s" % (", ".join(spoken[:-1]), spoken[-1]) if spoken else "somebody with no standing at all")
        arrival = h("p", ("You are in %s as %s." % (workspace.get("name"), standing)) if self.arrived else "", cls="visually-hidden", attrs={"role": "status"})
        guide = h("p", "", cls="visually-hidden", attrs={"role": "status", "aria-live": "assertive"})
        bar = None
        if self.journey and self.journey.get("road") == "wizard":
            stage = next((s for s in self.journey.get("stages") or [] if s.get("current")), None)
            if stage:
                at_home = stage.get("route") == self.path
                step = "Step %s of 7 — %s" % (stage["number"], stage["name"])
                bar = h("nav", h("span", step + (". You are here." if at_home else "")), None if at_home else h("a", "Continue", attrs={"href": stage["route"]},
                        click=lambda route=stage["route"]: self.navigate(route)), attrs={"aria-label": "Your journey"})
        rooms = [("Onboarding", "/onboarding"), ("Consolidation", "/"), ("Enter payments", "/entry"), ("Runs", "/runs"), ("Approver inbox", "/inbox"),
                 ("Payees", "/payees"), ("People", "/people"), ("Wallets", "/wallets")]
        sidebar = h("nav",
                    h("div", hidden("Estate: "), workspace.get("name") if self.BRAND_NAMES_ESTATE else None, cls="brand"),
                    h("div", *[h("a", name, attrs={"href": route}, click=lambda route=route: self.navigate(route)) for name, route in rooms], cls="nav"),
                    h("div", h("p", "Signed in as"), h("p", self.session.get("displayName")),
                      h("p", ", ".join(roles) if roles else "no permissions", hidden(" — set by your organisation’s policy")), h("button", "Sign out", click=self.sign_out)),
                    attrs={"aria-label": "Sections"})
        return h("html", banner, arrival, bar, guide, h("div", sidebar, h("main", self.screen.render(), cls="main"), cls="shell"))

    def sign_out(self) -> None:
        self.post("/v1/auth/logout")
        self.session = None
        self.csrf = None
        self.screen = SignIn(self)


class Consolidation:
    def __init__(self, app: App):
        self.app = app

    def mount(self) -> None:
        pass

    def render(self) -> El:
        return h("div", h("h1", "Consolidation"))


# ======================================================================================================================
# web/screens/Invite.tsx — outside the shell.
# ======================================================================================================================
class Invite:
    def __init__(self, app: App, token: str):
        self.app = app
        self.token = token.strip()
        self.name: Optional[str] = None
        self.stage = "opening"
        self.error: Optional[ApiError] = None
        self.nothing_recorded = False
        self.session: Optional[Dict[str, Any]] = None

    def mount(self) -> None:
        if not self.token:
            self.stage = "no_link"
            return
        try:
            start = self.app.post("/v1/auth/invite/options", {"token": self.token, "issuedAtMs": now_ms(), "response": {}})
        except ApiError as err:
            self.stage = "dead_link"
            self.error = err
            return
        self.name = start.get("displayName")
        self.create_key(start)

    def create_key(self, start: Optional[Dict[str, Any]] = None) -> None:
        self.stage = "creating"
        self.error = None
        self.nothing_recorded = False
        try:
            opened = start or self.app.post("/v1/auth/invite/options", {"token": self.token, "issuedAtMs": now_ms(), "response": {}})
            self.name = opened.get("displayName")
            created = self.app.page.credentials_create(opened["options"])
            signed_in = self.app.post("/v1/auth/invite/verify", {"token": self.token, "issuedAtMs": opened["issuedAtMs"], "response": created})
        except NotAllowed:
            self.nothing_recorded = True
            self.stage = "waiting"
            return
        except ApiError as err:
            self.nothing_recorded = True
            self.stage = "waiting"
            self.error = err
            return
        self.app.page.url = self.app.page.world.estate.origin + "/"  # window.history.replaceState(null, '', '/')
        self.session = signed_in
        self.stage = "done"

    def render(self) -> El:
        if self.stage == "opening":
            return h("main", h("h1", "Your key"), h("p", "Opening your invitation…", attrs={"role": "status"}))
        if self.stage == "no_link":
            return h("main", h("h1", "An invitation link is needed"), plain_card(h("p", "This page needs an invitation link. Ask your administrator to send you one.")))
        if self.stage == "dead_link":
            return h("main", h("h1", "This invitation could not be opened"), refusal_notice(self.error.refusal) if self.error else None)
        if self.stage == "done":
            seat = (self.session or {}).get("approverSeat")
            said = ENROLMENT_KEY_EXISTS if not seat or not seat.get("charterNamedThem") else (ENROLMENT_KEY_AND_SEAT_GRANTED if seat.get("granted") else ENROLMENT_KEY_EXISTS_SEAT_PENDING)
            estate = ((self.session or {}).get("workspace") or {}).get("name") or "your organisation"
            return h("main", h("h1", said),
                     plain_card(h("p", "%s passkey is held only on this device. From now on, your fingerprint, your face or your screen lock is how you sign in — there is nothing "
                                       "to type and no password to remember." % (("%s, your" % self.name) if self.name else "Your")),
                                h("div", h("button", "Continue to %s" % estate, click=lambda: self.app.arrive(self.session)), cls="actions")))
        creating = self.stage == "creating"
        return h("main", h("h1", ("%s, create your key" % self.name) if self.name else "Create your key"),
                 h("p", "One step creates your key — nothing is done until it exists", cls="lede"),
                 h("p", "Nothing was recorded — your invitation still works; the key is created only at the moment your device confirms it.", attrs={"role": "status"})
                 if self.nothing_recorded else None,
                 refusal_notice(self.error.refusal) if self.error else None,
                 h("div", h("button", "Waiting for your device…" if creating else "Create my key now", disabled=creating or not self.token,
                            click=lambda: self.create_key()), cls="one-act"))


# ======================================================================================================================
# web/screens/SignIn.tsx — any URL with no session.
# ======================================================================================================================
class SignIn:
    def __init__(self, app: App):
        self.app = app
        self.error: Optional[Dict[str, Any]] = None

    def mount(self) -> None:
        pass

    def sign_in(self) -> None:
        self.error = None
        try:
            start = self.app.post("/v1/auth/login/options", {})
            assertion = self.app.page.credentials_get(start["options"]["challenge"], allow=[], user_verification="required")
            session = self.app.post("/v1/auth/login/verify", {"nonce": start["nonce"], "issuedAtMs": start["issuedAtMs"], "response": assertion})
        except NotAllowed:
            self.error = {"code": "STEP_UP_INVALID", "message": "The passkey confirmation did not complete, so you are not signed in."}
            return
        except ApiError as err:
            self.error = err.refusal
            return
        self.app.arrive(session)

    def render(self) -> El:
        return h("main", h("h1", "Sign in"),
                 h("p", "Your workspace is born from your AEGISKey account. Sign in with your passkey — there is nothing to type and no password anywhere.", cls="muted"),
                 refusal_notice(self.error) if self.error else None,
                 plain_card(h("div", h("button", "Sign in with passkey", click=self.sign_in), cls="actions"),
                            h("p", "New here? Enrolment is by invitation: open the invitation link you were sent and confirm with your device. No key or identifier is ever typed.",
                              cls="hint")))


# ======================================================================================================================
# web/screens/Onboarding.tsx — the Policy Interview.
# ======================================================================================================================
class Onboarding:
    def __init__(self, app: App):
        self.app = app
        self.page: Optional[Dict[str, Any]] = None
        self.lines: Optional[List[Dict[str, Any]]] = None
        self.result: Optional[Dict[str, Any]] = None
        self.charter: Optional[Dict[str, Any]] = None
        self.error: Optional[Dict[str, Any]] = None
        self.reset({})

    def reset(self, prior: Dict[str, Any]) -> None:
        q = (self.page or {}).get("question") or {}
        v = q.get("priorValue") or prior or {}
        self.choice = v.get("choice") if isinstance(v.get("choice"), str) else (v.get("text") if q.get("kind") == "currency" and isinstance(v.get("text"), str) else "")
        self.choices = list(v.get("choices") or []) if isinstance(v.get("choices"), list) else []
        self.text = v.get("text") if isinstance(v.get("text"), str) else ""
        self.amount = ("%s" % (int(v["cents"]) / 100)) if isinstance(v.get("cents"), str) else ""
        self.percent = str(v["percent"]) if isinstance(v.get("percent"), (int, float)) else ""
        self.people = ", ".join(v.get("people") or []) if isinstance(v.get("people"), list) else ""
        self.entries: List[Dict[str, str]] = [dict(e) for e in v.get("entries") or []] if isinstance(v.get("entries"), list) and v.get("entries") else (
            [dict(v["person"])] if isinstance(v.get("person"), dict) else [])

    def mount(self) -> None:
        try:
            self.charter = self.app.get("/v1/onboarding/charter")
        except ApiError:
            self.charter = None

    def adopt(self, page: Dict[str, Any]) -> None:
        self.page = page
        self.lines = None
        self.error = None
        self.reset({})
        if page.get("contradiction"):
            self.error = page["contradiction"]
        if page.get("question") is None and page.get("state") in ("at_read_back", "in_progress"):
            try:
                self.lines = self.app.get("/v1/onboarding/interviews/%s/readback" % page["interviewId"])["lines"]
            except ApiError as err:
                self.error = err.refusal

    def begin(self, kind: str) -> None:
        try:
            started = self.app.post("/v1/onboarding/interviews", {"interviewType": kind})
        except ApiError as err:
            self.error = err.refusal
            return
        self.adopt(started["page"])

    def compose(self, q: Dict[str, Any]) -> Dict[str, Any]:
        kind = q.get("kind")
        if kind == "statement":
            return {"acknowledged": True}
        if kind == "single_choice":
            return {"choice": self.choice}
        if kind == "multi_choice":
            return {"choices": list(self.choices)}
        if kind == "text":
            return {"text": self.text}
        if kind == "currency":
            return {"text": self.choice}
        if kind == "list":
            return {"entries": [e for e in self.entries if any(str(s).strip() for s in e.values())]}
        if kind == "money":
            trimmed = self.amount.strip()
            if not trimmed:
                return {"cents": None}
            units, _, frac = trimmed.replace(",", "").replace(" ", "").partition(".")
            return {"cents": str(int((units or "0") + (frac + "00")[:2]))}
        if kind == "percent":
            return {"percent": float(self.percent) if self.percent.strip() else None}
        if kind in ("roster_single", "roster_multi"):
            return {"people": [p.strip() for p in self.people.split(",") if p.strip()]}
        if kind == "person_or_none":
            first = (q.get("options") or [""])[0]
            if self.choice != first:
                return {"choice": self.choice, "person": None}
            named = self.entries[0] if self.entries else {}
            return {"choice": self.choice, "person": {"name": str(named.get("name", "")).strip(), "email": str(named.get("email", "")).strip()}}
        return {}

    def next(self) -> None:
        q = (self.page or {}).get("question")
        if not q:
            return
        self.error = None
        try:
            advanced = self.app.post("/v1/onboarding/interviews/%s/answers" % self.page["interviewId"], {"questionId": q["questionId"], "value": self.compose(q)})
        except ApiError as err:
            self.error = err.refusal
            walk = (err.refusal.get("walkBackTo") or {}).get("questionId") if isinstance(err.refusal.get("walkBackTo"), dict) else None
            if walk:
                try:
                    self.page = self.app.get("/v1/onboarding/interviews/%s/questions/%s" % (self.page["interviewId"], walk))
                    self.reset({})
                except ApiError:
                    pass
            return
        self.adopt(advanced)

    def confirm(self) -> None:
        interview_id = self.page["interviewId"]
        self.error = None
        try:
            start = self.app.post("/v1/onboarding/interviews/%s/confirm/options" % interview_id, {})
            allow = [c["id"] for c in start["options"].get("allowCredentials") or []]
            assertion = self.app.page.credentials_get(start["options"]["challenge"], allow=allow)
            self.app.post("/v1/onboarding/interviews/%s/confirm" % interview_id, {"issuedAtMs": start["issuedAtMs"], "response": assertion})
            compiled = self.app.post("/v1/onboarding/interviews/%s/compile" % interview_id, {})
        except NotAllowed:
            self.error = {"code": "STEP_UP_INVALID", "message": "The passkey confirmation did not complete; nothing was recorded."}
            return
        except ApiError as err:
            self.error = err.refusal
            return
        if compiled.get("state") == "awaiting_approvals":
            self.page = dict(self.page, state="awaiting_approvals", question=None)
            return
        self.result = compiled

    def set_entry(self, index: int, key: str, value: str) -> None:
        while len(self.entries) <= index:
            self.entries.append({})
        self.entries[index] = dict(self.entries[index], **{key: value})

    def toggle(self, option: str, on: bool) -> None:
        self.choices = [c for c in self.choices if c != option] + ([option] if on else [])

    def render(self) -> El:
        if self.result:
            charter = self.result.get("charter") or {}
            receipt = self.result.get("receipt") or {}
            return h("main", h("h1", "Onboarding"),
                     plain_card(h("h2", "The charter is written"),
                                h("p", "%s is live. Its policy travels the networks %s — Aeredium first, always." % (charter.get("name"), ", ".join(charter.get("allowedChains") or []))),
                                h("p", "The account was opened on the platform as the last step. Account id %s%s." % (
                                    receipt.get("aapAccountId"), (", policy entry %s" % receipt["policyEntryId"]) if receipt.get("policyEntryId") else "")) if receipt.get("aapAccountId")
                                else h("p", "The charter is recorded; this interview opened no new account."),
                                h("p", "Every question, every answer, every revision, who confirmed and when, and this write receipt now live together in the answer record.", cls="muted"),
                                h("p", h("strong", "Next: Create the first wallet account."), " The estate’s first wallet account is born from the Account Creation Interview.",
                                  attrs={"role": "status"})))
        if self.page is None:
            written = bool(self.charter and self.charter.get("standsWritten"))
            return h("main", h("h1", "Onboarding"),
                     h("p", "This estate is established on four things, and the interviews below are where you author all of them."),
                     refusal_notice(self.error) if self.error else None,
                     plain_card(h("h2", "The Policy Interview"),
                                h("p", ("Your charter is written and in force since %s. A charter is amended by running a new interview — it is never repeated; a new interview "
                                        "replaces the standing answers when it is confirmed." % (self.charter or {}).get("inForceSince")) if written else
                                  "The estate’s general charter: the census, your standing, the company ceiling, the agents, the levels beneath. Run once; amended by interview thereafter."),
                                h("button", "Amend the charter with a new interview" if written else "Begin the Policy Interview", click=lambda: self.begin("policy"))),
                     plain_card(h("h2", "Create a wallet account"), h("button", "Create a wallet account", click=lambda: self.begin("wallet_account"))))
        q = self.page.get("question")
        if q is None and self.page.get("state") in ("at_read_back", "in_progress"):
            lines = self.lines or []
            return h("main", h("h1", "The read-back"),
                     h("p", "Every answer, read back in plain sentences. Nothing has been recorded as policy yet. Confirming is the authoring act, under your own passkey.",
                       cls="muted"),
                     refusal_notice(self.error) if self.error else None,
                     plain_card(h("dl", *[h("div", h("dt", l.get("prompt")), h("dd", l.get("spoken")),
                                            None if l.get("synthetic") else h("dd", h("button", "Change this answer", attrs={"aria-label": "Change this answer — %s" % l.get("prompt")},
                                                                                     click=lambda: None))) for l in lines])) if self.lines is not None else None,
                     h("div", h("button", "← Back", attrs={"aria-label": "Back — return to the last question"}, click=lambda: None),
                       h("button", "Confirm with my passkey — author this charter", disabled=self.lines is None, click=self.confirm)
                       if self.page.get("state") == "at_read_back" else h("button", "Continue the interview", click=lambda: None)))
        if q is None:
            return h("main", h("h1", "Onboarding"), refusal_notice(self.error) if self.error else None,
                     card("This charter is written" if self.page.get("state") == "written" else "This interview", h("p", "This interview stands in state %s." % self.page.get("state"))))
        progress = self.page.get("progress") or {}
        line = "%s, question %s of %s. %s of %s overall." % (q.get("part"), progress.get("positionInPart"), progress.get("ofPart"), progress.get("position"), progress.get("of"))
        return h("main", h("h1", "Onboarding"), h("p", line, cls="muted"), refusal_notice(self.error) if self.error else None,
                 plain_card(h("form",
                              h("fieldset", h("legend", q.get("prompt")), h("p", q.get("note"), cls="muted") if q.get("note") else None,
                                h("p", "Recommended: %s." % q["recommended"], cls="muted") if q.get("recommended") else None, *self.controls(q)),
                              h("div", h("button", "← Back", attrs={"aria-label": "Back — return to the previous question"}, disabled=not self.page.get("previousQuestionId"), click=lambda: None),
                                h("button", "Next →", attrs={"aria-label": "Next — commit this answer and continue"}, click=self.next),
                                h("button", "Leave this interview", attrs={"aria-label": "Leave this interview — the draft stays, resumable later; nothing is recorded as policy"},
                                  click=lambda: None)))))

    def controls(self, q: Dict[str, Any]) -> List[Any]:
        kind = q.get("kind")
        out: List[Any] = []
        if kind == "statement":
            out.append(h("p", "Press Next to acknowledge and continue."))
        elif kind == "single_choice":
            for opt in q.get("options") or []:
                out.append(label_of(" ", h("input", kind="radio", checked=self.choice == opt, check=lambda on, opt=opt: setattr(self, "choice", opt)), opt))
        elif kind == "multi_choice":
            for opt in q.get("options") or []:
                out.append(label_of(" ", h("input", kind="checkbox", checked=opt in self.choices, check=lambda on, opt=opt: self.toggle(opt, on)), opt))
        elif kind == "text":
            out.append(label_of("Your answer", h("input", value=self.text, fill=lambda t: setattr(self, "text", t))))
        elif kind == "money":
            out.append(label_of("Amount in US dollars%s" % (" (required)" if q.get("required") else " — leave empty for no limit"),
                                h("input", value=self.amount, fill=lambda t: setattr(self, "amount", t)),
                                hidden("A blank field. No amounts are suggested; you enter the amount yourself."), h("span", "")))
        elif kind == "currency":
            options = [h("option", "Choose…", attrs={"value": ""})] + [h("option", c, attrs={"value": c}) for c in q.get("options") or []]
            out.append(label_of("Currency", h("select", *options, value=self.choice, select=lambda v: setattr(self, "choice", v))))
        elif kind == "percent":
            out.append(label_of("Percentage%s" % (" (required)" if q.get("required") else " — leave empty for never"), h("input", value=self.percent, fill=lambda t: setattr(self, "percent", t))))
        elif kind in ("roster_single", "roster_multi"):
            words = "One email address, from the people you named" if kind == "roster_single" else "Email addresses, comma separated, from the people you named"
            out.append(label_of(words, h("input", value=self.people, fill=lambda t: setattr(self, "people", t))))
        elif kind == "person_or_none":
            for i, opt in enumerate(q.get("options") or []):
                out.append(label_of(" ", h("input", kind="radio", checked=self.choice == opt, check=lambda on, opt=opt: setattr(self, "choice", opt)), opt))
                if i == 0 and self.choice == opt:
                    for field in q.get("listFields") or DEFAULT_LIST_FIELDS:
                        out.append(label_of(field["label"], h("input", value=(self.entries[0] if self.entries else {}).get(field["key"], ""),
                                                              fill=lambda t, key=field["key"]: self.set_entry(0, key, t))))
        elif kind == "list":
            fields = q.get("listFields") or DEFAULT_LIST_FIELDS
            for i, entry in enumerate(self.entries):
                row = []
                for field in fields:
                    text = "%s (entry %d)" % (field["label"], i + 1)
                    if field.get("kind") == "choice" and field.get("options"):
                        options = [h("option", "Choose…", attrs={"value": ""})] + [h("option", o, attrs={"value": o}) for o in field["options"]]
                        row.append(label_of(text, h("select", *options, value=entry.get(field["key"], ""), select=lambda v, i=i, key=field["key"]: self.set_entry(i, key, v))))
                    else:
                        row.append(label_of(text, h("input", value=entry.get(field["key"], ""), fill=lambda t, i=i, key=field["key"]: self.set_entry(i, key, t))))
                out.append(h("div", *row))
            out.append(h("button", "Add another entry", click=lambda: self.entries.append({})))
        return out


# ======================================================================================================================
# web/screens/People.tsx.
# ======================================================================================================================
class People:
    def __init__(self, app: App):
        self.app = app
        self.invites: List[Dict[str, Any]] = []
        self.seats: Optional[Dict[str, Any]] = None
        self.level: Optional[int] = None
        self.error: Optional[Dict[str, Any]] = None
        self.minted: Optional[Dict[str, Any]] = None
        self.name = ""
        self.email = ""
        self.standing = "overseer"
        self.pen = False
        self.said = ""
        self.confirming: Optional[str] = None

    def mount(self) -> None:
        roles = self.app.roles()
        if "author" in roles or "approver" in roles:
            self.load()
        if "author" in roles:
            try:
                self.level = (self.app.get("/v1/visibility").get("standing") or {}).get("level")
            except ApiError:
                pass
            self.load_seats()

    def load(self) -> None:
        try:
            self.invites = self.app.get("/v1/invites")["invites"]
        except ApiError as err:
            self.error = err.refusal

    def load_seats(self) -> None:
        try:
            self.seats = self.app.get("/v1/approver-seats")
        except ApiError as err:
            self.error = err.refusal

    def invite(self) -> None:
        wire = {"executive": "author", "overseer": "viewer"}[self.standing]
        try:
            self.minted = self.app.post("/v1/invites", {"displayName": self.name.strip(), "email": self.email.strip(), "role": wire})
        except ApiError as err:
            self.error = err.refusal
            return
        self.name, self.email, self.standing, self.pen = "", "", "overseer", False
        self.load()

    def revoke(self, row: Dict[str, Any]) -> None:
        """People.tsx revoke: the register's own withdraw road, once the row's second question is answered."""
        self.error = None
        try:
            self.app.post("/v1/invites/%s/revoke" % row["id"])
            self.confirming = None
        except ApiError as err:
            self.error = err.refusal
        self.load()

    def withdraw(self, seat: Dict[str, Any]) -> None:
        try:
            self.app.post("/v1/invites/%s/revoke" % seat["invitation"]["id"], {})
            self.said = "The invitation to %s has been withdrawn." % (seat.get("name") or seat.get("email"))
        except ApiError as err:
            self.error = err.refusal
        self.load_seats()

    def standing_name(self, standing: str) -> str:
        return "Level 1 Executive" if standing == "executive" and self.level == 1 else {"executive": "Executive", "overseer": "Overseer"}[standing]

    def render(self) -> El:
        roles = self.app.roles()
        children: List[Any] = [h("div", h("h1", "People"), h("p", "Invite someone into this estate, and say where they belong."))]
        if self.error:
            children.append(refusal_notice(self.error))
        if self.minted:
            role = self.minted["invite"].get("role")
            words = ("a Level 1 Executive" if self.level == 1 else "an Executive") if role == "author" else "an Overseer"
            link = h("input", value=self.minted["url"], attrs={"readonly": True})
            children.append(plain_card(
                h("h2", "%s has been invited as %s" % (self.minted["invite"]["displayName"], words)),
                h("p", "This link works once and expires soon. It is shown here and nowhere else — the register below will never show it again. Copy it and send it to this person now."),
                h("div", label_of("One-time invitation link", link), h("button", "Copy link", click=lambda: None)),
                h("p", h("strong", "No email sent"), " — ", self.minted["dispatch"]["reason"], cls="hint"),
                h("div", h("button", "I have sent the link — hide it", click=lambda: setattr(self, "minted", None)), cls="actions")))
        if "author" in roles:
            ready = bool(self.name.strip() and self.email.strip() and (self.standing != "executive" or self.pen))
            # an <input type="email"> keeps its value sanitised (HTML's value sanitization algorithm: leading and trailing whitespace stripped), so what
            # a person types around an address never reaches setEmail — the browser's doing, not People.tsx's
            form = [label_of("Full name", h("input", value=self.name, fill=lambda t: setattr(self, "name", t))),
                    label_of("Email address", h("input", kind="email", value=self.email, fill=lambda t: setattr(self, "email", t.strip()))),
                    label_of("Phone number (optional)", h("input", kind="tel", value="", fill=lambda t: None)),
                    h("fieldset", h("legend", "What standing are they being invited to?"),
                      *[h("label", h("input", kind="radio", name=self.standing_name(s), checked=self.standing == s, check=lambda on, s=s: self.choose(s)),
                          h("strong", self.standing_name(s))) for s in ("executive", "overseer")],
                      *[h("label", h("input", kind="radio", name=n, disabled=True, checked=False, check=lambda on: None), h("strong", n))
                        for n in ("Client", "Principal", "Agent Owner", "Agent Manager", "Custody Client")])]
            if self.standing == "executive":
                form.append(h("div", h("p", "An executive has full powers at their level — creates, submits, changes. Invite an executive only when they should hold the pen."),
                              label_of("Yes — %s should hold the pen." % (self.name.strip() or "this person"), h("input", kind="checkbox", checked=self.pen,
                                                                                                             check=lambda on: setattr(self, "pen", on))),
                              cls="banner", attrs={"role": "status"}))
            form.append(h("div", h("button", "Invite, and show me the link", disabled=not ready, click=self.invite), cls="actions"))
            children.append(card("Invite someone to a standing", h("form", *form)))
            children.append(self.seats_panel())
        if "author" in roles or "approver" in roles:
            may_invite = "author" in roles
            rows = [h("tr", h("th", "Person"), h("th", "Invited as"), h("th", "State"), *([h("th", "Send again, or withdraw")] if may_invite else []))]
            for row in self.invites:
                standing = {"author": self.standing_name("executive"), "viewer": "Overseer"}.get(row.get("role") or "", "Not recorded (invited from the command line)")
                cells = [h("th", row["displayName"], *((hidden(", email "), row["email"]) if row.get("email") else ())), h("td", standing),
                         h("td", pill(STATUS_WORDS.get(row["state"], row["state"])), hidden(" — %s" % REGISTER_STATE_SENTENCE.get(row["state"], row["state"])))]
                if may_invite:
                    if row["state"] != "pending":
                        cells.append(h("td", h("span", "—", cls="muted")))
                    elif self.confirming == row["id"]:
                        cells.append(h("td", h("div", h("p", "Withdraw the invitation to %s? Their link stops working at once, and the register keeps the record." % row["displayName"]),
                                               h("button", "Yes — withdraw %s’s invitation" % row["displayName"], click=lambda row=row: self.revoke(row)),
                                               h("button", "Keep it", click=lambda: setattr(self, "confirming", None)),
                                               attrs={"role": "group", "aria-label": "Withdraw the invitation to %s?" % row["displayName"]})))
                    else:
                        cells.append(h("td", h("div", h("button", "Send again", hidden(" — the same invitation, to %s" % row["displayName"]), click=lambda: None),
                                               h("button", "Withdraw", hidden(" the invitation to %s" % row["displayName"]),
                                                 click=lambda row=row: setattr(self, "confirming", row["id"])), cls="actions")))
                rows.append(h("tr", *cells))
            children.append(card("Invitations", h("table", *rows)))
        return h("div", *children)

    def choose(self, standing: str) -> None:
        self.standing = standing
        self.pen = False

    def seats_panel(self) -> El:
        view = self.seats or {}
        body: List[Any] = [h("p", "These are the approvers your charter names, and only they can be given a seat — permissions come from your organisation’s policy, and the charter "
                                  "is how that policy is authored, so naming a new approver is done in an interview."),
                           h("p", self.said, cls="hint", attrs={"role": "status"})]
        if view.get("charterStands") and view.get("summary"):
            body.append(h("p", view["summary"], cls="lede"))
        if not view.get("charterStands"):
            body.append(h("p", "No interview of this estate has been written yet, so there is no charter naming approvers.", cls="empty"))
        else:
            rows = [h("tr", h("th", "Approver"), h("th", "Seat"), h("th", "Action"))]
            for seat in view.get("seats") or []:
                who = seat.get("name") or seat.get("email")
                state = seat.get("state")
                if state == "not_enrolled":
                    action = h("button", "Invite", hidden(" %s" % who), click=lambda seat=seat: self.fill_from(seat))
                elif state == "invited":
                    action = h("div", h("button", "Resend the invitation", hidden(" to %s" % who), click=lambda: None),
                               h("button", "Withdraw it", hidden(" — the invitation to %s" % who), click=lambda seat=seat: self.withdraw(seat)))
                elif state == "seated":
                    action = h("button", "Withdraw the seat", hidden(" from %s" % who), click=lambda: None)
                else:
                    action = h("button", "Grant the seat", hidden(" to %s" % who), click=lambda: None)
                rows.append(h("tr", h("th", who, hidden(", email ") if seat.get("name") else None, seat.get("email") if seat.get("name") else None),
                              h("td", pill(SEAT_STATE_WORDS.get(state, state)), hidden(" — %s" % SEAT_STATE_MEANING.get(state, ""))), h("td", action)))
            body.append(h("table", *rows))
        return card("Approver seats", *body)

    def fill_from(self, seat: Dict[str, Any]) -> None:
        self.name = seat.get("name") or ""
        self.email = seat.get("email") or ""


# ======================================================================================================================
# web/screens/Wallets.tsx.
# ======================================================================================================================
class Wallets:
    def __init__(self, app: App):
        self.app = app
        self.payload: Optional[Dict[str, Any]] = None
        self.funding: Optional[Dict[str, Any]] = None
        self.offer = False
        self.stage = "idle"
        self.whose = "estate"
        self.born: Optional[Dict[str, Any]] = None
        self.refusal: Optional[Dict[str, Any]] = None

    def mount(self) -> None:
        self.load()
        self.funding = self.app.get("/v1/workspace")
        roles = self.app.get("/v1/auth/session").get("roles") or []
        standing = (self.app.get("/v1/visibility").get("standing") or {}).get("kind")
        self.offer = "author" in roles and standing == "root"

    def load(self) -> None:
        self.payload = self.app.get("/v1/aer360/wallets?")

    def assert_with(self, start: Dict[str, Any]) -> Dict[str, Any]:
        allow = [c["id"] for c in start["options"].get("allowCredentials") or []]
        return self.app.page.credentials_get(start["options"]["challenge"], allow=allow)

    def press_funding(self) -> None:
        self.refusal = None
        try:
            start = self.app.post("/v1/workspace/funding-wallet/options", {})
            response = self.assert_with(start)
            self.app.post("/v1/workspace/funding-wallet", {"issuedAtMs": start["issuedAtMs"], "response": response})
            self.funding = self.app.get("/v1/workspace")
        except NotAllowed:
            self.refusal = {"code": "STEP_UP_INVALID", "message": "The passkey signature did not complete; nothing was recorded."}
        except ApiError as err:
            self.refusal = err.refusal

    def press_new_wallet(self) -> None:
        self.stage = "pressing"
        self.refusal = None
        try:
            start = self.app.post("/v1/workspace/wallets/options", {"whose": self.whose})
            response = self.assert_with(start)
            born = self.app.post("/v1/workspace/wallets", {"whose": self.whose, "issuedAtMs": start["issuedAtMs"], "response": response, "walletId": start["walletId"]})
            self.born = born["wallet"]
            self.load()
        except NotAllowed:
            self.refusal = {"code": "STEP_UP_INVALID", "message": "The passkey signature did not complete; nothing was recorded."}
        except ApiError as err:
            self.refusal = err.refusal
        self.stage = "idle"

    def render(self) -> El:
        children: List[Any] = [h("h1", "Wallets")]
        wallet = (self.funding or {}).get("fundingWallet")
        if wallet:
            children.append(h("p", wallet["sentence"], attrs={"role": "note", "aria-label": "Funding wallet"}))
            children.append(h("p", wallet["fundSentence"], attrs={"role": "note", "aria-label": "Fund this account"}))
            if self.offer:
                body: List[Any] = []
                if self.stage == "idle":
                    body.append(h("button", "Create a new wallet", click=lambda: setattr(self, "stage", "confirm")))
                if self.stage == "confirm":
                    body.append(h("fieldset", h("legend", "Whose wallet is this?"),
                                  label_of(" ", h("input", kind="radio", checked=self.whose == "estate", check=lambda on: setattr(self, "whose", "estate")), "This estate"),
                                  label_of(" ", h("input", kind="radio", checked=self.whose == "client", check=lambda on: setattr(self, "whose", "client")), "A client’s")))
                    body.append(h("p", "%s: %s" % LEVEL_ONE, attrs={"role": "note", "aria-label": "Before this wallet is born"}))
                    body.append(h("button", "Create it", click=self.press_new_wallet))
                    body.append(h("button", "Not now", click=lambda: setattr(self, "stage", "idle")))
                if self.refusal:
                    body.append(refusal_notice(self.refusal))
                if self.born and self.stage == "idle" and not self.refusal:
                    body.append(h("p", "Wallet %s is born%s. It is counted below." % (self.born["walletNumber"], (": %s" % self.born["address"]) if self.born.get("address") else ""),
                                  attrs={"role": "status"}))
                children.append(card("A new wallet", *body))
        elif self.funding is not None:
            children.append(card("Funding wallet", h("p", self.funding.get("fundingWalletAbsence"), cls="empty"),
                                 h("button", "Give this estate its funding wallet", click=self.press_funding), refusal_notice(self.refusal) if self.refusal else None))
        for w in ((self.payload or {}).get("register") or {}).get("wallets") or []:
            if w.get("funding"):
                continue
            children.append(card(" · ".join([w["walletNumber"], w["name"]] + ([w["address"]] if w.get("address") else [])),
                                 h("p", LEVEL_ONE[0], attrs={"role": "note", "aria-label": "Level of wallet %s" % w["walletNumber"]}),
                                 h("p", w["fundSentence"], attrs={"role": "note", "aria-label": "Fund wallet %s" % w["walletNumber"]}),
                                 h("p", "Its holdings are read at the next refresh and counted at the next close.", cls="hint"),
                                 h("p", h("a", "Pay from this wallet", attrs={"href": "/entry?wallet=%s" % w["walletId"]},
                                          click=lambda w=w: self.app.navigate("/entry?wallet=%s" % w["walletId"]))) if w.get("keyed") else None))
        return h("section", *children, attrs={"aria-labelledby": "wallets-heading"})


# ======================================================================================================================
# web/screens/PayeeRegistry.tsx.
# ======================================================================================================================
def payee_address_refusal(chain: str, address: str) -> Optional[Dict[str, Any]]:
    """shared/payeeaddress.ts payeeAddressRefusal: the shape (trimmed first), then the EIP-55 checksum where the letters are mixed."""
    trimmed = address.strip()
    named = CHAIN_NAMES.get(chain, chain)
    if not re.match(r"^0x[0-9a-fA-F]{40}$", trimmed):
        return {"code": "ADDRESS_MALFORMED", "message": "That is not an address %s can pay, so nothing was saved. On %s, an address is 0x followed by exactly 40 hexadecimal "
                                                         "characters." % (named, named), "detail": {"field": "address", "chain": chain, "address": address}}
    digits = trimmed[2:]
    if re.search(r"[a-f]", digits) and re.search(r"[A-F]", digits):
        from aer360_tables import checksum_address
        if checksum_address(trimmed) != trimmed:
            return {"code": "ADDRESS_CHECKSUM_MISMATCH", "message": "This address does not match its own checksum, so it is a mistyped or altered address. Nothing was saved. "
                                                                    "Check every character against the source and enter it again."}
    return None


class Payees:
    def __init__(self, app: App):
        self.app = app
        self.payees: List[Dict[str, Any]] = []
        self.error: Optional[Dict[str, Any]] = None
        self.address_refusal: Optional[Dict[str, Any]] = None
        self.pending_said: Dict[str, str] = {}
        self.name = ""
        self.chain = "ethereum"
        self.address = ""

    def mount(self) -> None:
        self.load()

    def load(self) -> None:
        try:
            self.payees = self.app.get("/v1/payees")["payees"]
            self.app.get("/v1/counterparties")
            self.app.get("/v1/deposits")
            self.app.get("/v1/sets")
            self.error = None
        except ApiError as err:
            self.error = err.refusal

    def act(self, path: str, body: Any = None, address_id: Optional[str] = None) -> None:
        self.error = None
        try:
            answer = self.app.post(path, body)
        except ApiError as err:
            self.error = err.refusal
            return
        if address_id:
            said = answer.get("sentence") if isinstance(answer, dict) else None
            if isinstance(said, str) and said:
                self.pending_said[address_id] = said
            else:
                self.pending_said.pop(address_id, None)
        self.load()

    def add(self) -> None:
        refused = payee_address_refusal(self.chain, self.address) if self.chain in KNOWN_CHAINS else None
        self.address_refusal = refused
        if refused:
            return
        self.act("/v1/payees", {"displayName": self.name, "defaultChain": self.chain, "addresses": [{"chain": self.chain, "address": self.address}]})
        self.name, self.address = "", ""

    def render(self) -> El:
        rows = [h("tr", h("th", "Payee"), h("th", "Chain"), h("th", "Address"), h("th", "Whitelisted?"), h("th", "Action"))]
        for payee in self.payees:
            for a in payee["addresses"]:
                status = a["whitelistStatus"]
                if status == "proposed":
                    action = h("button", "Send for approval", click=lambda a=a: self.act("/v1/payees/addresses/%s/promote" % a["id"], None, a["id"]))
                elif status == "pending_promotion":
                    action = h("div", h("button", "Approve", click=lambda a=a: self.act("/v1/payees/addresses/%s/approve" % a["id"], None, a["id"])),
                               h("button", "Reject", click=lambda a=a: self.act("/v1/payees/addresses/%s/reject" % a["id"], None, a["id"])),
                               h("div", "Approving records your own signature. The address stands once everyone your charter named has approved it.", cls="muted"))
                else:
                    action = h("span", "—", cls="muted")
                said = self.pending_said.get(a["id"])
                rows.append(h("tr", h("th", payee["displayName"], pill("Approved payee" if status == "whitelisted" else "One-off")), h("td", a["chain"]),
                              h("td", a["address"][:6] + "…" + a["address"][-4:]),
                              h("td", pill(STATUS_WORDS.get(status, status)), h("p", said, cls="muted", attrs={"role": "status"}) if said else None), h("td", action)))
        return h("div", h("div", h("h1", "Payees and counterparties"), h("p", "Who you pay, and who pays you.")),
                 refusal_notice(self.error) if self.error else None,
                 card("Add a payee",
                      h("div", label_of("Name", h("input", value=self.name, fill=lambda t: setattr(self, "name", t))),
                        label_of("Chain", h("input", value=self.chain, fill=lambda t: setattr(self, "chain", t))),
                        label_of("Address", h("input", value=self.address, fill=lambda t: setattr(self, "address", t)))),
                      refusal_notice(self.address_refusal) if self.address_refusal else None,
                      h("div", h("button", "Add payee", disabled=not self.name or not self.address, click=self.add), cls="actions")),
                 card("Payees — who you pay", h("table", *rows) if self.payees else h("p", "No payees yet.", cls="empty")))


# ======================================================================================================================
# web/screens/PaymentEntry.tsx.
# ======================================================================================================================
def to_minor(amount: str, decimals: int) -> Optional[str]:
    text = amount.strip()
    if not re.match(r"^\d+(?:\.\d+)?$", text):
        return None
    whole, _, fraction = text.partition(".")
    if len(fraction) > decimals:
        return None
    value = (whole + fraction.ljust(decimals, "0")).lstrip("0")
    return value or "0"


class PaymentEntry:
    def __init__(self, app: App, wallet_id: str):
        self.app = app
        self.wallet_id = wallet_id
        self.payees: List[Dict[str, Any]] = []
        self.sources: List[Dict[str, Any]] = []
        self.rows: List[Dict[str, Any]] = [self.blank()]
        self.review: Optional[Dict[str, Any]] = None
        self.error: Optional[Dict[str, Any]] = None
        self.acknowledged = False
        self.reference = ""
        self.attempt = str(uuid.uuid4())

    @staticmethod
    def blank() -> Dict[str, Any]:
        return {"payeeAddressId": "", "oneOffAddress": "", "oneOffName": "", "isOneOff": False, "asset": "ETH", "chain": "anvil", "amount": "", "invoiceRef": ""}

    def mount(self) -> None:
        try:
            self.payees = self.app.get("/v1/payees")["payees"]
        except ApiError as err:
            self.error = err.refusal
        try:
            register = self.app.get("/v1/aer360/wallets").get("register") or {}
            self.sources = [w for w in register.get("wallets") or [] if w.get("keyed") is True]
        except ApiError:
            self.sources = []

    def pays(self) -> List[Dict[str, Any]]:
        out = []
        for r in self.rows:
            minor = to_minor(r["amount"], ASSET_DECIMALS.get(r["asset"], 18)) or "0"
            if r["isOneOff"]:
                pay: Dict[str, Any] = {"oneOff": dict({"chain": r["chain"], "address": r["oneOffAddress"], "declared": True}, **({"payeeName": r["oneOffName"]} if r["oneOffName"] else {})),
                                       "asset": r["asset"], "chain": r["chain"], "amountMinor": minor}
            else:
                pay = {"payeeAddressId": r["payeeAddressId"], "asset": r["asset"], "chain": r["chain"], "amountMinor": minor}
            if r["invoiceRef"]:
                pay["invoiceRef"] = r["invoiceRef"]
            out.append(pay)
        return out

    def run_review(self) -> None:
        self.error = None
        try:
            self.review = self.app.post("/v1/sets/review", {"pays": self.pays(), "duplicatesAcknowledged": self.acknowledged, "walletId": self.wallet_id or None})
        except ApiError as err:
            self.review = None
            self.error = err.refusal

    def create(self) -> None:
        self.error = None
        try:
            created = self.app.post("/v1/sets", {"pays": self.pays(), "duplicatesAcknowledged": self.acknowledged, "walletId": self.wallet_id or None,
                                                 "reference": self.reference or "Payment run", "idempotencyKey": self.attempt})
        except ApiError as err:
            if err.refusal.get("code") == "IDEMPOTENCY_KEY_REUSED":
                self.attempt = str(uuid.uuid4())
            self.error = err.refusal
            return
        self.attempt = str(uuid.uuid4())
        run_id = created["set"]["id"]
        if created.get("alreadyExisted") is True and created["set"]["status"] != "draft":
            self.app.navigate("/runs/%s" % run_id)
            return
        try:
            answer = self.app.post("/v1/sets/%s/submit" % run_id)
            state: Dict[str, Any] = {"submitted": {"status": answer["status"], "approvalsRequired": answer["approvalsRequired"]}}
        except ApiError as err:
            state = {"submitRefused": err.refusal if err.from_server else None}
        self.app.navigate("/runs/%s" % run_id, state)

    def update(self, index: int, key: str, value: Any) -> None:
        self.rows[index] = dict(self.rows[index], **{key: value})

    def source_label(self, w: Dict[str, Any]) -> str:
        return "%s · %s · %s%s" % (w["walletNumber"], w["name"], LEVEL_ONE[0], (" · held for %s" % w["beneficiary"]) if w.get("beneficiary") else "")

    def render(self) -> El:
        children: List[Any] = [h("div", h("h1", "Enter payments"), h("p", "Every payment is checked before the run exists: the payee list, the price in your currency, your "
                                                                         "monthly signature allowance, network fees, and anything that looks like a repeat."))]
        if self.error:
            children.append(refusal_notice(self.error))
        run_card = [h("div", label_of("Reference for this run", h("input", value=self.reference, attrs={"placeholder": "Weekly supplier run, 31 July"},
                                                                   fill=lambda t: setattr(self, "reference", t))), h("p", "Shown everywhere this run appears.", cls="hint"))]
        if self.sources or self.wallet_id:
            options = [h("option", "This estate’s funding wallet", attrs={"value": ""})] + [h("option", self.source_label(w), attrs={"value": w["walletId"]}) for w in self.sources]
            run_card.append(h("div", label_of("Pay from", h("select", *options, value=self.wallet_id, select=lambda v: setattr(self, "wallet_id", v))),
                              h("p", "A payment leaves the wallet it names, signed under that wallet’s own key.", cls="hint")))
        children.append(card("The run", *run_card))
        review_rows = {r["index"]: r for r in (self.review or {}).get("rows") or []}
        for index, row in enumerate(self.rows):
            body: List[Any] = [label_of(" ", h("input", kind="checkbox", checked=row["isOneOff"], check=lambda on, index=index: self.update(index, "isOneOff", on)),
                                        "This is a one-off payment to an address that is not on our approved list")]
            if row["isOneOff"]:
                body.append(label_of("Who is being paid", h("input", value=row["oneOffName"], fill=lambda t, index=index: self.update(index, "oneOffName", t))))
                body.append(label_of("Address", h("input", value=row["oneOffAddress"], fill=lambda t, index=index: self.update(index, "oneOffAddress", t))))
            else:
                options = [h("option", "Choose a payee…", attrs={"value": ""})] + [
                    h("option", "%s — %s — %s" % (p["displayName"], a["chain"], "approved" if a["whitelistStatus"] == "whitelisted" else a["whitelistStatus"].replace("_", " ")),
                      attrs={"value": a["id"]}) for p in self.payees for a in p["addresses"]]
                body.append(label_of("Payee", h("select", *options, value=row["payeeAddressId"], select=lambda v, index=index: self.update(index, "payeeAddressId", v))))
            body.append(label_of("Chain", h("input", value=row["chain"], fill=lambda t, index=index: self.update(index, "chain", t))))
            body.append(label_of("Asset", h("input", value=row["asset"], fill=lambda t, index=index: self.update(index, "asset", t.upper()))))
            body.append(label_of("Amount", h("input", value=row["amount"], fill=lambda t, index=index: self.update(index, "amount", t))))
            body.append(label_of("Reference (inv #, description)", h("input", value=row["invoiceRef"], fill=lambda t, index=index: self.update(index, "invoiceRef", t))))
            reviewed = review_rows.get(index)
            if reviewed:
                body.extend(refusal_notice(r) for r in reviewed.get("refusals") or [])
            if len(self.rows) > 1:
                body.append(h("button", "Remove this payment", click=lambda index=index: self.rows.pop(index)))
            children.append(card("Payment %d" % (index + 1), *body))
        children.append(h("div", h("button", "Add another payment", click=lambda: self.rows.append(self.blank())), h("button", "Check this run", click=self.run_review),
                          cls="actions"))
        if self.review:
            rows = [h("tr", h("th", "Check"), h("th", "Result"), h("th", "What was found"))]
            for gate in self.review.get("gates") or []:
                rows.append(h("tr", h("th", GATE_LABELS.get(gate["gate"], gate["gate"])), h("td", pill("Passed" if gate.get("passed") else "Stopped")), h("td", gate.get("evidence") or "—")))
            wallet = self.review.get("wallet")
            approval = self.review.get("approval")
            total = self.review.get("aggregate") or {}
            words = None
            if approval:
                words = (" · your organisation’s policy requires no approval for this run — it executes when you submit it" if approval.get("approvalsRequired") == 0 else
                         " · needs %d approval%s, and never yours" % (approval["approvalsRequired"], "" if approval["approvalsRequired"] == 1 else "s"))
            ack = self.review.get("acknowledgeable") or []
            body = [h("table", *rows),
                    *[refusal_notice(r) for g in self.review.get("gates") or [] if not g.get("passed") for r in g.get("refusals") or [] if r.get("rowIndex") is None],
                    h("p", ("This run leaves from wallet %s (%s)." % (self.source_label(wallet), wallet["address"])) if wallet else "This run leaves from this estate’s funding wallet.",
                      attrs={"role": "note", "aria-label": "Leaves from"}),
                    h("p", "Run total: ", h("strong", "US$%s" % total.get("amountBaseMinor")), h("span", words) if words else None) if self.review.get("aggregate") else None]
            if ack:
                body.append(h("div", label_of(" ", h("input", kind="checkbox", checked=self.acknowledged, check=lambda on: setattr(self, "acknowledged", on)),
                                              "I have checked the possible repeat%s above and want to continue" % ("" if len(ack) == 1 else "s")),
                              h("p", "Your acknowledgement is recorded against the run.", cls="hint")))
            body.append(h("div", h("button", "Check again", click=self.run_review), h("button", "Submit this run", disabled=not self.review.get("acceptable"), click=self.create),
                          cls="actions"))
            children.append(card("What the checks found", *body))
        return h("div", *children)


# ======================================================================================================================
# web/screens/Runs.tsx — a run's own page.
# ======================================================================================================================
def run_status_words(run: Dict[str, Any]) -> str:
    """shared/runs.ts runStatusWords."""
    status = run.get("status")
    instructions = run.get("instructions") or []
    if status in ("draft", "cancelled"):
        return status
    if status == "pending_approval":
        required = (run.get("approval") or {}).get("approvalsRequired") or 0
        return "waiting for the client’s approval" if required == 0 else "waiting for approvals (%s of %s)" % ((run.get("approval") or {}).get("approvalsGiven") or 0, required)
    landed = sum(1 for i in instructions if i.get("status") == "confirmed")
    failed = sum(1 for i in instructions if i.get("status") in ("failed", "rejected"))
    if status == "settled":
        return "landed"
    if status == "partially_settled":
        return "failed" if landed == 0 else ("landed" if failed == 0 else "landed %d of %d, failed %d" % (landed, len(instructions), failed))
    return str(status)


def payment_status_words(i: Dict[str, Any]) -> str:
    if i.get("status") == "confirmed":
        return "landed"
    if i.get("status") == "queued" and i.get("failureReason"):
        return "not sent"
    return str(i.get("status"))


def submitted_words(answer: Dict[str, Any]) -> str:
    if answer.get("status") == "approved":
        return "Submitted: approved, executing."
    if answer.get("approvalsRequired") == 0:
        return "Submitted: waiting for the client’s approval."
    n = answer.get("approvalsRequired")
    return "Submitted: waiting for %s approval%s." % (n, "" if n == 1 else "s")


class RunPage:
    def __init__(self, app: App, run_id: str, state: Optional[Dict[str, Any]]):
        self.app = app
        self.run_id = run_id
        self.arrived = state
        self.run: Optional[Dict[str, Any]] = None
        self.refusal: Optional[Dict[str, Any]] = None

    def mount(self) -> None:
        self.read()

    def read(self) -> None:
        try:
            self.run = self.app.get("/v1/sets/%s" % self.run_id)["set"]
        except ApiError as err:
            self.refusal = err.refusal

    def press(self, path: str) -> None:
        self.refusal = None
        try:
            self.app.post(path)
        except ApiError as err:
            self.refusal = err.refusal
        self.read()

    def approvals(self, run: Dict[str, Any]) -> Optional[El]:
        """Runs.tsx:354-360: a run waiting on approvals says how many are given, "in the Approver inbox" — plain words at b523cbf, a link where the inbox's cards carry an anchor."""
        approval = run.get("approval") or {}
        if run.get("status") != "pending_approval" or not approval.get("approvalsRequired"):
            return None
        where: Any = "the Approver inbox"
        if Inbox.CARD_NAMES_ITS_RUN == "anchor":
            where = h("a", "the Approver inbox", attrs={"href": "/inbox#run-%s" % run["id"]}, click=lambda: self.app.navigate("/inbox"))
        return h("dl", h("dt", "Approvals"), h("dd", "%s of %s given, in " % (approval.get("approvalsGiven") or 0, approval.get("approvalsRequired")), where))

    def render(self) -> El:
        if not self.run:
            return h("div", h("p", h("a", "All runs", attrs={"href": "/runs"}, click=lambda: None)), h("h1", "Runs"), refusal_notice(self.refusal) if self.refusal else None)
        run = self.run
        me = (self.app.session or {}).get("credentialId")
        roles = self.app.roles()
        words = run_status_words(run)
        own = "author" in roles and run.get("authorCredentialId") == me
        actions: List[Any] = []
        if own and run.get("status") == "draft":
            actions.append(h("button", "Submit", click=lambda: self.press("/v1/sets/%s/submit" % self.run_id)))
        if own and run.get("status") in ("draft", "pending_approval", "approved"):
            actions.append(h("button", "Cancel", click=lambda: self.press("/v1/sets/%s/cancel" % self.run_id)))
        rows = [h("tr", h("th", "Payee"), h("th", "Amount"), h("th", "Asset"), h("th", "Chain"), h("th", "Status"), h("th", "Transaction"), h("th", "Reason"))]
        for i in run.get("instructions") or []:
            chain = CHAIN_NAMES.get(i.get("chain"), i.get("chain"))
            tx = h("a", "%s…%s" % (i["txHash"][:6], i["txHash"][-4:]), hidden(" — this transaction on the %s explorer" % chain),
                   attrs={"href": "https://arbiscan.io/tx/%s" % i["txHash"]}, click=lambda: None) if i.get("txHash") else "—"
            reason = i.get("failureReason") or "—"
            rows.append(h("tr", h("th", i.get("payeeName"), pill("One-off" if i.get("isOneOff") else "Approved payee"), "%s…%s" % (i["address"][:6], i["address"][-4:])),
                          h("td", str(int(i["amountMinor"]) / 10 ** 6)), h("td", i.get("asset")), h("td", chain), h("td", pill(payment_status_words(i))), h("td", tx), h("td", reason)))
        submitted = (self.arrived or {}).get("submitted")
        return h("div",
                 h("p", h("a", "All runs", attrs={"href": "/runs"}, click=lambda: None)),
                 h("div", h("h1", run.get("reference")), h("p", "Created %s · leaves from %s" % (run.get("createdAt"), run.get("sourceAccount")))),
                 h("p", submitted_words(submitted), attrs={"role": "status", "aria-label": "Your submission"}) if submitted else None,
                 refusal_notice((self.arrived or {})["submitRefused"]) if (self.arrived or {}).get("submitRefused") else None,
                 refusal_notice(self.refusal) if self.refusal else None,
                 card("Where it stands", h("p", pill(words), attrs={"role": "status", "aria-label": "Status of this run"}),
                      self.approvals(run), h("div", *actions, cls="actions")),
                 card("Payments", h("table", *rows)))


# ======================================================================================================================
# web/screens/ApproverInbox.tsx.
# ======================================================================================================================
class Inbox:
    # Whether a card names its run. None: as ApproverInbox.tsx renders it at b523cbf — no id, no data attribute, no link: the card names no run.
    # "link": an estate whose card links to its run's page (/runs/<id>). "anchor": one whose card carries an anchor that the run's own page
    # links to (/inbox#run-<id>, from "in the Approver inbox" on the run's page).
    CARD_NAMES_ITS_RUN: Optional[str] = None

    def __init__(self, app: App):
        self.app = app
        self.sets: List[Dict[str, Any]] = []
        self.error: Optional[Dict[str, Any]] = None

    def mount(self) -> None:
        self.load()

    def load(self) -> None:
        try:
            self.sets = self.app.get("/v1/approvals/inbox")["sets"]
        except ApiError as err:
            self.error = err.refusal

    def approve(self, run: Dict[str, Any]) -> None:
        self.error = None
        try:
            challenge = self.app.post("/v1/approvals/%s/challenge" % run["id"])["challenge"]
            assertion = self.app.page.credentials_get(challenge, allow=[])
            self.app.post("/v1/approvals/%s/approve" % run["id"], {"response": assertion})
            self.load()
        except NotAllowed:
            self.error = {"code": "STEP_UP_INVALID", "message": "The passkey confirmation did not complete, so nothing was approved."}
        except ApiError as err:
            self.error = err.refusal

    def render(self) -> El:
        children: List[Any] = [h("div", h("h1", "Approver inbox"), h("p", "One passkey confirmation approves a whole run, over a digest of every payment in it.")),
                               refusal_notice(self.error) if self.error else None, h("h2", "Payments waiting approval")]
        if not self.sets:
            children.append(plain_card(h("p", "Nothing is waiting for your approval.", cls="empty")))
        for run in self.sets:
            rows = [h("tr", h("th", "Payee"), h("th", "Address"), h("th", "Reference"), h("th", "Value now"))]
            for i in run["instructions"]:
                rows.append(h("tr", h("td", i["payeeName"]), h("td", "%s…%s" % (i["address"][:6], i["address"][-4:])), h("td", i.get("invoiceRef") or "—"), h("td", "—")))
            approval = run.get("approval") or {}
            names = self.CARD_NAMES_ITS_RUN
            children.append(card(run["reference"],
                                 h("p", h("a", "Open this run", attrs={"href": "/runs/%s" % run["id"]}, click=lambda run=run: self.app.navigate("/runs/%s" % run["id"])))
                                 if names == "link" else None,
                                 h("table", *rows),
                                 h("p", "%s of %s approval%s given." % (approval.get("approvalsGiven"), approval.get("approvalsRequired"), "" if approval.get("approvalsRequired") == 1 else "s")),
                                 h("div", h("button", "Approve with passkey", disabled=not run.get("mayApprove"), click=lambda run=run: self.approve(run)),
                                   h("button", "Send back for editing", click=lambda: None), cls="actions"),
                                 h("p", run["blockedSentence"], cls="hint") if not run.get("mayApprove") and run.get("blockedSentence") else None,
                                 action=pill("Pending approval"), attrs={"id": "run-%s" % run["id"]} if names == "anchor" else None))
        return h("div", *children)
