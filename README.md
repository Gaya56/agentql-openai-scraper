# AgentQL + AI Web Scraping Framework

An intelligent web scraping framework that combines **AgentQL**, **OpenAI**, and **Ollama** to create a complete data extraction and analysis pipeline. This framework supports both cloud-based and privacy-first local AI analysis modes.

## 🎯 Purpose & Workflow

This framework creates an end-to-end intelligent scraping pipeline:

1. **🔍 Smart Scraping** → AgentQL uses natural language selectors to extract data
2. **💾 Data Storage** → Structured storage with SQLite database and multiple export formats
3. **🤖 AI Analysis** → Choose between OpenAI (cloud) or Ollama (local) for data analysis
4. **📊 Insights Generation** → Generate actionable insights and recommendations
5. **🔌 Agent Integration** → MCP server enables AI agents to access scraping tools

## 🏗️ Architecture

### Core Components
- **AgentQLScraper**: Natural language web scraping with Playwright
- **OpenAIAnalyzer**: Cloud-based AI analysis and processing
- **OllamaAnalyzer**: Local LLM analysis for privacy-aware processing
- **ScrapingWorkflowController**: Unified workflow orchestrator
- **AgentQLMCPServer**: Model Context Protocol server for AI agent integration
- **DataProcessor**: Multi-format data export and transformation

### Operational Modes
- **🌩️ Cloud Mode**: OpenAI-powered analysis (high accuracy, requires API)
- **🏠 Local Mode**: Ollama-powered analysis (privacy-first, offline capable)
- **🔄 Hybrid Mode**: Combines both for comprehensive analysis

## ✨ Key Features

- 🔍 **Natural Language Scraping** - Use human-readable selectors like "main heading" or "product price"
- 🤖 **Dual AI Analysis** - Choose between cloud (OpenAI) or local (Ollama) AI processing
- � **Multi-Format Export** - JSON, CSV, Excel output with timestamps
- 🔄 **Batch Processing** - Scrape multiple URLs with concurrent processing
- 🎯 **Template System** - Reusable project templates for different scraping tasks
- � **MCP Integration** - AI agents can use scraping tools via Model Context Protocol
- � **Workflow Tracking** - Complete session history and status monitoring
- 🔒 **Privacy Options** - Local analysis mode keeps data on your machine

## Prerequisites

- Python 3.8 or higher
- **Required**: AgentQL API key
- **Optional**: OpenAI API key (for cloud analysis)
- **Optional**: Ollama installation (for local analysis)

## Installation

### Quick Setup

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

### Optional: Local AI Setup (Ollama)

For privacy-first local analysis:

```bash
# Install Ollama (see https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2
```

## Quick Start

### Method 1: Template-Based Projects

1. Create a new project in the `projects/` directory:

```bash
cp -r projects/template projects/my-scraper
```

2. Edit `projects/my-scraper/config.yaml` with your scraping requirements

3. Run your scraper:

```bash
python -m projects.my-scraper.main
```

### Method 2: Direct Workflow Controller

```python
import asyncio
from core import create_hybrid_controller

async def main():
    # Create controller (hybrid mode uses both OpenAI and Ollama)
    controller = create_hybrid_controller()
    await controller.initialize()
    
    # Scrape and analyze
    result = await controller.scrape_and_analyze(
        url="https://example.com",
        query="main heading and all paragraph text",
        analysis_prompt="Summarize the key points and extract main topics"
    )
    
    print(result)

asyncio.run(main())
```

### Method 3: MCP Server for AI Agents

Start the MCP server to enable AI agents to use scraping tools:

```bash
python -m core.mcp_server --port 8000
```

Then AI agents can call scraping functions via the MCP protocol.

## Project Structure

```
├── core/                    # Core framework modules
│   ├── __init__.py         # Module exports and optional imports
│   ├── scraper.py          # AgentQL scraper wrapper
│   ├── analyzer.py         # OpenAI analysis module
│   ├── ollama_analyzer.py  # Local Ollama LLM integration
│   ├── controller.py       # Unified workflow controller
│   ├── mcp_server.py       # Model Context Protocol server
│   ├── data_processor.py   # Data processing utilities
│   └── utils.py            # Utility functions
├── projects/               # Your scraping projects
│   ├── template/          # Template project structure
│   └── examples/          # Example implementations
├── data/                   # Scraped data storage
├── logs/                   # Application logs
├── integration-staging/    # Development integration files
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md
```

## Creating a New Scraper

### Template Method

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
  title: "main heading"
  content: "article body text"
analysis:
  enabled: true
  prompt: "Analyze this data and..."
```

3. Customize the scraping logic in `main.py`

### Direct Controller Usage

```python
from core import create_local_controller, create_cloud_controller, create_hybrid_controller

# Local-only (Ollama)
controller = create_local_controller()

# Cloud-only (OpenAI) 
controller = create_cloud_controller()

# Hybrid (both)
controller = create_hybrid_controller()
```

## Examples & Use Cases

- **E-commerce Analysis**: Product prices, reviews, specifications
- **News Monitoring**: Article summarization, sentiment analysis
- **Job Market Research**: Listing aggregation and trend analysis
- **Social Media Intelligence**: Content analysis and engagement metrics
- **Competitive Intelligence**: Market research and competitor monitoring

## Configuration

### Environment Variables (.env)

```bash
# Required for scraping
AGENTQL_API_KEY=your-agentql-api-key-here

# For OpenAI cloud analysis
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# For local Ollama analysis
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# MCP Server settings
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=127.0.0.1
```

### Project Configuration

Each project has its own `config.yaml` file with:

- **Target URLs**: Websites to scrape
- **AgentQL Selectors**: Natural language element queries
- **Analysis Prompts**: AI analysis instructions
- **Data Export Settings**: Output formats and options
- **Advanced Options**: Browser settings, timeouts, delays

## Advanced Features

### Batch Processing

```python
urls_and_queries = [
    {"url": "https://site1.com", "query": "product details"},
    {"url": "https://site2.com", "query": "article content"},
]

results = await controller.batch_scrape_and_analyze(
    urls_and_queries, 
    "Compare and analyze the content",
    max_concurrent=3
)
```

### AI Analysis Comparison

```python
# Compare local vs cloud analysis
ollama_result = await ollama_analyzer.analyze(data, prompt)
openai_result = openai_analyzer.analyze(data, prompt)

comparison = await ollama_analyzer.compare_with_openai(
    data, prompt, openai_analyzer
)
```

### MCP Server Integration

The framework exposes scraping capabilities as MCP tools:

- `scrape_url`: Single URL scraping
- `scrape_multiple`: Batch URL scraping  
- `get_scraping_history`: Session history
- `get_session_data`: Retrieve stored data

## Testing & Status

**Framework Status**: ✅ **FUNCTIONAL** (88.9% test success rate)

**Working Components**:

- ✅ Core web scraping (AgentQL + Playwright)
- ✅ Data processing and export (JSON, CSV, Excel)  
- ✅ AI analysis integration (OpenAI ready, Ollama capable)
- ✅ Project template system
- ✅ Workflow orchestration
- ✅ Error handling and logging

**Optional Components**:

- ⚠️ MCP server (requires `fastmcp` installation)
- ⚠️ Ollama integration (requires local Ollama setup)

Run tests: `python test_workflow_pipeline.py`

## Contributing

Feel free to submit issues and enhancement requests! Areas for contribution:

- Additional analyzer integrations (Anthropic Claude, etc.)
- New project templates and examples
- Enhanced data processing capabilities
- Performance optimizations

## License

MIT License