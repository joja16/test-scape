"""Integration tests for the web scraper."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path

from src.auto_scrape.core.scraper import WebScraper
from src.auto_scrape.core.config import ScrapingConfig
from src.auto_scrape.core.browser import BrowserManager


class TestScraperIntegration:
    """Integration tests for the WebScraper class."""
    
    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self, sample_config, temp_dir):
        """Test the complete scraping workflow."""
        # Update config to use temp directory
        sample_config.excel.output_file = str(temp_dir / "integration_test.xlsx")
        
        # Mock browser and page interactions
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup mock playwright
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # Mock page navigation and data extraction
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.wait_for_selector = AsyncMock()
            mock_page.url = "https://example.com"
            
            # Mock element extraction
            mock_element = AsyncMock()
            mock_element.inner_text = AsyncMock(return_value="Test Title")
            mock_page.query_selector_all = AsyncMock(return_value=[mock_element])
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            
            # Create and run scraper
            scraper = WebScraper(sample_config)
            
            try:
                scraped_data = await scraper.scrape_all()
                
                # Verify scraping results
                assert isinstance(scraped_data, dict)
                assert "test_site" in scraped_data
                
                # Verify Excel file was created
                excel_file = Path(sample_config.excel.output_file)
                assert excel_file.exists()
                
            finally:
                # Cleanup is handled by scraper's finally block
                pass
    
    @pytest.mark.asyncio
    async def test_multiple_sites_scraping(self, temp_dir):
        """Test scraping multiple sites concurrently."""
        from src.auto_scrape.core.config import SiteConfig, SelectorConfig
        
        # Create config with multiple sites
        config = ScrapingConfig(
            sites=[
                SiteConfig(
                    name="site1",
                    url="https://example1.com",
                    selectors={"title": SelectorConfig(selector="h1")}
                ),
                SiteConfig(
                    name="site2", 
                    url="https://example2.com",
                    selectors={"title": SelectorConfig(selector="h1")}
                )
            ],
            excel={"output_file": str(temp_dir / "multi_site_test.xlsx")},
            concurrent_sites=2
        )
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup mocks similar to above test
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.url = "https://example.com"
            
            mock_element = AsyncMock()
            mock_element.inner_text = AsyncMock(return_value="Test Title")
            mock_page.query_selector_all = AsyncMock(return_value=[mock_element])
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            
            scraper = WebScraper(config)
            scraped_data = await scraper.scrape_all()
            
            # Should have data for both sites
            assert len(scraped_data) == 2
            assert "site1" in scraped_data
            assert "site2" in scraped_data
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, sample_config, temp_dir):
        """Test error handling and recovery mechanisms."""
        sample_config.excel.output_file = str(temp_dir / "error_test.xlsx")
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup mock that throws error on first call
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # First call fails, subsequent calls succeed
            call_count = 0
            def mock_goto(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Network error")
                return AsyncMock()
            
            mock_page.goto = AsyncMock(side_effect=mock_goto)
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.url = "https://example.com"
            
            scraper = WebScraper(sample_config)
            
            # Should handle the error and potentially retry
            scraped_data = await scraper.scrape_all()
            
            # Even with errors, should return a result structure
            assert isinstance(scraped_data, dict)
    
    @pytest.mark.asyncio
    async def test_data_validation_and_transformation(self, sample_config, temp_dir):
        """Test data validation and transformation during scraping."""
        sample_config.excel.output_file = str(temp_dir / "validation_test.xlsx")
        
        # Add transformation to config
        sample_config.sites[0].selectors["price"] = {
            "selector": ".price",
            "text": True,
            "transform": "extract_price"
        }
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup mocks
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.url = "https://example.com"
            
            # Mock elements with different data types
            mock_title = AsyncMock()
            mock_title.inner_text = AsyncMock(return_value="Test Product")
            
            mock_price = AsyncMock()
            mock_price.inner_text = AsyncMock(return_value="$19.99")
            
            def mock_query_selector(selector):
                if selector == "h1":
                    return mock_title
                elif selector == ".price":
                    return mock_price
                return AsyncMock()
            
            mock_page.query_selector = AsyncMock(side_effect=mock_query_selector)
            mock_page.query_selector_all = AsyncMock(return_value=[])
            
            scraper = WebScraper(sample_config)
            scraped_data = await scraper.scrape_all()
            
            # Verify data was scraped and potentially transformed
            assert "test_site" in scraped_data
    
    @pytest.mark.asyncio
    async def test_excel_output_formatting(self, sample_config, temp_dir):
        """Test Excel output formatting and structure."""
        import pandas as pd
        
        sample_config.excel.output_file = str(temp_dir / "formatting_test.xlsx")
        sample_config.excel.add_timestamp = True
        sample_config.excel.auto_fit_columns = True
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup basic mocks
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.url = "https://example.com"
            
            # Mock successful data extraction
            mock_element = AsyncMock()
            mock_element.inner_text = AsyncMock(return_value="Test Data")
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_page.query_selector_all = AsyncMock(return_value=[])
            
            scraper = WebScraper(sample_config)
            await scraper.scrape_all()
            
            # Verify Excel file formatting
            excel_file = Path(sample_config.excel.output_file)
            if excel_file.exists():
                df = pd.read_excel(excel_file)
                
                # Check if timestamp column was added
                if sample_config.excel.add_timestamp:
                    assert "Timestamp" in df.columns
    
    @pytest.mark.asyncio
    async def test_browser_configuration_effects(self, temp_dir):
        """Test different browser configurations."""
        from src.auto_scrape.core.config import BrowserConfig, BrowserType
        
        config = ScrapingConfig(
            sites=[{
                "name": "test_site",
                "url": "https://example.com",
                "selectors": {"title": {"selector": "h1"}}
            }],
            browser=BrowserConfig(
                type=BrowserType.CHROMIUM,
                headless=True,
                timeout=15000,
                viewport_width=1366,
                viewport_height=768
            ),
            excel={"output_file": str(temp_dir / "browser_test.xlsx")}
        )
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            # Verify browser launch options
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            scraper = WebScraper(config)
            
            # Start browser manager to test configuration
            await scraper.browser_manager.start()
            
            # Verify chromium was launched with correct settings
            mock_pw_instance.chromium.launch.assert_called_once()
            launch_args = mock_pw_instance.chromium.launch.call_args[1]
            
            assert launch_args["headless"] == True
            
            await scraper.browser_manager.stop()