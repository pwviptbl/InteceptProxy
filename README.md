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

## Uso

### 1. Iniciar a Aplicação

Execute o script principal:
```bash
python intercept_proxy.py
```

### 2. Configurar Regras de Interceptação

Na interface gráfica:

1. **Host/Domínio**: Digite o domínio a ser interceptado (ex: `exemplo.com`)
2. **Caminho**: Digite o caminho da rota (ex: `/contato`)
3. **Nome do Parâmetro**: Digite o nome do parâmetro a ser modificado (ex: `Titulo`)
4. **Novo Valor**: Digite o valor que substituirá o original (ex: `teste1`)
5. Clique em **"Adicionar Regra"**

### 3. Iniciar o Proxy

Clique no botão **"Iniciar Proxy"**. O servidor será iniciado na porta 8080.

### 4. Configurar o Navegador

Configure seu navegador para usar o proxy:

- **Host/IP**: `localhost` ou `127.0.0.1`
- **Porta**: `8080`

#### Exemplo no Firefox:
1. Configurações → Geral → Configurações de Rede
2. Configurar Proxy Manualmente
3. HTTP Proxy: `localhost`, Porta: `8080`
4. Marcar "Usar este proxy para todos os protocolos"

#### Exemplo no Chrome:
Use as configurações de sistema ou extensões como "Proxy SwitchyOmega"

### 5. Navegação

Navegue normalmente. Quando acessar uma URL que corresponda às regras configuradas, os parâmetros serão automaticamente substituídos.

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
├── intercept_proxy.py       # Script principal com GUI e lógica do proxy
├── requirements.txt          # Dependências Python
├── intercept_config.json     # Arquivo de configuração (gerado automaticamente)
└── README.md                 # Este arquivo
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

## Solução de Problemas

### Certificado HTTPS
Se precisar interceptar HTTPS, instale o certificado do mitmproxy:
1. Com o proxy rodando, acesse: http://mitm.it
2. Siga as instruções para instalar o certificado no seu sistema

### Porta já em uso
Se a porta 8080 já estiver em uso, você pode modificar a linha no código:
```python
mitmdump(['-s', __file__, '--listen-port', '8080', ...])
```

## Licença

Este projeto é de código aberto.
