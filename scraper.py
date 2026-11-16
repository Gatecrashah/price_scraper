"""Read a product's price and availability from a store page's structured data."""

import json
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass(frozen=True)
class Offer:
    price: float
    available: bool
    original_price: float | None = None


class NoProductData(Exception):
    """The page loaded but carries no product data we know how to read."""


def fetch_offer(session: requests.Session, url: str) -> Offer:
    response = session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return parse_offer(response.text)


def parse_offer(html: str) -> Offer:
    soup = BeautifulSoup(html, "html.parser")
    offer = _from_json_ld(soup) or _from_tracking_view(soup)
    if offer is None:
        raise NoProductData("no product data on page")
    return offer


def _from_json_ld(soup: BeautifulSoup) -> Offer | None:
    """schema.org Product: Björn Borg, Tokmanni and the Shopify stores."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if not isinstance(item, dict) or item.get("@type") != "Product":
                continue
            offers = item.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else None
            if not isinstance(offers, dict) or offers.get("price") is None:
                continue
            spec = offers.get("priceSpecification")
            is_strikethrough = isinstance(spec, dict) and str(spec.get("priceType", "")).endswith(
                "StrikethroughPrice"
            )
            return Offer(
                price=float(offers["price"]),
                available="InStock" in offers.get("availability", ""),
                original_price=float(spec["price"]) if is_strikethrough else None,
            )
    return None


def _from_tracking_view(soup: BeautifulSoup) -> Offer | None:
    """Fitnesstukku has no JSON-LD Product; its analytics `var view = [...]` has the price."""
    for script in soup.find_all("script"):
        match = re.search(r"var view = (\[.*\])", script.string or "")
        if not match:
            continue
        try:
            events = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        for event in events:
            if isinstance(event, dict) and event.get("event") == "productDetail":
                product = event["ecommerce"]["detail"]["products"][0]
                return Offer(
                    price=float(product["price"]),
                    available=product.get("availability", "").upper() == "IN STOCK",
                )
    return None
