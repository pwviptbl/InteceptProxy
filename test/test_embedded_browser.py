#!/usr/bin/env python3
"""
Test script for the embedded browser integration.

This script tests all aspects of the browser integration without requiring a display.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.ui.embedded_browser import ProxyBrowser, launch_browser
        print("  ✓ embedded_browser module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import embedded_browser: {e}")
        return False
    
    try:
        from src.ui.gui import ProxyGUI
        print("  ✓ gui module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import gui: {e}")
        return False
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        print("  ✓ PyQt5 modules imported")
    except ImportError as e:
        print(f"  ✗ Failed to import PyQt5: {e}")
        return False
    
    return True


def test_browser_class():
    """Test that the ProxyBrowser class can be instantiated."""
    print("\nTesting ProxyBrowser class...")
    
    try:
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PyQt5.QtWidgets import QApplication
        from src.ui.embedded_browser import ProxyBrowser
        
        app = QApplication(sys.argv)
        
        # Test with default parameters
        browser1 = ProxyBrowser()
        assert browser1.proxy_host == '127.0.0.1'
        assert browser1.proxy_port == 8080
        print(f"  ✓ Default browser created: {browser1.proxy_host}:{browser1.proxy_port}")
        
        # Test with custom parameters
        browser2 = ProxyBrowser(proxy_host='localhost', proxy_port=9090)
        assert browser2.proxy_host == 'localhost'
        assert browser2.proxy_port == 9090
        print(f"  ✓ Custom browser created: {browser2.proxy_host}:{browser2.proxy_port}")
        
        # Test window title
        title1 = browser1.windowTitle()
        assert 'InteceptProxy Browser' in title1
        assert '8080' in title1
        print(f"  ✓ Window title correct: {title1}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to instantiate ProxyBrowser: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_integration():
    """Test that the GUI has the browser tab integrated."""
    print("\nTesting GUI integration...")
    
    try:
        from src.ui.gui import ProxyGUI
        import inspect
        
        # Check methods exist
        assert hasattr(ProxyGUI, 'setup_browser_tab')
        print("  ✓ setup_browser_tab method exists")
        
        assert hasattr(ProxyGUI, 'launch_embedded_browser')
        print("  ✓ launch_embedded_browser method exists")
        
        # Check method signatures
        setup_sig = inspect.signature(ProxyGUI.setup_browser_tab)
        assert len(setup_sig.parameters) == 1  # Just self
        print(f"  ✓ setup_browser_tab signature correct")
        
        launch_sig = inspect.signature(ProxyGUI.launch_embedded_browser)
        assert len(launch_sig.parameters) == 1  # Just self
        print(f"  ✓ launch_embedded_browser signature correct")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed GUI integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_integration():
    """Test that the browser can read proxy configuration."""
    print("\nTesting configuration integration...")
    
    try:
        from src.core.config import InterceptConfig
        
        config = InterceptConfig()
        port = config.get_port()
        
        assert isinstance(port, int)
        assert 1 <= port <= 65535
        print(f"  ✓ Proxy port from config: {port}")
        
        # Test that we can change the port
        success, message = config.set_port(9090)
        assert success
        assert config.get_port() == 9090
        print(f"  ✓ Port changed to: {config.get_port()}")
        
        # Reset to default
        config.set_port(8080)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed config integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test that all required dependencies are installed."""
    print("\nTesting dependencies...")
    
    dependencies = [
        ('PyQt5', 'PyQt5'),
        ('PyQtWebEngine', 'PyQt5.QtWebEngineWidgets'),
        ('mitmproxy', 'mitmproxy'),
        ('tkinter', 'tkinter'),
    ]
    
    all_ok = True
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"  ✓ {name} is installed")
        except ImportError:
            print(f"  ✗ {name} is NOT installed")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests."""
    print("=" * 70)
    print("Embedded Browser Integration Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("Dependency Test", test_dependencies),
        ("Configuration Integration Test", test_config_integration),
        ("Browser Class Test", test_browser_class),
        ("GUI Integration Test", test_gui_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    
    all_passed = all(results.values())
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
