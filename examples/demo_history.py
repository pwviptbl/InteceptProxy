#!/usr/bin/env python3
"""
Demo script to show the history functionality
"""
import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.history import RequestHistory
from unittest.mock import Mock
from datetime import datetime, timedelta

def demo_history():
    """Demonstrates the history functionality"""
    print("=" * 70)
    print("REQUEST HISTORY FEATURE DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Create history instance
    history = RequestHistory()
    print("✓ Created RequestHistory instance")
    print(f"  Max items: {history.max_items}")
    print()
    
    # Simulate some requests
    print("Simulating captured requests...")
    print("-" * 70)
    
    requests_data = [
        ("google.com", "GET", 200, "/search?q=test"),
        ("facebook.com", "POST", 201, "/api/post"),
        ("google.com", "GET", 200, "/maps"),
        ("api.exemplo.com", "POST", 200, "/v1/users"),
        ("test.com", "DELETE", 204, "/api/item/123"),
        ("google.com", "GET", 404, "/notfound"),
    ]
    
    for i, (host, method, status, path) in enumerate(requests_data):
        mock_flow = Mock()
        mock_flow.request = Mock()
        mock_flow.request.pretty_host = host
        mock_flow.request.method = method
        mock_flow.request.pretty_url = f"http://{host}{path}"
        mock_flow.request.path = path
        mock_flow.request.headers = {"User-Agent": "Demo/1.0"}
        mock_flow.request.content = f"body_{i}".encode()
        
        mock_flow.response = Mock()
        mock_flow.response.status_code = status
        mock_flow.response.headers = {"Content-Type": "text/html"}
        mock_flow.response.content = f"response_{i}".encode()
        
        history.add_request(mock_flow)
        print(f"  {i+1}. {method:6} {host:20} {status} {path}")
    
    print()
    print(f"✓ Added {len(history.get_history())} requests to history")
    print()
    
    # Demonstrate filtering
    print("FILTER EXAMPLES")
    print("=" * 70)
    print()
    
    # Filter by method
    print("1. Filter by Method: GET")
    print("-" * 70)
    get_requests = [e for e in history.get_history() if e['method'] == 'GET']
    for entry in get_requests:
        date_str = entry['timestamp'].strftime('%d/%m/%Y')
        time_str = entry['timestamp'].strftime('%H:%M:%S')
        print(f"  {entry['host']:20} {date_str} {time_str} {entry['method']:6} {entry['status']}")
    print(f"  Total: {len(get_requests)} requests")
    print()
    
    # Filter by domain (regex)
    print("2. Filter by Domain (regex): google.com|facebook.com")
    print("-" * 70)
    import re
    regex = re.compile("google.com|facebook.com", re.IGNORECASE)
    filtered = [e for e in history.get_history() if regex.search(e['host'])]
    for entry in filtered:
        date_str = entry['timestamp'].strftime('%d/%m/%Y')
        time_str = entry['timestamp'].strftime('%H:%M:%S')
        print(f"  {entry['host']:20} {date_str} {time_str} {entry['method']:6} {entry['status']}")
    print(f"  Total: {len(filtered)} requests")
    print()
    
    # Combined filter
    print("3. Combined Filter: Method=POST AND Domain=api.*")
    print("-" * 70)
    regex = re.compile(r"api\..*", re.IGNORECASE)
    combined = [e for e in history.get_history() 
                if e['method'] == 'POST' and regex.search(e['host'])]
    for entry in combined:
        date_str = entry['timestamp'].strftime('%d/%m/%Y')
        time_str = entry['timestamp'].strftime('%H:%M:%S')
        print(f"  {entry['host']:20} {date_str} {time_str} {entry['method']:6} {entry['status']}")
    print(f"  Total: {len(combined)} requests")
    print()
    
    # Show detail example
    print("4. Request Details Example")
    print("-" * 70)
    entry = history.get_history()[0]
    print(f"URL: {entry['url']}")
    print(f"Método: {entry['method']}")
    print(f"Host: {entry['host']}")
    print(f"Path: {entry['path']}")
    print(f"Status: {entry['status']}")
    print(f"\nRequest Headers:")
    for key, value in entry['request_headers'].items():
        print(f"  {key}: {value}")
    print(f"\nRequest Body:\n  {entry['request_body']}")
    print(f"\nResponse Headers:")
    for key, value in entry['response_headers'].items():
        print(f"  {key}: {value}")
    print(f"\nResponse Body:\n  {entry['response_body']}")
    print()
    
    # Test clear
    print("5. Clear History")
    print("-" * 70)
    print(f"  Before: {len(history.get_history())} requests")
    history.clear_history()
    print(f"  After: {len(history.get_history())} requests")
    print()
    
    print("=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    demo_history()
