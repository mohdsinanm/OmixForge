from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel
)
from src.core.settings_page.sections.section_base import SettingsSection


class ServerConfigWidget(QWidget):
    def __init__(self, parent_section):
        super().__init__()
        self.parent_section = parent_section
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Name")
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("Host")
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("Port")
        self.port_edit.setText("")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Key Path")

        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse_key)
        remove = QPushButton("-")
        remove.clicked.connect(self.remove_self)

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Host:"))
        layout.addWidget(self.host_edit)
        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.port_edit)
        layout.addWidget(QLabel("User:"))
        layout.addWidget(self.username_edit)
        layout.addWidget(QLabel("Key:"))
        layout.addWidget(self.key_edit)
        layout.addWidget(browse)
        layout.addWidget(remove)

    def _browse_key(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select SSH Key")
        if path:
            self.key_edit.setText(path)

    def remove_self(self):
        self.parent_section.remove_server(self)

    def get_config(self):
        port_text = self.port_edit.text()
        port = int(port_text) if port_text else ""
        return {
            "name": self.name_edit.text().strip(),
            "host": self.host_edit.text().strip(),
            "port": port,
            "username": self.username_edit.text().strip(),
            "key_path": self.key_edit.text().strip()
        }


class ServerSettingsSection(SettingsSection):
    def __init__(self):
        super().__init__("Server Settings")
        self.servers = []

        self.add_button = QPushButton("+ Add Server")
        self.add_button.clicked.connect(self.add_server)
        self.layout.addWidget(self.add_button)

    def add_server(self):
        server = ServerConfigWidget(self)
        self.servers.append(server)
        self.layout.insertWidget(self.layout.count() - 1, server)

    def remove_server(self, server):
        if server in self.servers:
            self.servers.remove(server)
            self.layout.removeWidget(server)
            server.deleteLater()

    def get_settings(self):
        return [server.get_config() for server in self.servers]

    def load_settings(self, data):
        # data is list of dicts
        for server_data in data:
            self.add_server()
            server = self.servers[-1]
            server.name_edit.setText(server_data.get("name", ""))
            server.host_edit.setText(server_data.get("host", ""))
            server.port_edit.setText(str(server_data.get("port", "")))
            server.username_edit.setText(server_data.get("username", ""))
            server.key_edit.setText(server_data.get("key_path", ""))

        