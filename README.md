# 🏠 Home Lab
A personal home lab built on a single-board computer — used to self-host services,
explore networking concepts, and document my progress in systems and infrastructure.
---
## 🖥️ Hardware
| Component | Details |
|-----------|---------|
| Board | Orange Pi PC H3 |
| RAM | 1GB DDR3 |
| OS | Armbian Debian Trixie Minimal |
| Storage | MicroSD (SanDisk High Endurance) |

📖 [Orange Pi Initial Setup Guide](docs/orange-pi-setup.md)

---
## 🧰 Current Stack
| Service | Purpose | Status | Docs |
|---------|---------|--------|------|
| Docker | Container runtime | ✅ Running | [Setup Guide](configs/docker/README.md) |
| AdGuard Home | Network-wide DNS filtering (~83% block rate) | ✅ Running (Docker) | [Setup Guide](configs/adguard/README.md) |
| Tailscale | VPN exit node — extends DNS filtering to mobile | ✅ Running | [Setup Guide](configs/tailscale/README.md) |

---
## 🌐 Network
| Layer | Details |
|-------|---------|
| DNS | AdGuard Home → Cloudflare DoH / Quad9 DoH / Google DoH |
| VPN | Tailscale NAT traversal — no port forwarding required |

---
## 🗺️ Roadmap
| Status | Task |
|--------|------|
| ✅ | Orange Pi initial setup |
| ✅ | AdGuard Home — network-wide ad/tracker blocking |
| ✅ | Tailscale — VPN exit node with DNS filtering on mobile |
| ✅ | Docker — container runtime |
| ✅ | Migrate AdGuard Home to Docker |
| ✅ | DNS-over-HTTPS (DoH) upstream configuration |
| ⏳ | UFW firewall |
| ⏳ | CrowdSec — intrusion detection |
| ⏳ | Nginx reverse proxy — clean local URLs |
| ⏳ | Expand to dedicated server (OptiPlex 3070) |

---
## 📋 Current State
AdGuard Home is running as a Docker container with config and data persisted via
volumes at `/opt/adguardhome/`. Tailscale runs natively on the host — this is
intentional, as exit node functionality requires direct access to the host network
stack that is easier to manage outside of a container.

Docker was chosen for AdGuard Home specifically for easier recovery after OS
reflashes and cleaner config backups.

AdGuard Home is configured with DNS-over-HTTPS upstreams (Cloudflare, Quad9, Google),
meaning DNS queries leaving the Orange Pi are encrypted and not visible to the ISP.

---
## 📅 Project Timeline

### Phase 1 — Initial Setup
- Purchased Orange Pi PC H3 from Lazada (listed as "Orange Pi One" — board was mislabeled)
- Flashed official Orange Pi Ubuntu 20.04 image — EOL and unstable
- Identified correct board model physically (Orange Pi PC, not One)

### Phase 2 — First Stack (Native)
- Installed AdGuard Home natively on Ubuntu 20.04
- Installed Tailscale natively and configured as exit node
- Confirmed DNS filtering and VPN working on mobile

### Phase 3 — OS Migration
- Reflashed to Armbian Debian Trixie Minimal (correct image for Orange Pi PC)
- Backed up AdGuard config before reflash via `scp`
- Disabled `systemd-resolved` to free port 53
- Restored AdGuard config after reflash

### Phase 4 — Docker Migration
- Installed Docker CE on Armbian Trixie using the official Debian repository
- Deployed AdGuard Home in Docker with persistent volumes
- Restored config from backup — credentials and blocklists intact
- Kept Tailscale native (intentional — exit node requires host networking)

### Phase 5 — Hardening & Privacy
- Configured DoH upstreams in AdGuard (Cloudflare, Quad9, Google)
- Verified DNS routing on all devices
- Identified and assessed CVE-2026-31431 exposure

### Phase 6 — Planned
- UFW firewall
- CrowdSec intrusion detection
- Nginx reverse proxy
- Dell OptiPlex 3070 hardware expansion

---
## 🎯 Goals
- Build hands-on experience with Linux, networking, and self-hosted infrastructure
- Document configurations and lessons learned for future reference
- Progressively expand services as hardware allows

---
## 📝 A Note on Documentation
Configuration guides and documentation in this repo were written with the assistance
of an LLM (Claude by Anthropic) for clarity and structure. All setup steps reflect
my actual hands-on experience building and troubleshooting this lab.