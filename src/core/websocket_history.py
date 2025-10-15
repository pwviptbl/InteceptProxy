from datetime import datetime
from typing import List, Dict, Optional


class WebSocketHistory:
    """Gerencia o histórico de conexões e mensagens WebSocket"""

    def __init__(self):
        self.connections = {}  # {flow_id: connection_info}
        self.messages = {}  # {flow_id: [messages]}
        self.current_id = 0

    def add_connection(self, flow_id: str, url: str, host: str):
        """Registra uma nova conexão WebSocket"""
        self.current_id += 1
        self.connections[flow_id] = {
            'id': self.current_id,
            'flow_id': flow_id,
            'url': url,
            'host': host,
            'start_time': datetime.now(),
            'end_time': None,
            'status': 'active',
            'message_count': 0,
        }
        self.messages[flow_id] = []

    def add_message(self, flow_id: str, message: bytes, from_client: bool):
        """Adiciona uma mensagem WebSocket ao histórico"""
        if flow_id not in self.messages:
            return

        try:
            # Tenta decodificar como texto
            content = message.decode('utf-8', errors='replace')
            is_binary = False
        except:
            content = message.hex()
            is_binary = True

        msg_entry = {
            'timestamp': datetime.now(),
            'from_client': from_client,
            'content': content,
            'is_binary': is_binary,
            'size': len(message),
        }
        
        self.messages[flow_id].append(msg_entry)
        
        # Atualiza contador de mensagens
        if flow_id in self.connections:
            self.connections[flow_id]['message_count'] += 1

    def close_connection(self, flow_id: str):
        """Marca uma conexão WebSocket como fechada"""
        if flow_id in self.connections:
            self.connections[flow_id]['end_time'] = datetime.now()
            self.connections[flow_id]['status'] = 'closed'

    def get_connections(self) -> List[Dict]:
        """Retorna todas as conexões WebSocket"""
        return list(self.connections.values())

    def get_messages(self, flow_id: str) -> List[Dict]:
        """Retorna todas as mensagens de uma conexão específica"""
        return self.messages.get(flow_id, [])

    def get_connection_info(self, flow_id: str) -> Optional[Dict]:
        """Retorna informações sobre uma conexão específica"""
        return self.connections.get(flow_id)

    def clear_history(self):
        """Limpa todo o histórico de WebSocket"""
        self.connections = {}
        self.messages = {}
        self.current_id = 0
