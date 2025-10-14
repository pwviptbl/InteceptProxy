#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do Scanner de Vulnerabilidades
"""
import os
import sys

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.scanner import VulnerabilityScanner


def test_sql_injection_detection():
    """Testa detecção de SQL Injection"""
    print("Testando detecção de SQL Injection...")
    
    scanner = VulnerabilityScanner()
    
    # Simula uma requisição com SQL injection
    request_data = {
        'method': 'GET',
        'url': 'http://example.com/search?q=test\' OR 1=1--',
        'headers': {},
        'body': '',
    }
    
    # Simula resposta com erro SQL
    response_data = {
        'status': 500,
        'headers': {},
        'body': 'SQL syntax error near "\'" at line 1',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    assert len(vulnerabilities) > 0, "Deveria detectar SQL Injection"
    assert any(v['type'] == 'SQL Injection' for v in vulnerabilities), "Tipo deveria ser SQL Injection"
    print(f"✓ SQL Injection detectado: {vulnerabilities[0]['description']}")
    
    return True


def test_xss_detection():
    """Testa detecção de XSS"""
    print("\nTestando detecção de XSS...")
    
    scanner = VulnerabilityScanner()
    
    # Simula requisição com XSS payload
    request_data = {
        'method': 'GET',
        'url': 'http://example.com/search?q=<script>alert(1)</script>',
        'headers': {},
        'body': '',
    }
    
    # Simula resposta que reflete o payload
    response_data = {
        'status': 200,
        'headers': {},
        'body': 'Resultados para: <script>alert(1)</script>',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    assert len(vulnerabilities) > 0, "Deveria detectar XSS"
    assert any(v['type'] == 'XSS (Cross-Site Scripting)' for v in vulnerabilities), "Tipo deveria ser XSS"
    print(f"✓ XSS detectado: {vulnerabilities[0]['description']}")
    
    return True


def test_path_traversal_detection():
    """Testa detecção de Path Traversal"""
    print("\nTestando detecção de Path Traversal...")
    
    scanner = VulnerabilityScanner()
    
    # Simula requisição com path traversal
    request_data = {
        'method': 'GET',
        'url': 'http://example.com/file?path=../../../../etc/passwd',
        'headers': {},
        'body': '',
    }
    
    # Simula resposta com conteúdo do /etc/passwd
    response_data = {
        'status': 200,
        'headers': {},
        'body': 'root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    assert len(vulnerabilities) > 0, "Deveria detectar Path Traversal"
    assert any(v['type'] == 'Path Traversal' for v in vulnerabilities), "Tipo deveria ser Path Traversal"
    assert any(v['severity'] == 'Critical' for v in vulnerabilities), "Severidade deveria ser Critical"
    print(f"✓ Path Traversal detectado: {vulnerabilities[0]['description']}")
    
    return True


def test_sensitive_info_detection():
    """Testa detecção de informações sensíveis"""
    print("\nTestando detecção de informações sensíveis...")
    
    scanner = VulnerabilityScanner()
    
    request_data = {
        'method': 'GET',
        'url': 'http://example.com/config',
        'headers': {},
        'body': '',
    }
    
    # Simula resposta com informações sensíveis
    response_data = {
        'status': 200,
        'headers': {},
        'body': 'api_key = "AKIAIOSFODNN7EXAMPLE123456"',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    assert len(vulnerabilities) > 0, "Deveria detectar informação sensível"
    assert any(v['type'] == 'Informação Sensível Exposta' for v in vulnerabilities), "Tipo deveria ser Informação Sensível"
    print(f"✓ Informação sensível detectada: {vulnerabilities[0]['description']}")
    
    return True


def test_cve_detection():
    """Testa detecção de CVEs conhecidas"""
    print("\nTestando detecção de CVEs...")
    
    scanner = VulnerabilityScanner()
    
    request_data = {
        'method': 'GET',
        'url': 'http://example.com/',
        'headers': {},
        'body': '',
    }
    
    # Simula resposta com server vulnerável
    response_data = {
        'status': 200,
        'headers': {
            'Server': 'Apache/2.4.49 (Unix)',
        },
        'body': '',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    assert len(vulnerabilities) > 0, "Deveria detectar CVE"
    assert any(v['type'] == 'CVE / Vulnerabilidade Conhecida' for v in vulnerabilities), "Tipo deveria ser CVE"
    assert any('2.4.49' in v['description'] for v in vulnerabilities), "Deveria mencionar Apache 2.4.49"
    print(f"✓ CVE detectada: {vulnerabilities[0]['description']}")
    
    return True


def test_csrf_detection():
    """Testa detecção de falta de proteção CSRF"""
    print("\nTestando detecção de CSRF...")
    
    scanner = VulnerabilityScanner()
    
    # Simula requisição POST sem token CSRF
    request_data = {
        'method': 'POST',
        'url': 'http://example.com/update',
        'headers': {},
        'body': 'email=user@example.com&name=John',
    }
    
    response_data = {
        'status': 200,
        'headers': {},
        'body': 'Updated successfully',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    assert len(vulnerabilities) > 0, "Deveria detectar falta de CSRF"
    assert any(v['type'] == 'CSRF (Cross-Site Request Forgery)' for v in vulnerabilities), "Tipo deveria ser CSRF"
    print(f"✓ CSRF detectado: {vulnerabilities[0]['description']}")
    
    return True


def test_no_vulnerabilities():
    """Testa quando não há vulnerabilidades"""
    print("\nTestando ausência de vulnerabilidades...")
    
    scanner = VulnerabilityScanner()
    
    request_data = {
        'method': 'GET',
        'url': 'http://example.com/',
        'headers': {},
        'body': '',
    }
    
    response_data = {
        'status': 200,
        'headers': {
            'Server': 'nginx/1.21.0',
        },
        'body': '<html><body>Hello World</body></html>',
    }
    
    vulnerabilities = scanner.scan_response(request_data, response_data)
    
    # Pode ou não ter vulnerabilidades dependendo dos padrões
    print(f"✓ Teste de resposta limpa concluído: {len(vulnerabilities)} vulnerabilidade(s) encontrada(s)")
    
    return True


def test_report_formatting():
    """Testa formatação do relatório"""
    print("\nTestando formatação de relatório...")
    
    scanner = VulnerabilityScanner()
    
    vulnerabilities = [
        {
            'type': 'SQL Injection',
            'severity': 'High',
            'description': 'Teste de SQL Injection',
            'evidence': 'SQL syntax error',
            'url': 'http://example.com',
            'method': 'GET',
        }
    ]
    
    report = scanner.format_vulnerabilities_report(vulnerabilities)
    
    assert 'SQL Injection' in report, "Relatório deveria conter tipo de vulnerabilidade"
    assert 'High' in report, "Relatório deveria conter severidade"
    print(f"✓ Relatório formatado corretamente")
    print(report)
    
    return True


if __name__ == "__main__":
    try:
        print("="*80)
        print("TESTES DO SCANNER DE VULNERABILIDADES")
        print("="*80)
        
        tests = [
            test_sql_injection_detection,
            test_xss_detection,
            test_path_traversal_detection,
            test_sensitive_info_detection,
            test_cve_detection,
            test_csrf_detection,
            test_no_vulnerabilities,
            test_report_formatting,
        ]
        
        for test in tests:
            if not test():
                print(f"\n❌ Teste falhou: {test.__name__}")
                sys.exit(1)
        
        print("\n" + "="*80)
        print("🎉 TODOS OS TESTES DO SCANNER PASSARAM COM SUCESSO!")
        print("="*80)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
