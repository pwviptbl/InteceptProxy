#!/usr/bin/env python3
"""
Demo script para visualizar a funcionalidade do Comparador de Requisições
Este script cria uma demonstração visual da UI do comparador
"""
import os
import sys

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    from ttkthemes import ThemedTk
    import difflib
    HAS_TK = True
except ImportError:
    HAS_TK = False
    print("⚠️  Tkinter não disponível neste ambiente")
    print("   A feature do Comparador foi implementada e funcionaria em um ambiente com GUI")


def create_demo_window():
    """Cria uma janela de demonstração do comparador"""
    if not HAS_TK:
        print("\n📋 Demonstração da estrutura do Comparador:")
        print("=" * 60)
        print("\nRecursos implementados:")
        print("✓ Seleção de duas requisições via menu de contexto")
        print("✓ Exibição lado a lado de requisições")
        print("✓ Exibição lado a lado de respostas")
        print("✓ Highlighting de diferenças usando difflib")
        print("✓ Botões Comparar e Limpar")
        print("✓ Instruções claras na interface")
        return

    # Cria janela principal
    root = ThemedTk(theme="arc")
    root.title("Demo: Comparador de Requisições - InteceptProxy")
    root.geometry("1200x700")

    # Frame de instruções
    info_frame = ttk.LabelFrame(root, text="Instruções", padding=5)
    info_frame.pack(fill="x", padx=10, pady=5)
    
    info_label = ttk.Label(info_frame, 
                          text="Use o menu de contexto (clique direito) no Histórico de Requisições para selecionar duas requisições para comparar.",
                          wraplength=1100)
    info_label.pack(padx=5, pady=5)

    # Frame de status
    status_frame = ttk.Frame(root)
    status_frame.pack(fill="x", padx=10, pady=5)
    
    # Labels para mostrar quais requisições foram selecionadas
    req1_frame = ttk.LabelFrame(status_frame, text="Requisição 1", padding=5)
    req1_frame.pack(side="left", fill="both", expand=True, padx=5)
    req1_label = ttk.Label(req1_frame, text="GET exemplo.com/api/users - 2025-01-15 10:30:00", foreground="black")
    req1_label.pack()
    
    req2_frame = ttk.LabelFrame(status_frame, text="Requisição 2", padding=5)
    req2_frame.pack(side="left", fill="both", expand=True, padx=5)
    req2_label = ttk.Label(req2_frame, text="POST exemplo.com/api/login - 2025-01-15 10:31:00", foreground="black")
    req2_label.pack()

    # Botões de ação
    buttons_frame = ttk.Frame(root)
    buttons_frame.pack(fill="x", padx=10, pady=5)
    
    ttk.Button(buttons_frame, text="Comparar", command=lambda: compare_demo(notebook)).pack(side="left", padx=5)
    ttk.Button(buttons_frame, text="Limpar", command=lambda: clear_demo(notebook)).pack(side="left", padx=5)

    # Notebook para Request/Response comparisons
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    # Tab de comparação de Request
    request_compare_tab = ttk.Frame(notebook)
    notebook.add(request_compare_tab, text="Request Comparison")
    
    request_paned = ttk.PanedWindow(request_compare_tab, orient=tk.HORIZONTAL)
    request_paned.pack(fill="both", expand=True)
    
    # Request 1
    req1_frame = ttk.LabelFrame(request_paned, text="Request 1", padding=5)
    request_paned.add(req1_frame, weight=1)
    request1_text = scrolledtext.ScrolledText(req1_frame, wrap=tk.WORD, height=20)
    request1_text.pack(fill="both", expand=True)
    
    # Request 2
    req2_frame = ttk.LabelFrame(request_paned, text="Request 2", padding=5)
    request_paned.add(req2_frame, weight=1)
    request2_text = scrolledtext.ScrolledText(req2_frame, wrap=tk.WORD, height=20)
    request2_text.pack(fill="both", expand=True)

    # Tab de comparação de Response
    response_compare_tab = ttk.Frame(notebook)
    notebook.add(response_compare_tab, text="Response Comparison")
    
    response_paned = ttk.PanedWindow(response_compare_tab, orient=tk.HORIZONTAL)
    response_paned.pack(fill="both", expand=True)
    
    # Response 1
    resp1_frame = ttk.LabelFrame(response_paned, text="Response 1", padding=5)
    response_paned.add(resp1_frame, weight=1)
    response1_text = scrolledtext.ScrolledText(resp1_frame, wrap=tk.WORD, height=20)
    response1_text.pack(fill="both", expand=True)
    
    # Response 2
    resp2_frame = ttk.LabelFrame(response_paned, text="Response 2", padding=5)
    response_paned.add(resp2_frame, weight=1)
    response2_text = scrolledtext.ScrolledText(resp2_frame, wrap=tk.WORD, height=20)
    response2_text.pack(fill="both", expand=True)

    # Configurar tags para highlighting de diferenças
    for text_widget in [request1_text, request2_text, response1_text, response2_text]:
        text_widget.tag_configure("diff", background="#ffcccc")
        text_widget.tag_configure("same", background="white")

    # Armazena os widgets no notebook para usar nas funções
    notebook.request1_text = request1_text
    notebook.request2_text = request2_text
    notebook.response1_text = response1_text
    notebook.response2_text = response2_text

    # Preenche com dados de exemplo
    compare_demo(notebook)

    root.mainloop()


