# 💾 Backups — Nightly, Off-Board

The SD card is the part most likely to die, so every night the Pi archives everything that's hard to recreate. A second machine then pulls a copy off the board.

---

## What gets saved

| Path | Why |
|---|---|
| `/opt/adguardhome` (conf + work) | AdGuard settings, clients, stats. Query log and filter lists are skipped because they re-download |
| `/opt/uptime-kuma` | Monitors and history (SQLite). The container is paused for a few seconds so the database copies cleanly |
| `/etc/sysctl.d/99-tailscale.conf` | IP forwarding for the exit node |
| `/etc/ssh/sshd_config.d/` | SSH hardening (root login off) |
| `/etc/fail2ban/jail.local`, `jail.d/` | Fail2ban jails |

An archive is about 22 MB. The Pi keeps 14 days in `/var/backups/pi/` (readable only by `fritz`, because it contains the AdGuard login hash). The pulling machine keeps the newest 30.

---

## 1. On the Pi

```bash
sudo install -m 755 pi-backup.sh /usr/local/bin/pi-backup.sh
sudo install -m 644 pi-backup.cron /etc/cron.d/pi-backup
sudo /usr/local/bin/pi-backup.sh && ls -lh /var/backups/pi
```

The job runs at 03:30 UTC (11:30 in Manila). Logs go to `journalctl -t pi-backup`.

---

## 2. On the machine that keeps copies

This uses a systemd **user** timer, so it needs no root. It works on the Steam Deck and on most Linux desktops. You need SSH key access to `fritz@192.168.18.28`.

```bash
install -Dm 755 pull-orangepi-backup.sh ~/.local/bin/pull-orangepi-backup.sh
install -Dm 644 orangepi-backup.service ~/.config/systemd/user/orangepi-backup.service
install -Dm 644 orangepi-backup.timer   ~/.config/systemd/user/orangepi-backup.timer
systemctl --user daemon-reload
systemctl --user enable --now orangepi-backup.timer
systemctl --user start orangepi-backup.service    # first pull now
ls -lh ~/Backups/orangepi
```

The timer fires daily at 12:00 local time, after the Pi's backup. `Persistent=true` catches up if the machine was asleep. The script tries the LAN address first and falls back to Tailscale.

---

## 3. Restore

On a freshly set-up Pi with Docker installed:

```bash
sudo tar -xzf pi-YYYY-MM-DD.tar.gz -C /
sudo sysctl --system && sudo systemctl reload ssh && sudo systemctl restart fail2ban
```

Then start the AdGuard Home and Uptime Kuma containers again with the same `-v /opt/...` mounts.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Pi Health shows "Backup is overdue" | Check `journalctl -t pi-backup` on the Pi |
| Pull fails | Run `systemctl --user status orangepi-backup` and test `ssh fritz@192.168.18.28` |
| Uptime Kuma shows "unhealthy" around 03:30 UTC | That's the backup pausing it for a few seconds. Pi Health waits 3 minutes before alerting |

> Not backed up: the Pi Health character pictures in `/var/lib/pi-health/custom`. They're your own files, so keep the originals.
