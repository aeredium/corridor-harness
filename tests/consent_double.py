"""
A double of the connector's auth, authorize and consent roads (Spec T21), written to the calls
`pages/consentpage.ts` makes and the routes that answer them — routes/auth.ts, routes/oauth.ts,
routes/consent.ts, services/session.ts, services/webauthn.ts, services/billing.ts's standing, http.ts's
refusal shape and statuses, packages.ts's Solo seats — and, past the consent, the MCP door the stored
token opens (routes/mcp.ts, mcprelay.ts's `my_agent`). The passkey ceremonies are verified for real
with aer360_passkey.verify_registration and verify_assertion, as @simplewebauthn/server verifies them.

It answers through corridor_harness.http_request's own signature, so a test patches that one function
and no port is bound. Every call is kept in `calls` as (method, path, status), every agent press in
`presses` and every finish in `finishes`, so a test can assert on the wire sequence as walked.

A double at least as strict as the service it stands in for: it refuses what the connector refuses, with
the connector's own code, status and sentence, and what the platform refuses through it — a fourth agent
on Solo, a destination that is not an address — in the platform's words.
"""
import base64
import hashlib
import hmac
import http.server
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_passkey as PK  # noqa: E402
import corridor_harness as H  # noqa: E402

ISSUER = "https://connector.test"
RP_ID = "connector.test"
RP_NAME = "AEREDIUM"
CHALLENGE_TTL_MS = 10 * 60 * 1000  # routes/auth.ts CHALLENGE_TTL_MS
SESSION_COOKIE = "aer_connector_session"
CSRF_HEADER = "x-aer-csrf"
SOLO_SEATS = 3
PLATFORM_PLAN = "connect-solo"

# packages/shared/src/refusals.ts, verbatim for the codes this double can answer with.
MESSAGES = {
    "NOT_AUTHENTICATED": "You are not signed in. Sign in with your passkey and try again.",
    "PASSKEY_NOT_ENROLLED": "Your browser offered a passkey this service has never registered. Sign up to enrol one; nothing was changed.",
    "PASSKEY_REJECTED": "That passkey could not be verified, so nothing was done. Try again, and if it keeps failing enrol a new one.",
    "ANSWER_INVALID": "That answer cannot be accepted. The reason is named beside it.",
    "REQUEST_MALFORMED": "That request could not be read. Nothing was changed.",
    "SUBSCRIPTION_REQUIRED": "This needs a paid subscription and none has been paid yet. Choose a plan on your account page; nothing else on this connector works until it clears.",
    "SUBSCRIPTION_LAPSED": "Your subscription has lapsed, so reading still works and acting does not. Pay it on your account page and acting returns at once.",
    "AAP_REFUSED": "The access platform refused this. Its own words are beside this.",
    "AGENT_NOT_FOUND": "There is no such agent here.",
    "ROLE_UNKNOWN": "There is no such role. The roles are MCP Police’s twelve, read from it live.",
    "AUTHORIZATION_NOT_FOUND": "There is no such connection request. Start again from Claude.",
    "AUTHORIZATION_NOT_OPEN": "This connection request is no longer open. Start again from Claude; nothing was changed.",
    "CONNECTION_NOT_FOUND": "There is no such connection here.",
    "AGENT_ALREADY_CONNECTED": "That agent already holds a connection to Claude. Hand that one over instead of granting a second.",
    "INTERNAL_ERROR": "AER Connect failed and did not expect to. Nothing was changed.",
}
# http.ts STATUS
STATUS = {
    "NOT_AUTHENTICATED": 401, "PASSKEY_NOT_ENROLLED": 401, "PASSKEY_REJECTED": 401, "REQUEST_MALFORMED": 400, "ANSWER_INVALID": 400,
    "SUBSCRIPTION_REQUIRED": 402, "SUBSCRIPTION_LAPSED": 402, "AAP_REFUSED": 502, "AGENT_NOT_FOUND": 404, "ROLE_UNKNOWN": 400,
    "AUTHORIZATION_NOT_FOUND": 404, "AUTHORIZATION_NOT_OPEN": 409, "CONNECTION_NOT_FOUND": 404, "AGENT_ALREADY_CONNECTED": 409,
    "INTERNAL_ERROR": 500,
}
# services/webauthn.ts, the connector's own counter check past the library's
CLONED_SAID = ("this passkey reported a signature counter that has already been used, which is what a cloned authenticator looks like; "
               "nobody was signed in")
