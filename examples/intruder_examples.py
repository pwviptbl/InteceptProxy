#!/usr/bin/env python3
"""
Exemplo de uso do Intruder Avançado via código.

Este script demonstra como usar o AdvancedSender programaticamente
para realizar diferentes tipos de ataques.
"""
import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.advanced_sender import AdvancedSender, load_payloads_from_file
import queue


def example_sniper_attack():
    """Exemplo de ataque Sniper"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Ataque Sniper")
    print("="*60)
    
    # Request com duas posições de payload
    raw_request = """GET /search?q=§test§&category=§all§ HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0

"""
    
    # Carregar payloads de arquivo (ou criar lista)
    payloads = ["admin", "user", "test", "root"]
    
    # Criar sender
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='sniper',
        payload_sets=[payloads],
        num_threads=2
    )
    
    # Gerar requisições (sem enviar)
    requests = sender.generate_requests()
    
    print(f"Requisições geradas: {len(requests)}")
    print("\nPrimeiras 3 requisições:")
    for i, (req, payloads_used) in enumerate(requests[:3]):
        print(f"\n{i+1}. Payloads: {payloads_used}")
        print(f"   First line: {req.split(chr(10))[0]}")


def example_battering_ram_attack():
    """Exemplo de ataque Battering Ram"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Ataque Battering Ram")
    print("="*60)
    
    raw_request = """POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

username=§admin§&password=§admin§
"""
    
    payloads = ["test123", "admin", "root"]
    
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='battering_ram',
        payload_sets=[payloads],
        num_threads=2
    )
    
    requests = sender.generate_requests()
    
    print(f"Requisições geradas: {len(requests)}")
    print("\nTodas as requisições:")
    for i, (req, payloads_used) in enumerate(requests):
        body = req.split('\n\n')[1] if '\n\n' in req else ''
        print(f"{i+1}. Payloads: {payloads_used} → {body.strip()}")


def example_pitchfork_attack():
    """Exemplo de ataque Pitchfork"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Ataque Pitchfork")
    print("="*60)
    
    raw_request = """POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

username=§admin§&password=§password§
"""
    
    usernames = ["admin", "user", "guest"]
    passwords = ["pass123", "12345", "abc"]
    
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='pitchfork',
        payload_sets=[usernames, passwords],
        num_threads=2
    )
    
    requests = sender.generate_requests()
    
    print(f"Requisições geradas: {len(requests)}")
    print("\nCombinações:")
    for i, (req, payloads_used) in enumerate(requests):
        print(f"{i+1}. username={payloads_used[0]}, password={payloads_used[1]}")


def example_cluster_bomb_attack():
    """Exemplo de ataque Cluster Bomb"""
    print("\n" + "="*60)
    print("EXEMPLO 4: Ataque Cluster Bomb")
    print("="*60)
    
    raw_request = """GET /api?user=§admin§&id=§1§ HTTP/1.1
Host: api.example.com

"""
    
    users = ["admin", "user"]
    ids = ["1", "2", "3"]
    
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='cluster_bomb',
        payload_sets=[users, ids],
        num_threads=2
    )
    
    requests = sender.generate_requests()
    
    print(f"Requisições geradas: {len(requests)}")
    print("\nTodas as combinações:")
    for i, (req, payloads_used) in enumerate(requests):
        first_line = req.split('\n')[0]
        print(f"{i+1}. {payloads_used} → {first_line}")


def example_with_payload_processing():
    """Exemplo com processamento de payloads"""
    print("\n" + "="*60)
    print("EXEMPLO 5: Processamento de Payloads")
    print("="*60)
    
    raw_request = """GET /api?token=§test§ HTTP/1.1
Host: api.example.com

"""
    
    payloads = ["admin", "user", "test"]
    
    # Definir processadores
    processors = [
        [
            {'type': 'prefix', 'value': 'AUTH_'},
            {'type': 'suffix', 'value': '_123'},
            {'type': 'base64'}
        ]
    ]
    
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='sniper',
        payload_sets=[payloads],
        processors=processors,
        num_threads=2
    )
    
    requests = sender.generate_requests()
    
    print(f"Requisições geradas: {len(requests)}")
    print("\nPayloads processados:")
    for i, (req, payloads_used) in enumerate(requests):
        print(f"{i+1}. Original: {['admin', 'user', 'test'][i]}")
        print(f"   Processado: {payloads_used[0]}")
        print(f"   Na URL: {req.split(chr(10))[0]}\n")


def example_with_grep_extraction():
    """Exemplo com extração via grep"""
    print("\n" + "="*60)
    print("EXEMPLO 6: Grep Extraction")
    print("="*60)
    
    from core.advanced_sender import GrepExtractor
    
    # Simular respostas
    responses = [
        'HTTP/1.1 200 OK\nContent-Type: application/json\n\n{"token":"abc123xyz","user_id":42}',
        'HTTP/1.1 200 OK\nContent-Type: application/json\n\n{"token":"def456uvw","user_id":99}',
        'HTTP/1.1 401 Unauthorized\n\n{"error":"Invalid credentials"}',
    ]
    
    # Criar extrator com padrões
    patterns = [
        r'"token":"([^"]+)"',
        r'"user_id":(\d+)'
    ]
    
    extractor = GrepExtractor(patterns)
    
    print("Padrões de extração:")
    for p in patterns:
        print(f"  - {p}")
    
    print("\nResultados:")
    for i, response_text in enumerate(responses):
        extracted = extractor.extract(response_text)
        print(f"{i+1}. Extraído: {extracted}")


def example_loading_from_file():
    """Exemplo carregando payloads de arquivo"""
    print("\n" + "="*60)
    print("EXEMPLO 7: Carregando de Arquivo")
    print("="*60)
    
    # Verifica se os arquivos de exemplo existem
    examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples', 'intruder_payloads')
    users_file = os.path.join(examples_dir, 'usernames.txt')
    
    if os.path.exists(users_file):
        payloads = load_payloads_from_file(users_file)
        print(f"Carregados {len(payloads)} payloads de {users_file}")
        print(f"Primeiros 5: {payloads[:5]}")
    else:
        print(f"Arquivo de exemplo não encontrado: {users_file}")
        print("Execute este script do diretório raiz do projeto.")


def main():
    """Executa todos os exemplos"""
    print("="*60)
    print("EXEMPLOS DE USO DO INTRUDER AVANÇADO")
    print("="*60)
    
    try:
        example_sniper_attack()
        example_battering_ram_attack()
        example_pitchfork_attack()
        example_cluster_bomb_attack()
        example_with_payload_processing()
        example_with_grep_extraction()
        example_loading_from_file()
        
        print("\n" + "="*60)
        print("TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("="*60)
        print("\nPara usar na GUI:")
        print("1. Execute: python intercept_proxy.py")
        print("2. Vá para a aba '💥 Intruder'")
        print("3. Configure e inicie seu ataque!")
        
    except Exception as e:
        print(f"\nErro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
