# Comparador de Requisições - Mockup Visual

## Aba Comparador - Estado Inicial

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ InteceptProxy - Configurador                                          [_][□][X]║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: Rodando                    [Iniciar Proxy] [Parar Proxy] [Pausar]    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ [Regras] [Intercept] [Histórico] [Repetição] [Sender] [Decoder] [►Comparador◄]║
║                          [Cookie Jar] [Scanner] [Spider]                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ┌─ Instruções ───────────────────────────────────────────────────────────┐  ║
║ │ Use o menu de contexto (clique direito) no Histórico de Requisições   │  ║
║ │ para selecionar duas requisições para comparar.                       │  ║
║ └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
║ ┌─ Requisição 1 ──────────────┐ ┌─ Requisição 2 ──────────────┐            ║
║ │                              │ │                              │            ║
║ │ Nenhuma requisição           │ │ Nenhuma requisição           │            ║
║ │ selecionada                  │ │ selecionada                  │            ║
║ │                              │ │                              │            ║
║ └──────────────────────────────┘ └──────────────────────────────┘            ║
║                                                                              ║
║ [ Comparar ] [ Limpar ]                                                      ║
║                                                                              ║
║ ┌───────────────────────────────────────────────────────────────────────┐  ║
║ │ [Request Comparison] [Response Comparison]                            │  ║
║ │                                                                        │  ║
║ │ ┌─ Request 1 ───────────────┐ ┌─ Request 2 ───────────────┐          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │  (vazio)                   │ │  (vazio)                   │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ └────────────────────────────┘ └────────────────────────────┘          │  ║
║ └───────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Histórico - Menu de Contexto

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ [Regras] [Intercept] [►Histórico◄] [Repetição] [Sender] [Decoder] [Comparador]║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ┌─ Filtros ──────────────────────────────────────────────────────────────┐  ║
║ │ Método: [Todos ▼]  Domínio (regex): [               ]                 │  ║
║ │                    [Aplicar Filtros] [Limpar Histórico]               │  ║
║ └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
║ ┌─ Requisições Capturadas ──────────────────────────────────────────────┐  ║
║ │ Host         │ Data      │ Hora     │ Método │ Status │ URL           │  ║
║ │──────────────┼───────────┼──────────┼────────┼────────┼───────────────│  ║
║ │►exemplo.com  │ 15/01/2025│ 10:30:00 │ GET    │ 200    │ /api/users    │  ║
║ │ exemplo.com  │ 15/01/2025│ 10:31:00 │ POST   │ 401    │ /api/login    │  ║
║ │ teste.com    │ 15/01/2025│ 10:32:00 │ GET    │ 200    │ /home         │  ║
║ └────────────────┌──────────────────────────────────┐────────────────────┘  ║
║                  │ ✓ Enviar para Repetição          │                       ║
║                  │ ✓ Enviar para o Sender           │                       ║
║                  │ ─────────────────────────────────│                       ║
║                  │ ► Definir como Requisição 1      │                       ║
║                  │   (Comparador)                   │                       ║
║                  │ ► Definir como Requisição 2      │                       ║
║                  │   (Comparador)                   │                       ║
║                  └──────────────────────────────────┘                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Comparador - Com Duas Requisições Selecionadas

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ [►Comparador◄]                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ┌─ Instruções ───────────────────────────────────────────────────────────┐  ║
║ │ Use o menu de contexto (clique direito) no Histórico de Requisições   │  ║
║ │ para selecionar duas requisições para comparar.                       │  ║
║ └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
║ ┌─ Requisição 1 ──────────────┐ ┌─ Requisição 2 ──────────────┐            ║
║ │                              │ │                              │            ║
║ │ GET exemplo.com/api/users -  │ │ POST exemplo.com/api/login - │            ║
║ │ 2025-01-15 10:30:00          │ │ 2025-01-15 10:31:00          │            ║
║ │                              │ │                              │            ║
║ └──────────────────────────────┘ └──────────────────────────────┘            ║
║                                                                              ║
║ [ Comparar ] [ Limpar ]                                                      ║
║                                                                              ║
║ ┌───────────────────────────────────────────────────────────────────────┐  ║
║ │ [Request Comparison] [Response Comparison]                            │  ║
║ │                                                                        │  ║
║ │ ┌─ Request 1 ───────────────┐ ┌─ Request 2 ───────────────┐          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │  (aguardando comparação)   │ │  (aguardando comparação)   │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ └────────────────────────────┘ └────────────────────────────┘          │  ║
║ └───────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Comparador - Após Clicar em "Comparar"

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ [►Comparador◄]                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ┌─ Instruções ───────────────────────────────────────────────────────────┐  ║
║ │ Use o menu de contexto (clique direito) no Histórico de Requisições   │  ║
║ │ para selecionar duas requisições para comparar.                       │  ║
║ └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
║ ┌─ Requisição 1 ──────────────┐ ┌─ Requisição 2 ──────────────┐            ║
║ │                              │ │                              │            ║
║ │ GET exemplo.com/api/users -  │ │ POST exemplo.com/api/login - │            ║
║ │ 2025-01-15 10:30:00          │ │ 2025-01-15 10:31:00          │            ║
║ │                              │ │                              │            ║
║ └──────────────────────────────┘ └──────────────────────────────┘            ║
║                                                                              ║
║ [ Comparar ] [ Limpar ]                                                      ║
║                                                                              ║
║ ┌───────────────────────────────────────────────────────────────────────┐  ║
║ │ [►Request Comparison◄] [Response Comparison]                          │  ║
║ │                                                                        │  ║
║ │ ┌─ Request 1 ───────────────┐ ┌─ Request 2 ───────────────┐          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ GET /api/users HTTP/1.1    │ │ POST /api/login HTTP/1.1   │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ Host: exemplo.com          │ │ Host: exemplo.com          │          │  ║
║ │ │ User-Agent: Mozilla/5.0    │ │ User-Agent: Mozilla/5.0    │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ Content-Type: application/ │ │ Content-Type: application/ │          │  ║
║ │ │               json         │ │               x-www-form-  │          │  ║
║ │ │                            │ │               urlencoded   │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │ {"limit": 10, "offset": 0} │ │ username=admin&password=   │          │  ║
║ │ │ ██████████████████████████ │ │ secret&csrf_token=abc123   │          │  ║
║ │ │                            │ │ ██████████████████████████ │          │  ║
║ │ └────────────────────────────┘ └────────────────────────────┘          │  ║
║ └───────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Legenda: ██████ = Linha destacada em vermelho claro (diferença detectada)
```

## Comparador - Aba Response Comparison

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ [►Comparador◄]                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ [ Comparar ] [ Limpar ]                                                      ║
║                                                                              ║
║ ┌───────────────────────────────────────────────────────────────────────┐  ║
║ │ [Request Comparison] [►Response Comparison◄]                          │  ║
║ │                                                                        │  ║
║ │ ┌─ Response 1 ──────────────┐ ┌─ Response 2 ──────────────┐          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ Status: 200                │ │ Status: 401                │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │ Content-Type: application/ │ │ Content-Type: application/ │          │  ║
║ │ │               json         │ │               json         │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ Server: nginx              │ │ Server: apache             │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ Cache-Control: no-cache    │ │ Cache-Control: no-store    │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │                            │ │                            │          │  ║
║ │ │ ██████████████████████████ │ │ ██████████████████████████ │          │  ║
║ │ │ {"users": [                │ │ {"error": "Invalid         │          │  ║
║ │ │   {"id": 1, "name": "João"},│ │  credentials",             │          │  ║
║ │ │   {"id": 2, "name": "Maria"}│ │  "csrf_token": "xyz789"}   │          │  ║
║ │ │  ],                        │ │ ██████████████████████████ │          │  ║
║ │ │  "total": 2}               │ │                            │          │  ║
║ │ │ ██████████████████████████ │ │                            │          │  ║
║ │ └────────────────────────────┘ └────────────────────────────┘          │  ║
║ └───────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Legenda: ██████ = Linha destacada em vermelho claro (diferença detectada)
```

