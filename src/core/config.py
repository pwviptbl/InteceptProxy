import json
import os


class InterceptConfig:
    """Gerencia a configuração do interceptador"""

    def __init__(self, config_file="intercept_config.json"):
        self.config_file = config_file
        self.rules = []
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
        """Adiciona uma regra de interceptação com validação."""
        # Validação
        if not all(str(val).strip() for val in [host, path, param_name, param_value]):
            return False, "Todos os campos devem ser preenchidos."

        rule = {
            'host': str(host).strip(),
            'path': str(path).strip(),
            'param_name': str(param_name).strip(),
            'param_value': str(param_value).strip(),
            'enabled': True
        }
        self.rules.append(rule)

        if self.save_config():
            return True, "Regra adicionada com sucesso!"
        else:
            # Em caso de falha ao salvar, remove a regra que foi adicionada
            self.rules.pop()
            return False, "Erro ao salvar a configuração."

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
