#!/usr/bin/env python3
"""
Email template system for price monitoring notifications
Modern minimal design with strong typography and mobile-first layout
"""

from datetime import datetime


class EmailTemplates:
    """Centralized email template manager with modern minimal design"""

    # Color palette - warm, modern, clean
    COLORS = {
        "text_primary": "#1c1917",  # Warm black
        "text_secondary": "#57534e",  # Stone gray
        "text_muted": "#a8a29e",  # Light stone
        "bg_main": "#fafaf9",  # Warm off-white
        "bg_white": "#ffffff",
        "bg_card": "#f5f5f4",  # Subtle card bg
        "accent_drop": "#059669",  # Emerald green for drops
        "accent_rise": "#dc2626",  # Red for increases
        "accent_highlight": "#fef3c7",  # Warm yellow highlight
        "border": "#e7e5e4",  # Light border
        "bjornborg": "#1c1917",  # Brand black
        "fitnesstukku": "#059669",  # Brand green
    }

    @classmethod
    def _email_wrapper(cls, content: str, preheader: str = "") -> str:
        """Wrap content in email-safe HTML structure with modern minimal design"""
        return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="x-apple-disable-message-reformatting">
    <title>Price Alert</title>
    <!--[if mso]>
    <style type="text/css">
        table, td, th {{font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: {cls.COLORS["bg_main"]}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
    <!-- Preheader text (hidden) -->
    <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
        {preheader}
        &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
    </div>

    <!-- Email container -->
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["bg_main"]};">
        <tr>
            <td align="center" style="padding: 24px 16px;">
                <!-- Main content area -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 480px;">
                    {content}
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    @classmethod
    def _format_price(cls, price: float, is_current: bool = True, size: str = "large") -> str:
        """Format a price with clean typography"""
        if size == "large":
            font_size = "36px"
            currency_size = "18px"
        elif size == "medium":
            font_size = "24px"
            currency_size = "14px"
        else:
            font_size = "18px"
            currency_size = "12px"

        color = cls.COLORS["text_primary"] if is_current else cls.COLORS["text_muted"]
        decoration = "none" if is_current else "line-through"

        return f"""<span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', 'Roboto Mono', monospace; font-size: {font_size}; font-weight: 600; color: {color}; text-decoration: {decoration}; letter-spacing: -1px;">{price:.2f}</span><span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: {currency_size}; font-weight: 500; color: {cls.COLORS["text_muted"]}; margin-left: 4px;">€</span>"""

    @classmethod
    def format_product_change(cls, change: dict) -> str:
        """Format individual product change with clean mobile-first layout"""
        product_name = change.get("name", "Unknown Product")
        current_price = change.get("current_price", 0)
        previous_price = change.get("previous_price", 0)
        purchase_url = change.get("purchase_url", "#")
        brand = change.get("brand", "")

        # Historical price data
        lowest_price = change.get("lowest_price")
        lowest_price_date = change.get("lowest_price_date")

        change_amount = current_price - previous_price
        change_percent = (
            ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0
        )

        is_drop = change_amount < 0
        indicator_color = cls.COLORS["accent_drop"] if is_drop else cls.COLORS["accent_rise"]
        indicator_bg = "#ecfdf5" if is_drop else "#fef2f2"
        change_symbol = "↓" if is_drop else "↑"
        savings_text = (
            f"You save {abs(change_amount):.2f}€" if is_drop else f"+{abs(change_amount):.2f}€"
        )

        # Check if current price matches or beats lowest price
        is_lowest = lowest_price and current_price <= lowest_price

        # Historical lowest price section
        lowest_price_html = ""
        if lowest_price and lowest_price_date:
            if is_lowest:
                lowest_price_html = f"""
                                <tr>
                                    <td style="padding-top: 12px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["accent_highlight"]}; border-radius: 8px;">
                                            <tr>
                                                <td style="padding: 10px 14px;">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; font-weight: 600; color: #92400e;">
                                                        Lowest price ever recorded
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>"""
            else:
                lowest_price_html = f"""
                                <tr>
                                    <td style="padding-top: 12px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            Historical low: <strong style="color: {cls.COLORS["text_secondary"]};">{lowest_price:.2f}€</strong> on {lowest_price_date}
                                        </span>
                                    </td>
                                </tr>"""

        brand_html = (
            f"""<span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; font-weight: 600; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; letter-spacing: 0.5px;">{brand}</span><br>"""
            if brand
            else ""
        )

        return f'''
                                    <tr>
                                        <td style="padding: 20px; background-color: {cls.COLORS["bg_white"]}; border-radius: 12px; margin-bottom: 12px;">
                                            <!-- Percentage badge - prominent at top -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                <tr>
                                                    <td>
                                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                                            <tr>
                                                                <td style="background-color: {indicator_bg}; padding: 6px 12px; border-radius: 20px;">
                                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 700; color: {indicator_color};">
                                                                        {change_symbol} {abs(change_percent):.0f}%
                                                                    </span>
                                                                </td>
                                                            </tr>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Product name -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 14px;">
                                                <tr>
                                                    <td>
                                                        {brand_html}
                                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 18px; font-weight: 500; color: {cls.COLORS["text_primary"]}; line-height: 1.4;">
                                                            {product_name}
                                                        </span>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Price display - stacked for mobile -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 16px;">
                                                <tr>
                                                    <td>
                                                        {cls._format_price(current_price, True, "large")}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding-top: 6px;">
                                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 17px; color: {cls.COLORS["text_muted"]}; text-decoration: line-through;">{previous_price:.2f}€</span>
                                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; font-weight: 600; color: {indicator_color}; margin-left: 10px;">
                                                            {savings_text}
                                                        </span>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Historical low info -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                {lowest_price_html}
                                            </table>

                                            <!-- CTA Button -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 16px;">
                                                <tr>
                                                    <td>
                                                        <a href="{purchase_url}" target="_blank" style="display: inline-block; padding: 12px 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; font-weight: 600; color: {cls.COLORS["bg_white"]}; background-color: {cls.COLORS["text_primary"]}; text-decoration: none; border-radius: 8px;">
                                                            View deal →
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <!-- Spacer between products -->
                                    <tr><td style="height: 12px;"></td></tr>'''

    @classmethod
    def create_price_alert_email(cls, price_changes: list[dict]) -> str:
        """Create complete price alert email with modern minimal design"""

        if not price_changes:
            return "No price changes detected."

        # Group by site
        bjornborg_changes = [
            p
            for p in price_changes
            if "bjornborg" in p.get("purchase_url", "").lower() or p.get("site") == "bjornborg"
        ]
        fitnesstukku_changes = [
            p
            for p in price_changes
            if "fitnesstukku" in p.get("purchase_url", "").lower()
            or p.get("site") == "fitnesstukku"
        ]

        # Count drops vs increases
        drops = sum(
            1 for p in price_changes if p.get("current_price", 0) < p.get("previous_price", 0)
        )
        increases = len(price_changes) - drops

        today = datetime.now().strftime("%b %d, %Y")

        # Build preheader
        preheader = (
            f"{drops} price drop{'s' if drops != 1 else ''}"
            if drops > 0
            else f"{increases} price change{'s' if increases != 1 else ''}"
        )

        # Summary text
        if drops > 0 and increases == 0:
            summary_text = f"{drops} price drop{'s' if drops != 1 else ''}"
            accent_color = cls.COLORS["accent_drop"]
        elif increases > 0 and drops == 0:
            summary_text = f"{increases} price increase{'s' if increases != 1 else ''}"
            accent_color = cls.COLORS["accent_rise"]
        else:
            summary_text = f"{drops} ↓ · {increases} ↑"
            accent_color = cls.COLORS["text_primary"]

        # Header section - clean and simple
        content = f"""
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 0 28px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <div style="width: 40px; height: 4px; background-color: {accent_color}; border-radius: 2px;"></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 28px; font-weight: 700; color: {cls.COLORS["text_primary"]}; letter-spacing: -0.5px;">
                                            Price Alert
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 8px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; color: {cls.COLORS["text_muted"]};">
                                            {today} · {summary_text}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # Björn Borg section
        if bjornborg_changes:
            content += f"""
                    <!-- Björn Borg Section -->
                    <tr>
                        <td style="padding: 0 0 8px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 12px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 600; color: {cls.COLORS["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Björn Borg
                                        </span>
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]}; margin-left: 8px;">
                                            {len(bjornborg_changes)} item{"s" if len(bjornborg_changes) != 1 else ""}
                                        </span>
                                    </td>
                                </tr>"""

            for change in bjornborg_changes:
                content += cls.format_product_change(change)

            content += """
                            </table>
                        </td>
                    </tr>"""

        # Fitnesstukku section
        if fitnesstukku_changes:
            content += f"""
                    <!-- Fitnesstukku Section -->
                    <tr>
                        <td style="padding: 8px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 12px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 600; color: {cls.COLORS["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Fitnesstukku
                                        </span>
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]}; margin-left: 8px;">
                                            {len(fitnesstukku_changes)} item{"s" if len(fitnesstukku_changes) != 1 else ""}
                                        </span>
                                    </td>
                                </tr>"""

            for change in fitnesstukku_changes:
                content += cls.format_product_change(change)

            content += """
                            </table>
                        </td>
                    </tr>"""

        # Footer - minimal
        content += f"""
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="border-top: 1px solid {cls.COLORS["border"]}; padding-top: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            Automated monitoring · Updates daily at 9:00 UTC
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        return cls._email_wrapper(content, preheader)

    @classmethod
    def create_failure_alert_email(cls, error_details: str) -> str:
        """Create scraper failure alert with clean modern design"""

        today = datetime.now().strftime("%b %d, %Y at %H:%M UTC")

        content = f"""
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 0 28px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <div style="width: 40px; height: 4px; background-color: {cls.COLORS["accent_rise"]}; border-radius: 2px;"></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 28px; font-weight: 700; color: {cls.COLORS["accent_rise"]}; letter-spacing: -0.5px;">
                                            Monitoring Failed
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 8px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; color: {cls.COLORS["text_muted"]};">
                                            {today}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Error card -->
                    <tr>
                        <td style="padding: 0 0 20px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #fef2f2; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; font-weight: 600; color: {cls.COLORS["accent_rise"]}; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Error Details
                                        </span>
                                        <pre style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 13px; color: {cls.COLORS["text_primary"]}; margin: 8px 0 0 0; white-space: pre-wrap; word-wrap: break-word; line-height: 1.5;">{error_details}</pre>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Possible causes -->
                    <tr>
                        <td style="padding: 0 0 20px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["bg_white"]}; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 600; color: {cls.COLORS["text_primary"]};">
                                            Possible causes
                                        </span>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 12px;">
                                            <tr>
                                                <td style="padding: 6px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: {cls.COLORS["text_secondary"]};">
                                                    • Product URLs changed or invalid
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: {cls.COLORS["text_secondary"]};">
                                                    • Website structure updated
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: {cls.COLORS["text_secondary"]};">
                                                    • Anti-bot measures blocking access
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: {cls.COLORS["text_secondary"]};">
                                                    • Network or connectivity issues
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
                        <td style="padding: 16px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="border-top: 1px solid {cls.COLORS["border"]}; padding-top: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            Check GitHub Actions logs for details
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        return cls._email_wrapper(
            content, "Action required: Price monitoring system encountered an error"
        )

    @classmethod
    def create_test_email(cls) -> str:
        """Create clean test email"""

        today = datetime.now().strftime("%b %d, %Y at %H:%M")

        content = f"""
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 0 28px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <div style="width: 40px; height: 4px; background-color: {cls.COLORS["accent_drop"]}; border-radius: 2px;"></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 28px; font-weight: 700; color: {cls.COLORS["text_primary"]}; letter-spacing: -0.5px;">
                                            Connection Verified
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 8px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; color: {cls.COLORS["text_muted"]};">
                                            {today}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Status card -->
                    <tr>
                        <td style="padding: 0 0 20px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["bg_white"]}; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; color: {cls.COLORS["text_secondary"]}; line-height: 1.5; margin: 0 0 16px 0;">
                                            Your price monitoring system is configured and ready. You'll receive alerts when tracked products change in price.
                                        </p>

                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="border-top: 1px solid {cls.COLORS["border"]}; padding-top: 16px;">
                                            <tr>
                                                <td style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; color: {cls.COLORS["text_muted"]}; padding: 8px 0;">
                                                    Email provider
                                                </td>
                                                <td align="right" style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; color: {cls.COLORS["text_primary"]}; font-weight: 500; padding: 8px 0;">
                                                    Resend API
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; color: {cls.COLORS["text_muted"]}; padding: 8px 0;">
                                                    Status
                                                </td>
                                                <td align="right" style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; color: {cls.COLORS["accent_drop"]}; font-weight: 600; padding: 8px 0;">
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
                        <td style="padding: 8px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="border-top: 1px solid {cls.COLORS["border"]}; padding-top: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            Automated monitoring · Updates daily at 9:00 UTC
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        return cls._email_wrapper(
            content, "Test email successful - your price monitor is configured correctly"
        )

    @classmethod
    def create_analysis_report_email(cls, report_data: dict) -> str:
        """Create monthly/quarterly analysis report with modern design"""

        period = report_data.get("period", "Monthly")
        date_range = report_data.get("date_range", "")
        products = report_data.get("products", [])
        summary = report_data.get("summary", {})

        # Calculate summary stats
        total_products = len(products)
        avg_savings = summary.get("average_savings", 0)
        best_deal = summary.get("best_deal", {})

        content = f"""
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 0 28px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <div style="width: 40px; height: 4px; background-color: {cls.COLORS["text_primary"]}; border-radius: 2px;"></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 28px; font-weight: 700; color: {cls.COLORS["text_primary"]}; letter-spacing: -0.5px;">
                                            {period} Report
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 8px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; color: {cls.COLORS["text_muted"]};">
                                            {date_range}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Stats card -->
                    <tr>
                        <td style="padding: 0 0 16px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["bg_white"]}; border-radius: 12px;">
                                <tr>
                                    <td width="33%" style="padding: 20px 16px; text-align: center;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 28px; font-weight: 700; color: {cls.COLORS["text_primary"]}; display: block;">
                                            {total_products}
                                        </span>
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; letter-spacing: 0.3px;">
                                            Products
                                        </span>
                                    </td>
                                    <td width="33%" style="padding: 20px 16px; text-align: center; border-left: 1px solid {cls.COLORS["border"]}; border-right: 1px solid {cls.COLORS["border"]};">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 28px; font-weight: 700; color: {cls.COLORS["accent_drop"]}; display: block;">
                                            {avg_savings:.0f}%
                                        </span>
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; letter-spacing: 0.3px;">
                                            Avg Discount
                                        </span>
                                    </td>
                                    <td width="34%" style="padding: 20px 16px; text-align: center;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 28px; font-weight: 700; color: {cls.COLORS["text_secondary"]}; display: block;">
                                            {summary.get("price_changes", 0)}
                                        </span>
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; letter-spacing: 0.3px;">
                                            Changes
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # Best deal highlight if available
        if best_deal:
            content += f"""
                    <!-- Best deal card -->
                    <tr>
                        <td style="padding: 0 0 16px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["accent_highlight"]}; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; font-weight: 600; color: #92400e; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Best Deal
                                        </span>
                                        <h3 style="margin: 8px 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 17px; font-weight: 600; color: {cls.COLORS["text_primary"]};">
                                            {best_deal.get("name", "N/A")}
                                        </h3>
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; color: {cls.COLORS["text_secondary"]};">
                                            Lowest: <strong>{best_deal.get("lowest_price", 0):.2f}€</strong>
                                            {f" ({best_deal.get('discount', 0):.0f}% off)" if best_deal.get("discount") else ""}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # Individual product analysis
        if products:
            content += f"""
                    <!-- Products section -->
                    <tr>
                        <td style="padding: 8px 0 12px 0;">
                            <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 600; color: {cls.COLORS["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.5px;">
                                Product Overview
                            </span>
                        </td>
                    </tr>"""

            for product in products:
                trend = product.get("trend", "stable")
                trend_color = (
                    cls.COLORS["accent_drop"]
                    if trend == "down"
                    else (cls.COLORS["accent_rise"] if trend == "up" else cls.COLORS["text_muted"])
                )
                trend_symbol = "↓" if trend == "down" else ("↑" if trend == "up" else "→")

                content += f"""
                    <tr>
                        <td style="padding: 0 0 12px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["bg_white"]}; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 16px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; font-weight: 500; color: {cls.COLORS["text_primary"]};">
                                                        {product.get("name", "Unknown")}
                                                    </span>
                                                </td>
                                                <td align="right">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 600; color: {trend_color};">
                                                        {trend_symbol} {trend.title()}
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 12px;">
                                            <tr>
                                                <td width="25%">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 10px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; display: block;">Now</span>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 15px; color: {cls.COLORS["text_primary"]}; font-weight: 600;">{product.get("current_price", 0):.2f}€</span>
                                                </td>
                                                <td width="25%">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 10px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; display: block;">Low</span>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 15px; color: {cls.COLORS["accent_drop"]}; font-weight: 500;">{product.get("lowest_price", 0):.2f}€</span>
                                                </td>
                                                <td width="25%">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 10px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; display: block;">High</span>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 15px; color: {cls.COLORS["text_secondary"]};">{product.get("highest_price", 0):.2f}€</span>
                                                </td>
                                                <td width="25%">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 10px; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; display: block;">Avg</span>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 15px; color: {cls.COLORS["text_secondary"]};">{product.get("average_price", 0):.2f}€</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # Footer
        content += f"""
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 16px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="border-top: 1px solid {cls.COLORS["border"]}; padding-top: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            {period} report · Price Monitor
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        return cls._email_wrapper(
            content, f"{period} price analysis: {total_products} products tracked"
        )

    @classmethod
    def create_ean_price_alert_email(cls, price_drops: list[dict]) -> str:
        """Create EAN-based cross-store price alert email"""

        if not price_drops:
            return "No price drops detected."

        today = datetime.now().strftime("%b %d, %Y")
        num_drops = len(price_drops)

        # Build preheader
        preheader = f"{num_drops} price drop{'s' if num_drops != 1 else ''} across stores"

        # Header
        content = f"""
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 0 28px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <div style="width: 40px; height: 4px; background-color: {cls.COLORS["accent_drop"]}; border-radius: 2px;"></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 28px; font-weight: 700; color: {cls.COLORS["text_primary"]}; letter-spacing: -0.5px;">
                                            Price Drop Alert
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 8px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; color: {cls.COLORS["text_muted"]};">
                                            {today} · Cross-store comparison
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # Products
        for drop in price_drops:
            name = drop.get("name", "Unknown Product")
            ean = drop.get("ean", "")
            store = drop.get("store", "")
            url = drop.get("url", "#")
            current_price = drop.get("current_price", 0)
            previous_price = drop.get("previous_price", 0)
            savings = drop.get("savings", 0)
            all_time_price = drop.get("all_time_price")
            all_time_date = drop.get("all_time_date")
            all_time_store = drop.get("all_time_store")
            all_store_prices = drop.get("all_store_prices", {})

            change_percent = (
                ((previous_price - current_price) / previous_price * 100)
                if previous_price > 0
                else 0
            )

            # Check if this is the all-time lowest
            is_all_time_low = all_time_price and current_price <= all_time_price

            # All-time low badge
            all_time_html = ""
            if is_all_time_low:
                all_time_html = f"""
                                <tr>
                                    <td style="padding-top: 12px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["accent_highlight"]}; border-radius: 8px;">
                                            <tr>
                                                <td style="padding: 10px 14px;">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; font-weight: 600; color: #92400e;">
                                                        ⭐ All-time lowest price!
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>"""
            elif all_time_price and all_time_date:
                all_time_html = f"""
                                <tr>
                                    <td style="padding-top: 12px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            All-time low: <strong style="color: {cls.COLORS["text_secondary"]};">{all_time_price:.2f}€</strong> at {all_time_store} ({all_time_date})
                                        </span>
                                    </td>
                                </tr>"""

            # Other store prices
            other_stores_html = ""
            if all_store_prices and len(all_store_prices) > 1:
                other_stores_html = f"""
                                <tr>
                                    <td style="padding-top: 16px; border-top: 1px solid {cls.COLORS["border"]}; margin-top: 12px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; font-weight: 600; color: {cls.COLORS["text_muted"]}; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Other in-stock prices
                                        </span>
                                    </td>
                                </tr>"""

                for other_store, other_price in sorted(
                    all_store_prices.items(), key=lambda x: x[1]
                ):
                    if other_store != store and other_price:
                        diff = other_price - current_price
                        other_stores_html += f"""
                                <tr>
                                    <td style="padding: 6px 0;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: {cls.COLORS["text_secondary"]};">
                                            {other_store.title()}: <strong>{other_price:.2f}€</strong>
                                            <span style="color: {cls.COLORS["text_muted"]};">(+{diff:.2f}€)</span>
                                        </span>
                                    </td>
                                </tr>"""

            content += f'''
                    <tr>
                        <td style="padding: 0 0 16px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {cls.COLORS["bg_white"]}; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <!-- Percentage badge -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                                        <tr>
                                                            <td style="background-color: #ecfdf5; padding: 6px 12px; border-radius: 20px;">
                                                                <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; font-weight: 700; color: {cls.COLORS["accent_drop"]};">
                                                                    ↓ {change_percent:.0f}%
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- Product name & EAN -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 14px;">
                                            <tr>
                                                <td>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 18px; font-weight: 500; color: {cls.COLORS["text_primary"]}; line-height: 1.4;">
                                                        {name}
                                                    </span>
                                                    <br>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 11px; color: {cls.COLORS["text_muted"]};">
                                                        EAN: {ean}
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- Price display -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 16px;">
                                            <tr>
                                                <td>
                                                    {cls._format_price(current_price, True, "large")}
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: {cls.COLORS["text_muted"]}; margin-left: 8px;">
                                                        at {store.title()}
                                                    </span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding-top: 6px;">
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 17px; color: {cls.COLORS["text_muted"]}; text-decoration: line-through;">{previous_price:.2f}€</span>
                                                    <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 16px; font-weight: 600; color: {cls.COLORS["accent_drop"]}; margin-left: 10px;">
                                                        Save {savings:.2f}€
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- All-time low info -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            {all_time_html}
                                        </table>

                                        <!-- Other store prices -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 12px;">
                                            {other_stores_html}
                                        </table>

                                        <!-- CTA Button -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 16px;">
                                            <tr>
                                                <td>
                                                    <a href="{url}" target="_blank" style="display: inline-block; padding: 12px 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; font-weight: 600; color: {cls.COLORS["bg_white"]}; background-color: {cls.COLORS["accent_drop"]}; text-decoration: none; border-radius: 8px;">
                                                        Buy at {store.title()} →
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''

        # Footer
        content += f"""
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 16px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="border-top: 1px solid {cls.COLORS["border"]}; padding-top: 16px;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; color: {cls.COLORS["text_muted"]};">
                                            EAN Price Monitor · Cross-store comparison · Daily at 9:15 UTC
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        return cls._email_wrapper(content, preheader)

    # Legacy method aliases for backward compatibility
    @classmethod
    def get_base_styles(cls) -> str:
        """Legacy method - styles are now inline"""
        return ""

    @classmethod
    def get_analysis_report_styles(cls) -> str:
        """Legacy method - styles are now inline"""
        return ""
