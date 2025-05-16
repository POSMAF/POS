from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox, QComboBox, QInputDialog
)
import sqlite3


class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Set dialog properties
        self.setWindowTitle("Add Item to Cart")
        self.setGeometry(300, 200, 400, 250)

        # Create a database connection
        self.conn = sqlite3.connect("pos2.db")
        self.cursor = self.conn.cursor()

        # Layout
        layout = QVBoxLayout()

        # Product Dropdown
        self.product_dropdown = QComboBox(self)
        self.load_products()
        layout.addWidget(QLabel("Select Product:"))
        layout.addWidget(self.product_dropdown)

        # Quantity Input
        self.quantity_input = QLineEdit(self)
        self.quantity_input.setPlaceholderText("Enter quantity")
        layout.addWidget(QLabel("Quantity:"))
        layout.addWidget(self.quantity_input)

        # Buttons
        button_layout = QHBoxLayout()
        add_product_button = QPushButton("Create New Product")
        save_button = QPushButton("Add Item to Cart")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(add_product_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Connect buttons
        add_product_button.clicked.connect(self.create_product)
        save_button.clicked.connect(self.add_item)
        cancel_button.clicked.connect(self.reject)

        # Set layout
        self.setLayout(layout)

    def load_products(self):
        """Load products from the database into the dropdown."""
        self.cursor.execute("SELECT id, name FROM Products")
        products = self.cursor.fetchall()
        self.product_dropdown.clear()  # Clear any existing items
        if not products:
            QMessageBox.warning(self, "No Products", "No products available. Please create a new product.")
        else:
            for product_id, name in products:
                self.product_dropdown.addItem(name, product_id)

    def create_product(self):
        """Open a dialog to create a new product."""
        # Get product name
        product_name, ok = QInputDialog.getText(self, "New Product", "Enter product name:")
        if not ok or not product_name.strip():
            return  # User canceled or entered an empty name

        try:
            # Get unit price
            unit_price, ok = QInputDialog.getDouble(self, "New Product", "Enter unit price:", decimals=2)
            if not ok or unit_price <= 0:
                QMessageBox.warning(self, "Invalid Input", "Unit price must be greater than 0.")
                return

            # Get stock quantity
            stock, ok = QInputDialog.getInt(self, "New Product", "Enter stock quantity:", min=1)
            if not ok or stock <= 0:
                QMessageBox.warning(self, "Invalid Input", "Stock quantity must be greater than 0.")
                return

            # Insert the new product into the database
            self.cursor.execute(
                "INSERT INTO Products (name, unit_price, stock) VALUES (?, ?, ?)",
                (product_name.strip(), unit_price, stock)
            )
            self.conn.commit()

            QMessageBox.information(self, "Success", f"Product '{product_name}' added successfully!")
            self.load_products()  # Reload the dropdown to include the new product

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "A product with this name already exists.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def add_item(self):
        """Add the selected item to the cart."""
        product_id = self.product_dropdown.currentData()
        quantity = self.quantity_input.text().strip()

        if not quantity:
            QMessageBox.warning(self, "Error", "Quantity is required.")
            return

        try:
            quantity = int(quantity)
        except ValueError:
            QMessageBox.warning(self, "Error", "Quantity must be an integer.")
            return

        if quantity <= 0:
            QMessageBox.warning(self, "Error", "Quantity must be greater than 0.")
            return

        # Fetch product details
        self.cursor.execute("SELECT unit_price, stock FROM Products WHERE id = ?", (product_id,))
        product = self.cursor.fetchone()
        if product is None:
            QMessageBox.warning(self, "Error", "Selected product not found.")
            return

        unit_price, stock = product
        if quantity > stock:
            QMessageBox.warning(self, "Error", f"Insufficient stock. Available: {stock}")
            return

        total_price = quantity * unit_price
        self.product_data = {
            "product_id": product_id,
            "quantity": quantity,
            "total_price": total_price,
        }

        # Update stock in the database
        self.cursor.execute(
            "UPDATE Products SET stock = stock - ? WHERE id = ?", (quantity, product_id)
        )
        self.conn.commit()

        self.accept()