"""Test script for Claude docs table scraper."""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from auto_scrape.core.config import ScrapingConfig
from auto_scrape.core.scraper import WebScraper
from auto_scrape.utils.logger import LoggerSetup
from loguru import logger


async def main():
    """Test the Claude docs table scraper."""
    # Setup logging
    logger.info("Starting Claude docs scraper test")
    
    try:
        # Load configuration
        config_path = Path("config/claude_docs_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return
        
        # Create scraper
        config = ScrapingConfig.from_file(config_path)
        scraper = WebScraper(config)
        
        # Run scraper
        logger.info("Starting scraping process")
        results = await scraper.scrape_all()
        
        # Print results
        total_items = sum(len(data) for data in results.values())
        logger.info(f"Scraping completed. Total items: {total_items}")
        
        for site_name, data in results.items():
            logger.info(f"Site: {site_name}, Items: {len(data)}")
            if data:
                # Show first few items
                for i, item in enumerate(data[:3]):
                    logger.info(f"  Item {i+1}: {item.get('command', 'N/A')} - {item.get('description', 'N/A')[:50]}...")
        
        if total_items > 0:
            logger.info("✅ Scraper test completed successfully!")
            print("✅ Test passed! Check the output Excel file for extracted data.")
        else:
            logger.warning("⚠️  No data extracted. Check configuration and selectors.")
            print("⚠️  No data extracted. Check the logs for details.")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())