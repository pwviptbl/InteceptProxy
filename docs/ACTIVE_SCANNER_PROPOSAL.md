# Proposta de Melhoria: Scanner Ativo de Vulnerabilidades

## 📋 Resumo Executivo

Esta proposta descreve como melhorar o scanner de vulnerabilidades do InteceptProxy, integrando o **Scanner Ativo** existente na interface gráfica e expandindo suas capacidades de detecção.

## 🎯 Problema Identificado

Você relatou que ao navegar em um site local, o scanner detectou vários avisos de **CSRF** mas **nenhum sobre SQL Injection**, mesmo sabendo que a maioria dos parâmetros GET e POST eram vulneráveis a SQL Injection.

### Por que isso acontece?

O scanner atual é **PASSIVO** - ele apenas analisa as respostas HTTP em busca de padrões conhecidos (mensagens de erro de SQL, tokens refletidos, etc.). Se o servidor não retornar mensagens de erro SQL visíveis, o scanner passivo não consegue detectar a vulnerabilidade.

**Exemplo:**
```
Requisição: GET /produto?id=1' OR 1=1--
Resposta: <html>Produto não encontrado</html>  (Status 200)
```
☝️ Neste caso, mesmo que haja SQL Injection, o scanner passivo NÃO detecta porque não há erro SQL na resposta.

## ✅ Solução Proposta

### 1. Integração do Scanner Ativo na Interface Gráfica

**O que já existe:**
- O código já possui um `ActiveScanner` em `src/core/active_scanner.py`
- Ele pode testar SQL Injection e XSS enviando payloads
- Porém, NÃO está acessível na GUI

**O que será implementado:**

