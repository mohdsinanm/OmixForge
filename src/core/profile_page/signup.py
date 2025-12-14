from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame,
)
from PyQt6.QtCore import  Qt
from PyQt6.QtGui import QIcon, QAction


class SignUp():

    def __init__(self, main_layout, parent_page):
        self.parent = parent_page
        
        # CARD CONTAINER
        card = QFrame()
        card.setObjectName("loginCard")
        card.setMaximumWidth(360)
        card.setMinimumWidth(360)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(18)

        # --- TITLE ---
        title = QLabel("Hi, Omix Smith")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("loginTitle")
        card_layout.addWidget(title)

        subtitle = QLabel("Create an account to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("loginSubtitle")
        card_layout.addWidget(subtitle)

        # --- USERNAME ---
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setObjectName("inputField")
        card_layout.addWidget(self.username_input)

        # Register in parent
        self.parent.username_input = self.username_input

        # --- PASSWORD ---
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("inputField")

        # toggle password action
        toggle_action = QAction(QIcon(), "toggle", self.parent)
        toggle_action.triggered.connect(self.parent.toggle_password)
        self.password_input.addAction(toggle_action, QLineEdit.ActionPosition.TrailingPosition)

        card_layout.addWidget(self.password_input)

        # Register in parent
        self.parent.password_input = self.password_input

        # --- LOGIN BUTTON ---
        self.login_btn = QPushButton("Sign Up")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.clicked.connect(self.parent.attempt_signup)
        card_layout.addWidget(self.login_btn)

        main_layout.addWidget(card)

