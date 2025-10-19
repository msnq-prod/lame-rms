#!/bin/bash

# This file is used by the docker container to build the database schema and seed the database with initial data

cd /var/www/html

# Validate expected environment variables
echo "AdamRMS - Checking for Environment Variables"
if [[ ! -v DB_HOSTNAME ]] || [[ ! -v DB_DATABASE ]] || [[ ! -v DB_USERNAME ]] || [[ ! -v DB_PASSWORD ]]; then
    echo "AdamRMS - Expected Environment Variables not set"
    exit 1
fi

# Wait for the database to become available
if [ -x ./scripts/wait-for-db.sh ]; then
    echo "AdamRMS - Waiting for database availability"
    ./scripts/wait-for-db.sh
fi

# Database migration & seed
echo "AdamRMS - Starting Migration Script"

php vendor/bin/phinx migrate -e production
php vendor/bin/phinx seed:run -e production

if [[ -v DEV_MODE ]] && [[ "${DEV_MODE}" == 'true' ]]; then
    echo "AdamRMS - Running in DEV MODE"
fi

# Start Server
echo "AdamRMS - Starting Apache2"
apache2-foreground