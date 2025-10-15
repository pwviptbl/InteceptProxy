"""
Módulo Spider/Crawler para descoberta automática de URLs e endpoints
"""
import re
from typing import Dict, List, Set, Any
from urllib.parse import urljoin, urlparse, parse_qs
from html.parser import HTMLParser
from .logger_config import log


class LinkParser(HTMLParser):
    """Parser HTML para extrair links e formulários"""
    
    def __init__(self):
        super().__init__()
        self.links = []
        self.forms = []
        self.current_form = None
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Extrai links de tags <a>
        if tag == 'a' and 'href' in attrs_dict:
            self.links.append(attrs_dict['href'])
        
        # Extrai links de <link> (CSS, etc)
        elif tag == 'link' and 'href' in attrs_dict:
            self.links.append(attrs_dict['href'])
        
        # Extrai scripts
        elif tag == 'script' and 'src' in attrs_dict:
            self.links.append(attrs_dict['src'])
        
        # Extrai imagens
        elif tag == 'img' and 'src' in attrs_dict:
            self.links.append(attrs_dict['src'])
        
        # Extrai iframes
        elif tag == 'iframe' and 'src' in attrs_dict:
            self.links.append(attrs_dict['src'])
        
        # Detecta formulários
        elif tag == 'form':
            self.current_form = {
                'action': attrs_dict.get('action', ''),
                'method': attrs_dict.get('method', 'get').upper(),
                'inputs': []
            }
        
        # Detecta campos de entrada em formulários
        elif tag == 'input' and self.current_form is not None:
            self.current_form['inputs'].append({
                'name': attrs_dict.get('name', ''),
                'type': attrs_dict.get('type', 'text'),
                'value': attrs_dict.get('value', '')
            })
    
    def handle_endtag(self, tag):
        if tag == 'form' and self.current_form is not None:
            self.forms.append(self.current_form)
            self.current_form = None


