#!/usr/bin/env python3
"""
InteceptProxy - Intercepta requisições HTTP e modifica parâmetros configurados
"""
import json
import os
import threading
import re
from mitmproxy import http
from mitmproxy.tools.main import mitmdump
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# Tkinter import é opcional (pode não estar disponível em ambientes headless)
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class InterceptConfig:
    """Gerencia a configuração do interceptador"""
    
    def __init__(self):
        self.config_file = "intercept_config.json"
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


class InterceptAddon:
    """Addon do mitmproxy para interceptar e modificar requisições"""
    
    def __init__(self, config):
        self.config = config
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Intercepta requisições HTTP"""
        request = flow.request
        
        for rule in self.config.get_rules():
            if not rule.get('enabled', True):
                continue
            
            # Verifica se a URL corresponde ao host e caminho configurados
            host_match = rule['host'] in request.pretty_host
            path_match = request.path.startswith(rule['path'])
            
            if host_match and path_match:
                # Modifica parâmetros na query string (GET)
                if request.query:
                    query_dict = dict(request.query)
                    if rule['param_name'] in query_dict:
                        query_dict[rule['param_name']] = rule['param_value']
                        request.query.clear()
                        for key, value in query_dict.items():
                            request.query[key] = value
                        print(f"[GET] Modificado: {rule['param_name']}={rule['param_value']} em {request.pretty_url}")
                
                # Modifica parâmetros no corpo (POST)
                if request.method == "POST" and request.content:
                    content_type = request.headers.get("content-type", "")
                    
                    if "application/x-www-form-urlencoded" in content_type:
                        # Parse form data
                        body = request.content.decode('utf-8', errors='ignore')
                        params = parse_qs(body, keep_blank_values=True)
                        
                        # Modifica o parâmetro se existir
                        if rule['param_name'] in params:
                            params[rule['param_name']] = [rule['param_value']]
                            # Reconstrói o corpo
                            new_body = urlencode(params, doseq=True)
                            request.content = new_body.encode('utf-8')
                            print(f"[POST] Modificado: {rule['param_name']}={rule['param_value']} em {request.pretty_url}")


class ProxyGUI:
    """Interface gráfica para configurar o proxy interceptador"""
    
    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter não está disponível. A interface gráfica não pode ser criada.")
        
        self.config = InterceptConfig()
        self.proxy_thread = None
        self.proxy_running = False
        
        # Janela principal
        self.root = tk.Tk()
        self.root.title("InteceptProxy - Configurador")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.refresh_rules_list()
    
    def setup_ui(self):
        """Configura a interface gráfica"""
        # Frame superior - Controle do Proxy
        control_frame = ttk.LabelFrame(self.root, text="Controle do Proxy", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(control_frame, text="Status: Parado", foreground="red")
        self.status_label.pack(side="left", padx=5)
        
        self.start_button = ttk.Button(control_frame, text="Iniciar Proxy", command=self.start_proxy)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Parar Proxy", command=self.stop_proxy, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        ttk.Label(control_frame, text="Porta: 8080").pack(side="left", padx=5)
        
        # Frame de configuração de regras
        config_frame = ttk.LabelFrame(self.root, text="Adicionar Regra de Interceptação", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # Host
        ttk.Label(config_frame, text="Host/Domínio:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.host_entry = ttk.Entry(config_frame, width=30)
        self.host_entry.grid(row=0, column=1, padx=5, pady=2)
        self.host_entry.insert(0, "exemplo.com")
        
        # Path
        ttk.Label(config_frame, text="Caminho:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.path_entry = ttk.Entry(config_frame, width=20)
        self.path_entry.grid(row=0, column=3, padx=5, pady=2)
        self.path_entry.insert(0, "/contato")
        
        # Nome do parâmetro
        ttk.Label(config_frame, text="Nome do Parâmetro:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.param_name_entry = ttk.Entry(config_frame, width=30)
        self.param_name_entry.grid(row=1, column=1, padx=5, pady=2)
        self.param_name_entry.insert(0, "Titulo")
        
        # Valor do parâmetro
        ttk.Label(config_frame, text="Novo Valor:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.param_value_entry = ttk.Entry(config_frame, width=20)
        self.param_value_entry.grid(row=1, column=3, padx=5, pady=2)
        self.param_value_entry.insert(0, "teste1")
        
        # Botão adicionar
        ttk.Button(config_frame, text="Adicionar Regra", command=self.add_rule).grid(row=2, column=0, columnspan=4, pady=10)
        
        # Frame de lista de regras
        list_frame = ttk.LabelFrame(self.root, text="Regras Configuradas", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview para mostrar regras
        columns = ('Host', 'Caminho', 'Parâmetro', 'Valor', 'Status')
        self.rules_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=10)
        
        self.rules_tree.heading('#0', text='#')
        self.rules_tree.column('#0', width=40)
        
        for col in columns:
            self.rules_tree.heading(col, text=col)
            self.rules_tree.column(col, width=150)
        
        self.rules_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.rules_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        # Frame de botões para regras
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Remover Regra Selecionada", command=self.remove_rule).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Ativar/Desativar Regra", command=self.toggle_rule).pack(side="left", padx=5)
        
        # Frame de instruções
        info_frame = ttk.LabelFrame(self.root, text="Instruções", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """1. Configure o navegador para usar o proxy: localhost:8080
