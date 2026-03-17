"""
Phase 1: Groww.in Scraper Module
Scrapes NAV, MIN SIP, Expense Ratio, Exit Load from Groww.in
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import re
import time
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

# Selenium imports for JavaScript-rendered content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Add shared config to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))
from config.csv_loader import CSVSourceManager


@dataclass
class GrowwFundData:
    """Data class for storing scraped fund data from Groww.in"""
    fund_name: str
    fund_code: str
    source: str
    source_url: str
    csv_reference: str
    last_updated: str
    nav: Optional[Dict[str, Any]] = None
    min_sip: Optional[str] = None
    expense_ratio: Optional[str] = None
    exit_load: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class GrowwScraper:
    """Scraper for Groww.in mutual fund data"""
    
    def __init__(self, csv_manager: CSVSourceManager = None, use_selenium: bool = True):
        self.csv_manager = csv_manager or CSVSourceManager()
        self.use_selenium = use_selenium
        self.driver = None
        
        # Setup requests session as fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"Failed to initialize Chrome driver: {e}")
                self.use_selenium = False
    
    def _get_page_content(self, url: str) -> Optional[str]:
        """Get page content using Selenium or requests"""
        if self.use_selenium:
            try:
                self._init_selenium()
                self.driver.get(url)
                time.sleep(3)
                return self.driver.page_source
            except Exception as e:
                print(f"Selenium error: {e}, falling back to requests")
                self.use_selenium = False
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def close(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _extract_nav(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract NAV value and date from page"""
        try:
            nav_value = None
            nav_date = None
            page_text = soup.get_text()
            
            # Look for NAV patterns
            nav_patterns = [
                r'NAV[\s:]*[₹Rs]?\s*([\d,]+\.?\d*)',
                r'Net Asset Value[\s:]*[₹Rs]?\s*([\d,]+\.?\d*)',
            ]
            
            for pattern in nav_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    nav_value = match.group(1).replace(',', '')
                    break
            
            # Look in specific elements
            if not nav_value:
                selectors = ['.fs-24', '.fw-500', '[class*="nav"]', '[class*="price"]']
                for selector in selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        if '₹' in text:
                            numbers = re.findall(r'[₹Rs]?\s*([\d,]+\.?\d*)', text)
                            if numbers:
                                try:
                                    val = float(numbers[0].replace(',', ''))
                                    if 1 <= val <= 10000:
                                        nav_value = numbers[0]
                                        break
                                except:
                                    pass
                    if nav_value:
                        break
            
            if nav_value:
                return {
                    "current": float(nav_value),
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            return None
        except Exception as e:
            print(f"Error extracting NAV: {e}")
            return None
    
    def _extract_min_sip(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract minimum SIP amount from page"""
        try:
            page_text = soup.get_text()
            
            sip_patterns = [
                r'(?:min|minimum)\s+SIP[\s:]*[₹Rs]?\s*([\d,]+)',
                r'SIP[\s:]+[₹Rs]?\s*([\d,]+)',
            ]
            
            for pattern in sip_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return f"₹{match.group(1)}"
            
            return None
        except Exception as e:
            print(f"Error extracting Min SIP: {e}")
            return None
    
    def _extract_expense_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract expense ratio from page"""
        try:
            page_text = soup.get_text().lower()
            
            match = re.search(r'expense ratio[\s:]*(\d+\.?\d*)\s*%', page_text)
            if match:
                return f"{match.group(1)}%"
            
            return None
        except Exception as e:
            print(f"Error extracting Expense Ratio: {e}")
            return None
    
    def _extract_exit_load(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract exit load information from page"""
        try:
            page_text = soup.get_text().lower()
            
            # Look for exit load patterns
            patterns = [
                r'exit load[\s:]*([^\.]+\.)',
                r'redemption[\s:]*([^\.]+\.)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    return match.group(1).strip().capitalize()
            
            return None
        except Exception as e:
            print(f"Error extracting Exit Load: {e}")
            return None
    
    def scrape_fund(self, fund_name: str) -> Optional[GrowwFundData]:
        """Scrape all data for a specific fund from Groww.in"""
        url = self.csv_manager.get_url(fund_name, "NAV")
        
        if not url:
            print(f"No URL found for {fund_name}")
            return None
        
        print(f"Scraping {fund_name} from {url}...")
        
        page_content = self._get_page_content(url)
        if not page_content:
            return None
        
        soup = BeautifulSoup(page_content, 'html.parser')
        fund_code = url.split('/')[-1]
        
        fund_data = GrowwFundData(
            fund_name=fund_name,
            fund_code=fund_code,
            source="groww.in",
            source_url=url,
            csv_reference=f"sources.csv:{fund_name}",
            last_updated=datetime.now().isoformat(),
            nav=self._extract_nav(soup),
            min_sip=self._extract_min_sip(soup),
            expense_ratio=self._extract_expense_ratio(soup),
            exit_load=self._extract_exit_load(soup)
        )
        
        return fund_data
    
    def scrape_all_funds(self) -> Dict[str, GrowwFundData]:
        """Scrape data for all funds from Groww.in"""
        results = {}
        groww_sources = self.csv_manager.get_groww_sources()
        fund_names = list(set(source.fund_name for source in groww_sources))
        
        try:
            for fund_name in fund_names:
                fund_data = self.scrape_fund(fund_name)
                if fund_data:
                    results[fund_name] = fund_data
        finally:
            self.close()
        
        return results
    
    def save_to_json(self, data: Dict[str, GrowwFundData], output_path: str = None):
        """Save scraped data to JSON file"""
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_path = os.path.join(base_dir, "shared", "data", "raw", "groww_data.json")
        
        output_data = {
            fund_name: fund_data.to_dict()
            for fund_name, fund_data in data.items()
        }
        
        output_data['_metadata'] = {
            'source': 'groww.in',
            'scraped_at': datetime.now().isoformat(),
            'total_funds': len(data)
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {output_path}")
        return output_path


def main():
    """Main function to test the scraper"""
    scraper = GrowwScraper()
    
    print("=== Phase 1: Groww.in Scraper ===\n")
    
    results = scraper.scrape_all_funds()
    
    print("\n=== Scraping Results ===")
    for fund_name, fund_data in results.items():
        print(f"\n{fund_name}:")
        print(f"  NAV: {fund_data.nav}")
        print(f"  Min SIP: {fund_data.min_sip}")
        print(f"  Expense Ratio: {fund_data.expense_ratio}")
        print(f"  Exit Load: {fund_data.exit_load}")
        print(f"  Source URL: {fund_data.source_url}")
    
    output_path = scraper.save_to_json(results)
    print(f"\nData saved to: {output_path}")


if __name__ == "__main__":
    main()
