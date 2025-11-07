#!/usr/bin/env python3
"""
CLI reporting tool for arbitrage finder analytics.
Usage: python report.py [command]

Commands:
    summary      - Overall statistics
    sport        - Breakdown by sport
    market       - Breakdown by market type
    bookmakers   - Most common bookmaker pairs
    recent       - Recent opportunities
    hourly       - Opportunities by hour of day
    export       - Export all data to CSV
"""

import sys
import csv
from pathlib import Path
from src import analytics
from src import config
from src.utils import format_currency, get_sport_display_name


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_table(headers: list, rows: list, alignments: list = None):
    """
    Print a simple ASCII table.
    
    Args:
        headers: List of column headers
        rows: List of row data (lists)
        alignments: List of '<' (left) or '>' (right) for each column
    """
    if not rows:
        print("  No data available.\n")
        return
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Default alignments (left)
    if not alignments:
        alignments = ['<'] * len(headers)
    
    # Print header
    header_format = "  " + "  ".join([f"{{:{align}{width}}}" for align, width in zip(alignments, widths)])
    print(header_format.format(*headers))
    print("  " + "  ".join(["-" * width for width in widths]))
    
    # Print rows
    for row in rows:
        print(header_format.format(*[str(cell) for cell in row]))
    
    print()


def command_summary():
    """Display overall summary statistics."""
    print_header("📊 ARBITRAGE FINDER - SUMMARY STATISTICS")
    
    stats = analytics.get_summary_stats()
    
    if not stats:
        print("  No data available. Run the arbitrage finder to collect data.\n")
        return
    
    print(f"  Total Opportunities Found:    {stats['total_opportunities']:,}")
    print(f"  Total Alerts Sent:            {stats['total_alerts']:,}")
    print(f"  Total Bets Placed:            {stats['total_bets_placed']:,}")
    print()
    print(f"  Average Profit Margin:        {stats['avg_profit_margin']:.2f}%")
    print(f"  Best Profit Margin:           {stats['best_profit_margin']:.2f}%")
    print()
    print(f"  Total Potential Profit:       {format_currency(stats['total_potential_profit'])}")
    print(f"  Actual Profit Realized:       {format_currency(stats['actual_profit'])}")
    print()
    print(f"  Alert Rate:                   {stats['alert_rate']:.1f}% of opportunities")
    print(f"  Bet Placement Rate:           {stats['bet_rate']:.1f}% of alerts")
    
    # ROI calculation
    roi = analytics.calculate_roi_if_all_taken()
    if roi:
        print()
        print(f"  If All Opportunities Taken:")
        print(f"    Total Investment:           {format_currency(roi['total_investment'])}")
        print(f"    Total Profit:               {format_currency(roi['total_profit'])}")
        print(f"    ROI:                        {roi['roi_percentage']:.2f}%")
    
    print()


def command_sport():
    """Display breakdown by sport."""
    print_header("🏆 OPPORTUNITIES BY SPORT")
    
    data = analytics.get_opportunities_by_sport()
    
    if not data:
        print("  No data available.\n")
        return
    
    # Format data for display
    rows = []
    for sport, count, avg_profit in data:
        sport_name = get_sport_display_name(sport)
        rows.append([sport_name, f"{count:,}", f"{avg_profit:.2f}%"])
    
    print_table(
        ["Sport", "Opportunities", "Avg Profit"],
        rows,
        ['<', '>', '>']
    )


def command_market():
    """Display breakdown by market type."""
    print_header("📈 OPPORTUNITIES BY MARKET TYPE")
    
    data = analytics.get_opportunities_by_market()
    
    if not data:
        print("  No data available.\n")
        return
    
    # Format data for display
    rows = []
    for market, count, avg_profit in data:
        market_name = config.MARKET_DISPLAY_NAMES.get(market, market)
        rows.append([market_name, f"{count:,}", f"{avg_profit:.2f}%"])
    
    print_table(
        ["Market", "Opportunities", "Avg Profit"],
        rows,
        ['<', '>', '>']
    )


def command_bookmakers():
    """Display most common bookmaker pairs."""
    print_header("🏪 MOST COMMON BOOKMAKER PAIRS")
    
    data = analytics.get_opportunities_by_bookmaker()
    
    if not data:
        print("  No data available.\n")
        return
    
    # Format data for display
    rows = []
    for book_a, book_b, count in data[:15]:  # Top 15
        rows.append([book_a, book_b, f"{count:,}"])
    
    print_table(
        ["Bookmaker A", "Bookmaker B", "Count"],
        rows,
        ['<', '<', '>']
    )


def command_recent():
    """Display recent opportunities."""
    print_header("🕐 RECENT OPPORTUNITIES")
    
    data = analytics.get_recent_opportunities(20)
    
    if not data:
        print("  No data available.\n")
        return
    
    # Format data for display
    rows = []
    for opp in data:
        timestamp = opp['timestamp'][:16].replace('T', ' ')  # Truncate timestamp
        sport_short = get_sport_display_name(opp['sport'])[:15]  # Truncate sport name
        market_short = config.MARKET_DISPLAY_NAMES.get(opp['market'], opp['market'])[:10]
        event_short = opp['event_name'][:30] if len(opp['event_name']) <= 30 else opp['event_name'][:27] + "..."
        
        rows.append([
            timestamp,
            sport_short,
            market_short,
            event_short,
            f"{opp['profit_margin']:.2f}%",
            format_currency(opp['guaranteed_profit'])
        ])
    
    print_table(
        ["Time", "Sport", "Market", "Event", "Profit %", "Profit $"],
        rows,
        ['<', '<', '<', '<', '>', '>']
    )


def command_hourly():
    """Display opportunities by hour of day."""
    print_header("⏰ OPPORTUNITIES BY HOUR OF DAY")
    
    data = analytics.get_opportunities_by_hour()
    
    if not data:
        print("  No data available.\n")
        return
    
    # Create bar chart
    max_count = max(data.values()) if data else 1
    
    rows = []
    for hour in range(24):
        count = data.get(hour, 0)
        bar_length = int((count / max_count) * 40) if max_count > 0 else 0
        bar = "█" * bar_length
        time_label = f"{hour:02d}:00"
        rows.append([time_label, f"{count:>3}", bar])
    
    print_table(
        ["Hour", "Count", "Distribution"],
        rows,
        ['<', '>', '<']
    )


def command_export():
    """Export all data to CSV."""
    from database import ArbitrageDatabase
    
    print_header("📤 EXPORT DATA TO CSV")
    
    try:
        db = ArbitrageDatabase(config.DATABASE_PATH)
        opportunities = db.get_opportunities(limit=10000)
        db.close()
        
        if not opportunities:
            print("  No data to export.\n")
            return
        
        # Export to CSV
        filename = f"arbitrage_export_{Path(config.DATABASE_PATH).stem}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = opportunities[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for opp in opportunities:
                writer.writerow(opp)
        
        print(f"  ✅ Exported {len(opportunities)} opportunities to: {filename}\n")
        
    except Exception as e:
        print(f"  ❌ Export failed: {e}\n")


def show_help():
    """Display help message."""
    print(__doc__)


def main():
    """Main entry point for report CLI."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'summary': command_summary,
        'sport': command_sport,
        'market': command_market,
        'bookmakers': command_bookmakers,
        'recent': command_recent,
        'hourly': command_hourly,
        'export': command_export,
        'help': show_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python report.py help' for available commands.\n")


if __name__ == "__main__":
    main()

