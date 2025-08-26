"""
Claude Documentation Table Scraper

Custom scraper specifically designed to extract the "Essential commands" table
from the Claude Code quickstart documentation.
"""

import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import Page
from loguru import logger
from datetime import datetime

from ..core.data_extractor import DataExtractor
from ..utils.exceptions import ScrapingError, ValidationError


class ClaudeDocsTableScraper:
    """Custom scraper for Claude documentation tables."""
    
    def __init__(self):
        """Initialize the Claude docs table scraper."""
        self.data_extractor = DataExtractor()
    
    async def extract_essential_commands_table(
        self, 
        page: Page, 
        site_config
    ) -> List[Dict[str, Any]]:
        """
        Extract the Essential Commands table from Claude docs.
        
        Args:
            page: Playwright page instance
            site_config: Site configuration
            
        Returns:
            List of command data dictionaries
            
        Raises:
            ScrapingError: If table extraction fails
            ValidationError: If extracted data is invalid
        """
        try:
            logger.info("Starting Claude docs Essential Commands table extraction")
            
            # Wait for page content to load
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Look for the Essential Commands section
            essential_section = await self._find_essential_commands_section(page)
            if not essential_section:
                raise ScrapingError("Could not find Essential Commands section")
            
            # Extract table data
            table_data = await self._extract_table_from_section(page, essential_section)
            
            if not table_data:
                raise ValidationError("No table data extracted")
            
            logger.info(f"Successfully extracted {len(table_data)} commands from table")
            return table_data
            
        except Exception as e:
            logger.error(f"Error extracting Claude docs table: {e}")
            raise ScrapingError(f"Table extraction failed: {e}")
    
    async def _find_essential_commands_section(self, page: Page) -> Optional[str]:
        """
        Find the Essential Commands section in the documentation.
        
        Args:
            page: Playwright page instance
            
        Returns:
            Selector for the Essential Commands section or None
        """
        try:
            # Simplified approach: look for any table with command-like content
            tables = await page.query_selector_all("table")
            logger.debug(f"Found {len(tables)} tables on page")
            
            for i, table in enumerate(tables):
                # Check if table contains command-like content
                table_text = await table.text_content()
                if table_text:
                    table_text_lower = table_text.lower()
                    # Look for Claude Code specific commands
                    command_keywords = ['claude', '/help', '/clear', 'exit', 'interactive mode']
                    if any(keyword in table_text_lower for keyword in command_keywords):
                        logger.info(f"Found table with command-like content at index {i}")
                        logger.debug(f"Table content preview: {table_text[:200]}...")
                        return f"table:nth-of-type({i + 1})"
            
            # Fallback: use the first table if it exists
            if tables:
                logger.warning("No command-specific table found, using first table as fallback")
                return "table"
            
            logger.error("No tables found on the page")
            return None
            
        except Exception as e:
            logger.error(f"Error finding Essential Commands section: {e}")
            return None
    
    async def _extract_table_from_section(
        self, 
        page: Page, 
        section_selector: str
    ) -> List[Dict[str, Any]]:
        """
        Extract table data from the identified section.
        
        Args:
            page: Playwright page instance
            section_selector: CSS selector for the section
            
        Returns:
            List of extracted table row data
        """
        try:
            # Find the table near the section
            table_selectors = [
                f"{section_selector} + table",  # Table immediately after section
                f"{section_selector} ~ table",   # Table as sibling after section
                "table",                         # Any table on page (fallback)
                "[role='table']"                 # ARIA table role
            ]
            
            table_element = None
            for selector in table_selectors:
                table_element = await page.query_selector(selector)
                if table_element:
                    logger.debug(f"Found table with selector: {selector}")
                    break
            
            if not table_element:
                raise ScrapingError("No table found in section")
            
            # Extract table headers
            headers = await self._extract_table_headers(page, table_element)
            logger.debug(f"Table headers: {headers}")
            
            # Extract table rows
            rows_data = await self._extract_table_rows(page, table_element, headers)
            
            return rows_data
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            raise
    
    async def _extract_table_headers(
        self, 
        page: Page, 
        table_element
    ) -> List[str]:
        """
        Extract table headers.
        
        Args:
            page: Playwright page instance
            table_element: Table element
            
        Returns:
            List of header names
        """
        try:
            # Try different header extraction methods
            headers = []
            
            # Method 1: Look for thead th elements
            header_elements = await table_element.query_selector_all("thead th")
            if header_elements:
                logger.debug("Found headers in thead")
                for header_elem in header_elements:
                    header_text = await header_elem.text_content()
                    if header_text:
                        headers.append(header_text.strip())
            
            # Method 2: Look for th elements anywhere in the table
            if not headers:
                header_elements = await table_element.query_selector_all("th")
                if header_elements:
                    logger.debug("Found headers as th elements")
                    for header_elem in header_elements:
                        header_text = await header_elem.text_content()
                        if header_text:
                            headers.append(header_text.strip())
            
            # Method 3: First row cells as headers
            if not headers:
                first_row = await table_element.query_selector("tr:first-child")
                if first_row:
                    header_elements = await first_row.query_selector_all("td")
                    if header_elements:
                        logger.debug("Using first row td elements as headers")
                        for header_elem in header_elements:
                            header_text = await header_elem.text_content()
                            if header_text:
                                headers.append(header_text.strip())
            
            # Default headers based on known structure
            if not headers:
                headers = ["Command", "Description", "Example"]
                logger.warning("No headers found, using default headers")
            else:
                logger.info(f"Extracted headers: {headers}")
            
            return headers
            
        except Exception as e:
            logger.error(f"Error extracting table headers: {e}")
            return ["Command", "Description", "Example"]
    
    async def _extract_table_rows(
        self, 
        page: Page, 
        table_element, 
        headers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract table row data.
        
        Args:
            page: Playwright page instance
            table_element: Table element
            headers: List of column headers
            
        Returns:
            List of row data dictionaries
        """
        try:
            # Try to get tbody rows first (more specific)
            row_elements = await table_element.query_selector_all("tbody tr")
            
            # If no tbody found, get all rows and skip the first header row
            if not row_elements:
                all_rows = await table_element.query_selector_all("tr")
                if len(all_rows) > 1:
                    row_elements = all_rows[1:]  # Skip header row
                else:
                    row_elements = []
            
            logger.debug(f"Found {len(row_elements)} table rows")
            rows_data = []
            
            for row_elem in row_elements:
                # Get all cells in the row
                cell_elements = await row_elem.query_selector_all("td")
                if not cell_elements:
                    logger.debug("Skipping row with no td elements")
                    continue
                
                logger.debug(f"Processing row with {len(cell_elements)} cells")
                
                # Extract cell text content
                row_data = {}
                for i, cell_elem in enumerate(cell_elements):
                    cell_text = await cell_elem.text_content()
                    if cell_text:
                        cell_text = cell_text.strip()
                        
                        # Map to standard field names based on column index
                        if i == 0:  # First column is the command
                            row_data["command"] = cell_text
                        elif i == 1:  # Second column is description
                            row_data["description"] = cell_text
                        elif i == 2:  # Third column is example
                            row_data["example"] = cell_text
                        
                        # Also store with header-based column name if available
                        if i < len(headers):
                            column_name = headers[i].lower().replace(" ", "_").replace("what_it_does", "description")
                            row_data[column_name] = cell_text
                        
                        logger.debug(f"Cell {i}: '{cell_text[:50]}{'...' if len(cell_text) > 50 else ''}'")
                
                # Add metadata
                row_data["_scraped_at"] = datetime.now().isoformat()
                row_data["_source_url"] = page.url
                row_data["_site_name"] = "claude_docs_essential_commands"
                row_data["_table_type"] = "essential_commands"
                
                # Only add rows with actual command data
                if row_data.get("command"):
                    rows_data.append(row_data)
                    logger.debug(f"Added command: {row_data['command']}")
                else:
                    logger.debug("Skipping row without command data")
            
            logger.info(f"Extracted {len(rows_data)} valid table rows")
            return rows_data
            
        except Exception as e:
            logger.error(f"Error extracting table rows: {e}")
            raise
    
    async def validate_extracted_data(
        self, 
        data: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate the extracted table data.
        
        Args:
            data: Extracted table data
            
        Returns:
            True if data is valid, False otherwise
            
        Raises:
            ValidationError: If data validation fails
        """
        try:
            if not data:
                raise ValidationError("No data to validate")
            
            # Check for required fields
            required_fields = ["command"]
            for i, row in enumerate(data):
                for field in required_fields:
                    if field not in row or not row[field].strip():
                        raise ValidationError(
                            f"Row {i+1} missing required field: {field}"
                        )
                
                # Validate command format (should not be empty or just whitespace)
                if not row["command"].strip():
                    raise ValidationError(f"Row {i+1} has empty command")
            
            logger.info(f"Data validation passed for {len(data)} rows")
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            raise