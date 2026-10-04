"""
Spec T25 (4 October 2026): Pathfinder's S2 and S8 read what the connector states today, so that a fail means a fault.

The owner's rule: the harnesses are the gate for re-onboarding "only if the harness is 100%", so a station may fail only on a
fault of the product; an expectation the harness holds that the product never promised is the harness's error. Seven runs of
3 October closed S2 and S8 as fail while the product was right. What the spec asks the tests to prove, each below:

  S2 judges what the connector states: the owner, the seat and the agents as before; a signing group stated on the page and
    other than the run expects fails S2 (a fault); none stated is a finding, never a fail, in the spec's words; --group names
    the group compared, on the command line and in the dry walk; a page the connector cannot answer fails in its own words.
  S8 expects the catalogue the connector publishes, by name: tables.py pins the seventeen, each with the door that answers it
    and the spec that added it; a pinned tool missing fails (a fault); a tool present but not pinned is a finding naming it;
    the two assignment tools are noted on every report until the owner rules (tests/test_aerconnect_harness.py, TheCatalogue).
  The closing table says why a station failed: a cause column, `fault` on every fail row and nothing on any other; a findings
    column and a Findings section, `none` where nothing was found.
  THE GUARD: every station's failure paths, each driven through the double, each a fault of the product in the station's own
    words — and a census of every fail site in the module, none naming `expectation`; the two lines of 3 October gone.
  The dry walk prints the new S2 and S8 words, and the frozen walk carries them.

Standard library only, and no network: every road answers through corridor_harness.http_request, patched to the double.
"""
import ast
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerconnect_harness as P  # noqa: E402
import corridor_consent as C  # noqa: E402
import corridor_harness as H  # noqa: E402
import tables as T  # noqa: E402

try:
    from .pathfinder_double import ISSUER
    from .test_aerconnect_harness import FUNDING, PathfinderBase, pinned
except ImportError:  # run as a top-level module by `unittest discover tests`
    from pathfinder_double import ISSUER
    from test_aerconnect_harness import FUNDING, PathfinderBase, pinned

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(ROOT, "aerconnect_harness.py")
DRY_WALK = os.path.join(ROOT, "tests", "fixtures", "aerconnect-dry-walk.txt")
GROUP_FINDING = P.NO_GROUP_FINDING % ("group-100", "/v1/account")
ASSIGNMENT_NOTE = P.ASSIGNMENT_NOTE % "police.request_assignment and police.assignment_status"
# The connector's own 500, in its own shape (apps/server/src/http.ts INTERNAL_ERROR): what a road it cannot answer says.
INTERNAL_ERROR_SAID = "Something went wrong at our end. Nothing was changed."
# The two lines of 3 October, as the seven reports carried them; neither may be said again.
THE_S2_LINE_OF_3_OCTOBER = "states no assigned signing group on any field, so"
THE_S8_LINE_OF_3_OCTOBER = "the fourteen were expected"


def cannot_answer(double, method, where):
    """The connector answering 500 on one road, in its own INTERNAL_ERROR shape; every other road exactly as before."""
    original = double.route

    def route(m, path, query, headers, payload, follow_redirects):
        if m == method and where(path):
            return 500, {"error": {"code": "INTERNAL_ERROR", "message": INTERNAL_ERROR_SAID, "detail": {}}}, {}
        return original(m, path, query, headers, payload, follow_redirects)

    double.route = route


