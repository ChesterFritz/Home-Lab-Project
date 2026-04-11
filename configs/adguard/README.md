# AdGuard Home — Setup Guide

Step-by-step instructions to replicate this AdGuard Home setup on a new machine.

---

## Prerequisites

- Linux-based SBC or server (tested on Orange Pi One H3, Ubuntu 20.04)
- Root or sudo access
- Port 53 and 80 available

---

## 1. Free Up Port 53

On Ubuntu, `systemd-resolved` occupies port 53 by default. Disable it first:

```bash
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 9.9.9.9" | sudo tee /etc/resolv.conf
```

---

## 2. Install AdGuard Home

```bash
curl -s -S -L https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh | sh -s -- -v
```

AdGuard Home will install to `/opt/AdGuardHome/`.

---

## 3. Initial Web Setup

1. Open a browser and go to `http://YOUR_DEVICE_IP:3000`
2. Follow the setup wizard
3. Set your admin username and password
4. Set DNS listen port to **53**
5. Set web interface port to **80**

---

## 4. Apply This Config

Replace the default config with the one from this repo:

```bash
sudo systemctl stop AdGuardHome
sudo cp AdGuardHome.yaml /opt/AdGuardHome/AdGuardHome.yaml
sudo systemctl start AdGuardHome
```

> **Note:** The config file does not include credentials. On first launch after
> applying the config, AdGuard Home will prompt you to create a new username
> and password via the setup wizard at `http://YOUR_DEVICE_IP:3000`.
> All other settings (blocklists, DNS upstreams, filters) will apply automatically
> from the config.

---

## 5. Add Blocklists

The following blocklists are used in this setup. These are already in the config
file but can be added manually via **Filters → DNS Blocklists → Add blocklist**:

| Name | URL |
|------|-----|
| AdGuard DNS filter | `https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt` |
| Hagezi Pro Plus | `https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/pro.plus.txt` |
| AdGuard SDNS Filter | `https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt` |
| OISD Full | `https://big.oisd.nl` |

---

## 6. Point Your Devices to AdGuard

Set your router's DNS server to your device's local IP, or configure per-device:

- **Router-level:** Change DNS in your router settings to `YOUR_DEVICE_IP`
- **Per-device:** Manually set DNS to `YOUR_DEVICE_IP` in network settings

---

## Verify It's Working

```bash
# Check AdGuard is running
sudo systemctl status AdGuardHome

# Test DNS resolution
nslookup google.com YOUR_DEVICE_IP
```

Access the dashboard at `http://YOUR_DEVICE_IP`