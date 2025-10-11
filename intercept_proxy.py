#!/usr/bin/env python3
"""
InteceptProxy - Intercepta requisições HTTP e modifica parâmetros configurados
"""
import asyncio
import json
import os
import threading
import re
from datetime import datetime
from mitmproxy import http
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from urllib.parse import parse_qs, urlencode, urlparse

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


class RequestHistory:
    """Gerencia o histórico de requisições"""
    
    def __init__(self):
        self.history = []
        self.max_items = 1000  # Limita o histórico a 1000 itens
    
    def add_request(self, flow: http.HTTPFlow):
        """Adiciona uma requisição ao histórico"""
        request = flow.request
        response = flow.response
        
        # Extrai informações da requisição
        entry = {
            'timestamp': datetime.now(),
            'host': request.pretty_host,
            'method': request.method,
            'url': request.pretty_url,
            'path': request.path,
            'status': response.status_code if response else 0,
            'request_headers': dict(request.headers),
            'request_body': request.content.decode('utf-8', errors='ignore') if request.content else '',
            'response_headers': dict(response.headers) if response else {},
            'response_body': response.content.decode('utf-8', errors='ignore') if response and response.content else '',
        }
        
        self.history.append(entry)
        
        # Limita o tamanho do histórico
        if len(self.history) > self.max_items:
            self.history.pop(0)
    
    def get_history(self):
        """Retorna todo o histórico"""
        return self.history
    
    def clear_history(self):
        """Limpa o histórico"""
        self.history = []


class InterceptAddon:
    """Addon do mitmproxy para interceptar e modificar requisições"""
    
    def __init__(self, config, history=None):
        self.config = config
        self.history = history

    @staticmethod
    def _split_host_and_path(raw_host: str):
        """Normaliza host configurado, aceitando entradas com esquema ou URL completa."""
        if not raw_host:
            return "", ""
        parsed = urlparse(raw_host) if "://" in raw_host else urlparse(f"//{raw_host}")
        host = (parsed.hostname or parsed.netloc or "").lower()
        extra_path = parsed.path if (parsed.scheme or parsed.netloc) else ""
        if not host:
            host = raw_host.lower()
        return host, extra_path

    @staticmethod
    def _host_matches(request_host: str, rule_host: str) -> bool:
        """Verifica se o host da requisição corresponde ao host da regra."""
        if not rule_host:
            return True
        request_host = request_host.lower()
        rule_host = rule_host.lower()
        if request_host == rule_host:
            return True
        return request_host.endswith(f".{rule_host}")
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Intercepta requisições HTTP"""
        request = flow.request
        
        for rule in self.config.get_rules():
            if not rule.get('enabled', True):
                continue
            
            # Verifica se a URL corresponde ao host e caminho configurados
            rule_host, host_path = self._split_host_and_path(rule.get('host', ''))
            normalized_rule_path = rule.get('path', '') or host_path or ""
            if normalized_rule_path and not normalized_rule_path.startswith('/'):
                normalized_rule_path = f"/{normalized_rule_path}"
            host_match = self._host_matches(request.pretty_host, rule_host)
            path_match = True if not normalized_rule_path else request.path.startswith(normalized_rule_path)
            
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
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Intercepta respostas HTTP e armazena no histórico"""
        if self.history is not None:
            self.history.add_request(flow)


