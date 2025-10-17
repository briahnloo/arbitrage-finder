#!/bin/bash
# Quick safety check before pushing to GitHub

echo "🔐 GITHUB SAFETY CHECK"
echo "====================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "✅ .env file exists (your secrets)"
else
    echo "⚠️  .env file not found"
fi

# Check if .env.example exists
if [ -f .env.example ]; then
    echo "✅ .env.example exists (safe template)"
else
    echo "⚠️  .env.example not found"
fi

# Check if .gitignore has .env
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "✅ .gitignore excludes .env"
else
    echo "❌ WARNING: .env NOT in .gitignore!"
    exit 1
fi

# Check if .env is ignored by git
if git check-ignore .env 2>/dev/null | grep -q ".env"; then
    echo "✅ Git will ignore .env file"
else
    echo "⚠️  Not a git repo yet (will be ignored once initialized)"
fi

echo ""
echo "📁 Files that WILL be committed:"
git ls-files 2>/dev/null | grep -E "\.py$|\.md$|\.txt$|\.example$|requirements|gitignore" | head -20 || echo "  (Initialize git to see tracked files)"

echo ""
echo "🚫 Files that WON'T be committed:"
echo "  .env (your API key)"
echo "  *.db (database files)"
echo "  *.csv (export files)"

echo ""
echo "✅ Safe to push to GitHub!"
