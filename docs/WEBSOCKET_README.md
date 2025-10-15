# WebSocket Support 🔌

O InteceptProxy agora suporta interceptação e monitoramento de conexões WebSocket!

## Funcionalidades Implementadas

### ✅ Listagem de Conexões WebSocket
- Visualize todas as conexões WebSocket capturadas pelo proxy
- Informações exibidas:
  - ID da conexão
  - Host
  - URL completa
  - Status (ativo/fechado)
  - Contador de mensagens
  - Timestamp de início

### ✅ Visualização de Mensagens
- Veja todas as mensagens trocadas em cada conexão
- Identifique a direção das mensagens:
  - Cliente → Servidor
  - Servidor → Cliente
- Suporte para:
  - Mensagens de texto (UTF-8)
  - Mensagens binárias (exibidas em hexadecimal)
- Informações de cada mensagem:
  - Timestamp preciso
  - Direção
  - Tamanho em bytes
  - Tipo (Texto/Binário)

### ✅ Conteúdo das Mensagens
- Visualize o conteúdo completo de cada mensagem
- Mensagens de texto são exibidas como strings
- Mensagens binárias são exibidas em formato hexadecimal

## Como Usar

### 1. Inicie o Proxy
- Clique em "Iniciar Proxy" na interface principal
- Configure seu navegador/aplicação para usar o proxy (localhost:8080)
- Instale o certificado SSL do mitmproxy se necessário (http://mitm.it)

### 2. Acesse a Aba WebSocket
- Navegue até a aba "WebSocket 🔌" na interface
- Aguarde as conexões WebSocket serem estabelecidas

### 3. Monitore Conexões
- A lista de conexões é atualizada automaticamente a cada 2 segundos
- Clique em uma conexão para ver suas mensagens
- Use o botão "Atualizar Lista" para forçar atualização manual

### 4. Visualize Mensagens
- Selecione uma conexão na lista superior
- As mensagens serão exibidas na lista do meio
- Clique em uma mensagem para ver seu conteúdo completo

### 5. Gerenciar Histórico
- Use "Limpar Histórico" para apagar todas as conexões e mensagens

## Arquitetura Técnica

### Componentes Principais

#### WebSocketHistory (`src/core/websocket_history.py`)
Gerencia o histórico de conexões e mensagens WebSocket:
- `add_connection()`: Registra nova conexão
- `add_message()`: Adiciona mensagem ao histórico
- `close_connection()`: Marca conexão como fechada
- `get_connections()`: Retorna todas as conexões
- `get_messages()`: Retorna mensagens de uma conexão

#### InterceptAddon (`src/core/addon.py`)
Intercepta eventos WebSocket do mitmproxy:
- `websocket_start()`: Chamado quando conexão é estabelecida
- `websocket_message()`: Chamado para cada mensagem
- `websocket_end()`: Chamado quando conexão é fechada

#### GUI (`src/ui/gui.py`)
Interface gráfica para WebSocket:
- `setup_websocket_tab()`: Cria a aba WebSocket
- `update_websocket_list()`: Atualiza lista periodicamente
- `on_ws_connection_select()`: Handler de seleção de conexão
- `on_ws_message_select()`: Handler de seleção de mensagem

## Funcionalidades Futuras

### ⚠️ Em Desenvolvimento
- **Modificação de Mensagens**: Editar mensagens antes de enviá-las
- **Reenvio de Mensagens**: Reenviar mensagens capturadas
- **Filtros Avançados**: Filtrar mensagens por conteúdo ou direção
- **Exportação**: Exportar histórico de mensagens para arquivo

## Exemplos de Uso

### Testar com WebSocket Echo Server
```bash
# 1. Inicie o proxy
# 2. Configure o navegador para usar o proxy
# 3. Acesse: wss://echo.websocket.org/
# 4. Envie mensagens e veja-as na aba WebSocket
```

### Monitorar Aplicação Real
```bash
# 1. Inicie o proxy
# 2. Configure a aplicação para usar o proxy
# 3. Use a aplicação normalmente
# 4. Todas as conexões WebSocket serão capturadas
```

## Limitações Conhecidas

1. **Modificação em Tempo Real**: Ainda não é possível modificar mensagens antes de enviá-las
2. **Reenvio**: Funcionalidade de reenvio ainda não implementada
3. **Histórico Limitado**: Mensagens são armazenadas apenas em memória

## Tecnologias Utilizadas

- **mitmproxy 12.1.2**: Engine de proxy com suporte a WebSocket
- **Python 3.12+**: Linguagem de programação
- **Tkinter**: Interface gráfica

## Contribuindo

Sinta-se livre para contribuir com melhorias! Áreas que precisam de atenção:
- [ ] Implementar modificação de mensagens em tempo real
- [ ] Adicionar funcionalidade de reenvio
- [ ] Criar filtros avançados
- [ ] Adicionar exportação de histórico
- [ ] Melhorar detecção de mensagens binárias vs texto

## Licença

Este projeto é open source.
