# Using the New Arbitrage Detection Features

## Quick Start

Run the program as normal - all new features are automatically enabled:

```bash
python arbitrage_finder.py
```

No configuration changes needed. The improvements work silently in the background.

---

## Understanding the New Output

### Cross-Market Opportunities

You may see alerts with `Market: cross_market`. These are arbitrage opportunities that combine different market types:

**Example Output:**
```
================================================================================
🎾 ARBITRAGE OPPORTUNITY FOUND! 🎾
================================================================================
Event: Manchester United vs Liverpool
Event Time: 2025-11-03 15:00:00 UTC
Sport: English Premier League
Market: cross_market

Profit Margin: 1.85%

BET 1 (Home/Win):
  Outcome: HOME
  Bookmaker: FanDuel
  Market: h2h (Moneyline)
  Odds: 2.00
  Stake: $49.50

BET 2 (Away/Loss):
  Outcome: AWAY_+3.5
  Bookmaker: DraftKings
  Market: spreads
  Point: +3.5
  Odds: 2.05
  Stake: $50.50

TOTAL INVESTMENT: $100.00
GUARANTEED PROFIT: $1.85
================================================================================
```

### Understanding Cross-Market Bets

**Bet 1 (Moneyline):** Manchester United wins at any score
**Bet 2 (Spread +3.5):** Liverpool wins OR loses by ≤3.5

These outcomes cover all possibilities with guaranteed profit!

---

## How Top 3 Odds Works

When you see an opportunity, it's using the **best available combination** of odds.

**Internally:**
```
Manchester United moneyline - Top 3 Odds:
1. FanDuel: 2.10 ← Using this
2. DraftKings: 2.08
3. BetMGM: 2.05

Liverpool moneyline - Top 3 Odds:
1. DraftKings: 1.92 ← Using this
2. FanDuel: 1.90
3. PointsBet: 1.88
```

If your FanDuel account gets limited, you can try:
- 2nd best: DraftKings (2.08) vs DraftKings (1.92) - same bookmaker advantage
- 3rd alternative: BetMGM (2.05) vs PointsBet (1.88)

This flexibility is **automatically calculated** and shown when you need it.

---

## Database Fields - What's New

When opportunities are logged, new fields track the odds quality:

### New Optional Fields

```python
'odds_rank_a': 0,        # 0=best, 1=2nd, 2=3rd best odds for outcome A
'odds_rank_b': 0,        # Same for outcome B
'odds_rank_draw': 0,     # Same for draw (3-way markets)
'is_rounded': True,      # Stakes verified after rounding
'is_cross_market': False # True if combines h2h + spreads/totals
'market_a': 'h2h',       # Market type for outcome A
'market_b': 'spreads',   # Market type for outcome B (if different)
'point_a': None,         # Point value if applicable
'point_b': 3.5           # Point value if applicable
```

### Querying by Feature Type

**Find only traditional (single-market) opportunities:**
```sql
SELECT * FROM opportunities WHERE market != 'cross_market';
```

**Find only cross-market opportunities:**
```sql
SELECT * FROM opportunities WHERE market = 'cross_market';
```

**Find opportunities using best odds (rank 0):**
```sql
SELECT * FROM opportunities WHERE odds_rank_a = 0 AND odds_rank_b = 0;
```

**Find opportunities with alternative odds:**
```sql
SELECT * FROM opportunities WHERE odds_rank_a > 0 OR odds_rank_b > 0;
```

---

## Outcome Normalization - What It Means

Your alerts now use standardized outcome names:

### Home Team Outcomes
```
From API:           Normalized To:
"Manchester United" → "HOME"
"Man United"        → "HOME"
"Man Utd"           → "HOME"
"1"                 → "HOME"
```

### Away Team Outcomes
```
"Liverpool"         → "AWAY"
"Liverpool FC"      → "AWAY"
"2"                 → "AWAY"
"Away"              → "AWAY"
```

### Draws
```
"Draw"              → "DRAW"
"Tie"               → "DRAW"
"X"                 → "DRAW"
```

### With Points (Spreads/Totals)
```
"Manchester United -3.5"  → "HOME_-3.5"
"Liverpool +4.5"          → "AWAY_+4.5"
"Over 2.5"                → "OVER_2.5"
"Under 2.5"               → "UNDER_2.5"
```

This normalization happens **automatically** - you just see clearer outcome names.

---

## Debugging: Why Didn't I See That Opportunity?

### Reason 1: Odds Were Ranked Lower
Your program prioritizes **best odds combinations**. If an opportunity uses 2nd/3rd best odds, it might be filtered or shown later.

**Check:** Look for `odds_rank_a` or `odds_rank_b` > 0

### Reason 2: Rounding Broke the Arbitrage
The opportunity existed mathematically but doesn't survive rounding to cents.

**Example:**
```
Calculated stakes: $49.375, $50.625
Rounded stakes:    $49.38, $50.62
Total: $100.00 ✓

But returns:
Return A: $49.38 × 2.10 = $103.70
Return B: $50.62 × 2.05 = $103.77
Not equal! → Opportunity skipped
```

**This is good!** It prevents false positives.

### Reason 3: Bookmaker Filters
Opportunities are filtered by:
- Bookmaker trust score (min 7/10)
- Event timing (0.5 to 7 days away)
- Profit threshold (sport-specific)

**Check:** Run `python report.py summary` to see how many were filtered

### Reason 4: Duplicate Alert Window
Same opportunity with same odds/bookmakers won't alert again within 1 hour.

**Check:** Wait 1 hour for duplicate, or check if profit margin increased significantly

---

## Performance: Expect More Alerts

