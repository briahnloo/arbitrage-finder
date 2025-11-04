# Discord Integration Guide - Arbitrage Finder Premium Service

This guide explains how to integrate the Discord bot with the existing `arbitrage_finder.py` application to send real-time alerts to Discord subscribers.

## Overview

The Discord integration consists of:

1. **discord_bot.py** - Main bot with slash commands
2. **discord_integration.py** - Integration manager connecting bot to arbitrage finder
3. **discord_notifier.py** - Handles formatted messages to Discord
4. **subscription_manager.py** - Manages user subscriptions
5. **user_manager.py** - Manages Discord user access control
6. **payment_handler.py** - Handles Stripe payments

## Architecture

```
┌─────────────────────────────────┐
│   arbitrage_finder.py           │
│  (Detects opportunities)        │
└──────────────┬──────────────────┘
               │
               ↓
┌─────────────────────────────────┐
│ discord_integration.py          │
│ (Bridges finder to Discord)     │
└──────────────┬──────────────────┘
               │
               ↓
┌─────────────────────────────────┐
│   discord_bot.py                │
│   (Manages Discord)             │
└──────────────┬──────────────────┘
               │
               ↓
┌─────────────────────────────────┐
│   Discord Server                │
│   (Sends alerts to users)       │
└─────────────────────────────────┘
```

## Step 1: Update arbitrage_finder.py

Add Discord integration to the main arbitrage finder loop:

### 1.1 Add imports at the top of arbitrage_finder.py

```python
import asyncio
from discord_integration import setup_discord_integration, DiscordIntegrationManager
import discord
from discord.ext import commands
```

### 1.2 Add Discord integration to ArbitrageFinder class

In the `__init__` method, add:

```python
class ArbitrageFinder:
    def __init__(self):
        # ... existing code ...

        self.discord_bot = None
        self.discord_manager = None

    async def initialize_discord(self, bot_token: str):
        """
        Initialize Discord bot integration

        Args:
            bot_token: Discord bot token
        """
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True

            self.discord_bot = commands.Bot(command_prefix='/', intents=intents)

            # Set up integration
            self.discord_manager = await setup_discord_integration(self.discord_bot, self)

            logger.info("Discord integration initialized")
        except Exception as e:
            logger.error(f"Error initializing Discord: {e}")
```

### 1.3 Modify check_for_arbitrage() to send alerts to Discord

In the `check_for_arbitrage()` method, when an opportunity is found:

```python
def check_for_arbitrage(self):
    """Check for arbitrage opportunities"""
    # ... existing code ...

    for opportunity in verified_opportunities:
        # Display to console (existing code)
        self.display_alert(opportunity)

        # Send to Discord (NEW)
        if self.discord_manager:
            try:
                asyncio.create_task(self.discord_manager.send_opportunity_alert(opportunity))
            except Exception as e:
                logger.error(f"Error sending Discord alert: {e}")
```

## Step 2: Run Discord Bot and Arbitrage Finder Together

### Option A: Run Both in Separate Processes (Recommended)

**Terminal 1 - Discord Bot:**
```bash
python3 discord_bot.py
```

**Terminal 2 - Arbitrage Finder:**
```bash
python3 arbitrage_finder.py
```

### Option B: Run Both in Same Process

Create a new file `main.py`:

