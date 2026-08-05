# Mac-letterhead MCP Server

**Companion reference for the Model Context Protocol server that ships with Mac-letterhead.** For what Mac-letterhead is, general install steps, quick start, and CSS branding, see the [main README](README.md). This document covers MCP-specific setup — how to hook Mac-letterhead into Claude Desktop, Claude Code, Cursor, and other MCP clients; the generic-vs-dedicated server modes; and the exact tool schemas.

Published as `io.github.easytocloud/mac-letterhead` on the [official MCP Registry](https://registry.modelcontextprotocol.io) — mirrored to [Glama](https://glama.ai/mcp/servers/easytocloud/mac-letterhead) and [PulseMCP](https://www.pulsemcp.com/servers/easytocloud).

## Install

### Claude Desktop (recommended)

Download the latest `mac-letterhead-<version>.mcpb` from the [releases page](https://github.com/easytocloud/Mac-letterhead/releases) and double-click. Claude for macOS installs the server automatically and presents a settings UI:

| Setting | Description | Default |
|---------|-------------|---------|
| **Letterhead Style** | Style name — resolves `~/.letterhead/<style>.pdf` (and `.css`). Leave blank to specify style per tool call. | _(none)_ |
| **Output Directory** | Directory where generated PDFs are saved. | `~/Desktop` |

No terminal, no JSON editing.

### Other MCP clients (Cursor, Claude Code, Windsurf, Zed, …)

Add a server entry to your client's MCP configuration. The command uses `uvx`, which downloads Mac-letterhead on demand — no pre-install required.

If you'd rather have it installed permanently first, any of these works and the client config below stays the same:

```bash
brew install easytocloud/tap/mac-letterhead     # via Homebrew tap
uv tool install "Mac-letterhead[mcp]"           # via uv
```

## Two configuration modes

Mac-letterhead can run as a **generic multi-style** server or a **dedicated single-style** server. Choose based on how you want the AI client to invoke it.

### Generic (multi-style)

One server handles every brand. The style is passed per tool call. Best when you have several letterheads and want the AI to pick between them explicitly.

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

Then in Claude: *"Using the letterhead server, create a `company` style PDF about our Q3 results."*

Every tool call requires a `style` parameter.

### Dedicated (single-style)

Pre-bind a server to one brand. Best when you use the same letterhead repeatedly and want to skip specifying it each time.

```json
{
  "mcpServers": {
    "company-letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "company"]
    },
    "personal-letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "personal"]
    }
  }
}
```

Register multiple dedicated servers side by side — one per brand — and the AI picks the right one based on the phrasing of the request (*"Create a company letterheaded PDF…"* vs *"Create a personal letterhead PDF…"*).

Tools in dedicated mode don't accept `style` (it's already configured); they optionally accept `letterhead_template` as a one-off override.

## Server parameters (`mac-letterhead mcp`)

| Flag | Description | Default |
|------|-------------|---------|
| `--style <name>` | Bind the server to a specific style. Resolves `~/.letterhead/<name>.pdf` and `~/.letterhead/<name>.css`. Omit for generic mode. | _(none)_ |
| `--output-dir <path>` | Default output directory for generated PDFs. | `~/Desktop` |
| `--output-prefix <str>` | Default prefix for auto-generated filenames. | _(none)_ |

Example:
```bash
uvx mac-letterhead[mcp] mcp --style company --output-dir ~/Documents/company-docs --output-prefix "CompanyReport-"
```

## Tools

The server registers four tools. Parameter names vary between the two modes — in dedicated mode, `style` disappears from every schema and `letterhead_template` appears as an optional override.

### `create_letterhead_pdf` — Print Markdown onto Letterhead

Renders Markdown content into a letterheaded PDF.

| Mode | Required | Optional |
|------|----------|----------|
| Generic | `markdown_content`, `style` | `output_path`, `output_filename`, `title`, `css_path`, `strategy` |
| Dedicated | `markdown_content` | `letterhead_template`, `output_path`, `output_filename`, `title`, `css_path`, `strategy` |

Tool annotations: `read_only=false`, `destructive=false`, `open_world=false`, `idempotent=false` — creates a new file, leaves inputs untouched, fully local.

### `merge_letterhead_pdf` — Print PDF onto Letterhead

Applies a letterhead to an existing PDF file.

| Mode | Required | Optional |
|------|----------|----------|
| Generic | `input_pdf_path`, `style` | `output_path`, `output_filename`, `strategy` |
| Dedicated | `input_pdf_path` | `letterhead_template`, `output_path`, `output_filename`, `strategy` |

Tool annotations: same profile as `create_letterhead_pdf`.

### `analyze_letterhead` — Analyze Letterhead Template

Reports the safe printable area (margins, header/footer zones) of a letterhead template. Uses the three-tier resolution described in the [main README's *Preview and mark the safe area* section](README.md#preview-and-mark-the-safe-area): user-drawn Square annotations take priority over the layout heuristic. This means AI clients get exactly the same safe-area result regardless of interface — droplet, CLI, or MCP.

| Mode | Required | Optional |
|------|----------|----------|
| Generic | `style` | — |
| Dedicated | — | `letterhead_template` |

Tool annotations: `read_only=true`, `idempotent=true`, `open_world=false` — pure inspection, same input reliably yields the same analysis.

### `list_letterhead_templates` — List Letterhead Templates

Enumerates PDF files in `~/.letterhead/` with their optional CSS companions. No parameters.

Tool annotations: `read_only=true`, `idempotent=true`, `open_world=false`.

## Where letterheads live

The default location for brand-identity pairs is `~/.letterhead/<name>.pdf` + optional `~/.letterhead/<name>.css`. See the [Brand Styling with CSS](README.md#brand-your-typography-with-css) section of the main README for a full CSS example.

## Logging & troubleshooting

The server writes to `~/Library/Logs/Mac-letterhead/letterhead.log` (not stdout — stdout is reserved for JSON-RPC). Tail during a session:

```bash
tail -f ~/Library/Logs/Mac-letterhead/letterhead.log
```

Common issues:

- **Missing letterhead** — place your PDF at `~/.letterhead/<style>.pdf`, or point at a custom path via `letterhead_template` in the tool call.
- **Permission errors** — check the output directory is writable.
- **WeasyPrint warnings** — suppressed automatically in MCP mode. If rendering looks wrong, `brew install pango cairo fontconfig freetype harfbuzz` and restart the client.

## Related

- [Main README](README.md) — what Mac-letterhead is, install, quick start, CSS branding, blend strategies
- [PRIVACY.md](PRIVACY.md) — fully local; no network, no telemetry, no data collection
- [llms-install.md](llms-install.md) — LLM-catalog-scraper-consumed install guide
- [`docs/publishing.md`](docs/publishing.md) — how Mac-letterhead publishes to registries and taps
- [Registered MCP Registry entry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.easytocloud%2Fmac-letterhead/versions/latest) (JSON)
