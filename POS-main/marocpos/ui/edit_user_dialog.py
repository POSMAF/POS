from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
from models.user import User

class EditUserDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)

        # Ensure the user object is valid
        if not user:
            raise ValueError("User data is missing or invalid.")

        self.user = user
        self.init_ui()

    def init_ui(self):
        # Set dialog properties
        self.setWindowTitle("Edit User")
        self.setGeometry(200, 200, 400, 300)

        # Layout
        layout = QVBoxLayout()

        # Username field (read-only)
        self.username_input = QLineEdit(self)
        self.username_input.setText(self.user["username"])
        self.username_input.setReadOnly(True)
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)

        # Role dropdown
        self.role_dropdown = QComboBox(self)
        self.role_dropdown.addItems(["Admin", "Cashier", "Manager"])
        self.role_dropdown.setCurrentText(self.user["role"])
        layout.addWidget(QLabel("Role:"))
        layout.addWidget(self.role_dropdown)

        # Full name field
        self.fullname_input = QLineEdit(self)
        self.fullname_input.setText(self.user["full_name"])
        layout.addWidget(QLabel("Full Name:"))
        layout.addWidget(self.fullname_input)

        # Active status dropdown
        self.active_dropdown = QComboBox(self)
        self.active_dropdown.addItems(["Yes", "No"])
        self.active_dropdown.setCurrentText("Yes" if self.user["active"] else "No")
        layout.addWidget(QLabel("Active:"))
        layout.addWidget(self.active_dropdown)

        # Save button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        # Set layout
        self.setLayout(layout)

    def save_changes(self):
        # Get updated details
        role = self.role_dropdown.currentText()
        full_name = self.fullname_input.text().strip()
        active = 1 if self.active_dropdown.currentText() == "Yes" else 0

        # Validate input
        if not full_name:
            QMessageBox.warning(self, "Error", "Full Name is required.")
            return

        # Update user in the database
        if User.update_user(self.user["id"], role, full_name, active):
            QMessageBox.information(self, "Success", "User details updated successfully!")
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Error", "Failed to update user details.")