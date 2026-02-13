# Life Manager – Projektkontext für Claude Code

## Projekt-Übersicht

KI-gestütztes persönliches Life-Management-System. Self-hosted auf Proxmox, Telegram als primäres Interface.

## Repository-Struktur

- **Projekt-Repo:** `/Users/martinmueller/Development/life-manager/`
- **Server-Dokumentation inkl. SSH-Zugriff:** `/Users/martinmueller/Development/server_config/`

## Infrastruktur

### Proxmox-Host

- **CPU:** Intel i5-13500, 64 GB RAM
- **Storage:** 2x 477 GB NVMe RAID-1, LVM Thinpool (leicht überbucht 410/400 GB)
- **SSH:** Direkter SSH-Zugriff auf Host und alle VMs (kein MCP, kein Jump-Host)

### Haupt-VM: VM 211 (xubuntu-services) – VLAN 10 (Infrastructure)

- **IP:** 10.10.10.211
- **Ressourcen:** 8 GB RAM (6,7 GB frei), 4 Kerne, 34 GB Disk frei
- **Laufende Services:** n8n (Docker), PostgreSQL (2x), Redis, Watchtower
- **Rolle:** Hosting aller Life-Manager-Services (n8n, FastAPI, Baserow, Qdrant, PostgreSQL)

### Reverse Proxy: VM 200 (ubuntu-nginx) – VLAN 10

- **IP:** 10.10.10.200
- **Nginx:** 7 bestehende Proxy-Einträge, Wildcard-SSL (Let's Encrypt)
- **Achtung:** Nur 4,2 GB Disk frei – keine großen Logs/Dateien hier

## Technologie-Stack

- **Orchestrierung:** n8n (Docker auf VM 211)
- **Backend:** Python FastAPI
- **Config-UI:** Baserow (Docker)
- **Vector-DB:** Qdrant (Docker)
- **Datenbank:** PostgreSQL (Docker, bereits vorhanden)
- **Messaging:** Telegram Bot (neuer Bot, NICHT @aura7coach_bot)
- **LLM:** API-Calls (Claude Sonnet, Gemini Flash, Whisper) – keine lokalen Modelle

## Sicherheitsregeln

- **Life Manager Bot hat KEINEN SSH-Zugriff** – nur API-Kommunikation
- **Nur Claude Code hat SSH-Zugriff** auf Proxmox/VMs
- **API-Keys:** In n8n Credential Store oder Docker Environment Variables
- **Keine Secrets in Git** – .env Dateien sind in .gitignore

## Entwicklungs-Workflow

1. Specs werden in Claude.ai (Opus) erarbeitet
2. Claude Code implementiert via SSH auf VM 211
3. Martin reviewt, testet, entscheidet
4. Jedes Feature wird einzeln reviewed vor Implementierung

## Konventionen

- Docker Compose Stacks unter `/opt/docker/life-manager/` auf VM 211
- Logs unter `/var/log/life-manager/`
- Alle Services als Docker Container (kein bare-metal install)
- Python-Code folgt PEP 8, Type Hints, FastAPI Best Practices
- Git: Feature Branches, Merge to main nach Review
