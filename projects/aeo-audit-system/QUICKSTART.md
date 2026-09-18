# 🚀 Quick Start Guide

Get the AEO Audit System running in 15 minutes.

---

## 5-Step Setup

### 1️⃣ Open in VS Code (30 seconds)

```bash
# Open VS Code
File > Open Folder > Select "aeo-audit-system"
```

### 2️⃣ Create Virtual Environment (1 minute)

```bash
# In VS Code terminal (Ctrl+`)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 3️⃣ Install Dependencies (3-5 minutes)

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4️⃣ Configure Environment (2 minutes)

```bash
# Copy template
cp config/.env.example .env

# Edit .env and add your Reddit credentials:
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
```

**Get Reddit credentials:**
1. Visit [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click "Create App"
3. Select "script" type
4. Copy Client ID and Secret

### 5️⃣ Start the API (10 seconds)

```bash
# Press F5 in VS Code
# Select: "Python: Flask API"

# Or in terminal:
python src/api/n8n_api.py
```

---

## Quick Tests

### Test Health Check
```bash
curl http://localhost:5000/health
```

### Test Reddit Scraper
```bash
curl -X POST http://localhost:5000/scrape/reddit \
  -H "Content-Type: application/json" \
  -d '{"brand_name": "Lyreco", "subreddits": ["smallbusiness"]}'
```

### Test Complete Audit
```bash
curl -X POST http://localhost:5000/audit/complete \
  -H "Content-Type: application/json" \
  -d '{"brand_name": "Lyreco", "domain": "lyreco.com"}'
```

---

## File Structure

```
aeo-audit-system/
├── src/
│   ├── api/n8n_api.py          ← Main Flask API
│   ├── scrapers/               ← Data collection
│   │   ├── reddit_scraper.py
│   │   ├── review_scraper.py
│   │   └── knowledge_checker.py
│   └── utils/                  ← Config & helpers
├── docs/SETUP.md               ← Full setup guide
└── .env                        ← Your credentials (create this!)
```

---

## Common Issues

**"No module named 'praw'"**
```bash
source venv/bin/activate  # Activate venv first!
pip install -r requirements.txt
```

**"Playwright not installed"**
```bash
playwright install chromium
```

**"Reddit 401 Error"**
- Check `.env` has correct credentials
- No extra spaces in credentials
- Reddit app type must be "script"

---

## VS Code Tips

### Debug Configurations (F5)
- **"Python: Flask API"** - Run API server
- **"Python: Current File"** - Run any .py file
- **"Python: Test Reddit Scraper"** - Test Reddit scraper

### Shortcuts
- `Ctrl+\`` - Open terminal
- `F5` - Start debugging
- `Cmd+Shift+P` - Command palette
- `Ctrl+C` (in terminal) - Stop server

### Extensions to Install
1. Python (ms-python.python)
2. Pylance
3. Black Formatter

---

## Next Steps

✅ **You're running!** Now:

1. **Read full setup:** [docs/SETUP.md](docs/SETUP.md)
2. **Review architecture:** [docs/PROJECT_ANALYSIS.md](docs/PROJECT_ANALYSIS.md)
3. **Test scrapers individually:** Run each .py file in `src/scrapers/`
4. **Integrate with N8N:** See [docs/SETUP.md#n8n-integration](docs/SETUP.md#n8n-integration)
5. **Add DataForSEO:** Configure DataForSEO APIs
6. **Add Claude analysis:** Implement report generation

---

## Getting Help

- **Configuration issues?** Run: `python -c "from src.utils.config import config; config.print_config()"`
- **API not working?** Check logs in terminal
- **Need details?** See [docs/SETUP.md](docs/SETUP.md)

---

**Happy coding! 🎉**
