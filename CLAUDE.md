# Price Monitor

Daily price monitor run by GitHub Actions. See README.md for the file overview,
config format and history format.

## Commands

- Dry run (scrape and print only): `uv run python monitor.py --dry-run`
- Tests: `uv run pytest`
- Lint and format: `uv run ruff check .` and `uv run ruff format .`

## Constraints

- `price_history.json` is committed by the workflow every day. Don't commit local
  changes to it; a local non-dry run rewrites it.
- The pharmacy Shopify stores (apteekki360, sinunapteekki, ruohonjuuri) answer 429 to
  some networks, so a local dry run may show them as failing while CI reads them fine.
- A product's `id` in `products.yaml` is its key in `price_history.json`. Renaming it
  starts a new history.
