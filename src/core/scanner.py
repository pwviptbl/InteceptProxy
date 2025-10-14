"""
Módulo de Scanner de Vulnerabilidades
Detecta vulnerabilidades comuns em requisições e respostas HTTP
"""
import re
from typing import Dict, List, Any
from .logger_config import log


class VulnerabilityScanner:
    """Scanner de vulnerabilidades para detecção automática de problemas de segurança"""
    
    def __init__(self):
        # Payloads para detecção de SQL Injection
        self.sql_injection_patterns = [
            r"(?i)sql\s+syntax",
            r"(?i)mysql_fetch",
            r"(?i)unclosed\s+quotation\s+mark",
            r"(?i)quoted\s+string\s+not\s+properly\s+terminated",
            r"(?i)ora-\d{5}",  # Oracle errors
            r"(?i)postgresql.*error",
            r"(?i)microsoft\s+sql\s+server",
            r"(?i)odbc\s+(microsoft|sql\s+server|driver)",
            r"(?i)sqlite.*error",
            r"(?i)warning.*mysql",
            r"(?i)pg_query\(\)",
            r"(?i)jdbc.*exception",
        ]
        
        # Padrões para detecção de XSS refletido
        self.xss_reflection_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'onerror\s*=',
            r'onload\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]
        
        # Padrões para Path Traversal
        self.path_traversal_patterns = [
            r'\.\./.*\.\./.*\.\.',  # Multiple ../
            r'\.\.[\\/]',
            r'[\\/]etc[\\/]passwd',
            r'[\\/]windows[\\/]win\.ini',
            r'[\\/]boot\.ini',
            r'%2e%2e%2f',  # URL encoded ../
            r'%252e%252e%252f',  # Double URL encoded
            r'\.\.%5c',  # Mixed encoding
        ]
        
        # Padrões de informações sensíveis
        self.sensitive_info_patterns = [
            (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]{3,})', 'Senha em texto claro'),
            (r'(?i)api[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{10,})', 'API Key exposta'),
            (r'(?i)secret[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{10,})', 'Secret Key exposta'),
            (r'(?i)token\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})', 'Token exposto'),
            (r'(?i)authorization:\s*bearer\s+([a-zA-Z0-9_\-\.]{20,})', 'Bearer Token exposto'),
            (r'(?i)aws[_-]?access[_-]?key[_-]?id\s*[:=]\s*["\']?(AKIA[A-Z0-9]{16})', 'AWS Access Key'),
            (r'(?i)private[_-]?key', 'Chave Privada mencionada'),
            (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', 'Chave Privada RSA'),
            (r'(?i)connection[_-]?string\s*[:=]', 'Connection String'),
            (r'(?i)mongodb://', 'MongoDB Connection String'),
            (r'(?i)mysql://|postgresql://', 'Database Connection String'),
        ]
        
        # CVEs e vulnerabilidades conhecidas (patterns básicos)
        self.cve_patterns = [
            (r'Apache/2\.4\.49', 'CVE-2021-41773 - Path Traversal Apache 2.4.49'),
            (r'Apache/2\.4\.50', 'CVE-2021-42013 - Path Traversal Apache 2.4.50'),
            (r'(?i)log4j.*2\.(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16)', 'Possível Log4Shell (CVE-2021-44228)'),
            (r'(?i)struts', 'Apache Struts - Verificar CVEs conhecidas'),
            (r'(?i)spring.*framework.*[45]\.', 'Spring Framework - Verificar Spring4Shell'),
            (r'(?i)phpMyAdmin/[234]\.', 'phpMyAdmin - Verificar CVEs conhecidas'),
            (r'(?i)WordPress/[45]\.', 'WordPress - Verificar vulnerabilidades conhecidas'),
            (r'(?i)Drupal\s+[78]\.', 'Drupal - Verificar Drupalgeddon'),
            (r'(?i)jQuery\s+(1\.|2\.|3\.[0-4])', 'jQuery versão antiga - XSS vulnerabilities'),
        ]
        
        # Padrões de CSRF
        self.csrf_indicators = [
            'csrf',
            'xsrf',
            '_token',
            'authenticity_token',
            'anti-forgery',
        ]
    
    def scan_response(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Escaneia uma resposta HTTP em busca de vulnerabilidades
        
        Args:
            request_data: Dados da requisição (method, url, headers, body)
            response_data: Dados da resposta (status, headers, body)
            
        Returns:
            Lista de vulnerabilidades encontradas
        """
        vulnerabilities = []
        
        # Detecção de SQL Injection
        sql_vulns = self._detect_sql_injection(request_data, response_data)
        vulnerabilities.extend(sql_vulns)
        
        # Detecção de XSS
        xss_vulns = self._detect_xss(request_data, response_data)
        vulnerabilities.extend(xss_vulns)
        
        # Detecção de Path Traversal
        path_vulns = self._detect_path_traversal(request_data, response_data)
        vulnerabilities.extend(path_vulns)
        
        # Detecção de informações sensíveis
        sensitive_vulns = self._detect_sensitive_info(response_data)
        vulnerabilities.extend(sensitive_vulns)
        
        # Detecção de CVEs conhecidas
        cve_vulns = self._detect_cve(response_data)
        vulnerabilities.extend(cve_vulns)
        
        # Detecção de CSRF
        csrf_vulns = self._detect_csrf(request_data, response_data)
        vulnerabilities.extend(csrf_vulns)
        
        return vulnerabilities
    
    def _detect_sql_injection(self, request_data: Dict, response_data: Dict) -> List[Dict]:
        """Detecta possíveis SQL Injection através de mensagens de erro"""
        vulnerabilities = []
        response_body = response_data.get('body', '')
        
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, response_body, re.IGNORECASE):
                vulnerabilities.append({
                    'type': 'SQL Injection',
                    'severity': 'High',
                    'description': 'Possível SQL Injection detectado - Mensagem de erro de banco de dados na resposta',
                    'evidence': re.search(pattern, response_body, re.IGNORECASE).group(0),
                    'url': request_data.get('url', ''),
                    'method': request_data.get('method', ''),
                })
                log.warning(f"SQL Injection detectado em {request_data.get('url', '')}")
                break  # Reporta apenas uma vez por resposta
        
        return vulnerabilities
    
    def _detect_xss(self, request_data: Dict, response_data: Dict) -> List[Dict]:
        """Detecta XSS refletido"""
        vulnerabilities = []
        response_body = response_data.get('body', '')
        request_params = request_data.get('body', '') + request_data.get('url', '')
        
        # Verifica se algum payload de XSS foi refletido na resposta
        for pattern in self.xss_reflection_patterns:
            matches_in_request = re.findall(pattern, request_params, re.IGNORECASE)
            for match in matches_in_request:
                if match in response_body:
                    vulnerabilities.append({
                        'type': 'XSS (Cross-Site Scripting)',
                        'severity': 'High',
                        'description': 'Possível XSS refletido - Payload encontrado na resposta',
                        'evidence': match[:100],  # Limita o tamanho da evidência
                        'url': request_data.get('url', ''),
                        'method': request_data.get('method', ''),
                    })
                    log.warning(f"XSS refletido detectado em {request_data.get('url', '')}")
                    return vulnerabilities  # Retorna após encontrar o primeiro
        
        return vulnerabilities
    
    def _detect_path_traversal(self, request_data: Dict, response_data: Dict) -> List[Dict]:
        """Detecta Path Traversal"""
        vulnerabilities = []
        request_url = request_data.get('url', '')
        request_body = request_data.get('body', '')
        response_body = response_data.get('body', '')
        
        # Verifica se há tentativa de path traversal na requisição
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, request_url) or re.search(pattern, request_body):
                # Verifica se obteve sucesso (arquivos sistema na resposta)
                if re.search(r'root:.*:0:0:|daemon:|bin:|sys:', response_body):
                    vulnerabilities.append({
                        'type': 'Path Traversal',
                        'severity': 'Critical',
                        'description': 'Path Traversal confirmado - Arquivo do sistema detectado na resposta',
                        'evidence': 'Conteúdo de arquivo do sistema encontrado',
                        'url': request_data.get('url', ''),
                        'method': request_data.get('method', ''),
                    })
                    log.critical(f"Path Traversal crítico detectado em {request_data.get('url', '')}")
                    break
                elif response_data.get('status', 0) == 200:
                    vulnerabilities.append({
                        'type': 'Path Traversal',
                        'severity': 'Medium',
                        'description': 'Possível Path Traversal - Tentativa detectada com resposta 200',
                        'evidence': re.search(pattern, request_url or request_body).group(0),
                        'url': request_data.get('url', ''),
                        'method': request_data.get('method', ''),
                    })
                    log.warning(f"Possível Path Traversal detectado em {request_data.get('url', '')}")
                    break
        
        return vulnerabilities
    
    def _detect_sensitive_info(self, response_data: Dict) -> List[Dict]:
        """Detecta informações sensíveis expostas"""
        vulnerabilities = []
        response_body = response_data.get('body', '')
        response_headers = response_data.get('headers', {})
        
        # Verifica no corpo da resposta
        for pattern, description in self.sensitive_info_patterns:
            matches = re.finditer(pattern, response_body, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append({
                    'type': 'Informação Sensível Exposta',
                    'severity': 'Medium',
                    'description': description,
                    'evidence': match.group(0)[:100],  # Limita tamanho
                    'url': '',  # Será preenchido pelo caller
                    'method': '',
                })
                log.warning(f"Informação sensível detectada: {description}")
                break  # Uma ocorrência por padrão é suficiente
        
        # Verifica headers sensíveis
        sensitive_headers = ['X-Api-Key', 'X-Auth-Token', 'Authorization']
        for header in sensitive_headers:
            if header.lower() in [h.lower() for h in response_headers.keys()]:
                vulnerabilities.append({
                    'type': 'Informação Sensível Exposta',
                    'severity': 'Low',
                    'description': f'Header sensível exposto: {header}',
                    'evidence': header,
                    'url': '',
                    'method': '',
                })
        
        return vulnerabilities
    
    def _detect_cve(self, response_data: Dict) -> List[Dict]:
        """Detecta versões de software com CVEs conhecidas"""
        vulnerabilities = []
        response_headers = response_data.get('headers', {})
        response_body = response_data.get('body', '')
        
        # Verifica Server header
        server_header = response_headers.get('Server', '') or response_headers.get('server', '')
        
        for pattern, description in self.cve_patterns:
            if re.search(pattern, server_header, re.IGNORECASE):
                vulnerabilities.append({
                    'type': 'CVE / Vulnerabilidade Conhecida',
                    'severity': 'High',
                    'description': description,
                    'evidence': server_header,
                    'url': '',
                    'method': '',
                })
                log.warning(f"CVE detectada: {description}")
            
            # Também verifica no corpo (para frameworks JavaScript, etc)
            if re.search(pattern, response_body, re.IGNORECASE):
                match = re.search(pattern, response_body, re.IGNORECASE)
                vulnerabilities.append({
                    'type': 'CVE / Vulnerabilidade Conhecida',
                    'severity': 'Medium',
                    'description': description,
                    'evidence': match.group(0),
                    'url': '',
                    'method': '',
                })
                log.warning(f"CVE detectada no body: {description}")
                break
        
        return vulnerabilities
    
    def _detect_csrf(self, request_data: Dict, response_data: Dict) -> List[Dict]:
        """Detecta possível falta de proteção CSRF"""
        vulnerabilities = []
        
        # Verifica apenas em requisições que modificam estado (POST, PUT, DELETE, PATCH)
        method = request_data.get('method', '').upper()
        if method not in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return vulnerabilities
        
        request_body = request_data.get('body', '')
        request_headers = request_data.get('headers', {})
        
        # Verifica se há algum token CSRF presente
        has_csrf_token = False
        
        for indicator in self.csrf_indicators:
            if indicator in request_body.lower():
                has_csrf_token = True
                break
            # Verifica headers
            for header_name in request_headers.keys():
                if indicator in header_name.lower():
                    has_csrf_token = True
                    break
        
        # Se não tem token CSRF em requisição que modifica estado
        if not has_csrf_token:
            vulnerabilities.append({
                'type': 'CSRF (Cross-Site Request Forgery)',
                'severity': 'Medium',
                'description': 'Possível falta de proteção CSRF - Token não detectado em requisição que modifica estado',
                'evidence': f'Método {method} sem token CSRF aparente',
                'url': request_data.get('url', ''),
                'method': method,
            })
            log.info(f"Possível falta de proteção CSRF em {request_data.get('url', '')}")
        
        return vulnerabilities
    
    def format_vulnerabilities_report(self, vulnerabilities: List[Dict]) -> str:
        """Formata um relatório de vulnerabilidades para exibição"""
        if not vulnerabilities:
            return "Nenhuma vulnerabilidade detectada."
        
        report = f"\n{'='*80}\n"
        report += f"RELATÓRIO DE VULNERABILIDADES ({len(vulnerabilities)} encontrada(s))\n"
        report += f"{'='*80}\n\n"
        
        for i, vuln in enumerate(vulnerabilities, 1):
            report += f"{i}. {vuln['type']}\n"
            report += f"   Severidade: {vuln['severity']}\n"
            report += f"   URL: {vuln.get('url', 'N/A')}\n"
            report += f"   Método: {vuln.get('method', 'N/A')}\n"
            report += f"   Descrição: {vuln['description']}\n"
            report += f"   Evidência: {vuln.get('evidence', 'N/A')}\n"
            report += f"   {'-'*78}\n"
        
        return report
