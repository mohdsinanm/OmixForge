"""Centralized Theme Management System for OmixForge.

Provides single-source-of-truth theme tokens, QPalette configuration,
QSS stylesheet generation, dynamic theme switching, and persistence.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QPalette, QIcon
from PyQt6.QtWidgets import QApplication

from src.utils.resource import resource_path
from src.utils.constants import CONFIG_FILE, CONFIG_DIR
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()


@dataclass(frozen=True)
class ThemeTokens:
    """Design tokens for an application theme."""
    name: str

    # Backgrounds
    main_bg: str
    primary_content_bg: str
    secondary_surface_bg: str
    elevated_card_bg: str
    input_bg: str
    header_bg: str
    hover_bg: str
    subtle_surface_bg: str

    # Text
    text_primary: str
    text_secondary: str
    text_disabled: str
    text_placeholder: str
    text_heading: str

    # Borders & Dividers
    border_standard: str
    border_divider: str
    border_focus: str
    border_handle: str
    border_handle_hover: str

    # Interactive & Accents
    accent_primary: str
    accent_hover: str
    accent_pressed: str
    accent_fg: str
    selection_bg: str
    selection_fg: str
    focus_indicator: str

    # Status Colors (Text / Accents)
    success: str
    success_bg: str
    success_border: str
    warning: str
    warning_bg: str
    warning_border: str
    error: str
    error_bg: str
    error_border: str
    info: str
    info_bg: str
    info_border: str

    # Status Badges
    badge_neutral_bg: str
    badge_neutral_fg: str
    badge_neutral_border: str

    # Scrollbars
    scrollbar_track: str
    scrollbar_handle: str
    scrollbar_handle_hover: str

    # Buttons
    btn_default_bg: str
    btn_default_border: str
    btn_default_fg: str
    btn_default_hover_bg: str
    btn_default_hover_border: str
    btn_default_pressed_bg: str
    btn_default_disabled_bg: str
    btn_default_disabled_border: str
    btn_default_disabled_fg: str

    btn_primary_bg: str
    btn_primary_border: str
    btn_primary_fg: str
    btn_primary_hover_bg: str
    btn_primary_pressed_bg: str
    btn_primary_disabled_bg: str
    btn_primary_disabled_fg: str

    btn_destructive_hover_bg: str
    btn_destructive_hover_border: str
    btn_destructive_hover_fg: str

    # Navigation & Toolbars
    nav_bg: str
    nav_item_fg: str
    nav_item_hover_bg: str
    nav_item_hover_fg: str
    nav_item_selected_bg: str
    nav_item_selected_fg: str
    nav_item_selected_border: str
    nav_header_fg: str
    toolbar_bg: str
    toolbar_border: str

    # Tabs
    tab_bg: str
    tab_border: str
    tab_fg: str
    tab_selected_bg: str
    tab_selected_fg: str
    tab_selected_border: str
    tab_hover_bg: str
    tab_hover_fg: str

    # Tables / Trees / Lists
    table_bg: str
    table_alt_bg: str
    table_grid: str
    table_header_bg: str
    table_header_fg: str

    # Tooltips & Menus
    tooltip_bg: str
    tooltip_border: str
    tooltip_fg: str
    menu_bg: str
    menu_border: str
    menu_item_hover_bg: str
    menu_item_hover_fg: str


LIGHT_TOKENS = ThemeTokens(
    name="light",

    # Backgrounds
    main_bg="#f3f7f6",
    primary_content_bg="#ffffff",
    secondary_surface_bg="#eaf1ee",
    elevated_card_bg="#ffffff",
    input_bg="#ffffff",
    header_bg="#edf3f1",
    hover_bg="#edf6f3",
    subtle_surface_bg="#f7faf9",

    # Text
    text_primary="#263b36",
    text_secondary="#536a63",
    text_disabled="#95a49f",
    text_placeholder="#71847d",
    text_heading="#193b34",

    # Borders & Dividers
    border_standard="#cbdad5",
    border_divider="#dbe6e2",
    border_focus="#111111",
    border_handle="#dbe6e2",
    border_handle_hover="#111111",

    # Interactive & Accents
    accent_primary="#111111",
    accent_hover="#292929",
    accent_pressed="#000000",
    accent_fg="#ffffff",
    selection_bg="#dfe7e4",
    selection_fg="#263b36",
    focus_indicator="#111111",

    # Status Colors
    success="#187b58",
    success_bg="#e5f3eb",
    success_border="#19825c",
    warning="#b87718",
    warning_bg="#fff3df",
    warning_border="#b87718",
    error="#be5540",
    error_bg="#fcebe8",
    error_border="#be5540",
    info="#49617d",
    info_bg="#e8eef8",
    info_border="#49617d",

    # Status Badges
    badge_neutral_bg="#edf1ef",
    badge_neutral_fg="#657a73",
    badge_neutral_border="#778780",

    # Scrollbars
    scrollbar_track="transparent",
    scrollbar_handle="#c6d5d0",
    scrollbar_handle_hover="#9db9b0",

    # Buttons
    btn_default_bg="#ffffff",
    btn_default_border="#cbdad5",
    btn_default_fg="#31564c",
    btn_default_hover_bg="#edf6f3",
    btn_default_hover_border="#7a8580",
    btn_default_pressed_bg="#dceee8",
    btn_default_disabled_bg="#edf1ef",
    btn_default_disabled_border="#d8e0dd",
    btn_default_disabled_fg="#95a49f",

    btn_primary_bg="#111111",
    btn_primary_border="#111111",
    btn_primary_fg="#ffffff",
    btn_primary_hover_bg="#292929",
    btn_primary_pressed_bg="#000000",
    btn_primary_disabled_bg="#555555",
    btn_primary_disabled_fg="#d0d0d0",

    btn_destructive_hover_bg="#fcebe8",
    btn_destructive_hover_border="#db9a88",
    btn_destructive_hover_fg="#9f452d",

    # Navigation & Toolbars
    nav_bg="#eaf1ee",
    nav_item_fg="#536a63",
    nav_item_hover_bg="#e2e9e6",
    nav_item_hover_fg="#263b36",
    nav_item_selected_bg="#dfe7e4",
    nav_item_selected_fg="#263b36",
    nav_item_selected_border="#b45c32",
    nav_header_fg="#8a9a95",
    toolbar_bg="#eaf1ee",
    toolbar_border="#d8e3df",

    # Tabs
    tab_bg="#e7efec",
    tab_border="#dbe6e2",
    tab_fg="#657a73",
    tab_selected_bg="#ffffff",
    tab_selected_fg="#111111",
    tab_selected_border="#111111",
    tab_hover_bg="#dce9e5",
    tab_hover_fg="#284b42",

    # Tables / Trees / Lists
    table_bg="#ffffff",
    table_alt_bg="#f5f9f7",
    table_grid="#e7eeeb",
    table_header_bg="#edf3f1",
    table_header_fg="#536a63",

    # Tooltips & Menus
    tooltip_bg="#203a34",
    tooltip_border="#203a34",
    tooltip_fg="#ffffff",
    menu_bg="#ffffff",
    menu_border="#dbe6e2",
    menu_item_hover_bg="#e4f1ec",
    menu_item_hover_fg="#292929",
)


DARK_TOKENS = ThemeTokens(
    name="dark",

    # Backgrounds
    main_bg="#121212",
    primary_content_bg="#181818",
    secondary_surface_bg="#202020",
    elevated_card_bg="#242424",
    input_bg="#1E1E1E",
    header_bg="#202020",
    hover_bg="#282828",
    subtle_surface_bg="#1A1A1A",

    # Text
    text_primary="#F5F5F5",
    text_secondary="#B3B3B3",
    text_disabled="#777777",
    text_placeholder="#888888",
    text_heading="#F5F5F5",

    # Borders & Dividers
    border_standard="#383838",
    border_divider="#2D2D2D",
    border_focus="#80CBC4",
    border_handle="#383838",
    border_handle_hover="#80CBC4",

    # Interactive & Accents
    accent_primary="#80CBC4",
    accent_hover="#A0DDD6",
    accent_pressed="#5FB5AA",
    accent_fg="#121212",
    selection_bg="#315D59",
    selection_fg="#FFFFFF",
    focus_indicator="#80CBC4",

    # Status Colors
    success="#81C784",
    success_bg="#173024",
    success_border="#2a5540",
    warning="#FFCC80",
    warning_bg="#332712",
    warning_border="#5c431b",
    error="#EF9A9A",
    error_bg="#331919",
    error_border="#5c2a2a",
    info="#90CAF9",
    info_bg="#15273b",
    info_border="#254569",

    # Status Badges
    badge_neutral_bg="#2c2c2c",
    badge_neutral_fg="#B3B3B3",
    badge_neutral_border="#404040",

    # Scrollbars
    scrollbar_track="transparent",
    scrollbar_handle="#383838",
    scrollbar_handle_hover="#505050",

    # Buttons
    btn_default_bg="#242424",
    btn_default_border="#383838",
    btn_default_fg="#F5F5F5",
    btn_default_hover_bg="#2e2e2e",
    btn_default_hover_border="#555555",
    btn_default_pressed_bg="#1e1e1e",
    btn_default_disabled_bg="#181818",
    btn_default_disabled_border="#2c2c2c",
    btn_default_disabled_fg="#777777",

    btn_primary_bg="#80CBC4",
    btn_primary_border="#80CBC4",
    btn_primary_fg="#121212",
    btn_primary_hover_bg="#A0DDD6",
    btn_primary_pressed_bg="#5FB5AA",
    btn_primary_disabled_bg="#253a37",
    btn_primary_disabled_fg="#567571",

    btn_destructive_hover_bg="#381b1b",
    btn_destructive_hover_border="#663030",
    btn_destructive_hover_fg="#EF9A9A",

    # Navigation & Toolbars
    nav_bg="#181818",
    nav_item_fg="#B3B3B3",
    nav_item_hover_bg="#242424",
    nav_item_hover_fg="#F5F5F5",
    nav_item_selected_bg="#263331",
    nav_item_selected_fg="#80CBC4",
    nav_item_selected_border="#80CBC4",
    nav_header_fg="#777777",
    toolbar_bg="#181818",
    toolbar_border="#2D2D2D",

    # Tabs
    tab_bg="#202020",
    tab_border="#383838",
    tab_fg="#B3B3B3",
    tab_selected_bg="#181818",
    tab_selected_fg="#80CBC4",
    tab_selected_border="#80CBC4",
    tab_hover_bg="#282828",
    tab_hover_fg="#F5F5F5",

    # Tables / Trees / Lists
    table_bg="#181818",
    table_alt_bg="#202020",
    table_grid="#2D2D2D",
    table_header_bg="#202020",
    table_header_fg="#B3B3B3",

    # Tooltips & Menus
    tooltip_bg="#242424",
    tooltip_border="#383838",
    tooltip_fg="#F5F5F5",
    menu_bg="#202020",
    menu_border="#383838",
    menu_item_hover_bg="#2b3a37",
    menu_item_hover_fg="#80CBC4",
)


class ThemeManager(QObject):
    """Central manager for application-wide theme state, palettes, and styles."""

    theme_changed = pyqtSignal(str)

    _instance: Optional["ThemeManager"] = None

    def __init__(self):
        super().__init__()
        self._current_theme_name: str = "light"
        self._palettes: Dict[str, ThemeTokens] = {
            "light": LIGHT_TOKENS,
            "dark": DARK_TOKENS,
        }

    @classmethod
    def instance(cls) -> "ThemeManager":
        """Get the singleton ThemeManager instance."""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def current_theme(self) -> str:
        """Return the active theme name ('light' or 'dark')."""
        return self._current_theme_name

    def is_dark(self) -> bool:
        """Return True if dark theme is currently active."""
        return self._current_theme_name == "dark"

    def get_tokens(self, theme_name: Optional[str] = None) -> ThemeTokens:
        """Return design tokens for the given or current theme."""
        name = theme_name or self._current_theme_name
        return self._palettes.get(name, LIGHT_TOKENS)

    def get_color(self, token_name: str, theme_name: Optional[str] = None) -> str:
        """Return hex color value for a token name."""
        tokens = self.get_tokens(theme_name)
        return getattr(tokens, token_name, "#ffffff")

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes."""
        target = "light" if self.is_dark() else "dark"
        self.set_theme(target)
        return target

    def set_theme(self, theme_name: str, save_preference: bool = True):
        """Switch application theme to 'light' or 'dark' dynamically."""
        theme_name = theme_name.lower().strip()
        if theme_name not in ("light", "dark"):
            logger.warning(f"Unknown theme '{theme_name}', defaulting to 'light'")
            theme_name = "light"

        self._current_theme_name = theme_name

        # Update QApplication palette and stylesheet if available
        app = QApplication.instance()
        if app is not None:
            app.setPalette(self.get_palette(theme_name))
            app.setStyleSheet(self.get_stylesheet(theme_name))

        if save_preference:
            self.save_theme(theme_name)

        logger.info(f"Theme switched to: {theme_name}")
        self.theme_changed.emit(theme_name)

    def get_palette(self, theme_name: Optional[str] = None) -> QPalette:
        """Generate a Qt QPalette matching the theme tokens."""
        tokens = self.get_tokens(theme_name)
        palette = QPalette()

        if tokens.name == "dark":
            palette.setColor(QPalette.ColorRole.Window, QColor(tokens.main_bg))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(tokens.text_primary))
            palette.setColor(QPalette.ColorRole.Base, QColor(tokens.primary_content_bg))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tokens.secondary_surface_bg))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(tokens.tooltip_bg))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(tokens.tooltip_fg))
            palette.setColor(QPalette.ColorRole.Text, QColor(tokens.text_primary))
            palette.setColor(QPalette.ColorRole.Button, QColor(tokens.btn_default_bg))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(tokens.text_primary))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Link, QColor(tokens.accent_primary))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens.selection_bg))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens.selection_fg))

            # Disabled group
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(tokens.text_disabled))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(tokens.text_disabled))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(tokens.text_disabled))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor("#223835"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(tokens.text_disabled))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(tokens.main_bg))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(tokens.text_primary))
            palette.setColor(QPalette.ColorRole.Base, QColor(tokens.primary_content_bg))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tokens.table_alt_bg))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(tokens.tooltip_bg))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(tokens.tooltip_fg))
            palette.setColor(QPalette.ColorRole.Text, QColor(tokens.text_primary))
            palette.setColor(QPalette.ColorRole.Button, QColor(tokens.btn_default_bg))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(tokens.btn_default_fg))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#19825c"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens.selection_bg))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens.selection_fg))

            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(tokens.text_disabled))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(tokens.text_disabled))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(tokens.text_disabled))

        return palette

    def get_stylesheet(self, theme_name: Optional[str] = None) -> str:
        """Generate comprehensive application-wide QSS for the specified theme."""
        t = self.get_tokens(theme_name)
        checkmark_svg = "checkmark_dark.svg" if t.name == "dark" else "checkmark.svg"
        checkmark_path = resource_path(f"src/assets/{checkmark_svg}").replace("\\", "/")
        if not os.path.exists(checkmark_path):
            checkmark_path = resource_path("src/assets/checkmark.svg").replace("\\", "/")

        return f"""
        /* === OmixForge {t.name.upper()} THEME STYLESHEET === */

        QWidget {{
            color: {t.text_primary};
            font-family: "Noto Sans";
            font-size: 13px;
        }}

        QMainWindow#mainWindow, QStackedWidget#mainPageStack {{
            background-color: {t.main_bg};
        }}

        QDialog, QMessageBox {{
            background-color: {t.secondary_surface_bg};
            color: {t.text_primary};
        }}

        /* Toolbars */
        QToolBar#mainToolbar {{
            background-color: {t.toolbar_bg};
            border: none;
            border-right: 1px solid {t.toolbar_border};
            border-bottom: 1px solid {t.toolbar_border};
            padding: 4px;
            spacing: 5px;
        }}

        QToolBar#mainToolbar QToolButton {{
            background: transparent;
            border: none;
            border-radius: 6px;
            padding: 8px;
        }}

        QToolBar#mainToolbar QToolButton:hover,
        QToolBar#mainToolbar QToolButton:checked {{
            background-color: {t.nav_item_selected_bg};
        }}

        QToolBar#sessionActionsToolbar {{
            background-color: {t.toolbar_bg};
            border: none;
            border-bottom: 1px solid {t.toolbar_border};
            padding: 4px;
            spacing: 4px;
        }}

        QPushButton#logoutButton, QPushButton#themeToggleButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            color: {t.text_primary};
            font-weight: 700;
            padding: 0;
        }}

        QPushButton#logoutButton:hover, QPushButton#themeToggleButton:hover {{
            background-color: {t.hover_bg};
            border-color: {t.border_standard};
        }}

        /* Sidebar Navigation */
        QDockWidget#navigationDock {{
            background-color: {t.nav_bg};
            border: none;
        }}

        QDockWidget#navigationDock::title {{
            background-color: {t.nav_bg};
            padding: 0;
        }}

        QListWidget#mainNavigation {{
            background-color: {t.nav_bg};
            border: none;
            outline: none;
            padding: 12px 8px;
        }}

        QListWidget#mainNavigation::item {{
            border-radius: 6px;
            color: {t.nav_item_fg};
            margin: 2px 0;
            min-height: 40px;
            padding: 0 11px;
        }}

        QListWidget#mainNavigation::item:hover {{
            background-color: {t.nav_item_hover_bg};
            color: {t.nav_item_hover_fg};
        }}

        QListWidget#mainNavigation::item:selected {{
            background-color: {t.nav_item_selected_bg};
            border-left: 3px solid {t.nav_item_selected_border};
            color: {t.nav_item_selected_fg};
            font-weight: 700;
        }}

        QListWidget#mainNavigation::item:disabled {{
            color: {t.nav_header_fg};
            font-size: 10px;
            font-weight: 700;
            min-height: 20px;
            padding: 12px 11px 0;
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {t.secondary_surface_bg};
            border-top: 1px solid {t.border_divider};
            color: {t.text_secondary};
        }}

        /* Standard Buttons */
        QPushButton {{
            background-color: {t.btn_default_bg};
            color: {t.btn_default_fg};
            border: 1px solid {t.btn_default_border};
            border-radius: 6px;
            padding: 8px 13px;
            font-size: 13px;
        }}

        QPushButton:hover {{
            background-color: {t.btn_default_hover_bg};
            border-color: {t.btn_default_hover_border};
        }}

        QPushButton:pressed {{
            background-color: {t.btn_default_pressed_bg};
        }}

        QPushButton:disabled {{
            color: {t.btn_default_disabled_fg};
            background-color: {t.btn_default_disabled_bg};
            border-color: {t.btn_default_disabled_border};
        }}

        /* Primary Action Buttons */
        QPushButton#fetchAccessionsButton,
        QPushButton#loginButton,
        QPushButton#saveSettingsButton,
        QPushButton#dashboardPrimaryButton,
        QPushButton#import_from_url,
        QPushButton#import_selected_pipeline,
        QPushButton#pipeline_run_btn,
        QPushButton#publicStartButton {{
            background-color: {t.btn_primary_bg};
            border: 1px solid {t.btn_primary_border};
            color: {t.btn_primary_fg};
            font-weight: 700;
        }}

        QPushButton#fetchAccessionsButton:hover,
        QPushButton#loginButton:hover,
        QPushButton#saveSettingsButton:hover,
        QPushButton#dashboardPrimaryButton:hover,
        QPushButton#import_from_url:hover,
        QPushButton#import_selected_pipeline:hover,
        QPushButton#pipeline_run_btn:hover,
        QPushButton#publicStartButton:hover {{
            background-color: {t.btn_primary_hover_bg};
            border-color: {t.btn_primary_hover_bg};
        }}

        QPushButton#fetchAccessionsButton:disabled,
        QPushButton#loginButton:disabled,
        QPushButton#saveSettingsButton:disabled,
        QPushButton#dashboardPrimaryButton:disabled,
        QPushButton#import_from_url:disabled,
        QPushButton#import_selected_pipeline:disabled,
        QPushButton#pipeline_run_btn:disabled,
        QPushButton#publicStartButton:disabled {{
            background-color: {t.btn_primary_disabled_bg};
            border-color: {t.btn_primary_disabled_bg};
            color: {t.btn_primary_disabled_fg};
        }}

        /* Input Controls */
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
        QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {{
            background-color: {t.input_bg};
            border: 1px solid {t.border_standard};
            border-radius: 6px;
            color: {t.text_primary};
            padding: 7px 9px;
            selection-background-color: {t.selection_bg};
            selection-color: {t.selection_fg};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {t.border_focus};
        }}

        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled,
        QComboBox:disabled, QSpinBox:disabled {{
            background-color: {t.btn_default_disabled_bg};
            color: {t.text_disabled};
            border-color: {t.btn_default_disabled_border};
        }}

        /* Checkboxes */
        QCheckBox {{
            color: {t.text_primary};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            background-color: {t.input_bg};
            border: 1px solid {t.border_standard};
            border-radius: 4px;
            height: 18px;
            width: 18px;
        }}

        QCheckBox::indicator:hover {{
            border-color: {t.border_focus};
        }}

        QCheckBox::indicator:checked {{
            background-color: {t.accent_primary};
            border-color: {t.accent_primary};
            image: url("{checkmark_path}");
        }}

        QCheckBox::indicator:disabled {{
            background-color: {t.btn_default_disabled_bg};
            border-color: {t.btn_default_disabled_border};
        }}

        /* Radio Buttons */
        QRadioButton {{
            color: {t.text_primary};
            spacing: 8px;
        }}

        QRadioButton::indicator {{
            background-color: {t.input_bg};
            border: 1px solid {t.border_standard};
            border-radius: 9px;
            height: 18px;
            width: 18px;
        }}

        QRadioButton::indicator:hover {{
            border-color: {t.border_focus};
        }}

        QRadioButton::indicator:checked {{
            background-color: {t.accent_primary};
            border-color: {t.accent_primary};
        }}

        /* Combo Box Popups */
        QComboBox::drop-down {{
            border: none;
            padding-right: 7px;
            width: 22px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {t.input_bg};
            border: 1px solid {t.border_standard};
            color: {t.text_primary};
            outline: none;
            selection-background-color: {t.selection_bg};
            selection-color: {t.selection_fg};
        }}

        QComboBox QAbstractItemView::item {{
            min-height: 24px;
            padding: 5px 8px;
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {t.selection_bg};
            color: {t.selection_fg};
        }}

        /* Lists and Views */
        QListWidget, QListView {{
            alternate-background-color: {t.table_alt_bg};
            background-color: {t.primary_content_bg};
            border: 1px solid {t.border_divider};
            border-radius: 6px;
            color: {t.text_primary};
            outline: none;
            selection-background-color: {t.selection_bg};
            selection-color: {t.selection_fg};
        }}

        QListWidget::item, QListView::item {{
            border-radius: 4px;
            padding: 7px 9px;
        }}

        QListWidget::item:selected, QListView::item:selected {{
            background-color: {t.selection_bg};
            color: {t.selection_fg};
        }}

        /* Content Containers & Scroll Areas */
        QWidget#enaDownloaderContent,
        QWidget#localPipelineScrollContent,
        QWidget#pluginStorePage,
        QWidget#pluginStoreTab,
        QWidget#pluginManageTab,
        QWidget[loadedPluginRoot="true"],
        QStackedWidget#loadedPluginStack,
        QWidget#runResultsScrollContent,
        QWidget#runStatusScrollContent,
        QScrollArea#runResultsScroll,
        QScrollArea#runStatusScroll,
        QScrollArea#pluginScrollArea,
        QWidget#pluginScrollAreaContent,
        QWidget#dashboardScrollContent {{
            background-color: {t.main_bg};
        }}

        QScrollArea {{
            background: transparent;
            border: none;
        }}

        QLabel#pipelineInfoLog, QLabel#runLogContent {{
            background-color: {t.primary_content_bg};
            color: {t.text_primary};
            border: 1px solid {t.border_divider};
            padding: 10px;
        }}

        QLabel#encryptedRunNotice {{
            background-color: {t.secondary_surface_bg};
            border-left: 3px solid {t.accent_primary};
            border-radius: 4px;
            color: {t.text_secondary};
            padding: 9px 11px;
        }}

        /* Cards */
        QFrame#pipelineCard {{
            background: {t.elevated_card_bg};
            border: 1px solid {t.border_divider};
            border-radius: 8px;
        }}

        QFrame#pipelineCard:hover {{
            background: {t.hover_bg};
            border-color: {t.border_handle_hover};
        }}

        QLabel#pipelineCardName {{
            color: {t.text_heading};
            font-size: 14px;
            font-weight: 700;
        }}

        QFrame#pipelineResultCard {{
            background-color: {t.elevated_card_bg};
            border: 1px solid {t.border_divider};
            border-left: 4px solid {t.badge_neutral_border};
            border-radius: 8px;
        }}

        QFrame#pipelineResultCard[state="completed"] {{
            border-left-color: {t.success_border};
        }}

        QFrame#pipelineResultCard[state="failed"] {{
            border-left-color: {t.error_border};
        }}

        QFrame#pipelineResultCard[state="cancelled"] {{
            border-left-color: {t.badge_neutral_border};
        }}

        QFrame#pipelineResultCard[state="running"] {{
            border-left-color: {t.warning_border};
        }}

        /* Status Badges */
        QLabel#resultStatusBadge {{
            background-color: {t.badge_neutral_bg};
            border-radius: 4px;
            color: {t.badge_neutral_fg};
            font-size: 11px;
            font-weight: 700;
            padding: 4px 8px;
        }}

        QLabel#resultStatusBadge[state="completed"] {{
            background-color: {t.success_bg};
            color: {t.success};
        }}

        QLabel#resultStatusBadge[state="failed"] {{
            background-color: {t.error_bg};
            color: {t.error};
        }}

        QLabel#resultStatusBadge[state="cancelled"] {{
            background-color: {t.badge_neutral_bg};
            color: {t.badge_neutral_fg};
        }}

        QLabel#resultStatusBadge[state="running"] {{
            background-color: {t.warning_bg};
            color: {t.warning};
        }}

        QLabel#resultStatusBadge[state="encrypted"] {{
            background-color: {t.info_bg};
            color: {t.info};
        }}

        /* Tabs */
        QTabWidget::pane {{
            background-color: {t.primary_content_bg};
            border: 1px solid {t.border_divider};
            border-radius: 8px;
            top: -1px;
        }}

        QTabBar::tab {{
            background-color: {t.tab_bg};
            border: 1px solid {t.tab_border};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            color: {t.tab_fg};
            margin-right: 4px;
            padding: 10px 15px;
        }}

        QTabBar::tab:selected {{
            background-color: {t.primary_content_bg};
            border-bottom: 2px solid {t.tab_selected_border};
            color: {t.tab_selected_fg};
            font-weight: 700;
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {t.tab_hover_bg};
            color: {t.tab_hover_fg};
        }}

        /* Group Boxes */
        QGroupBox {{
            background-color: {t.elevated_card_bg};
            border: 1px solid {t.border_divider};
            border-radius: 8px;
            margin-top: 12px;
            padding: 14px 12px 10px;
        }}

        QGroupBox::title {{
            color: {t.text_heading};
            left: 10px;
            padding: 0 5px;
        }}

        /* Tables and Trees */
        QTableWidget, QTableView, QTreeWidget, QTreeView {{
            alternate-background-color: {t.table_alt_bg};
            background-color: {t.table_bg};
            border: 1px solid {t.border_divider};
            border-radius: 6px;
            gridline-color: {t.table_grid};
            selection-background-color: {t.selection_bg};
            selection-color: {t.selection_fg};
            color: {t.text_primary};
        }}

        QHeaderView::section {{
            background-color: {t.table_header_bg};
            border: none;
            border-bottom: 1px solid {t.border_divider};
            color: {t.table_header_fg};
            font-weight: 700;
            padding: 8px;
        }}

        QHeaderView {{
            background-color: {t.table_header_bg};
        }}

        QTableCornerButton::section {{
            background-color: {t.table_header_bg};
            border: none;
            border-bottom: 1px solid {t.border_divider};
        }}

        /* Splitters */
        QSplitter::handle {{
            background-color: {t.border_handle};
        }}

        QSplitter::handle:hover {{
            background-color: {t.border_handle_hover};
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            background: {t.scrollbar_track};
            margin: 2px;
            width: 10px;
        }}

        QScrollBar:horizontal {{
            background: {t.scrollbar_track};
            height: 10px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {t.scrollbar_handle};
            border-radius: 4px;
            min-height: 24px;
            min-width: 24px;
        }}

        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
            background: {t.scrollbar_handle_hover};
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            background: none;
            border: none;
        }}

        /* Progress Bar */
        QProgressBar {{
            background-color: {t.secondary_surface_bg};
            border: 1px solid {t.border_divider};
            border-radius: 5px;
            color: {t.text_primary};
            min-height: 10px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {t.accent_primary};
            border-radius: 4px;
        }}

        /* Tooltip */
        QToolTip {{
            background-color: {t.tooltip_bg};
            border: 1px solid {t.tooltip_border};
            color: {t.tooltip_fg};
            padding: 5px 7px;
        }}

        /* Menus */
        QMenu {{
            background-color: {t.menu_bg};
            border: 1px solid {t.menu_border};
            color: {t.text_primary};
            padding: 4px;
        }}

        QMenu::item {{
            border-radius: 4px;
            padding: 7px 22px;
        }}

        QMenu::item:selected {{
            background-color: {t.menu_item_hover_bg};
            color: {t.menu_item_hover_fg};
        }}

        /* Empty States and Detail Panes */
        QLabel#dashboardEmptyState {{
            background: {t.subtle_surface_bg};
            border: 1px dashed {t.border_standard};
            border-radius: 8px;
            color: {t.text_placeholder};
            padding: 28px;
        }}

        QFrame#pipeline_info_box, QFrame#pipelineEditorDetails, QFrame#pipelineImportDetails {{
            background: {t.subtle_surface_bg};
            border: 1px solid {t.border_divider};
            border-radius: 8px;
            color: {t.text_primary};
        }}

        QWidget#pipelineImportDetailsContent {{
            background: {t.subtle_surface_bg};
            color: {t.text_primary};
        }}

        QLabel#pipeline_import_status {{
            background: {t.secondary_surface_bg};
            border-left: 3px solid {t.accent_primary};
            border-radius: 4px;
            color: {t.text_heading};
            padding: 9px 11px;
        }}

        QLabel#dashboardCount {{
            color: {t.warning};
            font-size: 12px;
            font-weight: 700;
        }}
        """

    def get_icon(self, icon_name: str, theme_name: Optional[str] = None) -> QIcon:
        """Return a QIcon tailored to the theme for visibility."""
        is_dark_mode = (theme_name or self._current_theme_name) == "dark"

        variant_map = {
            "lock": "lock_dark.svg" if is_dark_mode else "lock_light.svg",
            "logout": "logout_dark.svg" if is_dark_mode else "logout_light.svg",
            "theme": "sun.svg" if is_dark_mode else "moon.svg",
        }

        filename = variant_map.get(icon_name)
        if filename:
            path = resource_path(f"src/assets/{filename}")
            if os.path.exists(path):
                return QIcon(path)

        # Fallback to base asset
        fallback_path = resource_path(f"src/assets/{icon_name}.svg")
        if os.path.exists(fallback_path):
            return QIcon(fallback_path)
        png_path = resource_path(f"src/assets/{icon_name}.png")
        if os.path.exists(png_path):
            return QIcon(png_path)

        return QIcon()

    def get_svg_path(self, asset_name: str, theme_name: Optional[str] = None) -> str:
        """Return the filesystem path to an SVG asset matching the active theme."""
        is_dark_mode = (theme_name or self._current_theme_name) == "dark"

        if asset_name == "startup_bioinformatics":
            filename = "startup_bioinformatics_dark.svg" if is_dark_mode else "startup_bioinformatics.svg"
            path = resource_path(f"src/assets/{filename}")
            if os.path.exists(path):
                return path

        if asset_name == "lock":
            filename = "lock_dark.svg" if is_dark_mode else "lock_light.svg"
            path = resource_path(f"src/assets/{filename}")
            if os.path.exists(path):
                return path

        return resource_path(f"src/assets/{asset_name}.svg")

    def load_saved_theme(self) -> str:
        """Load the user's persisted theme preference (defaults to 'light')."""
        # 1. Try QSettings first
        try:
            settings = QSettings("OmixForge", "OmixForge")
            saved = settings.value("app/theme", None)
            if saved in ("light", "dark"):
                self._current_theme_name = saved
                return saved
            dark_flag = settings.value("app/dark_mode", None)
            if dark_flag is not None:
                is_dark = str(dark_flag).lower() in ("true", "1")
                theme = "dark" if is_dark else "light"
                self._current_theme_name = theme
                return theme
        except Exception as e:
            logger.debug(f"Could not read theme from QSettings: {e}")

        # 2. Try app.config
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    app_cfg = data.get("app", {})
                    if "theme" in app_cfg and app_cfg["theme"] in ("light", "dark"):
                        self._current_theme_name = app_cfg["theme"]
                        return app_cfg["theme"]
                    if "dark_mode" in app_cfg:
                        theme = "dark" if app_cfg["dark_mode"] else "light"
                        self._current_theme_name = theme
                        return theme
        except Exception as e:
            logger.debug(f"Could not read theme from app.config: {e}")

        self._current_theme_name = "light"
        return "light"

    def save_theme(self, theme_name: str):
        """Persist the chosen theme to QSettings and app.config safely."""
        # 1. Persist to QSettings
        try:
            settings = QSettings("OmixForge", "OmixForge")
            settings.setValue("app/theme", theme_name)
            settings.setValue("app/dark_mode", theme_name == "dark")
            settings.sync()
        except Exception as e:
            logger.warning(f"Could not persist theme to QSettings: {e}")

        # 2. Persist to app.config if directory/file is accessible
        try:
            config_data = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as f:
                        config_data = json.load(f)
                except Exception:
                    config_data = {}

            if not isinstance(config_data, dict):
                config_data = {}

            app_section = config_data.get("app", {})
            if not isinstance(app_section, dict):
                app_section = {}

            app_section["theme"] = theme_name
            app_section["dark_mode"] = (theme_name == "dark")
            config_data["app"] = app_section

            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            logger.debug(f"Could not persist theme to app.config: {e}")


# Global convenience singleton instance
theme_manager = ThemeManager.instance()
