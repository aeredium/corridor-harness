"""
Spec T18 (24 September 2026, from Bear's ruling "Let's move to Arbitrum."; amended 16:55: no address changes, the chain is one word in
one place): the book pays on Arbitrum. C9 answers `Arbitrum One`, the payees and the venue probe live on `arbitrum`, and S7 follows the
paymaster. Each test here was red on main.

The double is the estate at AER 360 Spec 106 (tests/test_aer360_double.py): C9 and X1 offer Ethereum, Arbitrum One, Solana, Bitcoin, and the
compiler writes a chosen network by the registry's id. `before_spec_106=True` is the estate before it, `recorded_chains=[…]` a compiler that
records those networks whatever was chosen (the charter double S3 is judged against), and `hold_payee(name, chain, address, status)` a payee
an earlier run left in the register.
"""
import json
import os
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
import tables as corridor  # noqa: E402
from tests.test_aer360_double import EstateDouble, VENUE_CONTRACTS, chain_allowlist, runner_on  # noqa: E402

# Uniswap's published deployments for Arbitrum One (chain id 42161), read once on 24 September 2026 — the row "SwapRouter02". The
# harness never writes the bytes in a table of its own (Spec T7); the corridor's row is held to them here.
UNISWAP_ARBITRUM_DEPLOYMENTS = "https://developers.uniswap.org/docs/protocols/v3/deployments/v3-arbitrum-deployments"
SWAPROUTER02_ON_ARBITRUM_ONE = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
# The payee door's sentence for the probe on the payments' chain (packages/shared/src/refusals.ts, payeeIsVenueContractSentence), word for word.
VENUE_SENTENCE_ON_ARBITRUM = "This address is the contract of Uniswap v3 on arbitrum. Your charter says a payee must be a wallet held by a person or a company (question C19). Nothing was saved."
# SPEC.md §4's sentence, for the offer of 21 September.
NOT_LIVE = "Spec 106 is not live: C9 offers ['Ethereum', 'Solana', 'Bitcoin']; nothing amended"
NORTHWIND = T.address("NORTHWIND_ETHEREUM")


def run_against(tmp=None, said=None, start_at=None, **double_kwargs):
    double = EstateDouble(**double_kwargs)
    runner = runner_on(double, tmp or tempfile.mkdtemp(), invite=double.mint_founder_link(), said=said, start_at=start_at)
    outcomes = {o.station: o for o in runner.run()}
    return double, runner, outcomes


def offline_runner():
    """A runner that reaches no estate: for the resolution of a payee from a register already in hand."""
    def no_transport(request):
        raise AssertionError("no call was expected: %s" % request.full_url)
    tmp = tempfile.mkdtemp()
    return H.Runner("https://estate.test", os.path.join(tmp, "store"), None, False, None, os.path.join(tmp, "out"), transport=no_transport, say=lambda s: None, sleep=lambda s: None)


def register_of(*rows):
    """A payees register as GET /v1/payees answers it: (displayName, chain, address, whitelistStatus, id) per row, one address each."""
    return {"payees": [{"id": "payee-%s" % row_id, "displayName": name, "addresses": [{"id": row_id, "chain": chain, "address": address.lower(), "whitelistStatus": status}]}
                       for name, chain, address, status, row_id in rows]}


