#!/bin/bash
cd /srv/cobl/
pcount=$(grep -c "^processor" /proc/cpuinfo)
wcount=$(./venv/bin/python -c "print($pcount * 2 + 1)")
./venv/bin/gunicorn --workers $wcount --bind=localhost:5000 wsgi:application
