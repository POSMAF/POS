from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from models.store import Store

class AddStoreDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Set dialog properties
        self.setWindowTitle("Add Store")
        self.setGeometry(300, 200, 400, 200)

        # Layout
        layout = QVBoxLayout()

        # Store Name Input
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter store name")
        layout.addWidget(QLabel("Store Name:"))
        layout.addWidget(self.name_input)

        # Store Location Input
        self.location_input = QLineEdit(self)
        self.location_input.setPlaceholderText("Enter store location")
        layout.addWidget(QLabel("Store Location:"))
        layout.addWidget(self.location_input)

        # Save Button
        save_button = QPushButton("Save Store")
        save_button.clicked.connect(self.save_store)
        layout.addWidget(save_button)

        # Set layout
        self.setLayout(layout)

    def save_store(self):
        # Get input values
        name = self.name_input.text().strip()
        location = self.location_input.text().strip()

        # Validate input
        if not name or not location:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        # Create and add store
        new_store = Store(name=name, location=location)
        if Store.add_store(new_store):
            QMessageBox.information(self, "Success", f"Store '{name}' added successfully!")
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Error", f"Failed to add store '{name}'. This name may already exist.")