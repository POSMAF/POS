from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
from controllers.auth_controller import AuthController
from models.user import User

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Set dialog properties
        self.setWindowTitle("Add User")
        self.setGeometry(200, 200, 400, 300)

        # Layout
        layout = QVBoxLayout()

        # Username field
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Enter username")
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)

        # Password field
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)

        # Role dropdown
        self.role_dropdown = QComboBox(self)
        self.role_dropdown.addItems(["Admin", "Cashier", "Manager"])
        layout.addWidget(QLabel("Role:"))
        layout.addWidget(self.role_dropdown)

        # Full name field
        self.fullname_input = QLineEdit(self)
        self.fullname_input.setPlaceholderText("Enter full name")
        layout.addWidget(QLabel("Full Name:"))
        layout.addWidget(self.fullname_input)

        # Add button
        add_button = QPushButton("Add User")
        add_button.clicked.connect(self.add_user)
        layout.addWidget(add_button)

        # Set layout
        self.setLayout(layout)

    def add_user(self):
        # Get user input
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_dropdown.currentText()
        full_name = self.fullname_input.text().strip()

        # Validate input
        if not username or not password or not full_name:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        # Hash password and create user
        password_hash = AuthController.hash_password(password)
        new_user = User(username=username, password_hash=password_hash, role=role, full_name=full_name)

        # Add user to database
        if User.add_user(new_user):
            QMessageBox.information(self, "Success", f"User '{username}' added successfully!")
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Error", f"Failed to add user '{username}'.")