#!/usr/bin/env python3
"""
Main price monitoring script for Björn Borg socks
Combines scraping with email notifications and price history tracking
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Import our modules
from bjornborg_scraper import BjornBorgScraper, FitnesstukuScraper
from email_sender import EmailSender

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceMonitor:
    def __init__(self, history_file='price_history.json'):
        self.history_file = history_file
        self.bjornborg_scraper = BjornBorgScraper()
        self.fitnesstukku_scraper = FitnesstukuScraper()
        self.email_sender = EmailSender()
        self.price_history = self.load_price_history()
    
    def load_price_history(self) -> Dict:
        """Load price history from JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading price history: {e}")
                return {}
        return {}
    
    def save_price_history(self):
        """Save price history to JSON file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
            logger.info("Price history saved successfully")
        except Exception as e:
            logger.error(f"Error saving price history: {e}")
    
    def get_product_key(self, product: Dict) -> str:
        """Generate a unique key for a product using scraper-specific logic"""
        # Determine which scraper to use based on the product's site
        site = product.get('site', 'unknown')
        
        if site == 'bjornborg':
            return self.bjornborg_scraper.generate_product_key(product)
        elif site == 'fitnesstukku':
            return self.fitnesstukku_scraper.generate_product_key(product)
        else:
            # Fallback logic for unknown sites (maintain backward compatibility)
            if 'base_product_code' in product and product['base_product_code']:
                return f"base_{product['base_product_code']}"
            elif 'product_id' in product and product['product_id']:
                return f"id_{product['product_id']}"
            elif 'item_number' in product and product['item_number']:
                return f"item_{product['item_number']}"
            else:
                return f"url_{product.get('url', 'unknown')}"
    
    def scrape_all_sites(self) -> List[Dict]:
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
    
    def detect_price_changes(self, current_products: List[Dict]) -> List[Dict]:
        """Detect price changes compared to last scrape"""
        price_changes = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for product in current_products:
            product_key = self.get_product_key(product)
            current_price = product.get('current_price')
            
            if not current_price:
                continue
            
            # Initialize product history if it doesn't exist
            if product_key not in self.price_history:
                self.price_history[product_key] = {
                    'name': product.get('name', 'Unknown'),
                    'purchase_url': product.get('purchase_url', product.get('url', '')),
                    'price_history': {}
                }
            
            # Get previous price (most recent entry)
            price_hist = self.price_history[product_key]['price_history']
            previous_price = None
            
            if price_hist:
                # Get the most recent price (excluding today)
                sorted_dates = sorted(price_hist.keys(), reverse=True)
                for date in sorted_dates:
                    if date != today:
                        previous_price = price_hist[date].get('current_price')
                        break
            
            # Record today's price
            self.price_history[product_key]['price_history'][today] = {
                'current_price': current_price,
                'original_price': product.get('original_price'),
                'discount_percent': product.get('discount_percent'),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Update product info
            self.price_history[product_key]['name'] = product.get('name', self.price_history[product_key]['name'])
            self.price_history[product_key]['purchase_url'] = product.get('purchase_url', product.get('url', ''))
            
            # Check for price changes
            if previous_price is not None and abs(current_price - previous_price) > 0.01:  # Ignore tiny rounding differences
                logger.info(f"Price change detected for {product.get('name')}: {previous_price:.2f} → {current_price:.2f} EUR")
                
                price_changes.append({
                    'name': product.get('name', 'Unknown Product'),
                    'current_price': current_price,
                    'previous_price': previous_price,
                    'original_price': product.get('original_price'),
                    'discount_percent': product.get('discount_percent'),
                    'purchase_url': product.get('purchase_url', product.get('url', '')),
                    'change_date': today,
                    'product_key': product_key
                })
            else:
                logger.info(f"No price change for {product.get('name')}: {current_price:.2f} EUR")
        
        return price_changes
    
    def cleanup_old_history(self, days_to_keep=365):
        """Remove price history older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        total_removed = 0
        
        for product_key in self.price_history:
            price_hist = self.price_history[product_key]['price_history']
            dates_to_remove = [date for date in price_hist.keys() if date < cutoff_date]
            
            for date in dates_to_remove:
                del price_hist[date]
                total_removed += 1
        
        if total_removed > 0:
            logger.info(f"Cleaned up {total_removed} price history entries older than {days_to_keep} days")
    
    def get_price_summary(self, current_products: Optional[List[Dict]] = None) -> Dict:
        """Get a summary of current prices and trends"""
        # If current_products is provided, only show those in summary
        if current_products:
            current_product_keys = {self.get_product_key(p) for p in current_products}
        else:
            current_product_keys = None
        
        summary = {
            'total_products': len(self.price_history),
            'products': []
        }
        
        for product_key, product_data in self.price_history.items():
            # Skip products not in current run if we're filtering
            if current_product_keys and product_key not in current_product_keys:
                continue
                
            price_hist = product_data['price_history']
            if not price_hist:
                continue
            
            # Get latest price
            latest_date = max(price_hist.keys())
            latest_data = price_hist[latest_date]
            
            # Calculate trend (compare with 7 days ago)
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            trend = "stable"
            trend_change = 0
            
            if week_ago in price_hist:
                old_price = price_hist[week_ago]['current_price']
                current_price = latest_data['current_price']
                trend_change = current_price - old_price
                
                if abs(trend_change) > 0.01:
                    trend = "down" if trend_change < 0 else "up"
            
            summary['products'].append({
                'name': product_data['name'],
                'current_price': latest_data['current_price'],
                'original_price': latest_data.get('original_price'),
                'discount_percent': latest_data.get('discount_percent'),
                'purchase_url': product_data['purchase_url'],
                'trend': trend,
                'trend_change': trend_change,
                'last_updated': latest_date
            })
        
        # Update total count if we filtered
        if current_product_keys:
            summary['total_products'] = len(summary['products'])
        
        return summary
    
    def check_for_new_variants(self, discovery_frequency_days=7) -> List[Dict]:
        """Check for new Essential 10-pack variants with configurable frequency"""
        
        # Check when we last ran variant discovery
        last_discovery_file = 'last_variant_discovery.json'
        today = datetime.now()
        
        should_run_discovery = True
        
        if os.path.exists(last_discovery_file):
            try:
                with open(last_discovery_file, 'r') as f:
                    last_discovery_data = json.load(f)
                    last_discovery_date = datetime.fromisoformat(last_discovery_data['last_discovery_date'])
                    
                    days_since_last = (today - last_discovery_date).days
                    if days_since_last < discovery_frequency_days:
                        logger.info(f"Skipping variant discovery - only {days_since_last} days since last check (frequency: {discovery_frequency_days} days)")
                        should_run_discovery = False
            except Exception as e:
                logger.warning(f"Error reading last discovery file: {e}")
        
        if not should_run_discovery:
            return []
        
        logger.info("Running new variant discovery check...")
        
        try:
            # Run variant discovery (Björn Borg specific)
            new_variants = self.bjornborg_scraper.discover_new_variants()
            
            # Update last discovery timestamp
            with open(last_discovery_file, 'w') as f:
                json.dump({
                    'last_discovery_date': today.isoformat(),
                    'variants_found': len(new_variants)
                }, f, indent=2)
            
            return new_variants
            
        except Exception as e:
            logger.error(f"Error during variant discovery: {e}")
            return []
    
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
                error_details += "Please check the product pages manually and update the scraper if needed."
                
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
            
            # Check for new variants (configurable frequency - default weekly)
            new_variants = self.check_for_new_variants()
            
            # Send email notifications if there are price changes or new variants
            if price_changes or new_variants:
                if price_changes:
                    logger.info(f"Sending email notification for {len(price_changes)} price changes")
                if new_variants:
                    logger.info(f"Found {len(new_variants)} new variants to report")
                
                success = self.email_sender.send_price_alert(price_changes, new_variants)
                if success:
                    logger.info("Email notification sent successfully")
                else:
                    logger.error("Failed to send email notification")
            else:
                logger.info("No price changes or new variants detected - no email sent")
            
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
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logger.info("Running in test mode...")
        
        try:
            monitor = PriceMonitor()
            
            # Test scraping
            print("Testing scraper...")
            products = monitor.scrape_all_sites()
            if products:
                print(f"✅ Scraping test passed - found {len(products)} products")
                for product in products:
                    print(f"  - {product.get('name', 'Unknown')}: {product.get('current_price', 0):.2f} EUR")
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
            for product in summary['products']:
                trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}[product['trend']]
                print(f"  {trend_emoji} {product['name']}: {product['current_price']:.2f} EUR")
                if product.get('original_price'):
                    discount = ((product['original_price'] - product['current_price']) / product['original_price'] * 100)
                    print(f"      (was {product['original_price']:.2f} EUR, -{discount:.0f}% off)")
        else:
            print("❌ Monitoring cycle failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()