"""
Spec T21 (26 September 2026): the corridor harness consents its own agents — it signs up once with its own
passkey, brings its own wallet address, and runs the series with no browser and no hand. Each test here was red
on main (there was no corridor_consent.py, no seat script, no funding-wallet file, and every consent printed a
link and waited on a listener).

Against a double of the connector's auth, authorize and consent roads (tests/consent_double.py), written to the
calls the consent page makes and verifying the passkey with aer360_passkey.verify_registration and
verify_assertion; the seat script against a psql that answers as told and writes down what it was asked; S5 of
the estate harness against the estate double.
"""
import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H360  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import corridor_consent as C  # noqa: E402
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

try:
    from .consent_double import ConnectorDouble, ISSUER, serve
    from .fakes import FakeSession, OWNER, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from consent_double import ConnectorDouble, ISSUER, serve
    from fakes import FakeSession, OWNER, runner_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEAT_SCRIPT = os.path.join(ROOT, "tools", "harness_seat.sh")
FUNDING = h.checksum_address("0x8bc9" + "a1" * 16 + "4949")
CUSTOMER_ID = "0f3a9b2c-1d4e-4f5a-8b6c-7d8e9f0a1b2c"


def write_funding(path, address):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"address": address, "chain": "arbitrum", "keyId": "key-1", "readAt": "2026-09-26T00:00:00Z"}, handle)


def mode_of(path):
    return oct(os.stat(path).st_mode & 0o777)


class ConsentBase(unittest.TestCase):
    seated = True
    standing = None

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = os.path.join(self.tmp, "store")
        self.runs = os.path.join(self.tmp, "runs")
        self.double = ConnectorDouble(seated=self.seated, standing=self.standing)
        self._http = h.http_request
        h.http_request = self.double
        self.funding = os.path.join(self.tmp, "funding-wallet.json")
        write_funding(self.funding, FUNDING)
        self.said = []
        self.records = []

    def tearDown(self):
        h.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def row(self, listed=OWNER, scope="agent", nogas=None):
        return {"agents": {"trader": "alpha-trader", "payer": "alpha-payer", "payer_nogas": nogas}, "listed_address": listed, "payer_list_scope": scope}

    def record(self, **line):
        self.records.append(line)

    def consent(self, role, label=None, tester="alpha", row=None, **kwargs):
        return C.consent(role, label or "%s-%s" % (tester, role), tester, ISSUER, self.store, row if row is not None else self.row(),
                         self.record, self.said.append, funding_wallet=self.funding, **kwargs)

    def run_file(self, listed=OWNER, scope="agent", nogas=None):
        return {"issuer": ISSUER, "testers": {"alpha": self.row(listed, scope, nogas)}, "chains": {}}

    def runner(self, run_file=None):
        oauth = h.Oauth(ISSUER, self.store, say=self.said.append)
        folder = h.RunFolder(self.runs, "alpha")
        return h.Runner("alpha", run_file or self.run_file(), oauth, folder, say=self.said.append, ask=lambda q: "", sleep=lambda s: None,
                        funding_wallet_path=self.funding)

    def born(self):
        """The harness's customer born and seated with no agent standing: a consent stopped at the seat, then the operator's seat."""
        self.double.default_standing = "none"
        with self.assertRaises(C.ConsentStop):
            self.consent("trader")
        customer = next(iter(self.double.customers.values()))
        self.double.seat(customer["id"], "paid")
        self.double.default_standing = "paid"
        self.said.clear()
        self.records.clear()
        self.double.calls.clear()
        return customer

    def statuses(self):
        """The wire sequence as walked, each road with its status, the consent id replaced by :id."""
        out = []
        for method, path, status in self.double.calls:
            if path.startswith("/v1/consent/"):
                rest = path[len("/v1/consent/"):]
                _, _, action = rest.partition("/")
                path = "/v1/consent/:id" + ("/" + action if action else "")
            out.append((method, path, status))
        return out


class AFreshTesterSignsUpAndIsNotSeated(ConsentBase):
    seated = False

    def test_a_fresh_tester_signs_up_with_a_software_passkey_and_the_run_stops_with_the_seat_sentence_naming_the_customer_id(self):
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        customer = next(iter(self.double.customers.values()))
        self.assertEqual(stopped.exception.sentence, "the harness is not seated: run tools/harness_seat.sh %s on the box, then rerun" % customer["id"])
        self.assertEqual(stopped.exception.outcome, "refused")
        self.assertEqual(stopped.exception.code, "SUBSCRIPTION_REQUIRED")
        self.assertNotIn("http", stopped.exception.sentence, "one sentence, one command, no link")
        # the customer as the harness names itself
        self.assertEqual((customer["displayName"], customer["email"], customer["country"]), ("alpha (harness)", "harness+alpha@aeredium.io", "AU"))
        self.assertEqual(self.double.registrations_verified, 1, "the registration was verified as @simplewebauthn/server verifies a `none` attestation")
        self.assertEqual(len(self.double.passkeys), 1)
        # the two files, mode 600
        passkey_path = os.path.join(self.store, "alpha", "passkey.json")
        customer_path = os.path.join(self.store, "alpha", "customer.json")
        self.assertEqual(mode_of(passkey_path), "0o600")
        self.assertEqual(mode_of(customer_path), "0o600")
        with open(customer_path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["id"], customer["id"])
        stored = PK.SoftwarePasskey.load(passkey_path)
        self.assertEqual(stored.rp_id, "connector.test", "rp.id came from the server's options")
        self.assertEqual(stored.origin, ISSUER, "the origin is the issuer from the run file")
        # the one line printed, and the road as walked: stopped at the read, before any press
        self.assertEqual(self.said, ["signed up as the harness's own customer %s; seat it with tools/harness_seat.sh %s" % (customer["id"], customer["id"])])
        self.assertEqual(self.statuses(), [("POST", "/v1/auth/signup/options", 200), ("POST", "/v1/auth/signup/verify", 200),
                                           ("GET", "/.well-known/oauth-authorization-server", 200), ("POST", "/register", 201),
                                           ("GET", "/.well-known/oauth-protected-resource/mcp", 200), ("GET", "/authorize", 302),
                                           ("GET", "/v1/consent/:id", 200)])
        self.assertEqual(self.double.presses, [])
        self.assertEqual(self.double.finishes, [])

    def test_a_second_run_signs_in_with_the_stored_passkey_and_is_not_born_twice(self):
        with self.assertRaises(C.ConsentStop):
            self.consent("trader")
        self.said.clear()
        self.double.calls.clear()
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        self.assertEqual(len(self.double.customers), 1, "a customer once born is never born again")
        self.assertEqual(self.statuses()[:2], [("POST", "/v1/auth/signin/options", 200), ("POST", "/v1/auth/signin/verify", 200)])
        self.assertEqual(self.said, [], "nothing is printed on the way to the seat sentence")
        self.assertIn("the harness is not seated: run tools/harness_seat.sh", stopped.exception.sentence)

    def test_a_lapsed_seat_says_so(self):
        self.double = ConnectorDouble(standing="lapsed")
        h.http_request = self.double
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        customer = next(iter(self.double.customers.values()))
        self.assertEqual(stopped.exception.sentence, "the harness is not seated (its seat lapsed): run tools/harness_seat.sh %s on the box, then rerun" % customer["id"])
        self.assertEqual(stopped.exception.code, "SUBSCRIPTION_LAPSED")

    def test_a_tester_name_outside_the_form_is_refused_before_any_call(self):
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader", label="Alpha_1-trader", tester="Alpha_1")
        self.assertEqual(stopped.exception.sentence, C.TESTER_NAME_SENTENCE % ("Alpha_1", "harness+<tester>@aeredium.io"))
        self.assertEqual(self.double.calls, [])

    def test_the_run_from_the_command_line_stops_with_the_seat_sentence_before_any_series_test(self):
        path = os.path.join(self.tmp, "harness_run.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.run_file(listed=FUNDING), handle)
        out = io.StringIO()
        with patched(h, "STORE_DIR", self.store), patched(C, "funding_wallet_path", lambda: self.funding), contextlib.redirect_stdout(out):
            code = h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs, "--series", "A"])
        customer = next(iter(self.double.customers.values()))
        self.assertEqual(code, 2)
        self.assertIn("the harness is not seated: run tools/harness_seat.sh %s on the box, then rerun" % customer["id"], out.getvalue())
        self.assertNotIn("A1", out.getvalue(), "no series test ran")
        self.assertNotIn("Consent link", out.getvalue())