## Características Destacadas

### 🎨 Visual Highlighting
- Linhas com diferenças são destacadas com fundo vermelho claro (#ffcccc)
- Facilita identificação imediata de mudanças
- Funciona linha por linha para precisão

### 📊 Layout Side-by-Side
- Comparação lado a lado facilita análise
- Scroll sincronizado (em versões futuras)
- Abas separadas para Request e Response

### 🔄 Workflow Simples
1. Seleciona Req 1 → Vai para Comparador
2. Volta ao Histórico → Seleciona Req 2
3. Clica "Comparar" → Vê diferenças
4. Clica "Limpar" → Recomeça

### 💡 Casos de Uso Reais

#### Exemplo 1: Token CSRF
```
Request 1: cookie: csrf=abc123
Request 2: cookie: csrf=xyz789
          ^^^^^^^^^^^^^^^^      ← Destacado em vermelho
```

#### Exemplo 2: Mudança de Método
```
Request 1: GET /api/users
          ^^^              ← Destacado
Request 2: POST /api/users
          ^^^^             ← Destacado
```

#### Exemplo 3: Diferença em JSON
```
Response 1: {"status": "success"}
                      ^^^^^^^^    ← Destacado
Response 2: {"status": "error"}
                      ^^^^^       ← Destacado
```
