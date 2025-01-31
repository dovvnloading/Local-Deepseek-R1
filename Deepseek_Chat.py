from PyQt5.QtGui import QCursor, QIcon, QPixmap
import markdown
from PyQt5.QtWidgets import (QApplication, QComboBox, QMainWindow, QMenu, QScrollArea, QSplashScreen, 
                           QSystemTrayIcon, QWidget, QTextEdit, QPushButton, QLabel, 
                           QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy, QInputDialog, 
                           QMessageBox)
from PyQt5.QtCore import QEvent, QPoint, QPropertyAnimation, QRect, QSize, QTimer, Qt, QThread, pyqtSignal
import sys
import ollama
import re
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime
from pathlib import Path
import uuid
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

# Define the scrollbar style
SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        border: none;
        background: #2D2D2D;
        width: 10px;
        margin: 0;
        border-radius: 0;
    }
    QScrollBar::handle:vertical {
        background: #404040;
        min-height: 20px;
        border-radius: 5px;
        margin: 2px;
    }
    QScrollBar::add-line:vertical {
        height: 0px;
        background: none;
        border: none;
    }
    QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
        border: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
        border: none;
    }
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
        background: none;
        border: none;
    }
    QScrollBar:horizontal {
        border: none;
        background: #2D2D2D;
        height: 10px;
        margin: 0;
        border-radius: 0;
    }
    QScrollBar::handle:horizontal {
        background: #404040;
        min-width: 20px;
        border-radius: 5px;
        margin: 2px;
    }
    QScrollBar::add-line:horizontal {
        width: 0px;
        background: none;
        border: none;
    }
    QScrollBar::sub-line:horizontal {
        width: 0px;
        background: none;
        border: none;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
        border: none;
    }
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
        background: none;
        border: none;
    }
"""

class ChatManager:
    def __init__(self):
        self.app_data_dir = self._get_app_data_dir()
        self.chats_dir = self.app_data_dir / 'chats'
        self.active_chat_id = None
        self.chats_metadata = {}
        self._initialize_directories()
        self._load_chats_metadata()
        
        # Initialize first chat if no chats exist
        if not self.chats_metadata:
            self.create_new_chat()

    def _get_app_data_dir(self):
        """Get the appropriate application data directory based on the OS."""
        if os.name == 'nt':  # Windows
            app_data = Path(os.getenv('APPDATA'))
            return app_data / 'DeepseekChat'
        else:  # Unix-like
            home = Path.home()
            return home / '.deepseek-chat'

    def _initialize_directories(self):
        """Create necessary directories if they don't exist."""
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.chats_dir.mkdir(exist_ok=True)
        
        # Create metadata file if it doesn't exist
        metadata_file = self.app_data_dir / 'chats_metadata.json'
        if not metadata_file.exists():
            with open(metadata_file, 'w') as f:
                json.dump({}, f)

    def _load_chats_metadata(self):
        """Load chat metadata from the metadata file."""
        try:
            with open(self.app_data_dir / 'chats_metadata.json', 'r') as f:
                self.chats_metadata = json.load(f)
        except FileNotFoundError:
            self.chats_metadata = {}

    def _save_chats_metadata(self):
        """Save chat metadata to the metadata file."""
        with open(self.app_data_dir / 'chats_metadata.json', 'w') as f:
            json.dump(self.chats_metadata, f, indent=2)

    def create_new_chat(self):
        """Create a new chat and return its ID."""
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Initialize chat metadata
        self.chats_metadata[chat_id] = {
            'created_at': timestamp,
            'updated_at': timestamp,
            'title': f'Chat {len(self.chats_metadata) + 1}',
            'messages': []
        }
        
        # Save empty chat file
        chat_file = self.chats_dir / f'{chat_id}.json'
        with open(chat_file, 'w') as f:
            json.dump({'messages': []}, f)
        
        self._save_chats_metadata()
        self.active_chat_id = chat_id  # Set as active chat
        return chat_id, self.chats_metadata[chat_id]['title']

    def load_chat(self, chat_id):
        """Load a chat's messages by ID."""
        try:
            chat_file = self.chats_dir / f'{chat_id}.json'
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)
            self.active_chat_id = chat_id
            return chat_data['messages']
        except FileNotFoundError:
            raise Exception(f"Chat {chat_id} not found")

    def save_message(self, role, content):
        """Save a new message to the current chat."""
        if not self.active_chat_id:
            raise Exception("No active chat")
        
        timestamp = datetime.now().isoformat()
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp
        }
        
        # Update chat file
        chat_file = self.chats_dir / f'{self.active_chat_id}.json'
        try:
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)
        except FileNotFoundError:
            chat_data = {'messages': []}
        
        chat_data['messages'].append(message)
        
        with open(chat_file, 'w') as f:
            json.dump(chat_data, f, indent=2)
        
        # Update metadata
        self.chats_metadata[self.active_chat_id]['updated_at'] = timestamp
        if 'messages' not in self.chats_metadata[self.active_chat_id]:
            self.chats_metadata[self.active_chat_id]['messages'] = []
        self.chats_metadata[self.active_chat_id]['messages'].append(message)
        self._save_chats_metadata()

    def get_chat_list(self):
        """Get list of all chats with metadata."""
        return [(chat_id, data['title'], data['updated_at']) 
                for chat_id, data in self.chats_metadata.items()]

    def update_chat_title(self, chat_id, new_title):
        """Update the title of a chat."""
        if chat_id not in self.chats_metadata:
            raise Exception(f"Chat {chat_id} not found")
        
        self.chats_metadata[chat_id]['title'] = new_title
        self.chats_metadata[chat_id]['updated_at'] = datetime.now().isoformat()
        self._save_chats_metadata()

    def delete_chat(self, chat_id):
        """Delete a chat and its metadata."""
        if chat_id not in self.chats_metadata:
            raise Exception(f"Chat {chat_id} not found")
        
        # Remove chat file
        chat_file = self.chats_dir / f'{chat_id}.json'
        try:
            chat_file.unlink()
        except FileNotFoundError:
            pass
        
        # Remove from metadata
        del self.chats_metadata[chat_id]
        self._save_chats_metadata()
        
        if self.active_chat_id == chat_id:
            self.active_chat_id = None