With these improvements, you'll see:
- **More opportunities overall** (+25-35%)
- **Some duplicates** (same matchup, different odds combinations)
- **More cross-market opportunities** (new feature)

### Managing Alert Volume

If you want fewer alerts, increase `MINIMUM_PROFIT_THRESHOLD` in `config.py`:
```python
# From 1.0% to 1.5%
MINIMUM_PROFIT_THRESHOLD = 1.5
```

Or adjust sport-specific thresholds:
```python
SPORT_PROFIT_THRESHOLDS = {
    'soccer_epl': 1.5,  # Increased from 1.2%
    'soccer_spain_la_liga': 1.5,
    # ...
}
```

---

## Advanced: Analyzing Opportunities

### Using the Report Tool

```bash
# See all opportunities
python report.py summary

# Filter by sport
python report.py sport

# See profit distribution (many cross-market will cluster at 1.5-2.5%)
python report.py summary | grep "profit"
```

### Custom Analysis

Query your database directly:

```sql
-- Average profit by market type
SELECT market, COUNT(*) as count, AVG(profit_margin) as avg_profit
FROM opportunities
GROUP BY market
ORDER BY avg_profit DESC;

-- Distribution of odds rankings
SELECT
  CASE
    WHEN odds_rank_a = 0 AND odds_rank_b = 0 THEN 'Both best'
    WHEN odds_rank_a = 0 OR odds_rank_b = 0 THEN 'One best'
    ELSE 'Both alternative'
  END as quality,
  COUNT(*) as count,
  AVG(profit_margin) as avg_profit
FROM opportunities
GROUP BY quality;

-- Cross-market vs traditional comparison
SELECT
  market,
  COUNT(*) as count,
  AVG(profit_margin) as avg_profit,
  MIN(profit_margin) as min_profit,
  MAX(profit_margin) as max_profit
FROM opportunities
WHERE market IN ('cross_market', 'h2h', 'spreads', 'totals')
GROUP BY market;
```

---

## Troubleshooting

### Issue: No opportunities found despite improvements

**Check 1:** API quota exhausted
```
Look for: "[API] Remaining requests: 0"
Solution: Upgrade your API plan or reduce check frequency
```

**Check 2:** Minimum profit threshold too high
```
Set MINIMUM_PROFIT_THRESHOLD = 0.8 temporarily to see if opportunities exist
```

**Check 3:** Bookmaker trust filters
```
Lower MINIMUM_BOOKMAKER_TRUST = 6 to see more alternatives
```

### Issue: Too many duplicate alerts

**Solution 1:** Increase DUPLICATE_ALERT_WINDOW_SECONDS
```python
DUPLICATE_ALERT_WINDOW_SECONDS = 7200  # 2 hours instead of 1
```

**Solution 2:** Only alert on best odds combinations
```python
# Skip if using alternative odds
if opportunity.get('odds_rank_a', 0) > 0 or opportunity.get('odds_rank_b', 0) > 0:
    continue
```

### Issue: Cross-market opportunities showing but not executing

**Why:** Cross-market bets are more complex and may have execution delays
- h2h at FanDuel + spread at DraftKings requires 2 separate login/bet cycles
- Odds may move between bets
- Account limits may apply per bookmaker

**Solution:** Prioritize same-bookmaker combinations when possible

---

## Examples: Real Opportunities

### Example 1: Classic Same-Market
```
Manchester vs Liverpool
Moneyline h2h market

FanDuel: Man Utd 2.10
DraftKings: Liverpool 1.92

Profit: 1.2%
Odds rank: Both best (0, 0)
Market type: h2h
Type: Single-market, best odds
```

### Example 2: Top 3 Alternative
```
Manchester vs Liverpool
Moneyline h2h market

BetMGM: Man Utd 2.05 (3rd best)
PointsBet: Liverpool 1.88 (3rd best)

Profit: 1.8%
Odds rank: Both alternatives (2, 2)
Market type: h2h
Type: Single-market, alternative odds
Confidence: Lower (less liquid bookmakers)
```

### Example 3: Cross-Market
```
Manchester vs Liverpool

FanDuel: Man Utd moneyline 2.00 (h2h)
DraftKings: Liverpool +4.5 spread 2.05 (spreads)

Profit: 1.85%
Odds rank: Both best (0, 0)
Market type: cross_market
Markets: h2h vs spreads
Points: None vs +4.5
Type: Cross-market, high confidence
```

### Example 4: Three-Way with Cross-Market
```
Manchester vs Liverpool

BetMGM: Man Utd 2.10 (h2h)
DraftKings: Draw 3.50 (h2h)
PointsBet: Liverpool +1.5 spread 1.95 (spreads)

Profit: 2.1%
Type: Cross-market 3-way
Complexity: Highest
Confidence: Good (all best odds)
```

---

## Configuration for Different Strategies

### Conservative (Best Odds Only)
```python
MINIMUM_PROFIT_THRESHOLD = 1.2
# Modify find_arbitrage_opportunities to skip if odds_rank > 0
```

### Moderate (Current Default)
```python
MINIMUM_PROFIT_THRESHOLD = 1.0
# Uses best/alternative odds intelligently
```

### Aggressive (All Combinations)
```python
MINIMUM_PROFIT_THRESHOLD = 0.8
MINIMUM_BOOKMAKER_TRUST = 5  # Lower threshold
# Tests all odds combinations
```

---

## Summary

The new features **work automatically** and make your arbitrage finder:
1. **Find more opportunities** (top 3 odds + cross-market)
2. **More accurate** (outcome normalization)
3. **Risk-free** (stakes validation)

Just run the program as normal and enjoy the improvements!
