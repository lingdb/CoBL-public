#!/bin/bash
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root." 1>&2
   exit 1
fi
cd /srv/cobl/deployment
cp cobl.service cobl-{backup,nexus}.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable cobl.service
systemctl enable cobl-backup.timer
systemctl enable cobl-nexus.timer
