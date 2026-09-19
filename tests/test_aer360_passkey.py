"""
The software passkey (Spec T7): the P-256 signer reproduces a published test vector and its
signature verifies under the pure-Python verifier; the CBOR encoder reproduces the RFC 8949
examples for the shapes used; a registration built by the module is accepted by a verifier
written to @simplewebauthn's rules for the `none` format, and an assertion it signs verifies
over authenticatorData ‖ SHA-256(clientDataJSON).
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_passkey as PK  # noqa: E402

# RFC 6979, Appendix A.2.5: ECDSA on P-256 with SHA-256, message "sample".
RFC6979_PRIVATE = 0xC9AFA9D845BA75166B5C215767B1D6934E50C3DB36E89B127B8A622B120F6721
RFC6979_UX = 0x60FED4BA255A9D31C961EB74C6356D68C049B8923B61FA6CE669622E60F29FB6
RFC6979_UY = 0x7903FE1008B8BC99A41AE9E95628BC64F2F1B20C2D7E9F5177A3C294D4462299
RFC6979_R = 0xEFD48B2AACB6A8FD1140DD9CD45E81D69D2C877B56AAF991C34D0EA84EAF3716
RFC6979_S = 0xF7CB1C942D657C41D436C7A1B6E29F65F3E900DBB9AFF4064DC4AB2F843ACDA8
ORIGIN = "https://accounts.aeredium.io"
RP_ID = "accounts.aeredium.io"

# RFC 8949, Appendix A: the examples for the shapes an attestation object needs.
RFC8949_EXAMPLES = [
    (0, "00"), (1, "01"), (10, "0a"), (23, "17"), (24, "1818"), (25, "1819"), (100, "1864"), (1000, "1903e8"),
    (1000000, "1a000f4240"), (1000000000000, "1b000000e8d4a51000"), (-1, "20"), (-10, "29"), (-100, "3863"), (-1000, "3903e7"),
    (b"", "40"), (bytes.fromhex("01020304"), "4401020304"), ("", "60"), ("a", "6161"), ("IETF", "6449455446"),
    ("\"\\", "62225c"), ("ü", "62c3bc"), ([], "80"), ([1, 2, 3], "83010203"), ([1, [2, 3], [4, 5]], "8301820203820405"),
    ({}, "a0"), ({1: 2, 3: 4}, "a201020304"), ({"a": 1, "b": [2, 3]}, "a26161016162820203"), (["a", {"b": "c"}], "826161a161626163"),
    ({"a": "A", "b": "B", "c": "C", "d": "D", "e": "E"}, "a56161614161626142616361436164614461656145"),
    (False, "f4"), (True, "f5"), (None, "f6"),
]


def registration_options(challenge="Y2hhbGxlbmdl"):
    return {"challenge": challenge, "rp": {"id": RP_ID, "name": "AER Accounts"},
            "user": {"id": PK.b64url_encode(b"credential-uuid"), "name": "Harness Holdings Pty Ltd · AER 360", "displayName": "Harriet"},
            "pubKeyCredParams": [{"alg": -8, "type": "public-key"}, {"alg": -7, "type": "public-key"}, {"alg": -257, "type": "public-key"}],
            "authenticatorSelection": {"residentKey": "required", "userVerification": "required"}, "attestation": "none"}


class CborTest(unittest.TestCase):
    def test_the_encoder_reproduces_the_rfc_8949_examples(self):
        for value, hexs in RFC8949_EXAMPLES:
            self.assertEqual(PK.cbor_encode(value).hex(), hexs, repr(value))

    def test_the_decoder_reads_the_rfc_8949_examples_back(self):
        for value, hexs in RFC8949_EXAMPLES:
            self.assertEqual(PK.cbor_decode(bytes.fromhex(hexs)), value, hexs)

    def test_maps_are_written_in_the_canonical_order_ctap2_asks_for(self):
        # shorter keys first, then bytewise: 1, 3, -1, -2, -3 for a COSE key; fmt, attStmt, authData for an attestation object
        cose = PK.cbor_decode(PK.cose_ec2_key(b"\x01" * 32, b"\x02" * 32))
        self.assertEqual(list(cose.keys()), [1, 3, -1, -2, -3])
        self.assertEqual(cose[1], 2)
        self.assertEqual(cose[3], -7)
        self.assertEqual(cose[-1], 1)
        attestation = PK.cbor_decode(PK.attestation_object_none(b"\x00" * 37))
        self.assertEqual(list(attestation.keys()), ["fmt", "attStmt", "authData"])

    def test_trailing_bytes_and_unknown_shapes_are_refused(self):
        with self.assertRaises(PK.PasskeyError):
            PK.cbor_decode(bytes.fromhex("0100"))
        with self.assertRaises(PK.PasskeyError):
            PK.cbor_encode(1.5)


class P256Test(unittest.TestCase):
    def test_the_public_key_of_the_rfc_6979_private_key_is_the_published_one(self):
        self.assertEqual(PK.p256_public_key(RFC6979_PRIVATE), (RFC6979_UX, RFC6979_UY))
        self.assertTrue(PK.p256_on_curve(RFC6979_UX, RFC6979_UY))

    def test_the_verifier_accepts_the_published_signature_and_refuses_a_moved_digest(self):
        digest = hashlib.sha256(b"sample").digest()
        self.assertTrue(PK.p256_verify((RFC6979_UX, RFC6979_UY), digest, RFC6979_R, RFC6979_S))
        self.assertFalse(PK.p256_verify((RFC6979_UX, RFC6979_UY), hashlib.sha256(b"sampla").digest(), RFC6979_R, RFC6979_S))
        self.assertFalse(PK.p256_verify((RFC6979_UX, RFC6979_UY), digest, RFC6979_R, RFC6979_S + 1))
        self.assertFalse(PK.p256_verify((RFC6979_UX + 1, RFC6979_UY), digest, RFC6979_R, RFC6979_S), "a point off the curve verifies nothing")

    def test_der_and_raw_signatures_round_trip(self):
        raw = RFC6979_R.to_bytes(32, "big") + RFC6979_S.to_bytes(32, "big")
        der = PK.raw_signature_to_der(raw)
        self.assertEqual(der[0], 0x30)
        self.assertEqual(PK.der_signature_to_raw(der), raw)
        self.assertEqual(PK.signature_r_s(der), (RFC6979_R, RFC6979_S))
        # an r with its high bit set is padded with a zero byte in DER, and read back the same
        self.assertEqual(PK.der_integer(0x80), bytes.fromhex("02020080"))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class OpensslTest(unittest.TestCase):
    def test_openssl_reads_the_vectors_key_and_its_signature_verifies_in_pure_python(self):
        key = PK.OpensslKey(PK.ec_private_key_pem(RFC6979_PRIVATE, RFC6979_UX, RFC6979_UY))
        self.assertEqual(key.public_key(), (RFC6979_UX, RFC6979_UY), "the PEM the module writes is the key openssl reads")
        signature = key.sign(b"sample")
        raw = PK.der_signature_to_raw(signature)
        self.assertEqual(len(raw), 64)
        self.assertEqual(PK.raw_signature_to_der(raw), signature, "DER to raw and back is byte for byte")
        self.assertTrue(PK.ecdsa_sha256_verify_der((RFC6979_UX, RFC6979_UY), b"sample", signature))
        self.assertFalse(PK.ecdsa_sha256_verify_der((RFC6979_UX, RFC6979_UY), b"sampla", signature))

    def test_a_generated_key_signs_what_its_own_public_point_verifies(self):
        key = PK.OpensslKey.generate()
        self.assertIn("EC PRIVATE KEY", key.pem)
        self.assertTrue(PK.ecdsa_sha256_verify_der(key.public_key(), b"the founder's road", key.sign(b"the founder's road")))


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class WebAuthnTest(unittest.TestCase):
    def setUp(self):
        self.options = registration_options()
        self.passkey = PK.SoftwarePasskey.create_for(self.options, ORIGIN)

    def test_a_registration_passes_the_none_format_checks(self):
        registration = self.passkey.registration(self.options)
        self.assertEqual(registration["type"], "public-key")
        self.assertEqual(registration["id"], registration["rawId"])
        self.assertEqual(registration["response"]["transports"], ["internal"])
        client_data = json.loads(PK.b64url_decode(registration["response"]["clientDataJSON"]))
        self.assertEqual(client_data, {"type": "webauthn.create", "challenge": "Y2hhbGxlbmdl", "origin": ORIGIN, "crossOrigin": False})
        stored = PK.verify_registration(registration, "Y2hhbGxlbmdl", ORIGIN, RP_ID)
        self.assertEqual(stored["credential_id"], self.passkey.credential_id)
        self.assertEqual(stored["public_key"], self.passkey.key.public_key())
        self.assertEqual(stored["sign_count"], 0)
        attestation = PK.cbor_decode(PK.b64url_decode(registration["response"]["attestationObject"]))
        self.assertEqual(attestation["fmt"], "none")
        self.assertEqual(attestation["attStmt"], {})
        parsed = PK.parse_authenticator_data(attestation["authData"])
        self.assertEqual(parsed["rpIdHash"], hashlib.sha256(RP_ID.encode()).digest())
        self.assertEqual(parsed["flags"], PK.FLAG_UP | PK.FLAG_UV | PK.FLAG_AT, "user presence, user verification, attested credential data")
        self.assertEqual(parsed["aaguid"], bytes(16))

    def test_the_verifier_refuses_a_registration_for_another_challenge_origin_or_relying_party(self):
        registration = self.passkey.registration(self.options)
        with self.assertRaisesRegex(PK.PasskeyRefused, "challenge"):
            PK.verify_registration(registration, "b3RoZXI", ORIGIN, RP_ID)
        with self.assertRaisesRegex(PK.PasskeyRefused, "origin"):
            PK.verify_registration(registration, "Y2hhbGxlbmdl", "https://elsewhere.example", RP_ID)
        with self.assertRaisesRegex(PK.PasskeyRefused, "RP ID hash"):
            PK.verify_registration(registration, "Y2hhbGxlbmdl", ORIGIN, "elsewhere.example")
        without_uv = self.passkey.registration(self.options, flags=PK.FLAG_UP | PK.FLAG_AT)
        with self.assertRaisesRegex(PK.PasskeyRefused, "User verification required"):
            PK.verify_registration(without_uv, "Y2hhbGxlbmdl", ORIGIN, RP_ID)

    def test_an_assertion_verifies_over_authenticator_data_and_the_hash_of_the_client_data(self):
        stored = PK.verify_registration(self.passkey.registration(self.options), "Y2hhbGxlbmdl", ORIGIN, RP_ID)
        assertion = self.passkey.assertion("bm9uY2U", origin=ORIGIN)
        self.assertEqual(assertion["response"]["userHandle"], self.options["user"]["id"], "the user handle is the one the server gave at registration")
        auth = PK.b64url_decode(assertion["response"]["authenticatorData"])
        self.assertEqual(len(auth), 37)
        self.assertEqual(auth[32], PK.FLAG_UP | PK.FLAG_UV)
        signed = auth + hashlib.sha256(PK.b64url_decode(assertion["response"]["clientDataJSON"])).digest()
        self.assertTrue(PK.ecdsa_sha256_verify_der(stored["public_key"], signed, PK.b64url_decode(assertion["response"]["signature"])))
        counter = PK.verify_assertion(assertion, "bm9uY2U", ORIGIN, RP_ID, stored["public_key"], stored["sign_count"])
        self.assertEqual(counter, 1)
        # the counter moves, and an old one is refused
        second = self.passkey.assertion("bm9uY2Uy", origin=ORIGIN)
        self.assertEqual(PK.verify_assertion(second, "bm9uY2Uy", ORIGIN, RP_ID, stored["public_key"], counter), 2)
        with self.assertRaisesRegex(PK.PasskeyRefused, "counter"):
            PK.verify_assertion(assertion, "bm9uY2U", ORIGIN, RP_ID, stored["public_key"], 2)

    def test_the_verifier_refuses_an_assertion_for_the_wrong_relying_party_or_a_tampered_signature(self):
        stored = PK.verify_registration(self.passkey.registration(self.options), "Y2hhbGxlbmdl", ORIGIN, RP_ID)
        wrong = self.passkey.assertion("bm9uY2U", rp_id="not-the-estate.invalid", origin=ORIGIN)
        with self.assertRaisesRegex(PK.PasskeyRefused, "Unexpected RP ID hash"):
            PK.verify_assertion(wrong, "bm9uY2U", ORIGIN, RP_ID, stored["public_key"], 0)
        good = self.passkey.assertion("bm9uY2U", origin=ORIGIN)
        tampered = dict(good, response=dict(good["response"], clientDataJSON=PK.b64url_encode(PK.client_data_json("webauthn.get", "bm9uY2U", ORIGIN) + b" ")))
        with self.assertRaisesRegex(PK.PasskeyRefused, "clientDataJSON|Signature"):
            PK.verify_assertion(tampered, "bm9uY2U", ORIGIN, RP_ID, stored["public_key"], 0)

    def test_the_key_file_is_the_owners_alone_and_reads_back_the_same_key(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "harness-holdings", "harriet.json")
        self.passkey.aap_credential_id = "cred-1"
        self.passkey.sign_count = 3
        self.passkey.save(path)
        self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
        self.assertEqual(oct(os.stat(os.path.dirname(path)).st_mode & 0o777), "0o700")
        loaded = PK.SoftwarePasskey.load(path)
        self.assertEqual(loaded.credential_id, self.passkey.credential_id)
        self.assertEqual(loaded.key.pem, self.passkey.key.pem)
        self.assertEqual(loaded.sign_count, 3)
        self.assertEqual(loaded.aap_credential_id, "cred-1")
        self.assertEqual(loaded.user_id, self.passkey.user_id)
        self.assertIsNone(PK.SoftwarePasskey.load(os.path.join(tmp, "nobody.json")))

    def test_a_server_offering_no_es256_is_refused_before_a_key_is_made(self):
        options = registration_options()
        options["pubKeyCredParams"] = [{"alg": -257, "type": "public-key"}]
        with self.assertRaisesRegex(PK.PasskeyError, "ES256"):
            PK.SoftwarePasskey.create_for(options, ORIGIN)


if __name__ == "__main__":
    unittest.main()
