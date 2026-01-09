"""
Scraper package for multi-site price monitoring.

This package contains modular scrapers for different e-commerce sites,
designed for robustness and maintainability.
"""

from .bjornborg import BjornBorgScraper
from .fitnesstukku import FitnesstukkuScraper
from .shopify_scraper import (
    Apteekki360Scraper,
    RuohonjuuriScraper,
    ShopifyScraper,
    SinunapteekkiScraper,
)
from .tokmanni import TokmanniScraper

__all__ = [
    "BjornBorgScraper",
    "FitnesstukkuScraper",
    "ShopifyScraper",
    "Apteekki360Scraper",
    "SinunapteekkiScraper",
    "RuohonjuuriScraper",
    "TokmanniScraper",
]
