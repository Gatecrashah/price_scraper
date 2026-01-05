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
        """Analyze pricing trends and statistics for a specific product"""

        if product_key not in self.price_history:
            return {"error": f"Product {product_key} not found in price history"}

        product_data = self.price_history[product_key]
        history = product_data.get("price_history", {})

        if not history:
            return {"error": f"No price history available for {product_key}"}

        # Extract price data
        price_points = []
        dates = []

        for date_str, data in sorted(history.items()):
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                price = float(data.get("current_price", 0))
                if price > 0:
                    price_points.append(price)
                    dates.append(date_obj)
            except (ValueError, TypeError):
                continue

        if not price_points:
            return {"error": f"No valid price data for {product_key}"}

        # Calculate statistics
        current_price = price_points[-1]
        lowest_price = min(price_points)
        highest_price = max(price_points)
        average_price = statistics.mean(price_points)

        # Analyze trends
        trend_analysis = self._analyze_price_trends(price_points, dates)

        # Find best deals
        best_deals = self._find_best_deals(price_points, dates)

        # Seasonal analysis
        seasonal_patterns = self._analyze_seasonal_patterns(price_points, dates)

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
                "total_data_points": len(price_points),
            },
            "trends": trend_analysis,
            "best_deals": best_deals,
            "seasonal_patterns": seasonal_patterns,
            "days_tracked": len(price_points),
            "tracking_period": {
                "start_date": dates[0].strftime("%Y-%m-%d") if dates else None,
                "end_date": dates[-1].strftime("%Y-%m-%d") if dates else None,
            },
        }

    def _analyze_price_trends(self, prices: list[float], dates: list[datetime]) -> dict:
        """Analyze price trends over time"""

        if len(prices) < 2:
            return {
                "trend": "stable",
                "trend_strength": 0,
                "recent_change": 0,
                "analysis": "insufficient_data",
            }

        # Calculate trend over entire period
        first_price = prices[0]
        last_price = prices[-1]
        total_change = last_price - first_price
        total_change_pct = (total_change / first_price) * 100 if first_price > 0 else 0

        # Recent trend (last 7 days or half the data, whichever is smaller)
        recent_window = min(7, len(prices) // 2 + 1)
        recent_prices = prices[-recent_window:]

        recent_change = 0
        if len(recent_prices) >= 2:
            recent_change = recent_prices[-1] - recent_prices[0]
            recent_change_pct = (
                (recent_change / recent_prices[0]) * 100 if recent_prices[0] > 0 else 0
            )

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
            "recent_change_percent": round(recent_change_pct, 1) if len(recent_prices) >= 2 else 0,
            "analysis": "available",
        }

    def _find_best_deals(self, prices: list[float], dates: list[datetime]) -> list[dict]:
        """Find the best deals (lowest prices) in the history"""

        if not prices or not dates:
            return []

        # Create price-date pairs and sort by price
        price_date_pairs = list(zip(prices, dates))
        price_date_pairs.sort(key=lambda x: x[0])  # Sort by price (ascending)

        best_deals = []
        current_date = datetime.now()

        # Take up to 3 best deals
        for price, date in price_date_pairs[:3]:
            days_ago = (current_date - date).days
            best_deals.append(
                {"price": price, "date": date.strftime("%Y-%m-%d"), "days_ago": days_ago}
            )

        return best_deals

    def _analyze_seasonal_patterns(self, prices: list[float], dates: list[datetime]) -> dict:
        """Analyze seasonal price patterns"""

        if len(prices) < 14:  # Need at least 2 weeks of data
            return {
                "analysis": "insufficient_data",
                "message": "Need at least 14 days of data for seasonal analysis",
            }

        # Group prices by month
        monthly_prices = {}
        for price, date in zip(prices, dates):
            month_name = calendar.month_name[date.month]
            if month_name not in monthly_prices:
                monthly_prices[month_name] = []
            monthly_prices[month_name].append(price)

        if len(monthly_prices) < 2:
            return {
                "analysis": "insufficient_data",
                "message": "Need data from multiple months for seasonal analysis",
            }

        # Calculate average price per month
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
        }

    def get_all_products_summary(self) -> dict:
        """Get a summary of all products in the price history"""

        if not self.price_history:
            return {"error": "No price history data available"}

        summary = {"total_products": len(self.price_history), "products": []}

        for product_key, product_data in self.price_history.items():
            history = product_data.get("price_history", {})
            if history:
                latest_date = max(history.keys())
                latest_data = history[latest_date]

                summary["products"].append(
                    {
                        "key": product_key,
                        "name": product_data.get("name", "Unknown"),
                        "current_price": latest_data.get("current_price"),
                        "days_tracked": len(history),
                        "last_updated": latest_date,
                    }
                )

        return summary

    def calculate_portfolio_insights(self) -> dict:
        """Calculate insights across all tracked products"""

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
                if current > lowest:
                    total_savings_potential += current - lowest

                # Count trends
                trend = analysis["trends"]["trend"]
                trend_counts[trend] += 1

        if not all_analyses:
            return {"error": "No valid product analyses available"}

        return {
            "total_products_analyzed": len(all_analyses),
            "total_savings_potential": round(total_savings_potential, 2),
            "trend_distribution": trend_counts,
            "average_tracking_days": round(
                statistics.mean([a["days_tracked"] for a in all_analyses]), 1
            ),
            "price_ranges": {
                "lowest_current_price": min(
                    a["price_statistics"]["current_price"] for a in all_analyses
                ),
                "highest_current_price": max(
                    a["price_statistics"]["current_price"] for a in all_analyses
                ),
                "average_current_price": round(
                    statistics.mean([a["price_statistics"]["current_price"] for a in all_analyses]),
                    2,
                ),
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
