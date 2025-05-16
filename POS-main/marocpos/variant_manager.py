"""
Variant Manager Module

This module provides functions for generating, managing, and calculating prices for
product variants with multiple attributes and price adjustments.
"""

from database import get_connection
import json
import time
import random

def create_variant_for_product(product_id, attribute_values, price_adjustment=0, sku=None, barcode=None, name=None, stock=0):
    """
    Create a new variant for a product with specific attribute values
    
    Args:
        product_id: The ID of the base product
        attribute_values: Dict mapping attribute names to values 
            (e.g., {'Color': 'Red', 'Size': 'XL'})
        price_adjustment: Additional price adjustment specific to this variant
        sku: The SKU code (if None, will be auto-generated)
        barcode: The barcode (if None, will be auto-generated)
        name: The variant name (if None, will be auto-generated)
        stock: Initial stock quantity
        
    Returns:
        ID of the created variant or None if failed
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        # Get product base information
        cursor.execute("SELECT name, unit_price, purchase_price FROM Products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            print(f"Product {product_id} not found")
            cursor.execute("ROLLBACK")
            return None
        
        base_name = product['name']
        base_price = product['unit_price']
        base_purchase_price = product['purchase_price']
        
        # Generate variant name if not provided
        if not name:
            variant_parts = [base_name]
            for attr, value in attribute_values.items():
                variant_parts.append(str(value))
            name = " / ".join(variant_parts)
        
        # Generate SKU if not provided
        if not sku:
            sku_parts = []
            for attr, value in attribute_values.items():
                # Clean up attribute name and value for SKU
                attr_prefix = attr[0].upper()
                clean_value = ''.join(c for c in value if c.isalnum())
                value_part = clean_value.upper() if len(clean_value) <= 4 else clean_value[:4].upper()
                sku_parts.append(f"{attr_prefix}{value_part}")
                
            # Add timestamp for uniqueness
            timestamp = str(int(time.time() * 1000))[-4:]
            sku = f"SKU-{base_name[:3].upper()}-{''.join(sku_parts)}-{timestamp}"
        
        # Generate barcode if not provided
        if not barcode:
            barcode = f"{int(time.time())}{random.randint(1000, 9999)}"
        
        # Insert the variant
        cursor.execute("""
            INSERT INTO ProductVariants (
                product_id, name, sku, barcode, unit_price, purchase_price, stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id, 
            name, 
            sku,
            barcode, 
            base_price + price_adjustment,
            base_purchase_price,
            stock
        ))
        variant_id = cursor.lastrowid
        
        # Associate variant with attribute values
        for attr_name, attr_value in attribute_values.items():
            # Get attribute ID
            cursor.execute("SELECT id FROM ProductAttributes WHERE name = ?", (attr_name,))
            attribute = cursor.fetchone()
            if not attribute:
                print(f"Attribute {attr_name} not found")
                continue
                
            attribute_id = attribute['id']
            
            # Get attribute line
            cursor.execute("""
                SELECT id FROM ProductTemplateAttributeLine
                WHERE product_id = ? AND attribute_id = ?
            """, (product_id, attribute_id))
            line = cursor.fetchone()
            if not line:
                print(f"Attribute line for {attr_name} not found")
                continue
                
            line_id = line['id']
            
            # Get value ID
            cursor.execute("""
                SELECT id FROM ProductAttributeValues
                WHERE attribute_id = ? AND value = ?
            """, (attribute_id, attr_value))
            value = cursor.fetchone()
            if not value:
                print(f"Attribute value {attr_value} for {attr_name} not found")
                continue
                
            value_id = value['id']
            
            # Get template attribute value
            cursor.execute("""
                SELECT id FROM ProductTemplateAttributeValue
                WHERE line_id = ? AND value_id = ?
            """, (line_id, value_id))
            template_value = cursor.fetchone()
            if not template_value:
                print(f"Template value for {attr_name}={attr_value} not found")
                continue
                
            template_value_id = template_value['id']
            
            # Create variant combination
            cursor.execute("""
                INSERT INTO ProductVariantCombination (
                    product_id, product_variant_id, template_attribute_value_id
                ) VALUES (?, ?, ?)
            """, (product_id, variant_id, template_value_id))
        
        cursor.execute("COMMIT")
        return variant_id
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error creating variant: {e}")
        return None
    finally:
        conn.close()

