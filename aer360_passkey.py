"""
THE SOFTWARE PASSKEY (Spec T7): a P-256 key pair the harness holds for one person at one
estate, an attestation object in the `none` format, and an assertion signature over
authenticatorData ‖ SHA-256(clientDataJSON).

AER 360 has no password and no test login: every founder enrols and signs in by WebAuthn
(`apps/server/src/routes/auth.ts`, verified by `@simplewebauthn/server` in
`apps/server/src/services/webauthn.ts`). The server accepts the `none` attestation format
and requires user verification (`attestationType: 'none'`, `residentKey: 'required'`,
`userVerification: 'required'`, `requireUserVerification: true`). So the harness carries a
passkey of its own, made of exactly two things:

  THE MAC'S OWN OPENSSL (/usr/bin/openssl, LibreSSL on every Mac), through subprocess, for
  the one thing the standard library lacks — ECDSA on the NIST P-256 curve:
      openssl ecparam -genkey -name prime256v1       the key
      openssl ec -pubout -outform DER                 its public point
      openssl dgst -sha256 -sign <key>                the signature, in DER
  PURE PYTHON for what openssl does not speak: base64url, the DER-to-raw signature and
  public-key conversions, the COSE key, the authenticator data, and a CBOR encoder for the
  handful of shapes an attestation object needs (RFC 8949).

Also here, for the tests and for a self-check before a ceremony is sent: a pure-Python P-256
verifier and a re-statement of the checks `@simplewebauthn/server` makes on a `none`
registration and on an assertion (rpIdHash, flags, COSE key, challenge, origin, counter,
signature). The verifier is proven against a published vector (RFC 6979 A.2.5) and against
a signature openssl produced.

The key is kept by the harness under ~/.aer360-harness/<estate>/<person>.json, mode 0600:
a test key for a sandbox estate that never leaves the Mac. Nothing here prints a key.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import struct
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

OPENSSL = "/usr/bin/openssl"
ES256 = -7  # COSE algorithm identifier for ECDSA with SHA-256 on P-256
COSE_KTY_EC2 = 2
COSE_CRV_P256 = 1
AAGUID_NONE = bytes(16)  # an attestation in the `none` format carries a zero AAGUID

# Authenticator data flags (WebAuthn §6.1).
FLAG_UP = 0x01  # user present
FLAG_UV = 0x04  # user verified
FLAG_BE = 0x08  # backup eligible
FLAG_BS = 0x10  # backup state
FLAG_AT = 0x40  # attested credential data included
FLAG_ED = 0x80  # extension data included


class PasskeyError(Exception):
    """A fault of the passkey module or its surroundings (openssl missing, a shape it cannot read)."""


class PasskeyRefused(Exception):
    """The verifier's refusal, in the words @simplewebauthn/server would use for the same fault."""


# ---------------------------------------------------------------------------
# base64url, as WebAuthn spells every binary field.
# ---------------------------------------------------------------------------
def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    text = text.strip()
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


# ---------------------------------------------------------------------------
# CBOR (RFC 8949), for the shapes an attestation object needs: unsigned and negative
# integers, byte strings, text strings, arrays, maps, and the three simple values.
# Maps are written in the canonical order CTAP2 asks for: shorter keys first, then bytewise.
# ---------------------------------------------------------------------------
def _cbor_head(major: int, n: int) -> bytes:
    if n < 24:
        return bytes([(major << 5) | n])
    if n <= 0xFF:
        return bytes([(major << 5) | 24, n])
    if n <= 0xFFFF:
        return bytes([(major << 5) | 25]) + struct.pack(">H", n)
    if n <= 0xFFFFFFFF:
        return bytes([(major << 5) | 26]) + struct.pack(">I", n)
    return bytes([(major << 5) | 27]) + struct.pack(">Q", n)


