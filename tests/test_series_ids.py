"""Every test id in series.py exists in the Series document, and every test the document names is in exactly
one of the three lists: run by the harness, paused for, or left to a person (Spec T1 §4, §11)."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import series as S  # noqa: E402
import tables as T  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "series-1.0.md")
ORIGINAL = os.path.expanduser(
    "~/Downloads/AER Connect Corridor Acceptance Test Series before Sale, version 1.0, 13 September 2026.md")


def ids_in(text):
    return re.findall(r"\*\*([A-H]\d{1,2})\.", text)


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


class SeriesIdsTest(unittest.TestCase):
    def setUp(self):
        self.document = read(FIXTURE)
        self.document_ids = ids_in(self.document)

    def test_the_document_names_sixty_tests(self):
        self.assertEqual(len(self.document_ids), 60)
        self.assertEqual(len(set(self.document_ids)), 60)

    def test_none_missing_and_none_invented(self):
        self.assertEqual(list(S.BY_ID), self.document_ids, "series.py holds the document's ids, in the document's order")

    def test_each_test_is_in_exactly_one_list(self):
        harness, pauses, person = set(S.HARNESS_RUNS), set(S.PAUSES), set(S.LEFT_TO_A_PERSON)
        self.assertEqual(harness | pauses | person, set(self.document_ids))
        self.assertEqual(harness & pauses, set())
        self.assertEqual(harness & person, set())
        self.assertEqual(pauses & person, set())

    def test_the_lists_are_spec_t1_section_4s(self):
        self.assertEqual(set(S.PAUSES), {"B1", "B2", "B3", "B4", "B5", "B8", "C5", "C6", "D6", "D9", "D13", "D14", "E6", "H2", "H3"})
        self.assertEqual(set(S.LEFT_TO_A_PERSON), {"A7", "A8", "B6", "B7", "F1", "F5", "F6", "G1", "G2", "G3", "G4", "H1", "H4"})
        self.assertEqual(set(S.HARNESS_RUNS), {"A1", "A2", "A3", "A4", "A5", "A6", "C1", "C2", "C3", "C4", "C7", "C8",
                                               "D1", "D2", "D3", "D4", "D5", "D7", "D8", "D10", "D11", "D12", "D15", "D16",
                                               "E1", "E2", "E3", "E4", "E5", "F2", "F3", "F4"})
        # Every test that pauses for a passkey is on the spec's pause list, plus D7, whose pool-address save is a
        # passkey step inside a test the spec lists among those the harness runs by itself.
        pausing = {t.id for t in S.TESTS if any(isinstance(step, S.Pause) for step in t.steps)}
        self.assertEqual(pausing, set(S.PAUSES) | {"D7"})

    def test_every_text_is_the_documents_own_paragraph(self):
        for test in S.TESTS:
            self.assertIn(test.text, self.document, "%s's text is not verbatim from the Series" % test.id)

    def test_every_pinned_address_is_in_the_document(self):
        for key, row in T.PINNED.items():
            self.assertIn(row.address, self.document, "%s (%s) is not in the Series" % (key, row.address))

    def test_the_series_figures(self):
        self.assertEqual(T.TRADE_USD, 5)
        self.assertEqual(T.PAYMENT_USD, 1)
        self.assertEqual(S.BY_ID["D13"].figure_usd, 12)
        self.assertEqual(S.BY_ID["C4"].figure_usd, 25)

    def test_the_fixture_says_it_is_amended(self):
        self.assertIn("**Amended 14 September 2026: A4, A5, A6 (Spec T2).**", self.document)

    def test_the_original_in_downloads_agrees_if_present(self):
        """The fixture is the Series as amended (Spec T2 §8): the three amended paragraphs are the
        only bytes that changed, and every other paragraph of the original is still in it verbatim."""
        if not os.path.exists(ORIGINAL):
            self.skipTest("the Series document is not in ~/Downloads on this machine")
        original = read(ORIGINAL)
        self.assertEqual(ids_in(original), self.document_ids, "no test id was added, removed or moved")
        amended, kept = [], 0
        for paragraph in original.split("\n\n"):
            if paragraph.startswith(("**A4.", "**A5.", "**A6.")):
                amended.append(paragraph)
                self.assertNotIn(paragraph, self.document, "an amended paragraph was left unamended")
            else:
                kept += 1
                self.assertIn(paragraph, self.document, "the fixture changed a paragraph Spec T2 did not amend")
        self.assertEqual(len(amended), 3, "A4, A5 and A6 are the three paragraphs amended")
        self.assertGreater(kept, 60)


if __name__ == "__main__":
    unittest.main()
