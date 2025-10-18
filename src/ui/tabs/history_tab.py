from PySide6.QtCore import QAbstractTableModel, Qt, Signal, QSortFilterProxyModel
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit,
                               QGroupBox, QHBoxLayout, QTableView, QAbstractItemView,
                               QTextEdit, QTabWidget, QSplitter, QComboBox, QHeaderView)
from PySide6.QtGui import QAction, QCursor

from src.core.history import RequestHistory

class HistoryTab(QWidget):
    """Aba de UI para exibir o histórico de requisições."""

    send_to_repeater_requested = Signal(dict)
    send_to_sender_requested = Signal(dict)
    clear_history_requested = Signal()

    def __init__(self, history: RequestHistory):
        super().__init__()
        self.history_manager = history
        self.entry_map = {} # Mapeia ID da entrada para a entrada completa

        layout = QVBoxLayout(self)

        self._setup_filters(layout)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        self._setup_history_table(splitter)
        self._setup_details_panel(splitter)

        splitter.setSizes([400, 300]) # Tamanhos iniciais

    def _setup_filters(self, layout):
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout()

        # Filtro por método
        filter_layout.addWidget(QLabel("Método:"))
        self.method_filter = QComboBox()
        self.method_filter.addItems(["Todos", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        filter_layout.addWidget(self.method_filter)

        # Filtro por domínio
        filter_layout.addWidget(QLabel("Domínio:"))
        self.domain_filter = QLineEdit()
        self.domain_filter.setPlaceholderText("ex: google.com")
        filter_layout.addWidget(self.domain_filter)

        # Botões de ação
        apply_button = QPushButton("Aplicar Filtros")
        apply_button.clicked.connect(self._apply_filters)
        filter_layout.addWidget(apply_button)

        clear_button = QPushButton("Limpar Histórico")
        clear_button.clicked.connect(self._confirm_clear_history)
        filter_layout.addWidget(clear_button)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

    def _setup_history_table(self, parent):
        table_group = QGroupBox("Requisições Capturadas")
        table_layout = QVBoxLayout()

        self.history_table = QTableView()
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setSortingEnabled(True)

        self.history_model = HistoryTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.history_model)
        self.history_table.setModel(self.proxy_model)

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self._show_context_menu)

        selection_model = self.history_table.selectionModel()
        selection_model.selectionChanged.connect(self._on_selection_changed)

        table_layout.addWidget(self.history_table)
        table_group.setLayout(table_layout)
        parent.addWidget(table_group)

    def _setup_details_panel(self, parent):
        details_group = QGroupBox("Detalhes da Requisição")
        details_layout = QVBoxLayout()

        self.details_tabs = QTabWidget()
        self.request_text = QTextEdit()
        self.request_text.setReadOnly(True)
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)

        self.details_tabs.addTab(self.request_text, "Request")
        self.details_tabs.addTab(self.response_text, "Response")

        details_layout.addWidget(self.details_tabs)
        details_group.setLayout(details_layout)
        parent.addWidget(details_group)

    def _show_context_menu(self, pos):
        """Exibe o menu de contexto na tabela."""
        selected_indexes = self.history_table.selectionModel().selectedRows()
        if not selected_indexes:
            return

        row = selected_indexes[0].row()
        source_index = self.proxy_model.mapToSource(selected_indexes[0])
        entry_id = self.history_model.get_entry_id(source_index.row())
        entry = self.entry_map.get(entry_id)

        if not entry:
            return

        menu = self.history_table.createStandardContextMenu()

        send_to_repeater_action = QAction("Enviar para Repetição", self)
        send_to_repeater_action.triggered.connect(lambda: self.send_to_repeater_requested.emit(entry))
        menu.addAction(send_to_repeater_action)

        send_to_sender_action = QAction("Enviar para o Sender", self)
        send_to_sender_action.triggered.connect(lambda: self.send_to_sender_requested.emit(entry))
        menu.addAction(send_to_sender_action)

        menu.exec_(self.history_table.viewport().mapToGlobal(pos))

    def _on_selection_changed(self, selected, deselected):
        """Exibe os detalhes da requisição selecionada."""
        if not selected.indexes():
            return

        proxy_index = selected.indexes()[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        entry_id = self.history_model.get_entry_id(source_index.row())
        entry = self.entry_map.get(entry_id)

        if entry:
            req_headers = "\n".join(f"{k}: {v}" for k, v in entry['request_headers'].items())
            req_full = f"{entry['method']} {entry['path']} HTTP/1.1\nHost: {entry['host']}\n{req_headers}\n\n{entry['request_body']}"
            self.request_text.setPlainText(req_full)

            resp_headers = "\n".join(f"{k}: {v}" for k, v in entry['response_headers'].items())
            resp_full = f"Status: {entry['status']}\n{resp_headers}\n\n{entry['response_body']}"
            self.response_text.setPlainText(resp_full)

    def add_history_entry(self, entry: dict):
        """Adiciona uma nova entrada de histórico à tabela."""
        self.entry_map[entry['id']] = entry
        self.history_model.add_entry(entry)

    def _confirm_clear_history(self):
        """Exibe um diálogo de confirmação antes de limpar o histórico."""
        reply = QMessageBox.question(self, 'Confirmar Limpeza',
                                     "Você tem certeza que deseja limpar todo o histórico?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_history_requested.emit()

    def _apply_filters(self):
        """Aplica os filtros de método e domínio na tabela."""
        # Filtro de método (Coluna 2)
        method_filter = self.method_filter.currentText()
        if method_filter != "Todos":
            self.proxy_model.setFilterKeyColumn(2)
            self.proxy_model.setFilterRegularExpression(f"^{method_filter}$")
        else:
            # Limpa o filtro de método se "Todos" for selecionado
            self.proxy_model.setFilterKeyColumn(2)
            self.proxy_model.setFilterRegularExpression(".*")

        # Filtro de domínio (Coluna 1)
        domain_filter = self.domain_filter.text().strip()
        self.proxy_model.setFilterKeyColumn(1)
        self.proxy_model.setFilterRegularExpression(domain_filter)

    def clear_display(self):
        """Limpa a exibição da tabela."""
        self.history_model.clear()
        self.entry_map.clear()

class HistoryTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = ['ID', 'Host', 'Método', 'Status', 'URL']

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            entry = self._data[index.row()]
            col = index.column()
            if col == 0: return entry['id']
            if col == 1: return entry['host']
            if col == 2: return entry['method']
            if col == 3: return entry['status']
            if col == 4: return entry['url']
        return None

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def add_entry(self, entry):
        self.beginInsertRows(self.index(self.rowCount(0), 0), self.rowCount(0), self.rowCount(0))
        self._data.append(entry)
        self.endInsertRows()

    def get_entry_id(self, row):
        return self._data[row]['id']

    def clear(self):
        """Limpa todos os dados do modelo."""
        self.beginResetModel()
        self._data = []
        self.endResetModel()
