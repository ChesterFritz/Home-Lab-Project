# 🛡️ AdGuard Home — Docker Setup Guide

Step-by-step instructions to replicate this AdGuard Home setup running in Docker on Armbian Debian Trixie.



## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Docker | Docker CE installed and running — see [Docker Setup Guide](../docker/README.md) |
| Ports | 53 (DNS) and 80 (Web UI) must be available |
| Firewall | Ports 53 and 80 allowed if UFW is active — see [UFW Setup Guide](../ufw/README.md) |

If UFW is already enabled:

```bash
sudo ufw allow from 192.168.18.0/24 to any port 53
sudo ufw allow from 192.168.18.0/24 to any port 80 proto tcp
```

> Port 53 intentionally omits `proto` — DNS clients use UDP, and both are needed.

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

Confirm nothing holds the port:

```bash
sudo ss -tulpn | grep :53
```

> ⚠️ **If Tailscale is installed**, MagicDNS will rewrite `/etc/resolv.conf`. Lock it after setting your nameserver — see the [Fail2ban guide](../fail2ban/README.md) for the full fix.

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

> **Tag** — `adguard/adguardhome` resolves to `:latest`. Convenient for updates, not reproducible. Pin a version tag if you want deterministic rebuilds.

---

## 3. Initial Web Setup

1. Open a browser and go to `http://YOUR_DEVICE_IP:3000`
2. Follow the setup wizard
3. Set your admin username and password
4. Set DNS listen interface to **All interfaces**, port **53**
5. Set web interface port to **80**

After completing the wizard, access the dashboard at `http://YOUR_DEVICE_IP`

---

## 4. Configure DNS-over-HTTPS Upstreams

By default AdGuard forwards queries in plaintext, which your ISP can read and log. DoH encrypts them.

**Settings → DNS settings → Upstream DNS servers**

```text
https://dns.cloudflare.com/dns-query
https://dns.quad9.net/dns-query
https://dns.google/dns-query
```

Set **Load-balancing mode** to *Parallel requests* for speed, or *Load-balancing* to spread queries across providers.

**Bootstrap DNS servers** — needed to resolve the DoH hostnames themselves:

```text
1.1.1.1
9.9.9.9
```

Click **Test upstreams** — all three should return OK. Apply.

> **Why this matters:** DoH means DNS queries leaving the Orange Pi are encrypted and not visible to the ISP. Without it, every domain you resolve is plaintext on the wire regardless of HTTPS on the site itself.

> **What it does not do:** the ISP still sees destination IPs and SNI. DoH hides the lookup, not the connection.

---

## 5. Restore Config from Backup (Optional)

If you have an existing AdGuard Home config backup:

```bash
# Copy backup to device
scp adguard-backup.tar.gz fritz@YOUR_DEVICE_IP:~/

# Stop the container
docker stop adguardhome

# Extract backup
tar -xzvf ~/adguard-backup.tar.gz -C /

# Copy config into the Docker volume
cp /opt/AdGuardHome/AdGuardHome.yaml /opt/adguardhome/conf/AdGuardHome.yaml

# Restart container
docker restart adguardhome
```

> ⚠️ **Watch the paths.** `/opt/AdGuardHome/` (capital) is the native install location from the backup. `/opt/adguardhome/conf/` (lowercase) is the Docker volume. They are different directories — easy to conflate.

**Backing up going forward:**

```bash
sudo tar -czvf adguard-backup-$(date +%F).tar.gz /opt/adguardhome/conf/
```

> ⚠️ **`AdGuardHome.yaml` contains your bcrypt admin password hash and client device names.** Do not commit it to a public repo. Add it to `.gitignore` and publish a sanitized `AdGuardHome.example.yaml` instead.

---

## 6. Blocklists

The following blocklists are used in this setup. Add via **Filters → DNS Blocklists → Add blocklist**:

