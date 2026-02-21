# Development Guide

## Code Changes and Container Rebuilds

### Short Answer

✅ **Agent code changes**: NO rebuild needed - files are mounted as volumes
✅ **Microservice code changes**: Rebuild required
✅ **Dependency changes**: Rebuild required

### How It Works

The agent container **mounts your source code as volumes**, so changes are reflected immediately:

```bash
# These are mounted in run-agent.sh:
-v "${SCRIPT_DIR}/main.py:/app/main.py:ro"
-v "${SCRIPT_DIR}/localdeamon:/app/localdeamon:ro"
-v "${SCRIPT_DIR}/spellbook:/app/spellbook:ro"
-v "${SCRIPT_DIR}/tools:/app/tools:ro"
```

This means:
- Edit `main.py` → Run immediately ✅
- Edit `localdeamon/deamon.py` → Run immediately ✅
- Edit `spellbook/SYSTEM.md` → Run immediately ✅
- Edit `requirements.txt` → **Rebuild required** ⚠️

---

## When Rebuilds Are Required

| Change Type | Agent | Scraper | Search | Command |
|-------------|-------|---------|--------|---------|
| **Code files** | ❌ No rebuild | ✅ Rebuild | ✅ Rebuild | `docker compose build scraper` |
| **requirements.txt** | ✅ Rebuild | ✅ Rebuild | ✅ Rebuild | `make build` |
| **Dockerfile** | ✅ Rebuild | ✅ Rebuild | ✅ Rebuild | `make build` |
| **.env changes** | ❌ No rebuild | ❌ No rebuild | ❌ No rebuild | Just restart services |

### Rebuild Commands

```bash
# Agent only (after requirements.txt change)
docker build -t local-daemon-agent:latest -f Dockerfile .
# or
make rebuild-agent

# Microservices (after code or requirements change)
docker compose build scraper
docker compose restart scraper

# Everything (nuclear option)
make rebuild
```

---

## Development Workflows

### Workflow 1: Agent Development (Instant Changes)

```bash
# 1. Start services once
./docker-start.sh

# 2. Edit code
vim localdeamon/deamon.py

# 3. Run immediately - NO rebuild needed!
./run-agent.sh "test task"

# 4. Edit more, run again - still no rebuild!
vim localdeamon/context.py
./run-agent.sh "another test"
```

**Execution time**: ~1-2 seconds overhead (no build step!)

### Workflow 2: Microservice Development

When working on scraper or search services:

```bash
# 1. Start services
docker compose up -d

# 2. Edit microservice code
vim services/scraper/scraper.py

# 3. Rebuild specific service
docker compose build scraper
docker compose restart scraper

# 4. Test
curl "http://localhost:8000/fetch_content?url=https://example.com"
```

### Workflow 3: Native Development (Even Faster)

For maximum speed, run agent natively:

```bash
# 1. Start microservices with Docker
docker compose up -d

# 2. Run agent natively
source .venv/bin/activate
python main.py "test task"

# Edit and run - instant!
```

---

## First-Time Setup

### Initial Build

On first run, `./docker-start.sh` or `./run-agent.sh` will build images:

```bash
# Option 1: Quick start (builds everything)
./docker-start.sh

# Option 2: Manual build
make build

# Option 3: Build components separately
docker compose build              # Microservices
docker build -t local-daemon-agent:latest -f Dockerfile .  # Agent
```

This only happens **once** (or when dependencies change).

---

## Why Volume Mounts Are Better

### Before (Rebuild Every Time)
```bash
./run-agent.sh "test"
# 1. Rebuild Docker image (2-5s)
# 2. Run container
# Total: ~3-7 seconds overhead
```

### After (Volume Mounts)
```bash
./run-agent.sh "test"
# 1. Run container with mounted files
# Total: ~1-2 seconds overhead
```

**Speed improvement**: 2-5x faster! 🚀

### Trade-offs

**Volume Mounts (Current Approach):**
- ✅ Instant code changes
- ✅ Fast development iteration
- ✅ No cache invalidation issues
- ⚠️ Requires image to be built once
- ⚠️ Files mounted read-only (security)

**Rebuild Every Time (Old Approach):**
- ❌ 2-5 second overhead per run
- ❌ Slower development
- ✅ Exact production parity
- ✅ No volume mount complexity

---

## When Dependencies Change

If you add/update dependencies in `requirements.txt`:

```bash
# 1. Rebuild agent image
docker build -t local-daemon-agent:latest -f Dockerfile .

# 2. Rebuild microservices (if their deps changed too)
docker compose build

# 3. Restart services
docker compose up -d

# Or use make
make rebuild
```

