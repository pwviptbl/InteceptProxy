#!/usr/bin/env python3
"""
Demo script para demonstrar a funcionalidade WebSocket do InteceptProxy

Este script simula o uso básico do WebSocketHistory para demonstrar
como as conexões e mensagens são rastreadas.
"""
import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.websocket_history import WebSocketHistory
import time


def demo_websocket_history():
    """Demonstra o uso do WebSocketHistory"""
    print("=" * 70)
    print("Demo: WebSocket Support no InteceptProxy")
    print("=" * 70)
    print()

    # Cria instância do histórico
    ws_history = WebSocketHistory()
    print("✓ WebSocketHistory inicializado")
    print()

    # Simula primeira conexão WebSocket
    print("📡 Simulando conexão WebSocket 1...")
    flow_id_1 = "websocket_flow_12345"
    ws_history.add_connection(
        flow_id_1, 
        "wss://example.com/chat", 
        "example.com"
    )
    print(f"   ✓ Conexão estabelecida: wss://example.com/chat")
    
    # Simula troca de mensagens
    print("\n💬 Simulando troca de mensagens...")
    ws_history.add_message(flow_id_1, b"Hello Server!", from_client=True)
    print("   → Cliente: 'Hello Server!'")
    time.sleep(0.1)
    
    ws_history.add_message(flow_id_1, b"Hello Client! Welcome to the chat.", from_client=False)
    print("   ← Servidor: 'Hello Client! Welcome to the chat.'")
    time.sleep(0.1)
    
    ws_history.add_message(flow_id_1, b"Thanks! How are you?", from_client=True)
    print("   → Cliente: 'Thanks! How are you?'")
    time.sleep(0.1)
    
    ws_history.add_message(flow_id_1, b"I'm doing great!", from_client=False)
    print("   ← Servidor: 'I'm doing great!'")
    
    # Simula segunda conexão WebSocket (binária)
    print("\n📡 Simulando conexão WebSocket 2 (dados binários)...")
    flow_id_2 = "websocket_flow_67890"
    ws_history.add_connection(
        flow_id_2,
        "wss://api.example.com/stream",
        "api.example.com"
    )
    print(f"   ✓ Conexão estabelecida: wss://api.example.com/stream")
    
    # Simula mensagem binária
    print("\n📦 Simulando mensagem binária...")
    binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
    ws_history.add_message(flow_id_2, binary_data, from_client=True)
    print(f"   → Cliente: {binary_data.hex()} (binário, {len(binary_data)} bytes)")
    
    # Mostra estatísticas
    print("\n" + "=" * 70)
    print("📊 Estatísticas das Conexões")
    print("=" * 70)
    
    connections = ws_history.get_connections()
    print(f"\nTotal de conexões: {len(connections)}\n")
    
    for conn in connections:
        print(f"Conexão #{conn['id']}:")
        print(f"  - URL: {conn['url']}")
        print(f"  - Host: {conn['host']}")
        print(f"  - Status: {conn['status']}")
        print(f"  - Mensagens: {conn['message_count']}")
        print(f"  - Início: {conn['start_time'].strftime('%H:%M:%S')}")
        print()
    
    # Mostra detalhes das mensagens da primeira conexão
    print("=" * 70)
    print(f"💬 Mensagens da Conexão #1 ({flow_id_1})")
    print("=" * 70)
    print()
    
    messages = ws_history.get_messages(flow_id_1)
    for i, msg in enumerate(messages, 1):
        direction = "Cliente → Servidor" if msg['from_client'] else "Servidor → Cliente"
        msg_type = "Binário" if msg['is_binary'] else "Texto"
        timestamp = msg['timestamp'].strftime('%H:%M:%S.%f')[:-3]
        
        print(f"Mensagem #{i}:")
        print(f"  - Timestamp: {timestamp}")
        print(f"  - Direção: {direction}")
        print(f"  - Tipo: {msg_type}")
        print(f"  - Tamanho: {msg['size']} bytes")
        print(f"  - Conteúdo: {msg['content']}")
        print()
    
    # Fecha primeira conexão
    print("=" * 70)
    print("🔌 Fechando Conexão #1...")
    print("=" * 70)
    ws_history.close_connection(flow_id_1)
    conn_info = ws_history.get_connection_info(flow_id_1)
    print(f"✓ Conexão fechada às {conn_info['end_time'].strftime('%H:%M:%S')}")
    print(f"  Status: {conn_info['status']}")
    print()
    
    # Resumo final
    print("=" * 70)
    print("✅ Demo Concluída!")
    print("=" * 70)
    print()
    print("Esta demo ilustra como o InteceptProxy rastreia conexões WebSocket.")
    print("Na interface gráfica, você verá:")
    print("  • Lista de todas as conexões WebSocket")
    print("  • Mensagens em tempo real")
    print("  • Suporte para texto e dados binários")
    print("  • Histórico completo de comunicação")
    print()
    print("Para usar:")
    print("  1. Inicie o InteceptProxy: python intercept_proxy.py")
    print("  2. Acesse a aba 'WebSocket 🔌'")
    print("  3. Configure seu navegador/app para usar o proxy")
    print("  4. Estabeleça conexões WebSocket")
    print()


if __name__ == "__main__":
    try:
        demo_websocket_history()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante a demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
