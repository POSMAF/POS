"""
Client Interface Module

This module provides components for the client-facing interface for selecting
product variants with their attributes.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QGroupBox, QRadioButton, QButtonGroup, QComboBox, QFrame,
    QGridLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QFont

from .attribute_manager import get_product_attributes_with_values
from .variant_manager import find_variant_by_attribute_values, calculate_variant_price
from .rules_engine import RulesEngine

class VariantSelectorDialog(QDialog):
    """Dialog for selecting product variants with attributes"""
    
    variantSelected = pyqtSignal(dict)  # Emits the selected variant
    
    def __init__(self, product_id, product_data, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.product_data = product_data
        self.attribute_widgets = {}  # Maps attribute_id to its widget (ButtonGroup/ComboBox)
        self.selected_values = {}    # Maps attribute_id to selected value_id
        self.rules_engine = RulesEngine(product_id)
        self.init_ui()
        self.load_attributes()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set dialog properties
        self.setWindowTitle(f"Sélectionner une variante: {self.product_data.get('name', '')}")
        self.setMinimumSize(500, 400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Product info
        self.product_header = QLabel(f"<h2>{self.product_data.get('name', '')}</h2>")
        self.product_header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.product_header)
        
        # Price display
        self.price_frame = QFrame()
        self.price_frame.setFrameShape(QFrame.StyledPanel)
        self.price_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        price_layout = QVBoxLayout(self.price_frame)
        
        self.base_price_label = QLabel(f"Prix de base: {self.product_data.get('unit_price', 0):.2f}")
        self.adjustment_label = QLabel("Suppléments: 0.00")
        self.final_price_label = QLabel(f"Prix final: {self.product_data.get('unit_price', 0):.2f}")
        self.final_price_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #28a745;")
        
        price_layout.addWidget(self.base_price_label)
        price_layout.addWidget(self.adjustment_label)
        price_layout.addWidget(self.final_price_label)
        
        main_layout.addWidget(self.price_frame)
        
        # Attribute selection area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.attribute_container = QWidget()
        self.attribute_layout = QVBoxLayout(self.attribute_container)
        self.attribute_layout.setSpacing(15)
        
        scroll_area.setWidget(self.attribute_container)
        main_layout.addWidget(scroll_area, 1)  # Give stretch factor
        
        # Status message area
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #dc3545; font-style: italic;")
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("Sélectionner")
        self.select_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.select_variant)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.select_btn)
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def load_attributes(self):
        """Load product attributes and build UI components"""
        try:
            # Get attributes with values
            attributes = get_product_attributes_with_values(self.product_id)
            
            if not attributes:
                self.status_label.setText("Ce produit n'a pas d'attributs configurés.")
                self.status_label.setVisible(True)
                return
            
            # Create widgets for each attribute
            for attr in attributes:
                self.create_attribute_widget(attr)
            
            # Add stretch at the end
            self.attribute_layout.addStretch()
            
        except Exception as e:
            print(f"Error loading attributes: {e}")
            self.status_label.setText(f"Erreur lors du chargement des attributs: {str(e)}")
            self.status_label.setVisible(True)
    
    def create_attribute_widget(self, attribute):
        """Create appropriate widget for an attribute based on its display type"""
        attribute_id = attribute['type']['id']
        display_type = attribute['type']['display_type']
        display_name = attribute['type']['display_name']
        values = attribute['values']
        
        if not values:
            return
        
        # Create attribute group
        group_box = QGroupBox(display_name)
        group_layout = QVBoxLayout(group_box)
        
        # Create widget based on display type
        if display_type == 'radio' or display_type == 'pills':
            # Create radio buttons in a button group
            button_group = QButtonGroup(self)
            button_group.setExclusive(True)
            
            # For 'pills' type, use a horizontal grid layout
            if display_type == 'pills':
                pills_layout = QGridLayout()
                pills_layout.setSpacing(5)
                col_count = 4  # Number of pills per row
                row, col = 0, 0
            
            for i, value in enumerate(values):
                value_id = value['attribute_value_id']
                display_value = value['display_value']
                price_extra = value['price_adjustment']
                
                # Create radio button
                radio = QRadioButton(display_value)
                radio.setProperty('value_id', value_id)
                radio.setProperty('price_extra', price_extra)
                
                if price_extra != 0:
                    price_sign = "+" if price_extra > 0 else ""
                    radio.setText(f"{display_value} ({price_sign}{price_extra:.2f})")
                
                button_group.addButton(radio, i)
                
                # Add to layout
                if display_type == 'pills':
                    pills_layout.addWidget(radio, row, col)
                    col += 1
                    if col >= col_count:
                        col = 0
                        row += 1
                else:
                    group_layout.addWidget(radio)
            
            # Add the pills layout if using pill type
            if display_type == 'pills':
                group_layout.addLayout(pills_layout)
            
            # Connect button group to handler
            button_group.buttonClicked.connect(lambda btn: self.on_attribute_changed(attribute_id, btn.property('value_id'), btn.property('price_extra')))
            
            # Store reference
            self.attribute_widgets[attribute_id] = button_group
            
        elif display_type == 'select':
            # Create a combo box
            combo = QComboBox()
            combo.addItem("Sélectionnez...", None)  # Default empty option
            
            for value in values:
                value_id = value['attribute_value_id']
                display_value = value['display_value']
                price_extra = value['price_adjustment']
                
                if price_extra != 0:
                    price_sign = "+" if price_extra > 0 else ""
                    display_value = f"{display_value} ({price_sign}{price_extra:.2f})"
                
                # Add to combo box, storing value_id and price_extra in item data
                combo.addItem(display_value, value_id)
                idx = combo.count() - 1
                combo.setItemData(idx, price_extra, Qt.UserRole + 1)
            
            # Connect to handler
            combo.currentIndexChanged.connect(lambda: self.on_combo_changed(attribute_id, combo))
            
            # Add to layout
            group_layout.addWidget(combo)
            
            # Store reference
            self.attribute_widgets[attribute_id] = combo
            
        elif display_type == 'color':
            # Create a grid of color buttons
            color_layout = QGridLayout()
            color_layout.setSpacing(5)
            col_count = 5  # Number of colors per row
            row, col = 0, 0
            
            # Create button group
            color_group = QButtonGroup(self)
            color_group.setExclusive(True)
            
            for i, value in enumerate(values):
                value_id = value['attribute_value_id']
                display_value = value['display_value']
                html_color = value.get('html_color', '#FFFFFF')
                price_extra = value['price_adjustment']
                
                # Create color button
                color_btn = QPushButton()
                color_btn.setFixedSize(40, 40)
                color_btn.setCheckable(True)
                
                if html_color:
                    color_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {html_color};
                            border: 1px solid #ccc;
                            border-radius: 20px;
                        }}
                        QPushButton:checked {{
                            border: 3px solid #000;
                        }}
                    """)
                
                # Set tooltip with name and price
                tooltip = display_value
                if price_extra != 0:
                    price_sign = "+" if price_extra > 0 else ""
                    tooltip += f" ({price_sign}{price_extra:.2f})"
                color_btn.setToolTip(tooltip)
                
                # Set properties for handler
                color_btn.setProperty('value_id', value_id)
                color_btn.setProperty('price_extra', price_extra)
                
                # Add to group and layout
                color_group.addButton(color_btn, i)
                color_layout.addWidget(color_btn, row, col)
                
                # Move to next position
                col += 1
                if col >= col_count:
                    col = 0
                    row += 1
            
            # Add color layout to group
            group_layout.addLayout(color_layout)
            
            # Add value labels if there are prices
            has_price_extras = any(value['price_adjustment'] != 0 for value in values)
            if has_price_extras:
                # Add a layout with price information
                price_info_layout = QHBoxLayout()
                price_info_label = QLabel("* Les prix sont indiqués dans les info-bulles")
                price_info_label.setStyleSheet("font-style: italic; color: #6c757d;")
                price_info_layout.addWidget(price_info_label)
                price_info_layout.addStretch()
                group_layout.addLayout(price_info_layout)
            
            # Connect group to handler
            color_group.buttonClicked.connect(lambda btn: self.on_attribute_changed(attribute_id, btn.property('value_id'), btn.property('price_extra')))
            
            # Store reference
            self.attribute_widgets[attribute_id] = color_group
        
        # Add group box to main layout
        self.attribute_layout.addWidget(group_box)
        
        # Set required indicator if applicable
        if attribute.get('is_required', True):
            group_box.setTitle(f"{display_name} *")
    
    def on_attribute_changed(self, attribute_id, value_id, price_extra):
        """Handle attribute value selection"""
        if value_id is None:
            # Remove from selected values if None
            if attribute_id in self.selected_values:
                del self.selected_values[attribute_id]
        else:
            # Update selected values
            self.selected_values[attribute_id] = value_id
        
        # Update price display
        self.update_price_display()
        
        # Validate selection
        self.validate_selection()
    
    def on_combo_changed(self, attribute_id, combo):
        """Handle combo box selection change"""
        index = combo.currentIndex()
        value_id = combo.itemData(index)
        price_extra = combo.itemData(index, Qt.UserRole + 1) if index > 0 else 0
        
        self.on_attribute_changed(attribute_id, value_id, price_extra)
    
    def update_price_display(self):
        """Update the price display based on selected attributes"""
        try:
            # Get base product price
            base_price = float(self.product_data.get('unit_price', 0))
            
            # Calculate price with selected attributes
            attr_value_ids = list(self.selected_values.values())
            
            if attr_value_ids:
                price_info = calculate_variant_price(self.product_id, attr_value_ids)
                
                if price_info:
                    # Update display
                    self.base_price_label.setText(f"Prix de base: {price_info['base_price']:.2f}")
                    self.adjustment_label.setText(f"Suppléments: {price_info['adjustment_amount']:.2f}")
                    self.final_price_label.setText(f"Prix final: {price_info['final_price']:.2f}")
                    return
            
            # Default if no selection or calculation failed
            self.base_price_label.setText(f"Prix de base: {base_price:.2f}")
            self.adjustment_label.setText("Suppléments: 0.00")
            self.final_price_label.setText(f"Prix final: {base_price:.2f}")
            
        except Exception as e:
            print(f"Error updating price display: {e}")
    
    def validate_selection(self):
        """Validate the current attribute selection"""
        try:
            # Get all attributes for this product
            attributes = get_product_attributes_with_values(self.product_id)
            
            # Check if all required attributes are selected
            required_selected = True
            for attr in attributes:
                if attr.get('is_required', True):
                    if attr['type']['id'] not in self.selected_values:
                        required_selected = False
                        break
            
            # Validate against rules engine
            valid_combo, error_msg = self.rules_engine.validate_combination(self.selected_values)
            
            if not valid_combo:
                self.status_label.setText(error_msg)
                self.status_label.setVisible(True)
                self.select_btn.setEnabled(False)
                return
            
            # If all required are selected and valid, enable the select button
            self.select_btn.setEnabled(required_selected)
            self.status_label.setVisible(False)
            
        except Exception as e:
            print(f"Error validating selection: {e}")
            self.status_label.setText(f"Erreur lors de la validation: {str(e)}")
            self.status_label.setVisible(True)
            self.select_btn.setEnabled(False)
    
    def select_variant(self):
        """Select the current variant configuration"""
        try:
            # Find matching variant
            attr_type_ids = {}
            for attr_id, value_id in self.selected_values.items():
                attr_type_ids[attr_id] = value_id
            
            variant_id = find_variant_by_attribute_values(self.product_id, attr_type_ids)
            
            if variant_id:
                # Emit the variant ID
                self.variantSelected.emit({
                    'variant_id': variant_id,
                    'attribute_values': self.selected_values
                })
                self.accept()
            else:
                # Calculate price and create a custom variant result
                price_info = calculate_variant_price(self.product_id, list(self.selected_values.values()))
                
                if price_info:
                    result = {
                        'variant_id': None,  # No existing variant
                        'attribute_values': self.selected_values,
                        'price': price_info['final_price'],
                        'needs_creation': True
                    }
                    self.variantSelected.emit(result)
                    self.accept()
                else:
                    QMessageBox.warning(
                        self,
                        "Attention",
                        "Impossible de déterminer le prix de cette combinaison. Veuillez contacter un administrateur."
                    )
            
        except Exception as e:
            print(f"Error selecting variant: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur s'est produite lors de la sélection de la variante: {str(e)}"
            )


def select_product_variant(product_id, product_data, parent=None):
    """
    Show the variant selector dialog for a product
    
    Args:
        product_id: The product ID
        product_data: Dictionary with basic product data (name, price, etc.)
        parent: Parent widget
        
    Returns:
        Selected variant data or None if canceled
    """
    dialog = VariantSelectorDialog(product_id, product_data, parent)
    
    if dialog.exec_() == QDialog.Accepted:
        # Get the selected variant from dialog's state
        variant_selection = {
            'attribute_values': dialog.selected_values,
            'price': float(dialog.final_price_label.text().split(":")[-1].strip().split()[0])
        }
        
        # Find matching variant in database
        attr_type_ids = {}
        for attr_id, value_id in dialog.selected_values.items():
            attr_type_ids[attr_id] = value_id
            
        variant_id = find_variant_by_attribute_values(product_id, attr_type_ids)
        
        if variant_id:
            variant_selection['variant_id'] = variant_id
            variant_selection['needs_creation'] = False
        else:
            variant_selection['variant_id'] = None
            variant_selection['needs_creation'] = True
        
        return variant_selection
    
    return None