RANK_VIEWS = {
    "agent": {"id": "agent", "label": "Acts as the agent", "sentence": "Claude may act as this agent within its mandate."},
    "reader": {"id": "reader", "label": "Reads only", "sentence": "Claude may read this agent's wallets and nothing else."},
}
SCOPES_FOR_RANK = {"agent": ["aeredium:act"], "reader": ["aeredium:read"]}
OFFERED_CHAINS = ("arbitrum", "base", "ethereum")
# The roles as `GET /v1/consent/:id` lists them at stage `agent`: Police's own fields passed through, `defaultRank` and the
# questionnaire's starting answers beside them (routes/consent.ts). The Trader's venues are NAMES, as the engine's template
# states them (aerkey-policy-engine templates.go) and services/roles.ts reads them with listFor('venue').
ROLES = [
    {"id": "trader.v1", "name": "Trader", "defaultRank": "agent",
     "questionnaire": {"holdAboveUsd": "10", "maxTxPerDay": "50", "chains": ["arbitrum", "base", "ethereum"], "assets": ["USDC", "USDT", "WETH"],
                       "functions": ["swap", "trade", "limit_order", "approve", "bridge"],
                       "venues": ["uniswap_v3", "pancakeswap_v3", "curve", "best_direct", "cctp", "usdt0"]}},
    {"id": "payer.v1", "name": "Payer", "defaultRank": "agent",
     "questionnaire": {"holdAboveUsd": "10", "maxTxPerDay": "20", "chains": ["arbitrum", "base", "ethereum"], "assets": ["USDC", "USDT"],
                       "functions": ["transfer", "approve", "bridge"], "venues": []}},
    {"id": "observer.v1", "name": "Observer", "defaultRank": "reader",
     "questionnaire": {"holdAboveUsd": None, "maxTxPerDay": None, "chains": ["arbitrum"], "assets": None, "functions": [], "venues": []}},
]
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DOLLARS_RE = re.compile(r"^\d+(\.\d{1,2})?$")
POLICY_HASH = "0x5237c7e1b0c4f1a9d8e3b26a5f470c91d2846ebb73f5a0c1e94d6b28fa310577"


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def now_ms():
    return int(time.time() * 1000)


class Refused(Exception):
    """A refusal, in the connector's shape: {error: {code, message, detail}} at http.ts's status."""

    def __init__(self, code, cause=None, **detail):
        super().__init__(code)
        self.code = code
        self.detail = dict(detail)
        if cause is not None:
            self.detail["cause"] = cause

    def answer(self):
        return STATUS.get(self.code, 422), {"error": {"code": self.code, "message": MESSAGES.get(self.code, self.code), "detail": self.detail}}


