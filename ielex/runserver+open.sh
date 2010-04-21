#!/bin/sh
# If we boot up the server in the background then open the browser, zombie
# python processes get left behind.

# Step 1: open the browser ten seconds from now
sh runserver_2.sh &

# Step 2: boot up the server in the meantime
python manage.py runserver
