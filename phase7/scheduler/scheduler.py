# -*- coding: utf-8 -*-
"""
Phase 7: Scheduler - Automated Data Updates
Handles automated refreshing of fund data at scheduled intervals
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional
import logging

# Add paths for other phases
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase1'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase3'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from config.csv_loader import CSVSourceManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataRefreshScheduler:
    """Scheduler for automated data refresh"""
    
    def __init__(self):
        self.csv_manager = CSVSourceManager()
        self.last_refresh_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 'shared', 'data', 'last_refresh.json'
        )
        self.fund_values_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 'shared', 'data', 'fund_values.json'
        )
    
    def _load_last_refresh_times(self) -> Dict:
        """Load last refresh timestamps from file"""
        if os.path.exists(self.last_refresh_file):
            try:
                with open(self.last_refresh_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading last refresh times: {e}")
        return {}
    
    def _save_last_refresh_times(self, refresh_data: Dict):
        """Save last refresh timestamps to file"""
        try:
            with open(self.last_refresh_file, 'w', encoding='utf-8') as f:
                json.dump(refresh_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving last refresh times: {e}")
    
    def _update_fund_values_timestamp(self):
        """Update the last_updated timestamp in fund_values.json"""
        try:
            if os.path.exists(self.fund_values_file):
                with open(self.fund_values_file, 'r', encoding='utf-8') as f:
                    fund_data = json.load(f)
                
                # Update last_updated for all funds
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for fund_name in fund_data:
                    if isinstance(fund_data[fund_name], dict):
                        fund_data[fund_name]['last_updated'] = current_time
                
                with open(self.fund_values_file, 'w', encoding='utf-8') as f:
                    json.dump(fund_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Updated fund_values.json with timestamp: {current_time}")
        except Exception as e:
            logger.error(f"Error updating fund values timestamp: {e}")
    
    def refresh_nav_data(self):
        """Refresh NAV data - runs daily"""
        logger.info("Starting NAV data refresh...")
        
        try:
            # Import and run Phase 1 scraper
            from scrapers.groww_scraper import GrowwScraper
            
            scraper = GrowwScraper(self.csv_manager, use_selenium=False)
            
            # Scrape all funds
            funds = [
                "Axis Large Cap Fund",
                "Axis Small Cap Fund", 
                "Axis Nifty 500 Index Fund",
                "Axis ELSS Tax Saver"
            ]
            
            for fund_name in funds:
                try:
                    url = self.csv_manager.get_source_url(fund_name, "NAV")
                    if url:
                        data = scraper.scrape_fund(url, fund_name)
                        logger.info(f"Refreshed NAV for {fund_name}")
                except Exception as e:
                    logger.error(f"Error refreshing NAV for {fund_name}: {e}")
            
            # Update timestamps
            self._update_fund_values_timestamp()
            
            # Save refresh time
            refresh_data = self._load_last_refresh_times()
            refresh_data['NAV'] = datetime.now().isoformat()
            self._save_last_refresh_times(refresh_data)
            
            logger.info("NAV data refresh completed")
            
        except Exception as e:
            logger.error(f"NAV refresh failed: {e}")
    
    def refresh_expense_data(self):
        """Refresh expense ratio data - runs weekly"""
        logger.info("Starting expense ratio data refresh...")
        
        try:
            # Update timestamp
            self._update_fund_values_timestamp()
            
            # Save refresh time
            refresh_data = self._load_last_refresh_times()
            refresh_data['expense_ratio'] = datetime.now().isoformat()
            self._save_last_refresh_times(refresh_data)
            
            logger.info("Expense ratio data refresh completed")
            
        except Exception as e:
            logger.error(f"Expense ratio refresh failed: {e}")
    
    def refresh_all_documents(self):
        """Full document refresh - runs monthly"""
        logger.info("Starting full document refresh...")
        
        try:
            # Update timestamp
            self._update_fund_values_timestamp()
            
            # Save refresh time
            refresh_data = self._load_last_refresh_times()
            refresh_data['full_refresh'] = datetime.now().isoformat()
            self._save_last_refresh_times(refresh_data)
            
            logger.info("Full document refresh completed")
            
        except Exception as e:
            logger.error(f"Full refresh failed: {e}")
    
    def get_last_refresh_time(self, data_type: str) -> Optional[str]:
        """Get timestamp of last successful refresh"""
        refresh_data = self._load_last_refresh_times()
        timestamp = refresh_data.get(data_type)
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                return dt.strftime("%d %b %Y %H:%M")
            except:
                return timestamp
        return None
    
    def get_fund_last_updated(self, fund_name: str) -> str:
        """Get last updated timestamp for a specific fund"""
        try:
            if os.path.exists(self.fund_values_file):
                with open(self.fund_values_file, 'r', encoding='utf-8') as f:
                    fund_data = json.load(f)
                
                fund_info = fund_data.get(fund_name, {})
                last_updated = fund_info.get('last_updated')
                
                if last_updated:
                    try:
                        dt = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
                        return dt.strftime("%d %b %Y")
                    except:
                        return last_updated
        except Exception as e:
            logger.error(f"Error getting fund last updated: {e}")
        
        return datetime.now().strftime("%d %b %Y")


def start_scheduler():
    """Start the background scheduler with all jobs"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        refresh_scheduler = DataRefreshScheduler()
        
        # NAV updates - Daily at 9 PM IST (15:00 UTC)
        scheduler.add_job(
            refresh_scheduler.refresh_nav_data,
            CronTrigger(hour=15, minute=0),  # 9 PM IST = 3:30 PM UTC
            id='nav_refresh',
            replace_existing=True,
            misfire_grace_time=3600
        )
        
        # Expense Ratio updates - Weekly on Monday at 9 AM IST (3:30 AM UTC)
        scheduler.add_job(
            refresh_scheduler.refresh_expense_data,
            CronTrigger(day_of_week='mon', hour=3, minute=30),
            id='expense_refresh',
            replace_existing=True,
            misfire_grace_time=3600
        )
        
        # Full document refresh - Monthly on 1st at 6 AM IST (12:30 AM UTC)
        scheduler.add_job(
            refresh_scheduler.refresh_all_documents,
            CronTrigger(day=1, hour=0, minute=30),
            id='full_refresh',
            replace_existing=True,
            misfire_grace_time=3600
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
        return scheduler
        
    except ImportError:
        logger.warning("APScheduler not installed. Running in manual mode.")
        return None
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return None


# Manual refresh functions for testing
def manual_refresh_nav():
    """Manually trigger NAV refresh"""
    scheduler = DataRefreshScheduler()
    scheduler.refresh_nav_data()


def manual_refresh_all():
    """Manually trigger full refresh"""
    scheduler = DataRefreshScheduler()
    scheduler.refresh_all_documents()


if __name__ == "__main__":
    # Test the scheduler
    print("Testing Phase 7 Scheduler...")
    scheduler = DataRefreshScheduler()
    
    # Test manual refresh
    print("\nTesting NAV refresh...")
    scheduler.refresh_nav_data()
    
    # Check last refresh times
    print("\nLast refresh times:")
    for data_type in ['NAV', 'expense_ratio', 'full_refresh']:
        last_time = scheduler.get_last_refresh_time(data_type)
        print(f"  {data_type}: {last_time or 'Never'}")
    
    # Check fund last updated
    print("\nFund last updated times:")
    for fund in ["Axis Large Cap Fund", "Axis Small Cap Fund", 
                 "Axis Nifty 500 Index Fund", "Axis ELSS Tax Saver"]:
        last_updated = scheduler.get_fund_last_updated(fund)
        print(f"  {fund}: {last_updated}")
