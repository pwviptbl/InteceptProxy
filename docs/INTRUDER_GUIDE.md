# Intruder Avançado - Guia de Uso

## 📋 Visão Geral

O **Intruder Avançado** é uma ferramenta poderosa para testes de segurança que permite:
- Enviar múltiplas requisições com payloads variados
- Testar diferentes posições de injeção simultaneamente
- Aplicar transformações nos payloads (encoding, hashing, etc.)
- Extrair dados das respostas usando expressões regulares
- 4 tipos diferentes de ataque para diferentes cenários

## 🎯 Tipos de Ataque

### 1. **Sniper** 🎯
- **Uso**: Testa cada posição de payload individualmente
- **Como funciona**: Usa um único conjunto de payloads e testa cada posição separadamente, mantendo as outras com valores originais
- **Exemplo**: 
  ```
  Request: GET /login?user=§admin§&pass=§123§
  Payloads: [test1, test2]
  
  Requisições geradas:
  - GET /login?user=test1&pass=123
  - GET /login?user=test2&pass=123
  - GET /login?user=admin&pass=test1
  - GET /login?user=admin&pass=test2
  ```
- **Quando usar**: Identificar qual parâmetro é vulnerável, fuzzing de parâmetros individuais

### 2. **Battering Ram** 🏏
- **Uso**: Usa o mesmo payload em todas as posições simultaneamente
- **Como funciona**: Um único conjunto de payloads, cada payload é inserido em TODAS as posições ao mesmo tempo
- **Exemplo**:
  ```
  Request: GET /login?user=§admin§&pass=§123§
  Payloads: [test1, test2]
  
  Requisições geradas:
  - GET /login?user=test1&pass=test1
  - GET /login?user=test2&pass=test2
  ```
- **Quando usar**: Testar quando o mesmo valor deve aparecer em múltiplas posições (ex: CSRF bypass, ataques de sincronização)

### 3. **Pitchfork** 🔱
- **Uso**: Itera através de múltiplos conjuntos de payloads em paralelo
- **Como funciona**: Requer um conjunto de payloads para cada posição, itera em paralelo (para quando o conjunto mais curto acaba)
- **Exemplo**:
  ```
  Request: GET /login?user=§admin§&pass=§123§
  Payload Set 1: [admin, user, guest]
  Payload Set 2: [pass123, 12345, abc]
  
  Requisições geradas:
  - GET /login?user=admin&pass=pass123
  - GET /login?user=user&pass=12345
  - GET /login?user=guest&pass=abc
  ```
- **Quando usar**: Testar combinações específicas de credenciais, ataques direcionados

### 4. **Cluster Bomb** 💣
- **Uso**: Testa TODAS as combinações possíveis de múltiplos conjuntos de payloads
- **Como funciona**: Produto cartesiano de todos os conjuntos de payloads
- **Exemplo**:
  ```
  Request: GET /login?user=§admin§&pass=§123§
  Payload Set 1: [admin, user]
  Payload Set 2: [pass1, pass2]
  
  Requisições geradas:
  - GET /login?user=admin&pass=pass1
  - GET /login?user=admin&pass=pass2
  - GET /login?user=user&pass=pass1
  - GET /login?user=user&pass=pass2
  ```
- **Quando usar**: Brute-force completo, teste exaustivo de todas as combinações

## 🔧 Processamento de Payloads

### Transformações Disponíveis

1. **URL Encode** 🔗
   - Codifica caracteres especiais para formato URL
   - Exemplo: `test value` → `test%20value`

2. **Base64** 🔒
   - Codifica em Base64
   - Exemplo: `test` → `dGVzdA==`

3. **MD5 Hash** #️⃣
   - Gera hash MD5
   - Exemplo: `test` → `098f6bcd4621d373cade4e832627b4f6`

4. **Prefix/Suffix** ➕
   - Adiciona texto antes ou depois do payload
   - Exemplo: Prefix=`admin_` → `admin_test`

### Cadeia de Processadores

