import json
from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QToolButton, QLineEdit, QTabWidget, QComboBox, QPushButton, QApplication

from src.core.about_page.about import AboutPage
from src.core.dashboard.pipeline_dashboard import PipelineDashboard
from src.core.dashboard.pipeline_import_tab.pipeline_import import PipelineImport
from src.core.dashboard.pipeline_dash_tab.local_pipeline import PipelineLocal
from src.core.dashboard.pipeline_dash_tab.pipeline_card import PipelineCard
from src.core.dashboard.pipeline_editor_tab.pipeline_editor import PipelineEditorTab, PipelineDataCard as EditorDataCard
from src.core.plugin_manager.plugin_page import PluginsPage
from src.core.profile_page.profile import ProfilePage
from src.core.profile_page.startup_page import AccessModePage
from src.core.sample.sample_page import Sample
from src.core.settings_page.sections.folder_path_section import FolderPathsSection
from src.core.settings_page.settings import SettingsPage
from src.core.status_page.results.run_results import PipelineResultsPage, PipelineDataCard as ResultsDataCard
from src.utils.nfcore_utils import NfcoreUtils

def test_starts_on_access_page(window):
    assert window.centralWidget().__class__.__name__ == "AccessModePage"
    title = window.findChild(QLabel, "titleLabel")
    title.text() == "OmixForge"

    subtitleLabel = window.findChild(QLabel, "subtitleLabel")
    assert subtitleLabel.text() == "Offline Bioinformatics Pipeline Execution"


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

    for i in sidebar_items:
        items = list_widget.findItems(i, Qt.MatchFlag.MatchExactly)
        assert items[0].text() == i

def test_sidebar_navigation_pipeline_status(window, qtbot):
    # Load the main UI
    window.access_page.public_selected.emit()

    list_widget = window.sidebar.widget()

    # Find the target list item (may have badge)
    pipeline_status_item = None
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        if item.text().startswith("Pipeline Status"):
            pipeline_status_item = item
            break
    assert pipeline_status_item, "Pipeline Status item not found in sidebar"

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


def test_check_pipeline_import_page(window, qtbot, monkeypatch):
    sample_pipelines = [
        SimpleNamespace(
            name="demo",
            full_name="nf-core/demo",
            description="Demo workflow",
            topics=["demo", "test"],
            archived=False,
        )
    ]
    monkeypatch.setattr(NfcoreUtils, "get_pipelines", lambda self: sample_pipelines)

    window.show()
    window.access_page.public_selected.emit()
    QApplication.processEvents()

    list_widget = window.sidebar.widget()
    window.badge_label.setText("1")
    window.badge_label.show()
    QApplication.processEvents()
    status_rect = window.sidebar_list.visualItemRect(window.pipeline_status_item)
    badge_center_y = window.badge_label.mapTo(
        window.sidebar_list.viewport(), window.badge_label.rect().center()
    ).y()
    status_widget = window.sidebar_list.itemWidget(window.pipeline_status_item)
    assert abs(badge_center_y - status_rect.center().y()) <= 1, (
        f"badge={window.badge_label.geometry()}, row={status_rect}, "
        f"widget={status_widget.geometry()}, "
        f"widget_in_viewport={status_widget.mapTo(window.sidebar_list.viewport(), status_widget.rect().topLeft())}"
    )

    items = list_widget.findItems("Pipeline Dashboard", Qt.MatchFlag.MatchExactly)
    assert items, "Pipeline Dashboard item not found in sidebar"
    pipeline_dash_item = items[0]

    rect = list_widget.visualItemRect(pipeline_dash_item)
    qtbot.mouseClick(list_widget.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())

    dashboard = window.pipeline_dashboard.widget
    assert window.stack.currentWidget() is dashboard

    tab = dashboard.findChild(QTabWidget)
    tabbar = tab.tabBar()
    for i in range(tab.count()):
        if tab.tabText(i) == "Import":
            rect = tabbar.tabRect(i)
            qtbot.mouseClick(tab.tabBar(), Qt.MouseButton.LeftButton, pos=rect.center())

    assert tab.currentIndex() == 1, "Not on the import tab"

    refresh_btn = dashboard.findChild(QPushButton, "refersh_pipeline")
    assert refresh_btn is not None, "Could not find refresh button"
    qtbot.mouseClick(refresh_btn, Qt.MouseButton.LeftButton)

    combo = dashboard.findChild(QComboBox, "select_pipelines_box")
    assert combo is not None, "Could not find combobox"
    qtbot.waitUntil(lambda: combo.count() > 0, timeout=15000)
    assert combo.count() > 0, "Pipeline list did not populate"
    assert combo.findText("demo") != -1, "Expected demo pipeline in the mocked results"

    combo.setCurrentIndex(combo.findText("demo"))
    QApplication.processEvents()

    def get_import_btn():
        return dashboard.findChild(QPushButton, "import_selected_pipeline")

    qtbot.waitUntil(lambda: get_import_btn() is not None, timeout=15000)
    assert get_import_btn() is not None, "Could not find import button"


