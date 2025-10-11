# Interface Visual - InteceptProxy

## Layout da Aplicação com Histórico

```
┌──────────────────────────────────────────────────────────────────────────┐
│ InteceptProxy - Configurador                                    [_][□][X] │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │ Controle do Proxy                                                  │   │
│ │ Status: Parado  [Iniciar Proxy] [Parar Proxy]  Porta: 8080        │   │
│ └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ ┌─────────────────────────┬──────────────────────────────────────┐  │ │
│ │ │ Regras de Interceptação │ Histórico de Requisições             │  │ │
│ │ └─────────────────────────┴──────────────────────────────────────┘  │ │
│ │                                                                      │ │
│ │  [Aba Selecionada: Regras de Interceptação]                         │ │
│ │  ┌──────────────────────────────────────────────────────────────┐  │ │
│ │  │ Adicionar Regra de Interceptação                             │  │ │
│ │  │ Host/Domínio: [exemplo.com     ] Caminho: [/contato        ] │  │ │
│ │  │ Parâmetro:    [Titulo          ] Valor:   [teste1          ] │  │ │
│ │  │                    [Adicionar Regra]                          │  │ │
│ │  └──────────────────────────────────────────────────────────────┘  │ │
│ │                                                                      │ │
│ │  ┌──────────────────────────────────────────────────────────────┐  │ │
│ │  │ Regras Configuradas                                          │  │ │
│ │  │ ┌──┬────────┬────────┬──────────┬────────┬────────┐         │  │ │
│ │  │ │# │Host    │Caminho │Parâmetro │Valor   │Status  │         │  │ │
│ │  │ ├──┼────────┼────────┼──────────┼────────┼────────┤         │  │ │
│ │  │ │1 │exemplo │/contato│Titulo    │teste1  │Ativo   │         │  │ │
│ │  │ └──┴────────┴────────┴──────────┴────────┴────────┘         │  │ │
│ │  └──────────────────────────────────────────────────────────────┘  │ │
│ │                                                                      │ │
│ │  [Remover Regra Selecionada] [Ativar/Desativar Regra]              │ │
│ │                                                                      │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

## Layout da Aba de Histórico

```
┌──────────────────────────────────────────────────────────────────────────┐
│ InteceptProxy - Configurador                                    [_][□][X] │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │ Controle do Proxy                                                  │   │
│ │ Status: Executando  [Iniciar Proxy] [Parar Proxy]  Porta: 8080    │   │
│ └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ ┌─────────────────────────┬──────────────────────────────────────┐  │ │
│ │ │ Regras de Interceptação │ Histórico de Requisições             │  │ │
│ │ └─────────────────────────┴──────────────────────────────────────┘  │ │
│ │                                                                      │ │
│ │  [Aba Selecionada: Histórico de Requisições]                        │ │
│ │                                                                      │ │
│ │  ┌──────────────────────────────────────────────────────────────┐  │ │
│ │  │ Filtros                                                      │  │ │
│ │  │ Método: [Todos ▼]  Domínio (regex): [google|facebook       ] │  │ │
│ │  │ (Use '|' para múltiplos: google.com|facebook.com)            │  │ │
│ │  │                 [Aplicar Filtros] [Limpar Histórico]         │  │ │
│ │  └──────────────────────────────────────────────────────────────┘  │ │
│ │                                                                      │ │
│ │  ┌──────────────────────────────────────────────────────────────┐  │ │
│ │  │ Requisições Capturadas                                       │  │ │
│ │  │ ┌──────────┬──────────┬────────┬────────┬──────┬──────────┐ │  │ │
│ │  │ │Host      │Data      │Hora    │Método  │Status│URL       │ │  │ │
│ │  │ ├──────────┼──────────┼────────┼────────┼──────┼──────────┤ │  │ │
│ │  │ │google.com│15/01/2025│14:30:15│GET     │200   │http://...│ │  │ │
│ │  │ │google.com│15/01/2025│14:30:16│POST    │201   │http://...│ │  │ │
│ │  │ │facebook..│15/01/2025│14:30:17│GET     │200   │http://...│ │  │ │
│ │  │ └──────────┴──────────┴────────┴────────┴──────┴──────────┘ │  │ │
│ │  └──────────────────────────────────────────────────────────────┘  │ │
│ │                                                                      │ │
│ │  ┌──────────────────────────────────────────────────────────────┐  │ │
│ │  │ Detalhes da Requisição                                       │  │ │
│ │  │ ┌────────┬──────────┐                                        │  │ │
│ │  │ │Request │Response  │                                        │  │ │
│ │  │ └────────┴──────────┘                                        │  │ │
│ │  │                                                               │  │ │
│ │  │ URL: http://google.com/search?q=test                         │  │ │
│ │  │ Método: GET                                                  │  │ │
│ │  │ Host: google.com                                             │  │ │
│ │  │ Path: /search                                                │  │ │
│ │  │                                                               │  │ │
│ │  │ Headers:                                                     │  │ │
│ │  │   User-Agent: Mozilla/5.0...                                │  │ │
│ │  │   Accept: text/html...                                       │  │ │
│ │  │                                                               │  │ │
│ │  │ Body:                                                         │  │ │
│ │  │ [Conteúdo do corpo da requisição...]                        │  │ │
│ │  └──────────────────────────────────────────────────────────────┘  │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

## Detalhes da Aba Response

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Detalhes da Requisição                                                   │
│ ┌────────┬──────────┐                                                    │
│ │Request │Response  │  <- Aba Response selecionada                       │
│ └────────┴──────────┘                                                    │
│                                                                           │
│ Status: 200                                                              │
│                                                                           │
│ Headers:                                                                 │
│   Content-Type: text/html; charset=utf-8                                │
│   Content-Length: 52468                                                  │
│   Server: gws                                                             │
│   Date: Mon, 15 Jan 2025 14:30:15 GMT                                   │
│                                                                           │
│ Body:                                                                     │
│ <!DOCTYPE html>                                                          │
│ <html lang="pt-BR">                                                      │
│ <head>                                                                   │
│   <title>Google</title>                                                  │
│   ...                                                                     │
│ </head>                                                                  │
│ <body>                                                                   │
│   [Conteúdo HTML completo da resposta...]                               │
│ </body>                                                                  │
│ </html>                                                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Fluxo de Uso

1. **Iniciar Aplicação** → Interface abre com duas abas
2. **Configurar Regras** → Aba "Regras de Interceptação"
3. **Iniciar Proxy** → Botão no topo
4. **Navegar no Browser** → Com proxy configurado
5. **Ver Histórico** → Aba "Histórico de Requisições"
6. **Filtrar Requisições** → Use os filtros de método e domínio
7. **Analisar Detalhes** → Clique em uma requisição
8. **Ver Request/Response** → Alterne entre as abas
