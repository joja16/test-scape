"""
Generic Table Scraper Runner

Extract tables from any website and save to Excel.
Usage: python run_table_scraper.py [URL] [table_index]
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from auto_scrape.core.config import ScrapingConfig
from auto_scrape.core.scraper import WebScraper
from auto_scrape.utils.logger import LoggerSetup


def update_config_for_url(config_path: Path, target_url: str, table_index: Optional[int] = None, output_file: Optional[str] = None):
    """Update the configuration file with the target URL and options."""
    import yaml
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # Update the URL
    config_data['sites'][0]['url'] = target_url
    config_data['sites'][0]['name'] = f"table_extraction_{target_url.replace('://', '_').replace('/', '_')[:50]}"
    
    # Set table index if specified
    if table_index is not None:
        config_data['sites'][0]['table_index'] = table_index
    
    # Update output file if specified
    if output_file:
        config_data['excel']['output_file'] = output_file
    
    # Write back to config
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


def main():
    """Run the generic table scraper."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_table_scraper.py <URL> [table_index] [output_file]")
        print("Examples:")
        print("  python run_table_scraper.py https://example.com/page.html")
        print("  python run_table_scraper.py https://example.com/page.html 0")
        print("  python run_table_scraper.py https://example.com/page.html 1 my_table.xlsx")
        sys.exit(1)
    
    target_url = sys.argv[1]
    table_index = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("Generic Table Extraction Tool")
    print("=" * 50)
    print(f"Target URL: {target_url}")
    if table_index is not None:
        print(f"Table Index: {table_index} (0-based)")
    else:
        print("Table Index: All tables")
    
    try:
        # Load and update configuration
        config_path = Path("config/generic_table_config.yaml")
        if not config_path.exists():
            print(f"ERROR: Configuration file not found: {config_path}")
            return 1
        
        print(f"Updating configuration...")
        update_config_for_url(config_path, target_url, table_index, output_file)
        
        # Load updated configuration
        config = ScrapingConfig.from_file(config_path)
        
        # Setup logger
        LoggerSetup.setup_logger(config.logging)
        
        print("Connecting to website and analyzing tables...")
        
        # Create and run scraper
        scraper = WebScraper(config)
        results = asyncio.run(scraper.scrape_all())
        
        # Display results
        total_items = sum(len(data) for data in results.values())
        print(f"Extraction completed!")
        print(f"Total rows extracted: {total_items}")
        
        if total_items > 0:
            output_file = config.excel.output_file
            print(f"Data saved to: {output_file}")
            
            # Show summary of extracted data
            for site_name, data in results.items():
                if data:
                    print(f"\nExtracted data from {site_name}:")
                    
                    # Group by table index if multiple tables
                    tables = {}
                    for item in data:
                        table_idx = item.get('_table_index', 0)
                        if table_idx not in tables:
                            tables[table_idx] = []
                        tables[table_idx].append(item)
                    
                    for table_idx, table_data in tables.items():
                        print(f"  Table {table_idx}: {len(table_data)} rows")
                        
                        # Show column names from first row
                        if table_data:
                            sample_row = table_data[0]
                            columns = [k for k in sample_row.keys() if not k.startswith('_')]
                            print(f"    Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                            
                            # Show first few rows preview
                            print("    Sample data:")
                            for i, row in enumerate(table_data[:3]):
                                row_preview = []
                                for col in columns[:3]:
                                    value = str(row.get(col, ''))[:30]
                                    row_preview.append(value + "..." if len(str(row.get(col, ''))) > 30 else value)
                                print(f"      Row {i+1}: {' | '.join(row_preview)}")
                            
                            if len(table_data) > 3:
                                print(f"      ... and {len(table_data) - 3} more rows")
            
            print(f"\nTable extraction completed successfully!")
            print(f"Excel file: {output_file}")
            
        else:
            print("WARNING: No table data was extracted. This could be due to:")
            print("  - No tables found on the page")
            print("  - Tables are dynamically loaded by JavaScript")
            print("  - Website blocking automated access")
            print("  - Incorrect table index specified")
            print("  - Network connectivity issues")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("Check the log files for detailed error information")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)