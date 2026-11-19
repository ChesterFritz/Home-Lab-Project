# 🔒 Tailscale — Setup Guide (Armbian Debian Trixie)

Step-by-step instructions to replicate this Tailscale setup on Armbian Debian Trixie.

---

## Why Tailscale

My ISP does not allow port forwarding, which makes traditional VPN setups like
WireGuard or OpenVPN impossible to self-host directly. Tailscale works around this
using NAT traversal — it creates an encrypted peer-to-peer tunnel between devices
without requiring any open ports on the router.

This setup uses the Orange Pi PC H3 as a **Tailscale exit node**, routing all
mobile traffic through the home network and extending AdGuard Home DNS filtering
to devices outside the house.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Account | Free Tailscale account at [tailscale.com](https://tailscale.com) |
| DNS | AdGuard Home installed and running — see [AdGuard Docker Setup Guide](../adguard/README.md) |

---

## 1. Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

---

## 2. Enable IPv4 and IPv6 Forwarding

Required for exit node functionality. Write a drop-in file:

```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

> **Why not `/etc/sysctl.conf`?** Debian Trixie no longer reads
> `/etc/sysctl.conf` at boot — only `/etc/sysctl.d/*.conf`. Lines in
> `sysctl.conf` still apply with `sysctl -p`, but are silently lost on reboot, and the exit
> node stops routing.

Confirm both read `1`:

```bash
sysctl net.ipv4.ip_forward net.ipv6.conf.all.forwarding
```

> If UFW is enabled, its forward policy must also be `ACCEPT` — see the
> [UFW guide](../ufw/README.md#3-allow-forwarding-for-the-tailscale-exit-node).

> **Note:** Skipping this step will cause a warning when advertising the exit node and subnet routes may not work correctly.

---

## 3. Authenticate and Advertise as Exit Node

```bash
sudo tailscale up --advertise-exit-node
```

This will output an authentication URL — open it in a browser and log in to authorize the device. Once authenticated your machine will appear in the Tailscale admin panel.

---

## 4. Approve the Exit Node in Tailscale Admin

1. Go to [login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines)
2. Find your machine in the list
3. Click the **three dots menu → Edit route settings**
4. Enable **Use as exit node** and click Save

---

## 5. Point the Tailnet at AdGuard

The exit node routes traffic, but DNS filtering only applies if tailnet
clients actually query AdGuard.

1. Go to [login.tailscale.com/admin/dns](https://login.tailscale.com/admin/dns)
2. **Nameservers → Add nameserver → Custom** — enter the Orange Pi's Tailscale IP (`tailscale ip -4`)
3. Enable **Override local DNS**

On the Pi itself, stop Tailscale from rewriting `/etc/resolv.conf` (it
would otherwise loop the Pi's own lookups back through MagicDNS):

```bash
sudo tailscale set --accept-dns=false
```

> AdGuard must accept queries arriving on `tailscale0` — it does by
> default when bound to `0.0.0.0`. Don't restrict port 53 to the LAN IP.

---

## 6. Enable on Your iPhone

1. Open the Tailscale app
2. Tap on your machine name
3. Select **Use as exit node**

All traffic will now route through your home network with AdGuard filtering applied.

---

## ✅ Verify It's Working

Browse to `ifconfig.me` on mobile data — it should show your home public IP instead of your mobile carrier's IP.

Then visit a known ad domain (e.g. `doubleclick.net`) — it should fail to load, and the query should appear in the AdGuard query log from the phone's Tailscale IP.

You can also SSH into the Pi remotely using the Tailscale IP:

```bash
ssh YOUR_USER@YOUR_TAILSCALE_IP
```

Check Tailscale status:

```bash
tailscale status
tailscale ip
```

The Tailscale IP is visible in the admin panel and via `tailscale ip` on the device.

---

## 📝 Notes

| Note | Details |
|------|---------|
| Cost | Free for personal use (up to 100 devices) |
| Ports | No ports need to be opened on your router |
| SSH | Works over Tailscale without additional configuration |
| Stability | Connection persists across network changes (WiFi → mobile data) |
| OS | Tested on Armbian Debian Trixie — replaces previous Ubuntu 20.04 setup |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [AdGuard Docker Setup](../adguard/README.md) | Network-wide DNS filtering via Docker |
| [UFW Setup](../ufw/README.md) | Firewall — keep forwarding allowed for the exit node |