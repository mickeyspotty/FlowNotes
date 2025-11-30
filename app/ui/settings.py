from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Signal

class SettingsDialog(QDialog):
    notes_cleared = Signal()  # Signal to notify when notes are cleared
    
    def __init__(self, parent=None, current_api_key="", storage=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 220)
        
        # Apply Deep Space theme
        self.setStyleSheet("""
            QDialog {
                background-color: #0F111A;
            }
            QLabel {
                color: #DFE6E9;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #1F2330;
                color: #DFE6E9;
                border: 1px solid #2D3436;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #6C5CE7;
                background-color: #252A3A;
            }
            QPushButton {
                background-color: #1F2330;
                color: #DFE6E9;
                border: 1px solid #2D3436;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #2D3436;
                color: #FFFFFF;
                border: 1px solid #636E72;
            }
            QPushButton:pressed {
                background-color: #000000;
            }
            QPushButton#clearButton {
                background-color: rgba(255, 118, 117, 0.1);
                color: #FF7675;
                border: 1px solid #FF7675;
            }
            QPushButton#clearButton:hover {
                background-color: #FF7675;
                color: #FFFFFF;
            }
            QPushButton#saveButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#saveButton:hover {
                background-color: #a29bfe;
            }
            QMessageBox {
                background-color: #0F111A;
            }
            QMessageBox QLabel {
                color: #DFE6E9;
            }
            QMessageBox QPushButton {
                background-color: #1F2330;
                color: #DFE6E9;
                border: 1px solid #2D3436;
                border-radius: 6px;
                padding: 6px 12px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        # API Key Section
        self.label = QLabel("Gemini API Key:")
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(current_api_key)
        self.api_key_input.setPlaceholderText("AIza...")

        # Clear Notes Button
        self.clear_notes_button = QPushButton("Clear All Notes", self)
        self.clear_notes_button.setObjectName("clearButton")
        self.clear_notes_button.clicked.connect(self.confirm_clear_notes)

        # Save/Cancel Buttons
        self.button_box = QHBoxLayout()
        self.save_button = QPushButton("Save", self)
        self.save_button.setObjectName("saveButton")
        self.cancel_button = QPushButton("Cancel", self)
        
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)

        # Add widgets to layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.api_key_input)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.clear_notes_button)
        self.layout.addSpacing(10)
        self.layout.addLayout(self.button_box)

    def confirm_clear_notes(self):
        """Show confirmation dialog before clearing notes"""
        reply = QMessageBox.question(
            self,
            "Clear All Notes",
            "Are you sure you want to delete all notes? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.storage:
                try:
                    self.storage.clear_all_notes()
                    self.notes_cleared.emit()  # Emit signal to refresh UI
                    QMessageBox.information(
                        self,
                        "Success",
                        "All notes have been cleared successfully."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to clear notes: {str(e)}"
                    )

    def get_api_key(self):
        return self.api_key_input.text().strip()
