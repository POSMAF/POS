from database import get_connection

class SettingsManager:
    @staticmethod
    def get_all_settings():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value, description FROM Settings")
                return cursor.fetchall()
            finally:
                conn.close()
        return []

    @staticmethod
    def update_setting(key, value):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Settings 
                    SET value = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE key = ?
                """, (value, key))
                conn.commit()
                return True
            finally:
                conn.close()
        return False

    @staticmethod
    def get_receipt_settings():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT value 
                    FROM Settings 
                    WHERE key IN (
                        'store_name', 'store_address', 'store_phone',
                        'store_email', 'receipt_footer', 'receipt_logo'
                    )
                """)
                return dict(cursor.fetchall())
            finally:
                conn.close()
        return {}