def test_pipeline_import_search_filters_name_and_topic(qtbot):
    import_tab = PipelineImport()
    qtbot.addWidget(import_tab)
    import_tab._on_pipelines_ready([
        SimpleNamespace(
            name="rnaseq",
            full_name="nf-core/rnaseq",
            description="RNA workflow",
            topics=["transcriptomics"],
            archived=False,
        ),
        SimpleNamespace(
            name="chipseq",
            full_name="nf-core/chipseq",
            description="ChIP workflow",
            topics=["epigenomics"],
            archived=False,
        ),
    ])

    import_tab.search_input.setText("EPI")

    assert import_tab.combobox.count() == 1
    assert import_tab.combobox.currentText() == "chipseq"
    assert import_tab.status_label.text() == "Showing 1 of 2 workflows."

    import_tab.search_input.setText("rnaseq")
    assert import_tab.combobox.count() == 1
    assert import_tab.combobox.currentText() == "rnaseq"

    import_tab.search_input.setText("no-match")

    assert import_tab.combobox.count() == 0
    assert "Adjust or clear your search" in import_tab.status_label.text()


def test_pipeline_import_empty_state_keeps_controls_at_top(qtbot):
    import_tab = PipelineImport()
    qtbot.addWidget(import_tab)
    import_tab.resize(1000, 600)
    import_tab.show()
    QApplication.processEvents()

    title = import_tab.content.findChild(QLabel, "dashboardSectionTitle")
    assert title is not None
    assert title.height() < 50
    assert import_tab.url_input.y() < 100
    assert import_tab.status_label.height() < 60


def test_pipeline_import_empty_results_offer_refresh_guidance(qtbot):
    import_tab = PipelineImport()
    qtbot.addWidget(import_tab)

    import_tab._on_pipelines_ready([])

    assert import_tab.combobox.count() == 0
    assert "refresh to try again" in import_tab.status_label.text()


def test_git_import_error_shows_inline_retry_guidance(qtbot):
    import_tab = PipelineImport()
    qtbot.addWidget(import_tab)

    import_tab._on_git_import_error("connection timed out")

    assert "Check the repository URL and your network connection" in import_tab.status_label.text()
    assert import_tab.url_import_btn.isEnabled()


def test_access_page_requirement_warning_on_missing_tools():
    page = AccessModePage(False, False)
    texts = [label.text() for label in page.findChildren(QLabel) if label.text()]
    assert "Oops — Requirements Missing" in texts
    assert any("Docker" in text for text in texts)
    assert any("Nextflow" in text for text in texts)


def test_profile_page_renders_signup_form(monkeypatch):
    monkeypatch.setattr("src.core.profile_page.profile.file_exists", lambda path: False)
    page = ProfilePage()
    assert page.findChild(QPushButton, "backButton") is not None
    assert page.findChild(QLineEdit, "inputField") is not None
    assert page.findChild(QPushButton, "loginButton") is not None
    assert page.findChild(QPushButton, "loginButton").text() == "Sign Up"


def test_about_page_is_populated():
    page = AboutPage()
    labels = [label.text() for label in page.findChildren(QLabel) if label.text()]
    assert any("OmixForge" in text for text in labels)
    assert any("Version:" in text for text in labels)
    assert any("License" in text for text in labels)
    assert any("Authors & Contributors" in text for text in labels)


