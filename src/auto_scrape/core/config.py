"""Configuration management for the auto scraper."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class SelectorConfig(BaseModel):
    """Configuration for element selectors."""
    selector: str = Field(..., description="CSS or XPath selector")
    attribute: Optional[str] = Field(None, description="Attribute to extract")
    text: bool = Field(True, description="Extract text content")
    required: bool = Field(True, description="Whether this field is required")
    transform: Optional[str] = Field(None, description="Transformation function")


class SiteConfig(BaseModel):
    """Configuration for a single site to scrape."""
    name: str = Field(..., description="Site identifier")
    url: str = Field(..., description="Base URL")
    enabled: bool = Field(True, description="Whether to scrape this site")
    
    # Navigation settings
    wait_for_selector: Optional[str] = Field(None, description="Selector to wait for")
    wait_timeout: int = Field(10000, description="Wait timeout in milliseconds")
    delay_before_scraping: int = Field(1000, description="Delay before scraping in ms")
    
    # Selectors for data extraction
    selectors: Dict[str, SelectorConfig] = Field(default_factory=dict)
    
    # Custom scraper specification
    custom_scraper: Optional[str] = Field(None, description="Name of custom scraper to use")
    table_index: Optional[int] = Field(None, description="Specific table index to extract (0-based, null for all tables)")
    
    # Authentication if needed
    auth: Optional[Dict[str, str]] = Field(None, description="Authentication config")
    
    # Custom headers
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class BrowserConfig(BaseModel):
    """Browser configuration."""
    type: BrowserType = Field(BrowserType.CHROMIUM, description="Browser type")
    headless: bool = Field(True, description="Run in headless mode")
    timeout: int = Field(30000, description="Default timeout in milliseconds")
    viewport_width: int = Field(1920, description="Viewport width")
    viewport_height: int = Field(1080, description="Viewport height")
    
    # Anti-detection settings
    user_agent: Optional[str] = Field(None, description="Custom user agent")
    locale: str = Field("en-US", description="Browser locale")
    timezone: str = Field("America/New_York", description="Browser timezone")
    
    # Performance settings
    javascript_enabled: bool = Field(True, description="Enable JavaScript")
    images_enabled: bool = Field(False, description="Load images")
    
    # Proxy settings
    proxy_server: Optional[str] = Field(None, description="Proxy server URL")
    proxy_username: Optional[str] = Field(None, description="Proxy username")
    proxy_password: Optional[str] = Field(None, description="Proxy password")


class ExcelConfig(BaseModel):
    """Excel file configuration."""
    output_file: str = Field(..., description="Output Excel file path")
    template_file: Optional[str] = Field(None, description="Template Excel file")
    worksheet_name: str = Field("Data", description="Worksheet name")
    
    # Formatting options
    auto_fit_columns: bool = Field(True, description="Auto-fit column widths")
    freeze_header_row: bool = Field(True, description="Freeze header row")
    add_timestamp: bool = Field(True, description="Add timestamp column")
    
    # Column mappings
    column_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Map data fields to column names"
    )


class RetryConfig(BaseModel):
    """Retry configuration for failed operations."""
    max_attempts: int = Field(3, description="Maximum retry attempts")
    delay: float = Field(1.0, description="Initial delay between retries in seconds")
    backoff_factor: float = Field(2.0, description="Backoff multiplier")
    max_delay: float = Field(60.0, description="Maximum delay between retries")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(LogLevel.INFO, description="Log level")
    file_path: str = Field("logs/scraper.log", description="Log file path")
    max_file_size: str = Field("10 MB", description="Maximum log file size")
    backup_count: int = Field(5, description="Number of backup log files")
    format: str = Field(
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log format"
    )


class ScrapingConfig(BaseSettings):
    """Main configuration for the scraper."""
    
    # Site configurations
    sites: List[SiteConfig] = Field(default_factory=list)
    
    # Browser settings
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    
    # Excel settings
    excel: ExcelConfig = Field(default_factory=lambda: ExcelConfig(output_file="output/scraped_data.xlsx"))
    
    # Retry settings
    retry: RetryConfig = Field(default_factory=RetryConfig)
    
    # Logging settings
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Performance settings
    concurrent_sites: int = Field(3, description="Number of sites to scrape concurrently")
    request_delay: float = Field(1.0, description="Delay between requests in seconds")
    
    # Output settings
    output_directory: str = Field("output", description="Output directory")
    backup_data: bool = Field(True, description="Create backup of existing data")
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "SCRAPER_",
        "case_sensitive": False
    }
    
    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values):
        """Validate the complete configuration."""
        if isinstance(values, dict):
            sites = values.get('sites', [])
            if not sites:
                raise ValueError("At least one site configuration is required")
            
            excel_config = values.get('excel')
            if excel_config:
                if isinstance(excel_config, dict):
                    output_file = excel_config.get('output_file')
                else:
                    output_file = getattr(excel_config, 'output_file', None)
                
                if output_file:
                    output_dir = Path(output_file).parent
                    output_dir.mkdir(parents=True, exist_ok=True)
        
        return values
    
    @classmethod
    def from_file(cls, config_path: str) -> "ScrapingConfig":
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        
        # Convert selectors to SelectorConfig objects
        if 'sites' in config_data:
            for site in config_data['sites']:
                if 'selectors' in site:
                    selectors = {}
                    for field_name, selector_data in site['selectors'].items():
                        if isinstance(selector_data, str):
                            selectors[field_name] = SelectorConfig(selector=selector_data)
                        else:
                            selectors[field_name] = SelectorConfig(**selector_data)
                    site['selectors'] = selectors
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and handle special types
        config_dict = self.model_dump(mode='json')
        
        # Convert SelectorConfig objects to dicts
        if 'sites' in config_dict:
            for site in config_dict['sites']:
                if 'selectors' in site:
                    selectors = {}
                    for field_name, selector_config in site['selectors'].items():
                        if isinstance(selector_config, dict):
                            selectors[field_name] = selector_config
                        else:
                            selectors[field_name] = selector_config.model_dump()
                    site['selectors'] = selectors
        
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(config_dict, file, default_flow_style=False, indent=2)
    
    def get_enabled_sites(self) -> List[SiteConfig]:
        """Get list of enabled sites."""
        return [site for site in self.sites if site.enabled]