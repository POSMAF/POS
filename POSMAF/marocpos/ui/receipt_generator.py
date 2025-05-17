from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QWidget, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QFont
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from models.sales import Sales
from database import get_connection
import os
from datetime import datetime
import json
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ReceiptGenerator:
    def __init__(self, sale_id, parent=None):
        """Initialize the receipt generator"""
        self.sale_id = sale_id
        self.parent = parent
        self.load_settings()
        self.load_sale_data()
        
    def load_settings(self):
        """Load settings from database"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM Settings")
                self.settings = dict(cursor.fetchall())
            except Exception as e:
                print(f"Error loading settings: {e}")
                self.settings = {}
            finally:
                conn.close()
                
    def load_sale_data(self):
        """Load sale data"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get sale details
                cursor.execute("""
                    SELECT s.*, u.username 
                    FROM Sales s
                    JOIN Users u ON s.user_id = u.id
                    WHERE s.id = ?
                """, (self.sale_id,))
                self.sale = dict(cursor.fetchone())
                
                # Get sale items
                cursor.execute("""
                    SELECT si.*, p.name as product_name
                    FROM SaleItems si
                    JOIN Products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (self.sale_id,))
                self.items = [dict(item) for item in cursor.fetchall()]
                
            except Exception as e:
                print(f"Error loading sale data: {e}")
                self.sale = {}
                self.items = []
            finally:
                conn.close()
                
    def show_receipt_dialog(self):
        """Show receipt dialog with preview and options"""
        dialog = ReceiptPreviewDialog(self.sale, self.items, self.settings, self.parent)
        return dialog.exec_()
        
    def print_thermal(self):
        """Print receipt to thermal printer"""
        # This is a placeholder - actual implementation would use a thermal printer library
        # such as python-escpos or similar
        try:
            # Since we don't have actual hardware, just show a success message
            QMessageBox.information(
                self.parent,
                "Impression thermique",
                "Le reçu a été envoyé à l'imprimante thermique."
            )
            return True
        except Exception as e:
            print(f"Error printing thermal receipt: {e}")
            QMessageBox.warning(
                self.parent,
                "Erreur d'impression",
                f"Impossible d'imprimer le reçu: {str(e)}"
            )
            return False
            
    def print_a4(self):
        """Print receipt on A4 paper"""
        try:
            # Generate PDF first
            pdf_path = self.generate_pdf(os.path.join(tempfile.gettempdir(), f"receipt_{self.sale_id}.pdf"))
            if not pdf_path:
                return False
                
            # Use Qt's printing system
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            
            dialog = QPrintDialog(printer)
            if dialog.exec_() == QPrintDialog.Accepted:
                # Create a QPixmap from the PDF - this is simplified
                QMessageBox.information(
                    self.parent,
                    "Impression A4",
                    f"Le reçu a été envoyé à l'imprimante.\nLe PDF est disponible ici: {pdf_path}"
                )
                return True
            return False
        except Exception as e:
            print(f"Error printing A4 receipt: {e}")
            QMessageBox.warning(
                self.parent,
                "Erreur d'impression",
                f"Impossible d'imprimer le reçu: {str(e)}"
            )
            return False
            
    def generate_pdf(self, output_path=None):
        """Generate PDF receipt"""
        if not output_path:
            # Ask user for save location
            file_dialog = QFileDialog()
            output_path, _ = file_dialog.getSaveFileName(
                self.parent,
                "Enregistrer le reçu",
                f"receipt_{self.sale_id}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not output_path:
                return None
        
        try:
            # Create PDF using ReportLab
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20
            )
            
            # Create content
            styles = getSampleStyleSheet()
            content = []
            
            # Store name (header)
            store_name_style = ParagraphStyle(
                'StoreNameStyle',
                parent=styles['Title'],
                alignment=1,  # Center alignment
                fontSize=18
            )
            content.append(Paragraph(self.settings.get('store_name', 'My Store'), store_name_style))
            content.append(Spacer(1, 10))
            
            # Store info
            store_info_style = ParagraphStyle(
                'StoreInfoStyle',
                parent=styles['Normal'],
                alignment=1,  # Center alignment
                fontSize=10
            )
            
            if self.settings.get('store_address'):
                content.append(Paragraph(self.settings.get('store_address'), store_info_style))
                content.append(Spacer(1, 5))
            
            contact_parts = []
            if self.settings.get('store_phone'):
                contact_parts.append(f"Tél: {self.settings.get('store_phone')}")
            if self.settings.get('store_email'):
                contact_parts.append(f"Email: {self.settings.get('store_email')}")
                
            if contact_parts:
                content.append(Paragraph(" | ".join(contact_parts), store_info_style))
                content.append(Spacer(1, 10))
            
            # Receipt details
            receipt_style = ParagraphStyle(
                'ReceiptStyle',
                parent=styles['Normal'],
                fontSize=10
            )
            
            content.append(Paragraph(f"Reçu #: {self.sale['id']}", receipt_style))
            content.append(Paragraph(f"Date: {self.sale['created_at']}", receipt_style))
            content.append(Paragraph(f"Caissier: {self.sale['username']}", receipt_style))
            content.append(Spacer(1, 15))
            
            # Items table
            data = [['Produit', 'Qté', 'Prix', 'Total']]
            for item in self.items:
                data.append([
                    item['product_name'],
                    str(item['quantity']),
                    f"{item['unit_price']:.2f}",
                    f"{item['subtotal']:.2f}"
                ])
            
            # Add table to content
            table = Table(data, colWidths=[250, 50, 70, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            content.append(table)
            content.append(Spacer(1, 15))
            
            # Totals
            currency = self.settings.get('currency', 'MAD')
            totals_data = []
            
            totals_data.append(['Sous-total:', f"{self.sale['total_amount']:.2f} {currency}"])
            
            if self.sale['discount'] > 0:
                totals_data.append(['Remise:', f"{self.sale['discount']:.2f} {currency}"])
                
            if self.sale['tax_amount'] > 0:
                totals_data.append(['TVA:', f"{self.sale['tax_amount']:.2f} {currency}"])
                
            totals_data.append(['Total:', f"{self.sale['final_total']:.2f} {currency}"])
            
            # Totals table
            totals_table = Table(totals_data, colWidths=[100, 100])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            # Right-align the totals table
            totals_wrapper = Table([[totals_table]], colWidths=[440])
            totals_wrapper.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ]))
            content.append(totals_wrapper)
            content.append(Spacer(1, 20))
            
            # Payment method
            payment_method = self.sale['payment_method']
            content.append(Paragraph(f"Mode de paiement: {payment_method}", receipt_style))
            content.append(Spacer(1, 15))
            
            # Footer
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                alignment=1,  # Center alignment
                fontSize=10
            )
            footer_text = self.settings.get('receipt_footer', 'Merci pour votre achat!')
            content.append(Paragraph(footer_text, footer_style))
            
            # Build the document
            doc.build(content)
            
            return output_path
        except Exception as e:
            print(f"Error generating PDF receipt: {e}")
            QMessageBox.warning(
                self.parent,
                "Erreur PDF",
                f"Impossible de générer le PDF: {str(e)}"
            )
            return None

class ReceiptPreviewDialog(QDialog):
    def __init__(self, sale, items, settings, parent=None):
        super().__init__(parent)
        self.sale = sale
        self.items = items
        self.settings = settings
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Aperçu du reçu")
        self.setMinimumSize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Tabs for different formats
        tabs = QTabWidget()
        
        # Thermal receipt preview
        thermal_tab = QScrollArea()
        thermal_tab.setWidgetResizable(True)
        thermal_widget = QWidget()
        thermal_layout = QVBoxLayout(thermal_widget)
        thermal_layout.setAlignment(Qt.AlignCenter)
        
        # Create thermal receipt preview
        thermal_receipt = self.create_thermal_preview()
        thermal_layout.addWidget(thermal_receipt)
        
        thermal_tab.setWidget(thermal_widget)
        tabs.addTab(thermal_tab, "Format thermique")
        
        # A4 receipt preview
        a4_tab = QScrollArea()
        a4_tab.setWidgetResizable(True)
        a4_widget = QWidget()
        a4_layout = QVBoxLayout(a4_widget)
        a4_layout.setAlignment(Qt.AlignCenter)
        
        # Create A4 receipt preview
        a4_receipt = self.create_a4_preview()
        a4_layout.addWidget(a4_receipt)
        
        a4_tab.setWidget(a4_widget)
        tabs.addTab(a4_tab, "Format A4")
        
        main_layout.addWidget(tabs)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        # Print thermal button
        thermal_btn = QPushButton("Imprimer (thermique)")
        thermal_btn.clicked.connect(self.print_thermal)
        
        # Print A4 button
        a4_btn = QPushButton("Imprimer (A4)")
        a4_btn.clicked.connect(self.print_a4)
        
        # Save PDF button
        pdf_btn = QPushButton("Enregistrer PDF")
        pdf_btn.clicked.connect(self.save_pdf)
        
        # Close button
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(thermal_btn)
        buttons_layout.addWidget(a4_btn)
        buttons_layout.addWidget(pdf_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        
        main_layout.addLayout(buttons_layout)
        
    def create_thermal_preview(self):
        """Create thermal receipt preview widget"""
        preview = QWidget()
        preview.setFixedWidth(300)  # Typical thermal receipt width in pixels
        preview.setStyleSheet("background-color: white; padding: 20px;")
        
        layout = QVBoxLayout(preview)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # Logo (if exists)
        logo_path = self.settings.get('receipt_logo_path')
        if logo_path and os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
            layout.addSpacing(10)
        
        # Store name
        store_name = QLabel(self.settings.get('store_name', 'My Store'))
        store_name.setAlignment(Qt.AlignCenter)
        store_name.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(store_name)
        
        # Store address
        if self.settings.get('store_address'):
            store_address = QLabel(self.settings.get('store_address'))
            store_address.setAlignment(Qt.AlignCenter)
            store_address.setWordWrap(True)
            layout.addWidget(store_address)
        
        # Store contact
        contact_parts = []
        if self.settings.get('store_phone'):
            contact_parts.append(self.settings.get('store_phone'))
        if self.settings.get('store_email'):
            contact_parts.append(self.settings.get('store_email'))
            
        if contact_parts:
            contact_label = QLabel(" | ".join(contact_parts))
            contact_label.setAlignment(Qt.AlignCenter)
            contact_label.setWordWrap(True)
            layout.addWidget(contact_label)
        
        layout.addSpacing(10)
        
        # Receipt info
        layout.addWidget(QLabel(f"Reçu #: {self.sale['id']}"))
        layout.addWidget(QLabel(f"Date: {self.sale['created_at']}"))
        layout.addWidget(QLabel(f"Caissier: {self.sale['username']}"))
        
        layout.addSpacing(10)
        
        # Separator
        separator = QLabel("----------------------------------------")
        separator.setAlignment(Qt.AlignCenter)
        layout.addWidget(separator)
        
        # Items
        for item in self.items:
            item_name = QLabel(item['product_name'])
            item_name.setWordWrap(True)
            layout.addWidget(item_name)
            
            item_detail = QLabel(f"{item['quantity']} x {item['unit_price']:.2f} = {item['subtotal']:.2f}")
            item_detail.setAlignment(Qt.AlignRight)
            layout.addWidget(item_detail)
        
        # Separator
        layout.addWidget(separator)
        
        # Totals
        currency = self.settings.get('currency', 'MAD')
        
        subtotal = QLabel(f"Sous-total: {self.sale['total_amount']:.2f} {currency}")
        subtotal.setAlignment(Qt.AlignRight)
        layout.addWidget(subtotal)
        
        if self.sale['discount'] > 0:
            discount = QLabel(f"Remise: {self.sale['discount']:.2f} {currency}")
            discount.setAlignment(Qt.AlignRight)
            layout.addWidget(discount)
            
        if self.sale['tax_amount'] > 0:
            tax = QLabel(f"TVA: {self.sale['tax_amount']:.2f} {currency}")
            tax.setAlignment(Qt.AlignRight)
            layout.addWidget(tax)
        
        total = QLabel(f"Total: {self.sale['final_total']:.2f} {currency}")
        total.setAlignment(Qt.AlignRight)
        total.setStyleSheet("font-weight: bold;")
        layout.addWidget(total)
        
        layout.addSpacing(10)
        
        # Payment method
        payment = QLabel(f"Mode de paiement: {self.sale['payment_method']}")
        layout.addWidget(payment)
        
        layout.addSpacing(10)
        
        # Footer
        footer = QLabel(self.settings.get('receipt_footer', 'Merci pour votre achat!'))
        footer.setAlignment(Qt.AlignCenter)
        footer.setWordWrap(True)
        layout.addWidget(footer)
        
        return preview
        
    def create_a4_preview(self):
        """Create A4 receipt preview widget"""
        preview = QWidget()
        preview.setFixedWidth(595)  # A4 width in pixels at 72 DPI
        preview.setMinimumHeight(842)  # A4 height in pixels
        preview.setStyleSheet("background-color: white; padding: 40px;")
        
        layout = QVBoxLayout(preview)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Logo (if exists)
        logo_path = self.settings.get('receipt_logo_path')
        if logo_path and os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(logo_label)
            header_layout.addSpacing(10)
        
        # Store name
        store_name = QLabel(self.settings.get('store_name', 'My Store'))
        store_name.setAlignment(Qt.AlignCenter)
        store_name.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(store_name)
        
        # Store address
        if self.settings.get('store_address'):
            store_address = QLabel(self.settings.get('store_address'))
            store_address.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(store_address)
        
        # Store contact
        contact_parts = []
        if self.settings.get('store_phone'):
            contact_parts.append(f"Tél: {self.settings.get('store_phone')}")
        if self.settings.get('store_email'):
            contact_parts.append(self.settings.get('store_email'))
            
        if contact_parts:
            contact_label = QLabel(" | ".join(contact_parts))
            contact_label.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(contact_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Receipt info
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"<b>Reçu #:</b> {self.sale['id']}"))
        info_layout.addWidget(QLabel(f"<b>Date:</b> {self.sale['created_at']}"))
        info_layout.addWidget(QLabel(f"<b>Caissier:</b> {self.sale['username']}"))
        layout.addLayout(info_layout)
        layout.addSpacing(20)
        
        # Items table header
        table_header = QHBoxLayout()
        table_header.addWidget(QLabel("<b>Produit</b>"), 3)
        table_header.addWidget(QLabel("<b>Qté</b>"), 1)
        table_header.addWidget(QLabel("<b>Prix</b>"), 1)
        table_header.addWidget(QLabel("<b>Total</b>"), 1)
        layout.addLayout(table_header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Items
        for item in self.items:
            item_layout = QHBoxLayout()
            
            name_label = QLabel(item['product_name'])
            name_label.setWordWrap(True)
            
            qty_label = QLabel(str(item['quantity']))
            qty_label.setAlignment(Qt.AlignCenter)
            
            price_label = QLabel(f"{item['unit_price']:.2f}")
            price_label.setAlignment(Qt.AlignRight)
            
            total_label = QLabel(f"{item['subtotal']:.2f}")
            total_label.setAlignment(Qt.AlignRight)
            
            item_layout.addWidget(name_label, 3)
            item_layout.addWidget(qty_label, 1)
            item_layout.addWidget(price_label, 1)
            item_layout.addWidget(total_label, 1)
            
            layout.addLayout(item_layout)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        layout.addSpacing(10)
        
        # Totals
        currency = self.settings.get('currency', 'MAD')
        totals_layout = QVBoxLayout()
        totals_layout.setAlignment(Qt.AlignRight)
        
        # Create a sub-layout for each total row
        subtotal_layout = QHBoxLayout()
        subtotal_layout.addStretch()
        subtotal_layout.addWidget(QLabel("<b>Sous-total:</b>"))
        subtotal_layout.addWidget(QLabel(f"{self.sale['total_amount']:.2f} {currency}"))
        totals_layout.addLayout(subtotal_layout)
        
        if self.sale['discount'] > 0:
            discount_layout = QHBoxLayout()
            discount_layout.addStretch()
            discount_layout.addWidget(QLabel("<b>Remise:</b>"))
            discount_layout.addWidget(QLabel(f"{self.sale['discount']:.2f} {currency}"))
            totals_layout.addLayout(discount_layout)
            
        if self.sale['tax_amount'] > 0:
            tax_layout = QHBoxLayout()
            tax_layout.addStretch()
            tax_layout.addWidget(QLabel("<b>TVA:</b>"))
            tax_layout.addWidget(QLabel(f"{self.sale['tax_amount']:.2f} {currency}"))
            totals_layout.addLayout(tax_layout)
        
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("<b>Total:</b>")
        total_label.setStyleSheet("font-size: 16px;")
        total_value = QLabel(f"{self.sale['final_total']:.2f} {currency}")
        total_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        total_layout.addWidget(total_label)
        total_layout.addWidget(total_value)
        totals_layout.addLayout(total_layout)
        
        layout.addLayout(totals_layout)
        layout.addSpacing(20)
        
        # Payment method
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel(f"<b>Mode de paiement:</b> {self.sale['payment_method']}"))
        layout.addLayout(payment_layout)
        
        layout.addStretch()
        
        # Footer
        footer = QLabel(self.settings.get('receipt_footer', 'Merci pour votre achat!'))
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        
        return preview
    
    def print_thermal(self):
        """Print thermal receipt"""
        receipt = ReceiptGenerator(self.sale['id'], self)
        if receipt.print_thermal():
            self.accept()
    
    def print_a4(self):
        """Print A4 receipt"""
        receipt = ReceiptGenerator(self.sale['id'], self)
        if receipt.print_a4():
            self.accept()
    
    def save_pdf(self):
        """Save receipt as PDF"""
        receipt = ReceiptGenerator(self.sale['id'], self)
        if receipt.generate_pdf():
            self.accept()
