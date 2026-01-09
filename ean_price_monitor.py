#!/usr/bin/env python3
"""
EAN-based price monitoring across multiple Finnish e-commerce stores.

Tracks products by EAN number, compares prices across stores,
and sends notifications when the lowest available price drops.
"""

import json
import logging
import os
import sys
from datetime import datetime

import yaml

from email_sender import EmailSender
from scrapers.shopify_scraper import (
    Apteekki360Scraper,
    RuohonjuuriScraper,
    SinunapteekkiScraper,
)
from scrapers.tokmanni import TokmanniScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EANPriceMonitor:
    """
    Monitors prices for products identified by EAN across multiple stores.

    Key features:
    - Cross-store price comparison
    - Excludes out-of-stock items from lowest price calculation
    - Tracks historical lowest prices
    - Sends notifications on price drops
    """

    def __init__(
        self,
        history_file: str = "ean_price_history.json",
        config_file: str = "ean_products.yaml",
    ):
        self.history_file = history_file
        self.config_file = config_file
        self.email_sender = EmailSender()
        self.price_history = self._load_history()
        self.product_config = self._load_config()

        # Initialize scrapers
        self.scrapers = {
            "apteekki360": Apteekki360Scraper(),
            "tokmanni": TokmanniScraper(),
            "sinunapteekki": SinunapteekkiScraper(),
            "ruohonjuuri": RuohonjuuriScraper(),
        }

    def _load_history(self) -> dict:
        """Load EAN price history from JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                return {}
        return {}

    def _load_config(self) -> dict:
        """Load EAN product configuration from YAML file."""
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file not found: {self.config_file}")
            return {"products": []}
        try:
            with open(self.config_file, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"products": []}

    def _save_history(self):
        """Save EAN price history to JSON file."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
            logger.info(f"Price history saved to {self.history_file}")
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def scrape_ean_product(self, ean_config: dict) -> dict[str, dict]:
        """
        Scrape all configured stores for a single EAN product.

        Args:
            ean_config: Product configuration from ean_products.yaml

        Returns:
            Dict mapping store name to scraped product data
        """
        results = {}
        stores = ean_config.get("stores", {})

        for store_name, store_config in stores.items():
            if store_config.get("status") != "active":
                logger.debug(f"Skipping inactive store: {store_name}")
                continue

            scraper = self.scrapers.get(store_name)
            if not scraper:
                logger.warning(f"No scraper found for store: {store_name}")
                continue

            url = store_config.get("url")
            if not url:
                logger.warning(f"No URL configured for {store_name}")
                continue

            try:
                logger.info(f"Scraping {store_name}: {url}")
                result = scraper.scrape_product_page(url)

                if result:
                    results[store_name] = result
                    logger.info(
                        f"  ✅ {store_name}: €{result.get('current_price', 'N/A')} "
                        f"({'In Stock' if result.get('available') else 'Out of Stock'})"
                    )
                else:
                    logger.warning(f"  ❌ Failed to scrape {store_name}")

            except Exception as e:
                logger.error(f"Error scraping {store_name}: {e}")

        return results

    def find_lowest_price(self, store_results: dict[str, dict]) -> tuple[str, float, str] | None:
        """
        Find the store with the lowest price among in-stock items.

        Args:
            store_results: Dict mapping store name to scraped data

        Returns:
            Tuple of (store_name, price, url) or None if no valid prices
        """
        valid_prices = []

        for store_name, data in store_results.items():
            if not data:
                continue

            price = data.get("current_price")
            available = data.get("available", True)

            # Only consider in-stock items
            if price and available:
                valid_prices.append((store_name, price, data.get("url", "")))

        if not valid_prices:
            return None

        # Return the lowest price
        return min(valid_prices, key=lambda x: x[1])

    def detect_price_drop(
        self, ean: str, today_lowest: float, today_store: str, history: dict
    ) -> dict | None:
        """
        Check if today's lowest price is lower than the previous lowest.

        Args:
            ean: Product EAN
            today_lowest: Today's lowest price across stores
            today_store: Store with the lowest price
            history: Full price history dict

        Returns:
            Dict with drop info if price dropped, None otherwise
        """
        ean_history = history.get(ean, {})
        current_lowest = ean_history.get("current_lowest", {})
        previous_price = current_lowest.get("price") if current_lowest else None

        # Check for price drop compared to previous lowest
        if previous_price and today_lowest < previous_price - 0.01:
            all_time = ean_history.get("all_time_lowest", {})

            return {
                "dropped": True,
                "today": today_lowest,
                "yesterday": previous_price,
                "savings": previous_price - today_lowest,
                "all_time_price": all_time.get("price") if all_time else None,
                "all_time_date": all_time.get("date") if all_time else None,
                "all_time_store": all_time.get("store") if all_time else None,
            }

        return None

    def update_history(
        self,
        ean: str,
        product_name: str,
        store_results: dict[str, dict],
        lowest: tuple[str, float, str] | None,
    ):
        """
        Update price history for an EAN product (event-based format).

        Only records changes - if price/availability changed, adds to price_changes.

        Args:
            ean: Product EAN
            product_name: Product name
            store_results: Scraped data from all stores
            lowest: Lowest price tuple (store, price, url) or None
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Initialize history for this EAN if needed
        if ean not in self.price_history:
            self.price_history[ean] = {
                "name": product_name,
                "stores": {},
                "current_lowest": None,
                "all_time_lowest": None,
                "price_changes": [],
            }

        ean_history = self.price_history[ean]
        ean_history["name"] = product_name

        # Ensure price_changes exists (for migrated data)
        if "price_changes" not in ean_history:
            ean_history["price_changes"] = []

        # Update per-store data and detect changes
        for store_name, data in store_results.items():
            new_price = data.get("current_price")
            new_available = data.get("available", True)

            # Get previous state for this store
            prev_store = ean_history.get("stores", {}).get(store_name, {})
            prev_price = prev_store.get("current_price")
            prev_available = prev_store.get("available")

            # Check for changes
            price_changed = (
                prev_price is not None
                and new_price is not None
                and abs(new_price - prev_price) > 0.01
            )
            avail_changed = prev_available is not None and new_available != prev_available
            is_new = store_name not in ean_history.get("stores", {})

            # Record change event if something changed
            if is_new:
                ean_history["price_changes"].append(
                    {
                        "date": today,
                        "store": store_name,
                        "price": new_price,
                        "available": new_available,
                        "type": "initial",
                    }
                )
            elif price_changed or avail_changed:
                change_entry = {
                    "date": today,
                    "store": store_name,
                    "available": new_available,
                }
                if price_changed:
                    change_pct = round(((new_price - prev_price) / prev_price) * 100, 1)
                    change_entry["from"] = prev_price
                    change_entry["to"] = new_price
                    change_entry["change_pct"] = change_pct
                if avail_changed:
                    change_entry["availability_changed"] = True
                    change_entry["from_available"] = prev_available

                ean_history["price_changes"].append(change_entry)

            # Update current store state
            if "stores" not in ean_history:
                ean_history["stores"] = {}

            ean_history["stores"][store_name] = {
                "url": data.get("url"),
                "current_price": new_price,
                "available": new_available,
                "last_updated": today,
            }

        # Update current lowest
        if lowest:
            store_name, price, url = lowest
            prev_lowest = ean_history.get("current_lowest", {})
            prev_lowest_price = prev_lowest.get("price") if prev_lowest else None

            # Check if cross-store lowest changed
            if prev_lowest_price is None or abs(price - prev_lowest_price) > 0.01:
                ean_history["current_lowest"] = {
                    "price": price,
                    "store": store_name,
                    "url": url,
                    "since": today,
                }

            # Update all-time lowest
            current_all_time = ean_history.get("all_time_lowest")
            if not current_all_time or price < current_all_time.get("price", float("inf")):
                ean_history["all_time_lowest"] = {
                    "price": price,
                    "store": store_name,
                    "date": today,
                    "url": url,
                }

    def run_monitoring_cycle(self) -> tuple[bool, list[dict]]:
        """
        Run a complete EAN price monitoring cycle.

        Returns:
            Tuple of (success, list of price drops)
        """
        logger.info("=" * 60)
        logger.info("Starting EAN Price Monitor cycle...")
        logger.info("=" * 60)

        products = self.product_config.get("products", [])
        price_drops = []
        all_results = []

        for product in products:
            if product.get("status") != "track":
                continue

            ean = product.get("ean")
            name = product.get("name", "Unknown Product")

            logger.info(f"\n📦 Processing: {name} (EAN: {ean})")

            # Scrape all stores for this EAN
            store_results = self.scrape_ean_product(product)

            if not store_results:
                logger.warning(f"No results for EAN {ean}")
                continue

            # Find lowest in-stock price
            lowest = self.find_lowest_price(store_results)

            if lowest:
                store_name, price, url = lowest
                logger.info(f"  💰 Lowest in-stock price: €{price:.2f} at {store_name}")

                # Check for price drop
                drop_info = self.detect_price_drop(ean, price, store_name, self.price_history)

                if drop_info:
                    logger.info(
                        f"  🎉 PRICE DROP! €{drop_info['yesterday']:.2f} → €{drop_info['today']:.2f} "
                        f"(save €{drop_info['savings']:.2f})"
                    )

                    price_drops.append(
                        {
                            "ean": ean,
                            "name": name,
                            "store": store_name,
                            "url": url,
                            "current_price": price,
                            "previous_price": drop_info["yesterday"],
                            "savings": drop_info["savings"],
                            "all_time_price": drop_info.get("all_time_price"),
                            "all_time_date": drop_info.get("all_time_date"),
                            "all_time_store": drop_info.get("all_time_store"),
                            "all_store_prices": {
                                s: d.get("current_price")
                                for s, d in store_results.items()
                                if d.get("available")
                            },
                        }
                    )
            else:
                logger.warning(f"  ⚠️ No in-stock prices found for EAN {ean}")

            # Update history
            self.update_history(ean, name, store_results, lowest)

            # Collect results for summary
            all_results.append(
                {
                    "ean": ean,
                    "name": name,
                    "store_results": store_results,
                    "lowest": lowest,
                }
            )

        # Save updated history
        self._save_history()

        # Send notifications for price drops
        if price_drops:
            logger.info(f"\n📧 Sending notification for {len(price_drops)} price drop(s)")
            success = self.email_sender.send_ean_price_alert(price_drops)
            if success:
                logger.info("✅ Notification sent successfully")
            else:
                logger.error("❌ Failed to send notification")
        else:
            logger.info("\n📭 No price drops detected - no notification sent")

        # Print summary
        self._print_summary(all_results)

        logger.info("\n" + "=" * 60)
        logger.info("EAN Price Monitor cycle completed")
        logger.info("=" * 60)

        return True, price_drops

    def _print_summary(self, results: list[dict]):
        """Print a summary of all scraped prices."""
        logger.info("\n" + "-" * 60)
        logger.info("PRICE SUMMARY")
        logger.info("-" * 60)

        for result in results:
            name = result["name"]
            lowest = result["lowest"]
            store_results = result["store_results"]

            logger.info(f"\n{name}:")

            # Sort stores by price
            sorted_stores = sorted(
                [
                    (s, d.get("current_price"), d.get("available"))
                    for s, d in store_results.items()
                    if d.get("current_price")
                ],
                key=lambda x: (not x[2], x[1]),  # In-stock first, then by price
            )

            for store, price, available in sorted_stores:
                status = "✅" if available else "❌"
                marker = " ← LOWEST" if lowest and store == lowest[0] else ""
                logger.info(f"  {status} {store}: €{price:.2f}{marker}")


def main():
    """Main entry point."""
    logger.info("EAN Price Monitor starting...")

    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Running in test mode...")

        # In test mode, we don't need email functionality
        try:
            monitor = EANPriceMonitor()
        except ValueError as e:
            if "RESEND_API_KEY" in str(e) or "EMAIL_TO" in str(e):
                logger.warning("Email not configured - testing scraping only")
                # Create monitor without email sender
                monitor = EANPriceMonitor.__new__(EANPriceMonitor)
                monitor.history_file = "ean_price_history.json"
                monitor.config_file = "ean_products.yaml"
                monitor.email_sender = None
                monitor.price_history = monitor._load_history()
                monitor.product_config = monitor._load_config()
                monitor.scrapers = {
                    "apteekki360": Apteekki360Scraper(),
                    "tokmanni": TokmanniScraper(),
                    "sinunapteekki": SinunapteekkiScraper(),
                    "ruohonjuuri": RuohonjuuriScraper(),
                }
            else:
                raise

        # Test scraping a single product
        products = monitor.product_config.get("products", [])
        if products:
            product = products[0]
            logger.info(f"Testing scrape for: {product.get('name')}")

            results = monitor.scrape_ean_product(product)

            if results:
                logger.info("✅ Scraping test passed")
                for store, data in results.items():
                    logger.info(
                        f"  {store}: €{data.get('current_price')} "
                        f"({'In Stock' if data.get('available') else 'Out of Stock'})"
                    )
            else:
                logger.error("❌ Scraping test failed - no results")

        return

    # Normal monitoring run
    try:
        monitor = EANPriceMonitor()
        success, price_drops = monitor.run_monitoring_cycle()

        if success:
            print("\n✅ EAN monitoring completed successfully")
            if price_drops:
                print(f"   Found {len(price_drops)} price drop(s)")
        else:
            print("\n❌ EAN monitoring failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
