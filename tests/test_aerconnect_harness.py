"""
Pathfinder, the AER Connect owner harness (Spec H-PATHFINDER, 2 October 2026), against a double of the connector, its two
doors and Arbitrum's JSON-RPC (tests/pathfinder_double.py, built on the T21 double, its passkey ceremonies verified for
real). Standard library only, and no network: every road answers through corridor_harness.http_request, patched.

What the spec asks the tests to prove, each below:
  the dry walk prints every station and every call, green, with no network;
  the test-ring guard: every state-creating station refuses a base that is not a declared test ring without --i-mean-it,
    in one sentence, and runs with it;
  the owner is born once, and a second run signs the same owner in rather than creating a second;
  the teardown: a completed run and an early-stopped run each remove the agent they created and revoke its connection,
    and never touch the owner;
  the redaction: no passkey material, bearer or credential appears whole in the report;
  resume with --from S8;
  the pinned catalogue (tables.py's seventeen, Spec T25) against a tools/list double returning them by name.
(The lexicon mirror is tests/test_aerconnect_lexicon.py.)
"""
import contextlib
import datetime
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_harness as E  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as ET  # noqa: E402
import aerconnect_harness as P  # noqa: E402
import corridor_consent as C  # noqa: E402
import corridor_harness as H  # noqa: E402
import tables as T  # noqa: E402
from tests.test_aer360_double import EstateDouble, runner_on  # noqa: E402  (the estate Harness Holdings pays from, Spec T23)

try:
    from .pathfinder_double import ISSUER, PathfinderDouble
except ImportError:  # run as a top-level module by `unittest discover tests`
    from pathfinder_double import ISSUER, PathfinderDouble

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
TOOLS_LIST = os.path.join(FIXTURES, "aerconnect-tools-list.json")
DRY_WALK = os.path.join(FIXTURES, "aerconnect-dry-walk.txt")
FUNDING = H.checksum_address("0x8bc9" + "a1" * 16 + "4949")
GUARDED_ROUTES = (("POST", "/v1/auth/signup/options"), ("POST", "/v1/auth/signup/verify"), ("GET", "/v1/account/agents/new"),
                  ("POST", "/v1/account/agents"), ("POST", "/v1/account/gas"), ("GET", "/authorize"))


def pinned():
    """The pinned catalogue as the fixture carries it: the names tools/list answers, in the pinned order."""
    with open(TOOLS_LIST, "r", encoding="utf-8") as handle:
        return [tool["name"] for tool in json.load(handle)["result"]["tools"]]


def standing_estate(tmp, **double_kwargs):
    """
    Harness Holdings and Harness Treasury as the estate harness leaves them (Spec T23 §5: the estate's people and roads come from where
    they already are): one full run of the estate harness against their double (tests/test_aer360_double.py) — the people enrolled, their
    passkeys stored under <store>/harness-holdings/ and harness-treasury/, admin.env filed, the charters compiled, the funding wallets born,
    the Treasury's float born and T14's three payments made. Holdings is born holding US$50.00 (`holdings_usdc_cents`, the double's word for
    the USDC Bear funds a wallet with), so after the three payments it holds US$31.76 and pays the agents' wallets from that; the Treasury
    holds its US$100.00. Answers the double and the store.
    """
    double_kwargs.setdefault("holdings_usdc_cents", 5000)
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tmp, invite=double.mint_founder_link())
    outcomes = {o.station: o for o in runner.run()}
    assert outcomes["S7"].outcome == E.PASS, outcomes["S7"].line
    return double, runner.store_dir


class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.t += seconds


class NoNetwork:
    def __call__(self, *args, **kwargs):
        raise AssertionError("the dry walk reached the network: %r" % (args[:2],))


class TheDryWalk(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._http = H.http_request
        H.http_request = NoNetwork()

    def tearDown(self):
        H.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_it_prints_every_station_and_every_call_in_order_with_no_network(self):
        lines = P.dry_lines(base="https://sandbox.example", store_dir=self.tmp, test_rings=["https://sandbox.example"])
        heads = [line for line in lines if re.match(r"^S\d+a? [A-Z]", line)]
        self.assertEqual([h.split(" ", 1)[0] for h in heads], P.STATION_IDS, "the twelve stations, the commission check and the teardown, in order")
        for station, title in P.STATIONS:
            self.assertTrue(any(h.startswith("%s %s — " % (station, title)) for h in heads), station)
            self.assertTrue(any(line.startswith("%s — " % station) for line in lines), "%s prints its calls" % station)
        self.assertNotIn("refused", " ".join(heads), "on a declared test ring the guard refuses nothing")
        default = [line for line in P.dry_lines(store_dir=self.tmp) if re.match(r"^S\d+a? [A-Z]", line)]
        self.assertEqual(sum("[guard: refused — " in h for h in default), len(P.GUARDED), "the customer connector is no test ring")

    def test_the_walk_is_the_frozen_one(self):
        lines = [line.replace(self.tmp, "<store>") for line in P.dry_lines(store_dir=self.tmp)]
        with open(DRY_WALK, "r", encoding="utf-8") as handle:
            self.assertEqual(lines, handle.read().splitlines())

    def test_main_prints_the_walk_and_says_nothing_was_sent(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = P.main(["--dry", "--store", self.tmp])
        printed = out.getvalue().splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(printed[-1], "Dry walk: nothing was sent.")
        self.assertEqual(printed[:-1], P.dry_lines(store_dir=self.tmp))
        self.assertEqual(os.listdir(self.tmp), [], "the dry walk writes nothing")

    def test_a_stored_owner_walks_the_sign_in_and_never_the_sign_up(self):
        os.makedirs(os.path.join(self.tmp, "pathfinder"))
        with open(os.path.join(self.tmp, "pathfinder", C.PASSKEY_FILE), "w") as handle:
            handle.write("{}")
        s1 = [line for line in P.dry_lines(store_dir=self.tmp) if line.startswith("S1 — ")]
        self.assertTrue(any(C.SIGNIN_VERIFY in line for line in s1))
        self.assertFalse(any(C.SIGNUP_OPTIONS in line for line in s1))

    def test_it_names_each_doors_own_fields(self):
        lines = P.dry_lines(store_dir=self.tmp)
        check = next(line for line in lines if "tools/call police.check_action" in line)
        build = next(line for line in lines if "tools/call wallet.build_transaction" in line)
        self.assertIn('"amount_usd_cents": 10', check, "MCP Police takes cents")
        self.assertIn('"asset_symbol": "USDC"', check)
        self.assertIn('"child_wallet_id"', check)
        self.assertIn('"amount_usd": 0.1', build, "the MCP Wallet takes dollars")
        self.assertIn('"police_receipt": "<receipt>"', build)

    def test_on_a_base_that_is_not_a_test_ring_it_says_what_the_guard_refuses(self):
        heads = [line for line in P.dry_lines(base="https://connect.example", store_dir=self.tmp) if re.match(r"^S\d+a? [A-Z]", line)]
        for station in P.GUARDED:
            head = next(h for h in heads if h.startswith(station + " "))
            self.assertIn("[guard: refused — %s]" % P.guard_sentence("https://connect.example", station), head)
        with_it = [line for line in P.dry_lines(base="https://connect.example", store_dir=self.tmp, i_mean_it=True) if re.match(r"^S3 ", line)]
        self.assertIn("[guard: --i-mean-it; it runs]", with_it[0])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class PathfinderBase(unittest.TestCase):
    options = {"account_group": "group-100"}

    @classmethod
    def setUpClass(cls):
        # Spec T23: the estate the owner's money is in stands before any run, once per class; every walk below pays its agent's wallet from it
        cls.estate_tmp = tempfile.mkdtemp()
        cls.estate_double, cls.estate_store = standing_estate(cls.estate_tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.estate_tmp, ignore_errors=True)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = os.path.join(self.tmp, "store")
        self.out = os.path.join(self.tmp, "out")
        self.funding = os.path.join(self.tmp, "funding-wallet.json")
        with open(self.funding, "w", encoding="utf-8") as handle:
            json.dump({"address": FUNDING, "chain": "arbitrum", "keyId": "key-1"}, handle)
        # the child wallet's USDC lives on the estate's chain: what Holdings pays through the estate's road is what the Wallet door reads
        self.double = PathfinderDouble(estate_chain=self.estate_double.chain, **self.options)
        self._http = H.http_request
        H.http_request = self.double
        self.said = []
        self.clock = FakeClock()
        self.runs = 0

    def tearDown(self):
        H.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def runner(self, rings=(ISSUER,), base=ISSUER, **kwargs):
        self.runs += 1
        started = datetime.datetime(2026, 10, 2, 3, 0, self.runs, tzinfo=datetime.timezone.utc)
        kwargs.setdefault("estate_base", self.estate_double.base)
        kwargs.setdefault("estate_store", self.estate_store)
        kwargs.setdefault("estate_transport", self.estate_double)
        return P.Pathfinder(base=base, owner="alpha", store_dir=self.store, out_dir=self.out, test_rings=rings, funding_wallet=self.funding,
                            say=self.said.append, sleep=self.clock.sleep, clock=self.clock.now, started_at=started, **kwargs)

    def holdings_and_treasury_hold(self, holdings_minor, treasury_minor):
        """Harness Holdings' and Harness Treasury's USDC on the estate's chain set for one test, and put back after it."""
        chain = self.estate_double.chain
        addresses = (self.estate_double.source_account.lower(), self.estate_double.treasury.source_account.lower())
        kept = {a: chain.balance_of(a) for a in addresses}
        self.addCleanup(chain.balances.update, kept)
        chain.balances[addresses[0]] = holdings_minor
        chain.balances[addresses[1]] = treasury_minor

    def walk(self, **kwargs):
        runner = self.runner(**kwargs)
        runner.run()
        return runner

    @staticmethod
    def words(runner):
        return {o.station: o.outcome for o in runner.outcomes}

    @staticmethod
    def line_of(runner, station):
        return runner.outcome_of(station).line

    def reached(self, method, path):
        return any(m == method and p == path for m, p, _ in self.double.calls)

    def agent_of(self, runner):
        return next(a for a in self.double.agents if a["id"] == runner.facts["agent_id"])


class AWholeWalk(PathfinderBase):
    def test_a_to_z_every_station_passes_and_the_exit_is_zero(self):
        runner = self.walk()
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertEqual(P.exit_code_of(runner.outcomes), 0)
        agent = self.agent_of(runner)
        self.assertEqual(agent["name"], runner.label)
        self.assertEqual(agent["roleId"], "trader.v1")
        # the questionnaire the server returned became the pact: its starting answers, the owner's two budgets, the trade's chain first
        scope = agent["document"]["scope"]
        self.assertEqual(scope["chains"], ["arbitrum", "base", "ethereum"])
        self.assertEqual(scope["counterparties_allowed"], [T.address(k) for k in T.TRADER_LIST_B3])
        self.assertEqual(scope["counterparties_whitelist_scope"], "agent")
        self.assertEqual(scope["assets_allowed"], ["USDC", "USDT", "WETH"])
        self.assertEqual(agent["document"]["budgets"], {"per_tx_cap_usd": 20.0, "daily_cap_usd": 100.0})
        self.assertEqual(agent["document"]["approvals"], {"human_approval_threshold_usd": 10.0})
        self.assertEqual(agent["document"]["velocity"], {"max_tx_per_day": 50})
        # the trade: judged by check_action, built with its receipt, submitted, landed, sponsored, read back
        names = [name for name, _ in self.double.tool_calls]
        self.assertLess(names.index("police.check_action"), names.index("wallet.build_transaction"))
        self.assertLess(names.index("wallet.build_transaction"), names.index("wallet.submit_transaction"))
        self.assertIn("sponsored by the paymaster %s" % H.checksum_address(P.PAYMASTER["arbitrum"]), self.line_of(runner, "S11"))
        self.assertIn("within US$0.02 to US$0.02 for gas plus the 10% charge", self.line_of(runner, "S12"))
        self.assertIn("the gas account fell by US$0.03, US$10.00 to US$9.97, which is the debit and the delegation's", self.line_of(runner, "S12"))
        self.assertIn("the balances reconcile: USDC 100000 → 0", self.line_of(runner, "S12"))

    def test_the_step_up_of_s3_is_the_only_one_and_s7_sends_no_agent_press(self):
        """S7 connects the agent S3 created with /finish {agentId}: the consent's /agent press would create a second (routes/consent.ts)."""
        runner = self.walk()
        self.assertEqual([press for press in self.double.presses], [], "no POST /v1/consent/:id/agent")
        self.assertEqual([f["body"] for f in self.double.finishes], [{"agentId": runner.facts["agent_id"]}])
        self.assertEqual(len([a for a in self.double.agents if a["customerId"] == runner.customer.customer_id]), 1, "one agent, one seat")
        self.assertEqual(sum(1 for m, p, _ in self.double.calls if p == C.STEPUP_OPTIONS), 1)

    def test_the_report_and_the_evidence_are_written_outside_the_checkout(self):
        runner = self.walk()
        path = runner.write_report()
        self.assertTrue(path.startswith(self.out))
        with open(path, encoding="utf-8") as handle:
            report = handle.read()
        for station, title in P.STATIONS:
            self.assertIn("| %s %s | pass |" % (station, title), report)
            self.assertIn("## %s — %s" % (station, title), report)
        self.assertIn("## What the teardown removed", report)
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(path), "evidence.jsonl")))
        self.assertIn("   - Expected: 200 with each of the 17 pinned tools present by name (tables.py CATALOGUE)", report)

    def test_main_runs_the_walk_from_the_command_line(self):
        code = P.main(["--base", ISSUER, "--test-ring", ISSUER, "--owner", "alpha", "--store", self.store, "--out", self.out,
                       "--funding-wallet", self.funding, "--estate-base", self.estate_double.base, "--estate-store", self.estate_store],
                      say=self.said.append, sleep=self.clock.sleep, clock=self.clock.now, estate_transport=self.estate_double)
        self.assertEqual(code, 0, "\n".join(self.said))
        self.assertTrue(any(line.startswith("Report: %s" % self.out) for line in self.said))

    def test_it_imports_the_standard_library_and_this_repository_only(self):
        with open(os.path.join(ROOT, "aerconnect_harness.py"), encoding="utf-8") as handle:
            text = handle.read()
        imported = set(re.findall(r"^import ([A-Za-z_][A-Za-z0-9_.]*)", text, re.M)) | set(re.findall(r"^from ([A-Za-z_][A-Za-z0-9_.]*) import", text, re.M))
        self.assertEqual(imported, {"__future__", "argparse", "datetime", "json", "os", "re", "secrets", "sys", "time", "urllib.parse", "typing",
                                    "corridor_harness", "corridor_consent", "series", "tables",
                                    "aer360_answers", "aer360_estate_road", "aer360_harness", "aer360_tables"})


