"""
THE ANSWER BOOK (Spec T7): every question of the AER 360 interviews, with its kind and the
answer the harness gives, and the estate, the people, the money and the payments the spec
decided.

Read from the AER 360 code, not from memory: `apps/server/src/services/questioncatalog.ts` at
aeredium/AERAccounts commit cf3be4a (Spec 92, CATALOG_VERSION 14), whose option strings are copied
here byte for byte because the interview refuses a choice that is not one of the options offered
(`services/onboarding.ts`, validateValue); and `questioncatalog.v11.ts`, the frozen record of
version 11, which is the fixture the tests held this book against until Spec T11. Version 12
retired C16 and C16C ("how long may a held payment wait before it is refused automatically?"),
so the two ids are carried here with the words version 11 offered them in (commit 5492703^),
and are never served by an estate at version 12 or later.

SPEC T11 (21 September 2026): THE BOOK LEARNS CATALOG VERSION 14. The run of 21 September stopped
at S3 and S5 — "the answer book has no answer for policy question C11A" and "… for wallet_account
question WO1" — because Spec 92 gave the catalog seven questions the book did not know (C11A, C11C,
C19, WO1, WO2, WO3, WO4) and one new answer kind, `person_or_none`. The book answers the seven
below, states the version it answers (CATALOG_VERSION_ANSWERED), and the tests hold it against the
pages the estate served that night (tests/fixtures/aer360-served-2026-09-21.json) plus the seven.
The wire shape of the new kind (`services/onboarding.ts`, `case 'person_or_none'`) is
{choice: <option sentence>, person: {name, email}} behind the first option and {choice} alone
behind "No one". WO2 is a `list` whose one entry carries name, surname, email and title (CEO, CFO
or COO). WO3 and WO4 are `money` — {cents}, as every money answer — and they are the two fields in
the estate that arrive written, at one dollar; the book writes the real figure. The compiler
refuses at the read-back where WO4 is not above WO3, and where WA1's people plus WO2's person are
fewer than three (`tiersNeedThreePeople`).

THE LAW OF THIS FILE. The harness never improvises an answer. A question the book does not know
stops the run at that station with the question's id, prompt and kind printed word for word,
because a moved catalog is a finding, not something to improvise around. A choice the served
page does not offer stops it the same way, with the options the page offered printed beside it.

WHAT THE SPEC DECIDED, AND WHAT THE BOOK DECIDED WHERE THE SPEC LEFT IT TO THE HARNESS:

  The company is Harness Holdings Pty Ltd, Australia, displayed in AUD. The people, as the
  census names them: Harriet Founder, the founder, level 1; Ada Approver, who approves payments;
  Ben Signatory, who signs changes to the rules; Cora Clerk, who enters payments. Work emails at
  harness+<first>@aeredium.io. The census offers four payment parts (Enter, Review, Authorise,
  Release payments); Ada is 'Release payments', Cora 'Enter payments', Harriet and Ben 'Authorise
  payments'. The rules: one approver for every payment (C10 = 1, C11 names Ada) and two for a
  change of rules (C12 = 2; the catalog offers no roster for changes — the change roster is the
  census, A8, so "the founder and Ben" cannot be written narrower than "two of the four named");
  sight granted to no level beneath (B4 unticked, and not served while A9 is No); no levels
  beneath (A9 No); no agents yet (A11 No). Recovery: the least the catalog allows (R1 No).
  Every other question: the catalog's recommended answer where it offers one, otherwise the
  answer written here.

  C15 (may the preparer also count among those who release) is answered Yes, and WA2 the same
  in the account's words — one fact, one field (`approvallaw.ts`). The invitation road enrols
  every author under the ONE role-bearing credential the account carries (`services/invites.ts`,
  roleBearingCredentialIds), so Ada, Ben and Cora hold the founder's credential id; a No would
  refuse every approval as a self-approval and the walk would stop at the first payee. Yes lets
  the walk reach the payments, and S10 and S11 report what the estate does with one credential
  worn by four people. WA2's No is also refused at the page beside a single named approver
  (`crosschecks.ts`, SEPARATION_DEADLOCK_CHECKS).

  The seven of catalog version 14 (Spec T11): C11A answers that a new payee is approved by the
  people who may change the rules, at the number set for a change — the census at C12's count of
  two, which is the roster T10 asserts in S6 (Ada and Ben, two of four). C11C is asked only behind
  C11A's third answer and is not served behind that one; it is written all the same, as no entries,
  so a walk that reaches it is answered and reported rather than stopped. C19 answers No — only
  wallets held by people or companies: Harness Holdings pays people and companies, the stipulation
  is the tighter law, and it is the one that proves the chain. WO1 names Ben Signatory as the one
  person who holds the wallet — he is its Officer — and WO2 names Harriet Founder, CEO, as the third
  party to its activation and its largest payments. WO3 is 2.00 (the holder alone) and WO4
  10.00 (two signatures enough) — Spec T14 scaled both by a thousand, as every money answer. WA1
  gains Ben beside Ada, so the tiers name three people (Ada, Ben, Harriet) and the read-back is not
  refused; WQ stays at one.

  The money is entered in the base the interview records — "Recorded in US dollars, the base;
  your display currency is shown beside it as you type" (MONEY_NOTE). SPEC T14 (22 September 2026,
  amended 22:35): THE BOOK PAYS IN CENTS. The sandbox estate pays on real chains with real USDC, by
  design, and the book's three payments totalled US$18,249.99 — a sandbox that costs eighteen thousand
  dollars a run is not a sandbox, and one that never pays proves nothing — so every money answer and
  expectation of Harness Holdings is scaled by one thousand: per payment 10.00 (O2, and P3 of the
  payroll dialect), per day 50.00 (O1, and X2), the treasury ceiling 250.00 (T1, in the book for the
  treasury dialect the operating account does not walk), the tiers 2.00 (WO3) and 10.00 (WO4); the
  payments P1 1.25 (within the holder's figure), P2 4.99 (two signatures) and P3 12.00 (three). The
  payments are made in USDC, so 12.00 is above 10.00 whatever the day's AUD rate; the display lens
  the page returns is printed in the report. Nothing else in the book changed. SPEC T18 (24 September 2026,
  from Bear's ruling "Let's move to Arbitrum."): THE BOOK PAYS ON ARBITRUM. C9 answers the network AER 360
  Spec 106 added to the catalog's offer, `Arbitrum One`, which the compiler writes as the registry's id
  `arbitrum`; the chain is one word in one place, aer360_tables.PAYEE_CHAIN, and the payments, the payees,
  the venue probe and every sentence that names a chain follow it. OTHER_NETWORKS mirrors 106's served list
  exactly. The tiers, the holds, the three payments and their outcomes stand as T14 left them; the payee keys
  keep the names they were first minted under (`NORTHWIND_ETHEREUM`, `CONTOSO_ETHEREUM`: the suffix records
  where the label was minted, not where the payee pays), so no address moved. The wallet account is an OPERATIONS account, because the operations
  dialect is the one that asks a per-payment hold (O2), a daily figure (O1) and the pause on a
  new destination (O3, Spec 69) that the three payments exercise.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aer360_tables as T  # noqa: E402

CATALOG_SOURCE = "aeredium/AERAccounts apps/server/src/services/questioncatalog.ts at cf3be4a (Spec 92), CATALOG_VERSION = 14"
CATALOG_VERSION_READ = 14
# THE VERSION THIS BOOK ANSWERS (Spec T11). S3 reports it beside what the estate serves; a question the estate serves that the
# book does not know is reported with this figure in the sentence, so a moved catalog names the two versions it stands between.
CATALOG_VERSION_ANSWERED = 14
RETIRED_IN_V12 = ("C16", "C16C")
# The seven questions catalog version 14 added (Spec 92), by interview; a double standing in for an older estate leaves them out.
ADDED_IN_V14 = {"policy": ("C11A", "C11C", "C19"), "wallet_account": ("WO1", "WO2", "WO3", "WO4")}

# ---------------------------------------------------------------------------
# The estate and its people.
# ---------------------------------------------------------------------------
ESTATE = {
    "company": "Harness Holdings Pty Ltd",
    "client_id": "harness-holdings",
    "email": "harness@aeredium.io",
    "country": "Australia",
    "display_currency": "AUD",
}


class Person(NamedTuple):
    key: str
    name: str
    email: str
    role: str  # the role the invitation asks for: founder (born by the birth script), author, viewer
    census: Optional[str]  # what they PRIMARILY do, as A8 offers it; None for a person not in the census
    does: str


FINANCE_ROLES = ["Enter payments", "Review payments", "Authorise payments", "Release payments"]

PEOPLE: Dict[str, Person] = {
    "harriet": Person("harriet", "Harriet Founder", "harness+harriet@aeredium.io", "founder", "Authorise payments", "the founder, level 1"),
    "ada": Person("ada", "Ada Approver", "harness+ada@aeredium.io", "author", "Release payments", "approves payments"),
    "ben": Person("ben", "Ben Signatory", "harness+ben@aeredium.io", "author", "Authorise payments", "signs changes to the rules"),
    "cora": Person("cora", "Cora Clerk", "harness+cora@aeredium.io", "author", "Enter payments", "enters payments"),
    # S11's fourth invitation: a viewer (the product calls the standing an Overseer). Not in the census.
    "olive": Person("olive", "Olive Overseer", "harness+olive@aeredium.io", "viewer", None, "reads every register and changes nothing"),
}
FOUNDER = "harriet"
AUTHORS_INVITED = ("ada", "ben", "cora")
VIEWER_INVITED = "olive"
CENSUS_ORDER = ("harriet", "ada", "ben", "cora")
PAYMENT_APPROVER = "ada"
PAYMENT_CLERK = "cora"
SECURITY_CONTACT = "harriet"
RUNS_THE_ACCOUNT = "cora"


def census_entries() -> List[Dict[str, str]]:
    return [{"name": PEOPLE[k].name, "email": PEOPLE[k].email, "role": PEOPLE[k].census or ""} for k in CENSUS_ORDER]


# ---------------------------------------------------------------------------
# The roster that whitelists a payee, and its quorum (Spec T9, 20 September 2026).
# ---------------------------------------------------------------------------
# Read from the compiler's own line, not guessed: aeredium/AERAccounts apps/server/src/services/
# onboardingcompiler.ts at 7d809e1 (Spec 89), the block "SPEC 89, COUNT 2 — A QUORUM NEVER EXCEEDS
# ITS ROSTER", which answers which people form the `whitelist_mutation` roster the policy charter
# writes and at what number:
#
#   THE MEMBERS are `governanceSignersFor`'s — the census (A8, as `changeApprovers`) where it names
#   anyone with a work email, else C11's people (`signers`). Harness Holdings' charter names four at
#   A8, so its roster is Harriet Founder, Ada Approver, Ben Signatory and Cora Clerk.
#
#   THE THRESHOLD is `governanceRecordsFor`'s — C12's number over every family where C12A was not
#   answered Yes, else each family's own (C12B, C12C, C12D). Harness Holdings answered C12 = 2 and
#   C12A = No, so the threshold is two.
#
# So a payee is whitelisted when two of these four have approved it, and S6 presses until they have.
# The roster is the census people in A8's order; the quorum is the figure answered at C12. A test
# (tests/test_aer360_answers.py) proves the two agree with the answers given at A8 and C12, so the
# harness's expectation is the charter's and cannot drift from it unnoticed.
WHITELIST_ROSTER = tuple(PEOPLE[k].name for k in CENSUS_ORDER)
WHITELIST_QUORUM = 2


# ---------------------------------------------------------------------------
# The money and the payments.
# ---------------------------------------------------------------------------
MONEY = {
    # Whole figures of the base, as cents, the shape a money answer travels in ({cents: "..."}).
    "per_payment_cents": "1000",          # 10.00 — O2: above it a payment is held for approval (Spec T14: the book pays in cents)
    "per_day_cents": "5000",              # 50.00 — O1: the account's normal day
    "treasury_ceiling_cents": "25000",     # 250.00 — T1, for the treasury dialect (not walked)
    # The signing tiers (Spec 92, WO3 and WO4; Spec T11). The two fields arrive written at one dollar ({cents: "100"}) and the
    # book writes the real figure: the holder alone up to 2.00, two signatures enough up to 10.00, three above it (Spec T14).
    "holder_alone_cents": "200",          # 2.00 — WO3: up to it the holder pays alone, with their own passkey
    "two_signatures_cents": "1000",       # 10.00 — WO4: up to it two signatures are enough; above it all three
}

WALLET_ACCOUNT_NAME = "Operating account"
WALLET_ACCOUNT_PURPOSE = "Operations — day-to-day business payments"
# The wallet's people (Spec 92, WO1 and WO2; Spec T11): Ben holds the wallet, so he is its Officer (`holderTitleFor`: the
# Principal of a customer's account, the Officer of every other wallet); Harriet, CEO, is the third party to its activation.
WALLET_HOLDER = "ben"
WALLET_HOLDER_TITLE = "Officer"
THIRD_PARTY = "harriet"
THIRD_PARTY_TITLE = "CEO"
THIRD_PARTY_TITLES = ("CEO", "CFO", "COO")  # questioncatalog.ts THIRD_PARTY_TITLES, WO2's title field


class Payment(NamedTuple):
    key: str
    payee_key: Optional[str]   # a pinned payee, or None for the one-off to the unlisted address
    payee_name: str
    amount: str                # the figure, as a plain decimal of the asset
    invoice: str
    expect: str                # the spec's word for what should happen
    why: str

    @property
    def amount_minor(self) -> str:
        return T.minor_units(self.amount, T.ASSET_DECIMALS[T.PAYMENT_ASSET])


# The payee keys are the pinned labels' names (aer360_tables.py PINNED): `_ETHEREUM` records where a label was first minted, never where
# the payee pays — every payment is made on T.PAYEE_CHAIN, and S6 and S7 resolve a payee by (name, chain) before paying it (Spec T18 §2).
PAYMENTS: List[Payment] = [
    Payment("P1", "NORTHWIND_ETHEREUM", "Northwind Supplies", "1.25", "HH-0001", "proceeds to approval",
            "listed, within limits; within the holder's own figure (WO3)"),
    Payment("P2", None, "Unlisted destination", "4.99", "HH-0002", "waits",
            "to an address not on the list, under an account that pauses the first payment somewhere new (Spec 69)"),
    Payment("P3", "CONTOSO_ETHEREUM", "Contoso Legal", "12.00", "HH-0003", "held",
            "above the per-payment limit of 10.00; above the two-signature figure (WO4)"),
]

# ---------------------------------------------------------------------------
# The catalog, as version 14 asks it: id, kind, the gate it hangs on, and its closed options.
# Order is the catalog's own; the interview serves questions in this order, skipping the gated.
# ---------------------------------------------------------------------------
class Question(NamedTuple):
    id: str
    kind: str
    depends_on: Optional[Dict[str, Any]]  # {"questionId": ..., "oneOf": [...]}
    options: Optional[List[str]]
    required: bool = False


LEVELS_BENEATH = [
    "Yes — our custody clients",
    "Yes — partial custodians who hold alongside us",
    "Yes — divisions of this company with their own limits",
    "Yes — more than one of these",
]
# The networks C9 and X1 offer beside Aeredium, exactly as AER 360 Spec 106 serves them (questioncatalog.ts OTHER_NETWORKS, 24 September
# 2026): Arbitrum One after Ethereum, and nothing else in the list moved. The book answers both with T.C9_NETWORK_CHOICE; a page still
# offering the three of 21 September is an estate before Spec 106, and S3 stops at C9 before anything is amended (Spec T18 §4).
OTHER_NETWORKS = ["Ethereum", "Arbitrum One", "Solana", "Bitcoin"]
ONE_TO_FIVE = ["1", "2", "3", "4", "5"]
PAYROLL = "Payroll — paying the people who work here"
TREASURY = "Treasury — holding and protecting the company’s digital assets"
OPERATIONS = "Operations — day-to-day business payments"
TRADING = "Trading — buying and selling on venues"
AGENT = "Agents — the wallet account holding your agents’ wallets"
OTHER = "Something else (describe it, and the general dialect is used)"
CUSTOMER = "A customer’s account — the customer initiates, the company approves above a figure"  # W1's option added by version 14
NON_AGENT_PURPOSES = [PAYROLL, TREASURY, OPERATIONS, TRADING, OTHER, CUSTOMER]  # the purposes that hold a wallet a person may hold
# Version 14's own words (questioncatalog.ts PAYEE_APPROVAL_OPTIONS, VENUE_CONTRACT_OPTIONS, HOLDER_OPTIONS), byte for byte.
PAYEE_APPROVAL_PAYMENT_APPROVERS = "The people who approve payments (the people you named just above), at the number you set for a payment"
PAYEE_APPROVAL_CHANGE_APPROVERS = "The people who may change these rules, at the number you set for a change"
PAYEE_APPROVAL_CFO = "The company’s CFO, or the person the CFO has delegated"
VENUE_YES = "Yes"
VENUE_NO = "No — only wallets held by people or companies"
HOLDER_PERSON = "One person, named here"
HOLDER_NO_ONE = "No one: this wallet is held by no person’s device and is visible and operated from AER 360 only"
WRITTEN_ONE_DOLLAR = {"cents": "100"}  # the figure WO3 and WO4 arrive written with (questioncatalog.ts WRITTEN_ONE_DOLLAR)
WA2_YES = "Yes — one person can both submit and release, where the quorum allows it"
WA2_NO = ("No — every release needs at least one approver who did not submit it; with a quorum of 1 "
          "this means someone other than the submitter must approve")


def _gate(question_id: str, one_of: Sequence[str]) -> Dict[str, Any]:
    return {"questionId": question_id, "oneOf": list(one_of)}


POLICY_CATALOG: List[Question] = [
    Question("A1", "text", None, None, True),
    Question("A4", "text", None, None, True),
    Question("A5", "currency", None, None, True),  # options dressed at run time from the currency registry
    Question("A8", "list", None, None, True),
    Question("A9", "single_choice", None, ["No — this company stands alone"] + LEVELS_BENEATH, True),
    Question("A11", "single_choice", None, ["No", "Yes"], True),
    Question("B1", "statement", None, None),
    Question("B2", "statement", None, None),
    Question("B3", "statement", None, None),
    Question("B4", "multi_choice", _gate("A9", LEVELS_BENEATH),
             ["Level 2 may see level 3", "Level 3 may see level 4 — the agents and their wallets"]),
    Question("C9S", "statement", None, None),
    Question("C9", "multi_choice", None, list(OTHER_NETWORKS)),
    Question("C10", "single_choice", None, list(ONE_TO_FIVE), True),
    Question("C11", "roster_multi", None, None, True),
    # version 14 (Spec 92): who approves a new payee, and — behind the third answer only — the CFO or the CFO's delegate
    Question("C11A", "single_choice", None, [PAYEE_APPROVAL_PAYMENT_APPROVERS, PAYEE_APPROVAL_CHANGE_APPROVERS, PAYEE_APPROVAL_CFO], True),
    Question("C11C", "list", _gate("C11A", [PAYEE_APPROVAL_CFO]), None, True),
    Question("C15", "single_choice", None, ["No", "Yes"], True),
    # version 14 (Spec 92): may a payee address be a venue's contract; its id is C19, not the C16 the spec drafted (C16 is retired for ever)
    Question("C19", "single_choice", None, [VENUE_YES, VENUE_NO], True),
    Question("C18", "list", None, None, True),
    Question("C12", "single_choice", None, list(ONE_TO_FIVE), True),
    Question("C12A", "single_choice", None, ["No", "Yes"], True),
    Question("C12B", "single_choice", _gate("C12A", ["Yes"]), list(ONE_TO_FIVE)),
    Question("C12C", "single_choice", _gate("C12A", ["Yes"]), list(ONE_TO_FIVE)),
    Question("C12D", "single_choice", _gate("C12A", ["Yes"]), list(ONE_TO_FIVE)),
    Question("D0", "statement", None, None),
    Question("D4", "single_choice", _gate("A11", ["Yes"]),
             ["Pause it — hold everything for a person to review",
              "Stop it cold — halt the agent’s account until a person restores it"]),
    Question("E0", "statement", _gate("A9", LEVELS_BENEATH), None),
    Question("R0", "statement", None, None),
    Question("R1", "single_choice", None, ["No", "Yes"], True),
    Question("R2", "multi_choice", _gate("R1", ["Yes"]), ["Self-recovery", "Recovery by your approvers acting together"]),
    Question("R3", "single_choice", _gate("R1", ["Yes"]), ["1", "2"]),
    Question("G1", "statement", None, None),
]

# Version 11 asked these two between C15 and C18; version 12 retired them (spec 73). Kept so the
# book covers the frozen v11 ids the tests read, with the options v11 offered (commit 5492703^).
RETIRED_POLICY_QUESTIONS: List[Question] = [
    Question("C16", "single_choice", None, ["4 hours", "24 hours", "3 days", "Custom"], True),
    Question("C16C", "text", _gate("C16", ["Custom"]), None),
]

ACCOUNT_CATALOG: List[Question] = [
    Question("W0", "statement", None, None),
    Question("WN", "text", None, None, True),
    Question("W1", "single_choice", None, [PAYROLL, TREASURY, OPERATIONS, TRADING, AGENT, OTHER, CUSTOMER], True),
    Question("P1", "list", _gate("W1", [PAYROLL]), None, True),
    Question("P2", "single_choice", _gate("W1", [PAYROLL]),
             ["Monthly, on a set day", "Fortnightly", "Weekly", "Custom — days, hours, and the timezone the run is anchored to"]),
    Question("P3", "money", _gate("W1", [PAYROLL]), None),
    Question("P4", "roster_single", _gate("W1", [PAYROLL]), None),
    Question("T1", "money", _gate("W1", [TREASURY]), None, True),
    Question("T3", "single_choice", _gate("W1", [TREASURY]), ["Yes — always", "Only above the usual approval band"]),
    Question("T4", "percent", _gate("W1", [TREASURY]), None),
    Question("O1", "money", _gate("W1", [OPERATIONS, OTHER]), None),
    Question("O2", "money", _gate("W1", [OPERATIONS, OTHER]), None),
    Question("O3", "single_choice", _gate("W1", [OPERATIONS, OTHER]), ["Yes", "List only", "Anyone, freely"]),
    Question("O4", "roster_single", _gate("W1", [OPERATIONS, OTHER]), None),
    Question("X1", "multi_choice", _gate("W1", [TRADING]), list(OTHER_NETWORKS)),
    Question("X1V", "list", _gate("W1", [TRADING]), None),
    Question("X2", "money", _gate("W1", [TRADING]), None),
    Question("X3", "single_choice", _gate("W1", [TRADING]), ["Pause for review at 1.5× the usual pace", "Pause at 2×", "Pause at 3×"]),
    Question("X4", "single_choice", _gate("W1", [TRADING]), ["No — the list only", "Pause anywhere new for approval"]),
    Question("X5", "percent", _gate("W1", [TRADING]), None),
    Question("X6", "percent", _gate("W1", [TRADING]), None),
    Question("X7", "single_choice", _gate("W1", [TRADING]), ["No", "Yes"]),
    Question("X8", "single_choice", _gate("W1", [TRADING]), ["No", "Yes"]),
    Question("AG0", "statement", _gate("W1", [AGENT]), None),
    Question("AG2", "money", _gate("W1", [AGENT]), None, True),
    Question("AG3", "money", _gate("W1", [AGENT]), None, True),
    Question("AG5", "single_choice", _gate("W1", [AGENT]),
             ["Pause it — hold everything for a person to review", "Stop it cold — halt the account until a person restores it"]),
    Question("AG6", "roster_single", _gate("W1", [AGENT]), None),
    Question("PN0", "statement", None, None),
    Question("PN1", "single_choice", None, ["No", "Yes"], True),
    Question("PN2", "list", _gate("PN1", ["Yes"]), None),
    Question("WQ", "single_choice", None, list(ONE_TO_FIVE), True),
    Question("WA1", "list", None, None, True),
    Question("WA2", "single_choice", None, [WA2_YES, WA2_NO], True),
    # version 14 (Spec 92): the wallet's people and tiers, for every purpose but the agents'; WO3 only where WO1 names a person
    Question("WO1", "person_or_none", _gate("W1", NON_AGENT_PURPOSES), [HOLDER_PERSON, HOLDER_NO_ONE], True),
    Question("WO2", "list", _gate("W1", NON_AGENT_PURPOSES), None, True),
    Question("WO3", "money", _gate("WO1", [HOLDER_PERSON]), None, True),
    Question("WO4", "money", _gate("W1", NON_AGENT_PURPOSES), None, True),
    Question("WCW", "statement", _gate("W1", [PAYROLL, TREASURY, OPERATIONS, TRADING, OTHER, CUSTOMER]), None),
    Question("WCA", "statement", _gate("W1", [AGENT]), None),
    Question("WG1", "statement", None, None),
]

CATALOGS: Dict[str, List[Question]] = {"policy": POLICY_CATALOG, "wallet_account": ACCOUNT_CATALOG}
INTERVIEW_TYPES = ("policy", "wallet_account")


def question(interview_type: str, question_id: str) -> Optional[Question]:
    for q in CATALOGS[interview_type] + (RETIRED_POLICY_QUESTIONS if interview_type == "policy" else []):
        if q.id == question_id:
            return q
    return None


# ---------------------------------------------------------------------------
# The answers, in the wire shape `POST /v1/onboarding/interviews/:id/answers` takes as `value`
# (`services/onboarding.ts`, AnswerValue): statement {acknowledged}, single_choice {choice},
# multi_choice {choices}, text and currency {text}, list {entries}, money {cents}, percent
# {percent}, count {count}, roster_single and roster_multi {people} (work emails, as the wizard
# collects them — `apps/web/src/screens/Onboarding.tsx`, "Email addresses, comma separated"),
# person_or_none {choice, person: {name, email}} or {choice} alone (Spec 92, WO1).
# ---------------------------------------------------------------------------
ACK: Dict[str, Any] = {"acknowledged": True}


def _payee_entries() -> List[Dict[str, str]]:
    return [{"label": p["name"], "address": T.address(p["key"])} for p in T.PAYEES]


POLICY_ANSWERS: Dict[str, Dict[str, Any]] = {
    "A1": {"text": ESTATE["company"]},
    "A4": {"text": ESTATE["country"]},
    "A5": {"text": ESTATE["display_currency"]},
    "A8": {"entries": census_entries()},
    "A9": {"choice": "No — this company stands alone"},
    "A11": {"choice": "No"},
    "B1": ACK,
    "B2": ACK,
    "B3": ACK,
    "B4": {"choices": []},  # sight granted to no level beneath; not served while A9 is No
    "C9S": ACK,
    "C9": {"choices": [T.C9_NETWORK_CHOICE]},
    "C10": {"choice": "1"},
    "C11": {"people": [PEOPLE[PAYMENT_APPROVER].email]},
    # Spec T11: a new payee is approved by the change approvers — the census at C12's count of two, the roster T10 asserts in S6
    "C11A": {"choice": PAYEE_APPROVAL_CHANGE_APPROVERS},
    # asked only behind C11A's third answer, which the book does not choose; written so a walk that reaches it is answered, not stopped
    "C11C": {"entries": []},
    "C15": {"choice": "Yes"},
    # Spec T11: Harness Holdings pays people and companies; the stipulation is the tighter law and the one that proves the chain
    "C19": {"choice": VENUE_NO},
    "C16": {"choice": "24 hours"},  # version 11 only; never served by version 12
    "C16C": {"text": ""},           # asked only behind Custom, which the book does not choose
    "C18": {"entries": [{"name": PEOPLE[SECURITY_CONTACT].name, "email": PEOPLE[SECURITY_CONTACT].email}]},
    "C12": {"choice": "2"},
    "C12A": {"choice": "No"},
    "C12B": {"choice": "2"},
    "C12C": {"choice": "2"},
    "C12D": {"choice": "2"},
    "D0": ACK,
    "D4": {"choice": "Stop it cold — halt the agent’s account until a person restores it"},  # the catalog recommends Stop it cold
    "E0": ACK,
    "R0": ACK,
    "R1": {"choice": "No"},          # the least the catalog allows
    "R2": {"choices": ["Self-recovery"]},
    "R3": {"choice": "1"},
    "G1": ACK,
}

ACCOUNT_ANSWERS: Dict[str, Dict[str, Any]] = {
    "W0": ACK,
    "WN": {"text": WALLET_ACCOUNT_NAME},
    "W1": {"choice": WALLET_ACCOUNT_PURPOSE},
    "P1": {"entries": _payee_entries()},
    "P2": {"choice": "Monthly, on a set day"},
    "P3": {"cents": MONEY["per_payment_cents"]},
    "P4": {"people": [PEOPLE[RUNS_THE_ACCOUNT].email]},
    "T1": {"cents": MONEY["treasury_ceiling_cents"]},
    "T3": {"choice": "Yes — always"},  # the catalog recommends it
    "T4": {"percent": None},
    "O1": {"cents": MONEY["per_day_cents"]},
    "O2": {"cents": MONEY["per_payment_cents"]},
    "O3": {"choice": "Yes"},           # the catalog recommends it: pause the first payment to somewhere new
    "O4": {"people": [PEOPLE[RUNS_THE_ACCOUNT].email]},
    "X1": {"choices": [T.C9_NETWORK_CHOICE]},
    "X1V": {"entries": _payee_entries()},
    "X2": {"cents": MONEY["per_day_cents"]},
    "X3": {"choice": "Pause at 2×"},   # recommended
    "X4": {"choice": "No — the list only"},  # recommended
    "X5": {"percent": None},
    "X6": {"percent": None},
    "X7": {"choice": "No"},
    "X8": {"choice": "No"},
    "AG0": ACK,
    "AG2": {"cents": MONEY["per_payment_cents"]},
    "AG3": {"cents": MONEY["per_day_cents"]},
    "AG5": {"choice": "Stop it cold — halt the account until a person restores it"},  # recommended
    "AG6": {"people": []},
    "PN0": ACK,
    "PN1": {"choice": "No"},
    "PN2": {"entries": []},
    "WQ": {"choice": "1"},
    # Spec T11: Ben beside Ada, so the tiers name three people with WO2's Harriet and the read-back is not refused (tiersNeedThreePeople)
    "WA1": {"entries": [{"name": PEOPLE[PAYMENT_APPROVER].name, "email": PEOPLE[PAYMENT_APPROVER].email},
                        {"name": PEOPLE[WALLET_HOLDER].name, "email": PEOPLE[WALLET_HOLDER].email}]},
    "WA2": {"choice": WA2_YES},
    # Spec 92's wallet people and tiers (Spec T11). WO1 in the person_or_none shape: the choice, and the person behind the first option.
    "WO1": {"choice": HOLDER_PERSON, "person": {"name": PEOPLE[WALLET_HOLDER].name, "email": PEOPLE[WALLET_HOLDER].email}},
    "WO2": {"entries": [{"name": "Harriet", "surname": "Founder", "email": PEOPLE[THIRD_PARTY].email, "title": THIRD_PARTY_TITLE}]},
    "WO3": {"cents": MONEY["holder_alone_cents"]},    # 2.00 — arrives written at one dollar; the book writes the real figure
    "WO4": {"cents": MONEY["two_signatures_cents"]},  # 10.00 — arrives written at one dollar; the book writes the real figure
    "WCW": ACK,
    "WCA": ACK,
    "WG1": ACK,
}

ANSWERS: Dict[str, Dict[str, Dict[str, Any]]] = {"policy": POLICY_ANSWERS, "wallet_account": ACCOUNT_ANSWERS}


# ---------------------------------------------------------------------------
# The shape an answer takes once the estate has stored it (Spec T8).
# ---------------------------------------------------------------------------
def _stored_key(key: str) -> tuple:
    encoded = key.encode("utf-8")
    return (len(encoded), encoded)


def as_the_estate_stores(value: Any) -> Any:
    """
    An answer as the estate holds it once written, which is the order the read-back speaks it in.

    `answers.value` is a jsonb column (`apps/server/src/db/onboardingschema.ts`, `value: jsonb('value')`),
    and PostgreSQL's jsonb does not keep the order an object's keys arrived in: it stores them shortest
    key first and, at equal length, in byte order (jsonb_util.c, lengthCompareJsonbStringValue), and a
    driver reading the column back hands the estate an object in that order. The read-back speaks a
    list entry's values in the order it finds them (`services/onboarding.ts`, the `spoken` switch:
    `Object.values(e).join(' — ')`), so the census the harness sends as name, email, role is spoken as
    `name — role — email` — which is what the estate said on 20 September 2026 and what the harness's
    own rendering, in the order it had sent, called a disagreement. Nested objects are reordered the
    same way; lists keep their order, as jsonb keeps it; scalars are returned as they are.
    """
    if isinstance(value, dict):
        return {key: as_the_estate_stores(value[key]) for key in sorted(value.keys(), key=_stored_key)}
    if isinstance(value, list):
        return [as_the_estate_stores(item) for item in value]
    return value


class UnknownQuestion(Exception):
    """The estate served a question the book does not know. The run stops at the station and prints it."""

    def __init__(self, interview_type: str, question_id: str, prompt: str, kind: str):
        super().__init__("the answer book has no answer for %s question %s (%s): %s" % (interview_type, question_id, kind, prompt))
        self.interview_type = interview_type
        self.question_id = question_id
        self.prompt = prompt
        self.kind = kind


class AnswerDoesNotFit(Exception):
    """The book's answer is not one the served page offers, or the served kind is not the book's."""

    def __init__(self, question_id: str, prompt: str, kind: str, cause: str, offered: Optional[List[str]] = None):
        super().__init__("%s (%s): %s" % (question_id, kind, cause))
        self.question_id = question_id
        self.prompt = prompt
        self.kind = kind
        self.cause = cause
        self.offered = offered


SHAPE_OF_KIND = {
    "statement": "acknowledged",
    "single_choice": "choice",
    "multi_choice": "choices",
    "text": "text",
    "currency": "text",
    "list": "entries",
    "money": "cents",
    "percent": "percent",
    "count": "count",
    "roster_single": "people",
    "roster_multi": "people",
    "person_or_none": "choice",  # Spec 92: {choice, person} behind the first option, {choice} alone behind "No one"
}


def answer_for(interview_type: str, served: Dict[str, Any]) -> Dict[str, Any]:
    """
    The book's answer for the question a page served (`page.question`), after checking that the
    served kind is the book's kind and that a choice is among the options the page offers.
    """
    question_id = str(served.get("questionId", ""))
    prompt = str(served.get("prompt", ""))
    kind = str(served.get("kind", ""))
    book = ANSWERS.get(interview_type, {})
    if question_id not in book:
        raise UnknownQuestion(interview_type, question_id, prompt, kind)
    known = question(interview_type, question_id)
    if known is not None and kind and kind != known.kind:
        raise AnswerDoesNotFit(question_id, prompt, kind, "the estate serves it as %s; the book knows it as %s" % (kind, known.kind))
    value = book[question_id]
    field = SHAPE_OF_KIND.get(kind)
    if field is not None and field not in value:
        raise AnswerDoesNotFit(question_id, prompt, kind, "the book's answer carries no %r for a %s question" % (field, kind))
    offered = served.get("options")
    if isinstance(offered, list) and offered:
        chosen = [value["choice"]] if "choice" in value else list(value.get("choices", []))
        if kind == "currency":
            chosen = [value.get("text")]
        for choice in chosen:
            if choice not in offered:
                raise AnswerDoesNotFit(question_id, prompt, kind,
                                       "the book answers %r, which the page does not offer" % (choice,), [str(o) for o in offered])
    return value


# ---------------------------------------------------------------------------
# The walk the book expects: which questions are visible given its own answers, in the catalog's
# order. The dry run prints one answer per visible question; the live run follows the server.
# ---------------------------------------------------------------------------
def _visible(q: Question, answers: Dict[str, Dict[str, Any]]) -> bool:
    if not q.depends_on:
        return True
    gate = answers.get(q.depends_on["questionId"])
    if not gate:
        return False
    chosen = gate.get("choice")
    if isinstance(chosen, str):
        return chosen in q.depends_on["oneOf"]
    choices = gate.get("choices")
    if isinstance(choices, list):
        return any(c in q.depends_on["oneOf"] for c in choices)
    return False


def expected_walk(interview_type: str) -> List[Question]:
    """The questions a version-14 estate serves for this book, in order."""
    answers = ANSWERS[interview_type]
    return [q for q in CATALOGS[interview_type] if _visible(q, answers)]


def all_question_ids(interview_type: str) -> List[str]:
    """Every id the book answers for an interview type: the live catalog's and, for the policy, the two v11 retired."""
    ids = [q.id for q in CATALOGS[interview_type]]
    if interview_type == "policy":
        ids += [q.id for q in RETIRED_POLICY_QUESTIONS]
    return ids


def kind_of(interview_type: str, question_id: str) -> Optional[str]:
    q = question(interview_type, question_id)
    return q.kind if q else None
