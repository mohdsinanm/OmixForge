"""Stylesheet provider for OmixForge application.

Integrates with ThemeManager to provide centralized, theme-aware
global and component stylesheets while maintaining backward compatibility.
"""

from typing import Optional
from src.utils.theme_manager import theme_manager


def global_style_sheet(theme_name: Optional[str] = None) -> str:
    """Return the shared visual stylesheet for the application.

    Parameters
    ----------
    theme_name : str, optional
        Specific theme name ('light' or 'dark'). Defaults to active theme.

    Returns
    -------
    str
        Complete QSS stylesheet.
    """
    return theme_manager.get_stylesheet(theme_name)


def close_button_style(theme_name: Optional[str] = None) -> str:
    """Return CSS stylesheet for a neutral close button tailored to active theme.

    Parameters
    ----------
    theme_name : str, optional
        Specific theme name ('light' or 'dark'). Defaults to active theme.

    Returns
    -------
    str
        CSS stylesheet string for close button styling.
    """
    t = theme_manager.get_tokens(theme_name)
    return f"""
    QPushButton {{
        color: {t.text_secondary};
        background-color: {t.btn_default_bg};
        border: 1px solid {t.btn_default_border};
        border-radius: 6px;
        padding: 6px 9px;
        font-size: 13px;
    }}

    QPushButton:hover {{
        background-color: {t.btn_destructive_hover_bg};
        border-color: {t.btn_destructive_hover_border};
        color: {t.btn_destructive_hover_fg};
    }}

    QPushButton:pressed {{
        background-color: {t.btn_default_pressed_bg};
    }}

    QPushButton:disabled {{
        color: {t.btn_default_disabled_fg};
        background-color: {t.btn_default_disabled_bg};
        border: 1px solid {t.btn_default_disabled_border};
    }}
    """
