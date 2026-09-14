# AER Connect Corridor — Acceptance Test Series before Sale

**Amended 14 September 2026: A4, A5, A6 (Spec T2).**

**Version 1.0, 13 September 2026, Melbourne.** Prepared for Albert Dadon. Purpose: to prove, with evidence a customer could read, that the corridor Claude → AER Connect (mcppro.aeredium.io) → MCP Police and MCP Wallet → the access platform → the AERKey policy engine does end to end what the twenty-one restated rules and the three rulings of 13 September say it does, so that the website can be written and the product sold on the strength of the results. Everything below refers to the product as it runs tonight: Wallet through Spec 46, engine library through E4 (template version 6), Police 1.8.0 through Spec 17, connector through Spec 39.

---

## 1. What a pass is, and what counts as evidence

A test passes when the corridor does what the numbered rule says, and says so in the words the Owner's Guide gives. A refusal that is expected is a pass; an allow where a refusal was expected is a failure of the first order and stops the series until it is explained. A test that produces a different sentence from the one written here, but the right outcome, is a pass with a note: the sentence goes into the guide or the code is corrected, and the note says which.

For every test the tester keeps three things: the words said to Claude and Claude's whole answer, copied as text; every transaction hash Claude reports; and the row the account page's record shows for that action. Where a test moves money, the tester also keeps the block explorer's page for each hash. Results are pasted back as text, in the order of the tests, one heading per test id. I read each result against the rule and the code, and the pass or failure is written into a results edition of this document.

Two testers run the series independently, Eitan Katz and Victor Huang, each with one Trader and one Payer, so that every role is exercised by two people and two wallets. Where the two disagree, the corridor is asked a third time by Albert.

## 2. Funds, chains and cost

The bulk of the series runs on Arbitrum, where a transaction costs cents. Base is used for the crossings and for one trade on each exchange. Ethereum is used for exactly three tests in Stage 2, because a mainnet transaction costs dollars.

Each tester's Trader wallet is funded with 30 USDC and 5 USDT on Arbitrum, 8 USDC on Base, and gas: 0.004 ETH on Arbitrum, 0.003 ETH on Base. Each tester's Payer wallet is funded with 10 USDC on Arbitrum and 0.002 ETH on Arbitrum. For Stage 2, one Trader wallet receives 10 USDC and 0.02 ETH on Ethereum. Every trade is for five dollars unless the test says otherwise; every payment is for one dollar. The whole series, both testers, costs under 150 dollars of stablecoin moved between the testers' own wallets and exchanges, plus perhaps 40 dollars of gas, most of it on Ethereum. The five-basis-point fee on trades comes to a few cents in total and lands in the agents' fee address, which Series F reads back.

Before funding, every owner opens Set limits on each agent and saves once (the re-save of 13 September, Guide section 4), sets "ask me first" per transaction at 50 dollars and the period total at 200 dollars so that the five-dollar tests are not held, sets per transaction at 20 dollars, per day at 100, per week at 300, transactions per day at 30, ticks Ethereum, Arbitrum and Base, ticks USDC, USDT and WETH where the form offers it, and writes the destination list of Series B.

## 3. Series A — readiness, no money moves

**A1. The public door.** From any computer: `https://mcppro.aeredium.io/.well-known/oauth-authorization-server` answers 200, `/healthz` answers 200, an unauthenticated POST to `/mcp` answers 401. Proves the door is up and closed to strangers. Evidence: the three status codes.

**A2. Claude connects as one agent.** In Claude, with AER Connect connected as the Trader, ask: *"Which agent are you?"* Claude calls `my_agent` and answers with the agent's name, role Trader, wallet id, address and chain, and the caps written on its policy entry. It names no other agent. Proves the connector acts for exactly one agent (Rule 17, Rule 21). Evidence: the answer.

**A3. The guide is inside the MCP.** Ask Claude: *"Which address do I list for Uniswap on Arbitrum?"* then *"Can my trader send money back to me?"* then *"What is not yet built?"* Each answer comes from `aerconnect_guide`, cites the AER Connect Owner's Guide v1.1 with its section, gives `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` for the first, says plainly that a Trader cannot send and that funds cannot yet leave for the second, and lists the hold page, the return road, Curve as a class, more exchanges, more chains and USDT to Base for the third. Proves Spec 39 and Rule 13. Evidence: the three answers.