2. Adicione regras de interceptação com host, caminho, nome do parâmetro e valor
3. Inicie o proxy
4. Navegue normalmente - os parâmetros configurados serão substituídos automaticamente"""
        
        ttk.Label(info_frame, text=info_text, justify="left").pack()
    
    def add_rule(self):
        """Adiciona uma nova regra"""
        host = self.host_entry.get().strip()
        path = self.path_entry.get().strip()
        param_name = self.param_name_entry.get().strip()
        param_value = self.param_value_entry.get().strip()
        
        if not all([host, path, param_name, param_value]):
            messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos!")
            return
        
        if self.config.add_rule(host, path, param_name, param_value):
            messagebox.showinfo("Sucesso", "Regra adicionada com sucesso!")
            self.refresh_rules_list()
        else:
            messagebox.showerror("Erro", "Erro ao salvar regra!")
    
    def remove_rule(self):
        """Remove a regra selecionada"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma regra para remover!")
            return
        
        item = selection[0]
        index = int(self.rules_tree.item(item)['text']) - 1
        
        if self.config.remove_rule(index):
            messagebox.showinfo("Sucesso", "Regra removida com sucesso!")
            self.refresh_rules_list()
        else:
            messagebox.showerror("Erro", "Erro ao remover regra!")
    
    def toggle_rule(self):
        """Ativa/desativa a regra selecionada"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma regra para ativar/desativar!")
            return
        
        item = selection[0]
        index = int(self.rules_tree.item(item)['text']) - 1
        
        if self.config.toggle_rule(index):
            self.refresh_rules_list()
    
    def refresh_rules_list(self):
        """Atualiza a lista de regras na interface"""
        # Limpa a lista
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # Adiciona regras
        for i, rule in enumerate(self.config.get_rules()):
            status = "Ativo" if rule.get('enabled', True) else "Inativo"
            self.rules_tree.insert('', 'end', text=str(i+1), 
                                   values=(rule['host'], rule['path'], 
                                          rule['param_name'], rule['param_value'], status))
    
    def start_proxy(self):
        """Inicia o servidor proxy"""
        if self.proxy_running:
            messagebox.showwarning("Aviso", "Proxy já está em execução!")
            return
        
        def run_proxy():
            try:
                addon = InterceptAddon(self.config)
                mitmdump(['-s', __file__, '--listen-port', '8080', '--set', 'confdir=~/.mitmproxy'])
            except Exception as e:
                print(f"Erro no proxy: {e}")
        
        self.proxy_thread = threading.Thread(target=run_proxy, daemon=True)
        self.proxy_thread.start()
        self.proxy_running = True
        
        self.status_label.config(text="Status: Executando", foreground="green")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        messagebox.showinfo("Proxy Iniciado", 
                           "Proxy iniciado na porta 8080\n\n"
                           "Configure seu navegador para usar:\n"
                           "Host: localhost\n"
                           "Porta: 8080")
    
    def stop_proxy(self):
        """Para o servidor proxy"""
        # Note: mitmproxy não tem um método simples de parar, então apenas atualizamos a interface
        self.proxy_running = False
        self.status_label.config(text="Status: Parado (reinicie o aplicativo)", foreground="orange")
        self.stop_button.config(state="disabled")
        
        messagebox.showinfo("Aviso", 
                           "Para parar completamente o proxy, feche e reabra o aplicativo.")
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()


# Configuração para uso como addon do mitmproxy
addons = []
if __name__ != "__main__":
    # Quando executado como addon do mitmproxy
    config = InterceptConfig()
    addons = [InterceptAddon(config)]


def main():
    """Função principal"""
    if not TKINTER_AVAILABLE:
        print("ERRO: Tkinter não está disponível neste sistema.")
        print("Para instalar tkinter:")
        print("  - Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  - Fedora: sudo dnf install python3-tkinter")
        print("  - macOS: Tkinter já deve estar incluído com Python")
        print("  - Windows: Tkinter já deve estar incluído com Python")
        return 1
    
    app = ProxyGUI()
    app.run()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
