#!/usr/bin/env python3
"""
Price Analyzer - Advanced analytics for price history data
Provides trend analysis, deal detection, and seasonal insights
"""

import calendar
import json
import os
import statistics
from datetime import datetime


class PriceAnalyzer:
    def __init__(self, price_history_file: str = "price_history.json"):
        self.price_history_file = price_history_file
        self.price_history = self.load_price_history()

    def load_price_history(self) -> dict:
        """Load price history from JSON file"""
        if not os.path.exists(self.price_history_file):
            return {}

        try:
            with open(self.price_history_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def analyze_product_pricing(self, product_key: str) -> dict:
        """Analyze pricing trends and statistics for a specific product (event-based format)"""

        if product_key not in self.price_history:
            return {"error": f"Product {product_key} not found in price history"}

        product_data = self.price_history[product_key]
        price_changes = product_data.get("price_changes", [])
        current = product_data.get("current", {})
        all_time_lowest = product_data.get("all_time_lowest", {})

        if not price_changes and not current:
            return {"error": f"No price history available for {product_key}"}

        # Extract price data from change events
        price_points = []
        dates = []

        for event in price_changes:
            try:
                date_obj = datetime.strptime(event.get("date", ""), "%Y-%m-%d")
                # Get price from either initial event or change event
                if event.get("type") == "initial":
                    price = float(event.get("price", 0))
                else:
                    price = float(event.get("to", 0))

                if price > 0:
                    price_points.append(price)
                    dates.append(date_obj)
            except (ValueError, TypeError):
                continue

        # Ensure current price is included
        current_price = (
            current.get("price") if current else (price_points[-1] if price_points else None)
        )

        if not price_points and current_price:
            price_points = [current_price]
            dates = [datetime.now()]

        if not price_points:
            return {"error": f"No valid price data for {product_key}"}

        # Calculate statistics
        lowest_price = all_time_lowest.get("price") if all_time_lowest else min(price_points)
        highest_price = max(price_points)
        average_price = statistics.mean(price_points)

        # Analyze trends
        trend_analysis = self._analyze_price_trends(price_changes)

        # Find best deals from events
        best_deals = self._find_best_deals(price_changes, all_time_lowest)

        # Seasonal analysis (limited with event-based data)
        seasonal_patterns = self._analyze_seasonal_patterns(price_changes)

        return {
            "product_name": product_data.get("name", "Unknown Product"),
            "purchase_url": product_data.get("purchase_url", ""),
            "price_statistics": {
                "current_price": current_price,
                "lowest_price": lowest_price,
                "highest_price": highest_price,
                "average_price": round(average_price, 2),
                "price_volatility": round(
                    statistics.stdev(price_points) if len(price_points) > 1 else 0, 2
                ),
                "total_price_changes": len(price_changes),
            },
            "trends": trend_analysis,
            "best_deals": best_deals,
            "seasonal_patterns": seasonal_patterns,
            "price_changes_count": len(price_changes),
            "tracking_period": {
                "start_date": dates[0].strftime("%Y-%m-%d") if dates else None,
                "end_date": dates[-1].strftime("%Y-%m-%d") if dates else None,
            },
        }

    def _analyze_price_trends(self, price_changes: list[dict]) -> dict:
        """Analyze price trends from change events"""

        if len(price_changes) < 2:
            return {
                "trend": "stable",
                "trend_strength": 0,
                "recent_change": 0,
                "analysis": "insufficient_data",
            }

        # Get first and last prices
        first_event = price_changes[0]
        last_event = price_changes[-1]

        first_price = first_event.get("price") or first_event.get("to", 0)
        last_price = last_event.get("price") or last_event.get("to", 0)

        if not first_price or not last_price:
            return {
                "trend": "stable",
                "trend_strength": 0,
                "recent_change": 0,
                "analysis": "insufficient_data",
            }

        total_change = last_price - first_price
        total_change_pct = (total_change / first_price) * 100 if first_price > 0 else 0

        # Recent change (from last event)
        recent_change = 0
        recent_change_pct = 0
        if "from" in last_event and "to" in last_event:
            recent_change = last_event["to"] - last_event["from"]
            recent_change_pct = last_event.get("change_pct", 0)

        # Determine trend direction
        if abs(total_change_pct) < 1:  # Less than 1% change
            trend = "stable"
        elif total_change_pct > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        # Calculate trend strength (0-100)
        trend_strength = min(abs(total_change_pct) * 10, 100)

        return {
            "trend": trend,
            "trend_strength": round(trend_strength, 1),
            "total_change": round(total_change, 2),
            "total_change_percent": round(total_change_pct, 1),
            "recent_change": round(recent_change, 2),
            "recent_change_percent": round(recent_change_pct, 1),
            "total_price_changes": len(price_changes),
            "analysis": "available",
        }

    def _find_best_deals(
        self, price_changes: list[dict], all_time_lowest: dict | None
    ) -> list[dict]:
        """Find the best deals (lowest prices) from change events"""

        if not price_changes:
            return []

        # Extract all prices with dates
        price_date_pairs = []
        for event in price_changes:
            try:
                date_str = event.get("date", "")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # Get price from event
                price = event.get("price") if event.get("type") == "initial" else event.get("to")

                if price:
                    price_date_pairs.append((price, date_obj, date_str))
            except (ValueError, TypeError):
                continue

        if not price_date_pairs:
            return []

        # Sort by price (ascending)
        price_date_pairs.sort(key=lambda x: x[0])

        best_deals = []
        current_date = datetime.now()

        # Take up to 3 best deals
        for price, date_obj, date_str in price_date_pairs[:3]:
            days_ago = (current_date - date_obj).days
            best_deals.append(
                {
                    "price": price,
                    "date": date_str,
                    "days_ago": days_ago,
                }
            )

        # If we have all_time_lowest and it's not already in best_deals, add it
        if all_time_lowest and all_time_lowest.get("price"):
            atl_price = all_time_lowest["price"]
            if not any(d["price"] == atl_price for d in best_deals):
                try:
                    atl_date = datetime.strptime(all_time_lowest.get("date", ""), "%Y-%m-%d")
                    days_ago = (current_date - atl_date).days
                    best_deals.insert(
                        0,
                        {
                            "price": atl_price,
                            "date": all_time_lowest.get("date"),
                            "days_ago": days_ago,
                            "is_all_time_lowest": True,
                        },
                    )
                except (ValueError, TypeError):
                    pass

        return best_deals[:3]  # Return top 3

    def _analyze_seasonal_patterns(self, price_changes: list[dict]) -> dict:
        """Analyze seasonal price patterns from change events"""

        if len(price_changes) < 3:
            return {
                "analysis": "insufficient_data",
                "message": "Need at least 3 price changes for seasonal analysis",
            }

        # Group price changes by month to see when deals typically happen
        monthly_prices = {}
        for event in price_changes:
            try:
                date_str = event.get("date", "")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                month_name = calendar.month_name[date_obj.month]

                # Get price from event
                price = event.get("price") if event.get("type") == "initial" else event.get("to")

                if price:
                    if month_name not in monthly_prices:
                        monthly_prices[month_name] = []
                    monthly_prices[month_name].append(price)
            except (ValueError, TypeError):
                continue

        if len(monthly_prices) < 2:
            return {
                "analysis": "insufficient_data",
                "message": "Need price changes from multiple months for seasonal analysis",
            }

        # Calculate average price per month (when changes occurred)
        monthly_averages = {}
        for month, month_prices in monthly_prices.items():
            monthly_averages[month] = statistics.mean(month_prices)

        # Find best and worst months
        best_month = min(monthly_averages.items(), key=lambda x: x[1])
        worst_month = max(monthly_averages.items(), key=lambda x: x[1])

        return {
            "analysis": "available",
            "monthly_averages": {month: round(avg, 2) for month, avg in monthly_averages.items()},
            "best_month": {"month": best_month[0], "average_price": round(best_month[1], 2)},
            "worst_month": {"month": worst_month[0], "average_price": round(worst_month[1], 2)},
            "seasonal_variation": round(worst_month[1] - best_month[1], 2),
            "note": "Based on price change events, not daily snapshots",
        }

    def get_all_products_summary(self) -> dict:
        """Get a summary of all products in the price history (event-based format)"""

        if not self.price_history:
            return {"error": "No price history data available"}

        summary = {"total_products": len(self.price_history), "products": []}

        for product_key, product_data in self.price_history.items():
            current = product_data.get("current", {})
            price_changes = product_data.get("price_changes", [])

            if current:
                summary["products"].append(
                    {
                        "key": product_key,
                        "name": product_data.get("name", "Unknown"),
                        "current_price": current.get("price"),
                        "price_changes_count": len(price_changes),
                        "last_updated": current.get("since"),
                    }
                )

        return summary

    def calculate_portfolio_insights(self) -> dict:
        """Calculate insights across all tracked products (event-based format)"""

        if not self.price_history:
            return {"error": "No price history data available"}

        all_analyses = []
        total_savings_potential = 0
        trend_counts = {"increasing": 0, "decreasing": 0, "stable": 0}

        for product_key in self.price_history.keys():
            analysis = self.analyze_product_pricing(product_key)
            if "error" not in analysis:
                all_analyses.append(analysis)

                # Calculate savings potential
                stats = analysis["price_statistics"]
                current = stats["current_price"]
                lowest = stats["lowest_price"]
                if current and lowest and current > lowest:
                    total_savings_potential += current - lowest

                # Count trends
                trend = analysis["trends"]["trend"]
                trend_counts[trend] += 1

        if not all_analyses:
            return {"error": "No valid product analyses available"}

        # Filter out None prices for statistics
        valid_prices = [
            a["price_statistics"]["current_price"]
            for a in all_analyses
            if a["price_statistics"]["current_price"] is not None
        ]

        return {
            "total_products_analyzed": len(all_analyses),
            "total_savings_potential": round(total_savings_potential, 2),
            "trend_distribution": trend_counts,
            "average_price_changes": round(
                statistics.mean([a["price_changes_count"] for a in all_analyses]), 1
            ),
            "price_ranges": {
                "lowest_current_price": min(valid_prices) if valid_prices else None,
                "highest_current_price": max(valid_prices) if valid_prices else None,
                "average_current_price": round(statistics.mean(valid_prices), 2)
                if valid_prices
                else None,
            },
        }


def main():
    """Test the PriceAnalyzer functionality"""

    print("🔍 Testing PriceAnalyzer...")

    analyzer = PriceAnalyzer()

    # Test summary
    summary = analyzer.get_all_products_summary()
    print(f"\n📊 Products Summary: {summary}")

    # Test individual product analysis
    if analyzer.price_history:
        first_product = list(analyzer.price_history.keys())[0]
        analysis = analyzer.analyze_product_pricing(first_product)
        print(f"\n📈 Analysis for {first_product}:")
        print(
            f"  Current Price: €{analysis.get('price_statistics', {}).get('current_price', 'N/A')}"
        )
        print(f"  Trend: {analysis.get('trends', {}).get('trend', 'N/A')}")
        print(f"  Best Deal: €{analysis.get('best_deals', [{}])[0].get('price', 'N/A')}")

    # Test portfolio insights
    portfolio = analyzer.calculate_portfolio_insights()
    print(f"\n💼 Portfolio Insights: {portfolio}")


if __name__ == "__main__":
    main()
