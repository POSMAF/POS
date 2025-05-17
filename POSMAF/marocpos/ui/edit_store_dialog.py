from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
from models.store import Store

class EditStoreDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.init_ui()

    def init_ui(self):
        # Set dialog properties
        self.setWindowTitle("Edit Store")
        self.setGeometry(300, 200, 400, 250)

        # Layout
        layout = QVBoxLayout()

        # Store Name Input
        self.name_input = QLineEdit(self)
        self.name_input.setText(self.store["name"])
        layout.addWidget(QLabel("Store Name:"))
        layout.addWidget(self.name_input)

        # Store Location Input
        self.location_input = QLineEdit(self)
        self.location_input.setText(self.store["location"])
        layout.addWidget(QLabel("Store Location:"))
        layout.addWidget(self.location_input)

        # Active Status Dropdown
        self.active_dropdown = QComboBox(self)
        self.active_dropdown.addItems(["Yes", "No"])
        self.active_dropdown.setCurrentText("Yes" if self.store["active"] else "No")
        layout.addWidget(QLabel("Active:"))
        layout.addWidget(self.active_dropdown)

        # Save Button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        # Set layout
        self.setLayout(layout)

    def save_changes(self):
        # Get updated values
        name = self.name_input.text().strip()
        location = self.location_input.text().strip()
        active = 1 if self.active_dropdown.currentText() == "Yes" else 0

        # Validate input
        if not name or not location:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        # Update store in the database
        if Store.update_store(self.store["id"], name, location, active):
            QMessageBox.information(self, "Success", f"Store '{name}' updated successfully!")
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Error", f"Failed to update store '{name}'.")