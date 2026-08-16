# 🧱 UFW — Firewall Setup

Host firewall on Armbian Debian Trixie, configured alongside Fail2ban
and a Tailscale exit node.

## Why

Default-deny inbound with explicit allows for LAN services only. Nothing
is exposed to the internet — the router does no port forwarding, and
remote access goes through Tailscale.

## Prerequisites

| | |
|---|---|
| Access | root or sudo |
| Second SSH session | **Required** — recovery path if you lock yourself out |
| Known subnet | Run `ip -4 addr show` first |

> ⚠️ Enabling UFW before adding an SSH allow rule will drop your session.
> Every `allow` goes in **before** `enable`.

## 1. Audit what's listening

```bash
sudo ss -tulpn | grep LISTEN
```

On this box:

| Port | Service | Binding |
|---|---|---|
| 22 | SSH | native |
| 53 (TCP+UDP) | AdGuard DNS | docker-proxy |
| 80 | AdGuard web UI | docker-proxy |
| 3000 | Speedtest Tracker | docker-proxy |
| 3001 | Uptime Kuma | docker-proxy |

> `ss -tulpn | grep LISTEN` only shows TCP. Check UDP separately with
> `sudo ss -ulpn | grep :53` — DNS clients use UDP.

## 2. Install

```bash
sudo apt update && sudo apt install ufw -y
```

Installing does not enable it. Nothing changes until `ufw enable`.

## 3. Allow forwarding for the Tailscale exit node

```bash
sudo nano /etc/default/ufw
```

```text
DEFAULT_FORWARD_POLICY="ACCEPT"
```

> Exit node functionality routes traffic *through* this host. UFW's
> default `FORWARD` policy is `DROP`, which silently breaks it.

## 4. Add rules

```bash
sudo ufw allow in on tailscale0
sudo ufw allow from 192.168.18.0/24 to any port 22 proto tcp
sudo ufw allow from 192.168.18.0/24 to any port 53
sudo ufw allow from 192.168.18.0/24 to any port 80 proto tcp
sudo ufw allow from 192.168.18.0/24 to any port 3000 proto tcp
sudo ufw allow from 192.168.18.0/24 to any port 3001 proto tcp
```

> Port 53 intentionally omits `proto` so both TCP and UDP are allowed.
> UDP is what clients actually use.

## 5. Set policies and review

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw show added
```

Confirm the SSH rule is present before continuing.

## 6. Enable

```bash
sudo ufw enable
```

## 7. Verify

```bash
sudo ufw status verbose
```

```text
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), allow (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
Anywhere on tailscale0     ALLOW IN    Anywhere
22/tcp                     ALLOW IN    192.168.18.0/24
53                         ALLOW IN    192.168.18.0/24
80/tcp                     ALLOW IN    192.168.18.0/24
3000/tcp                   ALLOW IN    192.168.18.0/24
3001/tcp                   ALLOW IN    192.168.18.0/24
Anywhere (v6) on tailscale0 ALLOW IN    Anywhere (v6)
```

`allow (routed)` confirms the forward policy applied — exit node intact.

**Then test each path:**

```bash
# From another machine on the LAN
ssh fritz@192.168.18.28
dig @192.168.18.28 google.com
```

- AdGuard UI — `http://192.168.18.28`
- Uptime Kuma — `http://192.168.18.28:3001` (all monitors should be green)
- Tailscale — WiFi off on mobile, confirm exit node routing

## ⚠️ Known limitation — Docker bypasses UFW

Containers with published ports write directly to the `DOCKER-USER`
nftables chain, which UFW does not manage. Ports 53, 80, 3000, and 3001
stay reachable from outside the allowed subnet regardless of UFW policy.

The UFW rules for those ports are documentation of intent, not
enforcement. Real restriction requires binding to a specific interface in
compose:

```yaml
ports:
  - "192.168.18.28:3001:3001"
```

Acceptable here because nothing is port-forwarded at the router. Worth
knowing before assuming UFW covers container traffic.

## 🔗 Interaction with Fail2ban

Both write nftables rules, but they don't conflict. Fail2ban's chain runs
at `priority filter - 1`, ahead of UFW's, so bans apply regardless of
firewall policy:

```bash
sudo nft list table inet f2b-table
```

```text
chain f2b-chain {
    type filter hook input priority filter - 1; policy accept;
    tcp dport 22 ip saddr @addr-set-sshd reject with icmp port-unreachable
}
```

## 🛠️ Commands

| | |
|---|---|
| `sudo ufw status verbose` | Current rules and policies |
| `sudo ufw status numbered` | Rules with index numbers |
| `sudo ufw delete <num>` | Remove a rule by index |
| `sudo ufw show added` | Rules as added, before enable |
| `sudo ufw disable` | Turn off — recovery |
| `sudo ufw reload` | Reapply config |

## 🚨 Lockout recovery

1. Use your second SSH session — `sudo ufw disable`
2. If both sessions are dead, pull the SD card, mount it elsewhere, set
   `ENABLED=no` in `/etc/ufw/ufw.conf`

## ⏭️ Next

| | |
|---|---|
| [Nginx reverse proxy](../nginx/README.md) | Clean local URLs |
| [Fail2ban](../fail2ban/README.md) | SSH brute-force protection |