**A4. The Wallet names its rails.** Ask Claude: *"What chains can your wallet reach, and what are my balances?"* Claude calls `wallet_status` and `get_balances`. `wallet_status` names the wallet's own chain, which must be one of ethereum, arbitrum and base; it does not yet name all three as rails, so a missing `rails` or `transfer_rails` field is a pass with a note pointing at Spec 49, not a failure. The native balance the Wallet states is compared with the chain's own `eth_getBalance`, whether the Wallet sends it as a JSON number or as a string. The ERC-20 balances are read from the chain's own RPC alone, because `get_balances` cannot yet state them (Spec 49), and the Wallet's own sentence is quoted in a note. Proves Rule 18. Evidence: the answer, compared with the chain's balances.

**A5. The Wallet and Police agree on the pact's hash.** Ask Claude: *"Which policy are you signing under right now?"* MCP Police carries no tool called `can_sign`, so the hash is read from the Wallet: `wallet_status` states it as `pact.policy_hash`. The harness then makes one `check_action` as the agent the run is connected as, with a question that fits its role and its own chain — a Payer asks C1's, a one-dollar `transfer_stable` to the listed address; a Trader asks D2's, a five-dollar `trade` on `uniswap_v3` for WETH with the listed router — and reads `judged.policy_hash` from Police's answer whatever the verdict: allow, deny and hold all carry it. The two hashes are the same string. A5 compares hashes, not verdicts, and fails in Police's own words where the answer carries no `judged` block. The same hash appears in the account page's mandate table for that agent. Proves Rule 4, one pact one hash. Evidence: the two hashes side by side. Cost: one metered `check_action` unit.

**A6. The fee address is configured, and is not advertised.** Albert, on Virginia: the Wallet's environment carries `AGENT_TRADE_FEE_BPS=5` and the fee address. From any computer: `/guide`, `/account` and the tool list carry none of "fee" as a whole word, "0.05%", "five basis points", "5 bps", "sweepTokenWithFee", "fee_recipient" or "feeRecipient"; `/terms` states the trading fee. "basis points" on its own is not counted: MCP Police's `check_action` schema uses the phrase for `slippage_bps` and `price_deviation_bps`, and neither is the fee. Proves the ruling of 13 September on the fee. Evidence: grep counts (guide 0, account 0, tool list 0, terms at least 1).

**A7. The oracle is fresh.** Albert, on Virginia: a dry quote on Arbitrum reports the Chainlink ETH/USD, USDC/USD and USDT/USD reads with timestamps inside each feed's heartbeat window. Proves the price-deviation and oracle facts can be established (Rule 12). Evidence: the log lines.

**A8. Halting is final, on a spare agent.** Each owner creates a throwaway Payer, halts it, and asks Claude connected as that agent to do anything. Both doors refuse on the next call; the account page shows it halted; there is no un-halt control. Proves Rule 20. Evidence: the refusal and the page.

## 4. Series B — the owner's road: the form and the list

**B1. A compulsory question left blank is refused before anything is sent.** Open Set limits, clear "a list for this agent only / one list for all my agents", press Save. The page says *"Say whether this list is for this agent only or for all your agents. Nothing was sent."* and the mandate table is unchanged. Proves Rule 2. Evidence: the sentence and the unchanged hash.

**B2. A wrong address is refused naming the line.** Add a line `0x1234` to the destination list and save. The platform refuses the whole save and names the line. Proves Rule 5, Rule 13. Evidence: the sentence.

**B3. The Trader's list.** For the Trader, write exactly these lines and save: Uniswap SwapRouter02 on Ethereum and Arbitrum `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`, Uniswap on Base `0x2626664c2603336E57B271c5C0b26F421741e481`, PancakeSwap SmartRouter on Ethereum `0x13f4EA83D0bd40E75C8222255bc855a974568Dd4`, on Arbitrum `0x32226588378236Fd0c7c4053999F88aC0e5cAc77`, on Base `0x678Aa4bF4E210cf2166753e054d5b7c31cc7fa86`, Circle CCTP TokenMessengerV2 `0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d`, Tether USDT0 on Ethereum `0x6C96dE32CEa08842dcc4058c14d3aaAD7Fa41dee` and on Arbitrum `0x14E4A1B13bf7F943c8ff7C51fb60FA964A298D92`. Choose "a list for this agent only". The save succeeds, the hash moves, and within a minute Claude's `can_sign` prints the new hash. Proves Rule 9 (the mirror refreshes) and Rule 4. Evidence: old hash, new hash, the minute.

