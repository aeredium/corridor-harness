"""
Spec T32 (14 November 2026): the estate harness learns that an estate holds bitcoin. The contract is the estate's own specification, Spec
AER360-BTC-1 with its security reading of 12 November 2026 and its second reading of 13 November 2026, as the builder brief carries it whole;
the estate's code stands outside this harness's working folder and was not read. This file holds:

  - the table (aer360_tables.py) to the specification's words, written here as literals, and to the double's own literals (tests/bitcoin_double.py),
    so a wrong pin in the table is a sentence the double does not say;
  - the address's form, the readers that find what the specification names without a field, and the sentence matcher on the two sentences that
    carry a stop's own figures or a door's own ending;
  - the answer book at catalog version 20 (C9B, answered Yes) against tests/fixtures/aer360-version-20-added.json;
  - the auditor's two readings of the new law (`audit_charter`'s expectation for C9B, and `audit_bitcoin_named`, which S3b speaks);
  - each Bitcoin station on the double, one test for each outcome it can report: a pass, the estate's refusal as expected, a finding, a silence,
    a skip;
  - the whole leg on an estate that holds bitcoin and on an estate before Spec AER360-BTC-1; the dry run; the README and the CHANGELOG.

No test here reaches a network, and none sends anything to an address: the addresses the double shows are strings of an address's form, made
from a label, with no key behind them.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_answers as A  # noqa: E402
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
import aer360_tables as T  # noqa: E402
import tests.bitcoin_double as B  # noqa: E402
import tests.test_aer360_double as D  # noqa: E402
from corridor_harness import matches_sentence  # noqa: E402
from tests.bitcoin_double import BitcoinEstate, bitcoin_address_for_tests  # noqa: E402
from tests.test_aer360_double import EstateDouble, runner_on  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BITCOIN_STATIONS = ("S3b", "S5b-1", "S5b-2", "S6b", "S7b-1", "S7b-2", "S7b-3", "S7b-4")
AFTER_THE_ADDRESS = ("S5b-2", "S6b", "S7b-1", "S7b-2", "S7b-3", "S7b-4")
TITLES = dict(H.STATIONS)
# The specification's own words, as literals (sections named beside each): the table and the double are held to these.
SPEC_HELD_NOT_PAID = "Bitcoin is held on this estate as a store of value and is not a method of payment, because a Bitcoin payment takes about an hour to be final."  # Finding 8
SPEC_LATCHED = ("The sources this service reads Bitcoin through did not answer alike on the movements of an address. Their tips stood at 1,002 and 1,002, "
                "and the bound between them is 1 block. The Bitcoin road is stopped: nothing is read on it, and it opens by itself once the sources answer "
                "alike again.")  # the reading of 12 November, Finding 1
SPEC_PROMPT = "Will this company hold bitcoin as a store of value?"  # section 1
SPEC_NOTE = ("Some companies keep part of their value in bitcoin, as a store of value, and your charter records whether yours will. Bitcoin is not a method "
             "of payment here, because a Bitcoin payment takes about an hour to be final. This is bitcoin on the Bitcoin network; wrapped bitcoin is not "
             "offered.")  # Finding 8
SPEC_EXAMPLE_ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"  # section 4: BIP-173's own example address


def read(name):
    with open(os.path.join(ROOT, name), "r", encoding="utf-8") as handle:
        return handle.read()


def holding(**dials):
    """An estate that holds bitcoin, said outright so no interview need be walked, its funding wallet already born."""
    dials.setdefault("bitcoin_held", True)
    dials.setdefault("funding_wallet", "born")
    return BitcoinEstate(**dials)


def enrolled(double, realm=None):
    """A runner on the double with the founder enrolled by invitation and nothing else walked; `realm` moves the workspace's realm before the session is read."""
    if realm is not None:
        double.workspace["realm"] = realm
    link = double.mint_founder_link()
    runner = runner_on(double, tempfile.mkdtemp(), invite=link)
    runner.enrol_by_invite(runner.people[A.FOUNDER], link, "test")
    return runner


def walk(runner, *stations):
    """The stations named, run as a run runs them (a stop caught as an outcome) and recorded, so the summary counts them; returns the outcomes by station."""
    out = {}
    for station in stations:
        outcome = runner.run_station(station, TITLES[station])
        runner.outcomes.append(outcome)
        out[station] = outcome
    return out


def calls_at(runner, station):
    return [c.route for c in runner.calls if c.station == station]


def probes_at(runner, station):
    return [f.probe for f in runner.findings if f.station == station]


def funding_address(double, network="bitcoin-testnet"):
    """The address the double shows for the funding wallet: the double's own derivation, restated here so the test names what it expects to be shown."""
    return bitcoin_address_for_tests("wallet-funding/%s" % double.source_account, network)


class TheTableIsTheSpecifications(unittest.TestCase):
    """aer360_tables.py against the specification's words as literals, and against the double's own literals."""

    def test_the_codes_and_their_statuses(self):
        self.assertEqual(T.BITCOIN_REFUSAL_STATUSES, {"BITCOIN_HELD_NOT_PAID": 422, "BITCOIN_ROAD_CLOSED": 503, "BITCOIN_SOURCES_DISAGREE": 503, "BITCOIN_READS_LIMITED": 429})
        self.assertEqual((T.BITCOIN_HELD_NOT_PAID, T.BITCOIN_ROAD_CLOSED, T.BITCOIN_SOURCES_DISAGREE, T.BITCOIN_READS_LIMITED),
                         (B.BITCOIN_HELD_NOT_PAID, B.BITCOIN_ROAD_CLOSED, B.BITCOIN_SOURCES_DISAGREE, B.BITCOIN_READS_LIMITED))
        for code, status in T.BITCOIN_REFUSAL_STATUSES.items():
            self.assertEqual(D.STATUS[code], status, "the double answers %s under the specification's status" % code)
        self.assertEqual(T.BITCOIN_SOURCES_SETTING, "BITCOIN_SOURCES")
        self.assertIn(T.BITCOIN_SOURCES_SETTING, B.ROAD_CLOSED_SENTENCE, "a closed road's refusal names its setting")

    def test_the_rows_the_asset_and_the_two_reads(self):
        self.assertEqual((T.BITCOIN_CHAIN, T.BITCOIN_TESTNET_CHAIN, T.BITCOIN_CHAINS), ("bitcoin", "bitcoin-testnet", ("bitcoin", "bitcoin-testnet")))
        self.assertEqual((T.BTC, T.BTC_DECIMALS, T.ASSET_DECIMALS["BTC"]), ("BTC", 8, 8))
        self.assertEqual(T.BITCOIN_ADDRESS_PREFIXES, {"bitcoin": "bc1q", "bitcoin-testnet": "tb1q"})
        self.assertEqual((T.BITCOIN_LIST_ROUTE, T.BITCOIN_WALLET_ROUTE % "w-1"), ("/v1/aer360/bitcoin", "/v1/aer360/bitcoin/wallets/w-1"))
        self.assertEqual((T.HELD_NETWORKS_FIELD, T.RECORDED_HELD_NETWORKS_FIELD, T.BITCOIN_HISTORY_WHOLE_FIELD), ("heldNetworks", "recordedHeldNetworks", "historyWhole"))
        self.assertEqual((T.BITCOIN_STATE_SILENT, T.BITCOIN_STATE_ROW_CLOSED, T.BITCOIN_CAUSE_TIPS_APART), ("silent", "row_closed", "tips_apart"))
        self.assertEqual(sorted(T.BITCOIN_LATCHED_DETAIL_KEYS), ["lagBlocks", "network", "read", "tips"])
        self.assertEqual(T.BITCOIN_SPEC_EXAMPLE_ADDRESS, SPEC_EXAMPLE_ADDRESS)
        self.assertEqual(T.BITCOIN_PROBE_SATOSHIS, 1, "one satoshi: the smallest thing a door could take, and no door may take it")

    def test_the_realm_of_the_moment_names_the_row(self):
        self.assertEqual(T.bitcoin_network_for_realm("sandbox"), "bitcoin-testnet")
        self.assertEqual(T.bitcoin_network_for_realm("live"), "bitcoin")
        self.assertEqual(T.bitcoin_network_for_realm(None), "bitcoin", "a realm not stated is never taken for the sandbox")
        self.assertTrue(T.is_bitcoin_chain("bitcoin") and T.is_bitcoin_chain("bitcoin-testnet") and T.is_bitcoin_chain("Bitcoin"))
        self.assertFalse(T.is_bitcoin_chain("arbitrum") or T.is_bitcoin_chain("solana") or T.is_bitcoin_chain(None))

    def test_the_sentences_are_the_specifications_and_the_doubles(self):
        self.assertEqual(T.BITCOIN_HELD_NOT_PAID_SENTENCE, SPEC_HELD_NOT_PAID)
        self.assertEqual(B.HELD_NOT_PAID_SENTENCE, SPEC_HELD_NOT_PAID)
        self.assertEqual(B.LATCHED_SENTENCE, SPEC_LATCHED)
        self.assertEqual(T.BITCOIN_ADDRESS_OPENS_LATER_SENTENCE, B.ADDRESS_OPENS_LATER_SENTENCE)
        self.assertTrue(T.BITCOIN_ADDRESS_OPENS_LATER_SENTENCE.startswith("Your charter says that your company will hold bitcoin, and that answer is kept. No Bitcoin address is shown yet: "))
        self.assertTrue(T.BITCOIN_ADDRESS_OPENS_LATER_SENTENCE.endswith("Nothing is asked of you until then."))
        self.assertEqual(T.BITCOIN_TIPS_APART_SENTENCE, B.TIPS_APART_SENTENCE)
        self.assertTrue(T.BITCOIN_TIPS_APART_SENTENCE.endswith("Nothing is wrong with the wallet; ask again in a moment."))
        self.assertEqual(T.BITCOIN_NEVER_SAID, ("can be moved from here", "held and moved"), "Finding 8: what no sentence says")

    def test_the_matcher_takes_the_judgment_followed_by_what_the_door_did_not_do(self):
        for did_not in B.DID_NOT.values():
            self.assertTrue(H.Runner.held_not_paid_said("%s %s" % (SPEC_HELD_NOT_PAID, did_not)), did_not)
        self.assertTrue(H.Runner.held_not_paid_said(SPEC_HELD_NOT_PAID))
        self.assertFalse(H.Runner.held_not_paid_said("%s Nothing was saved." % B.HELD_AND_MOVED_SENTENCE), "the sentence as it stood before Finding 8 is not the estate's sentence")
        self.assertFalse(H.Runner.held_not_paid_said(B.CHAIN_RECEIVABLE_ONLY_SENTENCE), "'not yet' is never said of Bitcoin")
        self.assertFalse(H.Runner.held_not_paid_said("%s Bitcoin can be moved from here." % SPEC_HELD_NOT_PAID), "nor is a sentence that says what Finding 8 says none says")
        self.assertFalse(H.Runner.held_not_paid_said(""))

    def test_the_matcher_takes_the_latched_stop_with_any_stops_own_figures_and_not_the_met_stop(self):
        self.assertTrue(matches_sentence(T.BITCOIN_SOURCES_LATCHED_SENTENCE, SPEC_LATCHED))
        another = ("The sources this service reads Bitcoin through did not answer alike on the summary of an address. Their tips stood at 975,560 and 975,562, and "
                   "the bound between them is 2 blocks. The Bitcoin road is stopped: nothing is read on it, and it opens by itself once the sources answer alike again.")
        self.assertTrue(matches_sentence(T.BITCOIN_SOURCES_LATCHED_SENTENCE, another), "the read, the tips and the bound are the stop's own")
        self.assertFalse(matches_sentence(T.BITCOIN_SOURCES_LATCHED_SENTENCE, B.MET_SENTENCE), "the met stop's sentence is another sentence")
        self.assertFalse(matches_sentence(T.BITCOIN_SOURCES_LATCHED_SENTENCE, SPEC_LATCHED.replace("it opens by itself once", "restart the estate once")))