```python
"""
Main entry point for Arbitrage Finder with Discord Integration
Runs both the Discord bot and arbitrage finder together
"""

import asyncio
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import components
from discord_bot import bot, ArbitrageBot, AlertSystem
from arbitrage_finder import ArbitrageFinder
from discord_integration import setup_discord_integration


async def run_arbitrage_finder_loop(finder, sleep_interval=60):
    """
    Run the arbitrage finder in a loop

    Args:
        finder: ArbitrageFinder instance
        sleep_interval: Seconds between checks
    """
    while True:
        try:
            finder.check_for_arbitrage()
            await asyncio.sleep(sleep_interval)
        except Exception as e:
            logger.error(f"Error in arbitrage finder loop: {e}")
            await asyncio.sleep(sleep_interval)


async def main():
    """Main async entry point"""

    # Initialize arbitrage finder
    finder = ArbitrageFinder()

    # Initialize Discord integration
    bot.loop = asyncio.get_event_loop()

    # Add cogs
    await bot.add_cog(ArbitrageBot(bot))
    await bot.add_cog(AlertSystem(bot))

    # Set up integration
    manager = await setup_discord_integration(bot, finder)
    finder.discord_manager = manager

    # Run both concurrently
    discord_task = asyncio.create_task(bot.start(os.getenv('DISCORD_BOT_TOKEN')))
    finder_task = asyncio.create_task(run_arbitrage_finder_loop(finder, sleep_interval=60))

    # Wait for both tasks
    await asyncio.gather(discord_task, finder_task)


if __name__ == '__main__':
    asyncio.run(main())
```

Run with:
```bash
python3 main.py
```

## Step 3: Test the Integration

### Test 1: Verify Bot is Running

In Discord, type:
```
/help
```

Should return help menu.

### Test 2: Test Trial Signup

1. Click `/subscribe`
2. Click "Start 7-Day Free Trial"
3. Check that user gets Subscriber role
4. Check that user can access `#premium-opportunities`

### Test 3: Test Opportunity Alert

Manually trigger an alert in the Discord bot:

```python
# In discord_bot.py or a test file
async def test_alert():
    from discord_notifier import DiscordNotifier

    bot = commands.Bot(command_prefix='/')
    notifier = DiscordNotifier(bot)

    # Get alert channel
    channel = bot.get_channel(ALERTS_CHANNEL_ID)

    # Create test opportunity
    test_opp = {
        'event_name': 'Test Opportunity',
        'sport': 'soccer_epl',
        'commence_time': '2024-01-15T20:00:00Z',
        'player_a': 'Team A',
        'player_b': 'Team B',
        'odds_a': 2.05,
        'odds_b': 1.95,
        'stake_a': 48.78,
        'stake_b': 51.22,
        'bookmaker_a': 'DraftKings',
        'bookmaker_b': 'FanDuel',
        'guaranteed_profit': 5.00,
        'profit_margin': 5.0,
        'confidence': 90.0,
        'confidence_label': 'HIGH',
        'is_validated': True
    }

    # Send alert
    await notifier.send_opportunity_alert(channel, test_opp)

# Run the test
asyncio.run(test_alert())
```

## Step 4: Configure Daily Summary

The Discord integration automatically sends daily summaries to the `#statistics` channel at midnight UTC.

To customize:

1. Edit `discord_integration.py` - `daily_summary_task()` method
2. Change the schedule using `@tasks.loop()`
3. Modify summary format in `send_daily_summary_to_channel()`

## Step 5: Set Up Payment Processing

### 5.1 Configure Stripe Webhook

1. In your hosting environment, set up a webhook endpoint:

```python
# In discord_bot.py or main.py
from flask import Flask, request
from payment_handler import get_payment_handler

app = Flask(__name__)
payment_handler = get_payment_handler()

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    success, event_data = payment_handler.process_webhook(payload, sig_header)

    if success and event_data:
        # Handle event
        logger.info(f"Webhook event: {event_data['type']}")
        # Could send Discord notification here

    return '', 200
```

### 5.2 Update Stripe Webhook URL

In Stripe Dashboard:
1. Go to Developers → Webhooks
2. Update endpoint URL to: `https://your-domain.com/webhook/stripe`
3. Copy Signing Secret to `.env` as `STRIPE_WEBHOOK_SECRET`

## Step 6: Monitor Performance

### View Logs

```bash
# Watch bot logs
tail -f arbitrage_finder.log

# Filter for Discord errors
grep "Discord" arbitrage_finder.log
```

### Monitor Subscriptions

Check subscription stats in Discord with admin command:

```
/admin-stats
```

(Or access database directly)

```python
from subscription_manager import SubscriptionManager

manager = SubscriptionManager()
stats = asyncio.run(manager.get_subscription_stats())
print(f"Active: {stats['active_subscriptions']}")
print(f"Trial: {stats['trial_subscriptions']}")
print(f"Revenue: ${stats['total_revenue']}")
```

