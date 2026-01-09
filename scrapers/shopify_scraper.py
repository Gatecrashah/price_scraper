#!/usr/bin/env python3
"""
Base scraper for Shopify-based e-commerce stores.

Shopify stores consistently provide JSON-LD structured data with:
- @type: "Product"
- gtin/gtin13 field for EAN
- offers.price and offers.availability

This base class covers: Apteekki360, Sinunapteekki, Ruohonjuuri
"""

import logging

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ShopifyScraper(BaseScraper):
    """
    Base scraper for Shopify-based stores.

    Provides common JSON-LD extraction logic for Shopify stores.
    Store-specific scrapers only need to set base_url and store_name.
    """

    def __init__(self, base_url: str, store_name: str):
        super().__init__(base_url)
        self.store_name = store_name

    def extract_structured_data(self, soup: BeautifulSoup, url: str) -> dict | None:
        """Extract product data from Shopify JSON-LD."""
        json_ld = self.extract_json_ld(soup, "Product")

        if not json_ld:
            # Try to find Product in array of schemas
            json_ld = self._find_product_in_schemas(soup)

        if not json_ld:
            logger.debug(f"No JSON-LD Product data found for {url}")
            return None

        # Extract offers (can be single object or array)
        offers = json_ld.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        # Get EAN from various possible fields
        ean = (
            offers.get("gtin13")
            or offers.get("gtin")
            or json_ld.get("gtin13")
            or json_ld.get("gtin")
            or json_ld.get("mpn")
        )

        # Parse availability
        availability_url = offers.get("availability", "")
        in_stock = "InStock" in availability_url

        # Get price
        price = offers.get("price")
        if price is not None:
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = self.extract_price(str(price))

        return {
            "name": json_ld.get("name"),
            "current_price": price,
            "ean": ean,
            "available": in_stock,
            "url": url,
            "store": self.store_name,
            "sku": offers.get("sku") or json_ld.get("sku"),
        }

    def _find_product_in_schemas(self, soup: BeautifulSoup) -> dict | None:
        """Find Product schema in array of JSON-LD objects."""
        import json

        try:
            json_scripts = soup.find_all("script", type="application/ld+json")

            for script in json_scripts:
                if not script.string:
                    continue

                try:
                    data = json.loads(script.string)

                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") == "Product":
                                return item

                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.debug(f"Error finding Product in schemas: {e}")
            return None

    def extract_fallback_data(self, soup: BeautifulSoup, url: str) -> dict | None:
        """
        Extract product data using CSS selectors as fallback.

        Shopify stores have fairly consistent CSS patterns.
        """
        try:
            # Common Shopify price selectors
            price_selectors = [
                ".price__current",
                ".product__price",
                ".price-item--regular",
                ".product-price",
                "[data-product-price]",
                ".money",
            ]

            price = None
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    price = self.extract_price(price_el.get_text())
                    if price:
                        break

            # Common Shopify title selectors
            title_selectors = [
                ".product__title",
                ".product-title",
                "h1.title",
                "[data-product-title]",
                "h1",
            ]

            name = None
            for selector in title_selectors:
                title_el = soup.select_one(selector)
                if title_el:
                    name = title_el.get_text().strip()
                    if name:
                        break

            if price and name:
                return {
                    "name": name,
                    "current_price": price,
                    "url": url,
                    "store": self.store_name,
                    "available": True,  # Assume in stock if page exists
                }

            return None

        except Exception as e:
            logger.error(f"Error in fallback extraction: {e}")
            return None

    def generate_product_key(self, product: dict) -> str:
        """Generate unique key based on store and EAN."""
        ean = product.get("ean") or product.get("sku") or "unknown"
        return f"{self.store_name}_{ean}"

    def get_product_urls(self) -> list[str]:
        """
        Get product URLs from EAN configuration.

        Note: For EAN monitoring, URLs are provided via ean_products.yaml,
        not loaded here. This method is for compatibility with BaseScraper.
        """
        return []

    def scrape_all_products(self) -> list[dict]:
        """
        Scrape all products for this store.

        Note: For EAN monitoring, products are scraped via EANPriceMonitor,
        not this method. This is for compatibility with BaseScraper.
        """
        urls = self.get_product_urls()
        products = []

        for url in urls:
            product = self.scrape_product_page(url)
            if product:
                products.append(product)

        return products


# Store-specific scrapers - minimal configuration needed


class Apteekki360Scraper(ShopifyScraper):
    """Scraper for Apteekki360.fi"""

    def __init__(self):
        super().__init__("https://apteekki360.fi", "apteekki360")


class SinunapteekkiScraper(ShopifyScraper):
    """Scraper for Sinunapteekki.fi"""

    def __init__(self):
        super().__init__("https://www.sinunapteekki.fi", "sinunapteekki")


class RuohonjuuriScraper(ShopifyScraper):
    """Scraper for Ruohonjuuri.fi"""

    def __init__(self):
        super().__init__("https://www.ruohonjuuri.fi", "ruohonjuuri")
