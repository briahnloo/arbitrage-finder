# Sports Betting Arbitrage Alert System MVP

A Python-based system that monitors real-time tennis odds from multiple sportsbooks and identifies arbitrage betting opportunities with guaranteed profit potential.

## What is Arbitrage Betting?

Arbitrage betting is a strategy where you place bets on all possible outcomes of a sports event at different sportsbooks to lock in a guaranteed profit. This system focuses on tennis (two-outcome events) where you can bet on both players across different bookmakers to ensure profit regardless of the match outcome.

**Example**: If Bookmaker A offers odds of 2.10 on Player X and Bookmaker B offers 2.05 on Player Y, the combined implied probability is ~95.2% (under 100%), creating a ~4.8% profit opportunity.

## Features

- **Real-time Odds Monitoring**: Fetches live odds from The Odds API every 15 minutes
- **Multi-Sport Coverage**: Monitors both ATP (men's) and WTA (women's) tennis matches
- **Smart Filtering**: Only alerts on opportunities with >1% profit margin
- **Stake Calculations**: Automatically calculates optimal bet distribution for $100 investment
- **Console Alerts**: Clean, formatted output with all necessary betting information
- **Duplicate Prevention**: Tracks recent opportunities to avoid alert spam

## Requirements

- Python 3.7 or higher
- Free API key from [The Odds API](https://the-odds-api.com/)
- macOS, Linux, or Windows

## Setup Instructions

### 1. Get Your Free API Key

1. Visit [The Odds API](https://the-odds-api.com/)
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Free tier includes 500 API calls per month

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install packages individually:
```bash
pip install requests python-dotenv schedule
```

### 3. Configure API Key

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```
ODDS_API_KEY=your_actual_api_key_here
```

## Usage

Run the arbitrage finder:

```bash
python arbitrage_finder.py
```

The system will:
1. Start monitoring tennis matches immediately
2. Check for new odds every 15 minutes
3. Display arbitrage opportunities in the console when found
4. Run continuously until you stop it (Ctrl+C)

### Sample Output

```
================================================================================
🎾 ARBITRAGE OPPORTUNITY FOUND! 🎾
================================================================================
Match: Novak Djokovic vs Carlos Alcaraz
Event Time: 2025-10-20 15:00:00 UTC
Sport: ATP Tennis

Profit Margin: 2.34%

BET 1:
  Player: Novak Djokovic
  Bookmaker: FanDuel
  Odds: 2.10
  Stake: $49.28

BET 2:
  Player: Carlos Alcaraz
  Bookmaker: DraftKings
  Odds: 2.05
  Stake: $50.72

TOTAL INVESTMENT: $100.00
GUARANTEED PROFIT: $2.34
================================================================================
```

## Understanding the Output

Each alert provides:
- **Match Details**: Players and start time
- **Profit Margin**: The percentage profit you'll make
- **Bet Instructions**: For each side:
  - Which player to bet on
  - Which sportsbook to use
  - The decimal odds
  - Exact amount to wager
- **Profit Amount**: Expected profit in dollars

## Important Notes

### API Usage Limits
- Free tier: 500 calls/month (~16 per day)
- This system uses ~96 calls/day (monitoring both ATP and WTA)
- For extended use, consider upgrading API plan or reducing check frequency

### Legal Considerations
- This tool only finds opportunities; it does NOT place bets automatically
- Sports betting is only legal in certain US states
- You must be physically located in a legal betting state to place wagers
- Ensure you comply with all local laws and regulations

### Betting Execution
- Act quickly when you receive an alert (odds can change)
- Have accounts funded at multiple sportsbooks
- Manually log in and place both bets as instructed
- Some bookmakers may limit accounts that consistently arbitrage

### Risk Factors
While arbitrage betting is low-risk, be aware:
- Odds can change between alert and bet placement
- Bookmakers may void bets if they detect a pricing error
- Account limitations possible if detected as an arbitrage bettor
- Requires sufficient bankroll across multiple sportsbooks

## Configuration

Edit `config.py` to adjust:
- `MINIMUM_PROFIT_THRESHOLD`: Minimum profit % to trigger alerts (default: 1.0%)
- `DEFAULT_STAKE`: Total investment amount for calculations (default: $100)
- `CHECK_INTERVAL_MINUTES`: How often to check for new odds (default: 15 minutes)

## Troubleshooting

**"Invalid API key" error**:
- Verify your API key is correct in `.env`
- Ensure no extra spaces or quotes around the key

**No opportunities found**:
- This is normal; arbitrage opportunities are rare
- The system will continue monitoring automatically
- Try running during peak betting hours

**Rate limit exceeded**:
- You've used your monthly API quota
- Wait for the next month or upgrade your API plan
- Reduce check frequency if needed

## Future Enhancements

Potential improvements for future versions:
- Add more sports (soccer, basketball, etc.)
- Email/SMS notifications instead of console only
- Web dashboard for monitoring
- Historical opportunity tracking
- Multiple betting markets (spreads, totals)
- Automated bet placement (complex, requires careful implementation)

## Disclaimer

This software is for educational and informational purposes only. Users are responsible for:
- Complying with all applicable laws and regulations
- Understanding the risks of sports betting
- Managing their own betting accounts and bankroll
- Any financial gains or losses incurred

The developers assume no liability for any losses or legal issues arising from use of this software.

## License

MIT License - Feel free to modify and use as needed.