def cbor_encode(value: Any) -> bytes:
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if value is None:
        return b"\xf6"
    if isinstance(value, int):
        if value >= 0:
            return _cbor_head(0, value)
        return _cbor_head(1, -1 - value)
    if isinstance(value, (bytes, bytearray)):
        return _cbor_head(2, len(value)) + bytes(value)
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return _cbor_head(3, len(encoded)) + encoded
    if isinstance(value, (list, tuple)):
        return _cbor_head(4, len(value)) + b"".join(cbor_encode(item) for item in value)
    if isinstance(value, dict):
        items = [(cbor_encode(k), cbor_encode(v)) for k, v in value.items()]
        items.sort(key=lambda kv: (len(kv[0]), kv[0]))
        return _cbor_head(5, len(items)) + b"".join(k + v for k, v in items)
    raise PasskeyError("cbor_encode does not speak %s" % type(value).__name__)


def _cbor_read_head(data: bytes, offset: int) -> Tuple[int, int, int]:
    """(major, argument, next offset) for the head at `offset`."""
    if offset >= len(data):
        raise PasskeyError("cbor: unexpected end of data")
    first = data[offset]
    major, info = first >> 5, first & 0x1F
    offset += 1
    if info < 24:
        return major, info, offset
    sizes = {24: 1, 25: 2, 26: 4, 27: 8}
    if info not in sizes:
        raise PasskeyError("cbor: indefinite lengths and reserved heads are not spoken here")
    size = sizes[info]
    if offset + size > len(data):
        raise PasskeyError("cbor: unexpected end of data")
    return major, int.from_bytes(data[offset:offset + size], "big"), offset + size


def cbor_decode_prefix(data: bytes, offset: int = 0) -> Tuple[Any, int]:
    major, arg, offset = _cbor_read_head(data, offset)
    if major == 0:
        return arg, offset
    if major == 1:
        return -1 - arg, offset
    if major == 2:
        if offset + arg > len(data):
            raise PasskeyError("cbor: byte string runs past the end")
        return bytes(data[offset:offset + arg]), offset + arg
    if major == 3:
        if offset + arg > len(data):
            raise PasskeyError("cbor: text string runs past the end")
        return data[offset:offset + arg].decode("utf-8"), offset + arg
    if major == 4:
        items: List[Any] = []
        for _ in range(arg):
            item, offset = cbor_decode_prefix(data, offset)
            items.append(item)
        return items, offset
    if major == 5:
        out: Dict[Any, Any] = {}
        for _ in range(arg):
            key, offset = cbor_decode_prefix(data, offset)
            val, offset = cbor_decode_prefix(data, offset)
            out[key] = val
        return out, offset
    if major == 7:
        if arg == 20:
            return False, offset
        if arg == 21:
            return True, offset
        if arg == 22:
            return None, offset
        raise PasskeyError("cbor: simple value %d is not spoken here" % arg)
    raise PasskeyError("cbor: major type %d (tags) is not spoken here" % major)


def cbor_decode(data: bytes) -> Any:
    value, offset = cbor_decode_prefix(data, 0)
    if offset != len(data):
        raise PasskeyError("cbor: %d trailing byte(s)" % (len(data) - offset))
    return value


# ---------------------------------------------------------------------------
# DER, for the two shapes openssl speaks and WebAuthn does not: the ECDSA signature
# (SEQUENCE of two INTEGERs) and the SubjectPublicKeyInfo of an EC public key.
# ---------------------------------------------------------------------------
def _der_length(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    body = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(body)]) + body


def der(tag: int, content: bytes) -> bytes:
    return bytes([tag]) + _der_length(len(content)) + content


def der_read(data: bytes, offset: int = 0) -> Tuple[int, bytes, int]:
    """(tag, content, next offset) for the element at `offset`."""
    if offset + 2 > len(data):
        raise PasskeyError("der: unexpected end of data")
    tag = data[offset]
    length = data[offset + 1]
    offset += 2
    if length & 0x80:
        count = length & 0x7F
        if count == 0 or offset + count > len(data):
            raise PasskeyError("der: unreadable length")
        length = int.from_bytes(data[offset:offset + count], "big")
        offset += count
    if offset + length > len(data):
        raise PasskeyError("der: element runs past the end")
    return tag, data[offset:offset + length], offset + length


