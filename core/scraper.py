"""AgentQL web scraper wrapper with enhanced functionality."""

import asyncio
from typing import List, Dict, Any, Optional
from agentql import create_async_playwright_page, QueryElements
import agentql
from playwright.async_api import Page
from loguru import logger
import json


class AgentQLScraper:
    """Enhanced web scraper using AgentQL."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.page = await create_async_playwright_page(headless=self.headless)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.page:
            await self.page.close()
            
    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        logger.info(f"Navigating to {url}")
        await self.page.goto(url)
        await self.page.wait_for_load_state('networkidle')
        
    async def query(self, selector: str) -> QueryElements:
        """Query elements using AgentQL natural language selector."""
        logger.debug(f"Querying: {selector}")
        return await self.page.query(selector)
        
    async def extract_data(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using multiple selectors."""
        results = {}
        
        for name, selector in selectors.items():
            try:
                element = await self.query(selector)
                if element:
                    results[name] = await self._extract_text(element)
                else:
                    results[name] = None
                    logger.warning(f"No element found for selector: {name}")
            except Exception as e:
                logger.error(f"Error extracting {name}: {e}")
                results[name] = None
                
        return results
        
    async def _extract_text(self, element: QueryElements) -> str:
        """Extract text from an element."""
        if hasattr(element, 'text_content'):
            return await element.text_content()
        return str(element)
        
    async def scrape_multiple(self, urls: List[str], selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs with the same selectors."""
        results = []
        
        for url in urls:
            try:
                await self.navigate(url)
                data = await self.extract_data(selectors)
                data['url'] = url
                results.append(data)
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                results.append({'url': url, 'error': str(e)})
                
        return results
        
    async def interact(self, actions: List[Dict[str, Any]]) -> None:
        """Perform interactions on the page."""
        for action in actions:
            action_type = action.get('type')
            
            if action_type == 'click':
                element = await self.query(action['selector'])
                await element.click()
            elif action_type == 'fill':
                element = await self.query(action['selector'])
                await element.fill(action['value'])
            elif action_type == 'wait':
                await asyncio.sleep(action.get('seconds', 1))
            else:
                logger.warning(f"Unknown action type: {action_type}")
                
    async def screenshot(self, path: str) -> None:
        """Take a screenshot of the current page."""
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")