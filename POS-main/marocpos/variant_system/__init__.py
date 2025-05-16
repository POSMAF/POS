"""
Variant System Package

This package provides a complete system for managing product variants,
including attributes, values, rules, and inventory.
"""

# Import main modules for easy access
from .db_schema import initialize_database
from .attribute_manager import AttributeType, AttributeValue, ProductAttribute, ProductAttributeValue
from .variant_manager import ProductVariant, VariantInventory
from .rules_engine import AttributeRule, RulesEngine

def initialize():
    """Initialize the variant system"""
    return initialize_database()
