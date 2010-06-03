#!/bin/sh
# If we boot up the server in the background then open the browser, zombie
# python processes get left behind. So we do it the other way around...

# Step 1: open the browser ten seconds from now
sh runserver_2_local.sh &

# Step 2: boot up the server in the meantime
# python manage.py runserver
# shared server on local network
python manage.py runserver 127.0.0.1:8000
