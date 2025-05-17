from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QGroupBox, QScrollArea, QFrame, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from models.category import Category
from datetime import datetime
import os
import shutil
import json

class AddProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.image_path = None
        self.variant_widgets = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Ajouter un produit" if not self.product else "Modifier le produit")
        self.setMinimumWidth(600)
        
        # Main Layout with ScrollArea
        main_layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout()

        # Basic Information Group
        basic_group = QGroupBox("Informations de base")
        basic_layout = QFormLayout()
        
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
        
        # Prix
        price_layout = QHBoxLayout()
        
        self.selling_price = QDoubleSpinBox()
        self.selling_price.setMaximum(999999.99)
        self.selling_price.setSuffix(" MAD")
        price_layout.addWidget(QLabel("Prix de vente:"))
        price_layout.addWidget(self.selling_price)
        
        self.purchase_price = QDoubleSpinBox()
        self.purchase_price.setMaximum(999999.99)
        self.purchase_price.setSuffix(" MAD")
        price_layout.addWidget(QLabel("Prix d'achat:"))
        price_layout.addWidget(self.purchase_price)
        
        self.margin_label = QLabel("0%")
        price_layout.addWidget(QLabel("Marge:"))
        price_layout.addWidget(self.margin_label)
        
        basic_layout.addRow(price_layout)
        
        # Stock
        stock_layout = QHBoxLayout()
        
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(999999)
        stock_layout.addWidget(QLabel("Stock:"))
        stock_layout.addWidget(self.stock_input)
        
        self.min_stock = QSpinBox()
        self.min_stock.setMaximum(999999)
        stock_layout.addWidget(QLabel("Stock minimum:"))
        stock_layout.addWidget(self.min_stock)
        
        basic_layout.addRow(stock_layout)
        
        basic_group.setLayout(basic_layout)
        form_layout.addRow(basic_group)

        # Variants Group
        variant_group = QGroupBox("Variantes")
        variant_layout = QVBoxLayout()
        
        # Has variants checkbox
        self.has_variants = QCheckBox("Article avec variantes")
        self.has_variants.stateChanged.connect(self.toggle_variant_options)
        variant_layout.addWidget(self.has_variants)
        
        # Variant options frame
        self.variant_frame = QFrame()
        variant_frame_layout = QVBoxLayout()
        
        # Attributes from database
        self.variant_attributes = []
        
        # Load custom attributes from database
        from models.product_attribute import ProductAttribute
        custom_attributes = ProductAttribute.get_all_attributes()
        
        # If no custom attributes, provide some predefined ones as fallback
        predefined_attributes = []
        if custom_attributes:
            predefined_attributes = [attr['name'] for attr in custom_attributes]
        else:
            predefined_attributes = ["Taille", "Couleur", "Matériau", "Style"]
            
        # Attribute checkbox group
        attr_group = QGroupBox("Attributs disponibles")
        attr_layout = QVBoxLayout()
        
        for attr in predefined_attributes:
            cb = QCheckBox(attr)
            self.variant_attributes.append((attr, cb))
            attr_layout.addWidget(cb)
        
        # Custom attribute
        custom_attr_layout = QHBoxLayout()
        self.custom_attr_input = QLineEdit()
        self.custom_attr_input.setPlaceholderText("Autre attribut...")
        add_attr_btn = QPushButton("+")
        add_attr_btn.clicked.connect(self.add_custom_attribute)
        custom_attr_layout.addWidget(self.custom_attr_input)
        custom_attr_layout.addWidget(add_attr_btn)
        attr_layout.addLayout(custom_attr_layout)
        
        # Manage attributes button
        manage_attr_btn = QPushButton("Gérer tous les attributs")
        manage_attr_btn.clicked.connect(self.manage_attributes)
        attr_layout.addWidget(manage_attr_btn)
        
        attr_group.setLayout(attr_layout)
        variant_frame_layout.addWidget(attr_group)
        
        # Variant management section
        variant_mgmt_layout = QHBoxLayout()
        
        # Button to open variant management
        manage_variants_btn = QPushButton("Gérer les variantes")
        manage_variants_btn.clicked.connect(self.manage_variants)
        manage_variants_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        variant_mgmt_layout.addWidget(manage_variants_btn)
        
        # Variant count label
        self.variant_count_label = QLabel("Aucune variante configurée")
        self.variant_count_label.setStyleSheet("color: #666;")
        variant_mgmt_layout.addWidget(self.variant_count_label)
        
        variant_frame_layout.addLayout(variant_mgmt_layout)
        
        # Initialize variants data
        self.variants_data = []
        
        self.variant_frame.setLayout(variant_frame_layout)
        self.variant_frame.setEnabled(False)
        variant_layout.addWidget(self.variant_frame)
        
        variant_group.setLayout(variant_layout)
        form_layout.addRow(variant_group)

        # Image Group
        image_group = QGroupBox("Image")
        image_layout = QHBoxLayout()
        
        self.image_button = QPushButton("Sélectionner une image")
        self.image_button.clicked.connect(self.select_image)
        self.image_label = QLabel()
        self.image_label.setFixedSize(100, 100)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        
        image_layout.addWidget(self.image_button)
        image_layout.addWidget(self.image_label)
        image_group.setLayout(image_layout)
        form_layout.addRow(image_group)

        # Category
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow("Catégorie:", self.category_combo)

        scroll_content.setLayout(form_layout)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Enregistrer")
        cancel_button = QPushButton("Annuler")
        
        save_button.clicked.connect(self.validate_and_accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.selling_price.valueChanged.connect(self.calculate_margin)
        self.purchase_price.valueChanged.connect(self.calculate_margin)
        
        # Fill data if editing
        if self.product:
            self.fill_product_data()

    def toggle_variant_options(self, state):
        self.variant_frame.setEnabled(state == Qt.Checked)
        
    def manage_variants(self):
        """Open the variant management dialog"""
        try:
            # Import dynamically to avoid circular dependencies
            module = __import__('ui.variant_management_dialog', fromlist=['VariantManagementDialog'])
            VariantManagementDialog = module.VariantManagementDialog

            # Collect selected attributes
            selected_attrs = [
                attr for attr, cb in self.variant_attributes 
                if cb.isChecked()
            ]
            
            product_id = None
            if self.product and 'id' in self.product:
                product_id = self.product['id']
                
            # Show the variant management dialog
            dialog = VariantManagementDialog(
                product_id=product_id,
                parent=self,
                variant_attributes=selected_attrs
            )
            
            if dialog.exec_():
                # Get the variant data
                self.variants_data = dialog.get_variants_data()
                
                # Update attribute list from dialog
                attr_names = dialog.get_attribute_names()
                
                # Also extract attribute names from variants in case get_attribute_names() misses some
                variant_attr_names = set()
                for variant in self.variants_data:
                    if 'attributes' in variant:
                        variant_attr_names.update(variant['attributes'].keys())
                    elif 'attribute_values' in variant:
                        try:
                            attrs = json.loads(variant['attribute_values'])
                            variant_attr_names.update(attrs.keys())
                        except:
                            pass
                
                # Combine both sources of attribute names
                all_attr_names = set(attr_names) | variant_attr_names
                print(f"All attribute names: {all_attr_names}")
                
                # Update variant count label
                if self.variants_data:
                    self.variant_count_label.setText(f"{len(self.variants_data)} variantes configurées")
                    self.variant_count_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.variant_count_label.setText("Aucune variante configurée")
                    self.variant_count_label.setStyleSheet("color: #666;")
                    
                # Update the selected attributes in the UI - check all that are in the combined list
                # Make case-insensitive comparison for attribute names
                all_attr_names_lower = {name.lower() for name in all_attr_names}
                print(f"Updating checkboxes for attributes: {[attr for attr, _ in self.variant_attributes]}")
                print(f"Normalized attribute names for comparison: {all_attr_names_lower}")
                
                for attr, cb in self.variant_attributes:
                    # Case-insensitive check
                    attr_lower = attr.lower()
                    should_check = attr_lower in all_attr_names_lower
                    cb.setChecked(should_check)
                    print(f"Setting {attr} to {'checked' if should_check else 'unchecked'} (lower: {attr_lower})")
                
                # Ensure the variants section is enabled
                self.has_variants.setChecked(bool(self.variants_data))
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture du gestionnaire de variantes: {str(e)}")

    def add_custom_attribute(self):
        attr_name = self.custom_attr_input.text().strip()
        if attr_name:
            for existing_attr, _ in self.variant_attributes:
                if existing_attr.lower() == attr_name.lower():
                    QMessageBox.warning(self, "Erreur", "Cet attribut existe déjà!")
                    return
            
            cb = QCheckBox(attr_name)
            self.variant_attributes.append((attr_name, cb))
            self.variant_frame.layout().insertWidget(
                len(self.variant_attributes) - 1,
                cb
            )
            self.custom_attr_input.clear()

    def calculate_margin(self):
        """Calculate profit margin percentage"""
        try:
            selling = self.selling_price.value()
            purchase = self.purchase_price.value()
            
            if purchase > 0:
                margin = ((selling - purchase) / purchase) * 100
                self.margin_label.setText(f"{margin:.1f}%")
                
                # Change color based on margin
                if margin < 0:
                    self.margin_label.setStyleSheet("color: red; font-weight: bold;")
                elif margin < 10:
                    self.margin_label.setStyleSheet("color: orange; font-weight: bold;")
                else:
                    self.margin_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.margin_label.setText("N/A")
                self.margin_label.setStyleSheet("color: grey;")
        except Exception as e:
            print(f"Error calculating margin: {e}")
            self.margin_label.setText("Erreur")

    def load_categories(self):
        """Load categories into combo box"""
        try:
            # Clear existing items
            self.category_combo.clear()
            
            # Add "No category" option
            self.category_combo.addItem("Aucune catégorie", None)
            
            # Get categories from database
            categories = Category.get_all_categories()
            for category in categories:
                self.category_combo.addItem(category[1], category[0])  # name, id
        except Exception as e:
            print(f"Error loading categories: {e}")

    def select_image(self):
        """Open file dialog to select product image"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self, "Sélectionner une image", "", 
                "Images (*.png *.jpg *.jpeg)"
            )
            
            if file_path:
                # Create images directory if it doesn't exist
                images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images')
                os.makedirs(images_dir, exist_ok=True)
                
                # Copy the file to images directory with a unique name
                file_name = os.path.basename(file_path)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_file_name = f"{timestamp}_{file_name}"
                new_file_path = os.path.join(images_dir, new_file_name)
                
                # Copy the file
                shutil.copy2(file_path, new_file_path)
                
                # Update image path and preview
                self.image_path = new_file_path
                self.update_image_preview()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la sélection de l'image: {str(e)}")

    def update_image_preview(self):
        """Update the image preview label"""
        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.image_label.width(), 
                    self.image_label.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("Image invalide")
        else:
            self.image_label.clear()
            self.image_label.setText("Aucune image")

    def fill_product_data(self):
        """Fill form with product data when editing"""
        try:
            if not self.product:
                return
                
            # Basic information
            self.barcode_input.setText(str(self.product.get('barcode', '')))
            self.name_input.setText(str(self.product.get('name', '')))
            self.description_input.setText(str(self.product.get('description', '')))
            
            # Prices
            self.selling_price.setValue(float(self.product.get('unit_price', 0)))
            self.purchase_price.setValue(float(self.product.get('purchase_price', 0)))
            
            # Stock
            self.stock_input.setValue(int(self.product.get('stock', 0)))
            self.min_stock.setValue(int(self.product.get('min_stock', 0)))
            
            # Category
            category_id = self.product.get('category_id')
            if category_id:
                # Find the index of the category in the combo box
                index = self.category_combo.findData(category_id)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
            
            # Image
            self.image_path = self.product.get('image_path')
            self.update_image_preview()
            
            # Variants
            has_variants = self.product.get('has_variants', False)
            self.has_variants.setChecked(has_variants)
            
            # Variant attributes
            if has_variants and self.product.get('variant_attributes'):
                try:
                    # Parse variant attributes
                    attributes = []
                    if isinstance(self.product['variant_attributes'], str):
                        attributes = json.loads(self.product['variant_attributes'])
                    else:
                        attributes = self.product['variant_attributes']
                    
                    # Check the corresponding checkboxes
                    for attr, cb in self.variant_attributes:
                        if attr in attributes:
                            cb.setChecked(True)
                except Exception as e:
                    print(f"Error parsing variant attributes: {e}")
        except Exception as e:
            print(f"Error filling product data: {e}")

    def validate_and_accept(self):
        """Validate form data and accept dialog"""
        # Check required fields
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Veuillez entrer un nom pour le produit.")
            return
        
        # Check if product has variants but no attributes selected and no variants configured
        if self.has_variants.isChecked():
            selected_attrs = [attr for attr, cb in self.variant_attributes if cb.isChecked()]
            has_configured_variants = hasattr(self, 'variants_data') and self.variants_data
            
            if not selected_attrs and not has_configured_variants:
                QMessageBox.warning(self, "Validation", "Vous avez activé les variantes mais aucun attribut n'est sélectionné.")
                return
            
            # If we have variants data but no selected attributes, select them automatically
            if has_configured_variants and not selected_attrs:
                # Extract attribute names from variants
                attr_names = set()
                for variant in self.variants_data:
                    if 'attributes' in variant:
                        attr_names.update(variant['attributes'].keys())
                    elif 'attribute_values' in variant:
                        try:
                            attrs = json.loads(variant['attribute_values'])
                            attr_names.update(attrs.keys())
                        except:
                            pass
                
                # Check the appropriate checkboxes
                for attr, cb in self.variant_attributes:
                    if attr in attr_names:
                        cb.setChecked(True)
        
        # All validation passed
        self.accept()

    def manage_attributes(self):
        """Open the attribute management dialog"""
        try:
            # Import dynamically to avoid circular dependencies
            module = __import__('ui.attribute_management_dialog', fromlist=['AttributeManagementDialog'])
            AttributeManagementDialog = module.AttributeManagementDialog
            
            dialog = AttributeManagementDialog(self)
            dialog.exec_()
            # We could refresh our attribute list here if needed
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture du gestionnaire d'attributs: {str(e)}")

    def get_product_data(self):
        """Get product data from form"""
        selected_attrs = [
            attr for attr, cb in self.variant_attributes 
            if cb.isChecked()
        ]
        
        data = {
            'barcode': self.barcode_input.text(),
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText(),
            'unit_price': self.selling_price.value(),
            'purchase_price': self.purchase_price.value(),
            'stock': self.stock_input.value(),
            'min_stock': self.min_stock.value(),
            'category_id': self.category_combo.currentData(),
            'image_path': self.image_path,
            'has_variants': self.has_variants.isChecked(),
            'variant_attributes': json.dumps(selected_attrs) if selected_attrs else None
        }
        
        # Add variants data if we have it
        if hasattr(self, 'variants_data') and self.variants_data and self.has_variants.isChecked():
            data['variants'] = self.variants_data
            
        return data