#### A) Nova Seção na Aba Scanner
```
┌─────────────────────────────────────────────────────────────┐
│ Scanner 🔐                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Scanner Passivo] [Scanner Ativo] <- Nova aba/seção        │
│                                                             │
│ ┌─── Scanner Ativo ───────────────────────────────────────┐│
│ │                                                          ││
│ │ Configurações:                                          ││
│ │ ☑ SQL Injection   ☑ XSS   ☑ Path Traversal            ││
│ │ ☑ Command Injection   ☐ XXE   ☐ SSRF                  ││
│ │                                                          ││
│ │ Agressividade: ◉ Baixa  ○ Média  ○ Alta               ││
│ │ Threads: [5]    Timeout: [10s]                         ││
│ │                                                          ││
│ │ [🔍 Scan Selecionado] [🔍 Scan Todos] [⏹ Parar]        ││
│ │                                                          ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ Resultados:                                                 │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ ID | Tipo | Severidade | URL | Payload | Scanner       ││
│ │ 12 | SQLi | Critical   | ... | ' OR 1=1| Ativo ✓       ││
│ │ 13 | XSS  | High       | ... | <script>| Ativo ✓       ││
│ │ 14 | CSRF | Medium     | ... | -       | Passivo       ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### B) Funcionalidades do Scanner Ativo

1. **Scan Manual (Sob Demanda)**
   - Selecionar uma ou várias requisições do histórico
   - Clicar em "Scan Ativo"
   - Scanner testa todos os parâmetros GET e POST
   - Exibe resultados em tempo real

2. **Scan Automático (Opcional)**
   - Opção para escanear automaticamente novas requisições
   - Pode ser ativado/desativado
   - Útil durante navegação exploratória

3. **Configuração de Testes**
   - Escolher quais tipos de vulnerabilidade testar
   - Ajustar agressividade (quantos payloads enviar)
   - Configurar threads e timeouts
   - Whitelist de domínios para scan

### 2. Expansão dos Payloads de Detecção

**SQL Injection - Melhorias:**

| Tipo | Payloads Atuais | Payloads Novos |
|------|----------------|----------------|
| Error-Based | `'`, `"`, `' OR 1=1--` | Já implementado |
| Boolean-Based | ❌ Nenhum | `' AND 1=1--`, `' AND 1=2--` (comparar respostas) |
| Time-Based | ❌ Nenhum | `'; WAITFOR DELAY '0:0:5'--`, `' OR SLEEP(5)--` |
| Union-Based | ❌ Nenhum | `' UNION SELECT NULL--`, `' UNION ALL SELECT` |

**Novas Vulnerabilidades a Detectar:**

1. **Command Injection**
   ```python
   Payloads: 
   - `; ls -la`
   - `| whoami`
   - `& ping -n 5 127.0.0.1`
   - `$(cat /etc/passwd)`
   ```

2. **LDAP Injection**
   ```python
   Payloads:
   - `*)(uid=*`
   - `admin)(&(password=*))`
   ```

3. **XXE (XML External Entity)**
   ```python
   Payloads:
   - `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>`
   ```

4. **SSRF (Server-Side Request Forgery)**
   ```python
   Payloads:
   - `http://127.0.0.1:8080`
   - `http://169.254.169.254/latest/meta-data/` (AWS metadata)
   ```

5. **Open Redirect**
   ```python
   Payloads:
   - `//evil.com`
   - `https://evil.com`
   - `javascript:alert(1)`
   ```

6. **Path Traversal Ativo**
   ```python
   Payloads mais sofisticados:
   - `....//....//....//etc/passwd`
   - `..%252f..%252f..%252fetc/passwd`
   - Testar vários níveis de encoding
   ```

### 3. Técnicas de Detecção Avançadas

#### A) Análise Diferencial (Diff-Based)

Para detectar **Boolean-Based SQL Injection**:
```python
1. Enviar: ?id=1 AND 1=1  (deve retornar resultados)
2. Enviar: ?id=1 AND 1=2  (não deve retornar resultados)
3. Comparar: Se as respostas forem diferentes, vulnerável!
```

#### B) Time-Based Detection

Para SQL Injection cega:
```python
1. Enviar: ?id=1' OR SLEEP(5)--
2. Medir tempo de resposta
3. Se resposta > 5 segundos, vulnerável!
```

#### C) Content-Length Analysis

```python
1. Enviar payload normal
2. Enviar payload malicioso
3. Comparar tamanho das respostas
4. Diferenças significativas indicam vulnerabilidade
```

### 4. Interface de Usuário Detalhada

#### Aba Scanner - Novo Layout

```
┌─────────────────────────────────────────────────────┐
│ 📊 Estatísticas                                     │
├─────────────────────────────────────────────────────┤
│ Total Vulnerabilidades: 15                          │
│ └─ Passivas: 8  |  Ativas: 7                       │
│                                                     │
│ Critical: 2  High: 5  Medium: 6  Low: 2           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ⚙️ Configurações do Scanner Ativo                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Vulnerabilidades a Testar:                         │
│ ☑ SQL Injection (Error, Boolean, Time)            │
│ ☑ Cross-Site Scripting (XSS)                      │
│ ☑ Path Traversal                                   │
│ ☑ Command Injection                                │
│ ☐ LDAP Injection                                   │
│ ☐ XXE Injection                                    │
│ ☐ SSRF                                             │
│ ☐ Open Redirect                                    │
│                                                     │
│ Modo:                                               │
│ ◉ Manual (Scan sob demanda)                        │
│ ○ Automático (Scan todas requisições novas)       │
│                                                     │
│ Agressividade:                                      │
│ ○ Baixa (3-5 payloads por parâmetro)              │
│ ◉ Média (10-15 payloads por parâmetro)            │
│ ○ Alta (30+ payloads por parâmetro)               │
│                                                     │
│ Performance:                                        │
│ Threads: [5]  ⬅───────────▶  (1-20)               │
│ Timeout: [10] segundos                             │
│ Delay entre requisições: [100] ms                  │
│                                                     │
│ Scope (Domínios):                                   │
│ ◉ Todos os domínios                                │
│ ○ Apenas: [________________]                       │
│ ○ Exceto:  [________________]                      │
│                                                     │
│ [💾 Salvar Configurações]                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🔍 Ações                                            │
├─────────────────────────────────────────────────────┤
│ [🎯 Scan Ativo - Requisição Selecionada]           │
│ [🌐 Scan Ativo - Todas no Histórico]               │
│ [⏹ Parar Scan]                                     │
│                                                     │
│ Status: ⏸️ Parado                                   │
│ Progresso: [████████░░░░░░░░░░░░] 40%             │
│ Testando: GET /api/users?id=5 (param: id)         │
│ 12/30 requisições | 3 vulnerabilidades encontradas │
└─────────────────────────────────────────────────────┘
```

#### Resultado do Scan

```
┌─────────────────────────────────────────────────────┐
│ Vulnerabilidade Detectada                          │
├─────────────────────────────────────────────────────┤
│ Tipo: SQL Injection (Boolean-Based)                │
│ Severidade: ⚠️ CRITICAL                            │
│ Scanner: 🔍 Ativo                                   │
│                                                     │
│ URL: http://localhost:8081/produto                 │
│ Método: GET                                         │
│ Parâmetro: id                                       │
│                                                     │
│ Payload Usado: ' AND 1=1--                         │
│                                                     │
│ Evidência:                                          │
│ ┌─────────────────────────────────────────────┐   │
│ │ Request 1: id=1 AND 1=1                      │   │
│ │ Response: 200 OK (5234 bytes)                │   │
│ │                                               │   │
│ │ Request 2: id=1 AND 1=2                      │   │
│ │ Response: 200 OK (892 bytes)                 │   │
│ │                                               │   │
│ │ Diferença: 4342 bytes                        │   │
│ │ Conclusão: Aplicação responde diferentemente│   │
│ │            a condições TRUE vs FALSE          │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ Recomendação:                                       │
│ Use prepared statements ou parameterized queries   │
│                                                     │
│ [📋 Copiar Detalhes] [🔗 Ir para Requisição]       │
└─────────────────────────────────────────────────────┘
```

### 5. Segurança e Ética

**⚠️ AVISOS IMPORTANTES A SEREM EXIBIDOS:**

```
┌──────────────────────────────────────────────────────────┐
│ ⚠️  AVISO DE USO RESPONSÁVEL                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ O Scanner Ativo envia múltiplas requisições com         │
│ payloads maliciosos para testar vulnerabilidades.       │
│                                                          │
│ ⚠️  Use APENAS em:                                      │
│   ✓ Seus próprios sistemas                             │
│   ✓ Ambientes de teste autorizados                     │
│   ✓ Sistemas com permissão explícita por escrito       │
│                                                          │
│ ❌ NÃO use em:                                          │
│   ✗ Sites de terceiros sem autorização                 │
│   ✗ Sistemas de produção sem approval                  │
│   ✗ Para atividades ilegais                            │
│                                                          │
│ O uso inadequado pode:                                   │
│ • Violar leis (LGPD, GDPR, Computer Fraud Act)         │
│ • Causar danos a sistemas                               │
│ • Resultar em ações legais                              │
│                                                          │
│ Você assume total responsabilidade pelo uso desta       │
│ ferramenta.                                              │
│                                                          │
│ ☑ Li e concordo com os termos de uso                   │
│                                                          │
│ [Continuar] [Cancelar]                                  │
└──────────────────────────────────────────────────────────┘
```

**Implementações de Segurança:**

1. **Rate Limiting**
   ```python
   - Delay configurável entre requisições
   - Máximo de requisições por minuto
   - Evita DDoS acidental
   ```

2. **Logging Completo**
   ```python
   - Log de todos os payloads enviados
   - Timestamp de cada teste
   - Resultados armazenados
   - Arquivo: active_scanner.log
   ```

3. **Confirmação para Ações Destrutivas**
   ```python
   - Confirmar antes de scan automático
   - Confirmar antes de scan em múltiplas URLs
   - Alertar sobre domínios públicos
   ```

### 6. Implementação Técnica

#### Arquivos a Modificar/Criar:

```
src/core/
├── active_scanner.py      (EXPANDIR - adicionar novos payloads)
├── scanner_config.py      (CRIAR - configurações do scanner)
└── addon.py               (MODIFICAR - integração)