def single_source_evidence(chain):
    """
    THE SINGLE-SOURCE PROOF (Spec T18's tests): with PAYEE_CHAIN set to `chain`, the lines that must move with it — S3's expectation, the payees'
    chain, the payee resolution, S7's note and the Treasury sentence — gathered as one list, for the test below and for the PR body.
    """
    out = []
    with unittest.mock.patch.object(T, "PAYEE_CHAIN", chain):
        out.append("PAYEE_CHAIN = %r" % T.PAYEE_CHAIN)
        out.append("S3 expects the recorded networks %s" % H.expected_recorded_networks())
        out.append("S3 on ['aeredium', 'arbitrum']: %s" % H.recorded_networks_difference(["aeredium", "arbitrum"]))
        lines = H.dry_lines()
        s6 = [l for l in lines if l.startswith("S6 — POST /v1/payees {")]
        for line in s6:
            out.append("S6 creates: %s" % line.split(" — ", 1)[1].split(" (as ", 1)[0])
        runner = offline_runner()
        runner.facts["payees_register"] = register_of(("Northwind Supplies", "ethereum", NORTHWIND, "whitelisted", "addr-eth"),
                                                      ("Northwind Supplies", "arbitrum", NORTHWIND, "whitelisted", "addr-arb"),
                                                      ("Northwind Supplies", chain, NORTHWIND, "whitelisted", "addr-%s" % chain))
        address_id, words = runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies")
        out.append("S7 resolves Northwind Supplies to %s — %s" % (address_id, words))
        s7 = [l for l in lines if l.startswith("S7 — ")]
        note = next(l for l in s7 if "fund Harness Treasury: <address> on " in l)
        out.append("S7's note: %s" % note[note.index("fund Harness Treasury"):].split('"', 1)[0])
        short = next(l for l in s7 if "Harness Treasury holds US$<x>" in l)
        out.append("the Treasury sentence: %s" % short[short.index("Harness Treasury holds"):].split('"', 1)[0])
        rows = [l for l in s7 if '"payeeAddressId"' in l or '"oneOff"' in l]
        out.append("S7's %d payment rows name the chain %s" % (len(rows), sorted({json.loads(l.split(" ", 4)[4].split(" (as ", 1)[0])["pays"][0]["chain"] for l in rows if l.split(" ", 4)[4].startswith("{")})))
        venue = next(l for l in lines if l.startswith("S11 — ") and "Venue probe" in l)
        out.append("S11's venue probe: %s" % venue.split(" — ", 1)[1].split(" → ", 1)[0])
    return out


class TheBookAnswersC9WithArbitrumOne(unittest.TestCase):
    """Spec T18 §1: the chain is one word in one place, and everything that names a chain reads it."""

    def test_the_chain_is_one_word_and_c9_is_arbitrum_one(self):
        self.assertEqual(T.PAYEE_CHAIN, "arbitrum")
        self.assertEqual(T.C9_NETWORK_CHOICE, "Arbitrum One")
        self.assertEqual(A.POLICY_ANSWERS["C9"], {"choices": ["Arbitrum One"]})
        self.assertEqual(A.OTHER_NETWORKS, ["Ethereum", "Arbitrum One", "Solana", "Bitcoin"], "Spec 106's served list, mirrored exactly")
        self.assertEqual(A.question("policy", "C9").options, A.OTHER_NETWORKS)
        self.assertEqual(A.question("wallet_account", "X1").options, A.OTHER_NETWORKS)
        self.assertEqual(H.expected_recorded_networks(), ["aeredium", "arbitrum"])
        self.assertEqual(T.public_rpc_url(T.PAYEE_CHAIN), "https://arb1.arbitrum.io/rpc", "the corridor's skeleton names Arbitrum One's public RPC")
        # the pinned keys keep their minted names, so no address moved (the amendment of 16:55)
        self.assertEqual([p["key"] for p in T.PAYEES], ["NORTHWIND_ETHEREUM", "CONTOSO_ETHEREUM"])
        self.assertEqual(T.derive_address("Northwind Supplies/ethereum"), NORTHWIND)
        self.assertEqual([p.payee_key for p in A.PAYMENTS], ["NORTHWIND_ETHEREUM", None, "CONTOSO_ETHEREUM"], "the payment references are unchanged")

    def test_spec_106s_rule_as_the_book_and_the_double_mirror_it(self):
        """chainIdForName / chainAllowlist (AER 360 Spec 106): a display name or an id answers the registry's id; a name the registry does not know is lower-cased."""
        for name in ("Arbitrum One", "arbitrum", " arbitrum one ", "ARBITRUM ONE"):
            self.assertEqual(T.chain_id_for_name(name), "arbitrum", name)
        self.assertEqual(T.chain_id_for_name("Ethereum"), "ethereum")
        self.assertEqual(T.chain_id_for_name("Bitcoin"), "bitcoin", "as the compiler falls back")
        self.assertEqual(chain_allowlist(["Arbitrum One"]), ["aeredium", "arbitrum"])
        self.assertEqual(chain_allowlist(["arbitrum"]), ["aeredium", "arbitrum"])
        self.assertEqual(chain_allowlist(["Arbitrum One", "arbitrum"]), ["aeredium", "arbitrum"], "one arbitrum")
        self.assertEqual(chain_allowlist(["Ethereum"]), ["aeredium", "ethereum"])
        self.assertEqual(chain_allowlist(["Bitcoin"]), ["aeredium", "bitcoin"])
        self.assertEqual(chain_allowlist([" arbitrum one "]), ["aeredium", "arbitrum"])
        self.assertEqual(chain_allowlist(["Local (anvil)"]), ["aeredium", "local (anvil)"], "devOnly is not matched")
        self.assertEqual(chain_allowlist(["Arbitrum One"], before_spec_106=True), ["aeredium", "arbitrum one"], "the compiler before Spec 106: a chain nothing knows")

    def test_a_charter_double_recording_aeredium_and_arbitrum_passes_and_the_two_others_fail_naming_the_difference(self):
        self.assertIsNone(H.recorded_networks_difference(["aeredium", "arbitrum"]))
        self.assertEqual(H.recorded_networks_difference(["aeredium", "ethereum"]),
                         "the charter records the networks ['aeredium', 'ethereum'], not ['aeredium', 'arbitrum']: ethereum is recorded and not expected; arbitrum is expected and not recorded")
        self.assertEqual(H.recorded_networks_difference(["aeredium", "ethereum", "arbitrum"]),
                         "the charter records the networks ['aeredium', 'ethereum', 'arbitrum'], not ['aeredium', 'arbitrum']: ethereum is recorded and not expected")
        self.assertEqual(H.recorded_networks_difference(["aeredium"]),
                         "the charter records the networks ['aeredium'], not ['aeredium', 'arbitrum']: arbitrum is expected and not recorded")
        self.assertEqual(H.recorded_networks_difference(None), "the charter records no networks (recordedChains null), not ['aeredium', 'arbitrum']")
        self.assertEqual(H.SPEC_106_NOT_LIVE % (["Ethereum", "Solana", "Bitcoin"],), NOT_LIVE)


