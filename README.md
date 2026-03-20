<h1 align="center">pip-skill</h1>
<p align="center"><strong>One command. Any pip package becomes an AI coding assistant skill.</strong></p>
<p align="center">Works with Claude Code, Cursor, Windsurf, and OpenCode - offline, no API keys needed.</p>

<p align="center">
  <a href="https://github.com/xmpuspus/pip-skill/stargazers"><img src="https://img.shields.io/github/stars/xmpuspus/pip-skill" alt="GitHub stars"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/status-pre--release-orange.svg" alt="Pre-release">
</p>

pip-skill introspects installed Python packages and generates Claude Code plugins — complete with skill instructions, API reference, and optional MCP server. No manual wrapping required.

```bash
pip install pip-skill
pip-skill convert requests
```

That's it. You get a ready-to-install Claude Code plugin:

```
requests/
├── .claude-plugin/plugin.json
└── skills/requests/
    ├── SKILL.md
    └── references/api-reference.md
```

## Why pip-skill?

Claude Code skills let Claude use Python libraries directly — but writing SKILL.md files by hand is tedious. You have to read the docs, pick the right functions, document parameters, and format everything correctly.

pip-skill automates the entire pipeline:

1. **Introspects** the installed package (signatures, types, docstrings)
2. **Selects** the most useful functions via a scoring algorithm
3. **Generates** JSON schemas, skill instructions, and API docs
4. **Outputs** a complete plugin directory you can install immediately

## Quick Start

### Install

```bash
pip install pip-skill
# or
uv add pip-skill
```

### Generate a plugin

```bash
# Basic: skill-only mode
pip-skill convert httpx

# With MCP server
pip-skill convert httpx --mcp

# Preview without writing files
pip-skill convert httpx --dry-run --verbose
```

### Install the plugin

```bash
# In Claude Code
/plugin install ./httpx
```

### Check version

```bash
pip-skill --version
```

<img src="demos/version.gif" alt="pip-skill --version" width="640">

### Explore a package

```bash
pip-skill info pandas
```

```
Package: pandas v2.2.0
Import name: pandas
Description: Powerful data structures for data analysis
Submodules: 42
Public functions: 156
Public classes: 38
Annotation coverage: 65%
Estimated tier: 2 (partial annotations)
```

## How It Works

pip-skill uses runtime introspection to analyze a package's API:

- **`inspect.signature()`** extracts function parameters and type annotations
- **`typing.get_type_hints()`** resolves forward references and `from __future__ import annotations`
- **`pkgutil.walk_packages()`** discovers all submodules
- **`docstring-parser`** extracts parameter descriptions from Google/NumPy/reST docstrings
- **`pydantic.TypeAdapter`** generates JSON Schema from type annotations

Each discovered function gets scored on 10 signals (module depth, docstring quality, annotation coverage, etc.) and the top candidates are selected for the plugin.

## Features

### Why pip-skill?

| | pip-skill | Write skills manually | Paste docs into context |
|---|---|---|---|
| Time per package | ~3 seconds | 1-2 hours | 10 minutes |
| Correct type hints | Yes (from runtime) | Maybe | No |
| JSON schemas | Auto-generated | Manual | No |
| Safety callouts | Auto-detected | Manual | No |
| Multi-format output | 4 formats | 1 format | N/A |
| Stays in sync | `pip-skill diff` | Manual tracking | Re-paste every update |
| Works offline | Yes | N/A | Needs docs URL |

### Skill-Only Mode (default)

Generates a SKILL.md that teaches Claude how to use the package via inline Python:

```
User invokes /requests → Claude reads SKILL.md →
Claude writes Python code → executes via Bash tool
```

### MCP Mode (`--mcp`)

Also generates a FastMCP server that exposes functions as structured tools:

```
Claude Code starts MCP server → tools available via MCP protocol →
Claude calls tools directly → structured JSON responses
```

### Multi-Format Output

Generate skills for any major AI coding assistant:

