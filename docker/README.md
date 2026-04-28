# Docker Infrastructure

## Containers Running on This Machine

### 1. `postgres-pgvector` (pg18 — existing)
- **Image**: `pgvector/pgvector:pg18`
- **Port**: `localhost:5432`
- **Extensions**: pgvector
- **Purpose**: Primary Postgres instance

### 2. `pgvector-age` (pg16 + Apache AGE)
- **Image**: `pgvector-age:pg16` (custom, built from `Dockerfile.pgvector-age`)
- **Port**: `localhost:5433`
- **Volume**: `pgdata-age`
- **Extensions**: pgvector 0.8.2, Apache AGE 1.5.0
- **Credentials**: user `postgres`, password `postgres`

**Why pg16?** Apache AGE 1.5.0 is incompatible with pg18. The pgvector base image for pg16 was the cleanest path — compiling AGE on top of the pgvector image works, whereas starting from the apache/age image and adding pgvector fights with the Debian package sources.

## Rebuilding the pgvector-age Image

If you ever need to rebuild (new machine, lost image, etc.):

```bash
# 1. Download the AGE source tarball into this directory
curl -L -o docker/age-PG16-v1.5.0-rc0.tar.gz \
  https://github.com/apache/age/archive/refs/tags/PG16/v1.5.0-rc0.tar.gz

# 2. Build the image
docker build -f docker/Dockerfile.pgvector-age -t pgvector-age:pg16 docker/

# 3. Run the container (port 5433 to avoid conflict with pg18 on 5432)
docker run --name pgvector-age -d \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  -v pgdata-age:/var/lib/postgresql/data \
  pgvector-age:pg16

# 4. Enable extensions (once per database)
docker exec pgvector-age psql -U postgres -d YOUR_DB -c \
  "CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS age;"
```

## AGE Per-Connection Setup

Apache AGE requires these statements **every connection**, not just once per DB:

```sql
LOAD 'age';
SET search_path = ag_catalog, public;
```

**In DBeaver**: Edit Connection > **Connection Settings** > **Initialization** > **Bootstrap queries**. Click **Add** and enter:

```
LOAD 'age' | SET search_path = ag_catalog, public
```

DBeaver uses `|` as the statement separator in bootstrap queries (not `;`).

## Quick Reference Commands

```bash
# Check running containers
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"

# Stop/start the AGE container
docker stop pgvector-age
docker start pgvector-age

# Connect via psql from inside the container
docker exec -it pgvector-age psql -U postgres

# Check installed extensions
docker exec pgvector-age psql -U postgres -c \
  "SELECT extname, extversion FROM pg_extension;"
```
