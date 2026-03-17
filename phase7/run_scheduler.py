# -*- coding: utf-8 -*-
"""
Phase 7: Run Scheduler
Starts the automated data refresh scheduler
"""

import sys
import os
import time

# Add phase7 to path
sys.path.insert(0, os.path.dirname(__file__))

from scheduler import start_scheduler, DataRefreshScheduler


def main():
    """Main entry point for scheduler"""
    print("=" * 60)
    print("PHASE 7: SCHEDULER - Automated Data Updates")
    print("=" * 60)
    
    # Start the scheduler
    scheduler = start_scheduler()
    
    if scheduler:
        print("\n✅ Scheduler started successfully!")
        print("\nScheduled Jobs:")
        print("  • NAV Refresh: Daily at 9:00 PM IST")
        print("  • Expense Ratio Refresh: Weekly on Monday at 9:00 AM IST")
        print("  • Full Document Refresh: Monthly on 1st at 6:00 AM IST")
        print("\nPress Ctrl+C to stop the scheduler")
        
        try:
            # Keep the script running
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\nStopping scheduler...")
            scheduler.shutdown()
            print("✅ Scheduler stopped")
    else:
        print("\n⚠️  APScheduler not installed. Running manual refresh...")
        
        # Run manual refresh
        refresh_scheduler = DataRefreshScheduler()
        refresh_scheduler.refresh_nav_data()
        
        print("\n✅ Manual refresh completed")


if __name__ == "__main__":
    main()