| Format | Flag | Output |
|--------|------|--------|
| Claude Code | `--format claude` (default) | `SKILL.md` + `plugin.json` + `CONTEXT.md` + `api-reference.md` |
| Cursor | `--format cursor` | `.cursorrules` |
| Windsurf | `--format windsurf` | `.windsurfrules` |
| OpenCode | `--format opencode` | `AGENTS.md` |

<img src="demos/format.gif" alt="pip-skill multi-format output" width="640">

### Batch Mode

Convert multiple packages at once with parallel processing:

```bash
pip-skill batch requirements.txt --format claude --workers 4
```

<img src="demos/batch.gif" alt="pip-skill batch conversion" width="640">

### Version Tracking

Detect API changes when packages update:

```bash
pip-skill diff requests
```

<img src="demos/diff.gif" alt="pip-skill diff output" width="640">

### Smart Function Selection

- 10-signal scoring algorithm (0-100 per function)
- Prioritizes top-level, well-documented, well-typed functions
- Deduplicates near-identical variants

### Package Tier Detection

Automatically classifies packages and adjusts strategy:

| Tier | Criteria | Example |
|------|----------|---------|
| 1 | >70% annotated, stateless | httpx, pydantic |
| 2 | <70% annotated, stateless | requests, click |
| 3 | Stateful/dynamic | boto3, sqlalchemy |

## CLI Reference

### `pip-skill convert <package>`

Generate a Claude Code plugin from an installed package.

```
Options:
  --mcp                Generate MCP server alongside SKILL.md
  --output DIR         Output directory (default: ./{package-name})
  --max-tools N        Maximum functions to include (default: 20)
  --include PATTERN    Include functions matching glob pattern
  --exclude PATTERN    Exclude functions matching glob pattern
  --dry-run            Preview without writing files
  --verbose            Show scoring breakdown
  --force              Overwrite existing output
```

### `pip-skill info <package>`

Show package metadata and API surface summary.

### `pip-skill validate <plugin-dir>`

Validate a generated plugin directory for correctness.

## Supported Packages

pip-skill works with any installed Python package. It handles:

- Fully annotated APIs (Tier 1): httpx, pydantic, fastapi
- Partially annotated APIs (Tier 2): requests, click, flask
- Stateful/dynamic APIs (Tier 3): boto3, sqlalchemy, stripe
- C extensions: numpy, pandas (limited signature info)
- Pydantic models: auto-detected, fields extracted from `model_fields`
- Dataclasses: auto-detected, fields extracted from `dataclasses.fields()`
- Lazy imports: detected via `__getattr__`, logged as warning

## Real-World Examples

These are real packages, one command each, that give Claude capabilities it simply doesn't have by default.

---

### 1. `Pillow` — Image editing without Photoshop

```bash
pip install Pillow && pip-skill convert Pillow
```

Claude can now resize, crop, rotate, watermark, convert formats, apply filters, and composite images — all from a single prompt.

```
"Resize all JPEGs in this folder to 1200px wide, convert to WebP, and add a 'CONFIDENTIAL' watermark"
```

---

### 2. `openpyxl` — Read and write real Excel files

```bash
pip install openpyxl && pip-skill convert openpyxl
```

Not CSV export — actual `.xlsx` with formulas, merged cells, charts, conditional formatting, and named ranges.

```
"Take this sales data and build an Excel report with a pivot-style summary sheet,
 SUM formulas in the totals row, and alternating row colors"
```

---

### 3. `boto3` — Full AWS control

```bash
pip install boto3 && pip-skill convert boto3
```

S3 uploads, Lambda invocations, EC2 management, CloudWatch logs, SQS queues, DynamoDB queries — with correct types and schemas generated from the installed API.

```
"List all S3 buckets with their sizes, find objects older than 90 days in the archive bucket,
 and move them to Glacier storage class"
```

---

### 4. `pytesseract` — Extract text from images

```bash
pip install pytesseract && pip-skill convert pytesseract
```

OCR on screenshots, scanned documents, photos of whiteboards, receipts, business cards. Claude can finally read images as text.