src/ui/
└── gui.py                 (MODIFICAR - nova UI do scanner ativo)

docs/
└── ACTIVE_SCANNER_GUIDE.md (CRIAR - documentação)

test/
└── test_active_scanner.py  (EXPANDIR - novos testes)
```

#### Fluxo de Dados:

```
┌──────────────┐
│   Usuário    │
│  Clica em    │
│ "Scan Ativo" │
└──────┬───────┘
       │
       v
┌──────────────────────────────────────┐
│  GUI - gui.py                        │
│  • Valida configurações              │
│  • Mostra aviso de responsabilidade  │
│  • Obtém requisição(ões) selecionada │
└──────────────┬───────────────────────┘
               │
               v
┌──────────────────────────────────────┐
│  InterceptAddon - addon.py           │
│  • run_active_scan_on_request()      │
│  • Prepara dados da requisição       │
└──────────────┬───────────────────────┘
               │
               v
┌──────────────────────────────────────┐
│  ActiveScanner - active_scanner.py   │
│  • _get_insertion_points()           │
│  • Para cada parâmetro:              │
│    - _check_sql_injection()          │
│    - _check_xss()                    │
│    - _check_command_injection()      │
│    - _check_path_traversal()         │
│    - etc.                            │
│  • Retorna lista de vulnerabilidades │
└──────────────┬───────────────────────┘
               │
               v
