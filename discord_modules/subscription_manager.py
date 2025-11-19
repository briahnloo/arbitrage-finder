"""
Subscription Manager for Arbitrage Finder Premium Service
Handles user subscriptions, trials, and access control
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class SubscriptionStatus(Enum):
    """Subscription status enum"""
    TRIAL = 'trial'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    SUSPENDED = 'suspended'


class SubscriptionManager:
    """Manages user subscriptions and trial periods"""

    def __init__(self, db_path: str = 'arbitrage_finder.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables for subscriptions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    discord_id INTEGER PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER NOT NULL,
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    status TEXT DEFAULT 'active',
                    trial_start TIMESTAMP,
                    trial_end TIMESTAMP,
                    billing_start TIMESTAMP,
                    billing_end TIMESTAMP,
                    payment_id TEXT,
                    amount_paid REAL DEFAULT 20.00,
                    auto_renew BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                )
            ''')

            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    discord_id INTEGER PRIMARY KEY,
                    min_profit_threshold REAL DEFAULT 2.0,
                    preferred_sports TEXT DEFAULT 'all',
                    alert_frequency TEXT DEFAULT 'realtime',
                    notification_channels TEXT DEFAULT 'discord',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                )
            ''')

            # Billing history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS billing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER NOT NULL,
                    amount REAL,
                    billing_date TIMESTAMP,
                    payment_id TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                )
            ''')

            # Premium entitlements table (one-time purchase, lifetime access)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS premium_entitlements (
                    discord_id INTEGER PRIMARY KEY,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lifetime BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                )
            ''')

            conn.commit()
            logger.info('Database initialized successfully')

        except sqlite3.Error as e:
            logger.error(f'Database initialization error: {e}')
            raise

        finally:
            conn.close()

    async def create_user(self, discord_id: int, username: str, email: str = None) -> bool:
        """
        Create a new user

        Args:
            discord_id: Discord user ID
            username: Discord username
            email: User email (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'INSERT OR IGNORE INTO users (discord_id, username, email) VALUES (?, ?, ?)',
                (discord_id, username, email)
            )

            conn.commit()
            logger.info(f'Created user {discord_id} ({username})')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error creating user: {e}')
            return False
        finally:
            conn.close()

    async def start_trial(self, discord_id: int, trial_days: int = 7) -> bool:
        """
        Start a trial subscription for a user

        Args:
            discord_id: Discord user ID
            trial_days: Duration of trial in days

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            trial_start = datetime.now()
            trial_end = trial_start + timedelta(days=trial_days)

            cursor.execute(
                '''INSERT INTO subscriptions
                   (discord_id, status, trial_start, trial_end)
                   VALUES (?, ?, ?, ?)''',
                (discord_id, SubscriptionStatus.TRIAL.value, trial_start, trial_end)
            )

            conn.commit()
            logger.info(f'Started trial for user {discord_id} ({trial_days} days)')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error starting trial: {e}')
            return False
        finally:
            conn.close()

    async def add_subscription(self, discord_id: int, stripe_customer_id: str,
                             stripe_subscription_id: str, billing_end: datetime = None) -> bool:
        """
        Add a paid subscription for a user

        Args:
            discord_id: Discord user ID
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            billing_end: Subscription end date

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if not billing_end:
                billing_end = datetime.now() + timedelta(days=30)

            cursor.execute(
                '''INSERT INTO subscriptions
                   (discord_id, stripe_customer_id, stripe_subscription_id, status,
                    billing_start, billing_end)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (discord_id, stripe_customer_id, stripe_subscription_id,
                 SubscriptionStatus.ACTIVE.value, datetime.now(), billing_end)
            )

            conn.commit()
            logger.info(f'Added subscription for user {discord_id}')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error adding subscription: {e}')
            return False
        finally:
            conn.close()

    async def check_subscription(self, discord_id: int) -> Optional[Dict]:
        """
        Check if user has active subscription

        Args:
            discord_id: Discord user ID

        Returns:
            Dictionary with subscription info or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                '''SELECT * FROM subscriptions
                   WHERE discord_id = ?
                   ORDER BY created_at DESC
                   LIMIT 1''',
                (discord_id,)
            )

            row = cursor.fetchone()
            if not row:
                return None

            subscription = dict(row)
            status = subscription['status']

            # Check if trial expired
            if status == SubscriptionStatus.TRIAL.value and subscription['trial_end']:
                if datetime.fromisoformat(subscription['trial_end']) < datetime.now():
                    return None

            # Check if billing expired
            if status == SubscriptionStatus.ACTIVE.value and subscription['billing_end']:
                if datetime.fromisoformat(subscription['billing_end']) < datetime.now():
                    return None

            return subscription

        except sqlite3.Error as e:
            logger.error(f'Error checking subscription: {e}')
            return None
        finally:
            conn.close()

    async def cancel_subscription(self, discord_id: int) -> bool:
        """
        Cancel a user's subscription

        Args:
            discord_id: Discord user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                '''UPDATE subscriptions
                   SET status = ?, updated_at = ?
                   WHERE discord_id = ? AND status != ?''',
                (SubscriptionStatus.CANCELLED.value, datetime.now(), discord_id,
                 SubscriptionStatus.CANCELLED.value)
            )

            conn.commit()
            logger.info(f'Cancelled subscription for user {discord_id}')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error cancelling subscription: {e}')
            return False
        finally:
            conn.close()

    async def update_preferences(self, discord_id: int, preferences: Dict) -> bool:
        """
        Update user preferences

        Args:
            discord_id: Discord user ID
            preferences: Dictionary of preference settings

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if preferences exist
            cursor.execute('SELECT * FROM user_preferences WHERE discord_id = ?', (discord_id,))
            exists = cursor.fetchone() is not None

            if exists:
                update_fields = ', '.join([f'{k} = ?' for k in preferences.keys()])
                values = list(preferences.values()) + [datetime.now(), discord_id]
                cursor.execute(
                    f'''UPDATE user_preferences
                       SET {update_fields}, updated_at = ?
                       WHERE discord_id = ?''',
                    values
                )
            else:
                columns = ', '.join(preferences.keys())
                placeholders = ', '.join(['?' for _ in preferences])
                values = list(preferences.values())
                cursor.execute(
                    f'''INSERT INTO user_preferences (discord_id, {columns})
                       VALUES (?, {placeholders})''',
                    [discord_id] + values
                )

            conn.commit()
            logger.info(f'Updated preferences for user {discord_id}')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error updating preferences: {e}')
            return False
        finally:
            conn.close()

    async def get_preferences(self, discord_id: int) -> Optional[Dict]:
        """
        Get user preferences

        Args:
            discord_id: Discord user ID

        Returns:
            Dictionary of preferences or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                'SELECT * FROM user_preferences WHERE discord_id = ?',
                (discord_id,)
            )

            row = cursor.fetchone()
            return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error(f'Error retrieving preferences: {e}')
            return None
        finally:
            conn.close()

    async def record_payment(self, discord_id: int, amount: float, payment_id: str) -> bool:
        """
        Record a payment transaction

        Args:
            discord_id: Discord user ID
            amount: Payment amount
            payment_id: Stripe payment ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                '''INSERT INTO billing_history (discord_id, amount, billing_date, payment_id)
                   VALUES (?, ?, ?, ?)''',
                (discord_id, amount, datetime.now(), payment_id)
            )

            conn.commit()
            logger.info(f'Recorded payment for user {discord_id}: ${amount}')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error recording payment: {e}')
            return False
        finally:
            conn.close()

    async def get_subscription_stats(self) -> Dict:
        """
        Get overall subscription statistics

        Returns:
            Dictionary with subscription stats
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status = ?',
                          (SubscriptionStatus.ACTIVE.value,))
            active_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status = ?',
                          (SubscriptionStatus.TRIAL.value,))
            trial_count = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(amount) FROM billing_history')
            total_revenue = cursor.fetchone()[0] or 0

            return {
                'active_subscriptions': active_count,
                'trial_subscriptions': trial_count,
                'total_revenue': total_revenue,
                'mrr': active_count * 20.0  # Monthly recurring revenue
            }

        except sqlite3.Error as e:
            logger.error(f'Error retrieving stats: {e}')
            return {}
        finally:
            conn.close()

    async def cleanup_expired_trials(self) -> int:
        """
        Clean up expired trial subscriptions

        Returns:
            Number of trials expired
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                '''UPDATE subscriptions
                   SET status = ?
                   WHERE status = ? AND trial_end < ?''',
                (SubscriptionStatus.EXPIRED.value, SubscriptionStatus.TRIAL.value, datetime.now())
            )

            expired_count = cursor.rowcount
            conn.commit()

            if expired_count > 0:
                logger.info(f'Cleaned up {expired_count} expired trials')

            return expired_count

        except sqlite3.Error as e:
            logger.error(f'Error cleaning up trials: {e}')
            return 0
        finally:
            conn.close()

    async def is_premium_user(self, discord_id: int) -> bool:
        """
        Check if user has active lifetime premium

        Args:
            discord_id: Discord user ID

        Returns:
            True if user has lifetime premium, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT is_active FROM premium_entitlements WHERE discord_id = ? AND lifetime = 1',
                (discord_id,)
            )
            result = cursor.fetchone()
            conn.close()

            return result is not None and result[0]

        except sqlite3.Error as e:
            logger.error(f'Error checking premium status: {e}')
            return False

    async def grant_lifetime_premium(self, discord_id: int) -> bool:
        """
        Grant lifetime premium access to user

        Args:
            discord_id: Discord user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # First ensure user exists
            await self.create_user(discord_id, f"User_{discord_id}")

            # Insert or update premium entitlement
            cursor.execute('''
                INSERT OR REPLACE INTO premium_entitlements
                (discord_id, lifetime, is_active)
                VALUES (?, 1, 1)
            ''', (discord_id,))

            conn.commit()
            logger.info(f'Granted lifetime premium to user {discord_id}')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error granting premium: {e}')
            return False
        finally:
            conn.close()

    async def revoke_premium(self, discord_id: int) -> bool:
        """
        Revoke premium access from user

        Args:
            discord_id: Discord user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'UPDATE premium_entitlements SET is_active = 0 WHERE discord_id = ?',
                (discord_id,)
            )

            conn.commit()
            logger.info(f'Revoked premium for user {discord_id}')
            return True

        except sqlite3.Error as e:
            logger.error(f'Error revoking premium: {e}')
            return False
        finally:
            conn.close()

    async def get_all_premium_users(self) -> List[int]:
        """
        Get list of all active premium users

        Returns:
            List of discord_ids with active lifetime premium
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT discord_id FROM premium_entitlements WHERE is_active = 1 AND lifetime = 1'
            )
            results = cursor.fetchall()
            conn.close()

            return [row[0] for row in results]

        except sqlite3.Error as e:
            logger.error(f'Error fetching premium users: {e}')
            return []
