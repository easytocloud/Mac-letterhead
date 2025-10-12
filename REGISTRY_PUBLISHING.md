# MCP Registry Publishing Guide

This document describes how to publish and maintain Mac-letterhead in MCP server registries.

## Published Registries

### Official MCP Registry
- **URL**: https://registry.modelcontextprotocol.io
- **Namespace**: `io.github.easytocloud/mac-letterhead`
- **Status**: Published
- **Automatic Sync**: GitHub MCP Registry

### Community Directories
- **mcp.so**: https://mcp.so (community-driven directory)
- **Cline MCP Marketplace**: For Cline IDE integration
- **MCP Index**: https://mcpindex.net (curated directory)

## Prerequisites

### Install mcp-publisher CLI

**Option 1: Homebrew (macOS)**
```bash
brew install mcp-publisher
```

**Option 2: Download Binary**
Download from: https://github.com/modelcontextprotocol/registry/releases

**Option 3: Build from Source**
```bash
git clone https://github.com/modelcontextprotocol/registry.git
cd registry
make publisher
# Binary created at: bin/mcp-publisher
```

## Publishing to Official MCP Registry

### Initial Publication

1. **Authenticate with GitHub**
   ```bash
   # Opens browser for GitHub OAuth
   mcp-publisher login github
   ```
   This proves ownership of the `easytocloud` GitHub account required for the `io.github.easytocloud/*` namespace.

2. **Validate Configuration**
   ```bash
   # Dry run to check for errors
   mcp-publisher publish --dry-run
   ```

3. **Publish to Registry**
   ```bash
   # Publish server.json to official registry
   mcp-publisher publish
   ```

4. **Verify Publication**
   Visit: https://registry.modelcontextprotocol.io/servers/io.github.easytocloud/mac-letterhead

### Version Updates

When releasing a new Mac-letterhead version:

1. **Update version in source files** (handled by `make release-version`):
   - `letterhead_pdf/__init__.py`
   - `Makefile`

2. **Update server.json**
   ```bash
   # Update version field to match new release
   sed -i '' 's/"version": ".*"/"version": "0.13.8"/' server.json

   # Update packages version
   sed -i '' 's/"version": "0.13.7"/"version": "0.13.8"/' server.json
   ```

3. **Publish Updated Version**
   ```bash
   mcp-publisher publish
   ```

4. **Commit Changes**
   ```bash
   git add server.json
   git commit -m "chore: update MCP registry version to 0.13.8"
   ```

## Publishing to Community Directories

### mcp.so Submission

**Option A: Web Submission**
1. Visit: https://mcp.so
2. Click "Submit" button
3. Fill form with:
   - **Name**: Mac-letterhead
   - **Description**: Professional letterhead PDF generator for macOS
   - **Installation**: `uvx mac-letterhead[mcp]`
   - **Command**: `uvx mac-letterhead mcp`
   - **Repository**: https://github.com/easytocloud/Mac-letterhead
   - **Documentation**: https://github.com/easytocloud/Mac-letterhead/blob/main/README_MCP.md
   - **Category**: Document Generation / PDF Tools

**Option B: GitHub Issue**
1. Go to: https://github.com/chatmcp/mcp-directory/issues
2. Create new issue using template in `.github/mcp-directory-submission.md`

### Cline MCP Marketplace

1. Fork: https://github.com/cline/mcp-marketplace
2. Add server entry to marketplace JSON
3. Submit pull request with:
   - Server configuration
   - Installation instructions
   - Usage examples

### MCP Index

1. Visit: https://mcpindex.net
2. Use submission system when available
3. Provide:
   - PyPI package name: `Mac-letterhead`
   - MCP extra: `[mcp]`
   - GitHub repository
   - Documentation links

## Automated Publishing Workflow

The repository includes automated registry publishing in `.github/workflows/publish-registry.yml`.

**Triggers**:
- When new version tags are pushed (v*)
- Manual workflow dispatch
- After successful PyPI publication

**Actions**:
1. Updates `server.json` version fields
2. Authenticates with GitHub
3. Publishes to MCP registry
4. Commits updated `server.json`

## Configuration Examples

Once published, users can find Mac-letterhead MCP server in registries and configure it:

### Generic Multi-Style Server
```json
{
  "mcpServers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"]
    }
  }
}
```

### Style-Specific Server
```json
{
  "mcpServers": {
    "easytocloud": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "easytocloud"]
    }
  }
}
```

### Custom Configuration
```json
{
  "mcpServers": {
    "company-docs": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "company",
        "--output-dir", "~/Documents/generated-pdfs",
        "--output-prefix", "CompanyDocs"
      ]
    }
  }
}
```

## Troubleshooting

### Authentication Issues
```bash
# Re-authenticate if token expired
mcp-publisher login github

# Check authentication status
mcp-publisher whoami
```

### Validation Errors
```bash
# Validate server.json schema
mcp-publisher publish --dry-run

# Common issues:
# - Version mismatch between server.json and PyPI
# - Invalid namespace format
# - Missing required fields
```

### Namespace Conflicts
The `io.github.easytocloud/*` namespace is reserved for repositories under the `easytocloud` GitHub account. Authentication proves ownership.

## Monitoring and Maintenance

### Check Registry Status
- Official Registry: https://registry.modelcontextprotocol.io/servers/io.github.easytocloud/mac-letterhead
- GitHub Registry: Automatically synced from official registry
- Community Directories: Check individual directory listings

### Update Frequency
- **Critical Updates**: Publish immediately after PyPI release
- **Feature Releases**: Publish after successful release validation
- **Documentation Changes**: Update every 2-3 releases or as needed

### Deprecation
If discontinuing MCP server support:
1. Update `server.json` with deprecation notice
2. Publish final version to registry
3. Update README and documentation
4. Provide migration guide if applicable

## Additional Resources

- **Official MCP Registry**: https://github.com/modelcontextprotocol/registry
- **MCP Documentation**: https://modelcontextprotocol.io
- **Publishing Guide**: https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md
- **Registry API Docs**: https://registry.modelcontextprotocol.io/docs
- **Mac-letterhead MCP Docs**: README_MCP.md, llms-install.md

## Support

For registry-related issues:
- **MCP Registry**: https://github.com/modelcontextprotocol/registry/issues
- **Mac-letterhead MCP**: https://github.com/easytocloud/Mac-letterhead/issues

For general MCP questions:
- **MCP Discussions**: https://github.com/orgs/modelcontextprotocol/discussions
