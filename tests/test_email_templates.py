"""Tests for email_templates.py module."""

from email_templates import EmailTemplates


class TestEmailTemplatesColors:
    """Tests for EmailTemplates color configuration."""

    def test_colors_defined(self):
        """Test that all required colors are defined."""
        colors = EmailTemplates.COLORS

        assert "text_primary" in colors
        assert "text_secondary" in colors
        assert "bg_cream" in colors
        assert "bg_white" in colors
        assert "price_drop" in colors
        assert "price_increase" in colors
        assert "bjornborg" in colors
        assert "fitnesstukku" in colors

    def test_colors_are_valid_hex(self):
        """Test that colors are valid hex codes."""
        for name, color in EmailTemplates.COLORS.items():
            assert color.startswith("#"), f"Color {name} should start with #"
            # Hex color should be 4 or 7 chars (#RGB or #RRGGBB)
            assert len(color) in [4, 7], f"Color {name} has invalid length"


class TestFormatPriceBadge:
    """Tests for _format_price_badge method."""

    def test_format_current_price(self):
        """Test formatting current price badge."""
        result = EmailTemplates._format_price_badge(35.96, is_current=True)

        assert "35.96" in result
        assert "EUR" in result
        assert "line-through" not in result

    def test_format_previous_price(self):
        """Test formatting previous (crossed out) price badge."""
        result = EmailTemplates._format_price_badge(44.95, is_current=False)

        assert "44.95" in result
        assert "line-through" in result

    def test_format_large_price(self):
        """Test formatting with large size."""
        result = EmailTemplates._format_price_badge(99.99, is_current=True, size="large")

        assert "32px" in result

    def test_format_small_price(self):
        """Test formatting with small size."""
        result = EmailTemplates._format_price_badge(99.99, is_current=True, size="small")

        assert "18px" in result


class TestFormatProductChange:
    """Tests for format_product_change method."""

    def test_format_price_drop(self):
        """Test formatting a price drop."""
        change = {
            "name": "Test Product",
            "current_price": 35.96,
            "previous_price": 44.95,
            "purchase_url": "https://example.com/product",
        }

        result = EmailTemplates.format_product_change(change)

        assert "Test Product" in result
        assert "35.96" in result
        assert "44.95" in result
        assert "Save" in result
        assert "▼" in result

    def test_format_price_increase(self):
        """Test formatting a price increase."""
        change = {
            "name": "Test Product",
            "current_price": 44.95,
            "previous_price": 35.96,
            "purchase_url": "https://example.com/product",
        }

        result = EmailTemplates.format_product_change(change)

        assert "Up" in result
        assert "▲" in result

    def test_format_with_brand(self):
        """Test formatting with brand information."""
        change = {
            "name": "Essential Socks",
            "current_price": 35.96,
            "previous_price": 44.95,
            "purchase_url": "https://example.com/product",
            "brand": "BJÖRN BORG",
        }

        result = EmailTemplates.format_product_change(change)

        assert "BJÖRN BORG" in result

    def test_format_with_original_price(self):
        """Test formatting with original price (RRP discount)."""
        change = {
            "name": "Test Product",
            "current_price": 35.96,
            "previous_price": 40.00,
            "original_price": 49.95,
            "purchase_url": "https://example.com/product",
        }

        result = EmailTemplates.format_product_change(change)

        assert "off RRP" in result
        assert "Originally" in result
        assert "49.95" in result

    def test_format_with_lowest_price_ever(self):
        """Test formatting when current price is lowest ever."""
        change = {
            "name": "Test Product",
            "current_price": 30.00,
            "previous_price": 35.00,
            "lowest_price": 30.00,
            "lowest_price_date": "2025-01-01",
            "purchase_url": "https://example.com/product",
        }

        result = EmailTemplates.format_product_change(change)

        assert "Lowest price ever" in result

    def test_format_with_historical_low(self):
        """Test formatting with historical low (not current)."""
        change = {
            "name": "Test Product",
            "current_price": 35.00,
            "previous_price": 40.00,
            "lowest_price": 30.00,
            "lowest_price_date": "2025-01-01",
            "purchase_url": "https://example.com/product",
        }

        result = EmailTemplates.format_product_change(change)

        assert "Historical Low" in result
        assert "30.00" in result

    def test_format_includes_cta_button(self):
        """Test that CTA button is included."""
        change = {
            "name": "Test Product",
            "current_price": 35.96,
            "previous_price": 44.95,
            "purchase_url": "https://example.com/product",
        }

        result = EmailTemplates.format_product_change(change)

        assert "View Deal" in result
        assert "https://example.com/product" in result


