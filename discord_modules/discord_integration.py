"""
Discord Integration Module for Arbitrage Finder
Connects the Discord bot with the arbitrage finder to send real-time alerts
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import discord.py from sys.modules (should be set by discord_bot.py)
# If not available, import it ourselves
if 'discord' not in sys.modules or not hasattr(sys.modules['discord'], 'ext'):
    # Remove local discord from path temporarily
    local_discord_dir = str(Path(__file__).parent)
    sys.path = [p for p in sys.path if p != local_discord_dir]

    try:
        import discord as discord_py
        from discord.ext import commands, tasks
        sys.modules['discord'] = discord_py
    finally:
        sys.path.insert(0, local_discord_dir)
else:
    discord_py = sys.modules['discord']
    from discord.ext import commands, tasks

discord = discord_py

import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime

from .discord_notifier import DiscordNotifier
from .subscription_manager import SubscriptionManager
from .user_manager import UserManager
from src.arbitrage_finder import ArbitrageFinder

logger = logging.getLogger(__name__)


class DiscordIntegrationManager:
    """Manages integration between Discord bot and arbitrage finder"""

    def __init__(self, bot: commands.Bot, arbitrage_finder: ArbitrageFinder):
        self.bot = bot
        self.arbitrage_finder = arbitrage_finder
        self.notifier = DiscordNotifier(bot)
        self.subscription_manager = SubscriptionManager()
        self.user_manager = None
        self.guild = None
        self.active_subscribers = set()
        self.daily_summary = {
            'total_found': 0,
            'high_confidence': 0,
            'total_profit': 0,
            'opportunities': []
        }

    async def initialize(self, guild: discord.Guild):
        """
        Initialize the integration manager

        Args:
            guild: Discord guild to manage
        """
        self.guild = guild
        self.user_manager = UserManager(guild, self.subscription_manager)
        logger.info(f'Discord integration initialized for guild {guild.id}')

    async def send_opportunity_to_subscribers(self, opportunity: Dict, is_high_priority: bool = False):
        """
        Send opportunity alert to subscribers based on premium status.
        Routes premium users to premium channel, free users to preview channel.
        ENHANCED: Comprehensive logging at each step for full visibility.
        """
        event_name = opportunity.get('event_name', 'unknown')
        logger.info(f'[DISCORD] 📤 Attempting to send alert: {event_name}')

        # STEP 1: Ensure guild is initialized
        # BUGFIX: If guild wasn't available at startup, try to initialize it now
        if not self.guild and self.bot.guilds:
            guild = self.bot.guilds[0]
            await self.initialize(guild)
            logger.info(f'[DISCORD] ✓ Deferred guild initialization: {guild.name} (ID: {guild.id})')

        # STEP 2: Validate guild exists before proceeding
        if not self.guild:
            logger.error(f'[DISCORD] ❌ CRITICAL: Guild not initialized - cannot send "{event_name}"')
            logger.error(f'[DISCORD] Bot must be invited to a Discord server. Check that bot is in your server.')
            return

        logger.debug(f'[DISCORD] ✓ Guild ready: {self.guild.name}')

        try:
            # STEP 3: Get channel IDs from config
            from src.config import (
                DISCORD_PREMIUM_ALERTS_CHANNEL_ID,
                DISCORD_FREE_PREVIEW_CHANNEL_ID
            )

            # STEP 4: Fetch channels from Discord
            premium_channel = self.bot.get_channel(DISCORD_PREMIUM_ALERTS_CHANNEL_ID)
            free_channel = self.bot.get_channel(DISCORD_FREE_PREVIEW_CHANNEL_ID)

            # STEP 5: Validate channels exist (detailed logging)
            if premium_channel:
                logger.debug(f'[DISCORD] ✓ Premium channel found: {premium_channel.name} (ID: {DISCORD_PREMIUM_ALERTS_CHANNEL_ID})')
            else:
                logger.error(f'[DISCORD] ❌ Premium channel NOT FOUND (ID: {DISCORD_PREMIUM_ALERTS_CHANNEL_ID})')
                logger.error(f'[DISCORD] Check: channel ID correct? Bot has permission to see channel?')

            if free_channel:
                logger.debug(f'[DISCORD] ✓ Free preview channel found: {free_channel.name} (ID: {DISCORD_FREE_PREVIEW_CHANNEL_ID})')
            else:
                logger.error(f'[DISCORD] ❌ Free preview channel NOT FOUND (ID: {DISCORD_FREE_PREVIEW_CHANNEL_ID})')
                logger.error(f'[DISCORD] Check: channel ID correct? Bot has permission to see channel?')

            # STEP 6: Get premium users for routing decision
            premium_users = await self.subscription_manager.get_all_premium_users()
            logger.debug(f'[DISCORD] Premium users in database: {len(premium_users)}')

            # STEP 7: Send to premium channel (if exists and has subscribers)
            premium_send_ok = False
            if premium_channel and premium_users:
                try:
                    await self.notifier.send_opportunity_alert(
                        premium_channel,
                        opportunity,
                        is_premium=True
                    )
                    logger.info(f'[DISCORD] ✓✓ Premium channel sent: "{event_name}"')
                    premium_send_ok = True
                except Exception as e:
                    logger.error(f'[DISCORD] ❌ Premium channel send failed: {e}')
                    import traceback
                    logger.error(f'[DISCORD] Traceback:\n{traceback.format_exc()}')
            elif premium_channel and not premium_users:
                logger.info(f'[DISCORD] ℹ️  Premium channel skipped: no premium users yet for "{event_name}"')
            elif not premium_channel:
                logger.warning(f'[DISCORD] ⚠️  Premium channel unavailable - skipping')

            # STEP 8: Always send to free preview channel (sample for all users)
            free_send_ok = False
            if free_channel:
                try:
                    await self.notifier.send_opportunity_alert(
                        free_channel,
                        opportunity,
                        is_premium=False
                    )
                    logger.info(f'[DISCORD] ✓✓ Free preview channel sent: "{event_name}"')
                    free_send_ok = True
                except Exception as e:
                    logger.error(f'[DISCORD] ❌ Free channel send failed: {e}')
                    import traceback
                    logger.error(f'[DISCORD] Traceback:\n{traceback.format_exc()}')
            else:
                logger.error(f'[DISCORD] ❌ Free preview channel unavailable - alert NOT sent')

            # STEP 9: Final status
            if free_send_ok or premium_send_ok:
                logger.info(f'[DISCORD] ✓✓✓ Alert completed for: "{event_name}"')
            else:
                logger.error(f'[DISCORD] ❌ Alert FAILED: no channels available or all sends failed')

            # Add to daily summary
            self.daily_summary['total_found'] += 1
            self.daily_summary['opportunities'].append(opportunity)

            if opportunity.get('confidence_label') == 'HIGH':
                self.daily_summary['high_confidence'] += 1

            profit = opportunity.get('guaranteed_profit', 0)
            self.daily_summary['total_profit'] += profit

        except Exception as e:
            logger.error(f'Error sending opportunity alert: {e}')

    async def _send_to_premium_subscribers(self, opportunity: Dict):
        """
        Send direct message to premium subscribers

        Args:
            opportunity: Arbitrage opportunity dictionary
        """
        try:
            # This would iterate through all subscribers from database
            # For now, logging the capability
            logger.debug(f'Premium subscriber direct messages ready for: {opportunity.get("event_name")}')

        except Exception as e:
            logger.error(f'Error sending to premium subscribers: {e}')

    async def send_daily_summary_to_channel(self, channel: discord.TextChannel):
        """
        Send daily summary to stats channel

        Args:
            channel: Discord channel to send summary to
        """
        try:
            if self.daily_summary['total_found'] == 0:
                logger.info('No opportunities found for daily summary')
                return

            summary_data = {
                'total_found': self.daily_summary['total_found'],
                'high_confidence': self.daily_summary['high_confidence'],
                'total_profit': self.daily_summary['total_profit'],
                'top_opportunity': None,
                'top_margin': 0,
                'top_profit': 0,
                'sports_breakdown': {}
            }

            # Find top opportunity
            if self.daily_summary['opportunities']:
                top_opp = max(
                    self.daily_summary['opportunities'],
                    key=lambda x: x.get('profit_margin', 0)
                )
                summary_data['top_opportunity'] = top_opp.get('event_name', 'Unknown')
                summary_data['top_margin'] = top_opp.get('profit_margin', 0)
                summary_data['top_profit'] = top_opp.get('guaranteed_profit', 0)

                # Build sports breakdown
                sports = {}
                for opp in self.daily_summary['opportunities']:
                    sport = opp.get('sport', 'Unknown')
                    sports[sport] = sports.get(sport, 0) + 1
                summary_data['sports_breakdown'] = sports

            # Send summary
            await self.notifier.send_daily_summary(channel, summary_data)
            logger.info('Sent daily summary to stats channel')

            # Reset daily summary
            self.daily_summary = {
                'total_found': 0,
                'high_confidence': 0,
                'total_profit': 0,
                'opportunities': []
            }

        except Exception as e:
            logger.error(f'Error sending daily summary: {e}')

    async def verify_user_subscription(self, user: discord.User) -> bool:
        """
        Verify user has active subscription

        Args:
            user: Discord user to verify

        Returns:
            True if user has active subscription, False otherwise
        """
        try:
            if not self.user_manager:
                return False

            return await self.user_manager.has_subscription(user.id)

        except Exception as e:
            logger.error(f'Error verifying subscription: {e}')
            return False

    async def activate_trial_for_user(self, user: discord.User, subscriber_role: discord.Role) -> bool:
        """
        Activate trial subscription for a user

        Args:
            user: Discord user to activate trial for
            subscriber_role: Role to assign

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.user_manager:
                return False

            # Start trial
            result = await self.user_manager.start_trial(user, trial_days=7)

            if result:
                # Assign role
                await self.user_manager.assign_subscriber_role(user, subscriber_role)

                # Send welcome message
                await self.user_manager.send_welcome_dm(user, is_trial=True)

                logger.info(f'Activated trial for user {user.id}')
                return True

            return False

        except Exception as e:
            logger.error(f'Error activating trial: {e}')
            return False

    async def activate_subscription_for_user(self, user: discord.User, stripe_customer_id: str,
                                            stripe_subscription_id: str, subscriber_role: discord.Role) -> bool:
        """
        Activate paid subscription for a user

        Args:
            user: Discord user to activate subscription for
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            subscriber_role: Role to assign

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.user_manager:
                return False

            # Activate subscription
            result = await self.user_manager.activate_subscription(
                user, stripe_customer_id, stripe_subscription_id, subscriber_role
            )

            if result:
                # Send welcome message
                await self.user_manager.send_welcome_dm(user, is_trial=False)
                logger.info(f'Activated subscription for user {user.id}')
                return True

            return False

        except Exception as e:
            logger.error(f'Error activating subscription: {e}')
            return False

    async def cancel_subscription_for_user(self, user: discord.User, subscriber_role: discord.Role) -> bool:
        """
        Cancel subscription for a user

        Args:
            user: Discord user to cancel subscription for
            subscriber_role: Role to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.user_manager:
                return False

            result = await self.user_manager.cancel_subscription(user, subscriber_role)

            if result:
                logger.info(f'Cancelled subscription for user {user.id}')

            return result

        except Exception as e:
            logger.error(f'Error cancelling subscription: {e}')
            return False

    async def get_subscriber_stats(self) -> Dict:
        """
        Get subscriber statistics

        Returns:
            Dictionary with subscriber stats
        """
        try:
            if not self.user_manager:
                return {}

            return await self.user_manager.get_revenue_stats()

        except Exception as e:
            logger.error(f'Error getting subscriber stats: {e}')
            return {}

    async def sync_subscriber_roles(self, subscriber_role: discord.Role) -> int:
        """
        Sync subscriber roles with subscription status

        Args:
            subscriber_role: Subscriber role to manage

        Returns:
            Number of users updated
        """
        try:
            if not self.user_manager:
                return 0

            updated = await self.user_manager.sync_roles_with_subscriptions(subscriber_role)
            logger.info(f'Synced subscriber roles: {updated} users updated')
            return updated

        except Exception as e:
            logger.error(f'Error syncing roles: {e}')
            return 0

    async def send_opportunity_alert(self, opportunity: Dict):
        """
        Integrated alert sender for use by arbitrage_finder

        Args:
            opportunity: Opportunity dictionary from arbitrage_finder
        """
        # Determine priority based on profit margin
        profit_margin = opportunity.get('profit_margin', 0)
        is_high_priority = profit_margin > 5.0

        # Send to Discord
        await self.send_opportunity_to_subscribers(opportunity, is_high_priority)

    async def handle_stripe_webhook(self, event_data: Dict) -> bool:
        """
        Handle Stripe webhook events

        Args:
            event_data: Webhook event data from Stripe

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            event_type = event_data.get('type')

            if event_type == 'subscription_created':
                logger.info(f'New subscription: {event_data.get("subscription_id")}')
                # Could send notification to admin channel
                return True

            elif event_type == 'subscription_cancelled':
                logger.info(f'Subscription cancelled: {event_data.get("subscription_id")}')
                return True

            elif event_type == 'payment_succeeded':
                logger.info(f'Payment received: ${event_data.get("amount") / 100}')
                return True

            elif event_type == 'payment_failed':
                logger.warning(f'Payment failed: {event_data.get("invoice_id")}')
                return True

            else:
                logger.debug(f'Unhandled webhook event: {event_type}')
                return True

        except Exception as e:
            logger.error(f'Error handling webhook: {e}')
            return False


class DiscordBotIntegration(commands.Cog):
    """Cog for Discord integration commands and background tasks"""

    def __init__(self, bot: commands.Bot, integration_manager: DiscordIntegrationManager):
        self.bot = bot
        self.integration_manager = integration_manager
        self.daily_summary_task.start()

    @tasks.loop(hours=24)
    async def daily_summary_task(self):
        """Send daily summary at midnight UTC"""
        try:
            # Get stats channel
            stats_channel_id = int(os.getenv('STATS_CHANNEL_ID', '0'))
            if stats_channel_id:
                channel = self.bot.get_channel(stats_channel_id)
                if channel:
                    await self.integration_manager.send_daily_summary_to_channel(channel)
        except Exception as e:
            logger.error(f'Error in daily summary task: {e}')

    @daily_summary_task.before_loop
    async def before_daily_summary(self):
        """Wait until bot is ready"""
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.daily_summary_task.cancel()


# Convenience function for integration
async def setup_discord_integration(bot: commands.Bot, arbitrage_finder: ArbitrageFinder) -> DiscordIntegrationManager:
    """
    Set up Discord integration for arbitrage finder

    Args:
        bot: Discord bot instance
        arbitrage_finder: ArbitrageFinder instance

    Returns:
        DiscordIntegrationManager instance
    """
    manager = DiscordIntegrationManager(bot, arbitrage_finder)

    # Initialize with bot's guild (first guild the bot is in)
    if bot.guilds:
        await manager.initialize(bot.guilds[0])

    # Add integration cog
    await bot.add_cog(DiscordBotIntegration(bot, manager))

    logger.info('Discord integration setup complete')
    return manager


# Import for access
import os
