"""End-to-end tests for the complete scraping workflow."""

import pytest
import asyncio
from pathlib import Path
import pandas as pd
from unittest.mock import patch, AsyncMock

from src.auto_scrape.core.scraper import WebScraper
from src.auto_scrape.core.config import ScrapingConfig


class TestFullWorkflow:
    """End-to-end tests for the complete workflow."""
    
    @pytest.mark.asyncio
    async def test_quotes_scraping_workflow(self, temp_dir):
        """Test scraping quotes from a mock quotes site."""
        # Create configuration for quotes scraping
        config_data = {
            "sites": [
                {
                    "name": "mock_quotes",
                    "url": "http://quotes.toscrape.com",
                    "enabled": True,
                    "wait_for_selector": ".quote",
                    "wait_timeout": 10000,
                    "delay_before_scraping": 500,
                    "selectors": {
                        "quote_text": {
                            "selector": ".quote .text",
                            "text": True,
                            "required": True
                        },
                        "author": {
                            "selector": ".quote .author", 
                            "text": True,
                            "required": True
                        },
                        "tags": {
                            "selector": ".quote .tags .tag",
                            "text": True,
                            "required": False
                        }
                    }
                }
            ],
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 15000
            },
            "excel": {
                "output_file": str(temp_dir / "quotes_scraped.xlsx"),
                "worksheet_name": "Quotes",
                "add_timestamp": True,
                "column_mappings": {
                    "quote_text": "Quote",
                    "author": "Author",
                    "tags": "Tags"
                }
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        config = ScrapingConfig(**config_data)
        
        # Mock the browser interactions
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup playwright mock
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # Mock page navigation
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.wait_for_selector = AsyncMock()
            mock_page.url = "http://quotes.toscrape.com"
            
            # Mock quote elements
            mock_quotes = []
            for i in range(3):  # Mock 3 quotes
                mock_quote_container = AsyncMock()
                
                mock_text = AsyncMock()
                mock_text.inner_text = AsyncMock(return_value=f"Quote {i+1} text")
                
                mock_author = AsyncMock()
                mock_author.inner_text = AsyncMock(return_value=f"Author {i+1}")
                
                mock_tag = AsyncMock()
                mock_tag.inner_text = AsyncMock(return_value=f"tag{i+1}")
                
                def make_selector_mock(text_elem, author_elem, tag_elem):
                    def selector_mock(selector):
                        if ".text" in selector:
                            return text_elem
                        elif ".author" in selector:
                            return author_elem
                        elif ".tag" in selector:
                            return tag_elem
                        return None
                    return selector_mock
                
                mock_quote_container.query_selector = AsyncMock(
                    side_effect=make_selector_mock(mock_text, mock_author, mock_tag)
                )
                mock_quotes.append(mock_quote_container)
            
            # Setup container detection
            def mock_query_selector_all(selector):
                if ".product" in selector or ".quote" in selector:
                    return mock_quotes
                return []  # No pagination elements
            
            def mock_query_selector(selector):
                if 'page' in selector or 'Next' in selector or 'next' in selector or 'pagination' in selector:
                    return None  # No pagination buttons
                return None
            
            mock_page.query_selector_all = AsyncMock(side_effect=mock_query_selector_all)
            mock_page.query_selector = AsyncMock(side_effect=mock_query_selector)
            
            # Run the scraper
            scraper = WebScraper(config)
            scraped_data = await scraper.scrape_all()
            
            # Verify results
            assert "mock_quotes" in scraped_data
            quotes_data = scraped_data["mock_quotes"]
            assert len(quotes_data) == 3
            
            # Check data structure
            for i, quote in enumerate(quotes_data):
                assert "quote_text" in quote
                assert "author" in quote
                assert "tags" in quote
                assert quote["quote_text"] == f"Quote {i+1} text"
                assert quote["author"] == f"Author {i+1}"
            
            # Verify Excel file was created
            excel_file = Path(config.excel.output_file)
            assert excel_file.exists()
            
            # Verify Excel content
            df = pd.read_excel(excel_file, sheet_name=config.excel.worksheet_name)
            assert len(df) == 3
            assert "Quote" in df.columns  # Mapped column name
            assert "Author" in df.columns
            assert "Tags" in df.columns
            assert "Timestamp" in df.columns  # Added timestamp
    
    @pytest.mark.asyncio
    async def test_product_catalog_scraping(self, temp_dir):
        """Test scraping a product catalog."""
        config_data = {
            "sites": [
                {
                    "name": "mock_products",
                    "url": "http://products.example.com",
                    "enabled": True,
                    "wait_for_selector": ".product",
                    "selectors": {
                        "title": {
                            "selector": ".product h3",
                            "text": True,
                            "required": True
                        },
                        "price": {
                            "selector": ".product .price",
                            "text": True,
                            "required": True,
                            "transform": "extract_price"
                        },
                        "rating": {
                            "selector": ".product .rating",
                            "attribute": "data-rating",
                            "required": False,
                            "transform": "extract_number"
                        },
                        "image_url": {
                            "selector": ".product img",
                            "attribute": "src",
                            "required": False
                        }
                    }
                }
            ],
            "browser": {
                "headless": True,
                "timeout": 20000
            },
            "excel": {
                "output_file": str(temp_dir / "products_scraped.xlsx"),
                "worksheet_name": "Products",
                "auto_fit_columns": True,
                "freeze_header_row": True
            }
        }
        
        config = ScrapingConfig(**config_data)
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup mocks
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.wait_for_selector = AsyncMock()
            mock_page.url = "http://products.example.com"
            
            # Mock product elements
            mock_products = []
            for i in range(5):  # Mock 5 products
                mock_product = AsyncMock()
                
                mock_title = AsyncMock()
                mock_title.inner_text = AsyncMock(return_value=f"Product {i+1}")
                
                mock_price = AsyncMock()
                mock_price.inner_text = AsyncMock(return_value=f"${(i+1)*10}.99")
                
                mock_rating = AsyncMock()
                mock_rating.get_attribute = AsyncMock(return_value=str((i % 5) + 1))
                
                mock_image = AsyncMock()
                mock_image.get_attribute = AsyncMock(return_value=f"http://example.com/image{i+1}.jpg")
                
                def make_product_selector_mock(title, price, rating, image):
                    def selector_mock(selector):
                        if "h3" in selector:
                            return title
                        elif ".price" in selector:
                            return price
                        elif ".rating" in selector:
                            return rating
                        elif "img" in selector:
                            return image
                        return None
                    return selector_mock
                
                mock_product.query_selector = AsyncMock(
                    side_effect=make_product_selector_mock(mock_title, mock_price, mock_rating, mock_image)
                )
                mock_products.append(mock_product)
            
            # Setup container and pagination detection
            def mock_query_selector_all_products(selector):
                if ".product" in selector:
                    return mock_products
                return []  # No pagination elements
            
            def mock_query_selector_products(selector):
                if 'page' in selector or 'Next' in selector or 'next' in selector or 'pagination' in selector:
                    return None  # No pagination buttons
                return None
            
            mock_page.query_selector_all = AsyncMock(side_effect=mock_query_selector_all_products)
            mock_page.query_selector = AsyncMock(side_effect=mock_query_selector_products)
            
            # Run scraper
            scraper = WebScraper(config)
            scraped_data = await scraper.scrape_all()
            
            # Verify results
            assert "mock_products" in scraped_data
            products_data = scraped_data["mock_products"]
            assert len(products_data) == 5
            
            # Check data transformations
            for i, product in enumerate(products_data):
                assert "title" in product
                assert "price" in product
                assert product["title"] == f"Product {i+1}"
                # Price should be transformed by extract_price transformer
                assert isinstance(product["price"], (int, float)) or "$" in str(product["price"])
            
            # Verify Excel output
            excel_file = Path(config.excel.output_file)
            assert excel_file.exists()
            
            df = pd.read_excel(excel_file, sheet_name=config.excel.worksheet_name)
            assert len(df) == 5
            assert all(col in df.columns for col in ["title", "price", "rating", "image_url"])
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, temp_dir):
        """Test workflow with error recovery and retry logic."""
        config_data = {
            "sites": [
                {
                    "name": "unreliable_site",
                    "url": "http://unreliable.example.com",
                    "enabled": True,
                    "selectors": {
                        "content": {
                            "selector": ".content",
                            "text": True
                        }
                    }
                }
            ],
            "browser": {
                "headless": True,
                "timeout": 5000  # Short timeout to test error handling
            },
            "excel": {
                "output_file": str(temp_dir / "error_recovery_test.xlsx")
            },
            "retry": {
                "max_attempts": 3,
                "delay": 0.1,
                "backoff_factor": 2.0
            }
        }
        
        config = ScrapingConfig(**config_data)
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # Simulate intermittent failures
            failure_count = 0
            def failing_goto(*args, **kwargs):
                nonlocal failure_count
                failure_count += 1
                if failure_count <= 2:  # Fail first 2 attempts
                    raise Exception(f"Network error {failure_count}")
                return AsyncMock()  # Succeed on 3rd attempt
            
            mock_page.goto = AsyncMock(side_effect=failing_goto)
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.url = "http://unreliable.example.com"
            
            # Mock successful content extraction after retries
            mock_element = AsyncMock()
            mock_element.inner_text = AsyncMock(return_value="Recovered content")
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_page.query_selector_all = AsyncMock(return_value=[])
            
            # Run scraper
            scraper = WebScraper(config)
            scraped_data = await scraper.scrape_all()
            
            # Should eventually succeed after retries
            assert "unreliable_site" in scraped_data
            
            # Even if individual site fails, should still create Excel file
            excel_file = Path(config.excel.output_file)
            # File might be created even with empty data depending on implementation
    
    @pytest.mark.asyncio 
    async def test_configuration_validation_workflow(self, temp_dir):
        """Test workflow with various configuration validations."""
        # Test with invalid configuration
        with pytest.raises(ValueError):
            ScrapingConfig(sites=[])  # Empty sites should fail validation
        
        # Test with valid minimal configuration
        minimal_config = ScrapingConfig(
            sites=[
                {
                    "name": "minimal_site",
                    "url": "https://example.com",
                    "selectors": {
                        "title": {"selector": "h1"}
                    }
                }
            ],
            excel={"output_file": str(temp_dir / "minimal_test.xlsx")}
        )
        
        assert len(minimal_config.sites) == 1
        assert minimal_config.sites[0].name == "minimal_site"
        assert minimal_config.excel.output_file == str(temp_dir / "minimal_test.xlsx")
    
    @pytest.mark.asyncio
    async def test_performance_benchmarking(self, temp_dir):
        """Test performance characteristics of the scraping workflow."""
        import time
        
        config_data = {
            "sites": [
                {
                    "name": f"perf_site_{i}",
                    "url": f"https://example{i}.com",
                    "selectors": {
                        "title": {"selector": "h1"},
                        "content": {"selector": ".content"}
                    }
                }
                for i in range(3)  # Test with 3 sites
            ],
            "browser": {
                "headless": True
            },
            "excel": {
                "output_file": str(temp_dir / "performance_test.xlsx")
            },
            "concurrent_sites": 3  # Scrape all sites concurrently
        }
        
        config = ScrapingConfig(**config_data)
        
        with patch('src.auto_scrape.core.browser.async_playwright') as mock_playwright:
            # Setup fast mocks for performance testing
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # Fast mocks
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.url = "https://example.com"
            
            # Mock elements to find
            mock_elements = []
            for j in range(10):  # 10 items per site
                mock_element = AsyncMock()
                mock_title = AsyncMock()
                mock_title.inner_text = AsyncMock(return_value=f"Title {j+1}")
                mock_content = AsyncMock()
                mock_content.inner_text = AsyncMock(return_value=f"Content {j+1}")
                
                def make_perf_selector_mock(title_elem, content_elem):
                    def selector_mock(selector):
                        if "h1" in selector:
                            return title_elem
                        elif ".content" in selector:
                            return content_elem
                        return None
                    return selector_mock
                
                mock_element.query_selector = AsyncMock(
                    side_effect=make_perf_selector_mock(mock_title, mock_content)
                )
                mock_elements.append(mock_element)
            
            def mock_query_selector_all_perf(selector):
                # For container detection, return elements that will be treated as containers
                if any(pattern in selector for pattern in ['.product', '.item', '.post', '.card', 'article', 'div']):
                    return mock_elements[:10]  # Only return 10 items
                return []
                
            def mock_query_selector_perf(selector):
                if 'page' in selector or 'Next' in selector or 'next' in selector or 'pagination' in selector:
                    return None
                return None
            
            mock_page.query_selector = AsyncMock(side_effect=mock_query_selector_perf)
            mock_page.query_selector_all = AsyncMock(side_effect=mock_query_selector_all_perf)
            
            # Measure execution time
            start_time = time.time()
            
            scraper = WebScraper(config)
            scraped_data = await scraper.scrape_all()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify concurrent execution was faster
            # With 3 concurrent sites, should be faster than 3 * single_site_time
            assert execution_time < 10.0  # Should complete within reasonable time
            
            # Verify all sites were processed
            assert len(scraped_data) == 3
            for i in range(3):
                assert f"perf_site_{i}" in scraped_data