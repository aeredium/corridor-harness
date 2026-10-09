"""
THE SCREENS' DOUBLE (Spec HRW-1's tests): a stand-in for Playwright's sync API that renders the AER 360 pages the browser leg walks,
each as its TSX renders it at aeredium/AERAccounts b523cbf — the same headings, the same controls by the same accessible names, the same
sentences — and makes the calls the TSX makes, in the order the TSX makes them, into the estate's own double (tests/test_aer360_double.py,
EstateDouble), extended below for the roads the screens use and the API leg never did. A passkey ceremony is answered by a virtual
authenticator double, keyed by the Mac's own openssl as the API leg's software passkey is, which the estate double verifies as
@simplewebauthn/server verifies a `none` attestation.

AS STRICT AS THE REAL PARTY: a control the page does not render cannot be found, and waiting for it times out; a disabled control cannot be
pressed; a CSS selector the double does not know is refused rather than guessed; a ceremony on a page with no authenticator attached, or with
one that holds no resident key or does not verify the user, fails as Chrome fails it; a run is executed by the estate the moment its approvals
land (Spec AER360-RUN-ROAD), never by the page; roster seats are written folded (Spec AER360-SEAT-CASE); and the compile writes the charter's
ceilings onto the estate's own signing entries, which the platform's read road reports at zero until then (Spec AER360-115).

The strings below are the screens' own, restated here and NOT read from aer360_screens.py, so a wrong pin in the harness's table is a control
the harness cannot find in this double — the way a wrong pin would meet the real page.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import http.cookiejar
import json
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_real_world as R  # noqa: E402
import aer360_tables as T  # noqa: E402
from tests import test_aer360_double as D  # noqa: E402


class FakeTimeout(Exception):
    """Stands for playwright.sync_api.TimeoutError: the thing waited for never came."""


class FakeError(Exception):
    """Stands for playwright.sync_api.Error: the browser refused what it was asked."""


class NotAllowed(Exception):
    """A WebAuthn ceremony the browser ended without a credential (NotAllowedError): the page's own catch takes it."""


# ======================================================================================================================
# The page's elements: a small accessibility tree, rebuilt from the screen's state on every query.
# ======================================================================================================================
IMPLICIT_ROLES = {"button": "button", "nav": "navigation", "main": "main", "select": "combobox", "tr": "row", "option": "option",
                  "h1": "heading", "h2": "heading", "h3": "heading", "table": "table", "ul": "list", "li": "listitem", "ol": "list", "form": "form"}


class El:
    def __init__(self, tag: str, *children: Any, role: Optional[str] = None, name: Optional[str] = None, cls: str = "", attrs: Optional[Dict[str, Any]] = None,
                 click: Optional[Callable[[], None]] = None, fill: Optional[Callable[[str], None]] = None, check: Optional[Callable[[bool], None]] = None,
                 select: Optional[Callable[[str], None]] = None, value: Optional[str] = None, checked: Optional[bool] = None, disabled: bool = False,
                 label: Optional[str] = None, kind: Optional[str] = None):
        self.tag = tag
        self.children = [c for c in children if c is not None and c is not False and c != ""]
        self.cls = cls.split()
        self.attrs = dict(attrs or {})
        self.on_click = click
        self.on_fill = fill
        self.on_check = check
        self.on_select = select
        self.value = value
        self.checked = checked
        self.disabled = disabled
        self.label = label  # the label's text content, as Playwright computes a form control's name from it
        self.kind = kind    # an input's type
        explicit = role or self.attrs.get("role")
        if explicit:
            self.role = explicit
        elif tag == "input":
            self.role = {"checkbox": "checkbox", "radio": "radio"}.get(kind or "text", "textbox")
        elif tag == "a":
            self.role = "link"
        else:
            self.role = IMPLICIT_ROLES.get(tag)
        self.level = int(tag[1]) if re.match(r"^h[1-6]$", tag) else None
        self._name = name

    def text(self) -> str:
        """The element's text, visually hidden words included (as innerText and an accessible name include them)."""
        parts: List[str] = []
        for c in self.children:
            parts.append(c.text() if isinstance(c, El) else str(c))
        return " ".join(" ".join(parts).split())

    @property
    def name(self) -> str:
        if self.attrs.get("aria-label"):
            return str(self.attrs["aria-label"])
        if self._name is not None:
            return self._name
        if self.tag in ("input", "select", "textarea"):
            return self.label or ""
        if self.role in ("button", "link", "heading", "option", "row", "radio", "checkbox"):
            return self.text()
        return ""

    def walk(self) -> Iterator["El"]:
        for c in self.children:
            if isinstance(c, El):
                yield c
                yield from c.walk()


def h(tag: str, *children: Any, **kw: Any) -> El:
    return El(tag, *children, **kw)


def label_of(text: str, control: El, *after: Any) -> El:
    """`<label>{text}<control/>…</label>`: the control named by the label's whole text, hidden words and all."""
    control.label = " ".join(" ".join([text] + [a.text() if isinstance(a, El) else str(a) for a in after]).split())
    return El("label", text, control, *after)


def matches_name(actual: str, wanted: Any, exact: bool) -> bool:
    actual = " ".join(str(actual).split())
    if isinstance(wanted, re.Pattern):
        return bool(wanted.search(actual))
    wanted = " ".join(str(wanted).split())
    return actual == wanted if exact else wanted.lower() in actual.lower()


# The CSS the harness may ask for, and nothing else: a selector the double does not know is refused, never guessed.
def css_predicate(selector: str) -> Callable[[El, List[El]], bool]:
    simple = {
        "section.card": lambda e: e.tag == "section" and "card" in e.cls,
        ".refusal": lambda e: "refusal" in e.cls,
        "legend": lambda e: e.tag == "legend",
        "main": lambda e: e.tag == "main",
        "p": lambda e: e.tag == "p",
        "option": lambda e: e.tag == "option",
        "dt": lambda e: e.tag == "dt",
        "dd": lambda e: e.tag == "dd",
        "dl": lambda e: e.tag == "dl",
    }
    if selector in simple:
        test = simple[selector]
        return lambda e, ancestors: test(e)
    if selector == "nav[aria-label='Sections'] .brand":
        return lambda e, ancestors: "brand" in e.cls and any(a.tag == "nav" and a.attrs.get("aria-label") == "Sections" for a in ancestors)
    if selector == "dl > div":
        return lambda e, ancestors: e.tag == "div" and bool(ancestors) and ancestors[-1].tag == "dl"
    raise FakeError("the screens' double knows no CSS selector %r; add it to the double where the page renders it" % selector)


