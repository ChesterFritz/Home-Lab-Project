#!/bin/sh
# Build the web UI and push an update to the Pi. Run from this folder on your computer.
# Needs install.sh to have been run once on the Pi.
set -eu
PI=${PI:-fritz@192.168.18.28}
cd "$(dirname "$0")"
if command -v npm >/dev/null 2>&1; then (cd web && npm ci --no-audit --no-fund && npm run build)
else distrobox enter dev -- sh -c "cd '$PWD/web' && npm ci --no-audit --no-fund && npm run build"; fi
rsync -a --delete static/ "$PI:/opt/pi-health/static/"
rsync -a server.py "$PI:/opt/pi-health/server.py"
ssh "$PI" 'sudo -n systemctl restart pi-health && sleep 2 && systemctl is-active pi-health'