class TheAccountPage(PathfinderBase):
    """S2 judges what the connector states (Spec T25 §1)."""

    def test_a_stated_group_the_run_expects_passes_with_no_finding(self):
        self.double.account_group = "group-100"
        runner = self.walk()
        self.assertEqual(runner.outcome_of("S2").outcome, P.PASS)
        self.assertTrue(self.line_of(runner, "S2").endswith("; assigned group group-100"), self.line_of(runner, "S2"))
        self.assertNotIn("S2", runner.findings)

    def test_no_stated_group_is_the_specs_finding_and_s2_passes(self):
        self.double.account_group = None
        runner = self.walk()
        s2 = runner.outcome_of("S2")
        self.assertEqual((s2.outcome, s2.cause), (P.PASS, None))
        self.assertTrue(s2.line.endswith("; the page states no signing group — a finding, not a fault"), s2.line)
        self.assertEqual(runner.findings["S2"], ["the account page states no signing group; the Wallet's door and the platform name group-100; "
                                                 "a connector spec should state it on GET /v1/account"])
        self.assertEqual(P.exit_code_of(runner.outcomes), 0, "a finding is not a fail")
        self.assertTrue(any(line == "  S2 finding: %s" % GROUP_FINDING for line in self.said), "said on the terminal as a finding")
        self.assertNotIn(THE_S2_LINE_OF_3_OCTOBER, s2.line)

    def test_a_group_stated_under_any_of_the_specs_three_names_is_read(self):
        self.assertEqual(P.GROUP_KEYS[:3], ("signingGroup", "signing_group", "group"), "the spec's three names first")
        for key in P.GROUP_KEYS:
            self.assertEqual(P.groups_in({"customer": {key: "group-100"}}), ["group-100"], key)
        self.assertEqual(P.groups_in({"customer": {"assignedGroups": ["group-100"]}}), ["group-100"])
        self.assertEqual(P.groups_in({"customer": {"id": "c1"}}), [])

    def test_group_on_the_command_line_names_the_group_s2_compares(self):
        self.double.account_group = "group-3"
        code = P.main(["--base", ISSUER, "--test-ring", ISSUER, "--owner", "alpha", "--store", self.store, "--out", self.out, "--group", "group-3",
                       "--funding-wallet", self.funding, "--estate-base", self.estate_double.base, "--estate-store", self.estate_store],
                      say=self.said.append, sleep=self.clock.sleep, clock=self.clock.now, estate_transport=self.estate_double)
        self.assertEqual(code, 0, "\n".join(self.said))
        self.assertTrue(any(line.startswith("S2 — pass — ") and line.endswith("; assigned group group-3") for line in self.said), "\n".join(self.said))

    def test_without_the_flag_the_group_expected_is_group_100(self):
        self.assertEqual(P.EXPECTED_GROUP, "group-100")
        self.assertEqual(self.runner().expected_group, "group-100")
        runner = self.runner(expected_group="group-3")
        self.assertEqual(runner.expected_group, "group-3")


class TheCatalogueIsPinned(unittest.TestCase):
    """tables.py pins the seventeen by name, each with the spec that added it (Spec T25 §2)."""

    def test_seventeen_names_each_with_a_door_what_it_does_and_where_it_was_read(self):
        self.assertEqual(len(T.CATALOGUE), 17)
        self.assertEqual(len(set(T.CATALOGUE_NAMES)), 17, "no name twice")
        self.assertEqual(T.CATALOGUE_NAMES, P.CATALOGUE, "the harness's catalogue is tables.py's")
        for row in T.CATALOGUE:
            self.assertIn(row.door, ("connector", "wallet", "police"), row.name)
            if row.door == "connector":
                self.assertNotIn(".", row.name, "the connector's own wear no prefix (mcprelay.ts)")
            else:
                self.assertTrue(row.name.startswith(row.door + "."), "%s is listed under its door's prefix" % row.name)
            self.assertTrue(row.what, row.name)
            self.assertTrue(row.source, row.name)
        self.assertEqual([r.door for r in T.CATALOGUE].count("connector"), 2)
        self.assertEqual([r.door for r in T.CATALOGUE].count("wallet"), 9)
        self.assertEqual([r.door for r in T.CATALOGUE].count("police"), 6)

    def test_the_three_added_after_the_fourteen_name_the_spec_that_added_them(self):
        crossing = T.tool("wallet.get_crossing")
        self.assertIn("Spec 46", crossing.source)
        self.assertIn("13 September 2026", crossing.source)
        self.assertIn("internal/mcp/catalog.go", crossing.source)
        self.assertEqual(T.ASSIGNMENT_TOOLS, ("police.request_assignment", "police.assignment_status"))
        for name in T.ASSIGNMENT_TOOLS:
            row = T.tool(name)
            self.assertIn("step four", row.source)
            self.assertIn("src/server.ts", row.source)
            self.assertIn("NOT THE ROAD FOR AN AER CONNECT AGENT", row.source)
            self.assertIn("open since 2 October 2026", row.source)
        self.assertIn("Spec 15", T.tool("aerconnect_my_agent").source)
        self.assertIn("Spec 22", T.tool("aerconnect_guide").source)
        self.assertIn("19 August 2026", T.tool("wallet.wallet_status").source)
        self.assertIn("step two", T.tool("police.check_action").source)

    def test_a_name_that_is_not_pinned_is_a_bug_and_throws(self):
        with self.assertRaises(KeyError):
            T.tool("wallet.sweep_dust")
        self.assertTrue(T.describe_tool("police.check_action").startswith("police.check_action — judges a stated action"))
        self.assertIn("(read from mcp-police src/server.ts", T.describe_tool("police.check_action"))

    def test_the_fixture_is_the_pinned_seventeen_in_the_pinned_order(self):
        self.assertEqual(tuple(pinned()), T.CATALOGUE_NAMES)


