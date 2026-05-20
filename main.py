import sys
import json
import os

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QHBoxLayout,
    QSystemTrayIcon, QMenu, QInputDialog, QDialog,
    QFormLayout, QSlider, QComboBox, QSpinBox,
    QCheckBox, QFileDialog, QLabel
)
from PyQt6.QtWidgets import QStyle
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtCore import Qt, QEvent


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setFixedSize(350, 300)
        self.current_settings = current_settings

        layout = QFormLayout()

        # 1. Тема (Світла / Темна)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(current_settings.get("theme", "Dark"))
        layout.addRow("Theme:", self.theme_combo)

        # 2. Прозорість вікна
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(int(current_settings.get("opacity", 0.9) * 100))
        layout.addRow("Opacity (%):", self.opacity_slider)

        # 3. Розмір шрифту
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(current_settings.get("font_size", 14))
        layout.addRow("Font Size:", self.font_spin)

        # 4. Завжди зверху
        self.on_top_check = QCheckBox()
        self.on_top_check.setChecked(current_settings.get("always_on_top", True))
        layout.addRow("Always on Top:", self.on_top_check)

        # 5. Шлях до JSON файлу з нотатками
        db_layout = QHBoxLayout()
        self.db_label = QLabel(current_settings.get("db_path", "notes.json"))
        db_btn = QPushButton("Browse...")
        db_btn.clicked.connect(self.browse_file)
        db_layout.addWidget(self.db_label)
        db_layout.addWidget(db_btn)
        layout.addRow("Notes File:", db_layout)

        # Кнопки Зберегти / Скасувати
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Notes JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            self.db_label.setText(file_name)

    def get_settings(self):
        return {
            "theme": self.theme_combo.currentText(),
            "opacity": self.opacity_slider.value() / 100.0,
            "font_size": self.font_spin.value(),
            "always_on_top": self.on_top_check.isChecked(),
            "db_path": self.db_label.text()
        }


class NotesApp(QWidget):
    def __init__(self):
        super().__init__()

        # Спочатку завантажуємо налаштування
        self.settings = self.load_settings()

        # Потім завантажуємо нотатки
        self.notes = []
        self.load_notes()

        self.setWindowTitle("qNotes")
        self.setFixedSize(420, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.is_dialog_open = False

        self.setup_ui()
        self.setup_tray()
        
        # Застосовуємо стилі на основі налаштувань
        self.apply_styles()

    def load_settings(self):
        default_settings = {
            "theme": "Dark",
            "opacity": 0.9,
            "font_size": 14,
            "always_on_top": True,
            "db_path": "notes.json"
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

        title = QPushButton("📌 qNotes")
        title.setEnabled(False)

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

        layout.addWidget(title)
        layout.addWidget(self.list_widget)
        layout.addLayout(buttons)

        self.container.setLayout(layout)
        
        # Налаштування списку
        self.list_widget.itemDoubleClicked.connect(self.edit_note)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.model().rowsMoved.connect(self.sync_order_after_drag)

        outer.addWidget(self.container)
        self.setLayout(outer)

    def apply_styles(self):
        theme = self.settings.get("theme", "Dark")
        opacity = self.settings.get("opacity", 0.9)
        font_size = self.settings.get("font_size", 14)
        always_on_top = self.settings.get("always_on_top", True)

        flags = Qt.WindowType.FramelessWindowHint
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

        if theme == "Dark":
            bg_color = f"rgba(32, 32, 32, {opacity})"
            text_color = "white"
            item_bg = "rgba(255, 255, 255, 0.06)"
            item_sel = "rgba(255, 255, 255, 0.12)"
            btn_bg = "rgba(255, 255, 255, 0.08)"
            btn_hover = "rgba(255, 255, 255, 0.14)"
        else: # Light
            bg_color = f"rgba(240, 240, 240, {opacity})"
            text_color = "#202020"
            item_bg = "rgba(0, 0, 0, 0.04)"
            item_sel = "rgba(0, 0, 0, 0.08)"
            btn_bg = "rgba(0, 0, 0, 0.05)"
            btn_hover = "rgba(0, 0, 0, 0.1)"

        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color}; border-radius: 20px;
                color: {text_color}; font-family: Segoe UI;
            }}
        """)

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
            if btn.text() == "📌 qNotes":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; border: none; font-size: 20px;
                        font-weight: bold; text-align: left; padding: 10px; color: {text_color};
                    }}
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
        quit_action.triggered.connect(app.quit)

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

    # --- Обробка подій (закриття, клавіші, перетягування мишею) ---

    def event(self, e):
        if e.type() == QEvent.Type.WindowDeactivate:
            if not self.is_dialog_open:
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = NotesApp()
    window.hide()

    sys.exit(app.exec())