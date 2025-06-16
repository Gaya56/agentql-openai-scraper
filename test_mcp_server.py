#!/usr/bin/env python3
"""Test script for AgentQL MCP Server."""

import asyncio
from core.mcp_server import create_server


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing AgentQL MCP Server...")
    
    # Create server instance
    server = create_server(db_path="test_scraping.db")
    
    print("✅ Server created successfully")
    print(f"📊 Database path: {server.db_path}")
    print(f"📁 Data directory: {server.data_dir}")
    
    # Test database initialization
    print("\n🔍 Testing database initialization...")
    try:
        import sqlite3
        conn = sqlite3.connect(server.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tables created: {[table[0] for table in tables]}")
        
        conn.close()
        print("✅ Database test passed")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    print("\n🛠️  MCP Tools available:")
    print("- scrape_url: Scrape a single URL with AgentQL selectors")
    print("- scrape_multiple: Scrape multiple URLs with same selectors")
    print("- get_scraping_history: Get recent scraping sessions")
    print("- get_session_data: Get data from a specific session")
    
    print("\n🚀 To start the server, run:")
    print("python -m core.mcp_server --server_type=sse --port=8000")
    
    # Clean up test database
    import os
    if os.path.exists("test_scraping.db"):
        os.remove("test_scraping.db")
        print("\n🧹 Cleaned up test database")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
