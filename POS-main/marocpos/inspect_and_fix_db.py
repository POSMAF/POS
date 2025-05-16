#!/usr/bin/env python3
"""
Database Schema Inspector and Variant Data Fixer

This script will:
1. Inspect your database schema to identify table and column names
2. Make necessary schema modifications if needed
3. Fix variant data (attributes, names, prices) using the correct column names
4. Handle both 'attributes' and 'attribute_values' column possibilities

Run this script to automatically fix your database regardless of its current schema.
"""

import sqlite3
import json
import os
import re
import time
from datetime import datetime

# Configuration
DATABASE_PATH = "pos2.db"  # Update this path if needed
DRY_RUN = False  # Set to False to actually update the database

# Known correct prices from admin (from user's feedback)
KNOWN_PRICES = [
    ["BLACK / 4/128", 1500.0],
    ["BLACK / 6/128", 200.0],
    ["WHITE / 4/128", 499.0],
    ["WHITE / 6/128", 399.0]
]

def get_connection():
    """Get a connection to the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def inspect_database():
    """Inspect the database schema and return information about tables and columns"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check if ProductVariants table exists
        if 'ProductVariants' not in tables:
            print("❌ ProductVariants table doesn't exist!")
            return None
        
        # Get column information for ProductVariants
        cursor.execute("PRAGMA table_info(ProductVariants)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Check for attributes or attribute_values column
        attributes_column = None
        if 'attribute_values' in columns:
            attributes_column = 'attribute_values'
            print("✓ Found 'attribute_values' column in ProductVariants table")
        elif 'attributes' in columns:
            attributes_column = 'attributes'
            print("✓ Found 'attributes' column in ProductVariants table")
        else:
            print("❌ Neither 'attributes' nor 'attribute_values' column exists in ProductVariants!")
            
        # Check for unit_price column
        has_unit_price = 'unit_price' in columns
        
        # Check for price_adjustment column
        has_price_adjustment = 'price_adjustment' in columns
        
        db_info = {
            'tables': tables,
            'product_variants_columns': columns,
            'attributes_column': attributes_column,
            'has_unit_price': has_unit_price,
            'has_price_adjustment': has_price_adjustment
        }
        
        return db_info
    
    except Exception as e:
        print(f"Error inspecting database: {e}")
        return None
    finally:
        conn.close()

def fix_schema(db_info):
    """Fix database schema issues if needed"""
    if not db_info or not db_info['attributes_column']:
        print("❌ Cannot fix schema without database information")
        return False
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if we need to add the attribute_values column
        if db_info['attributes_column'] == 'attributes' and 'attribute_values' not in db_info['product_variants_columns']:
            print("Adding 'attribute_values' column to ProductVariants table...")
            
            if not DRY_RUN:
                try:
                    cursor.execute("ALTER TABLE ProductVariants ADD COLUMN attribute_values TEXT")
                    
                    # Copy data from attributes to attribute_values
                    cursor.execute("UPDATE ProductVariants SET attribute_values = attributes")
                    
                    conn.commit()
                    print("✓ Successfully added 'attribute_values' column")
                    db_info['attributes_column'] = 'attribute_values'
                except Exception as e:
                    print(f"❌ Error adding column: {e}")
                    return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        return False
    finally:
        conn.close()

def extract_attributes_from_name(variant_name):
    """Extract attribute values from a variant name like 'BLACK / 6/128'"""
    if not variant_name or '/' not in variant_name:
        return {}
    
    # Split by '/' and clean up
    parts = [part.strip() for part in variant_name.split('/')]
    
    # Determine attribute types based on the values
    attributes = {}
    
    # Check if the first part is likely a color
    colors = ['BLACK', 'WHITE', 'RED', 'BLUE', 'GREEN', 'YELLOW', 'PURPLE', 'ORANGE', 'GRAY', 'GREY', 'BROWN']
    storage_patterns = [r'\d+/\d+', r'\d+GB', r'\d+\s*GB', r'\d+\s*TB']
    
    # First attribute - for color-like values
    first_part = parts[0].upper()
    # Fix misspelled colors
    if 'BI ACK' in first_part or 'BIACK' in first_part:
        first_part = 'BLACK'
    
    if any(color in first_part for color in colors):
        attributes["COLOR"] = first_part
    
    # Remaining parts - for storage-like values or other attributes
    for i, part in enumerate(parts[1:], 1):
        part = part.strip().upper()
        
        # Check if this part matches a storage pattern
        if any(re.match(pattern, part) for pattern in storage_patterns):
            # Fix misspelled attribute name
            attributes["STORAGE"] = part
        else:
            # If we can't determine the type, use a generic attribute name
            attributes[f"ATTRIBUTE_{i}"] = part
    
    return attributes

def get_correct_price(variant_name):
    """Get the correct price for a variant from our known list"""
    for pattern, price in KNOWN_PRICES:
        if pattern.lower() in variant_name.lower():
            return price
    
    # Default fallback price
    return 900.0  # Default to 900 as mentioned in feedback

def fix_variant_data(db_info):
    """Fix variant data issues using the appropriate column names"""
    if not db_info or not db_info['attributes_column']:
        print("❌ Cannot fix data without database information")
        return False
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Start a transaction
        if not DRY_RUN:
            cursor.execute("BEGIN TRANSACTION")
        
        # Use the correct attributes column name
        attr_column = db_info['attributes_column']
        
        # Get all product variants
        query = f"SELECT id, product_id, name, {attr_column}, unit_price, price_adjustment, sku, barcode FROM ProductVariants"
        cursor.execute(query)
        
        variants = cursor.fetchall()
        print(f"Found {len(variants)} variants to process")
        
        variant_updates = 0
        price_updates = 0
        
        for variant in variants:
            variant_id = variant['id']
            product_id = variant['product_id']
            current_name = variant['name']
            current_attrs = variant[attr_column]
            current_price = variant.get('unit_price', 0)
            current_adjustment = variant.get('price_adjustment', 0)
            
            updates = []
            params = []
            
            # 1. Extract attributes from name and update
            extracted_attrs = extract_attributes_from_name(current_name)
            
            if extracted_attrs:
                new_attrs_json = json.dumps(extracted_attrs)
                
                if current_attrs != new_attrs_json:
                    updates.append(f"{attr_column} = ?")
                    params.append(new_attrs_json)
                    
                    # If we have attribute_values column but used attributes before
                    if attr_column == 'attribute_values' and 'attributes' in db_info['product_variants_columns']:
                        updates.append("attributes = ?")
                        params.append(new_attrs_json)
                    
                    print(f"Variant {variant_id} ({current_name}): Updating attributes to {extracted_attrs}")
            
            # 2. Fix variant name if needed
            new_name = current_name
            if 'BI ACK' in current_name:
                new_name = current_name.replace('BI ACK', 'BLACK')
                updates.append("name = ?")
                params.append(new_name)
                print(f"Variant {variant_id}: Fixing name from '{current_name}' to '{new_name}'")
            
            # 3. Update price information
            correct_price = get_correct_price(current_name)
            
            # Get base product price
            cursor.execute("SELECT unit_price FROM Products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            
            if product:
                base_price = product['unit_price'] or 0
                price_adjustment = correct_price - base_price
                
                # Update unit_price if needed
                if abs(current_price - correct_price) > 0.01:
                    updates.append("unit_price = ?")
                    params.append(correct_price)
                    print(f"Variant {variant_id}: Updating price from {current_price} to {correct_price}")
                
                # Update price_adjustment if needed and column exists
                if db_info['has_price_adjustment'] and abs(current_adjustment - price_adjustment) > 0.01:
                    updates.append("price_adjustment = ?")
                    params.append(price_adjustment)
                    print(f"Variant {variant_id}: Updating price_adjustment from {current_adjustment} to {price_adjustment}")
            
            # Perform update if needed
            if updates and params:
                if not DRY_RUN:
                    # Add updated_at timestamp
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    
                    # Construct and execute query
                    query = f"UPDATE ProductVariants SET {', '.join(updates)} WHERE id = ?"
                    params.append(variant_id)
                    
                    try:
                        cursor.execute(query, params)
                        variant_updates += 1
                        print(f"✓ Updated variant {variant_id}")
                    except Exception as e:
                        print(f"❌ Error updating variant {variant_id}: {e}")
                else:
                    print(f"Would update variant {variant_id} (dry run)")
            
        # Fix attribute names in ProductAttributes table
        try:
            if not DRY_RUN:
                cursor.execute("""
                    UPDATE ProductAttributes
                    SET name = 'STORAGE'
                    WHERE name = 'STROAGE'
                """)
                
                # Check if any rows were affected
                if cursor.rowcount > 0:
                    print(f"✓ Fixed 'STROAGE' to 'STORAGE' in ProductAttributes table")
        except Exception as e:
            print(f"❌ Error fixing attribute names: {e}")
        
        # Commit the transaction
        if not DRY_RUN:
            cursor.execute("COMMIT")
            print(f"✓ Successfully updated {variant_updates} variants")
        else:
            print(f"Would have updated {variant_updates} variants (dry run)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error fixing variant data: {e}")
        if not DRY_RUN:
            cursor.execute("ROLLBACK")
        return False
    finally:
        conn.close()

def main():
    print("=== Database Schema Inspector and Variant Data Fixer ===")
    if DRY_RUN:
        print("Running in DRY RUN mode - no changes will be made")
    else:
        print("Running in LIVE mode - database will be updated")
    
    # Ask for confirmation
    proceed = input("Do you want to proceed? (y/n): ").lower()
    if proceed != 'y':
        print("Operation cancelled.")
        return
    
    # Step 1: Inspect database schema
    print("\n--- Inspecting Database Schema ---")
    db_info = inspect_database()
    
    if not db_info:
        print("❌ Could not inspect database schema. Exiting.")
        return
    
    # Step 2: Fix schema if needed
    print("\n--- Fixing Schema Issues ---")
    if not fix_schema(db_info):
        print("❌ Could not fix schema issues. Continuing with data fixes...")
    
    # Step 3: Fix variant data
    print("\n--- Fixing Variant Data ---")
    if not fix_variant_data(db_info):
        print("❌ Could not fix variant data.")
        return
    
    print("\n✓ Database inspection and fixes complete!")
    print("Please restart your application and check if the issues are resolved.")

if __name__ == "__main__":
    main()
