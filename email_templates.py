#!/usr/bin/env python3
"""
Email template system for price monitoring notifications
Redesigned with editorial/magazine aesthetic and email-safe inline styles
"""

from typing import Dict, List
from datetime import datetime


class EmailTemplates:
    """Centralized email template manager with premium editorial design"""

    # Color palette - refined, sophisticated
    COLORS = {
        'text_primary': '#1a1a2e',
        'text_secondary': '#4a5568',
        'text_muted': '#718096',
        'bg_cream': '#faf8f5',
        'bg_white': '#ffffff',
        'bg_light': '#f7f5f2',
        'accent_teal': '#0d7377',
        'accent_gold': '#b8860b',
        'price_drop': '#0d7377',      # Teal for savings
        'price_increase': '#9f1239',  # Deep rose for increases
        'border': '#e2ddd5',
        'border_dark': '#1a1a2e',
        'bjornborg': '#1a1a2e',       # Sophisticated black
        'fitnesstukku': '#0d7377',    # Teal
    }

    @classmethod
    def _email_wrapper(cls, content: str, preheader: str = "") -> str:
        """Wrap content in email-safe HTML structure"""
        return f'''<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="x-apple-disable-message-reformatting">
    <title>Price Alert</title>
    <!--[if mso]>
    <style type="text/css">
        table, td, th {{font-family: Georgia, serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: {cls.COLORS['bg_cream']}; font-family: Georgia, 'Times New Roman', serif; -webkit-font-smoothing: antialiased;">
    <!-- Preheader text (hidden) -->
    <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
        {preheader}
        &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
    </div>

    <!-- Email container -->
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS['bg_cream']};">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Main content card -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width: 600px; background-color: {cls.COLORS['bg_white']}; border: 1px solid {cls.COLORS['border']};">
                    {content}
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    @classmethod
    def _format_price_badge(cls, price: float, is_current: bool = True, size: str = "large") -> str:
        """Format a price as a styled badge"""
        font_size = "32px" if size == "large" else "18px"
        color = cls.COLORS['text_primary'] if is_current else cls.COLORS['text_muted']
        decoration = "none" if is_current else "line-through"

        return f'''<span style="font-family: 'Courier New', monospace; font-size: {font_size}; font-weight: bold; color: {color}; text-decoration: {decoration}; letter-spacing: -1px;">{price:.2f}</span><span style="font-family: Georgia, serif; font-size: 14px; color: {cls.COLORS['text_muted']}; margin-left: 4px;">EUR</span>'''

    @classmethod
    def format_product_change(cls, change: Dict) -> str:
        """Format individual product change with editorial styling"""
        product_name = change.get('name', 'Unknown Product')
        current_price = change.get('current_price', 0)
        previous_price = change.get('previous_price', 0)
        original_price = change.get('original_price')
        purchase_url = change.get('purchase_url', '#')
        brand = change.get('brand', '')

        # Historical price data
        lowest_price = change.get('lowest_price')
        lowest_price_date = change.get('lowest_price_date')

        change_amount = current_price - previous_price
        change_percent = ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0

        is_drop = change_amount < 0
        indicator_color = cls.COLORS['price_drop'] if is_drop else cls.COLORS['price_increase']
        indicator_bg = '#e6f3f3' if is_drop else '#fdf2f4'
        change_symbol = "▼" if is_drop else "▲"
        savings_text = f"Save {abs(change_amount):.2f} EUR" if is_drop else f"Up {abs(change_amount):.2f} EUR"

        # Check if current price matches or beats lowest price
        is_lowest = lowest_price and current_price <= lowest_price

        # Calculate total discount if original price available
        total_discount_html = ""
        if original_price and original_price > current_price:
            total_discount = ((original_price - current_price) / original_price * 100)
            total_discount_html = f'''
                                <tr>
                                    <td style="padding-top: 16px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="background-color: {cls.COLORS['accent_gold']}; padding: 6px 12px; border-radius: 2px;">
                                                    <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['bg_white']}; text-transform: uppercase; letter-spacing: 1px;">
                                                        {total_discount:.0f}% off RRP
                                                    </span>
                                                </td>
                                                <td style="padding-left: 10px;">
                                                    <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_muted']};">
                                                        Originally {original_price:.2f} EUR
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''

        # Historical lowest price section
        lowest_price_html = ""
        if lowest_price and lowest_price_date:
            if is_lowest:
                lowest_price_html = f'''
                                <tr>
                                    <td style="padding-top: 16px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #e6f3f3; border-radius: 4px;">
                                            <tr>
                                                <td style="padding: 12px 16px;">
                                                    <span style="font-family: Georgia, serif; font-size: 14px; color: {cls.COLORS['price_drop']}; font-weight: bold;">
                                                        ★ Lowest price ever!
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''
            else:
                lowest_price_html = f'''
                                <tr>
                                    <td style="padding-top: 16px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS['bg_light']}; border-radius: 4px;">
                                            <tr>
                                                <td style="padding: 12px 16px;">
                                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                        <tr>
                                                            <td>
                                                                <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1px;">Historical Low</span>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding-top: 4px;">
                                                                <span style="font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; color: {cls.COLORS['text_secondary']};">{lowest_price:.2f}</span>
                                                                <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']};"> EUR on {lowest_price_date}</span>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''

        brand_html = f'''<span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1.5px;">{brand}</span><br>''' if brand else ""

        return f'''
                                    <tr>
                                        <td style="padding: 24px 40px; border-bottom: 1px solid {cls.COLORS['border']};">
                                            <!-- Product header -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                <tr>
                                                    <td>
                                                        {brand_html}
                                                        <span style="font-family: Georgia, serif; font-size: 18px; color: {cls.COLORS['text_primary']}; line-height: 1.3;">
                                                            {product_name}
                                                        </span>
                                                    </td>
                                                    <td align="right" valign="top">
                                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                                            <tr>
                                                                <td style="background-color: {indicator_bg}; padding: 8px 14px; border-radius: 2px;">
                                                                    <span style="font-family: Georgia, serif; font-size: 13px; color: {indicator_color}; font-weight: bold;">
                                                                        {change_symbol} {abs(change_percent):.1f}%
                                                                    </span>
                                                                </td>
                                                            </tr>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Price display -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 16px;">
                                                <tr>
                                                    <td>
                                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                                            <tr>
                                                                <td style="padding-right: 20px; border-right: 1px solid {cls.COLORS['border']};">
                                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 4px;">Now</span>
                                                                    {cls._format_price_badge(current_price, True)}
                                                                </td>
                                                                <td style="padding-left: 20px;">
                                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 4px;">Was</span>
                                                                    {cls._format_price_badge(previous_price, False)}
                                                                </td>
                                                            </tr>
                                                        </table>
                                                    </td>
                                                    <td align="right" valign="bottom">
                                                        <span style="font-family: Georgia, serif; font-size: 14px; color: {indicator_color}; font-style: italic;">
                                                            {savings_text}
                                                        </span>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Additional info rows -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                {total_discount_html}
                                                {lowest_price_html}
                                            </table>

                                            <!-- CTA Button -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin-top: 20px;">
                                                <tr>
                                                    <td style="background-color: {cls.COLORS['text_primary']}; border-radius: 2px;">
                                                        <a href="{purchase_url}" target="_blank" style="display: inline-block; padding: 12px 24px; font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['bg_white']}; text-decoration: none; text-transform: uppercase; letter-spacing: 1.5px;">
                                                            View Deal &rarr;
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>'''

    @classmethod
    def create_price_alert_email(cls, price_changes: List[Dict]) -> str:
        """Create complete price alert email with editorial design"""

        if not price_changes:
            return "No price changes detected."

        # Group by site
        bjornborg_changes = [p for p in price_changes if 'bjornborg' in p.get('purchase_url', '').lower() or p.get('site') == 'bjornborg']
        fitnesstukku_changes = [p for p in price_changes if 'fitnesstukku' in p.get('purchase_url', '').lower() or p.get('site') == 'fitnesstukku']

        # Count drops vs increases
        drops = sum(1 for p in price_changes if p.get('current_price', 0) < p.get('previous_price', 0))
        increases = len(price_changes) - drops

        today = datetime.now().strftime("%B %d, %Y")

        # Build preheader
        preheader = f"{drops} price drop{'s' if drops != 1 else ''}" if drops > 0 else f"{increases} price change{'s' if increases != 1 else ''}"

        # Header section
        content = f'''
                    <!-- Masthead -->
                    <tr>
                        <td style="background-color: {cls.COLORS['text_primary']}; padding: 32px 40px; text-align: center;">
                            <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 3px;">
                                Price Monitor
                            </span>
                            <h1 style="margin: 12px 0 0 0; font-family: Georgia, serif; font-size: 28px; font-weight: normal; color: {cls.COLORS['bg_white']}; letter-spacing: -0.5px;">
                                Price Alert
                            </h1>
                        </td>
                    </tr>

                    <!-- Date & Summary bar -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: {cls.COLORS['bg_light']}; border-bottom: 1px solid {cls.COLORS['border']};">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td>
                                        <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_secondary']};">
                                            {today}
                                        </span>
                                    </td>
                                    <td align="right">
                                        <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_primary']};">
                                            <strong>{len(price_changes)}</strong> update{'s' if len(price_changes) != 1 else ''}
                                        </span>
                                        <span style="color: {cls.COLORS['border']}; margin: 0 8px;">|</span>
                                        <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['price_drop']};">
                                            <strong>{drops}</strong> ▼
                                        </span>
                                        <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['price_increase']}; margin-left: 8px;">
                                            <strong>{increases}</strong> ▲
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        # Björn Borg section
        if bjornborg_changes:
            content += f'''
                    <!-- Björn Borg Section -->
                    <tr>
                        <td style="padding: 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding: 24px 40px 16px 40px; border-bottom: 2px solid {cls.COLORS['bjornborg']};">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 2px;">
                                                        Fashion & Apparel
                                                    </span>
                                                    <h2 style="margin: 4px 0 0 0; font-family: Georgia, serif; font-size: 20px; font-weight: normal; color: {cls.COLORS['bjornborg']};">
                                                        Björn Borg
                                                    </h2>
                                                </td>
                                                <td align="right" valign="bottom">
                                                    <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_muted']};">
                                                        {len(bjornborg_changes)} item{'s' if len(bjornborg_changes) != 1 else ''}
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''

            for change in bjornborg_changes:
                content += cls.format_product_change(change)

            content += '''
                            </table>
                        </td>
                    </tr>'''

        # Fitnesstukku section
        if fitnesstukku_changes:
            content += f'''
                    <!-- Fitnesstukku Section -->
                    <tr>
                        <td style="padding: 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding: 24px 40px 16px 40px; border-bottom: 2px solid {cls.COLORS['fitnesstukku']};">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 2px;">
                                                        Sports Nutrition
                                                    </span>
                                                    <h2 style="margin: 4px 0 0 0; font-family: Georgia, serif; font-size: 20px; font-weight: normal; color: {cls.COLORS['fitnesstukku']};">
                                                        Fitnesstukku
                                                    </h2>
                                                </td>
                                                <td align="right" valign="bottom">
                                                    <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_muted']};">
                                                        {len(fitnesstukku_changes)} item{'s' if len(fitnesstukku_changes) != 1 else ''}
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''

            for change in fitnesstukku_changes:
                content += cls.format_product_change(change)

            content += '''
                            </table>
                        </td>
                    </tr>'''

        # Footer
        content += f'''
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 28px 40px; background-color: {cls.COLORS['bg_light']}; border-top: 1px solid {cls.COLORS['border']};">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; font-style: italic;">
                                            Automated price monitoring &middot; Updated daily at 9:00 UTC
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        return cls._email_wrapper(content, preheader)

    @classmethod
    def create_failure_alert_email(cls, error_details: str) -> str:
        """Create scraper failure alert with refined warning design"""

        today = datetime.now().strftime("%B %d, %Y at %H:%M UTC")

        content = f'''
                    <!-- Alert Header -->
                    <tr>
                        <td style="background-color: {cls.COLORS['price_increase']}; padding: 32px 40px; text-align: center;">
                            <span style="font-family: Georgia, serif; font-size: 11px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 3px;">
                                System Alert
                            </span>
                            <h1 style="margin: 12px 0 0 0; font-family: Georgia, serif; font-size: 28px; font-weight: normal; color: {cls.COLORS['bg_white']}; letter-spacing: -0.5px;">
                                Monitoring Interrupted
                            </h1>
                        </td>
                    </tr>

                    <!-- Timestamp -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: {cls.COLORS['bg_light']}; border-bottom: 1px solid {cls.COLORS['border']};">
                            <span style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_secondary']};">
                                {today}
                            </span>
                        </td>
                    </tr>

                    <!-- Alert content -->
                    <tr>
                        <td style="padding: 32px 40px;">
                            <p style="font-family: Georgia, serif; font-size: 16px; color: {cls.COLORS['text_primary']}; line-height: 1.6; margin: 0 0 24px 0;">
                                Your price monitoring system encountered an issue and was unable to complete the scheduled check. Manual intervention may be required.
                            </p>

                            <!-- Error details box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 28px;">
                                <tr>
                                    <td style="background-color: #fdf8f8; border-left: 3px solid {cls.COLORS['price_increase']}; padding: 20px;">
                                        <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1.5px; display: block; margin-bottom: 12px;">
                                            Error Details
                                        </span>
                                        <pre style="font-family: 'Courier New', monospace; font-size: 13px; color: {cls.COLORS['text_primary']}; margin: 0; white-space: pre-wrap; word-wrap: break-word;">{error_details}</pre>
                                    </td>
                                </tr>
                            </table>

                            <!-- Possible causes -->
                            <h3 style="font-family: Georgia, serif; font-size: 14px; color: {cls.COLORS['text_primary']}; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 16px 0; border-bottom: 1px solid {cls.COLORS['border']}; padding-bottom: 8px;">
                                Possible Causes
                            </h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 28px;">
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['text_muted']}; margin-right: 12px;">01</span> Product URLs have changed or are invalid
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['text_muted']}; margin-right: 12px;">02</span> Website structure has been updated
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['text_muted']}; margin-right: 12px;">03</span> Anti-bot measures blocking access
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['text_muted']}; margin-right: 12px;">04</span> Products discontinued or out of stock
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['text_muted']}; margin-right: 12px;">05</span> Network or connectivity issues
                                    </td>
                                </tr>
                            </table>

                            <!-- Actions -->
                            <h3 style="font-family: Georgia, serif; font-size: 14px; color: {cls.COLORS['text_primary']}; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 16px 0; border-bottom: 1px solid {cls.COLORS['border']}; padding-bottom: 8px;">
                                Recommended Actions
                            </h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['accent_teal']}; margin-right: 12px;">&rarr;</span> Verify products are available on the source websites
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['accent_teal']}; margin-right: 12px;">&rarr;</span> Check GitHub Actions logs for detailed errors
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-family: Georgia, serif; font-size: 15px; color: {cls.COLORS['text_secondary']};">
                                        <span style="color: {cls.COLORS['accent_teal']}; margin-right: 12px;">&rarr;</span> Update scraper selectors if site structure changed
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: {cls.COLORS['bg_light']}; border-top: 1px solid {cls.COLORS['border']};">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; font-style: italic;">
                                            Automated system alert &middot; Price Monitor
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        return cls._email_wrapper(content, "Action required: Price monitoring system encountered an error")

    @classmethod
    def create_test_email(cls) -> str:
        """Create elegant test email"""

        today = datetime.now().strftime("%B %d, %Y at %H:%M")

        content = f'''
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {cls.COLORS['accent_teal']}; padding: 32px 40px; text-align: center;">
                            <span style="font-family: Georgia, serif; font-size: 11px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 3px;">
                                System Check
                            </span>
                            <h1 style="margin: 12px 0 0 0; font-family: Georgia, serif; font-size: 28px; font-weight: normal; color: {cls.COLORS['bg_white']}; letter-spacing: -0.5px;">
                                Connection Verified
                            </h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px; text-align: center;">
                            <!-- Success checkmark -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin-bottom: 24px;">
                                <tr>
                                    <td style="width: 64px; height: 64px; background-color: #e6f3f3; border-radius: 50%; text-align: center; line-height: 64px;">
                                        <span style="font-size: 28px; color: {cls.COLORS['accent_teal']};">&#10003;</span>
                                    </td>
                                </tr>
                            </table>

                            <h2 style="font-family: Georgia, serif; font-size: 22px; font-weight: normal; color: {cls.COLORS['text_primary']}; margin: 0 0 16px 0;">
                                Email Configuration Successful
                            </h2>

                            <p style="font-family: Georgia, serif; font-size: 16px; color: {cls.COLORS['text_secondary']}; line-height: 1.6; margin: 0 0 24px 0;">
                                Your price monitoring system is properly configured and ready to send alerts. You'll receive notifications whenever tracked products change in price.
                            </p>

                            <!-- Status box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS['bg_light']}; border-radius: 4px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_muted']}; padding: 4px 0;">
                                                    Test sent
                                                </td>
                                                <td align="right" style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_primary']}; padding: 4px 0;">
                                                    {today}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_muted']}; padding: 4px 0;">
                                                    Email provider
                                                </td>
                                                <td align="right" style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_primary']}; padding: 4px 0;">
                                                    Resend API
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['text_muted']}; padding: 4px 0;">
                                                    Status
                                                </td>
                                                <td align="right" style="font-family: Georgia, serif; font-size: 13px; color: {cls.COLORS['accent_teal']}; font-weight: bold; padding: 4px 0;">
                                                    Operational
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: {cls.COLORS['bg_light']}; border-top: 1px solid {cls.COLORS['border']};">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; font-style: italic;">
                                            Price Monitor &middot; Automated Alerts
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        return cls._email_wrapper(content, "Test email successful - your price monitor is configured correctly")

    @classmethod
    def create_analysis_report_email(cls, report_data: Dict) -> str:
        """Create monthly/quarterly analysis report with editorial design"""

        period = report_data.get('period', 'Monthly')
        date_range = report_data.get('date_range', '')
        products = report_data.get('products', [])
        summary = report_data.get('summary', {})

        # Calculate summary stats
        total_products = len(products)
        avg_savings = summary.get('average_savings', 0)
        best_deal = summary.get('best_deal', {})

        content = f'''
                    <!-- Masthead -->
                    <tr>
                        <td style="background-color: {cls.COLORS['text_primary']}; padding: 32px 40px; text-align: center;">
                            <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 3px;">
                                {period} Report
                            </span>
                            <h1 style="margin: 12px 0 0 0; font-family: Georgia, serif; font-size: 28px; font-weight: normal; color: {cls.COLORS['bg_white']}; letter-spacing: -0.5px;">
                                Price Analysis
                            </h1>
                            <p style="margin: 8px 0 0 0; font-family: Georgia, serif; font-size: 14px; color: {cls.COLORS['text_muted']};">
                                {date_range}
                            </p>
                        </td>
                    </tr>

                    <!-- Summary stats -->
                    <tr>
                        <td style="padding: 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td width="33%" style="padding: 28px; text-align: center; border-bottom: 1px solid {cls.COLORS['border']}; border-right: 1px solid {cls.COLORS['border']};">
                                        <span style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: {cls.COLORS['text_primary']}; display: block;">
                                            {total_products}
                                        </span>
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1px;">
                                            Products Tracked
                                        </span>
                                    </td>
                                    <td width="33%" style="padding: 28px; text-align: center; border-bottom: 1px solid {cls.COLORS['border']}; border-right: 1px solid {cls.COLORS['border']};">
                                        <span style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: {cls.COLORS['accent_teal']}; display: block;">
                                            {avg_savings:.0f}%
                                        </span>
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1px;">
                                            Avg. Discount
                                        </span>
                                    </td>
                                    <td width="34%" style="padding: 28px; text-align: center; border-bottom: 1px solid {cls.COLORS['border']};">
                                        <span style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: {cls.COLORS['accent_gold']}; display: block;">
                                            {summary.get('price_changes', 0)}
                                        </span>
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 1px;">
                                            Price Changes
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        # Best deal highlight if available
        if best_deal:
            content += f'''
                    <!-- Best deal highlight -->
                    <tr>
                        <td style="padding: 28px 40px; background-color: #f8f6f0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td>
                                        <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['accent_gold']}; text-transform: uppercase; letter-spacing: 2px;">
                                            Best Deal This Period
                                        </span>
                                        <h3 style="margin: 8px 0; font-family: Georgia, serif; font-size: 18px; font-weight: normal; color: {cls.COLORS['text_primary']};">
                                            {best_deal.get('name', 'N/A')}
                                        </h3>
                                        <span style="font-family: Georgia, serif; font-size: 14px; color: {cls.COLORS['text_secondary']};">
                                            Lowest price: <strong>{best_deal.get('lowest_price', 0):.2f} EUR</strong>
                                            {f" ({best_deal.get('discount', 0):.0f}% off)" if best_deal.get('discount') else ""}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        # Individual product analysis
        if products:
            content += f'''
                    <!-- Products section header -->
                    <tr>
                        <td style="padding: 28px 40px 16px 40px; border-bottom: 2px solid {cls.COLORS['text_primary']};">
                            <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; letter-spacing: 2px;">
                                Detailed Analysis
                            </span>
                            <h2 style="margin: 4px 0 0 0; font-family: Georgia, serif; font-size: 22px; font-weight: normal; color: {cls.COLORS['text_primary']};">
                                Product Overview
                            </h2>
                        </td>
                    </tr>'''

            for product in products:
                trend = product.get('trend', 'stable')
                trend_color = cls.COLORS['price_drop'] if trend == 'down' else (cls.COLORS['price_increase'] if trend == 'up' else cls.COLORS['text_muted'])
                trend_symbol = "▼" if trend == 'down' else ("▲" if trend == 'up' else "→")

                content += f'''
                    <tr>
                        <td style="padding: 24px 40px; border-bottom: 1px solid {cls.COLORS['border']};">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td>
                                        <span style="font-family: Georgia, serif; font-size: 16px; color: {cls.COLORS['text_primary']};">
                                            {product.get('name', 'Unknown')}
                                        </span>
                                    </td>
                                    <td align="right">
                                        <span style="font-family: Georgia, serif; font-size: 13px; color: {trend_color};">
                                            {trend_symbol} {trend.title()}
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding-top: 12px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="25%">
                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; display: block;">Current</span>
                                                    <span style="font-family: 'Courier New', monospace; font-size: 16px; color: {cls.COLORS['text_primary']}; font-weight: bold;">{product.get('current_price', 0):.2f}</span>
                                                </td>
                                                <td width="25%">
                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; display: block;">Lowest</span>
                                                    <span style="font-family: 'Courier New', monospace; font-size: 16px; color: {cls.COLORS['accent_teal']};">{product.get('lowest_price', 0):.2f}</span>
                                                </td>
                                                <td width="25%">
                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; display: block;">Highest</span>
                                                    <span style="font-family: 'Courier New', monospace; font-size: 16px; color: {cls.COLORS['text_secondary']};">{product.get('highest_price', 0):.2f}</span>
                                                </td>
                                                <td width="25%">
                                                    <span style="font-family: Georgia, serif; font-size: 11px; color: {cls.COLORS['text_muted']}; text-transform: uppercase; display: block;">Average</span>
                                                    <span style="font-family: 'Courier New', monospace; font-size: 16px; color: {cls.COLORS['text_secondary']};">{product.get('average_price', 0):.2f}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        # Footer
        content += f'''
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 40px; background-color: {cls.COLORS['bg_light']}; border-top: 1px solid {cls.COLORS['border']};">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <span style="font-family: Georgia, serif; font-size: 12px; color: {cls.COLORS['text_muted']}; font-style: italic;">
                                            {period} analysis report &middot; Price Monitor
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        return cls._email_wrapper(content, f"{period} price analysis: {total_products} products tracked")


    # Legacy method aliases for backward compatibility
    @classmethod
    def get_base_styles(cls) -> str:
        """Legacy method - styles are now inline"""
        return ""

    @classmethod
    def get_analysis_report_styles(cls) -> str:
        """Legacy method - styles are now inline"""
        return ""
