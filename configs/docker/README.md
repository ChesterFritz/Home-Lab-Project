# 🐳 Docker — Setup Guide

Step-by-step instructions to install Docker CE on Armbian Debian Trixie (Orange Pi PC H3).

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Architecture | armhf (arm/v7) — confirmed via `uname -m` returning `armv7l` |

---

## ⚠️ Architecture Note

The Orange Pi PC H3 is a **32-bit ARMv7 board (armhf)**. Docker Engine installs and runs fine on armhf, but not all container images support this architecture. Always verify that an image has a `linux/arm/v7` build on Docker Hub before deploying.

```bash
# Check your architecture
uname -m                   # should return armv7l
dpkg --print-architecture  # should return armhf
```

> This rules out a surprising number of popular self-hosted images. Check
> the **Tags** tab on Docker Hub and look for `linux/arm/v7` in the OS/ARCH
> column before committing to a service.

---

## 1. Free Up Port 53

If you plan to run AdGuard Home or any DNS service, disable `systemd-resolved` first. It binds to port 53 by default and will block any container that needs it.

```bash
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf
```

> **Note:** Skip this step if you are not running any DNS containers.

> ⚠️ **If Tailscale is already installed**, MagicDNS will overwrite
> `/etc/resolv.conf` again. See the [Fail2ban guide](../fail2ban/README.md)
> for the full fix — short version is `sudo tailscale set --accept-dns=false`
> then `sudo chattr +i /etc/resolv.conf` to lock the file.

---

## 2. Remove Conflicting Packages

Remove any unofficial Docker packages that may conflict with the official Docker CE repository:

```bash
sudo apt remove docker.io docker-compose docker-doc podman-docker containerd runc
```

> It is fine if apt reports these packages are not installed.

---

## 3. Install Prerequisites

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
```

---

## 4. Add Docker's GPG Key

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

> **Why:** The GPG key authenticates packages from Docker's official repository, ensuring nothing has been tampered with in transit. This is the reason to use the official repo rather than `curl | sh` — the install script works, but skipping signature verification defeats the point.

---

## 5. Add Docker Repository

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

> `dpkg --print-architecture` auto-detects `armhf` and `VERSION_CODENAME` resolves to `trixie` — the correct repository is added automatically.

---

## 6. Install Docker Engine

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Confirm it starts on boot:

```bash
sudo systemctl enable --now docker
sudo systemctl status docker
```

---

## 7. Verify Installation

```bash
sudo docker run hello-world
```

Expected output includes `Hello from Docker!` and `(arm32v7)` — confirming Docker is running and correctly detected the armhf architecture.

---

## 8. Run Docker Without sudo (Optional)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

> ⚠️ **This is effectively granting root.** Any user in the `docker` group
> can mount the host filesystem into a privileged container and escalate.
> Acceptable on a single-user homelab; worth documenting as an accepted
> risk rather than an oversight.

---

## ✅ Verify It's Working

```bash
docker ps          # list running containers
docker info        # system-wide Docker info
```

---

## 🔥 Docker and UFW

Docker writes its own nftables rules into the `DOCKER-USER` chain, which **UFW does not manage**. Any container started with `-p 3001:3001` is reachable from outside your allowed subnet regardless of UFW policy.

```bash
# See Docker's own rules
sudo nft list chain inet filter DOCKER-USER 2>/dev/null || \
  sudo iptables -L DOCKER-USER -n
```

To actually restrict a container port, bind it to a specific interface instead of relying on the firewall:

```bash
# Reachable from anywhere
-p 3001:3001

# Reachable only from the LAN interface
-p 192.168.18.28:3001:3001

# Reachable only from localhost
-p 127.0.0.1:3001:3001
```

> Acceptable in this lab because nothing is port-forwarded at the router.
> Worth knowing before assuming UFW covers container traffic — this is a
> common and quiet misconfiguration.

See the [UFW guide](../ufw/README.md) for the full firewall setup.

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `docker: command not found` | Install failed | Re-run Step 6, check apt output for errors |
| `exec format error` | Wrong architecture image | Find a `linux/arm/v7` tag on Docker Hub |
| `permission denied` | User not in docker group | Run Step 8 then `newgrp docker` |
| Container stuck in `Created` | Port conflict (usually 53) | Disable `systemd-resolved` (Step 1) |
| `address already in use` on :53 | `systemd-resolved` came back | `sudo ss -ulpn \| grep :53` to identify the holder |
| Service won't start | Missing kernel feature | Run the moby check-config script |
| Container port open despite UFW | Docker bypasses UFW | Bind to a specific interface — see above |

---

## 📚 Lessons Learned

### Why Docker Matters — The "It Works on My Machine" Problem

Before this setup, services like AdGuard Home were installed directly on the host OS. This works, but it ties the service tightly to that specific machine, OS version, and configuration. If the OS gets reflashed, corrupted, or upgraded, the service has to be reinstalled and reconfigured from scratch.

Docker solves this by packaging a service and everything it needs — binaries, dependencies, config — into a container that runs the same way regardless of what machine it is on. The same `docker run` command that deployed AdGuard Home on this Orange Pi would deploy the exact same setup on a Raspberry Pi, a cloud VPS, or a Dell OptiPlex without any changes.

This is the core value of containerization — eliminating environment-specific failures. A container does not care what OS version the host is running or what other software is installed. It brings its own environment with it.

| Without Docker | With Docker |
|----------------|-------------|
| Reinstall and reconfigure after every OS reflash | `docker run` restores the service in one command |
| Dependencies tied to host OS version | Dependencies packaged inside the container |
| Works on this machine, breaks on another | Runs the same everywhere |
| Manual backup of scattered config files | Config persisted in a single volume directory |

This became immediately practical during this setup — after reflashing the Orange Pi from Ubuntu 20.04 to Armbian Debian Trixie, AdGuard Home was back up and running with the full config restored in minutes rather than starting from scratch.

### What Docker Does Not Solve

Worth being honest about the limits:

- **Networking still leaks** — containers punch through UFW via `DOCKER-USER`
- **Socket access is root access** — mounting `/var/run/docker.sock` into a container grants host-level control unless mounted `:ro`
- **Architecture still matters** — a container is portable across hosts of the *same* architecture; armhf images will not run on arm64 or amd64 without a rebuild
- **Volumes are still host state** — the container is disposable, but `/opt/adguardhome` is not. That directory still needs backing up

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [AdGuard Home Docker Setup](../adguard/README.md) | Network-wide DNS filtering via Docker |
| [Uptime Kuma Setup](../uptime-kuma/README.md) | Service and container monitoring |
| [UFW Setup](../ufw/README.md) | Host firewall configuration |
| [Tailscale Setup](../tailscale/README.md) | VPN exit node setup on Armbian |