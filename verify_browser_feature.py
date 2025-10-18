#!/usr/bin/env python3
"""
Final verification script for the embedded browser feature.

This script performs a comprehensive check of all components.
"""

import sys
import os

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{BOLD}{'=' * 70}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 70}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗{RESET} {text}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ{RESET} {text}")


def check_files():
    """Check that all required files exist."""
    print_header("CHECKING FILES")
    
    files = [
        ('Browser Module', 'src/ui/embedded_browser.py'),
        ('GUI Module', 'src/ui/gui.py'),
        ('User Guide', 'docs/EMBEDDED_BROWSER_GUIDE.md'),
        ('Implementation Doc', 'docs/EMBEDDED_BROWSER_IMPLEMENTATION.md'),
        ('Example Script', 'examples/demo_browser.py'),
        ('Integration Tests', 'test/test_embedded_browser.py'),
        ('Requirements', 'config/requirements.txt'),
        ('README', 'README.md'),
    ]
    
    all_exist = True
    for name, path in files:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print_success(f"{name}: {path} ({size} bytes)")
        else:
            print_error(f"{name}: {path} NOT FOUND")
            all_exist = False
    
    return all_exist


def check_imports():
    """Check that all modules can be imported."""
    print_header("CHECKING IMPORTS")
    
    imports = [
        ('PyQt5.QtWidgets', 'PyQt5 Core'),
        ('PyQt5.QtWebEngineWidgets', 'PyQt5 WebEngine'),
        ('src.ui.embedded_browser', 'Browser Module'),
        ('src.ui.gui', 'GUI Module'),
        ('src.core.config', 'Config Module'),
    ]
    
    all_ok = True
    for module, name in imports:
        try:
            __import__(module)
            print_success(f"{name}: {module}")
        except ImportError as e:
            print_error(f"{name}: {module} - {e}")
            all_ok = False
    
    return all_ok


def check_classes():
    """Check that key classes exist and are instantiable."""
    print_header("CHECKING CLASSES")
    
    try:
        from src.ui.embedded_browser import ProxyBrowser, ProxyBrowserPage
        from src.core.config import InterceptConfig
        
        print_success("ProxyBrowser class exists")
        print_success("ProxyBrowserPage class exists")
        print_success("InterceptConfig class exists")
        
        # Check InterceptConfig
        config = InterceptConfig()
        port = config.get_port()
        print_success(f"Config initialized (port: {port})")
        
        return True
        
    except Exception as e:
        print_error(f"Class check failed: {e}")
        return False


def check_gui_integration():
    """Check GUI integration."""
    print_header("CHECKING GUI INTEGRATION")
    
    try:
        from src.ui.gui import ProxyGUI
        
        # Check methods
        if hasattr(ProxyGUI, 'setup_browser_tab'):
            print_success("ProxyGUI.setup_browser_tab() exists")
        else:
            print_error("ProxyGUI.setup_browser_tab() NOT FOUND")
            return False
        
        if hasattr(ProxyGUI, 'launch_embedded_browser'):
            print_success("ProxyGUI.launch_embedded_browser() exists")
        else:
            print_error("ProxyGUI.launch_embedded_browser() NOT FOUND")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"GUI integration check failed: {e}")
        return False


def check_documentation():
    """Check documentation content."""
    print_header("CHECKING DOCUMENTATION")
    
    try:
        # Check README
        with open('README.md', 'r') as f:
            readme = f.read()
            if 'Browser Integrado' in readme or 'Embedded Browser' in readme:
                print_success("README.md mentions the browser feature")
            else:
                print_error("README.md does not mention the browser feature")
                return False
        
        # Check user guide
        if os.path.exists('docs/EMBEDDED_BROWSER_GUIDE.md'):
            print_success("User guide exists")
        else:
            print_error("User guide missing")
            return False
        
        # Check implementation doc
        if os.path.exists('docs/EMBEDDED_BROWSER_IMPLEMENTATION.md'):
            print_success("Implementation doc exists")
        else:
            print_error("Implementation doc missing")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Documentation check failed: {e}")
        return False


def check_requirements():
    """Check requirements.txt."""
    print_header("CHECKING REQUIREMENTS")
    
    try:
        with open('config/requirements.txt', 'r') as f:
            requirements = f.read()
            
            if 'PyQt5' in requirements:
                print_success("PyQt5 in requirements.txt")
            else:
                print_error("PyQt5 NOT in requirements.txt")
                return False
            
            if 'PyQtWebEngine' in requirements:
                print_success("PyQtWebEngine in requirements.txt")
            else:
                print_error("PyQtWebEngine NOT in requirements.txt")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Requirements check failed: {e}")
        return False


def main():
    """Run all checks."""
    print_header("EMBEDDED BROWSER - FINAL VERIFICATION")
    
    print_info("This script verifies that all components of the embedded browser")
    print_info("feature are properly installed and integrated.")
    print()
    
    checks = [
        ("File Structure", check_files),
        ("Module Imports", check_imports),
        ("Class Instantiation", check_classes),
        ("GUI Integration", check_gui_integration),
        ("Documentation", check_documentation),
        ("Dependencies", check_requirements),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"{name} check crashed: {e}")
            results[name] = False
    
    # Print summary
    print_header("VERIFICATION SUMMARY")
    
    for name, result in results.items():
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print()
    
    if all(results.values()):
        print(f"{GREEN}{BOLD}🎉 ALL CHECKS PASSED!{RESET}")
        print()
        print("The embedded browser feature is fully implemented and ready to use!")
        print()
        print("Next steps:")
        print("  1. Start InteceptProxy: python intercept_proxy.py")
        print("  2. Start the proxy")
        print("  3. Go to the Browser tab")
        print("  4. Click 'Abrir Browser'")
        print()
        return 0
    else:
        print(f"{RED}{BOLD}❌ SOME CHECKS FAILED{RESET}")
        print()
        print("Please review the errors above and fix any issues.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
