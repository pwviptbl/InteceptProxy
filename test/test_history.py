#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do RequestHistory
"""
import os
import sys
from unittest.mock import Mock

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.history import RequestHistory
from core.config import InterceptConfig
from core.addon import InterceptAddon


def test_request_history():
    """Testa a classe RequestHistory"""
    print("Testando RequestHistory...")

    # Cria instância
    history = RequestHistory()
    assert len(history.get_history()) == 0, "História deve começar vazia"
    print("✓ História inicializada corretamente")

    # Simula um flow HTTP
    mock_flow = Mock()
    mock_flow.request = Mock()
    mock_flow.request.pretty_host = "exemplo.com"
    mock_flow.request.method = "GET"
    mock_flow.request.pretty_url = "http://exemplo.com/test"
    mock_flow.request.path = "/test"
    mock_flow.request.headers = {"User-Agent": "Test"}
    mock_flow.request.content = b"test body"

    mock_flow.response = Mock()
    mock_flow.response.status_code = 200
    mock_flow.response.headers = {"Content-Type": "text/html"}
    mock_flow.response.content = b"response body"

    # Adiciona requisição
    history.add_request(mock_flow)
    assert len(history.get_history()) == 1, "Deve ter 1 entrada"
    print("✓ Requisição adicionada com sucesso")

    # Verifica conteúdo da entrada
    entry = history.get_history()[0]
    assert entry['host'] == "exemplo.com", "Host deve ser exemplo.com"
    assert entry['method'] == "GET", "Método deve ser GET"
    assert entry['status'] == 200, "Status deve ser 200"
    assert entry['url'] == "http://exemplo.com/test", "URL deve corresponder"
    print("✓ Conteúdo da entrada está correto")

    # Testa limpeza
    history.clear_history()
    assert len(history.get_history()) == 0, "História deve estar vazia após limpeza"
    print("✓ Limpeza de histórico funcionando")

    # Testa limite de tamanho
    history.max_items = 5
    for i in range(10):
        history.add_request(mock_flow)
    assert len(history.get_history()) == 5, "Histórico deve ser limitado a 5 itens"
    print("✓ Limite de tamanho funcionando")

    print("\n✅ Todos os testes de histórico passaram!")
    return True


def test_intercept_addon_with_history():
    """Testa o InterceptAddon com histórico"""
    print("\nTestando InterceptAddon com histórico...")

    config = InterceptConfig()
    history = RequestHistory()
    addon = InterceptAddon(config, history)

    # Simula um flow
    mock_flow = Mock()
    mock_flow.request = Mock()
    mock_flow.request.pretty_host = "exemplo.com"
    mock_flow.request.method = "GET"
    mock_flow.request.pretty_url = "http://exemplo.com/test"
    mock_flow.request.path = "/test"
    mock_flow.request.headers = {"User-Agent": "Test"}
    mock_flow.request.content = b""
    mock_flow.request.query = {}

    mock_flow.response = Mock()
    mock_flow.response.status_code = 200
    mock_flow.response.headers = {"Content-Type": "text/html"}
    mock_flow.response.content = b""

    # Processa requisição e resposta
    addon.request(mock_flow)
    addon.response(mock_flow)

    assert len(history.get_history()) == 1, "Deve ter 1 entrada no histórico"
    print("✓ Histórico captura requisições através do addon")

    print("\n✅ Todos os testes de integração passaram!")
    return True


if __name__ == "__main__":
    try:
        if not test_request_history():
            sys.exit(1)

        if not test_intercept_addon_with_history():
            sys.exit(1)

        print("\n🎉 Todos os testes de histórico passaram com sucesso!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