def der_integer(value: int) -> bytes:
    body = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    if body[0] & 0x80:
        body = b"\x00" + body
    return der(0x02, body)


def der_signature_to_raw(signature: bytes) -> bytes:
    """A DER ECDSA signature to the 64 raw bytes r ‖ s that a verifier reads."""
    tag, seq, end = der_read(signature, 0)
    if tag != 0x30 or end != len(signature):
        raise PasskeyError("der: a signature is one SEQUENCE")
    tag_r, r_bytes, offset = der_read(seq, 0)
    tag_s, s_bytes, offset = der_read(seq, offset)
    if tag_r != 0x02 or tag_s != 0x02 or offset != len(seq):
        raise PasskeyError("der: a signature is two INTEGERs")
    r = int.from_bytes(r_bytes, "big")
    s = int.from_bytes(s_bytes, "big")
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def raw_signature_to_der(raw: bytes) -> bytes:
    if len(raw) != 64:
        raise PasskeyError("a raw P-256 signature is 64 bytes")
    r = int.from_bytes(raw[:32], "big")
    s = int.from_bytes(raw[32:], "big")
    return der(0x30, der_integer(r) + der_integer(s))


def signature_r_s(signature_der: bytes) -> Tuple[int, int]:
    raw = der_signature_to_raw(signature_der)
    return int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")


OID_EC_PUBLIC_KEY = bytes.fromhex("2a8648ce3d0201")  # 1.2.840.10045.2.1
OID_PRIME256V1 = bytes.fromhex("2a8648ce3d030107")  # 1.2.840.10045.3.1.7


def public_point_from_spki(spki: bytes) -> Tuple[bytes, bytes]:
    """The uncompressed point (x, y), each 32 bytes, from an EC SubjectPublicKeyInfo."""
    tag, seq, end = der_read(spki, 0)
    if tag != 0x30 or end != len(spki):
        raise PasskeyError("spki: one SEQUENCE expected")
    tag_alg, alg, offset = der_read(seq, 0)
    tag_key, bits, offset = der_read(seq, offset)
    if tag_alg != 0x30 or tag_key != 0x03:
        raise PasskeyError("spki: an algorithm SEQUENCE and a BIT STRING expected")
    tag_oid, oid, alg_offset = der_read(alg, 0)
    tag_curve, curve, _ = der_read(alg, alg_offset)
    if tag_oid != 0x06 or oid != OID_EC_PUBLIC_KEY or tag_curve != 0x06 or curve != OID_PRIME256V1:
        raise PasskeyError("spki: not an EC public key on prime256v1")
    if len(bits) != 66 or bits[0] != 0x00 or bits[1] != 0x04:
        raise PasskeyError("spki: an uncompressed P-256 point expected")
    return bits[2:34], bits[34:66]


def ec_private_key_pem(d: int, x: int, y: int) -> str:
    """An RFC 5915 ECPrivateKey PEM for a known scalar, so a published vector can be signed with openssl."""
    point = b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")
    body = (
        der_integer(1)
        + der(0x04, d.to_bytes(32, "big"))
        + der(0xA0, der(0x06, OID_PRIME256V1))
        + der(0xA1, der(0x03, b"\x00" + point))
    )
    encoded = base64.b64encode(der(0x30, body)).decode("ascii")
    lines = [encoded[i:i + 64] for i in range(0, len(encoded), 64)]
    return "-----BEGIN EC PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END EC PRIVATE KEY-----\n"


# ---------------------------------------------------------------------------
# P-256 in pure Python: the verifier the tests judge with, and the scalar multiplication
# that reproduces a published public key. Affine coordinates; speed is not the point.
# ---------------------------------------------------------------------------
P256_P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
P256_A = P256_P - 3
P256_B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
P256_GX = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
P256_GY = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5
P256_N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551

Point = Optional[Tuple[int, int]]  # None is the point at infinity


