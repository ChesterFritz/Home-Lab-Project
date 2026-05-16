# 📡 Uptime Kuma — Setup Guide

Step-by-step instructions to replicate this Uptime Kuma setup on Armbian Debian Trixie.

---

## Why Uptime Kuma

I tried the usual monitoring recommendations — Grafana, Netdata, Prometheus — but they're either too heavy for a 1GB board or just overkill for what I actually need. Uptime Kuma made more sense, lightweight and gets the job done.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Docker | Docker CE installed and running — see [Docker Setup Guide](../docker/README.md) |

---

## 1. Run Uptime Kuma Container

The container must be run with the Docker socket mounted so it can monitor other containers directly:

```bash
docker run -d \
  --name uptime-kuma \
  --restart unless-stopped \
  -p 3001:3001 \
  -v /opt/uptime-kuma:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  louislam/uptime-kuma:1
```

> **Why mount the Docker socket?** Without `-v /var/run/docker.sock:/var/run/docker.sock`, Uptime Kuma cannot monitor Docker container health directly. The container will connect but the Docker Host test will fail with `connect ENOENT /var/run/docker.sock`.

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

---

## 4. Add Monitors

### DNS Primary (Ping)
| Field | Value |
|-------|-------|
| Monitor Type | `Ping` |
| Friendly Name | `DNS Primary` |
| Hostname | `1.1.1.1` |

### Orange Pi (Ping)
| Field | Value |
|-------|-------|
| Monitor Type | `Ping` |
| Friendly Name | `Orange Pi` |
| Hostname | `YOUR_DEVICE_IP` |

### AdGuard Home — Web UI (HTTP)
| Field | Value |
|-------|-------|
| Monitor Type | `HTTP(s)` |
| Friendly Name | `Adguard` |
| URL | `http://YOUR_DEVICE_IP` |

### AdGuard Home — Container (Docker)
| Field | Value |
|-------|-------|
| Monitor Type | `Docker Container` |
| Friendly Name | `AdGuard Home` |
| Container Name | `adguardhome` |
| Docker Host | `Orange Pi` |

### Speedtest Tracker — Container (Docker)
| Field | Value |
|-------|-------|
| Monitor Type | `Docker Container` |
| Friendly Name | `Speedtest Tracker` |
| Container Name | `speedtest-tracker` |
| Docker Host | `Orange Pi` |

---

## ✅ Verify It's Working

Dashboard should show all monitors green with **5 Up, 0 Down**.

```
Adguard          ✅ 100%
AdGuard Home     ✅ 100%
DNS Primary      ✅ 100%
Orange Pi        ✅ 100%
Speedtest Tracker ✅ 100%
```

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `connect ENOENT /var/run/docker.sock` | Docker socket not mounted | Recreate container with `-v /var/run/docker.sock:/var/run/docker.sock` |
| Docker Host test fails | Container recreated without socket | See fix above |
| Monitor shows Down immediately | Wrong monitor type | HTTP monitors need a URL, Ping monitors need a hostname |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [AdGuard Home Docker Setup](../adguard/README.md) | Network-wide DNS filtering via Docker |
| [Tailscale Setup](../tailscale/README.md) | VPN exit node setup on Armbian |