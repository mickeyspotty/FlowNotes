from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, Signal, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QPalette, QCursor, QMouseEvent

class PersistentOverlayBar(QWidget):
    """Always-on-top overlay bar similar to Turbo AI or Cluely"""
    show_main_window = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Window flags for always-on-top, frameless, and stays above ALL windows (including other apps)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)  # macOS specific
        
        # Make draggable
        self.dragging = False
        self.drag_position = QPoint()
        
        # Set size and position
        self.setFixedSize(280, 50)
        self.position_at_top_center()
        
        # Main container
        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: #1F2330;
                border: 1px solid #2D3436;
                border-radius: 25px;
            }
            QWidget#container:hover {
                border: 1px solid #6C5CE7;
                background-color: #252A3A;
            }
            QPushButton {
                background-color: transparent;
                color: #DFE6E9;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #2D3436;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #000000;
            }
            QLabel {
                color: #DFE6E9;
                background: transparent;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        
        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(15, 5, 15, 5)
        container_layout.setSpacing(10)
        
        # App icon/logo
        self.logo_label = QLabel("⚡")
        self.logo_label.setStyleSheet("font-size: 16px;")
        container_layout.addWidget(self.logo_label)
        
        # Status indicator
        self.status_label = QLabel("READY")
        self.status_label.setStyleSheet("""
            font-size: 10px;
            color: #00CEC9;
            font-weight: 700;
            letter-spacing: 1px;
            padding-top: 2px;
        """)
        container_layout.addWidget(self.status_label)
        
        container_layout.addStretch()
        
        # Quick action button
        self.open_button = QPushButton("OPEN APP")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #a29bfe;
            }
        """)
        self.open_button.clicked.connect(self.on_open_clicked)
        container_layout.addWidget(self.open_button)
        
        # Minimize button
        self.minimize_button = QPushButton("✕")
        self.minimize_button.setCursor(Qt.PointingHandCursor)
        self.minimize_button.clicked.connect(self.minimize_bar)
        self.minimize_button.setFixedWidth(24)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                color: #636E72;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                background: transparent;
            }
            QPushButton:hover {
                color: #FF7675;
                background: transparent;
            }
        """)
        container_layout.addWidget(self.minimize_button)
        
        # Install event filter on container to prevent click propagation
        self.container.installEventFilter(self)
        
        # Minimized state
        self.is_minimized = False
        self.full_width = 280
        self.minimized_width = 60
        
        # Hover effect
        self.setMouseTracking(True)
        self.container.setMouseTracking(True)
        
    def position_at_top_center(self):
        """Position the bar at the top center of the screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = 10  # 10px from top
        self.move(x, y)
    
    def minimize_bar(self):
        """Hide the persistent bar completely"""
        self.hide()
    
    def show_bar(self):
        """Show the persistent bar"""
        self.show()
    
    def set_status(self, status_text):
        """Update the status text"""
        self.status_label.setText(status_text)
    
    def set_processing(self):
        """Show processing state"""
        self.status_label.setText("Processing...")
        self.status_label.setStyleSheet("""
            font-size: 11px;
            color: #6B6B8D;
            font-weight: 600;
        """)
    
    def set_ready(self):
        """Show ready state"""
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("""
            font-size: 11px;
            color: #B8B8D1;
            font-weight: 500;
        """)
    
    def on_open_clicked(self):
        print("Open button clicked")
        self.show_main_window.emit()
        self.hide()  # Hide the bar when opening the app

    def minimize_bar(self):
        print("Minimize button clicked")
        self.show_main_window.emit()  # Show main window when hiding bar
        self.hide()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging - but don't open app"""
        if event.button() == Qt.LeftButton:
            # Check what is under the mouse
            child = self.childAt(event.position().toPoint())
            
            # If we clicked a button, it handles the event itself (usually).
            # If we clicked a label or the container, we need to decide.
            
            # If we clicked a button (or something inside it), we shouldn't drag.
            # We should just let the button handle it (if it didn't already).
            # Since we are in the parent's mousePressEvent, it implies the child 
            # might have ignored it OR we are catching it bubbling up.
            # But for QPushButton, it usually consumes the event.
            
            # To be safe: if it's a button, do nothing (don't drag).
            if isinstance(child, QPushButton):
                return

            # If it's a label, consume the event so it doesn't propagate, but don't drag.
            if isinstance(child, QLabel):
                event.accept()
                return
            
            # If we are here, we clicked the background (container or self).
            # Start dragging.
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle dragging"""
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
    
    def enterEvent(self, event):
        """Hover effect - slight glow"""
        self.container.setStyleSheet("""
            QWidget#container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(61, 61, 92, 250), 
                    stop:1 rgba(77, 77, 108, 250));
                border: 1px solid rgba(107, 107, 141, 220);
                border-radius: 25px;
            }
            QPushButton {
                background-color: transparent;
                color: #E8E8F5;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(107, 107, 141, 100);
            }
            QPushButton:pressed {
                background-color: rgba(107, 107, 141, 150);
            }
            QLabel {
                color: #E8E8F5;
                background: transparent;
            }
        """)
    
    def leaveEvent(self, event):
        """Remove hover effect"""
        self.container.setStyleSheet("""
            QWidget#container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(45, 45, 74, 240), 
                    stop:1 rgba(61, 61, 92, 240));
                border: 1px solid rgba(107, 107, 141, 180);
                border-radius: 25px;
            }
            QPushButton {
                background-color: transparent;
                color: #E8E8F5;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(107, 107, 141, 100);
            }
            QPushButton:pressed {
                background-color: rgba(107, 107, 141, 150);
            }
            QLabel {
                color: #E8E8F5;
                background: transparent;
            }
        """)


class OverlayWindow(QWidget):
    """Notification overlay for showing summaries"""
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 130)

        # UI Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: #1F2330;
                border-radius: 16px;
                border: 1px solid #2D3436;
            }
            QLabel {
                color: #DFE6E9;
            }
        """)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 20, 25, 20)
        self.container_layout.setSpacing(10)

        self.title_label = QLabel("SUMMARY READY", self.container)
        self.title_label.setStyleSheet("""
            font-weight: 700; 
            font-size: 12px; 
            color: #00CEC9;
            letter-spacing: 1px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
        
        self.preview_label = QLabel("Processing...", self.container)
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("""
            font-size: 14px; 
            color: #DFE6E9;
            line-height: 1.4;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

        self.container_layout.addWidget(self.title_label)
        self.container_layout.addWidget(self.preview_label)
        self.layout.addWidget(self.container)

        # Animation Setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.slide_out)
        
        # Add cursor pointer on hover
        self.setCursor(Qt.PointingHandCursor)

    def show_message(self, title, preview):
        self.title_label.setText(title)
        self.preview_label.setText(preview)
        
        # Position at bottom right
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y_start = screen_geometry.height()
        y_end = screen_geometry.height() - self.height() - 20

        self.setGeometry(x, y_start, self.width(), self.height())
        self.show()

        self.animation.setStartValue(QRect(x, y_start, self.width(), self.height()))
        self.animation.setEndValue(QRect(x, y_end, self.width(), self.height()))
        self.animation.start()

        self.hide_timer.start(4000)  # Hide after 4 seconds

    def slide_out(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = self.x()
        y_start = self.y()
        y_end = screen_geometry.height()

        self.animation.setStartValue(QRect(x, y_start, self.width(), self.height()))
        self.animation.setEndValue(QRect(x, y_end, self.width(), self.height()))
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def mousePressEvent(self, event):
        self.clicked.emit()
        self.hide()

    def hideEvent(self, event):
        self.hide_timer.stop()
        super().hideEvent(event)

class DecisionOverlay(QWidget):
    """Overlay for user decisions (Move/Create subject)"""
    decision_made = Signal(str)  # "yes", "no", "create"

    def __init__(self):
        super().__init__()

        # Make this overlay non-activating so it doesn't steal focus from
        # active app, but allow interaction.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedWidth(420)

        # UI Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: #1F2330;
                border-radius: 16px;
                border: 1px solid #FD79A8;
            }
            QLabel {
                color: #DFE6E9;
            }
        """)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 20, 25, 20)
        self.container_layout.setSpacing(15)

        self.title_label = QLabel("SUGGESTION", self.container)
        self.title_label.setStyleSheet("""
            font-weight: 700; 
            font-size: 12px; 
            color: #FD79A8;
            letter-spacing: 1px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

        self.question_label = QLabel("Question text here?", self.container)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            font-size: 14px; 
            color: #FFFFFF;
            font-weight: 600;
            line-height: 1.4;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

        self.reason_label = QLabel("Reasoning text here.", self.container)
        self.reason_label.setWordWrap(True)
        self.reason_label.setStyleSheet("""
            font-size: 12px; 
            color: #B2BEC3;
            font-style: italic;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.yes_button = QPushButton("Yes, do it")
        self.yes_button.setCursor(Qt.PointingHandCursor)
        self.yes_button.setStyleSheet("""
            QPushButton {
                background-color: #FD79A8;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e84393;
            }
        """)
        self.yes_button.clicked.connect(lambda: self.make_decision("yes"))

        self.no_button = QPushButton("No, keep here")
        self.no_button.setCursor(Qt.PointingHandCursor)
        self.no_button.setStyleSheet("""
            QPushButton {
                background-color: #2D3436;
                color: #DFE6E9;
                border: 1px solid #636E72;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #636E72;
                color: #FFFFFF;
            }
        """)
        self.no_button.clicked.connect(lambda: self.make_decision("no"))

        self.create_button = QPushButton("Create New")
        self.create_button.setCursor(Qt.PointingHandCursor)
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #2D3436;
                color: #DFE6E9;
                border: 1px solid #00CEC9;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #00CEC9;
                color: #000000;
            }
        """)
        self.create_button.clicked.connect(lambda: self.make_decision("create"))

        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.yes_button)

        self.container_layout.addWidget(self.title_label)
        self.container_layout.addWidget(self.question_label)
        self.container_layout.addWidget(self.reason_label)
        self.container_layout.addLayout(button_layout)
        self.layout.addWidget(self.container)

        # Animation Setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def show_decision(self, question, reason):
        self.question_label.setText(question)
        self.reason_label.setText(reason)

        # Disconnect any previous finished signal to prevent accidental hiding
        try:
            self.animation.finished.disconnect()
        except:
            pass

        # Position at bottom right (above regular overlay if needed, or same place)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y_start = screen_geometry.height()
        y_end = screen_geometry.height() - self.height() - 20

        self.setGeometry(x, y_start, self.width(), self.sizeHint().height())
        # show without activating keeps focus with the previous widget
        self.show()
        self.adjustSize()
        self.raise_()  # Ensure it's on top

        # Recalculate y_end with new height
        y_end = screen_geometry.height() - self.height() - 20

        self.animation.setStartValue(QRect(x, y_start, self.width(), self.height()))
        self.animation.setEndValue(QRect(x, y_end, self.width(), self.height()))
        self.animation.start()

    def make_decision(self, decision):
        self.decision_made.emit(decision)
        self.hide_overlay()

    def hide_overlay(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = self.x()
        y_start = self.y()
        y_end = screen_geometry.height()

        self.animation.setStartValue(QRect(x, y_start, self.width(), self.height()))
        self.animation.setEndValue(QRect(x, y_end, self.width(), self.height()))
        self.animation.finished.connect(self.hide)
        self.animation.start()
