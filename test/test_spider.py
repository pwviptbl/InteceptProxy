#!/usr/bin/env python3
"""
Test script para verificar a funcionalidade do Spider/Crawler
"""
import os
import sys

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.spider import Spider, LinkParser


def test_link_parser():
    """Testa o parser de links HTML"""
    print("Testando parser de links HTML...")
    
    html = """
    <html>
        <head>
            <link rel="stylesheet" href="/css/style.css">
            <script src="/js/app.js"></script>
        </head>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="http://example.com/external">External</a>
            <img src="/images/logo.png">
            <form action="/login" method="post">
                <input type="text" name="username">
                <input type="password" name="password">
                <input type="submit" value="Login">
            </form>
            <form action="/search" method="get">
                <input type="text" name="q">
            </form>
        </body>
    </html>
    """
    
    parser = LinkParser()
    parser.feed(html)
    
    assert len(parser.links) >= 6, f"Deveria encontrar pelo menos 6 links, encontrou {len(parser.links)}"
    assert '/page1' in parser.links, "Deveria encontrar /page1"
    assert '/page2' in parser.links, "Deveria encontrar /page2"
    assert '/css/style.css' in parser.links, "Deveria encontrar CSS"
    assert '/js/app.js' in parser.links, "Deveria encontrar JS"
    
    assert len(parser.forms) == 2, f"Deveria encontrar 2 formulários, encontrou {len(parser.forms)}"
    assert parser.forms[0]['action'] == '/login', "Primeiro formulário deveria ser /login"
    assert parser.forms[0]['method'] == 'POST', "Método deveria ser POST"
    assert len(parser.forms[0]['inputs']) == 3, "Login form deveria ter 3 inputs"
    
    print(f"✓ Parser encontrou {len(parser.links)} links e {len(parser.forms)} formulários")
    return True


def test_spider_initialization():
    """Testa inicialização do Spider"""
    print("\nTestando inicialização do Spider...")
    
    spider = Spider()
    
    assert not spider.is_running(), "Spider deveria estar parado inicialmente"
    assert len(spider.discovered_urls) == 0, "Não deveria ter URLs descobertas"
    assert len(spider.queue) == 0, "Fila deveria estar vazia"
    
    print("✓ Spider inicializado corretamente")
    return True


def test_spider_start_stop():
    """Testa iniciar e parar o Spider"""
    print("\nTestando start/stop do Spider...")
    
    spider = Spider()
    
    spider.start(target_urls=["http://example.com"], max_depth=2, max_urls=100)
    assert spider.is_running(), "Spider deveria estar em execução"
    assert len(spider.queue) == 1, "Deveria ter 1 URL na fila"
    assert spider.max_depth == 2, "Profundidade deveria ser 2"
    assert spider.max_urls == 100, "Max URLs deveria ser 100"
    
    spider.stop()
    assert not spider.is_running(), "Spider deveria estar parado"
    
    print("✓ Start/stop funcionando corretamente")
    return True


def test_spider_process_response():
    """Testa processamento de resposta HTML"""
    print("\nTestando processamento de resposta...")
    
    spider = Spider()
    spider.start(target_urls=["http://example.com"], max_depth=3, max_urls=1000)
    
    html_response = """
    <html>
        <body>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
            <a href="/products/item1">Product 1</a>
            <a href="http://example.com/services">Services</a>
            <a href="http://other.com/external">External Site</a>
            <form action="/subscribe" method="post">
                <input type="email" name="email">
                <input type="submit">
            </form>
        </body>
    </html>
    """
    
    spider.process_response("http://example.com", html_response, "text/html")
    
    assert "http://example.com" in spider.discovered_urls, "URL base deveria estar nas descobertas"
    assert "http://example.com" in spider.visited, "URL deveria estar marcada como visitada"
    
    # Verifica se links foram adicionados à fila (dentro do escopo)
    assert len(spider.queue) > 0, "Deveria ter URLs na fila"
    
    # Verifica se formulários foram descobertos
    assert len(spider.forms) >= 1, "Deveria ter descoberto pelo menos 1 formulário"
    
    print(f"✓ Processamento concluído: {len(spider.discovered_urls)} URLs, {len(spider.forms)} formulários")
    return True


def test_spider_scope():
    """Testa verificação de escopo"""
    print("\nTestando verificação de escopo...")
    
    spider = Spider()
    spider.start(target_urls=["http://example.com"], max_depth=3, max_urls=1000)
    
    # URLs dentro do escopo
    assert spider._is_in_scope("http://example.com/page1"), "Deveria estar no escopo"
    assert spider._is_in_scope("http://example.com/dir/page2"), "Deveria estar no escopo"
    
    # URLs fora do escopo
    assert not spider._is_in_scope("http://other.com/page"), "Não deveria estar no escopo"
    assert not spider._is_in_scope("http://example.org/page"), "Não deveria estar no escopo"
    
    print("✓ Verificação de escopo funcionando corretamente")
    return True


