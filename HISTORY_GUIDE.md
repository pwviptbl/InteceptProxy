# Histórico de Requisições - Documentação

## Nova Funcionalidade: Aba de Histórico

### Visão Geral
A nova aba "Histórico de Requisições" permite visualizar todas as requisições HTTP capturadas pelo proxy, com filtros avançados e detalhes completos de cada requisição e resposta.

## Interface da Aba de Histórico

### 1. Filtros (Parte Superior)
```
┌─────────────────────────────────────────────────────────────────┐
│ Filtros                                                         │
│ ┌─────────────┬──────────────────────────────────────────────┐ │
│ │ Método:     │ [Dropdown: Todos ▼]                          │ │
│ │ Domínio:    │ [Campo de texto para regex]                  │ │
│ │             │ (Use '|' para múltiplos: google.com|fb.com)  │ │
│ │             │ [Aplicar Filtros] [Limpar Histórico]         │ │
│ └─────────────┴──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Opções de Método:**
- Todos
- GET
- POST
- PUT
- DELETE
- PATCH
- HEAD
- OPTIONS

**Filtro de Domínio (Regex):**
- Suporta expressões regulares
- Use `|` para múltiplos domínios: `google.com|facebook.com|twitter.com`
- Exemplos:
  - `exemplo.com` - Filtra apenas exemplo.com
  - `google|facebook` - Filtra Google e Facebook
  - `api\..*\.com` - Filtra todos os domínios que começam com "api."

### 2. Lista de Requisições (Parte do Meio)
```
┌─────────────────────────────────────────────────────────────────┐
│ Requisições Capturadas                                         │
│ ┌──────────┬──────────┬──────────┬────────┬────────┬─────────┐ │
│ │ Host     │ Data     │ Hora     │ Método │ Status │ URL     │ │
│ ├──────────┼──────────┼──────────┼────────┼────────┼─────────┤ │
│ │exemplo.com│15/01/2025│14:30:15 │ GET    │ 200   │http://..│ │
│ │google.com│15/01/2025│14:30:16 │ POST   │ 201   │http://..│ │
│ │test.com  │15/01/2025│14:30:17 │ GET    │ 404   │http://..│ │
│ └──────────┴──────────┴──────────┴────────┴────────┴─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Colunas:**
- **Host**: Domínio da requisição
- **Data**: Data da captura (DD/MM/YYYY)
- **Hora**: Hora da captura (HH:MM:SS)
- **Método**: Tipo de requisição HTTP
- **Status**: Código de status HTTP da resposta
- **URL**: URL completa da requisição

### 3. Detalhes da Requisição (Parte Inferior)
Ao clicar em uma requisição na lista, os detalhes aparecem na parte inferior:

```
┌─────────────────────────────────────────────────────────────────┐
│ Detalhes da Requisição                                         │
│ ┌───────────┬───────────────────────────────────────────────┐  │
│ │ Request   │ Response                                      │  │
│ └───────────┴───────────────────────────────────────────────┘  │
│                                                                 │
│ [Conteúdo conforme a aba selecionada]                         │
└─────────────────────────────────────────────────────────────────┘
```

#### Aba "Request"
Mostra informações completas da requisição:
```
URL: http://exemplo.com/contato?Titulo=teste1
Método: GET
Host: exemplo.com
Path: /contato

Headers:
  User-Agent: Mozilla/5.0...
  Accept: text/html...
  Content-Type: application/x-www-form-urlencoded

Body:
[Conteúdo do corpo da requisição]
```

#### Aba "Response"
Mostra informações completas da resposta:
```
Status: 200

Headers:
  Content-Type: text/html; charset=utf-8
  Content-Length: 1234
  Server: nginx/1.18.0

Body:
[Conteúdo do corpo da resposta]
```

## Funcionalidades

### Captura Automática
- **Todas as requisições** que passam pelo proxy são automaticamente capturadas
- Armazena até **1000 requisições** (as mais antigas são removidas automaticamente)
- Atualiza a lista **a cada segundo** automaticamente

### Filtros em Tempo Real
- **Filtro por Método**: Selecione um método específico ou veja todos
- **Filtro por Domínio (Regex)**: 
  - Filtragem em tempo real enquanto você digita
  - Suporta expressões regulares complexas
  - Pode usar `|` para múltiplos domínios
  - Case-insensitive (não diferencia maiúsculas/minúsculas)

### Navegação
- **Clique** em qualquer requisição para ver os detalhes
- **Scroll** para navegar pelo histórico
- **Alternar entre abas** Request/Response para ver diferentes informações

### Limpeza
- Botão **"Limpar Histórico"** remove todas as requisições capturadas
- Confirmação antes de limpar para evitar perda acidental

## Exemplos de Uso

### Exemplo 1: Monitorar todas as requisições GET
1. Na aba "Histórico de Requisições"
2. Selecione "GET" no filtro de Método
3. Veja apenas requisições GET

### Exemplo 2: Filtrar múltiplos domínios
1. No campo "Domínio (regex)", digite: `google.com|facebook.com|twitter.com`
2. Pressione "Aplicar Filtros"
3. Veja apenas requisições para esses três domínios

### Exemplo 3: Encontrar requisições de API
1. No campo "Domínio (regex)", digite: `api\..*`
2. Veja todas as requisições para subdomínios que começam com "api."

### Exemplo 4: Analisar uma requisição específica
1. Encontre a requisição na lista
2. Clique nela
3. Veja os detalhes completos na aba "Request"
4. Alterne para a aba "Response" para ver a resposta

### Exemplo 5: Debug de requisições POST
1. Filtre por método "POST"
2. Clique em uma requisição POST
3. Na aba "Request", veja o corpo completo enviado
4. Na aba "Response", veja a resposta do servidor

## Integração com Regras de Interceptação

As requisições capturadas no histórico **incluem as modificações** feitas pelas regras de interceptação:

- Se uma regra modifica um parâmetro, o histórico mostra o **valor modificado**
- Útil para verificar se suas regras estão funcionando corretamente
- Compare a URL na lista com o que você esperava

## Limitações

- **Máximo de 1000 requisições**: Para evitar uso excessivo de memória
- **Não persiste entre sessões**: O histórico é limpo ao fechar o aplicativo
- **Requer proxy em execução**: Apenas captura quando o proxy está ativo

## Dicas

1. **Use filtros específicos** para encontrar requisições rapidamente
2. **Regex é poderoso**: Aprenda alguns padrões básicos de regex para filtrar melhor
3. **Limpe o histórico** periodicamente se estiver fazendo muitas requisições
4. **Verifique ambas as abas**: Request E Response para ter o contexto completo
5. **Combine filtros**: Use Método + Domínio para filtros muito específicos
