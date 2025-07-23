"""
Scraper package for multi-site price monitoring.

This package contains modular scrapers for different e-commerce sites,
designed for robustness and maintainability.
"""

from .bjornborg import BjornBorgScraper
from .fitnesstukku import FitnesstukuScraper

__all__ = ['BjornBorgScraper', 'FitnesstukuScraper']