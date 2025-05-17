from PyQt5.QtWidgets import QMessageBox
from models.product import Product
from models.category import Category
from database import get_connection
import json
import traceback
import sys

def debug_log(message):
    """Log debugging messages to console and file"""
    print(f"[DEBUG] {message}")
    try:
        with open("product_debug.log", "a") as f:
            f.write(f"{message}\n")
    except:
        pass

def get_all_products_reliable():
    """Get all products with enhanced error handling and debugging"""
    try:
        debug_log("Fetching all products...")
        conn = get_connection()
        if not conn:
            debug_log("Failed to get database connection")
            return []
            
        try:
            cursor = conn.cursor()
            
            # Direct SQL query with detailed error handling
            cursor.execute("""
                SELECT 
                    p.*,
                    c.name as category_name
                FROM Products p
                LEFT JOIN Categories c ON p.category_id = c.id
                ORDER BY p.name
            """)
            
            rows = cursor.fetchall()
            products = []
            
            for row in rows:
                try:
                    product_dict = dict(row)
                    
                    # Parse variant attributes if present
                    if product_dict.get('variant_attributes'):
                        try:
                            if isinstance(product_dict['variant_attributes'], str):
                                product_dict['variant_attributes'] = json.loads(product_dict['variant_attributes'])
                            # Validate it's iterable
                            if product_dict['variant_attributes'] is not None:
                                if not isinstance(product_dict['variant_attributes'], (list, dict)):
                                    product_dict['variant_attributes'] = []
                        except Exception as e:
                            debug_log(f"Error parsing variant attributes for product {product_dict.get('id')}: {e}")
                            product_dict['variant_attributes'] = []
                    
                    products.append(product_dict)
                except Exception as e:
                    debug_log(f"Error processing product row: {e}")
                    debug_log(f"Row data: {row}")
                    
            debug_log(f"Successfully retrieved {len(products)} products")
            return products
            
        except Exception as e:
            debug_log(f"Database error while fetching products: {e}")
            debug_log(traceback.format_exc())
            return []
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"Critical error in get_all_products: {e}")
        debug_log(traceback.format_exc())
        return []

def get_products_by_category_reliable(category_id):
    """Get products by category with enhanced error handling"""
    try:
        debug_log(f"Fetching products for category: {category_id}")
        conn = get_connection()
        if not conn:
            debug_log("Failed to get database connection")
            return []
            
        try:
            cursor = conn.cursor()
            
            # Direct SQL query with detailed error handling
            cursor.execute("""
                SELECT 
                    p.*,
                    c.name as category_name
                FROM Products p
                LEFT JOIN Categories c ON p.category_id = c.id
                WHERE p.category_id = ?
                ORDER BY p.name
            """, (category_id,))
            
            rows = cursor.fetchall()
            products = []
            
            for row in rows:
                try:
                    product_dict = dict(row)
                    
                    # Parse variant attributes if present
                    if product_dict.get('variant_attributes'):
                        try:
                            if isinstance(product_dict['variant_attributes'], str):
                                product_dict['variant_attributes'] = json.loads(product_dict['variant_attributes'])
                            # Validate it's iterable
                            if product_dict['variant_attributes'] is not None:
                                if not isinstance(product_dict['variant_attributes'], (list, dict)):
                                    product_dict['variant_attributes'] = []
                        except Exception as e:
                            debug_log(f"Error parsing variant attributes for product {product_dict.get('id')}: {e}")
                            product_dict['variant_attributes'] = []
                    
                    products.append(product_dict)
                except Exception as e:
                    debug_log(f"Error processing product row: {e}")
                    debug_log(f"Row data: {row}")
                    
            debug_log(f"Successfully retrieved {len(products)} products for category {category_id}")
            return products
            
        except Exception as e:
            debug_log(f"Database error while fetching products by category: {e}")
            debug_log(traceback.format_exc())
            return []
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"Critical error in get_products_by_category: {e}")
        debug_log(traceback.format_exc())
        return []

