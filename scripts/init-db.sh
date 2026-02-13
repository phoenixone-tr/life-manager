#!/bin/bash
set -e

# Erstelle zusätzliche Datenbank für Baserow
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE baserow;
    GRANT ALL PRIVILEGES ON DATABASE baserow TO $POSTGRES_USER;
EOSQL
