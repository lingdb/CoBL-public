#!/bin/bash
cd /srv/cobl/deployment
cp cobl.service cobl-{backup,nexus}.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable cobl.service
systemctl enable cobl-backup.timer
systemctl enable cobl-nexus.timer