class TheGuard(PathfinderBase):
    def test_the_refusal_is_one_sentence_naming_the_base_the_rings_and_the_word(self):
        sentence = P.guard_sentence("https://Connect.Example/", "S3")
        self.assertEqual(sentence, "https://connect.example is not a declared test ring (a test ring, the sandbox among them, is named with "
                                   "--test-ring), so the harness refuses to create an agent there without --i-mean-it.")
        self.assertEqual(sentence.count(". "), 0, "one sentence")
        for station, does in P.GUARDED.items():
            self.assertIn("refuses to %s there without --i-mean-it." % does, P.guard_sentence("https://x.example", station))

    def test_nothing_is_a_test_ring_unless_it_is_named_one(self):
        """The customer connector the Owner's Guide sends owners to is the default base, and no ring: the sandbox is named with --test-ring."""
        self.assertEqual(P.TEST_RINGS, ())
        self.assertEqual(P.DEFAULT_BASE, "https://mcppro.aeredium.io")
        self.assertFalse(P.is_test_ring(P.DEFAULT_BASE, P.TEST_RINGS))
        self.assertTrue(P.is_test_ring("https://Sandbox.Example/", ("https://sandbox.example",)))
        self.assertFalse(P.is_test_ring("http://sandbox.example", ("https://sandbox.example",)), "another scheme is another base")
        self.assertFalse(P.is_test_ring("https://sandbox.example.evil.test", ("https://sandbox.example",)))
        self.assertTrue(P.is_test_ring(ISSUER + "/", (ISSUER,)))
        self.assertEqual(P.GUARDED, {"S1": "sign up an owner", "S3": "create an agent", "S4": "recall and re-file an agent's policy", "S6": "buy gas",
                                     "S7": "connect Claude", "S11": "trade"})

    def test_no_owner_is_born_on_a_base_that_is_not_a_test_ring(self):
        runner = self.walk(rings=())
        self.assertEqual(runner.outcome_of("S1").outcome, P.GUARDED_OUT)
        self.assertEqual(self.line_of(runner, "S1"), "sign up: %s" % P.guard_sentence(ISSUER, "S1"))
        for station in P.STATION_IDS[1:-1]:
            self.assertIn(runner.outcome_of(station).outcome, (P.NOT_RUN, P.GUARDED_OUT), station)
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)
        self.assertIn("nothing was removed", self.line_of(runner, "S13"))
        self.assertEqual(self.double.customers, {}, "no owner was born")
        self.assertEqual(self.double.calls, [], "nothing was asked at all")
        self.assertEqual(P.exit_code_of(runner.outcomes), 2)

    def test_every_state_creating_station_refuses_and_the_reads_still_run(self):
        born = self.runner()
        born.run_station("S1", "Sign up")  # the owner, born on the test ring
        self.double.calls.clear()
        runner = self.walk(rings=())
        words = self.words(runner)
        for station in ("S3", "S4", "S6", "S7", "S11"):
            self.assertEqual(words[station], P.GUARDED_OUT, station)
            self.assertIn(P.guard_sentence(ISSUER, station), self.line_of(runner, station))
        self.assertEqual(words["S1"], P.PASS, "a stored owner is signed in with; signing in creates no owner")
        self.assertEqual(words["S2"], P.PASS, "a read is never refused")
        for method, path in GUARDED_ROUTES:
            self.assertFalse(self.reached(method, path), "%s %s was asked on a base that is not a test ring" % (method, path))
        self.assertFalse(any(p.startswith("/v1/consent/") for _, p, _ in self.double.calls))
        self.assertEqual(self.double.tool_calls, [])
        self.assertEqual(self.double.agents, [])
        self.assertEqual(self.double.checkouts, [])

    def test_with_i_mean_it_every_state_creating_station_runs(self):
        runner = self.walk(rings=(), i_mean_it=True)
        self.assertEqual(self.words(runner), {s: P.PASS for s in P.STATION_IDS}, [runner.line(o) for o in runner.outcomes])
        self.assertIn("not a declared test ring; --i-mean-it was passed", runner.report())

    def test_the_teardown_is_never_refused(self):
        """A run that created its agent with --i-mean-it is torn down; the teardown removes only what the run made, so no guard stands before it."""
        runner = self.walk(rings=(), i_mean_it=True)
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)
        self.assertEqual(self.double.deleted, [runner.facts["agent_id"]])


