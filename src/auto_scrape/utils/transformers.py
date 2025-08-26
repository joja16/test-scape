"""Data transformation utilities."""

import re
from datetime import datetime
from typing import Any, Optional
from decimal import Decimal, InvalidOperation

from loguru import logger


class DataTransformer:
    """Handles data transformation and cleaning."""
    
    def __init__(self):
        """Initialize the data transformer."""
        self._transformers = {
            "extract_price": self._extract_price,
            "extract_rating": self._extract_rating,
            "extract_number": self._extract_number,
            "clean_text": self._clean_text,
            "extract_date": self._extract_date,
            "normalize_whitespace": self._normalize_whitespace,
            "remove_html": self._remove_html,
            "extract_email": self._extract_email,
            "extract_phone": self._extract_phone,
            "extract_url": self._extract_url,
            "title_case": self._title_case,
            "upper_case": self._upper_case,
            "lower_case": self._lower_case,
            "trim": self._trim,
            "extract_digits": self._extract_digits,
        }
    
    def transform(self, value: Any, transform_name: str) -> Any:
        """Apply transformation to a value.
        
        Args:
            value: Value to transform
            transform_name: Name of the transformation
            
        Returns:
            Transformed value
        """
        if value is None:
            return value
        if value == "":
            return None if transform_name in ["extract_price", "extract_rating", "extract_number", "extract_email", "extract_phone", "extract_url", "extract_date"] else value
        
        if transform_name not in self._transformers:
            logger.warning(f"Unknown transformation: {transform_name}")
            return value
        
        try:
            return self._transformers[transform_name](value)
        except Exception as e:
            logger.warning(f"Error applying transformation '{transform_name}' to '{value}': {e}")
            return value
    
    def _extract_price(self, value: str) -> Optional[float]:
        """Extract price from text.
        
        Args:
            value: Text containing price
            
        Returns:
            Extracted price as float or None
        """
        if not isinstance(value, str):
            return None
        
        # Look for price patterns with currency symbols - order matters!
        price_patterns = [
            # Full format with thousands and decimals
            r'[\$€£¥]?\s*(\d{1,3}(?:,\d{3})+\.\d{2})',  # $1,234.56 or 1,234.56
            # European format with comma as decimal
            r'[\$€£¥]?\s*(\d+,\d{2})(?![,\d])',  # €25,99 (not part of larger number)
            # Simple decimal format
            r'[\$€£¥]\s*(\d+\.\d{2})',  # $19.99
            # Thousands separator without decimal
            r'[\$€£¥]?\s*(\d{1,3}(?:,\d{3})+)(?!\.\d)',  # $1,500
            # Simple number with currency
            r'[\$€£¥]\s*(\d+)',  # $100
            # Just number with decimal
            r'(\d+\.\d{2})',  # 19.99
            # Just integer
            r'(\d+)'  # 500
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, value)
            if match:
                price_str = match.group(1)
                try:
                    # Handle European format (comma as decimal, no thousands separator)
                    if re.match(r'^\d+,\d{2}$', price_str):
                        price_str = price_str.replace(',', '.')
                    # Handle thousands separators (comma as thousands separator)
                    elif ',' in price_str and price_str.count(',') >= 1:
                        if '.' in price_str:
                            # Format like 1,234.56
                            price_str = price_str.replace(',', '')
                        else:
                            # Format like 1,234 or 1,234,567
                            price_str = price_str.replace(',', '')
                    
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_rating(self, value: str) -> Optional[float]:
        """Extract rating from text or class names.
        
        Args:
            value: Text or class containing rating
            
        Returns:
            Extracted rating as float or None
        """
        if not isinstance(value, str):
            return None
        
        # Look for star ratings in class names like "star-rating Three"
        star_words = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5
        }
        
        for word, rating in star_words.items():
            if word.lower() in value.lower():
                return float(rating)
        
        # Look for numeric ratings
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?', value)
        if match:
            rating = float(match.group(1))
            max_rating = float(match.group(2)) if match.group(2) else 5
            
            # Normalize to 5-star scale
            if max_rating != 5:
                rating = (rating / max_rating) * 5
            
            return round(rating, 2)
        
        return None
    
    def _extract_number(self, value: str) -> Optional[float]:
        """Extract first number from text.
        
        Args:
            value: Text containing number
            
        Returns:
            Extracted number as float or None
        """
        if not isinstance(value, str):
            return None
        
        match = re.search(r'-?\d+(?:\.\d+)?', value)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return None
    
    def _clean_text(self, value: str) -> str:
        """Clean text by removing extra whitespace and special characters.
        
        Args:
            value: Text to clean
            
        Returns:
            Cleaned text
        """
        if not isinstance(value, str):
            return str(value)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', value)
        
        # Remove special characters but keep alphanumeric and common punctuation
        cleaned = re.sub(r'[^\w\s\-.,!?()\'"]', '', cleaned)
        
        return cleaned.strip()
    
    def _extract_date(self, value: str) -> Optional[str]:
        """Extract date from text.
        
        Args:
            value: Text containing date
            
        Returns:
            Extracted date in ISO format or None
        """
        if not isinstance(value, str):
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # MM.DD.YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, value)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD format
                            year, month, day = groups
                        else:  # MM/DD/YYYY format
                            month, day, year = groups
                        
                        date_obj = datetime(int(year), int(month), int(day))
                        return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _normalize_whitespace(self, value: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            value: Text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        if not isinstance(value, str):
            return str(value)
        
        return re.sub(r'\s+', ' ', value).strip()
    
    def _remove_html(self, value: str) -> str:
        """Remove HTML tags from text.
        
        Args:
            value: Text with HTML tags
            
        Returns:
            Text without HTML tags
        """
        if not isinstance(value, str):
            return str(value)
        
        # Remove HTML tags
        cleaned = re.sub(r'<[^>]+>', '', value)
        
        # Decode HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
        }
        
        for entity, replacement in html_entities.items():
            cleaned = cleaned.replace(entity, replacement)
        
        return self._normalize_whitespace(cleaned)
    
    def _extract_email(self, value: str) -> Optional[str]:
        """Extract email address from text.
        
        Args:
            value: Text containing email
            
        Returns:
            Extracted email or None
        """
        if not isinstance(value, str):
            return None
        
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, value)
        
        return match.group() if match else None
    
    def _extract_phone(self, value: str) -> Optional[str]:
        """Extract phone number from text.
        
        Args:
            value: Text containing phone number
            
        Returns:
            Extracted phone number or None
        """
        if not isinstance(value, str):
            return None
        
        # Remove all non-digit characters except + at the beginning
        cleaned = re.sub(r'[^\d+]', '', value)
        
        # Look for phone number patterns
        patterns = [
            r'\+?1?(\d{10})',  # US phone number
            r'\+?(\d{11})',    # International with country code
            r'\+?(\d{10})',    # 10-digit number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                return match.group()
        
        return None
    
    def _extract_url(self, value: str) -> Optional[str]:
        """Extract URL from text.
        
        Args:
            value: Text containing URL
            
        Returns:
            Extracted URL or None
        """
        if not isinstance(value, str):
            return None
        
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(pattern, value)
        
        return match.group() if match else None
    
    def _title_case(self, value: str) -> str:
        """Convert text to title case.
        
        Args:
            value: Text to convert
            
        Returns:
            Text in title case
        """
        if not isinstance(value, str):
            return str(value)
        
        return value.title()
    
    def _upper_case(self, value: str) -> str:
        """Convert text to upper case.
        
        Args:
            value: Text to convert
            
        Returns:
            Text in upper case
        """
        if not isinstance(value, str):
            return str(value)
        
        return value.upper()
    
    def _lower_case(self, value: str) -> str:
        """Convert text to lower case.
        
        Args:
            value: Text to convert
            
        Returns:
            Text in lower case
        """
        if not isinstance(value, str):
            return str(value)
        
        return value.lower()
    
    def _trim(self, value: str) -> str:
        """Trim whitespace from text.
        
        Args:
            value: Text to trim
            
        Returns:
            Trimmed text
        """
        if not isinstance(value, str):
            return str(value)
        
        return value.strip()
    
    def _extract_digits(self, value: str) -> str:
        """Extract only digits from text.
        
        Args:
            value: Text containing digits
            
        Returns:
            String with only digits
        """
        if not isinstance(value, str):
            return str(value)
        
        return re.sub(r'[^\d]', '', value)