def update_product_reliable(product_id, **kwargs):
    """Update product with enhanced error handling and validation"""
    try:
        debug_log(f"Updating product ID {product_id} with values: {kwargs}")
        
        # Validate required fields
        if 'name' in kwargs and not kwargs['name']:
            debug_log("Product name cannot be empty")
            return False
            
        # Ensure numeric fields are valid
        for field in ['unit_price', 'purchase_price', 'stock', 'min_stock']:
            if field in kwargs:
                try:
                    if field in ['unit_price', 'purchase_price']:
                        kwargs[field] = float(kwargs[field])
                    else:
                        kwargs[field] = int(kwargs[field])
                except (ValueError, TypeError):
                    debug_log(f"Invalid value for {field}: {kwargs[field]}")
                    return False
        
        # Handle special case for variant_attributes
        if 'variant_attributes' in kwargs and kwargs['variant_attributes']:
            if not isinstance(kwargs['variant_attributes'], str):
                try:
                    kwargs['variant_attributes'] = json.dumps(kwargs['variant_attributes'])
                except Exception as e:
                    debug_log(f"Failed to convert variant_attributes to JSON: {e}")
                    kwargs['variant_attributes'] = '[]'
        
        # Update the product
        result = Product.update_product(product_id, **kwargs)
        
        if result:
            debug_log(f"Successfully updated product {product_id}")
        else:
            debug_log(f"Failed to update product {product_id}")
            
        return result
        
    except Exception as e:
        debug_log(f"Critical error in update_product_reliable: {e}")
        debug_log(traceback.format_exc())
        return False

def add_product_reliable(**kwargs):
    """Add a new product with enhanced error handling and validation"""
    try:
        debug_log(f"Adding new product with values: {kwargs}")
        
        # Validate required fields
        if not kwargs.get('name'):
            debug_log("Product name cannot be empty")
            return None
            
        # Ensure numeric fields are valid
        for field in ['unit_price', 'purchase_price', 'stock', 'min_stock']:
            if field in kwargs:
                try:
                    if field in ['unit_price', 'purchase_price']:
                        kwargs[field] = float(kwargs[field])
                    else:
                        kwargs[field] = int(kwargs[field])
                except (ValueError, TypeError):
                    debug_log(f"Invalid value for {field}: {kwargs[field]}")
                    return None
        
        # Handle special case for variant_attributes
        if 'variant_attributes' in kwargs and kwargs['variant_attributes']:
            if not isinstance(kwargs['variant_attributes'], str):
                try:
                    kwargs['variant_attributes'] = json.dumps(kwargs['variant_attributes'])
                except Exception as e:
                    debug_log(f"Failed to convert variant_attributes to JSON: {e}")
                    kwargs['variant_attributes'] = '[]'
        
        # Add the product
        product = Product(**kwargs)
        product_id = Product.add_product(product)
        
        if product_id:
            debug_log(f"Successfully added product with ID {product_id}")
        else:
            debug_log("Failed to add product")
            
        return product_id
        
    except Exception as e:
        debug_log(f"Critical error in add_product_reliable: {e}")
        debug_log(traceback.format_exc())
        return None

def get_product_by_id(product_id):
    """Get a specific product by ID with enhanced error handling"""
    try:
        debug_log(f"Fetching product with ID: {product_id}")
        conn = get_connection()
        if not conn:
            debug_log("Failed to get database connection")
            return None
            
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.*,
                    c.name as category_name
                FROM Products p
                LEFT JOIN Categories c ON p.category_id = c.id
                WHERE p.id = ?
            """, (product_id,))
            
            row = cursor.fetchone()
            if not row:
                debug_log(f"No product found with ID {product_id}")
                return None
                
            try:
                product_dict = dict(row)
                
                # Parse variant attributes if present
                if product_dict.get('variant_attributes'):
                    try:
                        if isinstance(product_dict['variant_attributes'], str):
                            product_dict['variant_attributes'] = json.loads(product_dict['variant_attributes'])
                        # Validate it's iterable
                        if product_dict['variant_attributes'] is not None:
                            if not isinstance(product_dict['variant_attributes'], (list, dict)):
                                product_dict['variant_attributes'] = []
                    except Exception as e:
                        debug_log(f"Error parsing variant attributes for product {product_id}: {e}")
                        product_dict['variant_attributes'] = []
                
                debug_log(f"Successfully retrieved product {product_id}")
                return product_dict
            except Exception as e:
                debug_log(f"Error processing product row: {e}")
                debug_log(f"Row data: {row}")
                return None
            
        except Exception as e:
            debug_log(f"Database error while fetching product: {e}")
            debug_log(traceback.format_exc())
            return None
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"Critical error in get_product_by_id: {e}")
        debug_log(traceback.format_exc())
        return None

def handle_error(parent, title, message, error=None):
    """Display error message and log it"""
    full_message = message
    if error:
        full_message = f"{message}\n\nDétails techniques: {str(error)}"
        debug_log(f"ERROR: {message} - {error}")
        debug_log(traceback.format_exc())
    else:
        debug_log(f"ERROR: {message}")
        
    QMessageBox.critical(parent, title, full_message)