```
"Extract all the line items and totals from these receipt photos and put them in a spreadsheet"
```

---

### 5. `paramiko` — SSH and SFTP without leaving Claude

```bash
pip install paramiko && pip-skill convert paramiko
```

Connect to remote servers, run commands, transfer files, manage known_hosts. Claude becomes a remote ops assistant.

```
"SSH into each server in this list, check disk usage, and alert me to any partition above 80%"
```

---

### 6. `pdfplumber` — Extract structured data from PDFs

```bash
pip install pdfplumber && pip-skill convert pdfplumber
```

Not just text — tables, bounding boxes, character-level positions. The difference between useless blobs and actual structured data from PDFs.

```
"Pull the invoice table from each PDF in this folder, parse the line items,
 and consolidate into one spreadsheet with the source filename as a column"
```

---

### 7. `stripe` — Payment operations via chat

```bash
pip install stripe && pip-skill convert stripe
```

Create customers, list subscriptions, issue refunds, generate invoices, manage products and prices — the whole Stripe API from a conversation.

```
"Find all subscriptions that have been paused for more than 30 days,
 send each customer a reactivation coupon for 20% off, and log the results"
```

---

### 8. `cryptography` — Real encryption, not base64

```bash
pip install cryptography && pip-skill convert cryptography
```

Fernet symmetric encryption, RSA key generation, X.509 certificate parsing, HMAC signing, password hashing with proper key derivation.

```
"Encrypt all .env files in this repo with a passphrase, write the encrypted versions
 to .env.enc, and delete the originals"
```

---

### 9. `pydub` — Audio processing

```bash
pip install pydub && pip-skill convert pydub
```

Slice audio, adjust volume, convert formats, overlay tracks, strip silence, normalize levels. Works on anything ffmpeg can read.

```
"Split this podcast recording on silence longer than 2 seconds,
 normalize each segment to -14 LUFS, and export as individual MP3s"
```

---

### 10. `twilio` — Send SMS and WhatsApp

```bash
pip install twilio && pip-skill convert twilio
```

Outbound SMS, WhatsApp messages, voice calls, phone number lookup, messaging services. No API documentation required.

```
"Text everyone on this list that their appointment is confirmed tomorrow at 10am,
 and log any failed deliveries"
```

---

### 11. `reportlab` — Generate PDFs from scratch

```bash
pip install reportlab && pip-skill convert reportlab
```

Programmatic PDF creation with tables, charts, headers, footers, embedded images, and custom fonts. Contracts, invoices, reports — fully generated.

```
"Take this JSON invoice data and produce a professional PDF with our logo,
 itemized table, tax calculations, and payment terms footer"
```

---

### 12. `pyarrow` — Work with massive datasets

```bash
pip install pyarrow && pip-skill convert pyarrow
```

Read Parquet files, convert between Arrow/Pandas/CSV, query columnar data, handle datasets too large for pandas to load at once.

```
"Read this 4GB Parquet file, filter rows where revenue > 10000 and region = 'APAC',
 export to CSV, show me the top 20 rows"
```

---

## FAQ

**Why not just paste the docs into context?**
Token limits. The boto3 docs are 50MB+. pip-skill selects the top 20 functions by usefulness score and fits everything in ~4,000 tokens with correct types and schemas.

**Why not rely on the LLM's built-in knowledge?**
It works for popular packages like `requests`. It fails for anything updated after training data cutoff, niche packages, or complex signatures. pip-skill reads the actual installed API at runtime - no hallucination possible.

**Why not just use MCP servers?**
pip-skill generates those too (`--mcp`). But skill-only mode is lighter - no server process, no port, no config. The AI reads the SKILL.md and writes correct Python directly.

**What about packages with C extensions?**
Works with numpy, pandas, etc. Signature info is limited for C-level functions, but pip-skill falls back to docstring parsing and marks the skill as Tier 3 so the AI knows to be cautious.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE).

---

<p align="center">Built by <a href="https://github.com/xmpuspus">Xavier Puspus</a></p>
