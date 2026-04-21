# 🍊 Orange Pi One H3 — Initial Setup Guide
Step-by-step instructions from selecting an OS to establishing first SSH contact.
> **Note:** This setup previously used the official Orange Pi Ubuntu image, which is now EOL. This guide has been updated to use **Armbian** instead. The switch was driven primarily by **Docker support** — Armbian provides a maintained kernel and proper cgroup configuration that makes running Docker reliable on the H3.
---
## 1. Choose an Operating System
This setup uses **Armbian** — a community-driven, lightweight OS with better long-term support than the official Orange Pi OS (which is now end-of-life).
**Image used:** `Armbian_community_26.2.0-trunk.703_Orangepipc_trixie_current_6.18.21_minimal.img`
| Detail | Value |
|--------|-------|
| Build | Armbian Community `26.2.0-trunk.703` |
| Board | Orange Pi PC (`Orangepipc`) |
| Base OS | Debian Trixie |
| Kernel | `6.18.21` (current branch) |
| Variant | Minimal (no GUI) |
Download Armbian images from the [Armbian download page](https://www.armbian.com/orange-pi-pc/).
> **Why Armbian?** The official Orange Pi OS is no longer maintained and lacks reliable Docker support. Armbian offers active development, a large community, proper cgroup v2 support for Docker, and better hardware support for the H3 chip long-term.
### Desktop vs Minimal
| Version | Description | Use Case |
|---------|-------------|----------|
| Desktop | Includes a full GUI | If you need a monitor and mouse |
| Minimal | Headless, CLI only | ✅ Recommended for home lab use |
> This guide uses the **Minimal variant**. It is lighter on resources, has no unnecessary GUI overhead, and is managed entirely over SSH — ideal for a 1GB RAM board like the Orange Pi One H3.
---
## 2. Flash the SD Card
**What you need:**
- MicroSD card (recommended: SanDisk High Endurance 64GB)
- [Balena Etcher](https://etcher.balena.io) or the official Armbian Flasher
**Steps:**
1. Download the Armbian image from the Armbian website
2. Open Balena Etcher
3. Select the downloaded `.img` file
4. Select your SD card as the target
5. Click **Flash** and wait for it to complete
> **Note:** Use a high endurance SD card. Standard cards degrade quickly under the constant read/write load of a server workload.
---
## 3. First Boot
1. Insert the flashed SD card into the Orange Pi
2. Connect an ethernet cable from the Orange Pi to your router
3. Plug in the power supply
The Orange Pi will boot automatically — no monitor needed.
---
## 4. Find the IP Address
1. Open a browser and go to your router admin page (`192.168.x.x` — check the label on your router for the exact address)
2. Log in and navigate to the connected devices or DHCP client list
3. Look for a device named `orangepipc` — note the IP and MAC address
> **Tip:** Note the MAC address and set a DHCP reservation in your router so the Orange Pi always gets the same IP. This is important for DNS and SSH stability.
---
## 5. First SSH Connection
From your Mac or any machine on the same network:
```bash
ssh root@YOUR_ORANGE_PI_IP
```
Default credentials for Armbian:
| Field | Value |
|-------|-------|
| Username | `root` |
| Password | `1234` |
---
## 6. First Login — Armbian Setup Wizard
Unlike the official Orange Pi OS, **Armbian will walk you through initial configuration on first login.** You cannot skip this.
### Step 1 — Change the root password
You will be prompted immediately:
Set a strong password and remember it.
### Step 2 — Create a non-root user
Armbian will then ask you to create a regular user account:
Enter a username (e.g. `pi` or your own name), then set a password for this user.
> **Why a non-root user?** It is best practice to do day-to-day work as a non-root user and only escalate with `sudo` when needed. Armbian enforces this by prompting you to create one on first boot.
After this the setup wizard completes and you will be dropped into a shell.
---
## 7. Update the System
```bash
sudo apt update && sudo apt upgrade -y
```
This may take a few minutes on first run. Reboot after upgrading:
```bash
sudo reboot
```
After reboot, SSH back in with your non-root user:
```bash
ssh YOUR_USERNAME@YOUR_ORANGE_PI_IP
```
Your Orange Pi is now ready for use.
---
## ⏭️ Next Steps
| Guide | Description |
|-------|-------------|
| [AdGuard Home Setup](../configs/adguard/README.md) | Network-wide DNS filtering |
| [Tailscale Setup](../configs/tailscale/README.md) | VPN exit node setup |