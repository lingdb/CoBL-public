#!/bin/sh
python manage.py runserver &
open http://127.0.0.1:8000/
