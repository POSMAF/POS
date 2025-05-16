"""
Database Schema for Advanced Variant System

This module defines the database schema for the new variant system,
including tables for attributes, variants, rules, pricing, and inventory.
"""

from database import get_connection

def create_variant_system_tables():
    """Create all necessary tables for the variant system"""
    conn = get_connection()
    if not conn:
        print("❌ Database connection failed")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # ===== Attribute Management =====
        
        # Attribute Types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AttributeTypes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT,
                display_type TEXT NOT NULL DEFAULT 'select' CHECK(display_type IN ('select', 'radio', 'color', 'image', 'text', 'number')),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Attribute Values
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AttributeValues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attribute_type_id INTEGER NOT NULL,
                value TEXT NOT NULL,
                display_value TEXT NOT NULL,
                description TEXT,
                html_color TEXT,
                image_path TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attribute_type_id) REFERENCES AttributeTypes(id) ON DELETE CASCADE,
                UNIQUE(attribute_type_id, value)
            )
        """)
        
        # ===== Product Attribute Association =====
        
        # Product Attribute Link
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ProductAttributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                attribute_type_id INTEGER NOT NULL,
                is_required BOOLEAN NOT NULL DEFAULT 1,
                affects_price BOOLEAN NOT NULL DEFAULT 1,
                affects_inventory BOOLEAN NOT NULL DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
                FOREIGN KEY (attribute_type_id) REFERENCES AttributeTypes(id) ON DELETE CASCADE,
                UNIQUE(product_id, attribute_type_id)
            )
        """)
        
        # Product Attribute Values
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ProductAttributeValues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_attribute_id INTEGER NOT NULL,
                attribute_value_id INTEGER NOT NULL,
                price_adjustment REAL DEFAULT 0,
                price_adjustment_type TEXT DEFAULT 'fixed' CHECK(price_adjustment_type IN ('fixed', 'percentage')),
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_attribute_id) REFERENCES ProductAttributes(id) ON DELETE CASCADE,
                FOREIGN KEY (attribute_value_id) REFERENCES AttributeValues(id) ON DELETE CASCADE,
                UNIQUE(product_attribute_id, attribute_value_id)
            )
        """)
        
        # ===== Variant Management =====
        
        # Product Variants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ProductVariants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                sku TEXT,
                barcode TEXT,
                name TEXT,
                description TEXT,
                image_path TEXT,
                base_price REAL,
                final_price REAL,
                cost_price REAL,
                weight REAL,
                dimensions TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE
            )
        """)
        
        # Variant Attribute Values
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VariantAttributeValues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variant_id INTEGER NOT NULL,
                attribute_value_id INTEGER NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (variant_id) REFERENCES ProductVariants(id) ON DELETE CASCADE,
                FOREIGN KEY (attribute_value_id) REFERENCES AttributeValues(id) ON DELETE CASCADE,
                UNIQUE(variant_id, attribute_value_id)
            )
        """)
        
        # ===== Inventory Management =====
        
        # Variant Inventory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VariantInventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variant_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                reserved_quantity INTEGER NOT NULL DEFAULT 0,
                reorder_level INTEGER DEFAULT 0,
                reorder_quantity INTEGER DEFAULT 0,
                location TEXT,
                last_counted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (variant_id) REFERENCES ProductVariants(id) ON DELETE CASCADE,
                UNIQUE(variant_id)
            )
        """)
        
        # Inventory Movements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS InventoryMovements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variant_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                movement_type TEXT NOT NULL CHECK(movement_type IN ('purchase', 'sale', 'adjustment', 'transfer', 'return')),
                reference_id INTEGER,
                notes TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (variant_id) REFERENCES ProductVariants(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE SET NULL
            )
        """)
        
        # ===== Attribute Rules =====
        
        # Attribute Compatibility Rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AttributeRules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                rule_type TEXT NOT NULL CHECK(rule_type IN ('compatibility', 'dependency', 'exclusion')),
                primary_attribute_id INTEGER NOT NULL,
                primary_value_id INTEGER,
                secondary_attribute_id INTEGER NOT NULL,
                secondary_value_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
                FOREIGN KEY (primary_attribute_id) REFERENCES AttributeTypes(id) ON DELETE CASCADE,
                FOREIGN KEY (primary_value_id) REFERENCES AttributeValues(id) ON DELETE CASCADE,
                FOREIGN KEY (secondary_attribute_id) REFERENCES AttributeTypes(id) ON DELETE CASCADE,
                FOREIGN KEY (secondary_value_id) REFERENCES AttributeValues(id) ON DELETE CASCADE
            )
        """)
        
        # Commit all changes
        cursor.execute("COMMIT")
        print("✅ Created variant system tables successfully")
        return True
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ Error creating variant system tables: {e}")
        return False
    finally:
        conn.close()

