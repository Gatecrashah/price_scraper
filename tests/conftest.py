"""Shared fixtures for price monitoring tests."""

import pytest


@pytest.fixture
def sample_bjornborg_product():
    """Sample Björn Borg product data."""
    return {
        "name": "Essential Socks 10-pack",
        "url": "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/",
        "purchase_url": "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/",
        "current_price": 35.96,
        "original_price": 44.95,
        "discount_percent": 20,
        "sku": "10004564_MP001",
        "base_product_code": "10004564",
        "product_id": "10004564",
        "site": "bjornborg",
        "brand": "BJÖRN BORG",
        "in_stock": True,
    }


@pytest.fixture
def sample_bjornborg_apparel():
    """Sample Björn Borg apparel product (no base_product_code)."""
    return {
        "name": "Centre Crew Sweatshirt",
        "url": "https://www.bjornborg.com/fi/centre-crew-9999-1431-gy013/",
        "purchase_url": "https://www.bjornborg.com/fi/centre-crew-9999-1431-gy013/",
        "current_price": 79.95,
        "product_id": "centre-crew-9999-1431-gy013",
        "site": "bjornborg",
        "brand": "BJÖRN BORG",
        "in_stock": True,
    }


@pytest.fixture
def sample_fitnesstukku_product():
    """Sample Fitnesstukku product data."""
    return {
        "name": "Whey-80 4 kg",
        "url": "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html",
        "purchase_url": "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html",
        "current_price": 89.90,
        "product_id": "fitnesstukku_5854R",
        "site": "fitnesstukku",
        "brand": "Star Nutrition",
        "category": "Proteiinit",
        "in_stock": True,
        "currency": "EUR",
    }


@pytest.fixture
def sample_price_history():
    """Sample price history data structure."""
    return {
        "base_10004564": {
            "name": "Essential Socks 10-pack",
            "purchase_url": "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/",
            "price_history": {
                "2025-01-01": {
                    "current_price": 44.95,
                    "original_price": 44.95,
                    "discount_percent": 0,
                    "scraped_at": "2025-01-01T09:00:00",
                },
                "2025-01-02": {
                    "current_price": 35.96,
                    "original_price": 44.95,
                    "discount_percent": 20,
                    "scraped_at": "2025-01-02T09:00:00",
                },
            },
        },
        "id_fitnesstukku_5854R": {
            "name": "Whey-80 4 kg",
            "purchase_url": "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html",
            "price_history": {
                "2025-01-01": {
                    "current_price": 99.90,
                    "original_price": None,
                    "discount_percent": None,
                    "scraped_at": "2025-01-01T09:00:00",
                },
                "2025-01-02": {
                    "current_price": 89.90,
                    "original_price": 99.90,
                    "discount_percent": 10,
                    "scraped_at": "2025-01-02T09:00:00",
                },
            },
        },
    }


@pytest.fixture
def sample_products_config():
    """Sample products.yaml configuration."""
    return {
        "products": {
            "bjornborg": [
                {
                    "name": "Essential Socks 10-pack (Multi)",
                    "url": "/fi/essential-socks-10-pack-10004564-mp001/",
                    "product_id": "10004564",
                    "site": "bjornborg",
                    "category": "socks",
                    "status": "track",
                },
                {
                    "name": "Essential Socks 5-pack",
                    "url": "/fi/essential-socks-5-pack-10003419-mp001/",
                    "product_id": "10003419",
                    "site": "bjornborg",
                    "category": "socks",
                    "status": "ignore",
                },
            ],
            "fitnesstukku": [
                {
                    "name": "Whey-80 Protein 4kg",
                    "url": "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html",
                    "product_id": "5854R",
                    "site": "fitnesstukku",
                    "category": "supplements",
                    "status": "track",
                },
            ],
        },
        "sites": {
            "bjornborg": {
                "base_url": "https://www.bjornborg.com",
                "name": "Björn Borg",
            },
            "fitnesstukku": {
                "base_url": "https://www.fitnesstukku.fi",
                "name": "Fitnesstukku",
            },
        },
    }


@pytest.fixture
def bjornborg_json_ld_html():
    """Sample Björn Borg product page HTML with JSON-LD."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Essential Socks 10-pack | Björn Borg</title>
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Essential Socks 10-pack",
            "sku": "10004564_MP001",
            "brand": {"@type": "Brand", "name": "BJÖRN BORG"},
            "offers": {
                "@type": "Offer",
                "price": "35.96",
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        }
        </script>
    </head>
    <body>
        <div class="product-price">35.96 EUR44.95 EUR-20%</div>
    </body>
    </html>
    """


@pytest.fixture
def fitnesstukku_tracking_html():
    """Sample Fitnesstukku product page HTML with dataTrackingView."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Whey-80 4 kg - Fitnesstukku</title>
        <script>
        var view = [{"event":"productDetail","ecommerce":{"detail":{"products":[{"name":"Whey-80 4 kg","id":"590-1","price":"89.90","brand":"Star Nutrition","category":"Proteiinit","variant":"Suklaa","availability":"IN STOCK","isOnSale":"false","isPartOfBundle":"false"}]}}}];
        </script>
    </head>
    <body>
        <h1 class="product-name">Whey-80 4 kg</h1>
    </body>
    </html>
    """
