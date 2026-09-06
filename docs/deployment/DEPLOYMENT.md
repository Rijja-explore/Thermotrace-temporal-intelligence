# ThermoTrace Deployment Guide

## Docker Compose Deployment

```bash
# Build and run containers
docker-compose up --build -d

# Check running status
docker-compose ps

# View backend logs
docker-compose logs -f backend
```

## Environment Configuration (`.env`)

```ini
NODE_ENV=production
PORT=8000
DATABASE_URL=postgresql+asyncpg://thermotrace:thermotrace_pass@localhost:5432/thermotrace_db
POSTGRES_USER=thermotrace
POSTGRES_PASSWORD=thermotrace_pass
POSTGRES_DB=thermotrace_db
```

## Production Verification Health Check

```bash
curl http://localhost:8000/api/health
```

Expected Response:
```json
{
  "status": "ok",
  "service": "thermotrace-api",
  "version": "1.0.0",
  "engine": "thermotrace-temporal-v1.0",
  "model": "M4-B_HistGradientBoosting_v1.0"
}
```
