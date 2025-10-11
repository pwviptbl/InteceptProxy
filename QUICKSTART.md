# Quick Start Guide - InteceptProxy

## Instalação Rápida (3 passos)

### 1. Clone e instale
```bash
git clone https://github.com/pwviptbl/InteceptProxy.git
cd InteceptProxy
pip install -r requirements.txt
```

### 2. Execute a aplicação
```bash
# Com interface gráfica (recomendado)
python intercept_proxy.py

# Ou sem interface (headless)
python run_proxy_headless.py
```

### 3. Configure seu navegador
- **Proxy HTTP**: `localhost`
- **Porta**: `8080`

## Exemplo Prático

### Cenário: Modificar parâmetro "Titulo" em exemplo.com/contato

#### Opção A: Via Interface Gráfica

1. Execute: `python intercept_proxy.py`
2. Preencha os campos:
   - Host: `exemplo.com`
   - Caminho: `/contato`
   - Parâmetro: `Titulo`
   - Valor: `teste1`
3. Clique em "Adicionar Regra"
4. Clique em "Iniciar Proxy"
5. Configure seu navegador para usar o proxy
6. Acesse `exemplo.com/contato?Titulo=original`
   - O proxy modificará automaticamente para `Titulo=teste1`

#### Opção B: Via Arquivo de Configuração

1. Crie `intercept_config.json`:
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

2. Execute: `python run_proxy_headless.py`

3. Configure o navegador e acesse a URL

#### Opção C: Via Código Python

1. Execute: `python examples.py` (veja vários exemplos)

2. Ou crie seu próprio script:
```python
from intercept_proxy import InterceptConfig

config = InterceptConfig()
config.add_rule("exemplo.com", "/contato", "Titulo", "teste1")
print("Regra adicionada!")
```

3. Execute: `python run_proxy_headless.py`

## Verificação

### Como saber se está funcionando?

1. **Verifique o console**: Você verá mensagens como:
```
[GET] Modificado: Titulo=teste1 em http://exemplo.com/contato
```

2. **Inspecione a rede no navegador**:
   - Abra DevTools (F12)
   - Vá para a aba Network
   - Veja a requisição real enviada

3. **Verifique no servidor**: O servidor receberá o valor modificado

## Comandos Úteis

```bash
# Executar testes
python test_intercept.py

# Ver exemplos interativos
python examples.py

# Executar em modo headless
python run_proxy_headless.py

# Executar com GUI
python intercept_proxy.py
```

## Configuração do Navegador - Detalhado

### Firefox (Mais Fácil)

1. Menu (☰) → **Configurações**
2. Role até "Configurações de Rede"
3. Clique em **"Configurações..."**
4. Selecione **"Configuração manual de proxy"**
5. Preencha:
   - Proxy HTTP: `localhost`
   - Porta: `8080`
   - ☑ Usar este servidor proxy para todos os protocolos
6. **OK**

**Desativar depois:** Volte aqui e selecione "Sem proxy"

### Chrome / Edge

**Via Extensão (Recomendado):**

1. Instale "Proxy SwitchyOmega" da Chrome Web Store
2. Configure:
   - Nome: InteceptProxy
   - Protocolo: HTTP
   - Servidor: localhost
   - Porta: 8080
3. Ative o perfil no ícone da extensão

**Via Sistema (Windows):**

1. Configurações → Rede e Internet → Proxy
2. Configuração manual de proxy → **Ativar**
3. Endereço: `localhost:8080`
4. **Salvar**

**Desativar:** Desmarque "Usar um servidor proxy"

### Safari (macOS)

1. Preferências → Avançado → **"Alterar Configurações..."** (Proxies)
2. ☑ Proxy Web (HTTP)
3. Servidor: `localhost` : `8080`
4. **OK** → **Aplicar**

## Solução Rápida de Problemas

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: No module named 'mitmproxy'` | `pip install -r requirements.txt` |
| `No module named 'tkinter'` | Use `run_proxy_headless.py` ou instale tkinter |
| `Address already in use` | Porta 8080 ocupada - feche outra aplicação ou mude a porta |
| Regras não funcionam | Verifique: regra ativada? navegador configurado? host/path corretos? |
| HTTPS não funciona | Instale o certificado: acesse http://mitm.it |

## Próximos Passos

Após o Quick Start, consulte:

- **README.md** - Documentação completa
- **USAGE_GUIDE.md** - Guia detalhado de uso
- **ARCHITECTURE.md** - Como funciona internamente
- **examples.py** - Exemplos práticos

## Resumo de 30 Segundos

```bash
# Instalar
pip install mitmproxy

# Executar
python intercept_proxy.py

# Configurar navegador
# Proxy: localhost:8080

# Adicionar regra
# Host: exemplo.com
# Path: /contato
# Param: Titulo → teste1

# Pronto! 🎉
```

## Desinstalação

```bash
# Remover configuração do navegador
# (volte para "Sem proxy")

# Desinstalar dependências (opcional)
pip uninstall mitmproxy

# Remover pasta do projeto
cd ..
rm -rf InteceptProxy
```

## Suporte

- 📖 Documentação completa: Ver README.md
- 🐛 Problemas? Abra uma issue no GitHub
- 💡 Ideias? Contribuições são bem-vindas!

---

**Tempo estimado**: ~5 minutos do clone até a primeira interceptação funcionando! 🚀
