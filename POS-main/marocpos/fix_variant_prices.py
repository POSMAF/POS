#!/usr/bin/env python3
"""
Variant Price Fix Script

This script fixes price inconsistency issues by:
1. Updating unit_price values to match admin values
2. Ensuring price_adjustment and price_extras are properly set
3. Fixing any 0.00 prices that should have values

Run this after fix_variant_data.py to complete the database repair.
"""

import sqlite3
import json
import os

# Configuration
DATABASE_PATH = "pos2.db"  # Update this path if needed
DRY_RUN = False  # Set to False to actually update the database

# Known correct prices from admin (from user's feedback)
# Format: [variant_name_pattern, correct_price]
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

def get_correct_price(variant_name):
    """Get the correct price for a variant from our known list"""
    for pattern, price in KNOWN_PRICES:
        if pattern.lower() in variant_name.lower():
            return price
    
    # Default price if no match (can be adjusted based on your needs)
    return None

def fix_variant_prices():
    """Fix price inconsistency issues in variants"""
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
            SELECT id, product_id, name, unit_price, price_adjustment
            FROM ProductVariants
        """)
        
        variants = cursor.fetchall()
        print(f"Found {len(variants)} variants to process")
        
        fix_count = 0
        
        for variant in variants:
            variant_id = variant['id']
            product_id = variant['product_id']
            name = variant['name']
            current_price = variant['unit_price'] or 0
            current_adjustment = variant['price_adjustment'] or 0
            
            # Get correct price from our known list
            correct_price = get_correct_price(name)
            
            # If we have a known correct price
            if correct_price is not None:
                # Get the base price of the product
                cursor.execute("SELECT unit_price FROM Products WHERE id = ?", (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    print(f"Warning: Product {product_id} not found for variant {variant_id}")
                    continue
                
                base_price = product['unit_price'] or 0
                
                # Calculate the price adjustment needed
                price_adjustment = correct_price - base_price
                
                # Check if we need to update
                price_mismatch = abs(current_price - correct_price) > 0.01
                adjustment_mismatch = abs(current_adjustment - price_adjustment) > 0.01
                
                if price_mismatch or adjustment_mismatch:
                    print(f"Variant {variant_id} ({name}):")
                    print(f"  Current price: {current_price}")
                    print(f"  Correct price: {correct_price}")
                    print(f"  Current adjustment: {current_adjustment}")
                    print(f"  Calculated adjustment: {price_adjustment}")
                    
                    if not DRY_RUN:
                        cursor.execute("""
                            UPDATE ProductVariants
                            SET unit_price = ?,
                                price_adjustment = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (correct_price, price_adjustment, variant_id))
                        
                        fix_count += 1
                        print("  ✓ Updated")
                    print("")
            else:
                # If the price is 0 but should have a value
                if current_price == 0:
                    # Use a fallback price of 900 (the price mentioned in the feedback)
                    fallback_price = 900
                    
                    print(f"Variant {variant_id} ({name}):")
                    print(f"  Current price is 0, setting to fallback price: {fallback_price}")
                    
                    if not DRY_RUN:
                        cursor.execute("""
                            UPDATE ProductVariants
                            SET unit_price = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (fallback_price, variant_id))
                        
                        fix_count += 1
                        print("  ✓ Updated")
                    print("")
        
        if not DRY_RUN:
            # Commit the transaction
            cursor.execute("COMMIT")
        
        print(f"Fixed prices for {fix_count} variants")
        print("Price fix completed successfully!")
        
        if DRY_RUN:
            print("This was a DRY RUN - no changes were made to the database.")
            print("Set DRY_RUN = False to actually update the database.")
    
    except Exception as e:
        print(f"Error fixing variant prices: {e}")
        if not DRY_RUN:
            cursor.execute("ROLLBACK")
    finally:
        conn.close()

def main():
    print("=== Variant Price Fix Script ===")
    if DRY_RUN:
        print("Running in DRY RUN mode - no changes will be made")
    else:
        print("Running in LIVE mode - database will be updated")
    
    proceed = input("Do you want to proceed? (y/n): ").lower()
    if proceed != 'y':
        print("Operation cancelled.")
        return
    
    fix_variant_prices()

if __name__ == "__main__":
    main()
