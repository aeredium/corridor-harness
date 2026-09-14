"""
A6 pins the fee, not the word (Spec T2 §3).

The old pin counted "basis points" anywhere in `tools/list` and found it twice, in MCP
Police's own `check_action` schema: `slippage_bps` "Declared maximum slippage, in basis
points" and `price_deviation_bps` "Oracle-versus-execution price deviation, in basis
points". Neither is the fee. The pin was wrong, not the corridor.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def read(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as handle:
        return handle.read()


class FeePinTest(unittest.TestCase):
    def test_the_slippage_schema_counts_nothing(self):
        tools = read("tools-list-slippage.json")
        self.assertEqual(tools.count("in basis points"), 2, "the fixture is the door's own schema, twice")
        self.assertEqual(h.fee_words_found(tools), 0, h.fee_word_counts(tools))

    def test_a_tool_list_that_advertises_the_fee_counts_one(self):
        tools = read("tools-list-advertises-the-fee.json")
        self.assertEqual(tools.count("in basis points"), 2, "the same slippage schema is still there")
        self.assertEqual(h.fee_words_found(tools), 1, h.fee_word_counts(tools))
        self.assertEqual(h.fee_word_counts(tools)["0.05%"], 1)

    def test_a_tool_list_that_names_sweeptokenwithfee_counts_one(self):
        tools = read("tools-list-sweeptokenwithfee.json")
        self.assertEqual(tools.count("in basis points"), 2, "the same slippage schema is still there")
        self.assertEqual(h.fee_words_found(tools), 1, h.fee_word_counts(tools))
        self.assertEqual(h.fee_word_counts(tools)["sweepTokenWithFee"], 1)

    def test_each_pinned_word_counts_on_its_own(self):
        self.assertEqual(h.fee_words_found('{"x": "five basis points"}'), 1)
        self.assertEqual(h.fee_words_found('{"x": "5 bps"}'), 1)
        self.assertEqual(h.fee_words_found('{"fee_recipient": "0x…"}'), 1)
        self.assertEqual(h.fee_words_found('{"feeRecipient": "0x…"}'), 1)
        self.assertEqual(h.fee_words_found("The fee is taken on trades."), 1)

    def test_fee_is_counted_as_a_whole_word(self):
        self.assertEqual(h.fee_word_counts("coffee feeble")["fee"], 0, "a word that merely contains fee is not the fee")
        self.assertEqual(h.fee_word_counts("Fee")["fee"], 1, "case does not hide it")
        # sweepTokenWithFee, fee_recipient and feeRecipient each carry a word character beside
        # "fee", so none of them is caught by the whole word, and each is pinned in its own right.
        for carrier in ("sweepTokenWithFee", "fee_recipient", "feeRecipient"):
            self.assertEqual(h.fee_word_counts(carrier)["fee"], 0, carrier)
            self.assertEqual(h.fee_words_found(carrier), 1, carrier)

    def test_the_fee_is_caught_inside_a_longer_identifier(self):
        """Only `fee` is a whole word; the rest are counted as written, wherever they sit."""
        self.assertEqual(h.count_fee_word("sweepTokenWithFeeAndUnwrap", "sweepTokenWithFee"), 1)
        self.assertEqual(h.count_fee_word("feeRecipientAddress", "feeRecipient"), 1)
        self.assertEqual(h.count_fee_word("fee_recipient_address", "fee_recipient"), 1)
        self.assertEqual(h.fee_words_found('{"feeRecipientAddress": "0x…"}'), 1)

    def test_a_figure_is_not_counted_inside_a_longer_figure(self):
        """`5 bps` is the fee; the `15 bps` of a slippage cap is the prose A6 stopped counting."""
        self.assertEqual(h.count_fee_word("a 15 bps slippage cap", "5 bps"), 0)
        self.assertEqual(h.count_fee_word("a 2.5 bps cap", "5 bps"), 0)
        self.assertEqual(h.count_fee_word("a 5 bps cut", "5 bps"), 1)
        self.assertEqual(h.count_fee_word("price is 10.05% today", "0.05%"), 0)
        self.assertEqual(h.count_fee_word("a 0.05% cut", "0.05%"), 1)
        self.assertEqual(h.fee_words_found("Declared maximum slippage, 15 bps, in basis points"), 0)

    def test_the_phrase_basis_points_alone_is_no_longer_pinned(self):
        self.assertNotIn("basis points", S.FEE_WORDS)
        self.assertEqual(h.fee_words_found("Declared maximum slippage, in basis points"), 0)

    def test_a6_pins_these_words_and_still_wants_the_trading_fee_on_terms(self):
        step = S.BY_ID["A6"].steps[0]
        self.assertEqual(tuple(step.absent), S.FEE_WORDS)
        self.assertEqual(list(step.pages), ["/guide", "/account", "tools/list"])
        self.assertEqual(dict(step.present_on), {"/terms": ["trading fee"]})
        self.assertEqual(h.counts_for("Our trading fee is stated here.", ["trading fee"]), {"trading fee": 1})


if __name__ == "__main__":
    unittest.main()
