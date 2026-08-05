# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mac-letterhead is a macOS utility that merges letterhead templates with PDF and Markdown documents using a drag-and-drop interface. It creates AppleScript droplet applications that users can drop documents onto to automatically apply letterhead templates.

## Development Commands

### Build and Test Commands

**Development Setup:**
```bash
make dev-install        # Install package for local development using uv
make dev-droplet        # Create development droplet using local code
```

**Desktop Extension (DXT/MCPB):**
```bash
make build-dxt          # Build the Desktop Extension (.mcpb) for Claude for macOS
                        # Output: dxt/mac-letterhead-<version>.mcpb
                        # Requires: Node.js (npx @anthropic-ai/mcpb pack)
```

**Unit Tests (pytest-based software testing):**
```bash
make test-unit          # Run unit tests with default Python version
make test-unit-py3.11   # Run unit tests with specific Python version
make test-all-unit      # Run unit tests across all Python versions (3.10, 3.11, 3.12)
```

**Rendering Tests (document generation validation):**
```bash
make rendering-reportlab-basic      # Basic ReportLab rendering (minimal deps)
make rendering-reportlab-enhanced   # Enhanced ReportLab with full markdown features
make rendering-weasyprint           # High-quality WeasyPrint rendering (requires system deps)
make rendering-backend-matrix       # Test all backend/markdown combinations
make rendering-all-python-versions  # Test across all Python versions
make test-all-rendering             # Run all rendering tests
```

**Quick Tests:**
```bash
make test-dev           # Quick development validation (unit tests only)
make test-smoke         # Fast smoke test with single input file
```

**Comprehensive Testing:**
```bash
make test-all           # Run ALL tests (unit + smoke + rendering)
```

**Cleaning:**
```bash
make clean-all          # Clean everything (build artifacts, test files, droplets)
make clean-build        # Remove build artifacts and virtual environments only  
make clean-droplets     # Remove test droplets only
make clean-test-output  # Remove test output files (PDFs, HTMLs)
```

**Release (semantic-release via CI):**
```bash
make release-dry-run    # Preview next version without publishing
make publish            # Run tests then invoke semantic-release locally
```
PyPI uploads happen via GitHub Actions using PyPI Trusted Publishing (OIDC) — no `TWINE_PASSWORD` is used in CI. `make publish` above just runs semantic-release; the workflow (`publish.yml`) handles the actual PyPI upload.

### System Dependencies
For WeasyPrint functionality (high-quality Markdown to PDF conversion):
```bash
brew install pango cairo fontconfig freetype harfbuzz
```

### Running the Application
```bash
# Install and use
uvx mac-letterhead install --name "Company"

# Direct merge operations
uvx mac-letterhead merge letterhead.pdf "Output" ~/Desktop document.pdf
uvx mac-letterhead merge-md letterhead.pdf "Output" ~/Desktop document.md

# Visualize the safe area (cut marks + source-coded tint) — writes <name>-preview.pdf
uvx mac-letterhead preview ~/.letterhead/company.pdf
uvx mac-letterhead preview company              # style-name form (resolves ~/.letterhead/company.pdf)

# MCP server for AI integration
uvx mac-letterhead mcp --style easytocloud        # Style-specific server
uvx mac-letterhead mcp                             # Generic server, style specified per tool call
uvx mac-letterhead mcp --style personal --output-dir ~/Documents/personal-docs
```

### Install Command Behavior

The `install` command creates droplet applications using a name-based convention:

- `--name` is mandatory and sets both the app name and style
- Automatically resolves `~/.letterhead/<name>.pdf` and `~/.letterhead/<name>.css`
- `--letterhead` and `--css` flags can override the resolved paths
- Applications are created on Desktop by default

**Examples:**
```bash
# Uses ~/.letterhead/company.pdf and ~/.letterhead/company.css
uvx mac-letterhead install --name "company"

# Override letterhead but keep name-based CSS
uvx mac-letterhead install --name "report" --letterhead /path/to/custom.pdf

# Development droplet using local code
uvx mac-letterhead install --name "test" --dev
```

### Test File Processing

