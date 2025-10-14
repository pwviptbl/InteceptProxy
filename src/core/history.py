from datetime import datetime
from mitmproxy import http


class RequestHistory:
    """Gerencia o histórico de requisições"""

    def __init__(self):
        self.history = []
        self.max_items = 1000
        self.current_id = 0

    def add_request(self, flow: http.HTTPFlow, vulnerabilities=None):
        """Adiciona uma requisição ao histórico"""
        request = flow.request
        response = flow.response

        # Incrementa o ID para cada nova requisição
        self.current_id += 1

        # Extrai informações da requisição
        entry = {
            'id': self.current_id,
            'timestamp': datetime.now(),
            'host': request.pretty_host,
            'method': request.method,
            'url': request.pretty_url,
            'path': request.path,
            'status': response.status_code if response else 0,
            'request_headers': dict(request.headers),
            'request_body': request.content.decode('utf-8', errors='ignore') if request.content else '',
            'response_headers': dict(response.headers) if response else {},
            'response_body': response.content.decode('utf-8', errors='ignore') if response and response.content else '',
            'vulnerabilities': vulnerabilities or [],  # Adiciona lista de vulnerabilidades
        }

        self.history.append(entry)

        # Limita o tamanho do histórico
        if len(self.history) > self.max_items:
            self.history.pop(0)

    def get_history(self):
        """Retorna todo o histórico"""
        return self.history

    def clear_history(self):
        """Limpa o histórico"""
        self.history = []
        self.current_id = 0

    def get_new_entries(self, last_id=0):
        """Retorna apenas as entradas mais novas que o último ID conhecido."""
        if not last_id or not self.history:
            return self.history

        # Encontra o índice da primeira nova entrada
        first_new_index = -1
        for i, entry in enumerate(reversed(self.history)):
            if entry['id'] <= last_id:
                break
            first_new_index = len(self.history) - 1 - i

        if first_new_index != -1:
            return self.history[first_new_index:]
        else:
            return []
