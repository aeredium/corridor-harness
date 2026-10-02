#!/usr/bin/env python3
"""
THE ESTATE'S OWN PAYEE ROAD, SHARED (Spec T23, 2 October 2026).

Two harnesses walk one road to make an address a payee of Harness Holdings: the estate harness at S6, for Northwind and
Contoso (`aer360_harness.py`, Specs T9, T12, T13, T18), and Pathfinder at S11, for the wallet of the agent it has just
created (`aerconnect_harness.py`, Spec T23). The road is the one the founder's browser walks — `POST /v1/payees`, the
promote, the roster pressing `approve` in T12's order until the count is met, and `GET /v1/payees` as the judge (Spec T13
§3: the register decides, never the press) — and it is written once, here, lifted out of the estate harness's S6 word
for word. The estate harness imports it and its behaviour is unchanged; Pathfinder imports it so that the agent's wallet
is made a payee exactly as Northwind is, and never by a second writing of the same presses.

Everything else of the estate's payment road Pathfinder reuses as the estate harness's own methods, by import: the review,
the creation, the submit, the signers' presses, the execute, the landing reads and the judgment (`Runner.pay`,
`sign_the_run`, `read_until_terminal`, `judge_landing`), the Treasury (`bring_in_the_treasury`,
`treasury_pays_the_shortfall`), the money reads (`read_usdc_balance`, `read_gas_account`) and the gas credit road
(`read_admin_env`, `credit_gas`, `gas_credit_for`). Nothing of them is rewritten.

The functions take the estate runner as their first argument: its wire (`request`), its evidence (`step`), its facts
(the payee records S7 resolves from, Spec T18 §2), its roster presses (`approve_to_quorum`) and its register reader
(`register_status_of`). The sentences are the estate harness's own, unchanged.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import aer360_tables as T


def propose_payee(runner: Any, founder: Any, name: str, key: str, address: str, chain: str, station: str) -> Tuple[Optional[Dict[str, Any]], str, bool]:
    """
    One payee, created and promoted by the founder, then approved until the whitelist roster's quorum is met (Spec T9,
    T12): `POST /v1/payees` with one address on `chain`, `POST /v1/payees/addresses/{id}/promote`, then the roster people
    the runner holds a session for press `approve` in T12's order until the estate answers whitelisted, a refusal, or
    nobody is left (`Runner.approve_to_quorum`). The record is appended to the runner's `facts["payees"]` the moment the
    payee exists, so the register judgment and S7's resolution find it.

    Answers (record, said, whole): the record (None where the estate refused the creation), the line's words for this
    payee in the estate's own sentences, and whether the road ran to the presses — False where the creation was refused or
    the payee was created with no address id, each said in `said`.
    """
    body = {"displayName": name, "defaultAsset": T.PAYMENT_ASSET, "defaultChain": chain, "addresses": [{"chain": chain, "address": address}]}
    created = runner.request(founder, "POST", "/v1/payees", body, station)
    runner.step(station, created, "201 with the payee and its proposed address on %s" % chain, "created" if created.ok else created.sentence(), body, founder.name)
    if not created.ok or not isinstance(created.json, dict):
        return None, "%s: %s" % (name, created.sentence()), False
    row = created.json.get("payee") or {}
    addresses = row.get("addresses") or []
    address_id = str(addresses[0].get("id")) if addresses else None
    record: Dict[str, Any] = {"key": key, "name": name, "payee_id": row.get("id"), "address_id": address_id, "address": address, "chain": chain,
                              "promoted": None, "approved": None, "presses": []}
    runner.facts["payees"].append(record)
    if not address_id:
        return record, "%s: created with no address id" % name, False
    promoted = runner.request(founder, "POST", "/v1/payees/addresses/%s/promote" % address_id, {}, station)
    runner.step(station, promoted, "a ceremony: status pending_promotion, platformMembershipId, ceremony", "answered" if promoted.ok else promoted.sentence(), {}, founder.name)
    record["promoted"] = promoted.json if promoted.ok else promoted.sentence()
    promote_said = "promoted" if promoted.ok else "promote answered %s" % promoted.sentence()
    return record, "%s: created on %s; %s; %s" % (name, chain, promote_said, runner.approve_to_quorum(record)), True


def judge_payee_register(runner: Any, who: Any, station: str, records: Sequence[Dict[str, Any]], expected: str) -> Any:
    """
    Spec T13 §3: the register is the judge, not the press. After the presses, `GET /v1/payees` decides each payee on its
    whitelistStatus, read from the row whose id is the record's own payee id (never by address: earlier runs leave rows with
    the same addresses still pending). Each record gains `register_status`, `mirror` (the sentence for a register that
    reads proposed after the platform counted the quorum) and `elsewhere` (a same-named payee an earlier run left on another
    chain, Spec T18 §2). Answers the register's answer; the runner's `facts["payees_register"]` holds its body.
    """
    register = runner.request(who, "GET", "/v1/payees", None, station)
    runner.step(station, register, expected, "answered" if register.ok else register.sentence(), None, who.name)
    runner.facts["payees_register"] = register.json if isinstance(register.json, dict) else None
    for record in records:
        status = runner.register_status_of(register.json, record)
        record["register_status"] = status
        record["mirror"] = runner.mirror_sentence(record, status)
        record["elsewhere"] = runner.same_name_elsewhere(register.json, record)
    return register


def register_words(runner: Any, records: Sequence[Dict[str, Any]]) -> str:
    """The register's verdict on each record, as S6's line says it: `<name> <status> (<mirror>) (<elsewhere>)`, joined."""
    return ", ".join(
        "%s %s%s%s" % (r["name"], r.get("register_status"), (" (%s)" % r["mirror"]) if r.get("mirror") else "",
                       (" (%s)" % runner.elsewhere_words(r["name"], r["elsewhere"])) if r.get("elsewhere") else "") for r in records) or "none"


__all__: List[str] = ["propose_payee", "judge_payee_register", "register_words"]
