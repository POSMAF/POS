from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QGroupBox, QDialogButtonBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from database import get_connection
import os
import shutil

class ReceiptSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = {}
        self.logo_path = None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Paramètres du reçu de vente")
        self.setMinimumSize(700, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Store information group
        store_group = QGroupBox("Informations du magasin")
        store_layout = QFormLayout()
        
        # Store name
        self.store_name = QLineEdit()
        store_layout.addRow("Nom du magasin:", self.store_name)
        
        # Store address
        self.store_address = QTextEdit()
        self.store_address.setMaximumHeight(60)
        store_layout.addRow("Adresse:", self.store_address)
        
        # Store contact
        self.store_phone = QLineEdit()
        store_layout.addRow("Téléphone:", self.store_phone)
        
        self.store_email = QLineEdit()
        store_layout.addRow("Email:", self.store_email)
        
        # Store logo
        logo_layout = QHBoxLayout()
        self.logo_btn = QPushButton("Choisir un logo")
        self.logo_btn.clicked.connect(self.select_logo)
        self.logo_preview = QLabel("Aucun logo")
        self.logo_preview.setMinimumSize(100, 100)
        self.logo_preview.setStyleSheet("border: 1px solid #ddd; background-color: #f8f9fa;")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        
        logo_layout.addWidget(self.logo_btn)
        logo_layout.addWidget(self.logo_preview)
        
        store_layout.addRow("Logo:", logo_layout)
        
        store_group.setLayout(store_layout)
        main_layout.addWidget(store_group)
        
        # Receipt format group
        format_group = QGroupBox("Format du reçu")
        format_layout = QFormLayout()
        
        # Receipt printer type
        self.printer_type = QComboBox()
        self.printer_type.addItems(["Format thermique (58mm)", "Format thermique (80mm)", "Format A4", "PDF seulement"])
        format_layout.addRow("Type d'impression:", self.printer_type)
        
        # Currency
        self.currency = QLineEdit()
        format_layout.addRow("Devise:", self.currency)
        
        # Receipt footer message
        self.footer_message = QTextEdit()
        self.footer_message.setMaximumHeight(60)
        format_layout.addRow("Message de pied de page:", self.footer_message)
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # Receipt preview
        preview_group = QGroupBox("Aperçu du reçu")
        preview_layout = QVBoxLayout()
        
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        preview_frame_layout = QVBoxLayout(self.preview_frame)
        
        # Header
        self.preview_header = QLabel("Nom du magasin")
        self.preview_header.setAlignment(Qt.AlignCenter)
        self.preview_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        preview_frame_layout.addWidget(self.preview_header)
        
        # Address
        self.preview_address = QLabel("Adresse du magasin")
        self.preview_address.setAlignment(Qt.AlignCenter)
        preview_frame_layout.addWidget(self.preview_address)
        
        # Contact
        self.preview_contact = QLabel("Téléphone | Email")
        self.preview_contact.setAlignment(Qt.AlignCenter)
        preview_frame_layout.addWidget(self.preview_contact)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        preview_frame_layout.addWidget(separator)
        
        # Sample content
        preview_frame_layout.addWidget(QLabel("Date: 2023-05-14 12:30:45"))
        preview_frame_layout.addWidget(QLabel("Reçu #: 12345"))
        preview_frame_layout.addWidget(QLabel("Caissier: Admin"))
        
        preview_frame_layout.addWidget(QLabel("--------------------------------"))
        preview_frame_layout.addWidget(QLabel("Produit 1 x 100.00"))
        preview_frame_layout.addWidget(QLabel("Produit 2 x 50.00"))
        preview_frame_layout.addWidget(QLabel("--------------------------------"))
        
        # Totals
        totals_layout = QFormLayout()
        totals_layout.addRow("Sous-total:", QLabel("150.00 MAD"))
        totals_layout.addRow("TVA (20%):", QLabel("30.00 MAD"))
        totals_layout.addRow("Total:", QLabel("180.00 MAD"))
        preview_frame_layout.addLayout(totals_layout)
        
        # Footer
        self.preview_footer = QLabel("Merci pour votre achat!")
        self.preview_footer.setAlignment(Qt.AlignCenter)
        preview_frame_layout.addWidget(self.preview_footer)
        
        preview_layout.addWidget(self.preview_frame)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        # Connect signals for live preview update
        self.store_name.textChanged.connect(self.update_preview)
        self.store_address.textChanged.connect(self.update_preview)
        self.store_phone.textChanged.connect(self.update_preview)
        self.store_email.textChanged.connect(self.update_preview)
        self.footer_message.textChanged.connect(self.update_preview)

    def load_settings(self):
        """Load settings from database"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM Settings")
                self.settings = dict(cursor.fetchall())
                
                # Fill form with settings
                self.store_name.setText(self.settings.get('store_name', ''))
                self.store_address.setText(self.settings.get('store_address', ''))
                self.store_phone.setText(self.settings.get('store_phone', ''))
                self.store_email.setText(self.settings.get('store_email', ''))
                self.currency.setText(self.settings.get('currency', 'MAD'))
                self.footer_message.setText(self.settings.get('receipt_footer', 'Merci pour votre achat!'))
                
                # Set printer type
                printer_type = self.settings.get('receipt_printer_type', 'thermal_80')
                index_map = {
                    'thermal_58': 0,
                    'thermal_80': 1,
                    'a4': 2,
                    'pdf': 3
                }
                self.printer_type.setCurrentIndex(index_map.get(printer_type, 1))
                
                # Load logo
                logo_path = self.settings.get('receipt_logo_path', '')
                if logo_path and os.path.exists(logo_path):
                    self.logo_path = logo_path
                    self.update_logo_preview()
                
                # Update preview
                self.update_preview()
            except Exception as e:
                print(f"Error loading receipt settings: {e}")
            finally:
                conn.close()

    def select_logo(self):
        """Open file dialog to select a logo"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Sélectionner un logo", "", 
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            # Create receipt_logos directory if it doesn't exist
            logos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'receipt_logos')
            os.makedirs(logos_dir, exist_ok=True)
            
            # Copy file to logos directory
            file_name = os.path.basename(file_path)
            new_path = os.path.join(logos_dir, file_name)
            
            try:
                shutil.copy2(file_path, new_path)
                self.logo_path = new_path
                self.update_logo_preview()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible de copier le logo: {str(e)}")

    def update_logo_preview(self):
        """Update logo preview"""
        if self.logo_path and os.path.exists(self.logo_path):
            pixmap = QPixmap(self.logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    100, 100,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.logo_preview.setPixmap(pixmap)
            else:
                self.logo_preview.setText("Image invalide")
        else:
            self.logo_preview.setText("Aucun logo")

    def update_preview(self):
        """Update receipt preview"""
        # Update header
        self.preview_header.setText(self.store_name.text() or "Nom du magasin")
        
        # Update address
        self.preview_address.setText(self.store_address.toPlainText() or "Adresse du magasin")
        
        # Update contact
        contact_parts = []
        if self.store_phone.text():
            contact_parts.append(self.store_phone.text())
        if self.store_email.text():
            contact_parts.append(self.store_email.text())
        
        contact_text = " | ".join(contact_parts) if contact_parts else "Téléphone | Email"
        self.preview_contact.setText(contact_text)
        
        # Update footer
        self.preview_footer.setText(self.footer_message.toPlainText() or "Merci pour votre achat!")

    def save_settings(self):
        """Save settings to database"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Map printer type selection to value
                printer_types = ['thermal_58', 'thermal_80', 'a4', 'pdf']
                printer_type = printer_types[self.printer_type.currentIndex()]
                
                # Settings to save
                settings_to_save = {
                    'store_name': self.store_name.text(),
                    'store_address': self.store_address.toPlainText(),
                    'store_phone': self.store_phone.text(),
                    'store_email': self.store_email.text(),
                    'currency': self.currency.text(),
                    'receipt_printer_type': printer_type,
                    'receipt_footer': self.footer_message.toPlainText(),
                    'receipt_logo_path': self.logo_path or ''
                }
                
                # Update each setting
                for key, value in settings_to_save.items():
                    cursor.execute("""
                        UPDATE Settings 
                        SET value = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE key = ?
                    """, (value, key))
                
                conn.commit()
                QMessageBox.information(self, "Succès", "Paramètres enregistrés avec succès!")
                self.accept()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder les paramètres: {str(e)}")
            finally:
                conn.close()
