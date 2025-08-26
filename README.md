# Auto Scrape

A Python web scraping automation program using Playwright to extract information from websites and populate Excel files with high accuracy. Optimized for Chrome on Windows 11.

## 📥 Download

### Windows Executable (Recommended)
Download the latest Windows executable from the [Releases page](https://github.com/joja16/test-scape/releases).

**Latest Release:** [AutoScrape.exe v1.0.0](https://github.com/joja16/test-scape/releases/latest/download/AutoScrape.exe) (395 MB)

#### Installation Steps:
1. Download `AutoScrape.exe` from the releases page
2. Place the executable in your desired folder
3. Double-click to run (may require admin privileges)
4. On first run, the application will install necessary browser components

**Note:** Windows Defender may flag the executable on first run. This is normal for unsigned executables. Click "More info" → "Run anyway" to proceed.

## Features

- 🚀 **High Performance**: Async web scraping with Playwright
- 🛡️ **Anti-Detection**: Stealth browsing with undetected-playwright
- 📊 **Excel Integration**: Flexible Excel file generation and manipulation
- ⚙️ **Configuration-Driven**: YAML-based configuration management
- 🔄 **Reliability**: Built-in retry mechanisms and error handling
- 🧪 **Well-Tested**: Comprehensive test suite with high coverage

## Quick Start

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Basic Usage

```python
from auto_scrape import WebScraper, ScrapingConfig

# Load configuration
config = ScrapingConfig.from_file("config/scraping_config.yaml")

# Initialize scraper
scraper = WebScraper(config)

# Run scraping
await scraper.scrape_all()
```

## Configuration

Create a configuration file in `config/scraping_config.yaml`:

```yaml
browser:
  headless: false
  timeout: 30000
  
sites:
  - name: "example_site"
    url: "https://example.com"
    selectors:
      title: "h1"
      description: ".description"
    
excel:
  output_file: "output/scraped_data.xlsx"
  template: "templates/excel/default_template.xlsx"
```

## Project Structure

```
auto-scrape/
├── src/auto_scrape/           # Source code
│   ├── core/                  # Core scraping logic
│   ├── scrapers/              # Site-specific scrapers
│   ├── excel/                 # Excel handling
│   └── utils/                 # Utilities
├── config/                    # Configuration files
├── templates/excel/           # Excel templates
├── tests/                     # Test suite
├── logs/                      # Log files
└── output/                    # Generated files
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black src/
isort src/
flake8 src/
mypy src/
```

## License

MIT License