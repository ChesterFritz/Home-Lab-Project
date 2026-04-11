# 🏠 Home Lab

A personal home lab built on a single-board computer — used to self-host services,
explore networking concepts, and document my progress in systems and infrastructure.


## Hardware

| Component | Details |
|-----------|---------|
| Board | Orange Pi One H3 |
| RAM | 1GB |
| OS | Ubuntu 20.04 LTS (Focal Fossa) |
| Storage | MicroSD (SanDisk High Endurance) |

📖 [Orange Pi Initial Setup Guide](docs/orange-pi-setup.md)

## Current Stack

| Service | Purpose | Status | Docs |
|---------|---------|--------|------|
| AdGuard Home | Network-wide DNS filtering (~83% block rate) | ✅ Running | [Setup Guide](configs/adguard/README.md) |
| Tailscale | VPN exit node — extends DNS filtering to mobile | ✅ Running | [Setup Guide](configs/tailscale/README.md) |
| Docker | Container runtime for future services | 🔧 In Progress | — |


## Network

- **DNS:** AdGuard Home → Cloudflare (1.1.1.1) / Quad9 (9.9.9.9) upstream
- **VPN:** Tailscale NAT traversal for remote access


## Roadmap

- [x] AdGuard Home — network-wide ad/tracker blocking
- [x] Tailscale — VPN exit node with DNS filtering on mobile
- [ ] Docker — container orchestration
- [ ] Self-hosted dashboard
- [ ] Vaultwarden — self-hosted password manager

## Current Plan

AdGuard Home and Tailscale are currently running as native installs directly on the
host. The next step is migrating both services into Docker containers for easier
management and portability.

## Goals

- Build hands-on experience with Linux, networking, and self-hosted infrastructure
- Document configurations and lessons learned for future reference
- Progressively expand services as hardware allows


## A Note on Documentation

Configuration guides and documentation in this repo were written with the assistance
of an LLM (Claude by Anthropic) for clarity and structure. All setup steps reflect
my actual hands-on experience building and troubleshooting this lab.