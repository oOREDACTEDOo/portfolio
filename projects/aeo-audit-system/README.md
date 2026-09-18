# AEO Audit System

Complete Answer Engine Optimization (AEO) Readiness Audit System that combines DataForSEO APIs, custom scrapers, and AI testing to identify brand visibility gaps.

## 🎯 What This Does

Generates comprehensive AEO audits that show brands their "AI blind spots" by analyzing:

1. **Technical SEO Foundation** - DataForSEO OnPage API
2. **Authority & Backlinks** - DataForSEO Backlinks API
3. **Competitor Intelligence** - DataForSEO Labs API
4. **SERP Features** - DataForSEO SERP API
5. **AI Visibility** - ChatGPT, Gemini, Claude, Perplexity testing
6. **Community Signals** - Reddit mentions & sentiment
7. **Review Authority** - Multi-platform review aggregation
8. **Knowledge Presence** - Wikipedia, Wikidata, Google Knowledge Graph

**Cost per audit:** $1.40-1.60 USD  
**Generation time:** 5-10 minutes

---

## 📁 Project Structure

```
aeo-audit-system/
├── .vscode/                    # VS Code configuration
│   ├── settings.json          # Python, linting, formatting settings
│   └── launch.json            # Debug configurations
├── src/
│   ├── scrapers/              # Data collection modules
│   │   ├── reddit_scraper.py  # Reddit API integration
│   │   ├── review_scraper.py  # Multi-platform review scraping
│   │   └── knowledge_checker.py # Wikipedia/Wikidata/KG
│   ├── api/                   # Flask API for N8N
│   │   └── n8n_api.py        # Main API endpoints
│   ├── core/                  # Business logic
│   │   ├── aggregator.py     # Data aggregation
│   │   ├── analyzer.py       # Claude-powered analysis
│   │   └── report_generator.py # Report creation
│   └── utils/                 # Shared utilities
│       ├── config.py          # Configuration management
│       ├── logger.py          # Logging setup
│       └── validators.py      # Input validation
├── tests/                     # Test suite
│   ├── test_scrapers.py
│   ├── test_api.py
│   └── test_integration.py
├── config/
│   ├── .env.example          # Environment variables template
│   └── subreddits.json       # Industry-specific subreddit lists
├── docs/
│   ├── SETUP.md              # Installation guide
│   ├── API.md                # API documentation
│   └── ARCHITECTURE.md       # System architecture
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## 🚀 Quick Start

### 1. Clone & Setup Virtual Environment

```bash
# Navigate to project
cd aeo-audit-system

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp config/.env.example .env

# Edit .env with your credentials
nano .env  # or use VS Code
```

### 3. Test Individual Scrapers

```bash
# Test Reddit scraper
python src/scrapers/reddit_scraper.py

# Test Review scraper
python src/scrapers/review_scraper.py

# Test Knowledge checker
python src/scrapers/knowledge_checker.py
```

### 4. Start Flask API

```bash
# Run the API server
python src/api/n8n_api.py

# Or use VS Code debugger (F5) and select "Python: Flask API"
```

### 5. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Complete audit
curl -X POST http://localhost:5000/audit/complete \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Lyreco",
    "domain": "lyreco.com",
    "industry": "office supplies",
    "competitors": ["Viking", "Staples"]
  }'
```

---

## 🔧 Development Workflow

### Using VS Code

1. **Open Project:** `File > Open Folder` → Select `aeo-audit-system`
2. **Select Python Interpreter:** `Cmd+Shift+P` → "Python: Select Interpreter" → Choose `venv`
3. **Install Extensions:**
   - Python (Microsoft)
   - Pylance
   - Black Formatter
   - Python Test Explorer

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scrapers.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Debugging

- **Press F5** in VS Code and select configuration:
  - "Python: Flask API" - Run API server
  - "Python: Test Reddit Scraper" - Debug Reddit scraper
  - "Python: Current File" - Debug current open file
  - "Python: Run Tests" - Debug test suite

### Code Formatting

```bash
# Format all Python files
black src/ tests/

# Check linting
pylint src/

# Type checking
mypy src/
```

---

## 📊 API Endpoints

### Health Check
```
GET /health
```

### Complete Audit
```
POST /audit/complete
Body: {
  "brand_name": "string",
  "domain": "string",
  "industry": "string",
  "competitors": ["string"]
}
```

### Individual Scrapers
```
POST /scrape/reddit
POST /scrape/reviews
POST /check/knowledge
```

See [docs/API.md](docs/API.md) for full documentation.

---

## 🔐 Required API Keys

### Essential (Free)
- **Reddit API** - [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
- **Wikipedia/Wikidata** - No key needed (free)

### Optional
- **Google Knowledge Graph** - [console.cloud.google.com](https://console.cloud.google.com/)
- **Anthropic Claude** - [console.anthropic.com](https://console.anthropic.com/)

### External (Your Existing)
- **DataForSEO** - [dataforseo.com](https://dataforseo.com/)
- **OpenAI** (ChatGPT) - [platform.openai.com](https://platform.openai.com/)
- **Perplexity** - [perplexity.ai](https://perplexity.ai/)

---

## 💡 Development Roadmap

### ✅ Phase 1: MVP (Current)
- [x] Reddit scraper
- [x] Review scraper
- [x] Knowledge checker
- [ ] Flask API wrapper
- [ ] Data aggregator
- [ ] Claude analyzer
- [ ] Basic testing

### 🚧 Phase 2: Production Ready
- [ ] Comprehensive error handling
- [ ] Proper logging
- [ ] Rate limiting with backoff
- [ ] Caching layer (Redis)
- [ ] Full test coverage
- [ ] Documentation

### 🔮 Phase 3: Scale
- [ ] Async processing (Celery)
- [ ] Admin dashboard
- [ ] Monitoring (Sentry)
- [ ] Docker deployment
- [ ] Queue-based architecture
- [ ] Advanced analytics

---

## 🐛 Troubleshooting

### Common Issues

**ImportError: No module named 'praw'**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Playwright not installed**
```bash
playwright install chromium
```

**API returns 500 errors**
- Check logs in console
- Verify all environment variables are set
- Ensure API keys are valid

**Reddit scraper fails**
- Verify Reddit API credentials
- Check rate limiting (wait 60 seconds)
- Ensure user agent is set correctly

---

## 📚 Additional Resources

- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [API Documentation](docs/API.md) - Complete API reference
- [Architecture](docs/ARCHITECTURE.md) - System design overview
- [Original Specification](docs/Complete_AEO_Audit_Architecture.pdf)

---

## 🤝 Contributing

This is a private project. For questions or issues, contact the development team.

---

## 📝 License

Proprietary - All rights reserved

---

## 🎯 Next Steps

1. **Read:** [docs/SETUP.md](docs/SETUP.md) for detailed setup
2. **Configure:** Copy `.env.example` and add your API keys
3. **Test:** Run individual scrapers to verify setup
4. **Develop:** Start Flask API and test endpoints
5. **Integrate:** Connect to N8N workflow

**Need help?** Check the [docs/](docs/) folder or review code comments.
