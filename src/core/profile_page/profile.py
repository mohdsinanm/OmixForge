from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.profile_page.login import Login
from src.core.profile_page.signup import SignUp
from src.utils.encryption.handle import generate_encrypted_file, decrypt_file, generate_key
from src.utils.constants import AUTH_DIR ,  AUTH_JSON
from src.utils.fileops.file_handle import ensure_directory, file_exists


logger = OmixForgeLogger.get_logger()

import json

class ProfilePage(QWidget):
    login_success = pyqtSignal()
    go_back = pyqtSignal() 

    def __init__(self):
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


        self.setStyleSheet(self.stylesheet())

    def attempt_login(self):

        app = QApplication.instance()
        
        try:
            if self.username_input.text() and self.password_input.text():
                cred = decrypt_file(
                    filepath = AUTH_JSON,
                    key = generate_key((f"{self.username_input.text()}:{self.password_input.text()}" ))) 
                app.cred = json.loads("{" + cred + "}")

                self.login_success.emit()
        except Exception as e:
            logger.error(f"Failed to login {e}")
            self.login_error_label.setText("Invalid username or password")
            self.login_error_label.setVisible(True)
            self.username_input.setStyleSheet("border: 1px solid red;")
            self.password_input.setStyleSheet("border: 1px solid red;")
            return

    def attempt_signup(self):
        if self.username_input.text() and self.password_input.text():
            ensure_directory(AUTH_DIR)
            generate_encrypted_file(
                data = f'"user":"{self.username_input.text()}","password":"{self.password_input.text()}"',
                filepath = AUTH_JSON,
                key = generate_key((f"{self.username_input.text()}:{self.password_input.text()}" ))) # Replace with your actual
        
            self.login_success.emit()
            logger.info("User signed up and encrypted auth file created.")
            

    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)




    
    # ----- MODERN STYLES -----
    def stylesheet(self):
        return """
        QWidget {

            font-family: 'Segoe UI', sans-serif;
        }

        /* CARD */
        QFrame#loginCard {

            border-radius: 16px;
            padding: 20px;
            border: 1px solid #e4e4e4;
        }

        /* TITLE */
        QLabel#loginTitle {
            font-size: 22px;
            font-weight: bold;

        }

        QLabel#loginSubtitle {
            font-size: 14px;

            margin-bottom: 12px;
        }

        /* INPUT FIELDS */
        QLineEdit#inputField {
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid #c8c8c8;
            font-size: 14px;
            color: black;

        }
        QLineEdit#inputField:focus {
            border: 1px solid #448aff;
            color: black;

        }

        /* LOGIN BUTTON */
        QPushButton#loginButton {
            padding: 12px;
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton#loginButton:hover {
            background-color: #3f7fcc;
        }
        QPushButton#loginButton:pressed {
            background-color: #346db3;
        }

        QPushButton#backButton {
            border: none;
            background: transparent;
            color: #4a90e2;
            font-size: 14px;
            padding: 6px;
        }
        QPushButton#backButton:hover {
            text-decoration: underline;
            color: #3577c8;
        }
        """
