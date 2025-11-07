<!-- a993ba6b-4afe-4b46-9850-d72d29c407b1 af56ece9-888f-4bb5-a7c5-886f1f9aac6d -->
# Discord Product Launch Plan - Arbitrage Finder

## Executive Summary

Transform the arbitrage finder into a premium Discord-based subscription service ($20/month) providing real-time arbitrage opportunities to subscribers. This plan covers technical improvements, Discord infrastructure, monetization, and community building.

## Phase 1: Technical Foundation (Weeks 1-3)

### 1.1 Discord Bot Integration

- Create Discord bot using discord.py library
- Implement bot commands: `/subscribe`, `/status`, `/stats`, `/help`
- Set up bot authentication and permissions
- Create embed messages for opportunity alerts (cleaner than console output)
- Add role-based access control (subscriber role management)

### 1.2 Notification System Overhaul

- Replace console alerts with Discord channel notifications
- Create dedicated Discord channels:
                                - `#alerts` - Real-time opportunity alerts
                                - `#premium-opportunities` - Top 5 opportunities (private to subscribers)
                                - `#stats` - Daily/weekly statistics
                                - `#support` - User support
- Implement rate limiting to prevent spam
- Add formatting for Discord embeds (rich, visual alerts)

### 1.3 User Management System

- Create user database table (discord_id, subscription_status, subscription_date, payment_id)
- Implement subscription verification
- Add subscription expiration tracking
- Create admin commands for manual subscription management
- Track user activity and engagement

### 1.4 Enhanced Opportunity Filtering

- Add user preference settings (sport preferences, minimum profit threshold)
- Implement priority queuing (premium subscribers get alerts first)
- Add opportunity confidence scoring
- Create personalized alert frequency (high/medium/low priority)

## Phase 2: Payment & Access Control (Weeks 4-5)

### 2.1 Payment Processing Integration

- Choose payment provider (Stripe, PayPal, or Discord-native)
- Implement webhook handlers for payment verification
- Create subscription management system
- Add automatic role assignment on payment
- Handle subscription renewals and cancellations

### 2.2 Access Control System

- Implement role-based permissions
- Create subscriber role with channel access
- Add trial period functionality (7-day free trial)
- Implement grace period for expired subscriptions
- Create admin dashboard for subscription management

### 2.3 Security & Anti-Fraud

- Implement Discord user verification
- Add rate limiting for API calls per user
- Create audit logging system
- Implement duplicate account detection
- Add IP-based access control (optional)

## Phase 3: Discord Community Setup (Weeks 6-7)

### 3.1 Server Structure

```
📋 Server Rules
💰 Subscription Info
📊 General Channels
  - #welcome
  - #announcements
  - #introductions
  - #general-chat
  - #questions-help
📈 Trading Channels (Subscriber Only)
  - #alerts (real-time)
  - #premium-opportunities (top 5)
  - #stats (daily/weekly)
  - #trade-log (user sharing)
🎓 Educational Channels
  - #getting-started
  - #arbitrage-guide
  - #bookmaker-reviews
  - #strategy-discussion
💬 Community Channels
  - #success-stories
  - #support
  - #feedback
```

### 3.2 Bot Commands

- `/subscribe` - Show subscription options and pricing
- `/status` - Check subscription status
- `/stats` - View personal statistics
- `/preferences` - Set alert preferences
- `/help` - Command help
- `/feedback` - Submit feedback (admin only)

### 3.3 Community Engagement Features

- Daily opportunity summary posts
- Weekly statistics and performance reports
- Success story sharing (user testimonials)
- Educational content series
- Q&A sessions with admin

## Phase 4: Product Enhancement (Weeks 8-10)

### 4.1 Web Dashboard (Optional - Phase 2)

- User login portal
- Subscription management interface
- Historical opportunity tracking
- Performance analytics dashboard
- Custom alert settings UI

### 4.2 Enhanced Features

- Mobile notifications (Discord mobile app)
- Email backup alerts (optional)
- SMS alerts (premium tier option)
- Historical data export
- API access for advanced users (future)

### 4.3 Analytics & Reporting

- Track opportunity frequency
- Calculate average profit margins
- Monitor user engagement
- Generate monthly reports
- Success rate tracking

## Phase 5: Marketing & Launch (Weeks 11-12)

### 5.1 Pre-Launch

- Create landing page with Discord invite
- Set up social media presence (Twitter/X, Reddit)
- Write educational content about arbitrage betting
- Build email list of interested users
- Create demo videos showing system in action

### 5.2 Launch Strategy

- Soft launch to beta testers (free for 1 month)
- Collect feedback and iterate
- Official launch with promotional pricing ($15 first month)
- Create referral program (refer 3 friends, get 1 month free)
- Partner with betting content creators

### 5.3 Growth Tactics

- Reddit marketing (r/sportsbetting, r/arbitragebetting)
- Twitter/X content marketing
- YouTube tutorial videos
- Discord server partnerships
- Affiliate program for influencers

## Technical Implementation Details

### Discord Bot Architecture

```python
# New files needed:
- discord_bot.py - Main bot file
- payment_handler.py - Payment processing
- subscription_manager.py - Subscription logic
- user_manager.py - User management
- discord_notifier.py - Alert notifications
```

### Database Schema Additions

