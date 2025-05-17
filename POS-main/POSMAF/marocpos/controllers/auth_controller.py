import hashlib
import re
import bcrypt
from database import get_connection
from models.user import User

class AuthController:
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt."""
        return User._hash_password(None, password)
    
    @staticmethod
    def is_bcrypt_hash(password_hash):
        """Check if a password hash is in bcrypt format."""
        # Bcrypt hashes typically start with $2b$ or $2a$ and are 60 characters long
        return bool(re.match(r'^\$2[ab]\$\d+\$', password_hash)) and len(password_hash) == 60
    
    @staticmethod
    def update_password_hash(user_id, password):
        """Update a user's password to use bcrypt."""
        return User.update_password(user_id, password)

    def login(self, username, password):
        """Authenticate a user."""
        user = User.get_user_by_username(username)
        if user and user['active']:
            stored_password = user['password']
            
            # Check if the stored password is a bcrypt hash
            if self.is_bcrypt_hash(stored_password):
                # Use bcrypt verification
                if User.verify_password(password, stored_password):
                    return user
            else:
                # Legacy plaintext comparison for backward compatibility
                if stored_password == password:
                    # Password matches - update to bcrypt for future logins
                    self.update_password_hash(user['id'], password)
                    return user
                    
        return None