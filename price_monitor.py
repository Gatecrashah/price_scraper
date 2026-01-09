#!/usr/bin/env python3
"""
Main price monitoring script for Björn Borg socks
Combines scraping with email notifications and price history tracking
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta

import requests
import yaml

from email_sender import EmailSender

# Import our modules
from scrapers import BjornBorgScraper, FitnesstukkuScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PriceMonitor:
    def __init__(self, history_file="price_history.json", config_file="products.yaml"):
        self.history_file = history_file
        self.config_file = config_file
        self.bjornborg_scraper = BjornBorgScraper()
        self.fitnesstukku_scraper = FitnesstukkuScraper()
        self.email_sender = EmailSender()
        self.price_history = self.load_price_history()
        self.product_config = self.load_product_config()
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPOSITORY")

    def load_price_history(self) -> dict:
        """Load price history from JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading price history: {e}")
                return {}
        return {}

    def load_product_config(self) -> dict:
        """Load product config from YAML file."""
        if not os.path.exists(self.config_file):
            return {"products": {}}
        try:
            with open(self.config_file, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading {self.config_file}: {e}")
            return {"products": {}}

    def save_price_history(self):
        """Save price history to JSON file"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
            logger.info("Price history saved successfully")
        except Exception as e:
            logger.error(f"Error saving price history: {e}")

    def get_product_key(self, product: dict) -> str:
        """Generate a unique key for a product using scraper-specific logic"""
        # Determine which scraper to use based on the product's site
        site = product.get("site", "unknown")

        if site == "bjornborg":
            return self.bjornborg_scraper.generate_product_key(product)
        elif site == "fitnesstukku":
            return self.fitnesstukku_scraper.generate_product_key(product)
        else:
            # Fallback logic for unknown sites (maintain backward compatibility)
            if "base_product_code" in product and product["base_product_code"]:
                return f"base_{product['base_product_code']}"
            elif "product_id" in product and product["product_id"]:
                return f"id_{product['product_id']}"
            elif "item_number" in product and product["item_number"]:
                return f"item_{product['item_number']}"
            else:
                return f"url_{product.get('url', 'unknown')}"

    def scrape_all_sites(self) -> list[dict]:
        """Orchestrate scraping from all sites"""
        all_products = []

        logger.info("Orchestrating multi-site scraping...")

        # Scrape Björn Borg products
        logger.info("Scraping Björn Borg products...")
        try:
            bb_products = self.bjornborg_scraper.scrape_all_products()
            all_products.extend(bb_products)
            logger.info(f"Found {len(bb_products)} Björn Borg products")
        except Exception as e:
            logger.error(f"Error scraping Björn Borg: {e}")

        # Scrape Fitnesstukku products
        logger.info("Scraping Fitnesstukku products...")
        try:
            ft_products = self.fitnesstukku_scraper.scrape_all_products()
            all_products.extend(ft_products)
            logger.info(f"Found {len(ft_products)} Fitnesstukku products")
        except Exception as e:
            logger.error(f"Error scraping Fitnesstukku: {e}")

        logger.info(f"Total products scraped: {len(all_products)}")
        return all_products

    def detect_price_changes(self, current_products: list[dict]) -> list[dict]:
        """Detect price changes compared to last scrape (event-based format)"""
        price_changes = []
        today = datetime.now().strftime("%Y-%m-%d")

        for product in current_products:
            product_key = self.get_product_key(product)
            current_price = product.get("current_price")

            if not current_price:
                continue

            # Initialize product history if it doesn't exist
            if product_key not in self.price_history:
                self.price_history[product_key] = {
                    "name": product.get("name", "Unknown"),
                    "purchase_url": product.get("purchase_url", product.get("url", "")),
                    "current": None,
                    "all_time_lowest": None,
                    "price_changes": [],
                }

            product_history = self.price_history[product_key]

            # Ensure price_changes exists (for migrated data)
            if "price_changes" not in product_history:
                product_history["price_changes"] = []

            # Get previous price from current state
            previous_price = None
            if product_history.get("current"):
                previous_price = product_history["current"].get("price")

            # Update product info
            product_history["name"] = product.get("name", product_history["name"])
            product_history["purchase_url"] = product.get("purchase_url", product.get("url", ""))

            # Get all-time lowest for notifications
            all_time = product_history.get("all_time_lowest", {})
            lowest_price = all_time.get("price") if all_time else None
            lowest_price_date = all_time.get("date") if all_time else None

            # Format the lowest price date for display
            lowest_price_date_formatted = None
            if lowest_price_date:
                try:
                    lowest_price_date_formatted = datetime.strptime(
                        lowest_price_date, "%Y-%m-%d"
                    ).strftime("%b %d, %Y")
                except ValueError:
                    lowest_price_date_formatted = lowest_price_date

            # Check for price changes
            is_new = previous_price is None
            price_changed = (
                previous_price is not None and abs(current_price - previous_price) > 0.01
            )

            if is_new:
                # First time seeing this product - record initial price
                product_history["price_changes"].append(
                    {
                        "date": today,
                        "price": current_price,
                        "original_price": product.get("original_price"),
                        "discount_pct": product.get("discount_percent"),
                        "type": "initial",
                    }
                )
                logger.info(f"New product tracked: {product.get('name')}: {current_price:.2f} EUR")

            elif price_changed:
                # Price changed - record the change event
                change_pct = round(((current_price - previous_price) / previous_price) * 100, 1)
                product_history["price_changes"].append(
                    {
                        "date": today,
                        "from": previous_price,
                        "to": current_price,
                        "change_pct": change_pct,
                        "original_price": product.get("original_price"),
                        "discount_pct": product.get("discount_percent"),
                    }
                )

                logger.info(
                    f"Price change detected for {product.get('name')}: {previous_price:.2f} → {current_price:.2f} EUR"
                )

                price_changes.append(
                    {
                        "name": product.get("name", "Unknown Product"),
                        "current_price": current_price,
                        "previous_price": previous_price,
                        "original_price": product.get("original_price"),
                        "discount_percent": product.get("discount_percent"),
                        "purchase_url": product.get("purchase_url", product.get("url", "")),
                        "change_date": today,
                        "product_key": product_key,
                        "lowest_price": lowest_price,
                        "lowest_price_date": lowest_price_date_formatted,
                    }
                )
            else:
                logger.info(f"No price change for {product.get('name')}: {current_price:.2f} EUR")

            # Update current state
            product_history["current"] = {
                "price": current_price,
                "original_price": product.get("original_price"),
                "discount_pct": product.get("discount_percent"),
                "since": today
                if (is_new or price_changed)
                else product_history.get("current", {}).get("since", today),
            }

            # Update all-time lowest
            if lowest_price is None or current_price < lowest_price:
                product_history["all_time_lowest"] = {
                    "price": current_price,
                    "date": today,
                    "original_price": product.get("original_price"),
                }

        return price_changes

    def cleanup_old_history(self, days_to_keep=365):
        """Remove price change events older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        total_removed = 0

        for product_key in self.price_history:
            product_data = self.price_history[product_key]
            price_changes = product_data.get("price_changes", [])

            # Keep events newer than cutoff, but always keep the most recent one
            if len(price_changes) > 1:
                original_count = len(price_changes)
                # Filter out old events, but keep at least the last one
                new_changes = [e for e in price_changes if e.get("date", "") >= cutoff_date]

                # Always keep at least the most recent event for context
                if not new_changes and price_changes:
                    new_changes = [price_changes[-1]]

                product_data["price_changes"] = new_changes
                total_removed += original_count - len(new_changes)

        if total_removed > 0:
            logger.info(
                f"Cleaned up {total_removed} price change events older than {days_to_keep} days"
            )

    def get_price_summary(self, current_products: list[dict] | None = None) -> dict:
        """Get a summary of current prices and trends (event-based format)"""
        # If current_products is provided, only show those in summary
        if current_products:
            current_product_keys = {self.get_product_key(p) for p in current_products}
        else:
            current_product_keys = None

        summary = {"total_products": len(self.price_history), "products": []}

        for product_key, product_data in self.price_history.items():
            # Skip products not in current run if we're filtering
            if current_product_keys and product_key not in current_product_keys:
                continue

            current = product_data.get("current")
            if not current:
                continue

            # Calculate trend from recent price changes
            price_changes = product_data.get("price_changes", [])
            trend = "stable"
            trend_change = 0

            # Look at the most recent change to determine trend
            if len(price_changes) >= 2:
                last_change = price_changes[-1]
                if "from" in last_change and "to" in last_change:
                    trend_change = last_change["to"] - last_change["from"]
                    if abs(trend_change) > 0.01:
                        trend = "down" if trend_change < 0 else "up"

            summary["products"].append(
                {
                    "name": product_data["name"],
                    "current_price": current.get("price"),
                    "original_price": current.get("original_price"),
                    "discount_percent": current.get("discount_pct"),
                    "purchase_url": product_data.get("purchase_url", ""),
                    "trend": trend,
                    "trend_change": trend_change,
                    "last_updated": current.get("since"),
                }
            )

        # Update total count if we filtered
        if current_product_keys:
            summary["total_products"] = len(summary["products"])

        return summary

    def _get_open_discovery_issues(self) -> list[str]:
        """Gets the bodies of all open issues with the 'new-product' label to prevent duplicates."""
        if not self.github_token or not self.github_repo:
            logger.warning(
                "GITHUB_TOKEN or GITHUB_REPOSITORY not set. Cannot check for open issues."
            )
            return []

        url = (
            f"https://api.github.com/repos/{self.github_repo}/issues?state=open&labels=new-product"
        )
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return [issue["body"] for issue in response.json()]
        except Exception as e:
            logger.error(f"Failed to get open GitHub issues: {e}")
            return []

    def _create_github_issue(self, product: dict):
        """Creates a new GitHub issue for a discovered product."""
        if not self.github_token or not self.github_repo:
            logger.warning("GITHUB_TOKEN or GITHUB_REPOSITORY not set. Cannot create issue.")
            return

        name = product.get("name", "Unknown Product")
        title = f"New Product Discovery: {name}"

        # Embed product data in a JSON block for the action to parse
        product_data_for_issue = {
            "site": product.get("site", "bjornborg"),
            "url": product.get("url", "").replace("https://www.bjornborg.com", ""),
            "name": name,
            "current_price": product.get("current_price"),
        }

        body = f"""
A new product variant has been discovered. Please reply to this issue's notification email with a single word command.

- **To track this item:** Reply with `track`
- **To ignore this item:** Reply with `ignore`

### Product Details
- **Name**: {name}
- **Price**: {product.get("current_price")} EUR
- **URL**: {product.get("url")}

---
**For Automation (do not edit):**
```json
{json.dumps(product_data_for_issue, indent=2)}
```
"""

        issue_payload = {"title": title, "body": body, "labels": ["new-product"]}
        url = f"https://api.github.com/repos/{self.github_repo}/issues"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            response = requests.post(url, json=issue_payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Successfully created issue for {name}")
        except Exception as e:
            logger.error(f"Failed to create GitHub issue for {name}: {e}")

    def get_tracked_products(self) -> list[dict]:
        """Get list of products that should be tracked based on YAML config."""
        tracked_products = []
        for site_products in self.product_config.get("products", {}).values():
            for prod in site_products:
                if prod.get("status") == "track":
                    tracked_products.append(prod)
        return tracked_products

    def check_for_new_variants(self):
        """Discover new variants and create GitHub issues for them."""
        logger.info("🔍 Discovering new product variants...")

        # 1. Get all known product URLs from the config
        all_known_urls = set()
        for site_products in self.product_config.get("products", {}).values():
            for prod in site_products:
                all_known_urls.add(prod["url"])

        # 2. Get currently open discovery issues to avoid duplicates
        open_issue_bodies = self._get_open_discovery_issues()

        # 3. Scrape for products (Björn Borg specific for now)
        discovered_products = self.bjornborg_scraper.discover_new_variants()

        issues_created = 0
        for product in discovered_products:
            relative_url = product.get("url", "").replace(self.bjornborg_scraper.base_url, "")
            product["relative_url"] = relative_url

            # 4. Check if this product is truly new
            if relative_url in all_known_urls:
                continue  # Already in products.yaml

            if any(relative_url in body for body in open_issue_bodies):
                logger.info(
                    f"Skipping issue creation for {relative_url}, an open issue already exists."
                )
                continue  # Already has an open issue

            # 5. If truly new, create an issue
            logger.info(f"✨ Found new potential variant: {product.get('name')}")
            self._create_github_issue(product)
            issues_created += 1

        if issues_created > 0:
            logger.info(f"Created {issues_created} GitHub issues for new variants")
        else:
            logger.info("No new variants discovered")

    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle: scrape, compare, notify"""
        logger.info("Starting price monitoring cycle...")

        try:
            # Scrape current prices from all sites
            logger.info("Scraping current prices from all sites...")
            current_products = self.scrape_all_sites()

            if not current_products:
                logger.warning("No products found during scraping")

                # Send failure alert email
                error_details = "No Essential 10-pack products were found during scraping.\n\n"
                error_details += "This likely means:\n"
                error_details += "- Product URLs have changed or are no longer valid\n"
                error_details += "- Website structure has been updated\n"
                error_details += "- Products are out of stock or discontinued\n"
                error_details += "- Anti-bot measures are blocking access\n\n"
                error_details += (
                    "Please check the product pages manually and update the scraper if needed."
                )

                logger.info("Sending scraper failure alert email...")
                alert_sent = self.email_sender.send_scraper_failure_alert(error_details)
                if alert_sent:
                    logger.info("Failure alert email sent successfully")
                else:
                    logger.error("Failed to send failure alert email")

                return False, []

            logger.info(f"Successfully scraped {len(current_products)} products")

            # Detect price changes
            price_changes = self.detect_price_changes(current_products)

            # Save updated price history
            self.save_price_history()

            # Check for new variants and create GitHub issues (configurable frequency - default weekly)
            self.check_for_new_variants()

            # Send email notifications only for price changes
            if price_changes:
                logger.info(f"Sending email notification for {len(price_changes)} price changes")
                success = self.email_sender.send_price_alert(price_changes)
                if success:
                    logger.info("Email notification sent successfully")
                else:
                    logger.error("Failed to send email notification")
            else:
                logger.info("No price changes detected - no email sent")

            # Cleanup old history
            self.cleanup_old_history()

            logger.info("Monitoring cycle completed successfully")
            return True, current_products

        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")
            return False, []


def main():
    """Main function"""
    logger.info("Björn Borg Sock Price Monitor starting...")

    # Check if this is a test run
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Running in test mode...")

        try:
            monitor = PriceMonitor()

            # Test scraping
            print("Testing scraper...")
            products = monitor.scrape_all_sites()
            if products:
                print(f"✅ Scraping test passed - found {len(products)} products")
                for product in products:
                    print(
                        f"  - {product.get('name', 'Unknown')}: {product.get('current_price', 0):.2f} EUR"
                    )
                    print(f"    URL: {product.get('purchase_url', product.get('url', 'N/A'))}")
            else:
                print("❌ Scraping test failed - no products found")
                return

            # Test email
            print("\nTesting email notifications...")
            test_email = EmailSender()
            if test_email.send_test_email():
                print("✅ Email test passed")
            else:
                print("❌ Email test failed")

        except Exception as e:
            print(f"❌ Test failed: {e}")

        return

    # Normal monitoring run
    try:
        monitor = PriceMonitor()
        success, current_products = monitor.run_monitoring_cycle()

        if success:
            print("✅ Monitoring cycle completed successfully")

            # Print summary - only show currently tracked products
            summary = monitor.get_price_summary(current_products=current_products)
            print(f"\n📊 Price Summary ({summary['total_products']} products tracked):")
            for product in summary["products"]:
                trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}[product["trend"]]
                print(f"  {trend_emoji} {product['name']}: {product['current_price']:.2f} EUR")
                if product.get("original_price"):
                    discount = (
                        (product["original_price"] - product["current_price"])
                        / product["original_price"]
                        * 100
                    )
                    print(f"      (was {product['original_price']:.2f} EUR, -{discount:.0f}% off)")
        else:
            print("❌ Monitoring cycle failed")
            exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
