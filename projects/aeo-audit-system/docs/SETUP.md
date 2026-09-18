# AEO Audit System - Complete Setup Guide

This guide walks you through setting up the AEO Audit System from scratch in VS Code.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Testing Components](#testing-components)
5. [Running the API](#running-the-api)
6. [N8N Integration](#n8n-integration)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **VS Code** - [Download](https://code.visualstudio.com/)
- **Node.js** (for N8N) - [Download](https://nodejs.org/)

### VS Code Extensions

Install these extensions in VS Code:

1. **Python** (ms-python.python)
2. **Pylance** (ms-python.vscode-pylance)
3. **Black Formatter** (ms-python.black-formatter)
4. **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter)

To install:
1. Press `Cmd+Shift+X` (macOS) or `Ctrl+Shift+X` (Windows/Linux)
2. Search for each extension
3. Click "Install"

---

## Installation

### Step 1: Open Project in VS Code

```bash
# Open VS Code and select:
File > Open Folder > Select "aeo-audit-system" folder
```

### Step 2: Create Virtual Environment

**Option A: Using VS Code Terminal**

```bash
# Open terminal: Ctrl+` (backtick)

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Your prompt should now show (venv)
```

**Option B: Using VS Code Command Palette**

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows)
2. Type: "Python: Create Environment"
3. Select "Venv"
4. Select your Python interpreter

### Step 3: Install Dependencies

```bash
# Ensure virtual environment is activated (you should see (venv) in prompt)

# Install all Python packages
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
playwright install chromium

# Verify installation
python -c "import flask, praw, playwright; print('✅ All packages installed successfully')"
```

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp config/.env.example .env

# Open .env in VS Code
code .env
```

### Step 2: Get API Credentials

#### Reddit API (Required)

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name:** AEO Audit Bot
   - **Type:** Select "script"
   - **Description:** AEO Audit System
   - **Redirect URI:** http://localhost:8080 (not used but required)
4. Click "Create app"
5. Copy your credentials:
   - **Client ID:** The string under "personal use script"
   - **Client Secret:** The "secret" field

Add to `.env`:
```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=AEO_Audit_Bot/1.0_by_YourUsername
```

#### Anthropic Claude API (Recommended)

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key

Add to `.env`:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### Google Knowledge Graph API (Optional)

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Knowledge Graph Search API"
4. Go to "Credentials" > "Create Credentials" > "API Key"
5. Copy the key

Add to `.env`:
```bash
GOOGLE_KG_API_KEY=your_google_kg_api_key_here
```

### Step 3: Verify Configuration

```bash
# Run configuration check
python -c "from src.utils.config import config; config.print_config()"

# You should see a formatted configuration report
# Check that required credentials show as ✅
```

---

## Testing Components

### Test Individual Scrapers

#### 1. Test Reddit Scraper

```bash
# Run the Reddit scraper standalone
python src/scrapers/reddit_scraper.py

# Or use VS Code debugger:
# 1. Open reddit_scraper.py
# 2. Press F5
# 3. Select "Python: Test Reddit Scraper"
```

**Expected Output:**
- Search results for "Lyreco" (or test brand)
- Sentiment analysis
- Engagement metrics
- Visibility scores

#### 2. Test Review Scraper

```bash
# Run the review scraper standalone
python src/scrapers/review_scraper.py

# Or use VS Code debugger:
# F5 > "Python: Test Review Scraper"
```

**Expected Output:**
- Yelp review data
- Trustpilot ratings
- Aggregate metrics

**Note:** Review scraping uses Playwright which may be slower on first run.

#### 3. Test Knowledge Checker

```bash
# Run the knowledge checker standalone
python src/scrapers/knowledge_checker.py

# Or use VS Code debugger:
# F5 > "Python: Test Knowledge Checker"
```

**Expected Output:**
- Wikipedia presence check
- Wikidata entity information
- Google Knowledge Graph data (if API key configured)
- Authority scores

---

## Running the API

### Start Flask Development Server

**Option A: Terminal**

```bash
# Ensure virtual environment is activated
python src/api/n8n_api.py
```

**Option B: VS Code Debugger** (Recommended)

1. Press `F5` in VS Code
2. Select "Python: Flask API"
3. The debugger will start the server

**Expected Output:**
```
🔧 AEO Audit System Configuration
==================================================
📡 API Credentials:
  Reddit Client ID: ✅ abc1...xyz9
  ...
==================================================

INFO - Starting AEO Audit API on 0.0.0.0:5000
INFO - Environment: development
INFO - Debug mode: True
 * Running on http://0.0.0.0:5000
```

### Test API Endpoints

#### Health Check

```bash
# Test health endpoint
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "service": "aeo-audit-api",
  "version": "1.0.0",
  "environment": "development"
}
```

#### Test Reddit Endpoint

```bash
curl -X POST http://localhost:5000/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Lyreco",
    "subreddits": ["smallbusiness", "office"],
    "days_back": 90
  }'
```

#### Test Complete Audit

```bash
curl -X POST http://localhost:5000/audit/complete \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Lyreco",
    "domain": "lyreco.com",
    "industry": "office supplies",
    "competitors": ["Viking", "Staples"]
  }'
```

**Note:** This will take 5-10 minutes to complete as it runs all scrapers.

---

## N8N Integration

### Install N8N

```bash
# Install N8N globally
npm install -g n8n

# Start N8N
n8n start

# Access at http://localhost:5678
```

### Configure N8N Workflow

#### 1. Create New Workflow

1. Open N8N at `http://localhost:5678`
2. Click "New Workflow"
3. Name it "AEO Audit Pipeline"

#### 2. Add Webhook Trigger

1. Add node: "Webhook"
2. Configure:
   - **Method:** POST
   - **Path:** `aeo-audit-trigger`
3. Save

#### 3. Add HTTP Request Nodes

**Node 1: Reddit Scraping**

```
Add Node > HTTP Request
Name: Scrape Reddit
Method: POST
URL: http://localhost:5000/scrape/reddit
Body:
{
  "brand_name": "{{ $json.brand_name }}",
  "subreddits": {{ $json.subreddits }},
  "days_back": 180
}
Headers:
  Content-Type: application/json
```

**Node 2: Review Scraping**

```
Add Node > HTTP Request (parallel to Node 1)
Name: Scrape Reviews
Method: POST
URL: http://localhost:5000/scrape/reviews
Body:
{
  "business_name": "{{ $json.brand_name }}",
  "domain": "{{ $json.domain }}"
}
```

**Node 3: Knowledge Check**

```
Add Node > HTTP Request (parallel to Node 1 & 2)
Name: Check Knowledge
Method: POST
URL: http://localhost:5000/check/knowledge
Body:
{
  "brand_name": "{{ $json.brand_name }}"
}
```

#### 4. Merge Data

1. Add node: "Merge" 
2. Mode: "Combine"
3. Connect all three HTTP Request nodes to Merge node

#### 5. Test Workflow

1. Click "Execute Workflow"
2. Send test data to webhook:

```bash
curl -X POST http://localhost:5678/webhook/aeo-audit-trigger \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Lyreco",
    "domain": "lyreco.com",
    "subreddits": ["smallbusiness", "office"],
    "industry": "office supplies"
  }'
```

---

## Troubleshooting

### Common Issues

#### ImportError: No module named 'X'

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Playwright not installed

**Error:** `Executable doesn't exist at /path/to/chromium`

**Solution:**
```bash
playwright install chromium
```

#### Reddit API: 401 Unauthorized

**Error:** `401 Unauthorized` when testing Reddit scraper

**Solutions:**
1. Verify credentials in `.env` file
2. Check Reddit app type is "script"
3. Ensure no extra spaces in credentials
4. Generate new credentials at reddit.com/prefs/apps

#### Flask port already in use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change port in .env
FLASK_PORT=5001
```

#### Scraper timeout errors

**Error:** `Timeout waiting for page to load`

**Solutions:**
1. Check internet connection
2. Increase timeout in scraper configuration
3. Try different times (avoid peak hours)
4. Check if target site is blocking scraping

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
FLASK_DEBUG=True
```

Then check logs:
```bash
tail -f logs/aeo-audit.log
```

### Skip Components During Development

To speed up testing, skip certain components:

```bash
# In .env
SKIP_REDDIT=True
SKIP_REVIEWS=True
SKIP_KNOWLEDGE=False
```

---

## Next Steps

1. ✅ **Test all scrapers individually**
2. ✅ **Start Flask API and test endpoints**
3. ✅ **Set up N8N workflow**
4. 📋 **Integrate DataForSEO APIs** (see docs/DATAFORSEO.md)
5. 📋 **Add Claude analysis module** (see docs/CLAUDE_ANALYSIS.md)
6. 📋 **Set up report generation** (see docs/REPORTS.md)

---

## Getting Help

### Logs Location

- **Application logs:** `logs/aeo-audit.log`
- **Flask logs:** Console output when running API

### Configuration Check

```bash
# Print current configuration
python -c "from src.utils.config import config; config.print_config()"
```

### Status Endpoint

```bash
# Check API status
curl http://localhost:5000/status
```

---

## Development Workflow

### Recommended VS Code Setup

1. **Open Terminal:** `Ctrl+\`` (backtick)
2. **Activate venv:** `source venv/bin/activate`
3. **Start API:** `F5` > "Python: Flask API"
4. **Test in browser:** Open `http://localhost:5000/health`
5. **View logs:** Terminal shows colorized logs
6. **Debug breakpoints:** Click left of line numbers to add breakpoints

### Testing Cycle

1. Make code changes
2. Save file (API auto-reloads with Flask debug mode)
3. Test endpoint with curl or browser
4. Check logs in terminal
5. Iterate

---

## Production Deployment

For production deployment, see:
- [docs/DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [docs/DOCKER.md](DOCKER.md) - Docker containerization
- [docs/SCALING.md](SCALING.md) - Scaling strategies

---

**🎉 Congratulations!** You now have a fully functional AEO Audit System running locally.
