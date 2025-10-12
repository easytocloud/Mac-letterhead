# Quick Start: Publishing to MCP Registries

This guide provides the essential steps to publish Mac-letterhead MCP server to registries.

## Prerequisites Checklist

- [x] `server.json` created in repository root ✅
- [x] GitHub workflow configured for automated publishing ✅
- [x] Documentation updated with registry information ✅
- [ ] mcp-publisher CLI tool installed
- [ ] Authenticated with GitHub
- [ ] Published to official MCP registry

## Step 1: Install mcp-publisher

Choose your preferred installation method:

### Option A: Homebrew (Recommended for macOS)
```bash
brew install mcp-publisher
```

### Option B: Download Binary
1. Visit: https://github.com/modelcontextprotocol/registry/releases
2. Download the latest macOS binary
3. Extract and move to `/usr/local/bin/`

### Option C: Build from Source
```bash
git clone https://github.com/modelcontextprotocol/registry.git
cd registry
make publisher
# Binary created at: bin/mcp-publisher
```

Verify installation:
```bash
mcp-publisher --version
```

## Step 2: Authenticate with GitHub

```bash
# Opens browser for GitHub OAuth authentication
mcp-publisher login github
```

This proves you own the `easytocloud` GitHub account, required for the `io.github.easytocloud/*` namespace.

Verify authentication:
```bash
mcp-publisher whoami
```

## Step 3: Validate Configuration

```bash
# Dry run to check for errors (doesn't publish)
mcp-publisher publish --dry-run
```

Fix any validation errors before proceeding.

## Step 4: Publish to Official MCP Registry

```bash
# Publish server.json to the registry
mcp-publisher publish
```

Expected output:
```
✓ Validated server configuration
✓ Authenticated as easytocloud
✓ Published io.github.easytocloud/mac-letterhead
✓ Version 0.13.7 is now live
```

## Step 5: Verify Publication

Visit the registry to confirm:
- **Official Registry**: https://registry.modelcontextprotocol.io/servers/io.github.easytocloud/mac-letterhead
- **GitHub Registry**: Will automatically sync within minutes

## Step 6: Submit to Community Directories

### mcp.so
1. Visit: https://mcp.so
2. Click "Submit" button
3. Use template from `.github/mcp-directory-submission.md`

**OR** create GitHub issue:
1. Go to: https://github.com/chatmcp/mcp-directory/issues
2. Title: "Submit Mac-letterhead MCP Server"
3. Paste content from submission template

### Other Directories
- **Cline MCP Marketplace**: Fork and PR to https://github.com/cline/mcp-marketplace
- **MCP Index**: Submit when form becomes available at https://mcpindex.net

## Automated Updates

The GitHub workflow `.github/workflows/publish-mcp-registry.yml` automatically:
- Updates `server.json` version on new releases
- Publishes to MCP registry
- Commits updated configuration

**Triggers**:
- When version tags are pushed (`v*`)
- Manual workflow dispatch

## Testing Installation

Users can now discover and install Mac-letterhead:

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

Test by asking Claude or another MCP client:
*"List available MCP servers"* (should include mac-letterhead)

## Troubleshooting

### Authentication Issues
```bash
# Re-authenticate if token expired
mcp-publisher login github

# Check authentication status
mcp-publisher whoami
```

### Validation Errors
Common issues:
- **Version mismatch**: Ensure `server.json` version matches PyPI version
- **Invalid namespace**: Must be `io.github.easytocloud/mac-letterhead`
- **Missing fields**: Check against schema

### Publication Failures
```bash
# Check detailed error output
mcp-publisher publish --verbose

# Validate without publishing
mcp-publisher publish --dry-run
```

## Maintenance

### For New Releases

1. **Automatic** (via GitHub Actions):
   - Push version tag: `git push origin v0.14.0`
   - Workflow updates `server.json` and publishes

2. **Manual** (if needed):
   ```bash
   # Update version in server.json
   sed -i '' 's/"version": ".*"/"version": "0.14.0"/' server.json

   # Publish
   mcp-publisher publish

   # Commit
   git add server.json
   git commit -m "chore: update MCP registry version to 0.14.0"
   git push
   ```

### Monitoring

Check registry status:
- Official: https://registry.modelcontextprotocol.io/servers/io.github.easytocloud/mac-letterhead
- GitHub: Automatically synced
- Community: Check individual directories

## Quick Reference

| Action | Command |
|--------|---------|
| Install CLI | `brew install mcp-publisher` |
| Authenticate | `mcp-publisher login github` |
| Check auth | `mcp-publisher whoami` |
| Validate | `mcp-publisher publish --dry-run` |
| Publish | `mcp-publisher publish` |
| Manual trigger | GitHub Actions → publish-mcp-registry → Run workflow |

## Documentation

- **Full Guide**: [REGISTRY_PUBLISHING.md](REGISTRY_PUBLISHING.md)
- **MCP Setup**: [README_MCP.md](README_MCP.md)
- **Submission Template**: [.github/mcp-directory-submission.md](.github/mcp-directory-submission.md)
- **Official Docs**: https://github.com/modelcontextprotocol/registry

## Support

- **Registry Issues**: https://github.com/modelcontextprotocol/registry/issues
- **Mac-letterhead Issues**: https://github.com/easytocloud/Mac-letterhead/issues
- **MCP Discussions**: https://github.com/orgs/modelcontextprotocol/discussions

---

**Status**: Ready to publish ✅

**Next Steps**: Run steps 1-5 above to publish to the official MCP registry.
