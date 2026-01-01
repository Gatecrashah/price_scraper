#!/usr/bin/env python3
"""
Robust Fitnesstukku scraper using structured data prioritization.

This scraper prioritizes dataLayer objects and structured data extraction over
brittle text parsing, making it much more resilient to website changes.
"""

import json
import time
import re
import yaml
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class FitnesstukuScraper(BaseScraper):
    """Improved Fitnesstukku scraper with structured data prioritization."""
    
    def __init__(self):
        super().__init__("https://www.fitnesstukku.fi")
    
    def extract_structured_data(self, soup, url: str) -> Optional[Dict]:
        """Extract product information from window.dataTrackingView structured data."""
        try:
            # Extract from window.dataTrackingView - the primary structured data source
            tracking_data = self._extract_data_tracking_view(soup)
            
            if tracking_data:
                product_info = {
                    'url': url,
                    'purchase_url': url,
                    'site': 'fitnesstukku'
                }
                
                # Extract basic information
                product_info['name'] = tracking_data.get('name', '').strip()
                product_info['brand'] = tracking_data.get('brand', '').strip()
                product_info['category'] = tracking_data.get('category', '').strip()
                
                # Extract pricing
                price = tracking_data.get('price')
                if price:
                    try:
                        product_info['current_price'] = float(price)
                    except (ValueError, TypeError):
                        pass
                
                # Extract availability and stock status
                availability = tracking_data.get('availability', '').upper()
                product_info['in_stock'] = 'IN STOCK' in availability
                
                # Extract product ID from URL (stable identifier)
                # The URL contains the base product ID (e.g., 5854R from /5854R.html)
                # This is more stable than the variant ID from tracking data
                url_product_id = self._extract_product_id_from_url(url)
                if url_product_id:
                    product_info['product_id'] = f"fitnesstukku_{url_product_id}"

                # Store variant ID from tracking data as metadata (for reference)
                variant_id = tracking_data.get('id')
                if variant_id:
                    product_info['variant_sku'] = variant_id  # e.g., "590-1" for specific flavor
                
                # Extract variant information (flavor, size, etc.)
                variant = tracking_data.get('variant')
                if variant:
                    product_info['variant'] = variant
                
                # Check if it's on sale
                is_on_sale = tracking_data.get('isOnSale', 'false').lower() == 'true'
                if is_on_sale:
                    product_info['on_sale'] = True
                
                # Extract bundle status
                is_bundle = tracking_data.get('isPartOfBundle', 'false').lower() == 'true'
                if is_bundle:
                    product_info['is_bundle'] = True
                
                # Set currency
                product_info['currency'] = 'EUR'
                
                # Only return if we have essential information
                if product_info.get('name') and product_info.get('current_price'):
                    logger.debug(f"Successfully extracted dataTrackingView data for: {product_info['name']}")
                    return product_info
            
            # Fallback: Try generic dataLayer extraction
            datalayer_data = self.extract_dataLayer(soup)
            if datalayer_data and datalayer_data.get('event') == 'productDetail':
                ecommerce = datalayer_data.get('ecommerce', {})
                detail = ecommerce.get('detail', {})
                products = detail.get('products', [])
                
                if products:
                    product_data = products[0]
                    product_info = {
                        'url': url,
                        'purchase_url': url,
                        'site': 'fitnesstukku',
                        'name': product_data.get('name', '').strip(),
                        'brand': product_data.get('brand', '').strip(),
                        'category': product_data.get('category', '').strip(),
                    }
                    
                    price = product_data.get('price')
                    if price:
                        try:
                            product_info['current_price'] = float(price)
                        except (ValueError, TypeError):
                            pass
                    
                    if product_info.get('name') and product_info.get('current_price'):
                        logger.debug(f"Successfully extracted generic dataLayer data for: {product_info['name']}")
                        return product_info
            
            logger.debug("No structured data found or missing essential fields")
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting structured data: {e}")
            return None
    
    def _extract_product_id_from_url(self, url: str) -> Optional[str]:
        """Extract the base product ID from a Fitnesstukku URL.

        Example: https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html -> 5854R
        """
        try:
            # Match the product ID before .html (e.g., 5854R, 609)
            match = re.search(r'/([A-Za-z0-9-]+)\.html$', url)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None

    def _extract_data_tracking_view(self, soup) -> Optional[Dict]:
        """Extract product data from window.dataTrackingView - Fitnesstukku's primary structured data."""
        try:
            script_tags = soup.find_all('script')
            
            # Look specifically for productDetail events in any script tag
            for script in script_tags:
                if not script.string:
                    continue
                
                # Check if this script contains productDetail event
                if 'productDetail' in script.string and 'var view = [' in script.string:
                    # Extract the JSON array from the JavaScript variable declaration
                    lines = script.string.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('var view = [') and 'productDetail' in line:
                            # Extract just the JSON part - handle potential long lines
                            if line.endswith('];'):
                                json_str = line[len('var view = '):-1]  # Remove 'var view = ' and final ';'
                            else:
                                # Handle multiline case
                                json_str = line[len('var view = '):]
                                
                            try:
                                view_data = json.loads(json_str)
                                
                                # Find the productDetail event in the view array
                                for item in view_data:
                                    if isinstance(item, dict) and item.get('event') == 'productDetail':
                                        ecommerce = item.get('ecommerce', {})
                                        detail = ecommerce.get('detail', {})
                                        products = detail.get('products', [])
                                        
                                        if products and len(products) > 0:
                                            product_data = products[0]
                                            logger.debug(f"Found dataTrackingView product: {product_data.get('name', 'Unknown')}")
                                            return product_data
                                            
                            except json.JSONDecodeError as e:
                                logger.debug(f"Failed to parse dataTrackingView JSON: {e}")
                                # Try to extract just the productDetail part
                                try:
                                    # Look for the productDetail object within the line
                                    start_idx = line.find('{"event":"productDetail"')
                                    if start_idx != -1:
                                        # Find the matching closing brace
                                        brace_count = 0
                                        end_idx = start_idx
                                        for i, char in enumerate(line[start_idx:]):
                                            if char == '{':
                                                brace_count += 1
                                            elif char == '}':
                                                brace_count -= 1
                                                if brace_count == 0:
                                                    end_idx = start_idx + i + 1
                                                    break
                                        
                                        product_detail_str = line[start_idx:end_idx]
                                        product_detail = json.loads(product_detail_str)
                                        
                                        if product_detail.get('event') == 'productDetail':
                                            ecommerce = product_detail.get('ecommerce', {})
                                            detail = ecommerce.get('detail', {})
                                            products = detail.get('products', [])
                                            
                                            if products and len(products) > 0:
                                                product_data = products[0]
                                                logger.debug(f"Found productDetail via fallback parsing: {product_data.get('name', 'Unknown')}")
                                                return product_data
                                                
                                except json.JSONDecodeError:
                                    continue
            
            logger.debug("No productDetail data found in script tags")
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting dataTrackingView: {e}")
            return None
    
    def _extract_product_metadata(self, soup) -> Optional[Dict]:
        """Extract product metadata from script tags."""
        try:
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if not script.string:
                    continue
                
                # Look for product metadata patterns
                if 'name' in script.string and 'price' in script.string:
                    # Try to find JSON-like product data
                    patterns = [
                        r'"name":\s*"([^"]+)"',
                        r'"brand":\s*"([^"]+)"',
                        r'"price":\s*(\d+\.?\d*)',
                        r'"sku":\s*"([^"]+)"',
                        r'"availability":\s*"([^"]+)"'
                    ]
                    
                    product_data = {}
                    for pattern in patterns:
                        matches = re.findall(pattern, script.string)
                        if matches:
                            field = pattern.split('"')[1]  # Extract field name
                            product_data[field] = matches[0]
                    
                    if product_data.get('name') and product_data.get('price'):
                        try:
                            product_data['current_price'] = float(product_data['price'])
                            del product_data['price']  # Remove string version
                            return product_data
                        except (ValueError, TypeError):
                            continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting product metadata: {e}")
            return None
    
    def extract_fallback_data(self, soup, url: str) -> Optional[Dict]:
        """Extract product data using robust CSS selectors as fallback."""
        try:
            product_info = {
                'url': url,
                'purchase_url': url,
                'site': 'fitnesstukku'
            }
            
            # Extract product name using specific selectors
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
            
            # Extract current price using specific selectors
            current_price = None
            
            # Method 1: Try discount-specific selectors (for sales)
            discount_selectors = [
                '.price-adjusted',  # Fitnesstukku discounted price
                '.price-sales',     # Fitnesstukku regular price
            ]
            
            for selector in discount_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    current_price = self.extract_price(price_text)
                    if current_price:
                        logger.debug(f"Extracted price from {selector}: {current_price}")
                        break
            
            # Method 2: Fallback to general price selectors
            if not current_price:
                fallback_selectors = [
                    '.price .current',
                    '.current-price',
                    '[data-automation-id="current-price"]',
                    '.price-current',
                    '[data-testid="current-price"]'
                ]
                
                for selector in fallback_selectors:
                    price_elem = soup.select_one(selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        current_price = self.extract_price(price_text)
                        if current_price:
                            logger.debug(f"Extracted price from fallback {selector}: {current_price}")
                            break
            
            if current_price:
                product_info['current_price'] = current_price
            
            # Extract original/list price if available (for discounted products)
            original_price_selectors = [
                '.price-non-adjusted',          # Fitnesstukku original price for discounted items
                '.price-ref__stmt--list .price__value',  # Alternative original price selector
                '.price-original',
                '.list-price',
                '.price-was',
                '[data-automation-id="list-price"]'
            ]
            
            for selector in original_price_selectors:
                orig_price_elem = soup.select_one(selector)
                if orig_price_elem:
                    orig_price_text = orig_price_elem.get_text(strip=True)
                    original_price = self.extract_price(orig_price_text)
                    if original_price and original_price != product_info.get('current_price'):
                        product_info['original_price'] = original_price
                        logger.debug(f"Extracted original price from {selector}: {original_price}")
                        break
            
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
    
    def generate_product_key(self, product: Dict) -> str:
        """Generate a unique key for a Fitnesstukku product."""
        # Always use product_id for Fitnesstukku products (e.g., fitnesstukku_5854R)
        if 'product_id' in product and product['product_id']:
            return f"id_{product['product_id']}"
        # Fallback to URL-based key
        else:
            url = product.get('purchase_url', product.get('url', 'unknown'))
            url_parts = url.split('/')
            slug = url_parts[-1].replace('.html', '') if len(url_parts) > 1 else 'unknown'
            return f"url_fitnesstukku_{slug}"
    
    def get_product_urls(self) -> List[str]:
        """Get Fitnesstukku product URLs from products.yaml configuration."""
        try:
            with open('products.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            if not config:
                raise ValueError("products.yaml is empty or invalid")
                
            products = config.get('products', {})
            if not products:
                raise KeyError("'products' section missing from products.yaml")
                
            fitnesstukku_products = products.get('fitnesstukku', [])
            if not fitnesstukku_products:
                raise KeyError("No Fitnesstukku products found in products.yaml")
                
            # Only return URLs for products with status 'track'
            tracked_urls = []
            for product in fitnesstukku_products:
                if product.get('status') == 'track':
                    tracked_urls.append(product['url'])
                    
            if not tracked_urls:
                raise ValueError("No Fitnesstukku products are marked for tracking in products.yaml")
                
            return tracked_urls
            
        except FileNotFoundError:
            raise FileNotFoundError(
                "products.yaml configuration file not found. "
                "This file is required for the scraper to know which products to monitor."
            )
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse products.yaml: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load Fitnesstukku URLs from products.yaml: {e}")
    
    def scrape_all_products(self) -> List[Dict]:
        """Scrape all tracked Fitnesstukku products."""
        try:
            urls = self.get_product_urls()
            return self.scrape_fitnesstukku_products(urls)
        except Exception as e:
            logger.error(f"Error in scrape_all_products: {e}")
            return []
    
    def scrape_fitnesstukku_products(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple Fitnesstukku product URLs."""
        products = []
        successful_urls = []
        failed_urls = []
        
        logger.info(f"Attempting to scrape {len(urls)} Fitnesstukku products")
        
        for url in urls:
            time.sleep(1)  # Be respectful
            
            try:
                product_info = self.scrape_product_page(url)
                
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