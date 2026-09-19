/**
 * THE FROZEN CATALOG VERSION 11 — evidence, not a second source of truth.
 *
 * The seventh of the twins, generated the same way as `questioncatalog.v5.ts`
 * through `.v10.ts` and serving the same law: a shipped question's wording NEVER
 * changes, and neither does the SET of questions a shipped version asked.
 *
 * Version 12 (spec 73) retires C16 and C16C — "how long may a held payment wait
 * before it is refused automatically?" and the custom length behind it. The
 * founder's decision five of 30 August 2026 ended the thing they asked about:
 * "The payment will be held until the answer is provided. Only the answer can end
 * the block that payment held. And of course, the client is free to cancel the
 * payment." A held request no longer expires on any layer, so the pair asked a
 * client to choose a length of time that decides nothing and promised an
 * automatic refusal that no longer exists. So this file is the record of exactly
 * what version 11 asked, question by question, before that pair was retired.
 *
 * ─── WHAT THE LAW TEST DOES WITH THIS FILE ───────────────────────────────────
 *
 *   THE ADD-ONLY CHAIN IS HELD FROZEN-TO-FROZEN. v5 ⊆ v6 ⊆ v7, byte for byte,
 *   and v8 ⊆ v9 ⊆ v10 by id, without reference to the live catalog at all. Those
 *   versions still exist in the answer store and interviews still replay against
 *   them.
 *
 *   EACH LATER VERSION IS HELD AGAINST THE ONE BEFORE IT THROUGH NAMED LISTS.
 *   v7 → v8 is spec 57's amendment list; v8 → v9 is spec 60's; v9 → v10 is spec
 *   65's, which is an ADDITION list and an EMPTY amendment list; v10 → v11 is
 *   spec 67's RETIREMENT list beside its amendment list; v11 → v12 is spec 73's
 *   RETIREMENT list beside an EMPTY amendment list. A question on neither list
 *   must match THIS FILE byte for byte — so version 12 retired exactly the pair
 *   the founder's decision named and not one question more, and moved not one
 *   comma of anything else.
 *
 * AND NO INTERVIEW ALREADY ASKED IS TOUCHED (§5d). Retirement is PROSPECTIVE:
 * `seedCatalog` writes rows keyed by version and never rewrites one, so an
 * interview begun under v11 goes on reading the v11 rows this file records, keeps
 * the prompt-as-asked it recorded, still reads back its history in full — C16's
 * chosen length included — and still compiles. A retired question is a question
 * this estate stops ASKING; it is never a rewrite of what a client already said.
 *
 * Superseded versions survive; they are never overwritten. When a version 13
 * arrives, this file stays exactly as it is and a v12 twin joins it.
 *
 * Generated FROM the v11 catalog. Never edited by hand.
 */

/** One shipped question, reduced to the four things the law protects. */
export interface FrozenQuestion {
  questionId: string;
  part: string;
  kind: string;
  prompt: string;
}

