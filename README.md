# The Corridor Harness

A Python script that runs the AER Connect Corridor Acceptance Test Series as the agent, and reports precisely what happened. Spec T1, 13 September 2026, as amended by Spec T2, 14 September 2026.

**This repository is the harness's home.** The copy under `aer-connector` `tools/harness` is retired. Changes arrive here by pull request, never by a commit straight to `main`.

Two laws (Spec T1 §1). **The harness is the agent, not a judge.** It speaks to the corridor exactly as Claude does: MCP over HTTPS at `https://mcppro.aeredium.io/mcp`, under an agent's own OAuth consent, saying the words the Owner's Guide gives. It holds no key, no rail and no rule of its own. **A failure is evidence, not a verdict.** When a test does not come out as the Series expects, the report carries what was sent, what came back word for word, who answered, and where the truth can be read. The harness never paraphrases an answer and never guesses at a cause.

## What it needs

The Mac's own `python3`, which is Python 3.9.6, and nothing else: the standard library only (`urllib.request`, `json`, `hashlib`, `secrets`, `http.server`). There is no `requests`, no `requirements.txt` and nothing to install (Spec T1 §2 and §10 as amended by Bear on 13 September 2026). It also runs unchanged on Python 3.12.

## The files

- `corridor_harness.py` — the harness: the OAuth road, the MCP session, the chain reader and decoders, the sentence matcher, the classifier, the runner and the report.
- `series.py` — every test of the Series as data: id, rule, the Series' own text, the words said to Claude, the action, the expected kind, the expected sentence, the pause text. The Owner's Guide §10 table is transcribed here.
- `tables.py` — every address the harness may ever send, pinned verbatim with the page each was read from.
- `tests/` — the unit tests; `tests/fixtures/series-1.0.md` is the Series document, amended on 14 September 2026 for A4, A5 and A6 and otherwise byte for byte, so the tests can prove the ids against it without reaching into anybody's Downloads folder. The amendment is the only difference, and a test proves that every other paragraph is still the document's own.

## Running it

```
python3 corridor_harness.py --tester eitan --series A B C
```

- `--series` takes any of `A B C D E F H`, default all. Series G is Albert's on the boxes and is printed in the report for a person.
- `--from D7` resumes at a test id. Series A still runs first, because nothing that moves money is sent until Series A has passed in the same run.
- `--dry` prints every call the harness would make, without connecting and without a token.
- `--consent trader` (or `payer`, `payer_nogas`) runs only the consent for one agent, then calls `initialize`, `tools/list` and `aerconnect_my_agent`, and prints the agent it connected as, its pact and policy hash from `wallet_status`, and a note if the agent's role is not the one this label is for or its wallet is on a chain the product does not offer.
- `--stage2` includes E3, the Stage 2 crossing on Ethereum. Without it E3 is reported as skipped.
- `--run-file`, `--issuer`, `--out`, `--crossing-wait` override the defaults below.

The harness prints one line per test as it goes, plainly enough for a screen reader, for example:

```
D2 — pass — Uniswap v3 on Arbitrum — approval 0x…, multicall(deadline) 0x…, fee 0.000000993827160506 WETH to 0xabd0…, 0.0019 WETH arrived
```

and prints the report path at the end.

## The run file

`~/.corridor-harness/harness_run.json`, written on first use for the owner to complete. It carries no secrets: for each tester, the agent labels (`trader`, `payer`, and optionally `payer_nogas` for C8), the owner's listed address, and the list scope chosen at B4; and for each chain, a public RPC endpoint the harness may read from and the token contracts whose balances it reads for the report. Those token addresses are read targets, never destinations. Both testers may be in one file; the harness runs one tester at a time.

## The consent

The harness registers itself once at `/register` as a public client with a loopback redirect (`http://127.0.0.1:8765/callback`; the connector matches a loopback redirect on any port, RFC 8252 §7.3) and keeps the client id in `~/.corridor-harness/client.json`. For each agent it runs the authorization-code flow with PKCE S256 and prints the consent link as one line, exactly in this form:

```
Consent link for eitan-trader: https://mcppro.aeredium.io/authorize?response_type=code&client_id=mcp-…&redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Fcallback&code_challenge=…&code_challenge_method=S256&state=…&scope=aeredium%3Aact&resource=https%3A%2F%2Fmcppro.aeredium.io%2Fmcp
```

**If the consent page opens with "You are already connected", press "Connect a different agent" to choose the agent you are consenting now.** The page offers Finish first, which consents the agent already connected: Eitan's first run went as the wrong agent for this reason, and A2 says so when it happens.