def test_sample_page_has_expected_tabs():
    page = Sample()
    tab_widget = page.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.tabText(0) == "Sample Prep"
    assert tab_widget.tabText(1) == "ENA Fastq Downloader"


def test_plugins_page_can_register_and_show_widget():
    page = PluginsPage(object())
    widget = QWidget()
    widget.setObjectName("plugin_widget")
    page.add_plugin_widget("Alpha", widget)
    page.show_plugin("Alpha")
    assert page.stack.currentWidget() is widget


def test_settings_page_save_and_load_round_trip(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_file = config_dir / "app.config"

    import src.core.settings_page.settings as settings_module

    monkeypatch.setattr(settings_module, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_module, "CONFIG_FILE", config_file)

    page = SettingsPage()
    page.folder_section.data_dir.setText("/tmp/data")
    page.folder_section.run_dir.setText("/tmp/run")
    page.folder_section.pipeline_runs.setText("/tmp/pipeline-runs")
    page.folder_section.sample_prep_dir.setText("/tmp/sample")

    page.server_section.add_server()
    server = page.server_section.servers[0]
    server.name_edit.setText("Test Server")
    server.host_edit.setText("example.com")
    server.port_edit.setText("2222")
    server.username_edit.setText("demo-user")
    server.key_edit.setText("/tmp/key.pem")

    page.save_settings()

    assert config_file.exists()
    loaded = json.loads(config_file.read_text())
    assert loaded["folders"]["DATA_DIR"] == "/tmp/data"
    assert loaded["server"][0]["host"] == "example.com"

    restored = SettingsPage()
    assert restored.folder_section.data_dir.text() == "/tmp/data"
    assert restored.server_section.servers[0].host_edit.text() == "example.com"


def test_settings_folder_path_inputs_are_aligned(qtbot):
    section = FolderPathsSection()
    qtbot.addWidget(section)
    section.resize(900, 250)
    section.show()
    QApplication.processEvents()

    inputs = [
        section.data_dir,
        section.run_dir,
        section.pipeline_runs,
        section.sample_prep_dir,
    ]
    assert len({field.geometry().left() for field in inputs}) == 1


def test_pipeline_cards_scroll_after_fifteenth_pipeline(qtbot, monkeypatch):
    import src.core.dashboard.pipeline_dash_tab.local_pipeline as local_pipeline_module

    monkeypatch.setattr(
        local_pipeline_module,
        "run_shell_command",
        lambda _: SimpleNamespace(stdout=""),
    )
    monkeypatch.setattr(local_pipeline_module, "json_read", lambda _: {})

    page = PipelineLocal()
    qtbot.addWidget(page)
    page.resize(900, 600)
    page.show()

    page.pipelines = [f"nf-core/test-{index}" for index in range(15)]
    page.render_cards()
    QApplication.processEvents()
    assert page.cards_scroll.verticalScrollBar().maximum() == 0

    page.pipelines.append("nf-core/test-15")
    page.render_cards()
    QApplication.processEvents()
    assert page.cards_scroll.verticalScrollBar().maximum() > 0


def test_access_page_public_card_renders_expected_titles():
    page = AccessModePage(True, True)
    public_card = page.findChild(QWidget, "public_access_card")
    assert public_card is not None
    assert public_card.findChild(QLabel, "cardTitle").text() == "Public Mode"
    assert public_card.findChild(QLabel, "cardSubtitle").text() == "Run without login"

    private_card = page.findChild(QWidget, "private_access_card")
    assert private_card is not None
    assert private_card.findChild(QLabel, "cardTitle").text() == "Private Mode"
    assert private_card.findChild(QLabel, "cardSubtitle").text() == "Requires login"


def test_pipeline_dashboard_has_expected_tabs(monkeypatch):
    import src.core.dashboard.pipeline_dash_tab.local_pipeline as local_module
    monkeypatch.setattr(local_module, "run_shell_command", lambda *_args, **_kwargs: SimpleNamespace(stdout="demo\n"))
    monkeypatch.setattr(local_module, "json_read", lambda *_args, **_kwargs: {"folders": {"RUN_DIR": "/tmp", "PIPELINES_RUNS": "/tmp", "SAMPLE_PREP_DIR": "/tmp"}})

    page = PipelineDashboard()
    tab_widget = page.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.tabText(0) == "Pipeline"
    assert tab_widget.tabText(1) == "Import"
    assert tab_widget.tabText(2) == "Pipeline Editor"
    assert page.findChild(PipelineLocal) is not None


def test_pipeline_local_editor_and_results_pages_render_cards(monkeypatch, tmp_path):
    import src.core.dashboard.pipeline_dash_tab.local_pipeline as local_module
    import src.core.dashboard.pipeline_editor_tab.pipeline_editor as editor_module
    import src.core.status_page.results.run_results as results_module

    monkeypatch.setattr(local_module, "json_read", lambda *_args, **_kwargs: {"folders": {"RUN_DIR": str(tmp_path), "PIPELINES_RUNS": str(tmp_path), "SAMPLE_PREP_DIR": str(tmp_path)}})
    monkeypatch.setattr(local_module, "run_shell_command", lambda *_args, **_kwargs: SimpleNamespace(stdout="demo\n"))

    monkeypatch.setattr(editor_module, "json_read", lambda *_args, **_kwargs: {"folders": {"PIPELINE_DIR": str(tmp_path)}})
    monkeypatch.setattr(editor_module, "list_files_in_directory", lambda *_args, **_kwargs: ["editor_pipeline"])

    monkeypatch.setattr(results_module, "json_read", lambda *_args, **_kwargs: {"folders": {"RUN_DIR": str(tmp_path)}})
    monkeypatch.setattr(results_module, "list_files_in_directory", lambda *_args, **_kwargs: ["result_run"])

    local_page = PipelineLocal()
    assert any(card.name == "demo" for card in local_page.findChildren(PipelineCard))

    editor_page = PipelineEditorTab()
    assert any(card.name == "editor_pipeline" for card in editor_page.findChildren(EditorDataCard))

    results_page = PipelineResultsPage()
    assert any(card.name == "result_run" for card in results_page.findChildren(ResultsDataCard))


def test_pipeline_editor_refresh_is_manual(qtbot, monkeypatch):
    import src.core.dashboard.pipeline_editor_tab.pipeline_editor as editor_module

    pipeline_lists = iter([["first"], ["first", "second"]])
    monkeypatch.setattr(editor_module, "json_read", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        editor_module,
        "list_files_in_directory",
        lambda *_args, **_kwargs: next(pipeline_lists),
    )

    page = PipelineEditorTab()
    qtbot.addWidget(page)

    assert not hasattr(page, "_refresh_timer")
    assert len(page.findChildren(EditorDataCard)) == 1
    page.findChild(QPushButton, "refreshPipelineEditorButton").click()
    assert len(page.findChildren(EditorDataCard)) == 2


def test_pipeline_status_page_has_expected_tabs_and_cards(tmp_path, monkeypatch):
    from src.core.status_page.pipeline_status import PipelineStatus
    from src.core.status_page.status.run_status import PipelineCard

    run_dir = tmp_path / "runs"
    run_dir.mkdir(exist_ok=True)
    (run_dir / "demo_run.log").write_text("<<exit-code:0>>\ncompleted successfully\n")

    import src.core.status_page.status.run_status as run_status_module
    monkeypatch.setattr(run_status_module, "CONFIG_FILE", tmp_path / "app.config")
    monkeypatch.setattr(run_status_module, "PIPELINES_RUNS", str(run_dir))
    monkeypatch.setattr(run_status_module, "RUN_DIR", str(run_dir))
    monkeypatch.setattr(run_status_module, "json_read", lambda *_args, **_kwargs: {"folders": {"RUN_DIR": str(run_dir), "PIPELINES_RUNS": str(run_dir)}})

    page = PipelineStatus()
    tab_widget = page.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.tabText(0) == "Status"
    assert tab_widget.tabText(1) == "Results"

    cards = page.findChildren(PipelineCard)
    assert any(card.name == "demo_run.log" for card in cards)


def test_pipeline_result_cards_show_run_status(monkeypatch, qtbot):
    from pathlib import Path
    from tempfile import TemporaryDirectory

    import src.core.status_page.results.run_results as results_module

    with TemporaryDirectory() as temp_dir:
        run_root = Path(temp_dir)
        run_logs = run_root / "logs"
        run_logs.mkdir()
        (run_logs / "complete.txt").write_text("<<exit-code:0>>")
        (run_logs / "failed.txt").write_text("<<exit-code:1>>")
        (run_logs / "cancelled.txt").write_text("Pipeline run cancelled by user.")
        (run_logs / "running.txt").write_text("Running pipeline: nf-core/demo")
        (run_logs / "failed_with_cancel_text.txt").write_text(
            "A task was cancelled after an upstream failure.\n<<exit-code:1>>"
        )
        (run_logs / "locked_failure.txt").write_text("<<exit-code:1>>")

        monkeypatch.setattr(
            results_module,
            "json_read",
            lambda *_args, **_kwargs: {
                "folders": {"RUN_DIR": str(run_root), "PIPELINES_RUNS": str(run_logs)}
            },
        )
        monkeypatch.setattr(
            results_module,
            "list_files_in_directory",
            lambda *_args, **_kwargs: [
                "complete",
                "failed",
                "cancelled",
                "running",
                "failed_with_cancel_text",
                "locked.tar.gz.enc",
                "locked_failure.tar.gz.enc",
            ],
        )

        page = PipelineResultsPage()
        qtbot.addWidget(page)
        statuses = {card.name: card.status for card in page.findChildren(ResultsDataCard)}

        assert statuses == {
            "complete": "Completed",
            "failed": "Failed",
            "cancelled": "Cancelled",
            "running": "Running",
            "failed_with_cancel_text": "Failed",
            "locked.tar.gz.enc": "Encrypted",
            "locked_failure.tar.gz.enc": "Failed",
        }
        encrypted_card = next(
            card for card in page.findChildren(ResultsDataCard)
            if card.name == "locked.tar.gz.enc"
        )
        assert encrypted_card.status_group_layout.indexOf(encrypted_card.status_badge) < (
            encrypted_card.status_group_layout.indexOf(encrypted_card.lock_icon)
        )
        page._refresh_timer.stop()


def test_plugin_store_page_has_tabs_search_and_refresh(qtbot, monkeypatch):
    from src.core.plugin_manager.plugin_installer import PluginStore
    import src.core.plugin_manager.plugin_installer_tabs.store_tab as store_tab_module

    responses = iter([
        [{"name": "charts.py"}, {"name": "calculator.py"}],
        [{"name": "charts.py"}, {"name": "calculator.py"}, {"name": "new_chart.py"}],
    ])

    class Response:
        def __init__(self, contents):
            self.contents = contents

        def raise_for_status(self):
            pass

        def json(self):
            return self.contents

    monkeypatch.setattr(
        store_tab_module.requests,
        "get",
        lambda *_args, **_kwargs: Response(next(responses)),
    )

    class DummyPluginManager:
        def __init__(self):
            self.plugins = {}
            self.loaded_plugins = []

    class DummyWindow:
        def __init__(self):
            self.plugin_manager = DummyPluginManager()
            self.plugins_page = object()
            self.sidebar_list = object()

    window = DummyWindow()
    page = PluginStore(window)
    qtbot.addWidget(page)

    tab_widget = page.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.tabText(0) == "Store"
    assert tab_widget.tabText(1) == "Manage"
    assert page.store_tab.findChild(QLineEdit) is not None
    assert page.store_tab.refresh_button.text() == "Refresh"

    page.store_tab.search_input.setText("chart")
    page.store_tab.refresh_button.click()

    assert page.store_tab.available_plugins == ["charts.py", "calculator.py", "new_chart.py"]
    assert [
        page.store_tab.list_widget.item(index).text()
        for index in range(page.store_tab.list_widget.count())
    ] == ["charts.py", "new_chart.py"]
