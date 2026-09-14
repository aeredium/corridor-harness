"""The sentence matcher: Guide section 10's ellipses and angle brackets are wildcards (Spec T1 §7, §11)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

# One realistic answer per kind of sentence in Guide section 10, as a door would say it.
REALISTIC = {
    "destination": [
        "This action names no destination: transfer_stable needs a to_address before MCP Police can judge it.",
        "The destination 0x000000000000000000000000000000000000dEaD is not on this agent’s list; add it under Set limits.",
    ],
    "venue": ["The venue contract 0x32226588378236Fd0c7c4053999F88aC0e5cAc77 on arbitrum is not on this agent’s list."],
    "best_direct": [
        "best_direct may choose uniswap_v3, whose contract 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45 on arbitrum is not "
        "on this agent’s list; list it, or remove uniswap_v3 from the exchanges this agent may use."
    ],
    "hold": ["owner approval required before ticket can be minted: 3.00 USD meets the ask-me-first figure of 2.00 USD."],
    "allowance": [
        "the dry-run failed on arbitrum: execution reverted: TRANSFER_FROM_FAILED",
        "the dry-run failed on arbitrum: ERC20: insufficient allowance for the router",
    ],
    "gas": ["signing address 0x1234567890abcdef1234567890abcdef12345678 has 0 wei native balance; need at least 21000000000000 wei for gas on arbitrum."],
    "to_asset": ["a trade must name the asset it buys in to_asset: USDC, USDT, WETH or a token address."],
    "curve": ["curve on arbitrum has no pool holding both USDC and USDT that this door could quote."],
}


class MatcherTest(unittest.TestCase):
    def test_every_section_10_sentence_matches_a_realistic_answer(self):
        for row in S.GUIDE_SECTION_10:
            answers = REALISTIC[row["kind"]]
            self.assertTrue(any(h.matches_sentence(row["sentence"], a) for a in answers),
                            "no realistic %s answer matched %r" % (row["kind"], row["sentence"]))

    def test_does_not_match_a_sentence_of_a_different_kind(self):
        for row in S.GUIDE_SECTION_10:
            for kind, answers in REALISTIC.items():
                if kind == row["kind"]:
                    continue
                for answer in answers:
                    self.assertFalse(h.matches_sentence(row["sentence"], answer),
                                     "%r wrongly matched the %s answer %r" % (row["sentence"], kind, answer))

    def test_ellipses_and_angle_brackets_are_wildcards(self):
        pattern = "best_direct may choose <exchange>, whose contract … is not on this agent's list; list it, or remove <exchange>…"
        self.assertTrue(h.matches_sentence(pattern, REALISTIC["best_direct"][0]))
        self.assertTrue(h.matches_sentence("the dry-run failed on <chain>: … insufficient allowance / TRANSFER_FROM_FAILED",
                                           "the dry-run failed on base: execution reverted: TRANSFER_FROM_FAILED"))
        self.assertFalse(h.matches_sentence("the dry-run failed on <chain>: … insufficient allowance / TRANSFER_FROM_FAILED",
                                            "the dry-run failed on base: execution reverted: STF"))

    def test_curly_and_straight_quotes_and_case_are_one(self):
        self.assertTrue(h.matches_sentence("The destination … is not on this agent's list",
                                           "the destination 0x1 is not on this agent’s list"))
        self.assertTrue(h.matches_sentence("owner approval required before ticket can be minted",
                                           "Owner Approval Required Before Ticket Can Be Minted"))

    def test_matches_inside_a_json_body(self):
        body = json.dumps({"verdict": "deny", "reason": "denied",
                           "sentence": "The destination 0x000000000000000000000000000000000000dEaD is not on this agent’s list"})
        self.assertTrue(h.matches_sentence(S.DESTINATION_SENTENCE, body))
        self.assertFalse(h.matches_sentence(S.HOLD_SENTENCE, body))

    def test_the_series_other_sentences(self):
        self.assertTrue(h.matches_sentence(S.NOT_WIRED_SENTENCE,
                                           "this door trades directly on uniswap_v3, pancakeswap_v3, curve, best_direct; aerodrome is not yet wired to it."))
        self.assertTrue(h.matches_sentence(S.NOT_STABLECOIN_SENTENCE,
                                           "WETH is not a stablecoin this door transfers on arbitrum; it transfers USDC, USDT, PYUSD and EURC."))
        self.assertFalse(h.matches_sentence(S.NOT_WIRED_SENTENCE, REALISTIC["hold"][0]))

    def test_guide_sentence_for_names_the_row(self):
        row = h.guide_sentence_for(REALISTIC["venue"][0])
        self.assertIsNotNone(row)
        self.assertEqual(row["kind"], "venue")
        self.assertEqual(row["source"], "Owner's Guide v1.1 §10")
        self.assertIsNone(h.guide_sentence_for("something the guide never said"))

    def test_section_10_has_the_guides_nine_sentences(self):
        self.assertEqual(len(S.GUIDE_SECTION_10), 9)


if __name__ == "__main__":
    unittest.main()