```sql
-- Users table
CREATE TABLE users (
    discord_id TEXT PRIMARY KEY,
    username TEXT,
    subscription_status TEXT,
    subscription_start DATE,
    subscription_end DATE,
    payment_id TEXT,
    created_at TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    discord_id TEXT,
    payment_provider TEXT,
    payment_id TEXT,
    amount REAL,
    status TEXT,
    created_at TIMESTAMP
);

-- User preferences table
CREATE TABLE user_preferences (
    discord_id TEXT PRIMARY KEY,
    min_profit_threshold REAL,
    preferred_sports TEXT,
    alert_frequency TEXT,
    notification_channels TEXT
);
```

### Required Dependencies

```
discord.py>=2.3.0
stripe>=7.0.0 (or alternative)
python-dotenv>=1.0.0
aiohttp>=3.9.0 (async HTTP)
```

## Discord Setup Requirements

### 1. Server Setup

- Create Discord server with proper structure
- Set up channel categories and permissions
- Create subscriber role with appropriate permissions
- Configure bot permissions (read messages, send messages, manage roles)
- Set up welcome messages and rules

### 2. Bot Setup

- Create Discord application at https://discord.com/developers/applications
- Generate bot token
- Invite bot to server with required permissions:
                                - Send Messages
                                - Embed Links
                                - Manage Roles
                                - Read Message History
                                - Add Reactions

### 3. Payment Integration

- Set up Stripe account (or alternative)
- Create product and pricing in Stripe
- Set up webhook endpoint for payment events
- Configure subscription billing cycle
- Test payment flow

### 4. Legal & Compliance

- Terms of Service document
- Privacy Policy
- Disclaimer about betting risks
- Age verification (18+)
- Geographic restrictions if needed
- Refund policy

## Pricing Strategy

### Tier 1: Basic ($20/month)

- Real-time arbitrage alerts
- Access to top 5 opportunities
- Daily statistics
- Community access
- Basic support

### Tier 2: Premium ($35/month - Future)

- Everything in Basic
- SMS alerts
- Email backups
- Historical data export
- Priority support
- Custom alert thresholds

### Trial Period

- 7-day free trial for new users
- Full access during trial
- Automatic conversion to paid if not cancelled

## Success Metrics

### Technical KPIs

- Bot uptime (target: 99.5%)
- Alert latency (target: <30 seconds from opportunity detection)
- API quota usage efficiency
- System error rate

### Business KPIs

- Subscriber count
- Monthly recurring revenue (MRR)
- Churn rate (target: <10% monthly)
- Customer acquisition cost (CAC)
- Lifetime value (LTV)
- Conversion rate (trial to paid)

### Community KPIs

- Active users per day
- Message engagement rate
- Support ticket resolution time
- User satisfaction score

## Risk Mitigation

### Technical Risks

- API quota exhaustion → Implement caching, optimize polling
- Bot downtime → Redundant bot instances, monitoring
- Database issues → Regular backups, failover plan

### Business Risks

- Low subscription conversion → Improve value proposition, pricing
- High churn → Better onboarding, engagement features
- Payment fraud → Implement verification, rate limiting

### Legal Risks

- Betting regulations → Clear disclaimers, age verification
- Payment disputes → Clear refund policy, terms of service
- Data privacy → GDPR compliance, privacy policy

## Timeline & Resources

### Week 1-3: Technical Foundation

- Developer: Full-time
- Tasks: Discord bot, notification system, user management

### Week 4-5: Payment Integration

- Developer: Full-time
- Payment provider setup: 1-2 days
- Testing: 3-5 days

### Week 6-7: Discord Setup

- Developer: Part-time
- Community manager: Part-time
- Tasks: Server setup, content creation, rules

### Week 8-10: Product Enhancement

- Developer: Part-time
- Tasks: Additional features, bug fixes, optimization

### Week 11-12: Marketing & Launch

- Marketing: Full-time
- Tasks: Content creation, social media, launch prep

## Estimated Costs

### Monthly Operating Costs

- Discord API: Free (within limits)
- The Odds API: $50-200/month (depending on usage)
- Payment processing: 2.9% + $0.30 per transaction
- Server hosting: $10-50/month (VPS/cloud)
- Domain & email: $5-10/month
- **Total: ~$100-300/month** (excluding API costs)

### Revenue Projections

- 50 subscribers × $20 = $1,000/month
- 100 subscribers × $20 = $2,000/month
- 200 subscribers × $20 = $4,000/month
- Break-even: ~10-15 subscribers

## Next Steps

1. **Immediate**: Set up Discord server structure
2. **Week 1**: Begin Discord bot development
3. **Week 2**: Set up payment provider account
4. **Week 3**: Implement user management system
5. **Week 4**: Beta testing with 5-10 users
6. **Week 5**: Launch to public

## Conclusion

This plan transforms the arbitrage finder into a viable Discord-based subscription service. Focus on technical reliability, user experience, and community building. Start small, iterate based on feedback, and scale gradually.

### To-dos

- [ ] Fix evaluate_outcome_in_scenario() to handle string scenarios for MMA/boxing by adding special case logic before calling match methods
- [ ] Add isinstance() checks to all match methods (matches_home_win, matches_away_win, matches_draw, matches_home_spread, matches_away_spread) before accessing point_differential
- [ ] Fix outcome type mapping in arbitrage_finder.py for combat sports to properly handle string outcomes vs OutcomeType enums
- [ ] Add comprehensive error handling with try-except blocks and clear error messages for type mismatches
- [ ] Verify mathematical correctness of all arbitrage calculations after fixes, especially for string scenarios