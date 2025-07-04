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
    
    def format_price_change_email(self, price_changes: List[Dict]) -> str:
        """Format price changes into HTML email content"""
        
        if not price_changes:
            return "No price changes detected."
        
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
                .header { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }
                .product { background-color: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #3498db; }
                .price-drop { border-left-color: #27ae60; background-color: #f0f9f4; }
                .price-increase { border-left-color: #e74c3c; background-color: #fdf2f2; }
                .price { font-size: 20px; font-weight: bold; margin: 10px 0; }
                .old-price { text-decoration: line-through; color: #7f8c8d; }
                .discount { color: #27ae60; font-weight: bold; font-size: 16px; }
                .purchase-btn { 
                    display: inline-block; 
                    background-color: #3498db; 
                    color: white !important; 
                    padding: 12px 25px; 
                    text-decoration: none; 
                    border-radius: 6px; 
                    margin-top: 15px;
                    font-weight: bold;
                }
                .purchase-btn:hover { background-color: #2980b9; }
                .change-highlight { 
                    background-color: #fff3cd; 
                    padding: 8px 12px; 
                    border-radius: 4px; 
                    border-left: 3px solid #ffc107;
                    margin: 10px 0;
                }
                .footer { 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #bdc3c7; 
                    color: #7f8c8d; 
                    font-size: 12px; 
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Björn Borg Price Alert</h1>
                <p>Price changes detected for your tracked products!</p>
            </div>
        """
        
        for change in price_changes:
            product_name = change.get('name', 'Unknown Product')
            current_price = change.get('current_price', 0)
            previous_price = change.get('previous_price', 0)
            original_price = change.get('original_price', 0)
            purchase_url = change.get('purchase_url', '#')
            change_amount = current_price - previous_price
            change_percent = ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0
            
            # Determine if it's a price drop or increase
            css_class = "price-drop" if change_amount < 0 else "price-increase"
            change_icon = "📉" if change_amount < 0 else "📈"
            change_text = "PRICE DROP!" if change_amount < 0 else "Price Increase"
            change_color = "#27ae60" if change_amount < 0 else "#e74c3c"
            
            html_content += f"""
            <div class="product {css_class}">
                <h2>{change_icon} {product_name}</h2>
                
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
                html_content += f"""
                <div class="discount">
                    💰 Total Discount: {discount_percent:.0f}% off (originally {original_price:.2f} EUR)
                </div>
                """
            
            # Purchase button with URL
            html_content += f"""
                <div style="margin-top: 20px;">
                    <a href="{purchase_url}" class="purchase-btn">🛒 Buy Now</a>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #7f8c8d;">
                    <strong>Direct Link:</strong> <a href="{purchase_url}" style="color: #3498db;">{purchase_url}</a>
                </div>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p><strong>🤖 Automated by your Björn Borg price tracker</strong></p>
                <p>Happy shopping! 🛍️</p>
                <p><em>Powered by Resend API</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_price_alert(self, price_changes: List[Dict]) -> bool:
        """Send email notification about price changes using Resend API"""
        
        if not price_changes:
            logger.info("No price changes to report")
            return True
        
        try:
            # Determine email subject based on changes
            drops = sum(1 for change in price_changes if change.get('current_price', 0) < change.get('previous_price', 0))
            increases = len(price_changes) - drops
            
            if drops > 0 and increases == 0:
                subject = f"🧦📉 Price Drop Alert! {drops} product(s) cheaper"
            elif increases > 0 and drops == 0:
                subject = f"🧦📈 Price Increase Alert - {increases} product(s) more expensive"
            else:
                subject = f"🧦 Mixed Price Changes - {len(price_changes)} update(s)"
            
            # Create HTML content
            html_content = self.format_price_change_email(price_changes)
            
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
                    <p><strong>Your Björn Borg product price monitor has failed!</strong></p>
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
                        <li>Check if the Essential 10-pack is still available on bjornborg.com/fi</li>
                        <li>Verify the product URLs are still valid</li>
                        <li>Check GitHub Actions logs for detailed error messages</li>
                        <li>Update the scraper if needed</li>
                    </ol>
                </div>
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px;">
                    <p><strong>🤖 Automated alert from your Björn Borg product price tracker</strong></p>
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