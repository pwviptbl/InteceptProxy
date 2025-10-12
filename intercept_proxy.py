#!/usr/bin/env python3
"""
InteceptProxy - Ponto de entrada para a aplicação com GUI.
"""
import sys

# Tkinter import é opcional (pode não estar disponível em ambientes headless)
try:
    from src.ui.gui import ProxyGUI
    TKINTER_AVAILABLE = True
except ImportError as e:
    # Captura erros de importação do Tkinter e outros
    print(f"Erro de importação: {e}")
    TKINTER_AVAILABLE = False


def main():
    """Função principal"""
    if not TKINTER_AVAILABLE:
        print("\nERRO: Não foi possível iniciar a interface gráfica.")
        print("Verifique se o Tkinter está instalado no seu sistema:")
        print("  - Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  - Fedora: sudo dnf install python3-tkinter")
        print("  - Windows/macOS: O Tkinter geralmente já vem com o Python.")
        return 1

    try:
        app = ProxyGUI()
        app.run()
        return 0
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao executar a aplicação: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
