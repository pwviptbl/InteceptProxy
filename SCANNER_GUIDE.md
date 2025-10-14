# Scanner de Vulnerabilidades - InteceptProxy

## 📋 Visão Geral

O Scanner de Vulnerabilidades é uma funcionalidade integrada ao InteceptProxy que detecta automaticamente vulnerabilidades comuns de segurança em requisições e respostas HTTP. Este scanner transforma o InteceptProxy de um simples proxy HTTP em uma ferramenta de segurança profissional.

## 🎯 Funcionalidades

O scanner detecta automaticamente as seguintes vulnerabilidades:

### 1. SQL Injection 💉
Detecta possíveis vulnerabilidades de SQL Injection através de:
- Mensagens de erro de banco de dados (MySQL, PostgreSQL, Oracle, SQL Server, SQLite)
- Padrões específicos de erro SQL
- Sintaxe SQL exposta em respostas

**Exemplos de detecção:**
- `SQL syntax error`
- `mysql_fetch_array()`
- `ORA-01756`
- `unclosed quotation mark`

**Severidade:** High

### 2. XSS (Cross-Site Scripting) 🔓
Detecta XSS refletido verificando se payloads maliciosos da requisição são refletidos na resposta:
- Tags `<script>`
- Event handlers (onclick, onload, onerror, etc.)
- Protocolo `javascript:`
- Tags perigosas (iframe, object, embed)

**Exemplos de detecção:**
- `<script>alert(1)</script>`
- `<img onerror="alert(1)">`
- `javascript:void(0)`

**Severidade:** High

### 3. Path Traversal 📁
Detecta tentativas de acesso a arquivos do sistema:
- Múltiplos `../`
- Acesso a `/etc/passwd`
- Acesso a arquivos Windows (`win.ini`, `boot.ini`)
- Variações com URL encoding

**Exemplos de detecção:**
- `../../../../etc/passwd`
- `..%2f..%2f..%2f`
- Conteúdo do `/etc/passwd` na resposta

**Severidade:** Critical (se confirmado) / Medium (se tentativa)

### 4. CSRF (Cross-Site Request Forgery) 🔒
Detecta possível falta de proteção CSRF em requisições que modificam estado:
- Verifica presença de tokens CSRF em requisições POST, PUT, DELETE, PATCH
- Busca por indicadores comuns: `csrf`, `xsrf`, `_token`, `authenticity_token`

**Severidade:** Medium

### 5. Detecção de CVEs Conhecidas 🚨
Identifica versões de software com vulnerabilidades conhecidas:
- Apache 2.4.49/2.4.50 (Path Traversal)
- Log4j 2.x (Log4Shell)
- Spring Framework (Spring4Shell)
- jQuery versões antigas
- WordPress, Drupal, phpMyAdmin

**Exemplos de detecção:**
- `Server: Apache/2.4.49` → CVE-2021-41773
- `log4j-core-2.14.1` → CVE-2021-44228 (Log4Shell)

**Severidade:** High / Medium

### 6. Informações Sensíveis Expostas 🔑
Detecta exposição de informações sensíveis em respostas:
- Senhas em texto claro
- API Keys
- Secret Keys
- Tokens de autenticação
- AWS Access Keys
- Chaves privadas RSA
- Connection Strings (MongoDB, MySQL, PostgreSQL)

**Exemplos de detecção:**
- `password = "mypassword123"`
- `api_key = "AKIAIOSFODNN7EXAMPLE"`
- `-----BEGIN RSA PRIVATE KEY-----`

**Severidade:** Medium / Low

## 🎨 Interface do Usuário

O scanner possui uma aba dedicada na interface gráfica com:

### Filtros
- **Severidade:** Todas, Critical, High, Medium, Low
- **Tipo:** Filtra por tipo específico de vulnerabilidade

### Lista de Vulnerabilidades
Exibe vulnerabilidades detectadas com:
- ID único
- Severidade (com código de cores)
- Tipo de vulnerabilidade
- URL afetada
- Método HTTP

