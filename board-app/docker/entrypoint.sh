#!/bin/sh
set -eu

# Wait briefly for DB to be reachable, then run alembic migrations.
# alembic itself fails fast if DB is gone, so we just retry a few times.
TRIES="${ALEMBIC_RETRIES:-30}"
SLEEP="${ALEMBIC_RETRY_DELAY:-2}"

i=0
while [ "${i}" -lt "${TRIES}" ]; do
  if alembic upgrade head; then
    break
  fi
  i=$((i + 1))
  echo "alembic upgrade failed (attempt ${i}/${TRIES}); sleeping ${SLEEP}s" >&2
  sleep "${SLEEP}"
done

if [ "${i}" -ge "${TRIES}" ]; then
  echo "alembic upgrade did not succeed after ${TRIES} attempts" >&2
  exit 1
fi

exec "$@"