The agent container needs to reinstall dependencies since they're baked into the image, not mounted.

---

## Debugging

### Verify Volume Mounts

Check that files are being mounted:

```bash
# Inspect running container
docker run --rm -it \
    -v "$(pwd)/main.py:/app/main.py:ro" \
    -v "$(pwd)/localdeamon:/app/localdeamon:ro" \
    local-daemon-agent:latest bash

# Inside container
ls -la /app/
cat /app/main.py
```

### Test Code Changes

```bash
# 1. Edit a file
echo "# TEST CHANGE" >> main.py

# 2. Run immediately
./run-agent.sh "test"

# 3. Check logs - should reflect change
tail -f logs/agent_*.log

# 4. Revert change
git checkout main.py
```

### Force Image Rebuild

If something seems cached incorrectly:

```bash
# Nuclear option - rebuild from scratch
docker rmi local-daemon-agent:latest
docker build --no-cache -t local-daemon-agent:latest -f Dockerfile .
```

---

## Live Reload for Microservices

You can enable auto-reload for faster microservice development:

### 1. Enable in .env
```bash
SCRAPER_RELOAD=true
SEARCH_RELOAD=true
```

### 2. Mount Code as Volumes

Edit `docker-compose.yml`:
```yaml
services:
  scraper:
    volumes:
      - ./logs:/app/logs
      - ./services/scraper/scraper.py:/app/scraper.py  # Add this

  search:
    volumes:
      - ./logs:/app/logs
      - ./services/search:/app  # Mount entire directory
```

### 3. Restart Services
```bash
docker compose down
docker compose up -d
```

Now services auto-reload when you edit code! No rebuild or restart needed.

---

## Performance Comparison

### Agent Execution (Volume Mounts)

```bash
time ./run-agent.sh "What is 2 + 2?"

# Results:
# Container startup: ~1s
# Agent execution: varies (LLM dependent)
# Total overhead: ~1-2s
```

### Native Execution (Fastest)

```bash
source .venv/bin/activate
time python main.py "What is 2 + 2?"

# Results:
# Import time: ~0.1s
# Agent execution: varies (LLM dependent)
# Total overhead: ~0.1s
```

**For rapid iteration**: Use native Python
**For production testing**: Use Docker with volume mounts

---

## Common Issues

### "Module not found" After Dependency Change

**Cause**: Requirements installed in image, but image not rebuilt
**Solution**:
```bash
docker build -t local-daemon-agent:latest -f Dockerfile .
```

### Changes Not Reflected

**Cause**: Volume mount not working or wrong file edited
**Solution**: Verify mount paths in `run-agent.sh`:
```bash
-v "${SCRIPT_DIR}/localdeamon:/app/localdeamon:ro"
```

### Services Using Old Code

**Cause**: Microservices don't use volume mounts by default
**Solution**: Rebuild and restart
```bash
docker compose build scraper
docker compose restart scraper
```

### File Permission Issues

**Cause**: Container user vs host user mismatch
**Solution**: Volumes are mounted read-only (`:ro`), so container can't write
```bash
# If you need write access, remove :ro
-v "${SCRIPT_DIR}/localdeamon:/app/localdeamon"  # Read-write
```

---

## Production Deployment

For production, you want **immutable images** without volume mounts:

### Build Production Image

```bash
# Build with code baked in
docker build -t local-daemon-agent:prod -f Dockerfile .

# Run without volume mounts
docker run --rm \
    --network local-daemon_agent-network \
    --env-file .env \
    local-daemon-agent:prod "task"
```

This ensures:
- ✅ Exact version deployed
- ✅ No host filesystem dependency
- ✅ Immutable deployments
- ✅ Easier to version and rollback

---

## Summary

**Current Setup (Volume Mounts):**
```bash
./docker-start.sh    # Build once
./run-agent.sh "x"   # Run instantly
vim localdeamon/x.py # Edit code
./run-agent.sh "y"   # Run instantly - no rebuild! 🚀
```

**When to Rebuild:**
- ✅ Changed `requirements.txt`
- ✅ Changed `Dockerfile`
- ✅ Want production-ready immutable image

**When NOT to Rebuild:**
- ❌ Changed `.py` files (mounted as volumes)
- ❌ Changed `.md` files in spellbook (mounted as volumes)
- ❌ Changed `.sh` files in tools (mounted as volumes)

This approach gives you **instant feedback** during development while maintaining the option for **immutable production deployments**.
