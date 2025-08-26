"""Unit tests for configuration module."""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.auto_scrape.core.config import (
    ScrapingConfig, SiteConfig, BrowserConfig, ExcelConfig,
    SelectorConfig, BrowserType, LogLevel
)


class TestSelectorConfig:
    """Test SelectorConfig class."""
    
    def test_selector_config_creation(self):
        """Test creating a selector config."""
        selector = SelectorConfig(
            selector=".title",
            text=True,
            required=True
        )
        
        assert selector.selector == ".title"
        assert selector.text is True
        assert selector.required is True
        assert selector.attribute is None
    
    def test_selector_config_with_attribute(self):
        """Test selector config with attribute extraction."""
        selector = SelectorConfig(
            selector="a",
            attribute="href",
            text=False
        )
        
        assert selector.selector == "a"
        assert selector.attribute == "href"
        assert selector.text is False


class TestSiteConfig:
    """Test SiteConfig class."""
    
    def test_site_config_creation(self):
        """Test creating a site config."""
        site = SiteConfig(
            name="test_site",
            url="https://example.com",
            selectors={
                "title": SelectorConfig(selector="h1")
            }
        )
        
        assert site.name == "test_site"
        assert site.url == "https://example.com"
        assert site.enabled is True
        assert "title" in site.selectors
    
    def test_url_validation(self):
        """Test URL validation."""
        with pytest.raises(ValueError, match="URL must start with http"):
            SiteConfig(
                name="invalid",
                url="invalid-url",
                selectors={}
            )
    
    def test_valid_urls(self):
        """Test valid URL formats."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://example.com/path",
            "http://subdomain.example.com"
        ]
        
        for url in valid_urls:
            site = SiteConfig(
                name="test",
                url=url,
                selectors={}
            )
            assert site.url == url


class TestBrowserConfig:
    """Test BrowserConfig class."""
    
    def test_browser_config_defaults(self):
        """Test browser config with default values."""
        browser = BrowserConfig()
        
        assert browser.type == BrowserType.CHROMIUM
        assert browser.headless is True
        assert browser.timeout == 30000
        assert browser.viewport_width == 1920
        assert browser.viewport_height == 1080
    
    def test_browser_config_custom(self):
        """Test browser config with custom values."""
        browser = BrowserConfig(
            type=BrowserType.FIREFOX,
            headless=False,
            timeout=60000
        )
        
        assert browser.type == BrowserType.FIREFOX
        assert browser.headless is False
        assert browser.timeout == 60000


class TestExcelConfig:
    """Test ExcelConfig class."""
    
    def test_excel_config_creation(self):
        """Test creating Excel config."""
        excel = ExcelConfig(
            output_file="output.xlsx",
            worksheet_name="Data"
        )
        
        assert excel.output_file == "output.xlsx"
        assert excel.worksheet_name == "Data"
        assert excel.auto_fit_columns is True
        assert excel.add_timestamp is True


class TestScrapingConfig:
    """Test ScrapingConfig class."""
    
    def test_scraping_config_creation(self, sample_config):
        """Test creating scraping config."""
        assert len(sample_config.sites) == 1
        assert sample_config.sites[0].name == "test_site"
        assert sample_config.browser.headless is True
        assert sample_config.excel.output_file == "test_output.xlsx"
    
    def test_get_enabled_sites(self, sample_config):
        """Test getting enabled sites."""
        enabled_sites = sample_config.get_enabled_sites()
        assert len(enabled_sites) == 1
        
        # Disable a site
        sample_config.sites[0].enabled = False
        enabled_sites = sample_config.get_enabled_sites()
        assert len(enabled_sites) == 0
    
    def test_config_validation_empty_sites(self):
        """Test validation fails with empty sites."""
        with pytest.raises(ValueError, match="At least one site configuration is required"):
            ScrapingConfig(sites=[])
    
    def test_from_file_yaml(self, temp_dir):
        """Test loading config from YAML file."""
        config_data = {
            "sites": [
                {
                    "name": "test_site",
                    "url": "https://example.com",
                    "selectors": {
                        "title": {"selector": "h1", "text": True}
                    }
                }
            ],
            "browser": {
                "headless": True,
                "timeout": 15000
            },
            "excel": {
                "output_file": "test.xlsx"
            }
        }
        
        config_file = temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)
        
        config = ScrapingConfig.from_file(str(config_file))
        
        assert len(config.sites) == 1
        assert config.sites[0].name == "test_site"
        assert config.browser.timeout == 15000
        assert config.excel.output_file == "test.xlsx"
    
    def test_from_file_not_exists(self):
        """Test loading config from non-existent file."""
        with pytest.raises(FileNotFoundError):
            ScrapingConfig.from_file("non_existent.yaml")
    
    def test_save_to_file(self, sample_config, temp_dir):
        """Test saving config to YAML file."""
        config_file = temp_dir / "saved_config.yaml"
        
        sample_config.save_to_file(str(config_file))
        
        assert config_file.exists()
        
        # Load and verify
        with open(config_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["sites"][0]["name"] == "test_site"
        assert saved_data["browser"]["headless"] is True