class TheClosingTableSaysWhy(PathfinderBase):
    """The table gains a cause column and a findings column; the report a Findings section (Spec T25 §3 and §1)."""

    def test_a_fail_row_reads_fault_a_finding_rides_in_its_column_and_the_section_lists_it(self):
        self.double.account_group = None  # S2: the finding
        self.double.catalogue = pinned() + ["wallet.sweep_dust"]  # S8: a finding
        self.double.police_verdict = "deny"  # S10: a fail, in the Police's own words
        runner = self.walk()
        report = runner.report()
        table = report.split("## The closing table", 1)[1].split("## Findings", 1)[0]
        self.assertIn("| Station | Outcome | Cause | Line | Findings |\n|---|---|---|---|---|", table)
        rows = {line.split(" ")[1]: line for line in table.splitlines() if re.match(r"^\| S\d", line)}
        self.assertEqual(len(rows), len(P.STATIONS))
        self.assertTrue(rows["S10"].startswith("| S10 The judgment | fail | fault | the judgment: "), rows["S10"])
        self.assertTrue(rows["S10"].endswith(" |  |"), "no finding at S10")
        self.assertTrue(rows["S2"].startswith("| S2 The account | pass |  | the account: "), rows["S2"])
        self.assertTrue(rows["S2"].endswith(" | %s |" % GROUP_FINDING), rows["S2"])
        self.assertTrue(rows["S8"].endswith(" | %s |" % (P.UNPINNED_FINDING % "wallet.sweep_dust")), rows["S8"])
        self.assertTrue(rows["S11"].startswith("| S11 The trade | not run |  | "), rows["S11"])
        self.assertIn(P.CAUSE_LEGEND, table)
        findings = report.split("## Findings", 1)[1].split("## What the teardown removed", 1)[0]
        self.assertEqual([line for line in findings.splitlines() if line.startswith("- ")],
                         ["- S2 The account — %s" % GROUP_FINDING, "- S8 The catalogue — %s" % (P.UNPINNED_FINDING % "wallet.sweep_dust")])
        s2 = report.split("## S2 — The account", 1)[1].split("## S3 — ", 1)[0]
        self.assertIn("\nFinding: %s\n" % GROUP_FINDING, s2)
        s8 = report.split("## S8 — The catalogue", 1)[1].split("## S9 — ", 1)[0]
        self.assertIn("\nNote: %s\n" % ASSIGNMENT_NOTE, s8)
        self.assertIn("\nFinding: %s\n" % (P.UNPINNED_FINDING % "wallet.sweep_dust"), s8)
        self.assertEqual(P.exit_code_of(runner.outcomes), 1, "S10's fail")

    def test_where_nothing_was_found_the_section_says_none_and_no_outcome_but_a_fail_has_a_cause(self):
        runner = self.walk()
        report = runner.report()
        self.assertIn("## Findings\n\n- none: no station read anything the owner should know beyond its own line\n", report)
        self.assertEqual(runner.findings, {})
        for outcome in runner.outcomes:
            self.assertEqual(outcome.outcome, P.PASS, outcome.line)
            self.assertIsNone(outcome.cause)
        for line in report.split("## The closing table", 1)[1].split("## Findings", 1)[0].splitlines():
            if re.match(r"^\| S\d", line):
                self.assertIn(" | pass |  | ", line)
                self.assertTrue(line.endswith(" |  |"), line)

    def test_the_cause_is_one_of_two_words_and_fault_is_every_fails_default(self):
        self.assertEqual(P.CAUSES, ("fault", "expectation"))
        self.assertEqual(P.StationStop("x", outcome=P.FAIL).cause, P.FAULT)
        self.assertEqual(P.StationStop("x", outcome=P.FAIL, cause=P.FAULT).cause, P.FAULT)
        for word in (P.STOPPED, P.GUARDED_OUT, P.NOT_RUN, P.SKIPPED):
            self.assertIsNone(P.StationStop("x", outcome=word).cause, word)
        self.assertIsNone(P.Outcome("S1", P.PASS, "x").cause)
        self.assertEqual(P.Outcome("S1", P.FAIL, "x").cause, P.FAULT)
        with self.assertRaises(ValueError):
            P.StationStop("x", outcome=P.FAIL, cause="whim")
        with self.assertRaises(ValueError):
            P.Outcome("S1", P.FAIL, "x", cause="whim")


