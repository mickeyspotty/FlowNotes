import sys
import os
import json
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QInputDialog
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal, QThread

from app.ui.main_window import MainWindow
from app.ui.overlay import OverlayWindow, PersistentOverlayBar, DecisionOverlay
from app.ai.llm_service import LLMService
from app.notes.storage import NoteStorage
from app.utils.clipboard_monitor import ClipboardMonitor

class AIWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, llm_service, text, current_subject=None, existing_subjects=None):
        super().__init__()
        self.llm_service = llm_service
        self.text = text
        self.current_subject = current_subject
        self.existing_subjects = existing_subjects

    def run(self):
        result = self.llm_service.process_text(
            self.text, 
            self.current_subject, 
            self.existing_subjects
        )
        self.finished.emit(result)

class SmartStudyApp(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Services
        self.storage = NoteStorage()
        self.llm_service = LLMService()
        self.clipboard_monitor = ClipboardMonitor()

        # Load API Key
        self.load_config()

        # UI - Create persistent bar first
        self.persistent_bar = PersistentOverlayBar()
        self.main_window = MainWindow(self.storage, self.llm_service, self.persistent_bar)
        self.overlay = OverlayWindow()
        self.decision_overlay = DecisionOverlay()
        
        # Set window icon
        icon_path = "app/resources/icon.png"
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.app.setWindowIcon(app_icon)
            self.main_window.setWindowIcon(app_icon)
        
        # Tray Icon
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self.app)
        self.tray_menu = QMenu()
        show_action = QAction("Show Notes", self.app)
        show_action.triggered.connect(self.main_window.show)
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.app.quit)
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Connections
        self.clipboard_monitor.text_copied.connect(self.on_text_copied)
        self.overlay.clicked.connect(self.main_window.show)
        self.persistent_bar.show_main_window.connect(self.main_window.show)
        self.decision_overlay.decision_made.connect(self.on_decision_made)
        
        # Add polling timer for clipboard (more reliable on macOS)
        from PySide6.QtCore import QTimer
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.clipboard_monitor.manual_check)
        self.clipboard_timer.start(500)  # Check every 500ms
        
        print("Clipboard monitoring started with polling...")

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
                    api_key = config.get("api_key")
                    if api_key:
                        self.llm_service.set_api_key(api_key)
            except Exception as e:
                print(f"Error loading config: {e}")

    def on_text_copied(self, text):
        print(f"Text copied event received! Length: {len(text)}")  # Debug output
        
        # Check if monitoring is enabled via switch
        if not self.main_window.monitoring_switch.isChecked():
            print("Monitoring is paused. Skipping.")
            return
        
        # Only process if we have an API key
        if not self.llm_service.api_key:
            print("No API key set. Skipping.")
            self.persistent_bar.set_status("No API Key")
            return

        print("Starting AI processing...")  # Debug output
        
        # Update persistent bar status
        self.persistent_bar.set_processing()
        
        # Show loading animation in main window
        self.main_window.show_loading()
        
        # Show processing overlay notification
        self.overlay.show_message("Processing...", "Analyzing copied text...")
        
        # Run AI in background
        current_subject = self.main_window.current_subject
        existing_subjects = self.storage.get_subjects()
        
        self.worker = AIWorker(self.llm_service, text, current_subject, existing_subjects)
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.start()

    def on_ai_finished(self, result):
        # Hide loading animation
        self.main_window.hide_loading()
        
        # Update persistent bar status
        self.persistent_bar.set_ready()
        
        if result.get("subject") == "Error":
            self.overlay.show_message("Error", "Failed to process text.")
            self.persistent_bar.set_ready()
            return

        action = result.get("action", "keep")
        subject = result.get("subject", "Other")
        reason = result.get("reason", "")
        
        # Store result temporarily for decision
        self.pending_result = result
        
        if action == "keep" or not self.main_window.current_subject:
            # Auto-save if it matches current or no subject selected
            self.save_and_notify(result)
        elif action == "move":
            # Hide processing overlay first
            self.overlay.hide()
            # Prompt to move
            self.decision_overlay.show_decision(
                f"Move to '{subject}'?",
                f"Text doesn't fit '{self.main_window.current_subject}'. {reason}"
            )
        elif action == "create":
            # Hide processing overlay first
            self.overlay.hide()
            # Prompt to create
            self.decision_overlay.show_decision(
                f"Create '{subject}'?",
                f"New topic detected. {reason}"
            )
        else:
            # Fallback
            self.save_and_notify(result)

    def on_decision_made(self, decision):
        if not hasattr(self, 'pending_result'):
            return
            
        result = self.pending_result
        
        if decision == "yes":
            # User accepted the suggestion (move or create)
            self.save_and_notify(result)
        elif decision == "create":
            # User wants to create a completely new subject manually
            # Ensure the decision overlay is hidden immediately so it doesn't
            # interfere with the input dialog. Also pass the main window as
            # the parent so the dialog stays on top of the app.
            try:
                self.decision_overlay.hide()
            except Exception:
                pass
            text, ok = QInputDialog.getText(self.main_window, "Create New Subject", "Enter subject name:")
            if ok and text:
                result['subject'] = text
                self.save_and_notify(result)
            else:
                # Cancelled, re-show the decision overlay
                action = result.get("action", "keep")
                subject = result.get("subject", "Other")
                reason = result.get("reason", "")
                
                if action == "move":
                    self.decision_overlay.show_decision(
                        f"Move to '{subject}'?",
                        f"Text doesn't fit '{self.main_window.current_subject}'. {reason}"
                    )
                elif action == "create":
                    self.decision_overlay.show_decision(
                        f"Create '{subject}'?",
                        f"New topic detected. {reason}"
                    )
                return # Do not save yet
        else:
            # User rejected (decision == "no"), keep in current subject
            if self.main_window.current_subject:
                result['subject'] = self.main_window.current_subject
            self.save_and_notify(result)

    def save_and_notify(self, result):
        # Save note
        subject = result.get("subject", "Other")
        self.storage.save_note(result)
        
        # Update Main Window - refresh subjects list
        self.main_window.refresh_subjects()
        
        # Auto-refresh the current subject's notes if it matches the new note's subject
        self.main_window.auto_refresh_subject(subject)
        
        # Show Overlay
        summary_preview = result.get("summary", "")[:100] + "..."
        self.overlay.show_message("Summary Ready", summary_preview)
        
        # Reset persistent bar
        self.persistent_bar.set_ready()

    def run(self):
        self.main_window.show()
        # self.persistent_bar.show()  # Don't show on startup by default
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = SmartStudyApp()
    app.run()