def _p256_add(p1: Point, p2: Point) -> Point:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2:
        if (y1 + y2) % P256_P == 0:
            return None
        lam = (3 * x1 * x1 + P256_A) * pow(2 * y1, -1, P256_P) % P256_P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, P256_P) % P256_P
    x3 = (lam * lam - x1 - x2) % P256_P
    y3 = (lam * (x1 - x3) - y1) % P256_P
    return (x3, y3)


def _p256_mul(k: int, point: Point) -> Point:
    result: Point = None
    addend = point
    while k > 0:
        if k & 1:
            result = _p256_add(result, addend)
        addend = _p256_add(addend, addend)
        k >>= 1
    return result


def p256_on_curve(x: int, y: int) -> bool:
    return (y * y - (x * x * x + P256_A * x + P256_B)) % P256_P == 0


def p256_public_key(d: int) -> Tuple[int, int]:
    if not 1 <= d < P256_N:
        raise PasskeyError("a P-256 private scalar is in [1, n-1]")
    point = _p256_mul(d, (P256_GX, P256_GY))
    assert point is not None
    return point


def p256_verify(public_key: Tuple[int, int], digest: bytes, r: int, s: int) -> bool:
    """ECDSA verification of a SHA-256 digest under a P-256 public key (FIPS 186-4 §6.4.2)."""
    x, y = public_key
    if not p256_on_curve(x, y):
        return False
    if not (1 <= r < P256_N and 1 <= s < P256_N):
        return False
    e = int.from_bytes(digest, "big") % P256_N
    w = pow(s, -1, P256_N)
    u1 = (e * w) % P256_N
    u2 = (r * w) % P256_N
    point = _p256_add(_p256_mul(u1, (P256_GX, P256_GY)), _p256_mul(u2, (x, y)))
    if point is None:
        return False
    return point[0] % P256_N == r


def ecdsa_sha256_verify_der(public_key: Tuple[int, int], message: bytes, signature_der: bytes) -> bool:
    r, s = signature_r_s(signature_der)
    return p256_verify(public_key, hashlib.sha256(message).digest(), r, s)


# ---------------------------------------------------------------------------
# The WebAuthn shapes: COSE key, authenticator data, attestation object, client data.
# ---------------------------------------------------------------------------
def cose_ec2_key(x: bytes, y: bytes) -> bytes:
    if len(x) != 32 or len(y) != 32:
        raise PasskeyError("a P-256 coordinate is 32 bytes")
    return cbor_encode({1: COSE_KTY_EC2, 3: ES256, -1: COSE_CRV_P256, -2: x, -3: y})


def parse_cose_ec2_key(data: bytes) -> Tuple[Tuple[int, int], int]:
    """((x, y) as integers, next offset) — the COSE key sits at the end of authenticator data."""
    key, offset = cbor_decode_prefix(data, 0)
    if not isinstance(key, dict):
        raise PasskeyRefused("Credential public key is not a COSE map")
    if key.get(1) != COSE_KTY_EC2:
        raise PasskeyRefused("Unexpected COSE key type %r (expected EC2)" % (key.get(1),))
    if key.get(3) != ES256:
        raise PasskeyRefused("Unsupported COSE algorithm %r (expected ES256, -7)" % (key.get(3),))
    if key.get(-1) != COSE_CRV_P256:
        raise PasskeyRefused("Unexpected COSE curve %r (expected P-256)" % (key.get(-1),))
    x, y = key.get(-2), key.get(-3)
    if not (isinstance(x, bytes) and isinstance(y, bytes) and len(x) == 32 and len(y) == 32):
        raise PasskeyRefused("COSE key coordinates are not two 32-byte strings")
    return (int.from_bytes(x, "big"), int.from_bytes(y, "big")), offset


def rp_id_hash(rp_id: str) -> bytes:
    return hashlib.sha256(rp_id.encode("utf-8")).digest()


def authenticator_data(rp_id: str, flags: int, sign_count: int, attested: bytes = b"") -> bytes:
    return rp_id_hash(rp_id) + bytes([flags & 0xFF]) + struct.pack(">I", sign_count) + attested


