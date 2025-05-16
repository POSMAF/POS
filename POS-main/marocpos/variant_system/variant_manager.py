"""
Variant Manager Module

This module provides classes and functions for managing product variants,
including generation, pricing, and inventory management.
"""

from database import get_connection
import json
import time
import random
import itertools
from .attribute_manager import get_product_attributes_with_values

class ProductVariant:
    """Class representing a product variant"""
    
    def __init__(self, id=None, product_id=None, sku=None, barcode=None, name=None,
                 description=None, image_path=None, base_price=None, final_price=None,
                 cost_price=None, weight=None, dimensions=None, is_active=True,
                 is_default=False, created_at=None, updated_at=None):
        self.id = id
        self.product_id = product_id
        self.sku = sku
        self.barcode = barcode
        self.name = name
        self.description = description
        self.image_path = image_path
        self.base_price = base_price
        self.final_price = final_price
        self.cost_price = cost_price
        self.weight = weight
        self.dimensions = dimensions
        self.is_active = is_active
        self.is_default = is_default
        self.created_at = created_at
        self.updated_at = updated_at
        self._attribute_values = None
        self._inventory = None
    
    @property
    def attribute_values(self):
        """Get variant attribute values (lazy loaded)"""
        if self._attribute_values is None and self.id:
            self._attribute_values = VariantAttributeValue.get_by_variant_id(self.id)
        return self._attribute_values
    
    @property
    def inventory(self):
        """Get variant inventory (lazy loaded)"""
        if self._inventory is None and self.id:
            self._inventory = VariantInventory.get_by_variant_id(self.id)
        return self._inventory
    
    def to_dict(self, include_attributes=False, include_inventory=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'product_id': self.product_id,
            'sku': self.sku,
            'barcode': self.barcode,
            'name': self.name,
            'description': self.description,
            'image_path': self.image_path,
            'base_price': self.base_price,
            'final_price': self.final_price,
            'cost_price': self.cost_price,
            'weight': self.weight,
            'dimensions': self.dimensions,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_attributes:
            result['attribute_values'] = [av.to_dict() for av in self.attribute_values]
        
        if include_inventory and self.inventory:
            result['inventory'] = self.inventory.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            product_id=data.get('product_id'),
            sku=data.get('sku'),
            barcode=data.get('barcode'),
            name=data.get('name'),
            description=data.get('description'),
            image_path=data.get('image_path'),
            base_price=data.get('base_price'),
            final_price=data.get('final_price'),
            cost_price=data.get('cost_price'),
            weight=data.get('weight'),
            dimensions=data.get('dimensions'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_by_id(cls, id):
        """Get product variant by ID"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ProductVariants WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting product variant by ID: {e}")
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_by_product(cls, product_id, active_only=True):
        """Get all variants for a product"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM ProductVariants WHERE product_id = ?"
            params = [product_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [cls.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Error getting product variants: {e}")
            return []
        finally:
            conn.close()
    
    @classmethod
    def get_by_sku(cls, sku):
        """Get product variant by SKU"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ProductVariants WHERE sku = ?", (sku,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting product variant by SKU: {e}")
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_by_barcode(cls, barcode):
        """Get product variant by barcode"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ProductVariants WHERE barcode = ?", (barcode,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting product variant by barcode: {e}")
            return None
        finally:
            conn.close()
    
    @classmethod
    def find_by_attributes(cls, product_id, attribute_values):
        """
        Find a variant by its attribute values
        
        Args:
            product_id: The product ID
            attribute_values: Dict mapping attribute value IDs to attribute type IDs
                e.g., {12: 1, 25: 2} where 12 and 25 are AttributeValue IDs
        
        Returns:
            The matching variant or None
        """
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Get variants for this product
            variants = cls.get_by_product(product_id)
            
            # For each variant, check if it matches all attribute values
            for variant in variants:
                # Get attribute values for this variant
                variant_attr_values = VariantAttributeValue.get_by_variant_id(variant.id)
                
                # Check if this variant has all the specified attribute values
                attr_value_ids = [av.attribute_value_id for av in variant_attr_values]
                if all(av_id in attr_value_ids for av_id in attribute_values.keys()):
                    return variant
            
            return None
        except Exception as e:
            print(f"Error finding variant by attributes: {e}")
            return None
        finally:
            conn.close()
    
    def save(self):
        """Save product variant to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE ProductVariants 
                    SET product_id = ?, sku = ?, barcode = ?, name = ?,
                        description = ?, image_path = ?, base_price = ?,
                        final_price = ?, cost_price = ?, weight = ?,
                        dimensions = ?, is_active = ?, is_default = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.product_id, self.sku, self.barcode, self.name,
                    self.description, self.image_path, self.base_price,
                    self.final_price, self.cost_price, self.weight,
                    self.dimensions, self.is_active, self.is_default,
                    self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO ProductVariants 
                    (product_id, sku, barcode, name, description, image_path,
                     base_price, final_price, cost_price, weight, dimensions,
                     is_active, is_default)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.product_id, self.sku, self.barcode, self.name,
                    self.description, self.image_path, self.base_price,
                    self.final_price, self.cost_price, self.weight,
                    self.dimensions, self.is_active, self.is_default
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving product variant: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete product variant"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ProductVariants WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting product variant: {e}")
            return False
        finally:
            conn.close()


class VariantAttributeValue:
    """Class linking a variant to attribute values"""
    
    def __init__(self, id=None, variant_id=None, attribute_value_id=None, created_at=None):
        self.id = id
        self.variant_id = variant_id
        self.attribute_value_id = attribute_value_id
        self.created_at = created_at
        self._attribute_value = None
    
    @property
    def attribute_value(self):
        """Get the attribute value (lazy loaded)"""
        if self._attribute_value is None and self.attribute_value_id:
            # Import inside method to avoid circular imports
            from .attribute_manager import AttributeValue
            self._attribute_value = AttributeValue.get_by_id(self.attribute_value_id)
        return self._attribute_value
    
    def to_dict(self, include_attribute_value=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'variant_id': self.variant_id,
            'attribute_value_id': self.attribute_value_id,
            'created_at': self.created_at
        }
        
        if include_attribute_value and self.attribute_value:
            result['attribute_value'] = self.attribute_value.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            variant_id=data.get('variant_id'),
            attribute_value_id=data.get('attribute_value_id'),
            created_at=data.get('created_at')
        )
    
    @classmethod
    def get_by_variant_id(cls, variant_id):
        """Get all attribute values for a variant"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT vav.*, av.value, av.display_value, at.name as attribute_name
                FROM VariantAttributeValues vav
                JOIN AttributeValues av ON vav.attribute_value_id = av.id
                JOIN AttributeTypes at ON av.attribute_type_id = at.id
                WHERE vav.variant_id = ?
            """, (variant_id,))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                variant_attr_value = cls.from_dict(dict(row))
                
                # Import inside method to avoid circular imports
                from .attribute_manager import AttributeValue
                # Create and attach AttributeValue
                attr_value = AttributeValue(
                    id=row['attribute_value_id'],
                    value=row['value'],
                    display_value=row['display_value'],
                    attribute_type_id=None  # We don't have this in the query
                )
                variant_attr_value._attribute_value = attr_value
                
                result.append(variant_attr_value)
            
            return result
        except Exception as e:
            print(f"Error getting variant attribute values: {e}")
            return []
        finally:
            conn.close()
    
    def save(self):
        """Save variant attribute value to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE VariantAttributeValues 
                    SET variant_id = ?, attribute_value_id = ?
                    WHERE id = ?
                """, (
                    self.variant_id, self.attribute_value_id,
                    self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO VariantAttributeValues 
                    (variant_id, attribute_value_id)
                    VALUES (?, ?)
                """, (
                    self.variant_id, self.attribute_value_id
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving variant attribute value: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete variant attribute value"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM VariantAttributeValues WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting variant attribute value: {e}")
            return False
        finally:
            conn.close()


class VariantInventory:
    """Class representing inventory for a variant"""
    
    def __init__(self, id=None, variant_id=None, quantity=0, reserved_quantity=0,
                 reorder_level=0, reorder_quantity=0, location=None,
                 last_counted_at=None, created_at=None, updated_at=None):
        self.id = id
        self.variant_id = variant_id
        self.quantity = quantity
        self.reserved_quantity = reserved_quantity
        self.reorder_level = reorder_level
        self.reorder_quantity = reorder_quantity
        self.location = location
        self.last_counted_at = last_counted_at
        self.created_at = created_at
        self.updated_at = updated_at
    
    @property
    def available_quantity(self):
        """Get available quantity (total - reserved)"""
        return max(0, self.quantity - self.reserved_quantity)
    
    @property
    def needs_reorder(self):
        """Check if variant needs reordering"""
        return self.quantity <= self.reorder_level
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'reorder_level': self.reorder_level,
            'reorder_quantity': self.reorder_quantity,
            'location': self.location,
            'needs_reorder': self.needs_reorder,
            'last_counted_at': self.last_counted_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            variant_id=data.get('variant_id'),
            quantity=data.get('quantity', 0),
            reserved_quantity=data.get('reserved_quantity', 0),
            reorder_level=data.get('reorder_level', 0),
            reorder_quantity=data.get('reorder_quantity', 0),
            location=data.get('location'),
            last_counted_at=data.get('last_counted_at'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_by_variant_id(cls, variant_id):
        """Get inventory for a variant"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM VariantInventory WHERE variant_id = ?", (variant_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting variant inventory: {e}")
            return None
        finally:
            conn.close()
    
    def save(self):
        """Save variant inventory to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE VariantInventory 
                    SET variant_id = ?, quantity = ?, reserved_quantity = ?,
                        reorder_level = ?, reorder_quantity = ?, location = ?,
                        last_counted_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.variant_id, self.quantity, self.reserved_quantity,
                    self.reorder_level, self.reorder_quantity, self.location,
                    self.last_counted_at, self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO VariantInventory 
                    (variant_id, quantity, reserved_quantity, reorder_level,
                     reorder_quantity, location, last_counted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.variant_id, self.quantity, self.reserved_quantity,
                    self.reorder_level, self.reorder_quantity, self.location,
                    self.last_counted_at
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving variant inventory: {e}")
            return False
        finally:
            conn.close()
    
    def adjust_quantity(self, amount, movement_type='adjustment', reference_id=None, notes=None, user_id=None):
        """
        Adjust inventory quantity and record movement
        
        Args:
            amount: Amount to adjust (positive or negative)
            movement_type: Type of movement (purchase, sale, adjustment, transfer, return)
            reference_id: ID of related document (purchase, sale, etc)
            notes: Notes about the adjustment
            user_id: User performing the adjustment
            
        Returns:
            Success status
        """
        if not self.id or not self.variant_id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Update inventory
            new_quantity = self.quantity + amount
            if new_quantity < 0:
                new_quantity = 0
                
            cursor.execute("""
                UPDATE VariantInventory 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_quantity, self.id))
            
            # Record movement
            cursor.execute("""
                INSERT INTO InventoryMovements 
                (variant_id, quantity, movement_type, reference_id, notes, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.variant_id, amount, movement_type, reference_id, notes, user_id))
            
            # Update object
            self.quantity = new_quantity
            
            # Commit transaction
            cursor.execute("COMMIT")
            return True
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Error adjusting inventory: {e}")
            return False
        finally:
            conn.close()
    
    def reserve_quantity(self, amount):
        """
        Reserve inventory quantity (e.g., for a pending sale)
        
        Args:
            amount: Amount to reserve
            
        Returns:
            Success status
        """
        if not self.id:
            return False
        
        # Check if enough quantity is available
        if amount > self.available_quantity:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            new_reserved = self.reserved_quantity + amount
            
            cursor.execute("""
                UPDATE VariantInventory 
                SET reserved_quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_reserved, self.id))
            
            # Update object
            self.reserved_quantity = new_reserved
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error reserving inventory: {e}")
            return False
        finally:
            conn.close()
    
    def release_reserved_quantity(self, amount):
        """
        Release previously reserved inventory quantity
        
        Args:
            amount: Amount to release
            
        Returns:
            Success status
        """
        if not self.id:
            return False
        
        if amount > self.reserved_quantity:
            amount = self.reserved_quantity
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            new_reserved = self.reserved_quantity - amount
            
            cursor.execute("""
                UPDATE VariantInventory 
                SET reserved_quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_reserved, self.id))
            
            # Update object
            self.reserved_quantity = new_reserved
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error releasing reserved inventory: {e}")
            return False
        finally:
            conn.close()


def generate_variants_for_product(product_id, base_price=None, cost_price=None):
    """
    Generate all possible variant combinations for a product
    
    Args:
        product_id: The product ID
        base_price: Base price for variants (if None, uses product price)
        cost_price: Cost price for variants (if None, uses product cost)
        
    Returns:
        List of created variant IDs
    """
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Get product info
        cursor.execute("""
            SELECT name, unit_price, purchase_price 
            FROM Products 
            WHERE id = ?
        """, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print(f"Product {product_id} not found")
            cursor.execute("ROLLBACK")
            return []
        
        product_name = product['name']
        product_base_price = product['unit_price'] or 0
        product_cost_price = product['purchase_price'] or 0
        
        if base_price is None:
            base_price = product_base_price
        if cost_price is None:
            cost_price = product_cost_price
        
        # Get product attributes with values
        attr_data = get_product_attributes_with_values(product_id)
        
        if not attr_data:
            print(f"No attributes found for product {product_id}")
            cursor.execute("ROLLBACK")
            return []
        
        # Prepare data for combinations
        attr_combinations = []
        
        for attr in attr_data:
            # Skip if no values
            if not attr['values']:
                continue
                
            # Extract values
            values = []
            for val in attr['values']:
                values.append({
                    'attr_type_id': attr['type']['id'],
                    'attr_type_name': attr['type']['name'],
                    'attr_value_id': val['attribute_value_id'],
                    'attr_value': val['value'],
                    'display_value': val['display_value'],
                    'price_adjustment': val['price_adjustment'],
                    'price_adjustment_type': val['price_adjustment_type']
                })
            
            attr_combinations.append(values)
        
        if not attr_combinations:
            print(f"No valid attributes with values found for product {product_id}")
            cursor.execute("ROLLBACK")
            return []
        
        # Generate all combinations
        all_combinations = list(itertools.product(*attr_combinations))
        
        # Create variants for each combination
        variant_ids = []
        
        for combination in all_combinations:
            # Calculate price adjustments
            price_adjustment = 0
            for attr in combination:
                if attr['price_adjustment_type'] == 'fixed':
                    price_adjustment += attr['price_adjustment']
                elif attr['price_adjustment_type'] == 'percentage':
                    price_adjustment += (base_price * attr['price_adjustment'] / 100)
            
            # Create name
            variant_name_parts = [product_name]
            attr_value_parts = []
            
            for attr in combination:
                attr_value_parts.append(attr['display_value'])
            
            variant_name = f"{product_name} ({', '.join(attr_value_parts)})"
            
            # Generate SKU
            timestamp = str(int(time.time() * 10000))[-4:]
            sku_values = [attr['attr_value'].upper()[:3] for attr in combination]
            sku = f"{product_name[:3].upper()}-{''.join(sku_values)}-{timestamp}"
            
            # Generate barcode
            barcode = f"{int(time.time())}{random.randint(1000, 9999)}"
            
            # Create variant
            cursor.execute("""
                INSERT INTO ProductVariants 
                (product_id, sku, barcode, name, base_price, final_price, cost_price, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                product_id, sku, barcode, variant_name, 
                base_price, base_price + price_adjustment, cost_price
            ))
            
            variant_id = cursor.lastrowid
            variant_ids.append(variant_id)
            
            # Add attribute values to variant
            for attr in combination:
                cursor.execute("""
                    INSERT INTO VariantAttributeValues 
                    (variant_id, attribute_value_id)
                    VALUES (?, ?)
                """, (variant_id, attr['attr_value_id']))
            
            # Create inventory record
            cursor.execute("""
                INSERT INTO VariantInventory 
                (variant_id, quantity, reserved_quantity)
                VALUES (?, 0, 0)
            """, (variant_id,))
        
        # Commit transaction
        cursor.execute("COMMIT")
        return variant_ids
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error generating variants: {e}")
        return []
    finally:
        conn.close()


def get_variant_with_attributes(variant_id):
    """
    Get a variant with its attribute values
    
    Args:
        variant_id: The variant ID
        
    Returns:
        Dictionary with variant info and attributes
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get variant
        cursor.execute("SELECT * FROM ProductVariants WHERE id = ?", (variant_id,))
        variant_row = cursor.fetchone()
        
        if not variant_row:
            return None
        
        variant = dict(variant_row)
        
        # Get attribute values
        cursor.execute("""
            SELECT 
                vav.attribute_value_id,
                av.value,
                av.display_value,
                at.id as attribute_type_id,
                at.name as attribute_type_name,
                at.display_name as attribute_type_display_name
            FROM VariantAttributeValues vav
            JOIN AttributeValues av ON vav.attribute_value_id = av.id
            JOIN AttributeTypes at ON av.attribute_type_id = at.id
            WHERE vav.variant_id = ?
        """, (variant_id,))
        
        attribute_rows = cursor.fetchall()
        
        # Get inventory
        cursor.execute("SELECT * FROM VariantInventory WHERE variant_id = ?", (variant_id,))
        inventory_row = cursor.fetchone()
        
        # Format result
        result = {
            'id': variant['id'],
            'product_id': variant['product_id'],
            'sku': variant['sku'],
            'barcode': variant['barcode'],
            'name': variant['name'],
            'description': variant['description'],
            'image_path': variant['image_path'],
            'base_price': variant['base_price'],
            'final_price': variant['final_price'],
            'cost_price': variant['cost_price'],
            'is_active': variant['is_active'],
            'is_default': variant['is_default'],
            'created_at': variant['created_at'],
            'updated_at': variant['updated_at'],
            'attributes': {},
            'inventory': None
        }
        
        # Format attributes
        for attr in attribute_rows:
            attr_dict = dict(attr)
            attr_type_id = attr_dict['attribute_type_id']
            
            if attr_type_id not in result['attributes']:
                result['attributes'][attr_type_id] = {
                    'type_id': attr_type_id,
                    'type_name': attr_dict['attribute_type_name'],
                    'type_display_name': attr_dict['attribute_type_display_name'],
                    'value_id': attr_dict['attribute_value_id'],
                    'value': attr_dict['value'],
                    'display_value': attr_dict['display_value']
                }
        
        # Format inventory
        if inventory_row:
            inventory = dict(inventory_row)
            result['inventory'] = {
                'quantity': inventory['quantity'],
                'reserved_quantity': inventory['reserved_quantity'],
                'available_quantity': max(0, inventory['quantity'] - inventory['reserved_quantity']),
                'reorder_level': inventory['reorder_level'],
                'reorder_quantity': inventory['reorder_quantity'],
                'location': inventory['location'],
                'needs_reorder': inventory['quantity'] <= inventory['reorder_level']
            }
        
        return result
        
    except Exception as e:
        print(f"Error getting variant with attributes: {e}")
        return None
    finally:
        conn.close()


def find_variant_by_attribute_values(product_id, attr_value_dict):
    """
    Find a variant by attribute value IDs
    
    Args:
        product_id: The product ID
        attr_value_dict: Dictionary mapping attribute type IDs to value IDs
            e.g., {1: 12, 2: 25} where 1,2 are AttributeType IDs and 12,25 are AttributeValue IDs
            
    Returns:
        Variant ID if found, otherwise None
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get all variants for this product
        cursor.execute("SELECT id FROM ProductVariants WHERE product_id = ?", (product_id,))
        variant_rows = cursor.fetchall()
        
        if not variant_rows:
            return None
        
        # For each variant, check if it matches all attribute values
        for variant_row in variant_rows:
            variant_id = variant_row['id']
            matches = True
            
            # For each attribute type we're looking for
            for attr_type_id, attr_value_id in attr_value_dict.items():
                # Check if variant has this attribute value
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM VariantAttributeValues vav
                    JOIN AttributeValues av ON vav.attribute_value_id = av.id
                    WHERE vav.variant_id = ? 
                    AND av.id = ? 
                    AND av.attribute_type_id = ?
                """, (variant_id, attr_value_id, attr_type_id))
                
                result = cursor.fetchone()
                if result['count'] == 0:
                    # This variant doesn't have this attribute value
                    matches = False
                    break
            
            if matches:
                return variant_id
        
        return None
        
    except Exception as e:
        print(f"Error finding variant by attribute values: {e}")
        return None
    finally:
        conn.close()


def calculate_variant_price(product_id, attr_value_ids):
    """
    Calculate price for a specific attribute value combination
    
    Args:
        product_id: The product ID
        attr_value_ids: List of attribute value IDs
        
    Returns:
        Dictionary with base_price, adjustment_amount, and final_price
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get base product price
        cursor.execute("SELECT unit_price FROM Products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return None
        
        base_price = product['unit_price'] or 0
        
        # Get price adjustments for attribute values
        placeholders = ','.join(['?'] * len(attr_value_ids))
        query = f"""
            SELECT 
                pav.price_adjustment,
                pav.price_adjustment_type
            FROM ProductAttributeValues pav
            JOIN ProductAttributes pa ON pav.product_attribute_id = pa.id
            WHERE pa.product_id = ?
            AND pav.attribute_value_id IN ({placeholders})
            AND pa.affects_price = 1
        """
        
        cursor.execute(query, [product_id] + attr_value_ids)
        adjustments = cursor.fetchall()
        
        # Calculate total adjustment
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
        conn.close()
