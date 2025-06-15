"""Data processing utilities for scraped content."""

import pandas as pd
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class DataProcessor:
    """Process and export scraped data."""
    
    def __init__(self, output_dir: str = "./data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def save_json(self, data: Any, filename: str, timestamp: bool = True) -> str:
        """Save data as JSON."""
        if timestamp:
            filename = self._add_timestamp(filename)
            
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Data saved to {filepath}")
        return str(filepath)
        
    def save_csv(self, data: List[Dict[str, Any]], filename: str, timestamp: bool = True) -> str:
        """Save data as CSV."""
        if not data:
            logger.warning("No data to save")
            return ""
            
        if timestamp:
            filename = self._add_timestamp(filename)
            
        filepath = self.output_dir / filename
        
        # Get all unique keys
        keys = set()
        for item in data:
            keys.update(item.keys())
            
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(data)
            
        logger.info(f"Data saved to {filepath}")
        return str(filepath)
        
    def save_excel(self, data: List[Dict[str, Any]], filename: str, 
                   sheet_name: str = "Data", timestamp: bool = True) -> str:
        """Save data as Excel file."""
        if timestamp:
            filename = self._add_timestamp(filename)
            
        filepath = self.output_dir / filename
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, sheet_name=sheet_name, index=False)
        
        logger.info(f"Data saved to {filepath}")
        return str(filepath)
        
    def load_json(self, filename: str) -> Any:
        """Load data from JSON file."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def load_csv(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from CSV file."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
            
    def transform_data(self, data: List[Dict[str, Any]], 
                      transformations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply transformations to data."""
        df = pd.DataFrame(data)
        
        for column, transform in transformations.items():
            if column not in df.columns:
                continue
                
            if transform == "lowercase":
                df[column] = df[column].str.lower()
            elif transform == "uppercase":
                df[column] = df[column].str.upper()
            elif transform == "strip":
                df[column] = df[column].str.strip()
            elif isinstance(transform, dict):
                if "replace" in transform:
                    df[column] = df[column].replace(transform["replace"])
                    
        return df.to_dict('records')
        
    def aggregate_data(self, data: List[Dict[str, Any]], 
                      group_by: str, aggregate_on: str, 
                      method: str = "count") -> Dict[str, Any]:
        """Aggregate data by a specific field."""
        df = pd.DataFrame(data)
        
        if method == "count":
            result = df.groupby(group_by)[aggregate_on].count()
        elif method == "sum":
            result = df.groupby(group_by)[aggregate_on].sum()
        elif method == "mean":
            result = df.groupby(group_by)[aggregate_on].mean()
        elif method == "min":
            result = df.groupby(group_by)[aggregate_on].min()
        elif method == "max":
            result = df.groupby(group_by)[aggregate_on].max()
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
            
        return result.to_dict()
        
    def filter_data(self, data: List[Dict[str, Any]], 
                   filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data based on conditions."""
        df = pd.DataFrame(data)
        
        for column, condition in filters.items():
            if column not in df.columns:
                continue
                
            if isinstance(condition, dict):
                if "equals" in condition:
                    df = df[df[column] == condition["equals"]]
                elif "contains" in condition:
                    df = df[df[column].str.contains(condition["contains"], na=False)]
                elif "greater_than" in condition:
                    df = df[df[column] > condition["greater_than"]]
                elif "less_than" in condition:
                    df = df[df[column] < condition["less_than"]]
                elif "in" in condition:
                    df = df[df[column].isin(condition["in"])]
                    
        return df.to_dict('records')
        
    def _add_timestamp(self, filename: str) -> str:
        """Add timestamp to filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts = filename.split('.')
        
        if len(parts) > 1:
            return f"{'.'.join(parts[:-1])}_{timestamp}.{parts[-1]}"
        else:
            return f"{filename}_{timestamp}"