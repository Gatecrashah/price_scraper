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
            assert result["days_tracked"] == 2
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
    """Tests for _analyze_price_trends method."""

    def test_trends_with_single_price(self):
        """Test trend analysis with single data point."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        result = analyzer._analyze_price_trends([35.96], [datetime.now()])

        assert result["trend"] == "stable"
        assert result["analysis"] == "insufficient_data"

    def test_trends_with_stable_prices(self):
        """Test trend analysis when prices are stable."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        prices = [35.96, 35.96, 35.96]
        dates = [datetime.now() - timedelta(days=i) for i in range(3)]

        result = analyzer._analyze_price_trends(prices, dates)
        assert result["trend"] == "stable"
        assert result["total_change_percent"] == 0

    def test_trends_with_increasing_prices(self):
        """Test trend analysis with increasing prices."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        prices = [30.00, 35.00, 40.00]
        dates = [datetime.now() - timedelta(days=i) for i in range(2, -1, -1)]

        result = analyzer._analyze_price_trends(prices, dates)
        assert result["trend"] == "increasing"
        assert result["total_change"] > 0

    def test_trends_with_decreasing_prices(self):
        """Test trend analysis with decreasing prices."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        prices = [45.00, 40.00, 35.00]
        dates = [datetime.now() - timedelta(days=i) for i in range(2, -1, -1)]

        result = analyzer._analyze_price_trends(prices, dates)
        assert result["trend"] == "decreasing"
        assert result["total_change"] < 0


class TestFindBestDeals:
    """Tests for _find_best_deals method."""

    def test_best_deals_with_empty_data(self):
        """Test best deals with empty input."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        result = analyzer._find_best_deals([], [])
        assert result == []

    def test_best_deals_returns_sorted_prices(self):
        """Test that best deals are sorted by price ascending."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        prices = [45.00, 30.00, 35.00, 40.00]
        dates = [datetime.now() - timedelta(days=i) for i in range(4)]

        result = analyzer._find_best_deals(prices, dates)

        assert len(result) == 3  # Returns top 3
        assert result[0]["price"] == 30.00
        assert result[1]["price"] == 35.00
        assert result[2]["price"] == 40.00

    def test_best_deals_includes_date_info(self):
        """Test that best deals include date information."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        test_date = datetime.now() - timedelta(days=5)
        prices = [35.00]
        dates = [test_date]

        result = analyzer._find_best_deals(prices, dates)

        assert len(result) == 1
        assert "date" in result[0]
        assert "days_ago" in result[0]


class TestAnalyzeSeasonalPatterns:
    """Tests for _analyze_seasonal_patterns method."""

    def test_seasonal_with_insufficient_data(self):
        """Test seasonal analysis with less than 14 days of data."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        prices = [35.00] * 10
        dates = [datetime.now() - timedelta(days=i) for i in range(10)]

        result = analyzer._analyze_seasonal_patterns(prices, dates)
        assert result["analysis"] == "insufficient_data"

    def test_seasonal_with_single_month(self):
        """Test seasonal analysis with data from only one month."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")
        # All dates within January only
        prices = [35.00] * 20
        dates = [datetime(2025, 1, i + 1) for i in range(20)]

        result = analyzer._analyze_seasonal_patterns(prices, dates)
        assert result["analysis"] == "insufficient_data"
        assert "multiple months" in result["message"]

    def test_seasonal_with_multiple_months(self):
        """Test seasonal analysis with data spanning multiple months."""
        analyzer = PriceAnalyzer(price_history_file="/nonexistent.json")

        # Create data spanning January and February (at least 14 days, 2 months)
        prices = []
        dates = []
        # 10 days in January
        for i in range(10):
            prices.append(35.00)
            dates.append(datetime(2025, 1, 20 + i))
        # 10 days in February
        for i in range(10):
            prices.append(40.00)
            dates.append(datetime(2025, 2, 1 + i))

        result = analyzer._analyze_seasonal_patterns(prices, dates)

        assert result["analysis"] == "available"
        assert "monthly_averages" in result
        assert "best_month" in result
        assert "worst_month" in result
        assert result["best_month"]["month"] == "January"  # Lower price
        assert result["worst_month"]["month"] == "February"  # Higher price


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
        """Test that summary includes required product details."""
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
            assert "days_tracked" in product
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