class TheOwnerIsBornOnce(PathfinderBase):
    def test_a_second_run_signs_the_same_owner_in_and_creates_no_second(self):
        first = self.walk()
        owner = first.customer.customer_id
        self.assertEqual(len(self.double.customers), 1)
        self.assertEqual(self.double.registrations_verified, 1)
        signups = sum(1 for m, p, _ in self.double.calls if p == C.SIGNUP_VERIFY)
        second = self.walk()
        self.assertEqual(len(self.double.customers), 1, "the owner was not born twice")
        self.assertEqual(self.double.registrations_verified, 1)
        self.assertEqual(sum(1 for m, p, _ in self.double.calls if p == C.SIGNUP_VERIFY), signups)
        self.assertEqual(second.customer.customer_id, owner)
        self.assertIn("signed in with its stored passkey; it was born once and no second owner was created", self.line_of(second, "S1"))
        self.assertEqual(self.words(second)["S2"], P.PASS)
        self.assertNotEqual(first.facts["agent_id"], second.facts["agent_id"], "each run has its own agent")

    def test_the_owner_lives_where_the_corridor_keeps_its_customer(self):
        runner = self.walk()
        folder = os.path.join(self.store, "alpha")
        for name in (C.PASSKEY_FILE, C.CUSTOMER_FILE, P.RUN_FILE, "client.json", "%s.json" % runner.label):
            self.assertEqual(oct(os.stat(os.path.join(folder, name)).st_mode & 0o777), "0o600", name)
        customer = next(iter(self.double.customers.values()))
        self.assertEqual((customer["displayName"], customer["email"], customer["country"]), ("alpha (harness)", "harness+alpha@aeredium.io", "AU"))

    def test_a_customer_file_without_its_passkey_stops_rather_than_bear_a_second_owner(self):
        self.walk()
        os.remove(os.path.join(self.store, "alpha", C.PASSKEY_FILE))
        self.double.calls.clear()
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S1").outcome, P.STOPPED)
        self.assertIn("a sign-up now would be a second owner nobody can remove", self.line_of(runner, "S1"))
        self.assertFalse(self.reached("POST", C.SIGNUP_OPTIONS))
        self.assertEqual(len(self.double.customers), 1)

    def test_an_owner_born_at_another_connector_is_not_signed_in_here(self):
        self.walk()
        self.double.calls.clear()
        runner = self.walk(base="https://other.test", rings=("https://other.test",))
        self.assertEqual(runner.outcome_of("S1").outcome, P.STOPPED)
        self.assertIn("was born at %s, and this run's base is https://other.test: an owner is born once per connector" % ISSUER, self.line_of(runner, "S1"))
        self.assertFalse(any(p.startswith("/v1/auth/") for _, p, _ in self.double.calls))

    def test_the_sign_count_the_file_holds_when_each_assertion_is_judged_is_the_count_sent(self):
        seen = []

        def before_verify(counter):
            with open(os.path.join(self.store, "alpha", C.PASSKEY_FILE), encoding="utf-8") as handle:
                seen.append((counter, json.load(handle)["sign_count"]))

        self.double.before_verify = before_verify
        self.walk()
        self.walk()
        # the first run: the step-up at S3, the sign-in at S7 (S1 enrols, which is no assertion); the second: S1, S3, S7
        self.assertEqual(len(seen), 5, seen)
        self.assertEqual([c for c, f in seen], [f for c, f in seen], "the file is saved before the assertion is sent")
        self.assertEqual(sorted(set(c for c, _ in seen)), [c for c, _ in seen], "every counter is new; none is resent")


class TheTeardown(PathfinderBase):
    def test_a_completed_run_removes_its_connection_and_its_agent_and_never_touches_the_owner(self):
        runner = self.walk()
        agent_id = runner.facts["agent_id"]
        connection_id = runner.facts["connection_id"]
        self.assertEqual(self.double.revoked, [connection_id])
        self.assertEqual(self.double.halted, [agent_id])
        self.assertEqual(self.double.deleted, [agent_id])
        self.assertEqual(self.agent_of(runner)["state"], "deleted")
        removed = runner.removed
        self.assertTrue(removed[0].startswith("this run's connection %s (revoked)" % connection_id), removed)
        self.assertTrue(removed[1].startswith("this run's agent %s halted" % agent_id))
        self.assertTrue(removed[2].startswith("this run's agent %s deleted" % agent_id))
        self.assertIn("dust", removed[2], "the swap's WETH is below what counts as funds, and the delete names it")
        report = runner.report()
        self.assertIn("- this run's connection %s (revoked)" % connection_id, report)
        self.assertIn("- the owner %s was not touched" % runner.customer.customer_id, report)
        # the owner stands, and signs in again
        self.assertEqual(len(self.double.customers), 1)
        state = H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))
        self.assertTrue(state["torn_down"])
        self.assertEqual(self.words(self.walk())["S1"], P.PASS)

    def test_the_teardown_asks_nothing_but_the_three_roads(self):
        runner = self.walk()
        s13 = [step["route"] for step in runner.steps["S13"]]
        posts = [route for route in s13 if route.startswith("POST")]
        self.assertEqual(posts, ["POST " + P.REVOKE_ROUTE % runner.facts["connection_id"], "POST " + P.HALT_ROUTE % runner.facts["agent_id"],
                                 "POST " + P.DELETE_ROUTE % runner.facts["agent_id"]])
        self.assertTrue(all(step["sent"] == {"headers": step["sent"]["headers"], "body": {"reason": P.REASON % runner.run_id}}
                            for step in runner.steps["S13"] if step["route"].startswith("POST")))

    def test_an_early_stopped_run_removes_the_agent_it_created(self):
        """S7 cannot register the OAuth client, so nothing after it runs; the agent S3 created is halted and deleted, and there was no connection."""
        self.double.register_fails = True
        runner = self.walk()
        words = self.words(runner)
        self.assertEqual(words["S7"], P.FAIL)
        self.assertIn("the client registration", self.line_of(runner, "S7"))
        for station in ("S8", "S9", "S10", "S11", "S12", "S12a"):
            self.assertEqual(words[station], P.NOT_RUN, station)
        self.assertEqual(words["S13"], P.PASS)
        self.assertEqual(self.double.revoked, [])
        self.assertEqual(self.double.deleted, [runner.facts["agent_id"]])
        self.assertEqual(len(self.double.customers), 1)

    def test_a_run_stopped_at_the_trade_removes_its_connection_and_its_agent(self):
        self.holdings_and_treasury_hold(0, 0)  # Spec T23: the one stop on the funding road a person must mend — the Treasury's float
        runner = self.walk()
        self.assertEqual(self.words(runner)["S11"], P.STOPPED, self.line_of(runner, "S11"))
        self.assertEqual(self.words(runner)["S12"], P.NOT_RUN)
        self.assertEqual(self.double.revoked, [runner.facts["connection_id"]])
        self.assertEqual(self.double.deleted, [runner.facts["agent_id"]])

    def test_an_interrupted_run_still_tears_down(self):
        self.double.interrupt_on = "tools/list"
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S8").outcome, P.NOT_RUN)
        self.assertIn("interrupted during it", self.line_of(runner, "S8"))
        self.assertIn("interrupted before it", self.line_of(runner, "S9"))
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)
        self.assertEqual(self.double.deleted, [runner.facts["agent_id"]])
        self.assertEqual(len(runner.outcomes), len(P.STATIONS))
        self.assertEqual(len(P.STATIONS), 14)

    def test_a_delete_the_connector_refuses_is_said_in_its_words_and_the_agent_stays_named(self):
        self.double.funds_left = True
        runner = self.walk()
        s13 = runner.outcome_of("S13")
        self.assertEqual(s13.outcome, P.FAIL)
        self.assertIn("NOT removed: this run's agent %s was not deleted — refused: the connector refused the delete at POST /v1/account/agents/:id/delete "
                      "— AGENT_NOT_CONNECTABLE (409): This agent’s wallet still holds 0.05 USDC on arbitrum. Move the funds out before deleting the agent"
                      % runner.facts["agent_id"], s13.line)
        self.assertIn("this run's agent %s halted" % runner.facts["agent_id"], s13.line)
        self.assertEqual(self.double.deleted, [])
        state = H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))
        self.assertFalse(state["torn_down"])
        self.assertEqual(P.exit_code_of(runner.outcomes), 1)


class TheResume(PathfinderBase):
    def interrupted_after_s7(self):
        """A run that died after S7: its agent and its connection stand, and run.json says so."""
        first = self.runner()
        for station, title in P.STATIONS[:7]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        return first

    def test_from_s8_takes_up_the_standing_agent_and_tears_it_down_at_its_end(self):
        first = self.interrupted_after_s7()
        self.double.calls.clear()
        runner = self.walk(start_at="S8")
        words = self.words(runner)
        for station in P.STATION_IDS[:7]:
            self.assertEqual(words[station], P.SKIPPED, station)
            self.assertEqual(self.line_of(runner, station).split(": ", 1)[1], "resumed at S8")
        for station in P.STATION_IDS[7:]:
            self.assertEqual(words[station], P.PASS, runner.line(runner.outcome_of(station)))
        self.assertEqual(runner.facts["agent_id"], first.facts["agent_id"])
        self.assertEqual(runner.label, first.label, "the stored credential of that run's agent opens the session")
        self.assertFalse(self.reached("POST", C.SIGNUP_OPTIONS))
        self.assertFalse(self.reached("POST", "/v1/account/agents"))
        self.assertFalse(self.reached("GET", "/authorize"))
        self.assertTrue(self.reached("POST", C.SIGNIN_VERIFY), "the owner signs in with its stored passkey")
        self.assertEqual(self.double.deleted, [first.facts["agent_id"]])
        self.assertTrue(runner.steps.get("resume"))

    def test_from_s8_with_no_standing_agent_says_so_and_removes_nothing(self):
        self.walk()  # torn down at its end
        self.double.calls.clear()
        self.double.tool_calls.clear()
        runner = self.walk(start_at="S8")
        self.assertEqual(runner.outcome_of("S8").outcome, P.NOT_RUN)
        self.assertEqual(self.line_of(runner, "S8"), "the catalogue: %s" % (P.NO_RESUME_SENTENCE % os.path.join(self.store, "alpha", P.RUN_FILE)))
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)
        self.assertIn("nothing was removed", self.line_of(runner, "S13"))
        self.assertEqual(self.double.tool_calls, [])
        self.assertFalse(any("<" in p for _, p, _ in self.double.calls), "no road is built from a placeholder")

    def test_from_s13_tears_down_an_agent_an_earlier_run_left_standing(self):
        first = self.runner()
        for station, title in P.STATIONS[:3]:
            first.run_station(station, title)
        runner = self.walk(start_at="S13")
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)
        self.assertEqual(self.double.deleted, [first.facts["agent_id"]])
        self.assertEqual(self.double.revoked, [], "it held no connection")

    def test_from_s10_opens_the_session_the_skipped_s8_would_have(self):
        self.interrupted_after_s7()
        runner = self.walk(start_at="S10")
        self.assertEqual([self.words(runner)[s] for s in ("S10", "S11", "S12", "S13")], [P.PASS] * 4, [runner.line(o) for o in runner.outcomes])
        routes = [step["route"] for step in runner.steps["S10"]]
        self.assertEqual(routes[:3], ["MCP initialize", "MCP notifications/initialized", "MCP tools/list"])

    def test_an_interrupt_during_a_resumed_run_keeps_what_it_passed_over_and_still_tears_down(self):
        first = self.interrupted_after_s7()
        self.double.interrupt_on = "initialize"
        runner = self.walk(start_at="S8")
        self.assertEqual([self.words(runner)[s] for s in P.STATION_IDS[:7]], [P.SKIPPED] * 7)
        self.assertIn("interrupted during it", self.line_of(runner, "S8"))
        self.assertIn("interrupted before it", self.line_of(runner, "S12"))
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)
        self.assertEqual(self.double.deleted, [first.facts["agent_id"]])

    def test_a_station_that_is_not_one_is_refused(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out), self.assertRaises(SystemExit):
            P.main(["--from", "S14", "--store", self.store])