class TheGuardWalksEveryStationsFailurePaths(PathfinderBase):
    """
    Spec T25 §3, the guard that keeps the owner's rule: a test walks every station's failure paths and asserts each is a fault of
    the product, in the station's own words. Each scenario drives one station to a fail through the double — the product doing,
    saying or refusing something — and reads the station's line: fail, cause fault, the product's own words carried, and the
    closing table's row reading `| fail | fault |`. The stations driven here are the harness's own list: a station added to the
    harness without a scenario here fails the last test.
    """

    def assert_fault(self, runner, station, *product_words):
        outcome = runner.outcome_of(station)
        self.assertEqual(outcome.outcome, P.FAIL, "%s: %s" % (station, outcome.line))
        self.assertEqual(outcome.cause, P.FAULT, outcome.line)
        for words in product_words:
            self.assertIn(words, outcome.line)
        row = next(line for line in runner.report().splitlines() if line.startswith("| %s %s | " % (station, P.TITLES[station])))
        self.assertIn("| fail | fault |", row)
        self.assertNotIn("| expectation |", row)
        return outcome

    def test_s1_a_sign_up_the_connector_cannot_answer_fails_in_the_connectors_words(self):
        cannot_answer(self.double, "POST", lambda path: path == C.SIGNUP_OPTIONS)
        runner = self.walk()
        self.assert_fault(runner, "S1", "HTTP 500", INTERNAL_ERROR_SAID)
        self.assertEqual(runner.outcome_of("S2").outcome, P.NOT_RUN, "no session: S2 says so and does not fail")
        self.assertEqual(len(self.double.customers), 0, "no owner was born")

    def test_s2_a_group_stated_and_other_than_the_runs_is_a_fault(self):
        self.double.account_group = "group-3"
        runner = self.walk()
        self.assert_fault(runner, "S2", "the account is assigned group-3, and group-100 was expected")

    def test_s2_an_account_page_the_connector_cannot_answer_fails_in_the_connectors_words(self):
        cannot_answer(self.double, "GET", lambda path: path == P.ACCOUNT_ROUTE)
        runner = self.walk()
        self.assert_fault(runner, "S2", "unreachable: the connector could not answer the account at GET /v1/account (HTTP 500)", INTERNAL_ERROR_SAID)

    def test_s3_a_press_whose_answer_was_lost_is_the_connectors_fault_in_its_words(self):
        self.double.lose_press_answer = True
        runner = self.walk()
        self.assert_fault(runner, "S3", "unreachable: the connector could not be reached at POST /v1/account/agents", "its answer never arrived")

    def test_s4_a_policy_edit_the_connector_cannot_answer_fails_in_the_connectors_words(self):
        cannot_answer(self.double, "POST", lambda path: path.startswith("/v1/account/agents/") and path.endswith("/policy"))
        runner = self.walk()
        self.assert_fault(runner, "S4", "unreachable: the connector could not answer the agent's policy edit at POST /v1/account/agents/:id/policy (HTTP 500)",
                          INTERNAL_ERROR_SAID)

    def test_s5_a_page_naming_another_funding_wallet_than_the_one_it_registered_is_a_fault(self):
        other = H.checksum_address("0x" + "77" * 20)
        self.double.account_funding = other
        self.double.account_funding_after = 2
        runner = self.walk()
        self.assert_fault(runner, "S5", "is not shown bound to the owner: the owner's funding wallet is %s, and S3 minted the agent against %s" % (other, FUNDING))

    def test_s6_a_gas_door_without_its_key_is_the_deployments_fault_in_the_connectors_words(self):
        self.double.door_key = False
        runner = self.walk()
        self.assert_fault(runner, "S6", "misconfigured: the connector's deployment lacks AAP_GAS_DOOR_KEY", "AAP_UNREACHABLE (503)")

    def test_s7_a_client_registration_the_connector_cannot_answer_is_a_fault_in_its_words(self):
        self.double.register_fails = True
        runner = self.walk()
        self.assert_fault(runner, "S7", "the client registration", "Something went wrong and nothing was changed.")

    def test_s8_a_pinned_tool_missing_is_a_fault_naming_it(self):
        self.double.catalogue = [n for n in pinned() if n != "police.my_usage"]
        runner = self.walk()
        self.assert_fault(runner, "S8", "lists 16 tool(s), and the pinned catalogue of 17 (tables.py) is not all there; missing: police.my_usage")

    def test_s9_another_wallet_named_than_the_agents_is_a_fault(self):
        self.double.my_agent_wallet = "00000000-0000-4000-8000-000000000000"
        runner = self.walk()
        self.assert_fault(runner, "S9", "the wallet is 00000000-0000-4000-8000-000000000000, and S3's agent carries")

    def test_s10_the_polices_deny_is_a_fault_in_the_polices_words(self):
        self.double.police_verdict = "deny"
        runner = self.walk()
        self.assert_fault(runner, "S10", "PolicyDenied: denied (cause: legacy_limit_zero")

    def test_s11_the_rpcs_refusal_is_a_fault_in_the_rpcs_words(self):
        self.double.rpc_error_on = "eth_getTransactionReceipt"
        runner = self.walk()
        self.assert_fault(runner, "S11", "refused: the arbitrum RPC at https://arb1.arbitrum.io refused eth_getTransactionReceipt", "limit exceeded")

    def test_s12_a_debit_outside_the_platforms_own_arithmetic_is_a_fault(self):
        self.double.gas_price_wei = 10 ** 9
        self.double.margin_bps = 3000
        runner = self.walk()
        self.assert_fault(runner, "S12", "the debit of US$1.30 is outside US$1.08 to US$1.12")

    def test_s12a_a_swap_with_no_commission_is_a_fault(self):
        self.double.fee_leg = False
        runner = self.walk()
        self.assert_fault(runner, "S12a", "found no transfer to the fee address 0xabd0…")

    def test_s13_a_delete_refused_while_the_wallet_holds_funds_is_a_fault_in_the_connectors_words(self):
        self.double.funds_left = True
        runner = self.walk()
        self.assert_fault(runner, "S13", "refused: the connector refused the delete at POST /v1/account/agents/:id/delete", "AGENT_NOT_CONNECTABLE (409)")

    def test_every_station_of_the_harness_has_a_failure_path_walked_here(self):
        walked = {match.group(1).upper().replace("A", "a") for match in
                  (re.match(r"test_(s\d+a?)_", name) for name in dir(type(self))) if match}
        self.assertEqual(walked, set(P.STATION_IDS), "a station without a scenario here is a station whose fails nobody has read")


