"""
Attribute Manager Module

This module provides classes and functions for managing product attributes,
including creating, retrieving, updating and deleting attribute types and values.
"""

from database import get_connection
import json

class AttributeType:
    """Class representing an attribute type (e.g., Color, Size)"""
    
    def __init__(self, id=None, name=None, display_name=None, description=None, 
                 display_type='select', is_active=True, sort_order=0,
                 created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.display_name = display_name
        self.description = description
        self.display_type = display_type
        self.is_active = is_active
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
        self._values = None  # Lazy loaded
    
    @property
    def values(self):
        """Get attribute values for this type (lazy loaded)"""
        if self._values is None and self.id:
            self._values = AttributeValue.get_by_attribute_type(self.id)
        return self._values
    
    def to_dict(self, include_values=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'display_type': self.display_type,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_values:
            result['values'] = [v.to_dict() for v in self.values]
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            display_name=data.get('display_name'),
            description=data.get('description'),
            display_type=data.get('display_type'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_all(cls, active_only=True):
        """Get all attribute types"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM AttributeTypes"
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
            
            query += " ORDER BY sort_order, display_name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [cls.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Error getting attribute types: {e}")
            return []
        finally:
            conn.close()
    
    @classmethod
    def get_by_id(cls, id):
        """Get attribute type by ID"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM AttributeTypes WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting attribute type by ID: {e}")
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_by_name(cls, name):
        """Get attribute type by name"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM AttributeTypes WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting attribute type by name: {e}")
            return None
        finally:
            conn.close()
    
    def save(self):
        """Save attribute type to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE AttributeTypes 
                    SET name = ?, display_name = ?, description = ?, 
                        display_type = ?, is_active = ?, sort_order = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.name, self.display_name, self.description,
                    self.display_type, self.is_active, self.sort_order,
                    self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO AttributeTypes 
                    (name, display_name, description, display_type, is_active, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.name, self.display_name, self.description,
                    self.display_type, self.is_active, self.sort_order
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving attribute type: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete attribute type"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM AttributeTypes WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting attribute type: {e}")
            return False
        finally:
            conn.close()


class AttributeValue:
    """Class representing an attribute value (e.g., Red, XL)"""
    
    def __init__(self, id=None, attribute_type_id=None, value=None, display_value=None,
                 description=None, html_color=None, image_path=None, sort_order=0,
                 is_active=True, created_at=None, updated_at=None):
        self.id = id
        self.attribute_type_id = attribute_type_id
        self.value = value
        self.display_value = display_value
        self.description = description
        self.html_color = html_color
        self.image_path = image_path
        self.sort_order = sort_order
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'attribute_type_id': self.attribute_type_id,
            'value': self.value,
            'display_value': self.display_value,
            'description': self.description,
            'html_color': self.html_color,
            'image_path': self.image_path,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            attribute_type_id=data.get('attribute_type_id'),
            value=data.get('value'),
            display_value=data.get('display_value'),
            description=data.get('description'),
            html_color=data.get('html_color'),
            image_path=data.get('image_path'),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_by_id(cls, id):
        """Get attribute value by ID"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM AttributeValues WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting attribute value by ID: {e}")
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_by_attribute_type(cls, attribute_type_id, active_only=True):
        """Get all values for an attribute type"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM AttributeValues WHERE attribute_type_id = ?"
            params = [attribute_type_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY sort_order, display_value"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [cls.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Error getting attribute values by type: {e}")
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
                # Update existing
                cursor.execute("""
                    UPDATE AttributeValues 
                    SET attribute_type_id = ?, value = ?, display_value = ?, 
                        description = ?, html_color = ?, image_path = ?,
                        sort_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.attribute_type_id, self.value, self.display_value,
                    self.description, self.html_color, self.image_path,
                    self.sort_order, self.is_active, self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO AttributeValues 
                    (attribute_type_id, value, display_value, description, 
                     html_color, image_path, sort_order, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.attribute_type_id, self.value, self.display_value,
                    self.description, self.html_color, self.image_path,
                    self.sort_order, self.is_active
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving attribute value: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete attribute value"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM AttributeValues WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting attribute value: {e}")
            return False
        finally:
            conn.close()


class ProductAttribute:
    """Class representing an attribute associated with a product"""
    
    def __init__(self, id=None, product_id=None, attribute_type_id=None,
                 is_required=True, affects_price=True, affects_inventory=True,
                 sort_order=0, created_at=None, updated_at=None):
        self.id = id
        self.product_id = product_id
        self.attribute_type_id = attribute_type_id
        self.is_required = is_required
        self.affects_price = affects_price
        self.affects_inventory = affects_inventory
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
        self._attribute_type = None
        self._attribute_values = None
    
    @property
    def attribute_type(self):
        """Get the attribute type (lazy loaded)"""
        if self._attribute_type is None and self.attribute_type_id:
            self._attribute_type = AttributeType.get_by_id(self.attribute_type_id)
        return self._attribute_type
    
    @property
    def values(self):
        """Get product attribute values (lazy loaded)"""
        if self._attribute_values is None and self.id:
            self._attribute_values = ProductAttributeValue.get_by_product_attribute(self.id)
        return self._attribute_values
    
    def to_dict(self, include_values=False, include_type=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'product_id': self.product_id,
            'attribute_type_id': self.attribute_type_id,
            'is_required': self.is_required,
            'affects_price': self.affects_price,
            'affects_inventory': self.affects_inventory,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_type and self.attribute_type:
            result['attribute_type'] = self.attribute_type.to_dict()
        
        if include_values:
            result['values'] = [v.to_dict() for v in self.values]
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            product_id=data.get('product_id'),
            attribute_type_id=data.get('attribute_type_id'),
            is_required=data.get('is_required', True),
            affects_price=data.get('affects_price', True),
            affects_inventory=data.get('affects_inventory', True),
            sort_order=data.get('sort_order', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_by_product(cls, product_id):
        """Get all attributes for a product"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pa.* 
                FROM ProductAttributes pa
                JOIN AttributeTypes at ON pa.attribute_type_id = at.id
                WHERE pa.product_id = ?
                ORDER BY pa.sort_order, at.display_name
            """, (product_id,))
            rows = cursor.fetchall()
            
            return [cls.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Error getting product attributes: {e}")
            return []
        finally:
            conn.close()
    
    @classmethod
    def get_by_id(cls, id):
        """Get product attribute by ID"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ProductAttributes WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting product attribute by ID: {e}")
            return None
        finally:
            conn.close()
    
    def save(self):
        """Save product attribute to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE ProductAttributes 
                    SET product_id = ?, attribute_type_id = ?, is_required = ?,
                        affects_price = ?, affects_inventory = ?, sort_order = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.product_id, self.attribute_type_id, self.is_required,
                    self.affects_price, self.affects_inventory, self.sort_order,
                    self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO ProductAttributes 
                    (product_id, attribute_type_id, is_required, 
                     affects_price, affects_inventory, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.product_id, self.attribute_type_id, self.is_required,
                    self.affects_price, self.affects_inventory, self.sort_order
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving product attribute: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete product attribute"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ProductAttributes WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting product attribute: {e}")
            return False
        finally:
            conn.close()


class ProductAttributeValue:
    """Class representing a product attribute value with pricing info"""
    
    def __init__(self, id=None, product_attribute_id=None, attribute_value_id=None,
                 price_adjustment=0, price_adjustment_type='fixed', is_default=False,
                 is_active=True, sort_order=0, created_at=None, updated_at=None):
        self.id = id
        self.product_attribute_id = product_attribute_id
        self.attribute_value_id = attribute_value_id
        self.price_adjustment = price_adjustment
        self.price_adjustment_type = price_adjustment_type
        self.is_default = is_default
        self.is_active = is_active
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
        self._attribute_value = None
    
    @property
    def attribute_value(self):
        """Get the attribute value (lazy loaded)"""
        if self._attribute_value is None and self.attribute_value_id:
            self._attribute_value = AttributeValue.get_by_id(self.attribute_value_id)
        return self._attribute_value
    
    def to_dict(self, include_attribute_value=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'product_attribute_id': self.product_attribute_id,
            'attribute_value_id': self.attribute_value_id,
            'price_adjustment': self.price_adjustment,
            'price_adjustment_type': self.price_adjustment_type,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_attribute_value and self.attribute_value:
            result['attribute_value'] = self.attribute_value.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            product_attribute_id=data.get('product_attribute_id'),
            attribute_value_id=data.get('attribute_value_id'),
            price_adjustment=data.get('price_adjustment', 0),
            price_adjustment_type=data.get('price_adjustment_type', 'fixed'),
            is_default=data.get('is_default', False),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_by_product_attribute(cls, product_attribute_id, active_only=True):
        """Get all product attribute values for a product attribute"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT pav.*, av.value, av.display_value, av.html_color
                FROM ProductAttributeValues pav
                JOIN AttributeValues av ON pav.attribute_value_id = av.id
                WHERE pav.product_attribute_id = ?
            """
            params = [product_attribute_id]
            
            if active_only:
                query += " AND pav.is_active = 1"
            
            query += " ORDER BY pav.sort_order, av.display_value"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                # Create ProductAttributeValue
                product_attr_value = cls.from_dict(dict(row))
                
                # Create AttributeValue and attach
                attr_value = AttributeValue.from_dict({
                    'id': row['attribute_value_id'],
                    'value': row['value'],
                    'display_value': row['display_value'],
                    'html_color': row['html_color']
                })
                product_attr_value._attribute_value = attr_value
                
                result.append(product_attr_value)
            
            return result
        except Exception as e:
            print(f"Error getting product attribute values: {e}")
            return []
        finally:
            conn.close()
    
    def save(self):
        """Save product attribute value to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE ProductAttributeValues 
                    SET product_attribute_id = ?, attribute_value_id = ?, 
                        price_adjustment = ?, price_adjustment_type = ?,
                        is_default = ?, is_active = ?, sort_order = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.product_attribute_id, self.attribute_value_id,
                    self.price_adjustment, self.price_adjustment_type,
                    self.is_default, self.is_active, self.sort_order,
                    self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO ProductAttributeValues 
                    (product_attribute_id, attribute_value_id, price_adjustment,
                     price_adjustment_type, is_default, is_active, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.product_attribute_id, self.attribute_value_id,
                    self.price_adjustment, self.price_adjustment_type,
                    self.is_default, self.is_active, self.sort_order
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving product attribute value: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete product attribute value"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ProductAttributeValues WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting product attribute value: {e}")
            return False
        finally:
            conn.close()


# Helper function to get complete attribute configuration for a product
def get_product_attributes_with_values(product_id):
    """
    Get complete attribute configuration for a product including values
    
    Returns:
        List of dictionaries with attribute types and their values
    """
    # Get product attributes
    product_attributes = ProductAttribute.get_by_product(product_id)
    
    result = []
    for product_attr in product_attributes:
        # Get attribute type info
        attribute_type = product_attr.attribute_type
        if not attribute_type:
            continue
        
        # Get product attribute values
        product_attr_values = product_attr.values
        
        # Build result
        attr_dict = {
            'id': product_attr.id,
            'type': {
                'id': attribute_type.id,
                'name': attribute_type.name,
                'display_name': attribute_type.display_name,
                'display_type': attribute_type.display_type
            },
            'is_required': product_attr.is_required,
            'affects_price': product_attr.affects_price,
            'affects_inventory': product_attr.affects_inventory,
            'values': []
        }
        
        # Add values
        for pav in product_attr_values:
            attr_value = pav.attribute_value
            if not attr_value:
                continue
                
            attr_dict['values'].append({
                'id': pav.id,
                'attribute_value_id': attr_value.id,
                'value': attr_value.value,
                'display_value': attr_value.display_value,
                'html_color': attr_value.html_color,
                'image_path': attr_value.image_path,
                'price_adjustment': pav.price_adjustment,
                'price_adjustment_type': pav.price_adjustment_type,
                'is_default': pav.is_default
            })
        
        result.append(attr_dict)
    
    return result
