# Price Monitor

Checks a handful of product pages once a day and emails when a price changes.

- A product has one or more store URLs. Its price is the lowest **in-stock** price across them.
- An email goes out when that price moves (up or down), and once when a URL starts failing.
- Every price or stock change per store is appended to `price_history.json`.

## Files

| File | Purpose |
| --- | --- |
| `products.yaml` | What to track: `id`, `name`, `urls` |
| `monitor.py` | Scrape, compare with history, save, send the alert |
| `scraper.py` | Read price, list price and stock from a page |
| `emails.py` | Alert email (HTML) and delivery through Resend |
| `price_history.json` | State and change log, committed by the workflow |

## Adding a product

Add an entry to `products.yaml`:

```yaml
- id: some-stable-id        # key in price_history.json
  name: Shown in the email
  urls:
    - https://store-a.example/product
    - https://store-b.example/product   # optional: same product elsewhere
```

A page works if it has a schema.org `Product` JSON-LD block (most stores do) or
Fitnesstukku's `var view = [...]` analytics block. Check with a dry run.

## Running

```bash
uv run python monitor.py --dry-run   # scrape and print, no save, no email
RESEND_API_KEY=... EMAIL_TO=... uv run python monitor.py
uv run pytest
uv run ruff check . && uv run ruff format .
```

## Automation

`.github/workflows/price-monitor.yml` runs daily at 9:00 UTC and commits
`price_history.json` when it changed. It needs the `RESEND_API_KEY` and `EMAIL_TO`
secrets. If the email cannot be sent the run fails and nothing is committed, so the
next run detects and reports the same change again.

## History format

```json
{
  "base_10005071": {
    "name": "Essential Socks 10-pack (Variant 3)",
    "stores": {
      "bjornborg": {"url": "...", "price": 35.96, "original_price": 44.95, "available": true, "error": null}
    },
    "current_lowest": {"price": 35.96, "store": "bjornborg", "url": "...", "date": "2026-08-05"},
    "all_time_lowest": {"price": 31.47, "store": "bjornborg", "url": "...", "date": "2025-11-25"},
    "price_changes": [
      {"date": "2025-07-23", "store": "bjornborg", "price": 44.95, "original_price": null, "available": true}
    ]
  }
}
```

The store name is the URL's host without `www.` and the TLD. `current_lowest` keeps the
last known value while nothing is in stock. `price_changes` holds the state after each change.
