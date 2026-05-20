import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QHBoxLayout,
    QSystemTrayIcon, QMenu, QInputDialog, QLabel, QApplication
)
from PyQt6.QtWidgets import QStyle
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtCore import Qt, QEvent

# Імпортуємо наш клас налаштувань з іншого файлу
from settings_dialog import SettingsDialog


class NotesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.notes = []
        self.load_notes()

        self.setWindowTitle("qNotes")
        self.setFixedSize(420, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.is_dialog_open = False

        self.setup_ui()
        self.setup_tray()
        self.apply_styles()

    def load_settings(self):
        default_settings = {
            "theme": "Dark",
            "opacity": 0.9,
            "font_size": 14,
            "font_family": "Segoe UI",
            "always_on_top": True,
            "db_path": "notes.json",
            "is_pinned": False
        }
        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as f:
                try:
                    loaded = json.load(f)
                    default_settings.update(loaded)
                except:
                    pass
        return default_settings

    def save_settings(self):
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def setup_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(10, 10, 10, 10)

        self.container = QWidget()
        layout = QVBoxLayout()

        # Заголовок з кнопкою закріплення
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 0, 5, 0)
        
        is_pinned = self.settings.get("is_pinned", False)
        self.pin_btn = QPushButton("📌" if is_pinned else "📍")
        self.pin_btn.setToolTip("Toggle Pin to screen")
        self.pin_btn.setFixedSize(36, 36)
        self.pin_btn.clicked.connect(self.toggle_pin)

        self.title_lbl = QLabel("qNotes")
        
        header_layout.addWidget(self.pin_btn)
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()

        self.list_widget = QListWidget()
        self.refresh_notes()

        buttons = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self.add_note)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_note)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_note)

        buttons.addWidget(add_btn)
        buttons.addWidget(delete_btn)
        buttons.addWidget(edit_btn)

        layout.addLayout(header_layout)
        layout.addWidget(self.list_widget)
        layout.addLayout(buttons)

        self.container.setLayout(layout)
        
        self.list_widget.itemDoubleClicked.connect(self.edit_note)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.model().rowsMoved.connect(self.sync_order_after_drag)

        outer.addWidget(self.container)
        self.setLayout(outer)

    def toggle_pin(self):
        current_state = self.settings.get("is_pinned", False)
        new_state = not current_state
        self.settings["is_pinned"] = new_state
        self.save_settings()
        
        self.pin_btn.setText("📌" if new_state else "📍")

    def apply_styles(self):
        theme = self.settings.get("theme", "Dark")
        opacity = self.settings.get("opacity", 0.9)
        alpha = int(opacity * 255)
        font_size = self.settings.get("font_size", 14)
        font_family = self.settings.get("font_family", "Segoe UI")
        always_on_top = self.settings.get("always_on_top", True)

        flags = Qt.WindowType.FramelessWindowHint
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

        if theme == "Dark":
            bg_color = f"rgba(32, 32, 32, {alpha})"
            text_color = "white"
            item_bg = f"rgba(255, 255, 255, {int(0.06 * 255)})"
            item_sel = f"rgba(255, 255, 255, {int(0.12 * 255)})"
            btn_bg = f"rgba(255, 255, 255, {int(0.08 * 255)})"
            btn_hover = f"rgba(255, 255, 255, {int(0.14 * 255)})"
        else: # Light
            bg_color = f"rgba(240, 240, 240, {alpha})"
            text_color = "#202020"
            item_bg = f"rgba(0, 0, 0, {int(0.04 * 255)})"
            item_sel = f"rgba(0, 0, 0, {int(0.08 * 255)})"
            btn_bg = f"rgba(0, 0, 0, {int(0.05 * 255)})"
            btn_hover = f"rgba(0, 0, 0, {int(0.1 * 255)})"

        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color}; border-radius: 20px;
                color: {text_color}; font-family: "{font_family}";
            }}
        """)
        
        self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {text_color}; padding: 5px;")

        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none; padding: 5px; font-size: {font_size}px;
            }}
            QListWidget::item {{
                background-color: {item_bg}; border-radius: 14px; margin-bottom: 8px;
                padding: 14px; color: {text_color};
            }}
            QListWidget::item:selected {{ background-color: {item_sel}; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {item_sel}; border-radius: 4px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {btn_hover}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}
        """)

        for btn in self.findChildren(QPushButton):
            if btn == self.pin_btn:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; border: none; font-size: 18px; color: {text_color};
                    }}
                    QPushButton:hover {{ background-color: {btn_hover}; border-radius: 18px; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {btn_bg}; border: none; border-radius: 12px;
                        padding: 10px; color: {text_color}; font-size: {font_size - 2}px;
                    }}
                    QPushButton:hover {{ background-color: {btn_hover}; }}
                """)

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

        menu = QMenu()

        show_action = QAction("Open Notes", self)
        settings_action = QAction("⚙️ Settings", self)
        quit_action = QAction("Exit", self)

        show_action.triggered.connect(self.show_near_tray)
        settings_action.triggered.connect(self.open_settings)
        quit_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(show_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()

    def show_near_tray(self):
        cursor_pos = QCursor.pos()
        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() - 10
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def open_settings(self):
        self.is_dialog_open = True 
        dialog = SettingsDialog(self.settings, self)
        
        if dialog.exec():
            new_settings = dialog.get_settings()
            old_db = self.settings.get("db_path")
            new_db = new_settings.get("db_path")
            
            self.settings = new_settings
            self.save_settings()
            
            if old_db != new_db:
                self.load_notes()
                self.refresh_notes()
                
            self.apply_styles()
            
        self.is_dialog_open = False

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_near_tray()

    def add_note(self):
        self.is_dialog_open = True
        text, ok = QInputDialog.getMultiLineText(self, "New Note", "Write your note:")
        self.is_dialog_open = False

        if ok and text.strip():
            self.notes.append(text.strip())
            self.save_notes()
            self.refresh_notes()

    def edit_note(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            current_text = self.notes[row]
            self.is_dialog_open = True
            text, ok = QInputDialog.getMultiLineText(self, "Edit Note", "Edit your note:", current_text)
            self.is_dialog_open = False

            if ok and text.strip():
                self.notes[row] = text.strip()
                self.save_notes()
                self.refresh_notes()

    def delete_note(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            del self.notes[row]
            self.save_notes()
            self.refresh_notes()

    def refresh_notes(self):
        self.list_widget.clear()
        for note in self.notes:
            item = QListWidgetItem(note)
            self.list_widget.addItem(item)

    def load_notes(self):
        db_path = self.settings.get("db_path", "notes.json")
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                self.notes = json.load(f)

    def save_notes(self):
        db_path = self.settings.get("db_path", "notes.json")
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def sync_order_after_drag(self, *args):
        self.notes.clear()
        for i in range(self.list_widget.count()):
            self.notes.append(self.list_widget.item(i).text())
        self.save_notes()

    # --- Обробка подій ---
    def event(self, e):
        if e.type() == QEvent.Type.WindowDeactivate:
            if not self.is_dialog_open and not self.settings.get("is_pinned", False):
                self.hide()
        return super().event(e)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_note()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()