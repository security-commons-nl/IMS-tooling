# Server Access — IMS

## Connection Details

- **IP**: `77.42.66.251`
- **SSH Port**: `2222`
- **Username**: `ims` (sudo, NOPASSWD)
- **SSH Key Path**: `C:\Users\shgst\.ssh\id_ims`
- **SSH Alias**: `ims-admin` (interactive) / `hetzner-ims` (non-interactive)
- **Project Path**: `/opt/IMS`

## Connect

```powershell
# Interactive (drops into /opt/IMS with port forwards)
ssh ims-admin

# Non-interactive (for scripts/commands)
ssh hetzner-ims "docker compose ps"
```

## Deploy

```powershell
ssh hetzner-ims "cd /opt/IMS && git pull origin main && docker-compose up -d --build"
```

## Useful Commands

```powershell
# Service status
ssh hetzner-ims "cd /opt/IMS && docker compose ps"

# API logs
ssh hetzner-ims "cd /opt/IMS && docker compose logs --tail=50 -f ims-api"

# Database shell
ssh hetzner-ims "docker exec -it ims-db psql -U postgres -d ims"

# Apply RLS policies
ssh hetzner-ims "cd /opt/IMS && cat backend/enable_rls.sql | docker exec -i ims-db psql -U postgres -d ims"

# Restart API only
ssh hetzner-ims "cd /opt/IMS && docker compose restart ims-api"
```

## Port Forwards (via `ims-admin`)

| Service | Local Port | Description |
|---------|-----------|-------------|
| IMS API | `8001` | Swagger: http://localhost:8001/docs |
| PostgreSQL | `5432` | `psql -h localhost -p 5432 -U postgres ims` |
| PgAdmin | `5050` | http://localhost:5050 |
| Ollama | `11434` | AI model inference |

## Docker Services

| Service | Container | Port |
|---------|-----------|------|
| Backend API | `ims-api` | `8001` |
| PostgreSQL + pgvector | `ims-db` | `5432` |
| Frontend (Reflex) | `ims-frontend` | `3000` |
| PgAdmin | `ims-pgadmin` | `5050` |
| Ollama | `ims-ollama` | `11434` |

> **Note:** The IMS server shares IP `77.42.66.251` with `bedrijfsvoering-admin` (user `bas`). Use distinct SSH aliases to avoid conflicts.
