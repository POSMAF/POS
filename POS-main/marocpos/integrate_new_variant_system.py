#!/usr/bin/env python3
"""
Integration Script for New Variant System

This script:
1. Creates all necessary tables for the new variant system
2. Fixes existing attribute value data (corrects misspelled attributes)
3. Updates variant prices to reflect correct price calculations
4. Ensures all variants have proper attribute values

Run this script once to migrate your existing data to the new variant system.
"""

import sqlite3
import os
import json
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our variant manager
from variant_manager import get_variant_attributes, get_variant_price_with_extras
from models.product_attribute import ProductAttribute
from database import get_connection

def check_database_path():
    """Check if the database file exists"""
    db_path = "pos2.db"
    if not os.path.exists(db_path):
        print(f"⚠️ Database file {db_path} not found!")
        alt_path = input("Enter the correct path to your database file: ")
        if os.path.exists(alt_path):
            return alt_path
        else:
            print(f"⚠️ Database file {alt_path} not found! Exiting.")
            sys.exit(1)
    return db_path

def create_variant_tables():
    """Create all necessary tables for the variant system"""
    print("Creating or updating variant system tables...")
    result = ProductAttribute.create_tables()
    if result:
        print("✓ Variant tables created or updated successfully")
    else:
        print("⚠️ Error creating variant tables")
    return result

