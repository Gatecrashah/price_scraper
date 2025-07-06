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
        
        # Extract product name - improved to handle both socks and other products
        # First try to get from page title
        title_elem = soup.find('title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Extract product name from title like "Centre Crew - Peat | Björn Borg"
            if ' | Björn Borg' in title_text:
                product_name = title_text.split(' | Björn Borg')[0]
                # Remove color variations like "- Peat"
                if ' - ' in product_name:
                    product_name = product_name.split(' - ')[0]
                product_info['name'] = product_name
        
        # Fallback: extract from text content (for socks and packs)
        if 'name' not in product_info:
            text_content = soup.get_text()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            # Look for product name (usually near the beginning)
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['socks', 'pack', 'crew', 'sweater']):
                    if len(line) < 100 and not any(char.isdigit() for char in line[:10]):
                        product_info['name'] = line
                        break
        
        # Extract prices - improved to handle the actual page structure
        text_content = soup.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
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
        """Scrape the main multipack socks page for Essential 10-pack products"""
        try:
            logger.info(f"Scraping main page for Essential 10-pack variants: {self.target_url}")
            response = self.session.get(self.target_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Enhanced selectors specifically for Essential 10-pack products
            product_link_selectors = [
                'a[href*="/fi/"][href*="essential"][href*="10-pack"]',  # Direct essential 10-pack matches
                'a[href*="/fi/"][href*="sock"][href*="-mp"]',          # Finnish sock multipack products
                'a[href*="/fi/"][href*="-mp001"]',                     # Specific multipack pattern
            ]
            
            product_links = set()
            
            for selector in product_link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and self._is_essential_10pack_variant(href):
                        product_links.add(href)
            
            # Also search in script tags for dynamic content
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'essential' in script.string.lower() and '10-pack' in script.string.lower():
                    # Try to find Essential 10-pack URLs in JSON/JavaScript
                    url_matches = re.findall(r'["\'](/[^"\']*essential[^"\']*10-pack[^"\']*)["\']', script.string, re.IGNORECASE)
                    for url_match in url_matches:
                        if self._is_essential_10pack_variant(url_match):
                            product_links.add(url_match)
            
            logger.info(f"Found {len(product_links)} Essential 10-pack variant links")
            
            # Filter for unique Essential 10-pack products only
            essential_links = []
            for link in product_links:
                # Ensure it's a full URL
                if not link.startswith('http'):
                    link = self.base_url + link if not link.startswith('/') else self.base_url + link
                essential_links.append(link)
            
            logger.info(f"Processing {len(essential_links)} Essential 10-pack URLs")
            
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
    
    def _is_essential_10pack_variant(self, href: str) -> bool:
        """Helper method to identify Essential 10-pack variant URLs"""
        if not href:
            return False
        
        href_lower = href.lower()
        
        # Must be Finnish site
        if '/fi/' not in href_lower:
            return False
        
        # Must contain essential and 10-pack or mp (multipack) patterns
        has_essential = 'essential' in href_lower
        has_pack_indicator = any(pattern in href_lower for pattern in [
            '10-pack', 
            '-mp001',  # Standard multipack suffix
            'multipack',
            'socks'
        ])
        
        # Must be a product page, not category or other pages
        is_product_page = not any(exclude in href_lower for exclude in [
            '/category',
            '/search',
            '/filter',
            '/sort',
            '?',
            '#'
        ])
        
        # Additional check for Essential sock patterns
        has_sock_patterns = any(pattern in href_lower for pattern in [
            'essential-socks',
            'essential-sock',
            'essentials-sock'
        ])
        
        return (has_essential and has_pack_indicator and is_product_page) or has_sock_patterns
    
    def discover_new_variants(self) -> List[Dict]:
        """Discover new Essential 10-pack variants not in our tracking list"""
        logger.info("🔍 Discovering new Essential 10-pack variants...")
        
        # Get current tracked Essential products
        tracked_urls = {
            "/fi/essential-socks-10-pack-10004564-mp001/",
            "/fi/essential-socks-10-pack-10001228-mp001/", 
            "/fi/essential-socks-10-pack-10004085-mp001/"
        }
        
        # Scrape main page for all Essential variants
        discovered_products = self.scrape_main_page()
        
        # Filter out already tracked variants
        new_variants = []
        for product in discovered_products:
            product_url = product.get('url', '')
            # Extract relative URL for comparison
            if product_url.startswith(self.base_url):
                relative_url = product_url[len(self.base_url):]
            else:
                relative_url = product_url
                
            if relative_url not in tracked_urls:
                new_variants.append({
                    'name': product.get('name', 'Unknown Essential Variant'),
                    'url': product_url,
                    'current_price': product.get('current_price'),
                    'original_price': product.get('original_price'),
                    'discount_percent': product.get('discount_percent'),
                    'product_id': product.get('product_id'),
                    'base_product_code': product.get('base_product_code'),
                    'discovery_date': datetime.now().isoformat()
                })
        
        if new_variants:
            logger.info(f"✨ Found {len(new_variants)} new Essential 10-pack variants!")
            for variant in new_variants:
                logger.info(f"   - {variant['name']}: {variant.get('current_price', 'N/A')} EUR")
                logger.info(f"     URL: {variant['url']}")
        else:
            logger.info("No new Essential variants discovered")
        
        return new_variants
    
    def scrape_known_products(self) -> List[Dict]:
        """Scrape known products from both Björn Borg and Fitnesstukku"""
        all_products = []
        
        # Björn Borg Essential products
        bjornborg_urls = [
            "/fi/essential-socks-10-pack-10004564-mp001/",  # Main variant (Multi)
            "/fi/essential-socks-10-pack-10001228-mp001/",  # Backup variant 1
            "/fi/essential-socks-10-pack-10004085-mp001/",  # Backup variant 2
            "/fi/centre-crew-9999-1431-gy013/", # color 1
            "/fi/centre-crew-9999-1431-bl183/", # color 2
            "/fi/centre-crew-9999-1431-90741/", # centre sweatshirt color 3
        ]
        
        # Fitnesstukku products (full URLs)
        fitnesstukku_urls = [
            "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html",
            "https://www.fitnesstukku.fi/creatine-monohydrate-500-g/609.html"
        ]
        
        # Scrape Björn Borg products
        logger.info(f"Attempting to scrape {len(bjornborg_urls)} Björn Borg products")
        successful_bb_urls = []
        failed_bb_urls = []
        
        for url in bjornborg_urls:
            time.sleep(1)  # Be respectful
            product_info = self.scrape_product_page(url)
            if product_info:
                # Ensure URL is always included for easy purchasing
                product_info['purchase_url'] = self.base_url + url if not url.startswith('http') else url
                product_info['site'] = 'bjornborg'
                logger.info(f"✅ Successfully scraped: {product_info.get('name', 'Unknown')} at {product_info.get('current_price', 'N/A')} EUR from {url}")
                all_products.append(product_info)
                successful_bb_urls.append(url)
            else:
                logger.warning(f"❌ Failed to scrape Björn Borg product from {url}")
                failed_bb_urls.append(url)
        
        # Log Björn Borg scraping health
        logger.info(f"Björn Borg scraping health: {len(successful_bb_urls)}/{len(bjornborg_urls)} URLs successful")
        if failed_bb_urls:
            logger.warning(f"Failed Björn Borg URLs: {failed_bb_urls}")
        
        # Scrape Fitnesstukku products
        logger.info(f"Attempting to scrape {len(fitnesstukku_urls)} Fitnesstukku products")
        fitnesstukku_scraper = FitnesstukuScraper()
        fitnesstukku_products = fitnesstukku_scraper.scrape_fitnesstukku_products(fitnesstukku_urls)
        all_products.extend(fitnesstukku_products)
        
        # Overall health summary
        total_expected = len(bjornborg_urls) + len(fitnesstukku_urls)
        total_successful = len(successful_bb_urls) + len(fitnesstukku_products)
        logger.info(f"🎯 Overall scraping health: {total_successful}/{total_expected} products successful")
        logger.info(f"   - Björn Borg: {len(successful_bb_urls)}/{len(bjornborg_urls)}")
        logger.info(f"   - Fitnesstukku: {len(fitnesstukku_products)}/{len(fitnesstukku_urls)}")
        
        return all_products
    
    def scrape_all_products(self) -> List[Dict]:
        """Main scraping method - handles both Björn Borg and Fitnesstukku products"""
        all_products = []
        
        # Scrape products from both sites
        logger.info("Scraping products from Björn Borg and Fitnesstukku")
        known_products = self.scrape_known_products()
        all_products.extend(known_products)
        logger.info(f"Found {len(known_products)} products across all sites")
        
        # Scraper health check
        if not known_products:
            logger.error("🚨 SCRAPER HEALTH ALERT: No products found from any site!")
            logger.error("This could indicate:")
            logger.error("- Product URLs have changed")
            logger.error("- Website structures changed") 
            logger.error("- Anti-bot measures blocking access")
            logger.error("- Products out of stock or discontinued")
        
        # Remove duplicates based on base product code (keep best variant)
        seen_base_codes = set()
        seen_urls = set()
        unique_products = []
        
        for product in all_products:
            # Use base product code if available, otherwise fall back to URL
            base_code = product.get('base_product_code')
            # Handle both 'url' (Björn Borg) and 'purchase_url' (Fitnesstukku) fields
            url = product.get('url', '') or product.get('purchase_url', '')
            
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
                logger.info(f"Skipping duplicate product: {product.get('name', 'Unknown')} - {url}")
        
        logger.info(f"Found {len(all_products)} total Essential variants, {len(unique_products)} unique products to track")
        return unique_products

class FitnesstukuScraper:
    def __init__(self):
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_fitnesstukku_product(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract product information from Fitnesstukku page"""
        
        product_info = {
            'purchase_url': url,
            'site': 'fitnesstukku'
        }
        
        try:
            # Extract product name
            name_selectors = [
                'h1.product-name',
                'h1[data-testid="product-name"]', 
                '.pdp-product-name h1',
                'h1',
                '.product-title',
                '[data-automation-id="product-title"]'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product_info['name'] = name_elem.get_text(strip=True)
                    break
            
            # Extract brand if available
            brand_selectors = [
                '.product-brand',
                '.brand-name', 
                '[data-automation-id="product-brand"]',
                'a[href*="kaikkituotemerkit"]'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    product_info['brand'] = brand_elem.get_text(strip=True)
                    break
            
            # Extract current price
            price_selectors = [
                '.price-sales',
                '.price .current',
                '.current-price',
                '[data-automation-id="current-price"]',
                '.price-current'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    
                    # Extract numeric price from text like "22.90 €"
                    price_match = re.search(r'(\d+[.,]\d+)', price_text.replace(',', '.'))
                    if price_match:
                        try:
                            current_price = float(price_match.group(1))
                            product_info['current_price'] = current_price
                            break
                        except ValueError:
                            continue
            
            # Extract original/list price if available
            original_price_selectors = [
                '.price-ref__stmt--list .price__value',
                '.price-original',
                '.list-price',
                '.price-was',
                '[data-automation-id="list-price"]'
            ]
            
            for selector in original_price_selectors:
                orig_price_elem = soup.select_one(selector)
                if orig_price_elem:
                    orig_price_text = orig_price_elem.get_text(strip=True)
                    
                    orig_price_match = re.search(r'(\d+[.,]\d+)', orig_price_text.replace(',', '.'))
                    if orig_price_match:
                        try:
                            original_price = float(orig_price_match.group(1))
                            # Only set if different from current price
                            if original_price != product_info.get('current_price'):
                                product_info['original_price'] = original_price
                            break
                        except ValueError:
                            continue
            
            # Calculate discount if we have both prices
            if 'current_price' in product_info and 'original_price' in product_info:
                current = product_info['current_price']
                original = product_info['original_price']
                if original > current:
                    discount_pct = round(((original - current) / original) * 100)
                    product_info['discount_percent'] = discount_pct
            
            # Generate a product ID for tracking
            url_parts = url.split('/')
            if len(url_parts) > 1:
                product_slug = url_parts[-1].replace('.html', '')
                product_info['product_id'] = f"fitnesstukku_{product_slug}"
            
            return product_info if 'current_price' in product_info else None
            
        except Exception as e:
            logger.error(f"Error extracting Fitnesstukku product data: {e}")
            return None
    
    def scrape_fitnesstukku_products(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple Fitnesstukku product URLs"""
        products = []
        successful_urls = []
        failed_urls = []
        
        for url in urls:
            time.sleep(1)  # Be respectful
            
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"❌ Failed to fetch Fitnesstukku page: HTTP {response.status_code} - {url}")
                    failed_urls.append(url)
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                product_info = self.extract_fitnesstukku_product(soup, url)
                
                if product_info:
                    logger.info(f"✅ Successfully scraped: {product_info.get('name', 'Unknown')} at {product_info.get('current_price', 'N/A')} EUR from {url}")
                    products.append(product_info)
                    successful_urls.append(url)
                else:
                    logger.warning(f"❌ Failed to extract product info from {url}")
                    failed_urls.append(url)
                    
            except Exception as e:
                logger.error(f"❌ Error scraping Fitnesstukku {url}: {e}")
                failed_urls.append(url)
        
        # Log scraping health
        logger.info(f"Fitnesstukku scraping health: {len(successful_urls)}/{len(urls)} URLs successful")
        if failed_urls:
            logger.warning(f"Failed Fitnesstukku URLs: {failed_urls}")
        
        return products

def main():
    """Main function to run the multi-site scraper"""
    scraper = BjornBorgScraper()
    
    print("Starting multi-site price scraper (Björn Borg + Fitnesstukku)...")
    products = scraper.scrape_all_products()
    
    if products:
        # Group products by site for better display
        bjornborg_products = [p for p in products if p.get('site') == 'bjornborg']
        fitnesstukku_products = [p for p in products if p.get('site') == 'fitnesstukku']
        
        print(f"\nFound {len(products)} products across all sites:")
        print("=" * 60)
        
        if bjornborg_products:
            print(f"\n🧦 BJÖRN BORG ({len(bjornborg_products)} products):")
            print("-" * 40)
            for product in bjornborg_products:
                print(f"Name: {product.get('name', 'Unknown')}")
                print(f"Current Price: {product.get('current_price', 'N/A')} EUR")
                if 'original_price' in product:
                    print(f"Original Price: {product.get('original_price')} EUR")
                print(f"URL: {product.get('purchase_url', 'N/A')}")
                print(f"Product ID: {product.get('product_id', 'N/A')}")
                print("-" * 30)
        
        if fitnesstukku_products:
            print(f"\n💪 FITNESSTUKKU ({len(fitnesstukku_products)} products):")
            print("-" * 40)
            for product in fitnesstukku_products:
                print(f"Name: {product.get('name', 'Unknown')}")
                print(f"Current Price: {product.get('current_price', 'N/A')} EUR")
                if 'original_price' in product:
                    print(f"Original Price: {product.get('original_price')} EUR")
                if 'brand' in product:
                    print(f"Brand: {product.get('brand')}")
                print(f"URL: {product.get('purchase_url', 'N/A')}")
                print(f"Product ID: {product.get('product_id', 'N/A')}")
                print("-" * 30)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"multisite_prices_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'products': products,
                'summary': {
                    'total_products': len(products),
                    'bjornborg_products': len(bjornborg_products),
                    'fitnesstukku_products': len(fitnesstukku_products)
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to {filename}")
    else:
        print("No products found. The website structures may have changed.")
        print("Manual inspection may be required.")

if __name__ == "__main__":
    main()