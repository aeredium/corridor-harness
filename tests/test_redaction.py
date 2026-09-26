"""Redaction: the bearer and a receipt secret go, everything else stays byte for byte (Spec T1 §6, §10, §11)."""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402

BEARER = "hZ3l0m9Qw2Xy8Kp4Rt6Vb1Nn5Cc7Ff0Gg2Hh4Jj6Ll8Mm"
RECEIPT = "police-receipt-4c1d0c4e-1b53-4a6e-9c2a-8b1f0e7d6a55"

RECORD = {
    "test_id": "C1",
    "kind": "tools/call",
    "tool": "wallet.build_transaction",
    "headers": {"Authorization": "Bearer " + BEARER, "Accept": "application/json, text/event-stream"},
    "arguments": {
        "name": "wallet.build_transaction",
        "arguments": {"action": "transfer_stable", "chain": "arbitrum", "asset": "USDC", "amount_usd": 1,
                      "to_address": "0xfec697fc2D4323aE7618BFF2347C01E29653FB57", "wallet_id": "6b1c…", "police_receipt": RECEIPT},
    },
    "answer": {
        "jsonrpc": "2.0", "id": 7,
        "result": {
            "content": [{"type": "text", "text": json.dumps({"verdict": "allow", "receipt": {"issued": True, "token": RECEIPT, "nonce": "n-1", "expires_at": "2026-09-13T12:00:00Z"}})}],
            "structuredContent": {"verdict": "allow", "receipt": {"issued": True, "token": RECEIPT, "nonce": "n-1"}},
        },
    },
    "http_status": 200,
    "round_trip_ms": 412,
}


class RedactionTest(unittest.TestCase):
    def test_bearer_and_receipt_secret_are_removed_and_nothing_else_moves(self):
        before = copy.deepcopy(RECORD)
        secrets = [BEARER] + h.secret_values(RECORD)
        after = h.redact(RECORD, secrets)
        # what changed
        self.assertEqual(after["headers"]["Authorization"], h.REDACTED)
        self.assertEqual(after["arguments"]["arguments"]["police_receipt"], h.REDACTED)
        self.assertEqual(after["answer"]["result"]["structuredContent"]["receipt"]["token"], h.REDACTED)
        self.assertNotIn(RECEIPT, json.dumps(after))
        self.assertNotIn(BEARER, json.dumps(after))
        # what did not: rebuild the expectation by hand and compare byte for byte
        expected = copy.deepcopy(before)
        expected["headers"]["Authorization"] = h.REDACTED
        expected["arguments"]["arguments"]["police_receipt"] = h.REDACTED
        expected["answer"]["result"]["structuredContent"]["receipt"]["token"] = h.REDACTED
        expected["answer"]["result"]["content"][0]["text"] = before["answer"]["result"]["content"][0]["text"].replace(RECEIPT, h.REDACTED)
        self.assertEqual(json.dumps(after, sort_keys=True), json.dumps(expected, sort_keys=True))
        # the input itself was not touched
        self.assertEqual(RECORD, before)

    def test_nonce_and_ids_are_kept(self):
        after = h.redact(RECORD, [BEARER] + h.secret_values(RECORD))
        self.assertEqual(after["answer"]["result"]["structuredContent"]["receipt"]["nonce"], "n-1")
        self.assertEqual(after["arguments"]["arguments"]["wallet_id"], "6b1c…")
        self.assertEqual(after["round_trip_ms"], 412)

    def test_a_ticket_secret_and_the_refresh_token_are_redacted(self):
        record = {"ticket": {"id": "t-1", "token": "ticket-secret-value-1234"}, "refresh_token": "r" * 43, "code": "receipt_missing"}
        after = h.redact(record)
        self.assertEqual(after["ticket"]["token"], h.REDACTED)
        self.assertEqual(after["ticket"]["id"], "t-1")
        self.assertEqual(after["refresh_token"], h.REDACTED)
        self.assertEqual(after["code"], "receipt_missing", "a reason code is evidence, not a secret")

    def test_empty_secret_fields_are_left_as_they_are(self):
        self.assertEqual(h.redact({"receipt": {"token": None, "issued": False}}), {"receipt": {"token": None, "issued": False}})

    def test_the_consents_secrets_are_secret_keys_and_code_has_two_meanings(self):
        """Spec T21 §6: SECRET_KEYS gains the consent's eight; an OAuth code beside its state is a secret, a reason code is evidence."""
        for key in ("pem", "signature", "cookie", "set-cookie", "csrftoken", "code", "handle", "response"):
            self.assertIn(key, h.SECRET_KEYS, key)
        code = "Qm9iVGhlQnVpbGRlckNvZGVUb2tlbjEyMzQ1Njc4OTA"
        callback = h.redact({"code": code, "state": "s-1"})
        self.assertEqual(callback, {"code": h.REDACTED, "state": "s-1"}, "the finish's code rides beside its state, and is a secret")
        form = {"grant_type": "authorization_code", "client_id": "mcp-1", "code": code, "code_verifier": "v" * 43, "redirect_uri": "http://127.0.0.1:8765/callback"}
        self.assertEqual(h.redact(form)["code"], h.REDACTED)
        self.assertIn(code, h.secret_values(form), "the code is scrubbed by value wherever else it appears")
        refusal = {"error": {"code": "SUBSCRIPTION_REQUIRED", "message": "This needs a paid subscription and none has been paid yet.", "detail": {}}}
        self.assertEqual(h.redact(refusal), refusal, "a refusal's code travels into the record (the Refusals law)")
        self.assertEqual(h.redact({"code": "receipt_missing", "sentence": "no receipt"})["code"], "receipt_missing")
        self.assertEqual(h.redact({"handle": "0123456789abcdef", "response": {"clientDataJSON": "eyJ0eXBlIjoi"}}),
                         {"handle": h.REDACTED, "response": h.REDACTED})


if __name__ == "__main__":
    unittest.main()
