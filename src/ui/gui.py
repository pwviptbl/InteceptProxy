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
from src.core.addon import InterceptAddon
from src.core.config import InterceptConfig
from src.core.cookie_manager import CookieManager
from src.core.history import RequestHistory
from src.core.logger_config import log
from .tooltip import Tooltip


class ProxyGUI:
    """Interface gráfica para configurar o proxy interceptador"""

    def __init__(self):
        self.config = InterceptConfig()
        self.history = RequestHistory()
        self.cookie_manager = CookieManager()
        self.cookie_manager.set_ui_callback(self._refresh_cookie_trees)
        self.proxy_thread = None
        self.proxy_running = False
        self.proxy_master = None
        self.proxy_loop = None
        self.history_map = {}
        self.last_history_id = 0
        self.repeater_request_data = None
        self.current_intercept_request = None
        self.intercept_response_text = None

        # Janela principal com tema
        self.root = ThemedTk(theme="arc")
        self.root.title("InteceptProxy - Configurador")
        self.root.geometry("1000x700")

        self.setup_ui()
        self.refresh_rules_list()

        # Atualiza o histórico periodicamente
        self.update_history_list()
        
        # Atualiza a fila de interceptação periodicamente
        self.check_intercept_queue()

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

        ttk.Label(control_frame, text="Porta: 8080").pack(side="left", padx=5)

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Configuração de Regras
        self.setup_rules_tab()

        # Tab 2: Intercept Manual
        self.setup_intercept_tab()

        # Tab 3: Histórico de Requisições
        self.setup_history_tab()

        # Tab 4: Repetição
        self.setup_repeater_tab()

        # Tab 5: Sender
        self.setup_sender_tab()

        # Tab 6: Decoder
        self.setup_decoder_tab()

        # Tab 7: Cookie Jar
        self.setup_cookie_jar_tab()

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

        info_text = """1. Configure o navegador para usar o proxy: localhost:8080
2. Adicione regras de interceptação com host, caminho, nome do parâmetro e valor
3. Inicie o proxy
4. Navegue normalmente - os parâmetros configurados serão substituídos automaticamente"""

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
                    proxy_options = options.Options(listen_host='127.0.0.1', listen_port=8080)
                    master = DumpMaster(proxy_options, with_termlog=False, with_dumper=False)
                    master.addons.add(InterceptAddon(self.config, self.history, self.cookie_manager))
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

    def update_history_list(self):
        """Atualiza a lista de histórico adicionando apenas novas entradas."""
        new_entries = self.history.get_new_entries(self.last_history_id)
        if new_entries:
            self._add_new_history_entries(new_entries)
        self.root.after(1000, self.update_history_list)

    def _add_new_history_entries(self, entries):
        """Adiciona novas entradas de histórico à tabela e atualiza o ID mais recente."""
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
            response = send_from_raw(raw_request, param_name if manual_value else None, manual_value)
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
            args=(raw_request, file_path, param_name, threads, self.update_sender_results),
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

        result = action_function(input_text)

        self.decoder_output_text.delete("1.0", tk.END)
        self.decoder_output_text.insert("1.0", result)

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
                   command=lambda: self._handle_decode_action(decoder.b64_encode)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Decode Base64",
                   command=lambda: self._handle_decode_action(decoder.b64_decode)).grid(row=0, column=1, padx=5, pady=5)

        # Botões de URL
        ttk.Button(buttons_frame, text="URL Encode",
                   command=lambda: self._handle_decode_action(decoder.url_encode)).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(buttons_frame, text="URL Decode",
                   command=lambda: self._handle_decode_action(decoder.url_decode)).grid(row=1, column=1, padx=5, pady=5)

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

        # Reseta UI
        self._reset_intercept_ui()
        log.info(f"Requisição enviada: {self.current_intercept_request['url']}")

    def drop_request(self):
        """Cancela a requisição interceptada."""
        if not self.current_intercept_request:
            return

        # Envia resposta para a fila
        response_data = {'action': 'drop'}
        self.config.add_intercept_response(response_data)

        # Reseta UI
        self._reset_intercept_ui()
        log.info(f"Requisição cancelada: {self.current_intercept_request['url']}")

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

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()
