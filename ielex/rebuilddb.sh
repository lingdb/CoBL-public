#!/bin/sh
set -e
rotate -r db.sqlite3
python manage.py syncdb
cd dev
python dev_data.py
# open http://127.0.0.1:8000/
