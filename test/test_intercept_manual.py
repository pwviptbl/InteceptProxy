#!/usr/bin/env python3
"""
Test script for intercept manual feature logic
"""
import os
import sys
import time

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import InterceptConfig


def test_intercept_config():
    """Test the intercept config functionality"""
    print("Testing Intercept Manual Configuration...")
    
    config = InterceptConfig("test_intercept_config.json")
    
    # Test 1: Initial state
    print("\nTest 1: Initial state")
    assert config.is_intercept_enabled() == False, "Intercept should be disabled initially"
    print("✓ Intercept is disabled initially")
    
    # Test 2: Toggle intercept ON
    print("\nTest 2: Toggle intercept ON")
    enabled = config.toggle_intercept()
    assert enabled == True, "Intercept should be enabled after toggle"
    assert config.is_intercept_enabled() == True, "is_intercept_enabled should return True"
    print("✓ Intercept toggled ON successfully")
    
    # Test 3: Toggle intercept OFF
    print("\nTest 3: Toggle intercept OFF")
    enabled = config.toggle_intercept()
    assert enabled == False, "Intercept should be disabled after second toggle"
    assert config.is_intercept_enabled() == False, "is_intercept_enabled should return False"
    print("✓ Intercept toggled OFF successfully")
    
    # Test 4: Queue operations
    print("\nTest 4: Queue operations")
    
    # Add to queue
    test_data = {'method': 'GET', 'url': 'http://example.com', 'body': 'test'}
    config.add_to_intercept_queue(test_data)
    print("✓ Added data to intercept queue")
    
    # Get from queue
    retrieved_data = config.get_from_intercept_queue()
    assert retrieved_data == test_data, "Retrieved data should match added data"
    print("✓ Retrieved data from intercept queue")
    
    # Queue should be empty now
    empty_data = config.get_from_intercept_queue(timeout=0.1)
    assert empty_data is None, "Queue should be empty"
    print("✓ Queue is empty after retrieval")
    
    # Test 5: Response queue
    print("\nTest 5: Response queue")
    
    response_data = {'action': 'forward', 'modified_body': 'modified'}
    config.add_intercept_response(response_data)
    print("✓ Added response to queue")
    
    retrieved_response = config.get_intercept_response(timeout=1)
    assert retrieved_response == response_data, "Retrieved response should match added response"
    print("✓ Retrieved response from queue")
    
    # Test 6: Clear queues
    print("\nTest 6: Clear queues")
    
    # Add multiple items
    for i in range(5):
        config.add_to_intercept_queue({'id': i})
        config.add_intercept_response({'id': i})
    
    print("✓ Added 5 items to each queue")
    
    config.clear_intercept_queues()
    print("✓ Cleared all queues")
    
    # Verify queues are empty
    assert config.get_from_intercept_queue(timeout=0.1) is None, "Intercept queue should be empty"
    assert config.get_intercept_response(timeout=0.1) is None, "Response queue should be empty"
    print("✓ Queues are empty after clear")
    
    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50)
    
    # Cleanup
    import os
    if os.path.exists("test_intercept_config.json"):
        os.remove("test_intercept_config.json")
    
    return 0


if __name__ == "__main__":
    sys.exit(test_intercept_config())
