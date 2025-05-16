from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QDialog, QLineEdit, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from models.category import Category
from datetime import datetime

class CategoryManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Gestion des catégories")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Liste des catégories")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        add_button = QPushButton("Ajouter une catégorie")
        add_button.clicked.connect(self.add_category)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_button)
        layout.addLayout(header_layout)
        
        # Categories table
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(4)
        self.categories_table.setHorizontalHeaderLabels(["ID", "Nom", "Description", "Actions"])
        self.categories_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.categories_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.categories_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.categories_table.setColumnWidth(0, 50)
        self.categories_table.setColumnWidth(3, 100)
        layout.addWidget(self.categories_table)
        
        self.setLayout(layout)
        
        # Load categories
        self.load_categories()
    
    def load_categories(self):
        """Load categories into table"""
        categories = Category.get_all_categories()
        self.categories_table.setRowCount(len(categories))
        
        for row, category in enumerate(categories):
            # ID
            self.categories_table.setItem(row, 0, QTableWidgetItem(str(category[0])))
            # Name
            self.categories_table.setItem(row, 1, QTableWidgetItem(category[1]))
            # Description
            self.categories_table.setItem(row, 2, QTableWidgetItem(category[2] if category[2] else ""))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("✏️")
            delete_btn = QPushButton("🗑️")
            
            edit_btn.clicked.connect(lambda checked, cat=category: self.edit_category(cat))
            delete_btn.clicked.connect(lambda checked, id=category[0]: self.delete_category(id))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.categories_table.setCellWidget(row, 3, actions_widget)
    
    def add_category(self):
        """Open dialog to add a new category"""
        dialog = AddEditCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()
    
    def edit_category(self, category):
        """Open dialog to edit a category"""
        dialog = AddEditCategoryDialog(self, category)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()
    
    def delete_category(self, category_id):
        """Delete a category"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            "Êtes-vous sûr de vouloir supprimer cette catégorie ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if Category.delete_category(category_id):
                self.load_categories()
                QMessageBox.information(self, "Succès", "Catégorie supprimée avec succès!")
            else:
                QMessageBox.warning(self, "Erreur", "Échec de la suppression de la catégorie.")

class AddEditCategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Modifier la catégorie' if self.category else 'Ajouter une catégorie')
        self.setGeometry(300, 300, 400, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #80bdff;
                outline: 0;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Name field
        name_layout = QVBoxLayout()
        name_label = QLabel('Nom:')
        name_label.setStyleSheet("font-weight: bold;")
        self.name_input = QLineEdit()
        if self.category:
            self.name_input.setText(self.category[1])
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Description field
        desc_layout = QVBoxLayout()
        desc_label = QLabel('Description:')
        desc_label.setStyleSheet("font-weight: bold;")
        self.desc_input = QLineEdit()
        if self.category:
            self.desc_input.setText(self.category[2] or "")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton('Enregistrer')
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        cancel_button = QPushButton('Annuler')
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        save_button.clicked.connect(self.save_category)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save_category(self):
        name = self.name_input.text().strip()
        description = self.desc_input.text().strip()

        if not name:
            QMessageBox.warning(self, 'Erreur', 'Le nom est requis!')
            return

        if self.category:
            if Category.edit_category(self.category[0], name, description):
                QMessageBox.information(self, 'Succès', 'Catégorie modifiée avec succès!')
                self.accept()
            else:
                QMessageBox.warning(self, 'Erreur', 'Échec de la modification de la catégorie!')
        else:
            if Category.add_category(name, description):
                QMessageBox.information(self, 'Succès', 'Catégorie ajoutée avec succès!')
                self.accept()
            else:
                QMessageBox.warning(self, 'Erreur', 'Échec de l\'ajout de la catégorie!')

class CategoryManagementWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Gestion des catégories")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #212529;
            }
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 5px;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header section with info
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Title and datetime
        title_layout = QHBoxLayout()
        title_label = QLabel("Gestion des catégories")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529;")
        datetime_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        datetime_label.setStyleSheet("color: #6c757d;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(datetime_label)
        header_layout.addLayout(title_layout)
        
        # User info
        user_label = QLabel(f"Utilisateur: MAFPOS")
        user_label.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(user_label)
        
        layout.addWidget(header_frame)

        # Action buttons
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("➕ Ajouter une catégorie")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        clear_all_button = QPushButton("🗑️ Supprimer toutes les catégories")
        clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        refresh_button = QPushButton("🔄 Actualiser")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)

        add_button.clicked.connect(self.add_category)
        clear_all_button.clicked.connect(self.clear_all_categories)
        refresh_button.clicked.connect(self.load_categories)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(clear_all_button)
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)

        # Categories table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "Description", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(3, 100)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #495057;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e9ecef;
                color: #212529;
            }
        """)
        layout.addWidget(self.table)

        # Load categories
        self.load_categories()

    def load_categories(self):
        categories = Category.get_all_categories()
        self.table.setRowCount(len(categories))
        
        for row, category in enumerate(categories):
            # ID
            id_item = QTableWidgetItem(str(category[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, id_item)
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(category[1]))
            
            # Description
            self.table.setItem(row, 2, QTableWidgetItem(category[2] or ""))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(5)

            edit_btn = QPushButton("✏️")
            delete_btn = QPushButton("🗑️")
            
            edit_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                    color: #007bff;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)
            delete_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                    color: #dc3545;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)

            edit_btn.clicked.connect(lambda checked, c=category: self.edit_category(c))
            delete_btn.clicked.connect(lambda checked, id=category[0]: self.delete_category(id))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()
            
            self.table.setCellWidget(row, 3, action_widget)

    def add_category(self):
        dialog = AddEditCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()

    def edit_category(self, category):
        dialog = AddEditCategoryDialog(self, category)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()

    def delete_category(self, category_id):
        reply = QMessageBox.question(
            self,
            'Confirmation',
            'Êtes-vous sûr de vouloir supprimer cette catégorie ?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if Category.delete_category(category_id):
                self.load_categories()
                QMessageBox.information(self, "Succès", "Catégorie supprimée avec succès!")
            else:
                QMessageBox.warning(self, "Erreur", "Échec de la suppression de la catégorie.")

    def clear_all_categories(self):
        reply = QMessageBox.question(
            self,
            'Confirmation',
            'Êtes-vous sûr de vouloir supprimer TOUTES les catégories ? Cette action est irréversible.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if Category.clear_all_categories():
                self.load_categories()
                QMessageBox.information(self, "Succès", "Toutes les catégories ont été supprimées!")
            else:
                QMessageBox.warning(self, "Erreur", "Échec de la suppression des catégories.")