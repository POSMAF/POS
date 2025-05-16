"""
Variant Dashboard Integration Module

This module adds a "Manage Variants" button to the product management screen
that opens the variant dashboard for the selected product.

To use this integration:
1. Import this module in your product_management_window.py file
2. Call the add_variants_button function with your product management window instance
"""

from PyQt5.QtWidgets import QPushButton, QMessageBox
from PyQt5.QtCore import Qt

def add_variants_button(product_management_window):
    """
    Add a "Manage Variants" button to the product management window
    
    Args:
        product_management_window: The ProductManagementWindow instance
    """
    # Check if the button already exists
    if hasattr(product_management_window, 'manage_variants_btn'):
        return
    
    # Create the button
    manage_variants_btn = QPushButton("🧩 Gérer les variantes")
    manage_variants_btn.setStyleSheet("""
        QPushButton {
            background-color: #5e72e4;
            color: white;
            font-weight: bold;
            padding: 8px 15px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #324cdd;
        }
    """)
    
    # Add button to the layout
    # This is a best guess - you might need to adjust this based on your layout
    try:
        # Try to find the button layout
        for i in range(product_management_window.layout().count()):
            item = product_management_window.layout().itemAt(i)
            if item.layout() and any(isinstance(item.layout().itemAt(j).widget(), QPushButton) 
                                    for j in range(item.layout().count()) if item.layout().itemAt(j).widget()):
                item.layout().addWidget(manage_variants_btn)
                break
        else:
            # If we couldn't find a suitable layout, add to the main layout
            product_management_window.layout().addWidget(manage_variants_btn)
    except Exception as e:
        print(f"Error adding variants button: {e}")
        # Try a different approach
        try:
            # Find the toolbar if it exists
            toolbar = next((w for w in product_management_window.findChildren(QWidget) 
                            if hasattr(w, 'addAction') and hasattr(w, 'addWidget')), None)
            
            if toolbar:
                toolbar.addWidget(manage_variants_btn)
            else:
                # Last resort: add to main layout
                product_management_window.layout().addWidget(manage_variants_btn)
        except Exception as e2:
            print(f"Error adding variants button (second attempt): {e2}")
    
    # Connect button click event
    manage_variants_btn.clicked.connect(
        lambda: open_variant_dashboard(product_management_window)
    )
    
    # Store reference to the button
    product_management_window.manage_variants_btn = manage_variants_btn

def open_variant_dashboard(product_management_window):
    """
    Open the variant dashboard for the selected product
    
    Args:
        product_management_window: The ProductManagementWindow instance
    """
    # Get the selected product
    selected_product = None
    
    # Try to get the selected product from the table
    try:
        if hasattr(product_management_window, 'products_table'):
            table = product_management_window.products_table
            selected_rows = table.selectedItems()
            
            if selected_rows:
                # Get the product ID from the first column
                row = selected_rows[0].row()
                product_id_item = table.item(row, 0)
                
                if product_id_item:
                    product_id = product_id_item.text()
                    
                    # Get the product data
                    from models.product import Product
                    selected_product = {'id': int(product_id)}
            
            if not selected_product:
                QMessageBox.warning(
                    product_management_window,
                    "Aucun produit sélectionné",
                    "Veuillez sélectionner un produit dans la liste pour gérer ses variantes."
                )
                return
            
            # Open the variant dashboard
            open_dashboard_for_product(int(selected_product['id']), product_management_window)
        else:
            QMessageBox.warning(
                product_management_window,
                "Table de produits non trouvée",
                "Impossible de trouver la table des produits."
            )
    except Exception as e:
        print(f"Error opening variant dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        QMessageBox.critical(
            product_management_window,
            "Erreur",
            f"Une erreur s'est produite lors de l'ouverture du tableau de bord des variantes: {str(e)}"
        )

def open_dashboard_for_product(product_id, parent=None):
    """
    Open the variant dashboard for a specific product
    
    Args:
        product_id: The product ID
        parent: The parent widget
    """
    try:
        from ui.variant_dashboard import VariantDashboard
        
        dashboard = VariantDashboard(product_id, parent)
        dashboard.exec_()
        
        # Reload the product list if available
        if parent and hasattr(parent, 'load_products'):
            parent.load_products()
    except Exception as e:
        print(f"Error opening dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        QMessageBox.critical(
            parent,
            "Erreur",
            f"Une erreur s'est produite lors de l'ouverture du tableau de bord: {str(e)}"
        )

# Add a simple function to directly open the dashboard from anywhere
def manage_variants_for_product(product_id, parent=None):
    """
    Open the variant dashboard for a product from anywhere in the code
    
    Args:
        product_id: The product ID
        parent: Optional parent widget
    """
    open_dashboard_for_product(product_id, parent)
