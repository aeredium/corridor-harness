# Changelog

Changes arrive here by pull request, never by a commit straight to `main`. Earlier changes are recorded in the README's spec references and in the git history: Spec T1 (13 September 2026) brought the corridor harness home; Specs T2 and T3 (14 and 15 September) amended A4, A5 and A6; Specs T5 and T6 (16 and 17 September) made the harness name no real tester and the fixture the Series, version 1.2.

## Spec T7 — The estate harness (20 September 2026)

A Python script that walks AER 360 end to end as a founder, from Bear's ruling of 19 September 2026, read from aeredium/AERAccounts main after PR #106.

- New: `aer360_harness.py` — the runner: the invitation and sign-in ceremonies, the interviews answered from the book, the people, the wallet account, the payees, the payments, the journey; the three hats (S10 the auditor, S11 the attacker, S12 the optimizer); the dry run; the report.
- New: `aer360_passkey.py` — the software passkey: a P-256 key on the Mac's own `/usr/bin/openssl`, an attestation object in the `none` format, assertions over `authenticatorData ‖ SHA-256(clientDataJSON)`; CBOR, COSE and DER in pure Python; a pure-Python P-256 verifier and a re-statement of @simplewebauthn's checks, proven against RFC 8949 and RFC 6979.
- New: `aer360_answers.py` — the answer book: every question of the interviews with its kind and answer, the estate, the people, the money and the payments the spec decided; the live catalog's option strings byte for byte.
- New: `aer360_tables.py` — every address the estate harness may send, derived from a fixed seed and checksummed; the venue address S11 sends is read from the corridor's `tables.py` at run time.
- New: `tests/fixtures/aer360-questioncatalog.v11.ts` — the frozen version-11 catalog, copied verbatim, that the book is held against.
- New: `tests/test_aer360_*.py` — the passkey vectors, the book against the fixture, the tables, the dry run, the estate double, the founder's road against it, the three hats.
- README: the estate harness section. `.gitignore`: the report `aer360-harness-*.md` is never committed by accident.
- Not touched: corridor_harness.py, series.py, tables.py and the corridor's tests are not touched.
