"""
Embedded browser with automatic proxy configuration and certificate trust.
Uses PyQt5 WebEngine to provide a browser that automatically connects through the proxy.
"""

import os
import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtNetwork import QNetworkProxy


class ProxyBrowserPage(QWebEnginePage):
    """Custom web page that ignores SSL errors for the proxy certificate."""
    
    def certificateError(self, error):
        """Accept all certificate errors (for mitmproxy certificate)."""
        # Always accept certificate errors to trust mitmproxy's certificate
        return True


class ProxyBrowser(QMainWindow):
    """
    Embedded browser with automatic proxy configuration.
    Configures itself to use the proxy server and trusts the mitmproxy certificate.
    """
    
    def __init__(self, proxy_host='127.0.0.1', proxy_port=8080):
        super().__init__()
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.init_ui()
        self.setup_proxy()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"InteceptProxy Browser (Proxy: {self.proxy_host}:{self.proxy_port})")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Navigation bar
        nav_bar = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("←")
        self.back_button.setFixedWidth(40)
        self.back_button.clicked.connect(self.navigate_back)
        nav_bar.addWidget(self.back_button)
        
        # Forward button
        self.forward_button = QPushButton("→")
        self.forward_button.setFixedWidth(40)
        self.forward_button.clicked.connect(self.navigate_forward)
        nav_bar.addWidget(self.forward_button)
        
        # Reload button
        self.reload_button = QPushButton("⟳")
        self.reload_button.setFixedWidth(40)
        self.reload_button.clicked.connect(self.reload_page)
        nav_bar.addWidget(self.reload_button)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)
        
        # Go button
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.navigate_to_url)
        nav_bar.addWidget(self.go_button)
        
        layout.addLayout(nav_bar)
        
        # Status bar with proxy info
        status_bar = QHBoxLayout()
        self.status_label = QLabel(f"🔒 Using Proxy: {self.proxy_host}:{self.proxy_port} | ✓ mitmproxy certificate trusted")
        self.status_label.setStyleSheet("color: green; padding: 5px;")
        status_bar.addWidget(self.status_label)
        layout.addLayout(status_bar)
        
        # Web view
        self.browser = QWebEngineView()
        
        # Set custom page that accepts certificate errors
        self.page = ProxyBrowserPage(self.browser.page().profile(), self.browser)
        self.browser.setPage(self.page)
        
        # Connect URL changed signal
        self.browser.urlChanged.connect(self.update_url_bar)
        
        layout.addWidget(self.browser)
        
        # Load default page
        self.browser.setUrl(QUrl("http://mitm.it"))
        
    def setup_proxy(self):
        """Configure the browser to use the proxy server."""
        # Set up proxy for the web engine profile
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.HttpProxy)
        proxy.setHostName(self.proxy_host)
        proxy.setPort(self.proxy_port)
        
        # Apply proxy to the application
        QNetworkProxy.setApplicationProxy(proxy)
        
        # Also set proxy for the web engine profile
        profile = self.browser.page().profile()
        profile.setHttpUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 InteceptProxy/1.0"
        )
    
    def navigate_to_url(self):
        """Navigate to the URL in the address bar."""
        url = self.url_bar.text()
        
        # Add http:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        self.browser.setUrl(QUrl(url))
    
    def update_url_bar(self, url):
        """Update the URL bar when the page changes."""
        self.url_bar.setText(url.toString())
    
    def navigate_back(self):
        """Navigate to the previous page."""
        self.browser.back()
    
    def navigate_forward(self):
        """Navigate to the next page."""
        self.browser.forward()
    
    def reload_page(self):
        """Reload the current page."""
        self.browser.reload()


def launch_browser(proxy_host='127.0.0.1', proxy_port=8080):
    """
    Launch the embedded browser in a separate process.
    
    Args:
        proxy_host: The proxy host address (default: 127.0.0.1)
        proxy_port: The proxy port number (default: 8080)
    """
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create and show browser
    browser = ProxyBrowser(proxy_host=proxy_host, proxy_port=proxy_port)
    browser.show()
    
    # Run the application if this is the main thread
    if app.thread() == app.instance().thread():
        return app.exec_()
    
    return browser


if __name__ == "__main__":
    # For testing purposes
    launch_browser()
