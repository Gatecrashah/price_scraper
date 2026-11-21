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
  clients their bot check dislikes. From CI they accept GitHub's `setup-python` build
  but reject uv's own Python downloads, so `price-monitor.yml` must keep
  `actions/setup-python` and `UV_PYTHON_PREFERENCE: only-system`. Locally they answer
  429 to any Python, so a local dry run shows them as failing.
- A product's `id` in `products.yaml` is its key in `price_history.json`. Renaming it
  starts a new history.
