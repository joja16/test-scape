"""Main web scraper implementation."""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import ScrapingConfig, SiteConfig, SelectorConfig
from .browser import BrowserManager
from .data_extractor import DataExtractor
from ..utils.transformers import DataTransformer
from ..excel.writer import ExcelWriter
from ..scrapers import ClaudeDocsTableScraper
from ..scrapers.generic_table import GenericTableScraper


class WebScraper:
    """Main web scraper orchestrating the scraping process."""
    
    def __init__(self, config: ScrapingConfig):
        """Initialize the web scraper.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.browser_manager = BrowserManager(config.browser)
        self.data_extractor = DataExtractor()
        self.data_transformer = DataTransformer()
        self.excel_writer = ExcelWriter(config.excel)
        self.claude_docs_scraper = ClaudeDocsTableScraper()
        self.generic_table_scraper = GenericTableScraper()
        self._scraped_data: Dict[str, List[Dict[str, Any]]] = {}
        self._start_time: Optional[datetime] = None
    
    async def scrape_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape all enabled sites and return collected data.
        
        Returns:
            Dictionary with site names as keys and scraped data as values
        """
        self._start_time = datetime.now()
        logger.info("Starting web scraping process")
        
        try:
            # Start browser
            await self.browser_manager.start()
            
            # Get enabled sites
            enabled_sites = self.config.get_enabled_sites()
            if not enabled_sites:
                logger.warning("No enabled sites found in configuration")
                return {}
            
            logger.info(f"Found {len(enabled_sites)} enabled sites to scrape")
            
            # Scrape sites concurrently
            semaphore = asyncio.Semaphore(self.config.concurrent_sites)
            tasks = [
                self._scrape_site_with_semaphore(semaphore, site)
                for site in enabled_sites
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                site = enabled_sites[i]
                if isinstance(result, Exception):
                    logger.error(f"Failed to scrape site {site.name}: {result}")
                    self._scraped_data[site.name] = []
                else:
                    self._scraped_data[site.name] = result
                    logger.info(f"Successfully scraped {len(result)} items from {site.name}")
            
            # Save to Excel
            if self._scraped_data:
                await self._save_to_excel()
            
            # Log summary
            self._log_scraping_summary()
            
            return self._scraped_data
            
        except Exception as e:
            logger.error(f"Error during scraping process: {e}")
            raise
        finally:
            await self.browser_manager.stop()
    
    async def _scrape_site_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        site_config: SiteConfig
    ) -> List[Dict[str, Any]]:
        """Scrape a single site with semaphore control.
        
        Args:
            semaphore: Semaphore for concurrency control
            site_config: Site configuration
            
        Returns:
            List of scraped data items
        """
        async with semaphore:
            return await self._scrape_single_site(site_config)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((PlaywrightTimeoutError, ConnectionError))
    )
    async def _scrape_single_site(self, site_config: SiteConfig) -> List[Dict[str, Any]]:
        """Scrape a single site with retry logic.
        
        Args:
            site_config: Site configuration
            
        Returns:
            List of scraped data items
        """
        logger.info(f"Starting to scrape site: {site_config.name}")
        scraped_items = []
        
        async with self.browser_manager.get_page(site_config) as page:
            try:
                # Navigate to the site
                await self.browser_manager.navigate_to_url(page, site_config.url)
                
                # Wait for page to load
                await self.browser_manager.wait_for_load(page, site_config)
                
                # Extract data from the page
                page_data = await self._extract_page_data(page, site_config)
                scraped_items.extend(page_data)
                
                # Handle pagination if needed
                scraped_items.extend(
                    await self._handle_pagination(page, site_config)
                )
                
                logger.info(f"Completed scraping site: {site_config.name} ({len(scraped_items)} items)")
                
            except Exception as e:
                logger.error(f"Error scraping site {site_config.name}: {e}")
                raise
            
            # Delay between sites
            if self.config.request_delay > 0:
                await asyncio.sleep(self.config.request_delay)
        
        return scraped_items
    
    async def _extract_page_data(
        self, 
        page: Page, 
        site_config: SiteConfig
    ) -> List[Dict[str, Any]]:
        """Extract data from a single page.
        
        Args:
            page: Playwright page
            site_config: Site configuration
            
        Returns:
            List of extracted data items
        """
        try:
            # Take screenshot for debugging if needed
            if not self.config.browser.headless:
                screenshot_path = f"logs/screenshot_{site_config.name}_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.debug(f"Screenshot saved: {screenshot_path}")
            
            # Check if site uses a custom scraper
            custom_scraper = getattr(site_config, 'custom_scraper', None)
            if custom_scraper:
                logger.info(f"Using custom scraper: {custom_scraper}")
                return await self._extract_with_custom_scraper(page, site_config, custom_scraper)
            
            # Extract data using standard selectors
            extracted_data = await self.data_extractor.extract_from_page(
                page, site_config.selectors
            )
            
            # Transform data if needed
            for item in extracted_data:
                for field_name, field_value in item.items():
                    if field_name in site_config.selectors:
                        selector_config = site_config.selectors[field_name]
                        if selector_config.transform:
                            item[field_name] = self.data_transformer.transform(
                                field_value, selector_config.transform
                            )
                
                # Add metadata
                item["_scraped_at"] = datetime.now().isoformat()
                item["_source_url"] = site_config.url
                item["_site_name"] = site_config.name
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from page: {e}")
            return []

    async def _extract_with_custom_scraper(
        self,
        page: Page,
        site_config: SiteConfig,
        custom_scraper: str
    ) -> List[Dict[str, Any]]:
        """Extract data using a custom scraper.
        
        Args:
            page: Playwright page
            site_config: Site configuration
            custom_scraper: Name of the custom scraper to use
            
        Returns:
            List of extracted data items
            
        Raises:
            ValueError: If custom scraper is not supported
        """
        try:
            if custom_scraper == "claude_docs_table":
                return await self.claude_docs_scraper.extract_essential_commands_table(
                    page, site_config
                )
            elif custom_scraper == "generic_table":
                # Get table index from site config if specified
                table_index = getattr(site_config, 'table_index', None)
                return await self.generic_table_scraper.extract_all_tables(
                    page, site_config, table_index
                )
            else:
                raise ValueError(f"Unsupported custom scraper: {custom_scraper}")
                
        except Exception as e:
            logger.error(f"Error with custom scraper {custom_scraper}: {e}")
            # Fallback to standard extraction
            logger.warning("Falling back to standard selector-based extraction")
            return await self.data_extractor.extract_from_page(
                page, site_config.selectors
            )
    
    async def _handle_pagination(
        self, 
        page: Page, 
        site_config: SiteConfig
    ) -> List[Dict[str, Any]]:
        """Handle pagination to scrape multiple pages.
        
        Args:
            page: Playwright page
            site_config: Site configuration
            
        Returns:
            List of data from paginated pages
        """
        all_data = []
        page_count = 1
        max_pages = 10  # Safety limit
        
        try:
            while page_count < max_pages:
                # Look for "Next" button or pagination link
                next_button = await page.query_selector('a[href*="page"]:has-text("Next"), .next, .pagination-next')
                
                if not next_button:
                    # Try common pagination patterns
                    next_button = await page.query_selector(
                        'a[href*="page=' + str(page_count + 1) + '"], '
                        'a[href*="p=' + str(page_count + 1) + '"]'
                    )
                
                if not next_button or not await next_button.is_visible():
                    logger.debug(f"No more pages found for {site_config.name}")
                    break
                
                # Click next page
                await next_button.click()
                await self.browser_manager.wait_for_load(page, site_config)
                
                # Extract data from new page
                page_data = await self._extract_page_data(page, site_config)
                all_data.extend(page_data)
                
                page_count += 1
                logger.debug(f"Scraped page {page_count} of {site_config.name}")
                
                # Add delay between pages
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.warning(f"Error during pagination for {site_config.name}: {e}")
        
        logger.info(f"Scraped {page_count} pages from {site_config.name}")
        return all_data
    
    async def _save_to_excel(self) -> None:
        """Save scraped data to Excel file."""
        try:
            logger.info("Saving data to Excel file")
            
            # Prepare data for Excel
            all_data = []
            for site_name, site_data in self._scraped_data.items():
                for item in site_data:
                    # Apply column mappings
                    mapped_item = {}
                    for field_name, field_value in item.items():
                        column_name = self.config.excel.column_mappings.get(
                            field_name, field_name
                        )
                        mapped_item[column_name] = field_value
                    all_data.append(mapped_item)
            
            if all_data:
                await self.excel_writer.write_data(all_data)
                logger.info(f"Data saved successfully to {self.config.excel.output_file}")
            else:
                logger.warning("No data to save to Excel")
                
        except Exception as e:
            logger.error(f"Error saving data to Excel: {e}")
            raise
    
    def _log_scraping_summary(self) -> None:
        """Log a summary of the scraping process."""
        if not self._start_time:
            return
        
        end_time = datetime.now()
        duration = end_time - self._start_time
        
        total_items = sum(len(data) for data in self._scraped_data.values())
        sites_scraped = len([data for data in self._scraped_data.values() if data])
        
        logger.info("="*50)
        logger.info("SCRAPING SUMMARY")
        logger.info("="*50)
        logger.info(f"Duration: {duration}")
        logger.info(f"Sites processed: {len(self._scraped_data)}")
        logger.info(f"Sites successfully scraped: {sites_scraped}")
        logger.info(f"Total items scraped: {total_items}")
        
        for site_name, site_data in self._scraped_data.items():
            logger.info(f"  {site_name}: {len(site_data)} items")
        
        logger.info(f"Data saved to: {self.config.excel.output_file}")
        logger.info("="*50)