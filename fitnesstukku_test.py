#!/usr/bin/env python3
"""
Test script to verify we can extract prices from Fitnesstukku products
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

def test_fitnesstukku_extraction():
    """Test price extraction from Fitnesstukku product pages"""
    
    # Test URLs
    test_urls = [
        "https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html",
        "https://www.fitnesstukku.fi/creatine-monohydrate-500-g/609.html"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8',
    })
    
    print("🧪 Testing Fitnesstukku Price Extraction")
    print("=" * 60)
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📦 Test {i}: {url}")
        print("-" * 40)
        
        try:
            response = session.get(url, timeout=30)
            print(f"✅ Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch page: HTTP {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product info using the HTML structure you found
            product_info = extract_fitnesstukku_product(soup, url)
            
            if product_info:
                print(f"✅ Successfully extracted product data:")
                print(f"   Name: {product_info.get('name', 'N/A')}")
                print(f"   Current Price: {product_info.get('current_price', 'N/A')} EUR")
                print(f"   Original Price: {product_info.get('original_price', 'N/A')} EUR")
                print(f"   Brand: {product_info.get('brand', 'N/A')}")
                print(f"   Product URL: {product_info.get('purchase_url', 'N/A')}")
                
                results.append(product_info)
            else:
                print("❌ Failed to extract product information")
                
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            import traceback
            print(traceback.format_exc())
    
    print("\n" + "=" * 60)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully extracted: {len(results)}/{len(test_urls)} products")
    
    if results:
        print("\n🎯 All extracted products:")
        for product in results:
            print(f"  - {product.get('name', 'Unknown')}: {product.get('current_price', 'N/A')} EUR")
        
        print(f"\n💡 Integration Complexity: EASY")
        print(f"   - Basic requests + BeautifulSoup works ✅")
        print(f"   - No JavaScript/Selenium needed ✅") 
        print(f"   - Standard HTML parsing ✅")
        print(f"   - Can integrate with existing scraper in ~2-3 hours ✅")
    else:
        print(f"\n💡 Integration Complexity: COMPLEX")
        print(f"   - May need different approach")
        print(f"   - Check if login required or prices loaded by JavaScript")
    
    return results

def extract_fitnesstukku_product(soup: BeautifulSoup, url: str) -> Optional[Dict]:
    """Extract product information from Fitnesstukku page"""
    
    product_info = {
        'purchase_url': url,
        'site': 'fitnesstukku'
    }
    
    try:
        # Extract product name - try multiple selectors
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
                print(f"   📝 Found name with selector '{selector}': {product_info['name']}")
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
                print(f"   🏷️ Found brand: {product_info['brand']}")
                break
        
        # Extract current price using the structure you provided
        price_selectors = [
            '.price-sales',  # From your HTML structure
            '.price .current',
            '.current-price',
            '[data-automation-id="current-price"]',
            '.price-current'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                print(f"   💰 Found price text with '{selector}': '{price_text}'")
                
                # Extract numeric price from text like "22.90 €"
                price_match = re.search(r'(\d+[.,]\d+)', price_text.replace(',', '.'))
                if price_match:
                    try:
                        current_price = float(price_match.group(1))
                        product_info['current_price'] = current_price
                        print(f"   💰 Extracted current price: {current_price} EUR")
                        break
                    except ValueError:
                        print(f"   ❌ Could not convert price to float: {price_match.group(1)}")
        
        # Extract original/list price if available
        original_price_selectors = [
            '.price-ref__stmt--list .price__value',  # From your HTML structure
            '.price-original',
            '.list-price',
            '.price-was',
            '[data-automation-id="list-price"]'
        ]
        
        for selector in original_price_selectors:
            orig_price_elem = soup.select_one(selector)
            if orig_price_elem:
                orig_price_text = orig_price_elem.get_text(strip=True)
                print(f"   💸 Found original price text: '{orig_price_text}'")
                
                orig_price_match = re.search(r'(\d+[.,]\d+)', orig_price_text.replace(',', '.'))
                if orig_price_match:
                    try:
                        original_price = float(orig_price_match.group(1))
                        # Only set if different from current price (avoid duplicates)
                        if original_price != product_info.get('current_price'):
                            product_info['original_price'] = original_price
                            print(f"   💸 Extracted original price: {original_price} EUR")
                        break
                    except ValueError:
                        print(f"   ❌ Could not convert original price to float: {orig_price_match.group(1)}")
        
        # Calculate discount if we have both prices
        if 'current_price' in product_info and 'original_price' in product_info:
            current = product_info['current_price']
            original = product_info['original_price']
            if original > current:
                discount_pct = round(((original - current) / original) * 100)
                product_info['discount_percent'] = discount_pct
                print(f"   🎯 Calculated discount: {discount_pct}%")
        
        # Generate a product ID for tracking
        url_parts = url.split('/')
        if len(url_parts) > 1:
            product_slug = url_parts[-1].replace('.html', '')
            product_info['product_id'] = f"fitnesstukku_{product_slug}"
        
        return product_info if 'current_price' in product_info else None
        
    except Exception as e:
        print(f"   ❌ Error extracting product data: {e}")
        return None

def debug_page_content(url: str, limit_lines: int = 20):
    """Debug helper to see raw page content"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    })
    
    print(f"\n🔍 DEBUG: Page content for {url}")
    print("-" * 40)
    
    try:
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        text_content = soup.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        print(f"Total lines: {len(lines)}")
        print(f"First {limit_lines} lines:")
        for i, line in enumerate(lines[:limit_lines]):
            print(f"  {i:2d}: {line}")
            
        # Look for price-related content
        print(f"\nLines containing price indicators:")
        price_lines = [line for line in lines if any(indicator in line.lower() 
                      for indicator in ['€', 'eur', 'hinta', 'price'])]
        for line in price_lines[:10]:  # Show max 10 price-related lines
            print(f"  💰: {line}")
            
    except Exception as e:
        print(f"Debug error: {e}")

if __name__ == "__main__":
    # Run the main test
    results = test_fitnesstukku_extraction()
    
    # If no results, run debug to see what's happening
    if not results:
        print("\n" + "="*60)
        print("🔍 DEBUGGING - Let's see the raw content...")
        debug_page_content("https://www.fitnesstukku.fi/whey-80-heraproteiini-4-kg/5854R.html", 30)