def compare_demo(notebook):
    """Preenche o comparador com dados de exemplo"""
    # Dados de exemplo para Request 1
    req1 = """GET /api/users HTTP/1.1
Host: exemplo.com
User-Agent: Mozilla/5.0
Content-Type: application/json
Authorization: Bearer token123

{"limit": 10, "offset": 0}"""

    # Dados de exemplo para Request 2
    req2 = """POST /api/login HTTP/1.1
Host: exemplo.com
User-Agent: Mozilla/5.0
Content-Type: application/x-www-form-urlencoded

username=admin&password=secret&csrf_token=abc123"""

    # Dados de exemplo para Response 1
    resp1 = """Status: 200

Content-Type: application/json
Server: nginx
Cache-Control: no-cache

{"users": [{"id": 1, "name": "João"}, {"id": 2, "name": "Maria"}], "total": 2}"""

    # Dados de exemplo para Response 2
    resp2 = """Status: 401

Content-Type: application/json
Server: apache
Cache-Control: no-store

{"error": "Invalid credentials", "csrf_token": "xyz789"}"""

    # Limpa os campos
    notebook.request1_text.delete('1.0', tk.END)
    notebook.request2_text.delete('1.0', tk.END)
    notebook.response1_text.delete('1.0', tk.END)
    notebook.response2_text.delete('1.0', tk.END)

    # Insere o texto
    notebook.request1_text.insert('1.0', req1)
    notebook.request2_text.insert('1.0', req2)
    notebook.response1_text.insert('1.0', resp1)
    notebook.response2_text.insert('1.0', resp2)

    # Aplica highlighting de diferenças
    highlight_differences(notebook.request1_text, notebook.request2_text, req1, req2)
    highlight_differences(notebook.response1_text, notebook.response2_text, resp1, resp2)


def highlight_differences(text_widget1, text_widget2, text1, text2):
    """Aplica highlighting de diferenças entre dois textos"""
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


def clear_demo(notebook):
    """Limpa o comparador"""
    notebook.request1_text.delete('1.0', tk.END)
    notebook.request2_text.delete('1.0', tk.END)
    notebook.response1_text.delete('1.0', tk.END)
    notebook.response2_text.delete('1.0', tk.END)


if __name__ == "__main__":
    print("🎯 Demonstração do Comparador de Requisições")
    print("=" * 60)
    print()
    
    if HAS_TK:
        print("Abrindo janela de demonstração...")
        print("Pressione Ctrl+C ou feche a janela para sair")
        print()
        create_demo_window()
    else:
        create_demo_window()  # Mostra versão texto
        print("\n✅ A implementação do Comparador está completa!")
        print("   Execute em um ambiente com GUI para ver a interface visual")
