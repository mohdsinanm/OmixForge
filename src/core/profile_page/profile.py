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
from src.utils.theme_manager import theme_manager


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
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        """Update profile page styling when theme changes."""
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
            err_color = theme_manager.get_color("error")
            self.username_input.setStyleSheet(f"border: 1px solid {err_color};")
            self.password_input.setStyleSheet(f"border: 1px solid {err_color};")
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
        t = theme_manager.get_tokens()
        return f"""
        QWidget {{
            background-color: {t.main_bg};
            color: {t.text_primary};
            font-family: "Noto Sans";
        }}

        QFrame#loginCard {{
            background-color: {t.elevated_card_bg};
            border-radius: 8px;
            padding: 20px;
            border: 1px solid {t.border_divider};
        }}

        QLabel#loginTitle {{
            color: {t.text_heading};
            font-size: 22px;
            font-weight: 700;
            background: transparent;
        }}

        QLabel#loginSubtitle {{
            color: {t.text_secondary};
            font-size: 14px;
            margin-bottom: 12px;
            background: transparent;
        }}

        QLineEdit#inputField {{
            background-color: {t.input_bg};
            padding: 10px 12px;
            border-radius: 6px;
            border: 1px solid {t.border_standard};
            font-size: 14px;
            color: {t.text_primary};
        }}
        QLineEdit#inputField:focus {{
            border: 1px solid {t.border_focus};
        }}

        QPushButton#loginButton {{
            padding: 12px;
            background-color: {t.btn_primary_bg};
            color: {t.btn_primary_fg};
            border: 1px solid {t.btn_primary_border};
            border-radius: 6px;
            font-size: 15px;
            font-weight: 700;
        }}
        QPushButton#loginButton:hover {{
            background-color: {t.btn_primary_hover_bg};
            border-color: {t.btn_primary_hover_bg};
        }}
        QPushButton#loginButton:pressed {{
            background-color: {t.accent_pressed};
        }}

        QPushButton#backButton {{
            border: none;
            background: transparent;
            color: {t.accent_primary if t.name == "dark" else t.text_primary};
            font-size: 14px;
            padding: 6px;
        }}
        QPushButton#backButton:hover {{
            text-decoration: underline;
            color: {t.accent_hover if t.name == "dark" else t.btn_primary_hover_bg};
        }}

        QLabel#loginError {{
            color: {t.error};
        }}
        """
