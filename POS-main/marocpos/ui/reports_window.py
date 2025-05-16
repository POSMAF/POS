from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QTabWidget, QComboBox, QDateEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QScrollArea, QMessageBox, QGroupBox, QFormLayout, QGridLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from models.sales_report import SalesReport
from models.payment import Payment
import json
from datetime import datetime, timedelta

class ReportsWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Rapports et Statistiques")
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel("Rapports et Statistiques")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #24786d;")
        main_layout.addWidget(header)
        
        # Date filter section
        date_widget = QWidget()
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        date_label = QLabel("Période :")
        date_label.setStyleSheet("font-weight: bold;")
        date_layout.addWidget(date_label)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Aujourd'hui", 
            "Hier", 
            "Cette semaine", 
            "Semaine dernière", 
            "Ce mois", 
            "Mois dernier", 
            "Personnalisé"
        ])
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        date_layout.addWidget(self.period_combo)
        
        date_layout.addWidget(QLabel("Du :"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setEnabled(False)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("Au :"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        date_layout.addWidget(self.end_date)
        
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_reports)
        date_layout.addWidget(refresh_btn)
        
        date_layout.addStretch()
        main_layout.addWidget(date_widget)
        
        # Tab widget for different reports
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
                color: #495057;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
        
        # Create tabs
        self.tab_sales = QWidget()
        self.tab_products = QWidget()
        self.tab_inventory = QWidget()
        self.tab_payment = QWidget()
        
        self.setup_sales_tab()
        self.setup_products_tab()
        self.setup_inventory_tab()
        self.setup_payment_tab()
        
        self.tabs.addTab(self.tab_sales, "Ventes")
        self.tabs.addTab(self.tab_products, "Produits")
        self.tabs.addTab(self.tab_inventory, "Inventaire")
        self.tabs.addTab(self.tab_payment, "Paiements")
        
        main_layout.addWidget(self.tabs)
        
        # Initial report load
        self.refresh_reports()
        
    def setup_sales_tab(self):
        """Setup the sales report tab"""
        layout = QVBoxLayout(self.tab_sales)
        
        # Summary section
        self.sales_summary_widget = QWidget()
        summary_layout = QGridLayout(self.sales_summary_widget)
        
        # Create summary boxes
        self.summary_boxes = []
        summary_items = [
            {"title": "Nombre de ventes", "key": "sale_count", "color": "#28a745", "suffix": ""},
            {"title": "Total des ventes", "key": "total_sales", "color": "#007bff", "suffix": " MAD"},
            {"title": "Vente moyenne", "key": "average_sale", "color": "#fd7e14", "suffix": " MAD"},
            {"title": "Plus petite vente", "key": "min_sale", "color": "#6c757d", "suffix": " MAD"},
            {"title": "Plus grande vente", "key": "max_sale", "color": "#dc3545", "suffix": " MAD"},
            {"title": "Total remises", "key": "total_discount", "color": "#6f42c1", "suffix": " MAD"}
        ]
        
        # Add summary boxes in a grid (2 rows, 3 columns)
        for i, item in enumerate(summary_items):
            box = self.create_summary_box(
                title=item["title"],
                value="0",
                suffix=item["suffix"],
                color=item["color"]
            )
            self.summary_boxes.append((box, item["key"]))
            
            row = i // 3
            col = i % 3
            summary_layout.addWidget(box, row, col)
        
        layout.addWidget(self.sales_summary_widget)
        
        # Sales by category table
        category_group = QGroupBox("Ventes par catégorie")
        category_layout = QVBoxLayout(category_group)
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Catégorie", "Articles vendus", "Montant total"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.category_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.category_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.category_table.setColumnWidth(1, 150)
        self.category_table.setColumnWidth(2, 150)
        
        category_layout.addWidget(self.category_table)
        layout.addWidget(category_group)
        
        # Top Products table
        products_group = QGroupBox("Produits les plus vendus")
        products_layout = QVBoxLayout(products_group)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["Produit", "Quantité vendue", "Montant total", "Nb. ventes"])
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.products_table.setColumnWidth(1, 120)
        self.products_table.setColumnWidth(2, 120)
        self.products_table.setColumnWidth(3, 100)
        
        products_layout.addWidget(self.products_table)
        layout.addWidget(products_group)
        
    def setup_products_tab(self):
        """Setup the products analysis tab"""
        layout = QVBoxLayout(self.tab_products)
        
        # Product filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Produit :"))
        
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(300)
        filter_layout.addWidget(self.product_combo)
        
        filter_btn = QPushButton("Analyser")
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        filter_btn.clicked.connect(self.analyze_product)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Product details
        self.product_details = QWidget()
        details_layout = QVBoxLayout(self.product_details)
        
        # Product info section
        info_group = QGroupBox("Informations produit")
        info_layout = QFormLayout(info_group)
        
        self.product_name_label = QLabel("-")
        self.product_price_label = QLabel("-")
        self.product_cost_label = QLabel("-")
        self.product_margin_label = QLabel("-")
        self.product_total_sold_label = QLabel("-")
        self.product_total_revenue_label = QLabel("-")
        
        info_layout.addRow("Nom du produit:", self.product_name_label)
        info_layout.addRow("Prix de vente:", self.product_price_label)
        info_layout.addRow("Prix d'achat:", self.product_cost_label)
        info_layout.addRow("Marge:", self.product_margin_label)
        info_layout.addRow("Quantité vendue:", self.product_total_sold_label)
        info_layout.addRow("Chiffre d'affaires:", self.product_total_revenue_label)
        
        details_layout.addWidget(info_group)
        
        # Variant sales table (if product has variants)
        self.variant_group = QGroupBox("Ventes par variante")
        variant_layout = QVBoxLayout(self.variant_group)
        
        self.variant_table = QTableWidget()
        self.variant_table.setColumnCount(4)
        self.variant_table.setHorizontalHeaderLabels(["Variante", "Quantité vendue", "Montant total", "% des ventes"])
        self.variant_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.variant_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.variant_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.variant_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.variant_table.setColumnWidth(1, 120)
        self.variant_table.setColumnWidth(2, 120)
        self.variant_table.setColumnWidth(3, 100)
        
        variant_layout.addWidget(self.variant_table)
        details_layout.addWidget(self.variant_group)
        self.variant_group.hide()  # Hide initially
        
        # Monthly sales history
        history_group = QGroupBox("Historique des ventes")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Mois", "Quantité vendue", "Montant total", "Nb. ventes"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.history_table.setColumnWidth(0, 100)
        
        history_layout.addWidget(self.history_table)
        details_layout.addWidget(history_group)
        
        layout.addWidget(self.product_details)
        
        # Load product list
        self.load_product_list()
        
    def setup_inventory_tab(self):
        """Setup the inventory report tab"""
        layout = QVBoxLayout(self.tab_inventory)
        
        # Inventory summary section
        self.inventory_summary_widget = QWidget()
        summary_layout = QGridLayout(self.inventory_summary_widget)
        
        # Create summary boxes
        self.inventory_summary_boxes = []
        summary_items = [
            {"title": "Total produits", "key": "total_products", "color": "#28a745", "suffix": ""},
            {"title": "Stock faible", "key": "low_stock_products", "color": "#dc3545", "suffix": " produits"},
            {"title": "Stock attention", "key": "warning_stock_products", "color": "#fd7e14", "suffix": " produits"},
            {"title": "Valeur du stock", "key": "total_stock_value", "color": "#007bff", "suffix": " MAD"},
            {"title": "Valeur de vente", "key": "total_retail_value", "color": "#6f42c1", "suffix": " MAD"},
            {"title": "Profit potentiel", "key": "potential_profit", "color": "#20c997", "suffix": " MAD"}
        ]
        
        # Add summary boxes in a grid (2 rows, 3 columns)
        for i, item in enumerate(summary_items):
            box = self.create_summary_box(
                title=item["title"],
                value="0",
                suffix=item["suffix"],
                color=item["color"]
            )
            self.inventory_summary_boxes.append((box, item["key"]))
            
            row = i // 3
            col = i % 3
            summary_layout.addWidget(box, row, col)
        
        layout.addWidget(self.inventory_summary_widget)
        
        # Low stock products table
        low_stock_group = QGroupBox("Produits à stock faible")
        low_stock_layout = QVBoxLayout(low_stock_group)
        
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(5)
        self.low_stock_table.setHorizontalHeaderLabels([
            "Produit", "Catégorie", "Stock actuel", "Stock minimum", "Prix"
        ])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.low_stock_table.setColumnWidth(1, 150)
        self.low_stock_table.setColumnWidth(2, 100)
        self.low_stock_table.setColumnWidth(3, 100)
        self.low_stock_table.setColumnWidth(4, 100)
        
        low_stock_layout.addWidget(self.low_stock_table)
        layout.addWidget(low_stock_group)
        
        # Top value products table
        top_value_group = QGroupBox("Produits de plus grande valeur")
        top_value_layout = QVBoxLayout(top_value_group)
        
        self.top_value_table = QTableWidget()
        self.top_value_table.setColumnCount(5)
        self.top_value_table.setHorizontalHeaderLabels([
            "Produit", "Catégorie", "Stock", "Prix unitaire", "Valeur totale"
        ])
        self.top_value_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.top_value_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.top_value_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.top_value_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.top_value_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.top_value_table.setColumnWidth(1, 150)
        self.top_value_table.setColumnWidth(2, 80)
        self.top_value_table.setColumnWidth(3, 100)
        self.top_value_table.setColumnWidth(4, 120)
        
        top_value_layout.addWidget(self.top_value_table)
        layout.addWidget(top_value_group)
        
    def setup_payment_tab(self):
        """Setup the payment analysis tab"""
        layout = QVBoxLayout(self.tab_payment)
        
        # Payment methods summary
        methods_group = QGroupBox("Méthodes de paiement")
        methods_layout = QVBoxLayout(methods_group)
        
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(3)
        self.payment_table.setHorizontalHeaderLabels([
            "Méthode de paiement", "Nombre de transactions", "Montant total"
        ])
        self.payment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.payment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.payment_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.payment_table.setColumnWidth(1, 150)
        self.payment_table.setColumnWidth(2, 150)
        
        methods_layout.addWidget(self.payment_table)
        layout.addWidget(methods_group)
        
        # Payment averages
        averages_group = QGroupBox("Indicateurs de paiement")
        averages_layout = QHBoxLayout(averages_group)
        
        avg_transaction_box = self.create_summary_box(
            title="Transaction moyenne",
            value="0",
            suffix=" MAD",
            color="#007bff"
        )
        self.avg_transaction_box = avg_transaction_box
        
        cash_percent_box = self.create_summary_box(
            title="% en espèces",
            value="0",
            suffix="%",
            color="#28a745"
        )
        self.cash_percent_box = cash_percent_box
        
        card_percent_box = self.create_summary_box(
            title="% en carte",
            value="0",
            suffix="%",
            color="#fd7e14"
        )
        self.card_percent_box = card_percent_box
        
        other_percent_box = self.create_summary_box(
            title="% autres méthodes",
            value="0",
            suffix="%",
            color="#6f42c1"
        )
        self.other_percent_box = other_percent_box
        
        averages_layout.addWidget(avg_transaction_box)
        averages_layout.addWidget(cash_percent_box)
        averages_layout.addWidget(card_percent_box)
        averages_layout.addWidget(other_percent_box)
        
        layout.addWidget(averages_group)
        
        # Daily payments chart (could be represented as a table for now)
        daily_group = QGroupBox("Paiements par jour")
        daily_layout = QVBoxLayout(daily_group)
        
        self.daily_payment_table = QTableWidget()
        self.daily_payment_table.setColumnCount(4)
        self.daily_payment_table.setHorizontalHeaderLabels([
            "Date", "Nombre de ventes", "Montant total", "Méthode principale"
        ])
        self.daily_payment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.daily_payment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.daily_payment_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.daily_payment_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.daily_payment_table.setColumnWidth(0, 100)
        
        daily_layout.addWidget(self.daily_payment_table)
        layout.addWidget(daily_group)
        
    def create_summary_box(self, title, value, suffix="", color="#007bff"):
        """Create a summary box widget"""
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 10px;
                min-height: 100px;
            }}
        """)
        
        layout = QVBoxLayout(box)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        """)
        
        # Value label
        value_label = QLabel(f"{value}{suffix}")
        value_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        
        # Store the value label for future updates
        box.value_label = value_label
        box.suffix = suffix
        
        return box
        
    def on_period_changed(self, index):
        """Handle period selection change"""
        today = QDate.currentDate()
        
        # Enable/disable custom date fields
        custom_mode = (index == 6)  # "Personnalisé" is at index 6
        self.start_date.setEnabled(custom_mode)
        self.end_date.setEnabled(custom_mode)
        
        # Set appropriate date range based on selection
        if not custom_mode:
            if index == 0:  # Aujourd'hui
                self.start_date.setDate(today)
                self.end_date.setDate(today)
            elif index == 1:  # Hier
                yesterday = today.addDays(-1)
                self.start_date.setDate(yesterday)
                self.end_date.setDate(yesterday)
            elif index == 2:  # Cette semaine
                start_of_week = today.addDays(-(today.dayOfWeek() - 1))
                self.start_date.setDate(start_of_week)
                self.end_date.setDate(today)
            elif index == 3:  # Semaine dernière
                start_of_last_week = today.addDays(-(today.dayOfWeek() + 6))
                end_of_last_week = today.addDays(-(today.dayOfWeek()))
                self.start_date.setDate(start_of_last_week)
                self.end_date.setDate(end_of_last_week)
            elif index == 4:  # Ce mois
                start_of_month = QDate(today.year(), today.month(), 1)
                self.start_date.setDate(start_of_month)
                self.end_date.setDate(today)
            elif index == 5:  # Mois dernier
                last_month = today.addMonths(-1)
                start_of_last_month = QDate(last_month.year(), last_month.month(), 1)
                end_of_last_month = QDate(today.year(), today.month(), 1).addDays(-1)
                self.start_date.setDate(start_of_last_month)
                self.end_date.setDate(end_of_last_month)
    
    def refresh_reports(self):
        """Refresh all reports based on the current date range"""
        try:
            # Get date range
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            
            # Load sales report
            self.load_sales_report(start_date, end_date)
            
            # Load inventory report
            self.load_inventory_report()
            
            # Load payment analysis
            self.load_payment_analysis(start_date, end_date)
            
            # Update product analysis if a product is selected
            if hasattr(self, 'selected_product_id') and self.selected_product_id:
                self.analyze_product(self.selected_product_id)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des rapports: {str(e)}")
    
    def load_sales_report(self, start_date, end_date):
        """Load sales report data"""
        try:
            # Get sales report data
            report_data = SalesReport.get_sales_range(start_date, end_date)
            
            if not report_data:
                return
                
            # Update summary boxes
            for box, key in self.summary_boxes:
                value = report_data['summary'].get(key, 0) or 0
                if isinstance(value, (int, float)):
                    if key in ['total_sales', 'average_sale', 'min_sale', 'max_sale', 'total_discount']:
                        formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = f"{value}"
                else:
                    formatted_value = str(value)
                
                box.value_label.setText(f"{formatted_value}{box.suffix}")
            
            # Update category table
            categories = report_data['top_categories']
            self.category_table.setRowCount(len(categories))
            
            for row, category in enumerate(categories):
                # Category name
                name_item = QTableWidgetItem(category['category_name'])
                self.category_table.setItem(row, 0, name_item)
                
                # Items sold
                items_sold = category.get('items_sold', 0) or 0
                items_item = QTableWidgetItem(str(items_sold))
                items_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.category_table.setItem(row, 1, items_item)
                
                # Total sales
                total_sales = category.get('total_sales', 0) or 0
                sales_item = QTableWidgetItem(f"{total_sales:.2f} MAD")
                sales_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.category_table.setItem(row, 2, sales_item)
            
            # Update products table
            products = report_data['top_products']
            self.products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Product name
                name_item = QTableWidgetItem(product['product_name'])
                self.products_table.setItem(row, 0, name_item)
                
                # Quantity sold
                qty_sold = product.get('quantity_sold', 0) or 0
                qty_item = QTableWidgetItem(str(qty_sold))
                qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(row, 1, qty_item)
                
                # Total sales
                total_sales = product.get('total_sales', 0) or 0
                sales_item = QTableWidgetItem(f"{total_sales:.2f} MAD")
                sales_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(row, 2, sales_item)
                
                # Number of sales
                num_sales = product.get('number_of_sales', 0) or 0
                num_item = QTableWidgetItem(str(num_sales))
                num_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(row, 3, num_item)
                
                # Store product ID for double-click action
                name_item.setData(Qt.UserRole, product['product_id'])
            
            # Connect double-click to analyze product
            self.products_table.cellDoubleClicked.connect(
                lambda row, col: self.analyze_product(
                    self.products_table.item(row, 0).data(Qt.UserRole)
                ) if col == 0 else None
            )
            
        except Exception as e:
            print(f"Error loading sales report: {e}")
            raise
    
    def load_inventory_report(self):
        """Load inventory report data"""
        try:
            # Get inventory report data
            report_data = SalesReport.get_inventory_report()
            
            if not report_data:
                return
                
            # Update summary boxes
            for box, key in self.inventory_summary_boxes:
                value = report_data['summary'].get(key, 0) or 0
                if isinstance(value, (int, float)):
                    if key in ['total_stock_value', 'total_retail_value', 'potential_profit']:
                        formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = f"{value}"
                else:
                    formatted_value = str(value)
                
                box.value_label.setText(f"{formatted_value}{box.suffix}")
            
            # Update low stock table
            low_stock_products = [p for p in report_data['products'] if p['stock_status'] in ['low', 'warning']]
            self.low_stock_table.setRowCount(len(low_stock_products))
            
            for row, product in enumerate(low_stock_products):
                # Product name
                name_item = QTableWidgetItem(product['product_name'])
                if product['stock_status'] == 'low':
                    name_item.setBackground(QColor(255, 200, 200))  # Light red for low stock
                else:
                    name_item.setBackground(QColor(255, 235, 156))  # Light orange for warning
                self.low_stock_table.setItem(row, 0, name_item)
                
                # Category
                cat_item = QTableWidgetItem(product['category_name'])
                self.low_stock_table.setItem(row, 1, cat_item)
                
                # Current stock
                stock_item = QTableWidgetItem(str(product['current_stock']))
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.low_stock_table.setItem(row, 2, stock_item)
                
                # Minimum stock
                min_stock_item = QTableWidgetItem(str(product['minimum_stock']))
                min_stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.low_stock_table.setItem(row, 3, min_stock_item)
                
                # Price
                price_item = QTableWidgetItem(f"{product['price']:.2f} MAD")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.low_stock_table.setItem(row, 4, price_item)
            
            # Update top value products table
            # Sort products by stock value
            top_value_products = sorted(
                [p for p in report_data['products'] if p.get('stock_value', 0) > 0],
                key=lambda p: p.get('stock_value', 0),
                reverse=True
            )[:10]  # Top 10
            
            self.top_value_table.setRowCount(len(top_value_products))
            
            for row, product in enumerate(top_value_products):
                # Product name
                name_item = QTableWidgetItem(product['product_name'])
                self.top_value_table.setItem(row, 0, name_item)
                
                # Category
                cat_item = QTableWidgetItem(product['category_name'])
                self.top_value_table.setItem(row, 1, cat_item)
                
                # Stock
                stock_item = QTableWidgetItem(str(product['current_stock']))
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.top_value_table.setItem(row, 2, stock_item)
                
                # Unit price
                price_item = QTableWidgetItem(f"{product['price']:.2f} MAD")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.top_value_table.setItem(row, 3, price_item)
                
                # Total value
                value = product.get('stock_value', 0) or 0
                value_item = QTableWidgetItem(f"{value:.2f} MAD")
                value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.top_value_table.setItem(row, 4, value_item)
                
        except Exception as e:
            print(f"Error loading inventory report: {e}")
            raise
    
    def load_payment_analysis(self, start_date, end_date):
        """Load payment analysis data"""
        try:
            # Get payment summary data
            payment_data = Payment.get_payment_summary(start_date, end_date)
            
            if not payment_data:
                return
                
            # Update payment methods table
            self.payment_table.setRowCount(len(payment_data))
            
            total_transactions = sum(p.get('transaction_count', 0) or 0 for p in payment_data)
            total_amount = sum(p.get('total_amount', 0) or 0 for p in payment_data)
            
            cash_amount = 0
            card_amount = 0
            
            for row, payment in enumerate(payment_data):
                # Method name
                name_item = QTableWidgetItem(payment['payment_method'])
                self.payment_table.setItem(row, 0, name_item)
                
                # Transaction count
                count = payment.get('transaction_count', 0) or 0
                count_item = QTableWidgetItem(str(count))
                count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.payment_table.setItem(row, 1, count_item)
                
                # Total amount
                amount = payment.get('total_amount', 0) or 0
                amount_item = QTableWidgetItem(f"{amount:.2f} MAD")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.payment_table.setItem(row, 2, amount_item)
                
                # Track cash and card amounts
                method = payment['payment_method'].upper()
                if method == 'CASH' or method == 'ESPÈCES':
                    cash_amount = amount
                elif method == 'CARD' or method == 'CARTE':
                    card_amount = amount
            
            # Update summary boxes
            avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0
            self.avg_transaction_box.value_label.setText(f"{avg_transaction:.2f} MAD")
            
            cash_percent = (cash_amount / total_amount * 100) if total_amount > 0 else 0
            self.cash_percent_box.value_label.setText(f"{cash_percent:.1f}%")
            
            card_percent = (card_amount / total_amount * 100) if total_amount > 0 else 0
            self.card_percent_box.value_label.setText(f"{card_percent:.1f}%")
            
            other_percent = 100 - cash_percent - card_percent
            self.other_percent_box.value_label.setText(f"{other_percent:.1f}%")
            
            # We would need more data for daily payments table
            # For now we'll leave it empty
            
        except Exception as e:
            print(f"Error loading payment analysis: {e}")
            raise
    
    def load_product_list(self):
        """Load the list of products for the product selector"""
        try:
            from models.product import Product
            products = Product.get_all_products()
            
            # Clear and populate the combo box
            self.product_combo.clear()
            self.product_combo.addItem("Sélectionnez un produit...", None)
            
            for product in products:
                self.product_combo.addItem(product['name'], product['id'])
                
        except Exception as e:
            print(f"Error loading product list: {e}")
    
    def analyze_product(self, product_id=None):
        """Analyze a specific product"""
        # If called from button click with no args, get product_id from combo
        if product_id is None:
            index = self.product_combo.currentIndex()
            if index <= 0:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un produit à analyser.")
                return
                
            product_id = self.product_combo.currentData()
        else:
            # If called with product_id, set the combo box to match
            for i in range(self.product_combo.count()):
                if self.product_combo.itemData(i) == product_id:
                    self.product_combo.setCurrentIndex(i)
                    break
        
        # Store selected product for report refresh
        self.selected_product_id = product_id
            
        try:
            # Get date range
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            
            # Get product performance data
            performance = SalesReport.get_product_performance(product_id, start_date, end_date)
            
            if not performance:
                QMessageBox.warning(self, "Erreur", "Aucune donnée trouvée pour ce produit.")
                return
            
            # Update product info
            product = performance['product']
            
            self.product_name_label.setText(product.get('product_name', '-'))
            self.product_price_label.setText(f"{product.get('current_price', 0):.2f} MAD")
            self.product_cost_label.setText(f"{product.get('current_cost', 0):.2f} MAD")
            
            # Calculate margin
            price = product.get('current_price', 0) or 0
            cost = product.get('current_cost', 0) or 0
            if cost > 0:
                margin_pct = ((price - cost) / cost) * 100
                self.product_margin_label.setText(f"{margin_pct:.2f}%")
            else:
                self.product_margin_label.setText("-")
                
            self.product_total_sold_label.setText(f"{product.get('total_quantity', 0) or 0}")
            self.product_total_revenue_label.setText(f"{product.get('total_sales', 0) or 0:.2f} MAD")
            
            # Update variant sales if the product has variants
            variant_sales = performance.get('variant_sales', [])
            if variant_sales:
                self.variant_group.show()
                self.variant_table.setRowCount(len(variant_sales))
                
                total_qty = sum(v.get('quantity_sold', 0) or 0 for v in variant_sales)
                
                for row, variant in enumerate(variant_sales):
                    # Variant name
                    name = variant.get('variant_name', f"Variante #{variant.get('variant_id', '')}")
                    name_item = QTableWidgetItem(name)
                    self.variant_table.setItem(row, 0, name_item)
                    
                    # Quantity sold
                    qty = variant.get('quantity_sold', 0) or 0
                    qty_item = QTableWidgetItem(str(qty))
                    qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.variant_table.setItem(row, 1, qty_item)
                    
                    # Total sales
                    sales = variant.get('total_sales', 0) or 0
                    sales_item = QTableWidgetItem(f"{sales:.2f} MAD")
                    sales_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.variant_table.setItem(row, 2, sales_item)
                    
                    # Percentage
                    pct = (qty / total_qty * 100) if total_qty > 0 else 0
                    pct_item = QTableWidgetItem(f"{pct:.1f}%")
                    pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.variant_table.setItem(row, 3, pct_item)
            else:
                self.variant_group.hide()
            
            # Update monthly sales history
            monthly_sales = performance.get('monthly_sales', [])
            self.history_table.setRowCount(len(monthly_sales))
            
            for row, month_data in enumerate(monthly_sales):
                # Month
                month_item = QTableWidgetItem(month_data['month'])
                self.history_table.setItem(row, 0, month_item)
                
                # Quantity sold
                qty = month_data.get('quantity_sold', 0) or 0
                qty_item = QTableWidgetItem(str(qty))
                qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.history_table.setItem(row, 1, qty_item)
                
                # Total sales
                sales = month_data.get('total_sales', 0) or 0
                sales_item = QTableWidgetItem(f"{sales:.2f} MAD")
                sales_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.history_table.setItem(row, 2, sales_item)
                
                # Number of sales
                num_sales = month_data.get('number_of_sales', 0) or 0
                num_item = QTableWidgetItem(str(num_sales))
                num_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.history_table.setItem(row, 3, num_item)
                
            # Switch to the products tab
            self.tabs.setCurrentWidget(self.tab_products)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'analyse du produit: {str(e)}")