def get_variant_by_attributes(product_id, attribute_values):
    """
    Find a variant by its specific attribute values
    
    Args:
        product_id: The product ID
        attribute_values: Dict mapping attribute names to values
            (e.g., {'Color': 'Red', 'Size': 'XL'})
    
    Returns:
        The variant info if found, otherwise None
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get all attribute value IDs for the attribute value pairs
        attr_value_ids = []
        
        for attr_name, attr_value in attribute_values.items():
            cursor.execute("""
                SELECT pav.id
                FROM ProductAttributeValues pav
                JOIN ProductAttributes pa ON pav.attribute_id = pa.id
                WHERE pa.name = ? AND pav.value = ?
            """, (attr_name, attr_value))
            
            result = cursor.fetchone()
            if not result:
                print(f"Attribute value not found: {attr_name}={attr_value}")
                return None
                
            attr_value_ids.append(result['id'])
        
        # Get template attribute value IDs for the product
        template_value_ids = []
        
        for value_id in attr_value_ids:
            cursor.execute("""
                SELECT ptav.id
                FROM ProductTemplateAttributeValue ptav
                JOIN ProductTemplateAttributeLine ptal ON ptav.line_id = ptal.id
                WHERE ptal.product_id = ? AND ptav.value_id = ?
            """, (product_id, value_id))
            
            result = cursor.fetchone()
            if not result:
                print(f"Template attribute value not found for product {product_id}, value_id {value_id}")
                return None
                
            template_value_ids.append(result['id'])
        
        # Find variants that have all the specified template value IDs
        variant_counts = {}
        
        for template_value_id in template_value_ids:
            cursor.execute("""
                SELECT pvc.product_variant_id, COUNT(pvc.id) as count
                FROM ProductVariantCombination pvc
                WHERE pvc.product_id = ? AND pvc.template_attribute_value_id = ?
                GROUP BY pvc.product_variant_id
            """, (product_id, template_value_id))
            
            for row in cursor.fetchall():
                variant_id = row['product_variant_id']
                if variant_id not in variant_counts:
                    variant_counts[variant_id] = 0
                variant_counts[variant_id] += 1
        
        # Find any variant that has all the template values
        matching_variants = []
        for variant_id, count in variant_counts.items():
            if count == len(template_value_ids):
                matching_variants.append(variant_id)
        
        if not matching_variants:
            print(f"No variant found with attribute values: {attribute_values}")
            return None
        
        # Get full variant information
        cursor.execute("SELECT * FROM ProductVariants WHERE id = ?", (matching_variants[0],))
        variant = cursor.fetchone()
        
        if variant:
            # Convert to dictionary
            return dict(variant)
        
        return None
    except Exception as e:
        print(f"Error finding variant by attributes: {e}")
        return None
    finally:
        conn.close()

def generate_all_variants_for_product(product_id):
    """
    Generate all possible variants for a product based on its attributes and attribute values
    
    Args:
        product_id: The product ID
    
    Returns:
        List of generated variant IDs or empty list if failed
    """
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        # Get product base information
        cursor.execute("SELECT name, unit_price, purchase_price FROM Products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            print(f"Product {product_id} not found")
            cursor.execute("ROLLBACK")
            return []
        
        base_name = product['name']
        base_price = product['unit_price']
        base_purchase_price = product['purchase_price']
        
        # Get all attribute lines with their values
        cursor.execute("""
            SELECT 
                ptal.id as line_id,
                pa.id as attribute_id, 
                pa.name as attribute_name
            FROM ProductTemplateAttributeLine ptal
            JOIN ProductAttributes pa ON ptal.attribute_id = pa.id
            WHERE ptal.product_id = ?
        """, (product_id,))
        
        attribute_lines = cursor.fetchall()
        if not attribute_lines:
            print(f"No attributes found for product {product_id}")
            cursor.execute("ROLLBACK")
            return []
        
        # Get all possible values for each attribute line
        attribute_values = {}
        
        for line in attribute_lines:
            cursor.execute("""
                SELECT 
                    ptav.id as template_value_id,
                    pav.id as value_id,
                    pav.value,
                    ptav.price_extra
                FROM ProductTemplateAttributeValue ptav
                JOIN ProductAttributeValues pav ON ptav.value_id = pav.id
                WHERE ptav.line_id = ?
            """, (line['line_id'],))
            
            values = cursor.fetchall()
            if not values:
                print(f"No values found for attribute line {line['line_id']}")
                continue
                
            attribute_name = line['attribute_name']
            attribute_values[attribute_name] = {
                'attribute_id': line['attribute_id'],
                'line_id': line['line_id'],
                'values': values
            }
        
        # Generate all possible combinations
        combinations = generate_attribute_combinations(attribute_values)
        
        # Create variants for all combinations
        variant_ids = []
        
        for combo in combinations:
            attr_values = combo['attribute_values']
            price_extra = combo['price_extra']
            
            # Generate variant name
            variant_parts = [base_name]
            for attr, value in attr_values.items():
                variant_parts.append(value)
            variant_name = " / ".join(variant_parts)
            
            # Generate SKU
            sku_parts = []
            for attr, value in attr_values.items():
                attr_prefix = attr[0].upper()
                clean_value = ''.join(c for c in value if c.isalnum())
                value_part = clean_value.upper() if len(clean_value) <= 4 else clean_value[:4].upper()
                sku_parts.append(f"{attr_prefix}{value_part}")
            
            timestamp = str(int(time.time() * 1000))[-4:]
            sku = f"SKU-{base_name[:3].upper()}-{''.join(sku_parts)}-{timestamp}"
            
            # Generate barcode
            barcode = f"{int(time.time())}{random.randint(1000, 9999)}"
            
            # Insert variant
            cursor.execute("""
                INSERT INTO ProductVariants (
                    product_id, name, sku, barcode, 
                    unit_price, purchase_price, stock
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                variant_name,
                sku,
                barcode,
                base_price + price_extra,
                base_purchase_price,
                0  # Initial stock is 0
            ))
            
            variant_id = cursor.lastrowid
            variant_ids.append(variant_id)
            
            # Add combinations for this variant
            for template_value_id in combo['template_value_ids']:
                cursor.execute("""
                    INSERT INTO ProductVariantCombination (
                        product_id, product_variant_id, template_attribute_value_id
                    ) VALUES (?, ?, ?)
                """, (product_id, variant_id, template_value_id))
            
            # Wait a little to ensure unique timestamps for SKUs
            time.sleep(0.01)
        
        cursor.execute("COMMIT")
        return variant_ids
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error generating variants: {e}")
        return []
    finally:
        conn.close()

