# 🔀 Comparador de Requisições

## Descrição

O **Comparador de Requisições** é uma funcionalidade que permite comparar duas requisições/respostas HTTP lado a lado, com destaque visual das diferenças. É extremamente útil para:

- Encontrar tokens CSRF que mudam entre requisições
- Identificar diferenças sutis em headers
- Comparar respostas de diferentes endpoints
- Analisar mudanças em payloads JSON/XML
- Debug de comportamentos inconsistentes

## 🎯 Características

### ✨ Funcionalidades Implementadas

- ✅ **Seleção via Menu de Contexto**: Clique direito em qualquer requisição no histórico para selecioná-la
- ✅ **Comparação Lado a Lado**: Visualize Request 1 e Request 2 simultaneamente
- ✅ **Comparação de Respostas**: Compare também as respostas HTTP
- ✅ **Highlighting de Diferenças**: Diferenças são destacadas automaticamente com fundo vermelho claro
- ✅ **Algoritmo Inteligente**: Usa Python `difflib.SequenceMatcher` para detectar diferenças precisas
- ✅ **Interface Intuitiva**: Abas separadas para Request e Response comparisons
- ✅ **Botões de Ação**: Comparar e Limpar para controlar a visualização

## 📖 Como Usar

### Passo 1: Selecionar Requisição 1

1. Vá para a aba **Histórico de Requisições**
2. Localize a primeira requisição que deseja comparar
3. Clique direito sobre ela
4. Selecione **"Definir como Requisição 1 (Comparador)"**
5. A interface mudará automaticamente para a aba **Comparador**

### Passo 2: Selecionar Requisição 2

1. Volte para a aba **Histórico de Requisições**
2. Localize a segunda requisição que deseja comparar
3. Clique direito sobre ela
4. Selecione **"Definir como Requisição 2 (Comparador)"**

### Passo 3: Comparar

1. Na aba **Comparador**, você verá as duas requisições selecionadas nos labels de status
2. Clique no botão **"Comparar"**
3. As requisições e respostas serão exibidas lado a lado
4. Diferenças serão destacadas em vermelho claro

### Passo 4: Analisar Diferenças

- Use a aba **Request Comparison** para ver diferenças nas requisições
- Use a aba **Response Comparison** para ver diferenças nas respostas
- Linhas destacadas em vermelho indicam conteúdo diferente entre as duas requisições

### Passo 5: Limpar (Opcional)

- Clique em **"Limpar"** para resetar o comparador
- Isso permite selecionar novas requisições para comparar

## 🎨 Interface

```
┌────────────────────────────────────────────────────────────────┐
│ Comparador                                                     │
├────────────────────────────────────────────────────────────────┤
│ Instruções                                                     │
│ Use o menu de contexto (clique direito) no Histórico...       │
├────────────────────────────────────────────────────────────────┤
│ Requisição 1                  │ Requisição 2                  │
│ GET exemplo.com/api/users -   │ POST exemplo.com/api/login -  │
│ 2025-01-15 10:30:00           │ 2025-01-15 10:31:00           │
├────────────────────────────────────────────────────────────────┤
│ [Comparar] [Limpar]                                            │
├────────────────────────────────────────────────────────────────┤
│ ┌─Request Comparison───┬─Response Comparison───┐              │
│ │                      │                        │              │
│ │ Request 1 │ Request 2│  Response 1 │ Response 2              │
│ │ ──────────┼──────────│  ───────────┼──────────               │
│ │ GET ...   │ POST ... │  Status: 200│ Status: 401             │
│ │ Host: ... │ Host: ...│  Content-...│ Content-...             │
│ │           │          │             │                         │
│ └──────────────────────┴─────────────────────────┘             │
└────────────────────────────────────────────────────────────────┘
```

## 💡 Casos de Uso

### 1. Encontrar Tokens CSRF

```
Requisição 1 (GET /form):
  Set-Cookie: csrf_token=abc123

Requisição 2 (POST /form):
  Cookie: csrf_token=abc123
  
→ O comparador destacará o token CSRF diferente
```

### 2. Comparar Autenticação

```
Request 1 (sem auth):
  GET /api/data HTTP/1.1
  
Request 2 (com auth):
  GET /api/data HTTP/1.1
  Authorization: Bearer token123
  
→ Veja exatamente que header foi adicionado
```

### 3. Debug de API

```
Response 1:
  {"status": "success", "data": {...}}

Response 2:
  {"status": "error", "message": "Invalid token"}
  
→ Compare respostas para entender o erro
```

## 🔧 Implementação Técnica

### Estrutura de Dados

Cada requisição no histórico contém:
```python
{
    'host': 'exemplo.com',
    'method': 'GET',
    'path': '/api/users',
    'status': 200,
    'request_headers': {...},
    'request_body': '...',
    'response_headers': {...},
    'response_body': '...',
    'timestamp': '2025-01-15 10:30:00'
}
```

### Algoritmo de Diff

Usa `difflib.SequenceMatcher`:
```python
matcher = difflib.SequenceMatcher(None, lines1, lines2)
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag in ['replace', 'delete', 'insert']:
        # Marca diferenças
```

### Tags de Highlighting

- **diff**: Background vermelho claro (`#ffcccc`)
- **same**: Background branco (padrão)

## 🧪 Testes

Execute os testes:
```bash
python3 test/test_comparator.py
```

Execute a demonstração:
```bash
python3 demo_comparator.py
```

## 📊 Benefícios

| Benefício | Descrição |
|-----------|-----------|
| 🕒 **Economiza Tempo** | Não precisa comparar manualmente linha por linha |
| 🎯 **Precisão** | Algoritmo detecta todas as diferenças automaticamente |
| 👁️ **Visual** | Highlighting torna diferenças óbvias |
| 🔄 **Reutilizável** | Compare quantas vezes quiser |
| 📝 **Documentação** | Capture screenshots das comparações |

## 🚀 Próximas Melhorias (Futuro)

- [ ] Exportar comparação para HTML/PDF
- [ ] Comparar mais de 2 requisições simultaneamente
- [ ] Filtros de comparação (apenas headers, apenas body, etc.)
- [ ] Comparação semântica de JSON (ignorar ordem de campos)
- [ ] Histórico de comparações
- [ ] Estatísticas de diferenças (% de similaridade)

## 📚 Referências

- Python difflib: https://docs.python.org/3/library/difflib.html
- Burp Suite Comparer: Inspiração para esta funcionalidade
- Feature Analysis: `docs/FEATURE_ANALYSIS.md`

---

**Status**: ✅ Implementado e Testado  
**Versão**: 1.0  
**Data**: Janeiro 2025
