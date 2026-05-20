from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QSlider, QComboBox, QSpinBox,
    QCheckBox, QFileDialog, QLabel, QFontComboBox, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setFixedSize(360, 340)
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

        # 4. Стиль шрифту
        self.font_combo = QFontComboBox()
        current_font = QFont(current_settings.get("font_family", "Segoe UI"))
        self.font_combo.setCurrentFont(current_font)
        layout.addRow("Font Family:", self.font_combo)

        # 5. Завжди зверху
        self.on_top_check = QCheckBox()
        self.on_top_check.setChecked(current_settings.get("always_on_top", True))
        layout.addRow("Always on Top:", self.on_top_check)

        # 6. Шлях до файлу
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
            "font_family": self.font_combo.currentFont().family(),
            "always_on_top": self.on_top_check.isChecked(),
            "db_path": self.db_label.text(),
            "is_pinned": self.current_settings.get("is_pinned", False)
        }