**B4. The Payer's list.** For the Payer, write one line: the owner's own wallet address (Victor's listed destination `0xfec697fc2D4323aE7618BFF2347C01E29653FB57`, and Eitan's equivalent). Choose "one list for all my agents" for one tester and "a list for this agent only" for the other, so both answers are exercised. Proves Rule 5. Evidence: the mandate table reading the list back (Rule 21).

**B5. The template is a floor the owner narrows.** On the Payer's form, try to permit the action *trade*; on the Trader's, try to permit *transfer*. The form offers no such control, or refuses it. Proves Rule 3. Evidence: what the form shows.

**B6. The page reads the document back.** After B3 and B4, read the mandate table aloud with the screen reader: chains, assets, each limit, ask me first, period total, count, and the list. Where a figure was left blank the page says *the document states none*. Proves Rule 21. Evidence: the table as read.

**B7. Two agents, two lists.** With the shared list of B4 in force for the tester who chose "one list for all my agents", create a second Payer and confirm its mandate table shows the same list without writing it again. Proves the shared-list answer. Evidence: the second table.

**B8. The list is amended by saving again.** Remove one exchange line from the Trader's list, save, and see D6 below refuse the trade on that exchange; put the line back, save, and see it pass. Proves Rule 9. Evidence: the two hashes and the two outcomes.

## 5. Series C — the Payer

**C1. A payment to a listed address passes.** Say to Claude as the Payer: *"Pay 1 USDC on Arbitrum to <the listed address>."* Claude calls `check_action` (allow, receipt), `build_transaction` (ticket, dry-run passed), `submit_transaction` (hash). The explorer shows 1 USDC arriving. Proves Rules 5, 6, 10, 11, 14. Evidence: the receipt, the ticket, the hash, the record row.

**C2. A payment to an unlisted address is refused at pre-flight.** *"Pay 1 USDC on Arbitrum to 0x000000000000000000000000000000000000dEaD."* Police answers deny with the destination sentence; Claude does not build. Proves Rule 5, Rule 11. Evidence: the refusal.

**C3. The receipt is required to build.** Albert, from a shell with the agent's credential: call the Wallet's `build_transaction` for C1's payment without a Police receipt. The Wallet refuses in its own words. Proves Rule 11 (the order is enforced by the Wallet). Evidence: the refusal.

**C4. Above per transaction is refused.** *"Pay 25 USDC on Arbitrum to <listed>."* (per transaction is 20). Refused, naming the limit. Proves Rule 6. Evidence: the refusal.

**C5. Ask me first holds.** Set "ask me first" to 2 dollars on the Payer, save, then *"Pay 3 USDC on Arbitrum to <listed>."* The answer is a hold: *"owner approval required before ticket can be minted"*, and nothing is signed. Set it back to 50 and save. Proves Rule 7 and the guide's warning that a hold cannot yet be answered. Evidence: the hold sentence, the record row marked held.

**C6. A chain not ticked is refused.** Untick Base on the Payer, save, then *"Pay 1 USDC on Base to <listed>."* Refused, naming the chain. Re-tick and save. Proves Rule 16. Evidence: the refusal.

**C7. An asset the role does not move is refused in the Wallet's words.** *"Pay 1 WETH on Arbitrum to <listed>."* The Wallet answers that WETH is not a stablecoin this door transfers on arbitrum and names the ones it does. Proves Rule 13. Evidence: the sentence.

**C8. No gas is a named refusal.** On a Payer with USDC but no ETH on Arbitrum (drain the ETH first, or use a third throwaway Payer funded that way): *"Pay 1 USDC on Arbitrum to <listed>."* The Wallet says the signing address has so many wei native balance and needs at least so many for gas. Proves Rule 15, Rule 13. Evidence: the sentence.

## 6. Series D — the Trader

**D1. A Trader cannot send, not even to its owner.** As the Trader: *"Pay 1 USDC on Arbitrum to <the owner's address>."* Refused: the role permits trade and nothing else. Proves Rule 8 as amended. Evidence: the refusal, from Police or the Wallet, quoted.