@contextlib.contextmanager
def patched(module, name, value):
    before = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, before)


class ASeatedTesterConsentsByCreating(ConsentBase):
    def test_the_trader_is_created_with_the_books_answers_and_finished_by_its_connection(self):
        stored = self.consent("trader")
        customer = next(iter(self.double.customers.values()))
        self.assertEqual(self.said, [
            "signed up as the harness's own customer %s; seat it with tools/harness_seat.sh %s" % (customer["id"], customer["id"]),
            "consented alpha-trader as the harness's own customer with its stored passkey; agent %s, rank agent; funding wallet %s; tokens stored" % (self.double.agents[0]["id"], FUNDING),
        ])
        # the wire sequence as walked, with each road's status (the PR body's first item)
        self.assertEqual(self.statuses(), [
            ("POST", "/v1/auth/signup/options", 200), ("POST", "/v1/auth/signup/verify", 200),
            ("GET", "/.well-known/oauth-authorization-server", 200), ("POST", "/register", 201), ("GET", "/.well-known/oauth-protected-resource/mcp", 200),
            ("GET", "/authorize", 302), ("GET", "/v1/consent/:id", 200), ("POST", "/v1/auth/stepup/options", 200),
            ("POST", "/v1/consent/:id/agent", 200), ("POST", "/v1/consent/:id/finish", 200), ("POST", "/token", 200),
        ])
        # the press: the label as the name, the role, the harness's own funding wallet, the role's default rank, the book
        press = self.double.presses[0]["body"]
        self.assertEqual((press["name"], press["roleId"], press["fundingAddress"], press["rank"]), ("alpha-trader", "trader.v1", FUNDING, "agent"))
        self.assertEqual(press["answers"], {"perTxUsd": "20", "dailyUsd": "100", "holdAboveUsd": "50", "maxTxPerDay": "50",
                                            "chains": ["arbitrum", "base"], "assets": ["USDC", "USDT", "WETH"],
                                            "counterpartiesScope": "agent", "counterparties": []})
        self.assertEqual(self.double.assertions_verified, 1, "the step-up's assertion was verified under the purpose approve")
        connection = self.double.connection_of(self.double.agents[0]["id"])
        self.assertEqual(self.double.finishes, [{"body": {"connectionId": connection["id"]}, "customerId": customer["id"]}],
                         "Spec 35's first connection: the receipt's connection id, and nothing else")
        # the tokens, where the harness always stored them
        path = os.path.join(self.store, "alpha-trader.json")
        self.assertEqual(mode_of(path), "0o600")
        self.assertEqual(stored["access_token"], next(iter(self.double.access_tokens)))
        self.assertEqual(stored["customer_id"], customer["id"])
        self.assertEqual(stored["agent_id"], self.double.agents[0]["id"])
        self.assertIn("the harness's own passkey (Spec T21), created with the book's answers", stored["consented_by"])
        self.assertEqual(stored["funding_address"], FUNDING)
        self.assertEqual(customer["fundingAddress"], FUNDING, "the Wallet registers the harness's address as the owner root")

    def test_the_payer_lists_the_run_files_address_under_the_run_files_scope_and_payer_nogas_is_a_payer_under_its_own_name(self):
        self.consent("payer", row=self.row(scope="shared"))
        press = self.double.presses[-1]["body"]
        self.assertEqual((press["name"], press["roleId"]), ("alpha-payer", "payer.v1"))
        self.assertEqual(press["answers"]["counterpartiesScope"], "shared")
        self.assertEqual(press["answers"]["counterparties"], [OWNER])
        self.assertEqual(press["answers"]["maxTxPerDay"], "20", "the role's own count, from the payload")
        self.consent("payer_nogas", label="alpha-payer_nogas", row=self.row(nogas="alpha-payer_nogas"))
        press = self.double.presses[-1]["body"]
        self.assertEqual((press["name"], press["roleId"], press["answers"]["counterparties"]), ("alpha-payer_nogas", "payer.v1", [OWNER]))

    def test_a_payer_with_no_listed_address_is_refused_before_the_press(self):
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("payer", row=self.row(listed=""))
        self.assertEqual(stopped.exception.sentence, C.LISTED_ADDRESS_SENTENCE)
        self.assertEqual(self.double.presses, [])

    def test_no_port_is_bound(self):
        def no_listener():
            raise AssertionError("the consent bound a port")
        with patched(h.Oauth, "_listen", staticmethod(no_listener)):
            self.consent("trader")
        self.assertEqual(len(self.double.agents), 1)

    def test_a_fourth_agent_on_solo_is_refused_in_the_connectors_words_and_told_as_a_refusal(self):
        customer = self.born()
        for name in ("standing-1", "standing-2", "standing-3"):
            self.double.plant_agent(customer["id"], name, "payer.v1")
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        self.assertEqual(stopped.exception.outcome, "refused")
        self.assertEqual((stopped.exception.code, stopped.exception.status), ("AAP_REFUSED", 502))
        self.assertIn("plan connect-solo admits 3 agent credentials", stopped.exception.said)
        self.assertIn("The access platform refused this. Its own words are beside this.", stopped.exception.sentence)
        self.assertIn("the answer will be the same on retry", stopped.exception.sentence)
        for forbidden in ("could not be reached", "try again later", "something went wrong"):
            self.assertNotIn(forbidden, stopped.exception.sentence.lower())
        self.assertIn("Note: 3 agents stand on the harness's customer and Solo seats 3", self.said[-1])
        # and the record: the refusal's code and the platform's words intact, the outcome word first
        refused = [r for r in self.records if r.get("kind") == "consent" and r["http_status"] == 502][-1]
        self.assertEqual(refused["outcome"], "refused")
        self.assertEqual(refused["answer"]["error"]["code"], "AAP_REFUSED")
        self.assertIn("plan connect-solo admits 3 agent credentials", refused["answer"]["error"]["detail"]["cause"])


class AnAgentThatStandsIsHandedOver(ConsentBase):
    def test_the_payer_is_handed_over_by_its_connection_id_where_its_agent_already_holds_one(self):
        customer = self.born()
        planted = self.double.plant_agent(customer["id"], "alpha-payer", "payer.v1", connected=True, counterparties=[OWNER.lower()])
        standing = self.double.connection_of(planted["id"])
        stored = self.consent("payer")
        self.assertEqual(self.double.finishes[-1]["body"], {"connectionId": standing["id"], "rank": "agent"}, "the standing connection, at the role's default rank")
        self.assertEqual(self.double.presses, [], "nothing was created")
        self.assertNotIn(("POST", "/v1/auth/stepup/options", 200), self.statuses(), "no step-up: nothing was approved")
        self.assertEqual(stored["agent_id"], planted["id"])
        self.assertIn("handed over the connection it already holds", stored["consented_by"])

    def test_an_agent_without_a_connection_is_connected_first_and_agent_already_connected_is_never_sent(self):
        customer = self.born()
        planted = self.double.plant_agent(customer["id"], "alpha-payer", "payer.v1", connected=False)
        self.double.calls.clear()
        self.consent("payer")
        self.assertEqual(self.double.finishes[-1]["body"], {"agentId": planted["id"]}, "Spec 35's first connection for an agent born elsewhere")
        self.double.calls.clear()
        self.consent("payer")
        connection = self.double.connection_of(planted["id"])
        self.assertEqual(self.double.finishes[-1]["body"], {"connectionId": connection["id"], "rank": "agent"},
                         "now that a connection stands, it is handed over; {agentId} is never sent where one stands")
        self.assertNotIn(409, [s for _, _, s in self.double.calls])
        self.assertNotIn("AGENT_ALREADY_CONNECTED", json.dumps(self.records))


class TheCounterIsSavedBeforeTheAssertionIsSent(ConsentBase):
    def test_the_file_carries_the_counter_the_connector_is_about_to_judge(self):
        seen = []
        passkey_path = os.path.join(self.store, "alpha", "passkey.json")

        def before_verify(counter):
            with open(passkey_path, encoding="utf-8") as handle:
                seen.append((counter, json.load(handle)["sign_count"]))
        self.double.before_verify = before_verify
        self.consent("trader")  # sign-up (no assertion), then the step-up: counter 1
        self.consent("payer")  # sign-in: 2; the step-up: 3
        self.assertEqual(seen, [(1, 1), (2, 2), (3, 3)], "the count the file holds when the assertion is judged is the count sent")

    def test_a_counter_behind_the_connectors_is_refused_with_the_sentence_and_the_connectors_words_and_never_resent(self):
        self.consent("trader")
        passkey_path = os.path.join(self.store, "alpha", "passkey.json")
        with open(passkey_path, encoding="utf-8") as handle:
            stored = json.load(handle)
        stored["sign_count"] = 0  # the file was not saved after a sign-in
        with open(passkey_path, "w", encoding="utf-8") as handle:
            json.dump(stored, handle)
        self.double.calls.clear()
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("payer")
        self.assertTrue(stopped.exception.sentence.startswith(C.COUNTER_SENTENCE), stopped.exception.sentence)
        self.assertIn("PASSKEY_REJECTED (401)", stopped.exception.sentence)
        self.assertIn("Response counter value 1 was lower than expected 1", stopped.exception.said, "the connector's own words travel")
        self.assertEqual(stopped.exception.outcome, "refused")
        self.assertEqual([c for c in self.double.calls if c[1] == "/v1/auth/signin/verify"], [("POST", "/v1/auth/signin/verify", 401)], "sent once, never resent")
        with open(passkey_path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["sign_count"], 1, "the counter was saved before the assertion went")
        self.assertEqual(len(self.double.customers), 1, "no second customer was born")