def generate_attribute_combinations(attribute_values):
    """
    Generate all possible combinations of attribute values
    
    Args:
        attribute_values: Dict mapping attribute names to dict of attribute info and values
        
    Returns:
        List of combinations, each with attribute_values, template_value_ids, and price_extra
    """
    combinations = []
    
    def generate_combinations_recursive(attrs, index=0, current=None):
        if current is None:
            current = {
                'attribute_values': {},
                'template_value_ids': [],
                'price_extra': 0
            }
        
        # If we've processed all attributes, add the combination
        attr_names = list(attrs.keys())
        if index >= len(attr_names):
            combinations.append(current.copy())
            return
        
        # Get the current attribute and its values
        attr_name = attr_names[index]
        attr_info = attrs[attr_name]
        
        # Try each value for this attribute
        for value in attr_info['values']:
            # Create a new combination with this attribute value
            new_combination = current.copy()
            new_combination['attribute_values'] = current['attribute_values'].copy()
            new_combination['template_value_ids'] = current['template_value_ids'].copy()
            
            # Add this attribute value
            new_combination['attribute_values'][attr_name] = value['value']
            new_combination['template_value_ids'].append(value['template_value_id'])
            new_combination['price_extra'] += value['price_extra']
            
            # Continue with the next attribute
            generate_combinations_recursive(attrs, index + 1, new_combination)
    
    # Start the recursive generation
    generate_combinations_recursive(attribute_values)
    return combinations

def get_variant_price_with_extras(variant_id):
    """
    Calculate the full price for a variant including all price extras
    
    Args:
        variant_id: The variant ID
        
    Returns:
        The calculated price
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get base price and variant price
        cursor.execute("""
            SELECT 
                v.id, v.unit_price as variant_price,
                p.unit_price as base_price 
            FROM ProductVariants v
            JOIN Products p ON v.product_id = p.id
            WHERE v.id = ?
        """, (variant_id,))
        
        price_info = cursor.fetchone()
        if not price_info:
            return None
        
        # If variant has its own price defined, use that
        if price_info['variant_price'] and price_info['variant_price'] > 0:
            return price_info['variant_price']
        
        # Otherwise calculate price from attributes
        base_price = price_info['base_price']
        
        # Get price extras from template attribute values
        cursor.execute("""
            SELECT SUM(ptav.price_extra) as total_extra
            FROM ProductVariantCombination pvc
            JOIN ProductTemplateAttributeValue ptav ON pvc.template_attribute_value_id = ptav.id
            WHERE pvc.product_variant_id = ?
        """, (variant_id,))
        
        extras = cursor.fetchone()
        price_extra = extras['total_extra'] if extras and extras['total_extra'] else 0
        
        return base_price + price_extra
    except Exception as e:
        print(f"Error calculating variant price: {e}")
        return None
    finally:
        conn.close()

def get_variant_attributes(variant_id):
    """
    Get all attributes and their values for a variant
    
    Args:
        variant_id: The variant ID
        
    Returns:
        Dict mapping attribute names to their values
    """
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                pa.name as attribute_name,
                pav.value as attribute_value,
                ptav.price_extra
            FROM ProductVariantCombination pvc
            JOIN ProductTemplateAttributeValue ptav ON pvc.template_attribute_value_id = ptav.id
            JOIN ProductTemplateAttributeLine ptal ON ptav.line_id = ptal.id
            JOIN ProductAttributes pa ON ptal.attribute_id = pa.id
            JOIN ProductAttributeValues pav ON ptav.value_id = pav.id
            WHERE pvc.product_variant_id = ?
        """, (variant_id,))
        
        attributes = {}
        for row in cursor.fetchall():
            attributes[row['attribute_name']] = row['attribute_value']
        
        return attributes
    except Exception as e:
        print(f"Error getting variant attributes: {e}")
        return {}
    finally:
        conn.close()
