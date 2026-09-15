"""
The harness sends the field the door requires (Spec T3 §1).

A5 failed on 14 September 2026 on the harness's own argument. MCP Police's `check_action`
schema declares `amount_usd_cents` (required) and, beside it, `amount_usd` described
"NOT ACCEPTED. Present only so an amount sent in dollars is refused rather than silently
ignored." The alias table listed `amount_usd` first, `arguments_for` found the decoy and
sent `amount_usd: 5`, and Police refused before judging: no `judged` block, no hash. The
corridor did nothing wrong.

Now the whole inputSchema is read, and where a door declares more than one name for a
field the one its `required` list names is sent; failing that, one not described NOT
ACCEPTED; failing that, the first present. A door that declares only `amount_usd` — one
that speaks dollars — is obeyed as before. The fixture is Police 1.8.0's schema as the
relay lists it.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402
import tables as T  # noqa: E402

try:
    from .fakes import FakeSession, runner_for
except ImportError:  # run as a top-level module by `unittest discover tests`
    from fakes import FakeSession, runner_for

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
NOT_ACCEPTED = "NOT ACCEPTED. Present only so an amount sent in dollars is refused rather than silently ignored."


def police_tool():
    """MCP Police's check_action as tools/list gives it: amount_usd_cents required, amount_usd a decoy."""
    with open(os.path.join(FIXTURES, "tools-list-police-check-action.json"), "r", encoding="utf-8") as handle:
        return json.load(handle)["tools"][0]


def trade_fields():
    return h.action_fields(S.UNISWAP_ARBITRUM_TRADE, None)


class PoliceSchemaFixtureTest(unittest.TestCase):
    """The fixture really is the shape Eitan's A5 met: both names, one required, one a decoy."""

    def test_the_fixture_declares_the_decoy_beside_the_required_field(self):
        schema = police_tool()["inputSchema"]
        self.assertIn("amount_usd_cents", schema["properties"])
        self.assertIn("amount_usd", schema["properties"])
        self.assertIn("amount_usd_cents", schema["required"])
        self.assertNotIn("amount_usd", schema["required"])
        self.assertEqual(schema["properties"]["amount_usd"]["description"], NOT_ACCEPTED)
        self.assertNotIn("NOT ACCEPTED", schema["properties"]["amount_usd_cents"]["description"])


class TheRequiredFieldWinsTest(unittest.TestCase):
    def test_five_dollars_are_sent_as_five_hundred_cents_and_never_as_dollars(self):
        args, omitted = h.arguments_for(police_tool()["inputSchema"], trade_fields(), {"wallet_id": "w-1", "role_id": "trader.v1"})
        self.assertEqual(args["amount_usd_cents"], 500)
        self.assertNotIn("amount_usd", args, "the decoy is never sent")
        self.assertNotIn("amount", args)
        self.assertNotIn("amount_dollars", args)
        self.assertEqual(args["action_kind"], "trade")
        self.assertEqual(args["asset_symbol"], "USDC")
        self.assertEqual(args["child_wallet_id"], "w-1")
        self.assertEqual(args["role_id"], "trader.v1")
        # Police 1.8.0 declares no to_asset, so it is named in the evidence rather than guessed at (Spec T1 §5).
        self.assertEqual(omitted, ["to_asset"])

    def test_a_door_that_speaks_dollars_is_obeyed(self):
        """A schema with only amount_usd — the Wallet's — is sent dollars, as before Spec T3."""
        schema = {"type": "object", "properties": {"wallet_id": {}, "action": {}, "chain": {}, "asset": {},
                                                   "amount_usd": {"type": "number", "description": "The amount in USD."},
                                                   "to_asset": {}, "venue": {}, "contract_address": {}}}
        args, omitted = h.arguments_for(schema, trade_fields(), {"wallet_id": "w-1"})
        self.assertEqual(args["amount_usd"], 5)
        self.assertNotIn("amount_usd_cents", args)
        self.assertEqual(omitted, [])

    def test_the_required_name_wins_whichever_it_is(self):
        """The rule reads the schema, not the harness's preference: a door that requires dollars is sent dollars."""
        schema = {"type": "object", "properties": {"amount_usd": {}, "amount_usd_cents": {}}, "required": ["amount_usd"]}
        args, _ = h.arguments_for(schema, {"amount_usd": 5}, {})
        self.assertEqual(args, {"amount_usd": 5})

    def test_without_a_required_list_the_decoy_is_still_avoided(self):
        schema = {"type": "object", "properties": {"amount_usd": {"description": NOT_ACCEPTED},
                                                   "amount_usd_cents": {"description": "USD cents."}}}
        args, _ = h.arguments_for(schema, {"amount_usd": 5}, {})
        self.assertEqual(args, {"amount_usd_cents": 500})
        # and with the decoy on the other side
        schema = {"type": "object", "properties": {"amount_usd": {"description": "dollars"},
                                                   "amount_usd_cents": {"description": NOT_ACCEPTED}}}
        args, _ = h.arguments_for(schema, {"amount_usd": 5}, {})
        self.assertEqual(args, {"amount_usd": 5})

    def test_two_undescribed_names_fall_back_to_the_first_present_as_before(self):
        schema = {"type": "object", "properties": {"amount_usd": {}, "amount_usd_cents": {}}}
        args, _ = h.arguments_for(schema, {"amount_usd": 5}, {})
        self.assertEqual(args, {"amount_usd_cents": 500}, "the alias table now lists the cents name first")

    def test_the_alias_table_lists_the_cents_name_first(self):
        self.assertEqual(dict(h.CANON_ALIASES)["amount_usd"], ["amount_usd_cents", "amount_usd"])

    def test_a_schema_that_declares_nothing_sends_nothing_and_names_what_it_left_out(self):
        for schema in ({}, {"type": "object"}, {"type": "object", "properties": {}}):
            args, omitted = h.arguments_for(schema, trade_fields(), {"wallet_id": "w-1"})
            self.assertEqual(args, {}, schema)
            self.assertIn("amount_usd", omitted)
            self.assertIn("wallet_id", omitted)

    def test_schema_parts_reads_properties_required_and_descriptions(self):
        properties, required, descriptions = h.schema_parts(police_tool()["inputSchema"])
        self.assertIn("amount_usd_cents", properties)
        self.assertEqual(required, ["role_id", "amount_usd_cents"])
        self.assertEqual(descriptions["amount_usd"], NOT_ACCEPTED)
        self.assertEqual(h.schema_parts(None), (None, [], {}))
        # a malformed required list is read as none rather than raised on
        self.assertEqual(h.schema_parts({"properties": {"a": {}}, "required": "a"})[1], [])