def fix_misspelled_attributes():
    """Fix misspelled attribute values in the database"""
    print("Fixing misspelled attribute values...")
    
    # Common misspellings to fix
    corrections = [
        # Format: [wrong_value, correct_value]
        ["XI", "XL"],
        ["RFD", "RED"],
        ["BIACK", "BLACK"],
        ["BI ACK", "BLACK"],
        ["STROAGE", "STORAGE"]
    ]
    
    conn = get_connection()
    if not conn:
        print("⚠️ Could not connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Fix misspelled attribute values
        for wrong, correct in corrections:
            cursor.execute("""
                UPDATE ProductAttributeValues 
                SET value = ? 
                WHERE value = ?
            """, (correct, wrong))
            
            if cursor.rowcount > 0:
                print(f"✓ Fixed {cursor.rowcount} instances of '{wrong}' to '{correct}'")
        
        # Fix misspelled attribute names
        cursor.execute("""
            UPDATE ProductAttributes
            SET name = 'STORAGE'
            WHERE name = 'STROAGE'
        """)
        
        if cursor.rowcount > 0:
            print(f"✓ Fixed {cursor.rowcount} instances of 'STROAGE' to 'STORAGE'")
            
        # Commit changes
        conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error fixing misspelled attributes: {e}")
        return False
    finally:
        conn.close()

def update_variant_prices():
    """Update variant prices to reflect correct calculations"""
    print("Updating variant prices...")
    
    conn = get_connection()
    if not conn:
        print("⚠️ Could not connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get all variants
        cursor.execute("SELECT id, product_id FROM ProductVariants")
        variants = cursor.fetchall()
        
        updates = 0
        for variant in variants:
            variant_id = variant['id']
            product_id = variant['product_id']
            
            # Calculate correct price using our new system
            correct_price = get_variant_price_with_extras(variant_id)
            
            if correct_price is not None:
                # Update the variant price
                cursor.execute("""
                    UPDATE ProductVariants 
                    SET unit_price = ? 
                    WHERE id = ?
                """, (correct_price, variant_id))
                
                updates += 1
        
        print(f"✓ Updated prices for {updates} variants")
        
        # Commit changes
        conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error updating variant prices: {e}")
        return False
    finally:
        conn.close()

def fix_attribute_values():
    """Ensure all variants have proper attribute values"""
    print("Fixing variant attribute values...")
    
    conn = get_connection()
    if not conn:
        print("⚠️ Could not connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get all variants
        cursor.execute("SELECT id, name, product_id FROM ProductVariants")
        variants = cursor.fetchall()
        
        updates = 0
        for variant in variants:
            variant_id = variant['id']
            variant_name = variant['name']
            product_id = variant['product_id']
            
            # Extract attributes from name (e.g., "BLACK / XL")
            if variant_name and '/' in variant_name:
                parts = [part.strip() for part in variant_name.split('/')]
                
                # Get attribute names for this product
                cursor.execute("""
                    SELECT 
                        pa.name as attribute_name
                    FROM ProductTemplateAttributeLine ptal
                    JOIN ProductAttributes pa ON ptal.attribute_id = pa.id
                    WHERE ptal.product_id = ?
                """, (product_id,))
                
                attributes = cursor.fetchall()
                if not attributes or len(attributes) == 0:
                    continue
                
                attribute_names = [attr['attribute_name'] for attr in attributes]
                
                # Create attribute values dictionary from name parts
                attribute_values = {}
                
                # Handle case where attribute names are known
                if len(attribute_names) <= len(parts):
                    for i, attr_name in enumerate(attribute_names):
                        if i < len(parts):
                            attribute_values[attr_name] = parts[i]
                # Otherwise use generic attribute names
                else:
                    for i, part in enumerate(parts):
                        attribute_values[f"ATTRIBUTE_{i+1}"] = part
                
                # Store attribute values as JSON
                attribute_json = json.dumps(attribute_values)
                
                # Update the variant
                cursor.execute("""
                    UPDATE ProductVariants 
                    SET attribute_values = ?
                    WHERE id = ?
                """, (attribute_json, variant_id))
                
                updates += 1
        
        print(f"✓ Fixed attribute values for {updates} variants")
        
        # Commit changes
        conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error fixing attribute values: {e}")
        return False
    finally:
        conn.close()

def create_ui_integration_guide():
    """Create a guide for integrating the new variant UI"""
    guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variant_integration_guide.txt")
    
    guide_content = """
VARIANT SYSTEM INTEGRATION GUIDE
===============================

To complete the integration of the new variant system, follow these steps:

1. REPLACE THE VARIANT SELECTION DIALOG
--------------------------------------
In any file where you use the old variant dialog (like sales_management_windows.py), make these changes:

Find:
```python
from ui.variant_selection_dialog import VariantSelectionDialog
```

Replace with:
```python
from ui.improved_variant_dialog import ImprovedVariantSelectionDialog
```

Then find where the dialog is created:
```python
dialog = VariantSelectionDialog(product, self)
```

Replace with:
```python
dialog = ImprovedVariantSelectionDialog(product, self)
```

2. UPDATE PRICE CALCULATIONS
---------------------------
For any code that calculates variant prices, use the new method:

Add this import:
```python
from variant_manager import get_variant_price_with_extras
```

Then replace price calculations:
```python
# Old way
final_price = base_price + variant.get('price_adjustment', 0)

# New way
final_price = get_variant_price_with_extras(variant_id)
```

3. INITIALIZE THE SYSTEM IN main.py
---------------------------------
Make sure the system is initialized in your main.py:

```python
from models.product_attribute import ProductAttribute

# Add this after database initialization:
ProductAttribute.create_tables()
```

4. CREATE NEW VARIANTS CORRECTLY
------------------------------
When creating new variants, use the variant_manager:

```python
from variant_manager import create_variant_for_product, generate_all_variants_for_product

# To create a single variant:
variant_id = create_variant_for_product(
    product_id=1,
    attribute_values={"Color": "Red", "Size": "XL"},
    price_adjustment=10.0
)

# To generate all variants for a product:
variant_ids = generate_all_variants_for_product(product_id=1)
```

The data migration has been completed by the integration script, but these code changes
are required to ensure your application uses the new variant system going forward.
"""
    
    with open(guide_path, "w") as f:
        f.write(guide_content)
    
    print(f"✓ Created integration guide: {guide_path}")
    return guide_path

def main():
    print("=== New Variant System Integration ===")
    
    # Confirm before proceeding
    confirm = input("This script will modify your database to integrate the new variant system. Continue? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Check database path
    db_path = check_database_path()
    print(f"Using database at: {db_path}")
    
    # Create variant tables
    if not create_variant_tables():
        print("⚠️ Could not create variant tables. Exiting.")
        return
    
    # Fix misspelled attributes
    if not fix_misspelled_attributes():
        print("⚠️ Could not fix misspelled attributes. Continuing anyway...")
    
    # Update variant prices
    if not update_variant_prices():
        print("⚠️ Could not update variant prices. Continuing anyway...")
    
    # Fix attribute values
    if not fix_attribute_values():
        print("⚠️ Could not fix attribute values. Continuing anyway...")
    
    # Create integration guide
    guide_path = create_ui_integration_guide()
    
    print("\n=== Integration Complete ===")
    print("The new variant system has been integrated into your database.")
    print(f"Please follow the instructions in {guide_path} to complete the integration.")

if __name__ == "__main__":
    main()
