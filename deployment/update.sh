#!/bin/bash
cd /srv/cobl
git pull
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r REQUIREMENTS
cd static
npm install
nodejs ./node_modules/bower/bin/bower install
nodejs ./node_modules/grunt-cli/bin/grunt
cd ..
./venv/bin/python manage.py migrate