Os processadores são aplicados em ordem:
1. Prefix
2. Suffix
3. Encoding/Hashing selecionados

**Exemplo**:
```
Payload original: "user"
Prefix: "test_"
Suffix: "_123"
URL Encode: ✓

Resultado: test_user_123 (não URL encoded pois já tem o valor processado)
```

## 🔍 Grep Extraction

Extrai dados das respostas usando expressões regulares.

### Exemplos de Padrões

```regex
# Extrair tokens
token=([a-zA-Z0-9]+)

# Extrair IDs numéricos
id=(\d+)

# Extrair emails
([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})

# Extrair hashes
[a-f0-9]{32}  # MD5
[a-f0-9]{64}  # SHA256

# Extrair valores entre aspas
"([^"]*)"
```

### Casos de Uso

1. **Enumerar Usuários**: Extrair IDs ou nomes de usuário das respostas
2. **Coletar Tokens**: Capturar tokens CSRF ou de sessão
3. **Descobrir Informações**: Extrair emails, números de telefone, etc.
4. **Análise de Respostas**: Identificar padrões em diferentes respostas

## 📝 Como Usar

### Passo 1: Marcar Posições de Payload

Use o marcador `§...§` para indicar onde os payloads devem ser inseridos:

```http
GET /search?q=§PAYLOAD§ HTTP/1.1
Host: example.com

POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

username=§user§&password=§pass§
```

**Dica**: Selecione o texto e clique em "📋 Marcar Posições" para adicionar os marcadores automaticamente.

### Passo 2: Preparar Payloads

Crie arquivos .txt com um payload por linha:

**users.txt**:
```
admin
root
user
guest
test
```

**passwords.txt**:
```
password
123456
admin123
letmein
qwerty
```

### Passo 3: Configurar o Ataque

1. **Selecione o Tipo de Ataque**:
   - Sniper: Para testar cada posição separadamente
   - Battering Ram: Para usar o mesmo valor em todas as posições
   - Pitchfork: Para combinar sets em paralelo
   - Cluster Bomb: Para todas as combinações

2. **Carregue os Payloads**:
   - Payload Set 1: Sempre obrigatório
   - Payload Set 2: Opcional (para Pitchfork e Cluster Bomb)

3. **Configure Processamento** (opcional):
   - Marque transformações desejadas
   - Adicione prefix/suffix se necessário

4. **Configure Grep** (opcional):
   - Adicione regex para extrair dados

5. **Ajuste Threads**:
   - Padrão: 10 threads
   - Aumente para ataques mais rápidos
   - Diminua para evitar sobrecarga do servidor

### Passo 4: Iniciar e Monitorar

1. Clique em "▶ Iniciar Ataque"
2. Acompanhe o progresso na barra
3. Veja resultados na tabela:
   - **Payload(s)**: Valores usados
   - **Status**: Código HTTP
   - **Length**: Tamanho da resposta
   - **Extracted**: Dados extraídos via grep
   - **URL**: URL completa da requisição

## 💡 Exemplos Práticos

### Exemplo 1: Brute Force de Login (Pitchfork)

```http
POST /login HTTP/1.1
Host: vulnerable-site.com
Content-Type: application/x-www-form-urlencoded

username=§admin§&password=§password§
```

**Configuração**:
- Tipo: Pitchfork
- Payload Set 1: users.txt (admin, root, user, ...)
- Payload Set 2: passwords.txt (pass123, admin, ...)
- Grep: `Login successful|Welcome`

### Exemplo 2: SQL Injection (Sniper)

```http
GET /product?id=§1§ HTTP/1.1
Host: vulnerable-site.com
```

**Configuração**:
- Tipo: Sniper
- Payload Set 1: sqli_payloads.txt (`' OR 1=1--`, `1' UNION SELECT...`)
- Grep: `error|mysql|syntax|database`

### Exemplo 3: Directory Fuzzing (Sniper)

```http
GET /§admin§ HTTP/1.1
Host: target-site.com
```

