from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,QToolButton

def test_starts_on_access_page(window):
    assert window.centralWidget().__class__.__name__ == "AccessModePage"
    title = window.findChild(QLabel, "titleLabel")
    title.text() == "OmixForge"

    subtitleLabel = window.findChild(QLabel, "subtitleLabel")
    assert subtitleLabel.text() == "Offline Bioinformatics Pipeline Execution"

    print(window)

def test_public_access_button(window):

    public_card = window.findChild(QFrame, "public_access_card")
    assert public_card

    card_title = public_card.findChild(QLabel, "cardTitle")
    assert card_title.text() == "Public Mode"

    subtitle = public_card.findChild(QLabel, "cardSubtitle")
    assert subtitle.text() == "Run without login"

def test_private_access_button(window):

    public_card = window.findChild(QFrame, "private_access_card")
    assert public_card

    card_title = public_card.findChild(QLabel, "cardTitle")
    assert card_title.text() == "Private Mode"

    subtitle = public_card.findChild(QLabel, "cardSubtitle")
    assert subtitle.text() == "Requires login"


def test_public_mode_loads_main_ui(window, sidebar_items):
    # test the public mode ui has all the sidebar elements
    window.access_page.public_selected.emit()

    list_widget = window.sidebar.widget()

    assert window._main_ui_loaded is True
    assert list_widget
    assert len(list_widget) == 4

    for i in sidebar_items:
        items = list_widget.findItems(i, Qt.MatchFlag.MatchExactly)
        assert items[0].text() == i

def test_sidebar_navigation_pipeline_status(window, qtbot):
    # Load the main UI
    window.access_page.public_selected.emit()

    list_widget = window.sidebar.widget()

    # Find the target list item
    items = list_widget.findItems("Pipeline Status", Qt.MatchFlag.MatchExactly)
    assert items, "Pipeline Status item not found in sidebar"
    pipeline_status_item = items[0]

    # Click the item visually where it is rendered
    rect = list_widget.visualItemRect(pipeline_status_item)
    qtbot.mouseClick(
        list_widget.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center()
    )

    # Verify page switched
    assert window.stack.currentWidget() is window.pipeline_status.widget


def test_sidebar_navigation_pipeline_dashboard(window, qtbot):
    # Load the main UI
    window.access_page.public_selected.emit()

    list_widget = window.sidebar.widget()

    # Find the target list item
    items = list_widget.findItems("Pipeline Dashboard", Qt.MatchFlag.MatchExactly)
    assert items, "Pipeline Dashboard item not found in sidebar"
    pipeline_dash_item = items[0]

    # Click the item visually where it is rendered
    rect = list_widget.visualItemRect(pipeline_dash_item)
    qtbot.mouseClick(
        list_widget.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center()
    )

    # Verify page switched
    assert window.stack.currentWidget() is window.pipeline_dashboard.widget


def test_sidebar_navigation_sample_prep(window, qtbot):
    # Load the main UI
    window.access_page.public_selected.emit()

    list_widget = window.sidebar.widget()

    # Find the target list item
    items = list_widget.findItems("Sample Prep", Qt.MatchFlag.MatchExactly)
    assert items, "Sample Prep item not found in sidebar"
    sample_prep_page_item = items[0]

    # Click the item visually where it is rendered
    rect = list_widget.visualItemRect(sample_prep_page_item)
    qtbot.mouseClick(
        list_widget.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center()
    )

    # Verify page switched
    assert window.stack.currentWidget() is window.sample_prep_page.widget


def test_sidebar_navigation_settings_page(window, qtbot):
    # Load the main UI
    window.access_page.public_selected.emit()

    list_widget = window.sidebar.widget()

    # Find the target list item
    items = list_widget.findItems("Settings", Qt.MatchFlag.MatchExactly)
    assert items, "Settings page item not found in sidebar"
    settings_page_item = items[0]

    # Click the item visually where it is rendered
    rect = list_widget.visualItemRect(settings_page_item)
    qtbot.mouseClick(
        list_widget.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center()
    )

    # Verify page switched
    assert window.stack.currentWidget() is window.settings_page.widget
