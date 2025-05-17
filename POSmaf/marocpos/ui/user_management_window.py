from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QHeaderView
)
from PyQt5.QtCore import Qt
from models.user import User

class UserManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Gestion des utilisateurs")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Header with search and add button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Liste des utilisateurs")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Rechercher:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom d'utilisateur ou rôle...")
        self.search_input.textChanged.connect(self.filter_users)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        header_layout.addLayout(search_layout)
        header_layout.addStretch()
        
        # Add user button
        add_user_btn = QPushButton("Ajouter un utilisateur")
        add_user_btn.clicked.connect(self.add_user)
        header_layout.addWidget(add_user_btn)
        
        layout.addLayout(header_layout)
        
        # Users table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["ID", "Nom d'utilisateur", "Rôle", "Statut", "Actions"])
        
        # Set column widths
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.user_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.user_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.user_table.setColumnWidth(0, 50)    # ID
        self.user_table.setColumnWidth(2, 100)   # Role
        self.user_table.setColumnWidth(3, 80)    # Status
        self.user_table.setColumnWidth(4, 150)   # Actions
        
        layout.addWidget(self.user_table)
        
        self.setLayout(layout)
        
        # Load users
        self.load_users()
    
    def load_users(self):
        """Load users into the table"""
        users = User.get_all_users()
        self.user_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # Convert to dictionary if not already
            if not isinstance(user, dict):
                user_dict = {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'active': user[3]
                }
            else:
                user_dict = user
            
            # ID
            id_item = QTableWidgetItem(str(user_dict['id']))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            self.user_table.setItem(row, 0, id_item)
            
            # Username
            username_item = QTableWidgetItem(user_dict['username'])
            username_item.setFlags(username_item.flags() & ~Qt.ItemIsEditable)
            self.user_table.setItem(row, 1, username_item)
            
            # Role
            role_item = QTableWidgetItem(user_dict['role'].capitalize())
            role_item.setFlags(role_item.flags() & ~Qt.ItemIsEditable)
            self.user_table.setItem(row, 2, role_item)
            
            # Status
            status = "Actif" if user_dict['active'] else "Inactif"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.user_table.setItem(row, 3, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            # Edit button
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(30)
            edit_btn.clicked.connect(lambda checked, u=user_dict: self.edit_user(u))
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, u=user_dict: self.delete_user(u))
            
            # Reset password button
            reset_pwd_btn = QPushButton("🔑")
            reset_pwd_btn.setMaximumWidth(30)
            reset_pwd_btn.setToolTip("Réinitialiser le mot de passe")
            reset_pwd_btn.clicked.connect(lambda checked, u=user_dict: self.reset_password(u))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addWidget(reset_pwd_btn)
            
            self.user_table.setCellWidget(row, 4, actions_widget)
    
    def add_user(self):
        """Open dialog to add a new user"""
        dialog = AddEditUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            user_data = dialog.get_data()
            if User.add_user(User(**user_data)):
                self.load_users()
                QMessageBox.information(self, "Succès", "Utilisateur ajouté avec succès!")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de l'ajout de l'utilisateur.")
    
    def edit_user(self, user):
        """Open dialog to edit a user"""
        dialog = AddEditUserDialog(self, user)
        if dialog.exec_() == QDialog.Accepted:
            user_data = dialog.get_data()
            if User.update_user(user['id'], user_data):
                self.load_users()
                QMessageBox.information(self, "Succès", "Utilisateur modifié avec succès!")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la modification de l'utilisateur.")
    
    def delete_user(self, user):
        """Delete a user"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            f"Êtes-vous sûr de vouloir supprimer l'utilisateur {user['username']} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if User.delete_user(user['id']):
                self.load_users()
                QMessageBox.information(self, "Succès", "Utilisateur supprimé avec succès!")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la suppression de l'utilisateur.")
    
    def reset_password(self, user):
        """Reset a user's password"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            f"Réinitialiser le mot de passe pour {user['username']} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            new_password = "password123"  # Default password
            if User.reset_password(user['id'], new_password):
                QMessageBox.information(
                    self, 
                    "Succès", 
                    f"Le mot de passe a été réinitialisé à: {new_password}"
                )
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la réinitialisation du mot de passe.")
    
    def filter_users(self):
        """Filter users by search text"""
        search_text = self.search_input.text().lower()
        for row in range(self.user_table.rowCount()):
            username = self.user_table.item(row, 1).text().lower()
            role = self.user_table.item(row, 2).text().lower()
            self.user_table.setRowHidden(
                row, 
                search_text not in username and search_text not in role
            )

class AddEditUserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Modifier utilisateur" if self.user else "Ajouter utilisateur")
        self.setMinimumWidth(300)
        
        layout = QFormLayout()
        
        # Username
        self.username_input = QLineEdit()
        layout.addRow("Nom d'utilisateur:", self.username_input)
        
        # Password (only for new users)
        if not self.user:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            layout.addRow("Mot de passe:", self.password_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "cashier", "manager"])
        layout.addRow("Rôle:", self.role_combo)
        
        # Active status
        self.active_combo = QComboBox()
        self.active_combo.addItems(["Actif", "Inactif"])
        layout.addRow("Statut:", self.active_combo)
        
        # Fill data if editing
        if self.user:
            self.username_input.setText(self.user['username'])
            
            # Find role index
            role_index = self.role_combo.findText(self.user['role'])
            if role_index >= 0:
                self.role_combo.setCurrentIndex(role_index)
            
            # Set active status
            self.active_combo.setCurrentIndex(0 if self.user['active'] else 1)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Get user data from the form"""
        data = {
            'username': self.username_input.text(),
            'role': self.role_combo.currentText(),
            'active': self.active_combo.currentText() == "Actif"
        }
        
        # Add password for new users
        if hasattr(self, 'password_input'):
            data['password'] = self.password_input.text()
        
        return data
