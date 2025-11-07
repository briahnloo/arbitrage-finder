"""
Discord Bot for Arbitrage Finder Premium Service
Handles bot commands, alerts, and user management for $20/month subscription service
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import Optional
import asyncio

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

class ArbitrageBotConfig:
    """Configuration for the Discord bot"""
    DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    STRIPE_KEY = os.getenv('STRIPE_API_KEY')
    ALERTS_CHANNEL_ID = int(os.getenv('ALERTS_CHANNEL_ID', '0'))
    PREMIUM_ALERTS_CHANNEL_ID = int(os.getenv('PREMIUM_ALERTS_CHANNEL_ID', '0'))
    STATS_CHANNEL_ID = int(os.getenv('STATS_CHANNEL_ID', '0'))
    SUBSCRIBER_ROLE_ID = int(os.getenv('SUBSCRIBER_ROLE_ID', '0'))
    ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', '0'))
    SUBSCRIPTION_PRICE = 20.00
    TRIAL_DAYS = 7


class SubscriptionManager:
    """Manages user subscriptions and database operations"""

    def __init__(self):
        self.subscriptions = {}  # In-memory cache, replace with database

    async def check_subscription(self, discord_id: int) -> bool:
        """Check if user has active subscription"""
        if discord_id not in self.subscriptions:
            return False

        sub = self.subscriptions[discord_id]
        if sub.get('status') == 'active':
            return True
        return False

    async def add_subscription(self, discord_id: int, payment_id: str):
        """Add new subscription for user"""
        self.subscriptions[discord_id] = {
            'status': 'active',
            'payment_id': payment_id,
            'start_date': datetime.now(),
            'expires_at': datetime.now()
        }
        logger.info(f"Subscription added for user {discord_id}")

    async def cancel_subscription(self, discord_id: int):
        """Cancel user subscription"""
        if discord_id in self.subscriptions:
            self.subscriptions[discord_id]['status'] = 'cancelled'
            logger.info(f"Subscription cancelled for user {discord_id}")


class ArbitrageBot(commands.Cog):
    """Main bot cog for arbitrage finder commands"""

    def __init__(self, bot):
        self.bot = bot
        self.subscription_manager = SubscriptionManager()
        self.config = ArbitrageBotConfig()

    @app_commands.command(
        name='subscribe',
        description='Subscribe to Arbitrage Finder Premium ($20/month)'
    )
    async def subscribe_command(self, interaction: discord.Interaction):
        """Handle subscription signup"""
        embed = discord.Embed(
            title='🎯 Arbitrage Finder Premium',
            description='Transform your sports betting with real-time arbitrage opportunities',
            color=discord.Color.green()
        )

        embed.add_field(
            name='📦 Basic Plan - $20/month',
            value='• Real-time arbitrage alerts\n'
                  '• Top 5 opportunities daily\n'
                  '• Daily statistics\n'
                  '• Community access\n'
                  '• Basic support',
            inline=False
        )

        embed.add_field(
            name='🎁 Special Offer',
            value=f'7-day FREE trial - Full access, no payment required',
            inline=False
        )

        embed.add_field(
            name='📊 What You Get',
            value='✅ Guaranteed risk-free arbitrage opportunities\n'
                  '✅ Real-time Discord notifications\n'
                  '✅ Detailed bet information (odds, stakes, bookmakers)\n'
                  '✅ Profit calculations and ROI\n'
                  '✅ 24/7 access to premium channels',
            inline=False
        )

        embed.set_footer(text='Arbitrage Finder Premium | Mathematical precision, guaranteed profits')

        # Create button for payment
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label='Start 7-Day Free Trial',
            style=discord.ButtonStyle.primary,
            custom_id='start_trial'
        ))
        view.add_item(discord.ui.Button(
            label='Subscribe Now',
            style=discord.ButtonStyle.success,
            custom_id='subscribe_now'
        ))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(
        name='status',
        description='Check your subscription status'
    )
    async def status_command(self, interaction: discord.Interaction):
        """Check user subscription status"""
        user_id = interaction.user.id
        is_subscribed = await self.subscription_manager.check_subscription(user_id)

        if is_subscribed:
            embed = discord.Embed(
                title='✅ Subscription Active',
                description='You have access to all premium features',
                color=discord.Color.green()
            )
            embed.add_field(name='Status', value='Active', inline=True)
            embed.add_field(name='Renewal Date', value='Coming soon', inline=True)
        else:
            embed = discord.Embed(
                title='❌ No Active Subscription',
                description='Subscribe to get real-time arbitrage alerts',
                color=discord.Color.red()
            )
            embed.add_field(
                name='Action Required',
                value='Use `/subscribe` to start your 7-day free trial',
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='stats',
        description='View your arbitrage statistics'
    )
    async def stats_command(self, interaction: discord.Interaction):
        """Display user statistics"""
        embed = discord.Embed(
            title='📊 Your Arbitrage Statistics',
            color=discord.Color.blue()
        )

        embed.add_field(name='Opportunities Found', value='0', inline=True)
        embed.add_field(name='Total Potential Profit', value='$0.00', inline=True)
        embed.add_field(name='Avg Profit Margin', value='0.00%', inline=True)

        embed.add_field(
            name='This Month',
            value='```\n'
                  'Opportunities: 0\n'
                  'High Confidence: 0\n'
                  'Total ROI: 0.00%\n'
                  '```',
            inline=False
        )

        embed.set_footer(text='Data resets monthly')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='help',
        description='Get help with bot commands'
    )
    async def help_command(self, interaction: discord.Interaction):
        """Display help information"""
        embed = discord.Embed(
            title='🆘 Help & Commands',
            color=discord.Color.blue()
        )

        embed.add_field(
            name='/subscribe',
            value='Start your free trial or subscribe to premium',
            inline=False
        )
        embed.add_field(
            name='/status',
            value='Check your subscription and account status',
            inline=False
        )
        embed.add_field(
            name='/stats',
            value='View your arbitrage statistics and performance',
            inline=False
        )
        embed.add_field(
            name='/preferences',
            value='Set your alert preferences and sports filters',
            inline=False
        )
        embed.add_field(
            name='/help',
            value='Display this help message',
            inline=False
        )

        embed.add_field(
            name='📚 Learn More',
            value='Check out <#announcements> for tutorials and guides',
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='preferences',
        description='Set your alert preferences'
    )
    async def preferences_command(self, interaction: discord.Interaction):
        """Allow users to customize alert preferences"""
        embed = discord.Embed(
            title='⚙️ Alert Preferences',
            color=discord.Color.blue()
        )

        embed.add_field(
            name='Minimum Profit Threshold',
            value='Currently: 2.0%',
            inline=False
        )
        embed.add_field(
            name='Preferred Sports',
            value='All sports enabled',
            inline=False
        )
        embed.add_field(
            name='Alert Frequency',
            value='Real-time alerts',
            inline=False
        )

        embed.set_footer(text='Settings are saved per user and apply to all alerts')

        await interaction.response.send_message(embed=embed, ephemeral=True)


class AlertSystem(commands.Cog):
    """Handles sending alerts to Discord channels"""

    def __init__(self, bot):
        self.bot = bot
        self.config = ArbitrageBotConfig()
        self.rate_limit_cache = {}

    async def send_opportunity_alert(self, opportunity: dict, is_premium: bool = False):
        """
        Send formatted alert to Discord channel

        Args:
            opportunity: Opportunity dictionary from arbitrage finder
            is_premium: Whether to send to premium channel
        """
        channel_id = self.config.PREMIUM_ALERTS_CHANNEL_ID if is_premium else self.config.ALERTS_CHANNEL_ID
        channel = self.bot.get_channel(channel_id)

        if not channel:
            logger.error(f"Alert channel not found: {channel_id}")
            return

        # Create embed message
        embed = discord.Embed(
            title=f"🎯 {opportunity.get('event_name', 'Arbitrage Opportunity')}",
            color=discord.Color.gold()
        )

        # Event information
        embed.add_field(
            name='📌 Event Details',
            value=f"**Sport:** {opportunity.get('sport', 'Unknown')}\n"
                  f"**Time:** {opportunity.get('commence_time', 'N/A')}\n"
                  f"**Market:** {opportunity.get('market', 'H2H')}",
            inline=False
        )

        # Betting information
        embed.add_field(
            name='💰 BET 1',
            value=f"**{opportunity.get('player_a', 'Player A')}**\n"
                  f"Bookmaker: {opportunity.get('bookmaker_a', 'Unknown')}\n"
                  f"Odds: {opportunity.get('odds_a', 0):.2f}\n"
                  f"Stake: ${opportunity.get('stake_a', 0):.2f}",
            inline=True
        )

        embed.add_field(
            name='💰 BET 2',
            value=f"**{opportunity.get('player_b', 'Player B')}**\n"
                  f"Bookmaker: {opportunity.get('bookmaker_b', 'Unknown')}\n"
                  f"Odds: {opportunity.get('odds_b', 0):.2f}\n"
                  f"Stake: ${opportunity.get('stake_b', 0):.2f}",
            inline=True
        )

        # Profit information
        profit = opportunity.get('guaranteed_profit', 0)
        margin = opportunity.get('profit_margin', 0)

        embed.add_field(
            name='📊 Profit Summary',
            value=f"**Profit Margin:** {margin:.2f}%\n"
                  f"**Total Investment:** ${opportunity.get('total_stake', 100):.2f}\n"
                  f"**Guaranteed Profit:** ${profit:.2f}\n"
                  f"**ROI:** {(profit/opportunity.get('total_stake', 100)*100):.1f}%",
            inline=False
        )

        # Confidence level
        confidence = opportunity.get('confidence', 0)
        conf_label = opportunity.get('confidence_label', 'MEDIUM')
        color_emoji = '🟢' if conf_label == 'HIGH' else '🟡' if conf_label == 'MEDIUM' else '🔴'

        embed.add_field(
            name='🎲 Confidence',
            value=f"{color_emoji} {conf_label} ({confidence:.0f}%)\n"
                  f"Validation: {'✅ VERIFIED' if opportunity.get('is_validated') else '⚠️ Needs review'}",
            inline=False
        )

        embed.set_footer(text='Arbitrage Finder Premium | Risk-free guaranteed profits')
        embed.timestamp = datetime.now()

        await channel.send(embed=embed)

    async def send_daily_summary(self, summary_data: dict):
        """Send daily statistics summary to stats channel"""
        channel = self.bot.get_channel(self.config.STATS_CHANNEL_ID)

        if not channel:
            logger.error(f"Stats channel not found")
            return

        embed = discord.Embed(
            title='📊 Daily Arbitrage Summary',
            color=discord.Color.blue()
        )

        embed.add_field(
            name='Opportunities Found',
            value=str(summary_data.get('total_found', 0)),
            inline=True
        )
        embed.add_field(
            name='High Confidence',
            value=str(summary_data.get('high_confidence', 0)),
            inline=True
        )
        embed.add_field(
            name='Total Potential Profit',
            value=f"${summary_data.get('total_profit', 0):.2f}",
            inline=True
        )

        embed.add_field(
            name='Top Opportunity',
            value=f"{summary_data.get('top_opportunity', 'N/A')}\n"
                  f"Margin: {summary_data.get('top_margin', 0):.2f}%",
            inline=False
        )

        embed.timestamp = datetime.now()
        await channel.send(embed=embed)


@bot.event
async def on_ready():
    """Called when bot connects to Discord"""
    logger.info(f'Bot logged in as {bot.user}')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name='arbitrage opportunities 📊'
        )
    )

    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')


@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Handle button interactions"""
    if interaction.type == discord.InteractionType.component:
        if interaction.data['custom_id'] == 'start_trial':
            await handle_trial_start(interaction)
        elif interaction.data['custom_id'] == 'subscribe_now':
            await handle_subscribe(interaction)


