"""Tests for the EAN Price Monitor and Shopify/Tokmanni scrapers."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from scrapers.shopify_scraper import (
    Apteekki360Scraper,
    RuohonjuuriScraper,
    ShopifyScraper,
    SinunapteekkiScraper,
)
from scrapers.tokmanni import TokmanniScraper


class TestShopifyScraper:
    """Test cases for ShopifyScraper base class."""

    @pytest.fixture
    def scraper(self):
        """Create a ShopifyScraper instance."""
        return ShopifyScraper("https://test-store.fi", "test_store")

    @pytest.fixture
    def shopify_json_ld_html(self):
        """Sample Shopify product page HTML with JSON-LD."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Product | Test Store</title>
            <script type="application/ld+json">
            {
                "@type": "Product",
                "name": "Test Omega-3 180 kaps",
                "sku": "TEST-123",
                "offers": {
                    "@type": "Offer",
                    "price": "28.40",
                    "priceCurrency": "EUR",
                    "availability": "https://schema.org/InStock",
                    "gtin13": "6430050004729"
                }
            }
            </script>
        </head>
        <body>
            <h1 class="product__title">Test Omega-3 180 kaps</h1>
        </body>
        </html>
        """

    @pytest.fixture
    def shopify_json_ld_array_html(self):
        """Sample Shopify product page HTML with JSON-LD in array format."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            [
                {"@type": "WebSite", "name": "Test Store"},
                {
                    "@type": "Product",
                    "name": "Array Format Product",
                    "gtin": "1234567890123",
                    "offers": [
                        {
                            "@type": "Offer",
                            "price": 49.90,
                            "availability": "https://schema.org/InStock",
                            "gtin13": "1234567890123"
                        }
                    ]
                }
            ]
            </script>
        </head>
        <body></body>
        </html>
        """

    @pytest.fixture
    def shopify_out_of_stock_html(self):
        """Sample Shopify product page HTML for out of stock product."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Product",
                "name": "Out of Stock Product",
                "offers": {
                    "@type": "Offer",
                    "price": "29.90",
                    "availability": "https://schema.org/OutOfStock",
                    "gtin13": "9999999999999"
                }
            }
            </script>
        </head>
        <body></body>
        </html>
        """

    def test_extract_structured_data_basic(self, scraper, shopify_json_ld_html):
        """Test basic JSON-LD extraction from Shopify page."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(shopify_json_ld_html, "html.parser")
        result = scraper.extract_structured_data(soup, "https://test-store.fi/product")

        assert result is not None
        assert result["name"] == "Test Omega-3 180 kaps"
        assert result["current_price"] == 28.40
        assert result["ean"] == "6430050004729"
        assert result["available"] is True
        assert result["store"] == "test_store"

    def test_extract_structured_data_array_format(self, scraper, shopify_json_ld_array_html):
        """Test JSON-LD extraction when schema is in array format."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(shopify_json_ld_array_html, "html.parser")
        result = scraper.extract_structured_data(soup, "https://test-store.fi/product")

        assert result is not None
        assert result["name"] == "Array Format Product"
        assert result["current_price"] == 49.90
        assert result["ean"] == "1234567890123"
        assert result["available"] is True

    def test_extract_structured_data_out_of_stock(self, scraper, shopify_out_of_stock_html):
        """Test availability detection for out of stock products."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(shopify_out_of_stock_html, "html.parser")
        result = scraper.extract_structured_data(soup, "https://test-store.fi/product")

        assert result is not None
        assert result["available"] is False

    def test_generate_product_key(self, scraper):
        """Test product key generation."""
        product = {"ean": "6430050004729", "name": "Test Product"}
        key = scraper.generate_product_key(product)
        assert key == "test_store_6430050004729"

    def test_generate_product_key_fallback_to_sku(self, scraper):
        """Test product key generation falls back to SKU when no EAN."""
        product = {"sku": "TEST-123", "name": "Test Product"}
        key = scraper.generate_product_key(product)
        assert key == "test_store_TEST-123"


class TestStoreSpecificScrapers:
    """Test that store-specific scrapers are configured correctly."""

    def test_apteekki360_scraper_config(self):
        """Test Apteekki360Scraper configuration."""
        scraper = Apteekki360Scraper()
        assert scraper.base_url == "https://apteekki360.fi"
        assert scraper.store_name == "apteekki360"

    def test_sinunapteekki_scraper_config(self):
        """Test SinunapteekkiScraper configuration."""
        scraper = SinunapteekkiScraper()
        assert scraper.base_url == "https://www.sinunapteekki.fi"
        assert scraper.store_name == "sinunapteekki"

    def test_ruohonjuuri_scraper_config(self):
        """Test RuohonjuuriScraper configuration."""
        scraper = RuohonjuuriScraper()
        assert scraper.base_url == "https://www.ruohonjuuri.fi"
        assert scraper.store_name == "ruohonjuuri"


