from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QHeaderView, QWidget, QComboBox
)
from PyQt5.QtCore import Qt
from database import get_connection
from models.product_attribute import ProductAttribute as ProductAttributeModel

# Local version for the dialog, uses the model version underneath
class ProductAttribute:
    @staticmethod
    def get_all_attributes():
        """Get all product attributes - uses the model implementation"""
        return ProductAttributeModel.get_all_attributes()
    
    @staticmethod
    def get_values_by_attribute(attribute_id):
        """Get values for a specific attribute - uses the model implementation"""
        return ProductAttributeModel.get_attribute_values(attribute_id)
    
    @staticmethod
    def add_attribute(name, description=""):
        """Add a new product attribute - uses the model implementation"""
        return ProductAttributeModel.add_attribute(name, description)
    
    @staticmethod
    def add_attribute_value(attribute_id, value):
        """Add a value for an attribute - uses the model implementation"""
        return ProductAttributeModel.add_attribute_value(attribute_id, value)
    
    @staticmethod
    def delete_attribute(attribute_id):
        """Delete an attribute and its values - uses the model implementation"""
        return ProductAttributeModel.delete_attribute(attribute_id)
    
    @staticmethod
    def delete_attribute_value(value_id):
        """Delete an attribute value - uses the model implementation"""
        return ProductAttributeModel.delete_attribute_value(value_id)

class AttributeManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Gestion des attributs")
        self.setMinimumSize(800, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Attributes section
        attributes_label = QLabel("Attributs de produit")
        attributes_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(attributes_label)
        
        # Add attribute section
        add_attribute_layout = QHBoxLayout()
        
        self.attribute_name_input = QLineEdit()
        self.attribute_name_input.setPlaceholderText("Nom de l'attribut (ex: Taille, Couleur...)")
        
        add_attribute_btn = QPushButton("Ajouter attribut")
        add_attribute_btn.clicked.connect(self.add_attribute)
        
        add_attribute_layout.addWidget(self.attribute_name_input)
        add_attribute_layout.addWidget(add_attribute_btn)
        
        layout.addLayout(add_attribute_layout)
        
        # Attributes table
        self.attributes_table = QTableWidget()
        self.attributes_table.setColumnCount(3)
        self.attributes_table.setHorizontalHeaderLabels(["ID", "Nom", "Actions"])
        
        self.attributes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.attributes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.attributes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.attributes_table.setColumnWidth(0, 50)
        self.attributes_table.setColumnWidth(2, 150)
        
        layout.addWidget(self.attributes_table)
        
        # Attribute values section
        values_label = QLabel("Valeurs d'attribut")
        values_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(values_label)
        
        # Add value section
        add_value_layout = QHBoxLayout()
        
        add_value_label = QLabel("Pour attribut:")
        self.attribute_select = QLineEdit()
        self.attribute_select.setReadOnly(True)
        self.attribute_select.setPlaceholderText("Sélectionnez un attribut ci-dessus")
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Valeur de l'attribut (ex: Rouge, XL...)")
        self.value_input.setEnabled(False)
        
        add_value_btn = QPushButton("Ajouter valeur")
        add_value_btn.clicked.connect(self.add_attribute_value)
        add_value_btn.setEnabled(False)
        self.add_value_btn = add_value_btn
        
        add_value_layout.addWidget(add_value_label)
        add_value_layout.addWidget(self.attribute_select)
        add_value_layout.addWidget(self.value_input)
        add_value_layout.addWidget(add_value_btn)
        
        layout.addLayout(add_value_layout)
        
        # Values table
        self.values_table = QTableWidget()
        self.values_table.setColumnCount(3)
        self.values_table.setHorizontalHeaderLabels(["ID", "Valeur", "Actions"])
        
        self.values_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.values_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.values_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.values_table.setColumnWidth(0, 50)
        self.values_table.setColumnWidth(2, 100)
        
        layout.addWidget(self.values_table)
        
        # Close button
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # Connect signals
        self.attributes_table.itemClicked.connect(self.on_attribute_selected)
        
        # Initial load
        self.selected_attribute_id = None
        self.load_attributes()
        
    def load_attributes(self):
        """Load attributes into the table"""
        attributes = ProductAttribute.get_all_attributes()
        
        self.attributes_table.setRowCount(len(attributes))
        
        for row, attr in enumerate(attributes):
            # ID
            id_item = QTableWidgetItem(str(attr['id']))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.attributes_table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(attr['name'])
            name_item.setData(Qt.UserRole, attr['id'])
            self.attributes_table.setItem(row, 1, name_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, id=attr['id']: self.delete_attribute(id))
            
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.attributes_table.setCellWidget(row, 2, actions_widget)
            
    def load_attribute_values(self, attribute_id):
        """Load values for the selected attribute"""
        values = ProductAttribute.get_values_by_attribute(attribute_id)
        
        self.values_table.setRowCount(len(values))
        
        for row, val in enumerate(values):
            # ID
            id_item = QTableWidgetItem(str(val['id']))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.values_table.setItem(row, 0, id_item)
            
            # Value
            value_item = QTableWidgetItem(val['value'])
            value_item.setData(Qt.UserRole, val['id'])
            self.values_table.setItem(row, 1, value_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, id=val['id']: self.delete_attribute_value(id))
            
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.values_table.setCellWidget(row, 2, actions_widget)
            
    def on_attribute_selected(self, item):
        """Handle attribute selection"""
        if self.attributes_table.column(item) != 1:  # Only respond to clicks on the name column
            return
            
        attribute_id = item.data(Qt.UserRole)
        attribute_name = item.text()
        
        self.selected_attribute_id = attribute_id
        self.attribute_select.setText(attribute_name)
        
        # Enable value controls
        self.value_input.setEnabled(True)
        self.add_value_btn.setEnabled(True)
        
        # Load values for this attribute
        self.load_attribute_values(attribute_id)
        
    def add_attribute(self):
        """Add a new attribute"""
        name = self.attribute_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom d'attribut.")
            return
            
        # Add to database
        attribute_id = ProductAttribute.add_attribute(name)
        if attribute_id:
            self.attribute_name_input.clear()
            self.load_attributes()
            QMessageBox.information(self, "Succès", f"Attribut '{name}' ajouté avec succès.")
        else:
            QMessageBox.warning(self, "Erreur", "Erreur lors de l'ajout de l'attribut.")
        
    def add_attribute_value(self):
        """Add a value to the selected attribute"""
        if not self.selected_attribute_id:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord sélectionner un attribut.")
            return
            
        value = self.value_input.text().strip()
        if not value:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une valeur d'attribut.")
            return
            
        # Add to database
        value_id = ProductAttribute.add_attribute_value(self.selected_attribute_id, value)
        if value_id:
            self.value_input.clear()
            self.load_attribute_values(self.selected_attribute_id)
            QMessageBox.information(self, "Succès", f"Valeur '{value}' ajoutée avec succès.")
        else:
            QMessageBox.warning(self, "Erreur", "Erreur lors de l'ajout de la valeur. Assurez-vous qu'elle n'existe pas déjà.")
        
    def delete_attribute(self, attribute_id):
        """Delete an attribute and its values"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            'Supprimer cet attribut et toutes ses valeurs ?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if ProductAttribute.delete_attribute(attribute_id):
                # Reset if we deleted the selected attribute
                if self.selected_attribute_id == attribute_id:
                    self.selected_attribute_id = None
                    self.attribute_select.clear()
                    self.value_input.setEnabled(False)
                    self.add_value_btn.setEnabled(False)
                    self.values_table.setRowCount(0)
                
                self.load_attributes()
                QMessageBox.information(self, "Succès", "Attribut supprimé avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la suppression de l'attribut.")
        
    def delete_attribute_value(self, value_id):
        """Delete an attribute value"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            'Supprimer cette valeur d\'attribut ?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if ProductAttribute.delete_attribute_value(value_id):
                self.load_attribute_values(self.selected_attribute_id)
                QMessageBox.information(self, "Succès", "Valeur supprimée avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la suppression de la valeur.")
