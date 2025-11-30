from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QClipboard
from PySide6.QtCore import QObject, Signal, QTimer

class ClipboardMonitor(QObject):
    text_copied = Signal(str)

    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.last_text = ""
        
        # We can use dataChanged signal, but sometimes it fires multiple times or for non-text
        self.clipboard.dataChanged.connect(self.on_clipboard_change)

    def on_clipboard_change(self):
        mime_data = self.clipboard.mimeData()
        if mime_data.hasText():
            text = mime_data.text().strip()
            # Only process text that's substantial (more than 10 characters)
            if text and text != self.last_text and len(text) > 10:
                self.last_text = text
                print(f"Clipboard detected: {text[:50]}...")  # Debug output
                self.text_copied.emit(text)

    def manual_check(self):
        # Fallback if signal doesn't work reliably in some environments
        self.on_clipboard_change()
