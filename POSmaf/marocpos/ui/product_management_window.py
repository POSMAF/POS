from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox, QLineEdit,
    QSpinBox, QDoubleSpinBox, QFrame, QCheckBox, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from models.product import Product
from models.category import Category
import json
import os

class ProductManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_products()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Gestion des produits")
        self.setGeometry(100, 100, 1200, 800)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Search and filter section
        top_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("Rechercher:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom de produit, code-barres...")
        self.search_input.textChanged.connect(self.filter_products)
        
        # Category filter
        category_label = QLabel("Catégorie:")
        self.category_filter = QComboBox()
        self.category_filter.currentIndexChanged.connect(self.filter_products)
        
        # Add New Product button
        add_product_btn = QPushButton("+ Ajouter un produit")
        add_product_btn.clicked.connect(self.add_product)
        add_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        # Import/Export button
        import_export_btn = QPushButton("Importer/Exporter")
        import_export_btn.clicked.connect(self.open_import_export)
        import_export_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        # Add widgets to top layout
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(category_label)
        top_layout.addWidget(self.category_filter)
        top_layout.addStretch()
        top_layout.addWidget(import_export_btn)
        top_layout.addWidget(add_product_btn)
        
        main_layout.addLayout(top_layout)

        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(12)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Image", "Code-barres", "Nom", "Prix vente", "Prix achat", 
            "Stock", "Stock min", "Catégorie", "Variantes", "Marge", "Actions"
        ])

        # Set column widths
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(11, QHeaderView.Fixed)
        
        self.products_table.setColumnWidth(0, 50)  # ID
        self.products_table.setColumnWidth(1, 70)  # Image
        self.products_table.setColumnWidth(2, 100) # Barcode
        # Column 3 (Name) is set to stretch
        self.products_table.setColumnWidth(4, 80)  # Sell price
        self.products_table.setColumnWidth(5, 80)  # Purchase price
        self.products_table.setColumnWidth(6, 60)  # Stock
        self.products_table.setColumnWidth(7, 60)  # Min stock
        self.products_table.setColumnWidth(8, 120) # Category
        self.products_table.setColumnWidth(9, 120) # Variants
        self.products_table.setColumnWidth(10, 80) # Margin
        self.products_table.setColumnWidth(11, 180) # Actions
        
        main_layout.addWidget(self.products_table)
        
        # Status bar
        self.status_label = QLabel("Chargement des produits...")
        main_layout.addWidget(self.status_label)

        # Load categories for filter
        self.load_categories()

    def load_categories(self):
        """Load categories for the category filter"""
        # Clear the combo box
        self.category_filter.clear()
        
        # Add "All Categories" option
        self.category_filter.addItem("Toutes les catégories", None)
        
        # Get all categories
        categories = Category.get_all_categories()
        
        # Add each category to combo box
        for category in categories:
            self.category_filter.addItem(category[1], category[0])

    def load_products(self):
        """Load products into the table"""
        try:
            # Get all products
            products = Product.get_all_products()
            
            # Clear table
            self.products_table.setRowCount(0)
            
            # Set row count
            self.products_table.setRowCount(len(products))
            
            # Fill table with products
            for row, product in enumerate(products):
                # ID Column
                id_item = QTableWidgetItem(str(product['id']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 0, id_item)
                
                # Image Column
                image_cell = QTableWidgetItem("")
                
                if product.get('image_path') and os.path.exists(product['image_path']):
                    # Create a small pixmap for the thumbnail
                    pixmap = QPixmap(product['image_path'])
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        image_cell.setData(Qt.DecorationRole, scaled_pixmap)
                
                self.products_table.setItem(row, 1, image_cell)
                
                # Barcode Column
                barcode_item = QTableWidgetItem(str(product.get('barcode', '')))
                barcode_item.setFlags(barcode_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 2, barcode_item)
                
                # Name Column
                name_item = QTableWidgetItem(product['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 3, name_item)
                
                # Sell Price Column
                sell_price = product.get('unit_price', 0)
                price_item = QTableWidgetItem(f"{sell_price:.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 4, price_item)
                
                # Purchase Price Column
                purchase_price = product.get('purchase_price', 0)
                cost_item = QTableWidgetItem(f"{purchase_price:.2f}")
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 5, cost_item)
                
                # Stock Column
                stock_item = QTableWidgetItem(str(product.get('stock', 0)))
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 6, stock_item)
                
                # Min Stock Column
                min_stock_item = QTableWidgetItem(str(product.get('min_stock', 0)))
                min_stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                min_stock_item.setFlags(min_stock_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 7, min_stock_item)
                
                # Category Column
                category_name = product.get('category_name', 'Non catégorisé')
                category_item = QTableWidgetItem(category_name)
                category_item.setFlags(category_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 8, category_item)
                
                # Variants Column
                has_variants = product.get('has_variants', False)
                variants_item = QTableWidgetItem("Oui" if has_variants else "Non")
                variants_item.setFlags(variants_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.products_table.setItem(row, 9, variants_item)
                
                # Margin Column
                margin = 0
                if purchase_price and purchase_price > 0:
                    margin = ((sell_price - purchase_price) / purchase_price) * 100
                margin_item = QTableWidgetItem(f"{margin:.2f}%")
                margin_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                margin_item.setFlags(margin_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                
                # Color code margin
                if margin < 0:
                    margin_item.setForeground(Qt.red)
                elif margin > 50:
                    margin_item.setForeground(Qt.darkGreen)
                    
                self.products_table.setItem(row, 10, margin_item)
                
                # Actions Column - create a widget with buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                # Edit button
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("Modifier")
                edit_btn.setMaximumWidth(30)
                edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
                
                # Stock button
                stock_btn = QPushButton("📦")
                stock_btn.setToolTip("Gérer le stock")
                stock_btn.setMaximumWidth(30)
                stock_btn.clicked.connect(lambda checked, p=product: self.manage_stock(p))
                
                # Variant button (only for products with variants)
                variant_btn = QPushButton("🔄")
                variant_btn.setToolTip("Gérer les variantes")
                variant_btn.setMaximumWidth(30)
                variant_btn.setEnabled(has_variants)
                variant_btn.clicked.connect(lambda checked, p=product: self.manage_variants(p))
                
                # Delete button
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("Supprimer")
                delete_btn.setMaximumWidth(30)
                delete_btn.clicked.connect(lambda checked, id=product['id']: self.delete_product(id))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(stock_btn)
                actions_layout.addWidget(variant_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.products_table.setCellWidget(row, 11, actions_widget)
            
            # Update status label
            self.status_label.setText(f"Chargement de {len(products)} produits")
            
        except Exception as e:
            print(f"Error loading products: {e}")
            self.status_label.setText(f"Erreur: {str(e)}")

    def filter_products(self):
        """Filter products based on search text and category"""
        search_text = self.search_input.text().lower()
        category_id = self.category_filter.currentData()
        
        for row in range(self.products_table.rowCount()):
            show_row = True
            
            # Get product data
            name = self.products_table.item(row, 3).text().lower()
            barcode = self.products_table.item(row, 2).text().lower()
            category_name = self.products_table.item(row, 8).text().lower()
            
            # Check search text
            if search_text:
                show_row = search_text in name or search_text in barcode or search_text in category_name
                
            # Check category filter (if active)
            if show_row and category_id is not None:
                category_item = self.products_table.item(row, 8)
                if category_item:
                    # This is a simple check based on category name
                    # Ideally we would store category ID in the item data
                    current_category = category_item.text()
                    selected_category = self.category_filter.currentText()
                    if selected_category != "Toutes les catégories" and current_category != selected_category:
                        show_row = False
                
            # Show or hide row
            self.products_table.setRowHidden(row, not show_row)
            
        # Update status label with filtered count
        visible_count = sum(1 for row in range(self.products_table.rowCount()) if not self.products_table.isRowHidden(row))
        self.status_label.setText(f"Affichage de {visible_count} produits sur {self.products_table.rowCount()}")

    def add_product(self):
        """Open the add product dialog"""
        from ui.add_product_dialog import AddProductDialog
        dialog = AddProductDialog(self)
        if dialog.exec_():
            self.load_products()  # Refresh products list

    def edit_product(self, product):
        """Open the edit product dialog"""
        from ui.add_product_dialog import AddProductDialog
        dialog = AddProductDialog(self, product)
        if dialog.exec_():
            self.load_products()  # Refresh products list

    def delete_product(self, product_id):
        """Delete a product"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            'Êtes-vous sûr de vouloir supprimer ce produit? Cette action est irréversible.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if Product.delete_product(product_id):
                self.load_products()
                QMessageBox.information(self, "Succès", "Produit supprimé avec succès!")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la suppression du produit.")

    def manage_stock(self, product):
        """Open stock management dialog for a product"""
        try:
            # Import the dialog dynamically to avoid circular imports
            from .stock_management_dialog import StockManagementDialog
            
            # Create and show the dialog
            dialog = StockManagementDialog(product, self)
            
            if dialog.exec_():
                # Refresh the product list to show updated stock levels
                self.load_products()
        except Exception as e:
            print(f"Error opening stock management: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture du gestionnaire de stock: {str(e)}"
            )
    
    def manage_variants(self, product):
        """Open the variant management dialog for an existing product"""
        try:
            # Import the dialog dynamically to avoid circular imports
            from .variant_management_dialog import VariantManagementDialog
            
            # Parse variant attributes if they exist
            variant_attributes = []
            if product.get('variant_attributes'):
                try:
                    if isinstance(product['variant_attributes'], str):
                        variant_attributes = json.loads(product['variant_attributes'])
                    else:
                        variant_attributes = product['variant_attributes']
                except Exception as e:
                    print(f"Error parsing variant attributes: {e}")
                    variant_attributes = []
            
            # Create and show the dialog
            dialog = VariantManagementDialog(product['id'], self, variant_attributes)
            
            if dialog.exec_():
                # Refresh the product list after managing variants
                self.load_products()
        except Exception as e:
            print(f"Error opening variant management: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture du gestionnaire de variantes: {str(e)}"
            )
            
    def open_import_export(self):
        """Open the import/export dialog"""
        try:
            from .import_export_dialog import ImportExportDialog
            dialog = ImportExportDialog(self)
            if dialog.exec_():
                # Refresh products list after import
                self.load_products()
        except Exception as e:
            print(f"Error opening import/export dialog: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture de l'outil d'importation/exportation: {str(e)}"
            )
