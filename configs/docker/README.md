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
uname -m               # should return armv7l
dpkg --print-architecture  # should return armhf
```

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

> **Why:** The GPG key authenticates packages from Docker's official repository, ensuring nothing has been tampered with in transit.

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

---

## ✅ Verify It's Working

```bash
docker ps          # list running containers
docker info        # system-wide Docker info
```

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `docker: command not found` | Install failed | Re-run Step 6, check apt output for errors |
| `exec format error` | Wrong architecture image | Find a `linux/arm/v7` tag on Docker Hub |
| `permission denied` | User not in docker group | Run Step 8 then `newgrp docker` |
| Container stuck in `Created` | Port conflict (usually 53) | Disable `systemd-resolved` (Step 1) |
| Service won't start | Missing kernel feature | Run the moby check-config script |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [AdGuard Home Docker Setup](../adguard/README.md) | Network-wide DNS filtering via Docker |
| [Tailscale Setup](../tailscale/README.md) | VPN exit node setup on Armbian |