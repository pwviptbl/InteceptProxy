# Arquitetura e Fluxo do InteceptProxy

## Visão Geral da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                      InteceptProxy System                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────┐               │
│  │   ProxyGUI      │         │  InterceptConfig │               │
│  │  (Interface)    │────────▶│  (Configuração)  │               │
│  │                 │         │                  │               │
│  │ - Adicionar     │         │ - Load/Save JSON │               │
│  │ - Remover       │         │ - Manage Rules   │               │
│  │ - Ativar/Parar  │         │ - Toggle Rules   │               │
│  └─────────────────┘         └──────────────────┘               │
│         │                              │                         │
│         │                              │                         │
│         ▼                              ▼                         │
│  ┌──────────────────────────────────────────┐                   │
│  │         InterceptAddon                   │                   │
│  │      (Lógica de Interceptação)           │                   │
│  │                                           │                   │
│  │  - Intercepta Requisições HTTP/HTTPS     │                   │
│  │  - Aplica Regras de Modificação          │                   │
│  │  - Modifica Parâmetros GET/POST          │                   │
│  └──────────────────────────────────────────┘                   │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────────────────────────────┐                   │
│  │         mitmproxy                         │                   │
│  │      (Proxy HTTP/HTTPS Engine)            │                   │
│  │                                           │                   │
│  │  - Escuta na porta 8080                  │                   │
│  │  - Gerencia conexões                      │                   │
│  │  - Encaminha requisições                  │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Fluxo de Dados

```
    Navegador                Proxy                Servidor
        │                      │                     │
        │  1. Request          │                     │
        │ ──────────────────▶  │                     │
        │                      │                     │
        │                      │  2. Intercepta      │
        │                      │     e Verifica      │
        │                      │     Regras          │
        │                      │                     │
        │                      │  3. Modifica        │
        │                      │     Parâmetros      │
        │                      │                     │
        │                      │  4. Forward         │
        │                      │ ──────────────────▶ │
        │                      │                     │
        │                      │  5. Response        │
        │                      │ ◀────────────────── │
        │                      │                     │
        │  6. Response         │                     │
        │ ◀──────────────────  │                     │
        │                      │                     │
```

## Fluxo de Interceptação Detalhado

```
┌─────────────────────────────────────────────────────────────┐
│  1. Requisição Chega no Proxy                               │
│     GET http://exemplo.com/contato?Titulo=original&Nome=Joao│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. InterceptAddon.request() é chamado                      │
│     - Extrai host: exemplo.com                              │
│     - Extrai path: /contato                                 │
│     - Extrai params: {Titulo: "original", Nome: "Joao"}     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Itera sobre todas as regras                             │
│     Regra 1: {                                              │
│       host: "exemplo.com",                                  │
│       path: "/contato",                                     │
│       param_name: "Titulo",                                 │
│       param_value: "teste1",                                │
│       enabled: true                                         │
│     }                                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Verifica Match                                          │
│     ✓ "exemplo.com" in "exemplo.com"       → TRUE           │
│     ✓ "/contato" startswith "/contato"     → TRUE           │
│     ✓ enabled == true                      → TRUE           │
│                                                              │
│     → MATCH! Aplica modificação                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Modifica Parâmetro                                      │
│     params["Titulo"] = "teste1"                             │
│                                                              │
│     Nova Query String:                                      │
│     Titulo=teste1&Nome=Joao                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Log da Modificação                                      │
│     [GET] Modificado: Titulo=teste1 em                      │
│           http://exemplo.com/contato                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Encaminha Requisição Modificada                         │
│     GET http://exemplo.com/contato?Titulo=teste1&Nome=Joao  │
└─────────────────────────────────────────────────────────────┘
```

## Estrutura de Classes