class TheChainIsOneWordInOnePlace(unittest.TestCase):
    """Spec T18's single-source test: with PAYEE_CHAIN set to a double value, S3's expectation, the payees' chain, the payee resolution, S7's note and the Treasury sentence move together."""

    def test_with_payee_chain_set_to_a_double_value_everything_moves_together(self):
        evidence = single_source_evidence("base")
        self.assertEqual(evidence[0], "PAYEE_CHAIN = 'base'")
        self.assertEqual(evidence[1], "S3 expects the recorded networks ['aeredium', 'base']")
        self.assertEqual(evidence[2], "S3 on ['aeredium', 'arbitrum']: the charter records the networks ['aeredium', 'arbitrum'], not ['aeredium', 'base']: arbitrum is recorded and not expected; base is expected and not recorded")
        creates = [l for l in evidence if l.startswith("S6 creates: ")]
        self.assertEqual(len(creates), 2)
        for line in creates:
            body = json.loads(line.split("POST /v1/payees ", 1)[1])
            self.assertEqual((body["defaultChain"], body["addresses"][0]["chain"]), ("base", "base"), line)
        self.assertIn("S7 resolves Northwind Supplies to addr-base — the register's Northwind Supplies on base, whitelisted (the register also holds Northwind Supplies on arbitrum, ethereum: left alone, never paid)", evidence)
        self.assertIn("S7's note: fund Harness Treasury: <address> on base, then rerun", evidence)
        self.assertIn("the Treasury sentence: Harness Treasury holds US$<x>; the run needs US$<y>; fund <address> on base", evidence)
        self.assertIn("S7's 9 payment rows name the chain ['base']", evidence, "the Treasury's review and creation, S7a's review, and the three payments' reviews and creations")
        self.assertTrue(any(l.startswith("S11's venue probe: POST /v1/payees ") and '"chain": "base"' in l for l in evidence), evidence)
        self.assertFalse(any("arbitrum" in l for l in evidence if not l.startswith("S3 on") and "left alone" not in l), evidence)
        # and with the word back in its place, the same roads name arbitrum
        self.assertEqual(single_source_evidence("arbitrum")[1], "S3 expects the recorded networks ['aeredium', 'arbitrum']")
        self.assertIn("S7's note: fund Harness Treasury: <address> on arbitrum, then rerun", single_source_evidence("arbitrum"))

    def test_the_resolution_is_by_name_and_chain_and_a_record_on_another_chain_is_never_paid(self):
        runner = offline_runner()
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies"), (None, "no payee register was read, so Northwind Supplies could not be resolved on arbitrum"))
        runner.facts["payees_register"] = register_of(("Northwind Supplies", "ethereum", NORTHWIND, "whitelisted", "addr-eth"),
                                                      ("Northwind Supplies", "arbitrum", NORTHWIND, "whitelisted", "addr-arb"))
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies"),
                         ("addr-arb", "the register's Northwind Supplies on arbitrum, whitelisted (the register also holds Northwind Supplies on ethereum: left alone, never paid)"))
        self.assertEqual(runner.payee_address_id("NORTHWIND_ETHEREUM"), "addr-arb")
        runner.facts["payees_register"] = register_of(("Northwind Supplies", "ethereum", NORTHWIND, "whitelisted", "addr-eth"))
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies"),
                         (None, "no payee Northwind Supplies on arbitrum: the register holds Northwind Supplies on ethereum only, which is never paid"))
        self.assertIsNone(runner.payee_address_id("NORTHWIND_ETHEREUM"))
        # a whitelisted record on the chain before a proposed one; the same name on the chain at another address is not the pinned payee
        runner.facts["payees_register"] = register_of(("Northwind Supplies", "arbitrum", NORTHWIND, "proposed", "addr-old"),
                                                      ("Northwind Supplies", "arbitrum", T.address("CONTOSO_ETHEREUM"), "whitelisted", "addr-other"),
                                                      ("Northwind Supplies", "arbitrum", NORTHWIND, "whitelisted", "addr-new"))
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies")[0], "addr-new")
        runner.facts["payees_register"] = register_of(("Contoso Legal", "arbitrum", NORTHWIND, "whitelisted", "addr-contoso"))
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies"), (None, "no payee Northwind Supplies on arbitrum in the register"))
        # this run's own record comes first, and only on the chain
        runner.facts["payees"].append({"key": "NORTHWIND_ETHEREUM", "name": "Northwind Supplies", "address_id": "addr-mine", "chain": "arbitrum"})
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies"), ("addr-mine", "this run's Northwind Supplies on arbitrum"))
        runner.facts["payees"][0]["chain"] = "ethereum"
        self.assertEqual(runner.resolve_payee("NORTHWIND_ETHEREUM", "Northwind Supplies")[0], None, "a record of this run on another chain is not paid either")


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheBookPaysOnArbitrum(unittest.TestCase):
    """One run against the estate at Spec 106: S3 records arbitrum, S6 creates the payees on it, S7 pays on it, S11's venue probe is refused on it."""

    @classmethod
    def setUpClass(cls):
        cls.said = []
        cls.double, cls.runner, cls.outcomes = run_against(said=cls.said)

    def test_s3_answers_c9_with_arbitrum_one_and_the_charter_records_aeredium_and_arbitrum(self):
        o = self.outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        c9 = next(s for s in self.runner.evidence["S3"] if s["route"].endswith("/answers") and (s["sent"] or {}).get("questionId") == "C9")
        self.assertEqual(c9["sent"]["value"], {"choices": ["Arbitrum One"]})
        self.assertEqual(self.runner.facts["charter"]["policy"]["recordedChains"], ["aeredium", "arbitrum"])
        self.assertEqual(self.runner.facts["charter"]["policy"]["allowedChains"], ["aeredium-testnet"])
        self.assertIn("networks recorded ['aeredium', 'arbitrum'], allowed ['aeredium-testnet']", o.line, "allowed is printed, not judged")
        self.assertNotIn("the charter records the networks", o.line)
        self.assertEqual([n for n in self.runner.notes["S3"] if n.startswith("Spec 106 is not live")], [])

    def test_s6_creates_the_payees_on_arbitrum_and_the_register_holds_them_there(self):
        o = self.outcomes["S6"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("Northwind Supplies: created on arbitrum; promoted;", o.line)
        self.assertIn("Contoso Legal: created on arbitrum; promoted;", o.line)
        creates = [s for s in self.runner.evidence["S6"] if s["route"] == "POST /v1/payees"]
        self.assertEqual([(s["sent"]["defaultChain"], s["sent"]["addresses"][0]["chain"]) for s in creates], [("arbitrum", "arbitrum")] * 2)
        self.assertEqual({a["chain"] for a in self.double.addresses.values()}, {"arbitrum"})
        self.assertEqual([r["chain"] for r in self.runner.facts["payees"]], ["arbitrum", "arbitrum"])
        self.assertEqual([r["elsewhere"] for r in self.runner.facts["payees"]], [[], []])

    def test_s7_pays_on_arbitrum_reads_the_payees_from_arbitrums_public_rpc_and_names_the_chain_in_its_words(self):
        o = self.outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        rows = [c.sent["pays"][0] for c in self.runner.calls if c.station == "S7" and c.route in ("POST /v1/sets", "POST /v1/sets/review") and isinstance(c.sent, dict)]
        self.assertTrue(rows)
        self.assertEqual({r["chain"] for r in rows}, {"arbitrum"})
        self.assertEqual({r["oneOff"]["chain"] for r in rows if "oneOff" in r}, {"arbitrum"})
        rpc = [c for c in self.runner.calls if c.station == "S7" and c.path == "https://arb1.arbitrum.io/rpc"]
        self.assertEqual(len(rpc), 6, "each payee's balance before and after, on Arbitrum One's public RPC")
        self.assertIn("Harness Treasury holds US$100.00 of USDC on arbitrum", o.line)
        self.assertEqual(self.runner.facts["payee_resolution"], {"P1": "this run's Northwind Supplies on arbitrum", "P3": "this run's Contoso Legal on arbitrum"})
        self.assertNotIn("paid to the register's", o.line, "this run's own records: the resolution is not spoken")
        self.assertEqual([c for c in self.runner.calls if c.station == "S7" and c.route == "GET /v1/payees"], [], "S6 left its records, so S7 read no register")
        self.assertIn("the float Bear funds with USDC on arbitrum, once", self.runner.report())

    def test_the_venue_probe_expects_payee_is_venue_contract_on_arbitrum_and_the_checksum_probe_is_unchanged(self):
        o = self.outcomes["S11"]
        self.assertEqual(o.line, "the attacker: 17 probe(s), 1 finding(s)")
        venue = [s for s in self.runner.evidence["S11"] if "a real venue contract" in str(s.get("probe", ""))]
        self.assertEqual(len(venue), 1)
        self.assertEqual(venue[0]["sent"]["addresses"][0], {"chain": "arbitrum", "address": SWAPROUTER02_ON_ARBITRUM_ONE})
        self.assertEqual(venue[0]["status"], 422)
        self.assertEqual(venue[0]["expected"], "HTTP 422 PAYEE_IS_VENUE_CONTRACT: %s (this run's compiled policy charter says payeeVenueContracts \"refused\")" % VENUE_SENTENCE_ON_ARBITRUM)
        self.assertEqual(venue[0]["result"], "refused as the charter says (C19 No): PAYEE_IS_VENUE_CONTRACT: %s" % VENUE_SENTENCE_ON_ARBITRUM)
        came_back = json.loads(venue[0]["came_back"])
        self.assertEqual(came_back["error"]["detail"], {"venue": "uniswap_v3", "chain": "arbitrum", "address": SWAPROUTER02_ON_ARBITRUM_ONE, "charterQuestionId": "C19"})
        self.assertIn("a payee address that is a real venue contract (Uniswap v3 SwapRouter02 on Arbitrum, read from the corridor's tables.py at run time)", str(venue[0]["probe"]))
        findings = {f.probe: f for f in self.runner.findings if f.station == "S11"}
        self.assertEqual(list(findings), ["a payee address with a wrong checksum"], "the checksum probe is unchanged: the estate lower-cases, and its acceptance is the finding")
        checksum = [s for s in self.runner.evidence["S11"] if "wrong checksum" in str(s.get("probe", ""))][0]
        self.assertEqual(checksum["sent"]["addresses"][0], {"chain": "arbitrum", "address": T.wrong_checksum(T.address("CHECKSUM_PROBE_ETHEREUM"))})
        self.assertEqual(checksum["status"], 201)

    def test_the_probe_sends_the_corridors_arbitrum_row_which_is_uniswaps_published_swaprouter02(self):
        venue = T.venue_address_for_probe()
        self.assertEqual(venue["key"], T.UNISWAP_V3_ARBITRUM)
        self.assertEqual(venue["address"], SWAPROUTER02_ON_ARBITRUM_ONE, "the corridor's row is the address Uniswap publishes for SwapRouter02 on chain 42161")
        self.assertEqual(corridor.address("UNISWAP_V3_ARBITRUM"), SWAPROUTER02_ON_ARBITRUM_ONE)
        self.assertEqual(venue["what"], "Uniswap v3 SwapRouter02 on Arbitrum")
        self.assertEqual(T.UNISWAP_V3_ARBITRUM_SOURCE, UNISWAP_ARBITRUM_DEPLOYMENTS)
        self.assertIn(("uniswap_v3", "arbitrum", SWAPROUTER02_ON_ARBITRUM_ONE), VENUE_CONTRACTS, "the estate's own venue table holds the row on arbitrum")
        self.assertEqual(H.CORRIDOR_VENUE_IDS[T.UNISWAP_V3_ARBITRUM], "uniswap_v3")
        self.assertEqual(H.payee_is_venue_contract_sentence("Uniswap v3", T.PAYEE_CHAIN), VENUE_SENTENCE_ON_ARBITRUM)
        self.assertFalse(T.is_pinned(venue["address"]))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S3JudgesTheRecordedNetworks(unittest.TestCase):
    """Spec T18 §2 and §4 against the double: a charter recording other networks fails S3 naming the difference; a served C9 without Arbitrum One stops it."""

    def test_a_charter_recording_ethereum_fails_s3_naming_the_difference(self):
        double, runner, outcomes = run_against(recorded_chains=["aeredium", "ethereum"])
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("networks recorded ['aeredium', 'ethereum'], allowed ['aeredium-testnet']", o.line)
        self.assertIn("; the charter records the networks ['aeredium', 'ethereum'], not ['aeredium', 'arbitrum']: ethereum is recorded and not expected; arbitrum is expected and not recorded", o.line)
        self.assertEqual(runner.facts["charter"]["policy"]["recordedChains"], ["aeredium", "ethereum"])
        self.assertEqual(outcomes["S6"].outcome, H.PASS, "the payee door judges the registry, not the charter's list (Spec 106): the payees are still created on arbitrum")

    def test_a_charter_recording_ethereum_beside_arbitrum_fails_s3_naming_the_extra(self):
        double, runner, outcomes = run_against(recorded_chains=["aeredium", "ethereum", "arbitrum"])
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("; the charter records the networks ['aeredium', 'ethereum', 'arbitrum'], not ['aeredium', 'arbitrum']: ethereum is recorded and not expected", o.line)
        self.assertNotIn("expected and not recorded", o.line)

    def test_a_served_c9_without_arbitrum_one_stops_s3_with_the_sentence_and_nothing_is_amended(self):
        said = []
        double, runner, outcomes = run_against(said=said, before_spec_106=True)
        o = outcomes["S3"]
        self.assertEqual(o.outcome, H.FAILED_PREREQUISITE, o.line)  # Spec T19 §3: a precondition not met is a missing prerequisite, in red
        self.assertEqual(o.line, "policy interview: %s" % NOT_LIVE)
        self.assertIn("S3 — %s — policy interview: %s" % (H.FAILED_PREREQUISITE, NOT_LIVE), said)  # Spec T19 §3: the line names the kind
        # the served page is the one the estate offered on 21 September, and the book answered nothing on it
        given = [q for q, _, _, _ in runner.facts["answers"]["policy"]]
        self.assertEqual(given[-1], "C9S", "the walk stopped at C9, before answering it")
        self.assertNotIn("C9", given)
        s3_routes = [c.route for c in runner.calls if c.station == "S3"]
        self.assertFalse(any("/confirm" in r or "/compile" in r or "/readback" in r for r in s3_routes), s3_routes)
        self.assertIsNone(double.newest_written_policy_charter(), "nothing amended: no policy charter was written")
        self.assertEqual(runner.facts["charter"].get("policy"), None)
        draft = next(iv for iv in double.interviews.values() if iv["interviewType"] == "policy")
        self.assertEqual(draft["state"], "in_progress", "the draft stands at C9, unconfirmed and uncompiled")
        interview_id = runner.facts["interview"]["policy"]
        note = next(n for n in runner.notes["S3"] if n.startswith(NOT_LIVE))
        self.assertEqual(note, "%s — the book answers C9 with 'Arbitrum One' (aer360_tables.py, C9_NETWORK_CHOICE); the policy draft %s stands at C9, unconfirmed and uncompiled, and the standing charter is untouched" % (NOT_LIVE, interview_id))
        # the offer the double served is the record of 21 September, byte for byte: the page that came back with C9S's answer carries C9
        answered_c9s = [c for c in runner.calls if c.station == "S3" and c.route.endswith("/answers") and (c.sent or {}).get("questionId") == "C9S"][-1]
        served = json.loads(answered_c9s.text)
        self.assertEqual((served["question"]["questionId"], served["question"]["options"]), ("C9", ["Ethereum", "Solana", "Bitcoin"]))
        # the payee door judges the registry, not the charter's list (Spec 106), so S6 still creates the payees on arbitrum; with no policy
        # charter compiled this run the estate seated no whitelist roster, which is S6's own failure to report, not S3's
        self.assertEqual({a["chain"] for a in double.addresses.values()}, {"arbitrum"})


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheRegisterDouble(unittest.TestCase):
    """Spec T18's register doubles: Northwind on ethereum and on arbitrum, or on ethereum only, left by earlier runs."""

    def sets_bodies(self, runner):
        return [c.sent for c in runner.calls if c.station == "S7" and c.route in ("POST /v1/sets", "POST /v1/sets/review") and isinstance(c.sent, dict)]

    def test_holding_northwind_on_ethereum_and_on_arbitrum_p1_pays_the_arbitrum_record(self):
        double = EstateDouble()
        on_ethereum = double.hold_payee("Northwind Supplies", "ethereum", NORTHWIND)
        on_arbitrum = double.hold_payee("Northwind Supplies", "arbitrum", NORTHWIND)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        o6, o7 = outcomes["S6"], outcomes["S7"]
        self.assertEqual(o6.outcome, H.PASS, o6.line)
        self.assertIn("Northwind Supplies: created on arbitrum; promoted;", o6.line)
        self.assertIn("register: Northwind Supplies whitelisted (the register also holds Northwind Supplies on ethereum: left alone, never paid), Contoso Legal whitelisted", o6.line)
        self.assertEqual(runner.facts["payees"][0]["elsewhere"], ["ethereum"])
        self.assertEqual(o7.outcome, H.PASS, o7.line)
        p1 = runner.facts["sets"]["P1"]
        self.assertTrue(p1["landed"], p1["said"])
        mine = runner.facts["payees"][0]["address_id"]
        self.assertEqual(double.addresses[mine]["chain"], "arbitrum")
        paid_ids = [b["pays"][0]["payeeAddressId"] for b in self.sets_bodies(runner) if "payeeAddressId" in b["pays"][0]]
        self.assertIn(mine, paid_ids)
        self.assertNotIn(on_ethereum["id"], paid_ids, "a payee record on ethereum is never paid")
        self.assertEqual({double.addresses[i]["chain"] for i in paid_ids}, {"arbitrum"}, "P1 (and P3) pay arbitrum records")
        self.assertEqual(runner.facts["payee_resolution"]["P1"], "this run's Northwind Supplies on arbitrum")
        self.assertEqual(double.addresses[on_ethereum["id"]]["whitelistStatus"], "whitelisted", "left alone")
        self.assertEqual(double.addresses[on_arbitrum["id"]]["whitelistStatus"], "whitelisted", "left alone too: this run made its own record")
        self.assertFalse(any(on_ethereum["id"] in c.path for c in runner.calls), "no press, no payment, nothing touched the ethereum record")

    def test_holding_northwind_on_ethereum_only_s6_creates_it_on_arbitrum_names_the_other_and_it_is_never_paid(self):
        double = EstateDouble()
        on_ethereum = double.hold_payee("Northwind Supplies", "ethereum", NORTHWIND)
        runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
        outcomes = {o.station: o for o in runner.run()}
        o6, o7 = outcomes["S6"], outcomes["S7"]
        self.assertEqual(o6.outcome, H.PASS, o6.line)
        self.assertIn("payees: Northwind Supplies: created on arbitrum; promoted; Ada Approver counted (1 of 2); Ben Signatory counted (2 of 2): whitelisted; ", o6.line)
        self.assertIn("register: Northwind Supplies whitelisted (the register also holds Northwind Supplies on ethereum: left alone, never paid), Contoso Legal whitelisted", o6.line)
        created = [s for s in runner.evidence["S6"] if s["route"] == "POST /v1/payees" and s["sent"]["displayName"] == "Northwind Supplies"]
        self.assertEqual(created[0]["sent"]["addresses"], [{"chain": "arbitrum", "address": NORTHWIND}])
        self.assertEqual(o7.outcome, H.PASS, o7.line)
        paid_ids = [b["pays"][0]["payeeAddressId"] for b in self.sets_bodies(runner) if "payeeAddressId" in b["pays"][0]]
        self.assertNotIn(on_ethereum["id"], paid_ids, "a payee record on ethereum is never paid")
        self.assertEqual({double.addresses[i]["chain"] for i in paid_ids}, {"arbitrum"})
        self.assertEqual(double.addresses[on_ethereum["id"]]["whitelistStatus"], "whitelisted", "left alone")
        self.assertFalse(any(on_ethereum["id"] in c.path for c in runner.calls))
        # S10 reads the register against what S6 approved by (chain, address): the ethereum row does not stand in for the arbitrum one
        self.assertEqual([f.probe for f in runner.findings if f.probe.startswith("payees register")], [])

    def test_a_run_resumed_at_s7_reads_the_register_once_and_pays_the_arbitrum_record_never_the_ethereum_one(self):
        tmp = tempfile.mkdtemp()
        double = EstateDouble()
        on_ethereum = double.hold_payee("Northwind Supplies", "ethereum", NORTHWIND)
        first = runner_on(double, tmp, invite=double.mint_founder_link())
        first_outcomes = {o.station: o for o in first.run()}
        self.assertEqual(first_outcomes["S7"].outcome, H.PASS, first_outcomes["S7"].line)
        # the rerun at S7: no record of S6's, so the register is read once and each listed payee resolved by (name, chain)
        second = runner_on(double, tmp, start_at="S7")
        outcomes = {o.station: o for o in second.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        reads = [c for c in second.calls if c.station == "S7" and c.route == "GET /v1/payees"]
        self.assertEqual(len(reads), 1, "the register, read once, as the clerk")
        self.assertEqual(reads[0].who, "Cora Clerk")
        step = next(s for s in second.evidence["S7"] if s["route"] == "GET /v1/payees")
        self.assertIn("each listed payee is resolved by (name, chain)", step["expected"])
        first_northwind = first.facts["payees"][0]["address_id"]
        self.assertEqual(second.facts["payee_resolution"]["P1"],
                         "the register's Northwind Supplies on arbitrum, whitelisted (the register also holds Northwind Supplies on ethereum: left alone, never paid)")
        self.assertIn("P1 (1.25 USDC, expected to proceeds to approval): paid to the register's Northwind Supplies on arbitrum, whitelisted (the register also holds Northwind Supplies on ethereum: left alone, never paid); submitted:", o.line)
        paid_ids = [b["pays"][0]["payeeAddressId"] for b in self.sets_bodies(second) if "payeeAddressId" in b["pays"][0]]
        self.assertIn(first_northwind, paid_ids, "the first run's whitelisted record on arbitrum")
        self.assertNotIn(on_ethereum["id"], paid_ids)
        self.assertEqual({double.addresses[i]["chain"] for i in paid_ids}, {"arbitrum"})
        self.assertEqual(len(H.dry_lines()), 231, "the conditional register read is one dry line under S7 (193 → 194); Spec T19 adds S5's head and S14 (194 → 231)")

    def test_a_register_holding_the_payee_on_ethereum_only_at_s7_sends_nothing_for_it_and_says_so(self):
        """A run resumed at S7 on an estate whose register holds Northwind on ethereum only: P1 is not sent, and the line says which record was never paid."""
        tmp = tempfile.mkdtemp()
        double = EstateDouble()
        first = runner_on(double, tmp, invite=double.mint_founder_link())
        first.run()
        # the earlier runs' arbitrum records are gone from this register double; an ethereum record stands in their place
        for address_id in [i for i, a in double.addresses.items() if a["address"] == NORTHWIND.lower()]:
            del double.addresses[address_id]
        on_ethereum = double.hold_payee("Northwind Supplies", "ethereum", NORTHWIND)
        second = runner_on(double, tmp, start_at="S7")
        outcomes = {o.station: o for o in second.run()}
        o = outcomes["S7"]
        self.assertEqual(o.outcome, H.FAIL, o.line)
        self.assertIn("P1 (1.25 USDC, expected to proceeds to approval): no payee Northwind Supplies on arbitrum: the register holds Northwind Supplies on ethereum only, which is never paid; nothing was sent;", o.line)
        self.assertIn("S7a not made: no payee Northwind Supplies on arbitrum: the register holds Northwind Supplies on ethereum only, which is never paid, so the set of three could not be reviewed", o.line)
        paid_ids = [b["pays"][0]["payeeAddressId"] for b in self.sets_bodies(second) if "payeeAddressId" in b["pays"][0]]
        self.assertNotIn(on_ethereum["id"], paid_ids)
        self.assertNotIn("P1", second.facts["sets"])
        self.assertTrue(second.facts["sets"]["P3"]["landed"], "Contoso, still on arbitrum, is paid")


if __name__ == "__main__":
    if "--show" in sys.argv:
        print("\n".join(single_source_evidence(sys.argv[sys.argv.index("--show") + 1] if len(sys.argv) > sys.argv.index("--show") + 1 else "base")))
    else:
        unittest.main()
