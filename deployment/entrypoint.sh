#!/bin/bash
pcount=$(grep -c "^processor" /proc/cpuinfo)
wcount=$(./venv/bin/python -c "print($pcount * 2 + 1)")
./venv/bin/gunicorn --workers $wcount --bind=$(hostname -i):5000 wsgi:application