class ConnectorDouble:
    def __init__(self, seated=True, standing=None, issuer=ISSUER, rp_id=RP_ID, seats=SOLO_SEATS, roles=None,
                 refresh_refused=False, before_verify=None, mcp_refuses_unknown_bearer=True, register_fails=False):
        """
        `seated` True is a Solo trial standing (`paid`); False is a customer who never paid (standing `none`); `standing`
        "lapsed" is a trial whose period ended. `refresh_refused` makes /token refuse every refresh grant (invalid_grant), so a
        stored token the door refuses cannot be cured. `before_verify(counter)` is called with the assertion's counter before it
        is judged, so a test can read the passkey file at that moment. `register_fails` makes /register answer 500, the way a
        connector whose store is down would, so the Oauth road's own error is raised inside the consent.
        """
        self.issuer = issuer.rstrip("/")
        self.origin = self.issuer
        self.rp_id = rp_id
        self.secret = secrets.token_bytes(32)
        self.seats = seats
        self.roles = roles if roles is not None else [dict(r) for r in ROLES]
        self.refresh_refused = refresh_refused
        self.register_fails = register_fails
        self.before_verify = before_verify
        self.mcp_refuses_unknown_bearer = mcp_refuses_unknown_bearer
        self.default_standing = "paid" if seated else "none"
        if standing:
            self.default_standing = standing
        self.customers = {}
        self.passkeys = {}
        self.sessions = {}
        self.subscriptions = {}
        self.agents = []
        self.connections = {}
        self.clients = {}
        self.authorizations = {}
        self.codes = {}
        self.access_tokens = {}
        self.refresh_tokens = {}
        self.calls = []
        self.presses = []
        self.finishes = []
        self.registrations_verified = 0
        self.assertions_verified = 0
        self.my_agent_calls = 0
        # kept for the redaction tests: the secrets the wire carried, so a test can prove none of them is in a record whole
        self.handles = []
        self.signatures = []
        self.last_code = None

    # -- what a test plants -----------------------------------------------------
    def plant_agent(self, customer_id, name, role_id, connected=True, counterparties=(), scope="agent"):
        """An agent this customer already holds, with or without a standing connection (as the dashboard would leave one)."""
        agent = {"id": str(uuid.uuid4()), "customerId": customer_id, "name": name, "roleId": role_id, "state": "active",
                 "walletAddress": "0x" + secrets.token_hex(20), "walletChain": "arbitrum", "pactId": None,
                 "document": {"scope": {"chains": ["arbitrum", "base"], "counterparties_allowed": list(counterparties),
                                        "counterparties_whitelist_scope": scope}}}
        agent["pactId"] = "aerconn:%s" % agent["id"]
        self.agents.append(agent)
        if connected:
            self.mint_connection(agent, "agent", "mcp-planted")
        return agent

    def mint_connection(self, agent, rank, client_id):
        connection = {"id": str(uuid.uuid4()), "agentId": agent["id"], "customerId": agent["customerId"], "rank": rank,
                      "clientId": client_id, "state": "active", "credentialPrefix": "cp-" + secrets.token_hex(2)}
        self.connections[connection["id"]] = connection
        return connection

    def standing_connection(self, customer_id):
        for row in self.connections.values():
            if row["customerId"] == customer_id and row["state"] == "active":
                return row
        return None

    def connection_of(self, agent_id):
        for row in self.connections.values():
            if row["agentId"] == agent_id and row["state"] == "active":
                return row
        return None

    def customer_by_email(self, email):
        return next((c for c in self.customers.values() if c["email"] == email), None)

    # -- the challenge, stateless and bound (routes/auth.ts) --------------------
    def challenge_for(self, purpose, nonce, issued_at_ms):
        return b64url(hmac.new(self.secret, ("%s|%s|%d" % (purpose, nonce, issued_at_ms)).encode("utf-8"), hashlib.sha256).digest())

    def assert_challenge(self, purpose, nonce, issued_at_ms):
        now = now_ms()
        if not isinstance(issued_at_ms, int) or now - issued_at_ms > CHALLENGE_TTL_MS or issued_at_ms > now + 60_000:
            raise Refused("PASSKEY_REJECTED", "this ceremony timed out; start it again")
        return self.challenge_for(purpose, str(nonce), issued_at_ms)

    def authentication_options(self, purpose, nonce, issued_at_ms):
        return {"challenge": self.challenge_for(purpose, nonce, issued_at_ms), "timeout": 60000, "rpId": self.rp_id,
                "allowCredentials": [], "userVerification": "required"}

    # -- the session (services/session.ts, routes/guards.ts) --------------------
    def caller(self, headers, mutating=False):
        cookie = next((v for k, v in headers.items() if k.lower() == "cookie"), "") or ""
        sid = None
        for part in cookie.split(";"):
            name, _, value = part.strip().partition("=")
            if name == SESSION_COOKIE:
                sid = value
        if not sid:
            raise Refused("NOT_AUTHENTICATED")
        session = self.sessions.get(sid)
        if not session:
            raise Refused("NOT_AUTHENTICATED", "your session has expired; sign in again with your passkey")
        if mutating:
            header = next((v for k, v in headers.items() if k.lower() == CSRF_HEADER), None)
            if not header or header != session["csrf"]:
                raise Refused("NOT_AUTHENTICATED", "missing or incorrect CSRF token; nothing was changed")
        customer = self.customers.get(session["customerId"])
        if not customer:
            raise Refused("NOT_AUTHENTICATED", "this customer no longer exists")
        return customer, session

    def open_session(self, customer_id):
        sid = str(uuid.uuid4())
        csrf = b64url(secrets.token_bytes(32))
        self.sessions[sid] = {"customerId": customer_id, "csrf": csrf}
        secure = "; Secure" if self.origin.startswith("https://") else ""
        return csrf, "%s=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200%s" % (SESSION_COOKIE, sid, secure)

    # -- the money (services/billing.ts standingOf) -------------------------------
    def standing_of(self, customer_id):
        row = self.subscriptions.get(customer_id)
        if not row:
            return None, "none"
        if row["state"] in ("cancelled", "lapsed"):
            return row, "lapsed"
        if row["state"] not in ("active", "trialing"):
            return row, "none"
        if row.get("currentPeriodEnd") is not None and row["currentPeriodEnd"] <= time.time():
            return row, "lapsed"
        return row, "paid"

    def seat(self, customer_id, standing):
        """What the operator's seat leaves behind: a trialing Solo row; `lapsed` one whose period has ended; `none` no row."""
        if standing == "none":
            self.subscriptions.pop(customer_id, None)
            return
        self.subscriptions[customer_id] = {"plan": "monthly", "package": "solo", "state": "trialing", "priceCents": 4900,
                                           "currentPeriodEnd": time.time() + (33 * 86400 if standing == "paid" else -86400)}

    # -- the transport -------------------------------------------------------------
    def __call__(self, method, url, headers=None, body=None, timeout=None, follow_redirects=True):
        headers = dict(headers or {})
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        content_type = next((v for k, v in headers.items() if k.lower() == "content-type"), "")
        payload = None
        if body:
            if "x-www-form-urlencoded" in content_type:
                payload = {k: v[0] for k, v in urllib.parse.parse_qs(body.decode("ascii")).items()}
            else:
                try:
                    payload = json.loads(body.decode("utf-8"))
                except ValueError:
                    payload = None
        try:
            status, answer, extra = self.route(method, path, query, headers, payload, follow_redirects)
        except Refused as refused:
            status, answer = refused.answer()
            extra = {}
        self.calls.append((method, path, status))
        out_headers = {"Content-Type": "application/json"}
        out_headers.update(extra)
        text = answer if isinstance(answer, str) else json.dumps(answer)
        return H.HttpAnswer(status, out_headers, text, 1)

    def route(self, method, path, query, headers, payload, follow_redirects):
        # --- discovery and registration (routes/oauth.ts) ---
        if method == "GET" and path == "/.well-known/oauth-authorization-server":
            return 200, {"issuer": self.issuer, "authorization_endpoint": self.issuer + "/authorize", "token_endpoint": self.issuer + "/token",
                         "registration_endpoint": self.issuer + "/register", "response_types_supported": ["code"],
                         "code_challenge_methods_supported": ["S256"], "scopes_supported": ["aeredium:act", "aeredium:read"]}, {}
        if method == "GET" and path == "/.well-known/oauth-protected-resource/mcp":
            return 200, {"resource": self.issuer + "/mcp", "authorization_servers": [self.issuer]}, {}
        if method == "POST" and path == "/register":
            if self.register_fails:
                return 500, {"error": "server_error", "error_description": "Something went wrong and nothing was changed."}, {}
            client_id = "mcp-" + b64url(secrets.token_bytes(12))
            self.clients[client_id] = {"redirect_uris": list((payload or {}).get("redirect_uris") or [])}
            return 201, {"client_id": client_id, "client_id_issued_at": int(time.time()), "token_endpoint_auth_method": "none",
                         "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"],
                         "redirect_uris": self.clients[client_id]["redirect_uris"], "client_name": (payload or {}).get("client_name")}, {}
        # --- sign up and sign in (routes/auth.ts) ---
        if method == "POST" and path == "/v1/auth/signup/options":
            body = payload or {}
            for field in ("displayName", "email", "country"):
                if not isinstance(body.get(field), str) or not body[field]:
                    raise Refused("REQUEST_MALFORMED", issues="%s: Required" % field)
            if not re.match(r"^[A-Za-z]{2}$", body["country"]):
                raise Refused("REQUEST_MALFORMED", issues="country: Invalid")
            nonce = b64url(secrets.token_bytes(16))
            issued = now_ms()
            handle = secrets.token_hex(16)
            self.handles.append(handle)
            options = {"rp": {"id": self.rp_id, "name": RP_NAME}, "user": {"id": b64url(handle.encode("utf-8")), "name": RP_NAME, "displayName": body["displayName"]},
                       "challenge": self.challenge_for("signup:%s" % handle, nonce, issued),
                       "pubKeyCredParams": [{"alg": -8, "type": "public-key"}, {"alg": -7, "type": "public-key"}, {"alg": -257, "type": "public-key"}],
                       "timeout": 60000, "attestation": "none", "authenticatorSelection": {"residentKey": "required", "userVerification": "required"}}
            return 200, {"options": options, "nonce": nonce, "issuedAtMs": issued, "handle": handle}, {}
        if method == "POST" and path == "/v1/auth/signup/verify":
            body = payload or {}
            for field in ("displayName", "email", "country", "handle", "nonce", "issuedAtMs", "response"):
                if field not in body:
                    raise Refused("REQUEST_MALFORMED", issues="%s: Required" % field)
            challenge = self.assert_challenge("signup:%s" % body["handle"], body["nonce"], body["issuedAtMs"])
            try:
                credential = PK.verify_registration(body["response"], challenge, self.origin, self.rp_id)
            except PK.PasskeyRefused as err:
                raise Refused("PASSKEY_REJECTED", str(err)[:200])
            self.registrations_verified += 1
            customer = {"id": str(uuid.uuid4()), "displayName": body["displayName"], "email": body["email"], "country": body["country"].upper(),
                        "fundingAddress": None, "aapAccountId": None}
            self.customers[customer["id"]] = customer
            self.passkeys[PK.b64url_encode(credential["credential_id"])] = {"customerId": customer["id"], "publicKey": credential["public_key"], "signCount": credential["sign_count"]}
            self.seat(customer["id"], self.default_standing)
            csrf, set_cookie = self.open_session(customer["id"])
            return 200, {"customer": {"id": customer["id"], "displayName": customer["displayName"], "email": customer["email"]}, "csrfToken": csrf}, {"Set-Cookie": set_cookie}
        if method == "POST" and path == "/v1/auth/signin/options":
            nonce = b64url(secrets.token_bytes(16))
            issued = now_ms()
            return 200, {"options": self.authentication_options("signin", nonce, issued), "nonce": nonce, "issuedAtMs": issued}, {}
        if method == "POST" and path == "/v1/auth/signin/verify":
            body = payload or {}
            for field in ("nonce", "issuedAtMs", "response"):
                if field not in body:
                    raise Refused("REQUEST_MALFORMED", issues="%s: Required" % field)
            challenge = self.assert_challenge("signin", body["nonce"], body["issuedAtMs"])
            passkey = self.passkeys.get((body["response"] or {}).get("id"))
            if not passkey:
                raise Refused("PASSKEY_NOT_ENROLLED")
            self.verify_assertion(body["response"], challenge, passkey)
            customer = self.customers[passkey["customerId"]]
            csrf, set_cookie = self.open_session(customer["id"])
            return 200, {"customer": {"id": customer["id"], "displayName": customer["displayName"], "email": customer["email"]}, "csrfToken": csrf}, {"Set-Cookie": set_cookie}
        if method == "POST" and path == "/v1/auth/stepup/options":
            self.caller(headers)
            nonce = b64url(secrets.token_bytes(16))
            issued = now_ms()
            return 200, {"options": self.authentication_options("approve", nonce, issued), "nonce": nonce, "issuedAtMs": issued}, {}
        # --- authorize (routes/oauth.ts) ---
        if method == "GET" and path == "/authorize":
            return self.authorize(query, follow_redirects)
        # --- the consent (routes/consent.ts) ---
        if path.startswith("/v1/consent/"):
            rest = path[len("/v1/consent/"):]
            request_id, _, action = rest.partition("/")
            if method == "GET" and not action:
                return self.consent_read(request_id, query, headers)
            if method == "POST" and action == "agent":
                return self.consent_agent(request_id, headers, payload)
            if method == "POST" and action == "finish":
                return self.consent_finish(request_id, headers, payload)
            if method == "POST" and action == "checkout":
                raise AssertionError("the harness opened a checkout, which Spec T21 forbids by name")
        if method == "POST" and path == "/token":
            return self.token(payload or {})
        if method == "POST" and path == "/mcp":
            return self.mcp(headers, payload or {})
        raise AssertionError("the test reached for %s %s" % (method, path))

    def verify_assertion(self, response, challenge, passkey):
        parsed = PK.parse_authenticator_data(PK.b64url_decode(str((response.get("response") or {}).get("authenticatorData", ""))))
        self.signatures.append(str((response.get("response") or {}).get("signature", "")))
        if self.before_verify is not None:
            self.before_verify(parsed["counter"])
        try:
            new_counter = PK.verify_assertion(response, challenge, self.origin, self.rp_id, passkey["publicKey"], passkey["signCount"])
        except PK.PasskeyRefused as err:
            raise Refused("PASSKEY_REJECTED", str(err)[:200])
        if passkey["signCount"] > 0 and new_counter <= passkey["signCount"]:
            raise Refused("PASSKEY_REJECTED", CLONED_SAID)
        passkey["signCount"] = new_counter
        self.assertions_verified += 1

    def authorize(self, query, follow_redirects):
        if follow_redirects:
            raise AssertionError("the harness followed the authorize redirect instead of reading Location (Spec T21 §3)")
        client_id = (query.get("client_id") or [""])[0]
        client = self.clients.get(client_id)
        if not client:
            return 400, {"error": "invalid_client", "error_description": "Invalid client_id"}, {}
        redirect_uri = (query.get("redirect_uri") or [""])[0]
        if not any(self.redirect_matches(redirect_uri, known) for known in client["redirect_uris"]):
            return 400, {"error": "invalid_request", "error_description": "Unregistered redirect_uri"}, {}
        state = (query.get("state") or [None])[0]

        def fail(error, description):
            url = redirect_uri + "?" + urllib.parse.urlencode({"error": error, "error_description": description, **({"state": state} if state else {})})
            return 302, "", {"Location": url}

        if (query.get("response_type") or [""])[0] != "code":
            return fail("unsupported_response_type", "Only the authorization code flow is supported")
        challenge = (query.get("code_challenge") or [""])[0]
        if not challenge:
            return fail("invalid_request", "code_challenge is required: PKCE is mandatory on this server")
        if (query.get("code_challenge_method") or [""])[0] != "S256":
            return fail("invalid_request", "code_challenge_method must be S256: this server does not accept the plain method")
        resource = (query.get("resource") or [None])[0]
        if resource is not None and resource != self.issuer + "/mcp":
            return fail("invalid_target", "this authorization server issues tokens for its own MCP endpoint only")
        scopes = [s for s in (query.get("scope") or [""])[0].split(" ") if s]
        unknown = [s for s in scopes if s not in ("aeredium:act", "aeredium:read")]
        if unknown:
            return fail("invalid_scope", "this authorization server does not issue the scope %s" % " ".join(unknown))
        row = {"id": str(uuid.uuid4()), "clientId": client_id, "redirectUri": redirect_uri, "codeChallenge": challenge, "scopes": scopes or ["aeredium:act"],
               "clientState": state, "resource": resource, "state": "pending", "customerId": None, "agentId": None, "connectionId": None,
               "codeHash": None, "consumedAt": None, "expiresAt": time.time() + 4 * 3600}
        self.authorizations[row["id"]] = row
        return 302, "", {"Location": "%s/consent?request=%s" % (self.issuer, row["id"])}

    @staticmethod
    def redirect_matches(requested, registered):
        if requested == registered:
            return True
        try:
            req, reg = urllib.parse.urlparse(requested), urllib.parse.urlparse(registered)
        except ValueError:
            return False
        loopback = ("127.0.0.1", "localhost", "::1")
        return req.hostname in loopback and reg.hostname in loopback and req.scheme == reg.scheme and req.path == reg.path and req.query == reg.query

    def open_request(self, request_id):
        row = self.authorizations.get(request_id)
        if not row:
            raise Refused("AUTHORIZATION_NOT_FOUND")
        if row["state"] != "pending" or row["expiresAt"] <= time.time():
            raise Refused("AUTHORIZATION_NOT_OPEN", state="expired" if row["expiresAt"] <= time.time() else row["state"])
        return row

    @staticmethod
    def rank_for_scopes(scopes):
        return "reader" if scopes and all(s == "aeredium:read" for s in scopes) else "agent"

    def list_my_agents(self, customer_id):
        return [{"id": a["id"], "name": a["name"], "roleId": a["roleId"], "walletAddress": a["walletAddress"],
                 "connectionId": (self.connection_of(a["id"]) or {}).get("id")}
                for a in self.agents if a["customerId"] == customer_id and a["state"] == "active"]

    def consent_read(self, request_id, query, headers):
        try:
            row = self.open_request(request_id)
        except Refused as refused:
            state = "not_found" if refused.code == "AUTHORIZATION_NOT_FOUND" else refused.detail.get("state", "closed")
            said = ("This connection request has run out. Connect again from Claude." if state in ("expired", "not_found")
                    else "This connection request was already answered. There is nothing left to do here.")
            return 200, {"stage": "closed", "closed": {"state": state, "said": said}}, {}
        base = {"request": {"id": row["id"], "clientId": row["clientId"], "scopes": row["scopes"]}, "ranks": list(RANK_VIEWS.values()),
                "requestedRank": self.rank_for_scopes(row["scopes"])}
        try:
            customer, _ = self.caller(headers)
        except Refused:
            return 200, dict(base, stage="sign_in", customer=None), {}
        subscription, standing = self.standing_of(customer["id"])
        view = {"id": customer["id"], "displayName": customer["displayName"], "email": customer["email"], "country": customer["country"],
                "fundingAddress": customer["fundingAddress"]}
        sub_view = {"plan": subscription["plan"], "state": subscription["state"], "standing": standing} if subscription else None
        if standing != "paid":
            return 200, dict(base, stage="pay", customer=view, subscription=sub_view), {}
        connected = self.standing_connection(customer["id"])
        if connected and (query.get("connect") or [""])[0] != "1":
            agent = next((a for a in self.agents if a["id"] == connected["agentId"]), None)
            return 200, dict(base, stage="connected", customer=view, subscription=sub_view, connected={
                "connection": {"id": connected["id"], "rank": RANK_VIEWS[connected["rank"]], "credentialPrefix": connected["credentialPrefix"]},
                "defaultRank": "agent",
                "agent": {"id": agent["id"], "name": agent["name"], "roleId": agent["roleId"], "walletAddress": agent["walletAddress"]} if agent else None,
                "said": "Claude does not yet hold your connection. Press Finish to hand it over.", "another": "Connect a different agent"}), {}
        return 200, dict(base, stage="agent", customer=view, subscription=sub_view, roles=[dict(r) for r in self.roles],
                         chainOffer={"chains": [{"key": k, "name": k.title()} for k in OFFERED_CHAINS], "unreadable": None},
                         agents=self.list_my_agents(customer["id"]),
                         allowance={"activeAgents": len(self.list_my_agents(customer["id"])), "said": "…"}), {}

    def consent_agent(self, request_id, headers, payload):
        customer, _ = self.caller(headers, mutating=True)
        row = self.open_request(request_id)
        body = payload or {}
        for field in ("name", "roleId", "fundingAddress", "answers", "nonce", "issuedAtMs", "response"):
            if field not in body:
                raise Refused("REQUEST_MALFORMED", issues="%s: Required" % field)
        if body.get("rank") not in (None, "agent", "reader"):
            raise Refused("REQUEST_MALFORMED", issues="rank: Invalid enum value")
        answers = body["answers"]
        if not isinstance(answers, dict):
            raise Refused("REQUEST_MALFORMED", issues="answers: Expected object")
        for field in ("perTxUsd", "dailyUsd", "holdAboveUsd", "maxTxPerDay", "counterpartiesScope"):
            if not isinstance(answers.get(field), str):
                raise Refused("REQUEST_MALFORMED", issues="answers.%s: Required" % field)
        if not isinstance(answers.get("chains"), list) or not answers["chains"]:
            raise Refused("REQUEST_MALFORMED", issues="answers.chains: Array must contain at least 1 element(s)")
        if not isinstance(answers.get("counterparties"), list):
            raise Refused("REQUEST_MALFORMED", issues="answers.counterparties: Required")
        # readAnswers (routes/consent.ts): the two budgets may not be blank; every figure is dollars to the cent
        for field, label in (("perTxUsd", "Per trade"), ("dailyUsd", "Per day")):
            if answers[field].strip() == "":
                raise Refused("ANSWER_INVALID", "%s was left blank, and a blank is not a figure" % label)
        for field in ("perTxUsd", "dailyUsd", "holdAboveUsd"):
            if answers[field].strip() and not DOLLARS_RE.match(answers[field].strip()):
                raise Refused("ANSWER_INVALID", "%s must be an amount in US dollars, written as digits with at most two decimal places — it was %s"
                              % (field, json.dumps(answers[field])))
        if answers["maxTxPerDay"].strip() and not answers["maxTxPerDay"].strip().isdigit():
            raise Refused("ANSWER_INVALID", "the number of transactions a day must be a whole number written as digits")
        self.presses.append({"body": body, "customerId": customer["id"]})
        subscription, standing = self.standing_of(customer["id"])
        if standing != "paid":
            raise Refused("SUBSCRIPTION_LAPSED" if standing == "lapsed" else "SUBSCRIPTION_REQUIRED",
                          "nothing was created and nothing was charged: an agent is created only for a paid subscription, and this one is not paid.")
        strangers = [c for c in answers["chains"] if c not in OFFERED_CHAINS]
        if strangers:
            raise Refused("ANSWER_INVALID", "%s is not a chain this connector offers. The chains on offer are the ones the MCP Wallet's own registry "
                          "can read a balance on AND the access platform serves: %s. Nothing was created." % (", ".join(strangers), ", ".join(OFFERED_CHAINS)))
        # verifyStepUp: the passkey must be this customer's, under the purpose `approve`, and the counter must move
        challenge = self.assert_challenge("approve", body["nonce"], body["issuedAtMs"])
        passkey = self.passkeys.get((body["response"] or {}).get("id"))
        if not passkey or passkey["customerId"] != customer["id"]:
            raise Refused("PASSKEY_REJECTED", "that passkey does not belong to the person signed in here, so nothing was approved and no agent was created")
        self.verify_assertion(body["response"], challenge, passkey)
        role = next((r for r in self.roles if r["id"] == body["roleId"]), None)
        if role is None:
            raise Refused("ROLE_UNKNOWN")
        rank = body.get("rank") or self.rank_for_scopes(row["scopes"])
        # the platform: the package's seats, and a destination that is not an address (agent_whitelist_authoring.go)
        mine = [a for a in self.agents if a["customerId"] == customer["id"] and a["state"] == "active"]
        if len(mine) >= self.seats:
            raise Refused("AAP_REFUSED", "the access platform refused the agent's own credential (HTTP 409): plan %s admits %d agent credentials and %d are active; "
                          "aer_connect_says: the Team package holds ten" % (PLATFORM_PLAN, self.seats, len(mine)), status="409")
        for index, address in enumerate(answers["counterparties"]):
            if not ADDRESS_RE.match(str(address)):
                raise Refused("AAP_REFUSED", "the access platform refused the agent's pact (HTTP 400): scope.counterparties_allowed[%d] is %s, which is not an address on arbitrum"
                              % (index, json.dumps(address)), status="400")
        if customer["fundingAddress"] is None:
            customer["fundingAddress"] = body["fundingAddress"].strip()
            customer["aapAccountId"] = "acct-" + secrets.token_hex(4)
        document = {"scope": {"chains": list(answers["chains"]), "counterparties_allowed": [a.lower() for a in answers["counterparties"]],
                              "counterparties_whitelist_scope": answers["counterpartiesScope"].strip().lower(),
                              **({"assets_allowed": list(answers["assets"])} if isinstance(answers.get("assets"), list) else {})},
                    "budgets": {"per_tx_usd_cents": int(round(float(answers["perTxUsd"]) * 100)), "daily_usd_cents": int(round(float(answers["dailyUsd"]) * 100)),
                                "hold_above_usd_cents": int(round(float(answers["holdAboveUsd"] or "0") * 100)), "max_tx_per_day": int(answers["maxTxPerDay"] or "0")}}
        agent = {"id": str(uuid.uuid4()), "customerId": customer["id"], "name": body["name"].strip(), "roleId": body["roleId"], "state": "active",
                 "walletAddress": "0x" + secrets.token_hex(20), "walletChain": answers["chains"][0], "document": document, "pactId": None}
        agent["pactId"] = "aerconn:%s" % agent["id"]
        self.agents.append(agent)
        connection = self.mint_connection(agent, rank, row["clientId"])
        row.update(customerId=customer["id"], agentId=agent["id"], connectionId=connection["id"], scopes=SCOPES_FOR_RANK[rank])
        return 200, {"receipt": {
            "finish": {"said": "Fund the wallet, then press Finish; Claude then has five minutes to redeem the code.", "label": "Finish and return to Claude"},
            "agent": {"id": agent["id"], "name": agent["name"], "roleId": agent["roleId"], "credentialPrefix": "cp-" + secrets.token_hex(2)},
            "pact": {"id": agent["pactId"], "state": "active", "document": document, "said": "These are the limits you set, filed as your agent’s mandate at the access platform."},
            "wallet": {"id": "w-" + secrets.token_hex(3), "address": agent["walletAddress"], "chain": agent["walletChain"], "isMock": False, "said": "Fund this address to give your agent money."},
            "connection": {"id": connection["id"], "rank": RANK_VIEWS[rank], "credentialPrefix": connection["credentialPrefix"]},
        }}, {}

    def consent_finish(self, request_id, headers, payload):
        customer, _ = self.caller(headers, mutating=True)
        row = self.open_request(request_id)
        if row["customerId"] is not None and row["customerId"] != customer["id"]:
            raise Refused("AUTHORIZATION_NOT_OPEN", "this connection request belongs to another customer", state="granted")
        body = payload if isinstance(payload, dict) else {}
        self.finishes.append({"body": dict(body), "customerId": customer["id"]})
        if body.get("connectionId") is not None and body.get("agentId") is not None:
            raise Refused("REQUEST_MALFORMED", issues="body: a press names either the connection to hand over or the agent to connect for the first time, never both")
        if body.get("rank") not in (None, "agent", "reader"):
            raise Refused("REQUEST_MALFORMED", issues="rank: Invalid enum value")
        if body.get("agentId") is not None:
            agent = next((a for a in self.agents if a["id"] == body["agentId"] and a["customerId"] == customer["id"]), None)
            if agent is None:
                raise Refused("AGENT_NOT_FOUND")
            if self.connection_of(agent["id"]):
                raise Refused("AGENT_ALREADY_CONNECTED", "this agent already holds a connection; hand that one over instead. Nothing was minted and nothing was changed.")
            connection = self.mint_connection(agent, body.get("rank") or self.rank_for_scopes(row["scopes"]), row["clientId"])
        else:
            named = self.connections.get(row["connectionId"]) if row.get("connectionId") else None
            chosen = self.connections.get(body["connectionId"]) if body.get("connectionId") else None
            connection = named or chosen or self.standing_connection(customer["id"])
            if not connection or connection["state"] != "active" or connection["customerId"] != customer["id"]:
                raise Refused("CONNECTION_NOT_FOUND", "there is no standing connection to hand over. Name an agent on this page first; nothing was changed.")
            if body.get("rank"):
                connection["rank"] = body["rank"]
            connection["clientId"] = row["clientId"]
        code = b64url(secrets.token_bytes(32))
        self.last_code = code
        row.update(state="granted", customerId=customer["id"], agentId=connection["agentId"], connectionId=connection["id"],
                   scopes=SCOPES_FOR_RANK[connection["rank"]], codeHash=hashlib.sha256(code.encode("ascii")).hexdigest(), expiresAt=time.time() + 300)
        self.codes[row["codeHash"]] = row["id"]
        redirect = row["redirectUri"] + "?" + urllib.parse.urlencode({"code": code, **({"state": row["clientState"]} if row["clientState"] else {})})
        return 200, {"redirectTo": redirect}, {}

    def token(self, form):
        def failure(error, description, status=400):
            return status, {"error": error, "error_description": description}, {}
        client_id = form.get("client_id", "")
        if client_id not in self.clients:
            return failure("invalid_client", "Invalid client_id", 401)
        if form.get("client_secret"):
            return failure("invalid_client", "this authorization server issues no client secrets; authentication is PKCE", 401)
        grant = form.get("grant_type", "")
        if grant == "authorization_code":
            code, verifier = form.get("code", ""), form.get("code_verifier", "")
            if not code:
                return failure("invalid_request", "code is required")
            if not verifier:
                return failure("invalid_request", "code_verifier is required: PKCE is mandatory on this server")
            row_id = self.codes.get(hashlib.sha256(code.encode("ascii")).hexdigest())
            row = self.authorizations.get(row_id) if row_id else None
            if not row or row["clientId"] != client_id:
                return failure("invalid_grant", "this authorization code is not one this server issued to this client")
            if row["consumedAt"] is not None:
                return failure("invalid_grant", "this authorization code has already been redeemed")
            if row["expiresAt"] <= time.time():
                return failure("invalid_grant", "this authorization code has expired")
            expected = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
            if expected != row["codeChallenge"]:
                return failure("invalid_grant", "the code_verifier does not match the code_challenge")
            if form.get("redirect_uri") is not None and form["redirect_uri"] != row["redirectUri"]:
                return failure("invalid_grant", "redirect_uri does not match the one the authorization was granted to")
            row["consumedAt"] = time.time()
            return 200, self.issue_tokens(row["connectionId"], row["scopes"]), {}
        if grant == "refresh_token":
            if self.refresh_refused or form.get("refresh_token", "") not in self.refresh_tokens:
                return failure("invalid_grant", "this refresh token is not one this server issued, or it has been revoked")
            held = self.refresh_tokens.pop(form["refresh_token"])
            return 200, self.issue_tokens(held["connectionId"], held["scopes"]), {}
        return failure("unsupported_grant_type", "The grant type is not supported by this authorization server.")

    def issue_tokens(self, connection_id, scopes):
        access, refresh = "at-" + b64url(secrets.token_bytes(32)), "rt-" + b64url(secrets.token_bytes(32))
        self.access_tokens[access] = {"connectionId": connection_id, "scopes": scopes}
        self.refresh_tokens[refresh] = {"connectionId": connection_id, "scopes": scopes}
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": 3600, "scope": " ".join(scopes)}

    # -- the MCP door a stored token opens (routes/mcp.ts, mcprelay.ts) ------------
    def mcp(self, headers, payload):
        bearer = next((v for k, v in headers.items() if k.lower() == "authorization"), "").replace("Bearer ", "")
        held = self.access_tokens.get(bearer)
        if not held and self.mcp_refuses_unknown_bearer:
            return 401, {"jsonrpc": "2.0", "error": {"code": -32001, "message": "invalid_token: the bearer is not one this server issued"}}, {"WWW-Authenticate": 'Bearer error="invalid_token"'}
        connection = self.connections.get((held or {}).get("connectionId"))
        agent = next((a for a in self.agents if connection and a["id"] == connection["agentId"]), None)
        method = payload.get("method")
        rpc_id = payload.get("id")
        if method == "notifications/initialized":
            return 202, "", {}
        if method == "initialize":
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                                                                     "serverInfo": {"name": "aer-connect", "version": "double"}, "instructions": "AER Connect."}}, {}
        if method == "tools/list":
            tools = [{"name": n, "inputSchema": {"properties": p}} for n, p in (
                ("aerconnect_my_agent", {}), ("aerconnect_guide", {"question": {}}), ("police.check_action", {"action_kind": {}}),
                ("wallet.wallet_status", {"wallet_id": {}}), ("wallet.get_balances", {"wallet_id": {}}), ("wallet.build_transaction", {"wallet_id": {}}),
                ("wallet.submit_transaction", {"wallet_id": {}}))]
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": tools}}, {}
        if method == "tools/call":
            name = (payload.get("params") or {}).get("name")
            if name == "aerconnect_my_agent" and agent is not None:
                self.my_agent_calls += 1
                facts = {"source": "aer-connect", "agent": {"id": agent["id"], "name": agent["name"], "roleId": agent["roleId"]},
                         "connection": {"id": connection["id"], "rank": connection["rank"], "standing": "paid"},
                         "wallet": {"id": "w-" + agent["id"][:6], "address": agent["walletAddress"], "chain": agent["walletChain"]},
                         "fundingWallet": {"address": self.customers[agent["customerId"]]["fundingAddress"]},
                         "caps": {"maxPerTxUsdCents": 2000, "maxPerDayUsdCents": 10000, "said": "per trade US$20.00, per day US$100.00"},
                         "document": agent["document"], "said": "…"}
                return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(facts)}]}}, {}
            if name == "wallet.wallet_status" and agent is not None:
                status = {"wallet_id": "w-" + agent["id"][:6], "address": agent["walletAddress"], "chain": agent["walletChain"],
                          "native": {"symbol": "ETH", "wei": 10 ** 15}, "pact": {"id": agent["pactId"], "policy_hash": POLICY_HASH, "state": "active", "policy_generation": 1}}
                return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(status)}]}}, {}
            return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": "no such tool here"}], "isError": True}}, {}
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "method not found"}}, {}


# ---------------------------------------------------------------------------
# The same double served over HTTP on the loopback, for a test that runs the harness as a SCRIPT in a subprocess: the
# real urllib, the real cookie jar, the real 302. The port is the test's, bound by the double and never by the harness.
# ---------------------------------------------------------------------------
class _Handler(http.server.BaseHTTPRequestHandler):
    double = None

    def _serve(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items()}
        answer = self.double(self.command, self.double.issuer + self.path, headers, body, follow_redirects=False)
        data = answer.text.encode("utf-8")
        self.send_response(answer.status)
        for name, value in answer.headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_GET = _serve
    do_POST = _serve

    def log_message(self, fmt, *args):  # nothing of the wire is printed
        return


def serve(double):
    """Serve the double on 127.0.0.1 at a free port; the double's issuer, origin and rp id become that address. Returns the server."""
    handler = type("Handler", (_Handler,), {"double": double})
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    double.issuer = "http://127.0.0.1:%d" % server.server_address[1]
    double.origin = double.issuer
    double.rp_id = "127.0.0.1"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
