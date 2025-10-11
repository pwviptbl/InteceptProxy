from datetime import datetime
from mitmproxy import http


class RequestHistory:
    """Gerencia o histórico de requisições"""

    def __init__(self):
        self.history = []
        self.max_items = 1000  # Limita o histórico a 1000 itens

    def add_request(self, flow: http.HTTPFlow):
        """Adiciona uma requisição ao histórico"""
        request = flow.request
        response = flow.response

        # Extrai informações da requisição
        entry = {
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