# Create some initial attribute types and values for testing
def create_sample_data():
    """Create sample attribute types and values for testing"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if we already have attribute types
        cursor.execute("SELECT COUNT(*) FROM AttributeTypes")
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Skip if we already have data
            return True
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Size attribute type
        cursor.execute("""
            INSERT INTO AttributeTypes (name, display_name, description, display_type)
            VALUES ('size', 'Taille', 'Taille du produit', 'select')
        """)
        size_id = cursor.lastrowid
        
        # Size values
        size_values = [
            ('xs', 'XS', 'Très petit'),
            ('s', 'S', 'Petit'),
            ('m', 'M', 'Moyen'),
            ('l', 'L', 'Grand'),
            ('xl', 'XL', 'Très grand'),
            ('xxl', 'XXL', 'Extra grand')
        ]
        
        for i, (value, display, desc) in enumerate(size_values):
            cursor.execute("""
                INSERT INTO AttributeValues (attribute_type_id, value, display_value, description, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (size_id, value, display, desc, i))
        
        # Color attribute type
        cursor.execute("""
            INSERT INTO AttributeTypes (name, display_name, description, display_type)
            VALUES ('color', 'Couleur', 'Couleur du produit', 'color')
        """)
        color_id = cursor.lastrowid
        
        # Color values
        color_values = [
            ('black', 'Noir', 'Noir', '#000000'),
            ('white', 'Blanc', 'Blanc', '#FFFFFF'),
            ('red', 'Rouge', 'Rouge', '#FF0000'),
            ('blue', 'Bleu', 'Bleu', '#0000FF'),
            ('green', 'Vert', 'Vert', '#00FF00'),
            ('yellow', 'Jaune', 'Jaune', '#FFFF00')
        ]
        
        for i, (value, display, desc, color) in enumerate(color_values):
            cursor.execute("""
                INSERT INTO AttributeValues (attribute_type_id, value, display_value, description, html_color, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (color_id, value, display, desc, color, i))
        
        # Material attribute type
        cursor.execute("""
            INSERT INTO AttributeTypes (name, display_name, description, display_type)
            VALUES ('material', 'Matériau', 'Matériau du produit', 'select')
        """)
        material_id = cursor.lastrowid
        
        # Material values
        material_values = [
            ('cotton', 'Coton', 'Coton'),
            ('polyester', 'Polyester', 'Polyester'),
            ('leather', 'Cuir', 'Cuir véritable'),
            ('wool', 'Laine', 'Laine'),
            ('silk', 'Soie', 'Soie')
        ]
        
        for i, (value, display, desc) in enumerate(material_values):
            cursor.execute("""
                INSERT INTO AttributeValues (attribute_type_id, value, display_value, description, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (material_id, value, display, desc, i))
        
        # Commit transaction
        cursor.execute("COMMIT")
        print("✅ Created sample attribute data")
        return True
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ Error creating sample data: {e}")
        return False
    finally:
        conn.close()

# Initialize the database schema
def initialize_database():
    """Initialize the variant system database schema and sample data"""
    success = create_variant_system_tables()
    if success:
        create_sample_data()
    return success

if __name__ == "__main__":
    initialize_database()
