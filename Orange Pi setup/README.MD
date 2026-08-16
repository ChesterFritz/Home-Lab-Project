# 🍊 Orange Pi PC (H3) — Initial Setup

From picking an OS to first SSH contact.

> **Board naming:** This board is an **Orange Pi PC**, not an Orange Pi
> One. Mine shipped mislabeled. Check the silkscreen on the PCB before
> flashing — the wrong image won't boot, or boots with broken hardware
> support.

> **Why Armbian?** The official Orange Pi Ubuntu image is EOL and has
> unreliable Docker support. Armbian ships a maintained kernel with
> proper cgroup v2 config, which is what Docker needs on the H3.

## 1. Pick an image

**Used here:**
`Armbian_community_26.2.0-trunk.703_Orangepipc_trixie_current_6.18.21_minimal.img`

| | |
|---|---|
| Build | Armbian Community `26.2.0-trunk.703` |
| Board | Orange Pi PC (`Orangepipc`) |
| Base | Debian Trixie |
| Kernel | `6.18.21` (current) |
| Variant | Minimal — no GUI |

Download from [armbian.com/orange-pi-pc](https://www.armbian.com/orange-pi-pc/).

> ⚠️ `-trunk` builds are nightly and can break. If you want stability,
> grab a stable release instead. Pin the exact filename you used —
> "latest" is not reproducible.

**Minimal over Desktop** — headless, no GUI overhead, managed entirely
over SSH. On 1 GB of RAM you don't want a desktop competing with your
containers.

## 2. Flash

Need a MicroSD card — **SanDisk High Endurance 64 GB** or similar.
Standard cards die fast under constant server writes.

Flash with [Balena Etcher](https://etcher.balena.io):

1. Select the `.img`
2. Select the SD card
3. Flash, then wait for validation to finish

## 3. First boot

Insert the card, plug in ethernet, then power. It boots headless — no
monitor needed. Give it about 60 seconds.

## 4. Find the IP

**Via router** — log into your router admin page, find the DHCP client
list, look for `orangepipc`. Note the IP **and** MAC.

**If your router is ISP-locked** and you can't see the client list, scan
the subnet from another machine:

```bash
nmap -sn 192.168.1.0/24
```

Or on macOS without nmap:

```bash
arp -a | grep -i "02:"
```

> 💡 Set a **DHCP reservation** using the MAC so the IP never changes.
> Once AdGuard is your DNS server, a changed IP breaks resolution for
> every device on the network.

## 5. First SSH

```bash
ssh root@YOUR_PI_IP
```

Armbian defaults — user `root`, password `1234`.

## 6. Armbian first-run wizard

Armbian forces initial config on first login. You can't skip it.

**Change the root password.** Prompted immediately:

```text
You are required to change your password immediately (administrator enforced)
New password:
Retype new password:
```

**Create a non-root user.** Next prompt:

```text
Creating a new user account. Press <Ctrl-C> to abort
Please provide a username (eg. your first name): chester
Create password:
Repeat password:
```

It'll then ask for full name, timezone, and locale — all optional, just
hit Enter to skip.

> Day-to-day work happens as the non-root user; escalate with `sudo`
> only when needed. Armbian enforces this by prompting on first boot.

## 7. Update

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

First run takes a while. SSH back in as your user:

```bash
ssh YOUR_USER@YOUR_PI_IP
```

## 8. SSH keys + disable password auth

Do this before exposing anything. From your **local machine**:

```bash
ssh-keygen -t ed25519 -C "orangepi"
ssh-copy-id YOUR_USER@YOUR_PI_IP
```

Confirm key auth works, then on the **Pi**:

```bash
sudo nano /etc/ssh/sshd_config
```

Set:

```text
PasswordAuthentication no
PermitRootLogin no
```

Reload:

```bash
sudo systemctl restart ssh
```

> ⚠️ Keep your current session open and test a new one before closing.
> Locking yourself out means pulling the SD card.

## ⏭️ Next

| Guide | |
|---|---|
| [AdGuard Home](../configs/adguard/README.md) | Network-wide DNS filtering |
| [Tailscale](../configs/tailscale/README.md) | VPN exit node |
| [Docker](../configs/docker/README.md) | Container runtime |
| [Fail2ban](../configs/fail2ban/README.md) | SSH brute-force protection |