class TheHarnessHasNoExpectationLeft(unittest.TestCase):
    """The census: every fail site in the module, none naming expectation; the two lines of 3 October gone."""

    @staticmethod
    def fail_sites(tree):
        sites = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("StationStop", "Outcome")):
                continue
            keywords = {kw.arg: kw.value for kw in node.keywords}
            outcome = keywords.get("outcome")
            if node.func.id == "Outcome" and len(node.args) >= 2:
                outcome = node.args[1]
            if outcome is None or not any(isinstance(n, ast.Name) and n.id == "FAIL" for n in ast.walk(outcome)):
                continue
            sites.append((node.lineno, keywords.get("cause")))
        return sites

    def test_every_fail_site_is_a_fault_and_none_names_expectation(self):
        with open(HARNESS, encoding="utf-8") as handle:
            source = handle.read()
        sites = self.fail_sites(ast.parse(source))
        self.assertGreater(len(sites), 60, "the census saw the module's failure paths")
        for lineno, cause in sites:
            if cause is not None:
                self.assertFalse(isinstance(cause, ast.Name) and cause.id == "EXPECTATION", "line %d fails on an expectation" % lineno)
                self.assertFalse(isinstance(cause, ast.Constant) and cause.value == "expectation", "line %d fails on an expectation" % lineno)
        self.assertIsNone(re.search(r"cause\s*=\s*EXPECTATION\b", source))
        self.assertIsNone(re.search(r"cause\s*=\s*['\"]expectation['\"]", source))
        self.assertEqual(source.count("EXPECTATION"), 2, "the word is defined and listed among the causes, and used nowhere else")

    def test_the_two_lines_of_3_october_are_gone_from_the_harness_and_the_walk(self):
        with open(HARNESS, encoding="utf-8") as handle:
            source = handle.read()
        with open(DRY_WALK, encoding="utf-8") as handle:
            walk = handle.read()
        for text in (source, walk):
            self.assertNotIn(THE_S2_LINE_OF_3_OCTOBER, text)
            self.assertNotIn(THE_S8_LINE_OF_3_OCTOBER, text)
            self.assertNotIn("not expected:", text)
        self.assertFalse(hasattr(P, "CATALOGUE_SIZE"), "the count is gone; the names stay")