def attested_credential_data(credential_id: bytes, cose_key: bytes) -> bytes:
    return AAGUID_NONE + struct.pack(">H", len(credential_id)) + credential_id + cose_key


def attestation_object_none(auth_data: bytes) -> bytes:
    return cbor_encode({"fmt": "none", "attStmt": {}, "authData": auth_data})


def client_data_json(ceremony: str, challenge: str, origin: str) -> bytes:
    """The bytes a browser hands the server: type, the challenge as the server spelled it, the origin."""
    return json.dumps(
        {"type": ceremony, "challenge": challenge, "origin": origin, "crossOrigin": False},
        separators=(",", ":"),
    ).encode("utf-8")


def parse_authenticator_data(auth_data: bytes) -> Dict[str, Any]:
    if len(auth_data) < 37:
        raise PasskeyRefused("Authenticator data was fewer than 37 bytes")
    out: Dict[str, Any] = {
        "rpIdHash": auth_data[:32],
        "flags": auth_data[32],
        "counter": struct.unpack(">I", auth_data[33:37])[0],
        "credentialId": None,
        "publicKey": None,
    }
    offset = 37
    if auth_data[32] & FLAG_AT:
        if len(auth_data) < offset + 18:
            raise PasskeyRefused("Attested credential data was truncated")
        out["aaguid"] = auth_data[offset:offset + 16]
        offset += 16
        cred_len = struct.unpack(">H", auth_data[offset:offset + 2])[0]
        offset += 2
        if cred_len > 1023:
            raise PasskeyRefused("Credential ID was longer than 1023 bytes")
        out["credentialId"] = auth_data[offset:offset + cred_len]
        offset += cred_len
        public_key, used = parse_cose_ec2_key(auth_data[offset:])
        out["publicKey"] = public_key
        offset += used
    if auth_data[32] & FLAG_ED:
        extensions, used = cbor_decode_prefix(auth_data, offset)
        out["extensions"] = extensions
        offset += used
    if offset != len(auth_data):
        raise PasskeyRefused("Authenticator data carried %d unexpected trailing byte(s)" % (len(auth_data) - offset))
    return out


# ---------------------------------------------------------------------------
# The key, on the Mac's own openssl.
# ---------------------------------------------------------------------------
class OpensslKey:
    """A prime256v1 private key as PEM, generated and used through /usr/bin/openssl."""

    def __init__(self, pem: str, openssl: str = OPENSSL):
        if "BEGIN EC PRIVATE KEY" not in pem and "BEGIN PRIVATE KEY" not in pem:
            raise PasskeyError("not an EC private key in PEM")
        self.pem = pem
        self.openssl = openssl

    @classmethod
    def generate(cls, openssl: str = OPENSSL) -> "OpensslKey":
        out = _run([openssl, "ecparam", "-genkey", "-name", "prime256v1", "-noout"], b"")
        return cls(out.decode("ascii"), openssl)

    def public_point(self) -> Tuple[bytes, bytes]:
        spki = _run([self.openssl, "ec", "-pubout", "-outform", "DER"], self.pem.encode("ascii"))
        return public_point_from_spki(spki)

    def public_key(self) -> Tuple[int, int]:
        x, y = self.public_point()
        return int.from_bytes(x, "big"), int.from_bytes(y, "big")

    def sign(self, message: bytes) -> bytes:
        """ECDSA-SHA256 over `message`, as DER — the form WebAuthn carries an ES256 signature in."""
        fd, path = tempfile.mkstemp(prefix="aer360-key-", suffix=".pem")
        try:
            os.fchmod(fd, 0o600)
            os.write(fd, self.pem.encode("ascii"))
            os.close(fd)
            return _run([self.openssl, "dgst", "-sha256", "-sign", path], message)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


