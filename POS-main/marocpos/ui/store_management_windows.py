from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from models.store import Store
from ui.add_store_dialog import AddStoreDialog
from ui.edit_store_dialog import EditStoreDialog


class StoreManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Store Management - MarocPOS")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        layout = QVBoxLayout()

        # Table to display stores
        self.store_table = QTableWidget()
        self.store_table.setColumnCount(5)  # Added column for address
        self.store_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone", "Actions"])
        layout.addWidget(self.store_table)

        # Buttons for store actions
        button_layout = QHBoxLayout()
        add_store_button = QPushButton("Add Store")
        edit_store_button = QPushButton("Edit Store")
        delete_store_button = QPushButton("Delete Store")

        button_layout.addWidget(add_store_button)
        button_layout.addWidget(edit_store_button)
        button_layout.addWidget(delete_store_button)
        layout.addLayout(button_layout)

        # Set layout
        self.setLayout(layout)

        # Connect buttons to methods
        add_store_button.clicked.connect(self.add_store)
        edit_store_button.clicked.connect(self.edit_store)
        delete_store_button.clicked.connect(self.delete_store)

        # Load stores into the table
        self.load_stores()

    def load_stores(self):
        """Load stores from the database and populate the table."""
        stores = Store.get_all_stores()
        self.store_table.setRowCount(len(stores))

        for row, store in enumerate(stores):
            self.store_table.setItem(row, 0, QTableWidgetItem(str(store["id"])))
            self.store_table.setItem(row, 1, QTableWidgetItem(store["name"]))
            self.store_table.setItem(row, 2, QTableWidgetItem(store["location"]))
            self.store_table.setItem(row, 3, QTableWidgetItem("Yes" if store["active"] else "No"))

    def add_store(self):
        """Open a dialog to add a new store."""
        dialog = AddStoreDialog(self)
        if dialog.exec_():  # If the dialog is accepted
            self.load_stores()  # Refresh the store table

    def edit_store(self):
        """Open a dialog to edit the selected store."""
        selected_row = self.store_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a store to edit.")
            return

        # Construct store object from the selected row
        try:
            store = {
                "id": int(self.store_table.item(selected_row, 0).text()),
                "name": self.store_table.item(selected_row, 1).text(),
                "location": self.store_table.item(selected_row, 2).text(),
                "active": 1 if self.store_table.item(selected_row, 3).text() == "Yes" else 0
            }
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to retrieve store data: {e}")
            return

        # Open edit dialog
        dialog = EditStoreDialog(store, self)
        if dialog.exec_():  # If the dialog is accepted
            self.load_stores()  # Refresh the store table

    def delete_store(self):
        """Delete the selected store."""
        selected_row = self.store_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a store to delete.")
            return

        store_id = self.store_table.item(selected_row, 0).text()
        confirmation = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete store ID {store_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            if Store.delete_store(int(store_id)):
                QMessageBox.information(self, "Success", f"Store ID {store_id} deleted successfully!")
                self.load_stores()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete store.")