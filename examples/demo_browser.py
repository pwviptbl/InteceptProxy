#!/usr/bin/env python3
"""
Exemplo de uso do Browser Integrado do InteceptProxy.

Este exemplo demonstra como usar o browser integrado programaticamente.
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.ui.embedded_browser import launch_browser


def main():
    """
    Lança o browser integrado com configurações personalizadas.
    """
    print("=" * 60)
    print("Browser Integrado do InteceptProxy")
    print("=" * 60)
    print()
    print("Este exemplo lança o browser integrado com:")
    print("  - Proxy: localhost:8080")
    print("  - Certificado mitmproxy confiável")
    print("  - Integração completa com o proxy")
    print()
    print("Certifique-se de que o proxy está em execução!")
    print()
    print("=" * 60)
    print()
    
    # Configuração do proxy
    proxy_host = '127.0.0.1'
    proxy_port = 8080
    
    # Você pode alterar a porta se necessário
    # proxy_port = 9090
    
    print(f"Iniciando browser com proxy {proxy_host}:{proxy_port}...")
    print()
    
    # Lança o browser
    try:
        launch_browser(proxy_host=proxy_host, proxy_port=proxy_port)
    except KeyboardInterrupt:
        print("\nBrowser fechado pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro ao iniciar o browser: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
