"""
User Manager for Arbitrage Finder Discord Bot
Handles user profiles, roles, and access control
"""

import discord
import logging
from typing import Optional, Dict, List
from datetime import datetime
from subscription_manager import SubscriptionManager, SubscriptionStatus

logger = logging.getLogger(__name__)


class UserManager:
    """Manages Discord user profiles and access control"""

    def __init__(self, guild: discord.Guild, subscription_manager: SubscriptionManager):
        self.guild = guild
        self.subscription_manager = subscription_manager

    async def get_or_create_user(self, user: discord.User, email: str = None) -> bool:
        """
        Get or create a user in the system

        Args:
            user: Discord user object
            email: Optional email address

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.subscription_manager.create_user(
                user.id,
                user.name,
                email
            )
            logger.info(f'Created/retrieved user {user.id} ({user.name})')
            return result
        except Exception as e:
            logger.error(f'Error creating user: {e}')
            return False

    async def assign_subscriber_role(self, user: discord.User, role: discord.Role) -> bool:
        """
        Assign subscriber role to a user

        Args:
            user: Discord user object
            role: Subscriber role

        Returns:
            True if successful, False otherwise
        """
        try:
            member = self.guild.get_member(user.id)
            if member:
                await member.add_roles(role)
                logger.info(f'Assigned subscriber role to {user.id}')
                return True
            else:
                logger.warning(f'User {user.id} not found in guild')
                return False
        except discord.Forbidden:
            logger.error(f'Permission denied assigning role to {user.id}')
            return False
        except Exception as e:
            logger.error(f'Error assigning role: {e}')
            return False

    async def remove_subscriber_role(self, user: discord.User, role: discord.Role) -> bool:
        """
        Remove subscriber role from a user

        Args:
            user: Discord user object
            role: Subscriber role

        Returns:
            True if successful, False otherwise
        """
        try:
            member = self.guild.get_member(user.id)
            if member:
                await member.remove_roles(role)
                logger.info(f'Removed subscriber role from {user.id}')
                return True
            else:
                logger.warning(f'User {user.id} not found in guild')
                return False
        except discord.Forbidden:
            logger.error(f'Permission denied removing role from {user.id}')
            return False
        except Exception as e:
            logger.error(f'Error removing role: {e}')
            return False

    async def has_subscription(self, user_id: int) -> bool:
        """
        Check if user has active subscription

        Args:
            user_id: Discord user ID

        Returns:
            True if user has active subscription, False otherwise
        """
        subscription = await self.subscription_manager.check_subscription(user_id)
        return subscription is not None

    async def get_user_subscription_info(self, user_id: int) -> Optional[Dict]:
        """
        Get user subscription information

        Args:
            user_id: Discord user ID

        Returns:
            Dictionary with subscription info or None
        """
        return await self.subscription_manager.check_subscription(user_id)

    async def start_trial(self, user: discord.User, trial_days: int = 7) -> bool:
        """
        Start a trial subscription for user

        Args:
            user: Discord user object
            trial_days: Duration of trial

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create user if doesn't exist
            await self.get_or_create_user(user)

            # Start trial
            result = await self.subscription_manager.start_trial(user.id, trial_days)
            if result:
                logger.info(f'Started trial for user {user.id}')
            return result
        except Exception as e:
            logger.error(f'Error starting trial: {e}')
            return False

    async def activate_subscription(self, user: discord.User, stripe_customer_id: str,
                                   stripe_subscription_id: str, role: discord.Role) -> bool:
        """
        Activate a paid subscription for user

        Args:
            user: Discord user object
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            role: Subscriber role to assign

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create user if doesn't exist
            await self.get_or_create_user(user)

            # Add subscription
            result = await self.subscription_manager.add_subscription(
                user.id,
                stripe_customer_id,
                stripe_subscription_id
            )

            if result:
                # Assign role
                await self.assign_subscriber_role(user, role)
                logger.info(f'Activated subscription for user {user.id}')

            return result
        except Exception as e:
            logger.error(f'Error activating subscription: {e}')
            return False

    async def cancel_subscription(self, user: discord.User, role: discord.Role) -> bool:
        """
        Cancel subscription and remove access

        Args:
            user: Discord user object
            role: Subscriber role to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            # Cancel subscription
            result = await self.subscription_manager.cancel_subscription(user.id)

            if result:
                # Remove role
                await self.remove_subscriber_role(user, role)
                logger.info(f'Cancelled subscription for user {user.id}')

            return result
        except Exception as e:
            logger.error(f'Error cancelling subscription: {e}')
            return False

    async def verify_access(self, user: discord.User, required_role: discord.Role) -> bool:
        """
        Verify user has access to premium features

        Args:
            user: Discord user object
            required_role: Required subscriber role

        Returns:
            True if user has access, False otherwise
        """
        try:
            member = self.guild.get_member(user.id)
            if not member:
                return False

            # Check if user has role
            if required_role in member.roles:
                # Verify subscription is still valid
                has_active_sub = await self.has_subscription(user.id)
                return has_active_sub

            return False
        except Exception as e:
            logger.error(f'Error verifying access: {e}')
            return False

    async def get_subscriber_count(self) -> int:
        """
        Get count of active subscribers

        Returns:
            Number of active subscribers
        """
        try:
            stats = await self.subscription_manager.get_subscription_stats()
            return stats.get('active_subscriptions', 0)
        except Exception as e:
            logger.error(f'Error getting subscriber count: {e}')
            return 0

    async def get_revenue_stats(self) -> Dict:
        """
        Get revenue statistics

        Returns:
            Dictionary with revenue stats
        """
        try:
            stats = await self.subscription_manager.get_subscription_stats()
            return {
                'active_subscriptions': stats.get('active_subscriptions', 0),
                'trial_subscriptions': stats.get('trial_subscriptions', 0),
                'total_revenue': stats.get('total_revenue', 0),
                'mrr': stats.get('mrr', 0)
            }
        except Exception as e:
            logger.error(f'Error getting revenue stats: {e}')
            return {}

    async def sync_roles_with_subscriptions(self, subscriber_role: discord.Role):
        """
        Sync Discord roles with subscription status
        (Remove role from users with expired subscriptions)

        Args:
            subscriber_role: Subscriber role to manage

        Returns:
            Number of users updated
        """
        try:
            updated_count = 0

            # Get all members with subscriber role
            for member in self.guild.members:
                if subscriber_role not in member.roles:
                    continue

                # Check if they still have active subscription
                has_active_sub = await self.has_subscription(member.id)

                if not has_active_sub:
                    # Remove role
                    await self.remove_subscriber_role(member, subscriber_role)
                    updated_count += 1
                    logger.info(f'Removed role from {member.id} (expired subscription)')

            return updated_count

        except Exception as e:
            logger.error(f'Error syncing roles: {e}')
            return 0

    async def send_welcome_dm(self, user: discord.User, is_trial: bool = False) -> bool:
        """
        Send welcome message to new subscriber

        Args:
            user: Discord user object
            is_trial: Whether this is a trial signup

        Returns:
            True if successful, False otherwise
        """
        try:
            embed = discord.Embed(
                title='🎉 Welcome to Arbitrage Finder Premium!',
                color=discord.Color.green()
            )

            if is_trial:
                embed.add_field(
                    name='🎁 7-Day Free Trial Started',
                    value='You have full access to all premium features for 7 days',
                    inline=False
                )
            else:
                embed.add_field(
                    name='✅ Subscription Activated',
                    value='Your subscription is now active. Enjoy unlimited access!',
                    inline=False
                )

            embed.add_field(
                name='📚 Getting Started',
                value='1. Check <#getting-started> for tutorials\n'
                      '2. Join <#premium-opportunities> for alerts\n'
                      '3. Use `/stats` to track opportunities',
                inline=False
            )

            embed.add_field(
                name='🆘 Need Help?',
                value='Post in <#support> or DM an admin',
                inline=False
            )

            embed.set_footer(text='Happy arbitrage hunting!')

            await user.send(embed=embed)
            return True

        except discord.Forbidden:
            logger.warning(f'Could not send DM to {user.id} (DMs disabled)')
            return False
        except Exception as e:
            logger.error(f'Error sending welcome DM: {e}')
            return False

    async def send_expiration_warning(self, user: discord.User, days_remaining: int) -> bool:
        """
        Send subscription expiration warning

        Args:
            user: Discord user object
            days_remaining: Days until expiration

        Returns:
            True if successful, False otherwise
        """
        try:
            embed = discord.Embed(
                title='⚠️ Subscription Expiring Soon',
                color=discord.Color.orange()
            )

            embed.add_field(
                name='Days Remaining',
                value=f'{days_remaining} days',
                inline=False
            )

            embed.add_field(
                name='Action Required',
                value='Renew your subscription to maintain access',
                inline=False
            )

            embed.add_field(
                name='Renew Now',
                value='Use `/subscribe` to renew your subscription',
                inline=False
            )

            await user.send(embed=embed)
            return True

        except discord.Forbidden:
            logger.warning(f'Could not send DM to {user.id} (DMs disabled)')
            return False
        except Exception as e:
            logger.error(f'Error sending expiration warning: {e}')
            return False
