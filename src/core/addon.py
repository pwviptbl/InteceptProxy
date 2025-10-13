from mitmproxy import http
from urllib.parse import parse_qs, urlencode, urlparse

from .config import InterceptConfig
from .history import RequestHistory
from .logger_config import log


class InterceptAddon:
    """Addon do mitmproxy para interceptar e modificar requisições"""

    def __init__(self, config: InterceptConfig, history: RequestHistory = None):
        self.config = config
        self.history = history

    @staticmethod
    def _split_host_and_path(raw_host: str):
        """Normaliza host configurado, aceitando entradas com esquema ou URL completa."""
        if not raw_host:
            return "", ""
        parsed = urlparse(raw_host) if "://" in raw_host else urlparse(f"//{raw_host}")
        host = (parsed.hostname or parsed.netloc or "").lower()
        extra_path = parsed.path if (parsed.scheme or parsed.netloc) else ""
        if not host:
            host = raw_host.lower()
        return host, extra_path

    @staticmethod
    def _host_matches(request_host: str, rule_host: str) -> bool:
        """Verifica se o host da requisição corresponde ao host da regra."""
        if not rule_host:
            return True
        request_host = request_host.lower()
        rule_host = rule_host.lower()
        if request_host == rule_host:
            return True
        return request_host.endswith(f".{rule_host}")

    def request(self, flow: http.HTTPFlow) -> None:
        """Intercepta requisições HTTP"""
        # Se o proxy estiver pausado, ignora todas as regras e o histórico
        if self.config.is_paused():
            return

        request = flow.request

        for rule in self.config.get_rules():
            if not rule.get('enabled', True):
                continue

            # Verifica se a URL corresponde ao host e caminho configurados
            rule_host, host_path = self._split_host_and_path(rule.get('host', ''))
            normalized_rule_path = rule.get('path', '') or host_path or ""
            if normalized_rule_path and not normalized_rule_path.startswith('/'):
                normalized_rule_path = f"/{normalized_rule_path}"
            host_match = self._host_matches(request.pretty_host, rule_host)
            path_match = True if not normalized_rule_path else request.path.startswith(normalized_rule_path)

            if host_match and path_match:
                # Modifica parâmetros na query string (GET)
                if request.query:
                    query_dict = dict(request.query)
                    if rule['param_name'] in query_dict:
                        query_dict[rule['param_name']] = rule['param_value']
                        request.query.clear()
                        for key, value in query_dict.items():
                            request.query[key] = value
                        log.info(f"Regra GET aplicada: '{rule['param_name']}' -> '{rule['param_value']}' em {request.pretty_url}")

                # Modifica parâmetros no corpo (POST)
                if request.method == "POST" and request.content:
                    content_type = request.headers.get("content-type", "")

                    if "application/x-www-form-urlencoded" in content_type:
                        # Parse form data
                        body = request.content.decode('utf-8', errors='ignore')
                        params = parse_qs(body, keep_blank_values=True)

                        # Modifica o parâmetro se existir
                        if rule['param_name'] in params:
                            params[rule['param_name']] = [rule['param_value']]
                            # Reconstrói o corpo
                            new_body = urlencode(params, doseq=True)
                            request.content = new_body.encode('utf-8')
                            log.info(f"Regra POST aplicada: '{rule['param_name']}' -> '{rule['param_value']}' em {request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Intercepta respostas HTTP e armazena no histórico"""
        if self.history is not None:
            self.history.add_request(flow)
