"""
Rules Engine Module

This module provides classes and functions for managing attribute rules,
including compatibility, dependency, and exclusion rules.
"""

from database import get_connection
from .attribute_manager import AttributeType, AttributeValue

class AttributeRule:
    """Class representing a rule between attribute values"""
    
    def __init__(self, id=None, product_id=None, rule_type=None,
                 primary_attribute_id=None, primary_value_id=None,
                 secondary_attribute_id=None, secondary_value_id=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.product_id = product_id
        self.rule_type = rule_type  # compatibility, dependency, exclusion
        self.primary_attribute_id = primary_attribute_id
        self.primary_value_id = primary_value_id
        self.secondary_attribute_id = secondary_attribute_id
        self.secondary_value_id = secondary_value_id
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'rule_type': self.rule_type,
            'primary_attribute_id': self.primary_attribute_id,
            'primary_value_id': self.primary_value_id,
            'secondary_attribute_id': self.secondary_attribute_id,
            'secondary_value_id': self.secondary_value_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            product_id=data.get('product_id'),
            rule_type=data.get('rule_type'),
            primary_attribute_id=data.get('primary_attribute_id'),
            primary_value_id=data.get('primary_value_id'),
            secondary_attribute_id=data.get('secondary_attribute_id'),
            secondary_value_id=data.get('secondary_value_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def get_by_id(cls, id):
        """Get attribute rule by ID"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM AttributeRules WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return cls.from_dict(dict(row))
        except Exception as e:
            print(f"Error getting attribute rule by ID: {e}")
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_by_product(cls, product_id):
        """Get all rules for a product"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM AttributeRules WHERE product_id = ?
                ORDER BY rule_type, primary_attribute_id
            """, (product_id,))
            rows = cursor.fetchall()
            
            return [cls.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Error getting product rules: {e}")
            return []
        finally:
            conn.close()
    
    def save(self):
        """Save attribute rule to database"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            if self.id:
                # Update existing
                cursor.execute("""
                    UPDATE AttributeRules 
                    SET product_id = ?, rule_type = ?,
                        primary_attribute_id = ?, primary_value_id = ?,
                        secondary_attribute_id = ?, secondary_value_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.product_id, self.rule_type,
                    self.primary_attribute_id, self.primary_value_id,
                    self.secondary_attribute_id, self.secondary_value_id,
                    self.id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO AttributeRules 
                    (product_id, rule_type, primary_attribute_id, primary_value_id,
                     secondary_attribute_id, secondary_value_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.product_id, self.rule_type,
                    self.primary_attribute_id, self.primary_value_id,
                    self.secondary_attribute_id, self.secondary_value_id
                ))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving attribute rule: {e}")
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Delete attribute rule"""
        if not self.id:
            return False
        
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM AttributeRules WHERE id = ?", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting attribute rule: {e}")
            return False
        finally:
            conn.close()


class RulesEngine:
    """Engine for validating attribute combinations based on rules"""
    
    def __init__(self, product_id):
        self.product_id = product_id
        self.rules = AttributeRule.get_by_product(product_id)
        self._rule_cache = self._build_rule_cache()
    
    def _build_rule_cache(self):
        """Build an optimized structure for rule lookup"""
        cache = {
            'compatibility': {},  # primary_value_id -> {secondary_value_id: True}
            'dependency': {},     # primary_value_id -> [{attr_id, val_id}]
            'exclusion': {}       # primary_value_id -> {secondary_value_id: True}
        }
        
        for rule in self.rules:
            rule_type = rule.rule_type
            
            # Skip invalid rules
            if not rule_type or not rule.primary_attribute_id:
                continue
            
            # Handle different rule types
            if rule_type == 'compatibility':
                # For compatibility, we store which values can work together
                primary_id = f"{rule.primary_attribute_id}:{rule.primary_value_id}"
                secondary_id = f"{rule.secondary_attribute_id}:{rule.secondary_value_id}"
                
                if primary_id not in cache['compatibility']:
                    cache['compatibility'][primary_id] = {}
                
                cache['compatibility'][primary_id][secondary_id] = True
                
                # Add reverse mapping for bidirectional compatibility
                if secondary_id not in cache['compatibility']:
                    cache['compatibility'][secondary_id] = {}
                
                cache['compatibility'][secondary_id][primary_id] = True
                
            elif rule_type == 'dependency':
                # For dependency, A->B means "if A then must have B"
                primary_id = f"{rule.primary_attribute_id}:{rule.primary_value_id}"
                
                if primary_id not in cache['dependency']:
                    cache['dependency'][primary_id] = []
                
                cache['dependency'][primary_id].append({
                    'attribute_id': rule.secondary_attribute_id,
                    'value_id': rule.secondary_value_id
                })
                
            elif rule_type == 'exclusion':
                # For exclusion, we store which values cannot work together
                primary_id = f"{rule.primary_attribute_id}:{rule.primary_value_id}"
                secondary_id = f"{rule.secondary_attribute_id}:{rule.secondary_value_id}"
                
                if primary_id not in cache['exclusion']:
                    cache['exclusion'][primary_id] = {}
                
                cache['exclusion'][primary_id][secondary_id] = True
                
                # Add reverse mapping for bidirectional exclusion
                if secondary_id not in cache['exclusion']:
                    cache['exclusion'][secondary_id] = {}
                
                cache['exclusion'][secondary_id][primary_id] = True
        
        return cache
    
    def validate_combination(self, attribute_values):
        """
        Validate if a combination of attribute values is valid
        
        Args:
            attribute_values: Dictionary mapping attribute_id to value_id
                e.g., {1: 12, 2: 25} where 1,2 are AttributeType IDs and 12,25 are AttributeValue IDs
        
        Returns:
            Tuple (is_valid, error_message)
        """
        if not attribute_values:
            return True, None
        
        # Check compatibility rules
        for attr_id, value_id in attribute_values.items():
            item_id = f"{attr_id}:{value_id}"
            
            # If this value has compatibility rules
            if item_id in self._rule_cache['compatibility']:
                # For each other attribute value in the selection
                for other_attr_id, other_value_id in attribute_values.items():
                    # Skip self
                    if attr_id == other_attr_id:
                        continue
                    
                    other_id = f"{other_attr_id}:{other_value_id}"
                    
                    # If there's a compatibility rule and other value isn't compatible
                    if other_id not in self._rule_cache['compatibility'][item_id]:
                        return False, f"Incompatible attribute values: {item_id} and {other_id}"
        
        # Check dependency rules
        for attr_id, value_id in attribute_values.items():
            item_id = f"{attr_id}:{value_id}"
            
            # If this value has dependency rules
            if item_id in self._rule_cache['dependency']:
                dependencies = self._rule_cache['dependency'][item_id]
                
                # For each required dependency
                for dep in dependencies:
                    dep_attr_id = dep['attribute_id']
                    dep_value_id = dep['value_id']
                    
                    # Check if the dependency is satisfied
                    if dep_attr_id not in attribute_values or attribute_values[dep_attr_id] != dep_value_id:
                        return False, f"Missing required dependency for {item_id}"
        
        # Check exclusion rules
        for attr_id, value_id in attribute_values.items():
            item_id = f"{attr_id}:{value_id}"
            
            # If this value has exclusion rules
            if item_id in self._rule_cache['exclusion']:
                # For each other attribute value in the selection
                for other_attr_id, other_value_id in attribute_values.items():
                    # Skip self
                    if attr_id == other_attr_id:
                        continue
                    
                    other_id = f"{other_attr_id}:{other_value_id}"
                    
                    # If other value is excluded
                    if other_id in self._rule_cache['exclusion'][item_id]:
                        return False, f"Excluded attribute values: {item_id} and {other_id}"
        
        return True, None
    
    def get_compatible_values(self, attribute_id, selected_values=None):
        """
        Get compatible values for an attribute based on currently selected values
        
        Args:
            attribute_id: The attribute ID to get values for
            selected_values: Dictionary of attribute_id -> value_id for currently selected values
            
        Returns:
            List of compatible attribute values for the specified attribute
        """
        if selected_values is None:
            selected_values = {}
        
        # Get all values for this attribute
        all_values = self._get_attribute_values(attribute_id)
        
        # If no values are selected, return all values
        if not selected_values:
            return all_values
        
        # Filter values based on rules
        compatible_values = []
        
        for value in all_values:
            # Create a test combination with this value
            test_values = selected_values.copy()
            test_values[attribute_id] = value.id
            
            # Check if combination is valid
            is_valid, _ = self.validate_combination(test_values)
            
            if is_valid:
                compatible_values.append(value)
        
        return compatible_values
    
    def _get_attribute_values(self, attribute_id):
        """Get all values for an attribute"""
        return AttributeValue.get_by_attribute_type(attribute_id)


def create_compatibility_rule(product_id, primary_attribute_id, primary_value_id, 
                             secondary_attribute_id, secondary_value_id):
    """
    Create a compatibility rule (values work together)
    
    Args:
        product_id: The product ID
        primary_attribute_id: ID of primary attribute type
        primary_value_id: ID of primary attribute value
        secondary_attribute_id: ID of secondary attribute type
        secondary_value_id: ID of secondary attribute value
        
    Returns:
        ID of created rule
    """
    rule = AttributeRule(
        product_id=product_id,
        rule_type='compatibility',
        primary_attribute_id=primary_attribute_id,
        primary_value_id=primary_value_id,
        secondary_attribute_id=secondary_attribute_id,
        secondary_value_id=secondary_value_id
    )
    
    if rule.save():
        return rule.id
    return None


def create_dependency_rule(product_id, primary_attribute_id, primary_value_id, 
                          secondary_attribute_id, secondary_value_id):
    """
    Create a dependency rule (if A then must have B)
    
    Args:
        product_id: The product ID
        primary_attribute_id: ID of primary attribute type (A)
        primary_value_id: ID of primary attribute value (A)
        secondary_attribute_id: ID of secondary attribute type (B)
        secondary_value_id: ID of secondary attribute value (B)
        
    Returns:
        ID of created rule
    """
    rule = AttributeRule(
        product_id=product_id,
        rule_type='dependency',
        primary_attribute_id=primary_attribute_id,
        primary_value_id=primary_value_id,
        secondary_attribute_id=secondary_attribute_id,
        secondary_value_id=secondary_value_id
    )
    
    if rule.save():
        return rule.id
    return None


def create_exclusion_rule(product_id, primary_attribute_id, primary_value_id, 
                         secondary_attribute_id, secondary_value_id):
    """
    Create an exclusion rule (values cannot work together)
    
    Args:
        product_id: The product ID
        primary_attribute_id: ID of primary attribute type
        primary_value_id: ID of primary attribute value
        secondary_attribute_id: ID of secondary attribute type
        secondary_value_id: ID of secondary attribute value
        
    Returns:
        ID of created rule
    """
    rule = AttributeRule(
        product_id=product_id,
        rule_type='exclusion',
        primary_attribute_id=primary_attribute_id,
        primary_value_id=primary_value_id,
        secondary_attribute_id=secondary_attribute_id,
        secondary_value_id=secondary_value_id
    )
    
    if rule.save():
        return rule.id
    return None


def get_valid_variants(product_id):
    """
    Get all valid variant combinations for a product based on rules
    
    Args:
        product_id: The product ID
        
    Returns:
        List of valid attribute value combinations
    """
    # Import here to avoid circular imports
    from .attribute_manager import get_product_attributes_with_values
    
    # Get all attributes and values for this product
    attributes = get_product_attributes_with_values(product_id)
    
    if not attributes:
        return []
    
    # Create rules engine
    engine = RulesEngine(product_id)
    
    # Generate all valid combinations
    return _generate_valid_combinations(engine, attributes)


def _generate_valid_combinations(engine, attributes, current_index=0, current_values=None):
    """
    Recursively generate all valid attribute value combinations
    
    Args:
        engine: RulesEngine instance
        attributes: List of attribute data
        current_index: Current attribute index
        current_values: Current values dictionary (attribute_id -> value_id)
        
    Returns:
        List of valid combinations
    """
    if current_values is None:
        current_values = {}
    
    # If we've processed all attributes, add the combination
    if current_index >= len(attributes):
        # Validate the complete combination
        is_valid, _ = engine.validate_combination(current_values)
        
        if is_valid:
            return [current_values.copy()]
        else:
            return []
    
    # Get current attribute
    attribute = attributes[current_index]
    attr_id = attribute['type']['id']
    
    # Get all values for this attribute
    values = attribute['values']
    
    # Generate combinations
    valid_combinations = []
    
    for value in values:
        # Add this value to current values
        current_values[attr_id] = value['attribute_value_id']
        
        # Check if combination so far is valid
        is_valid, _ = engine.validate_combination(current_values)
        
        if is_valid:
            # Continue with next attribute
            valid_combinations.extend(
                _generate_valid_combinations(
                    engine, attributes, current_index + 1, current_values
                )
            )
        
        # Remove this value
        del current_values[attr_id]
    
    return valid_combinations
