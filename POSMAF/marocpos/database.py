import sqlite3
import os
from datetime import datetime, UTC

class DatabaseManager:
    # Get the absolute path to the marocpos directory
    MAROCPOS_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(MAROCPOS_DIR, "pos7.db")

    @classmethod
    def get_connection(cls):
        """Create and return a connection to the SQLite database."""
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None

    @classmethod
    def get_current_datetime(cls):
        """Get current UTC datetime in YYYY-MM-DD HH:MM:SS format."""
        return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

def get_connection():
    """Wrapper function for backward compatibility."""
    return DatabaseManager.get_connection()

def initialize_database():
    """Initialize the database by creating required tables if they don't exist."""
    connection = get_connection()
    if not connection:
        print("Failed to connect to the database. Initialization aborted.")
        return False

    cursor = connection.cursor()

    schema = """
    CREATE TABLE IF NOT EXISTS Stores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS Categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        parent_id INTEGER,
        image_path TEXT,
        tax_rate REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES Categories(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        barcode TEXT UNIQUE,
        unit_price REAL NOT NULL,
        purchase_price REAL DEFAULT 0,
        profit_margin REAL,
        stock INTEGER NOT NULL DEFAULT 0,
        min_stock INTEGER DEFAULT 0,
        reorder_point INTEGER DEFAULT 0,
        category_id INTEGER,
        image_path TEXT,
        unit TEXT DEFAULT 'piece',
        weight REAL,
        volume REAL,
        status TEXT DEFAULT 'available',
        product_type TEXT DEFAULT 'stockable',
        valuation_method TEXT DEFAULT 'FIFO',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES Categories(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS ProductAttributes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        display_type TEXT DEFAULT 'radio' CHECK(display_type IN ('radio', 'select', 'color', 'pills')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
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
    );
    
    CREATE TABLE IF NOT EXISTS ProductTemplateAttributeLine (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        attribute_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
        FOREIGN KEY (attribute_id) REFERENCES ProductAttributes(id) ON DELETE CASCADE,
        UNIQUE(product_id, attribute_id)
    );
    
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
    );
    
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
    );
    
    CREATE TABLE IF NOT EXISTS ProductVariants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        barcode TEXT UNIQUE,
        unit_price REAL,
        purchase_price REAL,
        stock INTEGER DEFAULT 0,
        attributes TEXT,
        sku TEXT,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS StockMovements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        variant_id INTEGER,
        movement_type TEXT CHECK(movement_type IN ('in', 'out', 'adjustment')),
        quantity INTEGER NOT NULL,
        unit_price REAL,
        reference TEXT,
        notes TEXT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
        FOREIGN KEY (variant_id) REFERENCES ProductVariants(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES Users(id)
    );

    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'cashier', 'manager')),
        full_name TEXT,
        email TEXT,
        phone TEXT,
        active INTEGER DEFAULT 1,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS Sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        discount REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        final_total REAL NOT NULL,
        payment_method TEXT DEFAULT 'CASH',
        payment_status TEXT DEFAULT 'COMPLETED',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(id)
    );

    CREATE TABLE IF NOT EXISTS SaleItems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        variant_id INTEGER,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sale_id) REFERENCES Sales(id),
        FOREIGN KEY (product_id) REFERENCES Products(id),
        FOREIGN KEY (variant_id) REFERENCES ProductVariants(id)
    );

    CREATE TABLE IF NOT EXISTS Cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        variant_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(id),
        FOREIGN KEY (product_id) REFERENCES Products(id),
        FOREIGN KEY (variant_id) REFERENCES ProductVariants(id)
    );

    CREATE TABLE IF NOT EXISTS Settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        value TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS Expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        date DATE NOT NULL,
        category TEXT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(id)
    );

    CREATE TABLE IF NOT EXISTS Suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ProductSuppliers (
        product_id INTEGER,
        supplier_id INTEGER,
        price REAL,
        lead_time INTEGER,
        minimum_order INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (product_id, supplier_id),
        FOREIGN KEY (product_id) REFERENCES Products(id),
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
    );
    """

    try:
        # Create tables
        cursor.executescript(schema)

        # Check if admin user exists, if not create it
        cursor.execute("SELECT COUNT(*) FROM Users WHERE username = ?", ('MAFPOS',))
        if cursor.fetchone()[0] == 0:
            current_time = DatabaseManager.get_current_datetime()
            cursor.execute("""
                INSERT INTO Users (
                    username, password, role, full_name, active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, ('MAFPOS', 'admin123', 'admin', 'Administrator', 1, current_time))

        # Initialize default settings
        default_settings = [
            ('store_name', 'My Store', 'Store name'),
            ('store_address', '', 'Store address'),
            ('store_phone', '', 'Store phone number'),
            ('store_email', '', 'Store email'),
            ('tax_rate', '0', 'Default tax rate'),
            ('currency', 'MAD', 'Store currency'),
            ('receipt_footer', 'Thank you for your purchase!', 'Receipt footer message'),
            ('default_product_type', 'stockable', 'Default product type'),
            ('default_valuation_method', 'FIFO', 'Default stock valuation method'),
            ('low_stock_alert', 'true', 'Enable low stock alerts'),
            ('auto_reorder', 'false', 'Enable automatic reordering'),
            ('default_unit', 'piece', 'Default unit of measure'),
            ('receipt_printer_type', 'thermal', 'Receipt printer type (thermal/A4)'),
            ('receipt_logo_path', '', 'Path to receipt logo image')
        ]

        for key, value, description in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO Settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))

        connection.commit()
        print("✅ Base de données initialisée avec succès.\n")

        # Print database info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📦 Tables existantes:")
        for table in tables:
            print(f"- {table[0]}")

        cursor.execute("SELECT name FROM Categories")
        categories = cursor.fetchall()
        print("\n📁 Catégories existantes:")
        for category in categories:
            print(f"- {category[0]}")

        print("\n✅ Tables créées ou vérifiées.")
        print("✅ Utilisateur admin par défaut existant.")
        return True

    except sqlite3.Error as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données : {e}")
        return False

    finally:
        if connection:
            connection.close()

def reset_database():
    """Reset the database by deleting and recreating it."""
    try:
        if os.path.exists(DatabaseManager.DB_PATH):
            os.remove(DatabaseManager.DB_PATH)
            print("🗑️ Ancienne base de données supprimée.")
        return initialize_database()
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation : {e}")
        return False