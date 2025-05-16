from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QTabWidget, QScrollArea, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox, QMessageBox, QGroupBox,
    QHeaderView, QFrame, QRadioButton, QButtonGroup, QColorDialog, QSplitter,
    QListWidget, QListWidgetItem, QMenu, QAction, QToolButton, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont, QPalette

import json
import os
import sys
import time
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our models
from models.product_attribute import ProductAttribute
from models.product import Product

class AttributeValueWidget(QWidget):
    """Widget for displaying and editing an attribute value"""
    
    valueChanged = pyqtSignal(int, str, float, str)  # id, value, price_extra, html_color
    deleteRequested = pyqtSignal(int)  # value_id
    
    def __init__(self, value_id, value_text, price_extra=0, html_color=None, parent=None):
        super().__init__(parent)
        self.value_id = value_id
        self.value_text = value_text
        self.price_extra = price_extra
        self.html_color = html_color
        
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Value text
        self.value_edit = QLineEdit(self.value_text)
        self.value_edit.setPlaceholderText("Valeur")
        self.value_edit.textChanged.connect(self.on_value_changed)
        
        # Price extra
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setPrefix("+")
        self.price_spin.setSuffix(" MAD")
        self.price_spin.setRange(-10000, 10000)
        self.price_spin.setValue(self.price_extra)
        self.price_spin.valueChanged.connect(self.on_price_changed)
        
        # Color picker (only shown if attribute is color type)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(24, 24)
        self.color_btn.setToolTip("Choisir une couleur")
        self.color_btn.clicked.connect(self.choose_color)
        self.update_color_button()
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setToolTip("Supprimer cette valeur")
        delete_btn.clicked.connect(self.on_delete)
        
        layout.addWidget(self.value_edit, 3)  # Stretch factor 3
        layout.addWidget(self.price_spin, 2)   # Stretch factor 2
        layout.addWidget(self.color_btn)
        layout.addWidget(delete_btn)
        
    def update_color_button(self):
        """Update color button background"""
        if self.html_color:
            self.color_btn.setStyleSheet(f"background-color: {self.html_color}; border: 1px solid #ccc;")
            self.color_btn.setText("")
        else:
            self.color_btn.setStyleSheet("")
            self.color_btn.setText("🎨")
    
    def set_color_visible(self, visible):
        """Show or hide the color button"""
        self.color_btn.setVisible(visible)
    
    def on_value_changed(self):
        """Handle value text change"""
        self.value_text = self.value_edit.text()
        self.valueChanged.emit(self.value_id, self.value_text, self.price_extra, self.html_color)
    
    def on_price_changed(self, value):
        """Handle price extra change"""
        self.price_extra = value
        self.valueChanged.emit(self.value_id, self.value_text, self.price_extra, self.html_color)
    
    def choose_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(Qt.white, self, "Choisir une couleur")
        if color.isValid():
            self.html_color = color.name()
            self.update_color_button()
            self.valueChanged.emit(self.value_id, self.value_text, self.price_extra, self.html_color)
    
    def on_delete(self):
        """Request deletion of this value"""
        self.deleteRequested.emit(self.value_id)


