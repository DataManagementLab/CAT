#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER cat WITH PASSWORD 'cat';
    GRANT ALL PRIVILEGES ON DATABASE cat TO cat;
    CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
    \i /init_data/entropy.sql
EOSQL
