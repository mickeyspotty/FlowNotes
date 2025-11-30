from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QListWidget, QTextEdit, QLabel, QPushButton, QSplitter, 
                               QMessageBox, QScrollArea, QFrame, QGraphicsDropShadowEffect,
                               QListWidgetItem, QSizePolicy, QLineEdit, QCheckBox)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QRect, QEasingCurve, Property, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QPixmap
from app.ui.settings import SettingsDialog
from app.notes.storage import NoteStorage
import hashlib

class ToggleSwitch(QCheckBox):
    """Custom toggle switch widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self.setCursor(Qt.PointingHandCursor)
        
        # Animation state
        self._circle_position = 4
        self._target_position = 4
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(10)  # Update every 10ms
        self.animation_timer.timeout.connect(self._animate_step)
        
        # Connect state change to start animation
        self.toggled.connect(self._on_toggle)
        
    def _on_toggle(self, checked):
        """Start animation when toggled"""
        if checked:
            self._target_position = 32
        else:
            self._target_position = 4
        
        if not self.animation_timer.isActive():
            self.animation_timer.start()
    
    def _animate_step(self):
        """Animate one step towards target position"""
        # Calculate step size (smooth easing)
        diff = self._target_position - self._circle_position
        
        if abs(diff) < 1:
            # Close enough, snap to target
            self._circle_position = self._target_position
            self.animation_timer.stop()
        else:
            # Move towards target (ease out)
            self._circle_position += diff * 0.2
        
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background track
        if self.isChecked():
            painter.setBrush(QColor("#00CEC9"))
        else:
            painter.setBrush(QColor("#2D3436"))
        
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 60, 30, 15, 15)
        
        # Draw toggle circle with animated position
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(int(self._circle_position), 3, 24, 24)
    
    def hitButton(self, pos):
        # Make entire widget clickable
        return self.contentsRect().contains(pos)

class FlipCard(QFrame):
    """Simple flashcard widget without animation — click toggles instantly."""
    def __init__(self, question, answer, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer
        self.is_flipped = False

        self.setStyleSheet("""
            QFrame {
                background-color: #1F2330;
                border: 1px solid #2D3436;
                border-radius: 12px;
                padding: 15px;
            }
            QFrame:hover {
                border: 1px solid #6C5CE7;
                background-color: #252A3A;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)

        # Simple shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.label = QLabel(f"<div style='color: #A29BFE; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px;'>QUESTION</div><div style='color: #FFFFFF; font-size: 14px; font-weight: 500;'>{question}</div>")
        self.label.setWordWrap(True)
        self.label.setStyleSheet("line-height: 1.4;")
        layout.addWidget(self.label)

    def mousePressEvent(self, event):
        # Toggle instantly without animation
        self.is_flipped = not self.is_flipped
        if self.is_flipped:
            self.label.setText(f"<div style='color: #00CEC9; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px;'>ANSWER</div><div style='color: #DFE6E9; font-size: 14px; font-style: italic;'>{self.answer}</div>")
        else:
            self.label.setText(f"<div style='color: #A29BFE; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px;'>QUESTION</div><div style='color: #FFFFFF; font-size: 14px; font-weight: 500;'>{self.question}</div>")

class LoadingOverlay(QWidget):
    """Loading overlay with fun animated emojis"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 17, 26, 200);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Emoji label
        self.emoji_label = QLabel("🧠", self)
        self.emoji_label.setStyleSheet("""
            font-size: 48px;
        """)
        self.emoji_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.emoji_label)
        
        # Text label
        self.label = QLabel("Thinking...", self)
        self.label.setStyleSheet("""
            color: #DFE6E9;
            font-size: 18px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            margin-top: 10px;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Animation state
        self.emojis = ["🧠", "💡", "✨", "🚀", "⚡", "🎯"]
        self.messages = [
            "Thinking...",
            "Analyzing...",
            "Processing...",
            "Almost there...",
            "Generating insights...",
            "Creating magic..."
        ]
        self.colors = ["#6C5CE7", "#00CEC9", "#FD79A8", "#FAB1A0", "#74B9FF", "#FFEAA7"]
        self.index = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
    def start(self):
        self.show()
        self.index = 0
        self.timer.start(500)  # Change every 500ms
        
    def stop(self):
        self.timer.stop()
        self.hide()
        
    def update_animation(self):
        # Cycle through emojis and messages
        self.emoji_label.setText(self.emojis[self.index])
        self.label.setText(self.messages[self.index])
        
        # Update text color
        self.label.setStyleSheet(f"""
            color: {self.colors[self.index]};
            font-size: 18px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            margin-top: 10px;
        """)
        
        self.index = (self.index + 1) % len(self.emojis)

class MainWindow(QMainWindow):
    # Subject color palette
    SUBJECT_COLORS = [
        "#6C5CE7",  # Electric Indigo
        "#00CEC9",  # Mint Green
        "#FD79A8",  # Pink
        "#FAB1A0",  # Peach
        "#74B9FF",  # Blue
        "#A29BFE",  # Lavender
        "#FFEAA7",  # Cream
        "#55EFC4",  # Teal
    ]
    
    # Subject icons (emoji)
    SUBJECT_ICONS = {
        "math": "📐",
        "science": "🔬",
        "history": "📜",
        "english": "📚",
        "computer": "💻",
        "biology": "🧬",
        "chemistry": "🧪",
        "physics": "⚛️",
        "geography": "🌍",
        "art": "🎨",
        "music": "🎵",
        "default": "📝"
    }
    
    def __init__(self, storage: NoteStorage, llm_service, persistent_bar=None):
        super().__init__()
        self.storage = storage
        self.llm_service = llm_service
        self.persistent_bar = persistent_bar  # Reference to persistent overlay bar
        self.setWindowTitle("FlowNotes")
        self.resize(1100, 750)
        self.current_subject = None
        self.subject_colors = {}  # Cache for subject colors
        
        # Apply Deep Space theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F111A;
            }
            QWidget {
                background-color: #0F111A;
                color: #DFE6E9;
                font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: #0F111A;
            }
            QLabel {
                color: #DFE6E9;
            }
            QSplitter::handle {
                background-color: #161925;
                width: 1px;
            }
        """)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar (Subjects)
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(20, 25, 20, 25)
        self.sidebar_layout.setSpacing(15)
        
        # Sidebar title
        sidebar_title = QLabel("SUBJECTS")
        sidebar_title.setStyleSheet("""
            font-size: 12px;
            font-weight: 700;
            color: #636E72;
            letter-spacing: 1px;
            padding-bottom: 10px;
        """)
        
        self.subject_list = QListWidget()
        self.subject_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.subject_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.subject_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-radius: 10px;
                margin-bottom: 5px;
                color: #B2BEC3;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background-color: #1F2330;
                color: #FFFFFF;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C5CE7, stop:1 #a29bfe);
                color: #FFFFFF;
                font-weight: 600;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #161925;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #2D3436;
                border-radius: 4px;
                min-height: 30px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #636E72;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.subject_list.itemClicked.connect(self.load_notes_for_subject)
        
        # Common Button Style
        btn_style = """
            QPushButton {
                background-color: #1F2330;
                color: #DFE6E9;
                border: 1px solid #2D3436;
                border-radius: 10px;
                padding: 12px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #2D3436;
                border: 1px solid #636E72;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #000000;
            }
        """
        
        self.export_button = QPushButton("📤  Export All Notes")
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.setStyleSheet(btn_style)
        self.export_button.clicked.connect(self.export_notes)
        
        # Clipboard monitoring toggle with switch
        monitoring_container = QWidget()
        monitoring_layout = QHBoxLayout(monitoring_container)
        monitoring_layout.setContentsMargins(15, 10, 15, 10)
        monitoring_layout.setSpacing(10)
        
        monitoring_label = QLabel("Clipboard\nMonitoring")
        monitoring_label.setWordWrap(True)
        monitoring_label.setStyleSheet("""
            color: #DFE6E9;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            line-height: 1.2;
        """)
        
        self.monitoring_switch = ToggleSwitch()
        self.monitoring_switch.setChecked(True)  # Start enabled
        self.monitoring_switch.toggled.connect(self.toggle_monitoring)
        
        monitoring_layout.addWidget(monitoring_label)
        monitoring_layout.addStretch()
        monitoring_layout.addWidget(self.monitoring_switch)
        
        monitoring_container.setStyleSheet("""
            QWidget {
                background-color: #1F2330;
                border: 1px solid #2D3436;
                border-radius: 10px;
            }
            QWidget:hover {
                background-color: #2D3436;
                border: 1px solid #636E72;
            }
        """)
        
        self.settings_button = QPushButton("⚙️  Settings")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet(btn_style)
        self.settings_button.clicked.connect(self.open_settings)
        
        self.show_overlay_button = QPushButton("👁️  Show Overlay Bar")
        self.show_overlay_button.setCursor(Qt.PointingHandCursor)
        self.show_overlay_button.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #a29bfe;
            }
        """)
        self.show_overlay_button.clicked.connect(self.show_overlay_bar)

        self.sidebar_layout.addWidget(sidebar_title)
        self.sidebar_layout.addWidget(self.subject_list)
        self.sidebar_layout.addStretch() # Push buttons to bottom
        self.sidebar_layout.addWidget(self.export_button)
        self.sidebar_layout.addWidget(monitoring_container)
        self.sidebar_layout.addWidget(self.show_overlay_button)
        self.sidebar_layout.addWidget(self.settings_button)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.sidebar_layout)
        sidebar_widget.setFixedWidth(260)
        sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: #161925;
                border-right: 1px solid #2D3436;
            }
        """)

        # Notes Area
        self.notes_area = QScrollArea()
        self.notes_area.setWidgetResizable(True)
        self.notes_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.notes_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0F111A;
            }
            QScrollBar:vertical {
                background-color: #0F111A;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #2D3436;
                border-radius: 4px;
                min-height: 30px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #636E72;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.notes_container = QWidget()
        self.notes_container.setStyleSheet("background-color: #0F111A;")
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setAlignment(Qt.AlignTop)
        self.notes_layout.setContentsMargins(30, 30, 30, 30)
        self.notes_layout.setSpacing(20)
        self.notes_area.setWidget(self.notes_container)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(self.notes_area)
        splitter.setStretchFactor(1, 1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #161925;
                width: 1px;
            }
        """)

        main_layout.addWidget(splitter)
        
        # Loading overlay
        self.loading_overlay = LoadingOverlay(central_widget)
        self.loading_overlay.hide()
        self.loading_overlay.setGeometry(central_widget.rect())

        self.refresh_subjects()
        
    def resizeEvent(self, event):
        """Resize loading overlay with window"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(self.centralWidget().rect())

    def show_loading(self):
        """Show loading animation"""
        self.loading_overlay.start()
        
    def hide_loading(self):
        """Hide loading animation"""
        self.loading_overlay.stop()
    
    def get_subject_color(self, subject):
        """Get consistent color for a subject"""
        if subject not in self.subject_colors:
            # Use hash to get consistent color
            hash_val = int(hashlib.md5(subject.encode()).hexdigest(), 16)
            color_idx = hash_val % len(self.SUBJECT_COLORS)
            self.subject_colors[subject] = self.SUBJECT_COLORS[color_idx]
        return self.subject_colors[subject]
    
    def get_subject_icon(self, subject):
        """Get icon for subject"""
        subject_lower = subject.lower()
        for key, icon in self.SUBJECT_ICONS.items():
            if key in subject_lower:
                return icon
        return self.SUBJECT_ICONS["default"]

    def refresh_subjects(self):
        self.subject_list.clear()
        subjects = self.storage.get_subjects()
        for subject in subjects:
            icon = self.get_subject_icon(subject)
            item = QListWidgetItem(f"{icon}  {subject}")
            item.setData(Qt.UserRole, subject)  # Store actual subject name
            self.subject_list.addItem(item)

    def load_notes_for_subject(self, item):
        subject = item.data(Qt.UserRole)
        self.current_subject = subject
        self._display_notes_for_subject(subject)

    def auto_refresh_subject(self, subject):
        """Auto-refresh notes for a specific subject when new content is added"""
        if self.current_subject == subject:
            self._display_notes_for_subject(subject)
        
        # Update subject list
        items = self.subject_list.findItems(f"*{subject}", Qt.MatchWildcard)
        if items:
            self.subject_list.setCurrentItem(items[0])
            if self.current_subject is None:
                self.current_subject = subject
                self._display_notes_for_subject(subject)

    def _display_notes_for_subject(self, subject):
        """Internal method to display notes for a subject"""
        notes = self.storage.get_notes_for_subject(subject)
        
        # Clear existing notes
        for i in reversed(range(self.notes_layout.count())): 
            self.notes_layout.itemAt(i).widget().setParent(None)

        subject_color = self.get_subject_color(subject)
        
        for note in notes:
            note_widget = self.create_note_widget(note, subject_color)
            self.notes_layout.addWidget(note_widget)
            
            # Fade-in animation
            note_widget.setWindowOpacity(0.0)
            fade_in = QPropertyAnimation(note_widget, b"windowOpacity")
            fade_in.setDuration(400)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.OutCubic)
            fade_in.start()

    def create_note_widget(self, note, subject_color):
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        # Use a slightly lighter background for the card
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: #161925;
                border: 1px solid #2D3436;
                border-radius: 16px;
                padding: 25px;
            }}
            QFrame:hover {{
                border: 1px solid {subject_color};
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        widget.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Timestamp
        timestamp = QLabel(f"<span style='color: #636E72; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>{note.get('timestamp')}</span>")
        layout.addWidget(timestamp)

        # Summary
        summary_label = QLabel(f"<div style='color: #A29BFE; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;'>SUMMARY</div><div style='color: #FFFFFF; font-size: 15px; line-height: 1.6;'>{note.get('summary')}</div>")
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("background: transparent; border: none; padding: 0;")
        layout.addWidget(summary_label)

        # Key Points
        if note.get('keyPoints'):
            points_html = "<div style='color: #00CEC9; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-top: 10px; margin-bottom: 8px;'>KEY POINTS</div><ul style='margin: 0; padding-left: 20px; color: #DFE6E9;'>"
            for p in note['keyPoints']:
                points_html += f"<li style='margin-bottom: 6px; font-size: 14px; line-height: 1.5;'>{p}</li>"
            points_html += "</ul>"
            points_label = QLabel(points_html)
            points_label.setWordWrap(True)
            points_label.setStyleSheet("background: transparent; border: none; padding: 0;")
            layout.addWidget(points_label)

        # Flashcards
        if note.get('flashcards'):
            fc_title = QLabel("<div style='margin-top: 15px; margin-bottom: 10px;'><span style='color: #FD79A8; font-size: 12px; font-weight: 700; text-transform: uppercase;'>FLASHCARDS</span> <span style='color: #636E72; font-size: 11px;'>(Click to flip)</span></div>")
            layout.addWidget(fc_title)
            
            # Container for flashcards
            flashcards_container = QWidget()
            flashcards_container.setStyleSheet("background: transparent; border: none; padding: 0;")
            flashcards_layout = QVBoxLayout(flashcards_container)
            flashcards_layout.setContentsMargins(0, 0, 0, 0)
            flashcards_layout.setSpacing(10)
            
            for fc in note['flashcards']:
                flip_card = FlipCard(fc.get('q'), fc.get('a'))
                flashcards_layout.addWidget(flip_card)
            
            layout.addWidget(flashcards_container)
            
            # Generate More Flashcards button
            more_fc_button = QPushButton("✨  Generate More Flashcards")
            more_fc_button.setCursor(Qt.PointingHandCursor)
            more_fc_button.setStyleSheet("""
                QPushButton {
                    background-color: #2D3436;
                    color: #DFE6E9;
                    border: 1px solid #636E72;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: #636E72;
                    color: #FFFFFF;
                    border: 1px solid #FFFFFF;
                }
                QPushButton:pressed {
                    background-color: #000000;
                }
            """)
            more_fc_button.clicked.connect(
                lambda checked, n=note, container=flashcards_layout: self.generate_more_flashcards(n, container)
            )
            layout.addWidget(more_fc_button)

        return widget
    
    def generate_more_flashcards(self, note, flashcards_layout):
        """Generate additional flashcards for a note"""
        summary = note.get('summary', '')
        key_points = note.get('keyPoints', [])
        
        if not summary:
            return
        
        # Show loading state
        self.show_loading()
        
        # Generate flashcards in background
        from PySide6.QtCore import QThread, Signal
        
        class FlashcardWorker(QThread):
            finished = Signal(list)
            
            def __init__(self, llm_service, summary, key_points):
                super().__init__()
                self.llm_service = llm_service
                self.summary = summary
                self.key_points = key_points
            
            def run(self):
                flashcards = self.llm_service.generate_more_flashcards(
                    self.summary, self.key_points, count=4
                )
                self.finished.emit(flashcards)
        
        def on_flashcards_generated(flashcards):
            self.hide_loading()
            if flashcards:
                # Add new flashcards to the layout with fade-in animation
                for fc in flashcards:
                    flip_card = FlipCard(fc.get('q'), fc.get('a'))
                    flashcards_layout.addWidget(flip_card)
                    
                    # Fade-in animation
                    flip_card.setWindowOpacity(0.0)
                    fade_in = QPropertyAnimation(flip_card, b"windowOpacity")
                    fade_in.setDuration(400)
                    fade_in.setStartValue(0.0)
                    fade_in.setEndValue(1.0)
                    fade_in.setEasingCurve(QEasingCurve.OutCubic)
                    fade_in.start()
                
                # Update the note data
                if 'flashcards' not in note:
                    note['flashcards'] = []
                note['flashcards'].extend(flashcards)
        
        worker = FlashcardWorker(self.llm_service, summary, key_points)
        worker.finished.connect(on_flashcards_generated)
        worker.start()
        self.flashcard_worker = worker  # Keep reference to prevent garbage collection

    def open_settings(self):
        current_key = self.llm_service.api_key or ""
        dialog = SettingsDialog(self, current_key, self.storage)
        dialog.notes_cleared.connect(self.on_notes_cleared)
        if dialog.exec():
            new_key = dialog.get_api_key()
            self.llm_service.set_api_key(new_key)
            # Save key to config file (simplified for now)
            with open("config.json", "w") as f:
                import json
                json.dump({"api_key": new_key}, f)
    
    def on_notes_cleared(self):
        """Refresh UI after notes are cleared"""
        self.current_subject = None
        self.refresh_subjects()
        # Clear the notes display area
        for i in reversed(range(self.notes_layout.count())): 
            self.notes_layout.itemAt(i).widget().setParent(None)

    def export_notes(self):
        try:
            self.storage.export_all_to_markdown("all_notes.md")
            QMessageBox.information(self, "Export Successful", "Notes exported to all_notes.md")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
    
    
    def show_overlay_bar(self):
        """Show the persistent overlay bar and minimize main window"""
        if self.persistent_bar:
            self.persistent_bar.show_bar()
            self.hide()  # Hide/minimize the main window
    
    
    def toggle_monitoring(self, checked):
        """Toggle clipboard monitoring on/off based on switch state"""
        # The switch is checked when monitoring is enabled
        pass  # monitoring_switch.isChecked() is automatically used in main.py
