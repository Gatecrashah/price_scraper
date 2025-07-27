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
    print("DEBUG: Starting product_manager.py execution")
    try:
        issue_body = os.getenv('ISSUE_BODY')
        comment_body = os.getenv('COMMENT_BODY', '').strip().lower()
        config_file = 'products.yaml'
        
        print(f"DEBUG: comment_body='{comment_body}'")
        print(f"DEBUG: issue_body length={len(issue_body) if issue_body else 0}")
        print(f"DEBUG: config_file='{config_file}'")

        # The action is the comment itself. Exit gracefully if not a valid command.
        if comment_body not in ['track', 'ignore']:
            print(f"DEBUG: Ignoring comment: '{comment_body}'. Not a valid command.")
            print(f"DEBUG: Exiting gracefully")
            sys.exit(0)
        
        print(f"DEBUG: Valid command received: '{comment_body}'")
        
        action = comment_body

        # Extract the JSON data block embedded in the issue body.
        print("DEBUG: Starting JSON extraction from issue body")
        try:
            # Find the start and end of the JSON block
            print(f"DEBUG: Looking for ```json marker in issue body")
            print(f"DEBUG: Issue body contains '```json': {'```json' in issue_body}")
            
            json_marker_pos = issue_body.find('```json')
            print(f"DEBUG: json_marker_pos = {json_marker_pos}")
            
            if json_marker_pos == -1:
                print("DEBUG: Could not find ```json marker")
                print(f"DEBUG: Full issue body: {repr(issue_body)}")
                raise ValueError("Could not find '```json' marker in issue body")
                
            json_start = json_marker_pos + len('```json')
            print(f"DEBUG: Found ```json at position {json_marker_pos}, content starts at {json_start}")
            
            # Skip any whitespace/newlines after ```json
            while json_start < len(issue_body) and issue_body[json_start] in ['\n', '\r', ' ', '\t']:
                json_start += 1
                
            json_end = issue_body.find('```', json_start)
            if json_end == -1:
                print("DEBUG: Could not find closing ``` marker")
                raise ValueError("Could not find closing '```' marker in issue body")
                
            print(f"DEBUG: Found closing ``` at position {json_end}")
            json_str = issue_body[json_start:json_end].strip()
            print(f"DEBUG: Extracted JSON string: {repr(json_str)}")
            
            product_data = json.loads(json_str)
            print(f"DEBUG: Successfully parsed JSON: {product_data}")
            
            product_url = product_data.get('url')
            product_name = product_data.get('name')
            product_site = product_data.get('site')
            
            print(f"DEBUG: Parsed product data - site: {product_site}, name: {product_name}, url: {product_url}")
            print("DEBUG: Starting YAML file processing")
            
        except (IndexError, json.JSONDecodeError, AttributeError, ValueError) as e:
            print(f"Error: Could not find or parse the JSON data block in the issue body. Details: {e}")
            print(f"DEBUG: Issue body content: {repr(issue_body)}")
            sys.exit(1)

        # Load the current YAML config
        print(f"DEBUG: Loading YAML config from {config_file}")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"DEBUG: Successfully loaded YAML config")

        # Ensure the site list exists in the config
        if 'products' not in config: 
            config['products'] = {}
        if product_site not in config['products']: 
            config['products'][product_site] = []
        
        # Remove any existing entry for this product to prevent duplicates
        config['products'][product_site] = [
            p for p in config['products'].get(product_site, []) if p.get('url') != product_url
        ]

        # Extract product_id from URL if possible
        product_id = None
        if product_site == "bjornborg":
            # Extract from URL like /fi/essential-socks-10-pack-10004564-mp001/
            import re
            id_match = re.search(r'-(\d+)-mp\d+', product_url)
            if id_match:
                product_id = id_match.group(1)
        elif product_site == "fitnesstukku":
            # Extract from URL like /whey-80-heraproteiini-4-kg/5854R.html
            url_parts = product_url.rstrip('.html').split('/')
            if len(url_parts) > 1:
                product_id = f"fitnesstukku_{url_parts[-1]}"
        
        # Add the new product with the specified status
        new_product = {
            "name": product_name,
            "url": product_url,
            "site": product_site,
            "status": action
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
        config['products'][product_site].append(new_product)

        # Save the updated config
        print(f"DEBUG: Saving updated config to {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, indent=2, sort_keys=False, allow_unicode=True)
        print(f"DEBUG: Successfully saved YAML config")

        print(f"Successfully processed command '{action}' for product '{product_name}'.")
        print(f"Updated {config_file}.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    manage_product_from_comment()