class TestCreatePriceAlertEmail:
    """Tests for create_price_alert_email method."""

    def test_empty_changes_returns_message(self):
        """Test that empty changes returns a simple message."""
        result = EmailTemplates.create_price_alert_email([])

        assert result == "No price changes detected."

    def test_single_change_creates_valid_html(self):
        """Test that single change creates valid HTML."""
        changes = [
            {
                "name": "Test Product",
                "current_price": 35.96,
                "previous_price": 44.95,
                "purchase_url": "https://www.bjornborg.com/product",
                "site": "bjornborg",
            }
        ]

        result = EmailTemplates.create_price_alert_email(changes)

        assert "<!DOCTYPE html>" in result
        assert "Price Alert" in result
        assert "Test Product" in result
        assert "Björn Borg" in result

    def test_groups_by_site(self):
        """Test that products are grouped by site."""
        changes = [
            {
                "name": "BB Product",
                "current_price": 35.96,
                "previous_price": 44.95,
                "purchase_url": "https://www.bjornborg.com/product",
                "site": "bjornborg",
            },
            {
                "name": "FT Product",
                "current_price": 89.90,
                "previous_price": 99.90,
                "purchase_url": "https://www.fitnesstukku.fi/product",
                "site": "fitnesstukku",
            },
        ]

        result = EmailTemplates.create_price_alert_email(changes)

        assert "Björn Borg" in result
        assert "Fitnesstukku" in result
        assert "BB Product" in result
        assert "FT Product" in result

    def test_counts_drops_and_increases(self):
        """Test that email counts drops and increases correctly."""
        changes = [
            {
                "name": "Drop Product",
                "current_price": 30.00,
                "previous_price": 40.00,
                "purchase_url": "https://example.com/1",
            },
            {
                "name": "Increase Product",
                "current_price": 50.00,
                "previous_price": 40.00,
                "purchase_url": "https://example.com/2",
            },
        ]

        result = EmailTemplates.create_price_alert_email(changes)

        # Should show counts in summary bar
        assert "2" in result  # Total updates


class TestCreateFailureAlertEmail:
    """Tests for create_failure_alert_email method."""

    def test_creates_valid_html(self):
        """Test that failure alert creates valid HTML."""
        result = EmailTemplates.create_failure_alert_email("Connection timeout")

        assert "<!DOCTYPE html>" in result
        assert "Monitoring Interrupted" in result

    def test_includes_error_details(self):
        """Test that error details are included."""
        error = "Failed to fetch URL: 404 Not Found"
        result = EmailTemplates.create_failure_alert_email(error)

        assert error in result
        assert "Error Details" in result

    def test_includes_possible_causes(self):
        """Test that possible causes are listed."""
        result = EmailTemplates.create_failure_alert_email("Test error")

        assert "Possible Causes" in result
        assert "Product URLs have changed" in result
        assert "Website structure" in result
        assert "Anti-bot" in result

    def test_includes_recommended_actions(self):
        """Test that recommended actions are listed."""
        result = EmailTemplates.create_failure_alert_email("Test error")

        assert "Recommended Actions" in result
        assert "GitHub Actions logs" in result


class TestCreateTestEmail:
    """Tests for create_test_email method."""

    def test_creates_valid_html(self):
        """Test that test email creates valid HTML."""
        result = EmailTemplates.create_test_email()

        assert "<!DOCTYPE html>" in result
        assert "Connection Verified" in result

    def test_includes_success_indicator(self):
        """Test that success indicator is present."""
        result = EmailTemplates.create_test_email()

        assert "Email Configuration Successful" in result
        assert "Operational" in result

    def test_includes_provider_info(self):
        """Test that email provider info is shown."""
        result = EmailTemplates.create_test_email()

        assert "Resend API" in result


