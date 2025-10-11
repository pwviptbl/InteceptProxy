#!/usr/bin/env python3
"""
Exemplo de uso programático do InteceptProxy
Demonstra como criar e configurar regras via código
"""
import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from intercept_proxy import InterceptConfig


def exemplo_basico():
    """Exemplo básico: adicionar uma regra"""
    print("=" * 60)
    print("Exemplo 1: Adicionar uma regra básica")
    print("=" * 60)
    
    # Cria ou carrega configuração
    config = InterceptConfig()
    
    # Remove todas as regras existentes (para exemplo limpo)
    while len(config.get_rules()) > 0:
        config.remove_rule(0)
    
    # Adiciona uma regra
    config.add_rule(
        host="exemplo.com",
        path="/contato",
        param_name="Titulo",
        param_value="teste1"
    )
    
    print("\n✓ Regra adicionada:")
    print(f"  Host: exemplo.com")
    print(f"  Path: /contato")
    print(f"  Parâmetro: Titulo → teste1")
    
    return config


def exemplo_multiplas_regras():
    """Exemplo: adicionar múltiplas regras"""
    print("\n" + "=" * 60)
    print("Exemplo 2: Adicionar múltiplas regras")
    print("=" * 60)
    
    config = InterceptConfig()
    
    # Remove regras existentes
    while len(config.get_rules()) > 0:
        config.remove_rule(0)
    
    # Define regras
    regras = [
        {
            "host": "api.exemplo.com",
            "path": "/v1/users",
            "param_name": "limit",
            "param_value": "100"
        },
        {
            "host": "site.com",
            "path": "/search",
            "param_name": "q",
            "param_value": "python"
        },
        {
            "host": "teste.com",
            "path": "/login",
            "param_name": "redirect",
            "param_value": "/dashboard"
        }
    ]
    
    # Adiciona cada regra
    for regra in regras:
        config.add_rule(**regra)
    
    print(f"\n✓ {len(regras)} regras adicionadas:")
    for i, regra in enumerate(config.get_rules(), 1):
        print(f"\n  {i}. {regra['host']}{regra['path']}")
        print(f"     {regra['param_name']} → {regra['param_value']}")
    
    return config


def exemplo_gerenciar_regras():
    """Exemplo: gerenciar regras (ativar/desativar/remover)"""
    print("\n" + "=" * 60)
    print("Exemplo 3: Gerenciar regras existentes")
    print("=" * 60)
    
    config = InterceptConfig()
    
    # Adiciona algumas regras para exemplo
    while len(config.get_rules()) > 0:
        config.remove_rule(0)
    
    config.add_rule("site1.com", "/path1", "param1", "value1")
    config.add_rule("site2.com", "/path2", "param2", "value2")
    config.add_rule("site3.com", "/path3", "param3", "value3")
    
    print("\n✓ Estado inicial:")
    listar_regras(config)
    
    # Desativa a primeira regra
    print("\n→ Desativando regra #1...")
    config.toggle_rule(0)
    listar_regras(config)
    
    # Remove a segunda regra
    print("\n→ Removendo regra #2...")
    config.remove_rule(1)
    listar_regras(config)
    
    # Reativa a primeira regra
    print("\n→ Reativando regra #1...")
    config.toggle_rule(0)
    listar_regras(config)
    
    return config


def listar_regras(config):
    """Helper para listar regras"""
    regras = config.get_rules()
    print(f"\n  Total de regras: {len(regras)}")
    for i, regra in enumerate(regras, 1):
        status = "✓ Ativo" if regra.get('enabled', True) else "✗ Inativo"
        print(f"  {i}. [{status}] {regra['host']}{regra['path']}")
        print(f"     {regra['param_name']} → {regra['param_value']}")


