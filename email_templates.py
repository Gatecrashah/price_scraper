#!/usr/bin/env python3
"""
Email template system for price monitoring notifications
Centralizes HTML generation to eliminate code duplication
"""

from typing import Dict, List
from datetime import datetime

class EmailTemplates:
    """Centralized email template manager"""
    
    @staticmethod
    def get_base_styles() -> str:
        """Common CSS styles for all email templates"""
        return """
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }
        .site-section { 
            margin: 25px 0; 
            border: 2px solid #ecf0f1; 
            border-radius: 10px; 
            padding: 20px; 
            background-color: #fdfdfe; 
        }
        .site-header { 
            font-size: 22px; 
            font-weight: bold; 
            margin-bottom: 15px; 
            padding-bottom: 8px; 
            border-bottom: 2px solid #ecf0f1; 
        }
        .bjornborg { border-color: #e67e22; }
        .bjornborg .site-header { color: #e67e22; }
        .fitnesstukku { border-color: #9b59b6; }
        .fitnesstukku .site-header { color: #9b59b6; }
        .product { background-color: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #3498db; }
        .price-drop { border-left-color: #27ae60; background-color: #f0f9f4; }
        .price-increase { border-left-color: #e74c3c; background-color: #fdf2f2; }
        .price { font-size: 20px; font-weight: bold; margin: 10px 0; }
        .old-price { text-decoration: line-through; color: #7f8c8d; }
        .discount { color: #27ae60; font-weight: bold; font-size: 16px; }
        .brand { color: #7f8c8d; font-style: italic; margin-bottom: 8px; }
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
        .summary {
            background-color: #e8f4fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        .footer { 
            margin-top: 30px; 
            padding-top: 20px; 
            border-top: 1px solid #bdc3c7; 
            color: #7f8c8d; 
            font-size: 12px; 
        }
        """
    
    @staticmethod
    def get_analysis_report_styles() -> str:
        """Additional styles for analysis reports"""
        return """
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f7fa; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 300; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .summary { background: #f8f9fb; padding: 25px; border-bottom: 1px solid #e1e8ed; }
        .summary h2 { color: #2c3e50; margin-top: 0; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
        .stat-number { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .stat-label { color: #7f8c8d; font-size: 14px; }
        .product { margin: 25px; padding: 20px; border: 1px solid #e1e8ed; border-radius: 8px; }
        .product h3 { color: #2c3e50; margin-top: 0; }
        .price-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 15px 0; }
        .price-item { text-align: center; }
        .price-value { font-size: 18px; font-weight: bold; }
        .price-label { font-size: 12px; color: #7f8c8d; }
        .trend { padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }
        .trend-up { background: #fee; color: #e74c3c; }
        .trend-down { background: #efe; color: #27ae60; }
        .trend-stable { background: #f0f0f0; color: #7f8c8d; }
        .buy-btn { background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 15px; }
        .footer { background: #2c3e50; color: white; padding: 20px; text-align: center; font-size: 14px; }
        """
    
    @classmethod
    def format_product_change(cls, change: Dict) -> str:
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
    
    
    @classmethod
    def create_price_alert_email(cls, price_changes: List[Dict]) -> str:
        """Create complete price alert email HTML"""
        
        if not price_changes:
            return "No price changes detected."
        
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
                {cls.get_base_styles()}
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
                html_content += cls.format_product_change(change)
            
            html_content += "</div>"
        
        # Add Fitnesstukku section  
        if fitnesstukku_changes:
            html_content += f"""
            <div class="site-section fitnesstukku">
                <div class="site-header">💪 Fitnesstukku ({len(fitnesstukku_changes)} products)</div>
            """
            
            for change in fitnesstukku_changes:
                html_content += cls.format_product_change(change)
            
            html_content += "</div>"
        
        # Add other sites section if any
        if other_changes:
            html_content += f"""
            <div class="site-section">
                <div class="site-header">🌐 Other Sites ({len(other_changes)} products)</div>
            """
            
            for change in other_changes:
                html_content += cls.format_product_change(change)
            
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
    
    @classmethod
    def create_failure_alert_email(cls, error_details: str) -> str:
        """Create scraper failure alert email HTML"""
        
        html_content = f"""
        <html>
        <head>
            <style>
                {cls.get_base_styles()}
            </style>
        </head>
        <body>
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
            <div class="footer">
                <p><strong>🤖 Automated alert from your multi-site product price tracker</strong></p>
                <p><em>Powered by Resend API</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    @classmethod
    def create_test_email(cls) -> str:
        """Create test email HTML"""
        
        html_content = f"""
        <html>
        <head>
            <style>
                {cls.get_base_styles()}
            </style>
        </head>
        <body>
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
        
        return html_content