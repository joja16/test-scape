"""Data extraction utilities for web scraping."""

import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse

from loguru import logger
from playwright.async_api import Page, ElementHandle


class DataExtractor:
    """Handles data extraction from web pages using various selectors."""
    
    def __init__(self):
        """Initialize the data extractor."""
        self._extraction_methods = {
            "css": self._extract_by_css,
            "xpath": self._extract_by_xpath,
            "text": self._extract_by_text,
        }
    
    async def extract_from_page(
        self, 
        page: Page, 
        selectors: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract data from a page using configured selectors.
        
        Args:
            page: Playwright page
            selectors: Dictionary of field selectors
            
        Returns:
            List of extracted data dictionaries
        """
        try:
            # Determine extraction strategy
            extraction_data = await self._determine_extraction_strategy(page, selectors)
            
            if extraction_data["strategy"] == "single_item":
                return [await self._extract_single_item(page, selectors)]
            else:
                return await self._extract_multiple_items(page, selectors, extraction_data)
                
        except Exception as e:
            logger.error(f"Error extracting data from page: {e}")
            return []
    
    async def _determine_extraction_strategy(
        self, 
        page: Page, 
        selectors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine whether to extract single item or multiple items.
        
        Args:
            page: Playwright page
            selectors: Dictionary of field selectors
            
        Returns:
            Dictionary with extraction strategy information
        """
        # Look for repeating patterns
        container_selectors = [
            ".product", ".item", ".card", ".post", ".article", ".quote",
            "[class*='item']", "[class*='product']", "[class*='card']"
        ]
        
        best_container = None
        max_count = 0
        
        for container in container_selectors:
            try:
                elements = await page.query_selector_all(container)
                count = len(elements)
                
                if count > max_count and count > 1:
                    # Check if this container has our target selectors
                    has_target_selectors = False
                    for field_name, selector_config in selectors.items():
                        selector = selector_config.selector if hasattr(selector_config, 'selector') else selector_config
                        element_in_container = await elements[0].query_selector(selector) if elements else None
                        if element_in_container:
                            has_target_selectors = True
                            break
                    
                    if has_target_selectors:
                        max_count = count
                        best_container = container
                        
            except Exception:
                continue
        
        if best_container and max_count > 1:
            return {
                "strategy": "multiple_items",
                "container_selector": best_container,
                "item_count": max_count
            }
        else:
            return {"strategy": "single_item"}
    
    async def _extract_single_item(
        self, 
        page: Page, 
        selectors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract data for a single item from the page.
        
        Args:
            page: Playwright page
            selectors: Dictionary of field selectors
            
        Returns:
            Extracted data dictionary
        """
        extracted_item = {}
        
        for field_name, selector_config in selectors.items():
            try:
                value = await self._extract_field_value(page, field_name, selector_config)
                extracted_item[field_name] = value
            except Exception as e:
                logger.warning(f"Error extracting field '{field_name}': {e}")
                if hasattr(selector_config, 'required') and selector_config.required:
                    extracted_item[field_name] = None
                else:
                    extracted_item[field_name] = ""
        
        return extracted_item
    
    async def _extract_multiple_items(
        self, 
        page: Page, 
        selectors: Dict[str, Any], 
        extraction_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract data for multiple items from the page.
        
        Args:
            page: Playwright page
            selectors: Dictionary of field selectors
            extraction_data: Extraction strategy data
            
        Returns:
            List of extracted data dictionaries
        """
        extracted_items = []
        container_selector = extraction_data["container_selector"]
        
        try:
            # Get all container elements
            containers = await page.query_selector_all(container_selector)
            logger.debug(f"Found {len(containers)} items with selector: {container_selector}")
            
            for i, container in enumerate(containers):
                item_data = {}
                
                for field_name, selector_config in selectors.items():
                    try:
                        value = await self._extract_field_value(
                            container, field_name, selector_config, is_container=True
                        )
                        item_data[field_name] = value
                    except Exception as e:
                        logger.warning(f"Error extracting field '{field_name}' from item {i}: {e}")
                        if hasattr(selector_config, 'required') and selector_config.required:
                            item_data[field_name] = None
                        else:
                            item_data[field_name] = ""
                
                # Only add item if it has some data
                if any(value for value in item_data.values() if value):
                    extracted_items.append(item_data)
            
            logger.debug(f"Extracted {len(extracted_items)} valid items")
            
        except Exception as e:
            logger.error(f"Error extracting multiple items: {e}")
        
        return extracted_items
    
    async def _extract_field_value(
        self, 
        context: Union[Page, ElementHandle], 
        field_name: str, 
        selector_config: Any,
        is_container: bool = False
    ) -> Optional[str]:
        """Extract value for a specific field.
        
        Args:
            context: Page or element context
            field_name: Name of the field
            selector_config: Selector configuration
            is_container: Whether context is a container element
            
        Returns:
            Extracted field value
        """
        # Handle different selector config formats
        if hasattr(selector_config, 'selector'):
            selector = selector_config.selector
            attribute = getattr(selector_config, 'attribute', None)
            get_text = getattr(selector_config, 'text', True)
        else:
            selector = selector_config if isinstance(selector_config, str) else str(selector_config)
            attribute = None
            get_text = True
        
        try:
            # Handle multiple elements (like tags)
            if selector.endswith(" *") or "," in selector:
                elements = await context.query_selector_all(selector.replace(" *", ""))
                if elements:
                    values = []
                    for element in elements:
                        if attribute:
                            value = await element.get_attribute(attribute)
                        else:
                            value = await element.inner_text() if get_text else await element.inner_html()
                        if value and value.strip():
                            values.append(value.strip())
                    return ", ".join(values) if values else None
                return None
            
            # Single element extraction
            element = await context.query_selector(selector)
            if not element:
                return None
            
            # Extract value based on configuration
            if attribute:
                value = await element.get_attribute(attribute)
            elif get_text:
                value = await element.inner_text()
            else:
                value = await element.inner_html()
            
            # Clean and process the value
            if value:
                value = value.strip()
                
                # Handle URLs - convert relative to absolute
                if attribute in ["href", "src"] and value.startswith("/"):
                    if hasattr(context, 'url'):
                        base_url = context.url()
                        value = urljoin(base_url, value)
                
                return value if value else None
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting field '{field_name}' with selector '{selector}': {e}")
            return None
    
    async def extract_links(self, page: Page, selector: str = "a[href]") -> List[Dict[str, str]]:
        """Extract all links from a page.
        
        Args:
            page: Playwright page
            selector: CSS selector for links
            
        Returns:
            List of link dictionaries with 'url' and 'text' keys
        """
        links = []
        
        try:
            link_elements = await page.query_selector_all(selector)
            
            for link_element in link_elements:
                href = await link_element.get_attribute("href")
                text = await link_element.inner_text()
                
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        href = urljoin(page.url, href)
                    
                    links.append({
                        "url": href.strip(),
                        "text": text.strip() if text else ""
                    })
            
            logger.debug(f"Extracted {len(links)} links")
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        
        return links
    
    async def extract_images(self, page: Page, selector: str = "img[src]") -> List[Dict[str, str]]:
        """Extract all images from a page.
        
        Args:
            page: Playwright page
            selector: CSS selector for images
            
        Returns:
            List of image dictionaries with 'src', 'alt', and 'title' keys
        """
        images = []
        
        try:
            image_elements = await page.query_selector_all(selector)
            
            for img_element in image_elements:
                src = await img_element.get_attribute("src")
                alt = await img_element.get_attribute("alt")
                title = await img_element.get_attribute("title")
                
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith("/"):
                        src = urljoin(page.url, src)
                    
                    images.append({
                        "src": src.strip(),
                        "alt": alt.strip() if alt else "",
                        "title": title.strip() if title else ""
                    })
            
            logger.debug(f"Extracted {len(images)} images")
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return images
    
    async def extract_table_data(self, page: Page, table_selector: str = "table") -> List[Dict[str, Any]]:
        """Extract data from HTML tables.
        
        Args:
            page: Playwright page
            table_selector: CSS selector for table
            
        Returns:
            List of row dictionaries with column headers as keys
        """
        table_data = []
        
        try:
            table = await page.query_selector(table_selector)
            if not table:
                logger.warning(f"No table found with selector: {table_selector}")
                return []
            
            # Extract headers
            header_elements = await table.query_selector_all("thead th, tr:first-child td, tr:first-child th")
            headers = []
            for header in header_elements:
                text = await header.inner_text()
                headers.append(text.strip() if text else f"Column_{len(headers) + 1}")
            
            if not headers:
                logger.warning("No table headers found")
                return []
            
            # Extract rows
            row_elements = await table.query_selector_all("tbody tr, tr")
            
            for row_element in row_elements[1:]:  # Skip header row
                cell_elements = await row_element.query_selector_all("td, th")
                
                if len(cell_elements) == len(headers):
                    row_data = {}
                    for i, cell in enumerate(cell_elements):
                        text = await cell.inner_text()
                        row_data[headers[i]] = text.strip() if text else ""
                    
                    table_data.append(row_data)
            
            logger.debug(f"Extracted {len(table_data)} rows from table")
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
        
        return table_data
    
    async def _extract_by_css(self, page: Page, selector: str) -> List[ElementHandle]:
        """Extract elements using CSS selector.
        
        Args:
            page: Playwright page
            selector: CSS selector
            
        Returns:
            List of element handles
        """
        return await page.query_selector_all(selector)
    
    async def _extract_by_xpath(self, page: Page, selector: str) -> List[ElementHandle]:
        """Extract elements using XPath selector.
        
        Args:
            page: Playwright page
            selector: XPath selector
            
        Returns:
            List of element handles
        """
        return await page.query_selector_all(f"xpath={selector}")
    
    async def _extract_by_text(self, page: Page, text: str) -> List[ElementHandle]:
        """Extract elements containing specific text.
        
        Args:
            page: Playwright page
            text: Text to search for
            
        Returns:
            List of element handles
        """
        return await page.query_selector_all(f"text={text}")