class ThePasskeyFileIsWrittenWhole(ConsentBase):
    def test_the_file_is_written_beside_itself_and_moved_over_never_truncated(self):
        moves = []
        real_replace = os.replace

        def watched(src, dst):
            with open(src, encoding="utf-8") as handle:
                moves.append((src, dst, json.load(handle)["sign_count"], os.path.exists(dst)))
            real_replace(src, dst)
        with patched(os, "replace", watched):
            self.consent("trader")
        path = os.path.join(self.store, "alpha", "passkey.json")
        self.assertEqual([m[0] for m in moves], [path + ".tmp"] * 2, "the sign-up's save and the step-up's save, each to the file beside")
        self.assertEqual([m[1] for m in moves], [path] * 2)
        self.assertEqual([m[2] for m in moves], [0, 1])
        self.assertEqual([m[3] for m in moves], [False, True], "the second move replaces a file that stands whole throughout")
        self.assertFalse(os.path.exists(path + ".tmp"))
        self.assertEqual(mode_of(path), "0o600")

    def test_a_passkey_file_that_was_not_written_whole_stops_with_a_sentence_before_any_call(self):
        path = os.path.join(self.store, "alpha", "passkey.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"kind": "aer360-harness software passkey", "pem": "-----BEGIN EC PRIVATE KEY')
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        self.assertTrue(stopped.exception.sentence.startswith("the passkey file at %s cannot be read (" % path), stopped.exception.sentence)
        self.assertIn("it was not written whole. Set that folder aside, or run as a new tester name, which is a new customer", stopped.exception.sentence)
        self.assertEqual(self.double.calls, [])


class TheWalletAddressIsTheHarnessesOwn(ConsentBase):
    def test_a_missing_funding_wallet_file_stops_with_the_s5_sentence_before_any_call(self):
        os.unlink(self.funding)
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        self.assertEqual(stopped.exception.sentence, "no wallet address of the harness's own: run aer360_harness.py first (S5 births the funding wallet and writes it down)")
        self.assertEqual(self.double.calls, [])

    def test_an_address_written_in_one_case_is_checksummed_and_used_and_a_mixed_case_mismatch_refuses_before_any_call(self):
        for spelling in (FUNDING.lower(), "0x" + FUNDING[2:].upper()):
            write_funding(self.funding, spelling)
            self.assertEqual(C.funding_wallet_address(self.funding), FUNDING, spelling)
        write_funding(self.funding, FUNDING.lower())
        self.consent("trader")
        self.assertEqual(self.double.presses[0]["body"]["fundingAddress"], FUNDING, "sent checksummed")
        wrong = FUNDING[:-1] + ("a" if FUNDING[-1] != "a" else "b")  # mixed case, and not its own checksum
        wrong = wrong[:2] + wrong[2:].swapcase() if wrong[2:] == wrong[2:].lower() else wrong
        write_funding(self.funding, wrong)
        self.double.calls.clear()
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("payer")
        self.assertEqual(stopped.exception.sentence, C.CHECKSUM_SENTENCE % (self.funding, wrong, h.checksum_address(wrong)))
        self.assertEqual(self.double.calls, [])
        write_funding(self.funding, "0x1234")
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("payer")
        self.assertEqual(stopped.exception.sentence, C.CHECKSUM_SENTENCE % (self.funding, "0x1234", "not an address of forty hex digits"))

    def test_a_listed_address_that_is_not_the_harnesss_wallet_stops_naming_both_and_the_same_wallet_in_another_case_stands(self):
        path = os.path.join(self.tmp, "harness_run.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.run_file(listed=OWNER), handle, indent=2)
        aer360 = os.path.join(self.tmp, "aer360")
        write_funding(os.path.join(aer360, C.HARNESS_HOLDINGS, C.FUNDING_WALLET_FILE), FUNDING)
        out = io.StringIO()
        with patched(h, "STORE_DIR", self.store), patched(C, "AER360_STORE_DIR", aer360), contextlib.redirect_stdout(out):
            code = h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs, "--series", "A"])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue().strip(), C.LISTED_DIFFERS_SENTENCE % (OWNER, FUNDING, os.path.join(aer360, C.HARNESS_HOLDINGS, C.FUNDING_WALLET_FILE)))
        self.assertEqual(self.double.calls, [], "stopped before any call")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.run_file(listed=FUNDING.lower()), handle, indent=2)
        with open(path, "rb") as handle:
            before = handle.read()
        with patched(h, "STORE_DIR", self.store), patched(C, "AER360_STORE_DIR", aer360), contextlib.redirect_stdout(io.StringIO()):
            code = h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs, "--consent", "trader"])
        self.assertEqual(code, 0, "the same wallet in another spelling is the harness's own, and the consent walks")
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before, "and the run file is left as it was")

    def test_listed_address_is_written_back_only_when_empty_and_printed_before_the_write(self):
        self.double = ConnectorDouble(seated=False)
        h.http_request = self.double
        path = os.path.join(self.tmp, "harness_run.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.run_file(listed=""), handle, indent=2)
        aer360 = os.path.join(self.tmp, "aer360")
        write_funding(os.path.join(aer360, C.HARNESS_HOLDINGS, C.FUNDING_WALLET_FILE), FUNDING)
        out = io.StringIO()
        with patched(h, "STORE_DIR", self.store), patched(C, "AER360_STORE_DIR", aer360), contextlib.redirect_stdout(out):
            code = h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs, "--series", "A"])
        self.assertEqual(code, 2, "the seat stops the run, after the write-back")
        printed = out.getvalue()
        self.assertIn("listed_address for alpha is empty; filling it with the harness's own funding wallet %s and writing it back to %s" % (FUNDING, path), printed)
        self.assertLess(printed.index("writing it back"), printed.index("the harness is not seated"), "printed before the write, before the stop")
        with open(path, encoding="utf-8") as handle:
            written = json.load(handle)
        self.assertEqual(written["testers"]["alpha"]["listed_address"], FUNDING)
        self.assertEqual(written["issuer"], ISSUER, "the rest of the file is as it was")
        # a listed address that stands is never overwritten
        written["testers"]["alpha"]["listed_address"] = FUNDING
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(written, handle, indent=2)
        with open(path, "rb") as handle:
            before = handle.read()
        with patched(h, "STORE_DIR", self.store), patched(C, "AER360_STORE_DIR", aer360), contextlib.redirect_stdout(io.StringIO()):
            h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs, "--series", "A"])
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before)

    def test_a_run_with_an_empty_listed_address_and_no_file_stops_with_the_s5_sentence(self):
        path = os.path.join(self.tmp, "harness_run.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.run_file(listed=""), handle, indent=2)
        out = io.StringIO()
        with patched(h, "STORE_DIR", self.store), patched(C, "AER360_STORE_DIR", os.path.join(self.tmp, "nowhere")), contextlib.redirect_stdout(out):
            code = h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue().strip(), C.NO_WALLET_SENTENCE)
        self.assertEqual(self.double.calls, [])

    def test_the_three_names_of_the_file_are_the_estate_harnesss_own(self):
        self.assertEqual(os.path.expanduser(C.AER360_STORE_DIR), H360.STORE_DIR)
        self.assertEqual(C.HARNESS_HOLDINGS, A.ESTATE["client_id"])
        self.assertEqual(C.FUNDING_WALLET_FILE, H360.FUNDING_WALLET_FILE)
        self.assertEqual(C.funding_wallet_path(), os.path.join(H360.STORE_DIR, "harness-holdings", "funding-wallet.json"))


