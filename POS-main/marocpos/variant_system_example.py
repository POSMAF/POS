#!/usr/bin/env python3
"""
Variant System Example Script

This script demonstrates the use of the new variant system by providing
a simple example application that allows:
1. Creating and configuring attributes
2. Adding attributes to products
3. Generating variants
4. Testing the variant selection UI

To use:
$ python variant_system_example.py
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox,
    QListWidget, QDialog, QFormLayout, QLineEdit, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import variant system components
from variant_system import initialize
from variant_system.attribute_manager import (
    AttributeType, AttributeValue, ProductAttribute, ProductAttributeValue
)
from variant_system.variant_manager import (
    ProductVariant, generate_variants_for_product
)
from variant_system.simple_ui import show_variant_dialog
from variant_system.client_interface import select_product_variant

# Import product model (just for the example)
try:
    from models.product import Product
except ImportError:
    # Mock Product class for the example
    from database import get_connection
    
    class Product:
        @staticmethod
        def get_all_products():
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, name, unit_price FROM Products")
                    return [dict(row) for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error getting products: {e}")
                    return []
                finally:
                    conn.close()
            return []
        
        @staticmethod
        def get_by_id(product_id):
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, name, unit_price FROM Products WHERE id = ?", (product_id,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
                except Exception as e:
                    print(f"Error getting product: {e}")
                    return None
                finally:
                    conn.close()
            return None


class AttributeManagerTab(QWidget):
    """Tab for managing attribute types and values"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_attributes()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Split view for attributes and values
        h_layout = QHBoxLayout()
        
        # Attribute types list (left side)
        attr_layout = QVBoxLayout()
        attr_layout.addWidget(QLabel("<b>Types d'attributs</b>"))
        
        self.attr_list = QListWidget()
        self.attr_list.currentRowChanged.connect(self.on_attribute_selected)
        attr_layout.addWidget(self.attr_list)
        
        # Attribute buttons
        attr_btn_layout = QHBoxLayout()
        
        add_attr_btn = QPushButton("Ajouter un attribut")
        add_attr_btn.clicked.connect(self.add_attribute_type)
        
        edit_attr_btn = QPushButton("Modifier")
        edit_attr_btn.clicked.connect(self.edit_attribute_type)
        
        delete_attr_btn = QPushButton("Supprimer")
        delete_attr_btn.clicked.connect(self.delete_attribute_type)
        
        attr_btn_layout.addWidget(add_attr_btn)
        attr_btn_layout.addWidget(edit_attr_btn)
        attr_btn_layout.addWidget(delete_attr_btn)
        
        attr_layout.addLayout(attr_btn_layout)
        h_layout.addLayout(attr_layout)
        
        # Attribute values list (right side)
        values_layout = QVBoxLayout()
        values_layout.addWidget(QLabel("<b>Valeurs d'attribut</b>"))
        
        self.values_list = QListWidget()
        values_layout.addWidget(self.values_list)
        
        # Value buttons
        values_btn_layout = QHBoxLayout()
        
        add_value_btn = QPushButton("Ajouter une valeur")
        add_value_btn.clicked.connect(self.add_attribute_value)
        
        edit_value_btn = QPushButton("Modifier")
        edit_value_btn.clicked.connect(self.edit_attribute_value)
        
        delete_value_btn = QPushButton("Supprimer")
        delete_value_btn.clicked.connect(self.delete_attribute_value)
        
        values_btn_layout.addWidget(add_value_btn)
        values_btn_layout.addWidget(edit_value_btn)
        values_btn_layout.addWidget(delete_value_btn)
        
        values_layout.addLayout(values_btn_layout)
        h_layout.addLayout(values_layout)
        
        layout.addLayout(h_layout)
    
    def load_attributes(self):
        """Load attribute types"""
        self.attr_list.clear()
        
        attr_types = AttributeType.get_all()
        for attr_type in attr_types:
            self.attr_list.addItem(f"{attr_type.display_name} ({attr_type.name})")
            self.attr_list.item(self.attr_list.count() - 1).setData(Qt.UserRole, attr_type)
    
    def on_attribute_selected(self, row):
        """Load values for selected attribute type"""
        self.values_list.clear()
        
        if row < 0:
            return
        
        attr_type = self.attr_list.item(row).data(Qt.UserRole)
        if not attr_type:
            return
        
        values = AttributeValue.get_by_attribute_type(attr_type.id)
        for value in values:
            self.values_list.addItem(value.display_value)
            self.values_list.item(self.values_list.count() - 1).setData(Qt.UserRole, value)
    
    def add_attribute_type(self):
        """Add a new attribute type"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un attribut")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        name_edit = QLineEdit()
        form.addRow("Nom technique:", name_edit)
        
        display_name_edit = QLineEdit()
        form.addRow("Nom affiché:", display_name_edit)
        
        display_type_combo = QComboBox()
        display_type_combo.addItem("Boutons radio", "radio")
        display_type_combo.addItem("Liste déroulante", "select")
        display_type_combo.addItem("Couleurs", "color")
        display_type_combo.addItem("Images", "image")
        form.addRow("Type d'affichage:", display_type_combo)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            display_name = display_name_edit.text().strip()
            display_type = display_type_combo.currentData()
            
            if not name or not display_name:
                QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
                return
            
            # Create attribute type
            attr_type = AttributeType(
                name=name,
                display_name=display_name,
                display_type=display_type
            )
            
            if attr_type.save():
                self.load_attributes()
                
                # Select the new attribute
                for i in range(self.attr_list.count()):
                    item_attr = self.attr_list.item(i).data(Qt.UserRole)
                    if item_attr.id == attr_type.id:
                        self.attr_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement de l'attribut.")
    
    def edit_attribute_type(self):
        """Edit the selected attribute type"""
        row = self.attr_list.currentRow()
        if row < 0:
            return
        
        attr_type = self.attr_list.item(row).data(Qt.UserRole)
        if not attr_type:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifier l'attribut")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        name_edit = QLineEdit(attr_type.name)
        form.addRow("Nom technique:", name_edit)
        
        display_name_edit = QLineEdit(attr_type.display_name)
        form.addRow("Nom affiché:", display_name_edit)
        
        display_type_combo = QComboBox()
        display_type_combo.addItem("Boutons radio", "radio")
        display_type_combo.addItem("Liste déroulante", "select")
        display_type_combo.addItem("Couleurs", "color")
        display_type_combo.addItem("Images", "image")
        
        # Set current display type
        index = display_type_combo.findData(attr_type.display_type)
        if index >= 0:
            display_type_combo.setCurrentIndex(index)
            
        form.addRow("Type d'affichage:", display_type_combo)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            display_name = display_name_edit.text().strip()
            display_type = display_type_combo.currentData()
            
            if not name or not display_name:
                QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
                return
            
            # Update attribute type
            attr_type.name = name
            attr_type.display_name = display_name
            attr_type.display_type = display_type
            
            if attr_type.save():
                self.load_attributes()
                
                # Reselect the attribute
                for i in range(self.attr_list.count()):
                    item_attr = self.attr_list.item(i).data(Qt.UserRole)
                    if item_attr.id == attr_type.id:
                        self.attr_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement de l'attribut.")
    
    def delete_attribute_type(self):
        """Delete the selected attribute type"""
        row = self.attr_list.currentRow()
        if row < 0:
            return
        
        attr_type = self.attr_list.item(row).data(Qt.UserRole)
        if not attr_type:
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer l'attribut '{attr_type.display_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        # Delete attribute type
        if attr_type.delete():
            self.load_attributes()
            self.values_list.clear()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la suppression de l'attribut.")
    
    def add_attribute_value(self):
        """Add a value to the selected attribute type"""
        row = self.attr_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner un attribut.")
            return
        
        attr_type = self.attr_list.item(row).data(Qt.UserRole)
        if not attr_type:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ajouter une valeur pour {attr_type.display_name}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        value_edit = QLineEdit()
        form.addRow("Valeur technique:", value_edit)
        
        display_value_edit = QLineEdit()
        form.addRow("Valeur affichée:", display_value_edit)
        
        # Add color picker for color attributes
        html_color = None
        color_btn = None
        
        if attr_type.display_type == 'color':
            from PyQt5.QtGui import QColor
            from PyQt5.QtWidgets import QColorDialog
            
            def choose_color():
                nonlocal html_color
                color = QColorDialog.getColor(Qt.white, dialog, "Choisir une couleur")
                if color.isValid():
                    html_color = color.name()
                    color_btn.setStyleSheet(f"background-color: {html_color}; min-height: 30px;")
                    color_btn.setText("")
            
            color_btn = QPushButton("Choisir une couleur")
            color_btn.setMinimumHeight(30)
            color_btn.clicked.connect(choose_color)
            
            form.addRow("Couleur:", color_btn)
            
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            value = value_edit.text().strip()
            display_value = display_value_edit.text().strip()
            
            if not value or not display_value:
                QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
                return
            
            # Create attribute value
            attr_value = AttributeValue(
                attribute_type_id=attr_type.id,
                value=value,
                display_value=display_value,
                html_color=html_color
            )
            
            if attr_value.save():
                self.on_attribute_selected(row)
                
                # Select the new value
                for i in range(self.values_list.count()):
                    item_value = self.values_list.item(i).data(Qt.UserRole)
                    if item_value.id == attr_value.id:
                        self.values_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement de la valeur.")
    
    def edit_attribute_value(self):
        """Edit the selected attribute value"""
        attr_row = self.attr_list.currentRow()
        value_row = self.values_list.currentRow()
        
        if attr_row < 0 or value_row < 0:
            return
        
        attr_type = self.attr_list.item(attr_row).data(Qt.UserRole)
        attr_value = self.values_list.item(value_row).data(Qt.UserRole)
        
        if not attr_type or not attr_value:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifier la valeur")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        value_edit = QLineEdit(attr_value.value)
        form.addRow("Valeur technique:", value_edit)
        
        display_value_edit = QLineEdit(attr_value.display_value)
        form.addRow("Valeur affichée:", display_value_edit)
        
        # Add color picker for color attributes
        html_color = attr_value.html_color
        color_btn = None
        
        if attr_type.display_type == 'color':
            from PyQt5.QtGui import QColor
            from PyQt5.QtWidgets import QColorDialog
            
            def choose_color():
                nonlocal html_color
                color = QColorDialog.getColor(
                    QColor(html_color) if html_color else Qt.white,
                    dialog, "Choisir une couleur"
                )
                if color.isValid():
                    html_color = color.name()
                    color_btn.setStyleSheet(f"background-color: {html_color}; min-height: 30px;")
                    color_btn.setText("")
            
            color_btn = QPushButton("Choisir une couleur")
            color_btn.setMinimumHeight(30)
            color_btn.clicked.connect(choose_color)
            
            if html_color:
                color_btn.setStyleSheet(f"background-color: {html_color}; min-height: 30px;")
                color_btn.setText("")
            
            form.addRow("Couleur:", color_btn)
            
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            value = value_edit.text().strip()
            display_value = display_value_edit.text().strip()
            
            if not value or not display_value:
                QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
                return
            
            # Update attribute value
            attr_value.value = value
            attr_value.display_value = display_value
            attr_value.html_color = html_color
            
            if attr_value.save():
                self.on_attribute_selected(attr_row)
                
                # Reselect the value
                for i in range(self.values_list.count()):
                    item_value = self.values_list.item(i).data(Qt.UserRole)
                    if item_value.id == attr_value.id:
                        self.values_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement de la valeur.")
    
    def delete_attribute_value(self):
        """Delete the selected attribute value"""
        value_row = self.values_list.currentRow()
        if value_row < 0:
            return
        
        attr_value = self.values_list.item(value_row).data(Qt.UserRole)
        if not attr_value:
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer la valeur '{attr_value.display_value}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        # Delete attribute value
        if attr_value.delete():
            attr_row = self.attr_list.currentRow()
            if attr_row >= 0:
                self.on_attribute_selected(attr_row)
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la suppression de la valeur.")


class ProductVariantsTab(QWidget):
    """Tab for configuring product variants"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.products = []
        self.init_ui()
        self.load_products()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Product selection section
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Sélectionnez un produit:"))
        
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.on_product_selected)
        selection_layout.addWidget(self.product_combo, 1)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self.load_products)
        selection_layout.addWidget(refresh_btn)
        
        layout.addLayout(selection_layout)
        
        # Current configuration
        config_layout = QVBoxLayout()
        config_layout.addWidget(QLabel("<b>Configuration actuelle</b>"))
        
        self.attributes_table = QTableWidget()
        self.attributes_table.setColumnCount(3)
        self.attributes_table.setHorizontalHeaderLabels(["Attribut", "Valeurs", "Prix"])
        self.attributes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        config_layout.addWidget(self.attributes_table)
        
        # Configuration buttons
        config_btn_layout = QHBoxLayout()
        
        add_attr_btn = QPushButton("Ajouter un attribut")
        add_attr_btn.clicked.connect(self.add_product_attribute)
        
        manage_attr_btn = QPushButton("Gérer les valeurs")
        manage_attr_btn.clicked.connect(self.manage_attribute_values)
        
        config_btn_layout.addWidget(add_attr_btn)
        config_btn_layout.addWidget(manage_attr_btn)
        config_btn_layout.addStretch()
        
        config_layout.addLayout(config_btn_layout)
        layout.addLayout(config_layout)
        
        # Variants section
        variants_layout = QVBoxLayout()
        variants_layout.addWidget(QLabel("<b>Variantes générées</b>"))
        
        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(4)
        self.variants_table.setHorizontalHeaderLabels(["Variante", "SKU", "Prix", "Attributs"])
        self.variants_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        variants_layout.addWidget(self.variants_table)
        
        # Variant buttons
        variant_btn_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Générer les variantes")
        generate_btn.clicked.connect(self.generate_variants)
        
        test_ui_btn = QPushButton("Tester l'interface client")
        test_ui_btn.clicked.connect(self.test_client_ui)
        
        variant_btn_layout.addWidget(generate_btn)
        variant_btn_layout.addWidget(test_ui_btn)
        variant_btn_layout.addStretch()
        
        variants_layout.addLayout(variant_btn_layout)
        layout.addLayout(variants_layout)
    
    def load_products(self):
        """Load products from database"""
        try:
            products = Product.get_all_products()
            
            if not products:
                QMessageBox.warning(self, "Attention", "Aucun produit trouvé dans la base de données.")
                return
            
            self.products = products
            
            # Update combo box
            self.product_combo.clear()
            for product in products:
                self.product_combo.addItem(
                    f"{product['id']} - {product['name']}",
                    product['id']
                )
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des produits: {str(e)}")
    
    def on_product_selected(self, index):
        """Handle product selection"""
        if index < 0:
            return
        
        product_id = self.product_combo.currentData()
        self.load_product_attributes(product_id)
        self.load_product_variants(product_id)
    
    def load_product_attributes(self, product_id):
        """Load attributes for the selected product"""
        self.attributes_table.setRowCount(0)
        
        # Get product attributes
        try:
            from variant_system.attribute_manager import get_product_attributes_with_values
            attributes = get_product_attributes_with_values(product_id)
            
            for i, attr in enumerate(attributes):
                self.attributes_table.insertRow(i)
                
                # Attribute name
                name_item = QTableWidgetItem(attr['type']['display_name'])
                self.attributes_table.setItem(i, 0, name_item)
                
                # Values
                values = [value['display_value'] for value in attr['values']]
                values_item = QTableWidgetItem(", ".join(values))
                self.attributes_table.setItem(i, 1, values_item)
                
                # Price extras
                price_extras = []
                for value in attr['values']:
                    if value['price_adjustment'] != 0:
                        sign = "+" if value['price_adjustment'] > 0 else ""
                        price_extras.append(
                            f"{value['display_value']}: {sign}{value['price_adjustment']:.2f}"
                        )
                
                price_item = QTableWidgetItem(", ".join(price_extras) if price_extras else "-")
                self.attributes_table.setItem(i, 2, price_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des attributs: {str(e)}")
    
    def load_product_variants(self, product_id):
        """Load variants for the selected product"""
        self.variants_table.setRowCount(0)
        
        # Get product variants
        try:
            from variant_system.variant_manager import ProductVariant, get_variant_with_attributes
            variants = ProductVariant.get_by_product(product_id)
            
            for i, variant in enumerate(variants):
                self.variants_table.insertRow(i)
                
                # Get variant details
                variant_details = get_variant_with_attributes(variant.id)
                
                # Variant name
                name_item = QTableWidgetItem(variant.name)
                self.variants_table.setItem(i, 0, name_item)
                
                # SKU
                sku_item = QTableWidgetItem(variant.sku or "")
                self.variants_table.setItem(i, 1, sku_item)
                
                # Price
                price = variant.final_price or variant.base_price or 0
                price_item = QTableWidgetItem(f"{price:.2f}")
                self.variants_table.setItem(i, 2, price_item)
                
                # Attributes
                attrs = []
                if variant_details and variant_details['attributes']:
                    for attr_type_id, attr_data in variant_details['attributes'].items():
                        attrs.append(f"{attr_data['type_display_name']}: {attr_data['display_value']}")
                
                attrs_item = QTableWidgetItem(", ".join(attrs))
                self.variants_table.setItem(i, 3, attrs_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des variantes: {str(e)}")
    
    def add_product_attribute(self):
        """Add an attribute to the selected product"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner un produit.")
            return
        
        # Get all attributes
        attributes = AttributeType.get_all()
        if not attributes:
            QMessageBox.warning(self, "Attention", "Aucun attribut n'est défini dans le système.")
            return
        
        # Get attributes already assigned to this product
        product_attributes = ProductAttribute.get_by_product(product_id)
        existing_attr_ids = [pa.attribute_type_id for pa in product_attributes]
        
        # Filter out attributes already assigned
        available_attributes = [attr for attr in attributes if attr.id not in existing_attr_ids]
        
        if not available_attributes:
            QMessageBox.information(self, "Information", "Toutes les attributs disponibles ont déjà été ajoutés à ce produit.")
            return
        
        # Create dialog to select attribute
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un attribut au produit")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        attr_combo = QComboBox()
        for attr in available_attributes:
            attr_combo.addItem(attr.display_name, attr.id)
            
        form.addRow("Attribut:", attr_combo)
        
        # Options
        required_check = QCheckBox("Obligatoire")
        required_check.setChecked(True)
        form.addRow("", required_check)
        
        affects_price_check = QCheckBox("Affecte le prix")
        affects_price_check.setChecked(True)
        form.addRow("", affects_price_check)
        
        affects_inventory_check = QCheckBox("Affecte l'inventaire")
        affects_inventory_check.setChecked(True)
        form.addRow("", affects_inventory_check)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            attr_id = attr_combo.currentData()
            
            # Create product attribute
            product_attr = ProductAttribute(
                product_id=product_id,
                attribute_type_id=attr_id,
                is_required=required_check.isChecked(),
                affects_price=affects_price_check.isChecked(),
                affects_inventory=affects_inventory_check.isChecked()
            )
            
            if product_attr.save():
                self.load_product_attributes(product_id)
                
                # Ask if user wants to add values
                confirm = QMessageBox.question(
                    self,
                    "Ajouter des valeurs",
                    "Voulez-vous ajouter des valeurs pour cet attribut maintenant?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if confirm == QMessageBox.Yes:
                    self.manage_attribute_values()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de l'ajout de l'attribut.")
    
    def manage_attribute_values(self):
        """Manage attribute values for the selected product/attribute"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner un produit.")
            return
        
        # Get product attributes
        product_attributes = ProductAttribute.get_by_product(product_id)
        if not product_attributes:
            QMessageBox.warning(self, "Attention", "Ce produit n'a pas d'attributs configurés.")
            return
        
        # Create dialog to select attribute
        dialog = QDialog(self)
        dialog.setWindowTitle("Gérer les valeurs d'attribut")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Attribute selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Attribut:"))
        
        attr_combo = QComboBox()
        for attr in product_attributes:
            attr_type = attr.attribute_type
            if attr_type:
                attr_combo.addItem(attr_type.display_name, attr.id)
        
        attr_combo.currentIndexChanged.connect(
            lambda: load_attribute_values(attr_combo.currentData())
        )
        
        selection_layout.addWidget(attr_combo, 1)
        layout.addLayout(selection_layout)
        
        # Values table
        values_table = QTableWidget()
        values_table.setColumnCount(3)
        values_table.setHorizontalHeaderLabels(["Valeur", "Prix", "Par défaut"])
        values_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(values_table)
        
        # Value buttons
        value_btn_layout = QHBoxLayout()
        
        def add_value():
            """Add a value to the selected attribute"""
            attr_id = attr_combo.currentData()
            if not attr_id:
                return
            
            # Get attribute type
            attr = next((a for a in product_attributes if a.id == attr_id), None)
            if not attr or not attr.attribute_type:
                return
            
            attr_type = attr.attribute_type
            
            # Get attribute values
            all_values = AttributeValue.get_by_attribute_type(attr_type.id)
            
            # Get values already added to this product attribute
            existing_values = attr.values
            existing_value_ids = [v.attribute_value_id for v in existing_values]
            
            # Filter out values already assigned
            available_values = [v for v in all_values if v.id not in existing_value_ids]
            
            if not available_values:
                QMessageBox.information(
                    dialog,
                    "Information",
                    "Toutes les valeurs disponibles ont déjà été ajoutées à cet attribut."
                )
                return
            
            # Create dialog to select value
            value_dialog = QDialog(dialog)
            value_dialog.setWindowTitle(f"Ajouter une valeur pour {attr_type.display_name}")
            value_dialog.setMinimumWidth(400)
            
            val_layout = QVBoxLayout(value_dialog)
            
            # Form
            val_form = QFormLayout()
            
            value_combo = QComboBox()
            for value in available_values:
                value_combo.addItem(value.display_value, value.id)
                
            val_form.addRow("Valeur:", value_combo)
            
            price_spin = QDoubleSpinBox()
            price_spin.setPrefix("+")
            price_spin.setRange(-10000, 10000)
            price_spin.setDecimals(2)
            val_form.addRow("Supplément de prix:", price_spin)
            
            default_check = QCheckBox("Valeur par défaut")
            val_form.addRow("", default_check)
            
            val_layout.addLayout(val_form)
            
            # Buttons
            val_btn_layout = QHBoxLayout()
            
            add_btn = QPushButton("Ajouter")
            add_btn.clicked.connect(value_dialog.accept)
            
            cancel_btn = QPushButton("Annuler")
            cancel_btn.clicked.connect(value_dialog.reject)
            
            val_btn_layout.addWidget(add_btn)
            val_btn_layout.addWidget(cancel_btn)
            
            val_layout.addLayout(val_btn_layout)
            
            # Show dialog
            if value_dialog.exec_() == QDialog.Accepted:
                value_id = value_combo.currentData()
                
                # Create product attribute value
                product_attr_value = ProductAttributeValue(
                    product_attribute_id=attr_id,
                    attribute_value_id=value_id,
                    price_adjustment=price_spin.value(),
                    is_default=default_check.isChecked()
                )
                
                if product_attr_value.save():
                    load_attribute_values(attr_id)
                else:
                    QMessageBox.critical(
                        dialog,
                        "Erreur",
                        "Erreur lors de l'ajout de la valeur."
                    )
        
        def edit_value():
            """Edit the selected value"""
            selected_items = values_table.selectedItems()
            if not selected_items:
                return
            
            row = selected_items[0].row()
            value_item = values_table.item(row, 0)
            if not value_item:
                return
            
            # Get product attribute value
            product_attr_value = value_item.data(Qt.UserRole)
            if not product_attr_value:
                return
            
            # Get attribute value
            attr_value = product_attr_value.attribute_value
            if not attr_value:
                return
            
            # Create dialog
            value_dialog = QDialog(dialog)
            value_dialog.setWindowTitle(f"Modifier la valeur {attr_value.display_value}")
            value_dialog.setMinimumWidth(400)
            
            val_layout = QVBoxLayout(value_dialog)
            
            # Form
            val_form = QFormLayout()
            
            price_spin = QDoubleSpinBox()
            price_spin.setPrefix("+")
            price_spin.setRange(-10000, 10000)
            price_spin.setDecimals(2)
            price_spin.setValue(product_attr_value.price_adjustment)
            val_form.addRow("Supplément de prix:", price_spin)
            
            default_check = QCheckBox("Valeur par défaut")
            default_check.setChecked(product_attr_value.is_default)
            val_form.addRow("", default_check)
            
            val_layout.addLayout(val_form)
            
            # Buttons
            val_btn_layout = QHBoxLayout()
            
            save_btn = QPushButton("Enregistrer")
            save_btn.clicked.connect(value_dialog.accept)
            
            cancel_btn = QPushButton("Annuler")
            cancel_btn.clicked.connect(value_dialog.reject)
            
            val_btn_layout.addWidget(save_btn)
            val_btn_layout.addWidget(cancel_btn)
            
            val_layout.addLayout(val_btn_layout)
            
            # Show dialog
            if value_dialog.exec_() == QDialog.Accepted:
                # Update product attribute value
                product_attr_value.price_adjustment = price_spin.value()
                product_attr_value.is_default = default_check.isChecked()
                
                if product_attr_value.save():
                    load_attribute_values(attr_combo.currentData())
                else:
                    QMessageBox.critical(
                        dialog,
                        "Erreur",
                        "Erreur lors de la modification de la valeur."
                    )
        
        def delete_value():
            """Delete the selected value"""
            selected_items = values_table.selectedItems()
            if not selected_items:
                return
            
            row = selected_items[0].row()
            value_item = values_table.item(row, 0)
            if not value_item:
                return
            
            # Get product attribute value
            product_attr_value = value_item.data(Qt.UserRole)
            if not product_attr_value:
                return
            
            # Get attribute value
            attr_value = product_attr_value.attribute_value
            if not attr_value:
                return
            
            # Confirm deletion
            confirm = QMessageBox.question(
                dialog,
                "Confirmation",
                f"Êtes-vous sûr de vouloir supprimer la valeur '{attr_value.display_value}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
            
            # Delete product attribute value
            if product_attr_value.delete():
                load_attribute_values(attr_combo.currentData())
            else:
                QMessageBox.critical(
                    dialog,
                    "Erreur",
                    "Erreur lors de la suppression de la valeur."
                )
        
        def load_attribute_values(attr_id):
            """Load values for the selected attribute"""
            values_table.setRowCount(0)
            
            if not attr_id:
                return
            
            # Get attribute
            attr = next((a for a in product_attributes if a.id == attr_id), None)
            if not attr:
                return
            
            # Get values
            values = attr.values
            
            for i, value in enumerate(values):
                values_table.insertRow(i)
                
                # Get attribute value
                attr_value = value.attribute_value
                if not attr_value:
                    continue
                
                # Value
                value_item = QTableWidgetItem(attr_value.display_value)
                value_item.setData(Qt.UserRole, value)
                values_table.setItem(i, 0, value_item)
                
                # Price adjustment
                price_text = f"+{value.price_adjustment:.2f}" if value.price_adjustment >= 0 else f"{value.price_adjustment:.2f}"
                price_item = QTableWidgetItem(price_text)
                values_table.setItem(i, 1, price_item)
                
                # Default
                default_item = QTableWidgetItem("✓" if value.is_default else "")
                default_item.setTextAlignment(Qt.AlignCenter)
                values_table.setItem(i, 2, default_item)
        
        add_value_btn = QPushButton("Ajouter une valeur")
        add_value_btn.clicked.connect(add_value)
        
        edit_value_btn = QPushButton("Modifier")
        edit_value_btn.clicked.connect(edit_value)
        
        delete_value_btn = QPushButton("Supprimer")
        delete_value_btn.clicked.connect(delete_value)
        
        value_btn_layout.addWidget(add_value_btn)
        value_btn_layout.addWidget(edit_value_btn)
        value_btn_layout.addWidget(delete_value_btn)
        
        layout.addLayout(value_btn_layout)
        
        # Close button
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        # Load values for first attribute
        if attr_combo.count() > 0:
            load_attribute_values(attr_combo.currentData())
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            self.load_product_attributes(product_id)
    
    def generate_variants(self):
        """Generate variants for the selected product"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner un produit.")
            return
        
        # Check if the product has attributes
        product_attributes = ProductAttribute.get_by_product(product_id)
        if not product_attributes:
            QMessageBox.warning(self, "Attention", "Ce produit n'a pas d'attributs configurés.")
            return
        
        # Check if variants already exist
        existing_variants = ProductVariant.get_by_product(product_id)
        if existing_variants:
            confirm = QMessageBox.question(
                self,
                "Variantes existantes",
                f"Ce produit a déjà {len(existing_variants)} variantes. Voulez-vous générer de nouvelles variantes?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
        
        # Create dialog for generation options
        dialog = QDialog(self)
        dialog.setWindowTitle("Générer des variantes")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        # Get product info
        product = None
        try:
            product = Product.get_by_id(product_id)
        except:
            pass
        
        # Base price
        base_price_spin = QDoubleSpinBox()
        base_price_spin.setRange(0, 99999)
        base_price_spin.setDecimals(2)
        base_price_spin.setValue(product.get('unit_price', 0) if product else 0)
        form.addRow("Prix de base:", base_price_spin)
        
        # Cost price
        cost_price_spin = QDoubleSpinBox()
        cost_price_spin.setRange(0, 99999)
        cost_price_spin.setDecimals(2)
        cost_price_spin.setValue(product.get('purchase_price', 0) if product else 0)
        form.addRow("Prix de revient:", cost_price_spin)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Générer")
        generate_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(generate_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Generate variants
            base_price = base_price_spin.value()
            cost_price = cost_price_spin.value()
            
            variant_ids = generate_variants_for_product(product_id, base_price, cost_price)
            
            if variant_ids:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"{len(variant_ids)} variantes ont été générées avec succès."
                )
                
                self.load_product_variants(product_id)
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors de la génération des variantes."
                )
    
    def test_client_ui(self):
        """Test the client UI for variant selection"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner un produit.")
            return
        
        # Check if the product has variants
        variants = ProductVariant.get_by_product(product_id)
        if not variants:
            QMessageBox.warning(
                self,
                "Attention",
                "Ce produit n'a pas de variantes. Veuillez d'abord générer des variantes."
            )
            return
        
        # Get product info
        product = None
        try:
            product = Product.get_by_id(product_id)
        except:
            product = {"id": product_id, "name": f"Produit {product_id}", "unit_price": 0}
        
        # Show client UI
        selected_variant = select_product_variant(product_id, product, self)
        
        if selected_variant:
            # Show result
            attr_values = []
            for attr_id, value_id in selected_variant['attribute_values'].items():
                # Get attribute type and value
                from variant_system.attribute_manager import AttributeType, AttributeValue
                attr_type = AttributeType.get_by_id(attr_id)
                attr_value = AttributeValue.get_by_id(value_id)
                
                if attr_type and attr_value:
                    attr_values.append(f"{attr_type.display_name}: {attr_value.display_value}")
            
            result_text = f"Variante sélectionnée:\n\n"
            result_text += f"Attributs: {', '.join(attr_values)}\n"
            result_text += f"Prix: {selected_variant['price']:.2f}\n"
            
            if selected_variant.get('needs_creation', False):
                result_text += "\nCette variante n'existe pas encore et devra être créée."
            else:
                result_text += f"\nID de variante: {selected_variant['variant_id']}"
            
            QMessageBox.information(self, "Résultat", result_text)
        else:
            QMessageBox.information(self, "Information", "Aucune variante sélectionnée.")


class VariantSystemExample(QMainWindow):
    """Main window for the variant system example"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Système de Variantes - Exemple")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Initialisation du système de variantes...")
        self.status_label.setStyleSheet("font-style: italic; color: #666;")
        main_layout.addWidget(self.status_label)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Attribute manager tab
        self.attr_tab = AttributeManagerTab()
        self.tabs.addTab(self.attr_tab, "Gestion des attributs")
        
        # Product variants tab
        self.product_tab = ProductVariantsTab()
        self.tabs.addTab(self.product_tab, "Variantes de produits")
        
        main_layout.addWidget(self.tabs)
        
        # Initialize the system
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize the variant system"""
        try:
            success = initialize()
            
            if success:
                self.status_label.setText("✅ Système de variantes initialisé avec succès.")
                self.status_label.setStyleSheet("color: #28a745;")
            else:
                self.status_label.setText("❌ Erreur lors de l'initialisation du système de variantes.")
                self.status_label.setStyleSheet("color: #dc3545;")
        except Exception as e:
            self.status_label.setText(f"❌ Erreur: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VariantSystemExample()
    window.show()
    sys.exit(app.exec_())
