"""The chain decoder: approve, transfer, exactInputSingle inside multicall with sweepTokenWithFee, depositForBurn,
receiveMessage and send from fixed calldata, and ERC-20 Transfer logs from a fixed receipt (Spec T1 §6, §11)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402

USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
ROUTER = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
WALLET = "0x1111111111111111111111111111111111111111"
FEE = "0xabd0235C036CBeCb911DC74958B3c8F114cec42a"
CCTP = "0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d"


def word(n):
    return int(n).to_bytes(32, "big")


def addr(a):
    return bytes(12) + bytes.fromhex(a[2:])


def b32(a):
    return bytes(12) + bytes.fromhex(a[2:]) if len(a) == 42 else bytes.fromhex(a[2:]).rjust(32, b"\x00")


def dyn(b):
    return word(len(b)) + b + bytes((-len(b)) % 32)


def bytes_array(items):
    head = word(len(items))
    offsets, body = [], b""
    for item in items:
        offsets.append(32 * len(items) + len(body))
        body += dyn(item)
    return head + b"".join(word(o) for o in offsets) + body


def sel(sig):
    return bytes.fromhex(h.selector(sig)[2:])


def hexs(b):
    return "0x" + b.hex()


class DecoderTest(unittest.TestCase):
    def test_keccak_vectors(self):
        self.assertEqual(h.keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(h.selector("transfer(address,uint256)"), "0xa9059cbb")
        self.assertEqual(h.selector("approve(address,uint256)"), "0x095ea7b3")
        self.assertEqual(h.selector("multicall(bytes[])"), "0xac9650d8")
        self.assertEqual(h.selector("exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))"), "0x04e45aaf")
        self.assertEqual(h.selector("receiveMessage(bytes,bytes)"), "0x57ecfd28")
        self.assertEqual(h.TRANSFER_TOPIC, "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")
        self.assertEqual(h.checksum_address("0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45"), ROUTER)

    def test_approve_and_transfer(self):
        approve = h.decode_call(hexs(sel("approve(address,uint256)") + addr(ROUTER) + word(5_000_000)))
        self.assertEqual(approve["function"], "approve")
        self.assertEqual(approve["args"], {"spender": ROUTER, "amount": 5_000_000})
        transfer = h.decode_call(hexs(sel("transfer(address,uint256)") + addr(WALLET) + word(1_000_000)))
        self.assertEqual(transfer["function"], "transfer")
        self.assertEqual(transfer["args"], {"to": WALLET, "amount": 1_000_000})

    def test_exact_input_single_inside_multicall_with_sweep_token_with_fee(self):
        swap = sel("exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))") + addr(USDC) + addr(WETH) + word(500) + \
            addr(ROUTER) + word(5_000_000) + word(1_900_000_000_000_000) + word(0)
        sweep = sel("sweepTokenWithFee(address,uint256,uint256,address)") + addr(WETH) + word(1_900_000_000_000_000) + word(5) + addr(FEE)
        data = sel("multicall(uint256,bytes[])") + word(1_760_000_000) + word(64) + bytes_array([swap, sweep])
        decoded = h.decode_call(hexs(data))
        self.assertEqual(decoded["function"], "multicall(deadline)")
        self.assertEqual(decoded["args"], {"deadline": 1_760_000_000})
        inner = decoded["inner"]
        self.assertEqual([i["function"] for i in inner], ["exactInputSingle", "sweepTokenWithFee"])
        self.assertEqual(inner[0]["args"]["tokenIn"], USDC)
        self.assertEqual(inner[0]["args"]["tokenOut"], WETH)
        self.assertEqual(inner[0]["args"]["fee"], 500)
        self.assertEqual(inner[0]["args"]["amountIn"], 5_000_000)
        self.assertEqual(inner[0]["args"]["recipient"], ROUTER)
        self.assertEqual(inner[1]["args"], {"token": WETH, "amountMinimum": 1_900_000_000_000_000, "feeBips": 5, "feeRecipient": FEE})
        plain = h.decode_call(hexs(sel("multicall(bytes[])") + word(32) + bytes_array([swap])))
        self.assertEqual(plain["function"], "multicall")
        self.assertEqual(plain["inner"][0]["function"], "exactInputSingle")

    def test_deposit_for_burn(self):
        v2 = sel("depositForBurn(uint256,uint32,bytes32,address,bytes32,uint256,uint32)") + word(5_000_000) + word(6) + b32(WALLET) + addr(USDC) + \
            word(0) + word(500) + word(1000)
        decoded = h.decode_call(hexs(v2))
        self.assertEqual(decoded["function"], "depositForBurn(v2)")
        self.assertEqual(decoded["args"]["amount"], 5_000_000)
        self.assertEqual(decoded["args"]["destinationDomain"], 6)
        self.assertEqual(decoded["args"]["mintRecipient"], WALLET)
        self.assertEqual(decoded["args"]["burnToken"], USDC)
        self.assertEqual(decoded["args"]["maxFee"], 500)
        self.assertEqual(decoded["args"]["minFinalityThreshold"], 1000)
        v1 = sel("depositForBurn(uint256,uint32,bytes32,address)") + word(1) + word(6) + b32(WALLET) + addr(USDC)
        self.assertEqual(h.decode_call(hexs(v1))["function"], "depositForBurn")

    def test_receive_message(self):
        message = bytes(range(1, 60))
        attestation = bytes(range(100, 165))
        data = sel("receiveMessage(bytes,bytes)") + word(64) + word(64 + len(dyn(message))) + dyn(message) + dyn(attestation)
        decoded = h.decode_call(hexs(data))
        self.assertEqual(decoded["function"], "receiveMessage")
        self.assertEqual(decoded["args"]["message"], hexs(message))
        self.assertEqual(decoded["args"]["message_bytes"], 59)
        self.assertEqual(decoded["args"]["attestation_bytes"], 65)

    def test_oft_send(self):
        extra = bytes.fromhex("0003010011010000000000000000000000000000ea60")
        param = word(30101) + b32(WALLET) + word(5_000_000) + word(4_990_000) + word(224) + word(224 + len(dyn(extra))) + \
            word(224 + len(dyn(extra)) + 32) + dyn(extra) + dyn(b"") + dyn(b"")
        data = sel("send((uint32,bytes32,uint256,uint256,bytes,bytes,bytes),(uint256,uint256),address)") + word(128) + word(123_456) + word(0) + addr(WALLET) + param
        decoded = h.decode_call(hexs(data))
        self.assertEqual(decoded["function"], "send")
        self.assertEqual(decoded["args"], {"dstEid": 30101, "to": WALLET, "amountLD": 5_000_000, "minAmountLD": 4_990_000,
                                           "nativeFee": 123_456, "lzTokenFee": 0, "refundAddress": WALLET})

    def test_unknown_and_empty_calls(self):
        self.assertEqual(h.decode_call("0x")["function"], "none")
        self.assertEqual(h.decode_call("0xdeadbeef" + "00" * 32)["function"], "unknown")
        self.assertEqual(h.decode_call("0xdeadbeef" + "00" * 32)["selector"], "0xdeadbeef")

    def test_transfer_logs_from_a_fixed_receipt(self):
        pool = "0x2222222222222222222222222222222222222222"
        receipt = {"status": "0x1", "logs": [
            {"address": USDC.lower(), "topics": [h.TRANSFER_TOPIC, h.pad_topic(WALLET), h.pad_topic(pool)], "data": hex(5_000_000), "logIndex": "0x0"},
            {"address": WETH.lower(), "topics": [h.TRANSFER_TOPIC, h.pad_topic(pool), h.pad_topic(ROUTER)], "data": hex(2_000_000_000_000_000), "logIndex": "0x1"},
            {"address": WETH.lower(), "topics": ["0x" + "ab" * 32], "data": "0x", "logIndex": "0x2"},
            {"address": WETH.lower(), "topics": [h.TRANSFER_TOPIC, h.pad_topic(ROUTER), h.pad_topic(FEE)], "data": hex(1_000_000_000_000), "logIndex": "0x3"},
            {"address": WETH.lower(), "topics": [h.TRANSFER_TOPIC, h.pad_topic(ROUTER), h.pad_topic(WALLET)], "data": hex(1_999_000_000_000_000), "logIndex": "0x4"},
        ]}
        transfers = h.transfers_in(receipt)
        self.assertEqual(len(transfers), 4)
        self.assertEqual(transfers[0], {"token": USDC, "from": WALLET, "to": h.checksum_address(pool), "amount": 5_000_000, "log_index": 0})
        self.assertEqual(transfers[2]["to"], FEE)
        self.assertEqual(transfers[2]["amount"], 1_000_000_000_000)
        self.assertEqual(transfers[3]["to"], WALLET)


if __name__ == "__main__":
    unittest.main()
