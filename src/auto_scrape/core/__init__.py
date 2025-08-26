"""Core components for auto scraper."""

from .config import ScrapingConfig, SiteConfig, BrowserConfig, ExcelConfig
from .scraper import WebScraper

__all__ = ["ScrapingConfig", "SiteConfig", "BrowserConfig", "ExcelConfig", "WebScraper"]