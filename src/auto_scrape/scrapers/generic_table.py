"""
Generic Table Scraper

A flexible scraper that can extract tables from any website.
Extracts exact headers and row content without HTML code.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import Page
from loguru import logger
from datetime import datetime

from ..core.data_extractor import DataExtractor
from ..utils.exceptions import ScrapingError, ValidationError


class GenericTableScraper:
    """Generic scraper for extracting tables from any website."""
    
    def __init__(self):
        """Initialize the generic table scraper."""
        self.data_extractor = DataExtractor()
    
    async def extract_all_tables(
        self, 
        page: Page, 
        site_config,
        table_index: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all tables or a specific table from the page.
        
        Args:
            page: Playwright page instance
            site_config: Site configuration
            table_index: Optional index of specific table to extract (0-based)
            
        Returns:
            List of extracted table data
            
        Raises:
            ScrapingError: If table extraction fails
            ValidationError: If extracted data is invalid
        """
        try:
            logger.info("Starting generic table extraction")
            
            # Wait for page content to load
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Find all tables on the page
            tables = await self._find_all_tables(page)
            if not tables:
                raise ScrapingError("No tables found on the page")
            
            logger.info(f"Found {len(tables)} tables on the page")
            
            # Extract specific table or all tables
            if table_index is not None:
                if table_index >= len(tables):
                    raise ScrapingError(f"Table index {table_index} out of range. Found {len(tables)} tables.")
                tables_to_extract = [tables[table_index]]
                logger.info(f"Extracting table at index {table_index}")
            else:
                tables_to_extract = tables
                logger.info("Extracting all tables")
            
            all_table_data = []
            
            for i, table_element in enumerate(tables_to_extract):
                try:
                    table_data = await self._extract_single_table(
                        page, table_element, i if table_index is None else table_index
                    )
                    all_table_data.extend(table_data)
                except Exception as e:
                    logger.warning(f"Failed to extract table {i}: {e}")
                    continue
            
            if not all_table_data:
                raise ValidationError("No table data extracted")
            
            logger.info(f"Successfully extracted {len(all_table_data)} total rows from tables")
            return all_table_data
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            raise ScrapingError(f"Table extraction failed: {e}")
    
    async def _find_all_tables(self, page: Page) -> List:
        """
        Find all table elements on the page.
        
        Args:
            page: Playwright page instance
            
        Returns:
            List of table elements
        """
        try:
            # Find all table elements using different selectors
            table_selectors = [
                "table",
                "[role='table']",
                ".table",
                "[data-table]",
                ".data-table"
            ]
            
            all_tables = []
            for selector in table_selectors:
                tables = await page.query_selector_all(selector)
                for table in tables:
                    if table not in all_tables:
                        # Verify it's actually a table-like structure
                        if await self._is_valid_table(table):
                            all_tables.append(table)
            
            logger.debug(f"Found {len(all_tables)} valid tables")
            return all_tables
            
        except Exception as e:
            logger.error(f"Error finding tables: {e}")
            return []
    
    async def _is_valid_table(self, table_element) -> bool:
        """
        Check if an element is a valid table structure.
        
        Args:
            table_element: Element to check
            
        Returns:
            True if valid table, False otherwise
        """
        try:
            # Check for table rows
            rows = await table_element.query_selector_all("tr, [role='row'], .table-row")
            if len(rows) < 2:  # At least header + 1 data row
                return False
            
            # Check for cells in first row
            first_row = rows[0]
            cells = await first_row.query_selector_all("td, th, [role='cell'], [role='columnheader'], .table-cell")
            return len(cells) >= 2  # At least 2 columns
            
        except Exception:
            return False
    
    async def _extract_single_table(
        self, 
        page: Page, 
        table_element, 
        table_index: int
    ) -> List[Dict[str, Any]]:
        """
        Extract data from a single table.
        
        Args:
            page: Playwright page instance
            table_element: Table element to extract
            table_index: Index of the table on the page
            
        Returns:
            List of extracted row data
        """
        try:
            # Extract headers
            headers = await self._extract_table_headers(table_element, table_index)
            logger.info(f"Table {table_index} headers: {headers}")
            
            # Extract rows
            rows_data = await self._extract_table_rows(table_element, headers, table_index)
            
            # Add table metadata to each row
            for row in rows_data:
                row["_table_index"] = table_index
                row["_scraped_at"] = datetime.now().isoformat()
                row["_source_url"] = page.url
            
            logger.info(f"Extracted {len(rows_data)} rows from table {table_index}")
            return rows_data
            
        except Exception as e:
            logger.error(f"Error extracting table {table_index}: {e}")
            raise
    
    async def _extract_table_headers(self, table_element, table_index: int) -> List[str]:
        """
        Extract headers from table using multiple strategies.
        
        Args:
            table_element: Table element
            table_index: Table index for logging
            
        Returns:
            List of header names
        """
        try:
            headers = []
            
            # Strategy 1: thead th elements
            header_elements = await table_element.query_selector_all("thead th, thead [role='columnheader']")
            if header_elements:
                logger.debug(f"Table {table_index}: Found headers in thead")
                for elem in header_elements:
                    text = await elem.text_content()
                    headers.append(text.strip() if text else "")
            
            # Strategy 2: First row th elements
            if not headers:
                header_elements = await table_element.query_selector_all("tr:first-child th, [role='row']:first-child [role='columnheader']")
                if header_elements:
                    logger.debug(f"Table {table_index}: Found headers in first row th")
                    for elem in header_elements:
                        text = await elem.text_content()
                        headers.append(text.strip() if text else "")
            
            # Strategy 3: First row td elements (if no th found)
            if not headers:
                first_row = await table_element.query_selector("tr:first-child, [role='row']:first-child")
                if first_row:
                    header_elements = await first_row.query_selector_all("td, [role='cell']")
                    if header_elements:
                        logger.debug(f"Table {table_index}: Using first row td as headers")
                        for elem in header_elements:
                            text = await elem.text_content()
                            headers.append(text.strip() if text else "")
            
            # Generate default headers if none found
            if not headers:
                # Count columns by checking first data row
                first_row = await table_element.query_selector("tr, [role='row']")
                if first_row:
                    cells = await first_row.query_selector_all("td, th, [role='cell'], [role='columnheader']")
                    headers = [f"Column_{i+1}" for i in range(len(cells))]
                    logger.warning(f"Table {table_index}: Generated default headers")
                else:
                    headers = ["Column_1", "Column_2"]
                    logger.warning(f"Table {table_index}: Using fallback headers")
            
            # Clean headers - remove empty strings and duplicates
            cleaned_headers = []
            for i, header in enumerate(headers):
                if not header.strip():
                    header = f"Column_{i+1}"
                # Handle duplicates by adding suffix
                original_header = header
                counter = 1
                while header in cleaned_headers:
                    header = f"{original_header}_{counter}"
                    counter += 1
                cleaned_headers.append(header)
            
            return cleaned_headers
            
        except Exception as e:
            logger.error(f"Error extracting headers from table {table_index}: {e}")
            return ["Column_1", "Column_2"]
    
    async def _extract_table_rows(
        self, 
        table_element, 
        headers: List[str], 
        table_index: int
    ) -> List[Dict[str, Any]]:
        """
        Extract data rows from table.
        
        Args:
            table_element: Table element
            headers: List of column headers
            table_index: Table index for logging
            
        Returns:
            List of row data dictionaries
        """
        try:
            # Find data rows (skip header row)
            all_rows = await table_element.query_selector_all("tr, [role='row']")
            
            # Determine which rows are data rows
            data_rows = []
            header_row_found = False
            
            for row in all_rows:
                # Check if this row contains headers
                th_cells = await row.query_selector_all("th, [role='columnheader']")
                td_cells = await row.query_selector_all("td, [role='cell']")
                
                # Skip rows that are primarily headers
                if th_cells and not td_cells:
                    header_row_found = True
                    continue
                
                # If we have mixed th/td or only td, treat as data row
                if td_cells or (th_cells and td_cells):
                    # Skip first row if no clear header row was found
                    if not header_row_found and not data_rows:
                        header_row_found = True
                        continue
                    data_rows.append(row)
            
            logger.debug(f"Table {table_index}: Found {len(data_rows)} data rows")
            
            rows_data = []
            for row_idx, row in enumerate(data_rows):
                try:
                    row_data = await self._extract_row_data(row, headers, table_index, row_idx)
                    if row_data and any(value.strip() for value in row_data.values() if isinstance(value, str)):
                        rows_data.append(row_data)
                except Exception as e:
                    logger.warning(f"Table {table_index}, Row {row_idx}: Failed to extract - {e}")
                    continue
            
            return rows_data
            
        except Exception as e:
            logger.error(f"Error extracting rows from table {table_index}: {e}")
            return []
    
    async def _extract_row_data(
        self, 
        row_element, 
        headers: List[str], 
        table_index: int, 
        row_index: int
    ) -> Dict[str, Any]:
        """
        Extract data from a single table row.
        
        Args:
            row_element: Row element
            headers: Column headers
            table_index: Table index
            row_index: Row index
            
        Returns:
            Row data dictionary
        """
        try:
            # Get all cells in the row
            cells = await row_element.query_selector_all("td, th, [role='cell'], [role='columnheader']")
            
            row_data = {}
            for i, cell in enumerate(cells):
                # Get cell text content
                cell_text = await cell.text_content()
                cell_value = cell_text.strip() if cell_text else ""
                
                # Map to header name
                if i < len(headers):
                    column_name = headers[i]
                else:
                    column_name = f"Column_{i+1}"
                
                row_data[column_name] = cell_value
                
                # Also create numeric column reference
                row_data[f"col_{i+1}"] = cell_value
            
            return row_data
            
        except Exception as e:
            logger.error(f"Error extracting row data: {e}")
            return {}
    
    async def get_table_summary(self, page: Page) -> Dict[str, Any]:
        """
        Get a summary of all tables on the page.
        
        Args:
            page: Playwright page instance
            
        Returns:
            Dictionary with table summary information
        """
        try:
            tables = await self._find_all_tables(page)
            summary = {
                "total_tables": len(tables),
                "tables": []
            }
            
            for i, table in enumerate(tables):
                try:
                    headers = await self._extract_table_headers(table, i)
                    rows = await table.query_selector_all("tr, [role='row']")
                    
                    table_info = {
                        "index": i,
                        "headers": headers,
                        "columns": len(headers),
                        "rows": len(rows) - 1,  # Subtract header row
                        "preview_available": len(rows) > 1
                    }
                    summary["tables"].append(table_info)
                    
                except Exception as e:
                    logger.warning(f"Could not analyze table {i}: {e}")
                    summary["tables"].append({
                        "index": i,
                        "error": str(e)
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting table summary: {e}")
            return {"total_tables": 0, "tables": [], "error": str(e)}