class TestTokmanniScraper:
    """Test cases for TokmanniScraper."""

    @pytest.fixture
    def scraper(self):
        """Create a TokmanniScraper instance."""
        return TokmanniScraper()

    @pytest.fixture
    def tokmanni_json_ld_html(self):
        """Sample Tokmanni product page HTML with JSON-LD."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Product",
                "name": "Premium Omega-3 Puhdas+ 180 kaps",
                "sku": "6430050004729",
                "mpn": "6430050004729",
                "offers": {
                    "@type": "Offer",
                    "price": "29.90",
                    "priceCurrency": "EUR",
                    "availability": "http://schema.org/OutOfStock"
                }
            }
            </script>
        </head>
        <body></body>
        </html>
        """

    def test_tokmanni_scraper_config(self, scraper):
        """Test TokmanniScraper configuration."""
        assert scraper.base_url == "https://www.tokmanni.fi"
        assert scraper.store_name == "tokmanni"

    def test_extract_structured_data(self, scraper, tokmanni_json_ld_html):
        """Test Tokmanni JSON-LD extraction using sku/mpn for EAN."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(tokmanni_json_ld_html, "html.parser")
        result = scraper.extract_structured_data(
            soup, "https://www.tokmanni.fi/premium-omega-3-puhdas-180-kaps-6430050004729"
        )

        assert result is not None
        assert result["name"] == "Premium Omega-3 Puhdas+ 180 kaps"
        assert result["current_price"] == 29.90
        assert result["ean"] == "6430050004729"
        assert result["available"] is False  # OutOfStock
        assert result["store"] == "tokmanni"

    def test_generate_product_key(self, scraper):
        """Test Tokmanni product key generation."""
        product = {"ean": "6430050004729"}
        key = scraper.generate_product_key(product)
        assert key == "tokmanni_6430050004729"


class TestEANPriceMonitor:
    """Test cases for EANPriceMonitor."""

    @pytest.fixture
    def ean_config(self):
        """Sample EAN products configuration."""
        return {
            "products": [
                {
                    "ean": "6430050004729",
                    "name": "Puhdas+ Premium Omega-3 1000mg 180 kaps",
                    "category": "supplements",
                    "status": "track",
                    "stores": {
                        "apteekki360": {
                            "url": "https://apteekki360.fi/products/test",
                            "status": "active",
                        },
                        "tokmanni": {
                            "url": "https://www.tokmanni.fi/test",
                            "status": "active",
                        },
                    },
                }
            ]
        }

    @pytest.fixture
    def ean_history(self):
        """Sample EAN price history."""
        return {
            "6430050004729": {
                "name": "Puhdas+ Premium Omega-3 1000mg 180 kaps",
                "stores": {
                    "apteekki360": {
                        "url": "https://apteekki360.fi/products/test",
                        "price_history": {
                            "2026-01-08": {"price": 30.00, "available": True}
                        },
                    }
                },
                "cross_store_lowest": {
                    "2026-01-08": {"price": 30.00, "store": "apteekki360"}
                },
                "all_time_lowest": {
                    "price": 28.00,
                    "store": "apteekki360",
                    "date": "2025-12-15",
                },
            }
        }

    @pytest.fixture
    def monitor(self, tmp_path, ean_config, ean_history):
        """Create an EANPriceMonitor instance with temporary files."""
        import yaml

        from ean_price_monitor import EANPriceMonitor

        history_file = tmp_path / "ean_price_history.json"
        config_file = tmp_path / "ean_products.yaml"

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(ean_history, f)

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(ean_config, f)

        # Mock email sender
        with patch("ean_price_monitor.EmailSender"):
            monitor = EANPriceMonitor(
                history_file=str(history_file), config_file=str(config_file)
            )

        return monitor

    def test_find_lowest_price_excludes_out_of_stock(self, monitor):
        """Test that out-of-stock items are excluded from lowest price."""
        store_results = {
            "apteekki360": {"current_price": 28.40, "available": True, "url": "url1"},
            "tokmanni": {"current_price": 25.00, "available": False, "url": "url2"},
            "sinunapteekki": {"current_price": 29.90, "available": True, "url": "url3"},
        }

        result = monitor.find_lowest_price(store_results)

        assert result is not None
        store, price, url = result
        assert store == "apteekki360"
        assert price == 28.40
        # Tokmanni's 25.00 is excluded because it's out of stock

    def test_find_lowest_price_all_out_of_stock(self, monitor):
        """Test that None is returned when all items are out of stock."""
        store_results = {
            "apteekki360": {"current_price": 28.40, "available": False},
            "tokmanni": {"current_price": 25.00, "available": False},
        }

        result = monitor.find_lowest_price(store_results)
        assert result is None

    def test_detect_price_drop(self, monitor, ean_history):
        """Test price drop detection."""
        # Previous lowest was 30.00, today is 28.00
        drop_info = monitor.detect_price_drop(
            "6430050004729", 28.00, ean_history
        )

        assert drop_info is not None
        assert drop_info["dropped"] is True
        assert drop_info["today"] == 28.00
        assert drop_info["yesterday"] == 30.00
        assert drop_info["savings"] == 2.00

    def test_detect_no_price_drop(self, monitor, ean_history):
        """Test no price drop when price is same or higher."""
        # Previous lowest was 30.00, today is 32.00
        drop_info = monitor.detect_price_drop(
            "6430050004729", 32.00, ean_history
        )

        assert drop_info is None

    def test_update_history(self, monitor):
        """Test history update functionality."""
        store_results = {
            "apteekki360": {
                "current_price": 28.40,
                "available": True,
                "url": "https://apteekki360.fi/test",
            }
        }
        lowest = ("apteekki360", 28.40, "https://apteekki360.fi/test")

        monitor.update_history(
            "NEW_EAN_123",
            "New Test Product",
            store_results,
            lowest,
        )

        assert "NEW_EAN_123" in monitor.price_history
        assert monitor.price_history["NEW_EAN_123"]["name"] == "New Test Product"
        assert "apteekki360" in monitor.price_history["NEW_EAN_123"]["stores"]