class TheAddressAndTheReaders(unittest.TestCase):
    """The form of the network the deployment serves, and the readers that find what the specification names without a field."""

    def test_the_specifications_own_address_has_the_form_of_the_real_network_alone(self):
        self.assertIsNone(T.bitcoin_address_fault(SPEC_EXAMPLE_ADDRESS, "bitcoin"))
        self.assertEqual(T.bitcoin_address_fault(SPEC_EXAMPLE_ADDRESS, "bitcoin-testnet"),
                         "it begins bc1q, the form of bitcoin, and this estate's row is bitcoin-testnet, whose addresses begin tb1q")
        self.assertEqual(len(SPEC_EXAMPLE_ADDRESS), T.BITCOIN_P2WPKH_LENGTH)

    def test_each_fault_of_the_form_is_said_in_words(self):
        test_address = bitcoin_address_for_tests("a wallet of the tests")
        self.assertIsNone(T.bitcoin_address_fault(test_address, "bitcoin-testnet"))
        self.assertEqual(T.bitcoin_address_fault(test_address, "bitcoin"), "it begins tb1q, the form of bitcoin-testnet, and this estate's row is bitcoin, whose addresses begin bc1q")
        self.assertEqual(T.bitcoin_address_fault(test_address.upper(), "bitcoin-testnet"), "it is not written in lower case")
        self.assertEqual(T.bitcoin_address_fault(test_address[:-1], "bitcoin-testnet"), "it is 41 characters long, and the native SegWit address of a key is 42")
        self.assertEqual(T.bitcoin_address_fault("tb1q" + "b" * 38, "bitcoin-testnet"), "it carries 'b', which bech32's alphabet does not hold")
        self.assertEqual(T.bitcoin_address_fault("0x" + "ab" * 20, "bitcoin"), "it does not begin bc1q, as an address of bitcoin does")
        self.assertEqual(T.bitcoin_address_fault(None, "bitcoin"), "it is no address at all")
        self.assertEqual(T.bitcoin_address_fault("", "bitcoin"), "it is no address at all")
        self.assertEqual(T.bitcoin_address_fault(test_address, "solana"), "'solana' is not one of the two Bitcoin rows")

    def test_the_alphabet_is_bip_173s(self):
        self.assertEqual(T.BECH32_ALPHABET, "qpzry9x8gf2tvdw0s3jn54khce6mua7l")
        self.assertEqual(len(set(T.BECH32_ALPHABET)), 32)
        for absent in "1bio":
            self.assertNotIn(absent, T.BECH32_ALPHABET)

    def test_the_doubles_addresses_are_of_the_form_and_are_nobodys(self):
        for network, prefix in (("bitcoin-testnet", "tb1q"), ("bitcoin", "bc1q")):
            address = bitcoin_address_for_tests("label", network)
            self.assertTrue(address.startswith(prefix))
            self.assertIsNone(T.bitcoin_address_fault(address, network))
        self.assertNotEqual(bitcoin_address_for_tests("one"), bitcoin_address_for_tests("two"))
        self.assertEqual(bitcoin_address_for_tests("one"), bitcoin_address_for_tests("one"))

    def test_an_address_is_found_by_its_form_wherever_the_answer_carries_it(self):
        address = bitcoin_address_for_tests("found")
        answer = {"wallets": [{"walletId": "wallet-1", "name": "Funding wallet", "shown": {"bitcoinAddress": address}}], "again": address, "evm": "0x" + "ab" * 20, "n": 3}
        self.assertEqual(T.bitcoin_addresses_in(answer), [address], "once, however often it is carried")
        self.assertEqual(T.bitcoin_addresses_in({"held": False, "wallets": []}), [])
        self.assertEqual(T.bitcoin_addresses_in([SPEC_EXAMPLE_ADDRESS, address]), [SPEC_EXAMPLE_ADDRESS, address])

    def test_a_field_a_sentence_and_the_sources_are_found_by_the_specifications_words(self):
        reading = {"state": "read", "asOf": {"height": 160854, "sources": 2}, "inner": {"historyWhole": False}, "moving": "Moving bitcoin out is not yet built.", "walletId": "wallet-1"}
        self.assertIs(T.deep_find(reading, "historyWhole"), False)
        self.assertIsNone(T.deep_find(reading, "nothing of the kind"))
        self.assertEqual(T.deep_find([{"a": 1}, {"cause": "tips_apart"}], "cause"), "tips_apart")
        self.assertEqual(T.sentences_in(reading), ["Moving bitcoin out is not yet built."], "a name, an id and a state are no sentence")
        self.assertIn("read", T.deep_strings(reading))
        self.assertEqual(T.bitcoin_sources_named(reading), 2)
        self.assertEqual(T.bitcoin_sources_named({"sources": ["the first source", "the second source", "the third source"]}), 3)
        self.assertEqual(T.bitcoin_sources_named({"agreedAt": {"sourceCount": "2"}}), 2)
        self.assertIsNone(T.bitcoin_sources_named({"height": 160854, "agreed": True}), "an answer that names no source is said not compared, never counted")

    def test_satoshis_are_said_in_btc_by_string_arithmetic(self):
        self.assertEqual(T.btc_words(1), "0.00000001 BTC")
        self.assertEqual(T.btc_words(150000000), "1.5 BTC")
        self.assertEqual(T.btc_words("2100000000000000"), "21000000 BTC")
        self.assertEqual(T.btc_words(0), "0 BTC")
        with self.assertRaises(ValueError):
            T.btc_words(-1)

    def test_the_stations_sentences_say_which_answer_they_follow(self):
        self.assertEqual(T.BITCOIN_STATIONS_SKIPPED_SENTENCE % ("S5b-1", T.BITCOIN_NOT_HELD_WORDS % T.BITCOIN_LIST_ROUTE),
                         "skipped by name: at S5b-1 the estate answers that it does not hold bitcoin (GET /v1/aer360/bitcoin: held false)")
        self.assertTrue((T.BITCOIN_ROAD_CLOSED_WORDS % "x").startswith("the estate answers that the Bitcoin road is closed on this deployment ("))
        for sentence in (T.BITCOIN_IMPORT_NOT_WALKED_SENTENCE, T.BITCOIN_DEPOSIT_NOT_WALKED_SENTENCE):
            self.assertTrue(sentence.startswith("skipped by name: "), sentence)
            self.assertIn("Nothing was offered and nothing is claimed of this door", sentence)
            self.assertIn("CONTESTED", sentence)
        self.assertIn("The deposit door is untouched", T.BITCOIN_DEPOSIT_NOT_WALKED_SENTENCE)
        self.assertIn("POST /v1/imports/:importId/review", T.BITCOIN_IMPORT_NOT_WALKED_SENTENCE)
        self.assertEqual(H.BITCOIN_SOURCES_SILENT, "a Bitcoin source was silent")


