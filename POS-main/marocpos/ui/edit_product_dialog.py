from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QGroupBox, QScrollArea, QFrame, QWidget,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from models.category import Category
from ui.product_helpers import debug_log, update_product_reliable, handle_error
import os
import shutil
import json

class EditProductDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.image_path = product.get('image_path')
        self.init_ui()
        self.load_product_data()

    def init_ui(self):
        self.setWindowTitle(f"Modifier le produit: {self.product.get('name', '')}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Main Layout with ScrollArea
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Product info form
        form_layout = QFormLayout()
        
        # Basic Information Group
        basic_group = QGroupBox("Informations de base")
        basic_layout = QFormLayout(basic_group)
        
        # Code barre
        self.barcode_input = QLineEdit()
        basic_layout.addRow("Code barre:", self.barcode_input)
        
        # Nom
        self.name_input = QLineEdit()
        basic_layout.addRow("Nom:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        basic_layout.addRow("Description:", self.description_input)
        
        # Image
        image_layout = QHBoxLayout()
        
        self.image_preview = QLabel("Aucune image")
        self.image_preview.setMinimumSize(100, 100)
        self.image_preview.setMaximumSize(100, 100)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet("border: 1px solid #ccc;")
        
        image_buttons_layout = QVBoxLayout()
        select_image_btn = QPushButton("Sélectionner une image")
        select_image_btn.clicked.connect(self.select_image)
        clear_image_btn = QPushButton("Supprimer l'image")
        clear_image_btn.clicked.connect(self.clear_image)
        
        image_buttons_layout.addWidget(select_image_btn)
        image_buttons_layout.addWidget(clear_image_btn)
        image_buttons_layout.addStretch()
        
        image_layout.addWidget(self.image_preview)
        image_layout.addLayout(image_buttons_layout)
        
        basic_layout.addRow("Image:", image_layout)
        
        # Prix
        price_layout = QHBoxLayout()
        
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setRange(0, 999999.99)
        self.unit_price_input.setDecimals(2)
        self.unit_price_input.setSuffix(" MAD")
        self.unit_price_input.valueChanged.connect(self.calculate_margin)
        
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 999999.99)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setSuffix(" MAD")
        self.purchase_price_input.valueChanged.connect(self.calculate_margin)
        
        self.margin_label = QLabel("0%")
        
        price_layout.addWidget(QLabel("Prix de vente:"))
        price_layout.addWidget(self.unit_price_input)
        price_layout.addWidget(QLabel("Prix d'achat:"))
        price_layout.addWidget(self.purchase_price_input)
        price_layout.addWidget(QLabel("Marge:"))
        price_layout.addWidget(self.margin_label)
        
        basic_layout.addRow(price_layout)
        
        # Stock
        stock_layout = QHBoxLayout()
        
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 999999)
        
        stock_layout.addWidget(QLabel("Stock:"))
        stock_layout.addWidget(self.stock_input)
        stock_layout.addWidget(QLabel("Stock minimum:"))
        stock_layout.addWidget(self.min_stock_input)
        
        basic_layout.addRow(stock_layout)
        
        # Category
        self.category_combo = QComboBox()
        self.load_categories()
        basic_layout.addRow("Catégorie:", self.category_combo)
        
        # Add basic group to form
        scroll_layout.addWidget(basic_group)
        
        # Additional information group (can be expanded later)
        additional_group = QGroupBox("Informations supplémentaires")
        additional_layout = QFormLayout(additional_group)
        
        # Weight
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 100000)
        self.weight_input.setDecimals(3)
        self.weight_input.setSuffix(" kg")
        additional_layout.addRow("Poids:", self.weight_input)
        
        # Volume
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0, 100000)
        self.volume_input.setDecimals(3)
        self.volume_input.setSuffix(" m³")
        additional_layout.addRow("Volume:", self.volume_input)
        
        # Unit
        self.unit_input = QLineEdit()
        additional_layout.addRow("Unité de mesure:", self.unit_input)
        
        # Add additional group to form
        scroll_layout.addWidget(additional_group)
        
        # Stock warning
        warning_label = QLabel("⚠️ L'édition d'un produit avec des variantes peut nécessiter une mise à jour des variantes séparément.")
        warning_label.setStyleSheet("color: orange; font-style: italic;")
        scroll_layout.addWidget(warning_label)
        
        # Set scroll content and add to main layout
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_product)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Update image preview
        self.update_image_preview()

    def load_categories(self):
        """Load categories into combo box"""
        try:
            self.category_combo.clear()
            categories = Category.get_all_categories()
            
            for category in categories:
                self.category_combo.addItem(category[1], category[0])
                
        except Exception as e:
            debug_log(f"Error loading categories: {e}")
            handle_error(self, "Erreur", "Impossible de charger les catégories", e)

    def calculate_margin(self):
        """Calculate and display profit margin"""
        try:
            unit_price = self.unit_price_input.value()
            purchase_price = self.purchase_price_input.value()
            
            if purchase_price > 0:
                margin = ((unit_price - purchase_price) / purchase_price) * 100
                self.margin_label.setText(f"{margin:.1f}%")
            else:
                self.margin_label.setText("N/A")
                
        except Exception as e:
            debug_log(f"Error calculating margin: {e}")
            self.margin_label.setText("Erreur")

    def select_image(self):
        """Select an image for the product"""
        try:
            file_dialog = QFileDialog()
            image_path, _ = file_dialog.getOpenFileName(
                self,
                "Sélectionner une image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)"
            )
            
            if image_path:
                # Create images directory if it doesn't exist
                images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "product_images")
                os.makedirs(images_dir, exist_ok=True)
                
                # Generate a unique filename
                file_ext = os.path.splitext(image_path)[1]
                from datetime import datetime
                new_filename = f"product_{self.product['id']}_{int(datetime.now().timestamp())}{file_ext}"
                new_path = os.path.join(images_dir, new_filename)
                
                # Copy file
                shutil.copy2(image_path, new_path)
                
                # Update image path
                self.image_path = new_path
                self.update_image_preview()
                
        except Exception as e:
            debug_log(f"Error selecting image: {e}")
            handle_error(self, "Erreur", "Impossible de sélectionner l'image", e)

    def clear_image(self):
        """Clear the product image"""
        self.image_path = None
        self.update_image_preview()

    def update_image_preview(self):
        """Update image preview"""
        try:
            if self.image_path and os.path.exists(self.image_path):
                pixmap = QPixmap(self.image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview.setPixmap(pixmap)
                    return
                    
            # No valid image, show placeholder
            self.image_preview.setText("Aucune image")
            self.image_preview.setPixmap(QPixmap())
            
        except Exception as e:
            debug_log(f"Error updating image preview: {e}")
            self.image_preview.setText("Erreur")

    def load_product_data(self):
        """Load product data into form fields"""
        try:
            debug_log(f"Loading product data for ID {self.product.get('id')}")
            
            # Basic info
            self.barcode_input.setText(str(self.product.get('barcode', '')))
            self.name_input.setText(str(self.product.get('name', '')))
            self.description_input.setText(str(self.product.get('description', '')))
            
            # Price
            self.unit_price_input.setValue(float(self.product.get('unit_price', 0)))
            self.purchase_price_input.setValue(float(self.product.get('purchase_price', 0)))
            
            # Stock
            self.stock_input.setValue(int(self.product.get('stock', 0)))
            self.min_stock_input.setValue(int(self.product.get('min_stock', 0)))
            
            # Additional info
            self.weight_input.setValue(float(self.product.get('weight', 0) or 0))
            self.volume_input.setValue(float(self.product.get('volume', 0) or 0))
            self.unit_input.setText(str(self.product.get('unit', 'pièce')))
            
            # Category
            category_id = self.product.get('category_id')
            if category_id:
                index = self.category_combo.findData(category_id)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
            
            # Calculate margin
            self.calculate_margin()
            
        except Exception as e:
            debug_log(f"Error loading product data: {e}")
            handle_error(self, "Erreur", "Impossible de charger les données du produit", e)

    def save_product(self):
        """Save product changes"""
        try:
            # Validate required fields
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Validation", "Le nom du produit est obligatoire.")
                return
                
            # Prepare product data
            product_data = {
                'name': self.name_input.text().strip(),
                'barcode': self.barcode_input.text().strip(),
                'description': self.description_input.toPlainText().strip(),
                'unit_price': self.unit_price_input.value(),
                'purchase_price': self.purchase_price_input.value(),
                'stock': self.stock_input.value(),
                'min_stock': self.min_stock_input.value(),
                'weight': self.weight_input.value(),
                'volume': self.volume_input.value(),
                'unit': self.unit_input.text().strip() or 'pièce',
                'image_path': self.image_path,
                'category_id': self.category_combo.currentData()
            }
            
            # Update product using the reliable helper
            if update_product_reliable(self.product['id'], **product_data):
                QMessageBox.information(self, "Succès", "Produit mis à jour avec succès.")
                self.accept()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de mettre à jour le produit.")
                
        except Exception as e:
            debug_log(f"Error saving product: {e}")
            handle_error(self, "Erreur", "Impossible de sauvegarder le produit", e)
