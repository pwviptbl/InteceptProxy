#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do WebSocket
"""
import os
import sys

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.websocket_history import WebSocketHistory


def test_websocket_history():
    """Testa a classe WebSocketHistory"""
    print("Testando WebSocketHistory...")

    # Cria instância
    ws_history = WebSocketHistory()
    assert len(ws_history.get_connections()) == 0, "Histórico deve começar vazio"
    print("✓ Histórico WebSocket inicializado corretamente")

    # Adiciona uma conexão
    flow_id = "test_flow_1"
    ws_history.add_connection(flow_id, "wss://exemplo.com/ws", "exemplo.com")
    
    connections = ws_history.get_connections()
    assert len(connections) == 1, "Deve ter 1 conexão"
    assert connections[0]['url'] == "wss://exemplo.com/ws", "URL deve corresponder"
    assert connections[0]['status'] == "active", "Status deve ser 'active'"
    print("✓ Conexão WebSocket adicionada com sucesso")

    # Adiciona mensagens
    ws_history.add_message(flow_id, b"Hello from client", from_client=True)
    ws_history.add_message(flow_id, b"Hello from server", from_client=False)
    
    messages = ws_history.get_messages(flow_id)
    assert len(messages) == 2, "Deve ter 2 mensagens"
    assert messages[0]['content'] == "Hello from client", "Conteúdo da primeira mensagem deve corresponder"
    assert messages[0]['from_client'] == True, "Primeira mensagem deve ser do cliente"
    assert messages[1]['from_client'] == False, "Segunda mensagem deve ser do servidor"
    print("✓ Mensagens WebSocket adicionadas com sucesso")

    # Verifica contador de mensagens
    conn_info = ws_history.get_connection_info(flow_id)
    assert conn_info['message_count'] == 2, "Contador de mensagens deve ser 2"
    print("✓ Contador de mensagens funcionando")

    # Fecha a conexão
    ws_history.close_connection(flow_id)
    conn_info = ws_history.get_connection_info(flow_id)
    assert conn_info['status'] == "closed", "Status deve ser 'closed'"
    assert conn_info['end_time'] is not None, "end_time deve estar definido"
    print("✓ Fechamento de conexão funcionando")

    # Testa mensagem binária
    flow_id_2 = "test_flow_2"
    ws_history.add_connection(flow_id_2, "wss://example.com/binary", "example.com")
    binary_data = b"\x00\x01\x02\x03\xff"
    ws_history.add_message(flow_id_2, binary_data, from_client=True)
    
    messages = ws_history.get_messages(flow_id_2)
    assert len(messages) == 1, "Deve ter 1 mensagem binária"
    assert messages[0]['is_binary'] == True, "Mensagem deve ser marcada como binária"
    assert messages[0]['size'] == 5, "Tamanho deve ser 5 bytes"
    print("✓ Mensagens binárias funcionando")

    # Testa limpeza
    ws_history.clear_history()
    assert len(ws_history.get_connections()) == 0, "Histórico deve estar vazio após limpeza"
    print("✓ Limpeza de histórico WebSocket funcionando")

    print("\n✅ Todos os testes de WebSocketHistory passaram!")
    return True


if __name__ == "__main__":
    try:
        if not test_websocket_history():
            sys.exit(1)

        print("\n🎉 Todos os testes de WebSocket passaram com sucesso!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
