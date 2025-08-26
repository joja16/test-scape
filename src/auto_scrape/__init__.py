"""Auto Scrape - Web scraping automation with Playwright and Excel integration."""

__version__ = "1.0.0"
__author__ = "Auto Scrape Team"
__email__ = "team@autoscrape.com"

from .core.scraper import WebScraper
from .core.config import ScrapingConfig
from .excel.writer import ExcelWriter

__all__ = ["WebScraper", "ScrapingConfig", "ExcelWriter"]