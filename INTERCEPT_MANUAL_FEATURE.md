# Intercept Manual Feature - UI Description

## Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ InteceptProxy - Configurador                                       [_][□][X]│
├─────────────────────────────────────────────────────────────────────────────┤
│ Controle do Proxy                                                           │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ Status: Executando  [Iniciar Proxy] [Parar Proxy] [Pausar] Porta: 8080│   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [Regras] [Intercept Manual] [Histórico] [Repetição] [Sender] [Decoder] │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                         │ │
│ │ Controle de Interceptação                                              │ │
│ │ ┌───────────────────────────────────────────────────────────────────┐   │ │
│ │ │ Intercept: ON (verde)      [Intercept is ON]                     │   │ │
│ │ └───────────────────────────────────────────────────────────────────┘   │ │
│ │                                                                         │ │
│ │ Requisição Interceptada                                                │ │
│ │ ┌───────────────────────────────────────────────────────────────────┐   │ │
│ │ │ Método:  POST                                                     │   │ │
│ │ │ URL:     http://example.com/api/login                             │   │ │
│ │ │ Host:    example.com                                              │   │ │
│ │ │                                                                   │   │ │
│ │ │ Headers                                                           │   │ │
│ │ │ ┌─────────────────────────────────────────────────────────────┐   │   │ │
│ │ │ │ Host: example.com                                           │   │   │ │
│ │ │ │ Content-Type: application/x-www-form-urlencoded             │   │   │ │
│ │ │ │ Content-Length: 29                                          │   │   │ │
│ │ │ │ User-Agent: Mozilla/5.0                                     │   │   │ │
│ │ │ └─────────────────────────────────────────────────────────────┘   │   │ │
│ │ │                                                                   │   │ │
│ │ │ Body                                                              │   │ │
│ │ │ ┌─────────────────────────────────────────────────────────────┐   │   │ │
│ │ │ │ username=admin&password=test123                             │   │   │ │
│ │ │ │                                                             │   │   │ │
│ │ │ └─────────────────────────────────────────────────────────────┘   │   │ │
│ │ └───────────────────────────────────────────────────────────────────┘   │ │
│ │                                                                         │ │
│ │ [  Forward  ]  [  Drop  ]    Aguardando requisição...                  │ │
│ │                                                                         │ │
│ │ Instruções                                                              │ │
│ │ ┌───────────────────────────────────────────────────────────────────┐   │ │
│ │ │ 1. Clique em "Intercept is OFF" para ativar a interceptação      │   │ │
│ │ │ 2. Quando uma requisição for interceptada, ela aparecerá aqui    │   │ │
│ │ │ 3. Você pode editar os headers e o body da requisição            │   │ │
│ │ │ 4. Clique em "Forward" para enviar a requisição (com mods)       │   │ │
│ │ │ 5. Clique em "Drop" para cancelar a requisição                   │   │ │
│ │ └───────────────────────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features Implemented

### 1. **ON/OFF Toggle Button**
- Located at the top of the Intercept Manual tab
- Shows current state: "Intercept is OFF" (red) or "Intercept is ON" (green)
- Requires proxy to be running before enabling

### 2. **Request Information Display**
- **Method**: Shows HTTP method (GET, POST, etc.)
- **URL**: Full URL of the intercepted request
- **Host**: Domain/host of the request

### 3. **Editable Headers**
- Scrollable text area showing all request headers
- Can be edited before forwarding
- One header per line in format: "Header-Name: value"

### 4. **Editable Body**
- Scrollable text area showing request body
- Can be edited before forwarding
- Shows form data, JSON, or raw content

### 5. **Action Buttons**
- **Forward Button**: 
  - Sends the request to the server
  - Includes any modifications made to headers or body
  - Disabled when no request is intercepted
  
- **Drop Button**:
  - Cancels the request (doesn't send it to the server)
  - Immediately kills the connection
  - Disabled when no request is intercepted

### 6. **Automatic Queue Handling**
- Checks for intercepted requests every 100ms
- Automatically switches to Intercept tab when request is captured
- Shows visual feedback with enabled/disabled states

## How It Works (Backend)

1. **When Intercept is ON**:
   - Every HTTP request is paused by the proxy addon
   - Request data is added to a queue
   - Addon waits for user decision (timeout: 5 minutes)

2. **User Decision**:
   - **Forward**: Sends response with 'action': 'forward' and optional modifications
   - **Drop**: Sends response with 'action': 'drop'
   - **Timeout**: After 5 min, request is automatically dropped

3. **Queue System**:
   - Uses Python `queue.Queue()` for thread-safe operations
   - One queue for intercepted requests
   - One queue for user responses
   - Both queues can be cleared when intercept is disabled

## Comparison with Burp Suite

✅ **Similar Features**:
- ON/OFF toggle for intercept
- View and edit request before sending
- Forward button to send request
- Drop button to cancel request
- Display of method, URL, headers, and body

🎯 **Differences**:
- Burp Suite has more advanced filtering options
- Burp Suite can queue multiple requests
- This implementation is simpler and more straightforward

## Usage Example

1. Start the proxy
2. Configure browser to use proxy (localhost:8080)
3. Go to "Intercept Manual" tab
4. Click "Intercept is OFF" button (turns to "Intercept is ON")
5. Navigate to a website in your browser
6. Request appears in the Intercept tab
7. Edit headers/body if needed
8. Click "Forward" to send or "Drop" to cancel
9. Repeat for each request
10. Click "Intercept is ON" to disable interception
