
### this file is required if I have written the same code in fastAPI and tryin to convert that as MCP server then Server.py helps to convert it.
### fast API code is not written in this file folder---- You need to write the fastAPI code in main.py file and import mcp from main.py to server.py file to run MCP server.


from fastmcp import FastMCP
from main import app           # Importing mcp from main.py

mcp = FastMCP.from_fastapi(

    app= app,
    name = "Expense Tracker Server",
    description = "API server for Expense Tracker Application",
    version = "1.0.0"

)

if __name__ =="__main__":
    mcp.run()