The owner opens it, chooses the agent on the consent page, consents with his passkey and presses Finish; the browser returns the code to the loopback listener; the harness exchanges it at `/token` and stores the access and refresh tokens in `~/.corridor-harness/<tester>-<label>.json`, mode 600. It refreshes when the door tells it to. It never asks for, prints or stores a passkey, a password or a private key, and never reads the agent's credential; the connector holds that.

## What it runs, what it pauses for, what it leaves to a person

Runs by itself: A1 A2 A3 A4 A5 A6, C1 C2 C3 C4 C7 C8, D1 D2 D3 D4 D5 D7 D8 D10 D11 D12 D15 D16, E1 E2 E3 E4 E5, F2 F3 F4.

Pauses for the owner's passkey, says in one sentence exactly what to do, waits for Enter, then reads `wallet.wallet_status` until `pact.policy_hash` has moved (ninety seconds, then asks whether to wait or skip; a skip is reported as skipped, never as passed): B1 B2 B3 B4 B5 B8, C5 C6, D6 D9 D13 D14, E6, H2 H3, and every restore afterwards. D7 also pauses once, for the owner to add the pool address the first refusal named.

Left to a person, with the Series' text printed in the report and a line for the outcome: A7 A8, B6 B7, F1 F5 F6, G1 G2 G3 G4, H1 H4.

Three notes on the data. C3 is made through the relay as the agent, not from a shell with the credential, because the harness never holds the credential; the Wallet's refusal is the same. C8 needs a Payer funded with USDC and no ETH, named as `payer_nogas` in the run file; without one it is skipped. E2 runs only if E1 said "awaiting attestation"; if E1 completed at once, the forced case is Albert's and the report says so.

## What gates money, and what Series A costs

Nothing that moves money is sent until **A1, A2, A3, A5 and A4's native-balance check** have passed in the same run (Spec T2 §5). **A6 and A4's notes gate nothing**: they prove wording and the Wallet's own reach under Spec 49, not the corridor's judgement. The report says which of them passed, in one line under the summary, and a money test skipped by the gate names the test that held it back. Where the native-balance check could not be made at all — the run file names no RPC for the agent's chain, or the chain did not answer — that holds nothing back, and the report says it was not made rather than that it passed.

**The fee pin.** A6 counts `fee` as a whole word, so `coffee` is not the fee. Every other pinned term is counted as it is written, wherever it sits, so `sweepTokenWithFeeAndUnwrap` and `feeRecipientAddress` are both caught. A term that opens with a digit may not begin inside a longer figure, so the fee's `5 bps` is not the `15 bps` of a slippage cap. "basis points" on its own is not counted at all: MCP Police's `check_action` schema uses the phrase for `slippage_bps` and `price_deviation_bps`, and neither is the fee.

**The chain guard.** An agent whose `wallet_status.chain` is not ethereum, arbitrum or base runs no money series at all, and the report says, for that agent: *"<label>'s wallet is on <chain>, which the product does not offer; the series runs on ethereum, arbitrum and base. Create the agent again on one of those and consent it."* The money series are C, D, E and H, whole — D4, D16 and E2 read back what the money tests did, so they are refused with the rest — and B8, which walks the corridor. Series A still runs and reports for that agent, because Series A moves nothing, and so do the owner's-road tests of Series B, which stand whatever chain the wallet is on. `--consent` says the same sentence the moment a consent lands, so a wallet on the wrong chain is found before a run is started.

**Cost.** Series A moves no money, but A5 spends **one metered `check_action` unit**: it asks MCP Police one question, the one its own role can ask, and reads the hash Police judged under. Nothing is built and nothing is submitted.

## Outcomes

- **pass** — the right kind of outcome, in the Guide's words.
- **pass with a note** — the right kind, in different words; both sentences are quoted, and F3 collects every note at the end of the report.
- **fail** — the wrong kind, a leg count or fee that does not match, a revert, or no judgment at all (a dead bearer, a door that did not answer, a relay refusal); followed by its evidence block.
- **held** — the corridor held an action the Series expected to pass; the hold's sentence is quoted. A hold the Series expected (C5, D13, H3) is a pass.
- **skipped** — the person chose to skip, or a precondition was missing; never counted as a pass.
- **left to a person** — the Series' text and a blank line.
- **not run** — the series stopped earlier on an unexpected allow.

## The three files of a run

`~/Downloads/harness-runs/<date-time>-<tester>/`:

- `report.md` — one heading per test in Series order, the rule, the outcome and one plain sentence; a summary at the top (counts, the policy hash at the start and the end, wallet addresses and balances before and after, the total moved, the fee legs found on chain, every transaction hash); every failure's evidence block in the order Spec T1 §6 gives, ending with a where-to-read line that names the part and the rule and never a cause.
- `evidence.jsonl` — one line per call: time to the millisecond, test id, tool, the arguments exactly as sent, the answer exactly as received, the HTTP status and the round trip, with the bearer token and every receipt or ticket secret replaced by `<redacted>`.
- `chain.jsonl` — one line per transaction hash: chain, hash, block, status, `to`, the decoded call where the harness knows the selector (`approve`, `transfer`, `exactInputSingle` inside `multicall` with `sweepTokenWithFee`, `depositForBurn`, `receiveMessage`, `send`, and Curve's `exchange`), the Transfer events with from, to and amount, and the gas used.

## Safety

Nothing that moves money is sent until Series A has passed in the same run, which means A1, A2, A3, A5 and A4's native-balance check (Spec T2 §5). An agent whose wallet is on a chain the product does not offer runs no money series at all. A destination, venue contract or fee address comes from two places only: the owner's listed address in the run file, and the pinned tables, verbatim with their page. No amount is sent above the Series' own figure for that test. A refused action is never retried. `submit_transaction` is never called except with the ticket this run's `build_transaction` issued. On the first unexpected allow, an action the Series expected to be refused or held that was built or signed, the whole series stops, the report says which, and nothing further is sent until a person restarts the harness. A hold, a refusal or a chain revert never stops the run.

## Read from the code, not from memory

The tool names are the relay's: `police.<name>` and `wallet.<name>`, and the connector's own `aerconnect_my_agent` and `aerconnect_guide` (`apps/server/src/services/mcprelay.ts`). The Police tools that propose or track an assignment, `request_assignment`, `police_assignment_status` and `assignment_status`, are marked "NOT THE ROAD FOR AN AER CONNECT AGENT" (`packages/shared/src/knowledge.ts`, `ROADS`) and the harness never calls them. **MCP Police carries no tool called `can_sign`.** It said so itself: *"MCP Police carries no tool called “can_sign”. Ask for the tool list again: this server relays whatever the doors carry and never a copy of its own."* Its tools are `list_roles`, `describe_role`, `check_action`, `request_assignment`, `assignment_status` and `my_usage`. So **every policy hash is read from the Wallet** (Spec T2 §1): `wallet.wallet_status` states it as `pact.policy_hash`, with `pact.id`, `pact.state` and `pact.policy_generation` beside it, and `wallet.get_balances`' `pact_budget.policy_hash` is the second source where `wallet_status` states none. A5 compares that hash with `judged.policy_hash` from one `police.check_action`, which allow, deny and hold all carry: A5 compares hashes, not verdicts. The arguments of a call are the Guide's own vocabulary (`action`, `chain`, `asset`, `amount_usd`, `to_address`, `to_asset`, `venue`, `contract_address`, `to_chain`) shaped to the door's own `inputSchema` read from `tools/list`: only the fields the door declares are sent, under the names it declares (the suite's door double spells Police's as `action_kind`, `asset_symbol`, `amount_usd_cents` and `child_wallet_id`), and a field the schema does not declare is named in the evidence rather than guessed. A dry run, with no schema to read, prints the Guide's names.

## The tests of the harness itself

```
python3 -m unittest discover tests
```

They run without a network and prove: the sentence matcher treats the Guide's ellipses and angle brackets as wildcards and matches every §10 sentence against a realistic answer, and none against a sentence of another kind; the redaction removes a bearer and a receipt secret and leaves everything else byte for byte; the classifier maps a Police deny, a Police `manual_approval_required`, a Wallet error body and a successful submit to the five kinds, and a dead bearer or a relay refusal to no judgment at all; the chain decoder decodes `approve`, `transfer`, `exactInputSingle` inside `multicall` with `sweepTokenWithFee`, `depositForBurn`, `receiveMessage` and `send` from fixed calldata and reads Transfer logs from a fixed receipt; the fee check finds the five-basis-point leg and fails when it is one unit off in either direction; `--dry` produces every call for Series A to E in order; the unexpected-allow guard stops the run before anything is signed; every id in `series.py` is in the Series document, every id in the document is in exactly one of the three lists, and every test's text is the document's own paragraph; the hash reader returns the pact's hash from a recorded `wallet_status` answer and sees it move between two; the A6 pin counts nothing on a `tools/list` that says "slippage, in basis points" twice and one on a page that says "0.05%" or "sweepTokenWithFee"; a native balance the Wallet sends as a JSON number is read and printed as the number it is; and an agent on `aeredium-testnet` is refused every money series in the guard's own sentence while Series A still runs.
