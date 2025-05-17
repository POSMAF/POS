from PyQt5.QtWidgets import QApplication
import sys
import os
from ui.login_window import LoginWindow
from controllers.auth_controller import AuthController
from models.user import User
from models.product import Product
from models.category import Category
from database import initialize_database
from datetime import datetime

def init_admin_user():
    """Initialize the default admin user if it doesn't exist."""
    admin_user = User.get_user_by_username("MAFPOS")
    if not admin_user:
        # Create default admin user
        default_admin = User(
            username="MAFPOS",
            password="admin123",
            role="admin",  # Use lowercase to match database constraint
            active=1
        )
        if User.add_user(default_admin):
            print("Default admin user created successfully.")
        else:
            print("Failed to create default admin user.")
    else:
        print("Default admin user already exists.")

def main():
    print("Starting application...")

    # Initialize database
    initialize_database()

    # Create tables
    User.create_table()
    Product.create_tables()
    Category.initialize_database()
    
    # Initialize product attribute tables for variants
    try:
        from models.product_attribute import ProductAttribute
        ProductAttribute.create_tables()
        print("✅ Product tables updated successfully")
    except Exception as e:
        print(f"⚠️ Error initializing product attribute tables: {e}")
    
    # Initialize payment tables for multiple payment methods
    try:
        from models.payment import Payment
        Payment.create_tables()
        print("✅ Payment tables created successfully")
    except Exception as e:
        print(f"⚠️ Error initializing payment tables: {e}")
        
    print("Database tables created or verified.")

    # Initialize admin user
    init_admin_user()
    
    # Patch missing window classes to fix module issues
    try:
        from ui.missing_class_patcher import patch_all_modules
        patch_all_modules()
    except Exception as e:
        print(f"⚠️ Error patching window classes: {e}")

    # Create images directory if it doesn't exist
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # Start the application
    app = QApplication(sys.argv)
    
    # Set current date/time format
    try:
        # Try using the newer Python 3.11+ approach
        current_datetime = datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    except AttributeError:
        # Fall back to the older method for compatibility
        current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Date and Time (UTC): {current_datetime}")
    
    print("Launching login window...")
    login_window = LoginWindow(auth_controller=AuthController())
    login_window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()