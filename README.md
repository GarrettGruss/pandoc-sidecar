# Pandoc-Sidecar

This app exposes the pandoc/extra engine through both a RESTful API and an MCP (Model Context Protocol) server for use within a k8s cluster. A FastAPI server runs as a sidecar to expose the pandoc/extra functionality via HTTP, while the MCP server provides direct integration with AI assistants like Claude.

## Features

- **RESTful API**: FastAPI server for HTTP-based file conversion
- **MCP Server**: Model Context Protocol server for AI assistant integration
- **LaTeX to PDF**: Convert LaTeX content to PDF documents
- **File Upload**: Upload and convert multiple file formats to PDF
- **Docker Integration**: Uses docker-compose with pandoc/extra for reliable conversions

## API Endpoints

### FastAPI Server (Port 8000)

- `GET /health` - Health check endpoint
- `POST /upload` - Upload files and convert to PDF
- `POST /latex` - Convert LaTeX string to PDF

### MCP Server

- `latex://convert` - MCP resource for LaTeX to PDF conversion

## Installation

```bash
uv sync
```

## Running the Servers

By default, both servers run simultaneously:

```bash
uv run start
```

Run only the FastAPI server:

```bash
uv run start --api-only
```

Run only the MCP server:

```bash
uv run start --mcp-only
```

## Resources

- [multiple file uploads](https://fastapi.tiangolo.com/tutorial/request-files/#multiple-file-uploads)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## Structure

This app is composed of a FastAPI server, an MCP server, and a pandoc/extra image running in separate containers, but on the same deployment. They are mounted to the same file store and communicate via stdio.