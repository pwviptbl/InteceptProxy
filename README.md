# InteceptProxy

Intercepta requisições HTTP para um determinado domínio e altera parâmetros específicos antes de enviar a requisição.

## Descrição

Aplicação Python com interface gráfica que permite configurar regras de interceptação para modificar parâmetros de requisições HTTP. Quando o navegador envia uma requisição para uma rota configurada, o proxy intercepta, modifica apenas os parâmetros especificados e encaminha a requisição mantendo todos os outros parâmetros originais.

## Funcionalidades

- ✅ Interface gráfica intuitiva (Tkinter)
- ✅ Configuração de múltiplas regras de interceptação
- ✅ Suporte para GET (query string) e POST (form data)
- ✅ Ativar/desativar regras individualmente
- ✅ Persistência de configurações em JSON
- ✅ Servidor proxy HTTP na porta 8080
- ✅ **Intercept Manual (Forward/Drop)** - Funcionalidade inspirada no Burp Suite
- ✅ **WebSocket Support** 🔌 - Interceptação e monitoramento de WebSocket:
  - Listagem de conexões WebSocket ativas e fechadas
  - Visualização de mensagens enviadas/recebidas
  - Suporte a mensagens de texto e binárias
  - Histórico completo por conexão
- ✅ **Intruder Avançado** 💥 - Ferramenta completa de ataque automatizado:
  - 4 tipos de ataque (Sniper, Battering Ram, Pitchfork, Cluster Bomb)
  - Múltiplas posições de payload (§markers§)
  - Payload processing (URL encode, Base64, MD5, SHA256, prefix/suffix)
  - Grep extraction (extração de dados via regex)
  - Resource pool management (controle de threads)
- ✅ **Scanner de Vulnerabilidades** 🔐 - Detecção automática de:
  - SQL Injection
  - XSS (Cross-Site Scripting)
  - CSRF (Cross-Site Request Forgery)
  - Path Traversal
  - CVEs conhecidas
  - Informações sensíveis expostas
- ✅ **Spider/Crawler** 🕷️ - Descoberta automática de:
  - URLs e endpoints
  - Formulários e seus campos
  - Estrutura do site (sitemap)
  - Parâmetros de query strings
- ✅ **Comparador de Requisições** 🔀 - Comparação lado a lado:
  - Diff visual de requisições e respostas
  - Highlighting automático de diferenças
  - Útil para encontrar tokens CSRF e mudanças sutis
  - Algoritmo inteligente usando difflib
- ✅ Histórico de requisições com filtros avançados
- ✅ Visualização detalhada de Request/Response
- ✅ Filtros por método HTTP e regex de domínio
- ✅ Interface de Linha de Comando (CLI) para gerenciamento de regras e execução headless

## Instalação

### Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/pwviptbl/InteceptProxy.git
cd InteceptProxy
```

2. Instale as dependências:
```bash
pip install -r config/requirements.txt
```

### Ambiente Virtual

Para isolar as dependências do projeto, é recomendado usar um ambiente virtual.

1. Criar o ambiente virtual:
```bash
python -m venv .venv
```

2. Ativar o ambiente virtual:
   - No Windows:
```bash
.venv\Scripts\activate
```
   - No Linux/Mac:
```bash
source .venv/bin/activate
```

3. Para desativar:
```bash
deactivate
```

> 💡 Lembre-se de ativar o ambiente virtual antes de instalar as dependências e executar o projeto.

## Uso

### 1. Iniciar a Aplicação

Execute o script principal:
```bash
python intercept_proxy.py
```

### 2. Configurar Regras de Interceptação

Na interface gráfica, vá para a aba **"Regras de Interceptação"**:

1. **Host/Domínio**: Digite o domínio a ser interceptado (ex: `exemplo.com`)
2. **Caminho**: Digite o caminho da rota (ex: `/contato`)
3. **Nome do Parâmetro**: Digite o nome do parâmetro a ser modificado (ex: `Titulo`)
4. **Novo Valor**: Digite o valor que substituirá o original (ex: `teste1`)
5. Clique em **"Adicionar Regra"**

### 3. Visualizar Histórico de Requisições

Na aba **"Histórico de Requisições"**:

1. **Filtros**: Use os filtros para encontrar requisições específicas
   - Filtrar por método (GET, POST, etc.)
   - Filtrar por domínio usando regex (ex: `google.com|facebook.com`)
2. **Lista**: Veja todas as requisições capturadas com host, data, hora, método e status
3. **Detalhes**: Clique em uma requisição para ver detalhes completos
   - Aba "Request": Headers e body da requisição
   - Aba "Response": Status, headers e body da resposta

Para mais informações sobre o histórico, veja [docs/HISTORY_GUIDE.md](docs/HISTORY_GUIDE.md)

### 3.1. Intercept Manual (Forward/Drop)

Na aba **"Intercept Manual"**, você pode pausar requisições e modificá-las manualmente antes de enviá-las:

1. **Ativar Intercept**: 
   - Clique no botão "Intercept is OFF" para ativar
   - O botão ficará verde: "Intercept is ON"
   
2. **Interceptar Requisição**:
   - Quando uma requisição for feita, ela aparecerá na aba
   - Você verá: Método, URL, Headers e Body
   
3. **Modificar Requisição**:
   - Edite os headers no campo "Headers"
   - Edite o body no campo "Body"
   
4. **Tomar Ação**:
   - **Forward**: Envia a requisição (com suas modificações)
   - **Drop**: Cancela a requisição (não envia ao servidor)

5. **Desativar Intercept**:
   - Clique em "Intercept is ON" para desativar
   - As requisições voltarão a passar normalmente

> 💡 **Dica**: Esta funcionalidade é inspirada no Burp Suite e é ideal para testes manuais de segurança e análise de requisições.

Para mais informações sobre o Intercept Manual, veja [docs/INTERCEPT_MANUAL_FEATURE.md](docs/INTERCEPT_MANUAL_FEATURE.md)

### 3.1.5. Intruder Avançado (Ataques Automatizados) 💥

Na aba **"💥 Intruder"**, você pode realizar ataques automatizados com múltiplas requisições:

1. **Marcar Posições de Payload**:
   - Use `§...§` para marcar onde inserir payloads
   - Exemplo: `GET /login?user=§admin§&pass=§123§`
   - Selecione texto e clique "📋 Marcar Posições" para facilitar

2. **Escolher Tipo de Ataque**:
   - **Sniper**: Testa cada posição individualmente (fuzzing)
   - **Battering Ram**: Mesmo payload em todas as posições
   - **Pitchfork**: Combina sets em paralelo (credenciais)
   - **Cluster Bomb**: Todas as combinações possíveis (brute-force)

3. **Configurar Payloads**:
   - **Payload Set 1**: Arquivo .txt com payloads (obrigatório)
   - **Payload Set 2**: Arquivo .txt adicional (para Pitchfork/Cluster Bomb)

4. **Processamento** (opcional):
   - ✓ URL Encode, Base64, MD5 Hash
   - Prefix/Suffix para adicionar texto aos payloads

5. **Grep Extraction** (opcional):
   - Use regex para extrair dados das respostas
   - Exemplo: `token=([a-zA-Z0-9]+)` para capturar tokens

6. **Iniciar Ataque**:
   - Ajuste threads (padrão: 10)
   - Clique "▶ Iniciar Ataque"
   - Monitore resultados em tempo real

**Exemplo de Uso - Brute Force**:
```
POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

username=§admin§&password=§password§
```

Com Pitchfork e dois arquivos (users.txt e passwords.txt), você testa combinações específicas.

> 💡 **Dica**: O Intruder é poderoso! Use com responsabilidade e apenas em ambientes autorizados.

Para mais informações detalhadas, veja [docs/INTRUDER_GUIDE.md](docs/INTRUDER_GUIDE.md)

### 3.2. Spider/Crawler (Descoberta Automática)

Na aba **"🕷️ Spider/Crawler"**, você pode descobrir automaticamente páginas, endpoints e formulários:

1. **Iniciar o Proxy**: 
   - Primeiro, certifique-se de que o proxy está em execução
   
2. **Configurar o Spider**:
   - **URL Inicial**: Digite a URL base do site a mapear (ex: `http://exemplo.com`)
   - **Profundidade Máxima**: Número de níveis de links a seguir (padrão: 3)
   - **Máximo de URLs**: Limite de URLs a descobrir (padrão: 1000)
   
3. **Iniciar Spider**:
   - Clique em "▶ Iniciar Spider"
   - O spider começará a descobrir automaticamente quando você navegar no site
   
4. **Navegar no Site**:
   - Use seu navegador normalmente
   - O spider analisará automaticamente as respostas HTML
   - Links, formulários e endpoints serão descobertos
   
5. **Visualizar Descobertas**:
   - **URLs Descobertas**: Lista de todas as URLs encontradas
   - **Formulários**: Tabela com formulários, métodos e campos de entrada
   - **Sitemap**: Estrutura do site organizada por host e paths
   
6. **Exportar**:
   - Use o botão "💾 Exportar" para salvar o sitemap em arquivo
   - Use "📋 Copiar Todas" para copiar as URLs para a área de transferência
   
7. **Parar Spider**:
   - Clique em "⏹ Parar Spider" quando terminar
   - Use "🗑 Limpar Dados" para resetar os resultados

> 💡 **Dica**: O Spider funciona passivamente analisando as respostas do proxy. Quanto mais você navegar pelo site, mais completo será o mapeamento!

### 4. Iniciar o Proxy

