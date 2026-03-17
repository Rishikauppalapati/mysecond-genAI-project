"""
Phase 1: AxisMF.com Scraper Module
Scrapes Riskometer, Benchmark, FAQs from AxisMF.com
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict, field

# Add shared config to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))
from config.csv_loader import CSVSourceManager


@dataclass
class AxisMFFundData:
    """Data class for storing scraped fund data from AxisMF.com"""
    fund_name: str
    fund_code: str
    source: str
    source_url: str
    csv_reference: str
    last_updated: str
    riskometer: Optional[str] = None
    benchmark: Optional[str] = None
    faqs: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AxisMFScraper:
    """Scraper for AxisMF.com mutual fund data"""
    
    def __init__(self, csv_manager: CSVSourceManager = None):
        self.csv_manager = csv_manager or CSVSourceManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_riskometer(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract riskometer/risk level from page"""
        try:
            risk_levels = ['very high', 'high', 'moderately high', 'moderate', 'low', 'very low']
            page_text = soup.get_text().lower()
            
            # Look for risk patterns
            for risk in risk_levels:
                pattern = rf'\b{risk}\s+risk\b'
                if re.search(pattern, page_text):
                    return risk.title()
            
            # Check specific elements
            selectors = ['[class*="riskometer"]', '[class*="risk"]']
            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    alt_text = elem.get('alt', '').lower()
                    for risk in risk_levels:
                        if risk in alt_text:
                            return risk.title()
            
            return None
        except Exception as e:
            print(f"Error extracting Riskometer: {e}")
            return None
    
    def _extract_benchmark(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract benchmark index from page"""
        try:
            page_text = soup.get_text()
            
            # Look for benchmark patterns
            match = re.search(r'benchmark[\s:]*(.+)', page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return None
        except Exception as e:
            print(f"Error extracting Benchmark: {e}")
            return None
    
    def _extract_faqs(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract FAQs from page"""
        faqs = []
        try:
            # Look for FAQ sections
            selectors = ['[class*="faq"]', '[class*="accordion"]', '.question']
            
            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    question = None
                    answer = None
                    
                    # Try to find question
                    q_elem = elem.select_one('h3, h4, strong, .question')
                    if q_elem:
                        text = q_elem.get_text(strip=True)
                        if '?' in text or len(text) > 10:
                            question = text
                    
                    # Try to find answer
                    a_elem = elem.select_one('p, .answer, [class*="content"]')
                    if a_elem:
                        text = a_elem.get_text(strip=True)
                        if text and text != question:
                            answer = text
                    
                    if question and answer:
                        faqs.append({'question': question, 'answer': answer})
            
            return faqs
        except Exception as e:
            print(f"Error extracting FAQs: {e}")
            return faqs
    
    def scrape_fund(self, fund_name: str) -> Optional[AxisMFFundData]:
        """Scrape all data for a specific fund from AxisMF.com"""
        url = self.csv_manager.get_url(fund_name, "riskometer")
        
        if not url:
            print(f"No URL found for {fund_name}")
            return None
        
        print(f"Scraping {fund_name} from {url}...")
        
        soup = self._get_soup(url)
        if not soup:
            return None
        
        fund_code = url.split('/')[-2] if '/' in url else 'unknown'
        
        fund_data = AxisMFFundData(
            fund_name=fund_name,
            fund_code=fund_code,
            source="axismf.com",
            source_url=url,
            csv_reference=f"sources.csv:{fund_name}",
            last_updated=datetime.now().isoformat(),
            riskometer=self._extract_riskometer(soup),
            benchmark=self._extract_benchmark(soup),
            faqs=self._extract_faqs(soup)
        )
        
        return fund_data
    
    def scrape_all_funds(self) -> Dict[str, AxisMFFundData]:
        """Scrape data for all funds from AxisMF.com"""
        results = {}
        axismf_sources = self.csv_manager.get_axismf_sources()
        fund_names = list(set(source.fund_name for source in axismf_sources))
        
        for fund_name in fund_names:
            fund_data = self.scrape_fund(fund_name)
            if fund_data:
                results[fund_name] = fund_data
        
        return results
    
    def save_to_json(self, data: Dict[str, AxisMFFundData], output_path: str = None):
        """Save scraped data to JSON file"""
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_path = os.path.join(base_dir, "shared", "data", "raw", "axismf_data.json")
        
        output_data = {
            fund_name: fund_data.to_dict()
            for fund_name, fund_data in data.items()
        }
        
        output_data['_metadata'] = {
            'source': 'axismf.com',
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
    scraper = AxisMFScraper()
    
    print("=== Phase 1: AxisMF.com Scraper ===\n")
    
    results = scraper.scrape_all_funds()
    
    print("\n=== Scraping Results ===")
    for fund_name, fund_data in results.items():
        print(f"\n{fund_name}:")
        print(f"  Riskometer: {fund_data.riskometer}")
        print(f"  Benchmark: {fund_data.benchmark}")
        print(f"  FAQs Count: {len(fund_data.faqs)}")
        print(f"  Source URL: {fund_data.source_url}")
    
    output_path = scraper.save_to_json(results)
    print(f"\nData saved to: {output_path}")


if __name__ == "__main__":
    main()
