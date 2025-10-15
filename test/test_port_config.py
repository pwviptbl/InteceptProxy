import unittest
import os
import sys

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import InterceptConfig

class TestPortConfig(unittest.TestCase):

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.config_file = "intercept_config_port_test.json"
        # Garante que o arquivo de teste não existe antes de cada teste
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def tearDown(self):
        """Limpa o ambiente após cada teste."""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_default_port(self):
        """Testa se a porta padrão é 8080."""
        config = InterceptConfig(config_file=self.config_file)
        self.assertEqual(config.get_port(), 8080, "Porta padrão deve ser 8080")

    def test_set_valid_port(self):
        """Testa definir uma porta válida."""
        config = InterceptConfig(config_file=self.config_file)
        success, message = config.set_port(9090)
        self.assertTrue(success, "Deve aceitar porta válida")
        self.assertEqual(config.get_port(), 9090, "Porta deve ser 9090")

    def test_set_port_as_string(self):
        """Testa definir porta como string."""
        config = InterceptConfig(config_file=self.config_file)
        success, message = config.set_port("8888")
        self.assertTrue(success, "Deve aceitar porta como string")
        self.assertEqual(config.get_port(), 8888, "Porta deve ser 8888")

    def test_set_invalid_port_negative(self):
        """Testa rejeitar porta negativa."""
        config = InterceptConfig(config_file=self.config_file)
        success, message = config.set_port(-1)
        self.assertFalse(success, "Deve rejeitar porta negativa")
        self.assertEqual(config.get_port(), 8080, "Porta deve permanecer 8080")

    def test_set_invalid_port_zero(self):
        """Testa rejeitar porta zero."""
        config = InterceptConfig(config_file=self.config_file)
        success, message = config.set_port(0)
        self.assertFalse(success, "Deve rejeitar porta zero")
        self.assertEqual(config.get_port(), 8080, "Porta deve permanecer 8080")

    def test_set_invalid_port_too_high(self):
        """Testa rejeitar porta maior que 65535."""
        config = InterceptConfig(config_file=self.config_file)
        success, message = config.set_port(65536)
        self.assertFalse(success, "Deve rejeitar porta > 65535")
        self.assertEqual(config.get_port(), 8080, "Porta deve permanecer 8080")

    def test_set_invalid_port_string(self):
        """Testa rejeitar string não numérica."""
        config = InterceptConfig(config_file=self.config_file)
        success, message = config.set_port("abc")
        self.assertFalse(success, "Deve rejeitar string não numérica")
        self.assertEqual(config.get_port(), 8080, "Porta deve permanecer 8080")

    def test_port_persistence(self):
        """Testa se a porta é persistida no arquivo."""
        config = InterceptConfig(config_file=self.config_file)
        config.set_port(7070)
        
        # Cria uma nova instância e verifica se a porta foi carregada
        config2 = InterceptConfig(config_file=self.config_file)
        self.assertEqual(config2.get_port(), 7070, "Porta deve ser carregada do arquivo")

    def test_port_with_rules(self):
        """Testa que a porta é salva junto com as regras."""
        config = InterceptConfig(config_file=self.config_file)
        config.set_port(5555)
        config.add_rule("exemplo.com", "/test", "param", "value")
        
        # Verifica se ambos foram salvos
        config2 = InterceptConfig(config_file=self.config_file)
        self.assertEqual(config2.get_port(), 5555, "Porta deve ser 5555")
        self.assertEqual(len(config2.get_rules()), 1, "Deve ter 1 regra")

if __name__ == '__main__':
    unittest.main()
