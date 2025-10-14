# Intercept Manual - Fluxo de Funcionamento

## Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│                      BROWSER REQUEST                            │
│                  (ex: POST /login HTTP/1.1)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MITMPROXY INTERCEPTOR                        │
│                     (addon.py: request())                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Proxy Paused?  │
                   └────────┬───────┘
                            │ No
                            ▼
                   ┌────────────────┐
                   │ Intercept ON?  │
                   └────┬───────┬───┘
                   Yes  │       │ No
                   ┌────▼───┐   │
                   │ QUEUE  │   │
                   │REQUEST │   │
                   └────┬───┘   │
                        │       │
        ┌───────────────▼───────▼──────────────────┐
        │    WAIT FOR USER DECISION (5 min)       │
        │         (config.py: queues)             │
        └───────────────┬──────────────────────────┘
                        │
        ┌───────────────┴──────────────┐
        │                              │
        ▼                              ▼
┌───────────────┐              ┌──────────────┐
│  USER CLICKS  │              │   TIMEOUT    │
│  FORWARD/DROP │              │  (5 minutes) │
└───────┬───────┘              └──────┬───────┘
        │                             │
        │      ┌──────────────────────┘
        │      │
        ▼      ▼
┌─────────────────────────────────────────┐
│       GUI (gui.py)                      │
│  ┌─────────────┐   ┌─────────────┐     │
│  │   FORWARD   │   │    DROP     │     │
│  │   BUTTON    │   │   BUTTON    │     │
│  └──────┬──────┘   └──────┬──────┘     │
│         │                 │             │
│         │                 │             │
└─────────┼─────────────────┼─────────────┘
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ forward_request │  │  drop_request    │
│                 │  │                  │
│ - Read edits    │  │ - Send 'drop'    │
│ - Send response │  │   action         │
│   to queue      │  │ - Kill request   │
└────────┬────────┘  └─────────┬────────┘
         │                     │
         │                     │
         ▼                     ▼
┌─────────────────────────────────────────┐
│    config.add_intercept_response()      │
│         (response queue)                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   addon.py: config.get_intercept_       │
│            response(timeout=300)        │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌───────────────┐
│   FORWARD    │  │     DROP      │
│              │  │               │
│ - Apply edits│  │ - flow.kill() │
│ - Continue   │  │ - Stop here   │
│   to rules   │  │               │
└──────┬───────┘  └───────────────┘
       │
       ▼
┌──────────────────┐
│  APPLY RULES     │
│  (if any)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  SEND TO SERVER  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     RESPONSE     │
└──────────────────┘
```

## Componentes Principais

### 1. InterceptConfig (config.py)
```python
class InterceptConfig:
    # Estado
    intercept_enabled = False
    
    # Filas (thread-safe)
    intercept_queue = Queue()           # Requisições interceptadas
    intercept_response_queue = Queue()  # Decisões do usuário
    
    # Métodos
    toggle_intercept()                  # ON/OFF
    add_to_intercept_queue(flow_data)   # Adiciona req à fila
    get_from_intercept_queue()          # Pega req da fila
    add_intercept_response(response)    # Adiciona decisão
    get_intercept_response(timeout=300) # Pega decisão (5 min)
    clear_intercept_queues()            # Limpa tudo
```

### 2. InterceptAddon (addon.py)
```python
def request(self, flow):
    if config.is_intercept_enabled():
        # 1. Prepara dados
        flow_data = {
            'flow': flow,
            'method': flow.request.method,
            'url': flow.request.pretty_url,
            'headers': dict(flow.request.headers),
            'body': flow.request.content.decode(),
            ...
        }
        
        # 2. Adiciona à fila
        config.add_to_intercept_queue(flow_data)
        
        # 3. Aguarda decisão (bloqueante, 5 min timeout)
        response = config.get_intercept_response(timeout=300)
        
        # 4. Processa decisão
        if response is None or response['action'] == 'drop':
            flow.kill()  # Cancela requisição
            return
        
        if response['action'] == 'forward':
            # Aplica modificações
            if 'modified_body' in response:
                flow.request.content = response['modified_body'].encode()
            if 'modified_headers' in response:
                flow.request.headers.clear()
                for k, v in response['modified_headers'].items():
                    flow.request.headers[k] = v
    
    # Continua com regras normais...
