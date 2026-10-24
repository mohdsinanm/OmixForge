from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.utils.theme_manager import theme_manager


class PageHeader(QWidget):
    """Shared page title styled to match the pipeline dashboard header."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardHeader")

        header_layout = QHBoxLayout(self)
        header_layout.setContentsMargins(2, 0, 2, 2)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("dashboardTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._on_theme_changed(theme_manager.current_theme())

    def set_title(self, title: str):
        self.title_label.setText(title)

    def _on_theme_changed(self, _theme_name: str):
        tokens = theme_manager.get_tokens()
        self.title_label.setStyleSheet(
            f"color: {tokens.text_heading}; font-size: 23px; font-weight: 700;"
        )