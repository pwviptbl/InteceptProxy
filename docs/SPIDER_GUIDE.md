# 🕷️ Spider/Crawler - Guia Completo

## 📋 Índice
- [O que é o Spider/Crawler?](#o-que-é-o-spidercrawler)
- [Como Funciona](#como-funciona)
- [Como Usar](#como-usar)
- [Recursos](#recursos)
- [Configurações](#configurações)
- [Exemplos de Uso](#exemplos-de-uso)
- [Limitações](#limitações)
- [Dicas e Boas Práticas](#dicas-e-boas-práticas)

## O que é o Spider/Crawler?

O **Spider/Crawler** é uma funcionalidade de descoberta automática que mapeia a estrutura de um site através da análise passiva das respostas HTTP. Ele extrai automaticamente:

- 🔗 **URLs e Links**: Todos os links encontrados nas páginas HTML
- 📝 **Formulários**: Formulários HTML com seus campos de entrada
- 🗺️ **Sitemap**: Estrutura organizada do site por host e paths
- 🔑 **Parâmetros**: Parâmetros de query strings descobertos

## Como Funciona

O Spider funciona de forma **passiva**, ou seja, ele não faz requisições automáticas. Em vez disso:

1. **Você navega** normalmente pelo site usando o navegador
2. **O proxy intercepta** todas as respostas HTTP
3. **O Spider analisa** o conteúdo HTML das respostas
4. **Links e formulários** são extraídos automaticamente
5. **O sitemap** é construído progressivamente

Este método é:
- ✅ Seguro (não bombardeia o servidor com requisições)
- ✅ Discreto (tráfego parece navegação normal)
- ✅ Eficiente (aproveita sua navegação existente)

## Como Usar

### Passo 1: Iniciar o Proxy

Primeiro, inicie o proxy na aba "Controle do Proxy":
```
1. Clique em "Iniciar Proxy"
2. Configure seu navegador para usar o proxy (localhost:8080)
3. Instale o certificado do mitmproxy para HTTPS (http://mitm.it)
```

### Passo 2: Configurar o Spider

Na aba "🕷️ Spider/Crawler", configure:

- **URL Inicial (escopo)**: `http://example.com`
  - Define o domínio que será mapeado
  - Apenas URLs deste domínio serão descobertas
  
- **Profundidade Máxima**: `3`
  - Quantos níveis de links seguir
  - Exemplo: página → link → link → link = 3 níveis
  
- **Máximo de URLs**: `1000`
  - Limite de URLs para evitar mapear sites muito grandes

### Passo 3: Iniciar o Spider

```
1. Clique em "▶ Iniciar Spider"
2. O status mudará para "Em Execução" (verde)
```

### Passo 4: Navegar no Site

```
1. Abra seu navegador (já configurado com o proxy)
2. Acesse a URL inicial (ex: http://example.com)
3. Navegue normalmente pelo site
4. O Spider analisará automaticamente as páginas
```

### Passo 5: Visualizar Resultados

O Spider possui 3 abas de resultados:

#### 📋 URLs Descobertas
- Lista de todas as URLs encontradas
- Botões:
  - **↻ Atualizar**: Recarrega a lista
  - **📋 Copiar Todas**: Copia URLs para área de transferência

#### 📝 Formulários
- Tabela com formulários descobertos:
  - Método (GET/POST)
  - URL do formulário
  - Campos de entrada
  
#### 🗺️ Sitemap
- Estrutura organizada do site:
  - Agrupado por host
  - Lista de paths descobertos
  - Parâmetros de query string encontrados
- Botões:
  - **↻ Atualizar**: Recarrega o sitemap
  - **💾 Exportar**: Salva em arquivo .txt

### Passo 6: Parar e Limpar

```
1. Clique em "⏹ Parar Spider" quando terminar
2. Use "🗑 Limpar Dados" para resetar os resultados
```

## Recursos

### Estatísticas em Tempo Real

Na parte superior da aba, você vê estatísticas atualizadas a cada 2 segundos:

```
URLs Descobertas: 45 | Na Fila: 12 | Visitadas: 33 | Formulários: 3
```

- **URLs Descobertas**: Total de URLs únicas encontradas
- **Na Fila**: URLs aguardando para serem visitadas
- **Visitadas**: URLs já processadas pelo Spider
- **Formulários**: Número de formulários descobertos

### Filtragem Automática

O Spider automaticamente ignora:
- ❌ Arquivos estáticos: `.jpg`, `.png`, `.css`, `.js`, `.pdf`, etc.
- ❌ URLs fora do escopo (domínios diferentes)
- ❌ Fragmentos (#) de URLs
- ❌ Duplicatas

### Extração de Formulários

Para cada formulário descoberto, o Spider captura:
- URL do formulário
- Método (GET ou POST)
- Todos os campos `<input>`:
  - Nome do campo
  - Tipo (text, password, email, etc.)
  - Valor padrão (se houver)

## Configurações

### URL Inicial (Escopo)

A URL inicial define o **escopo** do Spider:

```
URL: http://example.com
```

O Spider descobrirá:
- ✅ `http://example.com/page1`
- ✅ `http://example.com/dir/page2`
- ✅ `http://www.example.com/page3` (subdomínio)
- ❌ `http://other.com/page` (domínio diferente)

### Profundidade Máxima

Controla quantos níveis de links seguir:

```
Profundidade: 3
```

Exemplo:
```
Nível 0: http://example.com/              (página inicial)
Nível 1: http://example.com/about         (link da inicial)
Nível 2: http://example.com/about/team    (link de about)
Nível 3: http://example.com/about/team/ceo (link de team)
PARADA: Profundidade 3 atingida
```

### Máximo de URLs

Limite de segurança para evitar descobrir sites muito grandes:

```
Máximo: 1000 URLs
```

Quando este limite é atingido, o Spider para de adicionar novas URLs à fila.

## Exemplos de Uso

### Exemplo 1: Mapear Site Pequeno

**Objetivo**: Mapear completamente um site pequeno (blog pessoal)

```
Configuração:
- URL Inicial: http://meublog.com
- Profundidade: 5
- Máximo URLs: 500

Passos:
1. Iniciar Spider
2. Navegar pela página inicial
3. Clicar em alguns links
4. Aguardar o mapeamento
5. Exportar sitemap
```

### Exemplo 2: Descobrir Formulários

**Objetivo**: Encontrar todos os formulários de um site

```
Configuração:
- URL Inicial: http://example.com
- Profundidade: 3
- Máximo URLs: 1000

Passos:
1. Iniciar Spider
2. Navegar por páginas com formulários (login, contato, cadastro)
3. Ir para aba "Formulários"
4. Analisar campos descobertos
```

### Exemplo 3: Mapear API Endpoints

**Objetivo**: Descobrir endpoints de API baseados em HTML

```
Configuração:
- URL Inicial: http://app.example.com
- Profundidade: 4
- Máximo URLs: 2000

Passos:
1. Iniciar Spider
2. Usar a aplicação web normalmente
3. O Spider captura chamadas AJAX em links e scripts
4. Exportar lista de URLs para análise
```

## Limitações

### 1. Funciona Apenas com HTML

O Spider analisa apenas respostas com `content-type: text/html`. Ele não processa:
- ❌ JSON
- ❌ XML
- ❌ JavaScript puro
- ❌ Respostas binárias

### 2. Não Executa JavaScript

O Spider não executa JavaScript, então ele não descobre:
- ❌ Links gerados dinamicamente por JS
- ❌ Single Page Applications (SPAs) que usam frameworks JS
- ❌ Rotas do React Router, Vue Router, etc.

**Solução**: Navegue manualmente pelas páginas geradas por JS

### 3. Não Faz Requisições Automáticas

O Spider é **passivo**. Ele não faz crawling automático como o Burp Spider ou Scrapy.

**Vantagem**: Mais seguro e discreto
**Desvantagem**: Você precisa navegar manualmente

### 4. Escopo Simples

O escopo é baseado apenas no domínio base, sem suporte a:
- ❌ Regex avançada
- ❌ Exclusões de paths específicos
- ❌ Múltiplos domínios simultâneos

## Dicas e Boas Práticas

### 💡 Dica 1: Navegue Completamente

Para um mapeamento completo:
- ✅ Clique em links do menu principal
- ✅ Acesse páginas de erro (404, 500)
- ✅ Teste diferentes seções do site
- ✅ Faça login e navegue em áreas autenticadas

### 💡 Dica 2: Use com Histórico

O Spider trabalha em conjunto com o Histórico:
- Histórico mostra todas as requisições
- Spider mostra estrutura organizada
- Use ambos para análise completa

### 💡 Dica 3: Exporte Regularmente

```
1. Vá para aba "Sitemap"
2. Clique em "💾 Exportar"
3. Salve como: sitemap_exemplo_2025-10-15.txt
```

Benefícios:
- Backup dos dados
- Comparação entre versões do site
- Documentação do mapeamento

### 💡 Dica 4: Combine com Scanner

Para testes de segurança:
1. Use o Spider para mapear o site
2. Ative o Scanner na outra aba
3. O Scanner analisará todas as páginas descobertas

### 💡 Dica 5: Ajuste a Profundidade

- Sites pequenos: profundidade 5-10
- Sites médios: profundidade 3-5  
- Sites grandes: profundidade 2-3

### 💡 Dica 6: Monitore as Estatísticas

Fique de olho nos números:
- Se "Na Fila" está crescendo muito → reduza profundidade
- Se "Visitadas" = "Descobertas" → você mapeou tudo
- Se "Formulários" = 0 → navegue mais pelo site

## Integração com Outras Funcionalidades

### Com Intercept Manual
```
1. Inicie o Spider
2. Ative o Intercept Manual
3. Ao modificar requisições, o Spider ainda mapeia as respostas
```

### Com Scanner de Vulnerabilidades
```
1. Inicie o Spider primeiro
2. Navegue pelo site
3. O Scanner analisa automaticamente as páginas
4. O Spider mapeia a estrutura
5. Resultado: Mapeamento + Análise de Segurança
```

### Com Repeater
```
1. Descubra URLs com o Spider
2. Copie uma URL da lista
3. Use no Repeater para testes manuais
```

## Comparação com Outras Ferramentas

| Recurso | InteceptProxy Spider | Burp Suite Spider | ZAP Spider |
|---------|---------------------|-------------------|------------|
| Modo Passivo | ✅ | ✅ | ✅ |
| Modo Ativo | ❌ | ✅ | ✅ |
| Descoberta de Formulários | ✅ | ✅ | ✅ |
| Exportar Sitemap | ✅ | ✅ | ✅ |
| Executar JavaScript | ❌ | ✅ (Pro) | ✅ |
| Scope Avançado | ❌ | ✅ | ✅ |

## Solução de Problemas

### Problema: Spider não descobre nada

**Soluções:**
1. Verifique se o proxy está rodando
2. Confirme que seu navegador está configurado corretamente
3. Navegue manualmente pelo site
4. Verifique se a URL está no escopo

### Problema: Muitas URLs sendo descobertas

**Soluções:**
1. Reduza a profundidade máxima
2. Diminua o limite de URLs
3. Pare e reinicie com escopo mais restrito

### Problema: Formulários não aparecem

**Soluções:**
1. Navegue em páginas com formulários (login, cadastro, contato)
2. Clique em "↻ Atualizar" na aba Formulários
3. Verifique se a página usa formulários HTML (não AJAX puro)

## Conclusão

O Spider/Crawler do InteceptProxy é uma ferramenta poderosa para:
- 🗺️ Mapear a estrutura de sites
- 📝 Descobrir formulários e campos
- 🔍 Reconhecimento passivo
- 🎯 Preparação para testes de segurança

**Próximos Passos:**
1. Experimente mapear um site de teste
2. Compare o sitemap antes e depois de alterações
3. Use em conjunto com Scanner e Intercept Manual
4. Exporte e documente seus mapeamentos

---

**Documentação criada em:** 2025-10-15
**Versão:** 1.0
