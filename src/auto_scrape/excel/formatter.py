"""Excel formatting utilities."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from loguru import logger


class ExcelFormatter:
    """Handles Excel data formatting and styling."""
    
    def __init__(self):
        """Initialize Excel formatter."""
        self._format_rules = {
            "currency": self._format_currency,
            "percentage": self._format_percentage,
            "date": self._format_date,
            "phone": self._format_phone,
            "url": self._format_url,
            "text": self._format_text,
            "number": self._format_number,
        }
    
    def format_data(
        self, 
        data: List[Dict[str, Any]], 
        format_rules: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Format data according to specified rules.
        
        Args:
            data: List of data dictionaries
            format_rules: Dictionary mapping field names to format types
            
        Returns:
            List of formatted data dictionaries
        """
        if not format_rules:
            format_rules = self._infer_format_rules(data)
        
        formatted_data = []
        
        for item in data:
            formatted_item = {}
            for field_name, field_value in item.items():
                format_type = format_rules.get(field_name, "text")
                formatted_item[field_name] = self._apply_format(field_value, format_type)
            formatted_data.append(formatted_item)
        
        return formatted_data
    
    def _infer_format_rules(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Infer format rules from data patterns.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            Dictionary mapping field names to inferred format types
        """
        format_rules = {}
        
        if not data:
            return format_rules
        
        # Analyze each field
        for field_name in data[0].keys():
            field_values = [item.get(field_name) for item in data if item.get(field_name)]
            
            if not field_values:
                format_rules[field_name] = "text"
                continue
            
            # Check for currency patterns
            if any(self._is_currency(str(value)) for value in field_values):
                format_rules[field_name] = "currency"
            # Check for percentage patterns
            elif any("%" in str(value) for value in field_values):
                format_rules[field_name] = "percentage"
            # Check for date patterns
            elif any(self._is_date(str(value)) for value in field_values):
                format_rules[field_name] = "date"
            # Check for phone patterns
            elif any(self._is_phone(str(value)) for value in field_values):
                format_rules[field_name] = "phone"
            # Check for URL patterns
            elif any(self._is_url(str(value)) for value in field_values):
                format_rules[field_name] = "url"
            # Check for numeric patterns
            elif any(self._is_number(str(value)) for value in field_values):
                format_rules[field_name] = "number"
            else:
                format_rules[field_name] = "text"
        
        logger.debug(f"Inferred format rules: {format_rules}")
        return format_rules
    
    def _apply_format(self, value: Any, format_type: str) -> Any:
        """Apply specific formatting to a value.
        
        Args:
            value: Value to format
            format_type: Type of formatting to apply
            
        Returns:
            Formatted value
        """
        if value is None or value == "":
            return value
        
        if format_type not in self._format_rules:
            logger.warning(f"Unknown format type: {format_type}")
            return value
        
        try:
            return self._format_rules[format_type](value)
        except Exception as e:
            logger.warning(f"Error formatting value '{value}' as '{format_type}': {e}")
            return value
    
    def _format_currency(self, value: Any) -> str:
        """Format value as currency.
        
        Args:
            value: Value to format as currency
            
        Returns:
            Formatted currency string
        """
        if isinstance(value, (int, float)):
            return f"${value:,.2f}"
        
        # Try to extract numeric value from string
        value_str = str(value)
        numeric_match = re.search(r'[\d,]+\.?\d*', value_str)
        
        if numeric_match:
            try:
                numeric_value = float(numeric_match.group().replace(',', ''))
                return f"${numeric_value:,.2f}"
            except ValueError:
                pass
        
        return str(value)
    
    def _format_percentage(self, value: Any) -> str:
        """Format value as percentage.
        
        Args:
            value: Value to format as percentage
            
        Returns:
            Formatted percentage string
        """
        if isinstance(value, (int, float)):
            return f"{value:.1f}%"
        
        value_str = str(value)
        
        # If already has %, just clean it up
        if "%" in value_str:
            numeric_match = re.search(r'(\d+\.?\d*)', value_str)
            if numeric_match:
                try:
                    numeric_value = float(numeric_match.group())
                    return f"{numeric_value:.1f}%"
                except ValueError:
                    pass
        else:
            # Try to convert to percentage
            try:
                numeric_value = float(value_str)
                if numeric_value <= 1:  # Assume it's a decimal
                    return f"{numeric_value * 100:.1f}%"
                else:  # Assume it's already a percentage
                    return f"{numeric_value:.1f}%"
            except ValueError:
                pass
        
        return str(value)
    
    def _format_date(self, value: Any) -> str:
        """Format value as date.
        
        Args:
            value: Value to format as date
            
        Returns:
            Formatted date string
        """
        value_str = str(value)
        
        # Common date patterns and their desired format
        date_patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%m-%d-%Y'),
        ]
        
        for pattern, format_str in date_patterns:
            match = re.search(pattern, value_str)
            if match:
                try:
                    if format_str == '%Y-%m-%d':
                        year, month, day = match.groups()
                    else:
                        month, day, year = match.groups()
                    
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return str(value)
    
    def _format_phone(self, value: Any) -> str:
        """Format value as phone number.
        
        Args:
            value: Value to format as phone number
            
        Returns:
            Formatted phone number string
        """
        value_str = str(value)
        
        # Extract digits only
        digits = re.sub(r'[^\d]', '', value_str)
        
        # Format based on length
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return str(value)
    
    def _format_url(self, value: Any) -> str:
        """Format value as URL.
        
        Args:
            value: Value to format as URL
            
        Returns:
            Formatted URL string
        """
        value_str = str(value).strip()
        
        # Ensure URL has protocol
        if not value_str.startswith(('http://', 'https://')):
            if value_str.startswith('www.'):
                return f"https://{value_str}"
            elif '.' in value_str and not value_str.startswith('//'):
                return f"https://{value_str}"
        
        return value_str
    
    def _format_text(self, value: Any) -> str:
        """Format value as clean text.
        
        Args:
            value: Value to format as text
            
        Returns:
            Formatted text string
        """
        value_str = str(value)
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', value_str).strip()
        
        # Remove excessive punctuation
        cleaned = re.sub(r'([.!?]){2,}', r'\1', cleaned)
        
        return cleaned
    
    def _format_number(self, value: Any) -> str:
        """Format value as number.
        
        Args:
            value: Value to format as number
            
        Returns:
            Formatted number string
        """
        try:
            # Try to convert to float
            if isinstance(value, (int, float)):
                if value == int(value):
                    return f"{int(value):,}"
                else:
                    return f"{value:,.2f}"
            
            # Try to parse string as number
            value_str = str(value).replace(',', '')
            numeric_value = float(value_str)
            
            if numeric_value == int(numeric_value):
                return f"{int(numeric_value):,}"
            else:
                return f"{numeric_value:,.2f}"
                
        except ValueError:
            return str(value)
    
    def _is_currency(self, value_str: str) -> bool:
        """Check if value looks like currency.
        
        Args:
            value_str: String value to check
            
        Returns:
            True if looks like currency
        """
        currency_patterns = [
            r'^\$[\d,]+\.?\d*$',
            r'^[\d,]+\.?\d*\s*(dollar|usd|\$)s?$',
            r'^(price|cost|amount).*[\d,]+\.?\d*$',
        ]
        
        value_lower = value_str.lower()
        return any(re.search(pattern, value_lower) for pattern in currency_patterns)
    
    def _is_date(self, value_str: str) -> bool:
        """Check if value looks like a date.
        
        Args:
            value_str: String value to check
            
        Returns:
            True if looks like a date
        """
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
        ]
        
        return any(re.search(pattern, value_str) for pattern in date_patterns)
    
    def _is_phone(self, value_str: str) -> bool:
        """Check if value looks like a phone number.
        
        Args:
            value_str: String value to check
            
        Returns:
            True if looks like a phone number
        """
        # Remove all non-digit characters
        digits = re.sub(r'[^\d]', '', value_str)
        
        # Check for valid phone number lengths
        return len(digits) in [10, 11] and digits.isdigit()
    
    def _is_url(self, value_str: str) -> bool:
        """Check if value looks like a URL.
        
        Args:
            value_str: String value to check
            
        Returns:
            True if looks like a URL
        """
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            r'[a-zA-Z0-9-]+\.(com|org|net|edu|gov|mil|int|co|io|ly|me|tv)',
        ]
        
        return any(re.search(pattern, value_str) for pattern in url_patterns)
    
    def _is_number(self, value_str: str) -> bool:
        """Check if value looks like a number.
        
        Args:
            value_str: String value to check
            
        Returns:
            True if looks like a number
        """
        try:
            # Try to parse as float after removing commas
            float(value_str.replace(',', ''))
            return True
        except ValueError:
            return False