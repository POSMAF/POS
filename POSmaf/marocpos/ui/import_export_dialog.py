from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QComboBox, QCheckBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer
from models.product import Product
from models.category import Category
import csv
import json
import os

class ImportExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Importation/Exportation de Produits")
        self.resize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.export_tab = QWidget()
        self.import_tab = QWidget()
        
        self.setup_export_tab()
        self.setup_import_tab()
        
        self.tabs.addTab(self.export_tab, "Exportation")
        self.tabs.addTab(self.import_tab, "Importation")
        
        main_layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
    def setup_export_tab(self):
        layout = QVBoxLayout(self.export_tab)
        
        # Export options group
        options_group = QGroupBox("Options d'exportation")
        options_layout = QFormLayout(options_group)
        
        # Export type
        self.export_type = QComboBox()
        self.export_type.addItems(["Tous les produits", "Produits sans variantes", "Produits avec variantes", "Variantes uniquement"])
        options_layout.addRow("Type d'exportation:", self.export_type)
        
        # Include fields
        fields_layout = QHBoxLayout()
        self.include_stock = QCheckBox("Stock")
        self.include_stock.setChecked(True)
        self.include_prices = QCheckBox("Prix")
        self.include_prices.setChecked(True)
        self.include_images = QCheckBox("Chemin des images")
        self.include_images.setChecked(True)
        
        fields_layout.addWidget(self.include_stock)
        fields_layout.addWidget(self.include_prices)
        fields_layout.addWidget(self.include_images)
        fields_layout.addStretch()
        
        options_layout.addRow("Inclure:", fields_layout)
        
        # CSV Options
        csv_options = QHBoxLayout()
        
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems([",", ";", "Tab"])
        
        self.enclosure_combo = QComboBox()
        self.enclosure_combo.addItems(['"', "'"])
        
        csv_options.addWidget(QLabel("Délimiteur:"))
        csv_options.addWidget(self.delimiter_combo)
        csv_options.addWidget(QLabel("Encadrement:"))
        csv_options.addWidget(self.enclosure_combo)
        csv_options.addStretch()
        
        options_layout.addRow("Options CSV:", csv_options)
        
        layout.addWidget(options_group)
        
        # Export destination
        dest_layout = QHBoxLayout()
        self.export_path = QLineEdit()
        self.export_path.setPlaceholderText("Chemin de destination")
        self.export_path.setReadOnly(True)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_export_path)
        
        dest_layout.addWidget(self.export_path)
        dest_layout.addWidget(browse_button)
        
        layout.addLayout(dest_layout)
        
        # Progress
        self.export_progress = QProgressBar()
        self.export_progress.setRange(0, 100)
        self.export_progress.setValue(0)
        self.export_progress.setVisible(False)
        layout.addWidget(self.export_progress)
        
        # Export button
        export_button = QPushButton("Exporter")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        export_button.clicked.connect(self.export_products)
        layout.addWidget(export_button)
        
        # Preview section
        preview_group = QGroupBox("Aperçu")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(7)
        self.preview_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Catégorie", "Prix", "Prix d'achat", "Stock", "Variantes"
        ])
        
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.preview_table.setColumnWidth(0, 50)
        self.preview_table.setColumnWidth(2, 150)
        self.preview_table.setColumnWidth(3, 80)
        self.preview_table.setColumnWidth(4, 100)
        self.preview_table.setColumnWidth(5, 80)
        self.preview_table.setColumnWidth(6, 100)
        
        preview_layout.addWidget(self.preview_table)
        
        # Refresh preview button
        refresh_button = QPushButton("Actualiser l'aperçu")
        refresh_button.clicked.connect(self.refresh_export_preview)
        preview_layout.addWidget(refresh_button)
        
        layout.addWidget(preview_group)
        
        # Load the initial preview
        self.refresh_export_preview()
        
    def setup_import_tab(self):
        layout = QVBoxLayout(self.import_tab)
        
        # Import file selection
        file_layout = QHBoxLayout()
        
        self.import_path = QLineEdit()
        self.import_path.setPlaceholderText("Fichier CSV à importer")
        self.import_path.setReadOnly(True)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_import_path)
        
        file_layout.addWidget(self.import_path)
        file_layout.addWidget(browse_button)
        
        layout.addLayout(file_layout)
        
        # Import options
        options_group = QGroupBox("Options d'importation")
        options_layout = QFormLayout(options_group)
        
        # CSV Options
        csv_options = QHBoxLayout()
        
        self.import_delimiter_combo = QComboBox()
        self.import_delimiter_combo.addItems([",", ";", "Tab"])
        
        self.import_enclosure_combo = QComboBox()
        self.import_enclosure_combo.addItems(['"', "'"])
        
        csv_options.addWidget(QLabel("Délimiteur:"))
        csv_options.addWidget(self.import_delimiter_combo)
        csv_options.addWidget(QLabel("Encadrement:"))
        csv_options.addWidget(self.import_enclosure_combo)
        csv_options.addStretch()
        
        options_layout.addRow("Options CSV:", csv_options)
        
        # Import behavior
        behavior_layout = QHBoxLayout()
        
        self.update_existing = QCheckBox("Mettre à jour les produits existants")
        self.update_existing.setChecked(True)
        
        self.create_categories = QCheckBox("Créer les catégories manquantes")
        self.create_categories.setChecked(True)
        
        behavior_layout.addWidget(self.update_existing)
        behavior_layout.addWidget(self.create_categories)
        behavior_layout.addStretch()
        
        options_layout.addRow("Comportement:", behavior_layout)
        
        layout.addWidget(options_group)
        
        # Progress
        self.import_progress = QProgressBar()
        self.import_progress.setRange(0, 100)
        self.import_progress.setValue(0)
        self.import_progress.setVisible(False)
        layout.addWidget(self.import_progress)
        
        # Import button
        import_button = QPushButton("Importer")
        import_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        import_button.clicked.connect(self.import_products)
        layout.addWidget(import_button)
        
        # Preview section
        preview_group = QGroupBox("Aperçu du fichier")
        preview_layout = QVBoxLayout(preview_group)
        
        self.import_preview_table = QTableWidget()
        self.import_preview_table.setColumnCount(0)
        self.import_preview_table.setRowCount(0)
        
        preview_layout.addWidget(self.import_preview_table)
        
        layout.addWidget(preview_group)
        
    def browse_export_path(self):
        """Browse for export file path"""
        default_path = os.path.expanduser("~/produits_export.csv")
        path, _ = QFileDialog.getSaveFileName(
            self, "Sélectionner le fichier d'exportation", 
            default_path, "Fichiers CSV (*.csv)"
        )
        
        if path:
            self.export_path.setText(path)
            
    def browse_import_path(self):
        """Browse for import file path"""
        default_path = os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier d'importation", 
            default_path, "Fichiers CSV (*.csv)"
        )
        
        if path:
            self.import_path.setText(path)
            self.load_import_preview()
            
    def refresh_export_preview(self):
        """Load products preview for export"""
        try:
            # Get all products
            products = Product.get_all_products()
            
            # Filter based on export type
            export_type = self.export_type.currentText()
            if export_type == "Produits sans variantes":
                products = [p for p in products if not p.get('has_variants')]
            elif export_type == "Produits avec variantes":
                products = [p for p in products if p.get('has_variants')]
            
            # Clear table and set row count
            self.preview_table.setRowCount(0)
            self.preview_table.setRowCount(min(len(products), 100))  # Limit to 100 rows in preview
            
            # Add products to table
            for row, product in enumerate(products):
                if row >= 100:  # Limit preview to 100 rows
                    break
                    
                # ID
                id_item = QTableWidgetItem(str(product['id']))
                self.preview_table.setItem(row, 0, id_item)
                
                # Name
                name_item = QTableWidgetItem(product['name'])
                self.preview_table.setItem(row, 1, name_item)
                
                # Category
                category_name = product.get('category_name', 'Non catégorisé')
                cat_item = QTableWidgetItem(category_name)
                self.preview_table.setItem(row, 2, cat_item)
                
                # Price
                price_item = QTableWidgetItem(f"{product.get('unit_price', 0):.2f}")
                self.preview_table.setItem(row, 3, price_item)
                
                # Purchase price
                cost_item = QTableWidgetItem(f"{product.get('purchase_price', 0):.2f}")
                self.preview_table.setItem(row, 4, cost_item)
                
                # Stock
                stock_item = QTableWidgetItem(str(product.get('stock', 0)))
                self.preview_table.setItem(row, 5, stock_item)
                
                # Has variants
                has_variants = product.get('has_variants', False)
                variant_item = QTableWidgetItem("Oui" if has_variants else "Non")
                self.preview_table.setItem(row, 6, variant_item)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement de l'aperçu: {str(e)}")
            
    def load_import_preview(self):
        """Load preview of the import file"""
        path = self.import_path.text()
        if not path or not os.path.exists(path):
            return
            
        try:
            # Determine delimiter
            delimiter = self.import_delimiter_combo.currentText()
            if delimiter == "Tab":
                delimiter = '\t'
                
            # Open the file and read the first few rows
            with open(path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter, quotechar=self.import_enclosure_combo.currentText())
                
                # Get headers and a few rows of data
                headers = next(reader)
                preview_rows = []
                for i, row in enumerate(reader):
                    if i >= 10:  # Limit to 10 rows for preview
                        break
                    preview_rows.append(row)
                    
                # Setup the table
                self.import_preview_table.setColumnCount(len(headers))
                self.import_preview_table.setHorizontalHeaderLabels(headers)
                self.import_preview_table.setRowCount(len(preview_rows))
                
                # Fill the table with data
                for row_idx, row_data in enumerate(preview_rows):
                    for col_idx, cell_data in enumerate(row_data):
                        if col_idx < len(headers):  # Ensure we don't exceed column count
                            self.import_preview_table.setItem(row_idx, col_idx, QTableWidgetItem(cell_data))
                            
                # Adjust column widths
                for col in range(len(headers)):
                    self.import_preview_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la lecture du fichier CSV: {str(e)}")
    
    def export_products(self):
        """Export products to CSV file"""
        # Validate path
        path = self.export_path.text()
        if not path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier de destination.")
            return
            
        # Get export options
        export_type = self.export_type.currentText()
        include_stock = self.include_stock.isChecked()
        include_prices = self.include_prices.isChecked()
        include_images = self.include_images.isChecked()
        
        # Get delimiter
        delimiter = self.delimiter_combo.currentText()
        if delimiter == "Tab":
            delimiter = '\t'
            
        quotechar = self.enclosure_combo.currentText()
        
        try:
            # Show progress bar
            self.export_progress.setVisible(True)
            self.export_progress.setValue(10)
            
            # Get products
            products = Product.get_all_products()
            
            # Filter products based on export type
            if export_type == "Produits sans variantes":
                products = [p for p in products if not p.get('has_variants')]
            elif export_type == "Produits avec variantes":
                products = [p for p in products if p.get('has_variants')]
            
            self.export_progress.setValue(30)
            
            # Prepare headers
            headers = ['id', 'name', 'description', 'barcode', 'category_id', 'category_name']
            
            if include_prices:
                headers.extend(['unit_price', 'purchase_price'])
                
            if include_stock:
                headers.extend(['stock', 'min_stock'])
                
            headers.append('has_variants')
            
            if include_images:
                headers.append('image_path')
                
            # Prepare data rows
            rows = []
            
            for product in products:
                row = [
                    product.get('id', ''),
                    product.get('name', ''),
                    product.get('description', ''),
                    product.get('barcode', ''),
                    product.get('category_id', ''),
                    product.get('category_name', '')
                ]
                
                if include_prices:
                    row.extend([
                        product.get('unit_price', 0),
                        product.get('purchase_price', 0)
                    ])
                    
                if include_stock:
                    row.extend([
                        product.get('stock', 0),
                        product.get('min_stock', 0)
                    ])
                    
                row.append(1 if product.get('has_variants') else 0)
                
                if include_images:
                    row.append(product.get('image_path', ''))
                    
                rows.append(row)
                
            self.export_progress.setValue(60)
            
            # Export variants if requested
            variants_file = None
            if export_type in ["Produits avec variantes", "Variantes uniquement"]:
                variants_path = path.replace('.csv', '_variants.csv')
                variants_file = open(variants_path, 'w', newline='', encoding='utf-8')
                variants_writer = csv.writer(variants_file, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
                
                # Variant headers
                variant_headers = ['product_id', 'product_name', 'variant_name', 'sku', 'barcode']
                
                if include_prices:
                    variant_headers.extend(['price_adjustment', 'unit_price', 'purchase_price'])
                    
                if include_stock:
                    variant_headers.append('stock')
                    
                variant_headers.append('attribute_values')
                
                variants_writer.writerow(variant_headers)
                
                # Write variant rows
                for product in products:
                    if product.get('has_variants'):
                        variants = Product.get_variants(product['id'])
                        for variant in variants:
                            variant_row = [
                                product.get('id', ''),
                                product.get('name', ''),
                                variant.get('name', ''),
                                variant.get('sku', ''),
                                variant.get('barcode', '')
                            ]
                            
                            if include_prices:
                                # Use total_price_adjustment if available
                                price_adj = variant.get('total_price_adjustment', variant.get('price_adjustment', 0))
                                variant_row.extend([
                                    price_adj,
                                    variant.get('unit_price', 0),
                                    variant.get('purchase_price', 0)
                                ])
                                
                            if include_stock:
                                variant_row.append(variant.get('stock', 0))
                                
                            # Convert attribute values to JSON string
                            attr_values = variant.get('attributes', {})
                            variant_row.append(json.dumps(attr_values))
                            
                            variants_writer.writerow(variant_row)
            
            self.export_progress.setValue(80)
            
            # Write main products file
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
                
                # Write headers
                writer.writerow(headers)
                
                # Write data rows
                for row in rows:
                    writer.writerow(row)
                    
            # Close variants file if opened
            if variants_file:
                variants_file.close()
                
            self.export_progress.setValue(100)
            
            # Show success message
            if variants_file:
                QMessageBox.information(
                    self, 
                    "Exportation réussie", 
                    f"Les produits ont été exportés avec succès dans:\n{path}\n\nLes variantes ont été exportées dans:\n{variants_path}"
                )
            else:
                QMessageBox.information(
                    self, 
                    "Exportation réussie", 
                    f"Les produits ont été exportés avec succès dans:\n{path}"
                )
                
            # Hide progress after a delay
            QTimer.singleShot(2000, lambda: self.export_progress.setVisible(False))
            
        except Exception as e:
            self.export_progress.setVisible(False)
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'exportation: {str(e)}")
            
    def import_products(self):
        """Import products from CSV file"""
        # Validate path
        path = self.import_path.text()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier CSV valide.")
            return
            
        # Get import options
        update_existing = self.update_existing.isChecked()
        create_categories = self.create_categories.isChecked()
        
        # Get delimiter
        delimiter = self.import_delimiter_combo.currentText()
        if delimiter == "Tab":
            delimiter = '\t'
            
        quotechar = self.import_enclosure_combo.currentText()
        
        try:
            # Show progress bar
            self.import_progress.setVisible(True)
            self.import_progress.setValue(10)
            
            # Read products CSV
            products_data = []
            with open(path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=delimiter, quotechar=quotechar)
                for row in reader:
                    products_data.append(row)
                    
            self.import_progress.setValue(30)
            
            # Check if a variants file exists
            variants_path = path.replace('.csv', '_variants.csv')
            variants_data = []
            
            if os.path.exists(variants_path):
                with open(variants_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile, delimiter=delimiter, quotechar=quotechar)
                    for row in reader:
                        variants_data.append(row)
                        
            self.import_progress.setValue(50)
            
            # Create category mapping (name -> id) for newly created categories
            category_mapping = {}
            
            # Import products
            imported_count = 0
            updated_count = 0
            failed_count = 0
            
            for product in products_data:
                try:
                    # Get category
                    category_id = product.get('category_id')
                    category_name = product.get('category_name')
                    
                    if not category_id and category_name and create_categories:
                        # Check if we've already created this category
                        if category_name in category_mapping:
                            category_id = category_mapping[category_name]
                        else:
                            # Create new category
                            try:
                                category_id = Category.add_category(category_name)
                                if category_id:
                                    category_mapping[category_name] = category_id
                            except Exception as e:
                                print(f"Error creating category {category_name}: {e}")
                    
                    # Convert stock and price values
                    try:
                        unit_price = float(product.get('unit_price', 0))
                    except (ValueError, TypeError):
                        unit_price = 0
                        
                    try:
                        purchase_price = float(product.get('purchase_price', 0))
                    except (ValueError, TypeError):
                        purchase_price = 0
                        
                    try:
                        stock = int(product.get('stock', 0))
                    except (ValueError, TypeError):
                        stock = 0
                        
                    try:
                        min_stock = int(product.get('min_stock', 0))
                    except (ValueError, TypeError):
                        min_stock = 0
                        
                    try:
                        has_variants = bool(int(product.get('has_variants', 0)))
                    except (ValueError, TypeError):
                        has_variants = False
                    
                    # Prepare product data
                    product_data = {
                        'name': product.get('name', ''),
                        'description': product.get('description', ''),
                        'barcode': product.get('barcode', ''),
                        'category_id': category_id,
                        'unit_price': unit_price,
                        'purchase_price': purchase_price,
                        'stock': stock,
                        'min_stock': min_stock,
                        'has_variants': has_variants,
                        'image_path': product.get('image_path', '')
                    }
                    
                    # Check if product exists
                    existing_id = product.get('id')
                    product_name = product.get('name', '')
                    
                    if existing_id:
                        existing_product = Product.get_product_by_id(existing_id)
                    else:
                        existing_product = None
                        
                    if not existing_product and product_name:
                        # Try to find by name
                        existing_product = Product.get_product_by_name(product_name)
                        
                    # Update or create product
                    if existing_product and update_existing:
                        # Update existing product
                        product_id = existing_product['id']
                        Product.update_product(product_id, **product_data)
                        updated_count += 1
                    else:
                        # Create new product
                        product_id = Product.add_product(**product_data)
                        imported_count += 1
                    
                    # Process variants for this product
                    if has_variants and product_id:
                        # Filter variants for this product
                        product_variants = []
                        for variant in variants_data:
                            if (variant.get('product_id') == str(existing_id) or 
                                variant.get('product_name') == product_name):
                                product_variants.append(variant)
                                
                        # Add variants
                        for variant in product_variants:
                            try:
                                # Parse attribute values
                                attr_values_json = variant.get('attribute_values', '{}')
                                try:
                                    attr_values = json.loads(attr_values_json)
                                except:
                                    attr_values = {}
                                    
                                # Convert numeric values
                                try:
                                    price_adj = float(variant.get('price_adjustment', 0))
                                except (ValueError, TypeError):
                                    price_adj = 0
                                    
                                try:
                                    stock = int(variant.get('stock', 0))
                                except (ValueError, TypeError):
                                    stock = 0
                                
                                # Add variant to product
                                variant_data = {
                                    'name': variant.get('variant_name', ''),
                                    'sku': variant.get('sku', ''),
                                    'barcode': variant.get('barcode', ''),
                                    'price_adjustment': price_adj,
                                    'stock': stock,
                                    'attribute_values': json.dumps(attr_values)
                                }
                                
                                # Add variant
                                Product.add_variant(product_id, **variant_data)
                                
                            except Exception as e:
                                print(f"Error adding variant {variant.get('variant_name', '')} to product {product_name}: {e}")
                                failed_count += 1
                    
                except Exception as e:
                    print(f"Error importing product {product.get('name', '')}: {e}")
                    failed_count += 1
                    
            self.import_progress.setValue(100)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Importation terminée", 
                f"Importation terminée avec succès:\n\n"
                f"{imported_count} produits importés\n"
                f"{updated_count} produits mis à jour\n"
                f"{failed_count} erreurs\n\n"
                f"{len(variants_data)} variantes traitées"
            )
            
            # Hide progress after a delay
            QTimer.singleShot(2000, lambda: self.import_progress.setVisible(False))
            
        except Exception as e:
            self.import_progress.setVisible(False)
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'importation: {str(e)}")
