#!/bin/bash
# tools/harness_seat.sh — seat the corridor harness's own customer on the connector's box (Spec T21 §2, 26 September 2026).
#
#   bash tools/harness_seat.sh <customer-id>
#
# Run by Bear on his Mac, as the birth scripts are (~/Downloads/diag/alex_invite.sh): it speaks to the connector's box
# over ssh and to the connector's Postgres through psql, with the customer id passed as a psql VARIABLE
# (-v customer_id=…) and read back as :'customer_id' — never interpolated into SQL. DATABASE_URL is read ON THE BOX
# from the unit's own environment file, and nothing of it is printed.
#
# What it does, and what it refuses:
#   reads the customer row BY ID — never by email — and refuses unless the email matches
#     ^harness\+[a-z0-9-]+@aeredium\.io$ exactly: only the harness's own customer is ever seated here;
#   refuses a customer holding an active (paid) live row, and any second live row (subscriptions_one_live admits one);
#   upserts the ONE live subscription row as the desk's webhook sets a Solo trial (services/billing.ts,
#     recordSubscriptionTrialStarted): package solo, plan monthly, state trialing, price_cents Solo's monthly figure as
#     the box configures it (CONNECTOR_PRICE_SOLO_MONTHLY_CENTS, 4900 unless the box says otherwise), current_period_end
#     now plus thirty-three days (CONNECTOR_TRIAL_DAYS, 30 unless the box says otherwise, and the webhook's three of
#     grace), the desk's handles (checkout_session_id, external_subscription_id) left null;
#   writes the zero-cent subscription_trial_started ledger line the webhook writes, idempotency key
#     harness:<customer-id>:<date>, so a second run the same day writes nothing twice;
#   never writes state active, never touches aap_account_id, funding_address or any agent row;
#   prints what it seated: the customer id, the package, the period end.
#
# HARNESS_SEAT_BOX (default ec2-user@3.231.26.5, the estate box the connector runs on — the box the birth script speaks
# to) and HARNESS_SEAT_ENV (default /etc/aer-connector/aer-connector.env, the unit's EnvironmentFile) name where the
# body runs and the file DATABASE_URL is read from there. HARNESS_SEAT_BOX=local runs the same body on this machine
# with the psql on PATH, which is how the tests hold the guard without a network.
set -euo pipefail

usage() {
  echo "usage: bash tools/harness_seat.sh <customer-id>" >&2
}

