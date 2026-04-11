# Orange Pi One H3 — Initial Setup Guide

Step-by-step instructions from selecting an OS to establishing first SSH contact.


## 1. Choose an Operating System

Two main options for the Orange Pi One H3:

| OS | Description | Recommended For |
|----|-------------|-----------------|
| [Orange Pi OS](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-PC.html) | Official OS from Orange Pi | Beginners, straightforward setup |
| [Armbian](https://www.armbian.com) | Community-driven, more lightweight | Advanced users, better long-term support |

> This guide uses the **official Orange Pi Ubuntu image**. Steps may vary slightly
> for Armbian.

### Desktop vs Server

When downloading the official OS you will be given two options:

| Version | Description | Use Case |
|---------|-------------|----------|
| Desktop | Includes a full GUI | If you need a monitor and mouse |
| Server | Headless, CLI only | ✅ Recommended for home lab use |

> This guide uses the **Server version**. It is lighter on resources, has no
> unnecessary GUI overhead, and is managed entirely over SSH — ideal for a
> 1GB RAM board like the Orange Pi One H3.


## 2. Flash the SD Card

**What you need:**
- MicroSD card (recommended: SanDisk High Endurance 64GB)
- [Balena Etcher](https://etcher.balena.io) or the official Armbian Flasher

**Steps:**
1. Download the OS image from the Orange Pi website
2. Open Balena Etcher
3. Select the downloaded image
4. Select your SD card as the target
5. Click **Flash** and wait for it to complete

> **Note:** Use a high endurance SD card. Standard cards degrade quickly under
> the constant read/write load of a server workload.


## 3. First Boot

1. Insert the flashed SD card into the Orange Pi
2. Connect an ethernet cable from the Orange Pi to your router
3. Plug in the power supply

The Orange Pi will boot automatically — no monitor needed.


## 4. Find the IP Address

1. Open a browser and go to your router admin page (`192.168.x.x` — check the
   label on your router for the exact address)
2. Log in and navigate to the connected devices or DHCP client list
3. Look for a device named `orangepipc` — note the IP and MAC address

> **Tip:** Note the MAC address and set a DHCP reservation in your router so the
> Orange Pi always gets the same IP. This is important for DNS and SSH stability.


## 5. First SSH Connection

From your Mac or any machine on the same network:

```bash
ssh root@YOUR_ORANGE_PI_IP
```

Default credentials for the official Orange Pi OS:

| Field | Value |
|-------|-------|
| Username | `root` |
| Password | `orangepi` |


## 6. Change the Default Password

The official OS does not prompt you to change the password on first login — do it
manually immediately:

```bash
passwd
```

Enter your current password (`orangepi`), then set a new strong password.

> **Security note:** Never leave the default password on any networked device.


## 7. Update the System

```bash
sudo apt update && sudo apt upgrade -y
```

This may take a few minutes on first run. Reboot after upgrading:

```bash
sudo reboot
```

After reboot, SSH back in and your Orange Pi is ready for use.


## Next Steps

- [AdGuard Home Setup](../configs/adguard/README.md)
- [Tailscale Setup](../configs/tailscale/README.md)