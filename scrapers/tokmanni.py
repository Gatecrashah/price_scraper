#!/usr/bin/env python3
"""
Scraper for Tokmanni.fi (custom platform, not Shopify).

Tokmanni uses sku/mpn fields for EAN instead of gtin13.
The EAN is also included directly in the product URL path.
"""

import logging

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TokmanniScraper(BaseScraper):
    """
    Scraper for Tokmanni.fi.

    Tokmanni uses a custom e-commerce platform with JSON-LD structured data.
    Key differences from Shopify:
    - EAN is in 'sku' and 'mpn' fields (not gtin13)
    - EAN is included in the URL path
    """

    def __init__(self):
        super().__init__("https://www.tokmanni.fi")
        self.store_name = "tokmanni"

    def extract_structured_data(self, soup: BeautifulSoup, url: str) -> dict | None:
        """Extract product data from Tokmanni JSON-LD."""
        json_ld = self.extract_json_ld(soup, "Product")

        if not json_ld:
            logger.debug(f"No JSON-LD Product data found for {url}")
            return None

        offers = json_ld.get("offers", {})

        # Tokmanni uses sku/mpn for EAN (not gtin13)
        ean = json_ld.get("sku") or json_ld.get("mpn")

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
            "sku": json_ld.get("sku"),
        }

    def extract_fallback_data(self, soup: BeautifulSoup, url: str) -> dict | None:
        """Extract product data using CSS selectors as fallback."""
        try:
            # Tokmanni price selectors
            price_selectors = [
                ".product-price",
                ".price",
                "[data-price]",
                ".current-price",
            ]

            price = None
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    price = self.extract_price(price_el.get_text())
                    if price:
                        break

            # Title selectors
            title_selectors = [
                "h1.product-name",
                ".product-title",
                "h1",
            ]

            name = None
            for selector in title_selectors:
                title_el = soup.select_one(selector)
                if title_el:
                    name = title_el.get_text().strip()
                    if name:
                        break

            # Try to extract EAN from URL (Tokmanni includes it in the path)
            ean = None
            if "-" in url:
                # URL format: /product-name-EAN
                potential_ean = url.rstrip("/").split("-")[-1]
                if potential_ean.isdigit() and len(potential_ean) == 13:
                    ean = potential_ean

            if price and name:
                return {
                    "name": name,
                    "current_price": price,
                    "ean": ean,
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
        return f"tokmanni_{ean}"

    def get_product_urls(self) -> list[str]:
        """Get product URLs from EAN configuration."""
        return []

    def scrape_all_products(self) -> list[dict]:
        """Scrape all products for this store."""
        urls = self.get_product_urls()
        products = []

        for url in urls:
            product = self.scrape_product_page(url)
            if product:
                products.append(product)

        return products