/** The Policy Interview as version 11 shipped it. */
export const CATALOG_V11_POLICY: readonly FrozenQuestion[] = [
  {
    questionId: "A1",
    part: "Part A — The census",
    kind: "text",
    prompt: "What is the company’s legal name?",
  },
  {
    questionId: "A4",
    part: "Part A — The census",
    kind: "text",
    prompt: "What country is the company in?",
  },
  {
    questionId: "A5",
    part: "Part A — The census",
    kind: "currency",
    prompt: "What currency do you want your numbers displayed in?",
  },
  {
    questionId: "A8",
    part: "Part A — The census",
    kind: "list",
    prompt: "Name them. For each person: full name, work email, and what they PRIMARILY do — many people do several of these, so choose the one that is mostly theirs.",
  },
  {
    questionId: "A9",
    part: "Part A — The census",
    kind: "single_choice",
    prompt: "Will anyone stand at a level beneath you on the AER 360 system — your custody clients, partial custodians who hold alongside you, or divisions of this company that carry their own limits? Every level here is a STANDING inside this one company: one bill, one charter, one company.",
  },
  {
    questionId: "A11",
    part: "Part A — The census",
    kind: "single_choice",
    prompt: "Does the company use AI agents or automated systems anywhere near payments — paying, trading, purchasing, moving digital assets?",
  },
  {
    questionId: "B1",
    part: "Part B — Standing",
    kind: "statement",
    prompt: "You are founding this estate. You are level 1. Your answers here set who decides — who approves, who may change the rules, who sees what, and the networks this company uses. What this company can MOVE is set on the wallet accounts that pay, and your estate’s capacity is their total, added up and never asked. A level is a STANDING within this one company — your custody clients, your partial custodians, your divisions. Level 1 controls all levels; each level controls only the levels beneath it; no level controls above itself.",
  },
  {
    questionId: "B2",
    part: "Part B — Standing",
    kind: "statement",
    prompt: "What stands beside you cannot see you, and you cannot see it. Each standing lives in its own branch of the tree: visible in full to the levels above, invisible to others.",
  },
  {
    questionId: "B3",
    part: "Part B — Standing",
    kind: "statement",
    prompt: "You see every level of this estate, always — that is what being level 1 is, and nothing on the next page can change it. Below you, sight is GRANTED and never assumed: a level sees only its own level unless you say otherwise. Nothing sees above itself, and nothing sees beside itself, ever — that is not yours to grant or ours to offer.",
  },
  {
    questionId: "B4",
    part: "Part B — Standing",
    kind: "multi_choice",
    prompt: "AER 360 carries four levels in all: you at level 1, and three beneath you — the deepest being the agents and their wallets. Which levels beneath you may see the level beneath THEM? Tick each grant you are making. You are not on this list: you see everything already. Anything you leave unticked stays unseen — a level that is not granted sight of the level below it cannot see it, cannot list it, and is not told it is there.",
  },
  {
    questionId: "C9S",
    part: "Part C — The company’s rules",
    kind: "statement",
    prompt: "The Aeredium network is enabled by default. It is the native network for the wallets and for the entire ecosystem of AER 360, and it cannot be switched off — every client operates on Aeredium; opting out of it is opting out of being a client.",
  },
  {
    questionId: "C9",
    part: "Part C — The company’s rules",
    kind: "multi_choice",
    prompt: "Which OTHER networks may this company use, in addition to Aeredium? Choosing none is allowed, and means Aeredium only.",
  },
  {
    questionId: "C10",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "When a payment is held for approval, how many people must approve online to release it?",
  },
  {
    questionId: "C11",
    part: "Part C — The company’s rules",
    kind: "roster_multi",
    prompt: "Name them — choose from the people you told us about.",
  },
  {
    questionId: "C15",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "May the person who prepares a payment also count among those who release it?",
  },
  {
    questionId: "C16",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "When a payment is held for approval, how long may it wait before it is refused automatically?",
  },
  {
    questionId: "C16C",
    part: "Part C — The company’s rules",
    kind: "text",
    prompt: "How long, then? Name the length of time.",
  },
  {
    questionId: "C18",
    part: "Part C — The company’s rules",
    kind: "list",
    prompt: "Who should be told, immediately, when something is refused, paused, or halted? Name the security contact — a person, with a work email.",
  },
  {
    questionId: "C12",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "If these rules themselves ever need to change — limits raised, a person removed, the list edited — how many of these people must agree to the change?",
  },
  {
    questionId: "C12A",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "Should some kinds of change need more agreement than others?",
  },
  {
    questionId: "C12B",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "How many must agree to change the payment rules?",
  },
  {
    questionId: "C12C",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "How many must agree to change who the approvers are?",
  },
  {
    questionId: "C12D",
    part: "Part C — The company’s rules",
    kind: "single_choice",
    prompt: "How many must agree to change the approved lists?",
  },
  {
    questionId: "D0",
    part: "Part D — The agents",
    kind: "statement",
    prompt: "An agent can never be an approver. People release agents’ held payments; never the reverse. This is the platform’s rule, not a choice.",
  },
  {
    questionId: "D4",
    part: "Part D — The agents",
    kind: "single_choice",
    prompt: "If an agent suddenly starts paying much faster than its own usual pattern, what should happen?",
  },
  {
    questionId: "E0",
    part: "Part E — The levels beneath",
    kind: "statement",
    prompt: "Everything a level beneath you charters must fit inside your capacity — the total of what your wallet accounts can move, which is added up from them and never asked of you here. You can always tighten a level beneath you; if it ever needs more room, its manager can ask you for it, and you approve or decline.",
  },
  {
    questionId: "R0",
    part: "Part R — Recovery",
    kind: "statement",
    prompt: "Recovery exists, and it is governed. If the people who hold this estate are ever gone, or their passkeys are ever lost, there is a way back in — and the way back in obeys rules you set here, exactly as payments do. Nothing about recovery happens outside them.",
  },
  {
    questionId: "R1",
    part: "Part R — Recovery",
    kind: "single_choice",
    prompt: "If access is ever lost — people gone, passkeys lost — should this estate be recoverable?",
  },
  {
    questionId: "R2",
    part: "Part R — Recovery",
    kind: "multi_choice",
    prompt: "Which ways back in do you accept?",
  },
  {
    questionId: "R3",
    part: "Part R — Recovery",
    kind: "single_choice",
    prompt: "How many accepted methods must succeed before recovery is granted?",
  },
  {
    questionId: "G1",
    part: "Part G — The read-back",
    kind: "statement",
    prompt: "Nothing has been recorded as policy yet. Your whole charter is now read back in plain sentences — the chain of command first, then the people, the networks, the agents — and beside them your estate’s capacity, which nobody asked you for: it is the total of what your wallet accounts can move, added up. Confirming is the authoring act, under your own passkey.",
  },
] as const;

