"""Daily price monitor: scrape every product URL, record changes, email what changed.

A product has one or more store URLs. Its price is the lowest in-stock price across them.
"""

import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlsplit

import requests
import yaml

import emails
from scraper import Offer, fetch_offer

CONFIG_FILE = Path("products.yaml")
HISTORY_FILE = Path("price_history.json")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    urls: list[str]


@dataclass(frozen=True)
class Failed:
    error: str


class StoreState(TypedDict):
    url: str
    price: float | None
    original_price: float | None
    available: bool
    error: str | None


class Lowest(TypedDict):
    price: float
    store: str
    url: str
    date: str


class Event(TypedDict):
    date: str
    store: str
    price: float
    original_price: float | None
    available: bool


class ProductHistory(TypedDict):
    name: str
    stores: dict[str, StoreState]
    current_lowest: Lowest | None
    all_time_lowest: Lowest | None
    price_changes: list[Event]


@dataclass(frozen=True)
class PriceChange:
    name: str
    store: str
    url: str
    price: float
    previous_price: float
    original_price: float | None
    all_time_lowest: Lowest | None
    in_stock_prices: dict[str, float]


@dataclass(frozen=True)
class NewFailure:
    name: str
    url: str
    error: str


@dataclass(frozen=True)
class Recovered:
    name: str
    url: str
    price: float
    available: bool


def store_name(url: str) -> str:
    """https://www.bjornborg.com/fi/... -> bjornborg"""
    return (urlsplit(url).hostname or url).removeprefix("www.").split(".")[0]


def load_products(path: Path) -> list[Product]:
    products = [Product(**entry) for entry in yaml.safe_load(path.read_text("utf-8"))["products"]]
    ids = [p.id for p in products]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate product ids in {path}")
    for product in products:
        stores = [store_name(url) for url in product.urls]
        if len(set(stores)) != len(stores):
            raise ValueError(f"{product.id}: more than one URL for the same store")
    return products


def new_history() -> ProductHistory:
    return {
        "name": "",
        "stores": {},
        "current_lowest": None,
        "all_time_lowest": None,
        "price_changes": [],
    }


def update_product(
    entry: ProductHistory, product: Product, results: dict[str, Offer | Failed], today: str
) -> tuple[PriceChange | None, list[NewFailure], list[Recovered]]:
    """Fold today's scrape results into the product's history.

    Returns the change in the lowest in-stock price, if any, the URLs that started failing
    and the URLs that work again after failing.
    """
    previous = entry["stores"]
    entry["name"] = product.name
    entry["stores"] = {}
    failures = []
    recoveries = []

    for url, result in results.items():
        store = store_name(url)
        before = previous.get(store)
        if isinstance(result, Failed):
            if before is None or before["error"] is None:
                failures.append(NewFailure(product.name, url, result.error))
            entry["stores"][store] = {
                "url": url,
                "price": before["price"] if before else None,
                "original_price": before["original_price"] if before else None,
                "available": before["available"] if before else False,
                "error": result.error,
            }
            continue
        if before is not None and before["error"] is not None:
            recoveries.append(Recovered(product.name, url, result.price, result.available))
        if before is None or (before["price"], before["available"]) != (
            result.price,
            result.available,
        ):
            entry["price_changes"].append(
                {
                    "date": today,
                    "store": store,
                    "price": result.price,
                    "original_price": result.original_price,
                    "available": result.available,
                }
            )
        entry["stores"][store] = {
            "url": url,
            "price": result.price,
            "original_price": result.original_price,
            "available": result.available,
            "error": None,
        }

    in_stock = {
        store: state["price"]
        for store, state in entry["stores"].items()
        if state["error"] is None and state["available"] and state["price"] is not None
    }
    if not in_stock:
        return None, failures, recoveries

    store = min(in_stock, key=lambda s: in_stock[s])
    price = in_stock[store]
    url = entry["stores"][store]["url"]
    before_lowest = entry["current_lowest"]
    all_time = entry["all_time_lowest"]

    change = None
    since = today
    if before_lowest is not None:
        if price == before_lowest["price"]:
            since = before_lowest["date"]
        else:
            change = PriceChange(
                name=product.name,
                store=store,
                url=url,
                price=price,
                previous_price=before_lowest["price"],
                original_price=entry["stores"][store]["original_price"],
                all_time_lowest=all_time,
                in_stock_prices=in_stock,
            )

    entry["current_lowest"] = {"price": price, "store": store, "url": url, "date": since}
    if all_time is None or price < all_time["price"]:
        entry["all_time_lowest"] = {"price": price, "store": store, "url": url, "date": today}
    return change, failures, recoveries


def scrape(session: requests.Session, url: str) -> Offer | Failed:
    try:
        return fetch_offer(session, url)
    except Exception as e:
        return Failed(f"{type(e).__name__}: {e}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    dry_run = "--dry-run" in sys.argv[1:]

    products = load_products(CONFIG_FILE)
    history: dict[str, ProductHistory] = (
        json.loads(HISTORY_FILE.read_text("utf-8")) if HISTORY_FILE.exists() else {}
    )
    today = date.today().isoformat()
    session = requests.Session()
    changes: list[PriceChange] = []
    failures: list[NewFailure] = []
    recoveries: list[Recovered] = []

    for product in products:
        logger.info(product.name)
        results = {}
        for url in product.urls:
            results[url] = scrape(session, url)
            if isinstance(results[url], Failed):
                logger.warning("  FAILED %s: %s", url, results[url].error)
            else:
                stock = "in stock" if results[url].available else "out of stock"
                logger.info("  %s: %.2f € (%s)", store_name(url), results[url].price, stock)
            time.sleep(1)
        change, failed, recovered = update_product(
            history.setdefault(product.id, new_history()), product, results, today
        )
        if change:
            logger.info("  CHANGED %.2f -> %.2f €", change.previous_price, change.price)
            changes.append(change)
        failures.extend(failed)
        recoveries.extend(recovered)

    logger.info(
        "%d price change(s), %d newly failing URL(s), %d URL(s) working again",
        len(changes),
        len(failures),
        len(recoveries),
    )
    if dry_run:
        return

    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", "utf-8")
    if changes or failures or recoveries:
        emails.send(*emails.render_alert(changes, failures, recoveries))


if __name__ == "__main__":
    main()
