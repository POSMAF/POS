from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QTextEdit, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QGroupBox,
    QDialogButtonBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
from models.product import Product
from datetime import datetime
import json

class StockManagementDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.init_ui()
        self.load_stock_movements()

    def init_ui(self):
        """Initialize the UI elements"""
        self.setWindowTitle(f"Gestion de stock: {self.product['name']}")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        main_layout = QVBoxLayout(self)

        # Product info header
        self.create_product_header(main_layout)
        
        # Stock adjustment tools
        adjustment_group = QGroupBox("Ajustement de stock")
        adjustment_layout = QVBoxLayout(adjustment_group)
        
        # Movement type selection
        movement_layout = QHBoxLayout()
        movement_layout.addWidget(QLabel("Type de mouvement:"))
        
        self.movement_type = QComboBox()
        self.movement_type.addItems([
            "Entrée (augmentation)",
            "Sortie (diminution)",
            "Ajustement (inventaire)"
        ])
        movement_layout.addWidget(self.movement_type)
        
        # Quantity adjustment
        movement_layout.addWidget(QLabel("Quantité:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 10000)
        self.quantity_spin.setValue(1)
        movement_layout.addWidget(self.quantity_spin)
        
        # Price adjustment for incoming stock
        movement_layout.addWidget(QLabel("Prix unitaire:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 100000)
        self.price_spin.setValue(float(self.product.get('purchase_price', 0)))
        self.price_spin.setSuffix(" MAD")
        movement_layout.addWidget(self.price_spin)
        
        adjustment_layout.addLayout(movement_layout)
        
        # Reason and notes
        reason_layout = QHBoxLayout()
        reason_layout.addWidget(QLabel("Référence:"))
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Ex: Commande #1234, Inventaire, etc.")
        reason_layout.addWidget(self.reference_edit)
        adjustment_layout.addLayout(reason_layout)
        
        note_layout = QHBoxLayout()
        note_layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Détails supplémentaires...")
        self.notes_edit.setMaximumHeight(60)
        note_layout.addWidget(self.notes_edit)
        adjustment_layout.addLayout(note_layout)
        
        # Apply adjustment button
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()
        self.apply_btn = QPushButton("Appliquer l'ajustement")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_stock_adjustment)
        apply_layout.addWidget(self.apply_btn)
        adjustment_layout.addLayout(apply_layout)
        
        main_layout.addWidget(adjustment_group)
        
        # Stock movement history
        history_group = QGroupBox("Historique des mouvements")
        history_layout = QVBoxLayout(history_group)
        
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(7)
        self.movements_table.setHorizontalHeaderLabels([
            "Date", "Type", "Quantité", "Prix unitaire", "Total", "Référence", "Actions"
        ])
        
        self.movements_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.movements_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.movements_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.movements_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.movements_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.movements_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.movements_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.movements_table.setColumnWidth(6, 80)
        
        history_layout.addWidget(self.movements_table)
        
        main_layout.addWidget(history_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def create_product_header(self, layout):
        """Create the product information header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        # Product name and ID
        info_layout = QVBoxLayout()
        product_name = QLabel(self.product['name'])
        product_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addWidget(product_name)
        
        product_id = QLabel(f"ID: {self.product['id']} | Code: {self.product.get('barcode', 'N/A')}")
        product_id.setStyleSheet("color: #6c757d;")
        info_layout.addWidget(product_id)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        # Current stock and value info
        stock_layout = QVBoxLayout()
        current_stock = QLabel(f"Stock actuel: {self.product['stock']}")
        current_stock.setStyleSheet("font-size: 16px; font-weight: bold;")
        stock_layout.addWidget(current_stock)
        
        # Calculate stock value
        purchase_price = float(self.product.get('purchase_price', 0))
        stock_value = purchase_price * float(self.product['stock'])
        value_label = QLabel(f"Valeur: {stock_value:.2f} MAD")
        value_label.setStyleSheet("color: #28a745;")
        stock_layout.addWidget(value_label)
        
        header_layout.addLayout(stock_layout)
        
        layout.addWidget(header_frame)

    def load_stock_movements(self):
        """Load stock movement history for the product"""
        movements = Product.get_stock_movements(self.product['id'])
        
        self.movements_table.setRowCount(len(movements))
        
        for row, movement in enumerate(movements):
            # Date column
            date_item = QTableWidgetItem(movement['created_at'])
            self.movements_table.setItem(row, 0, date_item)
            
            # Movement type
            type_text = {
                'in': "Entrée ↑",
                'out': "Sortie ↓",
                'adjustment': "Ajustement ↔"
            }.get(movement['movement_type'], movement['movement_type'])
            
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(Qt.green if movement['movement_type'] == 'in' else 
                                   Qt.red if movement['movement_type'] == 'out' else
                                   Qt.blue)
            self.movements_table.setItem(row, 1, type_item)
            
            # Quantity
            quantity = movement['quantity']
            prefix = "+" if movement['movement_type'] == 'in' else "-" if movement['movement_type'] == 'out' else "±"
            quantity_item = QTableWidgetItem(f"{prefix}{abs(quantity)}")
            self.movements_table.setItem(row, 2, quantity_item)
            
            # Unit price
            unit_price = movement.get('unit_price', 0) or 0
            price_item = QTableWidgetItem(f"{unit_price:.2f} MAD")
            self.movements_table.setItem(row, 3, price_item)
            
            # Total value
            total = quantity * unit_price
            total_item = QTableWidgetItem(f"{total:.2f} MAD")
            self.movements_table.setItem(row, 4, total_item)
            
            # Reference
            ref_item = QTableWidgetItem(movement.get('reference', ''))
            self.movements_table.setItem(row, 5, ref_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, m=movement: self.delete_movement(m))
            
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.movements_table.setCellWidget(row, 6, actions_widget)

    def apply_stock_adjustment(self):
        """Apply a stock adjustment"""
        try:
            # Get movement details
            movement_index = self.movement_type.currentIndex()
            movement_types = ['in', 'out', 'adjustment']
            movement_type = movement_types[movement_index]
            
            quantity = self.quantity_spin.value()
            if movement_type == 'out':
                # Make quantity negative for outgoing
                quantity = -quantity
            
            # Check if there's enough stock for outgoing movement
            if movement_type == 'out' and abs(quantity) > self.product['stock']:
                QMessageBox.warning(
                    self,
                    "Stock insuffisant",
                    f"Le stock actuel ({self.product['stock']}) est insuffisant pour cette opération."
                )
                return
            
            unit_price = self.price_spin.value()
            reference = self.reference_edit.text()
            notes = self.notes_edit.toPlainText()
            
            # Add the stock movement
            result = Product.add_stock_movement(
                self.product['id'],
                None,  # variant_id
                movement_type,
                quantity,
                unit_price,
                reference,
                notes,
                1  # user_id - should be the current user
            )
            
            if result:
                # Update the product stock cache
                new_stock = int(self.product['stock']) + quantity
                Product.update_product(self.product['id'], stock=new_stock)
                
                # Update local product data
                self.product['stock'] = new_stock
                
                # Refresh UI
                self.create_product_header(QVBoxLayout())  # Create a dummy layout to update header
                self.load_stock_movements()
                
                # Clear inputs
                self.reference_edit.clear()
                self.notes_edit.clear()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    "L'ajustement de stock a été effectué avec succès."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Une erreur est survenue lors de l'ajustement de stock."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur critique",
                f"Une erreur inattendue est survenue: {str(e)}"
            )

    def delete_movement(self, movement):
        """Delete a stock movement and revert its effects"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Etes-vous sûr de vouloir supprimer ce mouvement de stock? Cette action annulera également les changements de stock associés.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete the movement and revert stock changes
            if Product.delete_stock_movement(movement['id']):
                # Update product stock by reverting the movement
                quantity = movement['quantity']
                # Reverse the quantity - add what was removed, remove what was added
                new_stock = int(self.product['stock']) - quantity
                
                # Update product stock
                Product.update_product(self.product['id'], stock=new_stock)
                
                # Update local product data
                self.product['stock'] = new_stock
                
                # Refresh UI
                self.create_product_header(QVBoxLayout())  # Create a dummy layout to update header
                self.load_stock_movements()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    "Le mouvement de stock a été supprimé et les changements annulés."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Une erreur est survenue lors de la suppression du mouvement."
                )
