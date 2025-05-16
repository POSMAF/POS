from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from models.sales import Sales

class SalesHistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Sales History")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        layout = QVBoxLayout()

        # Sales Table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(["ID", "Total", "Discount", "Tax", "Final Total", "Date"])
        layout.addWidget(self.sales_table)

        # Set layout
        self.setLayout(layout)

        # Load sales
        self.load_sales()

    def load_sales(self):
        """Load sales from the database."""
        sales = Sales.get_sales()
        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            self.sales_table.setItem(row, 0, QTableWidgetItem(str(sale["id"])))
            self.sales_table.setItem(row, 1, QTableWidgetItem(f"{sale['total']:.2f}"))
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{sale['discount']:.2f}"))
            self.sales_table.setItem(row, 3, QTableWidgetItem(f"{sale['tax']:.2f}"))
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"{sale['final_total']:.2f}"))
            self.sales_table.setItem(row, 5, QTableWidgetItem(sale["created_at"]))