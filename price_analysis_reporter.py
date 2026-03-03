#!/usr/bin/env python3
"""
Automated price analysis reporter - generates and emails comprehensive pricing insights
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

from email_sender import EmailSender
from email_templates import EmailTemplates
from price_analyzer import PriceAnalyzer

C = EmailTemplates.COLORS
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


class PriceAnalysisReporter:
    def __init__(self):
        self.analyzer = PriceAnalyzer()
        self.email_sender = EmailSender()
        self.report_date = datetime.now()

    def generate_comprehensive_report(self) -> dict:
        """Generate a comprehensive price analysis report"""

        if not self.analyzer.price_history:
            return {"error": "No price history data available"}

        report_data = {
            "report_date": self.report_date.strftime("%Y-%m-%d"),
            "report_period": self._determine_report_period(),
            "products": {},
            "summary": {},
        }

        all_products_analysis = []

        # Analyze each product
        for product_key, product_data in self.analyzer.price_history.items():
            analysis = self.analyzer.analyze_product_pricing(product_key)

            if "error" not in analysis:
                # Attach purchase_url from history for site detection
                analysis["_purchase_url"] = product_data.get("purchase_url", "")
                report_data["products"][product_key] = analysis
                all_products_analysis.append(analysis)

        # Generate summary insights
        if all_products_analysis:
            report_data["summary"] = self._generate_summary_insights(all_products_analysis)

        # Group products by name for the HTML report
        report_data["grouped_products"] = self._group_products(report_data["products"])

        return report_data

    def _group_products(self, products: dict) -> dict:
        """Group products by name, aggregating stats across variants."""
        groups_by_name: dict[str, list] = defaultdict(list)

        for product_key, analysis in products.items():
            name = analysis["product_name"]
            groups_by_name[name].append(analysis)

        grouped = {}
        for name, variants in groups_by_name.items():
            current_prices = [
                v["price_statistics"]["current_price"]
                for v in variants
                if v["price_statistics"]["current_price"]
            ]
            lowest_prices = [
                v["price_statistics"]["lowest_price"]
                for v in variants
                if v["price_statistics"]["lowest_price"]
            ]

            # Find cheapest variant for the CTA link
            cheapest_variant = min(
                variants,
                key=lambda v: v["price_statistics"]["current_price"] or float("inf"),
            )

            # Dominant trend
            trend_counts: dict[str, int] = defaultdict(int)
            for v in variants:
                trend_counts[v["trends"]["trend"]] += 1
            dominant_trend = max(trend_counts, key=lambda t: trend_counts[t])

            # Best month across variants
            best_month = None
            for v in variants:
                seasonal = v["seasonal_patterns"]
                if seasonal.get("analysis") == "available":
                    bm = seasonal["best_month"]
                    if best_month is None or bm["average_price"] < best_month["average_price"]:
                        best_month = bm

            # Detect site from purchase URL
            url = cheapest_variant.get("_purchase_url", cheapest_variant.get("purchase_url", ""))
            if "bjornborg" in url.lower():
                site = "bjornborg"
            elif "fitnesstukku" in url.lower():
                site = "fitnesstukku"
            else:
                site = "other"

            grouped[name] = {
                "name": name,
                "variant_count": len(variants),
                "price_low": min(current_prices) if current_prices else 0,
                "price_high": max(current_prices) if current_prices else 0,
                "best_ever": min(lowest_prices) if lowest_prices else 0,
                "trend": dominant_trend,
                "best_month": best_month,
                "best_url": cheapest_variant.get("purchase_url", "#"),
                "site": site,
            }

        return grouped

    def _determine_report_period(self) -> str:
        """Determine what period this report covers"""
        month = self.report_date.month

        # Quarterly reports
        if month in [1, 4, 7, 10]:
            quarter_map = {1: "Q4", 4: "Q1", 7: "Q2", 10: "Q3"}
            prev_quarter = quarter_map[month]
            year = self.report_date.year if month != 1 else self.report_date.year - 1
            return f"{prev_quarter} {year} Quarterly Report"
        else:
            # Monthly reports
            prev_month = self.report_date.replace(day=1) - timedelta(days=1)
            return f"{prev_month.strftime('%B %Y')} Monthly Report"

    def _generate_summary_insights(self, analyses: list[dict]) -> dict:
        """Generate high-level insights across all products"""

        total_products = len(analyses)
        total_savings_potential = 0
        trending_up = 0
        trending_down = 0
        best_deals = []

        for analysis in analyses:
            stats = analysis["price_statistics"]
            trends = analysis["trends"]

            # Calculate total savings potential
            current = stats["current_price"]
            lowest = stats["lowest_price"]
            if current and lowest and current > lowest:
                total_savings_potential += current - lowest

            # Count trends
            if trends["trend"] == "increasing":
                trending_up += 1
            elif trends["trend"] == "decreasing":
                trending_down += 1

            # Collect best deals
            if analysis["best_deals"]:
                latest_deal = analysis["best_deals"][0]
                best_deals.append(
                    {
                        "product": analysis["product_name"],
                        "price": latest_deal["price"],
                        "days_ago": latest_deal["days_ago"],
                    }
                )

        # Sort best deals by recency
        best_deals.sort(key=lambda x: x["days_ago"])

        return {
            "total_products_tracked": total_products,
            "total_savings_potential": round(total_savings_potential, 2),
            "price_trends": {
                "increasing": trending_up,
                "decreasing": trending_down,
                "stable": total_products - trending_up - trending_down,
            },
            "recent_best_deals": best_deals[:3],  # Top 3 recent deals
            "market_sentiment": self._determine_market_sentiment(
                trending_up, trending_down, total_products
            ),
        }

    def _determine_market_sentiment(self, up: int, down: int, total: int) -> str:
        """Determine overall market sentiment"""
        if total == 0:
            return "unknown"

        up_pct = (up / total) * 100
        down_pct = (down / total) * 100

        if up_pct > 60:
            return "bullish"  # Prices generally rising
        elif down_pct > 60:
            return "bearish"  # Prices generally falling
        else:
            return "mixed"  # Mixed signals

    def format_html_report(self, report_data: dict) -> str:
        """Format the report as HTML email matching the price alert design."""

        summary = report_data.get("summary", {})
        grouped = report_data.get("grouped_products", {})
        today = self.report_date.strftime("%b %d, %Y")
        period = report_data["report_period"]
        total = summary.get("total_products_tracked", 0)
        trends = summary.get("price_trends", {})
        savings = summary.get("total_savings_potential", 0)

        # ── Header ──────────────────────────────────────────────
        content = f"""
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 0 28px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <div style="width: 40px; height: 4px; background-color: {C["text_primary"]}; border-radius: 2px;"></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h1 style="margin: 0; font-family: {FONT}; font-size: 28px; font-weight: 700; color: {C["text_primary"]}; letter-spacing: -0.5px;">
                                            Monthly Report
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 8px;">
                                        <span style="font-family: {FONT}; font-size: 16px; color: {C["text_muted"]};">
                                            {today} &middot; {period}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # ── Summary card ────────────────────────────────────────
        content += f"""
                    <!-- Summary -->
                    <tr>
                        <td style="padding: 0 0 24px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {C["bg_white"]}; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="font-family: {FONT}; font-size: 13px; font-weight: 600; color: {C["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.5px; padding-bottom: 16px;">
                                                    Overview
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                        <tr>
                                                            <td style="font-family: {FONT}; font-size: 14px; color: {C["text_secondary"]}; padding: 6px 0;">
                                                                Products tracked
                                                            </td>
                                                            <td align="right" style="font-family: {FONT}; font-size: 14px; font-weight: 600; color: {C["text_primary"]};">
                                                                {total}
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="font-family: {FONT}; font-size: 14px; color: {C["text_secondary"]}; padding: 6px 0;">
                                                                Savings potential
                                                            </td>
                                                            <td align="right" style="font-family: {FONT}; font-size: 14px; font-weight: 600; color: {C["accent_drop"]};">
                                                                {savings:.2f}&euro;
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="font-family: {FONT}; font-size: 14px; color: {C["text_secondary"]}; padding: 6px 0;">
                                                                Trends
                                                            </td>
                                                            <td align="right" style="font-family: {FONT}; font-size: 14px; font-weight: 600; color: {C["text_primary"]};">
                                                                {trends.get("decreasing", 0)} &#8595; &middot; {trends.get("increasing", 0)} &#8593; &middot; {trends.get("stable", 0)} &#8594;
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        # ── Product groups by site ──────────────────────────────
        site_labels = {
            "bjornborg": "Björn Borg",
            "fitnesstukku": "Fitnesstukku",
            "other": "Other",
        }

        for site_key, site_label in site_labels.items():
            site_groups = [g for g in grouped.values() if g["site"] == site_key]
            if not site_groups:
                continue

            content += f"""
                    <!-- {site_label} Section -->
                    <tr>
                        <td style="padding: 0 0 8px 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-bottom: 12px;">
                                        <span style="font-family: {FONT}; font-size: 13px; font-weight: 600; color: {C["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.5px;">
                                            {site_label}
                                        </span>
                                        <span style="font-family: {FONT}; font-size: 12px; color: {C["text_muted"]}; margin-left: 8px;">
                                            {len(site_groups)} product{"s" if len(site_groups) != 1 else ""}
                                        </span>
                                    </td>
                                </tr>"""

            for group in site_groups:
                content += self._format_product_group(group)

            content += """
                            </table>
                        </td>
                    </tr>"""

        # ── Footer ──────────────────────────────────────────────
        content += f"""
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 0 0 0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="border-top: 1px solid {C["border"]}; padding-top: 16px;">
                                        <span style="font-family: {FONT}; font-size: 12px; color: {C["text_muted"]};">
                                            Automated analysis &middot; Generated monthly
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>"""

        return EmailTemplates._email_wrapper(content, f"{period} - {total} products analyzed")

    @staticmethod
    def _format_product_group(group: dict) -> str:
        """Format a single grouped product card."""
        name = group["name"]
        variant_count = group["variant_count"]
        price_low = group["price_low"]
        price_high = group["price_high"]
        best_ever = group["best_ever"]
        trend = group["trend"]
        best_month = group["best_month"]
        best_url = group["best_url"]

        # Price range display
        if variant_count > 1 and price_low != price_high:
            price_display = f"{price_low:.2f} &ndash; {price_high:.2f}&euro;"
        else:
            price_display = f"{price_low:.2f}&euro;"

        # Trend badge
        trend_colors = {
            "decreasing": (C["accent_drop"], "#ecfdf5"),
            "increasing": (C["accent_rise"], "#fef2f2"),
            "stable": (C["text_muted"], C["bg_card"]),
        }
        trend_fg, trend_bg = trend_colors.get(trend, (C["text_muted"], C["bg_card"]))
        trend_labels = {
            "decreasing": "&#8595; Decreasing",
            "increasing": "&#8593; Increasing",
            "stable": "&#8594; Stable",
        }
        trend_label = trend_labels.get(trend, trend.title())

        # Variant count label
        variant_label = f"{variant_count} variants" if variant_count > 1 else ""

        # Best month info
        best_month_html = ""
        if best_month:
            best_month_html = f"""
                                                <tr>
                                                    <td style="font-family: {FONT}; font-size: 13px; color: {C["text_secondary"]}; padding: 4px 0;">
                                                        Best month: <strong style="color: {C["text_primary"]};">{best_month["month"]}</strong> (avg {best_month["average_price"]:.2f}&euro;)
                                                    </td>
                                                </tr>"""

        return f"""
                                <tr>
                                    <td style="padding: 20px; background-color: {
            C["bg_white"]
        }; border-radius: 12px;">
                                        <!-- Trend badge -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="background-color: {
            trend_bg
        }; padding: 5px 12px; border-radius: 20px;">
                                                    <span style="font-family: {
            FONT
        }; font-size: 13px; font-weight: 700; color: {trend_fg};">
                                                        {trend_label}
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- Product name -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 14px;">
                                            <tr>
                                                <td>
                                                    <span style="font-family: {
            FONT
        }; font-size: 18px; font-weight: 500; color: {C["text_primary"]}; line-height: 1.4;">
                                                        {name}
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- Price info -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 12px;">
                                            <tr>
                                                <td style="font-family: {
            FONT
        }; font-size: 14px; color: {C["text_secondary"]}; padding: 4px 0;">
                                                    Current: <strong style="color: {
            C["text_primary"]
        };">{price_display}</strong>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="font-family: {
            FONT
        }; font-size: 14px; color: {C["text_secondary"]}; padding: 4px 0;">
                                                    Best ever: <strong style="color: {
            C["accent_drop"]
        };">{best_ever:.2f}&euro;</strong>
                                                </td>
                                            </tr>
                                            {
            f'''<tr>
                                                <td style="font-family: {FONT}; font-size: 13px; color: {C["text_muted"]}; padding: 4px 0;">
                                                    {variant_label}
                                                </td>
                                            </tr>'''
            if variant_label
            else ""
        }
                                            {best_month_html}
                                        </table>

                                        <!-- CTA -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 16px;">
                                            <tr>
                                                <td>
                                                    <a href="{
            best_url
        }" target="_blank" style="display: inline-block; padding: 12px 20px; font-family: {
            FONT
        }; font-size: 14px; font-weight: 600; color: {C["bg_white"]}; background-color: {
            C["text_primary"]
        }; text-decoration: none; border-radius: 8px;">
                                                        View best price &#8594;
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <!-- Spacer -->
                                <tr><td style="height: 12px;"></td></tr>"""

    def send_analysis_report(self, report_data: dict) -> bool:
        """Send the analysis report via email using EmailSender"""

        if "error" in report_data:
            # Send error notification
            subject = "Price Analysis Report - Error"
            html_content = f"""
            <html><body style="font-family: Arial, sans-serif; margin: 20px;">
                <h2 style="color: #e74c3c;">Price Analysis Report Error</h2>
                <p>Unable to generate price analysis report: {report_data["error"]}</p>
                <p>This usually means the price monitoring system needs more historical data.</p>
                <p>The analysis will become available after a few days of price tracking.</p>
            </body></html>
            """
        else:
            # Send comprehensive report
            period = report_data["report_period"]
            total_products = report_data.get("summary", {}).get("total_products_tracked", 0)

            subject = f"{period} - {total_products} Products Analyzed"
            html_content = self.format_html_report(report_data)

        # Use EmailSender's method instead of duplicating logic
        try:
            success = self.email_sender.send_analysis_report(subject, html_content)
            if success:
                print("Analysis report sent successfully")
            else:
                print("Failed to send analysis report")
            return success

        except Exception as e:
            print(f"Failed to send analysis report: {e}")
            return False

    def save_report_files(self, report_data: dict) -> None:
        """Save report as text and HTML files"""

        timestamp = self.report_date.strftime("%Y-%m-%d_%H-%M-%S")

        # Save as JSON
        with open(f"price_analysis_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # Save as HTML
        if "error" not in report_data:
            html_content = self.format_html_report(report_data)
            with open(f"price_analysis_{timestamp}.html", "w", encoding="utf-8") as f:
                f.write(html_content)

        print(f"Report files saved with timestamp: {timestamp}")


def main():
    """Generate and send automated price analysis report"""

    print("Starting automated price analysis report generation...")

    reporter = PriceAnalysisReporter()

    # Generate comprehensive report
    report_data = reporter.generate_comprehensive_report()

    # Save report files (for GitHub Actions artifacts)
    reporter.save_report_files(report_data)

    # Send via email
    success = reporter.send_analysis_report(report_data)

    if success:
        print("Price analysis report generated and sent successfully!")
    else:
        print("Failed to send price analysis report")
        exit(1)


if __name__ == "__main__":
    main()
