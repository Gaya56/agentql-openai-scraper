# Competitive Analysis Setup Guide

A complete step-by-step guide to set up and run competitive analysis using the AgentQL + AI framework.

## 🚀 Quick Start

### Step 1: Create Your Competitive Analysis Project

```bash
# Navigate to your project directory
cd /workspaces/agentql-openai-scraper

# Create a new competitive analysis project
cp -r projects/template projects/competitive-analysis
cd projects/competitive-analysis
```

### Step 2: Files You Need to Edit

You only need to edit **2 files** to get started:

1. **`config.yaml`** - Your scraping configuration
2. **`main.py`** - Your analysis execution script

## 📝 File 1: Edit `config.yaml`

Replace the entire contents of `projects/competitive-analysis/config.yaml` with:

```yaml
name: "Competitive Analysis - Market Intelligence"
description: "Analyze competitor pricing and features for strategic insights"
mode: "hybrid"  # Options: "cloud", "local", "hybrid"

# Target competitor websites to analyze
target_urls:
  - "https://slack.com/pricing"
  - "https://discord.com/nitro"
  - "https://teams.microsoft.com/pricing"
  - "https://zoom.us/pricing"
  # Add your competitor URLs here

# Natural language selectors for data extraction
selectors:
  # Core competitive intelligence data
  features: "product features, feature list, capabilities, or benefits section"
  pricing: "pricing information, price plans, subscription tiers, or cost details"
  
  # Additional strategic data points
  value_props: "value proposition, unique selling points, or main benefits"
  target_audience: "target market, customer types, or use cases mentioned"
  integrations: "integrations, partnerships, or supported platforms"
  testimonials: "customer reviews, testimonials, or case studies"
  free_trial: "free trial, demo, or trial period information"
  enterprise_features: "enterprise features, business plans, or advanced capabilities"

# AI analysis configuration
analysis:
  enabled: true
  model: "gpt-4-turbo-preview"
  prompt: |
    Analyze this competitor data and provide comprehensive strategic insights:
    
    1. **Competitive Positioning Analysis**
       - How does this competitor position themselves in the market?
       - What is their unique value proposition?
       - Who is their primary target audience?
    
    2. **Pricing Strategy Insights**
       - What pricing model do they use (freemium, subscription, one-time, etc.)?
       - How do their prices compare to market standards?
       - What value do they offer at each price tier?
    
    3. **Feature Analysis**
       - What are their core features and capabilities?
       - What features do they emphasize most?
       - What advanced/enterprise features do they offer?
    
    4. **Market Opportunities**
       - What gaps do you identify in their offering?
       - What customer needs might they be missing?
       - What competitive advantages could we leverage?
    
    5. **Strategic Recommendations**
       - How should we position against this competitor?
       - What pricing strategy would be most effective?
       - What features should we prioritize?
    
    Provide specific, actionable insights for business strategy decisions.

# Data processing options
processing:
  transformations:
    - "clean_text"  
    - "extract_numbers"
    - "normalize_pricing"

# Export configuration
export:
  formats: ["json", "csv", "excel"]
  include_analysis: true
  include_timestamps: true
  filename_prefix: "competitive_analysis"

# Browser settings
browser:
  headless: true
  timeout: 30000
  wait_for_content: true

# Rate limiting (be respectful)
rate_limiting:
  delay_between_requests: 3
  max_concurrent_requests: 2
```

## 🐍 File 2: Edit `main.py`

Replace the entire contents of `projects/competitive-analysis/main.py` with:

```python
import asyncio
import yaml
from pathlib import Path
import sys
import os

# Add the core module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core import ScrapingWorkflowController

async def main():
    """Main competitive analysis execution"""
    print("🔍 Starting Competitive Analysis...")
    
    # Load project configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize controller (hybrid mode uses both OpenAI and Ollama)
    controller = ScrapingWorkflowController(mode=config.get('mode', 'hybrid'))
    
    try:
        await controller.initialize()
        print("✅ Controller initialized successfully")
        
        # Execute competitive analysis
        print(f"📊 Analyzing {len(config['target_urls'])} competitors...")
        
        results = []
        for i, url in enumerate(config['target_urls'], 1):
            print(f"🌐 Processing competitor {i}/{len(config['target_urls'])}: {url}")
            
            try:
                result = await controller.scrape_and_analyze(
                    url=url,
                    selectors=config['selectors'],
                    analysis_prompt=config['analysis']['prompt'],
                    project_name=config['name']
                )
                results.append(result)
                print(f"✅ Completed analysis for: {url}")
                
            except Exception as e:
                print(f"❌ Error analyzing {url}: {str(e)}")
                continue
        
        # Generate comparative analysis report
        if results:
            await generate_competitive_report(results, controller, config)
            print("📈 Competitive analysis complete!")
            print(f"📁 Results saved to: data/ directory")
        else:
            print("❌ No results to process")
            
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
    finally:
        if controller:
            await controller.cleanup()

async def generate_competitive_report(results, controller, config):
    """Generate a comprehensive competitive analysis report"""
    
    print("📊 Generating competitive intelligence report...")
    
    # Aggregate all competitor data
    competitor_profiles = {}
    all_insights = []
    
    for result in results:
        url = result.get('url', 'Unknown')
        scraped_data = result.get('scraped_data', {})
        analysis = result.get('analysis', {})
        
        # Build competitor profile
        competitor_profiles[url] = {
            'scraped_data': scraped_data,
            'ai_analysis': analysis,
            'timestamp': result.get('timestamp')
        }
        
        if analysis:
            all_insights.append(f"Analysis for {url}:\n{analysis}")
    
    # Generate master comparative analysis
    comparative_prompt = f"""
    Based on the analysis of {len(results)} competitors, provide a comprehensive competitive intelligence report:
    
    ## Executive Summary
    What are the key findings from this competitive analysis?
    
    ## Market Landscape
    How do these competitors position themselves in the market?
    
    ## Pricing Strategy Insights  
    What pricing patterns and strategies do you observe?
    
    ## Feature Comparison
    What are the common features vs unique differentiators?
    
    ## Market Opportunities
    What gaps or opportunities exist in the market?
    
    ## Strategic Recommendations
    Based on this analysis, what should our competitive strategy be?
    
    Individual competitor insights:
    {chr(10).join(all_insights)}
    """
    
    # Generate master analysis using the controller's analyzer
    master_analysis = await controller.generate_comparative_analysis(comparative_prompt)
    
    # Create comprehensive report
    final_report = {
        'executive_summary': master_analysis,
        'competitor_profiles': competitor_profiles,
        'analysis_metadata': {
            'total_competitors': len(results),
            'analysis_date': controller.session_id,
            'project_name': config['name'],
            'mode_used': config.get('mode', 'hybrid')
        }
    }
    
    # Export the comprehensive report
    await controller.export_final_report(final_report, "competitive_intelligence_master_report")
    
    print("✅ Competitive intelligence report generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Environment Setup

### Step 3: Set Up Your Environment Variables

Edit your `.env` file in the project root:

```bash
# Required for scraping
AGENTQL_API_KEY=your-agentql-api-key-here

