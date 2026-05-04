# DailyFinNews

DailyFinNews is a v1 scaffold for an 8am SGT cross-asset market report.

The current implementation is intentionally conservative:

- RSS, central-bank, Substack, Reddit, and Yahoo Finance chart endpoints are supported.
- Social sources that require brittle scraping, such as X and 小红书, are represented in config but disabled by default.
- Reports are composed deterministically from normalized data so the pipeline can be tested before adding an LLM layer.

## Quick Start

```powershell
python -m pip install -e ".[dev]"
dailyfinnews ingest --config config/sources.yaml --db data/dailyfinnews.sqlite
dailyfinnews report --config config/sources.yaml --db data/dailyfinnews.sqlite --out reports/latest.md
```

If you only want to verify the local scaffold:

```powershell
python -m pytest -q
```

## Product Contract

See [docs/report_spec.md](docs/report_spec.md) for the locked v1 report format.

## v1 Scope

- Market snapshot table for the configured instrument universe.
- Normalized content table: source, timestamp, region, asset class, title, body, URL, language.
- Deduplication by normalized title similarity.
- Report sections: TL;DR, cross-asset table, by asset class, narrative drivers, social pulse, day ahead.
- Major financial press digest for RSS-accessible headlines/excerpts from The Economist, Wall Street Journal, Financial Times, and similar sources.

## Next Hardening Steps

1. Add paid market-data and pro-media adapters behind the same source config schema.
2. Add LLM driver extraction, claim validation, social distillation, and QA passes.
3. Add licensed full-text newspaper ingestion where subscriptions permit it.
4. Add scheduler deployment, email distribution, and one-click section feedback.
