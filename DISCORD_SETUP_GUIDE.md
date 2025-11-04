# Discord Bot Setup Guide - Arbitrage Finder Premium Service

This guide walks you through setting up the Discord bot for the Arbitrage Finder premium subscription service.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Create Discord Application](#step-1-create-discord-application)
3. [Step 2: Create Discord Server](#step-2-create-discord-server)
4. [Step 3: Set Up Channels](#step-3-set-up-channels)
5. [Step 4: Create Roles](#step-4-create-roles)
6. [Step 5: Install Dependencies](#step-5-install-dependencies)
7. [Step 6: Configure Environment Variables](#step-6-configure-environment-variables)
8. [Step 7: Start the Bot](#step-7-start-the-bot)
9. [Step 8: Set Up Stripe Integration](#step-8-set-up-stripe-integration)
10. [Testing](#testing)

## Prerequisites

- **Discord Account**: You need a Discord account
- **Python 3.8+**: Required for running the bot
- **Stripe Account**: For payment processing (optional for testing)
- **The Odds API Key**: Already configured in your project

## Step 1: Create Discord Application

### 1.1 Go to Discord Developer Portal

1. Visit https://discord.com/developers/applications
2. Click "New Application"
3. Enter a name: "Arbitrage Finder Premium"
4. Accept the terms and click "Create"

### 1.2 Create a Bot User

1. Go to the "Bot" section on the left sidebar
2. Click "Add Bot"
3. Under the TOKEN section, click "Copy" to copy your bot token
4. **IMPORTANT**: Keep this token secret! Store it in `.env` as `DISCORD_BOT_TOKEN`

### 1.3 Set Bot Permissions

1. Go to "OAuth2" → "URL Generator"
2. Under "SCOPES", select:
   - `bot`
   - `applications.commands`
3. Under "PERMISSIONS", select:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
   - `Add Reactions`
   - `Manage Roles`
   - `Manage Messages`
4. Copy the generated URL and save it for later

## Step 2: Create Discord Server

### 2.1 Create a New Server

1. Open Discord
2. Click the "+" icon on the left sidebar
3. Select "Create My Own"
4. Give it a name: "Arbitrage Finder Premium"
5. Click "Create"
6. Invite yourself if needed

### 2.2 Get Server ID

1. Enable "Developer Mode" in Discord:
   - User Settings → Advanced → Developer Mode (toggle ON)
2. Right-click on your server name
3. Click "Copy Server ID"
4. Store this in `.env` as `DISCORD_GUILD_ID`

## Step 3: Set Up Channels

Create the following channels in your Discord server:

### Create Channel Categories

1. Right-click in the left sidebar → "Create Category"

#### Create these channels:

**Public Channels**:
- `#welcome` - Welcome message and rules
- `#announcements` - Major announcements
- `#general-chat` - General discussion
- `#support` - Support requests

**Subscriber-Only Channels**:
- `#alerts` - Real-time opportunity alerts
- `#premium-opportunities` - Top 5 weekly summary
- `#statistics` - Daily/weekly stats

**Admin Channels**:
- `#admin-panel` - Admin commands and management

### 3.1 Get Channel IDs

For each channel you need the ID in your `.env`:

1. Enable Developer Mode (if not already done)
2. Right-click on channel
3. Click "Copy Channel ID"
4. Store in `.env`:
   - `ALERTS_CHANNEL_ID`
   - `PREMIUM_ALERTS_CHANNEL_ID`
   - `STATS_CHANNEL_ID`
   - `SUPPORT_CHANNEL_ID`
   - `ADMIN_CHANNEL_ID`

### 3.2 Set Channel Permissions

For subscriber-only channels:

1. Right-click channel → "Edit Channel"
2. Go to "Permissions" tab
3. Click "@everyone" role
4. Deny "View Channel"
5. Save changes

## Step 4: Create Roles

### 4.1 Create Subscriber Role

1. Server Settings → Roles
2. Click "Create Role"
3. Name it: "Subscriber"
4. Color: Green (or your preference)
5. Under Permissions, enable:
   - View Channels
   - Send Messages
   - Read Message History
6. Save

### 4.2 Create Admin Role

1. Click "Create Role"
2. Name it: "Admin"
3. Color: Red
4. Enable admin permissions
5. Save

### 4.3 Create Trial Role (Optional)

1. Click "Create Role"
2. Name it: "Trial"
3. Color: Yellow
4. Same permissions as Subscriber
5. Save

### 4.4 Get Role IDs

For each role:

1. Right-click the role
2. Click "Copy Role ID"
3. Store in `.env`:
   - `SUBSCRIBER_ROLE_ID`
   - `ADMIN_ROLE_ID`
   - `TRIAL_ROLE_ID`

## Step 5: Install Dependencies

```bash
# Navigate to project directory
cd "Arbitrage Finder"

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# If you want to use Stripe payments
pip install stripe
```

## Step 6: Configure Environment Variables

### 6.1 Copy the template

```bash
cp .env.example .env
```

### 6.2 Edit `.env` with your values

Open `.env` in a text editor and fill in:

```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here

# Channel IDs
ALERTS_CHANNEL_ID=your_channel_id
PREMIUM_ALERTS_CHANNEL_ID=your_channel_id
STATS_CHANNEL_ID=your_channel_id
SUPPORT_CHANNEL_ID=your_channel_id
ADMIN_CHANNEL_ID=your_channel_id

# Role IDs
SUBSCRIBER_ROLE_ID=your_role_id
ADMIN_ROLE_ID=your_role_id
TRIAL_ROLE_ID=your_role_id

# The Odds API
ODDS_API_KEY=your_api_key

# Stripe (optional, for payments)
STRIPE_API_KEY=your_stripe_key
```

## Step 7: Start the Bot

### 7.1 Run the bot

```bash
python3 discord_bot.py
```

You should see:
```
Bot logged in as Arbitrage Finder Premium#1234
Synced 5 command(s)
```

### 7.2 Invite Bot to Server

1. Use the OAuth2 URL you generated in Step 1.3
2. Select your server
3. Click "Authorize"
4. Complete any CAPTCHA

### 7.3 Test the Bot

In Discord, try:
- `/subscribe` - Should show subscription options
- `/help` - Should display command help
- `/status` - Should show subscription status

## Step 8: Set Up Stripe Integration

### 8.1 Create Stripe Account

1. Go to https://stripe.com
2. Sign up for an account
3. Go to Dashboard → API Keys
4. Copy your Secret Key
5. Store in `.env` as `STRIPE_API_KEY`

### 8.2 Create Product and Price

1. In Stripe Dashboard, go to Products
2. Click "Create product"
3. Name: "Arbitrage Finder Premium"
4. Price: $20
5. Billing period: Monthly
6. Save the Product ID as `STRIPE_PRODUCT_ID`
7. Save the Price ID as `STRIPE_PRICE_ID`

### 8.3 Set Up Webhooks

1. In Stripe Dashboard, go to Developers → Webhooks
2. Click "Add an endpoint"
3. Endpoint URL: `https://your-domain.com/stripe-webhook`
4. Events to listen: `customer.subscription.*`, `invoice.payment_*`
5. Copy Signing Secret
6. Store in `.env` as `STRIPE_WEBHOOK_SECRET`

## Testing

### Test 1: Bot Responds to Commands

```
/subscribe
/help
/status
/stats
```

All should return embed messages.

### Test 2: Trial Signup

1. Click "Start 7-Day Free Trial"
2. User should get Subscriber role (check in Server Settings → Members)
3. User should have access to `#premium-opportunities`

### Test 3: Send Test Alert

```python
# In Discord bot console or test file
from discord_notifier import DiscordNotifier

notifier = DiscordNotifier(bot)
test_opportunity = {
    'event_name': 'Test Event',
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
    'confidence': 90,
    'confidence_label': 'HIGH',
    'is_validated': True
}

await notifier.send_opportunity_alert(channel, test_opportunity)
```

### Test 4: Daily Summary

```python
from discord_notifier import DiscordNotifier

summary = {
    'total_found': 15,
    'high_confidence': 5,
    'total_profit': 125.50,
    'top_opportunity': 'Team A vs Team B',
    'top_margin': 8.5,
    'top_profit': 25.00
}

await notifier.send_daily_summary(channel, summary)
```

## Common Issues

### Issue 1: Bot Doesn't Show Up in Server

**Solution**: Check that the bot has the correct OAuth2 scopes and permissions.

### Issue 2: Commands Not Working

**Solution**:
- Restart the bot
- Ensure `DISCORD_BOT_TOKEN` is correct
- Check bot has "Use Slash Commands" permission

### Issue 3: Role Assignment Fails

**Solution**:
- Ensure bot role is ABOVE subscriber/admin roles in role hierarchy
- Check role IDs in `.env` are correct

### Issue 4: Channel Permissions Issues

**Solution**:
- Ensure bot has "Manage Roles" permission
- Check channel @everyone permissions

## Next Steps

1. **Integrate with arbitrage_finder.py** - Add bot alerts to main application
2. **Set up web dashboard** - Create user management interface
3. **Marketing & Launch** - Promote to users

## Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/)
- [Stripe Documentation](https://stripe.com/docs)
- [The Odds API](https://the-odds-api.com/)

## Support

If you encounter issues:

1. Check the bot logs for error messages
2. Verify all environment variables are set correctly
3. Ensure Discord bot has required permissions
4. Check Stripe account is in test mode (during development)

---

**Ready to launch?** Once testing is complete, you're ready to invite users to your Discord server!
