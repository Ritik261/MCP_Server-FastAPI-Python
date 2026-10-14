
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from supabase import create_client, Client

load_dotenv()

# Connect to Supabase
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

# Initialize MCP server
mcp = FastMCP("Supabase Data Server")

# Allow only approved tables
ALLOWED_TABLES = {"customers", "chat_sessions"}

@mcp.tool()
def get_data(table_name: str, limit: int = 10) -> dict:
    """
    Retrieve records from an approved Supabase table.

    Args:
        table_name: Name of the table, for example products.
        limit: Maximum number of records to return.
    """
    if table_name not in ALLOWED_TABLES:
        return {
            "success": False,
            "error": "Table is not allowed."
        }

    if not 1 <= limit <= 100:
        return {
            "success": False,
            "error": "Limit must be between 1 and 100."
        }

    try:
        response = (
            supabase.table(table_name)
            .select("*")
            .limit(limit)
            .execute()
        )

        return {
            "success": True,
            "table": table_name,
            "count": len(response.data),
            "data": response.data,
        }

    except Exception:
        return {
            "success": False,
            "error": "Failed to retrieve data from Supabase."
        }


# Integrate MCP into FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Supabase MCP Server",
    lifespan=lifespan,
)

# MCP endpoint: /mcp  (the sub-app registers /mcp internally, so mount at root)
app.mount("/", mcp.streamable_http_app())


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Supabase MCP Server"
    }
