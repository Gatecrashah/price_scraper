#!/usr/bin/env python3
"""
Product Manager - Updates products.yaml based on GitHub Issue comments.
"""

import json
import os
import sys

import yaml


def manage_product_from_comment():
    """
    Reads issue and comment details from environment variables,
    updates products.yaml, and saves it.
    """
    try:
        issue_body = os.getenv("ISSUE_BODY")
        comment_body = os.getenv("COMMENT_BODY", "").strip().lower()
        config_file = "products.yaml"

        # Fallback: if issue_body is null, fetch via GitHub API
        if not issue_body or issue_body == "null":
            github_token = os.getenv("GITHUB_TOKEN")
            issue_number = os.getenv("ISSUE_NUMBER")
            repo = os.getenv("REPO")

            if github_token and issue_number and repo:
                import requests

                headers = {"Authorization": f"token {github_token}"}
                url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    issue_data = response.json()
                    issue_body = issue_data.get("body", "")

        # Extract action from comment (handle both direct comments and email replies)
        if comment_body in ["track", "ignore"]:
            action = comment_body
        elif comment_body.startswith("ignore"):
            action = "ignore"
        elif comment_body.startswith("track"):
            action = "track"
        else:
            print(f"Ignoring comment: '{comment_body}'. Not a valid command.")
            sys.exit(0)

        # Extract the JSON data block embedded in the issue body.
        try:
            # Find the start and end of the JSON block
            json_marker_pos = issue_body.find("```json")
            if json_marker_pos == -1:
                raise ValueError("Could not find '```json' marker in issue body")

            json_start = json_marker_pos + len("```json")
            # Skip any whitespace/newlines after ```json
            while json_start < len(issue_body) and issue_body[json_start] in [
                "\n",
                "\r",
                " ",
                "\t",
            ]:
                json_start += 1

            json_end = issue_body.find("```", json_start)
            if json_end == -1:
                raise ValueError("Could not find closing '```' marker in issue body")

            json_str = issue_body[json_start:json_end].strip()
            product_data = json.loads(json_str)

            product_url = product_data.get("url")
            product_name = product_data.get("name")
            product_site = product_data.get("site")

        except (IndexError, json.JSONDecodeError, AttributeError, ValueError) as e:
            print(
                f"Error: Could not find or parse the JSON data block in the issue body. Details: {e}"
            )
            sys.exit(1)

        # Load the current YAML config
        with open(config_file, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Ensure the site list exists in the config
        if "products" not in config:
            config["products"] = {}
        if product_site not in config["products"]:
            config["products"][product_site] = []

        # Remove any existing entry for this product to prevent duplicates
        config["products"][product_site] = [
            p for p in config["products"].get(product_site, []) if p.get("url") != product_url
        ]

        # Extract product_id from URL if possible
        product_id = None
        if product_site == "bjornborg":
            # Extract from URL like /fi/essential-socks-10-pack-10004564-mp001/
            import re

            id_match = re.search(r"-(\d+)-mp\d+", product_url)
            if id_match:
                product_id = id_match.group(1)
        elif product_site == "fitnesstukku":
            # Extract from URL like /whey-80-heraproteiini-4-kg/5854R.html
            url_parts = product_url.rstrip(".html").split("/")
            if len(url_parts) > 1:
                product_id = f"fitnesstukku_{url_parts[-1]}"

        # Add the new product with the specified status
        new_product = {
            "name": product_name,
            "url": product_url,
            "site": product_site,
            "status": action,
        }

        # Add product_id if we found one
        if product_id:
            new_product["product_id"] = product_id

        # Add category based on product name/site
        if product_site == "bjornborg":
            if "sock" in product_name.lower():
                new_product["category"] = "socks"
            elif "crew" in product_name.lower() or "sweater" in product_name.lower():
                new_product["category"] = "apparel"
            else:
                new_product["category"] = "unknown"
        elif product_site == "fitnesstukku":
            if "whey" in product_name.lower() or "protein" in product_name.lower():
                new_product["category"] = "protein"
            elif "creatine" in product_name.lower():
                new_product["category"] = "supplements"
            else:
                new_product["category"] = "nutrition"

        config["products"][product_site].append(new_product)

        # Save the updated config
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, indent=2, sort_keys=False, allow_unicode=True)

        print(f"Successfully processed command '{action}' for product '{product_name}'.")
        print(f"Updated {config_file}.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    manage_product_from_comment()
