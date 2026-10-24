from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt
from src.core.settings_page.sections.section_base import SettingsSection
from src.utils.theme_manager import theme_manager


class AppSettingsSection(SettingsSection):
    def __init__(self):
        super().__init__("Application Settings")

        self.auto_update = QCheckBox("Enable auto updates")
        self.dark_mode = QCheckBox("Enable dark mode")
        self.confirm_exit = QCheckBox("Confirm before exit")

        self.layout.addWidget(self.auto_update)
        self.layout.addWidget(self.dark_mode)
        self.layout.addWidget(self.confirm_exit)

        # Sync checkbox to reflect the current active theme (e.g. loaded from settings)
        self.dark_mode.setChecked(theme_manager.is_dark())

        # Wire checkbox → theme manager (stateChanged emits int: 0=unchecked, 2=checked)
        self.dark_mode.stateChanged.connect(self._on_dark_mode_changed)

        # Keep the checkbox in sync if theme is changed from elsewhere (e.g. toolbar toggle)
        theme_manager.theme_changed.connect(self._on_external_theme_changed)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _on_dark_mode_changed(self, state: int):
        """User toggled the dark-mode checkbox → switch theme."""
        new_theme = "dark" if state == Qt.CheckState.Checked.value else "light"
        # Avoid emitting theme_changed if theme is already correct
        if theme_manager.current_theme() != new_theme:
            theme_manager.set_theme(new_theme)

    def _on_external_theme_changed(self, theme_name: str):
        """External theme change (e.g. toolbar toggle) → keep checkbox in sync."""
        # Block signals so we don't trigger _on_dark_mode_changed recursively
        self.dark_mode.blockSignals(True)
        self.dark_mode.setChecked(theme_name == "dark")
        self.dark_mode.blockSignals(False)

    # ------------------------------------------------------------------
    # SettingsSection interface
    # ------------------------------------------------------------------

    def get_settings(self) -> dict:
        """Return the current app-settings values as a dict."""
        return {
            "theme": "dark" if self.dark_mode.isChecked() else "light",
            "dark_mode": self.dark_mode.isChecked(),
            "auto_update": self.auto_update.isChecked(),
            "confirm_exit": self.confirm_exit.isChecked(),
        }

    def load_settings(self, data: dict):
        """Populate controls from saved settings dict."""
        if not data:
            return

        # Apply theme without triggering save logic
        saved_theme = data.get("theme", "dark" if data.get("dark_mode", False) else "light")
        self.dark_mode.blockSignals(True)
        self.dark_mode.setChecked(saved_theme == "dark")
        self.dark_mode.blockSignals(False)

        self.auto_update.setChecked(bool(data.get("auto_update", False)))
        self.confirm_exit.setChecked(bool(data.get("confirm_exit", False)))