class TheBookAtVersion20(unittest.TestCase):
    """Spec T32 item 1: the answer book answers catalog version 20's one question so that Harness Holdings holds bitcoin."""

    def setUp(self):
        self.page = D.V20_ADDED["C9B"]

    def test_the_fixture_is_the_specifications_page(self):
        self.assertEqual(list(D.V20_ADDED), ["C9B"], "version 20 added one question, to the Policy Interview")
        self.assertEqual((self.page["questionId"], self.page["kind"], self.page["required"], self.page["options"]), ("C9B", "single_choice", True, ["Yes", "No"]))
        self.assertEqual(self.page["prompt"], SPEC_PROMPT)
        self.assertEqual(self.page["note"], SPEC_NOTE)
        self.assertEqual(self.page["part"], D.V15_ADDED["C2"]["part"], "in Part C, where C9 and the ceilings stand")
        for never in T.BITCOIN_NEVER_SAID:
            self.assertNotIn(never, self.page["note"].lower(), "Finding 8 reworded the note inside version 20")

    def test_the_book_carries_the_questions_words_byte_for_byte(self):
        self.assertEqual((A.HOLD_BITCOIN_QUESTION_ID, A.HOLD_BITCOIN_PROMPT, A.HOLD_BITCOIN_OPTIONS, A.HOLD_BITCOIN_NOTE), ("C9B", SPEC_PROMPT, ["Yes", "No"], SPEC_NOTE))
        q = A.question("policy", "C9B")
        self.assertEqual((q.kind, q.depends_on, q.options, q.required), ("single_choice", None, ["Yes", "No"], True), "compulsory, and gated by nothing")
        self.assertEqual(A.kind_of("policy", "C9B"), self.page["kind"])

    def test_the_book_answers_yes_so_that_harness_holdings_holds_bitcoin(self):
        self.assertEqual(A.POLICY_ANSWERS["C9B"], {"choice": "Yes"})
        self.assertEqual(A.answer_for("policy", self.page), {"choice": "Yes"})
        self.assertEqual(H.spoken_for("single_choice", "C9B", A.POLICY_ANSWERS["C9B"]), "Yes", "as the read-back speaks a single choice")
        with self.assertRaises(A.AnswerDoesNotFit):
            A.answer_for("policy", dict(self.page, options=["No"]))
        self.assertNotIn("C9B", A.ACCOUNT_ANSWERS, "a wallet-account interview never answers C9B")
        self.assertNotIn("C9B", [q.id for q in A.CATALOGS["wallet_account"]])

    def test_the_book_states_version_20_and_keeps_the_record_of_what_was_read_from_the_code(self):
        self.assertEqual(A.CATALOG_VERSION_ANSWERED, 20)
        self.assertEqual(A.CATALOG_VERSION_READ, 15)
        self.assertIn("CATALOG_VERSION = 15", A.CATALOG_SOURCE)
        self.assertEqual(A.ADDED_IN_V20, {"policy": ("C9B",), "wallet_account": ()})
        self.assertIn("Spec AER360-BTC-1", A.CATALOG_VERSION_20_SOURCE)
        self.assertIn("not read from questioncatalog.ts", A.CATALOG_VERSION_20_SOURCE)

    def test_c9b_stands_straight_after_c9_and_the_walk_is_26(self):
        ids = [q.id for q in A.expected_walk("policy")]
        self.assertEqual(ids[ids.index("C9"):ids.index("C2") + 1], ["C9", "C9B", "C2"])
        self.assertEqual(len(ids), 26)
        self.assertEqual(len([q for q in ids if q not in A.ADDED_IN_V20["policy"]]), 25, "an estate before version 20 serves the walk of Spec T27")

    def test_the_double_asks_c9b_from_version_20_and_never_before(self):
        self.assertNotIn("C9B", [q.id for q in EstateDouble().catalog("policy")], "the default double is the estate at version 15")
        self.assertNotIn("C9B", [q.id for q in EstateDouble(catalog_version=19).catalog("policy")])
        ids = [q.id for q in BitcoinEstate().catalog("policy")]
        self.assertEqual(ids[ids.index("C9") + 1], "C9B")
        self.assertEqual(BitcoinEstate().catalog_version, 20)

    def test_the_double_compiles_the_answer_as_the_specification_says(self):
        double = BitcoinEstate()
        answers = {q.id: A.POLICY_ANSWERS[q.id] for q in A.expected_walk("policy")}
        charter = double.compile_charter("policy", answers, 20)
        self.assertEqual((charter["heldNetworks"], charter["recordedHeldNetworks"]), (["bitcoin-testnet"], ["bitcoin"]), "a sandbox charter: the test network's row, the live-day intent beside it")
        self.assertFalse(any(T.is_bitcoin_chain(c) for c in charter["allowedChains"] + charter["recordedChains"]), "nothing is added to allowedChains or recordedChains")
        said_no = double.compile_charter("policy", dict(answers, C9B={"choice": "No"}), 20)
        never_asked = double.compile_charter("policy", {q: v for q, v in answers.items() if q != "C9B"}, 20)
        for charter in (said_no, never_asked):
            self.assertNotIn("heldNetworks", charter)
            self.assertNotIn("recordedHeldNetworks", charter)


def charter_that_holds(**changes):
    """The fields of a compiled sandbox charter that `audit_bitcoin_named` reads, as the specification's section 1 says a Yes compiles them."""
    charter = {"realm": "sandbox", "heldNetworks": ["bitcoin-testnet"], "recordedHeldNetworks": ["bitcoin"], "allowedChains": ["aeredium-testnet"], "recordedChains": ["aeredium", "arbitrum"]}
    charter.update(changes)
    return {k: v for k, v in charter.items() if v is not None}


def read_back_lines(spoken="Yes", beside=B.HELD_READBACK_SANDBOX):
    """A read-back's lines about C9: the networks, the Bitcoin question as answered, the line beside it where one is given, and the next answer."""
    lines = [{"questionId": "C9", "prompt": "prompt of C9", "spoken": "Arbitrum One"}]
    if spoken is not None:
        lines.append({"questionId": "C9B", "prompt": SPEC_PROMPT, "spoken": spoken})
        if beside is not None:
            lines.append({"questionId": B.HELD_READBACK_QUESTION_ID, "prompt": B.HELD_READBACK_PROMPT, "spoken": beside, "synthetic": True})
    lines.append({"questionId": "C2", "prompt": "prompt of C2", "spoken": "US$100.00."})
    return lines


def named(found):
    return [f["probe"] for f in found]


class TheAuditorReadsTheNewLawBack(unittest.TestCase):
    """Spec T32 items 1 and 2: `audit_charter`'s expectation for C9B (S10), and `audit_bitcoin_named` (S3b), each held on a fixture."""

    PROBE = "charter (policy): the networks held (C9B)"

    def held_findings(self, charter, answer):
        answers = {"C9B": answer} if answer is not None else {}
        return [f for f in H.audit_charter("policy", charter, answers) if f["probe"] == self.PROBE]

    def test_a_yes_expects_the_row_of_the_charters_realm(self):
        yes = {"choice": "Yes"}
        self.assertEqual(self.held_findings(charter_that_holds(), yes), [])
        self.assertEqual(self.held_findings(charter_that_holds(realm="live", heldNetworks=["bitcoin"]), yes), [])
        wrong_row = self.held_findings(charter_that_holds(heldNetworks=["bitcoin"]), yes)
        self.assertEqual([(f["expected"], f["said"]) for f in wrong_row], [('["bitcoin-testnet"]', 'the charter carries ["bitcoin"]')])
        dropped = self.held_findings(charter_that_holds(heldNetworks=None), yes)
        self.assertEqual([(f["expected"], f["said"]) for f in dropped], [('["bitcoin-testnet"]', "the charter carries null")], "a Yes the compiler dropped is the auditor's finding")

    def test_a_no_expects_no_such_field_and_a_question_never_asked_expects_nothing(self):
        self.assertEqual(self.held_findings(charter_that_holds(heldNetworks=None, recordedHeldNetworks=None), {"choice": "No"}), [])
        self.assertEqual([f["said"] for f in self.held_findings(charter_that_holds(), {"choice": "No"})], ['the charter carries ["bitcoin-testnet"]'])
        self.assertEqual(self.held_findings(charter_that_holds(heldNetworks=None), None), [], "an estate before version 20: arithmetic on the answers given, nothing assumed")
        self.assertEqual(self.held_findings(charter_that_holds(), None), [])

    def test_a_charter_that_states_no_realm_is_admitted_either_row(self):
        yes = {"choice": "Yes"}
        self.assertEqual(self.held_findings(charter_that_holds(realm=None, heldNetworks=["bitcoin"]), yes), [])
        self.assertEqual(self.held_findings(charter_that_holds(realm=None), yes), [])
        self.assertEqual(len(self.held_findings(charter_that_holds(realm=None, heldNetworks=["arbitrum"]), yes)), 1)

    def test_bitcoin_named_as_the_specification_words_it_raises_nothing(self):
        found, said, is_named = H.audit_bitcoin_named(read_back_lines(), charter_that_holds(), True, D.V20_ADDED["C9B"])
        self.assertEqual(found, [])
        self.assertIs(is_named, True)
        self.assertIn("the estate asked C9B in the specification's words, its note among them", said)
        self.assertIn("the read-back says C9B: 'Yes'; beside it, quoted for a person because the specification gives this sentence's sense and not its words: \"%s\"" % B.HELD_READBACK_SANDBOX, said)
        self.assertIn('the compiled charter of this sandbox estate carries heldNetworks ["bitcoin-testnet"] and recordedHeldNetworks ["bitcoin"], and no Bitcoin row among allowedChains or recordedChains', said)

    def test_the_question_served_in_other_words_is_a_finding_that_names_both(self):
        found, _, _ = H.audit_bitcoin_named(read_back_lines(), charter_that_holds(), True, dict(D.V20_ADDED["C9B"], note="Bitcoin is held here and can be moved from here."))
        self.assertEqual(named(found), ["the charter names bitcoin: the question's note"])
        self.assertIn(SPEC_NOTE, found[0]["expected"])
        self.assertIn("can be moved from here", found[0]["said"])
        found, _, _ = H.audit_bitcoin_named(read_back_lines(), charter_that_holds(), True, dict(D.V20_ADDED["C9B"], prompt="Will this company pay in bitcoin?", options=["Yes", "No", "Later"]))
        self.assertEqual(named(found), ["the charter names bitcoin: the question's words", "the charter names bitcoin: the question's options"])
        found, said, _ = H.audit_bitcoin_named(read_back_lines(), charter_that_holds(), True, None)
        self.assertEqual(found, [], "a run that recorded no page for C9B judges the read-back and the charter alone")
        self.assertFalse(any("the estate asked" in words for words in said))

    def test_the_read_back_is_held_to_the_line_the_answer_and_what_stands_beside_a_yes(self):
        charter = charter_that_holds()
        self.assertEqual(named(H.audit_bitcoin_named(read_back_lines(spoken=None), charter, True)[0]), ["the charter names bitcoin: the read-back's line for C9B"])
        self.assertEqual(named(H.audit_bitcoin_named(read_back_lines(spoken="No", beside=None), charter, True)[0]), ["the charter names bitcoin: the answer read back"])
        self.assertEqual(named(H.audit_bitcoin_named(read_back_lines(beside=None), charter, True)[0]), ["the charter names bitcoin: what the read-back says beside a Yes"])
        moved = H.audit_bitcoin_named(read_back_lines(beside=B.HELD_READBACK_SAYS_MOVED), charter, True)[0]
        self.assertEqual(named(moved), ["the charter names bitcoin: what the read-back says beside a Yes"])
        self.assertIn("no sentence says 'can be moved from here'", moved[0]["expected"])
        other_heading = read_back_lines()
        other_heading[1]["prompt"] = "Does this company hold bitcoin?"
        self.assertEqual(named(H.audit_bitcoin_named(other_heading, charter, True)[0]), ["the charter names bitcoin: the question's words on the read-back"])

    def test_the_compiled_charter_is_held_to_the_row_the_intent_and_the_payment_networks(self):
        lines = read_back_lines()
        found, _, is_named = H.audit_bitcoin_named(lines, charter_that_holds(heldNetworks=["bitcoin"]), True)
        self.assertEqual((named(found), is_named), (["the charter names bitcoin: heldNetworks in the compiled charter"], False))
        self.assertIn('["bitcoin-testnet"] on the charter of a sandbox estate that answered Yes', found[0]["expected"])
        found, _, is_named = H.audit_bitcoin_named(lines, charter_that_holds(heldNetworks=None, recordedHeldNetworks=None), True)
        self.assertEqual((named(found), is_named), (["the charter names bitcoin: heldNetworks in the compiled charter", "the charter names bitcoin: recordedHeldNetworks in the compiled charter"], False))
        found, _, is_named = H.audit_bitcoin_named(lines, charter_that_holds(recordedHeldNetworks=None), True)
        self.assertEqual((named(found), is_named), (["the charter names bitcoin: recordedHeldNetworks in the compiled charter"], True))
        found, _, _ = H.audit_bitcoin_named(lines, charter_that_holds(recordedChains=["aeredium", "arbitrum", "bitcoin"]), True)
        self.assertEqual(named(found), ["the charter names bitcoin: a Bitcoin row among recordedChains"])
        found, _, _ = H.audit_bitcoin_named(lines, charter_that_holds(allowedChains=["aeredium-testnet", "bitcoin-testnet"]), True)
        self.assertEqual(named(found), ["the charter names bitcoin: a Bitcoin row among allowedChains"])

    def test_a_live_charter_holds_the_real_networks_row(self):
        lines = read_back_lines()
        live = charter_that_holds(realm="live", heldNetworks=["bitcoin"], recordedHeldNetworks=None, allowedChains=["arbitrum"])
        found, said, is_named = H.audit_bitcoin_named(lines, live, False)
        self.assertEqual((found, is_named), ([], True), "the specification writes recordedHeldNetworks beside a sandbox charter's row; on a live charter it is judged only where present")
        self.assertTrue(any("the compiled charter of this live estate" in words for words in said))
        found, _, is_named = H.audit_bitcoin_named(lines, dict(live, heldNetworks=["bitcoin-testnet"]), False)
        self.assertEqual((named(found), is_named), (["the charter names bitcoin: heldNetworks in the compiled charter"], False))
        found, _, _ = H.audit_bitcoin_named(lines, dict(live, recordedHeldNetworks=["bitcoin-testnet"]), False)
        self.assertEqual(named(found), ["the charter names bitcoin: recordedHeldNetworks in the compiled charter"])

    def test_a_run_that_holds_no_compiled_charter_says_so_and_names_nothing(self):
        found, said, is_named = H.audit_bitcoin_named(read_back_lines(), None, True)
        self.assertEqual((found, is_named), ([], None))
        self.assertTrue(any("heldNetworks was not compared here" in words for words in said))