class SplashScreen(QSplashScreen):
    def __init__(self):
        logo_path = r"C:\Users\Admin\source\repos\Deepseek-Chat\asset\DeepSeek_logo.svg.png"
        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                 (screen.height() - self.height()) // 2)

class ChatDisplay(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.page().loadFinished.connect(self._on_load_finished)
        self.setHtml(self._get_template())
        self._pending_update = None
        
    def _get_template(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <script>
                let isReady = false;
                
                MathJax = {
                    tex: {
                        inlineMath: [['$', '$'], ['\\(', '\\)']],
                        displayMath: [['$$', '$$'], ['\\[', '\\]']]
                    },
                    svg: {
                        fontCache: 'global'
                    }
                };
                
                document.addEventListener('DOMContentLoaded', function() {
                    isReady = true;
                    if (window.pendingContent !== undefined) {
                        updateContent(window.pendingContent);
                        window.pendingContent = undefined;
                    }
                });

                function updateContent(content) {
                    if (!isReady) return false;
                    const container = document.getElementById('chat-container');
                    if (!container) return false;
                    
                    container.innerHTML = content;
                    
                    if (typeof MathJax !== 'undefined') {
                        MathJax.typesetPromise && MathJax.typesetPromise();
                    }
                    
                    window.scrollTo(0, document.body.scrollHeight);
                    return true;
                }
            </script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js"></script>
            <style>
                body { 
                    background-color: #2D2D2D;
                    color: #E0E0E0;
                    font-family: 'Segoe UI', sans-serif;
                    padding: 20px;
                    margin: 0;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }
                /* Scrollbar Styling */
                ::-webkit-scrollbar {
                    width: 10px;
                    height: 10px;
                    background: #2D2D2D;
                    border: none;
                    border-radius: 0;
                }
                ::-webkit-scrollbar-thumb {
                    background: #404040;
                    min-height: 20px;
                    min-width: 20px;
                    border-radius: 5px;
                    margin: 2px;
                }
                ::-webkit-scrollbar-corner,
                ::-webkit-scrollbar-track,
                ::-webkit-scrollbar-track-piece {
                    background: none;
                    border: none;
                }
                ::-webkit-scrollbar-button,
                ::-webkit-scrollbar-track-piece,
                ::-webkit-scrollbar-corner,
                ::-webkit-resizer {
                    display: none;
                }
                /* End Scrollbar Styling */
                
                #chat-container {
                    width: 100%;
                    max-width: 100%;
                }
                .message {
                    margin: 15px 0;
                    padding: 15px;
                    border-radius: 8px;
                    background-color: #252525;
                }
                .message-header {
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-size: 14px;
                }
                .message-content {
                    margin-left: 10px;
                    line-height: 1.6;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    font-size: 14px;
                }
                .user-message {
                    border-left: 4px solid #0078D4;
                }
                .user-message .message-header {
                    color: #0078D4;
                }
                .ai-message {
                    border-left: 4px solid #4EC9B0;
                }
                .ai-message .message-header {
                    color: #4EC9B0;
                }
                .message-content p {
                    margin: 8px 0;
                }
                .message-content strong {
                    color: #CE9178;
                    font-weight: bold;
                }
                .message-content em {
                    color: #4EC9B0;
                    font-style: italic;
                }
                .message-content code {
                    background-color: #1E1E1E;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Consolas', monospace;
                    font-size: 13px;
                    color: #D4D4D4;
                }
                pre {
                    background-color: #1E1E1E;
                    padding: 12px;
                    border-radius: 6px;
                    margin: 10px 0;
                    font-family: 'Consolas', monospace;
                    font-size: 13px;
                    color: #D4D4D4;
                    white-space: pre-wrap;
                }
                .mathjax-content {
                    font-size: 14px;
                }
                .MathJax {
                    color: #E0E0E0 !important;
                }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
        </body>
        </html>
        '''

    def _on_load_finished(self, ok):
        if ok and self._pending_update is not None:
            self._do_update(self._pending_update)
            self._pending_update = None

    def _do_update(self, content):
        """Perform the actual update of the content."""
        escaped_content = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        script = f'''
            (function() {{
                if (!updateContent(`{escaped_content}`)) {{
                    window.pendingContent = `{escaped_content}`;
                }}
            }})();
        '''
        self.page().runJavaScript(script)

    def append(self, html_content):
        """Add new message to chat display."""
        self.messages.append(html_content)
        self._update_display()

    def clear(self):
        """Clear all messages from display."""
        self.messages = []
        self._update_display()

    def _update_display(self):
        """Update the web view with all messages."""
        chat_html = ''.join(self.messages)
        self._do_update(chat_html)

class MessageInput(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.setPlaceholderText("Type your message...")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: none;
                padding: 2px;
            }}
            {SCROLLBAR_STYLE}
        """)

class ModelSelector(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        
        # Add model options
        self.models = [
            "deepseek-r1:7b (default)",
            "deepseek-r1:1.5b",
            "deepseek-r1:8b", 
            "deepseek-r1:14b",
            "deepseek-r1:32b",
            "deepseek-r1:70b",
            "deepseek-r1:671b"
        ]
        self.addItems(self.models)
        
        # Style the dropdown
        self.setStyleSheet("""
            QComboBox {
                background-color: #252525;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 2px 8px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #E0E0E0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                color: #E0E0E0;
                selection-background-color: #404040;
                selection-color: #E0E0E0;
                border: 1px solid #404040;
            }
        """)

    def get_selected_model(self):
        """Get clean model name without '(default)' suffix"""
        return self.currentText().split(" ")[0]

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setFixedHeight(32)
        self.setStyleSheet("background-color: #1A1A1A; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 5, 0)
        
        # Add icon
        icon_label = QLabel()
        icon_pixmap = QPixmap(r"C:\Users\Admin\source\repos\Deepseek-Chat\asset\whaaaaaaaale.png")
        icon_label.setPixmap(icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(icon_label)
        
        # Add title
        title = QLabel("   Deepseek-R1   ")
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        # Add model selector
        self.model_selector = ModelSelector(self)
        self.model_selector.currentTextChanged.connect(self.model_changed)
        layout.addWidget(self.model_selector)
        
        layout.addStretch()
        
        # Add window control buttons
        for symbol, slot in [("−", parent.showMinimized), ("□", parent.toggle_maximize), ("×", parent.close)]:
            btn = QPushButton(symbol)
            btn.setFixedSize(45, 30)
            btn.clicked.connect(slot)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #888888;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.1);
                    color: white;
                }
            """)
            layout.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Get the relative position of the click within the title bar
            click_pos = event.pos()
            
            # Check if click is within the model selector's area
            model_selector_rect = self.model_selector.geometry()
            
            # If click is NOT in the model selector area, allow dragging
            if not model_selector_rect.contains(click_pos):
                self.dragPos = event.globalPos() - self.parent.pos()
                event.accept()
            else:
                # Let the model selector handle the click
                event.ignore()

    def mouseMoveEvent(self, event):
        # Only move if we have a valid dragPos (meaning click wasn't on dropdown)
        if event.buttons() == Qt.LeftButton and hasattr(self, 'dragPos'):
            self.parent.move(event.globalPos() - self.dragPos)
            event.accept()

    def model_changed(self, model_name):
        """Handle model selection change"""
        if hasattr(self.parent, 'chat_worker'):
            selected_model = model_name.split(" ")[0]  # Remove "(default)" if present
            self.parent.chat_worker.model = selected_model

class ChatHistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.expanded_width = 250
        self.collapsed_width = 50
        self.setFixedWidth(self.collapsed_width)
        self.is_expanded = False
        self.animation = None
        self.chat_buttons = {}  # Store chat buttons by ID

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create content widget
        self.content = QWidget()
        self.content.setVisible(False)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(8)
        
        # New Chat Button
        self.new_chat_btn = QPushButton("  + New Chat")
        self.new_chat_btn.setObjectName("newChatBtn")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.create_new_chat)
        self.content_layout.addWidget(self.new_chat_btn)
        
        # Scroll Area for Chat History
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(SCROLLBAR_STYLE)
        
        # Container for chat history items
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(2)
        self.scroll_area.setWidget(self.chat_container)
        
        self.content_layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.content)

        # Set up timers
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.expand)
        
        self.check_hover_timer = QTimer(self)
        self.check_hover_timer.setInterval(100)
        self.check_hover_timer.timeout.connect(self.check_hover)

        # Style the panel
        self.setStyleSheet("""
            ChatHistoryPanel {
                background-color: #252525;
                border-right: 1px solid #333333;
            }
            ChatHistoryPanel:hover {
                background-color: #2A2A2A;
            }
            QPushButton#newChatBtn {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                margin: 2px 0px;
            }
            QPushButton#newChatBtn:hover {
                background-color: #1084D9;
            }
            QPushButton#chatItem {
                background-color: #333333;
                color: #E0E0E0;
                border: none;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                margin: 2px 0px;
            }
            QPushButton#chatItem:hover {
                background-color: #404040;
            }
        """)

        # Load existing chats
        self.load_existing_chats()

    def load_existing_chats(self):
        """Load existing chats from ChatManager."""
        if hasattr(self.parent, 'chat_manager'):
            chat_list = self.parent.chat_manager.get_chat_list()
            for chat_id, title, _ in reversed(chat_list):  # Reverse to show newest first
                self.add_chat_item(chat_id, title)

    def add_chat_item(self, chat_id, title):
        """Add a chat item to the panel."""
        chat_button = QPushButton(f"  {title}")
        chat_button.setObjectName("chatItem")
        chat_button.setCursor(Qt.PointingHandCursor)
        
        # Create context menu
        context_menu = QMenu(chat_button)
        rename_action = context_menu.addAction("Rename")
        delete_action = context_menu.addAction("Delete")
        
        # Set up context menu actions
        rename_action.triggered.connect(lambda: self.rename_chat(chat_id))
        delete_action.triggered.connect(lambda: self.delete_chat(chat_id))
        
        chat_button.setContextMenuPolicy(Qt.CustomContextMenu)
        chat_button.customContextMenuRequested.connect(
            lambda pos: context_menu.exec_(chat_button.mapToGlobal(pos))
        )
        
        # Connect click handler
        chat_button.clicked.connect(lambda: self.switch_chat(chat_id))
        
        # Store button reference
        self.chat_buttons[chat_id] = chat_button
        
        # Add to layout
        self.chat_layout.insertWidget(0, chat_button)

    def rename_chat(self, chat_id):
        """Rename a chat."""
        if chat_id in self.chat_buttons:
            current_title = self.chat_buttons[chat_id].text().strip()
            new_title, ok = QInputDialog.getText(
                self, 
                "Rename Chat",
                "Enter new chat name:",
                text=current_title
            )
            
            if ok and new_title:
                try:
                    self.parent.chat_manager.update_chat_title(chat_id, new_title)
                    self.chat_buttons[chat_id].setText(f"  {new_title}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to rename chat: {str(e)}")

    def delete_chat(self, chat_id):
        """Delete a chat."""
        reply = QMessageBox.question(
            self,
            "Delete Chat",
            "Are you sure you want to delete this chat?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.parent.chat_manager.delete_chat(chat_id)
                if chat_id in self.chat_buttons:
                    self.chat_buttons[chat_id].deleteLater()
                    del self.chat_buttons[chat_id]
                    
                # Create new chat if this was the last one
                if not self.chat_buttons:
                    self.create_new_chat()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete chat: {str(e)}")

    def create_new_chat(self):
        """Create a new chat."""
        if hasattr(self.parent, 'create_new_chat'):
            self.parent.create_new_chat()

    def switch_chat(self, chat_id):
        """Switch to a different chat."""
        if hasattr(self.parent, 'load_chat'):
            self.parent.load_chat(chat_id)

    def enterEvent(self, event):
        if not self.is_expanded:
            self.hover_timer.start(200)

    def leaveEvent(self, event):
        self.hover_timer.stop()
        if self.is_expanded:
            cursor_pos = QCursor.pos()
            panel_rect = self.geometry()
            panel_global_rect = self.mapToGlobal(panel_rect.topLeft())
            expanded_rect = QRect(panel_global_rect, QSize(self.expanded_width, panel_rect.height()))
            
            if not expanded_rect.contains(cursor_pos):
                self.collapse()

    def check_hover(self):
        if self.is_expanded:
            cursor_pos = QCursor.pos()
            panel_rect = self.geometry()
            panel_global_rect = self.mapToGlobal(panel_rect.topLeft())
            expanded_rect = QRect(panel_global_rect, QSize(self.expanded_width, panel_rect.height()))
            
            if not expanded_rect.contains(cursor_pos):
                self.collapse()

    def expand(self):
        if not self.is_expanded:
            self.content.setVisible(True)
            if self.animation and self.animation.state() == QPropertyAnimation.Running:
                self.animation.stop()
            
            self.animation = QPropertyAnimation(self, b"minimumWidth")
            self.animation.setDuration(150)
            self.animation.setStartValue(self.collapsed_width)
            self.animation.setEndValue(self.expanded_width)
            self.animation.finished.connect(lambda: self.check_hover_timer.start())
            self.animation.start()
            
            self.setMaximumWidth(self.expanded_width)
            self.is_expanded = True

    def collapse(self):
        if self.is_expanded:
            if self.animation and self.animation.state() == QPropertyAnimation.Running:
                self.animation.stop()
            
            self.animation = QPropertyAnimation(self, b"minimumWidth")
            self.animation.setDuration(0)
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self.collapsed_width)
            self.animation.finished.connect(lambda: self.content.setVisible(False))
            self.animation.start()
            
            self.check_hover_timer.stop()
            self.setMaximumWidth(self.collapsed_width)
            self.is_expanded = False

class ChatWorker(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.prompt = ""
        self.message_history = []
        self.max_retries = 10
        self.model = "deepseek-r1:7b"  # Default model
        self.system_prompt = """You are a helpful AI assistant.""" # system prompt

    def set_prompt(self, prompt, history):
        self.prompt = prompt
        self.message_history = history

    def validate_response(self, content):
        """Validate response format using XML parsing."""
        if not content:
            return False
            
        try:
            # Wrap content in root element for valid XML
            xml_content = f"<root>{content}</root>"
            tree = ET.fromstring(xml_content)
            
            # Find all think elements
            think_elements = tree.findall('.//think')
            
            if not think_elements:
                return False
                
            # Validate last think element
            last_think = think_elements[-1]
            
            # Check for meaningful content (at least 10 chars)
            if not last_think.text or len(last_think.text.strip()) < 10:
                return False
                
            # Verify think tag appears at the end
            # Get the last element's position in the tree
            last_element = None
            for elem in tree.iter():
                if elem.tag == 'think':
                    last_element = elem
            
            # Check if there's significant content after the last think tag
            if last_element is not None:
                parent = tree.find('.//*[think]')
                if parent is not None:
                    think_index = list(parent).index(last_element)
                    if think_index < len(list(parent)) - 1:
                        return False
                        
            return True
            
        except ET.ParseError:
            return False

    def enhance_prompt(self, failed_attempts):
        """Generate increasingly strict prompts based on failed attempts."""
        enhanced_prompts = [
            "IMPORTANT: Your response MUST end with <think></think>",
            "CRITICAL: You MUST include meaningful thoughts in <think></think> tags at the END of your response",
            "FINAL REMINDER: Response format must be: [Your answer] followed by <think>your thoughts</think>",
            "STRICT REQUIREMENT: End your response with detailed thoughts in <think></think> tags",
            "MANDATORY: Include substantial thoughts (>10 words) in <think></think> tags at the end"
        ]
        return enhanced_prompts[min(failed_attempts, len(enhanced_prompts) - 1)]

    def extract_content_and_thoughts(self, content):
        """Extract main content and thoughts using XML parsing."""
        try:
            # Split content into parts
            parts = content.split('<think>')
            
            # Get main content (everything before first <think>)
            before_think = parts[0].strip()
            
            # Get thoughts content (between <think></think>)
            think_content = ""
            if len(parts) > 1:
                think_parts = parts[1].split('</think>')
                think_content = think_parts[0].strip()
                
                # Get content after </think> if any
                if len(think_parts) > 1:
                    after_think = think_parts[1].strip()
                    before_think = (before_think + " " + after_think).strip()
            
            return before_think, think_content
            
        except Exception as e:
            print(f"Error in extraction: {str(e)}")
            return content.strip(), ""

    def get_valid_response(self):
        """Get a valid response with proper think tags."""
        messages = [{'role': 'system', 'content': self.system_prompt}]
        messages.extend(self.message_history[-10:] if len(self.message_history) > 10 else self.message_history)
        messages.append({'role': 'user', 'content': self.prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = ollama.chat(
                    model=self.model,  # Use current model
                    messages=messages
                )
                content = response['message']['content']
                
                if self.validate_response(content):
                    return content
                
                # Add increasingly strict reminders
                messages.append({
                    'role': 'system',
                    'content': self.enhance_prompt(attempt)
                })
                
                # Re-add the original prompt to maintain context
                messages.append({'role': 'user', 'content': self.prompt})
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to get valid response after {self.max_retries} attempts: {str(e)}")
        
        raise Exception("Failed to get valid response with proper think tags")

    def run(self):
        try:
            # Get valid response with retries
            content = self.get_valid_response()
            
            # Extract main content and thoughts
            main_content, thoughts = self.extract_content_and_thoughts(content)
            
            # Emit the results
            self.finished.emit(main_content, thoughts)
            
        except Exception as e:
            self.error.emit(str(e))
            
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1200, 800)
        
        # Initialize chat manager
        self.chat_manager = ChatManager()
        self.message_history = []
        
        # Initialize chat panel before setup_ui
        self.chat_history_panel = None
        
        self.setup_ui()
        self.chat_worker = ChatWorker()
        self.chat_worker.finished.connect(self.handle_response)
        self.chat_worker.error.connect(self.handle_error)
        
        # Set up system tray icon
        self.setup_tray_icon()
        
        # Create initial chat if no chats exist
        if not self.chat_manager.get_chat_list():
            self.create_new_chat()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(r"C:\Users\Admin\source\repos\Deepseek-Chat\asset\whaaaaaaaale.png"))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def setup_ui(self):
        # Main container
        main_container = QFrame()
        main_container.setStyleSheet("background-color: #1E1E1E; border-radius: 10px;")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = TitleBar(self)
        main_layout.addWidget(title_bar)

        # Content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)

        # Initialize the sliding panel
        self.chat_history_panel = ChatHistoryPanel(self)

        # Left panel (Chat History - Sliding)
        content_layout.addWidget(self.chat_history_panel)

        # Center panel (Chat)
        chat_panel = QFrame()
        chat_panel.setStyleSheet("background-color: #252525; border-radius: 5px;")
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.chat_display = ChatDisplay()
        chat_layout.addWidget(self.chat_display, stretch=1)

        # Input area
        input_container = QWidget()
        input_container.setFixedHeight(50)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(5)

        self.chat_input = MessageInput()
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(70, 30)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1084D9;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_button)
        chat_layout.addWidget(input_container)

        # Right panel (Thoughts)
        thoughts_panel = QFrame()
        thoughts_panel.setFixedWidth(300)
        thoughts_panel.setStyleSheet("background-color: #252525; border-radius: 5px;")
        thoughts_layout = QVBoxLayout(thoughts_panel)
        thoughts_layout.setContentsMargins(5, 5, 5, 5)

        thoughts_label = QLabel("Thoughts")
        thoughts_label.setStyleSheet("color: #0078D4;")
        thoughts_layout.addWidget(thoughts_label)

        self.thoughts_display = QTextEdit()
        self.thoughts_display.setReadOnly(True)
        self.thoughts_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #2D2D2D;
                color: #4EC9B0;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }}
            {SCROLLBAR_STYLE}
        """)
        thoughts_layout.addWidget(self.thoughts_display)

        # Add panels to content layout
        content_layout.addWidget(chat_panel, stretch=1)
        content_layout.addWidget(thoughts_panel)

        main_layout.addWidget(content)
        self.setCentralWidget(main_container)

    def create_new_chat(self):
        """Create a new chat and update UI."""
        chat_id, title = self.chat_manager.create_new_chat()
        self.message_history.clear()
        self.chat_display.clear()
        self.thoughts_display.clear()
        if self.chat_history_panel:
            self.chat_history_panel.add_chat_item(chat_id, title)

    def load_chat(self, chat_id):
        """Load an existing chat."""
        try:
            messages = self.chat_manager.load_chat(chat_id)
            self.message_history = [{'role': msg['role'], 'content': msg['content']} 
                                  for msg in messages]
            
            # Clear and reload chat display
            self.chat_display.clear()
            self.thoughts_display.clear()
            
            for message in messages:
                if message['role'] == 'user':
                    formatted_message = self.format_user_message(message['content'])
                else:
                    formatted_message = self.format_assistant_message(message['content'])
                self.chat_display.append(formatted_message)
                
        except Exception as e:
            self.handle_error(f"Error loading chat: {str(e)}")

    def format_user_message(self, content):
        """Format user message for display."""
        return f'''
            <div class="message user-message">
                <div class="message-header">You</div>
                <div class="message-content">{content}</div>
            </div>
        '''

    def format_assistant_message(self, content):
        """Format assistant message for display with markdown and MathJax support."""
        # Extract main content and thoughts
        content_parts = content.split('<think>')
        main_content = content_parts[0].strip()
    
        if len(content_parts) > 1:
            thoughts = content_parts[1].split('</think>')[0].strip()
            self.thoughts_display.setText(thoughts)
    
        # Process markdown
        formatted_content = self.format_markdown(main_content)
    
        # Wrap the content in a div that enables MathJax processing
        message_html = f'''
            <div class="message ai-message">
                <div class="message-header">AI</div>
                <div class="message-content mathjax-content">{formatted_content}</div>
            </div>
        '''
        return message_html

    def handle_error(self, error_message):
        error_html = f'''
            <div class="message ai-message">
                <div class="message-header" style="color: #E74856;">Error</div>
                <div class="message-content" style="color: #E74856;">{error_message}</div>
            </div>
        '''
        self.chat_display.append(error_html)

    def format_markdown(self, text):
        """Convert Markdown to HTML with custom styling"""
        # Configure markdown extensions
        md = markdown.Markdown(extensions=['extra', 'codehilite'])
        
        # Convert markdown to HTML
        html = md.convert(text)
        
        # Apply custom styling
        styled_html = html.replace('<h1>', '<h1 style="color: #E0E0E0; font-size: 24px; margin: 15px 0;">')
        styled_html = styled_html.replace('<h2>', '<h2 style="color: #E0E0E0; font-size: 20px; margin: 12px 0;">')
        styled_html = styled_html.replace('<h3>', '<h3 style="color: #E0E0E0; font-size: 16px; margin: 10px 0;">')
        styled_html = styled_html.replace('<code>', '<code style="background-color: #1E1E1E; padding: 2px 4px; border-radius: 3px; font-family: \'Consolas\', monospace; font-size: 13px; color: #D4D4D4;">')
        styled_html = styled_html.replace('<pre>', '<pre style="background-color: #1E1E1E; padding: 10px; border-radius: 4px; margin: 10px 0; font-family: \'Consolas\', monospace; font-size: 13px; color: #D4D4D4; white-space: pre-wrap;">')
        styled_html = styled_html.replace('<a ', '<a style="color: #569CD6; text-decoration: none;" ')
        styled_html = styled_html.replace('<strong>', '<strong style="color: #CE9178;">')
        styled_html = styled_html.replace('<em>', '<em style="color: #4EC9B0;">')
        
        return styled_html

    def format_code_blocks(self, text):
        """Format code blocks with proper styling"""
        # Handle multi-line code blocks
        text = re.sub(
            r'```(.*?)\n(.*?)```',
            lambda m: f'''
                <div style="
                    background-color: #1E1E1E;
                    border-radius: 4px;
                    padding: 8px;
                    margin: 8px 0;
                    font-family: 'Consolas', monospace;
                    font-size: 13px;
                    color: #D4D4D4;
                    white-space: pre-wrap;
                ">
                    {m.group(2)}
                </div>
            ''',
            text,
            flags=re.DOTALL
        )
        
        # Handle inline code
        text = re.sub(
            r'`([^`]+)`',
            r'<span style="background-color: #1E1E1E; padding: 2px 4px; border-radius: 3px; font-family: \'Consolas\', monospace; font-size: 13px; color: #D4D4D4;">\1</span>',
            text
        )
        
        return text

    def send_message(self):
        """Handle sending a new message"""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return

        # If no active chat exists, create a new one FIRST
        if self.chat_manager.active_chat_id is None:
            self.create_new_chat()  # This sets up everything we need for a new chat

        # Now we can safely proceed with sending the message
        formatted_message = self.format_user_message(message)
        self.chat_display.append(formatted_message)

        # Save message to chat manager
        self.chat_manager.save_message('user', message)

        # Update message history and clear input
        self.message_history.append({'role': 'user', 'content': message})
        self.chat_input.clear()
        self.send_button.setEnabled(False)

        # If this is the first message in this chat, generate a title
        is_new_chat = len(self.chat_manager.chats_metadata[self.chat_manager.active_chat_id]['messages']) == 1
        if is_new_chat:
            try:
                messages = [{
                    'role': 'system',
                    'content': """You are a chat title generator. Generate a SHORT, CONCISE title (2-5 words) based on the user's first message. 
                    Rules:
                    - Title should be descriptive but brief
                    - NO quotation marks or special characters
                    - NO phrases like 'Chat about' or 'Discussion of'
                    - Just the essential topic or question
                    - Max 40 characters
                    Example input: "Can you help me understand how photosynthesis works in plants?"
                    Example output: Plant Photosynthesis"""
                }, {
                    'role': 'user',
                    'content': message
                }]

                # Get title from model
                response = ollama.chat(model='qwen2.5:3b', messages=messages)
                title = response['message']['content'].strip()

                # Clean up the title
                title = re.sub(r'["\']', '', title)  # Remove quotes
                title = re.sub(r'^(Chat about|Discussion of|About)\s*', '', title, flags=re.IGNORECASE)
                title = title[:40]  # Truncate if too long

                # Update chat title
                self.chat_manager.update_chat_title(self.chat_manager.active_chat_id, title)
                if self.chat_history_panel and self.chat_manager.active_chat_id in self.chat_history_panel.chat_buttons:
                    self.chat_history_panel.chat_buttons[self.chat_manager.active_chat_id].setText(f"  {title}")

            except Exception as e:
                print(f"Error generating title: {str(e)}")
                fallback_title = f"New Chat {datetime.now().strftime('%H:%M')}"
                self.chat_manager.update_chat_title(self.chat_manager.active_chat_id, fallback_title)
                if self.chat_history_panel and self.chat_manager.active_chat_id in self.chat_history_panel.chat_buttons:
                    self.chat_history_panel.chat_buttons[self.chat_manager.active_chat_id].setText(f"  {fallback_title}")

        # Send to chat worker for response
        self.chat_worker.set_prompt(message, self.message_history)
        self.chat_worker.start()

    def handle_response(self, response, thoughts):
        # Format and display response
        message_html = self.format_assistant_message(response)
        self.chat_display.append(message_html)
        
        # Save response to chat manager
        self.chat_manager.save_message('assistant', response)
        
        # Update message history
        self.message_history.append({'role': 'assistant', 'content': response})
        
        # Update thoughts display
        self.thoughts_display.setText(thoughts)
        
        # Re-enable send button
        self.send_button.setEnabled(True)

    def handle_error(self, error_message):
        error_html = f'''
            <div style="margin: 10px 0;">
                <div style="color: #E74856; margin-bottom: 4px;">
                    <b>Error</b>
                </div>
                <div style="margin-left: 10px; color: #E74856;">
                    {error_message}
                </div>
            </div>
        '''
        self.chat_display.append(error_html)

    def handle_response(self, response, thoughts):
        # Format and display response
        message_html = self.format_assistant_message(response)
        self.chat_display.append(message_html)
    
        # Save response to chat manager
        self.chat_manager.save_message('assistant', response)
    
        # Update message history
        self.message_history.append({'role': 'assistant', 'content': response})
    
        # Update thoughts display
        self.thoughts_display.setText(thoughts)
    
        # Re-enable send button
        self.send_button.setEnabled(True)

    def handle_error(self, error_message):
        error_html = f'''
            <div style="margin: 10px 0;">
                <div style="color: #E74856; margin-bottom: 4px;">
                    <b>Error</b>
                </div>
                <div style="margin-left: 10px; color: #E74856;">
                    {error_message}
                </div>
            </div>
        '''
        self.chat_display.append(error_html)
        self.send_button.setEnabled(True)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def closeEvent(self, event):
        """Handle application close event."""
        self.hide()
        event.ignore()  # Don't actually close, just hide

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Create main window
    window = MainWindow()
    
    # Close splash and show main window after 2 seconds
    def show_main_window():
        splash.close()
        window.show()
    
    QTimer.singleShot(2000, show_main_window) # timer for splash-screen
    
    sys.exit(app.exec_())
