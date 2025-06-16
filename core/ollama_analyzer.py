"""Ollama-based local LLM analyzer with MCP integration.

This module provides local LLM analysis capabilities using Ollama,
offering privacy-aware analysis that doesn't send data to external services.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import httpx
from loguru import logger


class OllamaAnalyzer:
    """Analyze scraped data using local Ollama LLM."""
    
    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        mcp_server_url: str = "http://127.0.0.1:8000",
        temperature: float = 0.6
    ):
        """Initialize Ollama analyzer.
        
        Args:
            model: Ollama model name to use
            base_url: Ollama server base URL
            mcp_server_url: MCP server URL for tool access
            temperature: LLM temperature setting
        """
        self.model = model
        self.base_url = base_url
        self.mcp_server_url = mcp_server_url
        self.temperature = temperature
        
        # Initialize Ollama LLM
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            streaming=False
        )
        
        # MCP client configuration
        self.mcp_client = None
        self.agent_executor = None
        self.chat_history = []
        
        # Analysis prompts
        self.SYSTEM_PROMPT = (
            "You are an expert data analyst specializing in "
            "web scraping analysis.\n"
            "You can analyze scraped data, identify patterns, extract "
            "insights, and provide structured summaries.\n\n"
            "Your capabilities include:\n"
            "1. Data structure analysis and validation\n"
            "2. Content summarization and key point extraction\n"
            "3. Pattern recognition and trend identification\n"
            "4. Data quality assessment and cleanup suggestions\n"
            "5. Actionable insights and recommendations\n\n"
            "Always provide clear, structured responses with specific "
            "examples from the data."
        )
        
    async def initialize(self) -> bool:
        """Initialize the analyzer and MCP connections.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Check Ollama availability
            if not await self._check_ollama_connection():
                logger.warning(
                    "Ollama not available, analyzer will work in basic mode"
                )
                return False
                
            # Setup MCP client if available
            await self._setup_mcp_client()
            
            logger.info(f"OllamaAnalyzer initialized with model: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OllamaAnalyzer: {e}")
            return False
    
    async def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [
                        m.get("name", "").split(":")[0] for m in models
                    ]
                    if self.model.split(":")[0] not in model_names:
                        logger.warning(
                            f"Model {self.model} not found in Ollama"
                        )
                        return False
                    return True
                return False
        except Exception as e:
            logger.debug(f"Ollama connection check failed: {e}")
            return False
    
    async def _setup_mcp_client(self):
        """Setup MCP client for tool access."""
        try:
            server_config = {
                "default": {
                    "url": f"{self.mcp_server_url}/sse",
                    "transport": "sse",
                    "options": {
                        "timeout": 10.0,
                        "retry_connect": True,
                        "max_retries": 2
                    }
                }
            }
            
            self.mcp_client = MultiServerMCPClient(server_config)
            logger.debug("MCP client configured")
            
        except Exception as e:
            logger.debug(f"MCP client setup failed: {e}")
            self.mcp_client = None
    
    async def analyze(
        self,
        data: Any,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Analyze data with a custom prompt using local Ollama LLM.
        
        Args:
            data: Data to analyze (dict, list, or string)
            prompt: Analysis prompt/question
            system_prompt: Optional system prompt override
            
        Returns:
            str: Analysis results
        """
        try:
            # Prepare data for analysis
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                data_str = str(data)
            
            # Prepare messages
            messages = [
                SystemMessage(content=system_prompt or self.SYSTEM_PROMPT),
                HumanMessage(
                    content=f"{prompt}\n\nData to analyze:\n{data_str}"
                )
            ]
            
            # Get response from Ollama
            response = await self.llm.ainvoke(messages)
            result = (
                response.content
                if hasattr(response, 'content')
                else str(response)
            )
            
            # Store in chat history
            self.chat_history.extend([
                HumanMessage(content=prompt),
                AIMessage(content=result)
            ])
            
            logger.debug(f"Analysis completed, result length: {len(result)}")
            return result
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def summarize(
        self,
        text: str,
        max_length: int = 200,
        focus: Optional[str] = None
    ) -> str:
        """Summarize text content using local LLM.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in words
            focus: Optional focus area for summary
            
        Returns:
            str: Text summary
        """
        focus_instruction = f" Focus particularly on: {focus}." if focus else ""
        prompt = (
            f"Summarize the following text in {max_length} words or less. "
            f"Focus on key points and main ideas.{focus_instruction}"
        )
        
        return await self.analyze(text, prompt)
    
    async def extract_insights(self, data: Any) -> Dict[str, Any]:
        """Extract structured insights from scraped data.
        
        Args:
            data: Scraped data to analyze
            
        Returns:
            dict: Structured insights
        """
        prompt = """Analyze this scraped data and provide structured insights in the following format:

        1. **Data Overview**: Brief description of what was scraped
        2. **Key Findings**: 3-5 most important discoveries  
        3. **Data Quality**: Assessment of completeness and accuracy
        4. **Patterns**: Any notable patterns or trends
        5. **Recommendations**: Actionable next steps or improvements
        
        Please be specific and reference actual data points from the content.
        """
        
        try:
            analysis = await self.analyze(data, prompt)
            
            # Try to parse structured response
            insights = {
                "timestamp": datetime.now().isoformat(),
                "data_size": len(str(data)),
                "analysis": analysis,
                "model_used": self.model,
                "local_analysis": True
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "local_analysis": True
            }
    
    async def compare_with_openai(
        self, 
        data: Any, 
        prompt: str,
        openai_analyzer=None
    ) -> Dict[str, Any]:
        """Compare analysis results between Ollama and OpenAI.
        
        Args:
            data: Data to analyze
            prompt: Analysis prompt
            openai_analyzer: OpenAI analyzer instance for comparison
            
        Returns:
            dict: Comparison results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "data_size": len(str(data))
        }
        
        # Get Ollama analysis
        try:
            ollama_result = await self.analyze(data, prompt)
            results["ollama_analysis"] = {
                "result": ollama_result,
                "model": self.model,
                "local": True,
                "error": None
            }
        except Exception as e:
            results["ollama_analysis"] = {
                "result": None,
                "model": self.model,
                "local": True,
                "error": str(e)
            }
        
        # Get OpenAI analysis if available
        if openai_analyzer:
            try:
                openai_result = openai_analyzer.analyze(data, prompt)
                results["openai_analysis"] = {
                    "result": openai_result,
                    "model": openai_analyzer.model,
                    "local": False,
                    "error": None
                }
            except Exception as e:
                results["openai_analysis"] = {
                    "result": None,
                    "model": getattr(openai_analyzer, 'model', 'unknown'),
                    "local": False,
                    "error": str(e)
                }
        else:
            results["openai_analysis"] = {
                "result": "OpenAI analyzer not available",
                "model": None,
                "local": False,
                "error": "Analyzer not provided"
            }
        
        return results
    
    async def batch_analyze(
        self, 
        data_items: List[Any], 
        prompt: str,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """Analyze multiple data items concurrently.
        
        Args:
            data_items: List of data items to analyze
            prompt: Analysis prompt for each item
            max_concurrent: Maximum concurrent analyses
            
        Returns:
            list: Analysis results for each item
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_item(item, index):
            async with semaphore:
                try:
                    result = await self.analyze(item, prompt)
                    return {
                        "index": index,
                        "success": True,
                        "result": result,
                        "error": None
                    }
                except Exception as e:
                    return {
                        "index": index,
                        "success": False,
                        "result": None,
                        "error": str(e)
                    }
        
        tasks = [
            analyze_item(item, i) 
            for i, item in enumerate(data_items)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions in gather
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "result": None,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Ollama model.
        
        Returns:
            dict: Model information
        """
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "local": True,
            "mcp_enabled": self.mcp_client is not None,
            "chat_history_length": len(self.chat_history)
        }
    
    def clear_history(self):
        """Clear chat history."""
        self.chat_history.clear()
        logger.debug("Chat history cleared")


# Utility functions for integration
def create_ollama_analyzer(
    model: str = None,
    base_url: str = None,
    **kwargs
) -> OllamaAnalyzer:
    """Factory function to create OllamaAnalyzer with environment defaults.
    
    Args:
        model: Override model name (defaults to OLLAMA_MODEL env var)
        base_url: Override base URL (defaults to OLLAMA_BASE_URL env var)
        **kwargs: Additional arguments for OllamaAnalyzer
        
    Returns:
        OllamaAnalyzer: Configured analyzer instance
    """
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    return OllamaAnalyzer(
        model=model,
        base_url=base_url,
        **kwargs
    )
