import asyncio
import subprocess
import sys
from playwright.async_api import async_playwright, Playwright, Browser, Page
from threading import Thread

class BrowserManager:
    """
    Gerencia a instalação e o lançamento de um navegador Chromium pré-configurado.
    """
    def __init__(self, proxy_port: int = 9507, on_install_start=None, on_install_finish=None):
        self.proxy_port = proxy_port
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.playwright: Playwright | None = None
        self.on_install_start = on_install_start
        self.on_install_finish = on_install_finish

    def _is_chromium_installed(self):
        """Verifica se o Chromium está instalado."""
        try:
            # O Playwright usa um comando 'npx' ou similar para verificar,
            # mas uma forma programática é verificar os executáveis.
            # Uma maneira mais simples é tentar lançar e capturar o erro.
            # Por agora, vamos usar o método de verificação de instalação do Playwright.
            proc = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
                capture_output=True, text=True, check=False
            )
            return "chromium is already installed" in proc.stdout.lower()
        except FileNotFoundError:
            return False

    def _install_chromium(self):
        """Instala o Chromium usando o comando do Playwright."""
        if self.on_install_start:
            self.on_install_start()
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True, capture_output=True, text=True
            )
        finally:
            if self.on_install_finish:
                self.on_install_finish()

    async def _launch_browser_async(self):
        """Lança o navegador de forma assíncrona."""
        if not self._is_chromium_installed():
            # Executa a instalação em uma thread para não bloquear a UI
            install_thread = Thread(target=self._install_chromium, daemon=True)
            install_thread.start()
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            proxy={"server": f"http://127.0.0.1:{self.proxy_port}"},
            args=["--ignore-certificate-errors"]
        )
        self.page = await self.browser.new_page()
        # Garante que o navegador seja fechado quando a página for fechada pelo usuário
        self.page.on("close", self.close_browser_sync)


    def launch_browser(self):
        """Ponto de entrada síncrono para lançar o navegador."""
        # O Playwright é assíncrono, então precisamos de um loop de eventos
        # para executá-lo a partir de um contexto síncrono (como o Tkinter).
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._launch_browser_async())
            loop.run_forever()

        thread = Thread(target=run_async, daemon=True)
        thread.start()

    def close_browser_sync(self, *args):
        """Fecha o navegador a partir de um contexto síncrono."""
        if self.playwright:
            # Obtenha o loop de eventos da thread onde o playwright está rodando
            loop = asyncio.get_event_loop()
            # Agende o fechamento de forma thread-safe
            loop.call_soon_threadsafe(lambda: asyncio.create_task(self._close_browser_async()))

    async def _close_browser_async(self):
        """Fecha o navegador e o playwright de forma assíncrona."""
        if self.browser and not self.browser.is_closed():
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        # Para o loop de eventos
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()

    def close(self):
        """Ponto de entrada síncrono para fechar tudo."""
        self.close_browser_sync()

if __name__ == '__main__':
    # Exemplo de uso
    manager = BrowserManager()
    print("Verificando Chromium...")
    if not manager._is_chromium_installed():
        print("Chromium não instalado. Instalando...")
        manager._install_chromium()
        print("Instalação concluída.")

    print("Lançando navegador...")
    manager.launch_browser()

    # Em uma aplicação real, o fechamento seria acionado pelo fechamento da UI
    input("Pressione Enter para fechar o navegador...")
    manager.close()
    print("Navegador fechado.")