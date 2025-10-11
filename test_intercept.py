#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do InterceptConfig e InterceptAddon.
"""
import os
import sys
import json
from unittest.mock import Mock

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from core.config import InterceptConfig
from core.addon import InterceptAddon


def test_config_management():
    """Testa a classe InterceptConfig"""
    config_file = "intercept_config.test.json"
    
    # Garante que o arquivo de teste não existe
    if os.path.exists(config_file):
        os.remove(config_file)
    
    print("Testando InterceptConfig...")
    
    # Cria instância com arquivo de teste
    config = InterceptConfig(config_file=config_file)

    assert len(config.get_rules()) == 0, "Config deve começar vazio"
    print("✓ Config inicializado corretamente")
    
    # Adiciona uma regra
    config.add_rule("exemplo.com", "/contato", "Titulo", "teste1")
    assert len(config.get_rules()) == 1, "Deve ter 1 regra"
    print("✓ Regra adicionada com sucesso")
    
    # Verifica persistência
    config2 = InterceptConfig(config_file=config_file)
    assert len(config2.get_rules()) == 1, "Config carregado deve ter 1 regra"
    print("✓ Persistência funcionando")
    
    # Limpa
    os.remove(config_file)
    print("\n✅ Testes de InterceptConfig passaram!")
    return True


def test_addon_logic():
    """Testa a lógica de modificação do InterceptAddon"""
    print("\nTestando InterceptAddon...")

    # Usa um arquivo de config temporário para não interferir com outros testes
    config = InterceptConfig(config_file="intercept_config.addon_test.json")
    config.add_rule("exemplo.com", "/test", "param1", "modificado")
    addon = InterceptAddon(config)

    # Simula um flow GET
    mock_flow = Mock()
    mock_flow.request = Mock()
    mock_flow.request.pretty_host = "exemplo.com"
    mock_flow.request.path = "/test?param1=original&param2=manter"
    mock_flow.request.query = {"param1": "original", "param2": "manter"}

    addon.request(mock_flow)

    # Verifica se o parâmetro foi modificado
    assert mock_flow.request.query["param1"] == "modificado"
    assert mock_flow.request.query["param2"] == "manter"
    print("✓ Modificação de parâmetro GET funcionando")

    # Limpa
    if os.path.exists("intercept_config.addon_test.json"):
        os.remove("intercept_config.addon_test.json")

    print("\n✅ Testes de InterceptAddon passaram!")
    return True


if __name__ == "__main__":
    try:
        if not test_config_management():
            sys.exit(1)

        if not test_addon_logic():
            sys.exit(1)
            
        print("\n🎉 Todos os testes passaram com sucesso!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
