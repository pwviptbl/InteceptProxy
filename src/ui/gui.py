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

from src.core.addon import InterceptAddon
from src.core.config import InterceptConfig
from src.core.history import RequestHistory
from src.core.logger_config import log
from .tooltip import Tooltip


class ProxyGUI:
    """Interface gráfica para configurar o proxy interceptador"""

    def __init__(self):
        self.config = InterceptConfig()
        self.history = RequestHistory()
        self.proxy_thread = None
        self.proxy_running = False
        self.proxy_master = None
        self.proxy_loop = None
        self.history_map = {}
        self.last_history_id = 0
        self.repeater_request_data = None

        # Janela principal com tema
        self.root = ThemedTk(theme="arc")
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

        self.pause_button = ttk.Button(control_frame, text="Pausar", command=self.toggle_pause_proxy, state="disabled")
        self.pause_button.pack(side="left", padx=5)

        ttk.Label(control_frame, text="Porta: 8080").pack(side="left", padx=5)

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Configuração de Regras
        self.setup_rules_tab()

        # Tab 2: Histórico de Requisições
        self.setup_history_tab()

        # Tab 3: Repetição (Sender)
        self.setup_sender_tab()

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
                    master.addons.add(InterceptAddon(self.config, self.history))
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

    def setup_sender_tab(self):
        """Configura a aba de Repetição (Sender) com abas para Request e Response."""
        sender_tab = ttk.Frame(self.notebook)
        self.notebook.add(sender_tab, text="Repetição")

        # Frame superior para configuração
        config_frame = ttk.LabelFrame(sender_tab, text="Configuração do Reenvio", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Parâmetro a Substituir
        ttk.Label(config_frame, text="Parâmetro a Substituir:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.sender_param_entry = ttk.Entry(config_frame, width=30)
        self.sender_param_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        Tooltip(self.sender_param_entry, "Nome do parâmetro a ser substituído (na URL ou no Body).")

        # Novo Valor
        ttk.Label(config_frame, text="Novo Valor (Manual):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.sender_manual_value_entry = ttk.Entry(config_frame, width=30)
        self.sender_manual_value_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        Tooltip(self.sender_manual_value_entry, "Valor que substituirá o original. Deixe em branco para usar um arquivo.")

        # Arquivo de Lista
        ttk.Label(config_frame, text="Ou usar Arquivo (.txt):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sender_file_path = tk.StringVar()
        file_entry = ttk.Entry(config_frame, textvariable=self.sender_file_path, width=50, state="readonly")
        file_entry.grid(row=1, column=1, columnspan=2, sticky="we", padx=5, pady=5)
        file_button = ttk.Button(config_frame, text="Selecionar...", command=self.select_sender_file)
        file_button.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        Tooltip(file_button, "Use para envios em massa. Um valor por linha.")

        # Valor Manual
        ttk.Label(sender_frame, text="Valor Manual:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.sender_manual_value_entry = ttk.Entry(sender_frame, width=30)
        self.sender_manual_value_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        Tooltip(self.sender_manual_value_entry, "Um valor único para ser usado na substituição do parâmetro.")

        # Número de Threads
        ttk.Label(config_frame, text="Threads:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.sender_threads_spinbox = ttk.Spinbox(config_frame, from_=1, to=100, width=10)
        self.sender_threads_spinbox.set("10")
        self.sender_threads_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        Tooltip(self.sender_threads_spinbox, "Número de requisições simultâneas para envios em massa.")

        # Botão de Iniciar
        start_sender_button = ttk.Button(config_frame, text="Reenviar Requisição", command=self.start_sender)
        start_sender_button.grid(row=3, column=0, columnspan=4, pady=15)
        Tooltip(start_sender_button, "Inicia o processo de reenvio.")

        # PanedWindow para dividir Request e Response
        paned = ttk.PanedWindow(sender_tab, orient=tk.VERTICAL)
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

    def start_sender(self):
        """Inicia o processo de reenvio a partir da aba Repetição."""
        raw_request = self.repeater_request_text.get("1.0", tk.END).strip()
        if not raw_request:
            messagebox.showwarning("Aviso", "Não há nenhuma requisição para reenviar.")
            return

        param_name = self.sender_param_entry.get().strip()
        manual_value = self.sender_manual_value_entry.get().strip()
        file_path = self.sender_file_path.get().strip()

        # Limpa a aba de resposta
        self.repeater_response_text.delete('1.0', tk.END)

        # Lógica de reenvio
        if file_path:  # Envio em massa
            if not param_name:
                messagebox.showwarning("Aviso", "O 'Parâmetro a Substituir' é obrigatório para envios em massa.")
                return
            threads = int(self.sender_threads_spinbox.get())
            from src.core.sender import run_sender_from_file
            # Para envios em massa, não exibimos a resposta na aba, pois são muitas
            thread = threading.Thread(target=run_sender_from_file, args=(raw_request, file_path, param_name, threads, None), daemon=True)
            thread.start()
            messagebox.showinfo("Iniciado", "Envio em massa iniciado. Acompanhe os logs para detalhes.")

        else:  # Envio único (manual ou sem modificação)
            from src.core.sender import send_from_raw

            def sender_thread():
                # Se não houver valor manual, param_name é ignorado
                response = send_from_raw(raw_request, param_name if manual_value else None, manual_value)
                self.root.after(0, self._display_repeater_response, response)

            thread = threading.Thread(target=sender_thread, daemon=True)
            thread.start()

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

        # Exibe o menu na posição do cursor
        context_menu.tk_popup(event.x_root, event.y_root)

    def send_to_repeater(self, entry):
        """Copia todos os dados da requisição para a aba de Repetição e preenche a UI."""
        self.repeater_request_data = entry
        self.notebook.select(2)  # Muda para a aba de Repetição
        self._populate_repeater_request_tab()

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

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()
