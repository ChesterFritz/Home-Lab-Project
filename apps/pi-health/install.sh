#!/bin/sh
# First-time install (or full reinstall) of Pi Health on the Orange Pi.
# Run on the Pi from this folder:  sudo ./install.sh
# After this, ./deploy.sh on your computer can push updates without a password.
set -eu
APP_USER=${APP_USER:-fritz}
rm -rf /opt/pi-health/static
install -d -o "$APP_USER" -g "$APP_USER" /opt/pi-health /opt/pi-health/static
install -m 644 -o "$APP_USER" -g "$APP_USER" server.py /opt/pi-health/server.py
cp -r static/. /opt/pi-health/static/
chown -R "$APP_USER:$APP_USER" /opt/pi-health
[ -f /etc/pi-health.json ] || install -m 644 config.example.json /etc/pi-health.json
install -m 644 pi-health.service /etc/systemd/system/pi-health.service

# Let the app user restart this one service (and nothing else) without a password.
RULE="$APP_USER ALL=(root) NOPASSWD: /usr/bin/systemctl restart pi-health, /usr/bin/systemctl restart pi-health.service"
echo "$RULE" > /etc/sudoers.d/pi-health.tmp
chmod 440 /etc/sudoers.d/pi-health.tmp
visudo -cf /etc/sudoers.d/pi-health.tmp >/dev/null && mv /etc/sudoers.d/pi-health.tmp /etc/sudoers.d/pi-health

systemctl daemon-reload
systemctl enable pi-health >/dev/null 2>&1
systemctl restart pi-health
sleep 2
systemctl --no-pager --lines=3 status pi-health
