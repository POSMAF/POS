#!/usr/bin/env python3
"""
Variant Data Migration Script

This script fixes existing variant data issues by:
1. Extracting attribute values from variant names
2. Updating attribute_values with proper JSON
3. Fixing misspelled attributes
4. Ensuring price consistency
5. Updating SKUs where needed

Run this once to fix existing data in your database.
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

def get_connection():
    """Get a connection to the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

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

def generate_sku(attributes):
    """Generate a SKU based on attributes"""
    sku_parts = []
    
    # Process each attribute
    for attr_name, attr_value in attributes.items():
        # Clean up the attribute name and value
        attr_prefix = attr_name[0].upper()
        cleaned_value = ''.join(c for c in attr_value if c.isalnum())
        value_part = cleaned_value.upper() if len(cleaned_value) <= 4 else cleaned_value[:4].upper()
        sku_parts.append(f"{attr_prefix}{value_part}")
    
    # Add a unique timestamp-based suffix
    timestamp_suffix = str(int(time.time() * 1000))[-4:]
    
    return f"SKU-{''.join(sku_parts)}-{timestamp_suffix}"

def fix_variant_data():
    """Fix variant data issues in the database"""
    conn = get_connection()
    if not conn:
        print("Could not connect to the database. Exiting.")
        return
    
    try:
        cursor = conn.cursor()
        
        # Start a transaction
        if not DRY_RUN:
            cursor.execute("BEGIN TRANSACTION")
        
        # Get all product variants
        cursor.execute("""
            SELECT id, product_id, name, attribute_values, 
                   unit_price, price_adjustment, sku, barcode
            FROM ProductVariants
        """)
        
        variants = cursor.fetchall()
        print(f"Found {len(variants)} variants to process")
        
        update_count = 0
        
        for variant in variants:
            variant_id = variant['id']
            product_id = variant['product_id']
            current_name = variant['name']
            current_attrs = variant['attribute_values']
            current_price = variant['unit_price']
            current_sku = variant['sku']
            
            # Extract attributes from the name
            extracted_attrs = extract_attributes_from_name(current_name)
            
            if not extracted_attrs:
                print(f"Warning: Could not extract attributes from variant name: '{current_name}' (ID: {variant_id})")
                continue
            
            # Convert to JSON
            new_attrs_json = json.dumps(extracted_attrs)
            
            # Generate a new SKU if needed
            update_sku = False
            new_sku = current_sku
            
            if not current_sku or any(misspelled in current_sku for misspelled in ['BIACK', 'STROA']):
                new_sku = generate_sku(extracted_attrs)
                update_sku = True
            
            # Update variant in the database
            if not DRY_RUN:
                query = """
                    UPDATE ProductVariants 
                    SET attribute_values = ?,
                        updated_at = CURRENT_TIMESTAMP
                """
                params = [new_attrs_json]
                
                # Update name if needed to fix misspellings
                new_name = current_name
                if 'BI ACK' in current_name:
                    new_name = current_name.replace('BI ACK', 'BLACK')
                    query += ", name = ?"
                    params.append(new_name)
                
                # Update SKU if needed
                if update_sku:
                    query += ", sku = ?"
                    params.append(new_sku)
                
                # Add WHERE clause
                query += " WHERE id = ?"
                params.append(variant_id)
                
                # Execute the update
                cursor.execute(query, params)
                update_count += 1
            
            # Print what we're doing
            print(f"Variant {variant_id} ('{current_name}'):")
            print(f"  Extracted attributes: {extracted_attrs}")
            print(f"  JSON: {new_attrs_json}")
            if update_sku:
                print(f"  New SKU: {new_sku}")
            if current_name != new_name:
                print(f"  New name: {new_name}")
            print("")
        
        # Fix attribute names in ProductAttributes table
        if not DRY_RUN:
            cursor.execute("""
                UPDATE ProductAttributes
                SET name = 'STORAGE'
                WHERE name = 'STROAGE'
            """)
            
            # Commit the transaction
            cursor.execute("COMMIT")
        
        print(f"Updated {update_count} variants")
        print("Fix completed successfully!")
        
        if DRY_RUN:
            print("This was a DRY RUN - no changes were made to the database.")
            print("Set DRY_RUN = False to actually update the database.")
    
    except Exception as e:
        print(f"Error fixing variant data: {e}")
        if not DRY_RUN:
            cursor.execute("ROLLBACK")
    finally:
        conn.close()

def main():
    print("=== Variant Data Migration Script ===")
    if DRY_RUN:
        print("Running in DRY RUN mode - no changes will be made")
    else:
        print("Running in LIVE mode - database will be updated")
    
    proceed = input("Do you want to proceed? (y/n): ").lower()
    if proceed != 'y':
        print("Operation cancelled.")
        return
    
    fix_variant_data()

if __name__ == "__main__":
    main()
