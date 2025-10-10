import uvicorn
import sys
import threading
from pandoc_sidecar.app import app
from pandoc_sidecar.mcp_server import mcp


def run_fastapi():
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_mcp():
    """Run the MCP server"""
    mcp.run()


def main():
    # Check if running in MCP-only mode
    if "--mcp-only" in sys.argv:
        run_mcp()
    # Check if running in FastAPI-only mode
    elif "--api-only" in sys.argv:
        run_fastapi()
    # Default: run both servers
    else:
        # Start FastAPI in a separate thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()

        # Run MCP in the main thread
        run_mcp()


if __name__ == "__main__":
    main()