Clique no botão **"Iniciar Proxy"**. O servidor será iniciado na porta 8080.

### 5. Configurar o Navegador

Configure seu navegador para usar o proxy:

- **Host/IP**: `localhost` ou `127.0.0.1`
- **Porta**: `8080`

> 💡 Para interceptar tráfego HTTPS é obrigatório instalar o certificado raiz do mitmproxy. Com o proxy em execução, acesse `http://mitm.it`, baixe o certificado para o seu sistema/navegador e instale-o na lista de autoridades confiáveis. Reinicie o navegador depois dessa etapa.

#### Exemplo no Firefox:
1. Configurações → Geral → Configurações de Rede
2. Configurar Proxy Manualmente
3. HTTP Proxy: `localhost`, Porta: `8080`
4. Marcar "Usar este proxy para todos os protocolos"

#### Exemplo no Chrome:
Use as configurações de sistema ou extensões como "Proxy SwitchyOmega"

### 6. Navegação

Navegue normalmente. Quando acessar uma URL que corresponda às regras configuradas, os parâmetros serão automaticamente substituídos.

### Uso via Linha de Comando (CLI)

A aplicação também pode ser controlada via terminal usando `cli.py`.

#### Listar Regras
```bash
python cli.py list
```

#### Adicionar uma Regra
```bash
python cli.py add --host exemplo.com --path /login --param user --value admin
```

#### Remover uma Regra
Use o índice (o número # da lista) para remover.
```bash
python cli.py remove 1
```

#### Ativar/Desativar uma Regra
Use o índice para ativar ou desativar.
```bash
python cli.py toggle 1
```

#### Iniciar o Proxy (Headless)
```bash
python cli.py run
```

#### Enviar Requisições em Massa (Sender)
Para automatizar testes de carga ou fuzzing, use o comando `send`. Crie um arquivo `lista.txt` com um valor por linha.

```bash
# Exemplo de conteúdo para lista.txt
valor1
valor2
valor3
```

```bash
python cli.py send --url http://exemplo.com/api --file lista.txt --param userID --threads 10
```
Este comando enviará requisições para `http://exemplo.com/api?userID=valor1`, `.../api?userID=valor2`, etc., usando 10 threads simultâneas.

#### Obter Informações do Sistema
Para ajudar a decidir o número de threads, use o comando `info`.
```bash
python cli.py info
```

## Exemplo de Uso

**Configuração:**
- Host: `exemplo.com`
- Caminho: `/contato`
- Parâmetro: `Titulo`
- Valor: `teste1`

**Comportamento:**

Quando você acessar `exemplo.com/contato?Titulo=original&Nome=João`, o proxy irá modificar para:
`exemplo.com/contato?Titulo=teste1&Nome=João`

O parâmetro `Titulo` é substituído por `teste1`, mas o parâmetro `Nome` permanece com seu valor original.

## Estrutura de Arquivos

```
InteceptProxy/
├── src/
│   ├── core/               # Lógica principal do proxy
│   └── ui/                 # Interface gráfica
├── cli.py                  # Ponto de entrada para a CLI
├── intercept_proxy.py      # Ponto de entrada para a GUI
├── config/                 # Arquivos de configuração
│   ├── requirements.txt    # Dependências
│   └── intercept_config.example.json  # Configuração de exemplo
└── README.md
```

## Gerenciamento de Regras

- **Adicionar Regra**: Preencha os campos e clique em "Adicionar Regra"
- **Remover Regra**: Selecione uma regra na lista e clique em "Remover Regra Selecionada"
- **Ativar/Desativar**: Selecione uma regra e clique em "Ativar/Desativar Regra"

## Tecnologias Utilizadas

- **Python 3**: Linguagem de programação
- **Tkinter**: Interface gráfica
- **mitmproxy**: Servidor proxy HTTP/HTTPS com capacidade de interceptação
- **JSON**: Armazenamento de configurações

## Observações

- O proxy intercepta apenas requisições HTTP. Para HTTPS, você precisará instalar o certificado CA do mitmproxy no navegador
- As configurações são salvas automaticamente no arquivo `intercept_config.json`
- O proxy mantém todos os parâmetros não configurados com seus valores originais
- **NOVO:** A atividade do proxy (regras aplicadas, erros) é registrada no arquivo `proxy.log` para facilitar a depuração.

## Solução de Problemas

### Certificado HTTPS
Se precisar interceptar HTTPS, instale o certificado do mitmproxy:
1. Com o proxy rodando, acesse: http://mitm.it
2. Siga as instruções para instalar o certificado no seu sistema
3. Reinicie o navegador para que ele reconheça a nova autoridade

### Porta já em uso
Se a porta 8080 já estiver em uso, você pode modificar a linha no código:
```python
mitmdump(['-s', __file__, '--listen-port', '8080', ...])
```

## Licença

Este projeto é de código aberto.
