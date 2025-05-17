from database import get_connection

class Category:
    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description

    @staticmethod
    def get_all_categories():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description 
                    FROM Categories 
                    ORDER BY name
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"Error getting categories: {e}")
                return []
            finally:
                conn.close()
        return []

    @staticmethod
    def add_category(name, description=None):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Categories (name, description)
                    VALUES (?, ?)
                """, (name, description))
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"Error adding category: {e}")
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def update_category(category_id, name, description=None):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Categories 
                    SET name = ?, description = ?
                    WHERE id = ?
                """, (name, description, category_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating category: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def delete_category(category_id):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                try:
                    # Update products to remove the category reference
                    cursor.execute("""
                        UPDATE Products 
                        SET category_id = NULL 
                        WHERE category_id = ?
                    """, (category_id,))
                    
                    # Delete the category
                    cursor.execute("""
                        DELETE FROM Categories 
                        WHERE id = ?
                    """, (category_id,))
                    
                    cursor.execute("COMMIT")
                    return True
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    print(f"Error in delete_category transaction: {e}")
                    return False
            finally:
                conn.close()
        return False

    @staticmethod
    def clear_all_categories():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                try:
                    # Update all products to remove category references
                    cursor.execute("UPDATE Products SET category_id = NULL")
                    
                    # Delete all categories
                    cursor.execute("DELETE FROM Categories")
                    
                    # Reset the auto-increment counter
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name='Categories'")
                    
                    cursor.execute("COMMIT")
                    return True
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    print(f"Error in clear_all_categories transaction: {e}")
                    return False
            finally:
                conn.close()
        return False

    @staticmethod
    def get_category_by_id(category_id):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description 
                    FROM Categories 
                    WHERE id = ?
                """, (category_id,))
                row = cursor.fetchone()
                if row:
                    return Category(id=row[0], name=row[1], description=row[2])
                return None
            except Exception as e:
                print(f"Error getting category: {e}")
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def initialize_database():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Create Categories table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT
                    )
                """)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error initializing Categories table: {e}")
                return False
            finally:
                conn.close()
        return False