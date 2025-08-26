"""Main entry point for the auto scraper application."""

import asyncio
import sys
from pathlib import Path

from src.auto_scrape.core.config import ScrapingConfig
from src.auto_scrape.core.scraper import WebScraper
from src.auto_scrape.utils.logger import LoggerSetup
from src.auto_scrape.utils.exceptions import AutoScrapeError


async def main():
    """Main function to run the scraper."""
    try:
        # Load configuration
        config_path = Path("config/scraping_config.yaml")
        if not config_path.exists():
            print(f"Configuration file not found: {config_path}")
            print("Please create a configuration file based on the example.")
            return 1
        
        print("Loading configuration...")
        config = ScrapingConfig.from_file(str(config_path))
        
        # Setup logging
        LoggerSetup.setup_logger(config.logging)
        
        print("Starting web scraper...")
        
        # Initialize and run scraper
        scraper = WebScraper(config)
        scraped_data = await scraper.scrape_all()
        
        # Print summary
        total_items = sum(len(data) for data in scraped_data.values())
        print(f"\n✓ Scraping completed successfully!")
        print(f"✓ Total items scraped: {total_items}")
        print(f"✓ Output file: {config.excel.output_file}")
        
        return 0
        
    except AutoScrapeError as e:
        print(f"\n✗ Scraping failed: {e}")
        return 1
    except KeyboardInterrupt:
        print(f"\n⚠ Scraping interrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)