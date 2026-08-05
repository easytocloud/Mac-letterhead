# Privacy Policy

_Last updated: 2026-08-05_

## Summary

**Mac-letterhead runs entirely on your local machine. It does not collect, transmit, store, or share any personal data.**

This document exists to make that explicit, so you know what to expect before installing.

## What Mac-letterhead does with your data

Mac-letterhead reads two kinds of files on your machine:

1. **Your letterhead templates** — PDF (and optional CSS) files you have placed in `~/.letterhead/`, or that you point it at directly via the `--letterhead` / `--css` flags.
2. **The documents you ask it to process** — the Markdown files, existing PDFs, or content passed to it via MCP tool calls.

It reads these, produces a letterheaded PDF, and writes the result to a location you choose (the macOS save dialog, a `--output-dir` you configured, or a path an MCP client passed in). That is the entire data path.

## What Mac-letterhead does NOT do

- **No network calls.** Mac-letterhead makes no HTTP or HTTPS requests during normal operation. It does not phone home, does not check for updates, does not send telemetry, does not report crashes to any remote service.
- **No analytics or telemetry.** No usage tracking, no error reporting to third parties, no analytics libraries embedded.
- **No cloud storage or sync.** Everything happens on-disk on your Mac. Your letterheads never leave your machine unless you send them somewhere yourself.
- **No third-party sharing.** There is no third party to share with — see above.
- **No account, no login, no identifier.** Mac-letterhead has no user accounts and generates no identifiers.

## Logs

Mac-letterhead writes a local log file at `~/Library/Logs/Mac-letterhead/letterhead.log` (when installed as a droplet) for diagnostic purposes. The log stays on your machine. It contains file paths and processing steps, not the document contents themselves. You can delete this file at any time.

## The MCP server mode

When Mac-letterhead is invoked as an MCP server (via `uvx mac-letterhead[mcp] mcp`, the Desktop Extension, or a client's MCP config), the AI client (Claude Desktop, Cursor, etc.) is the party that passes content to it. Any privacy considerations about *how the client uses your data* are governed by the client's own privacy policy, not this one. Mac-letterhead itself sees only what the client passes it in a tool call, processes it locally, and returns the resulting file path — nothing more.

## Data controllers and processors

Mac-letterhead is free open-source software distributed under the MIT license. There is no operator, no service provider, no data controller — it's a program you run on your own machine.

## Changes

If future versions of Mac-letterhead ever start making network calls or collecting data (e.g. an opt-in update-check), this document will be updated first, in the same commit that introduces the behavior. Watch this file, or the [CHANGELOG](CHANGELOG.md), for changes.

## Contact

Questions or concerns: open an issue at [github.com/easytocloud/Mac-letterhead/issues](https://github.com/easytocloud/Mac-letterhead/issues).