class Locator:
    """A query, evaluated against the page as it stands when an action or a read is made — as Playwright's locators are."""

    def __init__(self, page: "Page", steps: List[Tuple[Any, ...]]):
        self.page = page
        self.steps = steps

    # -- composing -------------------------------------------------------------------------------------------------
    def _with(self, step: Tuple[Any, ...]) -> "Locator":
        return Locator(self.page, self.steps + [step])

    def get_by_role(self, role: str, name: Any = None, exact: bool = False, level: Optional[int] = None) -> "Locator":
        return self._with(("role", role, name, exact, level))

    def get_by_label(self, text: Any, exact: bool = False) -> "Locator":
        return self._with(("label", text, exact))

    def locator(self, selector: str) -> "Locator":
        return self._with(("css", selector, css_predicate(selector)))

    def filter(self, has_text: Any = None, has: Optional["Locator"] = None) -> "Locator":
        return self._with(("filter", has_text, has))

    @property
    def first(self) -> "Locator":
        return self._with(("nth", 0))

    def nth(self, index: int) -> "Locator":
        return self._with(("nth", index))

    # -- evaluating ------------------------------------------------------------------------------------------------
    def resolve(self, roots: Optional[List[El]] = None) -> List[El]:
        current = roots if roots is not None else [self.page.render()]
        for step in self.steps:
            kind = step[0]
            if kind in ("role", "label", "css"):
                found: List[El] = []
                for root in current:
                    for element, ancestors in descendants_with_ancestors(root):
                        if kind == "role":
                            _, role, name, exact, level = step
                            if element.role != role or (level is not None and element.level != level):
                                continue
                            if name is not None and not matches_name(element.name, name, exact):
                                continue
                        elif kind == "label":
                            _, text, exact = step
                            if element.tag not in ("input", "select", "textarea") or element.label is None or not matches_name(element.label, text, exact):
                                continue
                        else:
                            if not step[2](element, ancestors):
                                continue
                        if element not in found:
                            found.append(element)
                current = found
            elif kind == "filter":
                _, has_text, has = step
                kept = []
                for element in current:
                    if has_text is not None and not (has_text.search(element.text()) if isinstance(has_text, re.Pattern) else str(has_text).lower() in element.text().lower()):
                        continue
                    if has is not None and not has.resolve([element]):
                        continue
                    kept.append(element)
                current = kept
            elif kind == "nth":
                current = current[step[1]:step[1] + 1]
        return current

    def count(self) -> int:
        return len(self.resolve())

    def all(self) -> List["Locator"]:
        return [self.nth(i) for i in range(self.count())]

    def one(self) -> El:
        found = self.resolve()
        if not found:
            raise FakeTimeout("Timeout 30000ms exceeded waiting for %s" % self.describe())
        if len(found) > 1:
            raise FakeError("strict mode violation: %s resolved to %d elements" % (self.describe(), len(found)))
        return found[0]

    def describe(self) -> str:
        return " >> ".join("%s(%s)" % (s[0], ", ".join(repr(x) for x in s[1:3] if not callable(x))) for s in self.steps)

    # -- reading ---------------------------------------------------------------------------------------------------
    def inner_text(self) -> str:
        return self.one().text()

    def all_inner_texts(self) -> List[str]:
        return [e.text() for e in self.resolve()]

    def input_value(self) -> str:
        element = self.one()
        if element.tag not in ("input", "select", "textarea"):
            raise FakeError("Error: Node is not an <input>, <textarea> or <select> element")
        return element.value or ""

    def get_attribute(self, name: str) -> Optional[str]:
        value = self.one().attrs.get(name)
        return None if value is None else str(value)

    def is_enabled(self) -> bool:
        return not self.one().disabled

    def is_checked(self) -> bool:
        return bool(self.one().checked)

    def is_visible(self) -> bool:
        return self.count() > 0

    def wait_for(self, state: str = "visible", timeout: Optional[int] = None) -> None:
        if state == "visible" and not self.resolve():
            raise FakeTimeout("Timeout %sms exceeded waiting for %s to be visible" % (timeout, self.describe()))

    # -- acting ----------------------------------------------------------------------------------------------------
    def click(self) -> None:
        element = self.one()
        if element.disabled:
            raise FakeTimeout("Timeout 30000ms exceeded: element is not enabled — %s" % self.describe())
        if element.on_click is None:
            raise FakeError("the double's %s %r does nothing when pressed" % (element.tag, element.name))
        self.page.act(element.on_click)

    def fill(self, text: str) -> None:
        element = self.one()
        if element.on_fill is None or element.disabled or element.attrs.get("readonly"):
            raise FakeError("Error: Element is not an editable <input>: %s" % self.describe())
        self.page.act(lambda: element.on_fill(text))

    def check(self) -> None:
        element = self.one()
        if element.on_check is None or element.disabled:
            raise FakeError("Error: Not a checkbox or radio button, or disabled: %s" % self.describe())
        self.page.act(lambda: element.on_check(True))

    def uncheck(self) -> None:
        element = self.one()
        if element.on_check is None or element.kind == "radio":
            raise FakeError("Error: Cannot uncheck a radio button: %s" % self.describe())
        self.page.act(lambda: element.on_check(False))

    def select_option(self, label: Optional[str] = None, value: Optional[str] = None) -> List[str]:
        element = self.one()
        if element.tag != "select" or element.on_select is None:
            raise FakeError("Error: Element is not a <select> element: %s" % self.describe())
        options = [o for o in element.walk() if o.tag == "option"]
        chosen = next((o for o in options if (label is not None and o.text() == label) or (value is not None and o.attrs.get("value") == value)), None)
        if chosen is None:
            raise FakeTimeout("Timeout 30000ms exceeded waiting for option %r in %s" % (label or value, self.describe()))
        self.page.act(lambda: element.on_select(str(chosen.attrs.get("value", chosen.text()))))
        return [str(chosen.attrs.get("value", chosen.text()))]


