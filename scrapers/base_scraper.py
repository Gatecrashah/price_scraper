#!/usr/bin/env python3
"""
Base scraper interface for multi-site price monitoring.

Defines the common interface and utilities that all site-specific scrapers should implement.
"""

import json
import logging
import re
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all site scrapers."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

        # Set common headers to mimic a real browser
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    @abstractmethod
    def extract_structured_data(self, soup: BeautifulSoup, url: str) -> dict | None:
        """
        Extract product data from structured sources (JSON-LD, dataLayer, etc.).

        This method should be implemented by each scraper to extract product information
        from the most reliable structured data sources available on the site.

        Args:
            soup: BeautifulSoup object of the parsed HTML
            url: The product URL being scraped

        Returns:
            Dict containing product information, or None if extraction fails
        """
        pass

    @abstractmethod
    def extract_fallback_data(self, soup: BeautifulSoup, url: str) -> dict | None:
        """
        Extract product data using CSS selectors as fallback.

        This method provides a fallback when structured data is not available.
        Should use specific, robust CSS selectors rather than text parsing.

        Args:
            soup: BeautifulSoup object of the parsed HTML
            url: The product URL being scraped

        Returns:
            Dict containing product information, or None if extraction fails
        """
        pass

    @abstractmethod
    def generate_product_key(self, product: dict) -> str:
        """
        Generate a unique identifier for a product.

        Args:
            product: Product dictionary containing product information

        Returns:
            Unique string identifier for the product
        """
        pass

    def extract_json_ld(self, soup: BeautifulSoup, schema_type: str = "Product") -> dict | None:
        """
        Extract JSON-LD structured data from script tags.

        Args:
            soup: BeautifulSoup object
            schema_type: The @type to look for (e.g., "Product", "Organization")

        Returns:
            Dict containing the structured data, or None if not found
        """
        try:
            # Find all JSON-LD script tags
            json_scripts = soup.find_all("script", type="application/ld+json")

            for script in json_scripts:
                if not script.string:
                    continue

                try:
                    data = json.loads(script.string)

                    # Handle single objects
                    if isinstance(data, dict):
                        if data.get("@type") == schema_type:
                            return data

                    # Handle arrays of objects
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") == schema_type:
                                return item

                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.debug(f"Error extracting JSON-LD: {e}")
            return None

    def extract_dataLayer(self, soup: BeautifulSoup) -> dict | None:
        """
        Extract Google Analytics dataLayer objects from script tags.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dict containing dataLayer data, or None if not found
        """
        try:
            script_tags = soup.find_all("script")

            for script in script_tags:
                if not script.string:
                    continue

                # Look for dataLayer declarations
                if "dataLayer" in script.string:
                    # Try to extract product detail events
                    if "productDetail" in script.string:
                        # Use regex to extract the dataLayer object
                        pattern = r"dataLayer\.push\(({[^}]+}(?:[^}]*})*)\)"
                        matches = re.findall(pattern, script.string)

                        for match in matches:
                            try:
                                data = json.loads(match)
                                if data.get("event") == "productDetail":
                                    return data
                            except json.JSONDecodeError:
                                continue

            return None

        except Exception as e:
            logger.debug(f"Error extracting dataLayer: {e}")
            return None

    def extract_price(self, price_text: str) -> float | None:
        """Extract numeric price from text."""
        if not price_text:
            return None

        # Remove currency symbols and whitespace, find numbers
        price_match = re.search(r"(\d+[.,]\d+|\d+)", price_text.replace(",", "."))
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        return None

    def scrape_product_page(self, product_url: str) -> dict | None:
        """
        Main scraping method that tries structured data first, then fallback.

        Args:
            product_url: URL to scrape

        Returns:
            Product information dictionary or None if scraping fails
        """
        try:
            full_url = (
                product_url if product_url.startswith("http") else self.base_url + product_url
            )
            logger.info(f"Scraping product page: {full_url}")

            response = self.session.get(full_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Try structured data first (most reliable)
            logger.debug("Attempting structured data extraction")
            product_info = self.extract_structured_data(soup, full_url)

            if product_info:
                logger.info(
                    f"✅ Successfully extracted via structured data: {product_info.get('name', 'Unknown')}"
                )
                return product_info

            # Fallback to CSS selectors
            logger.debug("Structured data failed, trying fallback extraction")
            product_info = self.extract_fallback_data(soup, full_url)

            if product_info:
                logger.info(
                    f"✅ Successfully extracted via fallback: {product_info.get('name', 'Unknown')}"
                )
                return product_info
            else:
                logger.warning(f"❌ All extraction methods failed for {full_url}")
                return None

        except Exception as e:
            logger.error(f"Error scraping product page {product_url}: {e}")
            return None

    @abstractmethod
    def get_product_urls(self) -> list[str]:
        """
        Get list of product URLs to scrape from configuration.

        Returns:
            List of product URLs
        """
        pass

    @abstractmethod
    def scrape_all_products(self) -> list[dict]:
        """
        Scrape all products for this site.

        Returns:
            List of product information dictionaries
        """
        pass