class Spider:
    """Spider/Crawler para descoberta automática de URLs"""
    
    def __init__(self):
        self.discovered_urls: Set[str] = set()
        self.queue: List[str] = []
        self.visited: Set[str] = set()
        self.forms: List[Dict[str, Any]] = []
        self.sitemap: Dict[str, Any] = {}
        self.running = False
        self.scope_urls: List[str] = []  # URLs no escopo
        self.max_depth = 3
        self.max_urls = 1000
        
    def is_running(self) -> bool:
        """Retorna se o spider está ativo"""
        return self.running
    
    def start(self, target_urls: List[str] = None, max_depth: int = 3, max_urls: int = 1000):
        """
        Inicia o spider
        
        Args:
            target_urls: Lista de URLs iniciais para crawl
            max_depth: Profundidade máxima de navegação
            max_urls: Número máximo de URLs para descobrir
        """
        self.running = True
        self.max_depth = max_depth
        self.max_urls = max_urls
        
        if target_urls:
            self.scope_urls = target_urls
            for url in target_urls:
                self.add_to_queue(url)
        
        log.info(f"Spider iniciado - Escopo: {len(target_urls) if target_urls else 0} URLs")
    
    def stop(self):
        """Para o spider"""
        self.running = False
        log.info("Spider parado")
    
    def clear(self):
        """Limpa todos os dados do spider"""
        self.discovered_urls.clear()
        self.queue.clear()
        self.visited.clear()
        self.forms.clear()
        self.sitemap.clear()
        self.running = False
        log.info("Spider resetado")
    
    def add_to_queue(self, url: str):
        """Adiciona URL à fila de descoberta"""
        if url and url not in self.visited and url not in self.queue:
            if self._is_in_scope(url):
                self.queue.append(url)
                log.debug(f"URL adicionada à fila: {url}")
    
    def _is_in_scope(self, url: str) -> bool:
        """Verifica se a URL está no escopo configurado"""
        if not self.scope_urls:
            return True
        
        parsed = urlparse(url)
        url_base = f"{parsed.scheme}://{parsed.netloc}"
        
        for scope_url in self.scope_urls:
            scope_parsed = urlparse(scope_url)
            scope_base = f"{scope_parsed.scheme}://{scope_parsed.netloc}"
            
            if url_base == scope_base:
                return True
            
            # Verifica subdomínios
            if parsed.netloc.endswith(f".{scope_parsed.netloc}"):
                return True
        
        return False
    
    def process_response(self, url: str, response_body: str, content_type: str = ""):
        """
        Processa uma resposta HTTP para extrair links
        
        Args:
            url: URL da requisição
            response_body: Corpo da resposta
            content_type: Tipo de conteúdo da resposta
        """
        if not self.running:
            return
        
        # Marca como visitada
        self.visited.add(url)
        
        # Limite de URLs descobertas
        if len(self.discovered_urls) >= self.max_urls:
            log.warning(f"Limite de URLs descobertas atingido ({self.max_urls})")
            return
        
        # Adiciona à lista de URLs descobertas
        self.discovered_urls.add(url)
        
        # Atualiza o sitemap
        self._update_sitemap(url)
        
        # Processa apenas HTML
        if 'html' not in content_type.lower():
            return
        
        try:
            # Parse HTML para extrair links e formulários
            parser = LinkParser()
            parser.feed(response_body)
            
            # Processa links encontrados
            for link in parser.links:
                absolute_url = urljoin(url, link)
                
                # Remove fragmentos (#)
                absolute_url = absolute_url.split('#')[0]
                
                # Ignora URLs vazias ou inválidas
                if not absolute_url or absolute_url == url:
                    continue
                
                # Ignora certos tipos de arquivos
                if self._should_ignore_url(absolute_url):
                    continue
                
                # Adiciona à fila
                self.add_to_queue(absolute_url)
            
            # Processa formulários encontrados
            for form in parser.forms:
                form_url = urljoin(url, form['action']) if form['action'] else url
                form['url'] = form_url
                form['page_url'] = url
                
                # Adiciona à lista de formulários se não estiver duplicado
                if not any(f['url'] == form_url and f['page_url'] == url for f in self.forms):
                    self.forms.append(form)
                    log.info(f"Formulário descoberto: {form['method']} {form_url}")
            
            log.debug(f"Processado {url}: {len(parser.links)} links, {len(parser.forms)} formulários")
            
        except Exception as e:
            log.error(f"Erro ao processar resposta de {url}: {e}")
    
    def _should_ignore_url(self, url: str) -> bool:
        """Verifica se a URL deve ser ignorada (arquivos estáticos, etc)"""
        ignored_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
            '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
            '.pdf', '.zip', '.tar', '.gz', '.rar',
            '.mp4', '.avi', '.mov', '.mp3', '.wav',
            '.xml', '.json'
        ]
        
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in ignored_extensions)
    
    def _update_sitemap(self, url: str):
        """Atualiza o sitemap com a nova URL"""
        parsed = urlparse(url)
        host = parsed.netloc
        path = parsed.path or '/'
        
        # Inicializa host no sitemap se não existir
        if host not in self.sitemap:
            self.sitemap[host] = {
                'paths': set(),
                'parameters': set()
            }
        
        # Adiciona o path
        self.sitemap[host]['paths'].add(path)
        
        # Extrai parâmetros da query string
        if parsed.query:
            params = parse_qs(parsed.query)
            for param_name in params.keys():
                self.sitemap[host]['parameters'].add(param_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do spider"""
        return {
            'running': self.running,
            'discovered_urls': len(self.discovered_urls),
            'queue_size': len(self.queue),
            'visited': len(self.visited),
            'forms_found': len(self.forms),
            'hosts': len(self.sitemap)
        }
    
    def get_discovered_urls(self) -> List[str]:
        """Retorna lista de URLs descobertas"""
        return sorted(list(self.discovered_urls))
    
    def get_forms(self) -> List[Dict[str, Any]]:
        """Retorna lista de formulários descobertos"""
        return self.forms
    
    def get_sitemap(self) -> Dict[str, Any]:
        """Retorna o sitemap"""
        # Converte sets para listas para serialização
        sitemap_serializable = {}
        for host, data in self.sitemap.items():
            sitemap_serializable[host] = {
                'paths': sorted(list(data['paths'])),
                'parameters': sorted(list(data['parameters']))
            }
        return sitemap_serializable
    
    def export_sitemap_text(self) -> str:
        """Exporta o sitemap como texto"""
        lines = []
        lines.append("=" * 80)
        lines.append("SITEMAP - Estrutura Descoberta")
        lines.append("=" * 80)
        lines.append("")
        
        for host, data in sorted(self.sitemap.items()):
            lines.append(f"Host: {host}")
            lines.append(f"  Paths descobertos: {len(data['paths'])}")
            for path in sorted(data['paths']):
                lines.append(f"    - {path}")
            
            if data['parameters']:
                lines.append(f"  Parâmetros encontrados: {len(data['parameters'])}")
                for param in sorted(data['parameters']):
                    lines.append(f"    - {param}")
            
            lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"Total de URLs descobertas: {len(self.discovered_urls)}")
        lines.append(f"Total de formulários: {len(self.forms)}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
