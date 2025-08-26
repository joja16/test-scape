"""Browser management with Playwright and anti-detection features."""

import asyncio
import random
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError
)
from loguru import logger

from .config import BrowserConfig, SiteConfig


class BrowserManager:
    """Manages browser instances with anti-detection features."""
    
    def __init__(self, config: BrowserConfig):
        """Initialize browser manager.
        
        Args:
            config: Browser configuration
        """
        self.config = config
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]
    
    async def start(self) -> None:
        """Start the browser."""
        try:
            logger.info("Starting browser manager")
            self._playwright = await async_playwright().start()
            
            # Browser launch options
            launch_options = {
                "headless": self.config.headless,
                "args": self._get_browser_args(),
            }
            
            # Add proxy if configured
            if self.config.proxy_server:
                proxy_config = {"server": self.config.proxy_server}
                if self.config.proxy_username and self.config.proxy_password:
                    proxy_config.update({
                        "username": self.config.proxy_username,
                        "password": self.config.proxy_password
                    })
                launch_options["proxy"] = proxy_config
            
            # Launch browser based on type
            if self.config.type.value == "chromium":
                self._browser = await self._playwright.chromium.launch(**launch_options)
            elif self.config.type.value == "firefox":
                self._browser = await self._playwright.firefox.launch(**launch_options)
            else:
                self._browser = await self._playwright.webkit.launch(**launch_options)
            
            logger.info(f"Browser started successfully: {self.config.type.value}")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the browser and cleanup resources."""
        try:
            logger.info("Stopping browser manager")
            
            # Close all contexts
            for context_id, context in self._contexts.items():
                try:
                    await context.close()
                    logger.debug(f"Closed context: {context_id}")
                except Exception as e:
                    logger.warning(f"Error closing context {context_id}: {e}")
            
            self._contexts.clear()
            
            # Close browser
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            # Stop playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            logger.info("Browser manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping browser: {e}")
    
    @asynccontextmanager
    async def get_page(self, site_config: SiteConfig):
        """Get a page for scraping with anti-detection setup.
        
        Args:
            site_config: Site configuration
            
        Yields:
            Configured page ready for scraping
        """
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        context_id = site_config.name
        page = None
        
        try:
            # Create or reuse context
            if context_id not in self._contexts:
                self._contexts[context_id] = await self._create_context(site_config)
            
            context = self._contexts[context_id]
            page = await context.new_page()
            
            # Apply anti-detection measures
            await self._apply_anti_detection(page, site_config)
            
            logger.debug(f"Created page for site: {site_config.name}")
            yield page
            
        except Exception as e:
            logger.error(f"Error creating page for {site_config.name}: {e}")
            raise
        finally:
            if page:
                try:
                    await page.close()
                    logger.debug(f"Closed page for site: {site_config.name}")
                except Exception as e:
                    logger.warning(f"Error closing page for {site_config.name}: {e}")
    
    async def _create_context(self, site_config: SiteConfig) -> BrowserContext:
        """Create a browser context with anti-detection settings.
        
        Args:
            site_config: Site configuration
            
        Returns:
            Configured browser context
        """
        # Context options
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height
            },
            "user_agent": self._get_user_agent(),
            "locale": self.config.locale,
            "timezone_id": self.config.timezone,
            "extra_http_headers": self._get_default_headers(),
        }
        
        # Add site-specific headers
        if site_config.headers:
            context_options["extra_http_headers"].update(site_config.headers)
        
        # Create context
        context = await self._browser.new_context(**context_options)
        
        # Add authentication if configured
        if site_config.auth:
            await self._setup_authentication(context, site_config.auth)
        
        logger.debug(f"Created context for site: {site_config.name}")
        return context
    
    async def _apply_anti_detection(self, page: Page, site_config: SiteConfig) -> None:
        """Apply anti-detection measures to the page.
        
        Args:
            page: Playwright page
            site_config: Site configuration
        """
        try:
            # Stealth scripts to avoid detection
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
                
                // Mock chrome runtime
                window.chrome = {
                    runtime: {},
                };
            """)
            
            # Set random mouse movements
            await page.mouse.move(
                random.randint(0, self.config.viewport_width),
                random.randint(0, self.config.viewport_height)
            )
            
            logger.debug(f"Applied anti-detection measures for: {site_config.name}")
            
        except Exception as e:
            logger.warning(f"Error applying anti-detection for {site_config.name}: {e}")
    
    async def _setup_authentication(self, context: BrowserContext, auth_config: Dict[str, str]) -> None:
        """Setup authentication for the context.
        
        Args:
            context: Browser context
            auth_config: Authentication configuration
        """
        if auth_config.get("type") == "basic":
            await context.set_extra_http_headers({
                "Authorization": f"Basic {auth_config.get('credentials')}"
            })
        elif auth_config.get("type") == "bearer":
            await context.set_extra_http_headers({
                "Authorization": f"Bearer {auth_config.get('token')}"
            })
        
        logger.debug("Authentication setup completed")
    
    def _get_browser_args(self) -> List[str]:
        """Get browser launch arguments for anti-detection.
        
        Returns:
            List of browser arguments
        """
        args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-extensions",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--start-maximized",
        ]
        
        # Add Windows-specific args
        args.extend([
            "--disable-background-mode",
            "--disable-background-networking",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-hangout-services-extension",
        ])
        
        if not self.config.images_enabled:
            args.append("--blink-settings=imagesEnabled=false")
        
        return args
    
    def _get_user_agent(self) -> str:
        """Get a user agent string.
        
        Returns:
            User agent string
        """
        if self.config.user_agent:
            return self.config.user_agent
        
        # Return random user agent for better anonymity
        return random.choice(self._user_agents)
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
    
    async def wait_for_load(self, page: Page, site_config: SiteConfig) -> None:
        """Wait for page to load based on site configuration.
        
        Args:
            page: Playwright page
            site_config: Site configuration
        """
        try:
            # Wait for network to be idle
            await page.wait_for_load_state("networkidle", timeout=site_config.wait_timeout)
            
            # Wait for specific selector if configured
            if site_config.wait_for_selector:
                await page.wait_for_selector(
                    site_config.wait_for_selector,
                    timeout=site_config.wait_timeout
                )
            
            # Additional delay before scraping
            if site_config.delay_before_scraping > 0:
                await asyncio.sleep(site_config.delay_before_scraping / 1000)
            
            logger.debug(f"Page loaded successfully for: {site_config.name}")
            
        except PlaywrightTimeoutError as e:
            logger.warning(f"Timeout waiting for page load: {site_config.name}")
            raise
        except Exception as e:
            logger.error(f"Error waiting for page load: {e}")
            raise
    
    async def navigate_to_url(self, page: Page, url: str, timeout: Optional[int] = None) -> None:
        """Navigate to URL with random delays.
        
        Args:
            page: Playwright page
            url: URL to navigate to
            timeout: Navigation timeout
        """
        try:
            # Random delay before navigation
            delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            
            # Navigate to URL
            await page.goto(
                url,
                timeout=timeout or self.config.timeout,
                wait_until="networkidle"
            )
            
            # Random delay after navigation
            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)
            
            logger.debug(f"Navigated to: {url}")
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise