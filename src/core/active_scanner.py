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

    def _check_boolean_sqli(self, base_request: Dict, point: Dict) -> List[Dict]:
        """Testa SQL Injection Boolean-Based (TRUE vs FALSE)."""
        vulnerabilities = []
        
        try:
            # Obtém resposta original
            original_response = self._send_modified_request(base_request, point, point['value'])
            original_len = len(original_response.text)
            original_status = original_response.status_code
            
            # Testa payload TRUE (condição verdadeira)
            true_payload = f"{point['value']}' AND '1'='1"
            true_response = self._send_modified_request(base_request, point, true_payload)
            true_len = len(true_response.text)
            
            # Testa payload FALSE (condição falsa)
            false_payload = f"{point['value']}' AND '1'='2"
            false_response = self._send_modified_request(base_request, point, false_payload)
            false_len = len(false_response.text)
            
            # Se TRUE é similar ao original mas FALSE é diferente, há SQL Injection
            true_diff = abs(original_len - true_len)
            false_diff = abs(original_len - false_len)
            
            # Considera que há diferença se variar mais que 10% ou 100 bytes
            threshold = max(100, original_len * 0.1)
            
            if true_diff < threshold and false_diff > threshold:
                vuln = {
                    'type': 'SQL Injection (Boolean-Based)',
                    'severity': 'High',
                    'url': base_request['url'],
                    'method': base_request['method'],
                    'description': f"SQL Injection Boolean-Based detectado no parâmetro '{point['name']}'. "
                                   f"Respostas TRUE e FALSE diferem significativamente.",
                    'evidence': f"Original: {original_len} bytes, TRUE: {true_len} bytes, FALSE: {false_len} bytes",
                }
                vulnerabilities.append(vuln)
                log.warning(f"Boolean-Based SQL Injection detectado em {base_request['url']} no parâmetro {point['name']}")
                
        except requests.exceptions.RequestException as e:
            log.error(f"Erro no teste de Boolean SQLi para {base_request['url']}: {e}")
        
        return vulnerabilities

    def _check_time_based_sqli(self, base_request: Dict, point: Dict) -> List[Dict]:
        """Testa SQL Injection Time-Based (SLEEP/WAITFOR)."""
        vulnerabilities = []
        
        # Payloads para diferentes bancos de dados
        time_payloads = [
            ("' OR SLEEP(5)--", "MySQL"),
            ("'; WAITFOR DELAY '0:0:5'--", "MSSQL"),
            ("'||pg_sleep(5)--", "PostgreSQL"),
        ]
        
        try:
            # Mede tempo de resposta normal
            import time
            start = time.time()
            self._send_modified_request(base_request, point, point['value'])
            normal_time = time.time() - start
            
            for payload, db_type in time_payloads:
                try:
                    full_payload = f"{point['value']}{payload}"
                    start = time.time()
                    self._send_modified_request(base_request, point, full_payload)
                    delay_time = time.time() - start
                    
                    # Se demorou pelo menos 4 segundos a mais, detectou
                    if delay_time - normal_time >= 4:
                        vuln = {
                            'type': 'SQL Injection (Time-Based)',
                            'severity': 'High',
                            'url': base_request['url'],
                            'method': base_request['method'],
                            'description': f"SQL Injection Time-Based detectado no parâmetro '{point['name']}'. "
                                           f"Possível banco de dados: {db_type}",
                            'evidence': f"Delay detectado: {delay_time - normal_time:.2f} segundos",
                        }
                        vulnerabilities.append(vuln)
                        log.warning(f"Time-Based SQL Injection ({db_type}) detectado em {base_request['url']} no parâmetro {point['name']}")
                        return vulnerabilities  # Retorna na primeira detecção
                        
                except requests.exceptions.RequestException as e:
                    log.debug(f"Erro no teste time-based para {db_type}: {e}")
                    
        except requests.exceptions.RequestException as e:
            log.error(f"Erro no teste de Time-Based SQLi para {base_request['url']}: {e}")
        
        return vulnerabilities

    def _check_command_injection(self, base_request: Dict, point: Dict) -> List[Dict]:
        """Testa Command Injection."""
        vulnerabilities = []
        
        # Comandos que podem indicar execução
        cmd_payloads = [
            ("; sleep 5", "Unix/Linux"),
            ("| sleep 5", "Unix/Linux"),
            ("& timeout /t 5", "Windows"),
            ("; whoami", "Unix/Linux"),
            ("| whoami", "Unix/Linux"),
        ]
        
        # Padrões que indicam sucesso de execução
        success_patterns = [
            r"uid=\d+",  # Output do whoami no Unix
            r"root|daemon|www-data",  # Usuários comuns
        ]
        
        try:
            # Testa cada payload
            for payload, os_type in cmd_payloads:
                try:
                    full_payload = f"{point['value']}{payload}"
                    
                    if "sleep" in payload or "timeout" in payload:
                        # Testa time-based
                        import time
                        start = time.time()
                        response = self._send_modified_request(base_request, point, full_payload)
                        delay = time.time() - start
                        
                        if delay >= 4:
                            vuln = {
                                'type': 'Command Injection (Time-Based)',
                                'severity': 'Critical',
                                'url': base_request['url'],
                                'method': base_request['method'],
                                'description': f"Command Injection detectado no parâmetro '{point['name']}'. "
                                               f"Sistema operacional: {os_type}",
                                'evidence': f"Delay detectado: {delay:.2f} segundos com payload '{payload}'",
                            }
                            vulnerabilities.append(vuln)
                            log.critical(f"Command Injection detectado em {base_request['url']} no parâmetro {point['name']}")
                            return vulnerabilities
                    else:
                        # Testa output-based
                        response = self._send_modified_request(base_request, point, full_payload)
                        for pattern in success_patterns:
                            if re.search(pattern, response.text, re.IGNORECASE):
                                vuln = {
                                    'type': 'Command Injection',
                                    'severity': 'Critical',
                                    'url': base_request['url'],
                                    'method': base_request['method'],
                                    'description': f"Command Injection detectado no parâmetro '{point['name']}'. "
                                                   f"Sistema operacional: {os_type}",
                                    'evidence': re.search(pattern, response.text, re.IGNORECASE).group(0),
                                }
                                vulnerabilities.append(vuln)
                                log.critical(f"Command Injection detectado em {base_request['url']} no parâmetro {point['name']}")
                                return vulnerabilities
                                
                except requests.exceptions.RequestException as e:
                    log.debug(f"Erro no teste de command injection: {e}")
                    
        except Exception as e:
            log.error(f"Erro no teste de Command Injection para {base_request['url']}: {e}")
        
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
            # Error-Based SQL Injection
            vulnerabilities.extend(self._check_sql_injection(base_request, point))
            
            # Boolean-Based SQL Injection (novo)
            vulnerabilities.extend(self._check_boolean_sqli(base_request, point))
            
            # Time-Based SQL Injection (novo)
            vulnerabilities.extend(self._check_time_based_sqli(base_request, point))
            
            # Command Injection (novo)
            vulnerabilities.extend(self._check_command_injection(base_request, point))
            
            # XSS
            vulnerabilities.extend(self._check_xss(base_request, point))

        # Remove duplicatas
        unique_vulns = [dict(t) for t in {tuple(d.items()) for d in vulnerabilities}]

        if unique_vulns:
            log.warning(f"{len(unique_vulns)} vulnerabilidades ativas encontradas para {base_request['url']}")

        return unique_vulns
