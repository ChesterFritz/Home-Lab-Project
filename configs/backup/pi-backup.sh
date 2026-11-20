#!/bin/sh
# Nightly backup of AdGuard Home, Uptime Kuma and key system config.
set -eu
DEST=/var/backups/pi
KEEP_DAYS=14
STAMP=$(date +%F)
mkdir -p "$DEST"
# Pause Uptime Kuma briefly so its SQLite database is copied consistently.
docker pause uptime-kuma >/dev/null 2>&1 || true
trap 'docker unpause uptime-kuma >/dev/null 2>&1 || true' EXIT
tar -czf "$DEST/pi-$STAMP.tar.gz" \
  --exclude='opt/adguardhome/work/data/querylog*' \
  --exclude='opt/adguardhome/work/data/filters' \
  --exclude='opt/uptime-kuma/screenshots' \
  -C / opt/adguardhome opt/uptime-kuma \
  etc/sysctl.d/99-tailscale.conf etc/ssh/sshd_config.d \
  $(cd / && ls -d etc/fail2ban/jail.local etc/fail2ban/jail.d 2>/dev/null)
docker unpause uptime-kuma >/dev/null 2>&1 || true
trap - EXIT
chown -R fritz:fritz "$DEST"; chmod 700 "$DEST"; chmod 600 "$DEST"/*.tar.gz
find "$DEST" -name 'pi-*.tar.gz' -mtime +$KEEP_DAYS -delete