if [ $# -ne 1 ] || [ -z "${1:-}" ]; then
  usage
  exit 2
fi
ID="$1"
UUID_RE='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
if ! [[ "$ID" =~ $UUID_RE ]]; then
  echo "refused: $ID is not a customer id (a lower-case UUID); nothing was written" >&2
  exit 2
fi
BOX="${HARNESS_SEAT_BOX:-ec2-user@3.231.26.5}"
ENV_FILE="${HARNESS_SEAT_ENV:-/etc/aer-connector/aer-connector.env}"

# The body that runs where Postgres is. CUSTOMER_ID and ENV_FILE arrive in its environment; the heredoc is quoted, so
# nothing of this machine's shell is expanded into it.
BODY=$(cat <<'BODY'
set -euo pipefail
refuse() { echo "refused: $*" >&2; exit 3; }
if [ ! -r "$ENV_FILE" ]; then
  echo "fault: $ENV_FILE cannot be read here, so DATABASE_URL is unknown; nothing was written" >&2
  exit 4
fi
set -a; . "$ENV_FILE"; set +a
: "${DATABASE_URL:?fault: DATABASE_URL is not set in $ENV_FILE; nothing was written}"
PRICE_CENTS="${CONNECTOR_PRICE_SOLO_MONTHLY_CENTS:-4900}"
TRIAL_DAYS="${CONNECTOR_TRIAL_DAYS:-30}"
GRACE_DAYS=3
EMAIL_RE='^harness\+[a-z0-9-]+@aeredium\.io$'
TAB=$'\t'
PSQL=(psql "$DATABASE_URL" -X -q -v ON_ERROR_STOP=1 -v customer_id="$CUSTOMER_ID")

# 1. The customer row, by id and never by email. (The reads take no stdin: the body itself arrives on stdin.)
ROW=$("${PSQL[@]}" -At -F $'\t' -c "SELECT id, email FROM customers WHERE id = :'customer_id'::uuid" </dev/null)
if [ -z "$ROW" ]; then
  refuse "no customer holds the id $CUSTOMER_ID; nothing was written"
fi
EMAIL="${ROW#*$TAB}"
if ! [[ "$EMAIL" =~ $EMAIL_RE ]]; then
  refuse "customer $CUSTOMER_ID is not the harness's own: its email is not of the form harness+<tester>@aeredium.io; nothing was written"
fi

# 2. The live rows: subscriptions_one_live admits one, and this script writes no second and touches no paid one.
LIVE=$("${PSQL[@]}" -At -F $'\t' -c "SELECT id, state FROM subscriptions WHERE customer_id = :'customer_id'::uuid AND state IN ('pending', 'trialing', 'active') ORDER BY created_at DESC" </dev/null)
COUNT=0
if [ -n "$LIVE" ]; then
  COUNT=$(printf '%s\n' "$LIVE" | grep -c .)
fi
if [ "$COUNT" -gt 1 ]; then
  refuse "customer $CUSTOMER_ID holds $COUNT live subscription rows; subscriptions_one_live admits one, and this script writes no second; nothing was written"
fi
LIVE_STATE=""
if [ "$COUNT" -eq 1 ]; then
  LIVE_STATE="${LIVE#*$TAB}"
fi
if [ "$LIVE_STATE" = "active" ]; then
  refuse "customer $CUSTOMER_ID holds an active (paid) subscription; this script never writes state active and never touches a paid row; nothing was written"
fi

# 3. The seat, in one transaction: the one live row upserted as the webhook sets a Solo trial, and the ledger's line.
SEATED=$("${PSQL[@]}" -At -F $'\t' -v price_cents="$PRICE_CENTS" -v trial_days="$TRIAL_DAYS" -v grace_days="$GRACE_DAYS" <<'SQL'
BEGIN;
INSERT INTO subscriptions (customer_id, plan, package, state, price_cents, current_period_end)
VALUES (:'customer_id'::uuid, 'monthly', 'solo', 'trialing', :'price_cents'::int,
        now() + (:'trial_days'::int + :'grace_days'::int) * interval '1 day')
ON CONFLICT (customer_id) WHERE state IN ('pending', 'trialing', 'active')
DO UPDATE SET plan = EXCLUDED.plan, package = EXCLUDED.package, state = EXCLUDED.state, price_cents = EXCLUDED.price_cents,
              current_period_end = EXCLUDED.current_period_end, updated_at = now()
  WHERE subscriptions.state <> 'active'
RETURNING customer_id, package, plan, state, price_cents, to_char(current_period_end AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS UTC');
INSERT INTO ledger_entries (customer_id, kind, amount_cents, idempotency_key, detail)
SELECT s.customer_id, 'subscription_trial_started', 0,
       'harness:' || :'customer_id' || ':' || to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD'),
       jsonb_build_object('subscriptionId', s.id, 'externalSubscriptionId', NULL, 'trialDays', :'trial_days'::int,
                          'trialEndsAt', to_char((now() + :'trial_days'::int * interval '1 day') AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                          'seatedBy', 'tools/harness_seat.sh')
FROM subscriptions s
WHERE s.customer_id = :'customer_id'::uuid AND s.state = 'trialing'
ON CONFLICT (idempotency_key) DO NOTHING;
COMMIT;
SQL
)
if [ -z "$SEATED" ]; then
  refuse "nothing was seated for $CUSTOMER_ID: the live row was not written (an active row is never touched)"
fi
IFS=$'\t' read -r SEATED_ID SEATED_PACKAGE SEATED_PLAN SEATED_STATE SEATED_PRICE SEATED_END <<<"$SEATED"
echo "seated customer $SEATED_ID: package $SEATED_PACKAGE, plan $SEATED_PLAN, state $SEATED_STATE, price $SEATED_PRICE cents; period end $SEATED_END"
BODY
)

if [ "$BOX" = "local" ]; then
  CUSTOMER_ID="$ID" ENV_FILE="$ENV_FILE" bash -s <<<"$BODY"
else
  # The id is a UUID (checked above) and the file name is the operator's own, so both are safe to quote through sudo.
  ssh "$BOX" "sudo env CUSTOMER_ID='$ID' ENV_FILE='$ENV_FILE' bash -s" <<<"$BODY"
fi
