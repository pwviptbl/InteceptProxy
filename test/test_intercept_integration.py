#!/usr/bin/env python3
"""
Integration test for intercept manual feature
Tests the interaction between addon and config
"""
import os
import sys
import threading
import time
from unittest.mock import Mock, MagicMock

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import InterceptConfig


def test_intercept_integration():
    """Test the integration between addon and config"""
    print("Testing Intercept Manual Integration...")
    
    config = InterceptConfig("test_integration_config.json")
    
    # Test 1: Simulate addon adding request to queue
    print("\nTest 1: Addon adds request to intercept queue")
    
    # Enable intercept
    config.toggle_intercept()
    assert config.is_intercept_enabled() == True
    
    # Simulate addon preparing flow data
    mock_flow_data = {
        'method': 'POST',
        'url': 'http://example.com/login',
        'headers': {'Host': 'example.com', 'Content-Type': 'application/x-www-form-urlencoded'},
        'body': 'username=admin&password=test',
        'host': 'example.com',
        'path': '/login'
    }
    
    # Addon adds to queue (non-blocking)
    config.add_to_intercept_queue(mock_flow_data)
    print("✓ Addon added request to queue")
    
    # Test 2: Simulate GUI retrieving from queue
    print("\nTest 2: GUI retrieves request from queue")
    
    retrieved = config.get_from_intercept_queue(timeout=0.1)
    assert retrieved is not None, "Should retrieve request"
    assert retrieved['method'] == 'POST', "Method should match"
    assert retrieved['url'] == 'http://example.com/login', "URL should match"
    print("✓ GUI retrieved request successfully")
    
    # Test 3: Simulate user clicking Forward
    print("\nTest 3: User clicks Forward button")
    
    # GUI prepares response
    user_response = {
        'action': 'forward',
        'modified_headers': {
            'Host': 'example.com',
            'Content-Type': 'application/json'  # User changed this
        },
        'modified_body': 'username=hacker&password=test'  # User modified this
    }
    
    # GUI adds response to queue (non-blocking)
    config.add_intercept_response(user_response)
    print("✓ GUI added user response to queue")
    
    # Addon retrieves response (would be blocking in real scenario)
    response = config.get_intercept_response(timeout=0.1)
    assert response is not None, "Should retrieve response"
    assert response['action'] == 'forward', "Action should be forward"
    assert response['modified_body'] == 'username=hacker&password=test', "Body should be modified"
    print("✓ Addon retrieved user response")
    print(f"  - Action: {response['action']}")
    print(f"  - Modified body: {response['modified_body']}")
    
    # Test 4: Simulate user clicking Drop
    print("\nTest 4: User clicks Drop button")
    
    # Add another request
    config.add_to_intercept_queue(mock_flow_data)
    retrieved = config.get_from_intercept_queue(timeout=0.1)
    assert retrieved is not None
    
    # User decides to drop
    drop_response = {'action': 'drop'}
    config.add_intercept_response(drop_response)
    
    response = config.get_intercept_response(timeout=0.1)
    assert response is not None, "Should retrieve response"
    assert response['action'] == 'drop', "Action should be drop"
    print("✓ Drop action works correctly")
    
    # Test 5: Simulate timeout scenario
    print("\nTest 5: Timeout scenario (user doesn't respond)")
    
    # Add request but don't respond
    config.add_to_intercept_queue(mock_flow_data)
    retrieved = config.get_from_intercept_queue(timeout=0.1)
    assert retrieved is not None
    
    # Addon waits for response with short timeout (simulating 5 min timeout)
    start = time.time()
    response = config.get_intercept_response(timeout=0.2)  # 200ms timeout
    elapsed = time.time() - start
    
    assert response is None, "Should timeout and return None"
    assert elapsed >= 0.2, "Should wait at least timeout duration"
    print(f"✓ Timeout works correctly (waited {elapsed:.2f}s)")
    
    # Test 6: Thread safety test
    print("\nTest 6: Thread safety (concurrent access)")
    
    results = {'gui_retrieved': 0, 'addon_added': 0}
    
    def addon_thread():
        """Simulate addon adding requests"""
        for i in range(10):
            config.add_to_intercept_queue({'id': i, 'method': 'GET'})
            results['addon_added'] += 1
            time.sleep(0.01)
    
    def gui_thread():
        """Simulate GUI retrieving requests"""
        for _ in range(10):
            req = config.get_from_intercept_queue(timeout=0.5)
            if req:
                results['gui_retrieved'] += 1
    
    # Start threads
    t1 = threading.Thread(target=addon_thread)
    t2 = threading.Thread(target=gui_thread)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    assert results['addon_added'] == 10, "All requests should be added"
    assert results['gui_retrieved'] == 10, "All requests should be retrieved"
    print(f"✓ Thread safety verified (added: {results['addon_added']}, retrieved: {results['gui_retrieved']})")
    
    # Test 7: Clear queues while items in queue
    print("\nTest 7: Clear queues with items")
    
    # Add items to both queues
    for i in range(5):
        config.add_to_intercept_queue({'id': i})
        config.add_intercept_response({'id': i})
    
    # Verify queues are not empty
    assert not config.intercept_queue.empty(), "Request queue should not be empty"
    assert not config.intercept_response_queue.empty(), "Response queue should not be empty"
    
    # Clear
    config.clear_intercept_queues()
    
    # Verify both queues are empty
    assert config.intercept_queue.empty(), "Request queue should be empty"
    assert config.intercept_response_queue.empty(), "Response queue should be empty"
    print("✓ Clear queues works correctly")
    
    # Test 8: Disable intercept and verify state
    print("\nTest 8: Disable intercept")
    
    config.toggle_intercept()
    assert config.is_intercept_enabled() == False, "Intercept should be disabled"
    print("✓ Intercept disabled successfully")
    
    print("\n" + "="*60)
    print("✅ All integration tests passed!")
    print("="*60)
    print("\nSummary:")
    print("- Request/response queue operations work correctly")
    print("- Forward and Drop actions work as expected")
    print("- Timeout handling works properly")
    print("- Thread-safe operations verified")
    print("- Queue clearing works correctly")
    print("\nThe Intercept Manual feature is ready to use! 🎉")
    
    # Cleanup
    import os
    if os.path.exists("test_integration_config.json"):
        os.remove("test_integration_config.json")
    
    return 0


if __name__ == "__main__":
    sys.exit(test_intercept_integration())
