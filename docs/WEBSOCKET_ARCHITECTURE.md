# WebSocket Support Architecture

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Cliente (Browser/App)                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ WebSocket Upgrade Request
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         InteceptProxy (Port 8080)                    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    InterceptAddon                            │   │
│  │                                                               │   │
│  │  • websocket_start()   ──────────────────┐                  │   │
│  │  • websocket_message() ──────────────┐   │                  │   │
│  │  • websocket_end()     ──────────┐   │   │                  │   │
│  └──────────────────────────────────┼───┼───┼──────────────────┘   │
│                                     │   │   │                       │
│                                     ▼   ▼   ▼                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 WebSocketHistory                             │   │
│  │                                                               │   │
│  │  connections = {                                             │   │
│  │    flow_id: {                                                │   │
│  │      'id', 'url', 'host', 'status',                         │   │
│  │      'start_time', 'end_time', 'message_count'              │   │
│  │    }                                                         │   │
│  │  }                                                           │   │
│  │                                                               │   │
│  │  messages = {                                                │   │
│  │    flow_id: [                                                │   │
│  │      {                                                       │   │
│  │        'timestamp', 'from_client', 'content',               │   │
│  │        'is_binary', 'size'                                  │   │
│  │      }                                                       │   │
│  │    ]                                                         │   │
│  │  }                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                     │                                │
└─────────────────────────────────────┼────────────────────────────────┘
                                      │
                                      │ Passa para o servidor real
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Servidor WebSocket Real                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Interface Gráfica

```
┌─────────────────────────────────────────────────────────────────────┐
│                    InteceptProxy GUI                                 │
│                                                                       │
│  [Regras] [Intercept] [Histórico] ... [WebSocket 🔌]                │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                       │
│  ┌─ Conexões WebSocket ─────────────────────────────────────────┐  │
│  │ ID │ Host         │ URL                  │ Status │ Msg │...│  │
│  │ 1  │ example.com  │ wss://example.com/ws │ active │ 42  │...│  │
│  │ 2  │ api.test.com │ wss://api.test.com   │ closed │ 156 │...│  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ▲                                            │
│                          │ Seleção                                   │
│                          │                                            │
│  ┌─ Mensagens ─────────────────────────────────────────────────┐   │
│  │ Timestamp    │ Direção           │ Tamanho │ Tipo          │   │
│  │ 14:23:45.123 │ Cliente→Servidor  │ 15 B    │ Texto         │   │
│  │ 14:23:45.456 │ Servidor→Cliente  │ 234 B   │ Texto         │   │
│  │ 14:23:46.789 │ Cliente→Servidor  │ 512 B   │ Binário       │   │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ▲                                            │
│                          │ Seleção                                   │
│                          │                                            │
│  ┌─ Conteúdo da Mensagem ───────────────────────────────────────┐  │
│  │                                                                │  │
│  │ {"type":"message","data":"Hello World"}                       │  │
│  │                                                                │  │
│  │                                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  [Atualizar] [Limpar Histórico] [Reenviar] (desabilitado)           │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Eventos WebSocket

### 1. websocket_start
Chamado quando uma conexão WebSocket é estabelecida.

**Ações:**
- Cria entrada no histórico de conexões
- Registra URL, host e timestamp
- Define status como 'active'

### 2. websocket_message
Chamado para cada mensagem WebSocket (cliente→servidor ou servidor→cliente).

**Ações:**
- Identifica direção da mensagem
- Detecta se é texto ou binário
- Armazena conteúdo e metadata
- Incrementa contador de mensagens

### 3. websocket_end
Chamado quando a conexão WebSocket é fechada.

**Ações:**
- Atualiza status para 'closed'
- Registra timestamp de fechamento
- Mantém histórico de mensagens

## Tipos de Mensagens

### Mensagens de Texto
- Codificadas em UTF-8
- Exibidas como string
- Exemplo: `{"type":"ping"}`

### Mensagens Binárias
- Não são UTF-8 válido ou contêm bytes não-imprimíveis
- Exibidas em formato hexadecimal
- Exemplo: `00010203fffefd`

## Limitações Atuais

### ✅ Implementado
- [x] Interceptação de conexões
- [x] Captura de mensagens
- [x] Visualização de histórico
- [x] Suporte a texto e binário
- [x] Interface gráfica

### ⚠️ Futuro
- [ ] Modificação de mensagens em tempo real
- [ ] Reenvio de mensagens
- [ ] Filtros avançados
- [ ] Exportação de histórico
- [ ] Busca em mensagens

## Integração com mitmproxy

O InteceptProxy utiliza os eventos WebSocket do mitmproxy:

```python
class InterceptAddon:
    def websocket_start(self, flow: websocket.WebSocketFlow):
        # Captura início da conexão
        pass
    
    def websocket_message(self, flow: websocket.WebSocketFlow):
        # Captura cada mensagem
        pass
    
    def websocket_end(self, flow: websocket.WebSocketFlow):
        # Captura fechamento da conexão
        pass
```

Esses eventos são automaticamente chamados pelo mitmproxy quando ele intercepta
tráfego WebSocket através do proxy.
