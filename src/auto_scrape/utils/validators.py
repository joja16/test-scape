"""Data validation utilities."""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from loguru import logger


class DataValidator:
    """Validates scraped data for accuracy and completeness."""
    
    def __init__(self):
        """Initialize the data validator."""
        self._validators = {
            "required": self._validate_required,
            "email": self._validate_email,
            "url": self._validate_url,
            "phone": self._validate_phone,
            "number": self._validate_number,
            "price": self._validate_price,
            "date": self._validate_date,
            "min_length": self._validate_min_length,
            "max_length": self._validate_max_length,
            "regex": self._validate_regex,
        }
    
    def validate_item(
        self, 
        item_data: Dict[str, Any], 
        validation_rules: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Validate a single data item.
        
        Args:
            item_data: Data item to validate
            validation_rules: Validation rules for each field
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "field_results": {}
        }
        
        for field_name, field_value in item_data.items():
            if field_name in validation_rules:
                field_result = self._validate_field(
                    field_value, validation_rules[field_name]
                )
                validation_results["field_results"][field_name] = field_result
                
                if not field_result["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["errors"].extend(
                        [f"{field_name}: {error}" for error in field_result["errors"]]
                    )
                
                validation_results["warnings"].extend(
                    [f"{field_name}: {warning}" for warning in field_result["warnings"]]
                )
        
        return validation_results
    
    def validate_batch(
        self, 
        data_items: List[Dict[str, Any]], 
        validation_rules: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Validate a batch of data items.
        
        Args:
            data_items: List of data items to validate
            validation_rules: Validation rules for each field
            
        Returns:
            Dictionary with batch validation results
        """
        batch_results = {
            "total_items": len(data_items),
            "valid_items": 0,
            "invalid_items": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "item_results": [],
            "field_statistics": {},
            "common_errors": {}
        }
        
        for i, item in enumerate(data_items):
            item_result = self.validate_item(item, validation_rules)
            item_result["item_index"] = i
            batch_results["item_results"].append(item_result)
            
            if item_result["is_valid"]:
                batch_results["valid_items"] += 1
            else:
                batch_results["invalid_items"] += 1
            
            batch_results["total_errors"] += len(item_result["errors"])
            batch_results["total_warnings"] += len(item_result["warnings"])
            
            # Track common errors
            for error in item_result["errors"]:
                if error not in batch_results["common_errors"]:
                    batch_results["common_errors"][error] = 0
                batch_results["common_errors"][error] += 1
        
        # Calculate field statistics
        batch_results["field_statistics"] = self._calculate_field_statistics(
            data_items, validation_rules
        )
        
        batch_results["success_rate"] = (
            batch_results["valid_items"] / batch_results["total_items"] * 100
            if batch_results["total_items"] > 0 else 0
        )
        
        return batch_results
    
    def _validate_field(
        self, 
        field_value: Any, 
        field_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate a single field value.
        
        Args:
            field_value: Value to validate
            field_rules: List of validation rules
            
        Returns:
            Dictionary with field validation results
        """
        field_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        for rule in field_rules:
            rule_type = rule.get("type")
            rule_params = rule.get("params", {})
            
            if rule_type not in self._validators:
                logger.warning(f"Unknown validation rule: {rule_type}")
                continue
            
            try:
                validator_result = self._validators[rule_type](field_value, rule_params)
                
                if not validator_result["is_valid"]:
                    field_result["is_valid"] = False
                    field_result["errors"].extend(validator_result.get("errors", []))
                
                field_result["warnings"].extend(validator_result.get("warnings", []))
                
            except Exception as e:
                logger.error(f"Error validating field with rule {rule_type}: {e}")
                field_result["errors"].append(f"Validation error: {e}")
        
        return field_result
    
    def _validate_required(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a value is not empty or None.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Validation result
        """
        is_valid = value is not None and str(value).strip() != ""
        
        return {
            "is_valid": is_valid,
            "errors": ["Field is required but empty"] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_email(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email format.
        
        Args:
            value: Email value to validate
            params: Validation parameters
            
        Returns:
            Validation result
        """
        if value is None or str(value).strip() == "":
            return {"is_valid": True, "errors": [], "warnings": []}
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(email_pattern, str(value)))
        
        return {
            "is_valid": is_valid,
            "errors": ["Invalid email format"] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_url(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate URL format.
        
        Args:
            value: URL value to validate
            params: Validation parameters
            
        Returns:
            Validation result
        """
        if value is None or str(value).strip() == "":
            return {"is_valid": True, "errors": [], "warnings": []}
        
        try:
            result = urlparse(str(value))
            is_valid = all([result.scheme, result.netloc])
        except Exception:
            is_valid = False
        
        return {
            "is_valid": is_valid,
            "errors": ["Invalid URL format"] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_phone(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate phone number format.
        
        Args:
            value: Phone value to validate
            params: Validation parameters
            
        Returns:
            Validation result
        """
        if value is None or str(value).strip() == "":
            return {"is_valid": True, "errors": [], "warnings": []}
        
        # Basic phone validation - adjust pattern as needed
        phone_pattern = r'^\+?[\d\s\-\(\)]{10,15}$'
        is_valid = bool(re.match(phone_pattern, str(value)))
        
        return {
            "is_valid": is_valid,
            "errors": ["Invalid phone number format"] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_number(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate numeric value.
        
        Args:
            value: Numeric value to validate
            params: Validation parameters (min, max)
            
        Returns:
            Validation result
        """
        if value is None or str(value).strip() == "":
            return {"is_valid": True, "errors": [], "warnings": []}
        
        try:
            num_value = float(value)
            errors = []
            warnings = []
            
            min_val = params.get("min")
            max_val = params.get("max")
            
            if min_val is not None and num_value < min_val:
                errors.append(f"Value {num_value} is below minimum {min_val}")
            
            if max_val is not None and num_value > max_val:
                errors.append(f"Value {num_value} is above maximum {max_val}")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except (ValueError, TypeError):
            return {
                "is_valid": False,
                "errors": ["Invalid numeric value"],
                "warnings": []
            }
    
    def _validate_price(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate price value.
        
        Args:
            value: Price value to validate
            params: Validation parameters
            
        Returns:
            Validation result
        """
        # Use number validation but with price-specific checks
        result = self._validate_number(value, params)
        
        if result["is_valid"]:
            try:
                price_value = float(value)
                warnings = []
                
                # Add price-specific warnings
                if price_value == 0:
                    warnings.append("Price is zero - might be incorrect")
                elif price_value < 0:
                    result["is_valid"] = False
                    result["errors"].append("Price cannot be negative")
                elif price_value > 100000:  # Adjust threshold as needed
                    warnings.append("Price seems unusually high")
                
                result["warnings"].extend(warnings)
                
            except (ValueError, TypeError):
                pass
        
        return result
    
    def _validate_date(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate date format.
        
        Args:
            value: Date value to validate
            params: Validation parameters
            
        Returns:
            Validation result
        """
        if value is None or str(value).strip() == "":
            return {"is_valid": True, "errors": [], "warnings": []}
        
        # Common date patterns
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
        ]
        
        is_valid = any(re.match(pattern, str(value)) for pattern in date_patterns)
        
        return {
            "is_valid": is_valid,
            "errors": ["Invalid date format"] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_min_length(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate minimum length.
        
        Args:
            value: Value to validate
            params: Parameters with 'length' key
            
        Returns:
            Validation result
        """
        if value is None:
            return {"is_valid": True, "errors": [], "warnings": []}
        
        min_length = params.get("length", 0)
        actual_length = len(str(value))
        is_valid = actual_length >= min_length
        
        return {
            "is_valid": is_valid,
            "errors": [
                f"Length {actual_length} is below minimum {min_length}"
            ] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_max_length(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate maximum length.
        
        Args:
            value: Value to validate
            params: Parameters with 'length' key
            
        Returns:
            Validation result
        """
        if value is None:
            return {"is_valid": True, "errors": [], "warnings": []}
        
        max_length = params.get("length", float('inf'))
        actual_length = len(str(value))
        is_valid = actual_length <= max_length
        
        return {
            "is_valid": is_valid,
            "errors": [
                f"Length {actual_length} exceeds maximum {max_length}"
            ] if not is_valid else [],
            "warnings": []
        }
    
    def _validate_regex(self, value: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate against regular expression pattern.
        
        Args:
            value: Value to validate
            params: Parameters with 'pattern' key
            
        Returns:
            Validation result
        """
        if value is None or str(value).strip() == "":
            return {"is_valid": True, "errors": [], "warnings": []}
        
        pattern = params.get("pattern")
        if not pattern:
            return {"is_valid": True, "errors": [], "warnings": []}
        
        try:
            is_valid = bool(re.match(pattern, str(value)))
            return {
                "is_valid": is_valid,
                "errors": [
                    f"Value does not match pattern: {pattern}"
                ] if not is_valid else [],
                "warnings": []
            }
        except re.error as e:
            return {
                "is_valid": False,
                "errors": [f"Invalid regex pattern: {e}"],
                "warnings": []
            }
    
    def _calculate_field_statistics(
        self, 
        data_items: List[Dict[str, Any]], 
        validation_rules: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics for each field.
        
        Args:
            data_items: List of data items
            validation_rules: Validation rules
            
        Returns:
            Dictionary with field statistics
        """
        field_stats = {}
        
        for field_name in validation_rules.keys():
            field_values = [item.get(field_name) for item in data_items]
            
            field_stats[field_name] = {
                "total_count": len(field_values),
                "non_null_count": sum(1 for v in field_values if v is not None),
                "empty_count": sum(1 for v in field_values if v is None or str(v).strip() == ""),
                "unique_count": len(set(str(v) for v in field_values if v is not None)),
                "fill_rate": sum(1 for v in field_values if v is not None and str(v).strip() != "") / len(field_values) * 100 if field_values else 0
            }
        
        return field_stats