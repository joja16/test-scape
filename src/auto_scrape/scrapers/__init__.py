"""
Custom scrapers for specific website patterns.

This module contains specialized scrapers for websites that require
custom extraction logic beyond the standard selector-based approach.
"""

from .claude_docs_table import ClaudeDocsTableScraper
from .generic_table import GenericTableScraper

__all__ = ["ClaudeDocsTableScraper", "GenericTableScraper"]