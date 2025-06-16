"""Unified controller for AgentQL scraping and analysis workflow.

This module provides a high-level interface that coordinates web scraping,
data storage, and analysis using either local (Ollama) or cloud (OpenAI) LLMs.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json

from loguru import logger

from .scraper import AgentQLScraper
from .analyzer import OpenAIAnalyzer
from .ollama_analyzer import OllamaAnalyzer, create_ollama_analyzer
from .data_processor import DataProcessor
from .mcp_server import AgentQLMCPServer


class ScrapingWorkflowController:
    """Unified controller for the complete scraping and analysis workflow."""
    
    def __init__(
        self,
        mode: str = "hybrid",  # "local", "cloud", or "hybrid"
        data_dir: str = "./data",
        enable_mcp: bool = True,
        **config
    ):
        """Initialize the workflow controller.
        
        Args:
            mode: Analysis mode - "local" (Ollama only), "cloud" (OpenAI only), 
                  or "hybrid" (both)
            data_dir: Directory for storing scraped data
            enable_mcp: Whether to enable MCP server functionality
            **config: Additional configuration options
        """
        self.mode = mode
        self.data_dir = Path(data_dir)
        self.enable_mcp = enable_mcp
        self.config = config
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.scraper: Optional[AgentQLScraper] = None
        self.openai_analyzer: Optional[OpenAIAnalyzer] = None
        self.ollama_analyzer: Optional[OllamaAnalyzer] = None
        self.data_processor: Optional[DataProcessor] = None
        self.mcp_server: Optional[AgentQLMCPServer] = None
        
        # Workflow state
        self.current_session: Optional[str] = None
        self.workflow_history: List[Dict[str, Any]] = []
        
        logger.info(f"WorkflowController initialized in {mode} mode")
    
    async def initialize(self) -> bool:
        """Initialize all components based on the selected mode.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize data processor
            self.data_processor = DataProcessor()
            
            # Initialize analyzers based on mode
            if self.mode in ["cloud", "hybrid"]:
                try:
                    self.openai_analyzer = OpenAIAnalyzer(
                        api_key=os.getenv("OPENAI_API_KEY"),
                        model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
                    )
                    logger.info("OpenAI analyzer initialized")
                except Exception as e:
                    logger.warning(f"OpenAI analyzer failed to initialize: {e}")
                    if self.mode == "cloud":
                        return False
            
            if self.mode in ["local", "hybrid"]:
                try:
                    self.ollama_analyzer = create_ollama_analyzer()
                    await self.ollama_analyzer.initialize()
                    logger.info("Ollama analyzer initialized")
                except Exception as e:
                    logger.warning(f"Ollama analyzer failed to initialize: {e}")
                    if self.mode == "local":
                        return False
            
            # Initialize MCP server if enabled
            if self.enable_mcp:
                try:
                    self.mcp_server = AgentQLMCPServer(
                        db_path=str(self.data_dir / "scraped_data.db")
                    )
                    logger.info("MCP server initialized")
                except Exception as e:
                    logger.warning(f"MCP server failed to initialize: {e}")
            
            logger.info("WorkflowController fully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WorkflowController: {e}")
            return False
    
    async def scrape_and_analyze(
        self,
        url: str,
        query: str,
        analysis_prompt: str,
        session_name: Optional[str] = None,
        analyzer_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete workflow: scrape data and analyze it.
        
        Args:
            url: URL to scrape
            query: AgentQL query for data extraction
            analysis_prompt: Prompt for LLM analysis
            session_name: Optional session name for tracking
            analyzer_preference: "local", "cloud", or None (use mode default)
            
        Returns:
            dict: Complete workflow results
        """
        session_name = session_name or f"session_{datetime.now().isoformat()}"
        self.current_session = session_name
        
        workflow_result = {
            "session_name": session_name,
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "query": query,
            "analysis_prompt": analysis_prompt,
            "mode": self.mode,
            "steps": {},
            "success": False,
            "error": None
        }
        
        try:
            # Step 1: Scrape data
            logger.info(f"[{session_name}] Starting scraping: {url}")
            scraped_data = await self._scrape_data(url, query)
            workflow_result["steps"]["scraping"] = {
                "success": scraped_data is not None,
                "data_size": len(str(scraped_data)) if scraped_data else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            if not scraped_data:
                workflow_result["error"] = "Scraping failed"
                return workflow_result
            
            # Step 2: Store data
            logger.info(f"[{session_name}] Storing scraped data")
            storage_result = await self._store_data(
                scraped_data, url, query, session_name
            )
            workflow_result["steps"]["storage"] = storage_result
            
            # Step 3: Analyze data
            logger.info(f"[{session_name}] Analyzing data")
            analysis_result = await self._analyze_data(
                scraped_data, analysis_prompt, analyzer_preference
            )
            workflow_result["steps"]["analysis"] = analysis_result
            
            # Step 4: Generate insights
            if analysis_result.get("success"):
                logger.info(f"[{session_name}] Generating insights")
                insights = await self._generate_insights(scraped_data)
                workflow_result["steps"]["insights"] = insights
            
            workflow_result["success"] = True
            workflow_result["results"] = {
                "scraped_data": scraped_data,
                "analysis": analysis_result.get("results"),
                "insights": workflow_result["steps"].get("insights", {})
            }
            
            # Save workflow result
            await self._save_workflow_result(workflow_result)
            
            logger.info(f"[{session_name}] Workflow completed successfully")
            return workflow_result
            
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            logger.error(f"[{session_name}] {error_msg}")
            workflow_result["error"] = error_msg
            return workflow_result
    
    async def _scrape_data(self, url: str, query: str) -> Optional[Dict[str, Any]]:
        """Scrape data from URL using AgentQL."""
        try:
            # Create scraper instance for this operation
            async with AgentQLScraper(headless=True) as scraper:
                await scraper.navigate(url)
                data = await scraper.query_data(query)
                return data
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return None
    
    async def _store_data(
        self, 
        data: Dict[str, Any], 
        url: str, 
        query: str, 
        session_name: str
    ) -> Dict[str, Any]:
        """Store scraped data."""
        try:
            # Store in JSON file
            filename = f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.data_dir / filename
            
            storage_data = {
                "session_name": session_name,
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "query": query,
                "data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
            
            # Also store in MCP database if available
            if self.mcp_server:
                try:
                    await self.mcp_server.store_scraped_data(
                        url, json.dumps(data), query, session_name
                    )
                except Exception as e:
                    logger.warning(f"MCP storage failed: {e}")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "size": filepath.stat().st_size,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data storage failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_data(
        self,
        data: Dict[str, Any],
        prompt: str,
        analyzer_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze data using available analyzers."""
        preference = analyzer_preference or self.mode
        results = {
            "timestamp": datetime.now().isoformat(),
            "preference": preference,
            "results": {}
        }
        
        # Try preferred analyzer first
        if preference in ["local", "hybrid"] and self.ollama_analyzer:
            try:
                ollama_result = await self.ollama_analyzer.analyze(data, prompt)
                results["results"]["ollama"] = {
                    "success": True,
                    "result": ollama_result,
                    "model": self.ollama_analyzer.model,
                    "local": True
                }
                results["success"] = True
            except Exception as e:
                results["results"]["ollama"] = {
                    "success": False,
                    "error": str(e),
                    "local": True
                }
        
        if preference in ["cloud", "hybrid"] and self.openai_analyzer:
            try:
                openai_result = self.openai_analyzer.analyze(data, prompt)
                results["results"]["openai"] = {
                    "success": True,
                    "result": openai_result,
                    "model": self.openai_analyzer.model,
                    "local": False
                }
                results["success"] = True
            except Exception as e:
                results["results"]["openai"] = {
                    "success": False,
                    "error": str(e),
                    "local": False
                }
        
        # Set overall success
        results["success"] = any(
            r.get("success", False) for r in results["results"].values()
        )
        
        return results
    
    async def _generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured insights from scraped data."""
        insights = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "results": {}
        }
        
        # Try Ollama first for privacy
        if self.ollama_analyzer:
            try:
                ollama_insights = await self.ollama_analyzer.extract_insights(data)
                insights["results"]["ollama"] = ollama_insights
                insights["success"] = True
            except Exception as e:
                logger.warning(f"Ollama insights failed: {e}")
        
        # Fallback to OpenAI if available and no local success
        if not insights["success"] and self.openai_analyzer:
            try:
                # Create insights prompt
                prompt = (
                    "Analyze this data and provide structured insights:\n"
                    "1. Data Overview\n2. Key Findings\n3. Patterns\n"
                    "4. Data Quality\n5. Recommendations"
                )
                openai_insights = self.openai_analyzer.analyze(data, prompt)
                insights["results"]["openai"] = {
                    "analysis": openai_insights,
                    "model": self.openai_analyzer.model,
                    "local": False
                }
                insights["success"] = True
            except Exception as e:
                logger.warning(f"OpenAI insights failed: {e}")
        
        return insights
    
    async def _save_workflow_result(self, result: Dict[str, Any]):
        """Save workflow result to file."""
        try:
            filename = f"workflow_{result['session_name']}.json"
            filepath = self.data_dir / "workflows" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.workflow_history.append(result)
            logger.debug(f"Workflow result saved: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save workflow result: {e}")
    
    async def batch_scrape_and_analyze(
        self,
        urls_and_queries: List[Dict[str, str]],
        analysis_prompt: str,
        max_concurrent: int = 3,
        session_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple URLs concurrently.
        
        Args:
            urls_and_queries: List of {"url": str, "query": str} dicts
            analysis_prompt: Analysis prompt for all items
            max_concurrent: Maximum concurrent operations
            session_name: Session name prefix
            
        Returns:
            list: Results for each URL
        """
        session_name = session_name or f"batch_{datetime.now().isoformat()}"
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item, index):
            async with semaphore:
                item_session = f"{session_name}_item_{index}"
                return await self.scrape_and_analyze(
                    url=item["url"],
                    query=item["query"],
                    analysis_prompt=analysis_prompt,
                    session_name=item_session
                )
        
        tasks = [
            process_item(item, i) 
            for i, item in enumerate(urls_and_queries)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "url": urls_and_queries[i]["url"],
                    "index": i
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current controller status."""
        return {
            "mode": self.mode,
            "initialized": {
                "scraper": self.scraper is not None,
                "openai_analyzer": self.openai_analyzer is not None,
                "ollama_analyzer": self.ollama_analyzer is not None,
                "data_processor": self.data_processor is not None,
                "mcp_server": self.mcp_server is not None
            },
            "current_session": self.current_session,
            "workflow_history_count": len(self.workflow_history),
            "data_dir": str(self.data_dir),
            "enable_mcp": self.enable_mcp
        }
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        return self.workflow_history.copy()
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.ollama_analyzer:
                self.ollama_analyzer.clear_history()
            
            logger.info("WorkflowController cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Factory functions
def create_local_controller(data_dir: str = "./data", **config) -> ScrapingWorkflowController:
    """Create controller for local-only (Ollama) analysis."""
    return ScrapingWorkflowController(
        mode="local",
        data_dir=data_dir,
        **config
    )


def create_cloud_controller(data_dir: str = "./data", **config) -> ScrapingWorkflowController:
    """Create controller for cloud-only (OpenAI) analysis."""
    return ScrapingWorkflowController(
        mode="cloud",
        data_dir=data_dir,
        **config
    )


def create_hybrid_controller(data_dir: str = "./data", **config) -> ScrapingWorkflowController:
    """Create controller for hybrid (local + cloud) analysis."""
    return ScrapingWorkflowController(
        mode="hybrid",
        data_dir=data_dir,
        **config
    )
