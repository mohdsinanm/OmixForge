from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)


class CredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Decrypt Pipeline")
        self.setModal(True)
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)

        # Username
        layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Buttons
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("Decrypt")

        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)

        layout.addLayout(buttons)

    def get_credentials(self):
        return (
            self.username_input.text().strip(),
            self.password_input.text()
        )
