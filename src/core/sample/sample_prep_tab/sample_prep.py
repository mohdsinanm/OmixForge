import csv
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QFileDialog, QLabel, QMessageBox, QSpinBox, QInputDialog, QApplication
)
from PyQt6.QtCore import Qt
import re, os
from PyQt6.QtGui import QKeySequence
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import SAMPLE_PREP_DIR, CONFIG_FILE
from src.utils.fileops.file_handle import ensure_directory, json_read
logger = OmixForgeLogger.get_logger()


class SamplePrepPage(QWidget):
    """Excel-like interface for adding/editing rows and columns with CSV export."""
    
    def __init__(self):
        super().__init__()
        self.current_file = None

        self.constants = json_read(CONFIG_FILE)
        self.SAMPLE_PREP_DIR =  self.constants.get("folders",{}).get("SAMPLE_PREP_DIR", SAMPLE_PREP_DIR)

        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Sample Preparation - Data Table")
        layout.addWidget(title)
        
        # Controls row
        controls_layout = QHBoxLayout()
        
        # Add row button
        add_row_btn = QPushButton("Add Row")
        add_row_btn.clicked.connect(self.add_row)
        controls_layout.addWidget(add_row_btn)
        
        # Remove row button
        remove_row_btn = QPushButton("Remove Row")
        remove_row_btn.clicked.connect(self.remove_row)
        controls_layout.addWidget(remove_row_btn)
        
        # Add column button
        add_col_btn = QPushButton("Add Column")
        add_col_btn.clicked.connect(self.add_column)
        controls_layout.addWidget(add_col_btn)
        
        # Remove column button
        remove_col_btn = QPushButton("Remove Column")
        remove_col_btn.clicked.connect(self.remove_column)
        controls_layout.addWidget(remove_col_btn)
        
        # Save button
        save_btn = QPushButton("Save as CSV")
        save_btn.clicked.connect(self.save_csv)
        controls_layout.addWidget(save_btn)
        
        # Load button
        load_btn = QPushButton("Load CSV")
        load_btn.clicked.connect(self.load_csv)
        controls_layout.addWidget(load_btn)
        
        # Load files from directory button
        load_dir_btn = QPushButton("Load files from Dir")
        load_dir_btn.clicked.connect(self.load_files_from_dir)
        controls_layout.addWidget(load_dir_btn)
        
        layout.addLayout(controls_layout)
        
        # Table widget with default 5 rows and 3 columns
        self.table = QTableWidget(5, 4)
        self.table.setHorizontalHeaderLabels([i for i in ["sample","fastq_1","fastq_2","strandedness"]])
        self.table.setVerticalHeaderLabels([f"{i+1}" for i in range(5)])
        
        # Make all cells editable
        for row in range(5):
            for col in range(3):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)
        
        # Connect horizontal header click to edit column header
        self.table.horizontalHeader().sectionClicked.connect(self.edit_column_header)
        
        # Store clipboard for copy/paste
        self.clipboard = QApplication.clipboard()
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.widget = self
    
    def add_row(self):
        """Add a new row to the table."""
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        self.table.setVerticalHeaderItem(row_pos, QTableWidgetItem(f"{row_pos+1}"))
        
        # Add editable cells to the new row
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_pos, col, item)
        
        logger.info(f"Added row {row_pos+1}")
    
    def remove_row(self):
        """Remove the selected row."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to remove.")
            return
        self.table.removeRow(current_row)
        logger.info(f"Removed row {current_row+1}")
    
    def add_column(self):
        """Add a new column to the table."""
        col_pos = self.table.columnCount()
        self.table.insertColumn(col_pos)
        self.table.setHorizontalHeaderItem(col_pos, QTableWidgetItem(f"Col {col_pos+1}"))
        
        # Add editable cells to the new column
        for row in range(self.table.rowCount()):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, col_pos, item)
        
        logger.info(f"Added column {col_pos+1}")
    
    def remove_column(self):
        """Remove the selected column."""
        current_col = self.table.currentColumn()
        if current_col < 0:
            QMessageBox.warning(self, "No Selection", "Please select a column to remove.")
            return
        self.table.removeColumn(current_col)
        logger.info(f"Removed column {current_col+1}")
    
    def save_csv(self):
        """Export table data to a CSV file."""
        ensure_directory(self.SAMPLE_PREP_DIR)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save as CSV", str(self.SAMPLE_PREP_DIR), "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path+".csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write headers
                headers = [self.table.horizontalHeaderItem(col).text() 
                          for col in range(self.table.columnCount())]
                writer.writerow(headers)
                
                # Write data rows
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            self.current_file = file_path
            logger.info(f"Saved table to {file_path}")
            QMessageBox.information(self, "Success", f"File saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
    
    def load_csv(self):
        """Load table data from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                QMessageBox.warning(self, "Empty File", "The CSV file is empty.")
                return
            
            # Clear existing table
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            
            # Set columns from header
            headers = rows[0]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            
            # Add data rows
            for row_idx, row_data in enumerate(rows[1:]):
                self.table.insertRow(row_idx)
                self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(f"Row {row_idx+1}"))
                
                for col_idx, value in enumerate(row_data):
                    # Pad with empty columns if needed
                    if col_idx >= self.table.columnCount():
                        self.table.insertColumn(col_idx)
                    
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, item)
            
            self.current_file = file_path
            logger.info(f"Loaded table from {file_path}")
            QMessageBox.information(self, "Success", f"File loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

    def load_files_from_dir(self):
        """Scan a directory for FASTQ/FASTA files and populate the table.

        Behavior:
        - Finds files with extensions: .fastq.gz, .fq.gz, .fastq, .fq, .fasta, .fa
        - Attempts to pair reads (R1/R2, _1/_2, _R1/_R2) into fastq_1 / fastq_2
        - Uses filename base (without PE suffix) as sample name
        - Clears the existing table and fills rows for each sample found
        """
        dir_path = QFileDialog.getExistingDirectory(self, "Select directory with FASTQ/FASTA files", f"{os.getenv("HOME")}")
        if not dir_path:
            return

        p = Path(dir_path)
        patterns = ["*.fastq.gz", "*.fq.gz", "*.fastq", "*.fq", "*.fasta", "*.fa"]
        files = []
        for pat in patterns:
            files.extend(p.rglob(pat))

        if not files:
            QMessageBox.information(self, "No files", "No FASTQ/FASTA files found in the selected directory.")
            return

        # Helper to normalize filename and determine sample base
        def sample_base(name: str):
            # remove common compressed/extension endings
            name = re.sub(r"\.fastq(?:\.gz)?$|\.fq(?:\.gz)?$|\.fasta$|\.fa$", "", name, flags=re.IGNORECASE)
            # remove common pair suffixes like _R1, _R2, _1, _2, .1, .2, -1, -2 and possible _001
            name = re.sub(r"(_|-)(R?)[12](_?\d{3})?$", "", name, flags=re.IGNORECASE)
            # remove trailing _001 etc
            name = re.sub(r"(_\d{3})$", "", name)
            return name

        # Map sample -> {'fastq_1': path or None, 'fastq_2': path or None}
        samples = {}
        for f in files:
            fname = f.name
            base = sample_base(fname)
            lower = fname.lower()
            # identify read1 or read2
            is_r1 = bool(re.search(r"[_.-](r?1)(?:[_.-]|$)", fname, flags=re.IGNORECASE))
            is_r2 = bool(re.search(r"[_.-](r?2)(?:[_.-]|$)", fname, flags=re.IGNORECASE))

            entry = samples.setdefault(base, {"fastq_1": None, "fastq_2": None})
            if is_r1:
                entry["fastq_1"] = str(f)
            elif is_r2:
                entry["fastq_2"] = str(f)
            else:
                # not obviously paired: put in fastq_1 if empty, else fastq_2 if empty, else create new sample name
                if entry["fastq_1"] is None:
                    entry["fastq_1"] = str(f)
                elif entry["fastq_2"] is None:
                    entry["fastq_2"] = str(f)
                else:
                    # create unique sample key
                    i = 2
                    new_base = f"{base}_extra{i}"
                    while new_base in samples:
                        i += 1
                        new_base = f"{base}_extra{i}"
                    samples[new_base] = {"fastq_1": str(f), "fastq_2": None}

        # Now populate the table: clear and set rows
        self.table.setRowCount(0)
        # Ensure at least 4 columns (sample, fastq_1, fastq_2, strandedness)
        if self.table.columnCount() < 3:
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["sample", "fastq_1", "fastq_2", "strandedness"])

        for row_idx, (sample_name, entry) in enumerate(sorted(samples.items())):
            self.table.insertRow(row_idx)
            # sample name
            s_item = QTableWidgetItem(sample_name)
            s_item.setFlags(s_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 0, s_item)
            # fastq_1
            fq1 = entry.get("fastq_1") or ""
            fq1_item = QTableWidgetItem(fq1)
            fq1_item.setFlags(fq1_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 1, fq1_item)
            # fastq_2
            fq2 = entry.get("fastq_2") or ""
            fq2_item = QTableWidgetItem(fq2)
            fq2_item.setFlags(fq2_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 2, fq2_item)
            # strandedness left blank
            if self.table.columnCount() > 3:
                st_item = QTableWidgetItem("")
                st_item.setFlags(st_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, 3, st_item)

        QMessageBox.information(self, "Files Loaded", f"Loaded {len(samples)} sample(s) from {dir_path}")
    
    def edit_column_header(self, col):
        """Allow editing of column header when clicked."""
        current_header = self.table.horizontalHeaderItem(col)
        current_text = current_header.text() if current_header else ""
        
        # Create input dialog with border styling
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Edit Column Header")
        dialog.setLabelText(f"Enter new name for Column {col + 1}:")
        dialog.setTextValue(current_text)
        dialog.setStyleSheet("""
            QInputDialog {
                border: 2px solid #333;
            }
            QInputDialog QLineEdit {
                border: 1px solid #999;
                padding: 4px;
                border-radius: 3px;
            }
            QInputDialog QPushButton {
                border: 1px solid #999;
                padding: 4px 12px;
                border-radius: 3px;
                min-width: 50px;
            }
            QInputDialog QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        
        ok = dialog.exec()
        new_text = dialog.textValue()
        
        if ok and new_text:
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(new_text))
            logger.info(f"Changed column {col+1} header to: {new_text}")
        elif ok and not new_text:
            QMessageBox.warning(self, "Empty Header", "Column header cannot be empty.")
    
    def copy_cells(self):
        """Copy selected cells to clipboard."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
        
        # Collect all selected cells
        copy_data = []
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                row_data = []
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                copy_data.append("\t".join(row_data))
        
        # Copy to clipboard
        if copy_data:
            self.clipboard.setText("\n".join(copy_data))
            logger.info(f"Copied {len(copy_data)} rows to clipboard")
    
    def paste_cells(self):
        """Paste cells from clipboard."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if current_row < 0 or current_col < 0:
            QMessageBox.warning(self, "No Selection", "Please select a cell to paste into.")
            return
        
        # Get text from clipboard
        text = self.clipboard.text()
        if not text:
            return
        
        # Parse clipboard data (tab-separated columns, newline-separated rows)
        rows = text.split("\n")
        
        try:
            for row_idx, row_text in enumerate(rows):
                if not row_text.strip():
                    continue
                
                target_row = current_row + row_idx
                
                # Add rows if needed
                while target_row >= self.table.rowCount():
                    self.add_row()
                
                # Split by tabs
                cols = row_text.split("\t")
                
                for col_idx, cell_text in enumerate(cols):
                    target_col = current_col + col_idx
                    
                    # Add columns if needed
                    while target_col >= self.table.columnCount():
                        self.add_column()
                    
                    # Set cell value
                    item = QTableWidgetItem(cell_text)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(target_row, target_col, item)
            
            logger.info(f"Pasted data at row {current_row}, col {current_col}")
        except Exception as e:
            logger.error(f"Error pasting data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to paste data: {e}")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for copy/paste and cell deletion."""
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_cells()
        elif event.matches(QKeySequence.StandardKey.Paste):
            self.paste_cells()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected_cells()
        else:
            super().keyPressEvent(event)
    
    def delete_selected_cells(self):
        """Delete content of selected cells."""
        selected_ranges = self.table.selectedRanges()
        
        if not selected_ranges:
            return
        
        # Clear all selected cells
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.table.item(row, col)
                    if item:
                        item.setText("")
                    else:
                        # Create empty item if it doesn't exist
                        new_item = QTableWidgetItem("")
                        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
                        self.table.setItem(row, col, new_item)
        
        logger.info(f"Cleared {len(selected_ranges)} cell range(s)")

