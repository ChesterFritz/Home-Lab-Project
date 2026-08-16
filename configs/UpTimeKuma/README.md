# 📡 Uptime Kuma — Setup Guide

Step-by-step instructions to replicate this Uptime Kuma setup on Armbian Debian Trixie.



## Why Uptime Kuma

I tried the usual monitoring recommendations — Grafana, Netdata, Prometheus — but they're either too heavy for a 1GB board or just overkill for what I actually need. Uptime Kuma made more sense, lightweight and gets the job done.



## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Docker | Docker CE installed and running — see [Docker Setup Guide](../docker/README.md) |
| Firewall | Port 3001 allowed if UFW is active — see [UFW Setup Guide](../ufw/README.md) |

If UFW is already enabled, open the port first or the web UI will not load:

```bash
sudo ufw allow from 192.168.18.0/24 to any port 3001 proto tcp
```



## 1. Run Uptime Kuma Container

The container must be run with the Docker socket mounted so it can monitor other containers directly:

```bash
docker run -d \
  --name uptime-kuma \
  --restart unless-stopped \
  -p 3001:3001 \
  -v /opt/uptime-kuma:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  louislam/uptime-kuma:1
```

> **Why mount the Docker socket?** Without `-v /var/run/docker.sock:/var/run/docker.sock:ro`, Uptime Kuma cannot monitor Docker container health directly. The container will connect but the Docker Host test will fail with `connect ENOENT /var/run/docker.sock`.

> ⚠️ **Mount it read-only.** The `:ro` suffix matters — read-write access to the Docker socket from inside a container is equivalent to root on the host. Health checks only need read access, so there is no reason to grant more.

> **Tag choice** — `:1` floats to the latest v1 release, so restarts pick up updates automatically. Convenient, but not reproducible. Pin a specific version if you want deterministic rebuilds.

---

## 2. Initial Setup

1. Open a browser and go to `http://YOUR_DEVICE_IP:3001`
2. Create an admin username and password
3. You will be taken to the dashboard

---

## 3. Setup Docker Host

Required before adding Docker container monitors:

1. Go to **Add New Monitor → Docker Container**
2. Click **Setup Docker Host**
3. Fill in the details:

| Field | Value |
|-------|-------|
| Friendly Name | `Orange Pi` |
| Connection Type | `Socket` |
| Docker Daemon | `/var/run/docker.sock` |

4. Click **Test** — should return green
5. Click **Save**



## 4. Add Monitors

All monitors use a **120 second** check interval — low frequency keeps CPU and SD card writes minimal on a 1GB board.

### AdGuard Home — Container (Docker)
| Field | Value |
|-------|-------|
| Monitor Type | `Docker Container` |
| Friendly Name | `AdGuard Home` |
| Container Name | `adguardhome` |
| Docker Host | `Orange Pi` |

> Docker Container monitors report health state, not latency — the Ping field will show `N/A`. This is expected.

### DNS Primary (Ping)
| Field | Value |
|-------|-------|
| Monitor Type | `Ping` |
| Friendly Name | `DNS Primary` |
| Hostname | `1.1.1.1` |

> This monitors upstream WAN reachability, not local DNS resolution. A future improvement is a **DNS** type monitor pointed at the Orange Pi itself, which would catch AdGuard failing to resolve.

### Orange Pi (Ping)
| Field | Value |
|-------|-------|
| Monitor Type | `Ping` |
| Friendly Name | `Orange pi` |
| Hostname | `192.168.18.28` |

### Tailscale (Ping)
| Field | Value |
|-------|-------|
| Monitor Type | `Ping` |
| Friendly Name | `Tailscale` |
| Hostname | `100.81.251.12` |

> Pings the host's own Tailscale IP — confirms the tailnet interface is up and the daemon is running.



## ✅ Verify It's Working

Dashboard should show all monitors green with **4 Up, 0 Down**.

```
AdGuard Home     ✅ 100%
DNS Primary      ✅ 100%
Orange pi        ✅ 100%
Tailscale        ✅ 100%
```



## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `connect ENOENT /var/run/docker.sock` | Docker socket not mounted | Recreate container with `-v /var/run/docker.sock:/var/run/docker.sock:ro` |
| Docker Host test fails | Container recreated without socket | See fix above — verify with `docker inspect uptime-kuma \| grep docker.sock` |
| Web UI unreachable on `:3001` | UFW blocking the port | `sudo ufw allow from YOUR_SUBNET to any port 3001 proto tcp` |
| Monitor shows Down immediately | Wrong monitor type | HTTP monitors need a URL, Ping monitors need a hostname |
| Container gone after reboot | Missing restart policy | Recreate with `--restart unless-stopped` |
| Docker monitor shows `Ping: N/A` | Not an error | Container monitors track health state, not latency |



## 📝 Notes

| Note | Details |
|------|---------|
| Data persistence | Stored in `/opt/uptime-kuma` — survives container recreation, back up before reflashing |
| Socket access | Mounted read-only — Uptime Kuma can inspect container state but cannot start, stop, or create containers |
| Check interval | 120 seconds — keeps CPU and SD card writes low |
| RAM usage | ~80–120MB — heaviest container in the stack, still fine on 1GB |
| Notifications | None configured yet — Discord, Telegram, ntfy, and webhooks are supported when needed |



## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [AdGuard Home Docker Setup](../adguard/README.md) | Network-wide DNS filtering via Docker |
| [UFW Setup](../ufw/README.md) | Host firewall configuration |
| [Tailscale Setup](../tailscale/README.md) | VPN exit node setup on Armbian |