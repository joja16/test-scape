"""Custom exceptions for the auto scraper."""


class AutoScrapeError(Exception):
    """Base exception for auto scraper errors."""
    pass


class ConfigurationError(AutoScrapeError):
    """Raised when there's an error in configuration."""
    pass


class BrowserError(AutoScrapeError):
    """Raised when there's an error with browser operations."""
    pass


class ScrapingError(AutoScrapeError):
    """Raised when there's an error during scraping."""
    pass


class DataExtractionError(ScrapingError):
    """Raised when data extraction fails."""
    pass


class SelectorError(DataExtractionError):
    """Raised when selectors fail to find elements."""
    pass


class ValidationError(AutoScrapeError):
    """Raised when data validation fails."""
    pass


class ExcelError(AutoScrapeError):
    """Raised when there's an error with Excel operations."""
    pass


class NetworkError(AutoScrapeError):
    """Raised when there's a network-related error."""
    pass


class RetryableError(AutoScrapeError):
    """Base class for errors that should trigger a retry."""
    pass


class TemporaryError(RetryableError):
    """Raised for temporary errors that should be retried."""
    pass


class RateLimitError(RetryableError):
    """Raised when rate limiting is encountered."""
    pass


class TimeoutError(RetryableError):
    """Raised when operations timeout."""
    pass