class TheSessionReadsTheWholeSchemaTest(unittest.TestCase):
    def test_schema_of_is_the_whole_input_schema_and_properties_of_its_properties(self):
        session = h.Mcp.__new__(h.Mcp)  # no OAuth road is walked: only the tool list is read
        session.tools = {"police.check_action": police_tool(),
                         "wallet.my_usage": {"name": "wallet.my_usage"},
                         "wallet.odd": {"name": "wallet.odd", "inputSchema": "not a schema"}}
        schema = session.schema_of("police.check_action")
        self.assertEqual(schema["required"], ["role_id", "amount_usd_cents"])
        self.assertEqual(session.properties_of("police.check_action"), schema["properties"])
        self.assertIsNone(session.schema_of("police.can_sign"), "a tool the door does not list has no schema")
        self.assertIsNone(session.properties_of("police.can_sign"))
        self.assertEqual(session.schema_of("wallet.my_usage"), {}, "a tool listed without a schema is an empty map")
        self.assertEqual(session.properties_of("wallet.my_usage"), {})
        self.assertEqual(session.schema_of("wallet.odd"), {})


class PoliceDoor(FakeSession):
    """The fake corridor with MCP Police's real check_action schema in its tool list."""

    def __init__(self, **kwargs):
        FakeSession.__init__(self, **kwargs)
        self.tools["police.check_action"] = police_tool()


class A5ThroughTheCorridorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a5_sends_cents_to_polices_own_schema_and_reads_the_hash(self):
        session = PoliceDoor(role_id="trader.v1")
        runner = runner_for(session, self.tmp)
        outcome = runner.run_test(S.BY_ID["A5"])
        sent = [c[2] for c in session.calls if c[0] == "A5" and c[1] == "police.check_action"]
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["amount_usd_cents"], 500)
        self.assertNotIn("amount_usd", sent[0])
        self.assertEqual(sent[0]["contract_address"], T.address("UNISWAP_V3_ARBITRUM"))
        self.assertEqual(outcome.outcome, h.PASS, outcome.sentence)

    def test_a_payers_dollar_is_a_hundred_cents(self):
        session = PoliceDoor(role_id="payer.v1")
        runner = runner_for(session, self.tmp)
        runner.run_test(S.BY_ID["A5"])
        sent = [c[2] for c in session.calls if c[0] == "A5" and c[1] == "police.check_action"][0]
        self.assertEqual(sent["amount_usd_cents"], 100)
        self.assertNotIn("amount_usd", sent)

    def test_a_walk_sends_cents_to_police_and_dollars_to_the_wallet(self):
        """The two doors keep their own vocabularies: Police takes cents, the Wallet's schema declares dollars."""
        session = PoliceDoor(police="allow", wallet="ticket", role_id="payer.v1")
        runner = runner_for(session, self.tmp)
        runner.run_test(S.BY_ID["C1"])
        police = [c[2] for c in session.calls if c[0] == "C1" and c[1] == "police.check_action"][0]
        build = [c[2] for c in session.calls if c[0] == "C1" and c[1] == "wallet.build_transaction"][0]
        self.assertEqual(police["amount_usd_cents"], 100)
        self.assertNotIn("amount_usd", police)
        self.assertEqual(build["amount_usd"], 1)
        self.assertNotIn("amount_usd_cents", build)


class TheDryRunPrintsTheCentsNameTest(unittest.TestCase):
    def setUp(self):
        self._http = h.http_request
        h.http_request = self.no_network

    def tearDown(self):
        h.http_request = self._http

    @staticmethod
    def no_network(*args, **kwargs):
        raise AssertionError("the dry run reached for the network: %r" % (args[:2],))

    def test_the_dry_run_line_for_a5_prints_amount_usd_cents(self):
        a5 = [l for l in h.dry_lines(["A"]) if l.startswith("A5 — ") and "police.check_action" in l]
        self.assertEqual(len(a5), 1, a5)
        self.assertIn('"amount_usd_cents": 500', a5[0])
        self.assertNotIn('"amount_usd"', a5[0])
        self.assertIn('"contract_address": "<the listed router for that chain>"', a5[0])
        self.assertIn("judged.policy_hash, whatever the verdict", a5[0])

    def test_every_police_line_in_a_dry_run_prints_the_cents_name(self):
        police = [l for l in h.dry_lines(["A", "C", "D", "E"]) if "tools/call police.check_action" in l]
        self.assertGreater(len(police), 10)
        for line in police:
            self.assertIn('"amount_usd_cents"', line)
            self.assertNotIn('"amount_usd"', line)


if __name__ == "__main__":
    unittest.main()