class TheCatalogue(PathfinderBase):
    def test_the_seventeen_against_a_tools_list_double_returning_them_by_name(self):
        names = pinned()
        self.assertEqual(len(names), 17)
        self.assertEqual(tuple(names), P.CATALOGUE)
        self.assertEqual(P.CATALOGUE, T.CATALOGUE_NAMES, "the pinned catalogue is tables.py's (Spec T25)")
        self.double.catalogue = names
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S8").outcome, P.PASS)
        self.assertEqual(self.line_of(runner, "S8"), "the catalogue: aer-connect double lists the 17 pinned tools by name — %s" % ", ".join(names))
        self.assertNotIn("S8", runner.findings, "every tool listed is pinned: nothing to find")

    def test_the_seventeen_are_two_connector_nine_wallet_and_six_police(self):
        self.assertEqual([n for n in P.CATALOGUE if "." not in n], ["aerconnect_my_agent", "aerconnect_guide"])
        self.assertEqual(len([n for n in P.CATALOGUE if n.startswith("wallet.")]), 9)
        self.assertIn("wallet.get_crossing", P.CATALOGUE, "the Wallet's Spec 46 tool, published since 13 September 2026")
        self.assertEqual([n for n in P.CATALOGUE if n.startswith("police.")],
                         ["police.list_roles", "police.describe_role", "police.check_action", "police.request_assignment", "police.assignment_status", "police.my_usage"],
                         "the Police's six, in the order src/server.ts registers them")
        self.assertNotIn("police.can_sign", P.CATALOGUE, "no commit of MCP Police registers can_sign; its judgment is check_action")

    def test_a_pinned_tool_missing_fails_naming_it_as_a_fault(self):
        self.double.catalogue = [n for n in pinned() if n != "police.my_usage"]
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S8").outcome, P.FAIL)
        self.assertEqual(runner.outcome_of("S8").cause, P.FAULT)
        self.assertEqual(self.line_of(runner, "S8"), "the catalogue: aer-connect double lists 16 tool(s), and the pinned catalogue of 17 (tables.py) is not all there; "
                                                     "missing: police.my_usage")
        self.assertEqual(runner.outcome_of("S9").outcome, P.PASS, "the session S8 opened carries on")

    def test_a_tool_the_harness_has_not_pinned_is_a_finding_naming_it_and_s8_passes(self):
        """Spec T25 §2: the harness has fallen behind, not the product; the tool is named, never a fail."""
        self.double.catalogue = pinned() + ["wallet.sweep_dust"]
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S8").outcome, P.PASS)
        self.assertEqual(self.line_of(runner, "S8"), "the catalogue: aer-connect double lists the 17 pinned tools by name, and 1 the harness has not pinned (a finding) — %s"
                         % ", ".join(pinned() + ["wallet.sweep_dust"]))
        self.assertEqual(runner.findings["S8"], [P.UNPINNED_FINDING % "wallet.sweep_dust"])
        self.assertEqual(P.exit_code_of(runner.outcomes), 0, "a finding is not a fail")

    def test_s8_notes_the_two_assignment_tools_until_the_owner_rules(self):
        runner = self.walk()
        self.assertEqual(runner.notes["S8"], [P.ASSIGNMENT_NOTE % "police.request_assignment and police.assignment_status"])
        self.assertIn("listed to a paying agent — a product ruling the owner has not yet given", runner.report().split("## S8 — The catalogue", 1)[1].split("## S9", 1)[0])

    def test_a_catalogue_that_answers_with_an_error_is_quoted_and_named(self):
        """The empty catalogue that speaks its cause (AAOI AT1): quoted, named, never a fault of the harness's."""
        double = self.double

        def refusing(headers, payload, _mcp=double.mcp):
            if payload.get("method") == "tools/list":
                return 200, {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32001, "message": "the judge could not vouch for your agent "
                                                                                    "right now: group_not_assigned"}}, {}
            return _mcp(headers, payload)

        double.mcp = refusing
        runner = self.walk()
        line = self.line_of(runner, "S8")
        self.assertEqual(runner.outcome_of("S8").outcome, P.FAIL)
        self.assertIn("tools/list answered no list — ", line)
        self.assertIn("the judge could not vouch for your agent right now: group_not_assigned", line)
        self.assertIn("[group_not_assigned: %s]" % P.LEXICON["group_not_assigned"]["description"], line)
        self.assertNotIn("a fault, not a judgment", line)

    def test_a_refresh_the_connector_refuses_is_told_as_a_refusal(self):
        stop = P.refresh_stop(H.HarnessError('the token endpoint answered 400: {"error": "invalid_grant", "error_description": "this refresh token '
                                             'is not one this server issued, or it has been revoked"}'))
        self.assertEqual(stop.outcome, P.FAIL)
        self.assertTrue(stop.sentence.startswith("refused: the connector's token endpoint refused to refresh the per-connection credential — "))
        self.assertIn("it has been revoked", stop.sentence)
        self.assertTrue(P.refresh_stop(H.HarnessError("the token endpoint answered 500: down")).sentence.startswith("fault: "))
        self.assertTrue(P.refresh_stop(H.HarnessError("the token endpoint answered 400: {\"error\": \"invalid_request\"}")).sentence.startswith("malformed: "))

    def test_the_judgment_is_asked_of_check_action(self):
        self.walk()
        judged = [args for name, args in self.double.tool_calls if name == "police.check_action"]
        self.assertEqual(len(judged), 1)
        self.assertEqual(judged[0]["amount_usd_cents"], P.TRADE_USD_CENTS)
        self.assertEqual(judged[0]["contract_address"], T.address("UNISWAP_V3_ARBITRUM"))
        self.assertNotIn("amount_usd", judged[0], "never a dollar figure to the Police")


