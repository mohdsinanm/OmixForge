from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QApplication

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.profile_page.login import Login
from src.core.profile_page.signup import SignUp
from src.utils.encryption.handle import generate_encrypted_file, decrypt_file, generate_key
from src.utils.constants import AUTH_DIR ,  AUTH_JSON
from src.utils.fileops.file_handle import ensure_directory, file_exists
from src.utils.widgets.loading_spinner import LoadingSpinner


logger = OmixForgeLogger.get_logger()

import json

class ProfilePage(QWidget):
    login_success = pyqtSignal()
    go_back = pyqtSignal() 

    def __init__(self):
        """Initialize the profile page with login or signup form."""
        super().__init__()

        # MAIN CENTER LAYOUT
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        back_btn = QPushButton("← Back")
        back_btn.setObjectName("backButton")
        back_btn.setFixedWidth(80)
        back_btn.clicked.connect(self.go_back.emit)
        

        main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)


        if file_exists(AUTH_JSON):
            Login(main_layout, self)
        else:
            SignUp(main_layout, self)

        # Add loading spinner widget (initially hidden)
        self.loading_spinner = LoadingSpinner("Loading OmixForge...", parent=self)
        main_layout.addWidget(self.loading_spinner, alignment=Qt.AlignmentFlag.AlignCenter)


        self.setStyleSheet(self.stylesheet())

    def attempt_login(self):
        """Attempt to authenticate user with provided credentials."""
        app = QApplication.instance()
        
        try:
            if self.username_input.text() and self.password_input.text():
                cred = decrypt_file(
                    filepath = AUTH_JSON,
                    key = generate_key((f"{self.username_input.text()}:{self.password_input.text()}" )),
                    need_data=True) 
                app.cred = json.loads("{" + cred + "}")
                self.loading_spinner.start_loading()
                QTimer.singleShot(100, lambda: self.login_success.emit())  

        except Exception as e:
            logger.error(f"Failed to login {e}")
            self.login_error_label.setText("Invalid username or password")
            self.login_error_label.setVisible(True)
            self.username_input.setStyleSheet("border: 1px solid red;")
            self.password_input.setStyleSheet("border: 1px solid red;")
            return

    def attempt_signup(self):
        """Create a new user account with provided credentials."""
        if self.username_input.text() and self.password_input.text():
            ensure_directory(AUTH_DIR)
            generate_encrypted_file(
                data = f'"user":"{self.username_input.text()}","password":"{self.password_input.text()}"',
                filepath = AUTH_JSON,
                key = generate_key((f"{self.username_input.text()}:{self.password_input.text()}" ))) # Replace with your actual
            
            self.loading_spinner.start_loading()
            QTimer.singleShot(100, lambda: self.login_success.emit())
            
            logger.info("User signed up and encrypted auth file created.")
            

    def toggle_password(self):
        """Toggle password visibility in the input field."""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)




    
    # ----- MODERN STYLES -----
    def stylesheet(self):
        """Return CSS stylesheet for the profile page widget."""
        return """
        QWidget {
            background-color: #f3f7f6;
            color: #263b36;
            font-family: "Noto Sans";
        }

        QFrame#loginCard {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #dbe6e2;
        }

        QLabel#loginTitle {
            color: #193b34;
            font-size: 22px;
            font-weight: 700;
            background: transparent;
        }

        QLabel#loginSubtitle {
            color: #71847d;
            font-size: 14px;
            margin-bottom: 12px;
            background: transparent;
        }

        QLineEdit#inputField {
            background-color: #ffffff;
            padding: 10px 12px;
            border-radius: 6px;
            border: 1px solid #cbdad5;
            font-size: 14px;
            color: #263b36;
        }
        QLineEdit#inputField:focus {
            border: 1px solid #111111;
        }

        QPushButton#loginButton {
            padding: 12px;
            background-color: #111111;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-size: 15px;
            font-weight: 700;
        }
        QPushButton#loginButton:hover {
            background-color: #292929;
        }
        QPushButton#loginButton:pressed {
            background-color: #000000;
        }

        QPushButton#backButton {
            border: none;
            background: transparent;
            color: #111111;
            font-size: 14px;
            padding: 6px;
        }
        QPushButton#backButton:hover {
            text-decoration: underline;
            color: #292929;
        }

        QLabel#loginError {
            color: #b74f3b;
        }
        """
