#!/usr/bin/env python3
"""
Test script for Advanced Sender functionality
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.advanced_sender import (
    PayloadProcessor, 
    PayloadPositionParser, 
    AttackTypeGenerator,
    GrepExtractor,
    AdvancedSender
)


def test_payload_processor():
    """Test payload processing functions"""
    print("\n=== Testing Payload Processors ===")
    
    # URL Encoding
    result = PayloadProcessor.url_encode("test value")
    assert result == "test%20value", f"URL encode failed: {result}"
    print("✓ URL encode works")
    
    # Base64 Encoding
    result = PayloadProcessor.base64_encode("test")
    assert result == "dGVzdA==", f"Base64 encode failed: {result}"
    print("✓ Base64 encode works")
    
    # HTML Encoding
    result = PayloadProcessor.html_encode("<script>alert(1)</script>")
    assert "&lt;script&gt;" in result, f"HTML encode failed: {result}"
    print("✓ HTML encode works")
    
    # MD5 Hash
    result = PayloadProcessor.md5_hash("test")
    assert result == "098f6bcd4621d373cade4e832627b4f6", f"MD5 hash failed: {result}"
    print("✓ MD5 hash works")
    
    # SHA256 Hash
    result = PayloadProcessor.sha256_hash("test")
    assert len(result) == 64, f"SHA256 hash failed: {result}"
    print("✓ SHA256 hash works")
    
    # Prefix
    result = PayloadProcessor.add_prefix("value", "test_")
    assert result == "test_value", f"Prefix failed: {result}"
    print("✓ Prefix works")
    
    # Suffix
    result = PayloadProcessor.add_suffix("value", "_test")
    assert result == "value_test", f"Suffix failed: {result}"
    print("✓ Suffix works")
    
    # Hex encoding
    result = PayloadProcessor.hex_encode("test")
    assert result == "74657374", f"Hex encode failed: {result}"
    print("✓ Hex encode works")
    
    # Processor chain
    processors = [
        {'type': 'prefix', 'value': 'pre_'},
        {'type': 'suffix', 'value': '_suf'},
        {'type': 'url_encode'}
    ]
    result = PayloadProcessor.apply_processors("test", processors)
    assert result == "pre_test_suf", f"Processor chain failed: {result}"
    print("✓ Processor chain works")
    
    print("All payload processor tests passed! ✓")


def test_payload_position_parser():
    """Test payload position parsing"""
    print("\n=== Testing Payload Position Parser ===")
    
    # Find positions
    request = "GET /path?param1=§value1§&param2=§value2§ HTTP/1.1"
    positions = PayloadPositionParser.find_positions(request)
    assert len(positions) == 2, f"Should find 2 positions, found {len(positions)}"
    assert positions[0][2] == "value1", f"First position value incorrect: {positions[0][2]}"
    assert positions[1][2] == "value2", f"Second position value incorrect: {positions[1][2]}"
    print("✓ Position finding works")
    
    # Count positions
    count = PayloadPositionParser.count_positions(request)
    assert count == 2, f"Should count 2 positions, got {count}"
    print("✓ Position counting works")
    
    # Replace positions
    replaced = PayloadPositionParser.replace_positions(request, ["NEW1", "NEW2"])
    assert "NEW1" in replaced, "First payload not replaced"
    assert "NEW2" in replaced, "Second payload not replaced"
    assert "§" not in replaced, "Markers not removed"
    print("✓ Position replacement works")
    
    print("All position parser tests passed! ✓")


def test_attack_type_sniper():
    """Test Sniper attack type"""
    print("\n=== Testing Sniper Attack ===")
    
    payloads = [["a", "b", "c"]]
    combinations = AttackTypeGenerator.sniper(payloads, 2)
    
    # Should have 6 combinations (3 payloads * 2 positions)
    assert len(combinations) == 6, f"Sniper should generate 6 combinations, got {len(combinations)}"
    
    # Check that only one position changes at a time
    for combo in combinations:
        originals = sum(1 for val in combo if val == '§ORIGINAL§')
        assert originals == 1, f"Sniper should keep 1 position original, got {originals}"
    
    print(f"✓ Sniper generated {len(combinations)} combinations correctly")
    print("Sniper attack test passed! ✓")


def test_attack_type_battering_ram():
    """Test Battering Ram attack type"""
    print("\n=== Testing Battering Ram Attack ===")
    
    payloads = [["a", "b", "c"]]
    combinations = AttackTypeGenerator.battering_ram(payloads, 2)
    
    # Should have 3 combinations (same as payload count)
    assert len(combinations) == 3, f"Battering Ram should generate 3 combinations, got {len(combinations)}"
    
    # Check that all positions have same value
    for combo in combinations:
        assert combo[0] == combo[1], f"Battering Ram should use same payload in all positions: {combo}"
    
    print(f"✓ Battering Ram generated {len(combinations)} combinations correctly")
    print("Battering Ram attack test passed! ✓")


def test_attack_type_pitchfork():
    """Test Pitchfork attack type"""
    print("\n=== Testing Pitchfork Attack ===")
    
    payload_sets = [["a", "b", "c"], ["x", "y", "z"]]
    combinations = AttackTypeGenerator.pitchfork(payload_sets, 2)
    
    # Should have 3 combinations (min length of sets)
    assert len(combinations) == 3, f"Pitchfork should generate 3 combinations, got {len(combinations)}"
    
    # Check parallel iteration
    assert combinations[0] == ["a", "x"], f"First combination incorrect: {combinations[0]}"
    assert combinations[1] == ["b", "y"], f"Second combination incorrect: {combinations[1]}"
    assert combinations[2] == ["c", "z"], f"Third combination incorrect: {combinations[2]}"
    
    print(f"✓ Pitchfork generated {len(combinations)} combinations correctly")
    print("Pitchfork attack test passed! ✓")


def test_attack_type_cluster_bomb():
    """Test Cluster Bomb attack type"""
    print("\n=== Testing Cluster Bomb Attack ===")
    
    payload_sets = [["a", "b"], ["x", "y"]]
    combinations = AttackTypeGenerator.cluster_bomb(payload_sets, 2)
    
    # Should have 4 combinations (2 * 2)
    assert len(combinations) == 4, f"Cluster Bomb should generate 4 combinations, got {len(combinations)}"
    
    # Check all combinations exist
    expected = [["a", "x"], ["a", "y"], ["b", "x"], ["b", "y"]]
    for exp in expected:
        assert exp in combinations, f"Missing combination: {exp}"
    
    print(f"✓ Cluster Bomb generated {len(combinations)} combinations correctly")
    print("Cluster Bomb attack test passed! ✓")


def test_grep_extractor():
    """Test grep extraction from responses"""
    print("\n=== Testing Grep Extractor ===")
    
    patterns = [r'token=([a-zA-Z0-9]+)', r'id=(\d+)']
    extractor = GrepExtractor(patterns)
    
    response_text = "Welcome! Your token=abc123def and id=42 is ready."
    matches = extractor.extract(response_text)
    
    assert len(matches) == 2, f"Should extract 2 matches, got {len(matches)}"
    assert "abc123def" in matches, "Token not extracted"
    assert "42" in matches, "ID not extracted"
    
    print(f"✓ Extracted {len(matches)} matches: {matches}")
    print("Grep extractor test passed! ✓")


def test_advanced_sender_request_generation():
    """Test request generation with different attack types"""
    print("\n=== Testing Advanced Sender Request Generation ===")
    
    raw_request = "GET /test?user=§admin§&pass=§password§ HTTP/1.1\nHost: example.com\n\n"
    
    # Test Sniper
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='sniper',
        payload_sets=[['test1', 'test2']],
        num_threads=1
    )
    requests = sender.generate_requests()
    assert len(requests) == 4, f"Sniper should generate 4 requests, got {len(requests)}"
    print(f"✓ Sniper generated {len(requests)} requests")
    
    # Test Battering Ram
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='battering_ram',
        payload_sets=[['test1', 'test2']],
        num_threads=1
    )
    requests = sender.generate_requests()
    assert len(requests) == 2, f"Battering Ram should generate 2 requests, got {len(requests)}"
    print(f"✓ Battering Ram generated {len(requests)} requests")
    
    # Test Pitchfork
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='pitchfork',
        payload_sets=[['user1', 'user2'], ['pass1', 'pass2']],
        num_threads=1
    )
    requests = sender.generate_requests()
    assert len(requests) == 2, f"Pitchfork should generate 2 requests, got {len(requests)}"
    print(f"✓ Pitchfork generated {len(requests)} requests")
    
    # Test Cluster Bomb
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='cluster_bomb',
        payload_sets=[['user1', 'user2'], ['pass1', 'pass2']],
        num_threads=1
    )
    requests = sender.generate_requests()
    assert len(requests) == 4, f"Cluster Bomb should generate 4 requests, got {len(requests)}"
    print(f"✓ Cluster Bomb generated {len(requests)} requests")
    
    print("Advanced Sender request generation tests passed! ✓")


def test_payload_processing_integration():
    """Test payload processing integration with request generation"""
    print("\n=== Testing Payload Processing Integration ===")
    
    raw_request = "GET /test?param=§value§ HTTP/1.1\nHost: example.com\n\n"
    
    processors = [
        [
            {'type': 'prefix', 'value': 'test_'},
            {'type': 'url_encode'}
        ]
    ]
    
    sender = AdvancedSender(
        raw_request=raw_request,
        attack_type='battering_ram',
        payload_sets=[['admin', 'user']],
        processors=processors,
        num_threads=1
    )
    
    requests = sender.generate_requests()
    assert len(requests) == 2, f"Should generate 2 requests, got {len(requests)}"
    
    # Check that processing was applied
    # First request should have "test_admin" URL encoded
    assert "test_admin" in requests[0][0], f"Prefix not applied: {requests[0][0]}"
    
    print("✓ Payload processing integrated correctly")
    print("Payload processing integration test passed! ✓")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Advanced Sender Tests")
    print("=" * 60)
    
    try:
        test_payload_processor()
        test_payload_position_parser()
        test_attack_type_sniper()
        test_attack_type_battering_ram()
        test_attack_type_pitchfork()
        test_attack_type_cluster_bomb()
        test_grep_extractor()
        test_advanced_sender_request_generation()
        test_payload_processing_integration()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED! ✓")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