class TheStationsSayWhatHappened(PathfinderBase):
    def test_s2_records_a_finding_not_a_fail_where_the_account_states_no_group(self):
        """Spec T25 §1: the connector's account page has never carried the group; its absence is a finding, never a fault."""
        self.double.account_group = None
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S2").outcome, P.PASS)
        self.assertTrue(self.line_of(runner, "S2").endswith("; the page states no signing group — a finding, not a fault"), self.line_of(runner, "S2"))
        self.assertEqual(runner.findings["S2"], ["the account page states no signing group; the Wallet's door and the platform name group-100; a connector spec "
                                                 "should state it on GET /v1/account"])
        self.assertNotIn("could not be read on this road", self.line_of(runner, "S2"))
        self.assertEqual(P.exit_code_of(runner.outcomes), 0)

    def test_s2_names_another_group_and_fails_on_it_as_a_fault(self):
        self.double.account_group = "group-3"
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S2").outcome, P.FAIL)
        self.assertEqual(runner.outcome_of("S2").cause, P.FAULT)
        self.assertIn("the account is assigned group-3, and group-100 was expected", self.line_of(runner, "S2"))

    def test_s3_stops_on_the_seat_with_the_operators_command(self):
        self.double.default_standing = "none"
        runner = self.walk()
        s3 = runner.outcome_of("S3")
        self.assertEqual(s3.outcome, P.STOPPED)
        self.assertIn("the harness is not seated: run tools/harness_seat.sh %s on the box, then rerun" % runner.customer.customer_id, s3.line)
        self.assertIn("SUBSCRIPTION_REQUIRED (402)", s3.line)

    def test_s3_stops_before_any_call_without_the_funding_wallet(self):
        os.remove(self.funding)
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S3").outcome, P.STOPPED)
        self.assertIn(C.NO_WALLET_SENTENCE, self.line_of(runner, "S3"))
        self.assertFalse(self.reached("GET", "/v1/account/agents/new"))

    def test_s6_names_the_floor_then_buys_ten_dollars_and_reads_the_balance(self):
        runner = self.walk()
        gas = [(c[0], c[1]) for c in self.double.account_calls if c[1] == "/v1/account/gas"]
        self.assertEqual(len(gas), 2)
        self.assertEqual([c["amountCents"] for c in self.double.checkouts], [1000], "the floor press opened nothing")
        self.assertIn("US$9.99 refused naming the floor", self.line_of(runner, "S6"))
        floor = runner.steps["S6"][0]
        self.assertEqual(floor["status"], 400)
        self.assertIn("US$9.99 is below the least gas that can be bought at once, which is US$10.00. Nothing was charged.", json.dumps(floor["came_back"], ensure_ascii=False))

    def test_s6_says_a_closed_gas_door_is_the_deployments_setting_in_the_connectors_words(self):
        self.double.door_key = False
        runner = self.walk()
        line = self.line_of(runner, "S6")
        self.assertEqual(runner.outcome_of("S6").outcome, P.FAIL)
        self.assertTrue(line.startswith("buy gas: misconfigured: the connector's deployment lacks AAP_GAS_DOOR_KEY, so it could not answer the gas press "
                                        "below the floor at POST /v1/account/gas — "), line)
        self.assertIn("AAP_UNREACHABLE (503): Buying gas is not open on this door yet. — This deployment holds no AAP_GAS_DOOR_KEY", line)
        self.assertNotIn("could not be reached", line, "a missing setting is not an outage")

    def test_s10_quotes_the_police_first_then_the_lexicon(self):
        self.double.police_verdict = "deny"
        runner = self.walk()
        line = self.line_of(runner, "S10")
        self.assertEqual(runner.outcome_of("S10").outcome, P.FAIL)
        quoted = "PolicyDenied: denied (cause: legacy_limit_zero; the per-payment limit has not been set to more than zero."
        self.assertIn(quoted, line)
        self.assertLess(line.index(quoted), line.index("[PolicyDenied: %s" % P.LEXICON["PolicyDenied"]["description"]))
        self.assertIn("legacy_limit_zero: %s" % P.LEXICON["legacy_limit_zero"]["description"], line)
        self.assertEqual(runner.outcome_of("S11").outcome, P.NOT_RUN)
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)

    def test_s11_waits_for_its_own_payment_to_the_deadline_then_stops_naming_the_set_and_its_state(self):
        """Spec T23 §3: the wait is for the payment the harness made; --funds-wait bounds it; the stop names the set and the state the register last gave it."""
        self.estate_double.settle_after_reads = 10 ** 6  # a chain that never gets there within the wait
        self.addCleanup(setattr, self.estate_double, "settle_after_reads", 0)
        runner = self.walk()
        s11 = runner.outcome_of("S11")
        address = runner.facts["wallet"]["address"]
        set_id = runner.state["estate"]["set_id"]
        self.assertEqual(s11.outcome, P.FAIL)
        self.assertEqual(s11.line, "the trade: " + P.NOT_LANDED_SENTENCE % (address, "arbitrum", "0 minor units of USDC", P.TRADE_RAW, set_id, int(P.TRADE_DEADLINE_SECONDS),
                                                                             "the instruction queued, the run executing"))
        self.assertIn(P.FUNDING_SENTENCE % (address, "arbitrum", set_id, runner.run_id), runner.notes["S11"])
        balances = [name for name, _ in self.double.tool_calls if name == "wallet.get_balances"]
        self.assertGreater(len(balances), 2, "the wallet is read every interval")
        self.assertGreater(len([s for s in runner.steps["S11"] if s["route"] == "GET /v1/sets/%s" % set_id]), E.LANDING_READS, "the run is read again from the register while it is not settled")
        self.assertGreaterEqual(self.clock.t, P.TRADE_DEADLINE_SECONDS)
        self.assertNotIn("wallet.build_transaction", [name for name, _ in self.double.tool_calls])
        self.assertEqual(self.estate_double.sets[set_id]["status"], "executing", "the register still had the run executing when the wait ended")

    def test_s11_trades_the_moment_its_own_payment_lands(self):
        """The register settles the run after the payment road's own bounded reads gave up; until_funded reads it again, judges the landing on the trail, and trades."""
        self.estate_double.settle_after_reads = E.LANDING_READS + 3
        self.addCleanup(setattr, self.estate_double, "settle_after_reads", 0)
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        funded = runner.facts["funded"]
        self.assertTrue(funded["landed"], funded)
        self.assertEqual((funded["status"], funded["set_status"]), ("confirmed", "settled"))
        self.assertIn(P.FUNDED_SENTENCE % (P.TRADE_RAW, funded["tx_hash"]), runner.notes["S11"])
        self.assertGreaterEqual(self.clock.slept.count(P.TRADE_POLL_SECONDS), 3, "the wallet and the register are read every interval until the payment lands")
        self.assertIn("landed (+US$0.10): instruction confirmed, run settled, userOpHash 0x", self.line_of(runner, "S11"))

    def test_s11_follows_the_ticket_until_the_operation_lands(self):
        self.double.lands_later = 2
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        reads = [name for name, _ in self.double.tool_calls if name == "wallet.ticket_status"]
        self.assertGreaterEqual(len(reads), 2)

    def test_a_submit_that_has_not_landed_yet_is_not_a_failure(self):
        """The Wallet answers `success: false` until the operation lands; the harness follows the ticket and lets the chain judge."""
        self.double.lands_later = 1
        runner = self.walk()
        submit = next(step for step in runner.steps["S11"] if step["route"] == "MCP tools/call wallet.submit_transaction")
        self.assertIn('"success": false', json.dumps(submit["came_back"]))
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))

    def test_s11_asks_the_chain_again_where_the_rpc_lags_the_wallet(self):
        self.double.receipt_lag = 2
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        asked = [route for route in (step["route"] for step in runner.steps["S11"]) if route.startswith("eth_getTransactionReceipt")]
        self.assertEqual(len(asked), 3)

    def test_s11_and_s12_say_where_the_operation_did_not_land(self):
        self.double.lands_later = 10 ** 6
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.FAIL)
        self.assertIn("had not landed at the deadline of %d s" % int(P.TRADE_DEADLINE_SECONDS), self.line_of(runner, "S11"))
        self.assertEqual(self.line_of(runner, "S12"), "the reader: %s" % P.NO_LANDING)

    def test_s12_judges_the_debit_at_the_platforms_ten_percent(self):
        self.double.gas_price_wei = 10 ** 9  # a dollar of gas, so the charge is more than its one-cent floor
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S12").outcome, P.PASS, self.line_of(runner, "S12"))
        self.assertIn("the debit: US$1.10", self.line_of(runner, "S12"))

    def test_s12_fails_a_debit_that_is_not_gas_plus_ten_percent(self):
        self.double.gas_price_wei = 10 ** 9
        self.double.margin_bps = 3000
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S12").outcome, P.FAIL)
        self.assertIn("the debit of US$1.30 is outside US$1.08 to US$1.12", self.line_of(runner, "S12"))

    def test_every_step_records_the_route_what_was_sent_what_came_back_the_expectation_and_the_result(self):
        runner = self.walk()
        for station in P.STATION_IDS:
            for step in runner.steps[station]:
                for key in ("route", "sent", "came_back", "expected", "result", "status"):
                    self.assertIn(key, step, (station, step.get("route")))
                self.assertTrue(step["expected"], (station, step["route"]))
        with open(os.path.join(runner.folder.path, "evidence.jsonl"), encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle]
        self.assertEqual(len(lines), sum(len(v) for v in runner.steps.values()))


SWAP_FIXTURE = os.path.join(FIXTURES, "aerconnect-swap-receipt.json")
SOLANA_FIXTURE = os.path.join(FIXTURES, "aerconnect-solana-swap.json")
WALLET = H.checksum_address("0x" + "5e" * 20)


def fixture_swap(wallet=WALLET, drop_fee=False, fee_bps=None, fee_to=None):
    """The fixture swap with its placeholders filled from tables.py and the harness, varied as a test asks."""
    try:
        from .pathfinder_double import ENTRY_POINT, POOL, USDC_ARBITRUM, WETH_ARBITRUM
    except ImportError:
        from pathfinder_double import ENTRY_POINT, POOL, USDC_ARBITRUM, WETH_ARBITRUM
    with open(SWAP_FIXTURE, encoding="utf-8") as handle:
        receipt = json.load(handle)
    names = {"<USDC>": USDC_ARBITRUM, "<WETH>": WETH_ARBITRUM, "<POOL>": POOL, "<ROUTER>": T.address("UNISWAP_V3_ARBITRUM"),
             "<FEE_ADDRESS>": fee_to or T.address("FEE_ADDRESS"), "<WALLET>": wallet, "<ENTRY_POINT>": ENTRY_POINT,
             "<PAYMASTER>": P.PAYMASTER["arbitrum"]}
    hashes = {"<TRANSFER>": H.TRANSFER_TOPIC, "<USER_OPERATION_EVENT>": P.USER_OPERATION_EVENT}
    for log in receipt["logs"]:
        log["address"] = names.get(log["address"], log["address"])
        log["topics"] = [hashes.get(t) or (H.pad_topic(names[t]) if t in names else t) for t in log["topics"]]
        log["transactionHash"], log["blockNumber"] = receipt["transactionHash"], receipt["blockNumber"]
    gross = int(receipt["logs"][1]["data"], 16)
    if fee_bps is not None:
        fee = gross * fee_bps // 10000
        receipt["logs"][2]["data"] = "0x%064x" % fee
        receipt["logs"][3]["data"] = "0x%064x" % (gross - fee)
    if drop_fee:
        del receipt["logs"][2]
        receipt["logs"][2]["data"] = "0x%064x" % gross  # the router pays the wallet the whole output
    return receipt


