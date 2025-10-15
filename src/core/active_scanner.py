"""
Módulo de Scanner Ativo de Vulnerabilidades
Este módulo testa ativamente os endpoints em busca de vulnerabilidades,
enviando payloads específicos e analisando as respostas.
"""
import requests
import re
from typing import Dict, List, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .logger_config import log


class ActiveScanner:
    """
    Realiza a varredura ativa em requisições HTTP para encontrar vulnerabilidades.
    """

    def __init__(self):
        """
        Inicializa o ActiveScanner.
        """
        self.session = requests.Session()
        self.session.verify = False  # Desabilita verificação de certificado SSL

        # Padrões de erro para SQL Injection
        self.sql_error_patterns = [
            r"(?i)sql\s+syntax", r"(?i)mysql_fetch", r"(?i)unclosed\s+quotation\s+mark",
            r"(?i)quoted\s+string\s+not\s+properly\s+terminated", r"(?i)ora-\d{5}",
            r"(?i)postgresql.*error", r"(?i)microsoft\s+sql\s+server", r"(?i)odbc\s+driver"
        ]

        log.info("Scanner Ativo inicializado.")

    def _get_insertion_points(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifica todos os pontos de inserção em uma requisição.
        """
        points = []
        parsed_url = urlparse(request['url'])
        query_params = parse_qs(parsed_url.query)

        for name, values in query_params.items():
            for value in values:
                points.append({'type': 'url', 'name': name, 'value': value})

        headers = {k.lower(): v for k, v in request.get('headers', {}).items()}
        if 'content-type' in headers and 'application/x-www-form-urlencoded' in headers['content-type']:
            if request.get('body'):
                body_params = parse_qs(request['body'])
                for name, values in body_params.items():
                    for value in values:
                        points.append({'type': 'body', 'name': name, 'value': value})

        log.debug(f"Pontos de inserção encontrados: {len(points)}")
        return points

    def _send_modified_request(self, original_request: Dict, insertion_point: Dict, payload: str) -> requests.Response:
        """
        Envia uma requisição HTTP modificada com um payload em um ponto de inserção.
        """
        method = original_request['method']
        url = original_request['url']
        headers = original_request.get('headers', {})
        body = original_request.get('body', '')
        parsed_url = urlparse(url)

        if insertion_point['type'] == 'url':
            query_params = parse_qs(parsed_url.query, keep_blank_values=True)
            query_params[insertion_point['name']] = [payload]
            new_query = urlencode(query_params, doseq=True)
            url_parts = list(parsed_url)
            url_parts[4] = new_query
            new_url = urlunparse(url_parts)
            return self.session.request(method, new_url, headers=headers, data=body.encode('utf-8'), timeout=10)

        elif insertion_point['type'] == 'body':
            body_params = parse_qs(body, keep_blank_values=True)
            body_params[insertion_point['name']] = [payload]
            new_body = urlencode(body_params, doseq=True)
            headers['Content-Length'] = str(len(new_body))
            return self.session.request(method, url, headers=headers, data=new_body.encode('utf-8'), timeout=10)

        return self.session.request(method, url, headers=headers, data=body.encode('utf-8'), timeout=10)

    def _check_sql_injection(self, base_request: Dict, point: Dict) -> List[Dict]:
        """Testa a vulnerabilidade de SQL Injection (Error-Based)."""
        vulnerabilities = []
        sqli_payloads = ["'", "\"", "' OR 1=1 --"]

        for payload in sqli_payloads:
            try:
                full_payload = f"{point['value']}{payload}"
                response = self._send_modified_request(base_request, point, full_payload)

                for pattern in self.sql_error_patterns:
                    if re.search(pattern, response.text, re.IGNORECASE):
                        vuln = {
                            'type': 'SQL Injection (Error-Based)',
                            'severity': 'High',
                            'url': base_request['url'],
                            'method': base_request['method'],
                            'description': f"Possível SQL Injection detectado no parâmetro '{point['name']}' com o payload '{payload}'.",
                            'evidence': re.search(pattern, response.text, re.IGNORECASE).group(0),
                        }
                        vulnerabilities.append(vuln)
                        log.warning(f"SQL Injection detectado em {base_request['url']} no parâmetro {point['name']}")
                        return vulnerabilities # Retorna na primeira detecção
            except requests.exceptions.RequestException as e:
                log.error(f"Erro no teste de SQLi para {base_request['url']}: {e}")
        return vulnerabilities

    def _check_xss(self, base_request: Dict, point: Dict) -> List[Dict]:
        """Testa a vulnerabilidade de XSS Refletido."""
        vulnerabilities = []
        xss_payload = "activescanner<xss>test"

        try:
            full_payload = f"{point['value']}{xss_payload}"
            response = self._send_modified_request(base_request, point, full_payload)

            if xss_payload in response.text:
                vuln = {
                    'type': 'Cross-Site Scripting (XSS)',
                    'severity': 'High',
                    'url': base_request['url'],
                    'method': base_request['method'],
                    'description': f"Payload de XSS refletido no parâmetro '{point['name']}'.",
                    'evidence': xss_payload,
                }
                vulnerabilities.append(vuln)
                log.warning(f"XSS Refletido detectado em {base_request['url']} no parâmetro {point['name']}")
        except requests.exceptions.RequestException as e:
            log.error(f"Erro no teste de XSS para {base_request['url']}: {e}")

        return vulnerabilities

    def scan_request(self, base_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Orquestra a varredura de uma única requisição, executando todos os checks.
        """
        vulnerabilities = []
        log.info(f"Iniciando varredura ativa em: {base_request.get('method')} {base_request.get('url')}")
        insertion_points = self._get_insertion_points(base_request)

        for point in insertion_points:
            log.debug(f"Testando ponto de inserção: {point['type']} - {point['name']}")

            # Executa os checks de vulnerabilidade
            vulnerabilities.extend(self._check_sql_injection(base_request, point))
            vulnerabilities.extend(self._check_xss(base_request, point))

        # Remove duplicatas
        unique_vulns = [dict(t) for t in {tuple(d.items()) for d in vulnerabilities}]

        if unique_vulns:
            log.warning(f"{len(unique_vulns)} vulnerabilidades ativas encontradas para {base_request['url']}")

        return unique_vulns
