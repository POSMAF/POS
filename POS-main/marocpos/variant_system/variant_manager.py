"""
Variant Manager Module

This module handles the generation, retrieval and management of product variants.
"""

import sqlite3
import json
import re
import string
import random
from datetime import datetime

from .db_schema import get_connection

class ProductVariant:
    """Product variant model"""
    
    def __init__(self, id=None, product_id=None, name=None, sku=None, barcode=None,
                 base_price=0.0, final_price=None, cost_price=0.0, is_active=True,
                 is_default=False, created_at=None, updated_at=None):
        self.id = id
        self.product_id = product_id
        self.name = name
        self.sku = sku
        self.barcode = barcode
        self.base_price = base_price
        self.final_price = final_price or base_price
        self.cost_price = cost_price
        self.is_active = is_active
        self.is_default = is_default
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = updated_at or self.created_at
    
    @staticmethod
    def get_by_id(variant_id):
        """Get variant by ID"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, product_id, name, sku, barcode, base_price, final_price,
                       cost_price, is_active, is_default, created_at, updated_at
                FROM product_variants
                WHERE id = ?
            """, (variant_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return ProductVariant(
                id=row[0],
                product_id=row[1],
                name=row[2],
                sku=row[3],
                barcode=row[4],
                base_price=row[5],
                final_price=row[6],
                cost_price=row[7],
                is_active=bool(row[8]),
                is_default=bool(row[9]),
                created_at=row[10],
                updated_at=row[11]
            )
        except Exception as e:
            print(f"Error getting variant by ID: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_by_product(product_id):
        """Get all variants for a product"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, product_id, name, sku, barcode, base_price, final_price,
                       cost_price, is_active, is_default, created_at, updated_at
                FROM product_variants
                WHERE product_id = ?
                ORDER BY is_default DESC, name
            """, (product_id,))
            
            variants = []
            for row in cursor.fetchall():
                variants.append(ProductVariant(
                    id=row[0],
                    product_id=row[1],
                    name=row[2],
                    sku=row[3],
                    barcode=row[4],
                    base_price=row[5],
                    final_price=row[6],
                    cost_price=row[7],
                    is_active=bool(row[8]),
                    is_default=bool(row[9]),
                    created_at=row[10],
                    updated_at=row[11]
                ))
            
            return variants
        except Exception as e:
            print(f"Error getting variants by product: {e}")
            return []
        finally:
            conn.close()
    
    def save(self):
        """Save variant to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.id:
                # Update existing variant
                cursor.execute("""
                    UPDATE product_variants
                    SET product_id = ?, name = ?, sku = ?, barcode = ?,
                        base_price = ?, final_price = ?, cost_price = ?,
                        is_active = ?, is_default = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    self.product_id, self.name, self.sku, self.barcode,
                    self.base_price, self.final_price, self.cost_price,
                    int(self.is_active), int(self.is_default), self.updated_at,
                    self.id
                ))
            else:
                # Insert new variant
                cursor.execute("""
                    INSERT INTO product_variants
                    (product_id, name, sku, barcode, base_price, final_price,
                     cost_price, is_active, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.product_id, self.name, self.sku, self.barcode,
                    self.base_price, self.final_price, self.cost_price,
                    int(self.is_active), int(self.is_default),
                    self.created_at, self.updated_at
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving variant: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete variant from database"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Delete associated inventory
            cursor.execute("DELETE FROM variant_inventory WHERE variant_id = ?", (self.id,))
            
            # Delete associated attribute values
            cursor.execute("DELETE FROM variant_attribute_values WHERE variant_id = ?", (self.id,))
            
            # Delete the variant
            cursor.execute("DELETE FROM product_variants WHERE id = ?", (self.id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting variant: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


class VariantAttributeValue:
    """Represents a specific attribute value for a variant"""
    
    def __init__(self, id=None, variant_id=None, attribute_type_id=None,
                 attribute_value_id=None, created_at=None):
        self.id = id
        self.variant_id = variant_id
        self.attribute_type_id = attribute_type_id
        self.attribute_value_id = attribute_value_id
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def get_by_variant(variant_id):
        """Get all attribute values for a variant"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, variant_id, attribute_type_id, attribute_value_id, created_at
                FROM variant_attribute_values
                WHERE variant_id = ?
            """, (variant_id,))
            
            values = []
            for row in cursor.fetchall():
                values.append(VariantAttributeValue(
                    id=row[0],
                    variant_id=row[1],
                    attribute_type_id=row[2],
                    attribute_value_id=row[3],
                    created_at=row[4]
                ))
            
            return values
        except Exception as e:
            print(f"Error getting variant attribute values: {e}")
            return []
        finally:
            conn.close()
    
    def save(self):
        """Save attribute value to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing value
                cursor.execute("""
                    UPDATE variant_attribute_values
                    SET variant_id = ?, attribute_type_id = ?, attribute_value_id = ?
                    WHERE id = ?
                """, (
                    self.variant_id, self.attribute_type_id, self.attribute_value_id,
                    self.id
                ))
            else:
                # Insert new value
                cursor.execute("""
                    INSERT INTO variant_attribute_values
                    (variant_id, attribute_type_id, attribute_value_id, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    self.variant_id, self.attribute_type_id, self.attribute_value_id,
                    self.created_at
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving variant attribute value: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


class VariantInventory:
    """Inventory information for a variant"""
    
    def __init__(self, id=None, variant_id=None, quantity=0, min_quantity=0,
                 updated_at=None):
        self.id = id
        self.variant_id = variant_id
        self.quantity = quantity
        self.min_quantity = min_quantity
        self.updated_at = updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def get_by_variant_id(variant_id):
        """Get inventory for a variant"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, variant_id, quantity, min_quantity, updated_at
                FROM variant_inventory
                WHERE variant_id = ?
            """, (variant_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return VariantInventory(
                id=row[0],
                variant_id=row[1],
                quantity=row[2],
                min_quantity=row[3],
                updated_at=row[4]
            )
        except Exception as e:
            print(f"Error getting variant inventory: {e}")
            return None
        finally:
            conn.close()
    
    def save(self):
        """Save inventory to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.id:
                # Update existing inventory
                cursor.execute("""
                    UPDATE variant_inventory
                    SET quantity = ?, min_quantity = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    self.quantity, self.min_quantity, self.updated_at,
                    self.id
                ))
            else:
                # Check if inventory already exists for this variant
                cursor.execute("SELECT id FROM variant_inventory WHERE variant_id = ?", (self.variant_id,))
                existing = cursor.fetchone()
                
                if existing:
                    self.id = existing[0]
                    cursor.execute("""
                        UPDATE variant_inventory
                        SET quantity = ?, min_quantity = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        self.quantity, self.min_quantity, self.updated_at,
                        self.id
                    ))
                else:
                    # Insert new inventory
                    cursor.execute("""
                        INSERT INTO variant_inventory
                        (variant_id, quantity, min_quantity, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        self.variant_id, self.quantity, self.min_quantity,
                        self.updated_at
                    ))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving variant inventory: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


def generate_variant_name(product_name, attributes):
    """Generate a name for a variant based on its attributes"""
    name_parts = [product_name]
    
    for attr_name, value_name in attributes.items():
        name_parts.append(f"{value_name}")
    
    return " - ".join(name_parts)


def generate_sku(product_name, attributes, product_id):
    """Generate a SKU for a variant"""
    # Clean product name for SKU
    product_code = re.sub(r'[^a-zA-Z0-9]', '', product_name)
    product_code = product_code[:4].upper()
    
    # Extract first few characters from each attribute value
    attr_codes = []
    for attr_name, value_name in attributes.items():
        value_code = re.sub(r'[^a-zA-Z0-9]', '', value_name)
        attr_codes.append(value_code[:3].upper())
    
    # Add product ID for uniqueness
    id_part = str(product_id).zfill(4)
    
    # Combine parts
    sku = f"{product_code}-{'-'.join(attr_codes)}-{id_part}"
    
    return sku


def generate_barcode():
    """Generate a random barcode"""
    return ''.join(random.choices(string.digits, k=13))


def generate_variants_for_product(product_id, base_price=0, cost_price=0):
    """
    Generate all possible variants for a product based on its attributes
    
    Args:
        product_id: Product ID
        base_price: Base price for the variants
        cost_price: Cost price for the variants
        
    Returns:
        List of generated variant IDs
    """
    from .attribute_manager import get_product_attributes_with_values
    
    try:
        # Get product info
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print(f"Product {product_id} not found")
            return []
        
        product_id, product_name = product
        
        # Get product attributes
        attributes = get_product_attributes_with_values(product_id)
        
        if not attributes:
            print(f"No attributes found for product {product_id}")
            return []
        
        # Prepare attribute values
        attr_values = {}
        for attr in attributes:
            attr_type_id = attr['type']['id']
            
            # Skip if no values
            if not attr['values']:
                continue
                
            attr_values[attr_type_id] = []
            for value in attr['values']:
                attr_value_id = value['attribute_value_id']
                attr_values[attr_type_id].append({
                    'id': attr_value_id,
                    'name': value['display_value'],
                    'price_adjustment': value['price_adjustment'],
                    'price_adjustment_type': value['price_adjustment_type']
                })
        
        # Generate all combinations
        combinations = []
        attr_types = list(attr_values.keys())
        
        def generate_combinations(index, current_combo):
            if index == len(attr_types):
                combinations.append(current_combo.copy())
                return
            
            attr_type_id = attr_types[index]
            for value in attr_values[attr_type_id]:
                current_combo[attr_type_id] = value
                generate_combinations(index + 1, current_combo)
        
        generate_combinations(0, {})
        
        # Create variants for each combination
        variant_ids = []
        
        for combo in combinations:
            # Generate variant info
            attr_display = {}
            price_adjustments = []
            attr_values_for_variant = []
            
            for attr_type_id, value in combo.items():
                attr_display[attributes[attr_types.index(attr_type_id)]['type']['name']] = value['name']
                
                # Add price adjustment
                price_adjustments.append({
                    'price_adjustment': value['price_adjustment'],
                    'price_adjustment_type': value['price_adjustment_type'] or 'fixed'
                })
                
                # Store for database
                attr_values_for_variant.append({
                    'type_id': attr_type_id,
                    'value_id': value['id']
                })
            
            # Calculate final price
            final_price = base_price
            for adj in price_adjustments:
                if adj['price_adjustment_type'] == 'fixed':
                    final_price += adj['price_adjustment']
                elif adj['price_adjustment_type'] == 'percentage':
                    final_price += (base_price * adj['price_adjustment'] / 100)
            
            # Create variant
            variant = ProductVariant(
                product_id=product_id,
                name=generate_variant_name(product_name, attr_display),
                sku=generate_sku(product_name, attr_display, product_id),
                barcode=generate_barcode(),
                base_price=base_price,
                final_price=final_price,
                cost_price=cost_price,
                is_default=(len(variant_ids) == 0)  # First variant is default
            )
            
            if variant.save():
                variant_ids.append(variant.id)
                
                # Save attribute values
                for attr_value in attr_values_for_variant:
                    vav = VariantAttributeValue(
                        variant_id=variant.id,
                        attribute_type_id=attr_value['type_id'],
                        attribute_value_id=attr_value['value_id']
                    )
                    vav.save()
                
                # Create inventory
                inventory = VariantInventory(
                    variant_id=variant.id,
                    quantity=0,
                    min_quantity=0
                )
                inventory.save()
        
        return variant_ids
    except Exception as e:
        print(f"Error generating variants: {e}")
        return []
    finally:
        if conn:
            conn.close()


def find_variant_by_attribute_values(product_id, attribute_values):
    """
    Find a variant that matches the given attribute values
    
    Args:
        product_id: Product ID
        attribute_values: Dictionary of attribute_type_id -> attribute_value_id
        
    Returns:
        Variant ID if found, None otherwise
    """
    try:
        # Get all variants for the product
        variants = ProductVariant.get_by_product(product_id)
        
        for variant in variants:
            # Get attribute values for this variant
            variant_attrs = VariantAttributeValue.get_by_variant(variant.id)
            
            # Convert to dictionary for easy comparison
            variant_attr_dict = {}
            for attr in variant_attrs:
                variant_attr_dict[attr.attribute_type_id] = attr.attribute_value_id
            
            # Check if all requested attributes match
            match = True
            for attr_type_id, attr_value_id in attribute_values.items():
                if (attr_type_id not in variant_attr_dict or 
                    variant_attr_dict[attr_type_id] != attr_value_id):
                    match = False
                    break
            
            if match:
                return variant.id
        
        return None
    except Exception as e:
        print(f"Error finding variant: {e}")
        return None


def get_variant_with_attributes(variant_id):
    """
    Get a variant with its attributes and inventory
    
    Args:
        variant_id: Variant ID
        
    Returns:
        Dictionary with variant info, attributes, and inventory
    """
    try:
        # Get variant
        variant = ProductVariant.get_by_id(variant_id)
        if not variant:
            return None
        
        # Get variant attributes
        variant_attrs = VariantAttributeValue.get_by_variant(variant_id)
        
        # Get attribute details
        from .attribute_manager import AttributeType, AttributeValue
        
        attributes = {}
        for attr in variant_attrs:
            attr_type = AttributeType.get_by_id(attr.attribute_type_id)
            attr_value = AttributeValue.get_by_id(attr.attribute_value_id)
            
            if attr_type and attr_value:
                attributes[attr.attribute_type_id] = {
                    'type_id': attr.attribute_type_id,
                    'type_name': attr_type.name,
                    'type_display_name': attr_type.display_name,
                    'value_id': attr.attribute_value_id,
                    'value': attr_value.value,
                    'display_value': attr_value.display_value
                }
        
        # Get inventory
        inventory = VariantInventory.get_by_variant_id(variant_id)
        
        # Create result
        result = {
            'id': variant.id,
            'product_id': variant.product_id,
            'name': variant.name,
            'sku': variant.sku,
            'barcode': variant.barcode,
            'base_price': variant.base_price,
            'final_price': variant.final_price,
            'cost_price': variant.cost_price,
            'is_active': variant.is_active,
            'is_default': variant.is_default,
            'created_at': variant.created_at,
            'updated_at': variant.updated_at,
            'attributes': attributes,
            'inventory': inventory.__dict__ if inventory else None
        }
        
        return result
    except Exception as e:
        print(f"Error getting variant with attributes: {e}")
        return None


def calculate_variant_price(product_id, attr_value_ids):
    """
    Calculate the price for a specific combination of attribute values
    
    Args:
        product_id: Product ID
        attr_value_ids: List of attribute value IDs
        
    Returns:
        Dictionary with base_price, adjustment_amount, final_price
    """
    try:
        # Get product base price
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute("SELECT unit_price FROM Products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return None
        
        base_price = product[0] or 0
        
        # Get price adjustments for attribute values
        from .attribute_manager import (
            ProductAttribute, ProductAttributeValue, AttributeValue
        )
        
        # Find all product attributes for this product
        product_attrs = ProductAttribute.get_by_product(product_id)
        
        # Get all price adjustments
        adjustments = []
        for attr in product_attrs:
            # Get attribute values
            attr_values = attr.values
            
            # Find values that match the requested ones
            for attr_value in attr_values:
                if attr_value.attribute_value_id in attr_value_ids:
                    adjustments.append({
                        'price_adjustment': attr_value.price_adjustment,
                        'price_adjustment_type': attr_value.price_adjustment_type or 'fixed'
                    })
        
        # Calculate final price
        total_adjustment = 0
        for adj in adjustments:
            if adj['price_adjustment_type'] == 'fixed':
                total_adjustment += adj['price_adjustment']
            elif adj['price_adjustment_type'] == 'percentage':
                total_adjustment += (base_price * adj['price_adjustment'] / 100)
        
        return {
            'base_price': base_price,
            'adjustment_amount': total_adjustment,
            'final_price': base_price + total_adjustment
        }
    except Exception as e:
        print(f"Error calculating variant price: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_variant_inventory(variant_id, quantity_change):
    """
    Update inventory for a variant
    
    Args:
        variant_id: Variant ID
        quantity_change: Amount to change quantity by (positive or negative)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current inventory
        inventory = VariantInventory.get_by_variant_id(variant_id)
        
        if not inventory:
            # Create new inventory
            inventory = VariantInventory(
                variant_id=variant_id,
                quantity=max(0, quantity_change),
                min_quantity=0
            )
        else:
            # Update quantity
            inventory.quantity = max(0, inventory.quantity + quantity_change)
        
        # Save changes
        return inventory.save()
    except Exception as e:
        print(f"Error updating variant inventory: {e}")
        return False
