# This file creates an MCP Server and exposes three Tools through it.
# An MCP Server is a program that makes several functions (Tools) available
# to an AI model (or any other client) over the MCP protocol.

# FastMCP is the main class from the official Python MCP SDK.
from mcp.server.fastmcp import FastMCP

# Import the three Tools we previously defined from the `tools` package.
from tools.stock_info import get_stock_info
from tools.gold_price import get_gold_price
from tools.usd_rate import get_usd_rate

# Step 1: Create an MCP server with an arbitrary name.
mcp = FastMCP("finance-server")

# Step 2: Register each function as a Tool on the server.
# FastMCP automatically builds the Function Calling schema from each
# function's type hints and docstring — no need to write schemas manually.
mcp.add_tool(get_stock_info)
mcp.add_tool(get_gold_price)
mcp.add_tool(get_usd_rate)

# Step 3: Run the server.
# By default, this server uses the "Stdio Transport", meaning it talks to
# the client over standard input/output (stdin/stdout). This is exactly what
# happens when a client launches this file with command="python",
# args=["server.py"].
if __name__ == "__main__":
    mcp.run()