**Input Files:**
- Place `.md` test files in `test-input/` directory
- All files are automatically discovered and processed
- Hidden files (starting with `.`) are ignored during rendering tests

**Output Organization:**
- Generated files appear in `test-output/` organized by input filename  
- Format: `test-output/{filename}/{filename}-py{version}-{config}.{pdf,html}`
- Example: `test-output/gfm-features-test/gfm-features-test-py3.11-reportlab-enhanced.pdf`

**Workflow Examples:**
```bash
# Development workflow
make dev-droplet → test → make clean-droplets

# Testing workflow  
make test-dev → make test-smoke → make test-all

# Release workflow
make test-all → make publish
```

## Architecture Overview

### Core Components

**Main Application (`letterhead_pdf/main.py`)**
- CLI interface with argparse
- Command handlers: `install`, `merge`, `merge-md`, `mcp`
- MCP server integration for AI tool usage
- macOS save dialog integration using AppKit/Foundation
- Logging configuration and error handling

**PDF Processing Pipeline**
- `PDFMerger` (pdf_merger.py): Core PDF merging with multiple blend strategies
- `MarkdownProcessor` (markdown/processor.py): Markdown to PDF conversion with smart margin detection
- `pdf_utils.py`: Low-level PDF operations using Quartz/CoreGraphics

**Markdown Pipeline (`letterhead_pdf/markdown/`)**
- `processor.py`: `MarkdownProcessor` orchestrator — capability flags, backend selection, WeasyPrint→ReportLab fallback
- `pdf_analyzer.py`: safe-area detection. `analyze_letterhead` (legacy, returns margins only), `analyze_letterhead_detailed` (returns `{source, rect, margins}`), `analyze_page_safe_area` (per-page), `find_safe_area_annotation` (annotation lookup), `SafeAreaSource` enum, `SAFE_AREA_LABELS`.
- `preview.py`: `render_safe_area_preview(letterhead, output)` — visualization overlay (cut marks + tint + source label), colour-coded by source. Used by the `preview` CLI command and the droplet's "Preview Safe Area" double-click action.
- `front_matter.py`: YAML front-matter parser + precedence-aware resolver. `parse(md) -> (fm_dict, body)`, `resolve(fm, explicit=..., server_bound_style=...) -> ResolvedConfig`, `page_numbers_css(position) -> str`. Precedence rule: `explicit > front matter > (nothing at this layer)`. Special case: on style-bound MCP servers, front-matter `style:` is ignored — server binding wins. Supported fields listed in the module docstring and mirrored in the README.
- `html_cleaner.py`: `clean_html_for_reportlab`, `preprocess_markdown_indentation`, list item processing
- `flowable_builder.py`: `build_styles`, `markdown_to_flowables`, nested list parsing
- `backends/weasyprint_backend.py`: WeasyPrint renderer with CSS path validation
- `backends/reportlab_backend.py`: ReportLab renderer
- `letterhead_pdf/markdown_processor.py`: backwards-compatibility shim (imports from `markdown/`)

**Droplet Creation System (`letterhead_pdf/installation/`)**
- `DropletBuilder`: Main orchestrator for droplet creation
- `AppleScriptGenerator`: Creates AppleScript code for droplets
- `ResourceManager`: Handles icon and resource embedding
- `MacOSIntegration`: macOS-specific integration (app bundle creation)
- `DropletValidator`: Validates created droplets

**MCP Server Integration (`letterhead_pdf/mcp_server.py`)**
- Model Context Protocol server for AI tool integration
- Dynamic tool schema adaptation based on server configuration
- Convention-based file resolution from `~/.letterhead/` directory
- Support for both generic multi-style and dedicated single-style servers
- Tools: `create_letterhead_pdf`, `merge_letterhead_pdf`, `analyze_letterhead`, `list_letterhead_templates`

### Key Features

