# Claude Context for Multi-Site Price Monitoring System

## Project Overview
This is a sophisticated multi-site price monitoring system that tracks product prices across:
- **Björn Borg** (Finnish site): Essential Socks 10-pack variants + Centre Crew sweatshirts
- **Fitnesstukku** (Finnish fitness supplements): Whey protein + Creatine

## Key Architecture Components

### Core Files
- `scrapers/bjornborg.py` - Björn Borg scraper with JSON-LD extraction
- `scrapers/fitnesstukku.py` - Fitnesstukku scraper with dataTrackingView extraction
- `scrapers/base_scraper.py` - Abstract base class for all scrapers
- `price_monitor.py` - Orchestrates monitoring cycle, detects price changes, manages history
- `email_sender.py` - Multi-site HTML email notifications via Resend API
- `email_templates.py` - HTML email templates with editorial aesthetic
- `price_analyzer.py` - Advanced analytics for trend analysis and seasonal patterns
- `price_analysis_reporter.py` - Monthly/quarterly analysis reports

### Configuration
- `products.yaml` - Product URLs and tracking configuration
- `.env` - Contains RESEND_API_KEY and EMAIL_TO (in gitignore)
- `price_history.json` - **CRITICAL: Managed by GitHub Actions, avoid manual commits**
- `ean_price_history.json` - Cross-store EAN price tracking (event-based format)

### EAN Price Monitor (Cross-Store Comparison)
- `ean_price_monitor.py` - Monitors products by EAN across multiple stores
- `ean_products.yaml` - EAN product configuration with store URLs
- `scrapers/shopify_scraper.py` - Scraper for Shopify-based stores (Apteekki360, Sinunapteekki, Ruohonjuuri)
- `scrapers/tokmanni.py` - Tokmanni scraper

### GitHub Actions
- **Daily monitoring**: 9:00 AM UTC - scrapes prices, updates history, sends alerts
- **Monthly analysis**: 1st of month - generates comprehensive trend reports
- **Tests & Linting**: Runs on push/PR - pytest and ruff checks

## Current Product Tracking (12 products)

### Björn Borg (10 tracked)
- Essential Socks 10-pack: 5 variants + 1 ankle variant
- Centre Crew sweatshirt: 3 colors (Grey, Blue, Black)

### Fitnesstukku (2 tracked)
- Whey-80 Protein 4kg
- Creatine Monohydrate 500g

## Important Development Notes

### CRITICAL: Price History Management
- **NEVER commit manual changes to `price_history.json` or `ean_price_history.json`**
- These files are automatically updated by GitHub Actions
- Manual commits can cause merge conflicts with automated updates
- Test locally but only commit code changes, not data changes

### Event-Based Data Structure
Both history files use an **event-based format** that only records price changes (not daily snapshots):

**price_history.json** (single-site tracking):
```json
{
  "base_10004564": {
    "name": "Essential Socks 10-pack",
    "purchase_url": "https://...",
    "current": {
      "price": 31.47,
      "original_price": 44.95,
      "discount_pct": 30,
      "since": "2025-12-25"
    },
    "all_time_lowest": {
      "price": 31.47,
      "date": "2025-11-25",
      "original_price": 44.95
    },
    "price_changes": [
      {"date": "2025-07-04", "price": 35.96, "type": "initial"},
      {"date": "2025-08-05", "from": 35.96, "to": 38.21, "change_pct": 6.3}
    ]
  }
}
```

**ean_price_history.json** (cross-store tracking):
```json
{
  "6430050004729": {
    "name": "Puhdas+ Premium Omega-3",
    "stores": {
      "apteekki360": {"url": "...", "current_price": 28.4, "available": true}
    },
    "current_lowest": {"price": 28.4, "store": "apteekki360", "url": "..."},
    "all_time_lowest": {"price": 28.4, "store": "apteekki360", "date": "2026-01-09"},
    "price_changes": [
      {"date": "2026-01-09", "store": "apteekki360", "price": 28.4, "available": true, "type": "initial"}
    ]
  }
}
```

**Key benefits**: 25x compression, meaningful change tracking, efficient storage

### Key Generation Logic
The `get_product_key()` method delegates to scraper-specific logic:
- **Björn Borg**: `base_product_code` → `base_XXXXX` (groups sock variants)
- **Fitnesstukku**: `product_id` → `id_fitnesstukku_XXXXX`
- **Fallback**: `product_id` → `id_XXXXX` or `url` → `url_XXXXX`

### Testing Environment
- Use `uv run python3 <script>` for running scripts
- Environment variables needed: `RESEND_API_KEY` and `EMAIL_TO`
- Run tests: `uv run pytest`
- Run linting: `uv run ruff check .`
- Run formatting: `uv run ruff format .`

## Common Commands

### Run full monitoring cycle
```bash
RESEND_API_KEY="..." EMAIL_TO="..." uv run python3 price_monitor.py
```

### Run tests
```bash
uv run pytest
uv run pytest --cov=. --cov-report=term-missing
```

### Run linting and formatting
```bash
uv run ruff check .
uv run ruff format .
```

### Test price analyzer
```bash
uv run python3 price_analyzer.py
```

### Generate analysis report
```bash
RESEND_API_KEY="..." EMAIL_TO="..." uv run python3 price_analysis_reporter.py
```

### Run EAN price monitor
```bash
RESEND_API_KEY="..." EMAIL_TO="..." uv run python3 ean_price_monitor.py
```

### Migrate price history (if needed)
```bash
uv run python3 migrate_price_history.py
```

## System Health
- **Automation**: Daily GitHub Actions working
- **Multi-site scraping**: All tracked products successful
- **Email notifications**: Multi-site HTML templates
- **Analysis reports**: Advanced analytics with PriceAnalyzer
- **Data quality**: Clean, unique product tracking
- **Testing**: pytest with core functionality coverage
- **Linting**: Ruff for formatting and code quality

## Future Expansion
To add new sites:
1. Create new scraper class in `scrapers/` (follow FitnesstukkuScraper pattern)
2. Add products to `products.yaml` under new site key
3. Update `price_monitor.py` to import and use new scraper
4. Update email templates for new site section
5. Add tests for new scraper

## Security Notes
- API keys stored in `.env` (gitignored)
- Never commit sensitive credentials
- Use environment variables for API access
