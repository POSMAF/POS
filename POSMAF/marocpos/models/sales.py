from database import get_connection
from datetime import datetime, UTC
from escpos.printer import Usb
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from PIL import Image
import os

class Sales:
    @staticmethod
    def create_tables():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Create Sales table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TIMESTAMP NOT NULL,
                        user_id INTEGER NOT NULL,
                        total_amount REAL NOT NULL,
                        discount REAL DEFAULT 0,
                        tax_amount REAL DEFAULT 0,
                        final_total REAL NOT NULL,
                        payment_method TEXT DEFAULT 'CASH',
                        payment_status TEXT DEFAULT 'COMPLETED',
                        notes TEXT,
                        FOREIGN KEY (user_id) REFERENCES Users(id)
                    )
                """)

                # Create SaleItems table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS SaleItems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sale_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity REAL NOT NULL,
                        unit_price REAL NOT NULL,
                        subtotal REAL NOT NULL,
                        FOREIGN KEY (sale_id) REFERENCES Sales(id),
                        FOREIGN KEY (product_id) REFERENCES Products(id)
                    )
                """)

                conn.commit()
                return True
            except Exception as e:
                print(f"Error creating sales tables: {e}")
                return False
            finally:
                conn.close()

    @staticmethod
    def create_sale(user_id, items, payment_method='CASH', discount=0, tax_rate=0):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")

                # Calculate totals
                subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
                tax_amount = subtotal * (tax_rate / 100)
                total_with_tax = subtotal + tax_amount
                final_total = total_with_tax - discount

                # Create sale record
                cursor.execute("""
                    INSERT INTO Sales (
                        created_at, user_id, total_amount, 
                        discount, tax_amount, final_total, 
                        payment_method
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    user_id, subtotal, discount, tax_amount,
                    final_total, payment_method
                ))
                
                sale_id = cursor.lastrowid

                # Add sale items
                for item in items:
                    cursor.execute("""
                        INSERT INTO SaleItems (
                            sale_id, product_id, quantity,
                            unit_price, subtotal
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        sale_id, item['product_id'], 
                        item['quantity'], item['unit_price'],
                        item['quantity'] * item['unit_price']
                    ))

                    # Update product stock
                    cursor.execute("""
                        UPDATE Products 
                        SET stock = stock - ? 
                        WHERE id = ?
                    """, (item['quantity'], item['product_id']))

                cursor.execute("COMMIT")
                return sale_id

            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Error creating sale: {e}")
                return None
            finally:
                conn.close()
        return None

class ReceiptPrinter:
    def __init__(self):
        self.load_settings()

    def load_settings(self):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM Settings")
                self.settings = dict(cursor.fetchall())
            finally:
                conn.close()

    def get_sale_data(self, sale_id):
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
                """, (sale_id,))
                sale = cursor.fetchone()

                # Get sale items with product names
                cursor.execute("""
                    SELECT si.*, p.name 
                    FROM SaleItems si
                    JOIN Products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (sale_id,))
                items = cursor.fetchall()

                return sale, items
            finally:
                conn.close()
        return None, None

    def print_thermal(self, sale_id):
        """Print receipt to thermal printer"""
        sale, items = self.get_sale_data(sale_id)
        if not sale:
            return False

        try:
            # Initialize printer (adjust vendor_id and product_id as needed)
            printer = Usb(0x0456, 0x0808)

            # Print header
            printer.set(align='center', font='a', width=2, height=2)
            printer.text(f"{self.settings.get('store_name', 'My Store')}\n\n")
            
            printer.set(align='center', font='a', width=1, height=1)
            printer.text(f"{self.settings.get('store_address', '')}\n")
            printer.text(f"Tel: {self.settings.get('store_phone', '')}\n\n")

            # Print sale info
            printer.set(align='left')
            printer.text(f"Date: {sale['created_at']}\n")
            printer.text(f"Receipt #: {sale['id']}\n")
            printer.text(f"Cashier: {sale['username']}\n\n")

            # Print items
            printer.text("--------------------------------\n")
            for item in items:
                printer.text(f"{item['name']}\n")
                printer.text(f"{item['quantity']} x {item['unit_price']} = {item['subtotal']}\n")
            printer.text("--------------------------------\n\n")

            # Print totals
            printer.set(align='right')
            printer.text(f"Subtotal: {sale['total_amount']}\n")
            if sale['discount'] > 0:
                printer.text(f"Discount: {sale['discount']}\n")
            if sale['tax_amount'] > 0:
                printer.text(f"Tax: {sale['tax_amount']}\n")
            printer.text(f"Total: {sale['final_total']}\n\n")

            # Print footer
            printer.set(align='center')
            printer.text(f"{self.settings.get('receipt_footer', 'Thank you!')}\n")
            printer.cut()

            return True

        except Exception as e:
            print(f"Error printing receipt: {e}")
            return False

    def generate_pdf(self, sale_id, output_path=None):
        """Generate PDF receipt"""
        sale, items = self.get_sale_data(sale_id)
        if not sale:
            return None

        if not output_path:
            output_path = f"receipt_{sale_id}.pdf"

        try:
            # Create PDF
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4

            # Add logo if exists
            logo_path = self.settings.get('receipt_logo')
            if logo_path and os.path.exists(logo_path):
                img = Image.open(logo_path)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                c.drawImage(logo_path, 40, height - 120, width=200, height=200*aspect)

            # Header
            c.setFont("Helvetica-Bold", 24)
            c.drawString(40, height - 40, self.settings.get('store_name', 'My Store'))
            
            c.setFont("Helvetica", 12)
            c.drawString(40, height - 60, self.settings.get('store_address', ''))
            c.drawString(40, height - 80, f"Tel: {self.settings.get('store_phone', '')}")

            # Sale info
            c.drawString(40, height - 120, f"Date: {sale['created_at']}")
            c.drawString(40, height - 140, f"Receipt #: {sale['id']}")
            c.drawString(40, height - 160, f"Cashier: {sale['username']}")

            # Items
            y = height - 200
            c.drawString(40, y, "Item")
            c.drawString(300, y, "Qty")
            c.drawString(400, y, "Price")
            c.drawString(500, y, "Total")
            y -= 20

            for item in items:
                if y < 50:  # New page if needed
                    c.showPage()
                    y = height - 50
                c.drawString(40, y, item['name'])
                c.drawString(300, y, str(item['quantity']))
                c.drawString(400, y, str(item['unit_price']))
                c.drawString(500, y, str(item['subtotal']))
                y -= 20

            # Totals
            y -= 20
            c.drawString(400, y, "Subtotal:")
            c.drawString(500, y, str(sale['total_amount']))
            
            if sale['discount'] > 0:
                y -= 20
                c.drawString(400, y, "Discount:")
                c.drawString(500, y, str(sale['discount']))
            
            if sale['tax_amount'] > 0:
                y -= 20
                c.drawString(400, y, "Tax:")
                c.drawString(500, y, str(sale['tax_amount']))
            
            y -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(400, y, "Total:")
            c.drawString(500, y, str(sale['final_total']))

            # Footer
            c.setFont("Helvetica", 10)
            c.drawString(40, 30, self.settings.get('receipt_footer', 'Thank you!'))

            c.save()
            return output_path

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None