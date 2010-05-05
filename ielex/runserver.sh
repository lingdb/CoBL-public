#!/bin/sh
# If we boot up the server in the background then open the browser, zombie
# python processes get left behind. So we do it the other way around...

# Step 1: open the browser ten seconds from now
sh runserver_2.sh &

# Step 2: boot up the server in the meantime
# python manage.py runserver
# shared server on local network
python manage.py runserver 172.16.22.214:8000