# For OpenAI cloud analysis (if using cloud or hybrid mode)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# For local Ollama analysis (if using local or hybrid mode)
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 4: Install Dependencies

```bash
# From the project root directory
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Optional: Install Ollama for local analysis
# Visit https://ollama.ai for installation instructions
```

## 🚀 Run Your Analysis

### Method 1: Run the Project

```bash
# From the project root
cd projects/competitive-analysis
python main.py
```

### Method 2: Quick Test Run

```bash
# Test with a single competitor
python -c "
import asyncio
from core import create_hybrid_controller

async def quick_test():
    controller = create_hybrid_controller()
    await controller.initialize()
    
    result = await controller.scrape_and_analyze(
        url='https://slack.com/pricing',
        selectors={
            'features': 'product features or capabilities',
            'pricing': 'pricing plans or subscription info'
        },
        analysis_prompt='Analyze this competitor data for strategic insights'
    )
    
    print('Results:', result)

asyncio.run(quick_test())
"
```

## 📊 Expected Output

### 1. Console Output
```
🔍 Starting Competitive Analysis...
✅ Controller initialized successfully
📊 Analyzing 4 competitors...
🌐 Processing competitor 1/4: https://slack.com/pricing
✅ Completed analysis for: https://slack.com/pricing
🌐 Processing competitor 2/4: https://discord.com/nitro
✅ Completed analysis for: https://discord.com/nitro
📊 Generating competitive intelligence report...
✅ Competitive intelligence report generated successfully!
📈 Competitive analysis complete!
📁 Results saved to: data/ directory
```

### 2. Generated Files
- `data/competitive_analysis_TIMESTAMP.json` - Raw scraped data
- `data/competitive_analysis_TIMESTAMP.csv` - Tabular data export
- `data/competitive_intelligence_master_report_TIMESTAMP.json` - AI analysis report

### 3. Sample Report Structure
```json
{
  "executive_summary": "Analysis reveals three distinct pricing strategies...",
  "competitor_profiles": {
    "https://slack.com/pricing": {
      "scraped_data": {...},
      "ai_analysis": "Slack positions itself as...",
      "timestamp": "2025-06-16T10:30:00Z"
    }
  },
  "analysis_metadata": {
    "total_competitors": 4,
    "analysis_date": "20250616_103000",
    "project_name": "Competitive Analysis - Market Intelligence"
  }
}
```

## 🎯 Customization Examples

### For SaaS Products
```yaml
selectors:
  features: "product features, integrations, API capabilities"
  pricing: "subscription plans, pricing tiers, free trial info"
  integrations: "supported integrations, API documentation"
  security: "security features, compliance, certifications"
```

### For E-commerce
```yaml
selectors:
  products: "product categories, inventory, catalog"
  pricing: "price ranges, discounts, promotions, shipping costs"
  delivery: "shipping options, delivery times, fulfillment"
  reviews: "customer reviews, ratings, testimonials"
```

### For Services
```yaml
selectors:
  services: "service offerings, specializations, packages"
  pricing: "hourly rates, project costs, service packages"
  team: "team size, expertise, credentials, certifications"
  process: "methodology, process, approach, timeline"
```

## 🚨 Important Notes

### Rate Limiting
The configuration includes respectful rate limiting:
- 3-second delays between requests
- Maximum 2 concurrent requests
- 3 retry attempts for failed requests

### Legal Compliance
- Only scrape publicly available information
- Respect robots.txt files
- Review website terms of service
- Consider adding longer delays for sensitive sites

### Troubleshooting

**Issue**: "Module not found" errors
**Solution**: Run from project root: `python -m projects.competitive-analysis.main`

**Issue**: AgentQL selectors not finding content
**Solution**: Try broader selectors: `"pricing information, cost, price, or fee details"`

**Issue**: AI analysis failing
**Solution**: Check your API keys in `.env` file and ensure services are running

## 🔄 Regular Monitoring

Set up automated competitive monitoring:

```python
# Add to main.py for scheduled runs
import schedule
import time

def run_analysis():
    asyncio.run(main())

# Schedule weekly competitive analysis
schedule.every().monday.at("09:00").do(run_analysis)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

---

**Ready to dominate your competition?** Follow this guide to get actionable competitive intelligence in minutes!
