# 💥 Intruder Avançado - Exemplos

Este diretório contém exemplos práticos de uso do **Intruder Avançado**.

## 📁 Estrutura

```
examples/
├── intruder_examples.py       # Script com exemplos de uso programático
└── intruder_payloads/         # Arquivos de payload para testes
    ├── usernames.txt          # Lista de usuários comuns
    ├── passwords.txt          # Lista de senhas comuns
    ├── sqli_payloads.txt      # Payloads de SQL Injection
    ├── xss_payloads.txt       # Payloads de XSS
    └── directories.txt        # Lista de diretórios comuns
```

## 🚀 Como Usar

### Via GUI (Recomendado)

1. **Inicie a aplicação**:
   ```bash
   python intercept_proxy.py
   ```

2. **Navegue para a aba "💥 Intruder"**

3. **Configure sua requisição**:
   - Cole ou digite a requisição HTTP base
   - Marque posições de payload com `§...§`
   - Ou selecione texto e clique "📋 Marcar Posições"

4. **Selecione arquivos de payload**:
   - Payload Set 1: `examples/intruder_payloads/usernames.txt`
   - Payload Set 2: `examples/intruder_payloads/passwords.txt` (opcional)

5. **Configure o ataque**:
   - Escolha o tipo (Sniper, Battering Ram, Pitchfork, Cluster Bomb)
   - Adicione processamento se necessário
   - Configure grep extraction (opcional)

6. **Inicie e monitore**:
   - Clique "▶ Iniciar Ataque"
   - Acompanhe resultados em tempo real

### Via Código Python

Execute o script de exemplos:

```bash
python examples/intruder_examples.py
```

Este script demonstra:
- ✅ Ataque Sniper
- ✅ Ataque Battering Ram
- ✅ Ataque Pitchfork
- ✅ Ataque Cluster Bomb
- ✅ Processamento de Payloads
- ✅ Grep Extraction
- ✅ Carregamento de arquivos

## 📚 Exemplos Práticos

### Exemplo 1: Brute Force de Login (Pitchfork)

**Requisição**:
```http
POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

username=§admin§&password=§password§
```

**Configuração**:
- Tipo: **Pitchfork**
- Payload Set 1: `usernames.txt`
- Payload Set 2: `passwords.txt`
- Threads: 10

**O que acontece**:
- Testa combinações específicas em paralelo
- `admin` + `password`, `root` + `123456`, etc.
- Eficiente para listas de credenciais conhecidas

### Exemplo 2: SQL Injection Discovery (Sniper)

**Requisição**:
```http
GET /product?id=§1§ HTTP/1.1
Host: vulnerable-site.com
```

**Configuração**:
- Tipo: **Sniper**
- Payload Set 1: `sqli_payloads.txt`
- Grep: `error|mysql|syntax|database`
- Threads: 5

**O que acontece**:
- Testa cada payload SQL injection
- Extrai erros de banco de dados das respostas
- Identifica vulnerabilidades SQL

### Exemplo 3: Directory Fuzzing (Sniper)

**Requisição**:
```http
GET /§admin§ HTTP/1.1
Host: target-site.com
```

**Configuração**:
- Tipo: **Sniper**
- Payload Set 1: `directories.txt`
- Threads: 20
- Analise Status: 200 = encontrado

**O que acontece**:
- Testa cada diretório
- Identifica diretórios existentes por status code
- Descobre áreas ocultas do site

### Exemplo 4: XSS Testing com Encoding (Sniper)

**Requisição**:
```http
GET /search?q=§<script>alert(1)</script>§ HTTP/1.1
Host: test-site.com
```

**Configuração**:
- Tipo: **Sniper**
- Payload Set 1: `xss_payloads.txt`
- Processamento: ✓ URL Encode
- Grep: `<script>|alert\(|onerror`
- Threads: 10

**O que acontece**:
- Testa payloads XSS
- URL encode automaticamente
- Detecta se os payloads aparecem sem escape

### Exemplo 5: Credential Stuffing (Cluster Bomb)

**Requisição**:
```http
POST /api/auth HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"user":"§admin§","pass":"§password§"}
```

**Configuração**:
- Tipo: **Cluster Bomb**
- Payload Set 1: `usernames.txt` (10 usuários)
- Payload Set 2: `passwords.txt` (10 senhas)
- Total: 100 requisições (10 × 10)
- Threads: 5