**Configuração**:
- Tipo: Sniper
- Payload Set 1: directories.txt (admin, backup, test, ...)
- Threads: 20
- Analise: Status codes (200 = encontrado)

### Exemplo 4: Parameter Discovery (Cluster Bomb)

```http
GET /api?§param1§=§value1§ HTTP/1.1
Host: api-server.com
```

**Configuração**:
- Tipo: Cluster Bomb
- Payload Set 1: param_names.txt (id, user, token, ...)
- Payload Set 2: values.txt (1, admin, test, ...)
- Grep: `"success":|"data":`

### Exemplo 5: XSS Testing com Encoding (Battering Ram)

```http
GET /search?q=§<script>alert(1)</script>§&category=§<script>alert(1)</script>§ HTTP/1.1
Host: test-site.com
```

**Configuração**:
- Tipo: Battering Ram
- Payload Set 1: xss_payloads.txt
- Processamento: URL Encode (testar se escapa)
- Grep: `<script>|alert\(|onerror`

## 📊 Análise de Resultados

### Interpretando Respostas

1. **Status Codes**:
   - **200 (Verde)**: Sucesso - requisição processada
   - **401/403 (Vermelho)**: Não autorizado/Proibido
   - **404**: Não encontrado
   - **500**: Erro do servidor (pode indicar payload problemático)

2. **Length (Tamanho)**:
   - Respostas com tamanho diferente podem indicar comportamento diferente
   - Útil para identificar credenciais válidas (resposta maior/menor)

3. **Extracted (Dados Extraídos)**:
   - Valores capturados pela regex
   - Útil para coletar tokens, IDs, etc.

### Dicas de Análise

- **Ordene por tamanho**: Clique na coluna "Length" para ordenar
- **Procure padrões**: Respostas diferentes podem indicar vulnerabilidades
- **Use grep inteligente**: Extraia dados relevantes automaticamente
- **Compare respostas**: Status codes similares mas tamanhos diferentes

## ⚠️ Considerações de Segurança

1. **Use apenas em ambientes autorizados**
2. **Respeite rate limits do servidor**
3. **Ajuste threads para não derrubar o servidor**
4. **Obtenha permissão antes de testar**
5. **Documente todos os testes realizados**

## 🚀 Performance

### Otimização

- **Threads**: Aumente para paralelizar (10-50 recomendado)
- **Payload Sets**: Use conjuntos menores para Cluster Bomb
- **Grep Patterns**: Use regex eficientes

### Estimativas

- **Sniper**: Posições × Payloads requisições
- **Battering Ram**: Payloads requisições
- **Pitchfork**: min(Set1, Set2, ...) requisições
- **Cluster Bomb**: Set1 × Set2 × ... requisições (cuidado!)

**Exemplo Cluster Bomb**:
- 100 usuários × 1000 senhas = 100.000 requisições
- Com 10 threads @ 1 req/s = ~2.7 horas

## 🔗 Integração

O Intruder trabalha bem com outras ferramentas:

1. **History**: Envie requisições do histórico para o Intruder
2. **Repeater**: Teste requisições individuais antes de automatizar
3. **Cookie Jar**: Cookies são automaticamente injetados
4. **Scanner**: Use resultados do Intruder para alimentar o scanner

## ❓ Troubleshooting

### Problema: Nenhuma requisição sendo enviada

- ✓ Verifique se marcou posições com §...§
- ✓ Confirme que selecionou arquivo de payload
- ✓ Verifique os logs para erros

### Problema: Todas as requisições falhando

- ✓ Teste a requisição base no Repeater primeiro
- ✓ Verifique se o proxy está rodando
- ✓ Confirme que o host está acessível

### Problema: Resultados inesperados

- ✓ Verifique o tipo de ataque selecionado
- ✓ Confirme os processadores aplicados
- ✓ Teste com payloads simples primeiro

### Problema: Muito lento

- ✓ Aumente o número de threads
- ✓ Reduza o número de payloads
- ✓ Para Cluster Bomb, considere Pitchfork
