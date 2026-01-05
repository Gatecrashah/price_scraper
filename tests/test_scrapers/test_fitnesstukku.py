"""Tests for the FitnesstukkuScraper."""

import pytest
from bs4 import BeautifulSoup

from scrapers.fitnesstukku import FitnesstukkuScraper


class TestFitnesstukkuScraper:
    """Test cases for FitnesstukkuScraper."""

    @pytest.fixture
    def scraper(self):
        """Create a FitnesstukkuScraper instance."""
        return FitnesstukkuScraper()

    def test_generate_product_key_with_product_id(self, scraper, sample_fitnesstukku_product):
        """Test key generation for Fitnesstukku products."""
        key = scraper.generate_product_key(sample_fitnesstukku_product)
        assert key == "id_fitnesstukku_5854R"

    def test_generate_product_key_url_fallback(self, scraper):
        """Test key generation falling back to URL."""
        product = {
            "url": "https://www.fitnesstukku.fi/some-product/ABC123.html",
            "purchase_url": "https://www.fitnesstukku.fi/some-product/ABC123.html",
        }
        key = scraper.generate_product_key(product)
        assert key == "url_fitnesstukku_ABC123"

    def test_extract_product_id_from_url_standard(self, scraper):
        """Test extracting product ID from standard URL pattern."""
        url = "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html"
        product_id = scraper._extract_product_id_from_url(url)
        assert product_id == "5854R"

    def test_extract_product_id_from_url_numeric(self, scraper):
        """Test extracting numeric product ID from URL."""
        url = "https://www.fitnesstukku.fi/creatine-monohydrate-500-g/609.html"
        product_id = scraper._extract_product_id_from_url(url)
        assert product_id == "609"

    def test_extract_product_id_from_url_invalid(self, scraper):
        """Test extracting product ID from invalid URL."""
        url = "https://www.fitnesstukku.fi/category/"
        product_id = scraper._extract_product_id_from_url(url)
        assert product_id is None

    def test_extract_structured_data_success(self, scraper, fitnesstukku_tracking_html):
        """Test successful extraction from dataTrackingView."""
        soup = BeautifulSoup(fitnesstukku_tracking_html, "html.parser")
        url = "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html"

        result = scraper.extract_structured_data(soup, url)

        assert result is not None
        assert result["name"] == "Whey-80 4 kg"
        assert result["current_price"] == 89.90
        assert result["brand"] == "Star Nutrition"
        assert result["site"] == "fitnesstukku"
        assert result["product_id"] == "fitnesstukku_5854R"

    def test_extract_structured_data_no_tracking(self, scraper):
        """Test extraction when no tracking data is present."""
        html = "<html><body><h1>Product</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        result = scraper.extract_structured_data(
            soup, "https://www.fitnesstukku.fi/product/123.html"
        )

        assert result is None

    def test_extract_fallback_data_with_h1(self, scraper):
        """Test fallback extraction from H1 element."""
        html = """
        <html>
        <body>
            <h1 class="product-name">Test Product Name</h1>
            <div class="price-sales">49.90 €</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        url = "https://www.fitnesstukku.fi/test-product/TEST123.html"

        result = scraper.extract_fallback_data(soup, url)

        assert result is not None
        assert result["name"] == "Test Product Name"
        assert result["current_price"] == 49.90
        assert result["product_id"] == "fitnesstukku_TEST123"

    def test_extract_fallback_data_missing_price(self, scraper):
        """Test fallback extraction without price returns None."""
        html = """
        <html>
        <body>
            <h1 class="product-name">Test Product Name</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = scraper.extract_fallback_data(soup, "https://www.fitnesstukku.fi/test/123.html")

        assert result is None

    def test_base_url(self, scraper):
        """Test that base URL is correctly set."""
        assert scraper.base_url == "https://www.fitnesstukku.fi"

    def test_extract_price(self, scraper):
        """Test price extraction from various formats."""
        assert scraper.extract_price("49.90 €") == 49.90
        assert scraper.extract_price("49,90 EUR") == 49.90
        assert scraper.extract_price("€49.90") == 49.90
        assert scraper.extract_price("Price: 49.90") == 49.90
        assert scraper.extract_price("") is None
        assert scraper.extract_price(None) is None
