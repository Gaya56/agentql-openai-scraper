"""OpenAI integration for data analysis and processing."""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger
import json


class OpenAIAnalyzer:
    """Analyze scraped data using OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
    def analyze(self, data: Any, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Analyze data with a custom prompt."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            # Convert data to string if needed
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, indent=2)
            else:
                data_str = str(data)
                
            user_message = f"{prompt}\n\nData:\n{data_str}"
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            return f"Analysis failed: {str(e)}"
            
    def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize text content."""
        prompt = f"Summarize the following text in {max_length} words or less. Focus on key points and main ideas."
        return self.analyze(text, prompt)
        
    def extract_entities(self, text: str, entity_types: List[str]) -> Dict[str, List[str]]:
        """Extract specific entities from text."""
        entity_list = ", ".join(entity_types)
        prompt = f"Extract the following entities from the text: {entity_list}. Return as JSON."
        
        system_prompt = "You are an entity extraction assistant. Always return valid JSON."
        
        result = self.analyze(text, prompt, system_prompt)
        
        try:
            return json.loads(result)
        except:
            logger.warning("Failed to parse entity extraction result as JSON")
            return {entity: [] for entity in entity_types}
            
    def classify(self, text: str, categories: List[str]) -> str:
        """Classify text into one of the provided categories."""
        category_list = ", ".join(categories)
        prompt = f"Classify the following text into one of these categories: {category_list}. Return only the category name."
        
        result = self.analyze(text, prompt)
        return result.strip()
        
    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Perform sentiment analysis on text."""
        prompt = """Analyze the sentiment of this text. Return a JSON with:
        - sentiment: positive, negative, or neutral
        - confidence: 0-100
        - key_phrases: list of phrases that influenced the sentiment"""
        
        system_prompt = "You are a sentiment analysis expert. Always return valid JSON."
        
        result = self.analyze(text, prompt, system_prompt)
        
        try:
            return json.loads(result)
        except:
            return {
                "sentiment": "neutral",
                "confidence": 0,
                "key_phrases": []
            }
            
    def generate_insights(self, data: List[Dict[str, Any]], context: str) -> str:
        """Generate insights from scraped data."""
        prompt = f"""Given the following context: {context}
        
        Analyze this data and provide:
        1. Key findings
        2. Patterns or trends
        3. Actionable recommendations
        
        Be specific and data-driven in your analysis."""
        
        return self.analyze(data, prompt)