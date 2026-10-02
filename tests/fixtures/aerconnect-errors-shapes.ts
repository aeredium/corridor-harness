/**
 * A dictionary in the shapes packages/shared/src/errors.ts may land in, for the harness's reader of it
 * (tests/test_aerconnect_lexicon.py). Not a copy of the connector's file, which does not exist yet: the reader must read
 * a name and its one-line description from a plain map, from a map of objects, across `+`, past comments, and must
 * leave alone what is not an entry.
 */
import { something } from './elsewhere';

// The plain map: a name, then its sentence. A comment with a colon: and a 'quote' is skipped.
export const ERROR_DESCRIPTIONS = Object.freeze({
  group_not_assigned: 'the signing group is not assigned to the account',
  'PolicyDenied': "A refusal of policy, " + 'the same on retry.',
  /* a block comment with "quotes", { braces } and key: 'value' inside */
  RESOURCE_EXHAUSTED: `On the stream road: the orchestrator pipeline is saturated.`,
});

// The map of objects: the description under its own key, other fields beside it.
export const ERROR_DICTIONARY: Readonly<Record<string, { status: number; description: string }>> = {
  invalid_credential: {
    status: 401,
    description:
      'the credential presented is not a credential this platform knows: ' +
      'no active credential matched it',
    owner: 'the access platform',
  },
  NOT_AUTHENTICATED: { status: 401, summary: 'You are not signed in.' },
};

// Not entries: a status table, a list, an interpolated template, a function.
export const STATUS = { NOT_AUTHENTICATED: 401, invalid_credential: 403 };
export const NAMES = ['PolicyDenied', 'Held'];
export const COMPOSED = { Held: `held for ${'a second approver'}` };
export function describe(name: string): string {
  return ERROR_DESCRIPTIONS[name as keyof typeof ERROR_DESCRIPTIONS] ?? 'unclassified';
}
