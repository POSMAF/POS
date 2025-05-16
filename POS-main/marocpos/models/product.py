from database import get_connection
from datetime import datetime, UTC
import json
import sqlite3

class Product:
    def __init__(self, name, unit_price=0, purchase_price=0, stock=0, category_id=None):
        self.name = name
        self.unit_price = unit_price or 0  # Convert None to 0
        self.purchase_price = purchase_price or 0  # Convert None to 0
        self.stock = stock or 0  # Convert None to 0
        self.category_id = category_id

    @staticmethod
    def create_tables():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Update Products table with variant support
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        barcode TEXT,
                        name TEXT NOT NULL,
                        description TEXT,
                        unit_price REAL DEFAULT 0,
                        purchase_price REAL DEFAULT 0,
                        profit_margin REAL,
                        stock INTEGER DEFAULT 0,
                        min_stock INTEGER DEFAULT 0,
                        reorder_point INTEGER,
                        image_path TEXT,
                        category_id INTEGER,
                        unit TEXT DEFAULT 'pièce',
                        weight REAL,
                        volume REAL,
                        status TEXT DEFAULT 'available',
                        product_type TEXT DEFAULT 'stockable',
                        valuation_method TEXT DEFAULT 'FIFO',
                        has_variants BOOLEAN DEFAULT 0,
                        variant_attributes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (category_id) REFERENCES Categories(id)
                    )
                """)
                
                # Create ProductVariants table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ProductVariants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        attribute_values TEXT,
                        price_adjustment REAL DEFAULT 0,
                        stock INTEGER DEFAULT 0,
                        barcode TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES Products(id)
                    )
                """)
                
                # Check if columns exist, add them if they don't
                cursor.execute("PRAGMA table_info(Products)")
                columns = {row[1] for row in cursor.fetchall()}
                
                # Add has_variants column if it doesn't exist
                if 'has_variants' not in columns:
                    print("Adding 'has_variants' column to Products table...")
                    cursor.execute("ALTER TABLE Products ADD COLUMN has_variants BOOLEAN DEFAULT 0")
                
                # Add variant_attributes column if it doesn't exist
                if 'variant_attributes' not in columns:
                    print("Adding 'variant_attributes' column to Products table...")
                    cursor.execute("ALTER TABLE Products ADD COLUMN variant_attributes TEXT")
                
                conn.commit()
            finally:
                conn.close()

    @staticmethod
    def get_all_products():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # First check if the variant columns exist
                cursor.execute("PRAGMA table_info(Products)")
                columns = {row[1] for row in cursor.fetchall()}
                
                # Build query based on available columns
                query = """
                    SELECT 
                        p.id, 
                        p.name, 
                        p.barcode,
                        p.description,
                        COALESCE(p.unit_price, 0) as unit_price, 
                        COALESCE(p.purchase_price, 0) as purchase_price,
                        p.profit_margin,
                        COALESCE(p.stock, 0) as stock,
                        p.min_stock,
                        p.reorder_point,
                        p.image_path,
                        p.category_id,
                        p.unit,
                        p.weight,
                        p.volume,
                        COALESCE(p.status, 'available') as status,
                        COALESCE(p.product_type, 'stockable') as product_type,
                        COALESCE(p.valuation_method, 'FIFO') as valuation_method,
                """
                
                # Add variant columns if they exist
                if 'has_variants' in columns:
                    query += "p.has_variants,"
                else:
                    query += "0 as has_variants,"
                    
                if 'variant_attributes' in columns:
                    query += "p.variant_attributes,"
                else:
                    query += "NULL as variant_attributes,"
                
                query += """
                        COALESCE(c.name, 'Non catégorisé') as category_name,
                        p.created_at,
                        p.updated_at
                    FROM Products p
                    LEFT JOIN Categories c ON p.category_id = c.id
                    ORDER BY p.id DESC
                """
                
                cursor.execute(query)
                return cursor.fetchall()
            except Exception as e:
                print(f"Error in get_all_products: {e}")
                return []
            finally:
                conn.close()
        return []

    @staticmethod
    def get_products_by_category(category_id=None):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if variant columns exist
                cursor.execute("PRAGMA table_info(Products)")
                columns = {row[1] for row in cursor.fetchall()}
                
                # Build the base query
                query = """
                    SELECT 
                        p.id, 
                        p.name, 
                        p.barcode,
                        COALESCE(p.unit_price, 0) as unit_price, 
                        COALESCE(p.stock, 0) as stock,
                        p.image_path,
                        p.category_id,
                """
                
                # Add variant columns if they exist
                if 'has_variants' in columns:
                    query += "p.has_variants,"
                else:
                    query += "0 as has_variants,"
                    
                if 'variant_attributes' in columns:
                    query += "p.variant_attributes,"
                else:
                    query += "NULL as variant_attributes,"
                
                query += """
                        COALESCE(c.name, 'Non catégorisé') as category_name,
                        p.description,
                        COALESCE(p.purchase_price, 0) as purchase_price,
                        COALESCE(p.min_stock, 0) as min_stock,
                        p.unit,
                        p.weight,
                        p.volume,
                        COALESCE(p.status, 'available') as status,
                        COALESCE(p.product_type, 'stockable') as product_type,
                        COALESCE(p.valuation_method, 'FIFO') as valuation_method
                    FROM Products p
                    LEFT JOIN Categories c ON p.category_id = c.id
                """
                
                # Add category filter if provided
                if category_id is not None:
                    query += " WHERE p.category_id = ? "
                    params = (category_id,)
                else:
                    params = ()
                
                query += " ORDER BY p.name"
                
                cursor.execute(query, params)

                products = cursor.fetchall()
                
                # Process variant attributes if present
                result = []
                for product in products:
                    product_dict = dict(product)
                    if product_dict.get('variant_attributes'):
                        try:
                            product_dict['variant_attributes'] = json.loads(product_dict['variant_attributes'])
                        except:
                            product_dict['variant_attributes'] = None
                    result.append(product_dict)
                
                return result
            except Exception as e:
                print(f"Error getting products by category: {e}")
                return []
            finally:
                conn.close()
        return []

    @staticmethod
    def add_variant(product_id, attribute_values, price_adjustment=0, stock=0, barcode=None):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Convert attribute values to JSON if it's a dict
                if isinstance(attribute_values, dict):
                    attribute_values = json.dumps(attribute_values)
                
                cursor.execute("""
                    INSERT INTO ProductVariants (
                        product_id, attribute_values, price_adjustment,
                        stock, barcode
                    ) VALUES (?, ?, ?, ?, ?)
                """, (product_id, attribute_values, price_adjustment, stock, barcode))
                
                variant_id = cursor.lastrowid
                conn.commit()
                return variant_id
            except Exception as e:
                print(f"Error adding variant: {e}")
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def get_variants(product_id):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # First get the variants basic data
                cursor.execute("""
                    SELECT *
                    FROM ProductVariants
                    WHERE product_id = ?
                    ORDER BY id
                """, (product_id,))
                variants = cursor.fetchall()
                
                # Convert variants to a more robust format
                result = []
                for variant in variants:
                    variant_dict = dict(variant)
                    
                    # Handle attribute_values with better error protection
                    if variant_dict.get('attribute_values'):
                        try:
                            if isinstance(variant_dict['attribute_values'], str):
                                parsed_values = json.loads(variant_dict['attribute_values'])
                                # Store in both attribute_values and attributes for compatibility
                                variant_dict['attribute_values'] = parsed_values
                                variant_dict['attributes'] = parsed_values.copy() if isinstance(parsed_values, dict) else {}
                            else:
                                # If it's already a dict/object, make sure we have it in both places
                                variant_dict['attributes'] = variant_dict['attribute_values'].copy() if isinstance(variant_dict['attribute_values'], dict) else {}
                        except Exception as e:
                            print(f"Error parsing variant attributes: {e}")
                            # Provide empty dictionaries as fallback
                            variant_dict['attribute_values'] = {}
                            variant_dict['attributes'] = {}
                    else:
                        # Ensure both attribute keys exist even if empty
                        variant_dict['attribute_values'] = {}
                        variant_dict['attributes'] = {}
                    
                    # Print parsed values for debugging
                    print(f"Variant {variant_dict['id']}: Parsed attribute values: {variant_dict['attributes']}")
                    
                    # Try to get product attribute lines to calculate price extras
                    try:
                        # Get product attributes and possible values
                        cursor.execute("""
                            SELECT 
                                pal.id as line_id,
                                a.name as attribute_name,
                                pav.value as attribute_value,
                                ptav.price_extra
                            FROM ProductTemplateAttributeLine pal
                            JOIN ProductAttributes a ON pal.attribute_id = a.id
                            JOIN ProductTemplateAttributeValue ptav ON ptav.line_id = pal.id
                            JOIN ProductAttributeValues pav ON ptav.value_id = pav.id
                            WHERE pal.product_id = ?
                        """, (product_id,))
                        
                        attribute_values = cursor.fetchall()
                        
                        # Get variant's attribute values from JSON
                        variant_attributes = variant_dict['attributes']
                        
                        # Calculate price extras
                        total_price_extra = 0.0
                        for attr in attribute_values:
                            # Check if this attribute value is used in the variant
                            if attr['attribute_name'] in variant_attributes and variant_attributes[attr['attribute_name']] == attr['attribute_value']:
                                # Add the price extra for this attribute value
                                total_price_extra += float(attr['price_extra'] or 0)
                        
                        # Get variant price adjustment
                        base_adj = float(variant_dict.get('price_adjustment') or 0)
                        
                        # Store both values
                        variant_dict['price_extras'] = total_price_extra
                        variant_dict['total_price_adjustment'] = total_price_extra + base_adj
                        
                        print(f"Variant {variant_dict['id']} - Total price adjustment: {variant_dict['total_price_adjustment']} ({base_adj} variant, {total_price_extra} attributes)")
                        
                    except Exception as e:
                        print(f"Error calculating price adjustment for variant {variant_dict['id']}: {e}")
                        
                        # Try alternative method using ProductVariantCombination
                        try:
                            cursor.execute("""
                                SELECT ptav.price_extra
                                FROM ProductVariantCombination pvc
                                JOIN ProductTemplateAttributeValue ptav ON pvc.template_attribute_value_id = ptav.id
                                WHERE pvc.product_variant_id = ?
                            """, (variant_dict['id'],))
                            
                            price_extras = cursor.fetchall()
                            total_price_extra = sum(float(extra['price_extra'] or 0) for extra in price_extras)
                            
                            # Add in any explicit price_adjustment for the variant 
                            base_adj = float(variant_dict.get('price_adjustment') or 0)
                            
                            # Store both values
                            variant_dict['price_extras'] = total_price_extra
                            variant_dict['total_price_adjustment'] = total_price_extra + base_adj
                            
                            print(f"Variant {variant_dict['id']} - Alt method - Total price adjustment: {variant_dict['total_price_adjustment']} ({base_adj} variant, {total_price_extra} attributes)")
                            
                        except Exception as e2:
                            print(f"Error with alternative method: {e2}")
                            # Use just the base adjustment as fallback
                            variant_dict['price_extras'] = 0
                            variant_dict['total_price_adjustment'] = float(variant_dict.get('price_adjustment') or 0)
                    
                    # Add explicit debugging output
                    print(f"Returning variant: {variant_dict['id']}, attributes: {variant_dict.get('attributes')}, price_adjustment: {variant_dict.get('total_price_adjustment')}")
                    
                    result.append(variant_dict)
                
                return result
            except Exception as e:
                print(f"Error getting variants: {e}")
                return []
            finally:
                conn.close()
        return []

    @staticmethod
    def get_stock_movements(product_id, variant_id=None):
        """Get stock movement history for a product"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Query base with parameters
                query = """
                    SELECT 
                        sm.id, sm.product_id, sm.variant_id, 
                        sm.movement_type, sm.quantity, sm.unit_price,
                        sm.reference, sm.notes, u.username as user_name,
                        sm.created_at
                    FROM StockMovements sm
                    LEFT JOIN Users u ON sm.user_id = u.id
                    WHERE sm.product_id = ?
                """
                params = [product_id]
                
                # Add variant filter if specified
                if variant_id:
                    query += " AND sm.variant_id = ?"
                    params.append(variant_id)
                
                # Sort by date (newest first)
                query += " ORDER BY sm.created_at DESC"
                
                cursor.execute(query, params)
                movements = cursor.fetchall()
                
                # Convert to dictionaries
                return [dict(movement) for movement in movements]
            except Exception as e:
                print(f"Error getting stock movements: {e}")
                return []
            finally:
                conn.close()
        return []
    
    @staticmethod 
    def add_stock_movement(product_id, variant_id, movement_type, quantity, unit_price, reference, notes, user_id):
        """Add a stock movement record"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Start a transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Insert movement record
                cursor.execute("""
                    INSERT INTO StockMovements (
                        product_id, variant_id, movement_type, 
                        quantity, unit_price, reference, 
                        notes, user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    product_id, variant_id, movement_type,
                    quantity, unit_price, reference,
                    notes, user_id
                ))
                
                movement_id = cursor.lastrowid
                
                # Update product or variant stock
                if variant_id:
                    cursor.execute("""
                        UPDATE ProductVariants
                        SET stock = stock + ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (quantity, variant_id))
                else:
                    cursor.execute("""
                        UPDATE Products
                        SET stock = stock + ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (quantity, product_id))
                
                cursor.execute("COMMIT")
                return movement_id
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error adding stock movement: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def delete_stock_movement(movement_id):
        """Delete a stock movement and revert its effects"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Start a transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Get the movement details
                cursor.execute("""
                    SELECT product_id, variant_id, quantity
                    FROM StockMovements
                    WHERE id = ?
                """, (movement_id,))
                
                movement = cursor.fetchone()
                if not movement:
                    cursor.execute("ROLLBACK")
                    return False
                
                product_id = movement['product_id']
                variant_id = movement['variant_id']
                quantity = movement['quantity']
                
                # Reverse the stock change
                if variant_id:
                    cursor.execute("""
                        UPDATE ProductVariants
                        SET stock = stock - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (quantity, variant_id))
                else:
                    cursor.execute("""
                        UPDATE Products
                        SET stock = stock - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (quantity, product_id))
                
                # Delete the movement record
                cursor.execute("DELETE FROM StockMovements WHERE id = ?", (movement_id,))
                
                cursor.execute("COMMIT")
                return True
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error deleting stock movement: {e}")
                return False
            finally:
                conn.close()
        return False
        
    @staticmethod
    def update_variant(variant_id, **kwargs):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key == 'attribute_values' and isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                
                # Add updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                # Add variant_id to values
                values.append(variant_id)
                
                query = f"""
                    UPDATE ProductVariants 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating variant: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def add_product(name, unit_price=0, purchase_price=0, stock=0, category_id=None, has_variants=False, variant_attributes=None, variants=None, **kwargs):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION")
                
                # Prepare fields and values
                fields = ['name', 'unit_price', 'purchase_price', 'stock', 'category_id', 'has_variants']
                values = [name, unit_price, purchase_price, stock, category_id, has_variants]
                
                # Add variant_attributes if present
                if variant_attributes:
                    fields.append('variant_attributes')
                    values.append(json.dumps(variant_attributes) if isinstance(variant_attributes, list) else variant_attributes)
                
                # Add optional fields
                optional_fields = [
                    'barcode', 'description', 'image_path', 'unit', 
                    'weight', 'volume', 'status', 'product_type',
                    'valuation_method', 'min_stock', 'reorder_point'
                ]
                
                for field in optional_fields:
                    if field in kwargs and kwargs[field] is not None:
                        fields.append(field)
                        values.append(kwargs[field])
                
                # Add timestamps
                try:
                    # For Python 3.11+
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    # For older Python versions
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                fields.extend(['created_at', 'updated_at'])
                values.extend([current_time, current_time])
                
                # Create the SQL query
                query = f"""
                    INSERT INTO Products ({', '.join(fields)})
                    VALUES ({', '.join(['?' for _ in fields])})
                """
                
                cursor.execute(query, values)
                product_id = cursor.lastrowid
                
                # Calculate and update profit margin if both prices are provided
                if unit_price and purchase_price:
                    profit_margin = ((unit_price - purchase_price) / purchase_price) * 100
                    cursor.execute("""
                        UPDATE Products 
                        SET profit_margin = ?
                        WHERE id = ?
                    """, (profit_margin, product_id))
                
                # Add default supplier if provided
                if 'supplier_id' in kwargs and kwargs['supplier_id']:
                    cursor.execute("""
                        INSERT INTO ProductSuppliers (
                            product_id, supplier_id, price, 
                            lead_time, minimum_order
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        product_id, 
                        kwargs['supplier_id'],
                        kwargs.get('supplier_price', purchase_price),
                        kwargs.get('lead_time'),
                        kwargs.get('minimum_order')
                    ))
                
                # Add variants if provided
                if has_variants and variants:
                    for variant in variants:
                        # Calculate variant price
                        variant_price = variant.get('price', unit_price)
                        
                        # Get attribute values and ensure they are in JSON format
                        attribute_values = variant.get('attribute_values', '{}')
                        if isinstance(attribute_values, dict):
                            attribute_values = json.dumps(attribute_values)
                        
                        # Prepare variant insert query with correct column names
                        cursor.execute("""
                            INSERT INTO ProductVariants (
                                product_id, name, barcode, unit_price, 
                                purchase_price, stock, attribute_values, sku,
                                created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            product_id,
                            variant.get('name', ''),
                            variant.get('barcode', ''),
                            variant_price,
                            variant.get('purchase_price', purchase_price),
                            variant.get('stock', 0),
                            attribute_values,
                            variant.get('sku', ''),
                            current_time,
                            current_time
                        ))
                
                # Commit transaction
                cursor.execute("COMMIT")
                return product_id
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error adding product: {e}")
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def update_product(product_id, **kwargs):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                values = []
                
                for key, value in kwargs.items():
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                
                # Calculate profit margin if prices are updated
                if 'unit_price' in kwargs or 'purchase_price' in kwargs:
                    # Get current prices if not being updated
                    if 'unit_price' not in kwargs or 'purchase_price' not in kwargs:
                        cursor.execute("""
                            SELECT unit_price, purchase_price 
                            FROM Products 
                            WHERE id = ?
                        """, (product_id,))
                        current = cursor.fetchone()
                        
                        unit_price = kwargs.get('unit_price', current['unit_price'])
                        purchase_price = kwargs.get('purchase_price', current['purchase_price'])
                    else:
                        unit_price = kwargs['unit_price']
                        purchase_price = kwargs['purchase_price']
                    
                    if purchase_price:
                        profit_margin = ((unit_price - purchase_price) / purchase_price) * 100
                        update_fields.append("profit_margin = ?")
                        values.append(profit_margin)
                
                # Add updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                # Add product_id to values
                values.append(product_id)
                
                query = f"""
                    UPDATE Products 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating product: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def delete_product(product_id):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete related records first
                cursor.execute("DELETE FROM ProductVariants WHERE product_id = ?", (product_id,))
                
                # Try to delete from StockMovements if the table exists
                try:
                    cursor.execute("DELETE FROM StockMovements WHERE product_id = ?", (product_id,))
                except sqlite3.OperationalError:
                    pass  # Table might not exist
                
                # Try to delete from ProductSuppliers if the table exists
                try:
                    cursor.execute("DELETE FROM ProductSuppliers WHERE product_id = ?", (product_id,))
                except sqlite3.OperationalError:
                    pass  # Table might not exist
                
                # Delete the product
                cursor.execute("DELETE FROM Products WHERE id = ?", (product_id,))
                
                cursor.execute("COMMIT")
                return True
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error deleting product: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def update_stock(product_id, quantity, movement_type='adjustment', reference=None, user_id=None):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION")

                # Get current stock and min_stock
                cursor.execute("""
                    SELECT stock, min_stock, reorder_point 
                    FROM Products 
                    WHERE id = ?
                """, (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    raise Exception("Product not found")
                
                new_stock = product['stock'] + quantity

                # Update product stock
                cursor.execute("""
                    UPDATE Products 
                    SET stock = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_stock, product_id))

                # Try to record stock movement if table exists
                try:
                    cursor.execute("""
                        INSERT INTO StockMovements (
                            product_id, quantity, movement_type,
                            reference, user_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (product_id, quantity, movement_type, reference, user_id))
                except sqlite3.OperationalError:
                    pass  # StockMovements table might not exist

                cursor.execute("COMMIT")
                
                # Check if stock is below minimum
                if new_stock <= product['min_stock']:
                    # Could trigger notifications or automatic reordering here
                    print(f"Warning: Product {product_id} stock is below minimum!")
                
                return True
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error updating stock: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def get_product(product_id):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        p.*, 
                        COALESCE(c.name, 'Non catégorisé') as category_name
                    FROM Products p
                    LEFT JOIN Categories c ON p.category_id = c.id
                    WHERE p.id = ?
                """, (product_id,))
                return cursor.fetchone()
            finally:
                conn.close()
        return None

    @staticmethod
    def search_products(query):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        p.id, 
                        p.name, 
                        p.barcode,
                        COALESCE(p.unit_price, 0) as unit_price, 
                        COALESCE(p.stock, 0) as stock,
                        p.image_path,
                        p.category_id,
                        COALESCE(c.name, 'Non catégorisé') as category_name
                    FROM Products p
                    LEFT JOIN Categories c ON p.category_id = c.id
                    WHERE p.name LIKE ? OR p.barcode LIKE ?
                    ORDER BY p.name
                """, (f"%{query}%", f"%{query}%"))
                return cursor.fetchall()
            finally:
                conn.close()
        return []

    @staticmethod
    def get_product_suppliers(product_id):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.*, 
                        ps.price as supplier_price,
                        ps.lead_time,
                        ps.minimum_order
                    FROM Suppliers s
                    JOIN ProductSuppliers ps ON s.id = ps.supplier_id
                    WHERE ps.product_id = ?
                    ORDER BY ps.price ASC
                """, (product_id,))
                return cursor.fetchall()
            finally:
                conn.close()
        return []

    @staticmethod
    def cleanup_database():
        """Clean up any NULL values in the database"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Products 
                    SET 
                        unit_price = COALESCE(unit_price, 0),
                        purchase_price = COALESCE(purchase_price, 0),
                        stock = COALESCE(stock, 0),
                        status = COALESCE(status, 'available'),
                        product_type = COALESCE(product_type, 'stockable'),
                        valuation_method = COALESCE(valuation_method, 'FIFO')
                    WHERE 
                        unit_price IS NULL 
                        OR purchase_price IS NULL
                        OR stock IS NULL 
                        OR status IS NULL 
                        OR product_type IS NULL 
                        OR valuation_method IS NULL
                """)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error cleaning up database: {e}")
                return False
            finally:
                conn.close()
        return False