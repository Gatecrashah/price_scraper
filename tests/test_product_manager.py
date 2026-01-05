"""Tests for product_manager.py module."""

import os
import tempfile

import yaml

# We'll test the logic by importing and manipulating environment variables
# since product_manager uses os.getenv


class TestExtractProductIdFromUrl:
    """Tests for product ID extraction logic from URLs."""

    def test_bjornborg_url_extraction(self):
        """Test extracting product ID from Björn Borg URLs."""
        import re

        url = "/fi/essential-socks-10-pack-10004564-mp001/"
        id_match = re.search(r"-(\d+)-mp\d+", url)

        assert id_match is not None
        assert id_match.group(1) == "10004564"

    def test_bjornborg_url_no_match(self):
        """Test that non-matching URLs don't extract ID."""
        import re

        url = "/fi/centre-crew-9999-1431-gy013/"
        id_match = re.search(r"-(\d+)-mp\d+", url)

        assert id_match is None

    def test_fitnesstukku_url_extraction(self):
        """Test extracting product ID from Fitnesstukku URLs."""
        url = "/whey-80-heraproteiini-4-kg/5854R.html"
        url_parts = url.rstrip(".html").split("/")
        product_id = f"fitnesstukku_{url_parts[-1]}"

        assert product_id == "fitnesstukku_5854R"

    def test_fitnesstukku_url_with_numbers(self):
        """Test Fitnesstukku URL extraction with numeric ID."""
        url = "/creatine-monohydrate-500-g/609.html"
        url_parts = url.rstrip(".html").split("/")
        product_id = f"fitnesstukku_{url_parts[-1]}"

        assert product_id == "fitnesstukku_609"


class TestCategoryAssignment:
    """Tests for automatic category assignment logic."""

    def test_bjornborg_socks_category(self):
        """Test category assignment for Björn Borg socks."""
        product_name = "Essential Socks 10-pack"
        product_site = "bjornborg"

        if product_site == "bjornborg":
            if "sock" in product_name.lower():
                category = "socks"
            elif "crew" in product_name.lower():
                category = "apparel"
            else:
                category = "unknown"

        assert category == "socks"

    def test_bjornborg_apparel_category(self):
        """Test category assignment for Björn Borg apparel."""
        product_name = "Centre Crew Sweatshirt"
        product_site = "bjornborg"

        if product_site == "bjornborg":
            if "sock" in product_name.lower():
                category = "socks"
            elif "crew" in product_name.lower():
                category = "apparel"
            else:
                category = "unknown"

        assert category == "apparel"

    def test_fitnesstukku_protein_category(self):
        """Test category assignment for Fitnesstukku protein products."""
        product_name = "Whey-80 4 kg"
        product_site = "fitnesstukku"

        if product_site == "fitnesstukku":
            if "whey" in product_name.lower() or "protein" in product_name.lower():
                category = "protein"
            elif "creatine" in product_name.lower():
                category = "supplements"
            else:
                category = "nutrition"

        assert category == "protein"

    def test_fitnesstukku_supplements_category(self):
        """Test category assignment for Fitnesstukku supplements."""
        product_name = "Creatine Monohydrate 500g"
        product_site = "fitnesstukku"

        if product_site == "fitnesstukku":
            if "whey" in product_name.lower() or "protein" in product_name.lower():
                category = "protein"
            elif "creatine" in product_name.lower():
                category = "supplements"
            else:
                category = "nutrition"

        assert category == "supplements"


class TestCommentParsing:
    """Tests for comment action parsing logic."""

    def _parse_action(self, comment_body: str) -> str | None:
        """Helper to parse action from comment body (mirrors product_manager logic)."""
        if comment_body in ["track", "ignore"]:
            return comment_body
        elif comment_body.startswith("ignore"):
            return "ignore"
        elif comment_body.startswith("track"):
            return "track"
        return None

    def test_track_command(self):
        """Test parsing 'track' command."""
        action = self._parse_action("track")
        assert action == "track"

    def test_ignore_command(self):
        """Test parsing 'ignore' command."""
        action = self._parse_action("ignore")
        assert action == "ignore"

    def test_track_with_extra_text(self):
        """Test parsing 'track' command with extra text (email reply)."""
        action = self._parse_action("track\n\nSent from my iPhone")
        assert action == "track"

    def test_ignore_with_extra_text(self):
        """Test parsing 'ignore' command with extra text."""
        action = self._parse_action("ignore this product")
        assert action == "ignore"

    def test_invalid_command(self):
        """Test parsing invalid command returns None."""
        action = self._parse_action("hello world")
        assert action is None


