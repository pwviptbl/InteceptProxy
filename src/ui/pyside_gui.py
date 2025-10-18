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
from src.ui.widgets.proxy_control_widget import ProxyControlWidget
from src.ui.tabs.rules_tab import RulesTab
from src.ui.tabs.intercept_tab import InterceptTab
from src.ui.tabs.history_tab import HistoryTab

class ProxyGUI(QMainWindow):
    """Interface gráfica em PySide6 para o proxy interceptador."""

    proxy_stopped_signal = Signal()
    ui_update_signal = Signal(dict)
    browser_install_start_signal = Signal()
    browser_install_finish_signal = Signal()

    def __init__(self):
        super().__init__()

        self.proxy_stopped_signal.connect(self._set_proxy_stopped_state)
        self.ui_update_signal.connect(self._handle_ui_update)
        self.browser_install_start_signal.connect(self._on_browser_install_start)
        self.browser_install_finish_signal.connect(self._on_browser_install_finish)

        # Inicializa a lógica de negócio (backend)
        self.config = InterceptConfig()
        self.history = RequestHistory()
        self.cookie_manager = CookieManager()
        self.spider = Spider()
        self.websocket_history = WebSocketHistory()
        self.active_scanner = ActiveScanner()
        self.browser_manager = BrowserManager(
            proxy_port=self.config.get_port(),
            on_install_start=self.browser_install_start_signal.emit,
            on_install_finish=self.browser_install_finish_signal.emit
        )

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

        # Inicia o timer para processar a fila de eventos da UI
        self.ui_queue_timer = QTimer()
        self.ui_queue_timer.timeout.connect(self._process_ui_queue)
        self.ui_queue_timer.start(100) # Verifica a cada 100ms

    def setup_ui(self):
        """Configura os elementos da UI."""
        # 1. Cria e adiciona o widget de controle do proxy
        self.control_widget = ProxyControlWidget(str(self.config.get_port()))
        self.main_layout.addWidget(self.control_widget)

        # Conecta os sinais do widget aos slots da janela principal
        self.control_widget.start_proxy_requested.connect(self.start_proxy)
        self.control_widget.stop_proxy_requested.connect(self.stop_proxy)
        self.control_widget.toggle_pause_requested.connect(self.toggle_pause_proxy)
        self.control_widget.save_port_requested.connect(self.save_port)
        self.control_widget.launch_browser_requested.connect(self.launch_browser)

        # 2. Notebook com as abas
        self._setup_tabs()

    def _setup_tabs(self):
        """Cria o sistema de abas."""
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Cria e adiciona a aba de regras
        rules_tab = RulesTab(self.config)
        self.tab_widget.addTab(rules_tab, "Regras de Interceptação")

        # Cria e adiciona a aba de interceptação
        self.intercept_tab = InterceptTab()
        self.intercept_tab.toggle_intercept_requested.connect(self.toggle_intercept)
        self.intercept_tab.forward_requested.connect(self.forward_request)
        self.intercept_tab.drop_requested.connect(self.drop_request)
        self.tab_widget.addTab(self.intercept_tab, "Intercept Manual")

        # Cria e adiciona a aba de histórico
        self.history_tab = HistoryTab(self.history)
        self.history_tab.send_to_repeater_requested.connect(self.send_to_repeater)
        self.history_tab.send_to_sender_requested.connect(self.send_to_sender)
        self.history_tab.clear_history_requested.connect(self._clear_history)
        self.tab_widget.addTab(self.history_tab, "Histórico de Requisições")

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

    def save_port(self, port_str: str):
        """Salva a porta configurada."""
        success, message = self.config.set_port(port_str)
        if success:
            QMessageBox.information(self, "Sucesso", message)
        else:
            QMessageBox.warning(self, "Erro", message)
            self.control_widget.set_port_text(str(self.config.get_port()))

    def launch_browser(self):
        """Abre o navegador pré-configurado."""
        if not self.proxy_running:
            QMessageBox.warning(self, "Aviso", "O proxy precisa estar em execução para abrir o navegador.")
            return

        log.info("PySide6 GUI: Solicitando abertura do navegador...")
        self.browser_manager.launch_browser()

    def update_ui_state(self):
        """Atualiza o estado dos widgets da UI."""
        self.control_widget.set_proxy_running(self.proxy_running)
        if self.proxy_running:
            self.control_widget.set_proxy_paused(self.config.is_paused())

    def closeEvent(self, event):
        """Handler para o fechamento da janela."""
        log.info("PySide6 GUI: Fechando aplicação...")
        # Adicionar lógica para parar o proxy se estiver rodando
        if self.proxy_running:
            self.stop_proxy()
        event.accept()

    # --- Slots para Sinais do Navegador ---
    def _on_browser_install_start(self):
        """Atualiza a UI quando a instalação do navegador começa."""
        self.control_widget.set_browser_installing()

    def _on_browser_install_finish(self):
        """Atualiza a UI quando a instalação do navegador termina."""
        self.control_widget.set_browser_installed()
        QMessageBox.information(self, "Sucesso", "Navegador instalado! Você já pode abri-lo.")

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
            self.history_tab.add_history_entry(data)
        elif msg_type == "intercepted_request":
            self.intercept_tab.display_request(data)
            self.tab_widget.setCurrentWidget(self.intercept_tab)
        elif msg_type == "update_spider_stats":
            pass
        elif msg_type == "update_websocket_list":
            pass

    # --- Lógica da Aba de Interceptação ---
    def toggle_intercept(self):
        """Alterna o estado de interceptação manual."""
        if not self.proxy_running:
            QMessageBox.warning(self, "Aviso", "Inicie o proxy primeiro.")
            self.intercept_tab.set_intercept_state(False)
            return

        is_enabled = self.config.toggle_intercept()
        self.intercept_tab.set_intercept_state(is_enabled)
        log.info(f"Interceptação manual alterada para: {is_enabled}")

    def forward_request(self, modified_data: dict):
        """Envia a requisição interceptada (com possíveis modificações)."""
        response_data = {
            'action': 'forward',
            **modified_data
        }
        self.config.add_intercept_response(response_data)
        self.intercept_tab.reset_ui()
        log.info("Requisição interceptada enviada (forward).")

    def drop_request(self):
        """Cancela a requisição interceptada."""
        response_data = {'action': 'drop'}
        self.config.add_intercept_response(response_data)
        self.intercept_tab.reset_ui()
        log.info("Requisição interceptada cancelada (drop).")

    # --- Lógica da Aba de Histórico ---
    def send_to_repeater(self, entry: dict):
        """Envia uma requisição do histórico para a aba de repetição."""
        log.info(f"Enviando requisição {entry['id']} para o Repeater.")
        # Lógica para popular a aba Repeater será implementada futuramente
        QMessageBox.information(self, "Ação", f"Enviar requisição {entry['id']} para o Repeater (a implementar).")

    def send_to_sender(self, entry: dict):
        """Envia uma requisição do histórico para a aba de sender."""
        log.info(f"Enviando requisição {entry['id']} para o Sender.")
        # Lógica para popular a aba Sender será implementada futuramente
        QMessageBox.information(self, "Ação", f"Enviar requisição {entry['id']} para o Sender (a implementar).")

    def _clear_history(self):
        """Limpa o histórico de requisições."""
        self.history.clear_history()
        self.history_tab.clear_display()
        log.info("Histórico de requisições limpo.")
        QMessageBox.information(self, "Sucesso", "Histórico limpo com sucesso!")
