#!/usr/bin/env python3
"""
Migration script to convert price history files from daily-snapshot format
to event-based format.

Old format: Every day's price is stored
New format: Only price changes are stored as events
"""

import json
import os
import shutil
from datetime import datetime


def migrate_price_history(input_file: str = "price_history.json") -> dict:
    """
    Migrate price_history.json from daily snapshots to event-based format.

    Old format:
    {
        "product_key": {
            "name": "...",
            "purchase_url": "...",
            "price_history": {
                "2025-07-04": {"current_price": 35.96, "original_price": 44.95, ...},
                "2025-07-05": {"current_price": 35.96, ...},
                ...
            }
        }
    }

    New format:
    {
        "product_key": {
            "name": "...",
            "purchase_url": "...",
            "current": {"price": 35.96, "original_price": 44.95, "since": "2025-07-04"},
            "all_time_lowest": {"price": 26.97, "date": "2025-11-25"},
            "price_changes": [
                {"date": "2025-07-04", "price": 35.96, "type": "initial"},
                {"date": "2025-08-05", "from": 35.96, "to": 38.21, "change_pct": 6.3},
                ...
            ]
        }
    }
    """
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return {}

    with open(input_file, encoding="utf-8") as f:
        old_data = json.load(f)

    new_data = {}
    total_old_entries = 0
    total_new_entries = 0

    for product_key, product_data in old_data.items():
        history = product_data.get("price_history", {})

        if not history:
            continue

        # Sort dates chronologically
        sorted_dates = sorted(history.keys())
        total_old_entries += len(sorted_dates)

        # Extract price change events
        price_changes = []
        prev_price = None
        current_price_since = None
        all_time_lowest = {"price": float("inf"), "date": None}

        for date in sorted_dates:
            entry = history[date]
            price = entry.get("current_price")
            original = entry.get("original_price")
            discount = entry.get("discount_percent")

            if price is None:
                continue

            # Track all-time lowest
            if price < all_time_lowest["price"]:
                all_time_lowest = {
                    "price": price,
                    "date": date,
                    "original_price": original,
                }

            # Check for price change
            if prev_price is None:
                # First entry
                price_changes.append(
                    {
                        "date": date,
                        "price": price,
                        "original_price": original,
                        "discount_pct": discount,
                        "type": "initial",
                    }
                )
                current_price_since = date
                total_new_entries += 1
            elif abs(price - prev_price) > 0.01:
                # Price changed
                change_pct = (
                    round(((price - prev_price) / prev_price) * 100, 1) if prev_price else 0
                )
                price_changes.append(
                    {
                        "date": date,
                        "from": prev_price,
                        "to": price,
                        "change_pct": change_pct,
                        "original_price": original,
                        "discount_pct": discount,
                    }
                )
                current_price_since = date
                total_new_entries += 1

            prev_price = price

        # Build new product entry
        if price_changes:
            last_entry = history[sorted_dates[-1]]
            new_data[product_key] = {
                "name": product_data.get("name", "Unknown"),
                "purchase_url": product_data.get("purchase_url", ""),
                "current": {
                    "price": last_entry.get("current_price"),
                    "original_price": last_entry.get("original_price"),
                    "discount_pct": last_entry.get("discount_percent"),
                    "since": current_price_since,
                },
                "all_time_lowest": all_time_lowest if all_time_lowest["date"] else None,
                "price_changes": price_changes,
            }

    print("Migration complete:")
    print(f"  Products: {len(new_data)}")
    print(f"  Old entries: {total_old_entries}")
    print(f"  New entries (changes only): {total_new_entries}")
    print(f"  Compression ratio: {total_old_entries / max(total_new_entries, 1):.1f}x")

    return new_data


def migrate_ean_price_history(input_file: str = "ean_price_history.json") -> dict:
    """
    Migrate ean_price_history.json from daily snapshots to event-based format.

    Old format stores every day's price per store.
    New format stores only price changes as events.
    """
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return {}

    with open(input_file, encoding="utf-8") as f:
        old_data = json.load(f)

    new_data = {}

    for ean, ean_data in old_data.items():
        stores_data = ean_data.get("stores", {})

        # Process each store's price history
        new_stores = {}
        all_price_changes = []

        for store_name, store_data in stores_data.items():
            history = store_data.get("price_history", {})

            if not history:
                continue

            sorted_dates = sorted(history.keys())
            prev_price = None
            prev_available = None

            for date in sorted_dates:
                entry = history[date]
                price = entry.get("price")
                available = entry.get("available", True)

                # Check for price or availability change
                price_changed = (
                    prev_price is not None and price is not None and abs(price - prev_price) > 0.01
                )
                avail_changed = prev_available is not None and available != prev_available

                if prev_price is None:
                    # Initial entry
                    all_price_changes.append(
                        {
                            "date": date,
                            "store": store_name,
                            "price": price,
                            "available": available,
                            "type": "initial",
                        }
                    )
                elif price_changed or avail_changed:
                    change_entry = {
                        "date": date,
                        "store": store_name,
                        "available": available,
                    }
                    if price_changed:
                        change_pct = (
                            round(((price - prev_price) / prev_price) * 100, 1) if prev_price else 0
                        )
                        change_entry["from"] = prev_price
                        change_entry["to"] = price
                        change_entry["change_pct"] = change_pct
                    if avail_changed:
                        change_entry["availability_changed"] = True
                        change_entry["from_available"] = prev_available

                    all_price_changes.append(change_entry)

                prev_price = price
                prev_available = available

            # Store current state for this store
            if sorted_dates:
                last_entry = history[sorted_dates[-1]]
                new_stores[store_name] = {
                    "url": store_data.get("url"),
                    "current_price": last_entry.get("price"),
                    "available": last_entry.get("available", True),
                    "last_updated": sorted_dates[-1],
                }

        # Sort all price changes chronologically
        all_price_changes.sort(key=lambda x: (x["date"], x["store"]))

        # Determine current lowest and all-time lowest
        current_lowest = ean_data.get("cross_store_lowest", {})
        all_time_lowest = ean_data.get("all_time_lowest")

        # Get most recent cross-store lowest
        if current_lowest:
            latest_date = max(current_lowest.keys())
            current_lowest_entry = current_lowest[latest_date]
        else:
            current_lowest_entry = None

        new_data[ean] = {
            "name": ean_data.get("name", "Unknown"),
            "stores": new_stores,
            "current_lowest": current_lowest_entry,
            "all_time_lowest": all_time_lowest,
            "price_changes": all_price_changes,
        }

    return new_data


def backup_and_migrate(file_path: str, migrate_func) -> bool:
    """Backup original file and perform migration."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    # Create backup
    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(file_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Perform migration
    new_data = migrate_func(file_path)

    if not new_data:
        print("Migration produced no data, keeping original file")
        return False

    # Write new format
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"Migration saved to: {file_path}")
    return True


def main():
    """Run migrations for both history files."""
    print("=" * 60)
    print("Price History Migration Tool")
    print("=" * 60)

    print("\n1. Migrating price_history.json...")
    print("-" * 40)
    backup_and_migrate("price_history.json", migrate_price_history)

    print("\n2. Migrating ean_price_history.json...")
    print("-" * 40)
    backup_and_migrate("ean_price_history.json", migrate_ean_price_history)

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
