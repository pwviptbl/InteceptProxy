# Guia de Uso - InteceptProxy

## Visão Geral

O InteceptProxy é um proxy HTTP que intercepta requisições para domínios específicos e modifica parâmetros configurados antes de encaminhar a requisição.

## Modos de Operação

### 1. Modo GUI (Recomendado para uso desktop)

```bash
python intercept_proxy.py
```

Interface gráfica completa com:
- Controle visual do proxy (Iniciar/Parar)
- Adicionar/remover regras facilmente
- Ativar/desativar regras individualmente
- Visualização de todas as regras configuradas

### 2. Modo Headless (Para servidores/automação)

```bash
python run_proxy_headless.py
```

Executa o proxy sem interface gráfica, ideal para:
- Servidores Linux sem GUI
- Ambientes de automação
- Docker containers
- CI/CD pipelines

## Configuração de Regras

### Via Interface Gráfica

1. **Abra a aplicação**: `python intercept_proxy.py`
2. **Preencha os campos**:
   - Host/Domínio: O domínio a interceptar (ex: `exemplo.com`)
   - Caminho: O path da URL (ex: `/contato`)
   - Nome do Parâmetro: O parâmetro a modificar (ex: `Titulo`)
   - Novo Valor: O valor de substituição (ex: `teste1`)
3. **Clique em "Adicionar Regra"**
4. **Inicie o proxy** com o botão "Iniciar Proxy"

### Via Arquivo de Configuração

1. **Crie/edite** `intercept_config.json`:

```json
{
  "rules": [
    {
      "host": "exemplo.com",
      "path": "/contato",
      "param_name": "Titulo",
      "param_value": "teste1",
      "enabled": true
    }
  ]
}
```

2. **Execute** o proxy:
   - GUI: `python intercept_proxy.py`
   - Headless: `python run_proxy_headless.py`

## Configuração do Navegador

### Firefox

1. Abra: **Preferências** → **Geral** → **Configurações de Rede** → **Configurações...**
2. Selecione: **Configuração manual de proxy**
3. Configure:
   - HTTP Proxy: `localhost`
   - Porta: `8080`
4. Marque: **"Usar este servidor proxy para todos os protocolos"**
5. Clique em **OK**

### Chrome / Edge

**Opção 1: Extensão Proxy SwitchyOmega**
1. Instale a extensão "Proxy SwitchyOmega"
2. Configure um novo perfil:
   - Protocolo: HTTP
   - Servidor: `localhost`
   - Porta: `8080`

**Opção 2: Configurações do Sistema**
- Windows: Configurações → Rede e Internet → Proxy
- macOS: Preferências do Sistema → Rede → Avançado → Proxies

## Exemplos de Uso

### Exemplo 1: Modificar parâmetro GET

**Configuração:**
```json
{
  "host": "exemplo.com",
  "path": "/busca",
  "param_name": "q",
  "param_value": "python"
}
```

**Comportamento:**
- URL original: `http://exemplo.com/busca?q=java&page=1`
- URL modificada: `http://exemplo.com/busca?q=python&page=1`

### Exemplo 2: Modificar parâmetro POST

**Configuração:**
```json
{
  "host": "site.com",
  "path": "/login",
  "param_name": "username",
  "param_value": "admin"
}
```

**Comportamento:**
- Formulário original: `username=user123&password=pass`
- Formulário modificado: `username=admin&password=pass`

### Exemplo 3: Múltiplas regras

```json
{
  "rules": [
    {
      "host": "api.exemplo.com",
      "path": "/v1/users",
      "param_name": "limit",
      "param_value": "100",
      "enabled": true
    },
    {
      "host": "site.com",
      "path": "/contact",
      "param_name": "subject",
      "param_value": "Teste Automatizado",
      "enabled": false
    }
  ]
}
```

## Gerenciamento de Regras

### Ativar/Desativar Regras

**Via GUI:**
1. Selecione a regra na lista
2. Clique em "Ativar/Desativar Regra"

**Via JSON:**
```json
{
  "enabled": false  // Desativa a regra
}
```

### Remover Regras

**Via GUI:**
1. Selecione a regra na lista
2. Clique em "Remover Regra Selecionada"

**Via JSON:**
- Delete o objeto da regra do array

## HTTPS e Certificados

Para interceptar HTTPS, você precisa instalar o certificado CA do mitmproxy:

1. **Inicie o proxy**
2. **Configure o navegador** para usar o proxy
3. **Acesse**: http://mitm.it
4. **Baixe e instale** o certificado para seu sistema operacional
5. **Reinicie o navegador**

### Instalação do Certificado

**Windows:**
1. Baixe o certificado em http://mitm.it
2. Duplo-clique no arquivo `.cer`
3. Instale no "Autoridades de Certificação Raiz Confiáveis"

**macOS:**
1. Baixe o certificado
2. Abra o "Acesso às Chaves"
3. Importe o certificado
4. Marque como "Sempre Confiar"

**Linux:**
```bash
# Ubuntu/Debian
sudo cp mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
sudo update-ca-certificates

# Firefox específico
# Preferences → Privacy & Security → Certificates → View Certificates → Import
```

## Logs e Debug

### Ver requisições interceptadas

O proxy imprime logs no console quando modifica parâmetros:

```
[GET] Modificado: Titulo=teste1 em http://exemplo.com/contato
[POST] Modificado: id=999 em http://test.com/api
```

### Habilitar logs detalhados

Edite o comando de inicialização em `intercept_proxy.py`:

```python
mitmdump([
    '--listen-port', '8080',
    '--set', 'flow_detail=3',  # Aumenta verbosidade
    '--set', 'confdir=~/.mitmproxy'
])
```

## Solução de Problemas

### Porta 8080 já em uso

**Erro:** `Address already in use`

**Solução:** Mude a porta no código:
```python
'--listen-port', '8081'  # Use outra porta
```

### Certificado HTTPS inválido

**Erro:** `SSL certificate error`

**Solução:** 
1. Acesse http://mitm.it
2. Instale o certificado CA
3. Reinicie o navegador

### Regras não estão funcionando

**Verifique:**
1. A regra está ativada (enabled: true)
2. O host e path correspondem exatamente
3. O parâmetro existe na requisição
4. O navegador está configurado para usar o proxy

### GUI não inicia

**Erro:** `No module named 'tkinter'`

**Solução:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Ou use o modo headless
python run_proxy_headless.py
```

## Segurança

⚠️ **Avisos Importantes:**

1. **Não use em redes públicas** sem criptografia
2. **Proteja o arquivo de configuração** - pode conter dados sensíveis
3. **Use apenas para testes** em ambientes controlados
4. **Não intercepte tráfego de terceiros** sem autorização
5. **Respeite a privacidade** e termos de serviço dos sites

## Limitações

- Funciona apenas com HTTP e HTTPS (com certificado instalado)
- Não intercepta WebSocket diretamente
- Suporta apenas `application/x-www-form-urlencoded` para POST
- Match de host/path é por substring (use caminhos específicos)

## Casos de Uso

✅ **Recomendado:**
- Testes de desenvolvimento
- QA e automação de testes
- Debug de integrações
- Desenvolvimento de APIs

❌ **Não Recomendado:**
- Produção
- Interceptação não autorizada
- Violação de termos de serviço
- Atividades maliciosas

## Contribuindo

Para reportar bugs ou sugerir melhorias, abra uma issue no GitHub.

## Licença

Código aberto - use com responsabilidade.
