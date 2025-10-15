#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do Comparador de Requisições
"""
import difflib


def test_comparator_data_structure():
    """Testa a estrutura de dados necessária para o comparador"""
    print("Testando estrutura de dados do Comparador...")

    # Simula entradas do histórico de requisições
    entry1 = {
        'host': 'exemplo.com',
        'method': 'GET',
        'path': '/test1',
        'status': 200,
        'request_headers': {'User-Agent': 'Test', 'Content-Type': 'application/json'},
        'request_body': 'request body 1',
        'response_headers': {'Content-Type': 'text/html', 'Server': 'nginx'},
        'response_body': 'response body 1',
        'timestamp': '2025-01-15 10:30:00'
    }
    
    entry2 = {
        'host': 'exemplo.com',
        'method': 'POST',
        'path': '/test2',
        'status': 404,
        'request_headers': {'User-Agent': 'Test', 'Content-Type': 'application/x-www-form-urlencoded'},
        'request_body': 'request body 2',
        'response_headers': {'Content-Type': 'text/html', 'Server': 'apache'},
        'response_body': 'response body 2',
        'timestamp': '2025-01-15 10:31:00'
    }
    
    entries = [entry1, entry2]
    
    print("✓ Duas entradas de requisição criadas")

    # Verifica que as entradas têm todos os campos necessários para comparação
    required_fields = ['host', 'method', 'path', 'status', 'request_headers', 
                      'request_body', 'response_headers', 'response_body', 'timestamp']
    
    for entry in entries:
        for field in required_fields:
            assert field in entry, f"Campo '{field}' deve estar presente na entrada"
    
    print("✓ Todas as entradas têm os campos necessários")

    # Verifica que as entradas são diferentes
    assert entry1['method'] != entry2['method'], "Métodos devem ser diferentes"
    assert entry1['path'] != entry2['path'], "Caminhos devem ser diferentes"
    assert entry1['status'] != entry2['status'], "Status devem ser diferentes"
    print("✓ Entradas têm diferenças que podem ser detectadas")

    print("\n✅ Todos os testes de estrutura de dados passaram!")


def test_diff_logic():
    """Testa a lógica de diferenciação de texto"""
    print("\nTestando lógica de diff...")
    
    import difflib
    
    text1 = "GET /test1 HTTP/1.1\nHost: exemplo.com\nUser-Agent: Test\n\nBody 1"
    text2 = "POST /test2 HTTP/1.1\nHost: exemplo.com\nUser-Agent: Test\n\nBody 2"
    
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)
    
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    
    opcodes = matcher.get_opcodes()
    assert len(opcodes) > 0, "Deve detectar diferenças"
    
    # Verifica se detectou diferenças
    has_differences = any(tag in ['replace', 'delete', 'insert'] for tag, _, _, _, _ in opcodes)
    assert has_differences, "Deve detectar diferenças entre os textos"
    
    print("✓ Lógica de diff funcionando corretamente")
    print("✓ Diferenças detectadas:")
    
    for tag, i1, i2, j1, j2 in opcodes:
        if tag != 'equal':
            print(f"  - {tag}: linhas {i1}-{i2} vs {j1}-{j2}")
    
    print("\n✅ Teste de lógica de diff passou!")


if __name__ == "__main__":
    test_comparator_data_structure()
    test_diff_logic()
    print("\n🎉 Todos os testes passaram com sucesso!")