class S3bTheCharterNamesBitcoin(unittest.TestCase):
    """S3b makes no call: it reads what S3 read. The facts S3 leaves are laid here by hand, one outcome a test."""

    def runner(self, lines=None, charter=None, answered=True):
        runner = runner_on(EstateDouble(), tempfile.mkdtemp())
        if lines is not None:
            runner.facts["readback"]["policy"] = {"realm": "sandbox", "lines": lines}
        if charter is not None:
            runner.facts["charter"]["policy"] = charter
        if answered:
            runner.facts["answers"]["policy"].append(("C9B", {"choice": "Yes"}, SPEC_PROMPT, "single_choice"))
        return runner

    def test_pass_where_the_read_back_and_the_charter_name_it(self):
        runner = self.runner(read_back_lines(), charter_that_holds())
        outcome = walk(runner, "S3b")["S3b"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("the read-back says C9B: 'Yes'", outcome.line)
        self.assertIn('heldNetworks ["bitcoin-testnet"]', outcome.line)
        self.assertIs(runner.facts["bitcoin"]["charter_named"], True)
        self.assertEqual((runner.findings, runner.calls), ([], []), "no finding, and no call of its own")

    def test_a_finding_where_the_charter_does_not_carry_the_holding(self):
        runner = self.runner(read_back_lines(), charter_that_holds(heldNetworks=None))
        outcome = walk(runner, "S3b")["S3b"]
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S3b"), ["the charter names bitcoin: heldNetworks in the compiled charter"])
        self.assertIs(runner.facts["bitcoin"]["charter_named"], False)

    def test_skipped_where_the_policy_interview_never_asked_the_question(self):
        runner = self.runner([l for l in read_back_lines() if not l["questionId"].startswith("C9B")], charter_that_holds(heldNetworks=None, recordedHeldNetworks=None), answered=False)
        outcome = walk(runner, "S3b")["S3b"]
        self.assertEqual(outcome.outcome, H.SKIPPED, outcome.line)
        self.assertEqual(outcome.line, T.BITCOIN_QUESTION_NOT_ASKED_SENTENCE % ("C9B", SPEC_PROMPT, "Yes"))
        self.assertIn("so it stands at a catalog version before 20 and its charter names no bitcoin", outcome.line)
        self.assertIs(runner.facts["bitcoin"]["charter_named"], False)
        self.assertEqual(runner.findings, [])

    def test_skipped_where_s3_left_no_read_back(self):
        runner = self.runner(answered=False)
        outcome = walk(runner, "S3b")["S3b"]
        self.assertEqual((outcome.outcome, outcome.line), (H.SKIPPED, T.BITCOIN_CHARTER_NOT_READ_SENTENCE))
        self.assertIsNone(runner.facts["bitcoin"]["charter_named"])

    def test_a_charter_that_states_no_realm_is_read_by_the_read_backs_own_word(self):
        runner = self.runner(read_back_lines(), charter_that_holds(realm=None))
        outcome = walk(runner, "S3b")["S3b"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("the compiled charter of this sandbox estate", outcome.line)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S5b1TheAddress(unittest.TestCase):
    """Spec T32 item 3: the address the estate shows for the holding, held to the form of the network the deployment serves, printed for a person."""

    def test_pass_on_a_test_deployment_the_test_networks_form_and_the_address_printed_for_a_person(self):
        double = holding()
        runner = enrolled(double)
        outcome = walk(runner, "S5b-1")["S5b-1"]
        address = funding_address(double)
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("held true, open true on bitcoin-testnet (the realm is sandbox): 1 wallet(s) in the founder's sight", outcome.line)
        self.assertIn("wallet 1 shows %s, of the form of bitcoin-testnet (tb1q…)" % address, outcome.line)
        self.assertEqual(runner.notes["S5b-1"], [T.BITCOIN_ADDRESS_FOR_A_PERSON_LINE % ("1", address, "bitcoin-testnet")])
        self.assertIn("the harness invents no address and asks no faucet", runner.notes["S5b-1"][0])
        self.assertEqual(calls_at(runner, "S5b-1"), ["GET /v1/aer360/bitcoin"], "one read, as the Wallets screen makes it with the page")
        self.assertEqual((runner.findings, len(double.bitcoin_reads)), ([], 1))
        bitcoin = runner.facts["bitcoin"]
        self.assertEqual((bitcoin["kind"], bitcoin["held"], bitcoin["network"], bitcoin["skipped"]), ("wallets", True, "bitcoin-testnet", None))
        self.assertEqual([(w["walletId"], w["address"], w["fault"]) for w in bitcoin["wallets"]], [("wallet-funding", address, None)])
        self.assertEqual(runner.bitcoin_summary_lines(), [
            "Bitcoin (Spec T32): the address the estate shows for the holding on bitcoin-testnet, for a person: wallet 1 — %s. The harness invents no address, asks no faucet and "
            "sends nothing to it; bitcoin is held and read on this estate, never paid." % address])

    def test_pass_where_a_wallet_shows_no_address_and_says_why(self):
        runner = enrolled(holding(funding_wallet_point=False))
        outcome = walk(runner, "S5b-1")["S5b-1"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("wallet 1 shows no address and says why: \"%s\"" % B.NO_POINT_SENTENCE, outcome.line)
        self.assertEqual(runner.notes["S5b-1"], [T.BITCOIN_NO_ADDRESS_FOR_A_PERSON_LINE % "no wallet in the founder's sight shows an address of the estate's row"])
        self.assertEqual(runner.findings, [])

    def test_pass_on_a_real_deployment_the_estates_sentence_for_the_closed_row(self):
        double = holding()
        runner = enrolled(double, realm="live")
        outcomes = walk(runner, "S5b-1", "S5b-2")
        first = outcomes["S5b-1"]
        self.assertEqual(first.outcome, H.PASS, first.line)
        self.assertTrue(first.line.startswith("the estate's sentence as expected: held true, open false and no address: the main network's row is closed until moving bitcoin out is built"), first.line)
        self.assertIn(T.BITCOIN_ADDRESS_OPENS_LATER_SENTENCE, first.line)
        self.assertEqual(runner.notes["S5b-1"], [T.BITCOIN_NO_ADDRESS_FOR_A_PERSON_LINE % T.BITCOIN_ROW_CLOSED_WORDS])
        self.assertEqual((runner.facts["bitcoin"]["kind"], runner.facts["bitcoin"]["network"], runner.facts["bitcoin"]["wallets"]), ("row_closed", "bitcoin", []))
        self.assertEqual(double.bitcoin_reads, [], "a closed row derives nothing and is not counted")
        # the reading is not offered on a closed row, so the station that asks for one is skipped by name, never passed
        self.assertEqual((outcomes["S5b-2"].outcome, outcomes["S5b-2"].line), (H.SKIPPED, "skipped by name: %s" % T.BITCOIN_ROW_CLOSED_WORDS))
        self.assertEqual(calls_at(runner, "S5b-2"), [])
        self.assertEqual(runner.findings, [])

    def test_the_estates_refusal_as_expected_where_the_road_is_closed_and_the_later_stations_skip_by_name(self):
        double = holding(bitcoin_road="closed", list_refuses_on_a_closed_road=True)
        runner = enrolled(double)
        outcomes = walk(runner, "S5b-1", *AFTER_THE_ADDRESS)
        first = outcomes["S5b-1"]
        self.assertEqual(first.outcome, H.PASS, first.line)
        self.assertIn("the estate's refusal as expected: BITCOIN_ROAD_CLOSED, 503 — \"%s\"" % B.ROAD_CLOSED_SENTENCE, first.line)
        self.assertTrue(first.line.endswith("; no address was shown, and the Bitcoin stations after this one are skipped by name"), first.line)
        which = T.BITCOIN_STATIONS_SKIPPED_SENTENCE % ("S5b-1", T.BITCOIN_ROAD_CLOSED_WORDS % ("BITCOIN_ROAD_CLOSED: %s" % B.ROAD_CLOSED_SENTENCE))
        for station in AFTER_THE_ADDRESS:
            self.assertEqual((outcomes[station].outcome, outcomes[station].line), (H.SKIPPED, which), station)
        self.assertEqual([c.route for c in runner.calls if c.station in BITCOIN_STATIONS], ["GET /v1/aer360/bitcoin"], "one read; nothing is offered to a door after the estate's answer")
        self.assertEqual((runner.findings, double.bitcoin_reads), ([], []))
        self.assertEqual(runner.bitcoin_summary_lines(), [
            "Bitcoin (Spec T32): at S5b-1 %s. Bitcoin stations skipped, counted as skipped and never as passed: 6 (S5b-2, S6b, S7b-1, S7b-2, S7b-3, S7b-4)." % (
                T.BITCOIN_ROAD_CLOSED_WORDS % ("BITCOIN_ROAD_CLOSED: %s" % B.ROAD_CLOSED_SENTENCE))])

    def test_the_estates_refusal_as_expected_where_the_road_is_stopped_or_the_caller_is_limited(self):
        stopped = enrolled(holding(bitcoin_road="stopped", list_refuses_on_a_closed_road=True))
        outcome = walk(stopped, "S5b-1")["S5b-1"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("the estate's refusal as expected: BITCOIN_SOURCES_DISAGREE, 503 — \"%s\"" % B.LATCHED_SENTENCE, outcome.line)
        self.assertIn("the latched form", outcome.line)
        self.assertTrue(outcome.line.endswith("; no address was shown in this run"), outcome.line)
        self.assertIsNone(stopped.facts["bitcoin"]["skipped"], "a stop is not the road closed on this deployment: the doors after are still walked")
        limited = enrolled(holding(bitcoin_reads_limited=True))
        outcome = walk(limited, "S5b-1")["S5b-1"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("the estate's refusal as expected: BITCOIN_READS_LIMITED, 429 — \"%s\"" % B.READS_LIMITED_SENTENCE, outcome.line)
        self.assertEqual((stopped.findings, limited.findings), ([], []))

    def test_skipped_where_the_estate_answers_that_it_does_not_hold_bitcoin(self):
        double = BitcoinEstate(bitcoin_held=False, funding_wallet="born")
        runner = enrolled(double)
        outcomes = walk(runner, "S5b-1", *AFTER_THE_ADDRESS)
        which = "skipped by name: at S5b-1 the estate answers that it does not hold bitcoin (GET /v1/aer360/bitcoin: held false)"
        self.assertEqual((outcomes["S5b-1"].outcome, outcomes["S5b-1"].line),
                         (H.SKIPPED, "%s; the Bitcoin stations after it are skipped with it, counted as skipped and never as passed" % which))
        for station in AFTER_THE_ADDRESS:
            self.assertEqual((outcomes[station].outcome, outcomes[station].line), (H.SKIPPED, which), station)
        self.assertEqual([c.route for c in runner.calls if c.station in BITCOIN_STATIONS], ["GET /v1/aer360/bitcoin"])
        self.assertEqual((runner.findings, double.payees, double.sets), ([], {}, {}))
        self.assertEqual(runner.notes["S5b-1"], [], "no address, so none is printed")
        self.assertEqual(runner.bitcoin_summary_lines(), [
            "Bitcoin (Spec T32): at S5b-1 the estate answers that it does not hold bitcoin (GET /v1/aer360/bitcoin: held false). Bitcoin stations skipped, counted as skipped "
            "and never as passed: 7 (S5b-1, S5b-2, S6b, S7b-1, S7b-2, S7b-3, S7b-4)."])
        self.assertEqual(H.exit_code_of(runner.outcomes), 0, "a skip is neither the estate's failure nor a pass")

    def test_skipped_where_the_estate_has_no_bitcoin_road_at_all(self):
        runner = enrolled(EstateDouble(funding_wallet="born"))
        outcomes = walk(runner, "S5b-1", "S6b")
        self.assertEqual(outcomes["S5b-1"].outcome, H.SKIPPED, outcomes["S5b-1"].line)
        self.assertIn("skipped by name: at S5b-1 the estate answers no Bitcoin road (GET /v1/aer360/bitcoin: REQUEST_MALFORMED: ", outcomes["S5b-1"].line)
        self.assertIn("so it stands before Spec AER360-BTC-1 and holds no bitcoin", outcomes["S5b-1"].line)
        self.assertEqual(outcomes["S6b"].outcome, H.SKIPPED, outcomes["S6b"].line)
        self.assertEqual((runner.facts["bitcoin"]["kind"], runner.findings), ("absent", []))

    def test_a_finding_where_a_test_deployment_shows_the_real_networks_form(self):
        double = holding(bitcoin_fault="address_of_the_main_network")
        runner = enrolled(double)
        outcome = walk(runner, "S5b-1")["S5b-1"]
        shown = funding_address(double, "bitcoin")
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-1"), ["the address shown for wallet 1 is not of the form of bitcoin-testnet"])
        finding = runner.findings[0]
        self.assertIn("tb1q… on bitcoin-testnet, the row of this estate's realm", finding.expected)
        self.assertIn("the estate shows %r: it begins bc1q, the form of bitcoin" % shown, finding.said)
        self.assertEqual(runner.notes["S5b-1"], [T.BITCOIN_NO_ADDRESS_FOR_A_PERSON_LINE % "no wallet in the founder's sight shows an address of the estate's row"],
                         "an address of the wrong network is not printed for a person to send to")
        self.assertEqual(runner.bitcoin_offer()[:2], ("bitcoin", SPEC_EXAMPLE_ADDRESS), "nor offered to a door: the specification's own example stands in")

    def test_a_finding_where_a_real_deployment_answers_the_main_networks_row_open(self):
        runner = enrolled(holding(main_network_open=True), realm="live")
        outcome = walk(runner, "S5b-1")["S5b-1"]
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-1"), ["the main network's row answered open"])
        self.assertIn("BITCOIN_MAIN_NETWORK_OPEN is false until brief AER360-BTC-2", runner.findings[0].expected)

    def test_a_finding_where_a_wallet_shows_neither_an_address_nor_a_sentence(self):
        runner = enrolled(holding(funding_wallet_point=False, bitcoin_fault="wallet_says_nothing"))
        outcome = walk(runner, "S5b-1")["S5b-1"]
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-1"), ["wallet 1 is shown with neither an address nor a sentence"])

    def test_a_finding_where_the_charter_names_bitcoin_and_the_estate_answers_that_it_holds_none(self):
        runner = enrolled(BitcoinEstate(bitcoin_held=False, funding_wallet="born"))
        runner.facts["bitcoin"]["charter_named"] = True  # as S3b leaves it where this run's compiled charter carries heldNetworks
        outcome = walk(runner, "S5b-1")["S5b-1"]
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-1"), ["the charter names bitcoin and the estate answers that it holds none"])

    def test_an_estate_that_names_its_fields_otherwise_is_read_by_the_specifications_words(self):
        double = holding(bitcoin_fault="other_field_names")
        runner = enrolled(double)
        outcomes = walk(runner, "S5b-1", "S5b-2")
        address = funding_address(double)
        self.assertEqual([outcomes[s].outcome for s in ("S5b-1", "S5b-2")], [H.PASS, H.PASS], [outcomes[s].line for s in ("S5b-1", "S5b-2")])
        self.assertIn("wallet Funding wallet shows %s, of the form of bitcoin-testnet (tb1q…)" % address, outcomes["S5b-1"].line)
        self.assertIn("wallet Funding wallet: a reading — historyWhole true; 2 sources answered and agree", outcomes["S5b-2"].line)
        self.assertEqual(runner.findings, [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class S5b2TheReading(unittest.TestCase):
    """Spec T32 item 4: the reading asked as the founder's screen asks it, and every answer told apart as the specification tells it apart."""

    def reading(self, **dials):
        double = holding(**dials)
        runner = enrolled(double)
        outcomes = walk(runner, "S5b-1", "S5b-2")
        self.assertEqual(outcomes["S5b-1"].outcome, H.PASS, outcomes["S5b-1"].line)
        return double, runner, outcomes["S5b-2"]

    def test_pass_a_reading_that_two_sources_answered_and_agree_on(self):
        double, runner, outcome = self.reading()
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("wallet 1: a reading — historyWhole true; 2 sources answered and agree; the estate's answer, for a person: ", outcome.line)
        self.assertIn(funding_address(double), outcome.line)
        self.assertEqual(calls_at(runner, "S5b-2"), ["GET /v1/aer360/bitcoin/wallets/wallet-funding"], "one press, one reading, never retried")
        self.assertEqual((runner.findings, len(double.bitcoin_reads)), ([], 2))
        self.assertEqual([r["kind"] for r in runner.facts["bitcoin"]["readings"]], ["reading"])

    def test_a_run_resumed_at_the_reading_reads_the_estates_standing_first(self):
        double = holding()
        runner = enrolled(double)
        outcome = walk(runner, "S5b-2")["S5b-2"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertEqual(calls_at(runner, "S5b-2"), ["GET /v1/aer360/bitcoin", "GET /v1/aer360/bitcoin/wallets/wallet-funding"])

    def test_the_estates_refusal_as_expected_a_closed_road_and_the_doors_after_it_skip_by_name(self):
        double, runner, outcome = self.reading(bitcoin_road="closed")
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("wallet 1: the estate's refusal as expected: BITCOIN_ROAD_CLOSED, 503 — \"%s\" — the Bitcoin road is closed on this deployment" % B.ROAD_CLOSED_SENTENCE, outcome.line)
        self.assertTrue(outcome.line.endswith("; the Bitcoin stations after this one are skipped by name"), outcome.line)
        after = walk(runner, "S6b", "S7b-1", "S7b-2", "S7b-3", "S7b-4")
        which = T.BITCOIN_STATIONS_SKIPPED_SENTENCE % ("S5b-2", T.BITCOIN_ROAD_CLOSED_WORDS % ("BITCOIN_ROAD_CLOSED: %s" % B.ROAD_CLOSED_SENTENCE))
        for station, skipped in after.items():
            self.assertEqual((skipped.outcome, skipped.line), (H.SKIPPED, which), station)
        self.assertEqual([c.route for c in runner.calls if c.route.startswith("POST") and c.station in BITCOIN_STATIONS], [], "nothing offered to a door")
        self.assertEqual(runner.findings, [])

    def test_the_estates_refusal_as_expected_a_stop_in_its_latched_form(self):
        double, runner, outcome = self.reading(bitcoin_road="stopped")
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("BITCOIN_SOURCES_DISAGREE, 503 — \"%s\"" % B.LATCHED_SENTENCE, outcome.line)
        self.assertIn("the latched form, told to every read after the one that met the difference: the network, the read, the tips and the bound, and nothing of any wallet", outcome.line)
        self.assertEqual(runner.findings, [])
        self.assertEqual(walk(runner, "S6b")["S6b"].outcome, H.PASS, "a stopped road stops no payment door's judgment")

    def test_the_estates_refusal_as_expected_a_stop_in_its_met_form_printed_and_not_matched(self):
        double, runner, outcome = self.reading(bitcoin_road="met")
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("BITCOIN_SOURCES_DISAGREE, 503 — \"%s\"" % B.MET_SENTENCE, outcome.line)
        self.assertIn("the met form, the stop's own sentence for the caller whose read met the difference", outcome.line)
        self.assertEqual(runner.findings, [])

    def test_the_estates_refusal_as_expected_a_reading_that_is_limited(self):
        double, runner, outcome = self.reading(bitcoin_reads_limited="readings")
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("BITCOIN_READS_LIMITED, 429 — \"%s\" — the readings of this caller are limited, and nothing was read" % B.READS_LIMITED_SENTENCE, outcome.line)
        self.assertEqual(runner.findings, [])

    def test_a_silence_is_reported_as_a_silence_and_never_as_a_pass(self):
        double, runner, outcome = self.reading(bitcoin_fault="silent")
        self.assertEqual(outcome.outcome, H.FAILED_PREREQUISITE, outcome.line)
        self.assertNotEqual(outcome.outcome, H.PASS)
        self.assertEqual(outcome.line, "bitcoin reading: %s — wallet 1: %s (cause source_silent)" % (H.BITCOIN_SOURCES_SILENT, T.BITCOIN_SILENCE_WORDS % ("\"%s\"" % B.SILENT_SENTENCE)))
        self.assertIn("a silence, reported as a silence and never as a pass", outcome.line)
        self.assertEqual(runner.findings, [], "a silence is not the estate's refusal and not a finding against it")
        self.assertEqual(H.exit_code_of([outcome]), 1, "and the run does not end clean on it")
        self.assertIsNone(runner.facts["bitcoin"]["skipped"], "a silence closes nothing: the next read asks again")

    def test_the_silence_of_tips_that_stood_apart_is_told_in_the_specifications_sentence(self):
        double, runner, outcome = self.reading(bitcoin_fault="tips_apart")
        self.assertEqual(outcome.outcome, H.FAILED_PREREQUISITE, outcome.line)
        self.assertIn(T.BITCOIN_TIPS_APART_SENTENCE, outcome.line)
        self.assertIn("(cause tips_apart)", outcome.line)
        self.assertEqual(runner.findings, [])

    def test_a_finding_where_that_silence_is_said_in_other_words(self):
        double, runner, outcome = self.reading(bitcoin_fault="tips_apart_in_other_words")
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-2"), ["the silence of tips that stood apart, for wallet 1"])
        self.assertIn(T.BITCOIN_TIPS_APART_SENTENCE, runner.findings[0].expected)
        self.assertIn(B.SILENT_SENTENCE, runner.findings[0].said)

    def test_a_finding_where_a_reading_names_one_source(self):
        double, runner, outcome = self.reading(bitcoin_fault="one_source")
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-2"), ["the sources of wallet 1's reading"])
        self.assertEqual(runner.findings[0].said, "the reading names 1 source(s)")

    def test_a_finding_where_the_reading_is_of_another_address(self):
        double, runner, outcome = self.reading(bitcoin_fault="reading_of_another_address")
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-2"), ["wallet 1's reading is of another address"])

    def test_a_finding_where_the_latched_stop_carries_something_of_a_wallet(self):
        double, runner, outcome = self.reading(bitcoin_road="stopped", bitcoin_fault="latched_names_a_wallet")
        self.assertEqual(outcome.outcome, H.FAIL, outcome.line)
        self.assertEqual(probes_at(runner, "S5b-2"), ["the latched stop's detail", "the latched stop names an address"])
        self.assertIn("the estate's detail holds address, lagBlocks, network, read, tips", runner.findings[0].said)

    def test_skipped_where_no_wallet_shows_an_address_to_read(self):
        double, runner, outcome = self.reading(funding_wallet_point=False)
        self.assertEqual(outcome.outcome, H.SKIPPED, outcome.line)
        self.assertTrue(outcome.line.startswith("skipped by name: no reading was taken, because no wallet in the founder's sight shows a Bitcoin address — wallet 1: no reading — "), outcome.line)
        self.assertIn(B.NO_POINT_SENTENCE, outcome.line)
        self.assertEqual(calls_at(runner, "S5b-2"), ["GET /v1/aer360/bitcoin/wallets/wallet-funding"], "asked once of the first wallet listed, as the screen's button would be")
        self.assertEqual(runner.findings, [])


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class HeldNotPaid(unittest.TestCase):
    """Spec T32 item 5: one station for each door, each offered one satoshi on the estate's Bitcoin row and refused in the estate's sentence. Nothing is paid and nothing moves."""

    REFUSED = "the estate's refusal as expected — BITCOIN_HELD_NOT_PAID, 422 — \"%s %s\""

    def at_the_doors(self, *stations, **dials):
        double = holding(**dials)
        runner = enrolled(double)
        outcomes = walk(runner, "S5b-1", *stations)
        return double, runner, outcomes

    def sent_at(self, runner, station, route):
        return next(c.sent for c in runner.calls if c.station == station and c.route == route)

    def test_s6b_pass_a_payee_in_bitcoin_is_refused_and_nothing_is_written(self):
        double, runner, outcomes = self.at_the_doors("S6b")
        outcome, address = outcomes["S6b"], funding_address(double)
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("a payee offered on bitcoin-testnet at %s — the address the estate itself shows for wallet 1 on bitcoin-testnet: " % address, outcome.line)
        self.assertIn(self.REFUSED % (SPEC_HELD_NOT_PAID, B.DID_NOT["payee"]), outcome.line)
        self.assertTrue(outcome.line.endswith("; nothing written"), outcome.line)
        self.assertEqual(calls_at(runner, "S6b"), ["POST /v1/payees", "GET /v1/payees"], "the offer, then the register read to prove nothing was written")
        self.assertEqual(self.sent_at(runner, "S6b", "POST /v1/payees"),
                         {"displayName": "Bitcoin payee probe", "defaultAsset": "BTC", "defaultChain": "bitcoin-testnet", "addresses": [{"chain": "bitcoin-testnet", "address": address}]})
        self.assertEqual((double.payees, double.addresses, runner.findings), ({}, {}, []))

    def test_s6b_on_a_closed_row_offers_the_specifications_own_address_and_never_one_of_its_invention(self):
        double = holding()
        runner = enrolled(double, realm="live")
        outcome = walk(runner, "S5b-1", "S6b")["S6b"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("a payee offered on bitcoin at %s — the specification's own example address (BIP-173's, Spec AER360-BTC-1 §4) on bitcoin" % SPEC_EXAMPLE_ADDRESS, outcome.line)
        self.assertEqual(self.sent_at(runner, "S6b", "POST /v1/payees")["addresses"], [{"chain": "bitcoin", "address": SPEC_EXAMPLE_ADDRESS}])
        self.assertEqual((double.payees, runner.findings), ({}, []))

    def test_s6b_a_finding_where_the_door_says_not_yet(self):
        double, runner, outcomes = self.at_the_doors("S6b", payment_doors="not_yet")
        self.assertEqual(outcomes["S6b"].outcome, H.FAIL, outcomes["S6b"].line)
        self.assertEqual(probes_at(runner, "S6b"), ["the payee door (POST /v1/payees) did not refuse a Bitcoin row as the specification says"])
        finding = runner.findings[0]
        self.assertIn("422 BITCOIN_HELD_NOT_PAID: \"%s\" followed by what the door did not do" % SPEC_HELD_NOT_PAID, finding.expected)
        self.assertEqual(finding.said, "the door answered HTTP 422 — CHAIN_RECEIVABLE_ONLY: %s" % B.CHAIN_RECEIVABLE_ONLY_SENTENCE, "the finding names both: the specification's sentence and the estate's")
        self.assertIn("not refused as the specification says", outcomes["S6b"].line)

    def test_s6b_a_finding_where_the_door_says_the_sentence_finding_8_struck(self):
        double, runner, outcomes = self.at_the_doors("S6b", payment_doors="held_and_moved")
        self.assertEqual(outcomes["S6b"].outcome, H.FAIL, outcomes["S6b"].line)
        self.assertEqual(probes_at(runner, "S6b"), ["the payee door (POST /v1/payees) did not refuse a Bitcoin row as the specification says"])
        self.assertIn(B.HELD_AND_MOVED_SENTENCE, runner.findings[0].said)

    def test_s7b_1_pass_a_set_in_bitcoin_is_refused_at_its_review_and_nothing_is_created(self):
        double, runner, outcomes = self.at_the_doors("S7b-1")
        outcome, address = outcomes["S7b-1"], funding_address(double)
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("a set of one payment of 0.00000001 BTC on bitcoin-testnet to %s" % address, outcome.line)
        self.assertIn(self.REFUSED % (SPEC_HELD_NOT_PAID, B.DID_NOT["review"]), outcome.line)
        self.assertTrue(outcome.line.endswith("; nothing created"), outcome.line)
        self.assertEqual(calls_at(runner, "S7b-1"), ["POST /v1/sets/review", "GET /v1/sets"])
        self.assertEqual(self.sent_at(runner, "S7b-1", "POST /v1/sets/review"), {
            "pays": [{"oneOff": {"chain": "bitcoin-testnet", "address": address, "declared": True, "payeeName": "Bitcoin probe destination"},
                      "asset": "BTC", "chain": "bitcoin-testnet", "amountMinor": "1", "invoiceRef": "HH-B001"}], "duplicatesAcknowledged": False})
        self.assertEqual((double.sets, runner.findings), ({}, []))

    def test_s7b_1_pass_where_the_review_answers_and_its_gate_refuses_the_row(self):
        double, runner, outcomes = self.at_the_doors("S7b-1", review_refuses="on the gate")
        outcome = outcomes["S7b-1"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("the estate's refusal as expected — the review answered HTTP 200, acceptable false, its gate's row refused BITCOIN_HELD_NOT_PAID — \"%s %s\"" % (
            SPEC_HELD_NOT_PAID, B.DID_NOT["review"]), outcome.line)
        self.assertEqual((double.sets, runner.findings), ({}, []))

    def test_s7b_1_a_finding_where_the_gate_refuses_in_the_struck_sentence_or_the_review_says_not_yet(self):
        probe = "the set's review (POST /v1/sets/review) did not refuse a Bitcoin row as the specification says"
        for dials in ({"review_refuses": "on the gate", "payment_doors": "held_and_moved"}, {"payment_doors": "not_yet"}, {"review_refuses": "on the gate", "payment_doors": "not_yet"}):
            double, runner, outcomes = self.at_the_doors("S7b-1", **dials)
            self.assertEqual(outcomes["S7b-1"].outcome, H.FAIL, "%r: %s" % (dials, outcomes["S7b-1"].line))
            self.assertEqual(probes_at(runner, "S7b-1"), [probe], dials)
        self.assertEqual(runner.findings[0].said, "the door answered HTTP 200, and nothing was refused", "a review that names another code on its gate has not refused the row as the specification says")

    def test_s7b_3_pass_a_run_in_bitcoin_is_refused_at_its_creation_and_no_run_stands(self):
        double, runner, outcomes = self.at_the_doors("S7b-3")
        outcome = outcomes["S7b-3"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertIn("a run of one payment of 0.00000001 BTC on bitcoin-testnet to %s" % funding_address(double), outcome.line)
        self.assertIn(self.REFUSED % (SPEC_HELD_NOT_PAID, B.DID_NOT["run"]), outcome.line)
        self.assertTrue(outcome.line.endswith("; no run was created"), outcome.line)
        self.assertEqual(calls_at(runner, "S7b-3"), ["POST /v1/sets", "GET /v1/sets"])
        sent = self.sent_at(runner, "S7b-3", "POST /v1/sets")
        self.assertEqual((sent["idempotencyKey"], sent["reference"], sent["pays"][0]["invoiceRef"], sent["pays"][0]["amountMinor"]),
                         ("aer360-harness-%s-PB1" % runner.run_stamp, "Harness bitcoin probe PB1", "HH-B002", "1"))
        self.assertEqual((double.sets, runner.findings), ({}, []))

    def test_s7b_3_a_finding_where_the_creation_says_not_yet(self):
        double, runner, outcomes = self.at_the_doors("S7b-3", payment_doors="not_yet")
        self.assertEqual(outcomes["S7b-3"].outcome, H.FAIL, outcomes["S7b-3"].line)
        self.assertEqual(probes_at(runner, "S7b-3"), ["the run road (POST /v1/sets) did not refuse a Bitcoin row as the specification says"])
        self.assertEqual(double.sets, {})

    def test_s7b_2_and_s7b_4_make_no_call_and_are_skipped_by_name_never_passed(self):
        double, runner, outcomes = self.at_the_doors("S7b-2", "S7b-4")
        self.assertEqual((outcomes["S7b-2"].outcome, outcomes["S7b-2"].line), (H.SKIPPED, T.BITCOIN_IMPORT_NOT_WALKED_SENTENCE))
        self.assertEqual((outcomes["S7b-4"].outcome, outcomes["S7b-4"].line), (H.SKIPPED, T.BITCOIN_DEPOSIT_NOT_WALKED_SENTENCE))
        self.assertEqual(calls_at(runner, "S7b-2") + calls_at(runner, "S7b-4"), [], "no shape is sent from memory, and no deposit is typed that never arrived")
        self.assertEqual(runner.findings, [])
        self.assertEqual(runner.bitcoin_summary_lines()[0].split(" Bitcoin stations skipped", 1)[1], ", counted as skipped and never as passed: 2 (S7b-2, S7b-4).")

    def test_a_door_station_resumed_alone_reads_the_estates_standing_first(self):
        double = holding()
        runner = enrolled(double)
        outcome = walk(runner, "S6b")["S6b"]
        self.assertEqual(outcome.outcome, H.PASS, outcome.line)
        self.assertEqual(calls_at(runner, "S6b"), ["GET /v1/aer360/bitcoin", "POST /v1/payees", "GET /v1/payees"])

    def test_every_door_passes_on_one_estate_and_nothing_moved(self):
        double, runner, outcomes = self.at_the_doors(*AFTER_THE_ADDRESS)
        self.assertEqual({s: o.outcome for s, o in outcomes.items()},
                         {"S5b-1": H.PASS, "S5b-2": H.PASS, "S6b": H.PASS, "S7b-1": H.PASS, "S7b-2": H.SKIPPED, "S7b-3": H.PASS, "S7b-4": H.SKIPPED})
        self.assertEqual((double.payees, double.addresses, double.sets, runner.findings), ({}, {}, {}, []))
        self.assertEqual([c.route for c in runner.calls if c.station in BITCOIN_STATIONS and c.route.startswith("POST")], ["POST /v1/payees", "POST /v1/sets/review", "POST /v1/sets"])
        self.assertFalse(any("/submit" in c.route or "/execute" in c.route or "/approve" in c.route or "faucet" in c.route for c in runner.calls), "nothing is submitted, approved or executed, and no faucet is asked")


def whole_leg(double):
    """The whole leg on a fresh estate, as a first run walks it; returns the runner, the outcomes by station and the report's text."""
    runner = runner_on(double, tempfile.mkdtemp(), invite=double.mint_founder_link())
    outcomes = {o.station: o for o in runner.run()}
    path = runner.write_report()
    with open(path, "r", encoding="utf-8") as handle:
        return runner, outcomes, path, handle.read()


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheWholeLegOnAnEstateThatHoldsBitcoin(unittest.TestCase):
    """An estate at catalog version 20, after Spec AER360-BTC-1: the book answers C9B Yes, the charter names bitcoin, the address is shown and read, and every door refuses."""

    @classmethod
    def setUpClass(cls):
        cls.double = BitcoinEstate(currency_spoken_as_code=True)
        cls.runner, cls.outcomes, cls.report_path, cls.report = whole_leg(cls.double)

    def test_s3_answers_c9b_from_the_book_and_names_version_20(self):
        o = self.outcomes["S3"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("policy interview: 26 questions answered", o.line)
        self.assertIn("; the answer book answers catalog version 20, and the estate served 26 question(s), every one known to the book", o.line)
        given = [q for q, _, _, _ in self.runner.facts["answers"]["policy"]]
        self.assertEqual(given, [q.id for q in A.expected_walk("policy")])
        self.assertEqual(self.runner.facts["charter"]["policy"]["heldNetworks"], ["bitcoin-testnet"])

    def test_s3b_reads_the_question_the_read_back_and_the_charter(self):
        o = self.outcomes["S3b"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("the estate asked C9B in the specification's words, its note among them", o.line)
        self.assertIn(B.HELD_READBACK_SANDBOX, o.line)
        self.assertIn('the compiled charter of this sandbox estate carries heldNetworks ["bitcoin-testnet"] and recordedHeldNetworks ["bitcoin"]', o.line)
        self.assertEqual(calls_at(self.runner, "S3b"), [])

    def test_the_address_is_the_funding_wallets_and_the_solana_wallets_say_why_they_show_none(self):
        o = self.outcomes["S5b-1"]
        self.assertEqual(o.outcome, H.PASS, o.line)
        self.assertIn("wallet 1 shows %s, of the form of bitcoin-testnet (tb1q…)" % funding_address(self.double), o.line)
        self.assertIn("wallet 2 shows no address and says why: \"%s\"" % B.SOLANA_KEY_SENTENCE, o.line)
        self.assertEqual(self.outcomes["S5b-2"].outcome, H.PASS, self.outcomes["S5b-2"].line)
        self.assertIn("wallet 1: a reading — historyWhole true; 2 sources answered and agree", self.outcomes["S5b-2"].line)

    def test_every_door_refuses_as_the_clerk_and_two_say_they_were_not_walked(self):
        for station in ("S6b", "S7b-1", "S7b-3"):
            self.assertEqual(self.outcomes[station].outcome, H.PASS, self.outcomes[station].line)
            self.assertIn("BITCOIN_HELD_NOT_PAID, 422", self.outcomes[station].line)
        for station in ("S7b-2", "S7b-4"):
            self.assertEqual(self.outcomes[station].outcome, H.SKIPPED, self.outcomes[station].line)
        self.assertFalse(any(T.is_bitcoin_chain(a["chain"]) for a in self.double.addresses.values()), "no payee stands on a Bitcoin row")
        carried = [i.get("invoiceRef") for s in self.double.sets.values() for i in s["instructions"]]
        self.assertFalse(any(ref in carried for ref in ("HH-B001", "HH-B002")), "no run carries a Bitcoin row")

    def test_the_auditor_reads_the_new_law_back_and_finds_nothing_of_bitcoin(self):
        bitcoin = [(f.station, f.probe) for f in self.runner.findings if f.station in BITCOIN_STATIONS or "C9B" in f.probe or "bitcoin" in f.probe.lower()]
        self.assertEqual(bitcoin, [])
        self.assertNotEqual(self.outcomes["S10"].outcome, H.NOT_RUN)
        self.assertFalse(any(f.station == "S10" and ("the networks held" in f.probe or "read-back (policy) of C9B" in f.probe) for f in self.runner.findings))

    def test_the_report_carries_the_eight_and_prints_the_address_for_a_person(self):
        read_back = H.read_report(self.report_path)
        self.assertEqual({s: read_back["outcomes"][s] for s in BITCOIN_STATIONS},
                         {"S3b": "pass", "S5b-1": "pass", "S5b-2": "pass", "S6b": "pass", "S7b-1": "pass", "S7b-2": "skipped", "S7b-3": "pass", "S7b-4": "skipped"})
        self.assertEqual(len(read_back["outcomes"]), len(H.STATIONS))
        for station in BITCOIN_STATIONS:
            self.assertIn("## %s — %s" % (station, TITLES[station]), self.report)
        self.assertIn("Bitcoin (Spec T32): the address the estate shows for the holding on bitcoin-testnet, for a person: wallet 1 — %s" % funding_address(self.double), self.report)
        self.assertIn("Bitcoin stations skipped, counted as skipped and never as passed: 2 (S7b-2, S7b-4).", self.report)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class TheWholeLegOnAnEstateBeforeBitcoin(unittest.TestCase):
    """The default double, an estate at catalog version 15 with no Bitcoin road: all eight stations skip by name, none passes, and no finding is raised for it."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble(currency_spoken_as_code=True)
        cls.runner, cls.outcomes, cls.report_path, cls.report = whole_leg(cls.double)

    def test_the_eight_are_skipped_and_none_is_passed(self):
        for station in BITCOIN_STATIONS:
            self.assertEqual(self.outcomes[station].outcome, H.SKIPPED, "%s: %s" % (station, self.outcomes[station].line))
        self.assertEqual(self.outcomes["S3b"].line, T.BITCOIN_QUESTION_NOT_ASKED_SENTENCE % ("C9B", SPEC_PROMPT, "Yes"))
        self.assertIn("the estate answers no Bitcoin road (GET /v1/aer360/bitcoin: ", self.outcomes["S5b-1"].line)
        for station in AFTER_THE_ADDRESS:
            self.assertTrue(self.outcomes[station].line.startswith("skipped by name: at S5b-1 the estate answers no Bitcoin road"), self.outcomes[station].line)

    def test_the_stations_that_stood_before_walk_as_they_did(self):
        self.assertIn("policy interview: 25 questions answered", self.outcomes["S3"].line)
        for station in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"):
            self.assertEqual(self.outcomes[station].outcome, H.PASS, self.outcomes[station].line)
        self.assertEqual([(f.station, f.probe) for f in self.runner.findings if f.station in BITCOIN_STATIONS or "C9B" in f.probe], [])
        self.assertEqual([c.route for c in self.runner.calls if c.station in BITCOIN_STATIONS], ["GET /v1/aer360/bitcoin"], "one read, answered that the road is not there")

    def test_the_report_counts_them_as_skipped(self):
        read_back = H.read_report(self.report_path)
        self.assertEqual([read_back["outcomes"][s] for s in BITCOIN_STATIONS], ["skipped"] * 8)
        self.assertIn("Bitcoin stations skipped, counted as skipped and never as passed: 8 (S3b, S5b-1, S5b-2, S6b, S7b-1, S7b-2, S7b-3, S7b-4).", self.report)


class TheDryRunPrintsTheEight(unittest.TestCase):
    def setUp(self):
        self.lines = H.dry_lines()

    def of(self, station):
        return [l for l in self.lines if l.startswith("%s — " % station)]

    def test_each_station_prints_in_its_place(self):
        self.assertEqual([len(self.of(s)) for s in BITCOIN_STATIONS], [1, 2, 2, 2, 2, 1, 2, 1])
        seen = []
        for line in self.lines:
            station = line.split(" — ", 1)[0]
            if station not in seen:
                seen.append(station)
        self.assertEqual(seen, [s for s, _ in H.STATIONS])
        self.assertEqual([s for s, _ in H.STATIONS if s in BITCOIN_STATIONS], list(BITCOIN_STATIONS))
        ids = [s for s, _ in H.STATIONS]
        self.assertEqual((ids[ids.index("S3") + 1], ids[ids.index("S5s") + 1], ids[ids.index("S6s") + 1], ids[ids.index("S7s-3") + 1], ids[ids.index("S7b-4") + 1]),
                         ("S3b", "S5b-1", "S6b", "S7b-1", "S8"))

    def test_the_doors_expect_the_estates_sentence_and_the_two_not_walked_say_why(self):
        expectation = "expect 422 BITCOIN_HELD_NOT_PAID: \"%s\" followed by what the door did not do, matched with the harness's sentence matcher" % SPEC_HELD_NOT_PAID
        for station in ("S6b", "S7b-1", "S7b-3"):
            self.assertIn(expectation, self.of(station)[0], station)
            self.assertIn('sset": "BTC"', self.of(station)[0], "the payee's defaultAsset, a row's asset")
        self.assertEqual(self.of("S7b-2"), ["S7b-2 — [not walked] POST /v1/imports/:importId/review → %s" % T.BITCOIN_IMPORT_NOT_WALKED_SENTENCE])
        self.assertEqual(self.of("S7b-4"), ["S7b-4 — [not walked] POST /v1/deposits → %s" % T.BITCOIN_DEPOSIT_NOT_WALKED_SENTENCE])
        self.assertIn('"amountMinor": "1"', self.of("S7b-1")[0])
        self.assertIn('"idempotencyKey": "aer360-harness-<run>-PB1"', self.of("S7b-3")[0])

    def test_the_reads_say_how_each_answer_is_told_apart(self):
        address, reading = self.of("S5b-1")[0], self.of("S5b-2")[1]
        self.assertTrue(address.startswith("S5b-1 — GET /v1/aer360/bitcoin (as Harriet Founder) → expect whether the estate holds bitcoin"), address)
        self.assertIn("tb1q… on bitcoin-testnet for a sandbox estate, bc1q… on bitcoin for a live one", address)
        self.assertIn(T.BITCOIN_ADDRESS_OPENS_LATER_SENTENCE, address)
        self.assertTrue(reading.startswith("S5b-2 — GET /v1/aer360/bitcoin/wallets/<walletId> (as Harriet Founder)"), reading)
        for words in ("BITCOIN_ROAD_CLOSED (503, naming BITCOIN_SOURCES", "BITCOIN_SOURCES_DISAGREE (503", "BITCOIN_READS_LIMITED (429)", "reported as a silence, FAILED — prerequisite, and never as a pass"):
            self.assertIn(words, reading, words)

    def test_no_line_carries_an_address_of_anyones(self):
        for line in self.lines:
            self.assertNotIn(SPEC_EXAMPLE_ADDRESS, line)
            self.assertEqual([w for w in line.replace('"', " ").split() if T.BITCOIN_ADDRESS_LOOK.match(w)], [], line)


class TheWords(unittest.TestCase):
    """The README and the CHANGELOG say what the stations do, with this spec's number and date."""

    def setUp(self):
        self.readme = read("README.md")
        self.section = self.readme.split("## The estate harness", 1)[1].split("## Harness Real World", 1)[0]

    def test_the_readme_carries_the_spec_t32_paragraph_before_running_it(self):
        title = "**The estate harness learns that an estate holds bitcoin: named in the charter, shown, read through two sources, and refused at every payment door (Spec T32, 14 November 2026).**"
        self.assertIn(title, self.section)
        self.assertLess(self.section.index("(Spec T31, 1 November 2026).**"), self.section.index(title))
        self.assertLess(self.section.index(title), self.section.index("**Running it.**"))
        paragraph = self.section.split(title, 1)[1].split("**Running it.**", 1)[0]
        for words in ("Spec AER360-BTC-1", "8bff50e", "It was read from the specification and not from the estate's code", "`CATALOG_VERSION_ANSWERED = 20`", "`ADDED_IN_V20`",
                      "*S3b The charter names bitcoin*", "*S5b-1 Bitcoin address*", "*S5b-2 Bitcoin reading*", "*S6b A payee in bitcoin*", "*S7b-1 A payment set in bitcoin*",
                      "*S7b-3 A payment run in bitcoin*", "*S7b-2 An imported file in bitcoin*", "*S7b-4 A deposit in bitcoin*", "`GET /v1/aer360/bitcoin`",
                      "`GET /v1/aer360/bitcoin/wallets/<walletId>`", "`heldNetworks`", "`BITCOIN_HELD_NOT_PAID`", "`BITCOIN_ROAD_CLOSED`", "`BITCOIN_SOURCES_DISAGREE`",
                      "`BITCOIN_READS_LIMITED`", SPEC_HELD_NOT_PAID, "*FAILED — prerequisite: a Bitcoin source was silent*", "never invents an address and never asks a faucet",
                      "count them as skipped, never as passed", "CONTESTED", "285 → 299 lines", "`tests/bitcoin_double.py`", "`tests/test_the_estate_harness_learns_bitcoin.py`",
                      "`tests/fixtures/aer360-version-20-added.json`"):
            self.assertIn(words, paragraph, words)

    def test_the_readme_names_every_bitcoin_station_among_the_stations(self):
        stations = self.section.split("**The stations.**", 1)[1].split("\n", 1)[0]
        for station in BITCOIN_STATIONS:
            self.assertIn("%s %s" % (station, TITLES[station]), stations, station)

    def test_the_readme_says_in_one_sentence_that_the_corridors_money_series_gain_nothing(self):
        sentence = ("Nothing was added to these money series when the estate harness learnt that an estate holds bitcoin (Spec T32, 14 November 2026): the gate's paying road "
                    "for Bitcoin is merged and not yet in service, so the series still run on ethereum, arbitrum and base alone.")
        guard = [line for line in self.readme.splitlines() if line.startswith("**The chain guard.**")]
        self.assertEqual(len(guard), 1)
        self.assertTrue(guard[0].endswith(sentence), guard[0][-400:])
        self.assertEqual(self.readme.count("not yet in service"), 1, "said once")

    def test_the_changelog_records_spec_t32_first_and_names_every_change(self):
        text = read("CHANGELOG.md")
        title = "## Spec T32 — The estate harness learns that an estate holds bitcoin (14 November 2026)"
        self.assertEqual(text.index("## "), text.index(title), "the newest entry first")
        entry = text.split(title, 1)[1].split("## Spec T31", 1)[0]
        for words in ("`aer360_tables.py`", "`aer360_answers.py`", "`aer360_harness.py`", "`tests/bitcoin_double.py` (new)", "`tests/test_the_estate_harness_learns_bitcoin.py` (new)",
                      "`tests/fixtures/aer360-version-20-added.json`", "`CATALOG_VERSION_ANSWERED = 20`", "`ADDED_IN_V20`", "`audit_bitcoin_named`", "`read_bitcoin_standing`",
                      "`read_bitcoin_wallet`", "`judge_held_not_paid`", "`skip_the_bitcoin_stations`", "`bitcoin_summary_lines`", "`BITCOIN_SOURCES_SILENT`", "285 → 299",
                      "8bff50e", "**Not run by the builder.**", "rule 189", "CONTESTED", "Not touched", "No dependency added", "No secret"):
            self.assertIn(words, entry, words)


if __name__ == "__main__":
    unittest.main()