**Safe-Area Detection (three-tier)**
- **Annotation (highest priority)**: users mark a Square annotation on the letterhead PDF. Two sub-rules:
  - *Labeled* — annotation whose title/contents/subject contains one of `SAFE_AREA_LABELS` (`safe-area`, `printable-area`, `content-area`, and variants; case-insensitive, substring). Any number of Squares can coexist; the labeled one wins.
  - *Single unlabeled* — if the page has *exactly one* Square annotation and none matched a label, that Square is used anyway. This accommodates macOS Preview.app, which draws Squares but doesn't expose an editable label field. Multiple unlabeled Squares are ambiguous and fall through to the heuristic with a warning.
  Treated verbatim — no padding applied. Escape hatch for pixel-precise control when the heuristic misjudges.
- **Heuristic**: layout analysis via PyMuPDF — text blocks, drawings, and images classified into header/middle/footer bands (top/bottom third of the page), then the safe rectangle is nudged to avoid detected content. `HEURISTIC_TOP_BOTTOM_PADDING = 40` pt is added on top and bottom for breathing room; without it, continuation-page wordmarks rendered as tiny vector paths can end up right against the safe-area edge.
- **Fallback**: if the heuristic finds no content at all (blank letterhead), returns generous 1-inch defaults on every side.
- Same resolution used by every interface — droplet, CLI, MCP — via `analyze_page_safe_area()` and `analyze_letterhead_detailed()`. Backwards-compatible `analyze_letterhead()` still returns margin dicts only.

**Multi-Page Letterhead Support**
- Single page: Applied to all document pages
- Two pages: First page → first document page, second page → other pages
- Three pages: First page → first page, second page → even pages, third page → odd pages

**Dual Rendering Pipeline**
- WeasyPrint: High-quality rendering with full CSS support (preferred)
- ReportLab: Fallback rendering for when WeasyPrint unavailable

**PDF Merge Strategies**
- `darken` (default): Content first, letterhead with multiply blend
- `multiply`: Original multiply blend strategy
- `overlay`: Overlay blend mode for better visibility
- `transparency`: Uses transparency layers
- `reverse`: Letterhead on top with transparency

**MCP Server Capabilities**
- **Dual Configuration Modes**: Generic multi-style server or dedicated single-style servers
- **Dynamic Tool Schemas**: Tools adapt parameter requirements based on server configuration
- **Convention-Based Resolution**: Auto-resolves `~/.letterhead/<style>.pdf` and `~/.letterhead/<style>.css`
- **AI Integration**: Enables natural language PDF generation through Claude and other AI tools
- **Flexible Output Control**: Configurable output directories and filename prefixes

### Dependencies and Compatibility

**Core Dependencies**
- PyObjC frameworks (Cocoa, Quartz) for macOS integration
- PyMuPDF for PDF analysis and margin detection
- ReportLab for fallback PDF generation
- WeasyPrint for high-quality Markdown rendering (optional)

**Optional Dependencies**
- Markdown + Pygments for syntax highlighting
- HTML5lib for HTML parsing
- MCP (Model Context Protocol) for AI tool integration

**Python Support**
- Requires Python ≥3.10
- Currently tested with Python 3.10, 3.11, 3.12

### File Structure Patterns

**Package Structure**
- Main entry point: `letterhead_pdf/main.py`
- Core logic: `pdf_merger.py`, `pdf_utils.py`
- Markdown pipeline: `letterhead_pdf/markdown/` (processor, pdf_analyzer, html_cleaner, flowable_builder, backends)
- Backwards-compat shim: `letterhead_pdf/markdown_processor.py` → re-exports from `letterhead_pdf/markdown/`
- MCP server: `letterhead_pdf/mcp_server.py` (AI tool integration)
- Installation system: `letterhead_pdf/installation/` (modular components)
- Resources: `letterhead_pdf/resources/` (defaults.css, icons)
- Tests: `tests/` with unit tests (`test_security.py`, `test_gfm_features.py`, `test_list_rendering.py`) and fixtures
- Documentation: `README_MCP.md`, `sample_mcp_config.json`, `setup_letterheads.sh`

**Configuration**
- Version management: `letterhead_pdf/__init__.py` is the canonical version, and semantic-release mirrors it into `dxt/manifest.json`, `server.json`, and `uv.lock` on every release (see `.releaserc.json` `@semantic-release/git` `assets`). Never hand-edit any one of those without keeping the rest in lockstep — the mirrors will drift and CI will start attaching the wrong `.mcpb` filename to releases.
- Build system: `pyproject.toml` with Hatch backend
- Make targets: Comprehensive Makefile for all operations

