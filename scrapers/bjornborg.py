#!/usr/bin/env python3
"""
Robust Björn Borg scraper using structured data prioritization.

This scraper prioritizes JSON-LD structured data extraction over brittle text parsing,
making it much more resilient to website changes.
"""

import json
import time
import re
import yaml
from datetime import datetime
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class BjornBorgScraper(BaseScraper):
    """Improved Björn Borg scraper with structured data prioritization."""
    
    def __init__(self):
        super().__init__("https://www.bjornborg.com")
        self.target_url = "https://www.bjornborg.com/fi/men/socks-accessories/socks/?multipack=10-pack"
    
    def extract_structured_data(self, soup, url: str) -> Optional[Dict]:
        """Extract product information from JSON-LD structured data."""
        try:
            # Extract JSON-LD Product schema
            product_schema = self.extract_json_ld(soup, "Product")
            
            if not product_schema:
                logger.debug("No JSON-LD Product schema found")
                return None
            
            product_info = {
                'url': url,
                'site': 'bjornborg'
            }
            
            # Extract basic product information
            product_info['name'] = product_schema.get('name', '').strip()
            
            # Extract pricing information from offers
            offers = product_schema.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    try:
                        product_info['current_price'] = float(price)
                    except (ValueError, TypeError):
                        pass
                
                # Extract availability
                availability = offers.get('availability', '')
                if 'InStock' in availability:
                    product_info['in_stock'] = True
                elif 'OutOfStock' in availability:
                    product_info['in_stock'] = False
            
            # Extract SKU for product identification
            sku = product_schema.get('sku', '')
            if sku:
                product_info['sku'] = sku
                # Extract base product code from SKU (e.g., "10004564_MP001" -> "10004564")
                sku_match = re.match(r'(\d+)_', sku)
                if sku_match:
                    product_info['base_product_code'] = sku_match.group(1)
            
            # Extract brand information
            brand = product_schema.get('brand')
            if isinstance(brand, dict):
                product_info['brand'] = brand.get('name', 'BJÖRN BORG')
            
            # Extract color and material
            if 'color' in product_schema:
                product_info['color'] = product_schema['color']
            if 'material' in product_schema:
                product_info['material'] = product_schema['material']
            
            # Extract ratings if available
            rating = product_schema.get('aggregateRating')
            if isinstance(rating, dict):
                product_info['rating'] = rating.get('ratingValue')
                product_info['review_count'] = rating.get('reviewCount')
            
            # Extract product ID from URL as fallback
            if 'product_id' not in product_info:
                product_info['product_id'] = self.extract_product_id_from_url(url)
            
            # Try to extract original price from HTML selectors if not in structured data
            if 'original_price' not in product_info:
                original_price_selectors = [
                    '[data-testid="original-price"]',
                    '.price-original',
                    '.original-price',
                    '.price .original',
                ]
                
                for selector in original_price_selectors:
                    orig_elem = soup.select_one(selector)
                    if orig_elem:
                        orig_price_text = orig_elem.get_text(strip=True)
                        orig_price = self.extract_price(orig_price_text)
                        if orig_price and orig_price != product_info.get('current_price'):
                            product_info['original_price'] = orig_price
                            break
            
            # Calculate discount percentage if we have both prices
            if product_info.get('original_price') and product_info.get('current_price'):
                original = product_info['original_price']
                current = product_info['current_price']
                if original > current:
                    discount_percent = round(((original - current) / original) * 100)
                    product_info['discount_percent'] = discount_percent
            
            # Only return if we have essential information
            if product_info.get('name') and product_info.get('current_price'):
                logger.debug(f"Successfully extracted structured data for: {product_info['name']}")
                return product_info
            else:
                logger.debug("Structured data missing essential fields (name or price)")
                return None
                
        except Exception as e:
            logger.debug(f"Error extracting structured data: {e}")
            return None
    
    def extract_fallback_data(self, soup, url: str) -> Optional[Dict]:
        """Extract product data using robust CSS selectors as fallback."""
        try:
            product_info = {
                'url': url,
                'site': 'bjornborg'
            }
            
            # Extract product name using specific selectors
            name_selectors = [
                'h1[data-testid="product-name"]',
                '.product-name h1',
                '.pdp-product-name',
                'h1.product-title',
                'title',  # Last resort from page title
            ]
            
            for selector in name_selectors:
                if selector == 'title':
                    title_elem = soup.find('title')
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        if ' | Björn Borg' in title_text:
                            product_name = title_text.split(' | Björn Borg')[0]
                            # Remove color variations like "- Peat"
                            if ' - ' in product_name:
                                product_name = product_name.split(' - ')[0]
                            product_info['name'] = product_name
                            break
                else:
                    name_elem = soup.select_one(selector)
                    if name_elem:
                        product_info['name'] = name_elem.get_text(strip=True)
                        break
            
            # Extract price using specific selectors
            price_selectors = [
                '[data-testid="current-price"]',
                '.price-current',
                '.current-price',
                '.price .current',
                '.product-price .current',
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self.extract_price(price_text)
                    if price:
                        product_info['current_price'] = price
                        break
            
            # If specific selectors fail, try finding EUR prices in script tags
            if 'current_price' not in product_info:
                price = self._extract_price_from_scripts(soup)
                if price:
                    product_info['current_price'] = price
            
            # Extract original price
            original_price_selectors = [
                '[data-testid="original-price"]',
                '.price-original',
                '.original-price',
                '.price .original',
            ]
            
            for selector in original_price_selectors:
                orig_elem = soup.select_one(selector)
                if orig_elem:
                    orig_price_text = orig_elem.get_text(strip=True)
                    orig_price = self.extract_price(orig_price_text)
                    if orig_price and orig_price != product_info.get('current_price'):
                        product_info['original_price'] = orig_price
                        break
            
            # Extract product ID
            product_info['product_id'] = self.extract_product_id_from_url(url)
            
            # Extract base product code from URL
            base_code = self._extract_base_product_code(url)
            if base_code:
                product_info['base_product_code'] = base_code
            
            # Calculate discount percentage if we have both prices
            if product_info.get('original_price') and product_info.get('current_price'):
                original = product_info['original_price']
                current = product_info['current_price']
                if original > current:
                    discount_percent = round(((original - current) / original) * 100)
                    product_info['discount_percent'] = discount_percent
            
            # Only return if we have essential information
            if product_info.get('name') and product_info.get('current_price'):
                logger.debug(f"Successfully extracted fallback data for: {product_info['name']}")
                return product_info
            else:
                logger.debug("Fallback extraction missing essential fields")
                return None
                
        except Exception as e:
            logger.debug(f"Error in fallback extraction: {e}")
            return None
    
    def _extract_price_from_scripts(self, soup) -> Optional[float]:
        """Extract price from script tags as last resort."""
        try:
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'EUR' in script.string:
                    # Look for price patterns like "price": 35.96
                    price_matches = re.findall(r'"price":\s*(\d+\.?\d*)', script.string)
                    for match in price_matches:
                        try:
                            return float(match)
                        except ValueError:
                            continue
            return None
        except Exception:
            return None
    
    def _extract_base_product_code(self, url: str) -> Optional[str]:
        """Extract base product code from URL pattern."""
        base_match = re.search(r'-(\d+)-mp\d+', url)
        return base_match.group(1) if base_match else None
    
    def extract_product_id_from_url(self, url: str) -> str:
        """Extract product ID from URL pattern."""
        # Try to extract from URL pattern like /product-name-12345-mp001/
        url_match = re.search(r'-(\d+)-mp\d+', url)
        if url_match:
            return url_match.group(1)
        
        # Fallback: use last part of URL
        return url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
    
    def generate_product_key(self, product: Dict) -> str:
        """Generate a unique key for a Björn Borg product."""
        # Use base product code if available (for socks - groups variants together)
        if 'base_product_code' in product and product['base_product_code']:
            return f"base_{product['base_product_code']}"
        # Use product_id for individual items (for Centre Crew variants)
        elif 'product_id' in product and product['product_id']:
            return f"id_{product['product_id']}"
        # Fallback to SKU
        elif 'sku' in product and product['sku']:
            return f"sku_{product['sku']}"
        # Last resort: use URL
        else:
            url = product.get('url', 'unknown')
            return f"url_{url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]}"
    
    def get_product_urls(self) -> List[str]:
        """Get Björn Borg product URLs from products.yaml configuration."""
        try:
            with open('products.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            if not config:
                raise ValueError("products.yaml is empty or invalid")
                
            products = config.get('products', {})
            if not products:
                raise KeyError("'products' section missing from products.yaml")
                
            bjornborg_products = products.get('bjornborg', [])
            if not bjornborg_products:
                raise KeyError("No Björn Borg products found in products.yaml")
                
            # Only return URLs for products with status 'track'
            tracked_urls = []
            for product in bjornborg_products:
                if product.get('status') == 'track':
                    tracked_urls.append(product['url'])
                    
            if not tracked_urls:
                raise ValueError("No Björn Borg products are marked for tracking in products.yaml")
                
            return tracked_urls
            
        except FileNotFoundError:
            raise FileNotFoundError(
                "products.yaml configuration file not found. "
                "This file is required for the scraper to know which products to monitor."
            )
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse products.yaml: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load Björn Borg URLs from products.yaml: {e}")
    
    def scrape_all_products(self) -> List[Dict]:
        """Scrape all tracked Björn Borg products."""
        all_products = []
        
        try:
            bjornborg_urls = self.get_product_urls()
            logger.info(f"Attempting to scrape {len(bjornborg_urls)} Björn Borg products")
            
            successful_urls = []
            failed_urls = []
            
            for url in bjornborg_urls:
                time.sleep(1)  # Be respectful with requests
                product_info = self.scrape_product_page(url)
                
                if product_info:
                    # Ensure URL is always included for easy purchasing
                    product_info['purchase_url'] = self.base_url + url if not url.startswith('http') else url
                    product_info['site'] = 'bjornborg'
                    
                    logger.info(f"✅ Successfully scraped: {product_info.get('name', 'Unknown')} at {product_info.get('current_price', 'N/A')} EUR from {url}")
                    all_products.append(product_info)
                    successful_urls.append(url)
                else:
                    logger.warning(f"❌ Failed to scrape Björn Borg product from {url}")
                    failed_urls.append(url)
            
            # Log scraping health
            logger.info(f"Björn Borg scraping health: {len(successful_urls)}/{len(bjornborg_urls)} URLs successful")
            if failed_urls:
                logger.warning(f"Failed Björn Borg URLs: {failed_urls}")
            
            return all_products
            
        except Exception as e:
            logger.error(f"Error in scrape_all_products: {e}")
            return []
    
    def discover_new_variants(self) -> List[Dict]:
        """Discover new Essential 10-pack variants using structured data."""
        logger.info("🔍 Discovering new Essential 10-pack variants...")
        
        try:
            # Get current tracked products from products.yaml
            with open('products.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            if not config:
                raise ValueError("products.yaml is empty or invalid")
                
            products = config.get('products', {})
            if not products:
                raise KeyError("'products' section missing from products.yaml")
                
            bjornborg_products = products.get('bjornborg', [])
            if not bjornborg_products:
                raise KeyError("No Björn Borg products found in products.yaml")
                
            # Extract tracked URLs from config
            tracked_urls = set()
            for product in bjornborg_products:
                url = product.get('url', '')
                # Ensure consistent URL format (relative path)
                if url.startswith('https://www.bjornborg.com'):
                    relative_url = url[len('https://www.bjornborg.com'):]
                elif url.startswith(self.base_url):
                    relative_url = url[len(self.base_url):]
                else:
                    relative_url = url
                tracked_urls.add(relative_url)
                
        except FileNotFoundError:
            raise FileNotFoundError(
                "products.yaml configuration file not found. "
                "This file is required for variant discovery to know which products are already tracked."
            )
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse products.yaml: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load tracked products from products.yaml: {e}")
        
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
                    'discovery_date': datetime.now().isoformat(),
                    'site': 'bjornborg'
                })
        
        if new_variants:
            logger.info(f"✨ Found {len(new_variants)} new Essential 10-pack variants!")
            for variant in new_variants:
                logger.info(f"   - {variant['name']}: {variant.get('current_price', 'N/A')} EUR")
                logger.info(f"     URL: {variant['url']}")
        else:
            logger.info("No new Essential variants discovered")
        
        return new_variants
    
    def scrape_main_page(self) -> List[Dict]:
        """Scrape the main multipack socks page for Essential 10-pack products."""
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
                    url_matches = re.findall(r'["\']([^"\']*essential[^"\']*10-pack[^"\']*)["\']', script.string, re.IGNORECASE)
                    for url_match in url_matches:
                        if self._is_essential_10pack_variant(url_match):
                            product_links.add(url_match)
            
            logger.info(f"Found {len(product_links)} Essential 10-pack variant links")
            
            # Filter for unique Essential 10-pack products only
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
        """Helper method to identify Essential 10-pack variant URLs."""
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