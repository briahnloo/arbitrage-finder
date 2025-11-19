"""
Discord Notifier for Arbitrage Finder
Sends formatted embed messages for arbitrage opportunities to Discord channels
"""

import sys
from pathlib import Path
import importlib.util

sys.path.insert(0, str(Path(__file__).parent.parent))

# Get discord.py from site-packages, bypassing local discord/ directory
spec = importlib.util.find_spec('discord', package=None)
if spec and spec.origin and 'site-packages' in spec.origin:
    import importlib
    discord = importlib.import_module('discord')
    sys.modules['discord'] = discord
else:
    # Fallback
    import discord
    sys.modules['discord'] = discord

import logging
from typing import Dict, Optional, List
from datetime import datetime
from src.utils import format_currency, format_timestamp, get_sport_display_name

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Handles sending formatted notifications to Discord"""

    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.rate_limit_cache = {}

    async def send_opportunity_alert(self, channel: discord.TextChannel, opportunity: Dict,
                                    is_premium: bool = False) -> bool:
        """
        Send a formatted opportunity alert to Discord

        Args:
            channel: Discord channel to send to
            opportunity: Opportunity dictionary
            is_premium: Whether this is for premium subscribers

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check rate limit (max 1 alert per opportunity per minute)
            opp_key = f"{opportunity.get('event_name')}_{opportunity.get('sport')}"
            if opp_key in self.rate_limit_cache:
                logger.debug(f'Rate limited alert for {opp_key}')
                return False

            # Create embed
            embed = await self._create_opportunity_embed(opportunity, is_premium)

            # Send to channel
            await channel.send(embed=embed)
            logger.info(f'Sent alert to {channel.name}: {opp_key}')

            # Add to rate limit cache
            self.rate_limit_cache[opp_key] = True

            return True

        except discord.Forbidden:
            logger.error(f'Permission denied sending to {channel.name}')
            return False
        except Exception as e:
            logger.error(f'Error sending alert: {e}')
            return False

    async def send_daily_summary(self, channel: discord.TextChannel,
                                 summary_data: Dict) -> bool:
        """
        Send daily summary to stats channel

        Args:
            channel: Discord channel to send to
            summary_data: Summary statistics

        Returns:
            True if successful, False otherwise
        """
        try:
            embed = discord.Embed(
                title='📊 Daily Arbitrage Summary',
                color=discord.Color.blue()
            )

            # Statistics
            embed.add_field(
                name='📈 Opportunities Found',
                value=str(summary_data.get('total_found', 0)),
                inline=True
            )

            embed.add_field(
                name='🟢 High Confidence',
                value=str(summary_data.get('high_confidence', 0)),
                inline=True
            )

            embed.add_field(
                name='💰 Total Potential Profit',
                value=format_currency(summary_data.get('total_profit', 0)),
                inline=True
            )

            # Top opportunity
            if summary_data.get('top_opportunity'):
                embed.add_field(
                    name='🥇 Top Opportunity',
                    value=f"**{summary_data.get('top_opportunity')}**\n"
                          f"Margin: {summary_data.get('top_margin', 0):.2f}%\n"
                          f"Potential Profit: {format_currency(summary_data.get('top_profit', 0))}",
                    inline=False
                )

            # Sport breakdown
            sports = summary_data.get('sports_breakdown', {})
            if sports:
                sport_text = '\n'.join([f"{k}: {v}" for k, v in sports.items()])
                embed.add_field(
                    name='⚽ Sport Breakdown',
                    value=sport_text,
                    inline=False
                )

            embed.set_footer(text='Arbitrage Finder Premium | Daily Report')
            embed.timestamp = datetime.now()

            await channel.send(embed=embed)
            logger.info(f'Sent summary to {channel.name}')
            return True

        except Exception as e:
            logger.error(f'Error sending summary: {e}')
            return False

    async def send_weekly_stats(self, channel: discord.TextChannel,
                               weekly_stats: Dict) -> bool:
        """
        Send weekly statistics report

        Args:
            channel: Discord channel to send to
            weekly_stats: Weekly statistics dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            embed = discord.Embed(
                title='📊 Weekly Arbitrage Report',
                color=discord.Color.blue()
            )

            embed.add_field(
                name='Total Opportunities',
                value=str(weekly_stats.get('total_opportunities', 0)),
                inline=True
            )

            embed.add_field(
                name='Converted Opportunities',
                value=str(weekly_stats.get('converted', 0)),
                inline=True
            )

            embed.add_field(
                name='Conversion Rate',
                value=f"{weekly_stats.get('conversion_rate', 0):.1f}%",
                inline=True
            )

            embed.add_field(
                name='Total Potential Profit',
                value=format_currency(weekly_stats.get('total_profit', 0)),
                inline=True
            )

            embed.add_field(
                name='Average Profit Margin',
                value=f"{weekly_stats.get('avg_margin', 0):.2f}%",
                inline=True
            )

            embed.add_field(
                name='ROI',
                value=f"{weekly_stats.get('roi', 0):.1f}%",
                inline=True
            )

            # Top sports
            top_sports = weekly_stats.get('top_sports', {})
            if top_sports:
                sport_text = '\n'.join([f"{k}: {v}" for k, v in top_sports.items()])
                embed.add_field(
                    name='🏆 Top Sports',
                    value=sport_text,
                    inline=False
                )

            embed.set_footer(text='Arbitrage Finder Premium | Weekly Report')
            embed.timestamp = datetime.now()

            await channel.send(embed=embed)
            logger.info(f'Sent weekly stats to {channel.name}')
            return True

        except Exception as e:
            logger.error(f'Error sending weekly stats: {e}')
            return False

    async def send_subscriber_alert(self, user: discord.User, opportunity: Dict) -> bool:
        """
        Send direct message alert to subscriber

        Args:
            user: Discord user
            opportunity: Opportunity dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            embed = await self._create_opportunity_embed(opportunity, is_premium=True)
            embed.title = f"🎯 Premium Alert: {opportunity.get('event_name', 'Arbitrage')}"

            await user.send(embed=embed)
            logger.info(f'Sent premium alert to {user.id}')
            return True

        except discord.Forbidden:
            logger.warning(f'Could not DM {user.id} (DMs disabled)')
            return False
        except Exception as e:
            logger.error(f'Error sending subscriber alert: {e}')
            return False

    async def send_error_notification(self, channel: discord.TextChannel, error_msg: str,
                                     error_details: str = None) -> bool:
        """
        Send error notification to admin channel

        Args:
            channel: Discord channel to send to
            error_msg: Error message
            error_details: Detailed error information

        Returns:
            True if successful, False otherwise
        """
        try:
            embed = discord.Embed(
                title='⚠️ System Error',
                description=error_msg,
                color=discord.Color.red()
            )

            if error_details:
                embed.add_field(
                    name='Details',
                    value=f'```{error_details}```',
                    inline=False
                )

            embed.timestamp = datetime.now()

            await channel.send(embed=embed)
            logger.info(f'Sent error notification to {channel.name}')
            return True

        except Exception as e:
            logger.error(f'Error sending error notification: {e}')
            return False

    async def _create_opportunity_embed(self, opportunity: Dict, is_premium: bool = False) -> discord.Embed:
        """
        Create a formatted Discord embed for an opportunity

        Args:
            opportunity: Opportunity dictionary
            is_premium: Whether this is for premium display

        Returns:
            Discord embed object
        """
        # Color based on confidence
        confidence_label = opportunity.get('confidence_label', 'MEDIUM')
        if confidence_label == 'HIGH':
            color = discord.Color.green()
        elif confidence_label == 'MEDIUM':
            color = discord.Color.gold()
        else:
            color = discord.Color.red()

        # Create embed
        event_name = opportunity.get('event_name', 'Arbitrage Opportunity')
        embed = discord.Embed(
            title=f'🎯 {event_name}',
            color=color
        )

        # Event information
        sport_name = get_sport_display_name(opportunity.get('sport', 'Unknown'))
        event_time = format_timestamp(opportunity.get('commence_time', ''))
        market_type = opportunity.get('market', 'H2H').upper()

        embed.add_field(
            name='📌 Event Details',
            value=f'**Sport:** {sport_name}\n'
                  f'**Time:** {event_time}\n'
                  f'**Market:** {market_type}',
            inline=False
        )

        # Bet 1 information
        player_a = opportunity.get('player_a', 'Player A')
        bookmaker_a = opportunity.get('bookmaker_a', 'Unknown')
        odds_a = opportunity.get('odds_a', 0)
        stake_a = opportunity.get('stake_a', 0)
        return_a = stake_a * odds_a

        embed.add_field(
            name=f'💰 BET 1 - {player_a}',
            value=f'**Bookmaker:** {bookmaker_a}\n'
                  f'**Odds:** {odds_a:.2f}\n'
                  f'**Stake:** {format_currency(stake_a)}\n'
                  f'**If Wins:** {format_currency(return_a)}',
            inline=True
        )

        # Bet 2 information
        player_b = opportunity.get('player_b', 'Player B')
        bookmaker_b = opportunity.get('bookmaker_b', 'Unknown')
        odds_b = opportunity.get('odds_b', 0)
        stake_b = opportunity.get('stake_b', 0)
        return_b = stake_b * odds_b

        embed.add_field(
            name=f'💰 BET 2 - {player_b}',
            value=f'**Bookmaker:** {bookmaker_b}\n'
                  f'**Odds:** {odds_b:.2f}\n'
                  f'**Stake:** {format_currency(stake_b)}\n'
                  f'**If Wins:** {format_currency(return_b)}',
            inline=True
        )

        # Profit information
        profit = opportunity.get('guaranteed_profit', 0)
        margin = opportunity.get('profit_margin', 0)
        total_stake = opportunity.get('total_stake', 100)
        roi = (profit / total_stake * 100) if total_stake > 0 else 0

        embed.add_field(
            name='📊 Profit Summary',
            value=f'**Margin:** {margin:.2f}%\n'
                  f'**Investment:** {format_currency(total_stake)}\n'
                  f'**Guaranteed Profit:** {format_currency(profit)}\n'
                  f'**ROI:** {roi:.1f}%',
            inline=False
        )

        # Confidence and validation
        confidence = opportunity.get('confidence', 0)
        is_validated = opportunity.get('is_validated', False)
        validation_status = '✅ VERIFIED' if is_validated else '⚠️ Not Verified'

        embed.add_field(
            name='🎲 Confidence',
            value=f'{confidence_label} ({confidence:.0f}%)\n'
                  f'Validation: {validation_status}',
            inline=False
        )

        # Footer
        embed.set_footer(text='Arbitrage Finder Premium | Risk-free guaranteed profits')
        embed.timestamp = datetime.now()

        return embed

    def clear_rate_limit_cache(self):
        """Clear the rate limit cache"""
        self.rate_limit_cache.clear()
        logger.info('Cleared rate limit cache')
