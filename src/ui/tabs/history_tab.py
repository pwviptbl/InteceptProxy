from PySide6.QtCore import QAbstractTableModel, Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit,
                               QGroupBox, QHBoxLayout, QTableView, QAbstractItemView,
                               QTextEdit, QTabWidget, QSplitter, QComboBox, QHeaderView)
from PySide6.QtGui import QAction, QCursor

from src.core.history import RequestHistory

class HistoryTab(QWidget):
    """Aba de UI para exibir o histórico de requisições."""

    send_to_repeater_requested = Signal(dict)
    send_to_sender_requested = Signal(dict)

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
        # Adicionar filtros aqui no futuro
        filter_layout.addWidget(QLabel("Filtros (a implementar)"))
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
        self.history_table.setModel(self.history_model)

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
        entry_id = self.history_model.get_entry_id(row)
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

        row = selected.indexes()[0].row()
        entry_id = self.history_model.get_entry_id(row)
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