class ProxyGUI:
    """Interface gráfica para configurar o proxy interceptador"""
    
    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter não está disponível. A interface gráfica não pode ser criada.")
        
        self.config = InterceptConfig()
        self.history = RequestHistory()
        self.proxy_thread = None
        self.proxy_running = False
        self.proxy_master = None
        self.proxy_loop = None
        
        # Janela principal
        self.root = tk.Tk()
        self.root.title("InteceptProxy - Configurador")
        self.root.geometry("1000x700")
        
        self.setup_ui()
        self.refresh_rules_list()
        
        # Atualiza o histórico periodicamente
        self.update_history_list()
    
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
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tab 1: Configuração de Regras
        self.setup_rules_tab()
        
        # Tab 2: Histórico de Requisições
        self.setup_history_tab()
    
    def setup_rules_tab(self):
        """Configura a aba de regras"""
        rules_tab = ttk.Frame(self.notebook)
        self.notebook.add(rules_tab, text="Regras de Interceptação")
        
        # Frame de configuração de regras
        config_frame = ttk.LabelFrame(rules_tab, text="Adicionar Regra de Interceptação", padding=10)
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
        list_frame = ttk.LabelFrame(rules_tab, text="Regras Configuradas", padding=10)
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
        buttons_frame = ttk.Frame(rules_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Remover Regra Selecionada", command=self.remove_rule).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Ativar/Desativar Regra", command=self.toggle_rule).pack(side="left", padx=5)
        
        # Frame de instruções
        info_frame = ttk.LabelFrame(rules_tab, text="Instruções", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """1. Configure o navegador para usar o proxy: localhost:8080
2. Adicione regras de interceptação com host, caminho, nome do parâmetro e valor
3. Inicie o proxy
4. Navegue normalmente - os parâmetros configurados serão substituídos automaticamente"""
        
        ttk.Label(info_frame, text=info_text, justify="left").pack()
    
    def setup_history_tab(self):
        """Configura a aba de histórico"""
        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text="Histórico de Requisições")
        
        # Frame de filtros
        filter_frame = ttk.LabelFrame(history_tab, text="Filtros", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Filtro por método
        ttk.Label(filter_frame, text="Método:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.method_filter = ttk.Combobox(filter_frame, width=15, state="readonly")
        self.method_filter['values'] = ("Todos", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")
        self.method_filter.current(0)
        self.method_filter.grid(row=0, column=1, padx=5, pady=2)
        self.method_filter.bind('<<ComboboxSelected>>', lambda e: self.apply_history_filter())
        
        # Filtro por domínio (regex)
        ttk.Label(filter_frame, text="Domínio (regex):").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.domain_filter_entry = ttk.Entry(filter_frame, width=40)
        self.domain_filter_entry.grid(row=0, column=3, padx=5, pady=2)
        self.domain_filter_entry.insert(0, "")
        self.domain_filter_entry.bind('<KeyRelease>', lambda e: self.apply_history_filter())
        
        ttk.Label(filter_frame, text="(Use '|' para múltiplos: google.com|facebook.com)").grid(row=1, column=3, sticky="w", padx=5)
        
        # Botões
        ttk.Button(filter_frame, text="Aplicar Filtros", command=self.apply_history_filter).grid(row=0, column=4, padx=5, pady=2)
        ttk.Button(filter_frame, text="Limpar Histórico", command=self.clear_history).grid(row=0, column=5, padx=5, pady=2)
        
        # PanedWindow para dividir lista e detalhes
        paned = ttk.PanedWindow(history_tab, orient=tk.VERTICAL)
        paned.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Frame superior: Lista de requisições
        list_frame = ttk.LabelFrame(paned, text="Requisições Capturadas", padding=5)
        paned.add(list_frame, weight=1)
        
        # Treeview para histórico
        columns = ('Host', 'Data', 'Hora', 'Método', 'Status', 'URL')
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.history_tree.heading('Host', text='Host')
        self.history_tree.heading('Data', text='Data')
        self.history_tree.heading('Hora', text='Hora')
        self.history_tree.heading('Método', text='Método')
        self.history_tree.heading('Status', text='Status')
        self.history_tree.heading('URL', text='URL')
        
        self.history_tree.column('Host', width=150)
        self.history_tree.column('Data', width=80)
        self.history_tree.column('Hora', width=80)
        self.history_tree.column('Método', width=70)
        self.history_tree.column('Status', width=60)
        self.history_tree.column('URL', width=400)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para histórico
        history_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_tree.yview)
        history_scrollbar.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        # Bind do clique para mostrar detalhes
        self.history_tree.bind('<<TreeviewSelect>>', self.show_request_details)
        
        # Frame inferior: Detalhes da requisição
        details_frame = ttk.LabelFrame(paned, text="Detalhes da Requisição", padding=5)
        paned.add(details_frame, weight=1)
        
        # Notebook para abas de Request e Response
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill="both", expand=True)
        
        # Aba de Request
        request_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(request_tab, text="Request")
        
        self.request_text = scrolledtext.ScrolledText(request_tab, wrap=tk.WORD, height=10)
        self.request_text.pack(fill="both", expand=True)
        
        # Aba de Response
        response_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(response_tab, text="Response")
        
        self.response_text = scrolledtext.ScrolledText(response_tab, wrap=tk.WORD, height=10)
        self.response_text.pack(fill="both", expand=True)
    
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def runner():
                try:
                    proxy_options = options.Options(listen_host='127.0.0.1', listen_port=8080)
                    master = DumpMaster(proxy_options, with_termlog=False, with_dumper=False)
                    master.addons.add(InterceptAddon(self.config, self.history))
                    self.proxy_master = master
                    self.proxy_loop = loop
                    await master.run()
                except Exception as err:
                    err_msg = str(err)
                    print(f"Erro no proxy: {err_msg}")
                    self.root.after(0, lambda message=err_msg: messagebox.showerror("Erro", f"Falha ao iniciar o proxy: {message}"))
                finally:
                    try:
                        if self.proxy_master is not None:
                            await self.proxy_master.shutdown()
                    except Exception as shutdown_error:
                        print(f"Erro ao finalizar proxy: {shutdown_error}")
                    finally:
                        self.proxy_master = None
                        self.proxy_loop = None
                        self.proxy_running = False
                        self.root.after(0, self._set_proxy_stopped_state)

            try:
                loop.run_until_complete(runner())
            finally:
                loop.close()
        
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
                           "Porta: 8080\n\n"
                           "Para HTTPS, instale o certificado em http://mitm.it")
    
    def stop_proxy(self):
        """Para o servidor proxy"""
        if not self.proxy_running:
            messagebox.showinfo("Proxy", "Proxy já está parado.")
            return
        
        if self.proxy_master is not None and self.proxy_loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(self.proxy_master.shutdown(), self.proxy_loop)
            except Exception as e:
                print(f"Erro ao parar proxy: {e}")
        else:
            self.proxy_running = False
            self._set_proxy_stopped_state()
        
        messagebox.showinfo("Proxy", "Proxy sendo finalizado.")

    def _set_proxy_stopped_state(self):
        """Atualiza UI quando o proxy para."""
        self.status_label.config(text="Status: Parado", foreground="red")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def update_history_list(self):
        """Atualiza a lista de histórico periodicamente"""
        self.apply_history_filter()
        # Atualiza a cada 1 segundo
        self.root.after(1000, self.update_history_list)
    
    def apply_history_filter(self):
        """Aplica filtros ao histórico"""
        # Limpa a lista
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Obtém valores dos filtros
        method_filter = self.method_filter.get()
        domain_pattern = self.domain_filter_entry.get().strip()
        
        # Compila o regex do domínio se fornecido
        domain_regex = None
        if domain_pattern:
            try:
                domain_regex = re.compile(domain_pattern, re.IGNORECASE)
            except re.error:
                # Regex inválido, ignora o filtro
                domain_regex = None
        
        # Filtra e adiciona requisições
        for entry in self.history.get_history():
            # Aplica filtro de método
            if method_filter != "Todos" and entry['method'] != method_filter:
                continue
            
            # Aplica filtro de domínio
            if domain_regex and not domain_regex.search(entry['host']):
                continue
            
            # Formata data e hora
            date_str = entry['timestamp'].strftime('%d/%m/%Y')
            time_str = entry['timestamp'].strftime('%H:%M:%S')
            
            # Adiciona à lista
            self.history_tree.insert('', 'end', 
                                    values=(entry['host'], date_str, time_str, 
                                           entry['method'], entry['status'], entry['url']),
                                    tags=(entry,))
    
    def show_request_details(self, event):
        """Mostra detalhes da requisição selecionada"""
        selection = self.history_tree.selection()
        if not selection:
            return
        
        # Obtém o item selecionado
        item = selection[0]
        values = self.history_tree.item(item)['values']
        
        # Procura a entrada correspondente no histórico
        selected_entry = None
        for entry in self.history.get_history():
            if (entry['host'] == values[0] and 
                entry['timestamp'].strftime('%d/%m/%Y') == values[1] and
                entry['timestamp'].strftime('%H:%M:%S') == values[2]):
                selected_entry = entry
                break
        
        if not selected_entry:
            return
        
        # Limpa os textos
        self.request_text.delete('1.0', tk.END)
        self.response_text.delete('1.0', tk.END)
        
        # Formata e exibe a requisição
        request_info = f"URL: {selected_entry['url']}\n"
        request_info += f"Método: {selected_entry['method']}\n"
        request_info += f"Host: {selected_entry['host']}\n"
        request_info += f"Path: {selected_entry['path']}\n\n"
        request_info += "Headers:\n"
        for key, value in selected_entry['request_headers'].items():
            request_info += f"  {key}: {value}\n"
        request_info += f"\nBody:\n{selected_entry['request_body']}"
        
        self.request_text.insert('1.0', request_info)
        
        # Formata e exibe a resposta
        response_info = f"Status: {selected_entry['status']}\n\n"
        response_info += "Headers:\n"
        for key, value in selected_entry['response_headers'].items():
            response_info += f"  {key}: {value}\n"
        response_info += f"\nBody:\n{selected_entry['response_body']}"
        
        self.response_text.insert('1.0', response_info)
    
    def clear_history(self):
        """Limpa o histórico de requisições"""
        if messagebox.askyesno("Confirmar", "Deseja realmente limpar todo o histórico?"):
            self.history.clear_history()
            self.apply_history_filter()
            messagebox.showinfo("Sucesso", "Histórico limpo com sucesso!")
    
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
