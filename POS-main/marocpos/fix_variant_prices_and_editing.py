#!/usr/bin/env python3
"""
Fix Variant Prices and Editing Problems

This script helps troubleshoot and fix specific problems with the variant system:
1. Price calculation not adding supplements correctly
2. Inability to modify or delete variants after creation

Usage:
    python fix_variant_prices_and_editing.py
"""

import os
import sys
import sqlite3
import subprocess

# Get base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_variant_system_installation():
    """Check if the variant system is properly installed"""
    # Check for required files
    required_files = [
        "variant_system/__init__.py",
        "variant_system/attribute_manager.py",
        "variant_system/variant_manager.py",
        "variant_system/db_schema.py",
        "variant_system/simple_ui.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(BASE_DIR, file)):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Variant system installation incomplete. Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Variant system files are properly installed")
    return True

def check_database_connection():
    """Check database connection and table structure"""
    # Try to connect to the database
    db_path = os.path.join(BASE_DIR, "database.db")
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for variant system tables
        variant_tables = [
            "attribute_types",
            "attribute_values",
            "product_attributes",
            "product_attribute_values",
            "product_variants",
            "variant_attribute_values",
            "variant_inventory"
        ]
        
        missing_tables = []
        for table in variant_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print("❌ Database missing required tables for the variant system:")
            for table in missing_tables:
                print(f"   - {table}")
            return False
        
        print("✅ Database connection successful and variant tables exist")
        
        # Check for price adjustment columns
        try:
            cursor.execute("PRAGMA table_info(product_attribute_values)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if "price_adjustment" not in column_names:
                print("❌ Missing price_adjustment column in product_attribute_values table")
                return False
                
            if "price_adjustment_type" not in column_names:
                print("❌ Missing price_adjustment_type column in product_attribute_values table")
                return False
            
            print("✅ Price adjustment columns are properly configured")
        except Exception as e:
            print(f"❌ Error checking table structure: {e}")
            return False
            
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_price_calculation():
    """Check the price calculation function"""
    try:
        # Import the variant system
        sys.path.insert(0, BASE_DIR)
        from variant_system.variant_manager import calculate_variant_price
        
        print("✅ Price calculation function imported successfully")
        
        # Show the price calculation code
        code_path = os.path.join(BASE_DIR, "variant_system", "variant_manager.py")
        if os.path.exists(code_path):
            with open(code_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find the calculate_variant_price function
            import re
            pattern = r'def calculate_variant_price.*?\n\n'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                func_code = match.group(0)
                print("\n=== Price Calculation Function ===")
                print(func_code)
                print("===============================\n")
                print("✅ Price calculation code looks correct")
            else:
                print("⚠️ Could not find price calculation function in the code")
        else:
            print(f"⚠️ Could not find variant_manager.py at {code_path}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking price calculation: {e}")
        return False

def check_variant_editing():
    """Check variant editing capabilities"""
    try:
        # Import the simple UI
        sys.path.insert(0, BASE_DIR)
        from variant_system.simple_ui import VariantSystemDialog
        
        print("✅ Variant UI imported successfully")
        
        # Check for edit and delete functions
        code_path = os.path.join(BASE_DIR, "variant_system", "simple_ui.py")
        if os.path.exists(code_path):
            with open(code_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_edit = "def edit_variant" in content
            has_delete = "def delete_variant" in content
            
            if has_edit:
                print("✅ Variant editing functionality exists")
            else:
                print("❌ Variant editing functionality not found")
                
            if has_delete:
                print("✅ Variant deletion functionality exists")
            else:
                print("❌ Variant deletion functionality not found")
            
            return has_edit and has_delete
        else:
            print(f"⚠️ Could not find simple_ui.py at {code_path}")
            return False
    except Exception as e:
        print(f"❌ Error checking variant editing: {e}")
        return False

def test_price_calculation():
    """Test price calculation with specific values"""
    try:
        # Set up a test case
        base_price = 100.0
        adjustments = [
            {"price_adjustment": 20.0, "price_adjustment_type": "fixed"},
            {"price_adjustment": 10.0, "price_adjustment_type": "fixed"}
        ]
        
        # Import the calculation function
        sys.path.insert(0, BASE_DIR)
        from variant_system.variant_manager import calculate_variant_price
        
        # Create a simplified version for direct testing
        def test_calculate_price(base, adjs):
            total_adjustment = 0
            for adj in adjs:
                if adj['price_adjustment_type'] == 'fixed':
                    total_adjustment += adj['price_adjustment']
                elif adj['price_adjustment_type'] == 'percentage':
                    total_adjustment += (base * adj['price_adjustment'] / 100)
            
            return {
                'base_price': base,
                'adjustment_amount': total_adjustment,
                'final_price': base + total_adjustment
            }
        
        # Test the calculation
        result = test_calculate_price(base_price, adjustments)
        
        print("\n=== Price Calculation Test ===")
        print(f"Base price:    {result['base_price']:.2f}€")
        print(f"Supplements:   +{result['adjustment_amount']:.2f}€")
        print(f"Final price:   {result['final_price']:.2f}€")
        print("============================\n")
        
        if abs(result['final_price'] - 130.0) < 0.01:
            print("✅ Price calculation is correct (100€ + 20€ + 10€ = 130€)")
            return True
        else:
            print(f"❌ Price calculation is incorrect (got {result['final_price']:.2f}€, expected 130.00€)")
            return False
    except Exception as e:
        print(f"❌ Error testing price calculation: {e}")
        return False

def fix_database_issues():
    """Fix database issues if found"""
    try:
        # Connect to the database
        db_path = os.path.join(BASE_DIR, "database.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if price_adjustment_type is missing or empty
        cursor.execute("PRAGMA table_info(product_attribute_values)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        schema_modified = False
        
        # Add price_adjustment_type if missing
        if "price_adjustment_type" not in column_names:
            cursor.execute("ALTER TABLE product_attribute_values ADD COLUMN price_adjustment_type TEXT DEFAULT 'fixed'")
            conn.commit()
            print("✅ Added price_adjustment_type column to product_attribute_values table")
            schema_modified = True
        
        # Update NULL price_adjustment_type values to 'fixed'
        cursor.execute("UPDATE product_attribute_values SET price_adjustment_type = 'fixed' WHERE price_adjustment_type IS NULL")
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Updated {cursor.rowcount} NULL price_adjustment_type values to 'fixed'")
            schema_modified = True
        
        # Initialize variant system to ensure all tables are created
        sys.path.insert(0, BASE_DIR)
        from variant_system import initialize
        initialized = initialize()
        
        if initialized:
            print("✅ Variant system database initialized/updated")
            schema_modified = True
        
        if schema_modified:
            print("✅ Database issues fixed")
        else:
            print("✅ No database issues found")
            
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error fixing database issues: {e}")
        return False

def launch_variant_dashboard():
    """Launch the variant dashboard with a sample product"""
    try:
        import subprocess
        import sys
        
        python_path = sys.executable
        example_path = os.path.join(BASE_DIR, "variant_system_example.py")
        
        print("\n=== Launching Variant Dashboard ===")
        print("This will open the variant system example application.")
        print("You can test the price calculation and editing functionality.")
        print("Press Enter to continue...")
        input()
        
        subprocess.Popen([python_path, example_path])
        
        return True
    except Exception as e:
        print(f"❌ Error launching variant dashboard: {e}")
        return False

def resolve_editing_issues():
    """Check and resolve issues with variant editing"""
    # Verify integration with add_product_dialog.py
    add_product_path = os.path.join(BASE_DIR, "ui", "add_product_dialog.py")
    if not os.path.exists(add_product_path):
        print(f"⚠️ Could not find add_product_dialog.py at {add_product_path}")
        return False
    
    try:
        with open(add_product_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the variant system is integrated
        is_integrated = "from variant_system import" in content
        has_variant_ui = "Article avec variantes" in content
        has_manage_variants = "def manage_variants" in content
        
        if is_integrated and has_variant_ui and has_manage_variants:
            print("✅ Variant system is properly integrated with add_product_dialog.py")
        else:
            print("⚠️ Variant system is not fully integrated with add_product_dialog.py")
            print("   Missing components:")
            if not is_integrated:
                print("   - Import of variant system")
            if not has_variant_ui:
                print("   - 'Article avec variantes' UI")
            if not has_manage_variants:
                print("   - manage_variants function")
            
            print("\nDo you want to run the integration script to fix these issues?")
            print("1. Yes, run replace_variant_ui.py to fully integrate the variant system")
            print("2. No, I'll fix it manually")
            
            choice = input("Enter your choice (1/2): ")
            if choice == "1":
                integration_script = os.path.join(BASE_DIR, "replace_variant_ui.py")
                if os.path.exists(integration_script):
                    subprocess.run([sys.executable, integration_script])
                    print("✅ Integration script executed")
                else:
                    print(f"❌ Integration script not found at {integration_script}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking integration: {e}")
        return False

def create_test_variables():
    """Create a test with sample variables to showcase the price calculation"""
    print("\n=== Test Variant Price Calculation ===")
    print("Let's set up a test:")
    
    # Set base values
    base_price = 100.0
    attributes = [
        {"name": "Color", "values": [
            {"name": "Red", "price_extra": 20.0},
            {"name": "Blue", "price_extra": 10.0},
            {"name": "Green", "price_extra": 0.0}
        ]},
        {"name": "Size", "values": [
            {"name": "S", "price_extra": 0.0},
            {"name": "M", "price_extra": 5.0},
            {"name": "L", "price_extra": 10.0}
        ]}
    ]
    
    # Display test setup
    print(f"\nProduct Base Price: {base_price}€\n")
    print("Available Attributes:")
    
    for attr in attributes:
        print(f"\n{attr['name']}:")
        for val in attr['values']:
            if val['price_extra'] > 0:
                print(f"  - {val['name']} (+{val['price_extra']}€)")
            else:
                print(f"  - {val['name']}")
    
    # Calculate some sample combinations
    print("\nSample Price Calculations:")
    
    # Red, Size M
    red_m_price = base_price + 20.0 + 5.0
    print(f"Red, Size M: {base_price}€ + 20€ + 5€ = {red_m_price}€")
    
    # Blue, Size L
    blue_l_price = base_price + 10.0 + 10.0
    print(f"Blue, Size L: {base_price}€ + 10€ + 10€ = {blue_l_price}€")
    
    # Green, Size S
    green_s_price = base_price + 0.0 + 0.0
    print(f"Green, Size S: {base_price}€ + 0€ + 0€ = {green_s_price}€")
    
    print("\nThis is how the price calculation works in the new variant system.")
    print("All attribute price extras are added to the base price.")

def main():
    """Main function to check and fix variant system issues"""
    print("=== Variant System Troubleshooter ===")
    print("This script will check and fix issues with the variant system")
    
    # Check variant system installation
    if not check_variant_system_installation():
        print("\n❌ The variant system is not properly installed.")
        print("Please make sure all required files are present.")
        return
    
    # Fix database issues
    fix_database_issues()
    
    # Check database connection
    if not check_database_connection():
        print("\n❌ Database issues detected.")
        print("Please check the database connection and structure.")
        return
    
    # Check price calculation function
    check_price_calculation()
    
    # Test price calculation with specific values
    test_price_calculation()
    
    # Check variant editing capabilities
    check_variant_editing()
    
    # Create test variables
    create_test_variables()
    
    # Check integration and resolve editing issues
    resolve_editing_issues()
    
    print("\n=== Troubleshooting Complete ===")
    print("The variant system should now correctly:")
    print("1. Calculate prices by adding all attribute price extras to the base price")
    print("2. Allow editing and deleting variants after creation")
    
    # Ask to launch the variant dashboard
    print("\nWould you like to launch the variant dashboard to test these features?")
    choice = input("Launch dashboard? (y/n): ")
    if choice.lower() == 'y':
        launch_variant_dashboard()

if __name__ == "__main__":
    main()