def _run(argv: List[str], stdin: bytes) -> bytes:
    try:
        done = subprocess.run(argv, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as err:
        raise PasskeyError("%s could not be run: %s" % (argv[0], err))
    if done.returncode != 0:
        raise PasskeyError("%s answered %d: %s" % (" ".join(argv[:2]), done.returncode,
                                                   done.stderr.decode("utf-8", "replace").strip()[:300]))
    return done.stdout


# ---------------------------------------------------------------------------
# The passkey a person carries.
# ---------------------------------------------------------------------------
class SoftwarePasskey:
    """
    One person's passkey at one estate: the key, the credential id the authenticator minted,
    the relying party it was registered with, the user handle the server gave it, and the
    signature counter. Serialisable to the key file (mode 0600) and back.
    """

    def __init__(self, key: OpensslKey, credential_id: bytes, rp_id: str, origin: str, user_id: bytes,
                 user_name: str = "", display_name: str = "", sign_count: int = 0,
                 aap_credential_id: Optional[str] = None, base: Optional[str] = None,
                 created_at: Optional[str] = None):
        self.key = key
        self.credential_id = credential_id
        self.rp_id = rp_id
        self.origin = origin
        self.user_id = user_id
        self.user_name = user_name
        self.display_name = display_name
        self.sign_count = sign_count
        self.aap_credential_id = aap_credential_id
        self.base = base
        self.created_at = created_at

    @property
    def credential_id_b64(self) -> str:
        return b64url_encode(self.credential_id)

    # -- the registration ceremony -----------------------------------------
    @classmethod
    def create_for(cls, options: Dict[str, Any], origin: str, openssl: str = OPENSSL) -> "SoftwarePasskey":
        """
        A new key for the registration options the server returned (`PublicKeyCredentialCreationOptionsJSON`):
        `rp.id` is the relying party, `user.id` the handle (base64url), `pubKeyCredParams` must offer ES256.
        """
        params = options.get("pubKeyCredParams") or []
        if params and not any(p.get("alg") == ES256 for p in params if isinstance(p, dict)):
            raise PasskeyError("the server's pubKeyCredParams offer no ES256 (-7); this passkey speaks nothing else")
        rp = options.get("rp") or {}
        rp_id = rp.get("id") or _host_of(origin)
        user = options.get("user") or {}
        user_id = b64url_decode(str(user.get("id", "")))
        return cls(OpensslKey.generate(openssl), secrets.token_bytes(32), rp_id, origin, user_id,
                   user_name=str(user.get("name", "")), display_name=str(user.get("displayName", "")))

    def registration(self, options: Dict[str, Any], origin: Optional[str] = None,
                     flags: int = FLAG_UP | FLAG_UV | FLAG_AT) -> Dict[str, Any]:
        """The `RegistrationResponseJSON` a browser would return for these options."""
        origin = origin or self.origin
        challenge = str(options["challenge"])
        rp_id = (options.get("rp") or {}).get("id") or self.rp_id
        x, y = self.key.public_point()
        auth = authenticator_data(rp_id, flags, self.sign_count,
                                  attested_credential_data(self.credential_id, cose_ec2_key(x, y)))
        client_data = client_data_json("webauthn.create", challenge, origin)
        return {
            "id": self.credential_id_b64,
            "rawId": self.credential_id_b64,
            "type": "public-key",
            "clientExtensionResults": {},
            "response": {
                "clientDataJSON": b64url_encode(client_data),
                "attestationObject": b64url_encode(attestation_object_none(auth)),
                "transports": ["internal"],
            },
        }

    # -- the assertion ceremony ----------------------------------------------
    def assertion(self, challenge: str, rp_id: Optional[str] = None, origin: Optional[str] = None,
                  flags: int = FLAG_UP | FLAG_UV, with_user_handle: bool = True,
                  count: bool = True) -> Dict[str, Any]:
        """
        The `AuthenticationResponseJSON` for a challenge: the signature is ECDSA-SHA256 over
        authenticatorData ‖ SHA-256(clientDataJSON). The counter moves by one unless told not to.
        `rp_id` and `origin` may be overridden on purpose — S11 signs for the wrong relying party.
        """
        if count:
            self.sign_count += 1
        auth = authenticator_data(rp_id or self.rp_id, flags, self.sign_count)
        client_data = client_data_json("webauthn.get", challenge, origin or self.origin)
        signature = self.key.sign(auth + hashlib.sha256(client_data).digest())
        response: Dict[str, Any] = {
            "clientDataJSON": b64url_encode(client_data),
            "authenticatorData": b64url_encode(auth),
            "signature": b64url_encode(signature),
        }
        if with_user_handle and self.user_id:
            response["userHandle"] = b64url_encode(self.user_id)
        return {
            "id": self.credential_id_b64,
            "rawId": self.credential_id_b64,
            "type": "public-key",
            "clientExtensionResults": {},
            "response": response,
        }

    # -- the key file ----------------------------------------------------------
    def to_json(self) -> Dict[str, Any]:
        return {
            "kind": "aer360-harness software passkey (P-256, attestation none)",
            "pem": self.key.pem,
            "credential_id": self.credential_id_b64,
            "rp_id": self.rp_id,
            "origin": self.origin,
            "user_id": b64url_encode(self.user_id),
            "user_name": self.user_name,
            "display_name": self.display_name,
            "sign_count": self.sign_count,
            "aap_credential_id": self.aap_credential_id,
            "base": self.base,
            "created_at": self.created_at,
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any], openssl: str = OPENSSL) -> "SoftwarePasskey":
        return cls(OpensslKey(str(data["pem"]), openssl), b64url_decode(str(data["credential_id"])),
                   str(data["rp_id"]), str(data["origin"]), b64url_decode(str(data.get("user_id", ""))),
                   user_name=str(data.get("user_name", "")), display_name=str(data.get("display_name", "")),
                   sign_count=int(data.get("sign_count", 0)), aap_credential_id=data.get("aap_credential_id"),
                   base=data.get("base"), created_at=data.get("created_at"))

    def save(self, path: str) -> None:
        write_private(path, self.to_json())

    @classmethod
    def load(cls, path: str, openssl: str = OPENSSL) -> Optional["SoftwarePasskey"]:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_json(json.load(handle), openssl)


