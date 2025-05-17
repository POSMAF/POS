from database import get_connection
import bcrypt
from datetime import datetime, UTC

class User:
    def __init__(self, username, password, role="cashier", active=1):
        self.username = username
        self.password = self._hash_password(password) if password else None
        # Ensure role is always lowercase to match database constraint
        self.role = role.lower() if role else "cashier"
        self.active = active

    def _hash_password(self, password):
        """Hash the password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def create_table():
        """Create or update the Users table."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # First, get existing columns
                cursor.execute("PRAGMA table_info(Users)")
                existing_columns = {row[1] for row in cursor.fetchall()}

                # Create table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL,
                        active INTEGER DEFAULT 1
                    )
                """)

                # Add new columns if they don't exist
                if 'last_login' not in existing_columns:
                    cursor.execute("ALTER TABLE Users ADD COLUMN last_login TIMESTAMP")
                
                # SQLite doesn't allow adding columns with DEFAULT CURRENT_TIMESTAMP
                # Add columns without defaults, then update existing rows
                try:
                    # For Python 3.11+
                    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                except AttributeError:
                    # For older Python versions
                    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                if 'created_at' not in existing_columns:
                    cursor.execute("ALTER TABLE Users ADD COLUMN created_at TIMESTAMP")
                    cursor.execute("UPDATE Users SET created_at = ? WHERE created_at IS NULL", (current_time,))
                    
                if 'updated_at' not in existing_columns:
                    cursor.execute("ALTER TABLE Users ADD COLUMN updated_at TIMESTAMP")
                    cursor.execute("UPDATE Users SET updated_at = ? WHERE updated_at IS NULL", (current_time,))

                conn.commit()
                return True
            except Exception as e:
                print(f"Error creating/updating Users table: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def add_user(user):
        """Add a new user to the database."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Users (username, password, role, active)
                    VALUES (?, ?, ?, ?)
                """, (
                    user.username,
                    user.password,
                    user.role,
                    user.active
                ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error adding user: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def get_user_by_username(username):
        """Get user by username."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, password, role, active
                    FROM Users 
                    WHERE username = ?
                """, (username,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'username': row[1],
                        'password': row[2],
                        'role': row[3],
                        'active': row[4]
                    }
                return None
            finally:
                conn.close()
        return None

    @staticmethod
    def get_all_users():
        """Get all users."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, role, active
                    FROM Users
                    ORDER BY username
                """)
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row[0],
                        'username': row[1],
                        'role': row[2],
                        'active': row[3]
                    })
                return users
            finally:
                conn.close()
        return []

    @staticmethod
    def update_user(user_id, username, role, active):
        """Update user details."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Users 
                    SET username = ?, role = ?, active = ?
                    WHERE id = ?
                """, (username, role, active, user_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating user: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def delete_user(user_id):
        """Delete a user."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Check if this is the last active user
                cursor.execute("""
                    SELECT COUNT(*) FROM Users WHERE active = 1 AND id != ?
                """, (user_id,))
                active_count = cursor.fetchone()[0]
                
                if active_count == 0:
                    print("Cannot delete the last active user")
                    return False

                cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error deleting user: {e}")
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def update_password(user_id, new_password):
        """Update user password."""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                hashed_password = bcrypt.hashpw(
                    new_password.encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                cursor.execute("""
                    UPDATE Users 
                    SET password = ?
                    WHERE id = ?
                """, (hashed_password, user_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating password: {e}")
                return False
            finally:
                conn.close()
        return False