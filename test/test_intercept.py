import unittest
import os
import sys
from unittest.mock import Mock

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import InterceptConfig
from core.addon import InterceptAddon

class TestIntercept(unittest.TestCase):

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.config_file = "intercept_config.test.json"
        # Garante que o arquivo de teste não existe antes de cada teste
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def tearDown(self):
        """Limpa o ambiente após cada teste."""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_config_management(self):
        """Testa a classe InterceptConfig."""
        config = InterceptConfig(config_file=self.config_file)
        self.assertEqual(len(config.get_rules()), 0, "Config deve começar vazio")

        config.add_rule("exemplo.com", "/contato", "Titulo", "teste1")
        self.assertEqual(len(config.get_rules()), 1, "Deve ter 1 regra")

        # Verifica persistência
        config2 = InterceptConfig(config_file=self.config_file)
        self.assertEqual(len(config2.get_rules()), 1, "Config carregado deve ter 1 regra")

    def test_addon_logic(self):
        """Testa a lógica de modificação do InterceptAddon."""
        config = InterceptConfig(config_file=self.config_file)
        config.add_rule("exemplo.com", "/test", "param1", "modificado")
        addon = InterceptAddon(config)

        # Simula um flow GET
        mock_flow = Mock()
        mock_flow.request = Mock()
        mock_flow.request.pretty_host = "exemplo.com"
        mock_flow.request.path = "/test?param1=original&param2=manter"

        # O query é um objeto especial no mock, então o inicializamos separadamente
        mock_flow.request.query = {"param1": "original", "param2": "manter"}

        addon.request(mock_flow)

        # Verifica se o parâmetro foi modificado
        self.assertEqual(mock_flow.request.query["param1"], "modificado")
        self.assertEqual(mock_flow.request.query["param2"], "manter")

if __name__ == '__main__':
    unittest.main()