```

### 3. ProxyGUI (gui.py)

#### Polling Loop
```python
def check_intercept_queue(self):
    """Verifica a fila a cada 100ms"""
    if config.is_intercept_enabled():
        request_data = config.get_from_intercept_queue(timeout=0.01)
        if request_data:
            self._display_intercepted_request(request_data)
    
    self.root.after(100, self.check_intercept_queue)
```

#### Display Request
```python
def _display_intercepted_request(self, request_data):
    """Mostra requisição na UI"""
    self.current_intercept_request = request_data
    
    # Atualiza UI
    self.intercept_method_label.config(text=request_data['method'])
    self.intercept_url_label.config(text=request_data['url'])
    self.intercept_headers_text.insert('1.0', headers_text)
    self.intercept_body_text.insert('1.0', request_data['body'])
    
    # Habilita botões
    self.forward_button.config(state="normal")
    self.drop_button.config(state="normal")
    
    # Muda para aba
    self.notebook.select(1)
```

#### Forward
```python
def forward_request(self):
    """Envia requisição (com edições)"""
    # Lê edições
    headers_text = self.intercept_headers_text.get('1.0', 'end')
    body_text = self.intercept_body_text.get('1.0', 'end')
    
    # Parse headers
    modified_headers = parse_headers(headers_text)
    
    # Envia resposta
    response_data = {
        'action': 'forward',
        'modified_headers': modified_headers,
        'modified_body': body_text
    }
    config.add_intercept_response(response_data)
    
    # Reseta UI
    self._reset_intercept_ui()
```

#### Drop
```python
def drop_request(self):
    """Cancela requisição"""
    response_data = {'action': 'drop'}
    config.add_intercept_response(response_data)
    self._reset_intercept_ui()
```

## Thread Safety

O sistema usa `queue.Queue()` do Python que é **thread-safe**:

- **Proxy Thread**: Roda o mitmproxy em thread separada
- **GUI Thread**: Thread principal do Tkinter
- **Queue**: Permite comunicação segura entre threads

## Timeouts

1. **GUI Polling**: 100ms (0.1s)
   - Verifica fila de requisições rapidamente
   - Não bloqueia a UI

2. **User Decision**: 300s (5 minutos)
   - Tempo máximo para usuário decidir
   - Se passar, requisição é automaticamente cancelada

3. **Queue Get**: Configurável
   - GUI: 0.01s (não bloqueia)
   - Addon: 300s (bloqueia até decisão)

## Estados da UI

```
INTERCEPT OFF
├── Botão: "Intercept is OFF" (vermelho)
├── Forward: Disabled
└── Drop: Disabled

INTERCEPT ON (aguardando)
├── Botão: "Intercept is ON" (verde)
├── Forward: Disabled
├── Drop: Disabled
└── Campos: Vazios

INTERCEPT ON (com requisição)
├── Botão: "Intercept is ON" (verde)
├── Forward: Enabled
├── Drop: Enabled
└── Campos: Preenchidos com dados da requisição

AFTER ACTION (Forward/Drop)
└── Volta para "aguardando"
```

## Exemplo de Uso

1. Usuário inicia proxy
2. Usuário clica "Intercept is OFF" → vira "Intercept is ON"
3. Usuário navega para http://example.com/login
4. Requisição POST é interceptada
5. GUI mostra:
   ```
   Método: POST
   URL: http://example.com/login
   Headers:
     Host: example.com
     Content-Type: application/x-www-form-urlencoded
   Body:
     username=admin&password=123
   ```
6. Usuário edita body:
   ```
   username=hacker&password=123
   ```
7. Usuário clica "Forward"
8. Requisição é enviada com modificação
9. UI reseta para aguardar próxima requisição