**D2. The first Uniswap trade: approval then swap, two hashes, exact allowance.** *"Trade 5 dollars of USDC for WETH on Arbitrum on Uniswap v3."* Claude sends venue `uniswap_v3`, `to_asset WETH`. The ticket carries two legs; `submit_transaction` returns two hashes. On the explorer: the first transaction is `approve(SwapRouter02, exactly the USDC amount of the trade)`, the second is the swap, WETH arrives in the agent's wallet, and a WETH transfer of five basis points of the output goes to the fee address in the same swap transaction. Proves Rule 8 amended (the one approval, exactly the amount), Spec 44, and the fee ruling. Evidence: both hashes, the approval's amount, the fee transfer.

**D3. The second Uniswap trade has one leg.** Repeat D2. Because the allowance was exact and is spent, a fresh approval is needed again: the ticket again carries two legs. Then trade *"5 dollars of USDC for WETH on Arbitrum on Uniswap v3"* a third time and confirm the same. Proves that an approval is never unlimited: every trade needs its own. Evidence: the leg counts. Note: if the Wallet ever reports one leg on a fresh trade, an allowance was left standing, and that is a failure.

**D4. The approval counts as two transactions.** After D2 and D3, ask Claude for `my_usage`; the count for the day has risen by two per trade with an approval. Proves the amendment's second sentence. Evidence: the count before and after.

**D5. PancakeSwap on Arbitrum.** *"Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3."* Same shape as D2, venue `pancakeswap_v3`, contract `0x32226588378236Fd0c7c4053999F88aC0e5cAc77`, fee peeled to the fee address. Proves Spec 45 part A. Evidence: hashes, fee transfer.

**D6. A venue whose contract is not listed is refused by Police, naming it.** With B8's line removed: *"Trade 5 dollars of USDC for WETH on Arbitrum on PancakeSwap v3."* Police says the venue contract is not on this agent's list. Proves Police Spec 16 and Rule 5 applied to trades. Evidence: the sentence.

**D7. Curve, refused first, then listed, then traded.** *"Trade 5 dollars of USDC for USDT on Arbitrum on Curve."* First outcome: a refusal naming the pool's address (or, if no pool holds both, the Wallet's sentence *"curve on arbitrum has no pool holding both USDC and USDT that this door could quote"*, which is also a pass with a note). Add the pool address to the list, save, repeat: the trade passes, USDT arrives, no fee is taken (Curve cannot peel one) and the record says so. Proves Spec 45 part B and the Guide's Curve caveat. Evidence: the refusal, the pool, the hash.

**D8. Best price, with every candidate recorded.** *"Trade 5 dollars of USDC for USDT on Arbitrum at the best price."* Claude sends venue `best_direct` with an empty `contract_address`. The answer names the exchange chosen; the record row shows every exchange's quote, the one chosen and `route_chosen_by`. Proves Spec 45 part C and the chooser ordering. Evidence: the answer, the record row with all candidates.

**D9. Best price with one candidate unlisted is refused by Police, naming it.** Remove the Uniswap Arbitrum line, save, repeat D8. Police: *"best_direct may choose uniswap_v3, whose contract 0x68b3… on arbitrum is not on this agent's list; list it, or remove uniswap_v3…"*. Put the line back and save. Proves Spec 16's chooser clause. Evidence: the sentence.

**D10. A trade that names nothing to buy is refused.** *"Trade 5 dollars of USDC on Arbitrum on Uniswap v3."* The Wallet: *"a trade must name the asset it buys in to_asset…"*. Proves Rule 12, Rule 13. Evidence: the sentence.

**D11. An exchange named but not wired is refused in words.** *"Trade 5 dollars of USDC for WETH on Arbitrum on Aerodrome."* The Wallet: *"this door trades directly on uniswap_v3, pancakeswap_v3, curve, best_direct; aerodrome is not yet wired to it."* Proves Rule 13. Evidence: the sentence.

**D12. Selling a non-stablecoin is refused.** *"Trade 5 dollars of WETH for USDC on Arbitrum on Uniswap v3."* Refused: `asset` must be a stablecoin. Proves the Wallet's stated limit. Evidence: the sentence.

