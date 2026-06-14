# 小游探 — YouGame Explorer

Gaming stream assistant. Check if streamers are live, get briefings, see trends.

## Quick Start

```bash
pip install -r requirements.txt
python src/app.py
```

Open http://localhost:7860

## Docker

```bash
docker compose up --build
```

## Project Structure

```
src/
  app.py      # Web UI + intent routing (~120 lines)
  data.py     # Mock streamer data (~90 lines)
  config.py   # Config loader (~30 lines)
config/
  players.yaml
```

## What Changed

This is a first-principles reconstruction. The original ~19,000-line codebase (4-agent architecture, LLM intent classification, 3 cache layers, Prometheus metrics, resource optimizer) was rebuilt in ~310 lines.

The entire product logic — intent detection, live status queries, briefing generation, trending topics — works the same. The infrastructure overhead was removed.

## Environment

```
PORT=7860                    # Server port
OPENAGENTS_HOST=0.0.0.0     # Server host
```

## License

MIT