| Name | URL |
|------|-----|
| AdGuard DNS filter | `https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt` |
| Hagezi Pro Plus | `https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/pro.plus.txt` |
| AdGuard SDNS Filter | `https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt` |
| OISD Full | `https://big.oisd.nl` |

Current block rate with this set is roughly **83%** of total queries.

> Overlapping lists are normal — AdGuard deduplicates rules. Stacking Hagezi Pro Plus with OISD Full is aggressive; expect occasional false positives and be ready to whitelist.

---

## 7. Point Your Devices to AdGuard

| Method | How |
|--------|-----|
| Router-level | Change DNS in your router settings to `YOUR_DEVICE_IP` |
| Per-device | Manually set DNS to `YOUR_DEVICE_IP` in network settings |
| Mobile off-network | Route through Tailscale — see [Tailscale Setup](../tailscale/README.md) |

> Router-level is preferred — it covers every device without per-device config. Set a **DHCP reservation** for the Orange Pi first, or a changed IP silently breaks DNS for the whole network.

---

## 8. Close Port 3000 (Optional Hardening)

The setup wizard port is no longer needed once initial configuration is done.

```bash
docker stop adguardhome && docker rm adguardhome
```

Then re-run the command from Step 2 **without** the `-p 3000:3000/tcp` line. Config persists in `/opt/adguardhome/conf/`.

Drop the matching UFW rule if you added one:

```bash
sudo ufw status numbered
sudo ufw delete <number>
```

---

## ✅ Verify It's Working

```bash
# Check container is running
docker ps

# Check AdGuard logs
docker logs adguardhome

# Test DNS resolution
dig @YOUR_DEVICE_IP google.com
```

Expected — `status: NOERROR` with an answer section:

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 23634
;; ANSWER SECTION:
google.com.		23	IN	A	142.250.198.46
;; SERVER: 192.168.18.28#53(192.168.18.28) (UDP)
```

Test that blocking works — a known ad domain should return `0.0.0.0` or NXDOMAIN:

```bash
dig @YOUR_DEVICE_IP doubleclick.net
```

Access the dashboard at `http://YOUR_DEVICE_IP`

> `dig` is in the `dnsutils` package, not installed by default on Armbian minimal — `sudo apt install dnsutils -y`.

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Container stuck in `Created` | Port 53 conflict | Disable `systemd-resolved` (Step 1) |
| Can't reach `:3000` after wizard | AdGuard moved to port 80 | Access `http://YOUR_DEVICE_IP` instead |
| Can't reach `:80` | Port 80 not mapped | Recreate container with `-p 80:80/tcp` |
| `exec format error` | Wrong architecture image | Verify `linux/arm/v7` support on Docker Hub |
| DNS works on Pi but not other devices | UFW blocking UDP 53 | `sudo ufw allow from YOUR_SUBNET to any port 53` |
| Upstream test fails | Bootstrap DNS not set | Add `1.1.1.1` under Bootstrap DNS servers |
| Whole network loses DNS | Container down or IP changed | `docker ps`, verify DHCP reservation |
| `nslookup: command not found` | `dnsutils` not installed | `sudo apt install dnsutils -y`, use `dig` |

---

## 📝 Notes

| Note | Details |
|------|---------|
| Why Docker | Config persists in `/opt/adguardhome/` — survives OS reflashes, one command to restore |
| Data to back up | `/opt/adguardhome/conf/AdGuardHome.yaml` — contains all settings, blocklists, and client config |
| Secrets | Config holds a bcrypt admin hash and device names — never commit it |
| UFW caveat | Docker publishes ports via `DOCKER-USER`, bypassing UFW — see [Docker guide](../docker/README.md) |
| Single point of failure | If this container is down, the whole network loses DNS. Uptime Kuma monitors it for this reason |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [Tailscale Setup](../tailscale/README.md) | VPN exit node — extends DNS filtering to mobile |
| [Uptime Kuma Setup](../uptime-kuma/README.md) | Monitor this container's health |
| [UFW Setup](../ufw/README.md) | Host firewall configuration |