class TheCommissionOnTheFixtureSwap(unittest.TestCase):
    """S12a's judgment against the fixture swap: corridor_harness.fee_check at tables.py's rate, to tables.py's fee wallet."""

    def judge(self, receipt):
        return P.judge_commission(H.transfers_in(receipt), WALLET, T.address("UNISWAP_V3_ARBITRUM"), T.address("FEE_ADDRESS"))

    def test_a_five_bps_leg_to_the_fee_address_passes(self):
        check = self.judge(fixture_swap())
        self.assertTrue(check["ok"], check)
        self.assertEqual((check["found"], check["expected"], check["gross"], check["bps"]), (20000000000, 20000000000, 40000000000000, T.FEE_BPS))

    def test_a_swap_with_no_fee_leg_fails_and_names_both_figures(self):
        check = self.judge(fixture_swap(drop_fee=True))
        self.assertFalse(check["ok"])
        self.assertEqual((check["found"], check["expected"], check["gross"]), (0, 20000000000, 40000000000000))

    def test_the_wrong_rate_fails(self):
        check = self.judge(fixture_swap(fee_bps=10))
        self.assertFalse(check["ok"])
        self.assertEqual((check["found"], check["expected"]), (40000000000, 20000000000))

    def test_the_wrong_address_fails(self):
        dead = T.address("DEAD_ADDRESS")
        check = self.judge(fixture_swap(fee_to=dead))
        self.assertFalse(check["ok"])
        self.assertEqual(check["legs_to_fee_address"], 0)
        self.assertEqual(check["elsewhere"], [{"to": H.checksum_address(dead), "amount": 20000000000}])
        self.assertEqual(check["expected"], 20000000000)

    def test_the_harness_reads_the_rate_and_the_wallet_from_tables_and_declares_neither(self):
        with open(os.path.join(ROOT, "aerconnect_harness.py"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn(T.address("FEE_ADDRESS").lower()[2:], text.lower(), "the fee wallet is tables.py's alone")
        self.assertIsNone(re.search(r"^\s*[A-Z_]*FEE_(BPS|ADDRESS)\s*=", text, re.M), "no fee figure or wallet is re-declared")
        self.assertIn('T.address("FEE_ADDRESS")', text)
        self.assertIn("T.FEE_BPS", text)
        self.assertIn("H.fee_check(", text)


class TheCommissionOnSolana(unittest.TestCase):
    def test_the_spl_reader_finds_the_fee_wallets_rise_and_fee_check_judges_it(self):
        with open(SOLANA_FIXTURE, encoding="utf-8") as handle:
            transaction = json.load(handle)
        moves = P.spl_transfers_in(transaction)
        self.assertEqual(sorted((m["to"], m["amount"]) for m in moves),
                         [("AgentWa11et1111111111111111111111111111111", 39980), ("TestFeeWa11et11111111111111111111111111111", 20)])
        check = H.fee_check(moves, "TestFeeWa11et11111111111111111111111111111", "AgentWa11et1111111111111111111111111111111", bps=T.FEE_BPS)
        self.assertTrue(check["ok"], check)
        transaction["meta"]["postTokenBalances"][2]["uiTokenAmount"]["amount"] = "540"  # ten basis points
        wrong = H.fee_check(P.spl_transfers_in(transaction), "TestFeeWa11et11111111111111111111111111111", "AgentWa11et1111111111111111111111111111111",
                            bps=T.FEE_BPS)
        self.assertFalse(wrong["ok"])

    def test_tables_pins_no_solana_fee_address_so_a_solana_trade_is_not_judged(self):
        self.assertNotIn(P.SOLANA_FEE_KEY, T.PINNED)
        self.assertEqual(P.chain_family("solana"), "solana")
        self.assertEqual(P.chain_family("arbitrum"), "evm")


class TheCommissionCheck(PathfinderBase):
    def test_s12a_passes_on_the_walks_swap_and_reads_like_the_corridor(self):
        runner = self.walk()
        line = self.line_of(runner, "S12a")
        self.assertEqual(runner.outcome_of("S12a").outcome, P.PASS, line)
        self.assertTrue(line.startswith("commission 0.00000002 WETH to %s (5 bps) — " % H.short(T.address("FEE_ADDRESS"))), line)
        self.assertIn("the fee address's own incoming Transfer logs at block", line)
        logs = [step for step in runner.steps["S12a"] if step["route"].startswith("eth_getLogs")]
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["sent"]["params"][0]["topics"], [H.TRANSFER_TOPIC, None, H.pad_topic(T.address("FEE_ADDRESS"))])

    def run_s12a_on(self, receipt):
        """S12a alone, against the fixture swap: the receipt S11 would have read, and the chain answering the fee address's logs from it."""
        runner = self.runner()
        self.double.receipts[receipt["transactionHash"]] = receipt
        self.double.block = int(receipt["blockNumber"], 16)
        try:
            from .pathfinder_double import USDC_ARBITRUM, WETH_ARBITRUM
        except ImportError:
            from pathfinder_double import USDC_ARBITRUM, WETH_ARBITRUM
        runner.facts.update(receipt_tx=receipt, event=P.user_operation_events(receipt)[0], wallet={"address": WALLET},
                            before={"usdc_contract": USDC_ARBITRUM, "weth_contract": WETH_ARBITRUM})
        return runner.run_station("S12a", "The commission check")

    def test_s12a_passes_against_the_fixture_swap(self):
        outcome = self.run_s12a_on(fixture_swap())
        self.assertEqual(outcome.outcome, P.PASS, outcome.line)
        self.assertTrue(outcome.line.startswith("commission 0.00000002 WETH to 0xabd0… (5 bps) — 5 bps of the 0.00004 WETH the pool paid the router"), outcome.line)

    def test_s12a_fails_a_fixture_swap_with_no_fee_leg(self):
        outcome = self.run_s12a_on(fixture_swap(drop_fee=True))
        self.assertEqual(outcome.outcome, P.FAIL)
        self.assertEqual(outcome.line, "the commission check: found no transfer to the fee address 0xabd0… in the swap's Transfer logs, where "
                                       "0.00000002 WETH (5 bps of 0.00004 WETH) was expected")

    def test_s12a_fails_a_fixture_swap_at_the_wrong_rate(self):
        outcome = self.run_s12a_on(fixture_swap(fee_bps=10))
        self.assertEqual(outcome.outcome, P.FAIL)
        self.assertEqual(outcome.line, "the commission check: found 0.00000004 WETH to 0xabd0…, and 5 bps of the 0.00004 WETH the pool paid "
                                       "the router is 0.00000002 WETH expected")

    def test_s12a_fails_a_fixture_swap_that_pays_the_fee_address_twice(self):
        receipt = fixture_swap()
        receipt["logs"].insert(3, json.loads(json.dumps(receipt["logs"][2])))
        outcome = self.run_s12a_on(receipt)
        self.assertEqual(outcome.outcome, P.FAIL)
        self.assertEqual(outcome.line, "the commission check: found 2 transfers to 0xabd0… in the swap's Transfer logs, the first of 0.00000002 WETH, "
                                       "where one of 0.00000002 WETH (5 bps of the 0.00004 WETH the pool paid the router) was expected")

    def test_s12a_fails_a_fixture_swap_paid_to_the_wrong_address(self):
        dead = T.address("DEAD_ADDRESS")
        outcome = self.run_s12a_on(fixture_swap(fee_to=dead))
        self.assertEqual(outcome.outcome, P.FAIL)
        self.assertEqual(outcome.line, "the commission check: found 0.00000002 WETH to %s, not to the fee address 0xabd0…, where 0.00000002 WETH "
                                       "(5 bps of 0.00004 WETH) was expected" % H.checksum_address(dead))

    def test_s12a_fails_where_the_fee_addresss_own_logs_do_not_carry_the_leg(self):
        receipt = fixture_swap()
        self.double.receipts[receipt["transactionHash"]] = receipt
        served = json.loads(json.dumps(receipt))
        del served["logs"][2]  # the chain's log index, asked by the fee address's topic, answers no such leg
        runner = self.runner()
        self.double.receipts = {receipt["transactionHash"]: served}
        self.double.block = int(receipt["blockNumber"], 16)
        try:
            from .pathfinder_double import USDC_ARBITRUM, WETH_ARBITRUM
        except ImportError:
            from pathfinder_double import USDC_ARBITRUM, WETH_ARBITRUM
        runner.facts.update(receipt_tx=receipt, event=P.user_operation_events(receipt)[0], wallet={"address": WALLET},
                            before={"usdc_contract": USDC_ARBITRUM, "weth_contract": WETH_ARBITRUM})
        outcome = runner.run_station("S12a", "The commission check")
        self.assertEqual(outcome.outcome, P.FAIL)
        self.assertIn("the fee address's own incoming Transfer logs at block %d carry no such leg in that transaction" % int(receipt["blockNumber"], 16), outcome.line)

    def test_s12a_fails_through_the_double_when_the_venue_takes_no_commission(self):
        self.double.fee_leg = False
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S12a").outcome, P.FAIL)
        self.assertIn("found no transfer to the fee address 0xabd0…", self.line_of(runner, "S12a"))
        self.assertEqual(runner.outcome_of("S12").outcome, P.PASS, "the reader's own judgments are not the commission's")

    def test_s12a_fails_through_the_double_at_the_wrong_rate_or_address(self):
        self.double.fee_bps = 10
        self.assertIn("found 0.00000004 WETH to 0xabd0…", self.line_of(self.walk(), "S12a"))
        self.double.fee_bps = T.FEE_BPS
        self.double.fee_to = T.address("DEAD_ADDRESS")
        self.assertIn("not to the fee address 0xabd0…", self.line_of(self.walk(), "S12a"))

    def test_a_solana_trade_is_not_judged_without_a_pinned_solana_fee_address(self):
        runner = self.runner()
        runner.facts.update(receipt_tx={"logs": []}, event={"sender": WALLET})
        saved = P.TRADE["chain"]
        P.TRADE["chain"] = "solana"
        try:
            outcome = runner.run_station("S12a", "The commission check")
        finally:
            P.TRADE["chain"] = saved
        self.assertEqual(outcome.outcome, P.STOPPED)
        self.assertEqual(outcome.line, "the commission check: " + P.NO_SOLANA_FEE_SENTENCE % (P.SOLANA_FEE_KEY, "solana"))

    def test_nothing_the_harness_sends_a_customer_facing_surface_carries_the_fee_rate_or_wallet(self):
        """The A6 discretion rule: the rate and the fee wallet reach the operator's terminal and report only; no request names them."""
        runner = self.walk()
        fee = T.address("FEE_ADDRESS").lower()[2:]
        for station, steps in runner.steps.items():
            for step in steps:
                if step["route"].startswith("eth_"):
                    continue  # the chain reads: the public RPC, asked for the fee address's own logs
                sent = json.dumps(step["sent"], ensure_ascii=False).lower()
                self.assertNotIn(fee, sent, (station, step["route"]))
                self.assertNotIn("bps", sent, (station, step["route"]))
                self.assertNotIn("basis point", sent, (station, step["route"]))
        self.assertNotIn(fee, "\n".join(self.said).lower(), "the terminal prints the fee wallet shortened, never whole")


class NothingIsCreatedWithoutTheWord(PathfinderBase):
    def test_a_run_with_no_flag_creates_nothing_on_the_customer_connector(self):
        runner = self.walk(base=P.DEFAULT_BASE, rings=())
        self.assertEqual(runner.outcome_of("S1").outcome, P.GUARDED_OUT)
        self.assertEqual(self.line_of(runner, "S1"), "sign up: " + P.guard_sentence(P.DEFAULT_BASE, "S1"))
        self.assertEqual(self.double.customers, {})
        self.assertEqual(self.double.calls, [])

    def test_the_command_line_with_no_base_refuses_every_state_creating_station(self):
        code = P.main(["--owner", "alpha", "--store", self.store, "--out", self.out, "--funding-wallet", self.funding],
                      say=self.said.append, sleep=self.clock.sleep, clock=self.clock.now)
        self.assertEqual(code, 2)
        self.assertTrue(any("S1 — refused by the guard — sign up: https://mcppro.aeredium.io is not a declared test ring" in line for line in self.said))
        self.assertEqual(self.double.customers, {})


class EveryAgentARunCreatesIsRemoved(PathfinderBase):
    def interrupted_after_s7(self):
        first = self.runner()
        for station, title in P.STATIONS[:7]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        return first

    def test_s7_never_creates_a_second_agent_where_this_runs_is_not_listed(self):
        """An agent halted with its funds still in it is not listed at step three; S7 says so and presses nothing (the review's scenario)."""
        self.double.funds_left = True
        first = self.walk()
        self.assertEqual(first.outcome_of("S13").outcome, P.FAIL)
        agents = len(self.double.agents)
        runner = self.walk(start_at="S7")
        s7 = runner.outcome_of("S7")
        self.assertEqual(s7.outcome, P.STOPPED)
        self.assertIn("this run's agent %s (%s) is not listed at the consent's step three" % (first.facts["agent_id"], first.label), s7.line)
        self.assertIn("nothing was pressed, since a press naming no standing agent would create another", s7.line)
        self.assertEqual(self.double.presses, [], "no POST /v1/consent/:id/agent")
        self.assertEqual(len(self.double.agents), agents, "no second agent")
        self.assertEqual(runner.outcome_of("S8").outcome, P.NOT_RUN, "a connection carried from run.json does not outlive a failed S7")
        self.assertEqual(self.line_of(runner, "S8"), "the catalogue: " + P.NO_CONNECTION)

    def test_a_run_from_s3_sets_the_standing_agent_aside_and_removes_both(self):
        first = self.interrupted_after_s7()
        runner = self.walk(start_at="S3")
        self.assertNotEqual(runner.facts["agent_id"], first.facts["agent_id"])
        self.assertNotEqual(runner.label, first.label, "this run's agent carries this run's label")
        self.assertEqual(sorted(self.double.deleted), sorted([first.facts["agent_id"], runner.facts["agent_id"]]))
        self.assertIn(first.facts["connection_id"], self.double.revoked)
        self.assertIn("run %s's agent %s deleted" % (first.run_id, first.facts["agent_id"]), self.line_of(runner, "S13"))
        self.assertEqual(H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))["earlier"], [])

    def test_a_fresh_run_removes_what_an_earlier_run_left_standing(self):
        first = self.interrupted_after_s7()
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS, self.line_of(runner, "S13"))
        self.assertEqual(sorted(self.double.deleted), sorted([first.facts["agent_id"], runner.facts["agent_id"]]))
        self.assertTrue(any("was not torn down" in line for line in self.said))

    def test_an_agent_whose_press_answer_was_lost_is_found_by_its_label_and_removed(self):
        self.double.lose_press_answer = True
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S3").outcome, P.FAIL)
        line = self.line_of(runner, "S3")
        self.assertIn("unreachable: the connector could not be reached at POST /v1/account/agents", line)
        self.assertIn("its answer never arrived, so whether the connector carried it out is not known; S13 looks for an agent named %s on "
                      "the account and removes it" % runner.label, line)
        self.assertNotIn("nothing was changed", line, "the connector did create it: the harness says only what it knows")
        self.assertEqual(self.line_of(runner, "S4"), "set the policy: " + P.NO_AGENT, "what this run holds, never that no agent stands")
        created = [a for a in self.double.agents if a["name"] == runner.label]
        self.assertEqual(len(created), 1, "the connector created it; the answer was lost")
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS, self.line_of(runner, "S13"))
        self.assertEqual(self.double.deleted, [created[0]["id"]])

    def test_an_earlier_agent_the_teardown_cannot_remove_stays_on_record(self):
        self.double.funds_left = True
        first = self.walk()
        second = self.walk()
        state = H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))
        self.assertEqual([e["agent"]["id"] for e in state["earlier"]], [first.facts["agent_id"]])
        self.assertIn("not removed by run %s" % second.run_id, state["earlier"][0]["why"])


