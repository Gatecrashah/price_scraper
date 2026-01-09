"""Tests for price_analyzer.py module."""

import json
import os
import tempfile
from datetime import datetime, timedelta

from price_analyzer import PriceAnalyzer


class TestPriceAnalyzerInit:
    """Tests for PriceAnalyzer initialization and loading."""

    def test_init_with_missing_file(self):
        """Test initialization when price history file doesn't exist."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent/path.json")
        assert analyzer.price_history == {}

    def test_init_with_empty_file(self):
        """Test initialization with empty JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            assert analyzer.price_history == {}
        finally:
            os.unlink(temp_path)

    def test_init_with_valid_data(self, sample_price_history):
        """Test initialization with valid price history data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            assert len(analyzer.price_history) == 2
            assert "base_10004564" in analyzer.price_history
        finally:
            os.unlink(temp_path)

    def test_init_with_invalid_json(self):
        """Test initialization with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{{{")
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            assert analyzer.price_history == {}
        finally:
            os.unlink(temp_path)


class TestAnalyzeProductPricing:
    """Tests for analyze_product_pricing method."""

    def test_analyze_nonexistent_product(self, sample_price_history):
        """Test analysis of product not in history."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.analyze_product_pricing("nonexistent_key")
            assert "error" in result
            assert "not found" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_analyze_product_with_empty_history(self):
        """Test analysis of product with empty price history."""
        data = {"test_product": {"name": "Test", "price_history": {}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.analyze_product_pricing("test_product")
            assert "error" in result
            assert "No price history" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_analyze_product_with_valid_data(self, sample_price_history):
        """Test analysis with valid price history data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.analyze_product_pricing("base_10004564")

            assert "error" not in result
            assert result["product_name"] == "Essential Socks 10-pack"
            assert "price_statistics" in result
            assert result["price_statistics"]["lowest_price"] == 35.96
            assert result["price_statistics"]["highest_price"] == 44.95
            assert result["price_changes_count"] == 2
        finally:
            os.unlink(temp_path)

    def test_analyze_product_returns_trends(self, sample_price_history):
        """Test that analysis includes trend information."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.analyze_product_pricing("base_10004564")

            assert "trends" in result
            assert "trend" in result["trends"]
            assert result["trends"]["trend"] == "decreasing"  # Price went from 44.95 to 35.96
        finally:
            os.unlink(temp_path)


class TestAnalyzePriceTrends:
    """Tests for _analyze_price_trends method (event-based format)."""

    def test_trends_with_single_price(self):
        """Test trend analysis with single data point."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        price_changes = [{"date": "2025-01-01", "price": 35.96, "type": "initial"}]

        result = analyzer._analyze_price_trends(price_changes)

        assert result["trend"] == "stable"
        assert result["analysis"] == "insufficient_data"

    def test_trends_with_stable_prices(self):
        """Test trend analysis when prices are stable."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        price_changes = [
            {"date": "2025-01-01", "price": 35.96, "type": "initial"},
            {"date": "2025-01-02", "from": 35.96, "to": 35.96, "change_pct": 0},
        ]

        result = analyzer._analyze_price_trends(price_changes)
        assert result["trend"] == "stable"
        assert result["total_change_percent"] == 0

    def test_trends_with_increasing_prices(self):
        """Test trend analysis with increasing prices."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        price_changes = [
            {"date": "2025-01-01", "price": 30.00, "type": "initial"},
            {"date": "2025-01-02", "from": 30.00, "to": 35.00, "change_pct": 16.7},
            {"date": "2025-01-03", "from": 35.00, "to": 40.00, "change_pct": 14.3},
        ]

        result = analyzer._analyze_price_trends(price_changes)
        assert result["trend"] == "increasing"
        assert result["total_change"] > 0

    def test_trends_with_decreasing_prices(self):
        """Test trend analysis with decreasing prices."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        price_changes = [
            {"date": "2025-01-01", "price": 45.00, "type": "initial"},
            {"date": "2025-01-02", "from": 45.00, "to": 40.00, "change_pct": -11.1},
            {"date": "2025-01-03", "from": 40.00, "to": 35.00, "change_pct": -12.5},
        ]

        result = analyzer._analyze_price_trends(price_changes)
        assert result["trend"] == "decreasing"
        assert result["total_change"] < 0


class TestFindBestDeals:
    """Tests for _find_best_deals method (event-based format)."""

    def test_best_deals_with_empty_data(self):
        """Test best deals with empty input."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        result = analyzer._find_best_deals([], None)
        assert result == []

    def test_best_deals_returns_sorted_prices(self):
        """Test that best deals are sorted by price ascending."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        today = datetime.now().strftime("%Y-%m-%d")
        price_changes = [
            {"date": today, "price": 45.00, "type": "initial"},
            {"date": today, "from": 45.00, "to": 30.00, "change_pct": -33.3},
            {"date": today, "from": 30.00, "to": 35.00, "change_pct": 16.7},
            {"date": today, "from": 35.00, "to": 40.00, "change_pct": 14.3},
        ]

        result = analyzer._find_best_deals(price_changes, None)

        assert len(result) == 3  # Returns top 3
        assert result[0]["price"] == 30.00
        assert result[1]["price"] == 35.00
        assert result[2]["price"] == 40.00

    def test_best_deals_includes_date_info(self):
        """Test that best deals include date information."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        test_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        price_changes = [{"date": test_date, "price": 35.00, "type": "initial"}]

        result = analyzer._find_best_deals(price_changes, None)

        assert len(result) == 1
        assert "date" in result[0]
        assert "days_ago" in result[0]


class TestAnalyzeSeasonalPatterns:
    """Tests for _analyze_seasonal_patterns method (event-based format)."""

    def test_seasonal_with_insufficient_data(self):
        """Test seasonal analysis with less than 3 price changes."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        price_changes = [
            {"date": "2025-01-01", "price": 35.00, "type": "initial"},
            {"date": "2025-01-05", "from": 35.00, "to": 36.00, "change_pct": 2.9},
        ]

        result = analyzer._analyze_seasonal_patterns(price_changes)
        assert result["analysis"] == "insufficient_data"

    def test_seasonal_with_single_month(self):
        """Test seasonal analysis with data from only one month."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        # All changes within January only
        price_changes = [
            {"date": "2025-01-01", "price": 35.00, "type": "initial"},
            {"date": "2025-01-10", "from": 35.00, "to": 36.00, "change_pct": 2.9},
            {"date": "2025-01-20", "from": 36.00, "to": 37.00, "change_pct": 2.8},
        ]

        result = analyzer._analyze_seasonal_patterns(price_changes)
        assert result["analysis"] == "insufficient_data"
        assert "multiple months" in result["message"]

    def test_seasonal_with_multiple_months(self):
        """Test seasonal analysis with data spanning multiple months."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")

        # Create price changes spanning January and February
        price_changes = [
            {"date": "2025-01-01", "price": 35.00, "type": "initial"},
            {"date": "2025-01-15", "from": 35.00, "to": 34.00, "change_pct": -2.9},
            {"date": "2025-02-01", "from": 34.00, "to": 40.00, "change_pct": 17.6},
            {"date": "2025-02-15", "from": 40.00, "to": 42.00, "change_pct": 5.0},
        ]

        result = analyzer._analyze_seasonal_patterns(price_changes)

        assert result["analysis"] == "available"
        assert "monthly_averages" in result
        assert "best_month" in result
        assert "worst_month" in result
        assert result["best_month"]["month"] == "January"  # Lower prices
        assert result["worst_month"]["month"] == "February"  # Higher prices


class TestGetAllProductsSummary:
    """Tests for get_all_products_summary method."""

    def test_summary_with_no_data(self):
        """Test summary when no price history exists."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        result = analyzer.get_all_products_summary()
        assert "error" in result

    def test_summary_with_valid_data(self, sample_price_history):
        """Test summary with valid price history."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.get_all_products_summary()

            assert "error" not in result
            assert result["total_products"] == 2
            assert len(result["products"]) == 2
        finally:
            os.unlink(temp_path)

    def test_summary_includes_product_details(self, sample_price_history):
        """Test that summary includes required product details (event-based format)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.get_all_products_summary()

            product = result["products"][0]
            assert "key" in product
            assert "name" in product
            assert "current_price" in product
            assert "price_changes_count" in product  # Changed from days_tracked
            assert "last_updated" in product
        finally:
            os.unlink(temp_path)


class TestCalculatePortfolioInsights:
    """Tests for calculate_portfolio_insights method."""

    def test_portfolio_with_no_data(self):
        """Test portfolio insights when no data exists."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        result = analyzer.calculate_portfolio_insights()
        assert "error" in result

    def test_portfolio_with_valid_data(self, sample_price_history):
        """Test portfolio insights with valid data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.calculate_portfolio_insights()

            assert "error" not in result
            assert "total_products_analyzed" in result
            assert "total_savings_potential" in result
            assert "trend_distribution" in result
            assert "price_ranges" in result
        finally:
            os.unlink(temp_path)

    def test_portfolio_trend_distribution(self, sample_price_history):
        """Test that portfolio insights include trend distribution."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_price_history, f)
            temp_path = f.name

        try:
            analyzer = PriceAnalyzer(price_history_file=temp_path)
            result = analyzer.calculate_portfolio_insights()

            trends = result["trend_distribution"]
            assert "increasing" in trends
            assert "decreasing" in trends
            assert "stable" in trends
        finally:
            os.unlink(temp_path)
