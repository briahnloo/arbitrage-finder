# 🔐 Secrets Management Guide

This guide explains how to safely manage API keys and other secrets in this project.

---

## 🛡️ Security Setup (Already Configured!)

Your project is **already secure** and ready for GitHub. Here's what's protecting your secrets:

### 1. `.env` File (Your Actual Secrets)
- **Location**: `/Arbitrage Finder/.env`
- **Contains**: Your real API key
- **Status**: ✅ **Protected by .gitignore** (won't be pushed to GitHub)

### 2. `.env.example` File (Public Template)
- **Location**: `/Arbitrage Finder/.env.example`
- **Contains**: Template with placeholder text
- **Status**: ✅ **Safe to commit** (no real secrets)

### 3. `.gitignore` File
- **Excludes from Git**:
  - `.env` (your secrets)
  - `*.db` (database files)
  - `*.csv` (export files)
  - `__pycache__/` (Python cache)

---

## ✅ Verification Checklist

Before pushing to GitHub, verify:

```bash
# 1. Check that .env is ignored
git status
# Should NOT show .env in untracked files

# 2. Check what will be committed
git add .
git status
# Should show .env.example but NOT .env

# 3. Double check .gitignore
cat .gitignore | grep .env
# Should show: .env
```

---

## 🚀 How to Share This Project

When someone clones your repository, they should:

### Step 1: Clone the repo
```bash
git clone https://github.com/your-username/arbitrage-finder.git
cd arbitrage-finder
```

### Step 2: Create their own `.env` file
```bash
cp .env.example .env
```

### Step 3: Add their API key
Edit `.env` and replace `your_api_key_here` with their actual key:
```
ODDS_API_KEY=abc123def456real789key
```

### Step 4: Install and run
```bash
pip install -r requirements.txt
python arbitrage_finder.py
```

---

## 🔍 What's Safe to Commit?

### ✅ SAFE (commit these):
- `.env.example` - Template with no real secrets
- `.gitignore` - Tells Git what to ignore
- `config.py` - Loads from .env, doesn't contain secrets
- `README.md` - Documentation
- All `.py` files - Code only, no secrets

### ❌ NEVER COMMIT:
- `.env` - Contains your real API key
- `*.db` - Database with your betting history
- `arbitrage_*.csv` - Export files with your data

---

## 🆘 Emergency: "I Accidentally Committed My .env!"

If you accidentally commit secrets:

### Quick Fix (before pushing):
```bash
# Remove from staging
git reset HEAD .env

# Remove from last commit
git reset --soft HEAD~1
```

### If Already Pushed to GitHub:
1. **Immediately revoke the API key** at https://the-odds-api.com/
2. Get a new API key
3. Update your local `.env` with the new key
4. Remove from Git history:
```bash
# Remove file from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (careful!)
git push origin --force --all
```

---

## 📝 Adding New Secrets

When you add new secrets (e.g., Telegram bot token):

### 1. Add to `.env` (your real secrets):
```bash
ODDS_API_KEY=your_real_api_key
TELEGRAM_BOT_TOKEN=your_real_telegram_token
```

### 2. Add template to `.env.example`:
```bash
ODDS_API_KEY=your_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### 3. Use in code:
```python
import os
from dotenv import load_dotenv

load_dotenv()
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
```

---

## 🔐 Best Practices

1. **Never hardcode secrets** in Python files
2. **Always use environment variables** via `.env`
3. **Check `.gitignore`** before committing
4. **Use `.env.example`** as a template for others
5. **Rotate API keys** periodically
6. **Use different keys** for development vs production
7. **Document required secrets** in README

---

## 🧪 Test Your Security

Run this command to check if secrets are exposed:

```bash
# Search for potential secrets in tracked files
git ls-files | xargs grep -l "ODDS_API_KEY"

# Should only show:
# - .env.example (template)
# - config.py (loads from env)
# - SECRETS_MANAGEMENT.md (this file)

# Should NOT show:
# - .env (your real secrets)
```

---

## ✨ You're All Set!

Your project is configured to:
- ✅ Keep secrets secure
- ✅ Work with Git/GitHub
- ✅ Be easily shared with others
- ✅ Follow security best practices

**You can now safely push to GitHub!** 🚀

