#!/usr/bin/env python3
"""
Standalone Example Script for Variant Dashboard

This script demonstrates the variant dashboard without requiring integration
with your existing application. It creates a simple window with a button
that opens the dashboard for a product.

Usage:
    python show_dashboard_example.py

Note: You may need to adjust the product_id in this example to match an
actual product ID in your database.
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QLabel, QWidget, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our variant dashboard
from ui.variant_dashboard import VariantDashboard
from database import get_connection


class DashboardExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_products()
        
    def init_ui(self):
        self.setWindowTitle("Variant Dashboard Example")
        self.setGeometry(100, 100, 400, 200)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Exemple de Tableau de Bord des Variantes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title)
        
        # Product selector
        layout.addWidget(QLabel("Sélectionnez un produit:"))
        self.product_combo = QComboBox()
        layout.addWidget(self.product_combo)
        
        # Button to open dashboard
        open_btn = QPushButton("🧩 Ouvrir le Tableau de Bord des Variantes")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #5e72e4;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                margin: 20px 0;
            }
            QPushButton:hover {
                background-color: #324cdd;
            }
        """)
        open_btn.clicked.connect(self.open_dashboard)
        layout.addWidget(open_btn)
        
        # Instructions
        instructions = QLabel(
            "Ce script est un exemple qui montre comment ouvrir le tableau de bord "
            "des variantes pour un produit sélectionné.\n\n"
            "Pour intégrer cette fonctionnalité dans votre application, suivez les "
            "instructions fournies dans le chat."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(instructions)
    
    def load_products(self):
        """Load products into the combo box"""
        try:
            from models.product import Product
            
            # Get all products
            products = Product.get_all_products()
            
            if not products:
                self.product_combo.addItem("Aucun produit trouvé", None)
                return
            
            # Add products to combo box
            for product in products:
                self.product_combo.addItem(
                    f"{product['id']} - {product['name']}", 
                    product['id']
                )
        except Exception as e:
            self.product_combo.clear()
            self.product_combo.addItem(f"Erreur: {str(e)}", None)
    
    def open_dashboard(self):
        """Open the variant dashboard for the selected product"""
        product_id = self.product_combo.currentData()
        
        if not product_id:
            QMessageBox.warning(
                self,
                "Aucun produit sélectionné",
                "Veuillez sélectionner un produit valide."
            )
            return
        
        try:
            # Create and show the dashboard
            dashboard = VariantDashboard(product_id, self)
            dashboard.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture du tableau de bord: {str(e)}"
            )


def main():
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = DashboardExample()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
