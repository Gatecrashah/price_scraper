#!/bin/bash
# Commands to restore persistent price history tracking

echo "📊 Restoring persistent price history tracking..."

# 1. Remove price_history.json from .gitignore
echo "🔧 Removing price_history.json from .gitignore..."
if grep -q "price_history.json" .gitignore; then
    sed -i '' '/price_history.json/d' .gitignore
    echo "✅ Removed price_history.json from .gitignore"
else
    echo "ℹ️ price_history.json was not in .gitignore"
fi

# 2. Create initial price history file if it doesn't exist
echo "📝 Creating initial price history file..."
if [ ! -f "price_history.json" ]; then
    echo "{}" > price_history.json
    echo "✅ Created empty price_history.json"
else
    echo "ℹ️ price_history.json already exists"
fi

# 3. Test the scraper to populate initial data
echo "🧪 Running initial scraper test to populate price data..."
uv run --env-file .env python price_monitor.py --test

# 4. Show current price data
echo "📊 Current price history contents:"
if [ -f "price_history.json" ]; then
    echo "File size: $(ls -lh price_history.json | awk '{print $5}')"
    echo "Products tracked: $(cat price_history.json | jq '. | length' 2>/dev/null || echo 'Unknown')"
else
    echo "❌ No price history file found"
fi

# 5. Commit all changes
echo "📤 Committing changes..."
git add .
git commit -m "🔄 Restore persistent price history tracking

- Remove price_history.json from .gitignore 
- Update GitHub Actions to handle Git commits properly
- Add price analysis tool for historical insights
- Enable tracking of pricing trends and seasonal patterns"

echo "🚀 Pushing to GitHub..."
git push

echo ""
echo "🎉 Setup complete! Your price monitoring now includes:"
echo "✅ Persistent price history in Git"
echo "✅ Historical trend analysis"
echo "✅ Seasonal pattern detection"
echo "✅ Best deal tracking"
echo ""
echo "📊 Run 'python price_analyzer.py' to see historical insights!"
echo "🔄 GitHub Actions will now maintain continuous price history"