def write_private(path: str, data: Any) -> None:
    """A JSON file only its owner can read: the folder 0700, the file 0600."""
    folder = os.path.dirname(path)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    try:
        os.chmod(folder, 0o700)
    except OSError:
        pass
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, json.dumps(data, indent=2, sort_keys=True).encode("utf-8"))
    finally:
        os.close(fd)


def _host_of(origin: str) -> str:
    host = origin.split("://", 1)[-1].split("/", 1)[0]
    return host.split(":", 1)[0]


# ---------------------------------------------------------------------------
# THE VERIFIER — a Python re-statement of what @simplewebauthn/server checks on a `none`
# registration (verifyRegistrationResponse) and on an assertion (verifyAuthenticationResponse),
# as `services/webauthn.ts` calls them: expectedChallenge, expectedOrigin, expectedRPID,
# requireUserVerification: true. Used by the tests, and by the harness's own self-check.
# ---------------------------------------------------------------------------
def _client_data_of(response: Dict[str, Any], ceremony: str, expected_challenge: str, expected_origin: str) -> Dict[str, Any]:
    if response.get("type") != "public-key":
        raise PasskeyRefused("Unexpected credential type %r, expected \"public-key\"" % (response.get("type"),))
    if not isinstance(response.get("id"), str) or not response["id"]:
        raise PasskeyRefused("Credential ID was not base64url-encoded")
    if response.get("rawId") != response.get("id"):
        raise PasskeyRefused("Credential ID was not equal to rawId")
    inner = response.get("response") or {}
    try:
        client_data = json.loads(b64url_decode(str(inner.get("clientDataJSON", ""))).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise PasskeyRefused("clientDataJSON could not be read")
    if client_data.get("type") != ceremony:
        raise PasskeyRefused("Unexpected authentication response type: %r" % (client_data.get("type"),))
    if client_data.get("challenge") != expected_challenge:
        raise PasskeyRefused("Unexpected authentication response challenge \"%s\", expected \"%s\"" % (
            client_data.get("challenge"), expected_challenge))
    if client_data.get("origin") != expected_origin:
        raise PasskeyRefused("Unexpected authentication response origin \"%s\", expected \"%s\"" % (
            client_data.get("origin"), expected_origin))
    return client_data


def _check_rp_and_flags(parsed: Dict[str, Any], expected_rp_id: str, require_uv: bool = True) -> None:
    if parsed["rpIdHash"] != rp_id_hash(expected_rp_id):
        raise PasskeyRefused("Unexpected RP ID hash")
    flags = parsed["flags"]
    if not flags & FLAG_UP:
        raise PasskeyRefused("User not present during authentication")
    if require_uv and not flags & FLAG_UV:
        raise PasskeyRefused("User verification required, but user could not be verified")
    if (flags & FLAG_BS) and not (flags & FLAG_BE):
        raise PasskeyRefused("Backup state flag set without backup eligibility")


def verify_registration(response: Dict[str, Any], expected_challenge: str, expected_origin: str,
                        expected_rp_id: str) -> Dict[str, Any]:
    """The `none` registration checks. Returns the credential id, public key and counter a server would store."""
    _client_data_of(response, "webauthn.create", expected_challenge, expected_origin)
    inner = response.get("response") or {}
    attestation = cbor_decode(b64url_decode(str(inner.get("attestationObject", ""))))
    if not isinstance(attestation, dict):
        raise PasskeyRefused("Attestation object was not a CBOR map")
    if attestation.get("fmt") != "none":
        raise PasskeyRefused("Unsupported attestation format %r" % (attestation.get("fmt"),))
    if attestation.get("attStmt") != {}:
        raise PasskeyRefused("None attestation included unexpected attestation statement")
    auth_data = attestation.get("authData")
    if not isinstance(auth_data, bytes):
        raise PasskeyRefused("Attestation object carried no authData")
    parsed = parse_authenticator_data(auth_data)
    _check_rp_and_flags(parsed, expected_rp_id)
    if not parsed["flags"] & FLAG_AT or parsed["credentialId"] is None or parsed["publicKey"] is None:
        raise PasskeyRefused("No attested credential data was included in authenticator data")
    if b64url_encode(parsed["credentialId"]) != response["id"]:
        raise PasskeyRefused("Credential ID in authenticator data did not match the response id")
    if parsed.get("aaguid") != AAGUID_NONE:
        raise PasskeyRefused("None attestation carried a non-zero AAGUID")
    transports = inner.get("transports")
    if transports is not None and not isinstance(transports, list):
        raise PasskeyRefused("transports was not a list")
    return {"credential_id": parsed["credentialId"], "public_key": parsed["publicKey"], "sign_count": parsed["counter"]}


def verify_assertion(response: Dict[str, Any], expected_challenge: str, expected_origin: str,
                     expected_rp_id: str, public_key: Tuple[int, int], previous_count: int = 0) -> int:
    """The assertion checks. Returns the new counter a server would store."""
    _client_data_of(response, "webauthn.get", expected_challenge, expected_origin)
    inner = response.get("response") or {}
    auth_data = b64url_decode(str(inner.get("authenticatorData", "")))
    parsed = parse_authenticator_data(auth_data)
    _check_rp_and_flags(parsed, expected_rp_id)
    counter = parsed["counter"]
    if (counter > 0 or previous_count > 0) and counter <= previous_count:
        raise PasskeyRefused("Response counter value %d was lower than expected %d" % (counter, previous_count))
    signed = auth_data + hashlib.sha256(b64url_decode(str(inner.get("clientDataJSON", "")))).digest()
    try:
        r, s = signature_r_s(b64url_decode(str(inner.get("signature", ""))))
    except PasskeyError as err:
        raise PasskeyRefused("Signature could not be read as DER: %s" % err)
    if not p256_verify(public_key, hashlib.sha256(signed).digest(), r, s):
        raise PasskeyRefused("Signature verification failed")
    return counter


def openssl_available(openssl: str = OPENSSL) -> bool:
    return os.path.isfile(openssl) and os.access(openssl, os.X_OK)
