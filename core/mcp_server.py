"""MCP Server for AgentQL Web Scraping Tools.

This module creates an MCP (Model Context Protocol) server that exposes
AgentQL web scraping functionality as tools that can be used by LLM agents.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
from loguru import logger

from .scraper import AgentQLScraper


class AgentQLMCPServer:
    """MCP server that exposes AgentQL scraping tools."""
    
    def __init__(self, db_path: str = "scraping_data.db",
                 data_dir: str = "./data"):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize FastMCP server
        self.mcp = FastMCP('agentql-scraper')
        
        # Initialize database
        self._init_database()
        
        # Register tools
        self._register_tools()
        
    def _init_database(self):
        """Initialize SQLite database for storing scraped data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create scraping sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                metadata TEXT
            )
        ''')
        
        # Create scraped data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                data_key TEXT NOT NULL,
                data_value TEXT,
                data_type TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES scraping_sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _register_tools(self):
        """Register MCP tools for AgentQL scraping."""
        
        @self.mcp.tool()
        async def scrape_url(url: str, selectors: str, headless: bool = True) -> dict:
            """Scrape a website URL using AgentQL natural language selectors.
            
            Args:
                url (str): The URL to scrape
                selectors (str): JSON string of selectors mapping names to AgentQL queries
                    Example: '{"title": "page title", "price": "product price", "description": "product description"}'
                headless (bool): Whether to run browser in headless mode (default: True)
            
            Returns:
                dict: Scraped data with success status and session ID
                
            Example:
                >>> selectors = '{"title": "the main heading", "links": "all navigation links"}'
                >>> result = await scrape_url("https://example.com", selectors)
                >>> print(result)
                {
                    "success": true,
                    "session_id": 123,
                    "data": {"title": "Example Page", "links": ["Home", "About", "Contact"]},
                    "url": "https://example.com"
                }
            """
            try:
                # Parse selectors
                selector_dict = json.loads(selectors)
                
                # Create scraping session
                session_id = self._create_session(url)
                
                # Perform scraping
                async with AgentQLScraper(headless=headless) as scraper:
                    await scraper.navigate(url)
                    data = await scraper.extract_data(selector_dict)
                
                # Save data to database
                self._save_scraped_data(session_id, data)
                self._update_session_success(session_id, True)
                
                logger.info(f"Successfully scraped {url} with session {session_id}")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "data": data,
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                }
                
            except json.JSONDecodeError:
                error_msg = "Invalid JSON format for selectors"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            except Exception as e:
                error_msg = f"Scraping failed: {str(e)}"
                logger.error(f"Error scraping {url}: {e}")
                if 'session_id' in locals():
                    self._update_session_success(session_id, False, error_msg)
                return {"success": False, "error": error_msg}
        
        @self.mcp.tool()
        async def scrape_multiple(urls: str, selectors: str, headless: bool = True) -> dict:
            """Scrape multiple URLs using the same selectors.
            
            Args:
                urls (str): JSON array of URLs to scrape
                    Example: '["https://site1.com", "https://site2.com"]'
                selectors (str): JSON string of selectors (same format as scrape_url)
                headless (bool): Whether to run browser in headless mode
            
            Returns:
                dict: Results from all URLs with success status
                
            Example:
                >>> urls = '["https://site1.com", "https://site2.com"]'
                >>> selectors = '{"title": "page title"}'
                >>> result = await scrape_multiple(urls, selectors)
            """
            try:
                # Parse inputs
                url_list = json.loads(urls)
                selector_dict = json.loads(selectors)
                
                results = []
                
                async with AgentQLScraper(headless=headless) as scraper:
                    for url in url_list:
                        try:
                            session_id = self._create_session(url)
                            await scraper.navigate(url)
                            data = await scraper.extract_data(selector_dict)
                            
                            # Save data
                            self._save_scraped_data(session_id, data)
                            self._update_session_success(session_id, True)
                            
                            results.append({
                                "url": url,
                                "success": True,
                                "session_id": session_id,
                                "data": data
                            })
                            
                        except Exception as e:
                            error_msg = f"Failed to scrape {url}: {str(e)}"
                            logger.error(error_msg)
                            if 'session_id' in locals():
                                self._update_session_success(session_id, False, error_msg)
                            results.append({
                                "url": url,
                                "success": False,
                                "error": error_msg
                            })
                
                return {
                    "success": True,
                    "total_urls": len(url_list),
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }
                
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            except Exception as e:
                error_msg = f"Multiple scraping failed: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        
        @self.mcp.tool()
        def get_scraping_history(limit: int = 10) -> dict:
            """Get recent scraping session history.
            
            Args:
                limit (int): Number of recent sessions to retrieve (default: 10)
            
            Returns:
                dict: List of recent scraping sessions with metadata
                
            Example:
                >>> history = get_scraping_history(5)
                >>> print(history["sessions"][0])
                {
                    "id": 123,
                    "url": "https://example.com",
                    "timestamp": "2024-01-01T12:00:00",
                    "success": true
                }
            """
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, url, timestamp, success, error_message, metadata
                    FROM scraping_sessions
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        "id": row[0],
                        "url": row[1],
                        "timestamp": row[2],
                        "success": bool(row[3]),
                        "error_message": row[4],
                        "metadata": json.loads(row[5]) if row[5] else None
                    })
                
                conn.close()
                
                return {
                    "success": True,
                    "sessions": sessions,
                    "count": len(sessions)
                }
                
            except Exception as e:
                error_msg = f"Failed to retrieve history: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        
        @self.mcp.tool()
        def get_session_data(session_id: int) -> dict:
            """Get scraped data for a specific session.
            
            Args:
                session_id (int): The session ID to retrieve data for
            
            Returns:
                dict: Scraped data from the specified session
                
            Example:
                >>> data = get_session_data(123)
                >>> print(data["data"])
                {"title": "Example Page", "price": "$29.99"}
            """
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get session info
                cursor.execute('''
                    SELECT url, timestamp, success, error_message
                    FROM scraping_sessions
                    WHERE id = ?
                ''', (session_id,))
                
                session_row = cursor.fetchone()
                if not session_row:
                    return {"success": False, "error": f"Session {session_id} not found"}
                
                # Get scraped data
                cursor.execute('''
                    SELECT data_key, data_value, data_type
                    FROM scraped_data
                    WHERE session_id = ?
                ''', (session_id,))
                
                data = {}
                for row in cursor.fetchall():
                    key, value, data_type = row
                    if data_type == 'json' and value:
                        data[key] = json.loads(value)
                    else:
                        data[key] = value
                
                conn.close()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "url": session_row[0],
                    "timestamp": session_row[1],
                    "session_success": bool(session_row[2]),
                    "error_message": session_row[3],
                    "data": data
                }
                
            except Exception as e:
                error_msg = f"Failed to retrieve session data: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
    
    def _create_session(self, url: str, metadata: Optional[Dict] = None) -> int:
        """Create a new scraping session in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_sessions (url, timestamp, success, metadata)
            VALUES (?, ?, ?, ?)
        ''', (url, datetime.now().isoformat(), False, json.dumps(metadata) if metadata else None))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def _update_session_success(self, session_id: int, success: bool, error_message: Optional[str] = None):
        """Update session success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE scraping_sessions
            SET success = ?, error_message = ?
            WHERE id = ?
        ''', (success, error_message, session_id))
        
        conn.commit()
        conn.close()
    
    def _save_scraped_data(self, session_id: int, data: Dict[str, Any]):
        """Save scraped data to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for key, value in data.items():
            if value is None:
                data_type = 'null'
                data_value = None
            elif isinstance(value, (dict, list)):
                data_type = 'json'
                data_value = json.dumps(value)
            else:
                data_type = 'text'
                data_value = str(value)
            
            cursor.execute('''
                INSERT INTO scraped_data (session_id, data_key, data_value, data_type)
                VALUES (?, ?, ?, ?)
            ''', (session_id, key, data_value, data_type))
        
        conn.commit()
        conn.close()
    
    def run(self, server_type: str = "sse", host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server."""
        logger.info(f"Starting AgentQL MCP Server on {host}:{port} ({server_type})")
        
        # Set environment variables for the server
        os.environ.setdefault('MCP_SERVER_HOST', host)
        os.environ.setdefault('MCP_SERVER_PORT', str(port))
        
        self.mcp.run(server_type)


def create_server(db_path: str = "scraping_data.db", data_dir: str = "./data") -> AgentQLMCPServer:
    """Factory function to create an AgentQL MCP server."""
    return AgentQLMCPServer(db_path=db_path, data_dir=data_dir)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentQL MCP Server")
    parser.add_argument("--server_type", type=str, default="sse", choices=["sse", "stdio"])
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db_path", type=str, default="scraping_data.db")
    parser.add_argument("--data_dir", type=str, default="./data")
    
    args = parser.parse_args()
    
    server = create_server(db_path=args.db_path, data_dir=args.data_dir)
    server.run(server_type=args.server_type, host=args.host, port=args.port)
