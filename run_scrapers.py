"""
Main script to run all scrapers for Phase 1
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from config.csv_loader import CSVSourceManager
from scrapers.groww_scraper import GrowwScraper
from scrapers.axismf_scraper import AxisMFScraper


def main():
    """Run all scrapers and save data"""
    print("=" * 60)
    print("PHASE 1: DATA INGESTION - GROWW RAG CHATBOT")
    print("=" * 60)
    
    # Initialize CSV manager
    print("\n[1/5] Loading URL sources from CSV...")
    csv_manager = CSVSourceManager()
    funds = csv_manager.get_all_funds()
    print(f"Found {len(funds)} funds: {', '.join(funds)}")
    
    # Scrape Groww.in
    print("\n[2/5] Scraping Groww.in for NAV, MIN SIP, Expense Ratio, Exit Load...")
    groww_scraper = GrowwScraper(csv_manager)
    groww_data = groww_scraper.scrape_all_funds()
    print(f"Successfully scraped {len(groww_data)} funds from Groww.in")
    
    # Scrape AxisMF.com
    print("\n[3/5] Scraping AxisMF.com for Riskometer, Benchmark, FAQs...")
    axismf_scraper = AxisMFScraper(csv_manager)
    axismf_data = axismf_scraper.scrape_all_funds()
    print(f"Successfully scraped {len(axismf_data)} funds from AxisMF.com")
    
    # Save data
    print("\n[4/5] Saving scraped data to JSON...")
    groww_path = groww_scraper.save_to_json(groww_data)
    axismf_path = axismf_scraper.save_to_json(axismf_data)
    print(f"Groww data saved to: {groww_path}")
    print(f"AxisMF data saved to: {axismf_path}")
    
    # Display summary
    print("\n[5/5] Scraping Summary:")
    print("-" * 60)
    print("\nGroww.in Data:")
    for fund_name, data in groww_data.items():
        print(f"\n  {fund_name}:")
        print(f"    NAV: {data.nav}")
        print(f"    Min SIP: {data.min_sip}")
        print(f"    Expense Ratio: {data.expense_ratio}")
        print(f"    Exit Load: {data.exit_load}")
    
    print("\nAxisMF.com Data:")
    for fund_name, data in axismf_data.items():
        print(f"\n  {fund_name}:")
        print(f"    Riskometer: {data.riskometer}")
        print(f"    Benchmark: {data.benchmark}")
        print(f"    FAQs: {len(data.faqs)} questions")
    
    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETE - Data ingestion finished successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
