from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy, QMainWindow, QAction,
    QMenu, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont
import os
import sys

class DashboardWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("MarocPOS - Tableau de Bord")
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Menu grid
        menu_grid = self.create_menu_grid()
        main_layout.addWidget(menu_grid)
        
        # Status bar info
        self.statusBar().showMessage(f"Connecté en tant que: {self.user['username'] if self.user else 'Invité'}")
        
    def create_header(self):
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #24786d;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Logo/app name
        logo_label = QLabel("MarocPOS")
        logo_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(logo_label)
        
        # User info
        if self.user:
            user_label = QLabel(f"Bienvenue, {self.user['username']}")
            user_label.setStyleSheet("""
                font-size: 16px;
                color: white;
            """)
            header_layout.addWidget(user_label, alignment=Qt.AlignRight)
        
        return header_frame
        
    def create_menu_grid(self):
        menu_frame = QFrame()
        menu_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        grid_layout = QGridLayout(menu_frame)
        grid_layout.setSpacing(20)
        
        # Create menu items
        menu_items = [
            {
                "title": "Ventes",
                "icon": "icons/sales.png",
                "color": "#28a745",
                "description": "Gérer les ventes et le panier",
                "callback": self.open_sales
            },
            {
                "title": "Produits",
                "icon": "icons/products.png",
                "color": "#007bff",
                "description": "Gérer les produits et le stock",
                "callback": self.open_products
            },
            {
                "title": "Catégories",
                "icon": "icons/categories.png",
                "color": "#fd7e14",
                "description": "Gérer les catégories de produits",
                "callback": self.open_categories
            },
            {
                "title": "Utilisateurs",
                "icon": "icons/users.png",
                "color": "#6f42c1",
                "description": "Gérer les utilisateurs du système",
                "callback": self.open_users
            },
            {
                "title": "Historique",
                "icon": "icons/history.png",
                "color": "#17a2b8",
                "description": "Historique des ventes",
                "callback": self.open_history
            },
            {
                "title": "Magasins",
                "icon": "icons/stores.png",
                "color": "#dc3545",
                "description": "Gérer les magasins",
                "callback": self.open_stores
            },
            {
                "title": "Paramètres",
                "icon": "icons/settings.png",
                "color": "#6c757d",
                "description": "Configurer l'application",
                "callback": self.open_settings
            },
            {
                "title": "Rapports",
                "icon": "icons/reports.png",
                "color": "#20c997",
                "description": "Rapports et statistiques",
                "callback": self.open_reports
            }
        ]
        
        # Add menu items to grid
        row, col = 0, 0
        max_cols = 4
        
        for item in menu_items:
            menu_button = self.create_menu_button(
                title=item["title"],
                icon=item.get("icon"),
                color=item.get("color", "#007bff"),
                description=item.get("description", ""),
                callback=item.get("callback")
            )
            
            grid_layout.addWidget(menu_button, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        return menu_frame
        
    def create_menu_button(self, title, icon=None, color="#007bff", description="", callback=None):
        button_frame = QFrame()
        button_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button_frame.setMinimumHeight(150)
        button_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: {self.lighten_color(color)};
                cursor: pointer;
            }}
        """)
        
        # Make the frame clickable
        button_frame.mousePressEvent = lambda e: callback() if callback else None
        
        layout = QVBoxLayout(button_frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
            
        # Add stretch to push content to the top
        layout.addStretch()
        
        return button_frame
    
    def lighten_color(self, color):
        """Lighten a hex color by 20%"""
        # Remove # if present
        color = color.lstrip('#')
        
        # Convert to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Lighten by 20%
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def open_sales(self):
        try:
            from .sales_management_windows import SalesManagementWindow
            self.sales_window = SalesManagementWindow(self.user)
            self.sales_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture de la gestion des ventes: {str(e)}")
            
    def open_products(self):
        try:
            from .product_management_window import ProductManagementWindow
            self.products_window = ProductManagementWindow()
            self.products_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture de la gestion des produits: {str(e)}")
            
    def open_categories(self):
        try:
            from .category_management_window import CategoryManagementWindow
            self.categories_window = CategoryManagementWindow()
            self.categories_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture de la gestion des catégories: {str(e)}")
            
    def open_users(self):
        try:
            from .user_management_window import UserManagementWindow
            self.users_window = UserManagementWindow()
            self.users_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture de la gestion des utilisateurs: {str(e)}")
            
    def open_history(self):
        try:
            from .sales_history_windows import SalesHistoryWindow
            self.history_window = SalesHistoryWindow()
            self.history_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture de l'historique: {str(e)}")
            
    def open_stores(self):
        try:
            from .store_management_windows import StoreManagementWindow
            self.stores_window = StoreManagementWindow()
            self.stores_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture de la gestion des magasins: {str(e)}")
            
    def open_settings(self):
        try:
            from .settings_window import SettingsWindow
            self.settings_window = SettingsWindow()
            self.settings_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture des paramètres: {str(e)}")
            
    def open_reports(self):
        try:
            from .reports_window import ReportsWindow
            self.reports_window = ReportsWindow(self.user)
            self.reports_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture des rapports: {str(e)}")
