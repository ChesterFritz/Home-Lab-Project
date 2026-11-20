# 🩺 Pi Health — Live Dashboard

A tiny health dashboard for the Orange Pi PC. It's a single Python file with no dependencies and uses about 11 MB of RAM. Open it in a browser, or add it to your phone's home screen to use it like an app.

**Open it:** `http://192.168.18.28:8090` at home, or `http://100.81.251.12:8090` over Tailscale.

---

## What it shows

| Panel | Source | Notes |
|---|---|---|
| CPU | `/proc/stat`, cpufreq | Total and per-core usage, clock speed, load average |
| Temperature | `thermal_zone0` | Allwinner H3 on-die sensor |
| GPU | devfreq `1c40000.gpu` | Mali-400 MP2 (lima). There's no usage counter, so "busy" is the share of time spent above the idle clock |
| Power **(estimated)** | Model | No current sensor on this board. Estimated from CPU load × clock × core voltage² plus GPU activity, about ±30%. Use a USB power meter for real numbers |
| Network | `/proc/net/dev` | LAN (`end0`) download and upload, plus Tailscale traffic |
| Memory, SD card, uptime | `/proc/meminfo`, `statvfs`, `/proc/uptime` | |
| Services | Docker socket, DNS query, TCP probe | AdGuard, Uptime Kuma, AdGuard DNS answering, internet, Tailscale, failed systemd units, last backup |

History keeps 1 hour at 2-second samples and 24 hours at 1-minute averages. The 24-hour history survives restarts.

---

## Alerts

An alert only fires once its condition has lasted for the hold time. That avoids false alarms from brief spikes.

| Alert | Severity | Hold |
|---|---|---|
| CPU ≥ 70 °C / ≥ 80 °C | Warning / Critical | 30 s |
| CPU ≥ 90% average | Warning | 5 min |
| CPU throttling under load | Warning | 60 s |
| Memory < 20% / < 10% available | Warning / Critical | 60 s |
| Swap ≥ 50% | Warning | 2 min |
| SD card ≥ 85% / ≥ 95% | Warning / Critical | — |
| Container down or missing | Critical | 30 s |
| Container unhealthy | Serious | 3 min (the nightly backup pauses Uptime Kuma briefly) |
| AdGuard DNS not answering | Critical | 60 s |
| Internet down | Serious | 60 s |
| Tailscale down | Serious | 60 s |
| A systemd unit failed | Warning | — |
| Backup older than 26 h | Warning | — |

### Apps launcher

The **Apps** row links to AdGuard Home, Uptime Kuma, the router and the Tailscale admin console. Each link shows whether the app is up: the Pi tries to open the link every 15 seconds and also checks the app's container. `{host}` is replaced by the address you opened the dashboard on, so the links work at home and over Tailscale. To add your own, put a `links` list in `/etc/pi-health.json`:

```json
"links": [
  { "name": "AdGuard Home", "desc": "Ad blocking and DNS", "url": "http://{host}/", "icon": "shield", "container": "adguardhome" },
  { "name": "My app", "desc": "What it does", "url": "http://{host}:8123/", "icon": "link" }
]
```

Icons: `shield`, `pulse`, `router`, `mesh`, `link`. Add `"probe": false` for links outside your network.

### Themes

The ♡/moon button at the top right switches between **Match system**, **Light**, **Dark** and two loud anime themes:

- **Kirino ♡**: pink manga panels, sakura petals, tsundere wording
- **Kuroneko ✦**: gothic black and purple, drifting feathers, dark-lord wording

Both have Pi-chan, an original mascot whose face follows the Pi's status (tap her). They also have sound-effect words on busy readouts, a stats ticker and a burst when an alert fires. Optional sound effects can be turned on in the same menu. Link straight to a theme with `?theme=kirino` or `?theme=kuroneko`. With Reduce Motion turned on, the animations switch off. The Japanese fonts only download once an anime theme is picked.

**Character pictures:** in an anime theme, open **Character pictures…** to upload your own images: a main picture, one per mood, a corner character and a background. They're stored in `/var/lib/pi-health/custom` on the Pi only, so nothing copyrighted ends up in this repo. PNG, JPEG, WebP or GIF, up to 8 MB.

### Phone notifications (optional)

1. Install the **ntfy** app and subscribe to a hard-to-guess topic, for example `pi-health-<random>`.
2. Set `"ntfy_url": "https://ntfy.sh/pi-health-<random>"` in `/etc/pi-health.json`.
3. Run `sudo systemctl restart pi-health`.

---

## Install or update

The page is a Svelte 5 + Tailwind app (with uPlot charts) in `web/`. It's built into `static/`, which the Python server serves. Fonts and libraries are bundled in, so the page keeps working when the internet is down.

**First install.** Build the page on your computer, because `static/` isn't committed. Then install once on the Pi:

```bash
cd apps/pi-health/web && npm ci && npm run build && cd ../../..
scp -r apps/pi-health fritz@192.168.18.28:/tmp/
ssh -t fritz@192.168.18.28 'cd /tmp/pi-health && sudo ./install.sh'
sudo ufw allow from 192.168.18.0/24 to any port 8090 proto tcp comment "Pi Health dashboard"
```

`install.sh` makes `fritz` the owner of `/opt/pi-health` and lets `fritz` restart this one service without a password. That way updates never need sudo.

**Updates**, from your computer:

```bash
./deploy.sh          # builds web/, then rsyncs to the Pi and restarts the service
```

**Working on the UI:** run `cd web && npm run dev`. It serves the page with hot reload and proxies `/api` to the real Pi.

| Path | What |
|---|---|
| `/opt/pi-health/` | App |
| `/etc/pi-health.json` | Config (thresholds, port, ntfy). Kept on updates |
| `/var/lib/pi-health/` | Saved alert log and 24-hour history |
| `pi-health.service` | Runs as `fritz` (+ `docker` group), limited to 60 MB of RAM, read-only filesystem |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Page won't load from another device | Check the UFW rule above with `sudo ufw status` |
| "Pi unreachable" banner | Pi is off or off the network, or the service stopped. Check `systemctl status pi-health` |
| Logs | `journalctl -u pi-health -f` |
| API | `curl localhost:8090/api/state`, and `/api/history?range=5m\|15m\|1h\|6h\|24h` |
