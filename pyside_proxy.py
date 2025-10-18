#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
from src.ui.pyside_gui import ProxyGUI

def main():
    """Inicia a aplicação GUI com PySide6."""
    # Adiciona o diretório 'src' ao path para importações corretas
    sys.path.append('src')

    app = QApplication(sys.argv)
    window = ProxyGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
