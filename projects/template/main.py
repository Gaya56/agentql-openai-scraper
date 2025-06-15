"""Main script for template scraper."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core import AgentQLScraper, OpenAIAnalyzer, DataProcessor
from core.utils import setup_logging, load_config, load_env, validate_api_keys
from loguru import logger


async def scrape_with_analysis(config: dict) -> list:
    """Scrape URLs and analyze content."""
    processor = DataProcessor(f"projects/template/output")
    analyzer = OpenAIAnalyzer(model=config["analysis"].get("model", "gpt-4-turbo-preview"))
    
    results = []
    
    async with AgentQLScraper(headless=config["advanced"]["headless"]) as scraper:
        for url in config["target_urls"]:
            try:
                logger.info(f"Scraping {url}")
                await scraper.navigate(url)
                
                # Extract data using selectors
                data = await scraper.extract_data(config["selectors"])
                data["url"] = url
                
                # Apply transformations if any
                if config["processing"]["transformations"]:
                    data = processor.transform_data([data], config["processing"]["transformations"])[0]
                
                # Add AI analysis if enabled
                if config["analysis"]["enabled"] and data.get("content"):
                    logger.info("Running AI analysis...")
                    analysis = analyzer.analyze(
                        data["content"], 
                        config["analysis"]["prompt"]
                    )
                    data["ai_analysis"] = analysis
                    
                    # Additional analysis features
                    if data.get("title"):
                        sentiment = analyzer.sentiment_analysis(data["title"])
                        data["title_sentiment"] = sentiment
                
                results.append(data)
                
                # Delay between requests
                if config["advanced"]["delay_between_requests"] > 0:
                    await asyncio.sleep(config["advanced"]["delay_between_requests"])
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                results.append({"url": url, "error": str(e)})
                
    return results


def save_results(results: list, config: dict, processor: DataProcessor) -> None:
    """Save results in configured formats."""
    if not results:
        logger.warning("No results to save")
        return
        
    timestamp = config["export"]["timestamp"]
    
    if "json" in config["export"]["formats"]:
        processor.save_json(results, "results.json", timestamp=timestamp)
        
    if "csv" in config["export"]["formats"]:
        processor.save_csv(results, "results.csv", timestamp=timestamp)
        
    if "excel" in config["export"]["formats"]:
        processor.save_excel(results, "results.xlsx", timestamp=timestamp)


async def main():
    """Main function."""
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(str(config_path))
    
    if not config:
        logger.error("Failed to load configuration")
        return
        
    # Create output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize data processor
    processor = DataProcessor(str(output_dir))
    
    # Run scraper
    logger.info(f"Starting {config['name']}...")
    results = await scrape_with_analysis(config)
    
    # Apply filters if any
    if config["processing"]["filters"]:
        results = processor.filter_data(results, config["processing"]["filters"])
    
    # Save results
    save_results(results, config, processor)
    
    # Generate insights if we have results
    if results and config["analysis"]["enabled"]:
        analyzer = OpenAIAnalyzer()
        insights = analyzer.generate_insights(
            results, 
            f"Project: {config['name']}. {config['description']}"
        )
        processor.save_json({"insights": insights}, "insights.json")
        logger.info("Generated insights saved")
    
    logger.success(f"Scraping completed. Processed {len(results)} items.")


if __name__ == "__main__":
    # Setup
    load_env()
    setup_logging(log_level="INFO")
    
    # Validate API keys
    if not validate_api_keys():
        print("\nPlease set up your API keys in the .env file:")
        print("1. Copy .env.example to .env")
        print("2. Add your AGENTQL_API_KEY")
        print("3. Add your OPENAI_API_KEY")
        sys.exit(1)
        
    # Run scraper
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")