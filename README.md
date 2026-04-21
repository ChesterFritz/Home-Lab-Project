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
| DNS | AdGuard Home → Cloudflare (1.1.1.1) / Quad9 (9.9.9.9) |
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
---
## 🎯 Goals
- Build hands-on experience with Linux, networking, and self-hosted infrastructure
- Document configurations and lessons learned for future reference
- Progressively expand services as hardware allows
- Build a foundation relevant to GRC and cybersecurity work (NIST, ISO 27001, IEC 62443)
---
## 📝 A Note on Documentation
Configuration guides and documentation in this repo were written with the assistance
of an LLM (Claude by Anthropic) for clarity and structure. All setup steps reflect
my actual hands-on experience building and troubleshooting this lab.