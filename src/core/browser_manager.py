import asyncio
import subprocess
import sys
import traceback
from playwright.async_api import async_playwright, Playwright, Browser, Page
from threading import Thread
import tkinter as tk

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

    def _get_screen_dimensions(self):
        """Obtém a largura e altura da tela principal."""
        root = tk.Tk()
        root.withdraw()  # Não exibe a janela principal do Tkinter
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        return screen_width, screen_height

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
            # Executa a instalação de forma assíncrona em thread para não bloquear a UI
            print("[DEBUG] Chromium não está instalado. Iniciando instalação...")
            await asyncio.to_thread(self._install_chromium)
            print("[DEBUG] Instalação do Chromium finalizada. Continuando tentativa de lançamento...")

        # Inicia o playwright e lança o browser dentro do bloco try abaixo.
        try:
            print("[DEBUG] Playwright: iniciando playwright...")
            self.playwright = self.playwright or await async_playwright().start()
            print("[DEBUG] Playwright: playwright iniciado.")
            print("[DEBUG] Playwright: lançando chromium...")
            screen_width, screen_height = self._get_screen_dimensions()
            print(f"[DEBUG] Screen dimensions detected: {screen_width}x{screen_height}")

            self.browser = await self.playwright.chromium.launch(
                headless=False,
                proxy={"server": f"http://127.0.0.1:{self.proxy_port}"},
                args=["--ignore-certificate-errors"]
            )
            print("[DEBUG] Playwright: chromium lançado.")

            print("[DEBUG] Playwright: criando novo contexto...")
            context = await self.browser.new_context(
                viewport={'width': screen_width, 'height': screen_height}
            )
            print("[DEBUG] Playwright: novo contexto criado.")

            print("[DEBUG] Playwright: criando nova página...")
            self.page = await context.new_page()
            print("[DEBUG] Playwright: nova página criada.")
            print("[DEBUG] Playwright: navegando para google.com...")
            await self.page.goto("https://www.google.com")
            print("[DEBUG] Playwright: navegação concluída.")
            # Garante que o navegador seja fechado quando a página for fechada pelo usuário
            self.page.on("close", self.close_browser_sync)
            print("[DEBUG] Playwright: handler de fechamento registrado.")
        except Exception as e:
            print(f"[ERRO] Falha ao abrir o navegador: {e}")
            traceback.print_exc()


    def launch_browser(self):
        """Ponto de entrada síncrono para lançar o navegador."""
        # O Playwright é assíncrono, então precisamos de um loop de eventos
        # para executá-lo a partir de um contexto síncrono (como o Tkinter).
        def run_async():
            loop = asyncio.new_event_loop()
            # Armazena o loop para permitir fechamentos thread-safe
            self.playwright_loop = loop
            asyncio.set_event_loop(loop)
            try:
                print("[DEBUG] Playwright thread: iniciando loop de eventos")
                loop.run_until_complete(self._launch_browser_async())
                print("[DEBUG] Playwright thread: _launch_browser_async finalizado, executando loop forever")
                loop.run_forever()
            except Exception as e:
                print(f"[DEBUG] Playwright thread: exceção não tratada: {e}")
                traceback.print_exc()

        thread = Thread(target=run_async, daemon=True)
        thread.start()

    def close_browser_sync(self, *args):
        """Fecha o navegador a partir de um contexto síncrono."""
        if self.playwright:
            # Usa o loop da thread do Playwright, se disponível
            loop = getattr(self, 'playwright_loop', None) or asyncio.get_event_loop()
            print(f"[DEBUG] close_browser_sync: agendando _close_browser_async no loop {loop}")
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