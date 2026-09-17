"""Every test id in series.py exists in the Series document, and every test the document names is in exactly
one of the three lists: run by the harness, paused for, or left to a person (Spec T1 §4, §11). The document
is version 1.2 of 17 September 2026, sixty-three tests (Spec T6); the fixture is that document with two
amendment lines and A4, A5 and A6 in the wording of Specs T2 and T3, and nothing else changed."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import series as S  # noqa: E402
import tables as T  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "series-1.2.md")
ORIGINAL = os.path.expanduser(
    "~/Downloads/AER Connect Corridor Acceptance Test Series before Sale, version 1.2, 17 September 2026.md")

# The sixty-three ids of version 1.2, in the document's order (Spec T6 §1).
IDS_1_2 = [
    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13", "D14", "D15", "D16",
    "E1", "E2", "E3", "E4", "E5", "E6",
    "F1", "F2", "F3", "F4", "F5", "F6",
    "G1", "G2", "G3", "G4",
    "H1", "H2", "H3", "H4", "H5", "H6", "H7",
]

# What the fixture carries that the document does not (Spec T6 §1, §2): two amendment lines after the title
# and before the version line, and A4, A5 and A6 in the wording Specs T2 and T3 gave the harness, which is
# still the harness's contract (corridor_harness.py runs it and tests/test_series_a.py proves it).
AMENDMENT_LINES = [
    "**Amended 14 September 2026: A4, A5, A6 (Spec T2).**",
    "**Amended 15 September 2026: A4 (Spec T3).**",
]
AMENDED_TESTS = ["A4", "A5", "A6"]
TITLE = "# AER Connect Corridor — Acceptance Test Series before Sale"
VERSION_LINE_OPENS = "**Version 1.2, 17 September 2026, Melbourne.**"


def ids_in(text):
    return re.findall(r"\*\*([A-H]\d{1,2})\.", text)


def test_id_of(paragraph):
    """The id a test paragraph opens with: '**A4. The Wallet names its rails.** …' gives 'A4'; else None."""
    found = re.match(r"\*\*([A-H]\d{1,2})\.", paragraph)
    return found.group(1) if found else None


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


class SeriesIdsTest(unittest.TestCase):
    def setUp(self):
        self.document = read(FIXTURE)
        self.document_ids = ids_in(self.document)
        self.paragraphs = self.document.split("\n\n")

    def test_the_document_names_sixty_three_tests_in_order(self):
        self.assertEqual(len(self.document_ids), 63)
        self.assertEqual(len(set(self.document_ids)), 63)
        self.assertEqual(self.document_ids, IDS_1_2, "the fixture's ids are version 1.2's, in the document's order")

    def test_none_missing_and_none_invented(self):
        self.assertEqual(list(S.BY_ID), self.document_ids, "series.py holds the document's ids, in the document's order")
        self.assertEqual(len(S.TESTS), 63)

    def test_each_test_is_in_exactly_one_list(self):
        harness, pauses, person = set(S.HARNESS_RUNS), set(S.PAUSES), set(S.LEFT_TO_A_PERSON)
        self.assertEqual(harness | pauses | person, set(self.document_ids))
        self.assertEqual(harness & pauses, set())
        self.assertEqual(harness & person, set())
        self.assertEqual(pauses & person, set())
        self.assertEqual(len(S.HARNESS_RUNS) + len(S.PAUSES) + len(S.LEFT_TO_A_PERSON), 63)

    def test_the_lists_are_spec_t1_section_4s_with_spec_t6s_three(self):
        self.assertEqual(set(S.PAUSES), {"B1", "B2", "B3", "B4", "B5", "B8", "C5", "C6", "D6", "D9", "D13", "D14", "E6", "H2", "H3"})
        self.assertEqual(set(S.LEFT_TO_A_PERSON), {"A7", "A8", "B6", "B7", "F1", "F5", "F6", "G1", "G2", "G3", "G4", "H1", "H4", "H6", "H7"})
        self.assertEqual(set(S.HARNESS_RUNS), {"A1", "A2", "A3", "A4", "A5", "A6", "C1", "C2", "C3", "C4", "C7", "C8",
                                               "D1", "D2", "D3", "D4", "D5", "D7", "D8", "D10", "D11", "D12", "D15", "D16",
                                               "E1", "E2", "E3", "E4", "E5", "F2", "F3", "F4", "H5"})
        # Every test that pauses for a passkey is on the spec's pause list, plus D7, whose pool-address save is a
        # passkey step inside a test the spec lists among those the harness runs by itself.
        pausing = {t.id for t in S.TESTS if any(isinstance(step, S.Pause) for step in t.steps)}
        self.assertEqual(pausing, set(S.PAUSES) | {"D7"})

    def test_h5_h6_and_h7_are_each_in_exactly_one_list(self):
        """Spec T6 §3: placed by the reading that placed H1 to H4. H5 has no form step ("there is none to set")
        and is one walk of the corridor as the Payer, C1's own, so the harness runs it. H6 needs an agent created
        before 15 September and not re-saved, which the run file does not name, and two readings of the account
        page, which the harness does not read (Spec T1 §9), so it is a person's, as H4 and B6 are. H7's second
        sentence is the engine's at mint, read on P0 as F5's is, and the harness never attempts a build after a
        refusal (Spec T1 §5), so it is a person's too."""
        lists = {"harness": set(S.HARNESS_RUNS), "pauses": set(S.PAUSES), "person": set(S.LEFT_TO_A_PERSON)}
        placed = {tid: [name for name, ids in lists.items() if tid in ids] for tid in ("H5", "H6", "H7")}
        self.assertEqual(placed, {"H5": ["harness"], "H6": ["person"], "H7": ["person"]})
        h5 = S.BY_ID["H5"]
        self.assertEqual((h5.who, h5.agent, h5.series), (S.HARNESS, "payer", "H"))
        self.assertTrue(h5.moves_money)
        self.assertEqual(h5.figure_usd, 1)
        self.assertEqual([type(step) for step in h5.steps], [S.Walk], "one walk and no form step: there is no period hold to set")
        walk = h5.steps[0]
        self.assertEqual((walk.expect, walk.legs), (S.ALLOWED, 1))
        self.assertEqual((walk.action.action, walk.action.chain, walk.action.asset, walk.action.amount_usd, walk.action.to_address),
                         ("transfer_stable", "arbitrum", "USDC", 1, S.OWNER))
        for tid in ("H6", "H7"):
            self.assertEqual(S.BY_ID[tid].who, S.PERSON, tid)
            self.assertEqual(S.BY_ID[tid].steps, [], tid)
            self.assertFalse(S.BY_ID[tid].moves_money, tid)

    def test_series_h_and_d13_walk_what_version_1_2_says(self):
        """H2 runs a fourth trade at exactly the figure, H3 moves the per-trade figure on the Payer and expects no
        hold, and D13 sets ask-me-first to the pre-filled ten rather than clearing it; there is no period total."""
        h2 = S.BY_ID["H2"]
        walks = [step for step in h2.steps if isinstance(step, S.Walk)]
        self.assertEqual([walk.expect for walk in walks], [S.ALLOWED, S.ALLOWED, S.REFUSED, S.ALLOWED])
        self.assertTrue(all(walk.action.action == "trade" and walk.action.amount_usd == 5 for walk in walks))
        pauses = [step.text for step in h2.steps if isinstance(step, S.Pause)]
        self.assertEqual(len(pauses), 3)
        self.assertIn("'per day' to 12 dollars", pauses[0])
        self.assertIn("'per day' to exactly 15 dollars", pauses[1])
        self.assertIn("'per day' back to 100 dollars", pauses[2])
        h3 = S.BY_ID["H3"]
        self.assertEqual(h3.agent, "payer")
        walks = [step for step in h3.steps if isinstance(step, S.Walk)]
        self.assertEqual([walk.expect for walk in walks], [S.REFUSED, S.ALLOWED])
        self.assertTrue(all(walk.action.action == "transfer_stable" and walk.action.amount_usd == 5 for walk in walks))
        pauses = [step.text for step in h3.steps if isinstance(step, S.Pause)]
        self.assertEqual(len(pauses), 3)
        self.assertIn("'per trade' to 4 dollars", pauses[0])
        self.assertIn("'per trade' to 5 dollars", pauses[1])
        self.assertIn("'per trade' back to 20 dollars", pauses[2])
        d13 = S.BY_ID["D13"]
        self.assertEqual([step.expect for step in d13.steps if isinstance(step, S.Walk)], [S.HELD])
        self.assertIn("ten dollars", [step for step in d13.steps if isinstance(step, S.Pause)][0].text)
        every_pause = " ".join(step.text for test in S.TESTS for step in test.steps if isinstance(step, S.Pause))
        self.assertNotIn("period total", every_pause, "the 1.2 form has no period total, so no pause asks for one")
        self.assertNotIn("blank", every_pause, "nothing is cleared: the owner's figure is the rule")
        for tid, title in (("B6", "The page reads the document back"), ("D13", "The hold at the pre-filled figure"),
                           ("H1", "The day resets at midnight UTC"), ("H2", "The per-day figure counts the trade in hand"),
                           ("H3", "A per-trade figure is the figure")):
            self.assertEqual(S.BY_ID[tid].title, title)
            self.assertTrue(S.BY_ID[tid].text.startswith("**%s. %s.**" % (tid, title)), tid)
        self.assertEqual(S.BY_ID["B6"].rule, "Proves Rules 21 and 27.")
        self.assertEqual(S.BY_ID["H1"].rule, "Proves Rule 26's day.")

    def test_every_text_is_the_documents_own_paragraph(self):
        for test in S.TESTS:
            self.assertIn(test.text, self.document, "%s's text is not verbatim from the Series" % test.id)
            self.assertEqual(test_id_of(test.text), test.id, "%s's text opens with its own id" % test.id)

    def test_every_pinned_address_is_in_the_document(self):
        for key, row in T.PINNED.items():
            self.assertIn(row.address, self.document, "%s (%s) is not in the Series" % (key, row.address))

    def test_the_series_figures(self):
        self.assertEqual(T.TRADE_USD, 5)
        self.assertEqual(T.PAYMENT_USD, 1)
        self.assertEqual(S.BY_ID["D13"].figure_usd, 12)
        self.assertEqual(S.BY_ID["C4"].figure_usd, 25)
        self.assertEqual(S.BY_ID["H2"].figure_usd, 5)
        self.assertEqual(S.BY_ID["H3"].figure_usd, 5)
        self.assertEqual(S.BY_ID["H5"].figure_usd, 1)

    def test_the_fixture_is_version_1_2_with_two_amendment_lines(self):
        """Spec T6 §1: the two lines sit after the title and before the version line; the Spec T5 line is gone,
        because version 1.2 itself names no tester; A4, A5 and A6 carry Specs T2's and T3's words."""
        self.assertEqual(self.paragraphs[0], TITLE)
        self.assertEqual(self.paragraphs[1:3], AMENDMENT_LINES)
        self.assertTrue(self.paragraphs[3].startswith(VERSION_LINE_OPENS), self.paragraphs[3][:80])
        self.assertEqual([p for p in self.paragraphs if p.startswith("**Amended")], AMENDMENT_LINES, "exactly two amendment lines")
        self.assertNotIn("**Amended 17 September 2026", self.document, "Spec T5's line is the document's own wording now")
        self.assertIn("Version 1.2 amends version 1.1 in wording only, so that the document names no tester", self.document)
        self.assertIn("Two testers run the series independently, each with one Trader and one Payer", self.document)
        # Specs T2 and T3's wording, which the harness still runs (Spec T6 §1).
        self.assertIn("MCP Police carries no tool called `can_sign`, so the hash is read from the Wallet", self.document)
        self.assertIn("The token balances are compared with the Wallet's statement where it makes one", self.document)
        self.assertIn("\"basis points\" on its own is not counted", self.document)
        self.assertNotIn("Claude calls `can_sign` or `assignment_status`", self.document)

    def test_the_fixture_carries_version_1_1s_amendments_and_1_2s_wording(self):
        for words in ("## 10. Series H — the two figures and the UTC day",
                      "**B6. The page reads the document back.** After B3 and B4, read the mandate table aloud with the screen "
                      "reader: chains, assets, per trade, per day, ask me first, transactions per day, and the list.",
                      "**D13. The hold at the pre-filled figure.**",
                      "**H1. The day resets at midnight UTC.**",
                      "**H2. The per-day figure counts the trade in hand.**",
                      "**H3. A per-trade figure is the figure.**",
                      "**H5. Ask me first alone is a complete discretion.**",
                      "**H6. The weekly figure is gone from every judge.**",
                      "**H7. Police and the engine count alike.**",
                      "There is no weekly box and no period total on the form",
                      "H2, H3, H5, H6 and H7 pass, with H1 and H4 read once",
                      "(one tester's listed destination `0xfec697fc2D4323aE7618BFF2347C01E29653FB57`, and the other tester's equivalent)"):
            self.assertIn(words, self.document)
        for gone in ("**H1. The daily count resets.**", "**H2. The per-day ceiling.**", "**H3. The period total holds.**",
                     "**D13. The hold at the Trader's default.**", "## 10. Series H — over a day and a week", "per week at 300",
                     "**Version 1.0, 13 September 2026", "**Version 1.1, 15 September 2026"):
            self.assertNotIn(gone, self.document)

    def test_the_original_in_downloads_agrees_if_present(self):
        """The fixture is version 1.2 (Spec T6 §2): the two amendment lines and A4, A5 and A6 in Specs T2's and
        T3's wording are the only bytes that differ, counted and named; every other paragraph of the document is
        in the fixture verbatim, in the document's order, and every test id in the same order."""
        if not os.path.exists(ORIGINAL):
            self.skipTest("the Series document is not in ~/Downloads on this machine")
        original = read(ORIGINAL)
        theirs = original.split("\n\n")
        self.assertEqual(ids_in(original), self.document_ids, "every test id of 1.2 is in the fixture, in the same order")
        added = [p for p in self.paragraphs if p not in theirs]
        removed = [p for p in theirs if p not in self.paragraphs]
        self.assertEqual(added[:2], AMENDMENT_LINES, "the two amendment lines are the first paragraphs the document lacks")
        self.assertEqual([test_id_of(p) for p in added[2:]], AMENDED_TESTS,
                         "A4, A5 and A6 in Spec T2's and T3's wording are the only other paragraphs the document lacks")
        self.assertEqual([test_id_of(p) for p in removed], AMENDED_TESTS,
                         "the document's own A4, A5 and A6 are the only paragraphs the fixture lacks")
        self.assertEqual((len(added), len(removed)), (5, 3), "two lines and three paragraphs, and nothing else")
        for ours, docs in zip(added[2:], removed):
            self.assertEqual(test_id_of(ours), test_id_of(docs))
            self.assertNotEqual(ours, docs)
        # Take the two lines out and put the document's three paragraphs back: the document, byte for byte.
        theirs_for_ours = dict(zip(added[2:], removed))
        rebuilt = "\n\n".join(theirs_for_ours.get(p, p) for p in self.paragraphs if p not in AMENDMENT_LINES)
        self.assertEqual(rebuilt, original, "the fixture is the document with the two lines added and three paragraphs amended, and nothing else")


if __name__ == "__main__":
    unittest.main()
