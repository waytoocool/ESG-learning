# Phase 4: Unit conversion utilities for ESG DataVault

class UnitConverter:
    """Utility class for converting between different units within the same category."""
    
    # Unit conversion mappings (base unit -> multiplier to convert to base)
    CONVERSION_FACTORS = {
        'energy': {
            'base': 'kWh',
            'conversions': {
                'Wh': 0.001,
                'kWh': 1.0,
                'MWh': 1000.0,
                'GWh': 1000000.0,
                'TWh': 1000000000.0,
                'J': 0.000000278,
                'kJ': 0.000278,
                'MJ': 0.278,
                'GJ': 278.0,
                'BTU': 0.000293,
                'kBTU': 0.293,
                'MMBTU': 293.0
            }
        },
        'money': {
            'base': 'USD',
            'conversions': {
                'USD': 1.0,
                'EUR': 1.1,  # Example rates - in production, use live rates
                'GBP': 1.25,
                'JPY': 0.0067,
                'CAD': 0.74,
                'AUD': 0.67,
                'INR': 0.012
            }
        },
        'emission': {
            'base': 'tCO2e',
            'conversions': {
                'gCO2e': 0.000001,
                'kgCO2e': 0.001,
                'tCO2e': 1.0,
                'MtCO2e': 1000000.0,
                'lbCO2e': 0.000454,
                'tonCO2e': 0.907  # Short ton to metric ton
            }
        },
        'weight': {
            'base': 'kg',
            'conversions': {
                'g': 0.001,
                'kg': 1.0,
                't': 1000.0,
                'Mt': 1000000000.0,
                'lb': 0.453592,
                'oz': 0.0283495,
                'ton': 907.185  # Short ton
            }
        },
        'volume': {
            'base': 'L',
            'conversions': {
                'mL': 0.001,
                'L': 1.0,
                'kL': 1000.0,
                'ML': 1000000.0,
                'm3': 1000.0,
                'gal': 3.78541,  # US gallon
                'ft3': 28.3168,
                'bbl': 158.987   # Oil barrel
            }
        },
        'percentage': {
            'base': '%',
            'conversions': {
                '%': 1.0,
                'decimal': 0.01,
                'ratio': 0.01,
                'bps': 0.0001  # Basis points
            }
        },
        'time': {
            'base': 'hours',
            'conversions': {
                'seconds': 0.000278,
                'minutes': 0.0167,
                'hours': 1.0,
                'days': 24.0,
                'weeks': 168.0,
                'months': 730.0,  # Approximate
                'years': 8760.0
            }
        },
        'count': {
            'base': 'units',
            'conversions': {
                'units': 1.0,
                'thousands': 1000.0,
                'millions': 1000000.0,
                'billions': 1000000000.0,
                'FTE': 1.0,  # Full-time equivalent
                'headcount': 1.0
            }
        }
    }

    @classmethod
    def get_unit_category(cls, unit):
        """Get the category for a given unit."""
        for category, data in cls.CONVERSION_FACTORS.items():
            if unit in data['conversions']:
                return category
        return None

    @classmethod
    def get_available_units(cls, category):
        """Get all available units for a given category."""
        if category in cls.CONVERSION_FACTORS:
            return list(cls.CONVERSION_FACTORS[category]['conversions'].keys())
        return []

    @classmethod
    def convert_value(cls, value, from_unit, to_unit):
        """Convert a value from one unit to another within the same category.
        
        Args:
            value (float): The value to convert
            from_unit (str): Source unit
            to_unit (str): Target unit
            
        Returns:
            tuple: (converted_value, success, error_message)
        """
        try:
            # Find categories for both units
            from_category = cls.get_unit_category(from_unit)
            to_category = cls.get_unit_category(to_unit)
            
            if not from_category or not to_category:
                return value, False, f"Unknown unit(s): {from_unit} or {to_unit}"
            
            if from_category != to_category:
                return value, False, f"Cannot convert between different categories: {from_category} -> {to_category}"
            
            # Same unit, no conversion needed
            if from_unit == to_unit:
                return value, True, None
            
            # Convert to base unit, then to target unit
            conversions = cls.CONVERSION_FACTORS[from_category]['conversions']
            base_value = value * conversions[from_unit]
            converted_value = base_value / conversions[to_unit]
            
            return converted_value, True, None
            
        except (KeyError, ZeroDivisionError, TypeError) as e:
            return value, False, f"Conversion error: {str(e)}"

    @classmethod
    def normalize_to_default(cls, value, unit, field_default_unit):
        """Convert a value to the field's default unit if different.
        
        Args:
            value (float): The value to normalize
            unit (str): Current unit of the value
            field_default_unit (str): Default unit for the field
            
        Returns:
            tuple: (normalized_value, success, conversion_info)
        """
        if not unit or unit == field_default_unit:
            return value, True, {"conversion_applied": False}
        
        converted_value, success, error = cls.convert_value(value, unit, field_default_unit)
        
        return converted_value, success, {
            "conversion_applied": success,
            "original_value": value,
            "original_unit": unit,
            "converted_value": converted_value,
            "target_unit": field_default_unit,
            "error": error
        }

    @classmethod
    def get_unit_dropdown_options(cls, unit_category):
        """Get formatted options for unit dropdown based on category.
        
        Args:
            unit_category (str): The unit category
            
        Returns:
            list: List of dicts with 'value' and 'label' keys
        """
        if unit_category not in cls.CONVERSION_FACTORS:
            return []
        
        units = cls.CONVERSION_FACTORS[unit_category]['conversions']
        base_unit = cls.CONVERSION_FACTORS[unit_category]['base']
        
        options = []
        for unit in sorted(units.keys()):
            label = unit
            if unit == base_unit:
                label += " (default)"
            options.append({
                'value': unit,
                'label': label
            })
        
        return options

    @classmethod
    def validate_unit_for_category(cls, unit, expected_category):
        """Validate that a unit belongs to the expected category.
        
        Args:
            unit (str): Unit to validate
            expected_category (str): Expected category
            
        Returns:
            tuple: (is_valid, actual_category, error_message)
        """
        if not unit:
            return True, None, None  # Empty unit is allowed
        
        actual_category = cls.get_unit_category(unit)
        
        if not actual_category:
            return False, None, f"Unknown unit: {unit}"
        
        if expected_category and actual_category != expected_category:
            return False, actual_category, f"Unit '{unit}' belongs to category '{actual_category}', expected '{expected_category}'"
        
        return True, actual_category, None


# Convenience functions for common operations

def convert_to_field_default(esg_data_value, input_unit, field):
    """Convert ESG data value to field's default unit.
    
    Args:
        esg_data_value (float): The raw value
        input_unit (str): Unit of the input value 
        field (FrameworkDataField): The field object
        
    Returns:
        tuple: (converted_value, conversion_info)
    """
    if not field.default_unit:
        return esg_data_value, {"no_default_unit": True}
    
    return UnitConverter.normalize_to_default(
        esg_data_value, 
        input_unit, 
        field.default_unit
    )


def get_unit_options_for_field(field):
    """Get unit dropdown options for a specific field.
    
    Args:
        field (FrameworkDataField): The field object
        
    Returns:
        list: Unit options for dropdown
    """
    if not field.unit_category:
        return []
    
    return UnitConverter.get_unit_dropdown_options(field.unit_category)


def validate_esg_data_unit(unit, field):
    """Validate that a unit is appropriate for a field.
    
    Args:
        unit (str): Unit to validate
        field (FrameworkDataField): The field object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    is_valid, actual_category, error = UnitConverter.validate_unit_for_category(
        unit, 
        field.unit_category
    )
    
    return is_valid, error 