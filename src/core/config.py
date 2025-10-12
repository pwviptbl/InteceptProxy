import json
import os


class InterceptConfig:
    """Gerencia a configuração do interceptador"""

    def __init__(self, config_file="intercept_config.json"):
        self.config_file = config_file
        self.rules = []
        self.paused = False
        self.load_config()

    def load_config(self):
        """Carrega configuração do arquivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rules = data.get('rules', [])
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
                self.rules = []
        else:
            self.rules = []

    def save_config(self):
        """Salva configuração no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'rules': self.rules}, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
            return False

    def add_rule(self, host, path, param_name, param_value):
        """Adiciona uma regra de interceptação"""
        rule = {
            'host': host,
            'path': path,
            'param_name': param_name,
            'param_value': param_value,
            'enabled': True
        }
        self.rules.append(rule)
        return self.save_config()

    def remove_rule(self, index):
        """Remove uma regra de interceptação"""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
            return self.save_config()
        return False

    def get_rules(self):
        """Retorna todas as regras"""
        return self.rules

    def toggle_rule(self, index):
        """Ativa/desativa uma regra"""
        if 0 <= index < len(self.rules):
            self.rules[index]['enabled'] = not self.rules[index]['enabled']
            return self.save_config()
        return False

    def toggle_pause(self):
        """Alterna o estado de pausa do proxy."""
        self.paused = not self.paused
        return self.paused

    def is_paused(self):
        """Verifica se o proxy está pausado."""
        return self.paused
