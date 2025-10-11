#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do InterceptConfig
"""
import os
import sys
import json

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

def test_config():
    """Testa a classe InterceptConfig"""
    from intercept_proxy import InterceptConfig
    
    # Remove arquivo de config se existir
    if os.path.exists("intercept_config.json"):
        os.remove("intercept_config.json")
    
    print("Testando InterceptConfig...")
    
    # Cria instância
    config = InterceptConfig()
    assert len(config.get_rules()) == 0, "Config deve começar vazio"
    print("✓ Config inicializado corretamente")
    
    # Adiciona uma regra
    success = config.add_rule("exemplo.com", "/contato", "Titulo", "teste1")
    assert success, "Deve adicionar regra com sucesso"
    assert len(config.get_rules()) == 1, "Deve ter 1 regra"
    print("✓ Regra adicionada com sucesso")
    
    # Verifica conteúdo da regra
    rule = config.get_rules()[0]
    assert rule['host'] == "exemplo.com", "Host deve ser exemplo.com"
    assert rule['path'] == "/contato", "Path deve ser /contato"
    assert rule['param_name'] == "Titulo", "Param deve ser Titulo"
    assert rule['param_value'] == "teste1", "Value deve ser teste1"
    assert rule['enabled'] == True, "Regra deve estar habilitada"
    print("✓ Conteúdo da regra está correto")
    
    # Adiciona mais regras
    config.add_rule("test.com", "/api", "id", "123")
    config.add_rule("site.com", "/page", "name", "valor")
    assert len(config.get_rules()) == 3, "Deve ter 3 regras"
    print("✓ Múltiplas regras adicionadas")
    
    # Testa toggle
    config.toggle_rule(0)
    assert config.get_rules()[0]['enabled'] == False, "Regra 0 deve estar desabilitada"
    print("✓ Toggle de regra funcionando")
    
    config.toggle_rule(0)
    assert config.get_rules()[0]['enabled'] == True, "Regra 0 deve estar habilitada novamente"
    print("✓ Toggle de regra funcionando (segunda vez)")
    
    # Testa remoção
    config.remove_rule(1)
    assert len(config.get_rules()) == 2, "Deve ter 2 regras após remoção"
    print("✓ Remoção de regra funcionando")
    
    # Verifica persistência
    config2 = InterceptConfig()
    assert len(config2.get_rules()) == 2, "Config carregado deve ter 2 regras"
    print("✓ Persistência funcionando")
    
    # Verifica arquivo JSON
    with open("intercept_config.json", 'r') as f:
        data = json.load(f)
        assert 'rules' in data, "Arquivo deve conter 'rules'"
        assert len(data['rules']) == 2, "Arquivo deve ter 2 regras"
    print("✓ Arquivo JSON está correto")
    
    # Limpa
    os.remove("intercept_config.json")
    print("\n✅ Todos os testes passaram!")
    return True


def test_imports():
    """Testa se todas as importações estão funcionando"""
    print("Testando imports...")
    try:
        from intercept_proxy import InterceptConfig, InterceptAddon
        print("✓ Imports funcionando (GUI não disponível em ambiente headless)")
        return True
    except Exception as e:
        print(f"✗ Erro nos imports: {e}")
        return False


if __name__ == "__main__":
    try:
        if not test_imports():
            sys.exit(1)
        
        if not test_config():
            sys.exit(1)
            
        print("\n🎉 Todos os testes passaram com sucesso!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