async def handle_trial_start(interaction: discord.Interaction):
    """Handle trial signup"""
    embed = discord.Embed(
        title='🎁 7-Day Free Trial Started!',
        description='Welcome to Arbitrage Finder Premium',
        color=discord.Color.green()
    )

    embed.add_field(
        name='What\'s Next?',
        value='1. Join <#premium-opportunities> for real-time alerts\n'
              '2. Use `/stats` to track opportunities\n'
              '3. Check <#getting-started> for tutorials',
        inline=False
    )

    embed.add_field(
        name='Trial Details',
        value='Duration: 7 days\n'
              'Cost: FREE\n'
              'Expires: In 7 days',
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


async def handle_subscribe(interaction: discord.Interaction):
    """Handle subscription"""
    embed = discord.Embed(
        title='💳 Subscription',
        description='Payment processing coming soon',
        color=discord.Color.blue()
    )

    embed.add_field(
        name='Price',
        value='$20/month (billed monthly)',
        inline=False
    )

    embed.add_field(
        name='Status',
        value='Payment system integration in progress\n'
              'Stripe integration launching soon',
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


async def main():
    """Main bot startup"""
    # Add cogs
    await bot.add_cog(ArbitrageBot(bot))
    await bot.add_cog(AlertSystem(bot))

    # Start bot
    if not ArbitrageBotConfig.DISCORD_TOKEN:
        logger.error('DISCORD_BOT_TOKEN not set in .env file')
        return

    try:
        await bot.start(ArbitrageBotConfig.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f'Failed to start bot: {e}')


if __name__ == '__main__':
    asyncio.run(main())
