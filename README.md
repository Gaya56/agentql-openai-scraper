# AgentQL + OpenAI Web Scraping Framework

A flexible web scraping framework that combines AgentQL's powerful web scraping capabilities with OpenAI's analysis and intelligence.

## Features

- 🔍 Smart web scraping using AgentQL's natural language selectors
- 🤖 AI-powered data analysis with OpenAI integration
- 📁 Modular project structure for different scraping tasks
- 🔄 Reusable components and utilities
- 📊 Built-in data processing and export capabilities

## Prerequisites

- Python 3.8 or higher
- AgentQL API key
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Gaya56/agentql-openai-scraper.git
cd agentql-openai-scraper
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright driver:
```bash
playwright install chromium
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Quick Start

1. Create a new project in the `projects/` directory:
```bash
cp -r projects/template projects/my-scraper
```

2. Edit `projects/my-scraper/config.yaml` with your scraping requirements

3. Run your scraper:
```bash
python -m projects.my-scraper.main
```

## Project Structure

```
├── core/                    # Core framework modules
│   ├── __init__.py
│   ├── scraper.py          # AgentQL scraper wrapper
│   ├── analyzer.py         # OpenAI analysis module
│   ├── utils.py            # Utility functions
│   └── data_processor.py   # Data processing utilities
├── projects/               # Your scraping projects go here
│   ├── template/          # Template project structure
│   └── .gitkeep
├── data/                   # Scraped data storage
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md
```

## Creating a New Scraper

1. Copy the template project:
```bash
cp -r projects/template projects/your-project-name
```

2. Update `config.yaml` with your requirements:
```yaml
name: "Your Project Name"
target_urls:
  - "https://example.com"
selectors:
  title: "h1"
  content: "article"
analysis:
  enabled: true
  prompt: "Analyze this data and..."
```

3. Customize the scraping logic in `main.py`

## Examples

Check the `projects/examples/` directory for sample scrapers:
- E-commerce product analysis
- News article summarization
- Job listing aggregator
- Social media sentiment analysis

## Configuration

Each project can have its own `config.yaml` file with:
- Target URLs
- AgentQL selectors
- OpenAI prompts
- Data export settings
- Scheduling options

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License