**O que acontece**:
- Testa TODAS as combinações
- Encontra credenciais válidas
- ⚠️ Use com cuidado - muitas requisições!

### Exemplo 6: Token Extraction

**Requisição**:
```http
POST /api/register HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"username":"§user1§","email":"test@test.com"}
```

**Configuração**:
- Tipo: **Sniper**
- Payload Set 1: `usernames.txt`
- Grep: `"token":"([a-zA-Z0-9]+)"`
- Threads: 5

**O que acontece**:
- Registra múltiplos usuários
- Extrai tokens de cada resposta
- Coleta tokens para uso posterior

## 🔧 Processamento de Payloads

### Exemplo: Payload Processing Chain

**Original**: `admin`

**Com processadores**:
```
Prefix: "test_"        → test_admin
Suffix: "_123"         → test_admin_123
URL Encode            → test_admin_123 (já URL safe)
Base64                → dGVzdF9hZG1pbl8xMjM=
MD5                   → 098f6bcd4621d373cade4e832627b4f6
```

**Uso**:
1. Marque os processadores desejados na GUI
2. Digite prefix/suffix nos campos
3. Os payloads serão transformados automaticamente

## 📊 Interpretando Resultados

### Coluna "Payload(s)"
- Mostra os payloads usados naquela requisição
- Para Sniper: mostra qual posição foi testada
- Para Cluster Bomb: mostra todas as combinações

### Coluna "Status"
- **200** (Verde): Sucesso
- **401/403**: Não autorizado
- **404**: Não encontrado
- **500**: Erro do servidor

### Coluna "Length"
- Tamanho da resposta em bytes
- Útil para identificar respostas diferentes
- Ordene por esta coluna para encontrar anomalias

### Coluna "Extracted"
- Dados extraídos via regex (Grep)
- Útil para coletar tokens, IDs, etc.
- Vazio se nenhum padrão foi encontrado

### Coluna "URL"
- URL completa da requisição
- Útil para reproduzir testes

## ⚠️ Avisos Importantes

1. **Use apenas em ambientes autorizados**
   - Nunca teste em produção sem permissão
   - Obtenha autorização por escrito

2. **Respeite rate limits**
   - Ajuste threads para não sobrecarregar
   - Use delays se necessário

3. **Cluster Bomb pode gerar MUITAS requisições**
   - 100 payloads × 100 payloads = 10.000 requisições!
   - Calcule antes de executar

4. **Monitore recursos**
   - Threads altas consomem mais CPU/memória
   - Ajuste conforme necessário

## 🎓 Dicas Profissionais

1. **Comece com Sniper**
   - Identifique qual parâmetro é vulnerável
   - Depois use Cluster Bomb para exploração

2. **Use Grep inteligentemente**
   - Extraia dados valiosos automaticamente
   - Regex eficiente é essencial

3. **Processamento é poderoso**
   - Combine múltiplos processadores
   - Teste diferentes encodings

4. **Analise por tamanho**
   - Respostas diferentes podem indicar sucesso
   - Ordene por "Length" para identificar

5. **Salve suas requisições**
   - Use o histórico para repetir testes
   - Documente descobertas

## 🔗 Recursos Adicionais

- **Guia Completo**: [docs/INTRUDER_GUIDE.md](../docs/INTRUDER_GUIDE.md)
- **Documentação Geral**: [README.md](../README.md)
- **Análise de Features**: [docs/FEATURE_ANALYSIS.md](../docs/FEATURE_ANALYSIS.md)

## 🐛 Problemas Comuns

### Erro: "Nenhuma posição marcada"
- Verifique se usou `§...§` corretamente
- Use o botão "Marcar Posições" para facilitar

### Erro: "Arquivo não encontrado"
- Verifique o caminho do arquivo
- Use caminhos absolutos se necessário

### Todas as requisições falhando
- Teste a requisição base no Repeater primeiro
- Verifique se o proxy está rodando
- Confirme conectividade com o host

### Muito lento
- Aumente número de threads
- Reduza número de payloads
- Para Cluster Bomb, considere Pitchfork

## 📞 Suporte

Para dúvidas ou problemas:
1. Leia o guia completo em `docs/INTRUDER_GUIDE.md`
2. Execute `python examples/intruder_examples.py` para ver exemplos
3. Verifique os logs para mensagens de erro

---

**Desenvolvido para InteceptProxy** 🚀
