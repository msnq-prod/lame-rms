#!/bin/sh
set -eu
if set -o pipefail 2>/dev/null; then
    :
fi

HOST="${DB_HOSTNAME:-db}"
PORT="${DB_PORT:-3306}"
USER="${DB_USERNAME:-root}"
PASSWORD="${DB_PASSWORD:-}"
TIMEOUT="${WAIT_FOR_DB_TIMEOUT:-60}"

start_time=$(date +%s)

echo "Waiting for database at ${HOST}:${PORT}"

if [ -n "$PASSWORD" ]; then
    export MYSQL_PWD="$PASSWORD"
fi

while true; do
    if mysqladmin ping --silent -h"$HOST" -P"$PORT" -u"$USER"; then
        break
    fi

    current_time=$(date +%s)
    if [ $((current_time - start_time)) -ge "$TIMEOUT" ]; then
        echo "Timed out waiting for database at ${HOST}:${PORT} after ${TIMEOUT}s" >&2
        exit 1
    fi

    sleep 1
done

echo "Database is available"
