# Guia do Browser Integrado 🌐

O InteceptProxy inclui um browser integrado baseado em PyQt5 WebEngine que elimina completamente a necessidade de configuração manual do proxy!

## Características Principais

### ✅ Configuração Automática
- O proxy é configurado automaticamente (localhost:porta)
- Não é necessário alterar configurações do navegador
- Funciona imediatamente após clicar em "Abrir Browser"

### ✅ Certificado Confiável
- O certificado do mitmproxy é automaticamente aceito
- Sem avisos de certificado HTTPS
- Navegação segura em qualquer site

### ✅ Interface Completa
- Barra de endereços para digitar URLs
- Botões de navegação (Voltar, Avançar, Recarregar)
- Status do proxy sempre visível
- Indicador de segurança HTTPS

### ✅ Integração Total
- Funciona perfeitamente com todas as ferramentas do InteceptProxy
- Histórico de requisições atualizado em tempo real
- Intercept Manual funciona com requisições do browser
- Scanner pode analisar páginas visitadas
- Spider/Crawler pode descobrir páginas automaticamente

## Como Usar

### 1. Iniciar o Proxy

Primeiro, certifique-se de que o proxy está em execução:

1. Na janela principal do InteceptProxy
2. Clique em **"Iniciar Proxy"** (parte superior)
3. Aguarde a mensagem de confirmação

### 2. Abrir o Browser

Na aba **"🌐 Browser"**:

1. Clique no botão **"🌐 Abrir Browser"**
2. Uma nova janela será aberta
3. O browser está pronto para uso!

### 3. Navegar

Use o browser normalmente:

#### Barra de Endereços
- Digite ou cole uma URL
- Pressione Enter ou clique em "Go"
- O protocolo http:// é adicionado automaticamente se não especificado

#### Botões de Navegação
- **← (Voltar)**: Volta para a página anterior
- **→ (Avançar)**: Avança para a próxima página
- **⟳ (Recarregar)**: Recarrega a página atual

#### Status do Proxy
- Sempre visível na parte inferior
- Mostra: "🔒 Using Proxy: 127.0.0.1:8080 | ✓ mitmproxy certificate trusted"
- Confirma que o proxy está funcionando

## Requisitos Técnicos

### Dependências
- Python 3.7+
- PyQt5 >= 5.15.0
- PyQtWebEngine >= 5.15.0

### Instalação
```bash
pip install PyQt5 PyQtWebEngine
```

Ou instale todas as dependências:
```bash
pip install -r config/requirements.txt
```

## Dicas e Truques

### Múltiplas Janelas
- Você pode abrir múltiplas janelas do browser
- Cada janela funciona independentemente
- Todas usam o mesmo proxy

### Integração com Ferramentas
- Todas as ferramentas do InteceptProxy funcionam com o browser
- Use "Enviar para Repetição" do histórico para testar requisições
- Use o Comparador para comparar requisições do browser

## Solução de Problemas

### Browser Não Abre

**Problema**: Ao clicar em "Abrir Browser", nada acontece.

**Solução**:
1. Verifique se o proxy está em execução
2. Verifique se PyQt5 e PyQtWebEngine estão instalados
3. Verifique os logs para mensagens de erro

### Páginas Não Carregam

**Problema**: O browser abre, mas as páginas não carregam.

**Solução**:
1. Verifique se o proxy está realmente em execução
2. Confirme que o proxy está na porta correta
3. Teste com sites HTTP simples primeiro (ex: http://example.com)

**Aproveite o browser integrado! 🌐**
