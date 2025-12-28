def global_style_sheet():
    return """
    QPushButton {
        color: palette(ButtonText);          /* adapts */
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 13px;
        border: 1px solid #2f6fd6;
    }

    QPushButton:hover {
        background-color: #5592ff;
    }

    QPushButton:pressed {
        background-color: #2f6fd6;
    }

    QPushButton:disabled {
        color: black
        background-color: #9ca3af;
        border: 1px solid #6b7280;
    }
    """
def close_btn_red_bg():
    return """
    QPushButton {
        color: palette(ButtonText);          /* adapts automatically */
        background-color: #ef4444;           /* red */
        border: 1px solid #b91c1c;           /* darker red border */
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 14px;
    }

    QPushButton:hover {
        background-color: #f87171;
    }

    QPushButton:pressed {
        background-color: #dc2626;
    }

    QPushButton:disabled {
        color: palette(Mid);
        background-color: palette(Base);
        border: 1px solid palette(Midlight);
    }
    """