def test_spider_ignore_static():
    """Testa se o Spider ignora arquivos estáticos"""
    print("\nTestando ignorar arquivos estáticos...")
    
    spider = Spider()
    
    assert spider._should_ignore_url("http://example.com/image.jpg"), "Deveria ignorar JPG"
    assert spider._should_ignore_url("http://example.com/style.css"), "Deveria ignorar CSS"
    assert spider._should_ignore_url("http://example.com/script.js"), "Deveria ignorar JS"
    assert spider._should_ignore_url("http://example.com/doc.pdf"), "Deveria ignorar PDF"
    
    assert not spider._should_ignore_url("http://example.com/page.html"), "Não deveria ignorar HTML"
    assert not spider._should_ignore_url("http://example.com/page"), "Não deveria ignorar página sem extensão"
    
    print("✓ Filtro de arquivos estáticos funcionando")
    return True


def test_spider_sitemap():
    """Testa geração de sitemap"""
    print("\nTestando geração de sitemap...")
    
    spider = Spider()
    spider.start(target_urls=["http://example.com"], max_depth=3, max_urls=1000)
    
    # Processa algumas respostas
    html = "<html><body><a href='/page1'>Page 1</a></body></html>"
    spider.process_response("http://example.com/", html, "text/html")
    spider.process_response("http://example.com/page1?id=123", html, "text/html")
    
    sitemap = spider.get_sitemap()
    
    assert "example.com" in sitemap, "Deveria ter o host no sitemap"
    assert len(sitemap["example.com"]["paths"]) >= 2, "Deveria ter pelo menos 2 paths"
    assert "id" in sitemap["example.com"]["parameters"], "Deveria ter parâmetro 'id'"
    
    # Testa exportação de texto
    sitemap_text = spider.export_sitemap_text()
    assert "SITEMAP" in sitemap_text, "Texto deveria conter SITEMAP"
    assert "example.com" in sitemap_text, "Texto deveria conter o host"
    
    print(f"✓ Sitemap gerado com {len(sitemap['example.com']['paths'])} paths")
    return True


def test_spider_stats():
    """Testa estatísticas do Spider"""
    print("\nTestando estatísticas...")
    
    spider = Spider()
    spider.start(target_urls=["http://example.com"], max_depth=3, max_urls=1000)
    
    stats = spider.get_stats()
    
    assert 'running' in stats, "Stats deveria ter 'running'"
    assert 'discovered_urls' in stats, "Stats deveria ter 'discovered_urls'"
    assert 'queue_size' in stats, "Stats deveria ter 'queue_size'"
    assert 'visited' in stats, "Stats deveria ter 'visited'"
    assert 'forms_found' in stats, "Stats deveria ter 'forms_found'"
    
    assert stats['running'] == True, "Spider deveria estar rodando"
    assert stats['queue_size'] == 1, "Deveria ter 1 URL na fila"
    
    print(f"✓ Estatísticas: {stats}")
    return True


def test_spider_clear():
    """Testa limpeza de dados do Spider"""
    print("\nTestando limpeza de dados...")
    
    spider = Spider()
    spider.start(target_urls=["http://example.com"], max_depth=3, max_urls=1000)
    
    html = "<html><body><a href='/page1'>Page 1</a></body></html>"
    spider.process_response("http://example.com/", html, "text/html")
    
    # Verifica que tem dados
    assert len(spider.discovered_urls) > 0, "Deveria ter URLs descobertas"
    
    # Limpa
    spider.clear()
    
    # Verifica que foi limpo
    assert len(spider.discovered_urls) == 0, "URLs descobertas deveriam estar vazias"
    assert len(spider.queue) == 0, "Fila deveria estar vazia"
    assert len(spider.visited) == 0, "Visitadas deveriam estar vazias"
    assert len(spider.forms) == 0, "Formulários deveriam estar vazios"
    assert not spider.is_running(), "Spider deveria estar parado"
    
    print("✓ Limpeza de dados funcionando")
    return True


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 80)
    print("TESTES DO SPIDER/CRAWLER")
    print("=" * 80)
    
    tests = [
        test_link_parser,
        test_spider_initialization,
        test_spider_start_stop,
        test_spider_process_response,
        test_spider_scope,
        test_spider_ignore_static,
        test_spider_sitemap,
        test_spider_stats,
        test_spider_clear,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ {test.__name__} FALHOU: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} ERRO: {e}")
    
    print("\n" + "=" * 80)
    print(f"RESULTADOS: {passed} PASSOU | {failed} FALHOU")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES DO SPIDER PASSARAM COM SUCESSO!")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