def exemplo_condicional():
    """Exemplo: adicionar regras condicionalmente"""
    print("\n" + "=" * 60)
    print("Exemplo 4: Adicionar regras condicionalmente")
    print("=" * 60)
    
    config = InterceptConfig()
    
    # Remove regras existentes
    while len(config.get_rules()) > 0:
        config.remove_rule(0)
    
    # Configuração baseada em ambiente
    ambiente = "desenvolvimento"  # ou "produção", "teste"
    
    if ambiente == "desenvolvimento":
        print(f"\n→ Configurando para ambiente: {ambiente}")
        config.add_rule("localhost:3000", "/api", "debug", "true")
        config.add_rule("localhost:3000", "/api", "verbose", "1")
    elif ambiente == "teste":
        print(f"\n→ Configurando para ambiente: {ambiente}")
        config.add_rule("test.example.com", "/api", "mock", "true")
    elif ambiente == "produção":
        print(f"\n→ Configurando para ambiente: {ambiente}")
        # Menos regras em produção
        config.add_rule("api.example.com", "/v1", "timeout", "5000")
    
    listar_regras(config)
    
    return config


def exemplo_validacao():
    """Exemplo: validar regras antes de adicionar"""
    print("\n" + "=" * 60)
    print("Exemplo 5: Validação de regras")
    print("=" * 60)
    
    config = InterceptConfig()
    
    def adicionar_regra_validada(host, path, param_name, param_value):
        """Adiciona regra com validação"""
        # Validações
        if not host or not isinstance(host, str):
            print(f"  ✗ Host inválido: {host}")
            return False
        
        if not path or not path.startswith('/'):
            print(f"  ✗ Path deve começar com '/': {path}")
            return False
        
        if not param_name or len(param_name) == 0:
            print(f"  ✗ Nome do parâmetro vazio")
            return False
        
        # Adiciona a regra
        if config.add_rule(host, path, param_name, param_value):
            print(f"  ✓ Regra adicionada: {host}{path} → {param_name}={param_value}")
            return True
        else:
            print(f"  ✗ Erro ao adicionar regra")
            return False
    
    # Testa validações
    print("\n→ Testando validações:")
    adicionar_regra_validada("exemplo.com", "/test", "param", "value")  # OK
    adicionar_regra_validada("", "/test", "param", "value")  # Falha: host vazio
    adicionar_regra_validada("exemplo.com", "test", "param", "value")  # Falha: path sem /
    adicionar_regra_validada("exemplo.com", "/test", "", "value")  # Falha: param vazio
    
    return config


def exemplo_completo():
    """Exemplo completo de configuração"""
    print("\n" + "=" * 60)
    print("Exemplo 6: Configuração completa para um projeto")
    print("=" * 60)
    
    config = InterceptConfig()
    
    # Limpa configuração
    while len(config.get_rules()) > 0:
        config.remove_rule(0)
    
    print("\n→ Configurando interceptações para projeto web...")
    
    # API endpoints
    print("\n  APIs:")
    config.add_rule("api.myapp.com", "/v1/users", "per_page", "50")
    config.add_rule("api.myapp.com", "/v1/search", "limit", "100")
    
    # Formulários
    print("  Formulários:")
    config.add_rule("myapp.com", "/contact", "source", "automated_test")
    config.add_rule("myapp.com", "/signup", "referrer", "test_campaign")
    
    # Debug
    print("  Debug:")
    config.add_rule("myapp.com", "/app", "debug", "true")
    config.add_rule("myapp.com", "/app", "log_level", "verbose")
    
    listar_regras(config)
    
    print("\n✓ Configuração completa!")
    print("  Execute: python run_proxy_headless.py")
    
    return config


def main():
    """Executa todos os exemplos"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  InteceptProxy - Exemplos de Uso Programático           ║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # Executa exemplos
        exemplo_basico()
        exemplo_multiplas_regras()
        exemplo_gerenciar_regras()
        exemplo_condicional()
        exemplo_validacao()
        exemplo_completo()
        
        print("\n" + "=" * 60)
        print("✅ Todos os exemplos executados com sucesso!")
        print("=" * 60)
        print("\nPróximos passos:")
        print("  1. Revise o arquivo intercept_config.json")
        print("  2. Execute: python run_proxy_headless.py")
        print("  3. Configure seu navegador para usar o proxy")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
