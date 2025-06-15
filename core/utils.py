"""Utility functions for the framework."""

import os
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger
import json


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Set up logging configuration."""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger if specified
    if log_file:
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB"
        )
        

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}
        

def load_env() -> None:
    """Load environment variables from .env file."""
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("Environment variables loaded from .env")
    else:
        logger.warning(".env file not found")
        

def validate_api_keys() -> bool:
    """Validate that required API keys are set."""
    required_keys = ['AGENTQL_API_KEY', 'OPENAI_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
            
    if missing_keys:
        logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
        return False
        
    return True
    

def create_project_structure(project_name: str) -> None:
    """Create a new project structure."""
    project_path = Path(f"projects/{project_name}")
    
    if project_path.exists():
        logger.error(f"Project {project_name} already exists")
        return
        
    # Create directories
    project_path.mkdir(parents=True)
    (project_path / "output").mkdir()
    (project_path / "logs").mkdir()
    
    # Create default files
    config = {
        "name": project_name,
        "description": "Description of your scraping project",
        "target_urls": ["https://example.com"],
        "selectors": {
            "title": "h1",
            "content": "main article"
        },
        "analysis": {
            "enabled": True,
            "prompt": "Analyze this content and provide insights"
        },
        "export": {
            "formats": ["json", "csv"],
            "timestamp": True
        }
    }
    
    with open(project_path / "config.yaml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
        
    # Create main.py
    main_content = '''"""Main script for {project_name} scraper."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core import AgentQLScraper, OpenAIAnalyzer, DataProcessor
from core.utils import setup_logging, load_config, load_env, validate_api_keys


async def main():
    """Main scraping function."""
    # Load configuration
    config = load_config("projects/{project_name}/config.yaml")
    
    # Initialize components
    processor = DataProcessor(f"projects/{project_name}/output")
    analyzer = OpenAIAnalyzer()
    
    # Scrape data
    async with AgentQLScraper() as scraper:
        results = []
        
        for url in config["target_urls"]:
            await scraper.navigate(url)
            data = await scraper.extract_data(config["selectors"])
            
            # Add analysis if enabled
            if config["analysis"]["enabled"]:
                analysis = analyzer.analyze(data, config["analysis"]["prompt"])
                data["analysis"] = analysis
                
            results.append(data)
            
    # Save results
    if "json" in config["export"]["formats"]:
        processor.save_json(results, "{project_name}_results.json")
    if "csv" in config["export"]["formats"]:
        processor.save_csv(results, "{project_name}_results.csv")
        
    print(f"Scraping completed. Found {{len(results)}} items.")
    

if __name__ == "__main__":
    # Setup
    load_env()
    setup_logging()
    
    # Validate API keys
    if not validate_api_keys():
        print("Please set up your API keys in the .env file")
        sys.exit(1)
        
    # Run scraper
    asyncio.run(main())
'''.format(project_name=project_name)
    
    with open(project_path / "main.py", 'w') as f:
        f.write(main_content)
        
    # Create __init__.py
    (project_path / "__init__.py").touch()
    
    logger.info(f"Project {project_name} created successfully")
    

def merge_configs(base_config: Dict[str, Any], 
                 override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries."""
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
            
    return result