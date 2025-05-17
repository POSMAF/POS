from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
# Remove circular import
# from ui.dashboard_window import DashboardWindow

class LoginWindow(QWidget):
    def __init__(self, auth_controller=None):
        super().__init__()
        self.auth_controller = auth_controller
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MarocPOS - Login")
        self.setGeometry(100, 100, 400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                margin-bottom: 10px;
            }
            QPushButton {
                padding: 12px;
                background-color: #24786d;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1e6459;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Logo and title
        logo_layout = QHBoxLayout()
        logo_label = QLabel("MarocPOS")
        logo_label.setFont(QFont("Arial", 24, QFont.Bold))
        logo_label.setStyleSheet("color: #24786d;")
        logo_layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        main_layout.addLayout(logo_layout)

        # Login form
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)

        # Username
        username_label = QLabel("Nom d'utilisateur")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Entrez votre nom d'utilisateur")
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Mot de passe")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Entrez votre mot de passe")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Se connecter")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.handle_login)
        form_layout.addWidget(self.login_button)

        main_layout.addWidget(form_frame)
        self.setLayout(main_layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs!")
            return

        user = self.auth_controller.login(username, password)
        if user:
            # Use lazy import to avoid circular dependency
            from ui.dashboard_window import DashboardWindow
            self.dashboard = DashboardWindow(user=user)
            self.dashboard.show()
            self.close()
        else:
            QMessageBox.warning(self, "Erreur", "Identifiants invalides!")