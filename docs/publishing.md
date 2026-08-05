# Publishing Mac-letterhead

Mac-letterhead is published on the **official MCP Registry** as `io.github.easytocloud/mac-letterhead`, and shows up on a handful of third-party MCP catalogs. This document covers where those listings live, how the release pipeline gets Mac-letterhead onto them, and how to publish by hand if the pipeline breaks.

For the internal mechanics of the pipeline (workflow file layout, commit-type → release-trigger mapping, `server.json` constraints), see [CLAUDE.md](../CLAUDE.md#release-process).

## Where Mac-letterhead is listed

### Official — updated automatically on every release

| Registry | URL | How we appear there |
|---|---|---|
| **Official MCP Registry** | https://registry.modelcontextprotocol.io/servers/io.github.easytocloud/mac-letterhead | Automated: `publish-mcp-registry.yml` fires on every `publish.yml` success and calls `mcp-publisher publish`. |
| **PyPI** | https://pypi.org/project/Mac-letterhead/ | Automated: `publish.yml` uses PyPI Trusted Publishing (OIDC). |
| **GitHub Releases** | https://github.com/easytocloud/Mac-letterhead/releases | Automated: `publish.yml` (via semantic-release) cuts the release and attaches the `.mcpb` bundle. |

### Third-party — auto-scraped, no submission needed

These catalogs pull from the Official MCP Registry, GitHub, or PyPI on their own schedule. We do not push to them — new versions surface within hours to days.

| Catalog | URL |
|---|---|
| PulseMCP | https://www.pulsemcp.com/servers/easytocloud |
| Glama | https://glama.ai/mcp/servers/easytocloud/mac-letterhead |
| GitHub MCP Registry mirror | (syncs from official registry) |

### Third-party — one-off submissions

These are hand-curated and don't auto-scrape. Submit once; entries are then stable across version bumps (they carry no version pin — see [community-projects notes](https://github.com/modelcontextprotocol/registry/blob/main/docs/community-projects.md)).

| Catalog | URL | How to submit |
|---|---|---|
| awesome-mcp-servers | https://github.com/punkpeye/awesome-mcp-servers | PR to `README.md` under the appropriate category. Mac-letterhead sits under **Workplace & Productivity**. |
| mcp.so | https://mcp.so | Web submission form, or GitHub issue at [chatmcp/mcp-directory](https://github.com/chatmcp/mcp-directory/issues). See [`.github/mcp-directory-submission.md`](../.github/mcp-directory-submission.md) for a fillable template. |
| Cline MCP Marketplace | https://github.com/cline/mcp-marketplace | Fork + PR adding a server entry. |
| MCP Index | https://mcpindex.net | Submission system if/when available. |

Smithery was investigated and skipped: its "hosted" mode requires a Linux Docker container, and Mac-letterhead is macOS-native (PyObjC + Quartz + AppKit). A local-stdio bundle route exists, but the payoff is small — Smithery users mostly want cloud-hosted servers, and PulseMCP + Glama already carry the listing.

## The release pipeline (summary)

Push a `fix:`/`feat:`/`perf:` commit — or one with `BREAKING CHANGE:` in the body — to `main`. `chore:`, `docs:`, `ci:`, `refactor:`, `test:`, `style:`, `build:` do **not** cut a release.

What happens on a release-triggering commit:

```
push main
   ↓
publish.yml (Semantic Release)
   ├─ Bumps version in letterhead_pdf/__init__.py, dxt/manifest.json,
   │  server.json, uv.lock
   ├─ Regenerates CHANGELOG.md, cuts a git tag + GitHub release
   ├─ Uploads to PyPI via Trusted Publishing (OIDC, with 3-attempt retry
   │  for transient Sigstore/TUF flakes)
   └─ Builds dxt/mac-letterhead-<version>.mcpb, attaches to GH release
        ↓
   [workflow_run: completed → success]
        ↓
publish-mcp-registry.yml
   ├─ Downloads the .mcpb from the release
   ├─ mcp-publisher login github-oidc  (no PAT, no MCP_PUBLISHER_TOKEN)
   └─ mcp-publisher publish  →  registry.modelcontextprotocol.io
        ↓
PulseMCP / Glama pick up the change on their own schedules
```

Full mechanics — including the `server.json` constraints that will 422 a publish (100-char description limit, required `packageArguments[].type`, `_meta` key restriction) — are documented in [CLAUDE.md](../CLAUDE.md#mcp-registry-pipeline).

## Manual publishing (fallback)

You should not need this. The automated pipeline handles every release. It's here in case:

- Sigstore/TUF is down and the retry fallback in `publish.yml` also fails
- OIDC auth breaks (e.g. the registry changes something on their side)
- A one-off backfill is needed for a version whose auto-publish died mid-flight

### 1. Install `mcp-publisher`

```bash
brew install mcp-publisher
# — or — download the binary for your platform from
# https://github.com/modelcontextprotocol/registry/releases
```

### 2. Authenticate

```bash
# Interactive: opens a browser, uses GitHub OAuth device-code flow.
# For manual publishing this is the simplest path.
mcp-publisher login github
```

This grants the `io.github.<yourname>/*` namespace, so it only works if you're publishing under your own GitHub account. To publish under `io.github.easytocloud/*` you need your `easytocloud` org membership set to **public** in GitHub. If it's private, the registry cannot verify the namespace and will 403. Alternatively use `mcp-publisher login github-oidc` from a GitHub Actions runner in the target repository (this is what CI does).

### 3. Publish

```bash
# From the repo root, with server.json valid at the current version:
mcp-publisher publish
```

The tool reads `server.json` from the working directory. If PyPI doesn't yet have the version referenced in `server.json`, the registry returns 400 — publish to PyPI first (`uv build && twine upload dist/*`), then rerun `mcp-publisher publish`.

### 4. Verify

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=mac-letterhead&limit=100" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print([s['server']['version'] for s in d['servers'] if s['_meta']['io.modelcontextprotocol.registry/official'].get('isLatest')])"
```

Should return `['<the version you just published>']`.

## Related documentation

- [CLAUDE.md](../CLAUDE.md) — operator guide, including the release-trigger rules and MCP registry pipeline details
- [README_MCP.md](../README_MCP.md) — user-facing MCP configuration guide
- [llms-install.md](../llms-install.md) — LLM-scraper-consumed install guide
- [`.github/mcp-directory-submission.md`](../.github/mcp-directory-submission.md) — reusable template for one-off directory submissions
- [Official MCP Registry docs](https://github.com/modelcontextprotocol/registry) — upstream reference
