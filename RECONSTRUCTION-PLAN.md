# Reconstruction Plan

## First Principles

**What this app does:** Check if gaming streamers are live. Generate briefings. That's it.

**What it pretends to do:** 4-agent distributed system with LLM intent classification, Prometheus metrics, 3 cache layers, resource optimization, connection pooling, rate limiting, concurrency control.

**Ratio:** 19,000 lines of code → ~500 lines of actual product logic → 38:1 bloat ratio.

## What Gets Cut

| Component | Lines | Why Cut |
|-----------|-------|---------|
| `router_agent.py` | 1052 | 4-agent routing is fake distribution. Replace with 20-line intent function. |
| `briefing_agent.py` | 1210 | Multi-agent collaboration is calling functions in the same process. |
| `data_source_agent.py` | 883 | Wraps a simple API call in 883 lines of abstraction. |
| `data_source_agent_cached.py` | 253 | Duplicate of above with cache bolted on. |
| `main.py` | 378 | 4-agent orchestrator. |
| `main_enhanced.py` | 142 | Duplicate main with different cache. |
| `llm_client.py` | 537 | LLM intent classification for 7 regex patterns. |
| `error_handler.py` | 538 | Recovery managers, cooldowns, severity enums for a demo. |
| `performance_metrics.py` | 570 | Prometheus metrics for a single-user demo. |
| `cache_optimizer.py` | 503 | 3 cache layers (LRU, Query, DataSource) for mock data. |
| `resource_optimizer.py` | 417 | psutil monitoring, connection pools, rate limiters for a demo. |
| `server_config.py` | 43 | Merged into app.py. |
| `router_enhanced.py` | 212 | Dead code (imports non-existent functions). |
| `studio_helper.py` | 438 | Help text generator. Merged into app.py. |
| `response_formatter.py` | 362 | Emoji formatter. Merged into app.py. |
| `common.py` | 510 | Performance monitor, detailed logger, pydantic models. Keep minimal utils. |
| `huya_api.py` | 160 | Not actually used (mock data is used). Cut. |
| `twitch_api.py` | 340 | Not actually used (mock data is used). Cut. |
| `data_sources.py` | 576 | Abstraction layer over mock data. Cut. |
| `tests/` (13 files) | ~2000+ | Test the old architecture. Cut. |
| `docs/` (19 files) | ~3000+ | Documentation of the old architecture. Cut. |
| `scripts/` (3 files) | ~200 | Setup scripts for old architecture. Cut. |
| Various root files | ~1000 | Deploy scripts, verify scripts, reports. Cut. |

## What Gets Built (~310 lines, 5 files)

### `app.py` (~120 lines)
- Gradio web UI
- Simple intent detection (regex, 15 lines)
- Query routing to data functions
- Health check endpoint
- Entry point

### `data.py` (~100 lines)
- Mock streamer data (from existing mock_data.py, trimmed)
- `get_live_streams(game=None, streamer=None)` → list of dicts
- `get_streamer_status(name)` → single streamer dict
- No classes, no abstractions, just functions

### `config.py` (~30 lines)
- Load players.yaml
- Load .env
- Simple dict access

### `requirements.txt` (~8 lines)
- Only what's actually needed: gradio, aiohttp, pyyaml, python-dotenv, loguru

### `Dockerfile` (~15 lines)
- Slim, minimal, copies only what exists

## Files Kept As-Is

- `config/players.yaml` - real config data
- `.env.example` - env template
- `.gitignore`
- `README.md` - will be trimmed

## Execution Order

1. Create `src/data.py` (mock data + fetch functions)
2. Create `src/config.py` (config loader)
3. Create `src/app.py` (web UI + intent routing)
4. Update `requirements.txt`
5. Update `Dockerfile`
6. Delete all old source files
7. Delete tests/, docs/, scripts/, root clutter
8. Update README.md
9. Git commit
