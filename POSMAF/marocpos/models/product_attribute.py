from database import get_connection
from datetime import datetime, UTC
import json

class ProductAttribute:
    def __init__(self, name, description=None, display_type='radio'):
        self.name = name
        self.description = description
        self.display_type = display_type  # radio, select, color, pills

    @staticmethod
    def create_tables():
        """Ensure the attribute and variant tables exist"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Create ProductAttributes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ProductAttributes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        display_type TEXT DEFAULT 'radio' CHECK(display_type IN ('radio', 'select', 'color', 'pills')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create ProductAttributeValues table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ProductAttributeValues (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        attribute_id INTEGER NOT NULL,
                        value TEXT NOT NULL,
                        sequence INTEGER DEFAULT 0,
                        html_color TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (attribute_id) REFERENCES ProductAttributes(id) ON DELETE CASCADE,
                        UNIQUE(attribute_id, value)
                    )
                """)
                
                # Create ProductTemplateAttributeLine table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ProductTemplateAttributeLine (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        attribute_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
                        FOREIGN KEY (attribute_id) REFERENCES ProductAttributes(id) ON DELETE CASCADE,
                        UNIQUE(product_id, attribute_id)
                    )
                """)
                
                # Create ProductTemplateAttributeValue table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ProductTemplateAttributeValue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        line_id INTEGER NOT NULL,
                        value_id INTEGER NOT NULL,
                        price_extra REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (line_id) REFERENCES ProductTemplateAttributeLine(id) ON DELETE CASCADE,
                        FOREIGN KEY (value_id) REFERENCES ProductAttributeValues(id) ON DELETE CASCADE,
                        UNIQUE(line_id, value_id)
                    )
                """)
                
                # Create ProductVariantCombination table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ProductVariantCombination (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        product_variant_id INTEGER NOT NULL,
                        template_attribute_value_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
                        FOREIGN KEY (product_variant_id) REFERENCES ProductVariants(id) ON DELETE CASCADE,
                        FOREIGN KEY (template_attribute_value_id) REFERENCES ProductTemplateAttributeValue(id) ON DELETE CASCADE,
                        UNIQUE(product_variant_id, template_attribute_value_id)
                    )
                """)
                
                # Check if we need to add display_type to existing ProductAttributes table
                cursor.execute("PRAGMA table_info(ProductAttributes)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'display_type' not in columns:
                    print("Adding display_type column to ProductAttributes table...")
                    cursor.execute("ALTER TABLE ProductAttributes ADD COLUMN display_type TEXT DEFAULT 'radio'")
                
                if 'updated_at' not in columns:
                    print("Adding updated_at column to ProductAttributes table...")
                    cursor.execute("ALTER TABLE ProductAttributes ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                # Check if we need to add sequence and html_color to existing ProductAttributeValues table
                cursor.execute("PRAGMA table_info(ProductAttributeValues)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'sequence' not in columns:
                    print("Adding sequence column to ProductAttributeValues table...")
                    cursor.execute("ALTER TABLE ProductAttributeValues ADD COLUMN sequence INTEGER DEFAULT 0")
                
                if 'html_color' not in columns:
                    print("Adding html_color column to ProductAttributeValues table...")
                    cursor.execute("ALTER TABLE ProductAttributeValues ADD COLUMN html_color TEXT")
                
                if 'updated_at' not in columns:
                    print("Adding updated_at column to ProductAttributeValues table...")
                    cursor.execute("ALTER TABLE ProductAttributeValues ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                conn.commit()
                return True
            except Exception as e:
                print(f"Error creating attribute tables: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def get_all_attributes():
        """Get all product attributes"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, created_at
                    FROM ProductAttributes
                    ORDER BY name
                """)
                
                attributes = []
                for row in cursor.fetchall():
                    attributes.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'created_at': row[3]
                    })
                return attributes
            except Exception as e:
                print(f"Error getting attributes: {e}")
                return []
            finally:
                conn.close()
        return []

    @staticmethod
    def add_attribute(name, description=None, display_type='radio'):
        """Add a new product attribute"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if attribute already exists
                cursor.execute("SELECT id FROM ProductAttributes WHERE name = ?", (name,))
                existing = cursor.fetchone()
                if existing:
                    return existing[0]  # Return existing attribute ID
                
                # Add new attribute
                try:
                    # For Python 3.11+
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    # For older Python versions
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    
                # Validate display_type
                valid_display_types = ['radio', 'select', 'color', 'pills']
                if display_type not in valid_display_types:
                    display_type = 'radio'
                    
                cursor.execute("""
                    INSERT INTO ProductAttributes (
                        name, description, display_type, 
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (name, description, display_type, current_time, current_time))
                
                attribute_id = cursor.lastrowid
                conn.commit()
                return attribute_id
            except Exception as e:
                print(f"Error adding attribute: {e}")
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def update_attribute(attribute_id, name, description=None):
        """Update an existing attribute"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ProductAttributes
                    SET name = ?, description = ?
                    WHERE id = ?
                """, (name, description, attribute_id))
                
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Error updating attribute: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def delete_attribute(attribute_id):
        """Delete an attribute and its values"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete attribute values
                cursor.execute("DELETE FROM ProductAttributeValues WHERE attribute_id = ?", (attribute_id,))
                
                # Delete attribute
                cursor.execute("DELETE FROM ProductAttributes WHERE id = ?", (attribute_id,))
                
                cursor.execute("COMMIT")
                return True
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error deleting attribute: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def get_attribute_values(attribute_id):
        """Get all values for a specific attribute"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, value
                    FROM ProductAttributeValues
                    WHERE attribute_id = ?
                    ORDER BY value
                """, (attribute_id,))
                
                values = []
                for row in cursor.fetchall():
                    values.append({
                        'id': row[0],
                        'value': row[1]
                    })
                return values
            except Exception as e:
                print(f"Error getting attribute values: {e}")
                return []
            finally:
                conn.close()
        return []

    @staticmethod
    def add_attribute_value(attribute_id, value, sequence=0, html_color=None):
        """Add a new value for an attribute"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if value already exists
                cursor.execute("""
                    SELECT id FROM ProductAttributeValues 
                    WHERE attribute_id = ? AND value = ?
                """, (attribute_id, value))
                existing = cursor.fetchone()
                if existing:
                    return existing[0]  # Return existing value ID
                
                # Get current timestamp
                try:
                    # For Python 3.11+
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    # For older Python versions
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add new value
                cursor.execute("""
                    INSERT INTO ProductAttributeValues (
                        attribute_id, value, sequence, html_color,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (attribute_id, value, sequence, html_color, current_time, current_time))
                
                value_id = cursor.lastrowid
                conn.commit()
                return value_id
            except Exception as e:
                print(f"Error adding attribute value: {e}")
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def delete_attribute_value(value_id):
        """Delete an attribute value"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ProductAttributeValues WHERE id = ?", (value_id,))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Error deleting attribute value: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def associate_attribute_to_product(product_id, attribute_id):
        """Associate an attribute to a product template"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if association already exists
                cursor.execute("""
                    SELECT id FROM ProductTemplateAttributeLine 
                    WHERE product_id = ? AND attribute_id = ?
                """, (product_id, attribute_id))
                existing = cursor.fetchone()
                if existing:
                    return existing[0]  # Return existing association ID
                
                # Get current timestamp
                try:
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                # Create new association
                cursor.execute("""
                    INSERT INTO ProductTemplateAttributeLine (
                        product_id, attribute_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?)
                """, (product_id, attribute_id, current_time, current_time))
                
                line_id = cursor.lastrowid
                conn.commit()
                return line_id
            except Exception as e:
                print(f"Error associating attribute to product: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def add_attribute_value_to_line(line_id, value_id, price_extra=0):
        """Add an attribute value to a product template attribute line with optional price extra"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if value is already associated
                cursor.execute("""
                    SELECT id FROM ProductTemplateAttributeValue 
                    WHERE line_id = ? AND value_id = ?
                """, (line_id, value_id))
                existing = cursor.fetchone()
                if existing:
                    # Update price_extra if the association already exists
                    cursor.execute("""
                        UPDATE ProductTemplateAttributeValue
                        SET price_extra = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (price_extra, existing[0]))
                    conn.commit()
                    return existing[0]
                
                # Get current timestamp
                try:
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                # Create new association
                cursor.execute("""
                    INSERT INTO ProductTemplateAttributeValue (
                        line_id, value_id, price_extra, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (line_id, value_id, price_extra, current_time, current_time))
                
                template_value_id = cursor.lastrowid
                conn.commit()
                return template_value_id
            except Exception as e:
                print(f"Error adding attribute value to line: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def get_product_attribute_lines(product_id):
        """Get all attribute lines for a product with their values"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get attribute lines
                cursor.execute("""
                    SELECT 
                        pal.id as line_id, 
                        pal.attribute_id,
                        a.name as attribute_name,
                        a.display_type
                    FROM ProductTemplateAttributeLine pal
                    JOIN ProductAttributes a ON pal.attribute_id = a.id
                    WHERE pal.product_id = ?
                """, (product_id,))
                
                lines = []
                for line in cursor.fetchall():
                    line_dict = dict(line)
                    
                    # Get values for this line
                    cursor.execute("""
                        SELECT 
                            ptav.id as template_value_id,
                            ptav.value_id,
                            ptav.price_extra,
                            pav.value,
                            pav.sequence,
                            pav.html_color
                        FROM ProductTemplateAttributeValue ptav
                        JOIN ProductAttributeValues pav ON ptav.value_id = pav.id
                        WHERE ptav.line_id = ?
                        ORDER BY pav.sequence, pav.value
                    """, (line_dict['line_id'],))
                    
                    line_dict['values'] = [dict(value) for value in cursor.fetchall()]
                    lines.append(line_dict)
                
                return lines
            except Exception as e:
                print(f"Error getting product attribute lines: {e}")
                return []
            finally:
                conn.close()
        return []
    
    @staticmethod
    def add_variant_combination(product_id, variant_id, template_value_ids):
        """
        Create variant combinations for a product variant
        
        Args:
            product_id: The base product ID
            variant_id: The product variant ID
            template_value_ids: List of template attribute value IDs that define this variant
        """
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Start a transaction
                cursor.execute("BEGIN TRANSACTION")
                
                for template_value_id in template_value_ids:
                    # Check if combination already exists
                    cursor.execute("""
                        SELECT id FROM ProductVariantCombination 
                        WHERE product_variant_id = ? AND template_attribute_value_id = ?
                    """, (variant_id, template_value_id))
                    
                    if not cursor.fetchone():
                        # Create the combination
                        cursor.execute("""
                            INSERT INTO ProductVariantCombination (
                                product_id, product_variant_id, template_attribute_value_id, created_at
                            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """, (product_id, variant_id, template_value_id))
                
                cursor.execute("COMMIT")
                return True
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error adding variant combination: {e}")
                return False
            finally:
                conn.close()
        return False
    
    @staticmethod
    def generate_variant_combinations(product_id_or_attributes):
        """
        Generate all possible variant combinations for a product
        
        Args:
            product_id_or_attributes: Either a product ID or a dictionary of attribute names to values
            
        Returns:
            A list of variant definitions
        """
        # Check if we received a dict of attributes instead of a product_id
        if isinstance(product_id_or_attributes, dict):
            # We received attributes_values directly, use the legacy dictionary method
            return ProductAttribute.generate_variant_combinations_dict(product_id_or_attributes)
            
        # Otherwise, we have a product_id, proceed with the new implementation    
        product_id = product_id_or_attributes
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get all attribute lines for this product
                attribute_lines = ProductAttribute.get_product_attribute_lines(product_id)
                
                if not attribute_lines:
                    return []
                
                # Prepare data structure for generating combinations
                line_values = {}
                for line in attribute_lines:
                    attribute_name = line['attribute_name']
                    line_values[attribute_name] = line['values']
                
                # Generate all combinations
                combinations = []
                
                def generate_combinations(lines, current_combination=None, index=0):
                    if current_combination is None:
                        current_combination = {
                            'attribute_value_ids': [],
                            'price_extra': 0,
                            'attributes': {}
                        }
                    
                    if index >= len(lines):
                        combinations.append(current_combination.copy())
                        return
                    
                    current_line = lines[index]
                    attribute_name = current_line['attribute_name']
                    
                    for value in current_line['values']:
                        # Add this attribute value to the combination
                        new_combination = {
                            'attribute_value_ids': current_combination['attribute_value_ids'] + [value['template_value_id']],
                            'price_extra': current_combination['price_extra'] + value['price_extra'],
                            'attributes': {**current_combination['attributes'], attribute_name: value['value']}
                        }
                        
                        generate_combinations(lines, new_combination, index + 1)
                
                generate_combinations(attribute_lines)
                return combinations
            except Exception as e:
                print(f"Error generating variant combinations: {e}")
                return []
            finally:
                conn.close()
        return []
        
    @staticmethod
    def generate_variant_combinations_dict(attributes_values):
        """
        Generate all possible combinations of attribute values
        
        Args:
            attributes_values: A dict where keys are attribute names and values are lists of values
                e.g. {'Color': ['Red', 'Blue'], 'Size': ['S', 'M', 'L']}
        
        Returns:
            A list of dictionaries, each representing a variant combination
        """
        def generate_combinations(attrs, current=None, index=0):
            if current is None:
                current = {}
            
            if index >= len(attrs):
                return [current.copy()]
            
            attr_name = list(attrs.keys())[index]
            combinations = []
            
            for value in attrs[attr_name]:
                current[attr_name] = value
                combinations.extend(generate_combinations(attrs, current, index + 1))
            
            return combinations
        
        return generate_combinations(attributes_values)
