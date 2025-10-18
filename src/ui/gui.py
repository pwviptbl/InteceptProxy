import asyncio
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from ttkthemes import ThemedTk

from src.core import decoder
from src.core.active_scanner import ActiveScanner
from src.core.addon import InterceptAddon
from src.core.config import InterceptConfig
from src.core.cookie_manager import CookieManager
from src.core.history import RequestHistory
from src.core.logger_config import log
from src.core.spider import Spider
from src.core.websocket_history import WebSocketHistory
from src.core.browser_manager import BrowserManager
from .tooltip import Tooltip


class ProxyGUI:
    """Interface gráfica para configurar o proxy interceptador"""

    def __init__(self):
        self.config = InterceptConfig()
        self.history = RequestHistory()
        self.cookie_manager = CookieManager()
        self.cookie_manager.set_ui_callback(self._refresh_cookie_trees)
        self.spider = Spider()  # Inicializa o Spider
        self.websocket_history = WebSocketHistory()  # Inicializa histórico WebSocket
        self.active_scanner = ActiveScanner()  # Inicializa o Scanner Ativo
        self.browser_manager = BrowserManager(
            proxy_port=self.config.get_port(),
            on_install_start=self.on_browser_install_start,
            on_install_finish=self.on_browser_install_finish
        )
        self.proxy_thread = None
        self.proxy_running = False
        self.proxy_master = None
        self.proxy_loop = None
        self.history_map = {}
        self.last_history_id = 0
        self.repeater_request_data = None
        self.current_intercept_request = None
        self.intercept_response_text = None
        
        # Comparator state
        self.comparator_request_1 = None
        self.comparator_request_2 = None
        
        # WebSocket state
        self.ws_connections_map = {}
        self.selected_ws_connection = None
        
        # Lazy loading state - track which tabs have been initialized
        self.initialized_tabs = set()
        self.tab_setup_methods = {}

        # Janela principal com tema
        self.root = ThemedTk(theme="arc")
        self.root.title("InteceptProxy - Configurador")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()
        self.refresh_rules_list()

        # Atualiza o histórico periodicamente
        self.update_history_list()
        
        # Atualiza a fila de interceptação periodicamente
        self.check_intercept_queue()
        
        # Atualiza estatísticas do Spider periodicamente
        self.update_spider_stats()
        
        # Atualiza lista de WebSocket periodicamente
        self.update_websocket_list()

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

        self.pause_button = ttk.Button(control_frame, text="Pausar", command=self.toggle_pause_proxy, state="disabled")
        self.pause_button.pack(side="left", padx=5)

        # Porta configurável
        ttk.Label(control_frame, text="Porta:").pack(side="left", padx=(20, 2))
        self.port_entry = ttk.Entry(control_frame, width=6)
        self.port_entry.insert(0, str(self.config.get_port()))
        self.port_entry.pack(side="left", padx=2)
        
        self.port_save_button = ttk.Button(control_frame, text="Salvar Porta", command=self.save_port)
        self.port_save_button.pack(side="left", padx=5)

        # Botão para abrir o navegador
        self.browser_button = ttk.Button(control_frame, text="Abrir Navegador", command=self.launch_browser, state="disabled")
        self.browser_button.pack(side="left", padx=(20, 5))
        Tooltip(self.browser_button, "Abre um navegador pré-configurado para usar o proxy.")

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Initialize only the first tab (Rules) immediately
        # Tab 1: Configuração de Regras (always loaded first)
        self.setup_rules_tab()

        # Create placeholder frames for other tabs and register their setup methods
        self._register_lazy_tab("Intercept Manual", self.setup_intercept_tab, 1)
        self._register_lazy_tab("Histórico de Requisições", self.setup_history_tab, 2)
        self._register_lazy_tab("Repetição", self.setup_repeater_tab, 3)
        self._register_lazy_tab("Sender", self.setup_sender_tab, 4)
        self._register_lazy_tab("Decoder", self.setup_decoder_tab, 5)
        self._register_lazy_tab("Comparator", self.setup_comparator_tab, 6)
        self._register_lazy_tab("Cookie Jar", self.setup_cookie_jar_tab, 7)
        self._register_lazy_tab("Scanner", self.setup_scanner_tab, 8)
        self._register_lazy_tab("🕷️ Spider/Crawler", self.setup_spider_tab, 9)
        self._register_lazy_tab("WebSocket", self.setup_websocket_tab, 10)

        # Bind tab change event to load tabs on demand
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _register_lazy_tab(self, tab_name, setup_method, tab_index):
        """Register a tab for lazy loading"""
        # Create a placeholder frame
        placeholder_frame = ttk.Frame(self.notebook)
        self.notebook.add(placeholder_frame, text=tab_name)
        
        # Store the setup method for this tab
        self.tab_setup_methods[tab_index] = (setup_method, placeholder_frame)
    
    def _on_tab_changed(self, event):
        """Called when user switches tabs - loads tab content on demand"""
        current_tab = self.notebook.index(self.notebook.select())
        
        # Check if this tab needs to be initialized
        if current_tab not in self.initialized_tabs and current_tab in self.tab_setup_methods:
            setup_method, placeholder_frame = self.tab_setup_methods[current_tab]
            
            # Remove the placeholder
            self.notebook.forget(current_tab)
            
            # Initialize the real tab content
            setup_method()
            
            # Mark as initialized
            self.initialized_tabs.add(current_tab)
            
            log.info(f"Lazy loaded tab at index {current_tab}")

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
        add_button = ttk.Button(config_frame, text="Adicionar Regra", command=self.add_rule)
        add_button.grid(row=2, column=0, columnspan=4, pady=10)

        # Adiciona tooltips
        Tooltip(self.host_entry, "Domínio a ser interceptado (ex: exemplo.com)")
        Tooltip(self.path_entry, "Caminho da URL a ser interceptado (ex: /login)")
        Tooltip(self.param_name_entry, "Nome do parâmetro na URL a ser modificado.")
        Tooltip(self.param_value_entry, "Novo valor que será atribuído ao parâmetro.")
        Tooltip(add_button, "Clique para salvar esta regra na lista.")

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

        remove_button = ttk.Button(buttons_frame, text="Remover Regra Selecionada", command=self.remove_rule)
        remove_button.pack(side="left", padx=5)
        Tooltip(remove_button, "Remove a regra atualmente selecionada na lista.")

        toggle_button = ttk.Button(buttons_frame, text="Ativar/Desativar Regra", command=self.toggle_rule)
        toggle_button.pack(side="left", padx=5)
        Tooltip(toggle_button, "Ativa ou desativa a regra selecionada.")

        duplicate_button = ttk.Button(buttons_frame, text="Duplicar Regra", command=self.duplicate_rule)
        duplicate_button.pack(side="left", padx=5)
        Tooltip(duplicate_button, "Cria uma cópia da regra selecionada.")

        # Frame de instruções
        info_frame = ttk.LabelFrame(rules_tab, text="Instruções", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)

        info_text = """1. Configure a porta desejada (padrão: 9507) e clique em "Salvar Porta"
2. Configure o navegador para usar o proxy: localhost:<porta configurada>
3. Adicione regras de interceptação com host, caminho, nome do parâmetro e valor
4. Inicie o proxy
5. Navegue normalmente - os parâmetros configurados serão substituídos automaticamente"""

        ttk.Label(info_frame, text=info_text, justify="left").pack()

    def setup_intercept_tab(self):
        """Configura a aba de interceptação manual"""
        intercept_tab = ttk.Frame(self.notebook)
        self.notebook.add(intercept_tab, text="Intercept Manual")

        # Frame de controle superior
        control_frame = ttk.LabelFrame(intercept_tab, text="Controle de Interceptação", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        # Status da interceptação
        self.intercept_status_label = ttk.Label(control_frame, text="Intercept: OFF", foreground="red", font=("Arial", 12, "bold"))
        self.intercept_status_label.pack(side="left", padx=10)

        # Botão ON/OFF
        self.intercept_toggle_button = ttk.Button(
            control_frame, 
            text="Intercept is OFF", 
            command=self.toggle_intercept,
            width=20
        )
        self.intercept_toggle_button.pack(side="left", padx=10)

        # Frame da requisição interceptada
        request_frame = ttk.LabelFrame(intercept_tab, text="Requisição Interceptada", padding=10)
        request_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame de informações básicas
        info_frame = ttk.Frame(request_frame)
        info_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(info_frame, text="Método:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.intercept_method_label = ttk.Label(info_frame, text="-")
        self.intercept_method_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(info_frame, text="URL:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.intercept_url_label = ttk.Label(info_frame, text="-", wraplength=700)
        self.intercept_url_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(info_frame, text="Host:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.intercept_host_label = ttk.Label(info_frame, text="-")
        self.intercept_host_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # Frame de headers (editável)
        headers_frame = ttk.LabelFrame(request_frame, text="Headers", padding=5)
        headers_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.intercept_headers_text = scrolledtext.ScrolledText(headers_frame, height=8, wrap=tk.WORD)
        self.intercept_headers_text.pack(fill="both", expand=True)

        # Frame de body (editável)
        body_frame = ttk.LabelFrame(request_frame, text="Body", padding=5)
        body_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.intercept_body_text = scrolledtext.ScrolledText(body_frame, height=8, wrap=tk.WORD)
        self.intercept_body_text.pack(fill="both", expand=True)

        # Frame de botões de ação
        action_frame = ttk.Frame(intercept_tab)
        action_frame.pack(fill="x", padx=10, pady=10)

        # Botão Forward
        self.forward_button = ttk.Button(
            action_frame,
            text="Forward",
            command=self.forward_request,
            state="disabled",
            width=15
        )
        self.forward_button.pack(side="left", padx=10)
        Tooltip(self.forward_button, "Envia a requisição (com modificações se houver)")

        # Botão Drop
        self.drop_button = ttk.Button(
            action_frame,
            text="Drop",
            command=self.drop_request,
            state="disabled",
            width=15
        )
        self.drop_button.pack(side="left", padx=10)
        Tooltip(self.drop_button, "Cancela a requisição")

        # Label de informação
        info_label = ttk.Label(
            action_frame,
            text="Aguardando requisição...",
            foreground="gray"
        )
        info_label.pack(side="left", padx=20)

        # Frame de instruções
        instructions_frame = ttk.LabelFrame(intercept_tab, text="Instruções", padding=10)
        instructions_frame.pack(fill="x", padx=10, pady=5)

        instructions_text = """1. Clique em "Intercept is OFF" para ativar a interceptação manual
2. Quando uma requisição for interceptada, ela aparecerá aqui
3. Você pode editar os headers e o body da requisição
4. Clique em "Forward" para enviar a requisição (com modificações)
5. Clique em "Drop" para cancelar a requisição
6. Clique em "Intercept is ON" para desativar a interceptação"""

        ttk.Label(instructions_frame, text=instructions_text, justify="left").pack()

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

        ttk.Label(filter_frame, text="(Use '|' para múltiplos: google.com|facebook.com)").grid(row=1, column=3,
                                                                                               sticky="w", padx=5)

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

        # Bind do clique para mostrar detalhes e menu de contexto
        self.history_tree.bind('<<TreeviewSelect>>', self.show_request_details)
        self.history_tree.bind('<Button-3>', self.show_context_menu)

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
        """Adiciona uma nova regra usando a lógica de validação centralizada."""
        host = self.host_entry.get()
        path = self.path_entry.get()
        param_name = self.param_name_entry.get()
        param_value = self.param_value_entry.get()

        success, message = self.config.add_rule(host, path, param_name, param_value)

        if success:
            messagebox.showinfo("Sucesso", message)
            self.refresh_rules_list()
        else:
            messagebox.showwarning("Erro de Validação", message)

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

    def duplicate_rule(self):
        """Duplica a regra selecionada."""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma regra para duplicar!")
            return

        item = selection[0]
        index = int(self.rules_tree.item(item)['text']) - 1

        rule_to_duplicate = self.config.get_rules()[index]

        host = rule_to_duplicate['host']
        path = rule_to_duplicate['path']
        param_name = rule_to_duplicate['param_name']
        param_value = rule_to_duplicate['param_value']

        if self.config.add_rule(host, path, param_name, param_value):
            messagebox.showinfo("Sucesso", "Regra duplicada com sucesso!")
            self.refresh_rules_list()
        else:
            messagebox.showerror("Erro", "Erro ao duplicar a regra!")

    def refresh_rules_list(self):
        """Atualiza a lista de regras na interface"""
        # Limpa a lista
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        # Adiciona regras
        for i, rule in enumerate(self.config.get_rules()):
            status = "Ativo" if rule.get('enabled', True) else "Inativo"
            self.rules_tree.insert('', 'end', text=str(i + 1),
                                   values=(rule['host'], rule['path'],
                                           rule['param_name'], rule['param_value'], status))

    def start_proxy(self):
        """Inicia o servidor proxy"""
        if self.proxy_running:
            messagebox.showwarning("Aviso", "Proxy já está em execução!")
            return

        log.info("Proxy (GUI) iniciando...")
        def run_proxy():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def runner():
                try:
                    port = self.config.get_port()
                    proxy_options = options.Options(listen_host='127.0.0.1', listen_port=port)
                    master = DumpMaster(proxy_options, with_termlog=False, with_dumper=False)
                    master.addons.add(InterceptAddon(self.config, self.history, self.cookie_manager, self.spider, self.websocket_history))
                    self.proxy_master = master
                    self.proxy_loop = loop
                    await master.run()
                except Exception as err:
                    err_msg = str(err)
                    log.error(f"Falha ao iniciar o proxy (GUI): {err_msg}", exc_info=True)
                    self.root.after(0, lambda message=err_msg: messagebox.showerror("Erro",
                                                                                    f"Falha ao iniciar o proxy: {message}"))
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
        self.pause_button.config(state="normal")
        self.browser_button.config(state="normal")

        port = self.config.get_port()
        messagebox.showinfo("Proxy Iniciado",
                            f"Proxy iniciado na porta {port}\n\n"
                            "Configure seu navegador para usar:\n"
                            f"Host: localhost\n"
                            f"Porta: {port}\n\n"
                            "Para HTTPS, instale o certificado em http://mitm.it")

    def stop_proxy(self):
        """Para o servidor proxy"""
        if not self.proxy_running:
            messagebox.showinfo("Proxy", "Proxy já está parado.")
            return

        log.info("Proxy (GUI) finalizando...")
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
        self.pause_button.config(state="disabled", text="Pausar")
        self.browser_button.config(state="disabled")

    def launch_browser(self):
        """Lança o navegador usando o BrowserManager."""
        if not self.proxy_running:
            messagebox.showwarning("Aviso", "O proxy precisa estar em execução para abrir o navegador.")
            return

        log.info("Solicitando abertura do navegador...")
        self.browser_manager.launch_browser()

    def toggle_pause_proxy(self):
        """Alterna o estado de pausa do proxy e atualiza a UI."""
        if not self.proxy_running:
            return

        is_paused = self.config.toggle_pause()

        if is_paused:
            self.status_label.config(text="Status: Pausado", foreground="orange")
            self.pause_button.config(text="Continuar")
            log.info("Proxy pausado.")
        else:
            self.status_label.config(text="Status: Executando", foreground="green")
            self.pause_button.config(text="Pausar")
            log.info("Proxy retomado.")

    def save_port(self):
        """Salva a porta configurada."""
        if self.proxy_running:
            messagebox.showwarning("Aviso", "Pare o proxy antes de alterar a porta.")
            return
        
        port_str = self.port_entry.get().strip()
        success, message = self.config.set_port(port_str)
        
        if success:
            messagebox.showinfo("Sucesso", message)
            log.info(f"Porta alterada para {self.config.get_port()}")
        else:
            messagebox.showerror("Erro", message)
            # Restaura o valor anterior
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, str(self.config.get_port()))

    def update_history_list(self):
        """Atualiza a lista de histórico adicionando apenas novas entradas."""
        # Only update if the history tab is initialized
        if 2 not in self.initialized_tabs:
            self.root.after(1000, self.update_history_list)
            return
        
        # Run the update in a background thread to avoid blocking the UI
        def update_in_background():
            try:
                new_entries = self.history.get_new_entries(self.last_history_id)
                if new_entries:
                    # Schedule UI update on main thread
                    self.root.after(0, lambda: self._add_new_history_entries(new_entries))
            except Exception as e:
                log.error(f"Error updating history list: {e}")
        
        thread = threading.Thread(target=update_in_background, daemon=True)
        thread.start()
        
        self.root.after(1000, self.update_history_list)

    def _add_new_history_entries(self, entries):
        """Adiciona novas entradas de histórico à tabela e atualiza o ID mais recente."""
        # Only add entries if history tab is initialized
        if not hasattr(self, 'history_tree'):
            return
        
        for entry in entries:
            # Aplica os filtros atuais antes de adicionar
            method_filter = self.method_filter.get()
            if method_filter != "Todos" and entry['method'] != method_filter:
                continue

            domain_pattern = self.domain_filter_entry.get().strip()
            if domain_pattern:
                try:
                    domain_regex = re.compile(domain_pattern, re.IGNORECASE)
                    if not domain_regex.search(entry['host']):
                        continue
                except re.error:
                    pass  # Ignora regex inválido

            date_str = entry['timestamp'].strftime('%d/%m/%Y')
            time_str = entry['timestamp'].strftime('%H:%M:%S')

            item_id = self.history_tree.insert('', 'end', values=(
                entry['host'], date_str, time_str, entry['method'], entry['status'], entry['url']
            ))
            self.history_map[item_id] = entry
            self.last_history_id = entry['id']
        
        # Atualiza também a lista de vulnerabilidades em background
        if entries:
            threading.Thread(target=self._update_scanner_list, daemon=True).start()

    def apply_history_filter(self):
        """Limpa a tabela e reaplica os filtros, carregando todo o histórico relevante."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.history_map.clear()
        self.last_history_id = 0  # Reseta o contador ao aplicar filtros

        # Re-adiciona todas as entradas que passam pelos filtros
        all_entries = self.history.get_history()
        self._add_new_history_entries(all_entries)

    def show_request_details(self, event):
        """Mostra detalhes da requisição selecionada."""
        selection = self.history_tree.selection()
        if not selection:
            return

        # Obtém o item selecionado
        item_id = selection[0]
        selected_entry = self.history_map.get(item_id)

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

    def setup_repeater_tab(self):
        """Configura a aba de Repetição manual."""
        repeater_tab = ttk.Frame(self.notebook)
        self.notebook.add(repeater_tab, text="Repetição")

        # Frame superior para configuração
        config_frame = ttk.LabelFrame(repeater_tab, text="Configuração do Reenvio", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Parâmetro a Substituir
        ttk.Label(config_frame, text="Parâmetro a Substituir:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.repeater_param_entry = ttk.Entry(config_frame, width=30)
        self.repeater_param_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        Tooltip(self.repeater_param_entry, "Nome do parâmetro a ser substituído (na URL ou no Body).")

        # Novo Valor
        ttk.Label(config_frame, text="Novo Valor:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.repeater_manual_value_entry = ttk.Entry(config_frame, width=30)
        self.repeater_manual_value_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        Tooltip(self.repeater_manual_value_entry, "Valor que substituirá o original.")

        # Botão de Iniciar
        start_repeater_button = ttk.Button(config_frame, text="Reenviar Requisição", command=self.start_repeater)
        start_repeater_button.grid(row=1, column=0, columnspan=4, pady=15)
        Tooltip(start_repeater_button, "Inicia o processo de reenvio manual.")

        # PanedWindow para dividir Request e Response
        paned = ttk.PanedWindow(repeater_tab, orient=tk.VERTICAL)
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para Request
        request_frame = ttk.LabelFrame(paned, text="Request Original", padding=5)
        paned.add(request_frame, weight=1)
        self.repeater_request_text = scrolledtext.ScrolledText(request_frame, wrap=tk.WORD, height=10)
        self.repeater_request_text.pack(fill="both", expand=True)

        # Frame para Response
        response_frame = ttk.LabelFrame(paned, text="Response Recebida", padding=5)
        paned.add(response_frame, weight=1)
        self.repeater_response_text = scrolledtext.ScrolledText(response_frame, wrap=tk.WORD, height=10)
        self.repeater_response_text.pack(fill="both", expand=True)

    def setup_sender_tab(self):
        """Configura a aba de Sender (envios em massa)."""
        sender_tab = ttk.Frame(self.notebook)
        self.notebook.add(sender_tab, text="Sender")

        # Frame superior para configuração
        config_frame = ttk.LabelFrame(sender_tab, text="Configuração de Envio em Massa", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Parâmetro a Substituir
        ttk.Label(config_frame, text="Parâmetro a Substituir:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.sender_param_entry = ttk.Entry(config_frame, width=30)
        self.sender_param_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        Tooltip(self.sender_param_entry, "Nome do parâmetro a ser substituído (na URL ou no Body).")

        # Arquivo de Lista
        ttk.Label(config_frame, text="Arquivo de Valores (.txt):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sender_file_path = tk.StringVar()
        file_entry = ttk.Entry(config_frame, textvariable=self.sender_file_path, width=50, state="readonly")
        file_entry.grid(row=1, column=1, columnspan=2, sticky="we", padx=5, pady=5)
        file_button = ttk.Button(config_frame, text="Selecionar...", command=self.select_sender_file)
        file_button.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        Tooltip(file_button, "Use para envios em massa. Um valor por linha.")

        # Número de Threads
        ttk.Label(config_frame, text="Threads:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.sender_threads_spinbox = ttk.Spinbox(config_frame, from_=1, to=100, width=10)
        self.sender_threads_spinbox.set("10")
        self.sender_threads_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        Tooltip(self.sender_threads_spinbox, "Número de requisições simultâneas para envios em massa.")

        # Botão de Iniciar
        start_sender_button = ttk.Button(config_frame, text="Iniciar Envio em Massa", command=self.start_sender)
        start_sender_button.grid(row=3, column=0, columnspan=4, pady=15)
        Tooltip(start_sender_button, "Inicia o processo de reenvio.")

        # --- Requisição ---
        request_frame = ttk.LabelFrame(sender_tab, text="Request Base", padding=5)
        request_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.sender_request_text = scrolledtext.ScrolledText(request_frame, wrap=tk.WORD, height=10)
        self.sender_request_text.pack(fill="both", expand=True)

        # --- Feedback Visual ---
        feedback_frame = ttk.Frame(sender_tab)
        feedback_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Barra de Progresso
        self.sender_progress = ttk.Progressbar(feedback_frame, orient="horizontal", length=100, mode="determinate")
        self.sender_progress.pack(fill="x", pady=5)

        # Frame de Resultados
        results_frame = ttk.LabelFrame(feedback_frame, text="Resultados do Envio", padding=10)
        results_frame.pack(fill="both", expand=True, pady=10)

        # Tabela (Treeview) de Resultados
        columns = ('URL', 'Status', 'Resultado')
        self.sender_results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=8)

        self.sender_results_tree.heading('URL', text='URL')
        self.sender_results_tree.heading('Status', text='Status')
        self.sender_results_tree.heading('Resultado', text='Resultado')

        self.sender_results_tree.column('URL', width=400)
        self.sender_results_tree.column('Status', width=100, anchor="center")
        self.sender_results_tree.column('Resultado', width=100, anchor="center")

        # Configuração de tags para cores
        self.sender_results_tree.tag_configure('success', foreground='green')
        self.sender_results_tree.tag_configure('failure', foreground='red')

        self.sender_results_tree.pack(side="left", fill="both", expand=True)

        # Scrollbar para a tabela
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.sender_results_tree.yview)
        results_scrollbar.pack(side="right", fill="y")
        self.sender_results_tree.configure(yscrollcommand=results_scrollbar.set)

        # Botão para Limpar Resultados
        clear_results_button = ttk.Button(feedback_frame, text="Limpar Resultados", command=self.clear_sender_results)
        clear_results_button.pack(pady=5)
        Tooltip(clear_results_button, "Limpa a tabela de resultados do envio.")

    def clear_sender_results(self):
        """Limpa a tabela de resultados da aba de repetição."""
        for item in self.sender_results_tree.get_children():
            self.sender_results_tree.delete(item)
        self.sender_progress['value'] = 0

    def select_sender_file(self):
        """Abre uma caixa de diálogo para selecionar o arquivo de valores."""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Selecione um arquivo de valores",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.sender_file_path.set(filepath)

    def start_repeater(self):
        """Inicia o processo de reenvio manual a partir da aba Repetição."""
        raw_request = self.repeater_request_text.get("1.0", tk.END).strip()
        if not raw_request:
            messagebox.showwarning("Aviso", "Não há nenhuma requisição para reenviar.")
            return

        # Injeta os cookies do Jar na requisição
        raw_request = self._inject_jar_cookies(raw_request)

        param_name = self.repeater_param_entry.get().strip()
        manual_value = self.repeater_manual_value_entry.get().strip()

        # Limpa a aba de resposta
        self.repeater_response_text.delete('1.0', tk.END)

        # Envio único (manual ou sem modificação)
        from src.core.sender import send_from_raw

        def repeater_thread():
            response = send_from_raw(raw_request, param_name if manual_value else None, manual_value, self.config.get_port())
            self.root.after(0, self._display_repeater_response, response)

        thread = threading.Thread(target=repeater_thread, daemon=True)
        thread.start()

    def start_sender(self):
        """Inicia o processo de envio em massa a partir da aba Sender."""
        raw_request = self.sender_request_text.get("1.0", tk.END).strip()
        if not raw_request:
            messagebox.showwarning("Aviso", "A 'Request Base' está vazia.")
            return

        # Injeta os cookies do Jar na requisição
        raw_request = self._inject_jar_cookies(raw_request)

        param_name = self.sender_param_entry.get().strip()
        if not param_name:
            messagebox.showwarning("Aviso", "O 'Parâmetro a Substituir' é obrigatório.")
            return

        file_path = self.sender_file_path.get().strip()
        if not file_path:
            messagebox.showwarning("Aviso", "Selecione um arquivo de valores.")
            return

        threads = int(self.sender_threads_spinbox.get())
        from src.core.sender import run_sender_from_file

        # Limpa a tabela de resultados
        self.clear_sender_results()

        # Inicia o envio em uma thread separada
        thread = threading.Thread(
            target=run_sender_from_file,
            args=(raw_request, file_path, param_name, threads, self.update_sender_results, self.config.get_port()),
            daemon=True
        )
        thread.start()
        messagebox.showinfo("Iniciado", "Envio em massa iniciado. Acompanhe a tabela de resultados.")

    def update_sender_results(self, result, progress):
        """
        Atualiza a tabela de resultados e a barra de progresso de forma thread-safe.
        Esta função é chamada como callback a partir do sender.
        """
        def _update():
            # Insere o resultado na tabela
            status = result.get('status', 'Erro')
            outcome = result.get('outcome', 'Falha')
            tag = 'success' if outcome == 'Sucesso' else 'failure'
            self.sender_results_tree.insert(
                '', 'end',
                values=(result.get('url', ''), status, outcome),
                tags=(tag,)
            )
            # Atualiza a barra de progresso
            self.sender_progress['value'] = progress

        # Garante que a atualização da UI ocorra na thread principal
        self.root.after(0, _update)

    def _display_repeater_response(self, response):
        """Exibe o conteúdo da resposta na aba 'Response' do repetidor."""
        self.repeater_response_text.delete('1.0', tk.END)
        if response is None:
            self.repeater_response_text.insert('1.0', "Erro: A requisição falhou. Verifique os logs para mais detalhes.")
            return

        # Formata a resposta
        status_line = f"HTTP/1.1 {response.status_code} {response.reason}\n"
        headers = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
        body = response.text

        full_response = f"{status_line}{headers}\n\n{body}"
        self.repeater_response_text.insert('1.0', full_response)

    def show_context_menu(self, event):
        """Exibe o menu de contexto no histórico de requisições."""
        # Seleciona o item sob o cursor
        item_id = self.history_tree.identify_row(event.y)
        if not item_id:
            return

        # Garante que o item clicado esteja selecionado
        self.history_tree.selection_set(item_id)

        selected_entry = self.history_map.get(item_id)
        if not selected_entry:
            return

        # Cria o menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(
            label="Enviar para Repetição",
            command=lambda: self.send_to_repeater(selected_entry)
        )
        context_menu.add_command(
            label="Enviar para o Sender",
            command=lambda: self.send_to_sender(selected_entry)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Definir como Requisição 1 (Comparador)",
            command=lambda: self.set_comparator_request_1(selected_entry)
        )
        context_menu.add_command(
            label="Definir como Requisição 2 (Comparador)",
            command=lambda: self.set_comparator_request_2(selected_entry)
        )

        # Exibe o menu na posição do cursor
        context_menu.tk_popup(event.x_root, event.y_root)

    def send_to_repeater(self, entry):
        """Copia todos os dados da requisição para a aba de Repetição e preenche a UI."""
        self.repeater_request_data = entry
        self.notebook.select(3)  # Muda para a aba de Repetição (agora índice 3)
        self._populate_repeater_request_tab()

    def send_to_sender(self, entry):
        """Copia todos os dados da requisição para a aba do Sender e preenche a UI."""
        self.sender_request_data = entry
        self.notebook.select(4)  # Muda para a aba do Sender (agora índice 4)
        self._populate_sender_request_tab()

    def _populate_repeater_request_tab(self):
        """Preenche a aba 'Request' do repetidor com os dados da requisição armazenada."""
        if not self.repeater_request_data:
            return

        entry = self.repeater_request_data

        # Formata o texto da requisição
        request_info = f"{entry['method']} {entry['path']} HTTP/1.1\n"
        request_info += f"Host: {entry['host']}\n"
        for key, value in entry['request_headers'].items():
            request_info += f"{key}: {value}\n"

        if entry['request_body']:
            request_info += f"\n{entry['request_body']}"

        # Preenche a área de texto
        self.repeater_request_text.delete('1.0', tk.END)
        self.repeater_request_text.insert('1.0', request_info)

        # Limpa a área de response
        self.repeater_response_text.delete('1.0', tk.END)

    def _populate_sender_request_tab(self):
        """Preenche a aba 'Request' do sender com os dados da requisição armazenada."""
        if not self.sender_request_data:
            return

        entry = self.sender_request_data

        # Formata o texto da requisição
        request_info = f"{entry['method']} {entry['path']} HTTP/1.1\n"
        request_info += f"Host: {entry['host']}\n"
        for key, value in entry['request_headers'].items():
            request_info += f"{key}: {value}\n"

        if entry['request_body']:
            request_info += f"\n{entry['request_body']}"

        # Preenche a área de texto
        self.sender_request_text.delete('1.0', tk.END)
        self.sender_request_text.insert('1.0', request_info)

    def setup_cookie_jar_tab(self):
        """Configura a aba do Gerenciador de Cookies (Cookie Jar)."""
        cookie_tab = ttk.Frame(self.notebook)
        self.notebook.add(cookie_tab, text="Cookie Jar")

        # PanedWindow para dividir a tela
        paned = ttk.PanedWindow(cookie_tab, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Frame da Esquerda: Todos os Cookies Capturados ---
        all_cookies_frame = ttk.LabelFrame(paned, text="Todos os Cookies Capturados", padding=10)
        paned.add(all_cookies_frame, weight=1)

        # Treeview para todos os cookies
        self.all_cookies_tree = ttk.Treeview(all_cookies_frame, columns=('Nome', 'Valor'), show='tree headings')
        self.all_cookies_tree.heading('#0', text='Domínio')
        self.all_cookies_tree.column('#0', width=150)
        self.all_cookies_tree.heading('Nome', text='Nome')
        self.all_cookies_tree.heading('Valor', text='Valor')
        self.all_cookies_tree.column('Nome', width=150)
        self.all_cookies_tree.column('Valor', width=250)
        self.all_cookies_tree.pack(side="left", fill="both", expand=True)

        all_scrollbar = ttk.Scrollbar(all_cookies_frame, orient="vertical", command=self.all_cookies_tree.yview)
        all_scrollbar.pack(side="right", fill="y")
        self.all_cookies_tree.configure(yscrollcommand=all_scrollbar.set)

        # --- Frame do Meio: Botões de Ação ---
        actions_frame = ttk.Frame(paned, padding=10)
        paned.add(actions_frame, weight=0) # Peso 0 para não expandir

        add_button = ttk.Button(actions_frame, text=">>", width=5, command=self._add_cookie_to_jar)
        add_button.pack(pady=10)
        Tooltip(add_button, "Adicionar selecionado ao Cookie Jar")

        remove_button = ttk.Button(actions_frame, text="<<", width=5, command=self._remove_cookie_from_jar)
        remove_button.pack(pady=10)
        Tooltip(remove_button, "Remover selecionado do Cookie Jar")


        # --- Frame da Direita: Cookie Jar ---
        jar_frame = ttk.LabelFrame(paned, text="Cookie Jar (Sessão Forçada)", padding=10)
        paned.add(jar_frame, weight=1)

        # Treeview para o Cookie Jar
        self.jar_tree = ttk.Treeview(jar_frame, columns=('Nome', 'Valor'), show='headings')
        self.jar_tree.heading('Nome', text='Nome')
        self.jar_tree.heading('Valor', text='Valor')
        self.jar_tree.column('Nome', width=150)
        self.jar_tree.column('Valor', width=250)
        self.jar_tree.pack(side="left", fill="both", expand=True)

        jar_scrollbar = ttk.Scrollbar(jar_frame, orient="vertical", command=self.jar_tree.yview)
        jar_scrollbar.pack(side="right", fill="y")
        self.jar_tree.configure(yscrollcommand=jar_scrollbar.set)

        # Botão para limpar o Jar
        clear_jar_button = ttk.Button(jar_frame, text="Limpar Cookie Jar", command=self._clear_cookie_jar)
        clear_jar_button.pack(side="bottom", fill="x", pady=5)
        Tooltip(clear_jar_button, "Remove todos os cookies do Jar")

    def _inject_jar_cookies(self, raw_request: str) -> str:
        """Substitui ou adiciona o cabeçalho de Cookie na requisição com os cookies do Jar."""
        jar_header = self.cookie_manager.get_jar_cookies_header()
        if not jar_header:
            return raw_request  # Retorna a requisição original se o Jar estiver vazio

        cookie_header_line = f"Cookie: {jar_header}"

        # Tenta substituir o cabeçalho de Cookie existente
        new_request, count = re.sub(
            r'^Cookie:.*$', cookie_header_line, raw_request, flags=re.IGNORECASE | re.MULTILINE
        )

        # Se nenhum cabeçalho de Cookie foi substituído, adiciona um novo
        if count == 0:
            # Insere o cabeçalho de Cookie após a linha do Host
            if '\nHost:' in new_request:
                new_request = re.sub(r'(\nHost:[^\n]*)', r'\1\n' + cookie_header_line, new_request, count=1)
            else:
                # Adiciona após a primeira linha (linha de requisição)
                parts = new_request.split('\n', 1)
                if len(parts) > 1:
                    new_request = f"{parts[0]}\n{cookie_header_line}\n{parts[1]}"
                else:
                    new_request = f"{parts[0]}\n{cookie_header_line}"

        return new_request

    def _refresh_cookie_trees(self):
        """Atualiza as árvores de cookies com os dados do CookieManager."""
        # --- Atualiza a árvore de todos os cookies ---
        self.all_cookies_tree.delete(*self.all_cookies_tree.get_children())
        all_cookies = self.cookie_manager.get_all_cookies()
        # A primeira coluna é a 'text', as outras são 'values'
        self.all_cookies_tree.column('#0', width=150)
        self.all_cookies_tree.heading('#0', text='Domínio')

        for domain, cookies in sorted(all_cookies.items()):
            domain_id = self.all_cookies_tree.insert('', 'end', text=domain, open=True)
            for name, value in sorted(cookies.items()):
                self.all_cookies_tree.insert(domain_id, 'end', values=(name, value))

        # --- Atualiza a árvore do Cookie Jar ---
        self.jar_tree.delete(*self.jar_tree.get_children())
        jar_cookies = self.cookie_manager.get_jar_cookies_list()
        for cookie in jar_cookies:
            self.jar_tree.insert('', 'end', values=(cookie['name'], cookie['value']))

    def _add_cookie_to_jar(self):
        """Adiciona o cookie selecionado da lista 'Todos' para o 'Jar'."""
        selection = self.all_cookies_tree.selection()
        if not selection:
            return

        item = selection[0]
        # Garante que estamos pegando um cookie (que tem um pai), não um domínio
        if self.all_cookies_tree.parent(item):
            values = self.all_cookies_tree.item(item)['values']
            if len(values) == 2:
                name, value = values
                self.cookie_manager.add_to_jar(name, value)
                self._refresh_cookie_trees()

    def _remove_cookie_from_jar(self):
        """Remove o cookie selecionado do 'Jar'."""
        selection = self.jar_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.jar_tree.item(item)['values']
        if len(values) == 2:
            name, _ = values
            self.cookie_manager.remove_from_jar(name)
            self._refresh_cookie_trees()

    def _clear_cookie_jar(self):
        """Limpa todos os cookies do 'Jar'."""
        if messagebox.askyesno("Confirmar", "Deseja realmente limpar todo o Cookie Jar?"):
            self.cookie_manager.clear_jar()
            self._refresh_cookie_trees()

    def _handle_decode_action(self, action_function):
        """Função auxiliar para executar uma ação de encode/decode."""
        input_text = self.decoder_input_text.get("1.0", tk.END).strip()
        if not input_text:
            return

        try:
            result = action_function(input_text)
            self.decoder_output_text.delete("1.0", tk.END)
            self.decoder_output_text.insert("1.0", result)
        except Exception as e:
            messagebox.showerror("Erro na Ação", f"Ocorreu um erro: {e}")

    def setup_intruder_tab(self):
        """Configura a aba de Intruder (Sender Avançado)."""
        intruder_tab = ttk.Frame(self.notebook)
        self.notebook.add(intruder_tab, text="💥 Intruder")

        # Frame superior para configuração
        config_frame = ttk.LabelFrame(intruder_tab, text="Configuração de Ataque", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Row 0: Attack Type Selection
        ttk.Label(config_frame, text="Tipo de Ataque:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.intruder_attack_type = tk.StringVar(value="sniper")
        attack_types = [
            ("Sniper", "sniper"),
            ("Battering Ram", "battering_ram"),
            ("Pitchfork", "pitchfork"),
            ("Cluster Bomb", "cluster_bomb")
        ]
        attack_frame = ttk.Frame(config_frame)
        attack_frame.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        for text, value in attack_types:
            ttk.Radiobutton(attack_frame, text=text, value=value, variable=self.intruder_attack_type).pack(side="left", padx=5)
        
        # Tooltips for attack types
        Tooltip(attack_frame, 
                "Sniper: Um payload set, testa cada posição individualmente\n"
                "Battering Ram: Um payload set, usa o mesmo valor em todas as posições\n"
                "Pitchfork: Múltiplos sets, itera em paralelo\n"
                "Cluster Bomb: Múltiplos sets, todas as combinações possíveis")

        # Row 1: Payload Files
        ttk.Label(config_frame, text="Payload Set 1:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.intruder_payload_file1 = tk.StringVar()
        file1_entry = ttk.Entry(config_frame, textvariable=self.intruder_payload_file1, width=40, state="readonly")
        file1_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(config_frame, text="📂", command=lambda: self.select_intruder_payload_file(1), width=3).grid(row=1, column=2, padx=2)

        ttk.Label(config_frame, text="Payload Set 2:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.intruder_payload_file2 = tk.StringVar()
        file2_entry = ttk.Entry(config_frame, textvariable=self.intruder_payload_file2, width=40, state="readonly")
        file2_entry.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(config_frame, text="📂", command=lambda: self.select_intruder_payload_file(2), width=3).grid(row=2, column=2, padx=2)
        Tooltip(file2_entry, "Opcional. Use para Pitchfork e Cluster Bomb")

        # Row 3: Payload Processing
        ttk.Label(config_frame, text="Processamento:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        proc_frame = ttk.Frame(config_frame)
        proc_frame.grid(row=3, column=1, columnspan=2, sticky="we", padx=5, pady=5)
        
        # Checkboxes for payload processing
        self.intruder_proc_url_encode = tk.BooleanVar()
        self.intruder_proc_base64 = tk.BooleanVar()
        self.intruder_proc_md5 = tk.BooleanVar()
        
        ttk.Checkbutton(proc_frame, text="URL Encode", variable=self.intruder_proc_url_encode).pack(side="left", padx=2)
        ttk.Checkbutton(proc_frame, text="Base64", variable=self.intruder_proc_base64).pack(side="left", padx=2)
        ttk.Checkbutton(proc_frame, text="MD5 Hash", variable=self.intruder_proc_md5).pack(side="left", padx=2)
        
        # Prefix/Suffix
        prefix_suffix_frame = ttk.Frame(config_frame)
        prefix_suffix_frame.grid(row=4, column=1, columnspan=2, sticky="we", padx=5, pady=5)
        ttk.Label(prefix_suffix_frame, text="Prefix:").pack(side="left", padx=2)
        self.intruder_prefix = ttk.Entry(prefix_suffix_frame, width=15)
        self.intruder_prefix.pack(side="left", padx=2)
        ttk.Label(prefix_suffix_frame, text="Suffix:").pack(side="left", padx=5)
        self.intruder_suffix = ttk.Entry(prefix_suffix_frame, width=15)
        self.intruder_suffix.pack(side="left", padx=2)

        # Row 5: Grep Extraction
        ttk.Label(config_frame, text="Grep (Regex):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.intruder_grep_pattern = ttk.Entry(config_frame, width=40)
        self.intruder_grep_pattern.grid(row=5, column=1, sticky="we", padx=5, pady=5)
        Tooltip(self.intruder_grep_pattern, "Regex para extrair dados das respostas. Ex: token=([a-zA-Z0-9]+)")

        # Row 6: Threads
        ttk.Label(config_frame, text="Threads:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.intruder_threads = ttk.Spinbox(config_frame, from_=1, to=100, width=10)
        self.intruder_threads.set("10")
        self.intruder_threads.grid(row=6, column=1, sticky="w", padx=5, pady=5)

        # Row 7: Action Buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="▶ Iniciar Ataque", command=self.start_intruder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="📋 Marcar Posições", command=self.mark_payload_positions).pack(side="left", padx=5)
        Tooltip(button_frame, "Use §...§ para marcar posições de payload na requisição")

        # Request Frame
        request_frame = ttk.LabelFrame(intruder_tab, text="Request Base (use §...§ para marcar posições)", padding=5)
        request_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add a text widget with scrollbar
        self.intruder_request_text = scrolledtext.ScrolledText(request_frame, wrap=tk.WORD, height=10)
        self.intruder_request_text.pack(fill="both", expand=True)
        
        # Example text
        example = (
            "GET /login?username=§admin§&password=§pass123§ HTTP/1.1\n"
            "Host: example.com\n"
            "User-Agent: Mozilla/5.0\n\n"
        )
        self.intruder_request_text.insert("1.0", example)

        # Results Frame
        results_frame = ttk.LabelFrame(intruder_tab, text="Resultados", padding=5)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Progress bar
        self.intruder_progress = ttk.Progressbar(results_frame, orient="horizontal", mode="determinate")
        self.intruder_progress.pack(fill="x", pady=5)

        # Results table
        columns = ('Payload(s)', 'Status', 'Length', 'Extracted', 'URL')
        self.intruder_results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        self.intruder_results_tree.heading('Payload(s)', text='Payload(s)')
        self.intruder_results_tree.heading('Status', text='Status')
        self.intruder_results_tree.heading('Length', text='Length')
        self.intruder_results_tree.heading('Extracted', text='Extracted')
        self.intruder_results_tree.heading('URL', text='URL')
        
        self.intruder_results_tree.column('Payload(s)', width=200)
        self.intruder_results_tree.column('Status', width=80, anchor="center")
        self.intruder_results_tree.column('Length', width=80, anchor="center")
        self.intruder_results_tree.column('Extracted', width=150)
        self.intruder_results_tree.column('URL', width=300)
        
        # Color tags
        self.intruder_results_tree.tag_configure('success', foreground='green')
        self.intruder_results_tree.tag_configure('failure', foreground='red')
        
        self.intruder_results_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.intruder_results_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.intruder_results_tree.configure(yscrollcommand=scrollbar.set)

        # Clear button
        ttk.Button(results_frame, text="🗑 Limpar Resultados", command=self.clear_intruder_results).pack(pady=5)

    def select_intruder_payload_file(self, set_number):
        """Seleciona arquivo de payload para o Intruder"""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title=f"Selecione Payload Set {set_number}",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            if set_number == 1:
                self.intruder_payload_file1.set(filepath)
            elif set_number == 2:
                self.intruder_payload_file2.set(filepath)

    def mark_payload_positions(self):
        """Ajuda o usuário a marcar posições de payload"""
        try:
            # Get current selection
            selection = self.intruder_request_text.tag_ranges("sel")
            if selection:
                start_idx = selection[0]
                end_idx = selection[1]
                selected_text = self.intruder_request_text.get(start_idx, end_idx)
                
                # Replace with marked version
                marked_text = f"§{selected_text}§"
                self.intruder_request_text.delete(start_idx, end_idx)
                self.intruder_request_text.insert(start_idx, marked_text)
                
                messagebox.showinfo("Sucesso", f"Posição marcada: §{selected_text}§")
            else:
                messagebox.showinfo("Info", 
                    "Selecione o texto que deseja marcar como posição de payload,\n"
                    "depois clique em 'Marcar Posições'.\n\n"
                    "Ou digite manualmente usando §...§ ao redor do valor.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao marcar posição: {e}")

    def start_intruder(self):
        """Inicia o ataque do Intruder"""
        from src.core.advanced_sender import AdvancedSender, load_payloads_from_file
        
        # Get request
        raw_request = self.intruder_request_text.get("1.0", tk.END).strip()
        if not raw_request:
            messagebox.showwarning("Aviso", "A requisição está vazia.")
            return
        
        # Check for payload positions
        if '§' not in raw_request:
            messagebox.showwarning("Aviso", 
                "Nenhuma posição de payload marcada!\n\n"
                "Use §...§ para marcar onde os payloads devem ser inseridos.\n"
                "Exemplo: GET /test?id=§1§")
            return
        
        # Inject cookies
        raw_request = self._inject_jar_cookies(raw_request)
        
        # Load payload sets
        payload_file1 = self.intruder_payload_file1.get().strip()
        if not payload_file1:
            messagebox.showwarning("Aviso", "Selecione pelo menos o Payload Set 1.")
            return
        
        payload_sets = [load_payloads_from_file(payload_file1)]
        
        payload_file2 = self.intruder_payload_file2.get().strip()
        if payload_file2:
            payload_sets.append(load_payloads_from_file(payload_file2))
        
        # Build processor chain
        processors_list = []
        for _ in range(len(payload_sets)):
            proc_chain = []
            
            # Prefix
            prefix = self.intruder_prefix.get().strip()
            if prefix:
                proc_chain.append({'type': 'prefix', 'value': prefix})
            
            # Suffix  
            suffix = self.intruder_suffix.get().strip()
            if suffix:
                proc_chain.append({'type': 'suffix', 'value': suffix})
            
            # Encoding/Hashing
            if self.intruder_proc_url_encode.get():
                proc_chain.append({'type': 'url_encode'})
            if self.intruder_proc_base64.get():
                proc_chain.append({'type': 'base64'})
            if self.intruder_proc_md5.get():
                proc_chain.append({'type': 'md5'})
            
            processors_list.append(proc_chain)
        
        # Get grep pattern
        grep_patterns = []
        grep_pattern = self.intruder_grep_pattern.get().strip()
        if grep_pattern:
            grep_patterns.append(grep_pattern)
        
        # Get attack type
        attack_type = self.intruder_attack_type.get()
        
        # Get threads
        threads = int(self.intruder_threads.get())
        
        # Clear results
        self.clear_intruder_results()
        
        # Create sender
        sender = AdvancedSender(
            raw_request=raw_request,
            attack_type=attack_type,
            payload_sets=payload_sets,
            processors=processors_list,
            grep_patterns=grep_patterns,
            num_threads=threads,
            proxy_port=self.config.get_port()
        )
        
        # Start attack in thread
        thread = threading.Thread(
            target=sender.run_attack,
            args=(self.update_intruder_results,),
            daemon=True
        )
        thread.start()
        
        messagebox.showinfo("Iniciado", 
            f"Ataque {attack_type} iniciado!\n"
            f"Acompanhe os resultados na tabela abaixo.")

    def update_intruder_results(self, message):
        """Atualiza resultados do Intruder (thread-safe)"""
        def _update():
            msg_type = message.get('type')
            
            if msg_type == 'progress_update':
                self.intruder_progress['value'] = message.get('value', 0)
            
            elif msg_type == 'result':
                data = message.get('data', {})
                payloads = ', '.join(str(p) for p in data.get('payloads', []))
                status = data.get('status', 'Error')
                length = data.get('length', 0)
                extracted = ', '.join(data.get('extracted', []))
                url = data.get('url', 'N/A')
                
                tag = 'success' if data.get('success', False) else 'failure'
                
                self.intruder_results_tree.insert(
                    '', 'end',
                    values=(payloads, status, length, extracted, url),
                    tags=(tag,)
                )
            
            elif msg_type == 'progress_done':
                self.intruder_progress['value'] = 100
                messagebox.showinfo("Concluído", "Ataque finalizado!")
        
        self.root.after(0, _update)

    def clear_intruder_results(self):
        """Limpa resultados do Intruder"""
        for item in self.intruder_results_tree.get_children():
            self.intruder_results_tree.delete(item)
        self.intruder_progress['value'] = 0

    def setup_decoder_tab(self):
        """Configura a aba da ferramenta Decoder."""
        decoder_tab = ttk.Frame(self.notebook)
        self.notebook.add(decoder_tab, text="Decoder")

        # PanedWindow para dividir a área de texto dos botões
        main_paned = ttk.PanedWindow(decoder_tab, orient=tk.VERTICAL)
        main_paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame superior com as áreas de texto
        text_frame = ttk.Frame(main_paned)
        main_paned.add(text_frame, weight=4)

        text_paned = ttk.PanedWindow(text_frame, orient=tk.HORIZONTAL)
        text_paned.pack(fill="both", expand=True)

        # Input Text
        input_frame = ttk.LabelFrame(text_paned, text="Input", padding=5)
        text_paned.add(input_frame, weight=1)
        self.decoder_input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=15)
        self.decoder_input_text.pack(fill="both", expand=True)

        # Output Text
        output_frame = ttk.LabelFrame(text_paned, text="Output", padding=5)
        text_paned.add(output_frame, weight=1)
        self.decoder_output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=15)
        self.decoder_output_text.pack(fill="both", expand=True)


        # Frame inferior com os botões
        buttons_frame = ttk.LabelFrame(main_paned, text="Ações", padding=10)
        main_paned.add(buttons_frame, weight=1)

        # Botões de Base64
        ttk.Button(buttons_frame, text="Encode Base64",
                   command=lambda: self._handle_decode_action(decoder.Decoder.b64_encode)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Decode Base64",
                   command=lambda: self._handle_decode_action(decoder.Decoder.b64_decode)).grid(row=0, column=1, padx=5, pady=5)

        # Botões de URL
        ttk.Button(buttons_frame, text="URL Encode",
                   command=lambda: self._handle_decode_action(decoder.Decoder.url_encode)).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(buttons_frame, text="URL Decode",
                   command=lambda: self._handle_decode_action(decoder.Decoder.url_decode)).grid(row=1, column=1, padx=5, pady=5)

        # Botões de HTML
        ttk.Button(buttons_frame, text="HTML Encode",
                   command=lambda: self._handle_decode_action(decoder.Decoder.html_encode)).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(buttons_frame, text="HTML Decode",
                   command=lambda: self._handle_decode_action(decoder.Decoder.html_decode)).grid(row=0, column=3, padx=5, pady=5)

        # Botões de Hex
        ttk.Button(buttons_frame, text="Hex Encode",
                   command=lambda: self._handle_decode_action(decoder.Decoder.hex_encode)).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Hex Decode",
                   command=lambda: self._handle_decode_action(decoder.Decoder.hex_decode)).grid(row=1, column=3, padx=5, pady=5)

        # Separador e Botões de Hash
        ttk.Separator(buttons_frame, orient='horizontal').grid(row=2, columnspan=4, sticky='ew', pady=10)

        ttk.Label(buttons_frame, text="Hashing:").grid(row=3, column=0, sticky='w', padx=5)
        ttk.Button(buttons_frame, text="MD5",
                   command=lambda: self._handle_decode_action(decoder.Decoder.hash_md5)).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(buttons_frame, text="SHA-1",
                   command=lambda: self._handle_decode_action(decoder.Decoder.hash_sha1)).grid(row=3, column=2, padx=5, pady=5)
        ttk.Button(buttons_frame, text="SHA-256",
                   command=lambda: self._handle_decode_action(decoder.Decoder.hash_sha256)).grid(row=3, column=3, padx=5, pady=5)

    def setup_comparator_tab(self):
        """Configura a aba de Comparador de Requisições."""
        comparator_tab = ttk.Frame(self.notebook)
        self.notebook.add(comparator_tab, text="Comparador")

        # Frame de instruções
        info_frame = ttk.LabelFrame(comparator_tab, text="Instruções", padding=5)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_label = ttk.Label(info_frame, 
                              text="Use o menu de contexto (clique direito) no Histórico de Requisições para selecionar duas requisições para comparar.",
                              wraplength=900)
        info_label.pack(padx=5, pady=5)

        # Frame de status
        status_frame = ttk.Frame(comparator_tab)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Labels para mostrar quais requisições foram selecionadas
        req1_frame = ttk.LabelFrame(status_frame, text="Requisição 1", padding=5)
        req1_frame.pack(side="left", fill="both", expand=True, padx=5)
        self.comparator_req1_label = ttk.Label(req1_frame, text="Nenhuma requisição selecionada", foreground="gray")
        self.comparator_req1_label.pack()
        
        req2_frame = ttk.LabelFrame(status_frame, text="Requisição 2", padding=5)
        req2_frame.pack(side="left", fill="both", expand=True, padx=5)
        self.comparator_req2_label = ttk.Label(req2_frame, text="Nenhuma requisição selecionada", foreground="gray")
        self.comparator_req2_label.pack()

        # Botões de ação
        buttons_frame = ttk.Frame(comparator_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Comparar", command=self.compare_requests).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Limpar", command=self.clear_comparator).pack(side="left", padx=5)

        # Notebook para Request/Response comparisons
        self.comparator_notebook = ttk.Notebook(comparator_tab)
        self.comparator_notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab de comparação de Request
        request_compare_tab = ttk.Frame(self.comparator_notebook)
        self.comparator_notebook.add(request_compare_tab, text="Request Comparison")
        
        request_paned = ttk.PanedWindow(request_compare_tab, orient=tk.HORIZONTAL)
        request_paned.pack(fill="both", expand=True)
        
        # Request 1
        req1_frame = ttk.LabelFrame(request_paned, text="Request 1", padding=5)
        request_paned.add(req1_frame, weight=1)
        self.comparator_request1_text = scrolledtext.ScrolledText(req1_frame, wrap=tk.WORD, height=20)
        self.comparator_request1_text.pack(fill="both", expand=True)
        
        # Request 2
        req2_frame = ttk.LabelFrame(request_paned, text="Request 2", padding=5)
        request_paned.add(req2_frame, weight=1)
        self.comparator_request2_text = scrolledtext.ScrolledText(req2_frame, wrap=tk.WORD, height=20)
        self.comparator_request2_text.pack(fill="both", expand=True)

        # Tab de comparação de Response
        response_compare_tab = ttk.Frame(self.comparator_notebook)
        self.comparator_notebook.add(response_compare_tab, text="Response Comparison")
        
        response_paned = ttk.PanedWindow(response_compare_tab, orient=tk.HORIZONTAL)
        response_paned.pack(fill="both", expand=True)
        
        # Response 1
        resp1_frame = ttk.LabelFrame(response_paned, text="Response 1", padding=5)
        response_paned.add(resp1_frame, weight=1)
        self.comparator_response1_text = scrolledtext.ScrolledText(resp1_frame, wrap=tk.WORD, height=20)
        self.comparator_response1_text.pack(fill="both", expand=True)
        
        # Response 2
        resp2_frame = ttk.LabelFrame(response_paned, text="Response 2", padding=5)
        response_paned.add(resp2_frame, weight=1)
        self.comparator_response2_text = scrolledtext.ScrolledText(resp2_frame, wrap=tk.WORD, height=20)
        self.comparator_response2_text.pack(fill="both", expand=True)

        # Configurar tags para highlighting de diferenças
        for text_widget in [self.comparator_request1_text, self.comparator_request2_text,
                           self.comparator_response1_text, self.comparator_response2_text]:
            text_widget.tag_configure("diff", background="#ffcccc")
            text_widget.tag_configure("same", background="white")

    def set_comparator_request_1(self, entry):
        """Define a primeira requisição para comparação."""
        self.comparator_request_1 = entry
        label_text = f"{entry['method']} {entry['host']}{entry['path']} - {entry['timestamp']}"
        self.comparator_req1_label.config(text=label_text, foreground="black")
        log.info(f"Requisição 1 selecionada para comparação: {label_text}")
        
        # Muda para a aba do comparador
        self.notebook.select(7)  # Tab 8 (índice 7)

    def set_comparator_request_2(self, entry):
        """Define a segunda requisição para comparação."""
        self.comparator_request_2 = entry
        label_text = f"{entry['method']} {entry['host']}{entry['path']} - {entry['timestamp']}"
        self.comparator_req2_label.config(text=label_text, foreground="black")
        log.info(f"Requisição 2 selecionada para comparação: {label_text}")
        
        # Muda para a aba do comparador
        self.notebook.select(7)  # Tab 8 (índice 7)

    def compare_requests(self):
        """Compara as duas requisições selecionadas."""
        if not self.comparator_request_1 or not self.comparator_request_2:
            messagebox.showwarning("Aviso", "Por favor, selecione duas requisições para comparar!")
            return

        # Formata as requisições
        req1_text = self._format_request(self.comparator_request_1)
        req2_text = self._format_request(self.comparator_request_2)
        
        resp1_text = self._format_response(self.comparator_request_1)
        resp2_text = self._format_response(self.comparator_request_2)

        # Limpa os campos
        self.comparator_request1_text.delete('1.0', tk.END)
        self.comparator_request2_text.delete('1.0', tk.END)
        self.comparator_response1_text.delete('1.0', tk.END)
        self.comparator_response2_text.delete('1.0', tk.END)

        # Insere o texto
        self.comparator_request1_text.insert('1.0', req1_text)
        self.comparator_request2_text.insert('1.0', req2_text)
        self.comparator_response1_text.insert('1.0', resp1_text)
        self.comparator_response2_text.insert('1.0', resp2_text)

        # Aplica highlighting de diferenças
        self._highlight_differences(self.comparator_request1_text, self.comparator_request2_text, req1_text, req2_text)
        self._highlight_differences(self.comparator_response1_text, self.comparator_response2_text, resp1_text, resp2_text)

        log.info("Comparação realizada")

    def _format_request(self, entry):
        """Formata uma requisição para exibição."""
        request_info = f"{entry['method']} {entry['path']} HTTP/1.1\n"
        request_info += f"Host: {entry['host']}\n"
        for key, value in entry['request_headers'].items():
            request_info += f"{key}: {value}\n"
        
        if entry['request_body']:
            request_info += f"\n{entry['request_body']}"
        
        return request_info

    def _format_response(self, entry):
        """Formata uma resposta para exibição."""
        response_info = f"Status: {entry['status']}\n\n"
        for key, value in entry['response_headers'].items():
            response_info += f"{key}: {value}\n"
        
        if entry['response_body']:
            response_info += f"\n{entry['response_body']}"
        
        return response_info

    def _highlight_differences(self, text_widget1, text_widget2, text1, text2):
        """Aplica highlighting de diferenças entre dois textos usando difflib."""
        import difflib
        
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        # Usa SequenceMatcher para encontrar diferenças
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        # Marca as linhas diferentes
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace' or tag == 'delete':
                # Marca linhas diferentes na primeira janela
                start_line = i1 + 1
                end_line = i2 + 1
                for line_num in range(start_line, end_line):
                    text_widget1.tag_add("diff", f"{line_num}.0", f"{line_num}.end")
            
            if tag == 'replace' or tag == 'insert':
                # Marca linhas diferentes na segunda janela
                start_line = j1 + 1
                end_line = j2 + 1
                for line_num in range(start_line, end_line):
                    text_widget2.tag_add("diff", f"{line_num}.0", f"{line_num}.end")

    def clear_comparator(self):
        """Limpa o comparador."""
        self.comparator_request_1 = None
        self.comparator_request_2 = None
        
        self.comparator_req1_label.config(text="Nenhuma requisição selecionada", foreground="gray")
        self.comparator_req2_label.config(text="Nenhuma requisição selecionada", foreground="gray")
        
        self.comparator_request1_text.delete('1.0', tk.END)
        self.comparator_request2_text.delete('1.0', tk.END)
        self.comparator_response1_text.delete('1.0', tk.END)
        self.comparator_response2_text.delete('1.0', tk.END)
        
        log.info("Comparador limpo")

    def toggle_intercept(self):
        """Alterna o estado de interceptação manual."""
        if not self.proxy_running:
            messagebox.showinfo("Intercept", "Por favor, inicie o proxy primeiro.")
            return

        is_enabled = self.config.toggle_intercept()

        if is_enabled:
            self.intercept_status_label.config(text="Intercept: ON", foreground="green")
            self.intercept_toggle_button.config(text="Intercept is ON")
            log.info("Interceptação manual ativada.")
        else:
            self.intercept_status_label.config(text="Intercept: OFF", foreground="red")
            self.intercept_toggle_button.config(text="Intercept is OFF")
            # Limpa a fila e reseta a UI
            self.config.clear_intercept_queues()
            self._reset_intercept_ui()
            log.info("Interceptação manual desativada.")

    def check_intercept_queue(self):
        """Verifica a fila de interceptação periodicamente."""
        if self.config.is_intercept_enabled():
            request_data = self.config.get_from_intercept_queue(timeout=0.01)
            if request_data:
                self._display_intercepted_request(request_data)
        
        # Agenda próxima verificação
        self.root.after(100, self.check_intercept_queue)

    def _display_intercepted_request(self, request_data):
        """Exibe a requisição interceptada na UI."""
        self.current_intercept_request = request_data

        # Atualiza labels
        self.intercept_method_label.config(text=request_data['method'])
        self.intercept_url_label.config(text=request_data['url'])
        self.intercept_host_label.config(text=request_data['host'])

        # Atualiza headers
        self.intercept_headers_text.delete('1.0', tk.END)
        headers_text = ""
        for key, value in request_data['headers'].items():
            headers_text += f"{key}: {value}\n"
        self.intercept_headers_text.insert('1.0', headers_text)

        # Atualiza body
        self.intercept_body_text.delete('1.0', tk.END)
        self.intercept_body_text.insert('1.0', request_data['body'])

        # Habilita botões
        self.forward_button.config(state="normal")
        self.drop_button.config(state="normal")

        # Muda para a aba de interceptação
        self.notebook.select(1)  # Aba Intercept Manual

    def forward_request(self):
        """Envia a requisição interceptada (com modificações)."""
        if not self.current_intercept_request:
            return

        # Lê os dados editados
        headers_text = self.intercept_headers_text.get('1.0', tk.END).strip()
        body_text = self.intercept_body_text.get('1.0', tk.END).strip()

        # Parse headers
        modified_headers = {}
        for line in headers_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                modified_headers[key.strip()] = value.strip()

        # Envia resposta para a fila
        response_data = {
            'action': 'forward',
            'modified_headers': modified_headers,
            'modified_body': body_text
        }
        self.config.add_intercept_response(response_data)

        # Guarda a URL para o log e reseta a UI
        url = self.current_intercept_request.get('url') if isinstance(self.current_intercept_request, dict) else None
        self._reset_intercept_ui()
        log.info(f"Requisição enviada: {url}")

    def drop_request(self):
        """Cancela a requisição interceptada."""
        if not self.current_intercept_request:
            return

        # Envia resposta para a fila
        response_data = {'action': 'drop'}
        self.config.add_intercept_response(response_data)

        # Guarda a URL para o log e reseta a UI
        url = self.current_intercept_request.get('url') if isinstance(self.current_intercept_request, dict) else None
        self._reset_intercept_ui()
        log.info(f"Requisição cancelada: {url}")

    def _reset_intercept_ui(self):
        """Reseta a UI de interceptação."""
        self.current_intercept_request = None
        self.intercept_method_label.config(text="-")
        self.intercept_url_label.config(text="-")
        self.intercept_host_label.config(text="-")
        self.intercept_headers_text.delete('1.0', tk.END)
        self.intercept_body_text.delete('1.0', tk.END)
        self.forward_button.config(state="disabled")
        self.drop_button.config(state="disabled")

    def setup_scanner_tab(self):
        """Configura a aba de Scanner de Vulnerabilidades"""
        scanner_frame = ttk.Frame(self.notebook)
        self.notebook.add(scanner_frame, text="Scanner 🔐")

        # Frame superior com informações
        info_frame = ttk.LabelFrame(scanner_frame, text="Scanner de Vulnerabilidades", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)

        info_text = "O scanner detecta automaticamente vulnerabilidades em requisições/respostas:\n"
        info_text += "• SQL Injection (Error-Based, Boolean-Based, Time-Based)\n"
        info_text += "• XSS (Cross-Site Scripting)\n"
        info_text += "• CSRF (Cross-Site Request Forgery)\n"
        info_text += "• Path Traversal\n"
        info_text += "• Command Injection\n"
        info_text += "• CVEs conhecidas\n"
        info_text += "• Informações sensíveis expostas"
        
        ttk.Label(info_frame, text=info_text, justify="left").pack(anchor="w")

        # Frame de Scanner Ativo
        active_frame = ttk.LabelFrame(scanner_frame, text="Scanner Ativo", padding=10)
        active_frame.pack(fill="x", padx=10, pady=5)
        
        active_info = ttk.Label(active_frame, 
                               text="Selecione uma requisição no Histórico e clique em 'Scan Ativo' para testar ativamente.",
                               foreground="blue")
        active_info.pack(side="left", padx=5)
        
        self.active_scan_button = ttk.Button(active_frame, text="🔍 Scan Ativo", command=self.run_active_scan)
        self.active_scan_button.pack(side="left", padx=5)
        
        self.active_scan_status = ttk.Label(active_frame, text="", foreground="green")
        self.active_scan_status.pack(side="left", padx=5)

        # Filtros
        filter_frame = ttk.LabelFrame(scanner_frame, text="Filtros", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Severidade:").pack(side="left", padx=5)
        self.scanner_severity_var = tk.StringVar(value="Todas")
        severity_combo = ttk.Combobox(filter_frame, textvariable=self.scanner_severity_var, 
                                      values=["Todas", "Critical", "High", "Medium", "Low"], 
                                      state="readonly", width=15)
        severity_combo.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="Tipo:").pack(side="left", padx=5)
        self.scanner_type_var = tk.StringVar(value="Todos")
        type_combo = ttk.Combobox(filter_frame, textvariable=self.scanner_type_var,
                                  values=["Todos", 
                                         "SQL Injection", 
                                         "SQL Injection (Error-Based)",
                                         "SQL Injection (Boolean-Based)",
                                         "SQL Injection (Time-Based)",
                                         "XSS (Cross-Site Scripting)", 
                                         "CSRF (Cross-Site Request Forgery)", 
                                         "Path Traversal",
                                         "Command Injection",
                                         "Command Injection (Time-Based)",
                                         "CVE / Vulnerabilidade Conhecida", 
                                         "Informação Sensível Exposta"],
                                  state="readonly", width=35)
        type_combo.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Filtrar", command=self.filter_vulnerabilities).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Limpar", command=self.clear_vulnerability_filters).pack(side="left", padx=5)

        # Frame de lista de vulnerabilidades
        list_frame = ttk.LabelFrame(scanner_frame, text="Vulnerabilidades Detectadas", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview para vulnerabilidades
        columns = ("ID", "Severidade", "Tipo", "URL", "Método")
        self.scanner_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        self.scanner_tree.heading("ID", text="ID")
        self.scanner_tree.heading("Severidade", text="Severidade")
        self.scanner_tree.heading("Tipo", text="Tipo")
        self.scanner_tree.heading("URL", text="URL")
        self.scanner_tree.heading("Método", text="Método")

        self.scanner_tree.column("ID", width=50)
        self.scanner_tree.column("Severidade", width=100)
        self.scanner_tree.column("Tipo", width=250)
        self.scanner_tree.column("URL", width=400)
        self.scanner_tree.column("Método", width=80)

        # Scrollbar
        scanner_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.scanner_tree.yview)
        self.scanner_tree.configure(yscrollcommand=scanner_scrollbar.set)
        
        self.scanner_tree.pack(side="left", fill="both", expand=True)
        scanner_scrollbar.pack(side="right", fill="y")

        # Frame de detalhes da vulnerabilidade
        detail_frame = ttk.LabelFrame(scanner_frame, text="Detalhes da Vulnerabilidade", padding=10)
        detail_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.scanner_detail_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=10)
        self.scanner_detail_text.pack(fill="both", expand=True)

        # Bind evento de seleção
        self.scanner_tree.bind("<<TreeviewSelect>>", self.show_vulnerability_details)

        # Contador de vulnerabilidades
        self.scanner_count_label = ttk.Label(scanner_frame, text="Total: 0 vulnerabilidades")
        self.scanner_count_label.pack(pady=5)

    def filter_vulnerabilities(self):
        """Filtra vulnerabilidades baseado nos critérios selecionados"""
        self._update_scanner_list()

    def clear_vulnerability_filters(self):
        """Limpa os filtros de vulnerabilidades"""
        self.scanner_severity_var.set("Todas")
        self.scanner_type_var.set("Todos")
        self._update_scanner_list()

    def show_vulnerability_details(self, event):
        """Mostra detalhes da vulnerabilidade selecionada"""
        selection = self.scanner_tree.selection()
        if not selection:
            return

        item = self.scanner_tree.item(selection[0])
        vuln_id = item['values'][0]

        # Busca a vulnerabilidade no histórico
        for entry in self.history.get_history():
            if entry.get('vulnerabilities'):
                for i, vuln in enumerate(entry['vulnerabilities'], 1):
                    unique_id = f"{entry['id']}-{i}"
                    if unique_id == str(vuln_id):
                        # Exibe detalhes
                        self.scanner_detail_text.delete('1.0', tk.END)
                        
                        details = f"VULNERABILIDADE DETECTADA\n"
                        details += f"{'='*80}\n\n"
                        details += f"Tipo: {vuln['type']}\n"
                        details += f"Severidade: {vuln['severity']}\n"
                        details += f"URL: {vuln.get('url', 'N/A')}\n"
                        details += f"Método: {vuln.get('method', 'N/A')}\n\n"
                        details += f"Descrição:\n{vuln['description']}\n\n"
                        details += f"Evidência:\n{vuln.get('evidence', 'N/A')}\n\n"
                        details += f"{'='*80}\n\n"
                        details += f"Requisição Original:\n"
                        details += f"ID: {entry['id']}\n"
                        details += f"Timestamp: {entry['timestamp']}\n"
                        details += f"Host: {entry['host']}\n"
                        details += f"Path: {entry['path']}\n"
                        details += f"Status: {entry['status']}\n"
                        
                        self.scanner_detail_text.insert('1.0', details)
                        return

    def _update_scanner_list(self):
        """Atualiza a lista de vulnerabilidades na UI"""
        # Only update if scanner tab is initialized
        if not hasattr(self, 'scanner_tree'):
            return
        
        # Limpa a árvore
        for item in self.scanner_tree.get_children():
            self.scanner_tree.delete(item)

        severity_filter = self.scanner_severity_var.get()
        type_filter = self.scanner_type_var.get()
        
        vuln_count = 0
        
        # Coleta todas as vulnerabilidades do histórico
        for entry in self.history.get_history():
            if entry.get('vulnerabilities'):
                for i, vuln in enumerate(entry['vulnerabilities'], 1):
                    # Aplica filtros
                    if severity_filter != "Todas" and vuln['severity'] != severity_filter:
                        continue
                    if type_filter != "Todos" and vuln['type'] != type_filter:
                        continue
                    
                    vuln_count += 1
                    unique_id = f"{entry['id']}-{i}"
                    
                    # Define cor baseada na severidade
                    tag = ""
                    if vuln['severity'] == 'Critical':
                        tag = "critical"
                    elif vuln['severity'] == 'High':
                        tag = "high"
                    elif vuln['severity'] == 'Medium':
                        tag = "medium"
                    else:
                        tag = "low"
                    
                    # Trunca a URL se for muito longa
                    url = vuln.get('url', 'N/A')
                    if len(url) > 60:
                        url = url[:57] + "..."
                    
                    self.scanner_tree.insert("", "end", 
                                           values=(unique_id, vuln['severity'], vuln['type'], 
                                                  url, vuln.get('method', 'N/A')),
                                           tags=(tag,))
        
        # Configura cores para as tags
        self.scanner_tree.tag_configure("critical", foreground="red", font=('TkDefaultFont', 9, 'bold'))
        self.scanner_tree.tag_configure("high", foreground="orange", font=('TkDefaultFont', 9, 'bold'))
        self.scanner_tree.tag_configure("medium", foreground="#DAA520")
        self.scanner_tree.tag_configure("low", foreground="gray")
        
        # Atualiza contador
        self.scanner_count_label.config(text=f"Total: {vuln_count} vulnerabilidade(s)")

    def run_active_scan(self):
        """Executa scan ativo na requisição selecionada do histórico"""
        # Verifica se há uma requisição selecionada no histórico
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma requisição no Histórico para escanear.")
            return
        # Obtém a entrada selecionada do mapa (o TreeView não guarda o ID como coluna)
        item_id = selection[0]
        entry = self.history_map.get(item_id)
        request_id = None
        if not entry:
            messagebox.showerror("Erro", "Requisição não encontrada no histórico.")
            return
        else:
            request_id = entry.get('id')
        
        # Atualiza status
        self.active_scan_status.config(text="Escaneando...", foreground="orange")
        self.root.update()
        
        try:
            # Prepara os dados da requisição para o scanner ativo
            request_data = {
                'method': entry['method'],
                'url': entry['url'],
                'headers': entry['request_headers'],
                'body': entry['request_body'],
            }
            
            # Executa o scan ativo
            log.info(f"Iniciando scan ativo em {entry['method']} {entry['url']}")
            vulnerabilities = self.active_scanner.scan_request(request_data)
            
            if vulnerabilities:
                # Adiciona as vulnerabilidades à entrada do histórico
                self.history.add_vulnerabilities_to_entry(request_id, vulnerabilities)
                
                # Atualiza a lista de vulnerabilidades
                self._update_scanner_list()
                
                # Atualiza status
                self.active_scan_status.config(
                    text=f"✓ {len(vulnerabilities)} vulnerabilidade(s) encontrada(s)", 
                    foreground="green"
                )
                
                messagebox.showinfo(
                    "Scan Ativo Concluído", 
                    f"Scan ativo concluído!\n\n{len(vulnerabilities)} vulnerabilidade(s) encontrada(s)."
                )
            else:
                self.active_scan_status.config(text="✓ Nenhuma vulnerabilidade encontrada", foreground="gray")
                messagebox.showinfo("Scan Ativo Concluído", "Scan ativo concluído!\n\nNenhuma vulnerabilidade encontrada.")
            
            log.info(f"Scan ativo concluído: {len(vulnerabilities)} vulnerabilidades encontradas")
            
        except Exception as e:
            self.active_scan_status.config(text="✗ Erro no scan", foreground="red")
            messagebox.showerror("Erro no Scan Ativo", f"Erro ao executar scan ativo:\n{str(e)}")
            log.error(f"Erro no scan ativo: {e}")

    def setup_spider_tab(self):
        """Configura a aba do Spider/Crawler"""
        spider_tab = ttk.Frame(self.notebook)
        self.notebook.add(spider_tab, text="🕷️ Spider/Crawler")
        
        # Frame de controle
        control_frame = ttk.LabelFrame(spider_tab, text="Controle do Spider", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Status do Spider
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill="x", pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side="left", padx=5)
        self.spider_status_label = ttk.Label(status_frame, text="Parado", foreground="red")
        self.spider_status_label.pack(side="left", padx=5)
        
        # Botões de controle
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        self.spider_start_button = ttk.Button(buttons_frame, text="▶ Iniciar Spider", 
                                              command=self.start_spider)
        self.spider_start_button.pack(side="left", padx=5)
        
        self.spider_stop_button = ttk.Button(buttons_frame, text="⏹ Parar Spider", 
                                             command=self.stop_spider, state="disabled")
        self.spider_stop_button.pack(side="left", padx=5)
        
        self.spider_clear_button = ttk.Button(buttons_frame, text="🗑 Limpar Dados", 
                                              command=self.clear_spider)
        self.spider_clear_button.pack(side="left", padx=5)
        
        # Configurações do Spider
        config_frame = ttk.LabelFrame(spider_tab, text="Configurações", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # URL inicial
        ttk.Label(config_frame, text="URL Inicial (escopo):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.spider_url_entry = ttk.Entry(config_frame, width=50)
        self.spider_url_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.spider_url_entry.insert(0, "http://example.com")
        
        # Profundidade máxima
        ttk.Label(config_frame, text="Profundidade Máxima:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.spider_depth_entry = ttk.Entry(config_frame, width=10)
        self.spider_depth_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.spider_depth_entry.insert(0, "3")
        
        # Máximo de URLs
        ttk.Label(config_frame, text="Máximo de URLs:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.spider_max_urls_entry = ttk.Entry(config_frame, width=10)
        self.spider_max_urls_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.spider_max_urls_entry.insert(0, "1000")
        
        config_frame.columnconfigure(1, weight=1)
        
        # Tooltips
        Tooltip(self.spider_url_entry, "URL base para iniciar o crawling (define o escopo)")
        Tooltip(self.spider_depth_entry, "Número máximo de níveis de links a seguir")
        Tooltip(self.spider_max_urls_entry, "Número máximo de URLs a descobrir")
        
        # Estatísticas
        stats_frame = ttk.LabelFrame(spider_tab, text="Estatísticas", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.spider_stats_label = ttk.Label(stats_frame, 
                                           text="URLs Descobertas: 0 | Na Fila: 0 | Visitadas: 0 | Formulários: 0",
                                           font=('TkDefaultFont', 9))
        self.spider_stats_label.pack(pady=5)
        
        # Notebook para resultados
        results_notebook = ttk.Notebook(spider_tab)
        results_notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tab 1: URLs Descobertas
        urls_frame = ttk.Frame(results_notebook)
        results_notebook.add(urls_frame, text="URLs Descobertas")
        
        # Barra de ferramentas para URLs
        urls_toolbar = ttk.Frame(urls_frame)
        urls_toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(urls_toolbar, text="↻ Atualizar", command=self.refresh_spider_urls).pack(side="left", padx=5)
        ttk.Button(urls_toolbar, text="📋 Copiar Todas", command=self.copy_all_spider_urls).pack(side="left", padx=5)
        
        # Lista de URLs
        urls_list_frame = ttk.Frame(urls_frame)
        urls_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        urls_scrollbar_y = ttk.Scrollbar(urls_list_frame, orient="vertical")
        urls_scrollbar_y.pack(side="right", fill="y")
        
        urls_scrollbar_x = ttk.Scrollbar(urls_list_frame, orient="horizontal")
        urls_scrollbar_x.pack(side="bottom", fill="x")
        
        self.spider_urls_listbox = tk.Listbox(urls_list_frame, 
                                               yscrollcommand=urls_scrollbar_y.set,
                                               xscrollcommand=urls_scrollbar_x.set,
                                               font=('Courier', 9))
        self.spider_urls_listbox.pack(side="left", fill="both", expand=True)
        
        urls_scrollbar_y.config(command=self.spider_urls_listbox.yview)
        urls_scrollbar_x.config(command=self.spider_urls_listbox.xview)
        
        # Tab 2: Formulários
        forms_frame = ttk.Frame(results_notebook)
        results_notebook.add(forms_frame, text="Formulários")
        
        forms_toolbar = ttk.Frame(forms_frame)
        forms_toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(forms_toolbar, text="↻ Atualizar", command=self.refresh_spider_forms).pack(side="left", padx=5)
        
        # Treeview para formulários
        forms_tree_frame = ttk.Frame(forms_frame)
        forms_tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        forms_scrollbar = ttk.Scrollbar(forms_tree_frame)
        forms_scrollbar.pack(side="right", fill="y")
        
        self.spider_forms_tree = ttk.Treeview(forms_tree_frame, 
                                              columns=("method", "url", "inputs"),
                                              show="headings",
                                              yscrollcommand=forms_scrollbar.set)
        
        self.spider_forms_tree.heading("method", text="Método")
        self.spider_forms_tree.heading("url", text="URL do Formulário")
        self.spider_forms_tree.heading("inputs", text="Campos")
        
        self.spider_forms_tree.column("method", width=80)
        self.spider_forms_tree.column("url", width=400)
        self.spider_forms_tree.column("inputs", width=200)
        
        self.spider_forms_tree.pack(side="left", fill="both", expand=True)
        forms_scrollbar.config(command=self.spider_forms_tree.yview)
        
        # Tab 3: Sitemap
        sitemap_frame = ttk.Frame(results_notebook)
        results_notebook.add(sitemap_frame, text="Sitemap")
        
        sitemap_toolbar = ttk.Frame(sitemap_frame)
        sitemap_toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(sitemap_toolbar, text="↻ Atualizar", command=self.refresh_spider_sitemap).pack(side="left", padx=5)
        ttk.Button(sitemap_toolbar, text="💾 Exportar", command=self.export_spider_sitemap).pack(side="left", padx=5)
        
        # Área de texto para sitemap
        sitemap_text_frame = ttk.Frame(sitemap_frame)
        sitemap_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        sitemap_scrollbar = ttk.Scrollbar(sitemap_text_frame)
        sitemap_scrollbar.pack(side="right", fill="y")
        
        self.spider_sitemap_text = scrolledtext.ScrolledText(sitemap_text_frame, 
                                                             wrap="none",
                                                             font=('Courier', 9),
                                                             yscrollcommand=sitemap_scrollbar.set)
        self.spider_sitemap_text.pack(side="left", fill="both", expand=True)
        sitemap_scrollbar.config(command=self.spider_sitemap_text.yview)

    def start_spider(self):
        """Inicia o Spider"""
        if not self.proxy_running:
            messagebox.showwarning("Aviso", "Inicie o proxy primeiro!")
            return
        
        if self.spider.is_running():
            messagebox.showwarning("Aviso", "Spider já está em execução!")
            return
        
        # Obtém configurações
        url = self.spider_url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Digite uma URL inicial!")
            return
        
        try:
            max_depth = int(self.spider_depth_entry.get())
            max_urls = int(self.spider_max_urls_entry.get())
        except ValueError:
            messagebox.showerror("Erro", "Valores numéricos inválidos!")
            return
        
        # Inicia o spider
        self.spider.start(target_urls=[url], max_depth=max_depth, max_urls=max_urls)
        
        # Atualiza UI
        self.spider_status_label.config(text="Em Execução", foreground="green")
        self.spider_start_button.config(state="disabled")
        self.spider_stop_button.config(state="normal")
        
        log.info(f"Spider iniciado com URL: {url}")
        messagebox.showinfo("Spider", f"Spider iniciado!\nURL: {url}\nNavegue no site para descobrir páginas.")
    
    def stop_spider(self):
        """Para o Spider"""
        self.spider.stop()
        
        # Atualiza UI
        self.spider_status_label.config(text="Parado", foreground="red")
        self.spider_start_button.config(state="normal")
        self.spider_stop_button.config(state="disabled")
        
        log.info("Spider parado")
        messagebox.showinfo("Spider", "Spider parado!")
    
    def clear_spider(self):
        """Limpa os dados do Spider"""
        if messagebox.askyesno("Confirmar", "Deseja limpar todos os dados do Spider?"):
            self.spider.clear()
            
            # Limpa UI
            self.spider_urls_listbox.delete(0, tk.END)
            
            for item in self.spider_forms_tree.get_children():
                self.spider_forms_tree.delete(item)
            
            self.spider_sitemap_text.delete('1.0', tk.END)
            
            self.spider_status_label.config(text="Parado", foreground="red")
            self.spider_start_button.config(state="normal")
            self.spider_stop_button.config(state="disabled")
            
            log.info("Dados do Spider limpos")
    
    def update_spider_stats(self):
        """Atualiza as estatísticas do Spider periodicamente"""
        # Only update if spider tab is initialized
        if 9 not in self.initialized_tabs:
            self.root.after(2000, self.update_spider_stats)
            return
        
        if hasattr(self, 'spider_stats_label'):
            # Run in background thread to avoid blocking UI
            def update_in_background():
                try:
                    stats = self.spider.get_stats()
                    # Schedule UI update on main thread
                    self.root.after(0, lambda: self.spider_stats_label.config(
                        text=f"URLs Descobertas: {stats['discovered_urls']} | "
                             f"Na Fila: {stats['queue_size']} | "
                             f"Visitadas: {stats['visited']} | "
                             f"Formulários: {stats['forms_found']}"
                    ))
                except Exception as e:
                    log.error(f"Error updating spider stats: {e}")
            
            thread = threading.Thread(target=update_in_background, daemon=True)
            thread.start()
        
        # Reagenda para 2 segundos depois
        self.root.after(2000, self.update_spider_stats)
    
    def refresh_spider_urls(self):
        """Atualiza a lista de URLs descobertas"""
        self.spider_urls_listbox.delete(0, tk.END)
        
        urls = self.spider.get_discovered_urls()
        for url in urls:
            self.spider_urls_listbox.insert(tk.END, url)
        
        log.info(f"Lista de URLs atualizada: {len(urls)} URLs")
    
    def copy_all_spider_urls(self):
        """Copia todas as URLs para a área de transferência"""
        urls = self.spider.get_discovered_urls()
        if urls:
            urls_text = "\n".join(urls)
            self.root.clipboard_clear()
            self.root.clipboard_append(urls_text)
            messagebox.showinfo("Copiado", f"{len(urls)} URLs copiadas para a área de transferência!")
        else:
            messagebox.showwarning("Aviso", "Nenhuma URL descoberta ainda!")
    
    def refresh_spider_forms(self):
        """Atualiza a lista de formulários"""
        # Limpa árvore
        for item in self.spider_forms_tree.get_children():
            self.spider_forms_tree.delete(item)
        
        # Adiciona formulários
        forms = self.spider.get_forms()
        for form in forms:
            inputs_str = ", ".join([f"{inp['name']}({inp['type']})" for inp in form['inputs'] if inp['name']])
            self.spider_forms_tree.insert("", "end", 
                                         values=(form['method'], form['url'], inputs_str))
        
        log.info(f"Lista de formulários atualizada: {len(forms)} formulários")
    
    def refresh_spider_sitemap(self):
        """Atualiza o sitemap"""
        self.spider_sitemap_text.delete('1.0', tk.END)
        sitemap_text = self.spider.export_sitemap_text()
        self.spider_sitemap_text.insert('1.0', sitemap_text)
        
        log.info("Sitemap atualizado")
    
    def export_spider_sitemap(self):
        """Exporta o sitemap para arquivo"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                sitemap_text = self.spider.export_sitemap_text()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(sitemap_text)
                messagebox.showinfo("Sucesso", f"Sitemap exportado para:\n{filename}")
                log.info(f"Sitemap exportado para: {filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar sitemap:\n{str(e)}")
                log.error(f"Erro ao exportar sitemap: {e}")

    def setup_websocket_tab(self):
        """Configura a aba de WebSocket"""
        websocket_tab = ttk.Frame(self.notebook)
        self.notebook.add(websocket_tab, text="WebSocket 🔌")

        # Frame superior - Lista de Conexões
        connections_frame = ttk.LabelFrame(websocket_tab, text="Conexões WebSocket", padding=10)
        connections_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview para listar conexões WebSocket
        columns = ('ID', 'Host', 'URL', 'Status', 'Mensagens', 'Início')
        self.ws_connections_tree = ttk.Treeview(connections_frame, columns=columns, show='headings', height=8)
        
        self.ws_connections_tree.heading('ID', text='ID')
        self.ws_connections_tree.heading('Host', text='Host')
        self.ws_connections_tree.heading('URL', text='URL')
        self.ws_connections_tree.heading('Status', text='Status')
        self.ws_connections_tree.heading('Mensagens', text='Mensagens')
        self.ws_connections_tree.heading('Início', text='Início')
        
        self.ws_connections_tree.column('ID', width=50)
        self.ws_connections_tree.column('Host', width=150)
        self.ws_connections_tree.column('URL', width=300)
        self.ws_connections_tree.column('Status', width=80)
        self.ws_connections_tree.column('Mensagens', width=100)
        self.ws_connections_tree.column('Início', width=150)
        
        self.ws_connections_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para conexões
        scrollbar_conn = ttk.Scrollbar(connections_frame, orient="vertical", command=self.ws_connections_tree.yview)
        scrollbar_conn.pack(side="right", fill="y")
        self.ws_connections_tree.configure(yscrollcommand=scrollbar_conn.set)
        
        # Bind para seleção de conexão
        self.ws_connections_tree.bind('<<TreeviewSelect>>', self.on_ws_connection_select)

        # Frame de mensagens
        messages_frame = ttk.LabelFrame(websocket_tab, text="Mensagens", padding=10)
        messages_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview para listar mensagens
        msg_columns = ('Timestamp', 'Direção', 'Tamanho', 'Tipo')
        self.ws_messages_tree = ttk.Treeview(messages_frame, columns=msg_columns, show='headings', height=8)
        
        self.ws_messages_tree.heading('Timestamp', text='Timestamp')
        self.ws_messages_tree.heading('Direção', text='Direção')
        self.ws_messages_tree.heading('Tamanho', text='Tamanho')
        self.ws_messages_tree.heading('Tipo', text='Tipo')
        
        self.ws_messages_tree.column('Timestamp', width=150)
        self.ws_messages_tree.column('Direção', width=150)
        self.ws_messages_tree.column('Tamanho', width=100)
        self.ws_messages_tree.column('Tipo', width=100)
        
        self.ws_messages_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para mensagens
        scrollbar_msg = ttk.Scrollbar(messages_frame, orient="vertical", command=self.ws_messages_tree.yview)
        scrollbar_msg.pack(side="right", fill="y")
        self.ws_messages_tree.configure(yscrollcommand=scrollbar_msg.set)
        
        # Bind para seleção de mensagem
        self.ws_messages_tree.bind('<<TreeviewSelect>>', self.on_ws_message_select)

        # Frame de detalhes da mensagem
        details_frame = ttk.LabelFrame(websocket_tab, text="Conteúdo da Mensagem", padding=10)
        details_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.ws_message_text = scrolledtext.ScrolledText(details_frame, height=10, wrap=tk.WORD)
        self.ws_message_text.pack(fill="both", expand=True)

        # Frame de botões
        buttons_frame = ttk.Frame(websocket_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(buttons_frame, text="Atualizar Lista", command=self.refresh_websocket_list).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Limpar Histórico", command=self.clear_websocket_history).pack(side="left", padx=5)
        
        # Botão de reenviar mensagem (placeholder para implementação futura)
        self.ws_resend_button = ttk.Button(buttons_frame, text="Reenviar Mensagem", command=self.resend_websocket_message, state="disabled")
        self.ws_resend_button.pack(side="left", padx=5)

    def update_websocket_list(self):
        """Atualiza periodicamente a lista de conexões WebSocket"""
        # Only update if websocket tab is initialized
        if 10 not in self.initialized_tabs:
            self.root.after(2000, self.update_websocket_list)
            return
        
        # Run in background thread to avoid blocking UI
        def update_in_background():
            try:
                # Get connections from history
                connections = self.websocket_history.get_connections()
                
                # Schedule UI update on main thread
                def update_ui():
                    try:
                        # Double check tree exists (in case tab was closed)
                        if not hasattr(self, 'ws_connections_tree'):
                            return
                        
                        # Limpa árvore de conexões
                        for item in self.ws_connections_tree.get_children():
                            self.ws_connections_tree.delete(item)
                        
                        # Adiciona novas conexões
                        for conn in connections:
                            flow_id = conn['flow_id']
                            
                            # Formata timestamp
                            start_time = conn['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Adiciona à árvore
                            item_id = self.ws_connections_tree.insert("", "end", 
                                values=(
                                    conn['id'],
                                    conn['host'],
                                    conn['url'],
                                    conn['status'],
                                    conn['message_count'],
                                    start_time
                                ))
                            
                            # Mapeia item_id para flow_id
                            self.ws_connections_map[item_id] = flow_id
                    except Exception as e:
                        log.error(f"Erro ao atualizar UI WebSocket: {e}")
                
                self.root.after(0, update_ui)
            
            except Exception as e:
                log.error(f"Erro ao atualizar lista de WebSocket: {e}")
        
        thread = threading.Thread(target=update_in_background, daemon=True)
        thread.start()
        
        # Reagenda para 2 segundos depois
        self.root.after(2000, self.update_websocket_list)

    def on_ws_connection_select(self, event):
        """Chamado quando uma conexão WebSocket é selecionada"""
        selection = self.ws_connections_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        flow_id = self.ws_connections_map.get(item_id)
        
        if flow_id:
            self.selected_ws_connection = flow_id
            self.refresh_ws_messages()

    def refresh_ws_messages(self):
        """Atualiza a lista de mensagens da conexão selecionada"""
        # Limpa árvore de mensagens
        for item in self.ws_messages_tree.get_children():
            self.ws_messages_tree.delete(item)
        
        # Limpa conteúdo
        self.ws_message_text.delete('1.0', tk.END)
        
        if not self.selected_ws_connection:
            return
        
        messages = self.websocket_history.get_messages(self.selected_ws_connection)
        for msg in messages:
            timestamp = msg['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            direction = "Cliente → Servidor" if msg['from_client'] else "Servidor → Cliente"
            msg_type = "Binário" if msg['is_binary'] else "Texto"
            size = f"{msg['size']} bytes"
            
            self.ws_messages_tree.insert("", "end", 
                values=(timestamp, direction, size, msg_type),
                tags=(msg,))

    def on_ws_message_select(self, event):
        """Chamado quando uma mensagem WebSocket é selecionada"""
        selection = self.ws_messages_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item = self.ws_messages_tree.item(item_id)
        
        # Pega a mensagem dos valores
        if not self.selected_ws_connection:
            return
        
        messages = self.websocket_history.get_messages(self.selected_ws_connection)
        
        # Encontra o índice da mensagem selecionada
        children = self.ws_messages_tree.get_children()
        msg_index = children.index(item_id)
        
        if msg_index < len(messages):
            msg = messages[msg_index]
            
            # Mostra o conteúdo
            self.ws_message_text.delete('1.0', tk.END)
            
            if msg['is_binary']:
                # Mostra representação hexadecimal para mensagens binárias
                self.ws_message_text.insert('1.0', f"Mensagem Binária ({msg['size']} bytes):\n\n{msg['content']}")
            else:
                self.ws_message_text.insert('1.0', msg['content'])

    def refresh_websocket_list(self):
        """Força atualização da lista de WebSocket"""
        # Limpa árvore de conexões
        for item in self.ws_connections_tree.get_children():
            self.ws_connections_tree.delete(item)
        
        # Adiciona novas conexões
        connections = self.websocket_history.get_connections()
        for conn in connections:
            flow_id = conn['flow_id']
            
            # Formata timestamp
            start_time = conn['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Adiciona à árvore
            item_id = self.ws_connections_tree.insert("", "end", 
                values=(
                    conn['id'],
                    conn['host'],
                    conn['url'],
                    conn['status'],
                    conn['message_count'],
                    start_time
                ))
            
            # Mapeia item_id para flow_id
            self.ws_connections_map[item_id] = flow_id
        
        # Atualiza mensagens se houver conexão selecionada
        if self.selected_ws_connection:
            self.refresh_ws_messages()
        
        messagebox.showinfo("Atualizado", "Lista de WebSocket atualizada!")

    def clear_websocket_history(self):
        """Limpa o histórico de WebSocket"""
        confirm = messagebox.askyesno("Confirmar", "Deseja limpar todo o histórico de WebSocket?")
        if confirm:
            self.websocket_history.clear_history()
            self.ws_connections_map = {}
            self.selected_ws_connection = None
            
            # Limpa árvores
            for item in self.ws_connections_tree.get_children():
                self.ws_connections_tree.delete(item)
            for item in self.ws_messages_tree.get_children():
                self.ws_messages_tree.delete(item)
            
            # Limpa conteúdo
            self.ws_message_text.delete('1.0', tk.END)
            
            messagebox.showinfo("Limpo", "Histórico de WebSocket limpo!")

    def resend_websocket_message(self):
        """Reenvia uma mensagem WebSocket (funcionalidade futura)"""
        messagebox.showinfo("Em Desenvolvimento", 
                          "A funcionalidade de reenvio de mensagens WebSocket\n"
                          "será implementada em uma versão futura.")

    def on_browser_install_start(self):
        """Callback para quando a instalação do navegador começa."""
        self.browser_button.config(state="disabled", text="Instalando Navegador...")
        self.root.update_idletasks()

    def on_browser_install_finish(self):
        """Callback para quando a instalação do navegador termina."""
        self.browser_button.config(state="normal", text="Abrir Navegador")
        messagebox.showinfo("Sucesso", "Navegador instalado! Você já pode abri-lo.")

    def on_closing(self):
        """Handler para o fechamento da janela."""
        log.info("Fechando aplicação...")
        if self.proxy_running:
            self.stop_proxy()
        self.browser_manager.close()
        self.root.destroy()

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()
