#!/bin/sh
# Push an updated server.py / UI to the Pi. Run from this folder on your computer.
# Needs install.sh to have been run once on the Pi. Never touches the database.
set -eu
PI=${PI:-fritz@192.168.18.28}
cd "$(dirname "$0")"
sh ./fetch-assets.sh
# Build the new UI (Svelte) into ./app; uses the dev distrobox when npm isn't on the host.
if command -v npm >/dev/null 2>&1; then (cd web && npm ci --no-audit --no-fund && npm run build)
else distrobox enter dev -- sh -c "cd '$PWD/web' && npm ci --no-audit --no-fund && npm run build"; fi
rsync -a --delete static/ "$PI:/opt/money-manager/static/"
rsync -a --delete app/ "$PI:/opt/money-manager/app/"
rsync -a server.py "$PI:/opt/money-manager/server.py"
ssh "$PI" 'sudo -n systemctl restart money-manager && sleep 2 && systemctl is-active money-manager'
