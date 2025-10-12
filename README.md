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
- ✅ **NOVO:** Histórico de requisições com filtros avançados
- ✅ **NOVO:** Visualização detalhada de Request/Response
- ✅ **NOVO:** Filtros por método HTTP e regex de domínio
- ✅ **NOVO:** Interface de Linha de Comando (CLI) para gerenciamento de regras e execução headless

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
pip install -r requirements.txt
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

Para mais informações sobre o histórico, veja [HISTORY_GUIDE.md](HISTORY_GUIDE.md)

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
├── requirements.txt        # Dependências
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