**D13. The hold at the Trader's default.** Clear "ask me first" on the Trader (leave it blank), save, and *"Trade 12 dollars of USDC for WETH on Arbitrum on Uniswap v3."* Held: *"owner approval required before ticket can be minted"* (the template's ten dollars applies). Set it back to 50 and save. Proves Rule 3 (the template's figure applies when the document states none) and Rule 7. Evidence: the hold.

**D14. The old Uniswap router is not a road.** Add `0xE592427A0AEce92De3Edee1F18E0157C05861564` to the list, save, and ask for a Uniswap trade with `contract_address` set to it. Refused: the Wallet does not use it. Remove the line. Proves the guide's warning. Evidence: the sentence.

**D15. Uniswap and PancakeSwap on Base.** Repeat D2 and D5 on Base with the Base contracts. Proves the per-chain address tables. Evidence: hashes and fee transfers on Base.

**D16. The agent never sees the transaction bytes.** Read Claude's answers from D2 to D15: no `quote_tx_json`, no calldata, no signed bytes appear. The ticket the agent sees names facts, hashes and legs. Proves the agent-facing ticket rule. Evidence: the transcripts.

## 7. Series E — the crossings

**E1. USDC Arbitrum to Base by Circle's road.** *"Move 5 USDC from Arbitrum to Base."* Claude sends `bridge_stable`, `to_chain base`. Police allows (the CCTP contract is listed, Spec 17); the ticket carries the approval and the burn; `submit_transaction` returns the hashes; within minutes the Wallet completes the arrival with `receiveMessage` on Base and reports that hash; 5 USDC appears on Base. The record names the venue `cctp` and *"through the issuer's own road"*, and *"a crossing carries no service fee"*. Proves Rule 23 and Spec 46. Evidence: burn hash, receive hash, the two balances.

**E2. A slow attestation is not a loss.** If E1's attestation outlives the ticket, the answer says *"awaiting attestation"* with the burn hash; ask Claude *"Complete my crossing"* and `get_crossing` finishes it. If E1 completed at once, Albert forces the case on Virginia by shortening `AGENT_BRIDGE_ATTESTATION_TIMEOUT_SECONDS` for one run. Proves the awaiting-attestation road. Evidence: the two answers.

**E3. USDT Arbitrum to Ethereum by Tether's road.** Stage 2. *"Move 5 USDT from Arbitrum to Ethereum."* Venue `usdt0`; one send transaction on Arbitrum paying LayerZero's fee in ETH; USDT arrives on Ethereum automatically; the Wallet confirms by the destination balance rising. Proves Rule 23 for USDT. Evidence: the send hash, the Ethereum balance.

**E4. USDT to Base is refused in words.** *"Move 5 USDT from Arbitrum to Base."* The Wallet: this road does not serve these two chains (Tether does not publish its road on Base). Proves Rule 13 and the guide's note. Evidence: the sentence.

**E5. A crossing goes to the agent's own address only.** Ask *"Move 5 USDC from Arbitrum to Base and deliver it to <the owner's address>."* The crossing either ignores the address and delivers to the agent's own wallet on Base, or refuses; it never delivers to the named address. Proves Rule 23's "to its own address only" and Spec 17's recipient check. Evidence: the destination of the minted USDC.

**E6. A bridge contract not listed is refused by Police.** Remove the CCTP line, save, repeat E1: Police says the destination is not on the list, naming the contract. Put the line back. Proves Spec 17. Evidence: the sentence.

## 8. Series F — the record, the accounts and the words

**F1. Every action is in the record.** On the account page, read the record for each agent: every test above, allowed, refused or held, is a row with action, amount, chain, venue, hashes per leg, and for D8 every candidate. Proves Rule 21 and the audit half of the fee ruling. Evidence: the rows, counted against the tests.

**F2. The fee is accounted.** On the explorer, read the fee address `0xabd0235C036CBeCb911DC74958B3c8F114cec42a` on Arbitrum and Base: its incoming transfers are exactly the fee legs of D2, D3, D5 and D15, each five basis points of that trade's output, and nothing else. The record rows show the same amounts. Proves the fee lands where the accounts expect and only there. Evidence: the explorer's transfer list against the rows.

**F3. Refusal sentences match the guide.** Compare every refusal collected in C, D and E with Guide section 10. Each is either there verbatim or is noted for the guide's version 1.2. Proves Rule 13 and the guide's promise. Evidence: the list of matches and the list of new sentences.

**F4. One hash everywhere.** For one allowed trade (D2), the policy hash in Police's receipt, in the Wallet's ticket, in the engine's verdict (Albert reads it on P0) and on the account page are the same string. Proves Rule 4. Evidence: the four hashes.

**F5. The engine judged the bytes.** Albert, on P0: the engine's log for D2 shows the approval judged as destination = SwapRouter02, amount = the allowance, and the swap judged with the venue contract as destination; for C1, the amount read from the transfer's calldata, not from the request. Proves Rule 14 and E2's parser. Evidence: the log lines.

**F6. Nothing on the public pages is untrue.** Read `/guide`, `/terms`, `/privacy` and the account page aloud: every sentence describes what the tests just showed, and the not-yet-built list matches Guide section 12. Proves Rule 13 for the website that will be written from them. Evidence: any sentence that is not true, listed.

## 9. Series G — when a part fails, the corridor fails closed

These are run by Albert on the boxes, with one tester ready in Claude, and each part is restored at once.

**G1. Police down.** Stop mcp-police on P0 for two minutes; the tester asks for C1's payment. Claude reports Police unreachable and builds nothing; the Wallet refuses a build without a receipt. Restart. Proves Rule 11. Evidence: the refusal.

**G2. A rail removed.** Remove Base from `AGENT_CHAIN_RPC_URLS` on Virginia and restart the Wallet; the tester asks for a payment on Base. The Wallet: *"no rail is configured for base on this door… so this…"*, and `wallet_status` no longer names Base. Restore. Proves Rule 18. Evidence: the sentence.

**G3. The engine's mirror lags.** Change a limit on the form and, within the same minute, ask for an action that the old document allows and the new one refuses. Either the new document is already in force (refused) or the old is (allowed, and the record shows the old hash). Both are the corridor telling the truth; what fails is a refusal with neither hash. Proves Rule 9's "within a minute". Evidence: the hashes on the row.

**G4. A stale oracle.** Set `AGENT_ORACLE_MAX_AGE_SECONDS` to 1 on Virginia and restart; ask for D2. The Wallet refuses because the oracle fact cannot be established, and says so; nothing is signed. Restore. Proves Rule 12. Evidence: the sentence.

## 10. Series H — over a day and a week

**H1. The daily count resets.** After Series D, note `my_usage`; the next day, the count is zero and the day's ceiling is whole again. Proves the day boundary. Evidence: the two readings.

**H2. The per-day ceiling.** Set per day to 12 dollars on the Trader, run three five-dollar trades; the third is refused, naming the daily figure. Set it back. Proves Rule 6. Evidence: the refusal.

**H3. The period total holds.** Set the period total to 12 dollars, run three five-dollar payments on the Payer; the third is held, not refused. Set it back. Proves Rule 7's second line. Evidence: the hold.

**H4. Two owners do not see each other.** Eitan's account page shows no agent of Victor's, and Claude connected as Eitan's Trader cannot name Victor's wallet. Proves Rule 17. Evidence: both pages.

## 11. Exit criteria for selling

The product may be put on the website when: every test in Series A to F passes for both testers, or passes with a note that has been carried into the guide's version 1.2 or a shipped fix; Series G passes as run by Albert; H2 and H3 pass, with H1 and H4 read once. The website's every sentence about the product is taken from the Owner's Guide, and the not-yet-built list of Guide section 12 appears on the site in plain words: no page to answer a hold, no road to return an agent's funds, Curve by pool address, three exchanges, three chains, USDT not to or from Base. A customer who reads the site and then reads a refusal must find the same words in both. That is Rule 13, and it is the thing a sold product is judged on.

## 12. Order and timing

Day one, evening: Series A and B (no money), then C on Arbitrum. Day two: Series D on Arbitrum and Base, E1, E2, E4, E5, E6, and F. Day three: Stage 2 on Ethereum (E3, one Uniswap trade on Ethereum, F2 on Ethereum), Series G with Albert, and H2 to H4. H1 is read on day two's morning. Results are pasted after each series, not at the end, so that a failure stops the series before money is spent past it.

---

*Prepared from the restated Rules of 12 September 2026, the rulings of 13 September (Rule 8 amended, the fee, Rule 23), the Owner's Guide version 1.1, and the code shipped through Wallet PR 39, engine PR 36, Police PR 14 and connector PR 30.*