### Development Workflow

**Testing Strategy**
- Unit tests via `uv run --with pytest pytest tests/ -v` — covers security, GFM features, list rendering
- Test droplets created on Desktop for manual testing
- Automated rendering tests for multiple Python versions and backend combinations
- Separate test environments for basic/full/WeasyPrint functionality

**Release Process**
1. Commit with Conventional Commit messages to `main`. Under this repo's Angular preset (`.releaserc.json`, default `commit-analyzer` rules), **only these types cut a release**:
   - `fix:` → patch bump (0.18.9 → 0.18.10)
   - `feat:` → minor bump (0.18.9 → 0.19.0)
   - `BREAKING CHANGE:` in body → major bump (0.18.9 → 1.0.0)
   - `perf:` → patch bump

   `chore:`, `docs:`, `style:`, `refactor:`, `test:`, `ci:`, `build:` all land on `main` without publishing. This is easy to forget — a `chore(deps): bump X` commit will *not* trigger 0.18.10.
2. GitHub Actions runs semantic-release (`publish.yml`): bumps version files, updates CHANGELOG, cuts a GitHub release, uploads to PyPI via Trusted Publishing (OIDC), builds the DXT `.mcpb`, and attaches it to the release.
3. On successful completion, `publish-mcp-registry.yml` fires via `workflow_run` and publishes `server.json` to the MCP Registry using `mcp-publisher login github-oidc` (no PAT). See "MCP Registry Pipeline" below.
4. Local preview: `make release-dry-run`. Do not run `make publish` from a workstation for real releases — the workflow handles it end-to-end.

**MCP Registry Pipeline**
- Triggered by: `publish.yml` completing successfully → `publish-mcp-registry.yml` fires on `workflow_run`.
- Auth: `mcp-publisher login github-oidc`. The workflow needs `permissions: id-token: write`. No `MCP_PUBLISHER_TOKEN` secret is used — an earlier PAT-based flow depended on the publisher's org membership being public, which is fragile; OIDC binds the token to the repo owner (`easytocloud`) directly.
- Namespace: `io.github.easytocloud/mac-letterhead`, defined by `server.json` `name`.
- Constraints on `server.json` that will 422 the publish if violated:
  - `description` must be **≤ 100 characters** (registry-enforced, not schema-visible).
  - `packageArguments[].type` is required — `"positional"` for our `mcp` arg.
  - `_meta` keys other than `io.modelcontextprotocol.registry/publisher-provided` are silently dropped.
  - Schema URL: `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` (2025-09-29 also still accepted but older).

### macOS Integration Details

**AppleScript Droplets**
- Created as full .app bundles with embedded Python code
- Support both development mode (local code) and production mode (installed package)
- Include letterhead preview functionality
- Handle file permissions and sandbox restrictions

**System Integration**
- Uses Quartz/CoreGraphics for PDF operations (native macOS PDF handling)
- AppKit for save dialogs and UI interactions
- Foundation for file operations and system integration

## MCP Server Integration

Each letterhead is a brand-identity pair: `~/.letterhead/<name>.pdf` (the stationery artwork) plus optional `~/.letterhead/<name>.css` (the typography — fonts, colors, spacing). Together they turn any Markdown file into a fully branded PDF.

Two configuration modes:
- **Generic multi-style server** (`uvx mac-letterhead[mcp] mcp`) — one server, `style` is required per tool call.
- **Style-specific server** (`uvx mac-letterhead[mcp] mcp --style <name>`) — pre-bound to a style; `style` parameter is not accepted by the tools.

Server tools adapt their schemas to the mode (generic requires `style`, style-specific omits it). Set up sample letterheads with `./setup_letterheads.sh`.

See [README_MCP.md](README_MCP.md) for full configuration examples, and [llms-install.md](llms-install.md) for the LLM-facing install guide. Tools and their responsibilities are already listed above under "Core Components → MCP Server Integration".