class AttributeEditorWidget(QWidget):
    """Widget for editing an attribute and its values"""
    
    attributeChanged = pyqtSignal(dict)  # attribute data
    
    def __init__(self, attribute, parent=None):
        super().__init__(parent)
        self.attribute = attribute
        self.value_widgets = {}
        self.init_ui()
        self.load_values()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header with attribute details
        header = QFrame()
        header.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        header_layout = QHBoxLayout(header)
        
        # Attribute name
        self.name_edit = QLineEdit(self.attribute.get('name', ''))
        self.name_edit.setPlaceholderText("Nom de l'attribut")
        self.name_edit.textChanged.connect(self.on_attribute_changed)
        
        # Display type selection
        self.display_type = QComboBox()
        self.display_type.addItem("Radio", "radio")
        self.display_type.addItem("Liste déroulante", "select")
        self.display_type.addItem("Couleur", "color")
        self.display_type.addItem("Pills", "pills")
        
        # Set current display type
        current_type = self.attribute.get('display_type', 'radio')
        index = self.display_type.findData(current_type)
        if index >= 0:
            self.display_type.setCurrentIndex(index)
        
        self.display_type.currentIndexChanged.connect(self.on_display_type_changed)
        
        header_layout.addWidget(QLabel("Nom:"))
        header_layout.addWidget(self.name_edit, 1)  # Stretch factor 1
        header_layout.addWidget(QLabel("Affichage:"))
        header_layout.addWidget(self.display_type)
        
        main_layout.addWidget(header)
        
        # Values section
        values_group = QGroupBox("Valeurs")
        self.values_layout = QVBoxLayout(values_group)
        
        # Add button for new values
        add_value_btn = QPushButton("+ Ajouter une valeur")
        add_value_btn.clicked.connect(self.add_new_value)
        
        main_layout.addWidget(values_group)
        main_layout.addWidget(add_value_btn)
        main_layout.addStretch()
    
    def load_values(self):
        """Load attribute values"""
        # Clear existing values
        while self.values_layout.count():
            item = self.values_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.value_widgets = {}
        
        # Get attribute values
        if 'id' in self.attribute:
            values = ProductAttribute.get_attribute_values(self.attribute['id'])
            
            for value in values:
                self.add_value_widget(
                    value['id'],
                    value['value'],
                    0,  # We'll need to get price_extra from a different query
                    value.get('html_color')
                )
    
    def add_value_widget(self, value_id, value_text, price_extra=0, html_color=None):
        """Add a widget for an attribute value"""
        widget = AttributeValueWidget(value_id, value_text, price_extra, html_color)
        widget.valueChanged.connect(self.on_value_changed)
        widget.deleteRequested.connect(self.on_value_deleted)
        
        # Show/hide color selector based on display type
        is_color_type = self.display_type.currentData() == "color"
        widget.set_color_visible(is_color_type)
        
        self.values_layout.addWidget(widget)
        self.value_widgets[value_id] = widget
    
    def add_new_value(self):
        """Add a new value to this attribute"""
        if 'id' not in self.attribute:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord enregistrer l'attribut.")
            return
        
        # Create a temporary value
        value_id = ProductAttribute.add_attribute_value(
            self.attribute['id'],
            f"Nouvelle valeur {len(self.value_widgets) + 1}"
        )
        
        if value_id:
            # Add the widget
            self.add_value_widget(value_id, f"Nouvelle valeur {len(self.value_widgets) + 1}")
            
            # Update the attribute data
            self.on_attribute_changed()
    
    def on_value_changed(self, value_id, value_text, price_extra, html_color):
        """Handle value change"""
        # Update the attribute value in the database
        if 'id' in self.attribute:
            # Update the value in the database
            # This would need to be implemented in ProductAttribute class
            pass
        
        # Update the attribute data
        self.on_attribute_changed()
    
    def on_value_deleted(self, value_id):
        """Handle value deletion"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer cette valeur?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete from database
            if ProductAttribute.delete_attribute_value(value_id):
                # Remove widget
                if value_id in self.value_widgets:
                    self.value_widgets[value_id].deleteLater()
                    del self.value_widgets[value_id]
                    
                    # Update the attribute data
                    self.on_attribute_changed()
    
    def on_display_type_changed(self):
        """Handle display type change"""
        # Update the attribute in the database
        display_type = self.display_type.currentData()
        
        if 'id' in self.attribute:
            ProductAttribute.update_attribute(
                self.attribute['id'],
                display_type=display_type
            )
        
        # Show/hide color selectors based on display type
        is_color_type = display_type == "color"
        for widget in self.value_widgets.values():
            widget.set_color_visible(is_color_type)
        
        # Update the attribute data
        self.on_attribute_changed()
    
    def on_attribute_changed(self):
        """Update the attribute data and emit signal"""
        name = self.name_edit.text()
        display_type = self.display_type.currentData()
        
        if 'id' in self.attribute:
            # Update attribute in database
            ProductAttribute.update_attribute(
                self.attribute['id'],
                name=name,
                display_type=display_type
            )
        
        # Update local attribute data
        self.attribute['name'] = name
        self.attribute['display_type'] = display_type
        
        # Emit signal
        self.attributeChanged.emit(self.attribute)


class VariantDashboard(QDialog):
    """Main dashboard for managing product variants"""
    
    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.attributes = []
        self.variants = []
        self.product = None
        
        self.init_ui()
        self.load_product()
        self.load_attributes()
        self.load_variants()
    
    def init_ui(self):
        self.setWindowTitle("Gestion des variantes de produit")
        self.setMinimumSize(1000, 600)
        
        # Main layout with tabs
        main_layout = QVBoxLayout(self)
        
        # Title and product info
        self.title_label = QLabel("Variantes: [Nom du produit]")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.title_label)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Attributes tab
        attributes_tab = QWidget()
        self.setup_attributes_tab(attributes_tab)
        tabs.addTab(attributes_tab, "1. Configurer les attributs")
        
        # Variants tab
        variants_tab = QWidget()
        self.setup_variants_tab(variants_tab)
        tabs.addTab(variants_tab, "2. Générer les variantes")
        
        # Add tabs to main layout
        main_layout.addWidget(tabs)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Générer toutes les variantes")
        self.generate_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 10px;")
        self.generate_btn.clicked.connect(self.generate_variants)
        
        save_btn = QPushButton("Enregistrer et fermer")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def setup_attributes_tab(self, tab):
        """Setup the attributes configuration tab"""
        layout = QVBoxLayout(tab)
        
        # Explanation text
        explanation = QLabel("Configurez les attributs de ce produit (couleur, taille, etc.) et leurs valeurs possibles.")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(explanation)
        
        # Split view for attributes list and editor
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Attributes list
        attributes_frame = QFrame()
        attributes_layout = QVBoxLayout(attributes_frame)
        attributes_layout.setContentsMargins(0, 0, 0, 0)
        
        # Attributes list
        self.attributes_list = QListWidget()
        self.attributes_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: #000;
            }
        """)
        self.attributes_list.currentRowChanged.connect(self.on_attribute_selected)
        
        # Buttons for attributes
        attr_buttons = QHBoxLayout()
        
        add_attr_btn = QPushButton("+ Ajouter un attribut")
        add_attr_btn.clicked.connect(self.add_new_attribute)
        
        remove_attr_btn = QPushButton("🗑️ Supprimer")
        remove_attr_btn.clicked.connect(self.remove_selected_attribute)
        
        attr_buttons.addWidget(add_attr_btn)
        attr_buttons.addWidget(remove_attr_btn)
        
        attributes_layout.addWidget(QLabel("<b>Attributs:</b>"))
        attributes_layout.addWidget(self.attributes_list)
        attributes_layout.addLayout(attr_buttons)
        
        # Right side: Attribute editor
        self.editor_stack = QStackedWidget()
        
        # Empty state widget
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_label = QLabel("Sélectionnez un attribut pour l'éditer ou créez-en un nouveau.")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("color: #999; font-style: italic;")
        empty_layout.addWidget(empty_label)
        
        self.editor_stack.addWidget(empty_widget)
        
        # Add widgets to splitter
        splitter.addWidget(attributes_frame)
        splitter.addWidget(self.editor_stack)
        
        # Set initial sizes (1:2 ratio)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
    
    def setup_variants_tab(self, tab):
        """Setup the variants management tab"""
        layout = QVBoxLayout(tab)
        
        # Explanation text
        explanation = QLabel("Générez et gérez les variantes de ce produit basées sur les attributs configurés.")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(explanation)
        
        # Variants table
        self.variants_table = QTableWidget()
        self.variants_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        
        # Set up the table
        self.setup_variants_table()
        
        layout.addWidget(self.variants_table)
        
        # Bulk actions
        bulk_layout = QHBoxLayout()
        
        bulk_price_btn = QPushButton("📊 Appliquer un prix en masse")
        bulk_price_btn.clicked.connect(self.apply_bulk_price)
        
        bulk_stock_btn = QPushButton("📦 Mettre à jour le stock en masse")
        bulk_stock_btn.clicked.connect(self.apply_bulk_stock)
        
        bulk_layout.addWidget(bulk_price_btn)
        bulk_layout.addWidget(bulk_stock_btn)
        bulk_layout.addStretch()
        
        layout.addLayout(bulk_layout)
    
    def setup_variants_table(self):
        """Setup the variants table structure"""
        self.variants_table.setColumnCount(7)
        self.variants_table.setHorizontalHeaderLabels([
            "Variante", "SKU", "Code-barres", "Prix de base", "Suppléments", "Prix final", "Stock"
        ])
        
        # Set column widths
        self.variants_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Variant name
        self.variants_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)    # SKU
        self.variants_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)    # Barcode
        self.variants_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)    # Base price
        self.variants_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)    # Price extras
        self.variants_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)    # Final price
        self.variants_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)    # Stock
        
        self.variants_table.setColumnWidth(1, 120)  # SKU
        self.variants_table.setColumnWidth(2, 120)  # Barcode
        self.variants_table.setColumnWidth(3, 100)  # Base price
        self.variants_table.setColumnWidth(4, 100)  # Price extras
        self.variants_table.setColumnWidth(5, 100)  # Final price
        self.variants_table.setColumnWidth(6, 80)   # Stock
    
    def load_product(self):
        """Load product data"""
        try:
            # Get the product
            # This would need to connect to your Product class
            # For now, we'll mock some data
            self.product = {
                'id': self.product_id,
                'name': "Produit exemple",
                'unit_price': 100.0
            }
            
            # Update title
            self.title_label.setText(f"Variantes: {self.product.get('name', '')}")
            
        except Exception as e:
            print(f"Error loading product: {e}")
    
    def load_attributes(self):
        """Load product attributes"""
        try:
            # Get attribute lines for this product
            self.attributes = ProductAttribute.get_product_attribute_lines(self.product_id)
            
            # Clear the list
            self.attributes_list.clear()
            
            # Add to list
            for attr in self.attributes:
                item = QListWidgetItem(attr['attribute_name'])
                item.setData(Qt.UserRole, attr)
                self.attributes_list.addItem(item)
            
        except Exception as e:
            print(f"Error loading attributes: {e}")
    
    def load_variants(self):
        """Load product variants"""
        try:
            # Get variants for this product
            self.variants = Product.get_variants(self.product_id)
            
            # Update the table
            self.update_variants_table()
            
        except Exception as e:
            print(f"Error loading variants: {e}")
    
    def update_variants_table(self):
        """Update the variants table with current data"""
        self.variants_table.setRowCount(0)  # Clear
        
        if not self.variants:
            return
        
        # Add variants to table
        base_price = self.product.get('unit_price', 0)
        
        for row, variant in enumerate(self.variants):
            self.variants_table.insertRow(row)
            
            # Variant name
            name_item = QTableWidgetItem(variant.get('name', ''))
            name_item.setData(Qt.UserRole, variant)
            self.variants_table.setItem(row, 0, name_item)
            
            # SKU
            sku_item = QTableWidgetItem(variant.get('sku', ''))
            self.variants_table.setItem(row, 1, sku_item)
            
            # Barcode
            barcode_item = QTableWidgetItem(variant.get('barcode', ''))
            self.variants_table.setItem(row, 2, barcode_item)
            
            # Base price
            base_price_item = QTableWidgetItem(f"{base_price:.2f}")
            base_price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.variants_table.setItem(row, 3, base_price_item)
            
            # Price extras
            price_extras = variant.get('price_extras', 0) or 0
            extras_item = QTableWidgetItem(f"{price_extras:.2f}")
            extras_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.variants_table.setItem(row, 4, extras_item)
            
            # Final price
            final_price = variant.get('unit_price', base_price)
            if not final_price or final_price == 0:
                final_price = base_price + price_extras
            
            final_item = QTableWidgetItem(f"{final_price:.2f}")
            final_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            final_item.setBackground(QColor("#e6f3ff"))  # Light blue background
            self.variants_table.setItem(row, 5, final_item)
            
            # Stock
            stock = variant.get('stock', 0) or 0
            stock_spin = QSpinBox()
            stock_spin.setRange(0, 999999)
            stock_spin.setValue(stock)
            stock_spin.valueChanged.connect(lambda value, v=variant: self.update_variant_stock(v, value))
            self.variants_table.setCellWidget(row, 6, stock_spin)
    
    def update_variant_stock(self, variant, value):
        """Update a variant's stock value"""
        try:
            variant_id = variant.get('id')
            if variant_id:
                # Update in database
                Product.update_variant(variant_id, stock=value)
                
                # Update in memory
                variant['stock'] = value
        except Exception as e:
            print(f"Error updating variant stock: {e}")
    
    def on_attribute_selected(self, row):
        """Handle attribute selection in the list"""
        if row < 0:
            # No selection, show empty state
            self.editor_stack.setCurrentIndex(0)
            return
        
        # Get the selected attribute
        item = self.attributes_list.item(row)
        if not item:
            return
        
        attribute = item.data(Qt.UserRole)
        
        # Check if we already have an editor for this attribute
        editor_widget = None
        for i in range(1, self.editor_stack.count()):
            widget = self.editor_stack.widget(i)
            if widget.attribute.get('id') == attribute.get('id'):
                editor_widget = widget
                self.editor_stack.setCurrentWidget(editor_widget)
                break
        
        # Create a new editor if needed
        if not editor_widget:
            editor_widget = AttributeEditorWidget(attribute)
            editor_widget.attributeChanged.connect(self.on_attribute_updated)
            self.editor_stack.addWidget(editor_widget)
            self.editor_stack.setCurrentWidget(editor_widget)
    
    def on_attribute_updated(self, attribute):
        """Handle attribute updates from the editor"""
        # Update the list item
        for i in range(self.attributes_list.count()):
            item = self.attributes_list.item(i)
            attr_data = item.data(Qt.UserRole)
            if attr_data.get('id') == attribute.get('id'):
                item.setText(attribute.get('name', ''))
                item.setData(Qt.UserRole, attribute)
                break
        
        # Refresh variants if needed
        self.load_variants()
    
    def add_new_attribute(self):
        """Add a new attribute to the product"""
        # Show a dialog to get the attribute name
        from PyQt5.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Nouvel attribut", "Nom de l'attribut:")
        if ok and name:
            # Create the attribute
            attribute_id = ProductAttribute.add_attribute(name)
            
            if attribute_id:
                # Associate with product
                line_id = ProductAttribute.associate_attribute_to_product(self.product_id, attribute_id)
                
                if line_id:
                    # Reload attributes
                    self.load_attributes()
                    
                    # Select the new attribute
                    for i in range(self.attributes_list.count()):
                        item = self.attributes_list.item(i)
                        attr_data = item.data(Qt.UserRole)
                        if attr_data.get('id') == attribute_id:
                            self.attributes_list.setCurrentRow(i)
                            break
    
    def remove_selected_attribute(self):
        """Remove the selected attribute"""
        row = self.attributes_list.currentRow()
        if row < 0:
            return
        
        # Get the selected attribute
        item = self.attributes_list.item(row)
        if not item:
            return
        
        attribute = item.data(Qt.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer l'attribut '{attribute.get('attribute_name')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete the attribute
            # This would need to be implemented in ProductAttribute class
            
            # Reload attributes
            self.load_attributes()
    
    def generate_variants(self):
        """Generate all possible variants for the product"""
        if not self.attributes:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord configurer des attributs.")
            return
        
        # Confirm if variants already exist
        if self.variants:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Des variantes existent déjà. La génération créera de nouvelles variantes pour toutes les combinaisons possibles. Continuer?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        try:
            # Generate variants
            from variant_manager import generate_all_variants_for_product
            variant_ids = generate_all_variants_for_product(self.product_id)
            
            if variant_ids:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"{len(variant_ids)} variantes ont été créées avec succès."
                )
                
                # Reload variants
                self.load_variants()
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Aucune variante n'a pu être générée. Vérifiez que vos attributs ont des valeurs."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la génération des variantes: {str(e)}"
            )
    
    def apply_bulk_price(self):
        """Apply a price to multiple variants at once"""
        if not self.variants:
            return
        
        # Show dialog to get price adjustment
        from PyQt5.QtWidgets import QInputDialog
        
        price, ok = QInputDialog.getDouble(
            self,
            "Appliquer un prix en masse",
            "Prix pour toutes les variantes sélectionnées:",
            100.0, 0, 999999, 2
        )
        
        if ok:
            # Apply to all selected rows
            selected_items = self.variants_table.selectedItems()
            variant_ids = set()
            
            for item in selected_items:
                row = item.row()
                variant_item = self.variants_table.item(row, 0)
                variant = variant_item.data(Qt.UserRole)
                variant_ids.add(variant.get('id'))
            
            if not variant_ids:
                # If nothing selected, ask if we should apply to all
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "Aucune variante n'est sélectionnée. Appliquer le prix à toutes les variantes?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    variant_ids = {v.get('id') for v in self.variants}
                else:
                    return
            
            # Apply price to all selected variants
            for variant_id in variant_ids:
                Product.update_variant(variant_id, unit_price=price)
            
            # Reload variants
            self.load_variants()
    
    def apply_bulk_stock(self):
        """Apply stock quantity to multiple variants at once"""
        if not self.variants:
            return
        
        # Show dialog to get stock quantity
        from PyQt5.QtWidgets import QInputDialog
        
        stock, ok = QInputDialog.getInt(
            self,
            "Mettre à jour le stock en masse",
            "Quantité en stock pour toutes les variantes sélectionnées:",
            10, 0, 999999
        )
        
        if ok:
            # Apply to all selected rows
            selected_items = self.variants_table.selectedItems()
            variant_ids = set()
            
            for item in selected_items:
                row = item.row()
                variant_item = self.variants_table.item(row, 0)
                variant = variant_item.data(Qt.UserRole)
                variant_ids.add(variant.get('id'))
            
            if not variant_ids:
                # If nothing selected, ask if we should apply to all
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "Aucune variante n'est sélectionnée. Appliquer le stock à toutes les variantes?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    variant_ids = {v.get('id') for v in self.variants}
                else:
                    return
            
            # Apply stock to all selected variants
            for variant_id in variant_ids:
                Product.update_variant(variant_id, stock=stock)
            
            # Reload variants
            self.load_variants()


# For testing
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create and show dialog
    dialog = VariantDashboard(1)  # Use product ID 1 for testing
    dialog.show()
    
    sys.exit(app.exec_())