class TheRunConsentsEveryLabelWhoseTokenIsMissing(ConsentBase):
    def test_consent_missing_consents_the_labels_without_a_token_and_leaves_the_others(self):
        runner = self.runner(self.run_file(nogas="alpha-payer_nogas"))
        runner.oauth.store_tokens("alpha-trader", {"access_token": "at-standing-" + "x" * 20, "refresh_token": "rt-" + "x" * 20}, "mcp-x")
        consented = runner.consent_missing()
        self.assertEqual(consented, ["alpha-payer", "alpha-payer_nogas"])
        self.assertEqual([p["body"]["name"] for p in self.double.presses], ["alpha-payer", "alpha-payer_nogas"])
        self.assertEqual(self.said.count("No token is stored for alpha-payer; the consent runs now."), 1)

    def test_a_label_the_run_file_leaves_null_is_not_consented(self):
        runner = self.runner(self.run_file(nogas=None))
        self.assertEqual(runner.consent_missing(), ["alpha-trader", "alpha-payer"])

    def test_a_token_the_first_call_refuses_is_consented_again_on_the_same_road(self):
        runner = self.runner()
        runner.oauth.store_tokens("alpha-trader", {"access_token": "at-spent-" + "x" * 24, "refresh_token": "rt-spent-" + "x" * 24}, "mcp-x")
        runner.session("trader", "A2")
        self.assertEqual(len(self.double.presses), 1, "the label was consented again, by creating")
        self.assertTrue(any(s.startswith("The token stored for alpha-trader was refused by the connector (") for s in self.said), self.said)
        self.assertEqual(self.double.my_agent_calls, 1, "the new token opened the door")
        self.assertEqual(runner.facts("trader")["name"], "alpha-trader")

    def test_the_command_line_consent_of_one_label_walks_the_road_and_connects(self):
        path = os.path.join(self.tmp, "harness_run.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.run_file(listed=FUNDING), handle, indent=2)
        out = io.StringIO()
        with patched(h, "STORE_DIR", self.store), patched(C, "funding_wallet_path", lambda: self.funding), contextlib.redirect_stdout(out):
            code = h.main(["--tester", "alpha", "--run-file", path, "--out", self.runs, "--consent", "trader"])
        self.assertEqual(code, 0, out.getvalue())
        printed = out.getvalue()
        self.assertIn("consented alpha-trader as the harness's own customer with its stored passkey", printed)
        self.assertIn("Connected as alpha-trader: alpha-trader (trader.v1)", printed)
        self.assertIn("Policy hash now: 0x5237c7e1", printed)
        self.assertNotIn("Consent link", printed)
        self.assertNotIn("listening", printed)

    def test_a_consent_that_stops_inside_a_series_stops_the_series(self):
        self.double = ConnectorDouble(seated=False)
        h.http_request = self.double
        runner = self.runner()
        runner.plan = lambda series, start_at=None: [S.BY_ID["A2"], S.BY_ID["A3"]]  # A2 opens the Trader's session; A1's probes are not the point
        runner.run(["A"])
        stopped = next(o for o in runner.outcomes if o.outcome == h.FAIL and o.line.startswith("stopped at the consent"))
        self.assertIn("the harness is not seated: run tools/harness_seat.sh", stopped.sentence)
        self.assertEqual(runner.stopped, stopped.test.id)
        self.assertEqual(runner.stopped_how, "at the consent")
        later = [o for o in runner.outcomes if o.outcome == h.NOT_RUN]
        self.assertTrue(later, "the tests after the stop were not run")
        self.assertEqual(later[0].sentence, "not run: the series stopped at %s at the consent." % stopped.test.id)
        self.assertIn("**The series stopped at %s: the harness is not seated" % stopped.test.id, runner.report())


class B4ReadsTheList(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_b4_passes_when_the_listed_address_stands_on_the_payers_list_and_asks_for_no_save(self):
        session = FakeSession(document={"scope": {"counterparties_allowed": [OWNER.lower()], "counterparties_whitelist_scope": "agent"}})
        runner = runner_for(session, self.tmp)
        asked = []
        runner.ask = lambda q: asked.append(q) or ""
        test = S.BY_ID["B4"]
        outcome = runner.step_pause(test, test.steps[0], None)
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)
        self.assertIn("the owner's listed address %s stands on the Payer's list as the document states it (1 entry, scope a list for this agent only), written at consent" % OWNER, outcome.sentence)
        self.assertEqual(asked, [], "no pause: nobody is asked to save")
        self.assertEqual(runner.payer_list("payer"), [OWNER.lower()])

    def test_b4_still_pauses_where_the_address_is_not_on_the_list(self):
        session = FakeSession(document={"scope": {"counterparties_allowed": ["0x000000000000000000000000000000000000dEaD"], "counterparties_whitelist_scope": "agent"}})
        runner = runner_for(session, self.tmp)
        asked = []
        runner.ask = lambda q: asked.append(q) or ""
        test = S.BY_ID["B4"]
        outcome = runner.step_pause(test, test.steps[0], None)
        self.assertEqual(asked[:1], ["Press Enter when done: "], "the person is asked to write the line, as before")
        self.assertNotEqual(outcome.outcome, h.PASS)

    def test_a_document_that_states_no_list_is_none_and_b4_pauses(self):
        runner = runner_for(FakeSession(), self.tmp)
        runner.session("payer", "B4")
        self.assertIsNone(runner.payer_list("payer"))


class TheRecordsRedaction(ConsentBase):
    def test_every_wire_exchange_is_recorded_with_the_secrets_redacted_to_their_last_four_characters(self):
        self.consent("trader")
        consent_records = [r for r in self.records if r.get("kind") == "consent"]
        self.assertEqual([r["tool"] for r in consent_records], [
            "POST /v1/auth/signup/options", "POST /v1/auth/signup/verify", "GET /authorize", "GET /v1/consent/%s" % list(self.double.authorizations)[0],
            "POST /v1/auth/stepup/options", "POST /v1/consent/%s/agent" % list(self.double.authorizations)[0], "POST /v1/consent/%s/finish" % list(self.double.authorizations)[0],
            "POST /token",
        ])
        dumped = json.dumps(consent_records, ensure_ascii=False)
        with open(os.path.join(self.store, "alpha", "passkey.json"), encoding="utf-8") as handle:
            pem = json.load(handle)["pem"]
        self.assertNotIn(pem.strip().splitlines()[1], dumped, "no line of the PEM is in the record")
        for secret in list(self.double.sessions) + [s["csrf"] for s in self.double.sessions.values()] + self.double.handles + self.double.signatures + [self.double.last_code]:
            self.assertNotIn(secret, dumped, "a secret is in the record whole")
            self.assertIn(C.last4(secret), dumped, "redacted to its last four characters")
        self.assertIn('"Cookie": "%s"' % C.last4(list(self.double.sessions)[0]), dumped, "the cookie header, a secret key, to its last four")
        self.assertIn('"redirectTo": "http://127.0.0.1:8765/callback?code=%s&state=' % C.last4(self.double.last_code), dumped, "the code inside redirectTo, by value")
        self.assertIn("harness+alpha@aeredium.io", dumped, "everything else is byte for byte")
        self.assertIn('"outcome": "answered"', dumped)
        self.assertIn('"outcome": "redirected"', dumped)
        self.assertNotIn("Consent link", json.dumps(self.said))

    def test_the_wire_redaction_is_the_harnesss_own_with_the_last_four_as_its_mask(self):
        self.assertEqual(h.redact({"code": "receipt_missing", "sentence": "x"}, mask=C.last4), {"code": "receipt_missing", "sentence": "x"})
        self.assertEqual(h.redact({"code": "abcdefghijklmnop", "state": "s"}, mask=C.last4), {"code": "…mnop", "state": "s"})
        ceremony = {"response": {"clientDataJSON": "eyJ0eXBl", "signature": "abcdefgh", "userHandle": "dXNlcg"}, "type": "public-key"}
        self.assertEqual(h.redact(ceremony, mask=C.last4), {"response": {"clientDataJSON": "…eXBl", "signature": "…efgh", "userHandle": "…Nlcg"}, "type": "public-key"})
        self.assertEqual(h.redact("the code abcdefghijklmnop rode by", ["abcdefghijklmnop"], mask=C.last4), "the code …mnop rode by")
        # a door's `response` or `signature` is evidence, not the ceremony's
        wallet = {"ticket": {"id": "t-1", "signature": "0x" + "ab" * 32}, "response": {"verdict": "allow", "receipt": {"issued": True}}}
        self.assertEqual(h.redact(wallet, mask=C.last4), wallet)
        self.assertEqual(h.redact(wallet), wallet)
        self.assertEqual(h.secret_values(ceremony), ["abcdefgh"], "the ceremony's signature is scrubbed by value; the Wallet's is not collected")
        self.assertEqual(h.secret_values(wallet), [])

    def test_the_token_exchange_is_in_the_record_with_the_code_and_the_verifier_redacted(self):
        self.consent("trader")
        exchange = [r for r in self.records if r.get("kind") == "consent" and r["tool"] == "POST /token"]
        self.assertEqual(len(exchange), 1)
        sent = exchange[0]["arguments"]["body"]
        self.assertEqual(sent["grant_type"], "authorization_code")
        self.assertEqual(sent["code"], C.last4(self.double.last_code))
        self.assertTrue(sent["code_verifier"].startswith("…"))
        self.assertEqual(exchange[0]["answer"]["access_token"], C.last4(next(iter(self.double.access_tokens))))
        self.assertEqual(exchange[0]["answer"]["token_type"], "bearer")


class TheBookAgreesWithTheSeries(ConsentBase):
    def test_the_series_figures_are_read_as_data_and_the_book_agrees(self):
        self.assertEqual(C.series_figures(), {"Payer": {"perTxUsd": "20", "holdAboveUsd": "50"}, "Trader": {"dailyUsd": "100", "holdAboveUsd": "50"}})
        self.assertEqual(C.book_disagreements(), [])
        self.assertEqual(C.book_figures("trader"), {"perTxUsd": "20", "dailyUsd": "100", "holdAboveUsd": "50"})
        self.assertIn("(per transaction is 20)", S.BY_ID["C4"].text)

    def test_a_disagreement_stops_the_run_naming_both_before_any_call(self):
        with patched(C, "BOOK_PER_TX_USD", "25"):
            with self.assertRaises(C.ConsentStop) as stopped:
                self.consent("trader")
        self.assertEqual(stopped.exception.sentence, C.BOOK_DISAGREES_SENTENCE % "series.py restores the Payer's per trade to 20 dollars and the book files 25")
        self.assertEqual(self.double.calls, [])

    def test_a_role_that_states_no_count_is_refused_rather_than_filed_as_zero(self):
        roles = [dict(r, questionnaire=dict(r["questionnaire"], maxTxPerDay=None)) for r in self.double.roles]
        self.double.roles = roles
        with self.assertRaises(C.ConsentStop) as stopped:
            self.consent("trader")
        self.assertEqual(stopped.exception.sentence, C.NO_COUNT_SENTENCE % "trader.v1")
        self.assertEqual(self.double.presses, [])


FAKE_PSQL = r'''#!/bin/bash
# A psql that behaves as psql does about variables — a -c string goes to the server VERBATIM, never through the lexer, so
# a :'name' in one is a syntax error; standard input goes through the lexer, where :'name' becomes the quoted value of
# -v name=… — answers as told, and writes down what it was asked (ARGS, then SQL-RAW as received and SQL as interpolated).
LOG="$FAKE_PSQL_LOG"
CMD=""; prev=""
NAMES=(); VALUES=()
for a in "$@"; do
  if [ "$prev" = "-c" ]; then CMD="$a"; fi
  if [ "$prev" = "-v" ]; then NAMES+=("${a%%=*}"); VALUES+=("${a#*=}"); fi
  prev="$a"
done
printf 'ARGS %s\n' "$*" >> "$LOG"
if [ -n "$CMD" ]; then
  printf 'CMD %s\n' "$CMD" >> "$LOG"
  if printf '%s' "$CMD" | grep -Eq ":['\"][A-Za-z_][A-Za-z0-9_]*['\"]"; then echo 'ERROR:  syntax error at or near ":"' >&2; exit 1; fi
  exit 0
fi
SQL=$(cat)
printf 'SQL-RAW %s\n' "$SQL" >> "$LOG"
i=0
while [ "$i" -lt "${#NAMES[@]}" ]; do
  n="${NAMES[$i]}"; v="${VALUES[$i]}"
  pat=":'$n'"; rep="'$v'"; SQL="${SQL//$pat/$rep}"
  pat=":\"$n\""; rep="\"$v\""; SQL="${SQL//$pat/$rep}"
  i=$((i+1))
done
if printf '%s' "$SQL" | grep -Eq ":['\"][A-Za-z_][A-Za-z0-9_]*['\"]"; then echo 'ERROR:  syntax error at or near ":" (a variable that was never set)' >&2; exit 1; fi
printf 'SQL %s\n' "$SQL" >> "$LOG"
case "$SQL" in
  *"INSERT INTO subscriptions"*) if [ -n "${FAKE_SEATED_ROW:-}" ]; then printf '%s\n' "$FAKE_SEATED_ROW"; fi;;
  *"FROM customers WHERE id = '$FAKE_CUSTOMER_ID'::uuid"*) if [ -n "${FAKE_CUSTOMER_ROW:-}" ]; then printf '%s\n' "$FAKE_CUSTOMER_ROW"; fi;;
  *"FROM subscriptions"*"WHERE customer_id = '$FAKE_CUSTOMER_ID'::uuid"*) if [ -n "${FAKE_LIVE_ROWS:-}" ]; then printf '%b\n' "$FAKE_LIVE_ROWS"; fi;;
esac
exit 0
'''


class TheSeatScript(unittest.TestCase):
    """tools/harness_seat.sh: the guard, held with a psql double on PATH and HARNESS_SEAT_BOX=local (no network)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "bin"))
        self.psql = os.path.join(self.tmp, "bin", "psql")
        with open(self.psql, "w", encoding="utf-8") as handle:
            handle.write(FAKE_PSQL)
        os.chmod(self.psql, os.stat(self.psql).st_mode | stat.S_IEXEC)
        self.env_file = os.path.join(self.tmp, "aer-connector.env")
        with open(self.env_file, "w", encoding="utf-8") as handle:
            handle.write("DATABASE_URL=postgres://double/aer_connector\nSESSION_SECRET=never-read-by-the-script\n")
        self.log = os.path.join(self.tmp, "psql.log")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_seat(self, customer_id, customer_row=None, live_rows="", seated_row=None, price=None, extra_env=None, env_lines=None):
        env = dict(os.environ, PATH=os.path.join(self.tmp, "bin") + os.pathsep + os.environ.get("PATH", ""),
                   HARNESS_SEAT_BOX="local", HARNESS_SEAT_ENV=self.env_file, FAKE_PSQL_LOG=self.log, FAKE_CUSTOMER_ID=customer_id,
                   FAKE_CUSTOMER_ROW=customer_row or "", FAKE_LIVE_ROWS=live_rows, FAKE_SEATED_ROW=seated_row or "")
        if price is not None:
            with open(self.env_file, "a", encoding="utf-8") as handle:
                handle.write("CONNECTOR_PRICE_SOLO_MONTHLY_CENTS=%s\n" % price)
        if env_lines:
            with open(self.env_file, "a", encoding="utf-8") as handle:
                handle.write("".join(line + "\n" for line in env_lines))
        env.update(extra_env or {})
        done = subprocess.run(["bash", SEAT_SCRIPT, customer_id], capture_output=True, text=True, env=env, cwd=ROOT)
        log = ""
        if os.path.exists(self.log):
            with open(self.log, encoding="utf-8") as handle:
                log = handle.read()
        return done, log

    def run_psql(self, args, stdin="", variables=()):
        """The psql double itself, so its own strictness is proven: a variable in a -c string is a syntax error, standard input interpolates."""
        argv = [self.psql]
        for name, value in variables:
            argv += ["-v", "%s=%s" % (name, value)]
        env = dict(os.environ, FAKE_PSQL_LOG=self.log, FAKE_CUSTOMER_ID=CUSTOMER_ID, FAKE_CUSTOMER_ROW="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID)
        return subprocess.run(argv + list(args), input=stdin, capture_output=True, text=True, env=env)

    @staticmethod
    def raw_and_interpolated(log):
        raw = [line[len("SQL-RAW "):] for line in log.split("\nARGS ") if False] or []
        entries = [chunk for chunk in ("\n" + log).split("\nARGS ")[1:]]
        raws, cooked = [], []
        for entry in entries:
            if "\nSQL-RAW " in entry:
                raws.append(entry.split("\nSQL-RAW ", 1)[1].split("\nSQL ", 1)[0])
            if "\nSQL " in entry:
                cooked.append(entry.split("\nSQL ", 1)[1])
        return raws, cooked

    def test_the_psql_double_is_as_strict_as_psql_about_variables(self):
        refused = self.run_psql(["-c", "SELECT id, email FROM customers WHERE id = :'customer_id'::uuid"], variables=[("customer_id", CUSTOMER_ID)])
        self.assertEqual(refused.returncode, 1, "a -c string is sent verbatim: the variable reference is a syntax error at the server")
        self.assertIn('syntax error at or near ":"', refused.stderr)
        self.assertEqual(refused.stdout, "")
        answered = self.run_psql(["-At"], stdin="SELECT id, email FROM customers WHERE id = :'customer_id'::uuid;\n", variables=[("customer_id", CUSTOMER_ID)])
        self.assertEqual(answered.returncode, 0, answered.stderr)
        self.assertEqual(answered.stdout.strip(), "%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, "standard input goes through the lexer")
        unset = self.run_psql(["-At"], stdin="SELECT :'customer_id';\n")
        self.assertEqual(unset.returncode, 1, "a variable never passed is left as written, and the server refuses it")

    def test_an_id_that_is_not_a_uuid_is_refused_before_psql_is_asked(self):
        done, log = self.run_seat("harness+alpha@aeredium.io")
        self.assertEqual(done.returncode, 2)
        self.assertIn("refused: harness+alpha@aeredium.io is not a customer id (a lower-case UUID); nothing was written", done.stderr)
        self.assertEqual(log, "", "psql was never asked: a seat is by id, never by email")

    def test_an_email_outside_the_form_is_refused_and_nothing_is_written(self):
        done, log = self.run_seat(CUSTOMER_ID, customer_row="%s\tsomebody@example.com" % CUSTOMER_ID)
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertIn("refused: customer %s is not the harness's own: its email is not of the form harness+<tester>@aeredium.io; nothing was written" % CUSTOMER_ID, done.stderr)
        self.assertNotIn("INSERT", log)
        self.assertNotIn("UPDATE", log)
        raws, cooked = self.raw_and_interpolated(log)
        self.assertIn("SELECT id, email FROM customers WHERE id = :'customer_id'::uuid", raws[0], "read by id, as a psql variable, on standard input")
        self.assertIn("WHERE id = '%s'::uuid" % CUSTOMER_ID, cooked[0], "which the lexer interpolated")
        self.assertNotIn("CMD ", log, "no -c string anywhere: psql interpolates nothing in one")
        self.assertIn("-v customer_id=%s" % CUSTOMER_ID, log)
        for near_miss in ("harness+alpha@example.com", "harness+Alpha@aeredium.io", "harness@aeredium.io", "xharness+alpha@aeredium.io"):
            done, _ = self.run_seat(CUSTOMER_ID, customer_row="%s\t%s" % (CUSTOMER_ID, near_miss))
            self.assertEqual(done.returncode, 3, near_miss)

    def test_a_missing_customer_is_refused(self):
        done, log = self.run_seat(CUSTOMER_ID, customer_row="")
        self.assertEqual(done.returncode, 3)
        self.assertIn("refused: no customer holds the id %s; nothing was written" % CUSTOMER_ID, done.stderr)
        self.assertNotIn("INSERT", log)

    def test_an_active_paid_row_and_a_second_live_row_are_refused_and_nothing_is_written(self):
        done, log = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, live_rows="%s\tactive" % CUSTOMER_ID)
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertIn("holds an active (paid) subscription; this script never writes state active and never touches a paid row; nothing was written", done.stderr)
        self.assertNotIn("INSERT", log)
        done, log = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, live_rows="id-1\ttrialing\\nid-2\tpending")
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertIn("holds 2 live subscription rows; subscriptions_one_live admits one, and this script writes no second; nothing was written", done.stderr)
        self.assertNotIn("INSERT", log)

    def test_the_seat_is_the_webhooks_solo_trial_written_through_psql_variables_and_printed(self):
        seated = "%s\tsolo\tmonthly\ttrialing\t4900\t2026-10-29 06:00:00 UTC" % CUSTOMER_ID
        done, log = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, live_rows="", seated_row=seated)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), "seated customer %s: package solo, plan monthly, state trialing, price 4900 cents; period end 2026-10-29 06:00:00 UTC" % CUSTOMER_ID)
        raws, cooked = self.raw_and_interpolated(log)
        self.assertEqual(len(raws), 3, "the customer read, the live-rows read, the write: three roads, all on standard input")
        self.assertNotIn("CMD ", log)
        sql = raws[2]
        self.assertIn("WHERE customer_id = '%s'::uuid AND state IN ('pending', 'trialing', 'active')" % CUSTOMER_ID, cooked[1], "the live-rows read, interpolated")
        self.assertIn("VALUES ('%s'::uuid, 'monthly', 'solo', 'trialing', '4900'::int," % CUSTOMER_ID, cooked[2], "the write, interpolated")
        self.assertIn("INSERT INTO subscriptions (customer_id, plan, package, state, price_cents, current_period_end)", sql)
        self.assertIn("VALUES (:'customer_id'::uuid, 'monthly', 'solo', 'trialing', :'price_cents'::int,", sql)
        self.assertIn("now() + (:'trial_days'::int + :'grace_days'::int) * interval '1 day'", sql)
        self.assertIn("ON CONFLICT (customer_id) WHERE state IN ('pending', 'trialing', 'active')", sql, "the one live row, subscriptions_one_live")
        self.assertIn("WHERE subscriptions.state <> 'active'", sql, "an active row is never touched")
        self.assertIn("'subscription_trial_started', 0,", sql, "the zero-cent line the webhook writes")
        self.assertIn("'harness:' || :'customer_id' || ':' || to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD')", sql, "idempotency key harness:<customer-id>:<date>")
        self.assertIn("ON CONFLICT (idempotency_key) DO NOTHING", sql)
        self.assertNotIn(CUSTOMER_ID, sql, "the id travels as a variable, never interpolated into SQL")
        self.assertIn("-v customer_id=%s" % CUSTOMER_ID, log)
        self.assertIn("-v price_cents=4900", log)
        self.assertIn("-v trial_days=30", log)
        self.assertIn("-v grace_days=3", log)
        self.assertIn("-v ON_ERROR_STOP=1", log)
        for never in ("state = 'active'", "'active')\nRETURNING", "aap_account_id", "funding_address", "UPDATE agents", "INSERT INTO agents", "checkout_session_id", "external_subscription_id"):
            self.assertNotIn(never, sql, never)
        self.assertNotIn("postgres://double", done.stdout + done.stderr, "DATABASE_URL is never printed")

    def test_the_env_file_is_read_by_key_and_never_sourced(self):
        """A systemd EnvironmentFile is unquoted: a secret with a space or an ampersand is not a line a shell may run."""
        seated = "%s\tsolo\tmonthly\ttrialing\t4900\t2026-10-29 06:00:00 UTC" % CUSTOMER_ID
        with open(self.env_file, "w", encoding="utf-8") as handle:
            handle.write('SESSION_SECRET=a secret with spaces & an ampersand; and a semicolon\nMASTER_SEAL_KEY_HEX=$(echo never)\nDATABASE_URL="postgres://double/aer_connector"\n')
        done, log = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, seated_row=seated)
        self.assertEqual(done.returncode, 0, done.stderr)
        for fragment in ("ampersand", "with spaces", "never", "command not found", "SESSION_SECRET"):
            self.assertNotIn(fragment, done.stdout + done.stderr, fragment)
        self.assertIn("ARGS postgres://double/aer_connector -X", log, "the quotes a systemd value may carry are stripped")
        done, _ = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, seated_row=seated, price='"59 00"')
        self.assertEqual(done.returncode, 4)
        self.assertIn("fault: CONNECTOR_PRICE_SOLO_MONTHLY_CENTS in", done.stderr)

    def test_the_price_is_the_boxs_own_where_the_box_says_otherwise(self):
        seated = "%s\tsolo\tmonthly\ttrialing\t5900\t2026-10-29 06:00:00 UTC" % CUSTOMER_ID
        done, log = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, seated_row=seated, price=5900)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("-v price_cents=5900", log)
        self.assertIn("price 5900 cents", done.stdout)
        raws, cooked = self.raw_and_interpolated(log)
        self.assertIn("'5900'::int", cooked[2])

    def test_a_write_that_seats_nothing_is_refused(self):
        done, _ = self.run_seat(CUSTOMER_ID, customer_row="%s\tharness+alpha@aeredium.io" % CUSTOMER_ID, seated_row="")
        self.assertEqual(done.returncode, 3)
        self.assertIn("refused: nothing was seated for %s" % CUSTOMER_ID, done.stderr)

    def test_the_script_is_executable_and_names_the_box_and_the_env_file_the_birth_script_uses(self):
        self.assertTrue(os.access(SEAT_SCRIPT, os.X_OK))
        with open(SEAT_SCRIPT, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("ec2-user@3.231.26.5", text)
        self.assertIn("/etc/aer-connector/aer-connector.env", text)
        self.assertIn("'sudo env CUSTOMER_ID='", text.replace('"', "'"))
        body = text.split("BODY=$(cat")[1]
        self.assertNotIn("SESSION_SECRET", body, "the body reads DATABASE_URL and the two figures, nothing else of the box")
        self.assertNotIn("set -a", body, "the unit's environment file is never sourced")
        import re as _re
        self.assertIsNone(_re.search(r'PSQL\[@\]\}"[^\n]* -c ', body), "no -c string on a psql call: psql interpolates a variable on standard input only")
        self.assertIn("export LC_ALL=C", body)


class TheScriptIsTheModule(unittest.TestCase):
    """
    Run as a script, corridor_harness.py is `__main__`; without the alias it sets, corridor_consent would import a second copy
    of it, and a HarnessError raised by the harness's own Oauth road inside the consent would escape the consent's catch as a
    traceback. Proven in a subprocess, against the double served over real HTTP on the loopback (the test's port, never the harness's).
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        write_funding(os.path.join(self.home, ".aer360-harness", "harness-holdings", "funding-wallet.json"), FUNDING)
        self.server = None

    def tearDown(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_script(self, double, *args):
        self.server = serve(double)
        path = os.path.join(self.tmp, "harness_run.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"issuer": double.issuer, "testers": {"alpha": {"agents": {"trader": "alpha-trader", "payer": "alpha-payer", "payer_nogas": None},
                                                                       "listed_address": FUNDING, "payer_list_scope": "agent"}}, "chains": {}}, handle)
        env = dict(os.environ, HOME=self.home)
        return subprocess.run([sys.executable, os.path.join(ROOT, "corridor_harness.py"), "--tester", "alpha", "--run-file", path,
                               "--out", os.path.join(self.tmp, "runs")] + list(args), capture_output=True, text=True, env=env, cwd=ROOT, timeout=120)

    def test_an_oauth_roads_own_error_inside_the_consent_is_told_as_a_sentence_and_never_as_a_traceback(self):
        done = self.run_script(ConnectorDouble(seated=True, register_fails=True), "--series", "A")
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        self.assertIn("fault: the connector answered the discovery or the client registration with registration answered 500", done.stdout,
                      "the consent's own catch caught the harness's HarnessError: one module, one class")

    def test_the_command_line_consent_walks_the_road_over_real_http(self):
        done = self.run_script(ConnectorDouble(seated=True), "--consent", "trader")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        self.assertIn("signed up as the harness's own customer", done.stdout)
        self.assertIn("consented alpha-trader as the harness's own customer with its stored passkey", done.stdout)
        self.assertIn("Connected as alpha-trader: alpha-trader (trader.v1)", done.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.home, ".corridor-harness", "alpha-trader.json")))
        self.assertTrue(os.path.exists(os.path.join(self.home, ".corridor-harness", "alpha", "passkey.json")))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".corridor-harness", "alpha", "passkey.json.tmp")), "written whole, then moved over")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S5WritesTheFundingWalletFile(unittest.TestCase):
    """Spec T21 §5: S5 of the estate harness writes ~/.aer360-harness/harness-holdings/funding-wallet.json, and nothing else changes."""

    @classmethod
    def setUpClass(cls):
        from tests.test_aer360_double import EstateDouble, runner_on
        cls.tmp = tempfile.mkdtemp()
        cls.double = EstateDouble()
        cls.runner = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        cls.outcomes = {o.station: o for o in cls.runner.run()}
        cls.path = os.path.join(cls.tmp, "store", "harness-holdings", "funding-wallet.json")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_file_carries_the_address_the_chain_the_key_and_the_moment_mode_600(self):
        self.assertEqual(self.outcomes["S5"].outcome, H360.PASS, self.outcomes["S5"].line)
        self.assertTrue(os.path.exists(self.path), self.path)
        self.assertEqual(mode_of(self.path), "0o600")
        with open(self.path, encoding="utf-8") as handle:
            written = json.load(handle)
        wallet = self.double.funding_wallet_view()
        self.assertEqual(sorted(written), ["address", "chain", "keyId", "readAt"])
        self.assertEqual(written["address"], wallet["address"])
        self.assertEqual(written["keyId"], wallet["keyId"])
        self.assertEqual(written["chain"], "double-stack-1", "the estate's homeStack, under the spec's word for it")
        self.assertRegex(written["readAt"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertIn("written down at %s for the corridor harness (Spec T21)" % self.path, self.outcomes["S5"].line)
        self.assertEqual(self.runner.funding_wallet_file(), self.path)
        self.assertNotIn("pem", json.dumps(written).lower(), "no key of any wallet in a file")

    def test_the_corridor_harness_reads_it_back_checksummed(self):
        with patched(C, "AER360_STORE_DIR", os.path.join(self.tmp, "store")):
            self.assertEqual(C.funding_wallet_address(), h.checksum_address(self.double.funding_wallet_view()["address"]))


if __name__ == "__main__":
    unittest.main()