class TestCreateAnalysisReportEmail:
    """Tests for create_analysis_report_email method."""

    def test_creates_valid_html(self):
        """Test that analysis report creates valid HTML."""
        report_data = {
            "period": "Monthly",
            "date_range": "January 2025",
            "products": [],
            "summary": {"average_savings": 15, "price_changes": 5},
        }

        result = EmailTemplates.create_analysis_report_email(report_data)

        assert "<!DOCTYPE html>" in result
        assert "Price Analysis" in result
        assert "Monthly Report" in result

    def test_includes_summary_stats(self):
        """Test that summary statistics are included."""
        report_data = {
            "period": "Monthly",
            "date_range": "January 2025",
            "products": [
                {"name": "Product 1"},
                {"name": "Product 2"},
            ],
            "summary": {"average_savings": 20, "price_changes": 8},
        }

        result = EmailTemplates.create_analysis_report_email(report_data)

        assert "Products Tracked" in result
        assert "Avg. Discount" in result
        assert "Price Changes" in result

    def test_includes_best_deal_section(self):
        """Test that best deal is highlighted when present."""
        report_data = {
            "period": "Monthly",
            "date_range": "January 2025",
            "products": [],
            "summary": {
                "average_savings": 15,
                "price_changes": 5,
                "best_deal": {
                    "name": "Best Deal Product",
                    "lowest_price": 29.99,
                    "discount": 30,
                },
            },
        }

        result = EmailTemplates.create_analysis_report_email(report_data)

        assert "Best Deal This Period" in result
        assert "Best Deal Product" in result
        assert "29.99" in result

    def test_includes_product_analysis(self):
        """Test that individual product analysis is included."""
        report_data = {
            "period": "Quarterly",
            "date_range": "Q1 2025",
            "products": [
                {
                    "name": "Test Product",
                    "current_price": 35.00,
                    "lowest_price": 30.00,
                    "highest_price": 45.00,
                    "average_price": 37.50,
                    "trend": "down",
                }
            ],
            "summary": {"average_savings": 10, "price_changes": 3},
        }

        result = EmailTemplates.create_analysis_report_email(report_data)

        assert "Product Overview" in result
        assert "Test Product" in result
        assert "Current" in result
        assert "Lowest" in result
        assert "Highest" in result
        assert "Average" in result

    def test_trend_indicators(self):
        """Test that trend indicators are shown correctly."""
        report_data = {
            "period": "Monthly",
            "date_range": "January 2025",
            "products": [
                {
                    "name": "Down Product",
                    "trend": "down",
                    "current_price": 30,
                    "lowest_price": 30,
                    "highest_price": 40,
                    "average_price": 35,
                },
                {
                    "name": "Up Product",
                    "trend": "up",
                    "current_price": 40,
                    "lowest_price": 30,
                    "highest_price": 40,
                    "average_price": 35,
                },
                {
                    "name": "Stable Product",
                    "trend": "stable",
                    "current_price": 35,
                    "lowest_price": 35,
                    "highest_price": 35,
                    "average_price": 35,
                },
            ],
            "summary": {"average_savings": 10, "price_changes": 3},
        }

        result = EmailTemplates.create_analysis_report_email(report_data)

        # Should contain trend symbols
        assert "▼" in result  # Down trend
        assert "▲" in result  # Up trend
        assert "→" in result  # Stable trend


class TestLegacyMethods:
    """Tests for legacy backward-compatibility methods."""

    def test_get_base_styles_returns_empty(self):
        """Test that legacy get_base_styles returns empty string."""
        result = EmailTemplates.get_base_styles()
        assert result == ""

    def test_get_analysis_report_styles_returns_empty(self):
        """Test that legacy get_analysis_report_styles returns empty string."""
        result = EmailTemplates.get_analysis_report_styles()
        assert result == ""


class TestEmailWrapper:
    """Tests for _email_wrapper method."""

    def test_wrapper_includes_doctype(self):
        """Test that wrapper includes DOCTYPE."""
        result = EmailTemplates._email_wrapper("<tr><td>Test</td></tr>")

        assert "<!DOCTYPE html>" in result

    def test_wrapper_includes_preheader(self):
        """Test that wrapper includes preheader text."""
        result = EmailTemplates._email_wrapper("<tr><td>Test</td></tr>", preheader="Test preheader")

        assert "Test preheader" in result

    def test_wrapper_uses_cream_background(self):
        """Test that wrapper uses cream background color."""
        result = EmailTemplates._email_wrapper("<tr><td>Test</td></tr>")

        assert EmailTemplates.COLORS["bg_cream"] in result

    def test_wrapper_sets_max_width(self):
        """Test that wrapper sets max width for email."""
        result = EmailTemplates._email_wrapper("<tr><td>Test</td></tr>")

        assert "max-width: 600px" in result
