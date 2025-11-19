#!/usr/bin/env python3
"""
Quick test script to verify premium model implementation
Tests: database setup, entitlement checking, granting, and revoking
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_premium_model():
    """Test the premium model implementation"""
    print("=" * 70)
    print("PREMIUM MODEL IMPLEMENTATION TEST")
    print("=" * 70)

    try:
        # Import subscription manager
        from discord.subscription_manager import SubscriptionManager
        print("\n✓ Successfully imported SubscriptionManager")

        # Initialize with test database
        test_db = 'test_premium.db'
        sub_manager = SubscriptionManager(db_path=test_db)
        print("✓ Initialized SubscriptionManager with test database")

        # Test 1: Grant premium to user
        test_user_id = 12345678
        print(f"\n[TEST 1] Granting lifetime premium to user {test_user_id}...")
        success = await sub_manager.grant_lifetime_premium(test_user_id)
        if success:
            print("✓ Successfully granted lifetime premium")
        else:
            print("✗ Failed to grant premium")
            return False

        # Test 2: Check if user is premium
        print(f"\n[TEST 2] Checking if user {test_user_id} is premium...")
        is_premium = await sub_manager.is_premium_user(test_user_id)
        if is_premium:
            print(f"✓ User {test_user_id} confirmed as premium user")
        else:
            print(f"✗ User {test_user_id} not recognized as premium")
            return False

        # Test 3: Grant premium to another user
        test_user_id_2 = 87654321
        print(f"\n[TEST 3] Granting lifetime premium to second user {test_user_id_2}...")
        success = await sub_manager.grant_lifetime_premium(test_user_id_2)
        if success:
            print(f"✓ Successfully granted premium to user {test_user_id_2}")
        else:
            print("✗ Failed to grant premium to second user")
            return False

        # Test 4: Get all premium users
        print(f"\n[TEST 4] Fetching all premium users...")
        premium_users = await sub_manager.get_all_premium_users()
        if premium_users:
            print(f"✓ Found {len(premium_users)} premium users: {premium_users}")
            if test_user_id in premium_users and test_user_id_2 in premium_users:
                print("✓ Both test users are in the list")
            else:
                print("✗ Not all test users found in premium list")
                return False
        else:
            print("✗ No premium users found")
            return False

        # Test 5: Revoke premium
        print(f"\n[TEST 5] Revoking premium from user {test_user_id}...")
        success = await sub_manager.revoke_premium(test_user_id)
        if success:
            print(f"✓ Successfully revoked premium from user {test_user_id}")
        else:
            print("✗ Failed to revoke premium")
            return False

        # Test 6: Verify revocation
        print(f"\n[TEST 6] Verifying user {test_user_id} is no longer premium...")
        is_premium = await sub_manager.is_premium_user(test_user_id)
        if not is_premium:
            print(f"✓ User {test_user_id} confirmed as non-premium after revocation")
        else:
            print(f"✗ User {test_user_id} still shows as premium after revocation")
            return False

        # Test 7: Verify other user still premium
        print(f"\n[TEST 7] Verifying user {test_user_id_2} still has premium...")
        is_premium = await sub_manager.is_premium_user(test_user_id_2)
        if is_premium:
            print(f"✓ User {test_user_id_2} still premium (not affected by revocation)")
        else:
            print(f"✗ User {test_user_id_2} lost premium unexpectedly")
            return False

        # Cleanup
        print(f"\n[CLEANUP] Removing test database...")
        if os.path.exists(test_db):
            os.remove(test_db)
            print("✓ Test database cleaned up")

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print("\nPremium Model Summary:")
        print("  • Database table created successfully")
        print("  • Grant lifetime premium: WORKING")
        print("  • Check premium status: WORKING")
        print("  • Get all premium users: WORKING")
        print("  • Revoke premium: WORKING")
        print("\nThe premium model is ready for production use!")

        return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_premium_model())
    sys.exit(0 if result else 1)