class AResumeFromEveryStation(PathfinderBase):
    def test_a_run_that_died_after_s11_resumes_from_any_station_and_is_torn_down(self):
        """From every station in turn: nothing escapes as a traceback, every station has its outcome, and what stands is removed."""
        for start in P.STATION_IDS[1:]:
            with self.subTest(start=start):
                self.double.deleted.clear()
                first = self.runner()
                for station, title in P.STATIONS[:11]:
                    outcome = first.run_station(station, title)
                    self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
                runner = self.walk(start_at=start)
                self.assertEqual([o.station for o in runner.outcomes], P.STATION_IDS)
                self.assertEqual(runner.outcome_of("S13").outcome, P.PASS, runner.line(runner.outcome_of("S13")))
                self.assertIn(first.facts["agent_id"], self.double.deleted, "the agent that run left standing is removed")
                for outcome in runner.outcomes:
                    self.assertNotIn("a fault, not a judgment", outcome.line, runner.line(outcome))


class OneConnectorPerOwner(PathfinderBase):
    def test_a_resume_on_another_connector_sends_nothing_there(self):
        EveryAgentARunCreatesIsRemoved.interrupted_after_s7(self)
        self.double.calls.clear()
        runner = self.walk(base="https://other.test", rings=("https://other.test",), start_at="S8")
        self.assertEqual(runner.outcome_of("S8").outcome, P.NOT_RUN)
        self.assertIn("was born at %s, and this run's base is https://other.test" % ISSUER, self.line_of(runner, "S8"))
        self.assertEqual(self.double.calls, [], "no bearer, no assertion and no teardown press went to another connector")
        self.assertEqual(runner.outcome_of("S13").outcome, P.FAIL)
        self.assertIn("nothing was asked of https://other.test", self.line_of(runner, "S13"))

    def test_a_credential_is_never_sent_to_another_connector(self):
        oauth = H.Oauth("https://other.test", self.store)
        H.write_private(oauth.token_path("alpha-trader-x"), {"issuer": ISSUER, "access_token": "at-" + "z" * 20, "expires_at": 9e12})
        session = P.OwnerMcp(oauth, "alpha-trader-x", lambda **line: None, "https://other.test/mcp", [])
        with self.assertRaises(P.StationStop) as stopped:
            session.bearer()
        self.assertIn("a credential is never sent to another connector", stopped.exception.sentence)

    def test_a_5xx_on_the_sign_in_road_is_unreachable_and_never_a_fault_of_the_harness(self):
        runner = self.runner()
        stop = runner.consent_stop(C.ConsentStop("fault: the connector answered the sign-in's options at POST /v1/auth/signin/options with "
                                                 "INTERNAL_ERROR (500): AER Connect failed and did not expect to. Nothing was changed.; nothing of the "
                                                 "harness's was judged", outcome="fault", code="INTERNAL_ERROR", status=500,
                                                 said="INTERNAL_ERROR (500): AER Connect failed and did not expect to. Nothing was changed.",
                                                 route="POST /v1/auth/signin/options"))
        self.assertEqual(stop.sentence, "unreachable: the connector could not answer at POST /v1/auth/signin/options (HTTP 500) — INTERNAL_ERROR (500): "
                                        "AER Connect failed and did not expect to. Nothing was changed. [unclassified]; nothing was judged, and a retry may reach it")

    def test_a_press_whose_answer_never_arrived_is_not_said_to_have_changed_nothing(self):
        lost = "unreachable: the connector could not be reached at %s: %s https://connector.test%s: timed out; nothing was changed, and a retry may reach it"
        finish = "/v1/consent/abc/finish"
        retold = P.press_unreachable(lost % ("POST " + finish, "POST", finish), "POST " + finish)
        self.assertTrue(retold.endswith("timed out; its answer never arrived, so whether the connector carried it out is not known"), retold)
        read = lost % ("GET /v1/account", "GET", "/v1/account")
        self.assertEqual(P.press_unreachable(read, "GET /v1/account"), read, "of a read, nothing was changed is true")
        road = ("unreachable: the connector could not be reached for the discovery or the client registration: POST https://connector.test/register: "
                "timed out; nothing was changed, and a retry may reach it")
        self.assertTrue(P.press_unreachable(road).endswith(P.PRESS_UNREACHABLE_TAIL), "the transport's own words name the method where no route is kept")
        stop = self.runner().consent_stop(C.ConsentStop(lost % ("POST " + finish, "POST", finish), outcome="unreachable", route="POST " + finish))
        self.assertEqual(stop.outcome, P.FAIL)
        self.assertNotIn("nothing was changed", stop.sentence)

    def test_a_refresh_the_harness_could_not_ask_for_is_not_the_endpoints_answer(self):
        stop = P.refresh_stop(H.HarnessError("no refresh token is stored for alpha-trader-x; run --consent trader"))
        self.assertEqual(stop.outcome, P.STOPPED)
        self.assertIn("nothing was asked of the token endpoint", stop.sentence)


