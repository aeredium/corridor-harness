"""
AN ESTATE THAT HOLDS BITCOIN (Spec T32, 14 November 2026): the estate double of tests/test_aer360_double.py, extended by subclass with what the
estate's Spec AER360-BTC-1 built — the question C9B of catalog version 20, heldNetworks on the compiled charter, the line beside a Yes on the
read-back, the two reads (GET /v1/aer360/bitcoin and GET /v1/aer360/bitcoin/wallets/:walletId), the road's three states and its limit, and
BITCOIN_HELD_NOT_PAID at the payee door, the set's review and the run's creation.

WHAT THIS DOUBLE IS HELD TO, AND WHAT IT IS NOT. The standing law (4 September 2026) is that a double is at least as strict as the service it
stands in for, with the service's own sentence and status. Every double before this one was a re-statement of the estate's CODE. This one
cannot be: aeredium/AERAccounts stands outside the harness's working folder, and the builder of Spec T32 read the estate's SPECIFICATION alone,
as the brief carries it whole. So:

  - every code, status, word and sentence the specification gives is restated here as a literal (never read from aer360_tables.py, so a wrong pin
    in the harness's table is a sentence this double does not say), and a test holds the two to each other;
  - where the specification names a thing and gives neither its words nor its field, the words and the field names below are THIS DOUBLE'S OWN,
    marked "the double's own words": the line beside a Yes on the read-back, the closed road's sentence around the setting it must name, the met
    stop's sentence, the limit's, a silent source's, the sentence of a wallet that shows no address, and the shapes of the two reads beyond the
    words held, open, row_closed, silent, cause 'tips_apart' and historyWhole. The harness reads the two answers by the specification's words
    alone (it finds an address by its form, a sentence by being one, the sources by the word in their key), so the first live run, not this
    double, is what proves those shapes; a test here proves the harness reads a shape that names its fields otherwise.

The dials: `bitcoin_held` (None reads the newest written policy charter's heldNetworks, as the estate's one reader does; True and False say it
outright, for a test that walks no interview); `bitcoin_road` — "open", "closed" (BITCOIN_SOURCES names fewer than two sources), "stopped" (a stop
standing: the latched refusal) or "met" (the stop as the caller whose read met the difference is told it); `main_network_open` (the constant
BITCOIN_MAIN_NETWORK_OPEN, false until brief AER360-BTC-2); `list_refuses_on_a_closed_road` (whether the list, which reads no chain, refuses on a
closed road: the specification does not say, so both are here and the harness walks both); `bitcoin_reads_limited` (True: the caller is past the
limit on both routes; "readings": on the wallet's reading alone); `funding_wallet_point` (False: a funding wallet born before the point was kept
on the trail, which shows no address and says why); `payment_doors` — "held_not_paid" (the specification), "not_yet" (a door that answers
CHAIN_RECEIVABLE_ONLY, which the specification says is never said of Bitcoin) or "held_and_moved" (the sentence as it stood before Finding 8);
`review_refuses` — "thrown" (422 on the answer) or "on the gate" (200 with the refusal on the gate's row); and `bitcoin_fault`, one fault at a
time for the tests that prove a finding: "readback_says_moved", "nothing_beside_the_yes", "charter_names_the_main_network",
"address_of_the_main_network", "wallet_says_nothing", "one_source", "reading_of_another_address", "latched_names_a_wallet", "silent",
"tips_apart", "tips_apart_in_other_words", "other_field_names".
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_tables as T  # noqa: E402
import tests.test_aer360_double as D  # noqa: E402
from tests.test_aer360_double import EstateDouble, Refusal  # noqa: E402

# --- the specification's own codes, statuses and sentences, restated as literals -------------------------------------------------------------
BITCOIN_HELD_NOT_PAID = "BITCOIN_HELD_NOT_PAID"        # "The refusals": 422
BITCOIN_ROAD_CLOSED = "BITCOIN_ROAD_CLOSED"            # "The refusals": 503
BITCOIN_SOURCES_DISAGREE = "BITCOIN_SOURCES_DISAGREE"  # "The refusals": 503
BITCOIN_READS_LIMITED = "BITCOIN_READS_LIMITED"        # Finding 3: 429
CHAIN_RECEIVABLE_ONLY = "CHAIN_RECEIVABLE_ONLY"        # "What the repository held": the code never said of Bitcoin
CHAIN_RECEIVABLE_ONLY_SENTENCE = "Funds can be received on this chain but not paid out from it yet"
HELD_NOT_PAID_SENTENCE = ("Bitcoin is held on this estate as a store of value and is not a method of payment, because a Bitcoin payment takes about an hour "
                          "to be final.")
HELD_AND_MOVED_SENTENCE = ("Bitcoin is held and moved on this estate and is not a method of payment, because a Bitcoin payment takes about an hour to be "
                           "final.")  # section 2, as it stood before Finding 8 reworded it
LATCHED_SENTENCE = ("The sources this service reads Bitcoin through did not answer alike on the movements of an address. Their tips stood at 1,002 and "
                    "1,002, and the bound between them is 1 block. The Bitcoin road is stopped: nothing is read on it, and it opens by itself once the "
                    "sources answer alike again.")
ADDRESS_OPENS_LATER_SENTENCE = ("Your charter says that your company will hold bitcoin, and that answer is kept. No Bitcoin address is shown yet: your "
                                "company's Bitcoin address opens when moving bitcoin out is built, so that no bitcoin is sent to an address this estate "
                                "cannot yet move it from. Nothing is asked of you until then.")
TIPS_APART_SENTENCE = ("The sources this service reads Bitcoin through stood a block apart while this address was read, so what each says the address "
                       "holds is said of a different block. The balance is not stated on one source alone, so nothing is shown. Nothing is wrong with the "
                       "wallet; ask again in a moment.")
MOVING_NOT_BUILT_SENTENCE = "Moving bitcoin out is not yet built."
# --- the double's own words, where the specification gives the sense and not the words --------------------------------------------------------
ROAD_CLOSED_SENTENCE = ("The Bitcoin road is closed on this deployment: BITCOIN_SOURCES names fewer than two sources to read Bitcoin through. Nothing was "
                        "read.")
MET_SENTENCE = ("The sources this service reads Bitcoin through did not answer alike on the movements of this address: the first source answered 3 "
                "movements in blocks and the second source 4, at tips 1,002 and 1,002. The Bitcoin road is stopped.")
READS_LIMITED_SENTENCE = "This credential has asked for 20 Bitcoin readings in the last minute, which is the limit. Ask again in 42 seconds; nothing was read."
SILENT_SENTENCE = ("The first source did not answer within 15,000 milliseconds, so nothing is shown on the other source alone. Nothing is wrong with the "
                   "wallet; ask again in a moment.")
NOT_HELD_SENTENCE = "Your charter does not say that your company holds bitcoin, so no Bitcoin address is shown."
FOUNDERS_SENTENCE = "Some companies keep part of their value in bitcoin, as a store of value."
TEST_NETWORK_HINT = ("This is a test network address. Test coin has no value, and bitcoin of the Bitcoin network must not be sent to it.")
SOLANA_KEY_SENTENCE = "This wallet's key is a Solana key, which is not of Bitcoin's curve, so it shows no Bitcoin address."
NO_POINT_SENTENCE = ("This wallet was born before its key's public point was kept on the trail, so no Bitcoin address can be shown for it. Send this "
                     "sentence to AEREDIUM.")
HELD_READBACK_QUESTION_ID = "C9B_HELD"
HELD_READBACK_PROMPT = "What holding bitcoin does on this estate"
HELD_READBACK_SANDBOX = ("Each wallet of this estate shows a Bitcoin test network address derived from its own key. Test coin sent to it is read through "
                         "two sources that must agree and is stated in both columns. No payment door takes bitcoin. Moving bitcoin out is not yet built.")
HELD_READBACK_SAYS_MOVED = "Bitcoin is held here and can be moved from here."
DID_NOT = {"payee": "Nothing was saved.", "review": "Nothing was reviewed for payment and nothing was created.", "run": "No run was created and nothing was sent."}

D.STATUS.update({BITCOIN_HELD_NOT_PAID: 422, BITCOIN_ROAD_CLOSED: 503, BITCOIN_SOURCES_DISAGREE: 503, BITCOIN_READS_LIMITED: 429, CHAIN_RECEIVABLE_ONLY: 422})
D.MESSAGES.update({BITCOIN_HELD_NOT_PAID: HELD_NOT_PAID_SENTENCE, BITCOIN_ROAD_CLOSED: ROAD_CLOSED_SENTENCE, BITCOIN_SOURCES_DISAGREE: LATCHED_SENTENCE,
                   BITCOIN_READS_LIMITED: READS_LIMITED_SENTENCE, CHAIN_RECEIVABLE_ONLY: CHAIN_RECEIVABLE_ONLY_SENTENCE})


def bitcoin_address_for_tests(label: str, network: str = "bitcoin-testnet") -> str:
    """
    A string of the FORM of a native SegWit address of `network` — the prefix, the length and bech32's alphabet — made from a label for the tests
    alone. It is the double's, never the harness's: its last six characters are not a checksum, no key stands behind it, and nothing is ever
    sent to it.
    """
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    tail = hashlib.sha256(digest).digest()[:6]
    return {"bitcoin": "bc1q", "bitcoin-testnet": "tb1q"}[network] + "".join(T.BECH32_ALPHABET[b % 32] for b in digest + tail)


class BitcoinEstate(EstateDouble):
    """The estate double at catalog version 20, after Spec AER360-BTC-1: an estate that may hold bitcoin as a store of value."""

    def __init__(self, bitcoin_road: str = "open", bitcoin_held: Optional[bool] = None, main_network_open: bool = False,
                 list_refuses_on_a_closed_road: bool = False, bitcoin_reads_limited: Any = False, funding_wallet_point: bool = True,
                 payment_doors: str = "held_not_paid", review_refuses: str = "thrown", bitcoin_fault: Optional[str] = None, **kwargs: Any):
        if bitcoin_road not in ("open", "closed", "stopped", "met"):
            raise ValueError("bitcoin_road is open, closed, stopped or met, not %r" % bitcoin_road)
        if payment_doors not in ("held_not_paid", "not_yet", "held_and_moved"):
            raise ValueError("payment_doors is held_not_paid, not_yet or held_and_moved, not %r" % payment_doors)
        if review_refuses not in ("thrown", "on the gate"):
            raise ValueError("review_refuses is thrown or on the gate, not %r" % review_refuses)
        self.bitcoin_road = bitcoin_road
        self.bitcoin_held = bitcoin_held
        self.main_network_open = main_network_open
        self.list_refuses_on_a_closed_road = list_refuses_on_a_closed_road
        self.bitcoin_reads_limited = bitcoin_reads_limited
        self.funding_wallet_point = funding_wallet_point
        self.payment_doors = payment_doors
        self.review_refuses = review_refuses
        self.bitcoin_fault = bitcoin_fault
        self.bitcoin_reads: List[str] = []  # every read counted against a caller: the list and each wallet's reading (the reading of 13 November, Finding 2)
        kwargs.setdefault("catalog_version", D.BITCOIN_FROM_CATALOG_VERSION)
        super().__init__(**kwargs)

    # -- section 1: the charter ------------------------------------------------------------------------------------------------------------------
    def compile_charter(self, interview_type: str, latest: Dict[str, Dict[str, Any]], catalog_version: Optional[int] = None) -> Dict[str, Any]:
        """holdsBitcoinOf and heldNetworksOfCharter: Yes writes heldNetworks — the test network's row on this double's sandbox charter — and recordedHeldNetworks beside it; No, or never asked, writes neither."""
        charter = super().compile_charter(interview_type, latest, catalog_version)
        if interview_type == "policy" and (latest.get("C9B") or {}).get("choice") == "Yes":
            charter["heldNetworks"] = ["bitcoin"] if self.bitcoin_fault == "charter_names_the_main_network" else ["bitcoin-testnet"]
            charter["recordedHeldNetworks"] = ["bitcoin"]
        return charter

    def readback(self, iv: Dict[str, Any], check_standing: bool = True) -> List[Dict[str, Any]]:
        """The read-back says, beside a Yes, what the answer does — in the double's own words, since the specification gives that sentence's sense alone."""
        out: List[Dict[str, Any]] = []
        for line in super().readback(iv, check_standing):
            out.append(line)
            if line.get("questionId") == "C9B" and not line.get("synthetic") and line.get("spoken") == "Yes" and self.bitcoin_fault != "nothing_beside_the_yes":
                out.append({"questionId": HELD_READBACK_QUESTION_ID, "prompt": HELD_READBACK_PROMPT, "synthetic": True,
                            "spoken": HELD_READBACK_SAYS_MOVED if self.bitcoin_fault == "readback_says_moved" else HELD_READBACK_SANDBOX})
        return out

    # -- sections 3 to 6: the holding, its address and its reading -----------------------------------------------------------------------------------
    def holds_bitcoin(self) -> bool:
        """heldBitcoinNetworkOf: the newest written Policy Interview's charter, read fail-closed — or the dial, for a test that walks no interview."""
        if self.bitcoin_held is not None:
            return bool(self.bitcoin_held)
        return bool((self.newest_written_policy_charter() or {}).get("heldNetworks"))

    def bitcoin_network(self) -> str:
        return "bitcoin-testnet" if self.workspace.get("realm") == "sandbox" else "bitcoin"

    def row_open(self) -> bool:
        """Finding 8: the test network's row is open; the main network's is closed by a constant until brief AER360-BTC-2."""
        return self.bitcoin_network() == "bitcoin-testnet" or self.main_network_open

    def bitcoin_wallets(self) -> List[Dict[str, Any]]:
        """Each wallet in the reader's sight with its address or the sentence for its absence; the field names are the double's own."""
        network = self.bitcoin_network()
        shown_on = "bitcoin" if self.bitcoin_fault == "address_of_the_main_network" else network
        out: List[Dict[str, Any]] = []
        for row in self.register()["wallets"]:
            pressed = self.pressed_wallets.get(row["walletId"]) or {}
            address: Optional[str] = None
            sentence: Optional[str] = None
            if pressed.get("curve") == T.SOLANA_CURVE:
                sentence = SOLANA_KEY_SENTENCE
            elif row.get("funding") and not self.funding_wallet_point:
                sentence = NO_POINT_SENTENCE
            else:
                address = bitcoin_address_for_tests("%s/%s" % (row["walletId"], row["address"]), shown_on)
                sentence = TEST_NETWORK_HINT if network == "bitcoin-testnet" else None
            if address is None and self.bitcoin_fault == "wallet_says_nothing":
                sentence = None
            if self.bitcoin_fault == "other_field_names":
                out.append({"id": row["walletId"], "name": row["name"], "bitcoinAddress": address, "why": sentence})
            else:
                out.append({"walletId": row["walletId"], "walletNumber": row["walletNumber"], "name": row["name"], "address": address, "sentence": sentence})
        return out

    def require_bitcoin_reader(self, network: str, address: Optional[str] = None) -> None:
        """requireBitcoinReader: a closed road is its refusal naming the setting; a stopped road is told `latched` to every read after the one that met the difference, and `met` to that one."""
        if self.bitcoin_road == "closed":
            raise Refusal(BITCOIN_ROAD_CLOSED, ROAD_CLOSED_SENTENCE, {"network": network, "setting": "BITCOIN_SOURCES", "sourcesNamed": 1})
        if self.bitcoin_road == "stopped":
            detail: Dict[str, Any] = {"network": network, "read": "the movements of an address", "tips": [1002, 1002], "lagBlocks": 1}
            if self.bitcoin_fault == "latched_names_a_wallet":
                detail["address"] = bitcoin_address_for_tests("another estate's wallet", network)
            raise Refusal(BITCOIN_SOURCES_DISAGREE, LATCHED_SENTENCE, detail)
        if self.bitcoin_road == "met":
            raise Refusal(BITCOIN_SOURCES_DISAGREE, MET_SENTENCE, {"network": network, "read": "the movements of this address", "tips": [1002, 1002], "lagBlocks": 1,
                                                                 "address": address, "first": 3, "second": 4})

    def take_bitcoin_read(self, caller: Dict[str, Any], on_the_list: bool) -> None:
        """takeBitcoinRead: counted per credential where a reading would be taken — the list as well as each wallet's reading — and refused at the limit."""
        if self.bitcoin_reads_limited is True or (self.bitcoin_reads_limited and not on_the_list):
            raise Refusal(BITCOIN_READS_LIMITED, READS_LIMITED_SENTENCE, {"limit": 20, "retryAfterSeconds": 42})
        self.bitcoin_reads.append(str(caller["credentialId"]))

    def bitcoin_list(self, headers: Dict[str, str]) -> Tuple[int, Any]:
        """GET /v1/aer360/bitcoin: not held and a closed row derive nothing and are not counted; it reads no chain."""
        caller = self.require_caller(headers, "viewer")
        network = self.bitcoin_network()
        if not self.holds_bitcoin():
            return 200, {"held": False, "open": self.row_open(), "network": None, "sentence": NOT_HELD_SENTENCE, "wallets": []}
        if not self.row_open():
            return 200, {"held": True, "open": False, "network": network, "sentence": ADDRESS_OPENS_LATER_SENTENCE, "wallets": []}
        if self.list_refuses_on_a_closed_road:
            self.require_bitcoin_reader(network)
        self.take_bitcoin_read(caller, on_the_list=True)
        if self.bitcoin_fault == "other_field_names":
            return 200, {"held": True, "open": True, "row": network, "said": FOUNDERS_SENTENCE, "wallets": self.bitcoin_wallets()}
        return 200, {"held": True, "open": True, "network": network, "sentence": FOUNDERS_SENTENCE, "wallets": self.bitcoin_wallets()}

    def bitcoin_reading(self, headers: Dict[str, str], wallet_id: str) -> Tuple[int, Any]:
        """
        GET /v1/aer360/bitcoin/wallets/:walletId, in the order the reading of 13 November gives it: the caller known; not held and a closed row
        answered; the wallet looked up (WALLET_NOT_FOUND); the road required; the caller counted; and only then the address, and the reading.
        """
        caller = self.require_caller(headers, "viewer")
        network = self.bitcoin_network()
        if not self.holds_bitcoin():
            return 200, {"state": "not_held", "sentence": NOT_HELD_SENTENCE}
        if not self.row_open():
            return 200, {"state": "row_closed", "sentence": ADDRESS_OPENS_LATER_SENTENCE}
        wallet = next((w for w in self.bitcoin_wallets() if (w.get("walletId") or w.get("id")) == wallet_id), None)
        if wallet is None:
            raise Refusal("WALLET_NOT_FOUND", detail={"walletId": wallet_id}, provenance={"source": "wallets"})
        address = wallet.get("address") or wallet.get("bitcoinAddress")
        self.require_bitcoin_reader(network, address)
        self.take_bitcoin_read(caller, on_the_list=False)
        if address is None:
            return 200, {"state": "no_address", "walletId": wallet_id, "sentence": wallet.get("sentence") or wallet.get("why")}
        if self.bitcoin_fault == "silent":
            return 200, {"state": "silent", "cause": "source_silent", "which": "the first source", "waitedMs": 15000, "sentence": SILENT_SENTENCE}
        if self.bitcoin_fault == "tips_apart":
            return 200, {"state": "silent", "cause": "tips_apart", "sentence": TIPS_APART_SENTENCE}
        if self.bitcoin_fault == "tips_apart_in_other_words":
            return 200, {"state": "silent", "cause": "tips_apart", "sentence": SILENT_SENTENCE}
        if self.bitcoin_fault == "reading_of_another_address":
            address = bitcoin_address_for_tests("another wallet's address", network)
        as_of = {"height": 160854, "sources": 1 if self.bitcoin_fault == "one_source" else 2, "readAt": self._now_iso()}
        if self.bitcoin_fault == "other_field_names":
            return 200, {"outcome": "reading", "wallet": wallet_id, "bitcoinAddress": address, "historyWhole": True, "agreedAt": {"block": 160854, "sourceCount": 2},
                         "heldSatoshisMinor": "0", "movements": [], "note": MOVING_NOT_BUILT_SENTENCE}
        return 200, {"state": "read", "walletId": wallet_id, "address": address, "network": network, "historyWhole": True, "asOf": as_of,
                     "confirmedMinor": "0", "arrivingMinor": "0", "leavingMinor": "0", "movements": [], "moving": MOVING_NOT_BUILT_SENTENCE}

    def dispatch(self, method: str, path: str, headers: Dict[str, str], body: Any, set_cookie: List[Tuple[str, str]]) -> Tuple[int, Any]:
        if method == "GET" and path == "/v1/aer360/bitcoin":
            return self.bitcoin_list(headers)
        m = re.match(r"^/v1/aer360/bitcoin/wallets/([^/]+)$", path)
        if m and method == "GET":
            return self.bitcoin_reading(headers, m.group(1))
        return super().dispatch(method, path, headers, body, set_cookie)

    # -- section 2: held, not paid ---------------------------------------------------------------------------------------------------------------
    def held_not_paid(self, door: str, detail: Dict[str, Any]) -> Refusal:
        """bitcoinHeldNotPaidRefusal: the judgment, followed by what the door did not do — or, by the dials, one of the two answers the specification says are never given."""
        if self.payment_doors == "not_yet":
            return Refusal(CHAIN_RECEIVABLE_ONLY, CHAIN_RECEIVABLE_ONLY_SENTENCE, detail)
        sentence = HELD_AND_MOVED_SENTENCE if self.payment_doors == "held_and_moved" else HELD_NOT_PAID_SENTENCE
        return Refusal(BITCOIN_HELD_NOT_PAID, "%s %s" % (sentence, DID_NOT[door]), detail, provenance={"source": "chain_registry"})

    def create_payee(self, headers: Dict[str, str], body: Any) -> Tuple[int, Any]:
        """The payee door: the default chain and every address's chain, judged before anything else of the payee."""
        self.require_caller(headers, "author", mutating=True)
        payee = body if isinstance(body, dict) else {}
        chains = [payee.get("defaultChain")] + [a.get("chain") for a in (payee.get("addresses") or []) if isinstance(a, dict)]
        named = next((c for c in chains if T.is_bitcoin_chain(c)), None)
        if named is not None:
            raise self.held_not_paid("payee", {"chain": named})
        return super().create_payee(headers, body)

    def review_or_create(self, headers: Dict[str, str], body: Any, create: bool) -> Tuple[int, Any]:
        """The payment entry and the run road: a Bitcoin row is judged first and for every estate, with a written charter or without."""
        self.require_caller(headers, "author", mutating=True)
        pays = (body or {}).get("pays") if isinstance(body, dict) else None
        for index, pay in enumerate(pays if isinstance(pays, list) else []):
            if not isinstance(pay, dict):
                continue
            one_off = pay.get("oneOff") if isinstance(pay.get("oneOff"), dict) else {}
            if T.is_bitcoin_chain(pay.get("chain")) or T.is_bitcoin_chain(one_off.get("chain")):
                refusal = self.held_not_paid("run" if create else "review", {"chain": pay.get("chain"), "rowIndex": index})
                if not create and self.review_refuses == "on the gate":
                    row_refusal = dict(refusal.body()["error"], rowIndex=index)
                    return 200, {"acceptable": False, "acknowledgeable": [], "wallet": None,
                                 "gates": [{"gate": "network_offered", "passed": False, "evidence": "1 row on a network that is held and not paid", "refusals": [row_refusal]}]}
                raise refusal
        return super().review_or_create(headers, body, create)