┌──────────────────────────────────────┐
│  RequestHistory - history.py         │
│  • add_vulnerabilities_to_entry()    │
│  • Armazena resultados               │
└──────────────┬───────────────────────┘
               │
               v
┌──────────────────────────────────────┐
│  GUI - gui.py                        │
│  • _update_scanner_list()            │
│  • Exibe resultados                  │
│  • Atualiza estatísticas             │
└──────────────────────────────────────┘
```

### 7. Exemplo de Uso

**Cenário: Testar um formulário de login local**

1. Navegue até `http://localhost:8081/login`
2. Preencha formulário e envie (capturado no histórico)
3. Vá para aba "Scanner 🔐"
4. Selecione a requisição POST para /login
5. Configure:
   - ✅ SQL Injection
   - ✅ Command Injection
   - Agressividade: Média
6. Clique em "🎯 Scan Ativo - Requisição Selecionada"
7. Aguarde o scan (progresso em tempo real)
8. Veja resultados:
   ```
   ✅ Encontrado: SQL Injection (Boolean-Based) no parâmetro 'username'
   ✅ Encontrado: SQL Injection (Time-Based) no parâmetro 'password'
   ❌ Não encontrado: Command Injection
   ```

### 8. Cronograma de Implementação

**Fase 1: Integração Básica** (2-3 dias)
- [ ] Adicionar botão de scan ativo na GUI
- [ ] Conectar com ActiveScanner existente
- [ ] Exibir resultados na lista
- [ ] Testes básicos

**Fase 2: Expansão de Payloads** (3-4 dias)
- [ ] Implementar Boolean-Based SQLi
- [ ] Implementar Time-Based SQLi
- [ ] Adicionar Command Injection
- [ ] Adicionar Path Traversal ativo
- [ ] Testes para cada novo tipo

**Fase 3: UI Avançada** (2-3 dias)
- [ ] Configurações de scan
- [ ] Barra de progresso
- [ ] Estatísticas
- [ ] Avisos de segurança

**Fase 4: Novas Vulnerabilidades** (3-4 dias)
- [ ] LDAP Injection
- [ ] XXE
- [ ] SSRF
- [ ] Open Redirect
- [ ] Testes completos

**Fase 5: Polimento** (2 dias)
- [ ] Documentação completa
- [ ] Rate limiting
- [ ] Logging
- [ ] Exportação de relatórios

**Total: 12-16 dias de desenvolvimento**

### 9. Vantagens da Solução

✅ **Detecção Proativa**: Encontra vulnerabilidades mesmo sem erros visíveis
✅ **Cobertura Ampla**: Testa múltiplos tipos de vulnerabilidades
✅ **Fácil de Usar**: Interface intuitiva, similar ao Burp Suite
✅ **Configurável**: Ajuste agressividade e scope conforme necessário
✅ **Seguro**: Avisos claros e controles de segurança
✅ **Profissional**: Ferramenta completa para pentesters

### 10. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Uso indevido | Legal | Avisos claros, termos de uso |
| Sobrecarga de servidor | Performance | Rate limiting, configuração de threads |
| Falsos positivos | Confiabilidade | Análise diferencial, múltiplos payloads |
| Bloqueio por WAF | Eficácia | Payloads variados, encoding |

## 📝 Conclusão

Esta proposta transforma o InteceptProxy de um proxy HTTP com scanner passivo em uma **ferramenta profissional de segurança** com capacidades de detecção ativa de vulnerabilidades, resolvendo completamente o problema relatado.

O scanner ativo detectará SQL Injection e outras vulnerabilidades que o scanner passivo não consegue identificar, proporcionando uma experiência similar ao Burp Suite Professional, mas em uma ferramenta open-source.

---

## ❓ Próximos Passos

**AGUARDANDO SUA APROVAÇÃO PARA IMPLEMENTAR**

Por favor, revise esta proposta e:
1. ✅ Aprovar para implementação completa
2. 📝 Sugerir modificações/ajustes
3. ❌ Rejeitar com feedback

Qual a sua decisão?