class TheDryWalkSaysTheNewWords(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._http = H.http_request
        H.http_request = lambda *a, **k: (_ for _ in ()).throw(AssertionError("the dry walk reached the network"))

    def tearDown(self):
        H.http_request = self._http
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_s2_and_s8_print_the_new_words(self):
        lines = P.dry_lines(store_dir=self.tmp)
        s2 = [line for line in lines if line.startswith("S2 ")]
        s8 = [line for line in lines if line.startswith("S8 ")]
        self.assertEqual(s2[0], "S2 The account — the account: the owner born once, the seat's standing; the signing group compared with group-100 where the page "
                                "states one, a finding where it states none")
        self.assertIn("a signing group stated on signingGroup, signing_group, group, assignedGroups, assigned_groups, signingGroups compared with group-100 "
                      "(another group fails — a fault)", s2[1])
        self.assertIn('none stated → the finding "%s", and S2 passes' % GROUP_FINDING, s2[1])
        self.assertEqual(s8[0], "S8 The catalogue — the catalogue: the 17 pinned tools, each by name (tables.py)")
        self.assertIn("MCP tools/list {} → expect each pinned tool present by name: %s; a pinned tool missing fails (a fault); a tool present but not pinned is a "
                      "finding naming it; note: \"%s\"" % (", ".join(T.CATALOGUE_NAMES), ASSIGNMENT_NOTE), s8[2])

    def test_the_frozen_walk_carries_them(self):
        with open(DRY_WALK, encoding="utf-8") as handle:
            walk = handle.read()
        self.assertIn("S2 The account — the account: the owner born once, the seat's standing; the signing group compared with group-100", walk)
        self.assertIn("S8 The catalogue — the catalogue: the 17 pinned tools, each by name (tables.py)", walk)
        for name in T.CATALOGUE_NAMES:
            self.assertIn(name, walk)
        self.assertIn(ASSIGNMENT_NOTE, walk)

    def test_group_names_the_group_the_walk_compares_in_dry_lines_and_on_the_command_line(self):
        s2 = next(line for line in P.dry_lines(store_dir=self.tmp, group="group-3") if line.startswith("S2 The account"))
        self.assertIn("compared with group-3 where the page states one", s2)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = P.main(["--dry", "--store", self.tmp, "--group", "group-3"])
        self.assertEqual(code, 0)
        self.assertIn("the Wallet's door and the platform name group-3", out.getvalue())
        self.assertEqual(os.listdir(self.tmp), [], "the dry walk writes nothing")


if __name__ == "__main__":
    unittest.main()