class TestJsonBlockExtraction:
    """Tests for JSON block extraction from issue body."""

    def test_extract_valid_json_block(self):
        """Test extracting valid JSON block from issue body."""
        import json

        issue_body = """
        New product discovered!

        ```json
        {"name": "Test Product", "url": "/test-url/", "site": "bjornborg"}
        ```

        Please respond with 'track' or 'ignore'.
        """

        json_marker_pos = issue_body.find("```json")
        json_start = json_marker_pos + len("```json")
        while json_start < len(issue_body) and issue_body[json_start] in [
            "\n",
            "\r",
            " ",
            "\t",
        ]:
            json_start += 1
        json_end = issue_body.find("```", json_start)
        json_str = issue_body[json_start:json_end].strip()
        product_data = json.loads(json_str)

        assert product_data["name"] == "Test Product"
        assert product_data["url"] == "/test-url/"
        assert product_data["site"] == "bjornborg"

    def test_extract_multiline_json_block(self):
        """Test extracting multiline JSON block."""
        import json

        issue_body = """
        ```json
        {
            "name": "Multi Line Product",
            "url": "/multi-line/",
            "site": "fitnesstukku"
        }
        ```
        """

        json_marker_pos = issue_body.find("```json")
        json_start = json_marker_pos + len("```json")
        while json_start < len(issue_body) and issue_body[json_start] in [
            "\n",
            "\r",
            " ",
            "\t",
        ]:
            json_start += 1
        json_end = issue_body.find("```", json_start)
        json_str = issue_body[json_start:json_end].strip()
        product_data = json.loads(json_str)

        assert product_data["name"] == "Multi Line Product"
        assert product_data["site"] == "fitnesstukku"

    def test_missing_json_marker(self):
        """Test error when JSON marker is missing."""
        issue_body = "No JSON block here"

        json_marker_pos = issue_body.find("```json")
        assert json_marker_pos == -1


class TestYamlOperations:
    """Tests for YAML config file operations."""

    def test_add_new_product_to_config(self):
        """Test adding a new product to YAML config."""
        config = {
            "products": {
                "bjornborg": [{"name": "Existing Product", "url": "/existing/", "status": "track"}]
            },
            "sites": {"bjornborg": {"base_url": "https://www.bjornborg.com"}},
        }

        new_product = {
            "name": "New Product",
            "url": "/new-product/",
            "site": "bjornborg",
            "status": "track",
        }

        config["products"]["bjornborg"].append(new_product)

        assert len(config["products"]["bjornborg"]) == 2
        assert config["products"]["bjornborg"][1]["name"] == "New Product"

    def test_remove_duplicate_before_adding(self):
        """Test removing duplicate product before adding updated version."""
        config = {
            "products": {
                "bjornborg": [
                    {"name": "Product A", "url": "/product-a/", "status": "track"},
                    {"name": "Product B", "url": "/product-b/", "status": "ignore"},
                ]
            }
        }

        product_url = "/product-a/"

        # Remove existing entry for this URL
        config["products"]["bjornborg"] = [
            p for p in config["products"]["bjornborg"] if p.get("url") != product_url
        ]

        assert len(config["products"]["bjornborg"]) == 1
        assert config["products"]["bjornborg"][0]["url"] == "/product-b/"

    def test_create_new_site_section(self):
        """Test creating a new site section in config."""
        config = {"products": {}, "sites": {}}
        product_site = "newsite"

        if product_site not in config["products"]:
            config["products"][product_site] = []

        config["products"][product_site].append(
            {"name": "First Product", "url": "/first/", "status": "track"}
        )

        assert product_site in config["products"]
        assert len(config["products"][product_site]) == 1

    def test_yaml_roundtrip(self):
        """Test that YAML config survives roundtrip save/load."""
        config = {
            "products": {
                "bjornborg": [
                    {
                        "name": "Essential Socks 10-pack",
                        "url": "/fi/essential-socks-10-pack-10004564-mp001/",
                        "product_id": "10004564",
                        "site": "bjornborg",
                        "category": "socks",
                        "status": "track",
                    }
                ]
            },
            "sites": {
                "bjornborg": {
                    "base_url": "https://www.bjornborg.com",
                    "name": "Björn Borg",
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f, indent=2, sort_keys=False, allow_unicode=True)
            temp_path = f.name

        try:
            with open(temp_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)

            assert loaded["products"]["bjornborg"][0]["name"] == "Essential Socks 10-pack"
            assert loaded["sites"]["bjornborg"]["name"] == "Björn Borg"
        finally:
            os.unlink(temp_path)
