#!/bin/bash

# Setup script for Mac-letterhead MCP servers
# Creates the ~/.letterhead directory structure

echo "Setting up Mac-letterhead MCP server configuration..."

# Create the letterhead directory
mkdir -p ~/.letterhead
echo "✓ Created ~/.letterhead directory"

# Create sample CSS file if it doesn't exist
if [ ! -f ~/.letterhead/sample.css ]; then
    cat > ~/.letterhead/sample.css << 'EOF'
/* Sample CSS for Mac-letterhead */
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333;
}

h1 {
    font-size: 16pt;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 5pt;
    margin-bottom: 12pt;
}

h2 {
    font-size: 14pt;
    color: #34495e;
    margin-top: 18pt;
    margin-bottom: 8pt;
}

h3 {
    font-size: 12pt;
    color: #7f8c8d;
    margin-top: 14pt;
    margin-bottom: 6pt;
}

p {
    margin-bottom: 8pt;
    text-align: justify;
}

ul, ol {
    margin-bottom: 10pt;
    padding-left: 20pt;
}

li {
    margin-bottom: 4pt;
}

blockquote {
    border-left: 3pt solid #bdc3c7;
    padding-left: 15pt;
    margin-left: 10pt;
    font-style: italic;
    color: #7f8c8d;
}

code {
    background-color: #f8f9fa;
    padding: 2pt 4pt;
    border-radius: 3pt;
    font-family: "Monaco", "Consolas", monospace;
    font-size: 9pt;
}

pre {
    background-color: #f8f9fa;
    padding: 10pt;
    border-radius: 5pt;
    border: 1pt solid #e9ecef;
    overflow-x: auto;
    margin: 10pt 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
}

th, td {
    border: 1pt solid #dee2e6;
    padding: 6pt;
    text-align: left;
}

th {
    background-color: #f8f9fa;
    font-weight: bold;
}

a {
    color: #3498db;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
EOF
    echo "✓ Created sample CSS file: ~/.letterhead/sample.css"
fi

echo ""
echo "Next steps:"
echo "1. Place your letterhead PDF files in ~/.letterhead/"
echo "   Example: ~/.letterhead/easytocloud.pdf"
echo ""
echo "2. Optionally create matching CSS files:"
echo "   Example: ~/.letterhead/easytocloud.css"
echo "   (You can use ~/.letterhead/sample.css as a starting point)"
echo ""
echo "3. Configure your MCP client with servers like:"
echo '   "easytocloud": {"command": "uvx", "args": ["mac-letterhead[mcp]", "mcp-letterhead", "--name", "easytocloud"]}'
echo ""
echo "4. Then ask Claude: 'Create an easytocloud letterheaded PDF with...'"
echo ""
echo "Directory structure:"
ls -la ~/.letterhead/ 2>/dev/null || echo "   (empty - add your letterhead files here)"