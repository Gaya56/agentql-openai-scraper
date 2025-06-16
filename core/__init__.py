"""Core framework modules for AgentQL + OpenAI + Ollama + MCP integration."""

from .scraper import AgentQLScraper
from .analyzer import OpenAIAnalyzer
from .data_processor import DataProcessor
from .utils import setup_logging, load_config

# Optional imports - may not be available in all environments
try:
    from .ollama_analyzer import OllamaAnalyzer, create_ollama_analyzer
    _OLLAMA_AVAILABLE = True
except ImportError:
    _OLLAMA_AVAILABLE = False
    OllamaAnalyzer = None
    create_ollama_analyzer = None

try:
    from .mcp_server import AgentQLMCPServer
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    AgentQLMCPServer = None

try:
    from .controller import (
        ScrapingWorkflowController,
        create_local_controller,
        create_cloud_controller,
        create_hybrid_controller
    )
    _CONTROLLER_AVAILABLE = True
except ImportError:
    _CONTROLLER_AVAILABLE = False
    ScrapingWorkflowController = None
    create_local_controller = None
    create_cloud_controller = None
    create_hybrid_controller = None

__all__ = [
    # Scraping
    'AgentQLScraper',
    
    # Analysis
    'OpenAIAnalyzer',
    'OllamaAnalyzer',
    'create_ollama_analyzer',
    
    # Data processing
    'DataProcessor',
    
    # MCP Integration
    'AgentQLMCPServer',
    
    # Unified workflow
    'ScrapingWorkflowController',
    'create_local_controller',
    'create_cloud_controller',
    'create_hybrid_controller',
    
    # Utilities
    'setup_logging',
    'load_config'
]