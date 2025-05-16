from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QFileDialog, QLabel, QMessageBox
)
from database import get_connection

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("Store Settings")
        layout = QFormLayout()

        # Store information
        self.store_name = QLineEdit()
        self.store_address = QLineEdit()
        self.store_phone = QLineEdit()
        self.store_email = QLineEdit()
        self.tax_rate = QLineEdit()
        self.currency = QLineEdit()
        self.receipt_footer = QLineEdit()

        layout.addRow("Store Name:", self.store_name)
        layout.addRow("Address:", self.store_address)
        layout.addRow("Phone:", self.store_phone)
        layout.addRow("Email:", self.store_email)
        layout.addRow("Tax Rate (%):", self.tax_rate)
        layout.addRow("Currency:", self.currency)
        layout.addRow("Receipt Footer:", self.receipt_footer)

        # Logo selection
        logo_layout = QVBoxLayout()
        self.logo_path = QLineEdit()
        self.logo_path.setReadOnly(True)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_logo)
        logo_layout.addWidget(self.logo_path)
        logo_layout.addWidget(browse_button)
        layout.addRow("Receipt Logo:", logo_layout)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addRow(save_button)

        self.setLayout(layout)

    def load_settings(self):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM Settings")
                settings = dict(cursor.fetchall())
                
                self.store_name.setText(settings.get('store_name', ''))
                self.store_address.setText(settings.get('store_address', ''))
                self.store_phone.setText(settings.get('store_phone', ''))
                self.store_email.setText(settings.get('store_email', ''))
                self.tax_rate.setText(settings.get('tax_rate', '0'))
                self.currency.setText(settings.get('currency', 'MAD'))
                self.receipt_footer.setText(settings.get('receipt_footer', ''))
                self.logo_path.setText(settings.get('receipt_logo', ''))
            finally:
                conn.close()

    def browse_logo(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.logo_path.setText(file_name)

    def save_settings(self):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                settings = {
                    'store_name': self.store_name.text(),
                    'store_address': self.store_address.text(),
                    'store_phone': self.store_phone.text(),
                    'store_email': self.store_email.text(),
                    'tax_rate': self.tax_rate.text(),
                    'currency': self.currency.text(),
                    'receipt_footer': self.receipt_footer.text(),
                    'receipt_logo': self.logo_path.text()
                }

                for key, value in settings.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO Settings (key, value)
                        VALUES (?, ?)
                    """, (key, value))

                conn.commit()
                QMessageBox.information(self, "Success", "Settings saved successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error saving settings: {str(e)}")
            finally:
                conn.close()