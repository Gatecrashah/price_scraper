#!/usr/bin/env python3
"""
Björn Borg Sock Price Scraper
Scrapes multipack sock prices from bjornborg.com/fi
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BjornBorgScraper:
    def __init__(self):
        self.base_url = "https://www.bjornborg.com"
        self.target_url = "https://www.bjornborg.com/fi/men/socks-accessories/socks/?multipack=10-pack"
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            # Removed Accept-Encoding to avoid compression issues
        })
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and whitespace, find numbers
        price_match = re.search(r'(\d+[.,]\d+|\d+)', price_text.replace(',', '.'))
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        return None
    
    def parse_bjornborg_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse Björn Borg product page using known structure"""
        product_info = {}
        
        # Extract product name from text content (observed pattern)
        text_content = soup.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # Look for product name (usually near the beginning)
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['socks', 'pack']):
                if len(line) < 100 and not any(char.isdigit() for char in line[:10]):
                    product_info['name'] = line
                    break
        
        # Extract prices - improved to handle the actual page structure
        eur_prices = []
        for line in lines:
            if 'EUR' in line and any(char.isdigit() for char in line):
                # Look for price patterns like "35.96 EUR 44.95 EUR"
                price_matches = re.findall(r'(\d+[.,]\d+)\s*EUR', line)
                for match in price_matches:
                    try:
                        price = float(match.replace(',', '.'))
                        eur_prices.append(price)
                    except ValueError:
                        continue
        
        if eur_prices:
            # Remove duplicates and sort
            unique_prices = sorted(set(eur_prices))
            product_info['current_price'] = unique_prices[0]  # Lowest price is current
            if len(unique_prices) > 1:
                product_info['original_price'] = unique_prices[-1]  # Highest price is original
        
        # Look for discount percentage in the text
        for line in lines:
            if '%' in line and '-' in line:
                discount_match = re.search(r'-(\d+)%', line)
                if discount_match:
                    product_info['discount_percent'] = int(discount_match.group(1))
                    break
        
        # Extract item number - improved to handle the actual page structure
        for line in lines:
            if 'item number:' in line.lower():
                item_match = re.search(r'item number:\s*([A-Z0-9_]+)', line, re.IGNORECASE)
                if item_match:
                    # Clean up the item number (remove any extra text)
                    item_num = item_match.group(1)
                    # Remove anything after the expected pattern (like "Sign" etc.)
                    clean_item = re.match(r'(\d+_[A-Z0-9]+)', item_num)
                    if clean_item:
                        product_info['item_number'] = clean_item.group(1)
                    else:
                        product_info['item_number'] = item_num
                    break
        
        # Extract base product code from URL
        if url:
            url_parts = url.split('/')
            if len(url_parts) > 3:
                product_slug = url_parts[-2]
                base_match = re.search(r'(\d+)-mp\d+', product_slug)
                if base_match:
                    product_info['base_product_code'] = base_match.group(1)
        
        product_info['url'] = url
        product_info['product_id'] = self.extract_product_id(url, soup)
        
        return product_info if 'current_price' in product_info else None
    
    def scrape_product_page(self, product_url: str) -> Optional[Dict]:
        """Scrape individual product page for detailed info"""
        try:
            full_url = product_url if product_url.startswith('http') else self.base_url + product_url
            logger.info(f"Scraping product page: {full_url}")
            
            response = self.session.get(full_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try the specific Björn Borg parser first
            logger.debug(f"Trying parse_bjornborg_page for {full_url}")
            product_info = self.parse_bjornborg_page(soup, full_url)
            if product_info:
                logger.info(f"Successfully parsed product: {product_info.get('name', 'Unknown')}")
                return product_info
            else:
                logger.warning(f"parse_bjornborg_page returned None for {full_url}")
            
            # Fallback to generic parsing
            logger.debug("Trying fallback generic parsing")
            product_info = {}
            
            # Extract product name
            title_selectors = [
                'h1.product-name',
                'h1[data-testid="product-name"]',
                '.product-title h1',
                'h1.title',
                'h1',
                # Add more specific selectors based on actual page structure
                '.product-info h1',
                '[class*="product"] h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_info['name'] = title_elem.get_text(strip=True)
                    break
            
            # Extract current price
            price_selectors = [
                '.price-current',
                '.current-price',
                '[data-testid="current-price"]',
                '.price .current',
                '.price-box .price',
                '.price',
                # Add more specific selectors based on page structure
                'span:contains("EUR")',
                '[class*="price"]',
                'div:contains("EUR")'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self.extract_price(price_text)
                    if price:
                        product_info['current_price'] = price
                        product_info['price_text'] = price_text
                        break
            
            # Extract original price (if on sale)
            original_price_selectors = [
                '.price-original',
                '.original-price',
                '[data-testid="original-price"]',
                '.price .original',
                '.price-was'
            ]
            
            for selector in original_price_selectors:
                orig_price_elem = soup.select_one(selector)
                if orig_price_elem:
                    orig_price_text = orig_price_elem.get_text(strip=True)
                    orig_price = self.extract_price(orig_price_text)
                    if orig_price:
                        product_info['original_price'] = orig_price
                        break
            
            # Extract product ID from URL or page
            product_info['url'] = full_url
            product_info['product_id'] = self.extract_product_id(full_url, soup)
            
            return product_info if 'name' in product_info or 'current_price' in product_info else None
            
        except Exception as e:
            logger.error(f"Error scraping product page {product_url}: {e}")
            return None
    
    def extract_product_id(self, url: str, soup: BeautifulSoup) -> str:
        """Extract product ID from URL or page content"""
        # Try to extract from URL pattern like /product-name-12345-mp001/
        url_match = re.search(r'-(\d+)-mp\d+', url)
        if url_match:
            return url_match.group(1)
        
        # Try to find product ID in page data
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                # Look for product ID patterns in JSON
                id_match = re.search(r'"productId":\s*"?(\d+)"?', script.string)
                if id_match:
                    return id_match.group(1)
        
        # Fallback: use last part of URL
        return url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
    
    def scrape_main_page(self) -> List[Dict]:
        """Scrape the main multipack socks page"""
        try:
            logger.info(f"Scraping main page: {self.target_url}")
            response = self.session.get(self.target_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Common product link selectors for e-commerce sites - focus on actual sock products
            product_link_selectors = [
                'a[href*="/fi/"][href*="sock"]',  # Finnish sock products
                'a[href*="/fi/"][href*="-mp"]',   # Finnish multipack products
            ]
            
            product_links = set()
            
            for selector in product_link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Very strict filtering for Finnish sock multipack products
                        if (('/fi/' in href) and 
                            (any(keyword in href.lower() for keyword in ['sock', '-mp'])) and
                            # Exclude category pages, bags, and other non-sock products
                            not any(exclude in href.lower() for exclude in [
                                '/bags/', '/caps', '/beanie', '/accessories/', '/shoes/', 
                                '/underwear/', '/clothing/', 'backpack', '/socks-accessories/',
                                '/se/', '/no/', '/can_', '/au/', '/uk/', '/us/', '/de/', '/en/'
                            ]) and
                            # Must be an actual product page (has product ID pattern)
                            (re.search(r'-\d+-mp\d+', href) or 'sock' in href.lower())):
                            product_links.add(href)
            
            logger.info(f"Found {len(product_links)} potential product links")
            
            # If no product links found, try to extract from page source
            if not product_links:
                # Look for product data in script tags (common with SPAs)
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string and 'product' in script.string.lower():
                        # Try to find product URLs in JSON
                        url_matches = re.findall(r'["\'](/[^"\']*sock[^"\']*)["\']', script.string)
                        product_links.update(url_matches)
            
            # Scrape each product page (limit to Finnish products only)
            finnish_links = [link for link in list(product_links)[:20] if '/fi/' in link]
            logger.info(f"Found {len(product_links)} total links, {len(finnish_links)} Finnish links")
            
            for link in finnish_links:
                time.sleep(1)  # Be respectful with requests
                product_info = self.scrape_product_page(link)
                if product_info:
                    products.append(product_info)
            
            return products
            
        except Exception as e:
            logger.error(f"Error scraping main page: {e}")
            return []
    
    def scrape_known_products(self) -> List[Dict]:
        """Scrape known Essential 10-pack sock product URLs with backup variants"""
        # Essential socks 10-pack products - multiple variants for redundancy
        essential_urls = [
            "/fi/essential-socks-10-pack-10004564-mp001/",  # Main variant (Multi)
            "/fi/essential-socks-10-pack-10001228-mp001/",  # Backup variant 1
            "/fi/essential-socks-10-pack-10004085-mp001/",  # Backup variant 2
        ]
        
        logger.info(f"Attempting to scrape {len(essential_urls)} Essential 10-pack variants")
        
        products = []
        successful_urls = []
        failed_urls = []
        
        for url in essential_urls:
            time.sleep(1)  # Be respectful
            product_info = self.scrape_product_page(url)
            if product_info:
                # Ensure URL is always included for easy purchasing
                product_info['purchase_url'] = self.base_url + url if not url.startswith('http') else url
                logger.info(f"✅ Successfully scraped: {product_info.get('name', 'Unknown')} at {product_info.get('current_price', 'N/A')} EUR from {url}")
                products.append(product_info)
                successful_urls.append(url)
            else:
                logger.warning(f"❌ Failed to scrape product from {url}")
                failed_urls.append(url)
        
        # Log scraping health
        logger.info(f"Scraping health: {len(successful_urls)}/{len(essential_urls)} URLs successful")
        if failed_urls:
            logger.warning(f"Failed URLs: {failed_urls}")
        
        return products
    
    def scrape_all_products(self) -> List[Dict]:
        """Main scraping method - focused on Essential 10-pack only"""
        all_products = []
        
        # Only scrape our target Essential 10-pack products (no main page scraping)
        logger.info("Scraping Essential 10-pack products only (focused mode)")
        known_products = self.scrape_known_products()
        all_products.extend(known_products)
        logger.info(f"Found {len(known_products)} Essential 10-pack products")
        
        # Scraper health check
        if not known_products:
            logger.error("🚨 SCRAPER HEALTH ALERT: No Essential 10-pack products found!")
            logger.error("This could indicate:")
            logger.error("- Product URLs have changed")
            logger.error("- Website structure changed") 
            logger.error("- Anti-bot measures blocking access")
            logger.error("- Products out of stock or discontinued")
        
        # Remove duplicates based on base product code (keep best variant)
        seen_base_codes = set()
        seen_urls = set()
        unique_products = []
        
        for product in all_products:
            # Use base product code if available, otherwise fall back to URL
            base_code = product.get('base_product_code')
            url = product.get('url', '')
            
            # Create a unique identifier - prefer the first working variant
            if base_code:
                unique_id = f"base_{base_code}"
            else:
                unique_id = f"url_{url}"
            
            if unique_id not in seen_base_codes and url not in seen_urls:
                seen_base_codes.add(unique_id)
                seen_urls.add(url)
                unique_products.append(product)
            else:
                logger.info(f"Skipping duplicate Essential variant: {product.get('name', 'Unknown')} - {url}")
        
        logger.info(f"Found {len(all_products)} total Essential variants, {len(unique_products)} unique products to track")
        return unique_products

def main():
    """Main function to run the scraper"""
    scraper = BjornBorgScraper()
    
    print("Starting Björn Borg sock price scraper...")
    products = scraper.scrape_all_products()
    
    if products:
        print(f"\nFound {len(products)} products:")
        print("=" * 50)
        
        for product in products:
            print(f"Name: {product.get('name', 'Unknown')}")
            print(f"Current Price: {product.get('current_price', 'N/A')} EUR")
            if 'original_price' in product:
                print(f"Original Price: {product.get('original_price')} EUR")
            print(f"URL: {product.get('url', 'N/A')}")
            print(f"Product ID: {product.get('product_id', 'N/A')}")
            print("-" * 30)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"bjornborg_prices_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'products': products
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to {filename}")
    else:
        print("No products found. The website structure may have changed.")
        print("Manual inspection may be required.")

if __name__ == "__main__":
    main()