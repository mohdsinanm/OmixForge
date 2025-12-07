from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import RUN_DIR, SAMPLE_PREP_DIR

logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
     QVBoxLayout, QLabel,
    QHBoxLayout, QGridLayout, QPushButton, QDialog, QLineEdit, 
    QFileDialog
)
from PyQt6.QtGui import QFont



class PipelineArgsDialog(QDialog):
    """Dialog to collect pipeline arguments and build JSON config."""

    def __init__(self, pipeline_name, sample_sheet_path=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure {pipeline_name}")
        self.setGeometry(100, 100, 600, 500)
        self.pipeline_name = pipeline_name
        self.config = {}
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Pipeline Configuration: {pipeline_name}")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Mandatory args grid
        args_layout = QGridLayout()
        row = 0
        
        # Input (sample sheet)
        args_layout.addWidget(QLabel("input (sample sheet):"), row, 0)
        self.input_field = QLineEdit()
        if sample_sheet_path:
            self.input_field.setText(sample_sheet_path)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_input)
        input_h = QHBoxLayout()
        input_h.addWidget(self.input_field)
        input_h.addWidget(browse_btn)
        args_layout.addLayout(input_h, row, 1)
        row += 1
        
        # Output directory
        args_layout.addWidget(QLabel("outdir:"), row, 0)
        self.outdir_field = QLineEdit()
        self.outdir_field.setText(str(RUN_DIR / f"{pipeline_name}_output"))
        args_layout.addWidget(self.outdir_field, row, 1)
        row += 1
    
        
        layout.addLayout(args_layout)
        
        # Optional args section
        opt_label = QLabel("Additional Arguments :")
        opt_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(opt_label)
        
        self.custom_args = []
        self.custom_args_layout = QVBoxLayout()
        layout.addLayout(self.custom_args_layout)
        
        # Add custom arg button
        add_arg_btn = QPushButton("+ Add Argument")
        add_arg_btn.clicked.connect(self.add_custom_arg)
        layout.addWidget(add_arg_btn)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Run Pipeline")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select sample sheet", str(SAMPLE_PREP_DIR), "CSV Files (*.csv)")
        if path:
            self.input_field.setText(path)

    

    
    def add_custom_arg(self):
        """Add a custom argument field."""
        arg_layout = QHBoxLayout()
        key_field = QLineEdit()
        key_field.setPlaceholderText("Key (e.g., max_cpus)")
        value_field = QLineEdit()
        value_field.setPlaceholderText("Value")
        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(70)
        
        def remove_arg():
            # Remove from layout and custom_args list
            for i in range(self.custom_args_layout.count()):
                if self.custom_args_layout.itemAt(i) == arg_layout:
                    self.custom_args_layout.takeAt(i)
                    break
            self.custom_args.remove((key_field, value_field))
            # Clean up widgets
            key_field.deleteLater()
            value_field.deleteLater()
            remove_btn.deleteLater()
        
        remove_btn.clicked.connect(remove_arg)
        
        arg_layout.addWidget(key_field)
        arg_layout.addWidget(value_field)
        arg_layout.addWidget(remove_btn)
        
        self.custom_args_layout.addLayout(arg_layout)
        self.custom_args.append((key_field, value_field))
    
    def get_config(self):
        """Return the config as a dictionary."""
        config = {}
        
        # Mandatory args
        if self.input_field.text():
            config["input"] = self.input_field.text()
        if self.outdir_field.text():
            config["outdir"] = self.outdir_field.text()
        
        # Custom args
        for key_field, value_field in self.custom_args:
            k = key_field.text().strip()
            v = value_field.text().strip()
            if k and v:
                config[k] = v
        
        return config