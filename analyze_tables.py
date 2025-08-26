"""
Table Analyzer

Analyze tables on a webpage and show their structure.
Usage: python analyze_tables.py [URL]
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from auto_scrape.core.browser import BrowserManager
from auto_scrape.core.config import BrowserConfig
from auto_scrape.scrapers.generic_table import GenericTableScraper
from auto_scrape.utils.logger import LoggerSetup
from loguru import logger


async def analyze_page_tables(url: str):
    """Analyze all tables on a webpage."""
    
    # Setup browser
    browser_config = BrowserConfig(
        type="chromium",
        headless=False,
        timeout=30000,
        viewport_width=1920,
        viewport_height=1080
    )
    
    browser_manager = BrowserManager(browser_config)
    scraper = GenericTableScraper()
    
    try:
        # Start browser
        await browser_manager.start()
        
        # Create a dummy site config for navigation
        class DummySiteConfig:
            def __init__(self, url):
                self.url = url
                self.name = "table_analysis"
                self.wait_for_selector = "table, .table, [role='table']"
                self.wait_timeout = 10000
                self.delay_before_scraping = 1000
                self.headers = {}
                self.auth = None
        
        site_config = DummySiteConfig(url)
        
        async with browser_manager.get_page(site_config) as page:
            print(f"Analyzing tables on: {url}")
            print("=" * 60)
            
            # Navigate to page
            await browser_manager.navigate_to_url(page, url)
            await browser_manager.wait_for_load(page, site_config)
            
            # Get table summary
            summary = await scraper.get_table_summary(page)
            
            if summary["total_tables"] == 0:
                print("No tables found on this page.")
                if "error" in summary:
                    print(f"Error: {summary['error']}")
            else:
                print(f"Found {summary['total_tables']} table(s):")
                print()
                
                for table_info in summary["tables"]:
                    if "error" in table_info:
                        print(f"Table {table_info['index']}: Error analyzing - {table_info['error']}")
                        continue
                    
                    print(f"Table {table_info['index']}:")
                    print(f"  Columns: {table_info['columns']}")
                    print(f"  Data Rows: {table_info['rows']}")
                    print(f"  Headers: {table_info['headers']}")
                    
                    if table_info.get('preview_available'):
                        print(f"  Status: Ready for extraction")
                    else:
                        print(f"  Status: May be empty or header-only")
                    
                    print()
                
                print("Usage Instructions:")
                print("-" * 40)
                print("To extract all tables:")
                print(f"  python run_table_scraper.py \"{url}\"")
                print()
                print("To extract a specific table (by index):")
                for table_info in summary["tables"]:
                    if not table_info.get("error"):
                        print(f"  python run_table_scraper.py \"{url}\" {table_info['index']}")
                print()
                
    except Exception as e:
        logger.error(f"Error analyzing page: {e}")
        print(f"Error analyzing page: {e}")
        
    finally:
        await browser_manager.stop()


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python analyze_tables.py <URL>")
        print("Example: python analyze_tables.py https://example.com/page.html")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Setup basic logging
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    
    try:
        asyncio.run(analyze_page_tables(url))
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"Failed to analyze page: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()