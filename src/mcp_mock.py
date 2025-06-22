"""
Mock MCP SDK for testing purposes.
"""

from typing import Any, Dict, Callable, Optional
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)


class ToolContext:
    """Mock tool context for MCP tools."""
    
    def __init__(self, session_id: str = "test_session"):
        self.session_id = session_id
        self.metadata = {}


class MCPServer:
    """Mock MCP server implementation."""
    
    def __init__(self, title: str, version: str = "1.0.0"):
        self.title = title
        self.version = version
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        
    def tool(self, name: str, schema: Optional[BaseModel] = None):
        """Decorator to register a tool."""
        def decorator(func: Callable):
            self.tools[name] = {
                'function': func,
                'schema': schema,
                'name': name
            }
            logger.info(f"Registered tool: {name}")
            return func
        return decorator
    
    def resource(self, uri: str):
        """Decorator to register a resource."""
        def decorator(func: Callable):
            self.resources[uri] = func
            logger.info(f"Registered resource: {uri}")
            return func
        return decorator
    
    def prompt(self, name: str):
        """Decorator to register a prompt."""
        def decorator(func: Callable):
            self.prompts[name] = func
            logger.info(f"Registered prompt: {name}")
            return func
        return decorator
    
    async def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered tool."""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        
        tool = self.tools[name]
        context = ToolContext()
        
        # Convert args dict to schema if provided
        if tool['schema']:
            args = tool['schema'](**args)
        
        result = await tool['function'](context, args)
        return result
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Mock server run method."""
        logger.info(f"Mock MCP Server '{self.title}' would start on {host}:{port}")
        logger.info(f"Registered tools: {list(self.tools.keys())}")
        logger.info(f"Debug mode: {debug}")
        
        # In a real implementation, this would start the server
        # For testing, we just log the configuration


class MCPClient:
    """Mock MCP client implementation."""
    
    def __init__(self, server_url: str = "ws://localhost:8000/mcp"):
        self.server_url = server_url
        self.connected = False
        
    async def connect(self):
        """Mock connection to server."""
        logger.info(f"Mock connecting to {self.server_url}")
        self.connected = True
        
    async def disconnect(self):
        """Mock disconnection from server."""
        logger.info("Mock disconnecting from server")
        self.connected = False
        
    async def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock tool call."""
        if not self.connected:
            await self.connect()
            
        logger.info(f"Mock calling tool {name} with args: {args}")
        # This would normally make an actual RPC call
        return {"mock": "response", "tool": name}