#!/bin/sh
set -eu

attempt=1
max_attempts=10

while ! alembic upgrade head; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Database migrations failed after $max_attempts attempts" >&2
    exit 1
  fi
  echo "Database migration attempt $attempt failed; retrying in 3s..." >&2
  attempt=$((attempt + 1))
  sleep 3
done

exec "$@"