class AResumedRunSaysWhatItCannotKnow(PathfinderBase):
    def test_from_s11_says_the_receipt_of_s10_is_not_kept(self):
        EveryAgentARunCreatesIsRemoved.interrupted_after_s7(self)
        runner = self.walk(start_at="S11")
        self.assertEqual(self.line_of(runner, "S11"), "the trade: S10 was passed over by --from S11, and its receipt — single-use, and never "
                                                      "written down — is not kept: resume at S10")
        self.assertEqual(runner.outcome_of("S13").outcome, P.PASS)

    def test_from_s12_reads_the_trade_run_json_keeps(self):
        first = self.runner()
        for station, title in P.STATIONS[:11]:
            outcome = first.run_station(station, title)
            self.assertEqual(outcome.outcome, P.PASS, first.line(outcome))
        runner = self.walk(start_at="S12")
        for station in ("S12", "S12a", "S13"):
            self.assertEqual(runner.outcome_of(station).outcome, P.PASS, runner.line(runner.outcome_of(station)))
        self.assertTrue(self.line_of(runner, "S12a").startswith("commission 0.00000002 WETH to 0xabd0… (5 bps)"))
        self.assertEqual(self.double.deleted, [first.facts["agent_id"]])

    def test_from_s2_a_failed_s7_is_s7s_and_never_that_no_earlier_agent_stands(self):
        """The review's third scenario: --from S2 with nothing standing, S3 creates this run's agent, S7 fails; S8 names S7."""
        born = self.runner()
        self.assertEqual(born.run_station(*P.STATIONS[0]).outcome, P.PASS)
        self.double.register_fails = True
        runner = self.walk(start_at="S2")
        self.assertEqual(runner.outcome_of("S3").outcome, P.PASS, self.line_of(runner, "S3"))
        self.assertEqual(runner.outcome_of("S7").outcome, P.FAIL, self.line_of(runner, "S7"))
        self.assertEqual(self.line_of(runner, "S8"), "the catalogue: " + P.NO_CONNECTION)
        for outcome in runner.outcomes:
            self.assertNotIn("no agent of an earlier run stands", outcome.line, runner.line(outcome))
        self.assertEqual(self.double.deleted, [runner.facts["agent_id"]])

    def test_a_wallet_s9_rejects_is_not_the_wallet_s10_judges(self):
        self.double.my_agent_wallet = "00000000-0000-4000-8000-000000000000"
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S9").outcome, P.FAIL)
        self.assertIn("the wallet is 00000000-0000-4000-8000-000000000000, and S3's agent carries", self.line_of(runner, "S9"))
        judged = [args for name, args in self.double.tool_calls if name == "police.check_action"]
        self.assertEqual(judged[0]["child_wallet_id"], self.agent_of(runner)["walletId"])


class TheTradeRoadSaysWhatHappened(PathfinderBase):
    def test_a_submit_whose_confirmation_timed_out_is_followed_not_refused(self):
        self.double.lands_later = 2
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.PASS, self.line_of(runner, "S11"))
        self.assertTrue(any("the Wallet answered the submit with an error after the operation was sent" in n for n in runner.notes["S11"]))
        self.assertIn("confirmation_timeout", " ".join(runner.notes["S11"]))

    def test_an_rpc_refusal_is_the_rpcs_and_the_hashes_are_kept(self):
        self.double.rpc_error_on = "eth_getTransactionReceipt"
        runner = self.walk()
        line = self.line_of(runner, "S11")
        self.assertEqual(runner.outcome_of("S11").outcome, P.FAIL)
        self.assertIn("refused: the arbitrum RPC at https://arb1.arbitrum.io refused eth_getTransactionReceipt", line)
        self.assertIn("limit exceeded", line)
        self.assertNotIn("a fault, not a judgment", line)
        traded = H.read_json(os.path.join(self.store, "alpha", P.RUN_FILE))["traded"]
        self.assertTrue(traded["handle_ops_tx_hash"] and traded["user_op_hash"], "the Wallet's hashes are written before the chain is read")
        self.assertIn("the Wallet says the operation %s landed in the handleOps transaction %s" % (traded["user_op_hash"], traded["handle_ops_tx_hash"]), line)
        for station in ("S12", "S12a"):
            later = self.line_of(runner, station)
            self.assertEqual(runner.outcome_of(station).outcome, P.FAIL, later)
            self.assertIn("refused: the arbitrum RPC at https://arb1.arbitrum.io refused eth_getTransactionReceipt", later)
            self.assertNotIn(P.NO_LANDING, later, "the Wallet said it landed: the chain's refusal is the cause, and no landing is denied")

    def test_s12_reads_again_the_receipt_the_rpc_refused_s11(self):
        self.double.rpc_error_on, self.double.rpc_error_times = "eth_getTransactionReceipt", 1
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.FAIL)
        self.assertIn("run.json keeps both hashes, and S12 reads the receipt again", self.line_of(runner, "S11"))
        for station in ("S12", "S12a", "S13"):
            self.assertEqual(runner.outcome_of(station).outcome, P.PASS, runner.line(runner.outcome_of(station)))
        self.assertIn("S11 could not read the handleOps receipt; it is read here, by the hash the Wallet named", runner.notes["S12"])
        self.assertTrue(self.line_of(runner, "S12a").startswith("commission 0.00000002 WETH to 0xabd0… (5 bps)"))

    def test_a_trade_s11_never_landed_is_not_read_in_its_place(self):
        """A resumed run whose S10 the Police refuses: S11 trades nothing, and the trade an earlier run left in run.json never stands in."""
        first = self.runner()
        for station, title in P.STATIONS[:11]:
            self.assertEqual(first.run_station(station, title).outcome, P.PASS)
        self.double.police_verdict = "deny"
        runner = self.walk(start_at="S10")
        self.assertNotEqual(runner.outcome_of("S11").outcome, P.PASS)
        for station in ("S12", "S12a"):
            self.assertEqual(self.line_of(runner, station), "%s: %s" % (P.TITLES[station].lower(), P.NO_LANDING))

    def test_the_event_of_another_operation_never_stands_in(self):
        self.double.event_for_another_hash = True
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S11").outcome, P.FAIL)
        self.assertIn("the EntryPoint emitted no UserOperationEvent for this hash in the transaction", self.line_of(runner, "S11"))

    def test_the_gas_is_the_greater_of_the_receipts_cost_and_the_operations_actual_cost(self):
        self.double.gas_price_wei = 10 ** 9
        self.double.actual_gas_factor = 3
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S12").outcome, P.PASS, self.line_of(runner, "S12"))
        self.assertIn("the debit: US$3.30 for 1200000000000000 wei of gas", self.line_of(runner, "S12"))

    def test_s5_says_where_the_wallet_is_not_shown_bound_to_the_owner(self):
        """A connector whose account page names another funding wallet than the one it let S3 register against: S5 says so (the page answers the owner's own at S2 and S3, another from S5 on)."""
        other = H.checksum_address("0x" + "77" * 20)
        self.double.account_funding = other
        self.double.account_funding_after = 2
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S5").outcome, P.FAIL)
        self.assertIn("is not shown bound to the owner: the owner's funding wallet is %s, and S3 minted the agent against %s" % (other, FUNDING),
                      self.line_of(runner, "S5"))

    def test_a_keyed_rpc_url_is_recorded_by_its_host_and_its_key_never_whole(self):
        self.double.rpc_host = "arb-mainnet.example"
        runner = self.walk(rpc_url="https://arb-mainnet.example/v2/SECRETKEY1234567890")
        self.assertEqual(runner.outcome_of("S12a").outcome, P.PASS, self.line_of(runner, "S12a"))
        report = runner.report()
        with open(os.path.join(runner.folder.path, "evidence.jsonl"), encoding="utf-8") as handle:
            evidence = handle.read()
        for text in (report, evidence, "\n".join(self.said)):
            self.assertNotIn("SECRETKEY1234567890", text)
        self.assertIn("eth_getTransactionReceipt https://arb-mainnet.example", evidence)


class TheRedaction(PathfinderBase):
    def test_no_passkey_material_bearer_or_credential_appears_whole_in_the_report_or_the_evidence(self):
        refresh = []
        issue = self.double.issue_tokens

        def recording(connection_id, scopes):
            tokens = issue(connection_id, scopes)
            refresh.append(tokens["refresh_token"])
            return tokens

        self.double.issue_tokens = recording
        runner = self.walk()
        report = runner.report()
        with open(os.path.join(runner.folder.path, "evidence.jsonl"), encoding="utf-8") as handle:
            evidence = handle.read()
        said = "\n".join(self.said)
        with open(os.path.join(self.store, "alpha", C.PASSKEY_FILE), encoding="utf-8") as handle:
            pem = json.load(handle)["pem"]
        secrets = {"the access token": list(self.double.access_tokens), "the refresh token": refresh,
                   "the session cookie": list(self.double.sessions), "the CSRF token": [s["csrf"] for s in self.double.sessions.values()],
                   "the authorization code": [self.double.last_code], "the code verifier": [f["code_verifier"] for f in self.double.token_forms if f.get("code_verifier")],
                   "the sign-up handle": self.double.handles, "a passkey signature": self.double.signatures,
                   "the Police's receipt": list(self.double.issued),
                   "the passkey's private key": [line for line in pem.splitlines() if len(line) >= 16 and "-----" not in line]}
        for what, values in secrets.items():
            self.assertTrue(values, "the walk carried %s" % what)
            for value in values:
                for text, where in ((report, "the report"), (evidence, "the evidence"), (said, "the terminal")):
                    self.assertNotIn(value, text, "%s appears whole in %s" % (what, where))
        bearer = list(self.double.access_tokens)[0]
        self.assertIn(C.last4(bearer), evidence, "the bearer is redacted to its last four characters, not dropped")
        self.assertIn(C.last4(list(self.double.issued)[0]), evidence)

    def test_a_refusals_code_and_sentence_survive_the_redaction(self):
        self.double.door_key = False
        runner = self.walk()
        step = runner.steps["S6"][0]
        self.assertEqual(step["came_back"]["error"]["code"], "AAP_UNREACHABLE")
        self.assertEqual(step["came_back"]["error"]["message"], "Buying gas is not open on this door yet.")


if __name__ == "__main__":
    unittest.main()