## Troubleshooting

### Issue 1: Bot Not Sending Alerts

**Check:**
1. Bot is running: `python3 discord_bot.py`
2. Arbitrage finder is running: `python3 arbitrage_finder.py`
3. Channel IDs are correct in `.env`
4. Bot has permissions in channels

**Fix:**
```bash
# Check bot is connected
python3 -c "from discord_bot import bot; print(f'Bot connected: {bot.latency}')"
```

### Issue 2: Alerts Not Appearing in Discord

**Check:**
1. Bot has "Send Messages" permission
2. Channel is not locked
3. Check logs for errors: `grep "Error sending" arbitrage_finder.log`

**Fix:**
```python
# Test sending message directly
import asyncio
from discord_bot import bot

async def test_send():
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("Test message")

asyncio.run(test_send())
```

### Issue 3: Subscription Verification Failing

**Check:**
1. User role ID is correct
2. Bot role is above subscriber role
3. User actually has subscriber role

**Fix:**
```python
# Check user roles
user = bot.get_user(USER_ID)
member = guild.get_member(user.id)
print(f"User roles: {member.roles}")
```

## Advanced Configuration

### Custom Alert Frequency

In `user_manager.py`, modify `update_preferences()` to store frequency preference:

```python
preferences = {
    'alert_frequency': 'realtime',  # or 'hourly', 'daily'
    'min_profit_threshold': 2.0,
    'preferred_sports': ['soccer_epl', 'soccer_spain_la_liga']
}

await subscription_manager.update_preferences(user_id, preferences)
```

### Custom Opportunity Filtering

In `discord_notifier.py`, add filtering before sending:

```python
async def send_opportunity_alert(self, channel, opportunity, is_premium=False):
    # Filter by profit margin
    if opportunity['profit_margin'] < 3.0:
        logger.debug(f"Filtered low-margin opportunity: {opportunity}")
        return False

    # Continue with normal send
    ...
```

### Multi-Server Support

To support multiple Discord servers:

1. Store server IDs in database
2. Create separate integration manager per server
3. Update `discord_integration.py` to handle multiple guilds

```python
class DiscordIntegrationManager:
    def __init__(self, bot, arbitrage_finder, guild_id):
        self.bot = bot
        self.arbitrage_finder = arbitrage_finder
        self.guild_id = guild_id
        self.guild = bot.get_guild(guild_id)
```

## Performance Considerations

### Database Optimization

Add indexes to frequently queried columns:

```python
# In subscription_manager.py init_database()
cursor.execute('CREATE INDEX idx_discord_id ON subscriptions(discord_id)')
cursor.execute('CREATE INDEX idx_status ON subscriptions(status)')
```

### Rate Limiting

The `DiscordNotifier` includes rate limiting to prevent spam:

```python
# In discord_notifier.py
self.rate_limit_cache = {}  # One alert per opportunity per minute

# Clear cache periodically
async def clear_old_cache(self):
    # Clear cache every hour
    await asyncio.sleep(3600)
    self.rate_limit_cache.clear()
```

### Async Processing

The integration uses asyncio for non-blocking operations:

```python
# Non-blocking alert send
asyncio.create_task(self.discord_manager.send_opportunity_alert(opportunity))
```

## Next Steps

1. **Deploy to Cloud** - Use Heroku, AWS, or similar
2. **Add Web Dashboard** - Create user management interface
3. **Expand Payment Options** - Add PayPal, crypto payments
4. **Marketing** - Launch promotional campaign

## Resources

- [Complete Implementation Example](./examples/discord_integration_example.py)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Stripe Integration Guide](./STRIPE_SETUP_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)

## Support

For issues or questions:

1. Check the logs: `tail -f arbitrage_finder.log`
2. Run tests: `python3 -m pytest tests/`
3. Enable debug logging: `LOG_LEVEL=DEBUG`

---

**Ready to launch?** Once integration is tested, you're ready to start accepting subscribers!
