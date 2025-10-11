#!/usr/bin/env python3
"""
Script de demonstração para executar o proxy sem a interface gráfica.
Útil para testes e ambientes sem GUI.
"""
import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from intercept_proxy import InterceptAddon, InterceptConfig
from mitmproxy.tools.main import mitmdump


def main():
    """Executa o proxy em modo headless"""
    print("=" * 60)
    print("InteceptProxy - Modo Headless")
    print("=" * 60)
    
    # Carrega configuração
    config = InterceptConfig()
    rules = config.get_rules()
    
    if not rules:
        print("\n⚠️  Nenhuma regra configurada!")
        print("\nPara adicionar regras:")
        print("1. Copie intercept_config.example.json para intercept_config.json")
        print("2. Edite intercept_config.json com suas regras")
        print("3. Execute este script novamente")
        return 1
    
    print(f"\n📋 Regras configuradas: {len(rules)}")
    print("-" * 60)
    for i, rule in enumerate(rules, 1):
        status = "✓ Ativo" if rule.get('enabled', True) else "✗ Inativo"
        print(f"{i}. [{status}] {rule['host']}{rule['path']}")
        print(f"   → {rule['param_name']} = {rule['param_value']}")
    
    print("\n" + "=" * 60)
    print("🚀 Iniciando proxy na porta 8080...")
    print("=" * 60)
    print("\nConfigure seu navegador para usar:")
    print("  Host: localhost")
    print("  Porta: 8080")
    print("\nPressione Ctrl+C para parar o proxy")
    print("=" * 60 + "\n")
    
    try:
        # Cria addon e executa mitmdump
        addon = InterceptAddon(config)
        mitmdump([
            '--listen-port', '8080',
            '--set', 'confdir=~/.mitmproxy',
            '--set', 'flow_detail=1'
        ])
    except KeyboardInterrupt:
        print("\n\n✓ Proxy encerrado pelo usuário")
        return 0
    except Exception as e:
        print(f"\n❌ Erro ao executar proxy: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
