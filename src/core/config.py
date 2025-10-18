import json
import os
import queue
import threading


class InterceptConfig:
    """Gerencia a configuração do interceptador"""

    def __init__(self, config_file="intercept_config.json"):
        self.config_file = config_file
        self.rules = []
        self.port = 9507  # Porta padrão
        self.paused = False
        self.intercept_enabled = False
        self.intercept_queue = queue.Queue()
        self.intercept_response_queue = queue.Queue()
        self.intercept_lock = threading.Lock()
        self.load_config()

    def load_config(self):
        """Carrega configuração do arquivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rules = data.get('rules', [])
                    self.port = data.get('port', 9507)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
                self.rules = []
                self.port = 9507
        else:
            self.rules = []
            self.port = 9507

    def save_config(self):
        """Salva configuração no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'rules': self.rules, 'port': self.port}, f, indent=2, ensure_ascii=False)
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

    def toggle_pause(self):
        """Alterna o estado de pausa do proxy."""
        self.paused = not self.paused
        return self.paused

    def is_paused(self):
        """Verifica se o proxy está pausado."""
        return self.paused

    def toggle_intercept(self):
        """Alterna o estado de interceptação manual."""
        self.intercept_enabled = not self.intercept_enabled
        return self.intercept_enabled

    def is_intercept_enabled(self):
        """Verifica se a interceptação manual está ativada."""
        return self.intercept_enabled

    def add_to_intercept_queue(self, flow_data):
        """Adiciona uma requisição à fila de interceptação."""
        self.intercept_queue.put(flow_data)

    def get_from_intercept_queue(self, timeout=0.1):
        """Obtém uma requisição da fila de interceptação."""
        try:
            return self.intercept_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def add_intercept_response(self, response_data):
        """Adiciona uma resposta à fila de respostas."""
        self.intercept_response_queue.put(response_data)

    def get_intercept_response(self, timeout=10):
        """Obtém uma resposta da fila de respostas."""
        try:
            return self.intercept_response_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_intercept_queues(self):
        """Limpa todas as filas de interceptação."""
        while not self.intercept_queue.empty():
            try:
                self.intercept_queue.get_nowait()
            except queue.Empty:
                break
        while not self.intercept_response_queue.empty():
            try:
                self.intercept_response_queue.get_nowait()
            except queue.Empty:
                break

    def get_port(self):
        """Retorna a porta configurada."""
        return self.port

    def set_port(self, port):
        """Define a porta e salva a configuração."""
        if not isinstance(port, int):
            try:
                port = int(port)
            except (ValueError, TypeError):
                return False, "Porta deve ser um número inteiro."
        
        if port < 1 or port > 65535:
            return False, "Porta deve estar entre 1 e 65535."
        
        self.port = port
        if self.save_config():
            return True, f"Porta configurada para {port}"
        else:
            return False, "Erro ao salvar a configuração."

