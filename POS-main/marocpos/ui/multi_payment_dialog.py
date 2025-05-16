from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QSpinBox, QDoubleSpinBox, QComboBox, QFrame,
    QGridLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from models.payment import Payment
from database import get_connection
import json
import os

class MultiPaymentDialog(QDialog):
    def __init__(self, total_amount, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.paid_amount = 0.0
        self.payments = []  # List to store payment entries
        self.init_ui()
        self.load_payment_methods()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Paiement multi-méthodes")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Amount section
        amount_frame = QFrame()
        amount_frame.setFrameShape(QFrame.StyledPanel)
        amount_frame.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 5px;")
        amount_layout = QGridLayout(amount_frame)
        
        # Total amount
        total_label = QLabel("Total à payer:")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.total_amount_label = QLabel(f"{self.total_amount:.2f} MAD")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #28a745;")
        amount_layout.addWidget(total_label, 0, 0)
        amount_layout.addWidget(self.total_amount_label, 0, 1)
        
        # Paid amount
        paid_label = QLabel("Montant payé:")
        paid_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.paid_amount_label = QLabel("0.00 MAD")
        self.paid_amount_label.setStyleSheet("font-size: 16px; color: #007bff;")
        amount_layout.addWidget(paid_label, 1, 0)
        amount_layout.addWidget(self.paid_amount_label, 1, 1)
        
        # Remaining amount
        remaining_label = QLabel("Reste à payer:")
        remaining_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.remaining_amount_label = QLabel(f"{self.total_amount:.2f} MAD")
        self.remaining_amount_label.setStyleSheet("font-size: 16px; color: #dc3545;")
        amount_layout.addWidget(remaining_label, 2, 0)
        amount_layout.addWidget(self.remaining_amount_label, 2, 1)
        
        # Change amount (only shown when overpaid)
        change_label = QLabel("Monnaie à rendre:")
        change_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.change_amount_label = QLabel("0.00 MAD")
        self.change_amount_label.setStyleSheet("font-size: 16px; color: #fd7e14;")
        amount_layout.addWidget(change_label, 3, 0)
        amount_layout.addWidget(self.change_amount_label, 3, 1)
        
        main_layout.addWidget(amount_frame)
        
        # Add payment section
        payment_frame = QFrame()
        payment_frame.setFrameShape(QFrame.StyledPanel)
        payment_frame.setStyleSheet("background-color: white; padding: 15px; border-radius: 5px;")
        payment_layout = QVBoxLayout(payment_frame)
        
        payment_title = QLabel("Ajouter un paiement")
        payment_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        payment_layout.addWidget(payment_title)
        
        # Payment form
        form_layout = QGridLayout()
        
        # Payment method
        method_label = QLabel("Méthode de paiement:")
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.currentIndexChanged.connect(self.on_payment_method_changed)
        form_layout.addWidget(method_label, 0, 0)
        form_layout.addWidget(self.payment_method_combo, 0, 1)
        
        # Amount
        amount_label = QLabel("Montant:")
        self.payment_amount_spin = QDoubleSpinBox()
        self.payment_amount_spin.setRange(0.01, 999999.99)
        self.payment_amount_spin.setDecimals(2)
        self.payment_amount_spin.setValue(self.total_amount)
        self.payment_amount_spin.setSuffix(" MAD")
        form_layout.addWidget(amount_label, 1, 0)
        form_layout.addWidget(self.payment_amount_spin, 1, 1)
        
        # Reference (visible only for certain payment methods)
        reference_label = QLabel("Référence:")
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Numéro de carte, chèque, etc.")
        self.reference_input.setVisible(False)
        reference_label.setVisible(False)
        self.reference_label = reference_label  # Store for later visibility control
        form_layout.addWidget(reference_label, 2, 0)
        form_layout.addWidget(self.reference_input, 2, 1)
        
        # Notes
        notes_label = QLabel("Notes:")
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes sur ce paiement...")
        form_layout.addWidget(notes_label, 3, 0)
        form_layout.addWidget(self.notes_input, 3, 1)
        
        payment_layout.addLayout(form_layout)
        
        # Add payment button
        add_payment_btn = QPushButton("Ajouter le paiement")
        add_payment_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        add_payment_btn.clicked.connect(self.add_payment)
        payment_layout.addWidget(add_payment_btn)
        
        main_layout.addWidget(payment_frame)
        
        # Payments table
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels(["Méthode", "Montant", "Référence", "Notes", "Actions"])
        
        self.payments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.payments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.payments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.payments_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.payments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.payments_table.setColumnWidth(1, 100)
        self.payments_table.setColumnWidth(4, 80)
        
        main_layout.addWidget(self.payments_table)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Customize the OK button
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Finaliser la vente")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        # Customize the Cancel button
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Annuler")
        
        main_layout.addWidget(button_box)

    def load_payment_methods(self):
        """Load payment methods from database"""
        payment_methods = Payment.get_all_payment_methods()
        
        self.payment_method_combo.clear()
        self.payment_methods = payment_methods
        
        for method in payment_methods:
            self.payment_method_combo.addItem(method['name'], method['id'])
        
        # Trigger method change to update UI
        if payment_methods:
            self.on_payment_method_changed(0)

    def on_payment_method_changed(self, index):
        """Handle payment method change"""
        if index < 0 or index >= len(self.payment_methods):
            return
            
        method = self.payment_methods[index]
        
        # Show/hide reference field based on method requirements
        requires_reference = bool(method['requires_reference'])
        self.reference_input.setVisible(requires_reference)
        self.reference_label.setVisible(requires_reference)
        
        # Clear reference if not required
        if not requires_reference:
            self.reference_input.clear()

    def add_payment(self):
        """Add a payment to the list"""
        # Get selected method
        method_index = self.payment_method_combo.currentIndex()
        if method_index < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une méthode de paiement.")
            return
            
        method = self.payment_methods[method_index]
        
        # Get amount
        amount = self.payment_amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à zéro.")
            return
            
        # Check reference if required
        if method['requires_reference'] and not self.reference_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Référence requise pour cette méthode de paiement.")
            return
            
        # Create payment entry
        payment = {
            'method_id': method['id'],
            'method_name': method['name'],
            'amount': amount,
            'reference': self.reference_input.text().strip(),
            'notes': self.notes_input.text().strip()
        }
        
        # Add to payments list
        self.payments.append(payment)
        
        # Update UI
        self.update_payment_table()
        self.update_amounts()
        
        # Reset form for next payment
        if len(self.payments) > 0 and self.get_remaining_amount() > 0:
            self.payment_amount_spin.setValue(self.get_remaining_amount())
        else:
            self.payment_amount_spin.setValue(0)
        self.reference_input.clear()
        self.notes_input.clear()
        
    def remove_payment(self, row):
        """Remove a payment from the list"""
        if 0 <= row < len(self.payments):
            del self.payments[row]
            self.update_payment_table()
            self.update_amounts()
            
            # Update amount for next payment
            if self.get_remaining_amount() > 0:
                self.payment_amount_spin.setValue(self.get_remaining_amount())

    def update_payment_table(self):
        """Update the payments table"""
        self.payments_table.setRowCount(len(self.payments))
        
        for row, payment in enumerate(self.payments):
            # Method name
            method_item = QTableWidgetItem(payment['method_name'])
            method_item.setFlags(method_item.flags() & ~Qt.ItemIsEditable)
            self.payments_table.setItem(row, 0, method_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{payment['amount']:.2f} MAD")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_item.setFlags(amount_item.flags() & ~Qt.ItemIsEditable)
            self.payments_table.setItem(row, 1, amount_item)
            
            # Reference
            reference_item = QTableWidgetItem(payment['reference'])
            reference_item.setFlags(reference_item.flags() & ~Qt.ItemIsEditable)
            self.payments_table.setItem(row, 2, reference_item)
            
            # Notes
            notes_item = QTableWidgetItem(payment['notes'])
            notes_item.setFlags(notes_item.flags() & ~Qt.ItemIsEditable)
            self.payments_table.setItem(row, 3, notes_item)
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #6c757d;
                    border: none;
                }
                QPushButton:hover {
                    color: #dc3545;
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_payment(r))
            
            self.payments_table.setCellWidget(row, 4, delete_btn)

    def update_amounts(self):
        """Update the amount labels"""
        self.paid_amount = sum(payment['amount'] for payment in self.payments)
        remaining = self.get_remaining_amount()
        
        self.paid_amount_label.setText(f"{self.paid_amount:.2f} MAD")
        
        if remaining > 0:
            # Still needs to pay more
            self.remaining_amount_label.setText(f"{remaining:.2f} MAD")
            self.remaining_amount_label.setStyleSheet("font-size: 16px; color: #dc3545;")
            self.change_amount_label.setText("0.00 MAD")
        else:
            # Paid enough
            self.remaining_amount_label.setText("0.00 MAD")
            self.remaining_amount_label.setStyleSheet("font-size: 16px; color: #28a745;")
            
            # Calculate change if overpaid
            if remaining < 0:
                self.change_amount_label.setText(f"{abs(remaining):.2f} MAD")
            else:
                self.change_amount_label.setText("0.00 MAD")

    def get_remaining_amount(self):
        """Calculate the remaining amount to pay"""
        return self.total_amount - self.paid_amount

    def accept(self):
        """Validate and accept the dialog"""
        if not self.payments:
            QMessageBox.warning(
                self, "Aucun paiement", 
                "Veuillez ajouter au moins un paiement avant de finaliser la vente."
            )
            return
            
        remaining = self.get_remaining_amount()
        if remaining > 0.01:  # Allow for small rounding errors
            QMessageBox.warning(
                self, "Paiement incomplet", 
                f"Le montant payé est insuffisant. Il reste {remaining:.2f} MAD à payer."
            )
            return
            
        # All is good, proceed
        super().accept()
        
    def get_payments_data(self):
        """Get the payments data for processing"""
        return self.payments
