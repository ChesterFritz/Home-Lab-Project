# 🔒 Tailscale — Setup Guide

Step-by-step instructions to replicate this Tailscale setup on a new machine.

---

## Why Tailscale

My ISP does not allow port forwarding, which makes traditional VPN setups like
WireGuard or OpenVPN impossible to self-host directly. Tailscale works around this
using NAT traversal — it creates an encrypted peer-to-peer tunnel between devices
without requiring any open ports on the router.

This setup uses the Orange Pi One H3 as a **Tailscale exit node**, routing all
mobile traffic through the home network and extending AdGuard Home DNS filtering
to devices outside the house.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi One H3, Ubuntu 20.04) |
| Access | Root or sudo |
| Account | Free Tailscale account at [tailscale.com](https://tailscale.com) |
| DNS | AdGuard Home installed and running — see [AdGuard Setup Guide](../adguard/README.md) |

---

## 1. Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

---

## 2. Authenticate

```bash
sudo tailscale up
```

This will output an authentication URL — open it in a browser and log in with
Google or GitHub to authorize the device. Once authenticated your machine will
appear in the Tailscale admin panel.

---

## 3. Enable IPv4 and IPv6 Forwarding

Required for exit node functionality. Open the sysctl config:

```bash
sudo nano /etc/sysctl.conf
```

Uncomment or add these two lines:

```
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
```

Apply the changes:

```bash
sudo sysctl -p
```

> **Note:** Skipping this step will cause a warning when advertising the exit
> node and subnet routes may not work correctly.

---

## 4. Advertise as Exit Node

```bash
sudo tailscale up --advertise-exit-node
```

---

## 5. Approve the Exit Node in Tailscale Admin

1. Go to [login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines)
2. Find your machine in the list
3. Click the **three dots menu → Edit route settings**
4. Enable **Use as exit node** and click Save

---

## 6. Enable on Your iPhone

1. Open the Tailscale app
2. Tap on your machine name
3. Select **Use as exit node**

All traffic will now route through your home network with AdGuard filtering applied.

---

## ✅ Verify It's Working

Browse to `ifconfig.me` on mobile data — it should show your home public IP
instead of your mobile carrier's IP.

You can also SSH into the Pi remotely using the Tailscale IP:

```bash
ssh root@YOUR_TAILSCALE_IP
```

The Tailscale IP is visible in the admin panel under your machine name.

---

## 📝 Notes

| Note | Details |
|------|---------|
| Cost | Free for personal use (up to 100 devices) |
| Ports | No ports need to be opened on your router |
| SSH | Works over Tailscale without additional configuration |
| Stability | Connection persists across network changes (WiFi → mobile data) |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [AdGuard Home Setup](../adguard/README.md) | Network-wide DNS filtering |