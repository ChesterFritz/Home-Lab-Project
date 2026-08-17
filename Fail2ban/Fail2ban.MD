# 🔐 Fail2ban — SSH Brute-Force Protection

Setup on Armbian Debian Trixie, Orange Pi PC (H3).

## Why

Network trust should never be assumed. Fail2ban watches SSH auth logs and
bans IPs that fail repeatedly — a zero trust baseline that applies even
before anything is publicly exposed. Pairs with key-only SSH auth as
defense in depth.

## Prerequisites

| | |
|---|---|
| Hardware | Linux SBC or server — tested on Orange Pi PC (H3), Armbian Trixie |
| Access | root or sudo |
| DNS | Must resolve before install — see below |

> ⚠️ **Tailscale MagicDNS conflict.** If MagicDNS is active, `apt install`
> fails with `Device or resource busy` because `/etc/resolv.conf` is
> locked. Fix first:
>
> ```bash
> sudo tailscale set --accept-dns=false
> sudo chattr -i /etc/resolv.conf
> sudo rm /etc/resolv.conf
> printf "nameserver 1.1.1.1\nnameserver 8.8.8.8\n" | sudo tee /etc/resolv.conf
> sudo chattr +i /etc/resolv.conf
> ```
>
> `chattr +i` makes the file immutable so Tailscale can't overwrite it
> again. Remember this if you need to change DNS later — `chattr -i`
> first.

## 1. Install

```bash
sudo apt update
sudo apt install fail2ban -y
```

## 2. Configure the SSH jail

Never edit `jail.conf` — it's overwritten on package updates. Use
`jail.local`:

```bash
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8 ::1 192.168.18.0/24 100.64.0.0/10 172.17.0.0/16 172.18.0.0/16

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
```

| Setting | Meaning |
|---|---|
| `bantime` | Banned IPs blocked for 1 hour |
| `findtime` | Failure counting window — 10 minutes |
| `maxretry` | 5 failures in the window triggers a ban |
| `ignoreip` | Never ban these — loopback, LAN, Tailscale CGNAT, Docker bridges |

> ⚠️ **Set `ignoreip` to your actual ranges.** `100.64.0.0/10` covers the
> whole Tailscale CGNAT range — keep it or you can ban yourself out of
> remote access. `172.17.0.0/16` and `172.18.0.0/16` are the Docker
> bridges, so container health checks can't trip the jail.

> Armbian on H3 names the ethernet interface `end0`, not `eth0`. Run
> `ip -4 addr show` to get your real subnet before setting `ignoreip`.

> Fail2ban 1.1.0 deprecates `backend = %(sshd_backend)s` — omit it. The
> systemd journal backend is used automatically.

Save with `Ctrl+O` → `Enter` → `Ctrl+X`.

## 3. Restart and confirm

```bash
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
sudo fail2ban-client status sshd
```

```text
Status for the jail: sshd
|- Filter
|  |- Currently failed: 0
|  |- Total failed:     0
|  `- Journal matches:  _SYSTEMD_UNIT=ssh.service + _COMM=sshd
`- Actions
   |- Currently banned: 0
   |- Total banned:     0
   `- Banned IP list:
```

Confirm `ignoreip` loaded:

```bash
sudo fail2ban-client get sshd ignoreip
```

## 4. Verify the ban path

Service running ≠ jail working. Confirm the backend:

```bash
sudo fail2ban-client get sshd actions
```

```text
The jail sshd has the following actions:
nftables
```

Force a ban on a test IP:

```bash
sudo fail2ban-client set sshd banip 203.0.113.42
sudo nft list table inet f2b-table
```

```text
table inet f2b-table {
	set addr-set-sshd {
		type ipv4_addr
		elements = { 203.0.113.42 }
	}

	chain f2b-chain {
		type filter hook input priority filter - 1; policy accept;
		tcp dport 22 ip saddr @addr-set-sshd reject with icmp port-unreachable
	}
}
```

Clean up and confirm the set drains:

```bash
sudo fail2ban-client set sshd unbanip 203.0.113.42
sudo nft list table inet f2b-table
```

`elements` should be gone.

> **Note:** `ignoreip` only filters bans triggered by log matches. Manual
> bans via `set banip` bypass it by design — a manual ban on a whitelisted
> IP will succeed. To verify `ignoreip` is active, use
> `fail2ban-client get sshd ignoreip` rather than trying to ban a LAN
> address.

## 🔗 Interaction with UFW

Both write nftables rules, but they don't conflict. Fail2ban's chain runs
at `priority filter - 1` — ahead of UFW's — so bans apply regardless of
firewall policy or state.

## 🛠️ Commands

| | |
|---|---|
| `sudo fail2ban-client status` | List all jails |
| `sudo fail2ban-client status sshd` | Jail detail + banned IPs |
| `sudo fail2ban-client get sshd ignoreip` | Confirm whitelist |
| `sudo fail2ban-client set sshd unbanip <IP>` | Unban |
| `sudo fail2ban-client banned` | All banned IPs across jails |
| `sudo journalctl -u fail2ban -f` | Follow logs live |
| `sudo fail2ban-client reload` | Apply config without restart |
| `sudo nft list table inet f2b-table` | Inspect active nftables rules |

## 📝 Notes

- **Config** — always `jail.local`, never `jail.conf`
- **RAM** — ~11 MB, negligible on a 1 GB board
- **Native, not Docker** — host-level security tooling needs direct access
  to journal logs and nftables; containerizing adds failure modes for no
  benefit
- **Persistence** — bans clear on service restart by default. Add
  `dbpurgeage = 7d` to `[DEFAULT]` to retain ban history
- **Not a substitute for keys** — Fail2ban slows brute force, key-only
  auth prevents it. Run both

## Optional — recidive jail

Bans repeat offenders for much longer. Add to `jail.local`:

```ini
[recidive]
enabled  = true
logpath  = /var/log/fail2ban.log
bantime  = 1w
findtime = 1d
maxretry = 3
```

Three separate bans within a day earns a one week ban. Mostly useful once
something is internet-facing.

## ⏭️ Next

| | |
|---|---|
| [UFW](../ufw/README.md) | Host firewall |
| [Docker](../docker/README.md) | Container runtime |
| [Tailscale](../tailscale/README.md) | VPN exit node |
| [AdGuard Home](../adguard/README.md) | DNS filtering |