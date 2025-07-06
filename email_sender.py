#!/usr/bin/env python3
"""
Email notification system for Björn Borg product price changes using Resend API
"""

import requests
import os
import json
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        # Get Resend API configuration from environment variables
        self.api_key = os.getenv('RESEND_API_KEY')
        self.email_to = os.getenv('EMAIL_TO')
        self.api_url = 'https://api.resend.com/emails'
        
        if not self.api_key:
            raise ValueError("RESEND_API_KEY environment variable is required")
        if not self.email_to:
            raise ValueError("EMAIL_TO environment variable is required")
    
    def format_price_change_email(self, price_changes: List[Dict], new_variants: List[Dict] = None) -> str:
        """Format price changes and new variants into HTML email content"""
        
        if new_variants is None:
            new_variants = []
            
        if not price_changes and not new_variants:
            return "No price changes or new variants detected."
        
        # Group price changes by site
        bjornborg_changes = [p for p in price_changes if p.get('site') == 'bjornborg']
        fitnesstukku_changes = [p for p in price_changes if p.get('site') == 'fitnesstukku']
        other_changes = [p for p in price_changes if p.get('site') not in ['bjornborg', 'fitnesstukku']]
        
        total_changes = len(price_changes)
        summary_breakdown = f" (Björn Borg: {len(bjornborg_changes)}, Fitnesstukku: {len(fitnesstukku_changes)})" if bjornborg_changes or fitnesstukku_changes else ""
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
                .site-section {{ 
                    margin: 25px 0; 
                    border: 2px solid #ecf0f1; 
                    border-radius: 10px; 
                    padding: 20px; 
                    background-color: #fdfdfe; 
                }}
                .site-header {{ 
                    font-size: 22px; 
                    font-weight: bold; 
                    margin-bottom: 15px; 
                    padding-bottom: 8px; 
                    border-bottom: 2px solid #ecf0f1; 
                }}
                .bjornborg {{ border-color: #e67e22; }}
                .bjornborg .site-header {{ color: #e67e22; }}
                .fitnesstukku {{ border-color: #9b59b6; }}
                .fitnesstukku .site-header {{ color: #9b59b6; }}
                .product {{ background-color: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #3498db; }}
                .price-drop {{ border-left-color: #27ae60; background-color: #f0f9f4; }}
                .price-increase {{ border-left-color: #e74c3c; background-color: #fdf2f2; }}
                .price {{ font-size: 20px; font-weight: bold; margin: 10px 0; }}
                .old-price {{ text-decoration: line-through; color: #7f8c8d; }}
                .discount {{ color: #27ae60; font-weight: bold; font-size: 16px; }}
                .brand {{ color: #7f8c8d; font-style: italic; margin-bottom: 8px; }}
                .purchase-btn {{ 
                    display: inline-block; 
                    background-color: #3498db; 
                    color: white !important; 
                    padding: 12px 25px; 
                    text-decoration: none; 
                    border-radius: 6px; 
                    margin-top: 15px;
                    font-weight: bold;
                }}
                .purchase-btn:hover {{ background-color: #2980b9; }}
                .change-highlight {{ 
                    background-color: #fff3cd; 
                    padding: 8px 12px; 
                    border-radius: 4px; 
                    border-left: 3px solid #ffc107;
                    margin: 10px 0;
                }}
                .summary {{
                    background-color: #e8f4fd;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #3498db;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #bdc3c7; 
                    color: #7f8c8d; 
                    font-size: 12px; 
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛒 Multi-Site Price Alert</h1>
                <p>Price changes detected across your tracked sites!</p>
            </div>
            
            <div class="summary">
                <strong>📊 Summary:</strong> {total_changes} price changes detected
                {summary_breakdown}
            </div>
        """
        
        # Add Björn Borg section
        if bjornborg_changes:
            html_content += f"""
            <div class="site-section bjornborg">
                <div class="site-header">🧦 Björn Borg ({len(bjornborg_changes)} products)</div>
            """
            
            for change in bjornborg_changes:
                html_content += self._format_product_change(change)
            
            html_content += "</div>"
        
        # Add Fitnesstukku section  
        if fitnesstukku_changes:
            html_content += f"""
            <div class="site-section fitnesstukku">
                <div class="site-header">💪 Fitnesstukku ({len(fitnesstukku_changes)} products)</div>
            """
            
            for change in fitnesstukku_changes:
                html_content += self._format_product_change(change)
            
            html_content += "</div>"
        
        # Add other sites section if any
        if other_changes:
            html_content += f"""
            <div class="site-section">
                <div class="site-header">🌐 Other Sites ({len(other_changes)} products)</div>
            """
            
            for change in other_changes:
                html_content += self._format_product_change(change)
            
            html_content += "</div>"
        
        # Add new variants section if any
        if new_variants:
            html_content += f"""
            <div class="site-section">
                <div class="site-header">✨ New Essential 10-pack Variants Discovered ({len(new_variants)} products)</div>
                <p style="margin-bottom: 15px; color: #2c3e50;">
                    <strong>Great news!</strong> We've found new Essential 10-pack variants that aren't currently being tracked. 
                    Consider adding them to your monitoring list!
                </p>
            """
            
            for variant in new_variants:
                html_content += self._format_new_variant(variant)
            
            html_content += "</div>"
        
        html_content += """
            <div class="footer">
                <p><strong>🤖 Automated by your multi-site price tracker</strong></p>
                <p>Happy shopping! 🛍️</p>
                <p><em>Powered by Resend API</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _format_product_change(self, change: Dict) -> str:
        """Format individual product change for email"""
        product_name = change.get('name', 'Unknown Product')
        current_price = change.get('current_price', 0)
        previous_price = change.get('previous_price', 0)
        original_price = change.get('original_price', 0)
        purchase_url = change.get('purchase_url', '#')
        brand = change.get('brand', '')
        change_amount = current_price - previous_price
        change_percent = ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0
        
        # Determine if it's a price drop or increase
        css_class = "price-drop" if change_amount < 0 else "price-increase"
        change_icon = "📉" if change_amount < 0 else "📈"
        change_text = "PRICE DROP!" if change_amount < 0 else "Price Increase"
        change_color = "#27ae60" if change_amount < 0 else "#e74c3c"
        
        product_html = f"""
        <div class="product {css_class}">
            <h3>{change_icon} {product_name}</h3>
        """
        
        # Add brand if available (mainly for Fitnesstukku products)
        if brand:
            product_html += f'<div class="brand">Brand: {brand}</div>'
        
        product_html += f"""
            <div class="change-highlight">
                <strong>{change_text}: {change_amount:+.2f} EUR ({change_percent:+.1f}%)</strong>
            </div>
            
            <div class="price">
                Current Price: <span style="color: {change_color};">{current_price:.2f} EUR</span>
            </div>
            <div style="margin: 5px 0;">
                Previous Price: <span class="old-price">{previous_price:.2f} EUR</span>
            </div>
        """
        
        # Show original price and total discount if available
        if original_price and original_price > current_price:
            discount_percent = ((original_price - current_price) / original_price * 100)
            product_html += f"""
            <div class="discount">
                💰 Total Discount: {discount_percent:.0f}% off (originally {original_price:.2f} EUR)
            </div>
            """
        
        # Purchase button with URL
        product_html += f"""
            <div style="margin-top: 20px;">
                <a href="{purchase_url}" class="purchase-btn">🛒 Buy Now</a>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #7f8c8d;">
                <strong>Direct Link:</strong> <a href="{purchase_url}" style="color: #3498db;">{purchase_url}</a>
            </div>
        </div>
        """
        
        return product_html
    
    def _format_new_variant(self, variant: Dict) -> str:
        """Format new variant discovery for email"""
        product_name = variant.get('name', 'Unknown Variant')
        current_price = variant.get('current_price', 0)
        original_price = variant.get('original_price', 0)
        purchase_url = variant.get('url', '#')
        product_id = variant.get('product_id', 'N/A')
        
        variant_html = f"""
        <div class="product" style="border: 2px solid #f39c12; background-color: #fef9e7;">
            <h3 style="margin: 0; color: #d68910;">✨ {product_name}</h3>
            <div style="font-size: 14px; color: #7f8c8d; margin: 5px 0;">
                Product ID: {product_id}
            </div>
            <div class="price">
                Current Price: <span style="color: #d68910; font-size: 24px;">{current_price:.2f} EUR</span>
            </div>
        """
        
        # Add original price if available
        if original_price and original_price > current_price:
            discount_pct = int(((original_price - current_price) / original_price) * 100)
            variant_html += f"""
            <div style="margin: 5px 0;">
                Original Price: <span class="old-price">{original_price:.2f} EUR</span>
            </div>
            <div class="discount" style="color: #27ae60;">
                🏷️ {discount_pct}% OFF!
            </div>
            """
        
        # Purchase button with URL
        variant_html += f"""
            <div style="margin-top: 15px;">
                <a href="{purchase_url}" class="purchase-btn" style="background-color: #f39c12;">🛒 View New Variant</a>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #7f8c8d;">
                <strong>Direct Link:</strong> <a href="{purchase_url}" style="color: #f39c12;">{purchase_url}</a>
            </div>
        </div>
        """
        
        return variant_html
    
    def send_price_alert(self, price_changes: List[Dict], new_variants: List[Dict] = None) -> bool:
        """Send email notification about price changes and new variants using Resend API"""
        
        if new_variants is None:
            new_variants = []
            
        if not price_changes and not new_variants:
            logger.info("No price changes or new variants to report")
            return True
        
        try:
            # Determine email subject based on changes and variants
            subject_parts = []
            
            if price_changes:
                drops = sum(1 for change in price_changes if change.get('current_price', 0) < change.get('previous_price', 0))
                increases = len(price_changes) - drops
                
                if drops > 0 and increases == 0:
                    subject_parts.append(f"📉 {drops} price drop(s)")
                elif increases > 0 and drops == 0:
                    subject_parts.append(f"📈 {increases} price increase(s)")
                else:
                    subject_parts.append(f"{len(price_changes)} price change(s)")
            
            if new_variants:
                subject_parts.append(f"✨ {len(new_variants)} new variant(s)")
            
            subject = f"🧦 {' + '.join(subject_parts)}"
            
            # Create HTML content
            html_content = self.format_price_change_email(price_changes, new_variants)
            
            # Prepare the email payload for Resend API
            payload = {
                "from": "Price Tracker <onboarding@resend.dev>",  # Using Resend's default domain
                "to": [self.email_to],
                "subject": subject,
                "html": html_content
            }
            
            # Send email via Resend API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                email_id = result.get('id', 'unknown')
                logger.info(f"Price alert email sent successfully to {self.email_to} (ID: {email_id})")
                return True
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}, Response: {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_scraper_failure_alert(self, error_details: str) -> bool:
        """Send email notification when scraper completely fails"""
        
        try:
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="background-color: #fdf2f2; border-left: 4px solid #e74c3c; padding: 20px; margin: 15px 0; border-radius: 8px;">
                    <h2 style="color: #e74c3c;">🚨 Scraper Health Alert</h2>
                    <p><strong>Your multi-site product price monitor has failed!</strong></p>
                    <div style="background-color: #fff; padding: 15px; border-radius: 4px; margin: 10px 0;">
                        <h3>Error Details:</h3>
                        <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">{error_details}</pre>
                    </div>
                    <h3>Possible Causes:</h3>
                    <ul>
                        <li>🔗 Product URLs have changed</li>
                        <li>🏗️ Website structure updated</li>
                        <li>🛡️ Anti-bot measures blocking access</li>
                        <li>📦 Products out of stock or discontinued</li>
                        <li>🌐 Network connectivity issues</li>
                    </ul>
                    <h3>Recommended Actions:</h3>
                    <ol>
                        <li>Check if products are still available on bjornborg.com/fi and fitnesstukku.fi</li>
                        <li>Verify the product URLs are still valid</li>
                        <li>Check GitHub Actions logs for detailed error messages</li>
                        <li>Update the scraper if needed</li>
                    </ol>
                </div>
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px;">
                    <p><strong>🤖 Automated alert from your multi-site product price tracker</strong></p>
                    <p><em>Powered by Resend API</em></p>
                </div>
            </body>
            </html>
            """
            
            payload = {
                "from": "Price Tracker Alert <onboarding@resend.dev>",
                "to": [self.email_to],
                "subject": "🚨 Procut Scraper Failure Alert - Action Required",
                "html": html_content
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                email_id = result.get('id', 'unknown')
                logger.info(f"Scraper failure alert sent successfully (ID: {email_id})")
                return True
            else:
                logger.error(f"Failed to send failure alert. Status: {response.status_code}, Response: {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send scraper failure alert: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email to verify Resend configuration"""
        
        try:
            payload = {
                "from": "Price Tracker <onboarding@resend.dev>",
                "to": [self.email_to],
                "subject": "🧦 Test Email - Björn Borg Price Tracker",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2>✅ Test Email Successful!</h2>
                    <p>This is a test email from your Björn Borg product price tracker.</p>
                    <p><strong>Configuration is working correctly!</strong></p>
                    <hr>
                    <p style="color: #7f8c8d; font-size: 12px;">
                        Powered by Resend API 🚀
                    </p>
                </body>
                </html>
                """
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                email_id = result.get('id', 'unknown')
                logger.info(f"Test email sent successfully (ID: {email_id})")
                return True
            else:
                logger.error(f"Failed to send test email. Status: {response.status_code}, Response: {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False

def main():
    """Test the Resend email sender"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create sample price change data for testing
    sample_price_changes = [
        {
            'name': 'Essential Socks 10-pack',
            'current_price': 31.47,
            'previous_price': 35.96,
            'original_price': 44.95,
            'purchase_url': 'https://www.bjornborg.com/fi/essential-socks-10-pack-10004564-mp001/'
        }
    ]
    
    try:
        email_sender = EmailSender()
        print("Testing Resend email configuration...")
        
        # Send test email
        if email_sender.send_test_email():
            print("✅ Test email sent successfully!")
            
            # Send sample price alert
            print("Sending sample price alert...")
            if email_sender.send_price_alert(sample_price_changes):
                print("✅ Sample price alert sent successfully!")
                print("Check your email inbox!")
            else:
                print("❌ Failed to send sample price alert")
        else:
            print("❌ Failed to send test email")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTo fix this, set the following environment variables:")
        print("export RESEND_API_KEY='your-resend-api-key'")
        print("export EMAIL_TO='<your-email-address>'")

if __name__ == "__main__":
    main()