```
InterceptConfig
├── __init__()
│   └── Carrega configuração do JSON
├── load_config()
│   └── Lê intercept_config.json
├── save_config()
│   └── Salva no intercept_config.json
├── add_rule(host, path, param_name, param_value)
│   └── Adiciona nova regra e salva
├── remove_rule(index)
│   └── Remove regra e salva
├── toggle_rule(index)
│   └── Ativa/desativa regra e salva
└── get_rules()
    └── Retorna lista de regras


InterceptAddon
├── __init__(config)
│   └── Recebe InterceptConfig
└── request(flow)
    ├── Para cada regra:
    │   ├── Verifica match (host + path)
    │   ├── Se GET: modifica query string
    │   └── Se POST: modifica form data
    └── Encaminha requisição modificada


ProxyGUI
├── __init__()
│   ├── Cria janela Tkinter
│   └── Inicializa InterceptConfig
├── setup_ui()
│   ├── Cria frames e widgets
│   └── Configura layout
├── add_rule()
│   └── Adiciona regra via GUI
├── remove_rule()
│   └── Remove regra selecionada
├── toggle_rule()
│   └── Ativa/desativa regra
├── refresh_rules_list()
│   └── Atualiza TreeView
├── start_proxy()
│   └── Inicia mitmproxy em thread
└── run()
    └── Inicia mainloop do Tkinter
```

## Formato do Arquivo de Configuração

```json
{
  "rules": [
    {
      "host": "exemplo.com",        // Host a interceptar
      "path": "/contato",            // Caminho da URL
      "param_name": "Titulo",        // Nome do parâmetro
      "param_value": "teste1",       // Novo valor
      "enabled": true                // Regra ativa?
    }
  ]
}
```

## Estados do Sistema

```
┌───────────────┐
│   STOPPED     │  Proxy não está rodando
│               │  - Pode adicionar/remover regras
│               │  - Pode editar configurações
└───────┬───────┘
        │ start_proxy()
        ▼
┌───────────────┐
│   RUNNING     │  Proxy está rodando
│               │  - Interceptando requisições
│               │  - Aplicando regras
│               │  - Pode adicionar regras (requer restart)
└───────┬───────┘
        │ stop_proxy()
        ▼
┌───────────────┐
│   STOPPING    │  Encerrando proxy
│               │  - Finalizando conexões
│               │  - Salvando estado
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   STOPPED     │  Retorna ao estado inicial
└───────────────┘
```

## Tipos de Requisições Suportadas

### GET - Query String
```
Antes:  http://site.com/page?param=old&other=value
Depois: http://site.com/page?param=new&other=value
```

### POST - Form Data (application/x-www-form-urlencoded)
```
Antes:  param=old&other=value
Depois: param=new&other=value
```

## Componentes Externos

1. **mitmproxy** (10.1.5)
   - Engine principal de proxy
   - Intercepta HTTP/HTTPS
   - Gerencia certificados SSL

2. **Tkinter**
   - Interface gráfica
   - Parte do Python padrão
   - Multiplataforma

3. **JSON**
   - Persistência de configuração
   - Formato legível e editável

## Segurança e Privacidade

```
┌──────────────────────────────────────────────────────┐
│  Considerações de Segurança                          │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ✓ Configurações salvas localmente                   │
│  ✓ Sem comunicação externa                           │
│  ✓ Proxy local (localhost:8080)                      │
│  ✓ Código aberto e auditável                         │
│                                                       │
│  ⚠️ Certificado CA instalado (para HTTPS)            │
│  ⚠️ Arquivo de config pode conter dados sensíveis    │
│  ⚠️ Use apenas em ambientes de desenvolvimento       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Performance

- **Latência**: ~1-5ms por requisição interceptada
- **Throughput**: Limitado pelo mitmproxy (~1000 req/s)
- **Memória**: ~50-100MB (varia com número de conexões)
- **CPU**: Mínimo (<1% em idle, <10% sob carga)

## Limitações Técnicas

1. **Tipos de Conteúdo POST**
   - ✓ application/x-www-form-urlencoded
   - ✗ multipart/form-data (não suportado)
   - ✗ application/json (não suportado)

2. **Match de Regras**
   - Usa substring match para host
   - Usa startswith para path
   - Case-sensitive

3. **Concorrência**
   - Single-threaded (Tkinter GUI)
   - mitmproxy é multi-threaded
   - Regras aplicadas sequencialmente
