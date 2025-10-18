import asyncio
import queue
import sys
import threading

from PySide6.QtCore import Signal, QAbstractTableModel, Qt, QTimer
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QGroupBox, QMessageBox, QTabWidget,
                               QTableView, QAbstractItemView, QGridLayout, QHeaderView)

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster

from src.core.addon import InterceptAddon
from src.core.config import InterceptConfig
from src.core.history import RequestHistory
from src.core.cookie_manager import CookieManager
from src.core.spider import Spider
from src.core.websocket_history import WebSocketHistory
from src.core.active_scanner import ActiveScanner
from src.core.browser_manager import BrowserManager
from src.core.logger_config import log

class ProxyGUI(QMainWindow):
    """Interface gráfica em PySide6 para o proxy interceptador."""

    proxy_stopped_signal = Signal()
    ui_update_signal = Signal(dict)

    def __init__(self):
        super().__init__()

        self.proxy_stopped_signal.connect(self._set_proxy_stopped_state)
        self.ui_update_signal.connect(self._handle_ui_update)

        # Inicializa a lógica de negócio (backend)
        self.config = InterceptConfig()
        self.history = RequestHistory()
        self.cookie_manager = CookieManager()
        self.spider = Spider()
        self.websocket_history = WebSocketHistory()
        self.active_scanner = ActiveScanner()
        self.browser_manager = BrowserManager(proxy_port=self.config.get_port())

        # Estado da aplicação
        self.proxy_thread = None
        self.proxy_running = False
        self.proxy_master = None
        self.proxy_loop = None
        self.ui_queue = queue.Queue()

        self.setWindowTitle("InterceptProxy - PySide6")
        self.setGeometry(100, 100, 1200, 800)

        # Configura o widget central e o layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.update_ui_state()
        self._refresh_rules_list()

        # Inicia o timer para processar a fila de eventos da UI
        self.ui_queue_timer = QTimer()
        self.ui_queue_timer.timeout.connect(self._process_ui_queue)
        self.ui_queue_timer.start(100) # Verifica a cada 100ms

    def setup_ui(self):
        """Configura os elementos da UI."""
        # 1. Grupo de Controle do Proxy
        self._setup_proxy_controls()

        # 2. Notebook com as abas
        self._setup_tabs()

    def _setup_tabs(self):
        """Cria o sistema de abas."""
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Aba de Regras
        self._setup_rules_tab()

    def _setup_rules_tab(self):
        """Cria a aba de Regras de Interceptação."""
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)

        # --- Formulário de Adicionar Regra ---
        add_rule_group = QGroupBox("Adicionar Regra de Interceptação")
        add_rule_layout = QGridLayout()

        # Linha 1
        add_rule_layout.addWidget(QLabel("Host/Domínio:"), 0, 0)
        self.host_entry = QLineEdit("exemplo.com")
        add_rule_layout.addWidget(self.host_entry, 0, 1)

        add_rule_layout.addWidget(QLabel("Caminho:"), 0, 2)
        self.path_entry = QLineEdit("/contato")
        add_rule_layout.addWidget(self.path_entry, 0, 3)

        # Linha 2
        add_rule_layout.addWidget(QLabel("Nome do Parâmetro:"), 1, 0)
        self.param_name_entry = QLineEdit("Titulo")
        add_rule_layout.addWidget(self.param_name_entry, 1, 1)

        add_rule_layout.addWidget(QLabel("Novo Valor:"), 1, 2)
        self.param_value_entry = QLineEdit("teste1")
        add_rule_layout.addWidget(self.param_value_entry, 1, 3)

        # Botão Adicionar
        add_button = QPushButton("Adicionar Regra")
        add_button.clicked.connect(self.add_rule)
        add_rule_layout.addWidget(add_button, 2, 0, 1, 4) # Ocupa 4 colunas

        add_rule_group.setLayout(add_rule_layout)
        rules_layout.addWidget(add_rule_group)

        # --- Lista de Regras ---
        rules_list_group = QGroupBox("Regras Configuradas")
        rules_list_layout = QVBoxLayout()

        self.rules_table = QTableView()
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.rules_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.rules_model = RulesTableModel(self.config.get_rules())
        self.rules_table.setModel(self.rules_model)
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        rules_list_layout.addWidget(self.rules_table)
        rules_list_group.setLayout(rules_list_layout)
        rules_layout.addWidget(rules_list_group)

        # --- Botões de Ação ---
        action_buttons_layout = QHBoxLayout()
        remove_button = QPushButton("Remover Regra Selecionada")
        remove_button.clicked.connect(self.remove_rule)
        action_buttons_layout.addWidget(remove_button)

        toggle_button = QPushButton("Ativar/Desativar Regra")
        toggle_button.clicked.connect(self.toggle_rule)
        action_buttons_layout.addWidget(toggle_button)

        duplicate_button = QPushButton("Duplicar Regra")
        duplicate_button.clicked.connect(self.duplicate_rule)
        action_buttons_layout.addWidget(duplicate_button)

        action_buttons_layout.addStretch()
        rules_layout.addLayout(action_buttons_layout)

        self.tab_widget.addTab(rules_tab, "Regras de Interceptação")

    def _setup_proxy_controls(self):
        """Cria o painel de controle do proxy."""
        control_group = QGroupBox("Controle do Proxy")
        control_layout = QHBoxLayout()

        # Status
        self.status_label = QLabel("Status: Parado")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.status_label)

        # Botões
        self.start_button = QPushButton("Iniciar Proxy")
        self.start_button.clicked.connect(self.start_proxy)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Parar Proxy")
        self.stop_button.clicked.connect(self.stop_proxy)
        control_layout.addWidget(self.stop_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.toggle_pause_proxy)
        control_layout.addWidget(self.pause_button)

        # Porta
        control_layout.addSpacing(20)
        control_layout.addWidget(QLabel("Porta:"))
        self.port_entry = QLineEdit(str(self.config.get_port()))
        self.port_entry.setFixedWidth(60)
        control_layout.addWidget(self.port_entry)

        self.port_save_button = QPushButton("Salvar Porta")
        self.port_save_button.clicked.connect(self.save_port)
        control_layout.addWidget(self.port_save_button)

        # Navegador
        control_layout.addSpacing(20)
        self.browser_button = QPushButton("Abrir Navegador")
        self.browser_button.clicked.connect(self.launch_browser)
        control_layout.addWidget(self.browser_button)

        control_layout.addStretch() # Empurra tudo para a esquerda
        control_group.setLayout(control_layout)
        self.main_layout.addWidget(control_group)

    def start_proxy(self):
        """Inicia o servidor proxy em uma thread separada."""
        if self.proxy_running:
            QMessageBox.warning(self, "Aviso", "Proxy já está em execução!")
            return

        log.info("Proxy (PySide6) iniciando...")

        def run_proxy():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def runner():
                try:
                    port = self.config.get_port()
                    proxy_options = options.Options(listen_host='127.0.0.1', listen_port=port)
                    master = DumpMaster(proxy_options, with_termlog=False, with_dumper=False)

                    addon = InterceptAddon(
                        self.config, self.history, self.cookie_manager,
                        self.spider, self.websocket_history, self.ui_queue
                    )
                    master.addons.add(addon)

                    self.proxy_master = master
                    self.proxy_loop = loop
                    await master.run()
                except Exception as err:
                    log.error(f"Falha ao iniciar o proxy (PySide6): {err}", exc_info=True)
                finally:
                    self.proxy_master = None
                    self.proxy_loop = None
                    # Emite o sinal para a thread principal atualizar a UI
                    self.proxy_stopped_signal.emit()

            loop.run_until_complete(runner())

        self.proxy_thread = threading.Thread(target=run_proxy, daemon=True)
        self.proxy_thread.start()
        self.proxy_running = True
        self.update_ui_state()

        QMessageBox.information(self, "Proxy Iniciado", f"Proxy iniciado na porta {self.config.get_port()}")

    def stop_proxy(self):
        """Para o servidor proxy."""
        if not self.proxy_running or not self.proxy_master:
            QMessageBox.information(self, "Proxy", "Proxy já está parado.")
            return

        log.info("Proxy (PySide6) finalizando...")
        if self.proxy_master and self.proxy_loop:
            self.proxy_loop.call_soon_threadsafe(self.proxy_master.shutdown)

        # A UI será atualizada quando a thread do proxy terminar e chamar _set_proxy_stopped_state

    def _set_proxy_stopped_state(self):
        """Atualiza a UI para o estado de proxy parado."""
        self.proxy_running = False
        self.update_ui_state()

    def toggle_pause_proxy(self):
        """Alterna o estado de pausa do proxy."""
        is_paused = self.config.toggle_pause()
        log.info(f"Proxy pausado: {is_paused}")
        self.update_ui_state()

    def save_port(self):
        """Salva a porta configurada."""
        port_str = self.port_entry.text().strip()
        success, message = self.config.set_port(port_str)
        if success:
            QMessageBox.information(self, "Sucesso", message)
        else:
            QMessageBox.warning(self, "Erro", message)
            self.port_entry.setText(str(self.config.get_port()))

    def launch_browser(self):
        """Abre o navegador pré-configurado."""
        log.info("PySide6 GUI: Abrindo o navegador...")
        QMessageBox.information(self, "Navegador", "Funcionalidade de abrir navegador a ser implementada.")

    def update_ui_state(self):
        """Atualiza o estado dos widgets da UI."""
        # Estado dos botões de controle
        self.start_button.setEnabled(not self.proxy_running)
        self.stop_button.setEnabled(self.proxy_running)
        self.pause_button.setEnabled(self.proxy_running)
        self.browser_button.setEnabled(self.proxy_running)
        self.port_entry.setEnabled(not self.proxy_running)
        self.port_save_button.setEnabled(not self.proxy_running)

        # Status e texto do botão de pausa
        if self.proxy_running:
            if self.config.is_paused():
                self.status_label.setText("Status: Pausado")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")
                self.pause_button.setText("Continuar")
            else:
                self.status_label.setText("Status: Executando")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.pause_button.setText("Pausar")
        else:
            self.status_label.setText("Status: Parado")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.pause_button.setText("Pausar")

    def closeEvent(self, event):
        """Handler para o fechamento da janela."""
        log.info("PySide6 GUI: Fechando aplicação...")
        # Adicionar lógica para parar o proxy se estiver rodando
        if self.proxy_running:
            self.stop_proxy()
        event.accept()

    # --- Processamento de Eventos da UI ---
    def _process_ui_queue(self):
        """Verifica a fila de eventos e emite um sinal para a thread principal."""
        try:
            while not self.ui_queue.empty():
                message = self.ui_queue.get_nowait()
                self.ui_update_signal.emit(message)
        except queue.Empty:
            pass

    def _handle_ui_update(self, message):
        """Recebe o sinal e atualiza a UI na thread principal."""
        msg_type = message.get("type")
        data = message.get("data")

        if msg_type == "new_history_entry":
            # Futuramente, isso atualizará a aba de histórico.
            # Por enquanto, podemos usar para log ou debug.
            log.debug(f"Novo item de histórico recebido: {data['id']}")
        elif msg_type == "intercepted_request":
            # Lógica para exibir requisição interceptada
            pass
        elif msg_type == "update_spider_stats":
            # Lógica para atualizar estatísticas do spider
            pass
        elif msg_type == "update_websocket_list":
            # Lógica para atualizar lista de websockets
            pass

    # --- Lógica da Aba de Regras ---
    def add_rule(self):
        """Adiciona uma nova regra e atualiza a UI."""
        host = self.host_entry.text()
        path = self.path_entry.text()
        param_name = self.param_name_entry.text()
        param_value = self.param_value_entry.text()

        success, message = self.config.add_rule(host, path, param_name, param_value)
        if success:
            QMessageBox.information(self, "Sucesso", message)
            self._refresh_rules_list()
        else:
            QMessageBox.warning(self, "Erro de Validação", message)

    def remove_rule(self):
        """Remove a regra selecionada."""
        selected_indexes = self.rules_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma regra para remover.")
            return

        row_index = selected_indexes[0].row()
        if self.config.remove_rule(row_index):
            QMessageBox.information(self, "Sucesso", "Regra removida.")
            self._refresh_rules_list()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível remover a regra.")

    def toggle_rule(self):
        """Ativa ou desativa a regra selecionada."""
        selected_indexes = self.rules_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma regra para ativar/desativar.")
            return

        row_index = selected_indexes[0].row()
        if self.config.toggle_rule(row_index):
            self._refresh_rules_list()

    def duplicate_rule(self):
        """Duplica a regra selecionada."""
        selected_indexes = self.rules_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma regra para duplicar.")
            return

        row_index = selected_indexes[0].row()
        rule_to_duplicate = self.config.get_rules()[row_index]

        # Usa a lógica de adicionar para manter a validação
        success, _ = self.config.add_rule(
            rule_to_duplicate['host'],
            rule_to_duplicate['path'],
            rule_to_duplicate['param_name'],
            rule_to_duplicate['param_value']
        )
        if success:
            QMessageBox.information(self, "Sucesso", "Regra duplicada.")
            self._refresh_rules_list()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível duplicar a regra.")

    def _refresh_rules_list(self):
        """Atualiza a tabela de regras com os dados mais recentes."""
        self.rules_model.update_data(self.config.get_rules())

# --- Model para a Tabela de Regras ---
class RulesTableModel(QAbstractTableModel):
    """Modelo de dados para a QTableView que exibe as regras."""
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = ['Host', 'Caminho', 'Parâmetro', 'Valor', 'Status']

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            rule = self._data[index.row()]
            col = index.column()
            if col == 0:
                return rule.get('host', '')
            elif col == 1:
                return rule.get('path', '')
            elif col == 2:
                return rule.get('param_name', '')
            elif col == 3:
                return rule.get('param_value', '')
            elif col == 4:
                return "Ativo" if rule.get('enabled', True) else "Inativo"
        return None

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def update_data(self, new_data):
        """Atualiza os dados do modelo e notifica a view."""
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()
