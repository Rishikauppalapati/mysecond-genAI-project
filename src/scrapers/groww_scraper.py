"""
Groww.in Scraper Module
Scrapes mutual fund data from Groww.in using Selenium for JavaScript-rendered content
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

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    """Scraper for Groww.in mutual fund data using Selenium"""
    
    def __init__(self, csv_manager: CSVSourceManager = None, use_selenium: bool = True):
        self.csv_manager = csv_manager or CSVSourceManager()
        self.use_selenium = use_selenium
        self.driver = None
        
        # Setup requests session as fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"Failed to initialize Chrome driver: {e}")
                print("Falling back to requests...")
                self.use_selenium = False
    
    def _get_page_content(self, url: str) -> Optional[str]:
        """Get page content using Selenium or requests"""
        if self.use_selenium:
            try:
                self._init_selenium()
                self.driver.get(url)
                # Wait for page to load
                time.sleep(3)
                # Wait for key elements
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    pass
                return self.driver.page_source
            except Exception as e:
                print(f"Selenium error: {e}, falling back to requests")
                self.use_selenium = False
        
        # Fallback to requests
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
    
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_nav(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract NAV value and date from page"""
        try:
            nav_value = None
            nav_date = None
            
            # Method 1: Look for NAV in specific text patterns
            page_text = soup.get_text()
            
            # Look for "NAV" followed by a number
            nav_patterns = [
                r'NAV[\s:]*[₹Rs]?\s*([\d,]+\.?\d*)',
                r'Net Asset Value[\s:]*[₹Rs]?\s*([\d,]+\.?\d*)',
                r'[₹Rs]\s*([\d,]+\.?\d*)\s*(?:per unit|NAV)',
            ]
            
            for pattern in nav_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    nav_value = match.group(1).replace(',', '')
                    break
            
            # Method 2: Look in specific elements
            if not nav_value:
                nav_selectors = [
                    '.fs-24',  # Common class for large numbers
                    '.fw-500',
                    '[class*="nav"]',
                    '[class*="price"]',
                ]
                
                for selector in nav_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        if '₹' in text or any(c.isdigit() for c in text):
                            numbers = re.findall(r'[₹Rs]?\s*([\d,]+\.?\d*)', text)
                            if numbers:
                                potential_nav = numbers[0].replace(',', '')
                                # Validate it's a reasonable NAV value (between 1 and 10000)
                                try:
                                    val = float(potential_nav)
                                    if 1 <= val <= 10000:
                                        nav_value = potential_nav
                                        break
                                except:
                                    pass
                    if nav_value:
                        break
            
            # Extract NAV date
            date_patterns = [
                r'as on[\s:]*([\d]{1,2}[\w\s,]+\d{4})',
                r'NAV date[\s:]*([\d]{1,2}[\w\s,]+\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    nav_date = match.group(1).strip()
                    break
            
            if nav_value:
                return {
                    "current": float(nav_value),
                    "date": nav_date or datetime.now().strftime("%Y-%m-%d")
                }
            return None
        except Exception as e:
            print(f"Error extracting NAV: {e}")
            return None
    
    def _extract_min_sip(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract minimum SIP amount from page"""
        try:
            page_text = soup.get_text()
            
            # Look for SIP patterns
            sip_patterns = [
                r'(?:min|minimum)\s+SIP[\s:]*[₹Rs]?\s*([\d,]+)',
                r'SIP[\s:]+[₹Rs]?\s*([\d,]+)',
                r'minimum investment[\s:]*[₹Rs]?\s*([\d,]+)',
                r'[₹Rs]\s*([\d,]+)\s*(?:min|minimum)',
            ]
            
            for pattern in sip_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return f"₹{match.group(1)}"
            
            # Look for SIP in tables or specific sections
            sip_selectors = [
                'td:contains("SIP")',
                'td:contains("Min")',
                '[class*="sip"]',
                '[class*="investment"]',
            ]
            
            for selector in sip_selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        numbers = re.findall(r'[₹Rs]?\s*([\d,]+)', text)
                        if numbers:
                            # Check if it's a reasonable SIP amount (100-100000)
                            val = int(numbers[0].replace(',', ''))
                            if 100 <= val <= 100000:
                                return f"₹{numbers[0]}"
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Error extracting Min SIP: {e}")
            return None
    
    def _extract_expense_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract expense ratio from page"""
        try:
            # Look for expense ratio
            expense_keywords = ['expense ratio', 'expense', 'ratio']
            page_text = soup.get_text().lower()
            
            for keyword in expense_keywords:
                if keyword in page_text:
                    import re
                    # Look for percentage pattern
                    pattern = rf'{keyword}[\s:]*(\d+\.?\d*)\s*%'
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        return f"{match.group(1)}%"
            
            # Try specific selectors
            expense_selectors = [
                '[data-testid="expense-ratio"]',
                '.expense-ratio',
                '[class*="expense"]',
            ]
            
            for selector in expense_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if '%' in text:
                        import re
                        numbers = re.findall(r'(\d+\.?\d*)\s*%', text)
                        if numbers:
                            return f"{numbers[0]}%"
            
            return None
        except Exception as e:
            print(f"Error extracting Expense Ratio: {e}")
            return None
    
    def _extract_exit_load(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract exit load information from page"""
        try:
            # Look for exit load
            exit_keywords = ['exit load', 'exit', 'redemption']
            page_text = soup.get_text().lower()
            
            for keyword in exit_keywords:
                if keyword in page_text:
                    # Find the sentence containing exit load
                    import re
                    sentences = page_text.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            # Clean up the sentence
                            clean = sentence.strip()
                            if len(clean) > 10:  # Ensure it's a meaningful sentence
                                return clean.capitalize()
            
            # Try specific selectors
            exit_selectors = [
                '[data-testid="exit-load"]',
                '.exit-load',
                '[class*="exit"]',
            ]
            
            for selector in exit_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5:
                        return text
            
            return None
        except Exception as e:
            print(f"Error extracting Exit Load: {e}")
            return None
    
    def scrape_fund(self, fund_name: str) -> Optional[GrowwFundData]:
        """Scrape all data for a specific fund from Groww.in"""
        # Get the URL for this fund (all data types use same URL on Groww)
        url = self.csv_manager.get_url(fund_name, "NAV")
        
        if not url:
            print(f"No URL found for {fund_name}")
            return None
        
        print(f"Scraping {fund_name} from {url}...")
        
        page_content = self._get_page_content(url)
        if not page_content:
            return None
        
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # Extract fund code from URL
        fund_code = url.split('/')[-1]
        
        # Extract all data points
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
        
        # Get unique fund names from Groww sources
        groww_sources = self.csv_manager.get_groww_sources()
        fund_names = list(set(source.fund_name for source in groww_sources))
        
        try:
            for fund_name in fund_names:
                fund_data = self.scrape_fund(fund_name)
                if fund_data:
                    results[fund_name] = fund_data
        finally:
            # Always close the driver
            self.close()
        
        return results
    
    def save_to_json(self, data: Dict[str, GrowwFundData], output_path: str = None):
        """Save scraped data to JSON file"""
        if output_path is None:
            # Default to data/raw directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_path = os.path.join(current_dir, "data", "raw", "groww_data.json")
        
        # Convert to dictionary
        output_data = {
            fund_name: fund_data.to_dict()
            for fund_name, fund_data in data.items()
        }
        
        # Add metadata
        output_data['_metadata'] = {
            'source': 'groww.in',
            'scraped_at': datetime.now().isoformat(),
            'total_funds': len(data)
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {output_path}")
        return output_path


def main():
    """Main function to test the scraper"""
    scraper = GrowwScraper()
    
    print("=== Starting Groww.in Scraper ===\n")
    
    # Scrape all funds
    results = scraper.scrape_all_funds()
    
    print("\n=== Scraping Results ===")
    for fund_name, fund_data in results.items():
        print(f"\n{fund_name}:")
        print(f"  NAV: {fund_data.nav}")
        print(f"  Min SIP: {fund_data.min_sip}")
        print(f"  Expense Ratio: {fund_data.expense_ratio}")
        print(f"  Exit Load: {fund_data.exit_load}")
    
    # Save to JSON
    output_path = scraper.save_to_json(results)
    print(f"\nData saved to: {output_path}")


if __name__ == "__main__":
    main()
