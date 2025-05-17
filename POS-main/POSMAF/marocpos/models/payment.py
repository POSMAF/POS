from database import get_connection
from datetime import datetime, UTC
import json

class Payment:
    """Model for managing payment methods and sales payments"""
    
    @staticmethod
    def create_tables():
        """Create the payment-related tables"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Create PaymentMethods table for available payment types
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS PaymentMethods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        active INTEGER DEFAULT 1,
                        requires_reference INTEGER DEFAULT 0,
                        requires_approval INTEGER DEFAULT 0,
                        icon TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create SalePayments table for multiple payments per sale
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS SalePayments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sale_id INTEGER NOT NULL,
                        payment_method_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        reference_number TEXT,
                        approved INTEGER DEFAULT 1,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sale_id) REFERENCES Sales(id) ON DELETE CASCADE,
                        FOREIGN KEY (payment_method_id) REFERENCES PaymentMethods(id)
                    )
                """)
                
                # Check if default payment methods exist, if not create them
                cursor.execute("SELECT COUNT(*) FROM PaymentMethods")
                if cursor.fetchone()[0] == 0:
                    # Insert default payment methods
                    default_methods = [
                        ('CASH', 'Paiement en espèces', 1, 0, 0, 'cash.png'),
                        ('CARD', 'Paiement par carte bancaire', 1, 1, 0, 'credit-card.png'),
                        ('CHECK', 'Paiement par chèque', 1, 1, 1, 'check.png'),
                        ('TRANSFER', 'Virement bancaire', 1, 1, 1, 'bank-transfer.png'),
                        ('MOBILE', 'Paiement mobile', 1, 1, 0, 'mobile-payment.png'),
                    ]
                    
                    try:
                        # For Python 3.11+
                        current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                    except AttributeError:
                        # For older Python versions
                        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    
                    for method in default_methods:
                        cursor.execute("""
                            INSERT INTO PaymentMethods (
                                name, description, active, 
                                requires_reference, requires_approval, 
                                icon, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (*method, current_time, current_time))
                
                conn.commit()
                print("✅ Payment tables created successfully")
                return True
            except Exception as e:
                print(f"❌ Error creating payment tables: {e}")
                return False
            finally:
                conn.close()
        return False
    
    @staticmethod
    def get_all_payment_methods(active_only=True):
        """Get all available payment methods"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, name, description, active, 
                           requires_reference, requires_approval, icon
                    FROM PaymentMethods
                """
                
                if active_only:
                    query += " WHERE active = 1"
                    
                query += " ORDER BY id"
                
                cursor.execute(query)
                return [dict(method) for method in cursor.fetchall()]
            except Exception as e:
                print(f"Error getting payment methods: {e}")
                return []
            finally:
                conn.close()
        return []
    
    @staticmethod
    def add_payment_method(name, description=None, active=True, requires_reference=False, requires_approval=False, icon=None):
        """Add a new payment method"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if method already exists
                cursor.execute("SELECT id FROM PaymentMethods WHERE name = ?", (name,))
                existing = cursor.fetchone()
                if existing:
                    return existing[0]  # Return existing ID
                
                # Prepare current timestamp
                try:
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert new payment method
                cursor.execute("""
                    INSERT INTO PaymentMethods (
                        name, description, active, 
                        requires_reference, requires_approval, 
                        icon, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, description, active, requires_reference, requires_approval, icon, current_time, current_time))
                
                method_id = cursor.lastrowid
                conn.commit()
                return method_id
            except Exception as e:
                print(f"Error adding payment method: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def update_payment_method(method_id, **kwargs):
        """Update an existing payment method"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                values = []
                
                for key, value in kwargs.items():
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                
                # Add updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                # Add method_id to values
                values.append(method_id)
                
                query = f"""
                    UPDATE PaymentMethods 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Error updating payment method: {e}")
                return False
            finally:
                conn.close()
        return False
    
    @staticmethod
    def add_sale_payment(sale_id, payment_method_id, amount, reference_number=None, approved=True, notes=None):
        """Add a payment for a sale"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Insert payment record
                cursor.execute("""
                    INSERT INTO SalePayments (
                        sale_id, payment_method_id, amount,
                        reference_number, approved, notes,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (sale_id, payment_method_id, amount, reference_number, approved, notes))
                
                payment_id = cursor.lastrowid
                conn.commit()
                
                return payment_id
            except Exception as e:
                print(f"Error adding sale payment: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def get_sale_payments(sale_id):
        """Get all payments for a specific sale"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT sp.*, pm.name as payment_method_name, pm.description as payment_method_description
                    FROM SalePayments sp
                    JOIN PaymentMethods pm ON sp.payment_method_id = pm.id
                    WHERE sp.sale_id = ?
                    ORDER BY sp.created_at
                """, (sale_id,))
                
                return [dict(payment) for payment in cursor.fetchall()]
            except Exception as e:
                print(f"Error getting sale payments: {e}")
                return []
            finally:
                conn.close()
        return []
    
    @staticmethod
    def get_payment_summary(start_date=None, end_date=None):
        """Get a summary of payments by method for a date range"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        pm.name as payment_method,
                        COUNT(sp.id) as transaction_count,
                        SUM(sp.amount) as total_amount
                    FROM SalePayments sp
                    JOIN PaymentMethods pm ON sp.payment_method_id = pm.id
                """
                
                params = []
                where_clauses = []
                
                if start_date:
                    where_clauses.append("sp.created_at >= ?")
                    params.append(start_date)
                    
                if end_date:
                    where_clauses.append("sp.created_at <= ?")
                    params.append(end_date)
                    
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += " GROUP BY pm.name ORDER BY total_amount DESC"
                
                cursor.execute(query, params)
                return [dict(summary) for summary in cursor.fetchall()]
            except Exception as e:
                print(f"Error getting payment summary: {e}")
                return []
            finally:
                conn.close()
        return []
