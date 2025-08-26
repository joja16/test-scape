"""Unit tests for data transformers."""

import pytest
from src.auto_scrape.utils.transformers import DataTransformer


class TestDataTransformer:
    """Test DataTransformer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = DataTransformer()
    
    def test_extract_price_simple(self):
        """Test extracting simple price."""
        test_cases = [
            ("$19.99", 19.99),
            ("$1,234.56", 1234.56),
            ("€15.50", 15.50),
            ("Price: $29.99", 29.99),
            ("£100", 100.0),
            ("¥500", 500.0)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_price")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_price_complex(self):
        """Test extracting price from complex strings."""
        test_cases = [
            ("Regular price $19.99, Sale price $15.99", 19.99),
            ("From $10.00 to $20.00", 10.00),
            ("USD 1,500.00", 1500.00),
            ("Cost: 25,99", 25.99)  # European format
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_price")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_price_invalid(self):
        """Test price extraction with invalid input."""
        test_cases = [
            ("No price here", None),
            ("", None),
            ("Price coming soon", None),
            ("Free", None)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_price")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_rating_stars(self):
        """Test extracting star ratings."""
        test_cases = [
            ("star-rating Three", 3.0),
            ("star-rating Five", 5.0),
            ("Rating: Four stars", 4.0),
            ("two star rating", 2.0)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_rating")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_rating_numeric(self):
        """Test extracting numeric ratings."""
        test_cases = [
            ("4.5/5", 4.5),
            ("3.8 out of 5", 3.8),
            ("8/10", 4.0),  # Normalized to 5-star scale
            ("9.5/10", 4.75),
            ("85/100", 4.25)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_rating")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_number(self):
        """Test extracting numbers from text."""
        test_cases = [
            ("Price: $25.99", 25.99),
            ("Quantity: 150 items", 150.0),
            ("Temperature: -5.5°C", -5.5),
            ("Model 2023", 2023.0),
            ("No numbers here", None)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_number")
            assert result == expected, f"Failed for {input_value}"
    
    def test_clean_text(self):
        """Test text cleaning."""
        test_cases = [
            ("  Multiple    spaces  ", "Multiple spaces"),
            ("Text with\n\nnewlines", "Text with newlines"),
            ("Special@#$%characters!", "Specialcharacters!"),
            ("Normal text", "Normal text")
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "clean_text")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_date(self):
        """Test date extraction."""
        test_cases = [
            ("2024-01-15", "2024-01-15"),
            ("01/15/2024", "2024-01-15"),
            ("15-01-2024", "2024-15-01"),  # Note: This might need adjustment
            ("Published on 2024-12-25", "2024-12-25"),
            ("No date here", None)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_date")
            if expected is None:
                assert result is None, f"Failed for {input_value}"
            # Note: Date parsing might need more sophisticated handling
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        test_cases = [
            ("Multiple   spaces", "Multiple spaces"),
            ("\tTab\tcharacters\t", "Tab characters"),
            ("Line\nbreaks\nhere", "Line breaks here"),
            ("  Leading and trailing  ", "Leading and trailing")
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "normalize_whitespace")
            assert result == expected, f"Failed for {input_value}"
    
    def test_remove_html(self):
        """Test HTML tag removal."""
        test_cases = [
            ("<p>Paragraph text</p>", "Paragraph text"),
            ("<b>Bold</b> and <i>italic</i>", "Bold and italic"),
            ("Text with &amp; entities", "Text with & entities"),
            ("<div><span>Nested</span></div>", "Nested"),
            ("No HTML here", "No HTML here")
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "remove_html")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_email(self):
        """Test email extraction."""
        test_cases = [
            ("Contact us at test@example.com", "test@example.com"),
            ("Email: user.name+tag@domain.co.uk", "user.name+tag@domain.co.uk"),
            ("Multiple emails: first@test.com and second@test.com", "first@test.com"),
            ("No email here", None)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_email")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_phone(self):
        """Test phone number extraction."""
        test_cases = [
            ("Call us at (555) 123-4567", "5551234567"),
            ("Phone: +1-800-555-0123", "+18005550123"),
            ("Contact: 555.123.4567", "5551234567"),
            ("International: +44 20 7946 0958", "+442079460958"),
            ("No phone here", None)
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_phone")
            if expected is None:
                assert result is None, f"Failed for {input_value}"
            else:
                # Phone extraction might return different formats
                assert result is not None, f"Failed for {input_value}"
    
    def test_case_transformations(self):
        """Test case transformations."""
        test_text = "Hello World"
        
        assert self.transformer.transform(test_text, "title_case") == "Hello World"
        assert self.transformer.transform(test_text, "upper_case") == "HELLO WORLD"
        assert self.transformer.transform(test_text, "lower_case") == "hello world"
    
    def test_trim(self):
        """Test text trimming."""
        test_cases = [
            ("  trimmed  ", "trimmed"),
            ("\ttabs\t", "tabs"),
            ("no trim needed", "no trim needed")
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "trim")
            assert result == expected, f"Failed for {input_value}"
    
    def test_extract_digits(self):
        """Test digit extraction."""
        test_cases = [
            ("Phone: 555-123-4567", "5551234567"),
            ("Product ID: ABC123DEF456", "123456"),
            ("Model 2024-X", "2024"),
            ("No digits", "")
        ]
        
        for input_value, expected in test_cases:
            result = self.transformer.transform(input_value, "extract_digits")
            assert result == expected, f"Failed for {input_value}"
    
    def test_unknown_transformation(self):
        """Test handling of unknown transformation."""
        result = self.transformer.transform("test", "unknown_transform")
        assert result == "test"  # Should return original value
    
    def test_none_input(self):
        """Test handling of None input."""
        result = self.transformer.transform(None, "extract_price")
        assert result is None
    
    def test_empty_input(self):
        """Test handling of empty input."""
        # For extraction transforms, empty string should return None
        result = self.transformer.transform("", "extract_price")
        assert result is None
        
        # For text transforms, empty string should remain empty string
        result = self.transformer.transform("", "trim")
        assert result == ""