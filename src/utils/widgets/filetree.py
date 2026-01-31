
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QUrl

from src.utils.widgets.fileview import FileViewerWindow
from PyQt6.QtGui import QDesktopServices


class FilesTreeWidget(QWidget):
    """
    Embedded widget that shows a directory tree.
    Double-clicking a file opens it in a FileViewerWindow.
    """

    def __init__(self, root_dir: str, allowed_exts: list[str], parent=None, exclude_dirs: list[str] = None):
        """Initialize the file tree widget with a root directory.
        
        Parameters
        ----------
        root_dir : str
            Root directory path to display.
        allowed_exts : list[str]
            List of file extensions to include (e.g., ['.txt', '.csv']).
        parent : QWidget, optional
            Parent widget for this widget.
        """
        super().__init__(parent)

        self.root_dir = os.path.abspath(root_dir)
        self.allowed_exts = allowed_exts
        self._viewer_windows = []  # prevent GC
        self.exclude_dirs = exclude_dirs if exclude_dirs else []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Files"])
        layout.addWidget(self.tree)

        self._populate_tree()
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)


    def _populate_tree(self):
        """Populate file tree widget with directory structure."""
        self.tree.clear()

        root_item = QTreeWidgetItem([os.path.basename(self.root_dir)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_dir)
        self.tree.addTopLevelItem(root_item)

        self._add_children(root_item, self.root_dir)
        root_item.setExpanded(True)

    # ------------------------------------------------------------------

    def _add_children(self, parent_item, path):
        """Recursively add child items to file tree.
        
        Parameters
        ----------
        parent_item : QTreeWidgetItem
            The parent tree item to add children to.
        path : str
            The directory path to list files from.
        """
        try:
            for name in sorted(os.listdir(path)):
                full_path = os.path.join(path, name)

                if any(skip in full_path for skip in self.exclude_dirs):
                    continue

                if os.path.isdir(full_path):
                    item = QTreeWidgetItem([name])
                    item.setData(0, Qt.ItemDataRole.UserRole, full_path)
                    parent_item.addChild(item)
                    self._add_children(item, full_path)

                elif os.path.isfile(full_path):
                    if os.path.splitext(name)[1].lower() in self.allowed_exts:
                        item = QTreeWidgetItem([name])
                        item.setData(0, Qt.ItemDataRole.UserRole, full_path)
                        parent_item.addChild(item)
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------

    def _on_item_double_clicked(self, item, column):
        """Handle file tree item double-click event.
        
        Parameters
        ----------
        item : QTreeWidgetItem
            The clicked tree item.
        column : int
            The column index of the click.
        """
        path = item.data(0, Qt.ItemDataRole.UserRole)

        if not os.path.isfile(path):
            return

        ext = os.path.splitext(path)[1].lower()

        # Open externally (NO window)
        if ext in (".html", ".pdf"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            return

        if os.path.isfile(path):
            viewer = FileViewerWindow(path, parent=self)
            viewer.show()
            self._viewer_windows.append(viewer)
