"""Main script to run the Claude docs table scraper."""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from auto_scrape.core.config import ScrapingConfig
from auto_scrape.core.scraper import WebScraper
from auto_scrape.utils.logger import LoggerSetup


def main():
    """Run the Claude docs table scraper."""
    print("Starting Claude Code Essential Commands Table Extraction")
    print("=" * 60)
    
    try:
        # Load configuration
        config_path = Path("config/claude_docs_config.yaml")
        if not config_path.exists():
            print(f"ERROR: Configuration file not found: {config_path}")
            return 1
        
        print(f"Loading configuration from: {config_path}")
        config = ScrapingConfig.from_file(config_path)
        
        # Setup logger
        LoggerSetup.setup_logger(config.logging)
        
        # Create scraper
        scraper = WebScraper(config)
        
        print("Connecting to Claude Code documentation...")
        
        # Run scraper
        results = asyncio.run(scraper.scrape_all())
        
        # Display results
        total_items = sum(len(data) for data in results.values())
        print("Extraction completed!")
        print(f"Total commands extracted: {total_items}")
        
        if total_items > 0:
            output_file = config.excel.output_file
            print(f"Data saved to: {output_file}")
            
            # Show summary of extracted commands
            for site_name, data in results.items():
                if data:
                    print(f"\nCommands from {site_name}:")
                    for item in data[:5]:  # Show first 5 commands
                        command = item.get('command', 'N/A')
                        description = item.get('description', 'N/A')
                        print(f"  - {command}: {description[:60]}{'...' if len(description) > 60 else ''}")
                    
                    if len(data) > 5:
                        print(f"  ... and {len(data) - 5} more commands")
            
            print(f"\nSuccessfully extracted Claude Code Essential Commands table!")
            print(f"Check the Excel file: {output_file}")
            
        else:
            print("WARNING: No data was extracted. Please check:")
            print("  - Internet connection")
            print("  - Claude Code documentation accessibility")
            print("  - Log files for detailed error information")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("Check the log files for detailed error information")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)