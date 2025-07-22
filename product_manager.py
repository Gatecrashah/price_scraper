#!/usr/bin/env python3
"""
Product Manager - Updates products.yaml based on GitHub Issue comments.
"""

import os
import sys
import json
import yaml


def manage_product_from_comment():
    """
    Reads issue and comment details from environment variables,
    updates products.yaml, and saves it.
    """
    try:
        issue_body = os.getenv('ISSUE_BODY')
        comment_body = os.getenv('COMMENT_BODY', '').strip().lower()
        config_file = 'products.yaml'

        # The action is the comment itself. Exit gracefully if not a valid command.
        if comment_body not in ['track', 'ignore']:
            print(f"Ignoring comment: '{comment_body}'. Not a valid command.")
            sys.exit(0)
        
        action = comment_body

        # Extract the JSON data block embedded in the issue body.
        try:
            # Find the start and end of the JSON block
            json_start = issue_body.find('```json') + len('```json\n')
            json_end = issue_body.find('```', json_start)
            json_str = issue_body[json_start:json_end]
            product_data = json.loads(json_str)
            
            product_url = product_data.get('url')
            product_name = product_data.get('name')
            product_site = product_data.get('site')
        except (IndexError, json.JSONDecodeError, AttributeError) as e:
            print(f"Error: Could not find or parse the JSON data block in the issue body. Details: {e}")
            sys.exit(1)

        # Load the current YAML config
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Ensure the site list exists in the config
        if 'products' not in config: 
            config['products'] = {}
        if product_site not in config['products']: 
            config['products'][product_site] = []
        
        # Remove any existing entry for this product to prevent duplicates
        config['products'][product_site] = [
            p for p in config['products'].get(product_site, []) if p.get('url') != product_url
        ]

        # Add the new product with the specified status
        new_product = {
            "name": product_name,
            "url": product_url,
            "site": product_site,
            "status": action
        }
        config['products'][product_site].append(new_product)

        # Save the updated config
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, indent=2, sort_keys=False, allow_unicode=True)

        print(f"Successfully processed command '{action}' for product '{product_name}'.")
        print(f"Updated {config_file}.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    manage_product_from_comment()