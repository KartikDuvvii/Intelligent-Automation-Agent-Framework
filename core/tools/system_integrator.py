import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import sqlalchemy
from sqlalchemy import create_engine, text
from pydantic import BaseModel, Field

class IntegrationTool(ABC):
    """Base class for all integration tools following the Strategy pattern."""
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

class SQLDatabaseTool(IntegrationTool):
    """Tool for interacting with SQL databases."""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns results as a list of dictionaries."""
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            connection.commit()
            return [{"status": "success", "row_count": result.rowcount}]

class FileSystemTool(IntegrationTool):
    """Tool for interacting with the local file system."""
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def execute(self, action: str, file_path: str, content: Optional[str] = None) -> Any:
        full_path = os.path.join(self.base_path, file_path)
        
        if action == "read":
            with open(full_path, "r") as f:
                return f.read()
        elif action == "write":
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content or "")
            return {"status": "success", "path": full_path}
        elif action == "list":
            return os.listdir(full_path if os.path.isdir(full_path) else os.path.dirname(full_path))
        else:
            raise ValueError(f"Unknown action: {action}")

class ExternalAPITool(IntegrationTool):
    """Placeholder for external API integration."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def execute(self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Implementation would use 'requests' or 'httpx'
        # For now, return a mock response
        return {
            "status": 200,
            "url": endpoint,
            "method": method,
            "data": "Mock response from " + endpoint
        }

class ToolFactory:
    """Factory for creating integration tools."""
    
    @staticmethod
    def get_tool(tool_type: str, **kwargs) -> IntegrationTool:
        if tool_type == "sql":
            return SQLDatabaseTool(kwargs.get("connection_string", "sqlite:///automation.db"))
        elif tool_type == "fs":
            return FileSystemTool(kwargs.get("base_path", "."))
        elif tool_type == "api":
            return ExternalAPITool(kwargs.get("api_key"))
        else:
            raise ValueError(f"Unknown tool type: {tool_type}")

# LangChain-compatible wrapper (Optional but useful for Agentic workflows)
from langchain.tools import Tool

def create_system_tools() -> List[Tool]:
    fs_tool = ToolFactory.get_tool("fs")
    sql_tool = ToolFactory.get_tool("sql")
    api_tool = ToolFactory.get_tool("api")
    
    return [
        Tool(
            name="read_file",
            func=lambda p: fs_tool.execute(action="read", file_path=p),
            description="Reads content from a file. Input: file path."
        ),
        Tool(
            name="write_file",
            func=lambda args: fs_tool.execute(action="write", **json.loads(args) if isinstance(args, str) else args),
            description="Writes content to a file. Input: JSON string with 'file_path' and 'content'."
        ),
        Tool(
            name="query_database",
            func=lambda q: sql_tool.execute(query=q),
            description="Executes a SQL query. Input: SQL query string."
        ),
        Tool(
            name="fetch_api",
            func=lambda args: api_tool.execute(**json.loads(args) if isinstance(args, str) else args),
            description="Calls an external API. Input: JSON string with 'endpoint' and 'method'."
        )
    ]
