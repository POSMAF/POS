from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from controllers.auth_controller import AuthController
from models.user import User

class ResetPasswordDialog(QDialog):
    def __init__(self, username=None, parent=None):
        super().__init__(parent)
        self.username = username
        self.init_ui()

    def init_ui(self):
        # Set dialog properties
        self.setWindowTitle("Reset Password")
        self.setGeometry(200, 200, 400, 200)

        # Layout
        layout = QVBoxLayout()

        # Username field (if not provided)
        if not self.username:
            self.username_input = QLineEdit(self)
            self.username_input.setPlaceholderText("Enter username")
            layout.addWidget(QLabel("Username:"))
            layout.addWidget(self.username_input)

        # New password field
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter new password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("New Password:"))
        layout.addWidget(self.password_input)

        # Confirm password field
        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Confirm Password:"))
        layout.addWidget(self.confirm_password_input)

        # Reset button
        reset_button = QPushButton("Reset Password")
        reset_button.clicked.connect(self.reset_password)
        layout.addWidget(reset_button)

        # Set layout
        self.setLayout(layout)

    def reset_password(self):
        # Get username (if not provided)
        username = self.username or self.username_input.text().strip()
        new_password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        # Validate input
        if not username or not new_password or not confirm_password:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        # Fetch user and update password
        user = User.get_user_by_username(username)
        if not user:
            QMessageBox.warning(self, "Error", f"User '{username}' not found.")
            return

        password_hash = AuthController.hash_password(new_password)
        if User.update_password(user["id"], password_hash):
            QMessageBox.information(self, "Success", f"Password for '{username}' has been reset.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to reset password for '{username}'.")