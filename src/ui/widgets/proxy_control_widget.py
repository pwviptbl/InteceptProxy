from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QPushButton, QLabel, QLineEdit)

class ProxyControlWidget(QGroupBox):
    """Widget para o painel de controle do proxy."""

    # Sinais emitidos quando os botões são clicados
    start_proxy_requested = Signal()
    stop_proxy_requested = Signal()
    toggle_pause_requested = Signal()
    save_port_requested = Signal(str)
    launch_browser_requested = Signal()

    def __init__(self, initial_port: str):
        super().__init__("Controle do Proxy")

        control_layout = QHBoxLayout()

        # Status
        self.status_label = QLabel("Status: Parado")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.status_label)

        # Botões
        self.start_button = QPushButton("Iniciar Proxy")
        self.start_button.clicked.connect(self.start_proxy_requested.emit)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Parar Proxy")
        self.stop_button.clicked.connect(self.stop_proxy_requested.emit)
        control_layout.addWidget(self.stop_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.toggle_pause_requested.emit)
        control_layout.addWidget(self.pause_button)

        # Porta
        control_layout.addSpacing(20)
        control_layout.addWidget(QLabel("Porta:"))
        self.port_entry = QLineEdit(initial_port)
        self.port_entry.setFixedWidth(60)
        control_layout.addWidget(self.port_entry)

        self.port_save_button = QPushButton("Salvar Porta")
        self.port_save_button.clicked.connect(lambda: self.save_port_requested.emit(self.port_entry.text()))
        control_layout.addWidget(self.port_save_button)

        # Navegador
        control_layout.addSpacing(20)
        self.browser_button = QPushButton("Abrir Navegador")
        self.browser_button.clicked.connect(self.launch_browser_requested.emit)
        control_layout.addWidget(self.browser_button)

        control_layout.addStretch()
        self.setLayout(control_layout)

        # Estado inicial
        self.set_proxy_running(False)

    def set_proxy_running(self, is_running: bool):
        """Atualiza o estado dos widgets baseado no status do proxy."""
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.pause_button.setEnabled(is_running)
        self.browser_button.setEnabled(is_running)
        self.port_entry.setEnabled(not is_running)
        self.port_save_button.setEnabled(not is_running)

        if not is_running:
            self.status_label.setText("Status: Parado")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.pause_button.setText("Pausar")

    def set_proxy_paused(self, is_paused: bool):
        """Atualiza o status de pausa."""
        if is_paused:
            self.status_label.setText("Status: Pausado")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.pause_button.setText("Continuar")
        else:
            self.status_label.setText("Status: Executando")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.pause_button.setText("Pausar")

    def get_port_text(self) -> str:
        """Retorna o texto do campo da porta."""
        return self.port_entry.text().strip()

    def set_port_text(self, port_text: str):
        """Define o texto do campo da porta."""
        self.port_entry.setText(port_text)

    def set_browser_installing(self):
        """Atualiza a UI para o estado de instalação do navegador."""
        self.browser_button.setEnabled(False)
        self.browser_button.setText("Instalando Navegador...")

    def set_browser_installed(self):
        """Restaura a UI após a instalação do navegador."""
        self.browser_button.setEnabled(True)
        self.browser_button.setText("Abrir Navegador")
