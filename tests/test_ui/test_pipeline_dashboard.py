import time
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QPushButton, QComboBox, QApplication
)
from src.utils.subcommands.shell import run_shell_command
from src.core.dashboard.pipeline_dash_tab.pipeline_card import PipelineCard

def debug_print_tree(widget, indent=0):
    for child in widget.findChildren(QWidget):
        print(" " * indent + f"{child.__class__.__name__}  objectName='{child.objectName()}'")

def test_check_pipline_card(window, qtbot):
    # get the pipelines installed
    pipelines = run_shell_command("nextflow list")
    pipelines_list =pipelines.stdout.splitlines()

    # click the public mode
    window.access_page.public_selected.emit()

    # get sidear widget list
    list_widget = window.sidebar.widget()


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
    assert window.stack.currentWidget() is window.pipeline_dashboard.widget, "Not in on the dashboard winfdow"

    dashboard = window.pipeline_dashboard.widget   # your dashboard QWidget
    cards = dashboard.findChildren(PipelineCard)

    # verify that the cards present exaclty matches the cli output
    assert cards
    assert len(cards) == len(pipelines_list), "Pipeline numbers did not matched"

    if len(cards) > 0:
        # click the card if it has more than 1 item
        qtbot.mouseClick(cards[0], Qt.MouseButton.LeftButton)

        def get_run_btn(): # lamda function for getting the run button for wait check
            return dashboard.findChild(QPushButton, "pipeline_run_btn")

        qtbot.waitUntil(lambda: get_run_btn() is not None, timeout=15000)
        pipeline_run_btn = get_run_btn()
        assert pipeline_run_btn, "Faile to find run button"

        pipeline_delete_btn = dashboard.findChild(QPushButton, "pipeline_delete_btn")
        assert pipeline_delete_btn, "Failed to find delete button"

def test_check_pipeline_import_page(window, qtbot):

    # click the public mode
    window.access_page.public_selected.emit()

    # get sidear widget list
    list_widget = window.sidebar.widget()


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

    dashboard = window.pipeline_dashboard.widget


    # Verify page switched
    assert window.stack.currentWidget() is dashboard

    # find tab and click the tab with name import
    tab = dashboard.findChild(QTabWidget)
    tabbar = tab.tabBar()
    for i in range(tab.count()):
        if tab.tabText(i) == "Import":
            rect = tabbar.tabRect(i)
            qtbot.mouseClick(tab.tabBar(), Qt.MouseButton.LeftButton, pos=rect.center())

    assert tab.currentIndex() == 1, "Not on the import tab"

    refresh_btn = dashboard.findChild(QPushButton, "refersh_pipeline")
    assert refresh_btn is not None, "Could not find refersh button"
    qtbot.mouseClick(refresh_btn, Qt.MouseButton.LeftButton)

    combo = dashboard.findChild(QComboBox, "select_pipelines_box")
    assert combo is not None, "Could not find combobox"

    qtbot.waitUntil(lambda: combo.count() > 0, timeout=15000)

    assert combo.count() > 0, "0 pipelines found, could be network issue"#currently 141 pipelines

    demo_index = combo.findText("demo")

    assert demo_index != -1, "could not find demo pipeline, may be officially removed"

    combo.setCurrentIndex(demo_index)

    assert combo.currentText() == "demo"

    QApplication.processEvents()

    # Now wait until the button exists
    def get_import_btn():
        return dashboard.findChild(QPushButton, "import_selected_pipeline")

    qtbot.waitUntil(lambda: get_import_btn() is not None)
    import_btn = get_import_btn()

    assert import_btn is not None, "could not find import button"

    # Click the Import button
    # qtbot.mouseClick(import_btn, Qt.MouseButton.LeftButton)







    