### Detalhes
Ao selecionar uma vulnerabilidade, são exibidos:
- Tipo e severidade
- Descrição completa
- Evidência encontrada
- URL e método
- Dados da requisição original

### Cores de Severidade
- 🔴 **Critical:** Vermelho (negrito)
- 🟠 **High:** Laranja (negrito)
- 🟡 **Medium:** Amarelo/Dourado
- ⚪ **Low:** Cinza

## 🔧 Como Usar

### 1. Iniciar o Proxy
```bash
python intercept_proxy.py
```

### 2. Ativar o Proxy
Clique no botão "Iniciar Proxy" na interface

### 3. Configurar o Navegador
Configure seu navegador para usar o proxy em `127.0.0.1:8080`

### 4. Navegar Normalmente
O scanner analisa automaticamente todas as respostas HTTP

### 5. Visualizar Vulnerabilidades
- Acesse a aba "Scanner 🔐"
- Use os filtros para organizar os resultados
- Clique em uma vulnerabilidade para ver detalhes

## 📊 Exemplo de Uso

### Caso 1: Detecção de SQL Injection
```
Requisição: GET /search?q=test' OR 1=1--
Resposta: SQL syntax error near "'" at line 1

→ Scanner detecta: SQL Injection (High)
```

### Caso 2: Detecção de XSS Refletido
```
Requisição: GET /search?q=<script>alert(1)</script>
Resposta: Resultados para: <script>alert(1)</script>

→ Scanner detecta: XSS (High)
```

### Caso 3: Detecção de API Key Exposta
```
Resposta: {"config": {"api_key": "AKIAIOSFODNN7EXAMPLE"}}

→ Scanner detecta: Informação Sensível Exposta (Medium)
```

## 🧪 Testes

Execute os testes do scanner:
```bash
python test_scanner.py
```

Os testes verificam:
- ✅ Detecção de SQL Injection
- ✅ Detecção de XSS
- ✅ Detecção de Path Traversal
- ✅ Detecção de Informações Sensíveis
- ✅ Detecção de CVEs
- ✅ Detecção de CSRF
- ✅ Formatação de relatórios

## 🔍 Arquitetura Técnica

### Módulo Principal
`src/core/scanner.py` - Classe `VulnerabilityScanner`

### Integração
- **addon.py:** Scanner executado no método `response()`
- **history.py:** Vulnerabilidades armazenadas junto com histórico
- **gui.py:** Interface visual na aba Scanner

### Fluxo de Dados
```
1. Requisição HTTP → mitmproxy
2. Resposta HTTP → InterceptAddon.response()
3. Scanner analisa → VulnerabilityScanner.scan_response()
4. Vulnerabilidades → RequestHistory.add_request()
5. UI atualizada → ProxyGUI._update_scanner_list()
```

## 📈 Limitações e Melhorias Futuras

### Limitações Atuais
- Scanner é baseado em padrões (pattern-matching)
- Pode gerar falsos positivos
- Não executa payloads ativos (é passivo)
- Não faz fuzzing automático

### Melhorias Futuras
- [ ] Scanner ativo com payloads automáticos
- [ ] Redução de falsos positivos com IA/ML
- [ ] Exportação de relatórios (PDF/HTML)
- [ ] Integração com bases CVE atualizadas
- [ ] Detecção de Open Redirect
- [ ] Análise de headers de segurança (CORS, CSP, etc.)
- [ ] Verificação de certificados SSL/TLS

## 🤝 Contribuindo

Para adicionar novos padrões de detecção:

1. Adicione o padrão em `VulnerabilityScanner.__init__()`
2. Crie método de detecção `_detect_xxx()`
3. Integre em `scan_response()`
4. Adicione testes em `test_scanner.py`

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [CVE - Common Vulnerabilities and Exposures](https://cve.mitre.org/)

## 📝 Licença

Este módulo está incluído no InteceptProxy sob a mesma licença do projeto principal.

---

**Desenvolvido com ❤️ para a comunidade de segurança da informação**
