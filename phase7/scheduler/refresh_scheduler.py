"""
Phase 7: Scheduler for Automated Data Refresh
Periodically updates data from sources
"""

import os
import sys
import time
from datetime import datetime
from typing import Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase1'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from scrapers.groww_scraper import GrowwScraper
from scrapers.axismf_scraper import AxisMFScraper
from processors.text_processor import TextProcessor
from config.csv_loader import CSVSourceManager


class DataRefreshScheduler:
    """Scheduler for automated data refresh"""
    
    def __init__(self):
        self.csv_manager = CSVSourceManager()
        self.last_refresh = {}
    
    def run_phase1(self):
        """Run Phase 1: Data Ingestion"""
        print(f"[{datetime.now()}] Running Phase 1: Data Ingestion...")
        
        # Scrape Groww.in
        groww_scraper = GrowwScraper(self.csv_manager, use_selenium=False)
        groww_data = groww_scraper.scrape_all_funds()
        groww_scraper.save_to_json(groww_data)
        
        # Scrape AxisMF.com
        axismf_scraper = AxisMFScraper(self.csv_manager)
        axismf_data = axismf_scraper.scrape_all_funds()
        axismf_scraper.save_to_json(axismf_data)
        
        self.last_refresh['phase1'] = datetime.now()
        print(f"[{datetime.now()}] Phase 1 Complete!")
    
    def run_phase2(self):
        """Run Phase 2: Document Processing"""
        print(f"[{datetime.now()}] Running Phase 2: Document Processing...")
        
        processor = TextProcessor(self.csv_manager)
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'data')
        
        # Process Groww data
        groww_chunks = processor.process_groww_data(
            os.path.join(base_dir, 'raw', 'groww_data.json')
        )
        
        # Process AxisMF data
        axismf_chunks = processor.process_axismf_data(
            os.path.join(base_dir, 'raw', 'axismf_data.json')
        )
        
        # Save all chunks
        all_chunks = groww_chunks + axismf_chunks
        processor.save_chunks(all_chunks, os.path.join(base_dir, 'processed', 'chunks.json'))
        
        self.last_refresh['phase2'] = datetime.now()
        print(f"[{datetime.now()}] Phase 2 Complete!")
    
    def run_full_refresh(self):
        """Run full data refresh pipeline"""
        print("\n" + "=" * 60)
        print("STARTING FULL DATA REFRESH")
        print("=" * 60)
        
        self.run_phase1()
        self.run_phase2()
        
        print("\n" + "=" * 60)
        print("FULL REFRESH COMPLETE!")
        print("=" * 60)
    
    def schedule_daily(self, hour: int = 21, minute: int = 0):
        """
        Schedule daily refresh at specified time (default 9 PM).
        In production, use APScheduler or cron.
        """
        print(f"Scheduled daily refresh at {hour:02d}:{minute:02d}")
        # This is a placeholder - in production use APScheduler
        # from apscheduler.schedulers.background import BackgroundScheduler
        # scheduler = BackgroundScheduler()
        # scheduler.add_job(self.run_full_refresh, 'cron', hour=hour, minute=minute)
        # scheduler.start()


def main():
    """Run scheduler"""
    print("=" * 60)
    print("PHASE 7: SCHEDULER")
    print("=" * 60)
    
    scheduler = DataRefreshScheduler()
    
    print("\n1. Run immediate full refresh")
    print("2. Schedule daily refresh (demo)")
    
    choice = input("\nSelect option (1/2): ").strip()
    
    if choice == '1':
        scheduler.run_full_refresh()
    elif choice == '2':
        scheduler.schedule_daily()
        print("\nScheduler configured. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
    else:
        print("Invalid option.")
    
    print("\n" + "=" * 60)
    print("PHASE 7 COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
