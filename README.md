# Life Manager

KI-gestütztes persönliches Life-Management-System. Self-hosted auf Proxmox, Telegram als primäres Interface.

## Stack

- **Orchestrierung:** n8n
- **Backend:** Python FastAPI
- **Config-UI:** Baserow
- **Vector-DB:** Qdrant
- **Datenbank:** PostgreSQL 16
- **Cache:** Redis 7
- **Messaging:** Telegram Bot

## Setup

```bash
cp .env.example .env
# Edit .env with your actual values
docker compose up -d --build
```

## Endpoints

- **API:** http://localhost:8000 (Docs: http://localhost:8000/docs)
- **Baserow:** http://localhost:8080
- **Qdrant:** http://localhost:6333

## Deployment

```bash
ssh martin@10.10.10.211 'cd /opt/docker/life-manager && bash scripts/deploy.sh'
```
