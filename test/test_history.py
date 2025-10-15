import unittest
import os
import sys
from unittest.mock import Mock

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.history import RequestHistory
from core.config import InterceptConfig
from core.addon import InterceptAddon

class TestHistory(unittest.TestCase):

    def setUp(self):
        """Configura um mock de flow para ser usado nos testes."""
        self.mock_flow = Mock()
        self.mock_flow.request = Mock()
        self.mock_flow.request.pretty_host = "exemplo.com"
        self.mock_flow.request.method = "GET"
        self.mock_flow.request.pretty_url = "http://exemplo.com/test"
        self.mock_flow.request.path = "/test"
        self.mock_flow.request.headers = {"User-Agent": "Test"}
        self.mock_flow.request.content = b"test body"
        self.mock_flow.request.query = {}

        self.mock_flow.response = Mock()
        self.mock_flow.response.status_code = 200
        self.mock_flow.response.headers = {"Content-Type": "text/html"}
        self.mock_flow.response.content = b"response body"

    def test_request_history(self):
        """Testa a classe RequestHistory."""
        history = RequestHistory()
        self.assertEqual(len(history.get_history()), 0, "História deve começar vazia")

        # Adiciona requisição
        history.add_request(self.mock_flow)
        self.assertEqual(len(history.get_history()), 1, "Deve ter 1 entrada")

        # Verifica conteúdo da entrada
        entry = history.get_history()[0]
        self.assertEqual(entry['host'], "exemplo.com")
        self.assertEqual(entry['method'], "GET")
        self.assertEqual(entry['status'], 200)
        self.assertEqual(entry['url'], "http://exemplo.com/test")

        # Testa limpeza
        history.clear_history()
        self.assertEqual(len(history.get_history()), 0, "História deve estar vazia após limpeza")

    def test_history_size_limit(self):
        """Testa o limite de tamanho do histórico."""
        history = RequestHistory()
        history.max_items = 5
        for i in range(10):
            history.add_request(self.mock_flow)
        self.assertEqual(len(history.get_history()), 5, "Histórico deve ser limitado a 5 itens")

    def test_intercept_addon_with_history(self):
        """Testa o InterceptAddon com histórico."""
        config = InterceptConfig()
        history = RequestHistory()
        addon = InterceptAddon(config, history)

        # Processa requisição e resposta
        addon.request(self.mock_flow)
        addon.response(self.mock_flow)

        self.assertEqual(len(history.get_history()), 1, "Deve ter 1 entrada no histórico")

    def test_get_entry_by_id(self):
        """Testa a busca de uma entrada pelo ID."""
        history = RequestHistory()
        history.add_request(self.mock_flow) # ID 1
        history.add_request(self.mock_flow) # ID 2

        entry = history.get_entry_by_id(2)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['id'], 2)

        entry_none = history.get_entry_by_id(99)
        self.assertIsNone(entry_none)

    def test_add_vulnerabilities_to_entry(self):
        """Testa a adição de vulnerabilidades a uma entrada existente."""
        history = RequestHistory()
        history.add_request(self.mock_flow) # ID 1

        vuln1 = {'type': 'SQLi', 'severity': 'High'}
        vuln2 = {'type': 'XSS', 'severity': 'Medium'}

        success = history.add_vulnerabilities_to_entry(1, [vuln1])
        self.assertTrue(success)

        entry = history.get_entry_by_id(1)
        self.assertEqual(len(entry['vulnerabilities']), 1)
        self.assertEqual(entry['vulnerabilities'][0]['type'], 'SQLi')

        # Adiciona outra vulnerabilidade e verifica se acumula
        success_again = history.add_vulnerabilities_to_entry(1, [vuln2])
        self.assertTrue(success_again)
        entry_updated = history.get_entry_by_id(1)
        self.assertEqual(len(entry_updated['vulnerabilities']), 2)

        # Testa adicionar a mesma vulnerabilidade (não deve duplicar)
        history.add_vulnerabilities_to_entry(1, [vuln1])
        entry_final = history.get_entry_by_id(1)
        self.assertEqual(len(entry_final['vulnerabilities']), 2)


if __name__ == '__main__':
    unittest.main()
