import sys
from PyQt6.QtWidgets import QApplication
from app import NotesApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Не закривати програму, якщо всі вікна сховані
    app.setQuitOnLastWindowClosed(False)

    window = NotesApp()
    window.hide() # Ховаємо вікно при старті (воно викличеться з трею)

    sys.exit(app.exec())