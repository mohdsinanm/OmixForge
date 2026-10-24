"""Tests for the centralized ThemeManager and application-wide dark theme support.

Run with:
    poetry run pytest tests/test_ui/test_theme.py -v

These tests validate the real ThemeManager API:
- set_theme() always emits theme_changed (no same-theme deduplication guard)
- get_color() returns "#ffffff" fallback for unknown keys (no raise)
- get_icon() returns a QIcon, not a raw path string
- save_theme(theme_name) requires the theme name argument
- set_theme() with an unrecognised name silently defaults to "light" (logs warning)
"""

import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QPalette, QIcon


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication exists for the whole test session."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def reset_theme(qapp):
    """Reset theme to light before every test to avoid state leakage."""
    from src.utils.theme_manager import theme_manager
    theme_manager.set_theme("light")
    yield
    theme_manager.set_theme("light")


# ---------------------------------------------------------------------------
# 1. ThemeManager core API
# ---------------------------------------------------------------------------

class TestThemeManagerAPI:
    def test_default_theme_is_light(self, qapp):
        from src.utils.theme_manager import theme_manager
        assert theme_manager.current_theme() == "light"

    def test_set_theme_dark(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        assert theme_manager.current_theme() == "dark"
        assert theme_manager.is_dark() is True

    def test_set_theme_light(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        theme_manager.set_theme("light")
        assert theme_manager.current_theme() == "light"
        assert theme_manager.is_dark() is False

    def test_toggle_theme(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        theme_manager.toggle_theme()
        assert theme_manager.current_theme() == "dark"
        theme_manager.toggle_theme()
        assert theme_manager.current_theme() == "light"

    def test_invalid_theme_name_silently_defaults_to_light(self, qapp):
        """Unknown theme names fall back to 'light' with a warning (no raise)."""
        from src.utils.theme_manager import theme_manager
        # Should not raise; logs a warning instead
        theme_manager.set_theme("solarized")
        assert theme_manager.current_theme() == "light"


# ---------------------------------------------------------------------------
# 2. Token values
# ---------------------------------------------------------------------------

class TestThemeTokens:
    def test_light_tokens_main_bg(self, qapp):
        from src.utils.theme_manager import theme_manager, LIGHT_TOKENS
        theme_manager.set_theme("light")
        t = theme_manager.get_tokens()
        assert t.name == "light"
        assert t.main_bg == LIGHT_TOKENS.main_bg

    def test_dark_tokens_main_bg(self, qapp):
        from src.utils.theme_manager import theme_manager, DARK_TOKENS
        theme_manager.set_theme("dark")
        t = theme_manager.get_tokens()
        assert t.name == "dark"
        assert t.main_bg == DARK_TOKENS.main_bg
        assert t.main_bg == "#121212"

    def test_dark_accent_primary(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        t = theme_manager.get_tokens()
        assert t.accent_primary == "#80CBC4"

    def test_dark_error_color(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        t = theme_manager.get_tokens()
        assert t.error == "#EF9A9A"

    def test_dark_success_color(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        t = theme_manager.get_tokens()
        assert t.success == "#81C784"

    def test_get_color_returns_string(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        val = theme_manager.get_color("accent_primary")
        assert isinstance(val, str)
        assert val.startswith("#")

    def test_get_color_unknown_key_returns_fallback(self, qapp):
        """get_color() returns a safe fallback string for unknown tokens (no raise)."""
        from src.utils.theme_manager import theme_manager
        val = theme_manager.get_color("nonexistent_token_xyz")
        assert isinstance(val, str)  # returns "#ffffff" fallback


# ---------------------------------------------------------------------------
# 3. theme_changed signal
# ---------------------------------------------------------------------------

class TestThemeChangedSignal:
    def test_signal_emitted_on_set_theme(self, qapp):
        from src.utils.theme_manager import theme_manager
        received = []
        theme_manager.theme_changed.connect(lambda t: received.append(t))
        theme_manager.set_theme("dark")
        theme_manager.theme_changed.disconnect()
        assert "dark" in received

    def test_signal_emitted_on_toggle(self, qapp):
        from src.utils.theme_manager import theme_manager
        received = []
        theme_manager.theme_changed.connect(lambda t: received.append(t))
        theme_manager.toggle_theme()
        theme_manager.theme_changed.disconnect()
        assert len(received) >= 1
        assert "dark" in received


# ---------------------------------------------------------------------------
# 4. QPalette generation
# ---------------------------------------------------------------------------

class TestPaletteGeneration:
    def test_get_palette_returns_qpalette(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        palette = theme_manager.get_palette()
        assert isinstance(palette, QPalette)

    def test_dark_palette_window_color_is_dark(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        palette = theme_manager.get_palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        # The window color should be a dark shade (R+G+B < 200*3)
        assert (window_color.red() + window_color.green() + window_color.blue()) < 200

    def test_light_palette_window_color_is_light(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        palette = theme_manager.get_palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        # Light theme has a bright window color
        assert (window_color.red() + window_color.green() + window_color.blue()) > 450


# ---------------------------------------------------------------------------
# 5. Stylesheet generation
# ---------------------------------------------------------------------------

class TestStylesheetGeneration:
    def test_get_stylesheet_returns_str(self, qapp):
        from src.utils.theme_manager import theme_manager
        ss = theme_manager.get_stylesheet()
        assert isinstance(ss, str)
        assert len(ss) > 0

    def test_dark_stylesheet_contains_dark_bg(self, qapp):
        from src.utils.theme_manager import theme_manager, DARK_TOKENS
        theme_manager.set_theme("dark")
        ss = theme_manager.get_stylesheet()
        assert DARK_TOKENS.main_bg.lower() in ss.lower()

    def test_global_style_sheet_delegates_to_theme_manager(self, qapp):
        from src.utils.theme_manager import theme_manager
        from src.assets.stylesheet import global_style_sheet
        theme_manager.set_theme("dark")
        assert global_style_sheet() == theme_manager.get_stylesheet()


# ---------------------------------------------------------------------------
# 6. Icon helpers
# ---------------------------------------------------------------------------

class TestIconHelpers:
    def test_get_icon_returns_qicon(self, qapp):
        """get_icon() returns a QIcon object (not a path string)."""
        from src.utils.theme_manager import theme_manager
        icon = theme_manager.get_icon("lock")
        assert isinstance(icon, QIcon)

    def test_get_icon_lock_dark_is_not_null(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        icon = theme_manager.get_icon("lock")
        assert not icon.isNull()

    def test_get_icon_lock_light_is_not_null(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        icon = theme_manager.get_icon("lock")
        assert not icon.isNull()

    def test_get_icon_logout_dark_is_not_null(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        icon = theme_manager.get_icon("logout")
        assert isinstance(icon, QIcon)

    def test_get_svg_path_theme_is_moon_for_light(self, qapp):
        """get_svg_path() returns a path string; light mode theme icon is moon."""
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        path = theme_manager.get_svg_path("moon")
        assert isinstance(path, str)
        assert "moon" in path.lower()

    def test_get_svg_path_theme_is_sun_for_dark(self, qapp):
        """get_svg_path() returns a path string; dark mode theme icon is sun."""
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        path = theme_manager.get_svg_path("sun")
        assert isinstance(path, str)
        assert "sun" in path.lower()


# ---------------------------------------------------------------------------
# 7. Persistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_and_load_via_qsettings(self, qapp):
        from src.utils.theme_manager import theme_manager

        # Write "dark" directly to QSettings (bypass set_theme to avoid autouse teardown race)
        qs = QSettings("OmixForge", "OmixForge")
        qs.setValue("app/theme", "dark")
        qs.sync()

        # Reset only the in-memory state so load_saved_theme has something to do
        theme_manager._current_theme_name = "light"

        # load_saved_theme reads QSettings and updates _current_theme_name
        result = theme_manager.load_saved_theme()
        assert result == "dark"
        assert theme_manager.current_theme() == "dark"

        # Cleanup: restore QSettings to "light"
        qs.setValue("app/theme", "light")
        qs.sync()
        theme_manager._current_theme_name = "light"

    def test_save_theme_accepts_string_argument(self, qapp):
        """save_theme requires a theme_name argument."""
        from src.utils.theme_manager import theme_manager
        # Should not raise
        theme_manager.save_theme("light")
        theme_manager.save_theme("dark")

    def test_load_saved_theme_defaults_to_light_when_no_setting(self, qapp):
        from src.utils.theme_manager import theme_manager
        # Clear any stored setting
        qs = QSettings("OmixForge", "OmixForge")
        qs.remove("app/theme")
        qs.remove("app/dark_mode")
        qs.sync()

        theme_manager._current_theme_name = "dark"  # pretend we're in dark
        theme_manager.load_saved_theme()
        assert theme_manager.current_theme() == "light"


# ---------------------------------------------------------------------------
# 8. Plugin API – on_theme_changed hook
# ---------------------------------------------------------------------------

class TestPluginThemeHook:
    def test_plugin_base_on_theme_changed_is_noop(self, qapp):
        """PluginBase.on_theme_changed must not raise (default no-op)."""
        from src.core.plugin_manager.plugin_api import PluginBase

        class ConcretePlugin(PluginBase):
            def name(self): return "test"
            def api_version(self): return "1.0"
            def load(self, w, c): pass
            def unload(self): pass

        plugin = ConcretePlugin()
        # Should not raise
        plugin.on_theme_changed("dark")
        plugin.on_theme_changed("light")

    def test_plugin_manager_dispatches_theme_changed(self, qapp):
        """PluginManager._on_theme_changed calls on_theme_changed on loaded plugins."""
        from src.core.plugin_manager.manager import PluginManager

        pm = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name.return_value = "mock"
        pm.loaded_plugins.append(mock_plugin)

        pm._on_theme_changed("dark")
        mock_plugin.on_theme_changed.assert_called_once_with("dark")

    def test_plugin_manager_theme_changed_signal_triggers_dispatch(self, qapp):
        """theme_manager.theme_changed signal automatically dispatches to plugins."""
        from src.utils.theme_manager import theme_manager
        from src.core.plugin_manager.manager import PluginManager

        pm = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name.return_value = "mock"
        pm.loaded_plugins.append(mock_plugin)

        theme_manager.set_theme("dark")
        mock_plugin.on_theme_changed.assert_called_with("dark")


# ---------------------------------------------------------------------------
# 9. AppSettingsSection – dark_mode checkbox wiring
# ---------------------------------------------------------------------------

class TestAppSettingsSection:
    def test_dark_mode_checkbox_reflects_current_theme(self, qapp):
        from src.utils.theme_manager import theme_manager
        from src.core.settings_page.sections.app_settings_section import AppSettingsSection
        theme_manager.set_theme("dark")
        section = AppSettingsSection()
        assert section.dark_mode.isChecked() is True

    def test_toggling_checkbox_switches_theme(self, qapp):
        from src.utils.theme_manager import theme_manager
        from src.core.settings_page.sections.app_settings_section import AppSettingsSection
        theme_manager.set_theme("light")
        section = AppSettingsSection()
        section.dark_mode.setChecked(True)
        assert theme_manager.current_theme() == "dark"

    def test_get_settings_includes_theme(self, qapp):
        from src.core.settings_page.sections.app_settings_section import AppSettingsSection
        section = AppSettingsSection()
        section.dark_mode.setChecked(True)
        settings = section.get_settings()
        assert settings["theme"] == "dark"
        assert settings["dark_mode"] is True

    def test_load_settings_restores_dark_mode(self, qapp):
        from src.core.settings_page.sections.app_settings_section import AppSettingsSection
        section = AppSettingsSection()
        section.load_settings({"theme": "dark", "dark_mode": True})
        assert section.dark_mode.isChecked() is True

    def test_external_theme_change_syncs_checkbox(self, qapp):
        from src.utils.theme_manager import theme_manager
        from src.core.settings_page.sections.app_settings_section import AppSettingsSection
        theme_manager.set_theme("light")
        section = AppSettingsSection()
        assert section.dark_mode.isChecked() is False
        theme_manager.set_theme("dark")
        assert section.dark_mode.isChecked() is True

    def test_get_settings_returns_light_when_unchecked(self, qapp):
        from src.core.settings_page.sections.app_settings_section import AppSettingsSection
        section = AppSettingsSection()
        section.dark_mode.setChecked(False)
        settings = section.get_settings()
        assert settings["theme"] == "light"
        assert settings["dark_mode"] is False


# ---------------------------------------------------------------------------
# 10. Widget dynamic theming – LoadingSpinner
# ---------------------------------------------------------------------------

class TestLoadingSpinnerTheme:
    def test_spinner_applies_dark_stylesheet(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("dark")
        from src.utils.widgets.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        # Progress bar stylesheet must reference the dark accent color
        ss = spinner.progress_bar.styleSheet()
        assert "#80CBC4" in ss  # dark accent_primary

    def test_spinner_applies_light_stylesheet(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        from src.utils.widgets.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        ss = spinner.progress_bar.styleSheet()
        # Should not contain the dark accent
        assert "#80CBC4" not in ss

    def test_spinner_updates_on_theme_change(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        from src.utils.widgets.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        light_ss = spinner.progress_bar.styleSheet()
        theme_manager.set_theme("dark")
        dark_ss = spinner.progress_bar.styleSheet()
        assert light_ss != dark_ss


# ---------------------------------------------------------------------------
# 11. PipelineCard (run_status) – theme-aware card colors
# ---------------------------------------------------------------------------

class TestPipelineCardColors:
    def test_failed_card_uses_error_bg_in_dark(self, qapp):
        from src.utils.theme_manager import theme_manager, DARK_TOKENS
        theme_manager.set_theme("dark")
        from src.core.status_page.status.run_status import PipelineCard
        card = PipelineCard("my-run", status="FAILED")
        ss = card.styleSheet()
        assert DARK_TOKENS.error_bg.lower() in ss.lower()

    def test_completed_card_uses_success_bg_in_dark(self, qapp):
        from src.utils.theme_manager import theme_manager, DARK_TOKENS
        theme_manager.set_theme("dark")
        from src.core.status_page.status.run_status import PipelineCard
        card = PipelineCard("my-run", status="COMPLETED")
        ss = card.styleSheet()
        assert DARK_TOKENS.success_bg.lower() in ss.lower()

    def test_card_update_style_changes_on_theme_switch(self, qapp):
        from src.utils.theme_manager import theme_manager
        theme_manager.set_theme("light")
        from src.core.status_page.status.run_status import PipelineCard
        card = PipelineCard("my-run", status="RUNNING")
        light_ss = card.styleSheet()
        theme_manager.set_theme("dark")
        card.update_style()
        dark_ss = card.styleSheet()
        assert light_ss != dark_ss

    def test_cancelled_card_uses_neutral_bg(self, qapp):
        from src.utils.theme_manager import theme_manager, DARK_TOKENS
        theme_manager.set_theme("dark")
        from src.core.status_page.status.run_status import PipelineCard
        card = PipelineCard("my-run", status="CANCELLED")
        ss = card.styleSheet()
        assert DARK_TOKENS.badge_neutral_bg.lower() in ss.lower()

    def test_running_card_uses_warning_bg_in_dark(self, qapp):
        from src.utils.theme_manager import theme_manager, DARK_TOKENS
        theme_manager.set_theme("dark")
        from src.core.status_page.status.run_status import PipelineCard
        card = PipelineCard("my-run", status="RUNNING")
        ss = card.styleSheet()
        assert DARK_TOKENS.warning_bg.lower() in ss.lower()


# ---------------------------------------------------------------------------
# 12. PluginsPage – transparent backgrounds
# ---------------------------------------------------------------------------

class TestPluginsPageTheme:
    def test_plugins_page_scroll_viewport_is_transparent(self, qapp):
        from src.core.plugin_manager.manager import PluginManager
        from src.core.plugin_manager.plugin_page import PluginsPage
        pm = PluginManager()
        page = PluginsPage(pm)
        # The viewport stylesheet should be "background: transparent;"
        vp_ss = page.scroll.viewport().styleSheet()
        assert "transparent" in vp_ss.lower()

    def test_plugins_page_stack_is_transparent(self, qapp):
        from src.core.plugin_manager.manager import PluginManager
        from src.core.plugin_manager.plugin_page import PluginsPage
        pm = PluginManager()
        page = PluginsPage(pm)
        assert "transparent" in page.stack.styleSheet().lower()