def descendants_with_ancestors(root: El) -> Iterator[Tuple[El, List[El]]]:
    def walk(node: El, ancestors: List[El]) -> Iterator[Tuple[El, List[El]]]:
        for c in node.children:
            if isinstance(c, El):
                yield c, ancestors + [node]
                yield from walk(c, ancestors + [node])
    yield from walk(root, [])


# ======================================================================================================================
# The network a page makes: the estate double as its server, every answer told to the page's listeners.
# ======================================================================================================================
class FakeRequest:
    def __init__(self, method: str, url: str, post_data: Optional[str]):
        self.method = method
        self.url = url
        self.post_data = post_data


class FakeResponse:
    def __init__(self, request: FakeRequest, status: int, text: str):
        self.request = request
        self.url = request.url
        self.status = status
        self._text = text

    def text(self) -> str:
        return self._text


class _CookieResponse:
    def __init__(self, headers: Sequence[Tuple[str, str]]):
        self._headers = list(headers)

    def info(self) -> "_CookieResponse":
        return self

    def get_all(self, name: str, default: Any = None) -> Any:
        found = [v for k, v in self._headers if k.lower() == name.lower()]
        return found if found else default


class ApiError(Exception):
    """web/lib/api.ts ApiError: the estate's refusal body, its status, and whether the estate (not a proxy) answered."""

    def __init__(self, refusal: Dict[str, Any], status: int, from_server: bool = True):
        super().__init__(refusal.get("message"))
        self.refusal = refusal
        self.status = status
        self.from_server = from_server


# ======================================================================================================================
# The virtual authenticator and the CDP session that drives it.
# ======================================================================================================================
def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def unb64(text: str) -> bytes:
    return base64.b64decode(text + "=" * (-len(text) % 4))


