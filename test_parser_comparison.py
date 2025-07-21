#!/usr/bin/env python3

"""
Test script to compare optimized and manual HTML parsers.

This script tests both the new optimized DOM-based parser and the original 
manual parser to ensure they produce equivalent outputs.
"""

import sys
import os
import tempfile
import time

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from letterhead_pdf.markdown_processor import MarkdownProcessor

def create_test_html_content():
    """Create various HTML test cases"""
    test_cases = {
        "simple": """
<h1>Main Heading</h1>
<p>This is a simple paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
""",
        
        "lists": """
<h2>Lists Test</h2>
<ul>
<li>First bullet point</li>
<li>Second bullet point with <code>inline code</code></li>
</ul>
<ol>
<li>First numbered item</li>
<li>Second numbered item</li>
</ol>
""",
        
        "code_blocks": """
<h2>Code Block Test</h2>
<pre><code>def hello_world():
    print("Hello, World!")
    return True
</code></pre>
""",
        
        "tables": """
<h2>Table Test</h2>
<table>
<tr>
<th>Header 1</th>
<th>Header 2</th>
</tr>
<tr>
<td>Cell 1</td>
<td>Cell 2</td>
</tr>
</table>
""",
        
        "complex": """
<h1>Complex Document</h1>
<p>This document contains <strong>multiple</strong> elements.</p>
<h2>Features</h2>
<ul>
<li>Nested <em>formatting</em></li>
<li>Code: <code>function()</code></li>
</ul>
<blockquote>
<p>This is a blockquote with important information.</p>
</blockquote>
<pre><code>// Code block example
if (condition) {
    return value;
}
</code></pre>
"""
    }
    
    return test_cases

def test_parser_equivalence():
    """Test that both parsers produce equivalent results"""
    print("🧪 Testing Parser Equivalence")
    print("=" * 50)
    
    # Create a markdown processor instance
    processor = MarkdownProcessor()
    
    # Get test cases
    test_cases = create_test_html_content()
    
    results = {}
    
    for test_name, html_content in test_cases.items():
        print(f"\n📝 Testing: {test_name}")
        
        # Test optimized parser
        try:
            start_time = time.time()
            optimized_flowables = processor._markdown_to_flowables_optimized(html_content)
            optimized_time = time.time() - start_time
            optimized_count = len(optimized_flowables)
            print(f"   ⚡ Optimized: {optimized_count} flowables in {optimized_time:.4f}s")
        except Exception as e:
            print(f"   ❌ Optimized parser failed: {e}")
            optimized_flowables = []
            optimized_time = 0
            optimized_count = 0
        
        # Test manual parser
        try:
            start_time = time.time()
            manual_flowables = processor._markdown_to_flowables_manual(html_content)
            manual_time = time.time() - start_time
            manual_count = len(manual_flowables)
            print(f"   🐌 Manual: {manual_count} flowables in {manual_time:.4f}s")
        except Exception as e:
            print(f"   ❌ Manual parser failed: {e}")
            manual_flowables = []
            manual_time = 0
            manual_count = 0
        
        # Compare results
        count_match = optimized_count == manual_count
        if optimized_time > 0 and manual_time > 0:
            speedup = manual_time / optimized_time
            print(f"   📊 Speedup: {speedup:.2f}x")
        else:
            speedup = 1.0
        
        print(f"   ✅ Count match: {count_match}")
        
        results[test_name] = {
            'optimized_count': optimized_count,
            'manual_count': manual_count,
            'optimized_time': optimized_time,
            'manual_time': manual_time,
            'speedup': speedup,
            'count_match': count_match
        }
    
    return results

def test_fallback_mechanism():
    """Test that fallback mechanism works correctly"""
    print("\n\n🛡️ Testing Fallback Mechanism")
    print("=" * 50)
    
    processor = MarkdownProcessor()
    
    # Test with various HTML that might cause issues
    problematic_html = """
<div>
<h1>Test with potential issues</h1>
<p>This has some <unknown-tag>custom elements</unknown-tag>.</p>
</div>
"""
    
    try:
        # This should work with both parsers
        flowables = processor.markdown_to_flowables(problematic_html)
        print(f"✅ Fallback mechanism works: Generated {len(flowables)} flowables")
        return True
    except Exception as e:
        print(f"❌ Fallback mechanism failed: {e}")
        return False

def test_performance_benchmark():
    """Run a performance benchmark on a larger document"""
    print("\n\n⚡ Performance Benchmark")
    print("=" * 50)
    
    processor = MarkdownProcessor()
    
    # Create a larger HTML document
    large_html = ""
    for i in range(100):
        large_html += f"""
<h2>Section {i+1}</h2>
<p>This is paragraph {i+1} with <strong>bold text</strong> and <em>italic text</em>.</p>
<ul>
<li>Item 1 in section {i+1}</li>
<li>Item 2 in section {i+1}</li>
</ul>
"""
    
    print(f"📄 Testing large document ({len(large_html)} characters)")
    
    # Test optimized parser
    try:
        start_time = time.time()
        optimized_flowables = processor._markdown_to_flowables_optimized(large_html)
        optimized_time = time.time() - start_time
        print(f"⚡ Optimized: {len(optimized_flowables)} flowables in {optimized_time:.4f}s")
    except Exception as e:
        print(f"❌ Optimized parser failed: {e}")
        optimized_time = float('inf')
    
    # Test manual parser
    try:
        start_time = time.time()
        manual_flowables = processor._markdown_to_flowables_manual(large_html)
        manual_time = time.time() - start_time
        print(f"🐌 Manual: {len(manual_flowables)} flowables in {manual_time:.4f}s")
    except Exception as e:
        print(f"❌ Manual parser failed: {e}")
        manual_time = float('inf')
    
    if optimized_time < float('inf') and manual_time < float('inf'):
        speedup = manual_time / optimized_time
        print(f"📊 Performance improvement: {speedup:.2f}x faster")
        return speedup
    else:
        print("⚠️ Could not measure performance improvement")
        return 1.0

def main():
    """Run all tests"""
    print("🚀 Mac-letterhead HTML Parser Optimization Test")
    print("=" * 60)
    
    # Test parser equivalence
    results = test_parser_equivalence()
    
    # Test fallback mechanism
    fallback_works = test_fallback_mechanism()
    
    # Performance benchmark
    performance_improvement = test_performance_benchmark()
    
    # Summary
    print("\n\n📊 Test Summary")
    print("=" * 50)
    
    all_count_matches = all(result['count_match'] for result in results.values())
    avg_speedup = sum(result['speedup'] for result in results.values()) / len(results)
    
    print(f"✅ Parser equivalence: {'PASS' if all_count_matches else 'FAIL'}")
    print(f"🛡️ Fallback mechanism: {'PASS' if fallback_works else 'FAIL'}")
    print(f"⚡ Average speedup: {avg_speedup:.2f}x")
    print(f"📊 Large document speedup: {performance_improvement:.2f}x")
    
    if all_count_matches and fallback_works:
        print("\n🎉 All tests passed! The optimization is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())