from fastmcp import FastMCP
import subprocess

# FastMCP 2.x expects only name and instructions as positional args;
# version must be provided as a keyword-only argument.
mcp = FastMCP(
    "digitalocean-mcp",
    "MCP Server over HTTP",
    version="0.1.0",
)

@mcp.tool
def hello(name: str = "there") -> str:
    return f"Hello {name}! I'm running on your DigitalOcean server."

@mcp.tool
def add(a: float, b: float) -> float:
    return a + b

@mcp.tool
def uptime() -> str:
    return subprocess.check_output(["uptime"], text=True)

if __name__ == "__main__":
    # Expose via HTTP transport instead of stdio
    # FastMCP.run accepts a transport; "http" will run an HTTP server
    # and use host/port provided below.
    mcp.run("http", host="0.0.0.0", port=8000)
