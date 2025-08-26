"""Pytest configuration and fixtures."""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.auto_scrape.core.config import (
    ScrapingConfig, SiteConfig, BrowserConfig, ExcelConfig,
    SelectorConfig, RetryConfig, LoggingConfig
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return ScrapingConfig(
        sites=[
            SiteConfig(
                name="test_site",
                url="https://example.com",
                selectors={
                    "title": SelectorConfig(selector="h1", text=True),
                    "description": SelectorConfig(selector=".description", text=True)
                }
            )
        ],
        browser=BrowserConfig(
            headless=True,
            timeout=10000
        ),
        excel=ExcelConfig(
            output_file="test_output.xlsx",
            worksheet_name="TestData"
        ),
        retry=RetryConfig(max_attempts=2),
        logging=LoggingConfig(level="DEBUG")
    )


@pytest.fixture
def sample_site_config():
    """Create a sample site configuration for testing."""
    return SiteConfig(
        name="test_site",
        url="https://example.com",
        selectors={
            "title": SelectorConfig(selector="h1", text=True),
            "description": SelectorConfig(selector=".description", text=True),
            "price": SelectorConfig(selector=".price", text=True, transform="extract_price")
        },
        wait_for_selector=".content",
        wait_timeout=5000,
        delay_before_scraping=500
    )


@pytest.fixture
def mock_page():
    """Create a mock Playwright page."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.screenshot = AsyncMock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock()
    return page


@pytest.fixture
def mock_browser():
    """Create a mock Playwright browser."""
    browser = AsyncMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_context():
    """Create a mock Playwright browser context."""
    context = AsyncMock()
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    return context


@pytest.fixture
def sample_scraped_data():
    """Sample scraped data for testing."""
    return [
        {
            "title": "Product 1",
            "description": "Description 1",
            "price": "$19.99",
            "_scraped_at": "2024-01-01T12:00:00",
            "_source_url": "https://example.com",
            "_site_name": "test_site"
        },
        {
            "title": "Product 2", 
            "description": "Description 2",
            "price": "$29.99",
            "_scraped_at": "2024-01-01T12:01:00",
            "_source_url": "https://example.com",
            "_site_name": "test_site"
        }
    ]


@pytest.fixture
def html_content():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Main Title</h1>
        <div class="content">
            <div class="item">
                <h2 class="title">Item 1</h2>
                <p class="description">Description 1</p>
                <span class="price">$19.99</span>
            </div>
            <div class="item">
                <h2 class="title">Item 2</h2>
                <p class="description">Description 2</p>
                <span class="price">$29.99</span>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def excel_test_file(temp_dir):
    """Create a test Excel file path."""
    return temp_dir / "test_output.xlsx"