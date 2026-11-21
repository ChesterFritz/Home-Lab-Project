#!/bin/sh
# First-time install (or full reinstall) of Money Manager on the Orange Pi.
# Run on the Pi from this folder:  sudo ./install.sh [http://PHONE-IP:8888]
# Pass the phone's address (Money Manager > PC Manager turned on) to import its data.
# After this, ./deploy.sh on your computer can push updates without a password.
set -eu
APP_USER=${APP_USER:-fritz}
PHONE=${1:-}
cd "$(dirname "$0")"
sh ./fetch-assets.sh
install -d -o "$APP_USER" -g "$APP_USER" /opt/money-manager /var/lib/money-manager
install -m 644 -o "$APP_USER" -g "$APP_USER" server.py /opt/money-manager/server.py
rm -rf /opt/money-manager/static && cp -r static /opt/money-manager/static
# The new UI is built on your computer (deploy.sh does it); copy it if it's here.
if [ -f app/index.html ]; then rm -rf /opt/money-manager/app && cp -r app /opt/money-manager/app
else echo "note: ./app not built yet; the classic UI works at /classic/ until you run ./deploy.sh" >&2; fi
chown -R "$APP_USER:$APP_USER" /opt/money-manager /var/lib/money-manager
install -m 644 money-manager.service /etc/systemd/system/money-manager.service

if [ -n "$PHONE" ]; then
  sudo -u "$APP_USER" MM_DB=/var/lib/money-manager/money.sqlite python3 /opt/money-manager/server.py --import-from "$PHONE"
fi
[ -f /var/lib/money-manager/money.sqlite ] || { echo "No database yet. Re-run with the phone's address: sudo ./install.sh http://PHONE-IP:8888" >&2; exit 1; }

RULE="$APP_USER ALL=(root) NOPASSWD: /usr/bin/systemctl restart money-manager, /usr/bin/systemctl restart money-manager.service"
echo "$RULE" > /etc/sudoers.d/money-manager.tmp
chmod 440 /etc/sudoers.d/money-manager.tmp
visudo -cf /etc/sudoers.d/money-manager.tmp >/dev/null && mv /etc/sudoers.d/money-manager.tmp /etc/sudoers.d/money-manager

command -v ufw >/dev/null 2>&1 && ufw allow from 192.168.18.0/24 to any port 8888 proto tcp comment 'Money Manager LAN' >/dev/null && ufw allow in on tailscale0 to any port 8888 proto tcp comment 'Money Manager Tailscale' >/dev/null

systemctl daemon-reload
systemctl enable money-manager >/dev/null 2>&1
systemctl restart money-manager
sleep 2
systemctl --no-pager --lines=3 status money-manager
