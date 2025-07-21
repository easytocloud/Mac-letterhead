#!/usr/bin/env python3

"""
Recovery test script to ensure basic functionality works.
"""

import sys
import os
import tempfile

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from letterhead_pdf.markdown_processor import MarkdownProcessor

def test_basic_functionality():
    """Test basic markdown processing functionality"""
    print("🧪 Testing Basic Functionality")
    print("=" * 50)
    
    # Create a markdown processor instance
    processor = MarkdownProcessor()
    
    # Simple HTML test
    simple_html = """
<h1>Test Document</h1>
<p>This is a simple paragraph.</p>
<ul>
<li>First item</li>
<li>Second item</li>
</ul>
"""
    
    try:
        flowables = processor.markdown_to_flowables(simple_html)
        print(f"✅ Basic processing works: Generated {len(flowables)} flowables")
        return True
    except Exception as e:
        print(f"❌ Basic processing failed: {e}")
        return False

def main():
    """Run recovery test"""
    print("🔄 Mac-letterhead Recovery Test")
    print("=" * 40)
    
    success = test_basic_functionality()
    
    if success:
        print("\n🎉 Recovery successful! Basic functionality is working.")
        print("✨ The optimization can be attempted again with a more conservative approach.")
        return 0
    else:
        print("\n❌ Recovery failed! Please restore from backup manually.")
        print("💡 Run: cp letterhead_pdf/markdown_processor_original.py letterhead_pdf/markdown_processor.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())