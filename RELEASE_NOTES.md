# Auto Scrape v1.0.0 Release

## 🎉 Initial Release

We're excited to announce the first official release of Auto Scrape, a powerful web scraping automation tool for Windows 11!

## ✨ Features

- **🚀 High-Performance Web Scraping**: Built with Playwright for fast, reliable scraping
- **🛡️ Anti-Detection Technology**: Uses stealth mode to avoid bot detection
- **📊 Excel Integration**: Direct export to Excel with formatting support
- **📋 Table Extraction**: Intelligent table detection and extraction from web pages
- **⚙️ Configuration-Driven**: YAML-based configuration for easy customization
- **🔄 Retry Mechanisms**: Built-in error handling and automatic retries
- **💻 Windows 11 Optimized**: Specially designed for Windows 11 compatibility

## 📦 What's Included

### Standalone Executable
- **AutoScrape.exe** (395 MB) - Complete standalone application
- No Python installation required
- All dependencies bundled
- Works on any Windows 11 machine

### Deployment Tools
- **QUICK_DEPLOY.bat** - One-click installation script
- **build.ps1** - Advanced build script with Inno Setup support
- **deploy.ps1** - Enterprise deployment automation

## 🚀 Quick Start

1. Download `AutoScrape.exe` from the releases page
2. Place in your desired folder
3. Double-click to run
4. Configure your scraping tasks in `config/scraping_config.yaml`
5. Start scraping!

## 📋 System Requirements

- Windows 11 (64-bit)
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Internet connection

## ⚠️ Known Issues

- Windows Defender may flag the unsigned executable on first run
- First launch may take longer due to browser component installation

## 🔧 For Developers

Clone the repository and build from source:

```bash
git clone https://github.com/joja16/test-scape.git
cd test-scape
python quick_build.py
```

## 📝 Configuration Example

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
```

## 🙏 Acknowledgments

Built with:
- Playwright for browser automation
- PyInstaller for executable creation
- Pandas for data processing
- OpenPyXL for Excel handling

## 📄 License

MIT License - See LICENSE.txt for details

---

**Full Changelog**: First release

**Download**: [AutoScrape.exe](https://github.com/joja16/test-scape/releases/download/v1.0.0/AutoScrape.exe)
