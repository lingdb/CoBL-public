#!/bin/bash
# Name to use for the new database dump:
cd /srv/cobl/deployment/backups/
t=$(date)
name=$(date -I)
echo "Creating backup $name…"
pg_dump --no-owner --no-acl cobl > $name.sql
echo "Compressing backup $name…"
gzip -f $name.sql
# Keeping only 10 latest dumps:
# Compare https://stackoverflow.com/a/10119963/448591
ls -tr *sql.gz | grep -v 'create\|dump.sql' | head -n -10 | xargs --no-run-if-empty rm
