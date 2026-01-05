"""Tests for the PriceMonitor class."""

import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from price_monitor import PriceMonitor


class TestPriceMonitor:
    """Test cases for PriceMonitor."""

    @pytest.fixture
    def monitor(self, tmp_path, sample_products_config, sample_price_history):
        """Create a PriceMonitor instance with temporary files."""
        # Create temporary files
        history_file = tmp_path / "price_history.json"
        config_file = tmp_path / "products.yaml"

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(sample_price_history, f)

        import yaml

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_products_config, f)

        # Change to temp directory for relative file access
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Mock email sender to avoid requiring API keys
            with patch("price_monitor.EmailSender"):
                monitor = PriceMonitor(history_file=str(history_file), config_file=str(config_file))
        finally:
            os.chdir(original_dir)

        return monitor

    def test_get_product_key_bjornborg_with_base_code(self, monitor, sample_bjornborg_product):
        """Test key generation for Björn Borg products with base_product_code."""
        key = monitor.get_product_key(sample_bjornborg_product)
        assert key == "base_10004564"

    def test_get_product_key_bjornborg_apparel(self, monitor, sample_bjornborg_apparel):
        """Test key generation for Björn Borg apparel (no base_product_code)."""
        key = monitor.get_product_key(sample_bjornborg_apparel)
        assert key == "id_centre-crew-9999-1431-gy013"

    def test_get_product_key_fitnesstukku(self, monitor, sample_fitnesstukku_product):
        """Test key generation for Fitnesstukku products."""
        key = monitor.get_product_key(sample_fitnesstukku_product)
        assert key == "id_fitnesstukku_5854R"

    def test_get_product_key_unknown_site_fallback(self, monitor):
        """Test key generation falls back for unknown sites."""
        product = {
            "site": "unknown_site",
            "product_id": "TEST123",
        }
        key = monitor.get_product_key(product)
        assert key == "id_TEST123"

    def test_get_product_key_url_fallback(self, monitor):
        """Test key generation falls back to URL when no ID available."""
        product = {
            "site": "unknown_site",
            "url": "https://example.com/product",
        }
        key = monitor.get_product_key(product)
        assert key == "url_https://example.com/product"

    def test_detect_price_changes_decrease(self, monitor, sample_bjornborg_product):
        """Test detecting a price decrease."""
        # Set up history with higher price
        monitor.price_history = {
            "base_10004564": {
                "name": "Essential Socks 10-pack",
                "purchase_url": sample_bjornborg_product["purchase_url"],
                "price_history": {
                    "2025-01-01": {
                        "current_price": 44.95,
                        "original_price": 44.95,
                        "discount_percent": 0,
                        "scraped_at": "2025-01-01T09:00:00",
                    }
                },
            }
        }

        # Current product has lower price
        sample_bjornborg_product["current_price"] = 35.96

        changes = monitor.detect_price_changes([sample_bjornborg_product])

        assert len(changes) == 1
        assert changes[0]["current_price"] == 35.96
        assert changes[0]["previous_price"] == 44.95
        assert changes[0]["name"] == "Essential Socks 10-pack"

    def test_detect_price_changes_increase(self, monitor, sample_bjornborg_product):
        """Test detecting a price increase."""
        # Set up history with lower price
        monitor.price_history = {
            "base_10004564": {
                "name": "Essential Socks 10-pack",
                "purchase_url": sample_bjornborg_product["purchase_url"],
                "price_history": {
                    "2025-01-01": {
                        "current_price": 30.00,
                        "original_price": 44.95,
                        "discount_percent": 33,
                        "scraped_at": "2025-01-01T09:00:00",
                    }
                },
            }
        }

        # Current product has higher price
        sample_bjornborg_product["current_price"] = 35.96

        changes = monitor.detect_price_changes([sample_bjornborg_product])

        assert len(changes) == 1
        assert changes[0]["current_price"] == 35.96
        assert changes[0]["previous_price"] == 30.00

    def test_detect_price_changes_no_change(self, monitor, sample_bjornborg_product):
        """Test that no change is detected when price is the same."""
        # Set up history with same price
        monitor.price_history = {
            "base_10004564": {
                "name": "Essential Socks 10-pack",
                "purchase_url": sample_bjornborg_product["purchase_url"],
                "price_history": {
                    "2025-01-01": {
                        "current_price": 35.96,
                        "original_price": 44.95,
                        "discount_percent": 20,
                        "scraped_at": "2025-01-01T09:00:00",
                    }
                },
            }
        }

        sample_bjornborg_product["current_price"] = 35.96

        changes = monitor.detect_price_changes([sample_bjornborg_product])

        assert len(changes) == 0

    def test_detect_price_changes_new_product(self, monitor):
        """Test handling of new products with no history."""
        # Empty history
        monitor.price_history = {}

        new_product = {
            "name": "New Product",
            "url": "https://example.com/new",
            "purchase_url": "https://example.com/new",
            "current_price": 29.99,
            "product_id": "NEW123",
            "site": "bjornborg",
        }

        changes = monitor.detect_price_changes([new_product])

        # No change detected for new products (no previous price to compare)
        assert len(changes) == 0
        # But product should be added to history
        assert "id_NEW123" in monitor.price_history

    def test_cleanup_old_history(self, monitor):
        """Test cleanup of old price history entries."""
        old_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
        recent_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        monitor.price_history = {
            "test_product": {
                "name": "Test",
                "purchase_url": "https://example.com",
                "price_history": {
                    old_date: {"current_price": 10.00},
                    recent_date: {"current_price": 10.00},
                },
            }
        }

        monitor.cleanup_old_history(days_to_keep=365)

        history = monitor.price_history["test_product"]["price_history"]
        assert old_date not in history
        assert recent_date in history

    def test_get_tracked_products(self, monitor):
        """Test getting list of tracked products from config."""
        tracked = monitor.get_tracked_products()

        # From sample_products_config, only products with status='track'
        assert len(tracked) == 2  # 1 bjornborg + 1 fitnesstukku tracked
        assert all(p["status"] == "track" for p in tracked)

    def test_load_price_history_empty(self, tmp_path):
        """Test loading price history when file doesn't exist."""
        with patch("price_monitor.EmailSender"):
            monitor = PriceMonitor(
                history_file=str(tmp_path / "nonexistent.json"),
                config_file=str(tmp_path / "nonexistent.yaml"),
            )

        assert monitor.price_history == {}

    def test_get_price_summary(self, monitor, sample_bjornborg_product):
        """Test price summary generation."""
        # Add product to history with today's data
        today = datetime.now().strftime("%Y-%m-%d")
        monitor.price_history = {
            "base_10004564": {
                "name": "Essential Socks 10-pack",
                "purchase_url": sample_bjornborg_product["purchase_url"],
                "price_history": {
                    today: {
                        "current_price": 35.96,
                        "original_price": 44.95,
                        "discount_percent": 20,
                    }
                },
            }
        }

        summary = monitor.get_price_summary()

        assert summary["total_products"] == 1
        assert len(summary["products"]) == 1
        assert summary["products"][0]["current_price"] == 35.96