def pkcs8_der_of(pem: str, openssl: str = PK.OPENSSL) -> bytes:
    """The key as the DevTools protocol carries a credential's privateKey: PKCS#8, DER (openssl pkcs8 -topk8 -nocrypt)."""
    done = subprocess.run([openssl, "pkcs8", "-topk8", "-nocrypt", "-outform", "DER"], input=pem.encode("ascii"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return done.stdout


def pem_of_pkcs8(der: bytes, openssl: str = PK.OPENSSL) -> str:
    done = subprocess.run([openssl, "pkey", "-inform", "DER", "-outform", "PEM"], input=der, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return done.stdout.decode("ascii")


class FakeAuthenticator:
    """One CDP virtual authenticator: its options, and the credentials it holds (each a software passkey, keyed by openssl)."""

    def __init__(self, authenticator_id: str, options: Dict[str, Any]):
        self.id = authenticator_id
        self.options = dict(options)
        self.passkeys: List[PK.SoftwarePasskey] = []

    def create(self, options: Dict[str, Any], origin: str) -> Dict[str, Any]:
        selection = options.get("authenticatorSelection") or {}
        if selection.get("residentKey") == "required" and not self.options.get("hasResidentKey"):
            raise NotAllowed("the authenticator cannot hold a discoverable credential")
        if selection.get("userVerification") == "required" and not (self.options.get("hasUserVerification") and self.options.get("isUserVerified")):
            raise NotAllowed("the authenticator cannot verify the user")
        excluded = {c.get("id") for c in options.get("excludeCredentials") or []}
        if any(p.credential_id_b64 in excluded for p in self.passkeys):
            raise NotAllowed("an excluded credential is held")
        passkey = PK.SoftwarePasskey.create_for(options, origin)
        registration = passkey.registration(options, origin)
        self.passkeys.append(passkey)
        return registration

    def get(self, challenge: str, rp_id: str, origin: str, allow: Sequence[str], user_verification: str) -> Dict[str, Any]:
        if user_verification == "required" and not (self.options.get("hasUserVerification") and self.options.get("isUserVerified")):
            raise NotAllowed("the authenticator cannot verify the user")
        candidates = [p for p in self.passkeys if p.rp_id == rp_id and (not allow or p.credential_id_b64 in allow)]
        if not candidates:
            raise NotAllowed("no credential for %s" % rp_id)
        return candidates[0].assertion(challenge, rp_id=rp_id, origin=origin)

    def export(self) -> List[Dict[str, Any]]:
        return [{"credentialId": b64(p.credential_id), "isResidentCredential": True, "rpId": p.rp_id, "privateKey": b64(pkcs8_der_of(p.key.pem)),
                 "userHandle": b64(p.user_id), "signCount": p.sign_count, "largeBlob": "", "backupEligibility": False, "backupState": False} for p in self.passkeys]

    def import_(self, credential: Dict[str, Any], origin: str) -> None:
        for field in ("credentialId", "rpId", "privateKey", "signCount"):
            if field not in credential:
                raise FakeError("WebAuthn.addCredential: the credential carries no %s" % field)
        key = PK.OpensslKey(pem_of_pkcs8(unb64(str(credential["privateKey"]))))
        self.passkeys.append(PK.SoftwarePasskey(key, unb64(str(credential["credentialId"])), str(credential["rpId"]), origin,
                                                unb64(str(credential.get("userHandle") or "")), sign_count=int(credential["signCount"])))


class FakeCDP:
    """`context.new_cdp_session(page)`: the WebAuthn domain, as far as the harness speaks it, and nothing else."""

    def __init__(self, page: "Page"):
        self.page = page
        self.enabled = False
        self.sent: List[Tuple[str, Dict[str, Any]]] = []

    def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        self.sent.append((method, params))
        if method == "WebAuthn.enable":
            self.enabled = True
            return {}
        if not self.enabled:
            raise FakeError("Protocol error (%s): The Virtual Authenticator Environment has not been enabled for this session" % method)
        if method == "WebAuthn.addVirtualAuthenticator":
            options = params.get("options") or {}
            if options.get("protocol") not in ("ctap2", "u2f"):
                raise FakeError("Protocol error (WebAuthn.addVirtualAuthenticator): Invalid protocol")
            authenticator = FakeAuthenticator(str(uuid.uuid4()), options)
            self.page.authenticators.append(authenticator)
            return {"authenticatorId": authenticator.id}
        authenticator = next((a for a in self.page.authenticators if a.id == params.get("authenticatorId")), None)
        if authenticator is None:
            raise FakeError("Protocol error (%s): Could not find a Virtual Authenticator matching the ID" % method)
        if method == "WebAuthn.addCredential":
            authenticator.import_(params.get("credential") or {}, self.page.world.estate.origin)
            return {}
        if method == "WebAuthn.getCredentials":
            return {"credentials": authenticator.export()}
        raise FakeError("Protocol error (%s): the screens' double does not speak this method" % method)

    def detach(self) -> None:
        pass


# ======================================================================================================================
# The browser: contexts, pages, and the request road a context reads the store on.
# ======================================================================================================================
SCREENSHOT_BYTES = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                    b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")


class FakeAPIResponse:
    def __init__(self, status: int, text: str):
        self.status = status
        self._text = text

    def text(self) -> str:
        return self._text


class FakeAPIRequestContext:
    """`context.request`: requests made with the context's own cookies and nothing else (no CSRF token, no page)."""

    def __init__(self, context: "Context"):
        self.context = context

    def get(self, url: str, timeout: Optional[int] = None) -> FakeAPIResponse:
        status, _, text = self.context.send("GET", url, None, csrf=None)
        return FakeAPIResponse(status, text)


class Context:
    def __init__(self, browser: "Browser", **options: Any):
        self.browser = browser
        self.world = browser.world
        self.options = options
        self.jar = http.cookiejar.CookieJar()
        self.pages: List["Page"] = []
        self.closed = False
        self.request = FakeAPIRequestContext(self)

    def new_page(self) -> "Page":
        page = Page(self)
        self.pages.append(page)
        return page

    def new_cdp_session(self, page: "Page") -> FakeCDP:
        return FakeCDP(page)

    def close(self) -> None:
        self.closed = True

    def send(self, method: str, url: str, body: Any, csrf: Optional[str]) -> Tuple[int, List[Tuple[str, str]], str]:
        """One request through the estate double, as a browser sends it: the context's cookies, JSON, the page's CSRF token on a mutating call."""
        if self.closed:
            raise FakeError("Target page, context or browser has been closed")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if csrf and method != "GET":
            headers["x-csrf-token"] = csrf
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        self.jar.add_cookie_header(request)
        status, answer_headers, text = self.world.estate(request)
        self.jar.extract_cookies(_CookieResponse(answer_headers), request)
        return status, answer_headers, text


class Browser:
    def __init__(self, world: "World", headless: bool):
        self.world = world
        self.headless = headless
        self.contexts: List[Context] = []

    def new_context(self, **options: Any) -> Context:
        context = Context(self, **options)
        self.contexts.append(context)
        return context

    def close(self) -> None:
        for c in self.contexts:
            c.close()


class Chromium:
    def __init__(self, world: "World"):
        self.world = world

    def launch(self, headless: bool = True, **_: Any) -> Browser:
        browser = Browser(self.world, headless)
        self.world.browsers.append(browser)
        return browser


class Playwright:
    def __init__(self, world: "World"):
        self.chromium = Chromium(world)
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class _Expecting:
    def __init__(self, page: "Page", predicate: Callable[[FakeResponse], bool]):
        self.page = page
        self.predicate = predicate
        self.start = len(page.responses)
        self.value: Optional[FakeResponse] = None


class Page:
    """One tab: its address, the app it runs (the screens), the authenticators attached to it, and every answer it has received."""

    def __init__(self, context: Context):
        self.context = context
        self.world = context.world
        self.url = "about:blank"
        self.listeners: List[Callable[[FakeResponse], None]] = []
        self.responses: List[FakeResponse] = []
        self.authenticators: List[FakeAuthenticator] = []
        self.app: Any = None
        self.default_timeout: Optional[int] = None
        self.screenshots: List[str] = []

    # -- Playwright's page surface ---------------------------------------------------------------------------------------
    def on(self, event: str, handler: Callable[[FakeResponse], None]) -> None:
        if event != "response":
            raise FakeError("the screens' double tells a page's listeners of answers only")
        self.listeners.append(handler)

    def set_default_timeout(self, ms: int) -> None:
        self.default_timeout = ms

    def goto(self, url: str, wait_until: str = "load", timeout: Optional[int] = None) -> None:
        parsed = urllib.parse.urlparse(url)
        if "%s://%s" % (parsed.scheme, parsed.netloc) != self.world.estate.origin:
            raise FakeError("net::ERR_NAME_NOT_RESOLVED at %s (the double serves %s alone)" % (url, self.world.estate.origin))
        self.url = url
        from tests.real_world_screens import App  # the screens, beside this file
        self.app = App(self, parsed.path or "/", parsed.query, parsed.fragment)
        self.app.mount()

    def wait_for_load_state(self, state: str = "load", timeout: Optional[int] = None) -> None:
        return None

    def wait_for_timeout(self, ms: float) -> None:
        """Nothing renders later in the double — every press runs its fetches and renders before it returns — so a pause passes no time."""
        return None

    @contextlib.contextmanager
    def expect_response(self, predicate: Callable[[FakeResponse], bool], timeout: Optional[int] = None) -> Iterator[_Expecting]:
        waiting = _Expecting(self, predicate)
        yield waiting
        waiting.value = next((r for r in self.responses[waiting.start:] if predicate(r)), None)
        if waiting.value is None:
            raise FakeTimeout("Timeout %sms exceeded while waiting for event \"response\"" % timeout)

    def screenshot(self, path: str, full_page: bool = False) -> bytes:
        with open(path, "wb") as handle:
            handle.write(SCREENSHOT_BYTES)
        self.screenshots.append(path)
        return SCREENSHOT_BYTES

    def get_by_role(self, role: str, name: Any = None, exact: bool = False, level: Optional[int] = None) -> Locator:
        return Locator(self, [("role", role, name, exact, level)])

    def get_by_label(self, text: Any, exact: bool = False) -> Locator:
        return Locator(self, [("label", text, exact)])

    def locator(self, selector: str) -> Locator:
        return Locator(self, [("css", selector, css_predicate(selector))])

    # -- what the app does on this page --------------------------------------------------------------------------------
    def render(self) -> El:
        return self.app.render() if self.app is not None else El("html")

    def act(self, handler: Callable[[], None]) -> None:
        handler()

    def fetch(self, method: str, path: str, body: Any = None) -> Any:
        """web/lib/api.ts: JSON in and out under the session's cookie; the CSRF token on a mutating call; a refusal raised as ApiError."""
        url = self.world.estate.origin + path
        csrf = self.app.csrf if self.app is not None else None
        status, _, text = self.context.send(method, url, body, csrf)
        request = FakeRequest(method, url, json.dumps(body) if body is not None else None)
        response = FakeResponse(request, status, text)
        self.responses.append(response)
        for listener in list(self.listeners):
            listener(response)
        try:
            parsed = json.loads(text) if text.strip() else None
        except ValueError:
            raise ApiError({"code": "INTERNAL_ERROR", "message": "Something went wrong. Nothing was changed."}, status, from_server=False)
        if not (200 <= status < 300):
            refusal = parsed.get("error") if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict) else {
                "code": "INTERNAL_ERROR", "message": "Something went wrong. Nothing was changed."}
            raise ApiError(refusal, status, from_server=isinstance(parsed, dict))
        return parsed

    def credentials_create(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """navigator.credentials.create, answered by the first authenticator attached to this page — or NotAllowedError where none is."""
        if not self.authenticators:
            raise NotAllowed("no authenticator is attached to this page")
        return self.authenticators[0].create(options, self.world.estate.origin)

    def credentials_get(self, challenge: str, allow: Sequence[str] = (), user_verification: str = "required") -> Dict[str, Any]:
        if not self.authenticators:
            raise NotAllowed("no authenticator is attached to this page")
        return self.authenticators[0].get(challenge, self.world.estate.rp_id, self.world.estate.origin, list(allow), user_verification)

    def navigate(self, path: str) -> None:
        """A route change inside the app (react-router's navigate): the app keeps its session and mounts the new screen."""
        self.url = self.world.estate.origin + path
        self.app.navigate(path)


# ======================================================================================================================
# The world the tests build: the estate double (its platform, its chain), and the browsers opened on it.
# ======================================================================================================================
class World:
    def __init__(self, estate: "ScreensEstate"):
        self.estate = estate
        self.browsers: List[Browser] = []

    def driver(self) -> R.Driver:
        return R.Driver(lambda: Playwright(self), FakeTimeout, FakeError)

    def pages(self) -> List[Page]:
        return [p for b in self.browsers for c in b.contexts for p in c.pages]


# ======================================================================================================================
# The estate as the live screens meet it (aeredium/AERAccounts b523cbf): the API leg's double, with what the screens use.
# ======================================================================================================================
ESTATE_ENTRY = "aer-accounts"           # services/provisioning.ts: the entry the estate births on every account
PLAN_SENTENCE = "This estate's account stands on group-100, the one signing group."
# The list questions' own fields, as the catalog serves them (server/services/questioncatalog.ts at b523cbf: A8 at 920-924, C11C at 1118, C18 at 1187)
# and the wizard renders them, "{label} (entry n)": the API leg posts the entries as JSON and never needed them, so its double serves none.
LIST_FIELDS = {
    "A8": [{"key": "name", "label": "Full name"}, {"key": "email", "label": "Work email"},
           {"key": "role", "label": "What they primarily do", "kind": "choice", "options": list(A.FINANCE_ROLES)}],
    "C11C": [{"key": "name", "label": "Full name"}, {"key": "email", "label": "Work email"}],
    "C18": [{"key": "name", "label": "Full name"}, {"key": "email", "label": "Work email"}],
}


class ScreensPlatform(D.PlatformDouble):
    """
    The access platform, with the one read road the browser leg uses beside the admin credit road: GET /v1/admin/accounts/{id}/policies under the
    admin key (internal/api/router.go AdminListPolicyEntries) — each signing entry with its two legacy limits, in whole dollars, zero until written.
    """

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.entries: Dict[str, List[Dict[str, Any]]] = {}

    def __call__(self, request: urllib.request.Request) -> Tuple[int, List[Tuple[str, str]], str]:
        url = urllib.parse.urlparse(request.full_url)
        m = re.match(r"^/v1/admin/accounts/([^/]+)/policies$", url.path)
        if m and request.get_method() == "GET":
            headers = {k.lower(): v for k, v in request.header_items()}
            self.requests.append({"method": "GET", "path": url.path, "headers": headers, "body": ""})
            if self.down:
                raise D.H.Unreachable("GET %s could not be reached: [Errno 61] Connection refused" % request.full_url)
            bearer = headers.get("authorization", "")[len("Bearer "):].strip() if headers.get("authorization", "").startswith("Bearer ") else ""
            if not bearer:
                return self._json(401, {"error": D.PLATFORM_ADMIN_MISSING})
            if bearer != self.admin_key:
                return self._json(401, {"error": D.PLATFORM_ADMIN_INVALID})
            if m.group(1) not in self.accounts:
                return self._json(404, {"error": D.PLATFORM_ACCOUNT_NOT_FOUND})
            return self._json(200, {"policy_entries": [dict(e) for e in self.entries.get(m.group(1), [])]})
        return super().__call__(request)


class ScreensEstate(D.EstateDouble):
    """
    The estate the browser leg walks: born by the CLI road (its founder's invitation minted with or without --email; its signing entries at zero),
    with the roads the screens call and the API leg never did — the new-wallet press (Spec 107b), the wallet register, the plan's signing group,
    the Approver inbox, a run's Cancel — and the live rules since Specs AER360-SEAT-CASE (roster seats folded), AER360-RUN-ROAD (a run executes
    the moment its approvals land, from the wallet it names) and AER360-115 (the Policy Interview's write puts C2 and C3 onto the estate's own
    entries where they stand at zero, and says so on its receipt).
    """

    def __init__(self, founder_name: str = "Harriet Founder", new_wallet_usdc_cents: int = 200, assigned_groups: Sequence[str] = ("group-100",),
                 **kw: Any):
        kw.setdefault("treasury", False)
        kw.setdefault("funding_wallet", "press")
        kw.setdefault("account_email", T.REAL_WORLD_BIRTH_EMAIL)
        kw.setdefault("platform", ScreensPlatform())
        super().__init__(**kw)
        self.founder_name = founder_name
        self.authorship_entry["name"] = "%s (author)" % founder_name   # group100_invite.sh: f"{first} (author)"
        self.credentials[self.founder_credential]["name"] = self.authorship_entry["name"]
        self.new_wallet_usdc_cents = new_wallet_usdc_cents            # what the owner funds a new wallet with before R7 (Spec HRW-1: funding is the owner's act)
        self.assigned_groups = list(assigned_groups)
        self.pressed_wallets: Dict[str, Dict[str, Any]] = {}
        self.wallet_challenges: Dict[str, Dict[str, Any]] = {}
        self.platform.entries[self.aap_account_id] = [
            {"id": "pe-" + secrets.token_hex(4), "name": ESTATE_ENTRY, "access_type": "sign+audit", "active": True, "superseded_by": "",
             "max_amount_per_tx_usd": 0, "max_amount_per_day_usd": 0},
            {"id": self.authorship_entry["id"], "name": self.authorship_entry["name"], "access_type": "sign+audit", "active": True, "superseded_by": "",
             "max_amount_per_tx_usd": 0, "max_amount_per_day_usd": 0},
        ]

    # -- the birth script's road (group100_invite.sh, invite.mjs --email) --------------------------------------------------------------
    def mint_founder_link(self, display_name: str = "Harriet Founder", email: Optional[str] = T.REAL_WORLD_BIRTH_EMAIL) -> str:
        link = super().mint_founder_link(display_name)
        token = link.split("#", 1)[1]
        self.invites[hashlib.sha256(token.encode()).hexdigest()]["email"] = email  # --email recorded on the row, or None as invite.mjs leaves it without
        return link

    def birth_printout(self, link: str, email: Optional[str] = T.REAL_WORLD_BIRTH_EMAIL) -> str:
        """What group100_invite.sh prints (the account id, the founder's credential, invite.mjs's lines), with invite.mjs's one line where --email was not given."""
        lines = ["— fresh account: %s —" % self.workspace["name"], "account id: %s" % self.aap_account_id, "— birth and provision the estate —",
                 "estate born and provisioned", "— the founder's author credential —", "founder credential: %s" % self.founder_credential,
                 "— the one-time enrolment link (72 hours) — send this to %s —" % (email or T.REAL_WORLD_BIRTH_EMAIL)]
        if not email:
            lines.append("no --email given: this founder's presses will carry no name until one is recorded")
        lines += ["", "Invite for %s (%s)" % (self.workspace["name"], self.founder_name), "Enrols:   credential %s" % self.founder_credential]
        if email:
            lines.append("Email:    %s" % email)
        lines += ["Expires:  %s" % self._iso(time.time() + 72 * 3600), "", "Send this link. The invitee clicks it, uses Touch ID, and is in —",
                  "no account key, no credential id, nothing to type:", "", "  %s" % link, ""]
        return "\n".join(lines)

    def record_founder_emails(self, email: str = T.REAL_WORLD_BIRTH_EMAIL) -> None:
        """dist-deploy/record-founder-emails.mjs (Spec AER360-SEAT-CASE §3.3): the redeemed founder row with a blank email gets the account's."""
        for row in self.invites.values():
            if row["credentialId"] == self.founder_credential and row["redeemedAt"] and not row.get("email"):
                row["email"] = email
                for passkey in self.passkeys.values():
                    if passkey["credentialId"] == self.founder_credential:
                        passkey["email"] = email
        for session in self.sessions.values():
            if session["credentialId"] == self.founder_credential:
                session["email"] = email

    # -- the roster, written folded (Spec AER360-SEAT-CASE §3.1) ------------------------------------------------------------------------
    def seat_whitelist_roster(self, charter: Dict[str, Any], latest: Dict[str, Dict[str, Any]]) -> None:
        super().seat_whitelist_roster(charter, latest)
        for seat in self.whitelist_seats:
            seat["user_id"] = seat["user_id"].strip().lower()

    def seat_change_roster(self, charter: Dict[str, Any], latest: Dict[str, Dict[str, Any]]) -> None:
        super().seat_change_roster(charter, latest)
        for seat in self.change_seats:
            seat["user_id"] = seat["user_id"].strip().lower()

    # -- the write puts the charter's ceilings onto the estate's own entries (Spec AER360-115) ----------------------------------------------
    def write_interview(self, caller: Dict[str, Any], iv: Dict[str, Any], road: str, pending_tx_id: Optional[str] = None) -> Tuple[int, Any]:
        status, answer = super().write_interview(caller, iv, road, pending_tx_id)
        if status == 200 and iv["interviewType"] == "policy":
            latest = {qid: row["value"] for qid, row in self.latest(iv["id"]).items()}
            cents = lambda qid: str((latest.get(qid) or {}).get("cents") or "")  # noqa: E731
            if cents("C2").isdigit() and cents("C3").isdigit() and int(cents("C2")) > 0 and int(cents("C3")) > 0:
                tx, day = -(-int(cents("C2")) // 100), -(-int(cents("C3")) // 100)
                written = []
                for entry in self.platform.entries.get(self.aap_account_id, []):
                    if not entry.get("active", True) or entry.get("superseded_by"):
                        continue  # isSigningEntryInForce (charterceilings.ts): a superseded or inactive version is listed, never written
                    if entry["name"] == ESTATE_ENTRY or entry["name"].endswith(" (author)"):
                        touched = False
                        if not entry["max_amount_per_tx_usd"]:
                            entry["max_amount_per_tx_usd"], touched = tx, True
                        if not entry["max_amount_per_day_usd"]:
                            entry["max_amount_per_day_usd"], touched = day, True
                        if touched:
                            written.append({"id": entry["id"], "name": entry["name"]})
                answer["receipt"]["ceilings"] = {"perPaymentUsd": tx, "perDayUsd": day, "entries": written, "unwritten": [], "at": self._now_iso()}
        return status, answer

    # -- a list question's fields, as the catalog serves them (LIST_FIELDS) ------------------------------------------------------------------
    def page(self, iv: Dict[str, Any], serve_truth: bool) -> Dict[str, Any]:
        page = super().page(iv, serve_truth)
        question = page.get("question")
        if isinstance(question, dict) and not question.get("listFields") and question.get("questionId") in LIST_FIELDS:
            question["listFields"] = [dict(f) for f in LIST_FIELDS[question["questionId"]]]
        return page

    # -- the roads the screens use ----------------------------------------------------------------------------------------------------
    def dispatch(self, method: str, path: str, headers: Dict[str, str], body: Any, set_cookie: List[Tuple[str, str]]) -> Tuple[int, Any]:
        route = "%s %s" % (method, path)
        if route == "GET /v1/visibility":
            self.require_session(headers)
            return 200, {"standing": {"level": 1, "kind": "root"}}
        if route in ("GET /v1/counterparties", "GET /v1/deposits"):
            self.require_caller(headers, "viewer")
            return 200, {route.rsplit("/", 1)[1]: []}
        if route == "GET /v1/aer360/wallets":
            self.require_caller(headers, "viewer")
            return 200, {"answer": None, "absence": D.WALLETS_ABSENCE, "display": {"currency": "AUD", "rateE8": "150000000"}, "register": self.register()}
        if route == "GET /v1/aer360/plan":
            self.require_caller(headers, "viewer")
            return 200, {"plan": "starter", "maxTokens": 10, "activeCredentials": len(self.credentials), "readAt": self._now_iso(), "absence": None,
                         "signingGroup": {"accountId": self.aap_account_id, "assigned": list(self.assigned_groups),
                                          "standing": "on_the_one_group" if self.assigned_groups == ["group-100"] else "elsewhere",
                                          "sentence": PLAN_SENTENCE if self.assigned_groups == ["group-100"] else
                                          "This estate's account stands on %s, not on group-100 alone." % ", ".join(self.assigned_groups)}}
        if route == "POST /v1/workspace/wallets/options":
            return self.wallet_options(headers, body)
        if route == "POST /v1/workspace/wallets":
            return self.wallet_press(headers, body)
        if route == "GET /v1/approvals/inbox":
            return self.inbox(headers)
        m = re.match(r"^/v1/sets/([^/]+)/cancel$", path)
        if m and method == "POST":
            return self.cancel_set(headers, m.group(1))
        m = re.match(r"^/v1/invites/([^/]+)/revoke$", path)
        if m and method == "POST":
            return self.revoke_invite(headers, m.group(1))
        return super().dispatch(method, path, headers, body, set_cookie)

    def register(self) -> Dict[str, Any]:
        rows = []
        if self.has_funding_wallet():
            rows.append({"walletId": "wallet-funding", "walletNumber": "1", "name": "Funding wallet", "address": self.source_account, "funding": True,
                         "chains": [T.PAYEE_CHAIN], "fundSentence": "Fund this account with USDC on %s. Gas is bought separately, below." % T.PAYEE_CHAIN,
                         "level": 1, "beneficiary": None, "clientSeat": None, "clientInvitation": None, "keyed": False})
        rows += [dict(w) for w in self.pressed_wallets.values()]
        return {"walletCount": len(rows), "wallets": rows,
                "levels": [{"level": 1, "name": "Level 1 — head office", "count": len(rows), "heldBaseMinor": None, "balancesSaid": None, "route": None}]}

    def wallet_options(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        if (body or {}).get("whose") != "estate":
            raise D.Malformed("whose: the double presses this estate's own wallets only")
        if not self.has_funding_wallet():
            raise D.Refusal("WORKSPACE_NOT_PROVISIONED", D.NO_FUNDING_WALLET_SENTENCE, {"cause": D.NO_FUNDING_WALLET_REASON}, provenance={"source": "workspace"})
        wallet_id = "wallet-" + secrets.token_hex(6)
        issued = int(time.time() * 1000)
        challenge = self.challenge("workspace.wallet", "wallet:%s:%s|%s" % (wallet_id, issued, caller["credentialId"]), issued)
        self.wallet_challenges[wallet_id] = {"challenge": challenge, "issuedAtMs": issued, "credentialId": caller["credentialId"]}
        own = [w for w, row in self.passkeys.items() if row["credentialId"] == caller["credentialId"]]
        return 200, {"options": {"challenge": challenge, "rpId": self.rp_id, "timeout": 60000, "userVerification": "required",
                                 "allowCredentials": [{"id": w, "type": "public-key", "transports": ["internal"]} for w in own]}, "issuedAtMs": issued, "walletId": wallet_id}

    def wallet_press(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        body = body or {}
        pending = self.wallet_challenges.pop(str(body.get("walletId")), None)
        if pending is None or pending["credentialId"] != caller["credentialId"] or body.get("issuedAtMs") != pending["issuedAtMs"]:
            raise D.Refusal("STEP_UP_INVALID", detail={"cause": "no press of this wallet was opened by this credential"})
        response = body.get("response") or {}
        stored = self.passkeys.get(str(response.get("id")))
        if not stored or stored["credentialId"] != caller["credentialId"]:
            raise D.Refusal("STEP_UP_INVALID", detail={"cause": "the asserting passkey is not the pressing credential"})
        try:
            stored["signCount"] = PK.verify_assertion(response, pending["challenge"], self.origin, self.rp_id, stored["publicKey"], stored["signCount"])
        except PK.PasskeyRefused as err:
            raise D.Refusal("STEP_UP_INVALID", detail={"cause": str(err)[:200]})
        number = str(2 + len(self.pressed_wallets))
        address = T.derive_address("the screens' double's pressed wallet %s/%s" % (number, self.workspace["name"]))
        wallet = {"walletId": body["walletId"], "walletNumber": number, "name": "Wallet %s" % number, "address": address, "funding": False, "chains": [T.PAYEE_CHAIN],
                  "fundSentence": "Fund this account with USDC on %s. Gas is bought separately, below." % T.PAYEE_CHAIN, "level": 1, "beneficiary": None,
                  "clientSeat": None, "clientInvitation": None, "keyed": True}
        self.pressed_wallets[wallet["walletId"]] = wallet
        if self.new_wallet_usdc_cents:
            self.chain.credit(address, T.usdc_minor_of_cents(self.new_wallet_usdc_cents))  # the owner funds the wallet (the harness never does)
        self.append_trail("wallet.registered", caller["credentialId"], {"walletId": wallet["walletId"], "address": address, "via": "press"})
        return 200, {"born": True, "wallet": {k: wallet[k] for k in ("walletId", "walletNumber", "name", "address", "level", "beneficiary")}, "invitation": None}

    # -- a run leaves the wallet it names (Spec 110a), and executes when its approvals land (Spec AER360-RUN-ROAD §3.3) ---------------------
    def review_or_create(self, headers: Dict[str, str], body: Any, create: bool) -> Tuple[int, Any]:
        body = dict(body or {})
        wallet_id = body.pop("walletId", None)
        wallet = None
        if wallet_id:
            wallet = self.pressed_wallets.get(str(wallet_id))
            if wallet is None or not wallet["keyed"]:
                raise D.Refusal("WALLET_NOT_FOUND", "No wallet of this estate's goes by that id.", {"walletId": str(wallet_id)}, provenance={"source": "wallets"})
        funding = self.source_account
        if wallet is not None:
            self.source_account = wallet["address"]
        try:
            status, answer = super().review_or_create(headers, body, create)
        finally:
            self.source_account = funding
        view = {k: wallet[k] for k in ("walletId", "walletNumber", "name", "level", "beneficiary", "address")} if wallet else None
        if create and isinstance(answer, dict) and isinstance(answer.get("set"), dict):
            row = self.sets[answer["set"]["id"]]
            if wallet is not None and not answer.get("alreadyExisted"):
                row["sourceAccount"] = wallet["address"]
                answer["set"]["sourceAccount"] = wallet["address"]
            answer["wallet"] = view
        elif isinstance(answer, dict):
            answer["wallet"] = view
        return status, answer

    def execute_on_approval(self, row: Dict[str, Any]) -> None:
        """Spec AER360-RUN-ROAD §3.3: the moment a run is approved the estate executes it under its author's credential, from the wallet it names."""
        author = {"credentialId": row["authorCredentialId"], "roles": self.roles_of(row["authorCredentialId"])}
        row["status"] = "executing"
        row["executedAt"] = self._now_iso()
        self.append_trail("set.execution_started", row["authorCredentialId"], {"setDigest": row["setDigest"], "road": "gas_roads", "account": row["sourceAccount"]},
                          subject_id=row["id"])
        funding = self.source_account
        self.source_account = row["sourceAccount"]
        try:
            self.drive_and_settle(author, row)
        finally:
            self.source_account = funding

    def submit_set(self, headers: Dict[str, str], set_id: str) -> Tuple[int, Any]:
        status, answer = super().submit_set(headers, set_id)
        if answer.get("status") == "approved":
            self.execute_on_approval(self.sets[set_id])
        return status, answer

    def approval(self, headers: Dict[str, str], set_id: str, action: str, body: Any) -> Tuple[int, Any]:
        status, answer = super().approval(headers, set_id, action, body)
        if action == "approve" and answer.get("status") == "approved":
            self.execute_on_approval(self.sets[set_id])
            answer["executionStarted"] = True
        return status, answer

    def cancel_set(self, headers: Dict[str, str], set_id: str) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        row = self.sets.get(set_id)
        if not row:
            raise D.Refusal("SET_NOT_EDITABLE", detail={"cause": "no such run"})
        if row["authorCredentialId"] != caller["credentialId"] or row["status"] not in ("draft", "pending_approval", "approved"):
            raise D.Refusal("SET_NOT_EDITABLE", detail={"status": row["status"]})
        row["status"] = "cancelled"
        self.append_trail("set.cancelled", caller["credentialId"], {"setDigest": row["setDigest"]}, subject_id=set_id)
        return 200, {"status": "cancelled", "approvalsRequired": row["approvalsRequired"]}

    def revoke_invite(self, headers: Dict[str, str], invite_id: str) -> Tuple[int, Any]:
        caller = self.require_caller(headers, "author", mutating=True)
        row = next((r for r in self.invites.values() if r["id"] == invite_id), None)
        if row is None:
            raise D.Refusal("INVITE_NOT_FOUND")
        if row["redeemedAt"] or row["revokedAt"]:
            raise D.Refusal("INVITE_NOT_REVOCABLE")
        row["revokedAt"] = self._now_iso()
        row["state"] = "revoked"
        row["revokedByCredentialId"] = caller["credentialId"]
        return 200, {"invite": {k: v for k, v in row.items() if not k.startswith("_")}}

    def inbox(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        """GET /v1/approvals/inbox (routes/approvals.ts): the runs waiting approval, each with whether this caller may approve it and, if not, why."""
        caller = self.require_caller(headers, "viewer")
        facts = self.charter_facts(caller)
        sets = []
        for row in sorted(self.sets.values(), key=lambda s: s["createdAt"]):
            if row["status"] != "pending_approval":
                continue
            given = [a for a in self.approvals.get(row["id"], []) if a["setDigest"] == row["setDigest"]]
            may, cause = self.may_approve(facts, row["authorCredentialId"], caller["credentialId"])
            already = any(a["credentialId"] == caller["credentialId"] for a in given)
            blocked = "You have already approved this run." if already else (None if may else "Your charter does not name you an approver of this run.")
            view = self.set_view(row, caller)
            sets.append({"id": row["id"], "reference": row["reference"], "realm": row["realm"], "status": row["status"], "authorCredentialId": row["authorCredentialId"],
                         "createdAt": row["createdAt"], "submittedAt": row["submittedAt"], "instructions": [dict(i, nowValue=i["entryValue"], drifted=False) for i in view["instructions"]],
                         "nowTotal": {"amountMinor": row["aggregateBaseMinor"], "currency": "USD", "currencyDecimals": 2}, "aggregate": view["aggregate"], "totalDrifted": False,
                         "approval": {"approvalsRequired": row["approvalsRequired"], "approvalsGiven": len(given)}, "approvalsSaid": None,
                         "mayApprove": bool(may) and not already and "approver" in caller["roles"], "blockedSentence": blocked})
        return 200, {"sets": sets, "held": [], "asClient": False}


def world(**kw: Any) -> Tuple[World, ScreensEstate]:
    estate = ScreensEstate(**kw)
    return World(estate), estate
