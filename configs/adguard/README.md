# 🛡️ AdGuard Home — Docker Setup Guide

Step-by-step instructions to replicate this AdGuard Home setup running in Docker on Armbian Debian Trixie.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Docker | Docker CE installed and running — see [Docker Setup Guide](../docker/README.md) |
| Ports | 53 (DNS) and 80 (Web UI) must be available |

---

## 1. Free Up Port 53

On Armbian Debian Trixie, `systemd-resolved` occupies port 53 by default. Disable it before starting the container:

```bash
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf
```

> **Why:** `systemd-resolved` binds to port 53 as a local DNS stub resolver. Any container attempting to bind port 53 will fail to start if this is not disabled first. The container will be stuck in `Created` state with no error logs.

---

## 2. Run AdGuard Home Container

```bash
docker run --name adguardhome \
  --restart unless-stopped \
  -v /opt/adguardhome/work:/opt/adguardhome/work \
  -v /opt/adguardhome/conf:/opt/adguardhome/conf \
  -p 53:53/tcp -p 53:53/udp \
  -p 80:80/tcp \
  -p 3000:3000/tcp \
  -d adguard/adguardhome
```

> **Note:** Port 3000 is the initial setup wizard only. After completing the wizard, AdGuard Home moves to port 80. Both are mapped here to cover the full setup flow.

---

## 3. Initial Web Setup

1. Open a browser and go to `http://YOUR_DEVICE_IP:3000`
2. Follow the setup wizard
3. Set your admin username and password
4. Set DNS listen interface to **All interfaces**, port **53**
5. Set web interface port to **80**

After completing the wizard, access the dashboard at `http://YOUR_DEVICE_IP`

---

## 4. Restore Config from Backup (Optional)

If you have an existing AdGuard Home config backup:

```bash
# Copy backup to device
scp adguard-backup.tar.gz root@YOUR_DEVICE_IP:~/

# Stop the container
docker stop adguardhome

# Extract backup
tar -xzvf ~/adguard-backup.tar.gz -C /

# Copy config to Docker volume
cp /opt/AdGuardHome/AdGuardHome.yaml /opt/adguardhome/conf/AdGuardHome.yaml

# Restart container
docker restart adguardhome
```

---

## 5. Blocklists

The following blocklists are used in this setup. Add via **Filters → DNS Blocklists → Add blocklist**:

| Name | URL |
|------|-----|
| AdGuard DNS filter | `https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt` |
| Hagezi Pro Plus | `https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/pro.plus.txt` |
| AdGuard SDNS Filter | `https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt` |
| OISD Full | `https://big.oisd.nl` |

---

## 6. Point Your Devices to AdGuard

| Method | How |
|--------|-----|
| Router-level | Change DNS in your router settings to `YOUR_DEVICE_IP` |
| Per-device | Manually set DNS to `YOUR_DEVICE_IP` in network settings |

---

## ✅ Verify It's Working

```bash
# Check container is running
docker ps

# Check AdGuard logs
docker logs adguardhome

# Test DNS resolution
nslookup google.com YOUR_DEVICE_IP
```

Access the dashboard at `http://YOUR_DEVICE_IP`

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Container stuck in `Created` | Port 53 conflict | Disable `systemd-resolved` (Step 1) |
| Can't reach `:3000` after wizard | AdGuard moved to port 80 | Access `http://YOUR_DEVICE_IP` instead |
| Can't reach `:80` | Port 80 not mapped | Recreate container with `-p 80:80/tcp` |
| `exec format error` | Wrong architecture image | Verify `linux/arm/v7` support on Docker Hub |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [Tailscale Setup](../tailscale-armbian/README.md) | VPN exit node setup on Armbian |