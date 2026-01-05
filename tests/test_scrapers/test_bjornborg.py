"""Tests for the BjornBorgScraper."""

import pytest
from bs4 import BeautifulSoup

from scrapers.bjornborg import BjornBorgScraper


class TestBjornBorgScraper:
    """Test cases for BjornBorgScraper."""

    @pytest.fixture
    def scraper(self):
        """Create a BjornBorgScraper instance."""
        return BjornBorgScraper()

    def test_generate_product_key_with_base_product_code(self, scraper, sample_bjornborg_product):
        """Test key generation for products with base_product_code (socks)."""
        key = scraper.generate_product_key(sample_bjornborg_product)
        assert key == "base_10004564"

    def test_generate_product_key_with_product_id_only(self, scraper, sample_bjornborg_apparel):
        """Test key generation for products with only product_id (apparel)."""
        key = scraper.generate_product_key(sample_bjornborg_apparel)
        assert key == "id_centre-crew-9999-1431-gy013"

    def test_generate_product_key_with_sku_fallback(self, scraper):
        """Test key generation falling back to SKU."""
        product = {"sku": "ABC123_MP001"}
        key = scraper.generate_product_key(product)
        assert key == "sku_ABC123_MP001"

    def test_generate_product_key_url_fallback(self, scraper):
        """Test key generation falling back to URL."""
        product = {"url": "https://example.com/product-name-12345/"}
        key = scraper.generate_product_key(product)
        assert key == "url_product-name-12345"

    def test_extract_product_id_from_url_standard(self, scraper):
        """Test extracting product ID from standard URL pattern."""
        url = "/fi/essential-socks-10-pack-10004564-mp001/"
        product_id = scraper.extract_product_id_from_url(url)
        assert product_id == "10004564"

    def test_extract_product_id_from_url_full(self, scraper):
        """Test extracting product ID from full URL."""
        url = "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/"
        product_id = scraper.extract_product_id_from_url(url)
        assert product_id == "10004564"

    def test_extract_product_id_from_url_apparel(self, scraper):
        """Test extracting product ID from apparel URL (no numeric ID)."""
        url = "/fi/centre-crew-9999-1431-gy013/"
        product_id = scraper.extract_product_id_from_url(url)
        # Should return the last part of URL as fallback
        assert product_id == "centre-crew-9999-1431-gy013"

    def test_extract_base_product_code(self, scraper):
        """Test extracting base product code from URL."""
        url = "/fi/essential-socks-10-pack-10004564-mp001/"
        base_code = scraper._extract_base_product_code(url)
        assert base_code == "10004564"

    def test_extract_base_product_code_none(self, scraper):
        """Test extracting base product code when not present."""
        url = "/fi/centre-crew-9999-1431-gy013/"
        base_code = scraper._extract_base_product_code(url)
        assert base_code is None

    def test_extract_structured_data_success(self, scraper, bjornborg_json_ld_html):
        """Test successful extraction from JSON-LD structured data."""
        soup = BeautifulSoup(bjornborg_json_ld_html, "html.parser")
        url = "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/"

        result = scraper.extract_structured_data(soup, url)

        assert result is not None
        assert result["name"] == "Essential Socks 10-pack"
        assert result["current_price"] == 35.96
        assert result["base_product_code"] == "10004564"
        assert result["site"] == "bjornborg"

    def test_extract_structured_data_no_json_ld(self, scraper):
        """Test extraction when no JSON-LD is present."""
        html = "<html><body><h1>Product</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        result = scraper.extract_structured_data(soup, "https://example.com/product/")

        assert result is None

    def test_extract_fallback_data_from_title(self, scraper):
        """Test fallback extraction from page title."""
        html = """
        <html>
        <head><title>Essential Socks 10-pack - Black | Björn Borg</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        url = "https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/"

        result = scraper.extract_fallback_data(soup, url)

        # Without price, result should be None (essential field missing)
        assert result is None

    def test_is_essential_10pack_variant_positive(self, scraper):
        """Test URL validation for Essential 10-pack variants."""
        valid_urls = [
            "/fi/essential-socks-10-pack-10004564-mp001/",
            "/fi/essential-ankle-sock-10-pack-10002940-mp001/",
        ]

        for url in valid_urls:
            assert scraper._is_essential_10pack_variant(url) is True

    def test_is_essential_10pack_variant_negative(self, scraper):
        """Test URL validation rejects non-Essential URLs."""
        invalid_urls = [
            "/en/essential-socks-10-pack-10004564-mp001/",  # Not Finnish
            "/fi/category/socks/",  # Category page
            "/fi/search?q=socks",  # Search page
        ]

        for url in invalid_urls:
            assert scraper._is_essential_10pack_variant(url) is False

    def test_base_url(self, scraper):
        """Test that base URL is correctly set."""
        assert scraper.base_url == "https://www.bjornborg.com"
