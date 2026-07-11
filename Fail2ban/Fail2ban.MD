# 🔐 Fail2ban — Setup Guide

Step-by-step instructions to replicate this Fail2ban setup on Armbian Debian Trixie.

---

## Why Fail2ban

Even on a private network, SSH should be hardened — network trust should never be assumed. This is a zero trust baseline. Fail2ban watches SSH login attempts and automatically bans IPs that fail too many times, adding a layer of protection even before any public exposure.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| DNS | Ensure system DNS is resolving correctly before installing — see note below |

> **Note:** If Tailscale MagicDNS is active and conflicting with system DNS, `apt install` will fail with `Device or resource busy`. Fix it first:
> ```bash
> sudo tailscale set --accept-dns=false
> sudo chattr -i /etc/resolv.conf
> sudo rm /etc/resolv.conf
> echo "nameserver 1.1.1.1
> nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
> sudo chattr +i /etc/resolv.conf
> ```

---

## 1. Install Fail2ban

```bash
sudo apt update
sudo apt install fail2ban -y
```

---

## 2. Configure SSH Jail

Create a local jail config — never edit the default `jail.conf` directly as it gets overwritten on updates:

```bash
sudo nano /etc/fail2ban/jail.local
```

Add the following:

```ini
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
```

> **What this means:**
> - `bantime = 1h` — banned IPs are blocked for 1 hour
> - `findtime = 10m` — failure window is 10 minutes
> - `maxretry = 5` — 5 failed attempts within the window triggers a ban

Save with `Ctrl+X → Y → Enter`.

---

## 3. Restart and Verify

```bash
sudo systemctl restart fail2ban
```

Check the SSH jail is active:

```bash
sudo fail2ban-client status sshd
```

Expected output:

```
Status for the jail: sshd
|- Filter
|  |- Currently failed:  0
|  |- Total failed:      0
|  `- Journal matches:   _SYSTEMD_UNIT=ssh.service + _COMM=sshd
`- Actions
   |- Currently banned:  0
   |- Total banned:      0
   `- Banned IP list:
```

---

## ✅ Verify It's Working

```bash
sudo systemctl status fail2ban
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

---

## 🛠️ Useful Commands

| Command | Description |
|---------|-------------|
| `sudo fail2ban-client status sshd` | Check SSH jail status and banned IPs |
| `sudo fail2ban-client unban <IP>` | Manually unban an IP |
| `sudo fail2ban-client banned` | List all currently banned IPs |
| `sudo journalctl -u fail2ban` | View Fail2ban logs |

---

## 📝 Notes

| Note | Details |
|------|---------|
| Config file | Always use `jail.local` — never edit `jail.conf` |
| Zero trust | SSH is hardened even on a private network — never assume network safety |
| RAM usage | ~11MB — negligible impact on a 1GB board |
| Runs natively | No Docker needed — simpler and more reliable for a host-level security tool |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [Docker Setup](../docker/README.md) | Container runtime |
| [Tailscale Setup](../tailscale/README.md) | VPN exit node setup on Armbian |