/** The Account Creation Interview as version 11 shipped it. */
export const CATALOG_V11_ACCOUNT: readonly FrozenQuestion[] = [
  {
    questionId: "W0",
    part: "Standing",
    kind: "statement",
    prompt: "You are creating a wallet account. Everything you set here must fit inside your company’s ceiling. This account’s policy governs the account and every wallet beneath it. Those wallets — the units carrying the chain addresses themselves — are unlimited, and have no questions and no policy of their own, by design.",
  },
  {
    questionId: "WN",
    part: "The wallet account",
    kind: "text",
    prompt: "What should this wallet account be called?",
  },
  {
    questionId: "W1",
    part: "The purpose",
    kind: "single_choice",
    prompt: "What is this wallet account for?",
  },
  {
    questionId: "P1",
    part: "The payroll dialect",
    kind: "list",
    prompt: "Who gets paid from this account? For each entry: person or provider, address, plain name.",
  },
  {
    questionId: "P2",
    part: "The payroll dialect",
    kind: "single_choice",
    prompt: "When does payroll run?",
  },
  {
    questionId: "P3",
    part: "The payroll dialect",
    kind: "money",
    prompt: "What is the largest single salary payment?",
  },
  {
    questionId: "P4",
    part: "The payroll dialect",
    kind: "roster_single",
    prompt: "Who runs payroll? (optional)",
  },
  {
    questionId: "T1",
    part: "The treasury dialect",
    kind: "money",
    prompt: "What is the absolute most that may ever leave treasury in one payment? This question is mandatory for a treasury account.",
  },
  {
    questionId: "T3",
    part: "The treasury dialect",
    kind: "single_choice",
    prompt: "Should a payment to anywhere new always wait for approval, even a small one?",
  },
  {
    questionId: "T4",
    part: "The treasury dialect",
    kind: "percent",
    prompt: "If more than a set share of this account’s balance is paid out in one day — digital assets leaving the account, not arriving — should the account stop cold? Enter the share as a percentage.",
  },
  {
    questionId: "O1",
    part: "The operations dialect",
    kind: "money",
    prompt: "How much does this account normally pay in one day?",
  },
  {
    questionId: "O2",
    part: "The operations dialect",
    kind: "money",
    prompt: "Below what amount may one person pay without a second approval?",
  },
  {
    questionId: "O3",
    part: "The operations dialect",
    kind: "single_choice",
    prompt: "Pay anyone, but pause the first payment to somewhere new?",
  },
  {
    questionId: "O4",
    part: "The operations dialect",
    kind: "roster_single",
    prompt: "Who runs this account day to day? (optional)",
  },
  {
    questionId: "X1",
    part: "The trading dialect",
    kind: "multi_choice",
    prompt: "Which networks does this account trade on, in addition to Aeredium — which is enabled by default and cannot be switched off?",
  },
  {
    questionId: "X1V",
    part: "The trading dialect",
    kind: "list",
    prompt: "Name the venues and counterparties: for each, the address and a plain name.",
  },
  {
    questionId: "X2",
    part: "The trading dialect",
    kind: "money",
    prompt: "What is the most this account may move in one day?",
  },
  {
    questionId: "X3",
    part: "The trading dialect",
    kind: "single_choice",
    prompt: "If this account’s pace suddenly jumps well beyond its own baseline, what should happen?",
  },
  {
    questionId: "X4",
    part: "The trading dialect",
    kind: "single_choice",
    prompt: "May it ever trade with a counterparty not on the list?",
  },
  {
    questionId: "X5",
    part: "The trading dialect",
    kind: "percent",
    prompt: "How far may a trade’s price slip from the price quoted before the trade must be abandoned? Enter a share as a percentage.",
  },
  {
    questionId: "X6",
    part: "The trading dialect",
    kind: "percent",
    prompt: "Should every trade be checked against an independent reference price? Enter the largest allowed difference as a percentage.",
  },
  {
    questionId: "X7",
    part: "The trading dialect",
    kind: "single_choice",
    prompt: "Should every trade be rehearsed as a dry run first, and refused if the rehearsal fails?",
  },
  {
    questionId: "X8",
    part: "The trading dialect",
    kind: "single_choice",
    prompt: "Should every trade be checked against an independent price oracle, and refused if the oracle disagrees?",
  },
  {
    questionId: "AG0",
    part: "The agent dialect",
    kind: "statement",
    prompt: "An agent can never be an approver. People release an agent’s held payments; never the reverse. This is the platform’s rule, not a choice. And for this account, the §2a law inverts (§2b): each agent’s wallet carries its OWN policy — one wallet per agent, one role per wallet, chosen from the twelve; the same role may dress several agents. Every agent is BORN FROZEN: nothing moves until you attach its role here in AER 360.",
  },
  {
    questionId: "AG2",
    part: "The agent dialect",
    kind: "money",
    prompt: "What is the most ANY agent’s wallet can pay in one payment? This is the outer ceiling — each agent’s own role policy may only tighten it.",
  },
  {
    questionId: "AG3",
    part: "The agent dialect",
    kind: "money",
    prompt: "And in one day, across ALL the agents in total?",
  },
  {
    questionId: "AG5",
    part: "The agent dialect",
    kind: "single_choice",
    prompt: "If this agent suddenly starts paying much faster than its own usual pattern, what should happen?",
  },
  {
    questionId: "AG6",
    part: "The agent dialect",
    kind: "roster_single",
    prompt: "Who oversees this agent — the person who answers for it when it is paused or halted? (optional)",
  },
  {
    questionId: "PN0",
    part: "Part PN — Areas of responsibility",
    kind: "statement",
    prompt: "A person here can hold an AREA OF RESPONSIBILITY with its own limits — a trader who may pay less in one payment than this account allows, a division head whose division carries its own daily ceiling. It stays inside this same company and this same charter: it is a scoped limit set attached to one named person, tighter than this account’s own and never wider. It is not a second estate, and it is not a company beneath you.",
  },
  {
    questionId: "PN1",
    part: "Part PN — Areas of responsibility",
    kind: "single_choice",
    prompt: "Does anyone here hold an area of responsibility with limits tighter than this account’s own?",
  },
  {
    questionId: "PN2",
    part: "Part PN — Areas of responsibility",
    kind: "list",
    prompt: "Name each one. For each: the person — by the work email your census gave them — what they are responsible for, and the limits that are theirs alone.",
  },
  {
    questionId: "WQ",
    part: "The approvers",
    kind: "single_choice",
    prompt: "When this account holds a payment for approval, how many people must agree to release it?",
  },
  {
    questionId: "WA1",
    part: "The approvers",
    kind: "list",
    prompt: "Name them. For each approver: full name, and work email. No policy exists without named people — and when more than one signature is required, name at least that many.",
  },
  {
    questionId: "WA2",
    part: "The approvers",
    kind: "single_choice",
    prompt: "May the person who submits a payment also be one of those who approve it?",
  },
  {
    questionId: "WCW",
    part: "The wallets",
    kind: "statement",
    prompt: "Once this account lives, wallets are created beneath it without limit — each carrying its own chain addresses, the 42-character EVM address and every other enabled network’s format. Every one of them comes under this account’s one policy, wholesale. There are no per-wallet questions, ever.",
  },
  {
    questionId: "WCA",
    part: "The wallets",
    kind: "statement",
    prompt: "Once this account lives, your agents gain the facility to create wallets beneath it — one per agent. Each agent is born frozen and takes its policy HERE: one of the twelve roles, attached in AER 360, adjustable beside its name — tighten or widen, save, and the save is attested by your approvers’ passkeys.",
  },
  {
    questionId: "WG1",
    part: "The read-back",
    kind: "statement",
    prompt: "Nothing is recorded until this account’s charter is read back — its standing, purpose, people, limits, list — and confirmed under your own passkey. On confirmation the writes travel in dependency order and the last step opens the account on the platform.",
  },
] as const;

/** The frozen set, by interview type — the shape the law test walks. */
export const CATALOG_V11: Record<'policy' | 'wallet_account', readonly FrozenQuestion[]> = {
  policy: CATALOG_V11_POLICY,
  wallet_account: CATALOG_V11_ACCOUNT,
};
